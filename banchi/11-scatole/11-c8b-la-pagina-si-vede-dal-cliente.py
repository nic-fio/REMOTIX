#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c8b — ⭐⭐⭐ «E LA STESSA PAGINA SI VEDE **DAL CLIENTE**»
===========================================================================

    python3 11-c8b-la-pagina-si-vede-dal-cliente.py
    python3 11-c8b-la-pagina-si-vede-dal-cliente.py --senza-cura
    python3 11-c8b-la-pagina-si-vede-dal-cliente.py --certifica

⛔ E' la META' B di C8, quella che nel documento di fase (§4.1, riga «C8b») era
   dichiarata *«oggi non si misura: le sessioni nuove nascono cieche»*.

---------------------------------------------------------------------------
⭐⭐ PERCHE' ADESSO SI PUO' — e la ragione va letta prima del codice
---------------------------------------------------------------------------

`[M]` 27 agosto 2026, banco isolato con Mutter vero: il `wl_output` di una
sessione headless nasce ⛔ **soltanto quando un consumatore PipeWire si aggancia
al flusso** — 65-93 ms dopo l'aggancio, ⛔ **mai prima**.

⇒ ⭐ **Mentre un cliente e' attaccato, lo schermo c'e'.**  E «mentre un cliente
  e' attaccato» e' esattamente la condizione di questa prova.  ⛔ La riga «oggi
  non si misura» non e' piu' vera, e questa maglia esiste per quello.

⚠⚠ E LA STESSA SCOPERTA PORTA DUE VINCOLI, che qui sono il disegno:

  1. ⭐ **Il cliente si attacca PRIMA**, e il browser si accende **dopo**, con il
     cliente ancora attaccato.  ⛔ La stesura vecchia della prova B faceva il
     contrario — scatto, distacco, browser, secondo scatto — cioe' accendeva il
     browser **quando lo schermo non c'era**, e poi si stupiva di non vedere
     niente.
  2. ⛔ **Il monitor muore con la connessione D-Bus del figlio, e il figlio
     muore col cliente.**  ⇒ Niente di quel che si vede qui sopravvive a un
     distacco, e questa maglia non ci conta mai: ⭐ **un attacco solo, continuo,
     che copre l'accensione del browser E la ripresa.**  (Quel che sopravvive a
     un distacco e' il mestiere di C6, non di questa.)

---------------------------------------------------------------------------
⛔⛔ FILE NUOVO E NON UN BRACCIO DI C8a — e la scelta si argomenta
---------------------------------------------------------------------------

La domanda vera era: *un braccio in piu' dentro `11-c8-il-secondo-apre-il-
browser.py`, o un file suo?*  ⚠ Le due strade avevano argomenti veri.

⭐ **A favore del braccio**: la scena e' la stessa — lo scheletro con
  `.cache -> /tmp`, i due inquilini fatti con `useradd -m`, la cura della
  provvista, il giudice dei pixel.  ⛔ Duplicarli vorrebbe dire **due posti che
  possono divergere in silenzio**, che e' il difetto che questo progetto teme
  per iscritto (`LEZIONI.md` §1.25, §1.17).

⛔ **A favore del file nuovo**, e ha vinto per tre ragioni che non si annullano:

  · **girano in posti diversi.**  C8a ⭐ non passa dal prodotto e gira in
    QUALUNQUE scatola (il collaudo del 26 agosto e' girato in quella di PLASMA).
    C8b passa dal prodotto, ⛔ e il prodotto sa avviare **solo GNOME**
    (`[R]` `src/sessione.c:778` scrive un drop-in per `gnome-shell`, e tutto
    `src/mutter.c` parla con Mutter).  ⇒ Nella scatola di KDE C8b direbbe «non
    ho potuto guardare» per sempre — il cugino del rosso perpetuo di §1.49.
  · **costano in modo diverso.**  C8a: `[M]` due inquilini, un paio di minuti.
    C8b: `[S]` **~6 minuti** — ogni inquilino tiene un filo attaccato per
    `26 + 120 + 30 = 176 s` (il tetto del palco di C1, quello del browser, il
    margine), ⛔ e il filo lo scrive solo alla fine.  ⇒ Un file solo
    obbligherebbe il gancio a pagare il caro per avere il poco.
  · **hanno esiti loro.**  Nel registro del gancio due mestieri diversi sotto lo
    stesso nome sono due righe che non si sanno leggere (§1.52: il giunto fra
    due maglie e' il posto dove i difetti si nascondono).

⭐⭐ **E l'argomento del braccio non si e' buttato: si e' onorato importando.**
  ⛔ Questa maglia **non riscrive niente** della scena: scheletro, creazione
  degli inquilini, cura della provvista, sgombero del posto condiviso, colore,
  tolleranza, frazione minima e lettore dei pixel ⇒ **arrivano tutti da C8a**,
  per `import`.  ⚠ E' la stessa disciplina che C8a applica a `10-f1-testimone.py`
  (*«il giudice si IMPORTA, non si riscrive»*) e che `10-f1` applica a
  `03-marca.py`.  ⇒ Se domani la tolleranza cambia in C8a, **cambia anche qui**,
  e non c'e' nessun secondo posto da ricordarsi.

---------------------------------------------------------------------------
⭐ COME GIUDICA — il pixel, **attraverso il prodotto**, e per DIFFERENZA
---------------------------------------------------------------------------

Per ogni inquilino, con **un attacco solo**:

    t=0    si attacca il cliente di prova  (⇒ nasce il monitor)
    t=?    si aspetta **l'evento**: il registro del prodotto dice che il palco
           ha montato un monitor per QUESTO inquilino
    +resp  un respiro, perche' almeno un fotogramma senza browser sia partito
    ⇒      si accende il browser DENTRO la sessione (kiosk, la pagina di C8)
    +brw   si aspetta che disegni
    t=R    il cliente si stacca e **scrive il flusso** (⛔ lo scrive solo alla
           fine: `01-b3-cliente.py`, `scrivi_video`)
           ⇒ dal flusso si tirano fuori DUE fotogrammi:
               il PRIMO   = il desktop **prima** che il browser disegnasse
               l'ULTIMO   = quel che il desktop mostra **adesso**

E il verdetto e' una **differenza**, non un valore assoluto:

    ⭐ ha visto la pagina  ⟺  frazione(ultimo) >= minima  E  frazione(primo) < minima

⛔ Il «prima» non e' cerimonia, e qui fa **tre** lavori:

  1. se il desktop e' nero o quasi-nero, ⇒ ⛔ **non e' un rosso di C8b**: e' il
     guasto che sta a monte, e dare la colpa al browser di una cosa successa
     prima che il browser esistesse e' il modo esatto in cui questo progetto ha
     gia' perso due diagnosi;
  2. se la pagina c'e' **gia'** prima che io accenda il browser, ⛔ **non e' un
     verde**: vorrebbe dire prendermi il merito del browser di qualcun altro.
     ⇒ «non ho potuto guardare», e si dice perche';
  3. e senza di lui *«il browser non ha aperto»* e *«non c'era nessuno schermo»*
     avrebbero la stessa faccia — ⚠ due guasti diversi con un sintomo solo.

⛔⛔ E «IL PALCO C'E'» NON SE LO CHIEDE DA SE': LO CHIEDE A **C1**.
   Il giudice della nascita — `leggi_nascita`, `monitor_nato`, `verdetto_giro` —
   e il suo tetto `TETTO_NASCITA` si **importano** da `11-c1-nasce-e-si-vede.py`.
   ⇒ ⭐ *«il palco ha montato un monitor per questo inquilino?»* e' una domanda
     sola, e in tutta la rete ha **una risposta sola**.

   ⚠⚠ E l'importo evita un errore che questa maglia avrebbe copiato volentieri:
      fino al 27 agosto 2026 la riga «⛔ ZERO MONITOR» era letta come **prova di
      cecita'**, ⛔ e `[R]` `src/sessione.c:345-348` la scrive nel passaggio
      obbligatorio di una nascita **RIUSCITA** — il monitor lo monta la cattura,
      dopo, quando qualcuno si aggancia.  ⭐ C1 oggi quella riga la conta e la
      stampa senza giudicarla, e C8b eredita la correzione invece di ripeterla.

   ⛔⛔ E LO STESSO VALE PER IL TETTO, che qui non c'e'.  La prima stesura aveva
      scritto **152 s**, copiati da C1 — 101,0 s misurati su GNOME piu' meta'.
      `[M]` Poche ore dopo si e' scoperto che quei ~97 s **non erano del
      prodotto**: erano un difetto della SCATOLA, e curata la scatola il palco
      nasce in **1,0 s** e il tetto di C1 e' sceso a **26 s**.  ⇒ ⭐ Un numero
      copiato e' un numero che resta indietro (`LEZIONI.md` §1.17): qui ce n'e'
      **uno solo**, e sta in C1.

---------------------------------------------------------------------------
⛔ COME SO CHE SA DARE ROSSO — `--senza-cura`, e si legge AL CONTRARIO
---------------------------------------------------------------------------

Stesso guasto innestato di C8a: gli inquilini nascono **senza** la cura di
`src/provisiona.sh`, cioe' come li faceva il codice del 25 agosto 2026 ⇒ il
**secondo** non riesce a farsi il profilo di Firefox, e la pagina non arriva.

⭐ E l'esito col guasto innestato **non si misura sul colore del verdetto** —
  `LEZIONI.md` §1.52.  Si pretende una **differenza misurabile**:

    guasto VISTO (esito 0)  ⟺  il PRIMO ha visto la pagina
                            E  almeno un altro NO
                            E  ⭐ le due frazioni distano almeno `SALTO_MINIMO`

  ⛔ Rosso a tutt'e due ⇒ esito **1**, e la riga lo dice: *«ha fallito anche il
     PRIMO»* — quel che si sta misurando non e' quel guasto (§7-bis.12, §1.45).
  ⛔ Verde a tutt'e due ⇒ esito **1**: o la cura non serviva, o questa maglia
     non guarda nel posto giusto.
  ⛔ Nessun giudizio ⇒ esito **3**: non posso dire se il guasto si sarebbe visto.

---------------------------------------------------------------------------
⭐ CHE COSA HA GIA' GIRATO — e che cosa no, che e' la meta' che conta
---------------------------------------------------------------------------

  `[M]` 27 ago 2026, **sul portatile**  `--certifica`: **51 casi su 51**, e
        ⭐ **12 guasti innestati nel banco stesso, tutti e 12 hanno morso**
        (fra cui: la guardia «ha fallito anche il PRIMO» smontata, il salto
        minimo smontato, il tetto del palco ricopiato invece che preso da C1).
  `[M]` 27 ago 2026, **sul portatile**  giro **a secco** della meccanica —
        cliente finto, registro finto, `ffmpeg` vero, flussi H.264 veri:
        i cinque casi (il browser disegna · non disegna · desktop nero ·
        nessun fotogramma · il palco non nasce) danno **SI · NO · non lo so ·
        non lo so · non lo so**, che e' quel che devono dare.
        ⭐ E un numero che vale: attraverso una catena **H.264 4:2:0 vera** il
        magenta torna indietro al **97,8 %** — cioe' la tolleranza di C8a
        (±48) regge il sottocampionamento del croma, che era il rilievo di
        Gemini accolto in §4.3.

  ⛔⛔ E QUEL CHE NON HA GIRATO, dichiarato: **il giro vero, nella scatola**.
     Non c'e' nessun `[M]` di questa maglia contro il prodotto — ne' verde ne'
     rosso — e finche' non c'e', ⚠ **i tetti sono argomenti, non misure**.
     ⇒ `--certifica` copre i giudizi e il giunto; ⛔ **non** copre la meccanica
       (il filo, `ffmpeg`, l'attesa) — quella l'ha esercitata il giro a secco,
       e nemmeno lui ha mai parlato col prodotto.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: TUTTI gli inquilini vedono la pagina DAL CLIENTE
  1  ho guardato: almeno uno NON la vede                    ⇒ rosso
  3  ⛔ non ho potuto guardare (niente palco, niente fotogrammi, giudice
     assente, campo non pulito) — ⛔ e NON e' un rosso
  2  il terreno non regge, o l'uso e' sbagliato

⚠ ⛔ E QUEL CHE QUESTA MAGLIA **NON** GUARDA, dichiarato:
  · **non** dice che il browser sia partito quando la pagina non si vede: dice
    che dal cliente non si vede.  ⭐ Chi separa i tre guasti (browser morto ·
    profilo mai nato · pagina non a schermo) e' **C8a**, e le due vanno lette
    insieme;
  · **non** guarda il collegamento `/etc/skel/.cache`: guarda l'effetto, non la
    causa che crediamo di conoscere;
  · **non** dice niente sulle sessioni **senza** nessuno attaccato — ⛔ e su
    quelle, dopo la scoperta del 27 agosto, non c'e' niente da dire: lo schermo
    li' non esiste per costruzione.
===========================================================================
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I TETTI — ognuno col SUO nome e il SUO valore.  `LEZIONI.md` §1.45: un
#    tetto prestato da un'altra prova produce un rosso che non distingue piu'
#    il guasto dal banco, e allora il collaudo non vale niente.
# ═══════════════════════════════════════════════════════════════════════════

# ── quanto puo' metterci il palco a montare un monitor ──────────────────────
# ⭐⭐ QUESTO NUMERO **NON STA QUI**: si prende da `11-c1-nasce-e-si-vede.py`
#     (`TETTO_NASCITA`), che e' la maglia il cui mestiere e' la nascita, e che
#     quel tetto lo certifica contro la propria misura.
#
# ⛔⛔ E la ragione e' costata mezza giornata a qualcun altro, oggi.  La prima
#     stesura di questa maglia ci aveva scritto **152 s**, copiati da C1 —
#     101,0 s misurati su GNOME per meta'.  ⚠ Poche ore dopo si e' scoperto che
#     quei ~97 s **non erano del prodotto**: erano un difetto della SCATOLA
#     (`groupmod -g` su `polkitd` che non si portava dietro i file ⇒ polkit
#     morto ⇒ quattro scadenze da 25 s addosso a `gnome-shell`).  ⇒ `[M]` 27
#     agosto 2026, scatola curata: il palco nasce in **1,0 s**, e il tetto di C1
#     e' sceso a **26 s**.
# ⇒ ⛔ Un numero copiato e' un numero che resta indietro (`LEZIONI.md` §1.17:
#   *un numero nuovo entra in cinque posti, e uno resta sempre indietro*).  ⭐ Qui
#   ce n'e' **uno solo**, ed e' di C1.

# ── quanto si da' al BROWSER per disegnare, dentro la sessione ───────────────
# ⛔ NON e' 25 s, e la ragione e' misurata: `LEZIONI.md` §1.45 — il **primo**
#    avvio di Firefox in una scatola fredda (che deve prima farsi il profilo)
#    passa abbondantemente i 25 s, e con quel tetto C8a dava **rosso a tutt'e
#    due** gli inquilini, con la cura e senza.  ⇒ C8a si e' data 120 s
#    (`--attesa-scatto`), e qui il browser e' **altrettanto freddo**: gli
#    inquilini di questa maglia sono nuovi, e il profilo non esiste ancora.
# ⚠ `[?]` Qui il browser deve anche **mappare una finestra su Wayland** e farla
#   arrivare al codificatore — cioe' fa **di piu'** che in C8a.  ⇒ 120 s e' un
#   limite basso credibile, non uno misurato: si tara al primo giro vero.
ATTESA_BROWSER = 120.0

# ── il respiro fra «il palco c'e'» e «accendo il browser» ────────────────────
# ⚠ Serve a una cosa sola: che almeno un fotogramma **senza browser** sia gia'
#   partito, o il «primo fotogramma» conterrebbe gia' la pagina e la maglia non
#   saprebbe distinguere la propria pagina da una che c'era gia'.
# ⛔ `[?]` Tre secondi e' una scelta prudente, non una misura.  Se al giro vero
#    il «prima» esce gia' magenta, ⭐ **il numero da alzare e' questo** — e la
#    maglia lo dice da se' invece di lasciarlo indovinare.
RESPIRO = 3.0

# ── il margine sul filo, dopo che il browser ha avuto il suo tempo ───────────
# ⛔ Il cliente di prova scrive il flusso **solo alla fine** di `--resta`
#    (`01-b3-cliente.py`, `scrivi_video`: *«si chiama DOPO l'attesa di --resta»*)
#    ⇒ non esiste un file da guardare a meta' strada, e `--resta` va deciso
#    PRIMA di sapere quanto ci mettera' il palco.  ⚠ E' il costo di questa
#    maglia, ed e' dichiarato invece che nascosto.
MARGINE_FILO = 30.0

# ── ⭐ IL SALTO CHE RENDE MISURABILE LA DIFFERENZA (`LEZIONI.md` §1.52) ───────
# Col guasto innestato non basta che il primo sia «si'» e il secondo «no»: le
# due frazioni devono **distare**, o si starebbe festeggiando un capello.
# ⚠ E la soglia si scrive sulla grandezza vera del fenomeno (§1.13): `[M]` 26
#   agosto 2026, C8a col guasto innestato ⇒ primo **98,7 %**, secondo **niente**.
#   ⇒ Un salto di 0,10 e' un decimo di quel che il fenomeno fa davvero: lontano
#   dal rumore, e lontanissimo dal vero.
SALTO_MINIMO = 0.10


# ═══════════════════════════════════════════════════════════════════════════
# GLI IMPORTI — ⛔ e ognuno con la ragione per cui non si riscrive
# ═══════════════════════════════════════════════════════════════════════════
def _modulo(percorso, nome):
    """Carica un banco vicino come modulo.  Torna `None` se non c'e' o non si
    lascia caricare — ⛔ e chi chiama deve dire «non ho potuto guardare», mai
    ripiegare su un giudizio piu' povero in silenzio."""
    if not percorso or not os.path.exists(percorso):
        return None
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception:
        return None
    return m


def prendi_c8a():
    """⭐⭐ LA SCENA E IL METRO ARRIVANO DA C8a, e non da una loro parafrasi.

    ⛔ Da qui vengono: `COLORE`, `TOLLERANZA`, `FRAZIONE_MINIMA`,
       `frazione_del_colore`, `prepara_lo_scheletro`, `sgombra_il_posto_condiviso`,
       `crea`, `applica_la_cura`, `sa_scrivere_nella_cache`, `apri_il_browser`,
       `sh` e `giudice_immagini`.
    ⇒ ⭐ Due maglie che misurano lo stesso colore con la stessa tolleranza
      **perche' e' lo stesso numero**, non perche' qualcuno si e' ricordato di
      copiarlo tutt'e due le volte.
    """
    return _modulo(os.path.join(QUI, "11-c8-il-secondo-apre-il-browser.py"),
                   "c8a")


# ⭐ I quattro pezzi di C1 senza i quali questa maglia non sa aspettare il palco.
#   ⛔ Sono qui, in un elenco, e non sparsi nel codice: un elenco si puo'
#      controllare, una decina di `getattr` no.
PEZZI_DI_C1 = ("leggi_nascita", "monitor_nato", "verdetto_giro", "TETTO_NASCITA")


def c1_ha_quel_che_serve(c1):
    """⛔ «C1 c'e'» non e' «C1 ha quel che mi serve».

    ⚠ C1 e' viva: `[M]` il 27 agosto 2026 e' stata riscritta due volte in un
      giorno, e la prima stesura di C8b importava una `FIRMA_MONITOR` che dopo
      quella riscrittura **non esisteva piu'**.  ⇒ La maglia se n'e' accorta
      perche' `--certifica` glielo chiedeva; ⛔ senza il controllo si sarebbe
      accorta solo dentro la scatola, con un `None` in mano e un rosso storto.
    ⭐ Quindi: se la maglia della nascita cambia forma, questa **lo dice** invece
      di ripiegare in silenzio su un giudizio suo (`LEZIONI.md` §1.29).
    """
    if c1 is None:
        return False
    return all(hasattr(c1, pezzo) for pezzo in PEZZI_DI_C1)


def prendi_c1():
    """⭐⭐ IL GIUDICE DELLA NASCITA ARRIVA DA C1 — ⛔ e non si riscrive.

    Da qui vengono `leggi_nascita`, `monitor_nato`, `verdetto_giro` e il tetto
    `TETTO_NASCITA`.  ⇒ ⭐ *«il palco ha montato un monitor per questo
    inquilino»* e' **una domanda sola**, e ha **una risposta sola** in tutta la
    rete: quella di C1.

    ⚠⚠ E l'importo evita di ereditare un difetto che questa maglia avrebbe
       copiato volentieri: fino al 27 agosto 2026 la riga «⛔ ZERO MONITOR» era
       letta come **prova di cecita'**, ⛔ e `[R]` `src/sessione.c:345-348` la
       scrive nel passaggio obbligatorio di una nascita **RIUSCITA** — il
       monitor lo monta la cattura, dopo.  ⇒ C1 oggi quella riga la **conta e la
       stampa**, e non la giudica.  ⭐ Importando, C8b eredita la correzione
       invece di ripetere l'errore.

    Torna il modulo, oppure `None` se non c'e' o se non ha quel che serve.
    """
    c1 = _modulo(os.path.join(QUI, "11-c1-nasce-e-si-vede.py"), "c1")
    return c1 if c1_ha_quel_che_serve(c1) else None


def trova_il_giudice(c8a):
    """Il giudice delle immagini di `10-f1-testimone.py`.

    ⚠ Due posti, e si DICE quale si e' usato (`LEZIONI.md` §1.48: un messaggio
      di riuscita che ripete l'intenzione non e' una verifica, e' un'eco):
        · accanto a C8a  ⇒ com'e' dentro la scatola (`/opt/remotix`)
        · nella cartella di sopra ⇒ com'e' nel deposito (`banchi/`)
    ⛔ Se non c'e' ne' qui ne' li', l'esito e' **3**, mai un giudizio piu' povero.
    """
    g = c8a.giudice_immagini() if c8a is not None else None
    if g is not None:
        return g, os.path.join(QUI, "10-f1-testimone.py")
    sopra = os.path.join(os.path.dirname(QUI), "10-f1-testimone.py")
    g = _modulo(sopra, "testimone10f1")
    if g is not None and hasattr(g, "giudica"):
        return g, sopra
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GIUDIZI — funzioni PURE, perche' `--certifica` le possa far girare tutte
#    senza una scatola, senza un server e senza un browser.
# ═══════════════════════════════════════════════════════════════════════════
def tetto_del_palco(c1):
    """⭐ Il tetto d'attesa del palco, **preso da C1**.

    ⛔ Non e' una costante di questo file, e non deve diventarlo: il giorno che
       la nascita cambia velocita', il numero si corregge in **un posto solo**,
       quello della maglia che la misura.
    """
    return float(c1.TETTO_NASCITA)


def resta_del_filo(attesa_palco, attesa_browser, margine=MARGINE_FILO):
    """Quanto deve restare attaccato il cliente.

    ⛔ Si CALCOLA dai tre tetti, non si sceglie: il filo deve coprire l'attesa
       del palco **piu'** quella del browser, o la maglia si staccherebbe prima
       di aver guardato quel che e' venuta a guardare.
    """
    return float(attesa_palco) + float(attesa_browser) + float(margine)


def giudica_il_prima(verdetto, frazione, minima):
    """Che cosa mostrava il desktop **prima** che accendessi il browser.

    `verdetto`  quel che dice il giudice di `10-f1` («nero», «quasi-nero»,
                «tinta-unita», «disegnato»), oppure `None` = non ho guardato
    `frazione`  quanta parte era gia' del colore della pagina, oppure `None`

    Torna `(stato, spiegazione)`, con `stato` fra:
      «pulito»       ⭐ c'e' uno schermo, disegnato, e la pagina NON c'e' ancora
      «a-monte»      ⛔ lo schermo e' nero: il guasto sta prima del browser
      «gia-magenta»  ⛔ la pagina c'era gia': non posso attribuirmela
      «non-lo-so»    ⛔ non ho guardato — ⚠ e `None` non e' zero
    """
    if verdetto is None or frazione is None:
        return "non-lo-so", ("non ho potuto guardare il desktop PRIMA del "
                             "browser ⇒ ⛔ non e' «era nero»")
    if verdetto in ("nero", "quasi-nero"):
        return "a-monte", ("il desktop e' «%s» PRIMA del browser: il guasto sta "
                           "a monte di C8b, ⛔ e non e' un suo rosso" % verdetto)
    if frazione >= minima:
        return "gia-magenta", ("⛔ la pagina copriva gia' il %.1f%% dello schermo "
                               "PRIMA che accendessi il browser: non posso dire "
                               "che l'abbia disegnata io" % (frazione * 100))
    return "pulito", ("il desktop e' «%s» e la pagina non c'e' ancora "
                      "(%.1f%%)" % (verdetto, frazione * 100))


def giudizio_inquilino(stato_prima, frazione_dopo, minima):
    """⭐ Il verdetto su UN inquilino: ha visto la pagina dal cliente?

    Torna `(True|False|None, motivo)` — ⛔ e `None` («non ho guardato») non e'
    `False` («ho guardato e non c'era»).
    """
    if stato_prima != "pulito":
        return None, "il campo non era pulito ⇒ non giudico il dopo"
    if frazione_dopo is None:
        return None, ("non ho potuto guardare il desktop DOPO ⇒ ⛔ non e' «la "
                      "pagina non c'era»")
    if frazione_dopo >= minima:
        return True, "la pagina copre il %.1f%% dello schermo" % (frazione_dopo * 100)
    return False, ("⛔ la pagina copre il %.1f%%, e ne serve almeno il %.0f%%"
                   % (frazione_dopo * 100, minima * 100))


def decidi(esiti, senza_cura, minima, salto=SALTO_MINIMO):
    """⭐⭐ IL GIUNTO — da N giudizi a UN codice d'uscita.

    ⛔ Sta in una funzione pura apposta: `LEZIONI.md` §1.52 racconta un difetto
       che **nessuna certificazione ha preso** perche' stava nel giunto fra due
       maglie — nel codice d'uscita, che non era il mestiere di nessuno dei due
       giudici.  ⇒ Qui il codice d'uscita **e'** un mestiere, e ha i suoi casi.

    `esiti` e' una lista, **in ordine di nascita**, di dizionari:
        {"chi": str, "visto": True|False|None, "dopo": float|None, ...}

    Torna `(codice, motivo, righe_da_stampare)`.

    ⭐⭐ E IL `motivo` NON E' UN LUSSO — e' nato da un guasto innestato che NON
    HA MORSO.  `[M]` 27 agosto 2026, scrivendo questa maglia: disfacendo la
    guardia *«ha fallito anche il PRIMO»* il codice d'uscita restava **1** lo
    stesso — per un'altra strada (il salto troppo piccolo) — ⛔ e una
    certificazione che guardava solo il numero **diceva OK su una guardia
    smontata**.
    ⇒ ⛔ Un verdetto giusto per la ragione sbagliata e' un verdetto che smettera'
      di essere giusto senza che nessuno se ne accorga (`LEZIONI.md` §2.0: *un
      banco che dice «no» deve dire CON CHE PALCO ha detto no*).  ⭐ Percio' il
      motivo esce dalla funzione, e la certificazione lo pretende insieme al
      numero.
    """
    righe = []
    si = [e for e in esiti if e["visto"] is True]
    no = [e for e in esiti if e["visto"] is False]
    ignoti = [e for e in esiti if e["visto"] is None]

    righe.append("  ⭐ vedono la pagina dal cliente: %d · ⛔ NON la vedono: %d · "
                 "non giudicati: %d" % (len(si), len(no), len(ignoti)))

    if not senza_cura:
        if no:
            righe.append("⛔ ROSSO: %d inquilini su %d non vedono la pagina dal "
                         "cliente" % (len(no), len(esiti)))
            for e in no:
                righe.append("   ⇒ %s: %s" % (e["chi"], e.get("perche", "")))
            return 1, "rosso", righe
        if ignoti or not esiti:
            righe.append("⛔ non ho potuto giudicare %d inquilini su %d ⇒ non e' "
                         "un verde e non e' un rosso (§4.5)"
                         % (len(ignoti), len(esiti)))
            for e in ignoti:
                righe.append("   ⇒ %s: %s" % (e["chi"], e.get("perche", "")))
            return 3, "non-giudicato", righe
        righe.append("⭐ tutt'e %d gli inquilini vedono la pagina ATTRAVERSO IL "
                     "PRODOTTO" % len(esiti))
        return 0, "tutti-vedono", righe

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ COL GUASTO INNESTATO SI LEGGE AL CONTRARIO: qui il verde e' un rosso.
    # ═══════════════════════════════════════════════════════════════════════
    if not esiti or all(e["visto"] is None for e in esiti):
        righe.append("⛔ non ho potuto giudicare nessuno: non posso dire se il "
                     "guasto si sarebbe visto")
        return 3, "nessun-giudizio", righe
    primo = esiti[0]
    if primo["visto"] is None:
        righe.append("⛔ non ho potuto giudicare il PRIMO inquilino (%s): senza "
                     "di lui non so di CHI sarebbe il rosso" % primo["chi"])
        return 3, "primo-non-giudicato", righe
    if primo["visto"] is False:
        righe.append("⛔⛔ HA FALLITO ANCHE IL PRIMO (%s): il guasto atteso morde "
                     "dal SECONDO in poi." % primo["chi"])
        righe.append("   ⇒ o il posto condiviso era gia' sporco, o quel che si "
                     "sta misurando non e' il difetto della provvista.")
        righe.append("   ⚠ E un rosso che non distingue il guasto dal banco non "
                     "certifica niente (`LEZIONI.md` §1.45).")
        return 1, "anche-il-primo", righe
    if not no:
        righe.append("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: tutti vedono la "
                     "pagina anche senza la cura.")
        righe.append("   ⇒ o la cura non serviva, o questa maglia non guarda nel "
                     "posto giusto — e in tutt'e due i casi non ci si puo' "
                     "fidare di lei.")
        return 1, "guasto-non-visto", righe

    # ⭐ E adesso la parte che vale: la DIFFERENZA, misurata (`LEZIONI.md` §1.52).
    fr_primo = primo.get("dopo")
    peggiori = [e.get("dopo") for e in no if e.get("dopo") is not None]
    if fr_primo is None or not peggiori:
        righe.append("⛔ il guasto sembra visto, ma non ho i due numeri per "
                     "misurare la differenza ⇒ non certifico niente")
        return 3, "senza-numeri", righe
    distanza = fr_primo - max(peggiori)
    righe.append("   la differenza: primo %.1f%% · peggiore %.1f%% ⇒ salto "
                 "%.1f punti (ne servono %.1f)"
                 % (fr_primo * 100, max(peggiori) * 100,
                    distanza * 100, salto * 100))
    if distanza < salto:
        righe.append("⛔ IL SALTO E' TROPPO PICCOLO: i due inquilini stanno ai "
                     "due lati di un capello.")
        righe.append("   ⇒ ⛔ non si certifica una rete su una differenza che "
                     "non si distingue dal rumore (`LEZIONI.md` §1.52).")
        return 1, "salto-troppo-piccolo", righe
    righe.append("⭐ IL GUASTO INNESTATO E' STATO VISTO: %d inquilini su %d non "
                 "vedono la pagina, ⛔ e il PRIMO si'"
                 % (len(no), len(esiti)))
    righe.append("   ⇒ non ce l'hanno fatta: %s"
                 % ", ".join(e["chi"] for e in no))
    righe.append("   ⇒ ⭐ questa maglia SA dare rosso, e la differenza e' "
                 "misurabile")
    return 0, "guasto-visto", righe


# ═══════════════════════════════════════════════════════════════════════════
# LA PRESA — ⛔ un attacco solo, e il browser si accende DENTRO quell'attacco
# ═══════════════════════════════════════════════════════════════════════════
def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def quanti_fotogrammi(testo):
    """Dal registro del cliente: quanti fotogrammi sono ARRIVATI.

    ⛔ `None` quando non e' arrivato niente, e non zero: un flusso vuoto
       decodificato direbbe «schermo nero» su un server che non ha mai avuto
       occasione di mandare niente (`LEZIONI.md` §1.30).
    """
    quanti = None
    for riga in (testo or "").splitlines():
        if "[vid]" in riga and "nessun fotogramma" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return quanti or None


def ffmpeg(c8a, comando):
    return c8a.sh(comando, secondi=240)


def estrai(c8a, flusso, primo, ultimo):
    """Dal flusso H.264 tira fuori il PRIMO e l'ULTIMO fotogramma.

    ⛔ Sono due domande diverse e servono due comandi: `-frames:v 1` prende il
       fotogramma d'apertura (il desktop **prima** del browser), `-update 1`
       riscrive sempre lo stesso file e quindi vince l'ULTIMO decodificato — che
       e' quel che il desktop mostra adesso.
    """
    for f in (primo, ultimo):
        if os.path.exists(f):
            os.unlink(f)
    ffmpeg(c8a, "ffmpeg -hide_banner -loglevel error -i %s -vsync 0 "
                "-frames:v 1 -y %s" % (flusso, primo))
    ffmpeg(c8a, "ffmpeg -hide_banner -loglevel error -i %s -vsync 0 "
                "-update 1 -y %s" % (flusso, ultimo))
    return (primo if os.path.exists(primo) and os.path.getsize(primo) else None,
            ultimo if os.path.exists(ultimo) and os.path.getsize(ultimo) else None)


def cerca_in_tutta_la_ripresa(c8a, flusso, cartella, chi, minima, quanti=240):
    """⭐ SOLO DIAGNOSI — la pagina e' comparsa **in qualche momento**?

    ⛔ Non cambia nessun verdetto, e non puo' farlo: il verdetto e' sull'ultimo
       fotogramma, cioe' su quel che il desktop mostra **adesso**.
    ⚠ Ma serve a nominare il motivo accanto al sintomo: `[M]` 25 agosto 2026, il
      dialogo «Profile Missing» di Firefox compariva a meta' della presa e
      sull'ultimo fotogramma non c'era piu' (`10-f1-testimone.py`, `--tutti`).
      ⇒ *«non ha mai disegnato»* e *«ha disegnato e poi e' sparita»* sono due
      guasti diversi, e chi legge ha diritto di sapere quale dei due e'.
    """
    modello = os.path.join(cartella, "%s-seq-%%03d.png" % chi)
    c8a.sh("rm -f %s" % os.path.join(cartella, "%s-seq-*.png" % chi))
    # ⚠ Un fotogramma al secondo, al massimo `quanti`: la ripresa dura minuti, e
    #   decodificarla tutta costerebbe piu' della prova.
    ffmpeg(c8a, "ffmpeg -hide_banner -loglevel error -i %s -vf fps=1 "
                "-frames:v %d -y %s" % (flusso, quanti, modello))
    migliore = None
    dove = None
    n = 0
    for i in range(1, quanti + 1):
        p = os.path.join(cartella, "%s-seq-%03d.png" % (chi, i))
        if not os.path.exists(p):
            continue
        n += 1
        fr = c8a.frazione_del_colore(p)
        if fr is not None and (migliore is None or fr > migliore):
            migliore = fr
            dove = i
    if not n:
        return "⚠ non sono riuscito a rileggere la ripresa: nessun campione"
    if migliore is None:
        return "⚠ %d campioni rivisti, nessuno leggibile" % n
    if migliore >= minima:
        return ("⛔⛔ LA PAGINA C'ERA e poi e' sparita: al campione %d/%d copriva "
                "il %.1f%% — ⚠ il browser ha disegnato, e qualcosa gliel'ha "
                "tolta di sotto" % (dove, n, migliore * 100))
    return ("⚠ in %d campioni della ripresa la pagina non e' MAI comparsa "
            "(massimo %.1f%%): ⇒ non e' «e' comparsa e sparita»"
            % (n, migliore * 100))


def aspetta_il_palco(registro, chi, c1, segno, scadenza, cliente):
    """⛔ Si aspetta L'EVENTO, non l'orologio — col giudice della nascita di C1.

    Torna `(secondi|None, perche|None)`.

    ⚠ Si sorveglia anche il cliente: se muore per conto suo, aspettare il palco
      fino alla scadenza sarebbe aspettare un morto — si torna subito, e si dice
      **chi** e' morto invece di lasciare un silenzio (`LEZIONI.md` §1.29).
    ⭐ E quando scade, il perche' lo dice **C1**: «CIECA» e «NON-LO-SO» sono due
      cose diverse, e chi legge ha diritto di sapere quale delle due.
    """
    t0 = time.time()
    ultimo = None
    while time.time() < scadenza:
        if cliente.poll() is not None:
            return None, ("il cliente di prova se n'e' andato dopo %.0f s, prima "
                          "che il palco montasse un monitor" % (time.time() - t0))
        testo = leggi(registro)
        fetta = testo[segno:] if testo is not None else ""
        ultimo = c1.leggi_nascita(fetta, chi)
        if c1.monitor_nato(ultimo):
            return time.time() - t0, None
        time.sleep(1.0)
    stato, perche = c1.verdetto_giro(ultimo)
    return None, ("in %.0f s il palco non ha montato nessun monitor per «%s» "
                  "(C1 dice «%s»: %s): ⛔ senza schermo il browser non ha dove "
                  "disegnare, e questo NON e' un rosso di C8b"
                  % (time.time() - t0, chi, stato, perche))


def guarda_un_inquilino(chi, a, c8a, c1, giudice):
    """⭐⭐ IL CUORE — un attacco solo, e dentro ci sta tutto.

    Torna un dizionario:
        {"prima": float|None, "dopo": float|None, "verdetto_prima": str|None,
         "fotogrammi": int|None, "palco_s": float|None, "perche": str}
    """
    esito = {"prima": None, "dopo": None, "verdetto_prima": None,
             "fotogrammi": None, "palco_s": None, "perche": ""}
    flusso = os.path.join(a.lavoro, "%s.264" % chi)
    diario = os.path.join(a.lavoro, "%s-cliente.log" % chi)
    for f in (flusso, diario):
        if os.path.exists(f):
            os.unlink(f)

    testo = leggi(a.registro)
    if testo is None:
        esito["perche"] = ("non riesco a leggere il registro del prodotto (%s): "
                           "⛔ non so quando il palco e' nato" % a.registro)
        return esito
    segno = len(testo)

    resta = resta_del_filo(a.attesa_palco, a.attesa_browser, a.margine_filo)
    # ⛔ Il cliente scrive il flusso SOLO alla fine: si lancia in sottofondo e si
    #    lavora mentre e' attaccato.  ⚠ E l'uscita va in un FILE, non in una
    #    pipe: una pipe piena bloccherebbe il cliente, e un banco appeso non
    #    dice niente a nessuno (`LEZIONI.md` §1.51).
    acceso = False
    with open(diario, "wb") as f:
        cliente = subprocess.Popen(
            ["python3", "-u", a.cliente,
             "--indirizzo", a.indirizzo, "--porta", str(a.porta),
             "--utente", chi, "--parola", a.parola,
             "--video-scrivi", flusso, "--resta", "%.1f" % resta],
            stdout=f, stderr=subprocess.STDOUT)

    try:
        palco, perche = aspetta_il_palco(
            a.registro, chi, c1, segno,
            time.time() + a.attesa_palco, cliente)
        esito["palco_s"] = palco
        if palco is None:
            esito["perche"] = perche
            return esito

        # ⭐ Il respiro: almeno un fotogramma SENZA browser dev'essere partito,
        #   o il «prima» conterrebbe gia' la pagina.
        time.sleep(a.respiro)

        display, err = c8a.apri_il_browser(chi, a)
        if display is None:
            esito["perche"] = "⛔ non ho potuto accendere il browser: %s" % err
            return esito
        acceso = True
        esito["perche"] = "browser acceso su %s" % display
        time.sleep(a.attesa_browser)
    finally:
        if esito["palco_s"] is None or not acceso:
            # ⛔ Qui non c'e' niente da raccogliere — il palco non e' nato, o il
            #    browser non si e' acceso — e restare attaccati fino alla fine
            #    vorrebbe dire pagare tre minuti per un file che non guardero'.
            # ⚠ E si dice: un banco che spende e non spiega e' un banco che
            #   qualcuno spegnera' (§1.3 del documento di fase).
            cliente.terminate()
            try:
                cliente.wait(timeout=30)
            except subprocess.TimeoutExpired:
                cliente.kill()
                cliente.wait(timeout=30)
        else:
            # ⭐ Altrimenti si aspetta che finisca DA SE': e' lui che scrive il
            #   flusso — solo alla fine — e ucciderlo butterebbe via la ripresa.
            try:
                cliente.wait(timeout=resta + 120)
            except subprocess.TimeoutExpired:
                cliente.kill()
                cliente.wait(timeout=30)

    coda = leggi(diario) or ""
    esito["fotogrammi"] = quanti_fotogrammi(coda)
    if esito["fotogrammi"] is None:
        ultima = ""
        for riga in reversed(coda.strip().splitlines()):
            if riga.strip():
                ultima = riga.strip()[:110]
                break
        esito["perche"] = ("nessun fotogramma e' arrivato dal filo ⇒ ⛔ non e' "
                           "«lo schermo era vuoto».  Il cliente dice: %s" % ultima)
        return esito

    primo, ultimo = estrai(c8a, flusso,
                           os.path.join(a.lavoro, "%s-prima.png" % chi),
                           os.path.join(a.lavoro, "%s-dopo.png" % chi))
    if primo is None or ultimo is None:
        esito["perche"] = ("%d fotogrammi sono arrivati ma ffmpeg non ne ha "
                           "fatto un'immagine" % esito["fotogrammi"])
        return esito
    g = giudice.giudica(primo)
    esito["verdetto_prima"] = g["verdetto"] if g else None
    esito["prima"] = c8a.frazione_del_colore(primo)
    esito["dopo"] = c8a.frazione_del_colore(ultimo)
    esito["png_prima"], esito["png_dopo"] = primo, ultimo
    return esito


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE — e si dichiara che cosa copre e che cosa no
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⭐ Fa girare **tutti** i giudizi di questa maglia, sul portatile, senza
    scatola, senza server e senza browser.

    COPRE: ⭐ il giudizio del «prima» (nero ⇒ non e' un rosso · gia' magenta ⇒
    non e' un verde · niente ⇒ «non lo so») · il verdetto sul singolo inquilino ·
    ⭐⭐ **il giunto**, cioe' il codice d'uscita, nei due versi (senza guasto e
    col guasto innestato, `LEZIONI.md` §1.52) · i tetti, che sono soglie e come
    tali si certificano · ⭐ che il metro sia **quello di C8a** e non una copia.
    ⛔ NON COPRE: che il lettore dei pixel sappia riconoscere il colore — quello
    e' certificato in C8a (8 casi su 8) — ne' che il giudice delle immagini
    sappia dire «nero» — quello e' certificato in `10-f1` (12 guasti innestati).
    ⇒ Una certificazione che si dichiara piu' larga di quel che e' vale meno di
      nessuna certificazione.
    """
    print("== certificazione di C8b — «la pagina si vede DAL CLIENTE» ==")

    c8a = prendi_c8a()
    if c8a is None:
        print("⛔ non trovo C8a (11-c8-il-secondo-apre-il-browser.py) accanto a me:")
        print("   ⇒ senza di lei non ho ne' la scena ne' il metro")
        print("   ⇒ non ho potuto guardare")
        return 3
    giudice, dove = trova_il_giudice(c8a)
    if giudice is None:
        print("⛔ non trovo il giudice delle immagini (10-f1-testimone.py)")
        print("   ⇒ non ho potuto guardare")
        return 3
    c1 = prendi_c1()
    if c1 is None:
        print("⛔ non trovo C1 (11-c1-nasce-e-si-vede.py), o non ha piu' il")
        print("   giudice della nascita che mi serve ⇒ non ho potuto guardare")
        return 3

    minima = c8a.FRAZIONE_MINIMA
    print("   il metro viene da C8a: colore %s · tolleranza ±%d · frazione "
          "minima %.2f" % (c8a.COLORE, c8a.TOLLERANZA, minima))
    print("   il giudice delle immagini: %s" % dove)
    print("   il giudice della nascita e il suo tetto: da C1, %.0f s"
          % c1.TETTO_NASCITA)
    print()

    guai = 0
    quanti = 0

    def prova(gruppo, nome, atteso, ottenuto):
        # ⛔ Il conto si tiene QUI e si stampa RILEGGENDOLO: un «N su N» scritto
        #    a mano in fondo e' un numero che resta indietro (`LEZIONI.md` §1.48).
        nonlocal guai, quanti
        quanti += 1
        ok = (atteso == ottenuto)
        if not ok:
            guai += 1
        print("  %s  %-8s %-52s atteso %-14s ottenuto %s"
              % ("OK " if ok else "NO ", gruppo, nome, repr(atteso),
                 repr(ottenuto)))
        return ok

    # ── P1 · il giudizio del PRIMA ──────────────────────────────────────────
    print("  P1 · il desktop PRIMA del browser — ⛔ tre esiti, non due")
    prova("P1", "desktop disegnato, niente pagina ⇒ pulito", "pulito",
          giudica_il_prima("disegnato", 0.001, minima)[0])
    prova("P1", "desktop NERO ⇒ «a monte», ⛔ non un rosso di C8b", "a-monte",
          giudica_il_prima("nero", 0.0, minima)[0])
    prova("P1", "desktop QUASI-NERO ⇒ «a monte»", "a-monte",
          giudica_il_prima("quasi-nero", 0.0, minima)[0])
    prova("P1", "⭐ la pagina c'era GIA' ⇒ non me l'attribuisco", "gia-magenta",
          giudica_il_prima("disegnato", 0.99, minima)[0])
    prova("P1", "⛔ non ho guardato ⇒ «non lo so», non «era nero»", "non-lo-so",
          giudica_il_prima(None, None, minima)[0])
    prova("P1", "⛔ ho un verdetto ma non la frazione ⇒ «non lo so»", "non-lo-so",
          giudica_il_prima("disegnato", None, minima)[0])

    # ⭐ E i due casi che attraversano DAVVERO i pixel, con immagini vere: qui
    #   non si certifica il lettore (e' di C8a), si certifica che l'IMPORTO sia
    #   vivo — ⛔ che il metro usato sia quello di C8a e non una copia sbiadita.
    print("\n  P2 · ⭐ il metro e' DAVVERO quello di C8a (l'importo e' vivo)")
    try:
        import numpy as np
        from PIL import Image
        import tempfile
        lav = tempfile.mkdtemp(prefix="c8bcert-")

        def dipingi(nome, riempi, macchia=None):
            arr = np.zeros((216, 384, 3), dtype="uint8")
            arr[:, :] = riempi
            if macchia is not None:
                arr[80:136, 100:284] = macchia
            p = os.path.join(lav, nome + ".png")
            Image.fromarray(arr).save(p)
            return p

        pagina = dipingi("pagina", c8a.COLORE, (0, 0, 0))
        vuoto = dipingi("vuoto", (58, 62, 70), (200, 200, 200))
        nero = dipingi("nero", (0, 0, 0))
        fr_pagina = c8a.frazione_del_colore(pagina)
        fr_vuoto = c8a.frazione_del_colore(vuoto)
        prova("P2", "la pagina si ritrova col metro importato", True,
              fr_pagina is not None and fr_pagina >= minima)
        prova("P2", "un desktop senza pagina non la ritrova", True,
              fr_vuoto is not None and fr_vuoto < minima)
        prova("P2", "⛔ un file che non c'e' ⇒ None, non zero", None,
              c8a.frazione_del_colore(os.path.join(lav, "manca.png")))
        prova("P2", "il giudice di 10-f1 dice «nero» su uno schermo nero",
              "nero", (giudice.giudica(nero) or {}).get("verdetto"))
        # ⭐ E la catena intera, dal PNG al verdetto dell'inquilino.
        stato, _ = giudica_il_prima(
            (giudice.giudica(vuoto) or {}).get("verdetto"),
            c8a.frazione_del_colore(vuoto), minima)
        prova("P2", "⭐ catena intera: desktop vuoto ⇒ campo pulito", "pulito",
              stato)
        prova("P2", "⭐ catena intera: pulito + pagina ⇒ VISTA", True,
              giudizio_inquilino(stato, fr_pagina, minima)[0])
    except ImportError:
        print("  ⛔ mancano numpy o Pillow: non posso certificare l'importo")
        print("     ⇒ non ho potuto guardare")
        return 3

    # ── P3 · il verdetto su un inquilino ────────────────────────────────────
    print("\n  P3 · il verdetto su UN inquilino")
    prova("P3", "campo pulito, pagina piena ⇒ SI", True,
          giudizio_inquilino("pulito", 0.987, minima)[0])
    prova("P3", "campo pulito, niente pagina ⇒ NO", False,
          giudizio_inquilino("pulito", 0.004, minima)[0])
    prova("P3", "⛔ campo pulito, dopo non guardato ⇒ «non lo so»", None,
          giudizio_inquilino("pulito", None, minima)[0])
    prova("P3", "⛔ desktop nero prima ⇒ «non lo so», non un rosso", None,
          giudizio_inquilino("a-monte", 0.0, minima)[0])
    prova("P3", "⛔ pagina gia' presente prima ⇒ «non lo so», non un verde", None,
          giudizio_inquilino("gia-magenta", 0.99, minima)[0])
    # ⚠ E la soglia si tara nei due versi, come C1 e C8a: appena sopra passa,
    #   appena sotto no — o non e' una soglia, e' un'opinione.
    prova("P3", "appena SOPRA la frazione minima ⇒ SI", True,
          giudizio_inquilino("pulito", minima + 0.001, minima)[0])
    prova("P3", "appena SOTTO la frazione minima ⇒ NO", False,
          giudizio_inquilino("pulito", minima - 0.001, minima)[0])

    def E(chi, visto, dopo):
        return {"chi": chi, "visto": visto, "dopo": dopo, "perche": ""}

    # ⛔⛔ E DA QUI IN POI SI PRETENDE **IL NUMERO E LA RAGIONE**, non il numero.
    #
    # `[M]` 27 agosto 2026, scrivendo questa maglia: smontando la guardia «ha
    # fallito anche il PRIMO» il codice d'uscita restava **1** lo stesso, per
    # un'altra strada — ⛔ e questa certificazione, che guardava solo il numero,
    # diceva **OK su una guardia smontata**.  ⇒ E' §1.44 in un'altra veste: un
    # controllo che non puo' dare rosso ha l'aspetto di uno che passa.
    def giudizio(esiti_, senza_cura_):
        c, m, _ = decidi(esiti_, senza_cura_, minima)
        return (c, m)

    # ── P4 · il giunto, SENZA guasto innestato ──────────────────────────────
    print("\n  P4 · il codice d'uscita, giro normale — ⭐ numero E ragione")
    prova("P4", "tutt'e due vedono ⇒ 0", (0, "tutti-vedono"),
          giudizio([E("u1", True, 0.98), E("u2", True, 0.98)], False))
    prova("P4", "uno non vede ⇒ 1 (rosso)", (1, "rosso"),
          giudizio([E("u1", True, 0.98), E("u2", False, 0.00)], False))
    prova("P4", "⛔ uno non giudicato ⇒ 3, e non e' un verde", (3, "non-giudicato"),
          giudizio([E("u1", True, 0.98), E("u2", None, None)], False))
    prova("P4", "⛔ nessuno giudicato ⇒ 3", (3, "non-giudicato"),
          giudizio([E("u1", None, None), E("u2", None, None)], False))
    prova("P4", "⛔ nessun inquilino affatto ⇒ 3, non 0", (3, "non-giudicato"),
          giudizio([], False))

    # ── P5 · il giunto COL guasto innestato — si legge al contrario ─────────
    print("\n  P5 · ⛔ col guasto innestato: `0` = guasto VISTO (§1.52)")
    prova("P5", "⭐ primo si', secondo no, salto largo ⇒ 0 (visto)",
          (0, "guasto-visto"),
          giudizio([E("u1", True, 0.987), E("u2", False, 0.001)], True))
    prova("P5", "⛔ tutt'e due vedono ⇒ 1 (il guasto non ha morso)",
          (1, "guasto-non-visto"),
          giudizio([E("u1", True, 0.98), E("u2", True, 0.98)], True))
    # ⭐⭐ LA GUARDIA DI §7-bis.12, e si pretende PER NOME: col guasto innestato
    #    un rosso anche sul PRIMO non e' quel guasto — ⛔ e senza la ragione
    #    questo caso passava anche con la guardia smontata.
    prova("P5", "⛔ ha fallito anche il PRIMO ⇒ 1, e per QUELLA ragione",
          (1, "anche-il-primo"),
          giudizio([E("u1", False, 0.0), E("u2", False, 0.0)], True))
    prova("P5", "⛔ nessun giudizio ⇒ 3, e non «non e' stato visto»",
          (3, "nessun-giudizio"),
          giudizio([E("u1", None, None), E("u2", None, None)], True))
    prova("P5", "⛔ il primo non giudicato ⇒ 3, e per QUELLA ragione",
          (3, "primo-non-giudicato"),
          giudizio([E("u1", None, None), E("u2", False, 0.0)], True))
    # ⭐⭐ IL CASO CHE VALE PIU' DI TUTTI — `LEZIONI.md` §1.52: il guasto
    #    innestato non si misura sul COLORE del verdetto, si misura sulla
    #    DIFFERENZA.  Qui i due stanno ai due lati di un capello: il verdetto
    #    sarebbe «visto», ⛔ e non deve bastare.
    prova("P5", "⛔⛔ salto sotto il minimo (0,26 vs 0,24) ⇒ 1, non 0",
          (1, "salto-troppo-piccolo"),
          giudizio([E("u1", True, minima + 0.01), E("u2", False, minima - 0.01)],
                   True))
    prova("P5", "⭐ e appena il salto basta ⇒ 0", (0, "guasto-visto"),
          giudizio([E("u1", True, minima + SALTO_MINIMO),
                    E("u2", False, minima - 0.001)], True))
    prova("P5", "⛔ visto ma senza i numeri ⇒ 3 (non certifico al buio)",
          (3, "senza-numeri"),
          giudizio([E("u1", True, None), E("u2", False, None)], True))

    # ── P6 · i tetti sono soglie, e le soglie si certificano ────────────────
    print("\n  P6 · ⭐ il giudice della NASCITA e' quello di C1, e lo dimostro")
    # `[M]` 27 ago 2026, scatola GNOME curata — la riga vera del testimone A.
    nata = c1.leggi_nascita(
        "cattura  [c8bu1] formato negoziato: 1920x1080\n", "c8bu1")
    prova("P6", "il «formato negoziato» ⇒ il monitor c'e'", True,
          bool(c1.monitor_nato(nata)))
    prova("P6", "e il verdetto di C1 e' «NATA»", "NATA",
          c1.verdetto_giro(nata)[0])
    # ⛔⛔ IL CASO CHE VALE DI PIU': la riga «ZERO MONITOR» da sola NON e' un
    #    monitor — e non e' nemmeno una prova di cecita'.  ⇒ Se questa maglia
    #    la leggesse come l'evento che aspetta, accenderebbe il browser su uno
    #    schermo che non c'e'.
    zero = c1.leggi_nascita(
        "sessione [c8bu1] ⛔ ZERO MONITOR, e la sessione e' viva\n", "c8bu1")
    prova("P6", "⛔ «ZERO MONITOR» da sola NON fa nascere il monitor", False,
          bool(c1.monitor_nato(zero)))
    # ⚠ E l'omonimia: il registro e' comune ai due inquilini.
    altrui = c1.leggi_nascita(
        "cattura  [c8bu2] formato negoziato: 1920x1080\n", "c8bu1")
    prova("P6", "⛔ il palco di un ALTRO inquilino non e' il mio", False,
          bool(c1.monitor_nato(altrui)))
    prova("P6", "⛔ registro muto ⇒ «non lo so», non «cieca»", "NON-LO-SO",
          c1.verdetto_giro(c1.leggi_nascita("", "c8bu1"))[0])
    # ⛔⛔ E LA GUARDIA SULL'IMPORTO, esercitata con una C1 finta a cui manca un
    #    pezzo: ⚠ un controllo che non si e' mai visto scattare non e' un
    #    controllo, e' una speranza (`LEZIONI.md` §1.44).
    import types as _tipi
    prova("P6", "la C1 vera ha tutti i pezzi che mi servono", True,
          c1_ha_quel_che_serve(c1))
    for manca in PEZZI_DI_C1:
        finta = _tipi.SimpleNamespace(**{p: (1 if p == "TETTO_NASCITA"
                                             else (lambda *x: None))
                                         for p in PEZZI_DI_C1 if p != manca})
        prova("P6", "⛔ una C1 senza «%s» viene rifiutata" % manca, False,
              c1_ha_quel_che_serve(finta))
    prova("P6", "⛔ e nessuna C1 affatto viene rifiutata", False,
          c1_ha_quel_che_serve(None))

    print("\n  P7 · i tetti — ⛔ ognuno col SUO valore, `LEZIONI.md` §1.45")
    # ⭐⭐ Il tetto del palco NON e' un numero di questo file: e' quello di C1.
    #    ⛔ Il caso che segue e' l'unico che avrebbe preso il difetto della prima
    #    stesura, che aveva copiato 152 s da C1 poche ore prima che C1 li
    #    abbassasse a 26 (`LEZIONI.md` §1.17).
    prova("P7", "⭐ il tetto del palco lo prendo da C1, non ne ho uno mio", True,
          "RITARDO_PALCO" not in globals())
    prova("P7", "e il predefinito e' esattamente il suo", c1.TETTO_NASCITA,
          tetto_del_palco(c1))
    # ⛔ Il tetto del browser NON e' prestato da un'altra attesa: e' suo, ed e'
    #    almeno quanto C8a si da' per il primo avvio a freddo (`--attesa-scatto`
    #    = 120 s, `LEZIONI.md` §1.45).
    prova("P7", "il tetto del browser regge il primo avvio a freddo (120 s)",
          True, ATTESA_BROWSER >= 120.0)
    prova("P7", "⛔ i due tetti sono DIVERSI: nessuno e' prestato all'altro",
          True, ATTESA_BROWSER != c1.TETTO_NASCITA)
    prova("P7", "il filo resta attaccato piu' della somma dei due", True,
          resta_del_filo(c1.TETTO_NASCITA, ATTESA_BROWSER)
          > c1.TETTO_NASCITA + ATTESA_BROWSER)
    prova("P7", "il conto del filo e' un CALCOLO, non un numero tondo", 176.0,
          resta_del_filo(26.0, 120.0, 30.0))
    prova("P7", "⭐ il respiro c'e', o il «prima» conterrebbe gia' la pagina",
          True, RESPIRO > 0)
    prova("P7", "⛔ il salto minimo e' ben sotto il fenomeno misurato (98,7 %)",
          True, 0.0 < SALTO_MINIMO < 0.5)

    print()
    if guai:
        print("⛔ C8b NON e' certificata: %d casi sbagliati su %d" % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: C8b sa dire verde, rosso e «non lo so» — e col "
          "guasto innestato" % (quanti, quanti))
    print("   ⭐ pretende una DIFFERENZA misurabile, non il colore del verdetto")
    print("⚠ e questa certificazione copre I GIUDIZI E IL GIUNTO, non il lettore")
    print("  dei pixel (certificato in C8a) ne' il giudice delle immagini")
    print("  (certificato in 10-f1) — vedi la dichiarazione in testa a certifica()")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente-base", default="c8bu",
                   help="⛔ diverso da quello di C8a («c8u»): due banchi con gli "
                        "stessi inquilini si falsano in silenzio (§1.26)")
    p.add_argument("--quanti", type=int, default=2,
                   help="DUE, come C8a: la domanda e' la correttezza a piu' "
                        "inquilini, non la capienza")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--pagina", default="/opt/remotix/11-c8-pagina.html")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--lavoro", default="/var/lib/rete11/c8b")
    p.add_argument("--attesa-palco", type=float, default=None,
                   help="quanto si aspetta che il palco monti un monitor. "
                        "⭐ Predefinito: il tetto di C1 (`TETTO_NASCITA`), preso "
                        "da lei e non ricopiato. Scaduto: «non ho potuto "
                        "guardare», ⛔ MAI un rosso")
    p.add_argument("--attesa-browser", type=float, default=ATTESA_BROWSER,
                   help="quanto si da' al browser per disegnare la pagina "
                        "DENTRO la sessione. ⛔ 120 s e non 25: il primo avvio a "
                        "freddo deve farsi il profilo (LEZIONI.md §1.45)")
    p.add_argument("--respiro", type=float, default=RESPIRO,
                   help="⭐ quanto si aspetta, dopo che il palco c'e', prima di "
                        "accendere il browser: serve a far partire almeno un "
                        "fotogramma SENZA la pagina")
    p.add_argument("--margine-filo", type=float, default=MARGINE_FILO,
                   help="quanto il filo resta attaccato oltre la somma dei due "
                        "tetti. ⛔ Il cliente scrive il flusso solo alla fine")
    p.add_argument("--attesa-sgombero", type=float, default=45.0,
                   help="quanto si aspetta che l'inquilino di prima sia sparito "
                        "DAVVERO, prima di far nascere il successivo")
    p.add_argument("--senza-cura", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: non si applica la cura della "
                        "provvista. Il secondo inquilino DEVE dare rosso, e la "
                        "differenza dev'essere misurabile")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: deve creare gli inquilini")
        sys.exit(2)

    # ── quel senza cui non si giudica ──────────────────────────────────────
    c8a = prendi_c8a()
    if c8a is None:
        print("⛔ non trovo C8a (11-c8-il-secondo-apre-il-browser.py) accanto a me")
        print("   ⇒ senza di lei non ho ne' la scena ne' il metro")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    giudice, dove_giudice = trova_il_giudice(c8a)
    if giudice is None:
        print("⛔ non trovo il giudice delle immagini (10-f1-testimone.py)")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    c1 = prendi_c1()
    if c1 is None:
        print("⛔ non trovo C1 (11-c1-nasce-e-si-vede.py), o non ha piu' il "
              "giudice della nascita che mi serve")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    # ⛔ Il tetto si riempie ADESSO, da C1: `argparse` non puo' farlo, perche'
    #    quando costruisce i predefiniti C1 non e' ancora stata caricata.
    if a.attesa_palco is None:
        a.attesa_palco = tetto_del_palco(c1)
    for nome, perc in (("il cliente di prova", a.cliente),
                       ("la pagina bersaglio", a.pagina)):
        if not os.path.exists(perc):
            print("⛔ non trovo %s: %s" % (nome, perc))
            print("   ⇒ non ho potuto guardare")
            sys.exit(3)
    if c8a.sh("command -v %s" % a.browser).returncode != 0:
        print("⛔ nella scatola non c'e' %s" % a.browser)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if c8a.sh("command -v ffmpeg").returncode != 0:
        print("⛔ nella scatola non c'e' ffmpeg: i fotogrammi non diventano "
              "un'immagine")
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if leggi(a.registro) is None:
        print("⛔ non riesco a leggere il registro del prodotto: %s" % a.registro)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)
    minima = c8a.FRAZIONE_MINIMA
    dove = c8a.prepara_lo_scheletro()
    # ⛔ Si sgombra `/tmp/mozilla` per TUTT'E DUE le famiglie di inquilini: se
    #    restasse quello di C8a, il PRIMO di questa maglia fallirebbe come il
    #    secondo — cioe' un rosso per la ragione sbagliata.
    # ⭐ E si chiama la funzione di C8a due volte invece di riscriverne una: la
    #   sua regola («non si tocca il `/tmp/mozilla` di chi non e' un inquilino di
    #   questa rete») resta scritta in un posto solo.
    resti = [c8a.sgombra_il_posto_condiviso(b)
             for b in (a.utente_base, "c8u")]

    resta = resta_del_filo(a.attesa_palco, a.attesa_browser, a.margine_filo)
    print("== C8b — e la stessa pagina si vede DAL CLIENTE ==")
    print("   %d inquilini · porta %d · pagina %s"
          % (a.quanti, a.porta, os.path.basename(a.pagina)))
    print("   terreno: /etc/skel/.cache -> %s  (la configurazione della "
          "macchina vera)" % (dove or "⛔ NON SONO RIUSCITO A METTERLO"))
    print("   cura della provvista: %s"
          % ("⛔ NON APPLICATA (guasto innestato: il secondo DEVE dare rosso)"
             if a.senza_cura else "applicata, come src/provisiona.sh"))
    print("   metro (da C8a): colore %s ±%d, almeno il %.0f%% dello schermo"
          % (c8a.COLORE, c8a.TOLLERANZA, minima * 100))
    print("   giudice delle immagini: %s" % dove_giudice)
    print("   giudice della nascita: C1 (e il tetto del palco e' il suo)")
    print("   tetti: palco %.0f s · browser %.0f s · respiro %.0f s ⇒ il filo "
          "resta attaccato %.0f s per inquilino"
          % (a.attesa_palco, a.attesa_browser, a.respiro, resta))
    for r in resti:
        if r:
            print("   %s" % r)
    if not dove:
        print("⛔ non sono riuscito a preparare lo scheletro: il terreno non regge")
        sys.exit(2)
    print()

    esiti = []
    for n in range(1, a.quanti + 1):
        chi = "%s%d" % (a.utente_base, n)
        fatto, perche = c8a.crea(chi, a.parola)
        if not fatto:
            print("  %-7s  ?   non sono riuscito a crearlo: %s" % (chi, perche))
            esiti.append({"chi": chi, "visto": None, "dopo": None,
                          "perche": "non creato"})
            continue
        if not a.senza_cura:
            c8a.applica_la_cura(chi)
        scrive = c8a.sa_scrivere_nella_cache(chi)

        r = guarda_un_inquilino(chi, a, c8a, c1, giudice)
        stato, detto = giudica_il_prima(r["verdetto_prima"], r["prima"], minima)
        if r["prima"] is None and r["verdetto_prima"] is None:
            detto = r["perche"] or detto
        visto, motivo = giudizio_inquilino(stato, r["dopo"], minima)

        print("  %-7s  %-3s  %s"
              % (chi, "SI" if visto else ("NO" if visto is False else "?"),
                 motivo))
        print("           prima: %s" % detto)
        print("           filo: %s fotogrammi · palco a %s · sa scrivere in "
              "~/.cache/mozilla: %s"
              % ("non lo so" if r["fotogrammi"] is None else r["fotogrammi"],
                 "non lo so" if r["palco_s"] is None else "%.0f s" % r["palco_s"],
                 "si'" if scrive else "⛔ NO"))
        # ⭐ Il motivo accanto al sintomo: «non si vede» nasconde due guasti
        #   diversi, e la ripresa sa dire quale.
        if visto is False and os.path.exists(
                os.path.join(a.lavoro, "%s.264" % chi)):
            print("           %s" % cerca_in_tutta_la_ripresa(
                c8a, os.path.join(a.lavoro, "%s.264" % chi), a.lavoro, chi,
                minima))

        esiti.append({"chi": chi, "visto": visto, "dopo": r["dopo"],
                      "prima": r["prima"],
                      "perche": motivo if visto is not None else detto})
        c8a.sh("pkill -KILL -u %s 2>/dev/null; loginctl terminate-user %s "
               "2>/dev/null" % (chi, chi))
        # ⛔ E si aspetta che se ne sia andato DAVVERO: `[M]` in C1, senza questa
        #    attesa i giri si alternavano «non lo so» / rosso, perche' il giro
        #    dopo partiva su un campo ancora occupato.
        scadenza = time.time() + a.attesa_sgombero
        libero = False
        while time.time() < scadenza:
            viva = subprocess.run(["loginctl", "show-user", chi],
                                  capture_output=True).returncode == 0
            proc = subprocess.run(["pgrep", "-u", chi],
                                  capture_output=True).returncode == 0
            if not viva and not proc:
                libero = True
                break
            time.sleep(0.5)
        if not libero:
            print("           ⚠ «%s» non se n'e' andato in %.0f s: il prossimo "
                  "NON parte da un campo libero" % (chi, a.attesa_sgombero))

    # ⛔⛔ E ADESSO SI SGOMBRA IL PROPRIO — «chi apre, chiude» (`LEZIONI.md`
    #    §9-ter), e qui non e' buona educazione: e' correttezza.
    #    ⚠ `/tmp/mozilla` resta di `c8bu1`, modo 0700.  ⭐ C8a lo toglie solo se
    #      e' di un «c8u*» — il suo prefisso — ⇒ se questa maglia girasse PRIMA
    #      di lei, il PRIMO inquilino di C8a fallirebbe come il secondo, e C8a
    #      direbbe «ha fallito anche il PRIMO»: ⛔ un rosso lasciato in eredita'
    #      da un banco a un altro, che e' §1.26 in piccolo.
    finale = c8a.sgombra_il_posto_condiviso(a.utente_base)
    if finale:
        print("  %s" % finale)

    print()
    codice, motivo, righe = decidi(esiti, a.senza_cura, minima)
    for r in righe:
        print(r)
    # ⭐ Il motivo si stampa accanto al numero: un esito senza la ragione che lo
    #   ha prodotto e' un numero che il giro dopo nessuno sa rileggere.
    print("  (esito %d · motivo «%s»)" % (codice, motivo))
    return codice


if __name__ == "__main__":
    sys.exit(main())
