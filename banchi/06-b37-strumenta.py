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
"""
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


def strumenta(dentro, fuori):
    with open(dentro, encoding="utf-8") as f:
        t = f.read()
    i = t.rfind("</body>")
    if i < 0:
        raise SystemExit("06-b37: nessun </body> in %s" % dentro)
    n = t[:i] + SONDA + t[i:]
    # ⛔ IL CONTROLLO: il prodotto deve stare INTATTO dentro la copia, nei due
    #    pezzi in cui la sonda lo taglia.  Senza, «ho misurato la pagina» e «ho
    #    misurato una pagina che le somiglia» hanno lo stesso aspetto.
    if t[:i] not in n or t[i:] not in n or len(n) != len(t) + len(SONDA):
        raise SystemExit("06-b37: la strumentazione ha cambiato il prodotto")
    with open(fuori, "w", encoding="utf-8") as f:
        f.write(n)
    print("06-b37: %s → %s (+%d byte di sonda, prodotto intatto)"
          % (dentro, fuori, len(SONDA)))


if __name__ == "__main__":
    strumenta(sys.argv[1], sys.argv[2])
