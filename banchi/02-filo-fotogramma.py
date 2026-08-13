#!/usr/bin/env python3
"""02-filo-fotogramma.py — ⛔ F2.4: il fotogramma giudicato contro `RCP.md`, byte per byte.

    python3 02-filo-fotogramma.py --elenco              le previsioni, senza misurare
    python3 02-filo-fotogramma.py                       il giro intero
    python3 02-filo-fotogramma.py --solo numero-zero    un caso solo
    python3 02-filo-fotogramma.py --guasto G1           con un guasto innestato nel GIUDICE
    python3 02-filo-fotogramma.py --certifica           sano -> G1 -> G2 -> G3 -> risanato
    python3 02-filo-fotogramma.py --uscita 02-filo-esiti.jsonl

⚠ Gira DOVUNQUE: non tocca la rete, non vuole aioquic, non vuole un server.
  ⛔ E questo NON e' una comodita': e' la ragione per cui esiste oggi.  Il
  prodotto della fase 2 non c'e' — `grep -c '0x0301\\|0x0302' src/*` da' **0**
  su tutti e tre i file, `[M]` 12 agosto 2026 — e `PIANO.md` §0.4 momento 1
  vuole il banco **prima** del prodotto.  Un banco che per esistere pretendesse
  il prodotto sarebbe scritto dopo, cioe' sarebbe scritto **sapendo che cosa il
  prodotto fa**, che e' precisamente il difetto muto contro cui `RCP.md` §0
  esiste.

===========================================================================
⛔ PERCHE' QUESTO BANCO ESISTE, E QUALE MISURA SBAGLIATA IMPEDISCE

La fase 2 consegna **un fotogramma**.  Il modo naturale di provarlo e':
si accende il server, si apre la pagina, si guarda se compare il desktop.

  ⛔ *Quella prova e' verde anche se server e pagina hanno capito `RCP.md`
     nello stesso modo sbagliato.*

E' `PIANO.md` §0.4: in v1 l'arbitro era **mstsc**, e quando sbagliavamo a
capire la specifica un client altrui protestava gratis.  Adesso client e server
sono nostri, ⛔ **e il pixel sullo schermo non distingue un protocollo capito
da un protocollo capito uguale in due**.  Un `istante` letto little-endian da
tutt'e due i lati dipinge un desktop perfetto.

Questo programma e' il **terzo lettore** del capitolo del video: giudica
un fotogramma leggendo **soltanto** `RCP.md` §2.5, §5.1, §5.2, §6.0 e §6.2 —
⛔ e chi lo fa crescere **non guarda `src/rcp.c` ne' `src/pagina.html`**.  Chi
l'ha scritto ha contato le occorrenze di `0x0301` in `src/` per sapere che sono
zero, e non ha aperto quei file.

===========================================================================
⛔ LE QUATTRO COSE CHE OGNI CASO VERIFICA, E LA QUARTA E' NUOVA

  1. ⛔ **l'esito giusto**, e gli esiti sono **TRE**, non due.  `RCP.md` chiede
     al client tre comportamenti diversi e confonderli e' la forma **E8**:

       ACCETTATO           si consegna al decodificatore
       SCARTATO            ⛔ si BUTTA e NON si consegna — e si tratta come un
                           buco (§6.2, §5.2).  La sessione **resta viva**
       ERRORE_PROTOCOLLO   la connessione cade, col motivo (§3)

     ⚠ Un banco a due esiti fa passare `SCARTATO` per `ERRORE_PROTOCOLLO`:
     cioe' promuove a caduta della sessione un fotogramma abbandonato dal
     server **di proposito**, che e' il caso normale di §5.1;

  2. ⛔ **quale byte**, non solo che e' rosso.  `fasi/01-filo-nudo.md` B4: un
     arbitro che dice la cosa giusta accusando il byte sbagliato manda la
     diagnosi a leggere il messaggio sbagliato.  Ogni verdetto porta lo
     scostamento dentro l'intestazione e la riga di `RCP.md` che lo regge;

  3. ⛔ **la regola citata**, e si confronta.  Un rosso con la sezione
     sbagliata accanto e' verde per chi guarda il colore (rilievo R7.12 di
     `fasi/01-filo-nudo.md`);

  4. ⭐⛔ **E IL QUARTO ESITO: `AMBIGUO`.**

     `fasi/01-filo-nudo.md` §«I dodici punti in cui `RCP.md` ammette due
     letture» e' l'esito piu' prezioso di B9, e nessun banco lo produceva: li
     ha trovati un programma scritto apposta, **dopo**.  Qui il quarto esito e'
     dentro il banco che gira ogni giorno.

     ⛔ Un caso `AMBIGUO` **non e' un caso da sistemare nel prodotto**: e' un
     posto in cui `RCP.md` non decide, e due implementazioni conformi
     divergono.  ⚠ Non fa fallire il giro — nessuno ha sbagliato — ⛔ **ma si
     stampa in fondo, si conta, e finisce nel registro**, perche' un'ambiguita'
     taciuta e' indistinguibile da una regola.

===========================================================================
⭐⛔ E IL 12 AGOSTO 2026 LE QUATTRO AMBIGUITA' SONO STATE CHIUSE — questo file
    E' STATO RISCRITTO DI CONSEGUENZA

*Il 12 agosto 2026 il coordinatore ha applicato a `RCP.md` le sette righe che
questo banco proponeva (§2.5, §5.2, §6.2, §11.1).  ⛔ Da quel momento le quattro
`AMBIGUO` che questo file stampava sono **regole normative**, e un giudice che
continuasse a chiamarle ambiguita' starebbe giudicando il documento di ieri.*

  | riga entrata in `RCP.md` | dove | qui era | qui e' adesso |
  |---|---|---|---|
  | **P2** `numero` parte da 1, lo 0 e' riservato | §6.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P6** il primo fotogramma dopo `SESSIONE` DEVE essere chiave | §5.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P5** `largh.`/`altezza` DEVONO valere la tela concessa | §6.2 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P3** un `0x03` sul canale di controllo | §2.5 | `AMBIGUO` | `ERRORE_PROTOCOLLO` |
  | **P1** nessuno stream video prima di `SESSIONE` | §2.5 | derivata da §3+§1 | **citata**: §2.5 |
  | **P4** FIN prima dei 28 byte | §6.2 | derivata da §3 | **citata**: §6.2 |

⛔ **E ogni riga ha DUE casi, non uno: quello che la viola e quello che la
   rispetta.**  Un arbitro che conosce una regola e non ha l'ingresso che la fa
   scattare non la fa rispettare, e il verde che da' e' quello che da' fiducia
   (`CODER.md` §4.6).  ⚠ E il caso che la **rispetta** non e' un di piu': senza,
   una regola scritta troppo larga — «ogni misura diversa da 1920x1080 e'
   `ERRORE_PROTOCOLLO`» invece che «diversa dalla tela **concessa**» —
   resterebbe verde su tutto il banco.  La tabella `REGOLE_NUOVE` tiene i due
   nomi accanto alla sigla, e il giro **conta** quante regole hanno tutt'e due:
   un conto scritto a mano sarebbe il numero che nessuno ricalcola.

⭐ **E l'esito `AMBIGUO` resta nel codice, con zero casi che lo pretendono** —
   ⛔ e lo si **dichiara in coda a ogni giro** invece di lasciarlo scoprire:
   «nessuna ambiguita' stampata» e «il ramo che le stampa non lo esercita
   nessun caso» sono due fatti diversi, ed e' la forma **E8** rivolta contro il
   banco stesso.  Resta per due ragioni: `RCP.md` tornera' ad ammettere due
   letture — ne ha ammesse **dodici** nella sola fase 1
   (`fasi/01-filo-nudo.md` B9) — e il guasto **G5**, *«il giudice della mattina
   del 12 agosto»*, fa produrre `AMBIGUO` al giudice a ogni certificazione.
   ⚠ Quel che G5 esercita e' il ramo del **giudice**, non quello che li stampa:
   coi quattro casi che pretendono `ERRORE_PROTOCOLLO`, un `AMBIGUO` e' un
   **rosso**, ed e' esattamente quel che deve essere.

===========================================================================
⛔⛔ E LA SERA DEL 12 AGOSTO 2026 LA CURA DI P5 NE HA APERTA UN'ALTRA — **D14**

*`RCP.md` §6.2 e' stato corretto due volte lo stesso giorno.  La seconda cura —
«la misura del fotogramma deve valere la **tela in vigore**» — ha reso **legale
il cambio di tela a meta' sessione** (§7.1, `ADATTA_TELA` -> `TELA(ADATTATA)`).
⛔ E ogni volta che si rende legale una cosa nuova, si apre quel che quella cosa
nuova porta con se'.*

  ⛔ §6.2 fa chiudere con `ERRORE_PROTOCOLLO` chi riceve una misura diversa
     dalla tela in vigore, **ma §6.2 dice anche** — sette righe piu' sotto —
     che *«gli stream sono indipendenti, quindi i fotogrammi possono arrivare
     fuori ordine»*.  ⇒ Dopo un `TELA(ADATTATA)` i fotogrammi **gia' in volo**
     portano **legittimamente** la misura precedente, e un client conforme a
     §6.2 **uccide una sessione sana**.

  ⚠ E' la stessa forma di **P5**, la riga che la mattina del 12 agosto e'
    rimasta due ore dentro il documento scritta male: *un server conforme a
    §7.1 ucciso da un client conforme a §6.2*.  ⛔ Ma non e' la stessa
    famiglia: P5 era una **lettura doppia** — due implementazioni conformi
    producevano byte diversi.  Qui due implementazioni conformi e attente
    producono **lo stesso byte**, e quel byte e' la chiusura della sessione.
    ⇒ E' una **contraddizione interna**: una regola che punisce un caso che il
    documento stesso rende legale — la forma gia' nominata due volte in
    `RCP.md` (§5.5, il cursore nascosto del rilievo R11.11; §9, le sette parole
    di §2.2 trovate da B5).

  ⭐ **E la cura esiste gia' nel documento, per un altro campo**: §7.1 protegge
     la stessa identica scena per le **coordinate di input** con una **grazia
     di un secondo** — *«e' l'unico momento in cui i due lati hanno
     legittimamente due verita' diverse»*, terza eccezione dichiarata di §3.
     Per i fotogrammi quella grazia non c'e'.  La proposta **P8** e' quella
     riga, scritta per il verso in cui manca: la strada buona esisteva gia' in
     casa.

⭐⛔ **E LA SERA STESSA IL COORDINATORE HA APPLICATO LE DUE CURE: DA QUI IN POI
    QUESTO GIUDICE LE FA RISPETTARE, E NON DICE PIU' `AMBIGUO` IN QUELLA
    SCENA.**  Le righe entrate sono due, e sono **P8** e **P9**:

     **P8** §6.2 in coda + §3 eccezione **6** — dopo un `TELA(ADATTATA)` il
            client **DEVE** accettare per **un secondo** i fotogrammi che
            portano la misura **precedente**, dipingendoli riscalati e
            **scrivendolo nel registro**; fuori dal secondo sono
            `ERRORE_PROTOCOLLO`, e lo e' **subito** una misura che non e' ne'
            quella in vigore ne' la precedente;
     **P9** §5.2 — il primo fotogramma alla **misura nuova** dopo un
            `TELA(ADATTATA)` **DEVE** essere una chiave **vera** (coi suoi
            parameter set), e il client **NON DEVE** consegnare al
            decodificatore un fotogramma la cui misura non e' quella per cui il
            decodificatore e' configurato (difetto **D13**, `[M]`).

⛔ **E la scena che uccide non basta: ce ne vogliono TRE per P8**, perche' una
   grazia scritta troppo larga e' un difetto quanto una regola scritta troppo
   stretta — ed e' esattamente cosi' che P5 e' finita sbagliata la prima volta:

     `p8-in-volo-dopo-adatta-tela`      una misura in vigore da quando la coda
                                        ha cominciato a svuotarsi ->
                                        **ACCETTATO**, e il giro controlla che
                                        la tolleranza sia **dichiarata** (§3,
                                        ultima riga)
     `p13-vecchia-dopo-la-chiave-nuova` la stessa misura, ma **la chiave alla
                                        misura nuova e' arrivata** ->
                                        `ERRORE_PROTOCOLLO`.  ⛔ La tolleranza
                                        non e' un permesso permanente
     `p8-misura-di-nessuna-tela`        una misura che in quella finestra non e'
                                        **mai** stata in vigore ->
                                        `ERRORE_PROTOCOLLO` **subito**

⭐ **E QUESTO BANCO NON HA UN OROLOGIO — E DALLA CURA DI P13 NON GLIENE SERVE
   PIU' UNO.**  La tolleranza finiva «dopo un secondo», che e' un fatto che sul
   filo non c'e': il caso doveva **dichiararlo**, e un arbitro che legge una
   registrazione non poteva vederlo affatto.  ⇒ Adesso finisce sulla **prima
   chiave alla misura nuova**, che e' un **fotogramma** — e i fotogrammi si
   vedono.  ⚠ Il tempo resta dichiarabile (`secondo_passato`) e non decide piu'
   niente: lo rimette a decidere il solo guasto **G10**, ed e' il caso
   `p13-linea-lenta` a dimostrare che la cura c'e'.

===========================================================================
⭐⛔⛔ E LE DUE CURE DI QUELLA SERA, LETTE CON L'OCCHIO OSTILE, NON REGGEVANO
     IN DUE PUNTI — **P10** e **P11**, trovati APPLICANDOLE, ed ENTRATI NEL
     DOCUMENTO IL GIRO DOPO

*E' successo di nuovo quel che e' successo stamattina, quando due delle sette
righe si sono rivelate sbagliate: a trovarle non e' stata una rilettura, e'
stato **chi doveva farle rispettare**.  ⛔ Nessuno dei due era un difetto del
prodotto: erano due punti in cui `RCP.md`, poche ore dopo la cura, non decideva
— e il coordinatore li ha chiusi nel giro seguente.*

  ⭐ **P10 — §5.2, la riga prima di quella del client**: *«il client
     riconfigura il decodificatore sulla prima **CHIAVE** alla misura nuova,
     non sul `TELA`»*, e la riga del client dice adesso *«ne' quella tollerata
     da §6.2»*.  ⛔ Prima, le due cure si contraddicevano sullo **stesso
     fotogramma**: §6.2 «accettalo e dipingilo», §5.2 «buttalo», e il documento
     non diceva in nessun punto **quando** si riconfigura — due letture
     conformi che divergevano sul filo.  ⇒ Qui la coppia di casi e'
     `p10-decodificatore-al-tela` (il client fuori posto: si ACCETTA lo stesso,
     ⛔ **col rilievo**) e `p10-decodificatore-alla-chiave` (il client dov'e'
     giusto: si accetta, **senza** rilievo).

  ⭐ **P11 — §6.2**: *«una tela che e' stata in vigore entro il **secondo
     appena passato**»* al posto di *«la tela precedente»*, e
     `ERRORE_PROTOCOLLO` subito per *«una misura che non e' mai stata in vigore
     in quella finestra»*.  ⛔ Al singolare la riga uccideva una sessione sana
     **un passo piu' in la'**: `ADATTA_TELA` lo manda l'utente che trascina una
     finestra, e trascinando se ne mandano due in un secondo — 1920x1080 ->
     `TELA(1600,900)` -> `TELA(1280,720)` — e la chiave aperta prima di tutto
     (la piu' grossa, la piu' lenta, quella che §5.2 vieta di abbandonare)
     portava una misura che non era ne' quella in vigore ne' la precedente.
     ⇒ Coppia: `p11-due-tele-nella-finestra` e `p11-misura-mai-in-vigore`.

===========================================================================
⛔⛔ E ALLA TERZA RILETTURA NE RESTANO DUE, DICHIARATE E NON CURATE — **P12** e
    **P13**.  Nessuna delle due si tocca da qui: `RCP.md` e' del coordinatore.

  ⛔ **P12 — §3 eccezione 6 e' rimasta al SINGOLARE mentre §6.2 e' passata alla
     finestra.**  §6.2 dice adesso *«una tela che e' stata in vigore entro il
     secondo appena passato»*; la riga 6 della tabella di §3 dice ancora *«i
     fotogrammi che portano la misura **precedente**»*.  ⛔ E §3 non e' un
     riassunto: dichiara *«le eccezioni sono sei, e sono tutte qui.  Fuori da
     questo elenco non se ne inventano»*, cioe' **vieta** la tolleranza piu'
     larga che §6.2 comanda.
     ⇒ Caso concreto, ed e' un caso che questo banco gia' porta:
     `p11-due-tele-nella-finestra`.  Un client scritto leggendo §3 **chiude**;
     uno scritto leggendo §6.2 **accetta e dipinge**.  Due implementazioni
     conformi, due byte diversi, e una delle due uccide una sessione sana — la
     **stessa** scena che P11 ha appena chiuso, sopravvissuta nella tabella che
     dichiara di essere completa.  ⚠ Qui il banco segue §6.2, che e' la sezione
     normativa del campo, e lo **dichiara** invece di sceglierlo in silenzio.

  ⛔ **P13 — il secondo di grazia e' un tempo, e quel che deve svuotarsi e' una
     CODA.**  `[?]` non misurata.  §6.2 tollera la misura vecchia per **un
     secondo** dal `TELA`; ma i fotogrammi in volo sono stream QUIC gia'
     aperti, e quanto ci mettono ad arrivare **dipende dalla banda**, non
     dall'orologio.  ⇒ Scena: tela 1920x1080, l'utente trascina, `TELA(ADATTATA,
     1280, 720)`; la **chiave** 1920x1080 aperta un istante prima pesa qualche
     MiB — §6.2 ne ammette fino a **16** — e la linea e' cattiva (il minimo di
     `CODER.md` §1 e' 480p25: le linee cattive sono **dentro** il modello).  Lo
     stream ci mette **piu' di un secondo** ad arrivare, e il client chiude con
     `ERRORE_PROTOCOLLO` un fotogramma che il server ha spedito quando era
     ancora legale, e che §5.2 gli vietava di abbandonare.
     ⛔ E qui non e' solo una sessione sana che cade: e' l'invariante **I1** —
     *«mai a staccare», «una sessione brutta vale piu' di una sessione
     chiusa»* — rotta **perche' la linea e' lenta**, che e' esattamente la
     condizione che I1 esiste per proteggere.  ⚠ La cura non e' allungare il
     secondo (un numero piu' grande sposta il difetto, non lo toglie): il
     client sa quando la coda si e' svuotata, perche' §5.2 gli garantisce una
     **chiave alla misura nuova**, e da quella in poi la misura vecchia non ha
     piu' scuse.  ⛔ Ma la riga e' del coordinatore, e questo banco non ha un
     orologio: qui si dichiara.

⚠ **E una `[?]` che P9 apre e NON chiude — dichiarata, non chiusa per
  simmetria**: §6.2 dice che i fotogrammi arrivano **fuori ordine**, quindi un
  delta alla misura nuova puo' arrivare **prima** della chiave che il server ha
  spedito per prima.  §5.2 vincola chi **spedisce**, e questo giudice — come
  per P6 da stamattina — la applica a chi **riceve**: e' la lettura severa.
  ⚠ E dalla riga di P10 il documento porta adesso un **candidato** di risposta
  per l'altra lettura — *«il client … non consegna al decodificatore un
  fotogramma la cui misura non e' quella per cui e' configurato … lo butta e lo
  tratta come un buco»*, che darebbe `SCARTATO` invece della chiusura — ⛔ ma
  **candidato non e' deciso**, e le due letture producono ancora byte diversi
  (`RICHIEDI_CHIAVE` contro `CONGEDO`).  ⛔ Per chiuderla serve una **misura**
  — quanto spesso un delta scavalchi la sua chiave sul filo vero — e questa
  non ce l'ha nessuno: resta `[?]`.

===========================================================================
⭐⛔⛔ E IL 13 AGOSTO 2026 LA RILETTURA OSTILE NE HA TROVATA UNA **DENTRO §6.2
     CONTRO SE STESSA** — **P21**, la settima della famiglia

*P8 -> P11 -> P13 -> P14 -> P19 -> P20 -> **P21**.  ⛔ Sei righe della stessa
famiglia ormai convivono nella stessa sezione, e questa e' venuta fuori
mettendole in fila: **due paragrafi di §6.2, a otto righe di distanza,
comandano il contrario sullo stesso fotogramma.**  ⚠ Non e' un difetto del
prodotto: e' il documento.*

  ⛔ Il paragrafo di **P19**: un fotogramma alla misura **nuova** puo' arrivare
     **prima** del `TELA` che la concede, e il client *«NON DEVE chiudere:
     trattiene»*.
  ⛔ Il paragrafo della tolleranza (**P11** + **P13**), otto righe sotto: una
     misura *«che non e' mai stata in vigore in quella finestra»* e'
     `ERRORE_PROTOCOLLO` **subito**.
  ⇒ Scena: `SESSIONE` 1920x1080 -> `TELA(ADATTATA, 1600, 900)`; il client manda
    `ADATTA_TELA(1280, 720)` e il fotogramma a 1280x720 arriva **prima** della
    risposta.  Due implementazioni conformi, **due byte diversi**.

⭐ **La cura, e la grandezza vera**: si trattiene finche' resta una
   `ADATTA_TELA` che **il client ha spedito lui** e a cui nessun `TELA` ha
   risposto — locale, monotona, indipendente dalla consegna, come `ATTACCA` per
   P20 e come `numero` per P14.  §7.1 garantisce che la risposta arrivi (*«a
   ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`, riuscito o
   no»*), e §4.2 che il canale sia ordinato ⇒ l'n-esimo `TELA` risponde
   all'n-esima richiesta.  ⛔ E chiude la `[?]` di P19 — *«fino a quando
   trattiene»*, che nel prodotto era **otto fotogrammi**: un fondo osservabile,
   ma pur sempre un sostituto.

⛔⛔ **E la prima stesura della cura era ancora un sostituto**, bocciata dal
    caso e non da una rilettura: diceva *«si trattiene la MISURA che il client
    ha nominato»*, e §4.5 dice che **la tela concessa puo' essere diversa da
    quella chiesta** — su KWin < 6.8 e' la strada normale (`SPECIFICHE.md`
    §6.3).  ⇒ Il client che chiede 1366x768 e riceve il 1280x720 che il
    compositore sta per concedere avrebbe chiuso una sessione sana **un passo
    piu' in la'**: l'ottava stesura, evitata.  Caso
    `p21-concessa-diversa-da-chiesta`, guasto **G14**.

⇒ Tre casi, come per P8, perche' una cura si sbaglia in **due** versi:
  `p21-nominata-e-in-volo` (la fa vedere) · `p21-concessa-diversa-da-chiesta`
  (impedisce di scriverla troppo stretta, **G14**) · `p11-misura-mai-in-vigore`
  (impedisce di scriverla troppo larga, **G15**).

===========================================================================
⛔ CHE COSA QUESTO BANCO **NON** PROVA, E VA DETTO

| | perche' non e' qui |
|---|---|
| che il server **spedisca** davvero un fotogramma | il prodotto non esiste (§0 di questo file).  Lo prova `02-filo-cliente.py` sulla **7514**, quando ci sara' |
| che i **pixel** decodificati siano quelli catturati | e' la sotto-fase **F2.6**, e non e' una misura di protocollo |
| che il **decodificatore** accetti i byte | e' **F2.5**: `VideoDecoder` e la tela |
| che la chiave alla misura nuova sia una chiave **vera** — §5.2 vuole i VPS/SPS/PPS davanti all'IDR | ⛔ questo giudice **non conserva i dati** del fotogramma, quindi di P9 vede la meta' che sta nell'intestazione (`tipo = 0x0301`) e non quella che sta nel carico.  La misurano `02-codifica-nal.py` e `02-pagina-tela-*` |
| il **credito** degli stream oltre i primi 256 fotogrammi (§2.3) | la fase 2 consegna **un** fotogramma fermo; e' la **fase 3** |
| l'**abbandono** vero con `RESET_STREAM` sul filo | qui si giudica un flusso azzerato, non se ne provoca uno.  Il banco che lo provoca e' della **fase 3** (`RCP.md` §11, «il fotogramma abbandonato») |

⚠ Scriverlo qui non e' modestia: un banco che tace su quel che non copre viene
letto come se coprisse tutto, ed e' cosi' che un verde diventa un'assoluzione.
"""
import argparse
import json
import os
import struct
import sys
import time

# ---------------------------------------------------------------------------
# ⛔ I NUMERI DI `RCP.md`, IN UN POSTO SOLO E CON LA SEZIONE ACCANTO.
#
#    Un numero ricopiato in tre punti e' un numero che prima o poi diverge in
#    uno dei tre, e nessuno se ne accorge finche' non produce un sintomo
#    lontano.  ⚠ `INTESTAZIONE` in particolare e' il numero che `RCP.md` §6.2
#    ha gia' dovuto correggere una volta, il 9 agosto 2026: il disegno dava
#    `… 24 │ 32`, cioe' quattro byte di riempimento mai dichiarati.
INTESTAZIONE = 28                 # §6.2, «28 byte esatti, senza riempimento»
TETTO_FOTOGRAMMA = 16 * 1024 * 1024   # §6.2, «NON DEVE produrre un fotogramma
                                      # piu' lungo di 16 MiB»
CHIAVE, DELTA = 0x0301, 0x0302    # §5.2, §6.2
CODEC = {1: "hevc", 2: "av1"}     # §6.2
CANALE_VIDEO = 0x03               # §2.5
CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}   # §2.5

# ⛔ Gli esiti, e sono QUATTRO.  Vedi il punto 1 e il punto 4 dell'intestazione.
ACCETTATO = "ACCETTATO"
SCARTATO = "SCARTATO"
ERRORE_PROTOCOLLO = "ERRORE_PROTOCOLLO"
AMBIGUO = "AMBIGUO"


class Verdetto:
    """Che cosa si e' deciso, con la riga di `RCP.md` che lo regge.

    ⛔ `scostamento` e' dentro l'intestazione del fotogramma, non dentro il
       file: qui non c'e' nessun file.  Chi legge una registrazione usa
       `02-filo-validatore.py`, che i due scostamenti di §11.1 li ha.
    """

    def __init__(self, esito, regola="", dice="", scostamento=None,
                 propone="", tollerato="", rilievo=None):
        self.esito = esito
        self.regola = regola
        self.dice = dice
        self.scostamento = scostamento
        self.propone = propone      # ⛔ solo per AMBIGUO: la cura, non il reclamo
        # ⛔ §3, ultima riga: *«ogni tolleranza va scritta nel registro.  Una
        #    tolleranza silenziosa e' indistinguibile da un difetto»*.  ⇒ Un
        #    fotogramma accettato **per un'eccezione** non ha lo stesso aspetto
        #    di uno accettato perche' era in regola, e il giro lo verifica.
        self.tollerato = tollerato
        # ⛔ P10 — un rilievo sullo **stato del client**, che non e' un giudizio
        #    sul filo e non cambia l'esito.  ⚠ Tenerli separati non e' ordine:
        #    un rilievo promosso a esito farebbe cadere una sessione in cui il
        #    server non ha sbagliato niente, ed e' la forma che questo capitolo
        #    ha gia' pagato tre volte oggi.
        self.rilievo = rilievo

    def __str__(self):
        p = [self.esito]
        if self.regola:
            p.append(f"[{self.regola}]")
        if self.dice:
            p.append(self.dice)
        if self.scostamento is not None:
            p.append(f"(byte {self.scostamento} dell'intestazione)")
        if self.rilievo:
            p.append(f"— RILIEVO SUL CLIENT: {self.rilievo}")
        return " ".join(p)

    def come_dizionario(self):
        return {"esito": self.esito, "regola": self.regola, "dice": self.dice,
                "scostamento": self.scostamento, "tollerato": self.tollerato,
                "rilievo": self.rilievo}


class Contesto:
    """Quel che il client sa gia' quando arriva un fotogramma.

    ⛔ Non e' un comodo: **meta' delle regole di §6.2 si applicano solo con
       questo in mano**.  `codec` «DEVE essere quello negoziato in §4.3»;
       `largh.`/`altezza` si confrontano con la **tela concessa** di §4.5; il
       `numero` si confronta con l'ultimo consegnato.  Un giudice senza
       contesto puo' dire soltanto se i 28 byte sono ben formati, che e' il
       terzo delle regole e non e' il piu' caro.
    """

    def __init__(self, tela=(1920, 1080), codec_negoziato=1,
                 sessione_aperta=True):
        # ⛔ LA TELA E' QUELLA **IN VIGORE**, E PUO' CAMBIARE A META' SESSIONE.
        #
        #    §6.2, corretta il 12 agosto 2026: *«DEVONO valere la tela in
        #    vigore — quella concessa in `SESSIONE` (§4.5), **oppure** l'ultima
        #    concessa da `TELA` se nel frattempo e' stata adattata (§7.1)»*.
        #    ⚠ La riga precedente diceva «la tela concessa in `SESSIONE`», e
        #      **uccideva una sessione sana**: dopo un `ADATTA_TELA` il server
        #      cattura alla misura nuova, e un client che confrontasse ancora
        #      con `SESSIONE` chiuderebbe — la scena che §7.1 protegge con la
        #      sua eccezione 4.  Trovata propagando la regola a questi arbitri.
        self.tela_larghezza, self.tela_altezza = tela
        # ⛔ E si tiene DA DOVE viene, perche' e' la meta' che il verdetto deve
        #    saper dire: «diversa dalla tela di `SESSIONE`» e «diversa dalla
        #    tela in vigore» mandano a cercare in due posti diversi.
        self.tela_da = "SESSIONE (§4.5)"
        # ⛔⭐ E LE DUE VERITA' IN VOLO — difetto **D14**, proposta **P8**.
        #
        #    §7.1 lascia cambiare la tela a meta' sessione; §6.2 dice che «gli
        #    stream sono indipendenti, quindi i fotogrammi possono arrivare
        #    fuori ordine».  ⇒ Subito dopo un `TELA(ADATTATA)` il client ha in
        #    volo fotogrammi che portano **legittimamente** la misura di prima,
        #    e §6.2 alla lettera gli fa chiudere la sessione.
        #    ⚠ `tela_precedente` e' `None` finche' non e' mai cambiata niente:
        #      `None` e' «non c'e' una precedente», e NON e' una misura.
        self.tela_precedente = None
        # ⛔⛔ E LE TELE CHE SONO STATE IN VIGORE **DA QUANDO LA CODA HA
        #    COMINCIATO A SVUOTARSI**, non una sola.  §6.2 nominava «la tela
        #    **precedente**» al singolare, ⚠ ma `ADATTA_TELA` lo manda l'utente
        #    che trascina una finestra, e trascinando se ne mandano parecchi:
        #    la tela puo' cambiare due volte mentre un fotogramma e' ancora in
        #    volo (rilievo **P11**, curato il 12 agosto 2026).
        self.tele_recenti = []
        # ⛔⭐ D13, §5.2: dopo un `TELA(ADATTATA)` il primo fotogramma alla
        #    misura NUOVA DEVE essere una chiave vera.  ⚠ `True` di suo vuol
        #    dire «non c'e' nessun cambio di tela in sospeso»: a inizio sessione
        #    la riga che comanda e' quella di P6, non questa.
        #
        # ⛔⭐⭐ E DALLA CURA DI **P13** QUESTO CAMPO FA **DUE** MESTIERI, ed e'
        #    il punto di tutta la cura: e' anche **la fine della tolleranza**.
        #    §6.2: *«la tolleranza non finisce a orologio: finisce quando arriva
        #    la prima chiave alla misura nuova»*.  ⇒ La coda si sta svuotando
        #    finche' questo e' `False`, e non c'e' nessun secondo da misurare —
        #    ⭐ **la fine e' un fatto osservabile sul filo**, e per questo il
        #    banco non ha piu' bisogno di un orologio che non ha mai avuto.
        self.chiave_alla_tela_nuova = True
        # ⛔ E IL SECONDO RESTA QUI, DICHIARATO E **INERTE** — non decide piu'
        #    niente.  ⚠ Non e' un residuo: e' la leva del guasto **G10**, «il
        #    giudice con l'orologio», cioe' la riga com'era due ore prima.  Un
        #    campo che non decide e che nessun guasto esercita andrebbe tolto;
        #    questo lo esercita, e dimostra che la cura di P13 e' **provata** e
        #    non raccontata.
        self.secondo_passato = False
        # ⛔⛔ E A CHE MISURA E' CONFIGURATO IL DECODIFICATORE — `None` = «non
        #    dichiarato», e NON e' «alla tela in vigore».
        #
        #    §5.2 (sera del 12 agosto) dice che il client **NON DEVE** consegnare
        #    al decodificatore un fotogramma la cui misura non e' quella per cui
        #    il decodificatore e' configurato; §6.2 (la stessa sera) dice che
        #    **DEVE** accettare e **dipingere** i fotogrammi in volo alla misura
        #    precedente.  ⇒ Le due righe si incontrano sullo stesso fotogramma,
        #    e chi le legge deve sapere **quando il client riconfigura**: al
        #    `TELA`, o alla prima chiave alla misura nuova.  ⛔ `RCP.md` non lo
        #    dice in nessun punto — vedi la proposta **P10**.
        self.decodificatore_a = None
        self.codec_negoziato = codec_negoziato
        # ⛔⛔ E QUESTE DUE NON SONO LA STESSA COSA — proposta **P20**.
        #
        #    `sessione_aperta` dice *«i byte di `SESSIONE` li ho gia' visti»*,
        #    e ⛔ **e' una grandezza sostitutiva**: il canale di controllo e lo
        #    stream del fotogramma sono due stream QUIC indipendenti, e
        #    RFC 9000 non ne ordina la consegna — §6.2 lo scrive due volte
        #    (P14, P19).  ⇒ Basta che si perda il pacchetto che porta
        #    `SESSIONE` perche' questo campo sia `False` mentre il server ha
        #    fatto **esattamente** quel che §2.5 e §5.2 gli impongono.
        #
        # ⭐ `attacca_spedito` e' la grandezza **vera**, ed e' quel che `numero`
        #    e' stato per P14: un fatto **locale, monotono e indipendente
        #    dall'ordine di consegna**.  §4.5 fa di `SESSIONE` la risposta ad
        #    `ATTACCA` ⇒ un server che non ha ricevuto `ATTACCA` **non puo'**
        #    aver spedito `SESSIONE`, e il client sa senza margine di errore se
        #    l'ha spedito, perche' l'ha spedito lui.
        #    ⚠ E copre l'invariante che la riga difende: il client che ha
        #      spedito `ATTACCA` e' gia' passato da `AMMESSO` (§1), cioe' **dal
        #      validatore** — che e' tutto quel che I3 chiede.
        self.sessione_aperta = sessione_aperta
        self.attacca_spedito = True
        # ⛔ `None` e' «nessuno», e NON e' zero: §6.0 vieta i valori sentinella
        #    impliciti, e zero e' un `numero` che il documento non esclude —
        #    vedi il caso `numero-zero`, che e' l'ambiguita' A1.
        self.ultimo_consegnato = None
        self.chiave_consegnata = False
        self.chiedi_chiave = False    # §5.2: il client DEVE chiederla su un buco
        # ⛔ «Questo lettore applica l'eccezione 6 di §3?» — e NON e' «il
        #    secondo non e' ancora passato»: il secondo non c'e' piu' (P13).
        self.grazia_concessa = True
        # ⛔⛔⭐ E LE RICHIESTE DI CAMBIO TELA CHE IL CLIENT HA SPEDITO E CHE
        #     NESSUN `TELA` HA ANCORA RISPOSTO — proposta **P21**, 13 agosto 2026.
        #
        #     ⚠ **Non e' un elenco di misure: e' un conto di richieste in volo**,
        #       e la differenza e' tutta la cura.  La grandezza vera del fenomeno
        #       *«questo fotogramma appartiene a un mondo che ho chiesto io e che
        #       non mi e' ancora stato risposto»* e' **il messaggio spedito**, non
        #       i numeri che porta — esattamente come per **P20** e' `ATTACCA` e
        #       non la tela che `ATTACCA` chiede.  ⛔ Le misure si tengono per il
        #       **registro** e per il guasto **G14**, mai per decidere: §4.5 dice
        #       che *«la tela concessa puo' essere diversa da quella chiesta»*, e
        #       un discriminante scritto sui numeri chiuderebbe una sessione sana
        #       il giorno in cui il compositore concede una misura vicina invece
        #       di quella chiesta (`SPECIFICHE.md` §6.3 e §6.4).
        #     ⭐ Locale, monotona, indipendente dalla consegna: il client sa
        #       quante `ADATTA_TELA` ha spedito perche' le ha spedite lui, e sa
        #       che a ciascuna arrivera' un `TELA` perche' §7.1 lo impone.
        #     ⛔ Vuota di suo: chi non dichiara niente ha il giudice di ieri, e
        #       nessun lettore che importa questo file (`01-b4-validatore.py`,
        #       `02-filo-validatore.py`) cambia verdetto senza saperlo — I6.
        self.adatta_in_volo = []

    def adatta_spedito(self, lar, alt):
        """⭐⛔ **Il client ha spedito un `ADATTA_TELA(lar, alt)`** — §7.1, e la
        risposta non e' ancora arrivata.

        ⛔ E' un fatto **del client**, non del filo che il client riceve: sta qui
           per la stessa ragione per cui ci sta `attacca_spedito` (P20).  Un
           arbitro che legge una **registrazione** lo vede lo stesso, perche'
           §11.1 registra tutt'e due i versi.
        """
        self.adatta_in_volo.append((lar, alt))

    def risponde_il_tela(self):
        """⛔ E' arrivato un `TELA`: **una** richiesta in volo e' stata risposta.

        ⭐ Quale?  **La piu' vecchia**, e non e' una scelta di comodo: il canale
           di controllo e' **uno solo, affidabile e ordinato** (§4.2, §2.5) e
           §7.1 impone **un** `TELA` a **ogni** `ADATTA_TELA` ⇒ l'n-esimo `TELA`
           risponde all'n-esimo `ADATTA_TELA`.  ⚠ Senza questa riga la cura di
           P21 non sarebbe scritta affatto nella scena che P11 ha gia' pagato —
           chi trascina una finestra ne manda **due**.

        ⚠ Vale per tutt'e due gli esiti: un `TELA(RIFIUTATA)` risponde quanto un
          `TELA(ADATTATA)` (§7.1, *«riuscito o no»*).
        """
        if self.adatta_in_volo:
            self.adatta_in_volo.pop(0)

    def adatta_tela(self, lar, alt, precedente=None, grazia=True):
        """§7.1 — e' arrivato un `TELA(ADATTATA, lar, alt)`.

        ⛔ Da questo momento la tela **in vigore** e' un'altra, e §6.2 ci lega
           `largh.`/`altezza` di ogni fotogramma successivo.  ⚠ Chi chiama
           questo metodo lo fa perche' ha **visto** il messaggio sul filo: il
           giudice del fotogramma non lo puo' sapere da solo, e infatti la tela
           gli si dichiara sempre da fuori.

        ⛔⭐ E si tiene **la precedente**, perche' e' la meta' del difetto D14:
           i fotogrammi gia' in volo la portano **legittimamente**, e senza
           averla in mano il client non puo' distinguere «una misura vecchia
           che sta ancora arrivando» da «una misura che non e' mai stata di
           nessuna tela» — cioe' non puo' fare quel che §7.1 fa gia' per le
           coordinate di input.  ⚠ `precedente` si puo' passare da fuori: chi
           legge una **registrazione** ricostruisce le tele sfogliando il file,
           e il contesto lo riusa da un flusso all'altro.

        ⛔⛔ **E LA CODA CHE SI SVUOTA NON HA PIU' UN INTERRUTTORE DEL TEMPO** —
           cura di **P13**, 12 agosto 2026.  §6.2: *«la tolleranza non finisce
           a orologio: finisce quando arriva la prima chiave alla misura
           nuova»*.  ⇒ Qui non si apre nessun secondo: si apre un **debito**
           (`chiave_alla_tela_nuova = False`), e a chiuderlo e' un fotogramma,
           non un cronometro.  ⭐ Il che rende giudicabile da un `.rcpreg` una
           cosa che prima non lo era.

        ⛔⛔ **E `grazia` E' ACCESA DI SUO DALLA SERA DEL 12 AGOSTO 2026 —
           cambiata, e la scelta va dichiarata.**

           Fino a quella sera era **spenta**, e con ragione: la grazia era la
           proposta **P8**, non una riga del documento, e accendere di suo una
           proposta avrebbe cambiato in silenzio il verdetto di
           `01-b4-validatore.py`, che la importa e non sa niente di D14 — cioe'
           l'invariante **I6** applicata a un banco.

           ⭐ Adesso `RCP.md` §6.2 la porta, ed e' la **sesta eccezione** di §3.
           ⇒ L'interruttore ha cambiato mestiere: spenta di suo, il predefinito
           sarebbe **il documento di ieri**, e ogni lettore che non conosce D14
           — B4 compreso — farebbe cadere una sessione sana senza che nessuno
           gliel'abbia chiesto.  ⛔ I6 protegge *«cio' che cambia quel che si
           vede»* da un cambiamento **non guardato**: qui il cambiamento e'
           stato guardato, sta nel documento, e il predefinito che tradisce non
           e' piu' quello acceso ma quello spento.
           ⚠ Il parametro **resta**, e serve al guasto **G6**: si spegne per
             dimostrare che il banco sa vedere la differenza fra il giudice di
             stasera e quello di ieri sera.

        ⛔ E UN `TELA` CHE RIPETE LA MISURA IN VIGORE NON E' UN CAMBIO: non
           lascia niente in volo, e riazzerare qui lo stato farebbe diventare
           `ERRORE_PROTOCOLLO` il delta legittimo che segue la chiave nuova
           quando i due arrivano su **due flussi** diversi (e' cosi' che
           `02-filo-validatore.py` e `01-b4-validatore.py` rimettono il contesto
           a posto flusso per flusso).
        """
        # ⛔ P21 — E UN `TELA` RISPONDE A UNA RICHIESTA, PRIMA DI QUALUNQUE
        #    ALTRA COSA: anche quello che ripete la misura in vigore, anche
        #    quello che rifiuta.  ⚠ Metterlo dopo il ritorno anticipato qui
        #    sotto lascerebbe in volo per sempre una richiesta a cui il server
        #    ha risposto — cioe' un client che trattiene senza fine.
        self.risponde_il_tela()
        if (lar, alt) == (self.tela_larghezza, self.tela_altezza):
            # ⛔ Niente e' cambiato: non c'e' nessuna «misura nuova» che pretenda
            #    una chiave (§5.2) e non c'e' niente in volo da graziare (§6.2).
            #    ⚠ E il caso esiste davvero: §7.1 fa rispondere `TELA` a **ogni**
            #      `ADATTA_TELA`, anche a uno che chiede la misura che c'e'
            #      gia'.  Aprire li' un debito di chiave farebbe cadere il
            #      delta legittimo che segue — un rosso su una sessione sana.
            self.tela_da = "TELA(ADATTATA) (§7.1)"
            return
        prec = (precedente if precedente is not None
                else (self.tela_larghezza, self.tela_altezza))
        # ⛔ La lista tiene la precedente **e** quelle di prima, se la coda si
        #    stava gia' svuotando: due `TELA` di fila sono la scena normale di
        #    chi trascina una finestra (P11).
        self.tele_recenti = ([prec] + self.tele_recenti
                             if self.coda_da_svuotare() else [prec])
        self.tela_precedente = prec
        # ⚠ `grazia` non apre piu' un tempo: dice soltanto **se questo lettore
        #   applica l'eccezione 6 di §3**.  Spenta (guasto G6) la coda non si
        #   tollera affatto, ed e' il giudice di prima della cura.
        self.grazia_concessa = bool(grazia)
        self.chiave_alla_tela_nuova = False
        self.tela_larghezza, self.tela_altezza = lar, alt
        self.tela_da = "TELA(ADATTATA) (§7.1)"

    def coda_da_svuotare(self):
        """⭐⛔ **La coda si sta ancora svuotando?** — §6.2, cura di **P13**.

        E' `True` fra un `TELA(ADATTATA)` e **la prima chiave alla misura
        nuova**, che §5.2 garantisce esistere.  ⛔ Non c'e' nessun orologio, e
        non e' una comodita' del banco: era la riga a essere sbagliata.

        ⚠ *Il secondo era la grandezza sbagliata.*  Quel che deve svuotarsi e'
          una **coda**, e quanto ci mette un fotogramma gia' in volo dipende
          dalla **banda**: una chiave 1920x1080 di qualche MiB (§6.2 ne ammette
          16) su una linea cattiva — che e' **dentro** il modello, il minimo e'
          480p a 25 — arriva **dopo** il secondo.  ⇒ Il client avrebbe chiuso
          un fotogramma spedito quando era legale, e che §5.2 vietava al server
          di abbandonare: l'invariante **I1** («mai a staccare») rotta
          **perche' la linea e' lenta**, cioe' nella condizione esatta che I1
          esiste per proteggere.  ⭐ E allungare il secondo avrebbe **spostato**
          il difetto invece di toglierlo.
        """
        return (self.grazia_concessa and not self.chiave_alla_tela_nuova
                and bool(self.tele_recenti))

    def arriva_la_chiave_nuova(self):
        """⛔ E' arrivata la prima chiave alla misura nuova: **la coda e'
           svuotata**, e da qui in poi una misura vecchia e'
           `ERRORE_PROTOCOLLO` come qualunque altra (§6.2).

        ⚠ Fino alla cura di **P13** questo metodo si chiamava
          `scade_la_grazia()` e diceva *«e' passato il secondo»* — un fatto che
          **non viaggia sul filo** e che il caso doveva dichiarare.  ⭐ Adesso
          il fatto e' un **fotogramma**, e lo si vede: e' la differenza fra una
          regola che un arbitro meccanico puo' far rispettare e una che deve
          indovinare.
        """
        self.chiave_alla_tela_nuova = True
        # ⛔ E con la coda se ne vanno le misure vecchie: non sono piu' «in
        #    volo», sono misure che non valgono piu' niente (§6.2).
        self.tele_recenti = []


# ---------------------------------------------------------------------------
class Giudice:
    """Giudica UN fotogramma mentre arriva, non dopo che e' arrivato.

    ⛔ **E il «mentre» e' normativo, non un vezzo di ingegneria.**  §6.2:
       *«Chi ne riceve uno piu' lungo chiude con `ERRORE_PROTOCOLLO` **invece
       di continuare ad accumulare**»*.  Un giudice che prende in mano il
       fotogramma intero e poi ne misura la lunghezza ha gia' fatto la cosa che
       quella riga vieta — e su una tela 7680x4320 il fotogramma che vuole
       fermare e' precisamente quello che non entra in memoria.

    ⛔ **E non conserva i dati.**  Conta i byte e li lascia andare: un banco che
       li tenesse per «guardarli meglio» misurerebbe la propria memoria.
    """

    def __init__(self, contesto, dove="uni", guasti=()):
        self.c = contesto
        self.dove = dove              # "uni" | "controllo"
        self.guasti = set(guasti)
        self.grezzo = bytearray()     # SOLO l'intestazione, mai i dati
        self.byte_dati = 0
        self.verdetto = None          # il primo verdetto vince
        self.letta = False
        self.campi = {}

        # ── i guasti innestabili, e ciascuno rompe UNA proprieta' ────────────
        # ⛔ Stanno qui e non in una copia del file perche' cio' che va
        #    guastato e' **il giudizio**, non lo scoring: un interruttore che
        #    spegnesse un controllo farebbe diventare rosso il banco senza
        #    dimostrare che il banco sa vedere quel guasto.  Vedi `--elenco`.
        self.intestazione = 32 if "G1" in self.guasti else INTESTAZIONE
        self.tipi_leciti = ({CHIAVE, DELTA, 0x0300} if "G2" in self.guasti
                            else {CHIAVE, DELTA})
        self.reset_come_fin = "G3" in self.guasti
        # ⛔ G5 — «il giudice della mattina del 12 agosto 2026», cioe' PRIMA che
        #    le quattro righe entrassero in `RCP.md`.  Vedi l'intestazione.
        self.regole_12_agosto = "G5" not in self.guasti
        # ⛔ G6 e G7 — «il giudice della SERA del 12 agosto», prima delle due
        #    cure di D13 e D14.  Ognuno spegne una riga sola.
        self.grazia_di_6_2 = "G6" not in self.guasti      # D14, §6.2 + §3 ecc. 6
        self.chiave_di_5_2 = "G7" not in self.guasti      # D13, §5.2
        # ⛔ G8 e G9 — «il giudice di due ore fa», cioe' fra le due cure della
        #    sera e le due che le hanno rimesse in piedi (P11 e P10).
        self.finestra_di_6_2 = "G8" not in self.guasti    # P11: la finestra
        self.rilievo_di_5_2 = "G9" not in self.guasti     # P10: il rilievo
        # ⛔ G10 — «il giudice con l'orologio»: la tolleranza torna a finire a
        #    tempo, cioe' la riga com'era prima della cura di **P13**.
        self.orologio_tolto = "G10" not in self.guasti
        # ⛔ G11 — «il giudice di un'ora fa»: la misura guardata PRIMA
        #    dell'ordine, cioe" §6.2 senza la precedenza di P14."
        self.ordine_prima = "G11" not in self.guasti
        # ⛔⛔ G12 e G13 — I DUE MODI DI SCRIVERE MALE **P20**, uno per verso.
        #
        #    G12 «la grandezza sostitutiva»: si misura §2.5 sull'arrivo di
        #        `SESSIONE` invece che sulla partenza di `ATTACCA` — cioe' il
        #        giudice di **oggi**, e il cliente di prova al suo primo giro
        #        dal vivo (`P2-6` §5.2).  ⇒ La sessione sana cade.
        #    G13 «la cura scritta troppo larga»: non si chiude **mai** prima di
        #        `SESSIONE`.  ⇒ I3 sparisce, e un server che non ha ricevuto
        #        `ATTACCA` puo' spingere pixel addosso a chi non si e' ancora
        #        attaccato.  ⚠ E' la forma con cui **P5** e' finita sbagliata:
        #        una cura che salva il caso che l'ha motivata e apre l'altro.
        self.sessione_come_grandezza = "G12" in self.guasti
        self.chiude_prima_di_attacca = "G13" not in self.guasti
        # ⛔⛔ G14 e G15 — I DUE MODI DI SCRIVERE MALE **P21**, uno per verso, e
        #     il primo non e' inventato: e' **la cura come e' stata proposta**.
        #
        #     G14 «il discriminante scritto sulla MISURA nominata»: si trattiene
        #         solo un fotogramma la cui misura il client ha nominato lui in
        #         un `ADATTA_TELA`.  ⛔ Troppo STRETTA: §4.5 dice che la tela
        #         concessa puo' essere diversa da quella chiesta, e su KWin < 6.8
        #         (`SPECIFICHE.md` §6.3) e' la strada normale ⇒ la sessione sana
        #         cade **un passo piu' in la'**, che e' la firma di questa
        #         famiglia da P8 in poi.
        #     G15 «trattiene sempre»: ogni misura mai in vigore si trattiene,
        #         anche senza nessuna richiesta in volo.  ⛔ Troppo LARGA: porta
        #         via la riga di P11 — quella che chiude **subito** su una misura
        #         che nessuno ha mai chiesto — cioe' proprio dove il server e'
        #         piu' probabile che sbagli.
        self.p21_sulla_misura = "G14" in self.guasti
        self.p21_trattiene_sempre = "G15" in self.guasti
        # ⛔ La misura tollerata dalla grazia si TIENE, non si decide subito:
        #    un fotogramma in volo resta soggetto a tutte le altre righe di
        #    §6.2 — l'ordine dei `numero`, il tetto, il FIN — e decidere qui
        #    salterebbe `_giudica_completo`, cioe' assolverebbe uno stream che
        #    non si e' mai chiuso.
        self.misura_tollerata = None
        # ⛔ Il rilievo sullo **stato del client** (P10), che non e' l'esito:
        #    vedi il punto 8-bis.  `None` = «non c'era niente da dire», e non
        #    e' «non ho guardato»: il decodificatore si dichiara da fuori, e
        #    quando non e' dichiarato il banco non inventa dove sia.
        self.rilievo_cliente = None

    # -- l'esito si scrive una volta sola: il primo verdetto e' la causa, i
    #    successivi sono conseguenze (come `_cade` in `01-b3-cliente.py`).
    def _decidi(self, v):
        if self.verdetto is None:
            self.verdetto = v
        return self.verdetto

    def _chiuso_il_12_agosto(self, sigla, scostamento, regola, dice,
                             regola_prima, dice_prima):
        """Una delle quattro letture doppie che `RCP.md` ha chiuso il 12 agosto.

        ⛔ Le due meta' stanno **nella stessa funzione** apposta: la riga di
           oggi e quella di ieri si leggono una sotto l'altra, e chi rileggesse
           questo file fra un mese vede subito **che cosa e' cambiato e
           perche'**.  ⚠ Tenerle in due punti lontani e' il modo in cui una
           delle due invecchia da sola.

        Col guasto **G5** innestato si torna alla lettura di ieri: il verdetto
        e' `AMBIGUO` invece di `ERRORE_PROTOCOLLO`, e i quattro casi che devono
        cadere diventano rossi con la marca `nome: ERRORE_PROTOCOLLO -> AMBIGUO`.
        """
        if not self.regole_12_agosto:
            return self._decidi(Verdetto(AMBIGUO, regola_prima, dice_prima,
                                         scostamento=scostamento,
                                         propone=sigla))
        return self._decidi(Verdetto(ERRORE_PROTOCOLLO, regola, dice,
                                     scostamento=scostamento))

    def arrivano(self, pezzo):
        """Arriva un pezzo dello stream.  Puo' gia' bastare a decidere."""
        if self.verdetto is not None:
            return
        if not self.letta:
            manca = self.intestazione - len(self.grezzo)
            self.grezzo += pezzo[:manca]
            pezzo = pezzo[manca:]
            if len(self.grezzo) == self.intestazione:
                self.letta = True
                self._leggi_intestazione()
                if self.verdetto is not None:
                    return
        self.byte_dati += len(pezzo)
        # ⛔ IL TETTO SI CONTROLLA QUI, MENTRE I BYTE SCORRONO — §6.2.
        if self.intestazione + self.byte_dati > TETTO_FOTOGRAMMA:
            self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"il fotogramma ha superato i {TETTO_FOTOGRAMMA} byte "
                f"({self.intestazione + self.byte_dati} finora): si chiude "
                f"«invece di continuare ad accumulare»"))

    def finisce(self, come):
        """`come` e' «fin» o «reset».  ⛔ E la differenza e' tutto §6.2."""
        if come not in ("fin", "reset"):
            raise ValueError(f"uno stream finisce con «fin» o «reset», non {come!r}")
        # ⛔ IL RESET SI GUARDA PER PRIMO, E PRIMA ANCORA DELL'INTESTAZIONE.
        #
        #    §6.2, rilievo R1.7: *«uno stream azzerato porta un fotogramma
        #    INCOMPLETO: il client DEVE buttare quel che ha ricevuto, NON DEVE
        #    consegnarlo al decodificatore, e DEVE trattarlo come un buco»*.
        #    ⚠ Un giudice che leggesse prima l'intestazione direbbe
        #    `ERRORE_PROTOCOLLO` su un `tipo` storto dentro un fotogramma che
        #    **non esiste**: il server lo ha abbandonato a meta', e i byte di
        #    quell'intestazione possono essere qualunque cosa.  Farebbe cadere
        #    la sessione per un abbandono, che e' il caso normale di §5.1.
        if come == "reset" and not self.reset_come_fin:
            self.c.chiedi_chiave = True
            return self._decidi(Verdetto(
                SCARTATO, "RCP.md §6.2",
                "stream azzerato: fotogramma INCOMPLETO — si butta, non si "
                "consegna al decodificatore, e si tratta come un buco (§5.2)"))
        if self.verdetto is not None:
            return self.verdetto
        if not self.letta:
            # ⛔ P4 — FIN PRIMA DEI 28 BYTE, e dal 12 agosto 2026 e' **citata**.
            #
            #    §6.2, terza riga di «⛔ La regola, in due righe:»: *«uno stream
            #    chiuso con FIN prima dei 28 byte dell'intestazione e'
            #    ERRORE_PROTOCOLLO: non e' un fotogramma corto, e' una
            #    lunghezza che non torna (§3)»*.
            #    ⚠ Fino all'11 agosto la regola si **ricavava** da §3, e §6.2 —
            #      il posto in cui chi implementa la guarda — non la scriveva:
            #      letta alla lettera, *«la fine dello stream e' la fine del
            #      fotogramma»* faceva di uno stream di 12 byte un fotogramma
            #      con **meno sedici** byte di dati.
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"lo stream finisce con FIN dopo {len(self.grezzo)} byte: "
                f"l'intestazione ne vuole {self.intestazione} esatti",
                scostamento=len(self.grezzo)))
        return self._decidi(self._giudica_completo())

    # -- l'intestazione, campo per campo, nell'ordine di §6.2 ----------------
    def _leggi_intestazione(self):
        g = bytes(self.grezzo[:INTESTAZIONE])
        tipo, codec, lar, alt, num, ist, inp = struct.unpack("!HHIIIQI", g)
        self.campi = {"tipo": tipo, "codec": codec, "larghezza": lar,
                      "altezza": alt, "numero": num, "istante": ist,
                      "input": inp}

        # 1. ⛔ IL CANALE, DAL BYTE ALTO — §2.5, e MAI dal numero dello stream.
        alto = tipo >> 8
        if alto != CANALE_VIDEO:
            nome = CANALI.get(alto)
            if nome is None:
                return self._decidi(Verdetto(
                    ERRORE_PROTOCOLLO, "RCP.md §2.5",
                    f"il byte alto del tipo vale {alto:#04x}: fuori dai cinque "
                    f"canali", scostamento=0))
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §2.5",
                f"su questo stream arriva il canale «{nome}» ({alto:#04x}) "
                f"dal server: e' il canale sbagliato, o il verso sbagliato",
                scostamento=0))

        # 2. ⭐⛔ P3 — DOVE E' ARRIVATO.  Chiusa il 12 agosto 2026.
        #
        #    §2.5, riga `0x03`: *«l'intestazione di 28 byte di §6.2, senza
        #    inquadratura — ⛔ e SOLO su uno stream unidirezionale aperto dal
        #    server: un `0x03` sul canale di controllo e' ERRORE_PROTOCOLLO,
        #    come lo e' un `0x00` su uno stream unidirezionale»*.
        #    ⚠ Fino all'11 agosto la stessa tabella chiudeva il caso per due
        #      canali su cinque e **non per il video**, e il client leggeva quei
        #      28 byte con l'inquadratura di §6.1 — un messaggio inventato di
        #      64 KiB.  Il server non apre stream bidirezionali (§2.5), quindi
        #      l'unico posto in cui puo' scrivere un `0x03` fuori posto e' il
        #      canale di controllo, che il client gli ha aperto.
        if self.dove == "controllo":
            return self._chiuso_il_12_agosto(
                "P3", 0, "RCP.md §2.5",
                "un fotogramma sul canale di CONTROLLO: §2.5 vuole il video "
                "«solo su uno stream unidirezionale aperto dal server», e un "
                "`0x03` sul canale di controllo e' ERRORE_PROTOCOLLO",
                "RCP.md §2.5",
                "un fotogramma sul canale di CONTROLLO: §2.5 vieta per nome il "
                "controllo su uno stream unidirezionale e l'audio su uno "
                "stream, e per il video non dice niente")

        # 3. ⛔ P1 — LO STATO, e dal 12 agosto 2026 e' **citata**.
        #
        #    §2.5, riga «video» della tabella: *«uno per fotogramma, ⛔ e
        #    nessuno prima di aver spedito `SESSIONE`: chi ne riceve uno prima
        #    chiude con ERRORE_PROTOCOLLO»*.
        #    ⚠ Fino all'11 agosto per chi RICEVE la regola si ricavava da §1
        #      («l'ordine dei cinque passi non ammette permute») piu' §3, e per
        #      chi MANDA non si ricavava da nessuna parte: era l'invariante
        #      **I3** — *chi non passa dal validatore non riceve un pixel* —
        #      lasciata senza una riga sul filo, mentre §2.5 la scriveva per il
        #      canale di input due righe sopra.
        #
        # ⛔⛔ E DAL 13 AGOSTO 2026 LA RIGA SI LEGGE IN DUE PEZZI — proposta
        #     **P20**, e sono due fenomeni diversi sotto la stessa parola.
        #
        #     3a. ⭐ **La certezza**: il client non ha ancora spedito `ATTACCA`.
        #         §4.5 fa di `SESSIONE` la **risposta** ad `ATTACCA` ⇒ il
        #         server non puo' averla spedita, e non serve nessuna ipotesi
        #         sull'ordine di consegna.  Qui si chiude, ed e' I3.
        #     3b. ⛔ **L'indecidibile**: `ATTACCA` e' partito e i byte di
        #         `SESSIONE` non sono ancora arrivati.  §2.5 alla lettera fa
        #         chiudere; ⚠ ma il fotogramma e il canale di controllo sono
        #         **due stream QUIC indipendenti** e niente ne ordina la
        #         consegna — basta perdere il pacchetto che porta `SESSIONE`.
        #         ⇒ Oggi il caso esce `AMBIGUO` con la cura accanto: e' del
        #         coordinatore, non di questo banco.
        if not self.c.attacca_spedito and self.chiude_prima_di_attacca:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §2.5",
                "un fotogramma prima di `SESSIONE`: §2.5 vieta al server di "
                "aprire uno stream video prima di averla spedita — e' "
                "l'invariante I3 sul filo, chi non passa dal validatore non "
                "riceve un pixel",
                scostamento=0))
        if not self.c.sessione_aperta:
            if self.sessione_come_grandezza:
                # ⛔ La lettura di OGGI, alla lettera: si chiude.  E' la
                #    grandezza sostitutiva, ed e' quel che ha fatto il cliente
                #    di prova al suo primo giro dal vivo (`P2-6` §5.2).
                return self._decidi(Verdetto(
                    ERRORE_PROTOCOLLO, "RCP.md §2.5",
                    "un fotogramma prima di `SESSIONE`: §2.5 vieta al server "
                    "di aprire uno stream video prima di averla spedita",
                    scostamento=0))
            return self._decidi(Verdetto(
                AMBIGUO, "RCP.md §2.5",
                "`ATTACCA` e' partito e i byte di `SESSIONE` non sono ancora "
                "arrivati: §2.5 alla lettera fa chiudere, ⛔ ma la misura e' "
                "presa sull'ordine di consegna di **due stream QUIC "
                "indipendenti** — il server puo' aver fatto tutto quel che "
                "§2.5 e §5.2 gli impongono e il pacchetto di `SESSIONE` "
                "essersi perso.  ⇒ Chi applica la riga alla lettera chiude "
                "una sessione in cui nessuno ha sbagliato",
                scostamento=0, propone="P20"))

        # 4. ⛔ IL TIPO — §6.2: «Altri valori: ERRORE_PROTOCOLLO».
        if tipo not in self.tipi_leciti:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"tipo {tipo:#06x}: RCP/1 ne definisce due, {CHIAVE:#06x} "
                f"chiave e {DELTA:#06x} delta", scostamento=0))

        # 5. ⛔ IL CODEC — §6.2: «DEVE essere quello negoziato in §4.3».
        if codec not in CODEC:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"codec {codec}: RCP/1 ne definisce due, 1 = HEVC e 2 = AV1",
                scostamento=2))
        if codec != self.c.codec_negoziato:
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §6.2",
                f"codec {codec} = {CODEC[codec]}, ma in §4.3 si era negoziato "
                f"{self.c.codec_negoziato} = {CODEC[self.c.codec_negoziato]}",
                scostamento=2))

        # 6. ⭐⛔ IL `numero` ZERO — l'ambiguita' A2, ed e' una CONTRADDIZIONE
        #    interna, non una lacuna.
        #
        #    §6.2: `numero` e' «contatore dei fotogrammi catturati, che cresce
        #    di uno per ogni fotogramma che il server decide di spedire» — e
        #    **non dice da quanto parte**.
        #    §7.1: `RICHIEDI_CHIAVE.ultimo_numero` e' «l'ultimo fotogramma
        #    decodificato, **0 se nessuno**».
        #    §6.0: «⛔ Ogni intero ha un solo significato di *assente*, e va
        #    dichiarato dove serve: **non esistono valori sentinella
        #    impliciti**».
        #    ⇒ Se il primo fotogramma porta `numero = 0`, `RICHIEDI_CHIAVE(0)`
        #      vuol dire tutt'e due le cose, e il server non puo' sapere quale.
        #    ⭐ Chiusa il 12 agosto 2026: §6.2 porta adesso *«il primo
        #      fotogramma di una sessione porta `numero = 1`, e lo 0 e'
        #      riservato»*, che e' la stessa convenzione dell'`id` dell'input
        #      (§7.3).
        if num == 0:
            return self._chiuso_il_12_agosto(
                "P2", 12, "RCP.md §6.2",
                "`numero = 0`: §6.2 riserva lo zero — «il primo fotogramma di "
                "una sessione porta `numero = 1`», e «al giro del contatore lo "
                "0 si salta» — perche' lo 0 vuol dire «nessun fotogramma», il "
                "significato che §7.1 gli da' in `RICHIEDI_CHIAVE`",
                "RCP.md §6.2 contro §7.1, per §6.0",
                "`numero = 0`: §7.1 usa lo zero come «nessuno» in "
                "`RICHIEDI_CHIAVE`, §6.2 non dice da dove parte il contatore, "
                "e §6.0 vieta i sentinella impliciti")

        # 7. ⭐⛔⛔ **L'ORDINE, E VIENE PRIMA DELLA MISURA** — §6.2, cura di
        #    **P14**, 12 agosto 2026: *«la regola dell'ordine si applica PRIMA
        #    di quella della misura: un fotogramma il cui `numero` e' precedente
        #    all'ultimo gia' consegnato si scarta, e la sua misura non si
        #    guarda nemmeno»*.
        #
        #    ⛔ **E la precedenza non e' un dettaglio di ordine del codice: e' la
        #    riga che tiene in piedi le altre tre.**  Senza, le due righe di
        #    questa stessa sezione si contraddicono e vince la piu' severa su
        #    una scena in cui nessuno ha sbagliato: la chiave che chiude la
        #    tolleranza **scavalca** i fotogrammi in volo — non per caso, ma
        #    perche' quello vecchio e' **il piu' grosso** (§5.2 vieta di
        #    abbandonare una chiave) e quello nuovo e' piu' piccolo.
        #    ⚠ Fino a questa cura il giudizio della misura stava qui sopra, e
        #      questo caso usciva `ERRORE_PROTOCOLLO`: la sessione cadeva.
        #
        #    ⚠ Il modulo non e' pedanteria: a 60 fotogrammi al secondo il
        #      contatore gira dopo due anni e due mesi, e una sessione puo'
        #      durare di piu' (§6.2).  Un confronto `<` diretto farebbe
        #      scartare **ogni** fotogramma dopo il giro, per sempre.
        #    ⛔ Col guasto **G11** l'ordine torna DOPO la misura, cioe' il
        #       giudice di un'ora fa: e' la stessa riga, spostata di due passi
        #       nel file, e basta a far cadere una sessione sana.
        if self.ordine_prima:
            fuori = self._ordine(num)
            if fuori is not None:
                return fuori

        # 8. ⭐⛔ P5 — LA MISURA.  Chiusa il 12 agosto 2026, e **corretta lo
        #    stesso giorno** perche' la prima stesura uccideva una sessione sana.
        #
        #    §6.2: *«la misura di QUESTO fotogramma.  ⛔ In RCP/1 DEVONO valere
        #    la **tela in vigore** — quella concessa in `SESSIONE` (§4.5),
        #    **oppure** l'ultima concessa da `TELA` se nel frattempo e' stata
        #    adattata (§7.1) — e chi ne riceve altre chiude con
        #    ERRORE_PROTOCOLLO: il client riscala alla VISTA, non alla tela»*.
        #    ⚠ Fino all'11 agosto la riga diceva *«e' sempre quella della tela,
        #      e il client riscala»* — che **descrive** e non comanda (§0
        #      dichiara normativo solo DEVE / NON DEVE / PUO') — e nessuna riga
        #      diceva che cosa fa chi riceve una misura diversa.
        #    ⛔ E per due ore ha detto «la tela concessa in `SESSIONE`», che
        #      dopo un `ADATTA_TELA` faceva chiudere il client davanti a un
        #      server conforme: le due parole giuste sono **in vigore**.
        #    ⛔ Il confronto e' con la tela CHE SI E' DICHIARATA, mai con un
        #      numero scritto qui: lo tengono onesto i due casi
        #      `misura-uguale-a-una-tela-diversa` e `misura-dopo-adatta-tela`.
        if (lar, alt) != (self.c.tela_larghezza, self.c.tela_altezza):
            # 8-bis. ⭐⛔ **D14 — I FOTOGRAMMI IN VOLO.  ENTRATA IN `RCP.md` LA
            #        SERA DEL 12 AGOSTO 2026**, §6.2 in coda e **sesta
            #        eccezione** di §3.
            #
            #        *«Dopo aver ricevuto un `TELA(ADATTATA)` (§7.1) il client
            #        DEVE accettare per un secondo i fotogrammi la cui misura
            #        vale la tela precedente, dipingendoli riscalati alla vista
            #        e scrivendolo nel registro; passato quel secondo sono
            #        ERRORE_PROTOCOLLO, e lo e' subito una misura che non e' ne'
            #        quella in vigore ne' la precedente.»*
            #        ⚠ Fino a quella sera era la proposta **P8** e qui usciva
            #          `AMBIGUO`: §6.2 faceva chiudere il client davanti a un
            #          fotogramma aperto **prima** che l'`ADATTA_TELA` arrivasse
            #          al server — e §5.2 vieta al server di sgombrare il tubo,
            #          perche' una **chiave** non si abbandona.
            # ⭐⛔ **P11 — LA FINESTRA, NON «LA PRECEDENTE».**  §6.2, corretta
            #    la sera del 12 agosto 2026: *«i fotogrammi la cui misura vale
            #    **una tela che e' stata in vigore da quando la coda ha
            #    cominciato a svuotarsi**»*, e `ERRORE_PROTOCOLLO` **subito**
            #    per una misura «che non e' mai stata in vigore in quella
            #    finestra».
            #    ⚠ Diceva «la tela precedente», al singolare, e chi trascina
            #      una finestra ne manda due: 1920x1080 -> `TELA(1600,900)` ->
            #      `TELA(1280,720)`, e la **chiave** aperta prima di tutto — la
            #      piu' grossa, la piu' lenta, e quella che §5.2 vieta al server
            #      di abbandonare — portava una misura che non era ne' quella in
            #      vigore ne' la precedente.  ⛔ La sessione sana cadeva lo
            #      stesso, **un passo piu' in la'** della scena che la cura
            #      aveva appena chiuso.
            # ⛔ Col guasto **G8** la finestra torna a essere «la precedente»
            #    sola, cioe' la riga di due ore fa.
            finestra = (self.c.tele_recenti if self.finestra_di_6_2
                        else self.c.tele_recenti[:1])
            # ⭐⛔ **P13 — LA TOLLERANZA FINISCE SULLA CHIAVE, NON A OROLOGIO.**
            #    §6.2: *«la tolleranza non finisce a orologio: finisce quando
            #    arriva la prima chiave alla misura nuova»*.  ⇒ La condizione e'
            #    `coda_da_svuotare()`, e **non** guarda `secondo_passato`: quel
            #    campo esiste solo perche' il guasto **G10** — «il giudice con
            #    l'orologio», la riga di due ore fa — lo rimetta a decidere e si
            #    veda cadere la sessione sulla linea lenta.
            coda = self.c.coda_da_svuotare()
            if not self.orologio_tolto and self.c.secondo_passato:
                coda = False
            if (coda and self.grazia_di_6_2 and (lar, alt) in finestra):
                # ⛔ NON si decide qui: si segna la tolleranza e si prosegue.
                #    Un fotogramma in volo resta soggetto all'ordine dei
                #    `numero`, al tetto e al FIN.
                self.misura_tollerata = (lar, alt)
                # ⭐⛔ **P10 — E QUI SI GUARDA DOV'E' IL DECODIFICATORE.**
                #
                #    §5.2, riga entrata la sera del 12 agosto: *«il client
                #    riconfigura il decodificatore sulla prima CHIAVE alla
                #    misura nuova, non sul `TELA`»*, e la riga del client dice
                #    adesso *«ne' quella tollerata da §6.2»*.  ⇒ Il fotogramma
                #    si consegna comunque — le due righe non comandano piu' il
                #    contrario — ⛔ ma un client che avesse riconfigurato sul
                #    `TELA` e' **fuori da §5.2**, e il banco lo dice invece di
                #    lasciarlo passare: `[M]` un decodificatore alla misura
                #    nuova che riceve la vecchia non solleva errori e **dipinge
                #    un'immagine sfasciata** (Chrome, HEVC, 12 agosto 2026).
                #    ⚠ Il rilievo NON e' l'esito: l'esito parla del filo, dove
                #      nessuno ha sbagliato; il rilievo parla dello **stato del
                #      client**, che si dichiara da fuori perche' sul filo non
                #      c'e'.
                if (self.rilievo_di_5_2
                        and self.c.decodificatore_a is not None
                        and self.c.decodificatore_a != (lar, alt)):
                    self.rilievo_cliente = (
                        f"⛔ il decodificatore e' configurato a "
                        f"{self.c.decodificatore_a[0]}x"
                        f"{self.c.decodificatore_a[1]} mentre arriva un "
                        f"fotogramma {lar}x{alt} tollerato da §6.2: chi lo ha "
                        f"riconfigurato sul `TELA` ha fatto quel che §5.2 "
                        f"vieta — si riconfigura sulla prima CHIAVE alla "
                        f"misura nuova.  `[M]` cosi' configurato il "
                        f"decodificatore dipinge un'immagine sfasciata senza "
                        f"sollevare un errore")
            # 8-quater. ⭐⛔⛔ **P21 — LE DUE RIGHE DI §6.2 COMANDANO IL
            #           CONTRARIO SULLO STESSO FOTOGRAMMA**, e a otto righe di
            #           distanza.  Proposta aperta il 13 agosto 2026.
            #
            #           §6.2, paragrafo di **P19**: un fotogramma alla misura
            #           **nuova** puo' arrivare **prima** del `TELA` che la
            #           concede, e il client ⛔ **NON DEVE chiudere: trattiene**.
            #           §6.2, paragrafo della tolleranza (**P11** + **P13**),
            #           otto righe sotto: una misura *«che non e' mai stata in
            #           vigore in quella finestra»* e' `ERRORE_PROTOCOLLO`
            #           ⛔ **subito**.
            #           ⇒ Sulla scena `SESSIONE` 1920x1080 -> `TELA(1600,900)`
            #             -> `ADATTA_TELA(1280,720)` senza risposta, col
            #             fotogramma 1280x720 che arriva prima del `TELA`, le
            #             due righe danno **due byte diversi**: `CONGEDO` da una
            #             parte, niente dall'altra.  E' la forma di **P10** —
            #             ⛔ ma li' erano due sezioni, qui e' **la stessa**.
            #
            #     ⭐ Il discriminante che questo banco propone e' quel che
            #        **il client ha spedito lui**, cioe' la stessa grandezza di
            #        P20 e la forma generale del `numero` di P14: locale,
            #        monotona, indipendente dalla consegna.  ⛔ E NON e' «la
            #        misura che il client ha nominato» — vedi `adatta_in_volo` e
            #        il guasto G14: §4.5 permette al server di concedere una
            #        tela **diversa da quella chiesta**, e il discriminante
            #        scritto sui numeri ucciderebbe la sessione sana un passo
            #        piu' in la'.
            #     ⛔ E qui non si cura niente: `RCP.md` e' del coordinatore.
            #        Finche' il documento porta le due righe, l'esito onesto e'
            #        `AMBIGUO` — due implementazioni conformi divergono.
            in_volo = (self.p21_trattiene_sempre
                       or ((lar, alt) in self.c.adatta_in_volo
                           if self.p21_sulla_misura
                           else bool(self.c.adatta_in_volo)))
            if self.misura_tollerata is None and in_volo:
                return self._decidi(Verdetto(
                    AMBIGUO, "RCP.md §6.2",
                    f"il fotogramma e' {lar}x{alt}, la tela in vigore e' "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza} e quella "
                    f"misura non e' mai stata in vigore in questa finestra — "
                    f"⛔ ma il client ha {len(self.c.adatta_in_volo)} "
                    f"`ADATTA_TELA` spedita e senza risposta: §6.2 dice "
                    f"«trattiene» nel paragrafo dei fotogrammi in volo e "
                    f"`ERRORE_PROTOCOLLO` **subito** otto righe sotto.  Due "
                    f"implementazioni conformi, due byte diversi",
                    scostamento=4, propone="P21"))
            if self.misura_tollerata is None:
                return self._chiuso_il_12_agosto(
                    "P5", 4, "RCP.md §6.2",
                    f"il fotogramma e' {lar}x{alt} e la tela IN VIGORE e' "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza}, da "
                    f"{self.c.tela_da}: §6.2 vuole che DEVANO coincidere",
                    "RCP.md §6.2",
                    f"il fotogramma e' {lar}x{alt} e la tela concessa e' "
                    f"{self.c.tela_larghezza}x{self.c.tela_altezza}: «e' sempre "
                    f"quella della tela» non dice che cosa fa chi riceve")

        # 8-ter. ⛔ E col guasto **G11** l'ordine si guarda QUI, dopo la
        #        misura: il fotogramma in volo scavalcato dalla chiave e' gia'
        #        caduto due passi piu' su, e la sessione con lui.
        if not self.ordine_prima:
            fuori = self._ordine(num)
            if fuori is not None:
                return fuori

        # 9. ⭐⛔ P6 — IL PRIMO FOTOGRAMMA E' UN DELTA.  Chiusa il 12 agosto
        #    2026, ed e' la riga che morde in QUESTA fase.
        #
        #    §5.2, primo punto delle «Le regole:»: *«⛔ il primo fotogramma che
        #    il server spedisce dopo `SESSIONE` DEVE essere una chiave
        #    (`0x0301`)»*.
        #    ⚠ Fino all'11 agosto un delta in apertura era **conforme a ogni
        #      riga del documento**, e la fase 2 — che consegna un fotogramma
        #      fermo — avrebbe mostrato spazzatura senza che nessuno avesse
        #      torto.  ⛔ E il client non aveva modo di accorgersene: §5.2 gli
        #      fa chiedere una chiave su un **buco** nei `numero`, e qui buchi
        #      non ce ne sono (e' il primo); e §5.2 stesso dichiara `[S]` che a
        #      un delta mancante il decodificatore **non solleva nessun errore**.
        if tipo == DELTA and not self.c.chiave_consegnata:
            return self._chiuso_il_12_agosto(
                "P6", 0, "RCP.md §5.2",
                "il primo fotogramma della sessione e' un DELTA: §5.2 vuole "
                "che il primo fotogramma dopo `SESSIONE` sia una chiave "
                "(0x0301)",
                "RCP.md §5.2",
                "il primo fotogramma della sessione e' un DELTA: nessuna riga "
                "obbliga il server a cominciare con una chiave, e il client "
                "non ha nessun buco da cui accorgersene")

        # 10. ⭐⛔ **P9 — IL PRIMO FOTOGRAMMA ALLA MISURA NUOVA.  Entrata in
        #     `RCP.md` §5.2 la sera del 12 agosto 2026, difetto D13.**
        #
        #     *«E lo stesso vale a ogni cambio di tela: il primo fotogramma
        #     spedito alla misura nuova, dopo un `TELA(ADATTATA…)` (§7.1), DEVE
        #     essere una chiave (`0x0301`) — e DEVE essere una chiave vera,
        #     cioe' portare con se' tutto quel che serve a decodificarla da
        #     sola: per HEVC i suoi VPS/SPS/PPS davanti all'IDR.»*
        #     ⛔ E la riga non e' prudenza: `[M]` 12 agosto 2026, banco
        #     `02-pagina-tela-*` — con soli delta alla misura nuova **Chrome su
        #     HEVC emette cinque fotogrammi, tutti dichiarati alla misura
        #     VECCHIA, dipinti, e zero errori**.  Il sintomo e' «il desktop si
        #     strappa quando ridimensiono la finestra», e non nomina ne' il
        #     protocollo ne' la tela.
        #
        #     ⚠ **E QUI IL BANCO GIUDICA MENO DI QUEL CHE LA RIGA DICE**, e va
        #       scritto invece che scoperto: questo giudice **non conserva i
        #       dati** del fotogramma (vedi la classe), quindi vede che il
        #       primo alla misura nuova e' `0x0301` e ⛔ **non puo' vedere se
        #       porta davvero i suoi VPS/SPS/PPS davanti all'IDR** — la meta'
        #       «chiave *vera*» resta al banco della codifica
        #       (`02-codifica-nal.py`) e alla pagina (`02-pagina-tela-*`).
        #     ⚠ `[?]` **E una domanda che questa riga apre e non chiude**:
        #       §6.2 dice che i fotogrammi arrivano **fuori ordine**, quindi un
        #       delta alla misura nuova puo' arrivare **prima** della chiave che
        #       il server ha spedito per prima.  La riga vincola chi **spedisce**
        #       e questo giudice la applica a chi **riceve**: e' la lettura
        #       severa, ed e' la stessa che P6 ha da stamattina.  Un buco nei
        #       `numero` distingue i due casi, e nessuna riga dice di guardarlo.
        if (self.chiave_di_5_2
                and self.c.tela_da.startswith("TELA")
                and not self.c.chiave_alla_tela_nuova
                and self.misura_tollerata is None
                and tipo == DELTA):
            return self._decidi(Verdetto(
                ERRORE_PROTOCOLLO, "RCP.md §5.2",
                f"il primo fotogramma alla misura NUOVA ({lar}x{alt}, da un "
                f"`TELA(ADATTATA)`) e' un DELTA: §5.2 vuole una chiave "
                f"({CHIAVE:#06x}) a ogni cambio di tela, e vera — coi suoi "
                f"parameter set.  Senza, `[M]` Chrome su HEVC dipinge cinque "
                f"fotogrammi alla misura vecchia senza sollevare un errore",
                scostamento=0))

    def _ordine(self, num):
        """⛔ §6.2 — si scarta un `numero` **precedente** all'ultimo gia'
           consegnato, con l'aritmetica modulo 2^32 e le differenze con segno.

        ⚠ Sta in un metodo suo perche' il guasto **G11** lo deve poter
          spostare **dopo** la misura senza che la riga cambi di una virgola:
          quel che P14 ha curato non e' il testo della regola, e' **il posto in
          cui si applica** — e un guasto che riscrivesse anche il testo
          dimostrerebbe un'altra cosa.
        """
        if self.c.ultimo_consegnato is None:
            return None
        d = (num - self.c.ultimo_consegnato) & 0xFFFFFFFF
        if d >= 0x80000000 or d == 0:
            return self._decidi(Verdetto(
                SCARTATO, "RCP.md §6.2",
                f"`numero` {num} non e' successivo a "
                f"{self.c.ultimo_consegnato} (differenza con segno "
                f"{d - 0x100000000 if d >= 0x80000000 else d}): si scarta, "
                f"e ⛔ **la misura non si guarda nemmeno** — gli stream sono "
                f"indipendenti e i fotogrammi arrivano fuori ordine",
                scostamento=12))
        return None

    def _giudica_completo(self):
        """Lo stream e' finito con FIN e l'intestazione era buona."""
        num = self.campi["numero"]
        # ⛔ IL BUCO — §5.2: «il client DEVE mandare `RICHIEDI_CHIAVE` quando si
        #    accorge di un buco nella successione dei `numero`».  ⚠ E il buco
        #    e' **normale**: §6.2 dice che il contatore cresce anche per i
        #    fotogrammi che il server poi abbandona.
        if (self.c.ultimo_consegnato is not None
                and num != ((self.c.ultimo_consegnato + 1) & 0xFFFFFFFF)):
            self.c.chiedi_chiave = True
        self.c.ultimo_consegnato = num
        if self.campi["tipo"] == CHIAVE:
            self.c.chiave_consegnata = True
            self.c.chiedi_chiave = False
            # ⛔ P9 — e la chiave vale per la tela nuova **solo se la porta**:
            #    una chiave in volo alla misura vecchia non paga il debito che
            #    §5.2 apre a ogni `TELA(ADATTATA)`.
            # ⭐⛔ E P13: questa **e' anche la fine della tolleranza**.  §6.2:
            #    *«finisce quando arriva la prima chiave alla misura nuova»* ⇒
            #    da qui in poi una misura vecchia e' `ERRORE_PROTOCOLLO`, e non
            #    e' un orologio a dirlo ma un fotogramma che si e' visto.
            if self.misura_tollerata is None:
                self.c.arriva_la_chiave_nuova()
        se = (f"{'chiave' if self.campi['tipo'] == CHIAVE else 'delta'} "
              f"n. {num}, {self.campi['larghezza']}x{self.campi['altezza']}, "
              f"{self.byte_dati} byte di dati")
        if self.misura_tollerata is not None:
            # ⛔ §3, ultima riga: la tolleranza SI SCRIVE NEL REGISTRO.  Una
            #    tolleranza silenziosa e' indistinguibile da un difetto.
            return Verdetto(
                ACCETTATO, "RCP.md §6.2",
                f"{se} — ⚠ TOLLERATO: porta la tela **precedente** e il "
                f"`TELA(ADATTATA)` e' appena passato, quindi era gia' in volo. "
                f"Si dipinge **riscalato alla vista** ed e' la sesta eccezione "
                f"di §3, che va scritta nel registro",
                tollerato=(f"tela {self.misura_tollerata[0]}x"
                           f"{self.misura_tollerata[1]}, in vigore dentro il "
                           f"secondo appena passato (§6.2, §3 eccezione 6)"),
                rilievo=self.rilievo_cliente)
        return Verdetto(ACCETTATO, "RCP.md §6.2", se)


# ---------------------------------------------------------------------------
def intestazione(tipo=CHIAVE, codec=1, lar=1920, alt=1080, num=1, ist=0, inp=0):
    """I 28 byte di §6.2, in ordine di rete e senza un byte di riempimento."""
    return struct.pack("!HHIIIQI", tipo, codec, lar, alt, num, ist, inp)


# ===========================================================================
# ⛔ LE RIGHE ENTRATE IN `RCP.md` IL 12 AGOSTO 2026, E I DUE CASI DI OGNUNA.
#    ⚠ Sei di mattina (P1-P6) e **due di sera** (P8 da D14, P9 da D13): il
#      conto non si scrive qui, lo calcola `regole_coperte()`.
#
#    ⚠ Fino all'11 agosto questa tabella si chiamava `PROPOSTE` ed era un
#      elenco di cose **da chiedere** al coordinatore.  Adesso le righe sono
#      **normative** — stanno in `RCP.md` §2.5, §5.2, §6.2 — e questa tabella
#      dice due cose che un elenco di proposte non diceva:
#
#      ⛔ **dove sta la riga**, per andarla a rileggere invece di fidarsi;
#      ⛔ **quale caso la viola e quale la rispetta**, per nome.
#
#    ⭐ E i due nomi non sono documentazione: `regole_coperte()` li **cerca**
#       fra i casi e il giro stampa il conto.  Una regola che perdesse uno dei
#       due casi — o che ne citasse uno rinominato — diventa rossa qui, e non
#       fra sei mesi quando qualcuno se ne accorge.
REGOLE_NUOVE = {
    "P1": {
        "dove": "RCP.md §2.5, riga «video» della tabella",
        "dice": "Il server NON DEVE aprire uno stream video prima di aver "
                "spedito `SESSIONE`; chi ne riceve uno prima chiude con "
                "`ERRORE_PROTOCOLLO`.",
        "era": "derivata da §1 + §3 per chi riceve, e da NIENTE per chi manda",
        "viola": "prima-di-sessione",
        "rispetta": "dopo-sessione",
    },
    "P2": {
        "dove": "RCP.md §6.2, campo `numero`",
        "dice": "Il primo fotogramma di una sessione porta `numero = 1`; ⛔ **0 "
                "e' riservato** e vuol dire «nessun fotogramma», che e' il "
                "significato che §7.1 gli da' in `RICHIEDI_CHIAVE`.  ⛔ E al "
                "giro del contatore lo 0 **si salta**: da `0xFFFFFFFF` si "
                "passa a `1`.",
        "era": "lettura doppia — §6.2 non diceva da dove parte il contatore; e "
               "la cura stessa e' durata due ore prima che si vedesse che al "
               "giro del contatore lo `0` riservato tornava in circolo da solo",
        "viola": "numero-zero",
        "rispetta": "numero-uno",
    },
    "P3": {
        "dove": "RCP.md §2.5, riga `0x03` della tabella dei canali",
        "dice": "Il video vive **solo** su uno stream unidirezionale aperto dal "
                "server: un `0x03` sul canale di controllo e' "
                "`ERRORE_PROTOCOLLO`.",
        "era": "lettura doppia — §2.5 chiudeva il caso per 0x00 e 0x04 e non "
               "per il video",
        "viola": "video-sul-controllo",
        "rispetta": "video-su-unidirezionale",
    },
    "P4": {
        "dove": "RCP.md §6.2, terza riga di «La regola, in due righe»",
        "dice": "Uno stream video chiuso con **FIN prima dei 28 byte** "
                "dell'intestazione e' `ERRORE_PROTOCOLLO`: non e' un "
                "fotogramma corto, e' una lunghezza che non torna (§3).",
        "era": "derivata da §3, e §6.2 — dove chi implementa la guarda — taceva",
        "viola": "intestazione-27-byte",
        "rispetta": "chiave-senza-dati",
    },
    "P5": {
        "dove": "RCP.md §6.2, campi `largh.` e `altezza`",
        "dice": "In RCP/1 `largh.` e `altezza` **DEVONO** valere la **tela in "
                "vigore** — quella di `SESSIONE` (§4.5), oppure l'ultima "
                "concessa da `TELA` se e' stata adattata (§7.1); chi riceve "
                "una misura diversa chiude con `ERRORE_PROTOCOLLO`.",
        "era": "lettura doppia — «e' sempre quella della tela» descrive e non "
               "comanda, e nessuna riga diceva che cosa fa chi riceve.  ⛔ E "
               "per due ore la cura stessa e' stata sbagliata: diceva «la tela "
               "concessa in `SESSIONE`», che dopo un `ADATTA_TELA` uccide una "
               "sessione sana.  Corretta il 12 agosto 2026: «la tela IN VIGORE»",
        "viola": "misura-diversa-dalla-tela",
        "rispetta": "misura-dopo-adatta-tela",
    },
    "P6": {
        "dove": "RCP.md §5.2, primo punto delle «Le regole:»",
        "dice": "Il primo fotogramma che il server spedisce dopo `SESSIONE` "
                "**DEVE** essere una chiave (`0x0301`).",
        "era": "lettura doppia — un delta in apertura era conforme a ogni riga, "
               "e il client non aveva modo di accorgersene",
        "viola": "primo-fotogramma-delta",
        "rispetta": "primo-fotogramma-chiave",
    },
    # ── ⭐⛔ E LE DUE ENTRATE LA **SERA** DEL 12 AGOSTO, DA D13 E D14 ─────────
    #    ⚠ Fino a quella sera stavano nella tabella `PROPOSTE_APERTE` qui
    #      sotto, e i loro casi uscivano `AMBIGUO`.  ⛔ Il giorno in cui una
    #      proposta diventa una riga, i suoi casi cambiano **atteso**: lasciarli
    #      dov'erano vorrebbe dire giudicare il documento di ieri, che e' quel
    #      che il guasto **G5** esiste per far vedere.
    "P8": {
        "dove": "RCP.md §6.2, in coda («Il cambio di tela e i fotogrammi in "
                "volo»), e §3 eccezione 6",
        "dice": "Dopo un `TELA(ADATTATA)` il client **DEVE** accettare per **un "
                "secondo** i fotogrammi che portano la misura **precedente**, "
                "dipingendoli riscalati alla vista e **scrivendolo nel "
                "registro**; fuori dal secondo sono `ERRORE_PROTOCOLLO`, e lo "
                "e' **subito** una misura che non e' ne' quella in vigore ne' "
                "la precedente.",
        "era": "⛔ **contraddizione interna** — non una lettura doppia: §6.2 "
               "faceva chiudere chi riceve una misura diversa dalla tela in "
               "vigore, e §6.2 stesso dice che i fotogrammi arrivano fuori "
               "ordine.  Due implementazioni conformi producevano lo **stesso** "
               "byte — la chiusura — e uccidevano una sessione sana",
        # ⛔ DUE casi la violano, e servono tutt'e due: uno tiene la grazia
        #    dentro **il secondo**, l'altro dentro **una misura**.  Una grazia
        #    scritta troppo larga e' un difetto quanto una regola troppo
        #    stretta, ed e' cosi' che P5 e' finita sbagliata stamattina.
        "viola": ("p13-vecchia-dopo-la-chiave-nuova",
                  "p8-misura-di-nessuna-tela"),
        "rispetta": "p8-in-volo-dopo-adatta-tela",
    },
    "P9": {
        "dove": "RCP.md §5.2, secondo punto delle «Le regole:»",
        "dice": "Il primo fotogramma spedito alla **misura nuova**, dopo un "
                "`TELA(ADATTATA…)`, **DEVE** essere una chiave (`0x0301`) — e "
                "una chiave **vera**, coi suoi VPS/SPS/PPS davanti all'IDR.  ⛔ "
                "E il client **NON DEVE** consegnare al decodificatore un "
                "fotogramma la cui misura non e' quella per cui il "
                "decodificatore e' configurato.",
        "era": "⛔ **difetto D13, `[M]`**: con soli delta alla misura nuova "
               "Chrome su HEVC emette 5 fotogrammi, tutti dichiarati alla "
               "misura VECCHIA, li dipinge e non solleva **nessun** errore — "
               "mentre AV1 protesta in tutt'e quattro le caselle.  La regola "
               "serve perche' sul codec principale il sintomo e' **muto**",
        "viola": "d13-delta-alla-misura-nuova",
        "rispetta": "d13-chiave-alla-misura-nuova",
    },
    "P11": {
        "dove": "RCP.md §6.2, in coda — la finestra al posto del singolare",
        "dice": "La grazia copre i fotogrammi la cui misura vale **una tela "
                "che e' stata in vigore entro il secondo appena passato**; ⛔ e "
                "`ERRORE_PROTOCOLLO` **subito** e' per una misura che in quella "
                "finestra **non e' mai stata in vigore**.",
        "era": "⛔ la cura di D14 nominava «la tela **precedente**», al "
               "singolare, ⚠ e chi trascina una finestra ne manda due: "
               "1920x1080 -> `TELA(1600,900)` -> `TELA(1280,720)`, e la chiave "
               "aperta prima di tutto — la piu' grossa, la piu' lenta, e quella "
               "che §5.2 vieta al server di abbandonare — cadeva lo stesso.  "
               "**Un passo piu' in la' della scena che la cura aveva appena "
               "chiuso**",
        "viola": "p11-misura-mai-in-vigore",
        "rispetta": "p11-due-tele-nella-finestra",
    },
    "P13": {
        "dove": "RCP.md §6.2, in coda — e §3, riga 6, che dice la stessa cosa",
        "dice": "La tolleranza **non finisce a orologio: finisce quando arriva "
                "la prima chiave alla misura nuova** (§5.2).  Da quel "
                "fotogramma in poi una misura vecchia e' `ERRORE_PROTOCOLLO`.",
        "era": "⛔ diceva «per **un secondo**», e il secondo era la grandezza "
               "sbagliata: quel che deve svuotarsi e' una **coda**, e quanto ci "
               "mette un fotogramma gia' in volo dipende dalla **banda**.  Una "
               "chiave 1920x1080 di qualche MiB su una linea cattiva — che e' "
               "**dentro** il modello, il minimo e' 480p a 25 — arriva **dopo** "
               "il secondo, e il client chiudeva un fotogramma spedito quando "
               "era legale e che §5.2 vietava di abbandonare.  ⛔ Non era solo "
               "una sessione sana che cadeva: era l'invariante **I1** («mai a "
               "staccare») rotta **perche' la linea e' lenta**, cioe' nella "
               "condizione esatta che I1 esiste per proteggere.  ⭐ E allungare "
               "il secondo avrebbe **spostato** il difetto invece di toglierlo",
        "viola": "p13-vecchia-dopo-la-chiave-nuova",
        "rispetta": "p13-linea-lenta",
    },
    "P14": {
        "dove": "RCP.md §6.2, subito prima del riquadro sui fotogrammi in volo",
        "dice": "⛔ **La regola dell'ordine si applica PRIMA di quella della "
                "misura**: un fotogramma il cui `numero` e' precedente "
                "all'ultimo gia' consegnato **si scarta**, e la sua misura non "
                "si guarda nemmeno.",
        "era": "⛔ due righe della **stessa sezione** che si contraddicevano, e "
               "vinceva la piu' severa su una scena in cui nessuno aveva "
               "sbagliato: la chiave che chiude la tolleranza **scavalca** i "
               "fotogrammi in volo — non per caso, ma perche' quello vecchio e' "
               "il piu' grosso (§5.2 vieta di abbandonarlo) e quello nuovo e' "
               "piu' piccolo.  ⚠ Quarta volta che la stessa famiglia si sposta "
               "di un passo: **P8 -> P11 -> P13 -> P14**",
        # ⛔ E QUI LA COPPIA NON E' «chiude / accetta», ed e' il punto della
        #    riga: e' «si scarta / si chiude davvero».  ⚠ Senza la seconda, la
        #    precedenza nuova diventa un **buco che ingoia anche i casi veri** —
        #    un fotogramma alla misura sbagliata passerebbe per «arrivato
        #    tardi» e la regola della misura non morderebbe piu' niente.
        "viola": "p13-vecchia-dopo-la-chiave-nuova",
        "rispetta": "p14-in-volo-scavalcato-dalla-chiave",
        "esito_viola": ERRORE_PROTOCOLLO,
        "esito_rispetta": SCARTATO,
        "etichetta_viola": "la tiene STRETTA (ordine a posto, misura sbagliata "
                           "-> si chiude davvero)",
        "etichetta_rispetta": "la ESERCITA (numero precedente -> si scarta)",
    },
}


# ===========================================================================
# ⛔ E UNA RIGA CHE NON PARLA DEL FILO MA DELLO **STATO DEL CLIENT** — P10.
#
#    §5.2: *«il client riconfigura il decodificatore sulla prima CHIAVE alla
#    misura nuova, non sul `TELA`»*.  ⛔ Quella misura **non e' sul filo**: un
#    arbitro che legge i byte non la puo' vedere, e questo banco la fa
#    **dichiarare** dal caso (`decodificatore_a`).
#
#    ⚠ Sta in una tabella sua e non fra le regole qui sopra per una ragione
#      sola, ed e' la stessa che tiene separati `SCARTATO` e
#      `ERRORE_PROTOCOLLO`: la coppia ha una **forma diversa**.  Una regola del
#      filo ha un caso che esce `ERRORE_PROTOCOLLO` e uno che esce `ACCETTATO`;
#      qui escono `ACCETTATO` tutt'e due — sul filo nessuno ha sbagliato — e a
#      cambiare e' il **rilievo sul client**, che c'e' in uno e non nell'altro.
#      ⛔ Metterle insieme vorrebbe dire pretendere che un difetto del client
#      faccia cadere la sessione, cioe' l'errore che questo capitolo ha gia'
#      pagato tre volte in un giorno.
REGOLE_DI_STATO = {
    "P10": {
        "dove": "RCP.md §5.2, la riga prima di quella del client",
        "dice": "Il client **riconfigura il decodificatore sulla prima CHIAVE "
                "alla misura nuova, non sul `TELA`** — e non consegna al "
                "decodificatore un fotogramma di misura diversa da quella per "
                "cui e' configurato **ne' quella tollerata da §6.2**.",
        "era": "⛔⛔ **le due cure del 12 agosto si contraddicevano sullo "
               "stesso fotogramma**: §6.2 «accettalo e dipingilo», §5.2 "
               "«buttalo», e il documento non diceva in nessun punto **quando** "
               "il client riconfigura.  Due letture conformi che divergevano "
               "sul filo — una mandava `RICHIEDI_CHIAVE`, l'altra no",
        "viola": "p10-decodificatore-al-tela",
        "rispetta": "p10-decodificatore-alla-chiave",
    },
}


# ===========================================================================
# ⛔⛔ E LE PROPOSTE ANCORA **APERTE** — quel che `RCP.md` NON dice ancora.
#
#    ⚠ Stanno in una tabella **separata** da `REGOLE_NUOVE`, e la separazione e'
#      la cosa piu' importante di questo blocco: la' ci sono righe **normative**
#      che si vanno a rileggere nel documento, qui c'e' una cura che il
#      coordinatore non ha ancora applicato.  ⛔ Mescolarle vorrebbe dire che
#      fra un mese nessuno sa piu' quale delle due un banco sta facendo
#      rispettare — ed e' la forma **E5** («un "fatto" che era una deduzione
#      mai misurata») applicata al documento invece che al codice.
#
#    ⛔ E ogni proposta porta i **suoi** casi con l'atteso di OGGI: quello che
#       la fa vedere, e quelli che impediscono di scriverla troppo larga.
#
# ⭐⛔ **E LA SERA DEL 12 AGOSTO 2026 QUESTA TABELLA SI E' SVUOTATA.**  P8 e P9
#    sono entrate nel documento, e i due punti in cui **non reggevano** — P10 e
#    P11, trovati applicandole — sono entrati nel giro dopo.  ⛔ Resta vuota, e
#    la si dichiara vuota invece di toglierla: il giorno in cui questo banco
#    trovera' il punto seguente, il posto dove scriverlo c'e' gia' — e
#    `proposte_coperte()` continua a contare «0 su 0», che e' un numero, non un
#    silenzio.
#
# ⭐⛔ **E IL 13 AGOSTO 2026 SI E' RIEMPITA DI NUOVO, CON UNA SOLA VOCE: P20.**
#    ⚠ Non l'ha trovata una rilettura: l'ha trovata il **cliente di prova** al
#      suo primo giro contro un server che spedisce davvero (`P2-6` §5.2), e la
#      cura di quel giro ha curato il **banco** — non la riga.
PROPOSTE_APERTE = {
    "P20": {
        "dove": "RCP.md §2.5, riga «video» della tabella",
        "dice":
            "⛔ Il divieto vincola **chi manda**, e chi riceve non lo puo' "
            "misurare: «prima di `SESSIONE`» e' un ordine fra **due stream "
            "QUIC indipendenti**, e RFC 9000 non ne ordina la consegna.  ⭐ La "
            "grandezza vera e' un fatto **locale del client**: se non ha "
            "ancora spedito `ATTACCA`, il server non puo' aver spedito "
            "`SESSIONE` (§4.5 ne fa la risposta) — e questo il client lo sa "
            "senza ipotesi sulla rete, perche' l'`ATTACCA` l'ha spedito lui.",
        "era":
            "⛔ *«uno per fotogramma, e nessuno prima di aver spedito "
            "`SESSIONE`: chi ne riceve uno prima chiude con "
            "`ERRORE_PROTOCOLLO`»* — e **«chi ne riceve uno prima»** e' una "
            "grandezza sostitutiva: chi riceve non ha altro da misurare che "
            "l'ordine in cui il proprio strato di rete gli consegna gli "
            "eventi, e i due stream sono indipendenti.  ⚠ Ed e' la **sesta** "
            "della famiglia P8 -> P11 -> P13 -> P14 -> P19 -> P20 "
            "(`LEZIONI.md` §1.13).  ⛔ Anche la prima cura proposta — *«solo "
            "se, quando il fotogramma arriva, i byte di `SESSIONE` non sono "
            "ancora arrivati»* — resta un sostituto: sposta la misura dal "
            "risveglio della coroutine ai byte, e i byte li ritarda **la "
            "rete** (un pacchetto perso, una ritrasmissione).  ⇒ Sarebbe la "
            "settima stesura, e si sposterebbe di un passo alla prima "
            "rilettura ostile.",
        # ⛔ E il testo pronto da incollare sta qui, non in un rapporto: un
        #    banco che nomina una cura senza portarla e' un reclamo (§«i quattro
        #    esiti»).  ⚠ Non tocca §9: nessun tipo, nessun campo, nessun valore
        #    nuovo — `ATTACCA` e `SESSIONE` ci sono da §4.5.
        "testo":
            "| **video** — unidirezionale | il server | uno **per "
            "fotogramma**, ⛔ e **nessuno prima di aver spedito `SESSIONE`**. "
            "⚠ Il divieto vincola **chi manda**: chi riceve non lo puo' "
            "misurare sull'ordine in cui gli arrivano le cose, perche' il "
            "canale di controllo e lo stream del fotogramma sono **due stream "
            "QUIC indipendenti** e niente ne ordina la consegna (§6.2).  ⇒ Il "
            "client dichiara `ERRORE_PROTOCOLLO` **solo** se non ha ancora "
            "spedito `ATTACCA`: §4.5 fa di `SESSIONE` la risposta ad "
            "`ATTACCA`, quindi li' il server **non puo'** averla spedita, e il "
            "client lo sa senza guardare la rete.  ⛔ Se `ATTACCA` e' partito "
            "e `SESSIONE` non e' ancora arrivata il client **NON DEVE "
            "chiudere**: **trattiene** il fotogramma e lo scrive nel registro, "
            "come per la misura mai in vigore di §6.2, e lo giudica quando "
            "`SESSIONE` arriva — che arriva per forza, perche' il canale di "
            "controllo e' affidabile e ordinato e §4.5 vieta al server di "
            "rispondere con un silenzio.  ⚠ E l'invariante **I3** resta "
            "intera: chi ha spedito `ATTACCA` e' gia' passato da `AMMESSO`, "
            "cioe' dal validatore |",
        "casi": {
            "p20-sessione-in-ritardo": AMBIGUO,
            "p20-prima-di-attacca": ERRORE_PROTOCOLLO,
        },
    },
    # ⭐⛔⛔ E LA **SETTIMA** DELLA FAMIGLIA, TROVATA DALLA RILETTURA OSTILE DEL
    #     13 AGOSTO 2026 rimettendo in fila le sei che ormai convivono:
    #     P8 -> P11 -> P13 -> P14 -> P19 -> P20 -> **P21**.
    #     ⚠ Il 13 agosto e' nata come rilievo **dichiarato e non curato**
    #       (`RILIEVI_DICHIARATI`), senza un caso.  ⛔ Ci e' rimasta un giro
    #       solo: un rilievo che ha una cura, tre casi e un guasto per verso
    #       **non e' piu' un rilievo, e' una proposta** — e la tabella in cui sta
    #       scritto e' meta' di quel che dice.
    "P21": {
        "dove": "RCP.md §6.2 — **due paragrafi della stessa sezione**, a otto "
                "righe di distanza",
        "dice":
            "⛔ Il fotogramma alla misura mai in vigore **si trattiene** finche' "
            "resta una `ADATTA_TELA` che il client ha **spedito lui** e a cui "
            "nessun `TELA` ha ancora risposto; quando quel `TELA` arriva, il "
            "fotogramma si **rigiudica** contro la tela che il `TELA` dichiara. "
            "⛔ E se non c'e' nessuna richiesta in volo non si trattiene "
            "niente: `ERRORE_PROTOCOLLO` **subito**, come §6.2 dice gia'.  "
            "⭐ La grandezza e' **una richiesta in volo**, non **la misura "
            "chiesta**: §4.5 permette una tela concessa diversa da quella "
            "chiesta.",
        "era":
            "⛔ **Contraddizione interna, e i due paragrafi sono nella stessa "
            "sezione**: quello di **P19** dice che un fotogramma alla misura "
            "nuova arrivato **prima** del suo `TELA` non fa chiudere — "
            "*«trattiene»* — e quello della tolleranza (**P11** + **P13**), "
            "otto righe sotto, dice che una misura *«che non e' mai stata in "
            "vigore in quella finestra»* e' `ERRORE_PROTOCOLLO` **subito**.  "
            "⇒ Sulla stessa scena due implementazioni conformi mandano due byte "
            "diversi: una `CONGEDO`, l'altra niente.  ⚠ E' la forma di **P10** "
            "— li' pero' erano §5.2 contro §6.2, **due sezioni**; qui e' §6.2 "
            "con se stessa, ⛔ e la seconda riga e' arrivata **dopo** la prima. "
            "⭐ E si distingue da **D14/P8** in un punto che conta: li' le due "
            "implementazioni **convergevano** sul byte sbagliato e nessun "
            "confronto le poteva smentire, qui **divergono** — questa un "
            "confronto fra due client la trova, e la troverebbe in produzione.  "
            "⛔ E la prima cura proposta era **la misura che il client ha "
            "nominato**, che e' ancora un sostituto: §4.5 dice *«la tela "
            "concessa puo' essere diversa da quella chiesta»* — su KWin < 6.8 "
            "e' la strada normale (`SPECIFICHE.md` §6.3) e la negoziazione "
            "PipeWire di §6.4 concede il modo che il compositore **ha** — e un "
            "client che trattenesse solo i numeri che ha nominato chiuderebbe "
            "la sessione **un passo piu' in la'**, che e' la firma di questa "
            "famiglia da P8 in poi.  ⇒ Sarebbe stata l'ottava stesura.",
        # ⛔ Il testo pronto da incollare, e **non tocca §9**: nessun tipo,
        #    nessun campo, nessun valore nuovo — `ADATTA_TELA` e `TELA` ci sono
        #    da §7.1, e la clausola di §9 e' consumata dal 10 agosto 2026.
        #    ⚠ Sono DUE pezzi, perche' i paragrafi che si contraddicono sono
        #      due: curarne uno solo lascerebbe in piedi la contraddizione, che
        #      e' l'errore che P12 ha gia' fatto pagare (§3 al singolare mentre
        #      §6.2 era passata alla finestra).
        "testo":
            "⛔ **[1] Al posto del paragrafo «Il client NON DEVE chiudere» e "
            "dell'intero riquadro `[?]` «fino a quando trattiene»:**\n"
            "\n"
            "⛔ **Il client NON DEVE chiudere: trattiene il fotogramma**, e lo "
            "scrive nel registro.  ⭐ **E fino a quando lo trattiene non e' un "
            "numero: e' una condizione** — finche' resta una `ADATTA_TELA` che "
            "**il client ha spedito** e a cui nessun `TELA` ha ancora risposto. "
            "Arrivato quel `TELA`, il fotogramma trattenuto **si rigiudica** "
            "contro la tela che quel `TELA` dichiara in vigore, e da li' e' un "
            "fotogramma come tutti gli altri: prima la regola dell'ordine, poi "
            "quella della misura.  ⛔ **E se nessuna `ADATTA_TELA` e' senza "
            "risposta non si trattiene niente**: una misura che il client non "
            "ha nessun motivo di aspettarsi e' `ERRORE_PROTOCOLLO` subito, come "
            "dice il paragrafo della tolleranza qui sotto.\n"
            "\n"
            "⚠ **E il `TELA` arriva per forza**, che e' la ragione per cui "
            "questa e' una fine e non un'attesa aperta: §7.1 impone *«a ogni "
            "`ADATTA_TELA` il server DEVE rispondere con un `TELA`, riuscito o "
            "no»*, e il canale di controllo e' **uno solo, affidabile e "
            "ordinato** (§4.2) ⇒ l'n-esimo `TELA` risponde all'n-esima "
            "`ADATTA_TELA`, e chi trascina una finestra ne manda due senza che "
            "il conto si perda.  ⛔ Un `TELA(RIFIUTATA)` chiude l'attesa quanto "
            "un `TELA(ADATTATA)`: il fotogramma trattenuto si rigiudica contro "
            "la tela rimasta in vigore, e di norma **e' `ERRORE_PROTOCOLLO`** — "
            "il server ha spedito una misura che non ha mai avuto.\n"
            "\n"
            "⭐ **E la grandezza e' «una richiesta in volo», non «la misura che "
            "il client ha chiesto»**: §4.5 dice che *«la tela concessa puo' "
            "essere diversa da quella chiesta»* — su KWin < 6.8 e' la strada "
            "normale (`SPECIFICHE.md` §6.3) e la negoziazione di §6.4 concede "
            "il modo che il compositore **ha**.  ⇒ Un client che trattenesse "
            "solo i numeri che ha nominato chiuderebbe una sessione in cui il "
            "server ha fatto esattamente quel che §7.1 gli permette.  ⚠ E' la "
            "stessa grandezza di **P20** — *quel che il client ha spedito lui*: "
            "locale, monotona, indipendente dalla consegna.\n"
            "\n"
            "⛔ **[2] In coda al paragrafo «Il cambio di tela e i fotogrammi in "
            "volo», al posto di «e lo e' subito una misura che non e' mai stata "
            "in vigore in quella finestra»:**\n"
            "\n"
            "e lo e' **subito** una misura che non e' mai stata in vigore in "
            "quella finestra ⛔ **e che nessuna `ADATTA_TELA` senza risposta "
            "puo' ancora concedere**: se una c'e', il fotogramma **si "
            "trattiene** invece di far chiudere (il paragrafo qui sopra).",
        "casi": {
            "p21-nominata-e-in-volo": AMBIGUO,
            "p21-concessa-diversa-da-chiesta": AMBIGUO,
            "p11-misura-mai-in-vigore": ERRORE_PROTOCOLLO,
        },
    },
}

# ⭐ E LE DUE CHE QUESTA TABELLA HA OSPITATO PER UN GIRO SOLO, con la data:
#    **P10** e **P11**, nate `AMBIGUO` la sera del 12 agosto 2026 e diventate
#    righe di `RCP.md` poche ore dopo — §5.2 (il client riconfigura sulla prima
#    CHIAVE) e §6.2 (la finestra al posto de «la precedente»).  ⛔ I loro casi
#    stanno adesso in `REGOLE_NUOVE` e in `REGOLE_DI_STATO`, con l'atteso di
#    oggi: un caso che restasse qui starebbe giudicando il documento di ieri.


# ===========================================================================
# ⛔⛔ I RILIEVI **DICHIARATI**: punti in cui `RCP.md` decide, e la decisione
#     non regge — o non e' la stessa in due sezioni.
#
#     ⚠ Non sono `AMBIGUO` e non sono proposte con un caso che le fa scattare:
#       il documento **ha** una risposta, e il banco la applica.  ⛔ Ma
#       applicarla e tacere sul fatto che uccide una sessione sana sarebbe
#       la forma **E8** rivolta contro chi legge il banco.  ⇒ Si stampano in
#       coda a ogni giro, con la scena concreta e il caso che le mostra —
#       oppure con «nessun caso», dichiarato.
#     ⛔ E qui non si cura niente: `RCP.md` e' del coordinatore, e la sera del
#       12 agosto 2026 tre righe applicate in fretta sono costate tre giri.
RILIEVI_DICHIARATI = {
    "P15": {
        "dove": "RCP.md §7.1 — la grazia sulle **coordinate di input**, che e' "
                "rimasta «per un secondo»",
        "dice": "La stessa grandezza sbagliata che P13 ha tolto da §6.2 e' "
                "ancora in §7.1 per il verso opposto del filo: il server "
                "tollera **per un secondo** le coordinate valide sulla tela "
                "precedente, e poi chiude.",
        "scena": "l'uplink e' il verso debole (ADSL, mobile) e gli stream di "
                 "QUIC condividono la finestra di congestione: un input partito "
                 "prima del `TELA` puo' arrivare **dopo** il secondo, e il "
                 "server chiude una sessione in cui il client non ha sbagliato "
                 "— l'invariante **I1** di nuovo.  ⚠ `[?]` **e la cura di P13 "
                 "NON si trasporta**: per i fotogrammi la fine e' un fatto "
                 "osservabile (la chiave alla misura nuova), per le coordinate "
                 "non c'e' niente di equivalente — una coordinata puo' essere "
                 "valida su tutt'e due le tele, e il server non sa distinguerla",
        "caso": None,
        "marca": "[?] non misurata, e **non e' di questo capitolo**: §7.1 e' "
                 "l'input, e questo banco giudica il canale video",
    },
    # ⭐⛔⛔ E QUESTA L'HA TROVATA LA RILETTURA OSTILE DEL 13 AGOSTO 2026, quella
    #     che rimetteva in fila le SETTE righe della famiglia — P8, P11, P13,
    #     P14, P19, P20, P21 — per vedere se ne restava un'ottava.  ⛔ Ne
    #     restava una, e non e' dentro §6.2: e' in §3, ed e' **la forma esatta
    #     di P12**, un passo piu' in la'.
    #     ⚠ **Dichiarata e non curata, e la cura NON si prova qui**: due cure in
    #       un giro sono la fretta che il 12 agosto e' costata tre giri, e
    #       questo giro ne porta gia' una (P21).
    "P22": {
        "dove": "RCP.md §3 — l'elenco delle eccezioni, contro §2.5 e §6.2",
        "dice":
            "§3 dichiara *«le eccezioni sono **sei**, e sono tutte qui.  Fuori "
            "da questo elenco non se ne inventano»* ⛔ e **il TRATTENERE non e' "
            "fra le sei**.  Ma §2.5 (cura di **P20**, 13 agosto) dice che un "
            "fotogramma arrivato prima di `SESSIONE` *«NON DEVE»* far chiudere: "
            "**si trattiene**; e §6.2 (cura di **P19**, 12 agosto) dice la "
            "stessa cosa del fotogramma alla misura mai in vigore.  ⇒ Sono "
            "**due tolleranze comandate da due sezioni normative** e assenti "
            "dall'elenco che si dichiara completo.  ⚠ L'eccezione 6 non le "
            "copre: parla dei fotogrammi che portano *«una misura che E' STATA "
            "in vigore»*, cioe' del caso opposto.",
        "scena": "un client scritto leggendo §3 — *«fuori da questo elenco non "
                 "se ne inventano»* — chiude con `ERRORE_PROTOCOLLO` il "
                 "fotogramma che §2.5 e §6.2 gli ordinano di trattenere; uno "
                 "scritto leggendo §2.5 lo trattiene.  ⛔ Due implementazioni "
                 "conformi, due byte diversi, e quella che chiude uccide "
                 "**proprio la sessione sana** che P19 e P20 sono state scritte "
                 "per salvare.  ⭐ E' la forma di **P12** — §3 rimasta indietro "
                 "mentre §6.2 andava avanti — con una differenza che la rende "
                 "peggiore: li' §3 era piu' STRETTA della stessa tolleranza, "
                 "qui la tolleranza in §3 **non c'e' affatto**.  ⛔ E la cura "
                 "di **P21**, quando entrera', ne aggiunge una terza allo "
                 "stesso elenco: applicarla senza toccare §3 lascia la ferita "
                 "aperta esattamente come il 12 agosto",
        "caso": None,
        "marca": "[R] contraddizione confermata da due righe gia' scritte (§3 "
                 "contro §2.5 e §6.2).  ⛔ **Nessun caso**: questo banco giudica "
                 "il fotogramma con la lettura di §6.2, e un caso che "
                 "pretendesse la lettura di §3 giudicherebbe un client "
                 "immaginario — si dichiara invece di fabbricarlo",
    },
}

# ⭐⛔ E UNA QUESTA TABELLA L'HA OSPITATA PER UN GIRO SOLO: **P21**, nata qui il
#    13 agosto 2026 — «§6.2 comanda il contrario di se stessa a otto righe di
#    distanza» — e passata a `PROPOSTE_APERTE` il giro dopo, con il testo
#    pronto, tre casi e due guasti.  ⛔ Il passaggio non e' contabilita': un
#    rilievo e' una **lettura**, una proposta e' una **cura con i casi che la
#    tengono onesta**, e questo banco dice quale delle due sta consegnando
#    (`REVIEWER.md` §4).  ⚠ E il discriminante che il rilievo proponeva —
#    *«la misura che il client ha nominato»* — la verifica col caso concreto
#    l'ha **bocciato**: §4.5 permette una tela concessa diversa da quella
#    chiesta.  Vedi `p21-concessa-diversa-da-chiesta` e il guasto **G14**.

# ⭐ E QUESTA TABELLA SI E' SVUOTATA IL 12 AGOSTO 2026, come quella delle
#    proposte: **P12** (§3 riga 6 rimasta al singolare mentre §6.2 era passata
#    alla finestra) e **P13** (il secondo di grazia, che era la grandezza
#    sbagliata) sono state curate nel giro dopo essere state scritte qui.
#    ⛔ Resta, vuota e dichiarata: un giro che non stampa niente e un giro che
#    non ha niente da stampare sono due fatti diversi, ed e' la forma E8
#    rivolta contro il banco.

def rilievi_col_caso(casi):
    """⛔ Quali rilievi dichiarati hanno un caso che li mostra, e quali no.

    ⚠ «Non ha un caso» non e' «non conta»: e' un fatto che si stampa.  Un
      rilievo senza caso resta una lettura, e questo banco dice quale delle due
      cose sta consegnando (`REVIEWER.md` §4: un rilievo senza «come si
      dimostra» e' un'ipotesi).
    """
    per_nome = {c["nome"] for c in casi}
    con, senza = [], []
    for sigla, r in RILIEVI_DICHIARATI.items():
        if r["caso"] and r["caso"] in per_nome:
            con.append(sigla)
        else:
            senza.append(sigla)
    return con, senza


def proposte_coperte(casi):
    """⛔ Come `regole_coperte`, per le proposte che il documento non ha ancora.

    ⚠ La differenza sta nella **forma della coppia**: una regola gia' entrata
      ha un caso che la viola (`ERRORE_PROTOCOLLO`) e uno che la rispetta
      (`ACCETTATO`); una proposta aperta ha il caso che la **fa vedere** —
      oggi `AMBIGUO`, perche' il documento non ha ancora deciso — e quelli che
      impediscono di scriverla **troppo larga**.  ⛔ Pretendere qui la stessa
      forma di la' vorrebbe dire far finta che la cura sia gia' applicata.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, p in PROPOSTE_APERTE.items():
        buchi = []
        for nome, atteso in p["casi"].items():
            c = per_nome.get(nome)
            if c is None:
                buchi.append(f"manca il caso «{nome}»")
            elif c["atteso"] != atteso:
                buchi.append(f"«{nome}» non pretende {atteso} ma {c['atteso']}")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


def regole_di_stato_coperte(casi):
    """⛔ Come `regole_coperte`, per le righe che parlano dello **stato del
       client** invece che dei byte — oggi la sola **P10**.

    ⚠ La coppia ha una forma diversa, ed e' il punto: tutt'e due i casi escono
      `ACCETTATO`, perche' sul filo nessuno ha sbagliato.  A cambiare e' il
      **rilievo**: il caso che viola la riga lo deve portare, ⛔ e quello che la
      rispetta **non lo deve portare** — che e' la stessa regola delle due
      meta' della marca (R12-A.3), applicata a un rilievo invece che a un
      guasto.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, r in REGOLE_DI_STATO.items():
        buchi = []
        for chi, nome in (("VIOLA", r["viola"]), ("RISPETTA", r["rispetta"])):
            c = per_nome.get(nome)
            if c is None:
                buchi.append(f"manca il caso che la {chi} («{nome}»)")
            elif c["atteso"] != ACCETTATO:
                buchi.append(f"«{nome}» non pretende ACCETTATO ma {c['atteso']}"
                             f": un difetto del CLIENT non fa cadere il filo")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


def regole_coperte(casi):
    """⛔ Quante delle righe entrate hanno DAVVERO un caso che le fa scattare.

    ⛔ Il conto lo **calcola** questa funzione cercando i nomi fra i casi: un
       numero scritto a mano in un commento e' il numero che nessuno ricalcola
       (`01-b5-violazioni.py`, rilievo R7.14 — tre numeri nei commenti e
       nessuno dei tre tornava con il file).

    Restituisce (coperte, mancanti), dove `mancanti` porta la sigla e **quale
    delle due meta'** manca: ⚠ «la regola c'e' ma il caso che la rispetta no»
    e «la regola non e' provata affatto» sono due difetti diversi, e il primo
    e' quello che lascia passare una regola scritta troppo larga.
    """
    per_nome = {c["nome"]: c for c in casi}
    coperte, mancanti = [], []
    for sigla, r in REGOLE_NUOVE.items():
        # ⛔ «viola» puo' essere UNO o PIU' D'UNO, e la differenza non e' di
        #    comodo: **P8** ha due meta' da tenere strette — il secondo di
        #    grazia e la misura — e una regola che ne provasse una sola
        #    resterebbe verde con l'altra scritta troppo larga.
        nomi_viola = (r["viola"] if isinstance(r["viola"], (tuple, list))
                      else (r["viola"],))
        # ⛔ E L'ESITO ATTESO DELLE DUE META' SI DICHIARA, non si da' per
        #    scontato: **P14** ha la coppia «si scarta / si chiude davvero», e
        #    pretendere qui `ERRORE_PROTOCOLLO` e `ACCETTATO` avrebbe voluto
        #    dire che una regola con una forma diversa non si puo' contare —
        #    cioe' contarla male, o non contarla affatto.
        att_v = r.get("esito_viola", ERRORE_PROTOCOLLO)
        att_s = r.get("esito_rispetta", ACCETTATO)
        s = per_nome.get(r["rispetta"])
        buchi = []
        for nome_v in nomi_viola:
            v = per_nome.get(nome_v)
            if v is None:
                buchi.append(f"manca il caso che la VIOLA («{nome_v}»)")
            elif v["atteso"] != att_v:
                buchi.append(f"«{nome_v}» non pretende {att_v} ma "
                             f"{v['atteso']}")
        if s is None:
            buchi.append(f"manca il caso che la RISPETTA («{r['rispetta']}»)")
        elif s["atteso"] != att_s:
            buchi.append(f"«{r['rispetta']}» non pretende {att_s} ma "
                         f"{s['atteso']}")
        if buchi:
            mancanti.append((sigla, "; ".join(buchi)))
        else:
            coperte.append(sigla)
    return coperte, mancanti


# ===========================================================================
# I CASI.  ⛔ Ciascuno dichiara la sua ATTESA **prima** di misurare: la colonna
#          «atteso» e' una PREVISIONE scritta nel file, non un commento sul
#          risultato (`LEZIONI.md` §1.11, `PIANO.md` §0.3 regola 4).
# ===========================================================================
CASI = []


def caso(nome, atteso, spiega, regola="", contesto=None, dove="uni"):
    def dec(f):
        CASI.append({"nome": nome, "atteso": atteso, "spiega": spiega,
                     "regola": regola, "contesto": contesto, "dove": dove,
                     "fabbrica": f})
        return f
    return dec


# ── L'inquadratura del canale (§2.5) ───────────────────────────────────────
@caso("canale-controllo-su-uni", ERRORE_PROTOCOLLO,
      "il canale di CONTROLLO (0x00) su uno stream unidirezionale del server: "
      "«il controllo vive solo sul primo stream bidirezionale»",
      "RCP.md §2.5")
def _():
    return [struct.pack("!HI", 0x0001, 0) + b"\x00" * 22], "fin"


@caso("canale-audio-su-stream", ERRORE_PROTOCOLLO,
      "il canale AUDIO (0x04) su uno stream: l'audio vive solo sui datagram.  "
      "⚠ Il carico e' l'intestazione di §6.3 ben formata — l'unica cosa storta "
      "e' lo stream",
      "RCP.md §2.5, §6.3")
def _():
    return [struct.pack("!HHQ", 0x0401, 2, 0) + b"\x00" * 16], "fin"


@caso("canale-ignoto", ERRORE_PROTOCOLLO,
      "un byte alto che non e' nessuno dei cinque di §2.5",
      "RCP.md §2.5")
def _():
    return [intestazione(tipo=0x0901)], "fin"


@caso("video-sul-controllo", ERRORE_PROTOCOLLO,
      "⭐⛔ **P3, il caso che la VIOLA** — un fotogramma BEN FORMATO scritto sul "
      "canale di controllo.  ⛔ E' l'unico posto in cui il server puo' "
      "sbagliare stream: §2.5 gli vieta di aprire stream bidirezionali, e il "
      "canale di controllo glielo ha aperto il client.  ⚠ Senza la riga del 12 "
      "agosto il client leggeva quei 28 byte con l'inquadratura di §6.1 e ne "
      "ricavava un messaggio inventato di 64 KiB",
      "RCP.md §2.5", dove="controllo")
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("video-su-unidirezionale", ACCETTATO,
      "⭐ **P3, il caso che la RISPETTA** — gli **stessi identici byte** del "
      "caso qui sopra, su uno stream unidirezionale del server.  ⛔ Senza "
      "questo caso, un giudice che rifiutasse il video **dovunque** — cioe' "
      "che avesse capito P3 come «il video non si accetta» invece che «il "
      "video solo di la'» — resterebbe verde sul caso che la viola",
      "RCP.md §6.2", dove="uni")
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── Il tipo e il codec (§6.2) ──────────────────────────────────────────────
@caso("tipo-0x0300", ERRORE_PROTOCOLLO,
      "`tipo = 0x0300`: canale giusto, valore non definito — §6.2 dice «Altri "
      "valori: ERRORE_PROTOCOLLO»",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=0x0300) + b"\x00" * 64], "fin"


@caso("tipo-0x0303", ERRORE_PROTOCOLLO,
      "`tipo = 0x0303`: il valore subito dopo i due definiti.  ⚠ E' il caso "
      "che un `if (tipo >= 0x0301)` scritto in fretta lascia passare",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=0x0303) + b"\x00" * 64], "fin"


@caso("codec-3", ERRORE_PROTOCOLLO,
      "`codec = 3`: RCP/1 ne definisce due, 1 = HEVC e 2 = AV1",
      "RCP.md §6.2")
def _():
    return [intestazione(codec=3) + b"\x00" * 64], "fin"


@caso("codec-non-negoziato", ERRORE_PROTOCOLLO,
      "`codec = 2` (AV1) su una sessione in cui §4.3 aveva negoziato HEVC.  "
      "⛔ Il campo e' ben formato: l'unica violazione e' che contraddice la "
      "negoziazione, ed e' la sola regola che un giudice senza contesto non "
      "puo' applicare",
      "RCP.md §6.2, §4.3")
def _():
    return [intestazione(codec=2) + b"\x00" * 64], "fin"


# ── La lunghezza, e il FIN contro il RESET (§6.2) ──────────────────────────
@caso("intestazione-27-byte", ERRORE_PROTOCOLLO,
      "⛔ **P4, il caso che la VIOLA** — FIN dopo 27 byte: uno in meno dei 28.  "
      "Letta alla lettera, «la fine dello stream e' la fine del fotogramma» fa "
      "di questo un fotogramma con **meno un** byte di dati.  ⭐ Dal 12 agosto "
      "2026 la regola non si ricava piu' da §3: §6.2 la scrive",
      "RCP.md §6.2")
def _():
    return [intestazione()[:27]], "fin"


@caso("stream-vuoto", ERRORE_PROTOCOLLO,
      "FIN a zero byte.  ⚠ E' il caso in cui «zero» e «fallimento» si "
      "somigliano di piu': uno stream aperto e chiuso subito",
      "RCP.md §6.2")
def _():
    return [], "fin"


@caso("reset-a-meta", SCARTATO,
      "⭐ stream AZZERATO dopo 10 KB: si butta, ⛔ **non** si consegna al "
      "decodificatore, e si tratta come un buco.  ⛔ E la sessione RESTA VIVA: "
      "l'abbandono e' il caso normale di §5.1, non una violazione",
      "RCP.md §6.2, §5.1, §5.2")
def _():
    return [intestazione(), b"\x00" * 10240], "reset"


@caso("reset-prima-dell-intestazione", SCARTATO,
      "stream azzerato dopo 4 byte soli.  ⛔ Il giudizio DEVE guardare il "
      "reset **prima** dell'intestazione: quei quattro byte possono essere "
      "qualunque cosa, e leggerli darebbe `ERRORE_PROTOCOLLO` su un fotogramma "
      "che il server ha abbandonato di proposito",
      "RCP.md §6.2")
def _():
    return [b"\xff\xff\xff\xff"], "reset"


@caso("oltre-16-mib", ERRORE_PROTOCOLLO,
      "un fotogramma di 16 MiB + 1 byte.  ⛔ E il giudizio deve arrivare "
      "**mentre** i byte scorrono, «invece di continuare ad accumulare»",
      "RCP.md §6.2")
def _():
    def pezzi():
        yield intestazione()
        rimane = TETTO_FOTOGRAMMA - INTESTAZIONE + 1
        blocco = b"\x00" * (1 << 20)
        while rimane > 0:
            n = min(rimane, len(blocco))
            yield blocco[:n]
            rimane -= n
    return pezzi(), "fin"


@caso("16-mib-esatti", ACCETTATO,
      "⭐ un fotogramma lungo **esattamente** 16 MiB: il tetto e' un massimo, "
      "non un limite superiore stretto.  ⚠ Senza questo caso «> 16 MiB» e "
      "«>= 16 MiB» danno lo stesso verde su tutto il resto del banco",
      "RCP.md §6.2")
def _():
    def pezzi():
        yield intestazione()
        rimane = TETTO_FOTOGRAMMA - INTESTAZIONE
        blocco = b"\x00" * (1 << 20)
        while rimane > 0:
            n = min(rimane, len(blocco))
            yield blocco[:n]
            rimane -= n
    return pezzi(), "fin"


# ── Lo stato (§1, §3, I3) ──────────────────────────────────────────────────
@caso("prima-di-sessione", ERRORE_PROTOCOLLO,
      "⭐⛔ **P1, il caso che la VIOLA** — un fotogramma ben formato **prima di "
      "`SESSIONE`**, cioe' prima che la tela sia concordata: il client "
      "riceverebbe un fotogramma di cui non conosce ne' la misura ne' il "
      "codec.  E' l'invariante **I3** sul filo — *chi non passa dal validatore "
      "non riceve un pixel* — e dal 12 agosto 2026 §2.5 la scrive anche per "
      "chi **manda**",
      "RCP.md §2.5",
      # ⛔ IL CONTESTO E' DIVENTATO ESPLICITO IL 13 AGOSTO 2026, e l'atteso NON
      #    e' cambiato.  Il caso dice da sempre *«prima che la tela sia
      #    concordata»*: la tela la chiede il client con `ATTACCA` (§4.5),
      #    quindi la scena che questo caso descrive e' quella **prima** di
      #    `ATTACCA`.  ⚠ Fino a oggi il campo non c'era e il caso non
      #    distingueva le due scene — perche' nessuno aveva visto che erano
      #    due.  ⭐ Il verdetto e' `ERRORE_PROTOCOLLO` con la riga di oggi **e**
      #    con la cura di P20: e' il caso su cui le due letture vanno
      #    d'accordo, e per questo resta qui invariato.
      contesto={"sessione_aperta": False, "attacca_spedito": False})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("dopo-sessione", ACCETTATO,
      "⭐ **P1, il caso che la RISPETTA** — gli **stessi identici byte**, con "
      "`SESSIONE` gia' spedita.  ⛔ Senza questo caso il banco non "
      "distinguerebbe «il video prima di `SESSIONE` cade» da «il video cade», "
      "e la seconda lettura fa fallire la fase 2 per intero",
      "RCP.md §6.2",
      contesto={"sessione_aperta": True})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── ⛔⛔ P20 — «prima di `SESSIONE`» misurato da chi RICEVE ─────────────────
#
#    ⭐ La sesta della famiglia P8 -> P11 -> P13 -> P14 -> P19 -> P20, e la
#      forma e' sempre quella di `LEZIONI.md` §1.13: la riga descrive il
#      fenomeno con una **grandezza sostitutiva**.  Qui il sostituto e'
#      *«l'ordine in cui i due stream mi arrivano»*, e il fenomeno vero e'
#      *«il server aveva gia' spedito `SESSIONE` quando ha aperto questo
#      stream»*.
#    ⛔ I due casi qui sotto sono la coppia, e il secondo e' quello che conta:
#      una cura scritta troppo larga passa il primo e apre il secondo, ed e'
#      cosi' che **P5** e' finita sbagliata.
@caso("p20-sessione-in-ritardo", AMBIGUO,
      "⭐⛔ **P20, il caso che la RISPETTA** — gli **stessi identici byte** di "
      "`dopo-sessione`, e un server che ha fatto **tutto** quel che §2.5 e "
      "§5.2 gli impongono: ha spedito `SESSIONE` sul canale di controllo e ha "
      "aperto lo stream del primo fotogramma nella riga dopo.  ⛔ Si perde il "
      "pacchetto che porta `SESSIONE`, il fotogramma arriva intero, e un "
      "client che applichi §2.5 alla lettera **chiude una sessione in cui "
      "nessuno ha sbagliato** — l'invariante **I1** rotta perche' la linea "
      "perde pacchetti, cioe' la condizione che I1 esiste per proteggere.  "
      "⚠ §6.2 dice due volte che gli stream sono indipendenti e che niente ne "
      "ordina la consegna (P14, P19): la stessa frase che qui §2.5 ignora.  "
      "⭐⛔ **E la famiglia e' la CONTRADDIZIONE INTERNA, non la lettura "
      "doppia**: chi riceve non ha nessun'altra grandezza da misurare che il "
      "proprio ordine d'arrivo, quindi due implementazioni attente "
      "**convergono sullo stesso byte** — `CONGEDO(ERRORE_PROTOCOLLO)` su una "
      "sessione sana — e nessun confronto fra client la trova.  ⚠ `[M]` 12 "
      "agosto 2026 e' successo: il cliente di prova ha accusato il server, e a "
      "smentirlo e' stato l'arbitro della **registrazione**, che l'ordine del "
      "filo ce l'ha scritto dentro e un client dal vivo no",
      "RCP.md §2.5",
      contesto={"sessione_aperta": False, "attacca_spedito": True})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


@caso("p20-prima-di-attacca", ERRORE_PROTOCOLLO,
      "⭐⛔ **P20, il caso che la VIOLA, e quello che impedisce di scrivere la "
      "cura TROPPO LARGA** — lo stesso fotogramma, ma il client **non ha "
      "ancora spedito `ATTACCA`**.  §4.5 fa di `SESSIONE` la **risposta** ad "
      "`ATTACCA` ⇒ un server che non l'ha ricevuto non puo' averla spedita, e "
      "il client lo sa **senza guardare l'ordine di consegna**: l'ha spedito "
      "lui.  ⛔ Senza questo caso, una cura nella forma «il client non chiude "
      "mai per un fotogramma prima di `SESSIONE`» resterebbe verde e "
      "porterebbe via l'invariante **I3** — *chi non passa dal validatore non "
      "riceve un pixel* — che e' la sola ragione per cui la riga esiste",
      "RCP.md §2.5",
      contesto={"sessione_aperta": False, "attacca_spedito": False})
def _():
    return [intestazione() + b"\x00" * 64], "fin"


# ── I numeri (§6.2, §6.0, §7.1) ────────────────────────────────────────────
@caso("numero-zero", ERRORE_PROTOCOLLO,
      "⭐⛔ **P2, il caso che la VIOLA** — `numero = 0` sul primo fotogramma.  "
      "Dal 12 agosto 2026 §6.2 riserva lo zero: **il primo porta 1**.  ⚠ Il "
      "caso concreto che la riga chiude: il client decodifica il fotogramma 0, "
      "poi manda `RICHIEDI_CHIAVE(ultimo_numero = 0)` — e il server non puo' "
      "sapere se voglia dire «ho decodificato il fotogramma 0» o «non ne ho "
      "decodificato nessuno» (§7.1), cioe' il sentinella implicito che §6.0 "
      "vieta",
      "RCP.md §6.2")
def _():
    return [intestazione(num=0) + b"\x00" * 64], "fin"


@caso("numero-zero-al-giro", ERRORE_PROTOCOLLO,
      "⭐⛔ **P2 dall'altra parte: lo `0` che RITORNA** — il fotogramma dopo il "
      "4294967295 porta `numero = 0`.  ⛔ E' la falla che P2 aveva lasciata "
      "aperta per due ore: riservava lo `0` e non diceva che al giro del "
      "contatore va **saltato**, cosi' il valore riservato tornava in circolo "
      "da solo dopo due anni e due mesi di sessione.  ⚠ Il sintomo sarebbe "
      "arrivato **una volta sola nella vita di una sessione**, e nessuno "
      "l'avrebbe collegato a `RICHIEDI_CHIAVE`.  Chiusa da §6.2 il 12 agosto "
      "2026: da `0xFFFFFFFF` si passa a `1`",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 0xFFFFFFFF, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=0) + b"\x00" * 64], "fin"


@caso("numero-uno", ACCETTATO,
      "⭐ **P2, il caso che la RISPETTA** — `numero = 1` sul primo fotogramma, "
      "che e' il valore che §6.2 impone.  ⛔ E' anche il caso che tiene onesto "
      "il confronto: un giudice che rifiutasse **ogni** `numero` basso "
      "sembrerebbe severissimo e sarebbe rotto",
      "RCP.md §6.2")
def _():
    return [intestazione(num=1) + b"\x00" * 64], "fin"


@caso("misura-diversa-dalla-tela", ERRORE_PROTOCOLLO,
      "⭐⛔ **P5, il caso che la VIOLA** — un fotogramma 1280x720 su una tela in "
      "vigore 1920x1080, e ⛔ **nessun `ADATTA_TELA` prima**.  Dal 12 agosto "
      "2026 §6.2 dice che `largh.` e `altezza` **DEVONO** valere la tela in "
      "vigore, e che chi ne riceve altre chiude.  ⚠ Prima le due letture erano "
      "tutt'e due difendibili — chiudere per §3, o riscalare come il client fa "
      "gia' per la **vista**",
      "RCP.md §6.2")
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("misura-dopo-adatta-tela", ACCETTATO,
      "⭐⛔ **P5, il caso che la RISPETTA, e ha corretto `RCP.md`** — gli "
      "**stessi identici byte** del caso qui sopra, ma prima e' passato un "
      "`TELA(ADATTATA, 1280, 720)` sul canale di controllo (§7.1).  ⛔ Per due "
      "ore §6.2 ha detto «la tela concessa in `SESSIONE`», e con quella riga "
      "questo caso sarebbe `ERRORE_PROTOCOLLO`: il client avrebbe ucciso la "
      "sessione perche' l'utente ha trascinato una finestra — che e' "
      "**esattamente** la scena che §7.1 protegge con la sua eccezione 4.  "
      "⚠ Senza questo caso la regola nuova sarebbe severa quanto quella "
      "sbagliata di prima, e nessun banco lo direbbe",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


@caso("misura-uguale-a-una-tela-diversa", ACCETTATO,
      "⭐⛔ **P5, il caso che la RISPETTA, e non e' il fotogramma predefinito** "
      "— 1280x720 su una tela **concessa** 1280x720.  ⛔ Sono gli **stessi "
      "byte** del caso che la viola: cambia solo la tela concordata in "
      "`SESSIONE`.  ⚠ Senza questo caso, un giudice che avesse scritto "
      "`if (lar, alt) != (1920, 1080)` — cioe' la misura predefinita al posto "
      "della tela concessa — sarebbe verde su tutti e ventisette gli altri "
      "casi, e rosso sulla prima sessione a 720p",
      "RCP.md §6.2",
      contesto={"tela": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720) + b"\x00" * 64], "fin"


# ── ⛔⛔ D14 — I FOTOGRAMMI IN VOLO, e la proposta **P8** ───────────────────
#    I tre casi vanno letti insieme: il primo mostra la sessione sana uccisa,
#    il secondo e il terzo impediscono di curarla con una regola troppo larga.
@caso("p8-in-volo-dopo-adatta-tela", ACCETTATO,
      "⭐⛔ **P8, IL CASO CHE LA RISPETTA — ED E' LA SCENA CHE UCCIDEVA UNA "
      "SESSIONE SANA** — la tela era 1920x1080, e' passato un `TELA(ADATTATA, "
      "1280, 720)` (§7.1), e adesso arriva il fotogramma **aperto prima**, che "
      "porta 1920x1080.  ⛔ Fino a stasera §6.2 alla lettera diceva "
      "`ERRORE_PROTOCOLLO` — mentre §6.2 **stesso** dice che «gli stream sono "
      "indipendenti, quindi i fotogrammi possono arrivare fuori ordine» — e "
      "questo caso usciva `AMBIGUO` perche' nessuno dei due lati aveva "
      "sbagliato.  ⭐ Dalla sera del 12 agosto 2026 la grazia di un secondo e' "
      "una riga di §6.2 e la **sesta eccezione** di §3: si ACCETTA, si dipinge "
      "**riscalato**, ⛔ e §3 pretende che la tolleranza sia **scritta nel "
      "registro** — questo caso guarda anche quella, perche' «una tolleranza "
      "silenziosa e' indistinguibile da un difetto»",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p13-vecchia-dopo-la-chiave-nuova", ERRORE_PROTOCOLLO,
      "⭐⛔ **P13, il caso che la VIOLA — e la tolleranza non e' un permesso "
      "permanente** — gli **stessi identici byte** del caso qui sopra, ma la "
      "**chiave alla misura nuova e' gia' arrivata**: la coda si e' svuotata.  "
      "⛔ Da li' in poi un fotogramma alla misura vecchia non e' piu' uno in "
      "volo: e' un server che continua a catturare a una tela che non e' piu' "
      "in vigore, ed e' §6.2 senza sconti.  ⭐ E la fine della tolleranza e' un "
      "**fatto osservabile sul filo**, non un tempo dichiarato: fino alla cura "
      "di P13 questo caso doveva annunciare «il secondo e' passato», cioe' una "
      "cosa che sul filo non c'e' — e che un arbitro che legge una "
      "registrazione non poteva vedere",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "chiave_alla_tela_nuova": True, "ultimo_consegnato": 41,
                "chiave_consegnata": True})
def _():
    # ⛔ `numero` **42**, cioe' DOPO la chiave alla misura nuova: non e' un
    #    fotogramma in volo — quelli sono stati catturati prima e portano numeri
    #    piu' bassi — e' un server che ha continuato a catturare alla tela
    #    vecchia.  ⚠ Il numero qui e' la meta' del caso, e senza sarebbe la
    #    scena del rilievo **P14**, che e' un'altra cosa.
    return [intestazione(lar=1920, alt=1080, num=42) + b"\x00" * 64], "fin"


@caso("p14-in-volo-scavalcato-dalla-chiave", SCARTATO,
      "⭐⛔⛔ **P14, IL CASO CHE LA ESERCITA — e fino a un'ora fa qui cadeva la "
      "sessione** — la chiave alla misura nuova (`numero` 41) e' gia' "
      "arrivata, e adesso arriva il fotogramma **in volo** che porta la misura "
      "vecchia e ⛔ **un numero PIU' BASSO** (40): e' stato catturato **prima** "
      "del `TELA`.  ⚠ E' la scena normale, non quella rara: il fotogramma "
      "vecchio e' il piu' grosso — §5.2 vieta al server di abbandonare una "
      "chiave — e gli stream sono indipendenti, quindi la chiave nuova, piu' "
      "piccola, **lo scavalca**.  ⛔ Prima della cura la misura si guardava per "
      "prima e il verdetto era `ERRORE_PROTOCOLLO`: cadeva una sessione in cui "
      "nessuno aveva sbagliato.  ⭐ Adesso §6.2 dice che **l'ordine viene prima "
      "della misura**: si SCARTA, «e la sua misura non si guarda nemmeno» — e "
      "la sessione resta viva, che e' quel che §5.1 chiede per un fotogramma "
      "arrivato tardi",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "chiave_alla_tela_nuova": True, "ultimo_consegnato": 41,
                "chiave_consegnata": True})
def _():
    return [intestazione(lar=1920, alt=1080, num=40) + b"\x00" * 64], "fin"


@caso("p13-linea-lenta", ACCETTATO,
      "⭐⛔⛔ **P13, IL CASO PER CUI LA CURA ESISTE — la linea lenta** — gli "
      "**stessi identici byte** del fotogramma in volo, e il caso dichiara una "
      "cosa sola in piu': ⛔ **il secondo e' passato da un pezzo**.  La chiave "
      "1920x1080 aperta un istante prima del `TELA` pesa qualche MiB (§6.2 ne "
      "ammette 16) e la linea porta poco — e le linee cattive sono **dentro** "
      "il modello: il minimo di `CODER.md` §1 e' 480p a 25.  ⛔ Con la riga a "
      "orologio il client chiudeva un fotogramma spedito quando era legale, e "
      "che §5.2 vietava al server di abbandonare: non e' solo una sessione "
      "sana che cade, e' l'invariante **I1** — «mai a staccare» — rotta "
      "**perche' la linea e' lenta**, cioe' nella condizione esatta che I1 "
      "esiste per proteggere.  ⭐ Adesso la tolleranza finisce sulla **chiave**, "
      "e la chiave non e' ancora arrivata: si ACCETTA.  ⚠ Il tempo dichiarato "
      "qui **non decide piu' niente** — lo rimette a decidere solo il guasto "
      "**G10**, «il giudice con l'orologio», e allora questo caso torna rosso: "
      "e' cosi' che la cura si dimostra invece di raccontarsi",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "secondo_passato": True})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p8-misura-di-nessuna-tela", ERRORE_PROTOCOLLO,
      "⭐⛔ **P8 copre UNA misura, non «tutto per un secondo»** — stessa scena "
      "e stessa grazia aperta, ma il fotogramma porta 800x600: ⛔ ne' la tela "
      "in vigore (1280x720) ne' la precedente (1920x1080).  Non e' un "
      "fotogramma in volo, e' un campo sbagliato — §6.2 chiude, e deve "
      "chiudere.  ⚠ Senza questo caso una grazia scritta «durante il cambio di "
      "tela la misura non si controlla» passerebbe il caso che uccide e "
      "spegnerebbe P5 nella finestra in cui il server e' piu' probabile che "
      "sbagli.  ⭐ E' la seconda meta' che alla prima stesura di P5 mancava",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720)})
def _():
    return [intestazione(lar=800, alt=600, num=41) + b"\x00" * 64], "fin"


# ── ⭐⛔ P10 E P11 — LE DUE CURE DELLA **SECONDA** TORNATA DI QUELLA SERA ───
#    ⚠ Questi quattro casi sono nati `AMBIGUO`, il 12 agosto sera: erano i due
#      punti in cui le cure di D13 e D14, appena applicate, non reggevano.  ⛔ Il
#      coordinatore ha applicato tutt'e due le cure nel giro dopo, e qui i casi
#      sono **passati a verdetto** — che e' la sola cosa che chiude il cerchio.
@caso("p10-decodificatore-al-tela", ACCETTATO,
      "⭐⛔ **P10, il caso che la VIOLA — e la violazione e' del CLIENT, non "
      "del filo** — stessa scena del fotogramma in volo, con **una cosa in "
      "piu' dichiarata**: il client ha riconfigurato il decodificatore a "
      "1280x720 quando e' arrivato il `TELA`.  ⛔ Fino alla riga di stasera qui "
      "§6.2 diceva «accettalo e dipingilo» e §5.2 «buttalo», e questo caso "
      "usciva `AMBIGUO`.  ⭐ Adesso §5.2 dice due cose che lo chiudono: il "
      "client riconfigura **sulla prima CHIAVE alla misura nuova, non sul "
      "`TELA`**, e non consegna un fotogramma di misura sbagliata «**ne' quella "
      "tollerata da §6.2**».  ⇒ Il fotogramma si ACCETTA — sul filo nessuno ha "
      "sbagliato — ⛔ e il banco stampa un **RILIEVO SUL CLIENT**: quel "
      "decodificatore e' dove §5.2 gli vieta di essere, e `[M]` dipinge "
      "un'immagine sfasciata senza sollevare un errore.  ⚠ Il rilievo non e' "
      "l'esito: promuoverlo farebbe cadere una sessione in cui il server e' "
      "conforme",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "decodificatore_a": (1280, 720)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p10-decodificatore-alla-chiave", ACCETTATO,
      "⭐ **P10, il caso che la RISPETTA** — gli **stessi identici byte**, e il "
      "client e' dove §5.2 lo vuole: il decodificatore e' ancora a 1920x1080 "
      "perche' la chiave alla misura nuova non e' ancora arrivata.  ⛔ La "
      "misura del fotogramma e quella del decodificatore **coincidono**, quindi "
      "non c'e' niente da rilevare — e il banco lo verifica: il rilievo del "
      "caso qui sopra **non deve comparire** qui.  ⚠ Senza questa meta', un "
      "banco che stampasse il rilievo sempre sarebbe verde su tutt'e due e non "
      "distinguerebbe il client conforme da quello che non lo e'",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "decodificatore_a": (1920, 1080)})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p11-due-tele-nella-finestra", ACCETTATO,
      "⭐⛔ **P11, il caso che la RISPETTA — e la scena e' quella che uccideva "
      "una sessione sana un passo piu' in la'** — 1920x1080, `TELA(ADATTATA, "
      "1600, 900)`, e 200 ms dopo `TELA(ADATTATA, 1280, 720)`: chi trascina "
      "una finestra ne manda due.  Arriva la **chiave** aperta prima di tutto, "
      "che porta 1920x1080: ⛔ non e' la tela in vigore e non e' **la** "
      "precedente, e §6.2 al singolare diceva `ERRORE_PROTOCOLLO` **subito**.  "
      "⭐ Dalla riga di stasera la grazia copre «una tela che e' stata in "
      "vigore entro il **secondo appena passato**», e questa lo e' stata: si "
      "ACCETTA, con la tolleranza dichiarata.  ⚠ Ed e' proprio la chiave a "
      "restare in volo piu' a lungo — e' la piu' grossa, e §5.2 vieta al server "
      "di abbandonarla",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080),
                "adatta_tela": [(1600, 900), (1280, 720)]})
def _():
    return [intestazione(lar=1920, alt=1080, num=41) + b"\x00" * 64], "fin"


@caso("p11-misura-mai-in-vigore", ERRORE_PROTOCOLLO,
      "⭐⛔ **P11, il caso che la VIOLA, e senza di lui la cura e' larga** — "
      "**stessa scena a due `TELA`** del caso qui sopra, ma il fotogramma porta "
      "800x600: ⛔ una misura che **in quella finestra non e' mai stata in "
      "vigore** — non 1920x1080, non 1600x900, non 1280x720.  §6.2 dice "
      "`ERRORE_PROTOCOLLO` **subito**, e deve dirlo.  ⚠ Senza questo caso, una "
      "finestra scritta «durante il secondo la misura non si controlla» "
      "passerebbe il caso qui sopra e spegnerebbe P5 **proprio** dove il server "
      "e' piu' probabile che sbagli.  ⛔ E' la seconda meta' che alla prima "
      "stesura di P5 mancava, e che a P8 e' costata due giri",
      "RCP.md §6.2",
      # ⛔ IL CONTESTO E' DIVENTATO ESPLICITO IL 13 AGOSTO 2026 — proposta
      #    **P21** — e l'atteso NON e' cambiato.  ⭐ Il campo che decide e'
      #    `adatta_in_volo`, e qui e' **vuoto**: i due `TELA` sono arrivati
      #    tutt'e due, quindi non c'e' nessuna richiesta del client che 800x600
      #    possa ancora concedere.  ⇒ E' il caso che tiene STRETTA la cura di
      #    P21: senza, *«si trattiene sempre»* resterebbe verde su tutto il
      #    banco e porterebbe via la riga di P11, cioe' la difesa proprio dove
      #    il server e' piu' probabile che sbagli.  Guasto **G15**.
      contesto={"tela": (1920, 1080),
                "adatta_tela": [(1600, 900), (1280, 720)],
                "adatta_spedito": []})
def _():
    return [intestazione(lar=800, alt=600, num=41) + b"\x00" * 64], "fin"


# ── ⭐⛔⛔ P21 — LE DUE RIGHE DI §6.2 CHE COMANDANO IL CONTRARIO ────────────
#    ⚠ La coppia di P21 e' di **tre** casi, come quella di P8, e per la stessa
#      ragione: una cura si puo' sbagliare in due versi, e la scena che l'ha
#      motivata li passa tutt'e due.  Il terzo caso e' quello contro cui la
#      cura **come e' stata proposta** si e' rotta.
@caso("p21-nominata-e-in-volo", AMBIGUO,
      "⭐⛔ **P21, IL CASO CHE LA FA VEDERE** — `SESSIONE` 1920x1080, e' passato "
      "un `TELA(ADATTATA, 1600, 900)`, il client manda `ADATTA_TELA(1280, 720)` "
      "e ⛔ **il fotogramma a 1280x720 arriva PRIMA della risposta**: gli stream "
      "sono indipendenti e §6.2 lo dice due volte.  ⇒ Otto righe di §6.2 "
      "comandano il contrario sullo stesso fotogramma — il paragrafo di **P19** "
      "dice *«NON DEVE chiudere: trattiene»*, quello della tolleranza (**P11** "
      "+ **P13**) dice `ERRORE_PROTOCOLLO` **subito** per una misura mai in "
      "vigore in quella finestra.  ⛔ Due implementazioni conformi, due byte "
      "diversi, e una delle due uccide una sessione in cui **nessuno** ha "
      "sbagliato: il server ha catturato alla misura che sta per concedere, "
      "com'e' tenuto a fare da §5.2 (la chiave a ogni cambio di tela).  ⭐ E la "
      "cura non e' un'attesa aperta: §7.1 impone un `TELA` a **ogni** "
      "`ADATTA_TELA`, «riuscito o no»",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1600, 900),
                "adatta_spedito": (1280, 720)})
def _():
    return [intestazione(lar=1280, alt=720, num=41) + b"\x00" * 64], "fin"


@caso("p21-concessa-diversa-da-chiesta", AMBIGUO,
      "⭐⛔⛔ **P21, IL CASO CHE IMPEDISCE DI SCRIVERE LA CURA TROPPO STRETTA — "
      "e ha bocciato il discriminante come era stato proposto** — stessa scena, "
      "ma il client ha chiesto `ADATTA_TELA(1366, 768)` e il fotogramma che "
      "arriva prima della risposta porta **1280x720**, che e' la misura che il "
      "compositore concedera'.  ⛔ Il client quel numero non l'ha **nominato** "
      "mai: la cura scritta *«si trattiene la misura che il client ha "
      "nominato»* chiude qui la sessione, e §4.5 dice a chiare lettere che *«la "
      "tela concessa puo' essere diversa da quella chiesta»* — su KWin < 6.8 e' "
      "**la strada normale** (`SPECIFICHE.md` §6.3), e la negoziazione di §6.4 "
      "concede il modo che il compositore **ha**, non quello che si e' chiesto. "
      "⇒ Il difetto si sposta di un passo, che e' la firma di questa famiglia "
      "da P8 in poi (`LEZIONI.md` §1.13): la grandezza vera non e' **la misura "
      "chiesta**, e' **una richiesta in volo**.  ⭐ Ed e' la stessa forma di "
      "P20, dove la grandezza e' `ATTACCA` e non la tela che `ATTACCA` chiede",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1600, 900),
                "adatta_spedito": (1366, 768)})
def _():
    return [intestazione(lar=1280, alt=720, num=41) + b"\x00" * 64], "fin"


# ── ⭐⛔ D13 — LA CHIAVE A OGNI CAMBIO DI TELA (§5.2), la riga di stasera ───
@caso("d13-delta-alla-misura-nuova", ERRORE_PROTOCOLLO,
      "⭐⛔ **P9, il caso che la VIOLA** — dopo un `TELA(ADATTATA, 1280, 720)` "
      "il primo fotogramma alla misura **nuova** e' un **delta**.  ⛔ `[M]` 12 "
      "agosto 2026, banco `02-pagina-tela-*`: con soli delta alla misura nuova "
      "**Chrome su HEVC emette 5 fotogrammi, tutti dichiarati alla misura "
      "VECCHIA, li dipinge, e non solleva NESSUN errore** — immagine "
      "strappata, 7/8 sul pattern vecchio.  ⚠ AV1 protesta (`EncodingError`) "
      "in tutt'e quattro le caselle: ⇒ la regola serve perche' **sul codec "
      "principale il sintomo e' muto**, e il sintomo sarebbe «il desktop si "
      "strappa quando ridimensiono la finestra»",
      "RCP.md §5.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "ultimo_consegnato": 40, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, lar=1280, alt=720, num=41)
            + b"\x00" * 64], "fin"


@caso("d13-chiave-alla-misura-nuova", ACCETTATO,
      "⭐ **P9, il caso che la RISPETTA** — gli **stessi identici byte**, con "
      "`tipo = 0x0301`.  ⛔ Senza questo caso una regola scritta «dopo un "
      "`TELA` non si accetta niente» resterebbe verde su quello che la viola.  "
      "⚠ E questo banco giudica **meno** di quel che §5.2 dice: vede che e' "
      "una chiave, ⛔ **non puo' vedere se e' una chiave *vera*** — i "
      "VPS/SPS/PPS davanti all'IDR stanno nei dati, e questo giudice i dati "
      "non li conserva.  Quella meta' la misurano `02-codifica-nal.py` e "
      "`02-pagina-tela-*`, ed e' scritto qui per non farla credere coperta",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "ultimo_consegnato": 40, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=CHIAVE, lar=1280, alt=720, num=41)
            + b"\x00" * 64], "fin"


@caso("d13-tela-che-non-cambia", ACCETTATO,
      "⭐⛔ **P9, la terza faccia: un `TELA` che NON cambia la misura non apre "
      "nessun debito** — §7.1 fa rispondere `TELA` a **ogni** `ADATTA_TELA`, "
      "compreso quello che chiede la misura che c'e' gia'; qui la tela resta "
      "1920x1080 e arriva un delta a 1920x1080.  ⛔ Senza questo caso, un "
      "giudice che aprisse il debito della chiave a ogni `TELA(ADATTATA)` "
      "invece che a ogni **cambio** di misura sarebbe verde su tutto il banco "
      "e rosso sulla prima sessione in cui l'utente trascina una finestra e la "
      "rimette dov'era.  ⚠ Ed e' un rosso su una sessione **sana**, cioe' la "
      "famiglia che ha gia' guastato P5 e D14",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1920, 1080),
                "ultimo_consegnato": 40, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, lar=1920, alt=1080, num=41)
            + b"\x00" * 64], "fin"


@caso("d13-delta-dopo-la-chiave-nuova", ACCETTATO,
      "⭐⛔ **P9, la seconda faccia: il debito si paga UNA volta** — la chiave "
      "alla misura nuova e' gia' stata consegnata, e adesso arriva un delta a "
      "1280x720.  ⛔ Senza questo caso, un giudice che avesse capito §5.2 come "
      "«dopo un `TELA` i delta non si accettano» sarebbe verde su tutto il "
      "banco e fermerebbe il video **dopo ogni ridimensionamento**, cioe' "
      "esattamente dove la fase 3 vive",
      "RCP.md §6.2",
      contesto={"tela": (1920, 1080), "adatta_tela": (1280, 720),
                "ultimo_consegnato": 40, "chiave_consegnata": True,
                "chiave_alla_tela_nuova": True})
def _():
    return [intestazione(tipo=DELTA, lar=1280, alt=720, num=41)
            + b"\x00" * 64], "fin"


@caso("primo-fotogramma-delta", ERRORE_PROTOCOLLO,
      "⭐⛔ **P6, il caso che la VIOLA, e morde proprio in questa fase** — il "
      "PRIMO fotogramma della sessione e' un delta.  Dal 12 agosto 2026 §5.2 "
      "vuole una chiave.  ⚠ Prima era conforme a **ogni riga** del documento, "
      "e il client non aveva modo di accorgersene: nessun buco nei `numero` "
      "(e' il primo) e il decodificatore non solleva errori su un delta orfano "
      "— il sintomo sarebbe stato *«il desktop compare a pezzi»*, che non "
      "nomina ne' il protocollo ne' la chiave",
      "RCP.md §5.2")
def _():
    return [intestazione(tipo=DELTA) + b"\x00" * 64], "fin"


@caso("primo-fotogramma-chiave", ACCETTATO,
      "⭐ **P6, il caso che la RISPETTA** — il primo fotogramma della sessione "
      "e' una chiave (`0x0301`).  ⛔ E' il fotogramma che la fase 2 esiste per "
      "consegnare, ed e' qui col suo nome perche' la riga di §5.2 abbia le due "
      "facce e non una",
      "RCP.md §6.2")
def _():
    return [intestazione(tipo=CHIAVE) + b"\x00" * 64], "fin"


@caso("delta-dopo-la-chiave", ACCETTATO,
      "⭐⛔ **P6, la seconda faccia: un delta che NON e' il primo** — chiave 4 "
      "gia' consegnata, arriva il delta 5.  ⚠ Senza questo caso, un giudice "
      "che avesse capito §5.2 come «i delta non si accettano» invece che «il "
      "PRIMO dev'essere una chiave» resterebbe verde su tutto il banco — e "
      "fermerebbe il video dalla fase 3 in poi, dove i delta sono il 99 % dei "
      "fotogrammi",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 4, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=5) + b"\x00" * 64], "fin"


@caso("fuori-ordine", SCARTATO,
      "il fotogramma 7 arriva dopo che il 9 e' stato consegnato: si scarta.  "
      "⛔ E si SCARTA, non si chiude: gli stream sono indipendenti e i "
      "fotogrammi fuori ordine sono il caso normale di §5.1",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=7) + b"\x00" * 64], "fin"


@caso("ripetuto", SCARTATO,
      "lo stesso `numero` due volte: la differenza con segno vale zero, che "
      "non e' «successivo».  ⚠ Senza questo caso un `d < 0x80000000` lascia "
      "passare il duplicato e il decodificatore riceve due volte lo stesso "
      "fotogramma",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=9) + b"\x00" * 64], "fin"


@caso("modulo-2-32", ACCETTATO,
      "⭐ il fotogramma **1** dopo il 4294967295: e' **successivo**, non "
      "precedente.  §6.2 vuole l'aritmetica modulo 2^32 con le differenze con "
      "segno, ⛔ e un confronto `<` diretto farebbe scartare **ogni** "
      "fotogramma dopo il giro, per sempre — a 60 al secondo il contatore gira "
      "dopo due anni e due mesi, e una sessione puo' durare di piu'.  ⭐⛔ E "
      "che dopo `0xFFFFFFFF` venga **1 e non 0** adesso e' una RIGA di §6.2 — "
      "*«al giro del contatore lo 0 si salta»*, aggiunta il 12 agosto 2026 — "
      "mentre fino a quel giorno era una scelta di questo banco: P2 riservava "
      "lo `0` e nessuna riga impediva al contatore di ripassarci sopra da solo",
      "RCP.md §6.2",
      contesto={"ultimo_consegnato": 0xFFFFFFFF, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=1) + b"\x00" * 64], "fin"


@caso("buco-nella-successione", ACCETTATO,
      "⭐ il fotogramma 12 dopo il 9: si ACCETTA — un buco e' normale, §6.2 "
      "dice che il contatore cresce anche per i fotogrammi abbandonati — ⛔ e "
      "il client DEVE chiedere una chiave.  ⚠ E' il caso in cui «accettato» da "
      "solo non basta: si guarda anche `chiedi_chiave`",
      "RCP.md §6.2, §5.2",
      contesto={"ultimo_consegnato": 9, "chiave_consegnata": True})
def _():
    return [intestazione(tipo=DELTA, num=12) + b"\x00" * 64], "fin"


# ── I verdi attesi: quel che DEVE passare ──────────────────────────────────
@caso("chiave-buona", ACCETTATO,
      "⭐ il fotogramma che la fase 2 esiste per consegnare: chiave, HEVC, "
      "1920x1080, numero 1.  ⛔ Senza questo caso il banco potrebbe rifiutare "
      "tutto e sembrare severissimo",
      "RCP.md §6.2")
def _():
    return [intestazione() + b"\x00" * 4096], "fin"


@caso("chiave-senza-dati", ACCETTATO,
      "⭐ 28 byte esatti e FIN: un fotogramma con **zero** byte di dati.  "
      "⚠ Nessuna riga di `RCP.md` lo vieta, e questo caso e' qui per "
      "dichiararlo invece di scoprirlo: e' legale, e passera' al "
      "decodificatore che lo rifiutera' lui.  ⛔ Se un giorno si decidesse che "
      "e' un errore, la riga va in `RCP.md`, non in un `if` del client",
      "RCP.md §6.2")
def _():
    return [intestazione()], "fin"


@caso("istante-zero", ACCETTATO,
      "⭐ `istante = 0`.  §6.2: «non e' un'ora, e' un orologio monotono che "
      "parte da un punto qualunque» — e zero e' un punto qualunque.  ⚠ Un "
      "giudice che lo rifiutasse starebbe inventando un sentinella che §6.0 "
      "vieta",
      "RCP.md §6.2")
def _():
    return [intestazione(ist=0) + b"\x00" * 64], "fin"


@caso("input-zero", ACCETTATO,
      "⭐ `input = 0`, che §6.2 dichiara essere «nessuno».  E' il valore che "
      "porta **ogni** fotogramma della fase 2, dove non esiste input",
      "RCP.md §6.2")
def _():
    return [intestazione(inp=0) + b"\x00" * 64], "fin"


@caso("dati-a-pezzetti", ACCETTATO,
      "⭐ l'intestazione spezzata in sette pezzi da quattro byte.  ⛔ Uno "
      "stream QUIC arriva a pezzi di misura qualunque, e un giudice che "
      "leggesse i 28 byte da un solo `recv` sarebbe verde su ogni banco e "
      "rosso sulla prima rete vera",
      "RCP.md §6.2")
def _():
    g = intestazione()
    return [g[i:i + 4] for i in range(0, 28, 4)] + [b"\x00" * 64], "fin"


# ===========================================================================
# ⛔ I GUASTI, E OGNUNO ROMPE UNA PROPRIETA' SOLA — `PIANO.md` §0.3 regola 4.
#
#    «Un banco che non e' mai diventato rosso non e' pulito: e' NON
#    CERTIFICATO» (`01-b12-guasti.py`).  ⛔ E la marca ha DUE meta': il giro
#    guasto la deve dire **e il giro sano NON la deve gia' dire** — il criterio
#    che l'11 agosto 2026 mancava proprio al banco che certifica gli altri
#    undici (rilievo R12-A.3).
GUASTI = {
    "G1": {
        "titolo": "l'intestazione letta di 32 byte invece che di 28",
        "rompe": "la misura dell'intestazione (§6.2)",
        "dimostra":
            "⛔ E' il difetto **storico** di questo campo: `RCP.md` §6.2 e' "
            "stato corretto il 9 agosto 2026 perche' il disegno dava «… 24 │ "
            "32», cioe' quattro byte di riempimento mai dichiarati.  Con 32, "
            "il giudice mangia quattro byte di dati dentro l'intestazione: "
            "ogni fotogramma corto diventa «intestazione corta» e ogni "
            "fotogramma lungo si sposta di quattro byte.  ⭐ Un banco che non "
            "avesse un caso da 28 byte esatti (`chiave-senza-dati`) NON "
            "vedrebbe questo guasto.",
        # ⭐ Questa marca e' piu' forte delle altre due, e va detto: non dice
        #    «un caso e' rosso», dice **il numero sbagliato**.  Distingue il
        #    rosso del guasto dal rosso di un banco che crolla.
        "marca": "l'intestazione ne vuole 32",
    },
    "G2": {
        "titolo": "il giudice accetta anche `tipo = 0x0300`",
        "rompe": "la regola di rigore sul tipo (§3, §6.2)",
        "dimostra":
            "⛔ E' l'indulgenza che `RCP.md` §3 esiste per togliere, nella sua "
            "forma piu' innocua: un valore in piu' in un `set`.  ⭐ Il guasto "
            "**non rompe niente di visibile** — tutti i fotogrammi buoni "
            "continuano a passare — e si vede solo dal caso che deve fallire.  "
            "Un banco fatto di soli verdi attesi resterebbe verde.",
        "marca": "tipo-0x0300: ERRORE_PROTOCOLLO -> ACCETTATO",
    },
    "G3": {
        "titolo": "uno stream AZZERATO trattato come uno chiuso con FIN",
        "rompe": "la distinzione fra abbandono e fotogramma completo (§6.2)",
        "dimostra":
            "⛔ E' **esattamente** il difetto che il rilievo R1.7 ha trovato in "
            "`RCP.md` la sera del 9 agosto 2026: senza le due parole «ma solo "
            "se lo stream e' finito con un FIN», *«un fotogramma abbandonato e "
            "uno completo avevano lo stesso aspetto»* — forma d'errore **E8**. "
            "⭐ Col guasto, i 10 KB di un fotogramma abbandonato finiscono al "
            "decodificatore: mezza immagine, o un rifiuto che nessuno collega "
            "all'abbandono.",
        "marca": "reset-a-meta: SCARTATO -> ACCETTATO",
    },
    # ⭐⛔ G5 — E QUESTO GUASTO NON E' INVENTATO: E' IL GIUDICE DI IERI MATTINA.
    "G5": {
        "titolo": "le quattro righe del 12 agosto tornano a essere ambiguita'",
        "rompe": "le quattro letture doppie chiuse da `RCP.md` il 12 agosto "
                 "2026 (P2 §6.2, P3 §2.5, P5 §6.2, P6 §5.2)",
        "dimostra":
            "⛔ E' **lo stato di questo stesso file la mattina del 12 agosto "
            "2026**, prima che il coordinatore applicasse le sette righe — "
            "come **G4** e' lo stato di oggi di `01-b4-validatore.py`.  ⭐ Un "
            "guasto preso dalla storia vera vale piu' di uno inventato: "
            "dimostra che il banco sa distinguere il documento di oggi da "
            "quello di ieri, che e' precisamente il modo in cui una "
            "certificazione scade senza che nessuno se ne accorga.  ⚠ E il "
            "guasto **non fa cadere niente**: i quattro casi diventano "
            "`AMBIGUO`, cioe' *«nessuno ha sbagliato»* — l'esito piu' "
            "indulgente che questo banco abbia.  Un banco che contasse solo i "
            "rossi lo lascerebbe passare.",
        # ⛔ Quattro casi cambiano, e la marca ne cita **uno**: basta e avanza,
        #    perche' la seconda meta' del criterio (R12-A.3) chiede che il giro
        #    sano NON la dica — e da sano `numero-zero` esce ERRORE_PROTOCOLLO
        #    atteso ed ERRORE_PROTOCOLLO visto.
        "marca": "numero-zero: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
    # ⭐⛔ G6 e G7 — E NEMMENO QUESTI DUE SONO INVENTATI: SONO IL GIUDICE DI
    #    IERI **SERA**, prima che le cure di D13 e D14 entrassero in `RCP.md`.
    "G6": {
        "titolo": "la grazia di un secondo sui fotogrammi in volo non c'e'",
        "rompe": "la sesta eccezione di §3 e la riga in coda a §6.2 (D14)",
        "dimostra":
            "⛔ E' lo stato di questo file **fino alla sera del 12 agosto "
            "2026**, quando la grazia era la proposta P8 e non una riga.  ⭐ Col "
            "guasto innestato il fotogramma gia' in volo dopo un "
            "`TELA(ADATTATA)` torna a essere `ERRORE_PROTOCOLLO`: cioe' **il "
            "client uccide una sessione sana** perche' l'utente ha trascinato "
            "una finestra.  ⚠ E' la stessa forma della prima stesura di P5, "
            "quella che e' rimasta due ore dentro il documento — un banco che "
            "non sapesse vedere questo guasto certificherebbe di nuovo quella "
            "riga.",
        "marca": "p8-in-volo-dopo-adatta-tela: ACCETTATO -> ERRORE_PROTOCOLLO",
    },
    "G7": {
        "titolo": "il primo fotogramma alla misura nuova puo' essere un delta",
        "rompe": "la riga di §5.2 sul cambio di tela (D13)",
        "dimostra":
            "⛔ E' il difetto **D13** rimesso dentro il giudice, ed e' quello "
            "che `[M]` fa dipingere a Chrome cinque fotogrammi alla misura "
            "vecchia **senza un errore**.  ⭐ Il guasto non rompe niente di "
            "visibile — ogni fotogramma buono continua a passare — e si vede "
            "solo dal caso che deve fallire: un banco fatto di soli verdi "
            "attesi resterebbe verde, ed e' precisamente com'e' stata la fase 2 "
            "fino a stasera.",
        "marca": "d13-delta-alla-misura-nuova: ERRORE_PROTOCOLLO -> ACCETTATO",
    },
    # ⭐⛔ G8 e G9 — IL GIUDICE DI **DUE ORE FA**: fra le due cure della sera e
    #    le due che le hanno rimesse in piedi.  ⚠ La storia di questo capitolo
    #    e' fatta di guasti veri a distanza di ore, e ognuno resta qui perche'
    #    e' cosi' che si dimostra che il banco sa distinguere il documento di
    #    adesso da quello di poco fa.
    "G8": {
        "titolo": "la grazia copre «la tela precedente» sola, non la finestra",
        "rompe": "la riga di §6.2 corretta da P11",
        "dimostra":
            "⛔ E' la cura di D14 **come era stata scritta la prima volta**, al "
            "singolare.  ⭐ Col guasto, la scena di chi trascina una finestra — "
            "due `TELA(ADATTATA)` in un secondo — torna a far cadere la "
            "sessione: la chiave aperta prima di tutto porta una misura che "
            "non e' ne' quella in vigore ne' la precedente, e nessuno ha "
            "sbagliato.  ⚠ E' **la stessa forma** di P5 e di D14: un difetto "
            "che sta un passo piu' in la' della scena appena curata, e che si "
            "vede solo se il banco porta il caso con **due** cambi di tela.",
        "marca": "p11-due-tele-nella-finestra: ACCETTATO -> ERRORE_PROTOCOLLO",
    },
    "G9": {
        "titolo": "il rilievo sullo stato del client non si stampa piu'",
        "rompe": "la riga di §5.2 su QUANDO il client riconfigura (P10)",
        "dimostra":
            "⛔ E' l'indulgenza nella sua forma piu' silenziosa: l'esito resta "
            "`ACCETTATO` — sul filo nessuno ha sbagliato davvero — e sparisce "
            "**soltanto** la riga che dice che il decodificatore e' dove §5.2 "
            "gli vieta di essere.  ⭐ Un banco che contasse solo gli esiti "
            "resterebbe verde, ed e' precisamente il difetto che `[M]` fa "
            "dipingere a Chrome un'immagine sfasciata senza sollevare un "
            "errore.  ⚠ Il guasto **non fa cadere nessun esito**: si vede solo "
            "dal controllo che pretende il rilievo.",
        "marca": "p10-decodificatore-al-tela: ACCETTATO -> ACCETTATO    "
                 "accettato, ma senza il RILIEVO",
    },
    "G10": {
        "titolo": "la tolleranza torna a finire A OROLOGIO, dopo un secondo",
        "rompe": "la riga di §6.2 corretta da P13",
        "dimostra":
            "⛔ E' la cura di D14 **come era scritta due ore prima**, con "
            "dentro un secondo.  ⭐ Col guasto, il caso `p13-linea-lenta` "
            "torna `ERRORE_PROTOCOLLO`: il client chiude un fotogramma che il "
            "server ha spedito quando era legale e che §5.2 gli vietava di "
            "abbandonare — **perche' la linea e' lenta**.  ⛔ E' l'invariante "
            "**I1** («mai a staccare») rotta nella condizione esatta che I1 "
            "esiste per proteggere, ed e' il guasto che dimostra che la cura di "
            "P13 non e' raccontata: senza il caso della linea lenta, «la "
            "tolleranza finisce sulla chiave» e «la tolleranza finisce dopo un "
            "secondo» danno lo stesso verde su tutto il resto del banco.",
        "marca": "p13-linea-lenta: ACCETTATO -> ERRORE_PROTOCOLLO",
    },
    "G11": {
        "titolo": "la misura si guarda PRIMA dell'ordine",
        "rompe": "la precedenza di §6.2 curata da P14",
        "dimostra":
            "⛔ E' il giudice di **un'ora fa**, e il guasto non riscrive "
            "nessuna regola: sposta **il posto** in cui una regola si applica, "
            "che e' esattamente quel che P14 ha curato.  ⭐ Col guasto, il "
            "fotogramma in volo scavalcato dalla chiave nuova — `numero` piu' "
            "basso, misura vecchia — torna `ERRORE_PROTOCOLLO` invece di "
            "`SCARTATO`: la sessione cade, e nessuno dei due lati ha "
            "sbagliato.  ⚠ E' la quarta forma della stessa famiglia (P8 -> P11 "
            "-> P13 -> P14), ed e' quella che si vede peggio: due righe "
            "**della stessa sezione**, tutt'e due giuste, e a decidere e' "
            "l'ordine in cui le si legge.",
        "marca": "p14-in-volo-scavalcato-dalla-chiave: SCARTATO -> "
                 "ERRORE_PROTOCOLLO",
    },
    # ⭐⛔ G12 e G13 — I DUE MODI DI SBAGLIARE **P20**, uno per verso.  ⚠ E il
    #    primo non e' inventato: e' il giudice di **stamattina**, ed e' quel
    #    che `02-filo-cliente.py` ha fatto al suo primo giro dal vivo.
    "G12": {
        "titolo": "§2.5 misurata sull'arrivo di `SESSIONE` invece che sulla "
                  "partenza di `ATTACCA`",
        "rompe": "la grandezza vera del fenomeno di §2.5 (proposta P20, "
                 "`LEZIONI.md` §1.13)",
        "dimostra":
            "⛔ E' il giudice di **oggi**, prima della proposta P20, ed e' "
            "esattamente quel che il cliente di prova ha fatto al suo primo "
            "giro contro un server vero (`P2-6` §5.2): "
            "*«[ERRORE_PROTOCOLLO] un fotogramma prima di `SESSIONE`»* su un "
            "server che aveva fatto tutto quel che §2.5 e §5.2 gli impongono.  "
            "⭐ Col guasto la sessione sana cade, e la causa non e' nel "
            "prodotto: e' **la rete**, che ha perso il pacchetto di "
            "`SESSIONE`.  ⚠ La cura di quel giro ha spostato la misura di un "
            "istante — dal risveglio della coroutine ai byte del canale — cioe' "
            "ha curato il **banco** e non la riga: la grandezza restava "
            "sostitutiva, e questo guasto e' la prova che il banco sa "
            "distinguere le due cose.",
        "marca": "p20-sessione-in-ritardo: AMBIGUO -> ERRORE_PROTOCOLLO",
    },
    "G13": {
        "titolo": "la cura di P20 scritta TROPPO LARGA: non si chiude mai "
                  "prima di `SESSIONE`",
        "rompe": "l'invariante **I3** sul filo (§2.5)",
        "dimostra":
            "⛔ E' la forma con cui **P5** e' finita sbagliata, e la lezione "
            "sta nel mandato di questo giro: una regola troppo severa uccide "
            "la sessione sana, una troppo larga lascia passare quel che la "
            "riga esisteva per fermare — e **tutt'e due passano il caso che ha "
            "motivato la cura**.  ⭐ Col guasto, un server puo' aprire uno "
            "stream video addosso a un client che non ha nemmeno spedito "
            "`ATTACCA`, cioe' spingere pixel su chi non si e' attaccato: I3 "
            "sparisce, e nessuno dei 49 verdi del banco se ne accorge.  ⚠ E' "
            "il guasto che dimostra che il **secondo** caso della coppia si "
            "guadagna il posto: senza di lui, «trattiene sempre» e «trattiene "
            "solo dopo `ATTACCA`» danno lo stesso verde su tutto il resto.",
        "marca": "p20-prima-di-attacca: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
    # ⭐⛔⛔ G14 e G15 — I DUE MODI DI SBAGLIARE **P21**, uno per verso.  ⚠ E il
    #     primo non e' inventato nemmeno lui: e' **la cura come e' stata
    #     proposta**, la mattina del 13 agosto, prima che qualcuno le mettesse
    #     davanti un compositore che concede una misura diversa da quella
    #     chiesta.
    "G14": {
        "titolo": "il discriminante di P21 scritto sulla MISURA che il client "
                  "ha nominato, invece che sulla richiesta in volo",
        "rompe": "la grandezza vera del fenomeno di §6.2 (proposta P21, "
                 "`LEZIONI.md` §1.13)",
        "dimostra":
            "⛔ E' la cura di P21 **come e' stata proposta**, e la verifica "
            "l'ha bocciata in un caso solo: §4.5 dice che *«la tela concessa "
            "puo' essere diversa da quella chiesta»*, su KWin < 6.8 e' la "
            "strada normale (`SPECIFICHE.md` §6.3) e la negoziazione di §6.4 "
            "concede il modo che il compositore **ha**.  ⭐ Col guasto, il "
            "client che ha chiesto 1366x768 e riceve — prima della risposta — "
            "il fotogramma 1280x720 che il compositore sta per concedere "
            "**chiude la sessione**: nessuno ha sbagliato, e il difetto si e' "
            "spostato di un passo invece di sparire.  ⚠ E' la ottava stesura "
            "della stessa riga, evitata perche' il banco porta il caso **appena "
            "fuori** dalla scena che la cura raccontava.",
        "marca": "p21-concessa-diversa-da-chiesta: AMBIGUO -> ERRORE_PROTOCOLLO",
    },
    "G15": {
        "titolo": "la cura di P21 scritta TROPPO LARGA: ogni misura mai in "
                  "vigore si trattiene, anche senza nessuna richiesta in volo",
        "rompe": "la riga di §6.2 curata da P11 — `ERRORE_PROTOCOLLO` **subito** "
                 "per una misura mai in vigore in quella finestra",
        "dimostra":
            "⛔ E' la forma con cui **P5** e' finita sbagliata, e con cui P8 e' "
            "costata due giri: una cura che salva il caso che l'ha motivata e "
            "porta via la difesa dall'altro lato.  ⭐ Col guasto, il fotogramma "
            "a 800x600 in mezzo a un cambio di tela — una misura che **nessuno "
            "ha mai chiesto**, cioe' il campo sbagliato che P11 esiste per "
            "fermare — smette di far chiudere: il banco non distingue piu' «il "
            "`TELA` e' ancora in volo» da «il server sta spedendo una misura "
            "che non ha».  ⚠ E' il guasto che dimostra che il **terzo** caso "
            "della terna si guadagna il posto: senza di lui, «si trattiene "
            "sempre» e «si trattiene finche' c'e' una richiesta in volo» danno "
            "lo stesso verde su tutto il resto del banco.",
        "marca": "p11-misura-mai-in-vigore: ERRORE_PROTOCOLLO -> AMBIGUO",
    },
}


# ===========================================================================
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def riga(colore, segno, nome, testo):
    print(f"    {colore}{segno}{GRIGIO}  {nome:30s} {testo}")


def gira_caso(c, guasti):
    """⛔ Restituisce (esito_visto, verdetto, contesto), e non giudica: giudicare
       e' di chi chiama, che ha in mano l'atteso.  Tenere le due cose insieme
       fa scrivere `if visto != atteso: atteso = visto` senza accorgersene."""
    campi = dict(c["contesto"] or {})
    ctx = Contesto(tela=campi.pop("tela", (1920, 1080)),
                   codec_negoziato=campi.pop("codec_negoziato", 1),
                   sessione_aperta=campi.pop("sessione_aperta", True))
    # ⛔ `adatta_tela` NON e' un campo: e' un messaggio arrivato sul filo
    #    (§7.1), e va fatto passare per il metodo — cosi' il contesto si porta
    #    dietro anche DA DOVE viene la tela in vigore, che e' meta' del
    #    verdetto di P5.  ⚠ Un `setattr` diretto avrebbe cambiato i numeri
    #    lasciando `tela_da` a dire «SESSIONE», cioe' un verdetto che nomina
    #    la sezione sbagliata.
    adatta = campi.pop("adatta_tela", None)
    # ⛔ Il tempo che passa NON e' un campo del filo, ed e' inerte dalla cura di
    #    **P13**: lo si dichiara perche' la **scena** lo dice (la linea lenta),
    #    non perche' decida qualcosa.  ⚠ A rimetterlo a decidere e' il solo
    #    guasto G10, ed e' li' che si vede che la cura c'e' davvero.
    secondo_passato = campi.pop("secondo_passato", False)
    # ⚠ E la chiave alla misura nuova si dichiara **dopo** il `TELA`, perche' e'
    #    quel che chiude la coda: vedi `arriva_la_chiave_nuova()`.
    chiave_nuova = campi.pop("chiave_alla_tela_nuova", None)
    if adatta is not None:
        # ⛔ Uno o PIU' D'UNO: chi trascina una finestra manda piu' di un
        #    `ADATTA_TELA` al secondo, ed e' la scena del caso
        #    `p8-due-tele-in-un-secondo`.  ⚠ Una tupla sola resta una tupla
        #    sola: `(1280, 720)` e `[(1280, 720)]` fanno la stessa cosa.
        passi = adatta if isinstance(adatta, list) else [adatta]
        for lar, alt in passi:
            # ⚠ La grazia e' accesa di suo dalla sera del 12 agosto 2026 —
            #   §6.2 la porta — e non si chiede piu': vedi `adatta_tela`.
            ctx.adatta_tela(lar, alt)
    # ⛔⭐ E LE `ADATTA_TELA` SPEDITE E NON ANCORA RISPOSTE — proposta **P21**.
    #
    #    ⚠ Si posano **dopo** i `TELA`, e l'ordine e' la scena: un `TELA` che
    #      arrivasse dopo risponderebbe a questa richiesta e la toglierebbe dal
    #      volo — cioe' il caso direbbe una cosa e il contesto un'altra.
    #    ⛔ E non e' un campo del filo che il client riceve: e' quel che il
    #      client ha **spedito lui**, come `attacca_spedito` per P20.  Un
    #      `setattr` diretto sull'elenco avrebbe scavalcato il metodo, che e'
    #      il posto in cui sta scritto **perche'** quel fatto conta.
    spedite = campi.pop("adatta_spedito", None)
    if spedite is not None:
        for lar, alt in (spedite if isinstance(spedite, list) else [spedite]):
            ctx.adatta_spedito(lar, alt)
    # ⛔ E i campi si posano DOPO il `TELA`, non prima: sono lo stato del
    #    client **al momento in cui il fotogramma arriva**, e un
    #    `chiave_alla_tela_nuova` scritto prima verrebbe azzerato da
    #    `adatta_tela` — cioe' il caso direbbe una cosa e il contesto un'altra.
    for k, v in campi.items():
        setattr(ctx, k, v)
    ctx.secondo_passato = secondo_passato
    if chiave_nuova:
        ctx.arriva_la_chiave_nuova()
    elif chiave_nuova is False:
        ctx.chiave_alla_tela_nuova = False
    g = Giudice(ctx, dove=c["dove"], guasti=guasti)
    pezzi, come = c["fabbrica"]()
    for p in pezzi:
        g.arrivano(p)
        if g.verdetto is not None:
            break          # ⛔ chi ha gia' deciso smette di leggere: e' §6.2
    v = g.finisce(come) if g.verdetto is None else g.verdetto
    return v.esito, v, ctx


def sezione_principale(r):
    """La PRIMA sezione citata, che e' quella che regge il verdetto.

    ⛔ Questa funzione e' nata da un rosso su giudizio giusto, al primo giro
       del banco — 12 agosto 2026.  Il confronto era
       `v.regola.split(" (")[0] == c["regola"].split(" (")[0]`, cioe'
       pretendeva che il verdetto citasse **tutte** le sezioni che la
       previsione elenca: `«RCP.md §6.2»` contro `«RCP.md §6.2, §5.1, §5.2»`
       dava **rosso**, e l'esito era ACCETTATO contro ACCETTATO.

    ⚠ Quattro casi su ventisette, tutti con il giudizio esatto: e' la forma
      che questo progetto paga piu' spesso — **il banco che accusa il
      prodotto** — e stavolta e' costata dieci minuti perche' il banco
      stampava «esito giusto, REGOLA sbagliata» invece di «rosso».  ⛔ Un
      controllo che non dice PERCHE' e' rosso manda a cercare dalla parte
      sbagliata: quella riga e' rimasta, e ha fatto il suo mestiere.

    ⭐ La regola giusta: il verdetto DEVE citare la sezione **portante**; le
       altre che la previsione elenca sono il contorno, e pretenderle sarebbe
       pretendere una formulazione, non un giudizio.
    """
    return r.split(",")[0].split(" (")[0].strip()


def conta(casi):
    """⛔ I numeri li CALCOLA questa funzione — mai un commento.

    `01-b5-violazioni.py` rilievo R7.14: tre numeri scritti a mano nei
    commenti, e **nessuno dei tre tornava con il file**.
    """
    return {
        "violazioni": sum(1 for c in casi if c["atteso"] == ERRORE_PROTOCOLLO),
        "scarti": sum(1 for c in casi if c["atteso"] == SCARTATO),
        "verdi": sum(1 for c in casi if c["atteso"] == ACCETTATO),
        "ambigui": sum(1 for c in casi if c["atteso"] == AMBIGUO),
    }


def giro(a, guasti=(), silenzioso=False):
    """Un giro intero.  Restituisce (guastati, ambigui, marche, righe)."""
    casi = [c for c in CASI if not a.solo or a.solo in c["nome"]]
    if not casi:
        # ⛔ ZERO CASI NON E' «TUTTI PASSATI» — rilievo R7.15.
        print(f"    {ROSSO}⛔ «--solo {a.solo}» ha selezionato ZERO casi su "
              f"{len(CASI)}: non c'e' niente da misurare{GRIGIO}")
        print("       Questo NON e' un verde.  I nomi si leggono con --elenco.")
        return None
    guastati, ambigui, righe = 0, [], []
    testo_intero = []
    for c in casi:
        try:
            visto, v, ctx = gira_caso(c, guasti)
            errore = None
        except Exception as e:   # noqa: BLE001 — il tipo dell'errore E' la misura
            visto, v, ctx, errore = None, None, None, f"{type(e).__name__}: {e}"
        atteso = c["atteso"]
        ok = (errore is None and visto == atteso)
        # ⛔ E LA REGOLA CITATA SI CONFRONTA, non si stampa soltanto: un rosso
        #    con la sezione sbagliata accanto passa per un rosso giusto.
        regola_ok = (errore is None and c["regola"]
                     and sezione_principale(v.regola)
                     == sezione_principale(c["regola"]))
        if ok and c["regola"] and not regola_ok:
            ok = False
            errore = (f"esito giusto, ma la SEZIONE PORTANTE non torna: il "
                      f"verdetto cita «{sezione_principale(v.regola)}», la "
                      f"previsione «{sezione_principale(c['regola'])}»")
        # ⛔ e i casi che chiedono qualcosa in piu' del solo esito
        if ok and c["nome"] == "buco-nella-successione" and not ctx.chiedi_chiave:
            ok, errore = False, ("accettato, ma il client non si e' segnato di "
                                 "dover chiedere una chiave (§5.2)")
        if ok and c["nome"] == "reset-a-meta" and not ctx.chiedi_chiave:
            ok, errore = False, ("scartato, ma non trattato come un buco: "
                                 "§6.2 lo impone (§5.2)")
        # ⛔ E LA TOLLERANZA SI SCRIVE NEL REGISTRO — §3, ultima riga: *«una
        #    tolleranza silenziosa e' indistinguibile da un difetto, ed e'
        #    precisamente l'indulgenza che questa sezione esiste per togliere»*.
        #    ⚠ Senza questo controllo un giudice che accettasse il fotogramma in
        #      volo **in silenzio** sarebbe verde qui e avrebbe tolto a chi
        #      legge il registro l'unico modo di distinguere l'eccezione dal
        #      difetto.
        if (ok and c["nome"] in ("p8-in-volo-dopo-adatta-tela",
                                 "p11-due-tele-nella-finestra")
                and not v.tollerato):
            ok, errore = False, ("accettato, ma senza dichiarare la "
                                 "tolleranza: §3 vuole che ogni eccezione "
                                 "sia scritta nel registro")
        # ⛔ P10 — E IL RILIEVO SUL CLIENT HA LE SUE DUE META', come una marca:
        #    il caso che viola la riga lo deve **portare**, quello che la
        #    rispetta **non lo deve portare**.  ⚠ Senza la seconda meta', un
        #    banco che stampasse il rilievo sempre sarebbe verde su tutt'e due
        #    e non distinguerebbe il client conforme da quello che non lo e' —
        #    e' il rilievo R12-A.3 applicato a un rilievo invece che a un
        #    guasto.
        if ok:
            for _s, _r in REGOLE_DI_STATO.items():
                if c["nome"] == _r["viola"] and not (v and v.rilievo):
                    ok, errore = False, (
                        f"accettato, ma senza il RILIEVO che {_s} pretende: lo "
                        f"stato del client contraddice §5.2 e il banco tace")
                if c["nome"] == _r["rispetta"] and (v and v.rilievo):
                    ok, errore = False, (
                        f"accettato, ma con un RILIEVO addosso: qui il client "
                        f"e' dove {_s} lo vuole, e un rilievo che compare "
                        f"sempre non distingue niente")
        testo = (errore if errore else str(v))
        righe.append({"nome": c["nome"], "atteso": atteso, "visto": visto,
                      "esito": bool(ok), "regola_vista": v.regola if v else None,
                      "dice": v.dice if v else None, "errore": errore})
        # ⛔ L'USCITA SU CUI SI CERCA LA MARCA PORTA `nome: atteso -> visto`.
        #
        #    Alla prima certificazione le marche di G2 e G3 erano i NOMI dei
        #    casi (`tipo-0x0300`, `reset-a-meta`), e non comparivano: il nome
        #    del caso sta nella riga stampata, non nel testo del verdetto, e
        #    `--certifica` gira in silenzio.  ⛔ Ma la cura non e' «cerchiamo
        #    anche nella riga stampata»: una marca che e' il nome del caso
        #    compare **anche nel giro sano**, dove quel caso passa — cioe'
        #    fallirebbe la seconda meta' del criterio (R12-A.3).
        # ⭐ `nome: atteso -> visto` e' una marca vera: nel giro sano atteso e
        #    visto coincidono sempre, quindi `X: A -> B` con A != B esiste
        #    **soltanto** quando qualcosa e' rotto.
        testo_intero.append(f"{c['nome']}: {atteso} -> {visto}    {testo}")
        if atteso == AMBIGUO:
            # ⛔ UN AMBIGUO NON E' UN GUASTO, E NON E' UN VERDE.
            #    Il caso e' verde se il giudice **riconosce** l'ambiguita';
            #    quel che resta rosso e' `RCP.md`, e si conta a parte.
            if ok:
                ambigui.append((c["nome"], v.propone, v.dice))
                if not silenzioso:
                    riga(GIALLO, "??", c["nome"],
                         f"⭐ RCP.md ammette due letture — proposta "
                         f"{v.propone or '?'}")
                continue
        if not silenzioso:
            riga(VERDE if ok else ROSSO, "OK" if ok else "NO", c["nome"], testo)
        if not ok:
            guastati += 1
            if not silenzioso:
                print(f"        atteso {atteso}, visto {visto}")
                print(f"        {c['spiega']}")
    return guastati, ambigui, righe, "\n".join(testo_intero)


def scrivi_esito(a, rec):
    """⛔ Una riga per giro, con l'ora e la scena, e si sincronizza subito.

    ⚠ Un registro assente e un registro vuoto non devono avere lo stesso
      aspetto: senza `--uscita` si dice, non si tace.
    """
    if not a.uscita:
        print(f"    ⚠ nessun --uscita: questo giro NON lascia registro")
        return False
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "banco": "F2.4",
             "scena": "nessuna rete e nessun server: i fotogrammi li fabbrica "
                      "il banco, e il giudice li legge come li leggerebbe da "
                      "uno stream QUIC (a pezzi, senza tenere i dati)",
             "macchina": os.uname().nodename, "python": sys.version.split()[0]}
    fuori.update(rec)
    try:
        with open(a.uscita, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {ROSSO}⛔ il registro «{a.uscita}» non si scrive: {e}{GRIGIO}")
        return False
    return True


def controllo_positivo():
    """⛔ IN CODA A OGNI ESECUZIONE: lo strumento sa trovare qualcosa che c'e'?

    `LEZIONI.md` §1.9, seconda regola.  Qui la domanda ha una risposta
    esatta e a costo zero: si innesta **G2** — un guasto che non rompe niente
    di visibile — e si verifica che il caso `tipo-0x0300` diventi rosso.

    ⚠ Se questo controllo passasse **anche a giudice sano**, vorrebbe dire che
      quel caso e' rosso sempre, cioe' che il verde di poco fa non era un
      verde.  Si guardano tutt'e due i giri, non uno.
    """
    class Finto:
        solo, uscita = "tipo-0x0300", ""
    sano = giro(Finto(), guasti=(), silenzioso=True)
    guasto = giro(Finto(), guasti=("G2",), silenzioso=True)
    if sano is None or guasto is None:
        return False, "il caso del controllo positivo non esiste piu'"
    if sano[0] != 0:
        return False, (f"⛔ `tipo-0x0300` e' rosso anche a giudice SANO: il "
                       f"verde di questo giro non vale niente")
    if guasto[0] != 1:
        return False, (f"⛔ col guasto G2 innestato `tipo-0x0300` resta VERDE: "
                       f"questo banco non sa vedere il guasto che cerca")
    return True, ("G2 innestato -> `tipo-0x0300` rosso; G2 tolto -> verde.  "
                  "Lo strumento sa trovare quel che c'e'")


def certifica(a):
    """⛔ sano N -> guasto M -> risanato N, e sono TRE esecuzioni per guasto.

    `01-b12-guasti.py`: *«"e' diventato rosso" non vuol dire niente se non era
    verde prima»*, e il terzo passo e' il piu' insidioso da perdere — senza,
    «il banco vede il guasto» e «il banco e' rimasto rotto» hanno lo stesso
    aspetto.
    """
    print(f"\n== ⛔ LA CERTIFICAZIONE — sano -> guasto -> risanato, "
          f"{len(GUASTI)} guasti")
    print(f"   ⛔ Gli attesi sono scritti in `--elenco`, PRIMA di questo giro\n")
    tutto_bene, righe = True, []
    sano = giro(a, guasti=(), silenzioso=True)
    if sano is None:
        return 2
    n_sano, _, _, testo_sano = sano
    print(f"    sano: {n_sano} guasti")
    for sigla, g in GUASTI.items():
        rotto = giro(a, guasti=(sigla,), silenzioso=True)
        n_rotto, _, _, testo_rotto = rotto
        marca = g["marca"]
        # ⛔ LA MARCA HA DUE META', e la seconda si dimentica — R12-A.3.
        vista = marca in testo_rotto
        gia = marca in testo_sano
        risanato = giro(a, guasti=(), silenzioso=True)[0]
        ok = (n_sano == 0 and n_rotto > n_sano and vista and not gia
              and risanato == n_sano)
        tutto_bene &= ok
        riga(VERDE if ok else ROSSO, "OK" if ok else "NO", sigla,
             f"sano {n_sano} -> guasto {n_rotto} -> risanato {risanato}   "
             f"marca «{marca}»: {'vista' if vista else '⛔ NON vista'}"
             + ("  ⛔ ma gia' presente nel giro sano" if gia else ""))
        if not ok:
            print(f"        {g['titolo']}")
        righe.append({"guasto": sigla, "titolo": g["titolo"], "sano": n_sano,
                      "guasto_conta": n_rotto, "risanato": risanato,
                      "marca": marca, "marca_vista": vista,
                      "marca_gia_nel_sano": gia, "esito": bool(ok)})
    scrivi_esito(a, {"tipo": "certificazione", "guasti": righe,
                     "esito": bool(tutto_bene)})
    print()
    if tutto_bene:
        print(f"    {VERDE}⭐ 02-filo-fotogramma.py e' CERTIFICATO: "
              f"{len(GUASTI)} guasti su {len(GUASTI)}{GRIGIO}")
        return 0
    print(f"    {ROSSO}⛔ NON certificato{GRIGIO}")
    return 1


def principale(a):
    n = conta(CASI)
    if a.elenco:
        print(f"== F2.4 — il fotogramma contro `RCP.md`: {len(CASI)} casi")
        print(f"   {n['violazioni']} violazioni · {n['scarti']} scarti · "
              f"{n['verdi']} ⭐ verdi attesi · {n['ambigui']} ⭐ ambiguita' "
              f"di `RCP.md`")
        print(f"   ⛔ Ogni riga e' una PREVISIONE, scritta prima del giro\n")
        for c in CASI:
            print(f"  {c['nome']:30s} {c['atteso']}")
            print(f"  {'':30s}   {c['spiega']}")
            if c["regola"]:
                print(f"  {'':30s}   regola attesa: {c['regola']}")
        print(f"\n== ⛔ I GUASTI, e l'atteso di ciascuno — scritto PRIMA")
        for sigla, g in GUASTI.items():
            print(f"  {sigla}  {g['titolo']}")
            print(f"      rompe:    {g['rompe']}")
            print(f"      atteso sano:   0 guasti su {len(CASI)} casi")
            print(f"      atteso guasto: > 0 guasti, e nell'uscita la marca "
                  f"«{g['marca']}»")
            print(f"      ⛔ e la marca NON deve comparire nel giro sano")
        print(f"\n== ⭐⛔ LE {len(REGOLE_NUOVE)} RIGHE ENTRATE IN `RCP.md` IL 12 AGOSTO 2026,")
        print(f"      e i DUE casi di ciascuna")
        coperte, mancanti = regole_coperte(CASI)
        for sigla, r in REGOLE_NUOVE.items():
            print(f"  {sigla}  {r['dove']}")
            print(f"      «{r['dice']}»")
            print(f"      era:      {r['era']}")
            viola = (", ".join(r["viola"])
                     if isinstance(r["viola"], (tuple, list)) else r["viola"])
            print(f"      {r.get('etichetta_viola', 'la VIOLA')}:    {viola}")
            print(f"      {r.get('etichetta_rispetta', 'la RISPETTA')}: "
                  f"{r['rispetta']}")
        print(f"\n  ⛔ regole con TUTT'E DUE i casi: {len(coperte)} su "
              f"{len(REGOLE_NUOVE)} — {', '.join(coperte) or '—'}")
        for sigla, perche in mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        # ⛔⛔ E LE PROPOSTE APERTE, SEPARATE: quel che il documento NON dice.
        print(f"\n== ⛔⛔ LE PROPOSTE ANCORA APERTE — `RCP.md` non le porta")
        print(f"      ⚠ Non sono regole: sono cure con il testo pronto, e il "
              f"documento")
        print(f"        lo tocca il coordinatore.  Qui c'e' l'atteso di OGGI, "
              f"non di domani")
        ap_coperte, ap_mancanti = proposte_coperte(CASI)
        for sigla, p in PROPOSTE_APERTE.items():
            print(f"  {sigla}  {p['dove']}")
            print(f"      «{p['dice']}»")
            print(f"      e':       {p['era']}")
            # ⛔ E IL TESTO PRONTO SI STAMPA, non si nomina.  Una proposta
            #    citata senza il testo e' un reclamo, ed e' la meta' che
            #    `F2-4-filo.md` §«Che cosa propongo» pretende da ogni riga.
            if p.get("testo"):
                print(f"      testo pronto da incollare:")
                print(f"        {p['testo']}")
            for nome, atteso in p["casi"].items():
                # ⛔ «(oggi)» in coda non e' decorazione: senza, questa riga
                #    finirebbe con `AMBIGUO` e `02-filo-lancia.sh` — che le
                #    ambiguita' le cerca con `grep 'AMBIGUO$'` — stamperebbe
                #    due volte lo stesso caso, una dalla tabella e una
                #    dall'elenco.  ⚠ Un banco che si duplica addosso le proprie
                #    righe fa contare male chi legge l'uscita.
                print(f"      {nome:32s} atteso {atteso} (oggi)")
        print(f"\n  ⛔ proposte con TUTTI i loro casi: {len(ap_coperte)} su "
              f"{len(PROPOSTE_APERTE)} — {', '.join(ap_coperte) or '—'}")
        for sigla, perche in ap_mancanti:
            print(f"     {ROSSO}⛔ {sigla}: {perche}{GRIGIO}")
        return 0

    if a.certifica:
        return certifica(a)

    print(f"== F2.4 — il fotogramma giudicato contro `RCP.md`")
    print(f"   ⛔ SCENA: nessuna rete, nessun server.  I fotogrammi li fabbrica")
    print(f"      questo banco e il giudice li legge **a pezzi**, come "
          f"arriverebbero")
    print(f"      da uno stream QUIC.  Il prodotto della fase 2 non esiste: "
          f"`grep -c`")
    print(f"      di `0x0301` in `src/` da' 0 su tutti e tre i file `[M]`")
    if a.guasto:
        print(f"   {GIALLO}⚠ GUASTO INNESTATO: {a.guasto} — "
              f"{GUASTI[a.guasto]['titolo']}{GRIGIO}")
    print(f"   {len(CASI)} casi: {n['violazioni']} violazioni · {n['scarti']} "
          f"scarti · {n['verdi']} verdi · {n['ambigui']} ambiguita'")
    print(f"   registro: {a.uscita or '⛔ NESSUNO'}\n")

    r = giro(a, guasti=(a.guasto,) if a.guasto else ())
    if r is None:
        return 2
    guastati, ambigui, righe, _ = r

    print(f"\n    == quel che questo giro ha davvero guardato")
    sel = conta([c for c in CASI if not a.solo or a.solo in c["nome"]])
    for che, tot in sel.items():
        if tot == 0:
            print(f"    --  {che:36s} nessun caso lo ha sollecitato")
        else:
            print(f"    {tot:3d}      {che}")

    # ⭐⛔ LE RIGHE NUOVE: QUANTE HANNO DAVVERO I DUE CASI.
    #
    #    ⛔ Questo conto sta **dentro il giro**, non in un commento e non nel
    #       rapporto: una regola che perdesse il caso che la fa scattare
    #       tornerebbe a essere una regola che nessuno fa rispettare, e il
    #       banco resterebbe verde — che e' la forma peggiore di verde.
    coperte, mancanti = regole_coperte(CASI)
    print(f"\n    == ⭐⛔ le {len(REGOLE_NUOVE)} righe entrate in `RCP.md` il 12 "
          f"agosto 2026 — sei di mattina, due di sera")
    riga(VERDE if not mancanti else ROSSO, "OK" if not mancanti else "NO",
         "regole-con-i-due-casi",
         f"{len(coperte)} su {len(REGOLE_NUOVE)} hanno il caso che le VIOLA e "
         f"quello che le RISPETTA: {', '.join(coperte) or '—'}")
    for sigla, perche in mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    # ⛔⛔ E LE PROPOSTE ANCORA APERTE, CONTATE ALLO STESSO MODO.
    #
    #    ⚠ Il conto sta accanto a quello delle regole entrate e **non insieme**:
    #      «le righe che il documento porta» e «una cura che il documento non
    #      ha ancora» sono due fatti diversi, e sommarli darebbe un numero che
    #      non vuol dire niente.
    # ⛔ E LA RIGA CHE PARLA DELLO STATO DEL CLIENT, CONTATA A PARTE — P10.
    st_coperte, st_mancanti = regole_di_stato_coperte(CASI)
    print(f"\n    == ⭐⛔ le righe che parlano dello STATO DEL CLIENT, non del "
          f"filo")
    riga(VERDE if not st_mancanti else ROSSO, "OK" if not st_mancanti else "NO",
         "stato-con-i-due-casi",
         f"{len(st_coperte)} su {len(REGOLE_DI_STATO)} hanno il caso che porta "
         f"il RILIEVO e quello che non lo porta: "
         f"{', '.join(st_coperte) or '—'}")
    for sigla, perche in st_mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    ap_coperte, ap_mancanti = proposte_coperte(CASI)
    print(f"\n    == ⛔⛔ le proposte APERTE — `RCP.md` non le porta ancora")
    riga(VERDE if not ap_mancanti else ROSSO, "OK" if not ap_mancanti else "NO",
         "proposte-con-i-loro-casi",
         f"{len(ap_coperte)} su {len(PROPOSTE_APERTE)} hanno tutti i loro "
         f"casi: {', '.join(ap_coperte) or '—'}")
    for sigla, perche in ap_mancanti:
        print(f"        ⛔ {sigla}: {perche}")

    # ⭐⛔ LE AMBIGUITA' DI `RCP.md`, IN FONDO E CON LA CURA ACCANTO.
    if ambigui:
        print(f"\n    {GIALLO}⭐⛔ `RCP.md` NON DECIDE BENE IN "
              f"{len(ambigui)} PUNT{'O' if len(ambigui) == 1 else 'I'}"
              f"{GRIGIO}")
        print(f"       ⚠ Non e' un guasto del prodotto e non fa fallire questo")
        print(f"         giro: e' un difetto del DOCUMENTO, e §0 dice che i")
        print(f"         difetti di quel file sono di quel file.")
        # ⛔ E le due famiglie si nominano, perche' non sono la stessa cosa e
        #    confonderle gonfia il conto (`F2-4-filo.md`, «Che cosa propongo»):
        #      lettura doppia  -> due implementazioni conformi producono byte
        #                         DIVERSI per lo stesso ingresso;
        #      contraddizione  -> due implementazioni conformi producono lo
        #                         STESSO byte, e quel byte e' sbagliato.
        print(f"       ⚠ E sono due famiglie: una **lettura doppia** fa "
              f"divergere due")
        print(f"         implementazioni attente; una **contraddizione "
              f"interna** le fa")
        print(f"         convergere sullo stesso byte sbagliato — e la seconda "
              f"e' peggio,")
        print(f"         perche' nessun confronto fra due implementazioni la "
              f"trova.")
        for nome, prop, dice in ambigui:
            # ⛔ La cura si cerca in tutt'e due le tabelle: una proposta ancora
            #    aperta non sta fra le regole entrate, e stamparla come «?»
            #    farebbe di un rilievo con la cura pronta un reclamo.
            r = REGOLE_NUOVE.get(prop) or PROPOSTE_APERTE.get(prop, {})
            print(f"\n       {nome}")
            print(f"         {dice}")
            print(f"         ⇒ {prop} — {r.get('dove', '?')}")
            print(f"           «{r.get('dice', '?')}»")
    elif not a.solo:
        # ⛔ E LO ZERO SI DICHIARA, non si tace: «nessuna ambiguita' stampata»
        #    e «il ramo che le stampa non e' esercitato da nessun caso» sono
        #    due fatti diversi, ed e' la forma E8 applicata al banco stesso.
        print(f"\n    --  ⭐ `RCP.md` non ammette piu' due letture in nessuno "
              f"dei {len(CASI)} casi:")
        print(f"        le **dieci** che questo banco ha trovato sono entrate "
              f"tutte nel documento")
        print(f"        il 12 agosto 2026, in quattro tornate: quattro di "
              f"mattina (P2 · P3 ·")
        print(f"        P5 · P6), due di sera (P8 §6.2 · P9 §5.2), ⛔ **due "
              f"nate dalle due di")
        print(f"        sera** (P10 §5.2 · P11 §6.2) e ⛔ **due nate da "
              f"quelle** (P12 §3 · P13")
        print(f"        §6.2) — ognuna trovata **applicando** la precedente, "
              f"non rileggendola.")
        print(f"        ⚠ Da cui: **nessun caso** pretende oggi `AMBIGUO`, e il "
              f"ramo che li")
        print(f"        stampa non e' esercitato da questo giro.  Il ramo del "
              f"GIUDICE che")
        print(f"        produce `AMBIGUO` lo esercita il guasto **G5**, a ogni "
              f"certificazione.")

    # ⛔⛔ I RILIEVI DICHIARATI — dove il documento decide, e la decisione non
    #    regge.  ⚠ Non fanno fallire il giro: non e' il banco a curarli.
    con, senza = rilievi_col_caso(CASI)
    if RILIEVI_DICHIARATI:
        n = len(RILIEVI_DICHIARATI)
        print(f"\n    {GIALLO}⛔⛔ E {n} RILIEV{'O' if n == 1 else 'I'} "
              f"DICHIARAT{'O' if n == 1 else 'I'} su `RCP.md`, che questo giro "
              f"NON cura{GRIGIO}")
        print(f"       ⚠ Qui il documento **decide**, e il banco applica la sua "
              f"decisione:")
        print(f"         non sono `AMBIGUO`.  ⛔ Ma applicarla e tacere che "
              f"uccide una")
        print(f"         sessione sana sarebbe la forma E8 rivolta contro chi "
              f"legge il banco.")
        print(f"       --  con un caso che li mostra: "
              f"{', '.join(con) or '—'} · senza: {', '.join(senza) or '—'}")
        for sigla, r in RILIEVI_DICHIARATI.items():
            print(f"\n       {sigla}  {r['dove']}   {r['marca']}")
            print(f"         {r['dice']}")
            print(f"         scena: {r['scena']}")
            senza_caso = "⛔ nessuno — resta una lettura, e si dichiara"
            print(f"         caso: {r['caso'] or senza_caso}")

    # ⛔ IL CONTROLLO POSITIVO, IN CODA A OGNI ESECUZIONE.
    print(f"\n    == ⛔ il controllo positivo")
    ok_cp, perche = controllo_positivo()
    riga(VERDE if ok_cp else ROSSO, "OK" if ok_cp else "NO",
         "controllo-positivo", perche)

    scritto = scrivi_esito(a, {
        "tipo": "giro", "guasto_innestato": a.guasto or None,
        "filtro": a.solo or None, "casi": len(righe), "guastati": guastati,
        "ambigui": [x[0] for x in ambigui], "proposte": [x[1] for x in ambigui],
        "controllo_positivo": bool(ok_cp), "righe": righe})
    print(f"    --  registro: {'una riga scritta in ' + a.uscita if scritto else 'NESSUNO'}")

    print()
    if guastati or not ok_cp:
        print(f"    {ROSSO}⛔ F2.4-fotogramma: {guastati} casi non passano"
              f"{'' if ok_cp else ', e il controllo positivo non regge'}{GRIGIO}")
        return 1
    if a.solo:
        print(f"    {VERDE}⭐ i casi selezionati passano{GRIGIO} — ⚠ e questo "
              f"NON e' «il banco passa»: il giro era parziale")
        return 0
    print(f"    {VERDE}⭐ il giudice del fotogramma e' d'accordo con `RCP.md` "
          f"su {len(righe)} casi{GRIGIO}")
    print(f"    ⚠ e NON e' «il fotogramma arriva»: qui non e' passato un byte "
          f"sulla rete.")
    print(f"      Quello lo misura `02-filo-cliente.py`, contro un server che "
          f"non esiste ancora.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — il fotogramma giudicato contro RCP.md")
    p.add_argument("--solo", default="",
                   help="gira solo i casi che contengono questo")
    p.add_argument("--elenco", action="store_true",
                   help="stampa le previsioni e i guasti, senza misurare")
    p.add_argument("--guasto", choices=sorted(GUASTI),
                   help="innesta un guasto NEL GIUDICE")
    p.add_argument("--certifica", action="store_true",
                   help="sano -> guasto -> risanato, per ogni guasto")
    p.add_argument("--uscita", default="",
                   help="il registro del giro, in JSONL")
    # ⛔ E CHI LEGGE QUESTA USCITA LA CHIUDE A META': `02-filo-lancia.sh` fa
    #    `--elenco | grep -q 'AMBIGUO$'`, e `grep -q` esce **al primo colpo**
    #    chiudendo il tubo.  ⚠ Fino al 13 agosto 2026 non si vedeva, perche'
    #    nessun caso pretendeva `AMBIGUO` e `grep` leggeva fino in fondo: alla
    #    prima proposta aperta lo script ha stampato un `BrokenPipeError` in
    #    mezzo al verdetto.  ⛔ Un tubo chiuso da chi legge non e' un difetto
    #    di questo banco, e non deve avere l'aspetto di uno — ma **si dichiara
    #    e non si tace**, che e' la forma E8 applicata a se stessi.
    try:
        _codice = principale(p.parse_args())
    except BrokenPipeError:
        # ⚠ Si dirotta il **descrittore 1**, non `sys.stdout`: chiudere
        #   l'oggetto Python fa fallire anche lo svuotamento finale, e il
        #   secondo errore nasconde il primo.
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
        _codice = 0
    sys.exit(_codice)
