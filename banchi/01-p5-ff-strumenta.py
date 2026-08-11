#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01-p5-ff-strumenta.py — ⛔ FABBRICA UNA COPIA STRUMENTATA DI `src/pagina.html`.

    python3 banchi/01-p5-ff-strumenta.py src/pagina.html /dove/va/la/copia.html

⛔ IL PRODOTTO NON SI TOCCA.  Questo script LEGGE `src/pagina.html` e SCRIVE un
   file diverso: la copia si serve da un server tutto nostro (`--pagina`), sulla
   porta 7511, e la 7448 non la vede nemmeno.

===========================================================================
⛔ PERCHE' UNA COPIA STRUMENTATA, E NON IL REGISTRO DEL SERVER

Sul registro del server «la pagina non ha spedito niente» e «la pagina ha
spedito e il motore ha buttato via» arrivano IDENTICI: in tutt'e due i casi non
arriva niente.  ⭐ La sola cosa che li separa e' una traccia scritta DA DENTRO
la pagina, che sopravviva alla chiusura della scheda.

⭐ E il portatore e' `navigator.sendBeacon`: e' l'unico meccanismo del web
   disegnato APPOSTA per uscire da `pagehide`, e non passa da WebTransport —
   cioe' non condivide il destino di quel che stiamo misurando.  Ogni traccia e'
   un `POST /ff.<giro>.<etichetta>`, che `pagina.c` non riconosce e serve con un
   404 ⛔ ma prima LOGGA la riga (`pagina.c:217`).

⚠ E il portatore si controlla da se': la PRIMA traccia dentro `pagehide` e'
  `ph-01-entrato`.  Se quella arriva, il canale delle tracce funziona durante la
  chiusura, e il silenzio delle tracce successive e' un silenzio VERO.  Se non
  arriva nemmeno quella, ⛔ non si dice «la pagina non ha spedito»: si dice «non
  ho potuto guardare».

===========================================================================
⛔ LE QUATTRO VARIANTI, e si sceglie con il FRAMMENTO dell'indirizzo

Il frammento (`#...`) non arriva mai al server: cambia il comportamento della
copia senza cambiare il file, cosi' i quattro giri misurano LO STESSO byte per
byte e nessuna differenza puo' venire da una modifica fra un giro e l'altro.

    #fedele.<giro>   ⭐ il prodotto tale e quale, con le sole tracce aggiunte
    #vivo.<giro>     ⭐ IL CONTROLLO POSITIVO: cinque secondi dopo SESSIONE, a
                        scheda VIVA, si chiama lo STESSO `congeda()` con lo
                        STESSO motivo.  Se qui il congedo arriva e dentro
                        `pagehide` no, l'imputato e' quel che succede a
                        `pagehide` — non il codice di `congeda()`.
    #tenace.<giro>   dentro `pagehide` si chiama `congeda()` per una via che
                        NON puo' essere nulla (`congeda_ultimo`, che nessuno
                        azzera).  Separa «non e' stato chiamato» da «e' stato
                        chiamato e non e' uscito niente».
    #codice.<giro>   dentro `pagehide` SOLO la seconda strada di §3.1, senza
                        nessun `await` davanti: `wt.close({closeCode})` e basta.
                        Separa «l'attesa non si e' mai risolta» da «il motore
                        butta via anche il codice di chiusura».

===========================================================================
⛔⭐ L'ATTESO E' CAMBIATO LA SERA DELL'11 AGOSTO 2026, E SI SCRIVE PRIMA DEL GIRO

Il pomeriggio dell'11 agosto questi quattro giri hanno attribuito il difetto:
`fedele` non spediva niente, `tenace` e `vivo` spedivano tutt'e due le strade di
§3.1.  ⇒ l'imputato era la PAGINA, e Gecko scagionato per misura.

⭐ La cura e' nel prodotto dalla sera dell'11 (`src/pagina.html`): il `finally`
   non azzera piu' `congeda_corrente`, e ad azzerarlo e' `wt.closed`.  ⛔ Da cui
   l'atteso NUOVO, dichiarato qui prima di misurare:

    fedele  ⭐ deve comportarsi come `tenace`: `pagehide` scatta, la guardia e'
               PRESENTE, `congeda()` viene chiamata, e al server arriva il
               motivo `0x01` — su TUTT'E DUE i motori.
    tenace  invariato: era gia' la dimostrazione che la strada funziona.
    vivo    invariato: e' il controllo positivo, e non passa da `pagehide`.
    codice  invariato.
    eco     ⭐ `eco-congeda_corrente` passa da NULLA a PRESENTE — ed e' la
               traccia piu' bassa e piu' diretta della cura.

⛔ E il controllo che dice NO resta quello di sempre: se il gesto non arriva
   (`gesto_fatto` diverso da «fatto»), nessuna di queste righe accusa o assolve
   nessuno.  ⚠ Con `ctrl+w` sull'UNICA scheda Firefox ESCE, e in quella scena
   non esce niente per nessuna via: si usa il gesto `ctrl-w-due`.

===========================================================================
⛔ LE PATCH SONO ANCORATE A TESTO ESATTO, E SE UNA NON ATTACCA SI MUORE.

Una patch che non attacca in silenzio produrrebbe una copia che assomiglia al
prodotto ma non lo strumenta — e il suo silenzio avrebbe la faccia del silenzio
che cerchiamo.  Ogni sostituzione si conta, e se il conto non torna: uscita 2.
"""
import sys

PATCH = []


def p(nome, vecchio, nuovo, quante=1):
    PATCH.append((nome, vecchio, nuovo, quante))


# ---------------------------------------------------------------------------
# 1. Il tracciatore, le variabili di modulo e la variante.  Entra subito dopo
#    la riga che il prodotto usa per leggere lo stato del ban: e' il primo
#    punto in cui `document.body` esiste di sicuro.
p("tracciatore",
  'const BANNATO = document.body.dataset.bannato === "si";',
  '''const BANNATO = document.body.dataset.bannato === "si";

/* ══ STRUMENTAZIONE DEL BANCO — NON E' DEL PRODOTTO ══════════════════════ */
const FF_H = (location.hash || "#fedele.ignoto").slice(1).split(".");
const FF_VARIANTE = FF_H[0] || "fedele";
const FF_GIRO = FF_H[1] || "ignoto";
let ff_wt = null;            /* la sessione, raggiungibile da fuori da `collega` */
let congeda_ultimo = null;   /* ⭐ la stessa `congeda`, ma NESSUNO la azzera */
let ff_n = 0;
function traccia(etichetta) {
  ff_n++;
  const u = "/ff." + FF_GIRO + "." + FF_VARIANTE + "."
          + String(ff_n).padStart(2, "0") + "." + etichetta;
  let ok = false;
  try { ok = navigator.sendBeacon(u); } catch (e) { ok = false; }
  /* ⛔ E se il portatore dice NO lo si scrive, invece di lasciare un buco che
     somiglia a un silenzio del prodotto. */
  if (!ok) { try { navigator.sendBeacon("/ff." + FF_GIRO + ".beacon-rifiutato." + etichetta); } catch (e) {} }
  return ok;
}
/* ⛔⭐ IL SECONDO PORTATORE, E SERVE A UNA DOMANDA SOLA.
 *
 *     `sendBeacon` che non arriva ha DUE letture: «l'evento non e' scattato» e
 *     «l'evento e' scattato e il motore ha buttato via il messaggio».  Sono le
 *     stesse due che questo banco esiste per separare, un piano piu' sotto.
 *
 * ⭐ Una `XMLHttpRequest` SINCRONA non ha quel dubbio: non torna finche' il
 *    server non ha risposto, e se torna la richiesta e' arrivata.  ⛔ Ma BLOCCA:
 *    dentro `congeda()` regalerebbe alla `write` il tempo di risolversi, cioe'
 *    cambierebbe proprio la risposta che si cerca.  ⇒ Si usa SOLO nella
 *    variante `eco`, che non fa nient'altro che questo e poi torna. */
function traccia_sincrona(etichetta) {
  ff_n++;
  const u = "/ff." + FF_GIRO + "." + FF_VARIANTE + "."
          + String(ff_n).padStart(2, "0") + "." + etichetta;
  try { const x = new XMLHttpRequest(); x.open("GET", u, false); x.send(); return true; }
  catch (e) { return false; }
}
traccia("vita-caricata-variante-" + FF_VARIANTE);
/* ══ FINE STRUMENTAZIONE ═════════════════════════════════════════════════ */''')

# ---------------------------------------------------------------------------
# 2. Il gestore di `pagehide`.  ⛔ La riga del PRODOTTO resta identica dentro il
#    ramo `fedele`: quel che si misura non cambia.
p("pagehide",
  '''window.addEventListener("pagehide", function () {
  if (congeda_corrente)
    congeda_corrente(MOT.CHIUSO_DALL_UTENTE, "la scheda e' stata chiusa");
});''',
  '''window.addEventListener("pagehide", function () {
  if (FF_VARIANTE === "eco") {
    /* ⭐ LA DOMANDA PIU' BASSA DI TUTTE, e per via sincrona: `pagehide` scatta?
       E se scatta, che cosa ha in mano la guardia del prodotto in QUEL momento?
       ⛔ Non si spedisce niente su RCP: questa variante non misura il congedo,
          misura l'evento e la guardia. */
    traccia_sincrona("eco-pagehide-E-SCATTATO");
    traccia_sincrona("eco-congeda_corrente-" + (congeda_corrente ? "PRESENTE" : "NULLA"));
    traccia_sincrona("eco-congeda_ultimo-" + (congeda_ultimo ? "PRESENTE" : "NULLA"));
    traccia_sincrona("eco-visibilita-" + document.visibilityState);
    return;
  }
  traccia("ph-entrato");
  traccia("ph-congeda_corrente-" + (congeda_corrente ? "PRESENTE" : "NULLA"));
  traccia("ph-congeda_ultimo-" + (congeda_ultimo ? "PRESENTE" : "NULLA"));
  traccia("ph-wt-" + (ff_wt ? "PRESENTE" : "NULLA"));
  if (FF_VARIANTE === "tenace") {
    /* la via che non puo' essere nulla: separa «non chiamata» da «chiamata e muta» */
    if (congeda_ultimo) congeda_ultimo(MOT.CHIUSO_DALL_UTENTE, "la scheda e' stata chiusa");
    else traccia("ph-tenace-IMPOSSIBILE-congeda_ultimo-nullo");
    traccia("ph-uscito-tenace");
    return;
  }
  if (FF_VARIANTE === "codice") {
    /* SOLO la seconda strada di §3.1, e senza nessun `await` davanti */
    traccia("ph-codice-prima-di-wt-close");
    try { ff_wt.close({ closeCode: MOT.CHIUSO_DALL_UTENTE, reason: "la scheda e' stata chiusa" }); }
    catch (e) { traccia("ph-codice-eccezione"); }
    traccia("ph-codice-dopo-wt-close");
    return;
  }
  /* ⭐ IL PRODOTTO, RIGA PER RIGA — `src/pagina.html:331-334` */
  if (congeda_corrente)
    congeda_corrente(MOT.CHIUSO_DALL_UTENTE, "la scheda e' stata chiusa");
  traccia("ph-uscito-fedele");
});''')

# ---------------------------------------------------------------------------
# 3. `congeda_ultimo` e `ff_wt` si posano dove il prodotto posa `congeda_corrente`.
p("congeda_ultimo",
  '  congeda_corrente = congeda;',
  '''  congeda_corrente = congeda;
  congeda_ultimo = congeda;   /* strumentazione: nessuno lo azzera */''')

p("ff_wt",
  '  await wt.ready;\n  nota("sessione WebTransport aperta");',
  '''  ff_wt = wt;                 /* strumentazione */
  await wt.ready;
  nota("sessione WebTransport aperta");''')

# ---------------------------------------------------------------------------
# 4. Dentro `congeda()`: PRIMA e DOPO ogni tentativo di spedizione.  ⛔ E' il
#    punto della domanda: «ha spedito e il motore ha buttato» contro «non e'
#    mai arrivata a spedire».
p("congeda-inizio",
  '''  async function congeda(motivo, perche, muto) {
    if (congedato) return;
    congedato = true;''',
  '''  async function congeda(motivo, perche, muto) {
    traccia("cg-chiamata-motivo-0x" + motivo.toString(16) + (muto ? "-muto" : ""));
    if (congedato) { traccia("cg-USCITA-era-gia-congedato"); return; }
    congedato = true;''')

p("congeda-manda",
  '''    try {
      const s = new Scrittore().u8(motivo).str(perche);
      await canale.manda(TIPO.CONGEDO, s.byte());
      await canale.scrittore.close();
    } catch (e) {''',
  '''    try {
      const s = new Scrittore().u8(motivo).str(perche);
      traccia("cg-prima-di-manda");
      await canale.manda(TIPO.CONGEDO, s.byte());
      traccia("cg-dopo-manda-la-write-si-e-risolta");
      await canale.scrittore.close();
      traccia("cg-dopo-il-FIN-del-canale");
    } catch (e) {
      traccia("cg-eccezione-sul-canale");''')

p("congeda-close",
  '''    try {
      wt.close({ closeCode: motivo, reason: perche.slice(0, 100) });
    } catch (e) {
      nota("la sessione non si e' chiusa col codice: " + e);
    }
  }''',
  '''    try {
      traccia("cg-prima-di-wt-close");
      wt.close({ closeCode: motivo, reason: perche.slice(0, 100) });
      traccia("cg-dopo-wt-close");
    } catch (e) {
      traccia("cg-eccezione-su-wt-close");
      nota("la sessione non si e' chiusa col codice: " + e);
    }
  }''')

p("congeda-muto",
  '''    if (muto) { try { wt.close({ closeCode: motivo, reason: perche.slice(0, 100) }); }''',
  '''    if (muto) { traccia("cg-ramo-muto"); try { wt.close({ closeCode: motivo, reason: perche.slice(0, 100) }); }''')

# ---------------------------------------------------------------------------
# 5. ⭐ IL CONTROLLO POSITIVO A SCHEDA VIVA.  In fondo a `collega()`, cioe' nel
#    punto esatto in cui la stretta di mano e' finita bene.
p("controllo-vivo",
  '''    esito("Ammesso, sessione " + (stato === 1 ? "nuova" : "ripresa") +
          ", tela " + tl + "×" + ta + ", desktop " + desktop, true);
  }
}''',
  '''    esito("Ammesso, sessione " + (stato === 1 ? "nuova" : "ripresa") +
          ", tela " + tl + "×" + ta + ", desktop " + desktop, true);
  }
  traccia("sessione-stabilita");
  if (FF_VARIANTE === "vivo") {
    /* ⭐ IL CONTROLLO POSITIVO: lo STESSO `congeda()`, con lo STESSO motivo, in
       un momento che NON e' una chiusura.  La scheda resta viva e visibile. */
    setTimeout(function () {
      traccia("vivo-timer-scattato-scheda-viva");
      congeda_ultimo(MOT.CHIUSO_DALL_UTENTE, "la scheda e' stata chiusa");
    }, 5000);
  }
}''')

# ---------------------------------------------------------------------------
# 6. ⛔⭐ IL SOSPETTO PRINCIPALE, E LA SUA CURA — 11 agosto misurato, 12 curato.
#
#    Il `finally` del gestore di `submit` azzerava `congeda_corrente` appena
#    `collega()` ritornava, cioe' subito dopo SESSIONE: da li' in poi il gestore
#    di `pagehide` era codice morto.  ⭐ La cura ha TOLTO quella riga e ha
#    spostato l'azzeramento dentro `wt.closed`, che e' l'unico punto che sa
#    quando la sessione e' FINITA.
#
# ⛔ L'appiglio vecchio (`congeda_corrente = null;` dentro il `finally`) NON
#    ESISTE PIU', e questo file si sarebbe fermato con uscita 2 — che e' il
#    comportamento giusto: una patch che non attacca non deve produrre una copia
#    che assomiglia al prodotto senza strumentarlo.  Qui si prende il punto
#    nuovo, e la traccia diventa la PROVA DELLA CURA: alla fine del tentativo il
#    riferimento deve essere ANCORA PRESENTE.
p("finally",
  '  } finally {',
  '''  } finally {
    traccia("finally-congeda_corrente-" + (congeda_corrente ? "PRESENTE-cura-in-vigore"
                                                            : "NULLA-la-cura-non-c-e-piu"));''')

# ---------------------------------------------------------------------------
# 7. ⭐ E DOVE L'AZZERAMENTO E' ANDATO A FINIRE: `wt.closed`, cioe' la fine vera
#       della sessione.  ⛔ Serve a distinguere «il riferimento c'e' ancora»
#       (cura in vigore) da «il riferimento non viene mai lasciato andare»
#       (perdita: un tentativo nuovo si porterebbe dietro il vecchio).
p("fine-sessione",
  '  const fine_sessione = () => { if (congeda_corrente === congeda) congeda_corrente = null; };',
  '''  const fine_sessione = () => {
    traccia("fine-sessione-" + (congeda_corrente === congeda ? "lascio-il-mio-riferimento"
                                                             : "il-riferimento-non-e-piu-mio"));
    if (congeda_corrente === congeda) congeda_corrente = null;
  };''')


def main():
    if len(sys.argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    testo = open(sys.argv[1], encoding="utf-8").read()
    originale = testo
    for nome, vecchio, nuovo, quante in PATCH:
        trovate = testo.count(vecchio)
        if trovate != quante:
            sys.stderr.write(
                "NO  ⛔ la patch «%s» doveva attaccare %d volta/e e ne ha "
                "trovate %d.\n"
                "    ⛔ Una patch che non attacca produce una copia che "
                "ASSOMIGLIA al prodotto\n"
                "       e non lo strumenta: il suo silenzio avrebbe la faccia "
                "del silenzio in prova.\n" % (nome, quante, trovate))
            return 2
        testo = testo.replace(vecchio, nuovo)
        sys.stderr.write("OK  patch «%s» attaccata\n" % nome)
    if testo == originale:
        sys.stderr.write("NO  ⛔ la copia e' identica all'originale\n")
        return 2
    open(sys.argv[2], "w", encoding="utf-8").write(testo)
    sys.stderr.write("OK  copia strumentata: %s (%d byte, l'originale ne aveva %d)\n"
                     % (sys.argv[2], len(testo), len(originale)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
