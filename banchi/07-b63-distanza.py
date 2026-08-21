#!/usr/bin/env python3
"""07-b63-distanza.py — ⭐⭐ LA DISTANZA FRA QUEL CHE SI SENTE E QUEL CHE SI VEDE.

    python3 banchi/07-b63-distanza.py --certifica     ⛔ PRIMA di credergli
    python3 banchi/07-b63-distanza.py --secondi 90

═══════════════════════════════════════════════════════════════════════════════
⛔ PERCHE' ESISTE, E PERCHE' NON POTEVA ESISTERE PRIMA
═══════════════════════════════════════════════════════════════════════════════

L'utente, il 21 agosto 2026: *«il ritardo di 400 ms tra audio e video te lo
confermo»*.  ⛔ E **nessun contatore della pagina poteva vederlo**: contano tutti
un flusso per volta — i blocchi audio suonati, i fotogrammi dipinti — e il
difetto non sta in nessuno dei due, sta **fra** i due.  ⇒ Quattro anelli verdi
hanno convissuto per giorni con un'esperienza sbagliata, ed e' esattamente la
forma di cecita' che `LEZIONI.md` §2.7 descrive: servono TUTTI gli anelli, e qui
ne mancava uno che non era un anello ma una **distanza**.

⭐ IL METRO NON HA BISOGNO NE' DI UN MICROFONO NE' DI UNA SCENA PREPARATA, e il
  dato c'era gia' nel protocollo:

  | | |
  |---|---|
  | `RCP.md` §6.2 | l'intestazione del fotogramma porta l'`istante` del SERVER |
  | `RCP.md` §6.3 | il datagram dell'audio porta l'`istante` dello STESSO server |

  `aoff` = (ora del client in cui il campione SUONA) − (istante del server)   ← A1
  `voff` = (ora del client in cui il fotogramma e' AL VETRO) − (istante)      ← A7

  Tutt'e due contengono lo scarto ignoto fra i due orologi, e quello e' lo
  STESSO.  ⇒ **`AV = aoff − voff` e' la distanza**, e la costante si elide.
  Positivo = il suono esce DOPO l'immagine.

═══════════════════════════════════════════════════════════════════════════════
⛔ I TRE CONTROLLI CHE VENGONO PRIMA DEL NUMERO
═══════════════════════════════════════════════════════════════════════════════

  C1  ⭐ **la premessa si misura, non si crede** — `voff` deve essere STABILE.
      `voff` e' «orologio del client − orologio del server + ritardo»: due
      orologi che ticchettano allo stesso ritmo, quindi il numero deve stare
      fermo entro qualche decina di ms.  ⛔ Se Firefox mettesse nel
      `VideoFrame.timestamp` qualcosa che NON e' l'`istante` del server — un
      indice di presentazione, uno zero — `voff` scapperebbe via, e la distanza
      sarebbe un numero grande, credibile e falso.  ⇒ Questo controllo guarda
      IL METRO, non il prodotto, ed e' l'unico qui che lo fa (la regola di
      `03-b18-credito.py`, presa di peso).
  C2  ⛔ **i due flussi devono essere VIVI tutt'e due**: `dipinti` e `suonati`
      devono crescere.  Senza, `AV` non e' una distanza piccola — e' una
      distanza **assente**, e zero contro zero passa verde (e' il difetto che
      ho appena trovato in `03-b19`).
  C3  ⛔ **la scena si muove**: su un desktop fermo Mutter non consegna
      fotogrammi e `voff` invecchia, mentre l'audio continua ⇒ `AV` cresce da
      sola e accusa il prodotto di un difetto della scena.

═══════════════════════════════════════════════════════════════════════════════
⚠ IL BUCO CIECO, DICHIARATO — e non e' piccolo
═══════════════════════════════════════════════════════════════════════════════

Le due meta' **non sono simmetriche**:
  · `aoff` include `outputLatency` — il suono esce dal dispositivo DOPO che la
    pagina l'ha programmato, e su qualche motore non e' zero;
  · `voff` NON puo' includere l'equivalente, perche' fra
    `transferFromImageBitmap` e il pixel acceso ci sono i `[?]` **16-40 ms** del
    compositore che nessuna API espone (`CODER.md` §1-bis).

⇒ **`AV` sovrastima il ritardo dell'audio di quei 16-40 ms.**  Si scrive accanto
  al numero e non si sottrae: sottrarre una stima e' fabbricare una misura.
"""
import argparse
import importlib.util as _iu
import json
import os
import statistics
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
ALBERO = os.path.dirname(QUI)
_spec = _iu.spec_from_file_location(
    "marionette", os.path.join(QUI, "07-b46-marionette.py"))
M = _iu.module_from_spec(_spec)
_spec.loader.exec_module(M)

VERDE, ROSSO, GRIGIO, FINE = "\033[1;32m", "\033[1;31m", "\033[2m", "\033[0m"
ROSSI = [0]


def ok(t):  print("    %sOK%s  %s" % (VERDE, FINE, t))
def ko(t):  ROSSI[0] += 1; print("    %sNO%s  %s" % (ROSSO, FINE, t))
def inf(t): print("    --  %s" % t)
def log(t): print("\n\033[1m== %s\033[0m" % t)


# ⛔ Un campione porta TUTTO quel che serve a giudicarlo, non solo `AV`: senza
#    i due addendi, «l'audio e' indietro» e «il video e' avanti» hanno la stessa
#    faccia, e sono due cure diverse.  Senza i contatori, non si sa se i due
#    flussi erano vivi nell'istante in cui il numero e' stato preso.
CAMPIONE = """
  const s = (window.REMOTIX && REMOTIX.schermo) || null;
  if (!s || typeof s.voff_ms !== 'function') return null;
  const c = (typeof audio_conti === 'function') ? audio_conti() : null;
  const v = s.voff_ms();
  return { t: performance.now(),
           voff: v,
           aoff: c ? c.aoff_ms : null,
           usc: c ? c.uscita_ms : null,
           av: (v === null || !c || c.aoff_ms === null) ? null : c.aoff_ms - v,
           dipinti: s.conti.dipinti,
           salt: s.conti.saltati_coda, buchi: s.conti.buchi,
           ord: s.conti.scartati_ordine, mis: s.conti.scartati_misura,
           tard: s.conti.tardive, err: s.errori.length,
           suonati: c ? c.suonati : null, usciti: c ? c.usciti : null,
           audio_buchi: c ? c.riarmi : null,
           coda_ms: c ? c.in_coda_ms : null,
           ctx: c ? c.contesto : null };
"""


def carico(macchina=None):
    if macchina:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", macchina, "cat /proc/loadavg"],
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip().split(" ")[0] if r.returncode == 0 else "?"
    return open("/proc/loadavg").read().split(" ")[0]


def riassunto(a):
    if not a:
        return None
    b = sorted(a)
    return {"n": len(b), "min": b[0], "med": b[len(b) // 2], "max": b[-1],
            "p05": b[int(0.05 * (len(b) - 1))], "p95": b[int(0.95 * (len(b) - 1))]}


def certifica():
    """⛔ Il banco si certifica prima di essere creduto, e QUI il guasto si
    innesta nei DATI: si danno **allo stesso giudice** che gira sul vero
    (`giudica_voff`) quattro serie note, e si pretende che dica la cosa giusta
    su tutte e quattro.  ⚠ Un giudice scritto due volte — uno per la
    certificazione e uno per la misura — certificherebbe l'altro."""
    log("La certificazione — serie note date allo STESSO giudice del vero")
    casi = [
        # (nome, serie, passo_s, atteso «regge»)
        ("un `voff` FERMO (il metro regge)",
         [100.0 + (i % 3) for i in range(40)], 0.5, True),
        ("un `voff` che BALLA come la rete vera (±60 ms, senza deriva)",
         [100.0 + (60 if i % 2 else 0) for i in range(40)], 0.5, True),
        ("un `voff` CHE SCAPPA di 33 ms a campione (un indice di presentazione "
         "al posto dell'`istante`)",
         [100.0 + 33.0 * i for i in range(40)], 0.5, False),
        ("⭐ un `voff` che DERIVA PIANO — 1,8 ms/s: i due orologi non "
         "ticchettano uguale, e l'escursione da sola NON lo vede",
         [100.0 + 0.9 * i for i in range(40)], 0.5, False),
    ]
    esito = True
    for nome, serie, passo, atteso in casi:
        regge, esc, pend = giudica_voff(serie, passo)
        if regge == atteso:
            ok("%s → «%s» (escursione %.0f ms, deriva %+.2f ms/s)"
               % (nome, "regge" if regge else "NON regge", esc, pend))
        else:
            ko("%s: il giudice ha sbagliato ⇒ NON CERTIFICATO" % nome)
            esito = False
    # ⛔ E il controllo che accusa il BANCO: due flussi fermi non fanno una
    #    distanza piccola, fanno una distanza assente.
    if vivi_abbastanza({"dipinti": 10, "suonati": 10},
                       {"dipinti": 10, "suonati": 10}):
        ko("⛔ due flussi FERMI passano il controllo C2 ⇒ NON CERTIFICATO")
        esito = False
    else:
        ok("due flussi fermi: rifiutati (zero contro zero non passa verde)")
    if not vivi_abbastanza({"dipinti": 10, "suonati": 10},
                           {"dipinti": 400, "suonati": 900}):
        ko("⛔ due flussi VIVI vengono rifiutati ⇒ NON CERTIFICATO")
        esito = False
    else:
        ok("due flussi vivi: accettati (controllo negativo)")
    return 0 if esito else 3


# ⛔ La soglia della stabilita' di `voff`.  ⚠ Non e' un gusto: `voff` contiene
#    il RITARDO di consegna del fotogramma, che sulla catena vera oscilla di
#    qualche decina di ms (il giro completo misurato da `07-b63-worker.py` va da
#    39 a 110 ms).  ⇒ 150 ms lascia passare l'oscillazione vera e ferma la
#    fuga: un `timestamp` che fosse un indice di presentazione scapperebbe di
#    33 ms A FOTOGRAMMA, cioe' di secondi in pochi secondi.
SOGLIA_STABILE = 150.0

# ⛔⭐ E LA SECONDA SOGLIA, ED E' QUELLA CHE L'ESCURSIONE NON PUO' DARE.
#
#    Una deriva LENTA — due orologi che non ticchettano allo stesso ritmo —
#    resta dentro l'escursione per tutta la finestra di misura e **passa**.
#    `[M]` La prima stesura di questo file aveva un caso di certificazione con
#    0,9 ms a campione e il giudice lo dichiarava sano: cioe' il banco sarebbe
#    stato verde su un metro che si sfalsa di **6,5 secondi all'ora**.
#    ⇒ Si guarda anche la PENDENZA, e la si guarda su terzi (robusta al ballo
#      della rete, che una retta ai minimi quadrati si porterebbe dentro).
#
# ⚠ 1 ms/s e' larghissimo: due orologi disciplinati da NTP stanno sotto 0,1
#   ms/s, e a 1 ms/s in un'ora la distanza sarebbe sbagliata di 3,6 s.
SOGLIA_DERIVA_MS_S = 1.0


def centro(a):
    """⛔ La media SPUNTATA (via il 10 % piu' basso e il 10 % piu' alto), e non
    la mediana: `[M]` con una serie che BALLA fra due valori — che e' come si
    comporta un ritardo di rete a due stati — la mediana di un terzo salta da
    un valore all'altro secondo la PARITA' del conto, e la pendenza che ne
    usciva era **4,4 ms/s su una serie senza nessuna deriva**.  ⚠ E nemmeno la
    media nuda: un solo campione lontano la sposta."""
    b = sorted(a)
    k = len(b) // 10
    c = b[k:len(b) - k] or b
    return sum(c) / len(c)


def giudica_voff(vs, passo_s):
    """⛔ IL GIUDICE, e ne esiste UNO SOLO: lo chiamano sia la misura vera sia
    `--certifica`.  Torna (regge, escursione_ms, deriva_ms_al_secondo)."""
    r = riassunto(vs)
    esc = r["max"] - r["min"]
    n = len(vs)
    if n >= 9:
        primo = centro(vs[:n // 3])
        ultimo = centro(vs[2 * n // 3:])
        # la distanza fra i centri dei due terzi estremi, in secondi
        span = max((n - n // 3) * passo_s, passo_s)
        pend = (ultimo - primo) / span
    else:
        pend = 0.0
    return (esc <= SOGLIA_STABILE and abs(pend) <= SOGLIA_DERIVA_MS_S), esc, pend


def vivi_abbastanza(a, b):
    """C2: tutti e due i flussi devono essere cresciuti."""
    return (b["dipinti"] - a["dipinti"]) > 0 and (b["suonati"] - a["suonati"]) > 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ind", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7771)
    p.add_argument("--macchina", default="nicfio@192.168.0.2")
    p.add_argument("--utente", default="provav7")
    p.add_argument("--parola", default="provav7-2026")
    p.add_argument("--secondi", type=float, default=60)
    p.add_argument("--riscaldamento", type=float, default=5)
    p.add_argument("--passo", type=float, default=0.5)
    p.add_argument("--worker", action="store_true")
    p.add_argument("--larghezza", type=int, default=1600)
    p.add_argument("--altezza", type=int, default=1000)
    p.add_argument("--marionette", type=int, default=2864)
    p.add_argument("--fuori", default="/tmp/07-b63")
    p.add_argument("--schermo", default="",
                   help="uno schermo X virtuale (es. :63) invece di --headless")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    log("La distanza audio↔video su una sessione VERA — %.0f s, un campione ogni %.1f s"
        % (a.secondi, a.passo))
    inf("⚠ la scena deve essere VIVA: `bash banchi/07-b63-scena.sh avvia`")
    c0 = (carico(), carico(a.macchina))
    url = "https://%s:%d/%s" % (a.ind, a.porta, "?video=worker" if a.worker else "")
    # ⛔⭐ LE DUE PREFERENZE DEL BANCO, E SI DICHIARANO — cambiano la scena.
    #
    #    `[M]` 21 agosto 2026: con le preferenze predefinite il contesto audio
    #    resta `suspended` per tutti i 90 s, **anche dopo un clic vero di
    #    Marionette**, e la pagina butta ogni blocco (`sospesi`) ⇒ `aoff` non
    #    nasce mai e la distanza non e' misurabile.
    #    ⛔ E la ragione NON e' il banco: `pagina.html` chiama `resume()` **una
    #      volta sola**, alla nascita del contesto, e non c'e' nessun gestore
    #      che ci riprovi al primo gesto — cioe' la riga che la pagina scrive
    #      all'utente («il suono parte al primo clic») non ha codice sotto.
    #      Il difetto e' della regione AUDIO, che non e' mia: lo riferisco.
    #    ⇒ Qui si toglie di mezzo la politica di autoplay, perche' l'utente
    #      vero quel clic lo fa e il suo contesto parte.  ⚠ Se il numero
    #      dipendesse da queste righe si vedrebbe: `ctx` finisce nel verbale.
    pr, m, prof = M.accendi(porta=a.marionette, headless=not a.schermo,
                            schermo=(a.schermo or None),
                            largo=a.larghezza, alto=a.altezza,
                            profilo_prefs={"media.autoplay.default": 0,
                                           "media.autoplay.blocking_policy": 0,
                                           "media.autoplay.block-webaudio": False,
                                           "media.block-autoplay-until-in-foreground": False})
    camp = []
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(a.larghezza, a.altezza)
        m.vai(url)
        m.js("""
          document.getElementById('utente').value = arguments[0];
          document.getElementById('parola').value = arguments[1];
          document.getElementById('vai').click(); return true;
        """, [a.utente, a.parola])
        t0 = time.time()
        while time.time() - t0 < 30:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.4)
        else:
            ko("lo schermo non si e' acceso in 30 s — NON pubblico un numero")
            return 3
        # ⛔ IL CONTESTO AUDIO NASCE SOSPESO senza un gesto: un clic, o `aoff`
        #    resta `null` per sempre e questo banco misurerebbe il silenzio.
        #    ⚠ E il clic e' anche il gesto che l'utente fa davvero.
        try:
            m.chiama("WebDriver:PerformActions", {"actions": [{
                "type": "pointer", "id": "mouse",
                "parameters": {"pointerType": "mouse"},
                "actions": [{"type": "pointerMove", "duration": 30,
                             "origin": "viewport", "x": 500, "y": 400},
                            {"type": "pointerDown", "button": 0},
                            {"type": "pause", "duration": 60},
                            {"type": "pointerUp", "button": 0}]}]})
        except Exception as e:                                   # noqa: BLE001
            inf("il clic di risveglio non e' passato (%s)" % e)
        time.sleep(a.riscaldamento)
        t_a = time.time()
        while time.time() - t_a < a.secondi:
            r = m.js(CAMPIONE)["value"]
            if r:
                r["s"] = round(time.time() - t_a, 2)
                camp.append(r)
            time.sleep(a.passo)
        righe = m.js("return document.getElementById('registro').innerText.slice(-3000)")["value"]
        m.vai("about:blank")
        time.sleep(1.5)
    finally:
        M.spegni(pr, prof)
    c1 = (carico(), carico(a.macchina))

    if not camp:
        ko("nessun campione")
        return 3

    log("C2 — i due flussi erano vivi?")
    if not vivi_abbastanza(camp[0], camp[-1]):
        ko("⛔ dipinti %d→%d · suonati %s→%s: uno dei due e' FERMO ⇒ `AV` non e' "
           "piccola, e' ASSENTE.  NON pubblico un numero"
           % (camp[0]["dipinti"], camp[-1]["dipinti"],
              camp[0]["suonati"], camp[-1]["suonati"]))
        return 3
    dt = camp[-1]["s"] - camp[0]["s"]
    ok("dipinti +%d (%.1f/s) · suonati +%d — tutt'e due vivi"
       % (camp[-1]["dipinti"] - camp[0]["dipinti"],
          (camp[-1]["dipinti"] - camp[0]["dipinti"]) / max(dt, 0.01),
          camp[-1]["suonati"] - camp[0]["suonati"]))

    log("C1 — la premessa: `voff` sta fermo?")
    vs = [c["voff"] for c in camp if c["voff"] is not None]
    if not vs:
        ko("⛔ `voff` e' sempre `null`: il metro non c'e'")
        return 3
    rv = riassunto(vs)
    regge, esc, pend = giudica_voff(vs, a.passo)
    if regge:
        ok("`voff` mediana %.0f ms · escursione %.0f ms · deriva %+.2f ms/s su "
           "%d campioni ⇒ il `timestamp` che esce dal decodificatore E' "
           "l'`istante` del server" % (rv["med"], esc, pend, rv["n"]))
    else:
        ko("⛔ `voff` non regge: da %.0f a %.0f ms (escursione %.0f, deriva "
           "%+.2f ms/s).  ⇒ O il `VideoFrame.timestamp` non porta l'`istante` "
           "del server, o i due orologi non ticchettano uguale: **ogni numero "
           "qui sotto e' falso**" % (rv["min"], rv["max"], esc, pend))

    log("⭐ LA DISTANZA — `AV = aoff − voff`")
    avs = [c["av"] for c in camp if c["av"] is not None]
    aos = [c["aoff"] for c in camp if c["aoff"] is not None]
    if not avs:
        ko("⛔ `AV` e' sempre `null`: `aoff` non c'e' (contesto audio %s) ⇒ la "
           "meta' audio del metro non ha mai avuto un campione"
           % camp[-1]["ctx"])
        return 3
    ra, raoff = riassunto(avs), riassunto(aos)
    print("      %-8s %8s %8s %8s %8s %8s" % ("", "min", "p05", "mediana", "p95", "max"))
    for nome, r in (("AV", ra), ("aoff", raoff), ("voff", rv)):
        print("      %-8s %8.0f %8.0f %8.0f %8.0f %8.0f"
              % (nome, r["min"], r["p05"], r["med"], r["p95"], r["max"]))
    inf("uscita del dispositivo audio (`outputLatency`): %s ms" % camp[-1]["usc"])
    inf("⚠ e `AV` SOVRASTIMA il ritardo dell'audio dei `[?]` 16-40 ms fra "
        "`transferFromImageBitmap` e il pixel acceso: nessuna API li espone")

    # ⛔ Come si MUOVE nel tempo, che e' la domanda del coordinatore: una
    #    distanza che cresce e una che sta ferma sono due difetti diversi.
    n = len(avs)
    if n >= 6:
        terzi = [avs[:n // 3], avs[n // 3:2 * n // 3], avs[2 * n // 3:]]
        inf("nel tempo (mediana dei tre terzi): %s ms"
            % " → ".join("%.0f" % statistics.median(t) for t in terzi))
        deriva = statistics.median(terzi[2]) - statistics.median(terzi[0])
        inf("deriva dall'inizio alla fine: %+.0f ms su %.0f s" % (deriva, dt))

    log("Il contorno")
    u = camp[-1]
    inf("video: salt %d buchi %d ord %d mis %d tard %d err %d"
        % (u["salt"] - camp[0]["salt"], u["buchi"] - camp[0]["buchi"],
           u["ord"] - camp[0]["ord"], u["mis"] - camp[0]["mis"],
           u["tard"] - camp[0]["tard"], u["err"]))
    inf("audio: coda %s ms · riarmi %s · contesto %s"
        % (u["coda_ms"], u["audio_buchi"], u["ctx"]))
    inf("%scarico portatile %s→%s · prova %s→%s%s"
        % (GRIGIO, c0[0], c1[0], c0[1], c1[1], FINE))

    os.makedirs(a.fuori, exist_ok=True)
    f = os.path.join(a.fuori, "07-b63-distanza.json")
    json.dump({"quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "worker": a.worker, "secondi": a.secondi,
               "carico_portatile": [c0[0], c1[0]], "carico_prova": [c0[1], c1[1]],
               "av": ra, "aoff": raoff, "voff": rv,
               "campioni": camp, "registro": righe[-1500:]},
              open(f, "w"), indent=1, ensure_ascii=False)
    inf("esiti: %s" % f)
    return 1 if ROSSI[0] else 0


if __name__ == "__main__":
    sys.exit(main())
