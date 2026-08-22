#!/usr/bin/env python3
"""07-b66-dentro.py — L'ULTIMO ANELLO DEL COLORE: quello DENTRO la sessione.

    python3 banchi/07-b66-dentro.py costruisci        compila la vetrina (nel contenitore)
    python3 banchi/07-b66-dentro.py giro [opzioni]    un giro di misura
    python3 banchi/07-b66-dentro.py certifica         i quattro giri di controllo
    python3 banchi/07-b66-dentro.py pulisci           spegne vetrina ed effetti

⛔ LA DOMANDA, IN UNA RIGA: **quel che c'e' sullo schermo della sessione e quel
   che noi catturiamo sono gli stessi pixel?**

Il 21 agosto 2026 il colore e' stato misurato **dal flusso al vetro** (banco
`07-b62`): sul decodificatore H.264 in hardware lo scarto peggiore su 847 canali
e' 0,51 livelli, e la conversione nostra da' 0,000.  ⭐ Ma chi l'ha misurato ha
dichiarato per primo quel che non aveva fatto:

    «ho misurato dal flusso al vetro, non dal desktop al vetro.  Resta aperto se
     la cattura di Mutter veda i pixel prima o dopo un profilo di colore del
     compositore (o Night Light).»

⇒ Questo banco chiude quell'anello, e lo fa in tre punti invece che in uno:

  1. ⭐⭐ **DIPINTO → CATTURATO**, e qui il confronto e' **byte per byte**.
     La vetrina (`07-b66-vetrina.c`) scrive pixel esatti in un `wl_shm`
     XRGB8888; il prodotto, al `SIGUSR1`, mette su disco `scatto-ingresso.bgrx`
     — *«i pixel che il codificatore HA IN MANO»* (`figlio.c:3861`).
     ⭐ E i due formati sono **lo stesso ordine di byte** (B,G,R,X): l'atteso
        non e' una formula, e' il file che abbiamo scritto.  ⇒ o sono identici,
        o non lo sono, e non c'e' spazio per l'interpretazione.
  2. **DIPINTO → FLUSSO**: `scatto-flusso.obu`, cioe' i byte che il prodotto
     **spedisce davvero**, riletti da `ffmpeg`.  ⇒ ci aggiunge la conversione
     BGRx→YUV del prodotto e il codificatore veri (QP 26, VAAPI), che `07-b62`
     aveva rifatto con `ffmpeg` invece di misurarli in opera.
  3. **DIPINTO → VETRO** (`--vetro`): la tela del browser, dallo stesso istante.

⛔⛔ E LO SCARTO COMUNE NON SI SOTTRAE.  Un difetto di colore *e'* uniforme:
    `mediana(letto − atteso)` lo cancella, ed e' l'errore che ha fabbricato il
    «+8» smentito il 21 agosto (`DECISIONI.md` §1.13-ter).  Qui si stampano
    medio e peggiore **assoluti**, per canale e per banda di livello.

⛔ I TRE GUASTI DELLA CERTIFICAZIONE — e i primi due non sono simulazioni:

    a. `--guasto N` — l'immagine **dipinta** e' spostata di +N livelli sopra una
       soglia, ma il confronto resta contro quella **pulita** ⇒ il banco deve
       accusare +N nelle luci e **0 nelle ombre**.  E' il difetto «una
       trasformazione fra il desktop e noi», messo dove si sa.
    b. `--effetto lente` — una trasformazione di colore **VERA del compositore**
       (l'ingranditore di GNOME a 1x con `invert-lightness`).  ⭐ E' il controllo
       che vale piu' di tutti: se il banco la vede, allora **vedrebbe anche un
       profilo di colore applicato in composizione**, e un «nessuna differenza»
       su Night Light diventa una risposta invece di una cecita'.
    c. `--effetto nottelunga` — Night Light acceso al massimo (1700 K).  ⚠ Qui
       NON si sa in anticipo la risposta: e' la misura.

⚠ IL CARICO SI DICHIARA ACCANTO A OGNI NUMERO (otto agenti sulla macchina),
  ⛔ anche se il colore dal carico non dipende.
"""
import argparse, base64, importlib.util as iu, json, os, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
_s = iu.spec_from_file_location("p62", os.path.join(QUI, "07-b62-prepara.py"))
P62 = iu.module_from_spec(_s); _s.loader.exec_module(P62)
_s = iu.spec_from_file_location("mario", os.path.join(QUI, "07-b46-marionette.py"))
M = iu.module_from_spec(_s); _s.loader.exec_module(M)
# ⛔ Da `07-b62-testimone.py` si PRENDONO `cage`, le preferenze della strada
#    hardware e il lettore del registro di Firefox: sono la parte che gli e'
#    costata due giri, e riscriverla vorrebbe dire ripagarli (`CODER.md` §4.1).
_s = iu.spec_from_file_location("t62", os.path.join(QUI, "07-b62-testimone.py"))
T62 = iu.module_from_spec(_s); _s.loader.exec_module(T62)

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA = os.environ.get("PAROLA_SUDO", "nicfio")
PORTA = int(os.environ.get("PORTA", "7771"))
UID_B = int(os.environ.get("UID_B", "1017"))
UTENTE = os.environ.get("UTENTE", "provav7")
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "provav7-2026")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-c8")
FUORI = os.environ.get("FUORI", "/tmp/07-b66")
# ⛔ La fascia di servizio: le ultime righe del quadro NON sono scena.  Ci sta
#    dentro il battito della vetrina, e nessun riquadro misurato la tocca.
FASCIA = 72
LATO_BATTITO = 64
CANALI = ("R", "G", "B")
BANDE = [("sotto il nero", 0, 15), ("ombre", 16, 63), ("mezzitoni bassi", 64, 127),
         ("mezzitoni alti", 128, 191), ("luci", 192, 234), ("sopra il bianco", 235, 255)]


# ---------------------------------------------------------------------------
# la macchina di prova
# ---------------------------------------------------------------------------
def remoto(comando, binario=False):
    """⛔ Il copione si spedisce come FILE: `printf … | sudo -S bash -s` da' a
    bash uno stdin gia' consumato dalla parola d'ordine — la trappola pagata in
    `07-b41` e ripetuta in `07-b63`."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
        f.write(comando)
        nome = f.name
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", nome,
                    "%s:/tmp/07-b66-remoto.sh" % MACCHINA], check=True)
    os.unlink(nome)
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                        "printf '%%s\\n' '%s' | sudo -S -p '' bash /tmp/07-b66-remoto.sh"
                        % PAROLA], capture_output=not binario, text=not binario)
    return p


def leggi_remoto(percorso):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                        "printf '%%s\\n' '%s' | sudo -S -p '' cat %s" % (PAROLA, percorso)],
                       capture_output=True)
    return p.stdout


def scrivi_remoto(percorso, dati):
    import tempfile
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(dati)
        nome = f.name
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", nome,
                    "%s:%s" % (MACCHINA, percorso)], check=True)
    os.unlink(nome)


def dentro_sessione(comando):
    """Esegue `comando` DENTRO la sessione grafica di provav7 — ⛔ e non nella
    sessione di chi sta davanti alla macchina."""
    return ("setpriv --reuid=%d --regid=%d --init-groups "
            "env XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
            "HOME=/home/%s USER=%s "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus %s"
            % (UID_B, UID_B, UID_B, UTENTE, UTENTE, UID_B, comando))


def carico():
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, "cat /proc/loadavg"],
                       capture_output=True, text=True)
    return p.stdout.split()[0] if p.stdout else "?"


# ---------------------------------------------------------------------------
# la scena
# ---------------------------------------------------------------------------
def fabbrica(L, A, guasto=0, sopra=180):
    """Ritorna (dipinto, atteso, riquadri) — due buffer XRGB8888 di L*A*4 byte.

    ⭐ `atteso` e' il metro, `dipinto` e' quel che finisce sullo schermo.  Sono
       lo stesso buffer tranne quando c'e' un guasto innestato: allora la
       differenza fra i due E' il difetto che il banco deve ritrovare.

    ⛔ La scena vera e' quella di `07-b62-prepara.py` — 343 riquadri, tutti e 256
       i livelli di Y, i limiti 0/16/235/255, le barre 100 % e 75 %, le rampe di
       croma.  ⚠ Non si riscrive: `CODER.md` §4.1.
    """
    # ⛔ La scena vuole una larghezza multipla di 256 e un'altezza multipla di 8;
    #    il monitor no.  Si genera la piu' grande che ci sta e si dichiara il
    #    resto FASCIA DI SERVIZIO, invece di riscalare (che sfocherebbe il metro).
    L2 = (L // 256) * 256
    A2 = ((A - FASCIA) // 8) * 8
    if L2 < 256 or A2 < 64:
        raise SystemExit("⛔ monitor %dx%d troppo piccolo per la scena" % (L, A))
    Y, U, V, riquadri = P62.costruisci_scena(L2, A2)

    px = bytearray(b"\x64\x64\x64\x00" * (L * A))
    # ⚠ La formula si applica una volta per TERNA distinta, non per pixel: la
    #   scena ne ha poche centinaia, e senza questa memoria il quadro ci mette
    #   minuti invece di secondi.  ⛔ Non e' un'approssimazione: e' la stessa
    #   funzione, chiamata meno volte.
    memoria = {}
    for r in range(A2):
        base = r * L2
        cbase = (r // 2) * (L2 // 2)
        o0 = 4 * r * L
        for c in range(L2):
            chiave = (Y[base + c], U[cbase + c // 2], V[cbase + c // 2])
            t = memoria.get(chiave)
            if t is None:
                rr, gg, bb = P62.rgb_da_yuv(chiave[0], chiave[1], chiave[2], "bt709", False)
                t = (round(bb), round(gg), round(rr))
                memoria[chiave] = t
            o = o0 + 4 * c
            px[o] = t[0]; px[o + 1] = t[1]; px[o + 2] = t[2]
    atteso = bytes(px)

    if guasto:
        # ⛔ Il guasto sta SOLO sopra la soglia: un banco che lo vedesse anche
        #    nelle ombre starebbe misurando qualcos'altro.
        for r in range(A2):
            for c in range(L2):
                o = 4 * (r * L + c)
                if max(px[o], px[o + 1], px[o + 2]) > sopra:
                    for k in range(3):
                        px[o + k] = min(255, px[o + k] + guasto)
    dipinto = bytes(px)

    # ⛔ E si CONTROLLA che il battito non tocchi nessun riquadro misurato: se lo
    #    toccasse, il banco accuserebbe il proprio quadrato lampeggiante.
    bx, by = L - LATO_BATTITO, A - LATO_BATTITO
    for q in riquadri:
        if q["x"] < L and q["y"] + q["h"] > by and q["x"] + q["w"] > bx:
            raise SystemExit("⛔ il battito tocca il riquadro «%s»" % q["nome"])
    return dipinto, atteso, riquadri, (L2, A2)


# ---------------------------------------------------------------------------
# il confronto
# ---------------------------------------------------------------------------
def medie_bgrx(buf, L, riquadri):
    out = {}
    for q in riquadri:
        sr = sg = sb = 0
        n = q["w"] * q["h"]
        for r in range(q["y"], q["y"] + q["h"]):
            o = 4 * (r * L + q["x"])
            for c in range(q["w"]):
                sb += buf[o]; sg += buf[o + 1]; sr += buf[o + 2]
                o += 4
        out[q["nome"]] = (sr / n, sg / n, sb / n)
    return out


def medie_rgb24(buf, L, riquadri):
    out = {}
    for q in riquadri:
        sr = sg = sb = 0
        n = q["w"] * q["h"]
        for r in range(q["y"], q["y"] + q["h"]):
            o = 3 * (r * L + q["x"])
            for c in range(q["w"]):
                sr += buf[o]; sg += buf[o + 1]; sb += buf[o + 2]
                o += 3
        out[q["nome"]] = (sr / n, sg / n, sb / n)
    return out


def confronta(titolo, letto, atteso_m, riquadri, soglia=1.0):
    """⛔ Medio e peggiore ASSOLUTI, per canale e per banda.  Nessuna mediana
    sottratta: un difetto uniforme si cancellerebbe da solo."""
    print("\n──── %s" % titolo)
    scarti = []
    for q in riquadri:
        a, m = atteso_m[q["nome"]], letto.get(q["nome"])
        if not m:
            continue
        for k in range(3):
            scarti.append((q["nome"], CANALI[k], a[k], m[k], m[k] - a[k]))
    if not scarti:
        print("  ⛔ NIENTE GIUDICATO")
        return {"esito": "⛔ NIENTE GIUDICATO", "n": 0}
    peggio = max(abs(x[4]) for x in scarti)
    medio = sum(abs(x[4]) for x in scarti) / len(scarti)
    print("  %d riquadri · %d canali · scarto medio %.3f · peggiore %.3f"
          % (len(riquadri), len(scarti), medio, peggio))
    print("     %-26s %4s   %15s %15s %15s"
          % ("banda", "n", "R medio/peggio", "G medio/peggio", "B medio/peggio"))
    per_banda = {}
    for nome, lo, hi in BANDE:
        dentro = [q for q in riquadri
                  if q["nome"].startswith("rampa-Y") and lo <= q["Y"] <= hi]
        if not dentro:
            continue
        cel = ""
        voce = {}
        for k in range(3):
            v = [letto[q["nome"]][k] - atteso_m[q["nome"]][k]
                 for q in dentro if q["nome"] in letto]
            if not v:
                cel += "         —     "
                continue
            voce[CANALI[k]] = {"medio": sum(v) / len(v), "peggio": max(v, key=abs)}
            cel += "  %+6.2f/%+6.2f" % (voce[CANALI[k]]["medio"], voce[CANALI[k]]["peggio"])
        print("     %-26s %4d %s" % ("%s (%d-%d)" % (nome, lo, hi), len(dentro), cel))
        per_banda[nome] = voce
    # ⭐ E le barre sature: il grigio non puo' accusare la matrice, loro si'.
    print("     le barre 100 %% (scarto R/G/B):")
    for q in riquadri:
        if not q["nome"].startswith("barra100"):
            continue
        m = letto.get(q["nome"])
        if not m:
            continue
        a = atteso_m[q["nome"]]
        print("       %-10s %+7.2f %+7.2f %+7.2f" % (q["nome"].split("-", 1)[1],
                                                     m[0] - a[0], m[1] - a[1], m[2] - a[2]))
    esito = ("⭐ NESSUNO SCARTO OLTRE %.1f LIVELLI (peggiore %.3f)" % (soglia, peggio)
             if peggio <= soglia else "⛔ SCARTO fino a %.3f livelli" % peggio)
    print("  ⇒ %s" % esito)
    return {"esito": esito, "medio": medio, "peggio": peggio, "canali": len(scarti),
            "riquadri": len(riquadri), "bande": per_banda}


def byte_per_byte(catturato, atteso, L, A):
    """⭐ IL CONFRONTO CHE NON SI PUO' INTERPRETARE: gli stessi byte o no.
    ⛔ Si esclude la sola fascia di servizio (il battito), e si dichiara quanto
       si e' escluso — un denominatore taciuto e' un verde che non ha guardato."""
    diversi = 0
    peggio = 0
    istogramma = {}
    righe_scena = A - FASCIA
    for r in range(righe_scena):
        o = 4 * r * L
        a = atteso[o:o + 4 * L]
        b = catturato[o:o + 4 * L]
        if a == b:
            continue
        for i in range(0, 4 * L, 4):
            for k in range(3):
                d = b[i + k] - a[i + k]
                if d:
                    diversi += 1
                    peggio = max(peggio, abs(d))
                    istogramma[d] = istogramma.get(d, 0) + 1
    tot = righe_scena * L * 3
    return {"canali_confrontati": tot, "diversi": diversi, "peggio": peggio,
            "righe_escluse": FASCIA,
            "istogramma": dict(sorted(istogramma.items(), key=lambda t: -t[1])[:12])}


# ---------------------------------------------------------------------------
# gli effetti del compositore
# ---------------------------------------------------------------------------
EFFETTI = {
    "niente": [
        "gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled false",
        "gsettings set org.gnome.desktop.a11y.applications screen-magnifier-enabled false",
        "gsettings reset org.gnome.desktop.a11y.magnifier invert-lightness",
        "gsettings reset org.gnome.desktop.a11y.magnifier brightness-blue",
        "gsettings reset org.gnome.desktop.a11y.magnifier mag-factor",
    ],
    # ⭐ IL CONTROLLO POSITIVO DEL COMPOSITORE: l'ingranditore a 1x con la
    #    luminosita' invertita e' una trasformazione di colore fatta DENTRO la
    #    composizione.  Se la cattura la vede, allora vedrebbe anche un profilo.
    "lente": [
        "gsettings set org.gnome.desktop.a11y.magnifier mag-factor 1.0",
        "gsettings set org.gnome.desktop.a11y.magnifier lens-mode false",
        "gsettings set org.gnome.desktop.a11y.magnifier screen-position 'full-screen'",
        "gsettings set org.gnome.desktop.a11y.magnifier invert-lightness true",
        "gsettings set org.gnome.desktop.a11y.magnifier brightness-blue -0.5",
        "gsettings set org.gnome.desktop.a11y.applications screen-magnifier-enabled true",
    ],
    # ⚠ E qui la risposta NON si sa prima: e' la misura.
    "nottelunga": [
        "gsettings set org.gnome.settings-daemon.plugins.color night-light-schedule-automatic false",
        "gsettings set org.gnome.settings-daemon.plugins.color night-light-schedule-from 0.0",
        "gsettings set org.gnome.settings-daemon.plugins.color night-light-schedule-to 24.0",
        "gsettings set org.gnome.settings-daemon.plugins.color night-light-temperature 1700",
        "gsettings set org.gnome.settings-daemon.plugins.color night-light-enabled true",
    ],
}


def applica_effetto(nome):
    righe = EFFETTI["niente"] + (EFFETTI[nome] if nome != "niente" else [])
    # ⛔⛔ IL COMANDO NON SI RIMETTE DENTRO A UN `echo` FRA APICI — difetto del
    #     banco, `[M]` 22 agosto 2026, e ha quasi prodotto un verde falso.
    #     `screen-position 'full-screen'` porta apici dentro, il copione remoto
    #     diventava sintatticamente rotto, **nessun** `gsettings` girava, e il
    #     giro seguente misurava «nessuna differenza» credendo di aver acceso
    #     l'ingranditore.  ⇒ Un controllo positivo che non si accende non e' un
    #     controllo: e' esattamente la cecita' che doveva escludere.
    #     ⚠ Adesso si numera il comando, e la rilettura e' l'unica prova.
    copione = "set -u\n" + "\n".join(
        "%s || echo '⚠ fallita la riga %d'" % (dentro_sessione(c), i)
        for i, c in enumerate(righe))
    copione += ("\n" + dentro_sessione(
        "gsettings get org.gnome.settings-daemon.plugins.color night-light-enabled") +
        "\n" + dentro_sessione(
        "gsettings get org.gnome.desktop.a11y.applications screen-magnifier-enabled"))
    p = remoto(copione)
    righe_uscita = (p.stdout or "").strip().splitlines()
    if (p.stderr or "").strip():
        print("   ⚠ dal copione degli effetti: %s" % (p.stderr or "").strip()[-300:])
    # ⛔ Non si dichiara «acceso» perche' lo si e' chiesto: si RILEGGE (`CODER.md`
    #    §3.8, si verifica dal lato che riceve).  ⚠ E se la rilettura non c'e',
    #    lo si dice — un «?» e' una risposta, un verde inventato no.
    coda = righe_uscita[-2:] if len(righe_uscita) >= 2 else ["?", "?"]
    print("   effetto «%s» ⇒ nottelunga=%s lente=%s  (RILETTI dal dconf della sessione)"
          % (nome, coda[0], coda[1]))
    if [r for r in righe_uscita if "⚠ fallita" in r]:
        print("   ⚠ %s" % "; ".join(r for r in righe_uscita if "⚠ fallita" in r))
    # ⛔ E SE LA RILETTURA NON DICE QUEL CHE SI E' CHIESTO, SI MUORE.  Un giro
    #    che misura «nessuna differenza» con l'effetto spento non e' una misura:
    #    e' il controllo positivo che non si e' acceso.
    atteso = {"niente": ("false", "false"), "lente": ("false", "true"),
              "nottelunga": ("true", "false")}[nome]
    if tuple(coda) != atteso:
        raise SystemExit("⛔ l'effetto «%s» NON e' in vigore: riletto %s, atteso %s"
                         % (nome, tuple(coda), atteso))
    return coda


# ---------------------------------------------------------------------------
# il giro
# ---------------------------------------------------------------------------
def tasto(m, valore, quante=1):
    """Un tasto vero, per la strada del PRODOTTO (pagina → RCP → libei → Mutter).
    ⛔ E non `org.gnome.Shell.Eval`, che su una build di distribuzione e' chiusa e
       che comunque non e' la strada dell'utente."""
    for _ in range(quante):
        m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "key", "id": "tastiera",
            "actions": [{"type": "keyDown", "value": valore},
                        {"type": "pause", "duration": 60},
                        {"type": "keyUp", "value": valore}]}]})
        time.sleep(1.0)


def chiudi_panoramica(m):
    """⛔⛔ LA PANORAMICA DI GNOME E' UN EFFETTO DELLO SHELL SULLA SUPERFICIE, ed
    e' la trappola 3 del mandato — trovata al primo giro, `[M]` 22 agosto 2026.

    Una sessione appena nata apre la **panoramica delle attivita'**: la finestra
    a schermo intero non e' a schermo intero, e' una **miniatura riscalata**
    dentro il pannello delle aree di lavoro, con barra in alto e dock sotto.
    `[M]` la cattura di quel quadro dava scarti fino a **221 livelli** — che un
    banco meno attento avrebbe scritto in tabella come «difetto di colore».
    ⇒ La panoramica si chiude PRIMA di misurare, e la si chiude con `Escape`
      dalla strada dell'utente."""
    m.js("const t=document.getElementById('schermo'); if(t) t.focus(); return true;")
    tasto(m, "\ue00c", 2)          # Escape


def spegni_vetrina():
    remoto("pkill -f 07-b66-vetrina 2>/dev/null; rm -f %s/vetrina.pid; echo spenta" % LAV)


def monitor_del_prodotto():
    p = remoto("grep -ao 'monitor «[^»]*»' %s/registro.log 2>/dev/null | grep -v '«»' "
               "| tail -1 | sed 's/monitor «//; s/»//'" % LAV)
    return (p.stdout or "").strip()


def giro(o):
    os.makedirs(FUORI, exist_ok=True)
    print("⭐ carico sulla macchina di prova: %s  (otto agenti; ⚠ il colore dal "
          "carico non dipende, ma si dichiara)" % carico())
    spegni_vetrina()
    # ⛔ La cartella del rilievo NON la crea il prodotto: `[M]` primo giro,
    #    «SCATTO … scatto-flusso.obu: No such file or directory» e i tre file
    #    non esistevano.  ⚠ Il registro pero' diceva «ingresso 1284x774, 3975264
    #    byte» ⇒ era la forma peggiore, una riga verde su un file mai scritto.
    remoto("mkdir -p %s/rilievo && chmod 777 %s/rilievo && echo ok" % (LAV, LAV))

    # --- 1 · il browser fa nascere la sessione e il monitor -----------------
    # ⛔⛔ E LA VETRINA DEL BROWSER NON E' UN DETTAGLIO: su `--headless` (e su
    #     Xvfb) Firefox mette la decodifica in hardware nella lista nera da se'
    #     — `FEATURE_FAILURE_VIDEO_DECODING_TEST_FAILED` — e la «strada
    #     dell'hardware» E' la strada software.  `[M]` 21 agosto 2026, `07-b62`:
    #     due giri interi hanno confrontato il software con se stesso dando
    #     «nessuna differenza».  ⇒ Per il VETRO si usa `cage`, e il banco
    #     RIFIUTA di chiamare «hardware» un giro senza `IsHardwareAccelerated=1`.
    #  ⚠ Per i punti 1 e 2 (cattura e flusso) il browser serve solo a far
    #    nascere la sessione: li' `--headless` va benissimo e si dichiara.
    prefs = dict(T62.PREFS_COMUNI)
    cage = disp = marca = reg_dir = reg_file = None
    if o.vetrina == "cage":
        prefs.update(T62.PREFS_HW)
        cage, disp, marca = T62.accendi_cage(o.nodo)
        print("⭐ compositore del browser: `cage` headless sul nodo %s, socket «%s» "
              "(NON la sessione di chi sta davanti alla macchina)" % (o.nodo, disp))
        reg_dir = __import__("tempfile").mkdtemp(prefix="remotix-b66-mozlog-")
        reg_file = os.path.join(reg_dir, "moz.log")
        # ⛔ Il registro si prepara PRIMA di accendere il browser, o il processo
        #    e' gia' partito e non lo vede: «zero tracce VA-API» sarebbe la forma
        #    peggiore di zero.
        os.environ["MOZ_LOG"] = "PlatformDecoderModule:5,FFmpegVideo:5,MediaDecoder:4"
        os.environ["MOZ_LOG_FILE"] = reg_file
        os.environ.update(T62.AMBIENTE_HW)
        os.environ["WAYLAND_DISPLAY"] = disp
        os.environ["MOZ_ENABLE_WAYLAND"] = "1"
        os.environ.pop("DISPLAY", None)
    p = m = prof = None
    esiti = {"comando": vars(o)}
    try:
        p, m, prof = M.accendi(profilo_prefs=prefs, headless=(o.vetrina != "cage"),
                               porta=o.marionette, largo=o.largo, alto=o.alto)
        # ⛔ La forma ANNIDATA (`capabilities.alwaysMatch`) di `Marionette.sessione()`
        #    NON accende `acceptInsecureCerts` su questo Firefox: `[M]` il primo
        #    giro e' morto con «insecure certificate» sul certificato nostro.
        #    ⚠ La forma piatta e' quella che `07-b52` usa gia' e che funziona.
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(o.largo, o.alto)
        # ⛔ SI RIPROVA, e non e' pigrizia: `[M]` 22 agosto, un giro su due il
        #    primo ingresso non attaccava — la pagina si collegava (le sue righe
        #    `/diario` stanno nel registro) ma la sessione WebTransport non
        #    nasceva, e il registro del server non scriveva nemmeno un «posto
        #    occupato».  ⚠ Il sospetto e' la connessione QUIC di prima, che
        #    resta viva trenta secondi dopo che il browser e' morto (§2.2).
        #    ⇒ Si aspetta, si ricarica e si riclicca fino a tre volte, e si
        #      DICHIARA quanti tentativi ci sono voluti invece di nasconderlo.
        acceso = False
        for tentativo in range(1, 4):
            m.vai("https://192.168.0.2:%d/" % PORTA)
            m.js("""document.getElementById('utente').value=arguments[0];
                    document.getElementById('parola').value=arguments[1];
                    document.getElementById('vai').click(); return true;""",
                 [UTENTE, PAROLA_UTENTE])
            t0 = time.time()
            while time.time() - t0 < 60:
                if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                    acceso = True
                    break
                time.sleep(0.5)
            if acceso:
                if tentativo > 1:
                    print("   ⚠ lo schermo si e' acceso al tentativo %d" % tentativo)
                break
            print("   ⚠ tentativo %d: lo schermo non si e' acceso in 60 s, riprovo" % tentativo)
            time.sleep(20)
        if not acceso:
            raise SystemExit("⛔ lo schermo non si e' acceso in tre tentativi")
        time.sleep(4)
        L, A = m.js("const t=document.getElementById('schermo'); return [t.width,t.height];")["value"]
        print("⭐ la sessione e' viva · il monitor e' %dx%d (letto dalla tela, non dedotto)" % (L, A))
        uscita = monitor_del_prodotto()
        if not uscita:
            raise SystemExit("⛔ il registro del MIO server non nomina nessun monitor")
        print("⭐ il monitor del MIO prodotto e' «%s» (letto dal registro)" % uscita)
        esiti["monitor"] = {"nome": uscita, "l": L, "a": A}

        # --- 2 · la scena esatta, alla misura del monitor -------------------
        dipinto, atteso, riquadri, (L2, A2) = fabbrica(L, A, o.guasto, o.sopra)
        print("⭐ scena %dx%d dentro un quadro %dx%d · %d riquadri · fascia di "
              "servizio %d righe%s" % (L2, A2, L, A, len(riquadri), FASCIA,
                                       "" if not o.guasto else
                                       "  ⛔ GUASTO INNESTATO: +%d sopra %d" % (o.guasto, o.sopra)))
        open(os.path.join(FUORI, "atteso.xrgb"), "wb").write(atteso)
        scrivi_remoto("/tmp/07-b66-dipinto.xrgb", dipinto)
        remoto("mkdir -p %s && mv /tmp/07-b66-dipinto.xrgb %s/dipinto.xrgb && "
               "chmod 644 %s/dipinto.xrgb && chmod 755 %s && echo ok" % (LAV, LAV, LAV, LAV))

        # --- 3 · l'effetto del compositore ---------------------------------
        applica_effetto(o.effetto)
        time.sleep(2)

        # --- 4 · la vetrina, DENTRO la sessione -----------------------------
        avvio = ("set -u\n"
                 ": >> %s/vetrina.log; chmod 666 %s/vetrina.log\n" % (LAV, LAV) +
                 dentro_sessione("nohup stdbuf -oL -eL %s/07-b66-vetrina "
                                 "--uscita '%s' --immagine %s/dipinto.xrgb "
                                 "--misura %dx%d --secondi %d --pulsa %d"
                                 % (LAV, uscita, LAV, L, A, o.secondi, LATO_BATTITO)) +
                 " >> %s/vetrina.log 2>&1 &\n" % LAV +
                 "echo $! > %s/vetrina.pid\nsleep 4\ntail -6 %s/vetrina.log\n" % (LAV, LAV))
        pr = remoto(avvio)
        print("   vetrina:\n%s" % "\n".join("      " + r for r in (pr.stdout or "").strip().splitlines()))
        if "muori" in (pr.stdout or "") or "⛔" in (pr.stdout or ""):
            raise SystemExit("⛔ la vetrina non e' partita")
        # ⛔ La panoramica si chiude DOPO che la finestra e' nata: una finestra
        #    nuova su una sessione appena accesa la riapre.  ⚠ E si RILEGGE dalla
        #    misura, non si spera: `verifica_intero()` piu' sotto.
        chiudi_panoramica(m)
        time.sleep(3)

        # --- 5 · lo SCATTO del prodotto -------------------------------------
        remoto("systemctl kill --kill-whom=main -s SIGUSR1 remotix-%d.service; echo armato" % PORTA)
        time.sleep(6)
        remoto("systemctl kill --kill-whom=main -s SIGUSR2 remotix-%d.service; echo chiuso" % PORTA)
        time.sleep(2)

        # --- 6 · la tela del browser, dallo stesso istante ------------------
        tela = None
        if o.vetro:
            d = m.js("const t=document.getElementById('schermo');"
                     "try{return t.toDataURL('image/png');}catch(e){return 'ERRORE '+e;}")["value"]
            if d.startswith("data:image"):
                tela = os.path.join(FUORI, "tela.png")
                open(tela, "wb").write(base64.b64decode(d.split(",", 1)[1]))
            conti = m.js("const x=REMOTIX.schermo; return [x.conti.consegnati,"
                         "x.conti.dipinti,x.conti.tardive,x.conti.buchi,x.errori.slice(-2)];")["value"]
            print("   tela: %s · conti %s" % (tela, conti))
            esiti["conti_pagina"] = conti
        # ⛔ CHI HA DECODIFICATO DAVVERO — dal registro di Firefox, non
        #    dall'interruttore.  Un interruttore chiamato «hardware» dice che
        #    cosa si e' CHIESTO.
        if reg_file:
            r = T62.chi_ha_decodificato(reg_file)
            acc = [x for x in r["righe"] if "IsHardwareAccelerated=1" in x]
            esiti["hardware_davvero"] = bool(acc)
            esiti["tracce_vaapi"] = r["tracce_vaapi"]
            print("\n  ⚠ chi ha decodificato: tracce VA-API %d su %d byte di registro · %s"
                  % (r["tracce_vaapi"], r["byte_registro"],
                     "⭐ IsHardwareAccelerated=1" if acc else
                     "⛔⛔ NESSUN `IsHardwareAccelerated=1`: NON e' la strada dell'hardware"))
            for x in r["righe"][:4]:
                print("      %s" % x[:150])
    finally:
        if p:
            M.spegni(p, prof)
        if cage:
            # ⛔ `terminate()` non basta: cage sopravvive al SIGTERM finche' il
            #    figlio e' vivo, e un compositore orfano fa morire il Firefox del
            #    giro dopo (`07-b62` §accendi_cage).
            cage.kill()
            try:
                cage.wait(10)
            except Exception:
                pass
            __import__("shutil").rmtree(marca, ignore_errors=True)
    spegni_vetrina()
    if o.effetto != "niente":
        applica_effetto("niente")

    # --- 7 · i tre punti di misura -----------------------------------------
    reg = remoto("grep SCATTO %s/registro.log | tail -3" % LAV)
    print("\n   dal registro del prodotto:\n%s"
          % "\n".join("      " + r for r in (reg.stdout or "").strip().splitlines()))
    ing = leggi_remoto("%s/rilievo/scatto-ingresso.bgrx" % LAV)
    flu = leggi_remoto("%s/rilievo/scatto-flusso.obu" % LAV)
    open(os.path.join(FUORI, "scatto-ingresso.bgrx"), "wb").write(ing)
    open(os.path.join(FUORI, "scatto-flusso.obu"), "wb").write(flu)
    print("   scatto-ingresso.bgrx %d byte (attesi %d) · scatto-flusso.obu %d byte"
          % (len(ing), L * A * 4, len(flu)))
    if len(ing) != L * A * 4:
        raise SystemExit("⛔ lo scatto non e' %dx%d: non confronto quadri di misura diversa" % (L, A))

    # ⭐ Le due immagini si scrivono SEMPRE, e servono all'occhio prima che alla
    #    tabella: `[M]` 22 agosto il primo giro dava «221 livelli di scarto», e
    #    il PNG diceva in un colpo d'occhio che la colpa era la panoramica di
    #    GNOME e non il colore.  ⛔ Una tabella non lo avrebbe mai detto.
    for nome, dati in (("cattura.png", ing), ("atteso.png", atteso)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                        "-s", "%dx%d" % (L, A), "-i", "-", "-frames:v", "1",
                        os.path.join(FUORI, nome)], input=dati, capture_output=True)

    atteso_m = medie_bgrx(atteso, L, riquadri)

    # 1 · dipinto → catturato, byte per byte
    bb = byte_per_byte(ing, atteso, L, A)
    print("\n════ 1 · DIPINTO → CATTURATO  (i pixel che il codificatore ha in mano)")
    print("   byte per byte: %d canali confrontati, %d diversi (%.6f %%), peggio %d livelli"
          % (bb["canali_confrontati"], bb["diversi"],
             100.0 * bb["diversi"] / bb["canali_confrontati"], bb["peggio"]))
    if bb["istogramma"]:
        print("   i dodici scarti piu' frequenti: %s" % bb["istogramma"])
    # ⛔ E UNO SCARTO ENORME NON SI CHIAMA «DIFETTO DI COLORE».  Sopra il 5 % di
    #    canali diversi non si sta guardando la stessa immagine con un colore
    #    storto: si sta guardando **un'altra immagine** (la panoramica, una
    #    finestra sopra, la scena non ancora a schermo intero).  Chiamarla colore
    #    sarebbe la diagnosi giusta sull'imputato sbagliato.
    # ⚠ E LE DUE CONDIZIONI VANNO INSIEME — difetto del banco, `[M]` 22 agosto:
    #   con la sola frazione, il guasto innestato «+8 sopra 180» faceva scattare
    #   l'avviso (36 % dei canali diversi) e il banco accusava se stesso di
    #   guardare l'immagine sbagliata mentre stava guardando quella giusta con
    #   dentro il difetto che gli era stato messo.  ⇒ serve anche uno scarto
    #   GROSSO: un colore storto sposta di pochi livelli, un'immagine diversa no.
    if bb["diversi"] > 0.05 * bb["canali_confrontati"] and bb["peggio"] > 32:
        print("   ⛔⛔ PIU' DEL 5 %% DEI CANALI E' DIVERSO: questa NON e' una misura di "
              "colore.\n"
              "        Il quadro catturato non e' la vetrina a schermo intero — "
              "guarda %s/cattura.png\n"
              "        accanto a %s/atteso.png prima di scrivere qualunque numero."
              % (FUORI, FUORI))
    esiti["byte_per_byte"] = bb
    esiti["cattura"] = confronta("per riquadro · dipinto → catturato",
                                 medie_bgrx(ing, L, riquadri), atteso_m, riquadri)

    # 2 · dipinto → flusso
    print("\n════ 2 · DIPINTO → FLUSSO  (i byte che il prodotto SPEDISCE, riletti da ffmpeg)")
    rgb = decodifica(os.path.join(FUORI, "scatto-flusso.obu"), L, A)
    if rgb:
        esiti["flusso"] = confronta("per riquadro · dipinto → flusso", medie_rgb24(rgb, L, riquadri),
                                    atteso_m, riquadri, soglia=3.0)
    else:
        print("   ⛔ ffmpeg non ha decodificato niente")

    # 3 · dipinto → vetro
    if o.vetro and tela:
        print("\n════ 3 · DIPINTO → VETRO  (la tela del browser)")
        rgbv = png_in_rgb(tela, L, A)
        if rgbv:
            esiti["vetro"] = confronta("per riquadro · dipinto → vetro",
                                       medie_rgb24(rgbv, L, riquadri), atteso_m, riquadri,
                                       soglia=3.0)

    dove = o.esiti or os.path.join(FUORI, "07-b66-esiti-%s.json" % o.etichetta)
    json.dump(esiti, open(dove, "w"), indent=1)
    print("\nesiti in %s" % dove)
    return esiti


def decodifica(percorso, L, A):
    """⛔ Si chiede la matrice PER NOME e l'uscita PIENA: il difetto predefinito
    di swscale non e' detto sia la VUI del flusso, e un riferimento storto
    accuserebbe il prodotto dello sbaglio di ffmpeg (`07-b62` §ffmpeg_in_rgb)."""
    cmd = ["ffmpeg", "-v", "error", "-f", "h264", "-i", percorso, "-frames:v", "1",
           "-vf", "scale=in_color_matrix=bt709:in_range=tv:out_range=full:"
                  "flags=full_chroma_int+accurate_rnd",
           "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode or len(p.stdout) < L * A * 3:
        print("   ⛔ ffmpeg: %s" % (p.stderr or b"")[-300:].decode(errors="replace"))
        return None
    return p.stdout[:L * A * 3]


def png_in_rgb(percorso, L, A):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", percorso, "-pix_fmt", "rgb24",
                        "-f", "rawvideo", "-"], capture_output=True)
    if p.returncode or len(p.stdout) < L * A * 3:
        print("   ⛔ ffmpeg sulla tela: %s" % (p.stderr or b"")[-300:].decode(errors="replace"))
        return None
    return p.stdout[:L * A * 3]


# ---------------------------------------------------------------------------
def costruisci():
    """⛔ Dentro il contenitore: sull'host non ci sono ne' `gcc` ne'
    `wayland-scanner` (`03-b17-accendi.sh` §scena-costruisci)."""
    # ⛔ Il contenitore NON vede il `/tmp` dell'host: monta `/media/REMOTIX` su
    #    `/srv/remotix` e `/media/REMOTIX/src` su `/srv/src` (`enter.sh`).  Il
    #    sorgente e il copione vanno messi **nella cartella condivisa**, o il
    #    sintomo e' «No such file or directory» su un file che c'e'.
    dentro = LAV.replace("/media/REMOTIX", "/srv/remotix")
    remoto("mkdir -p %s/costruzione && chmod 755 %s %s/costruzione && echo ok" % (LAV, LAV, LAV))
    sorgente = open(os.path.join(QUI, "07-b66-vetrina.c"), "rb").read()
    scrivi_remoto("/tmp/07-b66-vetrina.c", sorgente)
    remoto("mv /tmp/07-b66-vetrina.c %s/costruzione/ && echo ok" % LAV)
    copione = r"""set -e
cd %(dentro)s/costruzione
for c in gcc pkg-config wayland-scanner; do command -v $c >/dev/null || { echo "⛔ manca $c"; exit 2; }; done
X=/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml
[ -s $X ] || { echo "⛔ manca $X"; exit 2; }
wayland-scanner client-header $X xdg-shell-client-protocol.h
wayland-scanner private-code  $X xdg-shell-protocol.c
gcc -O2 -Wall -Wextra -o 07-b66-vetrina 07-b66-vetrina.c xdg-shell-protocol.c -I. \
    $(pkg-config --cflags --libs wayland-client) -lrt
cp 07-b66-vetrina %(dentro)s/07-b66-vetrina
chmod 755 %(dentro)s %(dentro)s/07-b66-vetrina
echo "⭐ costruita: %(dentro)s/07-b66-vetrina"
""" % {"dentro": dentro}
    scrivi_remoto("/tmp/07-b66-costruisci.sh", copione.encode())
    remoto("mv /tmp/07-b66-costruisci.sh %s/costruzione/ && echo ok" % LAV)
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                        "printf '%%s\\n' '%s' | sudo -S -p '' bash /media/REMOTIX/enter.sh "
                        "--root 'bash %s/costruzione/07-b66-costruisci.sh 2>&1'"
                        % (PAROLA, dentro)],
                       capture_output=True, text=True)
    print(p.stdout or "", p.stderr or "")
    return 0 if "⭐ costruita" in (p.stdout or "") else 1


def certifica(o):
    """⛔ IL BANCO SI CERTIFICA PRIMA DI ESSERE CREDUTO (`PIANO.md` §0.3.4) — e
    qui i controlli sono TRE, perche' tre sono le trasformazioni che il mandato
    chiede di separare.

      1. **sano**            i pixel dipinti e i pixel catturati devono essere
                             gli stessi byte.  ⚠ E' anche il denominatore: se
                             qui non fosse zero, nessun altro numero varrebbe.
      2. **guasto +8**       un difetto messo DOVE SI SA: il banco deve trovarlo
                             nelle luci e **non** nelle ombre.  Un banco che lo
                             vedesse dappertutto misurerebbe qualcos'altro.
      3. ⭐ **lente**        una trasformazione di colore VERA del compositore.
                             Se la cattura la vede, allora **vedrebbe anche un
                             profilo di colore applicato in composizione** — ed
                             e' quel che rende il punto 4 una risposta.
      4. **nottelunga**      Night Light a 1700 K.  ⚠ Non e' un controllo: e' la
                             domanda aperta, e la si legge dopo il 3.
    """
    fuori = {}
    for etichetta, extra in (("sano", {}),
                             ("guasto8", {"guasto": 8, "sopra": 180}),
                             ("lente", {"effetto": "lente"}),
                             ("nottelunga", {"effetto": "nottelunga"})):
        print("\n" + "=" * 78 + "\n════ CERTIFICAZIONE · %s" % etichetta)
        import copy
        oo = copy.copy(o)
        oo.guasto, oo.sopra, oo.effetto, oo.etichetta = 0, 180, "niente", etichetta
        for k, v in extra.items():
            setattr(oo, k, v)
        fuori[etichetta] = giro(oo)

    print("\n" + "=" * 78 + "\n════ IL VERDETTO DELLA CERTIFICAZIONE")
    sano = fuori["sano"]["cattura"]["peggio"]
    g = fuori["guasto8"]["cattura"]["bande"]
    luci = g["luci"]["R"]["medio"]
    ombre = g["ombre"]["R"]["medio"]
    lente = fuori["lente"]["cattura"]["peggio"]
    notte = fuori["nottelunga"]["cattura"]["peggio"]
    ok1 = sano == 0.0
    ok2 = 6.0 <= luci <= 9.0 and abs(ombre) <= 1.0
    ok3 = lente > 32.0
    print("  1 sano        peggio %7.3f   ⇒ %s" % (sano,
          "⭐ dipinto e catturato sono GLI STESSI BYTE" if ok1
          else "⛔ non sono gli stessi byte: ogni altro numero e' sospetto"))
    print("  2 guasto +8   luci %+7.2f · ombre %+7.2f  ⇒ %s" % (luci, ombre,
          "⭐ VISTO, e solo dove e' stato messo" if ok2 else "⛔ NON VISTO — BANCO CIECO"))
    print("  3 lente       peggio %7.3f   ⇒ %s" % (lente,
          "⭐ una trasformazione del COMPOSITORE la cattura la vede" if ok3
          else "⛔ NON VISTA — allora il «niente» del punto 4 non vale"))
    print("  4 nottelunga  peggio %7.3f   ⇒ %s" % (notte,
          ("⭐ Night Light NON entra nei pixel catturati (ed e' una RISPOSTA, "
           "perche' il punto 3 e' passato)" if ok3 else
           "⚠ nessuna differenza, ma il punto 3 non e' passato: non e' una risposta")
          if notte == 0.0 else "⛔ Night Light ENTRA nei pixel catturati: %.3f livelli" % notte))
    dove = os.path.join(FUORI, "07-b66-certificazione.json")
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "comando"}
               for k, v in fuori.items()}, open(dove, "w"), indent=1)
    print("\ncertificazione in %s" % dove)
    return 0 if (ok1 and ok2 and ok3) else 1


def main():
    a = argparse.ArgumentParser()
    a.add_argument("comando", choices=("costruisci", "giro", "certifica", "pulisci"))
    a.add_argument("--guasto", type=int, default=0, help="+N livelli sopra la soglia, DIPINTI")
    a.add_argument("--sopra", type=int, default=180)
    a.add_argument("--effetto", default="niente", choices=tuple(EFFETTI))
    a.add_argument("--vetro", action="store_true")
    a.add_argument("--vetrina", default="headless", choices=("headless", "cage"),
                   help="⛔ su headless la decodifica in hardware NON e' l'hardware")
    a.add_argument("--nodo", default="/dev/dri/renderD128")
    a.add_argument("--secondi", type=int, default=90)
    a.add_argument("--largo", type=int, default=1296)
    a.add_argument("--alto", type=int, default=860)
    a.add_argument("--marionette", type=int, default=2866)
    a.add_argument("--etichetta", default="sano")
    a.add_argument("--esiti", default="")
    o = a.parse_args()
    if o.comando == "costruisci":
        return costruisci()
    if o.comando == "pulisci":
        spegni_vetrina(); applica_effetto("niente"); return 0
    if o.comando == "certifica":
        return certifica(o)
    giro(o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
