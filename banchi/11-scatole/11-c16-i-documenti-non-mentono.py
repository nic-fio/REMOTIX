#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c16 — ⭐⭐ «I DOCUMENTI NON MENTONO» — la maglia che guarda LE CARTE
===========================================================================

    python3 11-c16-i-documenti-non-mentono.py
    python3 11-c16-i-documenti-non-mentono.py --certifica
    python3 11-c16-i-documenti-non-mentono.py --radice /altro/deposito

⛔ Questa maglia non prova il prodotto e non prova la rete: prova che **i
   documenti dicano ancora la verita' sul deposito in cui vivono**.

---------------------------------------------------------------------------
⛔⛔ IL GUASTO CHE PRENDE — *la coordinata che marcisce da sola*
---------------------------------------------------------------------------

Il 28 agosto 2026 e' venuto fuori questo, ed e' il motivo per cui la maglia
esiste.  `MASTERPLAN.md` citava `src/figlio.c:3290` con la marca `[M]` e la
data.  ⭐ **Il 25 agosto alle 15:18 `MOVIMENTO_FPS` era davvero alla riga
3290** — verificato commit per commit.  Poi il 27 il codice si e' mosso, e la
coordinata e' diventata falsa **senza che nessuno l'avesse toccata**.

⇒ ⛔ E' la forma peggiore di documento sbagliato: **nessuno ha fatto niente di
  male**.  Non c'e' un commit da incolpare, non c'e' una svista, non c'e' una
  riga scritta con leggerezza.  Il documento e' rimasto fermo e la verita' si e'
  spostata.  ⭐ Ogni altra affermazione di questo progetto ha qualcosa che la
  sorveglia — una misura, un banco, una certificazione.  Le carte no.

---------------------------------------------------------------------------
⭐ LE QUATTRO COSE CHE GUARDA
---------------------------------------------------------------------------

  1  ⛔ **nessuna coordinata di riga** verso il nostro codice (`src/x.c:123`).
     Non «e' sbagliata»: **c'e'**.  Una coordinata giusta oggi e' una
     coordinata sbagliata la settimana prossima, e non si puo' distinguere.
     ⇒ Si cita il NOME (`src/figlio.c` · `MOVIMENTO_FPS`), che si muove col
     codice.

  2  ogni **percorso citato** esiste nel deposito — o porta una marca che dice
     perche' no: `⟨v1⟩` (le carte del prodotto superato), `⟨mutter⟩`/`⟨gnome⟩`/
     `⟨lsquic⟩`… (alberi di altri, in `.gitignore`).

  3  nessun **link markdown** `[testo](percorso)` che non porta da nessuna
     parte.  ⚠ Un link rotto e' peggio di una citazione: promette di aprirsi.

  4  ⛔ **una sola** intestazione «DA QUI SI RIPRENDE» in tutta la
     documentazione.  Ne aveva sei, con sei date diverse.

---------------------------------------------------------------------------
⚠ QUEL CHE QUESTA MAGLIA **NON** SA FARE, e va detto
---------------------------------------------------------------------------

⛔ **Non sa se un documento dica il vero.**  Sa solo se i suoi *rimandi*
   reggono.  Una misura sbagliata, una data inventata, una conclusione che il
   codice contraddice: ⭐ **passano tutte di qui senza che se ne accorga**.
   ⇒ Chi legge un verde di C16 sappia che vuol dire «gli indirizzi tengono»,
   non «le carte sono giuste».  E' il rovescio di `LEZIONI.md` §1.3 applicato
   ai documenti.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ i quattro controlli reggono
  1  ⛔ almeno uno non regge ⇒ rosso
  3  ⛔ non ho potuto guardare (la radice non e' un deposito git)
  2  il terreno non regge, o l'uso e' sbagliato
===========================================================================
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

MARCHE_ESTERNE = ("⟨v1⟩", "⟨mutter⟩", "⟨gnome⟩", "⟨lsquic⟩", "⟨quiche⟩",
                  "⟨ngtcp2⟩", "⟨kwin⟩", "⟨xrdp⟩", "⟨esterno⟩")
# le carte storiche: fotografie di quel che era, non si rincorrono
ESCLUSE = ("fondamenta/", "memoria/")

# ⭐ I RAPPORTI TOLTI APPOSTA — 94 file, usciti il 16 agosto 2026 per decisione
#    dell'utente, e ⛔ **non persi**: vivono in `0c85e5c` e `FASI.md` §0 ha la
#    ricetta per tirarne fuori uno.  ⇒ Citarli e' PROVENIENZA e si tiene: dice
#    da dove viene una misura.  ⛔ **Linkarli** no: un link promette di aprirsi.
#    Per questo stanno qui e non nel controllo 3, che i link li prende lo stesso.
TOLTI_APPOSTA = ("fasi/rapporti/", "web/rapporti/")

ECCEZIONI = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "11-c16-eccezioni.txt")


def eccezioni_dichiarate(percorso=ECCEZIONI):
    """⛔ le eccezioni stanno in un file, non nel codice: cosi' si CONTANO"""
    fuori = []
    try:
        with open(percorso, encoding="utf-8") as f:
            for riga in f:
                riga = riga.rstrip("\n")
                if not riga.strip() or riga.lstrip().startswith("#"):
                    continue
                chiave = riga.split("\t")[0].strip()
                if chiave:
                    fuori.append(chiave)
    except OSError:
        return []
    return fuori

RX_RIGA  = re.compile(r'`(?:src|banchi)/[A-Za-z0-9_./-]+\.(?:c|h|py|sh):[0-9]+`')
RX_PERC  = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:c|h|py|sh|md|html|json|jsonl|pam|rs))`')
RX_LINK  = re.compile(r'\[[^\]]+\]\(([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|png|jpg|sh|py|c|h))\)')
RX_RIPR  = re.compile(r'DA QUI SI RIPRENDE')


def documenti(radice):
    try:
        fuori = subprocess.check_output(["git", "-C", radice, "ls-files", "*.md"],
                                        text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [f for f in fuori.split() if not f.startswith(ESCLUSE)]


def elenco_file(radice):
    fuori = subprocess.check_output(["git", "-C", radice, "ls-files"], text=True)
    tutti = set(fuori.split())
    nomi = set(p.rsplit("/", 1)[-1] for p in tutti)
    return tutti, nomi


def guarda(radice, eccezioni=None):
    """torna (coordinate, percorsi_morti, link_rotti, riprese) — ognuno una lista"""
    scusati = eccezioni if eccezioni is not None else eccezioni_dichiarate()
    docs = documenti(radice)
    if docs is None:
        return None
    tutti, nomi = elenco_file(radice)
    coord, morti, rotti, riprese = [], [], [], []
    for d in docs:
        p = os.path.join(radice, d)
        try:
            with open(p, encoding="utf-8") as f:
                righe = f.read().split("\n")
        except OSError:
            continue
        for n, riga in enumerate(righe, 1):
            for m in RX_RIGA.finditer(riga):
                coord.append(f"{d}:{n}  {m.group(0)}")
            if RX_RIPR.search(riga) and riga.lstrip("> ").startswith("#"):
                riprese.append(f"{d}:{n}")
            # i percorsi marcati ⟨…⟩ sono dichiarati di altri: non si rincorrono
            ripulita = riga
            for marca in MARCHE_ESTERNE:
                ripulita = re.sub(re.escape(marca) + r'\s*[A-Za-z0-9_./-]+', "", ripulita)
            for m in RX_PERC.finditer(ripulita):
                c = m.group(1)
                if c in tutti or c.rsplit("/", 1)[-1] in nomi:
                    continue
                if os.path.exists(os.path.join(radice, c)):
                    continue
                if c.startswith(TOLTI_APPOSTA):
                    continue
                if any(s in c for s in scusati):
                    continue
                morti.append(f"{d}:{n}  {c}")
            for m in RX_LINK.finditer(riga):
                c = m.group(1)
                if c.startswith(("http", "#")):
                    continue
                base = os.path.dirname(d)
                if c in tutti or os.path.exists(os.path.join(radice, c)) \
                   or os.path.exists(os.path.join(radice, base, c)):
                    continue
                rotti.append(f"{d}:{n}  {c}")
    return coord, morti, rotti, riprese


def stampa(nome, brutti, tetto, spiega):
    if not brutti:
        print(f"  \033[1;32mOK\033[0m  {nome}")
        return True
    print(f"  \033[1;31mNO\033[0m  {nome} — {len(brutti)}")
    print(f"      ⛔ {spiega}")
    for b in brutti[:tetto]:
        print(f"        {b}")
    if len(brutti) > tetto:
        print(f"        … e altri {len(brutti) - tetto}")
    return False


def giro(radice, silenzioso=False, eccezioni=None):
    visto = guarda(radice, eccezioni)
    if visto is None:
        if not silenzioso:
            print("  ⛔ non ho potuto guardare: la radice non e' un deposito git")
        return 3
    coord, morti, rotti, riprese = visto
    if silenzioso:
        return 1 if (coord or morti or rotti or len(riprese) > 1) else 0
    print("== C16 — i documenti non mentono ==")
    verdi = [
        stampa("nessuna coordinata di riga verso il nostro codice", coord, 8,
               "una coordinata giusta oggi e' sbagliata la settimana prossima: si cita il NOME"),
        stampa("ogni percorso citato esiste (o porta la marca ⟨…⟩)", morti, 8,
               "il documento manda a un file che nel deposito non c'e'"),
        stampa("nessun link markdown rotto", rotti, 8,
               "un link rotto e' peggio di una citazione: promette di aprirsi"),
        stampa("una sola intestazione «DA QUI SI RIPRENDE»",
               riprese if len(riprese) > 1 else [], 8,
               "piu' d'una, e chi riapre non sa quale valga"),
    ]
    print()
    if all(verdi):
        print("  ⭐ i quattro controlli reggono.")
        print("  ⚠ e questa maglia dice che gli INDIRIZZI tengono, ⛔ non che le")
        print("    carte siano giuste: una misura sbagliata passa di qui intatta.")
        return 0
    return 1


def certifica():
    """⛔ una maglia che non e' mai stata vista fallire non e' una maglia"""
    print("== certificazione di C16 — sa dare rosso? ==\n")
    guasti = {
        "una coordinata di riga":      ("g1.md", "vedi `src/main.c:111` per il resto.\n"),
        "un percorso che non esiste":  ("g2.md", "sta in `src/inventato_dal_nulla.c`.\n"),
        "un link markdown rotto":      ("g3.md", "il rapporto e' [qui](fasi/rapporti/mai-esistito.md).\n"),
        "due «DA QUI SI RIPRENDE»":    ("g4.md", "# DA QUI SI RIPRENDE — ieri\n\n# DA QUI SI RIPRENDE — oggi\n"),
    }
    esiti = []
    for nome, (file, testo) in guasti.items():
        with tempfile.TemporaryDirectory() as t:
            subprocess.run(["git", "-C", t, "init", "-q"], check=True)
            with open(os.path.join(t, "sano.md"), "w", encoding="utf-8") as f:
                f.write("Un documento onesto: cita `sano.md` e basta.\n")
            subprocess.run(["git", "-C", t, "add", "sano.md"], check=True)
            if giro(t, silenzioso=True, eccezioni=[]) != 0:
                print(f"  ⛔ il terreno SANO non e' verde: la certificazione non vale")
                return 2
            with open(os.path.join(t, file), "w", encoding="utf-8") as f:
                f.write(testo)
            subprocess.run(["git", "-C", t, "add", file], check=True)
            rosso = giro(t, silenzioso=True, eccezioni=[]) == 1
            esiti.append(rosso)
            print(f"  {'✓ VISTO ' if rosso else '⛔ NON VISTO'}  {nome}")
    print()
    if all(esiti):
        print("  ⭐ C16 sa dare rosso su tutt'e quattro i guasti, e il terreno")
        print("    sano resta verde. ⇒ Un suo verde vuol dire qualcosa.")
        return 0
    print("  ⛔ almeno un guasto innestato NON e' stato visto: la maglia tace.")
    return 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--radice", default=None, help="il deposito da guardare")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()
    if a.certifica:
        return certifica()
    radice = a.radice or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    ).stdout.strip()
    if not radice:
        print("  ⛔ non sono dentro un deposito git, e --radice non e' stata data")
        return 2
    return giro(radice)


if __name__ == "__main__":
    sys.exit(main())
