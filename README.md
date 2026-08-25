# REMOTIX_V2

Desktop remoto per Linux: un **server**, **nessun client da installare** — basta un browser
moderno — e un protocollo nostro chiamato **RCP** — *Remotix Control Protocol*, che viaggia su
**WebTransport**.

> # ⭐⭐⭐⭐⭐ DA QUI SI RIPRENDE — **25 agosto 2026**
>
> ## ➡️ LA PROSSIMA È LA **FASE 11 — LA RETE DI SICUREZZA**, e l'ha decisa l'utente
>
> *«Prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi. Prima di
> passare agli altri DE è necessaria una sessione dedicata per studiare una modalità che impedisca di
> introdurre regressioni.»* — 25 agosto 2026, `DECISIONI.md` §4.6-duodecies.
>
> ⚠ **KDE, XFCE e LXQt scalano di uno** (fasi 12, 13, 14): le fasi non cambiano di una riga, cambia
> il loro posto.
>
> ⭐⭐ **E il collaudo di quella fase è già scritto**: la rete va puntata contro il codice di oggi e
> ⛔ **deve diventare rossa sulla «sessione che nasce cieca»** — senza che nessuno le abbia detto dove
> guardare. **Se non la prende, non è una rete: è un rituale.**
>
> ---
>
> ## ✅⭐⭐⭐ LA FASE 10 È CHIUSA — *multi-tenant e il budget*
>
> **Chiusa il 25 agosto 2026, sul giudizio dell'utente**: *«sono soddisfatto — riprodotto audio e
> video su una connessione del 1990; non credo che si possa chiedere di più»*. ⭐ Un **video 4K**
> dentro il desktop remoto, con la banda del suo tablet strozzata a **10 Mbit/s**, cioè **un terzo
> del pavimento dichiarato**. ⇒ E il metro che ne è uscito è `DECISIONI.md` **§4.6-decies**: sotto le
> specifiche si perde **la nitidezza**, ⛔ **non la fluidità e non il sincronismo**.
>
> 📖 **[`fasi/10-multi-tenant-e-il-budget.md`](fasi/10-multi-tenant-e-il-budget.md)** — la **sintesi**
> in testa, **§5** le cure, **§6** le misure, **§8** le due decisioni che restano.
>
> ### ⭐⭐⭐ Il numero che la fase cercava — **e non era quello che si credeva**
>
> | dove si spende | motore | soffitto `[M]` |
> |---|---|---|
> | il **codificatore** | i due VDBOX | **1,86 Gpixel/s** in H.264 · **2,33** in HEVC |
> | ⭐⭐ **la COMPOSIZIONE** | ⛔ **`rcs0`** | ⭐ **0,97 Gpixel/s — la METÀ** |
>
> ⇒ ⛔⛔ **Il budget non è di codifica: è di composizione**, e a saturarlo è **`gnome-shell` al
> 99,5 %** mentre **`remotix` sta a `0,00 %`** — cioè **una cosa che non è nostra**.
> `DECISIONI.md` **§4.6-nonies** corregge §4.6.
>
> ### ⭐⭐ E quante ne stanno
>
> **Sei** sulla scena satura — *«tenendo conto che siamo su una scheda Intel integrata non
> particolarmente performante, 6 RDP attivi contemporaneamente non mi sembra un cattivo risultato»*,
> l'utente, §4.6-septies. ⭐ **E almeno UNDICI sul desktop vero**, dove `[M]` **il soffitto non è
> stato trovato: sono finiti gli utenti, non la macchina**.
>
> ### ⭐⭐⭐⭐ E LA COSA PIÙ UTILE DELLA GIORNATA NON È UN NUMERO
>
> ⛔ Il regista ha provato il prodotto e ha detto tre volte **«Firefox non funziona»**, fino a
> smettere. ⇒ **Era `~/.cache` che punta a `/tmp`**: il **primo** utente che apre il browser si
> prende `/tmp/mozilla` a modo `0700`, e **per tutti gli altri il profilo non nasce**.
> ⭐⭐ *Un difetto che su una macchina a UN utente non si vede mai, e che su dieci ne blocca nove* —
> ed è esattamente il tema di questa fase. Curato in `src/provisiona.sh`.
>
> ⛔⛔ **E la fase 9 l'aveva chiuso con un ✅ sbagliato** (§20.1-ter, ora **refutata**): il controllo
> che *«chiudeva la questione»* girava da un utente che **aveva lo stesso difetto**.
> ⇒ `LEZIONI.md` **§1.38** — *un controllo che condivide il fattore che deve escludere non controlla
> niente*.
>
> ⭐ **E adesso c'è il testimone che fa VEDERE** — `banchi/10-f1-testimone.py`, un PNG del desktop
> remoto, tarato, con il terzo esito **«non ho guardato»** distinto da «era nero» (`LEZIONI.md`
> §1.37).
>
> ### ⭐⭐ E IL PRODOTTO HA DIMEZZATO LA BANDA DA SOLO
>
> `[M]` Stessa scena, filo strozzato: **38,5 → 37,4 fot/s** (uguali), **6,0 → 3,20 Mbit/s** (metà),
> ⭐ **coda del filo VUOTA**, e il motore di composizione fermo sul **41-46 %** — cioè la scena si
> muoveva come prima. ⇒ ⭐ **Non ha rallentato: ha compresso di più.**
>
> ### ⛔⛔⛔ E UN DIFETTO RESTA APERTO, DICHIARATO — **la sessione che nasce cieca**
>
> `[M]` Su una sessione **appena nata** Mutter non annuncia nessun `wl_output` ⇒ ⛔ **nessuna
> applicazione può aprire una finestra**: Firefox resta vivo e non dipinge, il compositore sta a
> **0,0 %**, il palco consegna **zero fotogrammi**. ⚠ È **intermittente**: `provanic3` ha avuto il
> monitor **2 volte e poi 6 volte no**. ⇒ `fasi/10-multi-tenant-e-il-budget.md` **§7.4**.
>
> ⭐ **Non tocca i numeri di capacità** — quelli sono presi su sessioni che disegnavano davvero.
> ⛔ **Tocca la consegna**: oggi una sessione nuova su tre-quattro nasce cieca.
>
> ### ⚠ E DUE DECISIONI SONO RIMASTE NON PRESE — valgono i predefiniti
>
> ⛔ **QVBR resta SPENTA** e i numeri di fabbrica restano **tetto 10, riserva 0,5**.
> ⭐ E la fase ha portato un argomento nuovo: **QVBR non serve a un utente solo** — il regolatore fa
> già il suo mestiere — ⛔ **serve quando sono dieci**, e quel giro non è stato fatto (i clienti
> giravano su `lo`: il filo è **contato, non provato**).
>
> ---
>
> # ✅ E PRIMA DI QUESTA — **24 agosto 2026**
>
> ## ✅⭐⭐⭐ LA FASE 9 È CHIUSA — *la qualità e la degradazione*
>
> 📖 **[`fasi/09-la-qualita-e-la-degradazione.md`](fasi/09-la-qualita-e-la-degradazione.md)** — la
> sintesi in testa, e **§17-§21** la parte che conta.
>
> **Chiusa sul giudizio dell'utente**: *«il prodotto cambia in meglio; questa fase era per rendere
> più solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli»*.
> ⭐ È il **criterio**, non un commento: il traguardo non era **salvare** l'esperienza su qualunque
> rete — era **non peggiorarla, non mentire, e non fingere che una linea rotta sia una linea lenta**.
>
> ## ⭐⭐ IL BERSAGLIO L'HA CORRETTO LUI, A FASE APERTA
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
> perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter»* (`DECISIONI.md`
> §3.1-ter). ⇒ Ed era la grandezza giusta: **sulla banda il prodotto non cedeva; su un filo sporco
> sì.** ⛔ Il pavimento di banda è passato a **30 Mbit/s** (§3.1-sexies) e conta come **premessa**.
>
> ## ⭐⭐⭐ LA SCALA CHE CHIUDE LA FASE — dai suoi occhi
>
> | perdita reale | senza cure | con cure |
> |---|---|---|
> | 1 % | *«mi sembra ok»* | — |
> | 5,6 % | *«è tutto fluido»* | — |
> | **10 %** | ⛔ *«bloccato»* | ⛔ *«bloccato lo stesso»* |
>
> ⇒ **Sopra una certa perdita la scala di degradazione non ha più niente da offrire**, e l'unica
> risposta onesta è **dichiarare la linea morta** (§3.1-quater) — la decisione che l'utente ha preso
> **prima** di avere quel numero.
>
> ## ⭐ LE CINQUE CURE SONO ACCESE — e la linea sana non paga niente
>
> | cura | predefinito | si spegne con |
> |---|---|---|
> | silenzio dell'audio | **acceso** | `--niente-audio-silenzio` |
> | soglia sulla coda video | **100 ms** | `--sgombra-soglia-ms 0` |
> | regolatore del ritmo | **acceso** | `--niente-ritmo-adattivo` |
> | linea morta | **accesa** (stallo 5 s · silenzio 10 s) | `--niente-linea-morta` |
> | sfratto del fantasma | **15 000 ms** | `--sfratto-ms 0` |
>
> `[M]` **La prova che poteva far ritirare tutto è verde**: linea sana **39,69** fotogrammi/s coi
> predefiniti contro **39,60** a cure spente, zero chiavi in tutt'e due. ⭐ È la ferita per cui v1
> perse questa fase — *i numeri migliorano e l'esperienza peggiora* — ed è stata cercata apposta.
>
> ## ⭐⭐ I TRE FATTI CHE VALGONO OLTRE LA FASE
>
> 1. **Il difetto non comincia dove si vede.** La spirale di chiavi parte al **primo pacchetto
>    perso** (0,10 % di perdita); il calo che l'utente **vede** arriva **cinque volte più in là**
>    (0,53-0,75 %). ⇒ Un banco che guardi solo i fotogrammi/s dà **verde fino allo 0,5 %**.
> 2. **L'innesco ha un rischio costante**: ~5 % al secondo, mediana **13 s**, e una volta acceso non
>    si spegne. ⛔ I banchi girano 25 s, **le sessioni durano ore** ⇒ ogni misura presa vicino al
>    bordo **sottostima**, e non di poco.
> 3. **Il disordine viene scambiato per perdita — e ci è tornato addosso.** La prima «linea morta»
>    era tarata su `pkt_lost`, e `[M]` una linea che **regge** ne dichiarava il **512‰** contro il
>    **123‰** di una che **non regge**. Rifatta sullo **stallo dell'uscita** (5 s).
>
> ## ⚠ E IL CONTO DEGLI ERRORI DI METODO — la parte più utile
>
> `[M]` **Nove difetti nei banchi**, tutti della forma *«silenzio invece di rosso»* (uno faceva
> leggere a un banco i numeri del banco **precedente**) · **tre prove che non mordevano**, scoperte
> **contando i pacchetti** · **due conclusioni ritirate** (le applicazioni che «non arrivavano» — non
> c'era nessuno che guardava; e la prova della claquette dichiarata «nulla» e smentita dal **terzo**
> giudizio) · **due premesse false** ereditate e corrette (l'utente non è mai stato su **PCM**; i
> **+331 ms** non raggiungono il suo orecchio).
>
> ## ⏳ CHE COSA RESTA APERTO
>
> ⛔ ~~**Firefox non parte sulla macchina di prova** — `[M]` anche fuori da REMOTIX, headless e
> senza Wayland: **non è nostro**, ma blocca le prove col browser (§20.1-ter)~~
> ⭐⭐ **CHIUSA il 25 agosto 2026, e la causa era un'altra**: `~/.cache` è un **collegamento a
> `/tmp`** (da `/etc/skel`), e il **primo** utente che apre il browser si prende `/tmp/mozilla` a
> modo `0700` ⇒ **per tutti gli altri il profilo non nasce**. Curata in `src/provisiona.sh`, e
> `[M]` **Firefox rende una pagina nel desktop remoto**.
> ⚠ *E la conclusione «non è nostro» era giusta a metà: il collegamento non è nostro, ma è il
> nostro `useradd -m` a propagarlo, e sono i nostri dieci inquilini a renderlo certo.*
> `fasi/10-multi-tenant-e-il-budget.md` §5.10 ·
> ⚠ la metà **`AV`** del sincronismo non è rimisurata (vuole quel browser) ·
> ⚠ `rcp.c` dice ancora *«rifiutati da ngtcp2»* dove adesso sono *«buttati perché il filo era muto»* ·
> `[?]` l'algoritmo di congestione è **CUBIC** e **non è mai stato scelto**: la prova per contrasto
> non è stata fatta perché nessuna opzione lo espone.
>
> ## ➡️ LA PROSSIMA È LA **FASE 10** — il multi-tenant
>
> ⭐ E questa fase le ha lasciato due cose: la **scala di degradazione**, che è il modo di far stare
> più gente sulla stessa macchina (*«sì, più piccolo»* invece di *«no»*), e ⛔ il **budget di rete**
> mai misurato — dieci sessioni × 30 Mbit/s sono **300 Mbit/s sul filo del server** (§3.1-bis
> punto 2).
---

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
> in [`FASI.md` §02-primo-fotogramma](FASI.md#02-primo-fotogramma). ⚠ *Stavano anche nel riquadro
> «DA QUI SI RIPRENDE — 13 agosto» di questo file, potato il 16 agosto 2026: vedi la nota in
> fondo a questo riquadro.*
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
> **codice morto**. ⭐ **La cura è di tre righe ed è scritta** in `FASI.md` §01-filo-nudo, riquadro
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
> ### ⛔ IL DIARIO È STATO POTATO — *16 agosto 2026*
>
> *Decisione dell'utente, rivedendo i documenti.* Questo file portava **nove** riquadri «DA QUI SI
> RIPRENDE» impilati, uno per sessione di lavoro. ⛔ **Sei di essi erano già dichiarati morti dal
> file stesso**, con la formula *(superato dal riquadro qui sopra)*: **485 righe**, il 31 % del
> documento che si apre per primo.
>
> ⭐ **Sono usciti, e restano interi nella storia** — l'ultimo commit in cui vivono è **`47bd41c`**:
>
> ```
> git show 47bd41c:README.md | less        # il README com'era, diario compreso
> ```
>
> ⚠ **Nessuna misura è andata via con loro**: erano riquadri di *ripresa*, cioè stato di sessione,
> e i numeri che citavano stanno in `FASI.md`. ⛔ Se ne trovi uno che non ci sta, è un difetto —
> e la riga qui sopra dice dove rileggerlo.

> ### ⭐⭐⭐⭐⭐ DA QUI SI RIPRENDE — **15 agosto 2026, mattina.** ⇒ **LA CODA DELLA FASE 4 È CHIUSA: LA TELA È LA FINESTRA**
>
> > ## *«Sia su Linux sia su Android (DeX) è tutto perfetto.»*
> > — l'utente, 15 agosto 2026, dopo una notte di lavoro e tre difetti trovati da lui
>
> ⭐⭐ **Il desktop remoto prende la misura della finestra del browser**, e da questo discendono
> quattro cose che l'utente vedeva come difetti separati: niente bande nere, testo nitido (scala di
> disegno **1,000**), il ri-attacco che ritrova la sua misura, e il login che porta il desktop in
> **311 ms** invece di 4,4 secondi. ⭐ La conferma che non viene da noi: GNOME *Impostazioni →
> Displays*, **dentro** la sessione remota, dichiara «Resolution 1264 × 800».
>
> | | |
> |---|---|
> | ⭐ **il numero della fase** | la tela concordata all'attacco: `[M]` **1264×800** = la finestra, scala **1,000**, `pixelated` |
> | ⭐ **login → desktop** | `[M]` **4,4 s → 311 ms** — e la cura non è il ridimensionamento: è che **riavviare il flusso consegna un buffer** quando una chiave è dovuta e la scena è ferma |
> | ⭐⭐ **clic → fotogramma spedito** | `[M]` **136 ms → 41 ms** (peggiore 502 → 47), su scena FERMA. ⚠ Non è il numero di §1-bis (quello è su scena in movimento, 139 ms, e resta della fase 8): è l'anello che nessuno aveva misurato |
> | ⭐ **il ridimensionamento a caldo** | `[M]` **6 ms** dalla risposta del palco alla chiave spedita. ⚠ **E dal 17 agosto 2026 non è più una funzione dell'utente**: la tela si adatta all'attacco e al **riattacco** — che è dove questi 6 ms si pagano — e mai a sessione viva (`DECISIONI.md` §5.1-bis) |
> | ⛔ **e il blocco della costruzione** | sciolto **senza chiedere all'utente**: `src/Contenitore` (podman da utente, sul portatile) e l'errore di percorso in `enter.sh` |
>
> ⛔⛔ **DIECI DIFETTI TROVATI REFUTANDO** la cura appena scritta (quattro agenti, mandato
> avversariale), e **otto erano nati quella notte insieme a lei**: una lettura oltre la memoria
> copiata, un messaggio che faceva chiudere una sessione sana, due `ADATTA_TELA` incatenate che
> assestavano il desktop sulla misura sbagliata *con i conti in ordine*.
>
> ⛔⛔ **E TRE LI HA TROVATI L'UTENTE**, non i banchi — fra cui il più grosso della notte: *«su
> Android il mouse non prende più i click»* erano **due sue sessioni che si contendevano il palco
> diciassette volte al secondo**, e ogni giro ricreava i dispositivi di `libei` (`[M]` 640 ricambi).
>
> 📖 **Il documento**: [`FASI.md` §04-si-comanda](FASI.md#04-si-comanda), §«la coda della fase 4» ·
> il rapporto tecnico [`fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`](fasi/rapporti/F4-IN-13-la-tela-che-cambia.md).
>
> ⛔ **E QUESTA È LA FASE 4, NON LA 6** — corretto dall'utente il 15 agosto 2026, e la sua ragione
> regge: il numero della fase lo dà il **perché** si è fatto il lavoro, non l'elenco delle cose
> prodotte. Qui si è fatto per curare **il mouse e il ritardo dei clic**, cioè per finire il mandato
> della fase 4 — e tutti i rapporti della notte si chiamano `F4-IN-*`, compreso quello nuovo.
> ⇒ **La fase 6 resta APERTA** con tre quarti del suo contenuto già fatto e misurato (`PIANO.md` dice
> quali).
>
> ### ⭐⭐ E LA PROSSIMA È LA **5 — LA SESSIONE**, in una sessione di lavoro NUOVA
>
> *Deciso dall'utente il 15 agosto 2026.* Il mandato è scritto, a macchina in ordine e server
> acceso: 📖 **[`fasi/rapporti/F5-IN-0-mandato.md`](fasi/rapporti/F5-IN-0-mandato.md)** — dentro ci
> sono lo stato della macchina, **le due strade per costruire**, quel che della fase 5 è già vivo (e
> va **provato**, non riscritto), e i quattro pezzi che mancano davvero.
>
> ⛔ **Il primo gesto è aprire `FASI.md` §05-la-sessione**, prima di scrivere una riga: la coda della
> fase 4 quella regola l'ha violata, e porta la riserva in testa.
>
> ---
>
> ### ⭐⭐⭐⭐ Il dettaglio della notte del 13, e i due difetti trovati dal giudizio
>
> > ## ⭐ *«Mi sembra abbastanza fluido, non il massimo ma pur sempre fluido.»*
> > — l'utente, 14 agosto 2026, e **la fase 3 si chiude qui**
>
> ⛔⛔ **Ma il giudizio ha prodotto DUE difetti che nessun banco aveva trovato, e sono il lavoro che
> viene adesso.** Il dettaglio sta in [`FASI.md` §03-movimento](FASI.md#03-movimento) §0-ter e
> §0-quater; il conto della notte in
> [`fasi/rapporti/F3-sessione-13-sera.md`](fasi/rapporti/F3-sessione-13-sera.md).
>
> | | il lavoro, in ordine | perché prima |
> |---|---|---|
> | **1** | ⛔⛔ **FAR VEDERE IL DESKTOP VERO.** Il prodotto **aggiunge** un monitor virtuale alla sessione (`Meta-2`, *«2 prima e 3 dopo»*) e registra quello: GNOME ci mette **lo sfondo**, ma barra, dock e finestre restano sul **primario**. ⇒ **L'utente vede un secondo schermo vuoto, non il suo desktop** | ⭐ è **la domanda che l'utente ha fatto** — *«se il server non mostra il desktop, a che serve REMOTIX?»* — ed è `SPECIFICHE.md` §5.1. ⛔ **È rimasta nascosta per due fasi** dietro il giudizio della fase 2, *«è lo sfondo GNOME, è OK»*: **uno sfondo vuoto preso per un successo** |
> | **2** | ⛔⛔ **HEVC NON DIPINGE nel browser dell'utente.** `[M]` 1 748 fotogrammi consegnati, **0 dipinti**, e il client chiede una chiave **1 659 volte**. ⚠ **I banchi dicevano il contrario** (1 047 dipinti, 30 fps): quel giro aveva una **scena sintetica** e un **Chrome del banco** | senza, **la codifica in hardware non è giudicabile** — e la fase l'ha già dentro |
> | **3** | ⚠ ~~**IL DISEGNO: 28,0 ms su 78,1, il 36 %**~~ ⇒ ⛔ **CORRETTO il 14 agosto 2026**: il disegno costa **2,25 ms**; i 28 erano **l'attesa del fotogramma dalla GPU** più il disegno | il collo di bottiglia c'è, ⭐ ma **non è dove c'era scritto** |
>
> ⭐⭐ **E `D1` è CHIUSO, a costo zero, leggendo il registro della sessione del giudizio** — con una
> risposta **peggiore della domanda**: la strozzatura del debito di chiave **regge a 1/s quando il
> client dipinge** e ⛔ **si apre a 5/s quando NON dipinge**, cioè esattamente quando ogni chiave è
> sprecata. ⚠ E lo scenario temuto — *«un abbandono legittimo ne genera sessanta illegittimi»* —
> **non si è presentato**: `abbandonati 0`. *Il sintomo osservato era un altro da quello temuto.*
>
> ---
>
> ### ⭐⭐⭐⭐ Il numero della fase, e come è stato preso — **13 agosto 2026, notte**
>
> *La fase 3 ha il suo numero **con la codifica in hardware**, e la codifica in hardware è **nel
> prodotto**, non su una copia. ⏳ **Manca solo il giudizio dell'utente**, preparato in
> [`fasi/rapporti/F3-giudizio-elenco.md`](fasi/rapporti/F3-giudizio-elenco.md). Il conto per intero
> sta in [`fasi/rapporti/F3-sessione-13-sera.md`](fasi/rapporti/F3-sessione-13-sera.md).*
>
> | | totale | codifica | **disegno** | fps | P1 |
> |---|---|---|---|---|---|
> | AV1 in software *(la 7561)* | **71,86 ms** | 39,67 | ⭐ 9,07 | 22,0 | ✅ |
> | ⭐ **HEVC in hardware** *(la 7571, il deposito)* | **78,12 ms** | ⭐ 31,78 | ⛔ **28,00** ⚠ *(l'etichetta «disegno» è falsa: vedi il riquadro sotto)* | ⭐ **30,0** | ✅ |
>
> ⭐⭐ **L'ARCHITETTURA È ASSOLTA**: togliendo l'hardware si perdono **31,7 ms** e **gli altri quattro
> tratti non si muovono** (Mutter −0,02 · filo −0,12 · decodifica −0,76). La chiave passa da
> **114,5 ms a 5,1**, e il ritmo **raddoppia**.
> ⛔ **Ma il tetto SFORA** — 78,1 contro 50, e **94-118 ms** sul vetro col pezzo cieco dichiarato.
>
> #### ⛔⛔⛔ 14 agosto 2026 — **QUESTA RIGA È UN'ETICHETTA FALSA SU UN NUMERO VERO**, e si corregge qui
>
> *Corretto per decisione dell'utente il 14 agosto 2026, su due misure indipendenti della fase 4:
> `fasi/rapporti/F4-A2-pagina-dipinge.md` e `fasi/rapporti/F4-A10-anello-input.md`.*
>
> | | |
> |---|---|
> | ⭐ **che cosa resta vero** | il totale **78,1 ms** (n=379), e la scomposizione in cinque tratti |
> | ⛔ **che cosa era falso** | **il nome del tratto**: non è «il disegno». `[M]` il disegno del flusso vero costa **2,25 ms** (5 giri, dispersione 0,30), e il controllo positivo su AV1 dà 6,25-8,45 contro i 9,07 della fase 3 ⇒ **il cronometro era tarato** |
> | ⭐ **che cos'erano i 28 ms** | **l'ATTESA del fotogramma dalla GPU, più il disegno.** Un fotogramma HEVC decodificato in hardware esce **opaco** (`format = null`) e la rilettura della marca del banco (`03-b17:534`) ne provoca il trasferimento GPU→CPU; AV1 no |
> | ⛔ **e la prova che il confine era messo male** | ⭐ cambiando codec **a palco identico**, «decodifica» e «disegno» si muovono in **versi opposti** — AV1 `6,315 + 9,105`, HEVC `0,730 + 27,995` — e **la somma si conserva**. ⚠ Ma `drawImage` **non sa quale codec ha prodotto il fotogramma**: ⇒ il costo non è entrato nel disegno, ha **attraversato il confine fra i due tratti** |
> | ⭐ **il fatto nuovo che resta** | il costo del **client dopo il filo** raddoppia con HEVC: `[M]` **+10,5…+15,3 ms**. Quello è vero, ed è dove andare a cercare |
>
> ⛔ **E una cosa che fa una brutta figura, scritta perché non si perda**: la **cella di controllo di quel giro non è mai esistita** — il giro `con-gpu` ha provato HEVC, VP9 e H.264, e **non AV1**. Senza AV1 non c'era niente con cui confrontare.
>
> ⇒ ⭐ **Perché si corregge invece di annotarla**: chi legge «il collo di bottiglia è il disegno» si mette a ottimizzare un tratto che costa **2 ms** invece di uno che ne costa **28**. `LEZIONI.md` §7.2 — *ottimizzare nella direzione sbagliata è peggio che non ottimizzare*.
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
> `FASI.md` §00-ambiente B3.3 — è stata ripetuta **due volte nella stessa notte**, e la seconda è
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
> **Il dettaglio, file per file, sta in `FASI.md` §01-filo-nudo §«Che cosa è stato sviluppato».**
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
> ⇒ Il registro è `banchi/01-b12-registro.jsonl`, e il conto per esteso sta in `FASI.md` §01-filo-nudo.
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
> `FASI.md` §01-filo-nudo B0.3 e B8.
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
> | **1** | ~~accendere `src/` una volta~~ ✅ **fatto il 15 agosto 2026**, e più volte: `src/costruisci.sh` dentro `enter.sh` sulla macchina di prova, dieci giri | ⭐ E c'è una **seconda** strada, nata quella notte: `src/Contenitore` + `src/costruisci-in-contenitore.sh` — `podman` **da utente**, sul portatile, senza `sudo`. Le due rispondono a due domande diverse: *«compila?»* si chiede al portatile in venti secondi, *«gira?»* si chiede solo alla macchina di prova. Vedi `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` §1 |
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
> e l'altro si chiama il comando di sblocco, **mai dentro il giro di B8** (`FASI.md` §01-filo-nudo,
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
> **Fase 0 chiusa**: i banchi riproducono i numeri di v1 (`FASI.md` §00-ambiente).
> **Nessuna riga di codice di prodotto ancora scritta.**
>
> La giornata ha cambiato il prodotto e poi ha controllato il cambiamento:
>
> | | |
> |---|---|
> | ⭐ **il client è il browser** | cadono i due client nativi e cinque fasi di piano — `DECISIONI.md` §1.6 |
> | **la sicurezza è a due livelli** | TLS per il trasporto, indirizzo/porta/utente/password per l'accesso — §1.7 |
> | **la seconda connessione remota si rifiuta** | `RCP.md` §8.2, motivo `0x0F` |
> | 📖 **il sesto studio** | [`STUDI.md` §web](STUDI.md#web), con quattro rapporti in `web/rapporti/` |
> | ⛔ **due revisioni avversariali** | **46 rilievi numerati** — **29** in `web/rapporti/R1-revisione-rcp.md` e **17** in `R2-revisione-web.md` — **più le 12 omissioni** `O1`-`O12` di `R2` §2, e tutti **prima del primo byte**. ⚠ *Diceva «**51** contraddizioni», e quel numero non si ritrova con nessun criterio scritto: 29 + 17 = 46, e nessuna somma dichiarata da nessuna parte dà 51 (rilievo **R11.20**, chiuso la notte del 10 agosto 2026 **dichiarando che cosa si conta**). Le omissioni si contano a parte perché non sono contraddizioni: sono righe che **non c'erano**, e per definizione nessun controllo delle citazioni le trova* |
>
> ### Il prossimo passo
>
> ⭐ **`FASI.md` §01-filo-nudo è aperto e già revisionato**, con i banchi e **nessuna riga di
> prodotto scritta** — il documento si apre *prima* di sviluppare (`PIANO.md` §0.1).
>
> ⛔ **Due revisioni avversariali sul banco, prima del prodotto: 44 rilievi — 38 `[R]`, 6 `[?]`.**
> Nessuna delle due verde, e il documento è stato **riscritto**, non rattoppato. I verdetti stanno
> in `fasi/rapporti/R3-` (il banco come strumento) e `R4-` (la coerenza con quel che è scritto).
> La forma che si ripeteva: **cadeva sempre il controllo che dice *no***, e tre volte era già stato
> scritto da chi ci era passato prima.
>
> ⚠ **E la cura è uscita da quel file**: `RCP.md` §4.1-bis diceva ancora che WebKit non implementa
> `serverCertificateHashes` — ed è **l'arbitro**; `STUDI.md` §web ha riavuto i controlli negativi che i
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

## Gli studi — ⭐ **tutti in un documento solo**, [`STUDI.md`](STUDI.md), dal 16 agosto 2026

*Erano otto file nella radice. Sono diventati **otto capitoli** di un documento solo, per decisione
dell'utente. ⛔ **Non un riassunto**: il testo è quello che era, riga per riga, con i titoli
abbassati di un livello. ⇒ Un rimando che diceva `kde.md` §3.3-bis adesso dice `STUDI.md` §kde
3.3-bis, e **le chiavi dei capitoli sono i nomi che avevano i file**.*

Letture del codice, fatte prima di scrivere. I cinque dei desktop rispondono alle **quindici**
domande di `LEZIONI.md` §3.

[`STUDI.md` §gnome](STUDI.md#gnome) · [`STUDI.md` §kde](STUDI.md#kde) · [`STUDI.md` §xfce](STUDI.md#xfce) · [`STUDI.md` §lxqt](STUDI.md#lxqt) ·
[`STUDI.md` §cinnamon](STUDI.md#cinnamon)

⭐ **E il sesto, che non parla di un compositore**: [`STUDI.md` §web](STUDI.md#web) — il browser come client,
con i quattro rapporti di dettaglio in `web/rapporti/`. ⚠ **È quello che invecchia più in fretta**:
i compositori li congela Debian, i browser si aggiornano da soli.

⭐⭐ **E il settimo, che non parla di una tecnologia ma di un PRODOTTO**: [`STUDI.md` §xpra](STUDI.md#xpra) — chi
questo mestiere lo fa già, letto nel suo codice il 14 agosto 2026. ⛔ Doveva essere fatto **prima**
della pagina (`PIANO.md` §1.3) ed è stato fatto **dopo**, su richiesta dell'utente: ⇒ nel frattempo
avevamo scritto una specifica che si contraddiceva, e a trovarla è stato lui in trenta secondi
d'uso.

⛔ **E accanto ai quattro, un quinto file che non è uno studio**:
[`web/rapporti/S-esiti-sonda.md`](web/rapporti/S-esiti-sonda.md) — **gli esiti misurati** della sonda
del browser (S7 · S1b · S5 · e le tre che aspettano un dispositivo), con la scena accanto a ogni
numero e la ricontata che dice quali numeri hanno una provenienza su disco. ⚠ *I «quattro rapporti»
qui sopra restano quattro: sono i rapporti degli **studi**, ed è un denominatore dichiarato.*

⚠ **`STUDI.md` §gnome-remote-desktop non è uno di questi** *(chiarito il 9 agosto 2026)*. Studia **il
server RDP di GNOME**, cioè un concorrente sul filo che abbiamo buttato — non il desktop. Con RDP
morto decade quasi per intero, ed è scritto su una versione che Trixie non ha (51.alpha contro
48.1). **Su GNOME si legge [`STUDI.md` §gnome](STUDI.md#gnome)**, che parla di Mutter e resta valido.

---

## Le cartelle

⚠ *Questa tabella elencava **tre** voci — `fasi/`, `v1/`, `reference-*/` — e non aveva né `src/` né
`banchi/` né `web/`: **la cartella che contiene il prodotto non compariva nella tabella che dice che
cosa contengono le cartelle**. Completata l'11 agosto 2026, rilievo **R12C.1**.*

| | |
|---|---|
| ⭐⭐ `src/` | **il prodotto**: il server della fase 1 in C — **22 file, 9.647 righe** `[M]` 11 ago 2026. RCP/1 su WebTransport, i due certificati, la pagina servita dal server, il ban e il suo comando di sblocco. ⛔ **Non è in git**, e nessun banco lo accende ancora |
| ⭐ `banchi/` | **i banchi della fase 1** e la sonda del browser, più `banchi/rcp/` — la copia **gemella** di `rcp.c`/`rcp.h`/`autenticazione.c`, oggi identica a quella di `src/` byte per byte. ⚠ Qui il bersaglio è **l'innesto** dentro `bsslserver`, non `src/` |
| `fasi/` | ⚠ **c'è solo mentre una fase è aperta**, e contiene il documento di quella fase soltanto: alla chiusura diventa un capitolo di [`FASI.md`](FASI.md) e la cartella torna vuota (`PIANO.md` §0.1) |
| ⛔ ~~`web/rapporti/`, `fasi/rapporti/`~~ | **tolte il 16 agosto 2026** per decisione dell'utente — 94 file di rapporti degli agenti. ⭐ Restano per intero nella storia: come si rilegge o si recupera un rapporto sta in **`FASI.md`**, in testa |
| `v1/` | ⚠ **non è solo archivio, e questa riga lo diceva male**: l'eredità di REMOTIX v1 — 17.481 righe di C, i banchi, i documenti, le scene di taratura — ⭐ **ma dentro ci sono due cose VIVE**, `v1/banco/enter.sh` (il modo in cui si entra nella macchina di prova, **193 citazioni**) e `v1/strumenti/sshpw.py` (**81**, lo chiamano i banchi di V2). La mappa completa — vivo, archivio, morto, con le citazioni contate — sta in **`DECISIONI.md` §6.1** |
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
