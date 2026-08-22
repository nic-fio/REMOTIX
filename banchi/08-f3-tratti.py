#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""08-F3 · ⭐⭐ I QUATTRO TRATTI DEL CLIENTE, LETTI DA UNA SESSIONE VERA.

⛔⛔ PERCHE' QUESTO BANCO ESISTE, e non e' un doppione di `04-b30`.

  L'agente A ha scomposto l'anello e ha trovato `[M]` **17,48 ms** nel tratto
  *«richiamo del decodificatore → 1° `drawImage` finito»*, contro **0,10** del
  disegno vero.  ⛔ Ma quel numero e' della strada **`?tela=2d`** — la strada
  del 14 agosto — perche' il prologo di `04-b30` legge i pixel dal deposito, e
  dal 20 agosto il deposito **non esiste piu'** (`DECISIONI.md` §5.4).

  ⇒ ⭐ Qui NON si riscrive quel prologo.  I tratti li dichiara **il prodotto**
    (`REMOTIX.tratti()`, `src/pagina.html`), e questo banco li LEGGE — sulla
    strada `bitmaprenderer` come sulla `?tela=2d`, con gli stessi nomi.
    ⛔ E' la differenza fra misurare la pagina e misurare uno strumento
      innestato nella pagina.

⚠ E QUEL CHE QUESTO BANCO NON SA FARE, dichiarato: non misura l'anello, non
  misura il distacco, non ha un'ancora sul server.  Il metro finale della fase
  resta `banchi/08-b67-elastico.py`, che non si tocca.

⛔ IL CONFRONTO SI FA QUI, non a occhio: le due strade si girano nella STESSA
  seduta, sulla STESSA sessione, e la riga finale e' una sottrazione.
"""
import argparse
import json
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")

USCITA_CONFORME, USCITA_NON_CONFORME, USCITA_NIENTE = 0, 1, 3

# ⭐ `[M]` agente A, 22 agosto 2026, strada `?tela=2d`, mediana di 5 giri.
A9, A10 = 17.48, 0.10

TRATTI = [
    ("8_decode_richiamo",        "8  · `decode()` → richiamo      "),
    ("9a_richiamo_chiamata",     "9a · richiamo → chiamata        "),
    ("9b_conversione",           "9b · la conversione             "),
    ("10_vetro",                 "10 · il vetro                   "),
    ("9_10_richiamo_vetro",      "⭐ 9+10 · richiamo → VETRO      "),
    ("11_vetro_prossimo_quadro", "11 · vetro → prossimo quadro    "),
]


def carica(nome, percorso):
    import importlib.util
    s = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def b17():
    return carica("b17", os.path.join(QUI, "03-b17-ritardo.py"))


def b67():
    """⭐ Il `batti()` (il `thisisunsafe`) e il superamento dell'avviso vengono
    da `08-b67-elastico.py` e NON si ricopiano.  ⛔ Quel modulo fa `argparse` a
    livello di modulo? — no: lo fa dentro `main()`, quindi si importa senza che
    parta un altro banco.  ⚠ E se un giorno lo facesse, questa riga fallirebbe
    rumorosamente invece di lanciare un banco per sbaglio."""
    return carica("b67", os.path.join(QUI, "08-b67-elastico.py"))


def un_giro(palco, m67, a, coda, giro):
    """Un giro: apre la pagina, entra, aspetta che dipinga, muove la mano,
    e legge `REMOTIX.tratti()`."""
    url = "https://%s:%d/%s" % (a.host, a.porta, coda or "")
    palco.chiama("Page.navigate", url=url)
    time.sleep(3.0)
    if not m67.supera_l_avviso(palco, url):
        ko("⛔ l'avviso del certificato NON si e' superato: la pagina non e' "
           "mai stata caricata.  ⚠ Non e' «il prodotto non disegna»")
        return None
    parola = ""
    if a.parola_file and os.path.exists(a.parola_file):
        with open(a.parola_file) as f:
            parola = f.read().strip()
    if not parola:
        ko("⛔ nessuna parola d'ordine (--parola-file): non entro")
        return None
    palco.valuta(
        "(function(){var u=document.getElementById('utente');"
        "var p=document.getElementById('parola');"
        "if(!u||!p) return 'no-modulo';"
        "u.value=%s; p.value=%s;"
        "var f=document.getElementById('modulo');"
        "if(f) f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));"
        "return 'inviato';})()" % (json.dumps(a.utente), json.dumps(parola)),
        attendi=False)
    fine = time.time() + 60
    pronto = False
    while time.time() < fine:
        r = palco.valuta("(window.REMOTIX && REMOTIX.schermo && "
                         " REMOTIX.schermo.conti.dipinti) || 0", attendi=False)
        try:
            if int(r or 0) > 0:
                pronto = True
                break
        except Exception:                                # noqa: BLE001
            pass
        time.sleep(1.0)
    if not pronto:
        ko("⛔ la pagina non ha dipinto NESSUN fotogramma in 60 s: non e' «il "
           "ritardo e' grande», e' «non ho potuto guardare»")
        return None
    ok("la sessione e' aperta e la pagina dipinge")

    # ⛔ E `REMOTIX.tratti` DEVE esserci: se la macchina serve una pagina
    #    vecchia, ogni numero di questo giro sarebbe di un'altra pagina.
    if not palco.valuta("typeof (window.REMOTIX && REMOTIX.tratti) === "
                        "'function'", attendi=False):
        ko("⛔ questa pagina NON ha `REMOTIX.tratti()`: il server sta servendo "
           "una `pagina.html` vecchia.  ⇒ Non misuro: sarebbe un numero di un "
           "altro prodotto")
        return None

    # ── ⭐⭐ SI GUARDA CHE LA SCENA STIA DAVVERO CONSEGNANDO ─────────────
    #
    # ⛔⛔ E QUESTO CONTROLLO NASCE DA UN ROSSO DI OGGI: il primo giro ha letto
    #     `[M]` **2 fotogrammi dipinti in 30 secondi** — cioe' un desktop fermo
    #     — e i tratti erano tutti `null`.  ⚠ Senza questa riga il banco
    #     avrebbe consegnato «non misurato» senza dire che il PALCO era vuoto,
    #     ed e' la forma di `LEZIONI.md` §1.21: uno strumento che tace quando
    #     non ha guardato sembra uno strumento che ha guardato e non ha visto.
    #
    # ⛔ E LA MANO NON SI MUOVE PIU' DA QUI, con la ragione: `Input.dispatch-
    #    MouseEvent` via CDP ha impiegato `[M]` **5 secondi per evento** su
    #    questa sessione (6 movimenti in 30 s).  ⇒ Non era una mano: era un
    #    freno.  E per i tratti del CLIENTE la mano non serve — serve che
    #    arrivino fotogrammi, e a farli arrivare basta la scena a 60/s.
    d0 = int(palco.valuta("REMOTIX.schermo.conti.dipinti", attendi=False) or 0)
    time.sleep(3.0)
    d1 = int(palco.valuta("REMOTIX.schermo.conti.dipinti", attendi=False) or 0)
    ritmo = (d1 - d0) / 3.0
    if ritmo < 5.0:
        ko("⛔ la pagina dipinge %.1f fotogrammi/s: il PALCO e' fermo (la scena "
           "non e' sul monitor di questa sessione).  ⇒ NON misuro: sarebbe "
           "«non ho potuto guardare» travestito da «non misurato»" % ritmo)
        return None
    ok("la pagina dipinge %.1f fotogrammi/s: c'e' da misurare" % ritmo)

    # ⛔ Si azzerano i tratti PRIMA della misura: quel che c'e' dentro adesso e'
    #    l'accensione della sessione (la prima chiave, la prima misura di tela),
    #    che non e' regime.
    palco.valuta("(function(){var s=REMOTIX.schermo;"
                 "s.dec_ms.length=0; s.pre_ms.length=0; s.bmp_ms.length=0;"
                 "s.vetro_ms.length=0; s.tot_ms.length=0; s.quadro_ms.length=0;"
                 "return 1;})()", attendi=False)
    d0 = int(palco.valuta("REMOTIX.schermo.conti.dipinti", attendi=False) or 0)
    t0 = time.time()
    time.sleep(a.secondi)
    d1 = int(palco.valuta("REMOTIX.schermo.conti.dipinti", attendi=False) or 0)
    sec = time.time() - t0
    i = d1 - d0
    inf("⭐ %d fotogrammi dipinti in %.1f s = %.1f/s (`LEZIONI.md` §6.2: i "
        "fotogrammi vanno ACCANTO ai millisecondi)" % (i, sec, i / sec))

    t = palco.valuta("JSON.stringify(REMOTIX.tratti())", attendi=False)
    conti = palco.valuta("JSON.stringify(REMOTIX.schermo.conti)", attendi=False)
    palco_j = palco.valuta(
        "(function(){var s=REMOTIX.schermo;var g=null;"
        "try{var c=document.createElement('canvas').getContext('webgl');"
        "var d=c&&c.getExtension('WEBGL_debug_renderer_info');"
        "g=d?c.getParameter(d.UNMASKED_RENDERER_WEBGL):null;}catch(e){}"
        "return JSON.stringify({gpu:g, stringa:s.stringa, dpr:devicePixelRatio,"
        " tela:[s.tela_l,s.tela_a], formato:s.formato,"
        " errori:s.errori.slice(-4)});})()", attendi=False)
    return {"giro": giro, "coda_url": coda or "",
            "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "fotogrammi": i, "secondi": round(sec, 2), "dipinti_nel_giro": i,
            "tratti": json.loads(t) if t else None,
            "conti": json.loads(conti) if conti else None,
            "palco": json.loads(palco_j) if palco_j else None}


def stampa(v):
    t = v.get("tratti")
    if not t:
        ko("⛔ nessun tratto: non ho niente da giudicare")
        return False
    inf("strada **%s** · tela %s · dipinti %s · saltati in coda %s · tardive %s"
        % (t["strada"], t["tela"], t["dipinti"], t["saltati_coda"],
           t["tardive"]))
    if v.get("palco"):
        p = v["palco"]
        inf("palco · codec «%s» · GPU %s · formato %s · errori %s"
            % (p.get("stringa"), p.get("gpu"), p.get("formato"),
               p.get("errori") or "nessuno"))
    for k, e in TRATTI:
        s = t.get(k)
        if not s:
            print("        %s  —  ⛔ non misurato" % e)
            continue
        print("        %s  n=%-4d med=%7.2f  [p05 %6.2f · p95 %6.2f · max %7.2f]"
              % (e, s["n"], s["med"], s["p05"], s["p95"], s["max"]))
    return True


def giudica(giri):
    """⛔ E QUI I NUMERI SI CONFRONTANO — `LEZIONI.md` §1.20."""
    rossi = 0
    log("IL GIUDIZIO — ⛔ e non e' una stampa")
    atteso = A9 + A10
    print("\n    ⭐⭐ IL «PRIMA» DELL'AGENTE A, strada `?tela=2d`: 9+10 = %.2f ms"
          % atteso)
    for v in giri:
        t = v.get("tratti") or {}
        s = t.get("9_10_richiamo_vetro")
        if not s:
            ko("⛔ giro «%s»: il tratto 9+10 non c'e'" % v["giro"])
            rossi += 1
            continue
        print("        %-22s (%s)  9+10 = %7.2f ms  su n=%d  ⇒ %+.2f ms sul «prima»"
              % (v["giro"], t["strada"], s["med"], s["n"], s["med"] - atteso))

    # ── ⭐ IL FOTOGRAMMA E' UNA GRANDEZZA A PARTE, e va accanto sempre ─────
    #    `LEZIONI.md` §6.2: millisecondi per fotogramma, fotogrammi al secondo
    #    e ritardo si muovono INDIPENDENTEMENTE.  Una tabella con una colonna
    #    sola non e' una misura corta: e' una misura ORIENTATA.
    print("\n    ⭐ E I FOTOGRAMMI ACCANTO AI MILLISECONDI (`LEZIONI.md` §6.2)")
    for v in giri:
        t = v.get("tratti") or {}
        sec = v.get("secondi") or 1
        d = t.get("dipinti")
        print("        %-22s dipinti %s in %.1f s ⇒ %.1f/s · saltati in coda %s"
              % (v["giro"], d, sec, (d or 0) / sec, t.get("saltati_coda")))

    # ── il confronto fra le due strade, se ci sono tutt'e due ─────────────
    per_strada = {}
    for v in giri:
        t = v.get("tratti") or {}
        if t.get("9_10_richiamo_vetro"):
            per_strada[t["strada"]] = t["9_10_richiamo_vetro"]["med"]
    if len(per_strada) >= 2 and "bitmaprenderer" in per_strada:
        vera = per_strada["bitmaprenderer"]
        for nome, val in per_strada.items():
            if nome == "bitmaprenderer":
                continue
            print("\n    ⭐⭐ LE DUE STRADE, LA STESSA SESSIONE")
            print("        %-22s %7.2f ms" % (nome, val))
            print("        %-22s %7.2f ms  ⇒ %+.2f ms (%+.0f %%)"
                  % ("bitmaprenderer", vera, vera - val,
                     100.0 * (vera - val) / val if val else 0))
    else:
        dub("⚠ una strada sola: il confronto fra le due NON e' stato fatto in "
            "questa seduta, e non si prende da un'altra")

    # ── ⛔ e il tratto 9a DEVE valere ~0, o qualcuno ha infilato del lavoro
    #      fra il richiamo e la conversione senza che nessun conto lo veda ──
    for v in giri:
        t = v.get("tratti") or {}
        s = t.get("9a_richiamo_chiamata")
        if s and s["med"] > 1.0:
            ko("⛔ giro «%s»: fra il richiamo e la conversione passano %.2f ms, "
               "e non dovrebbero essere piu' di ~0" % (v["giro"], s["med"]))
            rossi += 1
    if not rossi:
        ok("il tratto 9a vale ~0 in tutti i giri: fra il richiamo e la "
           "conversione non c'e' nessun lavoro nascosto")
    return rossi


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7770)
    p.add_argument("--utente", default="provaf3")
    p.add_argument("--parola-file", default="/tmp/08-f3/parola")
    p.add_argument("--secondi", type=float, default=30.0)
    p.add_argument("--schermo", default=":92")
    p.add_argument("--diagnosi", type=int, default=9692)
    p.add_argument("--lavoro", default="/tmp/08-f3")
    # ⛔ La stessa finestra di `08-b67-elastico.py`: una finestra
    #    diversa fa chiedere una TELA diversa, e la scena resta sul
    #    monitor di prima — `[M]` 1520x868 invece di 1560x888, e zero
    #    fotogrammi da misurare.
    p.add_argument("--larghezza", type=int, default=1600)
    p.add_argument("--altezza", type=int, default=1000)
    p.add_argument("--giro", default="f3")
    p.add_argument("--coda-url", default=None,
                   help="⭐ una coda all'indirizzo; se non c'e', si girano "
                        "TUTT'E DUE le strade (vera e `?tela=2d`)")
    a = p.parse_args()

    m17, m67 = b17(), b67()
    log("IL PALCO — Xvfb + Chrome sul PORTATILE, cioe' il client vero")
    palco = m17.Palco(schermo=a.schermo, diagnosi=a.diagnosi,
                      finestra=(a.larghezza, a.altezza), lavoro=a.lavoro,
                      gpu=True)
    giri, verbali = [], []
    code = [a.coda_url] if a.coda_url is not None else ["", "?tela=2d"]
    try:
        misurato = palco.accendi()
        ok("Xvfb %s e Chrome accesi" % misurato)
        for c in code:
            log("GIRO «%s» — coda «%s»" % (a.giro, c or "(nessuna: la strada vera)"))
            v = un_giro(palco, m67, a, c, a.giro + ("-2d" if c else "-vera"))
            if v is None:
                continue
            v["palco_xvfb"] = misurato
            v["bandiere"] = palco.bandiere
            giri.append(v)
            stampa(v)
            verbali.append(v)
    finally:
        try:
            palco.spegni()
        except Exception:                                # noqa: BLE001
            pass

    with open(os.path.join(QUI, "08-f3-esiti.jsonl"), "a") as f:
        for v in verbali:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")

    if not giri:
        ko("⛔ nessun giro e' arrivato in fondo: NON e' «conforme»")
        return USCITA_NIENTE
    return USCITA_CONFORME if giudica(giri) == 0 else USCITA_NON_CONFORME


if __name__ == "__main__":
    sys.exit(main())
