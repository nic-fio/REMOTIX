#!/usr/bin/env python3
"""12-c20-veri — C20 COI BROWSER VERI: dopo «Esci» e un nuovo accesso dalla
stessa pagina, lo schermo non lampeggia.

    python3 banchi/12-c20-veri.py --scatola gnome [--browser firefox,chrome]
        [--visibile] [--salva DIR] [--attesa-rientro 3]

⛔ PERCHE' ESISTE.  `11-c20-…py` (la maglia della rete) usa il cliente Python,
   e il 23 set 2026, sera, su gnome ha dato «non ho potuto guardare»: il
   secondo accesso viene AMMESSO e un secondo dopo e' il CLIENTE a chiudere la
   connessione (nel registro del server la chiusura e' silenziosa, cioe' in
   drenaggio: l'ha chiesta l'altra parte).  Poi la maglia, arrendendosi, fa
   `loginctl terminate-user` — ed e' quello il segnale 15 che si leggeva nel
   giornale.  ⇒ Il cliente Python puo' indicare dove guardare, ⛔ ma non
   certificare ne' scagionare: l'utente, 23 set 2026, *«i test vanno fatti con
   i browser veri, non con emulatori»*.

⭐ CHE COSA FA, per ogni browser (Firefox con Marionette, Chrome con CDP, i
   guidatori sono quelli di `12-client-veri.py`, ⛔ non una copia):
     1  apre la pagina, entra, aspetta il primo fotogramma non degenere
     2  dentro la sessione, il gesto «Esci» DEL MENU (la tavola di C20)
     3  aspetta che il prodotto dichiari la sessione finita (le due forme di
        C20) e guarda che cosa fa la PAGINA: torna al modulo? con che frase?
     4  dopo `--attesa-rientro` secondi rientra DALLA STESSA PAGINA, come fa
        l'utente — e se il modulo non c'e', ricarica (e lo dice)
     5  primo fotogramma, poi accende nella sessione la scena di C20 (luce
        costante, bande che scorrono) e fotografa la tela per `--guarda-s`
     6  giudica le luminanze col giudice di C20 (⛔ lo stesso, importato):
        un lampeggio fra desktop, schermata d'uscita e nero e' ROSSO
   Esiti: 0 verde · 1 rosso · 3 non ho potuto guardare, col motivo.

⚠ Si entra nella scatola con `fondamenta/strumenti/sshpw.py` e `sudo podman
  exec rete11-<scatola>`: e' la stessa strada di `11-gancio.sh remoto`.
⚠ L'inquilino e' `c20u7<n>`, dentro lo spazio di nomi della rete: se questo
  banco morisse a meta', il gancio lo sgombera e C19 lo vede.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import random
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
SSHPW = os.path.join(RADICE, "fondamenta", "strumenti", "sshpw.py")
REGISTRO = "/var/lib/rete11/registro.log"
SCENA_DENTRO = "/opt/remotix/11-c20-scena.html"
PORTE = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


VERI = _carica("client_veri", os.path.join(QUI, "12-client-veri.py"))
C20 = _carica("c20", os.path.join(QUI, "11-scatole",
                                  "11-c20-la-rinascita-non-porta-fantasmi.py"))
VERDE, ROSSO, CIECO = VERI.VERDE, VERI.ROSSO, VERI.CIECO


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA SCATOLA
# ═══════════════════════════════════════════════════════════════════════════
class Scatola:
    def __init__(self, nome):
        self.nome = nome
        self.contenitore = "rete11-%s" % nome

    def dentro(self, riga, secondi=90):
        """(codice, uscita) di `riga` eseguita da root nella scatola.

        ⚠ La riga viaggia in base64: nessuna virgoletta da sfuggire su tre
          gusci (tablet → ssh → sudo → podman → sh)."""
        b = base64.b64encode(riga.encode()).decode()
        remoto = ("sudo -S -p 'Password sudo: ' podman exec %s sh -c "
                  "\"$(echo %s | base64 -d)\"; echo \"@@codice=$?\""
                  % (self.contenitore, b))
        try:
            r = subprocess.run([sys.executable, SSHPW, remoto], capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(nessuna risposta in %d s)" % secondi
        testo = "\n".join(x for x in r.stdout.splitlines()
                          if not x.startswith("tput:") and "Password sudo" not in x)
        codice = None
        if "@@codice=" in testo:
            testo, _, c = testo.rpartition("@@codice=")
            try:
                codice = int(c.strip())
            except ValueError:
                codice = None
        return codice, testo.strip()

    def righe_registro(self):
        c, t = self.dentro("wc -l < %s" % REGISTRO, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError):
            return None

    def registro_da(self, segno, chi):
        _c, t = self.dentro("tail -n +%d %s | grep -a -- '%s'" % (segno + 1, REGISTRO, chi),
                            60)
        return t.splitlines()

    def gesto_esci(self):
        """(desktop, gesto) — la stessa domanda di C20, fatta dentro."""
        for nome, ci_vuole, non_ci_vuole, gesto in C20.DESKTOP_E_GESTO:
            c, _ = self.dentro("command -v %s >/dev/null 2>&1" % ci_vuole, 30)
            if c != 0:
                continue
            if non_ci_vuole:
                c2, _ = self.dentro("command -v %s >/dev/null 2>&1" % non_ci_vuole, 30)
                if c2 == 0:
                    continue
            return nome, gesto
        return None, None

    def come_utente(self, chi, comando, secondi=60):
        return self.dentro(
            "u=$(id -u %s) && runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus %s 2>&1"
            % (chi, chi, comando), secondi)

    def accendi_scena(self, chi):
        c, t = self.dentro(
            "u=$(id -u %s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
            "| head -1); [ -n \"$d\" ] || { echo 'nessun socket wayland'; exit 2; }; "
            "[ -f %s ] || { echo 'manca %s'; exit 2; }; "
            "setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
            "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
            "firefox-esr --kiosk file://%s < /dev/null > /home/%s/.c20v-scena.log 2>&1 & "
            "for i in $(seq 1 40); do pgrep -u %s -f firefox-esr >/dev/null && "
            "{ echo accesa; exit 0; }; sleep 0.25; done; echo 'non si e vista'; exit 1"
            % (chi, SCENA_DENTRO, SCENA_DENTRO, chi, chi, SCENA_DENTRO, chi, chi), 60)
        return c == 0, t

    def crea(self, chi, parola):
        return self.dentro(
            "useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
            % (chi, chi, parola), 60)

    def sgombera(self, chi):
        # ⛔ `[c]20u7…`: `pkill -f` pescherebbe il guscio che lo esegue.
        self.dentro("loginctl terminate-user %s >/dev/null 2>&1; "
                    "pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null; "
                    "pkill -KILL -u %s >/dev/null 2>&1; sleep 0.5; "
                    "userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1; "
                    "rm -rf /home/%s"
                    % (chi, chi[0], chi[1:], chi, chi, chi, chi), 90)


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA DI UN BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def luminanza(png):
    """La luminanza media della fotografia della tela, o None."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("L").resize(
            (C20.LARGHEZZA, C20.ALTEZZA))
        px = list(im.getdata())
        return sum(px) // len(px)
    except Exception:                            # noqa: BLE001
        return None


def desktop_scuro_ma_vivo(e, m, s):
    """⭐ (esito, motivo) del primo fotogramma, con la tolleranza del 4K.

    ⛔ `[M]` 23 set 2026, xfce in 4K: lo sfondo della scatola e' NERO, e a
       3840x2160 pannello, icone e orologio coprono il 2,7 % ⇒ il giudice di
       `12-client-veri` (dominante >= 97 %) lo chiamava «degenere» — ma la
       fotografia mostrava il desktop vero.  ⇒ Qui un desktop con fotogrammi
       dipinti e ALMENO 40 colori distinti e' vivo: il giudizio vero di questo
       banco e' la scena accesa dopo, non il primo fotogramma."""
    if e == VERDE:
        return e, m
    import re
    c = re.search(r"colori distinti (\d+)", m or "")
    if (s or {}).get("dipinti") and c and int(c.group(1)) >= 40:
        return VERDE, "desktop scuro ma vivo (%s colori distinti): %s" % (c.group(1), m)
    return e, m


def aspetta_riga(sc, segno, chi, forme, tetto):
    fine = time.time() + tetto
    while time.time() < fine:
        for r in sc.registro_da(segno, chi):
            for f in forme:
                if f in r:
                    return f, r
        time.sleep(2)
    return None, None


def dimensiona(g, nome, largo, alto):
    """⭐ La finestra alla misura delle specifiche (4K), e si RILEGGE.

    ⚠ Le guide di `12-client-veri.py` nascono a 1400x1000; qui la misura si
      chiede dopo, e quel che vale e' `innerWidth` letto dalla pagina."""
    try:
        if nome == "firefox":
            g.m.chiama("WebDriver:SetWindowRect",
                       {"x": 0, "y": 0, "width": largo, "height": alto})
        elif nome == "chrome":
            # ⚠ `[M]` 23 set 2026, dentro labwc: la misura chiesta coi numeri
            #   Chrome la ignora (restava 1376x888); lo stato «massimizzata» lo
            #   onora il compositore.  Si chiede prima quello, poi i numeri.
            w = g.cdp.chiama("Browser.getWindowForTarget")
            wid = w.get("windowId") if isinstance(w, dict) else None
            if wid is None and isinstance(w, dict):
                wid = (w.get("result") or {}).get("windowId")
            g.cdp.chiama("Browser.setWindowBounds", windowId=wid,
                         bounds={"windowState": "maximized"})
    except Exception as e:                       # noqa: BLE001
        return "⚠ misura non cambiata: %s" % str(e)[:120]
    time.sleep(1)
    try:
        return "finestra %sx%s (dpr %s)" % tuple(g.js(
            "return [innerWidth, innerHeight, devicePixelRatio]"))
    except Exception as e:                       # noqa: BLE001
        return "⚠ misura non riletta: %s" % str(e)[:120]


def un_browser(nome, o, sc, chi, gesto):
    print("\n══ %s ══════════════════════════════" % nome.upper(), flush=True)
    esito = {"browser": nome}
    g = VERI.accendi_guida(nome, o)
    try:
        print("   palco: %s" % g.palco(), flush=True)
        if o.largo:
            esito["finestra"] = dimensiona(g, nome, o.largo, o.alto)
            print("   %s" % esito["finestra"], flush=True)
        pr = VERI.Prova(g, o, o.url, o.parola)

        # ── 1. il primo accesso ────────────────────────────────────────────
        ok, m = pr.apri()
        if not ok:
            return dict(esito, esito=CIECO, perche="la pagina non si apre: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(esito, esito=CIECO, perche="primo accesso: " + m)
        e, m, s = pr.primo_fotogramma()
        e, m = desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ primo accesso: %s" % m, flush=True)
        if e != VERDE:
            return dict(esito, esito=CIECO, perche="primo accesso senza immagine: " + m)
        time.sleep(o.primo_s)

        # ── 2. «Esci», il gesto del menu ───────────────────────────────────
        segno = sc.righe_registro()
        if segno is None:
            return dict(esito, esito=CIECO, perche="non leggo il registro del server")
        c, t = sc.come_utente(chi, gesto)
        if c != 0:
            return dict(esito, esito=CIECO, perche="il gesto «Esci» non ha risposto "
                        "(codice %s): %s" % (c, t[-300:]))
        t_esci = time.time()
        forma, riga = aspetta_riga(sc, segno, chi, [p for p, _d in C20.RIGHE_FINITA],
                                   o.attesa_uscita)
        if not forma:
            return dict(esito, esito=CIECO, perche="%d s dopo «Esci» il prodotto non ha "
                        "dichiarato la sessione finita" % o.attesa_uscita)
        print("   ⭐ «Esci»: dopo %.1f s il prodotto dice «%s»"
              % (time.time() - t_esci, forma), flush=True)

        # ── 3. che cosa fa la PAGINA ───────────────────────────────────────
        modulo, pagina = False, {}
        fine = time.time() + 30
        while time.time() < fine:
            try:
                mm = g.js(VERI.JS_MODULO)
                if mm and mm.get("modulo") and mm.get("visibile"):
                    modulo = True
                    break
            except Exception:                    # noqa: BLE001
                pass
            time.sleep(0.5)
        pagina = pr.stato()
        print("   %s la pagina dopo «Esci»: modulo %s · esito «%s»"
              % ("⭐" if modulo else "⚠", "VISIBILE" if modulo else "NON visibile",
                 (pagina.get("esito") or "")[:120]), flush=True)
        esito["pagina_dopo_esci"] = {"modulo": modulo, "esito": pagina.get("esito")}

        # ── 4. il nuovo accesso, DALLA STESSA PAGINA ───────────────────────
        time.sleep(o.attesa_rientro)
        segno2 = sc.righe_registro() or segno
        if not modulo:
            print("   ⚠ il modulo non c'e': ricarico, come farebbe l'utente", flush=True)
            g.ricarica()
            ok, m = pr.apri_dopo_ricarica()
            if not ok:
                return dict(esito, esito=CIECO, perche="dopo la ricarica: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            # ⛔ Qui il rosso e' del PRODOTTO: l'utente dopo «Esci» non rientra.
            coda = [x for x in (s or {}).get("registro", "").splitlines() if x.strip()][-6:]
            return dict(esito, esito=ROSSO, perche="dopo «Esci» NON RIENTRA: %s" % m,
                        pagina=coda, server=sc.registro_da(segno2, chi)[-25:])
        e, m, s = pr.primo_fotogramma()
        e, m = desktop_scuro_ma_vivo(e, m, s)
        print("   %s secondo accesso: %s" % ("⭐" if e == VERDE else "⛔", m), flush=True)
        if e != VERDE:
            return dict(esito, esito=ROSSO if e == ROSSO else CIECO,
                        perche="secondo accesso senza immagine: " + m,
                        server=sc.registro_da(segno2, chi)[-25:])

        # ── 5. la scena, e la tela fotografata ─────────────────────────────
        accesa, t = sc.accendi_scena(chi)
        if not accesa:
            return dict(esito, esito=CIECO, perche="la scena non si accende: %s" % t[-160:])
        print("   ⭐ scena accesa (%s)" % os.path.basename(SCENA_DENTRO), flush=True)
        lum, d0 = [], (pr.stato().get("dipinti") or 0)
        fine = time.time() + o.guarda_s
        while time.time() < fine:
            try:
                png, _p = g.fotografa_tela()
            except Exception:                    # noqa: BLE001
                png = None
            if png:
                v = luminanza(png)
                if v is not None:
                    lum.append(v)
                if o.salva and len(lum) % 10 == 1:
                    with open(os.path.join(o.salva, "%s-%03d.png" % (nome, len(lum))),
                              "wb") as f:
                        f.write(png)
            time.sleep(o.passo_s)
        s = pr.stato()
        d1 = s.get("dipinti") or 0
        print("   luminanze (%d fotografie, %d fotogrammi dipinti): %s"
              % (len(lum), d1 - d0, " ".join(str(x) for x in lum[:80])), flush=True)
        ep, salti, perche = C20.giudica_i_pixel(lum)
        server = sc.registro_da(segno2, chi)
        interessanti = [r for r in server if any(k in r for k in (
            "figlio generato", "RACCOLTO", "E' FINITA", "se n'e' andato", "butto",
            "RIAVVIO LA CATTURA", "congedo", "chiusa"))]
        return dict(esito, esito=ep, perche=perche, salti=salti, fotografie=len(lum),
                    dipinti=d1 - d0, server=interessanti[-20:])
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ chiusura del browser: %s" % ex)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", default="gnome", choices=sorted(PORTE))
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true")
    a.add_argument("--salva", default="")
    a.add_argument("--primo-s", type=float, default=5.0,
                   help="quanto resta il primo accesso prima di «Esci»")
    a.add_argument("--attesa-uscita", type=float, default=120.0)
    a.add_argument("--attesa-rientro", type=float, default=3.0,
                   help="secondi fra la sessione finita e il nuovo accesso")
    a.add_argument("--guarda-s", type=float, default=30.0)
    a.add_argument("--passo-s", type=float, default=0.2)
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--porte-base", type=int, default=2951)
    # ⭐ Le specifiche sono 4K (l'utente, 23 set 2026): la finestra si porta a
    #   3840x2160.  `--largo 0` lascia la misura delle guide (1400x1000).
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    o = a.parse_args()
    # ⚠ i campi che le guide e `Prova` di 12-client-veri si aspettano
    o.url = "https://%s:%d/" % (o.host, PORTE[o.scatola])
    o.parola = C20.PAROLA
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = Scatola(o.scatola)
    desktop, gesto = sc.gesto_esci()
    if not gesto:
        print("⛔ non so come si dice «Esci» in %s ⇒ 3" % sc.contenitore)
        return 3
    chi = "c20u7%02d" % random.randint(0, 99)
    o.utente = chi
    print("⭐ 12-c20-veri · %s (%s) · %s · inquilino %s · browser %s · %s"
          % (sc.contenitore, desktop, o.url, chi, o.browser,
             "finestre vere" if o.visibile else "HEADLESS"))
    print("   «Esci» si dice: %s" % gesto)
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ non ho potuto creare %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = un_browser(b, o, sc, chi, gesto)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "esito": CIECO, "perche": "il banco e' caduto: %r" % e}
        finally:
            sc.sgombera(chi)
        print("   ▶ %s: %s — %s" % (b, {0: "VERDE", 1: "ROSSO", 3: "NON HO POTUTO GUARDARE"}
                                   .get(r["esito"], r["esito"]), r.get("perche")))
        for x in r.get("server") or []:
            print("      server: %s" % x[:200])
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        righe.append(r)
    v = [r["esito"] for r in righe]
    return 1 if 1 in v else (3 if 3 in v else 0)


if __name__ == "__main__":
    sys.exit(main())
