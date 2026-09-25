#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f003 — F-003 L'AGGIORNAMENTO DELLO SCHERMO

    python3 15-f003-lo-schermo-si-aggiorna.py --scatola kde --browser chrome [--guasto]
    python3 15-f003-lo-schermo-si-aggiorna.py --certifica

La scena: la finestra nota di C21 (`firefox-esr` NORMALE nella sessione, pagina
a fondo CIANO con un riquadro GIALLO, 45 % x 55 % dello schermo, misura fissata
nel profilo) — con in piu' un CONTATORE: 15 caselle bianche/nere in basso nella
pagina che scrivono in binario n = floor(Date.now() / 200 ms) mod 4096, cioe'
la pagina CAMBIA ogni 200 ms.  (Guardia bianca, guardia nera, 12 bit, parita'.)
⭐ Il contatore e' un orologio: `firefox-esr` nella scatola e il banco girano
sulla STESSA macchina (podman, stesso orologio), quindi ogni fotografia dice
anche QUANTO e' vecchia l'immagine che mostra.

F-003, quattro parti in fila (come un utente vero), tutte dalla FOTOGRAFIA
della tela a piena risoluzione:
  apre     prima la foto non ha ciano; si apre la finestra ⇒ la foto la mostra
           (il rettangolo ciano, largo almeno il 70 % di quel che si e' chiesto)
  cambia   6 s di fotografie una dopo l'altra: ogni foto legge il contatore, e
           l'immagine non dev'essere piu' vecchia di TETTO_MS (1 s) rispetto
           all'istante in cui la foto e' stata CHIESTA (la misura favorisce il
           prodotto: se esce vecchia, lo e' di sicuro); nessuna foto uguale alla
           precedente se fra le due sono passati >= 400 ms; almeno 3 valori
           diversi; al massimo un quarto delle foto illeggibili
  sposta   si trascina la finestra per la BARRA DEL TITOLO col mouse del browser
           (eventi veri: Marionette / CDP), di +320,+120 px: la barra non sta
           nello stesso posto su tutti i desktop (Firefox con le schede nella
           barra, o la barra del desktop sopra), quindi si prova una scala di
           prese sopra il ciano, al centro, e ci si ferma alla prima che sposta
           ⇒ la foto mostra il ciano ALTROVE (spostato di almeno 100 px), della
           stessa misura (±8 px)
  chiude   si chiude la finestra (`firefox-esr` terminato nella sessione)
           ⇒ entro 10 s la foto non ha piu' ciano

GUASTO («la foto vecchia»): ogni parte si rigiudica sulla foto di PRIMA del
cambiamento — l'apertura sulla foto senza finestra, i cambi rapidi sulla PRIMA
foto ripetuta con gli istanti veri, lo spostamento sulla foto di prima del
gesto, la chiusura sull'ultima foto con la finestra aperta.  Tutt'e quattro
devono dare rosso.

⚠ Il giudizio di «cambia» e' un TETTO sul ritardo (1 s), non la latenza: la
  latenza la misura la fase 16.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

C21 = S.C21
F011 = S._carica("f011", os.path.join(S.QUI, "15-f011-la-tela-all-attacco.py"))
FUNZIONI = ("F-003",)

PERIODO_MS = 200
BIT = 12
MODULO = 1 << BIT
CELLE = 2 + BIT + 1                 # guardia bianca, guardia nera, 12 bit, parita'
CELLA_X0, CELLA_PASSO, CELLA_L = 0.03, 0.063, 0.05      # frazioni della pagina
CELLA_Y0, CELLA_A = 0.62, 0.24
TETTO_MS = 1000.0                   # l'immagine non piu' vecchia di cosi'
RAPIDI_S = 6.0
FOTO_MIN = 8
RAPIDI_MAX_S = 30.0
FERMA_MS = 400.0                    # due foto a questa distanza devono differire
SPOSTA = (320, 120)                 # il trascinamento, in pixel del desktop
PRESE_DY = (-62, -70, -54, -80, -100, -110, -46, -90, -120, -130)
SPOSTATA_MIN = 100
STESSA_MISURA = 8
CHIUSA_S = 10.0
APERTURA_S = 120.0                # [M] 24 set 2026, carico 51: firefox-esr ci mette ~50 s a comparire
CIANO_ASSENTE = 0.001               # quota di pixel ciani sotto cui «non c'e'»

PAGINA = C21.PAGINA.replace("REMOTIX C21", "REMOTIX F-003") + r"""
<script>
(function () {
  const N = %(celle)d, B = %(bit)d, celle = [];
  for (let i = 0; i < N; i++) {
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;top:%(y0)s%%;height:%(a)s%%;width:%(l)s%%;left:'
      + (%(x0)s + i * %(passo)s) + '%%;background:#000';
    document.body.appendChild(d); celle.push(d);
  }
  let ultimo = -1;
  function giro() {
    const n = Math.floor(Date.now() / %(periodo)d) %% %(modulo)d;
    if (n === ultimo) return;
    ultimo = n;
    const b = [1, 0];
    let p = 0;
    for (let k = B - 1; k >= 0; k--) { const v = (n >> k) & 1; b.push(v); p ^= v; }
    b.push(p);
    for (let i = 0; i < N; i++) celle[i].style.background = b[i] ? '#fff' : '#000';
  }
  giro();
  setInterval(giro, 20);
})();
</script>
""" % {"celle": CELLE, "bit": BIT, "y0": CELLA_Y0 * 100, "a": CELLA_A * 100,
       "l": CELLA_L * 100, "x0": CELLA_X0 * 100, "passo": CELLA_PASSO * 100,
       "periodo": PERIODO_MS, "modulo": MODULO}


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def bit_di(n):
    b = [1, 0]
    p = 0
    for k in range(BIT - 1, -1, -1):
        v = (n >> k) & 1
        b.append(v)
        p ^= v
    return b + [p]


def centri_celle(rett):
    """rett = [x0, y0, x1, y1] della pagina nella foto ⇒ [(x, y, mezza_l, mezza_a)]."""
    x0, y0, x1, y1 = rett
    w, h = x1 - x0 + 1, y1 - y0 + 1
    y = y0 + (CELLA_Y0 + CELLA_A / 2) * h
    return [(x0 + (CELLA_X0 + i * CELLA_PASSO + CELLA_L / 2) * w, y,
             CELLA_L * w * 0.25, CELLA_A * h * 0.25) for i in range(CELLE)]


def leggi_contatore(im, rett):
    """(n | None, motivo) dal contatore della pagina nella foto `im` (PIL RGB)."""
    from PIL import ImageStat
    b = []
    for x, y, ml, ma in centri_celle(rett):
        box = (int(x - ml), int(y - ma), int(x + ml) + 1, int(y + ma) + 1)
        m = ImageStat.Stat(im.crop(box).convert("L")).mean[0]
        if m < 70:
            b.append(0)
        elif m > 185:
            b.append(1)
        else:
            return None, "casella a (%d,%d) grigia (%.0f): non e' ne' bianca ne' nera" % (x, y, m)
    if b[0] != 1 or b[1] != 0:
        return None, "le guardie non ci sono (%s): il contatore non e' dove dico" % b[:2]
    if sum(b[2:2 + BIT]) % 2 != b[-1]:
        return None, "parita' sbagliata: %s" % "".join(map(str, b))
    n = 0
    for v in b[2:2 + BIT]:
        n = (n << 1) | v
    return n, ""


def ritardo_ms(n, t_ms):
    """Quanto e' vecchia, all'istante `t_ms` (ms dell'epoca), l'immagine che mostra
    `n`: t - (fine del periodo di n).  Negativo = n viene dal futuro (±1 periodo
    = orologio)."""
    pieno = int(t_ms // PERIODO_MS)
    k = (pieno - n) % MODULO
    if k > MODULO // 2:
        k -= MODULO
    n_pieno = pieno - k
    return t_ms - (n_pieno + 1) * PERIODO_MS


def giudica_rapidi(letture):
    """letture = [(t_prima_ms, t_dopo_ms, n | None, motivo)] ⇒ (esito, motivo, dettagli)."""
    if len(letture) < 4:
        return S.BLOCKED, "solo %d foto: troppo poche per giudicare" % len(letture), []
    righe, guai = [], []
    buone = [(tp, td, n) for tp, td, n, _m in letture if n is not None]
    illeggibili = len(letture) - len(buone)
    for tp, td, n, m in letture:
        if n is None:
            righe.append("illeggibile: %s" % m)
            continue
        r = ritardo_ms(n, tp)
        righe.append("n=%d ritardo %+.0f ms" % (n, r))
        if r > TETTO_MS:
            guai.append("foto vecchia di %.0f ms (n=%d, tetto %.0f)" % (r, n, TETTO_MS))
        if ritardo_ms(n, td) < -PERIODO_MS:
            guai.append("n=%d viene dal futuro (%.0f ms): orologio?" % (n, ritardo_ms(n, td)))
    for (tp0, _td0, n0), (tp1, _td1, n1) in zip(buone, buone[1:]):
        if n1 == n0 and tp1 - tp0 >= FERMA_MS:
            guai.append("due foto a %.0f ms di distanza mostrano lo stesso n=%d: FERMA"
                        % (tp1 - tp0, n0))
    diversi = len({n for _a, _b, n in buone})
    if illeggibili * 4 > len(letture):
        guai.append("%d foto su %d col contatore illeggibile" % (illeggibili, len(letture)))
    if diversi < 3:
        guai.append("solo %d valori diversi in %d foto" % (diversi, len(letture)))
    if guai:
        return S.FAIL, "; ".join(guai[:4]) + (" (+%d)" % (len(guai) - 4) if len(guai) > 4
                                               else ""), righe
    rit = [ritardo_ms(n, tp) for tp, _td, n in buone]
    return S.PASS, ("%d foto in %.1f s, %d valori diversi, ritardo massimo %.0f ms (tetto %.0f)"
                    % (len(letture), (letture[-1][0] - letture[0][0]) / 1000.0, diversi,
                       max(rit), TETTO_MS)), righe


def frazione_ciano(im):
    p = im.resize((max(1, im.size[0] // 4), max(1, im.size[1] // 4)))
    px = list(p.getdata())
    n = sum(1 for q in px if C21._vicino(q, C21.CIANO))
    return n / float(len(px))


CAMBIATO_MIN = 0.005                # quota di pixel cambiati: «e' comparso qualcosa»


def cambiato(im_a, im_b):
    """La quota di pixel (a 1/4) che differiscono di piu' di 40 in un canale."""
    if im_a.size != im_b.size:
        return 1.0
    from PIL import ImageChops
    w, h = im_a.size
    d = ImageChops.difference(im_a, im_b).resize((max(1, w // 4), max(1, h // 4)))
    px = list(d.getdata())
    return sum(1 for q in px if max(q) > 40) / float(len(px))


def trova(im):
    """La finestra di prova nella foto (`C21.trova_finestra`): (dict | None, motivo)."""
    w, h = im.size
    f, m = C21.trova_finestra(w, h, list(im.getdata()), passo=max(1, w // 960))
    if f:
        f["foto"] = [w, h]
        f["rett"] = [f["ciano"][0], f["ciano"][1], f["destro"], f["ciano"][3]]
    return f, m


def giudica_apertura(f, largo_px):
    if not f:
        return S.FAIL, "la finestra aperta non si vede nella foto"
    l = f["rett"][2] - f["rett"][0] + 1
    if l < 0.7 * largo_px:
        return S.FAIL, "il ciano c'e' ma e' largo %d px (chiesti %d)" % (l, largo_px)
    return S.PASS, "la finestra si vede: ciano %s" % f["rett"]


def giudica_spostamento(r0, r1):
    """r0, r1 = [x0,y0,x1,y1] nella foto (o r1 None) ⇒ (esito, motivo)."""
    if not r1:
        return S.FAIL, "dopo il gesto la finestra non si vede piu'"
    dx, dy = r1[0] - r0[0], r1[1] - r0[1]
    dl = (r1[2] - r1[0]) - (r0[2] - r0[0])
    da = (r1[3] - r1[1]) - (r0[3] - r0[1])
    if abs(dl) > STESSA_MISURA or abs(da) > STESSA_MISURA:
        return S.FAIL, "la finestra ha cambiato misura (%+d,%+d): non e' uno spostamento" % (dl, da)
    if (dx * dx + dy * dy) ** 0.5 < SPOSTATA_MIN:
        return S.FAIL, "la finestra e' ferma (%+d,%+d px)" % (dx, dy)
    return S.PASS, "la finestra e' spostata di (%+d,%+d) px, stessa misura" % (dx, dy)


def giudica_chiusura(quota):
    if quota < CIANO_ASSENTE:
        return S.PASS, "nella foto non c'e' piu' ciano (%.3f %%)" % (100 * quota)
    return S.FAIL, "la finestra chiusa si vede ancora: ciano sul %.1f %% della foto" % (100 * quota)


def complessivo(parti):
    es = [e for _p, e, _m in parti]
    return S.FAIL if S.FAIL in es else (S.BLOCKED if S.BLOCKED in es else S.PASS)


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE
# ═══════════════════════════════════════════════════════════════════════════
def _foto_finta(n, rett=(100, 80, 899, 579), w=1000, h=700, fondo=(40, 40, 90)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), fondo)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = rett
    d.rectangle(rett, fill=C21.CIANO)
    pw, ph = x1 - x0 + 1, y1 - y0 + 1
    d.rectangle((x0 + 0.06 * pw, y0 + 0.08 * ph, x0 + 0.40 * pw, y0 + 0.38 * ph), fill=C21.GIALLO)
    for i, v in enumerate(bit_di(n)):
        cx = x0 + (CELLA_X0 + i * CELLA_PASSO) * pw
        cy = y0 + CELLA_Y0 * ph
        d.rectangle((cx, cy, cx + CELLA_L * pw, cy + CELLA_A * ph),
                    fill=(255, 255, 255) if v else (0, 0, 0))
    return im


def certifica():
    guai = []

    def ok(c, cosa):
        print("%s %s" % ("⭐" if c else "⛔", cosa))
        if not c:
            guai.append(cosa)
    for n in (0, 1, 1234, 4095):
        im = _foto_finta(n)
        f, m = trova(im)
        ok(f is not None, "la finestra finta si trova (%s)" % (f["rett"] if f else m))
        v, m = leggi_contatore(im, f["rett"]) if f else (None, m)
        ok(v == n, "il contatore %d si legge %s %s" % (n, v, m))
    im = _foto_finta(77)
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle((100, 400, 899, 579), fill=(128, 128, 128))
    ok(leggi_contatore(im, [100, 80, 899, 579])[0] is None, "contatore coperto ⇒ illeggibile")
    t = 1_790_000_000_000.0
    n = int(t // PERIODO_MS) % MODULO
    ok(abs(ritardo_ms(n, t + 150) - (-50)) < 1e-6, "ritardo nello stesso periodo: -50 ms")
    ok(abs(ritardo_ms((n - 5) % MODULO, t) - 800) < 1e-6, "ritardo di 5 periodi: 800 ms")
    vive = [(t + i * 700, t + i * 700 + 300, int((t + i * 700 - 150) // PERIODO_MS) % MODULO, "")
            for i in range(9)]
    e, m, _ = giudica_rapidi(vive)
    ok(e == S.PASS, "cambi rapidi veri ⇒ PASS (%s)" % m)
    ferme = [(tp, td, vive[0][2], "") for tp, td, _n, _m in vive]
    e, m, _ = giudica_rapidi(ferme)
    ok(e == S.FAIL, "la prima foto ripetuta (guasto) ⇒ FAIL (%s)" % m[:90])
    lente = [(tp, td, int((tp - 1500) // PERIODO_MS) % MODULO, "") for tp, td, _n, _m in vive]
    e, m, _ = giudica_rapidi(lente)
    ok(e == S.FAIL, "immagini vecchie di 1,5 s ⇒ FAIL")
    e, _m, _ = giudica_rapidi(vive[:2])
    ok(e == S.BLOCKED, "due foto sole ⇒ BLOCKED")
    ok(giudica_spostamento([10, 10, 500, 400], [330, 130, 820, 520])[0] == S.PASS, "spostata ⇒ PASS")
    ok(giudica_spostamento([10, 10, 500, 400], [10, 10, 500, 400])[0] == S.FAIL, "ferma ⇒ FAIL")
    ok(giudica_spostamento([10, 10, 500, 400], [10, 10, 820, 400])[0] == S.FAIL,
       "allargata ⇒ FAIL (non e' uno spostamento)")
    from PIL import Image
    ok(giudica_chiusura(frazione_ciano(Image.new("RGB", (400, 300), (40, 40, 90))))[0] == S.PASS,
       "niente ciano ⇒ chiusa")
    ok(giudica_chiusura(frazione_ciano(_foto_finta(3)))[0] == S.FAIL, "ciano ⇒ non chiusa")
    ok(giudica_apertura(None, 800)[0] == S.FAIL, "niente finestra ⇒ apertura FAIL")
    print("⭐ certificazione verde" if not guai else "⛔ %d guai" % len(guai))
    return 0 if not guai else 1


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA PAGINA E NELLA SCATOLA
# ═══════════════════════════════════════════════════════════════════════════
JS_OSSERVA = r"""
(function () {
  if (window.__F003__) return;
  const C = window.__F003__ = { giu: 0, su: 0, premuti: 0 };
  addEventListener('mousedown', function () { C.giu++; }, true);
  addEventListener('mouseup', function () { C.su++; }, true);
  addEventListener('pointermove', function (e) { if (e.buttons & 1) C.premuti++; }, true);
})();
"""
JS_AZZERA = "const C=window.__F003__; if(!C) return false; C.giu=0; C.su=0; C.premuti=0; return true;"
JS_CONTA = r"""
const C = window.__F003__;
const st = window.REMOTIX && REMOTIX.input_classico ? REMOTIX.input_classico.stato() : null;
return C ? { giu: C.giu, su: C.su, premuti: C.premuti,
             spedito: st ? st.ultimo_spedito : null } : null;
"""
PASSI_GESTO = 16


def trascina(g, geo, X, Y, DX, DY):
    """Pulsante sinistro giu' su (X,Y) del desktop, trascinato di (DX,DY), su."""
    punti = [C21.dal_desktop_al_vetro(geo, X + DX * i / float(PASSI_GESTO),
                                      Y + DY * i / float(PASSI_GESTO))
             for i in range(PASSI_GESTO + 1)]
    if hasattr(g, "cdp"):
        c = g.cdp.chiama
        x0, y0 = punti[0]
        c("Input.dispatchMouseEvent", type="mouseMoved", x=x0, y=y0)
        time.sleep(0.15)
        c("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left",
          buttons=1, clickCount=1)
        time.sleep(0.2)
        for x, y in punti[1:]:
            c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="left", buttons=1)
            time.sleep(0.03)
        time.sleep(0.2)
        x, y = punti[-1]
        c("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
          buttons=0, clickCount=1)
        return
    az = [{"type": "pointerMove", "x": int(round(punti[0][0])), "y": int(round(punti[0][1])),
           "origin": "viewport", "duration": 0},
          {"type": "pause", "duration": 150}, {"type": "pointerDown", "button": 0},
          {"type": "pause", "duration": 200}]
    for x, y in punti[1:]:
        az += [{"type": "pointerMove", "x": int(round(x)), "y": int(round(y)),
                "origin": "viewport", "duration": 0}, {"type": "pause", "duration": 30}]
    az += [{"type": "pause", "duration": 200}, {"type": "pointerUp", "button": 0}]
    g._azioni([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


def prepara_la_casa(s, largo, alto):
    """La pagina di F-003 al posto di quella di C21 (stesso nome di file: cosi'
    `C21.accendi_la_finestra` la apre), e il profilo di Firefox di C21."""
    import base64
    b = lambda t: base64.b64encode(t.encode()).decode()       # noqa: E731
    return s.sc.dentro(
        "set -e; h=/home/%(c)s; mkdir -p $h/%(p)s; echo %(pag)s | base64 -d > $h/%(f)s; "
        "echo %(pref)s | base64 -d > $h/%(p)s/user.js; "
        "echo %(xul)s | base64 -d > $h/%(p)s/xulstore.json; chown -R %(c)s: $h/%(p)s $h/%(f)s; "
        "echo pronta" % {"c": s.chi, "p": C21.PROFILO, "f": C21.FILE_PAGINA, "pag": b(PAGINA),
                         "pref": b(C21.PREFERENZE), "xul": b(C21.xulstore(largo, alto))}, 60)


def foto_im(s, nome=None):
    """(png, PIL RGB, t_prima_ms, t_dopo_ms).  Salva se `nome`."""
    from PIL import Image
    tp = time.time() * 1000.0
    if nome:
        png, _dove = s.foto(nome)
    else:
        try:
            png = C21.foto_piena(s.g)
        except Exception:                        # noqa: BLE001
            png = None
    td = time.time() * 1000.0
    if not png:
        return None, None, tp, td
    return png, Image.open(io.BytesIO(png)).convert("RGB"), tp, td


def aspetta_ferma(s, attesa, nome):
    """La finestra ferma in due foto di fila: (f, im) o (None, motivo).

    ⚠ `[M]` 24 set 2026, lxqt sotto carico 50: la finestra spostata si vedeva
      in ogni foto ma due foto di fila non tornavano mai uguali entro 12 s ⇒
      alla scadenza vale l'ULTIMA finestra vista (con `ferma: False`): e' la
      foto, non un «non si vede»."""
    fine = time.time() + attesa
    ultima, perche, im, im_u = None, "nessuna foto", None, None
    while time.time() < fine:
        png, im, _tp, _td = foto_im(s)
        if im is None:
            perche = "la tela non si fotografa"
            time.sleep(1)
            continue
        f, perche = trova(im)
        if f and ultima and all(abs(a - b) <= 2 for a, b in zip(ultima["rett"], f["rett"])):
            if s.o.evidenze and nome:
                im.save(os.path.join(s.o.evidenze, "%s.png" % nome))
            f["ferma"] = True
            return f, im
        if f:
            ultima, im_u = f, im
        time.sleep(0.8)
    if ultima is not None:
        ultima["ferma"] = False
        if s.o.evidenze and nome:
            im_u.save(os.path.join(s.o.evidenze, "%s-non-ferma.png" % nome))
        return ultima, im_u
    if s.o.evidenze and nome and im is not None:
        im.save(os.path.join(s.o.evidenze, "%s-NON-trovata.png" % nome))
    return None, perche


def processo_vivo(s):
    c, t = s.sc.dentro("pgrep -u %s -f firefox-esr >/dev/null && echo vivo || echo morto" % s.chi,
                       30)
    return "vivo" in (t or "")


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    with S.Sessione(o, "003", E) as s:
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        # ⚠ `[M]` 24 set 2026, kde: al primo fotogramma la tela era ancora
        #   640x340; la misura della finestra arriva dopo.  Si aspetta la tela
        #   attesa (la regola e' quella di F-011), o la scena non e' quella voluta.
        cw, ch, dpr = s.g.js("const d=document.documentElement; "
                             "return [d.clientWidth, d.clientHeight, devicePixelRatio||1];")
        attesa = F011.tela_attesa(cw, ch, dpr)
        fine = time.time() + 40
        geo = None
        while time.time() < fine:
            geo = s.geometria()
            if geo and [geo.get("tl"), geo.get("ta")] == attesa:
                break
            time.sleep(1)
        if not geo:
            raise S.Bloccata("`REMOTIX_PUNTATORE.geometria` non c'e'")
        if [geo.get("tl"), geo.get("ta")] != attesa:
            raise S.Bloccata("la tela e' %sx%s e non %dx%d dopo 40 s: la scena non e' quella "
                             "voluta (e' F-011 a giudicarla)" % (geo.get("tl"), geo.get("ta"),
                                                                 attesa[0], attesa[1]))
        time.sleep(1.5)
        geo = s.geometria()
        if geo.get("disposizione") != "classico":
            raise S.Bloccata("la pagina non e' nella disposizione classica (%s): il "
                             "trascinamento col mouse non e' questa domanda" % geo.get("disposizione"))
        print("   tela %sx%s · sveglia: %s" % (geo["tl"], geo["ta"], C21.sveglia(s.g, geo)),
              flush=True)
        parti, guasti, ev = [], [], []

        # ── 0. la foto di prima: nessun ciano ──────────────────────────────
        time.sleep(1.5)
        png0, im0, _a, _b = foto_im(s, "prima-dell-apertura")
        if im0 is None:
            raise S.Bloccata("la tela non si fotografa")
        q0 = frazione_ciano(im0)
        if q0 >= CIANO_ASSENTE:
            raise S.Bloccata("prima di aprire c'e' gia' del ciano (%.2f %%): la scena non e' "
                             "pulita" % (100 * q0))

        # ── 1. APRE ────────────────────────────────────────────────────────
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        c, t = prepara_la_casa(s, largo_f, alto_f)
        if c != 0:
            raise S.Bloccata("la casa non si prepara: %s" % (t or "")[-200:])
        ok, t = C21.accendi_la_finestra(s.sc, s.chi)
        if not ok:
            raise S.Bloccata("firefox-esr non parte: %s" % (t or "")[-200:])
        t_ap = time.time()
        f1, im1 = aspetta_ferma(s, APERTURA_S, "aperta")
        if not f1:
            _c, log = s.sc.dentro("tail -n 40 /home/%s/.c21-firefox.log" % s.chi, 30)
            ev.append(s.salva_testo("firefox-esr-nella-sessione.log", log or ""))
            _p, im_x, _a, _b = foto_im(s, "apertura-non-vista")
            nuovo = cambiato(im0, im_x) if im_x is not None else 0.0
            if not processo_vivo(s):
                parti.append(("apre", S.BLOCKED, "firefox-esr non e' rimasto vivo: %s" % im1))
            elif nuovo > CAMBIATO_MIN:
                # ⚠ lo schermo si e' aggiornato (e' comparso ALTRO: un avviso,
                #   un'anteprima): la scena non e' quella che volevo ⇒ il banco
                parti.append(("apre", S.BLOCKED, "la foto e' cambiata (%.1f %% dei pixel) ma "
                              "non mostra la pagina di prova: e' comparso altro — vedi la foto "
                              "e il registro di firefox-esr" % (100 * nuovo)))
            else:
                parti.append(("apre", S.FAIL, "firefox-esr e' vivo da %.0f s e la foto e' "
                              "IDENTICA a quella di prima (%.2f %% dei pixel cambiati): lo "
                              "schermo non si aggiorna" % (time.time() - t_ap, 100 * nuovo)))
            raise _Fine(parti, [], ev)
        pw, ph = f1["foto"]
        largo_foto = largo_f * geo["sx"] * pw / geo["bw"]       # desktop ⇒ foto
        e, m = giudica_apertura(f1, largo_foto)
        if e == S.FAIL and f1:
            e = S.BLOCKED
            m = ("il ciano e' largo %d px e ne ho chiesti %d: un'anteprima (vista d'insieme?), "
                 "non la finestra" % (f1["rett"][2] - f1["rett"][0] + 1, largo_f))
        parti.append(("apre", e, m + " (in %.1f s)" % (time.time() - t_ap)))
        f0, _ = trova(im0)
        guasti.append(("apre", giudica_apertura(f0, largo_foto)))
        if e != S.PASS:
            raise _Fine(parti, guasti)

        # ── 2. CAMBIA: il contatore, per RAPIDI_S secondi ─────────────────
        v0, mv = leggi_contatore(im1, f1["rett"])
        if v0 is None:
            parti.append(("cambia", S.BLOCKED, "il contatore non si legge nella finestra "
                          "ferma: %s" % mv))
        else:
            # ⛔ un FAIL si conferma rifacendolo: se la prima serie e' rossa se ne
            #   fa una seconda, e il rosso vale solo se lo sono tutt'e due
            #   (`[M]` 24 set 2026, lxqt, carico 50: UNA foto vecchia di 1,5 s)
            serie = []
            for giro in range(2):
                letture, prima_im = [], None
                t_via = time.time()
                i = 0
                # ⚠ `[M]` 25 set 2026, gnome sotto carico: una foto 4K di Firefox
                #   costava 2-3 s, e in 6 s ne venivano 2 ⇒ almeno FOTO_MIN foto,
                #   fino a RAPIDI_MAX_S
                while (time.time() - t_via < RAPIDI_S or len(letture) < FOTO_MIN) \
                        and time.time() - t_via < RAPIDI_MAX_S:
                    _png, im, tp, td = foto_im(s)
                    if im is None:
                        continue
                    n, mn = leggi_contatore(im, f1["rett"])
                    letture.append((tp, td, n, mn))
                    if prima_im is None:
                        prima_im = im
                    if o.evidenze:
                        x0, y0, x1, y1 = f1["rett"]
                        im.crop((x0, y0 + int(0.55 * (y1 - y0)), x1, y1)).save(
                            os.path.join(o.evidenze, "rapida-%d-%02d-n%s.png" % (giro, i, n)))
                    i += 1
                e, m, righe = giudica_rapidi(letture)
                ev.append(s.salva_testo("rapide-%d.txt" % giro, righe))
                serie.append((e, m, letture, prima_im))
                print("   cambi rapidi, serie %d: %s %s" % (giro + 1, e, m), flush=True)
                if e == S.PASS:
                    break
            e, m, letture, prima_im = serie[-1]
            if len(serie) > 1:
                m = "serie 1: %s %s · serie 2: %s" % (serie[0][0], serie[0][1], m)
            parti.append(("cambia", e, m))
            # il guasto: la PRIMA foto per tutte, cogli istanti veri
            if letture and prima_im is not None:
                n0, m0 = leggi_contatore(prima_im, f1["rett"])
                vecchie = [(tp, td, n0, m0) for tp, td, _n, _m in letture]
                ge, gm, _ = giudica_rapidi(vecchie)
                guasti.append(("cambia", (ge, gm)))

        # ── 3. SPOSTA: per la barra del titolo ─────────────────────────────
        s.g.js(S.VERI._inietta(JS_OSSERVA))
        r0 = f1["rett"]
        f_prima, im_prima = f1, im1
        esito_sp = None
        tentativi = []
        for dy in PRESE_DY:
            Xc, Yt = C21.dalla_foto_al_desktop(geo, pw, ph, (r0[0] + r0[2]) / 2.0 + 0.5,
                                               r0[1] + 0.5)
            X, Y = Xc, Yt + dy
            if Y < 2:
                continue
            if X + SPOSTA[0] + 4 >= geo["tl"] or Y + SPOSTA[1] + 4 >= geo["ta"]:
                esito_sp = (S.BLOCKED, "non c'e' posto per spostare la finestra")
                break
            s.g.js(JS_AZZERA)
            trascina(s.g, geo, X, Y, SPOSTA[0], SPOSTA[1])
            time.sleep(0.4)
            n = s.g.js(JS_CONTA) or {}
            sp = n.get("spedito") or [-1, -1]
            if n.get("giu", 0) < 1 or n.get("su", 0) < 1 or n.get("premuti", 0) < PASSI_GESTO // 2:
                esito_sp = (S.BLOCKED, "il browser non ha consegnato il gesto alla pagina (%s)" % n)
                break
            if abs(sp[0] - int(X + SPOSTA[0])) > 2 or abs(sp[1] - int(Y + SPOSTA[1])) > 2:
                esito_sp = (S.BLOCKED, "la pagina ha spedito (%s,%s) invece di (%d,%d): il "
                            "puntatore non e' dove dico" % (sp[0], sp[1], X + SPOSTA[0],
                                                           Y + SPOSTA[1]))
                break
            f2, im2 = aspetta_ferma(s, 20, "dopo-presa%+d" % dy)
            if not f2:
                tentativi.append("%+d: la finestra non si vede piu' (%s)" % (dy, im2))
                esito_sp = (S.FAIL if processo_vivo(s) else S.BLOCKED,
                            "presa a %+d px sopra la pagina: dopo il gesto la finestra non si "
                            "vede piu' (%s)" % (dy, im2))
                break
            e, m = giudica_spostamento(r0, f2["rett"])
            if not f2.get("ferma", True):
                m += " (ultima foto: non stava ferma in due foto di fila)"
            tentativi.append("%+d: %s" % (dy, m))
            print("   presa %+d px sopra la pagina → %s" % (dy, m), flush=True)
            if e == S.PASS:
                esito_sp = (S.PASS, "presa a %+d px sopra la pagina: %s" % (dy, m))
                guasti.append(("sposta", giudica_spostamento(r0, f_prima["rett"])))
                f_dopo, im_dopo = f2, im2
                break
            # cambiata di misura o ferma: si riparte dalla finestra com'e' ora
            r0, f_prima, im_prima = f2["rett"], f2, im2
            time.sleep(0.6)
        if esito_sp is None:
            esito_sp = (S.FAIL, "in nessuna delle %d prese sopra la pagina la finestra si e' "
                        "spostata: %s" % (len(tentativi), "; ".join(tentativi[-3:])))
        parti.append(("sposta", esito_sp[0], esito_sp[1]))
        if esito_sp[0] != S.PASS:
            f_dopo, im_dopo = f_prima, im_prima

        # ── 4. CHIUDE ──────────────────────────────────────────────────────
        s.sc.dentro("pkill -u %s -f '[f]irefox-esr' ; echo fatto" % s.chi, 30)
        t_ch = time.time()
        quota, im3, foto_fatte = None, None, 0
        while time.time() - t_ch < CHIUSA_S:
            time.sleep(0.7)
            _png, im_c, _a, _b = foto_im(s)
            if im_c is None:
                continue
            foto_fatte += 1
            im3, quota = im_c, frazione_ciano(im_c)
            if quota < CIANO_ASSENTE:
                break
        if im3 is not None and o.evidenze:
            im3.save(os.path.join(o.evidenze, "chiusa.png"))
        if quota is None:
            # ⚠ `[M]` 25 set 2026, gnome/chrome: 60 s senza una foto riuscita
            #   (il browser sotto carico): non ho guardato, non e' un «si vede»
            parti.append(("chiude", S.BLOCKED, "dopo la chiusura nessuna foto e' riuscita in "
                          "%.0f s" % (time.time() - t_ch)))
        elif quota >= CIANO_ASSENTE and processo_vivo(s):
            parti.append(("chiude", S.BLOCKED, "firefox-esr non si e' chiuso (pkill)"))
        else:
            e, m = giudica_chiusura(quota)
            parti.append(("chiude", e, m + " (dopo %.1f s, %d foto)" % (time.time() - t_ch,
                                                                       foto_fatte)))
        guasti.append(("chiude", giudica_chiusura(frazione_ciano(im_dopo))))
        raise _Fine(parti, guasti, ev)


class _Fine(Exception):
    def __init__(self, parti, guasti=None, ev=None):
        super().__init__("fine")
        self.parti, self.guasti, self.ev = parti, guasti or [], ev or []


def corpo_e_giudizio(o, E):
    try:
        corpo(o, E)
    except _Fine as f:
        es = complessivo(f.parti)
        testo = " · ".join("%s %s: %s" % (p, e, m) for p, e, m in f.parti)
        guai = [x for x in f.parti if x[1] != S.PASS]
        ev = [p for p in f.ev if p]
        if o.evidenze:
            ev.append(o.evidenze)
        E.metti("F-003", es, testo if es != S.PASS else
                "apre, cambia, sposta, chiude: tutte le foto seguono lo schermo",
                atteso="la foto mostra la finestra aperta; il contatore nuovo (≤ %.0f ms) in ogni "
                       "foto di %d s; la finestra altrove dopo il trascinamento; niente "
                       "finestra dopo la chiusura" % (TETTO_MS, RAPIDI_S),
                osservato=testo, evidenze=ev, parti={p: [e, m] for p, e, m in f.parti},
                guai=[p for p, _e, _m in guai])
        if o.guasto:
            if es != S.PASS:
                E.guasto("F-003", None, "la passata sana non e' verde: il guasto «foto vecchia» "
                         "si giudica solo su una passata sana (%s)" % testo[:200])
                return
            visti = {p: r[0] == S.FAIL for p, r in f.guasti}
            tutti = len(visti) == 4 and all(visti.values())
            E.guasto("F-003", tutti, "foto di PRIMA del cambiamento ⇒ %s" % " · ".join(
                "%s %s" % (p, "rosso" if r[0] == S.FAIL else r[0]) for p, r in f.guasti),
                osservato=" | ".join("%s: %s" % (p, r[1]) for p, r in f.guasti))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo_e_giudizio, certifica))
