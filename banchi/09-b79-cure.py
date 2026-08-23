#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b79-cure — LE DUE CURE DELLA SPIRALE, APPAIATE SU UNA RETE CHE PERDE.

    porta 7940 · sonde 7949..7945 · utente `provanr4` (uid 1040)
    albero `/media/REMOTIX/src/09nr4-src` · lavoro `/media/REMOTIX/tmp/09nr4`
    unita' `remotix-7940` · ban-file e socket suoi

═══════════════════════════════════════════════════════════════════════════════
⛔ DA DOVE NASCE — e sono numeri, non intenzioni
═══════════════════════════════════════════════════════════════════════════════

`09-b76-rete-cattiva.py` ha chiuso `[M]` il 23 agosto 2026 la griglia della rete
cattiva, a **tutte le cure spente** (i predefiniti, invariante I6), e cinque
profili su undici sono rossi.  Il meccanismo, letto dal registro del server:
`abbandonato_in_coda` = `abbandonati` = `chiave_aspetta` a ogni profilo rosso,
con `delta_non_spedito` a 550-800.  ⇒ La catena e':

    il filo ritarda → la coda di spedizione cresce → §5.1 abbandona i delta
    → §5.2 accende il debito → si chiede una chiave → la chiave riempie la
    finestra → ricomincia.

⭐ E' **la spirale**, e a `perdita-3` fa 87 chiavi su 87 fotogrammi — la stessa
   faccia del difetto del 21 agosto (144/144).

⭐⭐⭐ E LA CURA DI QUESTA SPIRALE E' GIA' SCRITTA, COLLAUDATA E SPENTA.  Due
      interruttori, e hanno un ORDINE OBBLIGATO (`src/webtransport.c:2780`):

  · `--sgombra-soglia-ms N` — la soglia sulla coda.  `video_sgombra()` oggi
    abbandona i delta **a ogni fotogramma**; con la soglia li abbandona solo
    quando la coda e' davvero senza speranza (`byte × smoothed_rtt / cwnd`
    sopra N ms).  ⛔ E' il prerequisito dell'altro.
  · `--ritmo-adattivo` — il regolatore del ritmo: invece di abbandonare,
    rallenta la cattura.  ⛔ Viene DOPO la soglia, perche' finche'
    `video_sgombra()` svuota la coda a ogni fotogramma la grandezza su cui si
    aggancia (`arretrato`) e' **zero per costruzione**, e un regolatore muto e
    una linea sana hanno la stessa faccia.

⇒ La domanda di questo banco: **quelle due cure spengono la spirale su una rete
  che perde e sfarfalla, e a che prezzo?**

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ APPAIATO VUOL DIRE **UNA COSA SOLA CAMBIATA**
═══════════════════════════════════════════════════════════════════════════════

Stesso profilo, stessa durata, stessa tela, stessa scena, **stesso binario**, e
a cambiare solo gli interruttori del server.  Tre bracci per ogni profilo:

    A   (i predefiniti: le due cure SPENTE)
    B   --sgombra-soglia-ms 100
    C   --sgombra-soglia-ms 100 --ritmo-adattivo

⛔⛔ E IL BRACCIO **A** SI RIMISURA OGGI, non si riprende dalla tabella di
    `09-b76`.  Quei numeri vengono da un altro binario (HEAD, che non ha
    nemmeno le due opzioni) e da un'altra ora: usarli come braccio A sarebbe
    confrontare due cose diverse e chiamarlo appaiamento — ed e' esattamente il
    modo piu' educato in cui una griglia mente (`LEZIONI.md` §1.26).

⭐ L'ORDINE DENTRO IL PROFILO E' A-B-C, uno di fila all'altro, non A-A-A poi
   B-B-B: cosi' fra i tre bracci di uno stesso profilo passano tre minuti, non
   venti, e la macchina e' la stessa macchina.  ⚠ Costa 21 riavvii del server;
   sono venti secondi l'uno, ed e' il prezzo dell'appaiamento.

⛔⭐ E OGNI BRACCIO SI VERIFICA DAL REGISTRO DEL SERVER, non da quel che ho
    scritto sulla riga di comando (`LEZIONI.md` E1, «scritto non e' in
    vigore»).  Il prodotto scrive all'avvio, SEMPRE — acceso e spento — le due
    righe che dicono il valore in vigore (`sgombra_dichiara()`,
    `wt_ritmo_adattivo()`), e questo banco le rilegge e si ferma se non
    combaciano.

═══════════════════════════════════════════════════════════════════════════════
⛔ LA SEQUENZA DI UN BRACCIO, e ogni passo ha una ragione
═══════════════════════════════════════════════════════════════════════════════

 1. **la rete si rimette liscia**;
 2. **il server si riavvia** con le opzioni del braccio, e le due righe d'avvio
    si rileggono;
 3. **si innesca una sessione corta** — il palco e il monitor nascono col primo
    cliente, e la scena non saprebbe dove disegnare.
    ⛔⭐ E si innesca **A RETE PULITA**, apposta: `09-b78-apertura.py` ha
        misurato che un addio **perso** e un addio **mai detto** sono lo stesso
        fatto per il server, e il posto resta occupato per `SILENZIO` = 30 s
        (`src/rcp.c:263`) — undici `CONGEDO 0x0F` di fila, `[M]` 23 agosto.  Se
        innescassi sotto il guasto, il giro dopo potrebbe trovare il posto
        occupato e darei per «la cura non funziona» una serratura di trenta
        secondi.
 4. **si installa il profilo** (`del root` + `add`, mai `change`: `[M]` 23 ago,
    `tc qdisc change` e' appiccicoso), si rileggono i verbi, si rimettono i due
    filtri `u32` della sonda;
 5. **la sonda** — 8 000 pacchetti numerati attraverso lo stesso `netem`: il
    guasto e' stato messo o no?  ⛔ E si rifa a OGNI braccio, non una volta per
    profilo: un numero senza il suo guasto verificato accanto non e' una misura;
 6. **il giro**, 25 s, 1920×1080, scena `barra`;
 7. si leggono i contatori del `qdisc` attorno al giro e le righe `rete-quic`
    del registro (`cwnd`, `srtt_us`, `pto_us`, `dgram_persi`, `dgram_falsi`,
    `giudizio=`), che nell'albero di lavoro ci sono e in HEAD no.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LA REVISIONE DEL 23 AGOSTO SERA — «quali numeri erano sporcati», VERIFICATO
═══════════════════════════════════════════════════════════════════════════════

La griglia a tre bracci di stasera e' girata mentre `_root_che_trascrive`
avvolgeva `RETE.root` invece della `root` curata di b70 (⇒ il riquadro sopra
quella funzione).  ⇒ Va detto quali numeri quella riga ha sporcato, e la risposta
si LEGGE, non si suppone.  Sono tre verifiche, e nessuna e' un ragionamento:

 1. ⭐ **LA RIGA NON HA SPORCATO NIENTE SU QUESTA GRIGLIA — era un difetto ancora
    da riscuotere.**  `[R]` alle 19:00 del 23 agosto `09-b70-ritmo.py` a HEAD
    aveva ancora `def root(comando, tetto=300): return RETE.root(comando, tetto)`
    (riga 1236): la cura di b70 e' delle 19:41, **dopo**.  ⇒ Avvolgere `RETE.root`
    era allora identico ad avvolgere `B70.root`, e il difetto e' PROSPETTICO —
    avrebbe morso il giro successivo, quello con b70 curato.  ⚠ E' esattamente il
    motivo per cui va curato lo stesso: la sua faccia non cambia quando comincia
    a mentire.
 2. ⭐ **LA `riga0` C'ERA, e i conti del server sono DI QUESTO GIRO.**  `[R]`
    `09-b76-rete-cattiva.py` a HEAD (riga 297) sostituisce gia'
    `B70.righe_registro` con la sua, che mette il redirect dentro un `bash -c`.
    ⇒ Il difetto 2 di b70 (il `< file` che ruba lo stdin a `sudo -S`) **non ha
    sparato**: b79 non passava nemmeno dalla funzione rotta.
    `[M]` la controprova nei numeri, ed e' la firma opposta a quella cumulativa:
    su tutte e 36 le caselle `righe_ciclo` sta fra **25 e 27** (un giro di 25 s) e
    `attese_a_vuoto` fra **1 973 e 2 156** — costante, non in salita.  Su
    `ritardo-30` A-B-C fa 2 015 / 2 006 / 2 016.  Il cumulativo si vede a occhio
    (`[M]` b70: 4 041 contro 1 604, 2,5 volte, e in salita): qui non c'e'.
 3. ⭐ **IL CONTO DI UN ALTRO GIRO E' STRUTTURALMENTE IMPOSSIBILE QUI**, e non
    per fortuna: `[R]` `07-b64-terreno.sh:106` fa `: > "$LAV/registro.log"` a ogni
    `accendi`, e questo banco riaccende il server a **ogni braccio**.
    `[M]` la controprova: nessuna coppia di caselle porta numeri identici dal
    registro, e tre caselle (`perdita-3` A, `raffica-forte` A e B) hanno detto
    **«NIENTE DA LEGGERE»** invece di riferire il numero del vicino — che e' la
    prova che nella finestra non c'era nessun conto altrui da rubare.

⭐⭐ E LA COSA CHE CONTA DI PIU', ed e' una divisione, non un'assoluzione:
   **il verdetto non passa dal registro.**  `[R]` `p_spirale_spenta` (K′),
   `p_ritmo_restituito` (F′) e `p_linea_sana` (S′) leggono solo `n["chiavi"]`,
   `n["fotogrammi"]`, `n["quota_delta"]`, `n["fps"]`, `n["fps_finestra_min"]` e
   `n["deriva_*"]` — tutti da `misura(giornale, …)`, cioe' dalla **traccia §11.1
   del cliente**.  Dal registro del server vengono i quattro numeri che
   CORROBORANO (`delta_non_spedito`, `chiave_aspetta`, `non_spediti`,
   `abbandonati`) e nient'altro.
   ⇒ «la spirale si spegne, ma solo col braccio C: chiavi da 51,7-88,1 % a
     0,0-5,6 %» e «la linea sana non paga niente» non sono numeri del registro, e
     non avevano nulla da cui essere sporcati.  ⚠ Rifare i cinque profili rossi
     costa un'ora e non aggiunge niente (`LEZIONI.md`, processo proporzionato).

⭐⭐ E UNA SOLA CASELLA SI E' RIFATTA LO STESSO — `ritardo-30` a tre bracci, che
   e' il predicato che vale piu' di tutti («la linea sana non paga niente») e
   costa otto minuti, non un'ora.  Non e' un dubbio sui numeri: e' la sola prova
   che la catena CURATA gira davvero fino in fondo, e che le due guardie nuove
   scattano.  `[M]` 23 agosto 2026 sera, stesso binario (md5 `eee17f40…`):

     braccio    fps    peggior s   chiavi   deriva fine   deriva max
        A     39,94/s     37,0      0,0 %      0,0 ms      10,1 ms
        B     39,94/s     36,0      0,0 %      0,2 ms      11,0 ms
        C     39,32/s     34,0      0,0 %     -0,1 ms       6,2 ms

   ⇒ **S′ VERDE**: i tre bracci sono indistinguibili (B al 100 %, C al 98 %,
     dentro il 5 % di rumore), zero chiavi ovunque, la deriva non si muove.
     ⭐ E regge il confronto con le 19:00 (39,85 / 40,19 / 39,63): la stessa
       risposta a otto minuti di distanza.
   ⭐ La riprova nei conti del server, che e' quella che chiude la questione: le
     righe della spirale del braccio A tornano **identiche** a quelle delle 19:00
     (`chiave_aspetta` 1, `delta_non_spedito` 5, `abbandonato_in_coda` 1) e
     `attese_a_vuoto` fa 2 019 / 2 016 / 2 025 contro 2 015 / 2 006 / 2 016.  Un
     numero cumulativo non si riproduce; questi si riproducono.
   ⭐ E le guardie nuove hanno parlato: `riga0` = 205 / 219 / 229, `p_registro_letto`
     VERDE su tutt'e tre, `conti_finali` `[2, 4]` in ogni braccio — cioe' i due
     conti dell'innesco erano gia' posati e il giro ne ha scritti due SUOI.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I PREDICATI DELLA COPPIA — SCRITTI PRIMA, e ne torna `(passa, perche)`
═══════════════════════════════════════════════════════════════════════════════

Quelli del singolo giro si IMPORTANO da `09-b70`/`09-b76` e non si riscrivono
(`p_niente_stacco`, `p_degrada_nel_tempo`, `p_guasto_messo`, `p_coda_mia`).  I
tre che sono di questo banco guardano la **coppia**, che li' non esiste:

  **K′ · LA CURA SPEGNE LA SPIRALE.**  La quota di chiavi del braccio torna
  sotto 0,10 dove il braccio A la aveva sopra.
  ⚠ La soglia non e' scelta qui: e' il complemento di `QUOTA_DELTA = 0,90` di
    `09-b70`, cioe' §3.3 letto al contrario.  Due soglie per lo stesso fatto
    sono due soglie che divergono.
  ⛔ E TACE se in A la spirale non c'era: spegnere un incendio che non c'e' non
     e' un merito, ed e' un verde che si prenderebbe da solo.

  **F′ · LA CURA RESTITUISCE RITMO.**  I fotogrammi/s del braccio contro quelli
  di A, con la soglia e la ragione scritte:
  ⚠ `09-b70` stima al **5 %** il rumore fra due giri della stessa macchina.  ⇒
    Sotto il **10 %** di differenza — il doppio del rumore — questo banco
    **non giudica**: dice «indistinguibile», che e' un esito e non un verde.
    Sopra il 10 % in su e' verde; sopra il 10 % in giu' e' ROSSO, perche' una
    cura che toglie ritmo dove voleva darne e' la scoperta piu' importante che
    possa uscire di qui.

  **S′ · LA CURA NON COSTA SULLA LINEA SANA.**  ⛔ E' il predicato che vale piu'
  di tutti gli altri messi insieme: su `ritardo-30` — che perde zero, riordina
  zero, e arriva solo tardi — i tre bracci devono essere **indistinguibili**.
  Le tolleranze, e ciascuna col suo perche':
    · fotogrammi/s entro il **5 %**, che e' il rumore che `09-b70` misura fra
      due giri della stessa macchina: dentro quello non c'e' niente da vedere;
    · quota di chiavi sotto **0,10** in tutt'e tre, come sopra;
    · deriva finale che non cresce di piu' della **soglia stessa** (100 ms).
      ⭐ E questo numero non e' arbitrario: la cura tiene un delta finche' la
      coda non e' senza speranza per piu' di N ms, quindi il ritardo che puo'
      aggiungere e' N per costruzione.  Se ne aggiunge di piu', non e' la
      soglia che sta lavorando — e' qualcos'altro, e va guardato.

  ⚠⚠ **E IL PREZZO SI MISURA, NON SOLO IL GUADAGNO.**  La soglia sulla coda
  **tiene** i fotogrammi invece di buttarli ⇒ la **deriva** puo' crescere.  ⭐
  La deriva si riporta SEMPRE accanto ai fotogrammi/s: una cura che raddoppia
  il ritmo e triplica il ritardo **non e' ovviamente un miglioramento**, ed e'
  una scelta che spetta all'utente, non a questo banco.  ⇒ Qui non c'e' nessun
  predicato «B e' meglio di A»: ci sono i due numeri, accanto.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ `raffica-forte` — «SESSIONE STACCATA A 0,3 s SU 25», e la parola e' sbagliata
═══════════════════════════════════════════════════════════════════════════════

`09-b76` da' rosso su `raffica-forte` col predicato `p_niente_stacco`, che dice
*«la consegna e' durata 0,3 s su 25 chiesti: si e' staccata»*.  ⛔ Ma quel
predicato non guarda la connessione: guarda **quanto e' durata la consegna dei
fotogrammi**, e le due cose non sono la stessa.  ⇒ Il passo `stacco` di questo
banco chiede **chi** ha staccato, e lo chiede a quattro testimoni indipendenti:

  1. **il cliente**, che lo dice da solo e per esteso: `01-b3-cliente.py:1979`
     stampa *«⭐ ancora attaccato dopo N s: niente e' caduto»* e torna 0, oppure
     *«⛔ NON sono rimasto attaccato: …»* e torna 4;
  2. **il registro del server**: `congedo motivo=0x..`, `il client si congeda`,
     `posto NEGATO`, `BANNATO`, e il «conto finale» del video;
  3. **le righe `rete-quic`**: `cwnd`, `cwnd_left`, `giudizio=` — se la finestra
     si e' chiusa e non si e' piu' riaperta, la sessione e' viva e **muta**, che
     e' un fatto diverso dallo stacco e ha bisogno di un nome diverso;
  4. ⚠ **la terza possibilita' da escludere esplicitamente**: a 13 % di perdita
     a grappoli la STRETTA DI MANO potrebbe non completarsi, e «non si e' mai
     aperta» e «si e' staccata» hanno la stessa faccia.  ⭐ La distingue il
     cliente stesso, che stampa `SESSIONE` solo quando la sessione e' aperta;
     e `09-b78-apertura.py` ha gia' misurato `[M]` che fino al **25 %** di
     perdita indipendente la sessione si apre 10 volte su 10 in ~1,3 s.

⛔ `IDLE_MS` in `src/trasporto.c` e' **30 s**: a 0,3 s non e' lui, e infatti il
   passo `stacco` lo rilegge dal sorgente invece di fidarsi di questa riga.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ CHE COSA QUESTO BANCO **NON** SA VEDERE
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **L'IMMAGINE.**  Conta fotogrammi, chiavi, byte e ritardo.  «Si vede
    meglio con la cura accesa» e' un verdetto dell'utente sul desktop vero.
 2. ⛔ **QUALE BRACCIO E' MEGLIO.**  Vedi il prezzo, qui sopra: e' una scelta,
    non una misura.
 3. ⛔ **LA RETE VERA.**  `netem` su `lo`: nessuna radio, nessun router.
 4. ⛔ **IL BROWSER.**  Il cliente e' `01-b3-cliente.py`, che prende i byte dal
    filo e non decodifica: i fotogrammi/s sono un **tetto**.
 5. ⚠ **UN SOLO GIRO PER CASELLA.**  Ventuno caselle da 25 s sono gia' mezz'ora
    di lucchetto; una differenza sotto il 10 % non si distingue dal rumore, ed
    e' per questo che F′ tace li' invece di giudicare.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐⭐ QUEL CHE E' USCITO — `[M]` 23 agosto 2026, porta 7940, Intel UHD 730
═══════════════════════════════════════════════════════════════════════════════

Binario **md5 `eee17f40b0a5ff79fe3b1b3d060a08ed`** (albero di lavoro, non HEAD;
`webtransport.c` md5 `0f63542bf2ebf3617afa5b0a5bfe2371`), 25 s per casella,
1920×1080, h264, banda libera, scena `barra`, un giro per casella.  Ogni braccio
verificato dalle due righe d'avvio del prodotto; il guasto verificato dalla
sonda a ogni casella; nessuno attaccato alle porte non mie prima ne' dopo.

⭐⭐ **LE DUE RIGHE IN TESTA: LA SPIRALE SI SPEGNE SI', E LA SPEGNE `C`, NON `B`.
    E COSTA IN RITARDO DA ZERO A UN DECIMO DI SECONDO SUI PROFILI ORDINARI, E
    QUATTRO SECONDI E MEZZO SU `raffica-forte`.**

| profilo | br | fps | peggior s | chiavi % | deriva fin. | deriva max | Mbit/s filo |
|---|---|---|---|---|---|---|---|
| `ritardo-30` ⭐sana | A | 39,85 | 36 | 0,0 % | 0,1 | 8,9 | 7,55 |
|                     | B | 40,19 | 37 | 0,0 % | 0,2 | 5,8 | 7,60 |
|                     | C | 39,63 | 36 | 0,0 % | 0,9 | 6,1 | 7,53 |
| `perdita-1`   | A | 11,96 | 5 | **51,7 %** | −2,4 | 76,5 | 3,43 |
|               | B | 32,13 | 17 | 6,4 % | 23,2 | 107,8 | 4,84 |
|               | C | **32,85** | 21 | **0,0 %** | −1,6 | 99,3 | 5,11 |
| `perdita-3`   | A | 7,34 | 5 | **88,1 %** | −40,0 | 53,4 | 2,17 |
|               | B | 20,63 | 11 | ⛔ 23,8 % | 32,9 | 139,3 | 2,90 |
|               | C | 19,63 | 11 | **0,2 %** | −62,2 | 165,7 | 2,79 |
| `jitter-15`   | A | 10,76 | 6 | **59,2 %** | 11,7 | 102,1 | 3,48 |
|               | B | 25,88 | 9 | ⛔ 12,8 % | −65,7 | 64,0 | 8,06 |
|               | C | 21,48 | 15 | **0,0 %** | 53,8 | 168,4 | 6,63 |
| `jitter-30`   | A | 8,56 | 5 | **73,1 %** | 6,7 | 115,6 | 2,55 |
|               | B | 20,25 | 10 | ⛔ 19,9 % | −5,0 | 277,0 | 5,77 |
|               | C | 16,68 | 12 | **0,0 %** | −116,0 | 180,8 | 4,96 |
| `casa-cattiva`| A | 8,28 | 3 | **72,0 %** | −71,5 | 295,3 | 2,21 |
|               | B | 14,37 | 6 | ⛔ 33,6 % | 152,7 | 238,4 | 3,01 |
|               | C | 13,86 | 4 | **5,6 %** | 102,2 | 284,2 | 3,38 |
| ⚠ `raffica-forte` | A | — la consegna si ferma a **4,4 s** su 25 | | | | | |
|               | B | 4,25 | **0** | 44,6 % | 24,9 | **7 756** | 0,59 |
|               | C | 4,18 | **0** | 4,4 % | 2,1 | **4 521** | 0,78 |

1. ⛔⛔ **S′ · SULLA LINEA SANA LE CURE NON COSTANO NIENTE.**  39,85 / 40,19 /
   39,63 fotogrammi/s — un punto percentuale, dentro il rumore dichiarato del
   5 % — zero chiavi in tutt'e tre, e la deriva finale a 0,1 / 0,2 / 0,9 ms.
   ⭐ E' il predicato che valeva piu' di tutti gli altri, ed e' verde.

2. ⭐⭐⭐ **LA SPIRALE SI SPEGNE, MA SOLO CON TUTT'E DUE GLI INTERRUTTORI.**  La
   quota di chiavi passa da 51,7-88,1 % (braccio A) a **0,0-5,6 %** nel braccio
   C, su tutti e cinque i profili rossi.
   ⛔ Il braccio **B** — la sola soglia — **non basta**: lascia 12,8 % di chiavi
      a `jitter-15`, 19,9 % a `jitter-30`, 23,8 % a `perdita-3` e 33,6 % a
      `casa-cattiva`, cioe' sopra il 10 % di §3.3.  ⇒ K′ e' ROSSO su B in
      quattro profili su cinque e verde su C in tutti e cinque.
   ⭐ Il perche' si legge nei contatori del server: in C `chiave_aspetta` e
      `delta_non_spedito` **crollano** (su `raffica-forte`: 988 → 6 delta non
      spediti, 32 → 0 chiavi aspettate).  La soglia da sola smette di buttare a
      ogni fotogramma ma il debito di §5.2 continua a accendersi; il regolatore
      lo previene, perche' il fotogramma non parte affatto.

3. ⭐ **IL RITMO TORNA, DA 1,7 A 2,8 VOLTE**, e su ogni profilo rosso: F′ e'
   verde su B e su C dappertutto.  Il massimo e' `perdita-3`, 7,34 → 20,63/s
   (+181 %); il minimo `casa-cattiva`, 8,28 → 13,86/s (+67 %).
   ⚠ E B da' quasi sempre **piu'** fotogrammi/s di C (25,88 contro 21,48 a
     `jitter-15`; 20,25 contro 16,68 a `jitter-30`), perche' C rallenta la
     cattura apposta: ⇒ i due bracci non sono «meno buono e piu' buono», sono
     **piu' fotogrammi con piu' chiavi** contro **meno fotogrammi tutti delta**.

4. ⚠⚠ **IL PREZZO, E VA LETTO ACCANTO AL GUADAGNO.**  Sui cinque profili
   ordinari la deriva massima cresce di **−38 … +161 ms** (peggio: `jitter-30`
   B, da 116 a 277 ms; su `casa-cattiva` e `jitter-15` B **cala**).  Sul
   `raffica-forte` esplode: **da nessuna misura a 4,5-7,8 secondi**.
   ⛔ Su quella linea C non e' ovviamente meglio di A: e' *un'immagine che si
      muove con cinque secondi di ritardo* contro *un'immagine ferma*.  Questo
      banco da' i due numeri e **non sceglie**: la scelta e' dell'utente.

5. ⭐ E i byte sul filo **salgono** con la cura (3,43 → 5,11 Mbit/s a
   `perdita-1`, 3,48 → 8,06 a `jitter-15`): la linea non era satura, era
   **sprecata** — si spedivano chiavi al posto di delta.

6. ⭐⭐ **`raffica-forte`: NESSUNO STACCA.**  Vedi il passo `stacco` piu' sopra e
   il §che gli e' dedicato: `[M]` il cliente resta attaccato tutti i 25 s
   («⭐ ancora attaccato dopo 25.0 s: niente e' caduto»), l'audio arriva per
   tutto il giro (696 datagram, purezza 1,0000), il server non manda nessun
   `CONGEDO`, nessun `posto NEGATO`, nessun ban, e la sessione si era aperta
   normalmente (`AMMESSO dopo 1837 ms`).  A fermarsi e' **la sola consegna dei
   fotogrammi**.  ⇒ Il rosso di `09-b76` e' giusto come numero e **sbagliato
   come parola**.  ⭐ E le cure lo cambiano: la consegna, che in A muore dopo
   4,4 s, in B e C **dura tutti i 25 s** (4,2/s con secondi vuoti dentro).

I CODICI D'USCITA
    0   CONFORME · 1 NON CONFORME (c'e' un rosso) · 2 uso/terreno/rete
    3   ⛔ NON HO NIENTE DA GIUDICARE — un giro o un predicato si e' rifiutato

Uso (dal portatile):
    python3 banchi/09-b79-cure.py --certifica     ⭐ senza macchina
    python3 banchi/09-b79-cure.py terreno
    python3 banchi/09-b79-cure.py stacco          ⛔ la diagnosi di raffica-forte
    python3 banchi/09-b79-cure.py appaia [--secondi 25] [--solo perdita-1]
    python3 banchi/09-b79-cure.py rimetti
"""
import argparse, importlib.util, json, os, re, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL MIO ISOLAMENTO, SCRITTO PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b76` e `09-b70` legano le loro costanti all'ambiente **all'import**.
#    Importarli senza aver messo prima il mio vorrebbe dire scrivere nel lavoro
#    di un altro agente e guastare la porta di un altro banco — e la rete e'
#    l'unica cosa che, sbagliata, fa male a chi non c'entra.
# ⛔ Le 7900, 7910, 7920 sono termini di paragone gia' misurati e NON si
#    toccano; la 7930/7931/7932 sono di altri tre agenti.  Mia e' la **7940**.
QUI = os.path.dirname(os.path.abspath(__file__))
MIO = {
    "PORTA": "7940",
    "UTENTE": "provanr4",
    "UID_B": "1040",
    "MACCHINA": "nicfio@192.168.0.2",
    "PAROLA_SUDO": "nicfio",
    "IND": "192.168.0.2",
    "LAV": "/media/REMOTIX/tmp/09nr4",
    "ALBERO": "/media/REMOTIX/src/09nr4-src",
    "DENTRO_ALB": "/srv/src/09nr4-src",
    "DENTRO_LAV": "/srv/remotix/tmp/09nr4",
    "UNITA": "remotix-7940",
    "SHM": "/09nr4",
    # ⛔ La porta della sonda non puo' essere fissa: `09-b76` ha perso un giro
    #    intero perche' un altro agente le ha acceso un server sopra MENTRE
    #    girava.  ⇒ cinque candidate mie, e si sceglie quella libera adesso.
    "PORTE_SONDA": "7949,7948,7947,7946,7945",
    "FUORI": os.environ.get(
        "FUORI",
        "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
        "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09nr4"),
}
for _k, _v in MIO.items():
    os.environ[_k] = os.environ.get(_k) or _v

PORTA = int(os.environ["PORTA"])
UTENTE = os.environ["UTENTE"]
LAV = os.environ["LAV"]
ALB = os.environ["ALBERO"]
UNITA = os.environ["UNITA"]
FUORI = os.environ["FUORI"]
PAROLA_SUDO = os.environ["PAROLA_SUDO"]
MACCHINA = os.environ["MACCHINA"]
VIETATA = "enp7s0"
DEV = "lo"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ TUTTA LA MACCHINERIA SI IMPORTA — non se ne riscrive una riga
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b76-rete-cattiva.py` porta i profili, la sonda, la riduzione degli
#    arrivi, la rilettura della regola, i contatori del `qdisc` e 31 casi di
#    `--certifica` verdi; `09-b70-ritmo.py` porta il lettore della traccia
#    §11.1, la riduzione ai cinque numeri e i predicati del singolo giro.  Due
#    copie della stessa riduzione in due file sono due riduzioni che divergono
#    (e' la ferita del 16 agosto, `09-b70` riga ~430).
B76 = None
B70 = None
RETE = None
LUC = None


def importa(con_rete=True):
    global B76, B70, RETE, LUC
    B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))
    if not con_rete:
        B76.importa_finto()
        B70 = B76.B70
        return
    B70 = B76.importa()          # ⭐ e' lui che aggancia la rete e il lucchetto
    RETE = B76.RETE
    LUC = B76.LUC
    _aggancia_root()                 # ⛔ vedi `_root_che_trascrive`
    # ⛔⛔ E POI SI CONTROLLA CHE ABBIANO PRESO IL MIO AMBIENTE, non il loro.
    guai = []
    for nome, mio, suo in (("porta", PORTA, B76.PORTA), ("utente", UTENTE, B76.UTENTE),
                           ("lavoro", LAV, B76.LAV), ("albero", ALB, B76.ALB),
                           ("shm", os.environ["SHM"], B76.SHM),
                           ("dev", DEV, B76.DEV), ("vietata", VIETATA, B76.VIETATA)):
        if str(mio) != str(suo):
            guai.append("%s: il modulo ha «%s», il mio e' «%s»" % (nome, suo, mio))
    if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
        guai.append("il modulo della rete ha porta %d, dev «%s», vietata «%s»"
                    % (RETE.PORTA, RETE.DEV, RETE.VIETATA))
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import non ha preso il mio ambiente — "
                         + " · ".join(guai))


def root(comando, tetto=300):
    """⛔ Anche la `root` di questo file passa dalla catena CURATA quando c'e'.

    ⚠ I comandi di questo file si scrivono gia' tutti dentro un `bash -c "…"`
      loro — e' la disciplina di `09-b76` — quindi qui non cambia un numero.
      Ma la disciplina e' una convenzione, e una convenzione la dimentica il
      prossimo che aggiunge una riga: `RETE.root` da sola gli darebbe uno `0`
      plausibile invece di un errore (⇒ il riquadro sopra `_aggancia_root`).
    """
    if _ROOT_CURATA is not None:
        return _ROOT_CURATA(comando, tetto)
    return RETE.root(comando, tetto)


# ⛔⛔ IL CLIENTE VA ASCOLTATO PER INTERO, e non lo e'.
#
#    `09-b70.giro()` conserva `coda_cliente = testo[-400:]`, che bastano ai
#    cinque numeri e **non** alla domanda «chi ha staccato»: `[M]` 23 agosto
#    2026, in quei 400 byte ci stanno le tre righe finali dell'audio e non ci
#    sta la riga che risponde — *«⭐ ancora attaccato dopo 25.0 s»*
#    (`01-b3-cliente.py:1979`).  ⇒ Il primo giro di `stacco` si e' rifiutato di
#    giudicare avendo in mano la risposta, tagliata.
#
# ⇒ Si registra qui l'uscita INTERA di ogni comando che lancia il cliente,
#   **senza toccare il file di b70** (ci sono altri agenti): si sostituisce la
#   sua `root` con una che passa la palla e trascrive.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ E QUEL «PASSA LA PALLA» E' IL POSTO PIU' PERICOLOSO DI QUESTO FILE:
#      **A CHI** la passa decide se le cure del file sotto valgono ancora
# ═══════════════════════════════════════════════════════════════════════════
#
# Fino al 23 agosto 2026 questa funzione chiamava **`RETE.root`**, cioe' saltava
# `09-b70-ritmo.py:root()` e andava dritta al gradino di sotto.  ⛔ E' un difetto
# che **non si vede leggendo nessuno dei due file**: qui la riga e' corretta (una
# `root` che chiama una `root`), e li' la cura e' scritta e collaudata — solo che
# nessuno la esegue piu'.  E' il secondo che questo progetto paga in una sera.
#
# ⛔ `RETE.root` (`07-b64-rete.py:238`) e' un solo `sudo` **davanti al comando
#    nudo**:  `printf parola | sudo -S -p '' <comando>`.  Da li' vengono due
#    difetti, e sono quelli che `09-b70` ha curato il 23 agosto:
#      1. `sudo` copre **solo il primo anello** della catena: in `a && b > c` il
#         `b` e il `>` girano da UTENTE, non da root.  `[M]` il lettore della
#         traccia §11.1 non si scriveva, e §11.1 restava senza arbitro;
#      2. un `< file` in coda **ruba lo stdin a `sudo -S`** (il redirect e' della
#         shell e va all'ULTIMO comando della pipeline, che e' `sudo`): la parola
#         non arriva, `sudo` esce 1, e il numero torna **0 in silenzio**.  `[M]`
#         `righe_registro()` tornava 0, `conti_del_server()` leggeva il registro
#         **dall'accensione del server** invece che dal giro, e `attese_a_vuoto`
#         diventava cumulativo: 4 041 contro 1 604 su un giro fermo, 2,5 volte.
#
# ⭐ `09-b70.root()` cura tutt'e due con una riga sola — `catena_root()`, cioe'
#    **un** `sudo` e la catena intera dentro la SUA `bash -c`.  ⇒ Chi avvolge per
#    trascrivere deve avvolgere **quella**, o si riporta dentro i due difetti
#    passando da una funzione che si chiama come la curata.
#
# ⛔⛔ E NON BASTA SCRIVERE `B70.root`: quando questo file arriva, `B70.root` **e'
#     gia' stato sostituito** da `09-b76-rete-cattiva.py:416`, con un avvolgimento
#     che a sua volta chiama `RETE.root`.  Avvolgere `B70.root` allora vorrebbe
#     dire avvolgere il difetto di un altro e chiamarlo cura.  ⇒ Si ricostruisce
#     la catena curata **dai suoi pezzi** — `B70.catena_root` + `RETE.rem` — che
#     sono quello che `09-b70.root()` fa, e non passano da nessun sostituto.
#
# ⚠ E si aggancia UNA VOLTA SOLA: `appaia()` fa 21 caselle nello stesso processo
#   e `importa()` puo' essere chiamata piu' di una volta.  Un avvolgimento
#   ripetuto non sbaglia i numeri, ma annida 21 chiamate e la prima diagnosi
#   diventa illeggibile.
ULTIMO_CLIENTE = {"testo": ""}
_ROOT_CURATA = None


def _aggancia_root():
    """Installa il trascrittore SOPRA la `root` curata di b70 — una volta sola."""
    global _ROOT_CURATA
    if _ROOT_CURATA is not None:
        return
    if not hasattr(B70, "catena_root"):
        raise SystemExit(
            "⛔ NON MISURO: «09-b70-ritmo.py» non ha `catena_root()`, cioe' e' la "
            "versione con `sudo -S` davanti al comando nudo.  Su quella un "
            "`< file` in coda ruba la parola a sudo e i conti del server "
            "diventano cumulativi dall'accensione (2,5 volte, `[M]` 23 ago 2026). "
            "Si allinea l'albero prima di misurare.")
    _ROOT_CURATA = lambda c, tetto=300: RETE.rem(B70.catena_root(c), tetto)
    B70.root = _root_che_trascrive


def _root_che_trascrive(comando, tetto=300):
    rc, out, err = _ROOT_CURATA(comando, tetto)
    if "01-b3-cliente.py" in comando:
        ULTIMO_CLIENTE["testo"] = out + err
    return rc, out, err


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ I TRE BRACCI — e il braccio si VERIFICA dal registro, non dalla riga
# ═══════════════════════════════════════════════════════════════════════════
#
#   (etichetta, opzioni del server, soglia attesa in ms, regolatore atteso)
BRACCI = [
    ("A", "", 0, False,
     "⛔ i PREDEFINITI, cioe' le due cure SPENTE (invariante I6): e' il termine "
     "di paragone, e si rimisura OGGI"),
    ("B", "--sgombra-soglia-ms 100", 100, False,
     "⭐ la SOGLIA SULLA CODA: un delta fermo si abbandona solo quando la coda "
     "e' senza speranza per piu' di 100 ms, non a ogni fotogramma"),
    ("C", "--sgombra-soglia-ms 100 --ritmo-adattivo", 100, True,
     "⭐⭐ la soglia PIU' il regolatore del ritmo: invece di abbandonare, si "
     "rallenta la cattura.  ⛔ Viene dopo la soglia, o `arretrato` e' zero per "
     "costruzione e il regolatore non scatta mai"),
]

# ⛔ Le due righe che il prodotto scrive all'avvio, SEMPRE, acceso e spento.
#    Sono il contratto su cui si verifica il braccio (`LEZIONI.md` E1).
RE_SOGLIA = re.compile(r"soglia della coda video \(§5\.1\): (\d+) ms")
RE_RITMO_ACCESO = re.compile(r"il regolatore del ritmo e' ACCESO")
RE_RITMO_SPENTO = re.compile(r"il regolatore del ritmo e' SPENTO")


def riavvia(opzioni, soglia_attesa, ritmo_atteso):
    """⛔⭐ Il server si riaccende con le opzioni del braccio, e POI si rilegge
       il registro per sapere che cosa e' DAVVERO in vigore.

    `LEZIONI.md` E1 — «scritto non e' in vigore».  Un binario vecchio
    rifiuterebbe `--sgombra-soglia-ms` e non partirebbe; un binario giusto con
    un refuso nell'opzione partirebbe con la cura SPENTA e darebbe tre bracci
    identici, cioe' «la cura non serve» su una cura mai accesa.
    ⇒ Torna `(ok, righe)`, e `ok` e' falso se le due righe non combaciano.
    """
    amb = " ".join("%s=%s" % (k, os.environ[k]) for k in
                   ("PORTA", "IND", "UTENTE", "UID_B", "ALBERO", "LAV",
                    "DENTRO_ALB", "DENTRO_LAV", "UNITA", "MACCHINA",
                    "PAROLA_SUDO"))
    import subprocess
    p = subprocess.run(
        "%s OPZIONI_SERVER=%s bash %s/09-b79-terreno.sh accendi"
        % (amb, json.dumps(opzioni), os.path.join(QUI)),
        shell=True, capture_output=True, timeout=300)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    if "server " not in testo:
        return False, ["⛔ il server non e' partito: %s" % testo[-300:]]
    # ⛔ Il registro e' stato azzerato dall'accensione: le righe d'avvio sono
    #    le prime, e si aspetta che ci siano invece di leggere quel che capita.
    righe = []
    for _ in range(30):
        rc, out, _e = root("bash -c \"grep -a 'soglia della coda video\\|"
                           "regolatore del ritmo' %s/registro.log | head -4\"" % LAV)
        righe = [x for x in out.splitlines() if x.strip()]
        if len(righe) >= 2:
            break
        time.sleep(0.3)
    testo_righe = "\n".join(righe)
    m = RE_SOGLIA.search(testo_righe)
    letta = int(m.group(1)) if m else None
    acceso = bool(RE_RITMO_ACCESO.search(testo_righe))
    spento = bool(RE_RITMO_SPENTO.search(testo_righe))
    guai = []
    if letta is None:
        guai.append("la riga della soglia non c'e' nel registro")
    elif letta != soglia_attesa:
        guai.append("la soglia in vigore e' %d ms, chiesta %d" % (letta, soglia_attesa))
    if ritmo_atteso and not acceso:
        guai.append("il regolatore del ritmo NON risulta acceso")
    if (not ritmo_atteso) and not spento:
        guai.append("il regolatore del ritmo NON risulta spento")
    return (not guai), (righe + (["⛔ " + g for g in guai] if guai else []))


def md5_binario():
    """⚠ Il binario che misuro dev'essere quello che credo, e si dichiara."""
    rc, out, _ = root("md5sum %s/src/remotix" % ALB)
    return out.strip().split()[0] if out.strip() else "?"


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ LA SESSIONE DI PRIMA DEV'ESSERE FINITA DI CHIUDERSI — e non e' ovvio
# ═══════════════════════════════════════════════════════════════════════════
#
# `[M]` 23 agosto 2026, trovato su `07-b64-rete.py` (`registro_posato()`, riga
# 497) e portato qui **senza toccare quel file**: la chiusura di una sessione e'
# LENTA quando il pacer ha una coda — il profilo al 10 % di perdita ci ha messo
# **29 s in piu'** degli altri a scrivere il suo «conto finale».  ⇒ Due guasti,
# e hanno la stessa radice:
#
#  1. **il conto letto e' di un altro giro.**  `riga0` del giro nuovo si prende
#     PRIMA che la riga del giro vecchio sia scritta; quella riga cade dentro la
#     finestra, e `conti_del_server()` — che prende l'ULTIMA dopo `riga0` — la
#     legge come sua.  `[M]` tre profili di fila hanno riferito «spediti 4999 ·
#     rifiutati 3 · rimandati 7410», che era il conto del PRIMO dei tre;
#  2. **il posto e' ancora occupato.**  Finche' la sessione vecchia non si e'
#     chiusa, §4.4-bis rifiuta la nuova con `CONGEDO 0x0F GIA_ATTIVA_REMOTA`, e
#     la serratura dura fino a `SILENZIO` = 30 s (`09-b78-apertura.py` §4).
#     ⇒ Un giro puo' fallire per colpa del giro PRIMA, e tre bracci misurati di
#       fila smettono di essere confrontabili.
#
# ⭐⭐ E QUI DENTRO IL PRIMO E' STRUTTURALMENTE IMPOSSIBILE — si scrive perche'
#     e' un fatto verificato, non una speranza: `07-b64-terreno.sh:106` fa
#     `: > "$LAV/registro.log"` a OGNI `accendi`, e questo banco riaccende il
#     server a **ogni braccio** (`riavvia()`).  ⇒ Nella finestra di un braccio non
#     c'e' nessun conto del braccio prima da rubare, e il posto e' libero perche'
#     il processo che lo teneva e' morto.  `[M]` la controprova sui 36 giri del
#     23 agosto: nessuna coppia di caselle porta numeri identici dal registro, e
#     tre caselle (`perdita-3` A, `raffica-forte` A e B) hanno detto «NIENTE DA
#     LEGGERE» invece di riferire il numero del vicino.
#
# ⛔ Quel che RESTA scoperto, ed e' per questo che le due funzioni ci sono: dentro
#    UN braccio prima del giro c'e' la **sessione d'innesco**, e il suo «conto
#    finale» sta nello stesso registro.  Se arrivasse tardi cadrebbe nella
#    finestra del giro.  ⇒ Si aspetta che il conto stia FERMO, e poi il giro
#    PRETENDE una riga sua.
def conta_conti_finali():
    rc, out, _ = root("bash -c \"grep -ac 'conto finale' %s/registro.log "
                      "2>/dev/null || true\"" % LAV)
    t = out.strip()
    return int(t) if t.isdigit() else None


def registro_posato(tetto=60.0, quiete=3.0):
    """Aspetta che il conto delle righe «conto finale» stia fermo `quiete` s.

    Torna quel conto — e' l'`n0` da cui il giro nuovo pretende una riga SUA — o
    `None` se il registro non si e' letto (⛔ e `None` non e' zero).
    """
    n = conta_conti_finali()
    if n is None:
        return None
    fermo, scade = 0.0, time.time() + tetto
    while time.time() < scade and fermo < quiete:
        time.sleep(1.0)
        m = conta_conti_finali()
        if m is None:
            return None
        fermo = (fermo + 1.0) if m == n else 0.0
        n = m
    if fermo < quiete:
        _dub("⚠ in %.0f s il registro non si e' posato: qualcuno sta ancora "
             "chiudendo una sessione" % tetto)
    return n


def conto_e_mio(n0, n):
    """⛔ Il «conto finale» dentro `n["server"]` e' di QUESTO giro, o no?

    ⇒ Se il conto delle righe non e' cresciuto, la riga letta e' di prima (al
      peggio dell'innesco) e i quattro numeri del lato server **non vanno
      giudicati**.  Non si cancellano: si marcano, che e' la differenza fra
      «non ho letto» e «non e' successo niente» (`LEZIONI.md` §1.9).
    """
    s = (n or {}).get("server") or {}
    if n0 is None:
        s["conto_dubbio"] = ("⛔ non so quanti «conto finale» c'erano prima del "
                             "giro: non giudico i numeri del lato server")
        return False
    n1 = conta_conti_finali()
    if n1 is None or n1 <= n0:
        s["conto_dubbio"] = ("⛔ questo giro non ha scritto un «conto finale» SUO "
                             "(erano %s, sono %s): la riga letta e' di prima — "
                             "NON giudico i numeri del lato server" % (n0, n1))
        return False
    s["conti_finali"] = [n0, n1]
    return True


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LE RIGHE `rete-quic` — che nell'albero di lavoro ci sono e in HEAD no
# ═══════════════════════════════════════════════════════════════════════════
def leggi_rete_quic(riga0):
    """⭐ `src/webtransport.c:3772` fissa il formato come un CONTRATTO SUL TESTO:
       prefisso `rete-quic`, campi `nome=valore` senza spazi, e `giudizio=`
       ultimo, col valore che arriva a fine riga.  ⇒ `split()` e `split('=',1)`.

    ⛔ Non giudica niente: riduce e stampa.  ⚠ `dgram_falsi` = datagram
       dichiarati persi e poi riscontrati = **riordino misurato dal lato del
       server**, e vale sull'audio soltanto (gli stream non hanno un
       identificativo per pezzo: il prezzo si dichiara).
    """
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                      "'rete-quic ' | tail -400\"" % (riga0 + 1, LAV))
    righe = [r for r in out.splitlines() if "rete-quic " in r]
    if not righe:
        return {"esito": "NIENTE DA LEGGERE — nessuna riga «rete-quic» in questo giro"}
    campi = []
    for r in righe:
        d = {}
        corpo = r.split("rete-quic ", 1)[1]
        giud = None
        if "giudizio=" in corpo:
            corpo, giud = corpo.split("giudizio=", 1)
        for pezzo in corpo.split():
            if "=" in pezzo:
                k, v = pezzo.split("=", 1)
                d[k] = v
        d["giudizio"] = (giud or "").strip()
        campi.append(d)

    def num(d, k):
        v = d.get(k)
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def elenco(k):
        return [x for x in (num(d, k) for d in campi) if x is not None]

    ultima = campi[-1]
    giudizi = {}
    for d in campi:
        giudizi[d["giudizio"]] = giudizi.get(d["giudizio"], 0) + 1
    cwnd = elenco("cwnd")
    srtt = elenco("srtt_us")
    rttv = elenco("rttvar_us")
    n = {"esito": "letto", "righe": len(campi),
         "persi_tot": num(ultima, "persi"),
         "spediti_tot": num(ultima, "spediti"),
         "cwnd_min": min(cwnd) if cwnd else None,
         "cwnd_mediana": sorted(cwnd)[len(cwnd) // 2] if cwnd else None,
         "cwnd_fine": num(ultima, "cwnd"),
         "srtt_us_mediana": sorted(srtt)[len(srtt) // 2] if srtt else None,
         "srtt_us_max": max(srtt) if srtt else None,
         "rttvar_us_mediana": sorted(rttv)[len(rttv) // 2] if rttv else None,
         "pto_us_fine": num(ultima, "pto_us"),
         "dgram_persi": num(ultima, "dgram_persi"),
         "dgram_falsi": num(ultima, "dgram_falsi"),
         "dgram_ok": num(ultima, "dgram_ok"),
         "giudizi": giudizi}
    return n


def stampa_rete_quic(n):
    if n.get("esito") != "letto":
        _dub("QUIC    %s" % n.get("esito"))
        return
    _inf("QUIC    %d righe · persi %s pacchetti su %s spediti · cwnd min %s / "
         "mediana %s / fine %s"
         % (n["righe"], n["persi_tot"], n["spediti_tot"], n["cwnd_min"],
            n["cwnd_mediana"], n["cwnd_fine"]))
    _inf("        srtt mediano %s us (max %s) · rttvar mediano %s us · pto "
         "finale %s us"
         % (n["srtt_us_mediana"], n["srtt_us_max"], n["rttvar_us_mediana"],
            n["pto_us_fine"]))
    _inf("        datagram (audio): persi %s · riscontrati %s · ⭐ FALSI "
         "%s (= riordino misurato dal server)"
         % (n["dgram_persi"], n["dgram_ok"], n["dgram_falsi"]))
    _inf("        giudizi del server: %s"
         % json.dumps(n["giudizi"], ensure_ascii=False))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI DELLA COPPIA — scritti PRIMA
# ═══════════════════════════════════════════════════════════════════════════
#
# ── le soglie, in un posto solo, e ciascuna con la sua ragione ─────────────
QUOTA_CHIAVI_MAX = 0.10   # ⛔ il complemento di `QUOTA_DELTA = 0,90` di 09-b70,
                          #    cioe' §3.3 letto al contrario.  Non e' una soglia
                          #    nuova: e' la stessa, e due soglie per lo stesso
                          #    fatto sono due soglie che divergono.
RUMORE = 0.05             # ⚠ 09-b70 stima al 5 % la differenza fra due giri
                          #    della stessa macchina
DIFFERENZA_MINIMA = 0.10  # ⛔ il DOPPIO del rumore: sotto, questo banco non
                          #    giudica invece di chiamare «effetto» il rumore
DERIVA_TOLLERATA_MS = 100.0  # ⭐ = la soglia stessa: la cura tiene un delta
                             #   finche' la coda non e' senza speranza per piu'
                             #   di N ms, quindi il ritardo che puo' aggiungere
                             #   e' N per costruzione


def _quota_chiavi(n):
    if not B70._ha_misurato(n):
        return None
    return round(1.0 - n["quota_delta"], 4)


def p_spirale_spenta(a, x, etichetta):
    """**K′ — LA CURA SPEGNE LA SPIRALE.**

    ⛔ E TACE dove in A la spirale non c'era: spegnere un incendio che non c'e'
       non e' un merito, ed e' un verde che si prenderebbe da solo.
    """
    if not B70._ha_misurato(a):
        return _muto("il braccio A non ha misurato: senza di lui non c'e' "
                     "coppia, e un numero senza denominatore non giudica")
    if not B70._ha_misurato(x):
        return _muto("il braccio %s non ha misurato: %s"
                     % (etichetta, x.get("esito", "?")))
    qa, qx = _quota_chiavi(a), _quota_chiavi(x)
    coda = ("chiavi %d su %d = %.1f %% nel braccio %s, contro %d su %d = "
            "%.1f %% in A" % (x["chiavi"], x["fotogrammi"], qx * 100, etichetta,
                              a["chiavi"], a["fotogrammi"], qa * 100))
    if qa <= QUOTA_CHIAVI_MAX:
        return _muto("in A la spirale NON c'era (%.1f %% di chiavi, sotto il "
                     "%.0f %%): non c'e' niente da spegnere, e un verde qui me "
                     "lo prenderei da solo — %s"
                     % (qa * 100, QUOTA_CHIAVI_MAX * 100, coda))
    if qx <= QUOTA_CHIAVI_MAX:
        return _si("⭐ LA SPIRALE SI E' SPENTA: %s" % coda)
    return _no("⛔ la spirale NON si e' spenta: %s" % coda)


def p_ritmo_restituito(a, x, etichetta):
    """**F′ — LA CURA RESTITUISCE RITMO**, e la soglia e' il doppio del rumore.

    ⚠ Tre esiti, non due: sotto il 10 % di differenza questo banco dice
      «indistinguibile» invece di chiamare effetto il rumore.
    """
    if not B70._ha_misurato(a) or not B70._ha_misurato(x):
        return _muto("uno dei due bracci non ha misurato: A «%s», %s «%s»"
                     % (a.get("esito", "?"), etichetta, x.get("esito", "?")))
    if not a["fps"]:
        return _muto("il braccio A ha zero fotogrammi/s: non c'e' rapporto")
    r = x["fps"] / a["fps"]
    coda = ("%.2f/s nel braccio %s contro %.2f/s in A (%.0f %%) · peggior "
            "secondo %s contro %s · ⚠ E IL PREZZO: deriva finale %s ms contro "
            "%s ms (massima %s contro %s)"
            % (x["fps"], etichetta, a["fps"], r * 100, x["fps_finestra_min"],
               a["fps_finestra_min"], x["deriva_fine_ms"], a["deriva_fine_ms"],
               x["deriva_max_ms"], a["deriva_max_ms"]))
    if r >= 1.0 + DIFFERENZA_MINIMA:
        return _si("⭐ il ritmo e' tornato: %s" % coda)
    if r <= 1.0 - DIFFERENZA_MINIMA:
        return _no("⛔ LA CURA TOGLIE RITMO invece di darne: %s" % coda)
    return _muto("indistinguibile dal rumore (meno del %.0f %%, che e' il "
                 "doppio del %.0f %% fra due giri della stessa macchina): %s"
                 % (DIFFERENZA_MINIMA * 100, RUMORE * 100, coda))


def p_linea_sana(bracci):
    """**S′ — LA CURA NON COSTA SULLA LINEA SANA**, e vale piu' di tutti gli
       altri messi insieme.

    ⛔ Su `ritardo-30` non c'e' niente da curare: zero perdita, zero riordino,
       solo trenta millisecondi di ritardo.  ⇒ I tre bracci devono essere
       indistinguibili, e se non lo sono e' la scoperta piu' importante del
       giro — perche' vorrebbe dire che la cura si paga anche dove non serve.

    `bracci` = {"A": n, "B": n, "C": n}
    """
    a = bracci.get("A") or {}
    if not B70._ha_misurato(a):
        return _muto("il braccio A della linea sana non ha misurato: %s"
                     % a.get("esito", "?"))
    guai, detto = [], []
    for et in ("B", "C"):
        x = bracci.get(et) or {}
        if not B70._ha_misurato(x):
            return _muto("il braccio %s della linea sana non ha misurato: %s"
                         % (et, x.get("esito", "?")))
        r = x["fps"] / a["fps"] if a["fps"] else 0.0
        dq = _quota_chiavi(x)
        dd = x["deriva_fine_ms"] - a["deriva_fine_ms"]
        detto.append("%s %.2f/s (%.0f %%), chiavi %.1f %%, deriva %s ms "
                     "(%+.0f contro A)"
                     % (et, x["fps"], r * 100, dq * 100, x["deriva_fine_ms"], dd))
        if abs(r - 1.0) > RUMORE:
            guai.append("%s: %.2f/s contro %.2f/s = %.0f %%, oltre il %.0f %% "
                        "di rumore" % (et, x["fps"], a["fps"], r * 100,
                                       RUMORE * 100))
        if dq > QUOTA_CHIAVI_MAX:
            guai.append("%s: %.1f %% di chiavi su una linea che non perde "
                        "niente" % (et, dq * 100))
        if dd > DERIVA_TOLLERATA_MS:
            guai.append("%s: la deriva finale cresce di %.0f ms, piu' della "
                        "soglia stessa (%.0f ms) — non e' la soglia che "
                        "lavora" % (et, dd, DERIVA_TOLLERATA_MS))
    coda = "A %.2f/s, chiavi %.1f %%, deriva %s ms · %s" % (
        a["fps"], _quota_chiavi(a) * 100, a["deriva_fine_ms"], " · ".join(detto))
    if guai:
        return _no("⛔⛔ LA CURA COSTA SULLA LINEA SANA — %s · %s"
                   % (" · ".join(guai), coda))
    return _si("i tre bracci sono indistinguibili sulla linea sana: %s" % coda)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — «come fa questo banco a sapere di saper vedere?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«un banco che non sa vedere il difetto che cerca non ha
#    diritto al verde»*.  Qui si fabbricano coppie e si controlla che i tre
#    predicati diano quel che e' scritto PRIMA — verde, rosso **e muto**.
def _g(fps, chiave_ogni=0, deriva=0.0, secondi=25):
    """Un giro finto, ridotto dalla STESSA `misura()` che gira sui giri veri."""
    return B76._fab_giro(fps, secondi=secondi, chiave_ogni=chiave_ogni,
                         deriva=deriva)


def certifica():
    print("⭐ CERTIFICAZIONE DEL BANCO DELLE DUE CURE — l'atteso e' scritto "
          "PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova: qui si prova lo "
          "STRUMENTO,\n      non il prodotto.\n")
    importa(con_rete=False)
    verde = True

    def esito(nome, visto, atteso, perche):
        nonlocal verde
        bene = (visto is atteso)
        verde = verde and bene
        print("  %s%-64s atteso %-5s visto %-5s\n        %s"
              % ("OK  " if bene else "⛔  ", nome, atteso, visto, perche[:170]))

    # ── 1 · K′ · la spirale si spegne? ─────────────────────────────────────
    print("  ── K′ · la cura spegne la spirale ──\n")
    # ⭐ `chiave_ogni=1` = tutti i fotogrammi sono chiavi: e' la faccia del
    #    difetto del 21 agosto (144 chiavi su 144).
    spirale = _g(10, chiave_ogni=1)
    sana = _g(40)
    p, q = p_spirale_spenta(spirale, sana, "B")
    esito("1-⭐ A e' tutto chiavi, B non ne ha nessuna: la spirale si e' spenta",
          p, True, q)

    p, q = p_spirale_spenta(spirale, _g(12, chiave_ogni=1), "B")
    esito("2-⛔⛔ A e' tutto chiavi e B ANCHE: la cura non ha spento niente",
          p, False, q)

    p, q = p_spirale_spenta(sana, _g(41), "B")
    esito("3-⭐⭐ in A la spirale NON c'era: il banco TACE invece di prendersi "
          "un verde che si darebbe da solo", p, None, q)

    p, q = p_spirale_spenta(B70.misura([], 25, None, None), sana, "B")
    esito("4-⛔ il braccio A non ha misurato: senza denominatore, TACE",
          p, None, q)

    # ── 2 · F′ · il ritmo torna? e sotto il rumore si TACE ─────────────────
    print("\n  ── F′ · la cura restituisce ritmo (e il rumore non e' un "
          "effetto) ──\n")
    p, q = p_ritmo_restituito(_g(10), _g(40), "B")
    esito("5-⭐ da 10/s a 40/s: il ritmo e' tornato", p, True, q)

    p, q = p_ritmo_restituito(_g(40), _g(41), "B")
    esito("6-⭐⭐ 40 contro 41: e' il 2,5 %, meno del doppio del rumore — il "
          "banco NON chiama effetto il rumore e TACE", p, None, q)

    p, q = p_ritmo_restituito(_g(40), _g(20), "C")
    esito("7-⛔⛔ LA CURA TOGLIE RITMO: 40/s in A e 20/s in C — ed e' la "
          "scoperta piu' importante che possa uscire di qui", p, False, q)

    # ⚠⚠ IL CONFINE, e va provato da TUTT'E DUE le parti — un predicato a tre
    #    esiti si sbaglia proprio li' in mezzo.  ⛔ E il primo atteso che avevo
    #    scritto era SBAGLIATO: avevo dato per «sopra il confine» un 44 contro
    #    40, che il fabbricatore rende 44,04 contro 40,04 = **109,99 %**, cioe'
    #    un capello SOTTO.  ⇒ Il caso non si e' aggiustato spostando la soglia:
    #    si e' aggiustato l'ATTESO, che era mio e non del predicato.
    p, q = p_ritmo_restituito(_g(40), _g(44), "B")
    esito("8-⚠ un capello SOTTO il confine (109,99 %): il banco tace",
          p, None, q)

    p, q = p_ritmo_restituito(_g(40), _g(45), "B")
    esito("9-⚠ un passo SOPRA il confine (112,5 %): il banco giudica",
          p, True, q)

    # ── 3 · S′ · ⛔ la linea sana, che vale piu' di tutti gli altri ────────
    print("\n  ── ⛔⛔ S′ · la cura non deve costare sulla linea sana ──\n")
    p, q = p_linea_sana({"A": _g(40), "B": _g(40.5), "C": _g(39.6)})
    esito("10-⭐ i tre bracci entro il 5 %: indistinguibili", p, True, q)

    p, q = p_linea_sana({"A": _g(40), "B": _g(40.2), "C": _g(34)})
    esito("11-⛔⛔ IL DIFETTO CHE QUESTO PREDICATO ESISTE PER TROVARE: C perde "
          "il 15 % sulla linea SANA", p, False, q)

    p, q = p_linea_sana({"A": _g(40), "B": _g(40, chiave_ogni=1), "C": _g(40)})
    esito("12-⛔⛔ B e' tutto chiavi su una linea che non perde niente: la cura "
          "ha ACCESO una spirale dove non ce n'era", p, False, q)

    # ⭐ Il prezzo, ed e' il caso che il mandato chiede di non confondere con un
    #   miglioramento: stesso ritmo, ma il ritardo cresce piu' della soglia.
    p, q = p_linea_sana({"A": _g(40), "B": _g(40, deriva=0.0),
                         "C": _g(40, deriva=0.5)})
    esito("13-⛔⭐ IL PREZZO: C tiene il ritmo ma la deriva cresce piu' della "
          "soglia stessa (100 ms) — non e' la soglia che lavora", p, False, q)

    p, q = p_linea_sana({"A": _g(40), "B": _g(40),
                         "C": B70.misura([], 25, None, None)})
    esito("14-⛔ un braccio della linea sana non ha misurato: TACE", p, None, q)

    # ── 4 · ⛔ il braccio si verifica dal REGISTRO, non dalla riga di comando ─
    print("\n  ── ⛔ «scritto non e' in vigore»: le due righe d'avvio ──\n")
    # ⚠ Qui non si tocca la macchina: si esercita il RICONOSCITORE sulle righe
    #   vere che il prodotto scrive (`sgombra_dichiara`, `wt_ritmo_adattivo`).
    vere_A = ("⭐ FASE 9, soglia della coda video (§5.1): 0 ms (SPENTA: si "
              "abbandona a ogni fotogramma piu' recente, com'e' oggi — "
              "invariante I6) — sopra la soglia un delta fermo si abbandona\n"
              "il regolatore del ritmo e' SPENTO (invariante I6, "
              "`--ritmo-adattivo`): nessun fotogramma verra' mai saltato")
    vere_C = ("⭐ FASE 9, soglia della coda video (§5.1): 100 ms — sopra la "
              "soglia un delta fermo si abbandona, sotto si TIENE\n"
              "⭐ FASE 9: il regolatore del ritmo e' ACCESO (`--ritmo-adattivo`)")

    def riconosci(testo, soglia, ritmo):
        m = RE_SOGLIA.search(testo)
        letta = int(m.group(1)) if m else None
        acceso = bool(RE_RITMO_ACCESO.search(testo))
        spento = bool(RE_RITMO_SPENTO.search(testo))
        if letta != soglia:
            return False, "la soglia in vigore e' %s, chiesta %s" % (letta, soglia)
        if ritmo and not acceso:
            return False, "il regolatore non risulta acceso"
        if (not ritmo) and not spento:
            return False, "il regolatore non risulta spento"
        return True, "soglia %s ms, regolatore %s" % (letta,
                                                      "acceso" if ritmo else "spento")

    p, q = riconosci(vere_A, 0, False)
    esito("15-⭐ il braccio A riconosciuto dalle righe vere del prodotto", p, True, q)
    p, q = riconosci(vere_C, 100, True)
    esito("16-⭐ il braccio C riconosciuto dalle righe vere del prodotto", p, True, q)
    p, q = riconosci(vere_A, 100, False)
    esito("17-⛔⛔ CHIESTA la soglia 100 e in vigore c'e' 0: il banco si FERMA "
          "invece di misurare tre bracci identici e concludere «la cura non "
          "serve»", p, False, q)
    p, q = riconosci(vere_C, 100, False)
    esito("18-⛔ chiesto il regolatore SPENTO e risulta acceso", p, False, q)

    # ── 5 · la riduzione delle righe `rete-quic`, che e' un contratto sul testo ─
    print("\n  ── ⭐ le righe `rete-quic`: il contratto sul testo ──\n")
    finte = [
        "12:00:01.000 wt      rete-quic 192.168.0.2:52344 da_ms=0 persi=0 "
        "persi_d=0 cwnd=14000 cwnd_left=14000 srtt_us=30100 rttvar_us=900 "
        "pto_us=132000 spediti=100 dgram_persi=0 dgram_ok=10 dgram_falsi=0 "
        "giudizio=-- niente da segnalare",
        "12:00:02.000 wt      rete-quic 192.168.0.2:52344 da_ms=1000 persi=7 "
        "persi_d=7 cwnd=6000 cwnd_left=0 srtt_us=41230 rttvar_us=11400 "
        "pto_us=132000 spediti=210 dgram_persi=5 dgram_ok=40 dgram_falsi=3 "
        "giudizio=⛔ la linea perde",
    ]
    salvato = globals().get("root")
    globals()["root"] = lambda c, tetto=300: (0, "\n".join(finte), "")
    n = leggi_rete_quic(0)
    globals()["root"] = salvato
    esito("19-⭐ due righe ridotte: persi 7, cwnd min 6000, ⭐ dgram_falsi 3 "
          "(= riordino visto dal server)",
          (n["righe"] == 2 and n["persi_tot"] == 7 and n["cwnd_min"] == 6000
           and n["dgram_falsi"] == 3 and n["srtt_us_max"] == 41230),
          True, json.dumps({k: n[k] for k in ("righe", "persi_tot", "cwnd_min",
                                              "dgram_falsi", "srtt_us_max")}))
    esito("20-⭐ e il `giudizio=` arriva a fine riga, spazi compresi",
          (n["giudizi"].get("⛔ la linea perde") == 1
           and n["giudizi"].get("-- niente da segnalare") == 1),
          True, json.dumps(n["giudizi"], ensure_ascii=False))

    salvato = globals().get("root")
    globals()["root"] = lambda c, tetto=300: (0, "", "")
    n = leggi_rete_quic(0)
    globals()["root"] = salvato
    esito("21-⛔ nessuna riga `rete-quic`: «non ho letto» non e' «zero» "
          "(`CODER.md` §3.10)", n.get("esito") != "letto", True, n.get("esito"))

    print("\n== %s" % ("⭐ IL BANCO SA VEDERE I DIFETTI CHE CERCA — e sa TACERE "
                       "dove non puo' giudicare"
                       if verde else
                       "⛔⛔ IL BANCO NON SA VEDERE QUEL CHE CERCA: non si creda "
                       "a nessun suo verde"))
    return 0 if verde else 1


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def vicini_non_miei():
    """⚠ `LEZIONI.md` §1.26: due banchi sulla stessa macchina non danno un
       rosso, danno **un numero plausibile**.  ⛔ La 7930 di `09-b76` e' rimasta
       accesa: non e' mia e non si spegne, ma se qualcuno ci si attaccasse i
       miei numeri sarebbero sporchi.  ⇒ Si conta chi e' ATTACCATO, non chi
       ascolta: un server acceso e fermo non e' un banco che gira."""
    fuori = {}
    for p in ("7900", "7910", "7920", "7930", "7932", "7730"):
        rc, out, _ = root("bash -c \"ss -uan 2>/dev/null | grep ':%s ' | "
                          "grep -vc UNCONN || true\"" % p)
        fuori[p] = out.strip()
    rc, out, _ = root("uptime")
    fuori["carico"] = out.strip()[-32:]
    return fuori


def profilo(nome):
    for p in B76.PROFILI:
        if p[0] == nome:
            return p
    return None


def installa_profilo(regole):
    """⛔ `del root` + `add`, mai `change`: `[M]` 23 ago 2026, `tc qdisc change`
       e' APPICCICOSO e si e' portato dietro un `reorder` per quattro profili
       — che avrebbero misurato una rete che nessuno aveva chiesto."""
    ok, q = RETE.stringi(B76._regole(regole))
    if not ok:
        return False, q, ""
    B76.filtri_sonda()
    riletta = B76.regola_riletta()
    passa, perche = B76.controlla_regola(regole, riletta)
    return passa, perche, riletta


def una_casella(nome_profilo, regole, verifica, etichetta, opzioni, soglia,
                ritmo, secondi):
    """Un braccio di un profilo: la sequenza dei sette passi dell'intestazione."""
    voce = {"profilo": nome_profilo, "braccio": etichetta, "opzioni": opzioni}

    # 1 · la rete si rimette liscia, cosi' la sessione d'innesco nasce pulita
    RETE.rimetti(dillo=False)
    # 2 · il server si riavvia col braccio, e il braccio si VERIFICA
    ok, righe = riavvia(opzioni, soglia, ritmo)
    voce["avvio"] = righe
    for r in righe:
        _inf("AVVIO   %s" % r.split("avvio   ")[-1][:150])
    if not ok:
        _ko("⛔ il braccio %s NON e' in vigore: non misuro questa casella"
            % etichetta)
        voce["esito"] = "IL BRACCIO NON E' IN VIGORE"
        return voce
    # 3 · la sessione d'innesco, A RETE PULITA (vedi l'intestazione, punto 3)
    if not B70.innesca_sessione():
        _ko("la sessione d'innesco non si apre: non misuro questa casella")
        voce["esito"] = "LA SESSIONE D'INNESCO NON SI APRE"
        return voce
    # 4 · il profilo, e si rilegge
    passa_r, perche_r, riletta = installa_profilo(regole)
    voce["regola_riletta"] = riletta
    (_ok if passa_r else _ko)("la regola: %s" % perche_r)
    if not passa_r:
        voce["esito"] = "LA REGOLA INSTALLATA NON E' QUELLA CHIESTA"
        return voce
    # 5 · la sonda: il guasto e' stato messo?  ⛔ e si rifa a ogni braccio
    s = B76.sonda_gira()
    B76.stampa_sonda(s)
    passa_g, perche_g = B76.p_guasto_messo(nome_profilo, verifica, s)
    (_ok if passa_g else (_dub if passa_g is None else _ko))(
        "IL GUASTO E' STATO MESSO: %s" % perche_g)
    voce["sonda"] = s
    voce["guasto"] = {"passa": passa_g, "perche": perche_g}
    # 6 · il giro
    usc = B76.scena_accendi("barra")
    if not usc:
        _ko("la scena non parte: NON giudico questa casella")
        voce["esito"] = "LA SCENA NON E' PARTITA"
        return voce
    prima = B76.conti_qdisc()
    # ⛔ La sessione d'innesco dev'essere FINITA di chiudersi, o il suo «conto
    #    finale» cade nella finestra di questo giro (⇒ `registro_posato`).
    n0 = registro_posato()
    riga0 = B76.righe_registro()
    n = B70.giro("%s-%s" % (nome_profilo, etichetta), "barra",
                 B70.TELA_PIENA, secondi)
    if not conto_e_mio(n0, n):
        _dub("⚠ %s" % (n.get("server") or {}).get("conto_dubbio"))
    B76.scena_spegni()
    dopo = B76.conti_qdisc()
    # 7 · i contatori attorno al giro e le righe `rete-quic`
    delta = {k: dopo[k] - prima[k] for k in prima} if (prima and dopo) else None
    voce["qdisc"] = delta
    quic = leggi_rete_quic(riga0)
    voce["quic"] = quic
    B70.stampa_giro(n)
    # ⛔⭐ LA RETE DI SICUREZZA DI `09-b70` SI USA, NON SI AGGIRA: e' il predicato
    #    che si rifiuta di dire qualcosa sul lato server quando il registro non
    #    e' di questo giro — cioe' l'unica cosa che avrebbe preso da sola il
    #    difetto della `root` avvolta male.
    # ⚠ E si dichiara che cosa protegge: K′ e F′ NON passano di qui (vivono sulla
    #   traccia §11.1 del cliente), quindi un rosso suo non tocca il verdetto —
    #   marca come non giudicabili i quattro numeri di CORROBORAZIONE
    #   (`delta_non_spedito`, `chiave_aspetta`, `non_spediti`, `abbandonati`).
    if hasattr(B70, "p_registro_letto"):
        pr, perche_pr = B70.p_registro_letto(n)
        (_ok if pr else (_dub if pr is None else _ko))(
            "il registro e' di QUESTO giro (§1.9): %s" % perche_pr)
        voce["registro_letto"] = {"passa": pr, "perche": perche_pr}
    _inf("QDISC   attorno al giro: %s" % json.dumps(delta))
    stampa_rete_quic(quic)
    # ⛔ La serratura di §8.2: se il posto era occupato, questa casella non e'
    #    una misura della cura — e' una misura di trenta secondi di serratura.
    coda = ULTIMO_CLIENTE["testo"] or (n.get("coda_cliente") or "")
    if "GIA_ATTIVA" in coda or "0x0f" in coda.lower():
        _dub("⚠ il cliente ha trovato il posto OCCUPATO (§8.2 motivo 0x0F): "
             "questa casella non misura la cura")
        voce["esito"] = "IL POSTO ERA OCCUPATO"
    voce["giro"] = n
    voce["staccato_dal_cliente"] = ("NON sono rimasto attaccato" in coda)
    return voce


def appaia(a):
    _log("09-b79 · LE DUE CURE APPAIATE — porta %d · dev «%s»" % (PORTA, DEV))
    print("   ⛔ «%s» (ssh + la sessione dell'utente) NON si tocca" % VIETATA)
    print("   ⛔ le 7900/7910/7920/7930/7932 sono di altri: si CONTANO, non si toccano")
    md5 = md5_binario()
    print("   ⭐ il binario che misuro: md5 %s (albero di lavoro, non HEAD)" % md5)
    print("   --  «%s» prima: %s" % (DEV, RETE.qdisc() or "(nessuna)"))

    if not B76.spedisci_sonda():
        _ko("i copioni non si sono scritti in %s" % LAV)
        return 2
    if B76.scegli_porta_sonda() is None:
        _ko("⛔ nessuna delle mie porte per la sonda e' libera: NON misuro, "
            "perche' senza sonda non so se il guasto sia stato messo")
        return 2
    _ok("la sonda e il lettore sono in %s · la sonda usera' la porta %d"
        % (LAV, B76.PORTA_SONDA))
    prima_vicini = vicini_non_miei()
    _inf("attaccati alle porte NON mie, PRIMA: %s"
         % json.dumps(prima_vicini, ensure_ascii=False))

    nomi = [x.strip() for x in a.profili.split(",") if x.strip()]
    if a.solo:
        nomi = [n for n in nomi if a.solo in n]
    scelti = []
    for nome in nomi:
        p = profilo(nome)
        if not p:
            _ko("il profilo «%s» non esiste in 09-b76" % nome)
            return 2
        scelti.append(p)
    if not scelti:
        _ko("nessun profilo scelto")
        return 2
    bracci = [b for b in BRACCI if b[0] in a.bracci]
    _inf("%d profili × %d bracci = %d caselle da %d s"
         % (len(scelti), len(bracci), len(scelti) * len(bracci), a.secondi))

    CHI = "09-b79"
    AFFITTO = 900
    try:
        LUC.prendi(CHI, secondi=AFFITTO, attesa=a.attesa)
    except Exception as e:
        _ko("⛔ NON MISURO: %s" % e)
        return 2
    scadenza = time.time() + AFFITTO

    esiti = []
    RETE.guardiano_arma(min(7200, len(scelti) * len(bracci) * (a.secondi + 90) + 900))
    try:
        for p in scelti:
            nome, regole, _pieno, _spir, _senza, perche, verifica = p
            if time.time() > scadenza - 400:
                if B76.rinnova(CHI, AFFITTO):
                    scadenza = time.time() + AFFITTO
                    _inf("⛔ affitto del lucchetto rinnovato per %d s" % AFFITTO)
                else:
                    _ko("⛔ il lucchetto non e' piu' mio: MI FERMO")
                    break
            _log("PROFILO «%s» — %s" % (nome, perche[:110]))
            casella = {}
            for etichetta, opzioni, soglia, ritmo, perche_b in bracci:
                _log("  %s · braccio %s — %s" % (nome, etichetta, perche_b[:100]))
                v = una_casella(nome, regole, verifica, etichetta, opzioni,
                                soglia, ritmo, a.secondi)
                esiti.append(v)
                casella[etichetta] = v.get("giro") or {"esito": v.get("esito", "?")}

            # ── i predicati della COPPIA, e ciascuno dice il suo perche' ────
            _log("  %s · LA COPPIA" % nome)
            A = casella.get("A") or {}
            for et in ("B", "C"):
                if et not in casella:
                    continue
                passa, q = p_spirale_spenta(A, casella[et], et)
                (_ok if passa else (_dub if passa is None else _ko))(
                    "K′ · la cura spegne la spirale (%s): %s" % (et, q))
                passa2, q2 = p_ritmo_restituito(A, casella[et], et)
                (_ok if passa2 else (_dub if passa2 is None else _ko))(
                    "F′ · la cura restituisce ritmo (%s): %s" % (et, q2))
                esiti.append({"profilo": nome, "coppia": et,
                              "K": {"passa": passa, "perche": q},
                              "F": {"passa": passa2, "perche": q2}})
            if nome == "ritardo-30" and len(casella) == 3:
                passa, q = p_linea_sana(casella)
                (_ok if passa else (_dub if passa is None else _ko))(
                    "⛔⛔ S′ · la cura NON deve costare sulla linea sana: %s" % q)
                esiti.append({"profilo": nome, "linea_sana":
                              {"passa": passa, "perche": q}})
    finally:
        B76.scena_spegni()
        _log("⛔ LA RETE SI RIMETTE COM'ERA")
        rimessa = RETE.rimetti()
        LUC.molla(CHI)

    os.makedirs(FUORI, exist_ok=True)
    dove = os.path.join(FUORI, "09-b79-esiti.json")
    with open(dove, "w") as f:
        json.dump({"md5_binario": md5, "esiti": esiti,
                   "vicini_prima": prima_vicini,
                   "vicini_dopo": vicini_non_miei()}, f,
                  ensure_ascii=False, indent=1)
    _inf("esiti in %s" % dove)
    dopo_vicini = vicini_non_miei()
    _inf("attaccati alle porte NON mie, DOPO: %s"
         % json.dumps(dopo_vicini, ensure_ascii=False))
    tabella(esiti)
    rossi = [e for e in esiti
             if any((e.get(k) or {}).get("passa") is False
                    for k in ("K", "F", "linea_sana"))]
    if not rimessa:
        _ko("⛔ la rete NON e' tornata com'era: si rimette a mano con «rimetti»")
        return 2
    return 1 if rossi else 0


def tabella(esiti):
    """⛔ §6.2: si stampano TUTTE le grandezze.  ⭐ E la DERIVA sta accanto ai
       fotogrammi/s a ogni riga, perche' una cura che raddoppia il ritmo e
       triplica il ritardo non e' ovviamente un miglioramento — ed e' una
       scelta che spetta all'utente, non a questo banco."""
    _log("LA TABELLA A TRE BRACCI — ⚠ e il prezzo (la deriva) sta accanto al "
         "guadagno")
    print("  %-14s %-2s %7s %7s %7s %7s %8s %8s %9s"
          % ("profilo", "br", "fps", "peggio", "chiavi%", "deriva", "derivaMx",
             "Mbit/s", "cwnd_min"))
    for e in esiti:
        n = e.get("giro")
        if not n:
            continue
        if not B70._ha_misurato(n):
            print("  %-14s %-2s   %s" % (e["profilo"], e["braccio"],
                                         (n.get("esito") or "?")[:70]))
            continue
        q = e.get("quic") or {}
        print("  %-14s %-2s %7.2f %7s %6.1f%% %7s %8s %8s %9s"
              % (e["profilo"], e["braccio"], n["fps"], n["fps_finestra_min"],
                 (1 - n["quota_delta"]) * 100, n["deriva_fine_ms"],
                 n["deriva_max_ms"], n["mbit_s_filo"], q.get("cwnd_min")))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL PASSO `stacco` — «CHI» ha staccato su `raffica-forte`
# ═══════════════════════════════════════════════════════════════════════════
def stacco(a):
    """⛔ Non deduce: chiede a quattro testimoni indipendenti (vedi
       l'intestazione).  ⚠ E la terza possibilita' — «non si e' mai aperta» —
       si esclude ESPLICITAMENTE, perche' ha la stessa faccia dello stacco."""
    _log("09-b79 · `raffica-forte` — ⛔ CHI HA STACCATO?")
    p = profilo("raffica-forte")
    md5 = md5_binario()
    print("   ⭐ binario md5 %s · profilo netem: %s" % (md5, " ".join(p[1])))

    # ⭐ Il primo testimone si legge nel SORGENTE, prima di girare: `IDLE_MS`.
    rc, out, _ = root("bash -c \"grep -n 'IDLE_MS' %s/src/trasporto.c | head -4\""
                      % ALB)
    _inf("`[R]` src/trasporto.c: %s" % " | ".join(out.split()))

    if not B76.spedisci_sonda() or B76.scegli_porta_sonda() is None:
        _ko("i copioni o la porta della sonda non ci sono")
        return 2

    CHI = "09-b79-stacco"
    try:
        LUC.prendi(CHI, secondi=900, attesa=a.attesa)
    except Exception as e:
        _ko("⛔ NON MISURO: %s" % e)
        return 2
    RETE.guardiano_arma(1800)
    fuori = {}
    try:
        RETE.rimetti(dillo=False)
        ok, righe = riavvia("", 0, False)
        if not ok:
            _ko("il braccio A non e' in vigore: %s" % righe)
            return 2
        if not B70.innesca_sessione():
            _ko("la sessione d'innesco non si apre (a rete PULITA)")
            return 2
        _ok("⭐ a rete PULITA la sessione si apre: quel che segue e' del guasto")
        passa_r, perche_r, riletta = installa_profilo(p[1])
        (_ok if passa_r else _ko)("la regola: %s" % perche_r)
        if not passa_r:
            return 2
        s = B76.sonda_gira()
        B76.stampa_sonda(s)
        passa_g, perche_g = B76.p_guasto_messo("raffica-forte", p[6], s)
        (_ok if passa_g else (_dub if passa_g is None else _ko))(
            "IL GUASTO E' STATO MESSO: %s" % perche_g)
        fuori["sonda"] = s

        usc = B76.scena_accendi("barra")
        if not usc:
            _ko("la scena non parte")
            return 2
        n0 = registro_posato()      # ⛔ vedi `registro_posato`
        riga0 = B76.righe_registro()
        t0 = time.time()
        n = B70.giro("stacco-raffica-forte", "barra", B70.TELA_PIENA, a.secondi)
        if not conto_e_mio(n0, n):
            _dub("⚠ %s" % (n.get("server") or {}).get("conto_dubbio"))
        B76.scena_spegni()
        B70.stampa_giro(n)
        fuori["giro"] = n
        fuori["quic"] = leggi_rete_quic(riga0)
        stampa_rete_quic(fuori["quic"])

        # ── TESTIMONE 1 · IL CLIENTE, che lo dice da solo ──────────────────
        _log("TESTIMONE 1 · il cliente (`01-b3-cliente.py:1979`)")
        coda = ULTIMO_CLIENTE["testo"] or (n.get("coda_cliente") or "")
        print("   ┌─ il cliente, PER INTERO (⛔ non i suoi ultimi 400 byte) ─")
        for r in coda.splitlines():
            if r.strip() and "tput:" not in r:
                print("   │ %s" % r[:160])
        print("   └─")
        attaccato = "ancora attaccato dopo" in coda
        staccato = "NON sono rimasto attaccato" in coda
        fuori["cliente"] = {"attaccato_fino_in_fondo": attaccato,
                            "staccato": staccato, "coda": coda}
        if attaccato:
            _ok("⭐⭐ IL CLIENTE DICE CHE LA SESSIONE **NON** SI E' STACCATA: e' "
                "rimasto attaccato per tutti i %d s chiesti" % a.secondi)
        elif staccato:
            _ko("⛔ il cliente dice di essere caduto — e dice anche perche'")
        else:
            _dub("il cliente non ha detto ne' l'una ne' l'altra")

        # ── TESTIMONE 2 · IL REGISTRO DEL SERVER ───────────────────────────
        _log("TESTIMONE 2 · il registro del server — i motivi di congedo")
        cercati = ("congedo motivo=", "il client si congeda", "posto NEGATO",
                   "BANNATO", "SILENZIO", "conto finale", "chiusura",
                   "GIA_ATTIVA", "idle", "scaduto")
        fuori["registro"] = {}
        for c in cercati:
            rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                              "-i '%s' | tail -3\"" % (riga0 + 1, LAV, c))
            righe = [x[:200] for x in out.splitlines() if x.strip()]
            fuori["registro"][c] = righe
            if righe:
                for r in righe:
                    _inf("«%s» → %s" % (c, r))
        if not any(fuori["registro"][c] for c in
                   ("congedo motivo=", "il client si congeda", "posto NEGATO",
                    "BANNATO", "GIA_ATTIVA")):
            _ok("⭐ NESSUN congedo, NESSUN posto negato, NESSUN ban in tutto il "
                "giro: dal lato del server non ha staccato nessuno")

        # ── TESTIMONE 3 · LA STRETTA DI MANO — la terza possibilita' ───────
        _log("TESTIMONE 3 · ⚠ «non si e' mai aperta» ha la stessa faccia di "
             "«si e' staccata»")
        aperta = "SESSIONE" in coda or (n.get("fotogrammi_grezzi") or 0) > 0
        rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                          "'AMMESSO\\|ATTACCA\\|sessione aperta\\|monitor «' | "
                          "head -5\"" % (riga0 + 1, LAV))
        for r in out.splitlines()[:5]:
            _inf("apertura: %s" % r[:180])
        fuori["apertura"] = {"aperta": aperta, "righe": out.splitlines()[:5]}
        if aperta:
            _ok("⭐ LA SESSIONE SI E' APERTA (l'ipotesi «la stretta di mano non "
                "si completa» e' esclusa): `09-b78-apertura.py` l'aveva gia' "
                "misurato fino al 25 %% di perdita, 10 giri su 10 in ~1,3 s")
        else:
            _ko("⛔ la sessione NON si e' mai aperta: non e' uno stacco")

        # ── TESTIMONE 4 · LA FINESTRA, e il conto del server ───────────────
        _log("TESTIMONE 4 · la finestra di congestione e i conti del server")
        srv = (n.get("server") or {})
        _inf("SERVER  %s" % json.dumps(srv, ensure_ascii=False)[:600])
        q = fuori["quic"]
        if q.get("esito") == "letto":
            _inf("⭐ la finestra: cwnd min %s, mediana %s, fine %s · giudizi %s"
                 % (q["cwnd_min"], q["cwnd_mediana"], q["cwnd_fine"],
                    json.dumps(q["giudizi"], ensure_ascii=False)))
        fuori["secondi_veri"] = round(time.time() - t0, 1)
    finally:
        B76.scena_spegni()
        RETE.rimetti()
        LUC.molla(CHI)

    os.makedirs(FUORI, exist_ok=True)
    dove = os.path.join(FUORI, "09-b79-stacco.json")
    with open(dove, "w") as f:
        json.dump(fuori, f, ensure_ascii=False, indent=1)
    _inf("esiti in %s" % dove)

    # ── IL VERDETTO, e la parola giusta ────────────────────────────────────
    _log("IL VERDETTO su `raffica-forte`")
    n = fuori.get("giro") or {}
    if fuori.get("cliente", {}).get("attaccato_fino_in_fondo"):
        _ok("⭐⭐⭐ NESSUNO HA STACCATO.  La connessione e' rimasta viva per "
            "tutti i %d s; a fermarsi e' stata la CONSEGNA DEI FOTOGRAMMI dopo "
            "%s s.  ⇒ Il rosso di `09-b76` e' vero come numero e SBAGLIATO come "
            "parola: `p_niente_stacco` misura quanto e' durata la consegna, non "
            "se la connessione e' caduta.  ⛔ E il fatto resta grave — una "
            "sessione viva e MUTA e' uno schermo fermo — ma ha un altro nome e "
            "un'altra causa." % (a.secondi, n.get("vissuto_s")))
        return 0
    if fuori.get("cliente", {}).get("staccato"):
        _ko("⛔ IL CLIENTE E' CADUTO: %s" % fuori["cliente"]["coda"][-300:])
        return 1
    _dub("nessuno dei testimoni ha risposto: non ho niente da giudicare")
    return 3


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "appaia", "stacco", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: non tocca la macchina")
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--solo", default="", help="un profilo solo, per nome")
    p.add_argument("--bracci", default="ABC")
    p.add_argument("--profili", default=("ritardo-30,perdita-1,perdita-3,"
                                         "jitter-15,jitter-30,casa-cattiva,"
                                         "raffica-forte"))
    p.add_argument("--attesa", type=int, default=3600,
                   help="quanti secondi aspetto il lucchetto del netem")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    importa()
    if a.passo in ("rimetti", "stato"):
        _log("la rete della macchina di prova — dev «%s», porta %d" % (DEV, PORTA))
        _inf("attaccati alle porte NON mie: %s"
             % json.dumps(vicini_non_miei(), ensure_ascii=False))
        return 0 if RETE.rimetti() else 2
    if a.passo == "terreno":
        ok = B76.spedisci_sonda()
        _inf("binario md5 %s" % md5_binario())
        return 0 if (B70.terreno_controlla() and ok) else 2
    if a.passo == "stacco":
        return stacco(a)
    return appaia(a)


if __name__ == "__main__":
    sys.exit(principale())
