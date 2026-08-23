#!/usr/bin/env python3
"""01-b3-cliente.py — il cliente di prova: la stretta di mano di RCP, scritta una seconda volta.

    python3 01-b3-cliente.py --utente prova --parola X [--registra t.rcpreg]
    python3 01-b3-cliente.py --certifica     ⭐ QUI, senza rete e senza macchina

---------------------------------------------------------------------------
⭐⭐ FASE 9 — LE DUE REGOLE DELL'AUDIO, E L'INTERRUTTORE FRA LORO

La cura del riordino — quella che smette di buttare i blocchi arrivati fuori
sequenza — era scritta **solo in `src/pagina.html`**.  ⇒ Nessun banco poteva
misurare se morde, perche' il cliente che i banchi usano non ce l'aveva.
Adesso ce l'ha, dietro `--audio-regola vecchia|nuova`.

⛔⛔ **Il predefinito e' `vecchia`, e si cambia solo per decisione dell'utente.**
     Decine di banchi gia' misurati usano questo programma: con la regola nuova
     per predefinito, ogni numero gia' scritto smetterebbe di essere
     confrontabile — e il confronto «prima / dopo la cura» e' proprio quello
     che si vuole poter fare.  ⭐ `--certifica` caso 6 lo verifica contro una
     trascrizione LETTERALE del codice del 22 agosto, non contro un'opinione.

⚠ La traduzione dalla pagina a qui NON e' identica, e le cinque differenze
  stanno scritte per esteso sopra `class VaglioAudio` (T1..T5).  La piu'
  importante: **qui la decodifica costa zero**, e con `--audio-decodifica-ms 0`
  il contatore `scartati_tardivi` non e' una misura, e' uno zero cieco.

---------------------------------------------------------------------------
⛔ IL SUO MESTIERE, CHE NON E' «FUNZIONARE»

`PIANO.md` §1.1: questo e' **il secondo lettore di `RCP.md`**, in un linguaggio
diverso dal server.  ⛔ **Chi lo fa crescere non guarda il C**: se lo
guardasse ne erediterebbe i fraintendimenti, e due programmi scritti dalla
stessa mano che vanno d'accordo non confermano niente.

⭐ Il suo valore non e' il verde: e' che chi lo scrive **deve scegliere** dove
   la specifica ammette due letture, e quelle scelte vanno scritte in «che cosa
   NON ha funzionato» — sono difetti del documento, e questa e' la fase in cui
   costano meno.

---------------------------------------------------------------------------
⭐ E REGISTRA, NEL FORMATO DI §11.1

Ogni byte che passa sul canale di controllo finisce in una registrazione che
**il validatore di B4 puo' giudicare**.  ⛔ La parola d'ordine no: viene
oscurata come impone §11.1 — lunghezza vera, byte sostituiti con `0x2A`,
impronta di quel che c'era.  Cosi' il validatore vede l'inquadratura intera e
la parola non finisce in un file.

⛔ **E si registra anche quando la stretta di mano NON riesce.**  Un
`CONGEDO(GIA_ATTIVA_REMOTA)` e' l'oggetto che il terzo giro di B3 esiste per
produrre: se la traccia si scrivesse solo lungo la strada che riesce, l'unico
banco dell'invariante I2 non consegnerebbe niente all'arbitro (rilievo R8.9).

⛔ **E il codice d'uscita dice CHE COSA e' successo alla connessione**: `0` sono
rimasto attaccato per tutto il tempo chiesto, `4` la connessione o la sessione
sono cadute prima — e il registro dice quale delle due (rilievi R8.2, R8.4).
`5` nessun `TELA` e' arrivato (§7.1, il silenzio).  ⭐ `6` — 22 agosto 2026 —
**la scena chiesta non e' esercitabile**: e' il caso di `--puntatore-vecchia`
quando non c'e' nessuna tela precedente, o quando la tela nuova non e' piu'
piccola.  ⛔ Non e' `1` e non e' `0`: un banco che leggesse «tutto bene» da una
scena che non e' avvenuta sarebbe verde per costruzione, e un banco che
leggesse «il prodotto ha sbagliato» darebbe il rosso all'imputato sbagliato.
"""
import argparse
import asyncio
import hashlib
import json
import os
import ssl
import struct
import sys
import time

# ⛔⭐ E `aioquic` PUO' NON ESSERCI — 23 agosto 2026, fase 9.
#
#     `aioquic` sta DENTRO il contenitore, non sul portatile.  ⚠ Finche' questo
#     programma sapeva fare una cosa sola — attaccarsi a un server — un
#     `ModuleNotFoundError` in testa al file era la diagnosi giusta.  ⛔ Ma
#     `--certifica` non tocca la rete: e' un'autoprova del vaglio dell'audio, e
#     deve poter girare DOVE SI SCRIVE IL CODICE.  Con l'import in testa non
#     partiva nemmeno.
#
# ⇒ Si prova a importare, e se manca si tira avanti con dei segnaposto: chi
#   chiede la RETE lo scopre subito e con una riga che dice cosa fare, chi
#   chiede `--certifica` gira lo stesso.  ⚠ E il segnaposto ALZA: un import
#   silenziosamente finto che lasciasse partire un giro vero sarebbe la forma
#   d'errore peggiore, «funziona e misura niente».
try:
    from aioquic.asyncio import connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent
    AIOQUIC = None
except ModuleNotFoundError as _e:          # noqa: N816 — il nome dice il fatto
    AIOQUIC = str(_e)

    class QuicConnectionProtocol:          # segnaposto
        def __init__(self, *a, **kw):
            raise RuntimeError(f"⛔ senza `aioquic` non c'e' nessuna rete: {AIOQUIC}")

    class QuicEvent:                       # segnaposto (serve all'annotazione)
        pass

    class HeadersReceived:                 # segnaposto (serve a `isinstance`)
        pass

    H3_ALPN = H3Connection = QuicConfiguration = connect = None

CLIENT, SERVER = 1, 2
T = {"CIAO": 0x0001, "ECCOMI": 0x0002, "CREDENZIALI": 0x0003, "AMMESSO": 0x0004,
     "RESPINTO": 0x0005, "ATTACCA": 0x0006, "SESSIONE": 0x0007,
     # ⭐ La strada della TELA, entrata qui il 16 agosto 2026 (sottofase 6.6).
     #    ⛔ `fasi/06-la-tela-e-la-vista.md` §0 punto 6: erano nel protocollo da
     #    una settimana e questo cliente **non ne mandava nemmeno uno**.
     "VISTA": 0x0008, "DISPOSIZIONE": 0x0009, "CURSORE_FORMA": 0x000A,
     "ADATTA_TELA": 0x000B, "CONGEDO": 0x000C, "RICHIEDI_CHIAVE": 0x000D,
     "TELA": 0x000E, "TERMINA_SESSIONE": 0x0011}
NOME = {v: k for k, v in T.items()}
# ⛔ IL CANALE DI INPUT STA IN UN DIZIONARIO SUO, e non e' pignoleria: `NOME`
#    e' la mappa inversa di `T` e la usa `_sfoglia()` per dare un nome ai
#    messaggi che arrivano **sul canale di controllo**.  Un `0x0101` la' dentro
#    farebbe comparire la parola «PUNTATORE» nel registro di un messaggio di
#    controllo malformato — cioe' una diagnosi che manda a guardare il canale
#    sbagliato.  ⚠ E i canali sono due davvero: §2.5, byte alto `0x00` contro
#    `0x01`.
T_PUNTATORE = 0x0101            # §7.3
# I due esiti e i tre motivi di `TELA` — §7.1.
TELA_ESITO = {1: "ADATTATA", 2: "RIFIUTATA"}
TELA_MOTIVO = {0: "-", 1: "COMPOSITORE_INCAPACE", 2: "MISURA_FUORI_LIMITI",
               3: "NON_ORA"}
MOTIVI = {0x07: "CREDENZIALI_ERRATE", 0x08: "TROPPI_TENTATIVI",
          0x09: "NIENTE_IN_COMUNE", 0x0A: "VERSIONE_INCOMPATIBILE",
          0x0B: "ERRORE_PROTOCOLLO", 0x0D: "TEMPO_SCADUTO",
          0x0E: "SESSIONE_NON_SERVIBILE", 0x0F: "GIA_ATTIVA_REMOTA"}


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def inquadra(tipo, corpo):
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def _varint(d, i):
    """Legge un intero variabile QUIC da `d` a partire da `i`.

    Restituisce (valore, prossimo indice), oppure (None, i) se i byte non
    bastano.  ⚠ La lunghezza sta nei due bit alti del primo byte, e il valore
    e' quel che resta: leggere il primo byte per intero e' l'errore che fa
    scambiare 0x40 0x41 per due frame."""
    if i >= len(d):
        return None, i
    n = 1 << (d[i] >> 6)
    if i + n > len(d):
        return None, i
    v = d[i] & 0x3F
    for k in range(1, n):
        v = (v << 8) | d[i + k]
    return v, i + n


def _capsula_chiusura(d):
    """Cerca `CLOSE_WEBTRANSPORT_SESSION` (0x2843) e ne torna il codice.

    ⛔ Sul filo della CONNECT le capsule viaggiano **dentro i frame DATA**
       (RFC 9297), quindi il caso normale e' `DATA(0x00) → capsula`.  Il caso
       in cui la capsula arriva **nuda** e' un difetto del server — un browser
       leggerebbe `0x2843` come un tipo di frame HTTP/3 sconosciuto e la
       butterebbe (RFC 9114 §9) — e questo lettore lo riconosce per poterlo
       DIRE, non per perdonarlo.

    Restituisce (codice, nuda) oppure (None, False)."""
    def dentro(b):
        i = 0
        while i < len(b):
            tipo, j = _varint(b, i)
            if tipo is None:
                return None
            lung, j = _varint(b, j)
            if lung is None or j + lung > len(b):
                return None
            if tipo == 0x2843 and lung >= 4:
                return b[j + 3]      # i quattro byte del codice, il piu' basso
            i = j + lung
        return None

    # 1. la forma giusta: uno o piu' frame DATA, e le capsule dentro
    i = 0
    while i < len(d):
        tipo, j = _varint(d, i)
        if tipo is None:
            break
        lung, j = _varint(d, j)
        if lung is None or j + lung > len(d):
            break
        if tipo == 0x00:             # DATA
            c = dentro(d[j:j + lung])
            if c is not None:
                return c, False
        i = j + lung
    # 2. la forma sbagliata: la capsula senza il frame che la porta
    c = dentro(d)
    return (c, True) if c is not None else (None, False)


class Registratore:
    """Il formato di RCP.md §11.1, scritto una volta sola.

    ⛔⛔ LA MAGIA E' `RCPREG 0x00 0x02`, E FINO AL 16 AGOSTO 2026 NON LO ERA.

    ⭐ **E' il difetto piu' grosso trovato dalla sottofase 6.6, e non era nel
       prodotto: era fra due banchi.**  Il 12 agosto 2026 il formato di §11.1 e'
    passato a `0x00 0x02` — il blocco porta il campo `fine` e cresce da 16 a 17
    byte — e `01-b4-validatore.py` ha imparato a **rifiutare** il formato
    vecchio, come §11.1 gli impone: *«un validatore vecchio deve RIFIUTARE il
    formato nuovo, non leggerlo di traverso»*.

    ⛔ Ma questo registratore ha continuato a scrivere `0x00 0x01`.  ⇒ Da quel
       giorno **ogni traccia di B3 usciva 2 dall'arbitro** — «registrazione
    malformata» — e le cinque chiamate `valida` di `01-b3-lancia.sh` fallivano
    tutte, ⛔ facendo uscire **1** il banco intero.  ⚠ Nessuno dei due
    programmi era rotto da solo: il validatore faceva **esattamente** quel che
    la specifica gli chiede, e il registratore scriveva un formato che era
    stato valido fino a quattro giorni prima.  E' la forma d'errore che nasce
    fra due file, dove nessuna prova unitaria guarda.

    ⚠ **E il rosso non era muto: era illeggibile.**  «La traccia e' malformata»
      su un banco della stretta di mano manda a cercare un difetto del
    *registratore* — che infatti c'era — ma solo dopo aver escluso il server, la
    rete e il protocollo.  ⭐ Il banco che tiene chiusa questa porta e'
    `06-b38-registratore.py`, e non prova il filo: prova che i due banchi
    parlano la stessa lingua.

    ⭐⭐ **E DAL 21 AGOSTO 2026 LA MAGIA E' `0x00 0x03`: il blocco porta
       `istante_ms`.**

    §11.1 non registrava il **tempo**, e senza il tempo la regola del *«secondo
    di grazia dopo `TELA(ADATTATA)`»* di §7.1 non era collaudabile da nessun
    `.rcpreg` — era la `[?]` di `fasi/06-la-tela-e-la-vista.md` §7.2.

    ⛔ **E l'istante e' MONOTONO e RELATIVO al primo blocco, mai un'ora del
       mondo.**  §4.4 vieta i segreti nel file, e una data assoluta non e' un
    segreto per caso: dice **quando** e — insieme all'indirizzo che la
    registrazione gia' porta — **da dove** un utente si e' collegato.  Il primo
    blocco vale 0, e chi legge non impara niente su chi ha registrato.

    ⛔ **E il campo `orologio` nell'intestazione dice DI CHI sono i tempi**
       (1 = client, 2 = server), perche' la regola del secondo e' del **server**
    e una traccia presa al client misura un intervallo **piu' corto**: mezzo
    giro di rete per lato.  ⇒ Da qui l'arbitro conclude **in un verso solo**, e
    lo dichiara.  La riga sta in `01-b4-validatore.py`.
    """

    MAGIA = b"RCPREG\x00\x03"
    # ⛔ Le due magie di ieri si conservano QUI e non solo nell'arbitro: il
    #    banco che le rifiuta (`01-b4-registrazioni.py`) le scrive, e due
    #    elenchi di versioni in due file sono due elenchi che divergono.
    MAGIA_V1 = b"RCPREG\x00\x01"
    MAGIA_V2 = b"RCPREG\x00\x02"
    CONTINUA, FIN, RESET = 0, 1, 2
    OROLOGIO_CLIENT, OROLOGIO_SERVER = 1, 2

    def __init__(self):
        self.blocchi = []
        self.scritta = False
        # ⛔ Questo programma e' il CLIENT: i tempi sono i suoi, e lo dichiara.
        #    ⚠ Scrivere `2` qui vorrebbe dire far credere all'arbitro di avere
        #      l'orologio del server, e allora la conclusione «in un verso solo»
        #      diventerebbe una conclusione in due versi — sbagliata.
        self.orologio = self.OROLOGIO_CLIENT
        self.t0 = None
        # ⛔ Lo stream del canale di controllo, quello VERO.  §4.2: e' il primo
        #    stream bidirezionale della sessione, e ⚠ **non e' lo 0** — in
        #    HTTP/3 lo 0 e' gia' quello della CONNECT (rilievo R1.5).  Qui si
        #    scriveva `0` fisso: un numero che non e' mai stato quello, e che
        #    l'arbitro usa per P3 (§2.5, «un fotogramma sullo stream del canale
        #    di controllo»).
        self.stream = 0

    def istante(self):
        """⛔ Millisecondi dal PRIMO blocco, da un orologio monotono — §11.1.

        ⚠ `time.monotonic()` e non `time.time()`, e non e' pignoleria: un
          aggiustamento di NTP nel mezzo di una sessione farebbe **tornare
          indietro** gli istanti, e l'arbitro leggerebbe un `PUNTATORE`
          arrivato *prima* del `TELA` che lo precede sul filo.
        """
        adesso = time.monotonic()
        if self.t0 is None:
            self.t0 = adesso
        ms = int((adesso - self.t0) * 1000.0)
        # ⛔ Il campo e' u32: 49 giorni.  Si satura invece di avvolgersi, perche'
        #    un istante che riparte da zero e' peggio di un istante fermo.
        return min(ms, 0xFFFFFFFF)

    def aggiungi(self, verso, carico, oscurati=(), canale=0x00, stream=None,
                 fine=CONTINUA, istante=None):
        self.blocchi.append([verso, canale, fine,
                             self.stream if stream is None else stream,
                             carico, list(oscurati),
                             self.istante() if istante is None else istante])

    def segna_fine(self, verso, fine, stream=None):
        """⛔ Come si e' chiuso lo stream, e da QUALE lato — §11.1.

        ⭐ Non e' un dettaglio di formato: e' l'unico byte che permette
           all'arbitro di distinguere **«il server non ha risposto»** da **«la
        registrazione finisce qui»**.  §7.1 impone un `TELA` a ogni
        `ADATTA_TELA`, e senza questo campo una traccia che finisce con una
        richiesta in volo ha lo stesso aspetto nei due casi — la forma d'errore
        **E8**, e stavolta sulla regola con il sintomo peggiore:
        *«l'applicazione si e' piantata»*.

        ⚠ Se l'ultimo blocco e' gia' di quel verso lo si marca; altrimenti si
          aggiunge un blocco a carico **zero**, che e' il modo onesto di dire
          «da questo lato non e' arrivato altro, e poi si e' chiuso».
        """
        if self.blocchi and self.blocchi[-1][0] == verso:
            self.blocchi[-1][2] = fine
            return
        self.aggiungi(verso, b"", stream=stream, fine=fine)

    def scrivi(self, percorso):
        # ⛔ L'intestazione di §11.1: magia · u32 quanti_blocchi · u8 orologio ·
        #    3 byte riservati che DEVONO essere 0.
        out = bytearray(self.MAGIA + struct.pack("!IBBBB", len(self.blocchi),
                                                 self.orologio, 0, 0, 0))
        for verso, canale, fine, stream, carico, osc, ist in self.blocchi:
            out += struct.pack("!BBBIQIH", verso, canale, fine, ist, stream,
                               len(carico), len(osc))
            for ini, qua, imp in osc:
                out += struct.pack("!II", ini, qua) + imp
            out += carico
        with open(percorso, "wb") as f:
            f.write(bytes(out))


# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL VAGLIO DELL'AUDIO — §6.3, e la cura del riordino della fase 9
#
# ⛔⛔ PERCHE' ESISTE QUESTA CLASSE, E IL BUCO CHE CHIUDE — 23 agosto 2026.
#
#      La cura del riordino e' stata scritta **solo in `src/pagina.html`**
#      (`audio_posto_passato`, `scartati_tardivi`, `fuori_ordine`, `doppioni`,
#      `recuperati`, `ist_max_us`).  Questo cliente — che e' il secondo lettore
#      di `RCP.md` e quello che TUTTI i banchi usano — aveva ancora la regola di
#      prima: `istante <= ultimo ⇒ butta`.  ⇒ **Nessun banco poteva misurare se
#      la cura morde**, perche' il cliente che i banchi usano non ce l'ha.
#
# ⛔⛔ E IL PREDEFINITO RESTA `vecchia`, per decisione dell'utente.
#      `01-b3-cliente.py` lo usano decine di banchi gia' misurati: cambiare il
#      comportamento predefinito farebbe smettere di essere confrontabile ogni
#      numero gia' scritto.  ⭐ Con `--audio-regola vecchia` i contatori
#      `ricevuti` e `vecchi` e la lista dei blocchi consegnati sono IDENTICI a
#      quelli di prima — e `--certifica` caso 6 lo verifica contro una
#      trascrizione letterale del codice di prima, non contro un'opinione.
#
# ── LA REGOLA DELLA PAGINA, IN QUATTRO CASI ────────────────────────────────
#   `[R]` src/pagina.html:6497-6572 (il filo) e 5889-6186 (`suona()`).
#
#   1. `istante == ultimo`  ⇒ **doppione**: si butta.  Suonarlo due volte
#      raddoppierebbe il segnale, che e' il modo peggiore di fallire.
#      ⛔ Zero e' il numero atteso: QUIC scarta da se' i pacchetti ripetuti.
#   2. `istante < ultimo` (ARRETRATO) e il suo posto nel tempo e' GIA' PASSATO
#      ⇒ `scartati_vecchi`: e' consumato davvero, §6.3 alla lettera.
#   3. `istante < ultimo` ma il suo posto **c'e' ancora** ⇒ `fuori_ordine`:
#      ⭐ SI TIENE, ed e' tutta la cura.  L'ancora gli da' un posto assoluto:
#      non gli serve arrivare in ordine per finirci dentro.  E si ripaga il
#      debito dei `mancati` (`recuperati`), o ogni sorpasso curato si
#      presenterebbe come una perdita — la cura si accuserebbe da sola.
#   4. `istante > ultimo` (IL PIU' NUOVO) ⇒ non si vaglia MAI, si conta il buco
#      (`mancati`) e `ultimo` avanza.  ⛔ Vagliare anche il piu' nuovo
#      lascerebbe l'ancora alla deriva senza riarmo possibile: sessione muta per
#      sempre con tutti i contatori verdi (`LEZIONI.md` §2.2).
#
#   E poi c'e' la SECONDA PORTA, che nella pagina sta dentro `suona()`: un
#   blocco che ha passato il filo puo' aver perso il suo posto **mentre lo
#   decodificavamo**.  Li' i casi sono due e non uno:
#     · e' il piu' nuovo che abbiamo ⇒ e' TUTTA la riproduzione in ritardo:
#       l'ancora si riarma (`riarmi`), come ha sempre fatto;
#     · e' un SORPASSATO (`ist_max_us > istante`) ⇒ in ritardo c'e' solo lui:
#       `scartati_tardivi`, e l'ancora NON si tocca.  ⛔ Trattarli uguali
#       costerebbe un riarmo per ogni sorpasso, cioe' 250 ms di ritardo
#       regalato per un blocco da 5.
#
# ── ⚠ LA TRADUZIONE, E DOVE **NON** E' IDENTICA ALLA PAGINA ────────────────
#
#   La pagina misura «il posto e' passato» con `a.base + istante < ctx.currentTime`,
#   cioe' con la testina di un `AudioContext` vero.  Qui non c'e' ne' un
#   `AudioContext` ne' un decodificatore.  ⇒ Le differenze DICHIARATE sono
#   cinque, e chi legge un numero di questo cliente deve conoscerle:
#
#   T1 · **L'orologio di riproduzione e' SIMULATO**: `ora` viene dal monotonico
#        (o dall'orologio finto di `--certifica`), non da `ctx.currentTime`.
#        ⚠ Un `AudioContext` vero puo' derivare dal monotonico di qualche parte
#        per milione; qui i due orologi sono lo STESSO orologio, quindi questo
#        cliente **non puo' vedere la deriva** fra scheda audio e sistema.
#   T2 · **Non c'e' lo stato «sospeso»**: la pagina, con `ctx.state !== "running"`,
#        risponde «no» al posto passato e butta in `sospesi`.  Qui l'orologio
#        corre sempre ⇒ `sospesi` non esiste e non e' misurabile di qui.
#   T3 · **La decodifica costa zero**: nella pagina fra il filo e `suona()` c'e'
#        un `AudioDecoder` vero, e `scartati_tardivi` nasce PROPRIO da quel
#        ritardo.  ⇒ Qui la seconda porta si apre allo stesso istante della
#        prima e `scartati_tardivi` resterebbe **zero per costruzione** — che
#        sarebbe un verde falso.  ⭐ Percio' c'e' `ritardo_decodifica_s`: il
#        tempo che si finge di spendere a decodificare.  A zero (il predefinito
#        in rete) `scartati_tardivi` **non e' una misura, e' uno zero cieco**.
#   T4 · **`passo_us` non viene da un decodificatore**: per il PCM si CALCOLA
#        dal carico — `[S]` `RCP.md`:1299, «480 campioni, 960 byte, 5 ms per
#        datagram» — che e' esatto e non e' circolare.  ⚠ Per Opus non si sa
#        decodificare: `passo_us` resta 0 (e allora, come nella pagina, il conto
#        dei `mancati` E' SPENTO) finche' non lo si dichiara con
#        `--audio-passo-us`.
#   T5 · **`Math.round` contro `round()`**: JS arrotonda la meta' verso l'alto,
#        Python verso il pari.  Qui si scrive `int(x + 0.5)` a mano, o su un
#        salto di esattamente 1,5 passi i due programmi conterebbero `mancati`
#        diversi — e sarebbe una differenza invisibile fino al giorno sbagliato.
#
# ── LA PUREZZA, E PERCHE' CE NE SONO DUE ───────────────────────────────────
#
#   `purezza` = **consegnati all'uscita / arrivati sul filo** — dove «arrivati
#   sul filo» sono i datagram conformi (prefisso giusto, ≥12 byte, tipo 0x0401)
#   e «consegnati» quelli che finiscono in `a_blocchi`, cioe' quel che il
#   giudice del suono potra' ascoltare.  ⭐ E' la definizione che serve qui.
#
#   ⛔ E **NON** e' la formula che usano i banchi della pagina
#   (`09-b74-audio-firefox.py`:300, `suonati / ricevuti`): li' `ricevuti` si
#   incrementa **dopo** il vaglio (`src/pagina.html`:6574), quindi i datagram
#   buttati sul filo **non stanno ne' al numeratore ne' al denominatore** — e
#   quella frazione e' CIECA proprio al danno che questa cura ripara.  Si
#   stampa lo stesso, come `purezza_pagina`, perche' e' il numero con cui i
#   giri sulla pagina si confrontano; ⚠ in questo cliente vale 1,000 per
#   costruzione con la regola vecchia, e chi lo leggesse da solo concluderebbe
#   «tutto sano» da una successione distrutta.
AUDIO_CUSCINO_MS = 250          # `[R]` src/pagina.html:5550
# ⛔⛔ IL PREDEFINITO E' `vecchia`, e si cambia SOLO per decisione dell'utente.
REGOLA_AUDIO = "vecchia"
PASSO_AUDIO_US = 0              # 0 = lo si ricava dal PCM (T4)
DECODIFICA_AUDIO_S = 0.0        # ⚠ T3: a zero `scartati_tardivi` e' cieco


class VaglioAudio:
    """§6.3 e la cura del riordino, con l'interruttore fra le due regole.

    ⛔ `regola="vecchia"` e' il PREDEFINITO e non si cambia da qui: e' quel che
       tiene confrontabili i numeri gia' misurati.
    """

    REGOLE = ("vecchia", "nuova")

    def __init__(self, regola="vecchia", cuscino_ms=AUDIO_CUSCINO_MS,
                 orologio=time.monotonic, passo_us=0,
                 ritardo_decodifica_s=0.0):
        if regola not in self.REGOLE:
            raise ValueError(f"regola audio «{regola}»: sono {self.REGOLE}")
        self.regola = regola
        self.cuscino_s = cuscino_ms / 1000.0
        self._orologio = orologio
        self.ritardo_decodifica_s = ritardo_decodifica_s
        # ⚠ T4: 0 = non lo so, e allora il conto dei `mancati` e' SPENTO —
        #   come nella pagina, che scrive `if (a.passo_us > 0)`.
        self.passo_us = passo_us
        self.passo_dichiarato = passo_us > 0
        # ── i contatori, con i nomi della pagina ──────────────────────────
        self.sul_filo = 0            # datagram conformi arrivati (denominatore)
        self.ricevuti = 0            # hanno passato il vaglio del filo
        self.consegnati = 0          # `suonati` della pagina: usciti davvero
        self.scartati_vecchi = 0     # arretrato, e il suo posto e' passato
        self.scartati_tardivi = 0    # sorpassato, e il posto e' passato dopo
        self.fuori_ordine = 0        # ⭐ arretrato E TENUTO: la cura
        self.doppioni = 0            # lo stesso `istante` due volte
        self.recuperati = 0          # `mancati` ripagati da un fuori ordine
        self.mancati = 0             # mai arrivati: il buco sul filo
        self.mancati_volte = 0
        self.riarmi = 0              # l'ancora si e' spostata (i «BUCHI»)
        self.ist_max_us = 0          # il massimo MESSO IN SCALETTA
        self.ultimo_istante = None   # il massimo ACCETTATO SUL FILO
        self.base = None             # l'ancora: secondi da sommare a `istante`

    # ── la frontiera «il suo posto e' gia' passato» ────────────────────────
    def _posto_passato(self, ist_us, ora):
        """`[R]` `audio_posto_passato`, src/pagina.html:5889.

        ⛔ Due casi in cui la risposta e' «no» e non «non lo so»: `istante`
           nullo, e ancora non agganciata — li' non e' stato consumato NIENTE.
        ⚠ T2: manca il terzo caso della pagina (contesto sospeso), perche' qui
          l'orologio non si ferma mai.
        """
        if not ist_us > 0 or self.base is None:
            return False
        return self.base + ist_us / 1e6 < ora

    def _conta_mancati(self, istante):
        """`[R]` src/pagina.html:6550.  ⚠ T5: `int(x + 0.5)`, non `round()`."""
        if self.ultimo_istante is None or self.passo_us <= 0:
            return
        salto = istante - self.ultimo_istante
        quanti = int(salto / self.passo_us + 0.5) - 1
        # ⚠ La soglia e' 1,5 passi e non «piu' di un passo»: l'`istante` viene
        #   dalla cattura e non da un metronomo.
        if quanti >= 1 and salto > self.passo_us * 1.5:
            self.mancati += quanti
            self.mancati_volte += 1

    def arrivo(self, istante, codec=0, byte_carico=0):
        """Un datagram conforme e' arrivato.  Torna `(consegnato, motivo)`.

        ⛔ Il conto dei `sul_filo` e' QUI e non prima: i datagram scartati per
           prefisso, lunghezza o tipo non sono blocchi d'audio, e metterli al
           denominatore della purezza confonderebbe «la rete riordina» con «il
           server manda spazzatura».
        """
        self.sul_filo += 1
        nuova = self.regola == "nuova"

        if self.ultimo_istante is not None and istante == self.ultimo_istante:
            # ⚠ Con la regola VECCHIA `doppioni` e' un SOTTOCONTO di
            #   `scartati_vecchi`, non una voce a parte: il codice di prima li
            #   contava li' dentro (`istante <= ultimo`), e toglierli
            #   cambierebbe ogni numero gia' misurato.  ⭐ Contarli comunque
            #   costa zero e dice una cosa che prima non si sapeva.
            self.doppioni += 1
            if not nuova:
                self.scartati_vecchi += 1
            return (False, "doppione: lo stesso `istante` due volte")

        if self.ultimo_istante is not None and istante < self.ultimo_istante:
            if not nuova:
                # La regola di prima, alla lettera: arretrato ⇒ si butta.
                self.scartati_vecchi += 1
                return (False, "istante non piu' recente (regola vecchia)")
            ora = self._orologio()
            if self._posto_passato(istante, ora):
                self.scartati_vecchi += 1
                return (False, "il suo posto nel tempo e' gia' passato (§6.3)")
            # ⭐ FUORI ORDINE MA ANCORA SUONABILE: e' tutta la cura.
            self.fuori_ordine += 1
            if self.mancati > 0:
                self.mancati -= 1
                self.recuperati += 1
        else:
            self._conta_mancati(istante)
            # ⛔ SOLO IN AVANTI: `ultimo_istante` e' un MASSIMO.  Riportarlo
            #    indietro su un fuori ordine farebbe sembrare il datagram
            #    successivo un salto enorme, e il conto dei `mancati` si
            #    riempirebbe di perdite finte.
            self.ultimo_istante = istante

        self.ricevuti += 1
        return self._consegna(istante, codec, byte_carico)

    def _consegna(self, ist_us, codec, byte_carico):
        """La seconda porta: nella pagina e' dentro `suona()`.

        ⚠ T3: qui la decodifica costa `ritardo_decodifica_s`, che in rete e'
          zero — e con zero `scartati_tardivi` non e' una misura, e' uno zero
          cieco.  `--certifica` lo esercita con un ritardo dichiarato.
        """
        ora = self._orologio() + self.ritardo_decodifica_s
        t = ist_us / 1e6
        if self.base is None:
            self.base = ora + self.cuscino_s - t
        quando = self.base + t
        if quando < ora + 0.001:
            if self.regola == "nuova" and self.ist_max_us > ist_us:
                # ⛔ E' UN SORPASSATO, e in ritardo c'e' solo lui: si butta lui
                #    e l'ancora resta dov'e'.
                self.scartati_tardivi += 1
                return (False, "sorpassato, e il posto e' passato mentre lo "
                               "decodificavamo")
            # E' il piu' nuovo che abbiamo: e' TUTTA la riproduzione in
            # ritardo ⇒ l'ancora si sposta.  ⚠ E' l'unica cosa che RIALZA la
            # coda, ed e' udibile.
            self.riarmi += 1
            self.base = ora + self.cuscino_s - t
        if ist_us > self.ist_max_us:
            self.ist_max_us = ist_us
        # ⚠ T4: il passo dal carico del PCM, non da un decodificatore.
        if not self.passo_dichiarato and codec == 2 and byte_carico > 0:
            self.passo_us = int(byte_carico * 5000 / 960 + 0.5)
        self.consegnati += 1
        return (True, "")

    # ── i due numeri che si stampano ──────────────────────────────────────
    @property
    def purezza(self):
        """Consegnati all'uscita / arrivati sul filo.  `None` = niente da dire."""
        if self.sul_filo == 0:
            return None
        return self.consegnati / self.sul_filo

    @property
    def purezza_pagina(self):
        """`suonati / ricevuti`, la formula di `09-b74`.  ⚠ Cieca al vaglio."""
        if self.ricevuti == 0:
            return None
        return self.consegnati / self.ricevuti

    def riga(self):
        """I contatori, SEMPRE, con tutt'e due le regole e anche a zero."""
        p, pp = self.purezza, self.purezza_pagina
        return (f"regola {self.regola} · sul filo {self.sul_filo} · "
                f"ricevuti {self.ricevuti} · consegnati {self.consegnati} · "
                f"PUREZZA {'?' if p is None else format(p, '.4f')} "
                f"(pagina {'?' if pp is None else format(pp, '.4f')})")

    def riga_conti(self):
        return (f"tardivi {self.scartati_tardivi} · fuori {self.fuori_ordine} · "
                f"rec {self.recuperati} · dop {self.doppioni} · "
                f"mancati {self.mancati} volte {self.mancati_volte} · "
                f"riarmi {self.riarmi} · passo {self.passo_us}us")


class Cliente(QuicConnectionProtocol):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accettata = asyncio.get_event_loop().create_future()
        self.sessione = None
        self.controllo = None
        self.arrivati = bytearray()
        self.messaggi = asyncio.Queue()
        self.finito = False
        # ⛔⛔ IL REGISTRATORE STA QUI, E NON NELLA CODA — 21 agosto 2026.
        #
        #    Fino a oggi ogni messaggio del server finiva nella traccia **nel
        #    momento in cui qualcuno lo tirava fuori dalla coda** (`attendi()`
        #    e `chiedi_tela()`).  ⇒ Un messaggio che arriva quando nessuno
        #    aspetta — cioe' durante `--resta`, che e' quasi tutta la vita di
        #    una sessione — NON entrava nella traccia affatto.
        #
        # ⛔ E le due regole che ci cadevano dentro sono proprio le due che
        #    §7.1 affida all'arbitro:
        #      · **T1** — un `TELA` NON SOLLECITATO;
        #      · **V3** — un `TELA` dopo una `VISTA`.
        #    L'arbitro le sa accusare (`01-b4-registrazioni.py` casi 22 e 30,
        #    `06-b38-mutazioni.py`), ma su registrazioni **costruite**: da una
        #    traccia di questo cliente non potevano uscire mai.  ⇒ Il giro 5 di
        #    `06-b38-tela.sh` — *«nessun TELA dopo la VISTA»* — era **verde per
        #    costruzione**, che `LEZIONI.md` dice essere peggio di nessun caso.
        #
        # ⭐ La cura e' di posto, non di logica: si registra dove i byte
        #    ARRIVANO (`_sfoglia`), non dove vengono consumati.  ⚠ E cosi'
        #    l'ordine dei blocchi e' quello del filo, che e' quel che §11.1
        #    chiede.  Trovato con `06-b40-lancia.sh`, casi 6 e 9.
        self.reg = None
        # ⛔ §3.1 punto 3: il motivo viaggia ANCHE nel codice d'errore
        #    applicativo con cui si chiude la sessione WebTransport.  Si
        #    conserva, perche' e' la seconda delle due strade — e il giorno in
        #    cui il `CONGEDO` non arriva e' l'unica.
        self.codice_chiusura = None
        # ⛔ CHE COSA E' CADUTO, E QUANDO — rilievi R8.2 e R8.4 del 10 agosto 2026.
        #
        #    B3 chiede due volte «la prima e' ancora attaccata?», e tutt'e due
        #    le volte lo leggeva dall'ESISTENZA DEL PROCESSO o dal suo codice
        #    d'uscita.  ⚠ Ma questo programma, dopo SESSIONE, dormiva e basta:
        #    la connessione poteva morire per il tetto d'inattivita' di QUIC, o
        #    la sessione poteva essere chiusa dal server, e il processo restava
        #    vivo e usciva 0 lo stesso.  Il banco leggeva «viva» da un fatto che
        #    non aveva osservato (E7: si verifica dal lato che invia).
        #
        # ⭐ Qui si osserva dal lato che riceve: chi cade lo dice, con il nome
        #    di CHE COSA e' caduto — e i due casi non si confondono, perche'
        #    «QUIC ha chiuso da se'» e «il server ha chiuso la sessione» sono i
        #    due imputati che il quarto giro esiste per separare.
        self.caduta = None
        # ═══ L'AUDIO — fase 7 ═════════════════════════════════════════════
        # ⛔ I contatori sono SEI e non uno, e ognuno nomina una regola diversa
        #    di §6.3: chi li sommasse otterrebbe un numero che non dice mai
        #    dove guardare (`LEZIONI.md` §2.2).
        self.a_ricevuti = 0      # datagram arrivati e conformi
        self.a_corti = 0         # < 12 byte: §6.3 li fa scartare
        self.a_tipo = 0          # `tipo` != 0x0401
        self.a_prefisso = 0      # il prefisso RFC 9297 non e' la nostra sessione
        self.a_vecchi = 0        # `istante` non piu' recente: §6.3
        self.a_codec = None      # il codec dichiarato nei datagram
        self.a_byte = 0
        # ⭐ IL VAGLIO — fase 9.  ⛔ La regola arriva da una variabile di
        #    modulo e non dal costruttore perche' `create_protocol=Cliente`
        #    non passa argomenti; il predefinito e' `vecchia` in due posti (qui
        #    e in `--audio-regola`), e sono d'accordo apposta.
        self.a_vaglio = VaglioAudio(regola=REGOLA_AUDIO, passo_us=PASSO_AUDIO_US,
                                    ritardo_decodifica_s=DECODIFICA_AUDIO_S)
        # I blocchi come sono arrivati, per il giudice di `07-b42`.
        self.a_blocchi = []
        self.caduto = asyncio.Event()
        # ⛔ E LA TERZA CAUSA: CHE LA CONNESSIONE L'ABBIAMO CHIUSA NOI.
        #
        #    `[M]` 10 agosto 2026, terzo giro: la finestra di `--resta` scade,
        #    questo programma esce 0, e `connect()` chiude la connessione
        #    uscendo dal suo contesto — aioquic alza `ConnectionTerminated`
        #    codice 0 senza motivo, e la riga qui sotto finiva nel registro
        #    IDENTICA a quella di un server che ti spodesta.  Il banco la
        #    trovava con un grep sull'intero file e dava il rosso al server,
        #    che aveva appena tenuto viva la sessione con i PING per 25 s.
        #
        # ⭐ «Terminata da noi» e «terminata da qualcun altro» sono due fatti
        #    diversi e adesso hanno due righe diverse (CODER.md §3.9, §4.2).
        self.chiusa_da_noi = False
        # ═══ GLI APPUNTI — fase 7, §7.4 ═══════════════════════════════════
        # ⛔ QUESTO CLIENTE E' IL SECONDO LETTORE DI `RCP.md` (`PIANO.md` §1.1),
        #    e i tre messaggi di §7.4 entrano qui perche' altrimenti il filo
        #    degli appunti sarebbe validato da UNA SOLA implementazione — la
        #    pagina, scritta dalla stessa mano del server.
        #
        # ⚠ Il montaggio e' PER STREAM, non uno solo: §2.5 dice «uno stream per
        #   trasferimento», quindi ce n'e' piu' d'uno vivo insieme.  ⛔ Con un
        #   accumulo unico due trasferimenti intrecciati si mescolerebbero, ed e'
        #   esattamente il difetto che l'identificatore di §7.4 esiste per
        #   togliere — trovarlo qui vorrebbe dire non trovarlo mai.
        self.app_in = {}          # stream_id -> bytearray, il montaggio
        self.app_mio_id = 0       # §7.4: ciascun lato numera i PROPRI, da 1
        self.app_mio_testo = ""
        self.app_suo_id = 0       # l'ultimo annuncio del server
        self.app_suo_len = 0
        self.app_ricevuto = None  # l'ultimo testo che il server ci ha mandato
        self.app_annunci = []     # [(id, byte)] tutti gli annunci del server
        self.app_chiesti = []     # [id] i trasferimenti che il server ci ha chiesto
        self.app_serviti = 0
        self.app_violazioni = []  # quel che NON torna con §7.4, con il nome
        self.app_evento = asyncio.Event()
        # Il preambolo degli stream unidirezionali del server, per stream:
        # `0x40 0x54` piu' il varint della sessione.  `None` = non e' nostro.
        self.uni_pref = {}
        self.uni_genere = {}
        # ═══ IL VIDEO PRESO DAL FILO — fase 3/7, 17 agosto 2026 ═══════════
        # ⛔ NON per dipingerlo: per SEPARARE il nostro flusso dal
        #    decodificatore del browser.  «Gli artefatti sono nostri» e «sono
        #    suoi» hanno la stessa faccia guardando lo schermo, e si dividono in
        #    un modo solo — dando gli STESSI BYTE a un terzo decodificatore che
        #    non e' nessuno dei due (`ffmpeg`/`dav1d`).
        # ⚠ E i byte sono quelli del FILO, non quelli del rilievo: fra il
        #   codificatore e il browser c'e' tutto il trasporto, e un difetto li'
        #   in mezzo il rilievo non lo vedrebbe.
        self.v_in = {}          # stream_id -> bytearray in montaggio
        # ⛔ Gli stream gia' registrati: l'intestazione di §6.2 si scrive UNA
        #    volta per stream, o una tela sola comparirebbe dieci volte e il
        #    denominatore di T4 conterebbe fotogrammi che non ci sono.
        self.v_reg = set()
        self.v_fotogrammi = []  # [(numero, chiave, larghezza, altezza, dati)]
        # ═══ IL CANALE DI INPUT — §2.5, §7.3, e il 22 agosto 2026 ═════════
        # ⛔ `RCP.md` §2.5: «**uno solo**, aperto dopo aver ricevuto `SESSIONE`
        #    e tenuto aperto».  ⚠ NON e' come gli appunti, dove ogni
        #    trasferimento ha il suo stream: qui uno stream per messaggio
        #    sarebbe **un altro protocollo**, e il server che conta gli `id`
        #    «su tutto il canale» (§7.3) non avrebbe piu' un canale su cui
        #    contarli.
        self.inp_stream = None
        # §7.3: «crescente, comincia da 1.  ⛔ 0 e' riservato».
        self.inp_id = 0
        # ⭐ L'ISTANTE **REGISTRATO** DELL'ULTIMO `TELA`, e non l'ora di
        #    adesso: il secondo di grazia lo arbitra §11.1 su `istante_ms`, e
        #    un ritardo contato su un orologio diverso da quello che finisce
        #    nel file darebbe un `dt` che non e' quello che l'arbitro legge.
        self.ultimo_tela_ms = None

    def _cade(self, perche: str) -> None:
        """La prima causa vince: le successive sono conseguenze, non cause."""
        if self.caduta is None:
            self.caduta = perche
            self.caduto.set()

    def apri_sessione(self, autorita, percorso):
        sid = self._quic.get_next_available_stream_id(is_unidirectional=False)
        self.sessione = sid
        self._http.send_headers(sid, [
            (b":method", b"CONNECT"), (b":protocol", b"webtransport"),
            (b":scheme", b"https"), (b":authority", autorita.encode()),
            (b":path", percorso.encode()),
            (b"origin", f"https://{autorita}".encode()),
        ])
        self.transmit()

    def apri_controllo(self):
        # ⛔ RCP.md §4.2: il canale di controllo e' il PRIMO stream
        #    bidirezionale della sessione.  ⚠ E NON e' «lo stream 0»: in
        #    HTTP/3 lo 0 e' gia' quello della CONNECT che stabilisce la
        #    sessione, e l'API non espone nessun numero (rilievo R1.5).
        self.controllo = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)
        return self.controllo

    def manda(self, dati):
        self._quic.send_stream_data(self.controllo, dati, end_stream=False)
        self.transmit()

    # ══════════════════════════════════════════════════════════════════════
    # L'INPUT — §7.3, e il canale unico di §2.5
    # ══════════════════════════════════════════════════════════════════════

    def apri_input(self):
        """Lo stream del canale di input: **uno solo**, e si tiene aperto.

        ⛔ Si apre alla prima volta che serve, e non ad ogni messaggio: §2.5
           dice «uno solo … e tenuto aperto», e §7.3 conta gli `id` «su tutto
           il canale».  ⚠ Aprirlo e non chiuderlo non e' una svista: chiuderlo
           con FIN direbbe al server «il client non manda piu' input», che e'
           un'altra cosa da quella che questo banco vuole dire.
        """
        if self.inp_stream is None:
            self.inp_stream = self._http.create_webtransport_stream(
                self.sessione, is_unidirectional=True)
        return self.inp_stream

    def manda_puntatore(self, x, y):
        """⭐ `PUNTATORE(x, y)` — §7.3, coordinate sulla **tela**.

        ⛔ E si registra col canale `0x01` e con lo stream VERO: §11.1
           definisce il campo `canale` come «il byte alto di `tipo`», e
           l'arbitro **rifiuta** un blocco in cui i due non tornano — una
           registrazione che dichiarasse `0x00` farebbe leggere questi byte
           come se fossero controllo, e la regola del secondo non uscirebbe
           mai da questa traccia.
        """
        sid = self.apri_input()
        self.inp_id += 1
        # ⛔ §7.3: «microsecondi dell'orologio monotono del CLIENT», e «il
        #    client scrive microsecondi VERI e NON DEVE far credere a una
        #    precisione che non ha» (rilievo R1.27).  ⚠ Qui la grana e' quella
        #    di `time.monotonic()` di CPython — nanosecondi sul kernel Linux —
        #    quindi non si moltiplica niente per mille.
        ist_us = int(time.monotonic() * 1_000_000)
        b = inquadra(T_PUNTATORE,
                     struct.pack("!IQII", self.inp_id, ist_us, x, y))
        self._quic.send_stream_data(sid, b, end_stream=False)
        self.transmit()
        ms = None
        if self.reg is not None:
            self.reg.aggiungi(CLIENT, b, canale=0x01, stream=sid)
            ms = self.reg.blocchi[-1][6]
        return self.inp_id, ms

    # ══════════════════════════════════════════════════════════════════════
    # GLI APPUNTI — §7.4, e i tre messaggi letti da `RCP.md` e non dal C
    # ══════════════════════════════════════════════════════════════════════

    def appunti_manda(self, tipo, corpo):
        """Un messaggio del canale appunti, sul suo stream unidirezionale.

        ⛔ Uno stream per messaggio, e si chiude con FIN.  §2.5 dice «uno per
           trasferimento» e questo cliente ha scelto la lettura piu' stretta —
           la stessa del server — perche' a legare i messaggi di un
           trasferimento e' il campo `trasferimento` (§7.4), non lo stream.
           ⚠ Se le due implementazioni avessero letto §2.5 in modo diverso, il
             filo funzionerebbe lo stesso: e' la prova che la riga e' ambigua e
             che l'ambiguita' non morde.  Va scritta nel documento di fase.
        """
        sid = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=True)
        self._quic.send_stream_data(sid, inquadra(tipo, corpo), end_stream=True)
        self.transmit()
        return sid

    def appunti_annuncia(self, testo):
        """«Ho del testo nuovo» — §7.4, `APPUNTI_ANNUNCIO`."""
        d = testo.encode("utf-8")
        self.app_mio_id = 1 if self.app_mio_id >= 0xFFFFFFFF else self.app_mio_id + 1
        self.app_mio_testo = testo
        self.appunti_manda(0x0201, struct.pack("!II", self.app_mio_id, len(d)))
        print(f"   [app]  annunciato il trasferimento {self.app_mio_id}, "
              f"{len(d)} byte")
        return self.app_mio_id

    def appunti_chiedi(self, trasferimento=None):
        """«Mandamelo» — §7.4, `APPUNTI_CHIEDI`."""
        t = self.app_suo_id if trasferimento is None else trasferimento
        self.appunti_manda(0x0202, struct.pack("!I", t))
        print(f"   [app]  chiesto il trasferimento {t}")
        return t

    def _appunti_uno(self, tipo, corpo):
        """Un messaggio intero del canale appunti, gia' srotolato da §6.1."""
        if tipo == 0x0201:                                   # ANNUNCIO
            if len(corpo) != 8:
                self.app_violazioni.append(
                    f"APPUNTI_ANNUNCIO con {len(corpo)} byte: §7.4 ne vuole 8")
                return
            t, n = struct.unpack("!II", corpo)
            self.app_suo_id, self.app_suo_len = t, n
            self.app_annunci.append((t, n))
            print(f"   [app]  ⭐ il server annuncia il trasferimento {t}, {n} byte")
            self.app_evento.set()
            return
        if tipo == 0x0202:                                   # CHIEDI
            if len(corpo) != 4:
                self.app_violazioni.append(
                    f"APPUNTI_CHIEDI con {len(corpo)} byte: §7.4 ne vuole 4")
                return
            (t,) = struct.unpack("!I", corpo)
            self.app_chiesti.append(t)
            print(f"   [app]  ⭐ il server chiede il trasferimento {t}")
            # ⛔ §7.4: «un identificatore che non corrisponde a nessun annuncio
            #    vivo e' ERRORE_PROTOCOLLO».  ⚠ Qui NON si chiude la sessione:
            #    questo e' un banco, e il suo mestiere e' REGISTRARE che il
            #    server ha sbagliato, non punirlo — se chiudesse, il giro
            #    finirebbe e nessuno leggerebbe piu' niente.
            if t == 0 or t > self.app_mio_id:
                self.app_violazioni.append(
                    f"APPUNTI_CHIEDI per il trasferimento {t}, e io ne ho "
                    f"annunciati {self.app_mio_id} (§7.4)")
                return
            d = self.app_mio_testo.encode("utf-8")
            self.appunti_manda(0x0203, struct.pack("!I", t) + d)
            self.app_serviti += 1
            print(f"   [app]  serviti {len(d)} byte al server (trasferimento {t})")
            self.app_evento.set()
            return
        if tipo == 0x0203:                                   # TESTO
            if len(corpo) < 4:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO con {len(corpo)} byte: §7.4 ne vuole >= 4")
                return
            (t,) = struct.unpack("!I", corpo[:4])
            d = corpo[4:]
            if t != self.app_suo_id:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO per il trasferimento {t}, e l'annuncio vivo "
                    f"e' il {self.app_suo_id} (§7.4)")
            if len(d) != self.app_suo_len:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO porta {len(d)} byte e l'annuncio ne "
                    f"dichiarava {self.app_suo_len} (§7.4)")
            # ⛔ §5.4: «il testo DEVE essere UTF-8».  Si decodifica STRETTO: un
            #    decodificatore indulgente metterebbe caratteri di sostituzione
            #    al posto di un errore, e il banco direbbe verde su un testo che
            #    non e' quello che era stato copiato.
            try:
                self.app_ricevuto = d.decode("utf-8")
            except UnicodeDecodeError as e:
                self.app_violazioni.append(f"APPUNTI_TESTO non e' UTF-8: {e}")
                self.app_ricevuto = None
            print(f"   [app]  ⭐ arrivati {len(d)} byte dal server "
                  f"(trasferimento {t})")
            self.app_evento.set()
            return
        self.app_violazioni.append(
            f"tipo {tipo:#06x} sul canale appunti: §7.4 ne definisce TRE")

    def _decidi_canale(self, sid, carico, fine):
        """Il byte alto del `tipo` dice il canale (§2.5), e adesso c'e'."""
        self.uni_pref.pop(sid, None)
        if carico[0] == 0x02:
            self.uni_genere[sid] = "wt"
            self._appunti_stream(sid, carico, fine)
        elif carico[0] == 0x03:
            self.uni_genere[sid] = "video"
            self._video_stream(sid, carico, fine)
        else:
            # ⚠ Un canale che questo cliente non serve: lo DICE invece di
            #   tacere — «ricevuto e non usato» e «mai arrivato» non devono
            #   avere la stessa faccia.
            self.uni_genere[sid] = "altro"
            print(f"   [wt]   ⚠ stream uni {sid}, canale 0x{carico[0]:02x}: "
                  f"lecito e non servito da questo cliente (§2.5)")

    def _video_stream(self, sid, dati, fine):
        """Uno stream del canale VIDEO (§6.2): uno stream, un fotogramma.

        ⛔ E la fine dello stream E' la fine del fotogramma — ma **solo con un
           FIN**: uno stream azzerato porta un fotogramma incompleto, che §6.2
           impone di BUTTARE e non di consegnare al decodificatore.
        ⚠ Qui `aioquic` non distingue i due casi su questo cammino, quindi si
          registra quel che si e' visto e si dichiara: chi legge il file sa che
          i fotogrammi sono quelli finiti con FIN.
        """
        b = self.v_in.setdefault(sid, bytearray())
        b += dati
        # ⛔⛔ E DAL 21 AGOSTO 2026 I 28 BYTE DI §6.2 FINISCONO NELLA TRACCIA.
        #
        #    Fino a stamattina la registrazione portava **solo il canale di
        #    controllo**, e su una traccia senza video l'arbitro non puo'
        #    concludere niente su **T4** — *«un server che risponde
        #    `TELA(ADATTATA)` senza toccare il palco»*, che e' la crepa
        #    dichiarata di tutta la 6.6.  ⚠ `[M]` il primo giro vero contro il
        #    prodotto, 21 agosto: cinque tracce, e su tutte l'arbitro ha
        #    scritto *«dopo di lui la registrazione non porta NESSUN
        #    fotogramma: NON si giudica»*.  Una regola che non ha mai un
        #    ingresso e' una regola che non c'e'.
        #
        # ⛔⛔ E SI REGISTRA IL FLUSSO **INTERO**, non i soli 28 byte —
        #     e la prima stesura faceva l'altra cosa, per un'ora.
        #
        #  Sembrava furba: l'arbitro giudica misura, numero e codec, che stanno
        #  tutti nell'intestazione, e i pixel sono megabyte che nessuno legge.
        #  ⛔ **Ma un blocco di 28 byte marcato `fine = 0` dice all'arbitro una
        #  cosa falsa**: dice «di questo stream ho registrato tutto quel che e'
        #  passato, e non era finito».  ⇒ Il giudice del fotogramma non ha mai
        #  consumato quei flussi, e il fotogramma dopo — un delta legittimo —
        #  gli e' arrivato come **il primo della sessione**.
        #
        #  `[M]` 21 agosto 2026, giro vero sulla 7721: *«flusso 23: il primo
        #  fotogramma della sessione e' un DELTA — §5.2»*.  ⛔ **Un'accusa al
        #  PRODOTTO nata da una registrazione mia incompleta**, ed e' la cosa
        #  peggiore che un banco possa fare: §11.1 vuole i byte, e una traccia
        #  che ne porta un pezzo dichiarandosi intera non e' piu' un arbitro.
        #
        # ⚠ Il prezzo e' la misura del file, e si paga: chi vuole tracce
        #   piccole accorcia `--resta`, non il filo.
        if self.reg is not None:
            self.v_reg.add(sid)
            self.reg.aggiungi(SERVER, bytes(dati), canale=0x03, stream=sid,
                              fine=Registratore.FIN if fine
                              else Registratore.CONTINUA)
        if not fine:
            return
        del self.v_in[sid]
        if len(b) < 28:
            print(f"   [vid]  ⛔ stream {sid} finito con {len(b)} byte: §6.2 "
                  f"vuole 28 di intestazione")
            return
        tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI", bytes(b[:28]))
        self.v_fotogrammi.append((numero, tipo == 0x0301, l, a, bytes(b[28:])))

    def _appunti_stream(self, sid, dati, fine):
        """I byte di uno stream unidirezionale del SERVER, canale appunti.

        ⛔ Il preambolo di WebTransport si consuma qui: `0x40 0x54` piu' il
           varint della sessione.  ⚠ E si tiene per stream, perche' un
           pacchetto puo' tagliarlo in mezzo.
        """
        b = self.app_in.setdefault(sid, bytearray())
        b += dati
        while True:
            if len(b) < 6:
                break
            tipo, lung = struct.unpack("!HI", b[:6])
            if len(b) < 6 + lung:
                break
            corpo = bytes(b[6:6 + lung])
            del b[:6 + lung]
            self._appunti_uno(tipo, corpo)
        if fine:
            if b:
                self.app_violazioni.append(
                    f"lo stream di appunti {sid} e' finito con {len(b)} byte "
                    "che non fanno un messaggio (§6.1)")
            self.app_in.pop(sid, None)

    def _audio_datagram(self, d: bytes) -> None:
        """Un datagram di WebTransport: prefisso RFC 9297, poi §6.3.

        ⛔ Ogni scarto ha un contatore SUO.  «Non ho sentito niente» deve poter
           dire *perche'*: il prefisso sbagliato, il tipo sbagliato, il blocco
           corto e il blocco vecchio sono quattro difetti diversi con lo stesso
           sintomo, e senza quattro contatori si cerca per ore dalla parte
           sbagliata.
        """
        # Il prefisso: il quarto dell'identificativo dello stream della sessione.
        q, i = _varint(d, 0)
        if q is None:
            self.a_prefisso += 1
            return
        if self.sessione is not None and q != self.sessione // 4:
            # ⛔ Non e' un dettaglio di involucro: un prefisso sbagliato fa
            #    scartare il datagram AL BROWSER, senza un errore da nessuna
            #    parte — cioe' «l'audio non arriva» e basta.
            self.a_prefisso += 1
            return
        c = d[i:]
        if len(c) < 12:
            self.a_corti += 1
            return
        tipo = int.from_bytes(c[0:2], "big")
        if tipo != 0x0401:
            self.a_tipo += 1
            return
        codec = int.from_bytes(c[2:4], "big")
        istante = int.from_bytes(c[4:12], "big")
        # §6.3: «chi riceve scarta i datagram arrivati in ritardo rispetto a
        # quelli gia' consumati» — e QUANTO valga «gia' consumati» lo decide
        # `--audio-regola`.  ⛔ Il predefinito e' `vecchia`: con quella, queste
        # righe fanno esattamente quel che facevano prima del 23 agosto 2026.
        consegnato, _perche = self.a_vaglio.arrivo(istante, codec, len(c) - 12)
        self.a_vecchi = self.a_vaglio.scartati_vecchi
        self.a_ricevuti = self.a_vaglio.ricevuti
        if not consegnato:
            return
        self.a_byte += len(c) - 12
        if self.a_codec is None:
            self.a_codec = codec
            print(f"   [audio] ⭐ primo datagram: codec {codec} "
                  f"({'Opus' if codec == 1 else 'PCM' if codec == 2 else '⛔ ignoto'}), "
                  f"{len(c) - 12} byte di carico, prefisso {q} "
                  f"(sessione {self.sessione})")
        elif self.a_codec != codec:
            # ⚠ Il codec non cambia a meta' sessione: §4.3 lo negozia una volta.
            print(f"   [audio] ⛔ il codec e' CAMBIATO: {self.a_codec} → {codec}")
            self.a_codec = codec
        self.a_blocchi.append({"istante": istante, "codec": codec,
                               "byte": bytes(c[12:])})

    def quic_event_received(self, event: QuicEvent) -> None:
        nome = type(event).__name__
        # ═══ L'AUDIO — fase 7, `RCP.md` §6.3 ══════════════════════════════
        #
        # ⛔ Il datagram si legge QUI, prima di ogni altra cosa, e NON si passa
        #    allo strato H3 di aioquic: e' un datagram di WebTransport, non di
        #    HTTP/3 puro, e il suo primo campo e' il prefisso di RFC 9297.
        #
        # ⚠ E quel che questo lettore fa di piu' del browser e' il MOTIVO per
        #   cui esiste (`PIANO.md` §1.1): il browser dice «non sento niente»;
        #   questo dice QUALE regola di §6.3 e' stata violata e a quale byte.
        if nome == "DatagramFrameReceived":
            self._audio_datagram(event.data)
            return
        # ⛔ LA FINE DELLA CONNESSIONE SI STAMPA, SEMPRE.
        #
        #    E' l'unica riga che distingue «il tetto d'inattivita' di QUIC ha
        #    chiuso» da «il server ha liberato il posto lasciando aperta la
        #    connessione».  Senza, il quarto giro di B3 concludeva la seconda
        #    guardando /proc, che dice soltanto che un processo che dorme non
        #    e' morto (R8.2).
        if nome == "ConnectionTerminated":
            da_noi = " — CHIUSA DA NOI, a finestra finita" if self.chiusa_da_noi else ""
            print(f"   [quic] connessione TERMINATA: codice "
                  f"{getattr(event, 'error_code', '?')} · "
                  f"{getattr(event, 'reason_phrase', '') or '(nessun motivo)'}"
                  f"{da_noi}")
            self._cade(f"connessione TERMINATA ({getattr(event, 'reason_phrase', '') or 'senza motivo'})")
            self.messaggi.put_nowait(None)
            return
        if nome == "StreamDataReceived" and event.stream_id == self.controllo:
            self.arrivati += event.data
            self._sfoglia()
            if event.end_stream:
                self.finito = True
                self._cade("il canale di controllo si e' chiuso")
                self.messaggi.put_nowait(None)
            # ⛔ E NON si passa l'evento allo strato H3 di `aioquic`.
            #
            #    `[M]` 10 agosto 2026: passandoglielo, la prima stretta di mano
            #    e' morta con `CONNECTION_CLOSE 0x105 — DATA frame is not
            #    allowed in this state`, cioe' il CLIENTE che uccide la
            #    connessione mentre il server lavorava bene.
            #
            # ⚠ E' l'asimmetria gia' vista il 9 agosto: `aioquic` 1.2 sa
            #   CREARE uno stream WebTransport e non sa RICONOSCERLO quando
            #   risponde — quindi il suo strato HTTP/3 legge `ECCOMI` come un
            #   frame DATA su uno stream di richiesta.  Il banco di B2 non se
            #   n'era accorto perche' l'eco erano quattro byte; centosedici
            #   bastano a far cadere tutto.
            return
        # ⛔⭐ GLI STREAM UNIDIREZIONALI DEL SERVER — §2.5, e da qui passano il
        #     video (0x03) e gli appunti (0x02).  ⚠ Non tutti sono nostri: fra
        #     gli unidirezionali del server ci sono il canale di controllo di
        #     HTTP/3 e i due di QPACK, che sono di `aioquic`.  Uno stream
        #     WebTransport si riconosce dal suo tipo, `0x54` — che come `0x41`
        #     non sta in un byte: sul filo sono `0x40 0x54`.
        # ⛔⭐ GLI STREAM UNIDIREZIONALI DEL SERVER — §2.5: di qui passano il
        #     video (0x03) e gli appunti (0x02).  ⚠ Non tutti sono nostri: fra
        #     gli unidirezionali del server ci sono il canale di controllo di
        #     HTTP/3 e i due di QPACK, che sono di `aioquic`.
        #
        # ⛔⛔ E SI DECIDE SOLO QUANDO C'E' DA DECIDERE — tre volte in una sera
        #      il difetto e' stato lo stesso, e vale la pena scriverlo una volta
        #      per tutte: **classificare su byte che non sono ancora arrivati**.
        #
        #      1. si aspettavano DUE byte per riconoscere il preambolo, e gli
        #         stream QPACK ne portano UNO ⇒ inghiottiti, e il server ci
        #         congedava per `TEMPO_SCADUTO`;
        #      2. il giudizio «altro» non aveva un ramo suo ⇒ i byte del video
        #         finivano nello strato HTTP/3;
        #      3. `[M]` **il primo pacchetto di uno stream video porta il solo
        #         preambolo — `40 54 00`, tre byte, carico ZERO** ⇒ si decideva
        #         «non e' ne' appunti ne' video» su uno stream che era video, e
        #         si buttava tutto il resto.
        #
        # ⇒ La regola: finche' il byte che decide non e' arrivato, lo stato e'
        #   «lo so che e' nostro e non so ancora che cos'e'» — che e' uno stato
        #   VERO, non un giudizio.  ⛔ `LEZIONI.md` §1.9: «non lo so» e «non lo
        #   e'» non devono avere la stessa faccia.
        if nome == "StreamDataReceived" and (event.stream_id & 0x03) == 0x03:
            sid = event.stream_id
            if os.environ.get("B3_SPIA"):
                print(f"   [spia] uni {sid} genere={self.uni_genere.get(sid)} "
                      f"len={len(event.data)} fin={event.end_stream} "
                      f"primi={bytes(event.data[:6]).hex()}")
            g = self.uni_genere.get(sid)
            if g == "h3":
                pass                       # e' di `aioquic`: gli si lascia
            elif g == "wt":
                self._appunti_stream(sid, event.data, event.end_stream)
                return
            elif g == "video":
                self._video_stream(sid, event.data, event.end_stream)
                return
            elif g == "altro":
                return                     # nostro, e questo cliente non lo serve
            elif g == "wt-attesa":
                # Il preambolo c'e' gia': manca il byte che dice il canale.
                p = self.uni_pref.setdefault(sid, bytearray())
                p += event.data
                if p:
                    self._decidi_canale(sid, bytes(p), event.end_stream)
                return
            else:
                # ⛔ Si decide sul PRIMO byte: uno stream WebTransport comincia
                #    per `0x40` (il varint del tipo 0x54 non sta in un byte);
                #    qualunque altro primo byte e' di `aioquic`, e i suoi byte
                #    non devono passare di qui nemmeno per un giro.
                if not event.data:
                    return
                if event.data[0] != 0x40:
                    self.uni_genere[sid] = "h3"
                else:
                    p = self.uni_pref.setdefault(sid, bytearray())
                    p += event.data
                    if len(p) < 2:
                        return
                    if p[1] != 0x54:
                        self.uni_genere[sid] = "altro"
                        self.uni_pref.pop(sid, None)
                        print(f"   [wt]   ⚠ stream uni {sid} comincia per 0x40 "
                              f"0x{p[1]:02x}: non e' WebTransport, e i suoi byte "
                              f"sono stati trattenuti")
                        return
                    q, i = _varint(bytes(p), 2)
                    if q is None:
                        return         # il varint della sessione non e' tutto qui
                    resto = bytes(p[i:])
                    self.uni_genere[sid] = "wt-attesa"
                    self.uni_pref[sid] = bytearray(resto)
                    if resto:
                        self._decidi_canale(sid, resto, event.end_stream)
                    return
        if nome == "StreamDataReceived" and event.stream_id == self.sessione:
            # la capsula di chiusura della sessione (§3.1 punto 3)
            codice, nuda = _capsula_chiusura(event.data)
            if codice is not None:
                if nuda:
                    # ⛔ La capsula NUDA, senza il frame DATA che la porta.
                    #
                    #    E' quel che questo server faceva fino al 10 agosto 2026
                    #    (rilievo R10.1): sul filo della CONNECT le capsule
                    #    viaggiano DENTRO i frame DATA (RFC 9297), e un browser
                    #    che legge `0x2843` come tipo di frame HTTP/3 lo trova
                    #    sconosciuto e lo **ignora** (RFC 9114 §9).  Il motivo
                    #    non arrivava, e restava solo il FIN — cioe' `codice 0`.
                    #
                    # ⭐ Il banco lo legge lo stesso, ma lo DICHIARA: un cliente
                    #    indulgente che accettasse le due forme senza dire
                    #    quale ha visto nasconderebbe di nuovo quel difetto, ed
                    #    e' l'indulgenza che `REVIEWER.md` §5 vieta.
                    print("   [wt]   ⛔ capsula di chiusura NUDA, senza frame "
                          "DATA: un browser la ignorerebbe (RFC 9297)")
                self.codice_chiusura = codice
                print(f"   [wt]   sessione chiusa dal server, codice {codice:#04x}"
                      f" = {MOTIVI.get(codice, '?')}")
                self._cade(f"sessione chiusa dal server, codice {codice:#04x}"
                           f" = {MOTIVI.get(codice, '?')}")
            if event.end_stream:
                self.finito = True
                self._cade("la sessione WebTransport si e' chiusa")
                self.messaggi.put_nowait(None)
        for ev in self._http.handle_event(event):
            if isinstance(ev, HeadersReceived) and not self.accettata.done():
                self.accettata.set_result(
                    dict(ev.headers).get(b":status", b"?").decode())

    def _sfoglia(self):
        while len(self.arrivati) >= 6:
            tipo, lung = struct.unpack("!HI", self.arrivati[:6])
            if len(self.arrivati) < 6 + lung:
                return
            corpo = bytes(self.arrivati[6:6 + lung])
            grezzo = bytes(self.arrivati[:6 + lung])
            del self.arrivati[:6 + lung]
            # ⛔ SI REGISTRA QUI, all'arrivo: vedi il riquadro su `self.reg`.
            if self.reg is not None:
                self.reg.aggiungi(SERVER, grezzo)
                # ⭐ L'istante che l'arbitro leggera' nel file, preso dove il
                #    file lo prende.  ⛔ Non `time.monotonic()` di adesso: il
                #    `dt` del secondo di grazia si conta fra DUE `istante_ms`
                #    di §11.1, e contarlo su un orologio diverso vorrebbe dire
                #    che il ritardo dichiarato dal banco e quello letto
                #    dall'arbitro sono due numeri diversi — cioe' esattamente
                #    l'errore che il confine del secondo non perdona.
                if NOME.get(tipo) == "TELA":
                    self.ultimo_tela_ms = self.reg.blocchi[-1][6]
                if NOME.get(tipo) in ("TELA", "CURSORE_FORMA") \
                        and self.messaggi.qsize() > 0:
                    # ⚠ «E' arrivato mentre ce n'erano gia' altri in coda» non
                    #   e' una violazione: e' un fatto, e chi guarda deve
                    #   poterlo leggere senza aprire la traccia.
                    print(f"   ·  [filo] {NOME.get(tipo)} arrivato con "
                          f"{self.messaggi.qsize()} messaggi gia' in coda")
            self.messaggi.put_nowait((tipo, corpo, grezzo))


async def attendi(cli, quale, attesa=10.0, reg=None):
    m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
    if m is None:
        raise RuntimeError(f"il canale di controllo si e' chiuso: {cli.caduta}")
    tipo, corpo, grezzo = m
    nome = NOME.get(tipo, f"{tipo:#06x}")
    # ⛔ SI REGISTRA QUEL CHE ARRIVA, NON QUEL CHE SI SPERAVA — rilievo R8.9.
    #
    #    La registrazione si scriveva solo lungo la strada che riesce: un
    #    `CONGEDO(GIA_ATTIVA_REMOTA)` faceva sollevare l'eccezione qui sotto
    #    PRIMA di essere messo nella traccia, e `b3-terza.rcpreg` — cioe'
    #    l'unico oggetto che il terzo giro esiste per produrre — non arrivava
    #    mai all'arbitro di B4.  ⭐ Il rifiuto e' una misura, non un incidente.
    #    ⭐ E dal 21 agosto 2026 la riga `reg.aggiungi()` NON e' piu' qui: si
    #       registra all'ARRIVO, dentro `Cliente._sfoglia()`, o i messaggi che
    #       nessuno aspetta non entrano nella traccia (riquadro in `__init__`).
    #       ⚠ `reg` resta nella firma perche' i chiamanti lo passano, e
    #         toglierlo sarebbe una modifica piu' larga di quel che serve.
    if quale and nome != quale:
        if nome == "CONGEDO":
            motivo = corpo[0] if corpo else 0
            raise RuntimeError(
                f"CONGEDO invece di {quale}: motivo {motivo:#04x} = "
                f"{MOTIVI.get(motivo, '?')}")
        if nome == "RESPINTO":
            motivo = corpo[0] if corpo else 0
            raise RuntimeError(
                f"RESPINTO: motivo {motivo:#04x} = {MOTIVI.get(motivo, '?')}")
        raise RuntimeError(f"atteso {quale}, arrivato {nome}")
    return nome, corpo, grezzo


async def chiedi_tela(cli, reg, lar, alt, tetto):
    """⭐ `ADATTA_TELA(lar, alt)` e l'attesa del `TELA` — RCP.md §7.1.

    Restituisce `(esito, motivo, tela_lar, tela_alt, ms)`, oppure `None` se il
    tetto scade **senza nessuna risposta**.

    ⛔⛔ IL TETTO E' LA MISURA, NON UNA COMODITA'.

    §7.1: *«A ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`,
    riuscito o no.  Un silenzio lascia il client ad aspettare per sempre una
    risposta che non arrivera', e il sintomo e' "l'applicazione si e'
    piantata"»*.  ⇒ Un cliente di prova che aspettasse **senza tetto**
    riprodurrebbe il sintomo invece di misurarlo: il banco resterebbe appeso, e
    chi guarda direbbe «il banco si e' piantato» — che e' la stessa frase, dal
    lato sbagliato.

    ⚠ E il tetto NON e' una regola del protocollo: §7.1 non dice **entro
      quanto**.  ⛔ Quindi la scadenza non si registra come violazione dal
      cliente: si registra il **silenzio**, e a giudicarlo e' l'arbitro, che
      legge i byte e il campo `fine` di §11.1.  Il cliente misura; il verdetto
      e' di `01-b4-validatore.py`.

    ⚠ E si registra quel che arriva NEL FRATTEMPO — `CURSORE_FORMA` e i
      fotogrammi arrivano quando vogliono — perche' una traccia con dei buchi
      non e' giudicabile: §11.1 vuole i byte, non quelli che aspettavamo.
    """
    b = inquadra(T["ADATTA_TELA"], struct.pack("!II", lar, alt))
    cli.manda(b)
    reg.aggiungi(CLIENT, b)
    print(f"   → ADATTA_TELA {lar}x{alt}")
    t0 = time.monotonic()
    scade = t0 + tetto
    while True:
        resta = scade - time.monotonic()
        if resta <= 0:
            ms = (time.monotonic() - t0) * 1000
            print(f"   ⛔ NESSUN TELA dopo {ms:.0f} ms: §7.1 vuole una risposta "
                  f"«riuscita o no».  ⚠ E' il silenzio che «lascia il client ad "
                  f"aspettare per sempre»")
            return None
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            continue
        if m is None:
            print(f"   ⛔ il canale si e' chiuso mentre aspettavo il TELA: "
                  f"{cli.caduta}")
            return None
        tipo, corpo, grezzo = m
        # ⭐ (registrato all'arrivo da `Cliente._sfoglia()`, non qui)
        nome = NOME.get(tipo, f"{tipo:#06x}")
        if nome != "TELA":
            print(f"   ·  nel frattempo: {nome} ({len(corpo)} byte)")
            if nome == "CONGEDO":
                mot = corpo[0] if corpo else 0
                print(f"   ⛔ CONGEDO invece del TELA: motivo {mot:#04x} = "
                      f"{MOTIVI.get(mot, '?')}")
                return None
            continue
        ms = (time.monotonic() - t0) * 1000
        if len(corpo) < 10:
            print(f"   ⛔ TELA con un corpo di {len(corpo)} byte: §7.1 ne vuole "
                  f"10 (u8, u8, u32, u32) — i byte sono nella traccia")
            return None
        es, mot = corpo[0], corpo[1]
        tl, ta = struct.unpack("!II", corpo[2:10])
        print(f"   ← TELA {TELA_ESITO.get(es, es)}"
              f"/{TELA_MOTIVO.get(mot, mot)} tela in vigore {tl}x{ta} "
              f"dopo {ms:.0f} ms")
        return es, mot, tl, ta, ms


def scrivi_video(a, cli):
    """I fotogrammi presi dal filo, per un decodificatore TERZO.

    ⛔ E si chiama DOPO l'attesa di `--resta`, non prima: alla riga in cui la
       sessione si apre non e' ancora arrivato nessun fotogramma, e un file
       vuoto direbbe «il server non manda video» su un server che lo manda.
       ⚠ E' costato un giro, il 17 agosto 2026 — un difetto del banco con la
         faccia di un difetto del prodotto, il terzo della giornata.
    """
    if not a.video_scrivi or not cli.v_fotogrammi:
        if a.video_scrivi:
            print("   [vid]  ⛔ nessun fotogramma preso dal filo: niente file")
        return
    # ⛔ I fotogrammi si concatenano NELL'ORDINE DEL NUMERO (§6.2): gli stream
    #    sono indipendenti e possono arrivare fuori ordine, e un flusso rimesso
    #    in fila male darebbe artefatti che sarebbero NOSTRI del banco — cioe'
    #    la risposta sbagliata alla domanda che questo file esiste per fare.
    ordinati = sorted(cli.v_fotogrammi, key=lambda f: f[0])
    with open(a.video_scrivi, "wb") as f:
        for _, _, _, _, d in ordinati:
            f.write(d)
    chiavi = sum(1 for x in ordinati if x[1])
    print(f"   [vid]  {len(ordinati)} fotogrammi ({chiavi} chiavi), "
          f"{ordinati[0][2]}x{ordinati[0][3]}, scritti in {a.video_scrivi}")


def scrivi_appunti(a, cli):
    """L'esito degli appunti, in JSON, per il giudice del banco.

    ⛔ E i fatti si scrivono TUTTI, anche quelli che non servono a questo giro:
       «nessun annuncio», «annuncio senza testo» e «testo diverso da quello
       copiato» sono tre difetti con lo stesso sintomo, e un file che portasse
       solo il verdetto li renderebbe indistinguibili (`LEZIONI.md` §1.9).

    ⛔ E le VIOLAZIONI di §7.4 si scrivono anche quando il giro e' verde: un
       server che consegna il testo giusto violando il protocollo lungo la
       strada e' un server che il banco deve bocciare — «funziona» non e'
       «e' conforme».
    """
    if not a.appunti_scrivi:
        return
    esito = {
        "annunci_dal_server": cli.app_annunci,
        "chiesti_dal_server": cli.app_chiesti,
        "serviti_al_server": cli.app_serviti,
        "mio_id": cli.app_mio_id,
        "mio_testo": cli.app_mio_testo,
        # ⛔ `None` = non e' arrivato niente, `""` = e' arrivata una stringa
        #    vuota.  Sono due fatti diversi, e JSON li tiene separati.
        "ricevuto": cli.app_ricevuto,
        "violazioni": cli.app_violazioni,
    }
    with open(a.appunti_scrivi, "w") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    print(f"   [app]  esito scritto in {a.appunti_scrivi} "
          f"({len(cli.app_violazioni)} violazioni di §7.4)")


def scrivi_audio(a, cli):
    """I blocchi d'audio su disco, e i sei contatori a schermo.

    ⛔ I contatori si stampano SEMPRE, anche a zero: `CODER.md` §3.10 — «una
       lettura negata non e' una lettura che dice zero».  Un giro che non
       stampa niente e uno che ha ricevuto zero datagram devono avere due
       facce diverse.
    """
    if cli is None:
        return
    print(f"   [audio] ricevuti {cli.a_ricevuti} · {cli.a_byte} byte di carico · "
          f"codec {cli.a_codec if cli.a_codec is not None else '(nessuno)'}")
    # ⛔ `vecchi {n}` RESTA DOV'ERA E COME ERA: `07-b64-rete.py`:538 lo legge
    #    con la regex `vecchi (\d+)` su questa riga.  I quattro della fase 9
    #    si aggiungono IN CODA, dove nessuna regex di prima li incontra.
    print(f"   [audio] scartati — corti {cli.a_corti} · tipo {cli.a_tipo} · "
          f"prefisso {cli.a_prefisso} · vecchi {cli.a_vecchi}")
    # ⛔ I contatori della fase 9 si stampano SEMPRE e con TUTT'E DUE le
    #    regole, anche tutti a zero: «una lettura negata non e' una lettura che
    #    dice zero» (`CODER.md` §3.10).  ⚠ Con la regola vecchia `tardivi`,
    #    `fuori` e `rec` sono zero PER COSTRUZIONE — non e' salute, e' che
    #    quella regola non li puo' produrre.
    print(f"   [audio] riordino — {cli.a_vaglio.riga()}")
    print(f"   [audio] riordino — {cli.a_vaglio.riga_conti()}")
    if not a.audio_scrivi:
        return
    import base64
    with open(a.audio_scrivi, "w") as f:
        for b in cli.a_blocchi:
            f.write(json.dumps({"istante": b["istante"], "codec": b["codec"],
                                "byte": base64.b64encode(b["byte"]).decode()}) + "\n")
    print(f"   [audio] blocchi scritti in {a.audio_scrivi} ({len(cli.a_blocchi)})")


def scrivi_traccia(a, reg, cli=None):
    """La registrazione si scrive presto, e si RISCRIVE a ogni tappa.

    ⛔ «Non ho niente da giudicare» e «conforme» sono due cose diverse: un file
       vuoto non si scrive, cosi' chi lo cerca vede che non c'e' invece di
       giudicare zero blocchi.

    ⚠⛔ **E dal 16 agosto 2026 si RISCRIVE, dove prima si scriveva una volta
        sola.**  La guardia `scritta` era giusta finche' dopo `SESSIONE` questo
    programma non registrava piu' niente: adesso registra l'`ADATTA_TELA`, il
    `TELA`, la `VISTA` e la chiusura del canale — ⛔ e con la guardia in piedi
    **la meta' interessante della traccia non arrivava nel file**.  Un banco
    che chiude il file prima di fare la cosa che deve misurare consegna
    all'arbitro una registrazione conforme e vuota.

    ⭐ E il FIN si segna QUI, non nell'evento che lo riceve: i messaggi del
       server passano per una coda, e marcare la fine dal gestore dell'evento
    scriverebbe la chiusura **prima** di messaggi che nella traccia vengono
    dopo.  ⛔ Sarebbe un byte falso proprio nel campo che §11.1 ha aggiunto per
    non far confondere una fine con un'interruzione.
    """
    if not (a.registra and reg.blocchi):
        return
    if cli is not None and cli.finito and not getattr(reg, "fine_segnata", False):
        reg.segna_fine(SERVER, Registratore.FIN)
        reg.fine_segnata = True
    reg.scrivi(a.registra)
    reg.scritta = True
    print(f"   registrazione: {a.registra} ({len(reg.blocchi)} blocchi)")


def corpo_ciao(audio="opus,pcm", video="h264", prof="8,10"):
    # ⛔ `audio` si puo' restringere dalla riga di comando, e NON e' un trucco:
    #    e' quel che dichiara un client che Opus non lo sa fare.  §4.3 impone
    #    `pcm` a entrambi proprio per questo — e' «la base sempre disponibile»,
    #    e il controllo positivo di Opus.  ⇒ `--audio-codec pcm` esercita la
    #    negoziazione, non la scavalca.
    # ⛔ E anche il VIDEO si puo' restringere, dal 17 agosto 2026: serve a
    #    esercitare il ramo del ripiego senza un browser di mezzo.  ⚠ Non e' un
    #    trucco — e' quel che dichiara un client che l'HEVC non lo sa
    #    decodificare, cioe' **esattamente Firefox**.  §4.3 fa scegliere al
    #    server dentro l'intersezione, e restringere l'intersezione e' un uso
    #    del protocollo, non un aggiramento.
    #
    # ⛔⛔⛔ HO CAMBIATO IL METRO — 23 agosto 2026, sera (`fasi/09` §14.1).
    #    Il predefinito era **`hevc,av1`** ed e' rimasto tale quando AV1 e'
    #    uscito dal prodotto (20 agosto, `DECISIONI.md` §1.13-ter): il server
    #    sceglieva dunque **HEVC** in ogni giro di banco, mentre `pagina.html`
    #    (`PREFERENZA = ["hevc", "h264"]`, riga 818) dichiara **solo i codec che
    #    hanno davvero DIPINTO la sonda** — e su Firefox HEVC non dipinge.
    #    ⇒ Il banco misurava un codec che l'utente non riceve mai.
    #    `[M]` stessa scena, stessa tela, stesso QP 26: **21,18 Mbit/s in HEVC
    #    contro 7,92 in H.264**, un fattore **2,7** (`fasi/09` §13.5.1).
    #    ⇒ ⛔ **I numeri di banda presi prima di questa riga NON si confrontano
    #      con quelli presi dopo.**  Il vecchio metro si rifa' con
    #      `--video-codec hevc`, e va detto ogni volta che lo si usa.
    voci = [("video.codec", video), ("video.profondita", prof),
            ("audio.codec", audio), ("video.livello", "5.1"),
            ("video.misura_massima", "3840x2160"), ("appunti.testo", "si"),
            ("input.tocco", "no"), ("client.nome", "cliente-di-prova 0.1.0")]
    out = struct.pack("!HH", 1, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


async def principale(a) -> int:
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                            max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    reg = Registratore()
    autorita = f"{a.indirizzo}:{a.porta}"

    print(f"== cliente di prova RCP -> https://{autorita}{a.percorso}")
    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        print(f"   CONNECT estesa: :status = {stato}")
        if stato != "200":
            return 1
        # ⛔ Lo stream VERO del canale di controllo finisce nella traccia: §11.1
        #    lo chiede, e §2.5 ci fa poggiare sopra P3 — «un fotogramma sullo
        #    stream del canale di controllo».  Con lo `0` scritto a mano quel
        #    controllo dell'arbitro guardava un numero inventato.
        reg.stream = cli.apri_controllo()
        # ⛔ E il registratore si consegna al CLIENTE, perche' da qui in poi i
        #    byte del server si registrano dove arrivano (riquadro in
        #    `Cliente.__init__`).  ⚠ Prima di questa riga non puo' essere
        #    arrivato niente: il canale di controllo non esisteva.
        cli.reg = reg

        # ⛔ LA TRACCIA SI SCRIVE ANCHE QUANDO LA STRETTA DI MANO NON RIESCE.
        #
        #    Rilievo R8.9: il terzo giro di B3 esiste per produrre UN oggetto —
        #    la registrazione di chi ha ricevuto il `CONGEDO(0x0F)` — e quella
        #    registrazione non veniva scritta mai, perche' l'eccezione partiva
        #    prima.  ⭐ Il validatore di B4 e' l'arbitro anche del rifiuto.
        try:
            # ── CIAO ────────────────────────────────────────────────────────
            b = inquadra(T["CIAO"], corpo_ciao(a.audio_codec, a.video_codec, a.video_profondita))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "ECCOMI", reg=reg)
            versione = struct.unpack("!H", corpo[:2])[0]
            print(f"   ECCOMI: versione {versione}")

            # ── CREDENZIALI ─────────────────────────────────────────────────
            corpo_c = s(a.utente) + s(a.parola)
            b = inquadra(T["CREDENZIALI"], corpo_c)
            # §11.1: la parola si oscura, la lunghezza resta vera
            ini = 6 + 2 + len(a.utente.encode()) + 2
            qua = len(a.parola.encode())
            imp = hashlib.sha256(a.parola.encode()).digest()
            cli.manda(b)
            reg.aggiungi(CLIENT,
                         b[:ini] + bytes([0x2A]) * qua + b[ini + qua:],
                         [(ini, qua, imp)])
            t0 = time.monotonic()
            nome, corpo, grezzo = await attendi(cli, "AMMESSO", attesa=20, reg=reg)
            ms = (time.monotonic() - t0) * 1000
            # ⭐ §4.4-bis: il ritardo fisso vale ANCHE per AMMESSO.  Si
            #    cronometra qui perche' nessun altro banco lo vede, e una
            #    regressione che lo togliesse non farebbe fallire niente.
            print(f"   AMMESSO dopo {ms:.0f} ms"
                  + ("   ⭐ il secondo fisso c'e'" if ms >= 1000 else
                     "   ⛔ MENO DI UN SECONDO: §4.4-bis violata"))
            if ms < 1000:
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 1

            # ── ATTACCA ─────────────────────────────────────────────────────
            b = inquadra(T["ATTACCA"],
                         struct.pack("!IIII", a.larghezza, a.altezza,
                                     a.larghezza, a.altezza) + s(a.disposizione))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "SESSIONE", reg=reg)
        except Exception:
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
            raise
        stato_s = corpo[0]
        lar, alt = struct.unpack("!II", corpo[1:9])
        n = struct.unpack("!H", corpo[9:11])[0]
        desktop = corpo[11:11 + n].decode()
        print(f"   ⭐ SESSIONE: stato={stato_s} tela={lar}x{alt} desktop={desktop}")

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ LA STRADA DELLA TELA — sottofase 6.6, 16 agosto 2026
        #
        #    ⛔ *«Nessuno dei due manda un `ADATTA_TELA`»*: da qui in poi non e'
        #       piu' vero.  E c'e' una ragione in piu' per farlo **all'attacco**,
        #       ed e' del 15 agosto: `DECISIONI.md` §5.0-sexies fa chiedere al
        #       client *«la tela della propria finestra all'attacco di ogni
        #       sessione, da se'»* — quindi questa non e' una prova di
        #       laboratorio, e' quel che il client vero fa ogni volta.
        #
        # ⚠ E il conto in volo si tiene ANCHE QUI, non solo nell'arbitro: §6.2
        #   lega al conto il modo in cui il client tratta i fotogrammi, e un
        #   cliente di prova che non lo tenesse non potrebbe accorgersi di un
        #   `TELA` che non ha chiesto.
        tela_viva = (lar, alt)
        # ⭐ La tela in vigore **PRIMA** dell'ultimo `TELA(ADATTATA)`: e' quella
        #    su cui le coordinate in volo di §7.1 sono ancora valide, ed e'
        #    l'unico numero da cui si puo' costruire il caso del secondo di
        #    grazia senza inventarselo.  ⛔ `None` finche' nessun adattamento e'
        #    riuscito: allora la scena non esiste, e si dice invece di fingerla.
        tela_prec_adattata = None
        esiti_tela = []
        if a.adatta:
            for al, aa, quando in a.adatta:
                if quando:
                    # ⭐ E' il ridimensionamento **a caldo**: la sessione e' gia'
                    #    viva e in mezzo passano fotogrammi.  ⚠ Si aspetta con
                    #    gli occhi aperti — un `sleep` non si accorgerebbe che
                    #    la sessione e' caduta nel frattempo, e la misura
                    #    dell'`ADATTA_TELA` sarebbe presa su una connessione
                    #    morta (rilievi R8.2, R8.4).
                    print(f"   ·  aspetto {quando} s a sessione viva")
                    try:
                        await asyncio.wait_for(cli.caduto.wait(), timeout=quando)
                        print(f"   ⛔ caduta prima di poter chiedere la tela: "
                              f"{cli.caduta}")
                        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                        return 4
                    except asyncio.TimeoutError:
                        pass
                prima_di_questo = tela_viva
                r = await chiedi_tela(cli, reg, al, aa, a.attesa_tela)
                esiti_tela.append(r)
                if r is not None and r[0] == 1:
                    tela_prec_adattata = prima_di_questo
                if r is None:
                    # ⛔ Il silenzio si REGISTRA e si esce con un codice suo: e'
                    #    la scena di §7.1, e va distinta da «la sessione e'
                    #    caduta» (4) e da «tutto bene» (0).
                    scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                    return 5
                tela_viva = (r[2], r[3])
        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ IL SECONDO DI GRAZIA DI §7.1, PUNTATO CONTRO IL SERVER
        #     — 22 agosto 2026, e fino a stamattina non era mai stato fatto.
        #
        # §7.1: *«Dopo aver mandato `TELA(ADATTATA)` il server DEVE accettare
        # per **un secondo** coordinate di input valide sulla tela
        # **precedente**, saturandole alla nuova e scrivendolo nel registro;
        # passato quel secondo, sono `ERRORE_PROTOCOLLO`»*.
        #
        # ⛔⛔ LA TRAPPOLA, E VA DISINNESCATA PRIMA DI SCEGLIERE IL RITARDO.
        #
        #     La regola e' del **SERVER**; la registrazione la prende il
        #     **CLIENT**.  L'intervallo visto qui e' piu' CORTO di quello vero
        #     di mezzo giro di rete per lato (§11.1, *«il tempo registrato e'
        #     di CHI REGISTRA»*).  ⇒ Un caso «dentro il secondo» messo a 0,95 s
        #     potrebbe essere 1,02 s per il server, e il banco accuserebbe il
        #     prodotto di un difetto che non ha — o, peggio, si assolverebbe da
        #     solo.
        #
        # ⭐ La cura non e' un calcolo: e' **stare lontani dal confine**, e
        #    dichiarare perche'.  Chi chiama questo cliente sceglie il ritardo;
        #    qui si stampa il margine, cosi' un ritardo scelto male si vede
        #    invece di produrre un verdetto.
        #
        # ⛔ E LA COORDINATA NON SI INVENTA: e' **l'ultimo pixel della tela
        #    precedente**, `(prec_l - 1, prec_a - 1)`.  Due ragioni, e la
        #    seconda vale piu' della prima:
        #      · e' valida sulla tela di prima **per definizione** (§7.3: «0 <=
        #        x < tela_larghezza»), quindi il caso e' quello di §7.1 e non
        #        «una coordinata sbagliata» — che §7.1 NON copre, e il server
        #        ha una riga apposta per dirlo;
        #      · saturata, deve finire **esattamente** su `(nuova_l - 1,
        #        nuova_a - 1)`, cioe' su un punto NOTO.  ⭐ E' il controllo che
        #        attraversa la conversione: un server che rifiutasse la
        #        coordinata *dicendolo nel registro* ma la applicasse lo stesso
        #        passerebbe l'arbitro, e non passerebbe questo.
        if a.puntatore_vecchia is not None:
            if tela_prec_adattata is None:
                print("   ⛔ --puntatore-vecchia, ma nessun TELA(ADATTATA) e' "
                      "riuscito: non esiste nessuna «tela precedente», e una "
                      "coordinata scelta a caso proverebbe un'ALTRA regola "
                      "(§7.3 «fuori dalla tela»), non il secondo di grazia")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            px = tela_prec_adattata[0] - 1
            py = tela_prec_adattata[1] - 1
            if px < tela_viva[0] and py < tela_viva[1]:
                print(f"   ⛔ ({px},{py}) e' DENTRO la tela in vigore "
                      f"{tela_viva[0]}x{tela_viva[1]}: la scena di §7.1 non e' "
                      f"esercitata affatto — serve una tela nuova piu' piccola "
                      f"della precedente {tela_prec_adattata[0]}x"
                      f"{tela_prec_adattata[1]}")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            # La saturazione attesa, calcolata come §7.1 la descrive: «all'ultimo
            # pixel valido».
            sx = px if px < tela_viva[0] else tela_viva[0] - 1
            sy = py if py < tela_viva[1] else tela_viva[1] - 1
            rit_ms = int(round(a.puntatore_vecchia * 1000))
            print(f"   ⛔ ATTESO, dichiarato PRIMA: PUNTATORE ({px},{py}) — "
                  f"valido sulla tela precedente {tela_prec_adattata[0]}x"
                  f"{tela_prec_adattata[1]}, fuori da quella in vigore "
                  f"{tela_viva[0]}x{tela_viva[1]} — a {rit_ms} ms dal "
                  f"TELA(ADATTATA)")
            if rit_ms > 1000:
                print(f"      ⇒ oltre il secondo di grazia, e il margine e' "
                      f"{rit_ms - 1000} ms.  ⛔ Il server DEVE rifiutare: il "
                      f"SUO intervallo e' ancora piu' lungo di questo")
            else:
                print(f"      ⇒ dentro il secondo, e il margine e' "
                      f"{1000 - rit_ms} ms — cioe' quanto giro di rete ci "
                      f"vorrebbe per portarlo oltre.  ⛔ Il server DEVE "
                      f"saturare a ({sx},{sy}) e scriverlo nel registro")
            if cli.ultimo_tela_ms is None:
                print("   ⛔ nessun istante registrato per il TELA: non so da "
                      "quando contare")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            bersaglio = cli.ultimo_tela_ms + rit_ms
            # ⛔ SI ASPETTA CON GLI OCCHI APERTI — rilievi R8.2/R8.4.  Un
            #    `sleep` non si accorgerebbe che la sessione e' morta nel
            #    frattempo, e il `PUNTATORE` partirebbe su una connessione gia'
            #    chiusa: il banco misurerebbe se stesso.
            caduto_prima = False
            while True:
                resta = (bersaglio - reg.istante()) / 1000.0
                if resta <= 0:
                    break
                try:
                    await asyncio.wait_for(cli.caduto.wait(), timeout=resta)
                    caduto_prima = True
                    break
                except asyncio.TimeoutError:
                    pass
            if caduto_prima:
                print(f"   ⛔ la sessione e' caduta PRIMA del PUNTATORE: "
                      f"{cli.caduta} — la regola del secondo non e' stata "
                      f"esercitata")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 4
            pid, pms = cli.manda_puntatore(px, py)
            dt = None if pms is None else pms - cli.ultimo_tela_ms
            print(f"   → PUNTATORE id={pid} ({px},{py}) — dt registrato "
                  f"{dt} ms dal TELA(ADATTATA).  ⚠ E' il numero che l'arbitro "
                  f"leggera': l'intervallo del SERVER e' piu' lungo di questo")

            # ═══════════════════════════════════════════════════════════════
            # ⭐⛔ IL TERZO TESTIMONE: SI CHIEDE UN FOTOGRAMMA, PERCHE' UN
            #     DESKTOP FERMO NON NE MANDA.
            #
            # `[M]` 22 agosto 2026, primo giro vero su 7721: dopo il
            # `PUNTATORE` la traccia porta **zero** fotogrammi — la sessione
            # GNOME senza monitor non ha niente che si muova, e il server
            # spedisce solo quel che cambia.  ⇒ Il campo `input` di §6.2 —
            # *«l'identificatore dell'ultimo input INIETTATO»*, l'unico
            # testimone dell'iniezione che vive **sul filo** — non poteva dire
            # niente, e «non ha iniettato» e «non e' passato nessun
            # fotogramma» avevano la stessa faccia (`LEZIONI.md` §1.9).
            #
            # ⛔ E lo si chiede DOPO il puntatore, con un ritardo: il canale di
            #    input e quello di controllo sono **due stream indipendenti**
            #    (§2.5) e niente ne ordina la consegna.  Senza attesa la chiave
            #    potrebbe essere catturata PRIMA che l'input sia iniettato, e
            #    un `input = 0` significherebbe «non so», non «non iniettato».
            #
            # ⚠ E se la sessione e' gia' caduta non si manda niente: nel giro
            #   «oltre il secondo» quella e' la strada GIUSTA, e insistere su
            #   una connessione morta produrrebbe un errore del banco al posto
            #   di una misura.
            if a.chiave_dopo:
                try:
                    await asyncio.wait_for(cli.caduto.wait(),
                                           timeout=a.chiave_dopo)
                    print(f"   ·  niente RICHIEDI_CHIAVE: la sessione e' gia' "
                          f"caduta ({cli.caduta}) — ⭐ dopo un PUNTATORE oltre "
                          f"il secondo e' quel che §7.1 vuole")
                except asyncio.TimeoutError:
                    ultimo = max((f[0] for f in cli.v_fotogrammi), default=0)
                    b = inquadra(T["RICHIEDI_CHIAVE"],
                                 struct.pack("!I", ultimo))
                    cli.manda(b)
                    reg.aggiungi(CLIENT, b)
                    print(f"   → RICHIEDI_CHIAVE({ultimo}) — ⚠ non e' la scena "
                          f"di §5.2: serve a far passare UN fotogramma, cosi' "
                          f"il campo `input` di §6.2 puo' testimoniare")

        if a.vista:
            # ⚠ `VISTA` NON DEVE far cambiare la tela (§7.1).  Se dopo questa
            #   arriva un `TELA`, il filo lo dice e l'arbitro lo accusa: qui non
            #   si giudica, si registra.
            vl, va = a.vista
            b = inquadra(T["VISTA"], struct.pack("!II", vl, va))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            print(f"   → VISTA {vl}x{va}   ⚠ non deve far cambiare la tela")

        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)

        # ⛔ IL SEGNALE DI «ATTACCATO», E PERCHE' NON BASTA UNA RIGA STAMPATA.
        #
        #    Il 10 agosto 2026 il terzo giro di B3 aspettava la parola
        #    «SESSIONE» nel registro di questo programma — e Python **bufferizza
        #    lo stdout quando e' rediretto su un file**: quella riga compariva
        #    solo all'uscita del processo, cioe' **nell'istante esatto in cui il
        #    client si staccava**.
        #
        # ⚠ Il banco diceva «la prima e' attaccata» leggendo una verita' appena
        #   scaduta, e la seconda connessione arrivava sempre a posto libero.
        #   ⛔ Un controllo che sembra giusto e misura l'istante sbagliato: il
        #      rosso finiva sul server, che non c'entrava niente.
        #
        # ⭐ Un file scritto e chiuso e' un fatto; una riga stampata e' una
        #    speranza sul momento in cui qualcuno la vedra'.
        if a.segnale:
            with open(a.segnale, "w") as f:
                f.write("attaccato\n")

        # ═══ GLI APPUNTI — §7.4 ═══════════════════════════════════════════
        #
        # ⛔ E il verso `dispositivo → sessione` si annuncia PRIMA di scrivere
        #    il segnale?  NO, e la ragione e' l'ordine dei due lati del banco:
        #    il segnale dice «sono attaccato», e il lato che copia con `xclip`
        #    aspetta proprio quello.  Annunciare prima vorrebbe dire annunciare
        #    quando l'altro lato non e' ancora pronto a guardare.
        if a.appunti_copia:
            cli.appunti_annuncia(a.appunti_copia)

        if a.appunti_attendi:
            # ⛔ SI ASPETTA UN ANNUNCIO, E POI LO SI CHIEDE — §7.4: «si annuncia
            #    e si chiede, invece di spingere».  ⚠ E i due passi si contano
            #    separati: «non e' arrivato nessun annuncio» e «l'annuncio e'
            #    arrivato e il testo no» sono due difetti diversi con lo stesso
            #    sintomo (`LEZIONI.md` §1.9).
            print(f"   [app]  aspetto un annuncio dal server, fino a "
                  f"{a.appunti_attendi} s")
            fine = time.monotonic() + a.appunti_attendi
            while not cli.app_annunci and time.monotonic() < fine:
                cli.app_evento.clear()
                try:
                    await asyncio.wait_for(cli.app_evento.wait(),
                                           timeout=max(0.1, fine - time.monotonic()))
                except asyncio.TimeoutError:
                    break
            if not cli.app_annunci:
                print("   [app]  ⛔ nessun annuncio dal server entro il tempo")
            else:
                cli.appunti_chiedi()
                fine = time.monotonic() + a.appunti_attendi
                while cli.app_ricevuto is None and time.monotonic() < fine:
                    cli.app_evento.clear()
                    try:
                        await asyncio.wait_for(cli.app_evento.wait(),
                                               timeout=max(0.1, fine - time.monotonic()))
                    except asyncio.TimeoutError:
                        break
                if cli.app_ricevuto is None:
                    print("   [app]  ⛔ l'annuncio e' arrivato e il testo NO")
                else:
                    print(f"   [app]  ⭐ ricevuti {len(cli.app_ricevuto)} "
                          f"caratteri: «{cli.app_ricevuto[:60]}»")
        scrivi_appunti(a, cli)
        if a.resta:
            # ⛔ SI RESTA CON GLI OCCHI APERTI, NON DORMENDO — rilievi R8.2/R8.4.
            #
            #    Un `asyncio.sleep` non si accorge di niente: la connessione
            #    poteva cadere per il tetto d'inattivita' di QUIC, o la sessione
            #    poteva essere chiusa dal server per far posto a un altro, e
            #    questo programma usciva 0 dicendo «sono rimasto attaccato».
            #    Su quel codice d'uscita il terzo giro concludeva «nessun client
            #    vivo viene spodestato», che e' l'invariante I2 alla lettera.
            #
            # ⚠ NON si manda niente per accertarsene: il quarto giro misura
            #   l'orologio del SILENZIO, e un byte lo azzererebbe.  Si ascolta e
            #   basta — che e' precisamente il lato che riceve.
            print(f"   resto attaccato per {a.resta} s"
                  + (f", facendomi sentire ogni {a.vivo} s" if a.vivo else ""))
            try:
                if a.vivo:
                    # ⛔⛔ E QUESTA OPZIONE E' UNA TRAPPOLA — 16 agosto 2026.
                    #
                    #    `VISTA` (0x0008) e' nel protocollo, ⛔ ma QUESTO server
                    #    non la serve ancora: risponde `ERRORE_PROTOCOLLO` e
                    #    CHIUDE.  `[M]` Su venti giri di misura, tre sessioni
                    #    sono morte a 8 secondi per colpa di questa riga, e i
                    #    tempi risultavano «10,4 s» — un numero del banco, non
                    #    del prodotto.
                    #
                    # ⭐ La lezione, che l'utente ha detto meglio: *«per i test
                    #    usa il browser, non il banco — e' l'unico modo di
                    #    misurare quello che accade davvero»*.  Un client di
                    #    prova che manda quel che il vero client non manda non
                    #    misura il prodotto: misura se stesso.
                    raise SystemExit(
                        "⛔ --vivo manda VISTA (0x0008), che questo server non "
                        "serve: chiuderebbe la sessione con ERRORE_PROTOCOLLO. "
                        "Per misurare i tempi si usa il BROWSER.")
                    # ⭐ `--vivo`: si manda una `VISTA` IDENTICA ogni tanto, solo
                    #    per non farsi staccare dall'orologio del silenzio (§5.3).
                    #
                    # ⛔ SPENTO DI SUO, ed e' il punto: il comportamento
                    #    predefinito — tacere — serve a MISURARE quell'orologio, e
                    #    il commento qui sopra lo dice dal 10 agosto.  ⚠ Chi lo
                    #    accende sta misurando un'altra cosa: la scena in cui il
                    #    client c'e' e lavora, che e' quella del browser vero.
                    #
                    # ⚠ E `VISTA` con gli stessi numeri e' un no-op semantico: non
                    #   cambia niente, e' lecita a sessione attiva (§7.1), e non
                    #   chiede niente al palco — a differenza di `RICHIEDI_CHIAVE`,
                    #   che gli farebbe rifare una chiave e falserebbe la misura.
                    scaduto = asyncio.get_event_loop().time() + a.resta
                    while asyncio.get_event_loop().time() < scaduto:
                        quanto = min(a.vivo, scaduto - asyncio.get_event_loop().time())
                        try:
                            await asyncio.wait_for(cli.caduto.wait(), timeout=quanto)
                            break
                        except asyncio.TimeoutError:
                            pass
                        cli.manda(inquadra(0x0008,
                                           struct.pack("!II", a.larghezza,
                                                       a.altezza)))
                    if not cli.caduto.is_set():
                        raise asyncio.TimeoutError
                else:
                    await asyncio.wait_for(cli.caduto.wait(), timeout=a.resta)
            except asyncio.TimeoutError:
                # ⛔ La bandiera si alza PRIMA di uscire: uscendo di qui
                #    `connect()` chiude la connessione, e l'evento che ne segue
                #    dev'essere gia' riconoscibile come nostro.
                cli.chiusa_da_noi = True
                print(f"   ⭐ ancora attaccato dopo {a.resta} s: niente e' caduto")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 0
            print(f"   ⛔ NON sono rimasto attaccato: {cli.caduta}")
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
            return 4
        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
        return 0


# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON DEVE PASSARE DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ `--parola` finisce nell'`argv` del processo, cioe' in `/proc/<pid>/cmdline`,
#    che su Linux e' **leggibile da chiunque**: un `ps` lanciato da un altro
#    utente durante il giro la stampa per intero.
#
# ⭐ La strada buona esisteva gia' in casa e questa e' la sua estensione, non un
#    secondo modo: `01-b10-secondo-utente.py` prende `--parola-file`, un file
#    `0600` che il lanciatore scrive con `printf` — un **builtin** della shell,
#    quindi nemmeno la scrittura passa per un processo con la parola in `argv` —
#    e cancella con una `trap`.
#
# ⚠ E `--parola` NON e' stata tolta, e non per pigrizia: dei chiamanti non
#   ancora curati la passano ancora, e romperli **in silenzio** sarebbe peggio
#   del difetto.  ⛔ Ma il ripiego si DICHIARA (`CODER.md` §4.2): un ripiego
#   silenzioso produce due comportamenti sotto la stessa etichetta, che e' la
#   forma **E2** — e qui i due comportamenti sono «il segreto e' protetto» e
#   «il segreto e' pubblico».  ⇒ chi passa `--parola` se lo sente dire.
#
# ⚠ E l'avviso guarda `sys.argv`, non il valore: il predefinito scritto nel
#   codice non sta in nessuna riga di comando, e dirgli il contrario sarebbe un
#   allarme che si impara a ignorare.
# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ `--certifica` — L'AUTOPROVA DEL VAGLIO, SENZA RETE E SENZA MACCHINA
#
# ⛔⛔ R13 — OGNI ATTESO E' UN PREDICATO SCRITTO PRIMA.  Non una frase stampata
#      accanto ai numeri (quella resta vera «a leggerla» qualunque cosa esca),
#      ma una funzione `(numeri) -> (passa, perche)`.  `passa=None` e' il terzo
#      esito: **il banco si rifiuta di giudicare**, e non e' un verde.
#
# ⛔ E l'orologio e' FINTO, per due ragioni che valgono tutt'e due:
#    · il vaglio dipende dal tempo (il cuscino e' 250 ms), e con l'orologio
#      vero questa prova durerebbe minuti e sarebbe diversa ogni volta;
#    · un banco che dorme misura anche il carico della macchina che lo ospita.
PCM_BYTE = 960                  # `[S]` RCP.md:1299 — 480 campioni, 5 ms
PCM_PASSO_US = 5000


class OrologioFinto:
    """Il tempo lo muove il banco, non il sistema."""

    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _p(cond, perche):
    return (bool(cond), perche)


def _giro(regola, arrivi, ritardo_decodifica_s=0.0):
    """`arrivi` = [(secondi dall'inizio, istante_us)].  Torna `(vaglio, usciti)`.

    ⛔ `usciti` e' la LISTA degli `istante` consegnati, non il conto: serve a
       verificare che nessuna delle due regole **fabbrichi** un blocco che sul
       filo non c'era, e che un doppione non esca due volte.
    """
    orol = OrologioFinto()
    t0 = orol.t
    v = VaglioAudio(regola=regola, orologio=orol,
                    ritardo_decodifica_s=ritardo_decodifica_s)
    usciti = []
    for quando, ist in arrivi:
        orol.t = t0 + quando
        ok, _perche = v.arrivo(ist, 2, PCM_BYTE)
        if ok:
            usciti.append(ist)
    return v, usciti


def _conti(v):
    return {"sul_filo": v.sul_filo, "ricevuti": v.ricevuti,
            "consegnati": v.consegnati, "vecchi": v.scartati_vecchi,
            "tardivi": v.scartati_tardivi, "fuori": v.fuori_ordine,
            "doppioni": v.doppioni, "recuperati": v.recuperati,
            "mancati": v.mancati, "volte": v.mancati_volte,
            "riarmi": v.riarmi,
            "purezza": None if v.purezza is None else round(v.purezza, 4)}


def _ordinata(n):
    """n blocchi PCM da 5 ms, in ordine, senza perdite: il denominatore."""
    return [(i * 0.005, i * PCM_PASSO_US) for i in range(n)]


def _riordinata(n, k):
    """Riordino di `k` posti: gruppi di `k+1` rovesciati.

    ⭐ E' il riordino su cui la regola VECCHIA ha una purezza CALCOLABILE, non
       misurata a posteriori: dentro ogni gruppo rovesciato solo il primo
       arrivato e' il piu' nuovo, gli altri `k` sono arretrati e la regola
       vecchia li butta tutti ⇒ **purezza attesa = 1/(k+1) esatta**.
    ⛔ Questo e' l'atteso scritto prima, ed e' piu' forte di un numero magico:
       se il conto non torna, o il riordino non e' quello che credo o la regola
       vecchia non e' quella che credo.
    """
    fuori = []
    for i in range(0, n, k + 1):
        fuori += list(range(i, min(i + k + 1, n)))[::-1]
    return [(p * 0.005, j * PCM_PASSO_US) for p, j in enumerate(fuori)]


def _con_doppioni(n, ogni):
    """In ordine, ma ogni `ogni`-esimo blocco arriva DUE volte.

    ⚠ Il gemello arriva 1 ms dopo e **non consuma un posto**: se lo consumasse,
      i blocchi veri slitterebbero di 5 ms a testa e dopo 50 doppioni il ritardo
      accumulato supererebbe il cuscino ⇒ un riarmo dell'ancora, e il caso non
      misurerebbe piu' i doppioni ma la deriva che il banco stesso ha fabbricato.
    """
    a = []
    for i in range(n):
        a.append((i * 0.005, i * PCM_PASSO_US))
        if i and i % ogni == 0:
            a.append((i * 0.005 + 0.001, i * PCM_PASSO_US))
    return a


def _con_buchi(n, ogni):
    """Buchi VERI: i blocchi non arrivano affatto, e chi c'e' resta al suo posto.

    ⛔ Il blocco 0 c'e' SEMPRE, ed e' una scelta del banco: un buco **in testa**
       non e' contabile — non c'e' nessun `ultimo_istante` da cui misurare il
       salto — e mescolarlo ai buchi in mezzo darebbe un atteso sbagliato di 1.
       ⭐ Il punto cieco ha un caso suo (4-cieco).
    """
    return [(i * 0.005, i * PCM_PASSO_US)
            for i in range(n) if i == 0 or i % ogni]


def _vecchio_letterale(istanti):
    """⛔ IL CODICE DI PRIMA, TRASCRITTO ALLA LETTERA da `_audio_datagram`
       com'era fino al 22 agosto 2026.  Serve a una cosa sola: dimostrare che
       `--audio-regola vecchia` non ha cambiato NIENTE.  Non si tocca."""
    ric = vecchi = 0
    ult = None
    usciti = []
    for ist in istanti:
        if ult is not None and ist <= ult:
            vecchi += 1
            continue
        ult = ist
        ric += 1
        usciti.append(ist)
    return ric, vecchi, usciti


def certifica():
    esiti = []

    def caso(nome, passa, perche, numeri=None):
        esiti.append({"caso": nome, "passa": passa, "perche": perche,
                      "numeri": numeri})
        segno = "OK " if passa else ("-- " if passa is None else "⛔ NO")
        print(f"  {segno} {nome}")
        print(f"      atteso: {perche}")
        if numeri:
            print(f"      visto:  {numeri}")

    print("== ⭐ `01-b3-cliente.py --certifica` — il vaglio dell'audio, "
          "senza rete e senza macchina di prova")
    print(f"   PCM da {PCM_BYTE} byte = {PCM_PASSO_US} us (RCP.md:1299), "
          f"cuscino {AUDIO_CUSCINO_MS} ms, orologio finto")

    # ── 1 · in ordine: le due regole devono essere INDISTINGUIBILI ─────────
    print("\n  ── 1 · successione in ordine ──")
    av, uv = _giro("vecchia", _ordinata(840))
    an, un = _giro("nuova", _ordinata(840))
    caso("1 · in ordine ⇒ le due regole danno lo STESSO risultato",
         _conti(av) == _conti(an) and uv == un and av.purezza == 1.0,
         "ogni contatore uguale, stessa lista di usciti, purezza 1,0000 "
         "(⛔ se differiscono, la regola nuova ha un difetto sul caso facile)",
         {"vecchia": _conti(av), "nuova": _conti(an)})

    # ── 2 · riordino di 1, 2, 3 (e 7) posti ────────────────────────────────
    print("\n  ── 2 · successione riordinata ──")
    for k in (1, 2, 3, 7):
        av, uv = _giro("vecchia", _riordinata(840, k))
        an, un = _giro("nuova", _riordinata(840, k))
        atteso_v = 1.0 / (k + 1)
        arretrati = 840 - 840 // (k + 1)
        passa = (abs(av.purezza - atteso_v) <= 0.005
                 and an.purezza >= 0.95
                 and an.fuori_ordine == arretrati
                 and an.scartati_vecchi == 0 and an.doppioni == 0
                 and sorted(un) == [i * PCM_PASSO_US for i in range(840)])
        caso(f"2.{k} · riordino di {k} posti ⇒ la vecchia butta, la nuova tiene",
             passa,
             f"purezza vecchia = 1/(k+1) = {atteso_v:.4f} (±0,005) · "
             f"purezza nuova ≥ 0,95 · fuori_ordine = {arretrati} · "
             f"vecchi 0 · e l'uscita contiene TUTTI gli 840 `istante`",
             {"purezza_vecchia": round(av.purezza, 4),
              "purezza_nuova": round(an.purezza, 4),
              "vecchia": _conti(av), "nuova": _conti(an)})

    # ── 3 · doppioni: contati, e mai suonati due volte ─────────────────────
    print("\n  ── 3 · doppioni ──")
    arrivi = _con_doppioni(840, 10)
    attesi_dop = len(arrivi) - 840
    for regola in ("vecchia", "nuova"):
        v, u = _giro(regola, arrivi)
        passa = (v.doppioni == attesi_dop and len(u) == len(set(u))
                 and len(u) == 840)
        caso(f"3.{regola} · {attesi_dop} doppioni ⇒ contati, e mai due volte "
             "all'uscita",
             passa,
             f"doppioni = {attesi_dop} · nessun `istante` ripetuto all'uscita · "
             f"840 consegnati (⛔ un doppione suonato due volte raddoppia il "
             "segnale, che §6.3 non ammette)",
             _conti(v))

    # ── 4 · buchi veri: nessuna delle due deve FABBRICARE audio ────────────
    print("\n  ── 4 · buchi veri ──")
    arrivi = _con_buchi(840, 7)
    spediti = [ist for _q, ist in arrivi]
    attesi_mancati = 840 - len(spediti)
    for regola in ("vecchia", "nuova"):
        v, u = _giro(regola, arrivi)
        passa = (v.mancati == attesi_mancati and u == spediti
                 and v.consegnati == len(spediti)
                 and v.recuperati == 0)
        caso(f"4.{regola} · {attesi_mancati} blocchi MAI arrivati ⇒ `mancati` "
             "sale e non si fabbrica niente",
             passa,
             f"mancati = {attesi_mancati} · consegnati = {len(spediti)} · "
             "all'uscita SOLO gli `istante` che erano sul filo · recuperati 0",
             _conti(v))
    # ⛔⭐ IL PUNTO CIECO, E SI DICHIARA INVECE DI NASCONDERLO — trovato da
    #     questo banco il 23 agosto 2026, ed era un rosso che aveva ragione.
    #     I datagram persi PRIMA del primo che arriva non si possono contare:
    #     `mancati` misura la distanza fra due `istante`, e senza il primo non
    #     c'e' nessuna distanza.  ⚠ E' un limite della PAGINA, non della
    #     traduzione (`src/pagina.html`:6550, `a.ultimo_istante !== undefined`).
    #     ⇒ Un banco che chiedesse «mancati == tutti i buchi» su una successione
    #     che comincia con un buco darebbe rosso al prodotto per un difetto suo.
    ceco = [(i * 0.005, i * PCM_PASSO_US) for i in range(3, 200)]
    v, u = _giro("nuova", ceco)
    caso("4-cieco · ⚠ i 3 buchi IN TESTA non si contano, e non e' un difetto",
         v.mancati == 0 and v.consegnati == len(ceco),
         "mancati 0 (⛔ non c'e' nessun `istante` di prima da cui misurare il "
         "salto: e' un limite dichiarato, non un guasto) · tutti consegnati",
         _conti(v))

    # ── 5 · e il blocco arrivato DAVVERO troppo tardi ──────────────────────
    #
    # ⛔⛔ QUESTO E' IL CASO CHE DIMOSTRA CHE LA CURA NON E' «TENGO TUTTO».
    #     Se la regola nuova tenesse anche questo, non sarebbe una cura: sarebbe
    #     la rimozione di un controllo.
    #
    # ⚠ E i casi sono DUE, perche' nella pagina i contatori sono due e cadono
    #   in punti diversi del percorso:
    #     5a · il posto e' passato GIA' SUL FILO ⇒ `scartati_vecchi`
    #          (`src/pagina.html`:5999-6001 sta in `suona()`; il gemello sul filo
    #          e' :6514, e li' il contatore e' `scartati_vecchi`);
    #     5b · il posto e' passato MENTRE LO DECODIFICAVAMO ⇒ `scartati_tardivi`.
    #   ⛔ Chiamarli tutt'e due «tardivi» sarebbe comodo e sbagliato: il primo
    #     e' §6.3 alla lettera, il secondo e' la rete di sicurezza dopo il
    #     decodificatore, e se un giorno si confondessero nessuno saprebbe piu'
    #     se a buttare e' il filo o la macchina.
    # ⭐ E IL CONTO DEL MARGINE, scritto qui perche' senza si sbaglia il caso.
    #    L'ancora si aggancia DENTRO `_consegna`, cioe' **dopo** la decodifica:
    #    `base = ora + ritardo + cuscino - t`.  ⇒ Un blocco che arriva `Δ` in
    #    ritardo sul proprio posto e' scartato
    #      · SUL FILO   se  Δ > cuscino + ritardo   (il vaglio guarda `ora`);
    #      · ALLA CONSEGNA se Δ > cuscino           (il vaglio guarda `ora + ritardo`).
    #    ⇒ La finestra dei `scartati_tardivi` e' esattamente
    #      `cuscino < Δ ≤ cuscino + ritardo`, e senza ritardo di decodifica e'
    #      VUOTA — che e' T3 detto in numeri.
    print("\n  ── 5 · il blocco davvero troppo tardi ──")
    n, i_tardo = 200, 195
    base = _ordinata(n)
    suo_posto = i_tardo * 0.005          # quando sarebbe dovuto arrivare
    ultimo_arrivo = base[-1][0]
    cusc = AUDIO_CUSCINO_MS / 1000.0
    # 5a · Δ = 300 ms > cuscino 250 e ritardo 0 ⇒ e' passato GIA' SUL FILO.
    tardo = [(suo_posto + 0.300, i_tardo * PCM_PASSO_US)]
    assert tardo[0][0] > ultimo_arrivo    # dev'essere l'ultimo ad arrivare
    av, uv = _giro("vecchia", base + tardo)
    an, un = _giro("nuova", base + tardo)
    caso(f"5a · Δ = 300 ms > cuscino {AUDIO_CUSCINO_MS} ⇒ il posto e' passato "
         "SUL FILO, e la nuova lo SCARTA",
         (an.scartati_vecchi == 1 and an.fuori_ordine == 0
          and an.consegnati == n and un == [i * PCM_PASSO_US for i in range(n)]
          and av.scartati_vecchi == 1 and av.consegnati == n),
         "nuova: vecchi 1 · fuori 0 · consegnati 200, e il tardivo NON e' "
         "nell'uscita — vecchia: vecchi 1 · consegnati 200",
         {"vecchia": _conti(av), "nuova": _conti(an)})
    # 5b · Δ = 280 ms: sta nella finestra `250 < Δ ≤ 250+50` ⇒ passa il filo e
    #      perde il posto durante i 50 ms di decodifica dichiarati.
    dec = 0.050
    delta = cusc + dec / 2                # 275 ms: in mezzo alla finestra
    quasi = [(suo_posto + delta, i_tardo * PCM_PASSO_US)]
    assert quasi[0][0] > ultimo_arrivo
    an2, un2 = _giro("nuova", base + quasi, ritardo_decodifica_s=dec)
    av2, uv2 = _giro("vecchia", base + quasi, ritardo_decodifica_s=dec)
    caso(f"5b · Δ = {delta * 1000:.0f} ms, cioe' dentro la finestra "
         f"({AUDIO_CUSCINO_MS} < Δ ≤ {AUDIO_CUSCINO_MS + dec * 1000:.0f}) ⇒ "
         "`scartati_tardivi`",
         (an2.scartati_tardivi == 1 and an2.fuori_ordine == 1
          and an2.consegnati == n and an2.riarmi == 0
          and av2.consegnati == n and av2.scartati_vecchi == 1),
         "nuova: tardivi 1 · fuori 1 (il filo l'ha lasciato passare) · "
         "consegnati 200 · riarmi 0 (⛔ l'ancora NON si tocca per un "
         "sorpassato: un riarmo costerebbe 250 ms di ritardo per un blocco da "
         "5) — vecchia: vecchi 1 · consegnati 200",
         {"vecchia": _conti(av2), "nuova": _conti(an2)})
    # 5c · e la controprova: la cura NON e' «tengo tutto».
    an3, un3 = _giro("nuova", _riordinata(840, 3))
    caso("5c · ⭐ la controprova: sul riordino la nuova tiene 840/840, sul "
         "tardivo ne butta 1 ⇒ non e' «tengo tutto»",
         an3.consegnati == 840 and an.consegnati == n and an.scartati_vecchi == 1,
         "la stessa regola, due esiti opposti sui due casi (⛔ se buttasse zero "
         "in tutt'e due sarebbe la rimozione di un controllo)",
         {"riordino": an3.consegnati, "tardivo_scartati": an.scartati_vecchi})

    # ── 6 · la regressione: il predefinito NON e' cambiato ─────────────────
    print("\n  ── 6 · la regola vecchia contro il codice di prima ──")
    banchi_prova = {
        "in ordine": _ordinata(840),
        "riordinata di 3": _riordinata(840, 3),
        "con doppioni": _con_doppioni(840, 10),
        "con buchi": _con_buchi(840, 7),
        "mista": _riordinata(400, 2) + _con_doppioni(200, 5) + _con_buchi(200, 9),
    }
    guasti = []
    for nome, arrivi in banchi_prova.items():
        v, u = _giro("vecchia", arrivi)
        ric, vecchi, usciti = _vecchio_letterale([i for _q, i in arrivi])
        if (v.ricevuti, v.scartati_vecchi, u) != (ric, vecchi, usciti):
            guasti.append(f"{nome}: nuovo ({v.ricevuti}, {v.scartati_vecchi}, "
                          f"{len(u)} usciti) contro vecchio ({ric}, {vecchi}, "
                          f"{len(usciti)} usciti)")
    caso("6 · ⛔⛔ `--audio-regola vecchia` == il codice del 22 agosto, alla "
         "lettera, su 5 successioni",
         not guasti,
         "ricevuti, vecchi e la LISTA degli usciti identici in tutt'e cinque "
         "(⛔ se no, ogni numero gia' misurato dai banchi smette di essere "
         "confrontabile)",
         {"guasti": guasti or "nessuno",
          "predefinito": REGOLA_AUDIO,
          "predefinito_del_vaglio": VaglioAudio().regola})
    caso("6-bis · il PREDEFINITO e' ancora `vecchia` in tutt'e due i posti",
         REGOLA_AUDIO == "vecchia" and VaglioAudio().regola == "vecchia",
         "la variabile di modulo e il costruttore dicono tutt'e due «vecchia»",
         {"modulo": REGOLA_AUDIO, "costruttore": VaglioAudio().regola})

    rossi = [e for e in esiti if e["passa"] is False]
    muti = [e for e in esiti if e["passa"] is None]
    print(f"\n== {len(esiti)} casi · {len(rossi)} rossi · {len(muti)} «non "
          f"giudico»")
    for e in rossi:
        print(f"   ⛔ {e['caso']}")
        print(f"      atteso {e['perche']}")
        print(f"      visto  {e['numeri']}")
    if not rossi:
        print("== ⭐ IL VAGLIO FA QUEL CHE LA PAGINA FA, E IL PREDEFINITO NON "
              "E' CAMBIATO")
    return 1 if rossi else 0


def parola_dagli_argomenti(a):
    """La parola d'ordine: da `--parola-file` se c'e', da `--parola` altrimenti.

    ⛔ E i tre modi di fallire si distinguono: «non si legge», «e' leggibile da
    altri» e «e' vuoto» hanno tre cure diverse, e un file vuoto NON e' una
    parola vuota — e' «il lanciatore non l'ha scritta» (`LEZIONI.md` §1.9).
    """
    percorso = getattr(a, "parola_file", "") or ""
    if percorso:
        try:
            modo = os.stat(percorso).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ il file della parola «{percorso}» non si legge: {e}")
            sys.exit(2)
        if modo:
            print(f"   ⚠ «{percorso}» e' leggibile da altri (bit {modo:o}): il "
                  f"segreto non e' protetto")
        try:
            with open(percorso, encoding="utf-8") as f:
                parola = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ la parola non si legge da «{percorso}»: {e}")
            sys.exit(2)
        if not parola:
            print(f"   ⛔ il file della parola «{percorso}» e' VUOTO.  Non e'")
            print("      «la parola e' vuota»: e' «il lanciatore non l'ha scritta».")
            sys.exit(2)
        return parola
    if any(x == "--parola" or x.startswith("--parola=") for x in sys.argv[1:]):
        print("   ⚠ D12: la parola d'ordine e' arrivata da `--parola`, cioe' dalla")
        print("     RIGA DI COMANDO: sta in `/proc/<pid>/cmdline` e la vede chiunque")
        print("     faccia `ps` su questa macchina.  Il giro prosegue — il chiamante")
        print("     non e' stato curato — ma non e' un giro riservato.")
        print("     ⭐ La cura: `--parola-file <file 0600>`, come in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="la stretta di mano di RCP, dal lato client")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="prova")
    # ⛔ D12: la strada che NON passa da `ps`.  Vince su `--parola` se ci sono
    #    tutt'e due — un file scritto apposta e' sempre piu' recente di un
    #    predefinito.
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (⭐ D12: cosi' "
                        "non finisce in `ps`)")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--registra")
    # ⭐ LA STRADA DELLA TELA — sottofase 6.6.
    #
    # ⛔ `--adatta LxH` oppure `LxH@S`: manda `ADATTA_TELA` e aspetta il `TELA`
    #    che §7.1 impone.  Ripetibile, e con `@S` si aspettano S secondi PRIMA
    #    di mandarla — ⭐ cosi' la stessa opzione copre le due scene della fase
    #    6: la richiesta **all'attacco** (`DECISIONI.md` §5.0-sexies, il client
    #    chiede la tela della propria finestra da se') e il **ridimensionamento
    #    a caldo** a sessione avviata.
    p.add_argument("--adatta", action="append", default=[], metavar="LxH[@S]",
                   help="ADATTA_TELA (0x000B), ripetibile; @S = secondi di "
                        "attesa prima di mandarla")
    p.add_argument("--vista", metavar="LxH",
                   help="VISTA (0x0008) dopo l'attacco — ⚠ §7.1: NON deve far "
                        "cambiare la tela")
    # ⭐⛔ IL SECONDO DI GRAZIA DI §7.1 — 22 agosto 2026.
    #
    # ⛔ Il ritardo si passa in SECONDI e non ha predefinito: la regola vive su
    #    un confine, e un valore scelto dal programma invece che dal banco
    #    sarebbe un confine scelto da chi non dichiara perche'.
    p.add_argument("--puntatore-vecchia", type=float, default=None,
                   metavar="RITARDO",
                   help="§7.1: manda un PUNTATORE all'ULTIMO PIXEL della tela "
                        "PRECEDENTE, RITARDO secondi dopo il TELA(ADATTATA).  "
                        "⚠ Il tempo e' quello del CLIENT: l'intervallo del "
                        "SERVER e' piu' LUNGO, quindi si sta lontani dal "
                        "secondo dai due lati")
    p.add_argument("--chiave-dopo", type=float, default=0, metavar="SECONDI",
                   help="dopo il PUNTATORE, aspetta SECONDI e manda una "
                        "RICHIEDI_CHIAVE: serve a far passare un fotogramma "
                        "su un desktop fermo, perche' il campo `input` di §6.2 "
                        "possa dire se l'input e' stato INIETTATO.  ⚠ Non si "
                        "manda se la sessione e' gia' caduta")
    # ⚠ Il tetto NON e' una regola di RCP: §7.1 impone la risposta, non un
    #   tempo.  Serve a non riprodurre il sintomo che si vuole misurare.
    p.add_argument("--attesa-tela", type=float, default=5.0,
                   help="quanto si aspetta un TELA prima di dichiarare il "
                        "silenzio (⚠ non e' una regola di RCP.md)")
    # ═══ L'AUDIO — fase 7 ═════════════════════════════════════════════════
    p.add_argument("--video-scrivi", default="",
                   help="dove scrivere i fotogrammi presi DAL FILO, cosi' come "
                        "sono — per darli a un decodificatore terzo e separare "
                        "il nostro flusso da quello del browser")
    p.add_argument("--video-codec", default="h264",
                   help="che cosa dichiarare in `video.codec` (§4.3).  "
                        "⭐ Il predefinito e' **quel che dichiara Firefox**: "
                        "`pagina.html` manda solo i codec che hanno DIPINTO la "
                        "sonda, e li' HEVC non dipinge.  ⛔ `hevc` rifa' il "
                        "vecchio metro (fino al 23 agosto 2026), e i due "
                        "insiemi di numeri NON si confrontano: `fasi/09` §14.1")
    p.add_argument("--video-profondita", default="8,10",
                   help="che cosa dichiarare in `video.profondita` (§4.3)")
    p.add_argument("--audio-codec", default="opus,pcm",
                   help="che cosa dichiarare in `audio.codec` (§4.3).  "
                        "⛔ `pcm` da solo e' legittimo ed e' il controllo "
                        "positivo di Opus, non un aggiramento")
    # ⛔⛔ IL PREDEFINITO E' `vecchia`, E NON SI CAMBIA SENZA L'UTENTE.
    #     `01-b3-cliente.py` lo usano decine di banchi gia' misurati: con la
    #     regola nuova per predefinito, ogni numero gia' scritto smetterebbe di
    #     essere confrontabile — e il confronto «prima / dopo la cura» sarebbe
    #     proprio quello che si perde.
    p.add_argument("--audio-regola", default="vecchia",
                   choices=list(VaglioAudio.REGOLE),
                   help="`vecchia` = §6.3 come la leggeva il codice fino al 22 "
                        "agosto 2026 (arretrato ⇒ si butta); `nuova` = la cura "
                        "del riordino di `src/pagina.html` (arretrato ⇒ si "
                        "butta SOLO se il suo posto e' gia' passato).  "
                        "⛔ Il predefinito e' `vecchia` apposta")
    p.add_argument("--audio-passo-us", type=int, default=0,
                   help="quanto dura un blocco, in us.  0 = lo ricavo dal "
                        "carico del PCM (⚠ per Opus non so decodificare: senza "
                        "questo il conto dei `mancati` resta SPENTO)")
    p.add_argument("--audio-decodifica-ms", type=float, default=0.0,
                   help="il tempo che si finge di spendere a decodificare.  "
                        "⚠ A 0 `scartati_tardivi` non e' una misura: e' uno "
                        "zero cieco (T3)")
    p.add_argument("--certifica", action="store_true",
                   help="⭐ l'autoprova del vaglio dell'audio: NON tocca la "
                        "rete e non serve la macchina di prova")
    p.add_argument("--audio-scrivi", default="",
                   help="dove scrivere i blocchi d'audio ricevuti, in JSONL — "
                        "il giudice di `07-b42` legge questo")
    # ═══ GLI APPUNTI — fase 7, §7.4 ═══════════════════════════════════════
    p.add_argument("--appunti-copia", default="",
                   help="annuncia questo testo al server (verso dispositivo → "
                        "sessione) e poi resta a servirlo quando lo chiede")
    p.add_argument("--appunti-attendi", type=float, default=0,
                   help="aspetta fino a N secondi un annuncio dal server, lo "
                        "chiede, e scrive il testo che arriva (verso sessione → "
                        "dispositivo)")
    p.add_argument("--appunti-scrivi", default="",
                   help="dove scrivere l'esito degli appunti, in JSON — il "
                        "banco `07-b45` legge questo")
    p.add_argument("--resta", type=float, default=0)
    # ⭐ Ogni quanti secondi farsi sentire (0 = mai, ed e' il predefinito:
    #    tacere e' quel che serve a misurare l'orologio del silenzio).
    p.add_argument("--vivo", type=float, default=0)
    p.add_argument("--segnale",
                   help="file da scrivere quando la sessione e' aperta")
    a = p.parse_args()

    # ⭐ `--certifica` esce QUI: non tocca la rete, non chiede la parola
    #    d'ordine e non vuole la macchina di prova.
    if a.certifica:
        sys.exit(certifica())

    if AIOQUIC:
        print(f"   ⛔ senza `aioquic` questo cliente non puo' attaccarsi a "
              f"niente: {AIOQUIC}")
        print("      ⭐ gira DENTRO il contenitore (`enter.sh`), oppure chiedi "
              "`--certifica`, che non tocca la rete.")
        sys.exit(2)

    # ⛔ Le tre scelte dell'audio diventano variabili di modulo perche'
    #    `create_protocol=Cliente` non passa argomenti al costruttore.
    #    ⚠ Questo blocco gira a livello di modulo: l'assegnamento e' gia'
    #    globale, e `Cliente.__init__` legge queste tre righe.
    REGOLA_AUDIO = a.audio_regola
    PASSO_AUDIO_US = a.audio_passo_us
    DECODIFICA_AUDIO_S = a.audio_decodifica_ms / 1000.0
    if REGOLA_AUDIO != "vecchia":
        # ⛔ E SI DICE, forte: un giro con la regola nuova NON e' confrontabile
        #    con i numeri dei banchi di prima, e chi legge il registro dopo deve
        #    saperlo senza dover ritrovare la riga di comando.
        print(f"   ⚠ `--audio-regola {REGOLA_AUDIO}`: questo giro NON usa la "
              "regola con cui sono stati misurati i banchi di prima")

    a.parola = parola_dagli_argomenti(a)

    def misura(testo, dove):
        """`LxH` o `LxH@S`.  ⛔ Un argomento storto si dice, non si indovina.

        ⚠ Un banco che accettasse `1264-800` interpretandolo come puo' darebbe
          una misura diversa da quella che chi lancia crede di aver chiesto, e
          il numero finirebbe in un rapporto: la forma d'errore **E2**.
        """
        quando = 0.0
        if "@" in testo:
            testo, _, s = testo.partition("@")
            try:
                quando = float(s)
            except ValueError:
                print(f"   ⛔ {dove}: «{s}» non e' un numero di secondi")
                sys.exit(2)
        parti = testo.lower().split("x")
        if len(parti) != 2 or not all(x.isdigit() for x in parti):
            print(f"   ⛔ {dove}: «{testo}» non ha la forma LxH (es. 1264x800)")
            sys.exit(2)
        return int(parti[0]), int(parti[1]), quando

    a.adatta = [misura(x, "--adatta") for x in a.adatta]
    a.vista = misura(a.vista, "--vista")[:2] if a.vista else None
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
