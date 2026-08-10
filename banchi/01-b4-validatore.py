#!/usr/bin/env python3
"""01-b4-validatore.py — il validatore del filo: quale byte non è conforme a RCP.md.

    python3 01-b4-validatore.py registrazione.rcpreg

    uscita 0  la registrazione è conforme
    uscita 1  non è conforme — e si dice QUALE byte e QUALE regola
    uscita 2  la REGISTRAZIONE è malformata (non è un giudizio sul filo)

---------------------------------------------------------------------------
⛔ CHE COS'E', E PERCHE' E' UN TERZO PROGRAMMA

`RCP.md` §11: *«client e server NON si collaudano l'uno contro l'altro: si
collaudano contro questo documento»*.  Questo e' **l'unico arbitro meccanico**
che avremo, e vale solo se e' scritto **leggendo la specifica** — non il
server, non la pagina.  Chi lo fa crescere non guardi il C: se lo guardasse ne
erediterebbe i fraintendimenti, e due programmi scritti dalla stessa mano che
vanno d'accordo non confermano niente (`README.md`).

---------------------------------------------------------------------------
⛔ TRE ESITI, NON DUE

  0  conforme
  1  NON conforme — con lo scostamento del byte e la regola violata
  2  ⛔ la REGISTRAZIONE e' malformata

Il terzo esiste perche' «il file e' rotto» e «il filo non era conforme» sono
due fatti diversi con due cure diverse, e un validatore che li confondesse
manderebbe a cercare un difetto di protocollo dentro un difetto di banco.

---------------------------------------------------------------------------
⛔ E RIFERISCE **QUALE** BYTE, NON SOLO CHE E' ROSSO

`fasi/01-filo-nudo.md` B4: sulla registrazione col riempimento, un validatore
che non conosce §6.0 non vede il byte in piu': legge di traverso il messaggio
SUCCESSIVO e dichiara non conforme quello.  **Rosso giusto, byte sbagliato** —
e su una traccia vera manda la diagnosi a leggere il messaggio sbagliato.
Per questo ogni verdetto porta due scostamenti (assoluto e dentro il blocco) e
la riga di RCP.md che regge il giudizio.
"""
import hashlib
import struct
import sys

MAGIA = b"RCPREG\x00\x01"
RIEMPIMENTO = 0x2A  # il byte degli intervalli oscurati (RCP.md §11.1)

# ---------------------------------------------------------------------------
# I tipi di messaggio del canale di controllo — RCP.md §7.1
CLIENT, SERVER = 1, 2
TIPI = {
    0x0001: ("CIAO", CLIENT),
    0x0002: ("ECCOMI", SERVER),
    0x0003: ("CREDENZIALI", CLIENT),
    0x0004: ("AMMESSO", SERVER),
    0x0005: ("RESPINTO", SERVER),
    0x0006: ("ATTACCA", CLIENT),
    0x0007: ("SESSIONE", SERVER),
    0x0008: ("VISTA", CLIENT),
    0x0009: ("DISPOSIZIONE", CLIENT),
    0x000A: ("CURSORE_FORMA", SERVER),
    0x000B: ("ADATTA_TELA", CLIENT),
    0x000C: ("CONGEDO", None),  # ↔ tutt'e due i versi
    0x000D: ("RICHIEDI_CHIAVE", CLIENT),
    0x000E: ("TELA", SERVER),
    0x000F: ("BANCO_MARCA", CLIENT),
    0x0010: ("BANCO_ESITO", SERVER),
}

CANALI = {0x00: "controllo", 0x01: "input", 0x02: "appunti",
          0x03: "video", 0x04: "audio"}

# I motivi di §8.2, per dirli per nome invece che per numero.
MOTIVI = {
    0x01: "CHIUSO_DALL_UTENTE", 0x02: "INATTIVITA", 0x03: "SESSIONE_ABBANDONATA",
    0x04: "SESSIONE_LOCALE_PREVALSA", 0x05: "GIA_ATTIVA_LOCALE", 0x06: "BUDGET_PIENO",
    0x07: "CREDENZIALI_ERRATE", 0x08: "TROPPI_TENTATIVI", 0x09: "NIENTE_IN_COMUNE",
    0x0A: "VERSIONE_INCOMPATIBILE", 0x0B: "ERRORE_PROTOCOLLO", 0x0C: "SERVER_IN_CHIUSURA",
    0x0D: "TEMPO_SCADUTO", 0x0E: "SESSIONE_NON_SERVIBILE", 0x0F: "GIA_ATTIVA_REMOTA",
}

# Le capacita' di §4.3, con il lato che le puo' dichiarare.
CAPACITA = {
    "video.codec": None, "video.profondita": None, "audio.codec": None,
    "appunti.testo": None,
    "video.livello": CLIENT, "video.misura_massima": CLIENT,
    "input.tocco": CLIENT, "client.nome": CLIENT,
    "banco.marca": SERVER,
}
# ⛔ Il trattino basso c'e' dal 10 agosto 2026: la prima esecuzione di
#    questo validatore ha trovato che §4.3 vietava un carattere che §4.3
#    stessa usa in `video.misura_massima`.  La cura sta in RCP.md.
NOME_LECITO = set("abcdefghijklmnopqrstuvwxyz0123456789._")

MASSIMO_MESSAGGIO = 1024 * 1024  # §6.1


class NonConforme(Exception):
    """Il filo non rispetta RCP.md.  Porta il byte e la regola."""

    def __init__(self, regola, dice, ass, rel):
        super().__init__(dice)
        self.regola, self.dice, self.ass, self.rel = regola, dice, ass, rel


class Malformata(Exception):
    """La REGISTRAZIONE e' rotta: non e' un giudizio sul filo."""


# ---------------------------------------------------------------------------
class Lettore:
    """Legge campi dal carico di un blocco, e sa dove NON deve guardare.

    ⛔ Ogni lettura controlla di avere i byte prima di prenderli: leggere
       oltre la fine e dire «non conforme» sarebbe dire la cosa giusta per il
       motivo sbagliato — il difetto sarebbe un troncamento, non un campo.
    """

    def __init__(self, carico, base_ass, oscurati):
        self.b, self.i, self.base = carico, 0, base_ass
        self.oscurati = oscurati  # [(inizio, quanti)]

    def ass(self, rel=None):
        return self.base + (self.i if rel is None else rel)

    def resta(self):
        return len(self.b) - self.i

    def _prendi(self, n, che):
        if self.resta() < n:
            raise NonConforme(
                "RCP.md §6.1",
                f"il corpo finisce prima di {che}: servivano {n} byte, ce ne sono {self.resta()}",
                self.ass(), self.i)
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def u8(self, che):
        return self._prendi(1, che)[0]

    def u16(self, che):
        return struct.unpack("!H", self._prendi(2, che))[0]

    def u32(self, che):
        return struct.unpack("!I", self._prendi(4, che))[0]

    def oscurato(self, inizio, quanti):
        """L'intervallo [inizio, inizio+quanti) tocca una zona oscurata?"""
        return any(not (inizio + quanti <= o or inizio >= o + q)
                   for o, q in self.oscurati)

    def stringa(self, che, minimo=0, massimo=None):
        """RCP.md §6.0: u16 lunghezza + quella lunghezza di UTF-8, senza terminatore."""
        inizio_campo = self.i
        n = self.u16(f"la lunghezza di {che}")
        dati_inizio = self.i
        b = self._prendi(n, che)
        if n < minimo:
            raise NonConforme("RCP.md §4.4",
                              f"{che} e' lunga {n} byte, il minimo e' {minimo}",
                              self.base + inizio_campo, inizio_campo)
        if massimo is not None and n > massimo:
            raise NonConforme("RCP.md §4.3",
                              f"{che} e' lunga {n} byte, il massimo e' {massimo}",
                              self.base + inizio_campo, inizio_campo)
        # ⛔ Dentro un intervallo oscurato NON si guarda: quei byte sono
        #    riempimento, e giudicarli sarebbe giudicare il banco.
        if self.oscurato(dati_inizio, n):
            return None
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError as e:
            raise NonConforme(
                "RCP.md §6.0",
                f"{che} non e' UTF-8 valido ({e.reason}) al byte {e.start} della stringa",
                self.base + dati_inizio + e.start, dati_inizio + e.start) from None

    def fine(self, nome):
        """⛔ Non un byte di piu': §6.0 vieta l'allineamento e il riempimento."""
        if self.resta():
            raise NonConforme(
                "RCP.md §6.0",
                f"{nome}: {self.resta()} byte in piu' dopo i campi previsti — "
                "nessun campo e' allineato e nessun riempimento e' ammesso",
                self.ass(), self.i)


# ---------------------------------------------------------------------------
def leggi_capacita(le, nome_messaggio, lato):
    """RCP.md §4.3 — l'elenco delle capacita', con tutte le sue regole."""
    quante = le.u16("il numero di capacita'")
    visti = {}
    for k in range(quante):
        inizio = le.i
        nome = le.stringa(f"il nome della capacita' {k}", minimo=1, massimo=64)
        valore = le.stringa(f"il valore della capacita' {k}", massimo=256)
        if nome is None:
            continue  # oscurata: non si giudica
        if not nome or any(c not in NOME_LECITO for c in nome):
            raise NonConforme("RCP.md §4.3",
                              f"il nome di capacita' {nome!r} non e' fatto di a-z, 0-9 e punto",
                              le.base + inizio, inizio)
        # ⛔ Un nome ripetuto e' ERRORE_PROTOCOLLO: «vince l'ultimo» e «vince
        #    il primo» sono due implementazioni dello stesso documento.
        if nome in visti:
            raise NonConforme("RCP.md §4.3",
                              f"la capacita' {nome!r} compare due volte "
                              f"(la prima allo scostamento {visti[nome]})",
                              le.base + inizio, inizio)
        visti[nome] = inizio
        if valore is not None and valore == "":
            raise NonConforme("RCP.md §4.3",
                              f"la capacita' {nome!r} ha valore vuoto: "
                              "chi non ha niente da dire non manda la capacita'",
                              le.base + inizio, inizio)
        # ⛔ Un nome CONOSCIUTO dal lato sbagliato non e' coperto
        #    dall'eccezione dei nomi sconosciuti.
        atteso = CAPACITA.get(nome)
        if atteso is not None and atteso != lato:
            chi = "client" if lato == CLIENT else "server"
            raise NonConforme("RCP.md §4.3",
                              f"la capacita' {nome!r} non puo' arrivare dal {chi}",
                              le.base + inizio, inizio)
    return visti


def corpo(tipo, nome, le, lato):
    """Legge il corpo secondo il tipo.  §4.3, §4.4, §4.5, §7.1."""
    if nome in ("CIAO", "ECCOMI"):
        le.u16("la versione")
        leggi_capacita(le, nome, lato)
    elif nome == "CREDENZIALI":
        le.stringa("l'utente", minimo=1, massimo=256)
        le.stringa("la parola", minimo=1, massimo=1024)
    elif nome == "AMMESSO":
        pass
    elif nome == "RESPINTO":
        m = le.u8("il motivo")
        if m not in MOTIVI:
            raise NonConforme("RCP.md §8.2", f"motivo {m:#04x} sconosciuto",
                              le.ass(-1) if False else le.base + le.i - 1, le.i - 1)
    elif nome == "ATTACCA":
        lar, alt = le.u32("tela_larghezza"), le.u32("tela_altezza")
        le.u32("vista_larghezza")
        le.u32("vista_altezza")
        le.stringa("la disposizione", massimo=64)
        # ⛔ I limiti sono normativi, e la parita' non e' pignoleria: una
        #    misura dispari la arrotonda il codificatore, in silenzio.
        for eti, v, mi, ma in (("tela_larghezza", lar, 320, 7680),
                               ("tela_altezza", alt, 240, 4320)):
            if not (mi <= v <= ma):
                raise NonConforme("RCP.md §4.5",
                                  f"{eti} = {v}, fuori da {mi}..{ma}", le.base, 0)
            if v % 2:
                raise NonConforme("RCP.md §4.5", f"{eti} = {v} e' dispari",
                                  le.base, 0)
    elif nome == "SESSIONE":
        st = le.u8("lo stato")
        if st not in (1, 2):
            raise NonConforme("RCP.md §4.5",
                              f"stato {st}: previsti 1 = NUOVA o 2 = RIPRESA",
                              le.base + le.i - 1, le.i - 1)
        le.u32("tela_larghezza")
        le.u32("tela_altezza")
        le.stringa("il desktop", massimo=64)
    elif nome == "CONGEDO":
        m = le.u8("il motivo")
        if m not in MOTIVI:
            raise NonConforme("RCP.md §8.2",
                              f"motivo {m:#04x} sconosciuto — e il codice 0 "
                              "NON DEVE essere usato (§3.1)",
                              le.base + le.i - 1, le.i - 1)
        le.stringa("il dettaglio")
    elif nome in ("VISTA", "ADATTA_TELA"):
        le.u32("larghezza")
        le.u32("altezza")
    elif nome == "DISPOSIZIONE":
        le.stringa("la disposizione", massimo=64)
    elif nome == "RICHIEDI_CHIAVE":
        le.u32("ultimo_numero")
    else:
        # I corpi che RCP/1 definisce e questo validatore non serve ancora
        # (CURSORE_FORMA, TELA, BANCO_*): si dichiara di non giudicarli.
        return False
    le.fine(nome)
    return True


# ---------------------------------------------------------------------------
# La macchina degli stati della stretta di mano — RCP.md §1 e §4.
ORDINE = ["CIAO", "ECCOMI", "CREDENZIALI", "AMMESSO", "ATTACCA", "SESSIONE"]


class Stato:
    def __init__(self):
        self.fatti = []
        self.attiva = False

    def ammette(self, nome):
        """Il messaggio puo' arrivare adesso?  Restituisce None o il perche' no."""
        if nome in ("CONGEDO",):
            return None  # ↔ in qualunque momento
        if nome == "RESPINTO":
            return None if self.fatti[-1:] == ["CREDENZIALI"] else \
                "RESPINTO risponde a CREDENZIALI"
        if self.attiva:
            return None  # a sessione aperta l'ordine non e' piu' vincolato
        if nome not in ORDINE:
            return f"{nome} non fa parte della stretta di mano"
        atteso = ORDINE[len(self.fatti)] if len(self.fatti) < len(ORDINE) else None
        if nome != atteso:
            return f"atteso {atteso}, arrivato {nome}"
        return None

    def segna(self, nome):
        if nome in ORDINE and not self.attiva:
            self.fatti.append(nome)
            if self.fatti == ORDINE:
                self.attiva = True


# ---------------------------------------------------------------------------
def valida(percorso):
    with open(percorso, "rb") as f:
        d = f.read()

    if len(d) < 16 or d[:8] != MAGIA:
        raise Malformata("non comincia con la magia di RCP.md §11.1")
    quanti, riservato = struct.unpack("!II", d[8:16])
    if riservato != 0:
        raise Malformata(f"il campo riservato vale {riservato}, DEVE essere 0")

    print(f"== il validatore del filo — {percorso}")
    print(f"   blocchi dichiarati: {quanti}   byte: {len(d)}")

    p = 16
    stato = Stato()
    visti = 0
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
            impronta = d[p + 8:p + 40]
            p += 40
            if ini + qua > lung:
                raise Malformata(
                    f"blocco {nb}: intervallo oscurato [{ini},{ini + qua}) "
                    f"fuori dal carico di {lung} byte")
            for o, q in oscurati:
                if not (ini + qua <= o or ini >= o + q):
                    raise Malformata(f"blocco {nb}: due intervalli oscurati si sovrappongono")
            oscurati.append((ini, qua))
            del impronta
        if p + lung > len(d):
            raise Malformata(f"blocco {nb}: il carico e' troncato")
        carico, base = d[p:p + lung], p
        p += lung
        visti += 1

        if verso not in (CLIENT, SERVER):
            raise Malformata(f"blocco {nb}: verso {verso}, previsti 1 o 2")
        # ⛔ Il riempimento degli intervalli oscurati e' 0x2A, non zero: e' il
        #    formato che lo impone, e un intervallo di zeri «per caso»
        #    legittimo sarebbe un oscuramento che non si vede.
        for o, q in oscurati:
            if any(b != RIEMPIMENTO for b in carico[o:o + q]):
                raise Malformata(
                    f"blocco {nb}: un intervallo oscurato non e' fatto di 0x2A")

        chi = "client" if verso == CLIENT else "server"
        if canale not in CANALI:
            raise NonConforme("RCP.md §2.5",
                              f"il byte alto del tipo vale {canale:#04x}: "
                              "fuori dai cinque canali",
                              base, 0)
        if canale != 0x00:
            print(f"   blocco {nb}: canale {CANALI[canale]} dal {chi}, "
                  f"{lung} byte — non giudicato da questo validatore")
            continue

        # Il canale di controllo vive solo sullo stream 0 della sessione (§2.5).
        le = Lettore(carico, base, oscurati)
        while le.resta():
            inizio_msg = le.i
            tipo = le.u16("il tipo")
            lung_msg = le.u32("la lunghezza")
            if lung_msg > MASSIMO_MESSAGGIO:
                raise NonConforme("RCP.md §6.1",
                                  f"lunghezza {lung_msg} oltre il tetto di 1 MiB",
                                  base + inizio_msg + 2, inizio_msg + 2)
            if le.resta() < lung_msg:
                raise NonConforme(
                    "RCP.md §6.1",
                    f"dichiara {lung_msg} byte di corpo e ce ne sono {le.resta()}",
                    base + inizio_msg + 2, inizio_msg + 2)
            if (tipo >> 8) != 0x00:
                raise NonConforme("RCP.md §2.5",
                                  f"tipo {tipo:#06x}: byte alto {tipo >> 8:#04x}, "
                                  "il controllo vuole 0x00",
                                  base + inizio_msg, inizio_msg)
            if tipo not in TIPI:
                raise NonConforme("RCP.md §7.1", f"tipo {tipo:#06x} sconosciuto",
                                  base + inizio_msg, inizio_msg)
            nome, verso_atteso = TIPI[tipo]
            if verso_atteso is not None and verso_atteso != verso:
                raise NonConforme("RCP.md §7.1",
                                  f"{nome} non puo' arrivare dal {chi}",
                                  base + inizio_msg, inizio_msg)
            perche = stato.ammette(nome)
            if perche:
                raise NonConforme("RCP.md §4 (l'ordine della stretta di mano)",
                                  f"{nome} nello stato sbagliato: {perche}",
                                  base + inizio_msg, inizio_msg)

            sotto = Lettore(carico[le.i:le.i + lung_msg], base + le.i,
                            [(o - le.i, q) for o, q in oscurati
                             if o + q > le.i and o < le.i + lung_msg])
            giudicato = corpo(tipo, nome, sotto, verso)
            print(f"   blocco {nb}: {nome:<14s} dal {chi:<6s} {lung_msg:>5} byte"
                  + ("" if giudicato else "   (corpo non giudicato)"))
            stato.segna(nome)
            le.i += lung_msg

    if visti != quanti:
        raise Malformata(f"dichiarati {quanti} blocchi, letti {visti}")
    print(f"\n   ⭐ conforme: {visti} blocchi, nessuna violazione")
    return 0


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    try:
        return valida(sys.argv[1])
    except NonConforme as e:
        print(f"\n   ⛔ NON CONFORME — {e.regola}")
        print(f"      {e.dice}")
        print(f"      byte {e.ass} nel file · scostamento {e.rel} nel carico del blocco")
        return 1
    except Malformata as e:
        print(f"\n   ⚠ REGISTRAZIONE MALFORMATA: {e}")
        print("      ⛔ Non e' un giudizio sul filo: e' un difetto del file.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
