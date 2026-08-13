# REMOTIX_V2

Desktop remoto per Linux: un **server**, **nessun client da installare** — basta un browser
moderno — e un protocollo nostro chiamato **RCP** — *Remotix Control Protocol*, che viaggia su
**WebTransport**.

> ## Stato al 13 agosto 2026 — ⭐⭐⭐ **LA FASE 2 È CHIUSA: il desktop è dentro una scheda**
>
> ✅ **Chiusa il 13 agosto 2026, sul giudizio dell'utente**, che ha riaperto
> `https://192.168.0.2:7561/` **come sé stesso** dopo la cura del riscalamento e ha deciso di
> chiudere **davanti all'elenco di quel che resta aperto**.
>
> ⭐⭐ **E questa volta il giudizio non è solo una frase: i pixel sono stati misurati.** Il server
> dichiara `vista=2545x927` alle 08:45:44 UTC; lo scatto, otto secondi dopo, ha la zona dipinta alta
> **927 px** e larga **1648** — rapporto **1,7778** contro un 16:9 di **1,7778**. ⇒ La pagina riscala
> alla vista **senza storcere di un pixel**: `SPECIFICHE.md` §6.1 misurata sul vetro.
> ⭐ La provenienza sta in [`fasi/rapporti/GIUDIZIO-13-agosto.md`](fasi/rapporti/GIUDIZIO-13-agosto.md).
>
> ⛔ **E si chiude con SETTE cose dichiarate aperte**, messe davanti all'utente **prima** che
> decidesse — perché un giudizio dato senza sapere che cosa manca è un'approvazione al buio. Stanno
> nel riquadro «DA QUI SI RIPRENDE — 13 agosto» più sotto, e in
> [`fasi/02-primo-fotogramma.md`](fasi/02-primo-fotogramma.md).
>
> ⭐ **Il catalogo dei banchi è pieno: 15 su 15**, ed è il conto del **progetto** — le due copie del
> registro unite e rispecchiate, 90 giri, *nessuna riga persa, nessuna inventata*.
>
> ---
>
> ## Stato all'11 agosto 2026 — ⭐⭐ **LA FASE 1 È CHIUSA**
>
> ✅ **Chiusa la sera dell'11 agosto 2026, sul giudizio dell'utente**: *«Va bene, la stretta di mano
> funziona: fase 1 approvata»* — dopo aver aperto `https://192.168.0.2:7448` **dal portatile**, in
> **Chrome**, e aver letto *«Ammesso, sessione nuova, tela 1920×1080, desktop sconosciuto»*.
> ⭐ La misura ha una **provenienza su disco**: [`fasi/rapporti/GIUDIZIO-11-agosto.md`](fasi/rapporti/GIUDIZIO-11-agosto.md)
> — la scena, le impronte, il registro del server verbatim. ⛔ E la fase si chiude **con del lavoro
> dichiarato aperto**, che è la forma onesta: `PIANO.md` §0.2 la fa chiudere su *«una misura giudicata
> dall'utente, non un documento completo»*.
>
> **Il prodotto esiste**: `src/`, il server in C che un browser vero apre. Banco
> scritto e **revisionato prima del prodotto**: 44 rilievi — **38 `[R]`, tutti curati**, e **6 `[?]`,
> di cui due ancora aperte per nome** (R3.25 il segno della rotella su più di un compositore ·
> R3.26 la pila PAM per un utente diverso dal proprietario del processo). ⭐ **R3.27 — l'istante da
> cui parte il primo tetto — è chiusa dall'11 agosto 2026**, e l'ha chiusa il banco **B6** con due
> risposte. ⚠ *Questa riga diceva «44 rilievi, 38 `[R]`, tutti curati», e sommava i 38 ai 44: una
> `[?]` non si cura, **si misura** (`REVIEWER.md` §4). Corretta il 10 agosto 2026, rilievo **R11.19**.*
>
> ⛔ **E una quarta revisione avversariale, la notte del 10-11 agosto, su quattro lenti**: i banchi
> (**30** rilievi), il prodotto contro l'arbitro (**15**), i documenti (**17**), le cuciture fra i
> cinque agenti (**10**). ⛔ **Nessuna delle quattro è verde**, e i verdetti stanno in
> `fasi/rapporti/R12-A/B/C/D`. ⚠ *E il verdetto sui documenti ha trovato una causa di processo che
> vale più di metà dei suoi rilievi: i `.md` erano stati chiusi alle **22:40**, il codice ha
> continuato ad arrivare fino alle **00:36** — cioè la pagina che diceva «si riparte da qui» era già
> falsa nel momento della consegna. Questa pagina è stata riallineata l'11 agosto 2026, **a codice
> fermo**.*
> ⭐ **Il banco B2 ha chiuso `DECISIONI.md` §6.4: la libreria QUIC è
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
> | ⭐ **e adesso «quanto collante» ha un numero** | lo strato WebTransport su `ngtcp2`+`nghttp3`, **da solo**: **553 righe aggiunte — 373 di codice, 134 di commento, 46 vuote** `[M]` **10 agosto, ore 16:30**, con `git diff` su albero pulito e non stimate. ⚠ La successione delle misure della giornata sta in `DECISIONI.md` §6.4, riquadro «Quante righe sono nostre, e a che ora» — qui non si copia |
> | ⭐ **le sei proprietà di B2: 6 su 6** | tetto 30 s · datagram · credito **16** stream uni · migrazione **non** disabilitata · **niente 0-RTT** · `allowPooling: false`. ⛔ **Lette dal pari**, non dal registro del server — e proprio per questo hanno trovato **due difetti senza sintomo**: il server offriva 0-RTT (che §2.3 vieta) e concedeva 3 stream unidirezionali invece di 16 |
> | ⭐ **e il tetto si può cambiare** | con `--timeout=10s` il pari legge 10 000 ms: **B3** potrà distinguere il tetto del protocollo da quello del trasporto |
> | ⛔⭐ **e `quiche` non arriva a WebTransport dal C** | dichiara **4** impostazioni sul filo e **nessuna delle due di WebTransport**. `h3::Config::set_additional_settings` **esiste in Rust e non nell'FFI**, e il trucco usato su `ngtcp2` lì non c'è: quei byte un'applicazione in C non li vede mai. ⇒ **§6.4 è chiusa** |
> | ⭐ **l'arbitro non cade** | `aioquic` 1.2.0 porta WebTransport ⇒ il **cliente di prova** di B9 è possibile. ⚠ Ma parla la **bozza 02**, e i browser la **07**: il server manda tutt'e due le dichiarazioni, o metà degli strumenti direbbe di sì per il motivo sbagliato |
>
> | ⭐⭐ **RCP parla, e l'arbitro lo conferma** | **B3**: `CIAO`→`ECCOMI`→`CREDENZIALI` (PAM)→`AMMESSO`→`ATTACCA`→`SESSIONE`, su **due connessioni** — e ⛔ **le tracce sono dichiarate conformi dal validatore di B4**, un terzo programma scritto leggendo solo `RCP.md`. Il **secondo fisso** di §4.4-bis misurato a **1074-1085 ms** |
> | ⭐ **B4: il validatore è certificato** | **13 su 13** `[M]` **10 agosto, sera** — sette registrazioni guaste accusate **ciascuna sul byte dichiarato in anticipo**, la conforme accettata, e ⛔ **i quattro esiti del validatore tutti coperti**: conforme · non conforme · registrazione rotta · *niente da giudicare*. ⚠ *Diceva «7 su 7» con due soli esiti: «non ho niente da giudicare» e «conforme» avevano lo stesso codice d'uscita, rilievo **R7.4***. ⭐ E alla prima esecuzione ha trovato **una contraddizione in `RCP.md`**: §4.3 vietava un carattere che §4.3 stessa usa |
>
> | ⭐⭐ **B3: cinque giri su cinque** | 1ª · 2ª dopo la chiusura · **2ª mentre la 1ª è viva ⇒ `GIA_ATTIVA_REMOTA`** per tutt'e due le strade di §3.1, e la prima non viene spodestata · ⭐ **la 2ª dopo il silenzio**, 35 s a `max_idle_timeout` 120 — rifiutata a +6 s, **entra a +35 s**, e la connessione della prima è **ancora viva**: a liberare il posto è stato il server, non QUIC · ⭐ **la 3ª con il certificato ruotato, adesso PIENA** `[M]` **10 agosto, ore 18:5x**: la pagina ritira l'impronta nuova e apre su tutt'e due i motori, ⭐ **e il server risponde davvero** — `CIAO` → `ECCOMI` letto sul filo — ⛔ e con la vecchia tutt'e due **rifiutano**. ⚠ *La prima stesura di questo giro mandava la parola `ciao` aspettando l'eco dello strato WebTransport: una prova nata quando il server non parlava ancora RCP. Con RCP innestato quella parola non è un messaggio, il server ne aspettava il resto e la pagina restava appesa — ed è **quello** il «lo stream non ha funzionato» del mattino, non il certificato* |
>
> | ⭐⭐ **B5: quarantaquattro violazioni su quarantaquattro** | tipo sconosciuto · lunghezza in più e in meno · **4 GiB annunciati** · oltre 1 MiB · stato sbagliato · versione · nomi e valori di capacità · credenziali fuori intervallo · tela dispari e fuori limiti · disposizione malformata **contro** disposizione ignota (`SESSIONE_NON_SERVIBILE`) · secondo stream bidirezionale · tre canali nel verso sbagliato su stream unidirezionali. ⛔ Il motivo giusto ogni volta, **per tutt'e due le strade di §3.1**, e dopo **ciascuna** una connessione nuova arriva a `ECCOMI` |
> | ⭐ **e i cinque casi che DEVONO passare** | `hevc,vp9` → si sceglie `hevc` e **lo scarto si scrive** · **vista 300×801** e **1×1** (§7.1) · `BANCO_MARCA` a funzione spenta → `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` **senza chiudere** · `ritardo_ms = 20000` → `RITARDO_FUORI_LIMITI`. ⛔ Senza di loro, «il server chiude su tutto» darebbe **36 verdi su 36**. ⚠ *I casi che DEVONO passare sono **otto**, non cinque, e i 44 casi di B5 sono **36 violazioni + 8 verdi attesi**: la riga finale diceva «44 su 44», che è vera per costruzione (rilievo **R7.14**)* |
> | ⭐⭐ **B5 ha trovato un difetto che nessun altro banco vedeva** | il contatore **per indirizzo** di §4.4-bis era chiavato sulla provenienza **con la porta**, e con un solo tentativo per connessione la porta cambia ogni volta: quel contatore **valeva sempre 1**. Codice presente, che sembrava giusto, e che non faceva niente. Ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — anche per la parola d'ordine **giusta**. ⚠ *Il **sesto** era la regola di quel giorno: dalla sera del 10 agosto il ban scatta al **quarto** (`DECISIONI.md` §1.9), e la misura resta scritta com'era perché porta la data della regola che misurava* |
> | ⭐ **e una seconda contraddizione in `RCP.md`** | §2.2 dice che `CIAO(2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`; §9 dice di scegliere *«la più alta che non superi quella del `CIAO`»*. **Byte diversi per lo stesso ingresso.** Vince §2.2; §9 adesso la nomina. ⚠ *La cura del 10 agosto mandava a §2.4, che è «La porta» e non nomina né percorsi né versioni: corretta lo stesso giorno, rilievo **R11.2*** |
>
> ### ⭐⭐ LA CHIUSURA — la sera dell'11 agosto 2026
>
> #### ⭐⭐ LE CERTIFICAZIONI: **12 su 14**, e stamattina erano 3 — su un codice che non esiste più
>
> ⚠ *E stanotte sono **7 su 14**: non perché qualcuna sia fallita, ma perché la cura del congedo ha
> cambiato `rcp.c` e `RCP.md` sotto sette di loro. Il conto aggiornato, con i nomi, sta due riquadri
> più sotto.*
>
> ⛔ **E il denominatore è cambiato di sera, quindi i due numeri non si sottraggono.** Il catalogo di
> B12 è passato da **12 a 14 voci** (sono entrati **P1** e **P5**, i due banchi che guardano il
> prodotto), e ⚠ **i «14 banchi» e le «14 voci» non sono gli stessi 14**: il catalogo comprende
> **B10** ed esclude **B12**, che non certifica sé stesso. Contati bene: i banchi certificabili sono
> **13** e le voci con un banco dietro sono **13** — ⭐ due insiemi che adesso **coincidono**, mentre
> prima di stasera erano dodici e dodici **diversi**, cioè il conto tornava contando cose diverse.
>
> ```
> banchi nel catalogo: 14
> 12  certificati e valgono oggi   B2 B3 B4 B5 B6 B7 B8 B9 B10 B11 B13 C2
>  1  non riverificabile da CHUWI  P1   (la sua riga nomina un file che vive solo sul server)
>  1  provato e NON certificato    P5   (per un punto solo, e su un motore solo)
>  0  mai provati                  —    ⭐ la riga che stamattina non c'era
> ```
>
> ⛔⛔ **E QUESTO CONTO È SCADUTO POCHE ORE DOPO ESSERE STATO SCRITTO — `[M]` la notte fra l'11 e il
> 12 agosto 2026, `01-b12-guasti.py --registro`:**
>
> ```
> banchi nel catalogo: 14
>  7  certificati e valgono oggi   B2 B4 B10 B11 C2 P1 P5
>  7  certificazione SCADUTA       B3 B5 B6 B7 B8 B13 (rcp.c è cambiato) · B9 (RCP.md è cambiato)
>  0  non riverificabili           —   ⭐ P1 e P5 adesso si riverificano anche da CHUWI
>  0  provati e NON certificati    —
>  0  mai provati                  —
> ```
>
> ⭐⭐ **E le sette sono state RIESEGUITE la notte stessa — `[M]` 12 agosto 2026, `--registro`:
> 13 su 14, zero scadute, zero non riverificabili.** Certificati di nuovo: **B7** (`0→1→0`, 1m11s) ·
> **B9** (`0→3→0`, su CHUWI) · **B3** (`0→2→0`) · **B5** · **B6** · **B8** (`5→1→5`).
> ⛔ **Resta fuori B13, ed è l'unico dei quattordici.**
>
> ⛔⭐ **E la cosa che vale più delle sei righe: il primo giro si è RIFIUTATO di partire, in mezzo
> secondo.** `01-b0-terreno.sh` ha detto *«`examples/rcp.c` NON è `rcp/rcp.c`: il server misura una
> versione che nessuno sta leggendo»*. ⇒ Le sette non erano solo **scadute**: erano
> **irripetibili**. La cura aveva aggiornato `rcp/rcp.c`, ma il server dell'**innesto** — quello che
> sei di quei banchi interrogano — era ancora compilato sul codice del mattino. Rilanciarle senza
> guardare avrebbe scritto sei righe di registro con la data di stanotte **sul codice di prima**.
> ⭐ Curato: `rcp/rcp.c` propagato in `b2/ngtcp2/examples/rcp.c`, `ninja bsslserver`, terreno
> rimisurato (14 su 14). ⚠ **E nessun attrezzo fa quella propagazione** — i banchi la *controllano*
> soltanto: è il motivo per cui il disallineamento è rimasto lì mezza giornata.
>
> ⭐⭐⭐ **E POI ANCHE B13 È RIENTRATO: `[M]` 12 agosto 2026, `14 su 14`, zero scadute, zero non
> riverificabili, zero mai provati.** La cura non è stata toccare un numero: è stata **cambiare
> scena**. `01-b13-sera-certifica.sh certifica` rifà lo stesso ciclo con lo **stesso guasto** ma
> contro il **PRODOTTO** sulla 7481 — che la pagina la serve davvero — e lì `B13.4` ha un imputato:
> **sano 3 → guasto 1 → risanato 3**, con la marca «LE IMPRONTE COMBACIANO» contata **0 · 1 · 0**
> sui tre file d'uscita. ⇒ Il giro sano esce **3**, cioè esattamente l'atteso che il catalogo
> dichiarava: **il numero era giusto e la scena era sbagliata.**
> ⏳ **Quel che resta**: `01-b12-lancia.sh` non ha modo di essere puntato sul prodotto. Finché non
> ce l'ha, i due strumenti misurano due scene diverse e **solo uno dei due può certificare B13**.
>
> ⛔ **B13, perché sotto B12 non si certifica — e non è del prodotto.** Il suo giro sano esce **1** dove il catalogo
> dichiara **3**, e i numeri di B13 **non sono un conteggio**: `0` = sei proprietà su sei passano,
> `1` = **c'è almeno una proprietà ROSSA**, `3` = nessun rosso, ma restano buchi dichiarati `[?]`.
> Il rosso è **B13.4**, *«la pagina servita in TCP»*, che dà `[?]` se **nessuno** ascolta in TCP e
> **rosso** se qualcuno ascolta e la pagina non si carica (`SSLError: WRONG_VERSION_NUMBER`).
> ⚠ **E chi fosse ad ascoltare non è accertato**: finito il giro, su TCP 7447 non c'è più nessuno, e
> una seconda sonda non l'ha ripreso. ⛔ Quindi B13 resta **NON CERTIFICATO**, e si certifica il
> giorno in cui `B13.4` viene misurata dove la pagina **esiste** — cioè contro il **prodotto**, come
> già fu chiusa (riquadro «B13 — certificato», 200 e 31 083 byte) — non il giorno in cui qualcuno
> riscrive il numero.
> ⚠ *E per mezz'ora quel numero l'ho riscritto io, portandolo a **1**, avendo letto «1» come «un
> guasto solo» invece che «c'è un rosso». È stato rimesso a **3** e la ragione sta scritta accanto
> nel catalogo: con un rosso già presente il guasto non può più cambiare l'esito, e il banco
> diventerebbe **incertificabile per costruzione** — `[M]` sano 1 · guasto 1 · risano 1.*
>
> ⭐ **E la causa dello scadere non è una svista: è la cura del congedo.** `DECISIONI.md` §1.12 — la cura fuori
> fase decisa dall'utente — ha toccato **`rcp.c`** e **`RCP.md`**, cioè i file su cui poggiavano
> quelle sette certificazioni. ⇒ **Curare il prodotto fa scadere le certificazioni che lo
> guardavano, ed è esattamente quel che il registro deve dire**: la riga vale per quei byte, non per
> questi. ⛔ *«Scaduta» non è «fallita»*, e non è nemmeno «pulita»: quei sette **vanno rieseguiti**,
> e finché non lo sono valgono come **non certificati**.
>
> ⚠ E i due che si sono aggiunti al verde non sono la stessa cosa: **P5** è stato certificato
> stanotte con i tre giri; **P1** era già certificato dal pomeriggio, e a cambiare è che adesso la
> sua riga **si può riverificare da CHUWI** — prima il file che nomina non si leggeva di qua.
>
> ⛔ **E va detto che cosa vale come garanzia, perché non è lo stesso numero.**
> `banchi/01-b0-terreno.sh` — il controllo che guarda **sotto** i banchi, nato oggi perché **due
> volte in un giorno** un banco è stato verde su un terreno che non era quello che credevamo — è
> entrato nel giro alle **14:14**. Otto delle prime nove certificazioni sono delle ore precedenti.
> ⇒ **Come conteggio è 12; come garanzia «certificato su un terreno verificato» sono i giri della
> sera.**
>
> #### Il conto del pomeriggio, tenuto perché spiega da dove si partiva
>
> ⛔ **La prima cosa che ho trovato stamattina è che il conto era già scaduto.** Il registro porta,
> accanto a ogni certificazione, l'impronta di `rcp.c` con cui è stata fatta: era `d839839f…`, e il
> codice di oggi è `cb7af778…`. ⇒ *«3 su 12»* erano tre su un codice che non c'è più.
>
> | | |
> |---|---|
> | ⭐ **certificati oggi** | **B2 · B3 · B4 · B5 · B6 · B7 · B9 · B11 · C2** — tutti sul codice di adesso |
> | ⛔ **provati e NON certificati** | **B8** · **B13** — tutt'e due su lacune con un nome |
> | ⛔ **mai provato** | **B10** — il banco non esiste, ma ⭐ **il secondo utente adesso c'è** |
>
> ⚠ **Il numero dipende da dove lo si chiede**: il registro viveva in **due copie**, una per
> macchina. Unite in `banchi/01-b12-registro.jsonl` (quello versionato). ⛔ Ma il server ne dice
> **8** e il portatile **9**, e hanno ragione tutt'e due: sul server `RCP.md` non c'è, quindi B9 non
> si può *riverificare* lì — e lo strumento scrive «non so» invece di arrotondare.
>
> #### ⭐ CHE COSA È STATO FATTO LA SERA DELL'11 AGOSTO — i cinque punti dell'elenco
>
> | # | | esito |
> |---|---|---|
> | **1** | ⭐ **B8 — certificato**, `[M]` 13:46 UTC, innesto, porta 7471: **`5 → 1 → 5`**. Il giro copre finalmente la **sequenza intera** — due vite del server (*«ban caricati: 1»* dal disco, **I7**), la pagina del ban (200, *«tentativi esauriti»*, 12h 0m), lo sblocco su **un ban vero**. ⛔ **L'atteso sano è 5, non 0, ed è scritto nel catalogo prima del giro**: è l'esito *«il ban passa, ma le mediane si separano»*, e si concede solo perché l'imputato è **misurato** ed è **PAM** | ✅ fatto |
> | **2** | ⭐ **B13 — certificato**, e la cura del frammento **regge**: giro nuovo della sonda, **zero registri con la parola dentro**; poi buttati **33 file** con la traccia in `banchi/01-b13-buttati.jsonl`. ⭐ **`B13.4` chiusa contro il prodotto** (200, 31 083 byte, impronta corrente). ⛔ Restano `B13.3` e `B13.5` | ✅ fatto |
> | **3** | ⭐ **B10 — il banco esiste, e si è certificato nello stesso giro**: `prova2` arriva a `SESSIONE` sul **prodotto**. ⭐⭐ E **ha chiuso la `[?]` R3.26 con una misura**: la pila PAM giudica un altro utente **solo se il processo è privilegiato** | ✅ fatto |
> | **4** | ⭐ **Fatto dove mordeva, e fermato apposta**: `gira()` adesso **chiama** `01-b8-lancia.sh` invece di riscriverne la sequenza (come faceva già con C2). ⛔ Estenderlo agli altri stasera avrebbe **invalidato nove certificazioni** per rifarle in un tempo che non c'era | 🔸 metà |
> | **5** | ⭐ **P1 e P5 sono in catalogo**: 12 voci → **14**. **P1 certificato**; ⛔ **P5 no** — e vedi la riga qui sotto, che è la cosa che vale | 🔸 P5 no |
>
> #### ⛔⛔ IL DIFETTO DI PRODOTTO TROVATO IN FONDO ALLA SERATA — e prima era stato **assolto per sbaglio**
>
> **Il difetto**: chiudendo la scheda del browser, la pagina **non manda nessun `CONGEDO`**, dove
> `RCP.md` §8.1 lo impone senza condizioni. Il posto se ne va dopo **30 secondi di silenzio**.
> ⛔ **Su tutt'e due i motori.** La causa ha un nome: `src/pagina.html:620` azzera
> `congeda_corrente` **un millisecondo dopo `SESSIONE`**, e il gestore di `pagehide` (riga 331) è
> **codice morto**. ⭐ **La cura è di tre righe ed è scritta** in `fasi/01-filo-nudo.md`, riquadro
> P5.
>
> ⭐⭐ **E in fondo alla stessa serata è stata APPLICATA e RIMISURATA**, `[M]` **due giri per
> motore**: `pagehide` scatta con la guardia **PRESENTE**, `congeda()` viene chiamata, e al server
> arrivano **tutt'e due** le strade di §3.1 col motivo **`0x01`** — su Firefox **e** su Chrome, dove
> la chiusura col codice `0x0` che §3.1 vieta **non compare più**. L'ancora di `congeda_corrente`
> non è più *«il tentativo è finito»* ma ***«la sessione è finita»***: la azzera `wt.closed`, e solo
> se il riferimento è ancora il proprio. ✅ **Ed è un cambiamento di prodotto dopo la chiusura della
> fase 1, quindi è stato messo a verbale**: `DECISIONI.md` §1.12 — la cura è **fuori fase**, ⛔ la
> **fase 1 non si riapre** e la certificazione resta **12 su 14**, ⭐ e la cura **non si arretra**,
> perché è misurata con lo stesso rigore della fase. Alla fase 2 passa la **ricertificazione di P5**.
>
> ⛔⛔ **E la storia di come è stato quasi perso vale più del difetto.** In ordine:
>
> 1. **P5 accusava il prodotto** di non congedarsi — ⛔ ma batteva `ctrl+w` **su un display che non
>    era lo schermo finto**: un'accusa per **un gesto mai fatto**. Difetto del banco, vero.
> 2. **L'arbitrato che ne è seguito ha ASSOLTO la pagina** — ⛔ **e sbagliava**: contava la riga
>    *«la pagina ha chiuso la sessione, motivo»* **senza guardare il motivo**, e il motivo era
>    `0x0`, cioè **lo smontaggio di Chrome, che §3.1 vieta**. Una violazione contata come congedo,
>    e stampata come *«⭐⭐ la pagina fa quel che §8.1 le impone»*.
> 3. ⭐ **La terza misura ha attribuito davvero**, con una copia strumentata della pagina e un
>    portatore che non passa da WebTransport: `pagehide` **scatta**, e non c'è più niente da
>    chiamare. **Gecko è scagionato per misura** — la stessa `congeda()` chiamata da lì consegna
>    tutt'e due le strade di §3.1.
>
> ⇒ ⛔ **I due motori non erano opposti: era lo stesso difetto visto da due smontaggi**, e su uno il
> banco è inciampato nel proprio contatore. ⚠ **E il server lo diceva**: la riga
> `⛔ VIOLAZIONE §3.1 … A verbale va ERRORE_PROTOCOLLO` la scrive lui, ed era nel registro.
>
> #### ⭐ E un'accusa al prodotto che invece era davvero del banco
>
> **B8** scriveva *«la pagina del ban non si carica»* — cioè **proprio il silenzio che §4.4-bis
> vieta** — su un server che la pagina la serve: `leggi_pagina()` parlava **TLS a un innesto che
> risponde in chiaro**, e la causa era **la cura del giorno prima**, scritta per il prodotto.
>
> ⇒ Con B3, fa **tre volte in questa fase** che il rosso è puntato sull'imputato sbagliato — e una
> volta, stasera, che il **verde** lo era. ⭐ *La forma di `LEZIONI.md` §1.9 vale nei due versi, e il
> verde è quello che non torna a farsi vedere.*
>
> ⭐ **E c'è una regola nuova che vale più di ogni singolo punto**: *chi scrive un banco lo certifica
> nello stesso giro*, o il conto non cala mai. Oggi ne sono entrati due senza che nessuno lo notasse.
>
> #### ⭐ GLI ATTREZZI NUOVI, e servono al prossimo giro
>
> - **`banchi/01-b0-terreno.sh`** — ⛔ *il server è quello che credo?* 14 controlli, gira **prima**
>   di ogni certificazione, e B12 si rifiuta se non regge. ⭐ Nato perché **due volte oggi** un banco
>   è stato verde su un terreno sbagliato, e una l'ho presa **per caso**.
> - **`banchi/01-b0-chiamate.py`** — *chi chiama un banco gli passa quel che pretende?* Tre volte in
>   due giorni un chiamante era rimasto indietro su un argomento obbligatorio.
> - **`banchi/attrezzi-misura-marca.sh`** — innesta un guasto, cattura **tutta** l'uscita, e rimette
>   a posto **ricostruendo** anche se il giro muore. ⭐ È quello che rende una certificazione un'ora
>   invece di una mattinata.
>
> #### ⚠ QUEL CHE RESTA STORTO, detto invece che taciuto
>
> - ⛔ ~~**Su Firefox il congedo di §8.1 non esce**~~ — **separato, curato e rimisurato la stessa
>   notte**. ⚠ *«La pagina non spedisce»* e *«Firefox butta via quel che la pagina spedisce dentro
>   `pagehide`»* arrivavano **identici** al registro del server, e a separarli è servito il registro
>   **del browser**: `banchi/01-p5-ff-*`, con un portatore che non passa da WebTransport. ⇒
>   L'imputato era **la pagina**, su tutt'e due i motori; ⭐ la cura è nel prodotto e i due giri per
>   motore la confermano. ✅ **E la dichiarazione c'è**: `DECISIONI.md` §1.12 — cura **fuori fase**, la
>   fase 1 resta chiusa a **12 su 14**, e la ricertificazione di P5 è carico della fase 2.
> - ⚠ **E il tracciatore di quel banco è CIECO su Chrome dentro `pagehide`**: non esce né
>   `sendBeacon` né una XHR **sincrona**. Su Chrome l'attribuzione poggia solo sul registro del
>   server — che basta, perché fra prima e dopo cambia la riga della violazione, ⛔ ma chi
>   riusasse quel tracciatore altrove deve saperlo.
> - ⛔ **P5 non si certifica** per quel punto solo — il resto del suo giro sano è verde su Chrome.
>   ⭐ **E adesso la causa non c'è più**, ma il giro nuovo **non è stato fatto**: si fa alla fase 2
>   (`DECISIONI.md` §1.12). ⛔ *«Curato»* non vuol dire *«certificato»*: sono due parole diverse, e
>   questa fase le ha già confuse una volta.
>   ⭐ **La scena di P5 è curata la stessa notte** — due schede, così `ctrl+w` chiude **la scheda** e
>   non fa uscire Firefox — e con lei il contatore che l'avrebbe resa inutile: `01-p5-registro.py`
>   pretende adesso **`motivo 0x01`** invece di *«una chiusura qualunque»*, e conta la riga di
>   **violazione §3.1** con atteso zero. ⚠ *Provato su registri veri: il segmento pre-cura di Chrome
>   — quello su cui il banco vecchio stampava «la pagina fa quel che §8.1 le impone» — adesso è
>   **rosso con due guasti**.*
>   ⭐⭐ **E curando la scena è saltato fuori un terzo difetto**: sulla strada del `CONGEDO` il server
>   liberava il posto **senza scriverlo nel registro** (l'unico dei quattro punti a non farlo). Il
>   posto si liberava davvero — ⛔ ma l'invariante **§8.2 `0x0F` non era più osservabile**, e P5
>   avrebbe dato un rosso a un server sano. Curato e misurato (`DECISIONI.md` §1.12): il giudice di
>   P5 passa da **1 guasto falso** a **0**, due giri per motore.
> - ⛔ ~~La parola d'ordine nei registri sporchi~~ — **chiusa**: cura verificata con un giro nuovo,
>   **33 file** buttati con la traccia. ⛔ ~~E resta la parola sulla riga di comando (quindi in
>   `ps`)~~ — **chiusa anch'essa il 12 agosto 2026**, difetto **D12**: la strada di B10 (file `0600`,
>   `trap`) estesa a tutti i banchi. ⭐ **Verificata con un A/B, non dichiarata**: l'esca in `argv` è
>   vista **30 letture su 30**, la parola **0** e il percorso del file **30 su 30** — e quel «30» è il
>   denominatore, senza il quale lo zero sarebbe *«non ho guardato»*. ⛔ E il difetto non era teorico:
>   il contenitore è un **`chroot`, non uno spazio di nomi dei PID**, quindi i processi di dentro si
>   vedono tutti nel `ps` dell'host. ⚠ **Resta scoperto `01-b12-lancia.sh`** (5 chiamate) — e adesso
>   **dichiara a ogni giro** che la sua parola è in `ps`.
> - ⛔ ~~Il registro delle certificazioni va ancora unito a mano~~ — **chiuso il 12 agosto 2026**,
>   difetto **D10**: l'unione è **dentro il programma**, e dove non può esserlo (dal server la copia
>   del portatile non è raggiungibile) **il non averla fatta si vede nel posto in cui si legge il
>   numero**, col verdetto declassato. ⛔ **E il difetto aveva già morso**: le due copie divergevano
>   di **5 righe di qua e 2 di là**, e il passo manuale era stato saltato **sette volte**. ⛔⛔ E un
>   conflitto — la stessa certificazione con impronte diverse — si risolveva **in silenzio, per
>   ordine di riga nel file**: la stessa voce leggeva *«vale oggi»* o *«non oggi»* a seconda di quale
>   riga capitava più in basso. Adesso si ferma e lo nomina. ⭐ **Quel che NON è stato curato, perché
>   non è un difetto**: che il numero dipenda da dove lo si chiede — le due macchine hanno ragione
>   tutt'e due, e lo strumento scrive *«non so»* invece di arrotondare.
> - ⚠ ~~7 chiamate su 52 restano «IGNOTE»~~ → `[M]` 12 agosto 2026, difetto **D9**: **115 chiamate
>   guardate, 111 approvate, 0 rotte, 4 ignote** — e ognuna delle quattro porta scritto **nel codice**
>   perché è ingiudicabile (tre lo sono **per costruzione**: `$*`/`$@` vorrebbero eseguire il
>   chiamante del chiamante). ⛔ **E la metà peggiore del difetto non erano gli ignoti: era il
>   denominatore.** Le righe spezzate con `\` e i lanciatori che tengono il banco in una variabile
>   erano **fuori dal conto** — fra queste, quattro chiamate al validatore del filo e i giudici della
>   cattura, della sessione e di P5. ⭐ E il controllo positivo **non c'era**: aggiunto, e provato
>   mutando l'albero vero in copia (togliendo un obbligatorio dal profilo condiviso escono **7 rossi**).
> - ⚠ ~~`01-b0-terreno.sh prodotto` non guarda il binario del prodotto~~ — **curato il 12 agosto
>   2026**, difetto **D5**: il binario sta **accanto ai sorgenti** (`remotix/build/` non è mai
>   esistito, e un altro banco lo dichiarava già). ⛔ **E il caso che conta è un altro**: un binario
>   **stantio** sarebbe rimasto verde **anche col percorso corretto**, perché si confrontava il solo
>   `rcp.c`. Ora tutti i sorgenti più il `Makefile`, e l'albero **si dichiara** — sotto
>   `/media/REMOTIX/src` ce ne sono **cinque** con un `remotix` eseguibile dentro. Il terreno conta
>   **15 su 15** sull'innesto e **4 su 4** sul prodotto, dov'era *«2 controlli, 1 ignoto»*.
> - ⚠ **Le mediane di B8**: ~~1984~~ → `[M]` **2123 · 2198 · 1086 ms** (giro della sera). ⭐ Il numero
>   cambia perché cambia il giro; quel che è nuovo è che **l'imputato è misurato**: **+1034 ms** oltre
>   il secondo fisso sui respinti contro **+84 ms** sugli ammessi, cioè la firma di `pam_faildelay`.
>   ⇒ **PAM, non il nostro codice** — e la `[?]` resta aperta lo stesso.
>
> #### ⚖️ E QUEL CHE ASPETTA L'UTENTE — adesso è **una** cosa, non due
>
> ✅ **Il giudizio è dato**: 11 agosto 2026, e la fase è chiusa (in cima a questa pagina).
>
> ✅ **E i due ripieghi sono decisi anch'essi.** ⚠ *Questa riga li dava per aperti, ed era scaduta:
> l'utente li ha decisi la sera dell'11 agosto. Corretta il 12 agosto 2026.*
>
> 1. **Il filo unico** ⇒ `DECISIONI.md` **§1.10**: la verifica PAM **esce dal filo unico prima che la
>    fase 2 si apra**, e ⭐ **con un processo aiutante, non con un filo** — PAM non è affidabilmente
>    rientrante, e un thread porterebbe guai suoi dentro la cura di un problema di concorrenza.
>    ⛔ La ragione è del video: finché non c'è video il sintomo è *«l'ultimo dei dieci aspetta dieci
>    secondi»*, sgradevole e circoscritto; dalla fase 2 in poi **lo schermo di tutti quelli collegati
>    si pianta ogni volta che qualcun altro entra**, e chi lo vedrà **darà la colpa al video**.
> 2. **Il tetto delle sessioni** ⇒ `DECISIONI.md` **§1.11**: resta **16, fisso in compilazione, fino
>    alla fase 3** — perché *«il limite vero non è un conteggio: è un budget di pixel al secondo, e lo
>    pone il codificatore»*, e qualunque numero messo oggi sarebbe un segnaposto da cambiare due
>    volte. ⚠ E il prezzo è dichiarato: per due fasi **il codice dice 16 e la specifica dice 10**.
>
> ---
>
> ### ⭐⭐⭐⭐⭐ DA QUI SI RIPRENDE — **13 agosto 2026, notte.** ⇒ **IL NUMERO C'È: 78,1 ms — E IL COLLO DI BOTTIGLIA È IL DISEGNO**
>
> *La fase 3 ha il suo numero **con la codifica in hardware**, e la codifica in hardware è **nel
> prodotto**, non su una copia. ⏳ **Manca solo il giudizio dell'utente**, preparato in
> [`fasi/rapporti/F3-giudizio-elenco.md`](fasi/rapporti/F3-giudizio-elenco.md). Il conto per intero
> sta in [`fasi/rapporti/F3-sessione-13-sera.md`](fasi/rapporti/F3-sessione-13-sera.md).*
>
> | | totale | codifica | **disegno** | fps | P1 |
> |---|---|---|---|---|---|
> | AV1 in software *(la 7561)* | **71,86 ms** | 39,67 | ⭐ 9,07 | 22,0 | ✅ |
> | ⭐ **HEVC in hardware** *(la 7571, il deposito)* | **78,12 ms** | ⭐ 31,78 | ⛔ **28,00** | ⭐ **30,0** | ✅ |
>
> ⭐⭐ **L'ARCHITETTURA È ASSOLTA**: togliendo l'hardware si perdono **31,7 ms** e **gli altri quattro
> tratti non si muovono** (Mutter −0,02 · filo −0,12 · decodifica −0,76). La chiave passa da
> **114,5 ms a 5,1**, e il ritmo **raddoppia**.
> ⛔ **Ma il tetto SFORA** — 78,1 contro 50, e **94-118 ms** sul vetro col pezzo cieco dichiarato.
>
> > ### ⛔⛔⛔ E IL COLLO DI BOTTIGLIA NON È PIÙ LA CODIFICA: È IL DISEGNO
> > **28,0 ms su 78,1 — il 36 %** — contro i **5 ms** che ormai costa la codifica.
> > ⭐ E si vede **solo** perché i giri sono **quattro**: con due soli si leggerebbe *«−31 ms,
> > vittoria»* oppure *«l'hardware non serve»*. **Sono tutt'e due sbagliate.**
> > ⇒ **È il primo lavoro della prossima fase, e non era in nessun piano.**
>
> ⚠ **Il numero è 78,1 e non il 75,2 misurato su una copia**: quel giro aveva un controllo del banco
> **rosso**, questo no. ⛔ **Si è preso il peggiore dei due.**
>
> #### ⛔⛔ I tre lavori, in quest'ordine e non in un altro
>
> | | | perché **prima** |
> |---|---|---|
> | **1** | ⛔⛔ **IL PALCO**: i banchi browser **misurano sul desktop dell'utente** credendo di essere su uno schermo finto. Chrome ignora `DISPLAY` e va su Wayland da `XDG_SESSION_TYPE`. `[M]` `xlsclients` sull'Xvfb dice **0 clienti**, la pagina dice `screen 2560×1080` | finché non è fatto, **ogni numero di ritardo porta dentro la contesa col desktop dell'utente** — e il prossimo «prima» nascerebbe già sbagliato. ⚠ E ha già fatto **una vittima**: la certificazione di `03-b16` non si rigira, perché su una finestra da 2560 il caso `V3s` non trova più il difetto |
> | **2** | ⛔ **LA PAGINA**: HEVC **viene offerto e negoziato** ma **non dipinge nella sessione vera**, e il suo fallimento trascina `video.misura_massima` a **320×240** ⇒ tela 320×240 contro cattura 1920×1080, e il prodotto (correttamente, §6.2) **non spedisce**. **Zero fotogrammi** | senza, **nessun banco può esercitare il codificatore hardware**: non ci arriva un fotogramma, e la fase non si chiude |
> | **3** | ⭐ **IL NUMERO**: l'anello con la codifica in hardware, `03-b17-ritardo.py`, **stessa scena** | è il numero su cui la fase si chiude, e i due precedenti sono le sue precondizioni |
>
> ⚠ **E `/srv/src/03-B-src/` porta la pagina VECCHIA**: chi accendesse quell'albero così com'è
> misurerebbe il codificatore hardware **spento**, e scriverebbe *«l'hardware non serve a niente»*.
>
> #### ⭐ Quel che invece è in cassaforte
>
> | | |
> |---|---|
> | il numero della fase **regge** | **72,397 ms** rimisurati con banco e pagina nuovi (n=508), e la codifica vale **39,82 = il 55 %** |
> | la codifica in hardware **funziona** | `hevc_vaapi` porta il tratto da **28,03 a 2,64 ms** (scena facile) e da **113,10 a 3,93** (dura) |
> | ⛔ ma il totale **non** migliora | il collo di bottiglia si è spostato: **la conversione dei colori costa 5,65 ms**, più del doppio della codifica ⇒ ⭐ **`swscale` BGRx→P010 è il pezzo nuovo da aggredire: 7,1 ms su 9,7** |
> | il client **decodifica HEVC** | `VideoDecoder`: **120 fotogrammi su 120**, due strade di confezionamento, 5 giri su 5 |
> | ⛔ **AV1 in hardware NON esiste** | `av1_vaapi` esce **218**: restare su AV1 = restare in software **per sempre** |
> | ⛔ **Firefox non ha HEVC** in WebCodecs | ⇒ passare a HEVC **non toglie AV1: lo rende obbligatorio** |
>
> ---
>
> ### ⭐⭐⭐⭐ DA QUI SI RIPRENDE — **13 agosto 2026, notte.** ⇒ **LA SESSIONE NUOVA FA LA CODIFICA IN HARDWARE, DENTRO LA FASE 3** *(superato dal riquadro qui sopra)*
>
> *Deciso dall'utente: ⭐ «**si anticipa la codifica HW alla fase 3. Per questo però dopo servirà una
> nuova sessione**». ⛔ **La fase 3 NON è chiusa.***
>
> #### Perché, in un numero
>
> Il ritardo è **74,58 ms**, e ⛔ **39,17 — il 53 % — sono la codifica in software**. Gli altri
> quattro tratti sommano **~35,4 ms**: `[R]` **dentro il tetto dei 50 e vicino al traguardo dei 40**.
> ⇒ L'obiezione dell'utente, ed è quella giusta: *«senza accelerazione hw stiamo ragionando e
> sviluppando su numeri non molto affidabili»*. Le fasi 4-7 ne produrrebbero altri uguali, **da
> rifare dopo**.
>
> ⭐ **E costa poco farlo adesso**: la catena che si muove **esiste da oggi**, il banco dell'anello è
> scritto, la scena e la marca sono certificate ⇒ il *prima* e il *dopo* si misurano con **lo stesso
> strumento e la stessa scena**, e i due numeri **si sottraggono davvero**. Fra tre fasi non sarebbe
> più vero.
>
> #### ⭐⭐ Si può fare — `[M]` verificato il 13 agosto sul server
>
> ```
> Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
> VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
> VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
> ```
>
> ⛔ **E questa riga corregge un errore di oggi**: un agente aveva riferito *«su questo server non
> c'è un codificatore hardware per nessuno dei due codec»*, e **nessuno l'aveva verificata**. È vera
> per **AV1**, ⛔ **falsa per HEVC**. ⚠ Stessa forma dei «37 fotogrammi di Mutter»: una riga
> **ripetuta invece che misurata**, che poi decide un piano.
>
> #### ⛔⛔⛔ LO SCOGLIO NON C'ERA — **smentito la sera del 13, prima che partisse un agente**
>
> Qui era scritto: *«il codec negoziato è AV1 perché la sonda HEVC di Chrome fallisce su Xvfb ⇒
> senza un client che accetti HEVC l'anello intero non si misura. **Affrontalo per primo**»*.
> ⛔ **Lo scoglio non c'era — ma la ragione vera è la TERZA, e le prime due erano sbagliate.**
>
> | | chi | che cosa diceva | esito |
> |---|---|---|---|
> | 1ª | il piano del 13 notte | *«su Xvfb non c'è GPU ⇒ **è un problema di PALCO**, costruiscine uno»* | ⚠ **la premessa era giusta, la conseguenza no** |
> | 2ª | il coordinatore, ore 20:33 | *«non era il palco: era la **bandiera** `--disable-gpu` del banco»* | ⛔ **mezza falsa** |
> | 3ª | la corsia D, ore 22:00 | ⭐ **«Chrome ignora `DISPLAY` e va su Wayland da `XDG_SESSION_TYPE`: il banco non era MAI stato sull'Xvfb»** | ⭐ **e questa regge** |
>
> `[M]` con la controprova che **non passa dal browser** — `xlsclients`, chi è davvero attaccato a
> quello schermo:
>
> | come si lancia Chrome | clienti **sull'Xvfb** | `screen` | webgl | HEVC |
> |---|---|---|---|---|
> | **come lo lancia il banco** | ⛔ **0** | **2560×1080** (il monitor dell'utente) | GPU Intel | true |
> | `--ozone-platform=x11` | ⭐ **1** | 1280×1024 | *niente webgl* | **false** |
>
> ⇒ ⛔⛔ **La cosa grossa non è il codec: è che i banchi browser di questo progetto misurano sul
> desktop dell'utente credendo di essere su uno schermo finto.** Contesa non dichiarata, e ogni
> verbale che dice «Xvfb» dice una cosa che non è. **È il primo lavoro di chi riprende.**
>
> ⭐⭐ **E non è una dichiarazione: è una decodifica.** Il flusso uscito da `hevc_vaapi` è stato
> fatto **dipingere** al Chrome del banco — `[M]` **5 giri su 5**, 1920×1080, **119 fotogrammi su
> 120**, `powerEfficient: true`. **Il client c'è, ed è quello che c'era già.**
>
> ⛔⛔ **E una seconda riga che cambia il bersaglio per sempre**: la codifica **AV1 in hardware NON
> ESISTE** su questa macchina — `av1_vaapi` esce **218**, *«No usable encoding profile found»*, 3
> giri su 3. ⇒ **Restare su AV1 vuol dire restare in software per sempre.** HEVC non è una
> preferenza: è **l'unica strada** verso l'hardware, ed è misurata ai due capi.
>
> ⚠ **La forma dell'errore, che è la terza volta in due giorni**: una riga **ripetuta invece che
> misurata** stava per decidere il lavoro di una sessione intera. Qui però era peggio — ⛔ **il
> banco si era accecato da solo e non l'aveva scritto**. ⇒ La lezione nuova: *un banco che risponde
> «no» deve dire **con che palco** ha risposto*.
>
> #### L'ordine del lavoro, riscritto
>
> 1. ✅ ~~lo scoglio HEVC~~ — **chiuso**: resta una riga di cura alla sonda;
> 2. ⭐ **la codifica HEVC in hardware nel prodotto**, **su una copia** finché non è misurata — è
>    adesso **il primo lavoro**, e la sua strada critica è **B → E**;
> 3. ⭐ l'anello rimisurato con lo **STESSO** banco (`03-b17-ritardo.py`) e la **STESSA** scena;
> 4. ⛔ **i CINQUE tratti affiancati**, non il totale: *tolta la codifica software, gli altri quattro
>    restano dove sono?* Se restano, l'architettura è **assolta**;
> 5. ⚠ **i fotogrammi consegnati accanto ai millisecondi** — in v1 il costo scese da 41 ms a 6
>    **mentre i consegnati calavano da 29 a 22,7**;
> 6. e **solo allora** il giudizio dell'utente.
>
> ⚠ `EncSliceLP` è la codifica **a bassa potenza**: veloce, con limiti suoi — **non è equivalente**
> alla piena, e va dichiarato accanto al numero. ⭐ Ma porta un'occasione: è l'entrypoint che
> `web.md` nomina come *«da verificare»* per i **sotto-livelli temporali**, cioè abbandonare un
> fotogramma **senza rompere quelli dopo** — che oggi costa una chiave ogni volta.
> ⛔ **La copia zero NON si anticipa**: resta alla fase 8.
>
> ⭐⭐ **E L'ELENCO COMPLETO DI QUEL CHE C'È DA LAVORARE** — trentadue voci in sette gruppi, in
> ordine di quando mordono, con dentro **le trappole già pagate** perché non si ripaghino — sta in
> [`fasi/rapporti/F3-prossima-sessione.md`](fasi/rapporti/F3-prossima-sessione.md).
> ⛔ **RIVISTO la sera del 13**: quel file è stato **raddrizzato coi fatti misurati** — la corsia A
> è **cancellata**, la corsia K è **per metà già fatta** (il catalogo dice **24 banchi, 20
> certificati, 4 mai provati**), e gli agenti scendono da **dieci a sei**.
> ⇒ **Resta UNA voce bloccante**: il **punto cieco del catalogo** — nessuna certificazione guarda
> `codificatore.c`, e il lavoro nuovo va proprio lì. ⚠ E va detta più precisa di com'era scritta:
> `figlio.c` **a catalogo c'è**, nella lista di `03-b17` — ma `03-b17` **non è mai stato provato**,
> quindi la rete c'è **sulla carta e non nei fatti**.
>
> ⏳ **E i due punti che l'utente ha lasciato APERTI di proposito** stanno in
> [`fasi/03-movimento.md`](fasi/03-movimento.md), ciascuno con scritto **come si chiude**: il debito
> di chiave strozzato (si legge il registro della sessione del giudizio, **costa zero**) e *dove
> finisce di contare il tetto dei 50 ms* (si risponde **dopo** la misura in hardware).
>
> ---
>
> ### ⭐⭐⭐ DA QUI SI RIPRENDE — **13 agosto 2026, sera. LA FASE 3 HA IL SUO NUMERO, E SFORA** *(superato dal riquadro qui sopra)*
>
> *⛔ Scritto **a codice fermo**, con lo stato **verificato e non ricordato**. La fase 3 è stata
> divisa in **cinque step** su richiesta dell'utente, uno o due agenti per step, sviluppo + prova +
> correzione. ⏳ **La fase NON è chiusa**: manca la scrittura, non la misura.*
>
> #### ⭐ Il numero, che è quel che la fase esisteva per produrre
>
> **Ritardo cattura → vetro: mediana 74,58 ms** · p05 58,1 · p95 101,2 · p99 138,1 · errore
> d'orologio **±0,63 ms**. ⛔ **Pezzo cieco 16-40 ms NON compreso** ⇒ sullo schermo dell'utente
> **90-115 ms**, contro un tetto di **50**. ⇒ **SFORA i 50 e i 40.**
> ⚠ Non è input→vetro (`input` = 0 in 953 su 953): il canale di input nasce alla fase 4, e al suo
> posto c'è il controllo **P1**. Banco `03-b17-ritardo.py`, **31 controlli su 31**.
>
> | dove se ne va | mediana | di chi è |
> |---|---|---|
> | ⛔ **cattura → primo byte in pagina** | **39,17 ms** | ⛔ **nostro** — codificatore in software |
> | disegno → cattura | 16,66 ms | Mutter (**22 %**) — è un intervallo di quadro a 60 Hz |
> | richiamo → disegno finito | 10,51 ms | nostro |
> | decodifica | 7,58 ms | ⭐ **il 10 %, in software** |
> | il filo | 0,32 ms | — |
>
> ⭐⭐ **IL MURO NON È DI MUTTER, e la prova è che il figlio non lo aspetta mai**: zero attese a
> vuoto in 20 s. **58 ms su 74,6 sono nostri**, e quasi tutti nella codifica ⇒ **è la fase 8**.
>
> #### ⛔ QUATTRO RIGHE CHE TRE DOCUMENTI DANNO PER FATTE E CHE OGGI SONO SMENTITE
>
> 1. ⛔ **il muro dei 37 fotogrammi di Mutter NON SI RIPRODUCE**, e nemmeno i «sei decimi»: la
>    cella bassa dà **0,50 pulito e deterministico**. Con monitor a **120 Hz** e freno **90**: `[M]`
>    **61,4 fotogrammi/s, intervallo mediano 16,66 ms**. ⚠ **Il perché è `[R]`**: non un
>    **battimento** fra due orologi ma una **quantizzazione** letta nel codice di Mutter —
>    `min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) contro un tick da
>    16666,67 µs ⇒ chi cade sotto perderebbe un tick intero.
>    ⛔ ⚠ *Questa riga diceva «Legge verificata su **13 punti**, 8 confermano, **0 la smentiscono**».
>    **È falso**: `banchi/03-b14-esiti-griglia.jsonl` ha **due sole celle**, tutt'e due con
>    `scena_sul_mio_monitor: false`, e il banco stampa «la legge NON regge su 0 punti su 0».
>    Corretta il **13 agosto 2026**, rilievo del coordinatore della fase 3. ⇒ **M3 non è chiusa: è
>    mezza** (`gnome.md` §13);*
> 2. ⛔⛔ **ma quella cura NON è raggiungibile dal prodotto**: `MOVIMENTO_FPS 60` è una costante di
>    compilazione (`figlio.c:1465`), `main.c` non ha opzioni di cadenza, e **`RecordVirtual` non
>    prende la frequenza** (`mutter.h:82`) — i quattro monitor virtuali sono tutti **@60**. È `[M]`
>    sul banco e **zero in produzione**;
> 3. ⛔ **la motivazione prestazionale della FASE 10 (KDE) non regge più**: il piano la giustifica
>    con *«KWin consegna 60 dove Mutter ne dà 37 — è la strada per il traguardo dei 40 ms»*. I 37
>    non esistono e Mutter vale il 22 %: cambiare compositore **lascerebbe intatti i 39 ms di
>    codifica**. La fase 10 resta giusta come *«il secondo desktop»*; la promessa sul ritardo va
>    **riscritta o tolta**;
> 4. ⛔ **`web.md` §6.1 — «tutto in un worker dedicato» — è ATTUATA, MISURATA E RESPINTA**:
>    **+27,6/+33,5 ms** di mediana e **tetto −73 %** (127,6 → 33,9 dipinti/s a 1080p). ⭐ E il
>    meccanismo è nuovo: una `OffscreenCanvas` in un worker **si consegna al ritmo del quadro** —
>    è un `requestAnimationFrame` implicito che nessuno ha scritto. ⇒ Il divieto di §6.1 va esteso
>    **al meccanismo**, non alla sola parola. Il codice resta dietro `#video=worker`, **spento**.
>
> #### ⭐ Che cosa il prodotto sa fare adesso, e non sapeva stamattina
>
> **135 fotogrammi**, `numero` 1→135 · **132 delta e 3 chiavi** · il primo dopo `SESSIONE` è una
> **chiave** con FIN · `RICHIEDI_CHIAVE` → chiave in ≤200 ms · **10 stream azzerati contro 18 con
> FIN**, nessuna chiave abbandonata, **E8 provata sul filo** · **60,0 fotogrammi dipinti al secondo**
> offrendone 60, tetto a saturazione **127,6/s** · ⭐ nei 28 byte finisce il **`pts` di Mutter**,
> cioè l'istante **vero** della cattura (scarto dal nostro `CLOCK_MONOTONIC`: 11 347 µs).
> ⭐ **Sei dei sette punti del prodotto sono chiusi**, e il deposito è sparito del tutto: il prezzo
> dichiarato il 12 agosto — *«due utenti insieme non possono vedere tutt'e due il proprio»* — **è
> pagato**.
>
> #### ⛔ QUEL CHE MANCA PRIMA DI CHIEDERE IL GIUDIZIO — è scrittura, non misura
>
> 1. ✅ ~~**i documenti**: ~35 righe in **nove file**~~ — ⭐ **FATTO il 13 agosto, sera.** Il registro
>    è stato **portato dentro il deposito** (`fasi/rapporti/F3-righe-da-riscrivere.md`, 206 righe) e
>    le righe sono state riscritte in **quindici file**: `SPECIFICHE.md` · `DECISIONI.md` ·
>    `LEZIONI.md` · `PIANO.md` · `gnome.md` · `web.md` · `RCP.md` · `CODER.md` · `README.md` ·
>    `fasi/03-movimento.md` (le tre sezioni vuote riempite) · `fasi/00-ambiente.md` ·
>    `fasi/02-primo-fotogramma.md` · `fasi/rapporti/F2-6-giudizio.md` ·
>    `fasi/rapporti/P2-5-pagina.md` · `fasi/rapporti/F2-5-pagina.md`.
>    ⚠ **E toccare `RCP.md` fa scadere la certificazione di B9**: è previsto, e va rigirata insieme
>    alle altre (punto 2);
> 2. ⛔ **le certificazioni**: **10 su 15 sono scadute** perché `src/` è cambiato oggi, e i banchi
>    nuovi non sono a catalogo — ⚠ **SEI numerati** (`03-b14` · `03-b15` · `03-b16` · `03-b17` ·
>    `03-b18` · `03-b19`) **più tre** senza numero (`03-scena`, `03-marca`, `03-deposita`).
>    *⚠ Questa riga diceva «cinque banchi (`03-b14` … `03-b19`)» — **sei nomi per cinque banchi**,
>    e chi ricontava il catalogo ci andava a sbattere. Corretta la sera del 13 agosto 2026, contata
>    con `ls banchi/03-*`.* ⭐ Adesso si possono rigirare: la
>    pagina ha smesso di cambiare;
> 3. ⛔ **`src/pagina.c:243`**: `strcmp(percorso, "/")` confronta il bersaglio **con la stringa di
>    ricerca dentro** ⇒ `/?qualunque-cosa` prende **404** (`[M]`: `/` → 200/166107 byte,
>    `/?video=worker` → 404/9). ⇒ **`?tela=desincronizzata` non è MAI stato raggiungibile**, e il
>    commento della pagina indica da sempre una strada che non esiste. Non visto da nessuno perché
>    i banchi servono la pagina da un `http.server` di Python, che il `?` lo ignora;
> 4. ⚠ **la cura B-18 non è compilata né girata**: `rcp_video_niente_credito()` era l'unico dei tre
>    percorsi di abbandono di un delta a non accendere `serve_chiave` ⇒ **un solo delta saltato per
>    mancanza di posto sfasciava l'immagine per sempre e in silenzio** (il `numero` non è
>    consumato ⇒ nessun buco ⇒ il client non può chiedere la chiave; GOP infinito ⇒ non ne arriva
>    più una da sola). ✅ I due gemelli `rcp.c` **sono stati riallineati stasera** — divergevano, e
>    il prodotto **non compilava per nessuno**;
> 5. **il giudizio dell'utente**: il desktop che si muove dentro una scheda.
>
> ⚠⚠ **E UN RISCHIO DI CASA, misurato la sera del 13 agosto: `/tmp` è una tmpfs da 3,8 G al 94 %**,
> **246 M liberi**. Ha già fatto fallire un giro di `03-b16` (Chrome non parte). ⛔ **Non è stata
> svuotata di proposito**: dentro ci sono le prove dei giri di oggi — `/tmp/03-b17` (155 M, col
> `verbale.json` dell'anello del ritardo), `/tmp/03-b19-dipinti` (128 M), `/tmp/remotix-f26-*`
> (288 M) — e buttarle toglierebbe la **provenienza** dei numeri di questo riquadro. ⇒ **Si guarda
> prima di cancellare**, e si comincia da `/tmp/claude-1000` (1,1 G) e `/tmp/google-chrome`
> (227 M), che prove non ne portano.
>
> #### ⭐⭐ E la lezione del metodo, che stavolta ha un conto
>
> **Gli agenti mandati a REFUTARE hanno rifiutato CINQUE cure passate dal coordinatore, e avevano
> ragione tutte e cinque**: la `ResizeObserver` (la premessa era falsa) · la seconda cura della
> vista (caduta alla misura: `overflow-y: scroll` tiene `clientWidth` fermo) · il seqlock in
> contesa (**200 letture su 200 riuscite**: la causa era un relitto a `seq` dispari) · *«quel che
> manca ai 60 è di Mutter»* (**zero attese a vuoto**) · *«accendi su `Meta-3`»* (i monitor sono
> **quattro**, il suo era `Meta-2`: avrebbe misurato il palco di un altro gruppo).
> ⛔ **E un difetto che sembrava del prodotto era del BANCO**: il `STREAM_LIMIT_ERROR` nasceva da un
> banco che annunciava il credito **dopo** la stretta di mano — cosa che l'RFC vieta — e poi accusava
> il prodotto di non reggerlo. `ngtcp2` non aveva violato niente. ⭐ Ma cercandolo è uscito **B-18**,
> che era vero e peggiore.
> ⛔ **E un verde in catalogo lo produceva lo STRUMENTO**: `02-pagina-vista-prova.py` passava solo
> grazie a `Page.captureScreenshot`, chiamata da un'opzione di stampa (`--copia`); senza, lo stesso
> banco sul prodotto **sano** dava **5 pretese rosse** — e quelle quattro pretese non erano **mai
> state innestate con un guasto**. Curato, e adesso **si giudica prima il palco**.
>
> ---
>
> ### ⭐⭐⭐ DA QUI SI RIPRENDE — **13 agosto 2026, a fase 2 chiusa**. ⇒ **LA PROSSIMA SESSIONE FA LA FASE 3** *(superato dal riquadro qui sopra)*
>
> *Deciso dall'utente: «la prossima sessione si occuperà della fase 3». ⛔ Questo riquadro è scritto
> **prima** di chiudere e **a codice fermo**, con lo stato **verificato e non ricordato** — è la
> lezione che questa giornata è nata applicando, e che è stata mancata tre volte (11 agosto, 12
> agosto, e stamattina alle 09:57).*
>
> **Lo stato, verificato adesso:**
>
> | | |
> |---|---|
> | ⭐ **albero** | pulito, `47e006e` |
> | ⭐⭐⭐ **la fase 2** | **CHIUSA** sul giudizio dell'utente ⇒ [`fasi/rapporti/GIUDIZIO-13-agosto.md`](fasi/rapporti/GIUDIZIO-13-agosto.md) |
> | ⭐ **il catalogo** | **15 su 15**, e ⭐ è il conto del **progetto**: le due copie unite e rispecchiate, 90 giri. ⚠ **Ricontrollalo lo stesso** con `python3 banchi/01-b12-guasti.py --registro`: la fase 3 toccherà `rcp.c` e la pagina, e ⛔ **curare il prodotto fa scadere le certificazioni che lo guardavano** |
> | ⚠ **i server accesi su NIC-OS** | **7448** (prodotto di casa) · **7501** (bersaglio di P5) · ⭐ **7561**, **quella che l'utente apre** — e la 7561 è anche **il bersaglio del metro**: si legge, non si tocca. Verificato: sono le sole tre `:7xxx` in ascolto |
> | ⏳ **la sola scadenza** | `bash banchi/01-s1b-eccezione.sh oggi`, **una volta al giorno fino al 18 agosto**. Ultimo giro: 13 agosto ore 08:08, **2,46 giorni su 7** |
>
> #### ⛔ Le tre cose da decidere PRIMA di scrivere la fase 3
>
> 1. ⛔⛔ **La risoluzione della tela.** `1920×1080` è **ereditato dalla scena di un banco, senza
>    decisione né misura**; in v1 era `2560×1080`. ⭐ E adesso ha un numero addosso: sullo schermo
>    dell'utente il desktop è dipinto all'**86%**, cioè **912 px di nero**. ⇒ **È la tela di tutte le
>    fasi che vengono dopo: prima si decide, meno costa.** Decisione dell'utente, non un rilievo;
> 2. ⛔ **La scena si dichiara e si muove sempre** — `PIANO.md` fase 3: *«un client a schermo intero
>    che ridisegna a ogni richiamo del compositore»*. ⚠ **Tutte le misure di ritmo delle fasi 3-9 di
>    v1 sono state buttate per questo** (`LEZIONI.md` §1.1). Si sceglie la scena **prima** di scrivere
>    il banco;
> 3. ⚠ **L'attesa dichiarata in anticipo**: su GNOME il traguardo dei **40 ms** probabilmente **non si
>    raggiunge**, per il muro dei 37 fotogrammi di Mutter. Il numero da battere è **≤ 50 ms**
>    (`SPECIFICHE.md` §3.2). Se la misura lo confermasse **non è un difetto nostro** — ed è una
>    ragione in più per la fase 10.
>
> #### ⭐ Che cosa la fase 3 eredita, e che le morde addosso
>
> - ⛔ **P15** — `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto dove un
>   orologio decide**. La fase 3 è tutta tempo: è lì che si scoprirà se regge;
> - ⛔ **il metro non guarda a monte della cattura**, e con molti fotogrammi il punto cieco si allarga:
>   **M6** («il fotogramma è del giro prima») è l'unico che vede quel guasto, e ⛔ **non è mai stata
>   misurata sulla catena vera** perché manca la cattura del giro precedente. In fase 3 i giri
>   precedenti ci sono: **si può chiudere**;
> - ⛔ **«due utenti, ciascuno vede la propria sessione»** non lo copre nessun banco (metà positiva
>   scoperta). Con il movimento diventa più caro sbagliarlo, non meno;
> - ⚠ **M8 ha un controllo dichiarato NON APPLICABILE** (`giro`): il prodotto non conosce il nome del
>   giro del banco. In fase 3, con un contatore `numero` che cresce a ogni fotogramma, **si può
>   riaprire** — ⇒ `fasi/rapporti/F2-6-giudizio.md`. ⭐ **FATTO il 13 agosto**: la dichiarazione
>   *«non applicabile **per costruzione**»* **cade**, ed era il «per costruzione» a essere sbagliato;
> - ⚠ **`02-figlio-accendi.sh:165`** conta i figli **di tutti** invece dei propri: si accende solo
>   quando due banchi girano in parallelo, e in fase 3 gireranno. ✅ **Curato il 13 agosto** — ⛔ `[R]`,
>   **non eseguito**: la cura è letta nel codice e non è stata girata.
>
> #### ⚠ E due cose sul metodo, che hanno prodotto il risultato migliore di oggi
>
> ⭐⭐ **Gli agenti si mandano a REFUTARE, non a verificare.** La riga su cui stavo per chiedere il
> giudizio — *«12 guasti su 12, non ha più punti ciechi»* — è stata **refutata** da un agente mandato
> a smentirla: uno dei dodici era **verde per costruzione**. Un agente mandato a *verificare* avrebbe
> letto la stessa riga e confermato.
>
> ⭐ **E il mandato deve ammettere il rifiuto.** La cura che avevo passato io (*«leggi `azzerati`»*)
> era **sbagliata**, e chi curava l'ha rifiutata con un caso: avrebbe prodotto un **falso rosso**,
> che accusa il prodotto — peggio del falso verde che sostituiva.
>
> ---
>
> ### ⭐⭐ DA QUI SI RIPRENDE — **13 agosto 2026**, mattina *(superato dal riquadro qui sopra)*
>
> ⭐⭐⭐ **La fase 2 consegna: l'utente ha visto il proprio desktop dentro una scheda del browser**,
> a schermo pieno, e ha detto *«è lo sfondo GNOME, è OK»*. La storia sta in
> [`fasi/02-primo-fotogramma.md`](fasi/02-primo-fotogramma.md), che è **il documento da leggere per
> primo** insieme a questo riquadro.
>
> **Lo stato, verificato prima di scrivere** (albero pulito, `ec646d5`):
>
> | | |
> |---|---|
> | ⭐ **il metro della fase** | ha girato **sulla catena vera del prodotto** — cattura di Mutter → codifica → filo → `VideoDecoder` → `getImageData`, **con la mira di F2.6 messa a sfondo del desktop** — e dice **PROMOSSO**: piano 1 (browser ⟷ `ffmpeg` sullo stesso flusso) **PSNR-Y 62,09 dB**, soglia 45, **12 guasti su 12** e zero ciechi. ⛔ **E vanno dette tre cose accanto**, o la riga dice più della misura ⇓ |
> | ⛔ **1 — sul TUO desktop il metro dice BOCCIATO** | scena naturale, `cura-desktop-vero-20260813-103246`: **58,62 dB**, rosso su **M5**, e **8 guasti su 12** — senza la mira, M4, M7 e i marcatori di M-V si spengono. ⇒ *Il verde è del metro **con la mira**; sul desktop nudo il metro vede meno e trova un rosso.* ⛔ Il rosso **non è stato curato: è sparito quando è cambiata la scena** |
> | ⭐ **2 — «12 su 12» adesso è vero, e stamattina non lo era** | vuol dire **«nessuno strumento spento»**, non «dodici guasti innestati sul prodotto»: sul prodotto ne sono innestati **tre**. ⛔ **E uno dei dodici era verde per costruzione** — M8 leggeva un contatore `reset` che la pagina chiama `azzerati`, quindi **valeva sempre 0**. Erano **11 vivi più un verde vuoto**. ⭐ Curato e ricertificato il 13 agosto (0 → 1 → 0, col controllo del **falso rosso** accanto): ⇒ `fasi/rapporti/F2-6-giudizio.md` |
> | ⛔ **3 — il metro non guarda A MONTE della cattura** | il suo fondo di verità è **il buffer che il prodotto stesso ha catturato**: quale monitor, quale sessione, **quale utente** sono fuori dalla sua portata. ⇒ Se il prodotto catturasse il desktop di un altro utente, **il metro direbbe 62 dB e promosso** — ed è il difetto **numero 1** che l'utente ha trovato in una mattina. Lo copre `02-figlio-prova.py`, **rigirato il 13 agosto: 9 misure, 9 uscite 0** — ⛔ ma solo per **metà**: vedi le `[?]` |
> | ⭐ **il catalogo** | **14 su 15** `[M]` 13 agosto, `01-b12-guasti.py --registro`: ⭐ **B9 ricertificato alle 10:06** sul testo di `RCP.md` uscito dalle cure P20-P21-P22 (0 → 3 → 0, marca vista nel rosso e assente nel verde). ⛔ **Resta P5R**, e la causa è dichiarata: l'ha fatto scadere **la cura del riscalamento** delle 08:56, che ha cambiato `remotix/pagina.html`. ⚠ **E il conto è quello di QUESTA copia**: l'unione col server è ferma alle 02:29 e da allora c'è un giro nuovo di qua — si rimette con `--unisci-col-server --rispecchia`. ⚠ *Questa riga diceva «13 su 15, restano B9 e P5R»: era vera alle 09:57 ed è scaduta alle 10:06 (R13.3)* |
> | ⚠ **i server accesi su NIC-OS** | **7448** (prodotto di casa) · **7501** (bersaglio di P5) · ⭐ **7561**, che è **quella che l'utente apre** — gira **da root** (`banchi/02-figlio-accendi.sh`), e serve la pagina col riscalamento (`adatta_vista` **3**, verificato col conteggio). ⭐ `[M]` 13 agosto, ricontrollato: **34 file su 34** identici fra `src/` e l'albero del server, `pagina.html` **byte identica**, e ⛔ `/proc/…/exe` punta al binario **vero** — non a un `(deleted)`, che è la trappola già pagata due volte |
> | ⏳ **la sola scadenza** | `bash banchi/01-s1b-eccezione.sh oggi`, **una volta al giorno fino al 18 agosto**. Fatto il 13 alle 08:08: **2,46 giorni su 7**, canale certificato, **4 controlli su 4**, e il profilo nuovo vede ancora l'avviso. ⚠ *Questa riga diceva «2,04», che è il giro del **12 sera**: il numero era stato copiato da un giro che non era quello che la frase nominava (R13.4)* |
>
> #### ✅ Che cosa mancava per chiedere il giudizio — **fatto il 13 agosto, mattina tardi**
>
> ⭐ **Il catalogo è pieno: 15 su 15**, e ⭐ **è il conto del progetto, non di una copia** — le due
> copie del registro sono state unite e rispecchiate (90 giri, *nessuna riga persa, nessuna
> inventata*, verificato contando riga per riga). ⛔ Finché l'unione non era fresca, quel numero era
> «il conto di questa copia», e il `README` lo presentava come **il** numero.
>
> ⇒ Adesso si chiede *«questo vale come primo fotogramma?»* — ⛔ **e insieme al verde vanno dette
> tre cose**, o il giudizio è preso su metà quadro:
>
> 1. **il piano 2 del metro non è applicabile** e lo dichiara — cioè **la catena intera, pagina ⟷
>    cattura, non è stata giudicata**. Il numero grezzo c'è ed è **54,11 dB**; a mancare è il margine
>    che lo rende leggibile: la perdita del codificatore (**55,08 dB**) deve stare **10 dB sotto** il
>    rumore della tela a 8 bit (**62,09 dB**), e ne sta 7,01. ⚠ *Questa riga diceva «la codifica perde
>    **meno** della tela», ed è **invertita**: PSNR più alto vuol dire errore più piccolo, quindi la
>    codifica perde **più** della tela — solo non abbastanza (R13-M.6). La frase giusta era di un
>    altro giro, quello del 12 agosto a QP 20, e si era portata avanti senza rifare il conto.*
>    ⛔ **E c'è un difetto nello strumento, dichiarato**: il messaggio che finisce negli esiti dice
>    *«non è almeno **6 dB** sotto la prima»* mentre il codice usa **10** (`02-giudizio-metro.py:610`);
> 2. ⛔ **i dieci bit sono otto promossi**, e lo sono **a tutt'e due i capi** — `DECISIONI.md` §2.3-ter
>    (Mutter non li dà per nessuna strada) e la misura sul telefono (`copyTo` riuscito, 4 byte per
>    pixel);
> 3. ⚠ **il telefono è stato misurato, ma non sull'hardware** — e la differenza conta. `[M]` 13
>    agosto, **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte**, HEVC Main10
>    e AV1 10 bit. ⛔ **Quel che NON ha risposta è «lo decodifica il silicio o la CPU?»**: senza cavo
>    dati non si legge `Created MediaCodec <nome>`, e il criterio A/B esce `valido: false` perché
>    misura **spesa fissa**. `[?]` dichiarata, e più stretta di com'era scritta.
>
> #### ⚠ Le `[?]` aperte, dichiarate e non curate
>
> ⛔⛔ **La più grande, e non era dichiarata da nessuna parte fino a oggi: «due utenti con due
> sessioni vere, ciascuno vede LA PROPRIA» non lo copre nessun banco.** `[M]` 13 agosto:
> `02-figlio-prova.py` prova **la metà negativa** — `prova` (uid 1001, tutti e quattro i campi chiesti
> **al nucleo**) non vede il desktop di `nicfio`, e un cliente RCP indipendente conta **zero**
> fotogrammi dove il 12 agosto ne contava uno conforme. ⛔ **Ma la metà positiva no**: su quella
> macchina `prova` non ha mai fatto login, quindi **un prodotto che non consegnasse niente a nessuno
> passerebbe allo stesso modo**. ⚠ `01-b10-secondo-utente.py`, `attrezzi-prova2.sh` e `02-pam-i3.py`
> si fermano tutti **all'autenticazione**, non al vedere.
>
> **M5** — uno scarto di **crominanza fra due decodificatori** (0,9791 contro un limite di 0,98): è
> **l'unico rosso rimasto su catena sana**, ⛔ **non si riproduce sulla mira**, e **la soglia non è
> stata allargata**. ⚠ *Diceva «l'unico rosso mai uscito dal metro», ed è più largo della misura: ai
> giri delle 09:19-09:20 erano rossi anche **M0 e M1** (33,03 dB contro una soglia di 45), ed erano il
> difetto dell'immagine piccola, poi curato (R13.12).* · **P15** (`RCP.md` §7.1, il secondo di grazia
> sulle coordinate: l'ultimo posto dove un orologio decide) · **la risoluzione del desktop**,
> `1920×1080`, ⛔ **ereditata dalla scena di un banco senza decisione né misura** — e in v1 era
> **2560×1080**. ⚠ Le tre stanno adesso anche in `fasi/02-primo-fotogramma.md`, §«Che cosa resta
> `[?]`», che è dove chi riprende le cerca.
>
> #### ⭐ Le due lezioni nuove, e valgono più del codice
>
> **`LEZIONI.md` §1.13** — *una tolleranza si scrive sulla **grandezza vera del fenomeno**, o si sposta
> di un passo a ogni rilettura*, ⭐ **e l'elenco delle eccezioni è parte della tolleranza**: la
> successione intera sta là, e qui non si ricopia. · **§1.14** — *un controllo che accetta «una delle
> due strade» nasconde una strada rotta per sempre*.
>
> ⚠ *Questo riquadro portava la successione a sette e §1.13 — che è **la fonte** — diceva ancora
> «quattro volte» e dava P14 per una cura che regge. ⛔ Il rimando mandava a una sezione che
> **contraddiceva chi la citava**: si è aggiornata la fonte, non i due che la citano (R13.6).*
>
> ⭐⭐ **E la cosa che questa sessione ha dimostrato meglio di ogni numero**: i **tre** difetti più
> gravi della giornata li ha trovati **l'utente in una mattina**, e nessuno dei 518 file di banco li
> vedeva — il desktop di un altro utente, la pagina che restava vuota, l'immagine grande come un
> francobollo. ⇒ `CODER.md` **I8** non è una frase: *il metro è quel che l'utente vede*.
>
> ---
>
> ### ⭐ DA QUI SI RIPRENDE — **12 agosto 2026**, notte
>
> **Lo stato**: albero pulito (`636f088`), **14 banchi su 14 certificati e valgono oggi**, terreno
> dell'innesto `14 su 14`. ⚠ Su NIC-OS restano accesi **due** server, e sono voluti: il **prodotto
> di casa sulla 7448** (riavviato stanotte sul binario giusto) e il **bersaglio di P5 sulla 7501**.
> Le porte **7447** e **7481** sono libere. Nessun giro in corso, su nessuna delle due macchine.
>
> ⏳ **La sola cosa con una scadenza**: `bash banchi/01-s1b-eccezione.sh oggi`, **una volta al
> giorno fino al 18 agosto**. L'11 era stato saltato e recuperato in extremis (giorno 1.00 su 7);
> ⛔ non si rigenera `/media/REMOTIX/s1b-certificato/` né si cancella `~/.remotix-s1b/`.
>
> **Quel che resta, e non è stato deciso** — i punti 4-7 dell'elenco della notte:
>
> | | | dov'è finito |
> |---|---|---|
> | **4** | `01-b12-lancia.sh` ha `PORTA=7447` e `bsslserver` in chiaro: non si può puntare sul prodotto, e per questo B13 si certifica **solo** dal suo script «sera», mentre P1 e P5 stanno fuori dall'orchestratore | ⏳ **aperto**, difetto **D6** |
> | **5** | il guasto di P5 copre **meno** di quel che promette: la pagina ritira `/impronta` prima di ogni tentativo, quindi l'impronta falsa non uccide la sessione. Per coprire davvero **R1.14** serve un guasto che colpisca **il ritiro** | ✅ **chiuso** il 12 agosto, difetto **D11**: il guasto nuovo toglie **il ritiro**, e la prova che guarda un'altra cosa è che col guasto dentro **il controllo vecchio resta verde** |
> | **6** | i buchi **dichiarati**: `B13.3` (i certificati li fa un banco, non il codice), `B13.5` (il trasporto concede tutti gli stream chiesti), e il `[?]` di **B8** su `pam_faildelay` | ⏳ **aperti**, e dichiarati tali |
> | **7** | i due ripieghi di fase: **un filo solo** con la verifica PAM che lo blocca, e il tetto di **16 sessioni in compilazione** dove la regola ne vuole dieci configurabili | ✅ **decisi dall'utente** l'11 agosto — `DECISIONI.md` §1.10 e §1.11. ⚠ *Questa riga li dava per non decisi, ed era già scaduta quando è stata scritta* |
>
> ⚠ **E una cosa sul metodo, da chi ha tenuto la tastiera**: la trappola *«mai una redirezione
> **attorno** a `enter.sh`, o si mangia la richiesta di password di `sudo`»* — già in catalogo,
> `fasi/00-ambiente.md` B3.3 — è stata ripetuta **due volte nella stessa notte**, e la seconda è
> costata venti minuti di attesa su una compilazione che non stava compilando niente. ⇒ Vale la
> pena renderla impossibile invece di ricordarsela.
>
> ---
>
> ### ⭐⭐⭐ P5 È CERTIFICATO — la notte fra l'11 e il 12 agosto 2026, **0 → 1 → 0**
>
> *I tre giri della certificazione sono stati fatti per intero contro la copia curata sulla **7501**,
> con i browser su CHUWI e il prodotto su NIC-OS — cioè con il filo attraversato davvero.*
>
> | | |
> |---|---|
> | ⭐ **il giro sano: VERDE su tutt'e due i motori** | n1 giusta/storpiata `ok`, `n2-parola-sbagliata` **11 controlli 0 guasti**, `p-sessione` **15 controlli 0 guasti**, su Chrome **e** su Firefox |
> | ⭐ **il giro col guasto: ROSSO, e nomina la cosa giusta** | *«la pagina pubblica «AAAA…=» e l'endpoint dice «PJ03…=»: sono due impronte diverse per lo stesso certificato di sessione»* — il difetto **R1.14** di `RCP.md` §4.1-bis |
> | ⭐ **e la marca è una marca**: `[M]` compare **0 volte nel sano, 1 nel guasto, 0 nel risanato**, contate sui tre giri di quella notte — non su una misura di ieri |
> | ⭐ **il giro risanato: VERDE**, e il binario è tornato **identico byte per byte** | `d69df441…` → `117911ca…` → `d69df441…`: che il guasto sia entrato e poi uscito lo dice l'impronta del binario, non il colore del verdetto |
>
> ⛔ **E il guasto dimostra meno di quel che il suo titolo dice — va letto prima di credere alla
> riga sopra.** Con l'impronta falsa nella pagina, le gambe `p-sessione` restano **CONFORMI**: la
> sessione WebTransport **si apre lo stesso**. ⭐ La ragione è del prodotto, ed è §4.1-bis applicato:
> `pagina.html` **ritira `/impronta` prima di ogni tentativo** e usa quella, tenendo l'impronta
> servita solo come ripiego — e quando le due divergono **lo dice**. ⇒ Il guasto prova che **P5 vede
> la divergenza**, che è ciò per cui P5 esiste; **non** prova che la divergenza uccida la sessione,
> perché su questo prodotto non la uccide.
>
> ⛔ **E il primo tentativo di giro sano è uscito ROSSO con tutt'e quattro le gambe CONFORMI**: il
> registro del server aveva un buco di **37.120 byte NUL** — `svuota-registro` chiamato con il server
> vivo — e `grep`, diventato cieco, leggeva «NON LETTO» dove c'era il nostro indirizzo, mandando lo
> sblocco di §4.4-bis **sul server stesso**. Tre cure, tutte rimisurate; la lezione sta in
> `LEZIONI.md` §1.9 punto 9.
>
> **Come si rifà**, se serve rieseguirla:
>
> ```
> # il bersaglio: una COPIA del prodotto, porta 7501, ban e socket suoi
> bash /media/REMOTIX/enter.sh --root "bash /srv/src/01-p5-accendi.sh accendi"
>
> # il giro, DA CHUWI (i browser stanno di qua)
> SSH_ROOT="python3 v1/strumenti/sshpw.py" \
>   IND=192.168.0.2 PORTA=7501 SOCK=/srv/src/tmp/sera-p15.sock \
>   LOG_SERVER=/media/REMOTIX/src/tmp/sera-p15-browser.log \
>   SCHERMO=:79 PORTA_LOC=8859 bash banchi/01-p5-lancia.sh
> ```
>
> ⛔ **Fra un passo e l'altro ci vanno DUE cose, non una**: `costruisci.sh` sulla copia **e** il
> server riacceso su quel binario. P5 non ricostruisce da sé — trova un server acceso e lo interroga
> — quindi saltarne una lo farebbe misurare il binario di prima **con l'aria di aver innestato**.
> ⚠ Se manca la copia, `01-p5-accendi.sh copia` la rifà e la ricostruisce (`GEMELLO=/srv/src/rcp`);
> ⛔ e **non si usa `copia` per rifare il binario dopo un innesto**, perché ricopia dal prodotto e
> il guasto sparisce senza dirlo.
>
> #### ⭐⭐ IL PRODOTTO ESISTE: `src/`, il server della fase 1 in C
>
> ⚠ *Questa pagina, e il documento della fase, dicevano* «**nessuna riga di prodotto scritta**» *fino
> all'11 agosto 2026 — mentre `src/` era nato la notte del 10 e nessuno dei dieci documenti lo
> nominava (rilievo **R12C.1**). Chi riprendeva il lavoro leggeva quella riga e **riscriveva da zero
> un server che esiste.***
>
> `[M]` **11 agosto 2026** (`wc -l`, codice fermo alle 00:36): **22 file**, **9.647 righe**, di cui
> **5.248 di codice**. ⭐ **La stretta di mano di RCP/1 arriva fino a `SESSIONE` con un browser
> vero** — con i due certificati di §4.1-bis, il ban di §4.4-bis su file e il suo comando di
> sblocco. ⛔ Niente video, niente audio, niente input: quelle sono le fasi da 2 in poi.
> ⚠ *Questa riga diceva* «**un browser vero apre `https://192.168.0.2:7447`**, l'utente digita nome
> e parola d'ordine … **la pagina servita dal server stesso**», *e il registro di quel giro non ne
> regge tre pezzi: il browser stava **sulla stessa macchina del server**, la pagina **non l'ha
> servita il prodotto** (`GET /` zero volte su 48 righe), e la porta era la **7448** — la 7447 è
> dell'innesto. Corretta l'11 agosto 2026; il conto per esteso è nella tabella qui sotto.*
> **Il dettaglio, file per file, sta in `fasi/01-filo-nudo.md` §«Che cosa è stato sviluppato».**
>
> ⛔ **E quel che NON è provato, che è la metà che non si vede:**
>
> | | |
> |---|---|
> | ⛔ **UN SOLO MOTORE** | l'unica traccia di un giro con un browser vero contro questo server è un commento dentro `src/pagina.html` — `[M]` 10 agosto notte, **Firefox** — e quel giro ha trovato un difetto vero (la pagina dichiarava `disposizione = en`, che non è un nome XKB). ⛔ **Di Chrome contro questo server non c'è nessuna traccia**, e il criterio di B2 vuole **due motori su due** |
> | ⛔⛔ **e quel giro è MENO di quel che questa pagina diceva** | `[M]` **11 agosto 2026**, letto in `/media/REMOTIX/src/remotix-browser.log` (48 righe) e ricontato a mano. ⭐ **Quel che regge**: la stretta di mano arriva davvero fino a `SESSIONE` — `sessione aperta utente=prova … tela=1920x1080 vista=1152x836 disposizione=us`, e la vista dispari dice che a chiedere era una finestra vera. ⛔ **Quel che NON regge, e sono due cose**: *(1)* tutte e **19** le connessioni vengono da `[192.168.0.2]`, cioè **dal server stesso** — il giro **non ha attraversato la rete**, e questa pagina lo raccontava come un browser che apre un indirizzo da fuori; *(2)* **`GET /` compare ZERO volte** e `GET /impronta` una: ⛔ **la pagina non l'ha servita il prodotto**. Il secondo mestiere del server della fase 1 — *servire la pagina*, `PIANO.md` fase 1 — **non è misurato da nessuna parte** |
> | ⚠ **e in quel giro il client non si è congedato** | il posto se n'è andato con `STACCATO per silenzio: 30269 ms … (posti occupati adesso: 0)`. ⛔ A liberarlo è stato **l'orologio**, non un congedo: un banco che aspettasse cinque secondi scriverebbe «il posto non si è liberato» su un server che stava per liberarlo |
> | ⛔ **e quel giro non è riverificabile** | `[M]` 11 agosto: in `src/` non c'è né il binario né un `.o`, nessun `.jsonl`, e `git status` la dà **untracked**. ⛔ **Nessuno dei 14 script di lancio accende il prodotto**: `bsslserver` compare in **11** di loro, il binario `remotix` in **zero** |
> | ⛔ **il server intero non l'ha eseguito nessun revisore** | mancavano `ngtcp2`, `nghttp3`, `libssl-dev`, `libpam0g-dev`: `trasporto.c`, `webtransport.c`, `pagina.c`, `certificati.c` sono **letti, non misurati**. ⭐ L'unica esecuzione è `rcp.c` **compilato isolato**, `-Wall -Wextra`, **zero avvisi**, sei ingressi byte per byte |
> | ⛔ **le proprietà di trasporto non sono state rimisurate su di lui** | le sei di B2 sono `[M]` **sull'innesto**. Il prodotto oggi dichiara **19** stream unidirezionali dove la misura ne leggeva 16 |
> | ⛔ **due ripieghi di fase, dichiarati** | **un solo filo**, e la verifica PAM lo **blocca**: dieci utenti che entrano insieme fanno aspettare l'ultimo dieci secondi (`SPECIFICHE.md` §5.5 promette dieci sessioni). E **16 sessioni attaccate in compilazione**, dove il tetto è dieci configurabile |
>
> #### I banchi: **dodici scritti**, sei verdi, ⛔ **e TRE certificati**
>
> **Dodici banchi scritti** — `[M]` 11 agosto 2026, contando i prefissi distinti in `banchi/`:
> `01-b2 · b3 · b4 · b5 · b6 · b7 · b8 · b9 · b11 · b12 · b13 · c2`. ⚠ *Questa riga diceva «**otto**
> banchi scritti»: quattro erano nati la notte del 10 e nessuno li aveva aggiunti — rilievo
> **R12C.13**.*
>
> **Sei verdi**: B2 · B3 (cinque giri su cinque) · B4 (13 su 13, quattro esiti) · B5 (36 violazioni
> su 36 + 8 verdi attesi) · B7 (**7 motivi provocabili su 7, denominatore 15, e 15 frasi distinte**) ·
> B11 (13 casi su 13 sui due motori).
> ⭐ **B6 non è più giallo, e non è ancora verde**: ha chiuso R3.27 con **due** risposte (vedi sotto),
> e usciva **3** — *«il filo si comporta come il codice dice, e il documento dice un'altra cosa»*.
> ⛔ Adesso il documento è cambiato: **va rieseguito**, ed è la sola cosa che dirà se sia verde.
> ⚠ **B8 non ha finito**: le tre mediane restano da confrontare.
> ⭐ **E i quattro nati la notte del 10**: **B9** (il secondo lettore, che ha prodotto **dodici**
> punti in cui `RCP.md` ammette due letture), **B12** (la certificazione), **B13** (le sei proprietà),
> **C2** (le tre diagnosi) — più le **sette pagine della sonda**.
>
> ⛔ **E il conto onesto delle certificazioni è 3 su 12**, non sei e non quattro: *«verde»* vuol dire
> che il banco ha girato senza trovare niente, *«certificato»* che qualcuno gli ha **rotto sotto il
> codice** e lui è diventato rosso sulla marca giusta.
>
> ⚠ **E i due «dodici» NON sono lo stesso dodici, o questa riga sarebbe un conteggio senza
> denominatore**: i dodici *scritti* sono i prefissi in `banchi/`; i dodici del **catalogo di B12**
> comprendono **B10** — che non ha uno script suo — ed escludono **B12**, che non certifica sé stesso.
> Il conto qui sotto è sul catalogo di B12.
>
> | | |
> |---|---|
> | ⭐ **certificati** | **B4**, **B9** (11 ago 00:27, con le impronte dei file che partecipano) e **C2** (10 ago 22:32) — ⚠ su B9 con una riserva scritta: il suo guasto dimostra che sa vedere **un testo cambiato**, che è la cosa che B9 dichiara di saper fare |
> | ⛔ **provato e NON certificato** | **B13** — e il difetto è del **guasto**, che l'orchestratore non sa innestare e che costruirebbe un difetto che B13.1 non guarda |
> | ⚠ **certificato e NON riverificabile** | **B7** — la marca pretesa era la parola `CONGEDO`, che il banco stampa anche nel giro **sano**: *«una marca che compare in tutt'e due i giri non è una marca»* |
> | ⛔ **mai provati** | **B2 · B3 · B5 · B6 · B8 · B10 · B11** — sette |
>
> ⇒ Il registro è `banchi/01-b12-registro.jsonl`, e il conto per esteso sta in `fasi/01-filo-nudo.md`.
>
> #### ⭐ La regola dell'accesso è cambiata, e l'ha decisa l'utente — 10 agosto 2026
>
> ⛔ **Tre autenticazioni fallite dallo stesso indirizzo ENTRO 5 MINUTI, e quell'indirizzo è fuori
> per 12 ore.** Il **nome utente non conta**: tre nomi diversi contano tre. Un accesso riuscito azzera
> il conto; il ban **sta su file** e sopravvive al riavvio; si esce con le dodici ore **o** con un
> comando di sblocco sul server. Chi è bannato **vede una pagina che glielo dice**, non un silenzio.
>
> > ⚠ *Questa riga diceva* «tre autenticazioni fallite **consecutive**», *senza finestra —
> «consecutive» era la **prima** formulazione dell'utente, e la finestra dei cinque minuti è una
> **terza** frase dello stesso giorno che la stringe. ⛔ Le due regole danno **esiti opposti sullo
> stesso ingresso**: tre fallimenti alle 0:00, 4:00 e 8:00 sono consecutivi ⇒ bannati secondo questa
> riga, e **fuori finestra** ⇒ non bannati secondo il codice. La finestra c'era in `DECISIONI.md`, in
> `RCP.md` §4.4-bis, in `SPECIFICHE.md` §4.2 e nel codice, e mancava **nei due documenti da cui si
> scrive il banco**. Corretta l'11 agosto 2026, rilievo **R12C.5** — ed è successo perché la
> decisione era **copiata** in quattro documenti invece che rimandata, che è proprio quel che le
> convenzioni qui sotto vietano.*
> ⇒ `DECISIONI.md` §1.9 — e con essa `RCP.md` §4.4-bis (da 🔸 a ✅), `SPECIFICHE.md` §4.2,
> `fasi/01-filo-nudo.md` B0.3 e B8.
>
> ⭐ **Sostituisce la forma che avevo scritto io** — 5 in 5 minuti, finestra che raddoppia fino a 15
> minuti, due contatori — e ⛔ **il filo non guadagna un byte**: `TROPPI_TENTATIVI` esisteva già.
> ⚠ **Il prezzo è dichiarato in §1.9** e non lo paga chi indovina: dietro un NAT tre errori di una
> persona chiudono la porta a tutti per dodici ore, e il primo a inciamparci è chi digita una parola
> lunga sulla tastiera di un telefono.
>
> #### ⛔⭐ IL PRIMO PASSO DELLA PROSSIMA SESSIONE: **puntare i banchi al PRODOTTO**, e trovare un secondo motore
>
> *(B8 è stato riscritto la notte del 10 agosto sulla regola nuova — tre falliti con tre nomi
> diversi, il quarto con la parola giusta che DEVE essere rifiutato, più i controlli che dicono *no*.
> Quel passo è fatto; questo è il prossimo.)*
>
> ⛔ **Oggi ci sono due server, e i banchi ne misurano uno solo.** Il prodotto è `src/`; l'innesto è
> `banchi/01-b3-rcp-innesta.py` dentro `bsslserver`, ed è quello che tutti i 14 script di lancio
> accendono. ⛔ **Il protocollo è lo stesso file** — `src/rcp.c` e `banchi/rcp/rcp.c` sono identici
> byte per byte — **ma tutto quel che gli sta attorno è stato scritto due volte**, e nei punti in cui
> le due stesure divergevano una portava scritta la dimostrazione che l'altra non funzionava.
>
> ⚠ **E il rischio è preciso, non generico**: la prima volta che qualcuno punterà un banco al
> prodotto — cosa che prima o poi si farà, perché è il prodotto — otterrà **rossi su un server che le
> cose le fa**. Il precedente di questo progetto dice che quando un banco è rosso e il codice sembra
> funzionare, si cerca **nel codice per ore** prima di sospettare della misura.
>
> **In quest'ordine, e ciascuno costa poco:**
>
> | # | Che cosa | Perché prima o dopo |
> |---|---|---|
> | **1** | ⛔ **accendere `src/` una volta, e lasciarne una traccia in questo albero** — `bash src/costruisci.sh` e il registro del giro | il costruttore si difende dall'ottava veste di `LEZIONI.md` §1.9 (butta il binario prima, controlla cinque marche dentro quello nuovo, ha il controllo positivo dello strumento) ⛔ **e non è mai stato eseguito da nessuna parte in questo albero**. Un costruttore che si difende è esattamente il pezzo che non si può dare per buono senza averlo acceso una volta |
> | **2** | ⛔ **puntare `01-b8-sblocca.py` al prodotto**, con il `PING` | è lo strumento della regola **B0.3**, cioè quello da cui dipende l'isolamento di **tutti** gli altri banchi. Oggi parla col socket dell'innesto e col prodotto non ha mai parlato |
> | **3** | **B8, B6, B7 e B5 contro `src/`** | sono i quattro che toccano il ban, i tetti, il congedo e le violazioni — cioè i quattro punti in cui il prodotto ha del codice che nessuna misura ha visto. ⚠ E B7 lì trova **otto** motivi provocabili invece di sette: il prodotto ha un percorso di spegnimento, l'innesto no |
> | **4** | ⛔ **la sonda del trasporto di B2 contro `src/`** | il prodotto dichiara **19** stream unidirezionali dove la misura di B2 ne leggeva 16, e le altre cinque proprietà (0-RTT, migrazione, datagram, tetto, `allowPooling`) su di lui **non le ha lette nessuno** |
> | **5** | ⭐ **UN SECONDO MOTORE** | l'unico giro con un browser vero contro il prodotto è stato con **Firefox**. ⛔ Il criterio di B2 vuole **due motori su due**, e i difetti più cari di questa fase — i tre rossi di B11, il posto che non si liberava — **vivevano nella differenza fra i due motori**. Con un motore solo quella differenza non si vede |
>
> ⚠ **E una cosa da NON fare per prima**: rimettere mano ai documenti. Sono stati riallineati l'11
> agosto sul codice fermo; il prossimo disallineamento nasce dalla prima misura nuova, e si cura
> **nello stesso momento** (`CODER.md` §5).
>
> #### ⚠ E due cose che vanno con lui
>
> | | |
> |---|---|
> | ⛔ **a governare i tempi non è il nostro ritardo fisso, è PAM** | `[M]` mediana **2636 ms** su 42 tentativi respinti, dove §4.4-bis vuole ~1000. La previsione (`pam_faildelay`) era stata scritta **prima** di misurare. ⚠ Conta perché quel ritardo **non è costante**: se varia, rimette in circolo l'informazione che il secondo fisso serve a nascondere — cioè **se un nome utente esiste** |
> | ⚠ **il giro pieno di B8 si pianta al nono blocco su dieci** | resta fermo su qualcosa che nessuno gli dà. Il giro corto (`… 01-b8-lancia.sh 2`) arriva in fondo. ⛔ Va lanciato **staccato** dalla sessione di chi lo comanda, non attraverso di essa |
> | ⭐ **B6 ha chiuso R3.27, e con DUE risposte** | **la prima**: il cronometro parte dall'**apertura del canale di controllo**, non dalla fine del TLS ⇒ **`RCP.md` §4.6 riga 1 è cambiata di una parola**, l'11 agosto 2026. ⛔ **La seconda, e dice che curare la parola non basta**: chi apre una sessione WebTransport e **non apre mai il canale** non ha addosso **nessun tetto** e resta lì — §4.6 non aveva una riga per quello stato, adesso ce l'ha ed è ❓ (`DECISIONI.md` §7.17) |
| ⚠ **i tre tetti di B6 non hanno un registro** | scattano a **5,0 · 60,1 · 10,0 s** — ⛔ ma **non esiste nessun `.jsonl` di B6**, la scena di quel giro non è dichiarata da nessuna parte, e questi tre numeri **non sono riverificabili**. ⚠ *Stavano qui senza marca, senza data, senza scena e senza dispositivo, mentre `[M]` è definito più sotto come «misurato da noi, sul ferro, **con la data**» — rilievo **R12C.11**. Si rifanno col registro, oppure restano tre numeri di cui si sa solo l'ordine di grandezza.* |
>
> #### ⭐ Le misure della notte del 10 agosto, e dove vivono
>
> ⛔ **Gli esiti stanno in `web/rapporti/S-esiti-sonda.md`** — il quinto file di `web/rapporti/`, che
> non è uno studio: è **l'unico che porta numeri misurati**, con la scena accanto a ciascuno, i
> registri `.jsonl` e ⛔ **una ricontata dell'11 agosto che dichiara quali numeri hanno una
> provenienza su disco e quali no** (uno era falso, due erano senza provenienza, uno non era
> ritrovabile). ⚠ *Fino all'11 agosto quel rapporto non era nominato da **nessuno** dei dieci
> documenti — rilievo **R12C.15**.*
>
> | | |
> |---|---|
> | ⭐⭐ **S7 — il segno della rotella: MISURATO** | `[M]` 10 agosto, 20:59 UTC. `+120` di `libei` manda la pagina **verso la fine del documento** ⇒ ⛔ **il server RCP deve invertire l'asse verticale**. Scena per intero: GNOME headless su 192.168.0.2, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**, **Firefox 140.13.0esr** in kiosk; registro `banchi/01-s7-esiti.jsonl`. ⇒ **`RCP.md` §7.3 è chiusa** — ⛔ **su Mutter**: §7.3 vincola cinque desktop, e per gli altri quattro resta `[?]` |
> | ⛔ **S5 — la tela dichiarata: un DIFETTO DI PRODOTTO** | `[M]` 10 agosto, 23:13-23:14. A zoom 150 % **Chrome 151** dichiara una tela **del 50 % più grande** (1920×1080 → **2880×1620**) perché `screen.width` non cala; **Firefox 140** no. ⇒ la formula di `SPECIFICHE.md` §6.1-bis **non regge su Chrome**, e lì c'era ancora scritto *«va misurato»*. ⚠ La metà su **DeX** manca: il dispositivo non c'era |
> | ⭐⭐ **S1b — l'eccezione di Chrome: RISPOSTA, e senza aspettare i sette giorni** | `[M]` 11 agosto, `01-s1b-eccezione.sh scavalca`, **6 controlli su 6**. Invece di aspettare la scadenza **la si è portata da noi**, su una **copia** del profilo: Chrome si segna il clic **+ 604 799,99997 s** (i due istanti li scrive lui, nello stesso file), **onora** quell'istante — scadenza riscritta a ieri ⇒ la pagina non si apre più — e **non lo rinnova** quando lo si visita. ⛔ Il controllo che dice *no*: la **stessa** manomissione con data **+30 giorni** lascia la pagina aperta, quindi sopra è cambiato solo il segno. ⇒ **All'utente si dice «una volta a settimana»**. ⛔ I «13,111 s mancanti» non erano di Chrome: erano la distanza fra **due orologi**. ⏳ Il 17-18 agosto resta come conferma passiva, e l'orologio vero è intatto |
> | ⛔ **S2 · S3a · S6 — non eseguite** | mancano **il telefono Android**, **il DeX**, **una rete LTE vera**. ⭐ Non sono state dedotte (sarebbe la forma **E5**): i banchi sono pronti e girano il giorno che il ferro c'è |
>
> ⚠ **E una scoperta che non è di questa fase**, portata in `PIANO.md` fasi 2 e 6: in una sessione
> GNOME senza dispositivi di input fisici, un cliente partito **prima** che il puntatore virtuale di
> `libei` esista **non riceve niente** — né rotella, né bottoni, né il movimento. Mutter l'iniezione
> la riceve e non la consegna alla finestra.
>
> ⚠ **E QUATTRO decisioni aperte, e ciascuna si chiude con una parola**: la lettura di `RCP.md` §4.2
> sul `FIN` · la condizione di §8.1 · se §7.5 fosse davvero sua (intanto è 🔸) · ⭐ **e da oggi:
> quanto può restare lì una sessione WebTransport che non apre mai il canale di controllo**.
> ⛔ **Stanno in `DECISIONI.md` §7.14, §7.15, §7.16 e §7.17** — con le due letture possibili, **il
> byte che cambia sul filo** fra l'una e l'altra, il caso concreto in cui la differenza si vede e
> quale sembra più difendibile. ⚠ *Le prime tre erano nominate qui e in
> `fasi/rapporti/R11-documenti.md` (rilievi R11.22, R11.23, R11.15) e in nessun posto dove si decide:
> portate dove le decisioni stanno la notte del 10 agosto 2026. La quarta è nata l'11 agosto **da una
> misura** — B6 — e non da una lettura.* ⛔ **Nessuna delle quattro è decisa, e la marca resta ❓
> finché l'utente non parla.**
>
> ---
>
> ### Il passo appena chiuso
>
> ⭐⭐ **B3, B5 e adesso B11 sono chiusi. Tredici casi su tredici su TUTT'E DUE i motori** —
> Firefox 140 e Chrome 151 — più le due proprietà negative, e ⛔ **il secondo testimone verde**.
> *(10 agosto 2026, sera, e ripetuto)*
>
> ⚠ **E il controllo che dice di *no* gira su UN MOTORE SOLO — Firefox** *(rilievo **R11.24**,
> chiuso così la notte del 10 agosto: il banco lo dichiarava di suo, questa pagina no)*. È
> `01-b11-lancia.sh`: la pagina contro un server **sano** deve dire NON-CONFORME, e dice
> NON-CONFORME con **9 casi su 13** falliti. ⛔ **La riga qui sopra lo elencava dentro «su tutt'e
> due i motori»**, che è la lettura naturale e non era vera. ⚠ E la differenza morde proprio qui:
> i tre casi rossi di stasera **vivevano nella differenza fra i due motori**, cioè nel punto in cui
> *«per dire di no un motore basta»* è la premessa appena smentita. Si chiude del tutto
> eseguendolo anche su Chrome.
>
> ⭐ **B11 ha trovato sei difetti veri, e nessuno era visibile al cliente di prova**:
>
> 1. il **posto** (§8.2 `0x0F`) si liberava solo alla morte della *connessione* — e un browser
>    chiude la *sessione* tenendo viva la connessione. Ora si libera alla chiusura del canale di
>    controllo;
> 2. un messaggio spedito **subito prima** di chiudere la sessione, **il browser lo butta**: la
>    pagina non vedeva `RESPINTO`, vedeva silenzio. ⭐ È la prova che il punto 3 di §3.1 — *il
>    motivo dentro il codice di chiusura* — **non è ridondanza**. Curato dai due lati;
> 3. ⛔ la pagina **chiudeva senza congedarsi**, e §8.1 dice che chi chiude *DEVE* mandare `CONGEDO`
>    con un motivo — anche quando è una chiusura volontaria. Aggiunto: su Chrome i falliti sono
>    passati da 8 a 4;
> 4. ⛔ **il posto non si liberava quando a chiudere il canale era il SERVER.** Da lì in poi non
>    arrivava più un byte che potesse liberarlo, e la pagina non poteva rimediare: §4.2 le vieta di
>    spedire dopo la fine. Visto **solo su Chrome** — su Firefox il trasporto chiudeva lo stream in
>    tempo e il posto se ne andava lo stesso. ⭐ **Il difetto viveva nella differenza fra due
>    motori**, ed è quello che chiude i tre casi rossi di Chrome;
> 5. ⛔ **il server contava come «byte spediti dopo la fine» anche il `CONGEDO`** che §8.1 *impone*
>    a chi chiude. Il rosso finiva sulla pagina mentre faceva quel che deve. ⭐ Da lì il
>    chiarimento di `RCP.md` §4.4: dopo `RESPINTO` il divieto è di **riprovare**, non di
>    congedarsi;
> 6. ⛔ **il posto restava occupato per tutto lo smontaggio del trasporto**, e chi si ricollegava
>    subito si sentiva rispondere `GIA_ATTIVA_REMOTA`. ⚠ Sul banco era un caso rosso ogni tanto;
>    per chi usa il prodotto è *«mi dice che sono già collegato, e non è vero»*. Ora il server
>    **legge la capsula con cui la pagina chiude** e lascia il posto in quell'istante.
>
> ⭐⭐ **E il congedo arriva per DUE STRADE DIVERSE, una per motore.** Chrome lo manda come byte sul
> canale di controllo; **Firefox azzera il canale e butta quei byte**, e il motivo arriva solo
> dentro il codice di chiusura della sessione. ⛔ Fino a stasera il server **quella capsula non la
> leggeva**: di Firefox si sarebbe detto *«non si congeda»*, che è falso. È la prova, misurata, che
> il punto 3 di §3.1 non è ridondanza — **è l'altra strada**, e senza di essa metà dei browser
> sembrerebbe scortese.
>
> ⛔ **E due trappole nuove nel banco, tutt'e due sui denominatori**: il registro del server era
> tagliato a `tail -60`, e **aggiungere una riga al filtro ha fatto scendere «i guasti serviti» da
> 26 a 21** senza che il server cambiasse niente — un denominatore che dipende da quanto si parla.
> E il caso `respinto-poi-congedo` faceva **correre** la chiusura di §3.1 contro la risposta della
> pagina: Chrome ha perso la corsa in un giro su cinque. ⭐ Adesso quel guasto **non chiude**, e a
> chiudere è la pagina — che è proprio la cosa che il caso vuole vedere.
>
> ⚠ **E una cosa che B3 NON prova, scritta perché non sembri provata**: la rotazione **automatica**
> del certificato a quattordici giorni. Cambiarlo a mano dimostra che la pagina sa ritirare
> l'impronta; che il server rigeneri **prima** della scadenza resta senza banco, e il suo sintomo
> — *«non si collega più e non dice perché»* — arriva due settimane dopo la consegna.
>
> ⭐ **E il numero invecchiato è stato rimisurato, non riscritto a occhio** — `[M]` **10 agosto, ore
> 16:30**. La **lettura della capsula di chiusura** è cresciuta dentro lo strato WebTransport, e la
> misura si prende così: su albero pulito, `01-b3-rcp-innesta.py --togli`, poi
> `01-b2-ngtcp2-wt-innesta.py --togli`, poi si riapplica **il solo** innesto di B2. Risultato:
> **553 righe aggiunte, 373 di codice, 134 di commento, 46 vuote**.
> ⛔ **E i 972 / 618 sono un'altra cosa**: sono l'albero con **tutt'e due** gli innesti, B2 più i
> fili di B3. Non si mettono in fila con i 553 e non vanno dove sta quel numero — è la ragione per
> cui i due innesti sono separati (forma **E2**).
>
> ⚠ *Questo paragrafo diceva tre cose false, ed è stato riscritto il 10 agosto 2026 — rilievo
> **R11.7**, con **R11.1**.* Diceva che `01-b3-rcp-innesta.py --togli` *«non ha tolto niente, ha
> detto di sì e ha lasciato l'innesto dov'era»*, che *«la misura B2 da solo adesso non si sa
> prendere»*, e metteva in allarme su `ricostruisci`. ⛔ **Il comando fa una rimozione parziale e la
> dichiara a schermo**: toglie i file nostri, rimette `examples/CMakeLists.txt`, e stampa *«i file
> .cc/.h toccati da B3 vanno rimessi con `01-b2-ngtcp2-wt-innesta.py --togli` e riapplicati»*. ⛔ E
> `ricostruisci()` in `01-b11-guasto.sh` esegue **i due `--togli` nell'ordine prescritto** e poi
> riapplica: non si appoggia al primo da solo.
>
> ⚠ **Quel che resta vero, e resta aperto**: `--togli` **esce con 0 su un albero che in quello stato
> non compila** — chi si fermasse lì crederebbe di avere un albero sano. È un rilievo del banco, non
> di questo documento, e si cura là.
>
> ⚠ **E una manutenzione che ha una data**: quelle righe includono la **riscrittura del frame
> SETTINGS di nghttp3**, che dipende dalla forma dei suoi byte e non da una sua promessa. ⛔ Va
> riprovata a ogni aggiornamento di nghttp3 — e il banco che la riprova esiste.
>
> ⚠ **E una previsione resta aperta dopo due misure**: `lsquic` scrive le impostazioni della **bozza
> 02** e mai `SETTINGS_WT_MAX_SESSIONS`. Nemmeno con l'SNI ci si arriva — la connessione muore
> prima. Va tenuta aperta invece che chiusa con una prova che parla d'altro.
>
> ### Come si rimette in piedi il banco
>
> ⚠ *Questa sezione elencava **soltanto** i banchi di B2, mentre la stessa pagina dichiara chiusi
> B3, B4, B5 e B11 — rilievo **R11.21**, chiuso la notte del 10 agosto 2026. ⛔ Un banco che non è
> nominato dove si dice come rimettere in piedi i banchi ha lo stesso destino di uno che ha bisogno
> di una mano: **non si può rifare uguale**, e rifarlo uguale è l'unico modo di sapere se una misura
> è cambiata perché è cambiato il server.*
> ⚠ *L'elenco era della sera del 10 agosto 2026 e diceva:* «i banchi che nascono dopo — **B9, B12,
> B13, C2** — li aggiunge qui chi li scrive». *⛔ Sono nati fra le 22:54 e le 23:20 di quella notte e
> nessuno li ha aggiunti — e con loro mancavano i file di **B6, B7, B8 e B11**, che questa stessa
> pagina dà per chiusi o eseguiti, e le **sette pagine della sonda**. Completato l'11 agosto 2026,
> rilievo **R12C.13**: **R11.21 era stato chiuso la stessa notte in cui se ne apriva una versione due
> volte più grande.***
>
> **B2 — la libreria QUIC e il modello di fiducia** *(dal server, salvo dove detto)*:
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
> **Il filo — i banchi che hanno chiuso qualcosa:**
>
> ⭐ `01-b3-rcp-innesta.py` (**RCP sopra lo strato WebTransport di B2**; `--togli` fa una rimozione
> **parziale** e la dichiara a schermo) · `01-b3-lancia.sh` (**B3**, dal server: i primi tre giri,
> con `01-b3-terzo-giro.sh` che gira **dentro** il contenitore) · `01-b3-quarto-giro.sh`
> (l'orologio del silenzio, 35 s a `max_idle_timeout` 120) · ⚠ `01-b3-quinto-giro.sh` (**il
> certificato ruotato: si lancia da QUI, non dal server — i browser stanno da questa parte**) ·
> `01-b3-cliente.py` (**il secondo lettore di `RCP.md`**, e il registratore di §11.1) ·
> `01-b4-lancia.py` + `01-b4-validatore.py` + `01-b4-registrazioni.py` (**B4**: il validatore
> contro registrazioni **rigenerate adesso**) · `01-b5-lancia.sh` + `01-b5-violazioni.py` (**B5**,
> dal server: le violazioni verso il server) · `01-b6-lancia.sh` + `01-b6-tetti.py` (**B6**, i tre
> tetti) · `01-b7-lancia.sh` + `01-b7-congedo.py` (**B7**, il congedo **dal lato che riceve**) ·
> `01-b8-lancia.sh` + `01-b8-cronometro.py` (**B8**, il secondo fisso e il ban — ⛔ **si riscrive**,
> vedi sopra) · ⚠ `01-b11-lancia.sh` (**B11: da QUI**, coi due browser) + `01-b11-pagina.html` +
> `01-b11-guasto.sh` e `01-b11-guasto-innesta.py` (**il server guasto di proposito**, e
> `ricostruisci()` che rimette quello sano con i due `--togli` nell'ordine).
>
> **E quelli nati la notte del 10 agosto 2026:**
>
> ⭐ `01-b9-letture.py` (**B9**, il secondo lettore contro l'arbitro: **dodici** punti in cui
> `RCP.md` ammette due letture, ciascuno **coi byte che cambiano sul filo**) ·
> `01-b12-guasti.py` + `01-b12-lancia.sh` + `01-b12-copie/` (**B12**, la certificazione — un guasto
> per banco, e il registro `01-b12-registro.jsonl` con la data e le impronte) ·
> `01-b13-lancia.sh` + `01-b13-proprieta.py` (**B13**, le sei proprietà) ·
> `01-c2-lancia.sh` + `01-c2-diagnosi.py` (**C2**, le tre diagnosi del collegamento guasto) ·
> ⭐ `01-b8-sblocca.py` (⛔ **non è un pezzo di B8**: è **lo strumento della regola B0.3**, e parla il
> socket di comando di `RCP.md` §4.4-bis con `SBLOCCA` e `PING`) · `01-b8-prova-ban.c`.
>
> **E la sonda del browser** — ⚠ **queste girano da QUI o dal server secondo la riga, e la riga lo
> dice**:
>
> ⏳ `01-s1b-eccezione.sh` + `01-s1b-pagina.html` + `01-s1b-sito.sh` + `01-s1b-servi.py` (**S1b**,
> l'orologio dei sette giorni — ⛔ **`bash banchi/01-s1b-eccezione.sh oggi` una volta al giorno fino
> al 18 agosto**, e ⛔ **non si rigenera `/media/REMOTIX/s1b-certificato/` né si cancella
> `~/.remotix-s1b/`**, o l'orologio riparte da capo senza che nessuno se ne accorga per una
> settimana) · `01-s5-tela.sh` + `01-s5-pagina.html` + `01-s5-raccogli.py` (**S5**) ·
> `01-s7-rotella.sh` + `01-s7-rotella.c` + `01-s7-pagina.html` + `01-s7-raccogli.py` (**S7** — ⚠ e si
> chiude con `--pulisci`, o il drop-in resta e **il giro dopo non sa che era nostro**) ·
> `01-s2-pagina.html` · `01-s3a-pagina.html` · `01-s6-pagina.html` · `01-s-telefono.sh` (le tre che
> aspettano un dispositivo).
>
> ⚠ Tutto sotto `/media/REMOTIX` sopravvive al riavvio; il rootfs del server no —
> ⛔ **e per questo i server dei banchi sopravvivono anche loro**: il 10 agosto due di essi tenevano
> le porte otto ore dopo. Il banco adesso lo controlla prima di partire.
> ⛔ **E dal 10 agosto sopravvive anche il ban di `RCP.md` §4.4-bis, che sta su file**: fra un banco
> e l'altro si chiama il comando di sblocco, **mai dentro il giro di B8** (`fasi/01-filo-nudo.md`,
> regola B0.3).
>
> ### ⛔ Tredici trappole in due giorni, e due rifatte il giorno dopo — quindici occorrenze
>
> ⚠ *E il denominatore è dichiarato, perché prima non lo era: si contano **le voci elencate qui
> sotto**, e le due marcate «rifatto» contano **due volte** perché sono state pagate due volte.
> Il titolo diceva «**Quindici** trappole» su **undici** voci, e prima ancora «Dieci trappole in due
> sere» su otto: il conto non tornava nemmeno allora — rilievo **R11.20**, chiuso la notte del 10
> agosto 2026 dichiarando che cosa si conta e aggiungendo le **due** che mancavano.* ⛔ *«Un
> conteggio senza denominatore non è una misura: è una speranza con un numero davanti»*
> (`LEZIONI.md` §1.9 punto 4) — e qui il numero riassume **quanto lavoro di banco è stato buttato**.
>
> `grep -q` con `pipefail` · `| tail` che mangia lo stato d'uscita **(rifatto il giorno dopo)** ·
> due percorsi passati come una stringa, con `2>/dev/null` a nascondere l'errore — **e quello ha
> stampato un verde** · `pkill -f` che uccide chi lo esegue **(rifatto anche questo)** · porte
> tenute da server di ieri · `>/dev/null` che inghiotte la **richiesta di password** · `setsid` che
> forca e falsa il PID · `kill -0` che confonde *proibito* con *morto* · un'impronta tagliata di
> **una lettera**, che avrebbe bocciato una candidata · una cartella di profilo mancante, e nessuno
> dei due lati che lo dicesse · ⛔ **il registro tagliato a `tail -60`** e ⛔ **il caso
> `respinto-poi-congedo` che faceva correre** la chiusura contro la risposta della pagina — *le due
> di B11, raccontate per esteso qui sopra, tutt'e due sui **denominatori*** · ⛔ **e il buffer di Python, che ha fatto accusare al banco un server
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
> | ⛔ **due revisioni avversariali** | **46 rilievi numerati** — **29** in `web/rapporti/R1-revisione-rcp.md` e **17** in `R2-revisione-web.md` — **più le 12 omissioni** `O1`-`O12` di `R2` §2, e tutti **prima del primo byte**. ⚠ *Diceva «**51** contraddizioni», e quel numero non si ritrova con nessun criterio scritto: 29 + 17 = 46, e nessuna somma dichiarata da nessuna parte dà 51 (rilievo **R11.20**, chiuso la notte del 10 agosto 2026 **dichiarando che cosa si conta**). Le omissioni si contano a parte perché non sono contraddizioni: sono righe che **non c'erano**, e per definizione nessun controllo delle citazioni le trova* |
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

⛔ **E accanto ai quattro, un quinto file che non è uno studio**:
[`web/rapporti/S-esiti-sonda.md`](web/rapporti/S-esiti-sonda.md) — **gli esiti misurati** della sonda
del browser (S7 · S1b · S5 · e le tre che aspettano un dispositivo), con la scena accanto a ogni
numero e la ricontata che dice quali numeri hanno una provenienza su disco. ⚠ *I «quattro rapporti»
qui sopra restano quattro: sono i rapporti degli **studi**, ed è un denominatore dichiarato.*

⚠ **`gnome-remote-desktop.md` non è uno di questi** *(chiarito il 9 agosto 2026)*. Studia **il
server RDP di GNOME**, cioè un concorrente sul filo che abbiamo buttato — non il desktop. Con RDP
morto decade quasi per intero, ed è scritto su una versione che Trixie non ha (51.alpha contro
48.1). **Su GNOME si legge [`gnome.md`](gnome.md)**, che parla di Mutter e resta valido.

---

## Le cartelle

⚠ *Questa tabella elencava **tre** voci — `fasi/`, `v1/`, `reference-*/` — e non aveva né `src/` né
`banchi/` né `web/`: **la cartella che contiene il prodotto non compariva nella tabella che dice che
cosa contengono le cartelle**. Completata l'11 agosto 2026, rilievo **R12C.1**.*

| | |
|---|---|
| ⭐⭐ `src/` | **il prodotto**: il server della fase 1 in C — **22 file, 9.647 righe** `[M]` 11 ago 2026. RCP/1 su WebTransport, i due certificati, la pagina servita dal server, il ban e il suo comando di sblocco. ⛔ **Non è in git**, e nessun banco lo accende ancora |
| ⭐ `banchi/` | **i banchi della fase 1** e la sonda del browser, più `banchi/rcp/` — la copia **gemella** di `rcp.c`/`rcp.h`/`autenticazione.c`, oggi identica a quella di `src/` byte per byte. ⚠ Qui il bersaglio è **l'innesto** dentro `bsslserver`, non `src/` |
| `web/rapporti/` | i quattro rapporti dello studio del browser, ⭐ **più `S-esiti-sonda.md`**, che è l'unico posto dove vivono i numeri **misurati** della sonda |
| `fasi/` | un documento per fase, **aperto quando la fase si apre** — vedi `PIANO.md` §0.2. In `fasi/rapporti/` i verdetti delle revisioni avversariali: ⛔ **portano la loro data e non si riscrivono**, e quando uno è superato lo si dice **altrove**, con la data |
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
