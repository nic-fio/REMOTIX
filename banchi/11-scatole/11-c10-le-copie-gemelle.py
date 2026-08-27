#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c10 — ⭐ «LE DUE COPIE GEMELLE DEL PROTOCOLLO COMBACIANO»
===========================================================================

    python3 11-c10-le-copie-gemelle.py
    python3 11-c10-le-copie-gemelle.py --radice /altro/deposito
    python3 11-c10-le-copie-gemelle.py --certifica

⭐ **E' l'unica maglia della lista che non ha bisogno di una scatola.**  Non
   accende niente, non chiede la scheda grafica, non vuole podman: legge dei
   FILE.  ⇒ Gira sul portatile, sulla macchina di prova, dentro una scatola,
   dentro un gancio — `fasi/11…` §4.1, colonna «dove gira»: **ovunque**.
   ⚠ E gira **prima di compilare**, che e' l'altra meta' della riga C10: e'
     esattamente il momento in cui il difetto si puo' ancora fermare a costo
     zero.

---------------------------------------------------------------------------
⭐ PERCHE' ESISTONO DUE COPIE — e non e' una svista da ripulire
---------------------------------------------------------------------------

`rcp.c`, `rcp.h` e `autenticazione.c` stanno in **due cartelle** di questo
deposito, e ci stanno **apposta**:

  `src/`         il modulo montato sul **server di prodotto**
  `banchi/rcp/`  lo stesso modulo montato sull'**innesto dentro l'esempio di
                 ngtcp2** (`bsslserver`), che e' il banco con cui il protocollo
                 e' stato provato a QUIC nudo

⇒ ⭐ **Sono lo stesso modulo montato su due ospiti** — `src/Makefile`, riquadro
  «LE TRE COPIE CHE DEVONO ESSERE UNA» (rilievo R12.3, notte del 10 agosto
  2026), e `DECISIONI.md` §1.12 riquadro «il posto muto», dove la casella di
  `RCP.md` §0-bis dichiara che le due copie sono **identiche byte per byte**.

⛔ **E fino a quella notte erano identiche PER FORTUNA, non per costruzione**:
   nessun file del deposito le confrontava.  Il caso concreto che nessuno
   avrebbe visto, scritto nel Makefile: si cambia `BAN_DURATA` in `src/rcp.c`
   da dodici ore a una.  Il prodotto banna un'ora; `01-b6-lancia.sh` resta
   verde perche' confronta `banchi/rcp/` con la copia compilata dentro
   `examples/`; B8 resta verde perche' accende `bsslserver`.
   ⇒ ⛔ **Il difetto non cambia colore a niente.**

---------------------------------------------------------------------------
⛔⛔ CHE COSA DEVE COMBACIARE — **il file intero, byte per byte**
---------------------------------------------------------------------------

⚠ Questa e' la decisione vera di questa maglia, e non si poteva prendere
  leggendo un commento («scritto non e' in vigore», E1): un `diff` secco su due
  file legittimamente diversi darebbe **rosso per sempre**, e un rosso perpetuo
  non e' prudenza, e' rumore (`LEZIONI.md` §1.49).

⭐ Quindi e' stata **guardata prima di essere dichiarata**.  `[M]` 26 agosto
  2026, su questo deposito:

      rcp.c              identici   md5 8ddf04859e60…   7 691 righe
      rcp.h              identici   md5 432d06e909c7…   1 297 righe
      autenticazione.c   identici   md5 86451cd1c8bb…     202 righe

  ⇒ Non c'e' **nessun** punto legittimamente diverso fra le due copie: non e'
    una «copia del cliente» contro una «copia del server», e' **lo stesso
    file**.  ⭐ Percio' il metro e' il piu' severo possibile — **byte per
    byte** — e puo' esserlo perche' oggi e' verde: la controprova di §1.49
    («prova a farla diventare verde») e' gia' fatta, ed e' il giro vero.

---------------------------------------------------------------------------
⭐⭐ E QUEL CHE QUESTA MAGLIA AGGIUNGE A QUEL CHE C'ERA GIA'
---------------------------------------------------------------------------

Il confronto **c'era gia'**, in due posti, e la riga C10 lo dice: *«c'e' gia',
e va solo agganciata»*.  ⛔ Ma i due posti che c'erano hanno tutt'e due lo
stesso buco, e non e' il confronto:

  `src/Makefile`, bersaglio `impronte`
      ⭐ ferma la costruzione se divergono, e stampa il `diff`.
      ⛔ Ma vuole `make`, un compilatore, `pkg-config`, ngtcp2 e le librerie
        della fase 4: gira **dove si compila**, non ovunque.

  `banchi/04-b23-lancia.sh`, primo blocco
      fa lo stesso confronto in bash.
      ⛔ Ma tiene la **sua** copia dell'elenco, inchiodata nel `for`:
        `for f in rcp.c rcp.h autenticazione.c`.  ⇒ Due elenchi in due file
        che possono allontanarsi senza che nessuno se ne accorga.

⛔⛔ **E IL BUCO COMUNE: nessuno dei due si accorge di una COPPIA NUOVA.**

    L'elenco dei gemelli e' `GEMELLATI` dentro `src/Makefile`, e sono tre nomi
    scritti a mano.  Il giorno in cui nasce un quarto file gemello — mettiamo
    `ban.c` in `src/` e in `banchi/rcp/` — e nessuno tocca quella riga:

      · il Makefile confronta i tre di sempre e dice **OK**
      · `04-b23` confronta i tre di sempre e dice **✅**
      · ⛔ **il quarto diverge per mesi, e non e' rosso da nessuna parte**

    ⇒ ⭐⭐ E' **esattamente** `LEZIONI.md` §1.47: un controllo verde che non ha
      guardato niente, con la stessa faccia di quando guardava davvero.

⭐ Percio' questa maglia fa **tre cose**, e la terza e' la ragione per cui vale
  la pena scriverla invece di limitarsi ad agganciare il Makefile:

  1. **confronta** le copie dichiarate, byte per byte;
  2. ⛔ **non tiene un elenco suo**: `GEMELLATI` lo **LEGGE** da `src/Makefile`.
     ⚠ Un elenco ricopiato qui sarebbe stato il **terzo**, e la terza copia di
       una lista e' il terzo posto da cui puo' divergere.  ⛔ E se non riesce a
       leggerlo **non ripiega su una lista inchiodata**: dice «non ho potuto
       guardare» — una lista di ripiego che sostituisce in silenzio quella vera
       e' la bugia piu' comoda che questa maglia potesse raccontare;
  3. ⭐ **verifica che l'elenco COPRA la cartella**: ogni sorgente che sta in
     `banchi/rcp/` **e anche** in `src/` e' un gemello di fatto, e se non e'
     dichiarato in `GEMELLATI` questa maglia da' **rosso** — anche se i tre
     dichiarati combaciano perfettamente.

---------------------------------------------------------------------------
⛔ QUEL CHE C10 **NON** GUARDA — o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · ⛔ **se `rcp.c` sia GIUSTO.**  C10 dice che le due copie sono d'accordo,
    non che abbiano ragione.  Due copie identiche dello stesso difetto passano;
  · ⛔ **il binario.**  C10 gira PRIMA di compilare: non sa se il `remotix` che
    sta girando da qualche parte e' stato costruito da questi file.  ⇒ Quello e'
    il bersaglio **C11** (`md5` del binario, uguale in tutte le scatole);
  · **le copie di lavoro fuori dal deposito**: `src/rcp-gemello`, `/srv/src/rcp`
    sulla macchina di prova, e la copia innestata dentro `examples/` di ngtcp2.
    Sono **destinazioni**, non gemelli del deposito: `src/costruisci.sh` sceglie
    quale usare, e questa maglia guarda solo la coppia che sta in git;
  · **gli altri «gemelli» del progetto che non sono codice**: la tabella gemella
    di `SPECIFICHE.md` §8.1, e le copie **schierate** che `11-accendi.sh` mette
    dentro le scatole (`prodotto/pagina.html`, `prodotto/remotix`).  ⚠ Quelle
    sono destinazioni di una copia, non un modulo montato su due ospiti — e chi
    le guarda e' **C11**, con l'`md5` del binario;
  · **i file di `banchi/rcp/` che non hanno un fratello in `src/`.**  Oggi non
    ce ne sono; se ce ne fossero, C10 li **nomina** e ⛔ non li giudica: un file
    che vive in un posto solo non ha nessuno con cui combaciare, e chiamarlo
    rosso sarebbe un rosso che non si puo' far diventare verde (§1.49).

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ le copie gemelle combaciano, e l'elenco copre tutta la cartella
  1  ⛔ ROSSO: almeno una coppia diverge, **oppure** un gemello di fatto non e'
     dichiarato in `GEMELLATI` (cioe' nessuno lo sta guardando)
  3  ⛔ non ho potuto guardare: `GEMELLATI` illeggibile o vuoto, la cartella
     gemella non c'e', un file dichiarato manca da una parte
     — ⛔ **e non e' un rosso**
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ⛔ I DUE PERCORSI, dichiarati qui e stampati in ogni esito: «combaciano» e'
#    un verdetto, e un verdetto senza il suo metro e' un'opinione.
CASA = "src"
GEMELLA = "banchi/rcp"
MAKEFILE = "src/Makefile"

# ⚠ Quali file della cartella gemella sono CODICE, cioe' quali possono essere
#   un gemello.  ⛔ L'elenco e' dichiarato invece che dedotto: un `README.md`
#   messo un giorno in `banchi/rcp/` non deve diventare un rosso perpetuo.
SUFFISSI_SORGENTE = (".c", ".h")


# ---------------------------------------------------------------------------
def senza_commento(riga):
    """⛔⛔ In un Makefile un `#` apre un commento fino a fine riga.

    ⚠ Difetto vero di questa maglia, trovato il 27 ago 2026 da un agente
      mandato a smentirla.  Senza questa riga:

        GEMELLATI := rcp.c rcp.h autenticazione.c  # i tre di sempre
        ⇒ elenco: ['rcp.c','rcp.h','autenticazione.c','#','i','tre','di','sempre']
        ⇒ esito 3, ⛔ **e per sempre** — che e' §1.49 con l'aria di prudenza,
          e la maglia stessa dice piu' sotto che *«un 3 ripetuto non e' un
          esito: e' un guasto del banco»*.

    ⛔⛔ E c'e' un secondo verso, peggiore: se il commento NOMINA un file
        (`# e un giorno ban.c`), quel nome entrava nell'elenco **come
        dichiarato** ⇒ la guardia *«e' un gemello che nessuno sta guardando»*
        non scattava piu'.  ⇒ Il rosso piu' prezioso di C10 — quello che
        nessun altro qui faceva — si spegneva con un carattere.
    """
    return riga.split("#", 1)[0]


def elenco_dichiarato(percorso_makefile):
    """⭐ Legge `GEMELLATI` da `src/Makefile`.

    ⛔ Torna `None` se non l'ha trovato, e ⛔ **non ripiega su un elenco
       inchiodato**: «non ho letto l'elenco» e «l'elenco e' quello di sempre»
       sono due fatti diversi, e il secondo con l'aria del primo e' un
       controllo spento che sembra acceso (`src/Makefile`, R12.3).
    ⚠ E `None` non e' la lista vuota: la lista vuota vuol dire «il Makefile
      dichiara zero gemelli», che e' un altro fatto ancora — e passerebbe il
      confronto senza aver guardato niente (`LEZIONI.md` §1.47).
    """
    try:
        with open(percorso_makefile, "r", encoding="utf-8", errors="replace") as f:
            testo = f.read()
    except OSError:
        return None
    # ⚠ Si prendono le ASSEGNAZIONI, non una riga qualunque che nomini la
    #   variabile: `$(GEMELLATI)` compare anche nel corpo della regola.
    #
    # ⛔ E si prendono TUTTE, `+=` compresa.  ⚠ La prima stesura di questa
    #    maglia si fermava alla prima: il giorno in cui qualcuno avesse
    #    aggiunto un quarto gemello con `GEMELLATI += ban.c`, C10 non lo
    #    avrebbe visto nell'elenco e lo avrebbe accusato di **non essere
    #    dichiarato** ⇒ un rosso falso su una dichiarazione corretta, cioe'
    #    la forma d'errore di `LEZIONI.md` §1.49.
    #
    # ⛔ E le righe si RICUCISCONO se finiscono con la barra rovescia: un
    #    elenco spezzato su due righe e' normalissimo in un Makefile, e
    #    leggerne solo la prima meta' avrebbe lo stesso effetto di sopra.
    #
    # ⛔⛔ E IL COMMENTO IN CODA SI TAGLIA — difetto vero, trovato il 27 ago
    #    2026 (vedi `senza_commento`).  ⚠ La certificazione aveva il caso del
    #    commento a riga INTERA e non quello in CODA, che e' la cosa piu'
    #    normale del mondo dentro un Makefile.
    righe = []
    continua = False
    for riga in testo.splitlines():
        if continua:
            righe[-1] += " " + senza_commento(riga).rstrip()
        elif re.match(r"^GEMELLATI\s*[:?+]?=", riga):
            righe.append(senza_commento(riga).rstrip())
        else:
            continua = False
            continue
        continua = righe[-1].endswith("\\")
        if continua:
            righe[-1] = righe[-1][:-1]
    if not righe:
        return None
    nomi = []
    for riga in righe:
        for n in riga.split("=", 1)[1].split():
            if n not in nomi:
                nomi.append(n)
    return nomi


def leggi(percorso):
    try:
        with open(percorso, "rb") as f:
            return f.read()
    except OSError:
        return None


def impronta(percorso):
    """⚠ L'impronta serve a STAMPARE, non a giudicare: il confronto e' fatto
       sui byte (vedi `guarda`).  ⛔ «byte per byte» dev'essere vero alla
       lettera, non «uguale a meno di un'impronta»."""
    dati = leggi(percorso)
    return None if dati is None else hashlib.md5(dati).hexdigest()


# ---------------------------------------------------------------------------
def guarda(radice):
    """Raccoglie i FATTI.  ⛔ Non giudica: giudicare e' un altro mestiere, e
       tenerli separati e' quel che permette di certificare il giudice su casi
       sintetici senza toccare i file veri."""
    f = {
        "radice": radice,
        "makefile": os.path.join(radice, MAKEFILE),
        "casa": os.path.join(radice, CASA),
        "gemella": os.path.join(radice, GEMELLA),
    }
    f["elenco"] = elenco_dichiarato(f["makefile"])
    f["gemella_c_e"] = os.path.isdir(f["gemella"])
    f["casa_c_e"] = os.path.isdir(f["casa"])

    # ⭐ Le coppie dichiarate, una per una.
    f["coppie"] = []
    for nome in (f["elenco"] or []):
        a = os.path.join(f["casa"], nome)
        b = os.path.join(f["gemella"], nome)
        ci_a, ci_b = os.path.isfile(a), os.path.isfile(b)
        if not ci_a and not ci_b:
            stato = "mancano-tutt-e-due"
        elif not ci_a:
            stato = "manca-in-src"
        elif not ci_b:
            stato = "manca-nel-gemello"
        else:
            # ⛔ Byte per byte, e alla lettera: si confrontano i BYTE, non le
            #    righe e nemmeno le impronte.  Un file che differisce solo per
            #    un fine-riga e' un file diverso, e il compilatore lo sa anche
            #    se `diff` in certi modi non lo mostra.
            da, db = leggi(a), leggi(b)
            stato = "identici" if (da is not None and da == db) else "divergono"
        f["coppie"].append({"nome": nome, "stato": stato,
                            "md5": impronta(a) or impronta(b)})

    # ⭐⭐ E ADESSO LA PARTE CHE NESSUNO FACEVA: l'elenco copre la cartella?
    f["non_dichiarati"] = []   # sta in tutt'e due le cartelle, ma non in GEMELLATI
    f["solo_nel_banco"] = []   # sta solo in `banchi/rcp/`: non ha un gemello
    f["estranei"] = []         # non e' un sorgente: si nomina e non si giudica
    if f["gemella_c_e"]:
        for nome in sorted(os.listdir(f["gemella"])):
            if not os.path.isfile(os.path.join(f["gemella"], nome)):
                continue
            if not nome.endswith(SUFFISSI_SORGENTE):
                f["estranei"].append(nome)
                continue
            if f["elenco"] is not None and nome in f["elenco"]:
                continue
            if os.path.isfile(os.path.join(f["casa"], nome)):
                f["non_dichiarati"].append(nome)
            else:
                f["solo_nel_banco"].append(nome)
    return f


# ---------------------------------------------------------------------------
def giudica(f):
    """Dai fatti al verdetto.  Torna `(esito, motivi)`.

    ⛔ L'ordine non e' un dettaglio: un ROSSO trovato e' un giudizio gia' dato,
       e non si annacqua in «non ho potuto guardare» perche' un ALTRO file
       mancava.  ⇒ prima il rosso, poi il 3, poi il verde.
    """
    motivi = []

    # ── 3 · non c'e' niente da confrontare, e va detto ─────────────────────
    if f["elenco"] is None:
        return 3, ["⛔ non ho letto `GEMELLATI` da %s: non so che cosa dovrebbe "
                   "combaciare" % MAKEFILE]
    if not f["elenco"]:
        return 3, ["⛔ `GEMELLATI` e' VUOTO: zero coppie da confrontare — e "
                   "«zero differenze su zero coppie» sarebbe un verde che non ha "
                   "guardato niente (LEZIONI.md §1.47)"]
    if not f["gemella_c_e"]:
        return 3, ["⛔ la cartella gemella «%s» NON C'E': non e' «le copie "
                   "combaciano», e' «non ho potuto guardare»" % GEMELLA]
    if not f["casa_c_e"]:
        return 3, ["⛔ la cartella «%s» NON C'E'" % CASA]

    # ── 1 · i rossi ────────────────────────────────────────────────────────
    divergono = [c["nome"] for c in f["coppie"] if c["stato"] == "divergono"]
    for nome in divergono:
        motivi.append("⛔ %s DIVERGE fra %s/ e %s/" % (nome, CASA, GEMELLA))
    for nome in f["non_dichiarati"]:
        motivi.append("⛔ «%s» sta in tutt'e due le cartelle ma NON e' in "
                      "`GEMELLATI`: e' un gemello che nessuno sta guardando"
                      % nome)
    if divergono or f["non_dichiarati"]:
        return 1, motivi

    # ── 3 · ho guardato, e un pezzo non ha potuto parlare ──────────────────
    mancanti = [c for c in f["coppie"] if c["stato"] != "identici"]
    if mancanti:
        for c in mancanti:
            motivi.append("⛔ %s: %s" % (c["nome"], c["stato"].replace("-", " ")))
        motivi.append("⇒ «non ho trovato differenze» e «non ho potuto guardare» "
                      "hanno la stessa faccia: questo e' il secondo")
        return 3, motivi

    # ── 0 ──────────────────────────────────────────────────────────────────
    return 0, ["⭐ le %d coppie dichiarate combaciano byte per byte, e "
               "l'elenco copre tutta la cartella gemella" % len(f["coppie"])]


# ---------------------------------------------------------------------------
# ⭐ LA CERTIFICAZIONE — §3.6: «ogni prova ha il suo guasto innestato, e quel
#    caso va fatto girare, non immaginato».
#
# ⛔ E si fa su copie SINTETICHE in una cartella temporanea: i file veri del
#    deposito non si toccano nemmeno per un istante.  ⚠ Un banco che innesta un
#    guasto sui file veri e' un banco che, se muore a meta', lascia il deposito
#    guasto — e il guasto ha l'aria di essere del prodotto.
# ---------------------------------------------------------------------------
MAKEFILE_FINTO = (
    "# Makefile sintetico della certificazione di C10\n"
    "SORGENTI := main.c rcp.c\n"
    "GEMELLATI := rcp.c rcp.h autenticazione.c\n"
    "tutto: impronte\n"
    "\t@echo $(GEMELLATI)\n"
)


def scena(dove, elenco_makefile=MAKEFILE_FINTO, contenuti=None, gemello=None):
    """Costruisce un deposito finto: `src/`, `banchi/rcp/`, `src/Makefile`."""
    contenuti = contenuti or {"rcp.c": b"protocollo\n",
                              "rcp.h": b"intestazioni\n",
                              "autenticazione.c": b"pam\n"}
    gemello = contenuti if gemello is None else gemello
    os.makedirs(os.path.join(dove, CASA), exist_ok=True)
    if gemello is not False:
        os.makedirs(os.path.join(dove, GEMELLA), exist_ok=True)
    if elenco_makefile is not None:
        with open(os.path.join(dove, MAKEFILE), "wb") as f:
            f.write(elenco_makefile.encode("utf-8"))
    for nome, dati in contenuti.items():
        with open(os.path.join(dove, CASA, nome), "wb") as f:
            f.write(dati)
    if gemello is not False:
        for nome, dati in gemello.items():
            with open(os.path.join(dove, GEMELLA, nome), "wb") as f:
                f.write(dati)
    return dove


def certifica():
    sano = {"rcp.c": b"protocollo\n", "rcp.h": b"intestazioni\n",
            "autenticazione.c": b"pam\n"}
    # ⛔ Un BYTE, non una riga: se il giudice prendesse solo le differenze
    #    grosse, la taratura di `BAN_DURATA` da 12 a 1 gli sfuggirebbe.
    un_byte = dict(sano, **{"rcp.c": b"protocollo\r\n"})
    senza_uno = {k: v for k, v in sano.items() if k != "rcp.h"}
    quarto_uguale = dict(sano, **{"ban.c": b"ban\n"})
    quarto_diverso_src = dict(sano, **{"ban.c": b"ban DODICI ore\n"})
    quarto_diverso_gem = dict(sano, **{"ban.c": b"ban UNA ora\n"})

    casi = [
        # (nome, come si costruisce la scena, esito atteso)
        ("le tre copie sono identiche ⇒ VERDE",
         dict(contenuti=sano), 0),

        ("⛔ UN BYTE cambiato in una copia ⇒ ROSSO",
         dict(contenuti=sano, gemello=un_byte), 1),

        ("⛔ e la controprova di §1.49: tolto il byte, torna VERDE",
         dict(contenuti=sano, gemello=sano), 0),

        ("⛔ una copia gemella MANCA ⇒ 3, non ho potuto guardare",
         dict(contenuti=sano, gemello=senza_uno), 3),

        ("⛔ la cartella gemella non c'e' affatto ⇒ 3",
         dict(contenuti=sano, gemello=False), 3),

        ("⛔ `GEMELLATI` illeggibile (niente Makefile) ⇒ 3",
         dict(contenuti=sano, elenco_makefile=None), 3),

        ("⛔ `GEMELLATI` VUOTO ⇒ 3 — zero coppie non e' un verde",
         dict(contenuti=sano,
              elenco_makefile="GEMELLATI :=\n"), 3),

        ("⭐⭐ un QUARTO gemello non dichiarato, e IDENTICO ⇒ ROSSO lo stesso",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale), 1),

        ("⭐⭐ …e infatti eccolo DIVERSO: era rosso perche' nessuno lo guardava",
         dict(contenuti=quarto_diverso_src, gemello=quarto_diverso_gem), 1),

        ("⚠ un file solo nel banco (nessun fratello in src/) NON e' un rosso",
         dict(contenuti=sano,
              gemello=dict(sano, **{"innesto-solo-banco.c": b"x\n"})), 0),

        ("⚠ un file non-sorgente in banchi/rcp/ NON e' un rosso",
         dict(contenuti=sano,
              gemello=dict(sano, **{"APPUNTI.md": b"note\n"})), 0),

        # ⛔ I DUE CASI CHE PRENDONO UN DIFETTO DI QUESTA MAGLIA STESSA, non del
        #    prodotto: un quarto gemello DICHIARATO in un modo che la prima
        #    stesura non sapeva leggere ⇒ lo avrebbe accusato di non essere
        #    dichiarato.  ⭐ Un rosso falso su una dichiarazione corretta e'
        #    esattamente §1.49, e qui e' innestato e provato.
        ("⛔ dichiarato con `GEMELLATI += ban.c` ⇒ VERDE, non un rosso falso",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h autenticazione.c\n"
                              "GEMELLATI += ban.c\n"), 0),

        ("⛔ dichiarato su DUE righe con la barra rovescia ⇒ VERDE",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h \\\n"
                              "             autenticazione.c ban.c\n"), 0),

        ("⛔ …e con la barra rovescia il quarto DIVERGE ⇒ ROSSO lo stesso",
         dict(contenuti=quarto_diverso_src, gemello=quarto_diverso_gem,
              elenco_makefile="GEMELLATI := rcp.c rcp.h \\\n"
                              "             autenticazione.c ban.c\n"), 1),

        ("⚠ una riga di COMMENTO che nomina GEMELLATI non e' una dichiarazione",
         dict(contenuti=sano,
              elenco_makefile="# GEMELLATI := tutto quel che vuoi\n"
                              "GEMELLATI := rcp.c rcp.h autenticazione.c\n"), 0),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ I CASI CHE OGGI NON C'ERANO — 27 ago 2026.  ⚠ Il caso qui sopra
        #     ha il commento a riga INTERA; ⛔ quello in CODA e' la cosa piu'
        #     normale del mondo, e non era certificato.  `[D]` Prima della cura
        #     il primo di questi tre dava **3 per sempre** e il secondo
        #     **spegneva il rosso piu' prezioso di C10**.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ un `#` in CODA alla riga non avvelena l'elenco ⇒ VERDE",
         dict(contenuti=sano,
              elenco_makefile="GEMELLATI := rcp.c rcp.h autenticazione.c"
                              "  # i tre di sempre\n"), 0),

        ("⛔⛔ un commento che NOMINA un file NON lo dichiara ⇒ ROSSO",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h autenticazione.c"
                              "  # e un giorno ban.c\n"), 1),

        ("⛔ e il commento in coda a una riga RICUCITA con la barra rovescia",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h \\\n"
                              "             autenticazione.c ban.c  # i quattro\n"),
         0),
    ]

    print("== certificazione del giudice di C10 ==")
    print("   ⛔ su copie SINTETICHE in una cartella temporanea: i file veri")
    print("      del deposito non si toccano.\n")
    guai = 0
    for nome, come, atteso in casi:
        dove = tempfile.mkdtemp(prefix="c10-cert-")
        try:
            scena(dove, **come)
            esito, motivi = giudica(guarda(dove))
        finally:
            shutil.rmtree(dove, ignore_errors=True)
        bene = esito == atteso
        if not bene:
            guai += 1
        print("  %s %-62s  esito=%s (atteso %s)"
              % ("OK " if bene else "NO ", nome, esito, atteso))
        if not bene:
            for m in motivi:
                print("        %s" % m)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LA SECONDA META' — e il GUASTO INNESTATO si certifica anche lui.
    #
    # ⛔ Prima del 27 ago 2026 `--guasto-innestato` girava una volta sola, sul
    #    deposito vero, e non era certificato in nessun modo: la
    #    certificazione copriva `giudica` e basta.  ⇒ Il fatto che
    #    l'iniezione non guardasse la scena PRIMA di guastarla non poteva
    #    saltar fuori qui.
    # ⚠ Adesso `innesta_e_giudica` prende una cartella qualunque, ⇒ si prova
    #   con le scene sintetiche come tutto il resto.
    # ═══════════════════════════════════════════════════════════════════════
    casi_guasto = [
        ("⭐ scena VERDE ⇒ il byte morde ⇒ 0 (il guasto e' stato visto)",
         dict(contenuti=sano), 0),

        # ⛔⛔ IL CASO CHE AVREBBE PRESO IL DIFETTO: la scena e' gia' rossa —
        #     cioe' i due `rcp.c` divergono, che e' **il difetto per cui C10
        #     esiste**.  Prima della cura qui usciva **0**, ⇒ il gancio
        #     scriveva `ha_visto_il_guasto: true` su un rosso del PRODOTTO.
        ("⛔⛔ scena GIA' rossa (le copie divergono) ⇒ 3, ⛔ NON 0",
         dict(contenuti=sano, gemello=un_byte), 3),

        ("⛔⛔ gia' rossa per un gemello non dichiarato ⇒ 3, ⛔ NON 0",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale), 3),

        ("⛔ una copia gemella manca (esito 3 gia' prima) ⇒ 3",
         dict(contenuti=sano, gemello=senza_uno), 3),

        ("⛔ `GEMELLATI` illeggibile ⇒ 3: non c'e' niente da innestare",
         dict(contenuti=sano, elenco_makefile=None), 3),
    ]
    print()
    print("  ⛔ e il guasto innestato si giudica PRIMA di essere innestato (§1.52):")
    for nome, come, atteso in casi_guasto:
        dove = tempfile.mkdtemp(prefix="c10-cert-guasto-")
        try:
            scena(dove, **come)
            esito, righe = innesta_e_giudica(dove)
        finally:
            shutil.rmtree(dove, ignore_errors=True)
        bene = esito == atteso
        if not bene:
            guai += 1
        print("  %s %-62s  esito=%s (atteso %s)"
              % ("OK " if bene else "NO ", nome, esito, atteso))
        if not bene:
            for r in righe:
                print("        %s" % r)

    quanti = len(casi) + len(casi_guasto)
    print()
    print("  %d casi su %d" % (quanti - guai, quanti))
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice sa dire VERDE, sa dire ROSSO, e sa dire «non lo so» —")
    print("   ⛔ e sa dare rosso anche a un gemello che nessuno aveva dichiarato,")
    print("   che e' l'unica cosa che qui non faceva nessuno (LEZIONI.md §1.47).")
    print("⛔ E il guasto innestato non si certifica su una scena gia' rossa.")
    return 0


# ---------------------------------------------------------------------------
def radice_del_deposito(qui):
    """⚠ Si chiede a git, e se git non c'e' si sale di due cartelle — questo
       file sta in `banchi/11-scatole/`.  ⛔ Non e' un ripiego silenzioso: il
       percorso scelto si STAMPA, e se le cartelle non ci sono l'esito e' 3."""
    try:
        p = subprocess.run(["git", "-C", qui, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=30)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    # ⛔ `subprocess.TimeoutExpired` NON discende da `OSError`: senza nominarla,
    #    un `git` che si pianta faceva una traccia ⇒ Python usciva **1** ⇒ il
    #    gancio leggeva ROSSO su un guasto del banco (`LEZIONI.md` §1.51).
    except (OSError, subprocess.SubprocessError):
        pass
    return os.path.abspath(os.path.join(qui, "..", ".."))


# ---------------------------------------------------------------------------
# ⭐⭐ IL GUASTO INNESTATO, e gira nel GANCIO — non solo nella certificazione
#
# ⛔ La certificazione dimostra che il giudice sa dire rosso; ⭐ questo dimostra
#    che **la rete in esercizio** sa ancora dirlo, ed e' un'altra domanda (C13).
#
# ⚠ La meta' del gancio che vive sul portatile fa girare C10, C12 e C13 — e
#   ⛔ nessuna delle tre innesta un guasto.  ⇒ Senza questa modalita', C13 su
#   quella meta' NON POTREBBE MAI diventare verde: direbbe per sempre «nessun
#   guasto e' mai stato iniettato», che dall esterno somiglia a una rete rotta.
#
# ⭐ E si innesta sui file VERI, copiati in una cartella temporanea: e' il caso
#   che conta (i sintetici li fa gia' `--certifica`), e ⛔ i file del deposito
#   non si toccano nemmeno per un istante.
#
# ⛔ La convenzione del gancio si legge AL CONTRARIO: qui `0` vuol dire «il
#    guasto E' STATO VISTO».  ⇒ `esegui_maglia … true …` scrive nel registro
#    `ha_visto_il_guasto`, e C13 legge quello.
#
# ⛔⛔ E SI GIUDICA LA SCENA **PRIMA** DI GUASTARLA — §1.52, cura del 27 ago
#     2026.  ⚠ Fino a quel giorno qui non c'era nessun `giudica` prima
#     dell'iniezione: se `src/rcp.c` e `banchi/rcp/rcp.c` divergessero gia' —
#     ⛔ cioe' **esattamente il difetto per cui C10 esiste** — la copia
#     temporanea nascerebbe gia' rossa, il byte cambiato non aggiungerebbe
#     niente, e C10 uscirebbe **0** ⇒ il gancio scriverebbe
#     `ha_visto_il_guasto: true`.
# ⇒ ⭐ Il giorno in cui morde e' **precisamente il giorno del rosso**: il giro
#   in cui C10 finalmente prende il difetto e' anche il giro in cui il suo
#   guasto innestato smetterebbe di significare qualcosa.  ⛔ La rete si
#   certificherebbe su un difetto del prodotto.
# ---------------------------------------------------------------------------
def innesta_e_giudica(dove):
    """⭐ Il guasto innestato, e ⛔ **gira su una scena qualunque**.

    ⚠ Sta scritto cosi' apposta: prendendo la cartella come argomento, questo
      pezzo si puo' certificare su scene sintetiche invece di essere provato
      una volta sola sul deposito vero.  ⇒ E' come `--certifica` prova il
      giudice: chiamandolo.

    Torna `(esito, righe)`.  ⛔ Si legge AL CONTRARIO: `0` = il guasto e' stato
    visto.  `3` = non ho potuto innestare niente.
    """
    righe = []
    f = guarda(dove)
    if f["elenco"] is None or not f["elenco"]:
        return 3, ["⛔ non ho letto `GEMELLATI`: non posso nemmeno innestare "
                   "il guasto ⇒ non ho potuto guardare"]

    # ⛔⛔ PRIMA IL GIUDIZIO, POI IL GUASTO (§1.52).
    prima, motivi_prima = giudica(f)
    if prima != 0:
        righe.append("⛔⛔ la scena era GIA' rossa PRIMA del guasto (esito %d):"
                     % prima)
        righe += ["   " + m for m in motivi_prima]
        righe.append("⇒ un guasto innestato su una scena gia' rossa non "
                     "dimostra niente: il rosso ci sarebbe stato lo stesso.")
        righe.append("⛔ E questo NON e' «il guasto non e' stato visto»: e'")
        righe.append("  «non ho potuto innestare niente» ⇒ esito 3 (§1.52).")
        return 3, righe
    righe.append("⭐ la scena era VERDE prima del guasto: l'iniezione ha di "
                 "che mordere")

    # ⛔ UN BYTE, non una riga: se il giudice prendesse solo le differenze
    #    grosse, una costante spostata gli sfuggirebbe.
    bersaglio = os.path.join(dove, GEMELLA, f["elenco"][0])
    if not os.path.isfile(bersaglio):
        righe.append("⛔ la copia gemella di «%s» non c'e': non ho un bersaglio "
                     "da guastare ⇒ non ho potuto guardare" % f["elenco"][0])
        return 3, righe
    dati = bytearray(leggi(bersaglio) or b"")
    if not dati:
        righe.append("⛔ la copia gemella e' vuota: non ho un bersaglio")
        return 3, righe
    meta = len(dati) // 2
    dati[meta] = (dati[meta] + 1) % 256
    with open(bersaglio, "wb") as h:
        h.write(bytes(dati))
    righe.append("guasto: un byte cambiato in %s/%s (posizione %d di %d)"
                 % (GEMELLA, f["elenco"][0], meta, len(dati)))

    dopo, motivi = giudica(guarda(dove))
    righe += ["   " + m for m in motivi]
    if dopo == 1:
        righe.append("⭐ IL GUASTO E' STATO VISTO — C10 sa ancora dare rosso,")
        righe.append("  ⭐ e il rosso viene DAL GUASTO: prima era verde (§1.52).")
        return 0, righe
    righe.append("⛔⛔ IL GUASTO **NON** E' STATO VISTO (la maglia ha detto %d)."
                 % dopo)
    righe.append("⇒ C10 non e' piu' capace di dare rosso, e una maglia cosi'")
    righe.append("  ha lo stesso aspetto di una che non trova niente.")
    return 1, righe


def guasto_innestato(radice):
    import shutil
    import tempfile

    print("== C10 — IL GUASTO INNESTATO (§3.6) ==")
    print("   ⛔ si legge AL CONTRARIO: 0 = il rosso e' stato VISTO\n")

    vero = guarda(radice)
    if vero["elenco"] is None or not vero["elenco"]:
        print("⛔ non ho letto `GEMELLATI` dal deposito vero: non posso")
        print("   nemmeno innestare il guasto ⇒ non ho potuto guardare")
        return 3

    dove = tempfile.mkdtemp(prefix="c10-guasto-")
    try:
        os.makedirs(os.path.join(dove, CASA))
        os.makedirs(os.path.join(dove, GEMELLA))
        shutil.copy2(os.path.join(radice, MAKEFILE), os.path.join(dove, MAKEFILE))
        # ⛔ Si copia TUTTA la cartella gemella, non solo i dichiarati: la
        #    terza domanda di C10 e' «l'elenco copre la cartella?», e copiando
        #    solo i dichiarati la scena sarebbe verde per costruzione ⇒ il
        #    giudizio «prima» non avrebbe niente da giudicare.
        for nome in sorted(os.listdir(os.path.join(radice, GEMELLA))):
            for cartella in (CASA, GEMELLA):
                a = os.path.join(radice, cartella, nome)
                if os.path.isfile(a):
                    shutil.copy2(a, os.path.join(dove, cartella, nome))
        for nome in vero["elenco"]:
            for cartella in (CASA, GEMELLA):
                a = os.path.join(radice, cartella, nome)
                if os.path.isfile(a) and not os.path.isfile(
                        os.path.join(dove, cartella, nome)):
                    shutil.copy2(a, os.path.join(dove, cartella, nome))

        esito, righe = innesta_e_giudica(dove)
        for r in righe:
            print("   %s" % r)
        return esito
    finally:
        shutil.rmtree(dove, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(
        description="C10 — le due copie gemelle del protocollo combaciano")
    p.add_argument("--radice", default=None,
                   help="la radice del deposito (predefinito: quella di questo file)")
    p.add_argument("--certifica", action="store_true",
                   help="dimostra che il giudice sa dare verde, rosso e «non lo so»")
    p.add_argument("--guasto-innestato", action="store_true",
                   help="⛔ innesta un guasto sui file VERI copiati e pretende "
                        "il rosso — l'esito si legge al contrario (0 = visto)")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    qui = os.path.dirname(os.path.abspath(__file__))
    radice = a.radice or radice_del_deposito(qui)

    if a.guasto_innestato:
        return guasto_innestato(radice)

    print("== C10 — le due copie gemelle del protocollo combaciano? ==")
    print("   deposito : %s" % radice)
    print("   le due   : %s/  e  %s/" % (CASA, GEMELLA))
    print("   l'elenco : `GEMELLATI` LETTO da %s — ⛔ non ricopiato qui" % MAKEFILE)
    print("   il metro : ⛔ **il file intero, byte per byte** — e non e' un")
    print("              eccesso: le due copie sono lo stesso modulo montato su")
    print("              due ospiti, non due varianti (src/Makefile, R12.3)\n")

    f = guarda(radice)

    if f["elenco"] is None:
        print("   ⛔ `GEMELLATI` non letto.")
    else:
        print("   coppie dichiarate: %d  ⇒  %s"
              % (len(f["elenco"]), " ".join(f["elenco"]) or "(nessuna)"))
    print()

    # ⭐ La tabella si stampa SEMPRE, verde o rossa: e' quel che va guardato, e
    #   chi legge deve poterlo vedere senza rilanciare niente.
    if f["coppie"]:
        largh = max(len(c["nome"]) for c in f["coppie"])
        for c in f["coppie"]:
            segno = {"identici": "  ", "divergono": "⛔"}.get(c["stato"], "⚠ ")
            print(" %s %-*s  %-18s  md5 %s"
                  % (segno, largh, c["nome"], c["stato"],
                     (c["md5"] or "?")[:12]))
        print()

    # ⛔⛔ E QUI LA PARTE CHE NON FACEVA NESSUNO: l'elenco copre la cartella?
    if f["gemella_c_e"]:
        print("   ⭐ e l'elenco copre tutta la cartella gemella?")
        if f["non_dichiarati"]:
            for n in f["non_dichiarati"]:
                print("     ⛔ %s — sta in tutt'e due, e NON e' dichiarato" % n)
        else:
            print("     OK  nessun sorgente di %s/ e' rimasto fuori da `GEMELLATI`"
                  % GEMELLA)
        for n in f["solo_nel_banco"]:
            print("     ⚠  %s — sta SOLO nel banco: non ha un gemello, non lo "
                  "giudico" % n)
        for n in f["estranei"]:
            print("     ⚠  %s — non e' un sorgente (%s): non lo giudico"
                  % (n, "/".join(SUFFISSI_SORGENTE)))
        print()

    esito, motivi = giudica(f)
    for m in motivi:
        print("   %s" % m)
    print()

    if esito == 0:
        print("⭐ VERDE — e vale la pena dire che cosa NON vuol dire: che `rcp.c`")
        print("   sia giusto.  ⛔ Due copie identiche dello stesso difetto passano")
        print("   di qui senza fare rumore.")
    elif esito == 1:
        print("⛔⛔ ROSSO — §5.2: si ripara PRIMA di andare avanti.")
        print("   ⇒ Finche' e' cosi', il protocollo del prodotto e quello dei")
        print("     banchi sono DUE, e ogni banco che dice verde sull'innesto")
        print("     non sta dicendo niente sul prodotto.")
    elif esito == 3:
        print("⛔ NON HO POTUTO GUARDARE (esito 3) — ⛔ e non e' un rosso (§4.5).")
        print("   ⚠ E un 3 ripetuto non e' un esito: e' un guasto del banco.")
    return esito


if __name__ == "__main__":
    sys.exit(main())
