#!/usr/bin/env python3
"""01-b0-chiamate.py — ⛔ chi chiama un banco gli passa quel che il banco pretende?

    python3 banchi/01-b0-chiamate.py            il giro intero
    python3 banchi/01-b0-chiamate.py --elenco   che cosa pretende ogni banco

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

Le righe di comando dei lanciatori si costruiscono a pezzi:

    bash enter.sh --root "python3 $DENTRO/01-b7-congedo.py $COMUNE --solo $F"

`$COMUNE` questo programma non lo espande — e sarebbe una bugia farlo, perche'
il suo valore dipende da rami che qui non si eseguono.  ⭐ Quando in una
chiamata c'e' una variabile che non sappiamo sciogliere, l'esito e' **IGNOTO**,
non «va bene».  «Non ho potuto guardare» e «ho guardato e va bene» sono due
fatti, e confonderli e' esattamente il difetto che questo file esiste per
trovare (`LEZIONI.md` §1.9).

⚠ E un IGNOTO **non fa fallire** il giro: fa stampare quali chiamate nessuno
  sta sorvegliando, che e' un'informazione e non un allarme.
"""
import argparse
import ast
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
VERDE, ROSSO, GIALLO, GRIGIO, NETTO = (
    "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m", "\033[1m")


def opzioni_di(percorso):
    """{obbligatorie}, {tutte} — leggendo gli `add_argument` con l'AST.

    ⛔ Con l'AST e non con una espressione regolare: `required=True` puo' stare
       su una riga diversa dal nome, e un banco che il controllo non sa leggere
       diventerebbe un banco senza obblighi — cioe' sempre verde.
    """
    try:
        with open(percorso, encoding="utf-8") as f:
            albero = ast.parse(f.read(), percorso)
    except (OSError, SyntaxError):
        return None, None, None
    obbligatorie, tutte, scorciatoie = set(), set(), set()
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
    for nodo in ast.walk(albero):
        if (isinstance(nodo, ast.Compare) and len(nodo.ops) == 1
                and isinstance(nodo.ops[0], ast.In)
                and isinstance(nodo.left, ast.Constant)
                and isinstance(nodo.left.value, str)
                and nodo.left.value.startswith("--")):
            scorciatoie.add(nodo.left.value)
    for nodo in ast.walk(albero):
        if not (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "add_argument"):
            continue
        nomi = [a.value for a in nodo.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
                and a.value.startswith("--")]
        if not nomi:
            continue
        tutte.update(nomi)
        for k in nodo.keywords:
            if (k.arg == "required" and isinstance(k.value, ast.Constant)
                    and k.value.value is True):
                obbligatorie.update(nomi)
    return obbligatorie, tutte, scorciatoie


def assegnazioni(righe):
    """{NOME: valore} per le variabili di shell assegnate a un testo letterale.

    ⭐ Senza questo, il controllo guardava **un terzo** delle chiamate: i
       lanciatori costruiscono la riga a pezzi (`$COMUNE`, `$DENTRO`) e ogni
       riga con una variabile finiva fra le IGNOTE.  `[M]` 11 agosto 2026:
       28 ignote su 83 chiamate.

    ⚠ Un livello solo, e solo le assegnazioni **letterali**: quel che dipende
      da un ramo o da un comando resta ignoto, e ignoto si dichiara.
    """
    fuori = {}
    for riga in righe:
        m = re.match(r'^\s*([A-Z_][A-Z0-9_]*)=(.*)$', riga)
        if not m:
            continue
        nome, valore = m.group(1), m.group(2).strip()
        if valore.startswith('"') and valore.endswith('"') and len(valore) > 1:
            valore = valore[1:-1]
        elif valore.startswith("'") and valore.endswith("'") and len(valore) > 1:
            valore = valore[1:-1]
        elif re.search(r'[`$(]', valore):
            continue        # ⛔ viene da un comando: non lo so, e lo dico
        fuori[nome] = valore
    return fuori


def sciogli(testo, tabella):
    """Sostituisce `$VAR` e `${VAR}` finche' si puo', al massimo tre giri."""
    for _ in range(3):
        prima = testo
        testo = re.sub(r'\$\{?([A-Z_][A-Z0-9_]*)\}?',
                       lambda m: tabella.get(m.group(1), m.group(0)), testo)
        if testo == prima:
            break
    return testo


def chiamate(percorso, banchi):
    """[(banco, [opzioni citate], ha_variabili, riga)] trovate in `percorso`."""
    try:
        with open(percorso, encoding="utf-8") as f:
            righe = f.read().splitlines()
    except OSError:
        return []
    tabella = assegnazioni(righe)
    fuori = []
    # ⛔ E SI SALTANO ANCHE LE STRINGHE LUNGHE, non solo i commenti — `[M]` 11
    #    agosto 2026: alla prima stesura questo controllo accusava **ventuno**
    #    chiamate, e quasi tutte erano righe di ESEMPIO dentro la spiegazione in
    #    testa a un banco (`python3 01-b8-cronometro.py --campioni --blocco 3`).
    #    ⭐ Un controllo che grida sul falso non viene ignorato di meno di uno
    #    che tace: viene ignorato **insieme ai suoi veri**.  E' la ragione per
    #    cui questa funzione porta uno stato invece di una riga di espressione
    #    regolare in piu'.
    dentro_stringa = None
    for n, riga in enumerate(righe, 1):
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
            if not fuori_stringa.strip():
                continue
            riga = fuori_stringa
        # ⚠ I commenti si saltano: questo file stesso, e mezzo progetto,
        #   NOMINANO i banchi nelle spiegazioni.  Un controllo che accusasse
        #   una prosa sarebbe rumore, e il rumore si impara a ignorare.
        spoglia = riga.lstrip()
        if spoglia.startswith("#"):
            continue
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
            if not re.search(r'python3?\s+(-\S+\s+)*\S*$', testa):
                continue
            # si taglia alla redirezione o alla fine del comando
            coda = re.split(r'[>|;]|&&|\|\|', coda)[0]
            coda = sciogli(coda, tabella)
            opz = set(re.findall(r'(--[a-z0-9][a-z0-9-]*)', coda))
            # ⛔⭐ UNA VARIABILE NON SCIOLTA NON RENDE IGNOTA TUTTA LA RIGA, e
            #     la distinzione decide se questo controllo serve o no.
            #
            # `[M]` 11 agosto 2026: con «c'e' un `$` ⇒ IGNOTA» erano ignote 26
            # righe su 34 — ⛔ **compresa quella che aveva appena rotto B7**
            # (`01-b12-lancia.sh:430`), che porta un `$passo` dentro il valore
            # di `--registro`.  Un controllo nato da un difetto che poi non
            # vede quel difetto e' un controllo che si dichiara prudente e non
            # guarda niente.
            #
            # ⭐ La domanda giusta non e' «c'e' una variabile», e' **«quella
            #    variabile puo' nascondere il nome di un'opzione?»**.  Il valore
            #    di `--registro` no: qualunque cosa sia, `--bersaglio` non ci
            #    sta dentro.  Una variabile che sta **da sola** — `$COMUNE` —
            #    si', e quella resta IGNOTA.
            pezzi = coda.split()
            variabili = False
            for i, pezzo in enumerate(pezzi):
                if not re.match(r'^["\']?\$', pezzo):
                    continue
                prima = pezzi[i - 1] if i else ""
                if not prima.startswith("--"):
                    variabili = True
                    break
            fuori.append((banco, opz, variabili, n, riga.strip()))
    return fuori


def giro(elenco_solo=False):
    banchi = {}
    for nome in sorted(os.listdir(QUI)):
        if not nome.endswith(".py") or nome == os.path.basename(__file__):
            continue
        obb, tutte, corte = opzioni_di(os.path.join(QUI, nome))
        if obb is None:
            print(f"    {GIALLO}?{GRIGIO}  {nome}: non si e' potuto leggere")
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
        for aiuto in sorted(os.listdir(QUI)):
            if (aiuto.startswith("01-b0-") and aiuto.endswith(".py")
                    and aiuto != nome and aiuto[:-3] in open(
                        os.path.join(QUI, nome), encoding="utf-8",
                        errors="ignore").read()):
                sue_obb, sue, _c = opzioni_di(os.path.join(QUI, aiuto))
                if sue:
                    tutte = tutte | sue
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
                if sue_obb and "aggiungi_argomenti" in open(
                        os.path.join(QUI, nome), encoding="utf-8",
                        errors="ignore").read():
                    obb = obb | sue_obb
        if tutte:
            banchi[nome] = (obb, tutte, corte)

    if elenco_solo:
        print(f"{NETTO}== Che cosa pretende ogni banco{GRIGIO}\n")
        for nome, (obb, tutte, corte) in banchi.items():
            if obb:
                print(f"  {nome}\n     ⛔ obbligatorie: {', '.join(sorted(obb))}")
        return 0

    con_obblighi = {n: v for n, v in banchi.items() if v[0]}
    print(f"{NETTO}== ⛔ Chi chiama un banco gli passa quel che il banco "
          f"pretende?{GRIGIO}")
    print(f"   {len(banchi)} banchi letti, {len(con_obblighi)} con almeno un "
          f"argomento obbligatorio.\n")

    chiamanti = [n for n in sorted(os.listdir(QUI))
                 if n.endswith((".sh", ".py")) and n != os.path.basename(__file__)]
    mancanti, sconosciute, ignoti, viste = [], [], [], 0
    for chi in chiamanti:
        for banco, opz, variabili, n, riga in chiamate(
                os.path.join(QUI, chi), banchi):
            obb, tutte, corte = banchi[banco]
            # ⛔ `--elenco` e simili: una chiamata che non porta NESSUNA opzione
            #    quasi sempre e' una citazione in una stringa di aiuto, non un
            #    lancio.  Si contano solo le righe che almeno un'opzione ce
            #    l'hanno — e lo si dichiara, invece di sembrare esaustivi.
            if not opz:
                continue
            viste += 1
            if variabili:
                ignoti.append((chi, n, banco))
                continue
            # ⭐ Con una scorciatoia in mano, gli obbligatori non si pretendono.
            perse = set() if (opz & corte) else obb - opz
            if perse:
                mancanti.append((chi, n, banco, sorted(perse), riga))
            strane = {o for o in opz if o not in tutte and o != "--root"}
            if strane:
                sconosciute.append((chi, n, banco, sorted(strane), riga))

    for chi, n, banco, perse, riga in mancanti:
        print(f"  {ROSSO}NO{GRIGIO}  {chi}:{n} chiama {banco} SENZA "
              f"{', '.join(perse)}")
        print(f"        ⛔ il banco si rifiutera' di partire, e il giro "
              f"leggera' un ROSSO che non e' suo")
        print(f"        {riga[:150]}")
    for chi, n, banco, strane, riga in sconosciute:
        print(f"  {ROSSO}NO{GRIGIO}  {chi}:{n} passa a {banco} "
              f"{', '.join(strane)}, che il banco non conosce")
        print(f"        {riga[:150]}")
    if ignoti:
        print(f"\n  {GIALLO}?{GRIGIO}  {len(ignoti)} chiamate con variabili "
              f"che non so sciogliere — ⛔ IGNOTE, non approvate:")
        for chi, n, banco in ignoti:
            print(f"        {chi}:{n} → {banco}")

    print(f"\n    == quel che questo giro ha davvero guardato")
    print(f"    --  chiamate con almeno un'opzione:  {viste}")
    print(f"    {VERDE}{viste - len(ignoti) - len(mancanti) - len(sconosciute):3d}"
          f"{GRIGIO}  approvate")
    print(f"    {ROSSO}{len(mancanti) + len(sconosciute):3d}{GRIGIO}  "
          f"⛔ rotte")
    print(f"    {GIALLO}{len(ignoti):3d}{GRIGIO}  ⚠ IGNOTE (variabili non "
          f"sciolte) — non sono un rosso e non sono un verde")
    if viste == 0:
        print(f"    {ROSSO}⛔ ZERO chiamate guardate: questo giro non dice "
              f"niente, e «nessun problema trovato» sarebbe una bugia{GRIGIO}")
        return 2
    return 1 if (mancanti or sconosciute) else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--elenco", action="store_true",
                   help="che cosa pretende ogni banco, e basta")
    a = p.parse_args()
    sys.exit(giro(a.elenco))
