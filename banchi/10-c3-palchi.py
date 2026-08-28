#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-c3-palchi — ⛔ L'UNDICESIMO E' AMMESSO E NON VEDE UN PIXEL: il rosso e il verde.

    porta 8230 · utenti `provadec4` (1103), `provadec5` (1104), `provadec6` (1105)
    albero `/media/REMOTIX/src/10c3-src` · lavoro `/media/REMOTIX/tmp/10c3`
    unita' `remotix-8230` · lucchetto GPU `10-c3`

    python3 banchi/10-c3-palchi.py --certifica    ⭐ senza rete e senza macchina
    bash    banchi/10-c3-lancia.sh                il giro vero (sano + guasti)

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ IL DIFETTO — P3 di `fasi/10-…md` §8.2, rilievo R10-A1
═══════════════════════════════════════════════════════════════════════════════

I due tetti da 16 si liberano su **eventi diversi**:

  · il posto di `attaccate[]` (`rcp.c`) si libera **al distacco**, per sei strade;
  · ⛔ il **figlio** no — invariante **I4** (`figlio.h:69`): muore solo per
    logout esplicito o per abbandono a **60 minuti** senza input.

⇒ ⛔⛔ **La tabella dei figli puo' essere piena mentre quella dei posti e' vuota.**

**La scena vera**: dieci inquilini entrano la mattina, lavorano, **chiudono il
browser**.  I dieci palchi restano vivi fino a un'ora.  L'undicesimo supera PAM,
il posto **e' libero** — e `figli_assicura()` torna `false`.  Prima del 25 agosto
2026 il prodotto scriveva **una riga di registro** e ⛔ **sul filo non usciva
NIENTE**: ne' `0x0E`, ne' `0x06`.  Pagina nera, nessuna spiegazione, e nessun
tempo dopo il quale migliora.

⭐ **Il modello di come si fa bene era gia' nel codice, due funzioni piu' in
   la'**: `posto_prendi()` distingue «occupato» da «niente piu' posti» e per il
   secondo manda `SESSIONE_NON_SERVIBILE 0x0E` **col dettaglio nel corpo** —
   la cura di **R9.3**, vista scattare 10 su 10 in §6.4.

═══════════════════════════════════════════════════════════════════════════════
⛔⭐⭐ LA SCENA CHE QUESTO BANCO COSTRUISCE, e perche' e' proprio QUELLA
═══════════════════════════════════════════════════════════════════════════════

L'albero e' compilato col tetto a **2** (`10-c3-terreno.sh`, `TETTO=2`).  Poi:

  1. **A** (`provadec4`) entra e **resta attaccato** per tutto il giro;
  2. **B** (`provadec5`) entra, sta un po', e **se ne va pulito**
     ⇒ ⭐ il suo **posto torna libero** e il suo **palco resta vivo** (I4);
  3. si aspetta la condizione che e' TUTTO il difetto:
     ⛔ **posti occupati = 1 su 2** (ce n'e' uno libero) **e figli = 2 su 2**;
  4. **C** (`provadec6`) bussa.

⇒ Se il prodotto contasse solo i posti direbbe *«c'e' posto»* — e infatti
  `posto_prendi()` glielo darebbe.  ⛔ Il palco no.

⚠ **Due non e' dieci e non e' sedici**: qui si misura il COMPORTAMENTO al
  riempimento, non il numero.  Il numero della macchina e' un'altra misura di
  questa fase (§6.12: undici desktop veri, soffitto non trovato).

═══════════════════════════════════════════════════════════════════════════════
⛔ LE SETTE DOMANDE, e per ciascuna il predicato che sa dare rosso
═══════════════════════════════════════════════════════════════════════════════

 0. ⛔ **la sollecitazione e' ARRIVATA?** (`p_sollecitazione`) — `LEZIONI.md`
    §1.30: se al momento di bussare i figli non erano pieni **o** i posti non
    erano liberi, la scena non e' quella e il banco **si rifiuta di giudicare**;
 1. **il no esce sul filo?** (`p_congedo_sul_filo`) — letto ⛔ **DOVE ARRIVA**,
    cioe' nel cliente, non nel registro del server.  Tre esiti distinti:
    niente · un motivo sbagliato · `0x0E`;
 2. **il corpo porta il dettaglio?** (`p_dettaglio_nel_corpo`) — `RCP.md` §8.2
    lo impone per `0x0E`, e si legge dalla traccia §11.1 del cliente;
 3. ⛔ **nessuno resta davanti a una pagina nera** (`p_niente_pagina_nera`) — il
    sintomo vero del difetto: `AMMESSO`, `SESSIONE`, **zero fotogrammi** e
    niente sul filo per 60 s;
 4. ⛔ **il desktop NON si accende a chi verra' respinto** (`p_niente_desktop`)
    — §8.1 **D6**.  `[M]` §6.4: un utente **mai ammesso** aveva **42 processi e
    un `gnome-shell`**.  *«Rifiutare dopo aver acceso un desktop non e'
    rifiutare: e' fare login e poi cacciare.»*;
 5. **che frase mostra la PAGINA** (`p_frase_della_pagina`) — da un Firefox
    VERO, che gira sul **portatile** per non aggiungere carico alla GPU;
 6. **chi c'era gia' non se ne accorge** (`p_chi_c_era_resta`) — invariante
    **I1**: A dev'essere ancora attaccato e ricevere fotogrammi;
 7. ⭐ **i `#define` si seguono** (`p_define_seguono`) — letti **dopo il
    preprocessore**, non nei sorgenti: `10-c3-terreno.sh definisci`.

═══════════════════════════════════════════════════════════════════════════════
⛔ I GUASTI — un banco non e' finito finche' non lo si e' visto dare ROSSO
═══════════════════════════════════════════════════════════════════════════════

Sul campo (`10-c3-lancia.sh`, e li' si vedono girare):

  · `GUASTO=congedo-muto`     ⇒ 1, 2 e 3 devono diventare ROSSI
  · `GUASTO=figli-slegati`    ⇒ 4 e 7 devono diventare ROSSI
  · `GUASTO=palchi-otto`      ⇒ 7 rosso
  · `GUASTO=presenti-slegati` ⇒ 7 rosso

In `--certifica`, senza macchina: le tarature del metro e i guasti innestati
nelle **letture** — perche' un predicato che non sa leggere il rosso non e' un
predicato, e' una speranza.

═══════════════════════════════════════════════════════════════════════════════
⚠ QUEL CHE QUESTO BANCO **NON** MISURA, dichiarato prima
═══════════════════════════════════════════════════════════════════════════════

 · ⚠ **Non misura il numero**: il tetto e' 2 per costruzione.
 · ⚠ **Non misura `BUDGET_PIENO 0x06`**: il prodotto non lo emette, ed e' del
   giro del budget.  Qui il limite e' **amministrativo** — una tabella piena di
   palchi che nessuno sta guardando — e il motivo giusto e' `0x0E`.
 · ⚠ **I1 e' misurata in AGGREGATO** (A e' ancora attaccato, e ha ricevuto
   fotogrammi), non a finestre con il ponte fra i due orologi: quella misura
   l'ha gia' fatta `10-b93-pieno.py` §6.4, ed e' sua.
 · ⚠ **Non misura la rete**: nessun `netem`.
"""
import argparse
import importlib.util
import shlex
import json
import os
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'AMBIENTE SI PONE **PRIMA** DI IMPORTARE `10-b93-pieno.py`
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Quel modulo legge porta, albero, lavoro e unita' **all'import**, dai suoi
#    valori predefiniti (porta 8030, albero `10a8-src`).  ⇒ Importarlo senza
#    aver posto l'ambiente vorrebbe dire guidare **il banco di un altro
#    agente**: la rottura d'isolamento peggiore che ci sia, e per giunta muta.
# ⭐ E si riusa invece di riscrivere (`FASE10-GIRO3` §3): da li' vengono la
#    catena di root, il lettore del canale §11.1, la fotografia del respinto e
#    il Firefox vero.  ⚠ `RESPINTO` e `DENTRO` di quel modulo sono **gia' i
#    miei tre utenti**: il banco della tabella piena e questo hanno lo stesso
#    terreno umano, e porte e alberi diversi.
os.environ.setdefault("PORTA", "8230")
os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10c3")
os.environ.setdefault("ALBERO", "/media/REMOTIX/src/10c3-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10c3-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10c3")
os.environ.setdefault("UNITA", "remotix-8230")
os.environ.setdefault("PAROLA_UTENTE", "dec-pieno-2026")
# ⛔⭐ IL NOME CON CUI IL LUCCHETTO DEV'ESSERE MIO — 25 agosto 2026, quinto giro.
#
#     Era scritto a mano («10-c3») dentro il controllo del terreno, e la
#     GUARDIA E' GIUSTA: due carichi di GPU insieme si falsano in silenzio.
#     ⚠ Ma un incarico diverso che rifa' girare QUESTO banco sull'albero cucito
#     tiene il lucchetto col PROPRIO nome, e il controllo gli darebbe rosso su
#     una macchina perfettamente sua.  ⛔ La cura non e' spegnere la guardia:
#     e' dirle **di chi** dev'essere, come fanno gia' `10-b96` e `10-c1` con
#     `IO_SONO`.  ⇒ Chi non dichiara niente resta «10-c3», e nulla cambia.
IO_SONO = os.environ.setdefault("IO_SONO", "10-c3")


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔⭐ DOVE STANNO I BANCHI DELLA FASE 10 — e non e' sempre accanto a questo file.
#
#     Il terzo giro della fase 10 si lavora in un **git worktree per agente**,
#     e i banchi `10-b*` della fase **non sono nel ramo**: stanno nell'albero
#     principale, non versionati.  ⇒ Un `os.path.join(QUI, "10-b93-pieno.py")`
#     nudo dice *«non esiste»* dentro il worktree e *«esiste»* fuori, cioe' il
#     banco funziona o no **a seconda di dove lo si lancia**.
# ⚠ Da cui questo: si guarda accanto, poi nell'albero principale, e ⛔ si
#   **DICHIARA quale dei due si e' preso** — perche' «l'ho trovato» e «l'ho
#   trovato QUI» sono due fatti diversi, e il secondo e' quello che serve a chi
#   legge il rapporto.
ALTRI_BANCHI = os.environ.get("ALTRI_BANCHI",
                              "/home/nicfio/Documenti/REMOTIX/banchi")


def _trova(nome):
    accanto = os.path.join(QUI, nome)
    if os.path.exists(accanto):
        return accanto
    altrove = os.path.join(ALTRI_BANCHI, nome)
    if os.path.exists(altrove):
        _inf("⚠ «%s» non e' accanto a me: lo prendo da %s" % (nome, ALTRI_BANCHI))
        return altrove
    raise FileNotFoundError("«%s» non c'e' ne' in %s ne' in %s"
                            % (nome, QUI, ALTRI_BANCHI))


VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)

# ⛔ I tre esiti, e sono TRE.  `None` non e' `False`: «non ho potuto misurare»
#    non e' «non e' successo niente» (`FASE10-PREAMBOLO` regola 5).
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)

MOTIVO_GIUSTO = 0x0E
TETTO_ATTESO = int(os.environ.get("TETTO", "2"))
A_UTENTE, A_UID = "provadec4", 1103
B_UTENTE, B_UID = "provadec5", 1104
C_UTENTE, C_UID = "provadec6", 1105


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL METRO — leggere il CLIENTE, che e' il capo del filo dove il no arriva
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Perche' il cliente e non il registro del server: §6.4 ha pagato questa
#    lezione due volte.  *«armate 10, spedite 0»* era un rilievo preso leggendo
#    **dove la capsula parte** invece che **dove arriva**, e §6.8 l'ha
#    RITIRATO col browser vero.  ⇒ Il no si legge dove l'utente lo riceve.
#
# ⚠ E ogni campo che non si e' letto vale `None`, non zero.
RE_CONGEDO = re.compile(r"CONGEDO invece di \w+: motivo (0x[0-9a-fA-F]+)")
RE_RESPINTO = re.compile(r"RESPINTO: motivo (0x[0-9a-fA-F]+)")
RE_AMMESSO = re.compile(r"AMMESSO dopo (\d+) ms")
RE_VID = re.compile(r"\[vid\]\s+(\d+) fotogrammi \((\d+) chiavi\)")
RE_VID_ZERO = re.compile(r"nessun fotogramma preso dal filo")
RE_RESTA = re.compile(r"ancora attaccato dopo ([0-9.]+) s")
RE_SESSIONE = re.compile(r"SESSIONE: stato=")


def leggi_cliente(testo):
    """Dal fiato del cliente ai FATTI.  ⛔ `None` = non l'ho letto.

    Torna un dizionario:
      `congedo`   il motivo del `CONGEDO` arrivato, o `None` se non ne e'
                  arrivato nessuno **oppure** se il fiato non si e' letto —
                  e i due casi si distinguono con `letto`;
      `respinto`  il motivo di un `RESPINTO` (parola sbagliata, ban): ⛔ se
                  c'e', la prova NON ha morso e non si giudica niente;
      `ammesso_ms` quanti ms ci ha messo l'`AMMESSO`, o `None`;
      `sessione`  se il `SESSIONE` e' arrivato;
      `fotogrammi` quanti ne ha presi DAL FILO (0 e' un numero, `None` no);
      `resta_s`   per quanti secondi e' rimasto attaccato senza cadere.
    """
    d = {"letto": False, "congedo": None, "respinto": None, "ammesso_ms": None,
         "sessione": False, "fotogrammi": None, "resta_s": None}
    if not testo or not testo.strip():
        return d
    d["letto"] = True
    m = RE_CONGEDO.search(testo)
    if m:
        d["congedo"] = int(m.group(1), 16)
    m = RE_RESPINTO.search(testo)
    if m:
        d["respinto"] = int(m.group(1), 16)
    m = RE_AMMESSO.search(testo)
    if m:
        d["ammesso_ms"] = int(m.group(1))
    d["sessione"] = bool(RE_SESSIONE.search(testo))
    m = RE_VID.search(testo)
    if m:
        d["fotogrammi"] = int(m.group(1))
    elif RE_VID_ZERO.search(testo):
        # ⭐ E QUESTO E' UNO ZERO VERO, non un «non ho letto»: il cliente lo
        #    dichiara con una riga sua, e la riga c'e' solo se `--video-scrivi`
        #    era acceso.
        d["fotogrammi"] = 0
    m = RE_RESTA.search(testo)
    if m:
        d["resta_s"] = float(m.group(1))
    return d


# ═══════════════════════════════════════════════════════════════════════════
# I PREDICATI
# ═══════════════════════════════════════════════════════════════════════════

def p_sollecitazione(scena):
    """⛔ LA SOLLECITAZIONE E' ARRIVATA? — `LEZIONI.md` §1.30.

    La scena di P3 e' **una sola**: figli pieni **e** almeno un posto libero.
    Se non era quella, tutto il resto misura un'altra cosa, e un giudizio che
    sembra un risultato e' peggio di un buco dichiarato.
    """
    figli, occupati, tetto = scena.get("figli"), scena.get("occupati"), scena.get("tetto")
    if figli is None or occupati is None or tetto is None:
        return _muto("non ho letto la scena (figli=%s occupati=%s tetto=%s)"
                     % (figli, occupati, tetto))
    if figli < tetto:
        return _no("⛔ i palchi NON erano pieni al momento di bussare (%d su %d): "
                   "la scena di P3 non c'e'" % (figli, tetto))
    if occupati >= tetto:
        return _no("⛔ i posti erano PIENI anche loro (%d su %d): cosi' si misura "
                   "la tabella piena di §6.4, non P3 — a rifiutare sarebbe "
                   "`posto_prendi()`, non il palco" % (occupati, tetto))
    return _si("⭐ la scena c'e': palchi %d su %d (PIENI) e posti %d su %d "
               "(ce n'e' uno LIBERO) — e' esattamente P3"
               % (figli, tetto, occupati, tetto))


def p_congedo_sul_filo(c):
    """⛔ IL NO ESCE SUL FILO, E CON IL MOTIVO GIUSTO — letto nel CLIENTE."""
    if not c.get("letto"):
        return _muto("il cliente non ha detto niente: non ho misurato")
    if c.get("respinto") is not None:
        return _muto("⛔ il cliente e' stato RESPINTO (%#04x): parola sbagliata o "
                     "indirizzo bannato ⇒ la prova NON ha morso, e questo non e' "
                     "«respinto correttamente»" % c["respinto"])
    if c.get("congedo") is None:
        return _no("⛔⛔ SUL FILO NON E' USCITO NIENTE: il cliente non ha ricevuto "
                   "nessun CONGEDO.  E' il difetto P3 — pagina nera senza "
                   "spiegazione e senza nessun tempo dopo il quale migliora")
    if c["congedo"] != MOTIVO_GIUSTO:
        return _no("⛔ e' arrivato un congedo, ma col motivo %#04x invece di "
                   "%#04x: un motivo sbagliato racconta all'utente un fatto che "
                   "non e' il suo" % (c["congedo"], MOTIVO_GIUSTO))
    return _si("⭐ CONGEDO %#04x SESSIONE_NON_SERVIBILE, letto dove ARRIVA"
               % c["congedo"])


def p_dettaglio_nel_corpo(traccia):
    """§8.2: `0x0E` DEVE portare il dettaglio nel corpo.

    ⚠ `RCP.md` riga 2305 e' esplicita sul mestiere del dettaglio: **non si
      mostra all'utente**, e' per chi diagnostica.  ⇒ Qui si chiede che ci sia e
      che nomini il fatto, non che sia una frase da leggere.
    """
    if traccia is None:
        return _muto("non ho letto la traccia §11.1 del cliente")
    if traccia.get("motivo") is None:
        return _muto("nella traccia non c'e' nessun CONGEDO da cui leggere il "
                     "corpo: %s" % traccia.get("esito", "senza spiegazione"))
    det = (traccia.get("dettaglio") or "").strip()
    if not det:
        return _no("⛔ il CONGEDO %#04x arriva col corpo VUOTO: §8.2 vuole il "
                   "dettaglio, e chi diagnostica resta senza niente"
                   % traccia["motivo"])
    if "palch" not in det.lower() and "palco" not in det.lower():
        return _no("⛔ il dettaglio non nomina il fatto (i palchi): «%s»" % det)
    return _si("il corpo porta: «%s»" % det)


def p_niente_pagina_nera(c):
    """⛔⛔ IL SINTOMO VERO — e si misura per quel che l'utente VEDE.

    «Entra e non vede un pixel» sono tre fatti insieme: `AMMESSO` arrivato,
    `SESSIONE` arrivata, e **zero fotogrammi** per tutto il tempo.
    """
    if not c.get("letto"):
        return _muto("il cliente non ha detto niente: non ho misurato")
    if c.get("respinto") is not None:
        return _muto("il cliente e' stato RESPINTO: la prova non ha morso")
    if c.get("ammesso_ms") is None:
        return _si("⭐ l'AMMESSO non e' mai arrivato: nessuna pagina nera, il no "
                   "e' stato detto prima")
    if c.get("fotogrammi") is None:
        return _muto("⚠ e' entrato, ma non ho letto quanti fotogrammi ha preso: "
                     "senza quel numero non so dire se ha visto qualcosa")
    if c["fotogrammi"] == 0:
        return _no("⛔⛔ PAGINA NERA: AMMESSO dopo %d ms, SESSIONE %s, e **zero "
                   "fotogrammi** in %s s.  E' il difetto P3 alla lettera"
                   % (c["ammesso_ms"], "arrivata" if c["sessione"] else "NO",
                      c.get("resta_s")))
    return _no("⛔ e' entrato e ha visto %d fotogrammi: non e' la scena di P3 — "
               "il palco c'era" % c["fotogrammi"])


def p_niente_desktop(scatto):
    """⛔ IL DESKTOP NON SI ACCENDE A CHI VERRA' RESPINTO — §8.1 D6.

    `[M]` §6.4 punto 6: a fine giro `provadec6`, **mai ammesso**, aveva **42
    processi e 1 `gnome-shell`** — cioe' autenticato si', figlio nato, sessione
    grafica accesa.  ⇒ *«Rifiutare dopo aver acceso un desktop non e'
    rifiutare: e' fare login e poi cacciare.»*
    """
    if not scatto or scatto.get("gnome_respinto") is None:
        return _muto("non ho contato i processi del respinto")
    g = scatto["gnome_respinto"]
    pr = scatto.get("proc_respinto")
    if g > 0:
        return _no("⛔⛔ il respinto ha %d `gnome-shell` e %s processi: gli e' "
                   "stato acceso un desktop che non vedra' mai" % (g, pr))
    return _si("⭐ il respinto ha 0 `gnome-shell` (processi: %s): nessun desktop "
               "acceso per niente" % pr)


def p_frase_della_pagina(pagina, tabella):
    """⛔ CHE FRASE LEGGE L'UTENTE — da un Firefox VERO, non dedotta.

    ⚠ E la frase di `0x0E` **e' generica per una ragione**: `0x0E` copre gia'
      tre casi in `rcp.c`, e precisarla per uno la renderebbe **falsa** per gli
      altri due (§6.4).  ⇒ Qui il predicato chiede che ci sia, che non MENTA, e
      che sia costruita **da quel motivo**; il giudizio sulla frase e' del
      regista, e sta nel rapporto.
    """
    if not pagina or pagina.get("frase") is None:
        return _muto("la pagina non e' stata guardata: %s"
                     % (pagina or {}).get("perche", "senza spiegazione"))
    frase = (pagina["frase"] or "").strip()
    if not frase:
        return _no("⛔ la pagina non mostra NESSUNA frase")
    for bugia in ("gia' collegato", "già collegato", "altro client",
                  "sessione attiva altrove", "altro dispositivo"):
        if bugia in frase.lower():
            return _no("⛔⛔ LA PAGINA MENTE: «%s» a un utente che non ha nessuna "
                       "sessione da nessuna parte" % frase)
    attesa = (tabella or {}).get("0x0e")
    if attesa is not None and attesa.strip() and attesa.strip() not in frase:
        return _no("⛔ la frase mostrata («%s») non e' quella che la tabella "
                   "MOTIVO del file servito lega a 0x0E («%s»): la pagina l'ha "
                   "costruita da un altro motivo" % (frase, attesa))
    return _si("la pagina mostra: «%s»%s"
               % (frase, "" if attesa is None else
                  "  ⭐ ed e' la voce 0x0E del file servito"))


def p_chi_c_era_resta(a):
    """⛔ CHI C'ERA GIA' NON SE NE ACCORGE — invariante I1.

    ⚠ In aggregato: A dev'essere **ancora attaccato** alla fine e aver ricevuto
      fotogrammi.  La misura a finestre, col ponte fra i due orologi, e' di
      `10-b93-pieno.py`: non si ricopia.
    """
    if not a.get("letto"):
        return _muto("il cliente di dentro non ha detto niente")
    if a.get("congedo") is not None:
        return _no("⛔⛔ CHI ERA DENTRO E' STATO CONGEDATO (%#04x) mentre un "
                   "altro bussava: I1 dice «mai staccare», e §8.2 dice «chi "
                   "viene rifiutato e' chi arriva, non chi c'era»" % a["congedo"])
    if a.get("resta_s") is None:
        return _no("⛔ chi era dentro NON e' rimasto attaccato fino alla fine")
    if a.get("fotogrammi") is None:
        return _muto("⚠ e' rimasto attaccato %s s, ma non ho letto i suoi "
                     "fotogrammi" % a["resta_s"])
    if a["fotogrammi"] <= 0:
        return _no("⛔ chi era dentro e' rimasto attaccato %s s e ha ricevuto "
                   "ZERO fotogrammi" % a["resta_s"])
    return _si("⭐ chi era dentro e' rimasto attaccato %s s e ha ricevuto %d "
               "fotogrammi (%.1f/s)"
               % (a["resta_s"], a["fotogrammi"], a["fotogrammi"] / a["resta_s"]))


def p_define_seguono(righe, tetto):
    """⭐ I `#define` SI SEGUONO — e si legge **dopo il preprocessore**.

    ⛔ Guardare i sorgenti risponde alla domanda sbagliata: dice come sono
       SCRITTI, non che numero il compilatore ha visto.  ⚠ E' l'errore che il
       commento di `figlio.c` faceva da mesi — dichiarava un legame, e il
       legame non c'era.  `[M]` §6.4 l'ha provato: `MAX_ATTACCATE=2` e
       `MAX_FIGLI` rimasto **16**.

    `righe` viene da `10-c3-terreno.sh definisci`, e sono cinque:
    quattro che DEVONO valere `tetto` e ⭐ una — `aiutante.c` — che deve restare
    **16**, perche' e' un'altra grandezza.
    """
    if not righe:
        return _muto("non ho letto la misura degli array dopo il preprocessore")
    deve_seguire = {"rcp.c": "attaccate", "figlio.c": "v", "main.c": "presenti",
                    "webtransport.c": "palchi"}
    visti, guai = {}, []
    # ⛔ La misura si cerca in TUTTA la coda della riga, non nella quarta
    #    parola: `struct figlio v[2]` ha degli spazi dentro, e uno `split()`
    #    la spezzerebbe.  ⚠ Costato un rosso in `--certifica` il 25 ago 2026 —
    #    ⭐ ed e' il punto: e' stato il caso SANO a dirlo, non i guasti.
    for r in righe:
        m = re.match(r"^DEFINE\s+(\S+)\s+(\S+)\s+(.*)$", r.strip())
        if not m:
            continue
        n = re.search(r"\[(\d+)\]\s*$", m.group(3).strip())
        visti[m.group(1)] = int(n.group(1)) if n else None
    for f in list(deve_seguire) + ["aiutante.c"]:
        if f not in visti:
            return _muto("«%s» non e' stato letto: %s" % (f, visti))
        if visti[f] is None:
            return _muto("«%s» non ha dato un numero: %s" % (f, visti))
    for f in deve_seguire:
        if visti[f] != tetto:
            guai.append("%s = %d invece di %d" % (f, visti[f], tetto))
    if visti["aiutante.c"] != 16:
        guai.append("⛔ aiutante.c = %d: doveva restare 16, e' un'ALTRA "
                    "grandezza (le autenticazioni in volo)" % visti["aiutante.c"])
    if guai:
        return _no("⛔ i numeri NON si seguono: " + " · ".join(guai)
                   + "   (letti: %s)" % visti)
    return _si("⭐ il tetto e' UNO: %s tutti a %d, e aiutante.c resta 16 — "
               "un'altra grandezza, e non lo segue apposta"
               % (", ".join(deve_seguire), tetto))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA TARATURA DEL METRO — si tara PRIMA (`LEZIONI.md` §1.33)
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ E gira ANCHE nel giro vero, non solo in `--certifica`: un metro tarato in
#    laboratorio e non sul campo e' un metro di cui non si sa niente il giorno
#    in cui il campo cambia.
FIATO_CONGEDO = """   CIAO mandato
   ECCOMI: versione 1
   ⛔ RuntimeError: CONGEDO invece di AMMESSO: motivo 0x0e = SESSIONE_NON_SERVIBILE
"""
FIATO_NERO = """   ECCOMI: versione 1
   AMMESSO dopo 1004 ms   ⭐ il secondo fisso c'e'
   ⭐ SESSIONE: stato=1 tela=1920x1080 desktop=Meta-0
   resto attaccato per 60.0 s
   ⭐ ancora attaccato dopo 60.0 s: niente e' caduto
   [vid]  ⛔ nessun fotogramma preso dal filo: niente file
"""
FIATO_SANO = """   AMMESSO dopo 1013 ms   ⭐ il secondo fisso c'e'
   ⭐ SESSIONE: stato=1 tela=1920x1080 desktop=Meta-0
   ⭐ ancora attaccato dopo 60.0 s: niente e' caduto
   [vid]  1874 fotogrammi (3 chiavi), 1920x1080, scritti in /x/y.264
"""
FIATO_RESPINTO = """   ECCOMI: versione 1
   ⛔ RuntimeError: RESPINTO: motivo 0x07 = CREDENZIALI_ERRATE
"""


def taratura(verboso=True):
    """Quattro valori NOTI, e il metro deve ritrovarli."""
    casi = [
        ("T1 · il congedo noto", lambda: leggi_cliente(FIATO_CONGEDO)["congedo"], 0x0E),
        ("T2 · la pagina nera nota",
         lambda: (leggi_cliente(FIATO_NERO)["ammesso_ms"],
                  leggi_cliente(FIATO_NERO)["fotogrammi"],
                  leggi_cliente(FIATO_NERO)["sessione"]), (1004, 0, True)),
        ("T3 · i fotogrammi noti",
         lambda: leggi_cliente(FIATO_SANO)["fotogrammi"], 1874),
        ("T4 · ⛔ il fiato VUOTO non e' uno zero",
         lambda: (leggi_cliente("")["letto"], leggi_cliente("")["fotogrammi"],
                  leggi_cliente("")["congedo"]), (False, None, None)),
        ("T5 · il respinto si riconosce",
         lambda: leggi_cliente(FIATO_RESPINTO)["respinto"], 0x07),
    ]
    tutto = True
    for nome, f, atteso in casi:
        try:
            visto = f()
        except Exception as e:
            visto = "eccezione: %s" % e
        if visto == atteso:
            if verboso:
                _ok("%s — ritrovato %r" % (nome, visto))
        else:
            tutto = False
            _ko("%s — atteso %r, letto %r" % (nome, atteso, visto))
    return tutto


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ `--certifica` — i guasti innestati nei PREDICATI, senza macchina
# ═══════════════════════════════════════════════════════════════════════════

def certifica():
    _log("⭐ 10-c3-palchi --certifica — il metro e i predicati, senza rete")
    esiti = []

    def prova(nome, atteso, chiamata):
        try:
            visto = chiamata()[0]
        except Exception as e:
            visto = "eccezione: %s" % e
        buono = (visto == atteso)
        esiti.append((nome, buono, atteso, visto))
        (_ok if buono else _ko)("%s — atteso %s, visto %s" % (nome, atteso, visto))

    _log("1 · la taratura del metro")
    if not taratura():
        esiti.append(("taratura", False, "tutte", "una no"))

    _log("2 · `p_sollecitazione` — e i due modi di NON avere la scena")
    prova("sano: palchi pieni, un posto libero", True,
          lambda: p_sollecitazione({"figli": 2, "occupati": 1, "tetto": 2}))
    prova("⛔ G1: i palchi NON erano pieni", False,
          lambda: p_sollecitazione({"figli": 1, "occupati": 0, "tetto": 2}))
    prova("⛔ G2: erano pieni anche i posti (e' §6.4, non P3)", False,
          lambda: p_sollecitazione({"figli": 2, "occupati": 2, "tetto": 2}))
    prova("⚠ G3: non ho letto la scena ⇒ non giudico", None,
          lambda: p_sollecitazione({"figli": None, "occupati": 1, "tetto": 2}))

    _log("3 · `p_congedo_sul_filo` — il cuore del difetto")
    prova("sano: 0x0E", True, lambda: p_congedo_sul_filo(leggi_cliente(FIATO_CONGEDO)))
    prova("⛔ G4: SUL FILO NIENTE (il difetto P3)", False,
          lambda: p_congedo_sul_filo(leggi_cliente(FIATO_NERO)))
    prova("⛔ G5: il motivo sbagliato (0x0F, la bugia di R9.3)", False,
          lambda: p_congedo_sul_filo(leggi_cliente(
              FIATO_CONGEDO.replace("0x0e", "0x0f"))))
    prova("⚠ G6: RESPINTO ⇒ la prova non ha morso, non «respinto bene»", None,
          lambda: p_congedo_sul_filo(leggi_cliente(FIATO_RESPINTO)))
    prova("⚠ G7: il cliente non ha detto niente ⇒ non giudico", None,
          lambda: p_congedo_sul_filo(leggi_cliente("")))

    _log("4 · `p_niente_pagina_nera` — il sintomo che l'utente vede")
    prova("sano: l'AMMESSO non e' mai arrivato", True,
          lambda: p_niente_pagina_nera(leggi_cliente(FIATO_CONGEDO)))
    prova("⛔ G8: AMMESSO + SESSIONE + zero fotogrammi", False,
          lambda: p_niente_pagina_nera(leggi_cliente(FIATO_NERO)))
    prova("⛔ G9: e' entrato e ha visto (non e' la scena di P3)", False,
          lambda: p_niente_pagina_nera(leggi_cliente(FIATO_SANO)))
    prova("⚠ G10: entrato ma i fotogrammi non letti ⇒ non giudico", None,
          lambda: p_niente_pagina_nera(leggi_cliente(
              FIATO_NERO.replace("   [vid]  ⛔ nessun fotogramma preso dal filo: niente file\n", ""))))

    _log("5 · `p_dettaglio_nel_corpo`")
    prova("sano: il corpo nomina i palchi", True,
          lambda: p_dettaglio_nel_corpo(
              {"motivo": 0x0E, "dettaglio": "i palchi di questo server sono "
                                            "tutti impegnati (2 su 2)"}))
    prova("⛔ G11: corpo VUOTO", False,
          lambda: p_dettaglio_nel_corpo({"motivo": 0x0E, "dettaglio": ""}))
    prova("⛔ G12: il corpo non nomina il fatto", False,
          lambda: p_dettaglio_nel_corpo({"motivo": 0x0E, "dettaglio": "errore 14"}))
    prova("⚠ G13: nessun CONGEDO nella traccia ⇒ non giudico", None,
          lambda: p_dettaglio_nel_corpo({"motivo": None, "esito": "niente"}))
    prova("⚠ G14: traccia non letta ⇒ non giudico", None,
          lambda: p_dettaglio_nel_corpo(None))

    _log("6 · `p_niente_desktop` — §8.1 D6")
    prova("sano: 0 gnome-shell", True,
          lambda: p_niente_desktop({"gnome_respinto": 0, "proc_respinto": 3}))
    prova("⛔ G15: 1 gnome-shell e 42 processi (il numero di §6.4)", False,
          lambda: p_niente_desktop({"gnome_respinto": 1, "proc_respinto": 42}))
    prova("⚠ G16: non contati ⇒ non giudico", None,
          lambda: p_niente_desktop({"gnome_respinto": None}))

    _log("7 · `p_chi_c_era_resta` — I1")
    prova("sano: attaccato e con fotogrammi", True,
          lambda: p_chi_c_era_resta({"letto": True, "congedo": None,
                                     "resta_s": 120.0, "fotogrammi": 3600}))
    prova("⛔ G17: chi c'era e' stato CONGEDATO", False,
          lambda: p_chi_c_era_resta({"letto": True, "congedo": 0x0E,
                                     "resta_s": None, "fotogrammi": 10}))
    prova("⛔ G18: non e' rimasto attaccato", False,
          lambda: p_chi_c_era_resta({"letto": True, "congedo": None,
                                     "resta_s": None, "fotogrammi": 10}))
    prova("⛔ G19: attaccato ma ZERO fotogrammi", False,
          lambda: p_chi_c_era_resta({"letto": True, "congedo": None,
                                     "resta_s": 120.0, "fotogrammi": 0}))
    prova("⚠ G20: fotogrammi non letti ⇒ non giudico", None,
          lambda: p_chi_c_era_resta({"letto": True, "congedo": None,
                                     "resta_s": 120.0, "fotogrammi": None}))

    _log("8 · `p_define_seguono` — la prova che OGGI darebbe rosso sul prodotto di ieri")
    SANO = ["DEFINE rcp.c attaccate attaccate[2]",
            "DEFINE figlio.c v struct figlio v[2]",
            "DEFINE main.c presenti presenti[2]",
            "DEFINE webtransport.c palchi palchi[2]",
            "DEFINE aiutante.c volo struct volo volo[16]"]
    prova("sano: tutti a 2, e aiutante a 16", True,
          lambda: p_define_seguono(SANO, 2))
    prova("⛔ G21: MAX_FIGLI resta 16 — e' il rosso di §6.4", False,
          lambda: p_define_seguono(
              [r.replace("v[2]", "v[16]") for r in SANO], 2))
    prova("⛔ G22: WT_PALCHI resta 8 — morde a nove (R10-A6)", False,
          lambda: p_define_seguono(
              [r.replace("palchi[2]", "palchi[8]") for r in SANO], 2))
    prova("⛔ G23: QUANTI_PRESENTI resta 16", False,
          lambda: p_define_seguono(
              [r.replace("presenti[2]", "presenti[16]") for r in SANO], 2))
    prova("⛔ G24: ⛔ aiutante.c HA SEGUITO — e non doveva", False,
          lambda: p_define_seguono(
              [r.replace("volo[16]", "volo[2]") for r in SANO], 2))
    prova("⚠ G25: una riga non letta ⇒ non giudico", None,
          lambda: p_define_seguono(SANO[:4], 2))
    prova("⚠ G26: niente da leggere ⇒ non giudico", None,
          lambda: p_define_seguono([], 2))

    _log("9 · `p_frase_della_pagina`")
    prova("sano: la frase e' quella della voce 0x0E", True,
          lambda: p_frase_della_pagina(
              {"frase": "quella sessione non si può servire"},
              {"0x0e": "quella sessione non si può servire"}))
    prova("⛔ G27: LA PAGINA MENTE («gia' collegato»)", False,
          lambda: p_frase_della_pagina(
              {"frase": "sei gia' collegato altrove"}, {}))
    prova("⛔ G28: frase VUOTA", False,
          lambda: p_frase_della_pagina({"frase": "  "}, {}))
    prova("⛔ G29: la frase non viene dalla voce 0x0E", False,
          lambda: p_frase_della_pagina(
              {"frase": "il server e' pieno"},
              {"0x0e": "quella sessione non si può servire"}))
    prova("⚠ G30: la pagina non e' stata guardata ⇒ non giudico", None,
          lambda: p_frase_della_pagina({"frase": None, "perche": "niente Firefox"}, {}))

    rossi = [e for e in esiti if not e[1]]
    _log("%d casi · %d hanno fatto quel che dovevano · %d NO"
         % (len(esiti), len(esiti) - len(rossi), len(rossi)))
    for e in rossi:
        _ko("%s — atteso %s, visto %s" % (e[0], e[2], e[3]))
    return 0 if not rossi else 1


# ═══════════════════════════════════════════════════════════════════════════
# IL GIRO VERO
# ═══════════════════════════════════════════════════════════════════════════

def terreno_mio(B93):
    """⛔⛔ E QUI **NON** SI CHIAMA `10-b0-terreno.sh`, ED E' UNA SCELTA.

    Il controllo della fase confronta **byte per byte** i sorgenti del
    repository con quelli spediti (predicato T5.2, *«il server misura una
    versione che nessuno sta leggendo»*).  ⛔ Questo banco spedisce un albero
    **modificato di proposito** — il tetto a 2, e nei giri di controllo un
    guasto innestato — quindi T5.2 darebbe rosso **per costruzione**.

    ⇒ Un controllo che si sa di dover ignorare e' peggio di nessun controllo:
      la volta dopo lo si ignora anche quando ha ragione.  ⭐ Fa lo stesso
      `10-b93-pieno.py`, e per la stessa ragione.

    ⚠ Da cui questo, che guarda le cose che restano vere anche su un albero
      modificato — e le guarda TUTTE, dichiarando ognuna:
        1. i tre utenti esistono e la parola sta in un file `0600`;
        2. l'arbitro di §11.1 e' arrivato (senza, ogni traccia sembra vuota);
        3. c'e' un ascoltatore sulla MIA porta, e si contano quelli degli altri
           **senza toccarli**;
        4. ⛔ il binario e' **piu' giovane** dei sorgenti che dice di portare
           (la forma **D5**, «stantio ma verde»);
        5. ⛔⛔ il **lucchetto della GPU e' MIO** — non «libero»: mio.
    """
    _inf("⚠ `10-b0-terreno.sh` NON si chiama qui: l'albero e' modificato di "
         "proposito (tetto piccolo, e nei controlli un guasto), e il suo T5.2 "
         "darebbe rosso per costruzione — vedi il riquadro della funzione")
    guai = []
    for u in (A_UTENTE, B_UTENTE, C_UTENTE):
        rc, out, _ = B93.root("id %s >/dev/null 2>&1 && echo si || echo no" % u)
        if "si" not in out:
            guai.append("l'utente «%s» non c'e': bash banchi/10-c3-terreno.sh utenti" % u)
    rc, out, _ = B93.root("test -s %s/parola && echo si || echo no" % B93.LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % B93.LAV)
    rc, out, _ = B93.root("test -s %s/banchi/01-b4-validatore.py && echo si || echo no"
                          % B93.ALB)
    if "si" not in out:
        guai.append("manca l'arbitro di §11.1 in %s/banchi: senza, i lettori "
                    "della traccia non partono e OGNI giro sembra una sessione "
                    "morta" % B93.ALB)
    # ⛔ Le porte che NON sono mie: si CONTANO e non si toccano mai.  ⚠ Alla
    #    lista di `10-b93` si aggiungono le porte degli agenti che girano ADESSO
    #    accanto a me: contarle e' l'unico modo di sapere, leggendo il rapporto,
    #    se ero solo sulla macchina o no.
    vicine = list(B93.VICINE) + [p for p in ("8220", "8230") if p not in B93.VICINE
                                 and p != str(B93.PORTA)]
    conto = " ".join("%s:%s" % (p, B93.ascoltatori(p)) for p in vicine)
    _inf("ascoltatori NON miei (si contano, non si toccano): %s" % conto)
    n = B93.ascoltatori(B93.PORTA)
    _inf("il mio server sulla %d: %s ascoltatore/i" % (B93.PORTA, n))
    if not n:
        guai.append("nessuno ascolta sulla %d: bash banchi/10-c3-terreno.sh accendi"
                    % B93.PORTA)
    # ⛔ D5 — «un binario stantio resta verde».
    rc, out, _ = B93.root(
        "b=$(stat -c %%Y %s/src/remotix 2>/dev/null || echo 0); "
        "v=$(ls -t %s/src/*.c %s/src/*.h 2>/dev/null | head -1); "
        "echo BIN $b; echo PIUNUOVO $(stat -c %%Y \"$v\" 2>/dev/null || echo 0) $v"
        % (B93.ALB, B93.ALB, B93.ALB))
    bt = sn = None
    for r in out.splitlines():
        p = r.split()
        if len(p) >= 2 and p[0] == "BIN" and p[1].isdigit():
            bt = int(p[1])
        if len(p) >= 2 and p[0] == "PIUNUOVO" and p[1].isdigit():
            sn = int(p[1])
    if bt is None or sn is None or bt == 0:
        guai.append("⚠ non ho potuto confrontare l'eta' del binario coi sorgenti")
    elif sn > bt:
        guai.append("⛔ IL BINARIO E' PIU' VECCHIO DI UN SORGENTE (forma D5): "
                    "si ricostruisce prima di misurare")
    else:
        _inf("⭐ il binario e' piu' giovane dei sorgenti che porta")
    # ⛔⛔ Il lucchetto dev'essere MIO, non libero.
    try:
        luc = _carica("luc", _trova("09-lucchetto.py"))
        os.environ.setdefault("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-gpu.d")
        luc.POSTO = os.environ["LUCCHETTO"]
        chi, scad = luc.stato()
        if chi != IO_SONO:
            guai.append("⛔⛔ il lucchetto della GPU e' di «%s», non mio (%s): "
                        "due carichi di GPU insieme si falsano IN SILENZIO"
                        % (chi, IO_SONO))
        else:
            _inf("⭐ il lucchetto e' mio (%s), scade fra %d s"
                 % (IO_SONO, max(0, int((scad or 0) - time.time()))))
    except Exception as e:
        guai.append("⚠ non ho potuto leggere il lucchetto: %s" % e)
    for g in guai:
        _ko(g)
    if not guai:
        _ok("il terreno c'e', ed e' mio")
    return not guai


def leggi_define(B93):
    """Le cinque righe `DEFINE …` da `10-c3-terreno.sh definisci`."""
    p = subprocess.run(["bash", os.path.join(QUI, "10-c3-terreno.sh"), "definisci"],
                       capture_output=True, timeout=900,
                       env=dict(os.environ))
    out = p.stdout.decode("utf-8", "replace")
    return [r.strip() for r in out.splitlines() if r.strip().startswith("DEFINE")]


def cliente_riga(B93, utente, resta, registra=None, video=None):
    return ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
            "--utente %s --parola-file %s/parola --audio-codec pcm "
            "--video-codec h264 --adatta 1920x1080 %s%s--resta %s"
            % (B93.DENTRO_ALB, B93.IND, B93.PORTA, utente, B93.DENTRO_LAV,
               ("--registra %s/%s.rcpreg " % (B93.DENTRO_LAV, registra)) if registra else "",
               ("--video-scrivi %s/%s.264 " % (B93.DENTRO_LAV, video)) if video else "",
               resta))


def avvia(B93, utente, resta, registra=None, video=None):
    riga = B93.catena_root("bash /media/REMOTIX/enter.sh --root %s"
                           % shlex.quote(
                               cliente_riga(B93, utente, resta, registra, video)))
    return subprocess.Popen(["ssh", "-o", "BatchMode=yes", B93.MACCHINA, riga],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def fiato(proc, tetto):
    try:
        out, _ = proc.communicate(timeout=tetto)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
    return (out or b"").decode("utf-8", "replace")


def sblocca(B93, perche):
    """⛔⛔ IL CONTO DI §4.4-bis SI AZZERA, E SI DICHIARA PERCHE'.

    Il ban e' per **INDIRIZZO** e dura **dodici ore**, e tutti gli agenti di
    questa fase partono dallo stesso indirizzo.  ⇒ Tre tentativi falliti di
    questo banco mettono fuori uso **ogni altro banco della macchina**.
    ⚠ E `01-b8-sblocca.py` azzera il conto anche quando risponde *«non era
      bannato»* — `[M]` 11 agosto 2026, `01-b8-prova-ban.c` sezione 5.
    """
    _dub("⚠ sblocco l'indirizzo (%s): il ban e' per INDIRIZZO e lo pagherebbero "
         "tutti gli altri banchi" % perche)
    B93.dentro("python3 %s/banchi/01-b8-sblocca.py --socket %s/comando.sock %s"
               % (B93.DENTRO_ALB, B93.DENTRO_LAV, B93.IND))


def attendi_dentro(B93, proc, riga0, utente, tetto=120):
    """⛔⛔ «E' ENTRATO» LO DICE IL REGISTRO, MA «NON ENTRERA' MAI» LO DICE IL
        CLIENTE — e aspettare 120 s un fatto gia' impossibile e' il modo in cui
        un banco trasforma un difetto suo in un rosso del prodotto.

    `[M]` 25 agosto 2026, primo giro di questo banco: `provadec4` e' stato
    **RESPINTO con 0x07** perche' la sua parola d'ordine era stata cambiata da
    **un altro agente** — `provadec4/5/6` sono condivisi, e
    `07-b64-terreno.sh utente` **rifa' la parola a ogni chiamata**: l'ultimo che
    la scrive vince, e gli altri leggono «credenziali errate».
    ⛔ E ogni respinto **consuma uno dei tre tentativi** del ban per indirizzo.

    ⇒ Qui si guarda il registro **e** il processo del cliente, e appena il
      cliente muore si smette di aspettare, si legge il suo fiato e si dichiara.

    Torna `("dentro", "")` · `("morto", fiato)` · `("scaduto", "")`.
    """
    scade = time.time() + tetto
    atteso = "posto PRESO da %s" % utente
    while time.time() < scade:
        t = B93.registro_da(riga0, atteso, tetto=400) or ""
        if atteso in t:
            return ("dentro", "")
        if proc.poll() is not None:
            return ("morto", fiato(proc, 10))
        time.sleep(1.0)
    return ("scaduto", "")


def giro_vero(o):
    B93 = _carica("b93", _trova("10-b93-pieno.py"))
    if B93.PORTA != int(os.environ["PORTA"]) or B93.LAV != os.environ["LAV"]:
        _ko("⛔ l'ambiente non e' il mio (porta %s, lavoro %s): NON misuro"
            % (B93.PORTA, B93.LAV))
        return 2
    _inf("porta %d · albero %s · lavoro %s · unita' %s"
         % (B93.PORTA, B93.ALB, B93.LAV, B93.UNITA))

    _log("0 · ⭐ LA TARATURA DEL METRO — e gira anche qui, non solo in --certifica")
    if not taratura():
        _ko("⛔ il metro non e' tarato: NON misuro")
        return 2

    _log("1 · Il controllo del terreno")
    if not terreno_mio(B93):
        _ko("⛔ il terreno NON regge: non misuro")
        return 2

    esiti = {}
    scatto = {}
    scena = {"tetto": o.tetto, "figli": None, "occupati": None}
    traccia = None
    c_letto = {"letto": False}
    a_letto = {"letto": False}
    pagina = None

    _log("2 · ⛔ Sgombro quel che potrebbe essere rimasto di un altro giro")
    B93.root("pkill -f '%s'; true" % B93.modello_cliente("--porta %d" % B93.PORTA))
    # ⛔⭐ E SU UN SERVER APPENA ACCESO NON C'E' NIENTE DA ASPETTARE — `[M]` 25
    #     agosto 2026, e il banco ha detto una bugia prima che me ne accorgessi.
    #
    #     `aspetta_tabella_vuota()` chiede a `occupati_adesso()`, che legge
    #     l'ULTIMA riga «occupati adesso: N» del registro.  ⛔ `accendi` tronca
    #     il registro, quindi su un server appena acceso quella riga **non
    #     esiste**: la funzione torna `None`, la condizione `n == 0` non e' mai
    #     vera, e dopo 90 s il banco stampava *«i posti non sono tornati vuoti:
    #     la scena parte sporca»* — ⛔ **su una tabella perfettamente vuota**.
    #     ⚠ E' `None` scambiato per un valore, cioe' la forma d'errore che
    #       questo progetto punisce di piu': «non ho letto» con la faccia di
    #       «e' successo qualcosa».
    # ⇒ Si guarda prima se un posto sia MAI stato preso da quando il registro
    #   comincia.  Se no, non c'e' niente da aspettare, e lo si dice.
    presi = B93.registro_da(0, "posto PRESO da", tetto=50) or ""
    if not presi.strip():
        _inf("⭐ il registro non porta nessun «posto PRESO»: il server e' appena "
             "acceso e la tabella e' vuota per costruzione — niente da aspettare")
    elif not B93.aspetta_tabella_vuota(90):
        _dub("⚠ i posti non sono tornati vuoti: la scena parte sporca, e lo dico")

    pid = B93.pid_del_server()
    if not pid:
        _ko("⛔ il server non e' acceso sulla %d" % B93.PORTA)
        return 2
    riga0 = B93.righe_registro()
    _inf("server pid %s · registro a riga %s" % (pid, riga0))

    # ───────────────────────────────────────────────────────────────────────
    _log("3 · A entra e RESTA (%s, %d s)" % (A_UTENTE, o.durata_a))
    pa = avvia(B93, A_UTENTE, o.durata_a, video="a-dentro")
    esito, fa = attendi_dentro(B93, pa, riga0, A_UTENTE, 150)
    if esito != "dentro":
        _dub("⚠ A non ha preso il posto (%s): la scena non si e' formata, e "
             "NON giudico niente" % esito)
        for r in (fa or "").splitlines():
            if r.strip():
                _inf("[A] %s" % r.strip()[:160])
        if leggi_cliente(fa).get("respinto") is not None:
            _ko("⛔ A e' stato RESPINTO: la parola d'ordine di «%s» non e' quella "
                "che ho in mano.  ⚠ `provadec4/5/6` sono CONDIVISI e "
                "`07-b64-terreno.sh utente` la riscrive: rilancia "
                "`bash banchi/10-c3-terreno.sh utenti` e ripeti" % A_UTENTE)
            sblocca(B93, "A respinto")
        pa.kill()
        return 2
    _ok("A e' dentro")

    _log("4 · B entra e SE NE VA PULITO (%s, %d s) — il posto torna, il palco no"
         % (B_UTENTE, o.durata_b))
    pb = avvia(B93, B_UTENTE, o.durata_b, video="b-dentro")
    esito, fb = attendi_dentro(B93, pb, riga0, B_UTENTE, 150)
    if esito != "dentro":
        _dub("⚠ B non ha preso il posto (%s): la scena non si e' formata, e NON "
             "giudico niente" % esito)
        for r in (fb or "").splitlines():
            if r.strip():
                _inf("[B] %s" % r.strip()[:160])
        if leggi_cliente(fb).get("respinto") is not None:
            _ko("⛔ B e' stato RESPINTO: vedi la nota su «%s»" % A_UTENTE)
            sblocca(B93, "B respinto")
        pa.kill(); pb.kill()
        return 2
    _ok("B e' dentro")
    fiato(pb, o.durata_b + 90)
    _inf("B se n'e' andato")

    _log("5 · ⛔ LA SCENA — palchi pieni, e un posto LIBERO")
    scade = time.time() + 60
    while time.time() < scade:
        f = B93.fotografia(pid, riga0)
        scena["figli"] = f.get("figli")
        scena["occupati"] = B93.occupati_adesso()
        if scena["figli"] == o.tetto and (scena["occupati"] or 0) < o.tetto:
            break
        time.sleep(2.0)
    _inf("figli = %s · posti occupati = %s · tetto = %s"
         % (scena["figli"], scena["occupati"], o.tetto))
    esiti["0 · la sollecitazione e' arrivata"] = p_sollecitazione(scena)

    # ───────────────────────────────────────────────────────────────────────
    _log("6 · ⛔ C BUSSA (%s, %d s di ascolto)" % (C_UTENTE, o.durata_c))
    t_bussa = time.time()
    pc = avvia(B93, C_UTENTE, o.durata_c, registra="c-respinto", video="c-respinto")
    testo_c = fiato(pc, o.durata_c + 120)
    dt = time.time() - t_bussa
    c_letto = leggi_cliente(testo_c)
    # ⭐ QUANTO CI HA MESSO IL NO — ed e' la meta' del difetto che il motivo non
    #    dice: prima della cura l'utente restava li' **senza nessun tempo dopo
    #    il quale migliorasse**.  ⚠ E' il tempo del CLIENTE intero (stretta di
    #    mano + PAM + esito), non il tempo del solo congedo: si dichiara cosi'.
    c_letto["durata_s"] = round(dt, 1)
    for r in testo_c.splitlines():
        if r.strip():
            _inf("[C] %s" % r.strip()[:160])
    _inf("C ha finito in %.1f s" % dt)

    _log("7 · La fotografia del respinto — e il desktop che NON deve esserci")
    scatto = B93.fotografia(pid, riga0)
    _inf("gnome-shell del respinto: %s · processi: %s · figli: %s"
         % (scatto.get("gnome_respinto"), scatto.get("proc_respinto"),
            scatto.get("figli")))

    _log("8 · La traccia §11.1 di C — il corpo del CONGEDO")
    if B93.spedisci_lettori(_carica("b70", _trova("09-b70-ritmo.py"))):
        d = B93.leggi_traccia_canale("c-respinto")
        msg = [m for m in (d.get("messaggi") or []) if m.get("nome") == "CONGEDO"]
        if msg:
            traccia = {"motivo": msg[-1].get("motivo"),
                       "dettaglio": msg[-1].get("dettaglio")}
        else:
            traccia = {"motivo": None, "esito": d.get("esito", "nessun CONGEDO")}
        _inf("traccia: %s" % json.dumps(traccia, ensure_ascii=False)[:300])

    _log("9 · La frase che la PAGINA mostra — Firefox VERO, sul portatile")
    if o.pagina:
        try:
            pagina = B93.guarda_la_pagina()
            _inf("pagina: %s" % json.dumps(pagina, ensure_ascii=False)[:300])
        except Exception as e:
            pagina = {"frase": None, "perche": "%s" % e}
            _dub("⚠ non ho potuto guardare la pagina: %s" % e)
    else:
        pagina = {"frase": None, "perche": "--niente-pagina"}

    _log("10 · A, alla fine")
    testo_a = fiato(pa, o.durata_a + 120)
    a_letto = leggi_cliente(testo_a)
    for r in testo_a.splitlines():
        if r.strip() and ("[vid]" in r or "attaccato" in r or "CONGEDO" in r):
            _inf("[A] %s" % r.strip()[:160])

    _log("11 · I `#define`, letti dopo il preprocessore")
    righe = leggi_define(B93)
    for r in righe:
        _inf(r)

    # ───────────────────────────────────────────────────────────────────────
    esiti["1 · il no esce sul filo, col motivo giusto"] = p_congedo_sul_filo(c_letto)
    esiti["2 · il corpo porta il dettaglio"] = p_dettaglio_nel_corpo(traccia)
    esiti["3 · nessuna pagina nera"] = p_niente_pagina_nera(c_letto)
    esiti["4 · niente desktop a chi verra' respinto (D6)"] = p_niente_desktop(scatto)
    esiti["5 · la frase della pagina"] = p_frase_della_pagina(
        pagina, B93.tabella_motivo_servita())
    esiti["6 · chi c'era gia' non se ne accorge (I1)"] = p_chi_c_era_resta(a_letto)
    esiti["7 · i #define si seguono"] = p_define_seguono(righe, o.tetto)

    _log("IL VERDETTO")
    rossi = muti = 0
    for nome, (esito, perche) in esiti.items():
        if esito is True:
            _ok("%s — %s" % (nome, perche))
        elif esito is False:
            rossi += 1
            _ko("%s — %s" % (nome, perche))
        else:
            muti += 1
            _dub("%s — %s" % (nome, perche))
    _log("%d predicati · %d rossi · %d «non ho misurato»"
         % (len(esiti), rossi, muti))

    if o.jsonl:
        with open(o.jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "guasto": o.guasto, "tetto": o.tetto, "scena": scena,
                "c": c_letto, "a": a_letto, "scatto": scatto,
                "traccia": traccia, "pagina": pagina, "define": righe,
                "esiti": {k: v[0] for k, v in esiti.items()},
                "perche": {k: v[1] for k, v in esiti.items()},
            }, ensure_ascii=False) + "\n")
    return 1 if rossi else 0


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--tetto", type=int, default=TETTO_ATTESO)
    p.add_argument("--durata-a", type=int, default=260)
    p.add_argument("--durata-b", type=int, default=20)
    p.add_argument("--durata-c", type=int, default=60)
    p.add_argument("--guasto", default=os.environ.get("GUASTO", "nessuno"))
    p.add_argument("--jsonl", default="")
    p.add_argument("--niente-pagina", dest="pagina", action="store_false",
                   default=True)
    o = p.parse_args()
    if o.certifica:
        return certifica()
    return giro_vero(o)


if __name__ == "__main__":
    sys.exit(principale())
