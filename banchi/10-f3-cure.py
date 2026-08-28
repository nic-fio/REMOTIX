#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
10-f3-cure — ⛔ IL BANCO DELLE CURE F3: le righe MUTE e il testimone che MENTE
===========================================================================

Chiude due dei difetti che la fase 10 aveva trovato e lasciato aperti
(`fasi/10-multi-tenant-e-il-budget.md` §5.5):

  · **R4** — ⛔ nessuna delle righe che `webtransport.c` scrive di suo porta il
    nome dell'inquilino: **93 chiamate mute contro una sola che nomina**, e fra
    le mute c'e' ⛔⛔ **la riga dello sfratto**, quella che dice chi e' stato
    buttato fuori e perche'.  ⇒ *La riga piu' importante della fase non si sa
    di chi parla.*
  · **R5** — ⛔ `fermo_ms=` in quella stessa riga e' il contatore **GLOBALE**
    del ciclo del padre, mentre il commento accanto promette *«da quando questa
    sessione e' nata»*.  `[M]` §5.5: **54,5 secondi** di cecita' nostra
    attribuiti a **una sessione che non era ancora nata**.
  · **R7** — due commenti che mentivano (la riga d'avvio della sorveglianza che
    *«la scrive `main.c`»* e non la scriveva nessuno; il numero degli inquilini
    promesso da `sentinella.h` e assente dalla riga del guardiano).

---------------------------------------------------------------------------
⛔⛔ IL ROSSO PRIMA E IL VERDE DOPO — ed e' l'intera ragione del banco
---------------------------------------------------------------------------

Una cura senza il rosso di partenza non e' provata: e' un'opinione ordinata
bene (`CODER.md` §3.3).  ⇒ Questo banco misura **la stessa scena su due
binari**: `--albero-prima` (l'albero senza le cure) e `--albero-dopo`.

⭐ E LA SCENA E' COSTRUITA APPOSTA perche' il difetto di R5 si veda **nudo**:

  1. il server si accende e **non si collega nessuno**;
  2. ⛔ gli si manda un `SIGSTOP` di `--stallo-prima` secondi: il ciclo del
     padre resta fermo per un tempo NOTO, e `giro_fermo_ms` sale di quel tanto.
     ⚠ In quel momento **non esiste nessuna sessione**;
  3. **poi** si collega il cliente e apre la sessione;
  4. si ammazza il cliente con `kill -9`: dopo la soglia del silenzio la linea
     morta lo sfratta e scrive la sua riga.

  ⇒ ⛔ `fermo_ms=` in quella riga parla di secondi di cecita' **avvenuti prima
    che quella sessione nascesse**.  Sull'albero PRIMA e' un numero grosso;
    sull'albero DOPO dev'essere **zero**.

⭐ E IL CONTROLLO NEGATIVO E' UNA SECONDA SCENA, `--scena vivo-durante`: lo
   stallo si manda **mentre la sessione lavora**.  Li' `fermo_ms=` dev'essere
   **maggiore di zero anche DOPO la cura** — altrimenti la cura non avrebbe
   corretto il testimone, l'avrebbe **spento**, che e' il difetto peggiore dei
   due (`REVIEWER.md` E1: uno strumento che tace sembra uno strumento che dice
   «non e' successo niente»).

⭐⭐ E IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33): lo stallo e' un valore
    **iniettato e noto**, e il banco verifica che il prodotto lo **ritrovi** —
    la riga «il ciclo del padre e' rimasto indietro di N ms» dev'essere dentro
    la finestra attesa attorno al valore iniettato.  Un metro non tarato
    produce numeri, non misure.

---------------------------------------------------------------------------
⛔ L'ISOLAMENTO
---------------------------------------------------------------------------

  porta **8430** · utente **provanic3** (uid 1202) · unita' `remotix-8430`
  alberi `/media/REMOTIX/src/10f3-src` (dopo) e `…/10f3p-src` (prima)
  lavoro `/media/REMOTIX/tmp/10f3` · lucchetto della GPU **`10-f3`**

⛔ Non si tocca nessuna porta, nessun utente, nessuna unita' che non sia questa:
   in questo giro lavorano altri due incarichi con `provanic1` e `provanic2`.
⛔ E lo sgombero combacia **solo con la propria cartella di lavoro** — la
   quinta trappola di §7.3, che e' gia' costata un giro a qualcun altro.

Uso:
    python3 banchi/10-f3-cure.py --certifica      # ⛔ senza macchina, senza GPU
    python3 banchi/10-f3-cure.py --scena nato-dopo
    python3 banchi/10-f3-cure.py --scena vivo-durante
    python3 banchi/10-f3-cure.py --tutto          # le due scene sui due alberi

Codici d'uscita (il contratto di §7.3):
    0 regge · 1 NON regge · 2 terreno o uso sbagliato · 3 «non giudico»
    4 il turno del lucchetto non e' mai arrivato
"""

import argparse
import base64
import gzip
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, PRIMA DI QUALUNQUE IMPORT CHE LO LEGGA
# ═══════════════════════════════════════════════════════════════════════════
QUI = os.path.dirname(os.path.abspath(__file__))
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "8430"))
UTENTE = os.environ.get("UTENTE", "provanic3")
UID_B = int(os.environ.get("UID_B", "1202"))
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10f3")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/10f3")
ALB_DOPO = os.environ.get("ALBERO_DOPO", "/media/REMOTIX/src/10f3-src")
ALB_PRIMA = os.environ.get("ALBERO_PRIMA", "/media/REMOTIX/src/10f3p-src")
DENTRO_DOPO = os.environ.get("DENTRO_DOPO", "/srv/src/10f3-src")
DENTRO_PRIMA = os.environ.get("DENTRO_PRIMA", "/srv/src/10f3p-src")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
IO_SONO = os.environ.get("IO_SONO", "10-f3")
LUCCHETTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
FUORI = os.environ.get("FUORI", "/tmp/10-f3")
REGISTRO = LAV + "/registro.log"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LE SOGLIE, IN UN POSTO SOLO, CIASCUNA CON LA SUA RAGIONE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Il ciclo del padre si concede 1100 ms fra due passate
#   (`webtransport.c`, `WT_GIRO_ATTESO_MS`): un buco di `S` secondi si presenta
#   nel registro come `S*1000 - 1100` **piu'** quel che restava del `poll`, che
#   dorme al piu' 1000 ms.  ⇒ La finestra attesa e' [S*1000-1100, S*1000+200].
#   ⚠ Non e' una tolleranza scelta a occhio: sono i due estremi che il codice
#     stesso dichiara, ed e' cosi' che si tara un metro (`LEZIONI.md` §1.33).
GIRO_ATTESO_MS = 1100
POLL_MS = 1000
# ⛔ Sotto questo numero di secondi di stallo la finestra attesa si stringe
#    troppo per distinguere un buco vero dal respiro normale del ciclo.
STALLO_MIN_S = 3.0
# ⚠ La soglia del silenzio della linea morta, in millisecondi: il predefinito
#   del prodotto.  Serve solo a decidere quanto aspettare lo sfratto.
SILENZIO_MS = 10000
# ⛔ Quanto si aspetta al massimo che la sessione si apra (GNOME ci mette il
#    suo) e che lo sfratto arrivi.  Scaduto il tempo si dice «non giudico»,
#    NON «non e' successo».
ATTESA_SESSIONE_S = 90.0
ATTESA_SFRATTO_S = 45.0
# ⛔ Sotto questo numero di righe la finestra non ha misurato niente: `None`,
#    non «0 %» (regola 5 del preambolo della fase).
RIGHE_MINIME = 60


# ═══════════════════════════════════════════════════════════════════════════
# LA MACCHINA — e ogni comando porta con se' la MIA cartella, mai un modello
# globale (§7.3, la quinta trappola)
# ═══════════════════════════════════════════════════════════════════════════
def rem(cmd, tetto=180):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        MACCHINA, cmd],
                       capture_output=True, text=True, timeout=tetto)
    return p.returncode, p.stdout, p.stderr


def root(cmd, tetto=180):
    """⛔ La parola di sudo sullo STDIN, mai in argv (D12)."""
    return rem("printf '%%s\\n' %s | sudo -S -p '' bash -c %s"
               % (shlex.quote(PAROLA_SUDO), shlex.quote(cmd)), tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL LETTORE DEL REGISTRO — e riconosce le DUE forme di riga
# ═══════════════════════════════════════════════════════════════════════════
#
# Il formato lo pone `registro.c`:  "%s.%03ld %-7s "  e, se la riga ha
# un'identita', "[nome] " **in testa al corpo**.
# ⛔ I lettori devono funzionare su tutt'e due le forme, o la prova della cura
#    fallirebbe per colpa del banco invece che del prodotto (rilievo R1 di §5.5,
#    che e' costato il metro dei fotogrammi a cinque banchi).
RE_RIGA = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3}) (\S+) +(.*)$")
RE_CAPO = re.compile(r"^\[([^\]]{1,48})\] ")


class Riga(object):
    __slots__ = ("ms", "area", "corpo", "chi", "nudo")

    def __init__(self, ms, area, corpo):
        self.ms, self.area, self.corpo = ms, area, corpo
        m = RE_CAPO.match(corpo)
        # ⛔ `chi` e' l'identita' che il PRODOTTO ha scritto, non una dedotta:
        #    e' esattamente la grandezza che la cura muove.
        self.chi = m.group(1) if m else None
        self.nudo = corpo[m.end():] if m else corpo


def leggi(testo):
    righe = []
    for l in testo.split("\n"):
        m = RE_RIGA.match(l)
        if not m:
            continue
        h, mi, s, ms, area, corpo = m.groups()
        righe.append(Riga(((int(h) * 60 + int(mi)) * 60 + int(s)) * 1000
                          + int(ms), area, corpo))
    return righe


def quota_marcate(righe, aree=None):
    """La frazione di righe che PORTANO un'identita' scritta dal prodotto.

    ⛔ Torna `None` se le righe non bastano: «non ho misurato» non e' «0 %».
    """
    sel = [r for r in righe if aree is None or r.area in aree]
    if len(sel) < RIGHE_MINIME:
        return None
    con = sum(1 for r in sel if r.chi)
    return {"righe": len(sel), "marcate": con, "quota": con / len(sel),
            "nomi": sorted({r.chi for r in sel if r.chi})}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I CAMPI DELLE RIGHE CHE CONTANO
# ═══════════════════════════════════════════════════════════════════════════
RE_SFRATTO = re.compile(r"^linea-morta ")
RE_BUCO = re.compile(r"il ciclo del padre e' rimasto indietro di (\d+) ms")
RE_GUARDIANO = re.compile(r"^guardiano: ")
RE_SORVEGLIATA = re.compile(r"§5\.1, la meta' SORVEGLIATA")


def campi(corpo):
    """`chiave=valore` di una riga a campi.  ⚠ Solo i numerici interi."""
    return {k: int(v) for k, v in re.findall(r"\b([a-z_]+)=(\d+)\b", corpo)}


def trova_sfratto(righe):
    for r in righe:
        if RE_SFRATTO.match(r.nudo):
            return r
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I PREDICATI — e ciascuno torna `(True|False|None, frase)`
#    `None` = «non ho potuto giudicare», e NON e' un verde.
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def p_sfratto_ha_un_nome(sfratto, chi_atteso):
    """⭐ IL PREDICATO CHE E' TUTTO IL PUNTO DI R4."""
    if sfratto is None:
        return _muto("nessuna riga di sfratto nella finestra: NON giudico se "
                     "porti un nome")
    if not sfratto.chi:
        return _no("⛔ la riga dello sfratto e' MUTA: dice che qualcuno e' "
                   "stato buttato fuori e non dice CHI — «%s…»"
                   % sfratto.nudo[:70])
    if sfratto.chi != chi_atteso:
        return _no("⛔ la riga dello sfratto dice «%s» e l'inquilino era «%s»: "
                   "un nome sbagliato manda a guardare il desktop di un altro"
                   % (sfratto.chi, chi_atteso))
    return _si("la riga dello sfratto porta [%s]" % sfratto.chi)


def p_fermo_e_di_questa_sessione(sfratto, nata_dopo_lo_stallo, stallo_ms):
    """⭐ IL PREDICATO DI R5, e ha due facce apposta.

    · sessione **nata dopo** l'unico stallo ⇒ `fermo_ms` dev'essere **0**;
    · sessione **viva durante** lo stallo ⇒ `fermo_ms` dev'essere **> 0**, o la
      cura avrebbe spento il testimone invece di correggerlo.
    """
    if sfratto is None:
        return _muto("nessuna riga di sfratto: NON giudico `fermo_ms=`")
    c = campi(sfratto.nudo)
    if "fermo_ms" not in c:
        return _muto("la riga dello sfratto non porta `fermo_ms=`: NON giudico")
    v = c["fermo_ms"]
    # ⛔ La soglia NON e' «zero», ed e' una scelta, non una comodita': montare
    #    una sessione GNOME puo' far ritardare il ciclo del padre di suo, e
    #    quel ritardo e' **davvero** di questa sessione.  ⇒ Il rosso e'
    #    «il testimone le attribuisce lo stallo INIETTATO», e la firma di quello
    #    e' un numero dentro la finestra dello stallo.  ⚠ Sotto il bordo basso
    #    di quella finestra la riga non puo' star parlando dello stallo.
    basso = stallo_ms - GIRO_ATTESO_MS - 400
    if nata_dopo_lo_stallo:
        if v < basso:
            return _si("`fermo_ms=%d` — la sessione e' nata DOPO lo stallo di "
                       "%d ms e NON se lo vede attribuire (sotto %.0f, che e' "
                       "il bordo basso della sua firma)%s"
                       % (v, stallo_ms, basso,
                          "; ed e' esattamente ZERO" if v == 0 else ""))
        return _no("⛔ `fermo_ms=%d` su una sessione NATA DOPO l'unico stallo "
                   "(%d ms iniettati): il testimone accusa chi non c'era, e "
                   "chi legge ASSOLVE la rete quando la rete c'entrava"
                   % (v, stallo_ms))
    if v > 0:
        return _si("`fermo_ms=%d` — la sessione era VIVA durante lo stallo di "
                   "%d ms, e il testimone lo dice ancora" % (v, stallo_ms))
    return _no("⛔ `fermo_ms=0` su una sessione VIVA durante uno stallo di %d "
               "ms: il testimone e' stato SPENTO, non corretto" % stallo_ms)


def p_giri_fermi_resta_globale(sfratto):
    """⚠ `giri_fermi=` resta il conto della MACCHINA, e lo si verifica: se
       fosse sceso a zero insieme a `fermo_ms`, la cura avrebbe portato via
       anche il numero che dice se il ciclo sta bene."""
    if sfratto is None:
        return _muto("nessuna riga di sfratto: NON giudico `giri_fermi=`")
    c = campi(sfratto.nudo)
    if "giri_fermi" not in c:
        return _muto("la riga dello sfratto non porta `giri_fermi=`")
    if c["giri_fermi"] >= 1:
        return _si("`giri_fermi=%d` — il conto della macchina c'e' ancora"
                   % c["giri_fermi"])
    return _no("⛔ `giri_fermi=0` dopo uno stallo iniettato: il conto globale "
               "e' morto insieme a quello per sessione")


def p_metro_tarato(righe, stallo_s, deve_esserci):
    """⛔ IL METRO SI TARA PRIMA — si inietta un valore NOTO e si verifica che
       il prodotto lo ritrovi.

    ⚠ `deve_esserci=False` e' il caso «lo stallo e' avvenuto senza nessuna
      sessione viva»: allora la riga NON deve esserci — nessuno ha saltato un
      giudizio, perche' non c'era niente da giudicare.
    """
    letti = [int(m.group(1)) for r in righe
             for m in [RE_BUCO.search(r.nudo)] if m]
    atteso = stallo_s * 1000.0
    basso, alto = atteso - GIRO_ATTESO_MS - 400, atteso + POLL_MS + 400
    if not deve_esserci:
        if letti:
            return _no("⛔ una riga «il ciclo e' rimasto indietro» c'e' (%s) "
                       "mentre nessuna sessione era viva: il banco non sta "
                       "misurando la scena che crede" % letti)
        return _si("nessuna riga di buco, ed e' giusto: durante lo stallo non "
                   "c'era nessuna sessione da far saltare")
    if not letti:
        return _muto("nessuna riga «il ciclo e' rimasto indietro»: NON posso "
                     "tarare il metro su questo giro")
    peggio = max(letti)
    if basso <= peggio <= alto:
        return _si("metro TARATO: iniettati %.0f ms, il prodotto ne legge %d "
                   "(atteso fra %.0f e %.0f)" % (atteso, peggio, basso, alto))
    return _no("⛔ metro NON tarato: iniettati %.0f ms, il prodotto ne legge "
               "%d — fuori da [%.0f, %.0f].  Un metro non tarato produce "
               "numeri, non misure" % (atteso, peggio, basso, alto))


def p_guardiano_dice_gli_inquilini(righe):
    """⭐ R7, seconda meta': `sentinella.h` prometteva i suoi due numeri
       «accanto al numero degli inquilini serviti», e nella riga non c'era."""
    g = [r for r in righe if RE_GUARDIANO.match(r.nudo)]
    if not g:
        return _muto("nessuna riga «guardiano:» nella finestra (esce una volta "
                     "al minuto): NON giudico")
    c = campi(g[-1].nudo)
    if "inquilini" not in c:
        return _no("⛔ la riga del guardiano non porta `inquilini=`: manca il "
                   "DENOMINATORE, e senza `N` la frase «una chiamata per "
                   "ripasso, non per inquilino» non si puo' rifiutare")
    return _si("la riga del guardiano porta `inquilini=%d` accanto a "
               "`chiamate=%s`" % (c["inquilini"], c.get("chiamate", "?")))


def p_avvio_dichiara_la_sorveglianza(righe):
    """⭐ R7, prima meta': `webtransport.c` diceva che questa riga «la scrive
       `main.c` all'avvio», e ⛔ non la scriveva nessuno."""
    v = [r for r in righe if RE_SORVEGLIATA.search(r.nudo)]
    if v:
        return _si("l'avvio dichiara la meta' sorvegliata di §5.1: «%s…»"
                   % v[0].nudo[:80])
    return _no("⛔ nessuna riga sulla meta' SORVEGLIATA di §5.1 all'avvio: il "
               "commento di `webtransport.c` promette una rete che non c'e'")


def p_la_cura_del_nome_ha_morso(prima, dopo):
    """⭐ IL NUMERO CHE L'INCARICO CHIEDE: quanto SALE l'attribuzione."""
    if prima is None or dopo is None:
        return _muto("una delle due misure non ha abbastanza righe: NON "
                     "confronto due frazioni di cui una non e' stata misurata")
    if dopo["quota"] > prima["quota"]:
        return _si("attribuzione delle righe `wt`: %.1f %% → %.1f %% "
                   "(%d/%d → %d/%d)"
                   % (100 * prima["quota"], 100 * dopo["quota"],
                      prima["marcate"], prima["righe"],
                      dopo["marcate"], dopo["righe"]))
    return _no("⛔ l'attribuzione NON e' salita: %.1f %% → %.1f %%"
               % (100 * prima["quota"], 100 * dopo["quota"]))


# ═══════════════════════════════════════════════════════════════════════════
# LA SCENA
# ═══════════════════════════════════════════════════════════════════════════
def terreno_regge():
    """⛔ `10-b0-terreno.sh` prima di ogni misura, e fa fallire il banco."""
    amb = dict(os.environ)
    amb.update({"CHI": IO_SONO, "PORTA": str(PORTA), "UTENTE": UTENTE,
                "ALBERO": ALB_DOPO, "LAV": LAV, "LUCCHETTO": LUCCHETTO,
                "LUCCHETTO_MIO": "1",
                # ⚠ In questo giro lavorano altri due incarichi: le loro porte
                #   si DICHIARANO, non si tollerano in silenzio.
                "PORTE_AMMESSE": os.environ.get(
                    "PORTE_AMMESSE", "8400 8410 8420 8440 8450")})
    p = subprocess.run(["bash", os.path.join(QUI, "10-b0-terreno.sh")],
                       env=amb, capture_output=True, text=True, timeout=900)
    if p.returncode != 0:
        # ⛔ Su rosso si stampano TUTTE le righe rosse, non la coda: le due che
        #    dicono perche' stanno quasi sempre in cima (§7.3).
        for l in (p.stdout + p.stderr).split("\n"):
            if "NO" in l or "⛔" in l:
                print("        " + l)
    return p.returncode


def accendi(albero):
    amb = dict(os.environ)
    amb.update({"PORTA": str(PORTA), "IND": IND, "UTENTE": UTENTE,
                "UID_B": str(UID_B), "ALBERO": albero, "LAV": LAV,
                "UNITA": UNITA, "DENTRO_ALB": DENTRO_DOPO,
                "DENTRO_LAV": DENTRO_LAV})
    p = subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"),
                        "accendi"], env=amb, capture_output=True, text=True,
                       timeout=300)
    if p.returncode != 0:
        print(p.stdout[-2000:])
        print(p.stderr[-1000:])
    return p.returncode == 0


def spegni():
    amb = dict(os.environ)
    amb.update({"PORTA": str(PORTA), "LAV": LAV, "UNITA": UNITA})
    subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "spegni"],
                   env=amb, capture_output=True, text=True, timeout=120)


def pid_del_server():
    rc, out, _ = rem("systemctl show -p MainPID --value %s.service" % UNITA)
    t = out.strip()
    return int(t) if t.isdigit() and t != "0" else None


def registro_ora():
    rc, out, _ = root("stat -c %%s %s" % REGISTRO)
    t = out.strip()
    return int(t) if t.isdigit() else None


def fetta(da):
    """Il registro da `da` in poi.  ⛔ `None` se non l'ho preso."""
    if da is None:
        return None
    rc, out, err = root("tail -c +%d %s | gzip -9 | base64 -w0"
                        % (da + 1, REGISTRO), 600)
    t = out.strip()
    if rc != 0 or not t:
        _dub("⛔ la fetta da %s non si e' presa: %s" % (da, err[-160:]))
        return None
    return gzip.decompress(base64.b64decode(t)).decode("utf-8", "replace")


def stalla(secondi):
    """⛔ Il ciclo del padre FERMO per un tempo NOTO — il valore iniettato.

    ⚠ `SIGSTOP` al solo processo principale, letto da systemd: fermare il
      gruppo porterebbe via anche l'aiutante di PAM, e allora la scena non
      sarebbe piu' quella dichiarata.
    """
    pid = pid_del_server()
    if not pid:
        return None
    root("kill -STOP %d" % pid)
    time.sleep(secondi)
    root("kill -CONT %d" % pid)
    # ⚠ Un respiro perche' il ciclo faccia la passata che MISURA il buco: senza,
    #   si leggerebbe il registro prima che la riga esista.
    time.sleep(2.0)
    return pid


def sgombra_i_miei_clienti():
    """⛔ SOLO i miei: il modello porta la MIA cartella di lavoro.

    §7.3, la quinta trappola — `[M]` un modello globale ereditato combaciava
    con **24 clienti VIVI di un altro banco** che stava misurando.
    ⚠ E la classe di caratteri (`clien[t]e`) perche' `pkill -f` acchiappa la
      riga di comando che lo esegue.
    """
    root("pkill -9 -f -- '%s/01-b3-clien[t]e.py' ; true" % DENTRO_LAV)


# ⛔⛔ IL PALCO DEL MIO UTENTE — e si sgombra SOLO col lucchetto in mano.
#
#     Il palco SOPRAVVIVE alla sessione, ed e' voluto (invariante I4).  ⚠ Ma per
#     un banco vuol dire che il giro dopo parte da una scena diversa —
#     ri-attacco invece di accensione — e due scene diverse dette con lo stesso
#     nome sono la forma di `LEZIONI.md` §1.30.
# ⛔ E in questo giro `provanic3` puo' avere un palco montato da un ALTRO server
#    (quello della cucitura, sulla 8400): si chiude solo mentre il lucchetto e'
#    mio, cioe' quando per protocollo nessun altro sta misurando, e si DICE.
# ⚠ `pkill -u`, mai un modello globale: il fondo di `enable-linger` resta in
#   piedi apposta (ammazzarlo farebbe misurare al giro dopo la sua rinascita).
PALCO_NOMI = ("remotix-figlio|gnome-shell|gnome-session|mutter|Xwayland|"
              "gsd-|gjs|at-spi|xdg-|gvfs")


def _palco_vivo():
    """Quanti processi DEL PALCO ha il mio utente.  ⛔ `None` se non ho letto.

    ⛔⛔ E SI GUARDA TUTTO IL PALCO, non solo `remotix-figlio` — difetto di
        banco pagato il 25 agosto 2026: la prima stesura contava i soli figli, e
        `[M]` ha trovato zero figli con un **`gnome-shell` ancora vivo**.  ⇒ Non
        sgomberava, e il terreno dava rosso su T7.1 dopo aver «sgomberato».
        ⚠ Un figlio morto non porta con se' il suo compositore: il palco
          SOPRAVVIVE, ed e' voluto (invariante I4).
    """
    rc, out, _ = rem("ps -u %s -o args= 2>/dev/null | grep -cE '%s' || true"
                     % (UTENTE, PALCO_NOMI))
    t = out.strip().split("\n")[0]
    return int(t) if t.isdigit() else None


def sgombra_il_mio_palco():
    prima = _palco_vivo()
    if prima is None:
        _dub("⛔ non ho potuto leggere i processi di «%s»: NON dichiaro il "
             "palco chiuso" % UTENTE)
        return False
    if prima > 0:
        _inf("⚠ «%s» ha gia' un palco montato (%d processi): lo chiudo "
             "(lucchetto in mano) perche' il giro parta da un'accensione, non "
             "da un ri-attacco" % (UTENTE, prima))
        root("pkill -u %d -f -- '%s' ; true" % (UID_B, PALCO_NOMI))
        time.sleep(5.0)
    dopo = _palco_vivo()
    if dopo:
        _dub("⛔ dopo lo sgombero restano %d processi del palco di «%s»" % (dopo, UTENTE))
    return dopo == 0


def accendi_cliente(resta_s):
    """Il cliente di prova, DENTRO il contenitore (aioquic sta li')."""
    log = "%s/cliente.log" % LAV
    root("rm -f %s" % log)
    # ⛔ La copia del cliente sta nella MIA cartella di lavoro, e non
    #    nell'albero: cosi' il modello che la spegne combacia con me e con
    #    nessun altro.
    root("cp -f %s/banchi/01-b3-cliente.py %s/01-b3-cliente.py" % (ALB_DOPO, LAV))
    dentro = ("python3 -u %s/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --larghezza 1280 "
              "--altezza 720 --video-codec h264 --audio-codec pcm --resta %d"
              % (DENTRO_LAV, IND, PORTA, UTENTE, DENTRO_LAV, int(resta_s)))
    root("setsid nohup bash /media/REMOTIX/enter.sh --root %s >> %s 2>&1 & "
         "echo avviato" % (shlex.quote(dentro), log))


def aspetta_sessione(tetto_s):
    """⛔ «Il processo esiste» non e' «la sessione e' aperta»: si guarda il
       REGISTRO (`LEZIONI.md` §1.9)."""
    fine = time.time() + tetto_s
    while time.time() < fine:
        rc, out, _ = root("grep -ac 'sessione aperta utente=%s' %s || true"
                          % (UTENTE, REGISTRO))
        if out.strip().isdigit() and int(out.strip()) > 0:
            return True
        time.sleep(2.0)
    return False


def aspetta_sfratto(tetto_s):
    fine = time.time() + tetto_s
    while time.time() < fine:
        rc, out, _ = root("grep -ac 'linea-morta ' %s || true" % REGISTRO)
        if out.strip().isdigit() and int(out.strip()) > 0:
            return True
        time.sleep(2.0)
    return False


def scena(albero, quale, stallo_s):
    """Una scena su UN albero.  ⛔ Torna `None` se non ha misurato."""
    _log("SCENA «%s» sull'albero %s" % (quale, albero))
    sgombra_i_miei_clienti()
    if not accendi(albero):
        _dub("⛔ il server non si e' acceso: NON misuro")
        return None
    time.sleep(2.0)
    # ⛔⛔ LA FINESTRA COMINCIA DA ZERO, E NON E' PIGRIZIA — difetto di banco
    #     trovato al primo giro vero, 25 agosto 2026.
    #
    #     La prima stesura partiva dal byte del registro **dopo** l'accensione,
    #     per non contare le righe di un giro precedente.  ⛔ Ma `accendi`
    #     TRONCA il registro (`: > $LAV/registro.log`): il file contiene solo
    #     questo server, e cominciare «dopo l'avvio» tagliava fuori proprio **le
    #     righe d'avvio** — cioe' i due predicati di R7.
    # ⇒ ⛔ E il modo in cui falliva e' il peggiore: non «non giudico», ma **un
    #     ROSSO su un prodotto sano**, perche' la riga c'era e la finestra non
    #     la conteneva.  `LEZIONI.md` §2.3, il rosso su codice giusto.
    da = 0
    if registro_ora() is None:
        return None

    if quale == "nato-dopo":
        # 1. ⛔ LO STALLO CON ZERO SESSIONI — e' il cuore della prova.
        _inf("stallo di %.1f s con NESSUNA sessione viva" % stallo_s)
        if stalla(stallo_s) is None:
            _dub("⛔ non ho trovato il pid del server: NON misuro")
            return None
        _inf("apro la sessione DOPO lo stallo")
        accendi_cliente(300)
        if not aspetta_sessione(ATTESA_SESSIONE_S):
            _dub("⛔ la sessione non si e' aperta in %.0f s: NON misuro"
                 % ATTESA_SESSIONE_S)
            return None
        _ok("sessione aperta")
        time.sleep(20.0)          # un po' di regime, per avere righe da contare
    else:
        # ⭐ IL CONTROLLO NEGATIVO: lo stallo con la sessione VIVA.
        _inf("apro la sessione, POI stallo")
        accendi_cliente(300)
        if not aspetta_sessione(ATTESA_SESSIONE_S):
            _dub("⛔ la sessione non si e' aperta in %.0f s: NON misuro"
                 % ATTESA_SESSIONE_S)
            return None
        _ok("sessione aperta")
        time.sleep(15.0)
        _inf("stallo di %.1f s con la sessione VIVA" % stallo_s)
        if stalla(stallo_s) is None:
            _dub("⛔ non ho trovato il pid del server: NON misuro")
            return None
        time.sleep(5.0)

    # 2. ⛔ IL COLPO: `kill -9` al cliente.  Nessun congedo, nessun addio — e'
    #    la scena di §6.3, la sola in cui la linea morta sfratta per SILENZIO.
    _inf("kill -9 al cliente; lo sfratto arriva dopo ~%.0f s" % (SILENZIO_MS / 1000.0))
    sgombra_i_miei_clienti()
    visto = aspetta_sfratto(ATTESA_SFRATTO_S)
    time.sleep(2.0)
    testo = fetta(da)
    spegni()
    sgombra_i_miei_clienti()
    if testo is None:
        return None
    righe = leggi(testo)
    if not visto:
        _dub("⛔ nessuno sfratto in %.0f s: i predicati che ne dipendono NON "
             "giudicano" % ATTESA_SFRATTO_S)
    return {"albero": albero, "scena": quale, "stallo_s": stallo_s,
            "righe": righe, "testo": testo}


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ LA SCENA DELL'AMBIENTE — «Nautilus non parte», e il rosso e' a portata
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ L'ambiente che i banchi componevano per accendere un'applicazione DENTRO la
#    sessione remota era incompleto in **quattro copie a mano**: mancavano
#    `XDG_SESSION_TYPE`, `XDG_CURRENT_DESKTOP` e `GTK_A11Y`.
# ⇒ ⛔⛔ E il danno non e' estetico: un banco che accende un'applicazione con
#      quell'ambiente **misura il fallimento del proprio `env`, non il
#      prodotto** — `LEZIONI.md` §1.30, la prova che non morde.
#
# ⭐ Il metro e' quello che i banchi della fase usano gia': non «il comando e'
#    partito», ma **quante finestre sono VIVE** qualche secondo dopo
#    (`LEZIONI.md` §1.9: un'applicazione che muore subito e una che non c'e'
#    hanno la stessa faccia finche' non si guarda).
# ⭐ E accanto al conto c'e' il MECCANISMO: la riga che l'applicazione scrive
#    morendo (`LEZIONI.md` §1.31 — il sintomo dice quando, il meccanismo dice
#    perche').

# ⛔ L'ambiente VECCHIO, riga per riga come stava nelle quattro copie: si tiene
#    qui perche' e' il ROSSO, e un rosso che non si puo' piu' produrre non e'
#    un controllo negativo — e' un ricordo.
AMBIENTE_VECCHIO = (
    "setpriv --reuid=%(n)d --regid=%(n)d --init-groups env -i "
    "HOME=/home/%(u)s USER=%(u)s LANG=C.UTF-8 "
    "PATH=/usr/local/bin:/usr/bin:/bin XDG_RUNTIME_DIR=/run/user/%(n)d "
    "WAYLAND_DISPLAY=wayland-0 GDK_BACKEND=wayland "
    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%(n)d/bus")

# ⚠ La classe di caratteri: `pgrep -f 'nautilus'` da una shell la cui riga di
#   comando contiene «nautilus» conta SE STESSA (§7.3, terza trappola).
NAUTILU = "nautilu[s]"


def ambiente_nuovo(n, u):
    """Il frammento composto DALL'UNICO POSTO.  ⛔ `None` se non si e' composto:
       un ambiente a meta' non da' rosso, da' un desktop vuoto."""
    p = subprocess.run(["bash", os.path.join(QUI, "10-ambiente-sessione.sh"),
                        str(n), u], capture_output=True, text=True)
    f = p.stdout.strip()
    if p.returncode != 0 or "XDG_SESSION_TYPE=wayland" not in f:
        return None
    return f


def prova_finestra(frammento, etichetta):
    """Accende Nautilus con `frammento` e CONTA chi e' vivo dopo 6 s.

    ⛔ Torna `None` se non ha potuto guardare: «non ho contato» non e' «zero».
    """
    log = "%s/nautilus-%s.log" % (LAV, etichetta)
    root("pkill -u %d -f '%s' ; true" % (UID_B, NAUTILU))
    time.sleep(1.5)
    root("rm -f %s ; touch %s ; chmod 666 %s" % (log, log, log))
    root("setsid nohup %s nautilus >> %s 2>&1 & echo avviato"
         % (frammento, log))
    time.sleep(6.0)
    rc, out, _ = root("pgrep -u %d -c -f '%s' || true" % (UID_B, NAUTILU))
    t = out.strip().split("\n")[0]
    vive = int(t) if t.isdigit() else None
    rc, detto, _ = root("head -c 1200 %s || true" % log)
    root("pkill -u %d -f '%s' ; true" % (UID_B, NAUTILU))
    return {"etichetta": etichetta, "vive": vive, "detto": detto.strip()}


# ⛔⛔ IL METRO E' LA RIGA, NON IL PROCESSO — e questo l'ha insegnato il primo
#     giro vero, 25 agosto 2026.
#
#     La prima stesura contava i processi vivi, che e' il metro che
#     `10-b89-scena.sh` e `10-b92-dieci.py` usano gia' per dire «finestre vive».
#     `[M]` Su tre prove ha detto **1 processo vivo tutte e tre le volte**, con
#     l'ambiente vecchio e col nuovo — ⛔ mentre con quello vecchio Nautilus
#     scriveva *«Failed to initialize display server connection: Unsupported or
#     missing session type ''»* e **non apriva nessuna finestra**.
#
# ⇒ ⭐⭐ IL PROCESSO SOPRAVVIVE AL FALLIMENTO.  «Il processo esiste» non e' «la
#      finestra c'e'» (`LEZIONI.md` §1.9), un piano piu' giu' di dove il
#      progetto l'aveva gia' imparato.  ⛔ E il conto dei processi non e'
#      soltanto inutile qui: e' **cieco nel verso permissivo** — direbbe «due
#      finestre vive» su un desktop in cui non c'e' nessuna finestra.
# ⇒ Il metro e' il MECCANISMO: la riga che l'applicazione scrive fallendo
#   (`LEZIONI.md` §1.31).  ⚠ E il conto dei processi resta accanto come
#   testimone — di se stesso.
RE_NIENTE_DISPLAY = "Failed to initialize display server connection"
RE_A11Y = "org.a11y.Bus was not provided"


def p_la_finestra_si_apre(esito):
    if esito is None or esito.get("detto") is None:
        return _muto("non ho potuto leggere quel che Nautilus ha scritto: "
                     "NON giudico")
    detto = esito["detto"]
    if not detto.strip():
        return _muto("Nautilus non ha scritto niente: NON giudico se la "
                     "finestra si sia aperta")
    if RE_NIENTE_DISPLAY in detto:
        return _no("⛔ con l'ambiente «%s» Nautilus NON si e' agganciato al "
                   "compositore: «%s» ⇒ nessuna finestra, e il conto dei "
                   "processi dice %s — cioe' NON se ne accorge"
                   % (esito["etichetta"], RE_NIENTE_DISPLAY, esito["vive"]))
    return _si("con l'ambiente «%s» Nautilus si aggancia al compositore: "
               "nessun «%s» nel suo registro%s"
               % (esito["etichetta"], RE_NIENTE_DISPLAY,
                  "" if RE_A11Y in detto else ", e nemmeno il rumore di a11y"))


def scena_ambiente():
    """⛔ IL ROSSO E IL VERDE dell'ambiente, nella STESSA sessione."""
    _log("SCENA «ambiente» — Nautilus con l'ambiente di ieri e con quello di oggi")
    sgombra_i_miei_clienti()
    if not accendi(ALB_DOPO):
        _dub("⛔ il server non si e' acceso: NON misuro")
        return None
    accendi_cliente(300)
    if not aspetta_sessione(ATTESA_SESSIONE_S):
        _dub("⛔ la sessione non si e' aperta: NON misuro")
        return None
    _ok("sessione aperta")
    # ⚠ Un respiro perche' GNOME finisca di montarsi: chiedere una finestra a un
    #   compositore che sta ancora nascendo misurerebbe la fretta, non l'ambiente.
    time.sleep(12.0)
    nuovo = ambiente_nuovo(UID_B, UTENTE)
    if nuovo is None:
        _dub("⛔ l'ambiente nuovo non si e' composto: NON misuro")
        return None
    vecchio = AMBIENTE_VECCHIO % {"n": UID_B, "u": UTENTE}
    a = prova_finestra(vecchio, "vecchio")
    b = prova_finestra(nuovo, "nuovo")
    # ⭐ E il controllo negativo: si RIMETTE l'ambiente vecchio e deve tornare
    #    rosso.  Un banco che non sa piu' dire di no non sta misurando la cura.
    c = prova_finestra(vecchio, "vecchio-di-nuovo")
    spegni()
    sgombra_i_miei_clienti()
    sgombra_il_mio_palco()
    return {"vecchio": a, "nuovo": b, "vecchio_di_nuovo": c}


def giudica_ambiente(g):
    """Il verdetto della scena dell'ambiente.  ⭐ Si puo' rifare su un file gia'
       scritto (`--rileggi`): il giudizio non ha bisogno della macchina, e
       rifarlo non costa un turno di GPU a nessuno."""
    _log("VERDETTO — l'AMBIENTE DELLA SESSIONE")
    e = [("⛔ il ROSSO: l'ambiente di ieri",
          p_la_finestra_si_apre(g["vecchio"])),
         ("⭐ il VERDE: l'ambiente di oggi",
          p_la_finestra_si_apre(g["nuovo"])),
         ("⛔ il controllo NEGATIVO: rimesso quello di ieri",
          p_la_finestra_si_apre(g["vecchio_di_nuovo"]))]
    for nome, (v, frase) in e:
        (_ok if v is True else _ko if v is False else _dub)(
            "%s — %s" % (nome, frase))
    # ⭐ E IL TESTIMONE DI SE STESSO: il conto dei processi, che e' il metro
    #    usato oggi dagli altri banchi per dire «finestre vive».
    conti = [(k, g[k]["vive"]) for k in ("vecchio", "nuovo", "vecchio_di_nuovo")]
    _inf("⚠ il metro VECCHIO (processi vivi) direbbe: %s"
         % " · ".join("%s=%s" % (k, v) for k, v in conti))
    if len({v for _k, v in conti}) == 1:
        _inf("⛔ ⇒ lo stesso numero nei tre casi: il conto dei processi NON "
             "distingue una finestra aperta da una che non si e' mai aperta")
    # ⛔ Il rosso ATTESO e' il primo e il terzo; il verde e' il secondo.
    if any(x[1][0] is None for x in e):
        return 3
    if e[0][1][0] is False and e[1][1][0] is True and e[2][1][0] is False:
        return 0
    return 1


# ═══════════════════════════════════════════════════════════════════════════
# IL VERDETTO
# ═══════════════════════════════════════════════════════════════════════════
def giudica(g, prima_wt=None):
    """I predicati su UN giro.  Torna `(esiti, misura_wt)`."""
    righe = g["righe"]
    sfratto = trova_sfratto(righe)
    nato_dopo = g["scena"] == "nato-dopo"
    mis_wt = quota_marcate(righe, aree={"wt"})
    mis_tutte = quota_marcate(righe)
    esiti = [
        ("la riga dello sfratto dice di CHI parla",
         p_sfratto_ha_un_nome(sfratto, UTENTE)),
        ("`fermo_ms=` parla di QUESTA sessione",
         p_fermo_e_di_questa_sessione(sfratto, nato_dopo, g["stallo_s"] * 1000)),
        ("`giri_fermi=` resta il conto della macchina",
         p_giri_fermi_resta_globale(sfratto)),
        ("il metro dello stallo e' tarato",
         p_metro_tarato(righe, g["stallo_s"], deve_esserci=not nato_dopo)),
        ("la riga del guardiano porta gli inquilini",
         p_guardiano_dice_gli_inquilini(righe)),
        ("l'avvio dichiara la meta' sorvegliata di §5.1",
         p_avvio_dichiara_la_sorveglianza(righe)),
    ]
    if prima_wt is not None:
        esiti.append(("l'attribuzione delle righe `wt` e' SALITA",
                      p_la_cura_del_nome_ha_morso(prima_wt, mis_wt)))
    _log("VERDETTO — %s · %s" % (g["scena"], g["albero"]))
    if sfratto:
        _inf("la riga dello sfratto, per intero:")
        print("        " + sfratto.corpo[:400])
    for nome, (v, frase) in esiti:
        (_ok if v is True else _ko if v is False else _dub)("%s — %s" % (nome, frase))
    for etichetta, m in (("righe `wt`", mis_wt), ("tutte le righe", mis_tutte)):
        if m is None:
            _dub("%s: meno di %d righe, NON misuro la frazione"
                 % (etichetta, RIGHE_MINIME))
        else:
            _inf("%s: %d/%d portano un nome = %.1f %%  %s"
                 % (etichetta, m["marcate"], m["righe"], 100 * m["quota"],
                    m["nomi"]))
    return esiti, mis_wt


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ IL MODO CHE CERTIFICA SE STESSO — sano → guasto → risanato
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Un banco non e' finito finche' non lo si e' visto dare ROSSO
#    (`LEZIONI.md` §1.29).  Qui i guasti si innestano nel REGISTRO FINTO, che e'
#    l'ingresso vero di tutti i predicati: girano senza macchina e senza GPU.
# ⚠ E il registro finto e' costruito dalle righe VERE del prodotto, copiate
#   parola per parola: un finto che si somiglia soltanto certifica il banco su
#   una lingua che il prodotto non parla.
_SF = ("linea-morta [::ffff:192.168.0.9]:51000 causa=silenzio stallo_ms=1200 "
       "soglia_stallo_ms=5000 offerti=0 usciti_byte=0 coda_video=0 "
       "silenzio_ms=10002 soglia_silenzio_ms=10000 prove=10 minimo_prove=10 "
       "persi=0 spediti=930 permille=0 finestra_ms=30000 minimo_pacchetti=20 "
       "cwnd=14000 cwnd_left=13000 srtt_us=900 fermo_ms=%d giri_fermi=%d "
       "saltati=0 ritmo_giu=0 ritmo_arretrato=0 ritmo_posti=8 ritmo_scesi=0 "
       "giudizio=⛔ la linea e' MORTA")
_GU = ("guardiano: chiamate=42 peggiore_ms=31 %sgiri_fermi=1 "
       "giro_peggiore_ms=5900 — ⭐ una chiamata per RIPASSO, non per inquilino")
_SV = ("§5.1, la meta' SORVEGLIATA (il ripasso periodico delle sessioni "
       "locali): COLLEGATA, una domanda a logind per ripasso")
_BU = ("⚠ [::ffff:192.168.0.9]:51000: il ciclo del padre e' rimasto indietro "
       "di %d ms (1 buchi in tutto, il peggiore %d ms): la linea morta NON "
       "giudica questo giro e i suoi conti ripartono")


def _finto(chi_sfratto=UTENTE, fermo_ms=0, giri_fermi=1, inquilini=True,
           sorvegliata=True, buco_ms=None, quante=200, marcate=True):
    """Un registro finto, riga per riga come quelle vere."""
    fuori = []
    t0 = 12 * 3600 * 1000

    def riga(ms, area, corpo, chi=None):
        capo = ("[%s] " % chi) if chi else ""
        fuori.append("%02d:%02d:%02d.%03d %-7s %s%s"
                     % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60,
                        ms % 1000, area, capo, corpo))

    riga(t0, "sessione", _SV if sorvegliata else "guardiano delle sessioni "
                                                "locali pronto (bus di sistema)")
    riga(t0 + 10, "rcp", "posto PRESO da %s via [::ffff:192.168.0.9]:51000"
         % UTENTE)
    riga(t0 + 20, "rcp", "sessione aperta utente=%s via=[::ffff:192.168.0.9]:51000"
         % UTENTE, chi=UTENTE if marcate else None)
    for i in range(quante):
        riga(t0 + 100 + i * 30, "wt",
             "ritmo di [::ffff:192.168.0.9]:51000: posti 8, arretrato %d" % (i % 4),
             chi=UTENTE if marcate else None)
    if buco_ms is not None:
        riga(t0 + 20000, "wt", _BU % (buco_ms, buco_ms + 1100),
             chi=UTENTE if marcate else None)
    riga(t0 + 30000, "sessione", _GU % ("inquilini=1 " if inquilini else ""))
    riga(t0 + 40000, "wt", _SF % (fermo_ms, giri_fermi),
         chi=chi_sfratto if marcate else None)
    return "\n".join(fuori) + "\n"


def certifica():
    """⛔ Ogni predicato col SUO guasto, e il guasto si fa GIRARE."""
    casi = []

    def caso(nome, testo, scena_q, stallo_s, quale, atteso):
        righe = leggi(testo)
        sfr = trova_sfratto(righe)
        nato = scena_q == "nato-dopo"
        got = {
            "nome": p_sfratto_ha_un_nome(sfr, UTENTE),
            "fermo": p_fermo_e_di_questa_sessione(sfr, nato, stallo_s * 1000),
            "giri": p_giri_fermi_resta_globale(sfr),
            "metro": p_metro_tarato(righe, stallo_s, deve_esserci=not nato),
            "inq": p_guardiano_dice_gli_inquilini(righe),
            "sorv": p_avvio_dichiara_la_sorveglianza(righe),
        }[quale]
        ok = got[0] is atteso
        casi.append((nome, ok, got[1]))
        (_ok if ok else _ko)("%-58s atteso %-5s letto %-5s — %s"
                             % (nome, atteso, got[0], got[1][:80]))

    _log("⛔ LA CERTIFICAZIONE — sano → guasto → risanato, su registro finto")

    _log("1 · R4 — la riga dello sfratto dice di chi parla")
    caso("sano: la riga porta [provanic3]",
         _finto(), "nato-dopo", 6.0, "nome", True)
    caso("⛔ GUASTO: la riga e' MUTA (il prodotto di ieri)",
         _finto(marcate=False), "nato-dopo", 6.0, "nome", False)
    caso("⛔ GUASTO: la riga porta il nome di UN ALTRO",
         _finto(chi_sfratto="provanic1"), "nato-dopo", 6.0, "nome", False)
    caso("risanato: la riga porta di nuovo [provanic3]",
         _finto(), "nato-dopo", 6.0, "nome", True)
    caso("⛔ MUTO: non c'e' nessuno sfratto ⇒ NON giudico",
         _finto().replace("linea-morta ", "linea-viva "), "nato-dopo", 6.0,
         "nome", None)

    _log("2 · R5 — `fermo_ms=` parla di QUESTA sessione")
    caso("sano: nata dopo lo stallo, fermo_ms=0",
         _finto(fermo_ms=0), "nato-dopo", 6.0, "fermo", True)
    caso("⛔ GUASTO: nata dopo, e fermo_ms=4900 (il contatore GLOBALE)",
         _finto(fermo_ms=4900), "nato-dopo", 6.0, "fermo", False)
    caso("sano: nata dopo, fermo_ms=120 (il ciclo respira, non e' lo stallo)",
         _finto(fermo_ms=120), "nato-dopo", 6.0, "fermo", True)
    caso("⛔ GUASTO: nata dopo, fermo_ms=4600 (il bordo basso della firma)",
         _finto(fermo_ms=4600), "nato-dopo", 6.0, "fermo", False)
    caso("risanato: nata dopo, fermo_ms=0",
         _finto(fermo_ms=0), "nato-dopo", 6.0, "fermo", True)
    caso("sano (controllo negativo): viva durante, fermo_ms=2900",
         _finto(fermo_ms=2900, buco_ms=2900), "vivo-durante", 4.0, "fermo", True)
    caso("⛔ GUASTO: viva durante, e fermo_ms=0 (testimone SPENTO)",
         _finto(fermo_ms=0, buco_ms=2900), "vivo-durante", 4.0, "fermo", False)
    caso("⛔ MUTO: la riga non porta `fermo_ms=` ⇒ NON giudico",
         _finto().replace("fermo_ms=0 ", ""), "nato-dopo", 6.0, "fermo", None)

    _log("3 · `giri_fermi=` resta il conto della macchina")
    caso("sano: giri_fermi=1",
         _finto(giri_fermi=1), "nato-dopo", 6.0, "giri", True)
    caso("⛔ GUASTO: giri_fermi=0 dopo uno stallo iniettato",
         _finto(giri_fermi=0), "nato-dopo", 6.0, "giri", False)
    caso("risanato: giri_fermi=1",
         _finto(giri_fermi=1), "nato-dopo", 6.0, "giri", True)

    _log("4 · ⛔ IL METRO SI TARA PRIMA — valore iniettato contro valore letto")
    caso("sano: iniettati 4000 ms, letti 2900 (dentro la finestra)",
         _finto(buco_ms=2900), "vivo-durante", 4.0, "metro", True)
    caso("⛔ GUASTO: iniettati 4000 ms, letti 300 — il metro non li vede",
         _finto(buco_ms=300), "vivo-durante", 4.0, "metro", False)
    caso("⛔ GUASTO: iniettati 4000 ms, letti 40000 — il metro conta un'altra cosa",
         _finto(buco_ms=40000), "vivo-durante", 4.0, "metro", False)
    caso("risanato: iniettati 4000 ms, letti 3500",
         _finto(buco_ms=3500), "vivo-durante", 4.0, "metro", True)
    caso("⛔ MUTO: nessuna riga di buco con una sessione viva ⇒ NON giudico",
         _finto(), "vivo-durante", 4.0, "metro", None)
    caso("sano: nessuna riga di buco, e nessuna sessione c'era",
         _finto(), "nato-dopo", 6.0, "metro", True)
    caso("⛔ GUASTO: una riga di buco senza nessuna sessione viva",
         _finto(buco_ms=4900), "nato-dopo", 6.0, "metro", False)

    _log("5 · R7 — la riga del guardiano porta gli inquilini")
    caso("sano: `inquilini=1` c'e'", _finto(), "nato-dopo", 6.0, "inq", True)
    caso("⛔ GUASTO: `inquilini=` non c'e' (il prodotto di ieri)",
         _finto(inquilini=False), "nato-dopo", 6.0, "inq", False)
    caso("risanato: `inquilini=1` c'e'", _finto(), "nato-dopo", 6.0, "inq", True)
    caso("⛔ MUTO: nessuna riga «guardiano:» ⇒ NON giudico",
         _finto().replace("guardiano: ", "guardiaNO: "), "nato-dopo", 6.0,
         "inq", None)

    _log("6 · R7 — l'avvio dichiara la meta' sorvegliata")
    caso("sano: la riga c'e'", _finto(), "nato-dopo", 6.0, "sorv", True)
    caso("⛔ GUASTO: la riga non c'e' (il prodotto di ieri)",
         _finto(sorvegliata=False), "nato-dopo", 6.0, "sorv", False)
    caso("risanato: la riga c'e'", _finto(), "nato-dopo", 6.0, "sorv", True)

    _log("7 · ⛔ IL METRO DELL'ATTRIBUZIONE — e il suo `None`")
    m_mute = quota_marcate(leggi(_finto(marcate=False)), aree={"wt"})
    m_dette = quota_marcate(leggi(_finto()), aree={"wt"})
    v, frase = p_la_cura_del_nome_ha_morso(m_mute, m_dette)
    casi.append(("sano: 0 % → 100 % ⇒ la cura ha morso", v is True, frase))
    (_ok if v is True else _ko)("sano: la cura ha morso — %s" % frase)
    v, frase = p_la_cura_del_nome_ha_morso(m_dette, m_dette)
    casi.append(("⛔ GUASTO: stessa frazione ⇒ NON e' salita", v is False, frase))
    (_ok if v is False else _ko)("⛔ GUASTO: stessa frazione — %s" % frase)
    v, frase = p_la_cura_del_nome_ha_morso(m_mute, m_dette)
    casi.append(("risanato: 0 % → 100 %", v is True, frase))
    (_ok if v is True else _ko)("risanato — %s" % frase)
    corto = quota_marcate(leggi(_finto(quante=3)), aree={"wt"})
    v, frase = p_la_cura_del_nome_ha_morso(corto, m_dette)
    casi.append(("⛔ MUTO: meno di %d righe ⇒ NON giudico" % RIGHE_MINIME,
                 v is None and corto is None, frase))
    (_ok if (v is None and corto is None) else _ko)(
        "⛔ MUTO: finestra corta — %s" % frase)

    _log("8 · L'AMBIENTE — «la finestra si apre», e il metro e' la RIGA")
    _sano = ("** Message: Connecting to org.freedesktop.Tracker3.Miner.Files\n")
    _rotto = (_sano + "nautilus-application-Message: Failed to initialize "
              "display server connection: Unsupported or missing session "
              "type ''\n(org.gnome.Nautilus:1): Gtk-WARNING **: Unable to "
              "acquire the address of the accessibility bus: "
              "org.a11y.Bus was not provided by any .service files.\n")
    for nome, esito, atteso in (
            ("sano: nessuna riga di fallimento ⇒ la finestra si apre",
             {"etichetta": "nuovo", "vive": 1, "detto": _sano}, True),
            ("⛔ GUASTO: «Failed to initialize display server» ⇒ ROSSO",
             {"etichetta": "vecchio", "vive": 1, "detto": _rotto}, False),
            ("⛔⛔ GUASTO: e il PROCESSO E' VIVO lo stesso ⇒ ROSSO comunque",
             {"etichetta": "vecchio", "vive": 3, "detto": _rotto}, False),
            ("risanato: nessuna riga di fallimento",
             {"etichetta": "nuovo", "vive": 1, "detto": _sano}, True),
            ("⛔ MUTO: Nautilus non ha scritto niente ⇒ NON giudico",
             {"etichetta": "nuovo", "vive": 1, "detto": "   "}, None),
            ("⛔ MUTO: non ho proprio provato ⇒ NON giudico", None, None)):
        v, frase = p_la_finestra_si_apre(esito)
        ok = v is atteso
        casi.append((nome, ok, frase))
        (_ok if ok else _ko)("%-58s atteso %-5s letto %-5s — %s"
                             % (nome, atteso, v, frase[:80]))
    # ⛔ E l'unico posto dell'ambiente deve DAVVERO portare le tre variabili: se
    #    qualcuno le togliesse, questo caso lo direbbe subito.
    f = ambiente_nuovo(1202, "provanic3")
    manca = [x for x in ("XDG_SESSION_TYPE=wayland", "XDG_CURRENT_DESKTOP=GNOME",
                         "GTK_A11Y=none", "WAYLAND_DISPLAY=wayland-0",
                         "DBUS_SESSION_BUS_ADDRESS=") if f is None or x not in f]
    casi.append(("l'unico posto porta le tre variabili nuove", not manca,
                 "mancano: %s" % manca if manca else "ci sono tutte"))
    (_ok if not manca else _ko)(
        "l'unico posto porta le tre variabili nuove — %s"
        % ("mancano: %s" % manca if manca else "ci sono tutte"))
    # ⚠ E il vecchio NON le ha: se le avesse, il «rosso» non sarebbe un rosso.
    vecchio = AMBIENTE_VECCHIO % {"n": 1202, "u": "provanic3"}
    senza = all(x not in vecchio for x in ("XDG_SESSION_TYPE",
                                           "XDG_CURRENT_DESKTOP", "GTK_A11Y"))
    casi.append(("⛔ l'ambiente di IERI non le ha (o il rosso non e' un rosso)",
                 senza, "il vecchio e' davvero il vecchio" if senza
                 else "⛔ il «vecchio» porta gia' le variabili nuove"))
    (_ok if senza else _ko)("⛔ l'ambiente di IERI non le ha — %s"
                            % ("giusto" if senza else "⛔ NON e' il vecchio"))

    buoni = sum(1 for _n, ok, _f in casi if ok)
    _log("LA CERTIFICAZIONE: %d/%d" % (buoni, len(casi)))
    for n, ok, f in casi:
        if not ok:
            _ko("%s — %s" % (n, f))
    return 0 if buoni == len(casi) else 1


# ═══════════════════════════════════════════════════════════════════════════
# IL LUCCHETTO — e le trappole di §7.3 sono nel riquadro di `09-lucchetto.py`
# ═══════════════════════════════════════════════════════════════════════════
def lucchetto():
    os.environ["LUCCHETTO"] = LUCCHETTO
    spec = importlib.util.spec_from_file_location(
        "luc", os.path.join(QUI, "09-lucchetto.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--scena", default="nato-dopo",
                   choices=["nato-dopo", "vivo-durante"])
    p.add_argument("--tutto", action="store_true",
                   help="le due scene sui due alberi")
    p.add_argument("--rileggi", metavar="FILE",
                   help="rifa' il verdetto dell'ambiente su un file gia' "
                        "scritto, senza macchina e senza GPU")
    p.add_argument("--ambiente", action="store_true",
                   help="⛔ la scena dell'AMBIENTE: Nautilus con l'ambiente di "
                        "ieri (rifiuta) e con quello di oggi (apre)")
    p.add_argument("--stallo", type=float, default=6.0,
                   help="i secondi di SIGSTOP al ciclo del padre")
    p.add_argument("--senza-lucchetto", action="store_true",
                   help="⛔ per la messa a punto: i numeri NON valgono")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if a.rileggi:
        with open(a.rileggi, encoding="utf-8") as f:
            return giudica_ambiente(json.load(f))
    if a.stallo < STALLO_MIN_S:
        _ko("⛔ uno stallo di %.1f s e' sotto il minimo (%.1f): la finestra "
            "attesa non distinguerebbe un buco dal respiro del ciclo"
            % (a.stallo, STALLO_MIN_S))
        return 2

    os.makedirs(FUORI, exist_ok=True)
    luc = None
    if not a.senza_lucchetto:
        luc = lucchetto()
        # ⭐ La durata si SOMMA dalle parti vere e si moltiplica per un margine
        #    DICHIARATO (§7.3, la terza trappola): quattro giri da ~4 minuti,
        #    piu' due compilazioni gia' fatte.  ⚠ Sbagliare in alto costa
        #    qualche minuto al prossimo; sbagliare in basso costa a tutt'e due
        #    la misura.
        quanti = 4 if a.tutto else 1
        stima = 480 if a.ambiente else quanti * 260
        try:
            luc.prendi(IO_SONO, secondi=int(stima * 1.6), attesa=21600)
        except Exception as e:
            _ko("⛔ il turno non e' mai arrivato: %s" % e)
            return 4

    esiti_tutti = []
    try:
        sgombra_i_miei_clienti()
        if not sgombra_il_mio_palco():
            _dub("⛔ il palco di «%s» non si e' chiuso: NON misuro (il giro "
                 "partirebbe da un ri-attacco invece che da un'accensione)"
                 % UTENTE)
            return 2
        rc = terreno_regge()
        if rc != 0:
            _ko("⛔ il terreno non regge (uscita %d): NON misuro" % rc)
            return 2

        if a.ambiente:
            g = scena_ambiente()
            if g is None:
                return 3
            with open(os.path.join(FUORI, "10-f3-ambiente.json"), "w") as f:
                json.dump(g, f, ensure_ascii=False, indent=1)
            return giudica_ambiente(g)

        giri = ([("nato-dopo", ALB_PRIMA), ("nato-dopo", ALB_DOPO),
                 ("vivo-durante", ALB_PRIMA), ("vivo-durante", ALB_DOPO)]
                if a.tutto else [(a.scena, ALB_PRIMA), (a.scena, ALB_DOPO)])
        wt_di = {}
        for quale, albero in giri:
            g = scena(albero, quale, a.stallo)
            if g is None:
                _dub("⛔ la scena «%s» su %s non ha misurato" % (quale, albero))
                esiti_tutti.append((quale, albero, None))
                continue
            prima_wt = wt_di.get((quale, "prima")) if albero == ALB_DOPO else None
            esiti, mis = giudica(g, prima_wt)
            wt_di[(quale, "prima" if albero == ALB_PRIMA else "dopo")] = mis
            esiti_tutti.append((quale, albero, esiti))
            with open(os.path.join(
                    FUORI, "registro-%s-%s.log"
                    % (quale, os.path.basename(albero))), "w") as f:
                f.write(g["testo"])
    finally:
        _log("⛔ LA MACCHINA SI RIMETTE COM'ERA")
        spegni()
        sgombra_i_miei_clienti()
        sgombra_il_mio_palco()
        rc, out, _ = rem("ss -uln | grep -c ':%d ' || true" % PORTA)
        _inf("ascoltatori sulla %d dopo lo sgombero: %s" % (PORTA, out.strip()))
        if luc:
            luc.molla(IO_SONO)

    # ⛔ IL VERDETTO — e l'albero PRIMA deve dare ROSSO, o non si sta misurando
    #    una cura.
    with open(os.path.join(FUORI, "10-f3-esiti.json"), "w") as f:
        json.dump([{"scena": s, "albero": al,
                    "esiti": None if e is None
                             else [(n, v, fr) for n, (v, fr) in e]}
                   for s, al, e in esiti_tutti], f, ensure_ascii=False, indent=1)
    _inf("esiti in %s/10-f3-esiti.json" % FUORI)

    rossi_dopo, muti = 0, 0
    rossi_prima = 0
    for s, al, e in esiti_tutti:
        if e is None:
            muti += 1
            continue
        for n, (v, fr) in e:
            if v is None:
                muti += 1
            elif v is False:
                if al == ALB_DOPO:
                    rossi_dopo += 1
                else:
                    rossi_prima += 1
    _log("IL VERDETTO — rossi sull'albero PRIMA: %d (attesi) · rossi sull'albero "
         "DOPO: %d (attesi 0) · non giudicati: %d"
         % (rossi_prima, rossi_dopo, muti))
    if rossi_prima == 0:
        _ko("⛔ l'albero PRIMA non ha dato NESSUN rosso: senza il rosso di "
            "partenza la cura non e' provata, e' una speranza")
        return 1
    if rossi_dopo:
        return 1
    if muti:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(principale())
