#!/usr/bin/env python3
"""01-p5-registro.py — l'attrezzo che LEGGE e SCRIVE `01-p5-esiti.jsonl`.

    python3 01-p5-registro.py aggiungi '<json>'
    python3 01-p5-registro.py righe
    python3 01-p5-registro.py elenco   --giro G --da N
    python3 01-p5-registro.py battuta  --giro G --da N
    python3 01-p5-registro.py cerca    --giro G --da N --tipo PRONTA
    python3 01-p5-registro.py passi    --log FILE --marca-inizio A --marca-fine B \\
                                       --utente prova [--atteso sessione|respinto|niente-sessione]

===========================================================================
⛔ PERCHE' UN ATTREZZO E NON TRE `grep` DENTRO LO SCRIPT

`LEZIONI.md` §1.9, e le sue otto vesti: in questo progetto un `grep` dentro un
tubo ha gia' prodotto, in quattro giorni, un «0 su 4» che era un riscontro
riuscito, un «uscita 0» che era lo stato di `tail`, e un verde su una ricerca
mai eseguita.  ⭐ Qui ogni lettura **dichiara il proprio denominatore** — su
quante righe ha guardato — ed esce con uno stato che distingue «non c'e'» da
«non ho potuto leggere».

    0   trovato
    1   NON trovato (e il file c'era, e si dice quante righe aveva)
    3   ⛔ non ho potuto leggere: il file non c'e', o non si apre

===========================================================================
⛔ E IL COMANDO `passi`, CHE E' IL CUORE DEL GIRO CONTRO IL PRODOTTO

Il verdetto del giro col browser vero **non puo'** venire dalla pagina: quella
e' `src/pagina.html`, e' del prodotto, non e' nostra e non si tocca.  Viene dal
**registro del server**, cioe' dal lato che deve ricevere (`CODER.md` §3.8: *«il
registro di chi manda dice che ha chiamato una funzione, non che il byte e'
arrivato»* — e qui a mandare `CREDENZIALI` e' il browser, a riceverle e'
il server, quindi il server e' il lato giusto).

⛔ E l'attribuzione al motore NON si fa a tempo.  Gli orologi delle due
   macchine sono a **due ore di distanza** (`[M]` 11 agosto 2026: qui CEST, la'
   UTC), e un banco che segmenta un registro altrui con il proprio orologio e'
   la settima veste di §1.9 — il rosso puntato sull'imputato sbagliato.

⭐ La cura: **due marcatori scritti nel registro del server dal browser
   stesso**.  Prima e dopo il giro, il motore in prova naviga su

       https://192.168.0.2:7448/p5-<motore>-<giro>-inizio
       https://192.168.0.2:7448/p5-<motore>-<giro>-fine

   che `pagina.c` non riconosce (`strcmp(percorso, "/")`) e serve con un 404 —
   ⛔ ma **prima logga la riga** `GET /p5-… da <indirizzo>`.  Tutto quel che sta
   fra le due righe e' di quel motore, scritto **con l'orologio del server**, e
   nessuna aritmetica fra fusi entra nel verdetto.

⚠ E i marcatori li batte **il browser**, non `curl`: un marcatore di `curl`
  proverebbe che questa macchina raggiunge il server, non che il motore in
  prova ci sia arrivato — e sono due fatti diversi, uno dei quali e' proprio
  quello in prova.

===========================================================================
⭐ IL PASSO NUOVO DEL 12 AGOSTO 2026 — `impronta-ritirata` (difetto D11)

Questo attrezzo contava tutto quel che serve a dire «la stretta di mano e'
arrivata a `SESSIONE`», ⛔ e non contava **il ritiro dell'impronta**, che e' la
cura con cui `RCP.md` §4.1-bis chiude il rilievo **R1.14**.  ⇒ Un prodotto che
smettesse di ritirare — cioe' R1.14 vivo — sarebbe passato di qui **verde**,
perche' l'unico controllo sull'impronta guardava i VALORI, e su questo prodotto
il valore servito viene scavalcato dal ritiro.

⭐ Adesso il ritiro si conta dal registro del server (`GET /impronta da …`), sul
   segmento della gamba, e ha il suo denominatore: **la pagina servita**.

===========================================================================
⭐ E IL PASSO A0 — IL CONTROLLO POSITIVO DELL'ANCORA AL REGISTRO DEL SERVER

Sta in fondo a questo riquadro perche' e' l'ultimo arrivato, ⛔ ma gira **per
primo** a ogni comando `passi`: se l'ancora con cui si legge il verdetto di PAM
ha smesso di combaciare, tutto quel che sta sotto e' stato letto con un occhio
chiuso, e chi legge deve saperlo **prima** di credere a una riga.  Vedi il
riquadro sopra `ANCORA_PAM`, piu' giu' in questo file.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "01-p5-esiti.jsonl"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ⛔ La marca del banco rotto — e NON e' la marca di nessun guasto di catalogo.
#    Quelle di P5 e di P5R parlano del SERVER («sono due impronte diverse…»,
#    «NESSUN RITIRO DI /impronta…»); questa parla di QUESTO file, ed e' scritta
#    diversa apposta: `REVIEWER.md` §4 vieta di mescolare quel che si e'
#    misurato con quel che non si e' potuto misurare, e un banco che non sa piu'
#    leggere il registro non ha misurato niente.
MARCA_ANCORA_ROTTA = "ANCORA-AL-REGISTRO-ROTTA"


# ===========================================================================
# Scrittura
# ===========================================================================
def marca_il_bersaglio(dati):
    """⛔ Ogni riga dice CONTRO CHE COSA ha misurato — `01-b0-bersaglio.py`.

    *«Un registro che non dice contro quale server ha misurato mette in fila
    numeri di due cose diverse»*, e non ha nessun sintomo: i numeri sono tutti
    buoni, uno per uno.  ⚠ Il caso concreto e' gia' sul disco — i campioni del
    secondo fisso di B8 esistono in due copie con lo stesso nome e la stessa
    forma, una contro il prodotto e una contro l'innesto, e nessuna riga dice
    quale.  Qui il valore arriva dall'ambiente, lo mette il lanciatore, e
    ⛔ **`ignoto` e' un valore legittimo**: e' diverso da «prodotto» e diverso
    dall'assenza del campo, che e' la cosa che rende due registri
    indistinguibili.
    """
    dati.setdefault("bersaglio", os.environ.get("BERSAGLIO", "ignoto"))
    dati.setdefault("porta_bersaglio", os.environ.get("PORTA_BERSAGLIO", "ignota"))
    return dati


def marca_il_tempo(dati):
    marca_il_bersaglio(dati)
    adesso = datetime.now().astimezone()
    dati["ora"] = adesso.isoformat(timespec="milliseconds")
    dati["ora_utc"] = adesso.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    scarto = adesso.strftime("%z")
    dati["fuso"] = f"{adesso.tzname()} (UTC{scarto[:3]}:{scarto[3:]})"
    return dati


def aggiungi(testo):
    try:
        dati = json.loads(testo)
    except Exception as sbaglio:
        print(f"{ROSSO}NO{GRIGIO}  non e' JSON: {sbaglio}", file=sys.stderr)
        return 3
    marca_il_tempo(dati)
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dati, ensure_ascii=False) + "\n")
        f.flush()
    return 0


# ===========================================================================
# Lettura
# ===========================================================================
def leggi():
    """Restituisce (righe, guasto).  ⛔ Uno dei due e' sempre None.

    ⚠ Un registro che non esiste ancora e' **zero righe**, non un guasto: lo
      crea il raccoglitore alla prima riga, e prima di allora la risposta
      onesta a «quante ce ne sono» e' zero.  ⛔ Un file che c'e' e non si legge
      e' un'altra cosa, e sotto ha il suo ramo: e' la distinzione di §1.9 fra
      «vuoto» e «proibito», e va tenuta **anche quando il vuoto e' legittimo**.
    """
    if not REGISTRO.exists():
        return [], None
    try:
        crude = REGISTRO.read_text(encoding="utf-8").splitlines()
    except Exception as sbaglio:
        return None, f"«{REGISTRO}» non si legge: {sbaglio}"
    fuori = []
    for i, r in enumerate(crude):
        if not r.strip():
            continue
        try:
            fuori.append((i + 1, json.loads(r)))
        except Exception:
            fuori.append((i + 1, {"tipo": "RIGA-STORTA", "grezzo": r[:200]}))
    return fuori, None


def cerca(giro, da, tipo, ultima=True):
    righe, guasto = leggi()
    if guasto:
        print(guasto, file=sys.stderr)
        return None, 3, 0
    candidate = [(n, d) for n, d in righe
                 if n > da and d.get("giro") == giro and d.get("tipo") == tipo]
    if not candidate:
        return None, 1, len(righe)
    return (candidate[-1] if ultima else candidate[0]), 0, len(righe)


# ===========================================================================
# ⛔⭐ L'ANCORA AL VERDETTO DI PAM, E IL CONTROLLO CHE SI ACCORGE QUANDO SMETTE
#     DI COMBACIARE — cura del 12 agosto 2026, sera.
# ===========================================================================
# *La regex era gia' stata curata una volta, oggi stesso, e la cura era troppo
#  stretta.  ⛔ La seconda cura non e' la regex: e' il controllo che manca.*
#
# ⛔ QUEL CHE C'ERA, E QUANTO VEDEVA.  Fino a stasera il passo `pam` era ancorato
#    a
#
#        PAM ha risposto(?: \(pratica \d+\))?: (ammesso|respinto)
#
#    cioe' un'ancora che tollera **esattamente `(pratica N)` e niente altro**.
#    `[M]` provata riga per riga (`--controllo-ancora`), e' CIECA su tre forme:
#
#      1. un SECONDO campo in mezzo — «PAM ha risposto (pratica 2, aiutante 3):
#         ammesso»: il gruppo facoltativo non combacia, e allora i due punti
#         devono venire subito dopo «risposto», che non e' il caso;
#      2. un campo NON NUMERICO — «PAM ha risposto (pratica ROSSA): ammesso»:
#         `\d+` non ci arriva, e cade come sopra;
#      3. DUE SPAZI dopo i due punti — «PAM ha risposto:  ammesso»: lo spazio
#         nell'ancora e' uno solo, ed e' scritto in chiaro.
#
# ⛔ E NESSUNA DELLE TRE SI SAREBBE FATTA SENTIRE.  Il passo `pam` giudica
#    `atteso in trovate`, e `re.findall` su una riga che non combacia torna la
#    lista vuota — cioe' **`trovate=0`**, che ha esattamente la stessa faccia di
#    «il server non ha mai risposto».  E' la forma **E8** di `REVIEWER.md` §2,
#    ed e' la stessa che stamattina ha accecato B8 per un giro intero di
#    ricertificazione (`01-b8-cronometro.py`, riquadro «come si legge un verdetto
#    di PAM nel registro»).
#
# ⭐ LA FORMA DI CASA, gia' in `01-b8-cronometro.py` (`R_PAM`) e in
#    `01-b10-secondo-utente.py` (`R_RCP_VERDETTO`), ed e' la stessa stringa in
#    tutt'e tre: ci si ancora al **pezzo stabile** — il nome del fatto e la
#    parola che lo qualifica — e si lascia libero **tutto quel che sta in mezzo e
#    tutto quel che viene dopo**.
#
# ⛔⭐ E LA CURA VERA NON E' LA REGEX: E' IL CONTROLLO POSITIVO.  Una regex piu'
#     larga chiude le tre forme di oggi e non dice niente della quarta, che
#     qualcuno aggiungera' domani — e quel giorno la cecita' tornerebbe **muta**,
#     esattamente come oggi.  ⇒ Sotto c'e' `controllo_positivo_ancora()`, che a
#     ogni giro da' all'ancora le righe **vere** (lette nei registri del prodotto
#     e dell'innesto) piu' quelle che le si allungheranno addosso, e pretende che
#     l'esito **non cambi**.  E' `REVIEWER.md` §1 punto 5 applicato al lettore
#     del registro.
#
# ⚠ E SONO DUE APPIGLI, NON UNO, perche' sono due fatti diversi:
#     · `RIGA_PAM`    «questa e' una riga di PAM»;
#     · `R_PAM`       «e so leggerne il verdetto».
#   *«Non c'e' nessuna riga di PAM»* e *«c'e' una riga di PAM che non so
#   leggere»* non devono avere la stessa faccia: la seconda e' un difetto **di
#   questo file**, e va detta a voce alta invece di essere arrotondata a uno zero.
ANCORA_PAM = r"PAM ha risposto\b[^:]*:\s*(ammesso|respinto)\b"
RIGA_PAM = "PAM ha risposto"
R_PAM = re.compile(ANCORA_PAM)


def verdetto_nel_registro(testo):
    """(stato, verdetto, quante) — ⛔ e gli stati sono TRE, non due.

        `assente`      nessuna riga di PAM — non si sa niente, e «non ho potuto
                       guardare» non si arrotonda a «non c'e'»;
        `illeggibile`  la riga c'e' e l'ancora non la apre — ⛔ e' un difetto
                       DEL BANCO, ed e' il caso che il 12 agosto 2026 e' passato
                       inosservato due volte perche' non aveva un nome;
        `letto`        e allora il verdetto e' «ammesso» o «respinto».

    ⚠ Si tiene l'**ultimo** verdetto: il testo che arriva qui e' gia' il
      segmento della gamba, quindi le righe sono di questo giro.
    """
    righe = [r for r in testo.splitlines() if RIGA_PAM in r]
    if not righe:
        return "assente", None, 0
    letti = [m.group(1) for m in map(R_PAM.search, righe) if m]
    if not letti:
        return "illeggibile", None, len(righe)
    return "letto", letti[-1], len(righe)


# ⛔ I CASI SI IMPORTANO DA B10, NON SI RICOPIANO.  `CASI_ANCORA` e' nato la' il
#    12 agosto 2026 **per essere riusato**, e sono le righe vere lette nei
#    registri veri del server.  ⚠ Ricopiarle qui vorrebbe dire che il giorno in
#    cui il prodotto scrive una quarta forma i due banchi la imparano in momenti
#    diversi — cioe' due letture della stessa riga sotto la stessa etichetta,
#    che e' la forma E2.
#
# ⛔ E SI IMPORTANO I **CASI**, NON IL CONTROLLO.  `controllo_positivo_ancora()`
#    di B10 giudica l'ancora **di B10**, risolta dai globali del suo modulo:
#    chiamarla da qui direbbe «l'ancora regge» guardando un'altra ancora, e
#    questo file resterebbe cieco senza saperlo — ⇒ il rovescio esatto del
#    difetto che si sta curando.  ⚠ E si e' scartata anche la strada di
#    sostituire il lettore dentro il modulo di B10 (`b10.verdetto_nel_registro =
#    …`): cambierebbe il comportamento di B10 in corsa, e chi legge non avrebbe
#    nessun modo di accorgersene.  ⇒ I casi sono in comune, il giudizio e' di
#    ciascuno sul proprio.
def carica_casi_b10():
    """(casi, errore).  ⛔ Uno dei due e' sempre None: «non ho potuto caricare»
    non e' «nessun caso», ed e' la distinzione che questo file esiste per fare."""
    percorso = QUI / "01-b10-secondo-utente.py"
    try:
        spec = importlib.util.spec_from_file_location("b10ancora", percorso)
        if spec is None or spec.loader is None:
            return None, f"⛔ «{percorso}» non si e' potuto caricare"
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        casi = getattr(modulo, "CASI_ANCORA", None)
        if not casi:
            return None, f"⛔ «{percorso}» non porta piu' CASI_ANCORA"
        return list(casi), None
    except Exception as sbaglio:  # noqa: BLE001 — il tipo dell'errore E' la misura
        return None, f"⛔ {type(sbaglio).__name__}: {sbaglio}"


# ⚠ E TRE CASI IN PIU', CHE LA LISTA DI B10 NON PORTA — le due forme su cui
#   l'ancora vecchia di QUESTO file era cieca e che la' non servivano, piu' la
#   riga di PAM assente.  ⛔ Stanno qui e non la': `01-b10-*` e' di un altro
#   mandato, e un caso aggiunto nel file di un altro e' un file di due padroni.
CASI_ANCORA_P5 = [
    ("⏳ un campo NON NUMERICO in mezzo — «(pratica ROSSA)»: `\\d+` non ci arriva",
     "16:35:48.273 rcp     PAM ha risposto (pratica ROSSA): ammesso",
     "letto", "ammesso"),
    ("⏳ DUE SPAZI dopo i due punti: un allineamento a colonne, e l'ancora "
     "vecchia aveva lo spazio scritto in chiaro",
     "16:35:48.273 rcp     PAM ha risposto:  ammesso",
     "letto", "ammesso"),
    ("⛔ la riga tagliata a meta' dopo «risposto»: nessun verdetto, e "
     "«illeggibile» non e' «assente»",
     "16:35:48.273 rcp     PAM ha risposto (pratica 4)",
     "illeggibile", None),
]


def controllo_positivo_ancora(dettaglio=True):
    """⭐ (falliti, quanti) — l'ancora sa ancora leggere quel che c'e' di sicuro?

    ⛔ Gira a OGNI comando `passi`, prima di qualunque conteggio, e non e' una
       cerimonia: un controllo che si esegue solo quando qualcuno se lo ricorda
       e' un controllo che il giorno che serve non c'era.  Costa microsecondi,
       non tocca il server, non legge nessun file del giro.
    """
    casi, sbaglio = carica_casi_b10()
    if casi is None:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ i casi dell'ancora non si sono caricati da "
              f"01-b10-secondo-utente.py:")
        print(f"      {sbaglio}")
        print("      ⛔ E questo NON e' «l'ancora regge»: e' «non ho potuto")
        print("         provarla», e i due non si arrotondano.")
        print(f"      ⇒ {MARCA_ANCORA_ROTTA}")
        return 1, 0
    tutti = casi + CASI_ANCORA_P5
    falliti = []
    for che, riga, stato_atteso, verdetto_atteso in tutti:
        stato, verdetto, _ = verdetto_nel_registro(riga)
        buono = (stato == stato_atteso and verdetto == verdetto_atteso)
        if not buono:
            falliti.append((che, riga, stato_atteso, verdetto_atteso,
                            stato, verdetto))
        elif dettaglio:
            print(f"{VERDE}OK{GRIGIO}  {che}  ⇒ {stato}"
                  + (f"/{verdetto}" if verdetto else ""))
    for che, riga, sa, va, so, vo in falliti:
        print(f"{ROSSO}NO{GRIGIO}  {che}")
        print(f"      atteso «{sa}" + (f"/{va}" if va else "")
              + f"», ottenuto «{so}" + (f"/{vo}" if vo else "") + "»")
        print(f"      riga: {riga[:110]}")
    if falliti:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ L'ANCORA AL VERDETTO DI PAM E' ROTTA: "
              f"{len(falliti)} casi su {len(tutti)}.")
        print(f"      ancora: {ANCORA_PAM}")
        print("      ⛔ Finche' questa riga e' rossa un verde di P5 non vale: il")
        print("         passo «pam» puo' dire `trovate=0` su un server che ha")
        print("         risposto, ed e' un ROSSO SUL BANCO, non sul prodotto.")
        print(f"      ⇒ {MARCA_ANCORA_ROTTA}")
    elif dettaglio:
        print(f"{VERDE}OK{GRIGIO}  ⭐ tutte e {len(tutti)} — l'ancora regge alle "
              f"forme vere, a quelle di domani, e dice di no a quel che non "
              f"porta un verdetto")
    else:
        print(f"{VERDE}OK{GRIGIO}  A0 — l'ancora al verdetto di PAM: "
              f"{len(tutti)} casi su {len(tutti)} ({len(casi)} da B10 + "
              f"{len(CASI_ANCORA_P5)} di qui)")
    return len(falliti), len(tutti)


# ===========================================================================
# `passi` — il registro del server, segmentato per motore
# ===========================================================================
#
# ⛔ Ogni passo dichiara: la riga che lo prova, quante volte l'ha trovata, e
#    quante ne voleva.  Un conteggio senza denominatore non e' una misura
#    (`LEZIONI.md` §1.9, quarta regola).
#
# ⚠ I testi qui sotto sono LETTI da `src/rcp.c` e `src/pagina.c` dell'11 agosto
#   2026, non ricordati.  Se il server cambia una di queste frasi, questo banco
#   deve dare ROSSO su «passo non trovato» — non verde: e' la ragione per cui
#   ogni passo obbligatorio pretende almeno un'occorrenza, e per cui esiste il
#   passo `pagina-servita`, che se manca dice che si sta leggendo il registro
#   sbagliato.
PASSI = [
    ("pagina-servita",   r"GET / da ",                                   1, None),
    # ⛔⭐ IL RITIRO DELL'IMPRONTA — passo NUOVO, 12 agosto 2026, difetto D11.
    #
    # `RCP.md` §4.1-bis, rilievo **R1.14**: se l'impronta che la pagina ha in
    # mano e quella del certificato di sessione divergono, la sessione
    # WebTransport non si apre e **nessun errore nomina l'impronta** — il
    # sintomo che arriva a chi guarda e' «WebTransport non si connette», che ha
    # almeno quattro cause diverse.  ⭐ Delle due cure §4.1-bis ne sceglie una,
    # e il prodotto l'ha applicata: **la pagina RITIRA `/impronta` prima di ogni
    # tentativo** (`src/pagina.html`, funzione `impronta()`), e usa quella
    # servita con la pagina solo come ripiego dichiarato.
    #
    # ⛔ E FINO A OGGI NESSUNA RIGA DI QUESTO BANCO GUARDAVA IL RITIRO.  Il
    #    banco confrontava i VALORI — l'impronta scritta nella pagina servita
    #    contro quella dell'endpoint — cioe' la cosa che su questo prodotto
    #    **non decide niente**, perche' il valore servito viene scavalcato dal
    #    ritiro.  ⇒ Il guasto di catalogo faceva virare P5 per una ragione piu'
    #    debole di quella che dichiarava (difetto **D11**), e una pagina che
    #    smettesse di ritirare — cioe' R1.14 vivo — sarebbe passata VERDE.
    #
    # ⭐ Si guarda dal lato che RICEVE (`CODER.md` §3.8): il ritiro e' una
    #    richiesta HTTP ordinaria, e `src/pagina.c` la registra prima di
    #    servirla — `GET /impronta da <indirizzo>`.  «La pagina ha chiamato
    #    fetch» e «la richiesta e' arrivata» sono due fatti diversi, e qui si
    #    prende il secondo.
    # ⚠ Il conteggio e' sul SEGMENTO della gamba, quindi il `curl /impronta`
    #   che il lanciatore fa al passo 3 — molto prima del primo marcatore —
    #   non ci entra, e non puo' coprire un ritiro mancante.
    ("impronta-ritirata", r"GET /impronta da ",                          1, None),
    ("canale-controllo", r"canale di controllo aperto da ",              1, None),
    ("negoziato",        r"negoziato video\.codec=",                     1, None),
    ("credenziali",      r"CREDENZIALI ricevute utente=",                1, None),
    ("secondo-fisso",    r"il secondo fisso e' passato \((\d+) ms\)",    1, "ms"),
    # ⛔⭐ IL NUMERO DI PRATICA IN MEZZO — `[M]` 12 agosto 2026, sera, e questo
    #     passo era ROSSO su un prodotto SANO.
    #
    # Qui c'era `r"PAM ha risposto: (ammesso|respinto)"`.  La cura di
    # `DECISIONI.md` §1.10 (PAM esce dal filo unico) ha spostato la verifica in
    # un processo aiutante, e con essa la riga di registro: adesso il server
    # scrive `PAM ha risposto (pratica 3): respinto`, col numero di pratica che
    # dice QUALE domanda ha ricevuto risposta — ⭐ un'aggiunta giusta, perche'
    # con le verifiche in volo le risposte non tornano piu' in ordine.
    #
    # ⛔ Il vecchio ago non combaciava piu', e il passo usciva `trovate=0`, cioe'
    #    **NON-CONFORME su un server che aveva appena ammesso l'utente** — e le
    #    righe accanto lo dicevano (`ammesso trovate=1`, `respinto trovate=1`).
    #    ⇒ Un rosso puntato sull'imputato sbagliato: chi lo leggesse andrebbe a
    #    cercare un difetto di PAM dove PAM ha funzionato.
    #    ⚠ E il verso in cui ha sbagliato e' quello che si nota: se avesse
    #      sbagliato al contrario — un ago troppo largo — sarebbe rimasto verde,
    #      e non l'avrebbe visto nessuno.
    #
    # ⭐ Il numero di pratica e' FACOLTATIVO nell'ago, e non per indulgenza: il
    #    verdetto — `ammesso` o `respinto` — resta obbligatorio e resta la sola
    #    cosa che questo passo giudica.  Cosi' l'ago combacia con le due forme
    #    della riga (prima e dopo §1.10) senza allargare di un byte quel che
    #    pretende.
    #
    # ⛔⭐ E LA SERA DELLO STESSO GIORNO QUELL'AGO E' STATO ALLARGATO ANCORA, e
    #     stavolta con accanto il controllo che se ne accorge: tollerava
    #     **esattamente `(pratica N)` e niente altro**, ed era cieco su un
    #     secondo campo in mezzo, su un campo non numerico e su due spazi dopo i
    #     due punti — tutte e tre **in silenzio**, con la faccia di `trovate=0`.
    #     ⇒ L'ago adesso e' `ANCORA_PAM`, la forma di casa, ed e' **la stessa
    #     stringa** che legge il passo A0: cosi' il controllo positivo prova
    #     l'ago che questa tabella usa, e non una sua copia.  Il riquadro lungo
    #     sta sopra `ANCORA_PAM`.
    ("pam",              ANCORA_PAM,                                     1, "pam"),
    ("ammesso",          r"ammesso utente=",                             1, None),
    ("respinto",         r"respinto motivo=",                            0, None),
    ("posto-preso",      r"posto PRESO da .*occupati adesso: (\d+)",     1, "occupati"),
    ("sessione",         r"sessione aperta utente=",                     1, None),
    # ⛔⭐ SI CONTA IL MOTIVO, NON «UNA CHIUSURA QUALUNQUE» — cura della tarda
    #     serata dell'11 agosto 2026, e questo contatore e' costato il difetto
    #     piu' caro della fase.
    #
    #     Qui c'era `r"la pagina ha chiuso la sessione, motivo"`, SENZA il
    #     motivo.  ⛔ Su Chrome il server scriveva
    #
    #       ⛔ VIOLAZIONE §3.1 — la pagina ha chiuso la sessione col codice 0x0…
    #       la pagina ha chiuso la sessione, motivo 0x0b
    #
    #     cioe' **lo smontaggio del browser**, che §3.1 vieta — e questo passo lo
    #     contava come un congedo.  ⇒ Una violazione trasformata in un verde, e
    #     un difetto di prodotto assolto per un'ora (`01-p5-congedo.sh:318` aveva
    #     lo stesso difetto, e la sua copia porta l'avviso in testa).
    #
    # ⭐ §8.2 `CHIUSO_DALL_UTENTE` vale **0x01**, e in questa scena e' l'unico
    #    motivo giusto: un altro numero non e' un congedo, e' un'altra cosa.
    ("congedo-canale",   r"il client si congeda, motivo=0x01",           0, None),
    ("congedo-chiusura", r"la pagina ha chiuso la sessione, motivo 0x01", 0, None),
    # ⛔ E la violazione si conta a parte, perche' e' il server stesso a
    #    scriverla: era gia' nel registro mentre il banco stampava il verde.
    ("violazione-31",    r"VIOLAZIONE §3\.1",                            0, "zero"),
    # ⛔ IL POSTO SI LIBERA PER DUE STRADE, E LA SECONDA L'HA INSEGNATA IL
    #    REGISTRO VERO DEL 10 AGOSTO 2026 (`/media/REMOTIX/src/remotix-browser.log`,
    #    letto l'11 agosto).  Quel giro non ha **nessuna** riga `posto LASCIATO`:
    #    il browser e' stato chiuso di colpo, il client non si e' congedato, e il
    #    posto se n'e' andato trenta secondi dopo con
    #
    #      `STACCATO per silenzio: 30269 ms … (posti occupati adesso: 0; …)`
    #
    #    ⚠ Un banco che pretendesse solo la prima riga avrebbe dato ROSSO su un
    #      server che ha fatto il suo mestiere — e il rosso sarebbe finito
    #      sull'imputato sbagliato.  ⭐ Qui si contano tutt'e due, si giudica il
    #      NUMERO finale (che deve essere 0) e si dichiara **per quale strada**:
    #      la differenza fra le due e' precisamente cio' che distingue un client
    #      che si congeda da uno che sparisce.
    ("posto-lasciato",   r"posto LASCIATO da .*occupati adesso: (\d+)",  0, "occupati"),
    ("staccato-silenzio", r"STACCATO per silenzio: .*posti occupati adesso: (\d+)", 0, "occupati"),
    ("byte-dopo-la-fine", r"byte arrivati DOPO la fine",                 0, "zero"),
    ("tentativo-fallito", r"tentativo fallito da ",                      0, None),
    ("bannato",          r"BANNATO l'indirizzo ",                        0, "zero"),
    ("conto-azzerato",   r"il conto dei falliti torna a zero",           0, None),
]

# Che cosa ci si aspetta, scenario per scenario.  ⛔ Non e' una tabella di
# comodo: e' il posto in cui «l'atteso lo confronta il banco, non chi legge»
# (regola B0.4) diventa codice.
ATTESI = {
    # il giro buono: si arriva a SESSIONE, e il posto si libera alla fine
    "sessione": {
        "pagina-servita": 1,
        "canale-controllo": 1, "negoziato": 1, "credenziali": 1,
        "pam": "ammesso", "ammesso": 1, "posto-preso": 1, "sessione": 1,
        "byte-dopo-la-fine": 0, "respinto": 0,
        "tentativo-fallito": 0, "bannato": 0,
        # ⛔ Zero violazioni di §3.1: una chiusura col codice 0x0 non e' un
        #    congedo mal riuscito, e' un errore di protocollo che il server
        #    mette a verbale.  ⚠ Sta qui e non negli altri due scenari perche'
        #    QUESTA e' la scena misurata (`01-p5-ff-*`, due giri per motore):
        #    altrove il passo si dichiara e non si giudica.
        "violazione-31": 0,
        # ⚠ «posto-lasciato» NON e' qui: il posto si giudica sul NUMERO finale,
        #   piu' sotto, perche' le strade per liberarlo sono due.
    },
    # il controllo che dice NO, con la parola sbagliata
    "respinto": {
        "pagina-servita": 1,
        "canale-controllo": 1, "negoziato": 1, "credenziali": 1,
        "pam": "respinto", "respinto": 1, "ammesso": 0, "sessione": 0,
        "posto-preso": 0, "tentativo-fallito": 1, "bannato": 0,
    },
    # il controllo che dice NO, con l'impronta storpiata: la sessione
    # WebTransport non deve nemmeno nascere
    "niente-sessione": {
        "pagina-servita": 1, "canale-controllo": 0, "credenziali": 0,
        "sessione": 0, "posto-preso": 0, "tentativo-fallito": 0, "bannato": 0,
    },
}


def passi(percorso, marca_inizio, marca_fine, atteso, utente):
    # ── ⭐ A0: PRIMA DI CONTARE QUALUNQUE COSA, SI CONTROLLA LO STRUMENTO ────
    #
    # ⛔ Sta qui, in cima e prima della lettura del registro, e non in fondo: se
    #    l'ancora al verdetto di PAM e' rotta, il passo `pam` puo' gia' dire
    #    `trovate=0` su un server che ha risposto, **e chi legge deve saperlo
    #    prima di credere a qualunque riga sotto**.  ⚠ Non tocca il server, non
    #    tocca il registro e costa microsecondi: non c'e' nessun giro in cui
    #    valga la pena saltarlo.
    falliti_ancora, quanti_ancora = controllo_positivo_ancora(dettaglio=False)
    try:
        testo = Path(percorso).read_text(encoding="utf-8", errors="replace")
    except Exception as sbaglio:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ il registro del server non si legge ({sbaglio}).")
        print("      Non e' «nessun passo»: e' «non ho potuto guardare» — §1.9.")
        return None, 3
    tutte = testo.splitlines()

    # ── Il segmento, e i suoi due denominatori ──────────────────────────────
    inizi = [i for i, r in enumerate(tutte) if marca_inizio in r]
    fini = [i for i, r in enumerate(tutte) if marca_fine in r]
    esito = {
        "righe_nel_registro": len(tutte),
        "marca_inizio": marca_inizio, "marca_inizio_trovata": len(inizi),
        "marca_fine": marca_fine, "marca_fine_trovata": len(fini),
        # ⭐ A0 finisce nel registro dei fatti come tutto il resto: un controllo
        #    che gira e non lascia traccia non si puo' confrontare fra due giri.
        "ancora_pam": ANCORA_PAM,
        "ancora_casi": quanti_ancora, "ancora_falliti": falliti_ancora,
    }
    if not inizi or not fini:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ i marcatori non ci sono tutt'e due "
              f"(inizio {len(inizi)}, fine {len(fini)}) su {len(tutte)} righe.")
        print("      ⛔ E questo NON e' «il motore ha fallito»: e' «il motore non")
        print("         ha nemmeno parlato col server», oppure «sto leggendo un")
        print("         registro che non e' di questo giro».  Due cause opposte,")
        print("         e nessun verdetto si da' su nessuna delle due.")
        esito["verdetto"] = "SENZA-DENOMINATORE"
        return esito, 2
    segmento = tutte[inizi[-1]: fini[-1] + 1]
    esito["righe_nel_segmento"] = len(segmento)
    corpo = "\n".join(segmento)

    # ── I passi ─────────────────────────────────────────────────────────────
    voluti = ATTESI.get(atteso)
    if voluti is None:
        print(f"{ROSSO}NO{GRIGIO}  scenario «{atteso}» sconosciuto: "
              f"i noti sono {', '.join(sorted(ATTESI))}")
        return esito, 3
    esito["scenario"] = atteso
    esito["passi"] = {}
    guasti = 0
    approvati = 0
    for nome, modello, _minimo, extra in PASSI:
        trovate = re.findall(modello, corpo)
        quante = len(trovate)
        voce = {"trovate": quante, "modello": modello}
        if extra == "ms" and trovate:
            voce["ms"] = [int(x) for x in trovate]
        elif extra in ("pam", "occupati") and trovate:
            voce["valori"] = trovate
        if nome in voluti:
            atteso_qui = voluti[nome]
            approvati += 1
            if isinstance(atteso_qui, int):
                voce["atteso"] = atteso_qui
                if atteso_qui == 0:
                    voce["ok"] = (quante == 0)
                else:
                    voce["ok"] = (quante >= atteso_qui)
            else:  # un valore, non un conteggio (PAM)
                voce["atteso"] = atteso_qui
                voce["ok"] = atteso_qui in trovate
            if not voce["ok"]:
                guasti += 1
        else:
            voce["atteso"] = "—  (dichiarato, non giudicato)"
            voce["ok"] = None
        esito["passi"][nome] = voce

    # ── ⭐ A0, GIUDICATO: uno strumento cieco non da' nessun verdetto ────────
    #
    # ⛔ Il controllo e' gia' girato in cima (il suo esito e' stampato la'); qui
    #    entra nel conto, e conta **sempre** — anche nel giro sano, anche nelle
    #    gambe che non giudicano PAM.  ⚠ E' un controllo sul BANCO, non sulla
    #    scena: se dipendesse dallo scenario, ci sarebbe uno scenario in cui lo
    #    strumento non si guarda.
    approvati += 1
    if falliti_ancora:
        guasti += 1
        esito["ancora_verdetto"] = "ROTTA"
        print(f"{ROSSO}NO{GRIGIO}  ⛔ e il rosso qui sopra e' del BANCO, non del "
              f"server ({MARCA_ANCORA_ROTTA}):")
        print("      quel che questo giro ha contato sul passo «pam» e' stato")
        print("      letto con un'ancora che non combacia piu'.")
    else:
        esito["ancora_verdetto"] = "REGGE"

    # ── ⛔ LA RIGA DI PAM: TRE ESITI, NON DUE ────────────────────────────────
    #
    # ⛔ `re.findall` sul passo `pam` sa dire soltanto **quante** ne ha lette, e
    #    la sua lista vuota copre due fatti opposti: «il server non ha mai
    #    risposto» e «ha risposto e io non so leggerlo».  E' la forma **E8**, ed
    #    e' esattamente il modo in cui l'ancora vecchia sarebbe tornata muta.
    # ⭐ Qui si separano, e il secondo caso e' un rosso **sul banco**: la riga
    #    c'e', porta il nome del fatto, e l'ancora non la apre.
    stato_pam, verdetto_pam, righe_pam = verdetto_nel_registro(corpo)
    esito["pam_lettura"] = {"stato": stato_pam, "verdetto": verdetto_pam,
                            "righe_di_pam": righe_pam}
    if stato_pam == "illeggibile":
        # ⛔ E IL GUASTO SI CONTA UNA VOLTA SOLA.  Quando lo scenario giudica
        #    `pam`, il passo qui sopra ha gia' messo il suo rosso (`trovate=0`):
        #    questa riga non ne aggiunge un secondo — **cambia l'imputato**, che
        #    e' tutto quel che serviva e che prima mancava.  ⚠ Contarlo due
        #    volte gonfierebbe il denominatore del verdetto con lo stesso fatto,
        #    ed e' la stessa ragione per cui il ritiro dell'impronta non si
        #    giudica quando la pagina non e' stata servita.
        gia_contato = (esito["passi"]["pam"]["ok"] is False)
        if not gia_contato:
            approvati += 1
            guasti += 1
        print(f"{ROSSO}NO{GRIGIO}  ⛔ {righe_pam} riga/e «{RIGA_PAM}» ci sono in "
              f"questo segmento e NON SI LASCIANO LEGGERE")
        print(f"      dall'ancora «{ANCORA_PAM}».")
        print("      ⛔ Il primo imputato e' il BANCO (`REVIEWER.md` §1): il")
        print("         server ha scritto il verdetto, e sono io a non saperlo")
        print("         piu' leggere.  ⛔ NON e' «PAM non ha risposto», e i due")
        print("         non si arrotondano.")
        if gia_contato:
            print("      ⇒ e il rosso del passo «pam» qui sotto va letto COSI':")
            print("         non e' il server che ha taciuto, e' questo file che")
            print("         non legge piu'.  Il guasto resta UNO.")
        print(f"      ⇒ {MARCA_ANCORA_ROTTA}")
    elif stato_pam == "assente" and atteso in ("sessione", "respinto"):
        # ⚠ Dichiarato, non giudicato due volte: il passo `pam` della tabella
        #   qui sopra lo conta gia' come guasto, e un secondo rosso sullo stesso
        #   fatto conterebbe due volte lo stesso guasto.
        print(f"{GIALLO}⚠{GRIGIO}   nessuna riga «{RIGA_PAM}» in questo "
              f"segmento — e non e' «illeggibile»: e' che non c'e' proprio.")

    # ── ⛔ IL RITIRO DELL'IMPRONTA (§4.1-bis, R1.14) — il passo che copre D11 ─
    #
    # ⛔ Si giudica **solo dove c'e' un tentativo di sessione**: le gambe
    #    `sessione` e `respinto` caricano la pagina del prodotto e provano ad
    #    aprire WebTransport, quindi li' `impronta()` deve essere passata di
    #    li'.  La gamba `niente-sessione` non passa dalla pagina del prodotto.
    #
    # ⛔⭐ E IL DENOMINATORE E' «LA PAGINA E' STATA SERVITA».  Senza, «la pagina
    #     non ritira» e «la pagina non e' mai arrivata al browser» avrebbero lo
    #     stesso aspetto — che e' la forma **E8** di `REVIEWER.md` §2, e in
    #     questo banco l'ha gia' pagata il congedo (uno zero da segmento
    #     sbagliato ha la stessa faccia di uno zero vero).  ⇒ Se la pagina non
    #     e' stata servita, il ritiro NON si giudica: lo dice gia' il passo
    #     `pagina-servita`, e un secondo rosso sullo stesso fatto conterebbe due
    #     volte lo stesso guasto.
    ritiri = esito["passi"]["impronta-ritirata"]["trovate"]
    servite = esito["passi"]["pagina-servita"]["trovate"]
    if atteso in ("sessione", "respinto"):
        if servite == 0:
            esito["ritiro_impronta"] = "NON-GIUDICABILE (la pagina non e' stata servita)"
            print(f"{GIALLO}⚠{GRIGIO}   il ritiro di /impronta non si giudica: in questo "
                  f"segmento la pagina non e' stata servita nemmeno una volta,")
            print("      e «non ritira» e «non e' mai arrivata» sarebbero lo stesso zero.")
        else:
            approvati += 1
            esito["ritiro_impronta"] = ritiri
            if ritiri == 0:
                print(f"{ROSSO}NO{GRIGIO}  ⛔ NESSUN RITIRO DI /impronta IN QUESTA GAMBA "
                      f"(§4.1-bis): la pagina e' stata")
                print(f"      servita {servite} volta/e e non ha chiesto «/impronta» nemmeno una.")
                print("      ⛔ §4.1-bis impone di RITIRARE l'impronta prima di ogni tentativo:")
                print("      senza, una scheda aperta da due settimane tiene l'impronta di un")
                print("      certificato gia' ruotato, la sessione non si apre e nessun errore")
                print("      la nomina — che e' il rilievo R1.14 per intero.")
                print("      ⚠ E qui la sessione puo' essersi aperta lo stesso: l'impronta")
                print("      servita e' fresca perche' il server e' stato riacceso adesso.")
                print("      ⛔ Il difetto NON e' il valore: e' che il ritiro non c'e' piu'.")
                guasti += 1
            else:
                print(f"{VERDE}OK{GRIGIO}  ⭐ la pagina ha ritirato «/impronta» prima del "
                      f"tentativo: {ritiri} volta/e (§4.1-bis)")
    else:
        esito["ritiro_impronta"] = "—  (dichiarato, non giudicato: questa gamba non passa dalla pagina)"

    # ── Le due strade del congedo (§3.1 punto 3) ────────────────────────────
    #
    # ⛔ Non e' un di piu': §3.1 punto 3 ne prevede DUE, e una delle due puo'
    #    perdersi.  ⚠ Pretenderne una sola scriverebbe «non si congeda» su un
    #    client che si e' congedato per l'altra.  Qui si contano tutt'e due e si
    #    dichiara QUALE.
    #
    # ⛔ E LA VECCHIA RAGIONE SCRITTA QUI ERA FALSA: diceva «due strade diverse,
    #    una per motore — Chrome sul canale, Firefox nel codice di chiusura».
    #    `[M]` 11 agosto 2026, `banchi/01-p5-ff-*`, due giri per motore: curato
    #    il prodotto, **tutt'e due i motori consegnano tutt'e due le strade** col
    #    motivo 0x01.  Quel che sembrava «la strada di Chrome» era la chiusura
    #    col codice 0x0 — cioe' la violazione che il passo qui sopra adesso
    #    conta.  ⚠ Una osservazione contraria: il `CONGEDO` **sul canale** si e'
    #    perso una volta su sei giri (una corsa gia' vista su Chrome da B11), e
    #    il motivo e' arrivato lo stesso per il codice di chiusura — che e'
    #    esattamente perche' le strade sono due (`DECISIONI.md` §7.14).
    canale = esito["passi"]["congedo-canale"]["trovate"]
    chiusura = esito["passi"]["congedo-chiusura"]["trovate"]
    esito["congedo"] = {
        "sul_canale_di_controllo": canale,
        "nel_codice_di_chiusura": chiusura,
        "strada": ("canale" if canale and not chiusura else
                   "chiusura" if chiusura and not canale else
                   "tutt'e due" if canale and chiusura else "NESSUNA"),
    }
    if atteso == "sessione" and canale + chiusura == 0:
        print(f"{ROSSO}NO{GRIGIO}  ⛔ nessun congedo, per nessuna delle due strade "
              f"di §3.1: §8.1 lo impone senza condizioni")
        guasti += 1
    if atteso == "sessione":
        approvati += 1

    # ── ⛔ IL POSTO, e questo e' il punto che un motore solo non vede ────────
    #
    #    §8.2 `0x0F`: il posto non si liberava quando a chiudere il canale era
    #    il SERVER — visto **solo su Chrome**, perche' su Firefox il trasporto
    #    chiudeva lo stream in tempo e il posto se ne andava lo stesso.  Il
    #    numero che lo dice e' «occupati adesso: N» dell'ultima riga
    #    `posto LASCIATO`.
    lasciato = esito["passi"]["posto-lasciato"].get("valori") or []
    silenzio = esito["passi"]["staccato-silenzio"].get("valori") or []
    if lasciato and silenzio:
        strada_posto = "tutt'e due"
    elif lasciato:
        strada_posto = "congedo del client (posto LASCIATO)"
    elif silenzio:
        strada_posto = "⚠ tetto d'inattivita' (STACCATO per silenzio) — il client NON si e' congedato"
    else:
        strada_posto = "NESSUNA"
    ultimo = (lasciato + silenzio)[-1] if (lasciato or silenzio) else None
    esito["posto_finale_occupati"] = int(ultimo) if ultimo is not None else None
    esito["posto_strada"] = strada_posto
    if atteso == "sessione":
        approvati += 1
        if esito["posto_finale_occupati"] != 0:
            print(f"{ROSSO}NO{GRIGIO}  ⛔ IL POSTO NON SI E' LIBERATO: "
                  f"«occupati adesso» finisce a {esito['posto_finale_occupati']} "
                  f"(strada: {strada_posto})")
            print("      §8.2 0x0F — ed e' il difetto che si vede SOLO nella")
            print("      differenza fra i due motori: con un motore solo, questa")
            print("      riga e' verde per il motore sbagliato.")
            guasti += 1
        elif not lasciato:
            # ⚠ Non e' un guasto del server: e' un fatto sul CLIENT, e va detto.
            print(f"{GIALLO}⚠{GRIGIO}   il posto si e' liberato, ma per il tetto "
                  f"d'inattivita' e non per un congedo: §8.1 impone al client di")
            print("      dire perche' chiude, e qui non l'ha detto — oppure il")
            print("      browser e' stato chiuso di colpo dal banco.")

    esito["controlli_approvati"] = approvati
    esito["guasti"] = guasti
    # ⛔ Anche un verdetto ha un denominatore (§1.9, sesta regola): se non ha
    #    giudicato niente, non da' nessun esito.
    if approvati == 0:
        esito["verdetto"] = "NESSUN-CONTROLLO"
        return esito, 2
    esito["verdetto"] = "CONFORME" if guasti == 0 else "NON-CONFORME"
    return esito, (0 if guasti == 0 else 1)


def stampa_passi(esito):
    print(f"    --  A0, l'ancora al verdetto di PAM: "
          f"{esito.get('ancora_verdetto', '— (non giudicata)')} "
          f"— {esito.get('ancora_casi')} casi, "
          f"{esito.get('ancora_falliti')} falliti")
    p = esito.get("pam_lettura") or {}
    print(f"    --  la riga di PAM in questo segmento: {p.get('stato', '—')}"
          + (f"/{p['verdetto']}" if p.get("verdetto") else "")
          + f" ({p.get('righe_di_pam', '—')} riga/e)")
    print(f"    -- registro del server: {esito['righe_nel_registro']} righe, "
          f"il segmento di questo motore ne ha {esito.get('righe_nel_segmento', '—')}")
    print(f"    -- marcatori: inizio ×{esito['marca_inizio_trovata']}, "
          f"fine ×{esito['marca_fine_trovata']}")
    for nome, voce in (esito.get("passi") or {}).items():
        if voce["ok"] is None:
            segno = "  "
        else:
            segno = f"{VERDE}OK{GRIGIO}" if voce["ok"] else f"{ROSSO}NO{GRIGIO}"
        extra = ""
        if "ms" in voce:
            extra = f"  ms={voce['ms']}"
        elif "valori" in voce:
            extra = f"  valori={voce['valori']}"
        print(f"    {segno}  {nome:<20} trovate={voce['trovate']:<3} "
              f"atteso={voce['atteso']}{extra}")
    print(f"    --  ritiro di /impronta prima del tentativo (§4.1-bis): "
          f"{esito.get('ritiro_impronta', '—')}")
    c = esito.get("congedo") or {}
    print(f"    --  congedo: sul canale {c.get('sul_canale_di_controllo')}, "
          f"nel codice di chiusura {c.get('nel_codice_di_chiusura')} "
          f"⇒ strada «{c.get('strada')}»")
    print(f"    --  posto, «occupati adesso» finale: {esito.get('posto_finale_occupati')} "
          f"— strada: {esito.get('posto_strada')}")
    print(f"    --  controlli approvati: {esito.get('controlli_approvati')}, "
          f"guasti: {esito.get('guasti')}")


# ===========================================================================
def principale():
    p = argparse.ArgumentParser(add_help=True)
    sub = p.add_subparsers(dest="comando", required=True)

    a = sub.add_parser("aggiungi"); a.add_argument("json")
    sub.add_parser("righe")
    # ⭐ Il controllo positivo dell'ancora, da solo e SENZA NIENTE: non serve ne'
    #    il registro del server, ne' un giro, ne' un browser.  ⛔ Gira comunque a
    #    ogni comando `passi`; questa forma esiste perche' lo si possa provare in
    #    un secondo dopo aver toccato una riga di registro nel prodotto — che e'
    #    precisamente il momento in cui, il 12 agosto 2026, nessuno l'ha fatto.
    sub.add_parser("controllo-ancora")
    for nome in ("elenco", "battuta"):
        s = sub.add_parser(nome)
        s.add_argument("--giro", required=True)
        s.add_argument("--da", type=int, default=0)
    c = sub.add_parser("cerca")
    c.add_argument("--giro", required=True)
    c.add_argument("--da", type=int, default=0)
    c.add_argument("--tipo", required=True)
    q = sub.add_parser("passi")
    q.add_argument("--log", required=True)
    q.add_argument("--marca-inizio", required=True)
    q.add_argument("--marca-fine", required=True)
    q.add_argument("--atteso", default="sessione")
    q.add_argument("--utente", default="prova")
    q.add_argument("--registra", default=None,
                   help="json di contorno da unire alla riga scritta nel registro")
    a2 = p.parse_args()

    if a2.comando == "aggiungi":
        return aggiungi(a2.json)

    if a2.comando == "controllo-ancora":
        print("== A0 — ⭐ il CONTROLLO POSITIVO dell'ancora al verdetto di PAM")
        print("   le righe vere del prodotto e dell'innesto, piu' quelle che le")
        print("   si allungheranno addosso: l'esito NON deve cambiare")
        print(f"   ancora: {ANCORA_PAM}\n")
        falliti, _quanti = controllo_positivo_ancora(dettaglio=True)
        print()
        return 1 if falliti else 0

    if a2.comando == "righe":
        righe, guasto = leggi()
        if guasto:
            print(guasto, file=sys.stderr)
            print(0)
            return 3
        print(len(righe))
        return 0

    if a2.comando == "elenco":
        trovata, stato, quante = cerca(a2.giro, a2.da, "ELENCO")
        if stato:
            print(f"⛔ nessun ELENCO per il giro «{a2.giro}» dopo la riga {a2.da} "
                  f"(righe guardate: {quante})", file=sys.stderr)
            return stato
        n, d = trovata
        for i, voce in enumerate(d.get("elenco") or []):
            print(i, voce.get("xdo"), int(bool(voce.get("verdetto"))),
                  int(bool(voce.get("distruttiva"))), voce.get("che", ""), sep="\t")
        return 0

    # ⛔ E QUANDO NON C'E', NON SI STAMPA NIENTE SU STANDARD OUTPUT.
    #
    #    Difetto trovato dal primo giro di certificazione, 11 agosto 2026.
    #    Qui c'era `print("NIENTE")`, e `cerca` stampava `NIENTE\t(righe
    #    guardate: N)`: chi legge con `$(...)` riceveva una **stringa non
    #    vuota** per dire «non c'e'», e il `[ -n "$fuoco" ]` del pilota era vero
    #    **sempre**.  ⛔ Risultato: 26 combinazioni su 26 dichiarate «consegnata
    #    E riservata» — un verdetto uniforme, prodotto da uno strumento che
    #    diceva «qualcosa» ogni volta che non aveva trovato niente.
    #
    # ⭐ Ed e' `LEZIONI.md` §1.9 nella sua forma piu' nuda: «vuoto» e «trovato»
    #    con lo stesso aspetto, stavolta dentro un attrezzo scritto per non
    #    farlo succedere.  La diagnostica va su standard error, dove non
    #    inquina il valore; lo stato d'uscita resta l'unico canale del «c'e'».
    if a2.comando == "battuta":
        trovata, stato, quante = cerca(a2.giro, a2.da, "BATTUTA")
        if stato == 3:
            return 3
        if stato:
            print(f"nessuna BATTUTA dopo la riga {a2.da} "
                  f"(righe guardate: {quante})", file=sys.stderr)
            return 1
        n, d = trovata
        mods = "".join(x for x, v in (("ctrl", d.get("ctrl")), ("alt", d.get("alt")),
                                      ("shift", d.get("shift")), ("meta", d.get("meta")))
                       if v)
        print(n, d.get("key"), d.get("code"), mods or "-", d.get("cancelable"), sep="\t")
        return 0

    if a2.comando == "cerca":
        trovata, stato, quante = cerca(a2.giro, a2.da, a2.tipo)
        if stato == 3:
            return 3
        if stato:
            print(f"nessun «{a2.tipo}» dopo la riga {a2.da} "
                  f"(righe guardate: {quante})", file=sys.stderr)
            return 1
        n, d = trovata
        print(n, json.dumps(d, ensure_ascii=False)[:400], sep="\t")
        return 0

    if a2.comando == "passi":
        esito, stato = passi(a2.log, a2.marca_inizio, a2.marca_fine,
                             a2.atteso, a2.utente)
        if esito is not None:
            stampa_passi(esito)
            contorno = {}
            if a2.registra:
                try:
                    contorno = json.loads(a2.registra)
                except Exception:
                    contorno = {"contorno_non_json": a2.registra}
            contorno.update({"tipo": "PASSI", "esito": esito})
            aggiungi(json.dumps(contorno, ensure_ascii=False))
        return stato
    return 3


if __name__ == "__main__":
    sys.exit(principale())
