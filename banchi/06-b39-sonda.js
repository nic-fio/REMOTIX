/*
 * 06-b39-sonda.js — LA MISURA SUI PIXEL della vista che non combacia.
 *
 * ⛔ NON MODIFICA `src/pagina.html`.  Il lanciatore ne fa una COPIA nella
 *    cartella di lavoro e le appende questo file: il prodotto e' di altri
 *    (sottofase 6.5) e in questa stessa ora ci stanno scrivendo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA MISURA, E PERCHE' NON BASTAVA LEGGERE IL CODICE
 *
 * `SPECIFICHE.md` §6.2 dice «si impagina, non si stira» e `RCP.md` §7.1 dice
 * che la vista non ha vincoli.  Sono due affermazioni sui PIXEL, e l'invariante
 * **I8** dice che il metro e' quel che l'utente vede.  ⇒ Qui non si ricopiano
 * le formule della pagina: si chiama il codice VERO — `schermo.vista()`,
 * `cl_geometria()`, `cl_su_mousemove()` — e si misura con
 * `getBoundingClientRect()`, cioe' il vetro.
 *
 * ⛔ Quel che si sostituisce, e si DICHIARA (`CODER.md` §4.2):
 *   · `cl_manda_puntatore` — vuole un canale WebTransport, e qui non c'e'
 *     rete.  ⚠ E' a VALLE della conversione: le due righe che convertono
 *     (4957-4958) girano per intero prima di lui.
 *   · `SCENA.movimento` — contatori di scena, a valle anch'essi.
 *   Niente altro.  In particolare `cl_geometria()` e `cornice()` sono QUELLE
 *   DELLA PAGINA, non copie.
 *
 * ⛔ E IL CONTROLLO POSITIVO (`LEZIONI.md` §1.9): il caso `strumento` verifica
 *    che una scala 1:1 dia davvero 1:1 — cioe' che questa sonda sappia
 *    misurare un caso in cui la risposta e' nota — PRIMA di dichiarare che una
 *    scala diversa sia giusta o sbagliata.
 */
(function () {
  "use strict";

  const R = { motore: navigator.userAgent, dpr: devicePixelRatio || 1,
              casi: [], errori: [] };

  function dice(nome, atteso, misurato, bene, extra) {
    R.casi.push({ nome: nome, atteso: atteso, misurato: misurato,
                  bene: !!bene, extra: extra || null });
  }

  /* ── Il palco finto: un fotogramma che non e' mai arrivato dalla rete ──
     ⚠ Si dipinge una scacchiera invece di lasciarlo vuoto: una tela vuota e una
       tela nera hanno lo stesso aspetto, e il difetto «non ho dipinto niente»
       resterebbe invisibile (`LEZIONI.md` §2.2). */
  function metti_fotogramma(tl, ta) {
    const dep = document.createElement("canvas");
    dep.width = tl; dep.height = ta;
    const p = dep.getContext("2d");
    for (let y = 0; y < ta; y += 64)
      for (let x = 0; x < tl; x += 64) {
        p.fillStyle = ((x / 64 + y / 64) % 2) ? "#fff" : "#333";
        p.fillRect(x, y, 64, 64);
      }
    schermo.deposito = dep;
    schermo.tela.width = tl; schermo.tela.height = ta;
    schermo.tela.getContext("2d").drawImage(dep, 0, 0);
    schermo.tela_l = tl; schermo.tela_a = ta;
    /* Quel che `componi()` lascia dietro di se' (riga 2039 della pagina): il
       buffer vale esattamente il fotogramma, bande zero. */
    schermo.dipinta = { l: tl, a: ta, x: 0, y: 0,
                        fotogramma: [tl, ta], scala: 1 };
    document.body.dataset.schermo = "acceso";
  }

  function scena(tl, ta, vl, va) {
    metti_fotogramma(tl, ta);
    schermo.vista_l = 0; schermo.vista_a = 0;   /* forza il ricalcolo */
    schermo.vista(vl, va);
    const r = schermo.tela.getBoundingClientRect();
    return r;
  }

  /* Un `mousemove` vero sul percorso vero. */
  function muovi(cx, cy) {
    cl_px = -1; cl_py = -1;
    const ev = new MouseEvent("mousemove", {
      clientX: cx, clientY: cy, bubbles: true, cancelable: true });
    cl_su_mousemove(ev);
    return [cl_px, cl_py];
  }

  const quasi = (a, b, t) => Math.abs(a - b) <= (t === undefined ? 1.5 : t);

  try {
    /* ── i ripieghi a valle, dichiarati ─────────────────────────────────── */
    window.cl_manda_puntatore = function () {};
    SCENA.movimento = function () {};
    /* ⛔ `cl_in_vigore` e' un `let` di modulo (riga 4874): NON e' una proprieta'
     *    di `window`, e scriverci sopra creerebbe un'altra variabile lasciando
     *    la guardia a `false` — un ripiego che tace, cioe' il difetto peggiore.
     *    ⇒ Si sostituisce la GUARDIA, che e' una `function` dichiarata e quindi
     *    sta davvero sull'oggetto globale. */
    window.cl_utilizzabile = function () { return true; };
    if (cl_utilizzabile() !== true)
      R.errori.push("⛔ la guardia `cl_utilizzabile` NON e' stata sostituita: "
                  + "i `mousemove` non entreranno, e i casi 0/3/4 direbbero "
                  + "«coordinate ferme» invece di «non ho misurato»");

    /* ================================================================== *
     * 0 — CONTROLLO POSITIVO DELLO STRUMENTO
     *
     * Atteso, dichiarato prima: con tela 800x600 e vista 800x600 (dpr 1) la
     * scala vale ESATTAMENTE 1, il rettangolo sul vetro misura 800x600 CSS, e
     * il centro del rettangolo si converte nel centro della tela (400,300).
     * ⇒ Se questo caso fallisce, nessuna misura sotto vale niente.
     * ================================================================== */
    {
      /* ⚠ La vista si da' in pixel FISICI, il rettangolo si misura in pixel
       *   CSS: con scala 1 il lato CSS vale `800 / dpr`, non 800.  Su Xvfb
       *   `dpr` vale 1 e i due numeri coincidono — ⛔ e proprio per questo il
       *   conto si scrive per intero: un banco che funziona solo dove il
       *   fattore e' 1 e' un banco che tace sul telefono. */
      const atteso_lato = 800 / R.dpr;
      const r = scena(800, 600, 800 * R.dpr, 600 * R.dpr);
      const c = muovi(r.left + r.width / 2, r.top + r.height / 2);
      const bene = quasi(r.width, atteso_lato, 2)
                 && quasi(c[0], 400, 2) && quasi(c[1], 300, 2);
      dice("0 controllo POSITIVO 1:1",
           "rettangolo " + atteso_lato + "x" + (600 / R.dpr)
           + " CSS e centro → tela 400,300",
           "rettangolo " + r.width.toFixed(1) + "x" + r.height.toFixed(1)
           + " CSS, centro → " + c[0].toFixed(1) + "," + c[1].toFixed(1),
           bene, { rect: [r.width, r.height], centro: c });
    }

    /* ================================================================== *
     * 1 — SI IMPAGINA, NON SI STIRA (`SPECIFICHE.md` §6.2)
     *
     * Scena: tela 1920x1080 (16:9), vista 800x800 (1:1) — proporzioni che NON
     * combaciano, che e' il caso di §6.2 e la forma di §6.5.
     * Atteso: il rapporto dei lati del rettangolo DIPINTO resta 1920/1080 =
     * 1,7778 (±1 %), non 1,0.  E il rettangolo ci sta dentro la vista.
     * ================================================================== */
    {
      const r = scena(1920, 1080, 800, 800);
      const rap = r.height ? r.width / r.height : 0;
      const dentro = r.width <= 800 / R.dpr + 1 && r.height <= 800 / R.dpr + 1;
      const bene = Math.abs(rap - 1920 / 1080) < 0.018 && dentro;
      dice("1 impagina, non stira (16:9 in 1:1)",
           "rapporto dei lati 1,778 (quello della TELA), e sta dentro la vista",
           "rapporto " + rap.toFixed(4) + ", rettangolo "
           + r.width.toFixed(1) + "x" + r.height.toFixed(1) + " CSS",
           bene, { rect: [r.width, r.height], rapporto: rap });
    }

    /* ================================================================== *
     * 2 — LE BANDE ESISTONO, E DA CHE PARTE STANNO
     *
     * Stessa scena del caso 1.  Atteso: la banda totale in verticale vale
     * 800/dpr − altezza del rettangolo, cioe' > 0.  ⚠ E si misura DOVE sta:
     * §6.2 non lo dice, ma un'impaginazione asimmetrica e' un fatto da
     * consegnare, non da scoprire dall'utente.
     * ================================================================== */
    {
      const r = schermo.tela.getBoundingClientRect();
      const pe = schermo.tela.parentElement;
      if (!pe) throw new Error("la tela non ha un genitore: non so dove siano le bande");
      const padre = pe.getBoundingClientRect();
      const sopra = r.top - padre.top;
      const sotto = (padre.top + padre.height) - (r.top + r.height);
      const sinistra = r.left - padre.left;
      const destra = (padre.left + padre.width) - (r.left + r.width);
      const bene = (sopra + sotto) > 0.5 || (sinistra + destra) > 0.5;
      dice("2 le bande ci sono",
           "banda > 0 su almeno un asse (proporzioni diverse ⇒ si impagina)",
           "sopra " + sopra.toFixed(1) + " sotto " + sotto.toFixed(1)
           + " sinistra " + sinistra.toFixed(1) + " destra " + destra.toFixed(1),
           bene, { sopra: sopra, sotto: sotto, sinistra: sinistra, destra: destra });
    }

    /* ================================================================== *
     * 3 — ⛔ LE COORDINATE ARRIVANO GIUSTE quando la tela e' PIU' GRANDE
     *      della vista.  E' il punto in cui una scala sbagliata si vede come
     *      «il clic finisce altrove» — due giorni pagati sul DeX.
     *
     * Scena: tela 1920x1080, vista 640x480 (piu' piccola E di proporzioni
     * diverse).  Si punta a un QUARTO e a TRE QUARTI del rettangolo dipinto.
     * Atteso: tela 480,270 e 1440,810 — con tolleranza di 2 pixel di tela.
     * ================================================================== */
    {
      const r = scena(1920, 1080, 640, 480);
      const q = muovi(r.left + r.width * 0.25, r.top + r.height * 0.25);
      const t = muovi(r.left + r.width * 0.75, r.top + r.height * 0.75);
      const bene = quasi(q[0], 480, 3) && quasi(q[1], 270, 3)
                && quasi(t[0], 1440, 3) && quasi(t[1], 810, 3);
      dice("3 coordinate con tela>vista",
           "un quarto → 480,270 e tre quarti → 1440,810 (coordinate di TELA)",
           "un quarto → " + q[0].toFixed(1) + "," + q[1].toFixed(1)
           + " · tre quarti → " + t[0].toFixed(1) + "," + t[1].toFixed(1),
           bene, { rect: [r.width, r.height], quarto: q, trequarti: t });
    }

    /* ================================================================== *
     * 4 — LA VISTA 300x801: DISPARI, e sotto il minimo della TELA.
     * ⛔ E' il caso concreto del rilievo R1.17.
     * Atteso: la pagina NON si rompe, il rettangolo conserva il rapporto della
     * tela, e il centro si converte nel centro della tela (960,540).
     * ================================================================== */
    {
      const r = scena(1920, 1080, 300, 801);
      const c = muovi(r.left + r.width / 2, r.top + r.height / 2);
      const rap = r.height ? r.width / r.height : 0;
      const bene = r.width > 0 && Math.abs(rap - 1920 / 1080) < 0.03
                && quasi(c[0], 960, 4) && quasi(c[1], 540, 4);
      dice("4 vista 300x801 (dispari, sotto 320x240)",
           "la pagina regge: rapporto 1,778 e centro → 960,540",
           "rettangolo " + r.width.toFixed(2) + "x" + r.height.toFixed(2)
           + " CSS (rapporto " + rap.toFixed(4) + "), centro → "
           + c[0].toFixed(1) + "," + c[1].toFixed(1),
           bene, { rect: [r.width, r.height], centro: c });
    }

    /* ================================================================== *
     * 5 — LA VISTA 1x1.  `RCP.md` §7.1: legale.
     * Atteso: nessuna eccezione, rettangolo > 0 in entrambi i lati (un
     * rettangolo di lato 0 renderebbe `vx` zero e la geometria degenere).
     * ⚠ Qui l'atteso onesto e' debole apposta: 1x1 e' un caso limite e quel
     *   che conta e' che la pagina lo DICHIARI invece di rompersi.
     * ================================================================== */
    {
      let rotto = null, r = null;
      try { r = scena(1920, 1080, 1, 1); }
      catch (e) { rotto = String(e); }
      const g = rotto ? null : cl_geometria();
      const bene = !rotto;
      dice("5 vista 1x1",
           "nessuna eccezione (§7.1: 1x1 e' legale)",
           rotto ? ("ECCEZIONE: " + rotto)
                 : ("rettangolo " + r.width.toFixed(4) + "x" + r.height.toFixed(4)
                    + " CSS, vx=" + (g ? g.vx.toExponential(3) : "?")
                    + " sx=" + (g ? g.sx : "?")),
           bene, { rect: r ? [r.width, r.height] : null,
                   vx: g ? g.vx : null, sx: g ? g.sx : null });
    }

    /* ================================================================== *
     * 6 — ⭐ LA VISTA PIU' GRANDE DELLA TELA: si ingrandisce o no?
     *
     * ⛔ Qui il codice e il suo stesso commento si contraddicono: riga 1898
     *    `Math.min(…, 1)` mette un tetto a 1:1; il commento a 2005-2009 dice
     *    che il fattore «non ha un tetto a 1» e che un `Math.min(1, …)`
     *    «sarebbe la stessa famiglia del difetto curato oggi».
     * ⇒ Non si decide leggendo: si misura.  Scena: tela 640x360, vista
     *   1280x720 (il doppio).  Atteso secondo il CODICE: rettangolo 640x360
     *   CSS (scala 1, tetto attivo).  Atteso secondo il COMMENTO: 1280x720.
     * ================================================================== */
    {
      const r = scena(640, 360, 1280 * R.dpr, 720 * R.dpr);
      const tetto = quasi(r.width, 640, 3);
      const riempie = quasi(r.width, 1280, 3);
      dice("6 vista > tela: tetto a 1:1?",
           "il codice (riga 1898) dice 640 CSS; il commento (2005-2009) dice 1280",
           "rettangolo " + r.width.toFixed(1) + "x" + r.height.toFixed(1)
           + " CSS ⇒ " + (tetto ? "TETTO ATTIVO (vince il codice)"
                        : riempie ? "NESSUN TETTO (vince il commento)"
                        : "nessuno dei due"),
           tetto || riempie, { rect: [r.width, r.height] });
    }

    /* ================================================================== *
     * 7 — ⛔ `image-rendering` a scala ≠ 1.
     * Atteso (riga 1927): `pixelated` SOLO quando la scala e' esattamente 1.
     * Con tela 1920x1080 in vista 640x480 la scala non e' 1 ⇒ atteso `auto`.
     * ⚠ Il foglio di stile (riga 221) mette `pixelated` incondizionato: se la
     *   riga in linea non gira, si misura `pixelated` — ed e' il difetto del
     *   DeX descritto a 1906-1912.
     * ================================================================== */
    {
      scena(1920, 1080, 640, 480);
      const inlinea = schermo.tela.style.imageRendering;
      const calcolato = getComputedStyle(schermo.tela).imageRendering;
      const bene = calcolato !== "pixelated";
      dice("7 image-rendering a scala != 1",
           "auto (riga 1927: pixelated solo a scala esattamente 1)",
           "in linea «" + inlinea + "», calcolato «" + calcolato + "»",
           bene, { inlinea: inlinea, calcolato: calcolato });
    }

    /* ================================================================== *
     * 8 — la misura della finestra che la pagina dichiarerebbe al server.
     * ⛔ Non e' un atteso da passare/fallire: e' il NUMERO, e serve a sapere
     *    se la vista che il server riceve e' pari, dispari, o arrotondata.
     * ================================================================== */
    {
      let mv = null, td = null, err = null;
      try { mv = misura_vista(); } catch (e) { err = String(e); }
      try { td = tela_da_chiedere(); } catch (e) { err = (err || "") + " " + e; }
      dice("8 vista e tela dichiarate al server",
           "la vista NON si arrotonda al pari; la tela si',  e sta fra 320x240 e 7680x4320",
           "vista " + (mv ? mv.join("x") : "?") + " · tela chiesta "
           + (td ? td.join("x") : "?") + (err ? (" ⛔ " + err) : ""),
           !!(mv && td), { vista: mv, tela: td,
                           vista_pari: mv ? [mv[0] % 2 === 0, mv[1] % 2 === 0] : null,
                           tela_pari: td ? [td[0] % 2 === 0, td[1] % 2 === 0] : null });
    }

  } catch (e) {
    R.errori.push(String(e && e.stack ? e.stack : e));
  }

  /* ⛔ Il risultato torna al lanciatore.  Se la POST fallisce si scrive anche
   *    nel titolo e nel corpo, cosi' un canale rotto non si legge come «zero
   *    casi» (`LEZIONI.md` §1.9). */
  R.fatti = R.casi.length;
  const testo = JSON.stringify(R);
  document.title = "b39:" + R.fatti + ":" + R.errori.length;
  try {
    const pre = document.createElement("pre");
    pre.id = "b39-esito";
    pre.textContent = testo;
    document.body.appendChild(pre);
  } catch (e) {}
  try {
    fetch("/esito", { method: "POST", body: testo });
  } catch (e) {
    try { navigator.sendBeacon("/esito", testo); } catch (e2) {}
  }
})();
