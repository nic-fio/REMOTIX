#!/usr/bin/env python3
"""01-b9-letture.py — ⭐ B9: i punti in cui `RCP.md` ammetteva DUE letture.

    python3 01-b9-letture.py                 l'inventario, con i byte a confronto
    python3 01-b9-letture.py --byte          e stampa gli esadecimali per esteso
    python3 01-b9-letture.py --elenco        solo i titoli, senza costruire niente

⚠ Gira DOVUNQUE: non tocca la rete e non vuole un server.  Legge due file —
  `RCP.md` e `01-b3-cliente.py` — e costruisce byte.  Il pezzo che vuole un
  server e' un altro file, `01-b9-sonda.py`, e dice quale delle due letture ha
  scelto il SERVER.

===========================================================================
⛔ CHE COSA E' QUESTO BANCO, E PERCHE' NON HA UN «PASSA»

`fasi/01-filo-nudo.md` B9, ultima riga della tabella:

    ⚠ **l'esito piu' prezioso non e' «passa»**: e' **ogni punto in cui chi lo
      scrive ha dovuto scegliere** perche' `RCP.md` ammetteva due letture.
      Quei punti vanno in «che cosa NON ha funzionato», e sono difetti **del
      documento**.

⛔ Da cui la forma di questo file: **non e' un banco che promuove il cliente di
   prova**, e' un banco che **conta i punti in cui il documento non decideva**.
   Il numero che consegna e' quello, e il verde qui sotto vuol dire soltanto
   *«l'inventario e' intero e ogni voce regge»*, mai *«RCP e' senza ambiguita'»*.

⭐ E ogni voce porta **il byte che cambia sul filo fra le due letture**, non una
   spiegazione: se due letture producessero gli stessi byte non sarebbero due
   letture, sarebbero due modi di dire la stessa cosa.  ⛔ Questo file lo
   **verifica**, voce per voce (`controlla_byte`), e una voce i cui due byte
   combaciano e' un difetto **di questo banco** — diventa rossa.

===========================================================================
⛔ LO STATO INIZIALE, E QUI E' DI CARTA (B0.1)

Un banco che legge dei documenti ha per stato iniziale **il testo che ha
letto**.  `RCP.md` e `01-b3-cliente.py` cambiano sotto i piedi — li scrivono
altri, anche stanotte — e una voce che cita una riga sparita starebbe
descrivendo un documento che non esiste piu'.

⛔ Da cui: ogni voce dichiara i suoi **appigli** — pezzi di testo esatti che
   devono comparire nei due file — e il banco li cerca **prima** di dare
   qualunque verdetto.  Un appiglio che non si trova NON e' «la voce e'
   sbagliata»: e' `[?]` **il documento e' cambiato sotto il banco**, che e' una
   terza cosa e ha una cura diversa (rileggere, non correggere).

⚠ E i due file si cercano **accanto a questo**, cioe' nella copia che sta
  girando: leggere un `RCP.md` di un'altra copia direbbe di un documento che
  non e' quello contro cui il cliente di prova e' stato scritto.

===========================================================================
⛔ IL DENOMINATORE, E LE QUATTRO COLONNE CHE NON SONO LA STESSA COSA

  VOCI          quante volte il documento ammetteva due letture;
  CON APPIGLI   di quelle, quante si sono potute **verificare sul testo** oggi;
  SUL FILO      di quelle, quante producono **byte diversi** — cioe' quante un
                banco puo' andare a guardare;
  PROVATE       ⛔ di quelle, quante sono state misurate **sul comportamento**
                del cliente di prova invece che sulla sua citazione.  E' la
                colonna nata dal rilievo A8 (11 agosto 2026): un appiglio si
                puo' lasciare in piedi mentre il comportamento cambia, e per
                una notte questo banco e' stato verde su un cliente che aveva
                gia' cambiato lettura.  Il riquadro sta sopra `estrai_funzioni`.

⛔ Le tre non coincidono mai, e stamparne una sola sarebbe la forma di
   `LEZIONI.md` §1.9: *«il verdetto su zero cose»* e *«il denominatore falso»*.
   La voce **R3.27** e' quella che lo dimostra: e' una vera ambiguita', e sul
   filo **non cambia nessun byte della richiesta** — cambia *quando* arriva il
   `CONGEDO`, e nel caso peggiore *se* arriva.  E' dichiarata cosi', invece di
   essere gonfiata con un byte inventato per far tornare la colonna.

===========================================================================
⛔ IL MECCANISMO DI B9, E QUESTO FILE NON LO PUO' GARANTIRE

`fasi/01-filo-nudo.md` B9: la separazione fra chi scrive il cliente di prova e
chi scrive il server **dev'essere un meccanismo, non una regola** — *«chi
scrive il cliente riceve `RCP.md` e i suoi riferimenti, e non l'albero del
server e della pagina»*.

⚠ **Questo file non e' quel meccanismo e non lo dimostra.**  Dice solo che cosa
  il cliente di prova ha scelto, leggendo il cliente di prova.  ⛔ Se chi lo ha
  scritto avesse guardato `rcp/rcp.c`, le scelte combacerebbero con quelle del
  server **e questo file stamperebbe le stesse righe**: la concordanza non
  saprebbe distinguere «hanno letto lo stesso documento» da «hanno copiato».
  E' il guasto **B9** che B12 costruisce apposta (*«il cliente di prova che ha
  letto il C»*), e senza quello questa riga resta una dichiarazione.

===========================================================================
⭐ E LE DUE VOCI CHE VALGONO PIU' DELLE ALTRE

  L4  la coda di byte in fondo al corpo: il **cliente di prova** la tollera e
      il **validatore di B4** la rifiuta.  Sono i nostri due lettori indipendenti
      di §6.1, e hanno letto **due cose diverse** — cioe' esattamente l'oggetto
      che B9 esiste per produrre, trovato in casa e non in teoria;

  L11 la versione nel `CIAO` quando il percorso e' `/rcp/1`: §9 ordina di
      dichiarare **la piu' alta che si sa parlare**, §2.2 dice che una versione
      diversa dal percorso e' `VERSIONE_INCOMPATIBILE`.  Per un client che
      parlasse 1 **e** 2 le due righe ordinano il contrario, e oggi non morde
      solo perche' RCP/2 non esiste.
"""
import argparse
import ast
import hashlib
import os
import struct
import sys

QUI = os.path.dirname(os.path.abspath(__file__))


def cerca_in_su(nome, da):
    """Cerca `nome` risalendo le cartelle.  ⛔ Restituisce None se non c'e'.

    ⚠ Non e' comodita': B12 fa girare una COPIA di questo banco dentro
      `01-b12-copie/`, cioe' una cartella piu' in giu' — e un percorso calcolato
      con un solo `dirname` porterebbe a un `RCP.md` che non c'e'.  Il banco
      uscirebbe «non ho potuto leggere» **mentre B12 sta misurando tutt'altro**,
      e la certificazione registrerebbe un rosso della causa sbagliata.
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


RADICE = os.path.dirname(QUI)
RCP_MD = cerca_in_su("RCP.md", QUI) or os.path.join(RADICE, "RCP.md")
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
# I mattoni del filo, riscritti QUI e non importati dal cliente di prova.
#
# ⛔ Non e' duplicazione per distrazione: se questo file importasse `inquadra()`
#    dal cliente, le due letture di §6.1 uscirebbero **tutt'e due** dalla
#    lettura del cliente, e la voce L4 confronterebbe il cliente con se stesso.
#    I byte delle due letture si costruiscono a mano, dal documento.
# ===========================================================================
def u16(v):
    return struct.pack("!H", v)


def u32(v):
    return struct.pack("!I", v)


def stringa(t):
    """§6.0: `u16 lunghezza` + `lunghezza` byte di UTF-8, senza terminatore."""
    b = t.encode("utf-8") if isinstance(t, str) else t
    return u16(len(b)) + b


def inquadratura(tipo, corpo, lunghezza=None):
    """§6.1: `u16 tipo` · `u32 lunghezza` · corpo.

    `lunghezza` si puo' forzare: serve alla voce L4, dove il punto e' proprio
    che il numero dichiarato e quel che il tipo prevede non coincidono.
    """
    return u16(tipo) + u32(len(corpo) if lunghezza is None else lunghezza) + corpo


def capacita(voci):
    out = u16(len(voci))
    for n, v in voci:
        out += stringa(n) + stringa(v)
    return out


def ciao(versione=1, voci=None):
    voci = voci if voci is not None else [
        ("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
        ("audio.codec", "opus,pcm"), ("client.nome", "cliente-di-prova 0.1.0")]
    return inquadratura(0x0001, u16(versione) + capacita(voci))


def eccomi(voci):
    return inquadratura(0x0002, u16(1) + capacita(voci))


def capsula_chiusura(codice, larghezza=4, dentro_data=True):
    """La capsula `CLOSE_WEBTRANSPORT_SESSION` (0x2843), come la vede il filo.

    ⚠ Il tipo e la lunghezza sono interi variabili di QUIC: `0x2843` sta su due
      byte con i due bit alti a `01`, cioe' `0x68 0x43`.
    """
    corpo = codice.to_bytes(larghezza, "big")
    capsula = b"\x68\x43" + bytes([len(corpo)]) + corpo
    if not dentro_data:
        return capsula
    # RFC 9297: sul filo della CONNECT le capsule viaggiano dentro i frame DATA
    return b"\x00" + bytes([len(capsula)]) + capsula


# ===========================================================================
# L'INVENTARIO.
#
# ⛔ Ogni voce dichiara i suoi APPIGLI prima di dichiarare la sua tesi: una
#    citazione che non si trova piu' e' una voce che parla di un altro
#    documento, e va detto invece di essere creduta.
# ===========================================================================
VOCI = []


def voce(sigla, dove, domanda, lettura_a, lettura_b, scelta, morde,
         appigli_rcp=(), appigli_cliente=(), byte=None, nota=""):
    VOCI.append({
        "sigla": sigla, "dove": dove, "domanda": domanda,
        "a": lettura_a, "b": lettura_b, "scelta": scelta, "morde": morde,
        "appigli_rcp": list(appigli_rcp),
        "appigli_cliente": list(appigli_cliente),
        "byte": byte, "nota": nota,
    })


# ── L1 ──────────────────────────────────────────────────────────────────────
voce(
    "L1", "§4.3",
    "`ECCOMI` porta l'ELENCO dei codec del server, o LA SCELTA?",
    "A — l'elenco: §4.3 dice «capacita' del server», e la scelta viaggia solo "
    "nel registro del server e poi nel campo `codec` dell'intestazione del "
    "fotogramma (§6.2)",
    "B — la scelta: §4.3 dice «Chi sceglie e' il server», e l'unico posto in "
    "cui il client potrebbe leggerla e' questa capacita'",
    "il cliente di prova **non legge nessuna capacita' di `ECCOMI`**: legge i "
    "due byte della versione e butta il resto.  E' la lettura A per omissione, "
    "cioe' la scelta fatta senza accorgersi di sceglierla",
    "alla fase 2, sul primo fotogramma: un client che avesse letto B "
    "configurerebbe il decodificatore sul primo elemento dell'elenco e "
    "indovinerebbe **finche' l'ordine del server coincide con l'intersezione**. "
    "Il sintomo, lontano da qui, e' «il browser non apre il flusso» — lo stesso "
    "del rilievo O12 su `video.livello`",
    appigli_rcp=[
        "| **ECCOMI** | server → client. Versione scelta, capacità del server |",
        "⛔ **Chi sceglie è il server**, dentro l'intersezione",
        "La scelta **DEVE** essere scritta nel registro del server",
    ],
    appigli_cliente=['versione = struct.unpack("!H", corpo[:2])[0]'],
    byte=lambda: (
        eccomi([("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
                ("audio.codec", "opus,pcm")]),
        eccomi([("video.codec", "hevc"), ("video.profondita", "8"),
                ("audio.codec", "opus")]),
        "il valore di `video.codec` dentro `ECCOMI`: `0008 «hevc,av1»` contro "
        "`0004 «hevc»` — e con lui la `lunghezza` u32 dell'inquadratura",
    ),
)

# ── L2 ──────────────────────────────────────────────────────────────────────
voce(
    "L2", "§3.1 punto 3",
    "Il «codice d'errore applicativo pari al codice del motivo» quanto e' "
    "largo, e ci va il motivo nudo o il motivo mappato?",
    "A — il motivo nudo dentro i 32 bit della capsula: `00 00 00 0D`",
    "B — il motivo trasformato dalla mappatura che WebTransport su HTTP/3 "
    "impone ai codici d'errore, che sparpaglia i valori bassi su tutto lo "
    "spazio di HTTP/3",
    "il cliente di prova legge **l'ultimo dei quattro byte** e lo prende per il "
    "motivo (`_capsula_chiusura`, `return b[j + 3]`): e' la lettura A, **e in "
    "piu' tronca** — un codice sopra 255 gli arriverebbe come un altro motivo, "
    "senza una riga che lo dica",
    "il giorno in cui un'implementazione applicasse la mappatura, il motivo "
    "arriverebbe come un numero enorme e il lettore ne stamperebbe il byte "
    "basso: **un motivo sbagliato invece di un errore**, che e' peggio di un "
    "silenzio (§3.1: «il terzo punto e' quello che salva le diagnosi»)",
    appigli_rcp=[
        "**DEVE** chiudere la **sessione WebTransport** con il codice d'errore "
        "applicativo pari al\n   **codice del motivo** di §8.2",
    ],
    appigli_cliente=["return b[j + 3]      # i quattro byte del codice, il piu' basso"],
    byte=lambda: (
        capsula_chiusura(0x0D),
        capsula_chiusura(0x52E4A40FA8DB + 0x0D, larghezza=8),
        "i byte del codice dentro la capsula `0x2843`: `00 00 00 0D` contro "
        "otto byte di un valore mappato — e la capsula stessa cambia lunghezza",
    ),
    nota="⚠ `RCP.md` non dichiara la larghezza del campo in nessun punto: la "
         "dichiara solo il formato di WebTransport, che RCP non nomina.",
)

# ── L3 ──────────────────────────────────────────────────────────────────────
voce(
    "L3", "§3.1 punto 2 contro §4.2",
    "Dopo il `CONGEDO`, il canale di controllo si chiude con un FIN, oppure "
    "si chiude solo la sessione?",
    "A — `CONGEDO` **con** il FIN sul canale di controllo, poi la chiusura "
    "della sessione: §4.2 dice che il FIN su quello stream **e'** la fine "
    "della sessione, quindi e' il modo piu' esplicito di dirla",
    "B — `CONGEDO` **senza** FIN, e la fine la dichiara solo la chiusura della "
    "sessione (§3.1 punto 3)",
    "il cliente di prova non manda mai un `CONGEDO`; e quando spedisce "
    "qualunque cosa usa `end_stream=False`, cioe' la lettura B.  ⛔ E dal lato "
    "che riceve chiama il FIN «il canale di controllo si e' chiuso», che e' un "
    "esito **diverso** da «sessione chiusa dal server»",
    "chi aspetta il FIN per dichiarare finita la sessione resta appeso contro "
    "chi chiude solo la sessione; e chi manda il FIN **prima** della chiusura "
    "fa scattare §4.2 per primo, cosi' il pari registra «canale chiuso» invece "
    "del motivo.  E' la stessa famiglia del rilievo R1.4, sullo stesso punto",
    appigli_rcp=[
        "⛔ **In byte**: un FIN su quello stream, da una qualunque delle due parti, "
        "chiude la sessione.",
        "**DEVE** mandare `CONGEDO` (§8) con il motivo, sul canale di controllo",
    ],
    appigli_cliente=[
        "self._quic.send_stream_data(self.controllo, dati, end_stream=False)",
        'self._cade("il canale di controllo si e\' chiuso")',
    ],
    byte=lambda: (
        inquadratura(0x000C, bytes([0x01]) + stringa("")) + b"<FIN>",
        inquadratura(0x000C, bytes([0x01]) + stringa("")),
        "il bit FIN del frame STREAM che porta il `CONGEDO` — gli stessi byte "
        "di carico, un bit di trasporto in piu'",
    ),
    nota="⚠ Il `<FIN>` qui sopra e' scritto in chiaro perche' NON e' un byte "
         "del carico: e' un bit dell'intestazione del frame STREAM di QUIC, e "
         "fingere di poterlo stampare come carico sarebbe una bugia comoda.",
)

# ── L4 ──────────────────────────────────────────────────────────────────────
voce(
    "L4", "§6.1",
    "⭐ Byte in piu' in fondo al corpo, con la `lunghezza` che li conta: sono "
    "una violazione o sono riserva per le versioni future?",
    "A — violazione: §6.1 vuole che `lunghezza` sia «il numero esatto dei byte "
    "del corpo», e un corpo piu' lungo di quel che il tipo prevede e' «una "
    "lunghezza incoerente con quel che il tipo prevede» ⇒ `ERRORE_PROTOCOLLO`",
    "B — riserva: `lunghezza` e' autorevole, si leggono i campi che il tipo "
    "dichiara e il resto si salta.  E' l'unico modo in cui §9 potrebbe "
    "allargare un messaggio senza cambiare versione maggiore",
    "⛔ **I nostri due lettori hanno scelto diversamente**: il cliente di prova "
    "legge `lunghezza` byte e passa il corpo cosi' com'e' senza mai verificare "
    "di averlo consumato tutto (lettura B, tollerante); il validatore di B4 ha "
    "una registrazione apposta — `10-coda-di-spazzatura.rcpreg` — cioe' la "
    "lettura A",
    "e' il difetto che questo banco esiste per trovare: **l'arbitro e il "
    "secondo lettore non leggono la stessa specifica**.  Finche' nessuno manda "
    "byte in piu' non succede niente; il giorno in cui succede, uno dei due "
    "dice conforme e l'altro chiude la connessione",
    appigli_rcp=[
        "⛔ `lunghezza` **DEVE** essere il numero esatto dei byte del corpo.",
        "Un ricevente che legge una\nlunghezza incoerente con quel che il tipo "
        "prevede **DEVE** chiudere con `ERRORE_PROTOCOLLO`.",
    ],
    appigli_cliente=[
        'tipo, lung = struct.unpack("!HI", self.arrivati[:6])',
        "corpo = bytes(self.arrivati[6:6 + lung])",
    ],
    byte=lambda: (
        (lambda c: inquadratura(0x0001, c))(u16(1) + capacita(
            [("audio.codec", "opus,pcm"), ("video.profondita", "8")])),
        (lambda c: inquadratura(0x0001, c + b"\xDE\xAD\xBE\xEF"))(u16(1) + capacita(
            [("audio.codec", "opus,pcm"), ("video.profondita", "8")])),
        "quattro byte in coda al corpo e la `lunghezza` u32 piu' alta di "
        "quattro: `0000002A` contro `0000002E`",
    ),
)

# ── L5 ──────────────────────────────────────────────────────────────────────
voce(
    "L5", "§4.3",
    "Una capacita' **assente** e' un elenco vuoto o una cosa non negoziata?",
    "A — assente = elenco vuoto: l'intersezione e' vuota, e §4.3 impone "
    "`NIENTE_IN_COMUNE`",
    "B — assente = non negoziata: la riga che obbliga riguarda solo `pcm` e "
    "`8`, e per il resto chi tace non ha chiesto niente",
    "il cliente di prova dichiara **sempre** tutte e otto le capacita', quindi "
    "⚠ **non ha scelto: ha evitato la domanda**.  E averla evitata vuol dire "
    "che nessuna delle sue esecuzioni la fara' mai emergere",
    "il primo client altrui che tacesse su `video.codec` — perche' non decodifica "
    "video, per esempio un client di soli appunti — riceverebbe `NIENTE_IN_COMUNE` "
    "o entrerebbe, a seconda di chi ha scritto il server, e nessuno dei due "
    "sarebbe fuori specifica",
    appigli_rcp=[
        "⛔ Se l'intersezione di `video.codec` è **vuota**, il server **DEVE** "
        "congedare con\n`NIENTE_IN_COMUNE`.",
        "⚠ Ma se **dopo lo scarto l'elenco resta vuoto**, si congeda con "
        "`NIENTE_IN_COMUNE`",
    ],
    appigli_cliente=['("video.codec", "hevc,av1"), ("video.profondita", "8,10")'],
    byte=lambda: (
        ciao(voci=[("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
                   ("audio.codec", "opus,pcm")]),
        ciao(voci=[("video.profondita", "8,10"), ("audio.codec", "opus,pcm")]),
        "il campo `quante` dell'elenco delle capacita': `0003` contro `0002`, e "
        "ventidue byte in meno",
    ),
)

# ── L6 ──────────────────────────────────────────────────────────────────────
voce(
    "L6", "§4.6 riga 1  ·  la `[?]` R3.27",
    "Da quale istante parte il primo tetto: la fine del TLS, l'apertura della "
    "sessione WebTransport, o l'apertura del canale di controllo?",
    "A — la fine del TLS, alla lettera di §4.6",
    "B — l'apertura della sessione, o del canale: sono gli istanti che il "
    "server puo' davvero osservare, e fra il TLS e la sessione passa almeno un "
    "giro di rete",
    "il cliente di prova non ha dovuto scegliere — non misura tetti.  ⛔ **Ha "
    "scelto B6**, che il cronometro lo fa partire dall'apertura del canale, e "
    "questa voce e' li' per dichiarare che quella scelta e' del banco e non del "
    "documento",
    "una sessione aperta e un canale di controllo **mai aperto**: alla lettera "
    "di A il tetto e' gia' scaduto e la connessione dev'essere finita; alla "
    "lettura B non le sta addosso nessun tetto e **resta li'**, che e' proprio "
    "la cosa che §4.6 esiste per impedire",
    appigli_rcp=[
        "| stretta di mano TLS finita | `CIAO` ricevuto | **5 s** |",
    ],
    byte=None,
    nota="⛔ **Nessun byte cambia**, e va detto invece di inventarne uno: le "
         "due letture mandano lo stesso `CIAO` (o lo stesso silenzio).  Cambia "
         "**quando** arriva il `CONGEDO(TEMPO_SCADUTO)`, e nel caso della "
         "sessione senza canale cambia **se** arriva.  E' la voce che tiene "
         "onesta la colonna «sul filo».",
)

# ── L7 ──────────────────────────────────────────────────────────────────────
voce(
    "L7", "§2.2",
    "La CONNECT estesa che apre la sessione deve portare un `origin`?",
    "A — si': ogni browser lo manda, e un server che lo controlla e' conforme "
    "perche' RCP non gli vieta di controllarlo",
    "B — no: §2.2 detta il **percorso** e nient'altro dell'intestazione, "
    "quindi l'`origin` non e' di RCP",
    "il cliente di prova **lo manda**, copiando il browser.  ⚠ E' una scelta "
    "prudente che ha un prezzo: mandandolo, il cliente di prova **non puo' piu' "
    "scoprire** se il server lo pretende — l'arbitro si e' adattato all'imputato",
    "il primo client che non sia un browser: se il server controlla l'`origin`, "
    "quel client si vede rifiutare la CONNECT e la diagnosi che ne esce e' uno "
    "stato HTTP, cioe' fuori da RCP e fuori da tutti i motivi di §8.2",
    appigli_rcp=[
        "| **l'indirizzo della sessione** | `https://<host>:<porta>/rcp/1` |",
        "⛔ **Il server NON DEVE accettare una sessione WebTransport su un percorso "
        "diverso.**",
    ],
    appigli_cliente=['(b"origin", f"https://{autorita}".encode()),'],
    byte=lambda: (
        b":method CONNECT\n:protocol webtransport\n:path /rcp/1\n"
        b"origin https://192.168.0.2:7447\n",
        b":method CONNECT\n:protocol webtransport\n:path /rcp/1\n",
        "il campo `origin` dentro l'intestazione della CONNECT estesa — una "
        "riga di intestazione in piu', compressa da QPACK",
    ),
    nota="⚠ I due blocchi qui sopra sono i campi **prima** di QPACK: stamparli "
         "compressi darebbe due stringhe che dipendono dalla tabella dinamica, "
         "cioe' due numeri che non si possono confrontare.",
)

# ── L8 ──────────────────────────────────────────────────────────────────────
voce(
    "L8", "§4.5",
    "Un `desktop` fuori dai sei nomi: e' un campo fuori intervallo (§3) o e' "
    "una stringa di diagnosi da non guardare?",
    "A — §3 si applica: «un campo fuori intervallo» e' nell'elenco di §3, "
    "quindi il client chiude con `ERRORE_PROTOCOLLO`",
    "B — non si guarda: §4.5 dice, nello stesso paragrafo, che il client **NON "
    "DEVE** cambiare comportamento in base al suo valore",
    "il cliente di prova lo stampa e non lo controlla: lettura B",
    "il giorno in cui il server imparasse un settimo desktop — o scrivesse "
    "`plasma6` invece di `kde` — meta' delle implementazioni chiuderebbe la "
    "sessione appena aperta.  ⚠ Le due letture stanno in **sei righe**, una "
    "sotto l'altra, e sono opposte",
    appigli_rcp=[
        "└── stringa desktop             uno fra: gnome · kde · xfce · lxqt · "
        "cinnamon · sconosciuto",
        "Il campo `desktop` è per la diagnosi: il client\n**NON DEVE** cambiare "
        "comportamento in base al suo valore",
    ],
    appigli_cliente=['desktop = corpo[11:11 + n].decode()'],
    byte=lambda: (
        inquadratura(0x0007, bytes([1]) + u32(1920) + u32(1080) + stringa("gnome")),
        inquadratura(0x0007, bytes([1]) + u32(1920) + u32(1080) + stringa("plasma6")),
        "la stringa `desktop` in fondo a `SESSIONE`: `0005 «gnome»` contro "
        "`0007 «plasma6»` — e la connessione che sopravvive o cade",
    ),
)

# ── L9 ──────────────────────────────────────────────────────────────────────
voce(
    "L9", "§11.1 contro §6.0",
    "Nel blocco della registrazione, che cosa si scrive in `stream` quando "
    "l'identificatore non si conosce?",
    "A — l'identificatore vero, sempre: §11.1 dice «l'identificatore dello "
    "stream QUIC» e non prevede un caso in cui manchi",
    "B — zero, come «assente»",
    "⛔ il cliente di prova scrive **sempre zero** — "
    "`struct.pack(\"!BBQIH\", verso, 0x00, 0, ...)` — cioe' la lettura B.  Ma "
    "§6.0 vieta esattamente questo: *«ogni intero ha un solo significato di "
    "«assente», e va dichiarato dove serve: non esistono valori sentinella "
    "impliciti»*, e **zero e' un identificatore di stream legale** (e' quello "
    "della CONNECT)",
    "chi legge la registrazione per capire su quale stream e' passato un "
    "messaggio legge zero e crede allo zero.  ⚠ E il validatore non se ne puo' "
    "accorgere: un campo che vale sempre zero e un campo assente hanno lo "
    "stesso aspetto — la forma E8",
    appigli_rcp=[
        " ├── u64      stream         l'identificatore dello stream QUIC",
        "⛔ **Ogni intero ha un solo significato di «assente»**, e va dichiarato "
        "dove serve: non esistono valori sentinella impliciti.",
    ],
    appigli_cliente=['out += struct.pack("!BBQIH", verso, 0x00, 0, len(carico), len(osc))'],
    byte=lambda: (
        struct.pack("!BBQIH", 1, 0x00, 4, 12, 0),
        struct.pack("!BBQIH", 1, 0x00, 0, 12, 0),
        "gli otto byte di `stream` in testa a ogni blocco: "
        "`00 00 00 00 00 00 00 04` contro `00 00 00 00 00 00 00 00`",
    ),
)

# ── L10 ─────────────────────────────────────────────────────────────────────
voce(
    "L10", "§8.1 contro §4.4",
    "Il client, quando chiude, DEVE mandare `CONGEDO`: e dopo un `RESPINTO`?",
    "A — si', ed e' l'unica cosa che gli resta da dire: la regola di §4.4 "
    "vieta di **riprovare**, non di congedarsi",
    "B — no: dopo `RESPINTO` la sessione e' finita per il server, e ogni byte "
    "che arriva dopo e' byte di troppo",
    "il cliente di prova **non manda mai un `CONGEDO`, in nessun caso**: chiude "
    "e basta.  ⚠ Non e' la lettura B — e' la terza, «non applico §8.1 a me "
    "stesso», e vuol dire che il secondo lettore **non esercita mai** l'obbligo "
    "che §8.1 mette su chi chiude",
    "il caso e' gia' costato un rosso: il server contava come «byte dopo la "
    "fine» anche il congedo conforme della pagina, e B11 ha messo un rosso "
    "addosso alla pagina mentre faceva quel che §8.1 le impone (§4.4, riquadro "
    "del 10 agosto 2026)",
    appigli_rcp=[
        "⛔ **E dopo `RESPINTO` al client resta una cosa sola che può dire: "
        "`CONGEDO`.**",
        "⛔ Chi chiude **DEVE** mandare `CONGEDO` con un motivo **prima** di "
        "chiudere la **sessione",
    ],
    byte=lambda: (
        inquadratura(0x000C, bytes([0x01]) + stringa("")),
        b"",
        "un'inquadratura di undici byte contro **niente**: `000C 00000003 01 "
        "0000` contro il silenzio",
    ),
)

# ── L11 ─────────────────────────────────────────────────────────────────────
voce(
    "L11", "§9 contro §2.2",
    "⭐ Che versione mette nel `CIAO` un client che ne sa parlare DUE, su un "
    "percorso `/rcp/1`?",
    "A — **2**: §9 dice «`CIAO` porta la versione maggiore che il client sa "
    "parlare», senza condizioni",
    "B — **1**: §2.2 dice che le due DEVONO coincidere, e un `CIAO(2)` su "
    "`/rcp/1` e' `VERSIONE_INCOMPATIBILE`",
    "il cliente di prova scrive `1` a mano, perche' ne sa parlare una sola: "
    "⚠ **la domanda non gli si e' posta**, e non se la porra' finche' RCP/2 "
    "non esistera'",
    "il primo client che parli 1 e 2: seguendo §9 dichiara 2 su `/rcp/1` e si "
    "fa congedare; seguendo §2.2 dichiara 1 e **non potra' mai negoziare la "
    "versione piu' alta**, perche' l'unico posto in cui la puo' chiedere e' il "
    "percorso, che pero' e' quello che sta gia' usando.  ⛔ Le due righe non si "
    "citano a vicenda, ed e' la forma esatta del rilievo R1.2",
    appigli_rcp=[
        "`CIAO` porta la versione maggiore che il client sa parlare; `ECCOMI` "
        "quella scelta dal server.",
        "⛔ **E le due DEVONO coincidere**: un `CIAO(versione=2)` su `/rcp/1` è "
        "`VERSIONE_INCOMPATIBILE`",
    ],
    appigli_cliente=['out = struct.pack("!HH", 1, len(voci))'],
    byte=lambda: (
        ciao(versione=2),
        ciao(versione=1),
        "i due byte di `versione` in testa al corpo del `CIAO`: `0002` contro "
        "`0001` — due byte, e una connessione che vive o muore",
    ),
)

# ── L12 ─────────────────────────────────────────────────────────────────────
voce(
    "L12", "§4.5 contro §7.1",
    "I limiti 320×240-7680×4320 e la parita' valgono anche per `vista_*` "
    "dentro `ATTACCA`?",
    "A — si': §4.5 detta i limiti a due righe dal disegno che contiene "
    "`vista_larghezza` e `vista_altezza`, e non distingue",
    "B — no: la vista non ha i vincoli della tela, «qualunque misura da 1×1 in "
    "su e' legale, dispari compresa»",
    "il cliente di prova manda **vista = tela** (`--larghezza`/`--altezza` per "
    "tutti e quattro i campi): ⚠ ancora una volta la domanda evitata, non "
    "risposta",
    "una finestra stretta a 300 pixel — il caso concreto che il rilievo R1.17 "
    "descrive — passa o fa cadere la sessione a seconda di chi ha scritto il "
    "server.  ⭐ **La risposta esiste** ed e' B, ma sta in §7.1, cioe' nella "
    "sezione del messaggio `VISTA`: chi implementa `ATTACCA` leggendo §4.5 non "
    "ha nessun motivo di andarci",
    appigli_rcp=[
        "⛔ **I limiti, e sono normativi**: larghezza e altezza della tela "
        "**DEVONO** stare fra **320×240** e",
        "⛔ **La vista non ha i vincoli della tela**",
    ],
    appigli_cliente=[
        'struct.pack("!IIII", a.larghezza, a.altezza,\n                                     a.larghezza, a.altezza)',
    ],
    byte=lambda: (
        inquadratura(0x0006, u32(1920) + u32(1080) + u32(1920) + u32(1080)
                     + stringa("it")),
        inquadratura(0x0006, u32(1920) + u32(1080) + u32(300) + u32(801)
                     + stringa("it")),
        "gli otto byte di `vista_larghezza` e `vista_altezza`: "
        "`00000780 00000438` contro `0000012C 00000321` — sotto il minimo e "
        "dispari",
    ),
    nota="⚠ Questa e' un'ambiguita' di **collocazione**, non di contenuto: il "
         "documento decide, ma decide in un'altra sezione.  Conta lo stesso, "
         "perche' chi legge §4.5 non sa di dover cercare.",
)


# ===========================================================================
def leggi(percorso):
    """⛔ «Non ho potuto leggere» non e' «non c'e'» (`LEZIONI.md` §1.9)."""
    try:
        with open(percorso, encoding="utf-8") as f:
            return f.read(), None
    except OSError as e:
        return None, f"{type(e).__name__}: {e}"


def normalizza(t):
    """Toglie gli a capo e gli spazi doppi: un appiglio non deve cadere per
    una riga riavvolta a 100 colonne invece che a 98."""
    return " ".join(t.split())


def controlla_byte(v):
    """⛔ Due letture che producono gli stessi byte non sono due letture.

    Restituisce (esito, testo).  `esito` e' uno fra:
      "diversi"      le due letture si vedono sul filo;
      "senza-byte"   la voce dichiara di non cambiare nessun byte (L6);
      "UGUALI"       ⛔ difetto DI QUESTO BANCO: la voce non separa niente.
    """
    if v["byte"] is None:
        return "senza-byte", "nessun byte cambia — dichiarato nella voce"
    a, b, che = v["byte"]()
    if a == b:
        return "UGUALI", ("⛔ le due letture producono gli stessi byte: la voce "
                          "non separa niente")
    return "diversi", che


def esadecimale(b, quanti=48):
    if not isinstance(b, (bytes, bytearray)):
        return str(b)
    t = b[:quanti].hex(" ")
    return t + (f"  … (+{len(b) - quanti} byte)" if len(b) > quanti else "")


# ===========================================================================
# ⛔⭐ LA PROVA DI COMPORTAMENTO — e nasce dal rilievo A8, 11 agosto 2026
# ===========================================================================
# ⛔ CHE COSA NON ANDAVA, E VA LETTO PRIMA DI TOCCARE QUESTA PARTE.
#
# Fino a stanotte questo banco verificava le sue voci in un modo solo: gli
# **appigli**, cioe' pezzi di testo esatti che devono comparire nei due file.
# La revisione R12-A lo ha portato alla lettura opposta e ha lasciato la
# citazione dov'era:
#
#     si cambia il cliente di prova alla **lettura A** — la coda in piu' si
#     TAGLIA — ma si lascia intatta, riga per riga, la stringa che L4 cita
#     (`corpo = bytes(self.arrivati[6:6 + lung])`) e si aggiunge il troncamento
#     nelle righe successive.
#
# ⛔ B9 restava **verde, 12 voci su 12**, e continuava a stampare *«⭐ SCELTO …
#    il cliente di prova legge `lunghezza` byte e passa il corpo cosi' com'e' …
#    (lettura B, tollerante)»* — che a quel punto era **falso**.
#
# ⛔ Quindi il guasto che B12 costruisce per certificare B9 diventava rosso
#    perche' **cancellava una citazione**, non perche' il secondo lettore si
#    fosse allineato al primo: la certificazione dimostrava che B9 sa vedere *un
#    testo cambiato* — che B9 dichiara apertamente di saper fare — e **non** quel
#    che il catalogo di B12 scrive di aver certificato.
#
# ⭐ LA CURA: per le voci in cui la scelta del cliente **si vede sul filo**, la
#    si MISURA invece di citarla.  Si costruiscono qui i byte delle due letture,
#    si danno **al codice vero del cliente di prova**, e si guarda quale delle
#    due esce.  Una citazione la si puo' lasciare in piedi mentre il
#    comportamento cambia; un comportamento no.
#
# ⛔ E PERCHE' QUESTO NON CONTRADDICE IL RIQUADRO IN CIMA («i mattoni del filo
#    si riscrivono qui e non si importano dal cliente»).  Sono due usi opposti:
#    li' il cliente sarebbe stato la **fonte** dei byte, e la voce avrebbe
#    confrontato il cliente con se stesso; qui il cliente e' l'**imputato**, e i
#    byte glieli portiamo noi, costruiti dal documento.  Un banco che porta
#    l'imputato in aula non sta copiando dall'imputato.
#
# ⚠ E si estrae senza IMPORTARE, perche' `01-b3-cliente.py` importa `aioquic`
#   e questo banco «gira DOVUNQUE: non tocca la rete e non vuole un server».
#   Si prendono dal sorgente le funzioni che servono e si compilano da sole.
def estrai_funzioni(testo, nomi):
    """Le funzioni indicate, prese dal sorgente e rese chiamabili.

    Restituisce `(spazio, errore)`: uno dei due e' sempre `None`.
    ⛔ Se una funzione non c'e' piu' NON si finge di averla provata: e' la
       stessa terza cosa degli appigli — «il testo e' cambiato sotto il banco»."""
    try:
        albero = ast.parse(testo)
    except SyntaxError as e:
        return None, f"il cliente di prova non si compila: {e}"
    # ⛔ Si prendono TUTTE le funzioni di primo livello del cliente, non solo
    #    quelle chieste: una funzione che ne chiama un'altra e non la trova
    #    solleverebbe `NameError`, e un `NameError` ha la stessa faccia di «il
    #    lettore ha rifiutato l'inquadratura» — cioe' la prova direbbe «lettura
    #    A» avendo misurato la mia estrazione invece del cliente.  E' la faccia
    #    comune di vuoto e proibito, spostata dentro il banco.
    presi, visti = [], []
    for nodo in albero.body:
        if isinstance(nodo, ast.FunctionDef):
            presi.append(nodo)
            visti.append(nodo.name)
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.FunctionDef) and nodo.name in nomi \
                and nodo.name not in visti:
            presi.append(nodo)
            visti.append(nodo.name)
    persi = [n for n in nomi if n not in visti]
    if persi:
        return None, (f"non trovo piu' {persi} nel cliente di prova: la prova "
                      f"di comportamento non si puo' fare")
    modulo = ast.Module(body=presi, type_ignores=[])
    ast.fix_missing_locations(modulo)
    spazio = {"struct": struct}
    try:
        exec(compile(modulo, CLIENTE, "exec"), spazio)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        return None, f"le funzioni estratte non si compilano: {e}"
    return spazio, None


class _Coda:
    """Il minimo che `_sfoglia` chiede: un `put_nowait`."""

    def __init__(self):
        self.dentro = []

    def put_nowait(self, x):
        self.dentro.append(x)


class _Finto:
    """Il minimo che `_sfoglia` chiede di `self`: i byte arrivati e la coda."""

    def __init__(self, dati):
        self.arrivati = bytearray(dati)
        self.messaggi = _Coda()


def prova_L4(sp):
    """Il cliente di prova, davanti a byte in piu' in coda al corpo.

    ⛔ E il caso opposto e' scritto, come vuole `LEZIONI.md` §1.11:
       lettura B (tollerante) ⇒ il corpo consegnato e' lungo `lunghezza`, coda
       compresa;  lettura A ⇒ il corpo consegnato e' piu' corto, oppure non
       arriva nessun messaggio perche' il lettore ha rifiutato l'inquadratura."""
    dentro = u16(1) + capacita([("audio.codec", "opus,pcm"),
                                ("video.profondita", "8")])
    con_coda = dentro + b"\xDE\xAD\xBE\xEF"
    byte = inquadratura(0x0001, con_coda)
    c = _Finto(byte)
    try:
        sp["_sfoglia"](c)
    except (NameError, AttributeError) as e:
        # ⛔ Questi due NON sono «il lettore ha rifiutato»: sono «io non ho
        #    portato in aula tutto l'imputato».  Chiamarli lettura A vorrebbe
        #    dire dare a un difetto del banco la faccia di un difetto del
        #    cliente — la settima veste di `LEZIONI.md` §1.9.
        return "?", (f"l'estrazione e' incompleta: `_sfoglia` chiama qualcosa "
                     f"che non ho preso ({type(e).__name__}: {e})")
    except Exception as e:  # noqa: BLE001
        return "A", (f"il lettore ha sollevato {type(e).__name__} sui byte in "
                     f"piu': e' la lettura A (violazione), non la B")
    if len(c.messaggi.dentro) != 1:
        return "?", (f"il lettore ha consegnato {len(c.messaggi.dentro)} "
                     f"messaggi invece di 1: non e' ne' A ne' B, e' un terzo "
                     f"comportamento che nessuna delle due letture descrive")
    _tipo, corpo, _grezzo = c.messaggi.dentro[0]
    if corpo == con_coda:
        return "B", (f"il corpo consegnato e' lungo {len(corpo)} byte — "
                     f"`lunghezza` intera, coda compresa: **lettura B**, "
                     f"tollerante, com'e' scritto nella voce")
    return "A", (f"il corpo consegnato e' lungo {len(corpo)} byte invece di "
                 f"{len(con_coda)}: la coda e' stata TAGLIATA, cioe' **lettura "
                 f"A** — e la voce dice B")


def prova_L2(sp):
    """Il cliente di prova, davanti a un codice di chiusura piu' largo di 4 byte.

    ⛔ Il caso opposto: se un giorno leggesse i codici larghi per intero, la
       riga «e in piu' tronca» della voce sarebbe falsa e andrebbe riscritta."""
    stretto = sp["_capsula_chiusura"](capsula_chiusura(0x0D))
    largo_v = 0x52E4A40FA8DB + 0x0D
    largo = sp["_capsula_chiusura"](capsula_chiusura(largo_v, larghezza=8))
    if stretto[0] != 0x0D:
        return "?", (f"su un codice di 4 byte il lettore torna {stretto[0]!r} "
                     f"invece di 13: non e' piu' la lettura A che la voce "
                     f"descrive")
    if largo[0] == largo_v:
        return "?", (f"su un codice di 8 byte il lettore torna il valore "
                     f"INTERO ({largo_v:#x}): non tronca piu', e la voce va "
                     f"riscritta")
    return "A", (f"codice di 4 byte → {stretto[0]:#04x} (giusto); codice di 8 "
                 f"byte {largo_v:#x} → {largo[0]:#04x} — ⛔ **un motivo "
                 f"diverso**, che e' il danno che la voce descrive")


# (sigla, quali funzioni servono, la prova, che cosa la voce dichiara)
PROVE = [
    ("L4", ("_sfoglia",), prova_L4, "B"),
    ("L2", ("_varint", "_capsula_chiusura"), prova_L2, "A"),
]


def principale(a):
    print("== ⭐ B9 — i punti in cui `RCP.md` ammetteva DUE letture")
    print("   L'esito piu' prezioso di B9 non e' «passa»: e' questo elenco.")
    print("   (fasi/01-filo-nudo.md, B9 · PIANO.md §1.1)\n")

    if a.elenco:
        for v in VOCI:
            print(f"  {v['sigla']:4s} {v['dove']:22s} {v['domanda']}")
        print(f"\n  {len(VOCI)} voci.  Senza --elenco si costruiscono i byte.")
        return 0

    # ── B0.1: lo stato iniziale, che qui e' di carta ───────────────────────
    print("== ⛔ Lo stato iniziale (B0.1): i due testi che questo banco ha letto")
    testi, mancanti = {}, []
    for nome, percorso in (("RCP.md", RCP_MD), ("01-b3-cliente.py", CLIENTE)):
        t, errore = leggi(percorso)
        if t is None:
            print(f"    {ROSSO}NO{GRIGIO}  {nome:18s} {errore}")
            mancanti.append(nome)
        else:
            imp = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
            print(f"    {VERDE}OK{GRIGIO}  {nome:18s} {len(t):7d} byte · "
                  f"impronta {imp}")
            testi[nome] = t
    if mancanti:
        print(f"\n    {ROSSO}⛔ senza i testi non c'e' nessun inventario da "
              f"verificare: non e' un rosso delle voci{GRIGIO}")
        return 4
    print(f"    --  i due percorsi: {RCP_MD}")
    print(f"                        {CLIENTE}")
    print("    ⚠ le impronte servono al prossimo giro: se cambiano e le voci")
    print("      no, qualcuno ha corretto il documento e nessuno ha riletto\n")

    # ── LE VOCI ────────────────────────────────────────────────────────────
    conti = {"voci dell'inventario": [0, 0],
             "voci con TUTTI gli appigli al loro posto": [0, 0],
             "voci che cambiano BYTE sul filo": [0, 0],
             "⛔ voci PROVATE sul comportamento del cliente": [0, 0],
             "⛔ voci che separano davvero le due letture": [0, 0]}
    conti["voci dell'inventario"] = [len(VOCI), len(VOCI)]
    scollegate, rotte, smentite, non_provate = [], [], [], []

    for v in VOCI:
        print(f"== {v['sigla']}  ·  {v['dove']}")
        print(f"   {v['domanda']}")
        print(f"     lettura A   {v['a']}")
        print(f"     lettura B   {v['b']}")
        print(f"     ⭐ SCELTO   {v['scelta']}")
        print(f"     ⛔ MORDE    {v['morde']}")

        # gli appigli
        conti["voci con TUTTI gli appigli al loro posto"][1] += 1
        persi = []
        for testo, quali in ((testi["RCP.md"], v["appigli_rcp"]),
                             (testi["01-b3-cliente.py"], v["appigli_cliente"])):
            n_testo = normalizza(testo)
            for ap in quali:
                if normalizza(ap) not in n_testo:
                    persi.append(ap)
        if persi:
            scollegate.append((v["sigla"], persi))
            print(f"     {GIALLO}[?]{GRIGIO} {len(persi)} appigli su "
                  f"{len(v['appigli_rcp']) + len(v['appigli_cliente'])} non si "
                  f"trovano piu': il testo e' cambiato sotto il banco")
            for ap in persi:
                print(f"          «{normalizza(ap)[:88]}»")
        else:
            conti["voci con TUTTI gli appigli al loro posto"][0] += 1
            n = len(v["appigli_rcp"]) + len(v["appigli_cliente"])
            print(f"     {VERDE}OK{GRIGIO}  {n} appigli su {n} al loro posto "
                  f"nei due testi")

        # i byte
        esito, che = controlla_byte(v)
        conti["⛔ voci che separano davvero le due letture"][1] += 1
        if esito == "diversi":
            conti["voci che cambiano BYTE sul filo"][0] += 1
            conti["voci che cambiano BYTE sul filo"][1] += 1
            conti["⛔ voci che separano davvero le due letture"][0] += 1
            print(f"     {VERDE}BYTE{GRIGIO}  {che}")
            if a.byte:
                x, y, _ = v["byte"]()
                print(f"          A: {esadecimale(x)}")
                print(f"          B: {esadecimale(y)}")
        elif esito == "senza-byte":
            conti["voci che cambiano BYTE sul filo"][1] += 1
            conti["⛔ voci che separano davvero le due letture"][0] += 1
            print(f"     {GIALLO}BYTE{GRIGIO}  {che}")
        else:
            rotte.append(v["sigla"])
            conti["voci che cambiano BYTE sul filo"][1] += 1
            print(f"     {ROSSO}BYTE{GRIGIO}  {che}")
        if v["nota"]:
            print(f"     {v['nota']}")
        print()

    # ── ⛔ LA PROVA DI COMPORTAMENTO (A8) ──────────────────────────────────
    print("== ⛔ La prova di COMPORTAMENTO: il cliente di prova messo davanti "
          "ai byte")
    print("   ⭐ Un appiglio si puo' lasciare in piedi mentre il comportamento "
          "cambia: la")
    print("      revisione R12-A ha portato il cliente alla lettura opposta "
          "lasciando intatta")
    print("      la stringa che L4 cita, e questo banco e' rimasto VERDE.  "
          "Queste righe")
    print("      misurano quale lettura il cliente **esegue**, non quale "
          "citazione porta.")
    for sigla, funzioni, prova, dichiarata in PROVE:
        conti["⛔ voci PROVATE sul comportamento del cliente"][1] += 1
        spazio, errore = estrai_funzioni(testi["01-b3-cliente.py"], funzioni)
        if spazio is None:
            non_provate.append((sigla, errore))
            print(f"   {GIALLO}[?]{GRIGIO} {sigla}: {errore}")
            continue
        vista, perche = prova(spazio)
        if vista == "?":
            # ⛔ «Non l'ho potuta misurare» e' la terza cosa, e ha il suo colore.
            non_provate.append((sigla, perche))
            print(f"   {GIALLO}[?]{GRIGIO} {sigla}: {perche}")
        elif vista == dichiarata:
            conti["⛔ voci PROVATE sul comportamento del cliente"][0] += 1
            print(f"   {VERDE}OK{GRIGIO}  {sigla}: la voce dichiara la lettura "
                  f"{dichiarata} e il cliente ESEGUE la {vista}")
            print(f"          {perche}")
        else:
            smentite.append((sigla, dichiarata, vista, perche))
            print(f"   {ROSSO}NO{GRIGIO}  ⛔ {sigla}: la voce dichiara la "
                  f"lettura {dichiarata}, il cliente ESEGUE «{vista}»")
            print(f"          {perche}")
    print(f"   --  funzioni prese dal sorgente del cliente senza importarlo "
          f"(niente aioquic): "
          f"{', '.join(sorted({f for _s, fs, _p, _d in PROVE for f in fs}))}")
    print()

    # ── IL DENOMINATORE ────────────────────────────────────────────────────
    print("    == quel che questo giro ha davvero guardato")
    # ⛔ Solo l'ultima riga e' un passa/non passa.  Le altre tre sono
    #    DENOMINATORI, e un denominatore che non fa il pieno non e' un rosso:
    #    la riga «cambiano BYTE» non lo fara' mai, perche' L6 dichiara di non
    #    cambiare nessun byte.  Colorarla di rosso insegnerebbe a chi legge che
    #    quel rosso e' normale — cioe' a non guardare piu' i rossi.
    GIUDIZIO = "⛔ voci che separano davvero le due letture"
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            print(f"    --  {che:46s} nessun caso lo ha sollecitato")
            continue
        if che in (GIUDIZIO, "⛔ voci PROVATE sul comportamento del cliente"):
            col = VERDE if buoni == tot else ROSSO
        else:
            col = VERDE if buoni == tot else GIALLO
        print(f"    {col}{buoni:3d} su {tot:3d}{GRIGIO}  {che}"
              + ("   (denominatore, non un giudizio)" if che != GIUDIZIO else ""))

    # ⛔ ZERO VOCI NON E' «NESSUNA AMBIGUITA'».
    if not VOCI:
        print(f"\n    {ROSSO}⛔ ZERO voci: questo non e' «RCP e' senza "
              f"ambiguita'», e' un inventario vuoto{GRIGIO}")
        return 2

    print()
    # ⛔ E LE SMENTITE VENGONO PRIMA DI TUTTO, perche' sono l'unico rosso che
    #    dice «quel che questo file racconta del cliente non e' vero oggi».
    if smentite:
        print(f"    {ROSSO}⛔ B9: {len(smentite)} voci sono SMENTITE dal "
              f"comportamento del cliente di prova{GRIGIO}")
        for sigla, dichiarata, vista, perche in smentite:
            print(f"       {sigla}: la voce dice «lettura {dichiarata}», il "
                  f"cliente esegue «{vista}» — {perche}")
        print("       ⛔ Non e' un difetto del documento: e' che la voce "
              "descrive un cliente")
        print("          che non esiste piu'.  Va riletta e riscritta PRIMA di "
              "essere creduta,")
        print("          e la scelta nuova va portata in «che cosa NON ha "
              "funzionato».")
        return 1
    if non_provate:
        print(f"    {GIALLO}[?] B9: {len(non_provate)} voci non si sono potute "
              f"provare sul comportamento{GRIGIO}")
        for sigla, errore in non_provate:
            print(f"       {sigla}: {errore}")
        print("       ⛔ «Non l'ho potuta provare» non e' «passa»: senza queste "
              "righe il")
        print("          banco torna a poggiare sulle sole citazioni, che e' "
              "quel che il")
        print("          rilievo A8 ha rotto.")
        return 3
    if rotte:
        print(f"    {ROSSO}⛔ B9: {len(rotte)} voci non separano niente "
              f"({', '.join(rotte)}){GRIGIO}")
        print("       Due letture con gli stessi byte non sono due letture:")
        print("       il difetto e' DI QUESTO BANCO, non del documento.")
        return 1
    if scollegate:
        print(f"    {GIALLO}[?] B9: l'inventario e' intero, ma "
              f"{len(scollegate)} voci citano un testo che non c'e' piu'"
              f"{GRIGIO}")
        for sigla, persi in scollegate:
            print(f"       {sigla}: {len(persi)} appigli persi")
        print("       ⛔ Non e' «la voce e' sbagliata»: e' che RCP.md o il")
        print("          cliente di prova sono cambiati, e la voce va riletta")
        print("          prima di essere creduta.")
        return 3
    print(f"    {VERDE}⭐ B9: {len(VOCI)} punti in cui il documento non "
          f"decideva, tutti verificati sul testo di oggi{GRIGIO}")
    print("       ⚠ E questo NON vuol dire che siano soli: vuol dire che sono")
    print("         questi quelli trovati leggendo RCP.md una seconda volta.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B9 — i punti in cui RCP.md ammetteva due letture")
    p.add_argument("--byte", action="store_true",
                   help="stampa gli esadecimali delle due letture")
    p.add_argument("--elenco", action="store_true",
                   help="solo i titoli, senza costruire niente")
    sys.exit(principale(p.parse_args()))
