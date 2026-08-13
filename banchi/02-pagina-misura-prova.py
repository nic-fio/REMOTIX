#!/usr/bin/env python3
"""02-pagina-misura-prova.py — ⭐⭐ IL BANCO CHE PRENDE IL DIFETTO DELLE DUE
   GRANDEZZE CONFUSE: la pagina DEL PRODOTTO, su uno schermo piu' corto di
   1080, deve finire con **un fotogramma dipinto**.

   Lo lancia `02-pagina-misura-lancia.sh`, che apparecchia la scena (Xvfb e
   Chrome).  Qui c'e' il giro e il VERDETTO, con l'atteso scritto prima.

===========================================================================
⛔ PERCHE' NESSUN BANCO L'AVEVA PRESO

`banchi/01-b3-cliente.py`, `01-b4-registrazioni.py`, `02-pam-fermo.py`
dichiarano `video.misura_massima = "3840x2160"` **a mano**; il banco della
scheda (`02-montaggio-scheda.sh`) apparecchia uno schermo finto di 2048x1280
e ha perfino un riquadro che spiega perche' dev'essere grande.

⇒ ⛔ **Solo la pagina del prodotto, su uno schermo vero, sbagliava**, e la
  cosa che nessuno provava era proprio quella: uno schermo piu' CORTO della
  tela.  ⚠ E `02-montaggio-scheda.sh` chiamava quel vincolo *«non e' un
  difetto del prodotto»*: era il difetto del prodotto, letto al contrario.

===========================================================================
⛔⭐ DUE GIRI, E IL SECONDO E' IL CONTROLLO NEGATIVO

  giro «schermo-corto»   schermo 2560x1010 (quello dell'utente, `[M]`),
                         decodificatore VERO.
                         ATTESO: `video.misura_massima` ≥ 1920x1080 e NON la
                         misura dello schermo · tela concessa 1920x1080 ·
                         ⭐ **almeno un fotogramma dipinto**, e la tela del
                         prodotto NON uniforme.

  giro «telefono»        stesso schermo, ⛔ decodificatore INCAPPUCCIATO a
                         1280x720 dal banco (`02-pagina-misura-cdp.py`).
                         ATTESO: `video.misura_massima` = **1280x720** — cioe'
                         chi davvero non decodifica oltre una misura CONTINUA a
                         dichiararlo — · tela concessa dentro quel tetto ·
                         ⛔ nessun fotogramma (il server cattura 1920x1080 e
                         §6.2 gli vieta di spedirlo sotto un'altra etichetta) ·
                         ⭐ e **la pagina lo dice all'utente nel riquadro**.

⛔ Il secondo giro e' quel che rende il primo una misura invece che una
   speranza: cambia UNA cosa sola — il tetto del decodificatore — e la pretesa
   «un fotogramma dipinto» **cade**.  Un banco che non sappia diventare rosso
   non dice niente quando e' verde (`CODER.md` §4.6).

⚠ E il giro «telefono» e' anche l'unico posto in cui si prova che dichiarare
  «4K sempre» romperebbe il telefono: li' il tetto vero e' 1280x720, e se la
  pagina dichiarasse di piu' il server concederebbe una tela che quel
  decodificatore rifiuta.
"""
import argparse
import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_s = importlib.util.spec_from_file_location(
    "cdp", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "02-pagina-misura-cdp.py"))
cdp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(cdp)

VERDE = "\033[1;32m"; ROSSO = "\033[1;31m"; GIALLO = "\033[1;33m"; GRIGIO = "\033[0m"


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


# ---------------------------------------------------------------------------
# ⛔ Le espressioni che il banco valuta DENTRO la pagina.  Nessuna di esse
#    cambia niente: leggono `window.REMOTIX`, che esiste per la diagnosi, e i
#    pixel della tela del prodotto.
LEGGI_SONDAGGIO = """
(async function () {
  if (!window.REMOTIX) return { pronto: false };
  const s = await window.REMOTIX.sondaggio;
  const m = s.misura || {};
  return { pronto: true,
           schermo: [screen.width, screen.height, devicePixelRatio],
           tetto_banco: window.__BANCO_TETTO__ || null,
           misura: m.massima ? m.massima.join("x") : null,
           ms: m.ms,
           per_codec: Object.keys(m.per_codec || {}).map((n) => ({
             codec: n, ms: m.per_codec[n].ms,
             massima: m.per_codec[n].massima
                        ? m.per_codec[n].massima.join("x") : null,
             fermato: m.per_codec[n].fermato,
             gradini: m.per_codec[n].gradini.map(
               (g) => g.misura + (g.arriva ? "=si" : "=NO") + "/" + g.ms + "ms") })),
           codec: Object.keys(s.codec).filter((n) =>
             (s.codec[n][8] && s.codec[n][8].arriva) ||
             (s.codec[n][10] && s.codec[n][10].arriva)) };
})()
"""

ENTRA = """
(function () {
  const u = document.getElementById("utente");
  const p = document.getElementById("parola");
  if (!u || !p) return "⛔ il modulo non c'e'";
  u.value = %s; p.value = %s;
  document.getElementById("modulo").requestSubmit();
  return "inviato";
})()
"""

# ⭐ IL SECONDO PIANO DEL METRO: i pixel si rileggono DALLA TELA DEL PRODOTTO,
#    con `getImageData` — che e' quel che `P2-6` §7 punto 1 diceva mancante.
#    ⛔ E si guarda la VARIANZA, non la media: una tela nera e una tela verde
#      hanno due medie diverse e nessuna delle due porta un'immagine.
LEGGI_ESITO = """
(function () {
  const s = window.REMOTIX && window.REMOTIX.schermo;
  const d = document.getElementById("dichiarazione");
  const fuori = { conti: s ? s.conti : null, errori: s ? s.errori : null,
                  dichiarazione: d ? d.textContent : null,
                  esito: (document.getElementById("esito") || {}).textContent,
                  registro: (document.getElementById("registro") || {}).textContent };
  const t = document.getElementById("schermo");
  if (t && t.width > 16) {
    fuori.tela = [t.width, t.height];
    try {
      const p = t.getContext("2d", { willReadFrequently: true });
      const im = p.getImageData(0, 0, t.width, t.height).data;
      let n = 0, sr = 0, sg = 0, sb = 0, s2 = 0, neri = 0;
      for (let i = 0; i < im.length; i += 4 * 37) {
        const r = im[i], g = im[i + 1], b = im[i + 2];
        sr += r; sg += g; sb += b; s2 += r * r + g * g + b * b;
        if (r + g + b < 24) neri++;
        n++;
      }
      const mr = sr / n, mg = sg / n, mb = sb / n;
      fuori.pixel = { campioni: n,
                      medio: [Math.round(mr), Math.round(mg), Math.round(mb)],
                      scarto: Math.round(Math.sqrt(Math.max(0,
                        s2 / (3 * n) - (mr * mr + mg * mg + mb * mb) / 3))),
                      frazione_nera: Math.round(1000 * neri / n) / 1000 };
    } catch (e) { fuori.pixel = { errore: String(e) }; }
  }
  return fuori;
})()
"""


def aspetta(c, espressione, quanto, passo=0.5):
    fine = time.time() + quanto
    ultimo = None
    while time.time() < fine:
        ultimo = c.valuta(espressione)
        if ultimo:
            return ultimo
        time.sleep(passo)
    return ultimo


def batti(c, testo):
    """⛔ «thisisunsafe» si BATTE, non si aggira con un flag: togliere
    l'interstiziale con `--ignore-certificate-errors` toglierebbe dalla misura
    proprio la cosa che l'utente fa la prima volta.  Stessa scelta di
    `02-montaggio-scheda.sh`, fatta con lo stesso strumento della scheda."""
    for ch in testo:
        for tipo in ("keyDown", "char", "keyUp"):
            p = {"type": tipo, "text": ch} if tipo == "char" else {"type": tipo}
            if tipo != "char":
                p["key"] = ch
            c.chiama("Input.dispatchKeyEvent", **p)
        time.sleep(0.03)


def giro(nome, args, tetto):
    log(f"Il giro «{nome}»" + (f" — decodificatore incappucciato a {tetto}"
                               if tetto else " — decodificatore VERO"))
    b = cdp.pagina(args.diagnosi)
    c = cdp.Cdp(b["webSocketDebuggerUrl"])
    fuori = {"giro": nome, "tetto_banco": tetto}
    try:
        c.chiama("Page.enable")
        c.chiama("Runtime.enable")
        if tetto:
            l, a = (int(x) for x in tetto.split("x"))
            c.chiama("Page.addScriptToEvaluateOnNewDocument",
                     source=cdp.PROLOGO_TELEFONO % (l, a))
            inf("prologo del telefono innestato PRIMA di ogni script della pagina")
        c.chiama("Page.navigate", url=args.url)
        time.sleep(4)
        titolo = c.valuta("document.title", attendi=False)
        if isinstance(titolo, str) and "Privacy" in titolo or \
           c.valuta("!!document.getElementById('proceed-link')", attendi=False):
            inf("interstiziale del certificato: batto «thisisunsafe»")
            batti(c, "thisisunsafe")
            time.sleep(5)
        s = aspetta(c, LEGGI_SONDAGGIO, args.attesa_sonda)
        if not s or not s.get("pronto"):
            ko(f"⛔ la pagina non ha esposto REMOTIX in {args.attesa_sonda} s: {s}")
            fuori["guaio"] = "REMOTIX assente"
            return fuori
        fuori["sondaggio"] = s
        inf(f"schermo: {s['schermo'][0]}x{s['schermo'][1]} · dPR {s['schermo'][2]}")
        inf(f"codec che arrivano al pixel: {s['codec'] or 'NESSUNO'}")
        for p in s["per_codec"]:
            inf(f"scala {p['codec']}: fino a {p['massima']} in {p['ms']} ms "
                f"[{' '.join(p['gradini'])}]"
                + (f" — fermata a {p['fermato']}" if p["fermato"] else ""))
        ok(f"⭐ video.misura_massima MISURATA: {s['misura']} "
           f"(scala intera: {s['ms']} ms)")

        with open(args.parola_file) as f:
            parola = f.read().strip()
        c.valuta(ENTRA % (json.dumps(args.utente), json.dumps(parola)),
                 attendi=False)
        del parola
        inf(f"credenziali inviate per «{args.utente}» (la parola non passa da argv)")

        fine = time.time() + args.attesa_video
        e = None
        while time.time() < fine:
            e = c.valuta(LEGGI_ESITO, attendi=False)
            if e and e.get("conti") and e["conti"].get("dipinti", 0) > 0:
                break
            time.sleep(1)
        fuori["esito"] = e
        return fuori
    finally:
        # ⛔⭐ IL POSTO SI LASCIA, e non basta ammazzare il browser.  `[M]` 13
        #    agosto 2026, primo giro doppio: il secondo giro e' finito con
        #    *«quell'utente e' gia' collegato da un altro dispositivo»* — il
        #    posto del giro prima era ancora occupato, perche' il server lo
        #    libera dopo trenta secondi di silenzio (§4.4-bis) e un `kill` del
        #    browser non manda nessun `CONGEDO`.
        #    ⇒ Si naviga via: `pagehide` fa partire il congedo che la pagina ha
        #      gia' (§8.1), e il posto torna libero subito.  ⚠ Senza, il
        #      secondo giro misurerebbe un congedo invece che una sessione, e
        #      direbbe rosso per la ragione sbagliata.
        try:
            c.chiama("Page.navigate", url="about:blank")
            time.sleep(1.5)
        except Exception:                     # noqa: BLE001
            pass
        c.chiudi()


# ---------------------------------------------------------------------------
def verdetto(r, args):
    """⛔ L'ATTESO E' SCRITTO QUI, PRIMA DEL GIRO, e il confronto lo fa questo
    programma — non chi legge l'uscita (`banchi/01-b0-...` B0.4)."""
    nome = r["giro"]
    s = r.get("sondaggio") or {}
    e = r.get("esito") or {}
    conti = e.get("conti") or {}
    pixel = e.get("pixel") or {}
    guai = []
    schermo = s.get("schermo") or [0, 0, 1]
    scher_str = f"{int(schermo[0] * schermo[2])}x{int(schermo[1] * schermo[2])}"

    def pretesa(vero, testo):
        (ok if vero else ko)(testo)
        if not vero:
            guai.append(testo)

    log(f"Il verdetto del giro «{nome}» — l'atteso era scritto prima")
    if nome == "schermo-corto":
        pretesa(schermo[1] * schermo[2] < 1080,
                f"lo schermo e' piu' CORTO di 1080 ({scher_str}): e' la scena "
                f"che il difetto voleva")
        pretesa(s.get("misura") not in (None, scher_str),
                f"video.misura_massima ({s.get('misura')}) NON e' la misura "
                f"dello schermo ({scher_str}): sono due grandezze diverse (§4.3)")
        m = (s.get("misura") or "0x0").split("x")
        pretesa(int(m[0]) >= 1920 and int(m[1]) >= 1080,
                f"il tetto misurato ({s.get('misura')}) sta sopra la tela di "
                f"1920x1080 che la pagina chiede")
        pretesa(conti.get("dipinti", 0) >= 1,
                f"⭐ FOTOGRAMMI DIPINTI: {conti.get('dipinti', 0)} — e' il metro "
                f"di questo banco")
        pretesa(pixel.get("scarto", 0) > 8,
                f"e la tela del prodotto NON e' uniforme (scarto "
                f"{pixel.get('scarto')}, campioni {pixel.get('campioni')}, "
                f"nera al {100 * pixel.get('frazione_nera', 1):.0f}%): "
                f"«ha dipinto» e «e' rimasta com'era» non hanno lo stesso aspetto")
    elif nome == "telefono":
        pretesa(s.get("misura") == r["tetto_banco"],
                f"⛔ IL CASO OPPOSTO: il decodificatore si ferma a "
                f"{r['tetto_banco']} e la pagina dichiara {s.get('misura')} — "
                f"chi non decodifica oltre una misura CONTINUA a dichiararlo")
        pretesa(conti.get("dipinti", 0) == 0,
                f"e con quel tetto il fotogramma NON arriva "
                f"({conti.get('dipinti', 0)} dipinti): e' il controllo negativo "
                f"— la pretesa del primo giro sa cadere")
        d = e.get("dichiarazione") or ""
        pretesa("Nessun fotogramma" in d,
                "⭐ e LA PAGINA LO DICE ALL'UTENTE, nel riquadro e in italiano "
                "(CODER.md §4.2)")
        pretesa("tela" in d.lower(),
                "e la frase nomina la tela, cioe' la causa: non «qualcosa non "
                "va»")
        if d:
            for riga in d.split("\n"):
                if riga.strip():
                    inf(f"riquadro: {riga.strip()[:150]}")
    return guai


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--giro", required=True, choices=("schermo-corto", "telefono"))
    a.add_argument("--url", required=True)
    a.add_argument("--diagnosi", type=int, required=True)
    a.add_argument("--utente", default="nicfio")
    a.add_argument("--parola-file", required=True)
    a.add_argument("--tetto", default="")
    a.add_argument("--attesa-sonda", type=int, default=60)
    a.add_argument("--attesa-video", type=int, default=30)
    a.add_argument("--uscita", default="")
    args = a.parse_args()

    r = giro(args.giro, args, args.tetto or None)
    guai = verdetto(r, args)
    r["guai"] = guai
    if args.uscita:
        with open(args.uscita, "a") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print()
    if guai:
        print(f"    {ROSSO}⛔ il giro «{args.giro}»: {len(guai)} pretese non "
              f"onorate{GRIGIO}")
        sys.exit(1)
    print(f"    {VERDE}⭐ il giro «{args.giro}»: tutte le pretese onorate{GRIGIO}")
    sys.exit(0)
