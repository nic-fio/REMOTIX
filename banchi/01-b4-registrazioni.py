#!/usr/bin/env python3
"""01-b4-registrazioni.py — le registrazioni di B4, e che cosa il validatore DEVE dire.

    python3 01-b4-registrazioni.py [cartella]     predefinita: ./b4-registrazioni

⛔ **Quante sono non sta scritto qui**: le costruisce `costruisci()`, le conta
   il programma e le stampa insieme al manifesto.  Un numero scritto a mano in
   un commento e' il numero che nessuno ricalcola.

---------------------------------------------------------------------------
⛔ UNA CONFORME, E LE ALTRE SONO I QUATTRO MODI DI NON ESSERLO

`FASI.md` §01-filo-nudo B4: senza la registrazione **conforme**, «6 su 6» e'
compatibile con un validatore che **boccia tutto** — basta leggere `lunghezza`
come `u16` invece di `u32`, due caratteri, e da quel momento l'arbitro dichiara
non conforme ogni traccia con la diagnosi che punta su `RCP.md` §6.1 mentre il
difetto e' nello strumento (rilievo R3.5).

⛔ **E si dichiara QUALE byte**, non solo che dev'essere rosso.  Ogni guasto qui
   sotto porta lo scostamento esatto del byte offensivo, calcolato mentre lo si
   costruisce.  Un validatore che desse rosso sul byte sbagliato — tipico di
   chi non conosce §6.0 e legge di traverso il messaggio SUCCESSIVO — passerebbe
   un banco che guardasse solo il colore.

---------------------------------------------------------------------------
⛔ E GLI ESITI SONO QUATTRO, QUINDI I CONTROLLI POSITIVI SONO QUATTRO

*Aggiunti il 10 agosto 2026, rilievi R7.12 e R7.13.*

Il validatore dichiara quattro esiti — conforme, non conforme, registrazione
rotta, niente da giudicare — e fino a qui le registrazioni ne esercitavano
**due**.  ⚠ L'esito che il validatore dichiara essere *la ragione per cui gli
esiti non sono due* non era mai stato osservato dal banco che lo certifica:
si poteva rompere `Malformata` — farla diventare un `NonConforme` — e questo
banco continuava a stampare «e' certificato», perche' nessuna registrazione
era rotta.

Le nuove, e ciascuna copre un buco dichiarato:

| | |
|---|---|
| `7-tela-dispari` | ⛔ **nessuna registrazione esercitava §4.5**, ed e' proprio li' che il validatore accusava il byte sbagliato — `le.base, 0`, due scostamenti che indicano due byte diversi.  Il banco che esiste per prendere «rosso giusto, byte sbagliato» non copriva la famiglia in cui il difetto c'era davvero (R7.12) |
| `8-carico-troncato` | il primo controllo positivo dell'**esito 2** |
| `9-oscurati-sovrapposti` | il caso che §11.1 nomina per esteso: *«DEVE rifiutare una registrazione in cui un intervallo oscurato … si sovrappone a un altro»* |
| `10-coda-di-spazzatura` | byte dopo l'ultimo blocco dichiarato |
| `11-quanti-sotto-dichiarato` | ⛔ il piu' insidioso: si scrive 4 dove i blocchi sono 6, e il file resta **valido per ogni altra riga di §11.1** mentre due blocchi spariscono dal giudizio |
| `12-niente-da-giudicare` | l'**esito 3**: ⚠ *diceva «soli blocchi video»*, e dal **12 agosto 2026** porta soli blocchi di **appunti** — perche' il video adesso il validatore lo giudica, e quel file uscirebbe **1** |

---------------------------------------------------------------------------
⭐⛔ E DAL 12 AGOSTO 2026 CI SONO ANCHE LE REGISTRAZIONI DEL **VIDEO**

*Le sette righe di F2.4 sono entrate in `RCP.md` (§2.5, §5.2, §6.2, §11.1), e
sei di esse sono regole sul canale video che **nessun arbitro sapeva
giudicare**.*

⛔ Il formato della registrazione e' passato a **`RCPREG 0x00 0x02`** e il
blocco porta un campo in piu' — `fine`: *0 continua · 1 FIN · 2 RESET_STREAM* —
senza il quale *«un fotogramma abbandonato e uno troncato per errore hanno lo
stesso aspetto nella registrazione»* (§11.1, forma d'errore **E8**).

Le registrazioni nuove, **due per ciascuna riga**: quella che la viola e quella
che la rispetta, che qui e' la `13-video-conforme` per cinque righe su sei.

| | |
|---|---|
| `13-video-conforme` | ⭐ la chiave che la fase 2 esiste per consegnare: **rispetta** P1, P2, P4, P5, P6 in un colpo.  Senza, un validatore che rifiutasse ogni fotogramma sarebbe verde su tutte le violazioni |
| `14-video-prima-di-sessione` | **P1** §2.5 |
| `15-video-sul-controllo` | **P3** §2.5 |
| `16-video-numero-zero` | **P2** §6.2 |
| `17-video-misura-diversa` | **P5** §6.2 |
| `18-video-primo-delta` | **P6** §5.2 |
| `19-video-fin-corto` | **P4** §6.2 |
| `20-video-abbandonato` | ⭐ **P7** §11.1 — uscita **0**: `fine = 2` dice che il server ha abbandonato **di proposito**, il fotogramma si butta e la sessione regge (§5.1).  ⛔ E' la registrazione che dimostra a che cosa serve il campo nuovo: senza, era identica alla `19` |

---------------------------------------------------------------------------
⚠ E LA PAROLA D'ORDINE NON C'E'

La registrazione conforme contiene un `CREDENZIALI` vero, con la parola
**oscurata** secondo `RCP.md` §11.1: lunghezza vera, byte sostituiti con `0x2A`,
impronta di quel che c'era.  E' il caso che il formato esiste per servire, e va
esercitato qui — non alla prima traccia vera.
"""
import hashlib
import json
import os
import struct
import sys

# ⛔ LA MAGIA E' `0x00 0x02` DAL 12 AGOSTO 2026 — `RCP.md` §11.1, proposta P7.
#
#    Il blocco porta un campo in piu', `fine`, e quindi **cambia misura**: 17
#    byte invece di 16.  §11.1: *«la magia passa a 0x00 0x02 perche' il blocco
#    cambia misura: un validatore vecchio deve RIFIUTARE il formato nuovo, non
#    leggerlo di traverso»*.
#    ⚠ E gli scostamenti attesi di tutte le registrazioni si spostano di un
#      byte per blocco: ⭐ **non c'e' un solo numero da correggere a mano**,
#      perche' `Registrazione.scostamento()` li calcola da `BLOCCO_BYTE`.  Un
#      atteso scritto a mano avrebbe richiesto tredici correzioni, e sarebbe
#      stata la volta in cui una si dimentica.
MAGIA = b"RCPREG\x00\x02"
MAGIA_VECCHIA = b"RCPREG\x00\x01"
RIEMPIMENTO = 0x2A
CLIENT, SERVER = 1, 2

# Il blocco di §11.1: verso, canale, fine, stream, lunghezza, quanti_oscurati.
BLOCCO = "!BBBQIH"
BLOCCO_BYTE = struct.calcsize(BLOCCO)

# ⛔ `fine` — «come si e' chiuso lo stream DOPO questo blocco» (§11.1).
CONTINUA, FIN, RESET = 0, 1, 2

VIDEO = 0x03
CHIAVE, DELTA = 0x0301, 0x0302      # §6.2

# I quattro esiti di `01-b4-validatore.py`, con il loro nome — scritti qui una
# volta perche' il manifesto li porti per esteso e non per numero.
ESITI = {0: "conforme", 1: "non-conforme", 2: "registrazione-rotta",
         3: "niente-da-giudicare"}


# ---------------------------------------------------------------------------
def s(testo):
    """RCP.md §6.0: u16 lunghezza + UTF-8, senza terminatore."""
    b = testo.encode("utf-8") if isinstance(testo, str) else testo
    return struct.pack("!H", len(b)) + b


def cap(coppie):
    out = struct.pack("!H", len(coppie))
    for n, v in coppie:
        out += s(n) + s(v)
    return out


def msg(tipo, corpo, lunghezza=None):
    """L'inquadratura di §6.1: u16 tipo, u32 lunghezza, corpo."""
    n = len(corpo) if lunghezza is None else lunghezza
    return struct.pack("!HI", tipo, n) + corpo


CIAO = msg(0x0001, struct.pack("!H", 1) + cap([
    ("video.codec", "hevc,av1"),
    ("video.profondita", "8,10"),
    ("audio.codec", "opus,pcm"),
    ("video.livello", "5.1"),
    ("video.misura_massima", "3840x2160"),
    ("appunti.testo", "si"),
    ("input.tocco", "no"),
    ("client.nome", "cliente-di-prova 0.1.0"),
]))
ECCOMI = msg(0x0002, struct.pack("!H", 1) + cap([
    ("video.codec", "hevc"),
    ("video.profondita", "8,10"),
    ("audio.codec", "opus,pcm"),
    ("appunti.testo", "si"),
    ("banco.marca", "no"),
]))
AMMESSO = msg(0x0004, b"")
ATTACCA = msg(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080) + s("it"))
SESSIONE = msg(0x0007, struct.pack("!B", 1) + struct.pack("!II", 1920, 1080) + s("gnome"))

UTENTE, PAROLA = "prova", "parola-di-prova"


def credenziali():
    """Il corpo di CREDENZIALI, e dove cade la parola dentro il corpo.

    ⛔ Restituisce anche l'intervallo da oscurare: il registratore vero fara'
       la stessa cosa, e il fatto che il calcolo sia UNO SOLO e' il motivo per
       cui §11.1 dice «il formato e' uno solo, scritto una volta».
    """
    u, p = UTENTE.encode(), PAROLA.encode()
    corpo = s(u) + s(p)
    inizio_parola = 2 + len(u) + 2      # dentro il corpo del messaggio
    return corpo, inizio_parola, len(p), hashlib.sha256(p).digest()


# ---------------------------------------------------------------------------
class Registrazione:
    """Costruisce il file di §11.1 tenendo il conto degli scostamenti."""

    def __init__(self):
        self.blocchi = []
        # ⛔ I tre modi di rompere il FILE invece del filo, e vivono qui perche'
        #    una registrazione malformata si costruisce **di proposito**: senza
        #    di essi l'esito 2 del validatore non ha nessun controllo positivo
        #    (rilievo R7.13).
        self.dichiarate = {}    # indice -> lunghezza DICHIARATA, diversa dalla vera
        self.dichiara_quanti = None   # `quanti_blocchi` diverso da quelli scritti
        self.coda = b""         # byte dopo l'ultimo blocco
        # ⛔ E il quarto: la MAGIA di ieri, `RCPREG 0x00 0x01`, col blocco da 16
        #    byte.  Serve a una cosa sola, ed e' quella che §11.1 chiede per
        #    nome: *«un validatore vecchio deve RIFIUTARE il formato nuovo»*.
        #    ⚠ Un formato che sa scrivere solo la propria versione non puo'
        #      certificare di saper rifiutare le altre.
        self.magia = MAGIA

    def blocco(self, verso, carico, canale=0x00, stream=0, oscurati=(),
               fine=CONTINUA):
        """⛔ `fine` e' predefinito a CONTINUA, e non e' pigrizia.

        Il canale di controllo vive su **un solo stream per tutta la sessione**
        (§2.5): dentro una registrazione della stretta di mano quello stream
        non si chiude mai, quindi `0` — «continua» — e' il valore vero.
        ⚠ Metterci `1` per far contento un lettore direbbe che la sessione si e'
          chiusa a ogni messaggio.
        """
        self.blocchi.append((verso, canale, stream, carico, list(oscurati),
                             fine))
        return self

    def scostamento(self, indice_blocco, dentro):
        """Lo scostamento ASSOLUTO nel file del byte `dentro` del blocco dato.

        ⛔ Poggia su `BLOCCO_BYTE`, mai su un 16 scritto a mano: e' quel che ha
           reso il passaggio a `0x00 0x02` una riga sola invece di tredici
           attesi da correggere.
        """
        p = 16
        for i, b in enumerate(self.blocchi):
            carico, osc = b[3], b[4]
            p += BLOCCO_BYTE + 40 * len(osc)
            if i == indice_blocco:
                return p + dentro
            p += len(carico)
        raise IndexError(indice_blocco)

    def byte(self):
        quanti = (len(self.blocchi) if self.dichiara_quanti is None
                  else self.dichiara_quanti)
        out = bytearray(self.magia + struct.pack("!II", quanti, 0))
        for i, (verso, canale, stream, carico, osc, fine) in enumerate(
                self.blocchi):
            lung = self.dichiarate.get(i, len(carico))
            if self.magia == MAGIA_VECCHIA:
                out += struct.pack("!BBQIH", verso, canale, stream, lung,
                                   len(osc))
            else:
                out += struct.pack(BLOCCO, verso, canale, fine, stream, lung,
                                   len(osc))
            for ini, qua, imp in osc:
                out += struct.pack("!II", ini, qua) + imp
            out += carico
        return bytes(out) + self.coda


def conforme():
    """La stretta di mano intera, con la parola d'ordine oscurata."""
    corpo, ini, qua, imp = credenziali()
    cred = msg(0x0003, corpo)
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    # l'intervallo oscurato e' dentro il CARICO del blocco: 6 byte di
    # inquadratura, poi il corpo
    r.blocco(CLIENT, cred[:6 + ini] + bytes([RIEMPIMENTO]) * qua + cred[6 + ini + qua:],
             oscurati=[(6 + ini, qua, imp)])
    r.blocco(SERVER, AMMESSO)
    r.blocco(CLIENT, ATTACCA)
    r.blocco(SERVER, SESSIONE)
    return r


# ---------------------------------------------------------------------------
def costruisci():
    """Ciascuna col suo atteso: `(nome, registrazione, uscita, atteso, che)`.

    ⛔ `uscita` e' il codice che il validatore DEVE restituire — 0 conforme,
       1 non conforme, 2 registrazione rotta, 3 niente da giudicare — e
       `atteso` porta regola e byte **solo** quando l'uscita e' 1.  Prima qui
       c'erano due esiti su quattro, e i due mancanti erano proprio quelli che
       il validatore dichiara di avere per non confondere un difetto di banco
       con un difetto di protocollo (rilievo R7.13).
    """
    casi = []

    # ── 7. la conforme — si costruisce per prima perche' e' la base delle altre
    casi.append(("conforme", conforme(), 0, None,
                 "la stretta di mano intera, con la parola oscurata"))

    # ── 1. lunghezza incoerente col tipo (§6.1) ─────────────────────────────
    #    `ATTACCA` dichiara 4 byte in meno di quelli che i suoi campi vogliono:
    #    il corpo finisce mentre si legge la vista.
    corpo_a = struct.pack("!IIII", 1920, 1080, 1920, 1080) + s("it")
    r = conforme()
    r.blocchi[4] = (CLIENT, 0x00, 0, msg(0x0006, corpo_a[:-6],
                                        len(corpo_a) - 6), [], CONTINUA)
    # ⛔ Il byte offensivo e' dove il campo MANCANTE sarebbe cominciato — qui
    #    `vista_altezza`, dopo i primi tre u32 — non la fine del corpo.
    #    ⚠ Il primo atteso scritto il 10 agosto diceva «la fine del corpo», e
    #      il validatore ha risposto due byte prima.  Aveva ragione lui: il
    #      byte da mostrare a chi diagnostica e' quello da cui la lettura non
    #      prosegue, non quello dove i dati finiscono.  E' la terza volta in un
    #      giorno che l'ATTESO sbaglia e lo strumento no.
    casi.append(("1-lunghezza-incoerente", r, 1,
                 ("RCP.md §6.1", r.scostamento(4, 6 + 12)),
                 "ATTACCA dichiara meno byte di quanti i suoi campi ne vogliono"))

    # ── 2. UTF-8 non valido (§6.0) ──────────────────────────────────────────
    #    Un valore di capacita' con una sequenza rotta: 0xC3 senza il secondo
    #    byte.  E' il caso in cui un ricevente disattento accetta e poi mostra
    #    un nome storpiato in un registro.
    guasto = b"remotix\xc3\x28prova"
    corpo_c = struct.pack("!H", 1) + cap([("video.codec", "hevc")])
    # si rifa' l'elenco a mano per sapere DOVE cade il byte rotto
    voci = [(b"video.codec", b"hevc"), (b"client.nome", guasto)]
    corpo_c = struct.pack("!HH", 1, len(voci))
    # ⚠ Lo scostamento si accumula su TUTTE le voci che precedono, non solo su
    #   quella guasta: il primo giro del 10 agosto lo calcolava dall'inizio
    #   dell'elenco e accusava un byte 19 posizioni piu' indietro.
    #   ⛔ E' l'errore che questo banco esiste per prendere — solo che stavolta
    #      stava nell'ATTESO, non nel validatore.
    scost = None
    for n, v in voci:
        if v is guasto:
            scost = len(corpo_c) + 2 + len(n) + 2 + 7  # fino al byte 0xC3
        corpo_c += s(n) + s(v)
    r = conforme()
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [], CONTINUA)
    casi.append(("2-utf8-non-valido", r, 1,
                 ("RCP.md §6.0", r.scostamento(0, 6 + scost)),
                 "client.nome contiene una sequenza UTF-8 rotta"))

    # ── 3. nome di capacita' ripetuto (§4.3) ────────────────────────────────
    voci = [(b"video.codec", b"hevc"), (b"video.profondita", b"8"),
            (b"video.codec", b"av1")]
    corpo_c = struct.pack("!HH", 1, len(voci))
    scost = None
    for k, (n, v) in enumerate(voci):
        if k == 2:
            scost = len(corpo_c)
        corpo_c += s(n) + s(v)
    r = conforme()
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [], CONTINUA)
    casi.append(("3-capacita-ripetuta", r, 1,
                 ("RCP.md §4.3", r.scostamento(0, 6 + scost)),
                 "video.codec compare due volte"))

    # ── 4. byte alto fuori dai cinque canali (§2.5) ─────────────────────────
    #    Un tipo 0x0701: il byte alto vale 7, e i canali sono cinque.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0701, b""), [], CONTINUA)
    casi.append(("4-canale-sconosciuto", r, 1,
                 ("RCP.md §2.5", r.scostamento(3, 0)),
                 "un tipo il cui byte alto non e' uno dei cinque canali"))

    # ── 5. messaggio nello stato sbagliato (§4) ─────────────────────────────
    #    ATTACCA prima di CREDENZIALI.
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(CLIENT, ATTACCA)
    casi.append(("5-stato-sbagliato", r, 1,
                 ("RCP.md §4 (l'ordine della stretta di mano)", r.scostamento(2, 0)),
                 "ATTACCA prima di CREDENZIALI"))

    # ── 6. ⭐ corpo giusto ma ALLINEATO (§6.0) ───────────────────────────────
    #    `AMMESSO` ha corpo vuoto; qui ne dichiara quattro, di riempimento —
    #    esattamente quel che farebbe una struttura C allineata a 4.
    #    ⛔ E dopo c'e' un altro messaggio: un validatore che non conosce §6.0
    #       leggerebbe di traverso QUELLO, e darebbe rosso sul byte sbagliato.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0004, b"\x00\x00\x00\x00"), [],
                    CONTINUA)
    casi.append(("6-riempimento", r, 1,
                 ("RCP.md §6.0", r.scostamento(3, 6)),
                 "AMMESSO con quattro byte di riempimento, e un messaggio dopo"))

    # ── 7. ⛔ tela DISPARI (§4.5) — la famiglia che nessuna registrazione
    #        esercitava, ed e' quella in cui il validatore accusava il byte
    #        sbagliato: `le.base, 0`, cioe' l'inizio del CORPO come assoluto e
    #        ZERO come relativo — due byte diversi per lo stesso guasto, mentre
    #        §11.1 chiede due modi di dire lo STESSO byte (rilievo R7.12).
    #        L'atteso e' il primo byte di `tela_larghezza`, che sta all'inizio
    #        del corpo di ATTACCA, cioe' sei byte dopo l'inizio del blocco.
    r = conforme()
    r.blocchi[4] = (CLIENT, 0x00, 0,
                    msg(0x0006, struct.pack("!IIII", 1921, 1080, 1920, 1080)
                        + s("it")), [], CONTINUA)
    casi.append(("7-tela-dispari", r, 1,
                 ("RCP.md §4.5", r.scostamento(4, 6)),
                 "ATTACCA con tela_larghezza = 1921, dispari"))

    # ── 8. ⛔ il carico TRONCATO — controllo positivo dell'esito 2.
    #        Il blocco dichiara piu' byte di quanti ne porta: e' il file a
    #        essere rotto, non il filo a essere non conforme, e le due cose
    #        vogliono due frasi diverse.  ⚠ Se `Malformata` diventasse un
    #        `NonConforme`, questa registrazione lo grida; prima non lo
    #        gridava nessuna, e B4 continuava a stampare «e' certificato».
    r = conforme()
    r.dichiarate[5] = len(r.blocchi[5][3]) + 8
    casi.append(("8-carico-troncato", r, 2, None,
                 "l'ultimo blocco dichiara otto byte che non ci sono"))

    # ── 9. ⛔ due intervalli oscurati che SI SOVRAPPONGONO — §11.1 lo nomina
    #        per esteso, e nessuna registrazione lo esercitava.
    r = conforme()
    v, c, st, carico, osc, fine = r.blocchi[2]
    ini_osc = osc[0][0]
    r.blocchi[2] = (v, c, st, carico,
                    [(ini_osc, 4, osc[0][2]), (ini_osc + 2, 4, osc[0][2])],
                    fine)
    casi.append(("9-oscurati-sovrapposti", r, 2, None,
                 "due intervalli oscurati che si accavallano di due byte"))

    # ── 10. ⛔ una CODA dopo l'ultimo blocco dichiarato.
    r = conforme()
    r.coda = b"\xff" * 16
    casi.append(("10-coda-di-spazzatura", r, 2, None,
                 "sedici byte dopo l'ultimo blocco: non sono del formato"))

    # ── 11. ⛔ `quanti_blocchi` SOTTO-DICHIARATO, ed e' il piu' insidioso:
    #         il file resta valido per ogni altra riga di §11.1, e i due
    #         blocchi in coda non vengono mai letti.  Qui il quinto blocco
    #         porta un ATTACCA con la tela dispari — cioe' una violazione
    #         vera — che sotto-dichiarando sparisce dal giudizio.
    r = conforme()
    r.blocchi[4] = (CLIENT, 0x00, 0,
                    msg(0x0006, struct.pack("!IIII", 1921, 1080, 1920, 1080)
                        + s("it")), [], CONTINUA)
    r.dichiara_quanti = 4
    casi.append(("11-quanti-sotto-dichiarato", r, 2, None,
                 "quanti_blocchi dice 4 e i blocchi sono 6: la violazione "
                 "sta nel quinto"))

    # ── 12. ⛔ NIENTE DA GIUDICARE — l'esito 3.  Un file ben formato in cui
    #         non c'e' niente che questo validatore sappia giudicare:
    #         «conforme» qui sarebbe vero e vuoto (LEZIONI.md §1.9).
    #
    #    ⚠ ⛔ QUESTA REGISTRAZIONE E' CAMBIATA IL 12 AGOSTO 2026, e va detto
    #      perche' il cambiamento e' la MISURA di quel che il validatore ha
    #      imparato.  Prima portava **un blocco video**, e usciva 3 per la
    #      ragione che la sua riga 521 dichiarava: *«canale video — non
    #      giudicato da questo validatore»*.  ⭐ Adesso il video lo giudica, e
    #      quel file uscirebbe **1**.  ⇒ Per tenere vivo il controllo positivo
    #      dell'esito 3 ci vuole un canale che nessuno dei due arbitri giudica,
    #      e sono gli **appunti** (`0x02`, §7.4): li' «non ho guardato» resta
    #      un fatto vero, e resta dichiarato invece che assolto.
    r = Registrazione()
    r.blocco(CLIENT, msg(0x0201, b"\x00" * 8), canale=0x02, stream=6)
    casi.append(("12-niente-da-giudicare", r, 3, None,
                 "un solo blocco di APPUNTI: zero messaggi di controllo e zero "
                 "flussi video"))

    # =======================================================================
    # ⭐⛔ 13-20 — IL CANALE VIDEO, E LE SEI RIGHE ENTRATE IN `RCP.md` IL 12
    #             AGOSTO 2026 (§2.5, §5.2, §6.2)
    #
    # ⛔ Prima di oggi nessuna registrazione di B4 portava un fotogramma
    #    giudicabile, e non era una dimenticanza: il validatore il video non lo
    #    guardava.  ⭐ Adesso lo guarda, e **un arbitro che conosce una regola e
    #    non ha l'ingresso che la fa scattare non la fa rispettare**: queste
    #    otto registrazioni sono quell'ingresso.
    #
    # ⛔ E ognuna delle sei righe ha DUE registrazioni, non una: quella che la
    #    viola e quella che la rispetta.  Senza la seconda, un validatore che
    #    rifiutasse **ogni** fotogramma sarebbe verde su tutte le violazioni.
    #    La registrazione che le rispetta tutte e sei insieme e' la 13.
    # =======================================================================
    def con_video(*blocchi_video, base=None):
        """La stretta di mano intera, e poi il video.  ⛔ In quest'ordine.

        `SESSIONE` e' il sesto blocco di `conforme()`, quindi ogni fotogramma
        aggiunto qui arriva **dopo**, che e' quel che §2.5 pretende (P1).
        """
        r = conforme() if base is None else base
        for b in blocchi_video:
            r.blocco(*b[:2], canale=VIDEO, stream=b[2], fine=b[3])
        return r

    def intestazione(tipo=CHIAVE, codec=1, lar=1920, alt=1080, num=1, ist=0,
                     inp=0):
        """I 28 byte di §6.2, in ordine di rete e senza riempimento.

        ⚠ Ricalcati qui e non importati: questo file **costruisce** i byte, e
          chi li giudica e' un altro programma.  Se costruissero e giudicassero
          con la stessa funzione, un errore nella struttura si annullerebbe da
          solo — che e' il difetto muto di `RCP.md` §0 dentro un banco.
        """
        return struct.pack("!HHIIIQI", tipo, codec, lar, alt, num, ist, inp)

    # ── 13. ⭐ il fotogramma che la fase 2 esiste per consegnare ────────────
    r = con_video((SERVER, intestazione() + b"\x00" * 512, 7, FIN))
    casi.append(("13-video-conforme", r, 0, None,
                 "⭐ una chiave 1920x1080 numero 1 dopo SESSIONE, chiusa con "
                 "FIN: rispetta tutte e sei le righe del 12 agosto"))

    # ── 14. P1 — §2.5: nessuno stream video prima di `SESSIONE` ────────────
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(SERVER, intestazione() + b"\x00" * 64, canale=VIDEO, stream=7,
             fine=FIN)
    casi.append(("14-video-prima-di-sessione", r, 1,
                 ("RCP.md §2.5", r.scostamento(2, 0)),
                 "⛔ P1 — uno stream video si apre prima che SESSIONE sia "
                 "passata: il client non conosce ne' la misura ne' il codec"))

    # ── 15. P3 — §2.5: un `0x03` sul canale di controllo ────────────────────
    #    ⛔ E lo si scrive sullo STREAM 0, che e' quello del canale di
    #       controllo: e' l'unico posto in cui il server puo' sbagliare, visto
    #       che §2.5 gli vieta di aprire stream bidirezionali.
    r = con_video((SERVER, intestazione() + b"\x00" * 64, 0, CONTINUA))
    casi.append(("15-video-sul-controllo", r, 1,
                 ("RCP.md §2.5", r.scostamento(6, 0)),
                 "⛔ P3 — l'intestazione di 28 byte scritta sullo stream del "
                 "canale di controllo"))

    # ── 16. P2 — §6.2: `numero` parte da 1, lo 0 e' riservato ───────────────
    r = con_video((SERVER, intestazione(num=0) + b"\x00" * 64, 7, FIN))
    casi.append(("16-video-numero-zero", r, 1,
                 ("RCP.md §6.2", r.scostamento(6, 12)),
                 "⛔ P2 — `numero = 0`, che §7.1 usa per «nessun fotogramma»"))

    # ── 17. P5 — §6.2: la misura DEVE valere la tela concessa ───────────────
    #    ⛔ E la tela concessa e' 1920x1080, e sta nel `SESSIONE` di
    #       `conforme()`: non e' un numero scritto nel validatore.
    r = con_video((SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 64, 7,
                   FIN))
    casi.append(("17-video-misura-diversa", r, 1,
                 ("RCP.md §6.2", r.scostamento(6, 4)),
                 "⛔ P5 — un fotogramma 1280x720 su una tela concessa "
                 "1920x1080"))

    # ── 17-bis. ⭐⛔ P5 RISPETTATA, ED E' LA REGISTRAZIONE CHE HA CORRETTO
    #            `RCP.md` — §6.2 contro §7.1.
    #
    #    Gli **stessi identici byte** della 17, ma fra `SESSIONE` e il
    #    fotogramma passa un `TELA(ADATTATA, 1280, 720)`.  ⛔ Con la prima
    #    stesura di P5 — *«la tela concessa in `SESSIONE`»* — questa
    #    registrazione usciva **1**: il client uccideva la sessione perche'
    #    l'utente aveva trascinato una finestra, che e' **esattamente** la
    #    scena che §7.1 protegge con la sua eccezione 4.  ⭐ Corretta lo stesso
    #    giorno in «la tela **in vigore**», e questa e' la prova che lo tiene.
    #    ⚠ Senza di lei la regola nuova sarebbe severa quanto quella sbagliata.
    r = conforme()
    r.blocco(SERVER, msg(0x000E, struct.pack("!BBII", 1, 0, 1280, 720)))
    r = con_video((SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 64, 7,
                   FIN), base=r)
    casi.append(("17bis-video-dopo-adatta-tela", r, 0, None,
                 "⭐ P5 — 1280x720 dopo un TELA(ADATTATA, 1280, 720): la tela "
                 "in vigore non e' piu' quella di SESSIONE, e il fotogramma "
                 "e' conforme"))

    # ── 18. P6 — §5.2: il primo fotogramma dopo `SESSIONE` DEVE essere chiave
    r = con_video((SERVER, intestazione(tipo=DELTA) + b"\x00" * 64, 7, FIN))
    casi.append(("18-video-primo-delta", r, 1,
                 ("RCP.md §5.2", r.scostamento(6, 0)),
                 "⛔ P6 — il primo fotogramma della sessione e' un delta: "
                 "«il desktop compare a pezzi», e nessuno ha torto"))

    # ── 19. P4 — §6.2: FIN prima dei 28 byte ────────────────────────────────
    r = con_video((SERVER, intestazione()[:12], 7, FIN))
    casi.append(("19-video-fin-corto", r, 1,
                 ("RCP.md §6.2", r.scostamento(6, 12)),
                 "⛔ P4 — lo stream si chiude con FIN dopo 12 byte: non e' un "
                 "fotogramma corto, e' una lunghezza che non torna"))

    # ── 20. ⭐ P7 — §11.1: il campo `fine` distingue l'ABBANDONO dall'errore
    #    ⛔ Esce **0**, ed e' il punto: §5.1 concede al server di abbandonare un
    #       fotogramma, il client lo butta e **la sessione regge**.  ⚠ Senza il
    #       campo `fine` questa registrazione era identica alla 19 — un carico
    #       che finisce prima del previsto — e l'arbitro doveva scegliere fra
    #       accusare un abbandono legale e assolvere un troncamento vero.
    r = con_video((SERVER, intestazione(), 7, CONTINUA),
                  (SERVER, b"\x00" * 4096, 7, RESET))
    casi.append(("20-video-abbandonato", r, 0, None,
                 "⭐ P7 — uno stream AZZERATO a meta': il fotogramma si butta "
                 "e la sessione regge (§5.1).  E' `fine = 2` a dirlo"))

    # ── 21. ⛔⛔ IL FORMATO DI IERI, che DEVE essere rifiutato — §11.1.
    #
    #    *«La magia passa a 0x00 0x02 perche' il blocco cambia misura: un
    #    validatore vecchio deve RIFIUTARE il formato nuovo, non leggerlo di
    #    traverso»* — e vale nei due versi.  ⛔ Senza questa registrazione, la
    #    riga che rifiuta `0x00 0x01` sarebbe **un ramo che nessuno fa girare**:
    #    si potrebbe cancellarla e il banco resterebbe verde, perche' tutte le
    #    altre venti sono scritte con la magia nuova.
    #    ⚠ E il contenuto e' la registrazione **conforme**: cosi' l'unica cosa
    #      che la fa rifiutare e' la versione, non un difetto del filo.
    r = conforme()
    r.magia = MAGIA_VECCHIA
    casi.append(("21-formato-vecchio", r, 2, None,
                 "⛔ una registrazione «RCPREG 0x00 0x01», conforme in tutto il "
                 "resto: si RIFIUTA, non si legge di traverso"))

    return casi


def main():
    dove = sys.argv[1] if len(sys.argv) > 1 else "b4-registrazioni"
    os.makedirs(dove, exist_ok=True)
    casi = costruisci()
    manifesto = []
    # ⛔ Il conteggio per esito, CALCOLATO: «tredici registrazioni» non dice
    #    quanti esiti diversi coprono, ed e' la copertura che conta.
    per_esito = {}
    print(f"== le {len(casi)} registrazioni di B4  ->  {dove}/")
    for nome, r, uscita, atteso, che in casi:
        percorso = os.path.join(dove, f"{nome}.rcpreg")
        with open(percorso, "wb") as f:
            f.write(r.byte())
        manifesto.append({
            "file": f"{nome}.rcpreg",
            "che": che,
            "uscita": uscita,
            "atteso": ESITI[uscita],
            "regola": None if atteso is None else atteso[0],
            "byte": None if atteso is None else atteso[1],
        })
        per_esito[uscita] = per_esito.get(uscita, 0) + 1
        if atteso is None:
            print(f"   {nome:<26s} attesa uscita {uscita} = {ESITI[uscita]:<20s} — {che}")
        else:
            print(f"   {nome:<26s} attesa uscita {uscita}, byte {atteso[1]:<5} "
                  f"{atteso[0]:<28s} — {che}")
    print()
    for u in sorted(ESITI):
        print(f"   uscita {u} = {ESITI[u]:<20s} coperta da "
              f"{per_esito.get(u, 0)} registrazioni"
              + ("   ⛔ NESSUNA" if not per_esito.get(u) else ""))
    with open(os.path.join(dove, "manifesto.json"), "w") as f:
        json.dump(manifesto, f, indent=1, ensure_ascii=False)
    print(f"\n   il manifesto — cioe' l'ATTESO, scritto qui e non nella testa di")
    print(f"   chi guarda — sta in {dove}/manifesto.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
