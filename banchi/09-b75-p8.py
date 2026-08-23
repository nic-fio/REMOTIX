#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b75 — ⛔⭐⭐ P8: **il ritmo non cala a scena ferma**, e il controllo si fa
         A COPPIE nello stesso giro.

═══ ⛔ PERCHE' NON BASTA «il contatore e' zero» ══════════════════════════════
`LEZIONI.md` §1.9: **vuoto e proibito hanno la stessa faccia.**  Uno zero su un
ramo mai raggiunto non dimostra niente — e a scena ferma il ramo NON viene
raggiunto affatto, perche' `arretrato` si legge solo all'arrivo di un
fotogramma dal palco e a scena ferma Mutter non ne consegna nessuno (§3.1:
123 attese a vuoto al secondo).  ⇒ Un giro «tutto fermo» misurerebbe il nulla e
lo chiamerebbe una conferma.

═══ ⭐ LA FORMA, ed e' un contratto sul TESTO ═══════════════════════════════
Il prodotto scrive da se', **una volta al secondo e col battito, non coi
fotogrammi** (`webtransport.c:3663`, `ritmo_ciclo()`):

    ritmo di IND:PORTA: arretrato LETTO N volte in quest'ultimo secondo,
    massimo M, ultimo U, posti 2 — D fotogrammi non partiti in questo secondo,
    T in tutto.  ⚠ ZERO LETTURE = il palco non ha consegnato niente (scena
    ferma), e NON «arretrato zero»

⇒ **`LETTO N` distingue «l'anello non e' stato percorso» da «l'arretrato era
  zero»**, ed e' tutto quel che serve: non c'e' nessuno strumento nuovo di cui
  fidarsi, il verbale lo scrive il prodotto.

═══ ⭐ IL GIRO: mezzo ferma, mezzo mossa, ALTERNATI ═════════════════════════
    ferma  N s → mossa  N s → ferma  N s → mossa  N s → …

⛔ Alternate, non due giri separati: due giri separati riaprirebbero la porta a
   «e' cambiato qualcos'altro fra l'uno e l'altro».

═══ ⛔⛔ E I DUE INTERRUTTORI VANNO ACCESI TUTT'E DUE ════════════════════════
`fasi/09` S.3: con `--sgombra-soglia-ms 0` (il predefinito) `arretrato` vale
0 o 1 **per costruzione**, e il regolatore non scatta mai.  ⇒ il giro si fa con

    remotix --sgombra-soglia-ms 100 --ritmo-adattivo

e ⭐ **la riga d'avvio del prodotto lo conferma**: si legge, non si deduce.

═══ ⭐ IL VERDE, e i due rossi che lo buttano ═══════════════════════════════
  · meta' FERMA:  `video_ritmo_scesi` **invariato**, e le righe dicono
                  **«LETTO 0 volte»** — cioe' il ramo non e' stato percorso;
  · meta' MOSSA:  `arretrato` **letto >= 1 volta al secondo**.

⛔ ROSSO 1 — zero letture anche nella meta' mossa ⇒ **il giro non ha misurato
   niente** e si butta invece di interpretarlo (quasi sempre: la soglia spenta).
⛔ ROSSO 2 — discese nella meta' ferma ⇒ **I1 e' violato**, ed e' la ferita di
   v1: *«su un desktop poco mosso scendeva a 2-6 Mbit/s, contento di
   risparmiare»*.

Uso (dal portatile, con l'ambiente della 7920):
    python3 banchi/09-b75-p8.py --coppie 3 --meta 6
"""
import argparse, importlib.util, json, os, re, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))


def _m(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(QUI, f))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


b68 = _m("b68", "09-b68-ritmo.py")
b71 = _m("b71", "09-b71-risveglio.py")
root, rem = b68.root, b68.rem
LAV = b68.LAV
FUORI = os.environ.get("FUORI", "/tmp/09-b75")

# ⚠ L'ora ha i millesimi: serve per mettere ogni riga nella sua meta'.
R_RITMO = re.compile(
    r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) rcp\s+ritmo di \S+: arretrato LETTO (\d+) volte "
    r"in quest'ultimo secondo, massimo (\d+), ultimo (\d+), posti (\d+) — (\d+) "
    r"fotogrammi non partiti in questo secondo, (\d+) in tutto", re.M)
R_SCENDE = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) rcp\s+⛔ \S+: il ritmo SCENDE", re.M)


def orario(m, base=1):
    return (int(m.group(base)) * 3600 + int(m.group(base + 1)) * 60
            + int(m.group(base + 2)) + int(m.group(base + 3)) / 1000.0)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--coppie", type=int, default=3, help="quante coppie ferma/mossa")
    p.add_argument("--meta", type=float, default=6, help="secondi per meta'")
    p.add_argument("--utente", default="prova2")
    p.add_argument("--uid", type=int, default=1002)
    p.add_argument("--tela", default="2560x1080")
    p.add_argument("--movimento", default="pieno")
    p.add_argument("--guardia", type=float, default=2.5,
                   help="secondi da BUTTARE dopo ogni cambio di meta': il "
                        "compositore consegna ancora dopo la morte della scena, "
                        "e la scena appena accesa ci mette ~2 s a dipingere")
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    print("== 09-b75 · P8 a COPPIE — porta %d, tela %s, %d coppie da %g s"
          % (b68.PORTA, a.tela, a.coppie, a.meta))
    d = b71.pulizia()
    if not d["pulita"]:
        print("⛔ mi fermo: non si misura in due sulla stessa macchina")
        return 2
    b71.porta("09-b68-scena.sh")
    b71.porta("09-b71-sessione.sh")

    # ⛔ La riga d'avvio si LEGGE: «acceso» scritto nel comando non e' «in vigore».
    rc, out, _ = root("grep -a 'regolatore del ritmo\\|soglia della coda video' "
                      "%s/registro.log | tail -3" % LAV)
    for r in out.splitlines():
        print("   AVVIO %s" % r.strip()[:190])
    if "ACCESO" not in out:
        print("⛔ il regolatore NON risulta acceso nel registro del server: mi fermo")
        return 2
    if "SPENTA" in out and "soglia" in out:
        print("⛔ la soglia della coda e' SPENTA: `arretrato` non passerebbe mai 1 "
              "e il regolatore non scatterebbe mai (S.3)")
        return 2

    rc, o, _ = root("pgrep -f '01-b3-cliente[.]py' | head -1")
    if not o.strip():
        if not b71.sessione_apri("b75-p8", 3600, utente=a.utente, tela=a.tela):
            print("⛔ la sessione non si e' aperta")
            return 2
        time.sleep(3)

    riga0 = b68.righe_registro()
    tappe = []
    t0 = time.time()
    try:
        for i in range(a.coppie):
            # ── meta' FERMA: nessuna scena, e si VERIFICA che sia morta
            root("env LAV=%s UID_B=%d sh %s/09-b68-scena.sh -- spegni; true"
                 % (LAV, a.uid, LAV))
            for _ in range(10):
                rc, o, _ = root("pgrep -u %d -f '04-b30-scen[a]' | head -1" % a.uid)
                if not o.strip():
                    break
                time.sleep(0.5)
            else:
                print("⛔ la scena non muore: «ferma» non sarebbe ferma")
                return 2
            tappe.append(("ferma", time.time()))
            print("   %2d · ferma  da %6.1f s" % (i + 1, time.time() - t0))
            time.sleep(a.meta)

            # ── meta' MOSSA
            # ⛔⛔ LA TAPPA SI SEGNA **PRIMA** DI ACCENDERE, e non e' una
            #    sfumatura: `09-b68-scena.sh` lancia la scena e poi **dorme 2 s**
            #    per verificare che sia viva.  Segnando la tappa al suo ritorno,
            #    quei ~2,3 secondi — in cui la scena DIPINGE GIA' — finivano
            #    nella meta' «ferma».  `[M]` 23 ago 14:37: la meta' ferma usciva
            #    con 26 righe invece di 18 e **147 letture**, e il banco diceva
            #    GIALLO su un giro sano.  ⚠ Un difetto MIO travestito da difetto
            #    del prodotto — l'ottavo di oggi della stessa famiglia.
            tappe.append(("mossa", time.time()))
            usc, guasto = b71.scena_accendi(a.movimento, uid=a.uid, utente=a.utente)
            if guasto:
                print("⛔ %s" % guasto)
                return 2
            print("   %2d · mossa  da %6.1f s (monitor «%s»)" % (i + 1, time.time() - t0, usc))
            time.sleep(a.meta)
        root("env LAV=%s UID_B=%d sh %s/09-b68-scena.sh -- spegni; true"
             % (LAV, a.uid, LAV))
        tappe.append(("fine", time.time()))
    finally:
        root("env LAV=%s UID_B=%d sh %s/09-b68-scena.sh -- spegni; true"
             % (LAV, a.uid, LAV))

    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    with open(os.path.join(FUORI, "reg-p8.log"), "w") as f:
        f.write(reg)

    # ⛔ Le tappe sono in epoch, le righe in ora locale della macchina: l'ancora
    #    e' la PRIMA riga di ritmo, che sta dentro il giro.
    righe = list(R_RITMO.finditer(reg))
    if not righe:
        print("⛔ nessuna riga «ritmo di …»: il regolatore non ha scritto niente "
              "⇒ il giro non ha misurato nulla")
        return 2
    # ancora: la prima riga cade fra t0 e t0+meta (la prima meta' ferma)
    ancora_reg = orario(righe[0])
    ancora_epoch = tappe[0][1] + 0.5
    # ⚠ si raffina cercando l'offset che mette piu' righe dentro il giro
    off = ancora_epoch - ancora_reg

    # ⛔⭐ LA GUARDIA DOPO OGNI CAMBIO, E PERCHE' NON E' UN TRUCCO.
    #    `[M]` 23 agosto 2026, 14:39: nel PRIMO secondo di ogni meta' ferma il
    #    registro porta ancora 22-40 letture.  ⛔ Non e' il prodotto che non si
    #    ferma: e' che **uccidere il processo della scena non ferma Mutter**, e
    #    i fotogrammi gia' composti continuano ad arrivare per circa un secondo.
    #    Lo stesso dall'altra parte: la scena appena accesa ci mette ~2 s a
    #    dipingere, e quei secondi hanno ZERO letture pur essendo «mossa».
    #    ⇒ I secondi a cavallo di un cambio si BUTTANO, e si dichiara quanti:
    #      contarli da una parte o dall'altra sarebbe attribuire al prodotto un
    #      transitorio che e' del compositore.
    #    ⚠ La guardia NON puo' nascondere il rosso che conta: una discesa a
    #      scena ferma cadrebbe nei secondi CENTRALI, non sul bordo.
    def meta_di(t_reg):
        t = t_reg + off
        quale, quando_ultimo = None, None
        for nome, quando in tappe:
            if t >= quando - 0.05:
                quale, quando_ultimo = nome, quando
        if quale is not None and quando_ultimo is not None:
            if t - quando_ultimo < a.guardia:
                return None          # ⛔ secondo di guardia: non conta
        return quale

    conti = {"ferma": {"righe": 0, "letture": 0, "letture_zero": 0, "discese": 0,
                       "max": 0, "per_secondo": []},
             "mossa": {"righe": 0, "letture": 0, "letture_zero": 0, "discese": 0,
                       "max": 0, "per_secondo": []}}
    for m in righe:
        q = meta_di(orario(m))
        if q not in conti:
            continue
        letto, mx, disc = int(m.group(5)), int(m.group(6)), int(m.group(9))
        c = conti[q]
        c["righe"] += 1
        c["letture"] += letto
        c["discese"] += disc
        c["max"] = max(c["max"], mx)
        if letto == 0:
            c["letture_zero"] += 1
        c["per_secondo"].append(letto)

    scese = [orario(m) for m in R_SCENDE.finditer(reg)]
    disc_meta = {"ferma": 0, "mossa": 0}
    for t in scese:
        q = meta_di(t)
        if q in disc_meta:
            disc_meta[q] += 1

    print("\n== ⭐ IL VERBALE, e lo scrive il PRODOTTO")
    for q in ("ferma", "mossa"):
        c = conti[q]
        print("   %-6s · %2d righe al secondo · arretrato LETTO %d volte in tutto "
              "(%d secondi con ZERO letture) · massimo %d · discese %d"
              % (q, c["righe"], c["letture"], c["letture_zero"], c["max"], c["discese"]))
        print("            letture al secondo: %s" % " ".join(str(x) for x in c["per_secondo"]))
    print("   righe «il ritmo SCENDE»: ferma %d · mossa %d"
          % (disc_meta["ferma"], disc_meta["mossa"]))

    # ── ⛔ IL GIUDIZIO, e i due rossi vengono prima del verde
    esito = {"guardia_s": a.guardia,
             "tappe": [(n, round(t - t0, 2)) for n, t in tappe], "conti": conti,
             "discese_per_meta": disc_meta, "ora": time.strftime("%H:%M:%S")}
    mossa, ferma = conti["mossa"], conti["ferma"]
    if mossa["righe"] == 0 or mossa["letture"] == 0:
        esito["verdetto"] = ("⛔ ROSSO 1 — ZERO letture nella meta' MOSSA: l'anello "
                             "non e' stato percorso, il giro NON HA MISURATO NIENTE")
    elif ferma["discese"] or disc_meta["ferma"]:
        esito["verdetto"] = ("⛔⛔ ROSSO 2 — il ritmo E' SCESO a scena ferma (%d discese): "
                             "I1 violato" % (ferma["discese"] + disc_meta["ferma"]))
    elif mossa["letture"] / max(1, mossa["righe"]) < 1.0:
        esito["verdetto"] = ("⛔ le letture nella meta' mossa sono meno di una al "
                             "secondo (%.2f): sotto il contratto"
                             % (mossa["letture"] / max(1, mossa["righe"])))
    elif ferma["letture"]:
        esito["verdetto"] = ("⚠ GIALLO — nella meta' ferma ci sono %d letture: il palco "
                             "ha consegnato qualcosa, la meta' «ferma» non era ferma"
                             % ferma["letture"])
    else:
        esito["verdetto"] = ("⭐⭐⭐ VERDE — meta' ferma: %d righe, TUTTE «LETTO 0 volte», "
                             "zero discese.  meta' mossa: %.1f letture al secondo, "
                             "massimo %d, zero discese"
                             % (ferma["righe"], mossa["letture"] / max(1, mossa["righe"]),
                                mossa["max"]))
    print("\n== %s" % esito["verdetto"])
    with open(os.path.join(FUORI, "esito-p8.json"), "w") as f:
        json.dump(esito, f, indent=1, ensure_ascii=False)
    print("== esiti in %s" % FUORI)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
