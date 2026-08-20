#!/usr/bin/env python3
"""07-b52 — DOVE SI ROMPONO I PIXEL, sul PRODOTTO e non su un banco sintetico.

    python3 banchi/07-b52-dove-si-rompono-i-pixel.py /tmp/dove

⛔ PERCHE' ESISTE — 20 agosto 2026.  Il banco `07-b48` aveva scagionato il
   `VideoDecoder` su un flusso **fabbricato apposta**, e la §4.9 aveva concluso
   che la colpa fosse tutta della tela 2D.  ⭐ Curata quella, Chrome e' tornato
   pulito **e Firefox no**: erano DUE difetti sovrapposti, ed e' per questo che
   ogni ipotesi singola sembrava smentita.

⭐ Questo banco non fabbrica niente: muove la scena VERA (la panoramica di GNOME
   che si apre e si chiude venti volte) e prende TRE immagini dello stesso
   istante — i pixel in mano al codificatore, i byte spediti, la tela del
   browser.  ⇒ Il primo dei tre che porta i blocchi e' l'imputato.

`[M]` L'esito del 20 agosto, con AV1: cattura pulita · flusso pulito, riletto da
`ffmpeg/dav1d` su 22 delta della stessa catena · **Chrome pulito** · ⛔ **Firefox
a blocchi**, con `dipinti == consegnati` e zero errori.  ⇒ Il suo decodificatore
AV1.  Rifatto con H.264: **nessun blocco**.

⚠ Chiede lo SCATTO al server (`SIGUSR1`), quindi vuole `--rilievo` acceso, e
  muove il desktop di «prova»: non si lancia mentre l'utente sta guardando.

Dove si rompono i pixel, SUL PRODOTTO: cattura, codificatore o browser?

Tiene il desktop in movimento (la panoramica che si apre e si chiude), fa lo
SCATTO al server e tira giu' nello stesso istante:
  · `scatto-ingresso.bgrx`  i pixel che il codificatore ha in mano
  · `scatto-flusso.obu`     i byte spediti, dalla chiave in poi
  · la TELA del browser in PNG
⇒ Tre immagini dello stesso momento, e il primo che ha i blocchi e' l'imputato.
"""
import importlib.util as iu, base64, os, subprocess, sys, time
sp = iu.spec_from_file_location("m", "/home/nicfio/Documenti/REMOTIX_V2/banchi/07-b46-marionette.py")
M = iu.module_from_spec(sp); sp.loader.exec_module(M)
FUORI = sys.argv[1]; os.makedirs(FUORI, exist_ok=True)
SSH = ["ssh", "-o", "BatchMode=yes", "192.168.0.2"]
LAV = "/media/REMOTIX/tmp/07-appunti"

def remoto(c):
    return subprocess.run(SSH + ["printf 'nicfio\\n' | sudo -S -p '' " + c],
                          capture_output=True, text=True).stdout

p, m, prof = M.accendi(porta=2891, headless=True, largo=1600, alto=1000)
try:
    m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
    m.misura(1600, 1000); m.vai("https://192.168.0.2:7730/")
    m.js("""document.getElementById('utente').value='prova';
            document.getElementById('parola').value='prova2026';
            document.getElementById('vai').click(); return true;""")
    t0 = time.time()
    while time.time() - t0 < 40:
        if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
            break
        time.sleep(0.5)
    time.sleep(3)
    r = m.js("""const t=document.getElementById('schermo');
                const b=t.getBoundingClientRect();
                return [b.left,b.top,b.width,b.height,t.width,t.height];""")["value"]
    print("buffer:", r[4], "x", r[5])

    def clic(dx, dy):
        px = r[0] + dx * r[2] / r[4]; py = r[1] + dy * r[3] / r[5]
        m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
            "actions": [{"type": "pointerMove", "duration": 40, "x": int(px), "y": int(py)},
                        {"type": "pointerDown", "button": 0},
                        {"type": "pause", "duration": 60},
                        {"type": "pointerUp", "button": 0}]}]})

    # ⭐ LO SCATTO SI ARMA SUBITO, e la scena si muove DOPO: cosi' il flusso
    #   registrato e' la STESSA catena lunga di delta che vede il browser.
    remoto("systemctl kill --kill-whom=main -s SIGUSR1 remotix-7730.service")
    for i in range(20):
        clic(40, 12); time.sleep(0.9)
    print("scena mossa; contatori:", m.js(
        "const x=REMOTIX.schermo; return [x.conti.consegnati, x.conti.dipinti,"
        " x.conti.tardive, x.conti.buchi, x.errori.slice(-2)];")["value"])

    remoto("systemctl kill --kill-whom=main -s SIGUSR2 remotix-7730.service")
    time.sleep(1)

    # 3. la TELA, nello stesso momento
    d = m.js("const t=document.getElementById('schermo');"
             "try{return t.toDataURL('image/png');}catch(e){return 'ERRORE '+e;}")["value"]
    if d.startswith("data:image"):
        open(os.path.join(FUORI, "tela.png"), "wb").write(
            base64.b64decode(d.split(",", 1)[1]))
        print("tela salvata")
    print(remoto("tail -n 200 %s/registro.log | grep SCATTO | tail -4" % LAV))
finally:
    M.spegni(p, prof)

for f in ("scatto-ingresso.bgrx", "scatto-flusso.obu", "scatto-uscita.bgrx"):
    d = subprocess.run(SSH + ["printf 'nicfio\\n' | sudo -S -p '' cat %s/rilievo/%s" % (LAV, f)],
                       capture_output=True)
    open(os.path.join(FUORI, f), "wb").write(d.stdout)
    print(f, len(d.stdout), "byte")
