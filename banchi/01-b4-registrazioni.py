#!/usr/bin/env python3
"""01-b4-registrazioni.py — le registrazioni di B4, e che cosa il validatore DEVE dire.

    python3 01-b4-registrazioni.py [cartella]     predefinita: ./b4-registrazioni

⛔ **Quante sono non sta scritto qui**: le costruisce `costruisci()`, le conta
   il programma e le stampa insieme al manifesto.  Un numero scritto a mano in
   un commento e' il numero che nessuno ricalcola.

---------------------------------------------------------------------------
⛔ UNA CONFORME, E LE ALTRE SONO I QUATTRO MODI DI NON ESSERLO

`fasi/01-filo-nudo.md` B4: senza la registrazione **conforme**, «6 su 6» e'
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
| `12-niente-da-giudicare` | l'**esito 3**: soli blocchi video, zero messaggi di controllo |

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

MAGIA = b"RCPREG\x00\x01"
RIEMPIMENTO = 0x2A
CLIENT, SERVER = 1, 2

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

    def blocco(self, verso, carico, canale=0x00, stream=0, oscurati=()):
        self.blocchi.append((verso, canale, stream, carico, list(oscurati)))
        return self

    def scostamento(self, indice_blocco, dentro):
        """Lo scostamento ASSOLUTO nel file del byte `dentro` del blocco dato."""
        p = 16
        for i, (_, _, _, carico, osc) in enumerate(self.blocchi):
            p += 16 + 40 * len(osc)
            if i == indice_blocco:
                return p + dentro
            p += len(carico)
        raise IndexError(indice_blocco)

    def byte(self):
        quanti = (len(self.blocchi) if self.dichiara_quanti is None
                  else self.dichiara_quanti)
        out = bytearray(MAGIA + struct.pack("!II", quanti, 0))
        for i, (verso, canale, stream, carico, osc) in enumerate(self.blocchi):
            lung = self.dichiarate.get(i, len(carico))
            out += struct.pack("!BBQIH", verso, canale, stream, lung, len(osc))
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
    r.blocchi[4] = (CLIENT, 0x00, 0, msg(0x0006, corpo_a[:-6], len(corpo_a) - 6), [])
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
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [])
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
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [])
    casi.append(("3-capacita-ripetuta", r, 1,
                 ("RCP.md §4.3", r.scostamento(0, 6 + scost)),
                 "video.codec compare due volte"))

    # ── 4. byte alto fuori dai cinque canali (§2.5) ─────────────────────────
    #    Un tipo 0x0701: il byte alto vale 7, e i canali sono cinque.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0701, b""), [])
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
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0004, b"\x00\x00\x00\x00"), [])
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
                        + s("it")), [])
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
    v, c, st, carico, osc = r.blocchi[2]
    ini_osc = osc[0][0]
    r.blocchi[2] = (v, c, st, carico,
                    [(ini_osc, 4, osc[0][2]), (ini_osc + 2, 4, osc[0][2])])
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
                        + s("it")), [])
    r.dichiara_quanti = 4
    casi.append(("11-quanti-sotto-dichiarato", r, 2, None,
                 "quanti_blocchi dice 4 e i blocchi sono 6: la violazione "
                 "sta nel quinto"))

    # ── 12. ⛔ NIENTE DA GIUDICARE — l'esito 3.  Un file ben formato in cui
    #         non c'e' un solo messaggio di controllo: «conforme» qui sarebbe
    #         vero e vuoto (LEZIONI.md §1.9).
    r = Registrazione()
    r.blocco(SERVER, b"\x03\x01" + b"\x00" * 26, canale=0x03, stream=7)
    casi.append(("12-niente-da-giudicare", r, 3, None,
                 "un solo blocco video: zero messaggi di controllo"))

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
