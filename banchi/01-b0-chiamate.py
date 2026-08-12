#!/usr/bin/env python3
"""01-b0-chiamate.py — ⛔ chi chiama un banco gli passa quel che il banco pretende?

    python3 banchi/01-b0-chiamate.py            il giro intero
    python3 banchi/01-b0-chiamate.py --elenco   che cosa pretende ogni banco
    python3 banchi/01-b0-chiamate.py --autoprova  ⭐ solo il controllo positivo

---------------------------------------------------------------------------
⛔ PERCHE' ESISTE, E IL CONTO E' TRE VOLTE IN DUE GIORNI

Un banco guadagna un argomento **obbligatorio**, e uno dei suoi chiamanti resta
indietro.  Il banco allora non misura: si rifiuta di partire, esce 2, e chi
legge il giro vede un **rosso** — di un banco sano, per una ragione che non e'
del banco.

  `[M]` 10 agosto 2026 · `01-b2-sonda-trasporto.py` guadagna `--bersaglio`
        obbligatorio.  `01-b6-lancia.sh` lo chiamava senza: B6 **si e'
        rifiutato di misurare**.
  `[M]` 10 agosto 2026 · stessa cosa in `01-b3-quarto-giro.sh`.
  `[M]` 11 agosto 2026 · `01-b7-congedo.py` pretende `--bersaglio`, e
        `01-b12-lancia.sh` lo chiamava senza — **e per giunta gli passava un
        `--sorgente` che non esiste piu'**.  Il giro di certificazione ha
        scritto **«B7 NON certificato»**: un banco certificato ieri, dichiarato
        rotto oggi, da una riga di comando.

⭐ Tre volte la stessa forma vuole un controllo, non un terzo rattoppo.  E la
   forma ha un nome nel progetto: **la cucitura fra due file che nessuno
   possiede**, gia' pagata su B6 e su B7.

---------------------------------------------------------------------------
⛔ CHE COSA QUESTO CONTROLLO **NON** SA FARE, detto prima e non dopo

`[M]` 12 agosto 2026 — difetto **D9**: sette chiamate su cinquantadue
restavano «IGNOTE», e nessuno sapeva **perche'**.  Il difetto non era il
numero: era che «IGNOTA» era **un motivo solo per casi di tipo diverso**, e
quindi non diceva a nessuno che cosa fare.  Adesso ogni ignota porta con se'
il proprio motivo, e i motivi sono tre e stanno qui sotto, in `MOTIVI` —
**nel codice, accanto al caso**, non in un rapporto che nessuno rilegge.

⚠ E un IGNOTO **non fa fallire** il giro: fa stampare quali chiamate nessuno
  sta sorvegliando, che e' un'informazione e non un allarme.  ⛔ Ma non
  diventa mai un verde: e' la forma **E8** del catalogo (`REVIEWER.md` §2),
  *«vuoto» e «proibito» hanno lo stesso aspetto*, ed e' esattamente il difetto
  che questo file esiste per trovare (`LEZIONI.md` §1.9).

---------------------------------------------------------------------------
⭐ E IL CONTROLLO POSITIVO, che il 12 agosto **non c'era**

«0 rotte» non distingue *«tutto a posto»* da *«non sto guardando»*.  Percio'
ogni giro finisce costruendo, in una cartella temporanea, **un banco finto e
un chiamante guasto apposta** — con dentro le stesse quattro forme di guasto
gia' pagate — e verificando che lo strumento le veda **tutte**.  Se non le
vede, il giro esce **2** e il verde di sopra non vale.  (`REVIEWER.md` §1
punto 5; `CODER.md` §3.10.)
"""
import argparse
import ast
import collections
import os
import re
import shutil
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
VERDE, ROSSO, GIALLO, GRIGIO, NETTO = (
    "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m", "\033[1m")

# ---------------------------------------------------------------------------
# ⛔⭐ I TRE MOTIVI PER CUI UNA CHIAMATA RESTA INGIUDICABILE — dichiarati qui,
#     accanto al caso, e non in un rapporto.
#
# `[M]` 12 agosto 2026, difetto D9: prima di oggi il motivo era uno solo,
# «variabili che non so sciogliere», e sotto quella frase stavano casi di
# natura diversa — alcuni curabili, uno no.  Un «non so» che non dice **quale**
# non so e' un «non so» su cui nessuno puo' lavorare.
MOTIVI = {
    "PASSAGGIO":
        "la riga passa `$*` o `$@`: gli argomenti arrivano da CHI LANCIA lo "
        "script e non stanno in nessun file di questo deposito.\n"
        "        ⛔ INGIUDICABILE PER COSTRUZIONE, non per pigrizia dello "
        "strumento: per giudicarla bisognerebbe eseguire il chiamante del "
        "chiamante.",
    "SOTTOCOMANDO":
        "il banco ha sotto-comandi (`add_subparsers`) e qui il sotto-comando "
        "e' una variabile.\n"
        "        ⛔ Ogni sotto-comando pretende cose diverse: giudicare col "
        "solo insieme comune sarebbe un verde comprato allargando le maglie.",
    "VARIABILE-SOLA":
        "una variabile (o un vettore `${x[@]}`) che sta DA SOLA dove argparse "
        "aspetta un'opzione, e il suo valore o non e' letterale in nessuna riga "
        "del file, o dipende da un RAMO che qui non si esegue.\n"
        "        ⛔ Puo' portarsi dietro un `--qualcosa`, e non so quale: "
        "approvarla sarebbe scambiare «non ho guardato» per «ho guardato».",
}

Profilo = collections.namedtuple(
    "Profilo", "obb tutte corte arita posiz sotto")
# obb    — le opzioni obbligatorie del livello base
# tutte  — tutte le opzioni ammesse (base + ogni sotto-comando)
# corte  — le «scorciatoie»: `if "--elenco" in sys.argv:` prima di parse_args
# arita  — {opzione: quanti valori si porta via}, `-1` = quanti ne trova
# posiz  — quanti argomenti posizionali ammette il livello base, `-1` = infiniti
# sotto  — {sotto-comando: (obb, tutte, posiz)}; vuoto se non ce ne sono


# ---------------------------------------------------------------------------
#  Leggere un banco: che cosa pretende
# ---------------------------------------------------------------------------
def _arita_di(nodo):
    """Quanti valori si porta via un'opzione. `-1` = quanti ne trova."""
    azione, nargs = None, None
    for k in nodo.keywords:
        if k.arg == "action" and isinstance(k.value, ast.Constant):
            azione = k.value.value
        if k.arg == "nargs" and isinstance(k.value, ast.Constant):
            nargs = k.value.value
    if azione in ("store_true", "store_false", "count", "help", "version"):
        return 0
    if nargs is None:
        return 1
    if isinstance(nargs, int):
        return nargs
    if nargs == "?":
        return 1
    return -1                       # '*', '+', REMAINDER


def opzioni_di(percorso):
    """Il `Profilo` del banco, letto con l'AST — oppure `None`.

    ⛔ Con l'AST e non con una espressione regolare: `required=True` puo' stare
       su una riga diversa dal nome, e un banco che il controllo non sa leggere
       diventerebbe un banco senza obblighi — cioe' sempre verde.
    """
    try:
        with open(percorso, encoding="utf-8") as f:
            albero = ast.parse(f.read(), percorso)
    except (OSError, SyntaxError):
        return None

    # ⛔⭐ LE SCORCIATOIE — `if "--elenco" in sys.argv:` PRIMA di `parse_args`.
    #
    # `01-b7-congedo.py:1722` fa esattamente questo: con `--elenco` stampa il
    # catalogo dei motivi e se ne va, **senza** pretendere `--porta`.
    # `[M]` 11 agosto 2026: senza saperlo, questo controllo ha accusato tre
    # righe sane — fra cui `01-b7-lancia.sh:92`, che sul server esce **0**.
    # ⚠ Verificato lanciandole davvero, non deducendolo: due delle tre erano
    #   false e la terza (`01-b8-cronometro.py --previsione`) era vera.
    #   ⛔ Se avessi «curato» tutte e tre avrei rotto due chiamate funzionanti
    #   per far tacere il mio stesso strumento.
    scorciatoie = set()
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.Compare) and len(nodo.ops) == 1
                and isinstance(nodo.ops[0], ast.In)
                and isinstance(nodo.left, ast.Constant)
                and isinstance(nodo.left.value, str)
                and nodo.left.value.startswith("--")):
            scorciatoie.add(nodo.left.value)

    # ⛔⭐ I SOTTO-COMANDI — `[M]` 12 agosto 2026, difetto D9.
    #
    # `01-p5-registro.py` e' l'unico banco con `add_subparsers`, e i suoi
    # obblighi sono **per sotto-comando**: `cerca` pretende `--giro` e `--tipo`,
    # `righe` non pretende niente.  Unendoli in un insieme solo, come faceva la
    # prima stesura, `python3 "$REG" righe` sarebbe diventato un ROSSO su una
    # riga sana — cioe' la forma opposta del difetto che questo file cerca, e
    # gia' pagata una volta l'11 agosto sul modulo comune (piu' sotto).
    cicli = {}
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.For) and isinstance(nodo.target, ast.Name)
                and isinstance(nodo.iter, (ast.Tuple, ast.List))):
            valori = [e.value for e in nodo.iter.elts
                      if isinstance(e, ast.Constant)
                      and isinstance(e.value, str)]
            if valori:
                cicli[nodo.target.id] = valori

    tenitori = set()
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Call)
                and isinstance(nodo.value.func, ast.Attribute)
                and nodo.value.func.attr == "add_subparsers"):
            tenitori.update(t.id for t in nodo.targets
                            if isinstance(t, ast.Name))

    def nomi_del_parser(chiamata):
        if not (isinstance(chiamata.func, ast.Attribute)
                and chiamata.func.attr == "add_parser"
                and isinstance(chiamata.func.value, ast.Name)
                and chiamata.func.value.id in tenitori):
            return None
        arg = chiamata.args[0] if chiamata.args else None
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return [arg.value]
        if isinstance(arg, ast.Name) and arg.id in cicli:
            return list(cicli[arg.id])
        return []

    sotto = {}                     # nome sotto-comando -> [obb, tutte, posiz]
    di_chi = {}                    # variabile Python -> [nomi sotto-comando]

    def registra(nome):
        return sotto.setdefault(nome, [set(), set(), 0])

    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.Call):
            nomi = nomi_del_parser(nodo)
            if nomi:
                for x in nomi:
                    registra(x)
        if isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Call):
            nomi = nomi_del_parser(nodo.value)
            if nomi:
                for t in nodo.targets:
                    if isinstance(t, ast.Name):
                        di_chi[t.id] = nomi

    obbligatorie, tutte, arita, posiz = set(), set(), {}, 0
    for nodo in ast.walk(albero):
        if not (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "add_argument"):
            continue
        ricevente = (nodo.func.value.id
                     if isinstance(nodo.func.value, ast.Name) else None)
        dove = di_chi.get(ricevente)          # None ⇒ e' il parser principale
        nomi = [a.value for a in nodo.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
                and a.value.startswith("--")]
        posizionali = [a.value for a in nodo.args
                       if isinstance(a, ast.Constant)
                       and isinstance(a.value, str)
                       and not a.value.startswith("-")]
        quanti = _arita_di(nodo)
        richiesta = any(
            k.arg == "required" and isinstance(k.value, ast.Constant)
            and k.value.value is True for k in nodo.keywords)
        for n in nomi:
            arita[n] = quanti
        if posizionali:
            for nome_sotto in (dove or [None]):
                bersaglio = registra(nome_sotto) if nome_sotto else None
                if bersaglio is None:
                    posiz = -1 if (quanti < 0 or posiz < 0) else posiz + 1
                else:
                    bersaglio[2] = (-1 if (quanti < 0 or bersaglio[2] < 0)
                                    else bersaglio[2] + 1)
        if not nomi:
            continue
        for nome_sotto in (dove or [None]):
            if nome_sotto is None:
                tutte.update(nomi)
                if richiesta:
                    obbligatorie.update(nomi)
            else:
                b = registra(nome_sotto)
                b[1].update(nomi)
                if richiesta:
                    b[0].update(nomi)

    for b in sotto.values():
        tutte |= b[1]
    return Profilo(obbligatorie, tutte, scorciatoie, arita, posiz,
                   {k: tuple(v) for k, v in sotto.items()})


# ---------------------------------------------------------------------------
#  Leggere un chiamante: le righe, le variabili, le funzioni
# ---------------------------------------------------------------------------
def righe_logiche(percorso):
    """[(numero della PRIMA riga, testo)] con le CONTINUAZIONI unite.

    ⛔⭐ `[M]` 12 agosto 2026, difetto D9 — e questa e' la meta' peggiore del
    difetto, perche' non produceva un IGNOTO: produceva **il silenzio**.

    Una riga di comando spezzata con `\\` a fine riga porta le opzioni sulle
    righe DOPO.  Leggendo una riga per volta, questo controllo vedeva
    `python3 .../02-filo-validatore.py \\` — nessuna opzione — e la scartava
    come «citazione».  ⇒ **quattro chiamate all'arbitro nuovo di F2.4, zero
    guardate**, e nel conto non comparivano nemmeno come ignote.
    Cosi' erano fuori anche `01-b7-lancia.sh:256` e `01-b8-lancia.sh:410`.

    ⚠ Un commento non si unisce mai alla riga dopo: in shell `#` mangia fino a
      fine riga e basta, e unirlo commenterebbe una riga viva.
    """
    try:
        with open(percorso, encoding="utf-8") as f:
            grezze = f.read().splitlines()
    except OSError:
        return None
    unite, n_inizio, corrente = [], None, None
    for n, riga in enumerate(grezze, 1):
        if corrente is None:
            n_inizio, corrente = n, riga
        else:
            corrente += " " + riga.lstrip()
        # `\\` (due) e' una barra scritta, non una continuazione
        if (corrente.endswith("\\") and not corrente.endswith("\\\\")
                and not corrente.lstrip().startswith("#")):
            corrente = corrente[:-1]
            continue
        unite.append((n_inizio, corrente))
        corrente = None
    if corrente is not None:
        unite.append((n_inizio, corrente))
    return unite


def testo_utile(percorso):
    """Le righe logiche, senza le stringhe lunghe di Python e senza i commenti.

    ⛔ E SI SALTANO ANCHE LE STRINGHE LUNGHE, non solo i commenti — `[M]` 11
       agosto 2026: alla prima stesura questo controllo accusava **ventuno**
       chiamate, e quasi tutte erano righe di ESEMPIO dentro la spiegazione in
       testa a un banco (`python3 01-b8-cronometro.py --campioni --blocco 3`).
       ⭐ Un controllo che grida sul falso non viene ignorato di meno di uno
       che tace: viene ignorato **insieme ai suoi veri**.
    """
    righe = righe_logiche(percorso)
    if righe is None:
        return None
    fuori, dentro_stringa = [], None
    for n, riga in righe:
        if percorso.endswith(".py"):
            resto, fuori_stringa = riga, ""
            while resto:
                if dentro_stringa:
                    taglio = resto.find(dentro_stringa)
                    if taglio < 0:
                        break
                    resto = resto[taglio + 3:]
                    dentro_stringa = None
                    continue
                posti = [(resto.find(q), q) for q in ('"""', "'''")
                         if resto.find(q) >= 0]
                if not posti:
                    fuori_stringa += resto
                    break
                dove, virgolette = min(posti)
                fuori_stringa += resto[:dove]
                dentro_stringa = virgolette
                resto = resto[dove + 3:]
            riga = fuori_stringa
        # ⚠ I commenti si saltano: questo file stesso, e mezzo progetto,
        #   NOMINANO i banchi nelle spiegazioni.  Un controllo che accusasse
        #   una prosa sarebbe rumore, e il rumore si impara a ignorare.
        if riga.lstrip().startswith("#"):
            riga = ""
        fuori.append((n, riga))
    return fuori


def funzioni_printf(cartella):
    """{nome funzione di shell: quel che stampa} — solo le funzioni che sono
    UNA `printf` con un formato letterale.

    ⛔⭐ `[M]` 12 agosto 2026, difetto D9.  Cinque delle sette ignote nascevano
    tutte da qui: `bersaglio_opzioni_python`, in `01-b0-bersaglio.sh:712`, che
    e' **il profilo condiviso** — `--bersaglio --porta --uscita --md5 --giro`,
    in un posto solo apposta.  B5, B6, B7 e B8 lo chiamano con `$(...)`, e
    questo controllo si fermava davanti alla parentesi.

    ⇒ Non e' un'ipotesi: il corpo della funzione e' **una riga letterale**, e
      leggerla e' una `[R]`, non una `[?]`.
    ⚠ E si ferma dov'e' giusto fermarsi: se quel corpo un giorno guadagna un
      ramo, o un secondo comando, la funzione **non si scioglie piu'** e le sue
      chiamate tornano IGNOTE.  Meglio perdere copertura che inventarla.
    """
    fuori = {}
    for nome_file in sorted(os.listdir(cartella)):
        if not nome_file.endswith(".sh"):
            continue
        righe = righe_logiche(os.path.join(cartella, nome_file))
        if righe is None:
            continue
        testi = [t for _, t in righe]
        i = 0
        while i < len(testi):
            m = re.match(r'^([a-z_][a-z0-9_]*)\(\)\s*(\{)?\s*$', testi[i])
            if not m:
                i += 1
                continue
            j = i + 1
            if m.group(2) is None:
                if j < len(testi) and testi[j].strip() == "{":
                    j += 1
                else:
                    i += 1
                    continue
            corpo = []
            while j < len(testi) and testi[j].strip() != "}":
                spoglia = testi[j].strip()
                if spoglia and not spoglia.startswith("#"):
                    corpo.append(spoglia)
                j += 1
            if len(corpo) == 1:
                mp = re.match(r"^printf\s+(?:--\s+)?'([^']*)'", corpo[0])
                if mp:
                    fuori[m.group(1)] = mp.group(1).replace("%s", "VALORE")
            i = j + 1
    return fuori


def _valore_letterale(grezzo):
    """Il valore di un'assegnazione di shell, o `None` se non lo so leggere.

    ⛔ E IL COMMENTO IN CODA FA PARTE DEL VALORE SOLO SE STA FRA VIRGOLETTE.
       `[M]` 12 agosto 2026: `01-b0-bersaglio.sh` scrive
       `B0_DENTRO=/srv/src        # lo stesso posto, come lo vede il contenitore`,
       e la prima stesura si portava dentro anche il commento.  ⇒ Sciogliendo
       `$B_COMANDO` la riga si riempiva di dodici parole di prosa, e l'ultimo
       pezzo — `$ind`, che e' il posizionale di B8 — finiva **oltre** il posto
       che gli spettava: una IGNOTA fabbricata dal lettore delle variabili.
    """
    grezzo = grezzo.strip()
    if grezzo[:1] in ('"', "'"):
        q, i, dentro = grezzo[0], 1, ""
        while i < len(grezzo):
            if grezzo[i] == "\\" and i + 1 < len(grezzo):
                dentro += grezzo[i + 1]
                i += 2
                continue
            if grezzo[i] == q:
                return dentro
            dentro += grezzo[i]
            i += 1
        return None                 # virgoletta mai chiusa: non lo so, e lo dico
    return re.split(r'\s#', grezzo, maxsplit=1)[0].strip()


def assegnazioni(righe, funzioni):
    """{NOME: valore} per le variabili di shell assegnate a un testo letterale.

    ⭐ Senza questo, il controllo guardava **un terzo** delle chiamate: i
       lanciatori costruiscono la riga a pezzi (`$COMUNE`, `$DENTRO`) e ogni
       riga con una variabile finiva fra le IGNOTE.  `[M]` 11 agosto 2026:
       28 ignote su 83 chiamate.

    ⛔⭐ E L'ORDINE DEI DUE CONTROLLI NON E' UN DETTAGLIO — `[M]` 12 agosto
    2026, difetto D9.  La prima stesura toglieva le virgolette PRIMA di
    chiedersi se il valore venisse da un comando, e il ramo che scarta i
    comandi non veniva mai raggiunto per i valori fra virgolette.
    ⇒ `QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` entrava in tabella
      **come se fosse un testo**, e da li' finiva dentro tre chiamate di
      `02-filo-lancia.sh` sciolto in `"$(cd`, `&&`, `pwd)/...`: pezzi che
      sembravano variabili sole, e **tre IGNOTE inventate dallo strumento
      stesso**.  Non erano dubbi: erano un difetto travestito da prudenza.
    """
    fuori = {}
    for riga in righe:
        m = re.match(r'^\s*([A-Z_][A-Z0-9_]*)=(.*)$', riga)
        if not m:
            continue
        nome, valore = m.group(1), _valore_letterale(m.group(2))
        if valore is None:
            continue
        valore = re.sub(r'\$\(([a-z_][a-z0-9_]*)\)',
                        lambda x: funzioni.get(x.group(1), x.group(0)), valore)
        if re.search(r'[`]|\$\(', valore):
            continue        # ⛔ viene da un comando: non lo so, e lo dico
        fuori[nome] = valore
    return fuori


def alias_banchi(righe, banchi):
    """{NOME di variabile: banco} — chi tiene il PERCORSO di un banco.

    ⛔⭐ `[M]` 12 agosto 2026, difetto D9, punto 5 del mandato: «le chiamate dei
    banchi nuovi della fase 2, se lo strumento non le vede».  Non le vedeva, e
    non perche' fossero nuove: perche' i loro lanciatori mettono il percorso in
    una variabile e poi lanciano `python3 -u "$GIUDICE" ...`.  Il nome del
    banco **non compare sulla riga del lancio**, e il controllo cercava li'.

    Restavano fuori, in silenzio: `02-cattura-giudica.py` (F2.2, per due
    lanciatori), `02-sessione-stato.py` (F2.1), `01-p5-registro.py` e
    `01-c2-diagnosi.py`.  ⚠ Non erano ignote: erano **assenti dal
    denominatore**, che e' peggio — «0 rotte su 52» faceva credere di aver
    guardato cinquantadue cose.

    ⚠ Il nome del file e' LETTERALE nell'assegnazione, anche quando il resto
      del valore non lo e': `GIUDICE=$SRC/02-cattura-giudica.py`.  E' quello
      che si legge, ed e' una `[R]`.
    ⚠ Con `${STRUMENTO:-...}` si legge il valore di riserva, cioe' quel che il
      file dice: chi esporta la variabile lancia un altro programma, e questo
      controllo non lo puo' sapere.
    """
    fuori = {}
    for _, riga in righe:
        m = re.match(r'^\s*(?:local\s+|export\s+)?'
                     r'([A-Za-z_][A-Za-z0-9_]*)=(.*)$', riga)
        if not m:
            continue
        for banco in banchi:
            if banco in m.group(2):
                fuori[m.group(1)] = banco
                break
    return fuori


def applica_alias(riga, alias):
    for nome, banco in alias.items():
        riga = re.sub(r'\$\{%s\}|\$%s(?![A-Za-z0-9_])' % (nome, nome),
                      banco.replace("\\", "\\\\"), riga)
    return riga


def sciogli(testo, tabella, funzioni):
    """Sostituisce `$(funzione)`, `$VAR` e `${VAR}`, al massimo tre giri."""
    for _ in range(3):
        prima = testo
        testo = re.sub(r'\$\(([a-z_][a-z0-9_]*)\)',
                       lambda m: funzioni.get(m.group(1), m.group(0)), testo)
        testo = re.sub(r'\$\{?([A-Z_][A-Z0-9_]*)\}?',
                       lambda m: tabella.get(m.group(1), m.group(0)), testo)
        if testo == prima:
            break
    return testo


# ---------------------------------------------------------------------------
#  Spezzare una riga di comando come la spezzerebbe la shell
# ---------------------------------------------------------------------------
FINE = re.compile(r'^([0-9]?[<>]|\||;|&&|\|\|)')


def pezzi_shell(coda):
    """I pezzi della riga di comando, con le virgolette rispettate.

    ⛔ `[M]` 12 agosto 2026: spezzando sugli spazi, il valore JSON che
       `01-p5-lancia.sh:876` passa a `--registra` diventava otto pezzi, e due
       di quegli otto cominciavano per `$`: due IGNOTE nate dal coltello, non
       dal codice guardato.  Un `$(...)` con dentro degli spazi e' un pezzo
       solo, e cosi' una stringa fra virgolette.
    ⛔ E ci si ferma dove finisce il comando — `|`, `>`, `;`, `&&` — invece di
       tagliare il testo prima di leggerlo: tagliare prima spezzava a meta' i
       `$( ... | ... )`.
    """
    pezzi, corrente, i, aperto, iniziato = [], "", 0, None, False
    while i < len(coda):
        c = coda[i]
        if c == "\\" and i + 1 < len(coda):
            corrente += coda[i:i + 2]
            iniziato = True
            i += 2
            continue
        if coda.startswith("$(", i):
            profondita, j = 0, i
            while j < len(coda):
                if coda[j] == "(":
                    profondita += 1
                elif coda[j] == ")":
                    profondita -= 1
                    if profondita == 0:
                        j += 1
                        break
                j += 1
            corrente += coda[i:j]
            iniziato = True
            i = j
            continue
        if aperto:
            if c == aperto:
                aperto = None
            else:
                corrente += c
            i += 1
            continue
        if c in ('"', "'"):
            aperto = c
            iniziato = True
            i += 1
            continue
        if c.isspace():
            if iniziato:
                pezzi.append(corrente)
            corrente, iniziato = "", False
            i += 1
            continue
        if FINE.match(coda[i:]):
            break
        corrente += c
        iniziato = True
        i += 1
    if iniziato:
        pezzi.append(corrente)
    return pezzi


def taglia_coda(testa, coda):
    """Toglie da `coda` le virgolette che restavano aperte nella `testa`.

    Due forme, e vanno distinte o si perde la riga:
      `python3 "$QUI/banco.py" --uscita X`  ⇒ la virgoletta CHIUDE il percorso,
          e la coda comincia proprio con lei: si butta quella e basta.
      `bash enter.sh --root "python3 $D/banco.py --solo X"`  ⇒ la virgoletta
          chiude **tutto il comando**: il comando finisce li'.
    """
    for q in ('"', "'"):
        aperte = testa.count(q) - testa.count("\\" + q)
        if aperte % 2 == 0:
            continue
        if coda.startswith(q):
            coda = coda[1:]
            continue
        taglio = 0
        while taglio < len(coda):
            if coda[taglio] == "\\":
                taglio += 2
                continue
            if coda[taglio] == q:
                return coda[:taglio]
            taglio += 1
    return coda


# ---------------------------------------------------------------------------
#  Giudicare una chiamata
# ---------------------------------------------------------------------------
def giudica(profilo, pezzi):
    """(opzioni citate, sotto-comando, motivo dell'IGNOTO o None).

    ⛔⭐ UNA VARIABILE NON SCIOLTA NON RENDE IGNOTA TUTTA LA RIGA, e la
    distinzione decide se questo controllo serve o no.

    `[M]` 11 agosto 2026: con «c'e' un `$` ⇒ IGNOTA» erano ignote 26 righe su
    34 — ⛔ **compresa quella che aveva appena rotto B7**
    (`01-b12-lancia.sh:430`), che porta un `$passo` dentro il valore di
    `--registro`.  Un controllo nato da un difetto che poi non vede quel
    difetto e' un controllo che si dichiara prudente e non guarda niente.

    ⭐ La domanda giusta non e' «c'e' una variabile», e' **«quella variabile
       puo' nascondere il nome di un'opzione?»**.

    ⛔⭐ E `[M]` 12 agosto 2026, difetto D9: «il pezzo prima comincia per `--`»
    era una risposta troppo grossolana, e teneva ignote quattro chiamate sane.
    Argparse conta i posti: `--confronta` con `nargs=2` si porta via DUE
    valori (`02-codifica-lancia.sh:419`), `--storpia` TRE (`:458`), e dopo le
    opzioni resta il posto degli argomenti POSIZIONALI — dove `01-b8-sblocca.py`
    aspetta un indirizzo, ed e' quello che `01-b0-bersaglio.sh:689` e
    `01-p5-ff-lancia.sh:138` gli passavano.  In un posto che aspetta un valore,
    una variabile e' un valore: la si giudica, non la si teme.
    """
    opz, attesi, posti, sotto = set(), 0, 0, None
    cerco_sotto = bool(profilo.sotto)
    for pezzo in pezzi:
        # ⛔ Le barre di protezione si tolgono PRIMA di leggere il pezzo.
        #    `[M]` 12 agosto 2026: `01-p5-lancia.sh:599` sta dentro un comando
        #    dentro un `ssh`, e scrive `--ping\"`.  Il pezzo arrivava qui come
        #    `--ping\` e il controllo accusava B8 di non conoscere `--ping` —
        #    che invece dichiara a riga 503.  ⭐ Un rosso su codice sano vale
        #    meno di zero: fa perdere fiducia anche nei rossi veri.
        nudo = re.sub(r'\\(.)', r'\1', pezzo).strip("\"'").rstrip("\\")
        if re.match(r'^\$[\*@]|^\$\{[\*@]', nudo):
            return opz, sotto, "PASSAGGIO"
        if nudo.startswith("--") and len(nudo) > 2:
            nome = nudo.split("=", 1)[0]
            opz.add(nome)
            attesi = 0 if "=" in nudo else profilo.arita.get(nome, 1)
            continue
        if attesi:
            if attesi > 0:
                attesi -= 1
            continue
        if cerco_sotto and sotto is None:
            if nudo.startswith("$"):
                return opz, sotto, "SOTTOCOMANDO"
            if nudo in profilo.sotto:
                sotto = nudo
                continue
        posti += 1
        if nudo.startswith("$"):
            limite = profilo.posiz
            if sotto is not None:
                suoi = profilo.sotto[sotto][2]
                limite = -1 if (limite < 0 or suoi < 0) else limite + suoi
            if limite < 0 or posti <= limite:
                continue
            return opz, sotto, "VARIABILE-SOLA"
    return opz, sotto, None


def chiamate(percorso, banchi, funzioni):
    """[(banco, opzioni, sotto, motivo, numero, riga)] trovate in `percorso`."""
    righe = testo_utile(percorso)
    if righe is None:
        return []
    tabella = assegnazioni([t for _, t in righe], funzioni)
    alias = alias_banchi(righe, banchi)
    fuori = []
    for n, originale in righe:
        if not originale.strip():
            continue
        riga = applica_alias(originale, alias)
        for banco in banchi:
            if banco not in riga:
                continue
            testa, coda = riga.split(banco, 1)
            # ⛔ Dev'essere un LANCIO, non una citazione: il progetto nomina i
            #    banchi dappertutto, anche dentro stringhe normali che lo
            #    stacco delle virgolette lunghe non prende.  `[M]` 11 agosto:
            #    senza questa riga il controllo accusava `01-b12-guasti.py:398`,
            #    che e' una frase.
            # ⛔ E i FLAG dell'interprete vanno previsti: `python3 -u ...` e' la
            #    forma che meta' dei lanciatori usa.  `[M]` 11 agosto 2026: una
            #    prima stesura chiedeva `python3` **attaccato** al percorso e
            #    faceva sparire quelle chiamate **in silenzio** — le viste sono
            #    passate da 83 a 22 e il conto sembrava solo piu' pulito.
            #    ⭐ Una copertura che cala senza dirlo e' la stessa cosa di un
            #    banco che smette di guardare: si vede solo se si guarda il
            #    denominatore (`LEZIONI.md` §1.9 regola 6).
            # ⚠ `python3 - "$REG" ...` non entra qui, ed e' giusto: legge il
            #   programma dallo stdin e il banco gli e' solo un argomento.
            if not re.search(r'python3?\s+(-\S+\s+)*\S*$', testa):
                continue
            # ⛔ E in un file Python un accento grave non e' sintassi: e' PROSA.
            #    `[M]` 12 agosto 2026: `02-filo-cliente.py:456` e `:506` sono
            #    due `print` che suggeriscono all'utente
            #    «`python3 02-filo-fotogramma.py --elenco`», e il controllo le
            #    leggeva come chiamate — con l'accento grave attaccato
            #    all'opzione, per giunta.  In `.sh` un accento grave e' invece
            #    una sostituzione di comando, e li' la riga si guarda.
            if percorso.endswith(".py") and re.search(
                    r'`\s*python3?\s+(-\S+\s+)*\S*$', testa):
                continue
            coda = taglia_coda(testa, coda)
            coda = sciogli(coda, tabella, funzioni)
            opz, sotto, motivo = giudica(banchi[banco], pezzi_shell(coda))
            fuori.append((banco, opz, sotto, motivo, n, originale.strip()))
    return fuori


# ---------------------------------------------------------------------------
#  Il giro
# ---------------------------------------------------------------------------
Esito = collections.namedtuple(
    "Esito", "banchi guai viste approvate mancanti sconosciute ignoti muti")


def leggi_banchi(cartella, escludi=()):
    banchi, guai = {}, []
    for nome in sorted(os.listdir(cartella)):
        if not nome.endswith(".py") or nome in escludi:
            continue
        profilo = opzioni_di(os.path.join(cartella, nome))
        if profilo is None:
            guai.append(nome)
            continue
        # ⛔⭐ LE OPZIONI DEL PROFILO CONDIVISO CONTANO COME SUE — e senza
        #     questo il controllo accusava sei chiamate sane.
        #
        # `01-b0-bersaglio.py` e' un modulo comune: i banchi non dichiarano
        # `--bersaglio` da se', se lo fanno aggiungere da li' (`b0.aggiungi`,
        # caricato con `importlib`).  Leggendo solo il file del banco,
        # `--bersaglio` risultava **sconosciuto** — e il controllo scriveva
        # «passa un'opzione che il banco non conosce» proprio sulle righe
        # appena curate.
        # ⚠ E' la forma opposta del difetto che questo file cerca, nata nello
        #   stesso file nella stessa ora: un rosso su codice sano.
        # ⛔ Un file SENZA argparse non e' un banco che «pretende» qualcosa:
        #    non c'e' niente da confrontare, e ogni suo argomento e' un
        #    posizionale che questo strumento non puo' contare.
        #    `[M]` 12 agosto 2026: `01-p5-raccogli.py` legge la porta da
        #    `sys.argv[1]` e non ha un solo `add_argument` — ma **nomina**
        #    `01-b0-bersaglio.py` nella sua spiegazione, e la riga qui sotto lo
        #    promuoveva a banco con le opzioni del modulo comune.  ⇒ Due sue
        #    chiamate sane finivano fra le IGNOTE per un obbligo che non ha.
        if not profilo.tutte:
            continue
        with open(os.path.join(cartella, nome), encoding="utf-8",
                  errors="ignore") as f:
            sorgente = f.read()
        for aiuto in sorted(os.listdir(cartella)):
            if not (aiuto.startswith("01-b0-") and aiuto.endswith(".py")
                    and aiuto != nome and aiuto[:-3] in sorgente):
                continue
            suo = opzioni_di(os.path.join(cartella, aiuto))
            if suo is None or not suo.tutte:
                continue
            profilo = profilo._replace(tutte=profilo.tutte | suo.tutte,
                                       arita={**suo.arita, **profilo.arita})
            # ⛔⭐ E ANCHE LE SUE **OBBLIGATORIE**, che alla prima stesura
            #     non prendevo — ed e' il difetto piu' istruttivo di questo
            #     file, perche' l'ho fatto **curando i falsi positivi**.
            #
            # `[M]` 11 agosto 2026, un'ora dopo aver scritto questo
            # controllo: la riga che avevo appena aggiunto in
            # `01-b12-lancia.sh` per B6 era senza `--bersaglio`, e il
            # controllo l'ha dichiarata **approvata**.  `--bersaglio` non
            # e' dichiarato dal banco: glielo aggiunge `b0.aggiungi_
            # argomenti(p)`, e io avevo unito le opzioni **ammesse** dal
            # modulo comune senza unire quelle **pretese**.
            # ⇒ Il giro di certificazione ha scritto «B6 NON certificato»
            #   su un errore mio, che lo strumento nato per trovarlo aveva
            #   guardato e approvato.
            # ⭐ La lezione non e' la riga mancante: e' che **allargare le
            #   maglie per far tacere i falsi si porta via i veri nella
            #   stessa mossa**, e non lo si vede perche' il conto dei rossi
            #   scende — che e' precisamente l'aspetto di un progresso.
            if suo.obb and "aggiungi_argomenti" in sorgente:
                profilo = profilo._replace(obb=profilo.obb | suo.obb)
        if profilo.tutte:
            banchi[nome] = profilo
    return banchi, guai


def analizza(cartella, escludi=()):
    banchi, guai = leggi_banchi(cartella, escludi)
    funzioni = funzioni_printf(cartella)
    chiamanti = [n for n in sorted(os.listdir(cartella))
                 if n.endswith((".sh", ".py")) and n not in escludi]
    mancanti, sconosciute, ignoti, muti, viste, approvate = [], [], [], [], 0, 0
    for chi in chiamanti:
        for banco, opz, sotto, motivo, n, riga in chiamate(
                os.path.join(cartella, chi), banchi, funzioni):
            profilo = banchi[banco]
            # ⛔ Una chiamata senza NESSUNA opzione e senza sotto-comando quasi
            #    sempre e' una citazione in una stringa di aiuto, non un
            #    lancio.  Non si giudica — e lo si DICHIARA, con il suo numero,
            #    invece di sembrare esaustivi.
            # ⛔⭐ MA SOLO SE IL BANCO NON PRETENDE NIENTE.  `[M]` 12 agosto
            #    2026, provato mutando `02-filo-validatore.py` per fargli
            #    pretendere `--uscita`: le due chiamate di `02-filo-lancia.sh`
            #    che non gliela passano **non diventavano rosse**, perche'
            #    «nessuna opzione» le faceva scartare prima di guardarle.
            #    ⇒ La scorciatoia contro il rumore si era mangiata il caso
            #    esatto per cui questo file esiste: un chiamante rimasto
            #    indietro su un obbligatorio.
            if (not opz and not sotto and motivo is None
                    and not profilo.obb):
                muti.append((chi, n, banco))
                continue
            viste += 1
            if motivo:
                ignoti.append((chi, n, banco, motivo, riga))
                continue
            obb = profilo.obb | (set(profilo.sotto[sotto][0]) if sotto else set())
            # ⛔ Una scorciatoia E' una dichiarazione: `if "--elenco" in
            #    sys.argv` non passa da `add_argument`, ma il banco quell'opzione
            #    la conosce eccome.  `[M]` 12 agosto 2026: senza questa riga il
            #    controllo positivo qui sotto legge `--elenco` come «opzione che
            #    il banco non conosce» — un rosso su una riga sana, ed e' la
            #    stessa forma pagata l'11 agosto sul modulo comune.
            tutte = profilo.tutte | profilo.corte
            # ⭐ Con una scorciatoia in mano, gli obbligatori non si pretendono.
            perse = set() if (opz & profilo.corte) else obb - opz
            strane = {o for o in opz if o not in tutte and o != "--root"}
            if perse:
                mancanti.append((chi, n, banco, sorted(perse), riga))
            if strane:
                sconosciute.append((chi, n, banco, sorted(strane), riga))
            if not perse and not strane:
                approvate += 1
    return Esito(banchi, guai, viste, approvate, mancanti, sconosciute,
                 ignoti, muti)


# ---------------------------------------------------------------------------
#  ⭐ IL CONTROLLO POSITIVO — «questo strumento sa vedere una chiamata rotta?»
# ---------------------------------------------------------------------------
BANCO_COMUNE = '''\
"""01-b0-finto-comune.py — il profilo condiviso, finto, del controllo positivo."""


def aggiungi_argomenti(p):
    p.add_argument("--bersaglio", required=True)
'''

BANCO_FINTO = '''\
"""01-bz-finto.py — il banco finto del controllo positivo di 01-b0-chiamate.py.

Pretende `--bersaglio` dal modulo comune 01-b0-finto-comune e `--porta` da se'.
"""
import argparse
import importlib.util
import os
import sys

_s = importlib.util.spec_from_file_location(
    "comune", os.path.join(os.path.dirname(__file__), "01-b0-finto-comune.py"))
comune = importlib.util.module_from_spec(_s)
_s.loader.exec_module(comune)


def principale():
    if "--elenco" in sys.argv:
        print("il catalogo, e me ne vado")
        return 0
    p = argparse.ArgumentParser()
    comune.aggiungi_argomenti(p)
    p.add_argument("--porta", required=True)
    p.add_argument("--nota")
    p.add_argument("bersagliato", nargs="?")
    p.parse_args()
    return 0
'''

CHIAMANTE_FINTO = '''\
#!/bin/sh
# Il chiamante guasto apposta.  Ogni riga porta scritto che cosa DEVE uscire.
QUI=/finto
STRUM=$QUI/01-bz-finto.py

finte_opzioni()
{
	printf -- '--bersaglio %s --porta %s' "$A" "$B"
}

# 1 — SANA
python3 $QUI/01-bz-finto.py --bersaglio prova --porta 7500 --nota ciao

# 2 — ROTTA: manca --porta, che il banco pretende
python3 $QUI/01-bz-finto.py --bersaglio prova --nota ciao

# 3 — ROTTA: manca --bersaglio, che arriva dal modulo comune
python3 $QUI/01-bz-finto.py --porta 7500

# 4 — ROTTA: un'opzione che il banco non conosce
python3 $QUI/01-bz-finto.py --bersaglio prova --porta 7500 --inventata 1

# 5 — IGNOTA (PASSAGGIO): gli argomenti arrivano da fuori
python3 $QUI/01-bz-finto.py --bersaglio prova --porta 7500 $*

# 6 — SANA: variabili nei posti dove argparse aspetta VALORI
python3 $QUI/01-bz-finto.py --bersaglio $B --porta $P $IND

# 7 — SANA: la scorciatoia, che non pretende gli obbligatori
python3 $QUI/01-bz-finto.py --elenco

# 8 — SANA: il banco tenuto in una variabile, e la riga spezzata
python3 -u "$STRUM" \\
	--bersaglio prova --porta 7500

# 9 — SANA: le opzioni escono da una funzione di shell
python3 $QUI/01-bz-finto.py $(finte_opzioni) --nota x
'''

ATTESO = {"viste": 9, "approvate": 5, "mancanti": 2, "sconosciute": 1,
          "ignoti": 1}


def autoprova(chiasso=True):
    """⭐ Costruisce un banco finto e un chiamante ROTTO APPOSTA, e verifica che
    lo strumento li veda.

    ⛔ `[M]` 12 agosto 2026, difetto D9 punto 4: prima di oggi questo controllo
    non c'era, e senza di lui «0 rotte» non distingue *«tutto a posto»* da
    *«non sto guardando»* — che e' la forma **E8** applicata allo strumento
    invece che al codice.  Un `--bersaglio` scomparso dal profilo condiviso, o
    una espressione regolare che smette di riconoscere `python3 -u`, farebbero
    scendere il conto dei rossi a zero: **l'aspetto di un progresso**.

    ⚠ Le nove righe non sono decorative: sono le forme gia' pagate.  La 2 e la
      3 sono i difetti veri del 10 e dell'11 agosto (un obbligatorio del banco,
      un obbligatorio del modulo comune); la 4 e' il `--sorgente` che non
      esisteva piu'; la 5 e' l'unico ignoto che resta ingiudicabile; la 6, la 8
      e la 9 sono le tre abilita' aggiunte oggi, e senza di loro qui si
      rileggerebbero come guaste.
    """
    cartella = tempfile.mkdtemp(prefix="b0-chiamate-autoprova-")
    try:
        for nome, testo in (("01-b0-finto-comune.py", BANCO_COMUNE),
                            ("01-bz-finto.py", BANCO_FINTO),
                            ("01-bz-chiama.sh", CHIAMANTE_FINTO)):
            with open(os.path.join(cartella, nome), "w", encoding="utf-8") as f:
                f.write(testo)
        e = analizza(cartella)
        avuto = {"viste": e.viste, "approvate": e.approvate,
                 "mancanti": len(e.mancanti),
                 "sconosciute": len(e.sconosciute), "ignoti": len(e.ignoti)}
    finally:
        shutil.rmtree(cartella, ignore_errors=True)

    if chiasso:
        print(f"\n{NETTO}== ⭐ IL CONTROLLO POSITIVO — «so vedere una chiamata "
              f"DAVVERO rotta?»{GRIGIO}")
        print("    nove chiamate finte: 2 senza un obbligatorio, 1 con "
              "un'opzione che non esiste,")
        print("    1 ingiudicabile per costruzione, 5 sane.")
    guasti = [k for k in ATTESO if ATTESO[k] != avuto[k]]
    if guasti:
        if chiasso:
            for k in sorted(avuto):
                segno = ROSSO if k in guasti else VERDE
                print(f"    {segno}{avuto[k]:3d}{GRIGIO}  {k} "
                      f"(atteso {ATTESO[k]})")
            for chi, n, banco, motivo, riga in e.ignoti:
                print(f"        ignota {chi}:{n} → {banco} [{motivo}]")
            print(f"  {ROSSO}⛔ LO STRUMENTO NON VEDE QUEL CHE DEVE VEDERE: "
                  f"il verde qui sopra NON VALE{GRIGIO}")
        return False
    if chiasso:
        print(f"    {VERDE}tutt'e nove lette come dovevano{GRIGIO}: "
              f"{avuto['mancanti']} senza un obbligatorio, "
              f"{avuto['sconosciute']} con un'opzione ignota, "
              f"{avuto['ignoti']} IGNOTA, {avuto['approvate']} approvate.")
    return True


# ---------------------------------------------------------------------------
def giro(elenco_solo=False):
    if elenco_solo:
        banchi, _ = leggi_banchi(QUI, escludi=(os.path.basename(__file__),))
        print(f"{NETTO}== Che cosa pretende ogni banco{GRIGIO}\n")
        for nome, p in banchi.items():
            if p.obb:
                print(f"  {nome}\n     ⛔ obbligatorie: {', '.join(sorted(p.obb))}")
            for sotto, (obb, _t, _pz) in sorted(p.sotto.items()):
                if obb:
                    print(f"  {nome} {sotto}\n     ⛔ obbligatorie: "
                          f"{', '.join(sorted(obb))}")
        return 0

    e = analizza(QUI, escludi=(os.path.basename(__file__),))
    con_obblighi = [n for n, p in e.banchi.items()
                    if p.obb or any(s[0] for s in p.sotto.values())]
    print(f"{NETTO}== ⛔ Chi chiama un banco gli passa quel che il banco "
          f"pretende?{GRIGIO}")
    print(f"   {len(e.banchi)} banchi letti, {len(con_obblighi)} con almeno un "
          f"argomento obbligatorio.")
    # ⛔ Un banco che non si riesce a leggere SPARISCE dal denominatore, e con
    #    lui spariscono tutte le sue chiamate — in silenzio, e il conto dei
    #    rossi scende.  `[M]` 12 agosto 2026: e' capitato provando lo strumento
    #    con una mutazione mal scritta, e per un giro ho creduto a un verde.
    for nome in e.guai:
        print(f"    {GIALLO}?{GRIGIO}  {nome}: ⛔ non si e' potuto leggere "
              f"(sintassi?) — le sue chiamate NON sono guardate")
    print()

    for chi, n, banco, perse, riga in e.mancanti:
        print(f"  {ROSSO}NO{GRIGIO}  {chi}:{n} chiama {banco} SENZA "
              f"{', '.join(perse)}")
        print(f"        ⛔ il banco si rifiutera' di partire, e il giro "
              f"leggera' un ROSSO che non e' suo")
        print(f"        {riga[:150]}")
    for chi, n, banco, strane, riga in e.sconosciute:
        print(f"  {ROSSO}NO{GRIGIO}  {chi}:{n} passa a {banco} "
              f"{', '.join(strane)}, che il banco non conosce")
        print(f"        {riga[:150]}")

    if e.ignoti:
        per_motivo = collections.defaultdict(list)
        for chi, n, banco, motivo, riga in e.ignoti:
            per_motivo[motivo].append((chi, n, banco))
        print(f"\n  {GIALLO}?{GRIGIO}  {len(e.ignoti)} chiamate IGNOTE — ⛔ non "
              f"approvate, e ognuna con il suo perche':")
        for motivo in sorted(per_motivo):
            print(f"\n     {GIALLO}{motivo}{GRIGIO} — {MOTIVI[motivo]}")
            for chi, n, banco in per_motivo[motivo]:
                print(f"        {chi}:{n} → {banco}")

    print(f"\n    == quel che questo giro ha davvero guardato")
    print(f"    --  chiamate con almeno un'opzione o un sotto-comando: "
          f"{e.viste}")
    print(f"    {VERDE}{e.approvate:3d}{GRIGIO}  approvate")
    print(f"    {ROSSO}{len(e.mancanti) + len(e.sconosciute):3d}{GRIGIO}  "
          f"⛔ rotte")
    print(f"    {GIALLO}{len(e.ignoti):3d}{GRIGIO}  ⚠ IGNOTE — non sono un "
          f"rosso e non sono un verde (i motivi qui sopra)")
    print(f"    --  e {len(e.muti)} righe che NOMINANO un banco senza passargli "
          f"niente: non sono chiamate da giudicare,")
    print(f"        e non entrano nel conto — dichiarate per non far sembrare "
          f"il denominatore piu' grande di quel che e'.")

    sano = autoprova()
    if e.viste == 0:
        print(f"    {ROSSO}⛔ ZERO chiamate guardate: questo giro non dice "
              f"niente, e «nessun problema trovato» sarebbe una bugia{GRIGIO}")
        return 2
    if not sano:
        return 2
    return 1 if (e.mancanti or e.sconosciute) else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--elenco", action="store_true",
                   help="che cosa pretende ogni banco, e basta")
    p.add_argument("--autoprova", action="store_true",
                   help="⭐ solo il controllo positivo dello strumento")
    a = p.parse_args()
    if a.autoprova:
        sys.exit(0 if autoprova() else 2)
    sys.exit(giro(a.elenco))
