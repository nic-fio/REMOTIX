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
     controllo e quanti sul video, quanti messaggi letti, quanti col corpo
     davvero giudicato, quanti flussi video
  1  NON conforme — con lo scostamento del byte e la regola violata
  2  ⛔ la REGISTRAZIONE e' rotta, **o non si legge**, ⛔ **o e' di un'altra
     versione del formato**, ⛔ **o manca lo strumento per guardarla**
  3  ⛔ non c'e' NIENTE DA GIUDICARE: zero messaggi di controllo **e** zero
     flussi video — ⚠ e la seconda meta' e' del 12 agosto 2026

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

`FASI.md` §01-filo-nudo B4: sulla registrazione col riempimento, un validatore
che non conosce §6.0 non vede il byte in piu': legge di traverso il messaggio
SUCCESSIVO e dichiara non conforme quello.  **Rosso giusto, byte sbagliato** —
e su una traccia vera manda la diagnosi a leggere il messaggio sbagliato.
Per questo ogni verdetto porta due scostamenti (assoluto e dentro il blocco) e
la riga di RCP.md che regge il giudizio.

---------------------------------------------------------------------------
⭐⛔ IL 12 AGOSTO 2026 QUESTO VALIDATORE HA IMPARATO IL **CANALE VIDEO**

Fino all'11 agosto la riga 521 diceva:

    if canale != 0x00:
        print(... "non giudicato da questo validatore")
        continue

⚠ Era una riga **onesta** — dichiarava di non giudicare, che e' il contrario di
assolvere — ma dal primo fotogramma in poi il capitolo piu' voluminoso del filo
sarebbe tornato a essere validato da **una sola** implementazione, scritta
dalla stessa mano che scrive il server: lo stato che `RCP.md` §0 chiama il
difetto muto.

⛔ E il 12 agosto 2026 sono entrate in `RCP.md` **sei righe normative** che
parlano tutte del video (§2.5, §5.2, §6.2), e nessuno dei due arbitri le sapeva
giudicare.  Adesso:

  **P1** §2.5   nessuno stream video prima di aver spedito `SESSIONE`
  **P2** §6.2   `numero` parte da **1**, e lo `0` e' riservato
  **P3** §2.5   un `0x03` sul **canale di controllo** e' `ERRORE_PROTOCOLLO`
  **P4** §6.2   **FIN prima dei 28 byte** e' `ERRORE_PROTOCOLLO`
  **P5** §6.2   `largh.`/`altezza` **DEVONO** valere la tela concessa
  **P6** §5.2   il primo fotogramma dopo `SESSIONE` **DEVE** essere chiave

⛔⛔ **E IL GIUDIZIO DEL FOTOGRAMMA NON E' RISCRITTO QUI: SI IMPORTA.**
`02-filo-fotogramma.py` e' il giudice scritto leggendo `RCP.md` §6.2, e due
copie della stessa lettura sarebbero due implementazioni della stessa mano —
cioe' precisamente cio' che un arbitro esterno esiste per impedire.  ⚠ Se non
si trova, questo validatore **non indovina e non salta**: esce **2**, che e'
«non ho potuto guardare», e lo dice.

⚠ ⛔ **E UN BUCO CHE VA DICHIARATO, perche' non e' di questo file curarlo.**
`01-b12-guasti.py` elenca in `FILE_CHE_CONTANO["B4"]` i tre file su cui poggia
la certificazione di B4, e `02-filo-fotogramma.py` **non e' fra quelli**: da
oggi si puo' riscrivere il giudice del fotogramma e la riga «B4 certificato»
resta valida a vista mentre il banco certificato non e' piu' lo stesso.  E'
esattamente la forma del rilievo **R12-A.5**, rientrata da un'altra porta.
⇒ La cura e' una voce in `FILE_CHE_CONTANO` e una in `CORREDO`, e quel file e'
di chi cura **D10**.  Qui si dichiara.

---------------------------------------------------------------------------
⛔ IL FORMATO DELLA REGISTRAZIONE E' `RCPREG 0x00 0x02`, E IL VECCHIO SI RIFIUTA

§11.1, 12 agosto 2026: il blocco porta `fine` — *0 continua · 1 FIN · 2
RESET_STREAM* — e passa da **16 a 17 byte**.  ⛔ *«La magia passa a 0x00 0x02
perche' il blocco cambia misura: un validatore vecchio deve RIFIUTARE il
formato nuovo, non leggerlo di traverso»*, e vale nei due versi: un `.rcpreg`
del 10 agosto letto con questo lettore avrebbe il `canale` dentro lo `stream` e
ogni blocco scivolato di un byte — ne uscirebbe un **giudizio** su byte che
nessuno ha scritto.
"""
import hashlib
import importlib.util
import os
import struct
import sys

QUI = os.path.dirname(os.path.abspath(__file__))

MAGIA = b"RCPREG\x00\x02"
MAGIA_VECCHIA = b"RCPREG\x00\x01"
RIEMPIMENTO = 0x2A  # il byte degli intervalli oscurati (RCP.md §11.1)

# Il blocco di §11.1: verso, canale, fine, stream, lunghezza, quanti_oscurati.
BLOCCO = "!BBBQIH"
BLOCCO_BYTE = struct.calcsize(BLOCCO)
CONTINUA, FIN, RESET = 0, 1, 2
FINE = {CONTINUA: "continua", FIN: "FIN", RESET: "RESET_STREAM"}

VIDEO = 0x03
CONTROLLO = 0x00


def cerca_in_su(nome, da):
    """Il file `nome` risalendo le cartelle da `da`.  ⛔ (None) se non c'e'.

    ⚠ Serve perche' `01-b12-guasti.py` fa girare questo validatore da una
      **copia** (`01-b12-copie/`) che contiene solo il corredo di B4: il
      giudice del fotogramma non c'e', e va cercato dov'e' davvero.  E' la
      stessa strada che `01-b9-letture.py` usa per trovare `RCP.md`.
    """
    d = da
    for _ in range(6):
        p = os.path.join(d, nome)
        if os.path.exists(p):
            return p
        su = os.path.dirname(d)
        if su == d:
            break
        d = su
    return None


def giudice_del_fotogramma():
    """⛔ Il giudice si IMPORTA, non si ricopia — vedi l'intestazione.

    Restituisce (modulo, perche_no).  ⚠ Un'importazione fallita **non e' un
    fotogramma conforme**: chi chiama esce 2.
    """
    p = cerca_in_su("02-filo-fotogramma.py", QUI)
    if p is None:
        return None, ("`02-filo-fotogramma.py` non si trova risalendo da "
                      f"{QUI}: e' il giudice che applica §6.2, e senza di lui "
                      f"il canale video non si giudica")
    try:
        spec = importlib.util.spec_from_file_location("f24_b4", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:                      # noqa: BLE001
        return None, f"«{p}» non si importa: {type(e).__name__}: {e}"
    return mod, ""

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
    """⛔ Nel file non c'e' niente che questo validatore sappia giudicare.

    Non e' «conforme» e non e' «non conforme»: e' l'assenza dell'oggetto del
    giudizio, e ha un codice d'uscita suo perche' la cura e' un'altra —
    si guarda il registratore, non il protocollo (rilievo R7.4).

    ⚠ **E dal 12 agosto 2026 vuol dire due cose insieme**: zero messaggi di
      controllo **e** zero flussi video.  Prima bastava la prima, perche' il
      video non lo guardava nessuno; una registrazione di soli fotogrammi
      usciva 3 ed era vero.  Oggi quella stessa registrazione ha un oggetto
      del giudizio, e dire «niente da giudicare» sarebbe **assolvere senza
      aver guardato**.
    """


class NonHoPotutoGuardare(Exception):
    """⛔ Manca lo strumento, non il giudizio — e sono due cose diverse.

    ⚠ Ha lo stesso codice d'uscita di `Malformata` (**2**) perche' nessuno dei
      due e' un giudizio sul filo, ma **non la stessa frase**: li' si guarda il
      file, qui si guarda l'installazione.  Confonderle manderebbe a cercare un
      difetto di registrazione dentro un'importazione fallita.
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
    visti, valori = {}, {}
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
        valori[nome] = valore
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
    # ⛔ Si restituiscono i VALORI, non gli scostamenti: da qui `corpo()` prende
    #    il codec negoziato in `ECCOMI`, che §6.2 lega al campo `codec` di ogni
    #    fotogramma.  ⚠ Gli scostamenti restano interni — servivano solo al
    #    messaggio del nome ripetuto.
    return valori


def corpo(tipo, nome, le, lato, stato=None):
    """Legge il corpo secondo il tipo.  §4.3, §4.4, §4.5, §7.1.

    ⛔ `stato` c'e' dal 12 agosto 2026: il canale VIDEO non si puo' giudicare
       senza la **tela concessa** (§4.5, per P5) e senza il **codec negoziato**
       (§4.3, per §6.2), e tutt'e due viaggiano qui.  ⚠ Prenderli dai propri
       predefiniti sarebbe giudicare se' stessi.
    """
    if nome in ("CIAO", "ECCOMI"):
        le.u16("la versione")
        cap = leggi_capacita(le, nome, lato)
        if stato is not None and nome == "ECCOMI":
            # §4.3: `ECCOMI` porta la scelta del server, una sola.
            stato.codec = {"hevc": 1, "av1": 2}.get(
                (cap.get("video.codec") or "").split(",")[0].strip())
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
        lar = le.u32("tela_larghezza")
        alt = le.u32("tela_altezza")
        le.stringa("il desktop", massimo=64, regola="RCP.md §4.5")
        # ⛔ LA TELA CONCESSA — e' questa che §6.2 lega a `largh.`/`altezza`.
        if stato is not None and lar is not None and alt is not None:
            stato.tela = (lar, alt)
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
    elif nome == "TELA":
        # ⛔ GIUDICATO DAL 12 AGOSTO 2026, e non per completezza: §6.2 lega
        #    `largh.`/`altezza` di ogni fotogramma alla **tela in vigore**, e
        #    l'unico messaggio che la cambia e' questo.  ⚠ Fino a ieri finiva
        #    nel ramo «corpi che questo validatore non serve ancora», cioe' il
        #    canale video non avrebbe potuto essere giudicato affatto dopo un
        #    `ADATTA_TELA`.
        es = le.u8("l'esito")
        if es not in (1, 2):
            raise NonConforme("RCP.md §7.1",
                              f"esito {es}: previsti 1 = ADATTATA o "
                              f"2 = RIFIUTATA",
                              le.base + le.i - 1, le.i - 1)
        mot = le.u8("il motivo")
        if es == 1 and mot != 0:
            raise NonConforme("RCP.md §7.1",
                              f"TELA(ADATTATA) con motivo {mot}: §7.1 vuole "
                              f"0 quando l'esito e' ADATTATA",
                              le.base + le.i - 1, le.i - 1)
        if es == 2 and mot not in (1, 2, 3):
            raise NonConforme("RCP.md §7.1",
                              f"motivo {mot}: §7.1 ne definisce tre — 1 = "
                              f"COMPOSITORE_INCAPACE, 2 = MISURA_FUORI_LIMITI, "
                              f"3 = NON_ORA",
                              le.base + le.i - 1, le.i - 1)
        lar = le.u32("tela_larghezza")
        alt = le.u32("tela_altezza")
        # ⛔ §7.1: questi due campi sono «la tela in vigore DOPO questo
        #    messaggio» — e lo sono **anche** quando l'esito e' RIFIUTATA, dove
        #    riportano quella di prima.  ⇒ si prende il campo, non si deduce
        #    dall'esito: e' il campo a essere definito cosi'.
        if stato is not None and lar is not None and alt is not None:
            stato.tela = (lar, alt)
            if es == 1:
                stato.tela_da = "TELA(ADATTATA) (§7.1)"
    else:
        # I corpi che RCP/1 definisce e questo validatore non serve ancora
        # (CURSORE_FORMA, BANCO_*): si dichiara di non giudicarli.
        # ⚠ `TELA` stava qui fino all'11 agosto 2026, ed e' uscito perche' il
        #   canale video ha bisogno della tela in vigore (§6.2).
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
        # ⛔ Quel che il canale di controllo dice e che serve a giudicare il
        #    VIDEO: la tela concessa (§4.5) e il codec negoziato (§4.3).
        #    ⚠ `None` e' «non l'ho letto», e NON e' un valore predefinito.
        self.tela = None
        self.tela_da = "SESSIONE (§4.5)"
        self.codec = None

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

    # ⛔ IL FORMATO VECCHIO SI RIFIUTA, E CON LA SUA FRASE — §11.1.
    #
    #    «Non e' del formato» e «e' di un'altra versione» sono due fatti con
    #    due cure diverse: il primo manda a cercare chi ha rotto il file, il
    #    secondo a rigenerarlo.  ⛔ E leggerlo di traverso non e' un'opzione: il
    #    blocco vecchio e' di 16 byte, questo lettore ne vuole 17.
    if len(d) >= 8 and d[:8] == MAGIA_VECCHIA:
        raise Malformata(
            "e' una registrazione nel formato VECCHIO, «RCPREG 0x00 0x01»: il "
            "blocco non porta il campo `fine` e misura 16 byte invece di 17.  "
            "⛔ Non si legge di traverso — §11.1, 12 agosto 2026 — e non e' un "
            "file rotto: si RIGENERA con `01-b4-registrazioni.py`")
    if len(d) < 16 or d[:8] != MAGIA:
        raise Malformata("non comincia con la magia di RCP.md §11.1")
    quanti, riservato = struct.unpack("!II", d[8:16])
    if riservato != 0:
        raise Malformata(f"il campo riservato vale {riservato}, DEVE essere 0")

    print(f"== il validatore del filo — {percorso}")
    print(f"   blocchi dichiarati: {quanti}   byte: {len(d)}")

    p = 16
    stato = Stato()
    # ⛔ I DENOMINATORI DEL VERDETTO, e dal 12 agosto 2026 sono SEI: le cose che
    #    si possono NON aver guardato sono cresciute col canale video.
    #    «Nessuna violazione» senza di essi era vero anche su un file di zero
    #    blocchi (rilievo R7.4).
    visti = 0        # blocchi letti
    di_controllo = 0  # blocchi sul canale 0x00
    messaggi = 0     # messaggi di controllo letti
    giudicati = 0    # ... di cui con il corpo davvero giudicato
    di_video = 0     # blocchi sul canale 0x03
    flussi_video = 0  # ... raggruppati per stream: uno stream, un fotogramma
    # ⛔ Le due regole del 12 agosto che parlano di STREAM e non di byte: si
    #    decidono qui, sfogliando, perche' un giudice del singolo fotogramma
    #    non sa ne' su che stream sia arrivato ne' che cosa fosse gia' passato.
    sessione_vista = False          # P1 — §2.5
    stream_di_controllo = set()     # P3 — §2.5
    flussi, ordine = {}, []
    for nb in range(quanti):
        if p + BLOCCO_BYTE > len(d):
            raise Malformata(f"il blocco {nb} comincia oltre la fine del file")
        verso, canale, fine, stream, lung, nosc = struct.unpack(
            BLOCCO, d[p:p + BLOCCO_BYTE])
        p += BLOCCO_BYTE
        if fine not in FINE:
            raise Malformata(
                f"blocco {nb}: `fine` vale {fine}, e §11.1 ne definisce tre — "
                f"0 continua, 1 FIN, 2 RESET_STREAM")
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
        if canale == VIDEO:
            # ⛔ I blocchi video si RACCOLGONO e si giudicano dopo, per stream:
            #    uno stream, un fotogramma (§6.2), e i blocchi di stream
            #    diversi si interlacciano.  ⚠ E si tiene il **momento** in cui
            #    il flusso comincia — prima o dopo `SESSIONE` — perche' e' P1,
            #    e dopo la sfogliata quell'informazione e' persa.
            di_video += 1
            if stream not in flussi:
                flussi[stream] = {"pezzi": [], "base": base,
                                  "dopo_sessione": sessione_vista,
                                  "sul_controllo": stream in stream_di_controllo,
                                  # ⛔ la tela IN VIGORE quando il flusso si
                                  #    apre, non quella di fine file: giudicare
                                  #    un fotogramma con una tela concessa dopo
                                  #    di lui sarebbe leggere il filo
                                  #    all'indietro.
                                  "tela": stato.tela,
                                  "tela_da": stato.tela_da}
                ordine.append(stream)
            flussi[stream]["pezzi"].append((nb, verso, carico, fine, oscurati))
            continue
        if canale != CONTROLLO:
            print(f"   blocco {nb}: canale {CANALI[canale]} dal {chi}, "
                  f"{lung} byte — non giudicato da questo validatore")
            continue
        di_controllo += 1
        stream_di_controllo.add(stream)

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
            giudicato = corpo(tipo, nome, sotto, verso, stato)
            messaggi += 1
            giudicati += int(bool(giudicato))
            print(f"   blocco {nb}: {nome:<14s} dal {chi:<6s} {lung_msg:>5} byte"
                  + ("" if giudicato else "   (corpo non giudicato)"))
            stato.segna(nome)
            # ⛔ P1 — §2.5: da qui in poi il video e' lecito, e prima no.
            if nome == "SESSIONE" and verso == SERVER:
                sessione_vista = True
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

    # =======================================================================
    # ⭐⛔ IL CANALE VIDEO — le sei righe del 12 agosto 2026
    #
    #    Si giudica DOPO la sfogliata perche' due delle sei parlano di **quel
    #    che era gia' passato** (P1) e di **su quale stream** (P3), e un
    #    giudice del singolo fotogramma non lo puo' sapere.
    # =======================================================================
    if flussi:
        f24, perche_no = giudice_del_fotogramma()
        if f24 is None:
            # ⛔ E8: «non ho lo strumento» NON e' «va bene».  Un `continue` qui
            #    rimetterebbe in piedi la riga 521, con la differenza che
            #    stavolta il file dichiara di giudicare il video.
            raise NonHoPotutoGuardare(
                f"ci sono {len(flussi)} flussi video da giudicare e il giudice "
                f"non c'e': {perche_no}")
        # ⛔ La tela e il codec NON si indovinano: si prendono da `SESSIONE` e
        #    da `ECCOMI`, cioe' dal filo stesso.  Un arbitro che confrontasse
        #    con i propri predefiniti starebbe giudicando se' stesso — ed e' il
        #    caso `17-video-misura-diversa` a tenerlo onesto.
        #
        # ⭐ E LA TELA E' QUELLA **IN VIGORE**, NON QUELLA DI `SESSIONE` —
        #    §6.2, **corretta il 12 agosto 2026** poche ore dopo essere stata
        #    scritta, perche' propagarla fin qui ha mostrato che uccideva una
        #    sessione sana: dopo un `TELA(ADATTATA, 1280, 720)` (§7.1) il
        #    server cattura alla misura nuova, e un client che confrontasse
        #    ancora con `SESSIONE` chiuderebbe — la scena che §7.1 protegge
        #    con la sua eccezione 4.  ⇒ `stato.tela` si aggiorna su `SESSIONE`
        #    **e** su `TELA`, e ogni flusso video e' giudicato con la tela che
        #    era in vigore quando si e' aperto.
        ctx = f24.Contesto(tela=stato.tela or (1920, 1080),
                           codec_negoziato=stato.codec or 1,
                           sessione_aperta=True)
        for sid in ordine:
            fl = flussi[sid]
            flussi_video += 1
            # ⛔ P5 — la tela IN VIGORE all'apertura di QUESTO flusso.
            if fl["tela"] is not None:
                if fl["tela_da"].startswith("TELA"):
                    ctx.adatta_tela(*fl["tela"])
                else:
                    ctx.tela_larghezza, ctx.tela_altezza = fl["tela"]
            b0 = fl["pezzi"][0]
            base0 = fl["base"]

            # ── P3 — §2.5: un `0x03` sul canale di controllo
            if fl["sul_controllo"]:
                raise NonConforme(
                    "RCP.md §2.5",
                    f"flusso {sid}: un fotogramma sullo stream del CANALE DI "
                    f"CONTROLLO.  §2.5 vuole il video «solo su uno stream "
                    f"unidirezionale aperto dal server»", base0, 0)

            # ── P1 — §2.5: nessuno stream video prima di `SESSIONE`
            if not fl["dopo_sessione"]:
                raise NonConforme(
                    "RCP.md §2.5",
                    f"flusso {sid}: uno stream video si apre PRIMA di "
                    f"`SESSIONE` — il client riceve un fotogramma di cui non "
                    f"conosce ne' la misura ne' il codec.  E' l'invariante I3 "
                    f"sul filo", base0, 0)

            # ── e il verso, §2.5: il video va dal server al client
            if any(v != SERVER for _, v, _, _, _ in fl["pezzi"]):
                raise NonConforme(
                    "RCP.md §2.5",
                    f"flusso {sid}: un fotogramma DAL CLIENT — il video va dal "
                    f"server al client", base0, 0)
            if any(osc for _, _, _, _, osc in fl["pezzi"]):
                raise Malformata(
                    f"flusso {sid}: un intervallo oscurato su un blocco VIDEO. "
                    f"§11.1 esiste per la parola d'ordine (§4.4); un "
                    f"fotogramma non ha niente da oscurare, e il validatore "
                    f"non puo' giudicare quel che non gli si lascia leggere")

            chiusura = fl["pezzi"][-1][3]
            for nbx, _, _, fx, _ in fl["pezzi"][:-1]:
                if fx != CONTINUA:
                    raise Malformata(
                        f"blocco {nbx}: dichiara `fine = {fx}` ({FINE[fx]}) ma "
                        f"sullo stream {sid} arrivano altri blocchi dopo.  "
                        f"⛔ Uno stream si chiude una volta sola")

            g = f24.Giudice(ctx, dove="uni")
            # ⛔ IL RESET VINCE SULL'INTESTAZIONE — §6.2, rilievo R1.7: i byte
            #    di un'intestazione troncata possono essere qualunque cosa, e
            #    leggerli darebbe `ERRORE_PROTOCOLLO` su un abbandono legale.
            if chiusura == RESET:
                v = g.finisce("reset")
            else:
                for _, _, car, _, _ in fl["pezzi"]:
                    g.arrivano(car)
                    if g.verdetto is not None:
                        break
                if g.verdetto is not None:
                    v = g.verdetto
                elif chiusura == CONTINUA:
                    # ⛔ `fine = 0` sull'ultimo blocco: lo stream non si chiude
                    #    dentro il file, quindi la COMPLETEZZA non si giudica —
                    #    e si dichiara invece di darla per buona.
                    print(f"   flusso {sid}: {g.byte_dati} byte di dati e "
                          f"`fine = 0` sull'ultimo blocco — ⛔ la completezza "
                          f"NON si giudica (§6.2)")
                    continue
                else:
                    v = g.finisce("fin")
            if v.esito == f24.ERRORE_PROTOCOLLO:
                rel = v.scostamento if v.scostamento is not None else 0
                raise NonConforme(v.regola, f"flusso {sid}: {v.dice}",
                                  base0 + rel, rel)
            print(f"   flusso {sid}: {v.esito:<18s} {v.dice}")

    # ⛔ E «CONFORME» SI DICE CON IL DENOMINATORE, O NON SI DICE.
    print(f"\n   guardati: {visti} blocchi, di cui {di_controllo} sul canale di "
          f"controllo e {di_video} sul canale video · {messaggi} messaggi "
          f"letti, {giudicati} col corpo giudicato · {flussi_video} flussi "
          f"video")
    # ⛔ E DAL 12 AGOSTO 2026 «NIENTE DA GIUDICARE» VUOLE **DUE** ZERI.
    #
    #    Prima bastava `messaggi == 0`, perche' il video non lo guardava
    #    nessuno: una registrazione di soli fotogrammi usciva 3 ed era la
    #    verita'.  ⛔ Oggi quei fotogrammi sono l'oggetto del giudizio, e
    #    uscire 3 sarebbe assolvere senza aver guardato — la stessa cosa che
    #    il codice 3 esiste per impedire.
    if messaggi == 0 and flussi_video == 0:
        raise NienteDaGiudicare(
            f"{visti} blocchi, {di_controllo} sul canale di controllo e "
            f"{di_video} sul canale video, ZERO messaggi di controllo e ZERO "
            f"flussi video")
    print(f"   ⭐ conforme: nessuna violazione in {messaggi} messaggi e "
          f"{flussi_video} flussi video")
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
    except NonHoPotutoGuardare as e:
        # ⛔ Stesso codice della malformata — nessuno dei due e' un giudizio sul
        #    filo — ma un'altra frase: li' si guarda il file, qui l'attrezzo.
        print(f"\n   ⚠ NON HO POTUTO GUARDARE: {e}")
        print("      ⛔ Non e' un giudizio sul filo e non e' «il file e' rotto»:")
        print("         manca lo STRUMENTO.  ⚠ E non e' «va bene»: e' la forma")
        print("         E8, «vuoto» e «proibito» con lo stesso aspetto.")
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
