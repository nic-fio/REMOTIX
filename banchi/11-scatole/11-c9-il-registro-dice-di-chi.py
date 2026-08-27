#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c9 — ⭐⭐ «IL REGISTRO DICE DI CHI PARLA» — la maglia del multi-inquilino
===========================================================================

    python3 11-c9-il-registro-dice-di-chi.py --porta 8514
    python3 11-c9-il-registro-dice-di-chi.py --certifica
    python3 11-c9-il-registro-dice-di-chi.py --togli-nome tutto   (il guasto)

⛔ Perche' esiste, in una riga: **il prodotto e' multi-inquilino**.  Con due
   sessioni vive insieme, una riga senza nome e' una riga che **non si puo'
   attribuire** — e la diagnosi diventa indovinare.

`[M]` 25 agosto 2026, `fasi/10-…md` §6.7, ed e' la misura che ha fatto nascere
la cura R10-A4: con **quattro** sessioni vere, solo il **4,2 %** delle righe di
diagnosi diceva di chi parlava, e chi provava a indovinare il nome **sbagliava
96 volte su 100** — cioe' mandava a guardare il desktop di un altro.

---------------------------------------------------------------------------
⛔⛔ LA REGOLA PIU' DIFFICILE E' **QUALE RIGA DEVE PORTARE IL NOME**
---------------------------------------------------------------------------

E le due risposte comode sono tutt'e due sbagliate, ognuna a modo suo:

  «TUTTE»            ⛔ falso, e da' **rosso per sempre**: le righe d'avvio
                     precedono qualunque inquilino, e nominarne uno sarebbe
                     inventarlo.  `LEZIONI.md` §1.49 — un rosso che non si puo'
                     far diventare verde e' peggio di nessuna maglia.
  «QUELLE CHE CE     ⛔ vuoto: non puo' **mai** dare rosso.  `LEZIONI.md` §1.44
   L'HANNO»          — il predicato che non poteva fallire e aveva l'aspetto di
                     uno che passa.

⇒ ⭐ **L'insieme obbligato va DICHIARATO, e difeso.**  Questo e' il nostro.

  UNA RIGA E' OBBLIGATA SE VALGONO TUTT'E DUE:

    1. ⭐ **sta nella FINESTRA** — cioe' nella fetta di registro che va dal
       segno posato **prima** di aprire i due inquilini fino alla fine.
       ⛔ La finestra NON si indovina dal contenuto: e' la fetta, e basta.
       ⇒ L'avvio del server resta fuori **per costruzione**, non per una regola
         che deve riconoscerlo — ed e' la ragione per cui questa maglia non
         puo' dare il rosso perpetuo di §1.49.
       ⚠ E c'e' un prezzo, dichiarato: cosi' C9 giudica **solo quel che e'
         successo mentre guardava**.  Un registro vecchio si giudica con
         `--da-file`, e allora la finestra e' tutto il file (lo si dice).

    2. ⭐ **la sua AREA e' un'area di sessione** — un'area che esiste soltanto
       perche' esiste una sessione:

           figlio · sessione · video · cattura · cursore · input ·
           audio · suono · tastiera · appunti

  E QUEL CHE E' **ESENTE**, con la ragione di ciascuno — ⛔ nessuna esenzione
  per comodita':

    · ⛔ **fuori dalla finestra** — non c'e' nessun inquilino da nominare.
    · ⛔ **le aree del SERVER**: `avvio` `cert` `budget`.  Parlano della
      macchina, non di un inquilino: il budget in vigore e' di **tutti**, e il
      certificato pure.  ⚠ E `budget` resta esente **anche quando nomina uno**
      («verdetto per «c9u1»»): l'area dice del server, la riga e' un verdetto.
    · ⚠ **le aree del SALUTO**: `quic` `wt` `rcp` `pagina`.  ⛔ La stessa area
      serve **due momenti**: la stretta di mano — quando l'utente non si e'
      ancora nominato, e `wt_chi()` torna `""` **apposta** (`webtransport.c`
      §897: chi non sa tace) — e il dialogo dopo, che il nome ce l'ha.
      ⇒ Dalla riga sola i due momenti **non si distinguono**, e un obbligo qui
        sarebbe un rosso su una riga che ha ragione a tacere.
      ⭐ Percio' non sono obbligate, ⛔ **ma si contano e si stampano a parte**:
        e' li' che il difetto tornerebbe a nascondersi, e un'esenzione che non
        si vede e' un'esenzione di cui nessuno si accorge.
    · ⭐ **le righe di RIEPILOGO SU TUTTI**, e sono UNA famiglia sola, nominata
      per esteso qui sotto (`SEGNI_DI_RIEPILOGO`): la riga del guardiano porta
      `inquilini=N`, cioe' e' un conto **su tutti** — nominarne uno sarebbe
      **falso**.  ⚠ Senza questa esenzione C9 darebbe **un rosso al minuto**,
      per sempre, su una riga che ha ragione.

---------------------------------------------------------------------------
⭐ E «AVERE IL NOME» VUOL DIRE DUE COSE, E SI CONTANO SEPARATE
---------------------------------------------------------------------------

  1. ⭐ **nella parentesi d'identita'** — `HH:MM:SS.mmm area   [nome] corpo`.
     E' la forma canonica: la compone `registro.c riga()`, in un posto solo, e
     un attrezzo la legge per colonna.
  2. ⚠ **soltanto nel corpo** — la riga dice «c9u1» in mezzo alla prosa, fra
     virgolette basse, e la parentesi non c'e'.

⛔ La seconda **conta come attribuibile** — un uomo che legge il registro sa di
   chi si parla, e chiamarla rossa sarebbe un falso allarme su 1 riga su 4
   (`[M]` qui sotto).  ⚠ **Ma e' fragile**, e va detto: la prosa cambia quando
   qualcuno riscrive un messaggio, la parentesi no.  ⇒ Si stampa il suo conto,
   sempre, ⭐ **e questa maglia lo consegna come RILIEVO, non come verdetto**.

`[M]` 26 agosto 2026, scatola `rete11-lxqt`, due inquilini vivi insieme
(`c9u1`, `c9u2`) per 45 s, 5 752 righe di fetta, server con `--parlantina`:

       righe obbligate                    5 490
       col nome NELLA PARENTESI           4 084   (74,4 %)
       col nome SOLO NEL CORPO            1 402   (25,5 %)  ⚠ tutte del PADRE
       ⛔ SENZA NOME DA NESSUNA PARTE         4   (0,1 %) ⇒ **ROSSO**
       attribuite a c9u1 / c9u2         2 799 / 2 687   ⭐ la forma forte regge

⛔⛔ E LE QUATTRO SONO UN DIFETTO VERO DEL PRODOTTO, non del banco.  Ecco le
    otto righe vere, prese dalla fetta del giro ufficiale — ⭐ e si legge da
    sole:

       20:19:47.887 rcp      [c9u1] ritmo di [127.0.0.1]:40258: arretrato…
       20:19:47.895 tastiera modificatore 7: si preferisce il tasto 100 a 84…
       20:19:47.895 tastiera disposizione in vigore: it [Italian]
       20:19:47.895 rcp      [c9u1] posto PRESO da c9u1 via […]:40258 (1)
       …
       20:19:49.914 figlio   [c9u2] senza palco e QUALCUNO GUARDA…
       20:19:49.918 tastiera modificatore 7: si preferisce il tasto 100 a 84…
       20:19:49.918 tastiera disposizione in vigore: it [Italian]
       20:19:49.918 rcp      [c9u2] posto PRESO da c9u2 via […]:46239 (2)

    `[R]` `tastiera.c:486` (`registro_dice`) e `:342` (`registro_dettaglio`)
    scrivono **nel PADRE**, che non ha identita' di processo — e nel padre
    l'identita' e' della RIGA, non del processo (`registro.h`).  Nessuna delle
    due passa da `registro_dice_di()`.
    ⇒ Due righe per inquilino, **identiche parola per parola**, e con due
      inquilini vivi ⛔ **non c'e' modo di dire quale sia di chi**: la seconda
      coppia si potrebbe attribuire a `c9u1` con la stessa plausibilita'.
    ⭐ Con UN inquilino solo si attribuivano per esclusione — ⛔ **ed e'
      esattamente la ragione per cui questa maglia ne apre DUE.**
    ⇒ La cura sta in due righe: `registro_dice_di(REG_TASTIERA, chi, …)` e
      `registro_dettaglio_di(…)`, col nome che il padre gia' ha in mano
      (e' lo stesso che scrive nella riga `rcp` due millisecondi dopo).

---------------------------------------------------------------------------
⚠ E LA PARLANTINA — che cosa cambia, e che cosa no
---------------------------------------------------------------------------

`11-accendi.sh server` accende il prodotto con `--parlantina`, e quell'opzione
accende `registro_dettaglio*()`.  ⛔ **La domanda va posta, e la risposta e'
misurata invece che dedotta.**

`[M]` 26 agosto 2026, stessa scatola, stessi due inquilini, giro di controllo
col server riacceso **senza** `--parlantina`:

                              con parlantina     senza
       righe della fetta            5 752        4 158
       righe obbligate              5 490        3 990
       col nome nella parentesi     4 084        2 586   (74,4 % → 64,8 %)
       col nome solo nel corpo      1 402        1 402   ⭐ IDENTICHE
       ⛔ SENZA NOME                    4            2
       esito                            1            1   ⭐ rosso tutt'e due

⭐ **IL VERDETTO NON CAMBIA: rosso in tutt'e due i modi.**  ⚠ Ma il conto si',
   e le due cose vanno dette insieme:

  · `tastiera.c:486` («disposizione in vigore») e' `registro_dice()` ⇒ esce
    **sempre**, ed e' il rosso che regge senza parlantina;
  · `tastiera.c:342` («modificatore N: si preferisce…») e' `registro_dettaglio()`
    ⇒ ⛔ **senza parlantina non esiste**, e con lei sono altre due righe rosse;
  · ⭐ le 1 402 righe «solo nel corpo» sono **le stesse identiche**: il difetto
    del padre non e' un fatto della parlantina, e' un fatto del padre.

⇒ ⭐ **Con la parlantina si guardano piu' righe** — e sono proprio quelle che
   `[M]` §6.7 misurava allo 0,0 % prima della cura R10-A4.  ⛔ Chi fa girare C9
   su un server muto non sta misurando una cosa diversa: **ne sta misurando di
   meno**, e la percentuale col nome nella parentesi scende di 10 punti perche'
   spariscono le righe di dettaglio, che il nome ce l'hanno quasi tutte.
   ⚠ Il gancio la fa girare col server di `11-accendi.sh`, cioe' **con** la
     parlantina: e' la condizione in cui i numeri qui sopra sono stati presi.

---------------------------------------------------------------------------
⛔ IL GUASTO INNESTATO — e qui si puo' fare **sui dati veri**
---------------------------------------------------------------------------

  · `--certifica` : ⭐ obbligatorio, registri **fabbricati**: uno col nome
    (⇒ verde), uno senza (⇒ rosso), uno vuoto (⇒ 3, «non lo so»), piu' i casi
    che tengono onesto l'insieme obbligato (§1.44, §1.49).
  · `--togli-nome parentesi|corpo|tutto` : ⭐⭐ **il guasto sui dati VERI, senza
    ricompilare il prodotto**.  Si apre il giro normale, e la fetta appena
    letta viene sfregiata in memoria prima di essere giudicata:
        `parentesi` toglie `[nome] ` subito dopo l'area — la forma canonica;
        `corpo`     sostituisce il nome dentro la prosa;
        `tutto`     tutt'e due ⇒ ⛔ deve diventare ROSSO su quasi tutto.
    ⚠ Il registro sul disco **non si tocca**: si sfregia la copia.
    `[M]` 26 agosto 2026, sulla fetta vera del giro ufficiale (5 490 righe
    obbligate), righe che restano SENZA NOME:
        senza guasto   →      4   (0,1 %)   ⇒ rosso, ed e' il difetto vero
        `corpo`        →  1 406  (25,6 %)   ⚠ la parentesi regge da sola
        `parentesi`    →  3 614  (65,8 %)   ⚠ 1 876 lo ripetono nella prosa
        `tutto`        →  5 490 (100,0 %)   ⛔ tutto rosso
    ⇒ ⭐ Il giudice **sa** dare rosso sui dati veri, e i quattro numeri sono
      **diversi fra loro**: cioe' sta guardando davvero **due** posti, non uno
      che finge di essere due.

⭐ E la meta' che si dimentica sempre (`LEZIONI.md` §1.49): si prova anche il
   verso opposto — **tolto il guasto, torna verde**.  La certificazione lo fa.

---------------------------------------------------------------------------
⛔ QUEL CHE C9 **NON** GUARDA — e va scritto, o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · ⛔ **non guarda se il nome e' QUELLO GIUSTO**: guarda che ci sia.  Una riga
    di `c9u1` marcata `[c9u2]` per C9 e' verde.  ⚠ Prenderla vorrebbe dire
    sapere che cosa stava facendo ogni sessione, cioe' un'altra maglia.
  · ⛔ **non guarda le aree del saluto** (`quic` `wt` `rcp` `pagina`): le conta
    e le stampa, non le giudica — la ragione e' scritta sopra.
  · ⛔ **non guarda il contenuto della riga**: che sia utile, vera o completa
    non e' affare suo.
  · ⛔ **non guarda le righe che il registro NON ha scritto**: se una famiglia
    intera di messaggi sparisse, C9 direbbe verde su quel che resta.
  · ⚠ **non guarda oltre la finestra**: quel che e' successo prima del segno
    non e' giudicato (e con `--da-file` la finestra e' tutto il file, il che e'
    un'altra cosa e viene detto).

---------------------------------------------------------------------------
⚠ IL TEMPO, misurato invece che stimato

`[M]` 26 agosto 2026: **50 secondi** il giro vero (`--resta 45`), meno di un
secondo la certificazione.  ⛔ Nella famiglia veloce **non ci sta**: il tetto e'
180 s ed e' gia' pieno a 153 (§5.1).  ⇒ C9 sta in `tutto` e in `desktop-nuovo`,
e il gancio lo dichiara.  ⚠ Chi la vuole piu' corta abbassi `--resta`, ⛔ ma
sappia che cosa compra: meno righe guardate, non un'altra prova.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)

  0  ⭐ ogni riga obbligata dice di chi parla
  1  ⛔ almeno una riga obbligata non si puo' attribuire  ⇒ rosso
  3  ⛔ non ho potuto guardare — il registro non c'e', la fetta e' vuota,
     ⛔ **l'insieme obbligato e' VUOTO** (§1.44: un insieme vuoto non e' un
     verde), oppure i due inquilini non sono entrati tutt'e due (⭐ la forma
     forte e' DUE, e con uno solo questa maglia non ha provato quel che dice
     di provare) — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «IL CLIENTE E' STATO AMMESSO?» — ⛔ IL PREDICATO SI IMPORTA, NON SI
#     RISCRIVE.  La casa e' `11-c1-nasce-e-si-vede.py`, e ce n'e' UNA (§1.47).
#
# ⛔ Fino al 27 agosto 2026 qui c'era `"AMMESSO" in uscita`, ⭐ e non poteva
#    dire di no: `[R]` `01-b3-cliente.py` stampa quella parola anche nei **due
#    messaggi di rifiuto** — «CONGEDO invece di AMMESSO: motivo …» (:1315) e
#    «atteso AMMESSO, arrivato …» (:1322) — e li stampa sullo **stdout**, che
#    e' esattamente dove si guardava.  ⇒ Un predicato che non puo' fallire,
#    `LEZIONI.md` §1.44: la maglia si credeva entrata **anche quando era stata
#    respinta**, e poi giudicava il buio che ne seguiva come un difetto del
#    prodotto.
# ⚠ Era in CINQUE maglie con la stessa riga.  ⇒ Curarla cinque volte sarebbe
#   stato creare cinque posti da cui divergere di nuovo (§1.47): sta in C1, e
#   le altre quattro la importano da li'.
# ⛔ E se non si riesce a importarla si esce **3** e lo si dice, ⇒ ⛔ non si
#   ripiega in silenzio sul predicato povero — che e' il difetto stesso.
# ═══════════════════════════════════════════════════════════════════════════
_QUI_C1 = os.path.dirname(os.path.abspath(__file__))
_C1 = None


def _carica_c1():
    """⛔ E' un CARICATORE, non un giudice: trova il file, non decide niente.

    ⚠ Si cerca accanto a me (dentro la scatola tutto sta in `/opt/remotix`) e
      un piano piu' su, come fanno C2, C3 e C6 coi loro giudici importati.
    """
    for p in (os.path.join(_QUI_C1, "11-c1-nasce-e-si-vede.py"),
              os.path.join(os.path.dirname(_QUI_C1), "11-scatole",
                           "11-c1-nasce-e-si-vede.py")):
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location("c1_ammissione", p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ Si VERIFICA che ci sia quel che serve, invece di fidarsi del nome
        #    del file (`CODER.md` §3.9).
        if not callable(getattr(m, "e_stato_ammesso", None)):
            return None
        if not callable(getattr(m, "certifica_ammissione", None)):
            return None
        # ⭐ E da C1 viene anche la garanzia dei gruppi della scheda: stessa
        #    ragione, stesso posto solo (§1.47).
        for mestiere in ("garantisci_i_gruppi", "verdetto_gruppi",
                         "certifica_gruppi"):
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_dell_ammissione():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   viene il predicato «il cliente e' stato AMMESSO?» — che sta")
        print("   in un posto solo apposta (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama esce **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ e anche questo sta in un posto solo (C1).

    Torna `(esito, perche)`: `0` = l'inquilino vede e si puo' misurare,
    `3` = ⛔ NON si misura.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica.  ⭐ `[M]` senza i gruppi
       dei nodi `/dev/dri` la sessione nasce CIECA — 0 su 4, mai in 90 s, zero
       fotogrammi — e questa maglia avrebbe misurato il buio chiamandolo
       difetto del prodotto (`fasi/10-…` §7.4).
    ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid dai NODI e
       rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ L'INSIEME OBBLIGATO, DICHIARATO QUI E STAMPATO IN OGNI ESITO.
#    Un verdetto senza il suo metro e' un'opinione (C11, stessa regola).
# ---------------------------------------------------------------------------

# Le aree che esistono soltanto perche' esiste una sessione.  ⭐ Prese dai
# `#define` del prodotto: `registro.h` (REG_*) piu' i quattro `#define AREA` di
# `cattura.c`, `mutter.c` (= "cattura"), `cursore.c` e `input.c`.
AREE_DI_SESSIONE = ("figlio", "sessione", "video", "cattura", "cursore",
                    "input", "audio", "suono", "tastiera", "appunti")

# ⚠ La stessa area serve il saluto e il dialogo: non si giudicano, si contano.
AREE_DEL_SALUTO = ("quic", "wt", "rcp", "pagina")

# ⛔ Parlano della macchina, non di un inquilino.
#
# ⚠⚠ E LE TRE LISTE SONO ESAUSTIVE **PER DICHIARAZIONE**: un'area che non sta
#    in nessuna delle tre non e' esente — e' un buco, e `analizza` la conta e la
#    NOMINA (vedi li').  ⛔ Ricopiare a mano l'elenco del prodotto e' il
#    difetto strutturale di questa maglia: C10 l'elenco lo **legge** dalla
#    sorgente di verita' (`src/Makefile`), qui non c'e' un posto solo da
#    leggere — i `#define` stanno in `registro.h`, in `figlio.h`, in
#    `appunti.h` e in quattro `#define AREA` sparsi.  ⇒ La difesa non e'
#    l'elenco: e' che quel che l'elenco non conosce **si veda**.
AREE_DEL_SERVER = ("avvio", "cert", "budget")

# ⭐ L'UNICA esenzione per contenuto, e va nominata per esteso: una riga che
#    porta un conto SU TUTTI gli inquilini non puo' nominarne uno.
#    `sessione guardiano: chiamate=0 … inquilini=2 …` esce ogni 60 s.
SEGNI_DI_RIEPILOGO = ("inquilini=",)

# ⛔ La riga del prodotto, presa alla lettera da `registro.c riga()`:
#       "%s.%03ld %-7s [%s] "   oppure   "%s.%03ld %-7s "
#    ⚠ L'identita' e' riconosciuta SOLO subito dopo l'area.  Serve, e si vede:
#      «tastiera disposizione in vigore: it [Italian]» ha una parentesi in coda,
#      ⛔ e chiamarla identita' vorrebbe dire attribuire quella riga a un
#      inquilino di nome «Italian» — cioe' un verde comprato con un errore.
#    ⚠ I caratteri ammessi sono quelli che `registro.c` lascia passare quando
#      ripulisce l'identificatore: tutto il resto diventa `_`.
RIGA = re.compile(r"^(\d\d:\d\d:\d\d\.\d\d\d) (\S+) +"
                  r"(?:\[([0-9A-Za-z._@:\-]{1,48})\] )?(.*)$")


class Conto(object):
    """Il conto, e si stampa sempre — verde o rosso."""

    def __init__(self):
        self.totali = 0
        self.orfane = 0          # ⛔ righe senza marca temporale (registro.c)
        self.obbligate = 0
        self.parentesi = 0
        self.solo_corpo = 0
        self.senza = []          # (area, corpo) delle righe rosse
        self.esenti_area = 0
        self.esenti_riepilogo = 0
        self.saluto = 0
        self.saluto_con_nome = 0
        self.per_inquilino = {}  # nome -> quante righe obbligate sue
        self.altri_nomi = {}     # parentesi con un nome NON dichiarato
        # ⛔⛔ Le aree che NESSUNA delle tre liste conosce — vedi `analizza`.
        #     `area -> quante righe`, ⭐ e si stampano PER NOME.
        self.sconosciute = {}

    def righe_sconosciute(self):
        return sum(self.sconosciute.values())


def analizza(testo, nomi):
    """⭐ Il giudice, e non tocca ne' rete ne' disco: si certifica.

    `testo` e' **la finestra** (la fetta), `nomi` gli inquilini DICHIARATI.
    ⛔ Torna `None` se non c'e' niente da guardare: «non lo so» non e' zero.
    """
    if not testo:
        return None
    c = Conto()
    for r in testo.splitlines():
        if not r:
            continue
        c.totali += 1
        m = RIGA.match(r)
        if not m:
            # ⛔ Riga orfana: `registro.c` dichiara che sotto carico due
            #    scritture si potevano accavallare, e la cura del 21 agosto
            #    2026 (una sola `write` per riga) esiste per questo.  ⚠ Una
            #    riga che non si sa nemmeno di che area sia non e' giudicabile:
            #    si conta a parte, e NON si conta come verde.
            c.orfane += 1
            continue
        _quando, area, ident, corpo = m.group(1), m.group(2), m.group(3), m.group(4)
        nel_corpo = next((n for n in nomi if n and n in corpo), None)

        if area in AREE_DEL_SALUTO:
            c.saluto += 1
            if ident or nel_corpo:
                c.saluto_con_nome += 1
            continue
        if area not in AREE_DI_SESSIONE:
            # ═══════════════════════════════════════════════════════════════
            # ⛔⛔ E UN'AREA CHE NESSUNA DELLE TRE LISTE CONOSCE **NON E'**
            #     «roba del server».
            #
            # ⚠ Fino al 27 ago 2026 qui c'era solo `c.esenti_area += 1`, e
            #   `stampa_conto` presentava il conto sotto l'etichetta
            #   *«esenti — aree del server (avvio cert budget)»*.  ⇒ Tutto
            #   quel che non stava nelle tre liste finiva **muto** dentro
            #   quella riga: `[D]` cinquecento righe di un'area inventata
            #   davano verdetto **0** — ⛔ C9 verde su 500 righe che non aveva
            #   guardato, con la faccia di quando le guarda.
            #
            # ⭐ E l'ironia e' che questa maglia la frase giusta ce l'ha gia'
            #   scritta in testa, per le aree del saluto: **un'esenzione che
            #   non si vede e' un'esenzione di cui nessuno si accorge.**
            # ⇒ Adesso un'area sconosciuta e' NOMINATA e CONTATA a parte, e
            #   fa esito **3** — non un rosso (non e' colpa del prodotto), e
            #   ⛔ soprattutto non un verde.  ⚠ Non e' un rosso perpetuo
            #   (§1.49): si spegne appena qualcuno mette l'area nuova nella
            #   lista giusta, che e' esattamente il gesto che serve.
            # ═══════════════════════════════════════════════════════════════
            if area in AREE_DEL_SERVER:
                c.esenti_area += 1
            else:
                c.sconosciute[area] = c.sconosciute.get(area, 0) + 1
            continue
        if any(s in corpo for s in SEGNI_DI_RIEPILOGO):
            c.esenti_riepilogo += 1
            continue

        c.obbligate += 1
        if ident:
            c.parentesi += 1
            if ident in nomi:
                c.per_inquilino[ident] = c.per_inquilino.get(ident, 0) + 1
            else:
                # ⚠ Attribuita, ma a qualcuno che non avevo dichiarato: si dice.
                c.altri_nomi[ident] = c.altri_nomi.get(ident, 0) + 1
        elif nel_corpo:
            c.solo_corpo += 1
            c.per_inquilino[nel_corpo] = c.per_inquilino.get(nel_corpo, 0) + 1
        else:
            c.senza.append((area, corpo))
    return c


def verdetto_ammissione(quanti_ammessi, quanti_aperti):
    """⭐⭐ «Ho abbastanza inquilini per fare la prova che dico di fare?»

    ⛔ Separato dal resto apposta, come `verdetto()`: una regola che si legge in
       dieci righe e si CERTIFICA vale piu' di un `if` in mezzo al `main`.

    Torna `(esito, perche)` — `0` vuol dire «vai avanti», ⛔ non «verde».

    ⭐ La forma forte di C9 e' **DUE inquilini vivi INSIEME**.  Se non sono
       entrati tutt'e due, quella prova non e' stata fatta — ⛔ e non fatta non
       vuol dire fallita: un cliente RESPINTO non e' un prodotto rotto.
    ⚠ `quanti_aperti == 0` vuol dire `--da-file`: non li ho aperti io, non
      pretendo niente.
    """
    if quanti_aperti == 0:
        return 0, "non ho aperto io gli inquilini: giudico quel che c'e'"
    if quanti_ammessi < quanti_aperti:
        return 3, ("sono entrati %d inquilini su %d: la forma forte — DUE vivi "
                   "insieme — non e' stata provata" % (quanti_ammessi,
                                                       quanti_aperti))
    return 0, "tutti gli inquilini aperti sono entrati"


def verdetto(c, quanti_attesi):
    """Dal conto all'esito di §4.5.  ⛔ Separato dall'analisi apposta: cosi' la
       regola sul «non lo so» si legge in dieci righe e si certifica.

       `quanti_attesi` = quanti inquilini il banco ha APERTO lui.  ⭐ 0 vuol
       dire «non li ho aperti io» (`--da-file`), e allora la forma forte non
       si pretende: si giudica quel che c'e'.
    """
    if c is None:
        return 3, "la fetta di registro e' vuota: non c'e' niente da guardare"
    if c.totali and c.orfane == c.totali:
        return 3, ("tutte le %d righe sono orfane (nessuna marca temporale): "
                   "non so nemmeno di che area siano" % c.totali)
    # ⛔⛔ IL GUARDIANO DI §1.44, ed e' la riga piu' importante di questa
    #    funzione: un insieme obbligato VUOTO passerebbe qualunque controllo.
    #    «Zero righe obbligate, zero senza nome» ha esattamente l'aspetto di un
    #    verde, e non ha guardato niente.
    if c.obbligate == 0:
        return 3, ("⛔ NESSUNA riga obbligata nella finestra: il giudizio "
                   "sarebbe verde senza aver guardato niente (LEZIONI §1.44)")
    # ⛔⛔ E L'ORDINE DI QUESTI DUE CONTROLLI NON E' INDIFFERENTE — 26 agosto
    #    2026, ⭐ e l'ha trovato la certificazione di questa stessa maglia.
    #
    #    Nella prima stesura la guardia della «forma forte» veniva PRIMA.  ⇒ Col
    #    guasto innestato (`--togli-nome tutto`) nessuna riga nomina piu'
    #    nessuno, quindi «gli inquilini che parlano» sono ZERO, ⛔ e la maglia
    #    rispondeva **3** dove doveva rispondere **1**: cioe' il caso «si toglie
    #    il nome ⇒ rosso» — la ragione per cui C9 esiste — non dava rosso.
    #
    # ⭐ LA REGOLA, ed e' piu' larga del bug: **un ROSSO non ha bisogno della
    #    forma forte per essere creduto; un VERDE si.**  Se una riga obbligata
    #    non si puo' attribuire, quello e' un fatto, e vale anche se e' entrato
    #    un inquilino solo.  La forma forte serve a dire che il VERDE e' stato
    #    guadagnato con due inquilini vivi insieme, non con uno.
    # ⇒ Percio' il rosso si decide prima, e la guardia resta sotto.
    if c.senza:
        return 1, ("%d righe obbligate su %d non si possono attribuire"
                   % (len(c.senza), c.obbligate))
    # ⛔⛔ E UN VERDE NON SI DA' SU RIGHE CHE NON SI SONO SAPUTE CLASSIFICARE.
    #    ⚠ Sta DOPO il rosso, per la stessa regola di sopra: un rosso trovato
    #      e' un giudizio gia' dato e non si annacqua in «non lo so».
    if c.sconosciute:
        return 3, ("⛔ %d righe di %d aree che NON so classificare (%s): non "
                   "sono ne' giudicate ne' esenti, e un verde che le ignora "
                   "sarebbe un verde che non le ha guardate (§1.44)"
                   % (c.righe_sconosciute(), len(c.sconosciute),
                      " ".join(sorted(c.sconosciute))))
    if quanti_attesi >= 2 and len(c.per_inquilino) < 2:
        return 3, ("⭐ la forma forte e' DUE inquilini insieme, e nella "
                   "finestra ne parla %d: un VERDE cosi' non e' guadagnato"
                   % len(c.per_inquilino))
    return 0, "tutte le %d righe obbligate dicono di chi parlano" % c.obbligate


# ---------------------------------------------------------------------------
# ⛔ IL GUASTO SUI DATI VERI — senza ricompilare il prodotto, e senza toccare
#    il registro sul disco: si sfregia **la copia in memoria**.
# ---------------------------------------------------------------------------
def sfregia(testo, nomi, come):
    if come in ("parentesi", "tutto"):
        testo = re.sub(r"^(\d\d:\d\d:\d\d\.\d\d\d \S+ +)"
                       r"\[[0-9A-Za-z._@:\-]{1,48}\] ", r"\1",
                       testo, flags=re.M)
    if come in ("corpo", "tutto"):
        for n in nomi:
            if n:
                testo = testo.replace(n, "x" * len(n))
    return testo


# ---------------------------------------------------------------------------
def stampa_conto(c, nomi, esito, perche):
    print()
    print("  ⭐ IL CONTO — e si stampa sempre, verde o rosso:")
    print("     righe totali nella finestra        %6d" % c.totali)
    if c.orfane:
        print("     ⚠ di cui ORFANE (senza l'ora)      %6d   ⛔ non giudicabili"
              % c.orfane)
    print("     ⛔ righe OBBLIGATE                  %6d" % c.obbligate)
    if c.obbligate:
        print("        · col nome NELLA PARENTESI       %6d   (%4.1f %%)"
              % (c.parentesi, 100.0 * c.parentesi / c.obbligate))
        print("        · col nome SOLO NEL CORPO        %6d   (%4.1f %%)  ⚠"
              % (c.solo_corpo, 100.0 * c.solo_corpo / c.obbligate))
        print("        · ⛔ SENZA NOME                  %6d   (%4.1f %%)"
              % (len(c.senza), 100.0 * len(c.senza) / c.obbligate))
    print("     esenti — aree del server           %6d   (%s)"
          % (c.esenti_area, " ".join(AREE_DEL_SERVER)))
    # ⛔⛔ E le aree che nessuno conosce si stampano PER NOME, sempre: una
    #     esenzione che non si vede e' un'esenzione di cui nessuno si accorge.
    if c.sconosciute:
        print("     ⛔⛔ AREE CHE NON SO CLASSIFICARE  %6d   righe, in %d aree"
              % (c.righe_sconosciute(), len(c.sconosciute)))
        for area, q in sorted(c.sconosciute.items(), key=lambda x: -x[1]):
            print("        · %-12s %6d   ⛔ ne' obbligata ne' esente: nessuno"
                  " l'ha mai giudicata" % (area, q))
        print("        ⇒ va messa in una delle tre liste in testa a questa")
        print("          maglia (di sessione · del saluto · del server).")
    print("     esenti — riepiloghi su TUTTI       %6d   (portano «%s»)"
          % (c.esenti_riepilogo, "» «".join(SEGNI_DI_RIEPILOGO)))
    print("     ⚠ aree del saluto, NON giudicate   %6d   di cui col nome %d"
          % (c.saluto, c.saluto_con_nome))
    print("       (%s — la stessa area serve la stretta di mano e il dialogo)"
          % " ".join(AREE_DEL_SALUTO))
    print()
    print("  ⭐ e la FORMA FORTE — righe obbligate attribuite, per inquilino:")
    for n in nomi:
        print("       %-12s %6d" % (n, c.per_inquilino.get(n, 0)))
    for n, q in sorted(c.altri_nomi.items()):
        print("       ⚠ %-10s %6d   (nome NON dichiarato a questa maglia)" % (n, q))
    print()
    if c.solo_corpo:
        print("  ⚠ RILIEVO, non verdetto: %d righe obbligate (%.1f %%) nominano"
              % (c.solo_corpo, 100.0 * c.solo_corpo / max(1, c.obbligate)))
        print("    l'inquilino SOLO nella prosa, non nella parentesi d'identita'.")
        print("    ⛔ Sono attribuibili — un uomo che legge sa di chi si parla —")
        print("       ma la prosa cambia quando qualcuno riscrive un messaggio,")
        print("       e la parentesi no.  ⇒ Si conta, e non si giudica.")
        print()
    if c.senza:
        print("  ⛔⛔ ROSSO — %d righe obbligate NON si possono attribuire."
              % len(c.senza))
        print("     ⭐ E con DUE inquilini vivi non e' un dettaglio: sono righe")
        print("        identiche parola per parola, una per inquilino, e non c'e'")
        print("        modo di dire quale sia di chi.")
        viste = {}
        for area, corpo in c.senza:
            chiave = (area, re.sub(r"\d+", "N", corpo)[:110])
            viste[chiave] = viste.get(chiave, 0) + 1
        for (area, corpo), q in sorted(viste.items(), key=lambda x: -x[1])[:12]:
            print("       %4d × %-9s %s" % (q, area, corpo))
    print()
    print("  esito %d — %s" % (esito, perche))


# ---------------------------------------------------------------------------
def certifica():
    """⛔ Il giudice deve saper dire VERDE, ROSSO e «NON LO SO» — e va fatto
       girare, non immaginato (§3.6).

       ⚠ E si dichiara che cosa copre: **la lettura e la regola**.  ⛔ NON copre
         che il prodotto scriva le righe giuste, ne' che il nome sia quello
         vero — vedi «quel che C9 non guarda» in testa.
    """
    N = ["c9u1", "c9u2"]
    sano = (
        "20:07:42.262 rcp     [c9u1] ammesso utente=c9u1 da=[127.0.0.1]:58048\n"
        "20:07:44.294 figlio  [c9u1] entro nel montaggio del palco (tela 1920x1080)\n"
        "20:07:44.301 figlio  [c9u2] entro nel montaggio del palco (tela 1920x1080)\n"
        "20:07:45.100 sessione [c9u1] monitor 1/1: connettore «Meta-0»\n"
        "20:07:45.200 cattura [c9u2] tela CHIESTA al produttore: 1920x1080\n")

    casi = [
        # nome, testo, attesi, esito atteso, controllo in piu' (o None)
        ("⭐ tutte le righe obbligate hanno il nome", sano, 2, 0, None),
        # ⛔ IL GUASTO: si toglie la parentesi ⇒ deve diventare rosso.
        ("⛔ si toglie il nome dalla parentesi ⇒ ROSSO",
         sfregia(sano, N, "tutto"), 2, 1, None),
        # ⭐ E la meta' che si dimentica (LEZIONI §1.49): tolto il guasto,
        #    torna verde.  E' lo STESSO testo di prima, non sfregiato.
        ("⭐ e tolto il guasto torna VERDE (§1.49)", sano, 2, 0, None),
        ("⛔ registro vuoto ⇒ «non lo so», non verde", "", 2, 3, None),
        # ⛔ §1.44: solo righe d'avvio.  «Tutte» direbbe rosso; «quelle che ce
        #    l'hanno» direbbe verde.  ⭐ La risposta giusta e' «non lo so».
        ("⛔ solo righe d'AVVIO: nessuna obbligata ⇒ «non lo so» (§1.44)",
         "15:20:51.193 avvio   REMOTIX_V2 — fase 1, il filo nudo\n"
         "15:20:51.195 cert    ⭐ due certificati, due impronte\n"
         "15:20:51.196 quic    ascolto UDP su 0.0.0.0:8514\n", 2, 3, None),
        # ⛔⛔ IL CASO CHE SPIEGA PERCHE' LA FINESTRA E' LA FETTA, e va letto.
        #    `avvio` e `cert` sono esenti per AREA, quindi non danno fastidio.
        #    ⛔ Ma «figlio ⭐ tabella dei figli accesa» e' l'area `figlio` — di
        #       sessione — scritta dal PADRE all'avvio, quando nessun inquilino
        #       esiste ancora.  ⇒ Dentro una finestra e' un ROSSO, e sarebbe un
        #       rosso per sempre (§1.49).
        #    ⭐ La cura non e' un'eccezione: e' che la finestra normale comincia
        #       DOPO il segno, e quella riga non ci entra mai.  Con `--da-file`
        #       ci entra, ed e' il prezzo dichiarato di quella modalita'.
        ("⛔ con --da-file l'AVVIO entra in finestra e da' rosso: e' il prezzo",
         "15:20:51.193 avvio   REMOTIX_V2 — fase 1, il filo nudo\n"
         "15:20:51.194 figlio  ⭐ tabella dei figli accesa: fino a 10\n" + sano,
         2, 1, lambda c: len(c.senza) == 1 and c.esenti_area == 1),
        # ⛔ La riga di riepilogo del guardiano: esente, o sarebbe un rosso al
        #    minuto per sempre.
        ("⭐ il riepilogo su TUTTI e' esente (o e' un rosso al minuto)",
         sano + "20:08:45.559 sessione guardiano: chiamate=2 inquilini=2 "
                "giri_fermi=0\n", 2, 0,
         lambda c: c.esenti_riepilogo == 1),
        # ⚠ Il nome solo nella prosa: attribuibile, contato a parte.
        ("⚠ nome SOLO nel corpo ⇒ verde, ma contato a parte",
         sano + "20:07:46.000 figlio  «c9u1»: il palco per la tela 1920x1080 "
                "non c'e' ANCORA\n", 2, 0,
         lambda c: c.solo_corpo == 1),
        # ⛔ LA TRAPPOLA VERA, e viene dai dati misurati: una parentesi in CODA
        #    non e' un'identita'.  Se lo fosse, questa riga sarebbe attribuita a
        #    un inquilino di nome «Italian» ⇒ verde comprato con un errore.
        ("⛔ «it [Italian]» NON e' un'identita' ⇒ ROSSO (la riga vera)",
         sano + "20:07:42.270 tastiera disposizione in vigore: it [Italian]\n",
         2, 1, lambda c: len(c.senza) == 1),
        # ⛔ Le aree del saluto senza nome non sono rosse — e si contano.
        ("⛔ una riga di SALUTO senza nome non e' rossa (e si conta)",
         sano + "20:07:41.261 quic    connessione nuova da [127.0.0.1]:58048\n",
         2, 0, lambda c: c.saluto == 2 and c.saluto_con_nome == 1),
        # ⛔ Le aree del server: esenti anche quando nominano qualcuno.
        ("⛔ `budget verdetto per «c9u1»` e' esente: l'area e' del server",
         sano + "20:07:42.250 budget  verdetto per «c9u1»: ⭐ AMMESSO\n",
         2, 0, lambda c: c.esenti_area == 1 and not c.sconosciute),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ IL CASO CHE OGGI NON C'ERA, e avrebbe preso il difetto del
        #     27 ago 2026: un'area di sessione NUOVA — un `#define REG_…` che
        #     domani qualcuno aggiunge al prodotto — cadeva fra gli «esenti —
        #     aree del server» **senza dire niente**.  `[D]` 500 righe di
        #     un'area mai vista davano verdetto **0**.
        # ⚠ Le 2 righe obbligate del testo sano ci sono e vanno bene: il
        #   punto e' proprio che il verde sarebbe stato «guadagnato» su due
        #   righe ignorando le altre cinquecento.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ 500 righe di un'area MAI VISTA ⇒ «non lo so», ⛔ NON un verde",
         sano + "".join("20:09:%02d.%03d penna   [c9u1] traccia %d\n"
                        % (i // 60, i % 1000, i) for i in range(500)),
         2, 3, lambda c: c.sconosciute.get("penna") == 500
                         and c.esenti_area == 0),

        ("⛔ e basta UNA riga di un'area sconosciuta: non c'e' una soglia",
         sano + "20:09:01.000 penna   [c9u1] traccia 1\n", 2, 3,
         lambda c: c.sconosciute.get("penna") == 1),

        # ⭐ E la meta' che si dimentica (§1.49): messa l'area nella lista
        #   giusta, il 3 si spegne.  ⚠ Qui si simula proprio cosi': l'area
        #   sconosciuta e' `avvio`, che nella lista del server c'e' gia'.
        ("⭐ …e un'area CONOSCIUTA del server non fa scattare niente (§1.49)",
         sano + "20:09:01.000 avvio   una riga d'avvio qualunque\n", 2, 0,
         lambda c: not c.sconosciute and c.esenti_area == 1),

        # ⛔ Un rosso vero vince sul «non lo so»: l'ordine dei due controlli
        #    e' quello, e va provato invece che ricordato.
        ("⛔ un'area sconosciuta NON annacqua un rosso gia' trovato",
         sano + "20:09:01.000 penna   [c9u1] traccia 1\n"
                "20:07:42.270 tastiera disposizione in vigore: it [Italian]\n",
         2, 1, lambda c: c.sconosciute.get("penna") == 1 and len(c.senza) == 1),
        # ⭐ LA FORMA FORTE: due aperti, uno solo parla ⇒ «non lo so».
        ("⭐ due aperti e uno solo parla ⇒ «non lo so», NON verde",
         "20:07:44.294 figlio  [c9u1] entro nel montaggio del palco\n", 2, 3, None),
        # ⚠ ...ma con --da-file (nessuno aperto da me) uno solo va benissimo.
        ("⚠ con --da-file (0 aperti da me) un inquilino solo e' giudicabile",
         "20:07:44.294 figlio  [c9u1] entro nel montaggio del palco\n", 0, 0, None),
        # ⛔ Righe orfane: tutte orfane ⇒ non lo so.
        ("⛔ tutte le righe orfane ⇒ «non lo so»",
         "il palco per la tela 1920x1080 non c'e' ANCORA\nun'altra riga rotta\n",
         2, 3, None),
        # ⚠ Un nome NON dichiarato: attribuito, non «senza nome».
        ("⚠ una parentesi con un nome non dichiarato e' ATTRIBUITA",
         sano + "20:07:44.500 figlio  [provanic7] entro nel montaggio\n", 2, 0,
         lambda c: c.altri_nomi.get("provanic7") == 1 and not c.senza),
        # ⭐ Il guasto sui DATI VERI, verso «corpo»: la parentesi resta, e la
        #    riga resta attribuibile ⇒ verde.  Serve a dimostrare che le due
        #    forme sono davvero contate separate.
        ("⭐ sfregiato solo il CORPO: la parentesi regge ⇒ verde",
         sfregia(sano, N, "corpo"), 0, 0, None),
    ]

    print("== certificazione del giudice di C9 ==")
    print("   ⛔ copre LA LETTURA E LA REGOLA — non che il prodotto scriva le")
    print("      righe giuste, ne' che il nome sia quello vero (vedi in testa)\n")
    guai = 0
    for nome, testo, attesi, atteso, extra in casi:
        c = analizza(testo, N)
        e, perche = verdetto(c, attesi)
        ok = (e == atteso) and (extra is None or (c is not None and extra(c)))
        print("  %s  %-62s  esito %d (atteso %d)"
              % ("OK " if ok else "NO ", nome[:62], e, atteso))
        if not ok:
            guai += 1
            print("        ⛔ perche': %s" % perche)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ LA GUARDIA DELL'AMMISSIONE — ⛔ il caso che oggi non c'era.
    #    C9 apre DUE inquilini: se il server li respinge, il registro resta
    #    vuoto e il verdetto vecchio l'avrebbe messo in conto al PRODOTTO.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("  ── la guardia dell'ammissione: quanti sono entrati DAVVERO")
    casi_amm = [
        ("⭐ tutt'e due entrati ⇒ si va avanti", 2, 2, 0),
        ("⛔ uno solo su due ⇒ 3, la forma forte non e' stata provata", 1, 2, 3),
        ("⛔ nessuno dei due (respinti) ⇒ 3, ⛔ NON un rosso", 0, 2, 3),
        ("⚠ `--da-file`: non li ho aperti io ⇒ si giudica quel che c'e'",
         0, 0, 0),
        ("⭐ tre su tre ⇒ si va avanti (non e' inchiodato a due)", 3, 3, 0),
    ]
    for nome, amm, ape, atteso in casi_amm:
        e, perche = verdetto_ammissione(amm, ape)
        ok = e == atteso
        if not ok:
            guai += 1
        print("  %s  %-62s  esito %d (atteso %d)"
              % ("OK " if ok else "NO ", nome[:62], e, atteso))

    # ⭐⭐ E IL PREDICATO «AMMESSO» — vive in C1, e si certifica coi casi di C1:
    #    ⛔ una copia dei casi qui sarebbe un secondo posto da cui divergere.
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C9")
    guai += guai_amm

    # ⭐⭐ E I CASI DEI GRUPPI DELLA SCHEDA — ⛔ l'altro caso che non c'era:
    #    un inquilino senza i gruppi dei nodi ⇒ «non ho potuto guardare», ⛔
    #    mai rosso.  Vivono in C1 col passo che certificano.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C9")
    guai += guai_gr

    quanti = len(casi) + len(casi_amm) + quanti_amm + quanti_gr
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi su %d sbagliati"
              % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: il giudice sa dire verde, rosso e «non lo so»."
          % (quanti, quanti))
    print("⛔ E sa dire «non lo so» anche quando l'insieme obbligato e' VUOTO —")
    print("   che e' il modo in cui una maglia smette di guardare senza dirlo.")
    return 0


# ---------------------------------------------------------------------------
def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def apri_inquilini(a, nomi):
    """⭐ LA FORMA FORTE: i due si aprono INSIEME, non uno dopo l'altro.

    ⛔ E «da zero» comprende «da zero rispetto a me stesso di ieri»: l'utente si
       cancella **prima** di crearlo, o dal secondo giro in poi non e' piu'
       nuovo (`LEZIONI.md`, C1, 26 agosto 2026).
    Torna (segno, ammessi) oppure (None, …) se il terreno non regge.
    """
    for chi in nomi:
        subprocess.run(
            ["/bin/sh", "-c",
             "loginctl terminate-user %s 2>/dev/null; "
             "pkill -KILL -u %s 2>/dev/null; "
             "userdel -r %s 2>/dev/null; rm -rf /home/%s"
             % (chi, chi, chi, chi)], capture_output=True, text=True)
        # ⛔ I gruppi della scheda non stanno piu' dentro il `useradd`: li da'
        #    l'attrezzo, che li LEGGE dai nodi `/dev/dri` e poi RILEGGE.
        fatto = subprocess.run(
            ["/bin/sh", "-c",
             "useradd -m -s /bin/bash %s && "
             "printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
            capture_output=True, text=True)
        if fatto.returncode != 0:
            print("⛔ non riesco a creare l'inquilino «%s»: %s"
                  % (chi, fatto.stderr.strip()[:90]))
            return None, []
        # ⛔⛔ E SENZA I GRUPPI DELLA SCHEDA NON SI MISURA: `[M]` la sessione
        #     nasce cieca, e un registro che non nomina nessuno perche' nessuno
        #     ha mai visto niente non e' un difetto di attribuzione.
        #     ⇒ `None` ⇒ il chiamante esce **2/3**, ⛔ mai rosso.
        e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="  ")
        if e_gr != 0:
            print("  %s" % perche_gr)
            return None, []

    # ⛔ Si segna DOVE siamo nel registro PRIMA di aprire: la finestra e' la
    #    fetta, e cosi' l'avvio del server resta fuori per costruzione.
    #
    # ⛔⛔ E IL SEGNO SI PRENDE IN CARATTERI, NON IN BYTE — 26 agosto 2026, e
    #    questa riga e' costata un VERDE FALSO, il primo giro vero.
    #
    #    La prima stesura diceva `segno = os.path.getsize(...)`, cioe' **byte**,
    #    e poi tagliava `fetta = testo[segno:]`, cioe' **caratteri**.  ⛔ Il
    #    registro di questo prodotto e' pieno di ⭐ ⛔ ⚠ «» — tre byte l'uno —
    #    quindi il taglio cadeva **molto piu' avanti** del segno: `[M]` la fetta
    #    ha perso le sue prime righe, ⛔ fra cui le due righe `tastiera` che
    #    sono l'unico rosso vero di questa scatola.
    #    ⇒ La maglia ha detto **0 righe senza nome, esito 0 — verde**, mentre il
    #      registro sul disco le aveva, alle 20:17:47 e alle 20:17:49.
    #
    # ⚠ E il segnale che l'ha fatta scoprire e' stampato qui sotto: **1 riga
    #   ORFANA**.  Un taglio in mezzo a una riga ne produce esattamente una, e
    #   una fetta presa a un a-capo non ne produce nessuna.  ⇒ Il conto delle
    #   orfane non e' un ornamento: e' la spia che il taglio e' sbagliato.
    testo = leggi(a.registro)
    if testo is None:
        return None, []
    segno = len(testo)

    processi = []
    for chi in nomi:
        processi.append((chi, subprocess.Popen(
            ["python3", a.cliente, "--indirizzo", a.indirizzo,
             "--porta", str(a.porta), "--utente", chi, "--parola", a.parola,
             "--resta", str(a.resta)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
        # ⚠ Uno sfasamento piccolo e DICHIARATO: due `ATTACCA` nello stesso
        #   millisecondo non sono la prova che si vuole fare — la prova e' «due
        #   VIVI INSIEME», e ci restano insieme per tutto il `--resta`.
        time.sleep(a.sfasamento)

    ammessi = []
    for chi, q in processi:
        try:
            uscita, _ = q.communicate(timeout=max(120, a.resta * 4))
        except subprocess.TimeoutExpired:
            q.kill()
            uscita = ""
        # ⛔ NON `"AMMESSO" in uscita`: la parola c'e' anche nei due rifiuti, e
        #    ci arriva sullo stdout — vedi `e_stato_ammesso()` in testa.
        #    ⚠ Qui il difetto mordeva due volte: C9 apre **due** inquilini, e
        #    con due rifiuti la lista `ammessi` sarebbe stata piena mentre il
        #    registro restava vuoto ⇒ un rosso inventato sul prodotto.
        stato = e_stato_ammesso(uscita)
        if stato is True:
            ammessi.append(chi)
        else:
            coda = [r.strip() for r in (uscita or "").strip().splitlines()
                    if r.strip() and not r.startswith("==")]
            print("  ⛔ «%s» %s — %s"
                  % (chi, "e' stato RESPINTO" if stato is False
                     else "non ha detto NIENTE",
                     coda[-1][:80] if coda else "e non ha detto perche'"))
    return segno, ammessi


def sgombra(nomi):
    """⭐ Della PROPRIA cartella soltanto, per nome: mai un modello globale —
       nella fase 10 un `pkill -f` globale ha rischiato di uccidere il lavoro di
       un'altra prova in corso."""
    for chi in nomi:
        subprocess.run(["loginctl", "terminate-user", chi],
                       capture_output=True, text=True)
    time.sleep(1.0)
    for chi in nomi:
        subprocess.run(["pkill", "-KILL", "-u", chi],
                       capture_output=True, text=True)


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inquilini", default="c9u1,c9u2",
                   help="⭐ DUE, e insieme: e' la forma forte della maglia")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8514)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--resta", type=float, default=45.0,
                   help="quanto restano vivi INSIEME")
    p.add_argument("--sfasamento", type=float, default=2.0,
                   help="quanto passa fra l'apertura del primo e del secondo")
    p.add_argument("--da-file", default="",
                   help="⚠ giudica un registro gia' scritto invece di aprire "
                        "due inquilini: ⛔ allora la FINESTRA e' tutto il file")
    p.add_argument("--salva-fetta", default="",
                   help="⭐ scrive qui la fetta giudicata: ⛔ un verdetto che "
                        "non si puo' rileggere non si puo' contestare")
    p.add_argument("--togli-nome", default="no",
                   choices=("no", "parentesi", "corpo", "tutto"),
                   help="⛔ IL GUASTO INNESTATO SUI DATI VERI, senza "
                        "ricompilare: sfregia la COPIA in memoria della fetta")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    nomi = [n for n in a.inquilini.split(",") if n]

    print("== C9 — il registro dice DI CHI parla? ==")
    print("   ⭐ la forma forte: DUE inquilini vivi INSIEME (%s), e ogni riga"
          % ", ".join(nomi))
    print("      che riguarda una sessione deve dire QUALE delle due.")
    print()
    print("   l'insieme OBBLIGATO, dichiarato:")
    print("     aree di sessione : %s" % " ".join(AREE_DI_SESSIONE))
    print("     esenti (server)  : %s" % " ".join(AREE_DEL_SERVER))
    print("     non giudicate    : %s   ⚠ il saluto non ha ancora un nome"
          % " ".join(AREE_DEL_SALUTO))
    print("     esente per conto : le righe che portano «%s»"
          % "» «".join(SEGNI_DI_RIEPILOGO))
    print()

    quanti_attesi = 0
    if a.da_file:
        fetta = leggi(a.da_file)
        if fetta is None:
            print("⛔ non riesco a leggere %s ⇒ non ho potuto guardare" % a.da_file)
            sys.exit(3)
        print("   ⚠ --da-file: la finestra e' TUTTO il file «%s»." % a.da_file)
        print("     ⛔ Quindi ci sono dentro anche le righe d'avvio, che sono")
        print("        esenti per area — ma un file che non contenga nessuna")
        print("        riga obbligata dara' «non lo so», e non un verde.")
    else:
        if not os.path.exists(a.cliente):
            print("⛔ non trovo il cliente di prova «%s»" % a.cliente)
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
        if leggi(a.registro) is None:
            print("⛔ non riesco a leggere il registro «%s»" % a.registro)
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
        if len(nomi) < 2:
            print("⛔ servono DUE inquilini: con uno solo questa maglia non")
            print("   proverebbe quel che dice di provare  ⇒ uso sbagliato")
            sys.exit(2)

        print("   apro i due, porta %d, e restano vivi insieme %.0f s…"
              % (a.porta, a.resta))
        segno, ammessi = apri_inquilini(a, nomi)
        if segno is None:
            print("⛔ il terreno non regge: non sono riuscito a preparare gli")
            print("   inquilini  ⇒ 2")
            sgombra(nomi)
            sys.exit(2)
        print("   ammessi: %s" % (", ".join(ammessi) if ammessi else "⛔ nessuno"))
        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ LA GUARDIA CHE NON C'ERA — e senza di lei la cura di «AMMESSO»
        #     non sarebbe servita a niente in questa maglia.
        #
        # `ammessi` si stampava e basta: ⇒ con i due clienti RESPINTI C9
        # proseguiva, trovava la fetta di registro vuota o dimezzata, e usciva
        # con un verdetto sul PRODOTTO.  ⛔ La forma forte di C9 e' «DUE
        # inquilini vivi INSIEME»: se non sono entrati tutt'e due, non e' stata
        # provata — e non provata non vuol dire rotta.
        # ⇒ Esito **3**, ⛔ e non e' un rosso (§4.5).
        # ═══════════════════════════════════════════════════════════════════
        e_amm, perche_amm = verdetto_ammissione(len(ammessi), len(nomi))
        if e_amm != 0:
            print()
            print("  ⛔ %s," % perche_amm)
            print("     quindi non c'e' niente di cui giudicare l'attribuzione.")
            print("  ⇒ non ho potuto guardare, esito %d — ⛔ e un cliente"
                  % e_amm)
            print("     RESPINTO non e' un prodotto rotto (§4.5, §1.51).")
            sgombra(nomi)
            sys.exit(e_amm)
        fetta = leggi(a.registro)
        fetta = fetta[segno:] if fetta is not None else None
        sgombra(nomi)
        quanti_attesi = len(nomi)

    if a.salva_fetta and fetta is not None:
        try:
            with open(a.salva_fetta, "w") as f:
                f.write(fetta)
            print("   ⭐ fetta giudicata scritta in «%s» (%d righe): il verdetto"
                  % (a.salva_fetta, len(fetta.splitlines())))
            print("      si puo' rileggere, e quindi contestare.")
        except OSError as e:
            print("   ⚠ non sono riuscito a salvare la fetta: %s" % e)

    prima = None
    if a.togli_nome != "no":
        prima = analizza(fetta, nomi)
        fetta = sfregia(fetta or "", nomi, a.togli_nome)
        print()
        print("   ⛔⛔ GUASTO INNESTATO SUI DATI VERI: «%s»" % a.togli_nome)
        print("      il registro sul disco NON e' stato toccato: e' sfregiata")
        print("      la copia in memoria.  ⇒ Il giudizio qui sotto DEVE essere")
        print("      piu' rosso di quello vero, o questa maglia non sa mordere.")
        if prima is not None:
            print("      (senza guasto: %d obbligate, %d senza nome)"
                  % (prima.obbligate, len(prima.senza)))

    c = analizza(fetta, nomi)
    esito, perche = verdetto(c, quanti_attesi)
    if c is None:
        print()
        print("  ⛔ %s" % perche)
        print("  esito 3 — e ⛔ non e' un rosso (§4.5).")
        sys.exit(3)
    stampa_conto(c, nomi, esito, perche)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ COL GUASTO INNESTATO L'ESITO SI LEGGE AL CONTRARIO — e senza queste
    #     righe C13 diventa una bugia.
    #
    # `11-gancio.sh`, in `esegui_maglia`, scrive nel registro
    # `ha_visto_il_guasto: true` quando una maglia innestata esce **0**.  ⛔ La
    # prima stesura di questa maglia usciva col verdetto grezzo (**1**), cioe'
    # proprio nel giro del rosso avrebbe scritto `ha_visto_il_guasto: false`.
    # `[M]` 26 agosto 2026, primo giro del cablaggio: preso cosi'.
    #
    # ⭐⭐ E NON BASTA INVERTIRE, e questa e' la parte che conta: C9 oggi e'
    #    rossa **anche senza guasto** (le due righe di `src/tastiera.c`).  ⇒ Un
    #    semplice «rosso ⇒ visto» direbbe «il guasto e' stato visto» anche se
    #    l iniezione non avesse fatto NIENTE, e la certificazione della rete
    #    poggerebbe su un difetto del prodotto invece che sul guasto iniettato.
    #    ⛔ E' la forma d errore di `LEZIONI.md` §1.44: un predicato che non
    #      puo' fallire.
    # ⇒ Si pretendono DUE cose: il verdetto e' rosso, **e** le righe senza nome
    #   sono di piu' di quante ne aveva lasciate il difetto vero.
    # ═══════════════════════════════════════════════════════════════════════
    if a.togli_nome != "no":
        senza_prima = len(prima.senza) if prima is not None else 0
        senza_dopo = len(c.senza)
        print()
        print("   ⛔ IL GUASTO INNESTATO — e qui l'esito si legge AL CONTRARIO")
        print("      righe senza nome: %d senza il guasto  ⇒  %d col guasto"
              % (senza_prima, senza_dopo))
        if esito == 1 and senza_dopo > senza_prima:
            print("   ⭐ IL GUASTO E' STATO VISTO — C9 sa ancora dare rosso,")
            print("      e il rosso viene DAL GUASTO, non dal difetto che c'era gia'.")
            sys.exit(0)
        if esito == 1:
            print("   ⛔⛔ rosso, ma NON per colpa del guasto: le righe senza")
            print("      nome sono le stesse di prima ⇒ l'iniezione non ha morso.")
            sys.exit(1)
        # ⛔⛔ E SI INVERTONO SOLO 0 E 1 — `LEZIONI.md` §4.5, e C7 lo faceva gia'
        #     nel modo giusto tre file piu' in la'.  ⚠ Fino al 27 ago 2026 qui
        #     si usciva **1** qualunque cosa fosse successo: un giro innestato
        #     che non aveva potuto guardare (i due inquilini non entrano ⇒
        #     `verdetto` torna 3) diceva a schermo *«ho guardato e non regge»*,
        #     che e' falso.  ⇒ Il 2 e il 3 non sono giudizi, e si lasciano
        #     passare come sono.
        if esito == 0:
            print("   ⛔⛔ IL GUASTO **NON** E' STATO VISTO: si e' tolto il nome")
            print("      a tutte le righe e C9 dice comunque VERDE.")
            sys.exit(1)
        print("   ⚠ NON HO POTUTO GUARDARE (esito %d) — ⛔ e questo NON e' «il"
              % esito)
        print("     guasto non e' stato visto»: e' una prova che non e' girata.")
        print("     ⇒ esco %d, e il 2 e il 3 non si rovesciano (§4.5)." % esito)
        sys.exit(esito)

    sys.exit(esito)


if __name__ == "__main__":
    main()
