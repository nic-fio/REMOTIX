#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c15 — ⭐⭐ «LA META' REMOTA GIRA DAVVERO» — la maglia che guarda LA RETE
===========================================================================

    python3 11-c15-la-meta-remota-gira.py
    python3 11-c15-la-meta-remota-gira.py --certifica
    python3 11-c15-la-meta-remota-gira.py --ultimi 40 --giorni 3

⛔ Come C11-C14, questa maglia **non prova il prodotto**.  Non prova nemmeno la
   rete: prova che la meta' della rete **che vale** stia ancora girando.

---------------------------------------------------------------------------
⛔⛔ IL GUASTO CHE PRENDE — *C12, spostata di una macchina*
---------------------------------------------------------------------------

Da `DECISIONI.md` §4.6-novemdecies il gancio ha **due meta' su due macchine**:
**decide** sul portatile (dove c'e' il deposito git) ed **esegue** sulla
macchina di prova (dove ci sono le scatole e la scheda grafica).

⇒ ⛔⛔ E da quel giorno c'e' un buco che nessuna delle quattro maglie della rete
  sa vedere: **se la macchina di prova fosse spenta per sempre, C12 e C13
  resterebbero VERDI.**

Ecco come, passo per passo, e non e' un'ipotesi — sono righe che stanno nel
registro di oggi:

  · il `pre-push` chiama `remoto`; la meta' remota non risponde e vale **3**
    («non ho potuto guardare»), e ⭐ **per scelta dichiarata non blocca l'invio**;
  · la meta' del portatile gira lo stesso: C10, C12, C13 e ⭐ il guasto innestato
    di C10, `[M]` un secondo in tutto;
  · **C12** guarda l'ultimo giro non a vuoto e lo trova di un minuto fa ⇒ verde:
    *«il gancio e' vivo»*.  ⚠ E dice il vero;
  · **C13** trova, in quel giro, un guasto innestato **visto** — quello di C10,
    che gira sul deposito e non ha bisogno di nessuna scatola ⇒ verde: *«la rete
    sa ancora dare rosso»*.  ⚠ E anche lei dice il vero.

⇒ ⛔⛔ **Tutt'e due dicono il vero, e insieme raccontano una bugia**: le maglie
  che guardano il prodotto — quelle che accendono una sessione dentro una
  scatola — ⛔ **potrebbero non girare da settimane, e nessuna riga rossa lo
  direbbe.**  ⚠ E' esattamente il guasto che C12 esiste per prendere — *«il
  gancio spento in silenzio»*, `fasi/11…` §4.2 — solo che il gancio non e'
  spento: e' **dimezzato**.

⭐ E §5.2 aveva gia' la regola giusta e nessuno che la facesse valere:

      *«il singolo 3 e' neutro; ⛔ un 3 FREQUENTE e' un guasto del banco, non
        un esito.»*

⇒ ⭐⭐ **C15 e' la maglia che trasforma «un 3 frequente» in una riga rossa.**
  Il 3 di oggi non blocca niente (e non deve: un gancio che ferma il lavoro
  perche' una seconda macchina non risponde e' un gancio che qualcuno
  disinstalla).  ⛔ Otto giorni di 3 di fila sono un'altra cosa, e da qui in poi
  hanno un colore.

---------------------------------------------------------------------------
⭐⭐ COME SI RICONOSCE UN GIRO «ESEGUITO SULLE SCATOLE» — ⛔ e non dal nome
    della macchina
---------------------------------------------------------------------------

La tentazione era leggere il campo `dove` (il `hostname`) e cercare quello della
macchina di prova.  ⛔ **Scartata**, e per due ragioni che sono la stessa:

  1. sarebbe un nome inchiodato dentro una maglia — il giorno che la macchina di
     prova cambia nome, o ne compare una seconda, C15 direbbe rosso per sempre:
     `LEZIONI.md` §1.49, *«un rosso che non si puo' far diventare verde e' peggio
     di nessuna maglia»*;
  2. ⛔ e soprattutto **non misurerebbe la cosa giusta**: che una riga sia stata
     scritta su quella macchina non dice che li' sia stato *misurato* qualcosa.

⇒ ⭐ Il segno si prende **dentro il giro**, ed e' una proprieta' che non si puo'
  fingere: **una maglia che ha bisogno di una scatola, e che e' arrivata a un
  GIUDIZIO** (esito 0 o 1, non 3).

⛔ E il «non 3» e' meta' del mestiere di questa maglia.  `[M]` dal registro di
   oggi: **C11 esce 0 dove ci sono le scatole (26 ago 2026, 11 s) e 3 dove non ci
   sono** (quattro giri sul portatile, 0-1 s).  ⇒ Un giudizio di C11 e' una prova
   che le scatole c'erano; un 3 di C11 e' la prova del contrario.

---------------------------------------------------------------------------
⛔ E «LA META' REMOTA E' VERDE» NON CONTA — la trappola piu' vicina
---------------------------------------------------------------------------

`11-gancio.sh` scrive in ogni giro `remoto` un'annotazione che si chiama **«la
meta remota»**, con esito 0 quando la delega ha funzionato.  ⚠ Sembra fatta
apposta per questa maglia, ⛔ **e non lo e'**:

`[M]` riga del registro del 27 agosto 2026, 07:30 — `"secco": true`, e dentro
`{"nome":"la meta remota","esito":0,…,"nota":"la meta' remota e' verde"}`.
⇒ ⛔ **Un giro a VUOTO in cui la delega e' andata a buon fine e non e' stato
  misurato niente.**  Quell'annotazione dice che l'ssh e systemd hanno
  funzionato, non che una scatola si sia accesa.

⇒ ⭐ C15 la **ignora del tutto**, e quel caso e' dentro `--certifica`.

---------------------------------------------------------------------------
⭐ LE TRE DOMANDE — e solo due giudicano
---------------------------------------------------------------------------

  1 ⭐ **Nella finestra c'e' almeno un giro eseguito sulle scatole?**
      ⇒ altrimenti ROSSO.  E' la domanda per cui questa maglia esiste.

  2 ⭐ **Quel giro ha acceso il prodotto dentro una scatola, o si e' fermato a
      quelle a costo zero?**
      ⇒ altrimenti ROSSO.  ⚠ Le scatole possono rispondere a `dpkg` (C11) ed
        essere l'ombra di se stesse: se nessuno ci accende dentro una sessione,
        la scheda grafica — ⛔ la ragione per cui si usano scatole e non
        macchine virtuali (D1) — non e' stata toccata da nessuno.

  3 ⚠ **Quante scatole hanno risposto?**  ⛔ **Si STAMPA, non si giudica**, e la
      ragione va scritta o qualcuno lo trasformera' in un rosso: la famiglia
      veloce guarda **la sola GNOME per scelta dichiarata** (`11-gancio.sh`,
      `for d in gnome`), e il prodotto oggi sa accendere **un desktop solo**
      (§7-bis, KDE e' la fase 12).  ⇒ Pretendere quattro scatole vorrebbe dire
      un rosso perpetuo per una decisione presa apposta: `LEZIONI.md` §1.49.
      ⭐ Il conto e' informazione, e diventera' un giudizio quando il prodotto
      sapra' accendere piu' di un desktop — non prima.

---------------------------------------------------------------------------
⚠⚠ IL METRO, e **da dove viene** — ⛔ nessuno dei due numeri e' mio
---------------------------------------------------------------------------

    finestra   `[R]` **ultimi 20 giri veri** — presa da C13 (`ULTIMI_PREDEFINITI`)
    soglia     `[R]` **7 giorni**            — presa da C12 (`GIORNI_PREDEFINITI`)

⭐ **Non le ho scelte diverse di proposito, e le due ragioni sono diverse.**

  · La **finestra** e' quella di C13 perche' C13 e C15 leggono **la stessa
    memoria** e devono guardare **la stessa fetta**.  ⛔ Due finestre diverse
    vorrebbero dire due maglie che parlano di due «adesso» diversi, e nessuno
    che legge saprebbe quale delle due sta guardando il presente.
  · La **soglia** e' quella di C12 perche' ⭐ **il guasto e' lo stesso, spostato
    di una macchina**.  ⛔ Due soglie diverse per lo stesso guasto vorrebbero
    dire che almeno una delle due e' arbitraria.

⛔⛔ **E all'origine tutt'e due sono `[?]`, e va detto invece che ereditato in
    silenzio.**  C12 lo scrive di se': *«scelta, non misurata: nessuno ha ancora
    osservato ogni quanto questo deposito viene toccato»*.  ⇒ Ereditando i
    numeri eredito anche il punto interrogativo.

⇒ ⭐ **La misura che servirebbe, e che oggi NON c'e'**: ogni quanto la macchina
  di prova viene fatta girare davvero.  `[M]` il registro di oggi ha **24
  righe** e **un solo** giro eseguito sulle scatole (26 agosto 2026, 21:12 UTC).
  ⛔ **Un campione di uno non e' un tasso**, e un numero tondo tirato fuori da li'
  sarebbe un `[?]` travestito da `[M]`.  ⇒ La soglia resta `[?]` finche' nel
  registro non ci saranno abbastanza giri sulle scatole per contare **ogni quanto
  arrivano**; quel giorno si sostituisce, e questa riga dice a chi lo fara' che
  cosa deve contare.

⭐ E la finestra a conti ha una proprieta' che vale la pena di scrivere: **piu'
  si spinge, prima grida.**  Ogni invio col portatile solo consuma un posto dei
  venti; venti invii senza le scatole e C15 e' rossa, che siano un giorno o un
  mese.  ⛔ Ma da sola non basta — se nessuno spinge piu', la finestra non
  avanza e C15 resterebbe verde in eterno: ⇒ **e' per questo che le domande sono
  due, a conti E a giorni**, e non e' una cintura con le bretelle.

---------------------------------------------------------------------------
⛔ DOVE QUESTA MAGLIA HA SENSO — e dove esce **2** invece di mentire
---------------------------------------------------------------------------

C15 legge **la memoria unita**, e la memoria unita sta **sul portatile**
(`11-registro-unisci.py`, e li' c'e' scritto perche').

⛔⛔ Sulla macchina di prova il registro contiene **solo i giri di quella
    macchina** — cioe' **tutti** giri eseguiti sulle scatole.  ⇒ Li' C15 sarebbe
    verde qualunque cosa succeda: **un predicato che non puo' fallire**,
    `LEZIONI.md` §1.44, e per giunta dentro la maglia che serve a non farlo.

⇒ ⭐ Percio' C15 chiede la stessa cosa che chiede C12: **c'e' un deposito git?**
  Se non c'e', esce **2** — *«il terreno non regge»* — invece di dare un verde
  che non ha guardato niente.  ⚠ E' la stessa risposta che da' C12 sulla
  macchina di prova, e §7-bis.16 scrive che **e' la risposta giusta**.

---------------------------------------------------------------------------
⛔ QUEL CHE C15 **NON** GUARDA — o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · ⛔ **Non dice che il gancio sia partito da solo.**  Un giro lanciato a mano
    sulla macchina di prova conta esattamente come uno partito dal `pre-push`.
    ⚠ Ed e' giusto: le scatole hanno girato.  ⭐ Che a farle partire sia un
    gancio installato lo dice **C12**, ed e' bene che lo dica una maglia sola.
  · ⛔ **Non dice che le maglie abbiano dato verde.**  Una C1 rossa e' un giro
    eseguito sulle scatole tanto quanto una verde — anzi, e' la prova migliore
    che la scatola c'era.  ⭐ Il colore delle maglie e' affare loro.
  · ⛔ **Non dice che il TRASPORTO funzioni.**  Se la macchina di prova gira e
    `unisci_registri` non riporta le righe, per C15 e' identico a una macchina
    spenta.  ⚠ Non e' un difetto: e' la definizione — *un giro di cui la memoria
    comune non sa niente non e' un giro, per chiunque legga quella memoria.*
    ⭐ Il gancio quel caso lo grida gia' da se' (*«il giro di la' e' successo
    davvero, ma qui non se ne saprebbe niente»*).
  · ⛔ **Non dice che le scatole stiano sull'ALTRA macchina.**  C15 chiede che
    una maglia che vuole una scatola abbia giudicato; ⚠ se un giorno le scatole
    girassero sul portatile, C15 sarebbe verde — ⭐ e avrebbe ragione: le
    scatole avrebbero girato.  ⛔ Quel che si perderebbe e' la *seconda
    macchina*, e a quel punto e' il disegno del gancio a essere cambiato, non
    questa maglia a sbagliare.
  · ⛔ **Non guarda quali scatole.**  Vedi la domanda 3: il conto si stampa.
  · ⛔ **Non sa se le scatole erano quelle giuste** (allineate, ricostruite di
    nascosto): quella e' **C11**.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ nella finestra le scatole hanno girato, di recente, e col carico vero
  1  ⛔ una delle due domande che giudicano non regge ⇒ rosso
  3  ⛔ non ho potuto guardare — il registro non si lascia leggere, oppure non
     c'e' nessun giro vero da esaminare.  ⛔ E NON e' un rosso: che il gancio
     non giri **affatto** lo dice C12, e due maglie che danno rosso per lo
     stesso fatto fanno sembrare grave il doppio quel che e' successo una volta
  2  il terreno non regge (⛔ non e' la macchina della memoria unita), o l'uso
     e' sbagliato
===========================================================================
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
REGISTRO = os.path.join(QUI, "11-gancio-registro.jsonl")

# ⛔ I due numeri NON sono miei: vengono da C12 e da C13, e sopra c'e' scritto
#    perche' sono gli stessi e non due nuovi.  ⚠ All'origine sono `[?]`.
ULTIMI_PREDEFINITI = 20   # `[R]` C13, `ULTIMI_PREDEFINITI`
GIORNI_PREDEFINITI = 7    # `[R]` C12, `GIORNI_PREDEFINITI`

# ---------------------------------------------------------------------------
# ⭐⭐ LE DUE LISTE, e la differenza fra loro e' tutta la seconda domanda.
#
# ⛔ Stanno QUI, dichiarate, invece di essere indovinate da una regola: una
#    maglia nuova che vuole la scatola e non entra in questa lista non fa
#    diventare C15 rossa — la fa diventare **cieca**, ed e' peggio.  ⚠ Chi
#    aggiunge una maglia alla rete aggiunge una riga qui, e il commento accanto
#    dice come si decide in quale delle due va.
# ---------------------------------------------------------------------------

# ⭐ «Senza una scatola accesa non puo' arrivare a un giudizio.»
#    ⇒ Un loro 0 o 1 nel registro **e' la prova che le scatole c'erano.**
VOGLIONO_LA_SCATOLA = {
    "passo0",  # `[R]` valida l'AMBIENTE dentro la scatola (11-accendi.sh passo0)
    "c1",      # `[R]` la sessione nasce e si vede
    "c5",      # `[R]` il suono non e' silenzio
    "c7",      # `[R]` si chiude e non resta niente
    "c8",      # `[R]` il secondo inquilino apre il browser
    "c9",      # `[R]` il registro dice DI CHI parla
    "c11",     # `[R]` interroga le quattro scatole con dpkg — `[M]` 0 dove ci
               #       sono, 3 dove non ci sono (registro 26-27 ago 2026)
    "c14",     # `[R]` accende le quattro scatole INSIEME
}

# ⭐ «Accende il prodotto, o un browser, DENTRO la scatola.»
#    ⇒ Sono le sole che toccano la scheda grafica e la sessione, cioe' la
#      ragione per cui la macchina di prova esiste (D1).
# ⛔ `passo0` e `c11` restano fuori apposta: la prima guarda l'ambiente, la
#    seconda interroga il gestore dei pacchetti.  ⚠ Sono giudizi veri e valgono
#    per la domanda 1, ⛔ ma una rete che fa solo quelle ha smesso di misurare
#    il prodotto senza smettere di dire verde.
ACCENDONO_UNA_SESSIONE = {"c1", "c5", "c7", "c8", "c9", "c14"}

# ⛔ E questa NON e' una maglia: e' l'annotazione della delega.  Vale 0 anche in
#    un giro a vuoto — `[M]` registro del 27 ago 2026, 07:30.  ⇒ Non conta.
NON_E_UNA_MAGLIA = {"la meta remota"}


def numero_di(nome):
    """Da «C1(gnome)x2» a «c1», da «passo0(kde)» a «passo0».

    ⛔ Torna `None` quando non riconosce una maglia — e `None` non e' «no»: e'
       «non e' una delle maglie che conosco», che per le due liste vale uguale.
    """
    if not isinstance(nome, str):
        return None
    s = nome.strip().lower()
    if s in NON_E_UNA_MAGLIA:
        return None
    if s.startswith("passo0"):
        return "passo0"
    # ⚠ `\d+` e' avido apposta: «c10» dev'essere «c10» e non «c1».
    m = re.match(r"^(c\d+)", s)
    return m.group(1) if m else None


def scatola_di(nome):
    """Il nome della scatola scritto fra parentesi, o `None`.

    ⛔ E NON si filtra su un elenco di desktop noti: il giorno che entra un
       desktop nuovo — il caso che `11-gancio.sh` sa riconoscere da solo — un
       filtro lo renderebbe invisibile proprio qui.  ⚠ Il prezzo e' che una
       parentesi messa per altro finirebbe nel conto; ⭐ e siccome il conto **non
       giudica**, il prezzo e' una riga stampata storta, non un rosso falso.
    """
    if not isinstance(nome, str):
        return None
    m = re.search(r"\(([^)]+)\)", nome)
    return m.group(1).strip().lower() if m else None


def leggi_il_registro(percorso):
    """Torna (giri, guaio) — ⛔ e i casi sono tre, come in C12 e C13.

       (None, "assente")     il file non c'e'
       (None, "illeggibile") c'e' e non si apre, o e' tutto storto
       ([...], None)         i giri, in ordine di scrittura
    """
    if not os.path.exists(percorso):
        return None, "assente"
    try:
        with open(percorso, "r", errors="replace") as f:
            righe = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    giri, storte = [], 0
    for r in righe:
        r = r.strip()
        if not r:
            continue
        try:
            o = json.loads(r)
        except ValueError:
            storte += 1
            continue
        if not isinstance(o, dict):
            storte += 1
            continue
        giri.append(o)
    if not giri and storte:
        return None, "illeggibile"
    return giri, None


def eta_in_giorni(istante, adesso):
    """⛔ Torna `None` se non sa dirlo — mai zero, mai un numero inventato."""
    if not istante or adesso is None:
        return None
    try:
        import datetime
        t = datetime.datetime.fromisoformat(istante)
        if t.tzinfo is None:
            t = t.astimezone()
        return (adesso - t.timestamp()) / 86400.0
    except (ValueError, TypeError, OverflowError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
def giudica(giri, ultimi, giorni, adesso):
    """⭐ Il giudizio, separato dai file — cosi' si puo' certificare.

    ⛔ Torna `None` per «non ho potuto guardare» (registro illeggibile, o
       nessun giro vero da esaminare), altrimenti un dizionario con dentro
       `guai`: una LISTA, magari vuota.

    ⚠ `None` non e' la lista vuota.  «Non ho guardato» e «ho guardato e regge»
      sono due cose diverse, e questo progetto ha gia' pagato per averle
      confuse.
    """
    if giri is None:
        return None
    # ⛔ I giri a vuoto si buttano PRIMA di prendere gli ultimi N — la stessa
    #    regola di C13, e per la stessa ragione: venti `--secco` di fila
    #    spingerebbero fuori dalla finestra l'ultimo giro vero sulle scatole, e
    #    la maglia diventerebbe rossa per niente.
    veri = [g for g in giri if not g.get("secco")]
    if not veri:
        return None
    fetta = veri[-ultimi:]

    sulle_scatole = []      # i giri in cui una maglia della scatola HA GIUDICATO
    col_carico = []         # ... e fra quelli, quelli che hanno acceso qualcosa
    scatole_viste = set()   # ⚠ informazione, non giudizio (domanda 3)
    macchine = set()

    for g in fetta:
        d = g.get("dove")
        if d:
            macchine.add(d)
        giudicanti, accese = [], []
        for m in g.get("maglie") or []:
            # ⛔⛔ E QUI STA IL CUORE: **un 3 non e' un giudizio.**
            #    Una maglia che voleva la scatola e non l'ha trovata scrive 3,
            #    ed e' esattamente il sintomo della macchina di prova spenta.
            #    ⚠ Anche il -1 dei giri a vuoto cade qui, e non e' un doppione:
            #      e' una seconda rete sotto la prima.
            if m.get("esito") not in (0, 1):
                continue
            n = numero_di(m.get("nome"))
            if n is None or n not in VOGLIONO_LA_SCATOLA:
                continue
            giudicanti.append(m.get("nome"))
            s = scatola_di(m.get("nome"))
            if s:
                scatole_viste.add(s)
            if n in ACCENDONO_UNA_SESSIONE:
                accese.append(m.get("nome"))
        if giudicanti:
            sulle_scatole.append((g, giudicanti))
        if accese:
            col_carico.append((g, accese))

    r = {
        "esaminati": len(fetta),
        "totali": len(veri),
        "a_vuoto": len(giri) - len(veri),
        "sulle_scatole": len(sulle_scatole),
        "col_carico": len(col_carico),
        "scatole": sorted(scatole_viste),
        "macchine": sorted(macchine),
        "ultimo": sulle_scatole[-1][0] if sulle_scatole else None,
        "ultimo_maglie": sulle_scatole[-1][1] if sulle_scatole else [],
        "ultimo_carico": col_carico[-1][0] if col_carico else None,
        "eta": None,
        "guai": [],
    }

    # ── DOMANDA 1 ──────────────────────────────────────────────────────────
    if not sulle_scatole:
        # ⛔ E si torna SUBITO.  Senza un giro sulle scatole, «non ha acceso
        #    niente» e' una conseguenza, non un secondo guasto: un elenco che
        #    conta due volte lo stesso fatto fa sembrare grave quel che e'
        #    semplice (la stessa regola di C12).
        r["guai"].append(
            "negli ultimi %d giri veri ⛔ NESSUNO e' stato eseguito sulle "
            "scatole: nessuna maglia che ha bisogno di una scatola e' arrivata "
            "a un giudizio" % len(fetta))
        return r

    # ── e l'eta' dell'ultimo ───────────────────────────────────────────────
    eta = eta_in_giorni(r["ultimo"].get("istante"), adesso)
    r["eta"] = eta
    if eta is None:
        # ⚠ Un istante che non si lascia leggere non e' «vecchio»: e' «non lo
        #   so».  ⛔ E si dice come guasto del REGISTRO, non come macchina
        #   spenta — non e' la stessa cosa, e si curano in posti diversi.
        r["guai"].append(
            "l'ultimo giro sulle scatole non porta un istante leggibile (%r): "
            "il registro e' storto" % (r["ultimo"].get("istante"),))
    elif eta > giorni:
        r["guai"].append(
            "l'ultimo giro sulle scatole e' di %.1f giorni fa, e la soglia "
            "dichiarata e' %d" % (eta, giorni))

    # ── DOMANDA 2 ──────────────────────────────────────────────────────────
    if not col_carico:
        r["guai"].append(
            "nella finestra le scatole hanno risposto, ⛔ ma NESSUNO ci ha "
            "acceso dentro il prodotto: solo le maglie a costo zero "
            "(l'ambiente, i pacchetti). La scheda grafica non l'ha toccata "
            "nessuno")
    return r


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ Si dimostra che il giudice SA dare verde, SA dare rosso, e SA dire
       «non lo so» — e che ciascuna delle due domande si accende **nei due
       versi** (`LEZIONI.md` §1.49: si toglie il guasto e si pretende il verde).
    """
    import datetime
    adesso = time.time()

    def istante(giorni_fa):
        t = datetime.datetime.now().astimezone() - datetime.timedelta(days=giorni_fa)
        return t.isoformat()

    def giro(maglie, secco=False, giorni_fa=0.5, dove="NIC-OS"):
        return {"istante": istante(giorni_fa), "secco": secco,
                "dove": dove, "maglie": maglie}

    def m(nome, esito=0):
        return {"nome": nome, "esito": esito, "secondi": 1,
                "guasto_innestato": False}

    # ⭐ il giro «del solo portatile»: e' la riga esatta che il registro scrive
    #   oggi quando la macchina di prova non risponde.
    def portatile(giorni_fa=0.5):
        return giro([m("C10"), m("C11", esito=3), m("C12"), m("C13"),
                     m("C14", esito=3),
                     {"nome": "C10 guasto innestato", "esito": 0, "secondi": 0,
                      "guasto_innestato": True, "ha_visto_il_guasto": True}],
                    giorni_fa=giorni_fa, dove="CHUWI")

    casi = [
        # ── il verde, e da dove viene ───────────────────────────────────────
        ("⭐ un giro con C1(gnome) giudicata e recente",
         [giro([m("C10", esito=3), m("C11"), m("C1(gnome)x2", esito=1)])],
         "verde"),

        ("⭐ una C1 ROSSA e' un giro sulle scatole quanto una verde",
         [giro([m("C1(kde)x10", esito=1)])], "verde"),

        # ── ⭐⭐ IL BUCO PER CUI QUESTA MAGLIA ESISTE ───────────────────────
        ("⛔⛔ venti giri del SOLO PORTATILE — C12 e C13 sarebbero verdi",
         [portatile() for _ in range(20)], "ROSSO"),

        ("⛔⛔ «la meta remota e' verde» in un giro NON a vuoto non conta",
         [giro([{"nome": "la meta remota", "esito": 0, "secondi": 1,
                 "guasto_innestato": False, "nota": "la meta' remota e' verde"},
                m("C10")])], "ROSSO"),

        ("⛔ le maglie delle scatole ci sono, ma sono TUTTE esito 3",
         [giro([m("passo0(gnome)", esito=3), m("C1(gnome)x2", esito=3),
                m("C11", esito=3), m("C14", esito=3)])], "ROSSO"),

        ("⛔ le maglie ci sono con esito -1 (a vuoto dentro un giro vero)",
         [giro([m("C1(gnome)x2", esito=-1), m("C11", esito=-1)])], "ROSSO"),

        # ── DOMANDA 2, nei due versi ────────────────────────────────────────
        ("⛔ le scatole rispondono (C11) ma nessuno ci accende niente",
         [giro([m("C11"), m("C12"), m("C13")])], "ROSSO"),

        ("⛔ nemmeno il passo 0 basta: guarda l'ambiente, non accende",
         [giro([m("passo0(kde)"), m("C11")])], "ROSSO"),

        # ⭐⭐ E QUESTO E' IL CASO CHE IMPEDISCE A C15 DI CERTIFICARE SE STESSA.
        #    ⛔ Una maglia che si conta fra le prove che «le scatole hanno
        #       girato» sarebbe verde ogni volta che gira, cioe' sempre:
        #       `LEZIONI.md` §1.44 dentro la maglia scritta per non farlo.
        ("⛔⛔ venti giri di sole C15 verdi: ⭐ non certifica se stessa",
         [giro([m("C15"), m("C12"), m("C13")]) for _ in range(20)], "ROSSO"),

        ("⭐ C14 invece ACCENDE le quattro scatole ⇒ verde",
         [giro([m("C11"), m("C14")])], "verde"),

        ("⭐ passo0 + C5 ⇒ verde: una che accende basta",
         [giro([m("passo0(xfce)"), m("C5(xfce)")])], "verde"),

        # ── LA SOGLIA A GIORNI, nei due versi ───────────────────────────────
        ("⛔ l'ultimo giro sulle scatole e' di venti giorni fa (soglia 7)",
         [giro([m("C1(gnome)x2")], giorni_fa=20)], "ROSSO"),

        ("⭐ … e a 6,5 giorni e' ancora VERDE (il verso che si dimentica)",
         [giro([m("C1(gnome)x2")], giorni_fa=6.5)], "verde"),

        ("⚠ l'istante non si lascia leggere ⇒ e' il registro a essere storto",
         [{"istante": "ieri mattina", "secco": False,
           "maglie": [m("C1(gnome)x2")]}], "ROSSO"),

        # ── LA FINESTRA A CONTI, nei due versi ──────────────────────────────
        ("⭐ diciannove giri del portatile DOPO uno sulle scatole ⇒ verde",
         [giro([m("C1(gnome)x2")])] + [portatile() for _ in range(19)],
         "verde"),

        ("⛔⛔ ventuno, e il giro sulle scatole SCIVOLA FUORI dalla finestra",
         [giro([m("C1(gnome)x2")])] + [portatile() for _ in range(21)],
         "ROSSO"),

        ("⭐ venti giri A VUOTO non spingono fuori il giro sulle scatole",
         [giro([m("C1(gnome)x2")])]
         + [giro([m("C1(gnome)x2")], secco=True) for _ in range(20)], "verde"),

        # ── «NON LO SO», che non e' un rosso ────────────────────────────────
        ("⛔ nessun giro vero ⇒ «non lo so» — che il gancio non giri lo dice C12",
         [giro([m("C1(gnome)x2")], secco=True)], "non lo so"),

        ("⛔ nessun giro affatto ⇒ «non lo so»", [], "non lo so"),

        ("⛔ registro illeggibile ⇒ «non lo so», non rosso", None, "non lo so"),
    ]

    print("== certificazione del giudice di C15 ==")
    print("   metro in vigore: ultimi %d giri VERI `[R]` da C13  ·  ultimo giro"
          % ULTIMI_PREDEFINITI)
    print("   sulle scatole entro %d giorni `[R]` da C12  ·  ⛔ all'origine `[?]`"
          % GIORNI_PREDEFINITI)
    print("   ⛔ e un giro «sulle scatole» e' un giro in cui una maglia che vuole")
    print("      una scatola e' arrivata a un GIUDIZIO (0 o 1), non a un 3\n")

    guai = 0
    for nome, giri, atteso in casi:
        r = giudica(giri, ULTIMI_PREDEFINITI, GIORNI_PREDEFINITI, adesso)
        if r is None:
            ottenuto = "non lo so"
        elif r["guai"]:
            ottenuto = "ROSSO"
        else:
            ottenuto = "verde"
        ok = ottenuto == atteso
        print("  %s  %-63s ⇒ %-9s (atteso %s)"
              % ("OK " if ok else "NO ", nome, ottenuto, atteso))
        if not ok:
            guai += 1
            print("        (il giudice ha detto: %r)" % (r,))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ E IL CASO CHE DICHIARA UN **NON**-GIUDIZIO: il conto delle scatole.
    #
    # ⛔ Serve perche' e' la cosa piu' facile da trasformare in un rosso
    #    perpetuo: «hanno risposto in una su quattro» sembra un guasto, e non
    #    lo e' — la famiglia veloce guarda la sola GNOME per scelta dichiarata.
    # ⇒ Qui si PRETENDE che una scatola sola resti VERDE, e che il conto sia
    #   comunque scritto.  Il giorno che qualcuno lo trasformasse in un
    #   giudizio, questa riga diventerebbe rossa e glielo direbbe.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    una = giudica([giro([m("C1(gnome)x2")])],
                  ULTIMI_PREDEFINITI, GIORNI_PREDEFINITI, adesso)
    quattro = giudica([giro([m("C1(gnome)x2"), m("C1(kde)x2"),
                             m("C1(xfce)x2"), m("C1(lxqt)x2")])],
                      ULTIMI_PREDEFINITI, GIORNI_PREDEFINITI, adesso)
    ok = (una is not None and not una["guai"] and una["scatole"] == ["gnome"]
          and quattro is not None and not quattro["guai"]
          and quattro["scatole"] == ["gnome", "kde", "lxqt", "xfce"])
    print("  %s  %-63s ⇒ %s"
          % ("OK " if ok else "NO ",
             "⭐⭐ UNA scatola sola resta VERDE, e il conto si stampa lo stesso",
             "%r contro %r" % (una["scatole"] if una else None,
                               quattro["scatole"] if quattro else None)))
    if not ok:
        guai += 1

    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi sbagliati" % guai)
        return 1
    print("⭐ il giudice vede la macchina di prova spenta mentre il registro si")
    print("   riempie di giri verdi, ⭐⭐ e ⛔ NON si lascia ingannare ne' da un")
    print("   «la meta' remota e' verde» ne' da una fila di 3")
    print("⭐ e si accende nei DUE VERSI: a 20 giorni rosso, a 6,5 verde; a 21")
    print("   giri fuori finestra rosso, a 19 dentro verde")
    print("⚠ e questa certificazione copre IL GIUDIZIO, non il trasporto: che le")
    print("  righe della macchina di prova arrivino davvero fin qui lo dice")
    print("  `11-registro-unisci.py`, non io")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def qui_c_e_il_deposito():
    """⭐ La stessa domanda di C12, e per la stessa ragione.

    ⛔ Non e' pignoleria: sulla macchina di prova il registro contiene solo i
       giri di quella macchina — tutti sulle scatole — e C15 sarebbe verde
       qualunque cosa succeda (`LEZIONI.md` §1.44).
    """
    try:
        p = subprocess.run(["git", "-C", QUI, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=30)
    except OSError:
        return False
    return p.returncode == 0 and bool(p.stdout.strip())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--ultimi", type=int, default=ULTIMI_PREDEFINITI,
                   help="quanti giri veri guardare indietro. `[R]` la finestra "
                        "di C13, `[?]` alla sua origine")
    p.add_argument("--giorni", type=int, default=GIORNI_PREDEFINITI,
                   help="da quanti giorni al massimo le scatole possono non "
                        "aver girato. `[R]` la soglia di C12, `[?]` alla sua "
                        "origine")
    p.add_argument("--ovunque", action="store_true",
                   help="⛔ NON usarlo per far tacere un 2: qui il registro non "
                        "e' la memoria unita e il verde non vorrebbe dire "
                        "niente. Serve a diagnosticare un registro passato per "
                        "--registro")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if not a.ovunque and not qui_c_e_il_deposito():
        print("⛔ non sono dentro un deposito git.")
        print("   ⇒ se questa e' la macchina di prova, qui il registro contiene")
        print("     SOLO i giri di questa macchina — cioe' tutti giri sulle")
        print("     scatole — e questa maglia sarebbe verde qualunque cosa")
        print("     succeda: un predicato che non puo' fallire.")
        print("   ⭐ La memoria unita sta sul portatile, e li' va fatta girare.")
        print("   ⇒ il terreno non regge")
        sys.exit(2)

    giri, guaio = leggi_il_registro(a.registro)

    print("== C15 — la meta' remota gira davvero? ==")
    print("   ⛔ il guasto che cerca: la macchina di prova spenta in silenzio —")
    print("      ⛔⛔ e con C12 e C13 che restano VERDI, perche' la meta' del")
    print("      portatile gira lo stesso e lascia traccia")
    print("   metro: ultimi %d giri VERI `[R]` da C13  ·  ultimo giro sulle"
          % a.ultimi)
    print("          scatole entro %d giorni `[R]` da C12  ·  ⛔ all'origine `[?]`"
          % a.giorni)
    print("   ⛔ conta il GIUDIZIO di una maglia che vuole una scatola (0 o 1),")
    print("      non un 3 e non «la meta' remota e' verde»")
    print()

    if guaio == "assente":
        print("⛔ il registro non c'e': %s" % a.registro)
        print("   ⇒ non ho potuto guardare — ⛔ e NON e' un rosso.")
        print("     Che il gancio non abbia mai girato lo dice C12, ed e' giusto")
        print("     che lo dica UNA maglia sola.")
        return 3
    if guaio == "illeggibile":
        print("⛔ il registro c'e' e non si lascia leggere: %s" % a.registro)
        print("   ⇒ non ho potuto guardare")
        return 3

    r = giudica(giri, a.ultimi, a.giorni, time.time())
    if r is None:
        print("⛔ nessun giro VERO da guardare (%d righe, tutte a vuoto o nessuna)"
              % len(giri or []))
        print("   ⇒ non ho potuto guardare — ⛔ e NON e' un rosso")
        return 3

    print("   giri nel registro    : %d veri, %d a vuoto" % (r["totali"], r["a_vuoto"]))
    print("   guardati             : gli ultimi %d" % r["esaminati"])
    # ⚠ Il RAPPORTO si stampa e ⛔ NON si giudica: una soglia tipo «almeno un
    #   terzo dei giri sulle scatole» sarebbe un numero tondo inventato, cioe'
    #   un `[?]` travestito da metro.  ⭐ Ma chi legge deve vederlo, perche' e'
    #   la forma in cui il guasto si annuncia PRIMA di diventare rosso.
    print("   ⭐ sulle scatole      : %d su %d" % (r["sulle_scatole"], r["esaminati"]))
    print("   ⭐ col carico vero    : %d su %d  (una sessione accesa dentro una scatola)"
          % (r["col_carico"], r["esaminati"]))
    if r["ultimo"] is not None:
        print("   ultimo sulle scatole : %s  (%s)"
              % (r["ultimo"].get("istante"),
                 "eta ignota" if r["eta"] is None else "%.1f giorni fa" % r["eta"]))
        print("     ⇒ ci sono arrivate : %s" % ", ".join(r["ultimo_maglie"]))
    if r["ultimo_carico"] is not None:
        print("   ultimo col carico    : %s" % r["ultimo_carico"].get("istante"))
    # ⚠ INFORMAZIONE, non giudizio — e la riga lo dice, o qualcuno lo
    #   trasformera' in un rosso perpetuo (vedi la domanda 3 in testa).
    print("   ⚠ scatole viste      : %d  (%s)"
          % (len(r["scatole"]), ", ".join(r["scatole"]) if r["scatole"] else "nessuna col nome scritto"))
    print("     ⛔ e' informazione, NON un giudizio: la famiglia veloce guarda la")
    print("        sola GNOME per scelta dichiarata, e il prodotto oggi sa")
    print("        accendere un desktop solo")
    print("   ⚠ macchine nel registro: %s"
          % (", ".join(r["macchine"]) if r["macchine"] else "nessuna lo dice"))
    print()

    if r["guai"]:
        print("⛔⛔ ROSSO — la meta' che vale non sta girando:")
        for g in r["guai"]:
            print("   · %s" % g)
        print()
        print("   ⇒ ⛔ e il danno non e' che manchi una misura: e' che **C12 e")
        print("     C13 restano VERDI** mentre succede.  La meta' del portatile")
        print("     gira in un secondo, lascia traccia, e ci innesta dentro il")
        print("     guasto di C10: la rete si racconta di essere viva.")
        print()
        print("   ⭐ Per farla tornare verde — e si torna verde, non e' un rosso")
        print("     perpetuo:")
        print("       bash 11-gancio.sh remoto --famiglia tutto")
        print("     oppure, sulla macchina di prova:")
        print("       bash 11-gancio.sh gira --famiglia funziona")
        print("   ⚠ Se non torna verde, il guasto e' nella delega o nel")
        print("     trasporto del registro, non in questa maglia.")
        return 1

    print("⭐ negli ultimi %d giri veri le scatole hanno girato %d volte, e %d"
          % (r["esaminati"], r["sulle_scatole"], r["col_carico"]))
    print("   volte col carico vero — una sessione accesa dentro una scatola")
    # ⚠⚠ E QUI C'E' UN NUMERO, e va detto che c'e' invece di far finta di no
    #    (`LEZIONI.md` §1.50: un commento che descrive una grandezza diversa da
    #    quella che il codice governa e' una trappola).
    #
    #    **La meta'** — e governa UNA cosa sola: se questa riga si stampa.
    #    ⛔ Non governa l'esito: sotto la meta' C15 e' verde esattamente come
    #       sopra.  ⇒ E' un avviso, non una soglia di giudizio, ⭐ e non ha
    #       bisogno di una misura sotto perche' non decide niente.
    if r["sulle_scatole"] * 2 <= r["esaminati"]:
        print("⚠ ⛔ e sono **la minoranza**: %d giri su %d sono stati eseguiti"
              % (r["esaminati"] - r["sulle_scatole"], r["esaminati"]))
        print("  senza toccare una scatola.  ⚠ Questo NON e' un rosso — l'esito")
        print("  resta verde — ⭐ ma e' la forma in cui il guasto arriva: la")
        print("  meta' del portatile che continua a scrivere righe verdi mentre")
        print("  l'altra si dirada.  ⇒ Uno solo, poi zero.")
    print("⚠ e questa maglia dice che le scatole GIRANO, ⛔ non che il gancio le")
    print("  faccia partire da solo (quello e' C12), ne' che le scatole siano")
    print("  quelle giuste (quello e' C11).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
