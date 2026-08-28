#!/usr/bin/env python3
"""07-b55 — L'INCOLLA DALL'UTENTE AL DESKTOP REMOTO, su WAYLAND.

    WLR_BACKENDS=headless cage -- sleep 3600 &        (crea `wayland-1`)
    WAY=wayland-1 python3 banchi/07-b55-incolla-wayland.py

⛔ PERCHE' ESISTE — 20 agosto 2026: *«su Firefox la clipboard da server a client
   funziona, il contrario no»*.  ⚠ Il difetto NON si vede in headless ne' su
   X11: si vede solo su **Wayland**, col testo copiato da **un'altra
   applicazione** — cioe' l'ambiente dell'utente.

Come: due Firefox sullo stesso compositore annidato.  Il primo copia (ed e'
«l'altra applicazione»), il secondo apre il prodotto e batte `Ctrl+V`.

⚠ E IL SUO LIMITE E' DICHIARATO: i tasti di Marionette sono SINTETICI, e Wayland
  consegna gli appunti solo a fronte di un evento d'input VERO (serve il
  *serial* del compositore).  ⇒ Un rosso di questo banco su quella casella non
  accusa il prodotto: dice che li' serve una tastiera vera.
  `[M]` Con la clipboard posseduta dallo STESSO browser (in-page copy) il verso
  funziona anche qui — vedi `07-b54 --wayland`."""
import importlib.util as iu, json, os, subprocess, sys, time
sp = iu.spec_from_file_location("m", "/home/nicfio/Documenti/REMOTIX/banchi/07-b46-marionette.py")
M = iu.module_from_spec(sp); sp.loader.exec_module(M)

WAY = os.environ.get("WAY", "wayland-1")
TESTO = "WAYLAND-copiato-da-un-altra-applicazione-%d" % int(time.time() % 10000)
os.environ["WAYLAND_DISPLAY"] = WAY
os.environ["MOZ_ENABLE_WAYLAND"] = "1"
os.environ.pop("DISPLAY", None)

def sessione_incolla():
    c = ("printf 'nicfio\\n' | sudo -S -p '' runuser -u prova -- sh -c "
         "'XDG_RUNTIME_DIR=/run/user/$(id -u prova) WAYLAND_DISPLAY=wayland-0 "
         "timeout 8 wl-paste -n'")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "192.168.0.2", c],
                       capture_output=True, text=True, timeout=40)
    return (r.stdout or "").strip()

print("⏳ 1/3 · l'ALTRA applicazione: un secondo Firefox che possiede la clipboard")
pa, ma, profa = M.accendi(porta=2911, headless=False, largo=800, alto=600)
try:
    ma.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
    ma.vai("data:text/html,<textarea id=t style='width:400px;height:100px'></textarea>")
    time.sleep(2)
    ma.js("const t=document.getElementById('t'); t.value=arguments[0]; t.focus(); t.select(); return true;", [TESTO])
    ma.chiama("WebDriver:PerformActions", {"actions": [{
        "type": "key", "id": "k",
        "actions": [{"type": "keyDown", "value": ""},
                    {"type": "keyDown", "value": "c"},
                    {"type": "pause", "duration": 80},
                    {"type": "keyUp", "value": "c"},
                    {"type": "keyUp", "value": ""}]}]})
    time.sleep(1)
    print("   copiato:", TESTO)

    print("⏳ 2/3 · il PRODOTTO in un Firefox Wayland separato")
    pb, mb, profb = M.accendi(porta=2912, headless=False, largo=1200, alto=800)
    try:
        mb.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        mb.vai("https://192.168.0.2:7730/")
        mb.js("""document.getElementById('utente').value='prova';
                 document.getElementById('parola').value='prova2026';
                 document.getElementById('vai').click(); return true;""")
        t0 = time.time()
        while time.time() - t0 < 45:
            if mb.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.5)
        print("   schermo:", mb.js("return document.body.dataset.schermo || '(spento)'")["value"])
        time.sleep(2)
        print("⏳ 3/3 · Ctrl+V sulla pagina, come fa l'utente")
        mb.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "key", "id": "k",
            "actions": [{"type": "keyDown", "value": ""},
                        {"type": "keyDown", "value": "v"},
                        {"type": "pause", "duration": 80},
                        {"type": "keyUp", "value": "v"},
                        {"type": "keyUp", "value": ""}]}]})
        time.sleep(3.5)
        diario = mb.js("""const r=document.getElementById('registro');
            return (r?r.textContent:"").split("\\n").filter(function(x){
              return x.indexOf("appunti")>=0 || x.indexOf("paste")>=0
                  || x.indexOf("readText")>=0 || x.indexOf("Ctrl+V")>=0;}).slice(-8);""")["value"]
        stato = mb.js("""const A=window.REMOTIX&&window.REMOTIX.appunti;
            return A?{conti:A.conti, mio_id:A.mio_id}:null;""")["value"]
        print("\n--- diario della pagina ---")
        for r in diario: print("  ", r[:170])
        print("--- stato:", json.dumps(stato))
        ricevuto = sessione_incolla()
        print("--- il desktop remoto ha:", repr(ricevuto[:80]))
        print("\n⇒ VERSO client → sessione:",
              "⭐ FUNZIONA" if ricevuto == TESTO else "⛔ NON FUNZIONA")
    finally:
        M.spegni(pb, profb)
finally:
    M.spegni(pa, profa)
