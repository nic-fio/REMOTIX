#!/usr/bin/env python3
"""01-b4-validatore.py — il validatore del filo: quale byte non è conforme a RCP.md.

    python3 01-b4-validatore.py registrazione.rcpreg

    uscita 0  la registrazione è conforme — e si dice SU QUANTI messaggi
    uscita 1  non è conforme — e si dice QUALE byte e QUALE regola
    uscita 2  la REGISTRAZIONE è rotta, o non si legge (non è un giudizio sul filo)
    uscita 3  ⛔ non c'è NIENTE DA GIUDICARE (non è un giudizio sul filo)

---------------------------------------------------------------------------
⛔ CHE COS'E', E PERCHE' E' UN TERZO PROGRAMMA

`RCP.md` §11: *«client e server NON si collaudano l'uno contro l'altro: si
collaudano contro questo documento»*.  Questo e' **l'unico arbitro meccanico**
che avremo, e vale solo se e' scritto **leggendo la specifica** — non il
server, non la pagina.  Chi lo fa crescere non guardi il C: se lo guardasse ne
erediterebbe i fraintendimenti, e due programmi scritti dalla stessa mano che
vanno d'accordo non confermano niente (`README.md`).

---------------------------------------------------------------------------
⛔ QUATTRO ESITI, E TRE DI ESSI DICONO «NON E' UN GIUDIZIO SUL FILO»

  0  conforme — ⛔ e con il DENOMINATORE: quanti blocchi, quanti sul canale di
     controllo, quanti messaggi letti, quanti con il corpo davvero giudicato
  1  NON conforme — con lo scostamento del byte e la regola violata
  2  ⛔ la REGISTRAZIONE e' rotta, **o non si legge**
  3  ⛔ non c'e' NIENTE DA GIUDICARE: zero messaggi di controllo

Il **2** esiste perche' «il file e' rotto» e «il filo non era conforme» sono
due fatti diversi con due cure diverse, e un validatore che li confondesse
manderebbe a cercare un difetto di protocollo dentro un difetto di banco.

⛔ **E ci finisce anche il file che non si apre** — 10 agosto 2026, rilievo
R7.5.  Un `OSError` risaliva fuori da `main` e il processo usciva **1**, cioe'
diceva *«il filo non e' conforme»* per un file che non esisteva o di cui non
si avevano i permessi.  Questo validatore gira anche **dentro il contenitore**,
su registrazioni scritte da un server lanciato come root: il giorno in cui i
permessi non tornano, l'arbitro mandava la diagnosi a leggere il protocollo.
E' la forma d'errore **E8** alla lettera: «vuoto» e «proibito» hanno lo stesso
aspetto.

⛔ **E il 3 e' nuovo, dallo stesso rilievo (R7.4)**, e cura la faccia opposta:
una registrazione con **zero blocchi**, o fatta di soli blocchi video, usciva
**0** con la frase *«⭐ conforme: 0 blocchi, nessuna violazione»*.  «Non ho
niente da giudicare» e «ho giudicato tutto e va bene» sono due fatti diversi
con lo stesso colore, ed e' `LEZIONI.md` §1.9: *un conteggio senza
denominatore*.  ⚠ Un arbitro che assolve senza aver guardato e' peggio di un
arbitro che sbaglia: sopra il suo verde ci si costruisce.

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


class NienteDaGiudicare(Exception):
    """⛔ Nel file non c'e' nessun messaggio di controllo da giudicare.

    Non e' «conforme» e non e' «non conforme»: e' l'assenza dell'oggetto del
    giudizio, e ha un codice d'uscita suo perche' la cura e' un'altra —
    si guarda il registratore, non il protocollo (rilievo R7.4).
    """


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

    def stringa(self, che, minimo=0, massimo=None, regola="RCP.md §4.4"):
        """RCP.md §6.0: u16 lunghezza + quella lunghezza di UTF-8, senza terminatore.

        ⛔ `regola` si passa da fuori.  Gli intervalli dell'utente e della
           parola d'ordine stanno in §4.4, quelli dei nomi e dei valori di
           capacita' in §4.3 — e qui si citava §4.4 per tutti.  Un rosso con
           la sezione sbagliata accanto passa il controllo di
           `01-b4-lancia.py` senza che nessuno se ne accorga, perche' il
           colore e' quello giusto (rilievo R7.12).
        """
        inizio_campo = self.i
        n = self.u16(f"la lunghezza di {che}")
        dati_inizio = self.i
        b = self._prendi(n, che)
        if n < minimo:
            raise NonConforme(regola,
                              f"{che} e' lunga {n} byte, il minimo e' {minimo}",
                              self.base + inizio_campo, inizio_campo)
        if massimo is not None and n > massimo:
            raise NonConforme(regola,
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
        nome = le.stringa(f"il nome della capacita' {k}", minimo=1, massimo=64,
                          regola="RCP.md §4.3")
        valore = le.stringa(f"il valore della capacita' {k}", massimo=256,
                            regola="RCP.md §4.3")
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
        le.stringa("l'utente", minimo=1, massimo=256, regola="RCP.md §4.4")
        le.stringa("la parola", minimo=1, massimo=1024, regola="RCP.md §4.4")
    elif nome == "AMMESSO":
        pass
    elif nome == "RESPINTO":
        m = le.u8("il motivo")
        if m not in MOTIVI:
            raise NonConforme("RCP.md §8.2", f"motivo {m:#04x} sconosciuto",
                              le.ass(-1) if False else le.base + le.i - 1, le.i - 1)
    elif nome == "ATTACCA":
        # ⛔ LO SCOSTAMENTO DEL CAMPO SI PRENDE PRIMA DI LEGGERLO.
        #
        #    Questi quattro `raise` passavano `le.base, 0`: l'inizio del CORPO
        #    come assoluto e ZERO come relativo, cioe' **due byte diversi**.
        #    §11.1 chiede due modi di dire lo **stesso** byte — «assoluto nel
        #    file, e relativo al carico del blocco» — e chi apre il file con un
        #    editor e chi legge la specifica finivano a guardare due punti
        #    diversi.  E su `tela_altezza` il byte accusato era comunque quello
        #    della larghezza (rilievo R7.12).
        off_lar = le.i
        lar = le.u32("tela_larghezza")
        off_alt = le.i
        alt = le.u32("tela_altezza")
        le.u32("vista_larghezza")
        le.u32("vista_altezza")
        le.stringa("la disposizione", massimo=64, regola="RCP.md §4.5")
        # ⛔ I limiti sono normativi, e la parita' non e' pignoleria: una
        #    misura dispari la arrotonda il codificatore, in silenzio.
        for eti, v, off, mi, ma in (("tela_larghezza", lar, off_lar, 320, 7680),
                                    ("tela_altezza", alt, off_alt, 240, 4320)):
            if not (mi <= v <= ma):
                raise NonConforme("RCP.md §4.5",
                                  f"{eti} = {v}, fuori da {mi}..{ma}",
                                  le.base + off, off)
            if v % 2:
                raise NonConforme("RCP.md §4.5", f"{eti} = {v} e' dispari",
                                  le.base + off, off)
    elif nome == "SESSIONE":
        st = le.u8("lo stato")
        if st not in (1, 2):
            raise NonConforme("RCP.md §4.5",
                              f"stato {st}: previsti 1 = NUOVA o 2 = RIPRESA",
                              le.base + le.i - 1, le.i - 1)
        le.u32("tela_larghezza")
        le.u32("tela_altezza")
        le.stringa("il desktop", massimo=64, regola="RCP.md §4.5")
    elif nome == "CONGEDO":
        m = le.u8("il motivo")
        if m not in MOTIVI:
            raise NonConforme("RCP.md §8.2",
                              f"motivo {m:#04x} sconosciuto — e il codice 0 "
                              "NON DEVE essere usato (§3.1)",
                              le.base + le.i - 1, le.i - 1)
        le.stringa("il dettaglio", regola="RCP.md §7.1")
    elif nome in ("VISTA", "ADATTA_TELA"):
        le.u32("larghezza")
        le.u32("altezza")
    elif nome == "DISPOSIZIONE":
        le.stringa("la disposizione", massimo=64, regola="RCP.md §4.5")
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

# ⛔ I messaggi che vivono DOPO `SESSIONE`, e sono questi e basta (§7.1).
#    La stretta di mano non ci sta dentro: §1 dice che «l'ordine dei cinque
#    passi non ammette permute», e non che dopo il quinto tutto sia permesso.
DOPO_SESSIONE = {"VISTA", "DISPOSIZIONE", "CURSORE_FORMA", "ADATTA_TELA",
                 "RICHIEDI_CHIAVE", "TELA", "BANCO_MARCA", "BANCO_ESITO"}


class Stato:
    """La macchina della stretta di mano — RCP.md §1, §4, §4.4.

    ⛔ Aveva **tre** buchi nella stessa funzione (rilievo R7.10), e sul più
       grosso i due arbitri del progetto si contraddicevano:

       1. `RESPINTO` non veniva **segnato**, quindi dopo un rifiuto la
          macchina credeva ancora di aspettare `AMMESSO`.  ⇒ `CIAO · ECCOMI ·
          CREDENZIALI · RESPINTO · RESPINTO · AMMESSO · ATTACCA · SESSIONE`
          era dichiarato **conforme**: un server che rifiuta le credenziali,
          lo ripete, poi ammette l'utente e apre la sessione;
       2. a sessione aperta `ammette` diceva sì a **qualunque** nome, quindi
          un secondo `CREDENZIALI` passava — ed e' la violazione che §4.4
          nomina per esteso e che B5 prova con `credenziali-due-volte`.  ⛔ I
          due arbitri davano verdetti opposti sulla stessa regola;
       3. il commento diceva *«a sessione aperta l'ordine non e' piu'
          vincolato»*, che `RCP.md` non autorizza — un commento che spiega
          perche' una riga e' giusta non e' una prova che lo sia.
    """

    def __init__(self):
        self.fatti = []
        self.attiva = False
        self.respinto = False

    def ammette(self, nome):
        """Il messaggio puo' arrivare adesso?  Restituisce None o il perche' no."""
        # ⛔ Dopo `RESPINTO` al client resta una cosa sola che puo' dire, ed e'
        #    `CONGEDO` (§4.4).  Qualunque altro messaggio — «e in particolare
        #    un secondo `CREDENZIALI`» — e' la violazione che §4.4 vieta.
        if self.respinto:
            return None if nome == "CONGEDO" else \
                f"dopo RESPINTO al client resta solo CONGEDO, e' arrivato {nome}"
        if nome == "CONGEDO":
            return None  # ↔ in qualunque momento
        if nome == "RESPINTO":
            return None if self.fatti[-1:] == ["CREDENZIALI"] else \
                "RESPINTO risponde a CREDENZIALI"
        if self.attiva:
            # ⛔ A sessione aperta l'ordine dei messaggi DI SESSIONE e' libero;
            #    quelli della stretta di mano no: ripeterli e' una permuta dei
            #    cinque passi, che §1 vieta.
            if nome in DOPO_SESSIONE:
                return None
            return f"{nome} appartiene alla stretta di mano, gia' conclusa"
        if nome not in ORDINE:
            return f"{nome} non fa parte della stretta di mano"
        atteso = ORDINE[len(self.fatti)] if len(self.fatti) < len(ORDINE) else None
        if nome != atteso:
            return f"atteso {atteso}, arrivato {nome}"
        return None

    def segna(self, nome):
        if nome == "RESPINTO":
            self.respinto = True
            return
        if nome in ORDINE and not self.attiva:
            self.fatti.append(nome)
            if self.fatti == ORDINE:
                self.attiva = True


# ---------------------------------------------------------------------------
# ⛔ L'IMPRONTA DI §11.1: QUEL CHE SI PUO' VERIFICARE, E QUEL CHE NON SI PUO'.
#
#    Trentadue byte per intervallo oscurato viaggiano nel formato per legare
#    quel che il registratore dichiara di aver nascosto a quel che c'era.  Qui
#    venivano letti in una variabile e cancellati con `del` alla riga dopo, e
#    `hashlib` era importato e mai usato (rilievo R7.11).
#
# ⛔ **Ma verificarla contro i byte veri e' impossibile da questo lato, per
#    costruzione**: i byte veri sono precisamente quelli che il formato esiste
#    per NON far arrivare fin qui.  Chi puo' farlo e' solo chi li ha — il
#    registratore, con un banco suo.  Dirlo e' parte del mestiere di un
#    arbitro: un controllo che non si puo' fare va dichiarato, non simulato.
#
# ⭐ Quel che si puo' verificare, e da qui in poi si verifica, e' che
#    l'impronta non sia una delle **impronte finte** che un registratore
#    sbagliato produce da se':
#      · trentadue zeri — il campo mai riempito;
#      · SHA-256 del riempimento `0x2A` × quanti — ha impronto il RIEMPIMENTO
#        invece dei byte veri, cioe' ha certificato la propria sostituzione;
#      · SHA-256 del vuoto — ha impronto una stringa che non aveva.
#    ⚠ Sono difetti del REGISTRATORE, non del filo: escono con l'esito 2.
FINTE = {
    b"\x00" * 32: "trentadue zeri: il campo non e' mai stato riempito",
    hashlib.sha256(b"").digest(): "SHA-256 del vuoto",
}


def controlla_impronta(nb, ini, qua, impronta):
    perche = FINTE.get(impronta)
    if perche is None and impronta == hashlib.sha256(
            bytes([RIEMPIMENTO]) * qua).digest():
        perche = ("SHA-256 del RIEMPIMENTO 0x2A: il registratore ha impronto "
                  "quel che ha messo, non quel che ha tolto")
    if perche:
        raise Malformata(
            f"blocco {nb}: l'intervallo oscurato [{ini},{ini + qua}) porta "
            f"un'impronta finta — {perche}")


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
    # ⛔ I DENOMINATORI DEL VERDETTO, e sono quattro perche' le cose che si
    #    possono NON aver guardato sono quattro.  «Nessuna violazione» senza
    #    di essi era vero anche su un file di zero blocchi (rilievo R7.4).
    visti = 0        # blocchi letti
    di_controllo = 0  # blocchi sul canale 0x00
    messaggi = 0     # messaggi di controllo letti
    giudicati = 0    # ... di cui con il corpo davvero giudicato
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
            controlla_impronta(nb, ini, qua, impronta)
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
        di_controllo += 1

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
            messaggi += 1
            giudicati += int(bool(giudicato))
            print(f"   blocco {nb}: {nome:<14s} dal {chi:<6s} {lung_msg:>5} byte"
                  + ("" if giudicato else "   (corpo non giudicato)"))
            stato.segna(nome)
            le.i += lung_msg

    # ⛔ IL CONTROLLO CHE C'ERA NON POTEVA FALLIRE, E MANCAVA QUELLO CHE SERVE.
    #
    #    Qui stava `if visti != quanti: raise Malformata(...)`.  `visti` viene
    #    incrementato una volta per iterazione di un `for nb in range(quanti)`
    #    che o completa o solleva: era **codice morto**, in piedi al posto del
    #    controllo che copre i due modi veri di far sparire dei byte dal
    #    giudizio (rilievo R7.4):
    #      · `quanti_blocchi` sotto-dichiarato — si scrive 4 dove sono 6 e i
    #        due blocchi offensivi non vengono mai letti;
    #      · una coda di spazzatura dopo l'ultimo blocco dichiarato.
    #    In tutt'e due i casi il file usciva «⭐ conforme».
    if p != len(d):
        raise Malformata(
            f"restano {len(d) - p} byte dopo i {quanti} blocchi dichiarati: "
            f"o `quanti_blocchi` e' sotto-dichiarato — e allora c'e' del filo "
            f"che nessuno ha giudicato — o c'e' una coda che non e' del formato")

    # ⛔ E «CONFORME» SI DICE CON IL DENOMINATORE, O NON SI DICE.
    print(f"\n   guardati: {visti} blocchi, di cui {di_controllo} sul canale di "
          f"controllo · {messaggi} messaggi letti, {giudicati} col corpo giudicato")
    if messaggi == 0:
        raise NienteDaGiudicare(
            f"{visti} blocchi, {di_controllo} sul canale di controllo, "
            f"ZERO messaggi di controllo")
    print(f"   ⭐ conforme: nessuna violazione in {messaggi} messaggi")
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
    except OSError as e:
        # ⛔ E8: «vuoto» e «proibito» hanno lo stesso aspetto.  Prima questo
        #    risaliva fuori da `main` e il processo usciva **1**, cioe' «il
        #    filo non e' conforme», su un file che non si era nemmeno aperto —
        #    e la diagnosi partiva dal protocollo (rilievo R7.5).
        print(f"\n   ⚠ LA REGISTRAZIONE NON SI LEGGE: {e}")
        print("      ⛔ Non e' un giudizio sul filo, e non e' «il file e' rotto»:")
        print("         e' che non si e' potuto aprire.  Si guardano permessi,")
        print("         percorso e volume — non RCP.md.")
        return 2
    except NienteDaGiudicare as e:
        print(f"\n   ⛔ NIENTE DA GIUDICARE: {e}")
        print("      Non e' «conforme»: e' l'assenza dell'oggetto del giudizio.")
        print("      Si guarda il registratore — chi doveva scrivere quei byte.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
