#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c3 — ⭐⭐ «I FOTOGRAMMI ARRIVANO, E LA SCENA CAMBIA»
===========================================================================

    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511
    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511 --scena-ferma
    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511 --fotogramma-ripetuto
    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511 --codificatore-fermo
    python3 11-c3-i-fotogrammi-cambiano.py --certifica

E' la riga **C3** di `fasi/11-la-rete-di-sicurezza.md` §4.1, alla lettera:

    che cosa deve essere vero : i fotogrammi arrivano, e la scena CAMBIA
    da dove parte             : sessione NUOVA, ⭐ **scena dichiarata e in
                                movimento**
    che cosa guarda           : ⭐ **canarino anti-morte** — fotogrammi > 0 ·
                                **non crollati** rispetto a un riferimento
                                grezzo · ⛔ **i fotogrammi consecutivi sono
                                diversi fra loro**
    come so che sa dare rosso : si ferma il codificatore ⇒ rosso · ⭐ si manda
                                lo stesso fotogramma ripetuto ⇒ rosso
                                (immagine congelata).  ⚠ E *«scena ferma»*
                                **non** deve dare rosso

---------------------------------------------------------------------------
⛔⛔ LA COSA PIU' IMPORTANTE DI QUESTO FILE, e va letta prima dei numeri
---------------------------------------------------------------------------

⭐⭐ **«I fotogrammi consecutivi sono diversi» NON e' una proprieta' del
     prodotto: e' una proprieta' della COPPIA prodotto + scena.**

`[M]` `fasi/09-la-qualita-e-la-degradazione.md` §3.1, sul ferro vero, 30 secondi
per scena:

    | scena   | fotogrammi/s | attese a vuoto/s |
    |---------|--------------|------------------|
    | ferma   | ⛔ **0,03**   | **123**          |
    | barra   | **39,67**    | 80               |
    | pieno   | **39,00**    | 81               |

⇒ ⛔ **A scena ferma, in 30 secondi, esce UN fotogramma solo — la chiave
   d'apertura — e poi piu' niente.**  E il prodotto lo dichiara da se',
   `[R]` `src/figlio.c:3373`:

     *«su un desktop FERMO Mutter non consegna niente … Zero fotogrammi su una
       scena ferma e' un RISULTATO, non un difetto.»*

⇒ ⭐ Percio' questa maglia **mette lei la scena in movimento**, la **dichiara**
  (`11-c3-scena.html`), e **verifica che sia sullo schermo** prima di pretendere
  che i fotogrammi cambino.  ⛔ Una maglia che pretendesse «i fotogrammi
  cambiano» su un desktop qualunque sarebbe un generatore di rossi falsi — e un
  rosso falso, in una rete di sicurezza, finisce sempre allo stesso modo: la
  rete viene spenta da chi lavora (§1.3 del documento di fase).

⚠ **E QUESTO E' IL SENSO DI `--scena-ferma`**: e' il **controllo negativo**, ed
  e' l'altra meta' di `LEZIONI.md` §1.49 (*si toglie il guasto e si pretende il
  verde*).  ⛔ Con la scena ferma il GIUDIZIO SUI FOTOGRAMMI non puo' dare
  rosso: dice «non lo so» e dice perche' — un'immagine congelata e un desktop
  che non ha niente da mostrare hanno **lo stesso identico aspetto**, e chi non
  li sa distinguere non deve giudicare.

  ⛔⛔ **MA L'ESITO DELLA MAGLIA NON E' «3 comunque», ed e' una correzione.**
  La prima stesura usciva 3 sempre: ⚠ cosi' non distingueva *«il banco ha girato
  e il desktop era davvero fermo»* da *«non e' partito niente»* — un contenitore
  rotto dava lo stesso codice d'uscita del controllo riuscito, e cinque minuti
  di sessione producevano un bit che non poteva variare (§1.44).
  ⇒ ⭐ Adesso `--scena-ferma` **asserisce**, e pretende tre cose insieme:

      · il palco e' nato          (⇒ il giro e' davvero avvenuto)
      · il cliente e' stato ammesso
      · e il verdetto e' «non lo so» **per la ragione giusta** (motivo
        `scena-ferma`), non per un'altra

    ⇒ `0` il controllo negativo REGGE · `1` ⛔ a scena ferma la maglia ha dato
      un verdetto, cioe' e' rotta · `3` il giro non e' avvenuto e non ho
      controllato niente.
  ⭐ E quel giro lascia il numero con cui si tara `--ritmo-minimo`: quanti
    fotogrammi consegna davvero un desktop fermo **dentro la scatola**.

---------------------------------------------------------------------------
⭐ I TRE CONTROLLI, e non hanno lo stesso peso
---------------------------------------------------------------------------

  1. **fotogrammi > 0** — il canarino piu' povero.  ⛔ Vale solo perche' la
     scena e' in movimento (vedi sopra): a scena ferma lo zero e' giusto.

  2. **il ritmo non e' crollato** rispetto a un **riferimento grezzo**.
     ⛔⛔ E QUI IL LIMITE VA DICHIARATO, o il numero inganna:
       · il riferimento e' `[M]` **39,0 fotogrammi/s** — fase 9 §3.1, ⚠ **sul
         ferro vero, non nella scatola**, e con la scheda tutta per se';
       · il ritmo che questa maglia calcola e' **LORDO**, e vale la pena dire
         come: al **numeratore** ci sono TUTTI i fotogrammi del flusso —
         quelli della nascita del desktop compresi, perche' il cliente scrive
         un file solo e da un flusso H.264 senza marcatempo non si taglia un
         pezzo — mentre al **denominatore** c'e' **solo la finestra in cui la
         scena si muoveva**.  ⇒ Il ritmo e' **sovrastimato**, cioe' ⛔ **questo
         controllo e' OTTIMISTA**: puo' lasciar passare un crollo, non puo'
         inventarne uno.  ⚠ E' il verso giusto in cui sbagliare (un rosso
         falso spegne la rete, §1.3), ⛔ ma e' anche la ragione per cui il
         ritmo non e' quello che decide.
       · ⚠⚠ E **di quanto** sovrastimi non lo so, e va detto invece di
         inventare un limite.  Fuori dalla finestra il desktop e' fermo
         (`[M]` 0,03 fotogrammi/s, fase 9 §3.1) ⛔ **ma l'applicazione ci sta
         nascendo dentro**, e una finestra che si apre disegna eccome.  ⇒ Il
         termine in piu' e' «i fotogrammi che il compositore ha disegnato
         mentre la scena si avviava», che nessuno ha misurato: `[?]`.
         ⭐ La maglia stampa sempre i fotogrammi, i secondi e il ritmo: sono i
           tre numeri con cui quel `[?]` si chiude, e vanno guardati al primo
           giro verde.
       · ⇒ La soglia `--ritmo-minimo` e' **larga apposta**: separa *«arriva un
         rivolo»* da *«non arriva niente»*, ⛔ **non giudica la fluidita'**.
         La fluidita' e' giudizio dell'utente (I8) e §6 la mette fuori dalla
         rete.  ⚠ `[?]` **Da ritarare nella scatola**, misurando il ritmo vero.

  3. ⭐⭐ **I FOTOGRAMMI CONSECUTIVI SONO DIVERSI FRA LORO** — ed e' il
     controllo che decide.  ⛔ Non ha il difetto del ritmo: guarda **solo gli
     ultimi fotogrammi**, che per costruzione stanno dentro la finestra in cui
     la scena si muoveva.
     ⇒ E' l'unico dei tre che prende l'**immagine congelata**: la marca c'e',
       lo schermo e' pieno, il ritmo e' alto, ⛔ e non si aggiorna niente
       (§4.3, la terza riga della tabella «la marca da sola non basta»).

---------------------------------------------------------------------------
⛔ COME SO CHE SA DARE ROSSO — due guasti innestati, e sono di due nature
---------------------------------------------------------------------------

  `--fotogramma-ripetuto`   ⭐ IL GUASTO DELL'IMMAGINE CONGELATA.  Si prende la
                            presa VERA e si sfregia **la copia in memoria**
                            dell'elenco dei fotogrammi: al posto della sequenza
                            si mettono N copie del primo.  ⛔ Il flusso sul
                            disco non si tocca — e' la stessa forma che C9 usa
                            (`--togli-nome`), e il controllo sano e il guasto
                            girano sugli **stessi dati**.  ⇒ Un inquilino solo.
                            ⛔⛔ E QUI VA DETTA UNA COSA che un revisore ha
                            trovato e aveva ragione: **lo sfregio, da solo, non
                            puo' fallire** — se il sano e' verde, ripetere lo
                            stesso fotogramma da' per forza zero coppie
                            diverse.  E' aritmetica, ed e' gia' provata da
                            `--certifica` in tre decimi di secondo.  ⇒ Un giro
                            sul vero che asserisse solo quello spenderebbe una
                            sessione per un bit gia' noto: `LEZIONI.md` §1.44
                            travestito da collaudo.
                            ⭐ Percio' quel giro pretende **una cosa in piu' che
                            puo' davvero fallire**: che la coppia consecutiva
                            **piu' debole** del giro sano stia almeno
                            `MARGINE_SOGLIA` volte sopra la soglia.  ⇒ E' una
                            misura del MONDO — quanto e' vivace la scena vera
                            dopo la codifica — e se un giorno scendesse, si
                            vedrebbe **prima** che la maglia cominci a dare
                            rossi falsi.  ⚠ E' quel che C5 fa col margine
                            dell'RMS.

  `--codificatore-fermo`    ⛔ IL GUASTO VERO, sul prodotto.  ⭐⭐ **Appena la
                            scena si e' vista muovere** — non prima — si manda
                            **SIGSTOP** al processo dell'inquilino che
                            codifica e consegna.
                            ⛔⛔ E QUEL «NON PRIMA» E' UNA CURA DEL 27 AGOSTO
                            2026, non un dettaglio.  Fino a quel giorno
                            l'innesto stava **prima** che la scena si
                            accendesse: il codificatore moriva su un desktop
                            vuoto, la scena dichiarata non compariva mai, e la
                            maglia diceva — ⭐ onestamente — *«la scena che ho
                            dichiarato NON e' sullo schermo»* ⇒ esito **3**.
                            ⇒ Non era un difetto del prodotto e non era un
                            rosso: era ⛔ **un collaudo che non collaudava**,
                            perche' il guasto era innestato nel momento
                            sbagliato della storia.  ⭐ Il guardiano non si e'
                            toccato — e' quello che ha fatto vedere il difetto
                            invece di passarlo per verde: si e' spostato
                            l'innesto.
                            ⭐ «Si e' vista muovere» e' una MISURA e non una
                            fiducia: si guarda il **lavoro del codificatore**,
                            cioe' del processo che si sta per fermare.  ⛔ Non
                            i byte sul disco: il file dei fotogrammi il cliente
                            lo scrive **solo alla fine** (`[R]`
                            `01-b3-cliente.py:1416`).  ⚠ E non il lavoro del
                            cliente: `[M]` 27 ago 2026, col desktop in
                            movimento ne brucia 0,06 CPU/s, troppo poco per
                            distinguerlo da un cliente fermo senza inventare
                            una soglia sottile.  ⚠ E il nome va detto giusto:
                            **non si ferma «il solo codificatore»**, si ferma
                            il processo che lo contiene — e' quanto si puo'
                            fare senza toccare il prodotto, e la differenza e'
                            dichiarata invece che nascosta.
                            ⇒ Due inquilini: uno sano (controllo) e uno
                              guastato.

⛔⛔ E OGNI GUASTO PORTA CON SE' IL SUO CONTROLLO SANO — `LEZIONI.md` §1.52:
   *non basta il colore del verdetto; una maglia deve distinguere «il guasto ha
   morso» da «era gia' rosso per conto suo»*.  ⇒ Si pretendono **tre** cose:

     · il controllo sano e' VERDE       (o il confronto non vale niente)
     · il guastato e' ROSSO
     · ⭐ la **differenza** e' misurabile:
         `--fotogramma-ripetuto`  le coppie diverse crollano a **zero**
         `--codificatore-fermo`   ⭐⭐ il **lavoro del cliente dentro la
                                  finestra** scende sotto una **QUOTA** di
                                  quello sano (`QUOTA_GUASTO`, un decimo).
                                  ⚠ Una quota e non una differenza assoluta:
                                  §1.45, un numero assoluto e' un numero preso
                                  da una condizione.
                                  ⛔⛔ E DAL 27 AGOSTO 2026 LA MISURA NON E'
                                  PIU' IL RITMO: il ritmo e' **lordo** (al
                                  numeratore ci sono anche i fotogrammi nati
                                  prima che la finestra si aprisse), e adesso
                                  che l'innesto e' spostato in fondo quei
                                  fotogrammi arrivano **anche col guasto**.
                                  ⇒ Su un numero sporco non si puo' pretendere
                                  il decimo: si pretende dove la misura e'
                                  netta — il lavoro del cliente, che ha
                                  numeratore e denominatore tutt'e due dentro
                                  la finestra.  ⚠ Il ritmo lordo si guarda lo
                                  stesso, con una quota sua e dichiarata
                                  (`QUOTA_LORDA`).

⚠ E ciascun guasto pretende anche la propria **firma**, o non e' quel guasto:
   col `--codificatore-fermo` almeno un processo dell'inquilino dev'essere
   davvero in stato **T** (fermato).  ⛔ Se non lo e', l'iniezione non ha
   toccato niente e il rosso — se c'e' — e' di qualcun altro.

⭐⭐ E IL `--codificatore-fermo` PRETENDE UNA COSA IN PIU', dal 27 agosto 2026:
   che il guasto sia caduto **nel momento giusto della storia**.  Tre fatti, e
   ciascuno si misura e puo' mancare:
     · i fotogrammi si erano visti ARRIVARE prima dell'innesto;
     · gli ULTIMI fotogrammi consegnati erano **diversi fra loro** — cioe' la
       scena si stava muovendo nell'istante in cui il codificatore e' morto;
     · la finestra era lunga abbastanza perche' i fotogrammi nati prima
       dell'innesto non bastassero da soli a far sembrare vivo il flusso
       (`finestra_bastante`, e il conto si rifa' **coi numeri veri del giro**).
   ⛔ Se una manca, l'esito e' **3**: dire «il guasto non e' stato visto»
      sarebbe accusare la rete per un collaudo che non e' girato.

⛔⛔ E se la firma manca, l'esito e' **3**, non un rosso: una maglia che non ha
   potuto innestare il guasto non ha ne' visto ne' mancato niente, e scrivere
   *«il guasto NON e' stato visto»* sarebbe **un'accusa a una prova che non e'
   girata**.  ⇒ E' la stessa cura che `11-gancio.sh` si e' data il 27 agosto
   2026 sul proprio `3`.

---------------------------------------------------------------------------
⛔ I TETTI — sono argomenti, e vanno RITARATI SUL VERO
---------------------------------------------------------------------------

`LEZIONI.md` §1.45: *ogni attesa ha un nome suo e un valore suo*.  ⛔ Nessuno
dei numeri qui sotto e' stato misurato da chi ha scritto questo file.

  `--attesa-palco 60`    quanto si aspetta che il compositore annunci un
                         `wl_output`.  `[M]` (misura di C1, 27 agosto 2026,
                         **non mia**) nella scatola GNOME: 98,0 · 101,0 · 95,5 s
                         ⇒ massimo 101,0.  ⛔ E quel ritardo e' della **scatola**
                         (`polkit` che non parte, `Contenitore.gnome` §6-bis),
                         non del prodotto: curato quello il palco nasce in ~2 s
                         come nelle altre tre scatole ⇒ **rimettere a ~20 s**.
                         ⚠ La maglia stampa sempre quanto ci ha messo davvero.
  `--attesa-scena 30`    quanto si da' alla scena per essere sullo schermo.
                         `[?]` — il primo avvio del browser in una scatola
                         fredda passa i 25 s (`[M]` C8, 26 ago 2026).
  `--finestra 45`        quanti secondi si guarda la scena in movimento.
  `--ritmo-minimo 4.0`   `[?]` ⇒ ~10 % del riferimento grezzo.  Vedi sopra:
                         larga apposta, e non giudica la fluidita'.

---------------------------------------------------------------------------
⛔ QUEL CHE QUESTA MAGLIA **NON** GUARDA
---------------------------------------------------------------------------

  · ⛔ **Non guarda la fluidita'**, ne' il ritardo, ne' la qualita'
    dell'immagine: sono grandezze della fase 9, e §6 le tiene fuori dalla rete.
  · ⛔ **Non dimostra che la scena si muovesse davvero.**  Misura che il
    programma che la muove era **vivo** dall'inizio alla fine e che uno dei due
    colori dichiarati era sullo schermo.  ⚠ Se la scena si fosse bloccata da
    sola con un colore in vista, C3 direbbe rosso al prodotto per una cosa del
    browser.  ⇒ `[?]` **da tarare sul vero**: la prima volta che questa maglia
    da' rosso, si guarda il PNG che lascia in `--lavoro` prima di credere.
  · ⚠ **Non e' cieca al programma**: come C2, oggi usa `firefox-esr`, l'unico
    programma della scatola che sappia dipingere una scena che decidiamo noi.
    ⇒ `--applicazione` e `--argomenti` esistono per spostarla altrove.
  · ⛔ **Non guarda l'audio** (e' C5) ne' l'input (e' C4).

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: i fotogrammi arrivano e la scena CAMBIA
     (col guasto innestato: ⭐ **il guasto e' stato visto**)
     (con `--scena-ferma`: ⭐ **il controllo negativo regge**)
  1  ho guardato: non arrivano, o sono crollati, o l'immagine e' CONGELATA
  3  ⛔ non ho potuto guardare — il palco non e' nato, la scena dichiarata non
     era sullo schermo, il cliente non e' stato ammesso, il decodificatore ha
     lasciato un elenco troncato.  ⛔ E NON e' un rosso.
     ⚠ Col guasto innestato, **3** vuol dire anche *«l'iniezione non ha
     preso»*: ne' una certificazione ne' un'accusa alla rete
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import glob
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ IL METRO, DICHIARATO QUI E STAMPATO IN OGNI ESITO
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ I due colori della scena dichiarata — ⛔ **gli stessi di `11-c3-scena.html`**.
#    Se qualcuno ne cambia uno di la' e non di qua, questa maglia dira' «la scena
#    che ho dichiarato non e' sullo schermo» ⇒ **3**, non un rosso al prodotto.
SCENA_A = (0x00, 0x00, 0xFF)      # blu
SCENA_B = (0xFF, 0xFF, 0x00)      # giallo
# ⛔ La tolleranza per canale: stessa grandezza e stesso valore di C8 — lo
#    scostamento di un colore dichiarato dopo lo stesso percorso (compositore →
#    cattura → H.264 4:2:0 → cliente).  ⚠ Non e' un tetto preso in prestito
#    (`LEZIONI.md` §1.45): e' lo stesso numero per la stessa cosa.
# ⛔⛔ MA NON E' TARATO, e dirlo sarebbe §1.50.  `--certifica` lo attraversa **al
#     bordo** — ±48 dev'essere ancora la scena, ±49 no — su immagini
#     **sintetiche**, che non hanno mai visto ne' la codifica in 4:2:0 ne' un
#     profilo di colore.  ⇒ Si prova che il confronto cade dove dice di cadere,
#     non che 48 basti.
# ⚠⚠ E c'e' una ragione in piu' per diffidarne qui: C8 e' tarata sul **magenta**,
#    C3 chiede **blu puro** `#0000FF`, che ha luma 0,07 ed e' il caso peggiore
#    del sottocampiamento del croma.  ⇒ `[?]`, e si tara guardando la frazione
#    che la maglia stampa al primo giro verde.
TOLLERANZA = 48
# ⛔ Quanto schermo dev'essere di uno dei due colori perche' si dica «la scena
#    dichiarata e' quella che sto guardando».  ⚠ La banda nera ne copre il 20 %,
#    piu' la targa: 0,40 e' prudente in basso apposta.  `[?]`
FRAZIONE_SCENA = 0.40

# ⭐⭐ IL RIFERIMENTO GREZZO — `[M]` fase 9 §3.1, ⛔ **sul ferro vero, non nella
#     scatola**: 39,67 e 39,00 fotogrammi/s su due scene in movimento, contro
#     **0,03** a scena ferma.  ⇒ Il valore usato e' il piu' basso dei due.
RIFERIMENTO_FPS = 39.0
# ⛔ Sotto quanti fotogrammi al secondo si dice «crollati».  `[?]` ~10 % del
#    riferimento: larga apposta (vedi in testa), e da ritarare nella scatola.
RITMO_MINIMO = 4.0

# ⛔ Quando due fotogrammi sono DIVERSI — due numeri, e servono tutt'e due.
#    · sotto `SOGLIA_RUMORE` livelli su un canale, un pixel «non e' cambiato»:
#      e' il rumore di quantizzazione della codifica, non movimento.  `[?]`
#    · e i pixel cambiati devono essere almeno `SOGLIA_COPPIA` dell'immagine,
#      o basterebbe un cursore che lampeggia per dichiarare viva una scena morta.
SOGLIA_RUMORE = 12
SOGLIA_COPPIA = 0.01
# ⛔ Quante coppie devono essere diverse perche' la scena «cambi».  ⚠ La scena
#    dichiarata e' fatta per farle differire TUTTE (la banda si sposta a ogni
#    fotogramma): 0,50 lascia mezzo margine alla cadenza della cattura.  `[?]`
FRAZIONE_COPPIE = 0.50
# Quante coppie si guardano, in fondo alla presa.
COPPIE_ESAMINATE = 60

# ⭐⭐ Col guasto innestato: quanto deve CROLLARE la misura NETTA perche' si
#   possa dire «il guasto ha morso» invece di «il verdetto e' cambiato».
#   `LEZIONI.md` §1.52.
# ⛔⛔ E DAL 27 AGOSTO 2026 LA MISURA NETTA NON E' PIU' IL RITMO, ma **il lavoro
#     del cliente dentro la finestra** — vedi `QUOTA_LORDA` qui sotto e
#     `finestra_bastante`.  Il ritmo e' lordo, cioe' si porta dentro i
#     fotogrammi nati prima dell'innesto; il lavoro del cliente ha numeratore e
#     denominatore tutt'e due dentro la finestra, ⇒ e' l'unico dei due su cui si
#     puo' pretendere un decimo senza barare.
# ⚠⚠ Ed e' una QUOTA del ritmo sano, non una differenza in fotogrammi/s — e la
#    ragione e' §1.45: una differenza assoluta («almeno 10/s in meno») e' un
#    numero preso da una condizione.  ⛔ Nella scatola la scheda e' condivisa con
#    tre altre scatole e il ritmo sano potrebbe essere 12/s invece di 39: allora
#    un margine di 10/s comincerebbe a dire «il guasto non ha morso» su un
#    guasto che l'ha fermato del tutto.  ⇒ Una quota si porta dietro la sua scala.
# ⭐ E non e' un predicato che non puo' fallire: il ritmo sano dev'essere gia'
#   sopra `--ritmo-minimo` (4,0/s) per essere verde, ⇒ col guasto si pretende
#   meno di 0,4/s, che e' il ritmo di un desktop fermo ([M] 0,03/s, fase 9 §3.1).
QUOTA_GUASTO = 0.10

OUTPUT_MINIMI = 1
FIRMA_OUTPUT = re.compile(r"interface:\s*'wl_output'")

# ⛔⛔ E LA FIRMA DELL'AMMISSIONE E' UNA RIGA INTERA, NON UNA PAROLA.
#    `[R]` `01-b3-cliente.py:1615` scrive «   AMMESSO dopo 1023 ms» quando va
#    bene, e «CONGEDO invece di AMMESSO: …» / «atteso AMMESSO, arrivato …»
#    quando va male — ⛔ tutt'e tre sullo **stdout** (`:2560`) ⇒ `"AMMESSO" in
#    testo` sarebbe **vero in tutt'e tre i casi**: un predicato che non puo'
#    dire di no (`LEZIONI.md` §1.44), proprio nei casi che esiste per prendere.
# ⭐⭐ Dal 27 agosto 2026 la regola sta in `11-c1…py` e ci sta **una volta
#     sola**, per tutte e nove le maglie (§1.47): vedi `e_stato_ammesso()`.

# ⭐ Quanto deve stare LARGA la coppia piu' debole del giro sano rispetto alla
#   soglia, perche' si possa dire che la scena e' abbastanza vivace da provare
#   qualcosa.  ⛔ E' il numero che rende NON VUOTO il giro col guasto
#   «fotogramma ripetuto» (vedi in testa): senza, quel giro asserisce solo cose
#   gia' certificate.  ⚠ `[?]` — 2× e' prudente, e si tara guardando il
#   `margine` che la maglia stampa a ogni giro.
MARGINE_SOGLIA = 2.0

# ⛔ Se il decodificatore ne tira fuori molti meno di quanti il cliente ne
#    dichiara, il flusso e' stato troncato e il conto non e' quello del
#    prodotto: e' «non ho potuto guardare».  `[?]`
QUOTA_ESTRATTI = 0.50

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «I FOTOGRAMMI STANNO ARRIVANDO ADESSO?» — il segnale VIVO, e serve a
#    decidere **quando** innestare il guasto (27 agosto 2026, vedi in testa).
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ Il flusso sul disco non aiuta: `[R]` `01-b3-cliente.py:1416` — il cliente
#    tiene i fotogrammi in memoria e scrive il file **una volta sola, alla
#    fine**.  ⇒ Durante il giro il file non esiste, e non si puo' guardare
#    quanti ne siano arrivati.
# ⭐ Quel che invece si vede vivo e' il LAVORO DEL CODIFICATORE — cioe' del
#   processo che si sta per fermare: `ps -o times=`.  Comprimere 1920x1080
#   costa; ⛔ un desktop fermo non costa niente (`[M]` fase 9 §3.1: 0,03
#   fotogrammi/s).
# ⛔⛔ E NON SI GUARDA IL CLIENTE, e la ragione e' una MISURA e non un gusto:
#     `[M]` 27 agosto 2026, scatola gnome, col desktop in movimento il cliente
#     brucia **0,06 CPU/s**.  ⚠ Troppo poco: per distinguerlo da un cliente
#     attaccato a un desktop fermo ci vorrebbe una soglia sottile, cioe' un
#     numero che un giorno dice di si' e un giorno di no.
# ⚠ `[?]` — 0,10 secondi di CPU per secondo di orologio non e' tarato: e'
#   scelto molto sotto quel che ci si aspetta da una compressione 1080p, e la
#   maglia stampa **sempre** il valore vero, cosi' si tara guardando.
SOGLIA_CPU = 0.10
# ⭐ Ogni quanti secondi si guarda il lavoro del cliente.  ⛔ E' corto apposta:
#   fra l'istante in cui la scena comincia a dipingere e l'innesto ci stanno
#   **tutti** i fotogrammi che poi sporcano il ritmo lordo (vedi
#   `finestra_bastante`), ⇒ ogni secondo in piu' qui e' un fotogramma in piu'
#   che col guasto arriva lo stesso.
PASSO_CPU = 2.0

# ⛔ E il ritmo LORDO ha una quota **sua, piu' larga**, e la ragione va detta
#    invece di nasconderla: il suo numeratore contiene anche i fotogrammi nati
#    PRIMA della finestra, e col guasto innestato quelli restano tutti.  ⇒ Su
#    un numero sporco non si puo' pretendere lo stesso decimo che si pretende
#    su uno pulito: sarebbe una soglia che passa o non passa a seconda di
#    quanto e' stata svelta la scena a nascere.  `[?]`
# ⭐ Il decimo si pretende dove la misura e' netta (`QUOTA_LAVORO`); qui si
#   pretende solo che il ritmo lordo sia sceso **molto**, e il conto di quanto
#   ci si poteva aspettare lo fa `finestra_bastante`.
QUOTA_LORDA = 0.35


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔⛔ E DAL 27 AGOSTO 2026 IL PREDICATO NON E' PIU' QUI: sta in C1, e ci sta
        **una volta sola** per tutte e nove le maglie (§1.47).  ⚠ Questa maglia
        e C3 ce l'avevano giusto ma in copia propria; C1, C5, C6, C7 e C9 ce
        l'avevano SBAGLIATO — cinque volte la stessa riga, cinque volte lo
        stesso difetto.  ⇒ Due copie giuste sono comunque due posti da cui
        divergere il giorno che il cliente cambia la frase.
    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama esce **3**.
    """
    return casa_di_c1().e_stato_ammesso(coda)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GIUDICI SI IMPORTANO, NON SI RISCRIVONO
#
# ⛔ Due giudici che possono divergere in silenzio sono peggio di uno
#    (`banchi/10-f1-testimone.py`).  Qui se ne importano due:
#      `10-f1-testimone.py`  `giudica()`, per dire se un'immagine e' nera
#      `11-c8-…py`           `frazione_del_colore()`, gia' certificato, e prende
#                            colore e tolleranza come ARGOMENTI ⇒ si usa con i
#                            numeri di C3 senza ereditare quelli di C8
# ⭐ Il terzo giudice — «due fotogrammi sono diversi?» — non esiste da nessuna
#   parte, quindi nasce qui **ed e' certificato qui**.
# ═══════════════════════════════════════════════════════════════════════════
def _carica(nome_file, mestieri):
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, nome_file)
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location(
            "importato_" + re.sub(r"\W", "_", nome_file), perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None, perc
        for mestiere in mestieri:
            if not callable(getattr(m, mestiere, None)):
                return None, perc
        return m, perc
    return None, ""


def giudice_del_desktop():
    return _carica("10-f1-testimone.py", ("giudica",))


def lettore_del_colore():
    return _carica("11-c8-il-secondo-apre-il-browser.py", ("frazione_del_colore",))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ LA PROVVISTA CONDIVISA — `/tmp/mozilla`, e sta in UN POSTO SOLO
#
# `[M]` 27 agosto 2026, giro `--famiglia tutto` su tutt'e quattro le scatole,
#   binario `aa950804fed7`: C3 ⛔ **3** — «la scena che ho dichiarato NON e'
#   sullo schermo (0,0%)».  ⚠ E l'immagine giudicata diceva tutt'altro: la
#   sessione GNOME era **viva e dipinta**, ⛔ ma Firefox stava fermo sulla
#   **finestra di scelta del profilo**.
#
# ⇒ LA CAUSA: `/home/c3u1/.cache/mozilla` -> `/tmp/mozilla`, che era rimasto a
#   «c8u1» a modo 0700 — C8 e C8b, in `famiglia tutto`, girano PRIMA di me e
#   ⛔ non disfano lo scheletro che hanno messo.  ⛔ Nessuna delle due maglie
#   sbaglia da sola: e' l'ORDINE a romperle.
#
# ⛔⛔ E LA CURA NON PUO' STARE IN CHI MI ACCENDE: per un giorno e' stata in
#     `11-accendi.sh`, ⚠ ma una maglia che va «preparata da fuori» e', lanciata
#     a mano o da un altro gancio, una maglia che da' un **rosso falso**.
#
# ⭐⭐ E NON E' UNO SGOMBERO: e' la cura di `src/provisiona.sh` — una `~/.cache`
#     VERA all'inquilino che creo io.  ⛔ Cancellare il `/tmp/mozilla` di
#     un'altra maglia sarebbe un danno, e in parallelo (C14) la farebbe cadere.
#
# ⛔ Il codice sta in C2 e ⛔ non se ne fa una copia qui: la stessa regola in tre
#    file sono tre posti da cui divergere, ed e' l'errore che questa cura ripara.
# ⚠ Sta in C2 e non in C8 perche' C8 oggi non e' modificabile; ⭐ il giorno che lo
#   sara' si sposta accanto ad `applica_la_cura`, e questa riga cambia da sola.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_PROVVISTA = ("cura_della_provvista", "sgombra_il_mio_rimasuglio",
                       "certifica_la_provvista")
_PROVVISTA = None


def casa_della_provvista():
    global _PROVVISTA
    if _PROVVISTA is None:
        _PROVVISTA, _ = _carica("11-c2-una-finestra-si-apre.py",
                                _MESTIERI_PROVVISTA)
    return _PROVVISTA


def cura_della_provvista(chi):
    """⭐⭐ (fatto, perche') — e ⛔ se non regge NON e' un rosso: e' un **3**."""
    casa = casa_della_provvista()
    if casa is None:
        return False, ("non trovo `11-c2-una-finestra-si-apre.py` accanto a me: "
                       "da li' viene la cura della provvista, e ⛔ non se ne fa "
                       "una copia qui (§1.47)")
    return casa.cura_della_provvista(chi)


def sgombra_il_mio_rimasuglio(mio_base):
    """Toglie `/tmp/mozilla` ⛔ soltanto se e' rimasto a un inquilino MIO."""
    casa = casa_della_provvista()
    if casa is None:
        return "⚠ non trovo C2: non ho nemmeno guardato /tmp/mozilla"
    return casa.sgombra_il_mio_rimasuglio(mio_base)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 E' LA CASA DEI DUE PASSI COMUNI A TUTTE E NOVE LE MAGLIE — §1.47
#
# ⛔ Non e' comodita': e' che una riga ripetuta in nove file e' **nove posti da
#    cui divergere**, ed erano gia' divergiti.  Da `11-c1-nasce-e-si-vede.py`
#    vengono:
#
#   · `e_stato_ammesso(coda)`   — «il cliente e' stato AMMESSO?», che ⛔ non e'
#        la parola dentro un testo: il cliente la stampa anche nei DUE messaggi
#        di rifiuto, e sullo stdout (`01-b3-cliente.py:1315`, `:1322`, `:2560`).
#   · `garantisci_i_gruppi(chi)` — i gruppi dei nodi `/dev/dri`, ⛔ senza i
#        quali `[M]` la sessione nasce CIECA (0 su 4, zero fotogrammi,
#        `fasi/10-…` §7.4) e questa maglia misurerebbe il buio.
#
# ⛔ Se C1 non si carica si esce **3** e lo si dice: ⛔ non si ripiega in
#    silenzio su un giudizio piu' povero.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_C1 = ("e_stato_ammesso", "certifica_ammissione",
                "garantisci_i_gruppi", "verdetto_gruppi", "certifica_gruppi")
_C1 = None


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1, _perc = _carica("11-c1-nasce-e-si-vede.py", _MESTIERI_C1)
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   vengono il predicato dell'ammissione e la garanzia dei")
        print("   gruppi della scheda — che stanno in un posto solo (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — `(esito, perche)`; `0` = si puo' misurare.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica — E1, «scritto non e' in
       vigore».  ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid
       dai NODI e rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui.
    """
    return casa_di_c1().garantisci_i_gruppi(chi, prefisso)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL GIUDICE NUOVO: «questi due fotogrammi sono diversi?»
# ═══════════════════════════════════════════════════════════════════════════
def coppie_che_cambiano(elenco, soglia_rumore=SOGLIA_RUMORE,
                        soglia_coppia=SOGLIA_COPPIA):
    """Quante coppie consecutive di fotogrammi sono DIVERSE fra loro.

    Torna un dizionario, oppure ⛔ **`None`** se non ha potuto guardare
    (numpy/Pillow che mancano, meno di due immagini leggibili).
    ⚠ `None` non e' zero: *«non ho guardato»* e *«ho guardato e non cambiava»*
      sono due cose opposte, e questo progetto ha gia' pagato per averle confuse.

    ⛔ La distanza si prende **canale per canale** (norma del massimo) e non come
       somma: una somma lascerebbe passare un cambiamento grosso su un canale
       solo diluito dagli altri due.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    if not elenco or len(elenco) < 2:
        return None

    precedente = None
    coppie = diverse = illeggibili = 0
    minima = None
    massima = None
    for p in elenco:
        try:
            img = np.asarray(Image.open(p).convert("RGB")).astype("int16")
        except Exception:
            illeggibili += 1
            precedente = None      # ⛔ una coppia con un buco in mezzo non e' una coppia
            continue
        if img.ndim != 3 or img.size == 0:
            illeggibili += 1
            precedente = None
            continue
        if precedente is not None and precedente.shape == img.shape:
            scarto = abs(img - precedente).max(axis=2)
            quanti = float((scarto > soglia_rumore).mean())
            coppie += 1
            if quanti >= soglia_coppia:
                diverse += 1
            minima = quanti if minima is None else min(minima, quanti)
            massima = quanti if massima is None else max(massima, quanti)
        precedente = img

    if coppie == 0:
        return None
    return {"coppie": coppie, "diverse": diverse,
            "frazione": diverse / float(coppie),
            "minima": minima, "massima": massima,
            "illeggibili": illeggibili}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL GIUDIZIO — funzione PURA, cosi' `--certifica` la fa girare su
#    fotogrammi finti senza accendere niente.
# ═══════════════════════════════════════════════════════════════════════════
def giudica_il_flusso(elenco, secondi, scena_ferma=False,
                      ritmo_minimo=RITMO_MINIMO,
                      frazione_coppie=FRAZIONE_COPPIE,
                      coppie_esaminate=COPPIE_ESAMINATE,
                      soglia_rumore=SOGLIA_RUMORE,
                      soglia_coppia=SOGLIA_COPPIA):
    """Torna un dizionario con `stato` fra:

        "cambia"     ⭐ i fotogrammi arrivano e la scena cambia   ⇒ verde
        "congelata"     arrivano e NON cambiano                  ⇒ rosso
        "crollati"      non arrivano, o sono un rivolo           ⇒ rosso
        "non-lo-so"  ⛔ non ho potuto guardare                    ⇒ ne' l'uno
                     ne' l'altro
    """
    # ⭐⭐ E ACCANTO AL VERDETTO C'E' UN **MOTIVO**, che e' un fatto e non una
    #    frase.  ⛔ Senza, chi vuole sapere *perche'* «non lo so» dovrebbe
    #    leggere il testo di `perche` — cioe' decidere su una stringa, che e' il
    #    modo in cui un banco comincia a sbagliare in silenzio quando qualcuno
    #    corregge un refuso.  ⇒ Il collaudo del controllo negativo poggia su
    #    questo, non sulle parole.
    esito = {"stato": "non-lo-so", "motivo": "", "perche": "",
             "fotogrammi": None, "ritmo": None, "coppie": None,
             "diverse": None, "frazione_coppie": None, "minima": None,
             "massima": None, "illeggibili": None}
    if elenco is None:
        esito["motivo"] = "niente-elenco"
        esito["perche"] = "non ho potuto estrarre nessun fotogramma dal flusso"
        return esito

    n = len(elenco)
    esito["fotogrammi"] = n
    ritmo = (n / float(secondi)) if secondi and secondi > 0 else None
    esito["ritmo"] = ritmo

    # ═══════════════════════════════════════════════════════════════════════
    # ⚠⚠ IL CONTROLLO NEGATIVO — «scena ferma» NON DEVE DARE ROSSO.
    #
    # `[M]` fase 9 §3.1: a scena ferma escono **0,03 fotogrammi/s** — in 30
    # secondi UNO, la chiave d'apertura.  `[R]` `src/figlio.c:3373`: *«zero
    # fotogrammi su una scena ferma e' un RISULTATO, non un difetto»*.
    # ⇒ ⛔ Un'immagine congelata e un desktop che non ha niente da mostrare hanno
    #   lo stesso identico aspetto.  Chi non li sa distinguere non giudica.
    # ⚠ E questo ramo esce PRIMA di ogni altro controllo apposta: non e' una
    #   scorciatoia, e' la dichiarazione che in questa condizione la maglia non
    #   ha un metro.
    # ═══════════════════════════════════════════════════════════════════════
    if scena_ferma:
        esito["motivo"] = "scena-ferma"
        esito["perche"] = (
            "la scena era FERMA per mia scelta: %d fotogrammi, ritmo %s. "
            "⛔ A scena ferma il prodotto non consegna nulla ed e' giusto cosi' "
            "([M] fase 9 §3.1: 0,03 fotogrammi/s; [R] src/figlio.c:3373) ⇒ "
            "«immagine congelata» e «niente da mostrare» qui hanno lo stesso "
            "aspetto, e non li distinguo"
            % (n, "non lo so" if ritmo is None else "%.2f/s" % ritmo))
        return esito

    # ── 1. il canarino piu' povero ─────────────────────────────────────────
    if n == 0:
        esito["stato"] = "crollati"
        esito["motivo"] = "zero-fotogrammi"
        esito["perche"] = ("nessun fotogramma e' arrivato, e la scena era in "
                           "movimento: e' il canarino che muore")
        return esito

    # ── 2. il ritmo, contro il riferimento grezzo ──────────────────────────
    if ritmo is None:
        esito["motivo"] = "niente-secondi"
        esito["perche"] = "non so su quanti secondi contare: non calcolo un ritmo"
        return esito
    if ritmo < ritmo_minimo:
        esito["stato"] = "crollati"
        esito["motivo"] = "ritmo-crollato"
        esito["perche"] = ("%d fotogrammi in %.0f s = %.2f/s, sotto i %.2f/s "
                           "pretesi (riferimento grezzo [M] %.1f/s, fase 9 §3.1 "
                           "⇒ %.0f%% del riferimento)"
                           % (n, secondi, ritmo, ritmo_minimo, RIFERIMENTO_FPS,
                              ritmo / RIFERIMENTO_FPS * 100))
        return esito

    # ── 3. ⭐ il controllo che decide: i consecutivi sono diversi? ──────────
    coda = elenco[-(coppie_esaminate + 1):]
    m = coppie_che_cambiano(coda, soglia_rumore, soglia_coppia)
    if m is None:
        esito["motivo"] = "niente-coppie"
        esito["perche"] = ("non ho potuto confrontare i fotogrammi fra loro "
                           "(meno di due leggibili, o manca numpy/Pillow)")
        return esito
    esito.update({"coppie": m["coppie"], "diverse": m["diverse"],
                  "frazione_coppie": m["frazione"],
                  "minima": m["minima"], "massima": m["massima"],
                  "illeggibili": m["illeggibili"]})
    if m["frazione"] < frazione_coppie:
        esito["stato"] = "congelata"
        esito["motivo"] = "congelata"
        esito["perche"] = ("⛔ IMMAGINE CONGELATA: solo %d coppie su %d sono "
                           "diverse (%.0f%%, ne pretendo il %.0f%%) — i "
                           "fotogrammi arrivano e sono sempre lo stesso"
                           % (m["diverse"], m["coppie"], m["frazione"] * 100,
                              frazione_coppie * 100))
        return esito

    esito["stato"] = "cambia"
    esito["motivo"] = "cambia"
    # ⭐⭐ E IL MARGINE SI STAMPA SEMPRE, anche quando e' verde — e' l'unica cosa
    #    che avvisa PRIMA che una soglia diventi un rosso falso.  ⚠ E' quel che
    #    fa C5 (`11-c5…py`: *«la maglia stampa sempre il margine»*), e la prima
    #    stesura di C3 il numero se lo calcolava e lo buttava via.
    esito["perche"] = ("%d fotogrammi in %.0f s = %.2f/s (%.0f%% del "
                       "riferimento grezzo) · %d coppie su %d sono diverse · "
                       "⭐ la coppia piu' debole cambia il %.2f%% dei pixel, "
                       "cioe' %.1f volte la soglia (%.0f%%)"
                       % (n, secondi, ritmo, ritmo / RIFERIMENTO_FPS * 100,
                          m["diverse"], m["coppie"], (m["minima"] or 0) * 100,
                          (m["minima"] or 0) / soglia_coppia,
                          soglia_coppia * 100))
    return esito


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL LAVORO DEL CLIENTE — funzioni PURE, cosi' `--certifica` le attraversa
#    senza accendere niente.
# ═══════════════════════════════════════════════════════════════════════════
def cpu_dalla_riga(testo, tick=100.0):
    """I secondi di CPU bruciati da un processo, da una riga di `/proc/<pid>/stat`.

    ⛔⛔ E IL NOME DEL COMANDO STA FRA PARENTESI E **PUO' CONTENERE SPAZI** —
        `[R]` `proc(5)`.  Un processo che si chiamasse «(a b)» sposterebbe di
        uno tutti i campi, e questa funzione tornerebbe il numero sbagliato
        senza dirlo.  ⇒ Si taglia dopo l'**ultima** parentesi chiusa, e da li'
        in poi i campi sono posizionali per davvero.
    ⚠ Dopo la `)` il primo campo e' `state`, cioe' il **terzo** di `proc(5)`:
      `utime` e' il 14° ⇒ indice 11, `stime` il 15° ⇒ indice 12.
    ⛔ Torna **None** se la riga non si lascia leggere: «non lo so» non e' zero,
       e questa maglia ha gia' pagato per averli confusi.
    """
    if not testo or ")" not in testo or not tick:
        return None
    campi = testo.rsplit(")", 1)[1].split()
    if len(campi) < 13:
        return None
    try:
        return (int(campi[11]) + int(campi[12])) / float(tick)
    except (ValueError, ZeroDivisionError):
        return None


def lavoro_al_secondo(prima, dopo, secondi):
    """⭐ Quanta CPU al secondo fra due letture.  ⛔ `None` = non lo so.

    ⚠ E non si lascia mai andare sotto zero: un processo che rinasce con lo
      stesso pid darebbe un numero negativo, che non e' una misura.
    """
    if prima is None or dopo is None or not secondi or secondi <= 0:
        return None
    return max(0.0, (dopo - prima) / float(secondi))


def cpu_del_cliente(pid):
    """I secondi di CPU del processo `pid`, letti adesso.  `None` se non si sa."""
    try:
        with open("/proc/%d/stat" % pid, "rb") as f:
            testo = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    return cpu_dalla_riga(testo, float(os.sysconf("SC_CLK_TCK")))


def somma_lavoro(testo, nome):
    """⭐ PURA: i secondi di CPU dei processi il cui comando contiene `nome`.

    Legge l'uscita di `ps -o times=,args=`.
    ⛔ Torna **None** se non ce n'e' nemmeno uno: *«non c'e' nessun
       codificatore»* e *«il codificatore non lavora»* sono due cose opposte, e
       questo progetto ha gia' pagato per averle confuse.
    ⚠ E si somma **solo** chi ha `nome` nella riga di comando: contare tutti i
      processi dell'inquilino sarebbe un predicato un livello troppo in alto
      (`LEZIONI.md` §1.44), lo stesso difetto di `ferma_il_codificatore`.
    """
    if not testo:
        return None
    totale = None
    for riga in testo.splitlines():
        pezzi = riga.split(None, 1)
        if len(pezzi) < 2 or nome not in pezzi[1]:
            continue
        try:
            secondi = int(pezzi[0])
        except ValueError:
            continue
        totale = secondi if totale is None else totale + secondi
    return None if totale is None else float(totale)


def cpu_del_codificatore(chi, nome):
    """⭐⭐ IL LAVORO DEL CODIFICATORE — ed e' **il processo che si sta per
    fermare**, non un altro.

    ⛔⛔ E QUI SI GUARDA LUI E NON IL CLIENTE, e la ragione e' una MISURA.
        `[M]` 27 agosto 2026, scatola gnome: col desktop in movimento il
        cliente brucia **0,06 CPU/s** — troppo poco per distinguerlo da un
        cliente attaccato a un desktop fermo senza inventare una soglia sottile.
        ⭐ Il codificatore invece **comprime 1920x1080**: il suo lavoro e' di
          un altro ordine di grandezza, e a scena ferma e' quasi zero
          (`[M]` fase 9 §3.1: 0,03 fotogrammi/s).
    ⇒ E' anche la grandezza giusta per la domanda: prima di fermare un
      codificatore si vuole sapere se **quel** codificatore stava lavorando.
    """
    r = sh("ps -u %s -o times=,args=" % chi, secondi=30)
    return somma_lavoro(r.stdout or "", nome)


def secondi_in_vista(quanto, passo, soglia, cpu_al_s):
    """⭐⭐ QUANTA SCENA E' PASSATA IN VISTA PRIMA DELL'INNESTO — un TETTO, e
    ricavato da misure invece che scelto.

    ⛔ E' il termine che sporca il ritmo lordo: i fotogrammi nati fra l'istante
       in cui la scena ha cominciato a dipingere e l'istante dell'innesto
       arrivano **anche col guasto**, perche' il guasto e' venuto dopo.

    Come si limita, senza inventare:
      · nell'intervallo in cui il lavoro ha ATTRAVERSATO la soglia la scena
        puo' aver dipinto per tutto l'intervallo ⇒ al piu' `passo` secondi;
      · in tutti gli intervalli PRIMA il lavoro stava **sotto la soglia**, cioe'
        sotto `soglia / cpu_al_s` della consegna piena ⇒ al piu'
        `soglia × (quanto − passo) / cpu_al_s` secondi equivalenti.

    ⇒ Torna la somma.  ⛔ `None` se uno dei numeri non si sa: un tetto inventato
      sarebbe peggio di nessun tetto.
    """
    if quanto is None or cpu_al_s is None or not cpu_al_s or cpu_al_s <= 0:
        return None
    if passo is None or soglia is None or passo <= 0 or soglia < 0:
        return None
    return passo + soglia * max(0.0, quanto - passo) / float(cpu_al_s)


def finestra_bastante(secondi_prima, ritmo_sano, ritmo_minimo=RITMO_MINIMO):
    """⭐⭐ QUANTO DEVE ESSERE LUNGA LA FINESTRA perche' il guasto possa MORDERE.

    ⛔⛔ E questa e' la cosa che il 27 agosto 2026 mancava, ed e' la ragione per
        cui l'innesto stava nel posto sbagliato della storia.

    Il ritmo e' **lordo**: al numeratore ci sono TUTTI i fotogrammi del flusso,
    compresi quelli nati prima che la finestra si aprisse; al denominatore c'e'
    la sola finestra.  ⇒ Col codificatore fermo il numeratore non e' zero: e'
    `secondi_prima × ritmo_sano`, cioe' quel che la scena ha fatto in vista fra
    l'istante in cui ha cominciato a dipingere e l'istante dell'innesto.

    ⇒ Perche' la maglia possa dire «crollati» ci vuole:

        secondi_prima × ritmo_sano / FINESTRA  <  ritmo_minimo

    ⭐ Torna i secondi di finestra che servono.  ⛔ `None` se non si sa (e
       allora non si finge un numero).
    """
    if secondi_prima is None or ritmo_sano is None or not ritmo_minimo:
        return None
    if secondi_prima <= 0 or ritmo_sano <= 0 or ritmo_minimo <= 0:
        return None
    return secondi_prima * ritmo_sano / float(ritmo_minimo)


def aspetta_che_i_fotogrammi_arrivino(leggi, tetto, soglia=SOGLIA_CPU,
                                      passo=PASSO_CPU):
    """⭐⭐ ASPETTA CHE LA SCENA SI VEDA MUOVERE — e non un tempo fisso.

    ⛔ E' il passo che sostituisce `time.sleep(--attesa-scena)`: `--attesa-scena`
       da attesa diventa **TETTO**, e il giro va avanti appena i fotogrammi
       arrivano davvero invece che a orologio.  `LEZIONI.md` §1.45.
    ⚠ `leggi()` torna i secondi di CPU bruciati finora da chi consegna, oppure
      `None`.  ⛔ Non si guardano i byte sul disco: il file dei fotogrammi il
      cliente lo scrive **solo alla fine** (`[R]` `01-b3-cliente.py:1416`),
      quindi durante il giro non c'e' niente da pesare.

    Torna `(visto, lavoro_al_s, secondi_attesi)` — `visto` e' `True`, `False`
    (il tetto e' scaduto) oppure ⛔ `None` (non ho potuto leggere il lavoro).
    """
    partito = time.time()
    prima = leggi()
    if prima is None:
        return None, None, 0.0
    migliore = 0.0
    while time.time() - partito < tetto:
        t0 = time.time()
        time.sleep(passo)
        dopo = leggi()
        quanto = lavoro_al_secondo(prima, dopo, time.time() - t0)
        prima = dopo
        if quanto is None:
            # ⛔ Chi consegnava non c'e' piu', o non si lascia leggere.
            return None, migliore, round(time.time() - partito, 1)
        migliore = max(migliore, quanto)
        if quanto >= soglia:
            return True, quanto, round(time.time() - partito, 1)
    return False, migliore, round(time.time() - partito, 1)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ E si dichiara che cosa copre e che cosa no.

    COPRE tre cose, e la terza e' quella che si dimentica:
      1. **i due giudici** — quello nuovo («due fotogrammi sono diversi?») e
         quello del flusso: che una sequenza di fotogrammi identici sia ROSSA,
         che *«scena ferma»* non lo sia mai, che «non ho potuto guardare» torni
         «non lo so» e non zero, ⭐ e che le quattro soglie siano attraversate
         **al bordo**, un livello sopra e uno sotto;
      2. ⭐ **«il cliente e' stato AMMESSO?»**, che non e' una parola dentro un
         testo;
      3. ⭐⭐⭐ **i tre GIUNTI**: i codici d'uscita dei due guasti innestati e del
         controllo negativo, che sono **invertiti** e da cui C13 ricava se la
         rete sa ancora dare rosso.  ⛔ E' il pezzo che `LEZIONI.md` §1.52 e'
         nata per, e che nessuna delle due certificazioni di allora copriva.
    ⛔ NON COPRE, e va detto perche' e' la meta' che conta:
      · che la scena si muova davvero sullo schermo, ne' che il prodotto
        consegni — quello lo dicono i guasti innestati **sul vero**;
      · ⚠⚠ **che le cinque soglie siano nel PUNTO giusto.**  Qui le immagini
        sono sintetiche e non hanno mai attraversato ne' la codifica H.264 in
        4:2:0 ne' un profilo di colore.  ⇒ Si prova che ogni confronto **cade
        dove dice di cadere**, ⛔ non che il punto sia quello buono.  Restano
        `[?]`, e si tarano coi numeri che la maglia stampa a ogni giro.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("⛔ mancano numpy o Pillow: non posso nemmeno certificarmi")
        print("   ⇒ non ho potuto guardare")
        return 3
    import tempfile

    lettore, dove_l = lettore_del_colore()
    giudice, dove_g = giudice_del_desktop()
    if lettore is None or giudice is None:
        print("⛔ non trovo (o non regge) uno dei due giudici importati:")
        print("   10-f1-testimone.py    : %s" % (dove_g or "non trovato"))
        print("   11-c8-…apre-il-browser: %s" % (dove_l or "non trovato"))
        print("   ⇒ non ho potuto guardare")
        return 3

    lav = tempfile.mkdtemp(prefix="c3cert-")
    L, A = 128, 72

    def sequenza(nome, quanti, disegna):
        """Scrive `quanti` PNG e ne torna l'elenco.  `disegna(i)` -> array."""
        dove = os.path.join(lav, nome)
        os.makedirs(dove, exist_ok=True)
        fuori = []
        for i in range(quanti):
            p = os.path.join(dove, "f-%05d.png" % i)
            Image.fromarray(disegna(i)).save(p)
            fuori.append(p)
        return fuori

    def fondo(colore):
        a = np.zeros((A, L, 3), dtype="uint8")
        a[:, :] = colore
        return a

    def scena(i):
        """La scena dichiarata: il fondo che si alterna e la banda che scorre.

        ⚠ E' la copia sintetica di `11-c3-scena.html`, e i due numeri — il 3 %
          del passo e il 20 % della larghezza — devono restare **gli stessi**:
          se divergono, la certificazione prova una scena che nessuno mette
          mai sullo schermo.
        """
        a = fondo(SCENA_A if (i // 3) % 2 == 0 else SCENA_B)
        x = (i * 3) % 100
        c0 = int(L * x / 100.0)
        c1 = min(L, c0 + int(L * 0.20))
        a[:, c0:c1] = (10, 10, 10)
        return a

    def congelata(i):
        return scena(0)

    def rumore(i, ampiezza):
        """Un fondo fisso con un disturbo di ampiezza dichiarata: ⭐ serve a
        attraversare la soglia del RUMORE nei due versi."""
        a = fondo(SCENA_A).astype("int16")
        # meta' dell'immagine si scosta di `ampiezza` a fotogrammi alterni
        if i % 2:
            a[: A // 2, :, 0] = np.clip(a[: A // 2, :, 0] + ampiezza, 0, 255)
        return a.astype("uint8")

    def macchiolina(i):
        """Cambia POCHISSIMI pixel: ⭐ attraversa la soglia della COPPIA."""
        a = fondo(SCENA_A)
        a[0, (i * 3) % L] = (255, 255, 255)      # 1 pixel su 9216 = 0,01 %
        return a

    print("== certificazione dei giudici di C3 ==")
    print("   giudice del desktop : %s" % dove_g)
    print("   lettore del colore  : %s" % dove_l)
    print("   ritmo minimo %.2f/s (riferimento grezzo [M] %.1f/s) · rumore ±%d "
          "per canale · coppia ≥%.0f%% dei pixel · almeno il %.0f%% delle coppie"
          % (RITMO_MINIMO, RIFERIMENTO_FPS, SOGLIA_RUMORE, SOGLIA_COPPIA * 100,
             FRAZIONE_COPPIE * 100))
    print()
    guai = 0

    def prova(nome, ottenuto, atteso, extra=""):
        nonlocal guai
        ok = ottenuto == atteso
        if not ok:
            guai += 1
        print("  %s  %-58s  ⇒ %-10s (atteso %s)%s"
              % ("OK " if ok else "NO ", nome, ottenuto, atteso,
                 ("  %s" % extra) if extra else ""))

    # ── 1. la scena vera in movimento ──────────────────────────────────────
    viva = sequenza("viva", 61, scena)
    e = giudica_il_flusso(viva, 2.0)
    prova("la scena dichiarata si muove", e["stato"], "cambia",
          "coppie diverse %s/%s" % (e["diverse"], e["coppie"]))

    # ── 2. ⭐ IL GUASTO: lo stesso fotogramma ripetuto ─────────────────────
    ferma = sequenza("ferma", 61, congelata)
    e2 = giudica_il_flusso(ferma, 2.0)
    prova("⭐ lo stesso fotogramma ripetuto ⇒ IMMAGINE CONGELATA",
          e2["stato"], "congelata",
          "coppie diverse %s/%s" % (e2["diverse"], e2["coppie"]))

    # ── 3. il ritmo, attraversato nei DUE versi ────────────────────────────
    #    61 fotogrammi in 5 s = 12,2/s (sopra 4,0) · in 30 s = 2,03/s (sotto)
    prova("il ritmo sta sopra la soglia (12,2/s)",
          giudica_il_flusso(viva, 5.0)["stato"], "cambia")
    prova("⭐ il ritmo CROLLA sotto la soglia (2,03/s)",
          giudica_il_flusso(viva, 30.0)["stato"], "crollati")
    prova("nessun fotogramma con la scena in movimento ⇒ rosso",
          giudica_il_flusso([], 10.0)["stato"], "crollati")

    # ── 4. ⚠⚠ IL CONTROLLO NEGATIVO: «scena ferma» non deve MAI dare rosso ─
    prova("⚠ scena FERMA e nessun fotogramma ⇒ non lo so, NON rosso",
          giudica_il_flusso([], 30.0, scena_ferma=True)["stato"], "non-lo-so")
    prova("⚠ scena FERMA e fotogrammi tutti uguali ⇒ non lo so, NON rosso",
          giudica_il_flusso(ferma, 30.0, scena_ferma=True)["stato"], "non-lo-so")
    prova("⚠ scena FERMA con un fotogramma solo ⇒ non lo so, NON rosso",
          giudica_il_flusso(viva[:1], 30.0, scena_ferma=True)["stato"], "non-lo-so")

    # ── 5. la soglia del RUMORE, attraversata nei due versi ────────────────
    sotto = sequenza("rumore-sotto", 21, lambda i: rumore(i, SOGLIA_RUMORE - 2))
    sopra = sequenza("rumore-sopra", 21, lambda i: rumore(i, SOGLIA_RUMORE + 6))
    ms = coppie_che_cambiano(sotto)
    mp = coppie_che_cambiano(sopra)
    prova("un disturbo di ±%d livelli e' RUMORE, non movimento" % (SOGLIA_RUMORE - 2),
          0 if ms is None else ms["diverse"], 0)
    prova("⭐ un disturbo di ±%d livelli E' movimento" % (SOGLIA_RUMORE + 6),
          0 if mp is None else mp["diverse"], 20)

    # ── 6. la soglia della COPPIA, attraversata nei due versi ──────────────
    piccola = sequenza("macchiolina", 21, macchiolina)
    mm = coppie_che_cambiano(piccola)
    prova("un pixel che cambia non e' una scena che si muove",
          0 if mm is None else mm["diverse"], 0)
    prova("⇒ e il flusso corrispondente e' CONGELATO",
          giudica_il_flusso(piccola, 1.0)["stato"], "congelata")

    # ── 7. ⛔ i «non lo so», che non sono ne' verdi ne' rossi ──────────────
    prova("⛔ nessun elenco (ffmpeg non ha prodotto niente) ⇒ non lo so",
          giudica_il_flusso(None, 10.0)["stato"], "non-lo-so")
    prova("⛔ un fotogramma solo: non ci sono coppie ⇒ non lo so",
          giudica_il_flusso(viva[:1], 0.05)["stato"], "non-lo-so")
    manca = [os.path.join(lav, "non-ci-sono-%d.png" % i) for i in range(5)]
    prova("⛔ fotogrammi illeggibili ⇒ non lo so",
          giudica_il_flusso(manca, 1.0)["stato"], "non-lo-so")
    prova("⛔ e il misuratore torna «non lo so», non zero",
          "non lo so" if coppie_che_cambiano(manca) is None else "un numero",
          "non lo so")

    # ── 8. ⭐ la SCENA DICHIARATA e' sullo schermo? (il lettore importato) ──
    def fr(p, colore):
        return lettore.frazione_del_colore(p, colore, TOLLERANZA)

    ultimo_viva = viva[-1]
    ultimo_altro = sequenza("altro", 1, lambda i: fondo((58, 62, 70)))[0]
    prova("la scena dichiarata E' sullo schermo",
          "si" if max(fr(ultimo_viva, SCENA_A), fr(ultimo_viva, SCENA_B))
          >= FRAZIONE_SCENA else "no", "si")
    prova("⛔ un desktop qualunque NON e' la scena dichiarata",
          "si" if max(fr(ultimo_altro, SCENA_A), fr(ultimo_altro, SCENA_B))
          >= FRAZIONE_SCENA else "no", "no")
    # ⭐ e il colore spostato di quanto la tolleranza ammette deve restare «si»
    spostato = sequenza("spostata", 1, lambda i: fondo(
        tuple(min(255, max(0, c + s)) for c, s in zip(SCENA_A, (+30, +30, -30)))))[0]
    prova("⭐ colore spostato dentro la tolleranza ⇒ e' ancora la scena",
          "si" if max(fr(spostato, SCENA_A), fr(spostato, SCENA_B))
          >= FRAZIONE_SCENA else "no", "si")
    troppo = sequenza("troppo", 1, lambda i: fondo(
        tuple(min(255, max(0, c + s)) for c, s in zip(SCENA_A, (+120, +120, -120)))))[0]
    prova("colore spostato TROPPO ⇒ non e' piu' la scena",
          "si" if max(fr(troppo, SCENA_A), fr(troppo, SCENA_B))
          >= FRAZIONE_SCENA else "no", "no")

    # ── 9. ⭐⭐ E LA DIMOSTRAZIONE DEL GUASTO INNESTATO «fotogramma ripetuto»,
    #        fatta come la fara' sul vero: **sugli stessi dati**.
    print()
    sano = giudica_il_flusso(viva, 2.0)
    sfregiato = giudica_il_flusso(sfregia_ripetendo(viva), 2.0)
    dimostrato = (sano["stato"] == "cambia" and sfregiato["stato"] == "congelata"
                  and sano["diverse"] > 0 and sfregiato["diverse"] == 0)
    if not dimostrato:
        guai += 1
    print("  %s  ⭐ lo SFREGIO sugli stessi dati: coppie diverse da %s a %s, "
          "verdetti «%s» e «%s»"
          % ("OK " if dimostrato else "NO ", sano["diverse"],
             sfregiato["diverse"], sano["stato"], sfregiato["stato"]))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LE SOGLIE ATTRAVERSATE **AL BORDO**, e non da lontano.
    #
    # ⛔ Prima c'erano solo casi lontani (rumore 10 e 18 contro 12; ritmo 12,2 e
    #    2,03 contro 4,0; tolleranza 30 e 120 contro 48): con quelli si prova
    #    che il confronto ha il **verso** giusto, ⚠ non che la soglia cada nel
    #    punto in cui dice di cadere.  ⇒ E siccome i numeri sono tutti `[?]` da
    #    ritarare, e' proprio il posto in cui la trappola morde (§1.50).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    # il RUMORE, a un livello sotto e uno sopra
    b_sotto = sequenza("bordo-r-sotto", 11, lambda i: rumore(i, SOGLIA_RUMORE))
    b_sopra = sequenza("bordo-r-sopra", 11, lambda i: rumore(i, SOGLIA_RUMORE + 1))
    m1 = coppie_che_cambiano(b_sotto)
    m2 = coppie_che_cambiano(b_sopra)
    prova("uno scarto di ESATTAMENTE %d livelli e' ancora rumore" % SOGLIA_RUMORE,
          0 if m1 is None else m1["diverse"], 0)
    prova("⭐ uno scarto di %d livelli e' gia' movimento" % (SOGLIA_RUMORE + 1),
          0 if m2 is None else m2["diverse"], 10)

    # la COPPIA: quanti pixel devono cambiare.  9216 pixel ⇒ 1 % = 92,16
    def blocco(i, quanti_pixel):
        a = fondo(SCENA_A)
        if i % 2:
            piatta = a.reshape(-1, 3)
            piatta[:quanti_pixel] = (255, 255, 255)
            a = piatta.reshape(A, L, 3)
        return a
    sotto = sequenza("bordo-c-sotto", 11, lambda i: blocco(i, 92))   # 0,998 %
    sopra = sequenza("bordo-c-sopra", 11, lambda i: blocco(i, 93))   # 1,009 %
    m3 = coppie_che_cambiano(sotto)
    m4 = coppie_che_cambiano(sopra)
    prova("92 pixel su 9216 (0,998 %) NON sono un cambiamento",
          0 if m3 is None else m3["diverse"], 0)
    prova("⭐ 93 pixel su 9216 (1,009 %) LO sono",
          0 if m4 is None else m4["diverse"], 10)

    # il RITMO, a cavallo esatto di 4,00/s: 61 fotogrammi in 15,25 s = 4,000
    prova("il ritmo a 4,07/s (appena sopra la soglia) ⇒ VERDE",
          giudica_il_flusso(viva, 15.0)["stato"], "cambia")
    prova("⭐ il ritmo a 3,94/s (appena sotto) ⇒ ROSSO",
          giudica_il_flusso(viva, 15.5)["stato"], "crollati")

    # la TOLLERANZA sul colore della scena, al bordo
    al_limite = sequenza("bordo-t1", 1, lambda i: fondo(
        (TOLLERANZA, TOLLERANZA, 255 - TOLLERANZA)))[0]
    oltre = sequenza("bordo-t2", 1, lambda i: fondo(
        (TOLLERANZA + 1, TOLLERANZA + 1, 255 - TOLLERANZA - 1)))[0]
    prova("⭐ colore spostato di ESATTAMENTE ±%d ⇒ e' ancora la scena" % TOLLERANZA,
          "si" if max(fr(al_limite, SCENA_A), fr(al_limite, SCENA_B))
          >= FRAZIONE_SCENA else "no", "si")
    prova("colore spostato di ±%d ⇒ non e' piu' la scena" % (TOLLERANZA + 1),
          "si" if max(fr(oltre, SCENA_A), fr(oltre, SCENA_B))
          >= FRAZIONE_SCENA else "no", "no")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «IL CLIENTE E' STATO AMMESSO?» — la parola dentro un testo NON basta.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    for nome, testo, atteso in (
            ("la riga vera del cliente ammesso",
             "   AMMESSO dopo 1023 ms\n", True),
            ("⛔ CONGEDO invece di AMMESSO — la parola c'e', il senso e' opposto",
             "   ⛔ RuntimeError: CONGEDO invece di AMMESSO: motivo 0x03\n", False),
            ("⛔ «atteso AMMESSO, arrivato …» — idem",
             "   ⛔ RuntimeError: atteso AMMESSO, arrivato CONGEDO\n", False)):
        prova(nome, e_stato_ammesso(testo), atteso)
    prova("⛔ il cliente non ha detto NIENTE ⇒ non lo so",
          "non lo so" if e_stato_ammesso("") is None else "un si o un no",
          "non lo so")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «I FOTOGRAMMI STANNO ARRIVANDO ADESSO?» — il segnale che decide
    #    **quando** si innesta il guasto (cura del 27 agosto 2026).
    # ⛔ E' tutto in funzioni PURE apposta: il momento dell'innesto e' la cosa
    #    che il 27 agosto 2026 era sbagliata, e non si lascia a un codice che
    #    gira solo dentro la scatola.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    riga_vera = ("42 (remotix) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                 "5 5 20 0 3 0")
    prova("il lavoro di un processo, da /proc/<pid>/stat ⇒ 4,00 s di CPU",
          cpu_dalla_riga(riga_vera, 100.0), 4.0)
    prova("⛔ il nome del comando CON UNO SPAZIO non sposta i campi",
          cpu_dalla_riga("42 (a b) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                         "5 5 20 0 3 0", 100.0), 4.0)
    prova("⛔ il nome del comando con una PARENTESI dentro: si taglia l'ultima",
          cpu_dalla_riga("42 (we)ird) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                         "5 5 20 0 3 0", 100.0), 4.0)
    prova("⛔ una riga troncata ⇒ «non lo so», e non zero",
          cpu_dalla_riga("42 (remotix) S 1 42", 100.0), None)
    prova("⛔ nessuna riga ⇒ «non lo so», e non zero",
          cpu_dalla_riga("", 100.0), None)
    ps_vero = ("   12 /opt/remotix/remotix --sessione c3u1\n"
               "    3 /opt/remotix/remotix --sessione c3u1 --figlio\n"
               "  400 /usr/lib/firefox-esr/firefox-esr --kiosk file:///x.html\n")
    prova("⭐ il lavoro del CODIFICATORE, e solo suo: 12+3 ⇒ 15 s di CPU",
          somma_lavoro(ps_vero, "remotix"), 15.0)
    prova("⛔ il browser non e' il codificatore: non entra nella somma",
          somma_lavoro(ps_vero, "remotix") != somma_lavoro(ps_vero, ""), True)
    prova("⛔ nessun processo con quel nome ⇒ «non lo so», e ⛔ NON zero",
          somma_lavoro(ps_vero, "kwin_wayland"), None)
    prova("⚠ una riga senza il tempo non fa sballare la somma",
          somma_lavoro("nonunnumero /opt/remotix/remotix\n   7 "
                       "/opt/remotix/remotix\n", "remotix"), 7.0)
    prova("⛔ nessuna riga affatto ⇒ «non lo so»", somma_lavoro("", "remotix"),
          None)
    prova("il lavoro al secondo fra due letture (1,0 ⇒ 3,0 in 2 s) ⇒ 1,00/s",
          lavoro_al_secondo(1.0, 3.0, 2.0), 1.0)
    prova("⛔ una lettura che manca ⇒ «non lo so», e non zero",
          lavoro_al_secondo(None, 3.0, 2.0), None)
    prova("⛔ zero secondi fra le due letture ⇒ «non lo so»",
          lavoro_al_secondo(1.0, 3.0, 0.0), None)
    prova("⚠ un conto all'indietro non e' una misura ⇒ 0, mai un negativo",
          lavoro_al_secondo(5.0, 3.0, 2.0), 0.0)
    prova("⭐ la scena in vista prima dell'innesto: 27 s d'attesa, 0,60 CPU/s "
          "⇒ al piu' 6,17 s",
          round(secondi_in_vista(27.0, 2.0, 0.10, 0.60), 2), 6.17)
    prova("⭐ se i fotogrammi arrivano al primo colpo, e' solo il passo ⇒ 2,00 s",
          round(secondi_in_vista(2.0, 2.0, 0.10, 0.60), 2), 2.0)
    prova("⛔ senza il lavoro del cliente non si finge un tetto ⇒ «non lo so»",
          secondi_in_vista(27.0, 2.0, 0.10, None), None)
    prova("⭐⭐ la finestra che serve: 6 s in vista × 30/s sani ÷ 4/s pretesi "
          "⇒ 45 s",
          finestra_bastante(6.0, 30.0, 4.0), 45.0)
    prova("⛔ senza il ritmo sano non si finge una finestra ⇒ «non lo so»",
          finestra_bastante(6.0, None, 4.0), None)
    prova("⛔ senza i secondi in vista non si finge una finestra ⇒ «non lo so»",
          finestra_bastante(None, 30.0, 4.0), None)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ I TRE GIUNTI — i codici d'uscita, che sono INVERTITI e da cui C13
    #      ricava se la rete sa ancora dare rosso (`LEZIONI.md` §1.52).
    # ═══════════════════════════════════════════════════════════════════════
    print()

    def giro(stato, motivo="", diverse=None, coppie=None, minima=None,
             ritmo=None, fermati=None, preso=None, fotogrammi=None,
             secondi=90.0, lavoro_visto=True, coda_frazione=1.0,
             cpu_prima=0.60, cpu_finestra=0.60, secondi_prima=6.0):
        """⚠ I valori messi di ritratto sono quelli di un giro **che regge**:
        cosi' ogni caso qui sotto guasta UNA cosa sola, e si sa quale."""
        return {"stato": stato, "motivo": motivo, "perche": "(finto)",
                "diverse": diverse, "coppie": coppie, "minima": minima,
                "ritmo": ritmo, "fermati": fermati, "pkill_ha_preso": preso,
                "chi": "c3uX", "fotogrammi": fotogrammi, "secondi": secondi,
                "lavoro_visto": lavoro_visto, "coda_frazione": coda_frazione,
                "coda_diverse": 60, "coda_coppie": 60, "cpu_prima": cpu_prima,
                "cpu_finestra": cpu_finestra, "secondi_prima": secondi_prima}

    sano_ok = giro("cambia", "cambia", diverse=60, coppie=60, minima=0.08,
                   ritmo=30.0)
    congelato = giro("congelata", "congelata", diverse=0, coppie=60)
    # ⭐ Il giro col guasto che REGGE: la scena si muoveva, il codificatore e'
    #   morto, e dentro la finestra il cliente non ha piu' lavorato.
    rotto_ok = giro("crollati", "ritmo-crollato", ritmo=0.4, fermati=1,
                    preso=True, cpu_finestra=0.01)
    giunti = [
        ("ripetuto: sano verde + sfregiato congelato + scena vivace ⇒ 0",
         collauda_il_ripetuto(sano_ok, congelato), 0),
        ("⛔ ripetuto: lo sfregio NON e' stato visto ⇒ 1",
         collauda_il_ripetuto(sano_ok, giro("cambia", "cambia", 60, 60)), 1),
        ("⭐ ripetuto: la scena e' TROPPO TIMIDA (1,2× la soglia) ⇒ 1",
         collauda_il_ripetuto(giro("cambia", "cambia", 60, 60, minima=0.012,
                                   ritmo=30.0), congelato), 1),
        ("⭐ ripetuto: il CONTROLLO SANO e' rosso ⇒ 3, ⛔ NON 1",
         collauda_il_ripetuto(giro("congelata", "congelata", 0, 60), congelato), 3),
        ("ripetuto: il sano non ha potuto guardare ⇒ 3",
         collauda_il_ripetuto(giro("non-lo-so", "palco-non-nato"), congelato), 3),
        ("⭐ ripetuto: lo SFREGIATO non si e' lasciato giudicare ⇒ 3, non 1",
         collauda_il_ripetuto(sano_ok, giro("non-lo-so", "niente-coppie")), 3),
        ("fermo: sano verde + guasto crollato + firma ⇒ 0",
         collauda_il_fermo(sano_ok, rotto_ok), 0),
        ("⛔ fermo: col codificatore fermo i fotogrammi arrivano lo stesso ⇒ 1",
         collauda_il_fermo(sano_ok, giro("cambia", "cambia", ritmo=29.0,
                                         fermati=1, preso=True,
                                         cpu_finestra=0.01)), 1),
        ("⛔ fermo: il ritmo LORDO scende poco (30 ⇒ 12, sopra la quota) ⇒ 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=12.0, fermati=1, preso=True,
                                         cpu_finestra=0.01)), 1),
        ("⭐ fermo: il cliente LAVORA ANCORA dentro la finestra ⇒ 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.30)), 1),
        ("⚠ fermo: `pkill` non ha preso niente ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=0, preso=False)), 3),
        ("⭐ fermo: il CONTROLLO SANO e' rosso ⇒ 3, ⛔ NON 1",
         collauda_il_fermo(giro("crollati", "ritmo-crollato", ritmo=0.1),
                           rotto_ok), 3),
        # ⭐⭐⭐ IL MOMENTO DELL'INNESTO — i casi che il 27 agosto 2026 non
        #     c'erano, e sono quelli per cui il giro usciva 3.
        ("⭐⭐ fermo: i fotogrammi non si erano MAI visti arrivare ⇒ 3, ⛔ non 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01,
                                         lavoro_visto=False)), 3),
        ("⭐⭐ fermo: gli ultimi fotogrammi consegnati erano IDENTICI "
         "(innesto troppo presto) ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01,
                                         coda_frazione=0.0)), 3),
        ("⭐ fermo: non so se gli ultimi consegnati cambiassero ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01,
                                         coda_frazione=None)), 3),
        ("⭐⭐ fermo: la FINESTRA era troppo corta per questo ritmo ⇒ 3, non 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01, secondi=30.0)), 3),
        ("⭐ fermo: non so quanto abbia lavorato il cliente nella finestra ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=None)), 3),
        ("⭐ scena ferma: il giro e' avvenuto e non ha dato rosso ⇒ 0",
         collauda_la_scena_ferma(giro("non-lo-so", "scena-ferma",
                                      fotogrammi=1, secondi=60.0)), 0),
        ("⛔ scena ferma: la maglia ha dato ROSSO ⇒ 1 (il controllo e' fallito)",
         collauda_la_scena_ferma(giro("crollati", "zero-fotogrammi")), 1),
        ("⚠ scena ferma: il palco non e' nato ⇒ 3, ⛔ non un controllo riuscito",
         collauda_la_scena_ferma(giro("non-lo-so", "palco-non-nato")), 3),
    ]
    for nome, (e, _righe), atteso in giunti:
        prova(nome, e, atteso)

    shutil.rmtree(lav, ignore_errors=True)
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ il caso che oggi non c'era.
    #
    # ⛔ Un inquilino fuori dai gruppi dei nodi `/dev/dri` fa nascere una
    #    sessione CIECA (`[M]` 0 su 4, zero fotogrammi, `fasi/10-…` §7.4) ⇒
    #    questa maglia misurerebbe il buio.  ⭐ Si pretende che dica «non ho
    #    potuto guardare», ⛔ e MAI rosso: e' un guasto del BANCO (§1.51).
    # ⚠ I casi vivono in C1, col passo che certificano: ⛔ una copia qui
    #   sarebbe un secondo posto da cui divergere (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    guai_gr, quanti_gr = casa_di_c1().certifica_gruppi("C3")
    guai += guai_gr

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ LA PROVVISTA CONDIVISA — ⛔ il caso che il 27 agosto 2026 non c'era,
    #    e per cui questa maglia ha detto «non ho potuto guardare» accusando il
    #    prodotto di una colpa del banco.
    # ⚠ I casi vivono in C2, col codice che certificano: ⛔ una copia qui sarebbe
    #   un secondo posto da cui divergere (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    casa_pr = casa_della_provvista()
    if casa_pr is None:
        print("  NO   ⛔ non trovo `11-c2-…py`: la provvista non e' certificabile")
        guai += 1
        quanti_pr = 0
    else:
        guai_pr, quanti_pr = casa_pr.certifica_la_provvista("C3", "c3u")
        guai += guai_pr

    print()
    if guai:
        print("⛔ i giudici di C3 NON sono affidabili: %d casi sbagliati" % guai)
        return 1
    print("⭐ i giudici vedono la scena che cambia e prendono l'immagine "
          "congelata, le quattro soglie cadono dove dicono (al bordo),")
    print("   ⭐ «AMMESSO» e' una riga e non una parola, ⚠ a scena ferma non "
          "esce mai un rosso, ⛔ e «non lo so» non e' zero,")
    print("   ⭐⭐ e i TRE GIUNTI — i codici d'uscita dei due guasti innestati e "
          "del controllo negativo — dicono 0, 1 e 3 dove devono (§1.52)")
    print("   ⭐ e i GRUPPI DELLA SCHEDA: un inquilino che non vede fa dire "
          "«non ho potuto guardare», ⛔ mai rosso")
    # ⛔ La riga della provvista si stampa SOLO se i casi veri sono girati.
    if quanti_pr >= 4:
        print("   ⭐⭐ e LA PROVVISTA: un /tmp/mozilla di un'altra maglia non lo "
              "tocco, e il mio inquilino scrive lo stesso — ⛔ mai rosso")
    else:
        print("   ⚠ e LA PROVVISTA e' coperta SOLO a meta': i casi veri "
              "chiedono l'amministratore, e qui non li ho girati")
    print("⚠ e questa certificazione copre I GIUDICI E I GIUNTI, ⛔ non la "
          "consegna vera dei fotogrammi ne' che le cinque soglie siano nel "
          "PUNTO giusto (vedi in testa)")
    return 0


def sfregia_ripetendo(elenco):
    """⭐ IL GUASTO INNESTATO «fotogramma ripetuto», e sta in una riga.

    ⛔ Si sfregia **la copia in memoria** dell'elenco: il flusso sul disco non
       si tocca.  E' la stessa forma di C9 (`--togli-nome`), e ha il pregio che
       il controllo sano e il guasto girano **sugli stessi dati** ⇒ la differenza
       non puo' venire da un giro diverso.
    """
    if not elenco:
        return elenco
    return [elenco[0]] * len(elenco)


# ═══════════════════════════════════════════════════════════════════════════
# IL TERRENO E LE MOSSE — ⚠ le stesse di C2, e per le stesse ragioni
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=120):
    try:
        return subprocess.run(["/bin/sh", "-c", comando],
                              capture_output=True, text=True, timeout=secondi)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(comando, 124, "", "scaduto")


def quanti_schermi(testo):
    """⛔ `None` = non lo so; `0` = ho chiesto e non ce n'e' nessuno."""
    if testo is None:
        return None
    return len(FIRMA_OUTPUT.findall(testo))


def crea(chi, parola):
    """⛔ Si cancella PRIMA di crearlo: «da zero» comprende «da zero rispetto a
       me stesso di ieri» (`[M]` C1, 26 agosto 2026)."""
    sh("loginctl terminate-user %s 2>/dev/null; pkill -KILL -u %s 2>/dev/null; "
       "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi, chi, chi))
    # ⛔⛔ I GRUPPI DELLA SCHEDA NON STANNO PIU' DENTRO IL `useradd`.
    #     `usermod -aG video,render` inchiodava due nomi — che sono di UNA
    #     distribuzione — e ⛔ **non rileggeva**: `usermod` riuscito non vuol
    #     dire «ci sta dentro» (E1, «scritto non e' in vigore»).
    # ⭐ Li da' `attrezzi-gruppi-scheda.sh`, che li LEGGE dai nodi `/dev/dri` e
    #   poi VERIFICA confrontando i numeri.  ⇒ Qui non c'e' piu' nessun nome di
    #   gruppo e nessun numero.
    # ⛔ E senza, `[M]` la sessione nasce CIECA (0 su 4, zero fotogrammi,
    #   `fasi/10-…` §7.4): questa maglia misurerebbe il buio e lo chiamerebbe
    #   difetto del prodotto.  ⇒ Non si misura: chi chiama esce **3**.
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
    if r.returncode != 0:
        return False, (r.stderr or "").strip()[:120]
    e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="      ")
    if e_gr != 0:
        return False, perche_gr
    # ⭐⭐ E LA PROVVISTA, subito dopo il `useradd -m` che copia lo scheletro:
    #    e' li' che l'inquilino nasce con `~/.cache` puntata a `/tmp`, ⇒ e' li'
    #    che gli si da' la sua.  ⛔ Prima di accendere qualunque cosa.
    fatto_cura, perche_cura = cura_della_provvista(chi)
    if not fatto_cura:
        return False, perche_cura
    return True, ""


def sgombra(chi, attesa):
    # ⛔ Prima si RISVEGLIA: col `--codificatore-fermo` c'e' un processo in stato
    #    T, e un processo fermato non se ne va da solo.  ⚠ E si sgombra SOLO la
    #    propria roba, per nome (fase 10 §7.3).
    sh("pkill -CONT -u %s 2>/dev/null" % chi)
    sh("loginctl terminate-user %s 2>/dev/null" % chi)
    time.sleep(1.0)
    sh("pkill -KILL -u %s 2>/dev/null" % chi)
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        viva = sh("loginctl show-user %s >/dev/null 2>&1" % chi).returncode == 0
        proc = sh("pgrep -u %s >/dev/null 2>&1" % chi).returncode == 0
        if not viva and not proc:
            return True
        time.sleep(0.5)
    return False


def il_socket_di(chi):
    """⛔ Il socket di Wayland si CERCA, non si indovina (§3.7)."""
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, None
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    d = soc.stdout.strip()
    return (rtd, d) if d else (rtd, None)


def chiedi_al_compositore(chi):
    """⭐ Si chiede al COMPOSITORE se c'e' uno schermo, non al prodotto.

    ⛔ `[R]` la riga *«⛔ ZERO MONITOR»* di `src/sessione.c:345-348` il prodotto
       la scrive **anche durante una nascita che riuscira'** — a quel punto il
       monitor non e' ancora comparso (`src/mutter.c:697`).  ⇒ Leggerla come
       prova di cecita' e' un errore, e questa maglia non lo fa.
    """
    rtd, display = il_socket_di(chi)
    if rtd is None:
        return None, "non so l'uid di «%s»" % chi
    if display is None:
        return None, ("in %s non c'e' nessun socket wayland: il compositore non "
                      "e' (ancora) nato" % rtd)
    r = sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
           "wayland-info" % (chi, rtd, display), secondi=60)
    if r.returncode != 0 and not r.stdout:
        return None, ("wayland-info non ha parlato: %s"
                      % ((r.stderr or "").strip().replace("\n", " ")[:90]))
    return quanti_schermi(r.stdout), ""


def accendi_la_scena(chi, a):
    """Accende la scena dichiarata DENTRO la sessione dell'inquilino."""
    rtd, display = il_socket_di(chi)
    if display is None:
        return None, ("in %s non c'e' nessun socket wayland: non c'e' un "
                      "compositore a cui la scena possa parlare" % rtd)
    args = a.argomenti % {"pagina": a.scena}
    sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s %s > /home/%s/.c3-scena.log 2>&1 &"
       % (chi, rtd, display, chi, a.applicazione, args, chi), secondi=30)
    return display, ""


def la_scena_e_viva(chi, applicazione):
    """⚠ Non dimostra che la scena SI MUOVA: dimostra che il programma che la
       muove non e' morto.  ⛔ E la differenza e' dichiarata in testa al file."""
    r = sh("pgrep -u %s -f %s >/dev/null 2>&1" % (chi, applicazione))
    return r.returncode == 0


def ferma_il_codificatore(chi, nome):
    """⛔ IL GUASTO VERO: SIGSTOP al processo dell'inquilino che consegna.

    ⚠ E il nome va detto giusto: **non si ferma «il solo codificatore»**, si
      ferma il processo che lo contiene.  E' quanto si puo' fare senza toccare
      il prodotto, e la differenza si dichiara invece di nasconderla.

    Torna (quanti_fermati, elenco) — ⭐ e questa e' la FIRMA del guasto: se
    nessuno e' finito in stato **T**, l'iniezione non ha toccato niente e un
    eventuale rosso e' di qualcun altro (`LEZIONI.md` §1.52).
    """
    # ⭐ L'ESITO DEL `pkill` SI GUARDA: dice esattamente se ha trovato qualcosa
    #   da fermare, ed e' la differenza fra «ho fermato il codificatore» e
    #   «non c'era niente da fermare».  ⛔ Buttarlo via vorrebbe dire fidarsi
    #   di un comando senza guardare se e' stato eseguito (`LEZIONI.md` §1.46).
    k = sh("pkill -STOP -u %s -f %s" % (chi, nome))
    preso = (k.returncode == 0)
    time.sleep(1.0)
    r = sh("ps -u %s -o stat=,comm=" % chi)
    fermati = []
    for riga in (r.stdout or "").splitlines():
        pezzi = riga.split(None, 1)
        if len(pezzi) < 2 or not pezzi[0].startswith("T"):
            continue
        fermati.append(pezzi[1].strip())
    # ⚠ E si conta CHI e' fermo, non «quanti processi sono fermi»: un inquilino
    #   appena nato non ha altri processi in stato T, ⛔ ma contare tutti sarebbe
    #   un predicato un livello troppo in alto — §1.44, la forma esatta del
    #   difetto di C8 col `~/.cache` invece di `~/.cache/mozilla`.
    miei = [c for c in fermati if nome in c or c in nome]
    return len(miei), miei, preso


def estrai_i_fotogrammi(flusso, dove, larghezza, altezza, tetto=900.0):
    """Dal flusso H.264 preso dal filo tira fuori TUTTI i fotogrammi, rimpiccioliti.

    ⛔ Si rimpiccioliscono apposta: a 1920x1080 mille fotogrammi sono un
       gigabyte e mezzo, e il confronto non ne guadagna niente — la scena
       dichiarata cambia a blocchi larghi, non a dettagli fini.
    ⚠ E il prezzo si dichiara: un cambiamento piu' piccolo di un pixel della
      miniatura sparisce.  ⇒ Per questo la scena e' fatta di blocchi grandi, e
      non di un cursore che lampeggia.
    ⛔ E si giudica **il risultato, non il codice d'uscita** di ffmpeg
      (`LEZIONI.md` §1.50).
    """
    if os.path.isdir(dove):
        shutil.rmtree(dove, ignore_errors=True)
    os.makedirs(dove, exist_ok=True)
    r = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -vf scale=%d:%d "
           "-y %s/f-%%05d.png" % (flusso, larghezza, altezza, dove),
           secondi=tetto)
    elenco = sorted(glob.glob(os.path.join(dove, "f-*.png")))
    # ⛔⛔ E QUI IL CODICE D'USCITA **SI GUARDA**, ed e' il rovescio di §1.50.
    #    La' il codice d'uscita andava ignorato perche' il lavoro era
    #    **compiuto** (il PNG c'era ed era giusto).  ⚠ Qui una scadenza lascia
    #    un elenco **troncato**, che ha esattamente l'aspetto di una presa
    #    magra: ⛔ il ritmo uscirebbe sbagliato e la maglia direbbe «crollati»
    #    su una sessione sana.
    return (elenco or None), (r.returncode == 124)


def quanti_fotogrammi_dice_il_cliente(coda):
    quanti = None
    for riga in coda.splitlines():
        if "[vid]" in riga and "nessun fotogramma" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return quanti


# ═══════════════════════════════════════════════════════════════════════════
# UN GIRO
# ═══════════════════════════════════════════════════════════════════════════
def un_giro(chi, modo, a, giudice, lettore):
    """`modo` = None (sano) | "fermo" (SIGSTOP al codificatore).

    ⛔⛔ L'ORDINE DELLE MOSSE — ed e' la ragione per cui questa maglia oggi si
         puo' scrivere:

           1. si crea l'inquilino
           2. ⭐ **si attacca il cliente, e ci si RESTA**: `[R]` `src/mutter.c:697`
              — il `wl_output` di una sessione headless nasce quando un
              consumatore si aggancia al flusso, e muore col figlio
           3. si aspetta che il COMPOSITORE annunci uno schermo
           4. si accende la scena dichiarata
           5. ⭐⭐ si aspetta che i fotogrammi **arrivino davvero** — non un
              tempo fisso: si guarda il lavoro del cliente
              (`aspetta_che_i_fotogrammi_arrivino`)
           6. (col guasto: ⛔ SIGSTOP **QUI**) ⇒ ⭐ la scena c'e', si muove, e i
              fotogrammi stanno arrivando: **poi** il codificatore muore
           7. si apre la finestra di misura e si guarda per `--finestra` secondi
           8. il cliente finisce e scrive il flusso

    ⛔⛔ E IL PUNTO 6 E' UNA CURA DEL 27 AGOSTO 2026, non un dettaglio.
        Fino a quel giorno il SIGSTOP stava fra il 3 e il 4, cioe' **prima che
        la scena esistesse**: il codificatore moriva su un desktop vuoto, la
        scena dichiarata non compariva mai sullo schermo, e la maglia — ⭐
        onestamente — diceva *«la scena che ho dichiarato NON e' sullo schermo
        ⇒ non ho potuto guardare»*, esito **3**.
        ⇒ Non era un difetto del prodotto e non era un rosso: era ⛔ **un
          collaudo che non collaudava**, perche' il guasto era innestato nel
          momento sbagliato della storia.  Il guardiano non si e' toccato: si e'
          spostato l'innesto.
    """
    esito = {"chi": chi, "modo": modo or "sano", "stato": "non-lo-so",
             "perche": "", "fotogrammi": None, "ritmo": None, "coppie": None,
             "diverse": None, "palco_s": None, "schermi": None,
             "motivo": "", "scena_viva": None, "scena_viva_prima": None,
             "frazione_scena": None, "fermati": None, "pkill_ha_preso": None,
             "elenco": None, "secondi": None, "minima": None, "massima": None,
             # ⭐ i fatti nuovi del 27 agosto 2026 — vedi l'ordine delle mosse
             "lavoro_visto": None, "cpu_prima": None, "cpu_finestra": None,
             "secondi_prima": None, "coda_coppie": None, "coda_diverse": None,
             "coda_frazione": None, "finestra_pretesa": None}

    fatto, perche = crea(chi, a.parola)
    if not fatto:
        esito["motivo"] = "inquilino-non-creato"
        esito["perche"] = "non sono riuscito a creare «%s»: %s" % (chi, perche)
        return esito

    lavoro = os.path.join(a.lavoro, chi)
    os.makedirs(lavoro, exist_ok=True)
    flusso = os.path.join(lavoro, "presa.264")
    if os.path.exists(flusso):
        os.unlink(flusso)

    resta = a.attesa_palco + a.attesa_scena + a.finestra + a.coda
    partito = time.time()
    # ⛔⛔ E L'USCITA DEL CLIENTE VA IN UN FILE, NON IN UNA PIPE — e non e' uno
    #     stile: e' un guasto evitato.  Questo cliente resta acceso per minuti
    #     **mentre il banco fa altro**, e con `-u` scrive senza risparmio.  Una
    #     pipe che nessuno svuota si riempie (64 KB su Linux) e ⛔ **blocca chi
    #     scrive**: il cliente si fermerebbe a meta' di una `print`, smetterebbe
    #     di tenere viva la sessione, e il banco leggerebbe «nessun fotogramma»
    #     dando la colpa al prodotto.
    # ⚠ Gli esemplari non hanno questo problema perche' usano `subprocess.run`,
    #   che svuota le pipe mentre aspetta.  Qui non si aspetta: si lavora.
    detto_file = os.path.join(lavoro, "cliente.log")
    detto_fd = open(detto_file, "w")
    cliente = subprocess.Popen(
        ["python3", "-u", a.cliente,
         "--indirizzo", a.indirizzo, "--porta", str(a.porta),
         "--utente", chi, "--parola", a.parola,
         "--video-scrivi", flusso, "--resta", str(resta)],
        stdout=detto_fd, stderr=subprocess.STDOUT, text=True)

    def chiudi_il_cliente(scadenza):
        """Aspetta che il cliente finisca, e torna quel che ha detto.

        ⛔ Torna sempre una stringa: se il file non si lascia leggere e' un
           «non ho potuto guardare», e chi chiama lo vede come «non AMMESSO».
        """
        try:
            cliente.wait(timeout=scadenza)
        except subprocess.TimeoutExpired:
            cliente.kill()
            cliente.wait()
        detto_fd.close()
        try:
            with open(detto_file, "r", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    schermi = None
    motivo = "non ho mai potuto chiedere"
    scadenza = time.time() + a.attesa_palco
    while time.time() < scadenza:
        if cliente.poll() is not None:
            motivo = "il cliente se n'e' andato prima che nascesse uno schermo"
            break
        schermi, motivo = chiedi_al_compositore(chi)
        if schermi is not None and schermi >= OUTPUT_MINIMI:
            esito["palco_s"] = round(time.time() - partito, 1)
            break
        schermi = None
        time.sleep(2.0)
    esito["schermi"] = schermi

    if schermi is None or schermi < OUTPUT_MINIMI:
        esito["motivo"] = "palco-non-nato"
        esito["perche"] = ("in %.0f s il compositore non ha annunciato nessuno "
                           "schermo (%s) ⇒ non c'era niente da catturare"
                           % (a.attesa_palco, motivo or "?"))
        cliente.kill()
        chiudi_il_cliente(30)
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ── da qui in giu' c'e' l'accensione della scena e — col guasto — l'innesto
    # ⛔⛔ E SI STA DENTRO UN `try/finally`: fra l'iniezione e lo sgombero ci
    #     sono minuti di attesa, e ⚠ un Ctrl-C o un'eccezione li' lascerebbero
    #     **l'inquilino congelato in stato T**, il cliente attaccato e la
    #     macchina di prova sporca per chi viene dopo.
    #     ⭐ Il `finally` risveglia sempre, anche quando l'innesto non e' mai
    #       avvenuto: risvegliare uno che non dorme non costa niente,
    #       dimenticarsene una volta sola si.
    #     ⚠ E il `try` sta QUI e non piu' basso apposta: l'innesto e' sceso
    #       dentro `_il_resto_del_giro` (passo 6), ma la rete di sicurezza che
    #       lo risveglia dev'essere piu' larga di lui.
    try:
        return _il_resto_del_giro(chi, modo, a, giudice, lettore, esito,
                                  cliente, chiudi_il_cliente, flusso, lavoro,
                                  partito, resta)
    finally:
        if modo == "fermo":
            sh("pkill -CONT -u %s 2>/dev/null" % chi)


def _il_resto_del_giro(chi, modo, a, giudice, lettore, esito, cliente,
                       chiudi_il_cliente, flusso, lavoro, partito, resta):
    """La parte del giro che sta dentro il `try/finally` dell'iniezione."""
    # ── 4. la scena ────────────────────────────────────────────────────────
    if not a.scena_ferma:
        display, err = accendi_la_scena(chi, a)
        if display is None:
            esito["motivo"] = "scena-non-accesa"
            esito["perche"] = "non ho potuto accendere la scena: %s" % err
            cliente.kill()
            chiudi_il_cliente(30)
            sgombra(chi, a.attesa_sgombero)
            return esito
        # ── 5. ⭐⭐ SI ASPETTA CHE I FOTOGRAMMI ARRIVINO DAVVERO ────────────
        #    ⛔ E non un tempo fisso: `--attesa-scena` da attesa diventa TETTO.
        #    ⚠ Il momento in cui la scena comincia a dipingere e' quello che
        #      decide tutto (l'innesto, e quanti fotogrammi sporcano il ritmo
        #      lordo), e a orologio non lo si sa.
        visto, cpu_al_s, quanto = aspetta_che_i_fotogrammi_arrivino(
            lambda: cpu_del_codificatore(chi, a.nome_figlio),
            a.attesa_scena, a.soglia_cpu, a.passo_cpu)
        esito["lavoro_visto"] = visto
        esito["cpu_prima"] = cpu_al_s
        esito["secondi_prima"] = secondi_in_vista(
            quanto, a.passo_cpu, a.soglia_cpu, cpu_al_s) if visto else None
        print("           %s i fotogrammi arrivano: il codificatore brucia %s "
              "CPU/s (ne pretendo %.2f) dopo %.1f s · scena in vista prima "
              "dell'innesto: al piu' %s s"
              % ("⭐" if visto else "⚠",
                 "non lo so" if cpu_al_s is None else "%.2f" % cpu_al_s,
                 a.soglia_cpu, quanto,
                 "non lo so" if esito["secondi_prima"] is None
                 else "%.1f" % esito["secondi_prima"]))
        esito["scena_viva_prima"] = la_scena_e_viva(chi, a.applicazione)
    else:
        # ⚠ IL CONTROLLO NEGATIVO: non si accende niente, e si guarda un
        #   desktop che non ha nessuna ragione di cambiare.  ⛔ Qui l'attesa
        #   resta a orologio: non c'e' nessun fotogramma da aspettare, e
        #   aspettarne uno vorrebbe dire aspettare il tetto per niente.
        time.sleep(a.attesa_scena)

    # ── 6. ⛔⛔ IL GUASTO VERO, E ADESSO E' NEL MOMENTO GIUSTO DELLA STORIA ──
    #    ⭐ La scena e' accesa, il programma che la muove e' vivo, e i
    #      fotogrammi si sono visti arrivare: **poi** il codificatore muore.
    #    ⇒ E' questa la domanda che la maglia esiste per fare — «i fotogrammi
    #      si fermano?» — e prima del 27 agosto 2026 non le veniva fatta.
    if modo == "fermo":
        quanti, chi_fermato, preso = ferma_il_codificatore(chi, a.nome_figlio)
        esito["fermati"] = quanti
        esito["pkill_ha_preso"] = preso
        print("           ⛔ `pkill -STOP` %s · processi in stato T: %d%s"
              % ("ha preso" if preso else "⚠ NON ha preso", quanti,
                 (" (%s)" % ", ".join(sorted(set(chi_fermato))[:6]))
                 if chi_fermato else ""))

    # ⭐⭐ QUI SI APRE LA FINESTRA DI MISURA, e l'istante si SEGNA — e' il
    #     denominatore del ritmo, e un denominatore che nessuno segna e' un
    #     numero che dice quel che capita.
    inizio_finestra = time.time()
    cpu_apertura = cpu_del_cliente(cliente.pid)
    time.sleep(a.finestra)
    # ⛔ E IL LAVORO DEL CLIENTE SI RILEGGE **PRIMA** CHE IL CLIENTE MUOIA:
    #    dopo, `/proc/<pid>` non c'e' piu' e la misura sarebbe «non lo so» per
    #    un difetto del banco.
    esito["cpu_finestra"] = lavoro_al_secondo(
        cpu_apertura, cpu_del_cliente(cliente.pid), time.time() - inizio_finestra)

    # ── 8. il cliente finisce ──────────────────────────────────────────────
    coda = chiudi_il_cliente(int(resta) + 240)
    fine = time.time()
    detto = quanti_fotogrammi_dice_il_cliente(coda or "")
    ammesso = e_stato_ammesso(coda)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ E LA SCENA SI RIGUARDA **ADESSO**, alla fine — non solo all'inizio.
    #
    # ⚠ La prima stesura la guardava una volta sola, subito dopo `--attesa-scena`,
    #   e poi dichiarava in testa «vivo dall'inizio alla fine».  ⛔ Ma le coppie
    #   che decidono il verdetto sono gli ULTIMI fotogrammi, cioe' minuti dopo:
    #   una scena che muore a meta' lascia sullo schermo un colore dichiarato
    #   (quindi la guardia sui colori passa) e fotogrammi identici ⇒ ⛔ **rosso
    #   al prodotto per una cosa del browser**, che e' esattamente lo scenario
    #   che il file dice di temere.
    # ⇒ Si pretende viva **alla fine**; e se all'inizio era viva e alla fine no,
    #   lo si dice, perche' e' una diagnosi diversa da «non e' mai partita».
    # ═══════════════════════════════════════════════════════════════════════
    if not a.scena_ferma:
        esito["scena_viva"] = la_scena_e_viva(chi, a.applicazione)

    if ammesso is not True:
        ultimo = "?"
        for riga in reversed((coda or "").strip().splitlines()):
            riga = riga.strip()
            if riga and not riga.startswith("=="):
                ultimo = riga[:90]
                break
        esito["motivo"] = "cliente-non-ammesso"
        esito["perche"] = ("il cliente %s: %s"
                           % ("non e' stato AMMESSO" if ammesso is False
                              else "non ha detto NIENTE", ultimo))
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ IL DENOMINATORE DEL RITMO E' **LA SOLA FINESTRA IN CUI LA SCENA SI
    #     MUOVEVA**, e la scelta va detta per intero perche' decide il verso
    #     dell'errore — `LEZIONI.md` §1.50, un commento che descrive una
    #     grandezza diversa da quella che il codice governa.
    #
    #   numeratore   ⚠ TUTTI i fotogrammi del flusso, quelli della nascita del
    #                desktop compresi: il cliente scrive un file solo, e da un
    #                flusso H.264 senza marcatempo non si taglia un pezzo.
    #   denominatore ⭐ solo da quando la scena era sullo schermo alla fine.
    #
    # ⇒ Il ritmo cosi' e' **SOVRASTIMATO**, cioe' ⛔ **questo controllo e'
    #   OTTIMISTA**: puo' lasciar passare un crollo, non puo' inventarne uno.
    #   ⚠ E' il verso giusto in cui sbagliare — un rosso falso spegne la rete
    #     (§1.3 del documento di fase) — ⛔ ma e' anche la ragione per cui il
    #     ritmo NON e' il controllo che decide: quello e' «i fotogrammi
    #     consecutivi sono diversi», che guarda solo la coda della presa.
    #
    # ⚠⚠ E **di quanto** sovrastimi NON LO SO, e va detto invece di inventare
    #    un limite.  Fuori dalla finestra il desktop e' fermo (`[M]` 0,03
    #    fotogrammi/s, fase 9 §3.1), ⛔ **ma l'applicazione ci sta nascendo
    #    dentro**, e una finestra che si apre disegna eccome.  ⇒ Il termine in
    #    piu' e' «quel che il compositore ha disegnato mentre la scena si
    #    avviava», e nessuno l'ha misurato: `[?]`.
    # ⭐ I tre numeri con cui quel `[?]` si chiude — fotogrammi, secondi, ritmo —
    #   la maglia li stampa a ogni giro.
    #
    # ⚠ Se il palco fosse nato al limite del tetto, la finestra si accorcia ma
    #   NON si falsa: resta quel che e' stata, e il ritmo resta suo.
    # ═══════════════════════════════════════════════════════════════════════
    secondi = max(1.0, fine - inizio_finestra)
    esito["secondi"] = round(secondi, 1)

    if not os.path.exists(flusso) or os.path.getsize(flusso) == 0:
        # ⛔ Nessun byte sul filo.  ⚠ Con la scena FERMA questo e' un risultato
        #   atteso; con la scena in movimento e' il canarino che muore, e lo dice
        #   `giudica_il_flusso`.
        g = giudica_il_flusso([], secondi, a.scena_ferma, a.ritmo_minimo)
        esito.update({k: g[k] for k in ("stato", "motivo", "perche",
                                        "fotogrammi", "ritmo", "coppie",
                                        "diverse", "minima", "massima")})
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ⛔ Il tetto SEGUE il lavoro che governa, invece di stare fermo mentre
    #    `--attesa-palco` cresce (`LEZIONI.md` §1.17).
    elenco, scaduto = estrai_i_fotogrammi(
        flusso, os.path.join(lavoro, "fotogrammi"),
        a.larghezza, a.altezza, max(900.0, resta * 4.0))
    esito["elenco"] = elenco
    if scaduto:
        esito["motivo"] = "estrazione-troncata"
        esito["perche"] = ("il decodificatore non ha finito: l'elenco dei "
                           "fotogrammi e' TRONCATO, e un elenco troncato ha "
                           "l'aspetto di una presa magra ⇒ non giudico")
        sgombra(chi, a.attesa_sgombero)
        return esito
    # ⭐ E i due conti si confrontano PRIMA di giudicare, non dopo: il cliente
    #   dice quanti fotogrammi ha preso dal filo, il decodificatore quanti ne ha
    #   tirati fuori.  ⛔ Se il secondo e' molto piu' basso, il flusso si e'
    #   perso per strada e il ritmo non e' quello del prodotto.
    if detto and elenco and len(elenco) < detto * QUOTA_ESTRATTI:
        esito["fotogrammi"] = len(elenco)
        esito["motivo"] = "estrazione-magra"
        esito["perche"] = ("il cliente dichiara %d fotogrammi e il "
                           "decodificatore ne ha tirati fuori %d (meno del "
                           "%.0f%%): il flusso si e' perso per strada, e il "
                           "ritmo non sarebbe quello del prodotto"
                           % (detto, len(elenco), QUOTA_ESTRATTI * 100))
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ── ⭐ LA SCENA DICHIARATA E' QUELLA CHE STO GUARDANDO? ────────────────
    #    ⛔ Se non lo e', non si giudica: si direbbe rosso al prodotto per una
    #       cosa del browser.
    if elenco and not a.scena_ferma:
        ultimo_png = elenco[-1]
        g = giudice.giudica(ultimo_png)
        fa = lettore.frazione_del_colore(ultimo_png, SCENA_A, TOLLERANZA)
        fb = lettore.frazione_del_colore(ultimo_png, SCENA_B, TOLLERANZA)
        esito["frazione_scena"] = (None if (fa is None or fb is None)
                                   else max(fa, fb))
        if g is not None and g["verdetto"] in ("nero", "quasi-nero"):
            esito["motivo"] = "desktop-nero"
            esito["perche"] = ("l'ultimo fotogramma e' «%s»: la sessione non "
                               "aveva niente da mostrare, e questo non e' un "
                               "giudizio su C3" % g["verdetto"])
            sgombra(chi, a.attesa_sgombero)
            return esito
        if esito["frazione_scena"] is None or esito["frazione_scena"] < FRAZIONE_SCENA:
            esito["motivo"] = "scena-non-mia"
            esito["perche"] = (
                "la scena che ho dichiarato NON e' sullo schermo (i suoi colori "
                "coprono %s, ne pretendo il %.0f%%) ⇒ non posso pretendere che "
                "i fotogrammi cambino: la scena viva? %s"
                % ("non lo so" if esito["frazione_scena"] is None
                   else "%.1f%%" % (esito["frazione_scena"] * 100),
                   FRAZIONE_SCENA * 100,
                   "si'" if esito["scena_viva"] else "⛔ NO"))
            sgombra(chi, a.attesa_sgombero)
            return esito
        if not esito["scena_viva"]:
            esito["motivo"] = "scena-morta"
            esito["perche"] = (
                "il programma che muove la scena %s: non posso dire se "
                "l'immagine era congelata o se non c'era piu' niente da muovere"
                % ("e' MORTO fra l'avvio e la fine"
                   if esito["scena_viva_prima"] else "non e' mai partito"))
            sgombra(chi, a.attesa_sgombero)
            return esito

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LA CODA DEI FOTOGRAMMI CONSEGNATI — e si guarda SEMPRE, anche quando
    #    il verdetto uscira' «crollati».
    #
    # ⛔ `giudica_il_flusso` confronta le coppie **solo se il ritmo regge**: col
    #    codificatore fermo esce da «crollati» prima, e quel numero non lo
    #    calcola mai.  ⚠ Ma e' proprio il numero che dice se il guasto e' caduto
    #    nel momento giusto della storia: se gli ULTIMI fotogrammi arrivati —
    #    quelli dell'istante in cui il codificatore e' morto — erano **diversi
    #    fra loro**, allora la scena c'era e si muoveva, e quel che e' successo
    #    dopo e' che i fotogrammi si sono FERMATI.
    # ⇒ Se invece erano identici, l'innesto e' caduto su un desktop fermo, e il
    #   giro non ha provato niente: esito 3, non un rosso (`collauda_il_fermo`).
    # ═══════════════════════════════════════════════════════════════════════
    # ⚠ E l'elenco puo' essere **None** (il decodificatore non ha tirato fuori
    #   niente): `None` non e' una lista vuota, e affettarlo sarebbe un guasto
    #   del banco con la faccia di un guasto del prodotto.
    m_coda = (coppie_che_cambiano(elenco[-(a.coppie_esaminate + 1):],
                                  SOGLIA_RUMORE, a.soglia_coppia)
              if elenco else None)
    if m_coda is not None:
        esito["coda_coppie"] = m_coda["coppie"]
        esito["coda_diverse"] = m_coda["diverse"]
        esito["coda_frazione"] = m_coda["frazione"]

    g = giudica_il_flusso(elenco, secondi, a.scena_ferma, a.ritmo_minimo,
                          a.frazione_coppie, a.coppie_esaminate,
                          SOGLIA_RUMORE, a.soglia_coppia)
    esito.update({k: g[k] for k in ("stato", "motivo", "perche", "fotogrammi",
                                    "ritmo", "coppie", "diverse", "minima",
                                    "massima")})
    if detto is not None and esito["fotogrammi"] is not None \
            and detto != esito["fotogrammi"]:
        # ⚠ Non e' un verdetto: e' un'informazione.  Il cliente conta i
        #   fotogrammi presi dal filo, ffmpeg quelli che si sono decodificati:
        #   ⛔ se i due numeri divergono molto, il flusso ha dei buchi e chi
        #      diagnostica deve saperlo.
        esito["perche"] += (" ⚠ (il cliente ne dichiara %d, il decodificatore "
                            "ne ha tirati fuori %d)" % (detto, esito["fotogrammi"]))
    sgombra(chi, a.attesa_sgombero)
    return esito


def _n(x):
    return "non lo so" if x is None else x


def stampa(e):
    faccia = {"cambia": "SI ", "congelata": "NO ", "crollati": "NO ",
              "non-lo-so": "?  "}[e["stato"]]
    print("  %-8s %-6s %s  %s" % (e["chi"], e["modo"], faccia, e["perche"]))
    print("           schermi: %s · palco in %s s · fotogrammi %s in %s s "
          "(finestra vera, ⚠ non `--finestra`) · coppie diverse %s/%s"
          % (_n(e["schermi"]), _n(e["palco_s"]), _n(e["fotogrammi"]),
             _n(e["secondi"]), _n(e["diverse"]), _n(e["coppie"])))
    # ⭐⭐ IL MARGINE SI STAMPA SEMPRE, come fa C5: e' il numero che avvisa PRIMA
    #    che una soglia diventi un rosso falso, e la prima stesura lo calcolava
    #    e lo buttava via.
    # ⭐ E DOVE SONO I FOTOGRAMMI GIUDICATI: su un rosso, senza il percorso, non
    #   c'e' niente da guardare senza sapere gia' dove cercare.  ⚠ E restano li'
    #   apposta — il giro dopo dello stesso inquilino li rifa'.
    if e["elenco"]:
        print("           i fotogrammi giudicati (gli ultimi %d di %d): %s"
              % (min(len(e["elenco"]), COPPIE_ESAMINATE + 1), len(e["elenco"]),
                 os.path.dirname(e["elenco"][0])))
    print("           ⭐ margine sulla soglia della coppia: la piu' debole %s · "
          "la piu' forte %s (soglia %.0f%%) · scena sullo schermo %s · viva "
          "alla fine %s"
          % ("non lo so" if e["minima"] is None else "%.2f%%" % (e["minima"] * 100),
             "non lo so" if e["massima"] is None else "%.2f%%" % (e["massima"] * 100),
             SOGLIA_COPPIA * 100,
             "non lo so" if e["frazione_scena"] is None
             else "%.1f%%" % (e["frazione_scena"] * 100),
             _n(e["scena_viva"])))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ I TRE GIUNTI — e stanno in funzioni PURE perche' `--certifica` li provi.
#
# ⛔⛔ E' il pezzo che `LEZIONI.md` §1.52 e' nata per: *«la certificazione di C9
#     provava il giudice, quella di C13 la lettura del registro; il difetto
#     stava nel GIUNTO fra le due — nel codice d'uscita, che non e' di nessuno
#     dei due mestieri»*.  ⇒ Qui il codice d'uscita col guasto innestato e'
#     **invertito**, e da lui `11-gancio.sh` ricava `ha_visto_il_guasto`.
# ═══════════════════════════════════════════════════════════════════════════
LA_PROVA_NON_E_GIRATA = (
    "palco-non-nato", "scena-non-accesa", "cliente-non-ammesso",
    "estrazione-troncata", "estrazione-magra", "desktop-nero",
    "scena-non-mia", "scena-morta", "inquilino-non-creato", "niente-elenco",
    "niente-secondi", "niente-coppie")


def _sano_non_regge(sano, r):
    """La guardia comune ai due collaudi.  Torna l'esito, o `None` se regge.

    ⛔⛔ IL CONTROLLO SANO ROSSO ESCE **3**, E NON 1 — ed e' una correzione.
    La prima stesura usciva 1.  ⚠ Ma `11-gancio.sh` legge un giro innestato AL
    CONTRARIO: `1` ⇒ `ha_visto_il_guasto: false`.  ⇒ ⛔ Una regressione VERA del
    prodotto, capitata proprio durante il giro col guasto innestato, avrebbe
    fatto scrivere a C13 *«la rete non sa piu' dare rosso»* — cioe' il difetto
    di §1.52 prodotto dalla cura di §1.52.
    ⭐ Il rosso vero c'e' gia' e lo da' il giro SENZA guasto, che nella famiglia
      gira subito prima: qui non serve ripeterlo, serve non mentire.
    """
    if sano["stato"] == "non-lo-so":
        r.append("⚠ il giro sano non ha potuto guardare (%s): non posso dire "
                 "se il guasto si sarebbe visto" % (sano["motivo"] or "?"))
        r.append("   ⇒ e questo NON accusa la maglia (§4.5: «innesto non "
                 "giudicato»)")
        return 3
    if sano["stato"] != "cambia":
        r.append("⛔⛔ IL CONTROLLO SANO E' ROSSO: %s" % sano["perche"])
        r.append("    ⇒ questo giro NON misura il guasto — misura un rosso che "
                 "c'e' gia' per conto suo (§1.45).")
        r.append("    ⚠ E l'esito e' 3 e non 1: dire «il guasto non e' stato "
                 "visto» sarebbe un'accusa")
        r.append("      alla rete per una regressione del PRODOTTO. ⇒ Il rosso "
                 "vero lo da' il giro senza guasto.")
        return 3
    return None


def collauda_il_ripetuto(sano, sfregiato, margine_soglia=MARGINE_SOGLIA,
                         soglia_coppia=SOGLIA_COPPIA):
    """`--fotogramma-ripetuto`.  Torna `(esito, [righe])`, esito AL CONTRARIO.

    ⛔⛔ E QUI C'E' UNA COSA CHE VA DETTA, perche' un revisore l'ha trovata e
         aveva ragione: **lo sfregio, da solo, non puo' fallire.**  Se il giro
         sano e' verde, ripetere N volte lo stesso fotogramma da' per forza
         zero coppie diverse: e' aritmetica, ed e' gia' certificata in 0,3
         secondi da `--certifica`.  ⇒ Un giro sul vero che asserisse **solo**
         quello spenderebbe una sessione intera per un bit gia' noto — cioe'
         `LEZIONI.md` §1.44 travestito da collaudo.

    ⭐ Percio' questo collaudo pretende **una cosa in piu', e quella puo'
      fallire davvero**: che la coppia consecutiva **piu' debole** del giro
      sano stia almeno `margine_soglia` volte sopra la soglia.
      ⇒ E' una misura del MONDO — quanto e' vivace la scena vera, vista
        attraverso il prodotto, dopo la codifica — e se un giorno la scena
        diventasse timida (un browser che salta fotogrammi, una codifica che
        appiattisce) **questo numero scenderebbe prima che la maglia cominci a
        dare rossi falsi**.  ⚠ E' la stessa cosa che C5 fa col margine dell'RMS.
    """
    r = []
    esito = _sano_non_regge(sano, r)
    if esito is not None:
        return esito, r
    if sfregiato is None:
        r.append("⚠ non ho un elenco di fotogrammi da sfregiare: non posso "
                 "innestare il guasto (esito 3, non un rosso)")
        return 3, r

    r.append("  sano      : %s" % sano["perche"])
    r.append("  sfregiato : %s" % sfregiato["perche"])
    r.append("")
    if sfregiato["stato"] == "non-lo-so":
        # ⛔ «Non lo so» NON e' «il guasto non e' stato visto»: il primo
        #    fotogramma potrebbe essere illeggibile, e accusare la rete per un
        #    PNG rotto sarebbe la stessa forma d'errore di §1.47.
        r.append("⚠ lo sfregiato non si e' lasciato giudicare (%s): non posso "
                 "dire se il guasto si sarebbe visto" % (sfregiato["motivo"] or "?"))
        r.append("   ⇒ esito 3, non un rosso.")
        return 3, r
    if sfregiato["stato"] != "congelata":
        r.append("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: lo stesso "
                 "fotogramma ripetuto passa per una scena che cambia.")
        r.append("    ⇒ questa maglia non guarda nel posto giusto.")
        return 1, r
    if not (sano["diverse"] and sfregiato["diverse"] == 0):
        r.append("⛔ il verdetto e' cambiato ma il NUMERO no: coppie diverse "
                 "%s ⇒ %s." % (_n(sano["diverse"]), _n(sfregiato["diverse"])))
        return 1, r
    r.append("  ⭐ differenza misurabile, sugli STESSI dati: le coppie diverse "
             "passano da %s a %s su %s"
             % (sano["diverse"], sfregiato["diverse"], sano["coppie"]))

    # ⭐⭐ E LA MISURA CHE PUO' DAVVERO FALLIRE: quanto e' vivace la scena vera.
    minima = sano["minima"]
    if minima is None:
        r.append("⚠ non so quanto cambiasse la coppia piu' debole del giro "
                 "sano: senza quel numero questo collaudo non asserisce niente "
                 "sul mondo (esito 3).")
        return 3, r
    volte = minima / soglia_coppia if soglia_coppia else 0.0
    r.append("  ⭐ e la scena vera e' vivace: la coppia piu' debole cambia il "
             "%.2f%% dei pixel, %.1f volte la soglia (ne pretendo %.1f)"
             % (minima * 100, volte, margine_soglia))
    if volte < margine_soglia:
        r.append("⛔ LA SCENA E' TROPPO TIMIDA, o la soglia e' troppo vicina: "
                 "la coppia piu' debole")
        r.append("   sta a %.1f volte la soglia invece di %.1f. ⇒ Oggi il "
                 "verdetto e' ancora giusto," % (volte, margine_soglia))
        r.append("   ⚠ ma domani un rosso falso e' a un passo, e questa maglia "
                 "avvisa PRIMA invece che dopo.")
        return 1, r
    r.append("")
    r.append("⭐ IL GUASTO INNESTATO E' STATO VISTO — questa maglia SA prendere "
             "l'immagine congelata,")
    r.append("   ⭐ e la scena vera sta larga sulla soglia.")
    return 0, r


def collauda_il_fermo(sano, rotto, quota=QUOTA_GUASTO, quota_lorda=QUOTA_LORDA,
                      frazione_coppie=FRAZIONE_COPPIE,
                      ritmo_minimo=RITMO_MINIMO):
    """`--codificatore-fermo`.  Torna `(esito, [righe])`, esito AL CONTRARIO.

    ⛔⛔ E DAL 27 AGOSTO 2026 QUESTO COLLAUDO PRETENDE ANCHE **CHE IL GUASTO SIA
        CADUTO NEL MOMENTO GIUSTO DELLA STORIA** — perche' prima non lo
        pretendeva, e il giro usciva **3** per la ragione onesta sbagliata.

    Il senso del guasto e' uno solo: ⭐ *la scena c'e' e si muove, poi il
    codificatore muore* ⇒ **i fotogrammi si fermano**.  ⇒ Perche' quel giro
    valga, devono essere vere tre cose che si MISURANO e che possono mancare:

      1. ⭐ i fotogrammi si erano visti arrivare      (`lavoro_visto`)
      2. ⭐ gli ULTIMI fotogrammi consegnati erano diversi fra loro — cioe' la
         scena si stava muovendo nell'istante in cui il codificatore e' morto
         (`coda_frazione`)
      3. ⭐ la finestra era lunga abbastanza perche' i fotogrammi nati PRIMA
         dell'innesto non bastassero a far sembrare vivo il flusso
         (`finestra_bastante`)

    ⛔ Se una manca, l'esito e' **3**: non si e' innestato quel che si credeva,
       e dire «il guasto non e' stato visto» sarebbe un'accusa alla rete per un
       collaudo che non e' girato.
    """
    r = []
    esito = _sano_non_regge(sano, r)
    if esito is not None:
        return esito, r
    if rotto["stato"] == "non-lo-so":
        r.append("⚠ il giro col guasto non ha potuto guardare (%s): non posso "
                 "dire se il guasto si sarebbe visto" % (rotto["motivo"] or "?"))
        r.append("   ⇒ esito 3, non un rosso (§4.5).")
        return 3, r
    # ⚠⚠ LA FIRMA DEL GUASTO — e se manca l'esito e' **3**, non un rosso.
    if not rotto["fermati"] or rotto["pkill_ha_preso"] is False:
        r.append("⚠ l'iniezione non ha fermato niente: `pkill -STOP` %s, e i "
                 "processi di «%s» in stato T sono %s."
                 % ("ha preso" if rotto["pkill_ha_preso"] else "NON ha preso",
                    rotto["chi"], _n(rotto["fermati"])))
        r.append("   ⇒ qualunque verdetto esca NON e' il guasto che credevo di "
                 "aver innestato (§1.52).")
        r.append("   ⇒ esito 3, non un rosso.")
        return 3, r

    # ── ⭐⭐ IL MOMENTO DELL'INNESTO — la cura del 27 agosto 2026 ───────────
    if rotto.get("lavoro_visto") is not True:
        r.append("⚠ prima di fermare il codificatore NON ho mai visto arrivare "
                 "i fotogrammi (il codificatore bruciava %s CPU/s)."
                 % _n(rotto.get("cpu_prima")))
        r.append("   ⇒ ho fermato un codificatore che non stava consegnando: "
                 "non e' «i fotogrammi si fermano»,")
        r.append("     e' «non erano mai partiti». ⛔ Esito 3, non un rosso.")
        return 3, r
    if rotto.get("coda_frazione") is None:
        r.append("⚠ non ho potuto confrontare fra loro gli ultimi fotogrammi "
                 "consegnati: non so se la scena si muovesse")
        r.append("   nell'istante in cui il codificatore e' morto. ⇒ Esito 3.")
        return 3, r
    if rotto["coda_frazione"] < frazione_coppie:
        r.append("⛔ GLI ULTIMI FOTOGRAMMI CONSEGNATI ERANO IDENTICI FRA LORO "
                 "(%s coppie diverse su %s, %.0f%%):"
                 % (_n(rotto["coda_diverse"]), _n(rotto["coda_coppie"]),
                    rotto["coda_frazione"] * 100))
        r.append("   l'innesto e' caduto quando la scena non si muoveva ancora "
                 "⇒ questo giro NON prova «i fotogrammi si fermano»,")
        r.append("   prova «non c'era niente da fermare». ⛔ Esito 3, non un "
                 "rosso — e va spostato l'innesto, non ammorbidito il giudice.")
        return 3, r
    r.append("  ⭐ l'innesto e' caduto nel momento giusto: il codificatore "
             "stava lavorando (%.2f CPU/s) e gli ultimi fotogrammi consegnati"
             % (rotto.get("cpu_prima") or 0.0))
    r.append("     erano diversi fra loro (%s coppie su %s, %.0f%%) ⇒ la scena "
             "c'era e si muoveva, **poi** il codificatore e' morto."
             % (_n(rotto["coda_diverse"]), _n(rotto["coda_coppie"]),
                rotto["coda_frazione"] * 100))

    # ── ⭐ LA FINESTRA ERA LUNGA ABBASTANZA? ───────────────────────────────
    #    ⛔ Il ritmo e' LORDO: coi fotogrammi nati prima dell'innesto un flusso
    #       morto puo' sembrare vivo, e allora il giro non poteva mordere.
    serve = finestra_bastante(rotto.get("secondi_prima"), sano["ritmo"],
                              ritmo_minimo)
    if serve is not None:
        r.append("  ⭐ la finestra: %s s guardati, e per questa scatola ne "
                 "servivano piu' di %.0f (%.1f s di scena in vista prima "
                 "dell'innesto × %.1f/s sani ÷ %.1f/s pretesi)"
                 % (_n(rotto["secondi"]), serve, rotto["secondi_prima"],
                    sano["ritmo"], ritmo_minimo))
        if rotto["secondi"] is None or rotto["secondi"] <= serve:
            r.append("⚠ LA FINESTRA ERA TROPPO CORTA per questo ritmo: i "
                     "fotogrammi nati prima dell'innesto bastano da soli")
            r.append("   a tenere il ritmo lordo sopra la soglia ⇒ il guasto "
                     "non poteva mordere, e non l'ho collaudato.")
            r.append("   ⛔ Esito 3, non un rosso. ⇒ Si rilancia con "
                     "`--finestra-guasto %d`." % int(serve * 2 + 10))
            return 3, r

    if rotto["stato"] == "cambia":
        r.append("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: col codificatore "
                 "fermo i fotogrammi arrivano lo stesso.")
        return 1, r

    # ── ⭐⭐ LA DIFFERENZA MISURABILE, e la NETTA viene prima della lorda ───
    ls = sano.get("cpu_finestra")
    lr = rotto.get("cpu_finestra")
    if ls is None or lr is None:
        r.append("⚠ non so quanto abbia lavorato il cliente dentro la finestra "
                 "(sano %s · guasto %s): senza quel numero" % (_n(ls), _n(lr)))
        r.append("   la differenza non e' misurata, e' solo un verdetto "
                 "cambiato. ⇒ Esito 3.")
        return 3, r
    r.append("  ⭐⭐ differenza misurabile NETTA (numeratore e denominatore "
             "tutt'e due dentro la finestra):")
    r.append("     il lavoro del cliente passa da %.2f a %.2f CPU/s, cioe' il "
             "%.1f%% del sano (ne ammetto al piu' il %.0f%%)"
             % (ls, lr, (lr / ls * 100) if ls else 0.0, quota * 100))
    if ls <= 0 or lr > ls * quota:
        r.append("⛔ il verdetto e' cambiato ma il cliente lavora ancora: i "
                 "fotogrammi non si sono fermati davvero,")
        r.append("   e un collaudo cosi' non certifica la rete (§1.52).")
        return 1, r

    rs = sano["ritmo"] or 0.0
    rr = rotto["ritmo"] or 0.0
    r.append("  ⭐ e la differenza LORDA, che si porta dentro i fotogrammi nati "
             "prima dell'innesto: il ritmo passa da %.2f/s a %.2f/s"
             % (rs, rr))
    r.append("     ⇒ %.2f/s in meno, cioe' il %.1f%% del sano (qui ne ammetto "
             "al piu' il %.0f%%, ⛔ e non il %.0f%%: il numero e' sporco "
             "apposta)"
             % (rs - rr, (rr / rs * 100) if rs else 0.0, quota_lorda * 100,
                quota * 100))
    if rs <= 0 or rr > rs * quota_lorda:
        r.append("⛔ il verdetto e' cambiato ma il NUMERO quasi no: il guasto "
                 "ha morso poco, e un collaudo cosi' non certifica la rete.")
        return 1, r
    r.append("")
    r.append("⭐ IL GUASTO INNESTATO E' STATO VISTO — questa maglia SA dare rosso,")
    r.append("   ⭐ e per la ragione giusta: la scena si muoveva, il "
             "codificatore e' morto, e I FOTOGRAMMI SI SONO FERMATI.")
    return 0, r


def collauda_la_scena_ferma(e):
    """⚠⚠ IL CONTROLLO NEGATIVO — e adesso ASSERISCE qualcosa.

    ⛔ La prima stesura usciva **3 comunque**, e un revisore ha fatto notare che
       cosi' non distingueva *«il banco ha girato e il desktop era davvero
       fermo»* da *«non e' partito niente»*: un contenitore rotto dava lo stesso
       codice d'uscita del controllo riuscito.  ⇒ Cinque minuti di sessione per
       un bit che non poteva variare — `LEZIONI.md` §1.44.

    ⭐ Adesso pretende **tre cose insieme**, e ciascuna puo' mancare:
         · il palco e' nato          (⇒ il giro e' davvero avvenuto)
         · il cliente e' stato ammesso
         · e il verdetto e' «non lo so» **per la ragione giusta**, cioe' il
           motivo `scena-ferma` e non un altro
       ⇒ `0` = il controllo negativo REGGE: a scena ferma questa maglia non da'
         rosso, e l'ho verificato su un giro che e' successo davvero.
       ⇒ `1` = ⛔ a scena ferma la maglia ha dato un verdetto: **e' rotta**.
       ⇒ `3` = il giro non e' avvenuto, e allora non ho controllato niente.
    """
    r = []
    if e["stato"] in ("congelata", "crollati"):
        r.append("⛔⛔ IL CONTROLLO NEGATIVO E' FALLITO: con la scena FERMA "
                 "questa maglia ha dato ROSSO (%s)." % e["stato"])
        r.append("    ⇒ `[M]` fase 9 §3.1: a scena ferma escono 0,03 "
                 "fotogrammi/s ed e' un RISULTATO, non un difetto.")
        r.append("    ⛔ Una maglia che da' rosso li' e' un generatore di rossi "
                 "falsi, e §1.3 dice come va a finire.")
        return 1, r
    if e["motivo"] != "scena-ferma":
        r.append("⚠ il giro non e' arrivato al controllo: si e' fermato prima "
                 "(%s)." % (e["motivo"] or "?"))
        r.append("   ⇒ %s" % e["perche"])
        r.append("   ⛔ Quindi NON ho verificato niente: esito 3, e non lo si "
                 "scambi per un controllo riuscito.")
        return 3, r
    r.append("⭐ IL CONTROLLO NEGATIVO REGGE — il giro e' avvenuto (palco nato, "
             "cliente ammesso),")
    r.append("   la scena era ferma, e questa maglia ⛔ NON ha dato rosso: ha "
             "detto «non lo so» e ha detto perche'.")
    r.append("   ⭐ E il giro lascia il numero con cui si tara `--ritmo-minimo`: "
             "%s fotogrammi in %s s."
             % (_n(e["fotogrammi"]), _n(e["secondi"])))
    return 0, r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente-base", default="c3u")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--scena", default="/opt/remotix/11-c3-scena.html",
                   help="⭐ LA SCENA DICHIARATA: e' questo file a decidere che "
                        "cosa si muove e di quanto")
    p.add_argument("--applicazione", default="firefox-esr",
                   help="⚠ oggi il browser, perche' e' l'unico programma della "
                        "scatola che sappia dipingere una scena che decidiamo "
                        "noi. ⛔ Da spostare appena ce n'e' un altro")
    p.add_argument("--argomenti", default="--kiosk file://%(pagina)s")
    p.add_argument("--nome-figlio", default="remotix",
                   help="come si chiama, nella riga di comando, il processo "
                        "dell'inquilino che codifica e consegna")
    p.add_argument("--lavoro", default="/var/lib/rete11/c3")
    p.add_argument("--larghezza", type=int, default=128)
    p.add_argument("--altezza", type=int, default=72)
    # ⭐ 60 s, e il numero viene da una MISURA: `[M]` 27 agosto 2026, dentro la
    #   scatola GNOME curata il palco nasce in **2,1÷4,2 s** ⇒ 60 s sono piu'
    #   di dieci volte il peggiore misurato.  ⛔ I 200 s di prima erano un
    #   numero prudente scelto quando il fenomeno sembrava durare ~97 s — che
    #   era un guasto della scatola, poi curato (`LEZIONI.md` §1.54).
    # ⚠ E qui non e' una scadenza ma un ADDENDO di `--resta`: ogni secondo di
    #   troppo e' un secondo buttato per ogni inquilino, non un margine.
    p.add_argument("--attesa-palco", type=float, default=60.0,
                   help="⛔ TETTO DA RITARARE: [M] (C1, 27 ago 2026, non mia) "
                        "95-101 s nella scatola GNOME per un difetto della "
                        "SCATOLA; curato quello, ~2 s ⇒ rimettere a ~20")
    p.add_argument("--attesa-scena", type=float, default=30.0,
                   help="⛔ TETTO DA RITARARE [?]: quanto si da' alla scena per "
                        "essere sullo schermo")
    p.add_argument("--finestra", type=float, default=45.0,
                   help="⚠ il MINIMO di secondi in cui si guarda la scena in "
                        "movimento — NON la finestra vera. ⛔ Il cliente resta "
                        "attaccato `--attesa-palco + --attesa-scena + "
                        "--finestra + --coda` secondi in tutto, deciso al "
                        "lancio: se il palco nasce presto, la finestra vera e' "
                        "piu' lunga di questo numero. ⭐ Quella VERA la maglia "
                        "la stampa a ogni giro, ed e' il denominatore del ritmo")
    # ⭐⭐ LA FINESTRA DEL GIRO COL GUASTO E' PIU' LUNGA, e la ragione e' un
    #    conto, non un gusto: `finestra_bastante`.  Il ritmo e' LORDO, ⇒ i
    #    fotogrammi nati fra l'istante in cui la scena ha cominciato a dipingere
    #    e l'istante dell'innesto arrivano **anche col guasto**.  Perche' non
    #    bastino a far sembrare vivo un flusso morto, la finestra dev'essere
    #    lunga rispetto a loro.
    # ⚠ `[?]` 90 s: con ~6 s di scena in vista prima dell'innesto regge fino a
    #   un ritmo sano di ~58/s, cioe' ⭐ oltre il riferimento grezzo di 39/s
    #   (fase 9 §3.1).  ⛔ E la maglia CONTROLLA il conto a posteriori coi numeri
    #   veri del giro: se la finestra non e' bastata lo dice, ed esce 3.
    # ⚠ E vale per **tutt'e due** i giri del collaudo, il sano e il guastato:
    #   due finestre diverse renderebbero i due ritmi non confrontabili.
    p.add_argument("--finestra-guasto", type=float, default=90.0,
                   help="⭐ la finestra dei DUE giri di `--codificatore-fermo`: "
                        "misurare un'assenza costa tempo")
    p.add_argument("--coda", type=float, default=10.0)
    # ⭐ Il segnale vivo «i fotogrammi stanno arrivando»: vedi in testa.
    p.add_argument("--soglia-cpu", type=float, default=SOGLIA_CPU,
                   help="⭐ quanta CPU al secondo deve bruciare il "
                        "CODIFICATORE perche' si dica che i fotogrammi "
                        "ARRIVANO. [?] e la maglia stampa sempre il vero")
    p.add_argument("--passo-cpu", type=float, default=PASSO_CPU,
                   help="ogni quanti secondi si guarda il lavoro del cliente. "
                        "⛔ corto apposta: e' il tempo di scena che finisce nel "
                        "ritmo lordo anche col guasto")
    p.add_argument("--attesa-sgombero", type=float, default=60.0)
    p.add_argument("--ritmo-minimo", type=float, default=RITMO_MINIMO,
                   help="⛔ [?] larga apposta: separa «un rivolo» da «niente», "
                        "NON giudica la fluidita'")
    p.add_argument("--frazione-coppie", type=float, default=FRAZIONE_COPPIE)
    p.add_argument("--coppie-esaminate", type=int, default=COPPIE_ESAMINATE)
    p.add_argument("--soglia-coppia", type=float, default=SOGLIA_COPPIA,
                   help="quanti pixel devono cambiare perche' due fotogrammi "
                        "siano «diversi». [?] da ritarare nella scatola")
    p.add_argument("--margine-soglia", type=float, default=MARGINE_SOGLIA,
                   help="⭐ quante volte la coppia PIU' DEBOLE del giro sano "
                        "deve stare sopra la soglia. ⛔ E' quel che rende non "
                        "vuoto il collaudo `--fotogramma-ripetuto`")
    p.add_argument("--scena-ferma", action="store_true",
                   help="⚠ IL CONTROLLO NEGATIVO: non si accende nessuna scena. "
                        "⛔ In questo modo la maglia NON puo' dare rosso")
    p.add_argument("--fotogramma-ripetuto", action="store_true",
                   help="⛔ GUASTO INNESTATO: si sfregia la copia in memoria "
                        "dell'elenco mettendoci N volte il primo fotogramma. "
                        "L'esito si legge AL CONTRARIO")
    p.add_argument("--codificatore-fermo", action="store_true",
                   help="⛔ GUASTO INNESTATO: SIGSTOP al processo dell'inquilino "
                        "che consegna. L'esito si legge AL CONTRARIO")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    quanti_guasti = sum([a.fotogramma_ripetuto, a.codificatore_fermo])
    if quanti_guasti > 1:
        print("⛔ un guasto per volta: se se ne innestano due non si sa piu' "
              "quale ha morso")
        sys.exit(2)
    if a.scena_ferma and quanti_guasti:
        print("⛔ «scena ferma» e' il CONTROLLO NEGATIVO, non un guasto: con la "
              "scena ferma non c'e' niente da innestare")
        sys.exit(2)
    # ⛔⛔ LE GUARDIE SUI NUMERI — `LEZIONI.md` §1.44: una soglia messa a zero
    #     dalla riga di comando e' un predicato che non puo' piu' fallire, e
    #     `--certifica` non se ne accorgerebbe (certifica le COSTANTI).
    if not 0 < a.frazione_coppie <= 1:
        print("⛔ --frazione-coppie %s: fuori da 0..1 questa maglia non "
              "potrebbe piu' dare ne' rosso ne' verde" % a.frazione_coppie)
        sys.exit(2)
    if a.soglia_coppia <= 0 or a.ritmo_minimo <= 0:
        print("⛔ --soglia-coppia e --ritmo-minimo devono essere maggiori di "
              "zero: a zero nessuna delle due potrebbe piu' dare rosso")
        sys.exit(2)
    if a.coppie_esaminate < 2:
        print("⛔ --coppie-esaminate %d: con meno di due coppie non c'e' niente "
              "da confrontare" % a.coppie_esaminate)
        sys.exit(2)
    if a.soglia_cpu <= 0 or a.passo_cpu <= 0:
        print("⛔ --soglia-cpu e --passo-cpu devono essere maggiori di zero: a "
              "zero «i fotogrammi arrivano» sarebbe vero sempre, anche su un "
              "desktop morto")
        sys.exit(2)
    # ⭐⭐ E LA FINESTRA DEL COLLAUDO COL CODIFICATORE FERMO E' PIU' LUNGA — per
    #    tutt'e due i giri, il sano e il guastato, o i due ritmi non sarebbero
    #    confrontabili.  ⛔ La ragione e' un conto e sta in `finestra_bastante`.
    if a.codificatore_fermo:
        a.finestra = a.finestra_guasto
    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: deve creare inquilini nuovi")
        sys.exit(2)

    giudice, dove_g = giudice_del_desktop()
    if giudice is None:
        print("⛔ non trovo il giudice delle immagini (10-f1-testimone.py) accanto a me")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    lettore, dove_l = lettore_del_colore()
    if lettore is None:
        print("⛔ non trovo il lettore del colore (11-c8-…py) accanto a me")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    for che, dove in (("il cliente di prova", a.cliente),
                      ("la scena dichiarata", a.scena)):
        if not os.path.exists(dove):
            print("⛔ non trovo %s: %s" % (che, dove))
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
    for programma in (a.applicazione, "ffmpeg", "wayland-info", "runuser"):
        if sh("command -v %s" % programma).returncode != 0:
            print("⛔ nella scatola non c'e' %s" % programma)
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
    try:
        import numpy, PIL  # noqa: F401
    except ImportError:
        print("⛔ mancano numpy o Pillow: non posso confrontare due fotogrammi")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)

    # ⭐ PRIMA di ogni `crea`: `crea` fa `userdel -r`, e da quel momento il
    #   padrone di `/tmp/mozilla` sarebbe un NUMERO invece di un nome — cioe'
    #   non lo riconoscerei piu' come mio.
    resto = sgombra_il_mio_rimasuglio(a.utente_base)

    print("== C3 — i fotogrammi arrivano, e la scena CAMBIA ==")
    print("   porta %d · scena %s · applicazione «%s»"
          % (a.porta, os.path.basename(a.scena), a.applicazione))
    print("   metro: ritmo ≥ %.2f/s (riferimento grezzo [M] %.1f/s, fase 9 §3.1 "
          "⇒ %.0f%%) · almeno il %.0f%% delle coppie consecutive diverse"
          % (a.ritmo_minimo, RIFERIMENTO_FPS,
             a.ritmo_minimo / RIFERIMENTO_FPS * 100, a.frazione_coppie * 100))
    print("   ⚠ il ritmo e' LORDO e quindi OTTIMISTA: non e' il controllo che "
          "decide (vedi in testa)")
    print("   giudici importati: %s · %s"
          % (os.path.basename(dove_g), os.path.basename(dove_l)))
    print("   provvista: la cura di src/provisiona.sh, importata da C2, a ogni "
          "inquilino che creo")
    if resto:
        print("   %s" % resto)
    print("   tetti (⛔ da ritarare sul vero): palco %.0f s · scena %.0f s · "
          "finestra %.0f s" % (a.attesa_palco, a.attesa_scena, a.finestra))
    if a.scena_ferma:
        print("   ⚠ CONTROLLO NEGATIVO «scena ferma»: ⛔ questa maglia in "
              "questo modo NON puo' dare rosso, e dira' perche'")
    if a.fotogramma_ripetuto:
        print("   ⛔ GUASTO INNESTATO: «lo stesso fotogramma ripetuto» — sfregia "
              "la COPIA IN MEMORIA, il flusso sul disco non si tocca")
        print("   ⭐ controllo sano e guasto girano sugli STESSI dati: la "
              "differenza non puo' venire da un giro diverso")
    if a.codificatore_fermo:
        print("   ⛔ GUASTO INNESTATO: SIGSTOP al processo «%s» dell'inquilino"
              % a.nome_figlio)
        print("   ⭐ e con lui gira un CONTROLLO SANO, o non si potrebbe "
              "distinguere «il guasto ha morso» da «era gia' rosso»")
        print("   ⭐⭐ e l'innesto cade DOPO che la scena si e' vista muovere "
              "(cura del 27 ago 2026): prima moriva su un desktop vuoto")
        print("   ⚠ finestra %.0f s per tutt'e due i giri: misurare "
              "un'assenza costa tempo (vedi `finestra_bastante`)" % a.finestra)
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ «FOTOGRAMMA RIPETUTO»: un inquilino solo, e si giudica DUE VOLTE gli
    #    stessi dati.
    # ═══════════════════════════════════════════════════════════════════════
    if a.fotogramma_ripetuto:
        e = un_giro("%s1" % a.utente_base, None, a, giudice, lettore)
        stampa(e)
        print()
        sfregiato = giudica_il_flusso(sfregia_ripetendo(e["elenco"]),
                                      e["secondi"] or 1.0, False,
                                      a.ritmo_minimo, a.frazione_coppie,
                                      a.coppie_esaminate, SOGLIA_RUMORE,
                                      a.soglia_coppia) if e["elenco"] else None
        esito, righe = collauda_il_ripetuto(e, sfregiato, a.margine_soglia,
                                            a.soglia_coppia)
        for riga in righe:
            print(riga)
        sys.exit(esito)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ «CODIFICATORE FERMO»: due inquilini, uno sano e uno guastato.
    # ═══════════════════════════════════════════════════════════════════════
    if a.codificatore_fermo:
        sano = un_giro("%s1" % a.utente_base, None, a, giudice, lettore)
        stampa(sano)
        rotto = un_giro("%s2" % a.utente_base, "fermo", a, giudice, lettore)
        stampa(rotto)
        print()
        esito, righe = collauda_il_fermo(sano, rotto, QUOTA_GUASTO,
                                         QUOTA_LORDA, a.frazione_coppie,
                                         a.ritmo_minimo)
        for riga in righe:
            print(riga)
        sys.exit(esito)

    # ═══════════════════════════════════════════════════════════════════════
    # IL GIRO NORMALE — e il CONTROLLO NEGATIVO, che adesso asserisce qualcosa
    # ═══════════════════════════════════════════════════════════════════════
    e = un_giro("%s1" % a.utente_base, None, a, giudice, lettore)
    stampa(e)
    print()
    if a.scena_ferma:
        esito, righe = collauda_la_scena_ferma(e)
        for riga in righe:
            print(riga)
        sys.exit(esito)
    if e["stato"] == "cambia":
        print("⭐ VERDE — i fotogrammi arrivano e la scena CAMBIA.")
        sys.exit(0)
    if e["stato"] == "non-lo-so":
        print("⚠ NON GIUDICO — %s" % e["perche"])
        print("  ⛔ E questo non e' un verde: e' un esito suo (§4.5).")
        sys.exit(3)
    print("⛔⛔ ROSSO — %s" % e["perche"])
    sys.exit(1)


if __name__ == "__main__":
    main()
