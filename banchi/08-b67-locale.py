#!/usr/bin/env python3
"""08-b67-locale.py — ⭐⭐ IL TERMINE DI PARAGONE LOCALE, MISURATO SUL FERRO.

    python3 banchi/08-b67-locale.py --shm remotix-08-b --secondi 30 \\
            --fuori /media/REMOTIX/tmp/08-b/locale.jsonl

⛔ GIRA SULLA MACCHINA DI PROVA, accanto alla scena.  Non ha bisogno del
   prodotto: guarda **solo** il compositore.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐ PERCHE' ESISTE, e non e' un di piu'
═══════════════════════════════════════════════════════════════════════════════

La specifica dell'utente e' *«un'esperienza il piu' vicina possibile a una
situazione locale»* (`SPECIFICHE.md` §3.2-bis).  ⛔ «Locale» e' il termine di
paragone che lui ha nominato **per primo**, prima di xrdp — e finora nessuno lo
aveva misurato: si diceva «in locale il distacco e' zero» come se fosse ovvio.

⛔ **Non e' zero, ed e' importante che non lo sia**: anche in locale c'e' un
   fotogramma del compositore fra la mano e il pixel.  ⇒ Il traguardo vero di
   questa fase non e' 0 ms, e' **questo numero**, e conoscerlo cambia che cosa
   si chiama «riuscito».

═══════════════════════════════════════════════════════════════════════════════
⭐ CHE COSA MISURA — e le tre grandezze sono TRE, non una
═══════════════════════════════════════════════════════════════════════════════

`04-b30-scena.c` tiene in `/dev/shm` due blocchi.  Dal secondo si leggono:

    eco             l'ultimo input ricevuto, con dentro le sue COORDINATE
    eco_us          quando il COMPOSITORE gliel'ha consegnato   (CLOCK_MONOTONIC)
    eco_disegnato_us quando la scena l'ha DIPINTO la prima volta

e dal primo:

    ultimo_pres     ⭐ quando `wp_presentation` ha detto che quel disegno era
                    **SULLO SCHERMO**.  E' l'unico dei quattro conti della
                    scena che parla di pixel accesi e non di chiamate fatte.

⇒ Tre tratti, e ciascuno risponde a una domanda diversa:

  | tratto | che cosa e' |
  |---|---|
  | `eco_us → eco_disegnato_us` | ⭐ **la scena**: quanto ci mette l'applicazione a reagire.  ⛔ Non e' zero: `04-b30-scena.c` NON chiede un disegno in piu' quando riceve un input — alza il suo eco e aspetta il prossimo `wl_surface.frame`, **come farebbe qualunque applicazione scritta bene**.  ⇒ Questo tratto e' ~mezzo fotogramma, ed e' del modello di Wayland, non nostro |
  | `eco_disegnato_us → presentato` | il **compositore**: comporre e presentare |
  | ⭐⭐ `eco_us → presentato` | **L'ANELLO LOCALE**, ed e' il numero che si consegna: la stessa mano, la stessa scena, il compositore soltanto |

⛔ **E il distacco in pixel si ricava dallo stesso conto**: `velocita' ×
   anello_locale`.  Alla mediana dell'utente (3 400 px/s) un fotogramma a 60 Hz
   vale ~57 px, cioe' **0,08 barre del titolo** contro le 0,50 che lui riferisce
   su REMOTIX.  ⇒ Il confronto e' nella STESSA unita', ed e' questo che lo rende
   un termine di paragone invece di un'impressione.

═══════════════════════════════════════════════════════════════════════════════
⛔ QUEL CHE QUESTO STRUMENTO **NON** SA DIRE — si dichiara prima dei numeri
═══════════════════════════════════════════════════════════════════════════════

  · ⛔ **il pezzo prima del compositore non c'e'**: `eco_us` e' quando il
    compositore ha consegnato l'evento alla scena, non quando la mano si e'
    mossa.  ⇒ Per l'anello locale VERO ci vorrebbe anche il tratto
    dispositivo → compositore, che e' lo stesso pezzo cieco in ingresso che
    `04-b30` dichiara di la' (`[?]` 4-12 ms su un mouse USB).  ⚠ Si dichiara,
    non si somma;
  · ⛔ **il blocco si legge da FUORI, a campione**: non c'e' una riga per ogni
    fotogramma.  ⇒ L'accoppiamento fra un eco e la sua presentazione e'
    **il primo `ultimo_pres` maggiore di `eco_disegnato_us`**, che e' giusto
    per costruzione (la conferma arriva dopo) ⚠ ma puo' saltare un eco se due
    ne arrivano fra due letture.  Quelli saltati **si contano**;
  · ⛔ **`wp_presentation` puo' non esserci**: su una sessione senza monitor il
    campo `presentazione_disponibile` vale 0 e `ultimo_pres` resta fermo.  In
    quel caso questo strumento dice «non ho potuto guardare» e **non**
    consegna `eco_disegnato_us` spacciandolo per una presentazione.

═══════════════════════════════════════════════════════════════════════════════
I CODICI D'USCITA — gli stessi quattro del banco, e per la stessa ragione
    0 conforme · 1 rosso · 2 uso sbagliato · 3 ⛔ NIENTE DA GIUDICARE
"""
import argparse
import importlib.util
import json
import os
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
USCITA_CONFORME, USCITA_NON_CONFORME = 0, 1
USCITA_USO, USCITA_NIENTE_DA_GIUDICARE = 2, 3


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


def carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔ I due lettori si IMPORTANO: `03-marca.py` per il primo blocco (che porta
#    `ultimo_pres`) e `04-b30-anello-input.py` per il secondo (che porta l'eco).
#    Riscriverne uno vorrebbe dire due strutture C descritte in tre posti.
MARCA = carica("marca", os.path.join(QUI, "03-marca.py"))
B30 = carica("b30", os.path.join(QUI, "04-b30-anello-input.py"))


def istantanea(percorso):
    """⛔ Il seqlock si verifica QUI: si legge due volte e si pretende `seq`
    pari e uguale.  Senza, si puo' prendere un `eco` nuovo con un
    `eco_disegnato_us` vecchio e credere a un ritardo mai esistito."""
    try:
        with open(percorso, "rb") as f:
            a = f.read()
            f.seek(0)
            b = f.read()
    except OSError as e:
        return None, "⛔ non ho potuto leggere %s: %s" % (percorso, e)
    if len(a) < 16 or a != b:
        return None, "⚠ il blocco e' cambiato fra le due letture: si riprova"
    d1, perche1 = _primo_blocco(a)
    if d1 is None:
        return None, perche1
    d2, perche2 = B30.leggi_stato_scena_da_byte(a)
    if d2 is None:
        return None, perche2
    if d2["seq"] % 2:
        return None, "⚠ `seq` dispari: una scrittura e' in corso"
    d1.update(d2)
    return d1, None


def _primo_blocco(b):
    """Da `struct stato_condiviso`: i campi che servono qui e basta.

    ⛔ Il formato NON si riscrive: si prende da `03-marca.py`, che e' l'unico
       posto in cui la struttura di `03-scena.c` e' descritta di qua."""
    taglia = struct.calcsize(MARCA.FORMATO_STATO)
    if len(b) < taglia:
        return None, "⛔ il blocco e' %d byte, ne servono %d" % (len(b), taglia)
    a = struct.unpack(MARCA.FORMATO_STATO, b[:taglia])
    if a[0] != MARCA.STATO_MAGIA:
        return None, "⛔ magia 0x%08X: non e' un blocco di `03-scena`" % a[0]
    return ({"seq_scena": a[4], "disegni": a[5], "presentati": a[7],
             "ultimo_disegno_us": a[12], "ultimo_pres_us": a[13],
             "presentazione_disponibile": a[26]}, None)


def raccogli(percorso, secondi, passo_s):
    """⭐ Si campiona, e si CONTANO gli eco saltati: «non l'ho visto» non e'
    «non c'e' stato»."""
    fine = time.time() + secondi
    visti, aperti, chiusi = {}, [], []
    saltati, letture, rifiuti = 0, 0, 0
    ultimo_eco = None
    pres_disp = None
    while time.time() < fine:
        d, perche = istantanea(percorso)
        letture += 1
        if d is None:
            rifiuti += 1
            time.sleep(passo_s)
            continue
        pres_disp = d["presentazione_disponibile"]
        e = d["eco"]
        if e and e != ultimo_eco:
            if ultimo_eco is not None and d["eco_disegni"] == 0:
                saltati += 1
            aperti.append({"eco": e, "eco_us": d["eco_us"],
                           "eco_disegnato_us": d["eco_disegnato_us"]})
            ultimo_eco = e
        # ⭐ La chiusura: il primo `ultimo_pres` DOPO il disegno che porta l'eco.
        for x in list(aperti):
            if x["eco_disegnato_us"] and d["ultimo_pres_us"] > x["eco_disegnato_us"]:
                x["presentato_us"] = d["ultimo_pres_us"]
                chiusi.append(x)
                aperti.remove(x)
        time.sleep(passo_s)
    return {"chiusi": chiusi, "aperti": len(aperti), "saltati": saltati,
            "letture": letture, "rifiuti": rifiuti,
            "presentazione_disponibile": pres_disp}


def q(v, p):
    if not v:
        return None
    w = sorted(v)
    return w[min(len(w) - 1, max(0, int(round(p * (len(w) - 1)))))]


def giudica(r, velocita_px_s, barra_px):
    log("⭐⭐ L'ANELLO LOCALE — la stessa mano, la stessa scena, SENZA di noi")
    if r["presentazione_disponibile"] == 0:
        ko("⛔ `wp_presentation` NON e' disponibile su questa uscita: non c'e' "
           "nessun istante di presentazione da leggere.  ⚠ E NON consegno "
           "`eco_disegnato_us` al posto suo: sarebbe «ho chiamato», non «e' "
           "sullo schermo»")
        return USCITA_NIENTE_DA_GIUDICARE
    c = r["chiusi"]
    if len(c) < 10:
        ko("⛔ %d eco chiusi su %d letture (%d rifiutate dal seqlock, %d "
           "saltati): NON HO NIENTE DA GIUDICARE.  ⚠ Non e' «l'anello locale "
           "e' zero»" % (len(c), r["letture"], r["rifiuti"], r["saltati"]))
        return USCITA_NIENTE_DA_GIUDICARE
    # ⛔⛔ I TRE TRATTI SI CALCOLANO SUGLI STESSI CAMPIONI, e la prima stesura
    #     NO — trovato il 22 agosto 2026, primo giro vero.
    #
    #     Filtrava `eco_disegnato_us >= eco_us` **solo** per il tratto 1 e
    #     lasciava passare tutto agli altri due.  ⇒ `[M]` la scena diceva 7,29
    #     ms, il compositore 20,78 e l'anello **11,71** — cioe' un totale piu'
    #     PICCOLO delle sue due parti, che e' impossibile.  ⛔ Non era il
    #     prodotto: erano tre denominatori diversi sotto la stessa tabella, ed
    #     e' la forma di `LEZIONI.md` §1.9 (una lettura negata non e' una
    #     lettura che dice zero).
    #
    # ⇒ ⭐ Un solo setaccio, applicato una volta, e i buttati SI CONTANO.
    buoni = [x for x in c
             if x["eco_disegnato_us"] >= x["eco_us"]
             and x["presentato_us"] >= x["eco_disegnato_us"]]
    buttati = len(c) - len(buoni)
    if len(buoni) < 10:
        ko("⛔ %d eco chiusi su %d passano il setaccio (un disegno non puo' "
           "precedere l'evento che lo causa, ne' una presentazione il suo "
           "disegno): NON HO NIENTE DA GIUDICARE" % (len(buoni), len(c)))
        return USCITA_NIENTE_DA_GIUDICARE
    c = buoni
    scena = [(x["eco_disegnato_us"] - x["eco_us"]) / 1000.0 for x in c]
    comp = [(x["presentato_us"] - x["eco_disegnato_us"]) / 1000.0 for x in c]
    anello = [(x["presentato_us"] - x["eco_us"]) / 1000.0 for x in c]
    inf("n = %d eco chiusi e BUONI (su %d chiusi · %d buttati dal setaccio · "
        "%d letture · %d rifiutate dal seqlock · %d saltati fra due letture)"
        % (len(c), len(c) + buttati, buttati, r["letture"], r["rifiuti"],
           r["saltati"]))
    inf("  ⛔ e i tre tratti qui sotto sono sugli STESSI %d campioni: 1 + 2 = 3 "
        "campione per campione" % len(c))
    inf("  1. la SCENA        eco ricevuto → dipinto        %.2f ms mediani "
        "(p95 %.2f)" % (q(scena, .5) or 0, q(scena, .95) or 0))
    inf("  2. il COMPOSITORE  dipinto → PRESENTATO          %.2f ms mediani "
        "(p95 %.2f)" % (q(comp, .5) or 0, q(comp, .95) or 0))
    m = q(anello, .5) or 0.0
    inf("  3. ⭐⭐ L'ANELLO LOCALE  eco → sullo schermo     %.2f ms mediani "
        "(p95 %.2f, max %.2f)" % (m, q(anello, .95) or 0, max(anello)))
    px = velocita_px_s * m / 1000.0
    inf("  ⇒ 📏 in PIXEL, alla mediana dell'utente (%.0f px/s): **%.0f px** di "
        "distacco, cioe' **%.3f barre del titolo** (barra = %d px)"
        % (velocita_px_s, px, px / barra_px, barra_px))
    inf("  ⛔ E l'utente riferisce **0,50 barre** su REMOTIX: il confronto e' "
        "nella STESSA unita', ed e' per questo che vale.")
    inf("  ⚠ [?] fuori da questo numero: il tratto dispositivo → compositore "
        "(4-12 ms su un mouse USB), che nessuna API di qua vede.")
    if not anello:
        return USCITA_NIENTE_DA_GIUDICARE
    if m < 0:
        ko("⛔ un anello locale NEGATIVO e' impossibile: e' un difetto della "
           "lettura, non una misura")
        return USCITA_NON_CONFORME
    ok("⭐ il termine di paragone locale c'e', ed e' un numero e non "
       "un'impressione")
    return USCITA_CONFORME


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--shm", default="remotix-08-b")
    p.add_argument("--secondi", type=float, default=25.0)
    p.add_argument("--passo-ms", type=float, default=2.0,
                   help="⛔ 2 ms: piu' fitto del fotogramma, o si saltano eco")
    p.add_argument("--velocita", type=float, default=3400.0,
                   help="la velocita' della mano dell'utente, [M] 3 400 px/s")
    p.add_argument("--barra", type=int, default=720)
    p.add_argument("--fuori", default="")
    p.add_argument("--verbale", default="",
                   help="rigiudica un verbale gia' raccolto, "
                        "senza toccare la macchina")
    a = p.parse_args()
    if a.verbale:
        with open(a.verbale) as f:
            return giudica(json.load(f), a.velocita, a.barra)
    percorso = a.shm if a.shm.startswith("/") else "/dev/shm/" + a.shm
    if not os.path.exists(percorso):
        ko("⛔ «%s» non esiste: la scena non e' mai partita, o ha un altro "
           "`--shm`.  ⚠ NON e' «zero eventi»" % percorso)
        return USCITA_NIENTE_DA_GIUDICARE
    r = raccogli(percorso, a.secondi, a.passo_ms / 1000.0)
    if a.fuori:
        with open(a.fuori, "w") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        inf("verbale in %s" % a.fuori)
    return giudica(r, a.velocita, a.barra)


if __name__ == "__main__":
    sys.exit(main())
