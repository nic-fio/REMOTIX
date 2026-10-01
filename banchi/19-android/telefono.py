#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
telefono.py — LA GUIDA DEL TELEFONO VERO per la suite (fase 19 §5)
===========================================================================

`suite.py --browser telefono` la carica al posto di Firefox o di Chrome da
tavolo.  Gira SUL SERVER, dentro le prove della suite, e parla con due porte
che il portatile le porta col tunnel ssh (`19-android.py`):

  127.0.0.1:19333   il protocollo DevTools del Chrome del telefono
                    (portatile: `adb forward tcp:9333 localabstract:chrome_devtools_remote`)
  127.0.0.1:19334   lo SPORTELLO del portatile: le sole cose che vogliono adb
                    (chiamata in corso?, Chrome davanti, tocco vero, rotazione,
                    Chrome fermato di colpo).  ⛔ La chiave del telefono resta sul
                    portatile: di qua passano solo domande con nome.

⛔ LE REGOLE DEL TELEFONO (DECISIONI §10.27, fasi/19 §5):
  - solo Chrome, e solo verso le scatole del server: `vai()` rifiuta ogni
    indirizzo che non sia https://192.168.0.2:8511-8514 o 8611-8614;
  - una scheda NOSTRA (nuova), mai quelle dell'utente: si apre con /json/new,
    si chiude alla fine; il portatile la segna e la chiude anche se qui si cade;
  - prima di ogni gesto il controllo della chiamata (lo fa lo sportello, una
    riga `mCallState=[12]` per SIM): con una chiamata si ASPETTA, e se non
    finisce la prova cade BLOCKED «chiamata in corso» — mai un gesto durante.

L'input delle prove comuni (clic, tasti, trascinamenti) passa dal protocollo
DevTools come per Chrome da tavolo — mouse e tastiera, cioe' il caso DeX
(`SPECIFICHE.md` §7.2: «su Android l'uso primario e' DeX»).  Il TOCCO VERO
(`adb shell input`) lo usa la prova del tocco, `15-f031-tocco.py`.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

PORTA_CDP = int(os.environ.get("REMOTIX_TELEFONO_CDP", "19333"))
SPORTELLO = "http://127.0.0.1:%s" % os.environ.get("REMOTIX_TELEFONO_SPORTELLO", "19334")
SERVER = os.environ.get("REMOTIX_TELEFONO_HOST", "192.168.0.2")
PORTE_AMMESSE = set(range(8511, 8515)) | set(range(8611, 8615))
# ⚠ solo per la prova a secco del banco (19-android.py a-secco): una pagina locale in http
A_SECCO = os.environ.get("REMOTIX_TELEFONO_A_SECCO") == "1"
GUARDIA_OGNI_S = 5.0

# Il quaderno dei tocchi VERI: dove e' caduto ogni dito, visto dalla pagina.
QUADERNO_TOCCHI = r"""
(function () {
  if (window.__T19) return;
  window.__T19 = [];
  addEventListener("touchstart", function (e) {
    const t = e.touches[0];
    if (!t) return;
    window.__T19.push({ x: t.clientX, y: t.clientY, n: e.touches.length,
                        su: (e.target && e.target.id) || (e.target && e.target.tagName) || "",
                        t: performance.now() });
    if (window.__T19.length > 200) window.__T19.shift();
  }, { capture: true, passive: true });
})();
"""


class ChiamataInCorso(RuntimeError):
    """Il telefono e' in chiamata: nessun gesto."""


def sportello(percorso, dati=None, tetto=1800):
    """Una domanda allo sportello del portatile.  Torna il dizionario della risposta."""
    corpo = json.dumps(dati or {}).encode()
    rq = urllib.request.Request(SPORTELLO + percorso, data=corpo, method="POST",
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(rq, timeout=tetto) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            d = json.loads(e.read().decode() or "{}")
        except ValueError:
            d = {}
        if e.code == 409:
            raise ChiamataInCorso(d.get("perche") or "chiamata in corso sul telefono")
        raise RuntimeError("sportello %s: %s %s" % (percorso, e.code, d.get("perche", "")))
    except urllib.error.URLError as e:
        raise RuntimeError("lo sportello del portatile non risponde (%s): il tunnel ssh "
                           "c'e'?  %s" % (SPORTELLO, e))


def ammesso(url):
    """⛔ Solo le scatole del server (e la pagina vuota)."""
    if url in ("about:blank",):
        return True
    u = urllib.parse.urlsplit(url)
    if A_SECCO and u.scheme == "http" and u.hostname == "127.0.0.1":
        return True
    return u.scheme == "https" and u.hostname == SERVER and u.port in PORTE_AMMESSE


def orienta(verso):
    """«altro» gira il telefono nell'altro verso; «partenza» lo rimette com'era."""
    r = sportello("/ruota", {"verso": verso})
    return r.get("detto", str(r))


def _http(percorso, metodo="GET"):
    rq = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA_CDP, percorso), method=metodo)
    with urllib.request.urlopen(rq, timeout=15) as r:
        t = r.read().decode()
    try:
        return json.loads(t)
    except ValueError:
        return t


def _veri():
    """`12-client-veri.py` come lo carica la suite (gia' caricato: non si ricarica)."""
    import sys
    s = sys.modules.get("suite") or sys.modules.get("__main__")
    v = getattr(s, "VERI", None)
    if v is None:
        import importlib.util as iu
        qui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sp = iu.spec_from_file_location("veri", os.path.join(qui, "12-client-veri.py"))
        v = iu.module_from_spec(sp)
        sp.loader.exec_module(v)
    return v


VERI = _veri()


class GuidaTelefono(VERI.GuidaCdp):
    """Chrome del telefono vero, in una scheda NOSTRA."""
    tocco = False                 # l'input comune e' mouse+tastiera del protocollo (DeX)
    _n_chiusure = 0

    def __init__(self, o=None):
        super().__init__(PORTA_CDP, "telefono")
        self.o = o
        self._ultima_guardia = 0.0
        self.scala_foto = 1
        self._palco = None
        sportello("/pronto")                      # chiamata? schermo? Chrome davanti
        self.scheda = self._nuova_scheda()
        sportello("/mia", {"id": self.scheda["id"]})
        self.aggancia()
        try:
            self.scala_foto = float(self.js("return devicePixelRatio") or 1)
        except Exception:                         # noqa: BLE001
            self.scala_foto = 1

    # -- la scheda -------------------------------------------------------------
    def _nuova_scheda(self):
        try:
            t = _http("/json/new?about:blank", "PUT")
            if isinstance(t, dict) and t.get("id"):
                return t
        except Exception:                         # noqa: BLE001
            pass
        # ripiego: Target.createTarget dal bersaglio del browser
        v = _http("/json/version")
        b = VERI.Cdp(self._qui(v["webSocketDebuggerUrl"]))
        r = b.chiama("Target.createTarget", url="about:blank")
        try:
            b.ws.chiudi()
        except Exception:                         # noqa: BLE001
            pass
        for t in _http("/json/list"):
            if t.get("id") == r.get("targetId"):
                return t
        raise RuntimeError("la scheda nuova non compare nell'elenco del telefono")

    @staticmethod
    def _qui(ws):
        """Il websocket passa dal tunnel: l'host e' sempre 127.0.0.1:PORTA_CDP."""
        u = urllib.parse.urlsplit(ws)
        return urllib.parse.urlunsplit(u._replace(netloc="127.0.0.1:%d" % PORTA_CDP))

    def aggancia(self, attesa=40):
        self.cdp = VERI.Cdp(self._qui(self.scheda["webSocketDebuggerUrl"]))
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            try:
                self.cdp.chiama(d)
            except Exception:                     # noqa: BLE001
                pass
        self.cdp.chiama("Page.addScriptToEvaluateOnNewDocument", source=VERI.RACCOGLITORE)
        self.cdp.chiama("Page.addScriptToEvaluateOnNewDocument", source=QUADERNO_TOCCHI)
        try:
            self.cdp.chiama("Page.bringToFront")
        except Exception:                         # noqa: BLE001
            pass

    def versione(self):
        try:
            return _http("/json/version").get("Browser", "?")
        except Exception as e:                    # noqa: BLE001
            return "? (%s)" % e

    def palco(self):
        if self._palco is None:
            try:
                self._palco = sportello("/palco").get("palco")
            except Exception as e:                # noqa: BLE001
                self._palco = "%s su Android (palco non letto: %s)" % (self.versione(), e)
        return self._palco

    # -- la guardia della chiamata --------------------------------------------
    def guardia(self, subito=False):
        """⚠ Gli eventi del PROTOCOLLO (clic, tasti) vanno al renderer di Chrome, non
        al sistema: non possono rispondere a una chiamata ne' toccare altro.  Per
        loro il controllo si rifa' ogni 5 s (una prova manda centinaia di tasti).
        I gesti VERI (`adb shell input`) lo sportello li controlla ogni volta."""
        if not subito and time.time() - self._ultima_guardia < GUARDIA_OGNI_S:
            return
        try:
            sportello("/chiamata")                # aspetta lui; 409 ⇒ ChiamataInCorso
        except Exception:
            self._ultima_guardia = 0.0            # il prossimo gesto ricontrolla
            raise
        self._ultima_guardia = time.time()

    # -- le azioni: prima la guardia ------------------------------------------
    def vai(self, url):
        if not ammesso(url):
            raise RuntimeError("⛔ il telefono va solo alle scatole del server, non a %s" % url)
        self.guardia(subito=True)
        return super().vai(url)

    def ricarica(self):
        self.guardia()
        return super().ricarica()

    def muovi(self, x, y):
        self.guardia()
        return super().muovi(x, y)

    def clic(self, x, y):
        self.guardia()
        return super().clic(x, y)

    def tocca(self, x, y):
        self.guardia()
        return super().tocca(x, y)

    def trascina(self, punti):
        self.guardia()
        return super().trascina(punti)

    def tasto(self, t):
        self.guardia()
        return super().tasto(t)

    # -- chiudere, e uccidere --------------------------------------------------
    def _chiudi_scheda(self):
        sid = self.scheda.get("id")
        try:
            _http("/json/close/%s" % sid, "PUT")
        except Exception:                         # noqa: BLE001
            try:
                _http("/json/close/%s" % sid)
            except Exception:                     # noqa: BLE001
                pass
        try:
            sportello("/non-mia", {"id": sid})
        except Exception:                         # noqa: BLE001
            pass

    def chiudi(self):
        # ⭐ l'evidenza: com'era la pagina del telefono un attimo prima di chiudere
        cartella = getattr(self.o, "evidenze", "") if self.o else ""
        if cartella:
            GuidaTelefono._n_chiusure += 1
            foto_png(self, "chiusura-%02d" % GuidaTelefono._n_chiusure, cartella)
        try:
            self.cdp.chiama("Page.navigate", url="about:blank")   # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                         # noqa: BLE001
            pass
        try:
            self.cdp.ws.chiudi()
        except Exception:                         # noqa: BLE001
            pass
        self._chiudi_scheda()

    def uccidi(self):
        """⛔ Chrome fermato DI COLPO (`am force-stop`): nessun congedo, il filo tace.
        E' il gesto di F-020 «browser chiuso di colpo».  Torna 1 (un processo)."""
        self.guardia(subito=True)
        sportello("/uccidi-chrome")
        try:
            self.cdp.ws.chiudi()
        except Exception:                         # noqa: BLE001
            pass
        self.cdp = None
        return 1

    # ═════════════════════════════════════════════════════════════════════════
    #  IL TOCCO (per 15-f031-tocco.py): il modello a trackpad di SPECIFICHE §7.1
    # ═════════════════════════════════════════════════════════════════════════
    def stato_tocco(self):
        return self.js("return (window.REMOTIX && REMOTIX.tocco) ? REMOTIX.tocco.stato() : null")

    def disposizione(self):
        return self.js("return (window.REMOTIX && REMOTIX.tocco && REMOTIX.tocco.disposizione)"
                       " ? REMOTIX.tocco.disposizione() : null")

    def tocchi_visti(self, da=0):
        return (self.js("return (window.__T19 || []).slice(arguments[0])", da) or [])

    def puntatore_vetro(self, geo):
        """Dove sta il puntatore DISEGNATO, in coordinate del vetro."""
        st = self.stato_tocco() or {}
        p = st.get("puntatore")
        if not p:
            return None
        return (geo["left"] + (geo["bx0"] + p[0] * geo["sx"]) * geo["vx"],
                geo["top"] + (geo["by0"] + p[1] * geo["sy"]) * geo["vy"])

    def schermo(self):
        """(larghezza, altezza) dello schermo in pixel VERI, nel verso di adesso; dpr."""
        r = self.js("return [screen.width, screen.height, devicePixelRatio,"
                    " innerWidth, innerHeight]")
        return r[0] * r[2], r[1] * r[2], r[2], r[3], r[4]

    def dito_cdp(self, punti, pausa_s=0.03, tieni_s=0.0):
        """Un dito del protocollo: giu' sul primo punto, i movimenti, su."""
        self.guardia()
        c = self.cdp.chiama
        c("Input.dispatchTouchEvent", type="touchStart",
          touchPoints=[{"x": punti[0][0], "y": punti[0][1]}])
        if tieni_s:
            time.sleep(tieni_s)
        for x, y in punti[1:]:
            time.sleep(pausa_s)
            c("Input.dispatchTouchEvent", type="touchMove", touchPoints=[{"x": x, "y": y}])
        time.sleep(pausa_s)
        c("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def _centro_tela(self, geo):
        return geo["left"] + geo["width"] / 2.0, geo["top"] + geo["height"] / 2.0

    def porta_il_puntatore(self, geo, tx, ty, giri=6):
        """Trascina un dito (protocollo) finche' il puntatore disegnato sta su (tx,ty)
        del vetro.  Torna l'errore finale in px del vetro, o None se non si legge."""
        err = None
        for _ in range(giri):
            p = self.puntatore_vetro(geo)
            if p is None:
                return None
            dx, dy = tx - p[0], ty - p[1]
            err = max(abs(dx), abs(dy))
            if err <= 1.0:
                return err
            # un passo che resti nella tela, e che sia SEMPRE un trascinamento
            # (oltre la soglia del tap, 9 px CSS): se il passo e' corto, un giro largo
            lim = 0.35 * min(geo["width"], geo["height"])
            dx, dy = max(-lim, min(lim, dx)), max(-lim, min(lim, dy))
            cx, cy = self._centro_tela(geo)
            x0, y0 = cx - dx / 2.0, cy - dy / 2.0
            punti = [(x0, y0)]
            if max(abs(dx), abs(dy)) < 14:
                punti.append((x0 + 12, y0 + 18))
            n = 10
            for i in range(1, n + 1):
                punti.append((x0 + dx * i / n, y0 + dy * i / n))
            self.dito_cdp(punti)
            time.sleep(0.25)
        p = self.puntatore_vetro(geo)
        return None if p is None else max(abs(tx - p[0]), abs(ty - p[1]))

    def tap_vero(self, geo):
        """⭐ Un TOCCO VERO (`adb shell input tap`) dentro la tela.  Nel modello a
        trackpad il tap clicca dove sta il puntatore, non dove cade il dito:
        il dito va al centro della tela.  Torna il tocco come l'ha visto la pagina."""
        da = len(self.tocchi_visti())
        x, y = self.vetro_su_schermo(*self._centro_tela(geo))
        sportello("/tocca", {"x": round(x), "y": round(y)})
        time.sleep(0.6)
        return (self.tocchi_visti(da) or [None])[0]

    def scorri_vero(self, geo, dx, dy, ms=600):
        """⭐ Un dito VERO che scorre (`adb shell input swipe`) di (dx,dy) px del vetro,
        partendo in modo che i due capi stiano nella tela."""
        da = len(self.tocchi_visti())
        cx, cy = self._centro_tela(geo)
        x0, y0 = self.vetro_su_schermo(cx - dx / 2.0, cy - dy / 2.0)
        x1, y1 = self.vetro_su_schermo(cx + dx / 2.0, cy + dy / 2.0)
        sportello("/scorri", {"x1": round(x0), "y1": round(y0), "x2": round(x1),
                              "y2": round(y1), "ms": int(ms)})
        time.sleep(0.5)
        return (self.tocchi_visti(da) or [None])[0]

    _scarto = None        # (ox, oy): schermo = scarto + vetro × dpr, dal primo tocco vero

    def vetro_su_schermo(self, x, y):
        sw, sh, dpr, iw, ih = self.schermo()
        if self._scarto is None:
            # prima stima: la pagina occupa il fondo dello schermo, larga quanto lui
            # (sopra c'e' la barra di Chrome); il primo tocco vero la corregge
            return (sw - iw * dpr) / 2.0 + x * dpr, (sh - ih * dpr) + y * dpr - 0.0
        return self._scarto[0] + x * dpr, self._scarto[1] + y * dpr

    def taratura(self, geo):
        """Un dito vero che scorre poco (muove il puntatore e basta, non clicca):
        dove l'ha visto la pagina dice lo scarto fra schermo e vetro."""
        sw, sh, dpr, iw, ih = self.schermo()
        cx, cy = self._centro_tela(geo)
        x0, y0 = self.vetro_su_schermo(cx, cy)
        da = len(self.tocchi_visti())
        sportello("/scorri", {"x1": round(x0), "y1": round(y0), "x2": round(x0 + 60 * dpr),
                              "y2": round(y0), "ms": 400})
        time.sleep(0.5)
        t = (self.tocchi_visti(da) or [None])[0]
        if not t:
            return None
        self._scarto = (x0 - t["x"] * dpr, y0 - t["y"] * dpr)
        return {"tocco": t, "scarto": [round(v, 1) for v in self._scarto]}


def foto_png(g, nome, cartella):
    """Una fotografia di TUTTA la pagina del telefono (evidenza), o None."""
    try:
        s = g.cdp.chiama("Page.captureScreenshot", format="png")
    except Exception:                             # noqa: BLE001
        return None
    if not cartella:
        return None
    p = os.path.join(cartella, "telefono-%s.png" % nome)
    with open(p, "wb") as f:
        f.write(base64.b64decode(s["data"]))
    return p
