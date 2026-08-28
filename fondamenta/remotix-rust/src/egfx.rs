//! Pipeline grafica EGFX (MS-RDPEGFX).
//!
//! E' il percorso di rendering previsto dalla specifica di REMOTIX, e l'unico
//! che manterremo: niente ordini di disegno legacy, niente cache di bitmap.
//!
//! I fotogrammi viaggiano in **AVC420**, cioe' H.264. E' l'unico formato che
//! tutti e tre i client di riferimento disegnano davvero: il percorso non
//! compresso, pur ammesso dalla specifica, non e' reso dal client Microsoft ed
//! e' stato rimosso dopo la verifica sul campo.
//!
//! # Come si incastrano i pezzi
//!
//! IronRDP tiene EGFX separato dal flusso ordinario degli aggiornamenti: i
//! fotogrammi non passano per `next_update`, ma vengono spinti direttamente
//! nel `GraphicsPipelineServer` e poi consegnati al ciclo di eventi del server
//! sotto forma di messaggi gia' codificati.
//!
//! Ne consegue questo giro:
//!
//!   1. la fabbrica costruisce il server EGFX e ne conserva la maniglia;
//!   2. il client negozia le capacita' e il gestore segna «pronto»;
//!   3. chi disegna chiama `invia_avc420`, che accoda il fotogramma,
//!      svuota la coda di uscita e spedisce i messaggi al ciclo di eventi.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use anyhow::{Context as _, Result};
use ironrdp_dvc::encode_dvc_messages;
use ironrdp_egfx::pdu::{
    Avc420Region, CapabilitiesAdvertisePdu, CapabilitiesV10Flags, CapabilitiesV81Flags,
    CapabilitiesV103Flags, CapabilitiesV104Flags, CapabilitiesV107Flags, CapabilitySet,
};
use ironrdp_egfx::server::{GraphicsPipelineHandler, GraphicsPipelineServer};
use ironrdp_pdu::gcc::{Monitor, MonitorFlags};
use ironrdp_server::tokio::sync::mpsc::UnboundedSender;
use ironrdp_server::{
    DesktopSize, EgfxServerMessage, GfxDvcBridge, GfxServerFactory, GfxServerHandle, ServerEvent,
    ServerEventSender,
};
use ironrdp_svc::ChannelFlags;
use tracing::{debug, info, warn};

/// Stato condiviso fra la fabbrica, il gestore delle capacita' e chi disegna.
///
/// I tre vivono in punti diversi del server e non possono passarsi i dati per
/// parametro: questa struttura e' il loro terreno comune.
pub struct StatoGfx {
    /// Maniglia al server EGFX, disponibile dopo la costruzione.
    maniglia: Mutex<Option<GfxServerHandle>>,
    /// Canale verso il ciclo di eventi del server, per consegnare i messaggi.
    mittente: Mutex<Option<UnboundedSender<ServerEvent>>>,
    /// Vero quando il client ha negoziato EGFX e si possono inviare fotogrammi.
    pronto: AtomicBool,
    /// Superficie su cui si disegna, con la dimensione per cui e' stata creata.
    superficie: Mutex<Option<(u16, DesktopSize)>>,
}

impl StatoGfx {
    pub fn nuovo() -> Arc<Self> {
        Arc::new(Self {
            maniglia: Mutex::new(None),
            mittente: Mutex::new(None),
            pronto: AtomicBool::new(false),
            superficie: Mutex::new(None),
        })
    }

    /// Vero quando EGFX e' stato negoziato e si puo' disegnare.
    pub fn pronto(&self) -> bool {
        self.pronto.load(Ordering::Acquire)
    }

    /// Dimentica tutto quello che si sapeva della pipeline grafica del client.
    ///
    /// Serve dopo una **riattivazione della sessione**, cioe' la sequenza che
    /// RDP esegue quando cambia la risoluzione a sessione avviata: il client
    /// rifa' lo scambio delle capacita' e azzera il proprio stato grafico.
    /// Continuare a spedirgli fotogrammi come se nulla fosse significa parlare
    /// su un canale che per lui non vale piu': non protesta, semplicemente
    /// aspetta, e dopo una decina di secondi chiude la connessione.
    ///
    /// Azzerando, o il client rinegozia EGFX — e `on_ready` rimette tutto a
    /// posto — oppure si disegna col percorso di ripiego. In nessuno dei due
    /// casi si resta neri.
    pub fn azzera(&self) {
        self.pronto.store(false, Ordering::Release);
        self.invalida_superficie();
    }

    /// Invalida la superficie: la prossima chiamata ne creera' una nuova.
    ///
    /// Serve dopo un ridimensionamento, perche' la superficie porta con se'
    /// la dimensione per cui e' nata.
    pub fn invalida_superficie(&self) {
        *self.superficie.lock().expect("mutex avvelenato") = None;
    }

    /// Vero quando la pipeline accetterebbe un fotogramma **adesso**.
    ///
    /// Va interrogata **prima di codificare**, non dopo. Un fotogramma
    /// codificato e poi scartato non è lavoro sprecato e basta: il codificatore
    /// ha già spostato in avanti la propria immagine di riferimento, e il
    /// fotogramma dopo verrebbe descritto come differenza rispetto a
    /// un'immagine che il client non ha mai ricevuto. Da lì in poi le due
    /// ricostruzioni divergono e le zone che il codificatore considera già
    /// giuste non vengono più ritrasmesse: restano gli artefatti dietro alle
    /// finestre che si spostano e le copie del puntatore nelle posizioni
    /// vecchie.
    ///
    /// Il rifiuto arriva quando il client ha troppi fotogrammi non ancora
    /// confermati — tre, nella configurazione predefinita di IronRDP. In locale
    /// non capita quasi mai, perché i riscontri tornano in un istante; in rete,
    /// e con una superficie grande da spedire, capita di continuo. È il motivo
    /// per cui il difetto non si vedeva su FreeRDP e si vedeva su mstsc.
    pub fn puo_inviare(&self) -> bool {
        let maniglia = {
            let g = self.maniglia.lock().expect("mutex avvelenato");
            match g.as_ref() {
                Some(m) => Arc::clone(m),
                None => return false,
            }
        };
        let gfx = maniglia.lock().expect("mutex avvelenato");
        gfx.is_ready() && gfx.supports_avc420() && !gfx.should_backpressure()
    }

    /// Accoda un fotogramma **AVC420** e lo consegna al ciclo di eventi.
    ///
    /// `h264` e' un flusso Annex B; la regione dichiarata copre l'intera
    /// superficie, che e' quanto serve per un aggiornamento completo. La
    /// libreria costruisce da se' i metadati che MS-RDPEGFX antepone ai dati.
    ///
    /// Restituisce `false` quando il fotogramma non e' stato inviato perche'
    /// EGFX non e' pronto oppure perche' il client e' in ritardo — cioe' ha
    /// troppi fotogrammi non ancora confermati. Non e' un errore: si salta il
    /// giro e si riprova al successivo.
    pub fn invia_avc420(
        &self,
        superficie: DesktopSize,
        h264: &[u8],
        istante_ms: u32,
    ) -> Result<bool> {
        let maniglia = {
            let g = self.maniglia.lock().expect("mutex avvelenato");
            match g.as_ref() {
                Some(m) => Arc::clone(m),
                None => return Ok(false),
            }
        };

        let (messaggi, canale) = {
            let mut gfx = maniglia.lock().expect("mutex avvelenato");
            if !gfx.is_ready() {
                return Ok(false);
            }
            if !gfx.supports_avc420() {
                warn!("il client non ha negoziato AVC420");
                return Ok(false);
            }

            let id = match self.superficie_per(&mut gfx, superficie)? {
                Some(id) => id,
                None => return Ok(false),
            };

            // I bordi della regione sono INCLUSIVI: per una superficie larga
            // 2560 il bordo destro e' 2559, non 2560. Componendola a mano si
            // dichiarava una regione che sbordava di un pixel per lato, e
            // mstsc reagiva rinegoziando le capacita' e poi chiudendo la
            // connessione. Si usa il costruttore della libreria, che applica
            // la convenzione giusta.
            let regione = Avc420Region::full_frame(superficie.width, superficie.height, 26);

            if gfx
                .send_avc420_frame(id, h264, &[regione], istante_ms)
                .is_none()
            {
                debug!("fotogramma AVC420 saltato: il client e' in ritardo");
                return Ok(false);
            }

            let canale = gfx.channel_id().context("canale EGFX non ancora aperto")?;
            (gfx.drain_output(), canale)
        };

        if messaggi.is_empty() {
            return Ok(false);
        }

        let svc = encode_dvc_messages(canale, messaggi, ChannelFlags::empty())
            .context("codifica dei messaggi EGFX")?;

        let mittente = {
            let g = self.mittente.lock().expect("mutex avvelenato");
            match g.as_ref() {
                Some(m) => m.clone(),
                None => return Ok(false),
            }
        };
        mittente
            .send(ServerEvent::Egfx(EgfxServerMessage::SendMessages { messages: svc }))
            .map_err(|_| anyhow::anyhow!("il ciclo di eventi del server non riceve piu'"))?;

        Ok(true)
    }

    /// Restituisce la superficie corrente, creandola se manca o se e' cambiata
    /// la dimensione dello schermo.
    fn superficie_per(
        &self,
        gfx: &mut GraphicsPipelineServer,
        size: DesktopSize,
    ) -> Result<Option<u16>> {
        let mut corrente = self.superficie.lock().expect("mutex avvelenato");
        match *corrente {
            Some((id, s)) if s == size => Ok(Some(id)),
            altro => {
                if let Some((vecchia, _)) = altro {
                    gfx.delete_surface(vecchia);
                }

                // Dichiara la tela grafica CON la definizione del monitor.
                // Senza, il messaggio di reset viaggia con l'elenco dei monitor
                // vuoto: FreeRDP lo tollera, mstsc lo usa per posizionare
                // l'uscita e disegna l'immagine fuori posto.
                gfx.resize_with_monitors(
                    size.width,
                    size.height,
                    vec![Monitor {
                        left: 0,
                        top: 0,
                        // i bordi sono inclusivi, come per le regioni AVC420
                        right: i32::from(size.width) - 1,
                        bottom: i32::from(size.height) - 1,
                        flags: MonitorFlags::PRIMARY,
                    }],
                );

                let id = gfx
                    .create_surface(size.width, size.height)
                    .context("creazione della superficie EGFX")?;

                // Creare la superficie NON basta: va anche agganciata
                // all'uscita video, con un messaggio separato. Senza, il
                // client riceve i fotogrammi, li decodifica e li conferma
                // regolarmente, ma non li mostra — perche' nessuna superficie
                // e' collegata allo schermo. FreeRDP e' indulgente e disegna
                // lo stesso; mstsc fa quello che gli si e' detto, e resta nero.
                if !gfx.map_surface_to_output(id, 0, 0) {
                    anyhow::bail!("impossibile agganciare la superficie {id} all'uscita");
                }

                info!(
                    superficie = id,
                    larghezza = size.width,
                    altezza = size.height,
                    "creata la superficie EGFX e agganciata all'uscita"
                );
                *corrente = Some((id, size));
                Ok(Some(id))
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Registro: tiene lo stato grafico della connessione in corso
// ---------------------------------------------------------------------------

/// Punto d'incontro fra chi disegna e la connessione grafica del momento.
///
/// # Perche' non basta un solo stato condiviso
///
/// La pipeline grafica appartiene alla **singola connessione**, non al server:
/// canale, capacita' negoziate e superfici valgono per quel client e per
/// nessun altro. Tenerne uno solo per tutti sembra funzionare finche' le
/// connessioni non si sovrappongono — e si sovrappongono, perche' alcuni
/// client ne aprono una prima di chiudere l'altra.
///
/// Con uno stato unico, la connessione che muore per ultima azzera anche
/// quella appena nata, che resta a disegnare su una pipeline dichiarata
/// spenta: schermo nero senza alcun errore. Qui invece ogni connessione ha il
/// proprio stato, e chi se ne va porta via soltanto il suo.
pub struct RegistroGfx {
    corrente: Mutex<Option<Arc<StatoGfx>>>,
    mittente: Mutex<Option<UnboundedSender<ServerEvent>>>,
}

impl RegistroGfx {
    pub fn nuovo() -> Arc<Self> {
        Arc::new(Self {
            corrente: Mutex::new(None),
            mittente: Mutex::new(None),
        })
    }

    /// Lo stato della connessione grafica in corso, se ce n'e' una.
    pub fn corrente(&self) -> Option<Arc<StatoGfx>> {
        self.corrente.lock().expect("mutex avvelenato").clone()
    }

    /// Apre uno stato nuovo per una connessione che comincia adesso.
    fn apri(&self) -> Arc<StatoGfx> {
        // Va tracciato: chi disegna presume che questo avvenga **prima** che
        // gli venga chiesta una sorgente. E' vero con IronRDP di oggi, ma e'
        // un ordine che non controlliamo noi; se un giorno si invertisse, il
        // sintomo sarebbe una sessione bloccata sul percorso di ripiego, e
        // questa riga sarebbe l'unico modo per accorgersene.
        debug!("apro lo stato grafico di una nuova connessione");
        let stato = StatoGfx::nuovo();
        *stato.mittente.lock().expect("mutex avvelenato") =
            self.mittente.lock().expect("mutex avvelenato").clone();
        *self.corrente.lock().expect("mutex avvelenato") = Some(Arc::clone(&stato));
        stato
    }
}

// ---------------------------------------------------------------------------
// Fabbrica: costruisce il server EGFX quando arriva una connessione
// ---------------------------------------------------------------------------

pub struct FabbricaGfx {
    registro: Arc<RegistroGfx>,
}

impl FabbricaGfx {
    pub fn nuova(registro: Arc<RegistroGfx>) -> Self {
        Self { registro }
    }
}

impl ServerEventSender for FabbricaGfx {
    fn set_sender(&mut self, sender: UnboundedSender<ServerEvent>) {
        *self.registro.mittente.lock().expect("mutex avvelenato") = Some(sender.clone());
        // Se una connessione e' gia' aperta, va servita anche lei.
        if let Some(stato) = self.registro.corrente() {
            *stato.mittente.lock().expect("mutex avvelenato") = Some(sender);
        }
    }
}

impl GfxServerFactory for FabbricaGfx {
    fn build_gfx_handler(&self) -> Box<dyn GraphicsPipelineHandler> {
        let stato = self.registro.corrente().unwrap_or_else(|| self.registro.apri());
        Box::new(GestoreGfx { stato })
    }

    fn build_server_with_handle(&self) -> Option<(GfxDvcBridge, GfxServerHandle)> {
        // Una connessione che comincia porta con se' uno stato tutto suo.
        let stato = self.registro.apri();
        let server = GraphicsPipelineServer::new(Box::new(GestoreGfx {
            stato: Arc::clone(&stato),
        }));
        let maniglia: GfxServerHandle = Arc::new(Mutex::new(server));
        *stato.maniglia.lock().expect("mutex avvelenato") = Some(Arc::clone(&maniglia));

        Some((GfxDvcBridge::new(Arc::clone(&maniglia)), maniglia))
    }
}

// ---------------------------------------------------------------------------
// Gestore: riceve gli avvisi dal canale EGFX
// ---------------------------------------------------------------------------

struct GestoreGfx {
    stato: Arc<StatoGfx>,
}

impl GraphicsPipelineHandler for GestoreGfx {
    /// Il client dichiara cosa sa fare. Utile a capire, dal registro, perche'
    /// un client si comporti diversamente da un altro.
    fn capabilities_advertise(&mut self, dichiarate: &CapabilitiesAdvertisePdu) {
        info!(capacita = ?dichiarate, "il client dichiara le capacita' EGFX");
    }

    /// Il client ha negoziato le capacita': da qui si possono inviare fotogrammi.
    fn on_ready(&mut self, negoziate: &CapabilitySet) {
        info!(capacita = ?negoziate, "EGFX negoziato, pipeline grafica pronta");
        self.stato.invalida_superficie();
        self.stato.pronto.store(true, Ordering::Release);
    }

    fn on_surface_deleted(&mut self, superficie: u16) {
        debug!(superficie, "superficie EGFX eliminata");
    }

    /// Capacita' che il server dichiara di saper offrire.
    ///
    /// L'elenco deve essere fitto, non solo la versione piu' alta. La
    /// negoziazione sceglie la prima voce che il client dichiara a sua volta:
    /// mstsc arriva alla 10.6 e non oltre, quindi fermarsi alla 10.7 lo
    /// farebbe ripiegare sulla 8.1, dove AVC420 e' attivo solo se il client
    /// alza un flag apposito — cosa che mstsc non fa. Il risultato sarebbe una
    /// sessione senza alcun fotogramma.
    ///
    /// Dalla 10.0 in su AVC420 e' invece implicito salvo flag contrario, che
    /// e' esattamente il caso di mstsc.
    fn preferred_capabilities(&self) -> Vec<CapabilitySet> {
        let mut lista = vec![
            CapabilitySet::V10_7 {
                flags: CapabilitiesV107Flags::SMALL_CACHE,
            },
            CapabilitySet::V10_6 {
                flags: CapabilitiesV104Flags::SMALL_CACHE,
            },
            CapabilitySet::V10_5 {
                flags: CapabilitiesV104Flags::SMALL_CACHE,
            },
            CapabilitySet::V10_4 {
                flags: CapabilitiesV104Flags::SMALL_CACHE,
            },
            CapabilitySet::V10_3 {
                flags: CapabilitiesV103Flags::empty(),
            },
            CapabilitySet::V10_2 {
                flags: CapabilitiesV10Flags::SMALL_CACHE,
            },
            CapabilitySet::V10 {
                flags: CapabilitiesV10Flags::SMALL_CACHE,
            },
            CapabilitySet::V8_1 {
                flags: CapabilitiesV81Flags::AVC420_ENABLED | CapabilitiesV81Flags::SMALL_CACHE,
            },
        ];
        // Per riprodurre in locale la configurazione di client che non ho a
        // disposizione: REMOTIX_EGFX_MAX=10_6 scarta le versioni piu' alte,
        // cosi' FreeRDP negozia quello che negozierebbe mstsc.
        if let Ok(max) = std::env::var("REMOTIX_EGFX_MAX") {
            let salta = match max.as_str() {
                // Lascia la sola 8.1, che e' quella che negozia FreeRDP: serve
                // a distinguere un difetto del percorso V10.x da uno nostro,
                // quando un client si comporta diversamente dall'altro.
                "8_1" => 7,
                "10_6" => 1,
                "10_5" => 2,
                "10_4" => 3,
                "10_3" => 4,
                "10_2" => 5,
                "10" => 6,
                _ => 0,
            };
            lista.drain(..salta.min(lista.len()));
        }
        lista
    }
}

impl Drop for GestoreGfx {
    fn drop(&mut self) {
        if self.stato.pronto() {
            warn!("canale EGFX chiuso");
            self.stato.pronto.store(false, Ordering::Release);
        }
    }
}
