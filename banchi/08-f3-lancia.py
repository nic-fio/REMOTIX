#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""08-F3 · ⛔ CHE COSA SONO I 17 MILLISECONDI — il lanciatore del banco.

⛔ GIRA SUL PORTATILE, e non tocca ne' la macchina di prova ne' nessuna porta:
   il tratto da diagnosticare sta INTERAMENTE dentro il browser.

    python3 banchi/08-f3-lancia.py --prepara          # lo stream + l'indice
    python3 banchi/08-f3-lancia.py --giro             # tutti i giri
    python3 banchi/08-f3-lancia.py --giro --solo bitmap-hw

⭐ IL METODO, ed e' quello che ha gia' reso in questa fase: **si strumenta
  prima, e si lascia che lo strumento smentisca l'ipotesi.**

⛔ E QUEL CHE QUESTO BANCO NON FA: non misura l'anello, non misura il distacco,
  non da' un «prima» a nessuna cura.  Risponde a UNA domanda — *aspettando che
  cosa?* — e il numero della strada vera si prende in sessione.
"""
import argparse
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


def carica(nome, percorso):
    import importlib.util
    s = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def b17():
    return carica("b17", os.path.join(QUI, "03-b17-ritardo.py"))


# ═══════════════════════════════════════════════════════════════════════════
# §1  LO STREAM — ⛔ vero, codificato, e con l'indice dei pacchetti
#
# ⛔ Non si inventa un fotogramma: un decodificatore a cui si da' rumore
#    risponde in un tempo che non e' quello del prodotto.  ⇒ `ffmpeg` fa uno
#    stream della MISURA del palco di A (1460×888) a 60/s, con UNA chiave
#    sola — come il prodotto, che manda chiavi solo quando servono.
# ═══════════════════════════════════════════════════════════════════════════
LARGHEZZA, ALTEZZA, RITMO = 1460, 888, 60

CODEC_STRINGA = {
    # ⭐ `hev1` (non `hvc1`) = i parametri viaggiano NELLO stream (Annex-B),
    #   che e' come li manda il nostro server.
    "hevc": "hev1.1.6.L153.B0",
    # ⭐ `avc1.640033` = High, livello 5.1.  ⚠ La memoria del progetto dice
    #   che H.264 e' la strada dei motori mobili (`avc1.640032` verificato).
    "h264": "avc1.640033",
}


def prepara(lavoro, secondi=10):
    log("1 · LO STREAM E L'INDICE — ⛔ codificato davvero, non inventato")
    os.makedirs(lavoro, exist_ok=True)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        ko("⛔ senza `ffmpeg`/`ffprobe` non c'e' stream: non e' «il banco e' "
           "rosso», e' «non ho potuto guardare»")
        return False
    fatti = 0
    for codec, righe in (
        ("hevc", ["-c:v", "libx265", "-preset", "ultrafast", "-x265-params",
                  "keyint=%d:min-keyint=%d:scenecut=0:bframes=0:log-level=error"
                  % (secondi * RITMO, secondi * RITMO), "-f", "hevc"]),
        ("h264", ["-c:v", "libx264", "-preset", "ultrafast", "-x264-params",
                  "keyint=%d:min-keyint=%d:scenecut=0:bframes=0"
                  % (secondi * RITMO, secondi * RITMO),
                  "-profile:v", "high", "-level", "5.1", "-f", "h264"]),
    ):
        est = {"hevc": "h265", "h264": "h264"}[codec]
        fuori = os.path.join(lavoro, "stream." + est)
        if not os.path.exists(fuori):
            c = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                  "-f", "lavfi", "-i",
                  "testsrc2=size=%dx%d:rate=%d:duration=%d"
                  % (LARGHEZZA, ALTEZZA, RITMO, secondi)]
                 + righe[:-2] + ["-pix_fmt", "yuv420p"] + righe[-2:] + [fuori])
            r = subprocess.run(c, capture_output=True, text=True)
            if r.returncode != 0:
                ko("⛔ `ffmpeg` per %s: %s" % (codec, r.stderr.strip()[:200]))
                continue
        # ⛔ L'indice si legge da `ffprobe`, non si deduce dalle dimensioni:
        #    un Annex-B non ha una lunghezza in testa e tagliarlo a occhio
        #    darebbe pacchetti plausibili e sbagliati.
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                            "-show_packets", "-of", "json", fuori],
                           capture_output=True, text=True)
        if r.returncode != 0:
            ko("⛔ `ffprobe` per %s: %s" % (codec, r.stderr.strip()[:200]))
            continue
        pac = json.loads(r.stdout)["packets"]
        indice = {
            "codec": CODEC_STRINGA[codec],
            "larghezza": LARGHEZZA, "altezza": ALTEZZA, "ritmo": RITMO,
            "pacchetti": [{"da": int(p["pos"]), "quanti": int(p["size"]),
                           "chiave": "K" in p.get("flags", "")} for p in pac],
        }
        # ⛔ E si CONTROLLA che l'indice copra il file: un indice corto
        #    lascerebbe fuori dei byte e il decodificatore direbbe «flusso
        #    guasto» invece di «l'indice e' sbagliato».
        ultimo = indice["pacchetti"][-1]
        copre = ultimo["da"] + ultimo["quanti"]
        vero = os.path.getsize(fuori)
        if copre != vero:
            ko("⛔ %s: l'indice copre %d byte su %d — NON lo uso"
               % (codec, copre, vero))
            continue
        chiavi = sum(1 for p in indice["pacchetti"] if p["chiave"])
        with open(fuori + ".json", "w") as f:
            json.dump(indice, f)
        ok("%s · %d pacchetti · %d chiave/i · %.1f MiB · %dx%d"
           % (codec, len(pac), chiavi, vero / 1048576.0, LARGHEZZA, ALTEZZA))
        fatti += 1
    return fatti == 2


# ═══════════════════════════════════════════════════════════════════════════
# §2  IL SERVIZIO — ⛔ i file si servono, non si aprono con `file://`
#
# `fetch()` su `file://` e' vietata, e `createImageBitmap` su una pagina
# `file://` prende regole d'origine diverse: si servirebbe un palco che non e'
# quello del prodotto.
# ═══════════════════════════════════════════════════════════════════════════
class Zitto(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def servi(cartella, porta):
    class H(Zitto):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=cartella, **k)

    class S(socketserver.TCPServer):
        # ⛔ Sulla CLASSE, non sull'oggetto: `server_bind` gira dentro
        #   `__init__`, cioe' PRIMA che si possa toccare l'oggetto — e il
        #   secondo giro moriva su `Address already in use` (TIME_WAIT).
        allow_reuse_address = True

    s = S(("127.0.0.1", porta), H)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    return s


# ═══════════════════════════════════════════════════════════════════════════
# §3  I GIRI — ⛔ ognuno risponde a una domanda, e nessuno risponde da solo
# ═══════════════════════════════════════════════════════════════════════════
PULITO = 999999          # ⭐ «i controlli non girano»: il numero senza strumento

GIRI = [
    # nome                strada   codec   hw   guasto            campione leggi
    ("2d-hw-pulito",      "2d",     "hevc", "si", "", PULITO, 0,
     "⭐⭐ IL «PRIMA» DI A, rifatto SENZA strumento addosso: la strada "
     "`?tela=2d`, quella dei 17,48 ms"),
    ("bitmap-hw-pulito",  "bitmap", "hevc", "si", "", PULITO, 0,
     "⭐⭐ LA STRADA VERA del prodotto (`bitmaprenderer`), senza strumento"),
    # ⭐⭐⭐ I DUE GIRI CHE RIFANNO QUEL CHE FA IL BANCO DI A
    ("2d-hw-letto",       "2d",     "hevc", "si", "", PULITO, 1,
     "⭐⭐⭐ LA STRADA VECCHIA **CON LA LETTURA DEI PIXEL DENTRO IL RICHIAMO**, "
     "cioe' esattamente quel che fa il prologo di `04-b30`.  ⛔ Se i 17,48 ms "
     "compaiono qui e non nel giro pulito, sono dello STRUMENTO"),
    ("2d-hw-letto-freq",  "2d",     "hevc", "si", "", PULITO, 2,
     "⭐ LA CONTRO-PROVA del meccanismo: la stessa lettura ma con "
     "`willReadFrequently`.  Se e' la retrocessione della tela, qui cambia"),
    ("bitmap-hw-letto",   "bitmap", "hevc", "si", "", PULITO, 1,
     "⭐⭐ e lo stesso sulla strada vera, come lo fa il prologo di `08-b67`"),
    # ── i giri con i controlli: gli unici che sanno dire *aspettando che cosa*
    ("2d-hw",             "2d",     "hevc", "si", "", 1, 0,
     "la strada vecchia CON i controlli"),
    ("bitmap-hw",         "bitmap", "hevc", "si", "", 1, 0,
     "la strada vera con i controlli"),
    ("2d-hw-letto-c",     "2d",     "hevc", "si", "", 1, 1,
     "⭐⭐ la strada vecchia con la lettura E i controlli: e' il giro che "
     "attribuisce l'attesa quando l'attesa c'e'"),
    # ── l'ipotesi (a): lo stesso contenuto, un decodificatore diverso ──────
    ("2d-h264-hw",        "2d",     "h264", "si", "", PULITO, 0,
     "⚠ un ALTRO decodificatore hardware sullo stesso palco"),
    ("2d-h264-sw",        "2d",     "h264", "no", "", PULITO, 0,
     "⛔ IL CONTROLLO DELL'IPOTESI (a): lo stesso stream in SOFTWARE.  "
     "⚠ HEVC non si puo' usare per questo confronto — `[M]` Chrome rifiuta "
     "`prefer-software` su HEVC, cioe' su questo motore HEVC e' SOLO hardware"),
    ("2d-h264-sw-letto",  "2d",     "h264", "no", "", PULITO, 1,
     "⭐⭐ e la lettura su un fotogramma che NON viene dalla GPU: se il costo "
     "e' la rilettura di una superficie di GPU, qui NON deve comparire"),
    # ── i controlli positivi: senza questi, nessun verde vale ─────────────
    ("bitmap-hw-brucia",  "bitmap", "hevc", "si", "g1-brucia-nel-richiamo", 1, 0,
     "⭐ LA TARATURA: 20 ms bruciati fra il richiamo e la chiamata devono "
     "uscire NEL TRATTO GIUSTO (`pre`), e non altrove"),
    ("bitmap-hw-coda",    "bitmap", "hevc", "si", "g5-brucia-dopo-i-controlli", 1, 0,
     "⭐⭐ IL CONTROLLO POSITIVO DELL'IPOTESI (c): 20 ms bruciati DOPO che i "
     "controlli sono partiti.  ⇒ Tutti e quattro devono salire di 20 insieme "
     "e la NETTA restare a zero"),
    ("2d-hw-grande",      "2d",     "hevc", "si", "g6-disegno-grande", 1, 0,
     "⭐⭐ IL CONTROLLO POSITIVO DELL'IPOTESI (a): si da' al DISEGNO lavoro "
     "vero sul fotogramma (3840×2160).  ⇒ Il tratto 9 deve salire e i "
     "controlli NO"),
    ("bitmap-hw-quadro",  "bitmap", "hevc", "si", "g7-vetro-sul-quadro", 1, 0,
     "⭐⭐ IL CONTROLLO POSITIVO DELL'IPOTESI (b): il vetro si consegna SUL "
     "QUADRO.  ⇒ `tot` deve salire di ~un quadro e `bmp` non muoversi"),
]


def un_giro(palco, base, strada, codec, hw, guasto, campione, leggi, quanti,
            ritmo, salta):
    url = ("%s/08-f3-quanto-aspetta.html?strada=%s&codec=%s&hw=%s&quanti=%d"
           "&ritmo=%d&guasto=%s&salta=%s&campione=%d&leggi=%d&freq=%d"
           % (base, strada, codec, hw, quanti, ritmo, guasto,
              "1" if salta else "0", campione,
              1 if leggi else 0, 1 if leggi == 2 else 0))
    palco.chiama("Page.navigate", url=url)
    fine = time.time() + 20 + quanti / max(1, ritmo) * 1.6
    while time.time() < fine:
        t = palco.valuta("document.getElementById('stato')"
                         " ? document.getElementById('stato').textContent : ''",
                         attendi=False) or ""
        m = re.search(r"RISULTATO=(\{.*\})\s*$", t, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception as e:                       # noqa: BLE001
                return {"ok": False, "perche": "verbale illeggibile: %s" % e}
        time.sleep(0.5)
    return {"ok": False, "perche": "il giro non ha consegnato in tempo"}


def riga(s):
    if not s:
        return "        —"
    return ("n=%-4d med=%7.2f  [p05 %6.2f · p95 %6.2f · max %7.2f]"
            % (s["n"], s["med"], s["p05"], s["p95"], s["max"]))


def stampa(v):
    if not v.get("ok"):
        ko("⛔ %s" % v.get("perche"))
        return
    c, S = v["conti"], v["serie"]
    p = v["palco"]
    inf("palco · GPU %s · quadri %d (%s) · quadro %s ms"
        % (p.get("gpu"), p.get("quadri"),
           "SCANOUT" if p.get("scanout") else "⛔ NESSUNO SCANOUT",
           p.get("quadro_med_ms")))
    inf("conti · consegnati %d · usciti %d · dipinti %d · saltati %d · "
        "senza attesa %d · errori %s"
        % (c["consegnati"], c["usciti"], c["dipinti"], c["saltati"],
           c["senza_attesa"], c["errori"] or "nessuno"))
    inf("costo dello strumento: %s µs per fotogramma" % v.get("costo_strumento_us"))
    for k, etichetta in (("out", "8 · decode() → richiamo      "),
                         ("tot", "⭐ richiamo → VETRO (9+10)   "),
                         ("letto", "  · la lettura del banco     "),
                         ("pre", "  · richiamo → chiamata      "),
                         ("draw1", "9 · 1° drawImage  (2D)      "),
                         ("draw2", "10· 2° drawImage  (2D)      "),
                         ("bmp", "9'· createImageBitmap        "),
                         ("bmp_netta", "9'· ⭐ NETTA (− il gemello)  "),
                         ("bmp_su_piccola", "9'· ⭐ NETTA (− la piccola)  "),
                         ("vetro", "10'· transferFromImageBitmap "),
                         ("dopo_raf", "  · vetro → prossimo quadro  "),
                         ("micro", "C1· microtask (controllo)    "),
                         ("macro", "C2· macrotask (controllo)    "),
                         ("piccolo", "C3· bitmap PICCOLA (controllo)"),
                         ("raf", "C4· prossimo quadro (controllo)")):
        if S.get(k):
            print("        %s %s" % (etichetta, riga(S[k])))
    vd = v["verdetti"]
    if not vd.get("giudicabile"):
        ko("⛔ %s" % vd.get("perche"))
        return
    if vd.get("nessuna_attesa"):
        ok("⭐ %s" % vd["nessuna_attesa"]["perche"])
        return
    for nome, chiave in (("(a) il DECODIFICATORE", "a_fotogramma"),
                         ("(b) il QUADRO       ", "b_quadro"),
                         ("(c) la CODA         ", "c_coda")):
        d = vd.get(chiave) or {}
        s = d.get("spiega")
        t = "%s · %s" % (nome, json.dumps({k: x for k, x in d.items()
                                           if k != "perche"}))
        if s is True:
            ok(t)
        elif s is False:
            print("        %s%s%s  %s" % (GRIGIO, "no", GRIGIO, t))
        else:
            dub("%s · %s" % (nome, d.get("perche", "non giudicabile")))


def giro(a):
    lavoro = a.lavoro
    if not prepara(lavoro, a.secondi):
        return 3
    for f in ("08-f3-quanto-aspetta.html",):
        shutil.copy(os.path.join(QUI, f), os.path.join(lavoro, f))
    s = servi(lavoro, a.porta_http)
    base = "http://127.0.0.1:%d" % a.porta_http
    ok("i file si servono da %s" % base)

    m17 = b17()
    log("2 · IL PALCO")
    palco = m17.Palco(schermo=a.schermo, diagnosi=a.diagnosi,
                      finestra=(1200, 800),
                      lavoro=os.path.join(lavoro, "palco"), gpu=True)
    # ⛔ I giri di prima si RILEGGONO, o un `--solo` cancellerebbe il confronto
    #    invece di aggiornarlo — e il rosso comparirebbe sul confronto, non sul
    #    giro.  ⚠ E ogni riga porta il suo `quando`: chi rilegge sa se il
    #    confronto mescola due sedute.
    esiti = {}
    vecchi = os.path.join(QUI, "08-f3-esiti.json")
    if os.path.exists(vecchi):
        try:
            with open(vecchi) as f:
                esiti = json.load(f)
        except Exception:                                # noqa: BLE001
            esiti = {}
    try:
        misurato = palco.accendi()
        ok("Xvfb %s e Chrome accesi" % misurato)
        for (nome, strada, codec, hw, guasto, campione, leggi, perche) in GIRI:
            if a.solo and nome not in a.solo:
                continue
            log("GIRO «%s» — %s" % (nome, perche))
            v = un_giro(palco, base, strada, codec, hw, guasto, campione,
                        leggi, a.quanti, a.ritmo, a.salta)
            v["giro"] = nome
            v["perche"] = perche
            esiti[nome] = v
            stampa(v)
    finally:
        try:
            palco.spegni()
        except Exception:                                # noqa: BLE001
            pass
        s.shutdown()

    with open(os.path.join(QUI, "08-f3-esiti.json"), "w") as f:
        json.dump(esiti, f, indent=1, ensure_ascii=False)
    log("3 · IL CONFRONTO — ⛔ e qui i numeri si CONFRONTANO, non si stampano")
    return confronta(esiti)


# ═══════════════════════════════════════════════════════════════════════════
# §4  IL CONFRONTO — ⛔ un numero stampato e mai confrontato e' la forma di
#     difetto piu' comune che abbiamo (`LEZIONI.md` §1.20)
# ═══════════════════════════════════════════════════════════════════════════
def attesa_di(v):
    """⭐ L'attesa = il tratto 9 di A: `richiamo → 1° disegno finito`."""
    if not v or not v.get("ok"):
        return None
    S = v["serie"]
    s = S["bmp"] if v["strada"] == "bitmap" else S["draw1"]
    return s["med"] if s else None


def tot_di(v):
    """⭐ `richiamo → vetro` = i tratti 9+10 di A messi insieme (17,58 ms)."""
    if not v or not v.get("ok") or not v["serie"].get("tot"):
        return None
    return v["serie"]["tot"]["med"]


def confronta(e):
    rossi = 0
    A9, A10 = 17.48, 0.10                    # `[M]` agente A, 22 agosto 2026
    ATTESO = A9 + A10

    def r(nome):
        return e.get(nome)

    print("\n    \033[1m⭐⭐ LA DOMANDA: I 17,48 ms DI A SI RIVEDONO?\033[0m")
    print("        il «prima» di A, strada `?tela=2d`, tratti 9+10 = %.2f ms"
          % ATTESO)
    for nome in ("2d-hw-pulito", "2d-hw-letto", "2d-hw-letto-freq",
                 "bitmap-hw-pulito", "bitmap-hw-letto",
                 "2d-h264-hw", "2d-h264-sw", "2d-h264-sw-letto"):
        v = r(nome)
        t, at = tot_di(v), attesa_di(v)
        if t is None:
            print("        %-20s —  (%s)" % (nome, (v or {}).get("perche", "manca")))
            continue
        print("        %-20s 9 = %7.2f · 9+10 = %7.2f  (%+.0f %% sul «prima»)"
              % (nome, at, t, 100.0 * (t - ATTESO) / ATTESO))

    # ── ⭐⭐ LA TESI: la lettura dei pixel del banco COSTA sul disegno ──────
    pu, le = attesa_di(r("2d-hw-pulito")), attesa_di(r("2d-hw-letto"))
    if pu is None or le is None:
        ko("⛔ TESI · manca `2d-hw-pulito` o `2d-hw-letto`: non concludo")
        rossi += 1
    else:
        d = le - pu
        print("\n    ⭐ QUANTO COSTA, AL DISEGNO, IL FATTO CHE IL BANCO RILEGGA I PIXEL")
        print("        senza lettura %7.2f ms · con lettura %7.2f ms  ⇒ %+.2f ms"
              % (pu, le, d))
        if d >= 5.0:
            ok("⭐⭐ LA LETTURA DEL BANCO SPOSTA IL DISEGNO DI %+.2f ms: una "
               "parte dei 17,48 e' dello STRUMENTO, non del prodotto" % d)
        else:
            inf("la lettura del banco sposta il disegno di %+.2f ms: NON e' "
                "lei a fare i 17,48" % d)

    # ── la contro-prova del meccanismo ────────────────────────────────────
    fr = attesa_di(r("2d-hw-letto-freq"))
    if le is not None and fr is not None:
        print("        e con `willReadFrequently`: %7.2f ms (%+.2f rispetto "
              "alla lettura nuda)" % (fr, fr - le))

    # ── la taratura: 20 ms bruciati devono uscire nel tratto giusto ───────
    t, db = r("bitmap-hw-brucia"), r("bitmap-hw")
    if (t and t.get("ok") and t["serie"].get("pre")
            and db and db.get("ok") and db["serie"].get("pre")):
        d = t["serie"]["pre"]["med"] - db["serie"]["pre"]["med"]
        if 17.0 <= d <= 23.0:
            ok("TARATURA · i 20 ms bruciati escono nel tratto giusto: %+.2f ms "
               "in `pre`" % d)
        else:
            ko("⛔ TARATURA · i 20 ms bruciati NON escono in `pre`: %+.2f ms.  "
               "⇒ Lo strumento non attribuisce, e i suoi verdetti non valgono" % d)
            rossi += 1
    else:
        ko("⛔ TARATURA · il giro `bitmap-hw-brucia` non c'e': senza, nessun "
           "verdetto di questo banco e' credibile")
        rossi += 1

    # ── ⭐⭐ I TRE CONTROLLI POSITIVI ──────────────────────────────────────
    base = r("bitmap-hw")
    b_att = attesa_di(base)
    b_micro = (base["serie"]["micro"]["med"]
               if base and base.get("ok") and base["serie"].get("micro") else None)
    b_tot = tot_di(base)

    # (c) la coda
    c = r("bitmap-hw-coda")
    if c and c.get("ok") and b_att is not None:
        ca, cm = attesa_di(c), c["serie"]["micro"]["med"]
        net = c["serie"].get("bmp_su_piccola")
        salgono = (ca - b_att) >= 15.0 and (cm - (b_micro or 0)) >= 15.0
        netta_ferma = net is not None and abs(net["med"]) < 3.0
        if salgono and netta_ferma:
            ok("CONTROLLO (c) · col thread occupato attesa %+.2f e microtask "
               "%+.2f salgono INSIEME, e la NETTA resta %.2f ⇒ il banco sa "
               "riconoscere la coda" % (ca - b_att, cm - (b_micro or 0),
                                        net["med"]))
        else:
            ko("⛔ CONTROLLO (c) · attesa %+.2f · microtask %+.2f · netta %s: "
               "il controllo della coda e' cieco"
               % (ca - b_att, cm - (b_micro or 0),
                  net["med"] if net else "assente"))
            rossi += 1
    else:
        ko("⛔ CONTROLLO (c) · il giro `bitmap-hw-coda` non c'e'")
        rossi += 1

    # (a) il fotogramma — ⛔ e sulla strada 2D, l'unica in cui il disegno e'
    #     sincrono: sulla `bitmaprenderer` il controllo NON si puo' costruire
    #     (`[M]` un riscalamento a 3840×2160 lascia la netta a 0,00).
    g, d2 = r("2d-hw-grande"), r("2d-hw")
    a2 = attesa_di(d2)
    if g and g.get("ok") and a2 is not None:
        ga = attesa_di(g)
        gm = g["serie"]["micro"]["med"] if g["serie"].get("micro") else None
        m2 = d2["serie"]["micro"]["med"] if d2["serie"].get("micro") else None
        # ⛔⛔ E IL CRITERIO NON E' «i controlli restano fermi», ed e' un rosso
        #     gia' pagato: sulla strada 2D il disegno e' SINCRONO, quindi i
        #     gemelli stanno A VALLE e salgono per forza insieme a lui — `[M]`
        #     tratto 9 +11,50 e controlli +11,60.  ⇒ Un criterio «i controlli
        #     fermi» sarebbe rosso su un controllo che funziona.
        # ⭐ Il criterio giusto e' l'ATTRIBUZIONE: quanto salgono i gemelli
        #   OLTRE al disegno.  Se il di piu' e' zero, tutto il rincaro e' del
        #   disegno e il banco l'ha messo nel tratto giusto.
        sa_lui, sa_loro = ga - a2, (gm or 0) - (m2 or 0)
        if sa_lui >= 5.0 and abs(sa_loro - sa_lui) < 3.0:
            ok("CONTROLLO (a) · dando lavoro VERO al disegno il tratto 9 sale "
               "di %+.2f ms (%.2f → %.2f) e i gemelli salgono di %+.2f, cioe' "
               "di quel tanto e NON di piu' (%+.2f di residuo) ⇒ il banco "
               "attribuisce il costo del fotogramma al tratto giusto"
               % (sa_lui, a2, ga, sa_loro, sa_loro - sa_lui))
        else:
            ko("⛔ CONTROLLO (a) · tratto 9 %+.2f · gemelli %+.2f · residuo "
               "%+.2f: il controllo del fotogramma e' cieco"
               % (sa_lui, sa_loro, sa_loro - sa_lui))
            rossi += 1
    else:
        ko("⛔ CONTROLLO (a) · il giro `2d-hw-grande` non c'e'")
        rossi += 1

    # (b) il quadro — ⛔⛔ E QUI IL BANCO SI FERMA INVECE DI CONCLUDERE.
    q = r("bitmap-hw-quadro")
    if q and q.get("ok") and b_tot is not None:
        qt, qa = tot_di(q), attesa_di(q)
        quadro = q["palco"].get("quadro_med_ms") or 16.7
        dipinti = q["conti"]["dipinti"]
        consegnati = q["conti"]["consegnati"]
        if dipinti < 0.5 * consegnati:
            dub("⛔ CONTROLLO (b) NON ESEGUIBILE SU QUESTO PALCO: consegnando "
                "il vetro sul quadro si dipingono %d fotogrammi su %d.  `[M]` "
                "il ritmo di `requestAnimationFrame` su questo Xvfb va da 1 a "
                "434 quadri fra un giro e l'altro ⇒ l'ipotesi (b) qui non si "
                "prova NE' si esclude (`STUDI.md` §web §6.2).  ⚠ Si dichiara, "
                "non si conta come verde" % (dipinti, consegnati))
        elif (qt - b_tot) >= 0.5 * quadro and abs(qa - b_att) < 5.0:
            ok("CONTROLLO (b) · consegnando il vetro SUL QUADRO `tot` sale di "
               "%+.2f ms (un quadro e' %.1f) e l'attesa non si muove (%+.2f) ⇒ "
               "il banco sa riconoscere il quadro"
               % (qt - b_tot, quadro, qa - b_att))
        else:
            ko("⛔ CONTROLLO (b) · tot %+.2f · attesa %+.2f: il controllo del "
               "quadro e' cieco" % (qt - b_tot, qa - b_att))
            rossi += 1
    else:
        ko("⛔ CONTROLLO (b) · il giro `bitmap-hw-quadro` non c'e'")
        rossi += 1

    # ── l'ipotesi (a) sul ferro: hardware contro software ─────────────────
    hh, ww = attesa_di(r("2d-h264-hw")), attesa_di(r("2d-h264-sw"))
    if hh is not None and ww is not None:
        print("\n    ⭐ LO STESSO STREAM, DUE DECODIFICATORI (H.264)")
        print("        hardware %7.2f · software %7.2f  ⇒ %+.2f ms"
              % (hh, ww, ww - hh))
    lw = attesa_di(r("2d-h264-sw-letto"))
    if ww is not None and lw is not None:
        print("        e con la lettura del banco, in software: %7.2f (%+.2f)"
              % (lw, lw - ww))

    print("\n    ⇒ rossi: %d" % rossi)
    return 0 if rossi == 0 else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prepara", action="store_true")
    p.add_argument("--giro", action="store_true")
    p.add_argument("--solo", nargs="*", default=None)
    p.add_argument("--lavoro", default="/tmp/08-f3")
    p.add_argument("--porta-http", type=int, default=8873)
    p.add_argument("--schermo", default=":91")
    p.add_argument("--diagnosi", type=int, default=9691)
    p.add_argument("--quanti", type=int, default=400)
    p.add_argument("--ritmo", type=int, default=60)
    p.add_argument("--secondi", type=int, default=10)
    p.add_argument("--salta", action="store_true")
    a = p.parse_args()
    if a.prepara:
        return 0 if prepara(a.lavoro, a.secondi) else 3
    if a.giro:
        return giro(a)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
