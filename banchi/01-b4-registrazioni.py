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
⭐⛔ E DAL 16 AGOSTO 2026 CI SONO LE REGISTRAZIONI DELLA **TELA** — sottofase 6.6

*`fasi/06-la-tela-e-la-vista.md` §0 punto 6: `ADATTA_TELA` (0x000B), `TELA`
(0x000E) e `VISTA` (0x0008) erano nel protocollo da una settimana e **nessuna
registrazione li portava**.  Le sette regole che §7.1 scrive in lettere
maiuscole erano regole che nessun ingresso faceva scattare.*

| | |
|---|---|
| `22-tela-non-sollecitata` | **T1** §7.1 — e' anche la ⏳ riga che §7.1 dichiara mancante: *«che cosa fa il server quando il palco cambia misura da se'»* |
| `23-tela-doppia` | **T2** §6.2 — *«l'n-esimo `TELA` risponde all'n-esima `ADATTA_TELA`»* |
| `24` · `24bis` | **T3** §7.1 — il silenzio, per le sue due vie: il `CONGEDO` e il FIN del server |
| `24ter` | ⭐ la stessa scena che **non** si accusa: la sessione e' viva, e la traccia e' solo finita prima |
| `25` · `26` | esito e motivo fuori dai valori dichiarati |
| `27-tela-rifiutata-cambia` | **T5** §7.1 — ogni campo e' valido e il **rapporto** fra i campi mente |
| `28` · `29` | **T6** §4.5 — la tela **concessa** dispari, e fuori dai limiti |
| `30-vista-cambia-tela` | **V3** §7.1 — *«`VISTA` NON DEVE far cambiare la tela»* |
| `31-vista-legale` | ⭐ **V2** — 1x1, dispari, 300x800, 9000x5000: il rilievo **R1.17** che non deve rientrare dal lato dell'arbitro |
| `32-vista-zero` | **V1** §7.1 — *«da 1x1 in su»* |
| `33-adatta-fuori-limiti-rifiutata` | ⭐ la richiesta impossibile e' **lecita**: §7.1 le dedica `MISURA_FUORI_LIMITI` |
| `34` · `35` | ⭐ il giro pieno, e due richieste in volo insieme |
| `36` · `37` | l'ordine della stretta di mano, e i due tipi del 15 agosto (`TERMINA_SESSIONE`, `CONGEDO(0x10)`) |
| `38`-`45` | ⛔ **le otto che non ha scritto chi ha scritto l'arbitro** — vedi il riquadro accanto al codice |

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
MAGIA = b"RCPREG\x00\x03"
MAGIA_V1 = b"RCPREG\x00\x01"
MAGIA_V2 = b"RCPREG\x00\x02"
MAGIA_VECCHIA = MAGIA_V1        # ⚠ il nome vecchio resta per chi lo importa
RIEMPIMENTO = 0x2A
CLIENT, SERVER = 1, 2

# Il blocco di §11.1: verso, canale, fine, stream, lunghezza, quanti_oscurati.
BLOCCO = "!BBBIQIH"        # ⭐ +`istante_ms` dal 21 agosto 2026: 21 byte
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
        # ⛔ `orologio` di §11.1: 1 = i tempi sono del client.  Le
        #    registrazioni COSTRUITE lo dichiarano client perche' e' il verso
        #    in cui l'arbitro sa concludere — dichiararlo «server» renderebbe
        #    inaccusabile la regola del secondo, e un banco che si toglie da
        #    solo la possibilita' di fallire non e' un banco.
        self.orologio = 1
        self.orologio_falso = None   # per la registrazione malformata apposta

    def blocco(self, verso, carico, canale=0x00, stream=0, oscurati=(),
               fine=CONTINUA, istante=0):
        """⛔ `fine` e' predefinito a CONTINUA, e non e' pigrizia.

        Il canale di controllo vive su **un solo stream per tutta la sessione**
        (§2.5): dentro una registrazione della stretta di mano quello stream
        non si chiude mai, quindi `0` — «continua» — e' il valore vero.
        ⚠ Metterci `1` per far contento un lettore direbbe che la sessione si e'
          chiusa a ogni messaggio.
        """
        self.blocchi.append((verso, canale, stream, carico, list(oscurati),
                             fine, istante))
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
        oro = (self.orologio if self.orologio_falso is None
               else self.orologio_falso)
        out = bytearray(self.magia
                        + struct.pack("!IBBBB", quanti, oro, 0, 0, 0))
        for i, (verso, canale, stream, carico, osc, fine, ist) in enumerate(
                self.blocchi):
            lung = self.dichiarate.get(i, len(carico))
            if self.magia == MAGIA_V1:
                out += struct.pack("!BBQIH", verso, canale, stream, lung,
                                   len(osc))
            elif self.magia == MAGIA_V2:
                out += struct.pack("!BBBQIH", verso, canale, fine, stream,
                                   lung, len(osc))
            else:
                out += struct.pack(BLOCCO, verso, canale, fine, ist, stream,
                                   lung, len(osc))
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
                                        len(corpo_a) - 6), [], CONTINUA, 0)
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
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [], CONTINUA, 0)
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
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [], CONTINUA, 0)
    casi.append(("3-capacita-ripetuta", r, 1,
                 ("RCP.md §4.3", r.scostamento(0, 6 + scost)),
                 "video.codec compare due volte"))

    # ── 4. byte alto fuori dai cinque canali (§2.5) ─────────────────────────
    #    Un tipo 0x0701: il byte alto vale 7, e i canali sono cinque.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0701, b""), [], CONTINUA, 0)
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
                    CONTINUA, 0)
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
                        + s("it")), [], CONTINUA, 0)
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
    v, c, st, carico, osc, fine, ist = r.blocchi[2]
    ini_osc = osc[0][0]
    r.blocchi[2] = (v, c, st, carico,
                    [(ini_osc, 4, osc[0][2]), (ini_osc + 2, 4, osc[0][2])],
                    fine, ist)
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
                        + s("it")), [], CONTINUA, 0)
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
            # ⭐ il quinto elemento, facoltativo, e' l'`istante_ms` del blocco:
            #    serve a T4, e senza di lui «quanto tempo e' passato» non c'e'.
            r.blocco(*b[:2], canale=VIDEO, stream=b[2], fine=b[3],
                     istante=(b[4] if len(b) > 4 else 0))
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
    #
    # ⛔⛔ E IL 16 AGOSTO 2026 QUESTA REGISTRAZIONE E' CAMBIATA — sottofase 6.6,
    #     e il cambiamento e' **una misura**, non una manutenzione.
    #
    #     Com'era scritta il 12 agosto, portava il `TELA(ADATTATA, 1280, 720)`
    #     **senza nessun `ADATTA_TELA` prima**.  ⚠ Cioe' la registrazione che ha
    #     corretto `RCP.md` §6.2 metteva in scena un filo che §7.1 **vieta**: un
    #     `TELA` non sollecitato, che §6.2 dichiara far *«chiudere una sessione
    #     sana»*.  Nessuno se n'era accorto perche' nessun arbitro contava le
    #     richieste in volo — ed e' la forma d'errore E8 dentro un banco: la
    #     scena giusta e quella vietata avevano lo stesso aspetto.
    #
    # ⭐ Adesso l'`ADATTA_TELA(1280, 720)` c'e', e la registrazione dice quel
    #    che ha sempre voluto dire: **l'utente ha trascinato la finestra**.
    r = conforme()
    r.blocco(CLIENT, msg(0x000B, struct.pack("!II", 1280, 720)))
    r.blocco(SERVER, msg(0x000E, struct.pack("!BBII", 1, 0, 1280, 720)))
    r = con_video((SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 64, 7,
                   FIN), base=r)
    casi.append(("17bis-video-dopo-adatta-tela", r, 0, None,
                 "⭐ P5 — 1280x720 dopo ADATTA_TELA + TELA(ADATTATA, 1280, "
                 "720): la tela in vigore non e' piu' quella di SESSIONE, e il "
                 "fotogramma e' conforme"))

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

    # =======================================================================
    # ⭐⛔ 22-37 — LA TELA E LA VISTA, sottofase 6.6, 16 agosto 2026
    #
    # ⛔ `fasi/06-la-tela-e-la-vista.md` §0 punto 6: *«nessuno dei due manda un
    #    `ADATTA_TELA`»*.  ⇒ `ADATTA_TELA` (0x000B), `TELA` (0x000E) e `VISTA`
    #    (0x0008) erano nel protocollo da una settimana e **nessuna
    #    registrazione li portava**: le sette regole di §7.1 sulla tela erano
    #    regole che nessun ingresso faceva scattare.
    #
    # ⛔ E anche qui **due per regola**: quella che la viola e quella che la
    #    rispetta.  Le positive non sono di cortesia — un arbitro severo sulla
    #    tela e' esattamente cio' che ucciderebbe le sessioni sane, ed e' il
    #    difetto che §7.1 ha gia' fatto una volta (rilievo R1.17, la vista coi
    #    limiti della tela).
    #
    # Gli scostamenti dentro il corpo di `TELA`, contati dall'inizio del
    # messaggio: 6 = esito · 7 = motivo · 8 = tela_larghezza · 12 = tela_altezza.
    # Dentro `VISTA` e `ADATTA_TELA`: 6 = larghezza · 10 = altezza.
    # =======================================================================
    def tela(esito, motivo, lar, alt):
        return msg(0x000E, struct.pack("!BBII", esito, motivo, lar, alt))

    def adatta(lar, alt):
        return msg(0x000B, struct.pack("!II", lar, alt))

    def vista(lar, alt):
        return msg(0x0008, struct.pack("!II", lar, alt))

    # ── 22. ⛔ T1 §7.1 — un `TELA` NON SOLLECITATO ──────────────────────────
    #    ⚠ E' il caso che la ⏳ riga mancante di §7.1 descrive per esteso: *«che
    #      cosa fa il server quando il palco cambia misura senza che nessun
    #      `ADATTA_TELA` gliel'abbia chiesto»*.  §6.2 risponde per lui: il
    #      client non ha nessun modo di accettarlo, e **chiude una sessione
    #      sana**.  Finche' quella riga non c'e', questo e' il verdetto.
    r = conforme()
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("22-tela-non-sollecitata", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 0)),
                 "⛔ T1 — TELA(ADATTATA) senza nessuna ADATTA_TELA: il server "
                 "cambia la tela da se'"))

    # ── 23. ⛔ T2 §6.2 — DUE `TELA` per una sola `ADATTA_TELA` ──────────────
    #    ⛔ Il byte accusato e' quello del **secondo**: il primo e' giusto, e
    #       accusare lui manderebbe a cercare il difetto in una risposta
    #       corretta.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("23-tela-doppia", r, 1,
                 ("RCP.md §6.2", r.scostamento(8, 0)),
                 "⛔ T2 — due TELA per una sola ADATTA_TELA: da qui in poi "
                 "l'n-esimo TELA risponde all'(n+1)-esima richiesta"))

    # ── 24. ⛔ T3 §7.1 — `ADATTA_TELA` SENZA RISPOSTA, e poi il CONGEDO ─────
    #    ⛔ Il byte accusato e' quello della RICHIESTA, non del congedo: e' la
    #       richiesta a essere rimasta appesa, ed e' li' che chi diagnostica
    #       deve guardare.  ⚠ *«Il sintomo e' "l'applicazione si e' piantata"»*.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, msg(0x000C, struct.pack("!B", 0x01) + s("")))
    casi.append(("24-adatta-senza-risposta", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 0)),
                 "⛔ T3 — ADATTA_TELA, poi un CONGEDO e nessun TELA: il server "
                 "aveva TELA(RIFIUTATA, NON_ORA) anche mentre chiudeva"))

    # ── 24-bis. ⛔ T3 per l'altra via: il canale di controllo si CHIUDE ─────
    #    Nessun congedo, ma un FIN dal lato del server: la risposta non puo'
    #    piu' arrivare, e il fatto e' nei byte — e' il campo `fine` di §11.1.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, b"", fine=FIN)
    casi.append(("24bis-adatta-senza-risposta-fin", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 0)),
                 "⛔ T3 — ADATTA_TELA e poi il server chiude lo stream di "
                 "controllo con FIN senza rispondere"))

    # ── 24-ter. ⭐ LA STESSA SCENA CHE **NON** SI ACCUSA ────────────────────
    #    ⛔ Identica alla 24 meno la fine: lo stream continua, nessun congedo.
    #       Il TELA puo' ancora arrivare, e la registrazione e' solo **finita
    #       prima**.  ⚠ Ogni traccia di `01-b3-cliente.py` e' di questa specie —
    #       il cliente si stacca da se' — e un arbitro che accusasse qui
    #       darebbe un **falso rosso perpetuo** su ogni giro di B3.
    #    ⭐ E' la registrazione che tiene onesto T3, come la 17bis tiene onesto
    #       P5: senza di lei, «accusa il silenzio» e «accusa la fine del file»
    #       hanno lo stesso colore.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    casi.append(("24ter-adatta-in-volo-traccia-viva", r, 0, None,
                 "⭐ T3 — una ADATTA_TELA in volo con la sessione ancora viva: "
                 "non si accusa, si DICHIARA che non si giudica"))

    # ── 25. ⛔ §7.1 — l'esito fuori dai due valori dichiarati ───────────────
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(3, 0, 1280, 720))
    casi.append(("25-tela-esito-fuori", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 6)),
                 "⛔ TELA con esito 3: §7.1 ne definisce due, 1 = ADATTATA e "
                 "2 = RIFIUTATA"))

    # ── 26. ⛔ §7.1 — il motivo fuori dai tre dichiarati ────────────────────
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(2, 4, 1920, 1080))
    casi.append(("26-tela-motivo-fuori", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 7)),
                 "⛔ TELA(RIFIUTATA) con motivo 4: §7.1 ne definisce tre — "
                 "COMPOSITORE_INCAPACE, MISURA_FUORI_LIMITI, NON_ORA"))

    # ── 27. ⛔ T5 §7.1 — il RIFIUTO che CAMBIA la tela ──────────────────────
    #    ⛔ Il piu' insidioso dei sette: il messaggio e' ben formato, l'esito e
    #       il motivo sono leciti, e **ogni campo preso da solo e' valido**.  E'
    #       il rapporto fra i campi a mentire — il server dice «non ho
    #       adattato» e dichiara in vigore una tela che non era in vigore.  ⚠ E
    #       §6.2 ci lega la misura di ogni fotogramma che segue: da qui in poi
    #       il client butta i fotogrammi buoni.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(2, 3, 1280, 720))
    casi.append(("27-tela-rifiutata-cambia", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 8)),
                 "⛔ T5 — TELA(RIFIUTATA, NON_ORA) che dichiara in vigore "
                 "1280x720 mentre la tela era 1920x1080"))

    # ── 28. ⛔ T6 §4.5 — la tela CONCESSA con un lato DISPARI ───────────────
    #    ⚠ E la RICHIESTA e' pari e dentro i limiti — 1280x720 — di proposito:
    #      se anche la richiesta fosse dispari, il byte accusato sarebbe giusto
    #      per due ragioni insieme, e non si saprebbe quale delle due regge.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1281, 720))
    casi.append(("28-tela-concessa-dispari", r, 1,
                 ("RCP.md §4.5", r.scostamento(7, 8)),
                 "⛔ T6 — TELA(ADATTATA) concede 1281x720: il lato dispari lo "
                 "arrotonda il codificatore, in silenzio"))

    # ── 29. ⛔ T6 §4.5 — la tela CONCESSA fuori dai limiti ──────────────────
    #    ⛔ E l'ALTEZZA, non la larghezza: se l'arbitro accusasse sempre il
    #       primo campo il byte sarebbe giusto per caso.
    r = conforme()
    r.blocco(CLIENT, adatta(1920, 240))     # ⚠ la richiesta e' dentro i limiti
    r.blocco(SERVER, tela(1, 0, 1920, 200))
    casi.append(("29-tela-concessa-fuori-limiti", r, 1,
                 ("RCP.md §4.5", r.scostamento(7, 12)),
                 "⛔ T6 — TELA(ADATTATA) concede un'altezza di 200, sotto il "
                 "minimo di 240"))

    # ── 30. ⛔ V3 §7.1 — la `VISTA` che CAMBIA LA TELA ──────────────────────
    #    *«VISTA NON DEVE far cambiare la tela … l'unico messaggio che cambia
    #    la tela e' ADATTA_TELA»*.  Sul filo si presenta cosi': il client
    #    ridimensiona la finestra, manda `VISTA`, e il server **adatta il
    #    desktop** — che e' precisamente il comportamento che `?adatta=segui`
    #    deve poter tenere SPENTO.
    r = conforme()
    r.blocco(CLIENT, vista(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("30-vista-cambia-tela", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 0)),
                 "⛔ V3 — il server risponde a una VISTA con un TELA: la vista "
                 "non deve far cambiare la tela"))

    # ── 31. ⭐ V2 §7.1 — la vista 1x1 E' LEGALE, e non si accusa ────────────
    #    ⛔ *«Qualunque misura da 1x1 in su e' legale, dispari compresa»*, e i
    #       limiti della tela alla vista **non si applicano**: e' il rilievo
    #       R1.17, e questa registrazione esiste perche' non rientri dal lato
    #       dell'arbitro.  ⚠ Con la riga vecchia il client aveva tre scelte,
    #       tutte cattive — e una era «farsi chiudere la sessione perche' ha
    #       ridimensionato una finestra».
    r = conforme()
    r.blocco(CLIENT, vista(1, 1))
    r.blocco(CLIENT, vista(393, 851))       # un telefono, lati dispari
    r.blocco(CLIENT, vista(300, 800))       # sotto il minimo della tela
    r.blocco(CLIENT, vista(9000, 5000))     # oltre il massimo della tela
    casi.append(("31-vista-legale", r, 0, None,
                 "⭐ V2 — 1x1, 393x851 dispari, 300x800 sotto il minimo della "
                 "tela e 9000x5000 oltre il massimo: tutte legali (§7.1, "
                 "R1.17)"))

    # ── 32. ⛔ V1 §7.1 — la vista con un lato ZERO ──────────────────────────
    #    «Da 1x1 in su»: lo zero non e' «in su», e §6.0 vieta i valori
    #    sentinella impliciti — quindi non e' nemmeno «assente».
    r = conforme()
    r.blocco(CLIENT, vista(1280, 0))
    casi.append(("32-vista-zero", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 10)),
                 "⛔ V1 — VISTA con altezza 0: §7.1 dice «da 1x1 in su»"))

    # ── 33. ⭐ §7.1 — l'`ADATTA_TELA` FUORI LIMITI e' LECITA ────────────────
    #    ⛔ E' il controllo di non-severita' piu' importante della serie: §7.1
    #       dedica alla misura impossibile un motivo di rifiuto per nome —
    #       `MISURA_FUORI_LIMITI` — e un motivo esiste per essere raggiunto.  Un
    #       arbitro che bocciasse la richiesta renderebbe **irraggiungibile** un
    #       ramo che la specifica nomina, e nessun banco potrebbe piu'
    #       esercitarlo.
    #    ⚠ E il rifiuto lascia la tela dov'era: 1920x1080, invariata.
    r = conforme()
    r.blocco(CLIENT, adatta(8000, 4320))
    r.blocco(SERVER, tela(2, 2, 1920, 1080))
    casi.append(("33-adatta-fuori-limiti-rifiutata", r, 0, None,
                 "⭐ ADATTA_TELA(8000x4320) — fuori dai limiti di §4.5 — e "
                 "TELA(RIFIUTATA, MISURA_FUORI_LIMITI) con la tela invariata: "
                 "e' la strada che §7.1 prevede"))

    # ── 34. ⭐ IL GIRO PIENO DELLA TELA, che deve uscire CONFORME ───────────
    #    ⛔ Senza questa, «sedici su sedici» e' compatibile con un arbitro che
    #       boccia **ogni** ADATTA_TELA — e sarebbe verde su tutte le
    #       violazioni.  Qui dentro: la richiesta all'attacco, la risposta, il
    #       fotogramma alla misura NUOVA (§6.2), una vista che cambia da sola,
    #       un secondo adattamento durante la sessione, e un rifiuto onesto.
    r = conforme()
    r.blocco(CLIENT, adatta(1264, 800))
    r.blocco(SERVER, tela(1, 0, 1264, 800))
    r.blocco(CLIENT, vista(1264, 800))
    r = con_video((SERVER, intestazione(lar=1264, alt=800) + b"\x00" * 256, 7,
                   FIN), base=r)
    r.blocco(CLIENT, adatta(1920, 1080))
    r.blocco(SERVER, tela(2, 1, 1264, 800))   # COMPOSITORE_INCAPACE
    r.blocco(CLIENT, vista(640, 401))
    casi.append(("34-tela-giro-pieno", r, 0, None,
                 "⭐ il giro pieno: ADATTA_TELA → TELA(ADATTATA, 1264x800) → un "
                 "fotogramma alla misura nuova → una seconda richiesta "
                 "rifiutata con COMPOSITORE_INCAPACE, tela invariata"))

    # ── 35. ⭐ §6.2 — DUE RICHIESTE IN VOLO INSIEME, e il conto regge ───────
    #    *«Chi trascina una finestra ne manda due senza che il conto si
    #    perda»*.  ⛔ Le due risposte arrivano in ordine, e la seconda dichiara
    #    la tela finale: un arbitro che appaiasse per MISURA invece che per
    #    ORDINE fallirebbe qui, perche' la prima risposta concede una misura
    #    che il client non ha mai chiesto (§4.5 lo permette).
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(CLIENT, adatta(1600, 900))
    r.blocco(SERVER, tela(1, 0, 1264, 800))   # ⚠ concessa DIVERSA dalla chiesta
    r.blocco(SERVER, tela(1, 0, 1600, 900))
    casi.append(("35-due-richieste-in-volo", r, 0, None,
                 "⭐ due ADATTA_TELA in volo insieme e due TELA in ordine, con "
                 "la prima che concede una misura mai chiesta (§4.5)"))

    # ── 36. ⛔ §4 — `ADATTA_TELA` PRIMA di `SESSIONE` ───────────────────────
    #    Non e' una regola della tela: e' la stretta di mano.  Sta qui perche'
    #    un arbitro che imparasse la tela mettendo `ADATTA_TELA` fuori dalla
    #    macchina degli stati aprirebbe questo buco senza accorgersene.
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(CLIENT, adatta(1280, 720))
    casi.append(("36-adatta-prima-di-sessione", r, 1,
                 ("RCP.md §4 (l'ordine della stretta di mano)",
                  r.scostamento(2, 0)),
                 "⛔ ADATTA_TELA prima che la sessione esista"))

    # ── 37. ⭐ §7.6 e §8.2 — `TERMINA_SESSIONE` e il `CONGEDO(0x10)` ────────
    #    ⛔ Due tipi entrati il **15 agosto 2026** che questo arbitro non
    #       conosceva: `TERMINA_SESSIONE` (0x0011) sarebbe stato accusato come
    #       «tipo sconosciuto» e il motivo `0x10 SESSIONE_TERMINATA` come
    #       «motivo sconosciuto».  ⚠ Cioe' l'arbitro dava rosso al server che fa
    #       l'unica cosa che §7.6 gli permette, sul messaggio con cui l'utente
    #       esce dal desktop.  Questa registrazione tiene chiusa quella porta.
    r = conforme()
    r.blocco(CLIENT, msg(0x0011, b""))
    r.blocco(SERVER, msg(0x000C, struct.pack("!B", 0x10) + s("uscita")),
             fine=FIN)
    casi.append(("37-termina-sessione", r, 0, None,
                 "⭐ TERMINA_SESSIONE (0x0011) e CONGEDO(0x10 "
                 "SESSIONE_TERMINATA): i due tipi del 15 agosto"))

    # =======================================================================
    # ⭐⛔ 38-45 — LE OTTO REGISTRAZIONI CHE NON HO SCRITTO IO
    #
    # ⛔ La sera del 16 agosto 2026, subito dopo che le sedici qui sopra
    #    uscivano **41 su 41 al primo giro**, un agente e' stato mandato a
    #    **smentire** questo arbitro leggendo `RCP.md` e non il validatore.  Ha
    #    costruito 36 controesempi e ne ha trovati **14 divergenti**.
    #
    # ⚠ «41 su 41 al primo giro» era vero e non voleva dire quel che sembrava:
    #   le registrazioni e le regole erano state scritte **nella stessa ora,
    #   dalla stessa mano**, ed e' lo stato che `README.md` chiama «due
    #   programmi che vanno d'accordo e non confermano niente».  ⛔ Il numero
    #   che conta non e' quante ne passa un banco scritto da chi ha scritto
    #   l'arbitro: e' quante ne passa **dopo** che qualcuno ha provato a
    #   romperlo.
    #
    # ⭐ Queste otto sono quelle divergenze, portate qui perche' non si
    #    riaprano.  Le altre — quelle fuori dal mandato della tela — sono
    #    dichiarate nel rapporto della sottofase e restano `[?]`.
    # =======================================================================

    # ── 38. ⛔ §4.5 — `SESSIONE` oltre `video.misura_massima` ───────────────
    #    §4.5 mette nella stessa frase i limiti, la parita' **e** questo tetto.
    #    L'arbitro ne applicava due terzi.  ⚠ E il tetto non e' una preferenza:
    #    il client lo dichiara perche' oltre quello **non decodifica**.
    #    Il `CIAO` di `conforme()` dichiara 3840x2160.
    r = conforme()
    r.blocchi[5] = (SERVER, 0x00, 0,
                    msg(0x0007, struct.pack("!B", 1)
                        + struct.pack("!II", 7680, 4320) + s("gnome")),
                    [], CONTINUA, 0)
    casi.append(("38-sessione-oltre-misura-massima", r, 1,
                 ("RCP.md §4.5", r.scostamento(5, 7)),
                 "⛔ SESSIONE concede 7680x4320 a un client che ha dichiarato "
                 "video.misura_massima = 3840x2160"))

    # ── 39. ⛔ §4.5 — e la stessa frase vale per la tela concessa da `TELA` ──
    #    ⚠ Se non valesse, `ADATTA_TELA` sarebbe la porta da cui si supera un
    #      tetto che il client ha dichiarato per non restare al buio.
    r = conforme()
    r.blocco(CLIENT, adatta(7680, 4320))
    r.blocco(SERVER, tela(1, 0, 7680, 4320))
    casi.append(("39-concessa-oltre-misura-massima", r, 1,
                 ("RCP.md §4.5", r.scostamento(7, 8)),
                 "⛔ TELA(ADATTATA) concede 7680x4320 oltre la "
                 "video.misura_massima dichiarata in CIAO"))

    # ── 40. ⛔ §8.1 — il `TELA` mandato DOPO il proprio `CONGEDO` ───────────
    #    ⭐ E' la registrazione che ha sciolto una **contraddizione
    #       dell'arbitro con se' stesso**: accusava `ADATTA_TELA · CONGEDO`
    #       (nessuna risposta possibile) e assolveva `ADATTA_TELA · CONGEDO ·
    #       TELA`, cioe' diceva insieme che la risposta non poteva piu' arrivare
    #       **e** che era arrivata.  §8.1 sceglie: il congedo va *«prima di
    #       chiudere la sessione»*, quindi e' l'ultimo messaggio di quel lato.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, msg(0x000C, struct.pack("!B", 0x01) + s("")))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("40-tela-dopo-il-congedo", r, 1,
                 ("RCP.md §4 (l'ordine della stretta di mano)",
                  r.scostamento(8, 0)),
                 "⛔ il server manda un TELA dopo il proprio CONGEDO: §8.1 lo "
                 "vuole «prima di chiudere la sessione»"))

    # ── 41. ⛔ §11.1 — il `canale` DICHIARATO che non e' il byte alto del tipo
    #    ⭐ Bastavano due byte per rendere invisibile una violazione: gli stessi
    #       byte della 22 — un `TELA` non sollecitato — col blocco dichiarato
    #       `canale = 0x02`, uscivano ⭐ **conforme**.  §11.1 non descrive quel
    #       campo, lo **definisce**: *«canale: il byte alto di tipo»*.
    #    ⚠ E' la stessa forma della `11-quanti-sotto-dichiarato`: filo che
    #      sparisce dal giudizio con un file valido per ogni altra riga.
    r = conforme()
    r.blocco(SERVER, tela(1, 0, 1280, 720), canale=0x02, stream=9)
    casi.append(("41-canale-dichiarato-falso", r, 2, None,
                 "⛔ un TELA non sollecitato dentro un blocco che si dichiara "
                 "«appunti»: il giudizio lo saltava"))

    # ── 42. ⛔ §11.1 — un intervallo oscurato sopra un campo NUMERICO ───────
    #    ⭐ **Difetto nato e morto lo stesso giorno**: la regola nuova T6 leggeva
    #       dentro l'intervallo e accusava *«concede tela_larghezza =
    #       707406378»* — e 707406378 e' `0x2A2A2A2A`, il riempimento di §11.1
    #       letto come una misura.  ⛔ Un rosso di protocollo su byte che il
    #       formato dichiara di aver sostituito manda a cercare un difetto del
    #       server dentro una scelta del registratore.
    r = conforme()
    corpo_t = struct.pack("!BBII", 1, 0, 1280, 720)
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER,
             msg(0x000E, corpo_t[:2] + bytes([RIEMPIMENTO]) * 4 + corpo_t[6:]),
             oscurati=[(6 + 2, 4, hashlib.sha256(corpo_t[2:6]).digest())])
    casi.append(("42-oscurato-su-un-numero", r, 2, None,
                 "⛔ un intervallo oscurato sopra tela_larghezza di TELA: §11.1 "
                 "esiste per la parola d'ordine, e quel campo non si giudica"))

    # ── 43. ⭐ §6.2 — IL FOTOGRAMMA ALLA MISURA NUOVA **PRIMA** DEL SUO `TELA`
    #
    #    ⛔ *«Un fotogramma alla misura NUOVA puo' arrivare PRIMA del `TELA` che
    #       la concede … il client NON DEVE chiudere: trattiene il
    #       fotogramma»*, e la condizione e' *«finche' resta una `ADATTA_TELA`
    #       che il client ha spedito»*.
    #    ⭐ Fino al 16 agosto 2026 questa registrazione usciva **1**: B4
    #       costruiva il contesto del giudice **senza dichiarare nessuna
    #       richiesta in volo**, e la grazia di §6.2 — scritta, importata, e
    #       che nomina `01-b4-validatore.py` per esteso — era irraggiungibile.
    #       ⇒ L'arbitro chiudeva *«una sessione in cui nessuno ha sbagliato»*.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 128,
             canale=VIDEO, stream=7, fine=FIN)
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("43-fotogramma-prima-del-tela", r, 0, None,
                 "⭐ §6.2 — 1280x720 mentre una ADATTA_TELA e' senza risposta: "
                 "si trattiene, non si chiude"))

    # ── 44. ⭐ §6.2 / D14 — IL FOTOGRAMMA ALLA MISURA **VECCHIA** DOPO IL `TELA`
    #    L'altro verso della stessa scena: il `TELA(ADATTATA)` e' passato e i
    #    fotogrammi gia' in volo portano **legittimamente** la misura di prima.
    #    ⛔ Usciva 1 per un secondo motivo, diverso dal 43: B4 chiamava
    #       `adatta_tela()` su un contesto **gia'** alla misura nuova, e il
    #       giudice ha un ritorno anticipato quando la misura non cambia — per
    #       lui non era successo niente, e la coda non si apriva.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    r.blocco(SERVER, intestazione(lar=1920, alt=1080) + b"\x00" * 128,
             canale=VIDEO, stream=7, fine=FIN)
    casi.append(("44-fotogramma-vecchio-dopo-il-tela", r, 0, None,
                 "⭐ §6.2 D14 — 1920x1080 subito dopo TELA(ADATTATA, 1280x720): "
                 "era gia' in volo, e si dipinge riscalato"))

    # ── 45. ⭐⛔ LA CONTRADDIZIONE FRA §7.1 E §4.2, DICHIARATA E NON SCELTA ──
    #    Il client manda `ADATTA_TELA` e **chiude** il canale.  §7.1 impone al
    #    server di rispondere; §4.2 gli vieta di spedire dopo un FIN *«da una
    #    qualunque delle due parti»*.  ⇒ I due `DEVE` si escludono, e non e'
    #    un caso di laboratorio: e' l'utente che ridimensiona la finestra e
    #    chiude la scheda nello stesso gesto.
    #    ⛔ Esce **0** perche' non c'e' niente da accusare — ma il verdetto
    #       **nomina** la contraddizione, invece di supplirla in silenzio.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720), fine=FIN)
    casi.append(("45-adatta-poi-fin-del-client", r, 0, None,
                 "⭐ ADATTA_TELA e poi il FIN del CLIENT: §7.1 e §4.2 si "
                 "contraddicono, e l'arbitro lo dice invece di scegliere"))

    # =======================================================================
    # ⭐⛔ 46-52 — QUEL CHE `RCPREG 0x00 0x03` RENDE ARBITRABILE — 21 agosto 2026
    #
    # Il campo `istante_ms` non e' stato aggiunto per completezza: e' stato
    # aggiunto per DUE regole che nessuna registrazione poteva far scattare —
    # il secondo di grazia di §7.1 e T4.  ⛔ E se non ci fossero questi casi,
    # il campo sarebbe un costo pagato e mai riscosso.
    # =======================================================================

    # ── 46. ⛔ il formato del 12 agosto, `0x00 0x02`: si RIFIUTA ────────────
    #    ⚠ Non basta rifiutare `0x01`: quello e' il caso 21, e la riga che
    #      rifiuta `0x02` e' un'ALTRA riga.  Senza questo caso si potrebbe
    #      cancellarla e il banco resterebbe verde — ed e' esattamente la
    #      forma con cui il difetto del 12 agosto e' vissuto quattro giorni.
    r = conforme()
    r.magia = MAGIA_V2
    casi.append(("46-formato-del-12-agosto", r, 2, None,
                 "⛔ «RCPREG 0x00 0x02», conforme in tutto il resto: il blocco "
                 "misura 17 byte invece di 21 e si RIFIUTA — letto di traverso "
                 "ogni blocco scivolerebbe di quattro byte"))

    # ── 47. ⛔ `orologio` non dichiarato ────────────────────────────────────
    r = conforme()
    r.orologio_falso = 0
    casi.append(("47-orologio-non-dichiarato", r, 2, None,
                 "⛔ `orologio` = 0: §11.1 ne definisce due (1 client, 2 "
                 "server), e senza sapere DI CHI sono i tempi la regola del "
                 "secondo di grazia non e' giudicabile affatto"))

    # ── 48. ⛔ l'orologio che torna indietro ────────────────────────────────
    r = conforme()
    r.blocchi[3] = r.blocchi[3][:6] + (5000,)
    r.blocchi[4] = r.blocchi[4][:6] + (200,)
    casi.append(("48-istante-che-torna-indietro", r, 2, None,
                 "⛔ un `istante_ms` piu' piccolo del blocco precedente: §11.1 "
                 "vuole un orologio MONOTONO, e con `time.time()` al posto di "
                 "`time.monotonic()` un aggiustamento di NTP fa arrivare un "
                 "PUNTATORE «prima» del TELA che lo precede sul filo"))

    # ── 49-50. ⭐⛔ IL SECONDO DI GRAZIA DI §7.1, i due versi ────────────────
    def con_grazia(dt_ms):
        """La tela scende a 1280x720, e poi un PUNTATORE valido sulla VECCHIA.

        ⛔ (1900,1000) sta dentro 1920x1080 e fuori da 1280x720: e' esattamente
           la coordinata che §7.1 fa saturare **per un secondo** e rifiutare
           dopo.
        """
        r = conforme()
        r.blocco(CLIENT, adatta(1280, 720), istante=500)
        r.blocco(SERVER, tela(1, 0, 1280, 720), istante=1000)
        corpo_p = struct.pack("!IQII", 1, 0, 1900, 1000)
        r.blocco(CLIENT, msg(0x0101, corpo_p), canale=0x01, stream=9,
                 istante=1000 + dt_ms)
        # ⛔ E il server DEVE aver chiuso: qui invece continua a servire, e la
        #    prova e' che risponde a un'altra richiesta.  ⚠ Senza questo blocco
        #    la registrazione finirebbe «a sessione viva» e l'arbitro direbbe
        #    — giustamente — che non si giudica.
        r.blocco(CLIENT, adatta(1600, 900), istante=1000 + dt_ms + 100)
        r.blocco(SERVER, tela(1, 0, 1600, 900), istante=1000 + dt_ms + 150)
        return r

    r = con_grazia(1500)
    casi.append(("49-grazia-scaduta", r, 1,
                 ("RCP.md §7.1", r.scostamento(8, 0)),
                 "⛔ un PUNTATORE sulla tela VECCHIA 1500 ms dopo il "
                 "TELA(ADATTATA) — oltre il secondo di §7.1 — e il server che "
                 "continua a servire invece di chiudere.  ⭐ E' la [?] che "
                 "`istante_ms` esiste per chiudere"))

    r = con_grazia(800)
    casi.append(("50-grazia-dentro-il-secondo", r, 0, None,
                 "⭐ lo stesso filo a 800 ms: l'arbitro NON accusa, e ⛔ DICE "
                 "che non e' giudicabile — i tempi sono del client, e "
                 "l'intervallo vero del server e' piu' lungo di questo"))

    # ── 51-52. ⭐⛔ T4 — «CONFORME NON E' FUNZIONA» ──────────────────────────
    def con_t4(misura_fotogrammi):
        r = conforme()
        r.blocco(CLIENT, adatta(1264, 800), istante=50)
        r.blocco(SERVER, tela(1, 0, 1264, 800), istante=100)
        for i, (l, a, ist, sid) in enumerate(misura_fotogrammi):
            r.blocco(SERVER, intestazione(lar=l, alt=a, num=i + 1) + b"\x00" * 64,
                     canale=VIDEO, stream=sid, fine=FIN, istante=ist)
        return r

    r = con_t4([(1920, 1080, 500, 7), (1920, 1080, 2000, 11),
                (1920, 1080, 4000, 15)])
    # ⛔ Il byte accusato e' `tela_larghezza` del `TELA(ADATTATA)`, cioe' 8 byte
    #    dentro il messaggio (6 d'inquadratura + esito + motivo): e' il campo che
    #    dichiara la misura che il palco non ha mai avuto.
    casi.append(("51-t4-tela-finta", r, 1, ("RCP.md §7.1", r.scostamento(7, 8)),
                 "⛔⛔ T4 — il server risponde TELA(ADATTATA, 1264x800) e per "
                 "quattro secondi manda fotogrammi 1920x1080: la tela l'ha "
                 "detta e il palco NON l'ha toccato.  ⭐ E' la crepa dichiarata "
                 "di tutta la 6.6, e prima di `istante_ms` nessun arbitro la "
                 "vedeva"))

    # ⛔ E IL SECONDO FOTOGRAMMA ARRIVA A 3500 ms, NON A 900 — 21 agosto 2026,
    #    e a dirlo e' stata la mutazione `t4-conta-invece-di-cronometrare`.
    #
    #    Con la coppia (500, 900) la finestra e' 800 ms, cioe' SOTTO il tetto:
    #    un T4 che guardasse il PRIMO fotogramma invece della finestra usciva
    #    lo stesso «non giudicabile», e questa registrazione **non distingueva
    #    il conteggio dal cronometro** — cioe' non provava la cosa che la sua
    #    stessa riga dichiara di provare.  ⚠ E' la terza volta stasera che un
    #    guasto scritto apposta trova un caso che si credeva.
    r = con_t4([(1920, 1080, 500, 7), (1264, 800, 3500, 11)])
    casi.append(("52-t4-il-palco-e-stato-toccato", r, 0, None,
                 "⭐ lo stesso filo, ma il secondo fotogramma dichiara 1264x800 "
                 "OLTRE il tetto: il palco e' stato toccato davvero.  ⛔ E il "
                 "PRIMO resta 1920x1080 ed e' LEGALE — §6.2, il fotogramma gia' "
                 "in volo — che e' la ragione per cui T4 vuole un tetto in "
                 "TEMPO e non un conteggio"))

    # ── 53. ⭐⛔ DUE FOTOGRAMMI DOPO LO STESSO `TELA` — la scena che
    #        l'arbitro dichiarava NON CONFORME fino al 21 agosto 2026.
    #
    #    ⛔ E' la scena piu' banale che esista: la tela cambia, arriva la
    #       chiave alla misura nuova (§5.2 pagata), arriva il delta dopo.
    #    ⚠ Nessuna registrazione del deposito portava DUE flussi video dopo lo
    #      stesso `TELA`, e il cliente di prova non registrava il video: ⇒ il
    #      difetto ha aspettato il primo giro vero col video dentro, e allora
    #      ha accusato **il prodotto** di una cosa che il prodotto faceva bene.
    r = conforme()
    r.blocco(CLIENT, adatta(1264, 800), istante=50)
    r.blocco(SERVER, tela(1, 0, 1264, 800), istante=100)
    r.blocco(SERVER, intestazione(lar=1264, alt=800, num=1) + b"\x00" * 64,
             canale=VIDEO, stream=7, fine=FIN, istante=200)
    r.blocco(SERVER, intestazione(tipo=DELTA, lar=1264, alt=800, num=2)
             + b"\x00" * 64, canale=VIDEO, stream=11, fine=FIN, istante=300)
    casi.append(("53-due-fotogrammi-dopo-il-tela", r, 0, None,
                 "⭐ TELA(ADATTATA, 1264x800), poi la CHIAVE alla misura nuova "
                 "e poi un DELTA: §5.2 e' pagata dalla chiave, e il delta e' "
                 "legale.  ⛔ L'arbitro rigiocava il cambio di tela a OGNI "
                 "flusso e accusava il secondo — avrebbe dichiarato non "
                 "conforme ogni sessione vera"))

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
