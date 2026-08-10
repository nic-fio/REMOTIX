# REMOTIX_V2

Desktop remoto per Linux: un **server**, **nessun client da installare** — basta un browser
moderno — e un protocollo nostro chiamato **RCP** — *Remotix Control Protocol*, che viaggia su
**WebTransport**.

> ## Stato al 10 agosto 2026 — ⭐ **si riparte da qui**
>
> **Fase 1 aperta**, banco scritto e **revisionato prima del prodotto** (44 rilievi, 38 `[R]`,
> tutti curati). ⭐ **Il banco B2 ha chiuso `DECISIONI.md` §6.4: la libreria QUIC è
> `ngtcp2`+`nghttp3`** — con un banco, non su carta, e con le altre tre eliminate ciascuna da una
> misura.
>
> ### Che cosa è misurato `[M]`
>
> | | |
> |---|---|
> | ⭐ **il modello di fiducia regge** | una sessione WebTransport verso un certificato **autofirmato P-256 di 13 giorni**, con l'impronta pubblicata nella pagina e **nessun avviso**: **Chrome 151** (30,2 ms) e **Firefox 140** (52,0 ms). `RCP.md` §4.1-bis passa da `[S]` a `[M]` su **due motori** |
> | ⭐ **`ngtcp2` e `quiche` passano il criterio dell'SNI** | **10 agosto**: i loro server d'esempio servono il certificato a chi **non manda SNI**, e ⛔ **l'impronta ricevuta combacia con quella del file** — la stretta di mano che riesce non basta. ⇒ **il criterio non separa più le due candidate** |
> | ⭐ **la diagnosi di `lsquic` si chiude** | senza SNI: *«fail certificate lookup»*; **con** SNI: *«looked up cert for remotix.prova»*. ⛔ Il difetto è l'SNI e nient'altro — **l'eliminazione regge, adesso su una prova intera**. E resta in coda a ogni esecuzione come **controllo negativo**: dimostra che la sonda sa vedere un rifiuto |
> | ⛔ **e `quiche` porta un costo che non c'entra col QUIC** | la **0.29.3 pretende `rustc` 1.88** e Trixie ne ha **1.85**: si misura la **0.28.0**, scelta dal banco. Sceglierla significa restare lì finché Debian non aggiorna, **o** portarsi una catena Rust fuori dai pacchetti. `ngtcp2` non pone la domanda |
> | ⭐⭐ **il server minimo su `ngtcp2` esiste, e un BROWSER VERO apre la sessione** | **Chrome 151** e **Firefox 140**, tutt'e due `APERTA` su `https://192.168.0.2:7447/rcp/1`, impronta pubblicata, **nessun avviso**, `"ciao"` che torna identico. ⛔ E `/rcp/9` **rifiutato con 404**, come impone `RCP.md` §2.2 |
> | ⭐ **e adesso «quanto collante» ha un numero** | lo strato WebTransport su `ngtcp2`+`nghttp3`: **482 righe aggiunte, di cui 333 di codice**, misurate con `git diff` e non stimate |
> | ⭐ **le sei proprietà di B2: 6 su 6** | tetto 30 s · datagram · credito **16** stream uni · migrazione **non** disabilitata · **niente 0-RTT** · `allowPooling: false`. ⛔ **Lette dal pari**, non dal registro del server — e proprio per questo hanno trovato **due difetti senza sintomo**: il server offriva 0-RTT (che §2.3 vieta) e concedeva 3 stream unidirezionali invece di 16 |
> | ⭐ **e il tetto si può cambiare** | con `--timeout=10s` il pari legge 10 000 ms: **B3** potrà distinguere il tetto del protocollo da quello del trasporto |
> | ⛔⭐ **e `quiche` non arriva a WebTransport dal C** | dichiara **4** impostazioni sul filo e **nessuna delle due di WebTransport**. `h3::Config::set_additional_settings` **esiste in Rust e non nell'FFI**, e il trucco usato su `ngtcp2` lì non c'è: quei byte un'applicazione in C non li vede mai. ⇒ **§6.4 è chiusa** |
> | ⭐ **l'arbitro non cade** | `aioquic` 1.2.0 porta WebTransport ⇒ il **cliente di prova** di B9 è possibile. ⚠ Ma parla la **bozza 02**, e i browser la **07**: il server manda tutt'e due le dichiarazioni, o metà degli strumenti direbbe di sì per il motivo sbagliato |
>
> | ⭐⭐ **RCP parla, e l'arbitro lo conferma** | **B3**: `CIAO`→`ECCOMI`→`CREDENZIALI` (PAM)→`AMMESSO`→`ATTACCA`→`SESSIONE`, su **due connessioni** — e ⛔ **le tracce sono dichiarate conformi dal validatore di B4**, un terzo programma scritto leggendo solo `RCP.md`. Il **secondo fisso** di §4.4-bis misurato a **1074-1085 ms** |
> | ⭐ **B4: il validatore è certificato** | **7 su 7** — sei registrazioni guaste accusate **ciascuna sul byte dichiarato in anticipo**, e la settima, conforme, accettata. ⭐ E alla prima esecuzione ha trovato **una contraddizione in `RCP.md`**: §4.3 vietava un carattere che §4.3 stessa usa |
>
> | ⭐ **B3: tre giri su tre** | 1ª · 2ª dopo la chiusura · **2ª mentre la 1ª è viva ⇒ `GIA_ATTIVA_REMOTA`**, per tutt'e due le strade di §3.1 — `CONGEDO` sul controllo *e* il codice nella chiusura della sessione — e la prima **non viene spodestata**. ⛔ *Il terzo giro era rosso, e il colpevole era il banco* |
>
> ### ⛔ Il prossimo passo
>
> Le due prove di B3 che restano — **35 s a `max_idle_timeout` 120** (che distingue «il server sa
> che una sessione è staccata» da «QUIC ha chiuso da sé») e la **terza connessione con il
> certificato ruotato** — poi **B5**, le prove di violazione: tipo sconosciuto, lunghezza sbagliata,
> messaggio nello stato sbagliato. ⛔ *Un banco che non prova a violare il protocollo non prova il
> protocollo.*
>
> ⚠ **E una manutenzione che ha una data**: le 333 righe includono la **riscrittura del frame
> SETTINGS di nghttp3**, che dipende dalla forma dei suoi byte e non da una sua promessa. ⛔ Va
> riprovata a ogni aggiornamento di nghttp3 — e il banco che la riprova esiste.
>
> ⚠ **E una previsione resta aperta dopo due misure**: `lsquic` scrive le impostazioni della **bozza
> 02** e mai `SETTINGS_WT_MAX_SESSIONS`. Nemmeno con l'SNI ci si arriva — la connessione muore
> prima. Va tenuta aperta invece che chiusa con una prova che parla d'altro.
>
> ### Come si rimette in piedi il banco
>
> `banchi/01-b2-costruisci.sh` (BoringSSL + lsquic) · `01-b2-costruisci-ngtcp2.sh` ·
> `01-b2-sni-ngtcp2.sh` (costruisce `bsslserver`) · `01-b2-sni-quiche.sh` (`leggi`, poi
> `costruisci`) · `01-b2-lancia-sni.sh` (**la prova SNI sui tre bersagli**: `costruisci`, poi
> `misura`) · `01-b2-lancia-impostazioni.sh` (**chi dichiara WebTransport sul filo**) ·
> ⭐ `01-b2-ngtcp2-wt-innesta.py` (**lo strato WebTransport**) + `01-b2-lancia-wt.sh`
> (il cliente di prova, e il rifiuto di `/rcp/9`) + ⚠ `01-b2-lancia-sonda.sh` — **quest'ultimo si
> lancia da QUI, non dal server: i browser stanno da questa parte** · `01-b2-certificati.sh` (⚠ **rigenera l'impronta**: va rimessa nella
> pagina) · `01-b2-controllo-aioquic.py` (il controllo positivo) · `01-b2-cliente-aioquic.py` ·
> `01-b2-raccogli.py` + `01-b2-sonda.html` (la pagina, da `localhost`).
> ⚠ Tutto sotto `/media/REMOTIX` sopravvive al riavvio; il rootfs del server no —
> ⛔ **e per questo i server dei banchi sopravvivono anche loro**: il 10 agosto due di essi tenevano
> le porte otto ore dopo. Il banco adesso lo controlla prima di partire.
>
> ### ⛔ Quindici trappole in due giorni, tutte nel banco e nessuna nel prodotto
>
> `grep -q` con `pipefail` · `| tail` che mangia lo stato d'uscita **(rifatto il giorno dopo)** ·
> due percorsi passati come una stringa, con `2>/dev/null` a nascondere l'errore — **e quello ha
> stampato un verde** · `pkill -f` che uccide chi lo esegue **(rifatto anche questo)** · porte
> tenute da server di ieri · `>/dev/null` che inghiotte la **richiesta di password** · `setsid` che
> forca e falsa il PID · `kill -0` che confonde *proibito* con *morto* · un'impronta tagliata di
> **una lettera**, che avrebbe bocciato una candidata · una cartella di profilo mancante, e nessuno
> dei due lati che lo dicesse · ⛔ **e il buffer di Python, che ha fatto accusare al banco un server
> innocente**.
>
> ⛔ **Quest'ultima è la settima veste, ed è la peggiore**: non un falso rosso, ma **un rosso
> puntato sull'imputato sbagliato**. Il banco aspettava una riga di registro per sapere quando il
> primo client era attaccato, e quella riga usciva dal buffer solo quando il client **si
> staccava** — cioè dichiarava «attaccata» una verità appena scaduta. `LEZIONI.md` §1.9 punto 7:
> *un file scritto e chiuso è un fatto; una riga stampata è una speranza sul momento in cui
> qualcuno la vedrà.*
>
> ⭐ Da cui la **quarta regola** di `LEZIONI.md` §1.9 — *una misura deve dichiarare su che cosa ha
> guardato* — e il suo **corollario del 10 agosto**, nato dal difetto più grave finora:
> ⛔ **la sonda dichiarava un denominatore falso**, e le sue due gambe misuravano la stessa cosa
> mentre diceva che erano opposte. *Un denominatore si legge **dove la cosa succede** — sul filo,
> non nella configurazione — e chi non può leggerlo lì se lo fa confermare da un programma che non
> è suo.*
>
> ⛔ **E il corollario del corollario, che vale per i verdetti**: un giro ha stampato *«OK — i motori
> provati hanno registrato il loro esito»* con **zero motori provati**. *«Tutti quelli provati sono
> andati bene»* è vero anche quando i provati sono zero — ed è la forma di verde più vuota che ci
> sia, perché non ha nemmeno bisogno che qualcosa vada storto. **Il denominatore di
> un'approvazione è quante cose ha approvato**, e adesso il banco lo stampa e si rifiuta di
> concludere se è zero.
>
> ---
>
> ## Stato precedente — la sera del 9 agosto 2026
>
> **Fase 0 chiusa**: i banchi riproducono i numeri di v1 (`fasi/00-ambiente.md`).
> **Nessuna riga di codice di prodotto ancora scritta.**
>
> La giornata ha cambiato il prodotto e poi ha controllato il cambiamento:
>
> | | |
> |---|---|
> | ⭐ **il client è il browser** | cadono i due client nativi e cinque fasi di piano — `DECISIONI.md` §1.6 |
> | **la sicurezza è a due livelli** | TLS per il trasporto, indirizzo/porta/utente/password per l'accesso — §1.7 |
> | **la seconda connessione remota si rifiuta** | `RCP.md` §8.2, motivo `0x0F` |
> | 📖 **il sesto studio** | [`web.md`](web.md), con quattro rapporti in `web/rapporti/` |
> | ⛔ **due revisioni avversariali** | **51 contraddizioni** trovate e curate **prima del primo byte**: i verdetti sono `web/rapporti/R1-` e `R2-` |
>
> ### Il prossimo passo
>
> ⭐ **`fasi/01-filo-nudo.md` è aperto e già revisionato**, con i banchi e **nessuna riga di
> prodotto scritta** — il documento si apre *prima* di sviluppare (`PIANO.md` §0.1).
>
> ⛔ **Due revisioni avversariali sul banco, prima del prodotto: 44 rilievi — 38 `[R]`, 6 `[?]`.**
> Nessuna delle due verde, e il documento è stato **riscritto**, non rattoppato. I verdetti stanno
> in `fasi/rapporti/R3-` (il banco come strumento) e `R4-` (la coerenza con quel che è scritto).
> La forma che si ripeteva: **cadeva sempre il controllo che dice *no***, e tre volte era già stato
> scritto da chi ci era passato prima.
>
> ⚠ **E la cura è uscita da quel file**: `RCP.md` §4.1-bis diceva ancora che WebKit non implementa
> `serverCertificateHashes` — ed è **l'arbitro**; `web.md` ha riavuto i controlli negativi che i
> rapporti prescrivevano; `PIANO.md` ha l'ordine corretto e due banchi ricollocati.
>
> ⭐ **E una decisione dell'utente ha chiuso il conto dei dispositivi**: **Apple è un di più, non un
> obiettivo** — `DECISIONI.md` §1.8. Telefono e DeX ci sono, il Mac no e non si procura: **S1a esce
> dalla fase**, la libreria QUIC si sceglie su **due motori su tre**, e la riga sta scritta accanto
> alla scelta. ⛔ Safari resta **servito**, non **verificato**: sono due cose diverse, e la seconda
> non si scrive nella documentazione finché nessuno l'ha misurata.
>
> ⚠ **La libreria QUIC resta aperta** e la chiude un banco, non la carta (`DECISIONI.md` §6.4) —
> ed è il **primo** banco da eseguire, non più il secondo.

⭐ **Il client è una pagina web** *(deciso il 9 agosto 2026 — `DECISIONI.md` §1.6)*. Cadono i due
client nativi e con essi cinque fasi di piano; **Windows torna dentro come posto da cui ci si
collega**, senza che scriviamo una riga per lui e senza sottostare alle sue regole. Resta fuori
come **server**, che era la leva vera.

---

## Da dove si comincia a leggere

⛔ **In quest'ordine.** Chi salta il primo si ritrova a rifare errori già pagati.

| # | Documento | Che cosa contiene |
|---|---|---|
| **1** | [`LEZIONI.md`](LEZIONI.md) | **il fondamento**: come si misura, come si prova, come si impara. Ereditato da v1, che si è arenato ogni volta su una misura che non misurava quel che credevamo |
| **2** | [`SPECIFICHE.md`](SPECIFICHE.md) | **che cosa** fa il prodotto, e che cosa non fa |
| **3** | [`RCP.md`](RCP.md) | **come parlano** i due lati. È l'arbitro: in v1 lo era `mstsc`, ora è questo file |
| **4** | [`PIANO.md`](PIANO.md) | **le fasi**, in ordine, ciascuna col suo banco e il suo criterio di chiusura |
| **5** | [`DECISIONI.md`](DECISIONI.md) | **perché**: ogni decisione con la data, chi l'ha presa, e con che grado di certezza |

E per chi scrive o revisiona, prima di toccare qualcosa:
[`CODER.md`](CODER.md) · [`REVIEWER.md`](REVIEWER.md)

---

## Gli studi

Letture del codice, fatte prima di scrivere. I cinque dei desktop rispondono alle **quindici**
domande di `LEZIONI.md` §3.

[`gnome.md`](gnome.md) · [`kde.md`](kde.md) · [`xfce.md`](xfce.md) · [`lxqt.md`](lxqt.md) ·
[`cinnamon.md`](cinnamon.md)

⭐ **E il sesto, che non parla di un compositore**: [`web.md`](web.md) — il browser come client,
con i quattro rapporti di dettaglio in `web/rapporti/`. ⚠ **È quello che invecchia più in fretta**:
i compositori li congela Debian, i browser si aggiornano da soli.

⚠ **`gnome-remote-desktop.md` non è uno di questi** *(chiarito il 9 agosto 2026)*. Studia **il
server RDP di GNOME**, cioè un concorrente sul filo che abbiamo buttato — non il desktop. Con RDP
morto decade quasi per intero, ed è scritto su una versione che Trixie non ha (51.alpha contro
48.1). **Su GNOME si legge [`gnome.md`](gnome.md)**, che parla di Mutter e resta valido.

---

## Le cartelle

| | |
|---|---|
| `fasi/` | un documento per fase, **aperto quando la fase si apre** — vedi `PIANO.md` §0.2 |
| `v1/` | l'eredità di REMOTIX v1: **17.481 righe di C**, 4.563 di banchi, i documenti e le scene di taratura |
| `reference-*/` | cloni dei progetti di riferimento — **non versionati**, si rifanno con `git clone` |

---

## Le convenzioni

**Si scrive in italiano**, documenti e commenti. I nomi nel codice pure: `palco`, `cattura`,
`sentinella`, `appunti`.

**Le marche** dicono quanto vale un'affermazione, e vanno messe sempre:

| | |
|---|---|
| `[M]` | misurato da noi, sul ferro, con la data |
| `[R]` | letto nel codice di un riferimento |
| `[S]` | letto in una specifica |
| `[?]` | ipotizzato, **non ancora misurato** |

⛔ **Una decisione che poggia su una `[?]` va scritta come provvisoria.** Una ragione non misurata
rende la decisione presa a metà (`LEZIONI.md` §2.3-quater).

**Le decisioni stanno in `DECISIONI.md`, una sola volta.** Gli altri documenti rimandano, non
copiano — e le voci portano ✅ (deciso dall'utente), 🔸 (derivato, correggibile senza discussione)
o ❓ (aperto).

⛔ **Quando una misura contraddice un documento, lo si aggiorna nello stesso momento**, con la data
e la fonte. Un riferimento che invecchia in silenzio è peggio di nessun riferimento.

---

## Il metodo

Due tipi di agenti — chi scrive e chi cerca contraddizioni — e la revisione interviene **tre
volte** per fase: sul banco *prima* che il prodotto esista, sul codice prima di misurarlo, sul
documento prima della chiusura (`PIANO.md` §0.4).

⭐ **Perché la revisione qui pesa più del solito**: buttando RDP abbiamo perso l'arbitro esterno —
`mstsc` protestava gratis quando sbagliavamo. Ora client e server sono nostri, e **due programmi
scritti dalla stessa mano che vanno d'accordo non confermano niente**.

⚠ Con il client web ne torna indietro **un pezzo**: la pagina gira su tre motori scritti da tre
squadre che non ci conoscono, e il loro disaccordo è un difetto che si dichiara da solo. Non basta,
ma non è niente.

---

## La macchina di prova

`192.168.0.2` — i5-13500T, 31 GB, Intel UHD 730 (per REMOTIX) e Radeon RX 6800 (riservata
all'inferenza). Ci si arriva con `v1/strumenti/sshpw.py`, che legge le credenziali da
`~/SERVER.ssh`.

Là vivono il `devroot` per compilare e provare, la VM, e la cache dei pacchetti. **I sorgenti no**:
quelli stanno qui, versionati.
