#!/usr/bin/env python3
"""02-filo-validatore.py — ⛔ F2.4: l'arbitro meccanico impara il CANALE VIDEO.

    python3 02-filo-validatore.py registrazione.rcpreg
    python3 02-filo-validatore.py --fabbrica       costruisce le registrazioni di prova
    python3 02-filo-validatore.py --certifica      sano -> G4 -> risanato
    python3 02-filo-validatore.py --uscita 02-filo-esiti.jsonl reg.rcpreg

    uscita 0  il canale video e' conforme — e si dice SU QUANTI fotogrammi
    uscita 1  non e' conforme — e si dice QUALE byte e QUALE regola
    uscita 2  la REGISTRAZIONE e' rotta, o non si legge (non e' un giudizio sul filo)
    uscita 3  ⛔ non c'e' NIENTE DA GIUDICARE: zero blocchi sul canale video

===========================================================================
⛔ PERCHE' ESISTE, E NON E' UN DOPPIONE DI `01-b4-validatore.py`

`PIANO.md` §0.4 elenca **tre** sostituti dell'arbitro che abbiamo perso con
`mstsc`, e il validatore del filo e' quello **meccanico**: *«vede i byte non
conformi, ma solo quelli»*.

⛔ **E oggi non vede il video.**  `01-b4-validatore.py`, riga 521:

    if canale != 0x00:
        print(f"   blocco {nb}: canale {CANALI[canale]} dal {chi}, "
              f"{lung} byte — non giudicato da questo validatore")
        continue

⚠ E' una riga onesta — **dichiara** di non giudicare, che e' il contrario di
assolvere — ma la conseguenza e' che dal primo fotogramma in poi il capitolo
piu' voluminoso del filo torna a essere validato da **una sola**
implementazione, scritta dalla stessa mano che scrive il server.  ⛔ E' lo
stato che `RCP.md` §0 descrive come il difetto muto: *«se il server emette una
sciocchezza, il nostro client la accettera' volentieri»*.

⭐ **E il precedente dice che non e' teorico**: delle due contraddizioni interne
di `RCP.md` trovate nella fase 1, **una l'ha trovata questo strumento** — il
trattino basso di §4.3, alla prima esecuzione, prima che esistesse un byte di
server (`RCP.md` §4.3, riquadro del 10 agosto 2026).  ⛔ Tutt'e due sono state
trovate da programmi che leggevano **solo quel documento**, e **nessuna delle
due** da chi lo rileggeva.

===========================================================================
⛔ E QUESTO FILE NON TOCCA `01-b4-validatore.py`

Il mandato della fase 2 (§2): *«nessuno scrive fuori dai propri file»*.  B4 e'
della fase 1.  ⭐ Qui il canale video si giudica **accanto** a B4, con lo stesso
formato e gli stessi codici d'uscita, e la proposta di fonderli sta nel
rapporto `fasi/rapporti/F2-4-filo.md`: e' una decisione del coordinatore, non
di un sottoagente.

⚠ **E il giudizio non e' riscritto due volte**: importa `02-filo-fotogramma.py`,
che e' il giudice scritto leggendo `RCP.md` §6.2.  Due copie del giudizio
sarebbero due implementazioni della stessa lettura, cioe' precisamente cio' che
questo strumento esiste per impedire.

===========================================================================
⛔⭐ IL BUCO CHE QUESTO STRUMENTO HA TROVATO NEL FORMATO — proposta P7

`RCP.md` §11.1 descrive il blocco della registrazione:

    ├── u8   verso · u8 canale · u64 stream · u32 lunghezza
    ├── u16  quanti_oscurati  (+ gli intervalli)
    └── `lunghezza` byte di carico

⛔ **Non c'e' nessun campo che dica COME E' FINITO LO STREAM.**  E per il video
quella e' la distinzione piu' importante che il documento abbia: §6.2, rilievo
**R1.7** della sera del 9 agosto 2026, aggiunse due parole — *«ma solo se lo
stream e' finito con un FIN»* — perche' senza di esse

  ⛔ *«un fotogramma abbandonato e uno completo avevano lo stesso aspetto»*,

che il documento stesso classifica come forma d'errore **E8**.  ⭐ La cura e'
stata scritta **sul filo**, e la registrazione la riapre: guardando un file
`.rcpreg`, l'arbitro non puo' distinguere un fotogramma troncato perche' il
server lo ha **abbandonato di proposito** (§5.1, legale, e la sessione regge)
da uno troncato perche' il server **ha sbagliato** (§3, la connessione cade).

⚠ Ed e' lo stesso buco che B9 aveva sfiorato sul canale di controllo — la
lettura **L3**, *«il bit FIN del frame STREAM che porta il `CONGEDO`: gli
stessi byte di carico, un bit di trasporto in piu'»* — senza dire che il
formato della registrazione non sa scriverlo.

⛔ **Che cosa fa questo strumento nel frattempo, e non e' indovinare**: conta i
fotogrammi di cui **non ha potuto** giudicare la completezza e lo stampa con il
suo denominatore.  «Non l'ho guardato» e «l'ho guardato e va bene» sono due
fatti diversi (`LEZIONI.md` §1.9), e un arbitro che assolvesse per default
sarebbe peggio di uno che sbaglia: sopra il suo verde ci si costruisce.

⭐ E la cura **non tocca §9**: un blocco di registrazione non e' un messaggio,
e il formato porta gia' la propria versione nella magia (`"RCPREG" 0x00 0x01`).
Il testo della proposta sta in fondo a `--elenco` e nel rapporto.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Il giudice si IMPORTA, non si ricopia.  Vedi l'intestazione.
_spec = importlib.util.spec_from_file_location(
    "f24", os.path.join(QUI, "02-filo-fotogramma.py"))
f24 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f24)

MAGIA = b"RCPREG\x00\x01"
RIEMPIMENTO = 0x2A          # §11.1
CLIENT, SERVER = 1, 2
CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}
VIDEO = 0x03

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


class NonConforme(Exception):
    def __init__(self, regola, dice, ass, rel):
        super().__init__(dice)
        self.regola, self.dice, self.ass, self.rel = regola, dice, ass, rel


class Malformata(Exception):
    """La REGISTRAZIONE e' rotta: non e' un giudizio sul filo."""


class NienteDaGiudicare(Exception):
    """⛔ Nel file non c'e' nessun blocco video.  Non e' «conforme»."""


# ---------------------------------------------------------------------------
def leggi_blocchi(d):
    """I blocchi di §11.1, con i controlli che il formato impone.

    ⛔ I controlli del FORMATO stanno qui e sollevano `Malformata`, non
       `NonConforme`: *«una registrazione malformata e un filo non conforme
       sono due cose diverse, e vanno dette con due frasi diverse»* (§11.1).
    """
    if len(d) < 16 or d[:8] != MAGIA:
        raise Malformata("non comincia con la magia di RCP.md §11.1")
    quanti, riservato = struct.unpack("!II", d[8:16])
    if riservato != 0:
        raise Malformata(f"il campo riservato vale {riservato}, DEVE essere 0")
    p, fuori = 16, []
    for nb in range(quanti):
        if p + 16 > len(d):
            raise Malformata(f"il blocco {nb} comincia oltre la fine del file")
        verso, canale, stream, lung, nosc = struct.unpack("!BBQIH", d[p:p + 16])
        p += 16
        oscurati = []
        for _ in range(nosc):
            if p + 40 > len(d):
                raise Malformata(f"blocco {nb}: intervallo oscurato troncato")
            ini, qua = struct.unpack("!II", d[p:p + 8])
            p += 40
            if ini + qua > lung:
                raise Malformata(
                    f"blocco {nb}: intervallo oscurato [{ini},{ini + qua}) "
                    f"fuori dal carico di {lung} byte")
            for o, q in oscurati:
                if not (ini + qua <= o or ini >= o + q):
                    raise Malformata(
                        f"blocco {nb}: due intervalli oscurati si sovrappongono")
            oscurati.append((ini, qua))
        if p + lung > len(d):
            raise Malformata(f"blocco {nb}: il carico e' troncato")
        if verso not in (CLIENT, SERVER):
            raise Malformata(f"blocco {nb}: verso {verso}, previsti 1 o 2")
        for o, q in oscurati:
            if any(b != RIEMPIMENTO for b in d[p + o:p + o + q]):
                raise Malformata(
                    f"blocco {nb}: un intervallo oscurato non e' fatto di 0x2A")
        fuori.append({"n": nb, "verso": verso, "canale": canale,
                      "stream": stream, "base": p, "lung": lung,
                      "carico": d[p:p + lung], "oscurati": oscurati})
        p += lung
    if p != len(d):
        raise Malformata(
            f"restano {len(d) - p} byte dopo i {quanti} blocchi dichiarati: o "
            f"`quanti_blocchi` e' sotto-dichiarato — e allora c'e' del filo che "
            f"nessuno ha giudicato — o c'e' una coda che non e' del formato")
    return fuori


# ---------------------------------------------------------------------------
def valida(percorso, guasti=(), tela=(1920, 1080), codec=1, stampa=True):
    with open(percorso, "rb") as f:
        d = f.read()
    blocchi = leggi_blocchi(d)

    if stampa:
        print(f"== l'arbitro del canale VIDEO — {percorso}")
        print(f"   blocchi: {len(blocchi)}   byte: {len(d)}")
        print(f"   ⛔ contesto dichiarato: tela {tela[0]}x{tela[1]}, codec "
              f"negoziato {codec}")
        print(f"      ⚠ e va DICHIARATO da fuori: meta' delle regole di §6.2 "
              f"non si")
        print(f"        possono applicare senza — «DEVE essere quello "
              f"negoziato in §4.3»,")
        print(f"        «e' sempre quella della tela».  Un arbitro che li "
              f"indovinasse")
        print(f"        starebbe giudicando i propri predefiniti")

    # ⛔ I DENOMINATORI, E SONO QUATTRO PERCHE' LE COSE CHE SI POSSONO NON AVER
    #    GUARDATO SONO QUATTRO.
    conta = {"blocchi": len(blocchi), "video": 0, "flussi": 0,
             "giudicati": 0, "completezza_ignota": 0}
    ctx = f24.Contesto(tela=tela, codec_negoziato=codec, sessione_aperta=True)

    # I blocchi video si raggruppano per `stream`: uno stream, un fotogramma
    # (§6.2).  ⛔ E l'ordine dentro un flusso e' quello del file, non quello
    # dello `stream`: gli stream sono indipendenti e i blocchi si interlacciano.
    flussi, ordine = {}, []
    for b in blocchi:
        if b["canale"] not in CANALI:
            raise NonConforme("RCP.md §2.5",
                              f"blocco {b['n']}: il byte alto vale "
                              f"{b['canale']:#04x}, fuori dai cinque canali",
                              b["base"], 0)
        if b["canale"] != VIDEO:
            continue
        conta["video"] += 1
        # ⛔ G4 — IL GUASTO CHE E' LO STATO DI OGGI DI `01-b4-validatore.py`.
        #
        #    La sua riga 521 dichiara di non giudicare i canali diversi da
        #    `0x00` e prosegue.  Innestato qui, il canale video torna a non
        #    essere guardato da nessuno, e il file esce **3** — «niente da
        #    giudicare» — che e' esattamente il verdetto onesto di uno
        #    strumento cieco.  ⭐ Se uscisse **0** questo guasto sarebbe
        #    invisibile, ed e' la ragione per cui il codice 3 esiste.
        if "G4" in guasti:
            continue
        # ⛔ IL VERSO — §2.5: «un canale usato nel verso sbagliato».  Il video
        #    va dal server al client, e basta.
        if b["verso"] != SERVER:
            raise NonConforme("RCP.md §2.5",
                              f"blocco {b['n']}: un fotogramma DAL CLIENT — il "
                              f"video va dal server al client",
                              b["base"], 0)
        if b["oscurati"]:
            # ⛔ §11.1: «il validatore NON DEVE leggere dentro un intervallo
            #    oscurato».  Su un fotogramma non ci sono segreti da nascondere
            #    — §4.4 parla della parola d'ordine — quindi un oscuramento qui
            #    e' un difetto del REGISTRATORE, e si dice come tale.
            raise Malformata(
                f"blocco {b['n']}: un intervallo oscurato su un blocco VIDEO. "
                f"§11.1 esiste per la parola d'ordine (§4.4); un fotogramma non "
                f"ha niente da oscurare, e il validatore non puo' giudicare "
                f"quel che non gli si lascia leggere")
        if b["stream"] not in flussi:
            flussi[b["stream"]] = []
            ordine.append(b["stream"])
        flussi[b["stream"]].append(b)

    if not flussi:
        raise NienteDaGiudicare(
            f"{conta['blocchi']} blocchi, {conta['video']} sul canale video, "
            f"ZERO flussi da giudicare")

    conta["flussi"] = len(flussi)
    for sid in ordine:
        pezzi = flussi[sid]
        g = f24.Giudice(ctx, dove="uni", guasti=guasti)
        for b in pezzi:
            g.arrivano(b["carico"])
            if g.verdetto is not None:
                break
        # ⛔⭐ QUI STA IL BUCO DEL FORMATO — vedi l'intestazione, proposta P7.
        #
        #    §11.1 non porta come e' finito lo stream.  Si giudica quel che si
        #    puo' — l'intestazione, i campi, l'ordine — e la **completezza** si
        #    dichiara non giudicata invece di darla per buona.
        v = g.verdetto
        if v is None:
            v = g.finisce("fin")
            if v.esito == f24.ACCETTATO:
                conta["completezza_ignota"] += 1
                if stampa:
                    print(f"   {GIALLO}?? flusso {sid}: intestazione conforme, "
                          f"{g.byte_dati} byte di dati — ⛔ ma se lo stream sia "
                          f"finito con FIN o con RESET il formato NON LO "
                          f"DICE{GRIGIO}")
                conta["giudicati"] += 1
                continue
            if v.esito == f24.ERRORE_PROTOCOLLO and not g.letta:
                # Il carico e' finito prima dei 28 byte, ma non sappiamo se lo
                # stream fosse finito: e' l'altra faccia dello stesso buco.
                conta["completezza_ignota"] += 1
                if stampa:
                    print(f"   {GIALLO}?? flusso {sid}: solo {g.grezzo and len(g.grezzo)} "
                          f"byte, meno dei 28 dell'intestazione — ⛔ e il "
                          f"formato non dice se lo stream fosse finito: "
                          f"troncato dal server, o abbandonato di "
                          f"proposito?{GRIGIO}")
                conta["giudicati"] += 1
                continue
        conta["giudicati"] += 1
        if v.esito in (f24.ERRORE_PROTOCOLLO,):
            b0 = pezzi[0]
            rel = v.scostamento if v.scostamento is not None else 0
            raise NonConforme(v.regola, f"flusso {sid}: {v.dice}",
                              b0["base"] + rel, rel)
        if stampa:
            col = {f24.ACCETTATO: VERDE, f24.SCARTATO: GIALLO,
                   f24.AMBIGUO: GIALLO}[v.esito]
            extra = (f"   ⇒ proposta {v.propone}" if v.esito == f24.AMBIGUO
                     else "")
            print(f"   {col}{v.esito:18s}{GRIGIO} flusso {sid}: {v.dice}{extra}")

    if stampa:
        print(f"\n   guardati: {conta['blocchi']} blocchi, di cui "
              f"{conta['video']} sul canale video · {conta['flussi']} flussi · "
              f"{conta['giudicati']} giudicati")
        if conta["completezza_ignota"]:
            print(f"   {GIALLO}⛔ e di {conta['completezza_ignota']} su "
                  f"{conta['flussi']} NON si e' potuta giudicare la "
                  f"completezza{GRIGIO}")
            print(f"      il formato di §11.1 non porta il FIN.  Proposta P7 — "
                  f"e questo")
            print(f"      NON e' un difetto del filo: e' un difetto del "
                  f"formato")
        print(f"   ⭐ conforme: nessuna violazione in {conta['giudicati']} "
              f"flussi")
    return 0, conta


# ===========================================================================
# ⛔ LE REGISTRAZIONI DI PROVA — e servono a certificare l'arbitro, non il filo.
#
#    §11: *«prima di concludere che il validatore non trova errori, gli si da'
#    una registrazione CON UN ERRORE DENTRO e si verifica che lo veda.  Uno
#    strumento che non ha mai trovato niente non e' uno strumento pulito: e'
#    uno strumento non certificato»*.
def scrivi_reg(percorso, blocchi):
    out = bytearray(MAGIA + struct.pack("!II", len(blocchi), 0))
    for verso, canale, stream, carico in blocchi:
        out += struct.pack("!BBQIH", verso, canale, stream, len(carico), 0)
        out += carico
    with open(percorso, "wb") as f:
        f.write(bytes(out))
    return percorso


PROVE = {
    "buona": ("un fotogramma chiave conforme, in tre blocchi sullo stesso "
              "stream: e' il caso che la fase 2 esiste per produrre", 0,
              lambda: [(SERVER, VIDEO, 8, f24.intestazione()),
                       (SERVER, VIDEO, 8, b"\x00" * 2048),
                       (SERVER, VIDEO, 8, b"\x00" * 2048)]),
    "tipo-storto": ("`tipo = 0x0300` nell'intestazione: §6.2 «Altri valori: "
                    "ERRORE_PROTOCOLLO»", 1,
                    lambda: [(SERVER, VIDEO, 8,
                              f24.intestazione(tipo=0x0300) + b"\x00" * 64)]),
    "verso-sbagliato": ("un fotogramma DAL CLIENT: §2.5, il canale nel verso "
                        "sbagliato", 1,
                        lambda: [(CLIENT, VIDEO, 9,
                                  f24.intestazione() + b"\x00" * 64)]),
    "solo-controllo": ("⛔ una registrazione di sola stretta di mano: ZERO "
                       "blocchi video.  «Non ho niente da giudicare» e «ho "
                       "giudicato tutto e va bene» sono due fatti diversi", 3,
                       lambda: [(CLIENT, 0x00, 4,
                                 struct.pack("!HI", 0x0001, 0))]),
    "coda-di-troppo": ("⛔ `quanti_blocchi` sotto-dichiarato: del filo che "
                       "nessuno giudica.  E' un difetto del FILE, non del filo",
                       2, None),
    "canale-ignoto": ("un byte alto che non e' nessuno dei cinque di §2.5", 1,
                      lambda: [(SERVER, 0x09, 8, b"\x00" * 28)]),
}


def fabbrica(cartella):
    fatti = []
    for nome, (spiega, atteso, f) in PROVE.items():
        p = os.path.join(cartella, f"02-filo-prova-{nome}.rcpreg")
        if f is None:
            # la coda di spazzatura si costruisce a mano
            scrivi_reg(p, [(SERVER, VIDEO, 8,
                            f24.intestazione() + b"\x00" * 64)])
            with open(p, "ab") as fh:
                fh.write(b"spazzatura")
        else:
            scrivi_reg(p, f())
        fatti.append((nome, p, atteso, spiega))
        print(f"   {os.path.basename(p):44s} atteso uscita {atteso}")
        print(f"   {'':44s} {spiega}")
    return fatti


def gira_prove(cartella, guasti=(), stampa=True):
    """⛔ Ogni prova dichiara il proprio codice d'uscita PRIMA di essere girata."""
    fatti = fabbrica(cartella) if stampa else _fabbrica_muta(cartella)
    guastati, righe = 0, []
    if stampa:
        print()
    for nome, p, atteso, spiega in fatti:
        try:
            visto, _ = valida(p, guasti=guasti, stampa=False)
        except NonConforme:
            visto = 1
        except Malformata:
            visto = 2
        except NienteDaGiudicare:
            visto = 3
        except OSError:
            visto = 2
        ok = visto == atteso
        guastati += int(not ok)
        righe.append({"prova": nome, "atteso": atteso, "visto": visto,
                      "esito": bool(ok)})
        if stampa:
            print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
                  f"{nome:22s} uscita {visto} (atteso {atteso})")
            if not ok:
                print(f"        {spiega}")
    return guastati, righe


def _fabbrica_muta(cartella):
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        return fabbrica(cartella)


PROPOSTA_P7 = (
    "§11.1, il blocco della registrazione — come e' finito lo stream",
    "Il blocco porta, dopo `canale`, un `u8 fine`: `0` = lo stream continua, "
    "`1` = chiuso con **FIN**, `2` = azzerato con **RESET_STREAM**.  La magia "
    "diventa `\"RCPREG\" 0x00 0x02`.  Senza questo campo un fotogramma "
    "abbandonato (§5.1, legale) e uno troncato per errore (§3, la connessione "
    "cade) hanno lo stesso aspetto nella registrazione, cioe' l'arbitro non "
    "puo' applicare la riga che §6.2 ha aggiunto apposta il 9 agosto 2026.")


def scrivi_esito(percorso, rec):
    if not percorso:
        print("    ⚠ nessun --uscita: questo giro NON lascia registro")
        return False
    fuori = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "banco": "F2.4-validatore",
             "scena": "registrazioni fabbricate da questo stesso file, nel "
                      "formato di RCP.md §11.1: nessuna rete e nessun server",
             "macchina": os.uname().nodename}
    fuori.update(rec)
    try:
        with open(percorso, "a") as f:
            f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        print(f"    {ROSSO}⛔ il registro «{percorso}» non si scrive: {e}{GRIGIO}")
        return False
    return True


def certifica(a):
    """⛔ sano -> G4 -> risanato.  E G4 e' LO STATO DI OGGI DI `01-b4`.

    Il guasto da innestare non e' inventato: e' *«il validatore salta il canale
    video»*, cioe' la riga 521 di `01-b4-validatore.py`.  ⭐ Certificare contro
    quel guasto e' l'unico modo di dimostrare che questo file **aggiunge**
    qualcosa invece di ripetere B4 con altre parole.
    """
    print("\n== ⛔ LA CERTIFICAZIONE — sano -> G4 -> risanato")
    print("   G4: «l'arbitro salta il canale video», che e' quel che")
    print("       `01-b4-validatore.py` fa oggi (la sua riga 521).")
    print("   atteso sano:   0 prove sbagliate")
    print("   atteso guasto: le prove che devono uscire 1 escono 3 —")
    print("                  «niente da giudicare» — perche' il canale video")
    print("                  non viene guardato.  ⛔ E NON escono 0: un")
    print("                  arbitro che salta tutto non assolve, dichiara")
    print("                  di non aver guardato.  Se uscisse 0 il guasto")
    print("                  sarebbe passato per un verde\n")
    sano, righe_sane = gira_prove(a.cartella, guasti=())
    print()
    rotto, righe_rotte = gira_prove(a.cartella, guasti=("G4",))
    print()
    # ⛔ LA MARCA, CON LE SUE DUE META' (R12-A.3): il giro guasto la deve dire
    #    e il giro sano NON la deve gia' dire.
    marca_rotto = sum(1 for r in righe_rotte
                      if r["atteso"] == 1 and r["visto"] == 3)
    marca_sano = sum(1 for r in righe_sane
                     if r["atteso"] == 1 and r["visto"] == 3)
    risanato, _ = gira_prove(a.cartella, guasti=(), stampa=False)
    ok = (sano == 0 and rotto > 0 and marca_rotto > 0 and marca_sano == 0
          and risanato == 0)
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  G4  "
          f"sano {sano} -> guasto {rotto} -> risanato {risanato}   "
          f"marca «uscita 3 dove ne serviva 1»: {marca_rotto} volte col "
          f"guasto, {marca_sano} volte da sano")
    scrivi_esito(a.uscita, {"tipo": "certificazione", "guasto": "G4",
                            "sano": sano, "guasto_conta": rotto,
                            "risanato": risanato, "marca_col_guasto": marca_rotto,
                            "marca_da_sano": marca_sano, "esito": bool(ok),
                            "prove_sane": righe_sane, "prove_rotte": righe_rotte})
    print()
    if ok:
        print(f"    {VERDE}⭐ 02-filo-validatore.py e' CERTIFICATO{GRIGIO}")
        return 0
    print(f"    {ROSSO}⛔ NON certificato{GRIGIO}")
    return 1


def principale(a):
    if a.elenco:
        print("== le registrazioni di prova, e il codice d'uscita atteso di "
              "ciascuna")
        print("   ⛔ Ogni riga e' una PREVISIONE, scritta prima del giro\n")
        for nome, (spiega, atteso, _) in PROVE.items():
            print(f"  {nome:22s} uscita {atteso}")
            print(f"  {'':22s}   {spiega}")
        print(f"\n== ⛔ LA PROPOSTA A `RCP.md` che questo strumento ha trovato")
        print(f"  P7  {PROPOSTA_P7[0]}")
        print(f"      «{PROPOSTA_P7[1]}»")
        return 0
    if a.fabbrica:
        print("== le registrazioni di prova, nel formato di RCP.md §11.1\n")
        fabbrica(a.cartella)
        return 0
    if a.certifica:
        return certifica(a)
    if not a.registrazione:
        # ⛔ Senza un file non si gira in silenzio: si dice che non c'e' niente
        #    da giudicare, con il codice che quel fatto ha.
        print("== ⛔ nessuna registrazione da giudicare.")
        print("   Le prove si fabbricano con --fabbrica, il giro con "
              "--certifica.")
        return 3

    # ⛔ IL CONTROLLO POSITIVO, PRIMA del verdetto e non dopo: si verifica che
    #    questo strumento sappia trovare un errore che c'e' di sicuro, e solo
    #    dopo lo si punta sull'incognita (`LEZIONI.md` §1.2).
    print("== ⛔ il controllo positivo, PRIMA di puntare l'arbitro "
          "sull'incognita")
    guastati, _ = gira_prove(a.cartella)
    if guastati:
        print(f"\n    {ROSSO}⛔ l'arbitro sbaglia su {guastati} registrazioni "
              f"note: non e' il caso di credergli su una nuova{GRIGIO}")
        return 2
    print(f"\n    {VERDE}⭐ l'arbitro e' d'accordo su tutte le prove note"
          f"{GRIGIO}\n")

    try:
        codice, conta = valida(a.registrazione, tela=(a.tela_larghezza,
                                                      a.tela_altezza),
                               codec=a.codec)
    except NonConforme as e:
        print(f"\n   {ROSSO}⛔ NON CONFORME — {e.regola}{GRIGIO}")
        print(f"      {e.dice}")
        print(f"      byte {e.ass} nel file · scostamento {e.rel} nel carico "
              f"del blocco")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 1, "regola": e.regola, "dice": e.dice,
                                "byte": e.ass})
        return 1
    except Malformata as e:
        print(f"\n   ⚠ REGISTRAZIONE MALFORMATA: {e}")
        print("      ⛔ Non e' un giudizio sul filo: e' un difetto del file.")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 2, "dice": str(e)})
        return 2
    except NienteDaGiudicare as e:
        print(f"\n   ⛔ NIENTE DA GIUDICARE: {e}")
        print("      Non e' «conforme»: e' l'assenza dell'oggetto del "
              "giudizio.")
        print("      Si guarda il registratore — chi doveva scrivere quei "
              "byte.")
        scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                                "uscita": 3, "dice": str(e)})
        return 3
    except OSError as e:
        # ⛔ E8: «vuoto» e «proibito» hanno lo stesso aspetto.
        print(f"\n   ⚠ LA REGISTRAZIONE NON SI LEGGE: {e}")
        print("      ⛔ Non e' un giudizio sul filo, e non e' «il file e' "
              "rotto»:")
        print("         e' che non si e' potuto aprire.  Si guardano permessi,")
        print("         percorso e volume — non RCP.md.")
        return 2
    scrivi_esito(a.uscita, {"tipo": "giudizio", "file": a.registrazione,
                            "uscita": 0, **conta})
    return codice


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — l'arbitro meccanico del canale video")
    p.add_argument("registrazione", nargs="?")
    p.add_argument("--fabbrica", action="store_true",
                   help="costruisce le registrazioni di prova")
    p.add_argument("--certifica", action="store_true",
                   help="sano -> G4 -> risanato")
    p.add_argument("--elenco", action="store_true",
                   help="le previsioni e la proposta P7, senza misurare")
    p.add_argument("--cartella", default=os.path.join(QUI, "02-filo-prove"),
                   help="dove stanno le registrazioni di prova")
    p.add_argument("--tela-larghezza", type=int, default=1920)
    p.add_argument("--tela-altezza", type=int, default=1080)
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--uscita", default="", help="il registro del giro, in JSONL")
    a = p.parse_args()
    os.makedirs(a.cartella, exist_ok=True)
    sys.exit(principale(a))
