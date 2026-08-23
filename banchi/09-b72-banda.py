#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b72 — ⭐ LA BANDA: quanto costa un video a schermo intero, e che cosa fa un
         BUCO di 3 secondi.

Due misure, e un controllo che le tiene insieme.

═══ §2 · IL VIDEO A SCHERMO INTERO, ALLA TELA DELL'UTENTE ═══════════════════
⛔ E' l'unico numero che manca per decidere se serve un controllo del bitrate.
   Oggi il prodotto codifica a **QP 26 fisso, `rc_mode=CQP`**, e ⛔ **non ha
   nessun tetto di banda** (`grep bit_rate|maxrate|bufsize codificatore.c` →
   zero).  ⇒ quanto chiede, se nessuno glielo dice?

⛔ E UN SOLO NUMERO NON DICE NIENTE: si misurano **tre punti sulla stessa
   scala** — scena ferma · contenuto tipo-desktop · video a schermo intero —
   con la stessa tela, la stessa sessione, lo stesso strumento.  Senza i primi
   due, il terzo e' un numero senza unita' di misura.

⭐ E I BYTE SI CONTANO DUE VOLTE, perche' sono due cose diverse
   (`09-b68` §1.1): il **carico utile** dei fotogrammi (riga `SPEDITO`) e i
   **byte sul filo** (`/proc/net/dev`), che portano anche QUIC, l'audio PCM e i
   riscontri.  A desktop fermo `[M]` il 99,9 % del filo NON e' video.

═══ §3 · IL GRADINO — e non un limite costante ══════════════════════════════
⛔ Strozzare a 20 Mbit/s **costante** non prova niente: in regime la previsione
   e' che non succeda nulla, e una previsione confermata da un banco che non
   poteva contraddirla non e' una misura.  ⇒ serve un **transitorio**.

   linea larga ──► **10 Mbit/s per 3 secondi** ──► linea larga

⛔ LA DOMANDA A CUI RISPONDE, ed e' l'unica: *la spirale di §0.3 ha bisogno di
   una linea povera SOSTENUTA, o basta un buco?*  `[M]` a 2 Mbit/s costanti la
   spirale c'e' (151 abbandoni ⇒ 152 chiavi su 690 fotogrammi).  ⚠ Ma 2 Mbit/s
   e' **un decimo del pavimento** (§3.1-bis: 20 Mbit/s): e' un controllo, non
   una misura della fase.

⭐ E SI GUARDA IL RITORNO, non solo la caduta: **quanto ci mette a tornare come
   prima** dopo che la linea si riapre.  ⛔ Il numero della caduta senza quello
   del ritorno descrive meta' del guasto.

⚠ IL LIMITE DICHIARATO, e vale per tutt'e due: si strozza `lo`, dove la MTU e'
  65536 — non il percorso vero (`fasi/09` §1).  ⇒ i numeri valgono come
  **confronto fra le fasi del gradino**, non come promessa su una linea vera.

Uso (dal portatile):
    python3 banchi/09-b72-banda.py terreno --tela 2560x1080 --utente prova2
    python3 banchi/09-b72-banda.py punti   --secondi 30
    python3 banchi/09-b72-banda.py gradino --scena video
    python3 banchi/09-b72-banda.py chiudi
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("b68", os.path.join(QUI, "09-b68-ritmo.py"))
b68 = importlib.util.module_from_spec(_s); _s.loader.exec_module(b68)
_s2 = importlib.util.spec_from_file_location("b71", os.path.join(QUI, "09-b71-risveglio.py"))
b71 = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(b71)

root, rem = b68.root, b68.rem
LAV = b68.LAV
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/b72")

R_SPED = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) rcp\s+fotogramma (\d+) SPEDITO: "
                    r"(CHIAVE|delta) 0x0\d0\d, codec (\d+), (\d+)x(\d+), (\d+) byte", re.M)
R_ORA = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) ")

# ⛔ I contatori che descrivono la DEGRADAZIONE, e ognuno ha la sua riga nel
#    prodotto.  Si contano **al secondo**, non in totale: un totale non
#    distingue «durante il buco» da «dopo».
SPIE = {
    "abbandoni_5_1": "ABBANDONATO NELLA CODA (§5.1",
    "chiave_trattenuta_5_2": "§5.2 vieta di abbandonarla",
    "richiedi_chiave_accolte": "accolta (§5.2)",
    "chiave_girata_al_palco": "§5.2 vuole una CHIAVE — richiesta girata al palco",
    "delta_buttato_per_chiave": "e' un delta e §5.2 vuole una CHIAVE",
    "datagram_rifiutati": "rifiutat",
}


def sdg(hh, mm, ss, ms):
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def mezzanotte_da(testa):
    hh, mm, resto = testa["ancora_locale"].split(":")
    ss, ms = resto.split(".")
    return testa["ancora_epoch"] - sdg(hh, mm, ss, ms)


# ── il terreno ────────────────────────────────────────────────────────────
def terreno(utente, tela, secondi, uid):
    print("== il terreno: sessione «%s» a %s" % (utente, tela))
    rc, out, _ = root("pgrep -f '01-b3-cliente[.]py' | head -1")
    if out.strip():
        print("   --  chiudo la sessione che c'era (pid %s)" % out.strip())
        b71.sessione_chiudi(); time.sleep(1)
    if not b71.sessione_apri("banda", secondi, utente=utente, tela=tela):
        return False
    time.sleep(2)
    rc, out, _ = root("grep -a 'tela' %s/b71-banda.log | tail -2" % LAV)
    print("   %s" % out.strip()[:200])
    return True


# ⛔⛔ LA VISTA D'INSIEME, E PERCHE' OGNI SCENA ADESSO PASSA DI QUI.
#    La sessione headless di GNOME sta nell'Overview e ci resta: le finestre
#    sono **anteprime rimpicciolite**, e «a schermo intero» non lo e'.
#    `[M]` 23 ago 08:08, guardato nei pixel.  ⇒ prima di misurare si manda un
#    ESC per la porta che usa il prodotto (`09-b72-tasto.py`), e **si guarda
#    l'immagine** invece di crederci.
def esci_dalla_vista(uid):
    rc, out, err = root("python3 %s/09-b72-tasto.py --uid %d --tasti 1" % (LAV, uid), 60)
    return "TASTI MANDATI" in out


def scena(tipo, uid, utente):
    """⛔ «ferma» non e' «una scena che non si muove»: e' **nessuna scena**."""
    if tipo == "ferma":
        ok, chi = spegni_tutto(uid)
        if not ok:
            return None, "⛔ «ferma» non e' ferma: %s" % chi
        time.sleep(1.0)
        return "ferma", None
    if tipo.startswith("video"):
        film = ("/tmp/film-grana.webm" if tipo == "video-grana"
                else "/media/REMOTIX/src/08-D/scena-utente.webm")
        # ⛔ L'ESC PRIMA, non dopo: e' il tasto che esce dalla vista d'insieme
        #    di GNOME **ed e' anche** quello che esce dallo schermo intero del
        #    browser.  Mandato dopo, spegneva il video che doveva accendere.
        esci_dalla_vista(uid)
        rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s FILM=%s sh %s/09-b72-video.sh accendi"
                            % (LAV, uid, utente, film, LAV), 180)
        if "VIDEO ACCESO" not in out:
            return None, "il video non e' partito: %s" % (out + err).strip()[:400]
        time.sleep(4)
        return tipo, None
    usc = b68.monitor()
    if not usc:
        return None, "nessun monitor nel registro"
    rc, out, err = root("env LAV=%s UID_B=%d UTENTE=%s sh %s/09-b68-scena.sh %s %s"
                        % (LAV, uid, utente, LAV, usc, tipo), 120)
    if "SCENA ACCESA" not in out:
        return None, "la scena non e' partita: %s" % (out + err).strip()[:400]
    time.sleep(1)
    esci_dalla_vista(uid)
    time.sleep(1.5)
    return tipo, None


# ⛔⛔ E `UID_B` VA PASSATO ANCHE PER SPEGNERE — pagato il 23 ago, 08:11.
#    `09-b72-video.sh -- spegni` senza `UID_B` prende il riposo **1001** e
#    ammazza il Firefox di «prova», non quello di «prova2».  ⇒ nei quattro
#    punti di quel giro il video **e' rimasto acceso sotto**, e «ferma» ha
#    dato 25,9 fotogrammi/s e 0,235 Mbit/s: un desktop fermo che non era fermo.
#    ⚠ Terza volta oggi che il guasto e' «un numero plausibile».
# ⇒ da qui in poi si spegne E SI VERIFICA, e chi non muore lo si dice.
def spegni_tutto(uid):
    root("env LAV=%s UID_B=%d sh %s/09-b68-scena.sh -- spegni; true" % (LAV, uid, LAV))
    root("env LAV=%s UID_B=%d sh %s/09-b72-video.sh -- spegni; true" % (LAV, uid, LAV))
    for _ in range(15):
        rc, out, _ = root("pgrep -u %d -f 'firefo[x]|04-b30-scen[a]' | head -5" % uid)
        if not out.strip():
            return True, ""
        time.sleep(1)
    rc, out, _ = root("pgrep -au %d -f 'firefo[x]|04-b30-scen[a]' | head -3" % uid)
    return False, out.strip()[:300]


# ── ⭐ IL GIRO: l'agente sulla macchina guarda il filo (e muove il gradino) ──
def giro(etichetta, fasi, senza_tc, stretta="10mbit", ritardo="15ms"):
    riga0 = b68.righe_registro()
    usc = "%s/b72-%s.jsonl" % (LAV, etichetta)
    durata = sum(x[1] for x in fasi)
    rc, out, err = root("python3 %s/09-b72-agente.py --porta %d --fasi %s "
                        "--rate-stretta %s --ritardo %s %s --uscita %s"
                        % (LAV, b68.PORTA, ",".join("%s:%g" % x for x in fasi),
                           stretta, ritardo, "--senza-tc" if senza_tc else "", usc),
                        int(durata) + 180)
    if rc != 0:
        return {"etichetta": etichetta, "guasto": "⛔ l'agente: %s" % (out + err)[:400]}
    rc, jl, _ = root("cat %s" % usc, 120)
    righe = [json.loads(x) for x in jl.splitlines() if x.strip()]
    testa = righe[0]
    coda = [x for x in righe if x.get("che") == "coda"][0]
    mez = mezzanotte_da(testa)

    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    with open(os.path.join(FUORI, "reg-%s.log" % etichetta), "w") as f:
        f.write(reg)

    # ⭐ la linea del tempo, un secchiello al secondo
    secchi = {}

    def secchio(t):
        return secchi.setdefault(round(t - coda["campioni"][0]["t"]) if coda["campioni"] else 0,
                                 None)
    t_zero = coda["campioni"][0]["t"] if coda["campioni"] else testa["ancora_epoch"]
    linea = {}

    def tocca(t, chiave, quanto=1, byte=0):
        k = int(t - t_zero)
        v = linea.setdefault(k, {"fot": 0, "chiavi": 0, "delta": 0, "byte": 0})
        for s in SPIE:
            v.setdefault(s, 0)
        v[chiave] = v.get(chiave, 0) + quanto
        v["byte"] += byte

    sped = []
    for m in R_SPED.finditer(reg):
        t = mez + sdg(m.group(1), m.group(2), m.group(3), m.group(4))
        sped.append((t, m.group(6), int(m.group(10))))
        tocca(t, "fot", 1, int(m.group(10)))
        tocca(t, "chiavi" if m.group(6) == "CHIAVE" else "delta", 1)
    for riga in reg.splitlines():
        mo = R_ORA.match(riga)
        if not mo:
            continue
        t = mez + sdg(mo.group(1), mo.group(2), mo.group(3), mo.group(4))
        for nome, frammento in SPIE.items():
            if frammento in riga:
                tocca(t, nome)

    # le fasi, con i loro istanti veri
    conf = []
    t = t_zero
    for e, (nome, durata_f) in zip(coda["eventi"], fasi):
        conf.append({"fase": nome, "t_inizio": e["t_dopo"], "durata_s": durata_f,
                     "costo_tc_ms": e.get("costo_ms")})
    return {"etichetta": etichetta, "fasi": conf, "testa": testa,
            "qdisc_dopo": coda.get("qdisc_dopo"),
            "vietata_dopo": coda.get("vietata_dopo"),
            "campioni": coda["campioni"], "t_zero": t_zero,
            "linea": {k: linea[k] for k in sorted(linea)},
            "spediti": len(sped),
            "byte_carico": sum(x[2] for x in sped),
            "chiavi": sum(1 for x in sped if x[1] == "CHIAVE"),
            "spoglio": b68.spoglia(reg, max(1.0, sum(x[1] for x in fasi))),
            "ora": testa["ancora_locale"]}


def filo_mbit(d, da, a):
    """Mbit/s sul filo fra due istanti, dai campioni cumulativi."""
    c = [x for x in d["campioni"] if da <= x["t"] <= a]
    if len(c) < 2:
        return None
    return round((c[-1]["tx_byte"] - c[0]["tx_byte"]) * 8 / (c[-1]["t"] - c[0]["t"]) / 1e6, 3)


def stampa_punto(d, secondi):
    if "guasto" in d:
        print("   %s" % d["guasto"]); return
    car = d["byte_carico"] * 8 / secondi / 1e6
    filo = filo_mbit(d, d["t_zero"], d["t_zero"] + secondi + 1)
    print("   fotogrammi %d (%.2f/s) = %d CHIAVE + %d delta"
          % (d["spediti"], d["spediti"] / secondi, d["chiavi"], d["spediti"] - d["chiavi"]))
    print("   ⭐ carico video %d byte ⇒ **%.3f Mbit/s** = %.1f %% di 20 Mbit/s"
          % (d["byte_carico"], car, car / 20 * 100))
    print("      byte medio per fotogramma %d"
          % (d["byte_carico"] // max(1, d["spediti"])))
    print("   ⭐ FILO (`lo`, tutto: QUIC + audio PCM + riscontri) **%s Mbit/s** = %.1f %% di 20"
          % (filo, (filo or 0) / 20 * 100))
    s = d["spoglio"]
    print("   abbandoni §5.1 %d · chiave trattenuta %d · RICHIEDI_CHIAVE %d"
          % (s["abbandoni_5_1"], s["chiave_trattenuta_5_2"], s["richiedi_chiave_accolte"]))


def stampa_gradino(d):
    if "guasto" in d:
        print("   %s" % d["guasto"]); return
    print("   fasi: %s" % " · ".join("%s da +%.1f s (tc %s ms)"
                                     % (f["fase"], f["t_inizio"] - d["t_zero"],
                                        f["costo_tc_ms"]) for f in d["fasi"]))
    print("   ⛔ la rete dopo: lo «%s» · enp7s0 «%s»"
          % (d["qdisc_dopo"], d["vietata_dopo"]))
    print("   s  | fot chiavi delta |   kbyte | abb §5.1 | rich.chiave | filo Mbit/s")
    for k in sorted(d["linea"]):
        v = d["linea"][k]
        f = filo_mbit(d, d["t_zero"] + k, d["t_zero"] + k + 1)
        fase = ""
        for x in d["fasi"]:
            if d["t_zero"] + k >= x["t_inizio"] - 0.05:
                fase = x["fase"]
        print("   %2d | %3d %6d %5d | %7.1f | %8d | %11d | %s  %s"
              % (k, v["fot"], v["chiavi"], v["delta"], v["byte"] / 1000.0,
                 v.get("abbandoni_5_1", 0), v.get("richiedi_chiave_accolte", 0),
                 ("%7.3f" % f) if f is not None else "      -", fase))


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["terreno", "punti", "gradino", "chiudi"])
    p.add_argument("--utente", default="prova2")
    p.add_argument("--uid", type=int, default=1002)
    p.add_argument("--tela", default="2560x1080")
    p.add_argument("--secondi", type=int, default=30)
    p.add_argument("--scene", default="ferma,barra,pieno,video")
    p.add_argument("--scena", default="video")
    p.add_argument("--stretta", default="10mbit")
    p.add_argument("--prima", type=float, default=8)
    p.add_argument("--buco", type=float, default=3)
    p.add_argument("--dopo", type=float, default=17)
    p.add_argument("--durata-sessione", type=int, default=3600)
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    print("== 09-b72 · la BANDA — porta %d, utente «%s», tela %s"
          % (b68.PORTA, a.utente, a.tela))
    d = b71.pulizia()
    if not d["pulita"]:
        print("⛔ mi fermo: non si misura in due sulla stessa macchina"); return 2

    if a.passo == "chiudi":
        spegni_tutto(a.uid); b71.sessione_chiudi()
        print("   scene spente, sessione chiusa")
        return 0

    b71.porta("09-b72-agente.py"); b71.porta("09-b72-video.sh")
    b71.porta("09-b71-sessione.sh"); b71.porta("09-b72-tasto.py")

    if a.passo == "terreno":
        return 0 if terreno(a.utente, a.tela, a.durata_sessione, a.uid) else 2

    rc, out, _ = root("pgrep -f '01-b3-cliente[.]py' | head -1")
    if not out.strip():
        if not terreno(a.utente, a.tela, a.durata_sessione, a.uid):
            return 2

    esiti = []
    try:
        if a.passo == "punti":
            for tipo in a.scene.split(","):
                nome, guasto = scena(tipo, a.uid, a.utente)
                if guasto:
                    print("\n-- «%s» ⛔ %s" % (tipo, guasto))
                    esiti.append({"etichetta": tipo, "guasto": guasto}); continue
                time.sleep(2)
                print("\n-- punto «%s» · %d s · tela %s" % (tipo, a.secondi, a.tela))
                e = giro("punto-%s" % tipo, [("solo", a.secondi)], senza_tc=True)
                e["scena"] = tipo
                stampa_punto(e, a.secondi)
                esiti.append(e)
        else:
            nome, guasto = scena(a.scena, a.uid, a.utente)
            if guasto:
                print("⛔ %s" % guasto); return 2
            time.sleep(2)
            print("\n-- il GRADINO · %g s larga → %g s a %s → %g s larga · scena «%s»"
                  % (a.prima, a.buco, a.stretta, a.dopo, a.scena))
            e = giro("gradino-%s" % a.scena,
                     [("larga", a.prima), ("stretta", a.buco), ("larga", a.dopo)],
                     senza_tc=False, stretta=a.stretta)
            stampa_gradino(e)
            esiti.append(e)
    finally:
        spegni_tutto(a.uid)
        with open(os.path.join(FUORI, "b72-%s.json" % a.passo), "w") as f:
            json.dump(esiti, f, ensure_ascii=False, indent=1)
        print("\n== esiti in %s/b72-%s.json" % (FUORI, a.passo))
        print("== ⛔ la rete si rimette e si VERIFICA:")
        b68.rimetti()
    return 0


if __name__ == "__main__":
    sys.exit(principale())
