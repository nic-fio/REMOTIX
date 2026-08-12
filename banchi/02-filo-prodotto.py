#!/usr/bin/env python3
"""02-filo-prodotto.py — ⛔ F2.4: il PRODOTTO giudicato dall'arbitro del filo.

    python3 02-filo-prodotto.py --elenco      le previsioni, senza misurare
    python3 02-filo-prodotto.py               il giro
    python3 02-filo-prodotto.py --certifica   sano -> guasto -> risanato

===========================================================================
⛔ CHE COSA MISURA, E PERCHE' NON E' UN DOPPIONE DEL GIUDICE

`02-filo-fotogramma.py` giudica **fotogrammi fabbricati dal banco**: dice se
l'arbitro sa distinguere un fotogramma conforme da uno storto.  ⛔ Non dice
niente sul prodotto, perche' il prodotto non li ha scritti lui.

Questo file chiude l'altra meta': prende **i byte che `src/rcp.c` mette sul
filo** — raccolti da `02-filo-prodotto.c`, che monta il canale video su un
ospite finto — e li da' **allo stesso arbitro**.  ⭐ Il fotogramma viene
scritto da un programma in C che ha letto `RCP.md`, e giudicato da un
programma in Python che ha letto `RCP.md`, e i due non si parlano.

⛔ **E il divieto vale nel verso che conta**: il prodotto non importa il
   giudice e non lo puo' importare — e' in un altro linguaggio, in un altro
   processo, e i byte passano da un JSON.  Se i due lettori diventassero uno,
   la fase 2 avrebbe comprato un arbitro per poi buttarlo.

⚠ **E quel che questo giro NON dice**: che un fotogramma arrivi *sulla rete*.
  Qui non c'e' ne' QUIC ne' WebTransport — l'ospite e' finto.  Quella misura la
  da' `02-filo-cliente.py` sulla 7514, e il suo denominatore e' un altro.

===========================================================================
⛔ I CODICI D'USCITA

  0  ogni scena si comporta come previsto PRIMA del giro
  1  ⛔ una scena no — e si dice quale, che cosa si aspettava e che cosa ha visto
  2  il banco non ha potuto girare (manca `cc`, la compilazione e' fallita)
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
SORGENTE = os.path.join(QUI, "02-filo-prodotto.c")


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ SI IMPORTA, NON SI RICOPIA.  Una copia del giudice dentro questo file
#    sarebbe un terzo lettore scritto dalla stessa mano nella stessa ora, cioe'
#    lo stesso presupposto ripetuto (`RCP.md` §0).
G = _porta("filo_fotogramma", "02-filo-fotogramma.py")

ACC, SCA, ERR = G.ACCETTATO, G.SCARTATO, G.ERRORE_PROTOCOLLO

# Gli esiti di `rcp.h`, e i nomi sono quelli del prodotto.
E_SPEDITO, E_NIENTE_CANALE, E_PRIMA_DI_SESSIONE = 0, 1, 2
E_SERVE_UNA_CHIAVE, E_TROPPO_GRANDE = 3, 4
E_STREAM_NON_APERTO, E_ROTTO_A_META, E_GIA_APERTO = 5, 6, 7
NOME_ESITO = {0: "SPEDITO", 1: "NIENTE_CANALE", 2: "PRIMA_DI_SESSIONE",
              3: "SERVE_UNA_CHIAVE", 4: "TROPPO_GRANDE",
              5: "STREAM_NON_APERTO", 6: "ROTTO_A_META", 7: "GIA_APERTO",
              99: "RIFIUTATO"}

TETTO = 16 * 1024 * 1024


# ===========================================================================
# ⛔ LE PREVISIONI, SCRITTE PRIMA DEL GIRO — `PIANO.md` §0.3 regola 4
#
# Ogni riga dice tre cose: che cosa il prodotto deve **restituire a chi
# chiama**, che cosa deve aver messo **sul filo**, e che verdetto ne deve dare
# **l'arbitro**.  ⚠ Le prime due senza la terza direbbero solo che il prodotto
# fa quel che il prodotto crede.
#
# `verdetto = None` vuol dire ⛔ **nessuno stream**: e non e' «il fotogramma e'
# passato», e' «non e' partito un byte», che per meta' di queste regole e'
# precisamente il comportamento giusto.
# ===========================================================================
def ctx(**kw):
    """Il contesto del client per la scena, dichiarato caso per caso."""
    return kw


SCENE = [
    dict(
        nome="prima-di-sessione", regola="P1 · RCP.md §2.5",
        esito=E_PRIMA_DI_SESSIONE, stream=0, verdetto=None,
        spiega="⛔ **P1 / invariante I3 sul filo** — `SESSIONE` non e' stata "
               "spedita.  §2.5: «uno per fotogramma, e **nessuno prima di aver "
               "spedito `SESSIONE`**».  ⭐ E la previsione qui non e' un "
               "verdetto dell'arbitro: e' **zero stream**.  Un banco che si "
               "accontentasse di «l'arbitro lo boccia» proverebbe il CLIENT, "
               "mentre la meta' che manca a `RCP.md` era quella di chi MANDA",
    ),
    dict(
        nome="chiave-dopo-sessione", regola="P2 · P5 · P6 · §6.2",
        esito=E_SPEDITO, stream=1, verdetto=ACC,
        contesto=ctx(),
        testa=dict(tipo=0x0301, codec=1, lar=1920, alt=1080, num=1,
                   ist=123456789, inp=7),
        spiega="⭐ **il fotogramma che la fase 2 esiste per consegnare** — "
               "chiave, HEVC, la tela in vigore, `numero = 1`.  ⛔ Quattro "
               "regole in un caso solo, e i campi si controllano **uno per "
               "uno**: un verdetto `ACCETTATO` da solo sarebbe verde anche se "
               "l'istante fosse in little-endian",
    ),
    dict(
        nome="delta-in-apertura", regola="P6 · RCP.md §5.2",
        esito=E_SERVE_UNA_CHIAVE, stream=0, verdetto=None, serve_chiave=True,
        spiega="⭐⛔ **P6 dal lato di chi MANDA** — il primo fotogramma dopo "
               "`SESSIONE` DEVE essere una chiave, e qui chi codifica ne "
               "chiede un delta.  ⛔ Il prodotto **rifiuta e non spedisce**: "
               "promuoverlo a chiave sarebbe mentire sul campo `tipo`, e "
               "spedirlo sarebbe il caso che il client non ha modo di "
               "riconoscere (nessun buco nei `numero`, nessun errore dal "
               "decodificatore)",
    ),
    dict(
        nome="delta-dopo-la-chiave", regola="P6, seconda faccia · §6.2",
        esito=E_SPEDITO, stream=1, verdetto=ACC,
        contesto=ctx(ultimo_consegnato=1, chiave_consegnata=True),
        testa=dict(tipo=0x0302, num=2),
        spiega="⭐ la seconda faccia: un delta che **non** e' il primo passa. "
               "⛔ Senza questo caso, un prodotto che avesse capito §5.2 come "
               "«i delta non si spediscono» sarebbe verde su tutto il banco e "
               "fermerebbe il video dalla fase 3 in poi, dove i delta sono il "
               "99 % dei fotogrammi",
    ),
    dict(
        nome="codec-negoziato-av1", regola="RCP.md §6.2, §4.3",
        esito=E_SPEDITO, stream=1, verdetto=ACC,
        contesto=ctx(tela=(1280, 720), codec_negoziato=2),
        testa=dict(codec=2, lar=1280, alt=720),
        spiega="⛔ «`codec` DEVE essere quello negoziato in §4.3»: qui il "
               "client ha offerto **av1** e la tela e' 1280x720.  ⭐ E' il caso "
               "che tiene onesto `chiave-dopo-sessione`: senza, un prodotto "
               "che scrivesse `codec = 1` e `1920x1080` **costanti** sarebbe "
               "verde su tutto il resto del banco",
    ),
    dict(
        nome="oltre-16-mib", regola="RCP.md §6.2",
        esito=E_TROPPO_GRANDE, stream=0, verdetto=None,
        spiega="⛔ **il tetto vincola PRIMA chi spedisce** — un fotogramma di "
               "16 MiB + 1: «DEVE ricodificarlo a qualita' inferiore e "
               "scriverlo nel registro — mai spedirlo».  ⭐ La previsione e' "
               "**zero stream**, non «l'arbitro lo boccia»: se lo bocciasse "
               "l'arbitro vorrebbe dire che i byte erano partiti, cioe' che il "
               "tetto era diventato una punizione per chi subisce — che e' "
               "esattamente il rilievo R1.23 del 9 agosto 2026",
    ),
    dict(
        nome="16-mib-esatti", regola="RCP.md §6.2",
        esito=E_SPEDITO, stream=1, verdetto=ACC, lunghezza=TETTO,
        contesto=ctx(),
        spiega="⭐ e **16 MiB esatti passano**: il tetto e' un massimo, non un "
               "limite stretto.  ⚠ Senza questo caso «> 16 MiB» e «>= 16 MiB» "
               "danno lo stesso verde su tutto il resto",
    ),
    dict(
        nome="giro-del-contatore", regola="P2, l'altra meta' · §6.2",
        esito=E_SPEDITO, stream=1, verdetto=ACC,
        contesto=ctx(ultimo_consegnato=0xFFFFFFFF, chiave_consegnata=True),
        testa=dict(num=1),
        spiega="⭐⛔ **lo `0` che RITORNA** — il contatore e' a `0xFFFFFFFF` e "
               "il fotogramma dopo deve portare **1**, non 0.  ⛔ E' la falla "
               "che P2 ha avuto aperta per due ore: riservava lo zero e non "
               "diceva di saltarlo al giro.  ⚠ Il sintomo sarebbe arrivato "
               "**una volta sola nella vita di una sessione**, dopo due anni e "
               "due mesi, e nessuno l'avrebbe collegato a `RICHIEDI_CHIAVE`",
    ),
    dict(
        nome="delta-alla-misura-nuova", regola="P9 · RCP.md §5.2",
        esito=E_SERVE_UNA_CHIAVE, stream=0, verdetto=None, serve_chiave=True,
        spiega="⭐⛔ **P9 dal lato di chi MANDA** — dopo un `TELA(ADATTATA, "
               "1280, 720)` chi codifica chiede un delta, e il prodotto "
               "rifiuta.  ⛔ `[M]` 12 agosto: con soli delta alla misura nuova "
               "Chrome su HEVC emette cinque fotogrammi **alla misura "
               "vecchia**, li dipinge e non solleva nessun errore — il sintomo "
               "sarebbe «il desktop si strappa quando ridimensiono»",
    ),
    dict(
        nome="chiave-alla-misura-nuova", regola="P5 · P9 · §6.2",
        esito=E_SPEDITO, stream=1, verdetto=ACC,
        contesto=ctx(dopo_tela=(1280, 720), ultimo_consegnato=1,
                     chiave_consegnata=True),
        testa=dict(tipo=0x0301, lar=1280, alt=720, num=2),
        spiega="⭐ **P5: la tela IN VIGORE, non quella di `SESSIONE`** — la "
               "chiave dopo il `TELA` porta 1280x720.  ⛔ Per due ore, il 12 "
               "agosto, §6.2 diceva «la tela concessa in `SESSIONE`»: con "
               "quella riga questo fotogramma sarebbe stato "
               "`ERRORE_PROTOCOLLO`, e il client avrebbe ucciso la sessione "
               "perche' l'utente ha trascinato una finestra",
    ),
    dict(
        nome="tela-che-non-cambia", regola="P9, terza faccia · §7.1",
        esito=E_SPEDITO, stream=1, verdetto=ACC,
        contesto=ctx(dopo_tela=(1920, 1080), ultimo_consegnato=1,
                     chiave_consegnata=True),
        testa=dict(tipo=0x0302, lar=1920, alt=1080, num=2),
        spiega="⭐⛔ un `TELA(ADATTATA)` che chiede **la misura che c'e' gia'** "
               "non apre nessun debito, e il delta passa.  ⛔ §7.1 fa "
               "rispondere `TELA` a **ogni** `ADATTA_TELA`: un prodotto che "
               "aprisse il debito a ogni `TELA` invece che a ogni **cambio** "
               "sarebbe verde su tutto il banco e fermerebbe il video sulla "
               "prima sessione in cui l'utente trascina una finestra e la "
               "rimette dov'era — un rosso su una sessione **sana**",
    ),
    dict(
        nome="abbandono-di-un-delta", regola="RCP.md §5.1, §6.2",
        esito=0, stream=1, verdetto=SCA, serve_chiave=True,
        contesto=ctx(ultimo_consegnato=1, chiave_consegnata=True),
        fine="reset",
        spiega="⭐ §5.1: il server abbandona un delta perche' ne e' partito uno "
               "piu' recente ⇒ ⛔ **`RESET_STREAM`, mai FIN**, e l'arbitro dice "
               "`SCARTATO` — si butta, non si consegna, la sessione REGGE.  ⛔ "
               "E §5.2 vuole una chiave subito dopo, «senza aspettare che il "
               "client la chieda»: si controlla anche quella",
    ),
    dict(
        nome="abbandono-di-una-chiave", regola="RCP.md §5.2",
        esito=99, stream=1, verdetto=None, fine="aperto", serve_chiave=True,
        spiega="⛔ **una CHIAVE non si abbandona** — «abbandonare la cura non "
               "e' una cura».  Il prodotto rifiuta, lo stream resta aperto e "
               "il fotogramma parte per intero.  ⚠ La previsione e' il "
               "**rifiuto**: senza questo caso, un prodotto che azzerasse "
               "tutto sarebbe verde sul caso qui sopra",
    ),
    dict(
        nome="intestazione-che-non-esce", regola="P4 · RCP.md §6.2",
        esito=E_ROTTO_A_META, stream=1, verdetto=SCA, fine="reset",
        lunghezza=0, contesto=ctx(),
        spiega="⭐⛔ **P4 dal lato di chi MANDA** — l'ospite rifiuta i 28 byte, "
               "e il prodotto **AZZERA**.  ⛔ Un FIN qui sarebbe stato «una "
               "lunghezza che non torna» (§6.2) e avrebbe fatto cadere una "
               "sessione per un difetto **nostro**; un reset a zero byte e' un "
               "fotogramma abbandonato, cioe' il caso normale di §5.1 — la "
               "sessione regge.  ⚠ Le due chiusure NON sono intercambiabili",
    ),
    dict(
        nome="richiedi-chiave-accolta", regola="RCP.md §5.2, §7.1",
        esito=0, stream=0, verdetto=None, serve_chiave=True,
        spiega="⛔ §5.2: «il client DEVE mandare `RICHIEDI_CHIAVE` quando si "
               "accorge di un buco», e il server la serve.  ⚠ Fino a oggi "
               "questo tipo faceva **perdere la sessione** a un client "
               "conforme: cadeva nel `default` con la riga «la fase 1 non lo "
               "serve ancora»",
    ),
    dict(
        nome="richiedi-chiave-nei-200-ms", regola="§5.2 · §3 eccezione 5",
        esito=0, stream=0, verdetto=None, serve_chiave=False, tolleranza=True,
        spiega="⭐ la richiesta arriva 100 ms dopo la chiave: §3 eccezione 5 "
               "permette di ignorarla, ⛔ e §3 pretende che la tolleranza sia "
               "**scritta nel registro** — «una tolleranza silenziosa e' "
               "indistinguibile da un difetto».  Si controllano tutt'e due: "
               "che sia ignorata **e** che sia dichiarata",
    ),
    dict(
        nome="senza-i-ganci", regola="RCP.md §2.5",
        esito=E_NIENTE_CANALE, stream=0, verdetto=None,
        spiega="⛔ un ospite senza i quattro ganci non ha un canale video, e il "
               "prodotto lo **dice** invece di tacere: «non ho un canale "
               "video» e «il fotogramma non e' partito» sono due fatti diversi "
               "(`LEZIONI.md` §1.9 regola 1)",
    ),
]


# ===========================================================================
# ⛔ I GUASTI — e si innestano SUI BYTE, che e' quel che questo banco legge
#
# La domanda di `REVIEWER.md` §1 non e' «funziona?», e' **«saprebbe accorgersi
# che non funziona?»**.  ⚠ Guastare il prodotto per rispondere sarebbe
# guastare l'imputato; qui si guasta **la traccia**, cioe' si finge un
# prodotto che ha messo sul filo dei byte diversi — ed e' esattamente il modo
# in cui questo banco lo scoprirebbe.
#
# ⛔ E LA MARCA HA DUE META' (rilievo R12-A.3): il giro guasto la deve DIRE, e
#    il giro sano NON la deve gia' dire.  La marca e' `scena: atteso -> visto`,
#    che a giro sano non puo' esistere perche' i due coincidono sempre.
# ===========================================================================
GUASTI = {
    "GP1": dict(
        scena="chiave-dopo-sessione", campo="tipo", valore=0x0302,
        dice="il primo fotogramma e' un DELTA (P6 violata)",
        atteso="⛔ `chiave-dopo-sessione` diventa ERRORE_PROTOCOLLO"),
    "GP2": dict(
        scena="chiave-dopo-sessione", campo="num", valore=0,
        dice="`numero = 0`, il valore che P2 riserva",
        atteso="⛔ `chiave-dopo-sessione` diventa ERRORE_PROTOCOLLO"),
    "GP3": dict(
        scena="chiave-alla-misura-nuova", campo="lar", valore=1920,
        dice="la misura resta quella di `SESSIONE` dopo un `TELA` — cioe' "
             "§6.2 com'era per due ore il 12 agosto",
        atteso="⛔ `chiave-alla-misura-nuova` diventa ERRORE_PROTOCOLLO"),
    "GP4": dict(
        scena="abbandono-di-un-delta", fine="fin",
        dice="uno stream AZZERATO chiuso con FIN — la forma E8, e il rilievo "
             "R1.7 del 9 agosto 2026",
        atteso="⛔ `abbandono-di-un-delta` passa da SCARTATO ad ACCETTATO: i "
               "byte di un fotogramma abbandonato finiscono al decodificatore"),
    "GP5": dict(
        scena="16-mib-esatti", lunghezza=TETTO + 1,
        dice="un byte oltre il tetto",
        atteso="⛔ `16-mib-esatti` diventa ERRORE_PROTOCOLLO"),
    "GP6": dict(
        scena="chiave-dopo-sessione", campo="codec", valore=2,
        dice="`codec = 2` (AV1) su una sessione che ha negoziato HEVC",
        atteso="⛔ `chiave-dopo-sessione` diventa ERRORE_PROTOCOLLO"),
}


# ===========================================================================
def compila(dove):
    cc = os.environ.get("CC", "cc")
    r = subprocess.run(
        [cc, "-std=gnu11", "-D_GNU_SOURCE", "-O1", "-Wall", "-Wextra",
         "-Wno-unused-parameter", "-o", dove, SORGENTE],
        cwd=QUI, capture_output=True, text=True)
    return r


def raccogli(binario):
    """Fa girare l'ospite finto e riporta le tracce, una per scena."""
    r = subprocess.run([binario], cwd=QUI, capture_output=True, text=True)
    if r.returncode != 0:
        return None, f"l'ospite e' uscito {r.returncode}: {r.stderr[:400]}"
    fuori = {}
    for riga in r.stdout.splitlines():
        riga = riga.strip()
        if not riga:
            continue
        d = json.loads(riga)
        fuori.setdefault(d["scena"], []).append(d)
    return fuori, None


def campi(testa):
    """I sette campi di §6.2, letti dai 28 byte come li legge chi riceve."""
    import struct as _s
    t, c, lar, alt, num, ist, inp = _s.unpack("!HHIIIQI", testa)
    return dict(tipo=t, codec=c, lar=lar, alt=alt, num=num, ist=ist, inp=inp)


def rifai_testa(v):
    import struct as _s
    return _s.pack("!HHIIIQI", v["tipo"], v["codec"], v["lar"], v["alt"],
                   v["num"], v["ist"], v["inp"])


def contesto_di(sc):
    """Il contesto del client per questa scena.

    ⛔ Tre pezzi, e sono tre perche' i fatti sono tre: quel che il client sa
       dalla stretta di mano (la tela concessa, il codec negoziato), quel che
       ha gia' consegnato al decodificatore, e ⛔ **i messaggi di §7.1 che ha
       visto passare** — un `TELA(ADATTATA)` non e' uno stato, e' un
       messaggio, e il giudice non lo puo' sapere da solo.
    """
    d = dict(sc.get("contesto", {}))
    c = G.Contesto(tela=d.pop("tela", (1920, 1080)),
                   codec_negoziato=d.pop("codec_negoziato", 1),
                   sessione_aperta=d.pop("sessione_aperta", True))
    dopo = d.pop("dopo_tela", None)
    if dopo:
        c.adatta_tela(*dopo)
    for k, v in d.items():
        setattr(c, k, v)
    return c


def giudica(sc, tr, guasto=None):
    """Da' i byte del prodotto all'arbitro, a pezzi, come arriverebbero."""
    testa = bytes.fromhex(tr["testa"])
    lung = tr["lunghezza"]
    fine = tr["fine"]
    if guasto:
        if "campo" in guasto and len(testa) == 28:
            v = campi(testa)
            v[guasto["campo"]] = guasto["valore"]
            testa = rifai_testa(v)
        if "fine" in guasto:
            fine = guasto["fine"]
        if "lunghezza" in guasto:
            lung = guasto["lunghezza"]
    g = G.Giudice(contesto_di(sc), dove="uni")
    g.arrivano(testa)
    # ⛔ I dati si danno a PEZZI e non tutti insieme: §6.2 vuole che il tetto
    #    scatti «invece di continuare ad accumulare», e un banco che passasse
    #    16 MiB in una chiamata sola misurerebbe la propria memoria.
    resta = max(0, lung - len(testa))
    blocco = b"\x00" * 65536
    while resta > 0:
        q = min(resta, len(blocco))
        g.arrivano(blocco[:q])
        resta -= q
    if fine in ("fin", "reset"):
        g.finisce(fine)
    return g


def una_scena(sc, tracce, guasto=None):
    """Restituisce (va_bene, righe)."""
    righe = []
    ok = True
    ts = tracce.get(sc["nome"])
    if not ts:
        return False, [f"⛔ nessuna traccia per «{sc['nome']}»"]
    d = ts[0]

    if d["esito"] != sc["esito"]:
        ok = False
        righe.append(f"⛔ {sc['nome']}: esito {NOME_ESITO.get(sc['esito'])} -> "
                     f"{NOME_ESITO.get(d['esito'], d['esito'])}")
    if len(d["stream"]) != sc["stream"]:
        ok = False
        righe.append(f"⛔ {sc['nome']}: stream {sc['stream']} -> "
                     f"{len(d['stream'])}")
    if "serve_chiave" in sc and d["serve_chiave"] != sc["serve_chiave"]:
        ok = False
        righe.append(f"⛔ {sc['nome']}: serve_chiave {sc['serve_chiave']} -> "
                     f"{d['serve_chiave']}")
    if sc.get("tolleranza") and d["tolleranza"] != "si":
        ok = False
        righe.append(f"⛔ {sc['nome']}: la tolleranza di §3 NON e' dichiarata "
                     f"nel registro")
    # ⛔ P3: il video NON finisce sul canale di controllo.  I 150 byte sono
    #    quelli della stretta di mano; un fotogramma ne aggiungerebbe migliaia.
    if d["byte_sul_controllo"] > 400:
        ok = False
        righe.append(f"⛔ {sc['nome']}: {d['byte_sul_controllo']} byte sul "
                     f"canale di CONTROLLO — §2.5 vieta il video li'")

    if not d["stream"]:
        return ok, righe
    tr = d["stream"][0]
    if "fine" in sc and tr["fine"] != sc["fine"]:
        ok = False
        righe.append(f"⛔ {sc['nome']}: lo stream finisce «{sc['fine']}» -> "
                     f"«{tr['fine']}»")
    if "lunghezza" in sc and tr["lunghezza"] != sc["lunghezza"]:
        ok = False
        righe.append(f"⛔ {sc['nome']}: lunghezza {sc['lunghezza']} -> "
                     f"{tr['lunghezza']}")
    # i campi dichiarati, uno per uno
    if sc.get("testa") and len(tr["testa"]) == 56:
        v = campi(bytes.fromhex(tr["testa"]))
        for k, atteso in sc["testa"].items():
            if v[k] != atteso:
                ok = False
                righe.append(f"⛔ {sc['nome']}: campo `{k}` {atteso} -> {v[k]}")

    if sc["verdetto"] is None:
        return ok, righe
    g = giudica(sc, tr, guasto)
    visto = g.verdetto.esito if g.verdetto else ACC
    if visto != sc["verdetto"]:
        ok = False
        # ⛔ LA MARCA, nella forma delle due meta': a giro sano atteso e visto
        #    coincidono sempre, quindi «X: A -> B» con A != B esiste SOLTANTO
        #    quando qualcosa e' rotto.
        righe.append(f"⛔ {sc['nome']}: {sc['verdetto']} -> {visto}")
        if g.verdetto:
            righe.append(f"      l'arbitro dice: {g.verdetto}")
    return ok, righe


def giro(tracce, guasto=None, zitto=False):
    rossi = 0
    marche = []
    for sc in SCENE:
        gu = None
        if guasto and guasto.get("scena") == sc["nome"]:
            gu = guasto
        ok, righe = una_scena(sc, tracce, gu)
        if not ok:
            rossi += 1
            marche.extend(righe)
        if not zitto:
            segno = "OK" if ok else "NO"
            print(f"  {segno}  {sc['nome']:32s} {sc['regola']}")
            for r in righe:
                print(f"        {r}")
    return rossi, marche


def elenco():
    print("== F2.4 — il PRODOTTO sul filo, giudicato dall'arbitro: "
          f"{len(SCENE)} scene")
    n_byte = sum(1 for s in SCENE if s["stream"])
    print(f"   {n_byte} scene mettono byte sul filo · "
          f"{len(SCENE) - n_byte} devono NON metterne nemmeno uno")
    print("   ⛔ Ogni riga e' una PREVISIONE, scritta prima del giro")
    print()
    for s in SCENE:
        v = s["verdetto"] or "⛔ NESSUNO STREAM"
        print(f"  {s['nome']:32s} {v}")
        print(f"      esito atteso: {NOME_ESITO.get(s['esito'], s['esito'])} · "
              f"stream attesi: {s['stream']} · regola: {s['regola']}")
        print(f"      {s['spiega']}")
        print()
    print(f"== ⛔ I GUASTI, {len(GUASTI)}, e si innestano SUI BYTE")
    for k, g_ in GUASTI.items():
        print(f"  {k}  {g_['dice']}")
        print(f"      atteso: {g_['atteso']}")
    return 0


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--certifica", action="store_true")
    p.add_argument("--uscita", default=None)
    a = p.parse_args()

    if a.elenco:
        return elenco()

    # ⛔ Il binario si costruisce FUORI dall'albero: un artefatto lasciato in
    #    `banchi/` diventa un file che qualcuno un giorno crede sorgente, e
    #    `.gitignore` non lo copre.  ⚠ E si ricostruisce a ogni giro: «il file
    #    c'e'» e «il file e' quello che ho appena costruito» sono due domande
    #    diverse (`LEZIONI.md` §1.9 punto 8).
    import tempfile
    tmp = tempfile.mkdtemp(prefix="02-filo-prodotto-")
    binario = os.path.join(tmp, "ospite")
    r = compila(binario)
    if r.returncode != 0:
        print("⛔ la compilazione dell'ospite e' FALLITA — e non e' «zero "
              "scene»: e' «non ho potuto guardare»")
        print(r.stderr[:2000])
        return 2
    if r.stderr.strip():
        print("⚠ il compilatore ha avuto qualcosa da dire, e si riporta:")
        print("   " + r.stderr.strip().replace("\n", "\n   "))

    tracce, err = raccogli(binario)
    if err:
        print(f"⛔ {err}")
        return 2

    if not a.certifica:
        print("== F2.4 — i byte del PRODOTTO davanti all'arbitro del filo")
        print(f"   scene: {len(SCENE)}   sorgente: banchi/rcp/rcp.c "
              "(identico a src/rcp.c per costruzione — vedi il `Makefile`)")
        print()
        rossi, _ = giro(tracce)
        print()
        if rossi:
            print(f"  ⛔ {rossi} scene su {len(SCENE)} non passano")
            return 1
        print(f"  ⭐ {len(SCENE)} scene su {len(SCENE)} passano")
        print("  ⚠ e NON e' «il fotogramma arriva»: qui non c'e' ne' QUIC ne'")
        print("    WebTransport.  Quella misura e' del cliente di prova.")
        return 0

    # --- la certificazione: sano -> guasto -> risanato ---------------------
    print("== ⛔ LA CERTIFICAZIONE — «saprebbe accorgersi che non funziona?»")
    sano, marche_sane = giro(tracce, zitto=True)
    print(f"   sano: {sano} scene rosse su {len(SCENE)}   (atteso: 0)")
    if sano != 0:
        print("   ⛔ il giro sano non e' pulito: non certifico niente")
        for m in marche_sane:
            print(f"      {m}")
        return 1
    male = 0
    for sigla, gu in GUASTI.items():
        rossi, marche = giro(tracce, guasto=gu, zitto=True)
        # ⛔ LE DUE META' DELLA MARCA: il guasto la deve dire...
        detta = len(marche) > 0
        # ...e il giro sano NON la deve gia' dire.
        gia_detta = any(m in marche_sane for m in marche)
        stato = "OK" if (rossi > 0 and detta and not gia_detta) else "NO"
        if stato == "NO":
            male += 1
        print(f"  {stato}  {sigla}: sano 0 -> guasto {rossi} -> "
              f"marca {'vista' if detta else 'ASSENTE'}, "
              f"{'già nel sano ⛔' if gia_detta else 'assente dal sano'}")
        print(f"        {gu['dice']}")
        for m in marche[:2]:
            print(f"        {m}")
    # e si RISANA: lo stesso giro di prima, senza guasti
    di_nuovo, _ = giro(tracce, zitto=True)
    print(f"   risanato: {di_nuovo} scene rosse su {len(SCENE)}   (atteso: 0)")
    if di_nuovo != 0:
        male += 1
    print()
    if male:
        print(f"  ⛔ {male} guasti su {len(GUASTI)} non si vedono")
        return 1
    print(f"  ⭐ {len(GUASTI)} guasti su {len(GUASTI)}: sano 0 -> >0 -> 0, "
          "marca vista nel rosso e assente dal sano")
    return 0


if __name__ == "__main__":
    sys.exit(main())
