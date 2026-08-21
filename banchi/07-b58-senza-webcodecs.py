#!/usr/bin/env python3
"""07-b58 — REMOTIX su un browser SENZA WebCodecs, cioe' Firefox per Android.

    python3 banchi/07-b58-senza-webcodecs.py

⛔ PERCHE' ESISTE — 21 agosto 2026, e la ragione e' una frase dell'utente:
   *«Non e' cambiato assolutamente nulla, e mi stai facendo perdere tempo con
   test inutili»*.  ⇒ Aveva ragione: gli ho fatto provare tre volte sul telefono
   quel che potevo provare qui.

⭐ `dom.media.webcodecs.enabled = false` toglie `VideoDecoder` **e**
   `AudioDecoder` a un Firefox da tavolo: `[M]` `typeof VideoDecoder ===
   "undefined"`, esattamente quel che dichiara Firefox per Android.  ⇒ La strada
   di §7.18 si prova QUI, e sul telefono ci si va una volta sola, alla fine.

⚠ E quel che questo banco NON riproduce si dichiara: le regole di risparmio
  energetico dei motori mobili — un `<video>` piccolo o fuori dalla vista che
  non viene presentato.  E' proprio la trappola che ha fatto fallire la sonda
  tre volte, e per quella l'ultima parola resta del telefono.
"""
import argparse, importlib.util as iu, json, os, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
MACCHINA = "192.168.0.2"


def _mod(nome, file):
    s = iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = iu.module_from_spec(s); s.loader.exec_module(m); return m


M = _mod("marionette", "07-b46-marionette.py")

a = argparse.ArgumentParser()
a.add_argument("--porta", type=int, default=7730)
a.add_argument("--lavoro", default="/media/REMOTIX/tmp/07-appunti")
a.add_argument("--schermo", default=":96")
a.add_argument("--secondi", type=int, default=25)
o = a.parse_args()
URL = "https://%s:%d/" % (MACCHINA, o.porta)

STATO = """
  const S = window.REMOTIX && window.REMOTIX.schermo;
  const v = document.getElementById('tela-video');
  return { webcodecs: typeof VideoDecoder !== 'undefined',
           conti: S ? S.conti : null,
           ritardo: S ? S.mse_ritardo : null,
           video: v ? { l: v.videoWidth, a: v.videoHeight,
                        t: +(v.currentTime || 0).toFixed(2),
                        fermo: v.paused, pronto: v.readyState,
                        errore: v.error ? v.error.code : null } : null };
"""

RIGHE = """
  const x = document.getElementById('registro');
  return x ? x.textContent.split('\\n').filter(function (l) {
    return l.indexOf('7.18') >= 0 || l.indexOf('sonda video') >= 0
        || l.indexOf('MSE') >= 0 || l.indexOf('WebCodecs') >= 0;
  }).slice(-8) : [];
"""


# ⛔⛔ IL DESKTOP DEV'ESSERE VIVO, o il banco misura il silenzio.
#
# ⚠ Muovere il puntatore NON basta: il cursore viaggia su un canale suo
#   (`MSG_CURSORE`) e i pixel del desktop non cambiano.  ⇒ `[M]` un giro intero
#   con un fotogramma solo, e il banco stava per dichiarare «non dipinge» di una
#   strada che dipingeva quel che c'era.
# ⭐ Si apre un terminale che scorre: righe nuove ogni decimo di secondo, cioe'
#   fotogrammi veri per tutta la durata della prova.
SCENA = ("#!/bin/sh\n"
         "U=$(id -u prova)\n"
         "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
         "export DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus\n"
         "pkill -u prova -f 'REMOTIX-SCENA' 2>/dev/null\n"
         "setsid gnome-terminal --title=REMOTIX-SCENA -- "
         "sh -c 'while :; do date +%%H:%%M:%%S.%%N; sleep 0.1; done' "
         ">/dev/null 2>&1 &\n"
         "sleep 2\n"
         "echo scena-accesa\n")


def accendi_la_scena():
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                    "cat > /tmp/b58.sh && chmod +x /tmp/b58.sh"],
                   input=SCENA, text=True, capture_output=True)
    c = ("printf 'nicfio\\n' | sudo -S -p '' timeout 20 runuser -u prova -- "
         "/tmp/b58.sh 2>&1")
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                          capture_output=True, text=True, timeout=40).stdout.strip()


def spegni_la_scena():
    c = ("printf 'nicfio\\n' | sudo -S -p '' pkill -u prova -f REMOTIX-SCENA")
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                   capture_output=True, text=True)


def registro(n=200):
    c = ("printf 'nicfio\\n' | sudo -S -p '' tail -n %d %s/registro.log"
         % (n, o.lavoro))
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                          capture_output=True, text=True).stdout


def main():
    # ⛔ La preferenza e' del BANCO, non del prodotto: serve a rendere questo
    #    Firefox indistinguibile — per quel che ci riguarda — da quello di
    #    Android.  ⚠ E si verifica che abbia fatto effetto, invece di crederci.
    scena = accendi_la_scena()
    if "scena-accesa" not in scena:
        print("   ⚠ la scena non si e' accesa (%s): il desktop restera' fermo "
              "e il banco misurerebbe il silenzio" % scena[:60])
    p, m, prof = M.accendi(porta=2884, headless=False, largo=1280, alto=800,
                           schermo=o.schermo,
                           profilo_prefs={"dom.media.webcodecs.enabled": False})
    v = {"guai": []}
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(1280, 800)
        m.vai(URL)
        time.sleep(3)
        if m.js("return typeof VideoDecoder")["value"] != "undefined":
            v["guai"].append("⛔ BANCO: WebCodecs c'e' ancora, la preferenza non "
                             "ha fatto effetto: non si sta misurando niente")
            return v
        m.js("""document.getElementById('utente').value='prova';
                document.getElementById('parola').value='prova2026';
                document.getElementById('vai').click(); return true;""")
        t0 = time.time()
        acceso = False
        while time.time() - t0 < 60:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                acceso = True
                break
            time.sleep(1)
        v["schermo_acceso"] = acceso
        if not acceso:
            v["guai"].append("⛔ la sessione non si e' aperta in 60 s")
        # ⭐ Il desktop dev'essere VIVO, o non arrivano fotogrammi e il banco
        #   misurerebbe il silenzio.
        # ⛔ E si MUOVE IL PUNTATORE, non si battono tasti: una lettera su un
        #    desktop senza fuoco non cambia un pixel, e il banco misurerebbe il
        #    silenzio chiamandolo «non dipinge».
        for k in range(o.secondi):
            passi = []
            for j in range(10):
                passi.append({"type": "pointerMove", "duration": 30,
                              "x": 200 + ((k * 7 + j * 60) % 900),
                              "y": 150 + ((k * 11 + j * 40) % 500)})
            m.chiama("WebDriver:PerformActions", {"actions": [{
                "type": "pointer", "id": "mouse",
                "parameters": {"pointerType": "mouse"}, "actions": passi}]})
            time.sleep(0.6)
        v["stato"] = m.js(STATO)["value"]
        v["righe"] = m.js(RIGHE)["value"]
    finally:
        M.spegni(p, prof)
        spegni_la_scena()

    c = (v.get("stato") or {}).get("conti") or {}
    if not c.get("consegnati"):
        v["guai"].append("⛔ nessun fotogramma consegnato: la sessione non ha "
                         "portato video")
    elif not c.get("dipinti"):
        v["guai"].append("⛔ %d fotogrammi consegnati e ZERO presentati dal "
                         "`<video>`: la strada MSE non dipinge"
                         % c["consegnati"])
    return v


v = main()
fuori = os.path.join(QUI, "07-b58-esiti.json")
with open(fuori, "w", encoding="utf-8") as f:
    json.dump(v, f, ensure_ascii=False, indent=1)
print("\n══════════ VERDETTO ══════════")
st = v.get("stato") or {}
c = st.get("conti") or {}
print("WebCodecs: %s · schermo acceso: %s" % (st.get("webcodecs"), v.get("schermo_acceso")))
print("consegnati %s · dipinti %s · buchi %s · ritardo %s ms · video %s"
      % (c.get("consegnati"), c.get("dipinti"), c.get("buchi"),
         st.get("ritardo"), st.get("video")))
for l in v.get("righe") or []:
    print("   ", l[:190])
for g in v["guai"]:
    print(g)
print("\n%s — %s" % ("⛔ ROSSO" if v["guai"] else "⭐ VERDE", fuori))
sys.exit(1 if v["guai"] else 0)
