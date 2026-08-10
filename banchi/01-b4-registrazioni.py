#!/usr/bin/env python3
"""01-b4-registrazioni.py — le sette registrazioni di B4, e che cosa il validatore DEVE dire.

    python3 01-b4-registrazioni.py [cartella]     predefinita: ./b4-registrazioni

---------------------------------------------------------------------------
⛔ SEI GUASTE E UNA CONFORME, E LA SETTIMA E' QUELLA CHE CONTA

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
        out = bytearray(MAGIA + struct.pack("!II", len(self.blocchi), 0))
        for verso, canale, stream, carico, osc in self.blocchi:
            out += struct.pack("!BBQIH", verso, canale, stream, len(carico), len(osc))
            for ini, qua, imp in osc:
                out += struct.pack("!II", ini, qua) + imp
            out += carico
        return bytes(out)


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
    """Le sette, ciascuna col suo atteso."""
    casi = []

    # ── 7. la conforme — si costruisce per prima perche' e' la base delle altre
    casi.append(("conforme", conforme(), None,
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
    casi.append(("1-lunghezza-incoerente", r,
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
    casi.append(("2-utf8-non-valido", r,
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
    casi.append(("3-capacita-ripetuta", r,
                 ("RCP.md §4.3", r.scostamento(0, 6 + scost)),
                 "video.codec compare due volte"))

    # ── 4. byte alto fuori dai cinque canali (§2.5) ─────────────────────────
    #    Un tipo 0x0701: il byte alto vale 7, e i canali sono cinque.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0701, b""), [])
    casi.append(("4-canale-sconosciuto", r,
                 ("RCP.md §2.5", r.scostamento(3, 0)),
                 "un tipo il cui byte alto non e' uno dei cinque canali"))

    # ── 5. messaggio nello stato sbagliato (§4) ─────────────────────────────
    #    ATTACCA prima di CREDENZIALI.
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(CLIENT, ATTACCA)
    casi.append(("5-stato-sbagliato", r,
                 ("RCP.md §4 (l'ordine della stretta di mano)", r.scostamento(2, 0)),
                 "ATTACCA prima di CREDENZIALI"))

    # ── 6. ⭐ corpo giusto ma ALLINEATO (§6.0) ───────────────────────────────
    #    `AMMESSO` ha corpo vuoto; qui ne dichiara quattro, di riempimento —
    #    esattamente quel che farebbe una struttura C allineata a 4.
    #    ⛔ E dopo c'e' un altro messaggio: un validatore che non conosce §6.0
    #       leggerebbe di traverso QUELLO, e darebbe rosso sul byte sbagliato.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0004, b"\x00\x00\x00\x00"), [])
    casi.append(("6-riempimento", r,
                 ("RCP.md §6.0", r.scostamento(3, 6)),
                 "AMMESSO con quattro byte di riempimento, e un messaggio dopo"))

    return casi


def main():
    dove = sys.argv[1] if len(sys.argv) > 1 else "b4-registrazioni"
    os.makedirs(dove, exist_ok=True)
    casi = costruisci()
    manifesto = []
    print(f"== le {len(casi)} registrazioni di B4  ->  {dove}/")
    for nome, r, atteso, che in casi:
        percorso = os.path.join(dove, f"{nome}.rcpreg")
        with open(percorso, "wb") as f:
            f.write(r.byte())
        manifesto.append({
            "file": f"{nome}.rcpreg",
            "che": che,
            "atteso": "conforme" if atteso is None else "non-conforme",
            "regola": None if atteso is None else atteso[0],
            "byte": None if atteso is None else atteso[1],
        })
        if atteso is None:
            print(f"   {nome:<24s} atteso: CONFORME          — {che}")
        else:
            print(f"   {nome:<24s} atteso: byte {atteso[1]:<5} {atteso[0]:<28s} — {che}")
    with open(os.path.join(dove, "manifesto.json"), "w") as f:
        json.dump(manifesto, f, indent=1, ensure_ascii=False)
    print(f"\n   il manifesto — cioe' l'ATTESO, scritto qui e non nella testa di")
    print(f"   chi guarda — sta in {dove}/manifesto.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
