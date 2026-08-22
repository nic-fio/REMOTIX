#!/usr/bin/env python3
"""06-b37-strumenta.py — la copia strumentata di `src/pagina.html`.

    python3 banchi/06-b37-strumenta.py src/pagina.html /tmp/06-b37/pagina.html

⛔ CHE COSA AGGIUNGE, ESATTAMENTE — e non aggiunge altro:

  1. un `<script>` in fondo al corpo, DOPO quello del prodotto, con:
       · un annuncio al raccoglitore al caricamento e a ogni `resize`;
       · un ciclo che chiede comandi al raccoglitore, li passa a una `eval`
         DIRETTA e rimanda il valore.
  2. ⛔ NIENTE ALTRO.  Nessuna riga del prodotto viene tolta, cambiata o
     riordinata: la verifica sta in fondo a questo file (`differenza()`), che
     rifiuta di scrivere se il testo di partenza non e' contenuto intatto in
     quello di arrivo.

⚠ E la sonda NON tocca la geometria: non ha CSS, non aggiunge elementi al
  documento, non scrive su `body`.  Se lo facesse misurerebbe se stessa —
  ⛔ e in un banco che misura `clientWidth` un solo elemento in piu' sposta il
  numero (basta una barra di scorrimento: 15 px, `src/pagina.html:1397`).

═══════════════════════════════════════════════════════════════════════════
⛔⭐⭐ E UNA TERZA COSA, DAL 22 AGOSTO 2026: IL TESTO VERO DI `chiedi_tela`.

`fasi/06` §5.5, secondo falso verde: *«il ramo che attua la voce spenta non
viene mai eseguito»*.  `06-b37-voce.py` e `06-b37-modi.py` sostituivano
`chiedi_tela` con una spia **prima** di misurare, ⛔ e la guardia vera —
`if (tela_spenta) { … return; }` — sta **DENTRO la funzione sostituita**.
⇒ Quei banchi provavano che **un booleano cambia valore**, non che la pagina
smetta di chiedere.

⚠ E la funzione vera non si puo' semplicemente chiamare: e' una CHIUSURA creata
dentro `collega()` sopra il canale della stretta di mano, e senza server quella
stretta non avviene.

⇒ Qui si estrae dal prodotto **il testo esatto** dell'assegnazione
`chiedi_tela = function (perche) { … };` e lo si mette nella pagina come
stringa (`window.__b37_chiedi_tela_sorgente`).  Il banco lo passa a una `eval`
diretta con un **canale finto** nello scope: quel che viene installato non e'
un'imitazione, sono **gli stessi caratteri che gira il prodotto** — guardia
compresa.  ⛔ Se il testo cambia, cambia anche quel che il banco esercita; se
l'ancora non si trova piu', la strumentazione **fallisce rumorosamente** invece
di lasciare un banco verde che non prova niente.
"""
import json
import sys

SONDA = r"""
<script>
/* ══ 06-b37 · LA SONDA DELLA SOTTOFASE 6.5 — non e' prodotto ═══════════════
 * ⛔ Sta in fondo, dopo lo `<script>` del prodotto: cosi' `schermo`, `ADATTA` e
 *    `chiedi_tela` — che sono `const`/`let` di livello superiore, cioe' NON
 *    proprieta' di `window` — esistono gia' nel registro lessicale globale
 *    quando la `eval` diretta qui sotto li cerca per nome.                    */
(function () {
  const B = "/b37";
  let ultimo = 0;

  function posta(o) {
    o.giro = new URLSearchParams(location.search).get("giro") || "";
    try {
      fetch(B + "/esito", { method: "POST", body: JSON.stringify(o),
                            keepalive: true });
    } catch (e) { /* la pagina non deve morire per colpa della sonda */ }
  }

  /* ⚠ Lo stato si prende SEMPRE con le stesse chiamate del prodotto
   *   (`misura_vista`, `tela_da_chiedere`): una seconda formula che dica la
   *   stessa cosa e' la forma d'errore E2 — due autorita' sullo stesso numero. */
  function stato() {
    const d = document.documentElement;
    let v = null, t = null, err = null;
    try { v = misura_vista(); } catch (e) { err = "" + e; }
    try { t = tela_da_chiedere(); } catch (e) { err = (err || "") + "|" + e; }
    return {
      dpr: devicePixelRatio, cw: d.clientWidth, ch: d.clientHeight,
      iw: innerWidth, ih: innerHeight, ow: outerWidth, oh: outerHeight,
      sw: screen.width, sh: screen.height, vista: v, tela: t, errore: err,
      sx: scrollX, sy: scrollY,
      /* ⛔ la larghezza della barra di scorrimento in pixel CSS: e' la
       *    differenza fra le due misure che §6.1-bis nomina.                  */
      barra: innerWidth - d.clientWidth
    };
  }

  function sicuro(v) {
    try { JSON.parse(JSON.stringify(v)); return v; }
    catch (e) { return "" + v; }
  }

  posta(Object.assign({ tipo: "carico", ua: navigator.userAgent }, stato()));
  let f = 0;
  addEventListener("resize", function () {
    if (f) cancelAnimationFrame(f);
    f = requestAnimationFrame(function () {
      f = 0;
      posta(Object.assign({ tipo: "resize" }, stato()));
    });
  });

  (async function ciclo() {
    /* ⛔⭐ IL CURSORE PARTE DALLA FINE DELLA CODA, e non da zero — difetto del
     *    banco trovato il 16 agosto 2026 misurando `?adatta=segui`: dopo un
     *    `location.reload()` la pagina NUOVA ripescava TUTTI i comandi gia'
     *    eseguiti, **compreso il `reload()` stesso** ⇒ ciclo di ricaricamenti
     *    infinito, e le misure che seguivano descrivevano una pagina che
     *    ripartiva di continuo.  ⚠ Il primo esito uscito da quel ciclo era uno
     *    ZERO che sembrava un verde. */
    try {
      const s = await (await fetch(B + "/stato")).json();
      ultimo = s.comandi;
      posta({ tipo: "cursore", da: ultimo });
    } catch (e) { /* se il raccoglitore non risponde si riparte da 0 */ }
    for (;;) {
      try {
        const r = await fetch(B + "/comando?da=" + ultimo);
        const cs = await r.json();
        for (const c of cs) {
          if (c.n < ultimo) continue;
          ultimo = c.n + 1;
          let v, ok = true;
          try { v = eval(c.js); } catch (e) { ok = false; v = "" + e; }
          if (v && typeof v.then === "function") {
            try { v = await v; } catch (e) { ok = false; v = "" + e; }
          }
          await fetch(B + "/risposta", { method: "POST",
            body: JSON.stringify({ n: c.n, ok: ok, valore: sicuro(v) }) });
        }
      } catch (e) { /* il raccoglitore puo' morire prima della pagina */ }
      await new Promise(function (r) { setTimeout(r, 60); });
    }
  })();
})();
</script>
"""


ANCORA_INIZIO = "      chiedi_tela = function (perche) {"
ANCORA_FINE = "      };"


def estrai_chiedi_tela(testo):
    """⛔ Il testo ESATTO dell'assegnazione di `chiedi_tela` nel prodotto.
       Alza se l'ancora non c'e' o non e' unica: un'ancora scaduta e' la forma
       d'errore che `fasi/06` §5.2 ha gia' pagato una volta."""
    righe = testo.split("\n")
    inizi = [i for i, r in enumerate(righe) if r == ANCORA_INIZIO]
    if len(inizi) != 1:
        raise SystemExit(
            "06-b37: l'ancora «%s» compare %d volte invece di 1: la "
            "strumentazione NON procede (ancora scaduta o duplicata)"
            % (ANCORA_INIZIO.strip(), len(inizi)))
    i = inizi[0]
    fine = None
    for j in range(i + 1, len(righe)):
        if righe[j] == ANCORA_FINE:
            fine = j
            break
    if fine is None:
        raise SystemExit("06-b37: non trovo la fine di `chiedi_tela`")
    blocco = "\n".join(righe[i:fine + 1])
    for atteso in ("tela_spenta", "canale.manda(TIPO.ADATTA_TELA",
                   "tela_da_chiedere()"):
        if atteso not in blocco:
            raise SystemExit(
                "06-b37: il testo estratto di `chiedi_tela` non contiene «%s»: "
                "non e' la funzione che credo, e non la si usa" % atteso)
    return blocco


def strumenta(dentro, fuori):
    with open(dentro, encoding="utf-8") as f:
        t = f.read()
    i = t.rfind("</body>")
    if i < 0:
        raise SystemExit("06-b37: nessun </body> in %s" % dentro)
    sorgente_ct = estrai_chiedi_tela(t)
    ponte = ("\n<script>\n/* 06-b37: il TESTO VERO di `chiedi_tela`, estratto "
             "dal prodotto — non e' prodotto */\nwindow.__b37_chiedi_tela_"
             "sorgente = %s;\n</script>\n" % json.dumps(sorgente_ct))
    n = t[:i] + ponte + SONDA + t[i:]
    # ⛔ IL CONTROLLO: il prodotto deve stare INTATTO dentro la copia, nei due
    #    pezzi in cui la sonda lo taglia.  Senza, «ho misurato la pagina» e «ho
    #    misurato una pagina che le somiglia» hanno lo stesso aspetto.
    if (t[:i] not in n or t[i:] not in n
            or len(n) != len(t) + len(SONDA) + len(ponte)):
        raise SystemExit("06-b37: la strumentazione ha cambiato il prodotto")
    with open(fuori, "w", encoding="utf-8") as f:
        f.write(n)
    print("06-b37: %s → %s (+%d byte di sonda, +%d byte col testo vero di "
          "`chiedi_tela` (%d righe), prodotto intatto)"
          % (dentro, fuori, len(SONDA), len(ponte),
             sorgente_ct.count("\n") + 1))


if __name__ == "__main__":
    strumenta(sys.argv[1], sys.argv[2])
