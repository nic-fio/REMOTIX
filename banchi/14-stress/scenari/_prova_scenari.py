#!/usr/bin/env python3
"""_prova_scenari — ⛔ la certificazione degli OTTO SCENARI, col nucleo finto.

    python3 banchi/14-stress/scenari/_prova_scenari.py

⭐ CHE COSA DIMOSTRA, e non e' la stessa cosa che dimostrano gli scenari:
   · ognuno degli otto torna un esito BEN FORMATO (nome, esito 0/1/3, perche');
   · ognuno da' VERDE quando il finto si comporta bene;
   · ⭐⭐ e ognuno da' ROSSO quando il finto ha il difetto che quello scenario
     esiste per prendere — il guasto innestato, uno per scenario;
   · e da' **3**, non un rosso, quando lo strumento non ha potuto guardare (il
     browser che non si accende).  ⛔ Un 3 non e' un verde e non e' un'accusa.

⚠ Qui non c'e' nessun prodotto: questo file prova i GIUDICI, non REMOTIX.  Il
  giro vero e' `14-notte.sh` con il nucleo vero e i browser veri.
"""
import importlib
import inspect
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

import _comune as C                                    # noqa: E402
import _nucleo_finto as F                              # noqa: E402

# scenario · guasto che deve vedere · opzioni per fare in fretta
CASI = [
    ("pesante", "fermo", {"durata_s": 40, "tetto_s": 90, "fermo_massimo_s": 10}),
    ("pesante", "morto", {"durata_s": 20, "tetto_s": 90}),
    ("pesante", "strisce", {"durata_s": 20, "tetto_s": 90}),
    ("lunga", "cresce", {"durata_s": 20, "tetto_s": 90}),
    ("esci_rientra", "fantasma", {"giri": 1, "tetto_s": 90}),
    ("stacca_riattacca", "nero", {"giri": 2, "tetto_s": 90, "tetto_immagine_s": 3}),
    ("riavvio_del_server", "nero", {"giri": 1, "tetto_s": 90, "tetto_immagine_s": 3}),
    ("due_inquilini", "fermo", {"durata_s": 40, "tetto_s": 120, "fermo_massimo_s": 10}),
    ("rete_strozzata", "spirale", {"gradini": [5000], "per_gradino_s": 15,
                                   "tetto_s": 90}),
    ("input_sotto_carico", "muto", {"durata_s": 15, "tetto_s": 90}),
]
SANI = [
    ("pesante", {"durata_s": 20, "tetto_s": 90}),
    ("lunga", {"durata_s": 15, "tetto_s": 90}),
    ("esci_rientra", {"giri": 1, "tetto_s": 90}),
    ("stacca_riattacca", {"giri": 2, "tetto_s": 90, "tetto_immagine_s": 5}),
    ("riavvio_del_server", {"giri": 1, "tetto_s": 90, "tetto_immagine_s": 5}),
    ("due_inquilini", {"durata_s": 20, "tetto_s": 120}),
    ("rete_strozzata", {"gradini": [5000], "per_gradino_s": 15, "tetto_s": 90}),
    ("input_sotto_carico", {"durata_s": 15, "tetto_s": 90}),
]

ESITI = {0: "VERDE", 1: "ROSSO", 3: "non lo so"}
falliti = []


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ PRIMA DI TUTTO: LE FIRME DEL FINTO SONO QUELLE DEL VERO?
#
# `[M]` 23 settembre 2026, e questa prova nasce da li': il finto aveva firme
# inventate, gli scenari ci giravano verdi sopra, e contro il nucleo vero
# morivano al primo passo («too many values to unpack»).  ⇒ Un finto che non ha
# le firme del vero non prova niente, e questa e' la rete che lo prende.
# ═══════════════════════════════════════════════════════════════════════════
def firme():
    try:
        sys.path.insert(0, os.path.dirname(QUI))
        import stress_nucleo as vero
    except Exception as e:                       # noqa: BLE001
        print("  ⚠ il nucleo vero non si importa (%s): le firme NON sono state "
              "confrontate" % str(e)[:90])
        return
    finto = F.Finto("sano")
    guai = 0
    for nome in ("dentro", "crea_inquilino", "sgombera", "scena",
                 "istante_nella_scatola", "conta_dalla_pagina",
                 "conta_dal_server", "avvia_browser", "modello_senza_se_stesso",
                 "completa_la_riga", "numeri_in_vista"):
        f_vero = getattr(vero, nome, None)
        f_finto = getattr(finto, nome, None)
        if f_vero is None or f_finto is None:
            print("  NO   %-24s manca %s" % (nome, "nel vero" if f_vero is None
                                              else "nel finto"))
            guai += 1
            continue
        a = str(inspect.signature(f_vero))
        b = str(inspect.signature(f_finto))
        if a != b:
            print("  NO   %-24s vero%s · finto%s" % (nome, a, b))
            guai += 1
        else:
            print("  OK   %-24s %s" % (nome, a))
    # e i metodi del browser
    vb, fb = vero.Browser, F.Browser
    for nome in ("apri", "entra", "chiudi", "misura", "fotografa", "js",
                 "muovi", "clic", "tasto"):
        a = getattr(vb, nome, None)
        b = getattr(fb, nome, None)
        if a is None or b is None:
            print("  NO   Browser.%-16s manca %s" % (nome, "nel vero" if a is None
                                                     else "nel finto"))
            guai += 1
            continue
        sa, sb = str(inspect.signature(a)), str(inspect.signature(b))
        if sa != sb:
            print("  NO   Browser.%-16s vero%s · finto%s" % (nome, sa, sb))
            guai += 1
    if guai:
        falliti.append("le firme del finto non sono quelle del vero (%d)" % guai)
    else:
        print("  ⭐ tutte le firme del finto combaciano con quelle del nucleo vero")


def _finto(come):
    """Il finto, e con lui le tre funzioni che NON passano dal nucleo.

    ⚠ `riavvia_il_server`, `strozza` e `libera` toccano l'ospite e il tablet:
      qui si mettono da parte, o la certificazione strozzerebbe la rete vera.
    """
    f = F.Finto(come)
    C.riavvia_il_server = lambda d: (True, "il server ascolta (per finta)")
    C.strozza = lambda kbit: (True, "")
    C.libera = lambda: None
    return f


def prova(quale, atteso, come, opzioni, etichetta):
    mod = importlib.import_module(quale)
    f = _finto(come)
    t0 = time.time()
    try:
        r = mod.gira("kde", "firefox", f, opzioni)
    except Exception as e:
        falliti.append("%s (%s): si e' rotto — %s" % (quale, etichetta, e))
        print("  NO   %-22s %-9s si e' rotto: %s" % (quale, etichetta, str(e)[:60]))
        return
    secondi = time.time() - t0
    forma = (isinstance(r, dict) and r.get("scenario") and r.get("perche")
             and r.get("esito") in (0, 1, 3))
    tetto = float(opzioni.get("tetto_s", 1e9)) + 30
    ok = forma and r["esito"] == atteso and secondi <= tetto
    if not ok:
        falliti.append("%s (%s): atteso %s, avuto %s — %s"
                       % (quale, etichetta, ESITI[atteso],
                          ESITI.get(r.get("esito"), r.get("esito")),
                          str(r.get("perche"))[:100]))
    print("  %s   %-22s %-9s %-9s %5.1fs  %s"
          % ("OK " if ok else "NO ", quale, etichetta,
             ESITI.get(r.get("esito"), "?"), secondi,
             str(r.get("perche"))[:70]))


print("== la certificazione degli scenari — col nucleo FINTO, nessun prodotto\n")
print("  ⛔ le firme, prima di tutto")
firme()
print()
print("  ⭐ col finto SANO, ognuno deve dare VERDE")
for quale, opzioni in SANI:
    prova(quale, 0, "sano", opzioni, "sano")

print("\n  ⛔ col GUASTO INNESTATO, ognuno deve dare ROSSO")
for quale, come, opzioni in CASI:
    prova(quale, 1, come, opzioni, come)

print("\n  ⚠ e se il browser non si accende, e' 3 — non un rosso")
for quale, opzioni in SANI[:3]:
    prova(quale, 3, "rotto", opzioni, "rotto")

print()
if falliti:
    print("⛔ %d prove NON reggono:" % len(falliti))
    for r in falliti:
        print("   · %s" % r)
    sys.exit(1)
print("⭐ gli otto scenari danno verde quando devono, rosso quando c'e' il "
      "guasto che cercano, e «non lo so» quando lo strumento non guarda.")
print("⚠ E questa certificazione NON dice niente del prodotto: dice dei giudici.")
