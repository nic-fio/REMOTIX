#!/usr/bin/env python3
"""00-ancore.py — ⛔ LE ANCORE DEI GUASTI INNESTATI SONO ANCORA VIVE?

    python3 banchi/00-ancore.py               tutte, e l'uscita vale
    python3 banchi/00-ancore.py --vive         mostra anche quelle vive
    python3 banchi/00-ancore.py --solo 06-b33  un innestatore solo
    python3 banchi/00-ancore.py --json         una riga JSON per ancora

USCITA:  0 = tutte vive (o cieche dichiarate) · 1 = almeno una MORTA o
         AMBIGUA · 2 = l'attrezzo stesso non ha potuto lavorare.

===========================================================================
⛔ PERCHE' ESISTE — UN'ANCORA SCADE IN SILENZIO
===========================================================================

Un controllo positivo si fa innestando un guasto in una COPIA del prodotto:
lo script cerca una riga o un blocco — **l'ancora** — la sostituisce, e
pretende che il banco diventi rosso nel caso dichiarato.  ⛔ Ma il prodotto
cambia sotto le ancore, e quando l'ancora non combacia piu' il guasto **non
si innesta**: il banco resta verde, e quel verde non prova piu' niente.

E' gia' costato due volte:

  · `04-b31-certifica.sh` — fra le due funzioni che l'ancora di `G8`
    nominava e' nata `rcp_tela_rimanda()`.  Dal 16 agosto 2026 **il piu'
    grave dei dodici guasti non si innestava piu'**.  Il certificatore lo
    diceva con `??`, e nessuno lo lanciava.

  · `06-b34-guasti.sh` — l'ancora del guasto `B` era **nata scaduta**: la
    cura e il guasto che doveva provarla sono entrati nello stesso commit e
    il guasto non e' mai stato rilanciato.  ⇒ Il caso 4b, col rapporto
    danno/costo piu' alto di `RCP.md`, non aveva **nessun** controllo
    positivo.

⇒ In tutt'e due i casi la diagnosi c'era e nessuno la leggeva.  Questo
  attrezzo la legge **senza lanciare i banchi**: e' di sola lettura, gira in
  locale in un secondo, e si puo' mettere davanti a un commit.

===========================================================================
⛔ LE TRE RISPOSTE, E PERCHE' SONO TRE E NON DUE
===========================================================================

  VIVA      l'ancora compare **esattamente una volta** nel sorgente di
            adesso: il guasto si innesta dove e' scritto che si innesti.

  MORTA     zero occorrenze.  Il guasto non si innesta piu' e il caso che
            doveva provare **non ha piu' nessun controllo positivo**.

  AMBIGUA   due o piu' occorrenze.  ⛔ E' **peggio** di morta: gli
            innestatori scritti bene si rifiutano (`06-b33-guasti.py`,
            `06-b35-guasti.py`), ma quelli che chiamano `replace()` senza
            contare innestano in un posto a caso, o in due posti insieme.

  CIECA     il file non c'e' su questa macchina (gli alberi di fase 1 vivono
            su `/media/REMOTIX`).  ⛔ **Non e' morta**, ed e' la distinzione
            che tiene in piedi questo attrezzo: un attrezzo che dichiarasse
            morte le ancore che non ha potuto guardare sarebbe peggio del
            problema che cura — `LEZIONI.md` §1.20 applicata a se stesso.

===========================================================================
⛔ COME SI LEGGONO LE ANCORE — NON CON UN `grep` MIO
===========================================================================

Le ancore sono spesso blocchi di piu' righe, con tabulazioni e commenti in
mezzo.  ⚠ Un confronto «a modo mio» dichiarerebbe morte delle ancore vive.
⇒ Qui ogni ancora si estrae **dal codice dell'innestatore**, nella forma in
  cui l'innestatore la scrive:

  · gli innestatori in Python: si legge il loro albero sintattico (`ast`) e
    si prende il letterale della loro tabella dei guasti — **le stesse
    identiche stringhe** che passerebbero a `str.count()`;
  · gli innestatori in shell che portano dentro un Python (`<<'PITONE'`): si
    ritaglia il documento-qui e gli si fa la stessa cosa;
  · `05-b1-certifica.sh` innesta con `sed`: li' l'ancora e' un'espressione
    regolare ancorata a `^…$`, e si conta con `re` in modo multiriga —
    perche' e' cosi' che la conta `sed`.

⇒ Aggiungere un innestatore vuol dire aggiungere una voce a `INNESTATORI`.
  ⚠ Se la sua tabella cambia forma, l'estrattore **fallisce rumorosamente**
    (uscita 2) invece di dichiarare zero ancore: zero ancore trovate e' il
    modo in cui un attrezzo come questo mente.
"""
import argparse
import ast
import json
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)


# ===========================================================================
# ⛔⛔ `sed` NON PARLA LA LINGUA DI `re`, E CREDERLO E' IL PRIMO FALSO ALLARME
#     CHE QUESTO ATTREZZO HA DATO — 22 agosto 2026, durante la sua scrittura.
#
#     Le tre ancore di `05-b1-certifica.sh` sono espressioni `sed`, cioe' BRE.
#     Date a `re` cosi' com'erano, `^\t\tif (!seat || !\*seat)$` diventava
#     «`if ` seguito da un GRUPPO che vale `!seat ` oppure ` !*seat`», che nel
#     file non c'e' ⇒ l'attrezzo dichiarava MORTE tre ancore **vive**
#     (`src/sentinella.c:192, 190, 125` ci sono tutt'e tre).
#
# ⇒ Nelle BRE `( ) { } | + ?` sono LETTERALI, e sono le versioni con la barra
#   — `\( \) \{ \} \| \+ \?` — a essere speciali (estensioni GNU).  Qui si
#   traduce, invece di sperare che coincidano.
# ===========================================================================
_BRE_NUDI = "(){}|+?"
_BRE_CON_BARRA = {"(": "(", ")": ")", "{": "{", "}": "}",
                  "|": "|", "+": "+", "?": "?"}


def bre_a_python(bre):
    fuori = []
    i = 0
    while i < len(bre):
        c = bre[i]
        if c == "\\" and i + 1 < len(bre):
            d = bre[i + 1]
            if d in _BRE_CON_BARRA:
                fuori.append(_BRE_CON_BARRA[d])       # \( → (  : speciale
            else:
                fuori.append("\\" + d)                # \* \t \. … invariati
            i += 2
            continue
        if c in _BRE_NUDI:
            fuori.append("\\" + c)                    # ( → \(  : letterale
        else:
            fuori.append(c)
        i += 1
    return "".join(fuori)


# ===========================================================================
# L'ancora
# ===========================================================================
class Ancora:
    def __init__(self, banco, guasto, file_rel, testo, caso="", tipo="letterale"):
        self.banco = banco          # chi innesta
        self.guasto = guasto        # il nome del guasto
        self.file_rel = file_rel    # il file bersaglio, dalla radice
        self.testo = testo          # l'ancora, verbatim
        self.caso = caso            # il caso che resta scoperto se e' morta
        self.tipo = tipo            # "letterale" | "regex-sed"
        self.quante = None          # None = non ho potuto guardare
        self.esito = "?"
        # ⚠ Quasi sempre 1.  ⛔ Ma non SEMPRE, e darlo per scontato sarebbe
        #   un falso allarme: `01-p5-ff-strumenta.py` dichiara per ogni patch
        #   quante volte deve attaccare, e per una di loro non e' una.
        self.molteplicita_voluta = 1

    @property
    def percorso(self):
        return os.path.join(RADICE, self.file_rel)

    def guarda(self):
        p = self.percorso
        if not os.path.isfile(p):
            self.esito = "CIECA"
            return
        try:
            with open(p, encoding="utf-8") as f:
                testo = f.read()
        except OSError as sbaglio:
            self.esito = "CIECA"
            self.caso = (self.caso + f"  [{sbaglio}]").strip()
            return
        if self.tipo == "regex-sed":
            self.quante = len(re.findall(bre_a_python(self.testo), testo,
                                         re.MULTILINE))
        else:
            self.quante = testo.count(self.testo)
        if self.quante == self.molteplicita_voluta:
            self.esito = "VIVA"
        elif self.quante == 0:
            self.esito = "MORTA"
        else:
            self.esito = "AMBIGUA"


# ===========================================================================
# ⛔ Gli attrezzi di lettura.  Nessuno di questi importa o esegue un
#    innestatore: si legge il testo e si guarda l'albero sintattico.  ⚠ Un
#    `import` girerebbe il codice di modulo di file che aprono percorsi su
#    `/media/REMOTIX` — e un attrezzo di sola lettura non deve poter fare
#    danni per sbaglio.
# ===========================================================================
class Scaduto(Exception):
    """L'estrattore non ha riconosciuto la forma della tabella."""


def _sorgente(rel):
    p = os.path.join(RADICE, rel)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def _documento_qui(testo, marca):
    """Ritaglia il corpo di un `<<'MARCA' … MARCA` (documento-qui non espanso).

    ⛔ Se ce n'e' piu' d'uno li ritorna tutti, in ordine: `06-b34-guasti.sh`
       ne ha quattro, uno per guasto.
    """
    fuori = []
    apre = re.compile(r"<<'" + re.escape(marca) + r"'\s*\n")
    chiude = re.compile(r"^" + re.escape(marca) + r"\s*$", re.MULTILINE)
    da = 0
    while True:
        m = apre.search(testo, da)
        if not m:
            break
        c = chiude.search(testo, m.end())
        if not c:
            raise Scaduto(f"documento-qui «{marca}» aperto e mai chiuso")
        fuori.append(testo[m.end():c.start()])
        da = c.end()
    if not fuori:
        raise Scaduto(f"nessun documento-qui «{marca}»")
    return fuori


def _letterale(sorgente, nome):
    """Il valore letterale assegnato a `nome` al livello del modulo."""
    albero = ast.parse(sorgente)
    for nodo in albero.body:
        if isinstance(nodo, ast.Assign):
            for b in nodo.targets:
                if isinstance(b, ast.Name) and b.id == nome:
                    try:
                        return ast.literal_eval(nodo.value)
                    except ValueError as sbaglio:
                        raise Scaduto(f"«{nome}» non e' un letterale: {sbaglio}")
    raise Scaduto(f"nessuna assegnazione a «{nome}»")


def _nodo_assegnato(sorgente, nome):
    for nodo in ast.parse(sorgente).body:
        if isinstance(nodo, ast.Assign):
            for b in nodo.targets:
                if isinstance(b, ast.Name) and b.id == nome:
                    return nodo.value
    raise Scaduto(f"nessuna assegnazione a «{nome}»")


def _campi_dizionario(sorgente, nome, campi):
    """{chiave: {campo: valore}} prendendo SOLO i campi chiesti.

    ⛔ Serve perche' un dizionario di guasti puo' avere campi che non sono
       letterali (`03-b18-innesta.py` costruisce `mette` con `MARCA + …`):
       leggere tutto fallirebbe su un campo che non c'entra, e l'ancora —
       che e' un letterale — andrebbe persa.
    """
    nodo = _nodo_assegnato(sorgente, nome)
    if not isinstance(nodo, ast.Dict):
        raise Scaduto(f"«{nome}» non e' un dizionario letterale")
    fuori = {}
    for chiave, valore in zip(nodo.keys, nodo.values):
        k = ast.literal_eval(chiave)
        if not isinstance(valore, ast.Dict):
            raise Scaduto(f"«{nome}[{k}]» non e' un dizionario")
        dentro = {ast.literal_eval(a): b
                  for a, b in zip(valore.keys, valore.values)}
        prese = {}
        for c in campi:
            if c in dentro:
                try:
                    prese[c] = ast.literal_eval(dentro[c])
                except ValueError:
                    prese[c] = None
        fuori[k] = prese
    return fuori


def _chiamate(sorgente, funzione):
    """Tutte le chiamate di modulo a `funzione(...)`, come (posizionali, nomi).

    ⛔ Solo argomenti letterali: quel che non e' letterale torna come
       `NONLETTERALE`, e chi legge decide se e' un problema.
    """
    def val(nodo):
        try:
            return ast.literal_eval(nodo)
        except (ValueError, TypeError, SyntaxError):
            return NONLETTERALE
    albero = ast.parse(sorgente)
    fuori = []
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                and nodo.func.id == funzione):
            fuori.append(([val(a) for a in nodo.args],
                          {k.arg: val(k.value) for k in nodo.keywords}))
    if not fuori:
        raise Scaduto(f"nessuna chiamata a «{funzione}()»")
    return fuori


NONLETTERALE = object()


# ===========================================================================
# GLI ESTRATTORI, uno per innestatore.
# ===========================================================================
def e_b33(rel):
    """06-b33-guasti.py — GUASTI = {nome: (desc, caso, cerca, metti)}"""
    g = _letterale(_sorgente(rel), "GUASTI")
    return [Ancora("06-b33", k, "src/input.c", v[2], caso=f"caso {v[1]}")
            for k, v in g.items()]


def e_b33_risveglio(rel):
    """06-b33-risveglio-guasti.py — {nome: (file, desc, casi, cerca, sost)}"""
    g = _letterale(_sorgente(rel), "GUASTI")
    return [Ancora("06-b33-risveglio", k, v[0], v[3],
                   caso=f"casi {v[2] or 'nessuno (non-guasto misurato)'}")
            for k, v in g.items()]


def e_b35(rel):
    """06-b35-guasti.py — {nome: {file, cerca, metti, atteso, regola}}"""
    g = _letterale(_sorgente(rel), "GUASTI")
    return [Ancora("06-b35", k, "src/" + v["file"], v["cerca"],
                   caso=v["regola"]) for k, v in g.items()]


def e_b23(rel):
    """04-b23-guasti.py — {nome: {cerca, metti, …}} tutto su src/rcp.c"""
    g = _letterale(_sorgente(rel), "GUASTI")
    fuori = []
    for k, v in g.items():
        if "cerca" not in v:
            raise Scaduto(f"il guasto «{k}» non ha «cerca»")
        fuori.append(Ancora("04-b23", k, "src/rcp.c", v["cerca"],
                            caso=str(v.get("caso") or v.get("dimostra", ""))[:90]))
    return fuori


def e_b18(rel):
    """03-b18-innesta.py — AGHI = {nome: {file, cerca, mette, chi_lo_vede}}.

    ⚠ `mette` non e' un letterale (si compone con `MARCA`): si prendono solo
      i campi che servono.  E l'ago si pianta nei GEMELLI — `src/rcp.c` e
      `banchi/rcp/rcp.c` devono combaciare byte per byte (R12.3) — quindi
      l'ancora si guarda in tutt'e due.
    """
    s = _sorgente(rel)
    g = _campi_dizionario(s, "AGHI", ("file", "cerca", "chi_lo_vede"))
    gemelli = _letterale(s, "GEMELLI")
    fuori = []
    for k, v in g.items():
        if not v.get("cerca"):
            raise Scaduto(f"l'ago «{k}» non ha un «cerca» letterale")
        for dove in gemelli:
            eti = k if dove == v["file"] else f"{k} (gemello)"
            fuori.append(Ancora("03-b18", eti, dove, v["cerca"],
                                caso=str(v.get("chi_lo_vede", ""))[:90]))
    return fuori


def e_b41(rel):
    """06-b41-guasto.py — ANCORA, una sola, su src/rcp.c"""
    a = _letterale(_sorgente(rel), "ANCORA")
    return [Ancora("06-b41", "senza-la-cura-di-6.4", "src/rcp.c", a,
                   caso="la misura di 6.4 (richieste incatenate) senza controllo positivo")]


def _e_pitone_rcp(banco, rel, marca):
    """04-b31 e 06-b36: un documento-qui che definisce
       GUASTI = [(nome, spiega, cerca, sost, rossi)], `cerca` stringa o lista.
    """
    corpo = _documento_qui(_sorgente(rel), marca)[0]
    g = _letterale(corpo, "GUASTI")
    fuori = []
    for voce in g:
        nome, _spiega, cerca, _sost, rossi = voce
        ancore = cerca if isinstance(cerca, list) else [cerca]
        for i, a in enumerate(ancore):
            eti = nome if len(ancore) == 1 else f"{nome}[{i + 1}/{len(ancore)}]"
            fuori.append(Ancora(banco, eti, "src/rcp.c", a,
                                caso="casi rossi attesi " + str(rossi)))
    return fuori


def e_b31(rel):
    return _e_pitone_rcp("04-b31", rel, "PITONE")


def e_b36(rel):
    return _e_pitone_rcp("06-b36", rel, "PITONE")


def e_b34(rel):
    """06-b34-guasti.sh — quattro documenti-qui, ciascuno con `ancora = …`.

    ⚠ Il bersaglio si legge dalla riga `python3 - "$GUASTO/src/<file>"` che
      apre il documento-qui: e' l'unico posto dove sta scritto, e prenderlo
      da un elenco mio vorrebbe dire descrivere il copione invece di
      leggerlo.
    """
    s = _sorgente(rel)
    corpi = _documento_qui(s, "PY")
    # il file bersaglio, nell'ordine in cui i documenti-qui compaiono
    bersagli = re.findall(r'python3 - "\$GUASTO/(src/[A-Za-z0-9_.]+)" <<\'PY\'', s)
    if len(bersagli) != len(corpi):
        raise Scaduto(f"{len(corpi)} documenti-qui ma {len(bersagli)} bersagli")
    casi = re.findall(r'pretendi_rosso (\w+)', s)
    # il nome del guasto e' l'etichetta del `case` che apre il ramo
    etichette = [(m.start(), m.group(1))
                 for m in re.finditer(r"^([a-z][a-z0-9-]+)\)$", s, re.MULTILINE)]
    nomi = []
    for m in re.finditer(r"<<'PY'", s):
        prima = [e for p, e in etichette if p < m.start()]
        nomi.append(prima[-1] if prima else "?")
    fuori = []
    for i, (corpo, file_rel) in enumerate(zip(corpi, bersagli)):
        a = _letterale(corpo, "ancora")
        caso = casi[i] if i < len(casi) else "?"
        nome = nomi[i] if i < len(nomi) else f"guasto{i + 1}"
        fuori.append(Ancora("06-b34", nome, file_rel, a,
                            caso=f"il {caso} non ha piu' controllo positivo"))
    return fuori


def e_b1(rel):
    """05-b1-certifica.sh — tre `sed` su src/sentinella.c.

    ⛔ Qui l'ancora e' un'espressione REGOLARE ancorata a `^…$`, e si conta
       come la conta `sed`: riga per riga.  ⚠ E `sed` usa le BRE, dove `\\(`
       raggruppa e `(` e' letterale; le tre espressioni di oggi non hanno
       gruppi, quindi la traduzione a `re` e' fedele — se un giorno ne
       nascesse una con `\\(`, questa nota e' il posto dove accorgersene.
    """
    s = _sorgente(rel)
    righe = re.findall(
        r"innesta\s+(\d+)\s+\"([^\"]*)\"\s*\\\s*\n\s*'s@(.+?)@(.*?)@'\s+\"?([^\"\n]*)\"?",
        s)
    if not righe:
        raise Scaduto("nessuna riga `innesta N \"…\" 's@…@…@'`")
    fuori = []
    for numero, _desc, cerca, _metti, casi in righe:
        fuori.append(Ancora("05-b1", f"guasto{numero}", "src/sentinella.c",
                            cerca, caso=f"casi attesi rossi {casi.strip()}",
                            tipo="regex-sed"))
    return fuori


def e_codifica(rel):
    """02-codifica-guasti.py — {sigla: {file, appiglio, sostituto, …}}.

    Il campo `file` e' un percorso calcolato (`PRODOTTO`, `LANCIA`): si legge
    il nome della costante dall'albero sintattico invece del suo valore.
    """
    s = _sorgente(rel)
    albero = ast.parse(s)
    dove = {"PRODOTTO": "src/codificatore.c",
            "LANCIA": "banchi/02-codifica-lancia.sh",
            "NAL": "banchi/02-codifica-nal.py"}
    fuori = []
    for nodo in albero.body:
        if not (isinstance(nodo, ast.Assign)
                and any(isinstance(b, ast.Name) and b.id == "GUASTI"
                        for b in nodo.targets)):
            continue
        if not isinstance(nodo.value, ast.Dict):
            raise Scaduto("GUASTI non e' un dizionario letterale")
        for chiave, valore in zip(nodo.value.keys, nodo.value.values):
            sigla = ast.literal_eval(chiave)
            campi = {ast.literal_eval(k): v
                     for k, v in zip(valore.keys, valore.values)}
            if "appiglio" not in campi or "file" not in campi:
                raise Scaduto(f"il guasto «{sigla}» non ha appiglio/file")
            f = campi["file"]
            if not isinstance(f, ast.Name) or f.id not in dove:
                raise Scaduto(f"«{sigla}»: bersaglio ignoto {ast.dump(f)[:60]}")
            fuori.append(Ancora("02-codifica", sigla, dove[f.id],
                                ast.literal_eval(campi["appiglio"]),
                                caso=ast.literal_eval(campi.get(
                                    "sigla", ast.Constant(sigla)))))
        return fuori
    raise Scaduto("nessun GUASTI")


def e_pagina_vista(rel):
    """02-pagina-vista-prova.py — GUASTI = {nome: [(cerca, metti), …]}"""
    g = _letterale(_sorgente(rel), "GUASTI")
    fuori = []
    for nome, coppie in g.items():
        for i, (cerca, _metti) in enumerate(coppie):
            eti = nome if len(coppie) == 1 else f"{nome}[{i + 1}/{len(coppie)}]"
            fuori.append(Ancora("02-pagina-vista", eti, "src/pagina.html",
                                cerca, caso=f"il giro guasto «{nome}»"))
    return fuori


def e_p5_ritiro(rel):
    """01-p5-guasto-ritiro.py — un'ancora sola (`SANO`) su src/pagina.html"""
    a = _letterale(_sorgente(rel), "SANO")
    return [Ancora("01-p5-ritiro", "P5-ritiro", "src/pagina.html", a,
                   caso="RCP.md §4.1-bis: il RITIRO dell'impronta")]


def e_b38(rel):
    """06-b38-registratore.py — `ancore = [(vecchio, nuovo), …]` dentro una
       funzione, sul validatore di B4."""
    s = _sorgente(rel)
    albero = ast.parse(s)
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.Assign)
                and any(isinstance(b, ast.Name) and b.id == "ancore"
                        for b in nodo.targets)):
            coppie = ast.literal_eval(nodo.value)
            return [Ancora("06-b38", f"vecchio-validatore[{i + 1}]",
                           "banchi/01-b4-validatore.py", a,
                           caso="il caso «il validatore di ieri» (compatibilita')")
                    for i, (a, _b) in enumerate(coppie)]
    raise Scaduto("nessun elenco `ancore`")


def e_b40(rel):
    """06-b40-certifica.sh — un documento-qui con `a`, `b`, `c` sul cliente."""
    corpo = _documento_qui(_sorgente(rel), "PYTHON")[0]
    fuori = []
    for nome in ("a", "b", "c"):
        fuori.append(Ancora("06-b40", f"ancora-{nome.upper()}",
                            "banchi/01-b3-cliente.py",
                            _letterale(corpo, nome),
                            caso="«si registra all'arrivo, non al consumo»"))
    return fuori


# le costanti di percorso di `01-b12-guasti.py`, dalla radice del deposito
_B12_BASI = {
    "QUI": "banchi",
    "ESEMPI": "banchi/b2/ngtcp2/examples",     # ⛔ vive su /media/REMOTIX
    "COPIE": "banchi/01-b12-copie",
    "ORIGINALI": "banchi/01-b12-copie/originali",
}


def _b12_dove(sigla, nodo):
    """Il bersaglio di un guasto di B12, dalla radice.

    ⛔ E quando il bersaglio e' una COPIA che `prepara_copia()` rifa' da
       `banchi/<nome>` a ogni giro, si guarda **l'originale vivo**: la copia
       sul disco puo' essere di ieri, e un'ancora provata su una copia vecchia
       e' un verde che non descrive niente.
    """
    if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "join" and nodo.args
            and isinstance(nodo.args[0], ast.Name)
            and nodo.args[0].id in _B12_BASI):
        raise Scaduto(f"«{sigla}»: bersaglio ignoto {ast.dump(nodo)[:70]}")
    pezzi = [_B12_BASI[nodo.args[0].id]]
    for a in nodo.args[1:]:
        try:
            pezzi.append(ast.literal_eval(a))
        except ValueError:
            raise Scaduto(f"«{sigla}»: pezzo di percorso non letterale")
    rel = os.path.normpath(os.path.join(*pezzi))
    marca = "banchi/01-b12-copie/"
    if rel.startswith(marca):
        vivo = "banchi/" + rel[len(marca):]
        if os.path.isfile(os.path.join(RADICE, vivo)):
            return vivo
    return rel


def e_b12(rel):
    """01-b12-guasti.py — il catalogo di fase 1: `guasto(sigla, banco, titolo,
       dove, appiglio, sostituto, …)`.

    ⛔ `dove` e' un percorso calcolato.  Si riconoscono le due famiglie:
       `os.path.join(ESEMPI, "x")` (l'albero ngtcp2, che sta su
       `/media/REMOTIX` e qui non c'e' ⇒ CIECA) e `os.path.join(COPIE, "x")`
       (una copia rifatta a ogni giro da `banchi/x` ⇒ si guarda l'originale).
    """
    s = _sorgente(rel)
    albero = ast.parse(s)
    fuori = []
    for nodo in ast.walk(albero):
        if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                and nodo.func.id == "guasto"):
            continue
        if len(nodo.args) < 6:
            continue
        sigla = ast.literal_eval(nodo.args[0])
        dove = nodo.args[3]
        try:
            appiglio = ast.literal_eval(nodo.args[4])
        except ValueError:
            raise Scaduto(f"«{sigla}»: l'appiglio non e' un letterale")
        if not appiglio:
            continue        # i guasti «copia-di-file» non hanno appiglio
        rel_file = _b12_dove(sigla, dove)
        titolo = ast.literal_eval(nodo.args[2]) if len(nodo.args) > 2 else ""
        fuori.append(Ancora("01-b12", sigla, rel_file, appiglio,
                            caso=str(titolo)[:90]))
    if not fuori:
        raise Scaduto("nessuna chiamata a guasto() con appiglio")
    return fuori


def e_cucitura(rel):
    """06-b34-cucitura.py — ⚠ NON e' un innestatore di guasti: e' l'attrezzo
       che rimette una CURA nei file di altri agenti.  Ma le sue ancore
       scadono nello stesso modo, e quando scadono la cura non si applica.
       ⇒ Si guardano qui, marcate a parte.
    """
    pezzi = _letterale(_sorgente(rel), "PEZZI")
    fuori = []
    for i, voce in enumerate(pezzi):
        rel_file, ancora, _nuovo, marca = voce[0], voce[1], voce[2], voce[3]
        fuori.append(Ancora("06-b34-cucitura", f"pezzo{i + 1}:{marca[:24]}",
                            rel_file, ancora,
                            caso="⚠ CUCITURA (una cura, non un guasto)"))
    return fuori


def e_ff_strumenta(rel):
    """01-p5-ff-strumenta.py — `p(nome, vecchio, nuovo, quante=1)`.

    ⚠ Anche questo NON e' un innestatore di guasti: strumenta una copia della
      pagina per il giro Firefox.  Ma l'ancora scade allo stesso modo, e la
      molteplicita' voluta qui non e' sempre 1 — la dichiara `quante`.
    """
    fuori = []
    for i, (posiz, nomi) in enumerate(_chiamate(_sorgente(rel), "p")):
        if len(posiz) < 3 or posiz[1] is NONLETTERALE:
            raise Scaduto(f"la patch n. {i + 1} non ha un vecchio letterale")
        quante = nomi.get("quante", posiz[3] if len(posiz) > 3 else 1)
        a = Ancora("01-p5-ff-strumenta", str(posiz[0]), "src/pagina.html",
                   posiz[1], caso="⚠ STRUMENTAZIONE (non un guasto)")
        a.molteplicita_voluta = quante
        fuori.append(a)
    return fuori


# ===========================================================================
# ⛔ IL REGISTRO.  Aggiungere un innestatore vuol dire aggiungere una riga.
# ===========================================================================
INNESTATORI = [
    ("banchi/06-b33-guasti.py", e_b33),
    ("banchi/06-b33-risveglio-guasti.py", e_b33_risveglio),
    ("banchi/06-b34-guasti.sh", e_b34),
    ("banchi/06-b35-guasti.py", e_b35),
    ("banchi/06-b36-certifica.sh", e_b36),
    ("banchi/06-b38-registratore.py", e_b38),
    ("banchi/06-b40-certifica.sh", e_b40),
    ("banchi/06-b41-guasto.py", e_b41),
    ("banchi/05-b1-certifica.sh", e_b1),
    ("banchi/04-b23-guasti.py", e_b23),
    ("banchi/04-b31-certifica.sh", e_b31),
    ("banchi/03-b18-innesta.py", e_b18),
    ("banchi/02-codifica-guasti.py", e_codifica),
    ("banchi/02-pagina-vista-prova.py", e_pagina_vista),
    ("banchi/01-b12-guasti.py", e_b12),
    ("banchi/01-p5-guasto-ritiro.py", e_p5_ritiro),
    ("banchi/06-b34-cucitura.py", e_cucitura),
    ("banchi/01-p5-ff-strumenta.py", e_ff_strumenta),
]


# ===========================================================================
# ⛔ IL CONTROLLO POSITIVO DELL'ATTREZZO STESSO — `--controllo`.
#
#    Un attrezzo che cerca ancore morte deve saper distinguere le tre
#    risposte su un caso di prova, o il giorno che dicesse «tutte vive» non
#    si saprebbe se ha guardato.
# ===========================================================================
def controllo():
    import tempfile
    guai = []
    with tempfile.TemporaryDirectory() as d:
        prova = os.path.join(d, "prova.c")
        with open(prova, "w", encoding="utf-8") as f:
            f.write("uno\n\tdue\nuno\n")
        casi = [("una volta sola", "\tdue", "VIVA"),
                ("due volte", "uno", "AMBIGUA"),
                ("mai", "tre", "MORTA")]
        for nome, testo, atteso in casi:
            a = Ancora("prova", nome, os.path.relpath(prova, RADICE), testo)
            a.guarda()
            print(f"    {'OK ' if a.esito == atteso else '⛔ '} "
                  f"{nome}: {a.esito} (atteso {atteso})")
            if a.esito != atteso:
                guai.append(nome)
        a = Ancora("prova", "file che non c'e'", "questo/non/esiste.c", "x")
        a.guarda()
        print(f"    {'OK ' if a.esito == 'CIECA' else '⛔ '} "
              f"file assente: {a.esito} (atteso CIECA, ⛔ non MORTA)")
        if a.esito != "CIECA":
            guai.append("file assente")

    # ⛔ E il falso allarme che questo attrezzo HA GIA' DATO: le BRE di `sed`
    #    lette come se fossero espressioni di `re`.
    print()
    for bre, atteso in [(r"^\t\tif (!seat || !\*seat)$",
                         "^\\t\\tif \\(!seat \\|\\| !\\*seat\\)$"),
                        (r"a\(b\)c", "a(b)c"),
                        (r"x\{2\}", "x{2}")]:
        avuto = bre_a_python(bre)
        print(f"    {'OK ' if avuto == atteso else '⛔ '} BRE {bre!r} → {avuto!r}")
        if avuto != atteso:
            guai.append(f"BRE {bre}")
    prova = "\t\tif (!seat || !*seat)\n"
    n = len(re.findall(bre_a_python(r"^\t\tif (!seat || !\*seat)$"), prova,
                       re.MULTILINE))
    print(f"    {'OK ' if n == 1 else '⛔ '} l'ancora di 05-b1 su una riga "
          f"vera: {n} (atteso 1)")
    if n != 1:
        guai.append("BRE su riga vera")
    print()
    if guai:
        print(f"⛔ CONTROLLO FALLITO: {guai}")
        return 1
    print("⭐ CONTROLLO SUPERATO")
    return 0


# ===========================================================================
def main():
    p = argparse.ArgumentParser(description="le ancore dei guasti innestati")
    p.add_argument("--vive", action="store_true",
                   help="stampa anche le ancore vive")
    p.add_argument("--solo", default="",
                   help="un innestatore solo (sottostringa del nome)")
    p.add_argument("--json", action="store_true", help="una riga JSON per ancora")
    p.add_argument("--controllo", action="store_true",
                   help="il controllo positivo di questo attrezzo")
    a = p.parse_args()

    if a.controllo:
        return controllo()

    VERDE, ROSSO, GIALLO, BLU, GRIGIO = (
        "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[1;34m", "\033[0m")
    if not sys.stdout.isatty():
        VERDE = ROSSO = GIALLO = BLU = GRIGIO = ""

    tutte, rotti = [], []
    for rel, estrai in INNESTATORI:
        if a.solo and a.solo not in rel:
            continue
        if _sorgente(rel) is None:
            rotti.append((rel, "l'innestatore non c'e' piu'"))
            continue
        try:
            ancore = estrai(rel)
        except Scaduto as sbaglio:
            # ⛔ Un estrattore che non riconosce piu' la tabella NON deve
            #    tornare zero ancore in silenzio: sarebbe questo attrezzo a
            #    scadere, e nessuno se ne accorgerebbe.
            rotti.append((rel, f"⛔ l'ESTRATTORE e' scaduto: {sbaglio}"))
            continue
        for x in ancore:
            x.guarda()
        tutte.extend(ancore)

    if a.json:
        for x in tutte:
            print(json.dumps({"banco": x.banco, "guasto": x.guasto,
                              "file": x.file_rel, "esito": x.esito,
                              "quante": x.quante, "caso": x.caso},
                             ensure_ascii=False))
    else:
        banco = None
        for x in tutte:
            if x.esito == "VIVA" and not a.vive:
                continue
            if x.banco != banco:
                banco = x.banco
                print(f"\n{BLU}== {banco}{GRIGIO}")
            colore = {"VIVA": VERDE, "MORTA": ROSSO,
                      "AMBIGUA": ROSSO, "CIECA": GIALLO}[x.esito]
            n = "-" if x.quante is None else x.quante
            print(f"  {colore}{x.esito:<8}{GRIGIO}{n:>3}×  {x.guasto:<26} "
                  f"{x.file_rel}")
            if x.esito in ("MORTA", "AMBIGUA"):
                print(f"           ⛔ resta senza controllo positivo: {x.caso}")
                righe = x.testo.splitlines()
                for r in righe[:3]:
                    print(f"           ancora│ {r[:100]}")
                if len(righe) > 3:
                    print(f"           ancora│ … ({len(righe)} righe in tutto)")

    conto = {k: sum(1 for x in tutte if x.esito == k)
             for k in ("VIVA", "MORTA", "AMBIGUA", "CIECA")}
    print(f"\n{len(tutte)} ancore  ·  {conto['VIVA']} vive  ·  "
          f"{conto['MORTA']} morte  ·  {conto['AMBIGUA']} ambigue  ·  "
          f"{conto['CIECA']} cieche (file non su questa macchina)")

    for rel, perche in rotti:
        print(f"  ⛔ {rel}: {perche}")

    if rotti:
        return 2
    return 1 if conto["MORTA"] or conto["AMBIGUA"] else 0


if __name__ == "__main__":
    sys.exit(main())
