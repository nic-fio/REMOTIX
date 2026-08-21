#!/usr/bin/env python3
"""07-b59 — REMOTIX su FIREFOX PER ANDROID, in un emulatore, senza chiedere niente a nessuno.

    python3 banchi/07-b59-firefox-android.py [--accendi] [--secondi 40]

⛔ PERCHE' ESISTE — 21 agosto 2026, e la frase e' dell'utente: *«non sei in grado
   di far funzionare Firefox per android con remotix»*, dopo che gli avevo fatto
   provare **sei volte** sul suo telefono cose che si rompevano ogni volta in un
   punto diverso.  ⇒ *«Installa la suite android sdk, usa quella»*.

⭐ E aveva ragione due volte: sul risultato, e sul metodo.  Il banco `07-b58`
   toglie WebCodecs a un Firefox da tavolo e prende quasi tutto — ma NON prende
   quel che e' proprio di Android: le regole di presentazione dei motori mobili,
   e il comportamento del `<video>` sotto MSE su quel motore.  ⇒ Qui c'e'
   Firefox **154 per Android**, la stessa versione del suo telefono, dentro un
   emulatore con KVM.

Che cosa fa, da solo:
  1. accende l'emulatore (`remotix`) se non risponde;
  2. apre REMOTIX in Firefox, accetta il certificato, entra con «prova»;
  3. lascia girare, poi legge nel registro del SERVER quel che la pagina ha
     raccontato — `MISURA §7.18 MSE: …`, che e' la riga che dice se il `<video>`
     e' fermo, in ricerca, o senza dati.

⚠ Che cosa NON riproduce, e si dichiara: un telefono vero ha la decodifica in
  hardware e questo emulatore no.  ⇒ I NUMERI del ritardo non valgono; vale il
  COMPORTAMENTO — dipinge o no, si ferma o no, e perche'.

Preparazione, una volta sola (`~/Android/Sdk`):
    sdkmanager --install "platform-tools" "emulator" \\
               "system-images;android-34;google_apis;x86_64"
    avdmanager create avd -n remotix -k "system-images;android-34;google_apis;x86_64" -d pixel_6
    adb install fenix-<versione>.multi.android-x86_64.apk
"""
import argparse, json, os, subprocess, sys, time, urllib.parse

QUI = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.expanduser("~")
ADB = os.path.join(CASA, "Android/Sdk/platform-tools/adb")
EMU = os.path.join(CASA, "Android/Sdk/emulator/emulator")
MACCHINA = "192.168.0.2"

a = argparse.ArgumentParser()
a.add_argument("--porta", type=int, default=7730)
a.add_argument("--lavoro", default="/media/REMOTIX/tmp/07-appunti")
a.add_argument("--secondi", type=int, default=40)
a.add_argument("--accendi", action="store_true", help="accendi l'emulatore se non c'e'")
o = a.parse_args()


def adb(*v, testo=True, t=60):
    return subprocess.run([ADB] + list(v), capture_output=True, text=testo,
                          timeout=t).stdout


def vivo():
    return "device" in (adb("devices") or "").replace("offline", "")


def accendi():
    subprocess.Popen([EMU, "-avd", "remotix", "-no-window", "-no-audio",
                      "-no-boot-anim", "-gpu", "swiftshader_indirect",
                      "-no-snapshot", "-accel", "on", "-memory", "3072"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 300:
        if (adb("shell", "getprop", "sys.boot_completed") or "").strip() == "1":
            return True
        time.sleep(5)
    return False


def ui():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    return adb("shell", "cat", "/sdcard/ui.xml")


def tocca(chiave):
    import re
    x = ui()
    for m in re.finditer(r'<node[^>]*>', x):
        t = m.group(0)
        g = lambda k: (re.search(k + r'="([^"]*)"', t) or [None, ""])[1]
        b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', t)
        if not b:
            continue
        if chiave.lower() in (g("text") + " " + g("content-desc") + " "
                              + g("resource-id")).lower():
            x1, y1, x2, y2 = map(int, b.groups())
            adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
            return True
    return False


# ⛔⛔⭐ LA SCENA SI ACCENDE E SI SPEGNE **QUI DENTRO** — 21 agosto 2026, e il
#      difetto l'ha visto l'utente sul suo desktop: *«che diavolo succede?  E'
#      come se si aprissero terminali infiniti»*.
#
# ⚠ Un desktop fermo non manda fotogrammi, quindi il banco ha bisogno di
#   qualcosa che si muova: un terminale che scorre.  ⛔ Ma lo accendevo A MANO a
#   ogni giro, e nessuno lo spegneva — dopo dieci giri, dieci terminali e dieci
#   cicli infiniti **sul desktop di una persona**.
# ⇒ La accende il banco e la spegne il banco, in un `finally`: chi apre chiude.
SCENA = ("#!/bin/sh\n"
         "U=$(id -u prova)\n"
         "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
         "export DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus\n"
         # ⛔ Prima si spegne quel che c'era: due scene sono gia' troppe.
         "pkill -u prova -f 'REMOTIX-SCENA' 2>/dev/null\n"
         "sleep 0.5\n"
         "setsid gnome-terminal --title=REMOTIX-SCENA -- "
         "sh -c 'while :; do date +%H:%M:%S.%N; sleep 0.1; done' "
         ">/dev/null 2>&1 &\n"
         "sleep 2\n"
         "echo scena-accesa\n")


def nella_sessione(comando, t=40):
    c = ("printf 'nicfio\\n' | sudo -S -p '' timeout 25 " + comando)
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                          capture_output=True, text=True, timeout=t).stdout.strip()


def scena_accendi():
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                    "cat > /tmp/b59-scena.sh && chmod +x /tmp/b59-scena.sh"],
                   input=SCENA, text=True, capture_output=True)
    return "scena-accesa" in nella_sessione("runuser -u prova -- /tmp/b59-scena.sh")


def scena_spegni():
    """⛔ Si chiama SEMPRE, anche se il banco e' caduto: quel che si apre sul
    desktop di qualcuno si chiude."""
    nella_sessione("pkill -u prova -f 'REMOTIX-SCENA|gnome-terminal' || true")


def registro(n=400):
    c = ("printf 'nicfio\\n' | sudo -S -p '' tail -n %d %s/registro.log"
         % (n, o.lavoro))
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                          capture_output=True, text=True).stdout


def posto_libero(quanto=60):
    """⛔ Il posto e' UNO: se la sessione di prima non e' ancora scaduta (il
    tempo morto di QUIC e' ~20 s), la nuova non entra e il banco misurerebbe
    una pagina che non si e' collegata."""
    t0 = time.time()
    while time.time() - t0 < quanto:
        r = registro(150)
        if "ne restano 0" in r or "l'ultima sessione di" in r:
            time.sleep(3)
            return True
        time.sleep(3)
    return False


def righe_pagina(chiave):
    fuori = []
    for r in registro(900).splitlines():
        if "dice:" not in r:
            continue
        d = urllib.parse.unquote(r.split("dice:", 1)[1]).strip()
        if chiave in d:
            fuori.append((r.split()[0], d))
    return fuori


def main():
    if not vivo():
        if not o.accendi:
            print("⛔ l'emulatore non risponde.  Rilancia con --accendi")
            return 2
        print("⏳ accendo l'emulatore…")
        if not accendi():
            print("⛔ l'emulatore non ha finito l'avvio")
            return 2
    print("⭐ emulatore: Android %s · Firefox %s"
          % ((adb("shell", "getprop", "ro.build.version.release") or "?").strip(),
             (adb("shell", "dumpsys", "package", "org.mozilla.firefox")
              or "").split("versionName=")[-1].split()[0] if "versionName=" in
             (adb("shell", "dumpsys", "package", "org.mozilla.firefox") or "")
             else "?"))

    if not scena_accendi():
        print("   ⚠ la scena non si e' accesa: il desktop restera' fermo e il "
              "banco misurerebbe il silenzio")
    posto_libero()
    adb("shell", "am", "force-stop", "org.mozilla.firefox")
    time.sleep(2)
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW",
        # ⛔ `disegno=mse`: il prodotto non prende piu' questa strada da solo
        #    (§7.18, Firefox per Android dichiarato non supportato).
        "-d", "https://%s:%d/?disegno=mse&v=%d" % (MACCHINA, o.porta, int(time.time())),
        "-n", "org.mozilla.firefox/org.mozilla.fenix.IntentReceiverActivity")
    time.sleep(12)
    # ⚠ Il certificato e' autofirmato: la prima volta va accettato, e dopo
    #   l'eccezione resta.  Le due voci si cercano per NOME, non a coordinate.
    if tocca("advancedButton"):
        time.sleep(2)
        tocca("advancedPanelAcceptButton")
        time.sleep(12)
    tocca("Not now")          # il pannello delle traduzioni
    time.sleep(2)

    adb("shell", "input", "tap", "540", "544"); time.sleep(1)
    adb("shell", "input", "text", "prova"); time.sleep(1)
    adb("shell", "input", "tap", "540", "747"); time.sleep(1)
    adb("shell", "input", "text", "prova2026"); time.sleep(1)
    if not tocca("vai"):
        print("⛔ non ho trovato il bottone «Collegati»")
        return 1
    time.sleep(6)
    tocca("save_cancel")      # «Salvare la password?» — no
    print("⏳ lascio girare %d s…" % o.secondi)
    time.sleep(o.secondi)

    # ⛔⭐ E L'INPUT SI PROVA, non si suppone: `[M]` 21 agosto 2026 il desktop
    #    si vedeva e non si comandava, perche' la tela — che riceve TUTTI i
    #    gesti — era stata nascosta per far posto al `<video>`.  ⇒ Si tocca lo
    #    schermo e si guardano le righe NUOVE del registro del server.
    prima = registro(500)
    adb("shell", "input", "tap", "540", "900")
    time.sleep(1)
    adb("shell", "input", "tap", "540", "700")
    time.sleep(3)
    viste = set(prima.splitlines())
    nuove = [r for r in registro(800).splitlines()
             if r not in viste and ("input id=" in r or "PUNTATORE" in r)]
    print("\n⭐ input: %d righe nuove nel registro del server" % len(nuove))
    if nuove:
        print("   ", nuove[-1][:150])

    with open(os.path.join(QUI, "07-b59-schermo.png"), "wb") as f:
        f.write(subprocess.run([ADB, "exec-out", "screencap", "-p"],
                               capture_output=True, timeout=60).stdout)
    print("   fotografia: %s" % os.path.join(QUI, "07-b59-schermo.png"))
    stato = righe_pagina("MSE: consegnati")
    conti = righe_pagina("dipinti ")
    print("\n══════════ CHE COSA HA DETTO LA PAGINA ══════════")
    for t, d in stato[-3:]:
        print(" ", t, d[:200])
    if not stato:
        print("  ⛔ nessuna riga `MISURA §7.18 MSE`: o la pagina non ha aperto la")
        print("     sessione, o non e' quella nuova (la cache del browser).")
        for t, d in conti[-2:]:
            print("   ", t, d[:180])
    guai = []
    if not nuove:
        guai.append("⛔ L'INPUT NON ARRIVA: due tocchi non hanno prodotto "
                    "nessuna riga nel registro del server")
    # ⛔⛔⭐ E IL GIUDIZIO NON SI DA' SUL CONTATORE `dipinti` — 21 agosto 2026.
    #
    # ⚠ Quel numero conta i richiami di `requestVideoFrameCallback`, che sui
    #   motori mobili sono **strozzati**: `[M]` 24 scatti in 40 secondi mentre
    #   il desktop si muoveva sotto gli occhi.  ⛔ Giudicando li', il banco
    #   dichiarava rosso un prodotto che dipingeva — due volte.
    # ⇒ Si giudica su quel che descrive DAVVERO lo stato del `<video>`: sta
    #   suonando?  sta cercando?  ha dati?  quanto e' indietro?  E il ritardo si
    #   guarda fra DUE letture, perche' un'immagine che avanza e una ferma hanno
    #   lo stesso aspetto in una fotografia sola.
    if len(stato) >= 2:
        def leggi(d):
            n = dict(x.split("=") for x in d.split() if "=" in x and "→" not in x)
            b = d.split("buffer=")[1].split()[0]
            fine = float(b.split("→")[1]) if "→" in b else None
            return {"fermo": n.get("fermo") == "true",
                    "cerca": n.get("cerca") == "true",
                    "pronto": int(n.get("pronto", 0)),
                    "tempo": float(n.get("tempo", 0)),
                    "buffer": fine,
                    "dipinti": int(d.split("dipinti")[1].split("·")[0])}
        a1, a2 = leggi(stato[-2][1]), leggi(stato[-1][1])
        if a2["fermo"]:
            guai.append("⛔ il `<video>` e' FERMO")
        if a2["cerca"]:
            guai.append("⛔ il `<video>` e' bloccato in una RICERCA")
        if a2["buffer"] is None:
            guai.append("⛔ il `<video>` non ha dati (buffer vuoto)")
        elif a2["buffer"] - a2["tempo"] > 3:
            guai.append("⛔ il `<video>` e' indietro di %.1f s dal bordo vivo"
                        % (a2["buffer"] - a2["tempo"]))
        if a2["tempo"] <= a1["tempo"] + 0.2:
            guai.append("⛔ il tempo del `<video>` NON AVANZA fra due letture "
                        "(%.2f → %.2f): l'immagine e' ferma"
                        % (a1["tempo"], a2["tempo"]))
        print("\n   indietro dal bordo vivo: %.2f s · avanzato di %.2f s fra "
              "due letture" % (a2["buffer"] - a2["tempo"] if a2["buffer"] else 0,
                               a2["tempo"] - a1["tempo"]))
    elif not stato:
        guai.append("⛔ la pagina non ha raccontato niente: sessione non aperta, "
                    "o pagina vecchia in cache")

    print("\n%s" % ("⛔ ROSSO: " + guai[0] if guai else "⭐ VERDE"))
    return 1 if guai else 0


try:
    _esito = main()
finally:
    # ⛔ E il posto si libera anche lui: la sessione dell'emulatore terrebbe
    #    occupato l'unico posto, e il banco dopo misurerebbe una pagina che non
    #    si e' potuta collegare.
    try:
        adb("shell", "am", "force-stop", "org.mozilla.firefox")
    except Exception:
        pass
    scena_spegni()
sys.exit(_esito)
