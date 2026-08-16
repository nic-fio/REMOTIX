#!/usr/bin/env python3
"""06-b38-mutazioni.py — ⛔ si guasta l'ARBITRO apposta, e si guarda se il banco se ne accorge.

    python3 06-b38-mutazioni.py [cartella]

    uscita 0  ogni mutazione e' stata VISTA da almeno una registrazione
    uscita 1  ⛔ almeno una mutazione SOPRAVVIVE: c'e' una regola che nessuna
              registrazione fa scattare, e il suo verde non vuol dire niente
    uscita 2  il banco non si e' potuto fare girare

---------------------------------------------------------------------------
⛔ IL PROBLEMA CHE QUESTO BANCO RISOLVE, E CHE «41 SU 41» NON RISOLVE

`01-b4-lancia.py` dice *«il validatore accusa ciascun guasto sul byte
giusto»*, ed e' vero.  ⚠ Ma il 16 agosto 2026 le sedici registrazioni della
tela e le sette regole che le giudicano sono state scritte **nella stessa ora,
dalla stessa mano**: e due programmi scritti dalla stessa mano che vanno
d'accordo non confermano niente (`README.md`).  ⛔ «41 su 41 al primo giro» e'
compatibile con un banco che misura sé stesso.

⭐ **La domanda a cui questo file risponde e' l'altra**: se qualcuno CANCELLA
   una delle regole della tela dal validatore, qualche registrazione diventa
   rossa?  Se no, quella regola e' scritta e non provata — e il giorno in cui
   una modifica la togliesse per sbaglio, `01-b4-lancia.py` continuerebbe a
   stampare «e' certificato».

⛔ E vale nei DUE VERSI, che e' la parte che si dimentica:

  · **si toglie** un controllo → una registrazione **guasta** deve diventare
    verde, cioe' il banco deve accorgersene.  Prova che il controllo serve;
  · **si aggiunge** severita' — per esempio applicare a `ADATTA_TELA` i limiti
    di §4.5, che §7.1 le nega — → una registrazione **conforme** deve diventare
    rossa.  ⭐ Prova che le registrazioni positive non sono di cortesia: sono
    l'unica cosa che tiene un arbitro dall'essere severo, e un arbitro severo
    **uccide sessioni sane** (`RCP.md` §6.2, rilievo R1.17).

---------------------------------------------------------------------------
⚠ COME SI MUTA, E PERCHE' NON SI TOCCA IL FILE VERO

Ogni mutazione e' una sostituzione di testo su una **copia** del validatore,
nella cartella di lavoro.  ⛔ Il file del deposito non si tocca mai: un banco
che modificasse l'arbitro per provarlo lascerebbe l'arbitro modificato il
giorno in cui muore a meta'.

⛔ E se una sostituzione **non trova il suo testo**, la mutazione non e'
   «passata»: e' **saltata**, e conta come guasto del banco (uscita 2).  Una
   mutazione che non muta niente e' un controllo positivo che assolve sempre —
   la forma d'errore E8 dentro il banco che esiste per prenderla.
"""
import json
import os
import re
import shutil
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
VALIDATORE = os.path.join(QUI, "01-b4-validatore.py")
COSTRUTTORE = os.path.join(QUI, "01-b4-registrazioni.py")
# ⛔ Il giudice del fotogramma si IMPORTA risalendo le cartelle (§6.2, e il
#    validatore lo dichiara): il mutante vive in un'altra cartella e non lo
#    troverebbe.  ⚠ Primo giro del 16 agosto 2026: **dieci** registrazioni
#    video cambiavano esito a OGNI mutazione, e non era una scoperta — era
#    l'arbitro che usciva 2 «non ho potuto guardare» perche' il banco l'aveva
#    messo dove il giudice non c'era.  Un rumore di dieci righe su undici
#    avrebbe nascosto la mutazione che sopravvive.
FOTOGRAMMA = os.path.join(QUI, "02-filo-fotogramma.py")

# ---------------------------------------------------------------------------
# ⛔ LE MUTAZIONI, e ciascuna porta le registrazioni che DEVONO accorgersene.
#
#    `da` -> `a` e' una sostituzione letterale sul testo del validatore.  Le
#    registrazioni elencate in `viste_da` sono l'atteso, ⭐ **scritto qui prima
#    di far girare qualunque cosa**: se una mutazione e' vista solo da
#    registrazioni che non avevo previsto, il banco lo dice.
MUTAZIONI = [
    # ── togliere un controllo: una guasta deve diventare VERDE ─────────────
    ("T1-tela-non-sollecitata",
     "un TELA che non risponde a nessuna ADATTA_TELA passa",
     '        dopo_vista = (" ⚠ ed e\' arrivato subito dopo una VISTA',
     '        return\n        dopo_vista = (" ⚠ ed e\' arrivato subito dopo una VISTA',
     ["22-tela-non-sollecitata", "30-vista-cambia-tela"]),

    ("T2-tela-doppia",
     "il secondo TELA per la stessa richiesta passa",
     "        if self.ultima_consumata is not None:",
     "        if False:",
     ["23-tela-doppia"]),

    ("T3-adatta-senza-risposta",
     "una ADATTA_TELA senza risposta non si accusa mai",
     "    if stato.in_volo:",
     "    if False and stato.in_volo:",
     ["24-adatta-senza-risposta", "24bis-adatta-senza-risposta-fin"]),

    ("T5-rifiuto-che-cambia-la-tela",
     "un TELA(RIFIUTATA) puo' cambiare la tela in vigore",
     "            if es == 2 and prima is not None and (lar, alt) != prima:",
     "            if False:",
     ["27-tela-rifiutata-cambia"]),

    ("T6-tela-concessa-fuori-da-4.5",
     "una tela concessa dispari o fuori dai limiti passa",
     "            if es == 1:\n                for eti, v, off, mi, ma in (",
     "            if False:\n                for eti, v, off, mi, ma in (",
     ["28-tela-concessa-dispari", "29-tela-concessa-fuori-limiti"]),

    ("V1-vista-con-un-lato-zero",
     "una VISTA 1280x0 passa",
     "            if v == 0:",
     "            if False:",
     ["32-vista-zero"]),

    ("tipi-del-15-agosto",
     "TERMINA_SESSIONE torna a essere un tipo sconosciuto",
     '    0x0011: ("TERMINA_SESSIONE", CLIENT),',
     "",
     ["37-termina-sessione"]),

    ("motivo-0x10",
     "SESSIONE_TERMINATA torna a essere un motivo sconosciuto",
     '    0x10: "SESSIONE_TERMINATA",',
     "",
     ["37-termina-sessione"]),

    # ── ⛔ le sei cure del REFUTATORE, 16 agosto 2026 sera ─────────────────
    #    Nessuna di queste regole l'ha trovata una rilettura: le ha trovate un
    #    agente mandato a smentire l'arbitro, su 36 controesempi costruiti
    #    leggendo `RCP.md`.  ⚠ Senza queste mutazioni si potrebbero togliere
    #    tutte e sei e il banco continuerebbe a stampare «e' certificato».
    ("misura-massima-in-SESSIONE",
     "SESSIONE puo' concedere piu' di video.misura_massima (§4.5)",
     "            if not entro_la_massima(stato.misura_massima, lar, alt):",
     "            if False:",
     ["38-sessione-oltre-misura-massima"]),

    ("misura-massima-in-TELA",
     "TELA(ADATTATA) puo' concedere piu' di video.misura_massima (§4.5)",
     "            if es == 1 and not entro_la_massima(stato.misura_massima, lar, alt):",
     "            if False:",
     ["39-concessa-oltre-misura-massima"]),

    ("congedato-poi-tace",
     "dopo il proprio CONGEDO si puo' continuare a parlare (§8.1)",
     "        if verso is not None and verso in self.congedato_da:",
     "        if False:",
     ["40-tela-dopo-il-congedo"]),

    ("canale-dichiarato-si-verifica",
     "il campo `canale` del blocco si crede sulla parola (§11.1)",
     "                if alto != canale:",
     "                if False:",
     ["41-canale-dichiarato-falso"]),

    ("oscurato-sui-campi-numerici",
     "si legge dentro un intervallo oscurato (§11.1) — e si giudica 0x2A2A2A2A",
     "        if not ammetti_oscurato and self.oscurato(self.i, n):",
     "        if False:",
     ["42-oscurato-su-un-numero"]),

    ("in-volo-dichiarate-al-giudice",
     "⭐ il giudice del fotogramma non sa che una ADATTA_TELA e' in volo, e la "
     "grazia di §6.2 torna irraggiungibile",
     "            ctx.adatta_in_volo = list(fl[\"in_volo\"])",
     "            ctx.adatta_in_volo = []",
     ["43-fotogramma-prima-del-tela"]),

    ("tela-precedente-al-giudice",
     "⭐ si chiama adatta_tela su un contesto gia' alla misura nuova: per il "
     "giudice non e' successo niente, e la coda di D14 non si apre",
     "                    if fl[\"tela_prec\"] is not None:\n"
     "                        ctx.tela_larghezza, ctx.tela_altezza = fl[\"tela_prec\"]",
     "                    pass",
     ["44-fotogramma-vecchio-dopo-il-tela"]),

    # ── ⭐ e il verso opposto: aggiungere SEVERITA' ────────────────────────
    #    Qui la registrazione che deve accorgersene e' una **conforme**, ed e'
    #    l'unica prova che le positive servano a qualcosa.
    ("severita-limiti-su-ADATTA_TELA",
     "⭐ si applicano ad ADATTA_TELA i limiti di §4.5, che §7.1 le nega",
     '    elif nome == "ADATTA_TELA":',
     '    elif nome == "ADATTA_TELA":\n'
     '        _o = le.i\n'
     '        _l = le.u32("larghezza"); _a = le.u32("altezza")\n'
     '        if not (320 <= _l <= 7680 and 240 <= _a <= 4320) or _l % 2 or _a % 2:\n'
     '            raise NonConforme("RCP.md §4.5", "misura fuori dai limiti",\n'
     '                              le.base + _o, _o)\n'
     '        le.fine(nome)\n'
     '        return True\n'
     '    elif nome == "ADATTA_TELA_MAI":',
     ["33-adatta-fuori-limiti-rifiutata"]),

    ("severita-vista-coi-limiti-della-tela",
     "⭐ si rimettono alla VISTA i limiti della tela — il rilievo R1.17 "
     "rientrato dal lato dell'arbitro",
     "            if v == 0:",
     "            if v == 0 or not (320 <= v <= 7680) or v % 2:",
     # ⚠ E l'atteso porta anche `34-tela-giro-pieno`, che contiene una
     #   `VISTA(640x401)` dispari di proposito — §7.1 la dichiara legale.
     #   ⛔ Il primo atteso, scritto prima del giro, era INCOMPLETO: e' una
     #   volta in cui l'atteso sbaglia e lo strumento no, ed e' la terza in
     #   questo banco (le altre due sono in `01-b4-registrazioni.py`).
     ["31-vista-legale", "34-tela-giro-pieno"]),

    ("severita-T3-sempre",
     "⭐ si accusa la ADATTA_TELA in volo anche quando la sessione e' viva",
     "        if controllo_chiuso_dal_server is not None or stato.congedo is not None:",
     "        if True:",
     # ⚠ Ne rompe DUE, e la seconda e' la piu' istruttiva: `45` e' la traccia in
     #   cui a chiudere e' stato il **client**, dove §7.1 e §4.2 si
     #   contraddicono.  ⛔ Un arbitro che accusasse «sempre» prenderebbe
     #   posizione su una contraddizione di `RCP.md` **senza dirlo**, e darebbe
     #   rosso al server per un gesto dell'utente.
     ["24ter-adatta-in-volo-traccia-viva", "45-adatta-poi-fin-del-client"]),

    ("severita-misura-concessa-uguale-alla-chiesta",
     "⭐ si pretende che la tela concessa sia quella chiesta — §4.5 dice il "
     "contrario, ed e' la strada normale su KWin < 6.8",
     "            stato.tela = (lar, alt)\n            if es == 1:\n"
     '                stato.tela_da = "TELA(ADATTATA) (§7.1)"',
     "            if es == 1 and stato.in_volo and \\\n"
     "                    stato.in_volo[0][3] not in (None, (lar, alt)):\n"
     '                raise NonConforme("RCP.md §7.1",\n'
     '                                  "la tela concessa non e\' quella chiesta",\n'
     "                                  le.base + off_lar, off_lar)\n"
     "            stato.tela = (lar, alt)\n            if es == 1:\n"
     '                stato.tela_da = "TELA(ADATTATA) (§7.1)"',
     ["35-due-richieste-in-volo"]),
]


def rigenera(dove):
    p = subprocess.run([sys.executable, COSTRUTTORE, dove],
                       capture_output=True, text=True)
    if p.returncode != 0:
        print(f"   ⛔ il costruttore e' uscito {p.returncode}")
        print((p.stdout + p.stderr)[-800:])
        return None
    with open(os.path.join(dove, "manifesto.json")) as f:
        return json.load(f)


def esiti(validatore, dove, manifesto):
    """Il VERDETTO del validatore su ogni registrazione: uscita, regola, byte.

    ⛔ **Non basta il codice d'uscita**, e la prima stesura di questo banco lo
       usava da solo.  ⚠ La mutazione che toglie T2 — *«due `TELA` per una sola
       `ADATTA_TELA`»* — lasciava `23-tela-doppia` **rossa lo stesso**, perche'
       il controllo che segue (T1, il `TELA` non sollecitato) la prendeva
       comunque: stesso colore, **altra regola** e altra frase.  Il banco
       dichiarava la mutazione «non vista» e mandava a cercare un buco che non
       c'era.

    ⭐ Ed e' esattamente il difetto che il validatore esiste per prendere —
       *«rosso giusto, byte sbagliato»* — arrivato dentro il banco che lo
       certifica: una diagnosi che punta a §7.1 mentre la regola violata e'
       §6.2 manda a leggere la sezione sbagliata.
    """
    fuori = {}
    for voce in manifesto:
        p = subprocess.run(
            [sys.executable, validatore, os.path.join(dove, voce["file"])],
            capture_output=True, text=True)
        testo = p.stdout + p.stderr
        m = re.search(r"NON CONFORME — (RCP\.md [^\n]*)", testo)
        b = re.search(r"byte (\d+) nel file", testo)
        fuori[voce["file"]] = (p.returncode,
                               m.group(1).strip() if m else None,
                               int(b.group(1)) if b else None)
    return fuori


def dillo(v):
    """Il verdetto in una riga, per far vedere che cosa e' cambiato."""
    uscita, regola, byte = v
    if regola is None:
        return f"uscita {uscita}"
    return f"uscita {uscita} · {regola} · byte {byte}"


def main():
    dove = (sys.argv[1] if len(sys.argv) > 1
            else os.path.join(QUI, "b38-mutazioni"))
    os.makedirs(dove, exist_ok=True)
    reg = os.path.join(dove, "registrazioni")
    # ⛔ Il giudice del fotogramma accanto al mutante — vedi FOTOGRAMMA.
    try:
        shutil.copy2(FOTOGRAMMA, os.path.join(dove, "02-filo-fotogramma.py"))
    except OSError as e:
        print(f"   ⛔ «{FOTOGRAMMA}» non si copia: {e}")
        print("      Senza, ogni mutazione muoverebbe le registrazioni video e")
        print("      il rumore coprirebbe il segnale.")
        return 2

    print("== 1. le registrazioni, e l'arbitro SANO")
    manifesto = rigenera(reg)
    if manifesto is None:
        return 2
    atteso = {v["file"]: v["uscita"] for v in manifesto}
    sano = esiti(VALIDATORE, reg, manifesto)
    diversi = [f for f in atteso if sano[f][0] != atteso[f]]
    if diversi:
        print(f"   ⛔ l'arbitro SANO non e' d'accordo col manifesto su "
              f"{len(diversi)} registrazioni: {diversi}")
        print("      ⚠ Le mutazioni non si giudicano contro una base rotta.")
        return 2
    print(f"   ⭐ {len(manifesto)} registrazioni, e l'arbitro sano concorda con")
    print(f"      il manifesto su tutte.  E' la base.\n")

    print(f"== 2. {len(MUTAZIONI)} mutazioni dell'ARBITRO\n")
    with open(VALIDATORE, encoding="utf-8") as f:
        originale = f.read()

    sopravvissute, saltate, buoni = [], [], 0
    for nome, che, da, a, viste_da in MUTAZIONI:
        if originale.count(da) != 1:
            saltate.append((nome, originale.count(da)))
            print(f"   ⛔ {nome:<40s} SALTATA: il testo da sostituire compare "
                  f"{originale.count(da)} volte")
            continue
        mutato = os.path.join(dove, f"mutante-{nome}.py")
        with open(mutato, "w", encoding="utf-8") as f:
            f.write(originale.replace(da, a, 1))
        fuori = esiti(mutato, reg, manifesto)
        cambiate = sorted(f for f in atteso if fuori[f] != sano[f])
        nomi = [c[:-len(".rcpreg")] for c in cambiate]
        if not cambiate:
            sopravvissute.append((nome, che))
            print(f"   ⛔ {nome:<40s} SOPRAVVIVE — nessuna registrazione se ne "
                  f"accorge")
            print(f"      ⚠ {che}")
            continue
        impreviste = [n for n in nomi if n not in viste_da]
        mancate = [n for n in viste_da if n not in nomi]
        segno = "OK " if not (mancate or impreviste) else "⚠  "
        if not (mancate or impreviste):
            buoni += 1
        print(f"   {segno} {nome:<40s} vista da {len(cambiate)}: "
              f"{', '.join(nomi)}")
        for c in cambiate:
            n = c[:-len('.rcpreg')]
            if n in viste_da:
                print(f"        {n:<38s} {dillo(sano[c])}  ->  {dillo(fuori[c])}")
        if mancate:
            print(f"      ⚠ attese anche: {', '.join(mancate)} — l'atteso era "
                  f"scritto prima, e non torna")
        if impreviste:
            print(f"      ⛔ IMPREVISTE: {', '.join(impreviste)} — la mutazione")
            print(f"         tocca registrazioni che non c'entrano, e allora "
                  f"non e' quella regola che si sta provando")

    print("\n== 3. Esito")
    if saltate:
        print(f"   ⛔ {len(saltate)} mutazioni SALTATE: il banco non ha provato")
        print("      quel che dice di provare, e una mutazione che non muta e'")
        print("      un controllo positivo che assolve sempre.")
        return 2
    print(f"   {buoni} su {len(MUTAZIONI)} mutazioni viste ESATTAMENTE dalle")
    print(f"   registrazioni dichiarate prima del giro")
    # ⛔ E «vista da qualcuno» non basta: se una mutazione muove registrazioni
    #    che non c'entrano, non e' quella regola che si sta provando — ed e' la
    #    stessa forma del «rosso giusto, byte sbagliato» che il validatore
    #    esiste per prendere.  ⚠ Il primo giro stampava la stella con 10 su 12.
    if buoni != len(MUTAZIONI) and not sopravvissute:
        print(f"   ⛔ {len(MUTAZIONI) - buoni} mutazioni hanno mosso "
              f"registrazioni diverse da quelle attese: o l'atteso e' scritto")
        print("      male, o la mutazione tocca piu' di una regola.  In tutt'e")
        print("      due i casi il numero non e' ancora una misura.")
        return 1
    if sopravvissute:
        print(f"   ⛔ {len(sopravvissute)} SOPRAVVISSUTE: sono regole scritte e")
        print("      non provate — il loro verde non vuol dire niente")
        for nome, che in sopravvissute:
            print(f"      · {nome}: {che}")
        return 1
    print("   ⭐ ogni regola della tela ha almeno una registrazione che la")
    print("      fa scattare, e ogni severita' in piu' rompe una conforme.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
