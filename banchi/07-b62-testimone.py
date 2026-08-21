#!/usr/bin/env python3
"""07-b62-testimone.py — guida il banco del colore e dà il verdetto.

    python3 banchi/07-b62-prepara.py --dati /tmp/07-b62-dati
    python3 banchi/07-b62-testimone.py --dati /tmp/07-b62-dati

⛔ CHE COSA DEVE DECIDERE, e in che ordine.

`DECISIONI.md` §1.13-ter porta una `[?]`: *«il decodificatore H.264 in hardware
converte con una scala di colore diversa da ffmpeg: +8 livelli sulle zone
chiare»*.  ⚠ Il mandato è **avversariale**: si parte dall'ipotesi che i +8
siano FALSI e si cerca la prova.

Le tre domande, e ciascuna ha la sua leva:

  1. **c'è uno scarto?**  Si confronta quel che il browser legge con la
     FORMULA (`rgb_da_yuv`), non con un'altra misura.  Lo scarto si dice per
     canale (R/G/B) e per livello (ombre / mezzitoni / luci), con un numero.
  2. **su quale strada?**  Lo stesso flusso, gli stessi byte, tre lettori:
     `ffmpeg` (riga di comando), Firefox con la **decodifica in hardware**
     accesa, Firefox con la stessa **spenta**.  ⛔ Una sola variabile per volta.
  3. **di chi è la colpa?**  Lo stesso quadro con la VUI **dichiarata** (come
     fa `src/codificatore.c`) e con la VUI **«non specificato»**.  Se lo scarto
     compare solo quando si tace, è NOSTRO; se compare anche quando si
     dichiara, è del DECODIFICATORE.  ⭐ E il controllo che dimostra che la
     VUI viene letta davvero è la variante `601-dichiarato`: se il browser
     obbedisce lì, allora legge la VUI, e il suo comportamento sul `dichiarato`
     è una scelta e non un'ignoranza.

⛔ E IL BANCO SI CERTIFICA PRIMA DI ESSERE CREDUTO (`PIANO.md` §0.3.4):
   `--certifica` rifà un giro con `?guasto=8`, cioè **innesta esattamente il
   difetto sospettato** — +8 livelli sui soli campioni sopra 180 — e pretende
   di ritrovarlo: +8 nelle luci, 0 nelle ombre.  Se non lo vede, ogni suo verde
   è un verde che non ha guardato.

⚠ LA FINESTRA NON SI APRE SUL DESKTOP DELL'UTENTE.  Firefox gira dentro uno
  schermo virtuale (`Xvfb`) o dentro `cage`: `[M]` `--headless` non prende la
  strada della GPU, e un giro headless misurerebbe il colore di un'altra
  strada.  ⛔ Ed è per questo che il testimone LEGGE il registro di Firefox
  (`MOZ_LOG`) e dichiara quale decodificatore ha davvero lavorato, invece di
  fidarsi del nome dell'interruttore.
"""
import argparse, functools, glob, http.server, json, os, shutil, socketserver
import subprocess, sys, tempfile, threading, time
import importlib.util as _iu

QUI = os.path.dirname(os.path.abspath(__file__))
_spec = _iu.spec_from_file_location("marionette", os.path.join(QUI, "07-b46-marionette.py"))
M = _iu.module_from_spec(_spec)
_spec.loader.exec_module(M)

BANDE = [("sotto il nero", 0, 15), ("ombre", 16, 63), ("mezzitoni bassi", 64, 127),
         ("mezzitoni alti", 128, 191), ("luci", 192, 234), ("sopra il bianco", 235, 255)]
CANALI = ("R", "G", "B")


# ---------------------------------------------------------------------------
# il giudizio — ⛔ sta qui e non nella pagina: si confronta con la formula E con
# ffmpeg nello stesso posto, e un giudizio che cambia non fa riaprire un browser
# ---------------------------------------------------------------------------
def costruisci_attesi(riquadri, atteso_dec):
    """⭐ L'ATTESO DI QUESTA VARIANTE.

    ⛔ Se ci sono i campioni **decodificati** si usano quelli: il codificatore
       non è senza perdite, e la formula applicata ai campioni di PARTENZA
       attribuirebbe al colore uno scarto che è della compressione.  `[M]` con
       x264 a `-qp 4` il piano V si scosta di un livello, che sul rosso vale
       ~1,8 livelli — cioè un quinto della `[?]` che si sta misurando.
    ⚠ Senza (non dovrebbe capitare), si ripiega sui campioni di partenza e LO
      SI DICE nel titolo, invece di dare per buono un atteso più debole."""
    fuori = {}
    for q in riquadri:
        d = (atteso_dec or {}).get(q["nome"])
        if d:
            fuori[q["nome"]] = dict(d, Y=d["yuv"][0], U=d["yuv"][1], V=d["yuv"][2])
        else:
            fuori[q["nome"]] = {"709tv": q["rgb_709tv"], "601tv": q["rgb_601tv"],
                                "709pc": q["rgb_709pc"], "yuv": [q["Y"], q["U"], q["V"]],
                                "Y": q["Y"], "U": q["U"], "V": q["V"]}
    return fuori


def al_fondoscala(v):
    """⛔⭐ UN CANALE APPOGGIATO A 0 O A 255 NON SI GIUDICA, e il motivo è un
    difetto che questo banco ha avuto addosso.

    `[M]` 21 agosto 2026: sulle barre 100 % il banco segnava fino a **12
    livelli** sul blu del giallo e sul blu del magenta — cioè proprio i canali
    il cui valore atteso è **tagliato**.  La causa non era il decodificatore:
    il taglio non è lineare, quindi `media(taglia(x))` non è `taglia(media(x))`,
    e un pizzico di rumore attorno allo zero si raddrizza tutto verso l'alto.
    ⇒ Un difetto del METRO travestito da difetto della strada, e sarebbe
    finito nel rapporto come «il decodificatore sbaglia di 12».
    ⚠ Si toglie dal giudizio e si CONTA, invece di sparire in silenzio."""
    return v <= 0.5 or v >= 254.5


def scarti(medie, attesi, ipotesi="709tv", prefissi=None):
    """[(nome, canale, atteso, letto, scarto)] — scarto = letto − atteso.
    ⛔ Salta i canali al fondoscala: vedi `al_fondoscala`."""
    out, saltati = [], 0
    for nome, a in attesi.items():
        if prefissi and not any(nome.startswith(p) for p in prefissi):
            continue
        m = medie.get(nome)
        if not m:
            continue
        for k in range(3):
            if al_fondoscala(a[ipotesi][k]):
                saltati += 1
                continue
            out.append((nome, CANALI[k], a[ipotesi][k], m[k], m[k] - a[ipotesi][k]))
    return out, saltati


def aderenza(medie, attesi, prefissi):
    """Quale ipotesi di colore spiega quel che si è letto.  ⭐ È la domanda
    «matrice o intervallo?» ridotta a tre numeri confrontabili."""
    fuori = {}
    for ip in ("709tv", "601tv", "709pc"):
        s, saltati = scarti(medie, attesi, ip, prefissi)
        if not s:
            return {}
        fuori[ip] = {"medio": sum(abs(x[4]) for x in s) / len(s),
                     "peggio": max(abs(x[4]) for x in s),
                     "n": len(s), "saltati": saltati}
    return fuori


def per_livello(medie, riquadri, attesi):
    """Lo scarto sulla rampa di grigio, ⛔ per canale e per banda di livello —
    che è la forma in cui la `[?]` è scritta («+8 sulle zone chiare»)."""
    righe = []
    for nome, lo, hi in BANDE:
        dentro = [q for q in riquadri
                  if q["nome"].startswith("rampa-Y") and lo <= q["Y"] <= hi]
        voce = {"banda": nome, "da": lo, "a": hi, "riquadri": len(dentro)}
        for k, can in enumerate(CANALI):
            v = [medie[q["nome"]][k] - attesi[q["nome"]]["709tv"][k]
                 for q in dentro if q["nome"] in medie]
            if not v:
                continue
            voce[can] = {"medio": sum(v) / len(v), "peggio": max(v, key=abs)}
        righe.append(voce)
    return righe


def retta(medie, riquadri, attesi):
    """⭐ Guadagno e scostamento della rampa, sui livelli DENTRO l'intervallo
    legale (16-235).  ⚠ Distingue le due malattie che una media confonde: un
    intervallo sbagliato è un GUADAGNO diverso da 1; una matrice sbagliata sul
    grigio non si vede affatto (U=V=128 dà lo stesso RGB con 601 e con 709)."""
    x, y = [], []
    for q in riquadri:
        if not q["nome"].startswith("rampa-Y") or not (16 <= q["Y"] <= 235):
            continue
        m = medie.get(q["nome"])
        if not m:
            continue
        x.append(attesi[q["nome"]]["709tv"][0])
        y.append(sum(m) / 3.0)
    if len(x) < 10:
        return None
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    g = sxy / sxx
    return {"guadagno": g, "scostamento": my - g * mx, "punti": n}


def stampa_giudizio(titolo, medie, riquadri, attesi):
    print("\n──── %s" % titolo)
    ad = aderenza(medie, attesi, ("barra100", "barra75"))
    if ad:
        u = list(ad.values())[0]
        print("  quale conversione spiega le BARRE (%d canali giudicati, "
              "%d saltati perché al fondoscala):" % (u["n"], u["saltati"]))
        for ip, v in sorted(ad.items(), key=lambda t: t[1]["medio"]):
            print("     %-8s scarto medio %6.2f · peggiore %6.2f" % (ip, v["medio"], v["peggio"]))
    r = retta(medie, riquadri, attesi)
    if r:
        print("  la rampa di grigio (Y 16-235, %d livelli): guadagno %.4f · scostamento %+.2f"
              % (r["punti"], r["guadagno"], r["scostamento"]))
    print("  lo scarto per livello e per canale (letto − formula BT.709 limitata):")
    print("     %-26s %4s   %15s %15s %15s"
          % ("banda", "n", "R medio/peggio", "G medio/peggio", "B medio/peggio"))
    for v in per_livello(medie, riquadri, attesi):
        c = "".join("  %+6.2f/%+6.2f" % (v[k]["medio"], v[k]["peggio"])
                    if k in v else "         —     " for k in CANALI)
        print("     %-26s %4d %s" % ("%s (%d-%d)" % (v["banda"], v["da"], v["a"]),
                                     v["riquadri"], c))
    print("  i valori limite (Y del sorgente, U=V=128) — atteso / letto, per canale:")
    for q in riquadri:
        if not q["nome"].startswith("limite"):
            continue
        m, a = medie.get(q["nome"]), attesi[q["nome"]]
        if m:
            print("     Y=%3d (decodificato %6.2f)  atteso %6.1f %6.1f %6.1f  "
                  "letto %6.1f %6.1f %6.1f  scarto %+6.2f %+6.2f %+6.2f"
                  % (q["Y"], a["Y"], *a["709tv"], *m,
                     *[m[k] - a["709tv"][k] for k in range(3)]))
    print("  le barre 100 %% — scarto per canale contro BT.709 e contro BT.601:")
    for q in riquadri:
        if not q["nome"].startswith("barra100"):
            continue
        m, a = medie.get(q["nome"]), attesi[q["nome"]]
        if not m:
            continue
        # ⚠ Un canale al fondoscala si scrive «·» invece di un numero: il suo
        #   scarto è quello del taglio, non della conversione (`al_fondoscala`).
        def cella(atteso, letto):
            return "     ·" if al_fondoscala(atteso) else "%+6.1f" % (letto - atteso)
        print("     %-10s 709: %s %s %s    601: %s %s %s"
              % (q["nome"].split("-", 1)[1],
                 *[cella(a["709tv"][k], m[k]) for k in range(3)],
                 *[cella(a["601tv"][k], m[k]) for k in range(3)]))


# ---------------------------------------------------------------------------
# il servitore dei dati
# ---------------------------------------------------------------------------
def servi(cartella, porta):
    gest = functools.partial(http.server.SimpleHTTPRequestHandler, directory=cartella)
    gest.log_message = lambda *a, **k: None
    # ⛔ `allow_reuse_address` si mette sulla CLASSE: sull'istanza arriva dopo
    #    `server_bind()`, cioè troppo tardi, e il banco muore con «Address
    #    already in use» ogni volta che il giro precedente è stato interrotto.
    class Servitore(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True
    s = Servitore(("127.0.0.1", porta), gest)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


# ---------------------------------------------------------------------------
# lo schermo virtuale — ⛔ e NON il desktop dell'utente
# ---------------------------------------------------------------------------
def accendi_xvfb(numero, misura="1600x1000x24"):
    p = subprocess.Popen(["Xvfb", ":%d" % numero, "-screen", "0", misura, "-nolisten", "tcp"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if os.path.exists("/tmp/.X11-unix/X%d" % numero):
            return p
        time.sleep(0.25)
    p.kill()
    raise RuntimeError("Xvfb :%d non è partito" % numero)


def accendi_cage(nodo="/dev/dri/renderD128"):
    """⛔⭐ SERVE `cage`, E NON È UN VEZZO — `[M]` 21 agosto 2026.

    Su `Xvfb` Firefox mette la decodifica in hardware nella lista nera da sé:
    `about:support` dice `HARDWARE_VIDEO_DECODING · runtime unavailable · Force
    disabled by gfxInfo · FEATURE_FAILURE_VIDEO_DECODING_TEST_FAILED`, e il
    registro `IsHardwareAccelerated=0` a ogni fotogramma.  La causa è che la
    sua sonda (`/usr/lib/firefox-esr/vaapitest`) non trova nessun nodo DRM
    dietro uno schermo X finto — ⭐ e infatti chiamata **col nodo per nome**
    risponde `VAAPI_SUPPORTED TRUE`, `VAAPI_HWCODECS 368`.
    ⇒ Senza un compositore vero sul ferro vero, la strada «hardware» È la
      strada software, e il banco confronterebbe una cosa con se stessa.

    `cage` con la spalla `headless` di wlroots apre un Wayland vero sul nodo di
    rendering: `[M]` lì il registro dice `VA-API FFmpeg init successful` e
    `IsHardwareAccelerated=1`.

    ⛔⛔ E NON APRE NIENTE SUL DESKTOP DELL'UTENTE: se il socket che esce fosse
        `wayland-0` — il suo — il banco si RIFIUTA di partire."""
    # ⛔ Prima si porta via quel che è rimasto in piedi da un giro interrotto:
    #    `[M]` due `cage` orfani (il `finally` non gira se il banco viene
    #    ucciso dal tempo) tenevano i socket `wayland-1` e `wayland-2`, e il
    #    Firefox del giro nuovo è morto subito lasciando il banco appeso.
    #    ⚠ Si uccidono solo i `cage` che portano LA NOSTRA marca, non tutti.
    for vecchia in glob.glob("/tmp/remotix-cage-*"):
        subprocess.run(["pkill", "-9", "-f", "cage -- bash -c echo .*%s" % vecchia],
                       capture_output=True)
        shutil.rmtree(vecchia, ignore_errors=True)
    marca = tempfile.mkdtemp(prefix="remotix-cage-")
    dove = os.path.join(marca, "display")
    amb = dict(os.environ, WLR_BACKENDS="headless", WLR_LIBINPUT_NO_DEVICES="1",
               WLR_RENDER_DRM_DEVICE=nodo)
    amb.pop("WAYLAND_DISPLAY", None)
    p = subprocess.Popen(["cage", "--", "bash", "-c",
                          "echo $WAYLAND_DISPLAY > %s; exec sleep 100000" % dove],
                         env=amb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    disp = ""
    for _ in range(80):
        try:
            disp = open(dove).read().strip()
        except OSError:
            disp = ""
        if disp:
            break
        time.sleep(0.25)
    if not disp:
        p.kill()
        raise RuntimeError("cage non ha aperto nessun socket Wayland")
    if disp == os.environ.get("WAYLAND_DISPLAY"):
        p.kill()
        raise RuntimeError("⛔ cage ha preso «%s», che è la sessione di chi sta "
                           "davanti alla macchina: NON ci apro un browser" % disp)
    return p, disp, marca


PREFS_COMUNI = {
    # ⛔ WebCodecs va comunque, ma il registro serve a DIRE chi ha decodificato
    "media.ffvpx.enabled": True,
    "browser.cache.disk.enable": False,
}
PREFS_HW = {
    "media.ffmpeg.vaapi.enabled": True,
    "media.hardware-video-decoding.enabled": True,
    # ⛔ Senza `force-enabled` Firefox spegne la VA-API quando WebRender è in
    #    software — e su uno schermo virtuale WebRender è SEMPRE in software.
    #    ⇒ Senza questa riga il giro «hardware» misurerebbe il software, e il
    #    banco direbbe «nessuna differenza» avendo provato due volte la stessa
    #    cosa.  È la forma di difetto che LEZIONI §1.9 chiama la più cara.
    "media.hardware-video-decoding.force-enabled": True,
    # ⛔ E NON BASTANO: `[M]` 21 agosto 2026, col solo `force-enabled` il
    #    registro diceva `IsHardwareAccelerated=0` e zero tracce VA-API.  La
    #    VA-API di Firefox vive nel processo RDD, che è in gabbia e non arriva
    #    a `/dev/dri`; e vuole DMABUF, che su X11 passa da EGL.
    "media.rdd-ffmpeg.enabled": True,
    "media.rdd-process.enabled": True,
    "widget.dmabuf.force-enabled": True,
    "gfx.x11-egl.force-enabled": True,
}
PREFS_SW = {
    "media.ffmpeg.vaapi.enabled": False,
    "media.hardware-video-decoding.enabled": False,
    "media.hardware-video-decoding.force-enabled": False,
    "widget.dmabuf.force-enabled": False,
}
# ⛔ La gabbia del processo RDD gli toglie `/dev/dri`: senza questa variabile
#    la VA-API non si apre e Firefox ripiega in software SENZA dirlo alla
#    pagina.  ⚠ È una variabile del BANCO: nessun Firefox di utente parte così,
#    e la misura che ne esce va letta come «che cosa fa il decodificatore in
#    hardware», non come «che cosa fa il Firefox dell'utente».
AMBIENTE_HW = {"MOZ_DISABLE_RDD_SANDBOX": "1", "LIBVA_DRIVER_NAME": "iHD"}


def chi_ha_decodificato(percorso):
    """⛔⭐ SI LEGGE IL REGISTRO DI FIREFOX INVECE DI FIDARSI DELL'INTERRUTTORE.

    Un interruttore chiamato «hardware» dice che cosa si è CHIESTO, non che
    cosa è successo: se Firefox ripiega in software senza dirlo, il banco
    confronterebbe due volte la stessa strada e chiamerebbe «nessuna
    differenza» il fatto di non aver cambiato niente."""
    testo = ""
    cartella = os.path.dirname(percorso)
    nome = os.path.basename(percorso)
    try:
        for f in sorted(os.listdir(cartella)):
            if f.startswith(nome):
                testo += open(os.path.join(cartella, f), errors="replace").read()
    except OSError:
        pass
    basso = testo.lower()
    righe = [r.strip() for r in testo.splitlines()
             if ("va-api" in r.lower() or "vaapi" in r.lower()
                 or "Created decoder" in r or "Creating decoder" in r
                 or "FFmpegVideoDecoder" in r)]
    return {"tracce_vaapi": basso.count("va-api") + basso.count("vaapi"),
            "righe": righe[:10], "byte_registro": len(testo)}


# ---------------------------------------------------------------------------
def verdetto(medie, riquadri, attesi, soglia=2.0):
    """⛔⭐ IL VERDETTO ESPLICITO, CON I DUE ESTREMI E COL DENOMINATORE.

    Non basta una tabella: una tabella la si legge come si vuole.  E non basta
    un limite superiore — ⚠ un banco che chiede solo «non più di X» dà verde
    anche quando NON HA GUARDATO NIENTE.  ⇒ qui si dichiarano tre cose insieme:
    quanti riquadri sono stati giudicati (**il denominatore**), quanti canali,
    e lo scarto peggiore contro la formula.  Un denominatore troppo piccolo è
    esso stesso un rosso."""
    s, saltati = scarti(medie, attesi, "709tv", None)
    if not s:
        return {"esito": "⛔ NIENTE GIUDICATO", "n": 0}
    peggio = max(abs(x[4]) for x in s)
    medio = sum(abs(x[4]) for x in s) / len(s)
    nomi = {x[0] for x in s}
    # ⛔ IL DENOMINATORE HA DUE PARTI, ed è la trappola 1 di `CODER.md`: quanti
    #    canali sono stati giudicati sul totale giudicabile (cioè al netto di
    #    quelli al fondoscala) E quanti riquadri hanno portato almeno un canale.
    #    ⚠ Un riquadro tutto tagliato — il bianco, il nero — non ha niente da
    #      dire, e pretendere che ci sia falserebbe il conto.
    atteso_n = len(riquadri) * 3 - saltati
    con_qualcosa = sum(1 for q in riquadri
                       if any(not al_fondoscala(attesi[q["nome"]]["709tv"][k])
                              for k in range(3)))
    abbastanza = len(s) >= atteso_n and len(nomi) >= con_qualcosa
    dentro = peggio <= soglia
    return {"riquadri": len(nomi), "riquadri_giudicabili": con_qualcosa,
            "canali": len(s), "saltati_fondoscala": saltati,
            "canali_attesi": atteso_n, "medio": medio, "peggio": peggio,
            "soglia": soglia, "denominatore_pieno": abbastanza,
            "esito": ("⭐ NESSUNO SCARTO OLTRE %.1f LIVELLI (peggiore %.2f)" % (soglia, peggio))
            if (dentro and abbastanza)
            else ("⛔ SCARTO fino a %.2f livelli" % peggio) if abbastanza
            else "⛔ DENOMINATORE INCOMPLETO: %d canali su %d, %d riquadri su %d "
                 "— il verde non vale" % (len(s), atteso_n, len(nomi), con_qualcosa)}


def certifica(m, base, variante, hw, attesa, riquadri, attesi, sano, esiti, strada):
    """⛔ IL BANCO SI CERTIFICA PRIMA DI ESSERE CREDUTO — e con DUE guasti, non
    uno, perché i due numeri che questo banco pronuncia sono due:

      1. **+8 livelli sulle sole luci** — è la `[?]` di §1.13-ter alla lettera.
         Deve comparire nella banda «luci» e NON nelle «ombre»: un banco che lo
         vedesse dappertutto starebbe misurando qualcos'altro.
      2. ⭐ **un guadagno di 1,05** — è la forma che ha un intervallo sbagliato.
         Serve a certificare il DISCRIMINATORE «matrice o intervallo?»: senza,
         la riga «guadagno» del giudizio non è mai stata messa alla prova, e
         sarebbe una riga creduta invece che provata.

    ⚠ E il terzo controllo non è innestato, è VERO: la variante
      `601-dichiarato` cambia la matrice **nel flusso**, e il giudizio deve
      passare da «709tv spiega tutto» a «601tv spiega tutto» da sé."""
    out = {}
    print("\n════ CERTIFICAZIONE del banco (%s · %s)" % (strada, variante))

    def leggi(r):
        return "copyto" if r.get("copyto") else ("tela" if r.get("tela") else None)

    # --- 1 · +8 sulle sole luci ---------------------------------------------
    r = un_giro(m, base, variante, hw, attesa, guasto=8)
    esiti["%s/%s/guasto8" % (strada, variante)] = r
    punto = leggi(r)
    if not punto:
        print("  ⛔ guasto «+8 sulle luci»: nessuna lettura — non eseguibile")
        out["piu8"] = None
    else:
        liv = per_livello(r[punto], riquadri, attesi)
        luci = [x for x in liv if x["banda"] == "luci"][0]["R"]["medio"]
        ombre = [x for x in liv if x["banda"] == "ombre"][0]["R"]["medio"]
        b_luci = b_ombre = 0.0
        if sano.get(punto):
            bl = per_livello(sano[punto], riquadri, attesi)
            b_luci = [x for x in bl if x["banda"] == "luci"][0]["R"]["medio"]
            b_ombre = [x for x in bl if x["banda"] == "ombre"][0]["R"]["medio"]
        d_luci, d_ombre = luci - b_luci, ombre - b_ombre
        # ⛔ DUE ESTREMI, non uno: il guasto dev'essere abbastanza grande da
        #    vedersi E abbastanza piccolo da non essere qualcos'altro; e dove
        #    NON è stato messo il banco deve restare fermo.
        ok = 6.0 <= d_luci <= 9.0 and abs(d_ombre) <= 1.0
        print("  guasto «+8 livelli sopra 180»  luci %+6.2f (era %+6.2f) ⇒ %+6.2f "
              "· ombre %+6.2f (era %+6.2f) ⇒ %+6.2f  ⇒ %s"
              % (luci, b_luci, d_luci, ombre, b_ombre, d_ombre,
                 "⭐ VISTO, e solo dove è stato messo" if ok
                 else "⛔ NON VISTO come atteso — BANCO CIECO"))
        out["piu8"] = {"delta_luci": d_luci, "delta_ombre": d_ombre, "ok": ok}

    # --- 2 · un guadagno del 5 % --------------------------------------------
    r = un_giro(m, base, variante, hw, attesa, guadagno=1.05)
    esiti["%s/%s/guadagno105" % (strada, variante)] = r
    punto = leggi(r)
    if not punto:
        print("  ⛔ guasto «guadagno 1,05»: nessuna lettura — non eseguibile")
        out["guadagno"] = None
    else:
        g = retta(r[punto], riquadri, attesi)
        gb = retta(sano[punto], riquadri, attesi) if sano.get(punto) else None
        base_g = gb["guadagno"] if gb else 1.0
        ok = g and 1.03 <= g["guadagno"] / base_g <= 1.07
        print("  guasto «guadagno 1,05»          guadagno letto %.4f (era %.4f) "
              "⇒ rapporto %.4f  ⇒ %s"
              % (g["guadagno"], base_g, g["guadagno"] / base_g,
                 "⭐ VISTO: il discriminatore dell'INTERVALLO funziona" if ok
                 else "⛔ NON VISTO — il banco non saprebbe accorgersi di un "
                      "intervallo sbagliato"))
        out["guadagno"] = {"letto": g["guadagno"], "base": base_g, "ok": bool(ok)}
    return out


def un_giro(m, base, variante, hw, attesa, guasto=0, guadagno=1, lettura="entrambi"):
    url = "%s?variante=%s&hw=%s&guasto=%s&guadagno=%s&lettura=%s" % (
        base, variante, hw, guasto, guadagno, lettura)
    m.vai(url)
    scaduto = time.time() + attesa
    while time.time() < scaduto:
        r = m.js("return window.RISULTATO || null;")["value"]
        if r:
            # ⛔⛔ SI CONTROLLA CHE LA PAGINA SERVITA SIA QUELLA DI ADESSO, e
            #     questa riga è nata da un giro sprecato: la pagina viveva in
            #     una COPIA accanto ai dati, e dopo averla modificata il banco
            #     ha continuato a servire quella vecchia.  Il guasto «guadagno»
            #     non veniva applicato, e la certificazione diceva «⛔ NON
            #     VISTO» ⇒ il banco accusava se stesso di essere cieco quando
            #     era il servitore a essere stantio.  ⚠ Un rosso non spiegato
            #     costa quanto un verde non guardato.
            if "guadagno" not in r:
                return {"errore": "⛔ la pagina servita è VECCHIA (non conosce "
                                  "«guadagno»): ricopiala accanto ai dati",
                        "variante": variante, "hw": hw}
            return r
        time.sleep(0.5)
    try:
        st = m.js("return document.getElementById('stato').textContent")["value"]
    except Exception as e:
        st = "(non leggibile: %s)" % e
    return {"errore": "scaduto dopo %d s" % attesa, "stato": st, "variante": variante, "hw": hw}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dati", default="/tmp/07-b62-dati")
    a.add_argument("--porta", type=int, default=8062)
    a.add_argument("--marionette", type=int, default=2862)
    a.add_argument("--schermo", type=int, default=62, help="numero dello Xvfb")
    a.add_argument("--vetrina", default="cage", choices=("cage", "xvfb"),
                   help="⛔ su xvfb la strada «hardware» NON è l'hardware")
    a.add_argument("--nodo", default="/dev/dri/renderD128")
    a.add_argument("--varianti", default="")
    a.add_argument("--strade", default="hardware,software")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--attesa", type=int, default=120)
    a.add_argument("--esiti", default="")
    o = a.parse_args()

    ver = json.load(open(os.path.join(o.dati, "verita.json")))
    rif = json.load(open(os.path.join(o.dati, "riferimento.json")))
    riquadri = ver["riquadri"]
    varianti = [v for v in (o.varianti.split(",") if o.varianti else ver["varianti"]) if v]

    print("⭐ carico: %s" % (open("/proc/loadavg").read().split()[0]))
    print("⛔ il ferro: Intel UHD (iGPU) — le misure di tempo qui NON si dichiarano,"
          " questo banco misura COLORE, che dal carico non dipende")

    attesi = {v: costruisci_attesi(
        riquadri, (rif.get(v) or {}).get("atteso_dai_campioni_decodificati"))
        for v in varianti}

    # --- 0 · quel che ffmpeg legge dagli stessi byte ------------------------
    print("\n════ IL RIFERIMENTO — `ffmpeg`, sulla riga di comando, sugli STESSI byte")
    for v in varianti:
        r = rif.get(v)
        if not r or not r["ffmpeg_rgb"]:
            print("  ⛔ %-24s niente" % v)
            continue
        print("  %-24s ffprobe: %s / %s" % (v, r["ffprobe"].get("color_space", "—"),
                                            r["ffprobe"].get("color_range", "—")))
        stampa_giudizio("ffmpeg (come lo si chiama) · " + v,
                        r["ffmpeg_rgb"], riquadri, attesi[v])
        if r.get("ffmpeg_rgb_709_chiesta"):
            stampa_giudizio("ffmpeg CHIEDENDO bt709/tv · " + v,
                            r["ffmpeg_rgb_709_chiesta"], riquadri, attesi[v])

    # --- 1 · il browser -----------------------------------------------------
    strade = [x for x in o.strade.split(",") if x]
    esiti = {}
    if not strade:
        print("\n⚠ nessuna strada del browser chiesta (`--strade ''`): "
              "questo giro ha guardato SOLO `ffmpeg`, e non dice niente del browser.")
        return 0
    # ⛔ La pagina si RICOPIA a ogni giro: la copia accanto ai dati è quella
    #    che il browser vede, e una copia stantia è un banco che misura il
    #    codice di ieri.  È la forma D5 di `LEZIONI.md`, applicata all'HTML.
    shutil.copy(os.path.join(QUI, "07-b62-colore.html"),
                os.path.join(o.dati, "index.html"))
    s = servi(o.dati, o.porta)
    base = "http://127.0.0.1:%d/" % o.porta
    schermo = xvfb = cage = disp = marca = None
    if o.vetrina == "cage":
        cage, disp, marca = accendi_cage(o.nodo)
        print("\n⭐ compositore: `cage` headless sul nodo %s, socket «%s» "
              "(NON la sessione di chi sta davanti alla macchina)" % (o.nodo, disp))
    else:
        xvfb = accendi_xvfb(o.schermo)
        schermo = ":%d" % o.schermo
        print("\n⚠ compositore: Xvfb :%d — ⛔ qui Firefox mette la decodifica in "
              "hardware nella lista nera da sé: la strada «hardware» NON sarà "
              "l'hardware, e il banco lo dirà." % o.schermo)
    try:
        for strada in strade:
            prefs = dict(PREFS_COMUNI)
            prefs.update(PREFS_HW if strada == "hardware" else PREFS_SW)
            # ⛔ Il registro si prepara PRIMA di accendere il browser: se
            #    `MOZ_LOG_FILE` si scrive dopo, il processo è già partito e non
            #    lo vede — ⚠ e il banco riporterebbe «zero tracce VA-API»
            #    credendo di aver misurato, che è la forma peggiore di zero.
            reg_dir = tempfile.mkdtemp(prefix="remotix-mozlog-")
            reg_file = os.path.join(reg_dir, "moz.log")
            os.environ["MOZ_LOG"] = "PlatformDecoderModule:5,FFmpegVideo:5,MediaDecoder:4"
            os.environ["MOZ_LOG_FILE"] = reg_file
            for k, v in AMBIENTE_HW.items():
                if strada == "hardware":
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
            if disp:
                # ⛔ Il socket di `cage`, non quello dell'utente.  ⚠ E si toglie
                #    `DISPLAY`: con tutt'e due Firefox può scegliere X11 e
                #    finire su uno schermo che non è quello che abbiamo aperto.
                os.environ["WAYLAND_DISPLAY"] = disp
                os.environ["MOZ_ENABLE_WAYLAND"] = "1"
                os.environ.pop("DISPLAY", None)
            p = m = profilo = None
            try:
                p, m, profilo = M.accendi(profilo_prefs=prefs, headless=False,
                                          porta=o.marionette, largo=1500, alto=950,
                                          schermo=schermo)
                m.sessione()
                print("\n════ IL BROWSER — strada «%s» (%s)"
                      % (strada, ("cage «%s»" % disp) if disp else ("Xvfb %s" % schermo)))
                for v in varianti:
                    r = un_giro(m, base, v, "prefer-hardware" if strada == "hardware"
                                else "prefer-software", o.attesa)
                    esiti["%s/%s" % (strada, v)] = r
                    if r.get("errore"):
                        print("  ⛔ %-24s %s" % (v, r["errore"]))
                        continue
                    print("  %-24s formato «%s» · %d/%d fotogrammi · errori %d%s"
                          % (v, r["formato_fotogramma"], r["fotogrammi_usciti"],
                             r["fotogrammi_dati"], r["errori"],
                             (" · " + r["nota_copyto"]) if r.get("nota_copyto") else ""))
                    for punto in ("copyto", "tela"):
                        if r.get(punto):
                            stampa_giudizio("%s · %s · %s" % (strada, v, punto),
                                            r[punto], riquadri, attesi[v])
                            g = verdetto(r[punto], riquadri, attesi[v])
                            print("  ⇒ VERDETTO: %s  (%d riquadri, %d canali su %d "
                                  "attesi, %d al fondoscala; medio %.2f)"
                                  % (g["esito"], g.get("riquadri", 0), g.get("canali", 0),
                                     g.get("canali_attesi", 0), g.get("saltati_fondoscala", 0),
                                     g.get("medio", 0)))
                            esiti["%s/%s/%s/verdetto" % (strada, v, punto)] = g
                if o.certifica:
                    v = varianti[0]
                    hw = "prefer-hardware" if strada == "hardware" else "prefer-software"
                    sano = esiti.get("%s/%s" % (strada, v), {})
                    esiti.setdefault("certificazioni", {})[strada] = certifica(
                        m, base, v, hw, o.attesa, riquadri, attesi[v], sano, esiti, strada)
                reg = chi_ha_decodificato(reg_file)
                print("\n  ⚠ chi ha decodificato davvero (dal registro di Firefox): "
                      "tracce VA-API %d su %d byte" % (reg["tracce_vaapi"], reg["byte_registro"]))
                for r_ in reg["righe"]:
                    print("      %s" % r_[:160])
                acc = [r_ for r_ in reg["righe"] if "IsHardwareAccelerated=1" in r_]
                if strada == "hardware" and not acc:
                    print("  ⛔⛔ QUESTA NON È LA STRADA DELL'HARDWARE: il registro non porta "
                          "nemmeno un `IsHardwareAccelerated=1`.\n"
                          "      ⇒ Le righe qui sopra dicono che cosa fa il decodificatore "
                          "SOFTWARE, e la `[?]` dei «+8 livelli» resta aperta.")
                esiti["%s/registro" % strada] = reg
                esiti["%s/hardware_davvero" % strada] = bool(acc)
            finally:
                if p:
                    M.spegni(p, profilo)
                shutil.rmtree(reg_dir, ignore_errors=True)
    finally:
        if xvfb:
            xvfb.terminate()
        if cage:
            # ⛔ `terminate()` non basta: `[M]` cage sopravvive al SIGTERM
            #    finché il suo figlio (`sleep`) è vivo, e resta in piedi a
            #    tenersi il socket.  ⚠ Un compositore orfano fa morire il
            #    Firefox del giro dopo — e il banco resta appeso senza dire
            #    perché.
            cage.kill()
            try:
                cage.wait(10)
            except Exception:
                pass
            shutil.rmtree(marca, ignore_errors=True)
        s.shutdown()

    dove = o.esiti or os.path.join(o.dati, "07-b62-esiti.json")
    json.dump(esiti, open(dove, "w"), indent=1)
    print("\nesiti in %s" % dove)
    return 0


if __name__ == "__main__":
    sys.exit(main())
