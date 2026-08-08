//! Lettura dei fotogrammi dal nodo PipeWire aperto da Mutter.
//!
//! # Perche' un thread separato
//!
//! PipeWire ha un proprio ciclo di eventi, sincrono e bloccante, che non si
//! sposa con quello di tokio: mescolarli significa bloccare a vicenda. Il
//! ciclo PipeWire vive quindi in un thread dedicato e consegna i fotogrammi
//! attraverso un canale. E' anche la forma giusta per il seguito: la cattura
//! procede alla sua cadenza, indipendente da quella di chi codifica.
//!
//! # Perche' niente DmaBuf
//!
//! Un buffer DmaBuf resta nella memoria della GPU e va importato con EGL per
//! essere letto: e' la via veloce, e sara' quella della fase 9 quando il
//! codificatore lavorera' anch'esso su GPU. Per ora i fotogrammi devono
//! arrivare in memoria ordinaria, leggibili direttamente.
//!
//! Lo si ottiene **non dichiarando il campo `modifier`** nel formato proposto:
//! la negoziazione DmaBuf parte solo se il consumatore annuncia i modificatori
//! che sa importare. Tacendo, si ottiene memoria condivisa senza dover
//! aggiungere altro.

use anyhow::{Context as _, Result};
use tokio::sync::mpsc::{Receiver, Sender, channel};
use pipewire as pw;
use pw::spa;
use spa::param::format::{FormatProperties, MediaSubtype, MediaType};
use spa::param::format_utils;
use spa::param::video::{VideoFormat, VideoInfoRaw};
use spa::pod::{Pod, Property, object};
use spa::utils::{Direction, SpaTypes};
use tracing::{debug, info, warn};

/// Un fotogramma catturato, gia' copiato in memoria propria.
pub struct Fotogramma {
    pub larghezza: u32,
    pub altezza: u32,
    /// Byte per riga. **Non** e' `larghezza * 4`: il produttore allinea le
    /// righe come gli conviene e lo comunica nel chunk del buffer. Dedurlo
    /// dalla larghezza produce immagini oblique.
    pub stride: u32,
    /// Pixel in ordine B, G, R, A — lo stesso che vuole il codificatore.
    pub dati: Vec<u8>,
}

impl Fotogramma {
    /// Restituisce i pixel senza il riempimento di fine riga.
    ///
    /// Il codificatore vuole righe compatte; la cattura le consegna allineate.
    /// Quando i due valori coincidono non si copia nulla.
    pub fn compatto(&self) -> std::borrow::Cow<'_, [u8]> {
        let utile = self.larghezza as usize * 4;
        if self.stride as usize == utile {
            return std::borrow::Cow::Borrowed(&self.dati);
        }
        let mut fuori = Vec::with_capacity(utile * self.altezza as usize);
        for riga in self.dati.chunks_exact(self.stride as usize) {
            fuori.extend_from_slice(&riga[..utile]);
        }
        std::borrow::Cow::Owned(fuori)
    }
}

/// Maniglia sulla cattura in corso.
///
/// Lasciarla cadere ferma il ciclo PipeWire e chiude il thread.
///
/// # Perche' non si aspetta la fine del thread
///
/// Verrebbe spontaneo attendere che il thread finisca davvero. Sarebbe un
/// errore: questa struttura viene lasciata cadere da dentro il ciclo
/// asincrono del server, e mettersi in attesa li' **ferma un thread del
/// runtime** — con esso tutte le connessioni che gli sono affidate, non solo
/// la propria. Si manda il segnale di fermata e si prosegue; il thread chiude
/// il flusso e si spegne per conto suo, senza tenere nulla che serva ad altri.
pub struct Cattura {
    ferma: pw::channel::Sender<()>,
}

impl Cattura {
    /// Avvia la lettura dal nodo indicato.
    ///
    /// Il canale ha profondita' limitata e **scarta i fotogrammi in eccesso**
    /// invece di accodarli: se chi consuma e' piu' lento della cattura, una coda
    /// crescerebbe senza fine e mostrerebbe un desktop sempre piu' vecchio.
    ///
    /// Attenzione a cosa scarta: da questo lato si puo' solo buttare il
    /// fotogramma **nuovo**, perche' chi produce non puo' togliere dalla coda
    /// quelli gia' accodati. Tenere il nuovo e buttare il vecchio — che e' quel
    /// che si vuole davvero — tocca a chi consuma, che dopo ogni lettura svuota
    /// il canale fino all'ultimo arrivato (vedi `desktop.rs`). Senza quello
    /// svuotamento la profondita' del canale diventa ritardo puro.
    ///
    /// `dimensione` va indicata quando si riprende un **monitor virtuale**:
    /// in quel caso non esiste uno schermo da cui dedurla, ed e' il
    /// consumatore a dichiarare quanto grande lo vuole. Riprendendo invece un
    /// monitor esistente si lascia `None`, perche' la misura la impone lui e
    /// proporne un'altra farebbe fallire la negoziazione.
    ///
    /// E' asincrona perche' l'attesa dell'avvio **non deve bloccare il
    /// runtime**: il thread di PipeWire puo' metterci un attimo a negoziare
    /// col compositore, e fermare li' un thread del server significherebbe
    /// fermare anche le connessioni che gli sono affidate.
    pub async fn avvia(
        nodo: u32,
        dimensione: Option<(u32, u32)>,
    ) -> Result<(Self, Receiver<Fotogramma>)> {
        // Canale di tokio: il thread di PipeWire ci scrive senza bloccarsi,
        // il server lo legge dentro il proprio ciclo asincrono.
        let (tx_fotogrammi, rx_fotogrammi) = channel::<Fotogramma>(2);
        let (tx_ferma, rx_ferma) = pw::channel::channel::<()>();
        // Il thread segnala qui se non riesce nemmeno a partire, cosi'
        // l'errore emerge subito invece di manifestarsi come silenzio. Il
        // canale e' senza limite perche' ci si scrive da un thread ordinario,
        // dove non si puo' attendere.
        let (tx_avvio, mut rx_avvio) =
            tokio::sync::mpsc::unbounded_channel::<Result<(), String>>();

        std::thread::Builder::new()
            .name("cattura-pipewire".into())
            .spawn(move || {
                match ciclo(nodo, dimensione, tx_fotogrammi, rx_ferma, &tx_avvio) {
                    Ok(()) => debug!("ciclo di cattura terminato"),
                    Err(e) => {
                        let testo = format!("{e:#}");
                        warn!(errore = %testo, "ciclo di cattura interrotto");
                        let _ = tx_avvio.send(Err(testo));
                    }
                }
            })
            .context("avvio del thread di cattura")?;

        match tokio::time::timeout(std::time::Duration::from_secs(10), rx_avvio.recv()).await {
            Ok(Some(Ok(()))) => {}
            Ok(Some(Err(e))) => anyhow::bail!("cattura non avviata: {e}"),
            Ok(None) => anyhow::bail!("il thread di cattura e' morto senza dire perche'"),
            Err(_) => anyhow::bail!("il thread di cattura non ha dato segno di vita"),
        }

        Ok((Self { ferma: tx_ferma }, rx_fotogrammi))
    }
}

impl Drop for Cattura {
    fn drop(&mut self) {
        // Solo il segnale, nessuna attesa: vedi la nota sulla struttura.
        let _ = self.ferma.send(());
    }
}

/// Stato condiviso fra le richiamate del ciclo PipeWire.
struct Stato {
    formato: VideoInfoRaw,
    canale: Sender<Fotogramma>,
    /// Serve a segnalare una sola volta che i fotogrammi hanno cominciato ad
    /// arrivare: e' l'informazione che si cerca quando non si vede nulla.
    primo: bool,
}

fn ciclo(
    nodo: u32,
    dimensione: Option<(u32, u32)>,
    canale: Sender<Fotogramma>,
    ferma: pw::channel::Receiver<()>,
    avvio: &tokio::sync::mpsc::UnboundedSender<Result<(), String>>,
) -> Result<()> {
    pw::init();

    let ciclo_principale = pw::main_loop::MainLoop::new(None).context("ciclo PipeWire")?;
    let contesto = pw::context::Context::new(&ciclo_principale).context("contesto PipeWire")?;
    let nucleo = contesto.connect(None).context("connessione a PipeWire")?;

    let flusso = pw::stream::Stream::new(
        &nucleo,
        "remotix-cattura",
        pw::properties::properties! {
            *pw::keys::MEDIA_TYPE => "Video",
            *pw::keys::MEDIA_CATEGORY => "Capture",
            *pw::keys::MEDIA_ROLE => "Screen",
        },
    )
    .context("creazione del flusso PipeWire")?;

    let stato = Stato {
        formato: VideoInfoRaw::default(),
        canale,
        primo: true,
    };

    // Il ciclo deve poter chiudersi **da se'** quando il flusso si stacca, non
    // solo quando glielo si chiede da fuori.
    //
    // Serve al logout: quando l'utente esce dal menu di sistema, la sessione
    // grafica termina e Mutter porta il flusso a `Unconnected`. Se il thread
    // restasse vivo, il canale dei fotogrammi resterebbe aperto e chi legge non
    // distinguerebbe «desktop fermo» da «non c'e' piu' niente da catturare»: il
    // client resterebbe attaccato a un'immagine congelata, che e' esattamente il
    // difetto trovato in prova.
    let uscita = ciclo_principale.downgrade();

    let _ascoltatore = flusso
        .add_local_listener_with_user_data(stato)
        .state_changed(move |_, _, vecchio, nuovo| {
            info!(?vecchio, ?nuovo, "stato del flusso di cattura");
            // Solo se **eravamo** connessi: all'avvio il flusso parte da
            // `Unconnected`, e uscire li' sarebbe uscire prima di cominciare.
            let eravamo_connessi = matches!(
                vecchio,
                pw::stream::StreamState::Paused | pw::stream::StreamState::Streaming
            );
            if eravamo_connessi && matches!(nuovo, pw::stream::StreamState::Unconnected) {
                info!("il flusso di cattura si e' staccato: chiudo il ciclo");
                if let Some(ciclo) = uscita.upgrade() {
                    ciclo.quit();
                }
            }
        })
        .param_changed(|_, stato, id, param| {
            let Some(param) = param else { return };
            if id != pw::spa::param::ParamType::Format.as_raw() {
                return;
            }
            let Ok((tipo, sottotipo)) = format_utils::parse_format(param) else {
                return;
            };
            if tipo != MediaType::Video || sottotipo != MediaSubtype::Raw {
                return;
            }
            if let Err(e) = stato.formato.parse(param) {
                warn!(errore = ?e, "formato non interpretabile");
                return;
            }
            info!(
                larghezza = stato.formato.size().width,
                altezza = stato.formato.size().height,
                formato = ?stato.formato.format(),
                "formato negoziato con Mutter"
            );
        })
        .process(|flusso, stato| {
            let Some(mut buffer) = flusso.dequeue_buffer() else {
                debug!("nessun buffer disponibile");
                return;
            };
            let dati = buffer.datas_mut();
            let Some(primo_piano) = dati.first_mut() else { return };

            // Lo stride autorevole e' quello del chunk, non `larghezza * 4`:
            // il produttore allinea le righe a piacere.
            let chunk = primo_piano.chunk();
            let stride = chunk.stride().max(0) as u32;
            let dimensione = chunk.size() as usize;

            let Some(pixel) = primo_piano.data() else {
                debug!("buffer senza memoria mappata");
                return;
            };
            if stride == 0 || dimensione == 0 {
                return;
            }

            let altezza = stato.formato.size().height;
            let utili = (stride as usize * altezza as usize).min(pixel.len());

            if stato.primo {
                stato.primo = false;
                info!(stride, dimensione, "primo fotogramma ricevuto");
            }

            let fotogramma = Fotogramma {
                larghezza: stato.formato.size().width,
                altezza,
                stride,
                dati: pixel[..utili].to_vec(),
            };

            // Si scarta invece di attendere: bloccare qui fermerebbe il ciclo
            // di PipeWire, e con esso l'intera cattura.
            use tokio::sync::mpsc::error::TrySendError;
            match stato.canale.try_send(fotogramma) {
                Ok(()) => {}
                Err(TrySendError::Full(_)) => {
                    debug!("fotogramma scartato: il consumatore e' indietro");
                }
                Err(TrySendError::Closed(_)) => {
                    debug!("nessuno ascolta piu' la cattura");
                }
            }
            // Il buffer torna a PipeWire quando `buffer` esce di campo.
        })
        .register()
        .context("registrazione delle richiamate")?;

    let mut formato = formato_richiesto(dimensione);
    let mut parametri = [Pod::from_bytes(&formato).context("formato non serializzabile")?];

    flusso
        .connect(
            Direction::Input,
            Some(nodo),
            pw::stream::StreamFlags::AUTOCONNECT
                | pw::stream::StreamFlags::MAP_BUFFERS
                | pw::stream::StreamFlags::RT_PROCESS,
            &mut parametri,
        )
        .context("aggancio al nodo di Mutter")?;

    // Da qui in poi il ciclo e' avviato: chi ha chiamato puo' smettere di
    // aspettare.
    let _ = avvio.send(Ok(()));
    formato.clear();

    let ciclo_da_fermare = ciclo_principale.clone();
    let _ricevitore = ferma.attach(ciclo_principale.loop_(), move |()| {
        ciclo_da_fermare.quit();
    });

    ciclo_principale.run();
    Ok(())
}

/// Formato che REMOTIX dichiara di saper leggere.
///
/// Si elencano solo formati a 32 bit con i canali nell'ordine che il
/// codificatore si aspetta, e **nessun modificatore**: cosi' la negoziazione
/// resta in memoria ordinaria (vedi la nota in testa al modulo).
fn formato_richiesto(dimensione: Option<(u32, u32)>) -> Vec<u8> {
    let mut oggetto = object! {
        SpaTypes::ObjectParamFormat,
        pw::spa::param::ParamType::EnumFormat,
        Property::new(
            FormatProperties::MediaType.as_raw(),
            pw::spa::pod::Value::Id(spa::utils::Id(MediaType::Video.as_raw())),
        ),
        Property::new(
            FormatProperties::MediaSubtype.as_raw(),
            pw::spa::pod::Value::Id(spa::utils::Id(MediaSubtype::Raw.as_raw())),
        ),
        Property::new(
            FormatProperties::VideoFormat.as_raw(),
            pw::spa::pod::Value::Choice(pw::spa::pod::ChoiceValue::Id(
                spa::utils::Choice(
                    spa::utils::ChoiceFlags::empty(),
                    spa::utils::ChoiceEnum::Enum {
                        default: spa::utils::Id(VideoFormat::BGRx.as_raw()),
                        // **Solo i formati che sappiamo davvero leggere.**
                        //
                        // Qui c'erano anche RGBx e RGBA. Era un difetto
                        // silenzioso: tutto il resto della catena — la
                        // conversione in `colore.rs`, il ripiego a bitmap in
                        // `desktop.rs` — legge i canali nell'ordine B, G, R, e
                        // non esiste un solo punto che guardi il formato
                        // davvero negoziato. Se Mutter avesse scelto una delle
                        // due varianti RGB, rosso e blu sarebbero usciti
                        // scambiati, senza alcun errore da nessuna parte.
                        //
                        // Non e' mai successo perche' BGRx e' il primo della
                        // lista e Mutter lo accetta. Dipendeva quindi da una
                        // preferenza altrui, non da un accordo.
                        alternatives: vec![
                            spa::utils::Id(VideoFormat::BGRx.as_raw()),
                            spa::utils::Id(VideoFormat::BGRA.as_raw()),
                        ],
                    },
                ),
            )),
        ),
    };

    // La dimensione si dichiara solo per il monitor virtuale: e' l'unico caso
    // in cui non esiste uno schermo da cui dedurla.
    //
    // Si dichiara come **intervallo con un valore preferito**, non come misura
    // fissa: una misura fissa non lascia margine di accordo e Mutter respinge
    // la proposta con «no more input formats», che e' il suo modo di dire che
    // non ha trovato alcun formato in comune.
    //
    // La cadenza si dichiara a zero e si affida il ritmo al massimo: significa
    // «mandami un fotogramma quando cambia qualcosa, non a intervalli fissi»,
    // che e' esattamente il comportamento che serve a un desktop remoto.
    if let Some((larghezza, altezza)) = dimensione {
        // L'intervallo e' chiuso sul valore voluto: minimo, preferito e massimo
        // coincidono. Lasciandolo aperto Mutter sceglie per conto suo — e
        // sceglie 1280x720 — mentre qui la misura la decide chi guarda.
        let misura = spa::utils::Rectangle {
            width: larghezza,
            height: altezza,
        };
        let intervallo_dimensione = spa::utils::Choice(
            spa::utils::ChoiceFlags::empty(),
            spa::utils::ChoiceEnum::Range {
                default: misura,
                min: misura,
                max: misura,
            },
        );
        oggetto.properties.push(Property::new(
            FormatProperties::VideoSize.as_raw(),
            pw::spa::pod::Value::Choice(pw::spa::pod::ChoiceValue::Rectangle(
                intervallo_dimensione,
            )),
        ));
        oggetto.properties.push(Property::new(
            FormatProperties::VideoFramerate.as_raw(),
            pw::spa::pod::Value::Fraction(spa::utils::Fraction { num: 0, denom: 1 }),
        ));
        oggetto.properties.push(Property::new(
            FormatProperties::VideoMaxFramerate.as_raw(),
            pw::spa::pod::Value::Choice(pw::spa::pod::ChoiceValue::Fraction(spa::utils::Choice(
                spa::utils::ChoiceFlags::empty(),
                spa::utils::ChoiceEnum::Range {
                    default: spa::utils::Fraction { num: 60, denom: 1 },
                    min: spa::utils::Fraction { num: 1, denom: 1 },
                    max: spa::utils::Fraction {
                        num: 144,
                        denom: 1,
                    },
                },
            ))),
        ));
    }

    pw::spa::pod::serialize::PodSerializer::serialize(
        std::io::Cursor::new(Vec::new()),
        &pw::spa::pod::Value::Object(oggetto),
    )
    .expect("serializzazione di un oggetto costruito a mano")
    .0
    .into_inner()
}
