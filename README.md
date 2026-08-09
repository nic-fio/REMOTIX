# REMOTIX_V2

Desktop remoto per Linux: un **server**, **nessun client da installare** — basta un browser
moderno — e un protocollo nostro chiamato **RCP** — *Remotix Control Protocol*, che viaggia su
**WebTransport**.

> ## Stato alla notte del 9 agosto 2026 — ⭐ **si riparte da qui**
>
> **Fase 1 aperta**, banco scritto e **revisionato prima del prodotto** (44 rilievi, 38 `[R]`,
> tutti curati). Il banco **B2 — quale libreria QUIC** è in corso, e ha già prodotto misure.
>
> ### Che cosa è misurato `[M]`
>
> | | |
> |---|---|
> | ⭐ **il modello di fiducia regge** | una sessione WebTransport verso un certificato **autofirmato P-256 di 13 giorni**, con l'impronta pubblicata nella pagina e **nessun avviso**: **Chrome 151** (30,2 ms) e **Firefox 140** (52,0 ms). `RCP.md` §4.1-bis passa da `[S]` a `[M]` su **due motori** |
> | ⭐ **l'arbitro non cade** | `aioquic` 1.2.0 porta WebTransport ⇒ il **cliente di prova** di B9 è possibile |
> | ⛔ **`lsquic` è eliminata** | in HTTP/3 pretende **SNI** per trovare il certificato, e chi si collega a un **indirizzo IP** non lo manda. È il caso primario del prodotto. Scoperto dopo aver scritto **333 righe** di collante |
> | **`ngtcp2`+`nghttp3`** | costruite con lo stesso BoringSSL. Dentro 447 file: extended CONNECT in **9**, WebTransport in **0** ⇒ lo strato è tutto nostro |
>
> ### ⛔ Il prossimo passo, e non è scrivere codice
>
> **Una connessione senza SNI a `ngtcp2`.** È il criterio nuovo di `DECISIONI.md` §6.4, nato dalla
> morte di `lsquic`: *la libreria **deve** servire un certificato senza SNI*. Costa una connessione,
> e va provato **prima** del collante — non dopo 333 righe.
>
> ⚠ **E una previsione resta aperta**: `lsquic` scrive le impostazioni della **bozza 02** e mai
> `SETTINGS_WT_MAX_SESSIONS`. Non è stata né confermata né smentita — non ci siamo arrivati — e va
> tenuta aperta invece che chiusa con una prova che parla d'altro.
>
> ### Come si rimette in piedi il banco
>
> `banchi/01-b2-costruisci.sh` (BoringSSL + lsquic) · `01-b2-costruisci-ngtcp2.sh` ·
> `01-b2-certificati.sh` (⚠ **rigenera l'impronta**: va rimessa nella pagina) ·
> `01-b2-controllo-aioquic.py` (il controllo positivo) · `01-b2-cliente-aioquic.py` ·
> `01-b2-raccogli.py` + `01-b2-sonda.html` (la pagina, da `localhost`).
> ⚠ Tutto sotto `/media/REMOTIX` sopravvive al riavvio; il rootfs del server no.
>
> ### ⛔ Quattro trappole pagate in una sera, tutte nel banco e nessuna nel prodotto
>
> `grep -q` con `pipefail` (il riscontro riuscito letto come fallimento) · `| tail` che mangia lo
> stato d'uscita · due percorsi passati come una stringa, con `2>/dev/null` a nascondere l'errore —
> **e quello ha stampato un verde** · `pkill -f` che uccide il processo che lo esegue, **due volte**.
> ⭐ Da cui la **quarta regola** di `LEZIONI.md` §1.9: *una misura deve dichiarare su che cosa ha
> guardato — il denominatore, non solo il risultato*.
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
