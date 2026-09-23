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
import shutil
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

# ⚠ L'OCCHIO, QUI, GUARDA IN FRETTA — e si dice perche'.  Nella notte aspetta 25
#   secondi che il browser dentro la scatola compaia, e fotografa una volta al
#   secondo; qui non c'e' nessuna scatola che debba salire, e una prova che
#   dorme 25 s per ognuno dei suoi quindici casi non la lancia piu' nessuno.
#   ⛔ Quel che NON si tocca e' il giudizio: soglie, riscaldamento e regole sono
#      quelli veri.  ⭐ E i due numeri finiscono comunque nelle misure di ogni
#      giro, percio' una ripresa fatta cosi' lo dichiara da sola.
os.environ.setdefault("REMOTIX_OCCHIO_ATTESA", "2")
os.environ.setdefault("REMOTIX_OCCHIO_CADENZA", "0.4")
# ⛔ E le fotografie NON vanno in `/tmp`: sul tablet e' in RAM.
DOVE = os.path.expanduser("~/.cache/remotix-prova-scenari")

import _comune as C                                    # noqa: E402
import _nucleo_finto as F                              # noqa: E402

# scenario · guasto che deve vedere · opzioni per fare in fretta
# ⚠ I due «fermo» hanno il tetto LARGO, e il perche' e' del finto: il suo
#   contatore cresce A OGNI LETTURA fino a 20 s dall'accensione.  Da quando il
#   topo legge una volta al secondo, l'ultima crescita cade piu' tardi, e col
#   tetto di 90 s si guardavano solo ~20 s ⇒ il fermo misurava 9,5 s contro una
#   soglia di 10, e passava verde (`[M]` 23 set 2026, stesso caso a 120 s: 29,6
#   s, rosso).  ⛔ Il giudice non e' cambiato: e' cambiato quanto si guarda.
CASI = [
    ("pesante", "fermo", {"durata_s": 40, "tetto_s": 120, "fermo_massimo_s": 10}),
    ("pesante", "morto", {"durata_s": 20, "tetto_s": 90}),
    ("pesante", "strisce", {"durata_s": 20, "tetto_s": 90}),
    ("lunga", "cresce", {"durata_s": 20, "tetto_s": 90}),
    ("esci_rientra", "fantasma", {"giri": 1, "tetto_s": 90}),
    ("stacca_riattacca", "nero", {"giri": 2, "tetto_s": 90, "tetto_immagine_s": 3}),
    ("riavvio_del_server", "nero", {"giri": 1, "tetto_s": 90, "tetto_immagine_s": 3}),
    ("due_inquilini", "fermo", {"durata_s": 40, "tetto_s": 150, "fermo_massimo_s": 10}),
    ("rete_strozzata", "spirale", {"gradini": [5000], "per_gradino_s": 15,
                                   "tetto_s": 90}),
    ("input_sotto_carico", "muto", {"durata_s": 15, "tetto_s": 90}),
]

# ⭐⭐ IL GUASTO CHE IERI NOTTE PASSAVA VERDE, e questa e' la prova che oggi non
#   passa piu'.  Col finto «a_mosaico» **tutti i contatori sono perfetti** —
#   consegnati == dipinti, zero buchi, zero linee morte, nessuna spirale — e
#   l'unica cosa che non va e' l'IMMAGINE.  ⇒ Solo l'occhio puo' dire di no.
#   ⛔ E la controprova si fa con gli STESSI giri e `REMOTIX_OCCHIO=no`: danno
#      VERDE, che e' esattamente quel che e' successo la notte fra il 22 e il
#      23 settembre 2026.
A_MOSAICO = [
    ("pesante", {"durata_s": 40, "tetto_s": 120}),
    ("due_inquilini", {"durata_s": 40, "tetto_s": 150}),
    # ⚠ `lunga` vuole il tetto largo: si concede da sola 120 s di margine
    #   (`tetto.resta() - 120`) e con un tetto stretto non guarderebbe NIENTE.
    ("lunga", {"durata_s": 40, "tetto_s": 240}),
    ("input_sotto_carico", {"durata_s": 40, "tetto_s": 150}),
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
    opzioni = dict(opzioni)
    opzioni.setdefault("dove", DOVE)
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
    # ⭐ E quando c'e' di mezzo l'occhio si stampano i suoi numeri: un verdetto
    #   senza il numero che lo regge non si rilegge domani.
    occhio = ((r.get("misure") or {}).get("occhio")
              if isinstance(r, dict) else None)
    if occhio:
        print("       [M] occhio: %s fotografie viste, %s sopra soglia, %s "
              "devastate, peggiore %s%% · cadenza %ss, attesa %ss%s"
              % (occhio.get("occhio_foto"), occhio.get("occhio_guaste"),
                 occhio.get("occhio_devastate"),
                 occhio.get("occhio_peggiore_per_cento"),
                 occhio.get("cadenza_s"),
                 occhio.get("attesa_prima_di_guardare_s"),
                 "" if occhio.get("giudica", True) else " (misurato, NON giudicato)"))
    return r


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

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ L'OCCHIO: IL GUASTO CHE I CONTATORI NON VEDONO
#
# ⛔ Questa e' la prova che il difetto piu' grave del 23 settembre 2026 — il
#    GIUDICE, non il prodotto — non si puo' ripetere.  Gli stessi giri, con lo
#    stesso finto, due volte: con l'occhio e senza.
# ═══════════════════════════════════════════════════════════════════════════
print("\n  ⛔⛔ IL MOSAICO: contatori perfetti, immagine sbagliata")
print("      ⇒ con l'occhio dev'essere ROSSO")
os.environ["REMOTIX_OCCHIO"] = "si"
for quale, opzioni in A_MOSAICO:
    prova(quale, 1, "a_mosaico", opzioni, "a_mosaico")

print("\n      ⚠ e con l'occhio SPENTO (com'era ieri notte) gli stessi giri")
print("        devono dare VERDE: e' la misura di che cosa mancava.")
os.environ["REMOTIX_OCCHIO"] = "no"
try:
    for quale, opzioni in A_MOSAICO:
        prova(quale, 0, "a_mosaico", opzioni, "cieco")
finally:
    os.environ["REMOTIX_OCCHIO"] = "si"

print("\n  ⭐ e la SECONDA RETE, quella sui soli numeri: il server butta")
print("     fotogrammi gia' codificati e nessuna chiave li ricuce ⇒ ROSSO")
r = prova("pesante", 1, "catena_rotta", {"durata_s": 25, "tetto_s": 120},
          "catena")
ritmo = ((r.get("misure") or {}).get("ritmo") or {}) if isinstance(r, dict) else {}
print("       [M] ritmo: %s buttati, %s chiavi oltre a quella d'apertura ⇒ esito %s"
      % (ritmo.get("buttati_in_tutto"), ritmo.get("chiavi_riparatrici"),
         ritmo.get("esito")))
if ritmo.get("esito") != 1:
    falliti.append("pesante (catena): il giudice sui numeri non ha detto ROSSO "
                   "(%s) — e le righe di riepilogo c'erano" % ritmo.get("perche"))

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CLIENTE CHE NON STA FERMO — il topo e il suo guasto innestato
#
# ⛔ Il difetto del 23 settembre 2026 (schermo fermo per minuti mentre il mouse
#    si muoveva) passava verde in TUTTI gli scenari: nessuno muoveva il mouse.
#    Qui si prova che adesso (1) il mouse si muove davvero in ogni giro che
#    guarda, (2) il giudice sul blocco piu' lungo da' VERDE sul sano, e (3) col
#    compositore congelato da' ROSSO — ⭐ e lo da' LUI SOLO: il blocco di 14 s
#    sta sotto il tetto di 25 s del giudice di prima, che quindi taceva.
# ═══════════════════════════════════════════════════════════════════════════
print("\n  ⭐⭐ IL CLIENTE CHE NON STA FERMO")
r = prova("pesante", 0, "sano", {"durata_s": 45, "tetto_s": 150}, "topo-sano")
topo = ((r.get("misure") or {}).get("topo") or {}) if isinstance(r, dict) else {}
print("       [M] topo: esito %s · blocco piu' lungo %s s su %s s guardati · "
      "%s movimenti · mouse nel %s%% dei secondi"
      % (topo.get("esito"), topo.get("topo_blocco_s"), topo.get("topo_guardati_s"),
         topo.get("topo_mosse"), topo.get("topo_col_mouse_per_cento")))
if topo.get("esito") != 0:
    falliti.append("pesante (topo-sano): il giudice del topo non ha dato VERDE "
                   "sul sano (%s)" % topo.get("perche"))

print("      ⛔ e col COMPOSITORE CONGELATO 14 s (il guasto innestato) ⇒ ROSSO")
os.environ["REMOTIX_SCHERMO_CONGELATO"] = "14"
os.environ["REMOTIX_SCHERMO_CONGELATO_DOPO"] = "5"
try:
    r = prova("pesante", 1, "sano", {"durata_s": 45, "tetto_s": 150}, "congelato")
finally:
    os.environ.pop("REMOTIX_SCHERMO_CONGELATO", None)
    os.environ.pop("REMOTIX_SCHERMO_CONGELATO_DOPO", None)
topo = ((r.get("misure") or {}).get("topo") or {}) if isinstance(r, dict) else {}
g = topo.get("guasto_innestato") or {}
print("       [M] topo: esito %s · blocco %s s · guasto: innestato %s, rilasciato %s, "
      "visto %s" % (topo.get("esito"), topo.get("topo_blocco_s"), g.get("innestato"),
                    g.get("rilasciato"), topo.get("guasto_visto")))
print("       %s" % str(topo.get("perche"))[-90:])
if not (topo.get("esito") == 1 and topo.get("guasto_visto") is True):
    falliti.append("pesante (congelato): il guasto innestato NON e' stato visto "
                   "dal topo (%s)" % topo.get("perche"))
if g.get("rilasciato") is not True:
    falliti.append("pesante (congelato): il compositore NON risulta rilasciato")
altri = [x for x in ((r.get("guasti") or []) if isinstance(r, dict) else [])
         if "NON STA FERMO" not in str(x.get("che_cosa", x))]
if altri:
    falliti.append("pesante (congelato): il rosso non e' solo del topo: %s"
                   % str(altri)[:120])

print("      ⚠ e se la misura e' troppo corta per il congelamento ⇒ 3, non verde")
os.environ["REMOTIX_SCHERMO_CONGELATO"] = "25"
try:
    r = prova("pesante", 0, "sano", {"durata_s": 20, "tetto_s": 90}, "corto")
finally:
    os.environ.pop("REMOTIX_SCHERMO_CONGELATO", None)
topo = ((r.get("misure") or {}).get("topo") or {}) if isinstance(r, dict) else {}
print("       [M] topo: esito %s — %s" % (topo.get("esito"), str(topo.get("perche"))[-80:]))
if topo.get("esito") != 3:
    falliti.append("pesante (corto): un guasto chiesto e non innestato non ha dato 3")

# ⭐ E la terza domanda, che e' la piu' importante delle tre: quando l'occhio
#   NON riconosce la propria scena, deve dire «non lo so» — ⛔ mai rosso.
#   Il finto «fermo» tiene la scena testimone accesa ma i contatori si
#   inchiodano: il rosso deve venire da LORO, non dall'occhio.
print("\n  ⭐ e un occhio che non ha guardato non accusa nessuno")
r = prova("pesante", 1, "fermo",
          {"durata_s": 40, "tetto_s": 120, "fermo_massimo_s": 10}, "fermo")
occhio = ((r.get("misure") or {}).get("occhio") or {}) if isinstance(r, dict) else {}
if occhio.get("esito") == 1:
    falliti.append("pesante (fermo): il rosso l'ha dato l'OCCHIO, e li' il "
                   "guasto e' dei contatori")

try:
    shutil.rmtree(DOVE, ignore_errors=True)
except OSError:
    pass

print()
if falliti:
    print("⛔ %d prove NON reggono:" % len(falliti))
    for r in falliti:
        print("   · %s" % r)
    sys.exit(1)
print("⭐ gli otto scenari danno verde quando devono, rosso quando c'e' il "
      "guasto che cercano, e «non lo so» quando lo strumento non guarda.")
print("⚠ E questa certificazione NON dice niente del prodotto: dice dei giudici.")
