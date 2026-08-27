#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c1 — ⭐⭐ LA PRIMA MAGLIA DELLA RETE: «la sessione nasce e si VEDE»
===========================================================================

    python3 11-c1-nasce-e-si-vede.py --giri 8
    python3 11-c1-nasce-e-si-vede.py --certifica

⛔ E' anche il COLLAUDO A della fase 11: puntata contro il codice del 25
   agosto 2026, questa maglia deve diventare ROSSA sulla «sessione che nasce
   cieca» — senza che nessuno le abbia detto dove guardare.

---------------------------------------------------------------------------
⛔⛔ PERCHE' GIRA PIU' VOLTE, e non una sola

`fasi/10-multi-tenant-e-il-budget.md` §7.4: il guasto e' **INTERMITTENTE**.
`[M]` 25 agosto 2026, sulla macchina vera:

    utente        riuscito   fallito
    provanic3         2          6
    provanic4         0         98
    provanic5         0         55

⇒ ⛔ **Una prova sola non e' una prova**: su `provanic3` avrebbe detto verde due
   volte su otto.  ⭐ E' `LEZIONI.md` §1.32 — *«a volte succede» spesso vuol dire
   «succede sempre, aspetta solo il momento»*.

---------------------------------------------------------------------------
⭐ CHE COSA GUARDA — e da dove parte

  da dove parte : ⛔ DA ZERO, e «da zero» qui vuol dire **un UTENTE NUOVO** a
                  ogni giro, non un attacco nuovo.
                  ⚠⚠ E la ragione e' l'invariante I4: il palco appartiene alla
                  SESSIONE, non alla connessione, e **sopravvive al distacco**.
                  ⇒ Riattaccarsi con lo stesso utente NON fa nascere niente:
                  ritrova il palco del giro prima, gia' vivo e gia' col
                  monitor.  ⛔ Un banco cosi' direbbe verde otto volte
                  guardando **una sola nascita** — che e' letteralmente
                  l'errore di metodo per cui il guasto e' rimasto invisibile
                  per giorni (`LEZIONI.md` §1.39).
                  ⭐ Ed e' anche il modo in cui il guasto si e' manifestato sul
                  ferro: utenti NUOVI, `provanic4/5/6`, 0 riusciti su 98/55/50.
  che cosa guarda: ⛔ NON il conto dei processi, che diceva «1» sia con la
                  finestra sia senza.  Guarda **se il monitor e' NATO**, e lo
                  chiede a due testimoni indipendenti (qui sotto).

---------------------------------------------------------------------------
⛔⛔⛔ IL DIFETTO PIU' GROSSO CHE QUESTA MAGLIA ABBIA AVUTO — 27 agosto 2026

⚠ Sta in testa perche' e' il genere di difetto che si ripete, e perche' per
  giorni ha tenuto ferme cinque prove e rinviato una fase intera.

⛔⛔ **C1 non poteva dire verde, e non l'aveva mai detto.**  Le due righe su cui
    giudicava erano tutt'e due sbagliate, e nel modo peggiore:

  1. ⛔ leggeva `sessione [chi] ⛔ ZERO MONITOR` come **prova di cecita'**.
     `[R]` Il prodotto la scrive nel passaggio **obbligatorio di una nascita
     RIUSCITA** (`src/sessione.c:345-348`): dal 14 agosto *«zero monitor
     propri»* e' lo stato **voluto**, e il monitor lo monta la CATTURA, dopo.
     ⇒ La riga che C1 leggeva come il guasto era la riga della salute.
  2. ⛔ e il ramo verde chiedeva `sessione [chi] monitor N/N: connettore`,
     `[R]` che **non compare mai** in una nascita sana: `sessione_stato()` non
     viene piu' chiamata dopo che il palco e' preso.  `[M]` 27 ago 2026, in
     tutto il registro della scatola curata: **0 volte**.

⇒ ⭐⭐ **Un rosso che non si puo' far diventare verde** — `LEZIONI.md` §1.49
  nella sua forma peggiore.  E il verdetto non e' mai stato «C1 sbaglia»: e'
  stato *«la sessione nasce cieca»*, per giorni, su cinque prove.

⛔⛔ E LA CERTIFICAZIONE NON POTEVA PRENDERLO, perche' **imponeva il difetto
    come requisito**: i suoi due casi «sani» usavano proprio la riga che il
    prodotto non scrive.  ⇒ Passava, e passava perche' il giudice era rotto.
  ⭐ La cura non e' solo il giudizio nuovo: e' che adesso esiste **un caso di
    certificazione che parte da un registro SANO e finisce VERDE**.  Un giudice
    che non ha un caso verde non e' un giudice severo: e' un giudice rotto, e
    nessuno se ne accorge finche' qualcuno non prova a farlo passare.

---------------------------------------------------------------------------
⭐⭐ I TRE TESTIMONI — due giudicano, uno si stampa

  ⭐ A · `cattura [chi] formato negoziato: LxA …`     (`src/cattura.c:686`)
        E' **l'istante in cui il monitor nasce**: il `wl_output` compare solo
        quando un consumatore PipeWire si aggancia al flusso.  `[M]` 27 ago
        2026, scatola GNOME curata: **1,105 s · 0,998 s · 0,957 s** dalla riga
        «sessione aperta», e compare **8 volte** in tutto il registro.

  ⭐ B · `⭐ il palco di «chi»: … monitor «Meta-0» (0 prima, 1 dopo), 1920x1080 …`
        (`src/figlio.c:1826`, scritta dal PADRE).  ⛔ Vale come testimone solo
        se dice **tutt'e due** le cose: che un monitor c'e' (**M ≥ 1**) **e** a
        che misura.  ⚠ `monitor «» (0 prima, 2 dopo), 0x0` — il famoso «terzo
        stato» del 25 agosto — non e' un monitor: e' un conteggio senza niente
        sotto, ed e' esattamente il numero che per mesi e' stato letto come
        «due monitor comparsi».

  ⚠ C · `figlio [chi] ciclo: N fotogrammi consegnati` — ⛔ **si stampa e NON si
        giudica**, e la ragione e' §1.45: nessuno ha mai misurato quanto ci
        mette quella riga a comparire dopo la nascita.  ⇒ Metterla nel
        verdetto vorrebbe dire tarare un tetto al buio.  ⭐ Quando manca a
        monitor nato, si stampa un RILIEVO — cosi' si vede, e il giorno in cui
        qualcuno la misurera' si potra' promuovere.

⭐ E i due che giudicano sono INDIPENDENTI sul serio: A la scrive il FIGLIO, B
  la scrive il PADRE.  ⇒ Il giorno in cui una delle due righe cambia forma, C1
  non diventa cieca per conto suo — resta l'altra, e il conto lo dice.

⛔⛔ E UNA RIGA SI SCARTA, per nome: quelle del palco che finiscono con
    *«— aspetto la tela del cliente»*.  `[M]` Su quel ramo (`src/figlio.c:5287`)
    il prodotto spediva al padre una struttura **mai inizializzata** ⇒ i
    conteggi li' dentro sono spazzatura, e si smascheravano da soli
    (`stride 306537694`).  ⚠ La cura c'e' nel prodotto dal 27 agosto, ⛔ ma il
    binario curato non e' ancora nelle scatole.  ⇒ Finche' non c'e', si
    scartano — e ⭐ si CONTANO e si STAMPANO, che un'esclusione muta e'
    un'esclusione di cui nessuno si accorge.

⚠ E qui il metro e' il REGISTRO DEL PRODOTTO, non un'immagine — ⛔ e questo e'
  un limite dichiarato, non un dettaglio: il prodotto potrebbe dire «monitor
  1/1» e consegnare pixel neri.  ⭐ La maglia che guarda i pixel e' C2, e vuole
  il testimone; questa guarda la NASCITA, che e' lo strato di sotto.
  ⇒ `fasi/11-la-rete-di-sicurezza.md` §6, «quel che la rete non prende».

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)

  0  ⭐ ho guardato: tutti i giri sono nati con un monitor
  1  ho guardato: ALMENO UNO e' nato cieco          ⇒ rosso
  3  ⛔ non ho potuto guardare (il server non c'era, il cliente non e' partito,
     il registro non si e' fatto leggere) — ⛔ e NON e' un rosso
  2  il terreno non regge / uso sbagliato
===========================================================================
"""
import argparse
import os
import re
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LE FIRME, prese ALLA LETTERA dal registro del prodotto.
#
# ⛔ Non si cerca una parola dentro un testo (`CODER.md` §3.3-bis, corollario 3:
#    «ACCESA» e' vero anche in «nasce accesa, ed e' spenta»).  Si cercano righe
#    intere, ancorate, e il nome dell'inquilino si CONFRONTA, non si contiene.
#
# ⛔⛔⛔ E QUESTE FIRME SONO STATE RIFATTE DA CAPO IL 27 AGOSTO 2026, perche'
#       le vecchie facevano dire a C1 una cosa falsa.  La storia sta in testa
#       al file, sotto «IL DIFETTO PIU' GROSSO CHE QUESTA MAGLIA ABBIA AVUTO».
# ═══════════════════════════════════════════════════════════════════════════

# ⭐⭐ TESTIMONE A — `src/cattura.c:686`.  E' **l'istante in cui il monitor
#     nasce**: il `wl_output` compare solo quando un consumatore PipeWire si
#     aggancia al flusso, ⇒ questa riga non si puo' scrivere senza un monitor.
#     `[M]` 27 ago 2026, scatola GNOME curata: compare **8 volte**, in
#     1,105 s · 0,998 s · 0,957 s dalla riga «sessione aperta».
FIRMA_FORMATO = re.compile(
    r"cattura +\[(?P<chi>[^\]]+)\] formato negoziato: (?P<l>\d+)x(?P<a>\d+)")

# ⭐⭐ TESTIMONE B — `src/figlio.c:1826`, la riga che il PADRE scrive quando il
#     figlio gli manda `MSG_PALCO`.  ⚠ L'identita' sta nel CORPO («%s») e non
#     nella parentesi, perche' la scrive il padre: e' la stessa ragione per cui
#     C9 tiene quelle righe fuori dall'insieme obbligato.
#     `[M]` 27 ago 2026, scatola curata: `monitor «Meta-0» (0 prima, 1 dopo),
#     1920x1080`.
FIRMA_PALCO = re.compile(
    r"il palco di «(?P<chi>[^»]+)»:.*?monitor «(?P<nome>[^»]*)» "
    r"\((?P<prima>\d+) prima, (?P<dopo>\d+) dopo\), (?P<l>\d+)x(?P<a>\d+) stride")

# ⛔⛔ LA TRAPPOLA, ED E' MISURATA — `src/figlio.c:5287`.
#
# Sul ramo «aspetto la tela del cliente» il prodotto spediva al padre una
# struttura **mai inizializzata**: campo per campo, la memoria dello stack come
# l'aveva lasciata la chiamata di prima.  ⇒ I conteggi di QUELLE righe sono
# spazzatura, e si smascheravano da soli (`stride 306537694`).
# ⚠ `[M]` 27 ago 2026 la cura c'e' nel prodotto (il `memset` e' salito prima di
#   ogni via d'uscita), ⛔ **ma il binario curato non e' ancora nelle scatole**.
# ⇒ Finche' non c'e', quelle righe si SCARTANO per nome — e ⭐ si CONTANO e si
#   STAMPANO: un'esclusione che non si vede e' un'esclusione di cui nessuno si
#   accorge.
CODA_SPAZZATURA = "aspetto la tela del cliente"

# ⭐ TESTIMONE C — i fotogrammi consegnati.  ⚠ Si stampa e NON si giudica:
#   vedi «i tre testimoni» in testa al file, dove sta la ragione.
FIRMA_FOTOGRAMMI = re.compile(
    r"figlio +\[(?P<chi>[^\]]+)\] ciclo: (?P<n>\d+) fotogrammi consegnati")

# ⚠⚠ E QUESTA NON E' PIU' UNA PROVA DI CECITA' — `src/sessione.c:345-348`.
#
# ⛔⛔ Fino al 27 agosto 2026 era **il rosso** di questa maglia.  `[R]` Il
#     prodotto la scrive nel passaggio obbligatorio di una nascita **RIUSCITA**:
#     dal 14 agosto *«zero monitor propri»* e' lo stato **voluto**, e il monitor
#     lo monta la CATTURA, dopo.  ⇒ Si conta e si stampa — perche' e' la riga
#     che per mesi e' stata letta al contrario, e vederla contata a zero
#     giudizi e' quel che impedisce di ricascarci — ⛔ ma non decide niente.
FIRMA_ZERO_MONITOR = re.compile(
    r"sessione \[(?P<chi>[^\]]+)\] .*ZERO MONITOR")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ «IL CLIENTE E' STATO AMMESSO?» — ⭐ E QUESTA E' LA CASA, PER TUTTI.
#
# ⛔ La parola «AMMESSO» dentro l'uscita del cliente NON e' l'ammissione.
#    `[R]` `01-b3-cliente.py` la scrive in **tre** casi, e due sono rifiuti —
#    e tutt'e tre finiscono sullo **stdout**, perche' il rifiuto passa dal
#    gestore in coda al file (`01-b3-cliente.py:2560`), che *stampa* l'errore:
#
#      · ammesso   `01-b3-cliente.py:1615`
#            «   AMMESSO dopo 1023 ms   ⭐ il secondo fisso c'e'»
#      · RIFIUTO 1 `01-b3-cliente.py:1315-1317` (`CONGEDO` al posto suo)
#            «   ⛔ RuntimeError: CONGEDO invece di AMMESSO: motivo 0x03 = …»
#      · RIFIUTO 2 `01-b3-cliente.py:1322` (e' arrivato un altro messaggio)
#            «   ⛔ RuntimeError: atteso AMMESSO, arrivato CONGEDO»
#
# ⇒ ⛔ `"AMMESSO" in uscita` e' **VERO IN TUTT'E TRE**: e' un predicato che non
#   puo' dire di no, cioe' `LEZIONI.md` §1.44 — ⛔ e proprio nel caso che
#   esiste per prendere.  ⚠ Una maglia cosi' crede di essere entrata **anche
#   quando e' stata respinta**, poi guarda il buio che ne segue e lo chiama
#   difetto del prodotto: un rifiuto di credenziali usciva come *«nessun
#   fotogramma e' arrivato dal filo»* — un'accusa al filo.
#
# ⭐ La firma vera e' una RIGA INTERA — `^\s*AMMESSO dopo ` — e ⛔ non e' una
#   sesta soluzione: e' **la stessa** che l'agente delle refutazioni ha messo in
#   `11-c2-…py:311` e `11-c3-…py:331` il 27 agosto 2026.
#
# ⭐⭐ E STA IN UN POSTO SOLO — §1.47.  Cinque copie della stessa riga sono
#     cinque posti da cui divergere di nuovo.  ⇒ C5, C6, C7 e C9 la
#     **importano da qui** e non la riscrivono; se non riescono a importarla
#     escono **3** e lo dicono, ⛔ invece di ripiegare in silenzio sul
#     predicato povero.
#     ⚠ Perche' in C1 e non in un file nuovo: `11-accendi.sh` copia dentro la
#       scatola i file **uno per uno, per nome** (righe 258-274), e un file
#       nuovo non sarebbe copiato ⇒ le cinque maglie uscirebbero 3 in ogni
#       scatola.  ⭐ C1 e' gia' copiata in tutte, e «una maglia che importa da
#       un'altra maglia» e' gia' la forma del progetto (C2 e C3 importano
#       `giudica()` da `10-f1-testimone.py` e `frazione_del_colore()` da C8).
# ═══════════════════════════════════════════════════════════════════════════
FIRMA_AMMESSO = re.compile(r"^\s*AMMESSO dopo ", re.M)


def e_stato_ammesso(coda):
    """⛔ TRE stati, e il terzo non e' un no.

    `True`  — c'e' la riga dell'ammissione.
    `False` — il cliente ha parlato, e quella riga non c'e': **e' un
              rifiuto**, ⛔ non un prodotto rotto ⇒ chi chiama esce **3**.
    `None`  — il cliente non ha detto niente affatto: non lo so.
    """
    if not coda or not coda.strip():
        return None
    return bool(FIRMA_AMMESSO.search(coda))


def certifica_ammissione(sigla):
    """⭐ I casi dell'ammissione, gli stessi per tutte le maglie che la usano.

    ⛔ Vive qui con il predicato: una certificazione che sta lontano dalla cosa
       certificata e' una certificazione che un giorno non segue piu' la cosa.
    Torna `(guai, quanti)`.
    """
    casi = [
        ("⭐ la riga VERA dell'ammissione ⇒ True",
         "   → CIAO\n   ← ECCOMI\n"
         "   AMMESSO dopo 1023 ms   ⭐ il secondo fisso c'e'\n", True),
        ("⭐ ammesso ma sotto il secondo (§4.4-bis violata) ⇒ resta True",
         "   AMMESSO dopo 4 ms   ⛔ MENO DI UN SECONDO: §4.4-bis violata\n",
         True),
        ("⛔ RIFIUTO 1 «CONGEDO invece di AMMESSO» — la parola c'e' ⇒ False",
         "   → CREDENZIALI\n"
         "   ⛔ RuntimeError: CONGEDO invece di AMMESSO: motivo 0x03 = "
         "credenziali sbagliate\n", False),
        ("⛔ RIFIUTO 2 «atteso AMMESSO, arrivato …» — idem ⇒ False",
         "   ⛔ RuntimeError: atteso AMMESSO, arrivato CONGEDO\n", False),
        ("⛔ «in attesa di AMMESSO»: aspettarlo non e' averlo ⇒ False",
         "   [reg] in attesa di AMMESSO\n", False),
        ("⛔ «AMMESSO» attaccato ad altro non e' la riga ⇒ False",
         "   NON-AMMESSO dopo 12 ms\n", False),
        ("⚠ il cliente non ha detto NIENTE ⇒ None, e non e' un «no»",
         "", None),
        ("⚠ solo spazi ⇒ None", "   \n\n  ", None),
        ("⚠ `leggi()` ha fallito (None) ⇒ None", None, None),
    ]
    guai = 0
    print("  ── «AMMESSO» e' una RIGA, non una parola (§1.44) "
          "— il predicato di C1, importato da %s" % sigla)
    for nome, testo, atteso in casi:
        avuto = e_stato_ammesso(testo)
        ok = avuto is atteso
        if not ok:
            guai += 1
        print("  %s  %-62s  %-5s (atteso %s)"
              % ("OK " if ok else "NO ", nome[:62], avuto, atteso))
    return guai, len(casi)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ I GRUPPI DELLA SCHEDA — ⭐ E QUESTA E' LA CASA, PER TUTTE E CINQUE.
#
# ⛔ E' l'altra faccia dello stesso difetto di «AMMESSO»: non un controllo che
#    non puo' fallire, ma **una condizione che non viene garantita** e di cui
#    nessuno si accorge.  ⇒ La maglia misura una sessione CIECA e la chiama
#    difetto del prodotto.
#
# ⭐ `fasi/10-…` §7.4 — «la sessione nasce cieca», il difetto piu' vecchio del
#    progetto — e' stato chiuso il 27 agosto 2026, e la causa e' esattamente
#    questa: l'inquilino non nei gruppi dei nodi `/dev/dri`.
#
#      | inquilini CON i due gruppi | `[M]` **17 su 17** vedono, in ~2 s     |
#      | SENZA                      | `[M]` **0 su 4**, mai in 90 s, 0 fotog.|
#      | ⭐ controprova             | dati i gruppi allo stesso ⇒ **2,04 s** |
#
# ⛔⛔ E QUI DENTRO C'ERANO DUE FALLE, tutt'e due misurabili nel codice:
#   1. `[R]` il ramo `--riusa-utente` **saltava del tutto** il passo dei
#      gruppi: un giro di diagnosi poteva misurare un inquilino cieco;
#   2. `[R]` il ramo che crea inchiodava `usermod -aG video,render` **e non
#      rileggeva**: `video` e `render` sono i nomi di QUESTA distribuzione, e
#      `usermod` riuscito non vuol dire «ci sta dentro» (⛔ E1, «scritto non e'
#      in vigore»).  ⚠ La stessa falla stava in C5, C6, C7 e C9.
#
# ⭐⭐ L'ATTREZZO C'E' GIA' E NON SI RISCRIVE — `banchi/attrezzi-gruppi-scheda.sh`
#     (§1.47).  Legge il gid da ogni `card*`/`renderD*` con `stat -c %g`, chiede
#     il nome a `getent`, mette dentro l'inquilino e **rilegge confrontando i
#     numeri**.  ⛔ Percio' qui non c'e' nessun nome di gruppo e nessun numero.
# ⛔ E se l'attrezzo non si trova NON si inventa una copia e NON si tira a
#    indovinare con `video,render`: si esce **3** e si dice quale riga manca.
# ═══════════════════════════════════════════════════════════════════════════
NOME_ATTREZZO_GRUPPI = "attrezzi-gruppi-scheda.sh"

# ⭐ I codici dell'attrezzo, presi dal suo riquadro (`gruppi_scheda_dai_a`).
#    ⛔ Nessuno di loro e' **1**: un inquilino cieco non e' un prodotto rotto.
CODICI_GRUPPI = {
    0: (0, "⭐ l'inquilino e' nei gruppi dei nodi della scheda: puo' vedere"),
    # ⚠ `2` e' l'attrezzo che dice «va lanciato DA ROOT»: non e' il prodotto e
    #   non e' l'inquilino, e' l'USO ⇒ esito **2**, che ha il suo nome.
    2: (2, "⛔ l'attrezzo dei gruppi va lanciato DA ROOT, e questo banco non "
           "gira da root: e' uso sbagliato, non un difetto"),
    3: (3, "⛔ NON e' nei gruppi dei nodi /dev/dri: la sua sessione nascerebbe "
           "CIECA (`[M]` 0 su 4), e questo banco misurerebbe il buio"),
    4: (3, "⛔ i gruppi sono stati scritti ADESSO ma l'inquilino aveva gia' "
           "processi vivi: scritti si', IN VIGORE NO — la sessione che gira "
           "e' ancora cieca"),
    5: (3, "⛔ un gid dei nodi non ha nessun nome in /etc/group: l'inquilino "
           "non ci puo' entrare"),
}


def verdetto_gruppi(codice):
    """⭐ Dal codice dell'attrezzo all'esito di §4.5.  Torna `(esito, perche)`.

    ⛔ `0` vuol dire «si puo' misurare», non «verde».  ⛔ E non esiste un ramo
       che dia **1**: che un inquilino sia cieco e' un guasto del BANCO (§1.51),
       e accusarne il prodotto e' proprio l'errore che ha rinviato una fase.
    """
    if codice in CODICI_GRUPPI:
        return CODICI_GRUPPI[codice]
    return 3, ("⛔ l'attrezzo dei gruppi e' uscito con un codice che non "
               "conosco (%s): non so dire se l'inquilino veda" % codice)


def trova_attrezzo_gruppi():
    """⛔ Il percorso dell'attrezzo, o `None`.  E' un CERCATORE, non un giudice.

    ⚠ I posti: accanto a me (dentro la scatola tutto sta in `/opt/remotix`), un
      piano piu' su (nel deposito e' `banchi/`), e `/rete11`, che e' il deposito
      montato in sola lettura dentro la scatola.
    """
    qui = os.path.dirname(os.path.abspath(__file__))
    for base in (qui, os.path.dirname(qui), "/opt/remotix", "/rete11",
                 os.path.join("/rete11", "..")):
        p = os.path.join(base, NOME_ATTREZZO_GRUPPI)
        if os.path.exists(p):
            return p
    return None


def garantisci_i_gruppi(chi, prefisso="       "):
    """⭐⭐ Mette l'inquilino nei gruppi della scheda e VERIFICA che ci sia.

    Torna `(esito, perche)`: `0` = si puo' misurare, `3` = ⛔ non si misura.
    ⚠ Stampa quel che dice l'attrezzo, perche' un'esclusione che non si vede e'
      un'esclusione di cui nessuno si accorge.
    """
    attrezzo = trova_attrezzo_gruppi()
    if attrezzo is None:
        print("%s⛔⛔ non trovo `%s`, e senza di lui non posso GARANTIRE che"
              % (prefisso, NOME_ATTREZZO_GRUPPI))
        print("%s    «%s» veda la scheda." % (prefisso, chi))
        print("%s    ⛔ E non me lo riscrivo qui: dieci copie della stessa"
              % prefisso)
        print("%s    riga sono dieci posti da cui divergere (§1.47), e"
              % prefisso)
        print("%s    `video,render` sono i nomi di UNA distribuzione."
              % prefisso)
        print("%s    ⭐ La cura, una riga in `11-accendi.sh` accanto alle altre"
              % prefisso)
        print("%s    `cp` del passo «prodotto»:" % prefisso)
        print("%s        cp /rete11/%s /opt/remotix/"
              % (prefisso, NOME_ATTREZZO_GRUPPI))
        print("%s    ⚠ e perche' `/rete11` lo abbia, una `cp` del deposito"
              % prefisso)
        print("%s    dentro `banchi/11-scatole/` — oppure il montaggio di"
              % prefisso)
        print("%s    `banchi/` invece di `banchi/11-scatole/`." % prefisso)
        return 3, "manca l'attrezzo dei gruppi della scheda"
    r = subprocess.run(["bash", attrezzo, chi], capture_output=True, text=True)
    for riga in (r.stdout or "").splitlines():
        if riga.strip():
            print(riga.rstrip())
    esito, perche = verdetto_gruppi(r.returncode)
    if esito != 0:
        for riga in (r.stderr or "").strip().splitlines()[-3:]:
            print("%s%s" % (prefisso, riga.strip()[:100]))
    return esito, perche


def certifica_gruppi(sigla):
    """⭐ I casi dei gruppi della scheda, gli stessi per tutte le maglie.

    ⛔ Il caso che conta: un inquilino **senza** i gruppi ⇒ la maglia dice
       «non ho potuto guardare» (**3**), ⛔ **mai rosso** — un inquilino cieco
       non e' un prodotto rotto (§1.51).
    Torna `(guai, quanti)`.
    """
    casi = [
        ("⭐ l'attrezzo dice 0 (ci sta dentro davvero) ⇒ si misura", 0, 0),
        ("⛔⛔ NON e' nei gruppi dei nodi ⇒ 3, ⛔ E MAI 1 (il caso vero)", 3, 3),
        ("⚠ l'attrezzo dice «da root» ⇒ 2, uso sbagliato e ha il suo nome",
         2, 2),
        ("⛔ gruppi SCRITTI ma non in vigore (processi gia' vivi) ⇒ 3", 4, 3),
        ("⛔ un gid dei nodi senza nome in /etc/group ⇒ 3", 5, 3),
        ("⚠ un codice che non conosco ⇒ 3, ⛔ non si tira a indovinare", 7, 3),
        ("⚠ `bash` non ha trovato l'attrezzo (127) ⇒ 3", 127, 3),
        ("⚠ l'attrezzo ucciso da un segnale (-9) ⇒ 3", -9, 3),
    ]
    guai = 0
    print("  ── i gruppi della scheda: ⛔ senza, la sessione nasce CIECA "
          "(`[M]` 0 su 4) — il passo di C1, importato da %s" % sigla)
    for nome, codice, atteso in casi:
        e, perche = verdetto_gruppi(codice)
        ok = (e == atteso) and e != 1
        if not ok:
            guai += 1
        print("  %s  %-62s  esito %d (atteso %d)"
              % ("OK " if ok else "NO ", nome[:62], e, atteso))
    # ⛔⛔ E LA GUARDIA CHE TIENE ONESTA LA TABELLA: nessun codice, nemmeno uno
    #     mai visto, deve poter dare **1**.  ⚠ Senza questa riga la tabella
    #     sopra proverebbe solo i codici che ho scritto io.
    rossi = [c for c in list(range(-32, 256)) if verdetto_gruppi(c)[0] == 1]
    ok = not rossi
    if not ok:
        guai += 1
    print("  %s  ⛔⛔ NESSUN codice fra -32 e 255 da' ROSSO (un inquilino "
          "cieco non e' un prodotto rotto)" % ("OK " if ok else "NO "))
    return guai, len(casi) + 1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL TETTO D'ATTESA — ed e' una MISURA, non un numero tondo (§1.45).
#
# `[M]` **27 agosto 2026, scatola GNOME CURATA**, tre sessioni nuove: il
# `formato negoziato` arriva in
#
#         1,105 s        0,998 s        0,957 s        ⇒ massimo **1,105 s**
#
# ⛔⛔ E PRIMA DI OGGI QUESTO NUMERO ERA 152 s, per una misura che non era del
#     prodotto.  `[M]` I ~97 secondi di ritardo erano un guasto della SCATOLA:
#     il §6 della ricetta spostava il gruppo `polkitd` da 991 a 1991 per dare
#     991 a `render`, e `groupmod -g` **non si porta dietro i file** ⇒ `polkitd`
#     non poteva piu' leggere `/etc/polkit-1/rules.d`, moriva, e `gnome-shell`
#     incassava quattro scadenze da 25 s.  ⇒ ⚠ Un tetto tarato su quel numero
#     sarebbe stato **cento volte** il fenomeno vero: ⛔ un tetto cosi' non
#     protegge, **nasconde** — scaduto non ha piu' niente da dire.
#
# ⭐ IL MARGINE, E DA DOVE VIENE — e non e' il margine della dispersione di
#   oggi (0,957-1,105 s, il 15 %), che sarebbe un margine misurato su una
#   macchina sola e a riposo:
#
#     · il fenomeno sano, oggi                      `[M]`  1,105 s
#     · ⚠ la nascita piu' lenta MAI misurata in
#       questo progetto — 26 ago 2026, scatola
#       carica, ed e' la riga che sta nel corpo
#       di `main()` qui sotto                       `[M]` ~13 s
#     · il margine dichiarato su QUELLA             **× 2**
#                                                   ⇒ **26 s**
#
#   ⇒ 26 s sono **24 volte** il fenomeno sano e **due volte** il peggiore mai
#     visto.  ⚠ Il margine sta sul peggiore apposta: la scatola puo' essere
#     carica, e la macchina vera ha una **Intel UHD 730 integrata**, non una
#     scheda potente.  ⛔ Stringere fino a 1 s vorrebbe dire tarare sulla
#     macchina a riposo e chiamare «cieca» la macchina sotto carico.
#
# ⚠ E IL COSTO: `[S]` un giro sano costa ~30 s (20 s di `--resta` + ~1 s
#   d'attesa + lo sgombero), un giro CIECO costa il tetto intero, ~55 s.
#   ⇒ `COSTO_C1_GIRO = 74` nel gancio resta **prudente** e copre tutt'e due:
#   non va cambiato, e i due giri della famiglia veloce (148 s) tornano a
#   starci nei 180 s.
TETTO_NASCITA = 26.0


def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


class Nascita(object):
    """I fatti di UNA nascita, letti dalla fetta di registro di quel giro.

    ⛔ `None` vuol dire «non l'ho visto», mai zero: sono due fatti diversi e non
       devono avere la stessa faccia (§4.5, domanda 8).
    """

    def __init__(self):
        self.nominato = False       # il registro parla di questo inquilino
        self.formato = None         # ⭐ testimone A: (larghezza, altezza)
        self.monitor_dopo = None    # ⭐ testimone B: la M di «(N prima, M dopo)»
        self.monitor_nome = None
        self.monitor_misura = None  # la misura dichiarata dalla riga del palco
        self.fotogrammi = None      # ⚠ testimone C: stampato, NON giudicato
        self.palchi_scartati = 0    # ⛔ le righe «aspetto la tela»: contate
        self.zero_monitor = 0       # ⚠ contata e stampata, NON giudicata


def leggi_nascita(testo, chi):
    """⭐ Il giudice, e non tocca niente: si certifica chiamandolo.

    ⛔ Torna `None` se non c'e' niente da guardare — e `None` non e' «cieca».
    """
    if not testo:
        return None
    n = Nascita()
    marca, virgolette = "[%s]" % chi, "«%s»" % chi

    for riga in testo.splitlines():
        # ⚠ L'omonimia si chiude coi delimitatori: «c1u1» non sta dentro
        #   «c1u10», e `[c1u1]` non sta dentro `[c1u10]`.
        if marca in riga or virgolette in riga:
            n.nominato = True

        m = FIRMA_FORMATO.search(riga)
        if m and m.group("chi") == chi:
            n.formato = (int(m.group("l")), int(m.group("a")))

        m = FIRMA_PALCO.search(riga)
        if m and m.group("chi") == chi:
            # ⛔⛔ LA TRAPPOLA: su quel ramo i conteggi sono spazzatura.
            #    ⭐ Si scarta, si CONTA e si dira' a voce alta.
            if CODA_SPAZZATURA in riga:
                n.palchi_scartati += 1
            else:
                n.monitor_dopo = int(m.group("dopo"))
                n.monitor_nome = m.group("nome")
                n.monitor_misura = (int(m.group("l")), int(m.group("a")))

        m = FIRMA_FOTOGRAMMI.search(riga)
        if m and m.group("chi") == chi:
            n.fotogrammi = int(m.group("n"))

        m = FIRMA_ZERO_MONITOR.search(riga)
        if m and m.group("chi") == chi:
            n.zero_monitor += 1
    return n


def monitor_nato(n):
    """⭐ I due testimoni del monitor, e ne basta UNO — ma sono indipendenti.

    ⚠ Indipendenti sul serio: l'uno lo scrive il FIGLIO (`cattura.c`), l'altro
      il PADRE (`figlio.c`).  ⇒ Il giorno in cui una delle due righe cambiasse
      forma, C1 non diventerebbe cieca: resterebbe l'altra, e il conto
      stampato direbbe che ne parla una sola.
    Torna la lista dei testimoni che hanno parlato.
    """
    if n is None:
        return []
    testimoni = []
    if n.formato is not None and n.formato[0] > 0 and n.formato[1] > 0:
        testimoni.append("formato negoziato %dx%d" % n.formato)
    # ⛔ E il palco vale come testimone solo se dice tutt'e due le cose: che un
    #    monitor c'e' (M ≥ 1) **e** a che misura.  ⚠ `monitor «» (0 prima, 2
    #    dopo), 0x0` — la riga vera del 25 agosto — non e' un monitor: e' un
    #    conteggio senza niente sotto, ed e' proprio la riga che per mesi e'
    #    stata letta come «due monitor comparsi».
    if (n.monitor_dopo is not None and n.monitor_dopo >= 1
            and n.monitor_misura is not None
            and n.monitor_misura[0] > 0 and n.monitor_misura[1] > 0):
        testimoni.append("palco: monitor «%s» (%d dopo) %dx%d"
                         % (n.monitor_nome, n.monitor_dopo,
                            n.monitor_misura[0], n.monitor_misura[1]))
    return testimoni


def verdetto_giro(n):
    """Dai fatti allo STATO del giro.  ⛔ Tre, e sono tre cose diverse:

      «NATA»       ⭐ il monitor c'e', e almeno un testimone lo dice
      «CIECA»      ⛔ la sessione e' partita e il monitor NON e' nato  ⇒ rosso
      «NON-LO-SO»  ⛔ il registro non parla di questo inquilino: non ho
                   guardato niente — ⛔ e NON e' un rosso (§4.5)
    """
    testimoni = monitor_nato(n)
    if testimoni:
        return "NATA", " · ".join(testimoni)
    if n is None:
        return "NON-LO-SO", "la fetta di registro e' vuota"
    if not n.nominato:
        return "NON-LO-SO", ("il registro non nomina «questo» inquilino nella "
                             "fetta: la sessione non e' partita davvero")
    return "CIECA", ("la sessione e' partita e NESSUNO dei due testimoni del "
                     "monitor ha parlato")


# ---------------------------------------------------------------------------
# ⭐⭐ LA CERTIFICAZIONE — e la prima riga della lista e' la piu' importante.
#
# ⛔⛔ FINO AL 27 AGOSTO 2026 QUI NON C'ERA UN SOLO CASO CHE FINISSE VERDE
#     PARTENDO DA UN REGISTRO SANO.  ⚠ I due casi «sessione sana» e «cieca dopo
#     aver montato» usavano la riga `sessione [chi] monitor N/N: connettore`,
#     ⛔ che il prodotto non scrive **mai** in una nascita riuscita — e cosi'
#     la certificazione **imponeva il difetto come requisito**: passava, e
#     passava proprio perche' il giudice era sbagliato.
# ⇒ ⭐ E' `LEZIONI.md` §1.49 nella sua forma peggiore, ed e' la ragione per cui
#   il difetto e' rimasto in piedi: **un giudice che non ha un caso verde non
#   e' un giudice severo, e' un giudice rotto.**
# ---------------------------------------------------------------------------

# ⭐ IL REGISTRO SANO, trascritto dalla scatola GNOME curata (`[M]` 27 ago
#   2026).  ⛔ Non e' inventato: sono le righe che il prodotto scrive davvero,
#   nell'ordine in cui le scrive.
#   ⚠ E c'e' dentro anche `⛔ ZERO MONITOR`, apposta: in una nascita RIUSCITA
#     quella riga c'e', ed e' il passaggio obbligatorio in cui la sessione non
#     ha ancora monitor propri.  ⇒ Se qualcuno un giorno la rimettesse fra i
#     rossi, questo caso diventerebbe rosso e lo direbbe.
SANO = (
    "20:07:42.262 rcp     [c1u1] ammesso utente=c1u1 da=[127.0.0.1]:58048\n"
    "20:07:43.100 figlio  [c1u1] entro nel montaggio del palco (tela 1920x1080): "
    "dico al padre di attendere\n"
    "20:07:43.910 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva: e' la "
    "sessione «viva, completa e NERA» di STUDI.md §gnome §3.1 — non c'e' niente "
    "da catturare\n"
    "20:07:44.367 cattura [c1u1] formato negoziato: 1920x1080 BGRx (8 bit per "
    "canale), modificatore 0x0\n"
    "20:07:44.402 figlio  ⭐ il palco di «c1u1»: bus APERTO, sessione 1, presa 1, "
    "monitor «Meta-0» (0 prima, 1 dopo), 1920x1080 stride 7680 a 32 bit, "
    "1 flussi in consegna\n"
    "20:07:45.100 figlio  [c1u1] ciclo: 37 fotogrammi consegnati (1 chiavi)\n")

# ⛔ IL REGISTRO DEL GUASTO VERO — le righe del 25 agosto 2026, trascritte da
#    `fasi/10-multi-tenant-e-il-budget.md` §7.4 e da `fasi/11…` §7-bis.
#    ⚠ `(0 prima, 2 dopo)` e' il famoso «terzo stato»: ⛔ un conteggio senza
#      niente sotto (`0x0`), che per mesi e' stato letto come «due monitor».
CIECO = (
    "22:42:14.100 rcp     [c1u1] ammesso utente=c1u1 da=[127.0.0.1]:58048\n"
    "22:42:15.826 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva: e' la "
    "sessione «viva, completa e NERA» di STUDI.md §gnome §3.1\n"
    "22:42:18.145 figlio  ⛔ il palco di «c1u1»: bus APERTO, sessione 1, presa 0, "
    "monitor «» (0 prima, 2 dopo), 0x0 stride 0 a 0 bit, 0 flussi in consegna\n")


def certifica():
    """⛔ Si dimostra che il giudice sa dire VERDE, ROSSO e «non lo so».

    ⚠ E si dichiara che cosa copre e che cosa no.
      COPRE: **la lettura del registro e la regola** — che i due testimoni del
      monitor siano riconosciuti, che la riga della spazzatura sia scartata,
      che «⛔ ZERO MONITOR» non decida niente, e ⭐ che un registro SANO
      finisca VERDE.
      ⛔ NON COPRE: che il registro dica la verita' sui pixel.  Quello e' C2, e
      vuole il testimone.
      ⇒ Una certificazione che si dichiara piu' larga di quel che e' vale meno
        di nessuna certificazione.
    """
    casi = [
        # (nome, testo, chi, stato atteso, controllo in piu' o None)

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⭐⭐ IL CASO CHE NON ESISTEVA, ED E' QUELLO CHE CONTA: un registro
        #      SANO deve finire VERDE.  ⛔ Senza di lui il verde di questa
        #      maglia era irraggiungibile e nessuno se ne accorgeva.
        # ═══════════════════════════════════════════════════════════════════
        ("⭐⭐ IL REGISTRO SANO FINISCE VERDE (il caso che non c'era)",
         SANO, "c1u1", "NATA",
         lambda n: n.formato == (1920, 1080) and n.monitor_dopo == 1
                   and n.monitor_misura == (1920, 1080) and n.fotogrammi == 37),

        # ⭐ E i due testimoni sono INDIPENDENTI: ne basta uno, e si prova
        #   togliendo l'altro.  ⇒ Il giorno in cui una delle due righe cambia
        #   forma, C1 non diventa cieca per conto suo.
        ("⭐ col SOLO `formato negoziato` (niente riga del palco) ⇒ VERDE",
         "20:07:43.100 figlio  [c1u1] entro nel montaggio del palco\n"
         "20:07:44.367 cattura [c1u1] formato negoziato: 1920x1080 BGRx\n",
         "c1u1", "NATA", lambda n: n.monitor_dopo is None),

        ("⭐ con la SOLA riga del palco (niente `formato negoziato`) ⇒ VERDE",
         "20:07:43.100 figlio  [c1u1] entro nel montaggio del palco\n"
         "20:07:44.402 figlio  ⭐ il palco di «c1u1»: monitor «Meta-0» "
         "(0 prima, 1 dopo), 1920x1080 stride 7680 a 32 bit, 1 flussi\n",
         "c1u1", "NATA", lambda n: n.formato is None),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔ E IL ROSSO — che e' ancora il guasto vero del 25 agosto.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔ il guasto VERO del 25 agosto ⇒ CIECA",
         CIECO, "c1u1", "CIECA",
         lambda n: n.monitor_dopo == 2 and n.monitor_misura == (0, 0)
                   and n.zero_monitor == 1),

        # ⭐ La meta' che si dimentica (§1.49): tolto il guasto, torna VERDE.
        #   ⛔ E' lo stesso inquilino e la stessa forma di registro.
        ("⭐ e tolto il guasto torna VERDE — la controprova di §1.49",
         SANO, "c1u1", "NATA", None),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ «⛔ ZERO MONITOR» NON DECIDE PIU' NIENTE — ed e' il difetto in
        #     persona.  ⚠ Il registro sano ce l'ha dentro (vedi `SANO`): se
        #     tornasse a essere un rosso, il primo caso della lista fallirebbe.
        #     ⇒ Qui si prova il caso puro: SOLO quella riga, e nient'altro.
        # ═══════════════════════════════════════════════════════════════════
        ("⭐⭐ «ZERO MONITOR» + `formato negoziato` ⇒ VERDE (era il rosso!)",
         "20:07:43.910 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva\n"
         "20:07:44.367 cattura [c1u1] formato negoziato: 1920x1080 BGRx\n",
         "c1u1", "NATA", lambda n: n.zero_monitor == 1),

        # ⚠ E l'altro verso: da sola quella riga non e' un TESTIMONE del
        #   monitor — non lo nega e non lo afferma.  ⇒ Qui il giro resta CIECA
        #   perche' nessuno dei due testimoni ha parlato, ⛔ non perche' c'e'
        #   scritto «ZERO MONITOR».
        ("⛔ «ZERO MONITOR» da sola non e' un TESTIMONE ⇒ resta CIECA",
         "20:07:43.910 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva\n",
         "c1u1", "CIECA", lambda n: n.zero_monitor == 1),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ LA TRAPPOLA MISURATA: la riga del palco che finisce con
        #     «— aspetto la tela del cliente» porta conteggi di SPAZZATURA.
        #     ⚠ `stride 306537694` e' il numero vero che si smascherava da se'.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ la riga «aspetto la tela» si SCARTA (i conteggi sono spazzatura)",
         "20:07:43.100 figlio  [c1u1] entro nel montaggio del palco\n"
         "20:07:43.200 figlio  ⛔ il palco di «c1u1»: monitor «\x01\x02» "
         "(0 prima, 3 dopo), 1440x900 stride 306537694 a 32 bit, 0 flussi in "
         "consegna — aspetto la tela del cliente\n",
         "c1u1", "CIECA",
         lambda n: n.palchi_scartati == 1 and n.monitor_dopo is None),

        ("⭐ …e la riga BUONA che arriva dopo quella scartata vale lo stesso",
         "20:07:43.200 figlio  ⛔ il palco di «c1u1»: monitor «x» (0 prima, "
         "3 dopo), 1440x900 stride 306537694 a 32 bit, 0 flussi in consegna "
         "— aspetto la tela del cliente\n"
         "20:07:44.402 figlio  ⭐ il palco di «c1u1»: monitor «Meta-0» "
         "(0 prima, 1 dopo), 1920x1080 stride 7680 a 32 bit, 1 flussi\n",
         "c1u1", "NATA", lambda n: n.palchi_scartati == 1),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔ «NON HO POTUTO GUARDARE» — e non e' un rosso (§4.5).
        # ═══════════════════════════════════════════════════════════════════
        ("⛔ registro muto ⇒ «non lo so», ⛔ NON cieca",
         "20:07:42.000 avvio   ⭐ pronto: https://…\n", "c1u1", "NON-LO-SO",
         lambda n: not n.nominato),

        ("⛔ la fetta e' VUOTA ⇒ «non lo so», e il giudice torna None",
         "", "c1u1", "NON-LO-SO", None),

        # ⚠ L'omonimia, nei due versi: «c1u1» non e' «c1u10», e nemmeno il
        #   contrario.  ⛔ Un `in` senza delimitatori avrebbe scambiato i due.
        ("⚠ il registro parla di un ALTRO inquilino ⇒ «non lo so»",
         SANO.replace("c1u1", "c1u2"), "c1u1", "NON-LO-SO",
         lambda n: not n.nominato),

        ("⚠ «c1u1» non si confonde con «c1u10» (l'omonimia si chiude)",
         SANO.replace("c1u1", "c1u10"), "c1u1", "NON-LO-SO",
         lambda n: not n.nominato),

        # ⛔ Un monitor «nato» a misura zero non e' nato: e' un conteggio senza
        #    niente sotto.  ⚠ E' il cuore del rosso del 25 agosto, isolato.
        ("⛔ «(0 prima, 1 dopo), 0x0» NON e' un monitor ⇒ CIECA",
         "20:07:43.100 figlio  [c1u1] entro nel montaggio del palco\n"
         "20:07:44.402 figlio  ⛔ il palco di «c1u1»: monitor «» (0 prima, "
         "1 dopo), 0x0 stride 0 a 0 bit, 0 flussi\n",
         "c1u1", "CIECA", lambda n: n.monitor_dopo == 1),

        # ⚠ I fotogrammi si LEGGONO e non decidono: si prova che un monitor
        #   nato senza fotogrammi resta VERDE, e che il conto si vede.
        ("⚠ monitor nato e ZERO fotogrammi ⇒ VERDE (i fotogrammi non giudicano)",
         "20:07:44.367 cattura [c1u1] formato negoziato: 1920x1080 BGRx\n"
         "20:07:45.100 figlio  [c1u1] ciclo: 0 fotogrammi consegnati (0 chiavi)\n",
         "c1u1", "NATA", lambda n: n.fotogrammi == 0),
    ]

    print("== certificazione del giudice di C1 ==")
    print("   ⛔ copre LA LETTURA E LA REGOLA, non i pixel (vedi in testa)\n")
    guai = 0
    for nome, testo, chi, atteso, extra in casi:
        n = leggi_nascita(testo, chi)
        stato, perche = verdetto_giro(n)
        ok = (stato == atteso) and (extra is None or (n is not None and extra(n)))
        print("  %s  %-62s  %-10s (atteso %s)"
              % ("OK " if ok else "NO ", nome[:62], stato, atteso))
        if not ok:
            guai += 1
            print("        ⛔ perche': %s" % perche)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ E IL TETTO SI CERTIFICA COME UNA SOGLIA — ⛔ o e' un numero che
    #     nessuno ricontrolla piu' (`LEZIONI.md` §1.45).
    #
    # ⚠ E il margine sta sul PEGGIORE mai misurato, non sulla dispersione di
    #   oggi: la dispersione di tre misure su una macchina a riposo non dice
    #   niente su una scatola carica.  ⇒ Vedi `TETTO_NASCITA` in testa.
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ I CASI DELL'AMMISSIONE — ⛔ quelli che oggi non c'erano.
    #    Il predicato vive in questo file e serve altre quattro maglie: si
    #    certifica qui, una volta, per tutte.
    print()
    guai_amm, quanti_amm = certifica_ammissione("C1")
    guai += guai_amm

    # ⭐⭐ E I CASI DEI GRUPPI DELLA SCHEDA — ⛔ l'altro caso che non c'era.
    print()
    guai_gr, quanti_gr = certifica_gruppi("C1")
    guai += guai_gr

    MISURE_SANE = (1.105, 0.998, 0.957)   # `[M]` 27 ago 2026, scatola curata
    PEGGIORE_MAI_VISTA = 13.0             # `[M]` 26 ago 2026, scatola carica
    MARGINE = 2.0
    serve = PEGGIORE_MAI_VISTA * MARGINE
    tetto_ok = TETTO_NASCITA >= serve
    if not tetto_ok:
        guai += 1
    print()
    print("  %s  il tetto copre la nascita piu' lenta MAI misurata: "
          "%.0f s × %.0f = %.0f s ⇒ tetto %.0f s"
          % ("OK " if tetto_ok else "NO ", PEGGIORE_MAI_VISTA, MARGINE,
             serve, TETTO_NASCITA))
    print("      ⇒ e sono %.0f volte il fenomeno sano di oggi (%.3f s)"
          % (TETTO_NASCITA / max(MISURE_SANE), max(MISURE_SANE)))

    quanti = len(casi) + quanti_amm + quanti_gr + 1
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi su %d sbagliati"
              % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: il giudice sa dire VERDE, sa dire ROSSO e sa dire"
          % (quanti, quanti))
    print("   «non lo so» — ⭐ e **il verde e' raggiungibile**, che e' la cosa")
    print("   che questa certificazione non provava e avrebbe dovuto provare.")
    print("⚠ e copre la LETTURA, non i pixel (vedi in testa)")
    return 0


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--giri", type=int, default=8,
                   help="quante sessioni NUOVE aprire (il guasto e' intermittente)")
    p.add_argument("--utente-base", default="c1u",
                   help="a ogni giro si crea «<base><n>»: un utente NUOVO, "
                        "perche' riattaccarsi non fa nascere niente (I4)")
    p.add_argument("--riusa-utente", default="",
                   help="⛔ solo per diagnosi: un utente solo per tutti i giri. "
                        "NON e' la prova — ritrova il palco gia' vivo")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--resta", type=float, default=20.0)
    p.add_argument("--attesa-palco", type=float, default=TETTO_NASCITA,
                   help="quanto si aspetta che uno dei due testimoni del "
                        "monitor parli. ⭐ 26 s = la nascita piu' lenta MAI "
                        "misurata (13 s, 26 ago) × 2, cioe' 24 volte il "
                        "fenomeno sano di oggi (1,105 s) — vedi TETTO_NASCITA "
                        "in testa. ⛔ Scaduto NON e' un verde: e' «cieca» se "
                        "la sessione era partita, «non lo so» se non lo era")
    p.add_argument("--attesa-sgombero", type=float, default=45.0,
                   help="quanto si aspetta che l'inquilino del giro precedente "
                        "sia sparito DAVVERO. ⛔ Senza, il giro dopo parte su un "
                        "campo ancora occupato e non giudica")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if not os.path.exists(a.cliente):
        print("⛔ non trovo il cliente di prova: %s" % a.cliente)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if leggi(a.registro) is None:
        print("⛔ non riesco a leggere il registro del server: %s" % a.registro)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    print("== C1 — la sessione nasce e si vede ==")
    print("   %d giri · %s · porta %d"
          % (a.giri,
             ("⛔ UN SOLO utente «%s» (diagnosi, NON e\' la prova)" % a.riusa_utente)
             if a.riusa_utente else
             ("un UTENTE NUOVO a ogni giro: «%s1»…«%s%d»"
              % (a.utente_base, a.utente_base, a.giri)),
             a.porta))
    print("   ⛔ il guasto e' intermittente: un giro solo non sarebbe una prova\n")

    esiti = []
    creati = []
    for giro in range(1, a.giri + 1):
        # ⛔ L'utente NUOVO si crea qui, e si crea come lo creerebbe la
        #    macchina: `useradd -m`, i due gruppi della scheda, la parola.
        #    ⚠ Se questa parte fallisce l'esito e' «non lo so», MAI verde.
        #
        # ⛔⛔ E SI CANCELLA PRIMA DI CREARLO — `[M]` 26 agosto 2026, e questa
        #    riga vale piu' di quel che sembra.
        #    La prima stesura faceva `id -u X || useradd X`: cioe' ⇒ **l'utente
        #    era NUOVO soltanto la PRIMA volta che questo banco girava in vita
        #    sua.**  Dal secondo giro in poi ritrovava «c1u1» com'era rimasto —
        #    e con lui i suoi avanzi.
        #    `[M]` Il sintomo: il gancio ha fatto girare C1 due volte di fila, e
        #    la seconda il primo giro ha detto **«non lo so»** invece di
        #    giudicare.  ⛔ Non un rosso: un giudizio in meno, che e' il modo
        #    silenzioso in cui una prova smette di servire.
        #    ⚠ E' la stessa forma d'errore di C8 col `/tmp/mozilla` rimasto dal
        #      giro prima: ⭐ **«da zero» comprende anche «da zero rispetto a me
        #      stesso di ieri»**.
        if a.riusa_utente:
            chi = a.riusa_utente
        else:
            chi = "%s%d" % (a.utente_base, giro)
            subprocess.run(
                ["/bin/sh", "-c",
                 "loginctl terminate-user %s 2>/dev/null; "
                 "pkill -KILL -u %s 2>/dev/null; "
                 "userdel -r %s 2>/dev/null; rm -rf /home/%s"
                 % (chi, chi, chi, chi)],
                capture_output=True, text=True)
            # ⛔ E i gruppi della scheda NON stanno piu' qui dentro: li da'
            #    l'attrezzo, che li LEGGE dai nodi e poi RILEGGE (vedi in
            #    testa).  ⚠ `usermod -aG video,render` inchiodava due nomi e
            #    non verificava niente.
            fatto = subprocess.run(
                ["/bin/sh", "-c",
                 "useradd -m -s /bin/bash %s && "
                 "printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
                capture_output=True, text=True)
            if fatto.returncode != 0:
                print("  giro %2d/%d  ?    non sono riuscito a creare «%s»: %s"
                      % (giro, a.giri, chi, fatto.stderr.strip()[:80]))
                esiti.append(("NON-LO-SO", None))
                continue
            creati.append(chi)

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ I GRUPPI DELLA SCHEDA — ⭐ SU TUTT'E DUE I RAMI, riuso compreso.
        #
        # ⛔ Fino al 27 agosto 2026 il ramo `--riusa-utente` saltava questo
        #    passo: ⇒ un giro di diagnosi poteva misurare un inquilino CIECO e
        #    chiamarlo difetto del prodotto.  ⚠ E l'altro ramo li dava a nomi
        #    inchiodati senza rileggere, che e' la stessa cosa piu' in piccolo.
        # ⭐ Il passo sta QUI, fuori dall'`if`, cosi' non c'e' un ramo da cui
        #    dimenticarselo di nuovo.
        # ⛔ E se non si puo' garantire, il giro NON misura: «non lo so», ⛔ mai
        #    rosso — un inquilino cieco e' un guasto del banco (§1.51).
        # ═══════════════════════════════════════════════════════════════════
        e_gr, perche_gr = garantisci_i_gruppi(chi)
        if e_gr != 0:
            print("  giro %2d/%d  ?    «%s» non e' in condizione di vedere"
                  % (giro, a.giri, chi))
            print("       %s" % perche_gr)
            esiti.append(("NON-LO-SO", None))
            continue

        # ⛔ Si segna DOVE siamo nel registro PRIMA di aprire, cosi' il giudizio
        #    guarda solo la fetta di QUESTO giro.  Un banco che leggesse tutto
        #    il file leggerebbe i giri precedenti — ed e' successo davvero in
        #    questo progetto (fase 9: un banco leggeva i numeri del banco prima).
        prima = leggi(a.registro)
        segno = len(prima) if prima is not None else 0

        r = subprocess.run(
            ["python3", a.cliente,
             "--indirizzo", a.indirizzo, "--porta", str(a.porta),
             "--utente", chi, "--parola", a.parola,
             "--resta", str(a.resta)],
            capture_output=True, text=True, timeout=max(60, a.resta * 4))
        # ⛔ NON `"AMMESSO" in r.stdout`: la parola c'e' anche nei DUE rifiuti,
        #    e ci arriva sullo stdout — vedi `e_stato_ammesso()` in testa.
        #    `[M]` 26 ago 2026 e' proprio questa maglia che ha pagato il conto:
        #    cinque giri dissero «NON-AMMESSO» e nessuno sapeva perche'.
        # ⭐ Tre stati, e si tengono separati fino in fondo.
        ammesso = e_stato_ammesso((r.stdout or "") + (r.stderr or ""))

        # ⛔⛔ SI ASPETTA L'EVENTO, NON L'OROLOGIO.
        #
        # `[M]` 26 agosto 2026: con un'attesa fissa di 1,5 s **sei giri su sei**
        # hanno detto «non lo so» — non perche' qualcosa fosse rotto, ma perche'
        # il palco nasce in ~13 s e il banco guardava dopo 1,5.
        # ⇒ ⛔ Una scadenza a orologio e' una scadenza che scatta quando capita.
        #
        # ⭐⭐ E SI ESCE DAL CICLO SOLO SUL VERDE — 27 ago 2026.
        #   ⛔ «Cieca» non e' una cosa che si vede: e' una cosa che NON si
        #   vede, e per dire «non l'ho vista» bisogna aver aspettato tutto il
        #   tempo dichiarato.  ⚠ Il ciclo vecchio usciva anche sul rosso, e su
        #   un rosso che era la riga sbagliata — cioe' usciva subito e giudicava
        #   una sessione che stava ancora nascendo.
        n = None
        istante = None
        scadenza = time.time() + a.attesa_palco
        partenza_attesa = time.time()
        while time.time() < scadenza:
            dopo = leggi(a.registro)
            fetta = dopo[segno:] if dopo is not None else None
            n = leggi_nascita(fetta, chi)
            if monitor_nato(n):
                istante = time.time() - partenza_attesa
                break
            time.sleep(0.5)

        stato, perche = verdetto_giro(n)
        fot = None if n is None else n.fotogrammi

        if ammesso is not True:
            # ⛔ «Non ammesso» da solo e' un silenzio: nasconde tre cose
            #    diverse — il cliente non e' partito, il server ha rifiutato,
            #    il filo non c'era.  `[M]` 26 agosto 2026: cinque giri hanno
            #    detto «NON-AMMESSO» e la causa vera era che nella scatola
            #    mancava `aioquic`, cioe' il cliente non poteva nemmeno
            #    provarci.  ⇒ Si porta il MOTIVO accanto al sintomo.
            coda = (r.stdout or "") + (r.stderr or "")
            motivo = "?"
            for riga in reversed(coda.strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:70]
                    break
            # ⭐ E i due «no» si dicono per nome: «respinto» e «non ha parlato»
            #   non sono la stessa cosa, e mescolarli e' quel che rese muti i
            #   cinque giri del 26 agosto.  ⚠ Contano tutt'e due fra i NON
            #   GIUDICATI (esito 3): ⛔ un cliente respinto non e' un prodotto
            #   rotto, e un cliente muto non e' un giudizio.
            stato = "NON-AMMESSO" if ammesso is False else "NON-LO-SO"
            perche = motivo
            faccia = "?"
            print("       ⛔ %s — perche': %s"
                  % ("RESPINTO dal server (non e' un rosso del prodotto)"
                     if ammesso is False
                     else "il cliente non ha detto NIENTE", motivo))
        elif stato == "NATA":
            faccia = "SI"
        elif stato == "CIECA":
            faccia = "NO"
        else:
            faccia = "?"
        esiti.append((stato, fot))
        print("  giro %2d/%d  %-3s  %-10s  fotogrammi: %-9s %s"
              % (giro, a.giri, faccia, stato,
                 "non lo so" if fot is None else fot,
                 ("in %.3f s" % istante) if istante is not None else ""))
        # ⭐ E il TESTIMONE si dice per nome, verde o rosso: un verdetto senza
        #   il suo metro e' un'opinione (C11).
        print("       %s" % perche)
        if n is not None:
            if n.palchi_scartati:
                print("       ⚠ %d righe del palco SCARTATE («%s»): i loro "
                      "conteggi sono spazzatura" % (n.palchi_scartati,
                                                    CODA_SPAZZATURA))
            if n.zero_monitor:
                print("       ⚠ «⛔ ZERO MONITOR» ×%d — ⭐ e NON e' un rosso: e' "
                      "il passaggio obbligatorio di una nascita riuscita"
                      % n.zero_monitor)
            if stato == "NATA" and not n.fotogrammi:
                print("       ⚠ RILIEVO, non verdetto: il monitor e' nato e i "
                      "fotogrammi sono %s — ⛔ questa maglia non li giudica "
                      "(vedi in testa)"
                      % ("zero" if n.fotogrammi == 0 else "non lo so"))

        # ⛔⛔ E ADESSO SI SGOMBRA, o il giro dopo non parte piu' da zero.
        #
        # `[M]` 26 agosto 2026, primo giro vero di questa maglia: senza questo
        # pezzo, i sei giri hanno lasciato **sei sessioni vive** che ritentavano
        # tutte insieme (I4: il palco sopravvive al distacco), e dal secondo giro
        # in poi il compositore non rispondeva piu' ⇒ ⛔ **cinque «non lo so» su
        # sei**.  ⚠ Non erano rossi — il banco ha avuto la decenza di non
        # giudicare — ma una prova che non giudica non serve a niente.
        #
        # ⭐ E lo sgombero e' DELLA PROPRIA cartella soltanto: si chiude l'utente
        #   di QUESTO giro, per nome, mai un modello globale (fase 10 §7.3, dove
        #   un `pkill -f` globale ha rischiato di uccidere il lavoro di un'altra
        #   prova che stava misurando).
        if not a.riusa_utente:
            subprocess.run(["loginctl", "terminate-user", chi],
                           capture_output=True, text=True)
            time.sleep(1.0)
            subprocess.run(["pkill", "-KILL", "-u", chi],
                           capture_output=True, text=True)
            # ⛔⛔ E ADESSO SI ASPETTA CHE SE NE SIA ANDATO DAVVERO, non mezzo
            #    secondo a orologio.
            #
            # `[M]` 26 agosto 2026, dieci giri: ⛔ **`? NO ? NO ? NO ? NO ? NO`**
            # — un'alternanza PERFETTA fra «non lo so» e «cieca».  ⚠ Un'alternanza
            # perfetta non e' un caso: e' **uno stato che sopravvive al giro**.
            # ⇒ L'ipotesi che la spiega: lo sgombero torna SUBITO, e il giro dopo
            #   parte mentre il precedente sta ancora morendo — il compositore
            #   nuovo non riesce nemmeno a nascere, e il registro non dice ne'
            #   «monitor» ne' «cieca» ⇒ «non lo so».  Il giro ancora dopo trova
            #   il campo libero e giudica.
            # ⛔ E una prova che giudica la META' delle volte vale la meta'.
            #   ⭐ Si aspetta l'EVENTO — che l'utente non abbia piu' ne' sessione
            #   ne' processi — e se non se ne va entro il tempo dichiarato, ⚠ si
            #   DICE, invece di partire lo stesso fingendo di non saperlo.
            scadenza = time.time() + a.attesa_sgombero
            libero = False
            while time.time() < scadenza:
                viva = subprocess.run(["loginctl", "show-user", chi],
                                      capture_output=True, text=True).returncode == 0
                proc = subprocess.run(["pgrep", "-u", chi],
                                      capture_output=True, text=True).returncode == 0
                if not viva and not proc:
                    libero = True
                    break
                time.sleep(0.5)
            if not libero:
                print("       ⚠ «%s» non se n'e' andato in %.0f s: il giro dopo "
                      "NON parte da un campo libero" % (chi, a.attesa_sgombero))

    print()
    ciechi = sum(1 for s, _ in esiti if s == "CIECA")
    ignoti = sum(1 for s, _ in esiti if s in ("NON-LO-SO", "NON-AMMESSO"))
    sani = sum(1 for s, _ in esiti if s == "NATA")
    print("  nate con un monitor: %d   ⛔ CIECHE: %d   non giudicate: %d"
          % (sani, ciechi, ignoti))
    print("  ⭐ il metro: il monitor e' nato se lo dice almeno uno dei due")
    print("     testimoni — `cattura … formato negoziato: LxA` (src/cattura.c)")
    print("     oppure `il palco di «chi»: … monitor «N» (x prima, M dopo), LxA`")
    print("     con M ≥ 1 e una misura vera (src/figlio.c).")
    print("  ⛔ e «⛔ ZERO MONITOR» NON e' un testimone: e' il passaggio")
    print("     obbligatorio di una nascita riuscita (src/sessione.c:345).")

    # ⛔⛔ E LA GUARDIA DI §1.44: zero giri giudicati non e' un verde.
    #     ⚠ Senza, `--giri 0` — o otto giri tutti «non ammesso» — uscirebbero
    #     **0** avendo guardato niente, con la faccia di quando guardano.
    if sani == 0 and ciechi == 0:
        print("\n  ⚠ NON GIUDICO — nessun giro ha guardato una nascita.")
        print("     ⛔ E questo non e' un verde: e' un esito suo (§4.5, §1.44).")
        sys.exit(3)

    if ciechi:
        print("\n  ⛔⛔ ROSSO — %d sessioni su %d sono nate CIECHE." % (ciechi, len(esiti)))
        print("     Nessuna applicazione puo' aprire una finestra su quelle sessioni.")
        sys.exit(1)
    if ignoti:
        print("\n  ⚠ NON GIUDICO — %d giri non hanno parlato." % ignoti)
        print("     ⛔ E questo non e' un verde: e' un esito suo (§4.5).")
        sys.exit(3)
    print("\n  ⭐ VERDE — tutte e %d le sessioni sono nate con un monitor." % len(esiti))
    sys.exit(0)


if __name__ == "__main__":
    main()
