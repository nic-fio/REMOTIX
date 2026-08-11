# REMOTIX_V2

Desktop remoto per Linux: un **server**, **nessun client da installare** — basta un browser
moderno — e un protocollo nostro chiamato **RCP** — *Remotix Control Protocol*, che viaggia su
**WebTransport**.

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
> se il riferimento è ancora il proprio. ⛔ **Quel che resta non è una misura, è una dichiarazione**:
> è un cambiamento di prodotto **dopo** la chiusura della fase 1, e come metterlo a verbale è una
> **decisione dell'utente**, aperta.
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
>   motore la confermano. ⛔ **Resta aperta la dichiarazione**, non la misura: la fase era chiusa
>   quando la cura è stata applicata.
> - ⚠ **E il tracciatore di quel banco è CIECO su Chrome dentro `pagehide`**: non esce né
>   `sendBeacon` né una XHR **sincrona**. Su Chrome l'attribuzione poggia solo sul registro del
>   server — che basta, perché fra prima e dopo cambia la riga della violazione, ⛔ ma chi
>   riusasse quel tracciatore altrove deve saperlo.
> - ⛔ **P5 non si certifica** per quel punto solo — il resto del suo giro sano è verde su Chrome.
> - ⛔ ~~La parola d'ordine nei registri sporchi~~ — **chiusa**: cura verificata con un giro nuovo,
>   **33 file** buttati con la traccia. ⚠ **Resta** la parola sulla riga di comando dei banchi
>   (quindi in `ps`) per `parola-di-prova`; ⭐ **per la parola generata di `prova2` no**: B10 la passa
>   per file `0600` e la cancella con una `trap`.
> - ⚠ **Il registro delle certificazioni va ancora unito a mano**, e ⛔ **il numero dipende da dove lo
>   si chiede**: **12 su 14 da CHUWI**, **11 dal server** — là `RCP.md` non c'è (B9), qui non c'è
>   `remotix/pagina.c` (P1). ⭐ Hanno ragione tutt'e due, e lo strumento scrive *«non so»* invece di
>   arrotondare.
> - ⚠ **7 chiamate su 52 restano «IGNOTE»** a `01-b0-chiamate.py` — **0 rotte**: non sono un rosso e
>   non sono un verde.
> - ⚠ **`01-b0-terreno.sh prodotto` non guarda il binario del prodotto**: lo cerca in
>   `remotix/build/remotix` mentre `costruisci.sh` lo mette in `remotix/remotix`. ⇒ **il terreno del
>   prodotto non può uscire verde**, e quel controllo è un IGNOTO fisso.
> - ⚠ **Le mediane di B8**: ~~1984~~ → `[M]` **2123 · 2198 · 1086 ms** (giro della sera). ⭐ Il numero
>   cambia perché cambia il giro; quel che è nuovo è che **l'imputato è misurato**: **+1034 ms** oltre
>   il secondo fisso sui respinti contro **+84 ms** sugli ammessi, cioè la firma di `pam_faildelay`.
>   ⇒ **PAM, non il nostro codice** — e la `[?]` resta aperta lo stesso.
>
> #### ⚖️ E QUEL CHE ASPETTA L'UTENTE — adesso è **una** cosa, non due
>
> ✅ **Il giudizio è dato**: 11 agosto 2026, e la fase è chiusa (in cima a questa pagina).
>
> ⏳ **Restano i due ripieghi dichiarati, e sono di apertura della fase 2, non di chiusura della 1:**
>
> 1. **Il filo unico.** Il server ha un filo solo e la verifica PAM lo **blocca**: dieci utenti che
>    entrano insieme fanno aspettare l'ultimo dieci secondi, dove `SPECIFICHE.md` §5.5 promette dieci
>    sessioni. Si tiene il ripiego, o il filo separato per PAM prima della fase 2?
> 2. **Il tetto delle sessioni**, fissato a **16 in compilazione** dove la regola lo vuole **dieci,
>    configurabile**.
>
> ---
>
> ### ⛔ SI RIPARTE DA QUI — l'11 agosto 2026 *(la mattina — tenuto perché spiega da dove si partiva)*
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
