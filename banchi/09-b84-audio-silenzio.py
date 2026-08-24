#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b84-audio-silenzio — ⛔⭐⭐ CHE COSA COSTA L'AUDIO QUANDO NON C'E' AUDIO.

═══ IL FATTO DA CUI NASCE, E LA PRIMA COSA CHE HA REFUTATO ═════════════════

Il mandato diceva: *«su rete cattiva un terzo dell'audio non raggiunge mai il
filo»*, `[M]` `09-b77` su `casa-cattiva`, **1 823 blocchi rifiutati su ~5 000**;
e *«una sessione ferma costa 2 463 kbit/s di audio PCM»*, `[M]` `09-b81`.

⛔⛔ **TUTT'E DUE QUEI NUMERI SONO IN PCM, E IL PCM NON E' QUEL CHE IL PRODOTTO
     NEGOZIA.**  `[R]` I banchi lo IMPONGONO al cliente di prova:
     `09-b68:191`, `09-b70:1890`, `09-b71:144`, `09-b77:978`, `09-b81:2294`
     passano tutti `--audio-codec pcm`.  ⭐ E il registro della sessione VERA
     dell'utente (porta 7920, `/media/REMOTIX/tmp/09c/registro.log`) dice
     l'opposto, quattro volte su quattro:

         negoziato video.codec=hevc video.profondita=8 audio.codec=opus
         ⭐ FASE 7: canale audio ACCESO … — codec 1 (Opus)

     ⇒ Il 36 % e i 2 463 kbit/s sono proprieta' di **una configurazione di
     banco**, non del prodotto.  `[R]` `pagina.html:4727` chiede a
     `AudioDecoder.isConfigSupported` e dichiara `opus,pcm` quando il motore
     risponde di si'; il PCM resta la base di §4.3 per chi non ce l'ha.

═══ ⭐⭐⭐ E QUEL CHE C'E' DAVVERO E' PIU' GRAVE, NON MENO ══════════════════

`[M]` 24 agosto 2026, questo banco, porta 7972, 25 s per braccio, binari
`6c52adfc…` (spenta) e `02558a5c…` (accesa).  Sessione con **Opus** negoziato e
desktop **fermo** (`suono.c`: `PICCO 0 su 32767`, cioe' silenzio DIGITALE):

  braccio | sul filo      | pacchetti/s | datagram/s | byte/pacchetto | carico
  --------|---------------|-------------|------------|----------------|--------
  SPENTA  | 557,6 kbit/s  |  48,4       |  48,0      | 1 441          | 1,18 kbit/s
  ACCESA  |   5,5 kbit/s  |   0,5       |   0,0      |  —             | 0,00 kbit/s
                                                              ⇒ **102,1 volte**

⇒ **Il 99,8 % di quel traffico e' riempimento.**  Ogni blocco di silenzio si
porta via un pacchetto INTERO, perche' `webtransport.c:1613` scrive il datagram
con `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING`.  ⛔ E quel pacchetto lo paga la
**stessa finestra di congestione del video**: `[M]` sulla sessione vera la
finestra vale 2 888 - 5 704 byte, cioe' **due o tre pacchetti**, e l'audio ne
chiede cinquanta al secondo per non dire niente.

⭐ E la cura NON tocca il suono, misurato appaiato sulla scena col tono a 440 Hz
   (PCM, giudice di `07-b42`): copertura **1,0000 → 0,9996**, purezza del tono
   **1,000 → 1,000**, blocchi taciuti **1 su 5 001** — e quell'uno e' il primo
   blocco della sessione, che precede i primi campioni del tono.

⚠ IL PREZZO, e si scrive: sulla scena col tono i `mancati` del cliente passano
  da 0 a 2.  Un buco VOLUTO lascia lo stesso salto di `istante` di uno perso, e
  quel contatore non distingue le due cose.

⭐ LA CURA E' IN `src/audio.c`, E NASCE SPENTA (I6): un blocco in cui TUTTI i
   campioni sono esattamente zero non diventa un datagram.  §6.3 mette
   l'`istante` dentro ogni blocco e chi riceve li rimette al loro posto
   assoluto ⇒ **un blocco non spedito e' un buco, e un buco e' silenzio** —
   che e' quel che quel blocco conteneva.  Non e' un'approssimazione.

⛔ E QUEL CHE **NON** SI E' SCRITTO, perche' non e' nostro: `src/webtransport.c`
   e' di un altro.  La descrizione della sua meta' di cura sta in §PADDING, in
   fondo a questo file, con funzione, riga, cambio e ragione.

═══ ⛔ L'INTERRUTTORE E' DI COMPILAZIONE, E VA DETTO ════════════════════════

Il codificatore vive nel **figlio**, che e' un `execve` con l'ambiente
**composto da zero** (`figlio.c:1145`): una `REMOTIX_...` non lo raggiunge.
L'unico canale che attraversa l'`exec` e' la coda di `argv`, e quella si scrive
in `main.c` e in `figlio.c` — due file che non sono di questo mandato.

⇒ I due bracci sono **due binari dallo STESSO albero e dagli STESSI sorgenti**,
  con **un solo `-D` di differenza** (`AUDIO_SILENZIO_PREDEFINITO=1`), e i loro
  `md5` si stampano a ogni giro.  ⛔ E il banco CONTROLLA che siano diversi:
  due copie dello stesso file darebbero «nessuna differenza», che e' la stessa
  faccia di «la cura non serve» e la conclusione opposta.

═══ ⭐ LE GRANDEZZE, E QUELLA CHE CONTA NON E' «QUANTI NE BUTTO» ═══════════

  1. **`kbit_s`** — i byte che ngtcp2 dichiara spediti, dalla riga `rete-quic`
     del prodotto.  ⛔ Non e' una stima mia: e' il contatore del trasporto.
  2. **`pkt_s`** e **`dgram_s`** — pacchetti e datagram al secondo.  ⭐ Il loro
     rapporto e' la prova del riempimento: 50 datagram in 51 pacchetti vuol
     dire «un pacchetto per blocco».
  3. **`copertura`** — quanta parte della linea del tempo ha davvero ricevuto
     campioni, contata da `09-b77.scaletta()` sui blocchi PCM.  ⭐ E' la
     grandezza su cui la cura puo' fare danno: se tacesse del suono, scenderebbe.
  4. **`purezza_tono`** — il giudice di `07-b42` via `09-b77.purezza_tono()`.

═══ ⛔ E SU RETE CATTIVA IL CODEC NON BASTA — la previsione che NON ha retto ══

`[M]` 24 agosto 2026, `casa-cattiva` (40±20 ms, 2 % di perdita), scena col tono,
25 s per codec, **stesso `netem` per tutt'e due**, cura SPENTA:

  codec | sul filo      | spediti | rifiutati | ‰ rifiutati | COPERTURA del filo
  ------|---------------|---------|-----------|-------------|-------------------
  PCM   | 1 024,5 kbit/s|  3 135  | **1 880** | **375‰**    | **0,6088**
  Opus  |   366,3 kbit/s|  1 127  |   **126** | **101‰**    | **0,8803**

⭐ La grandezza che conta sale: **copertura 0,61 → 0,88**, cioe' +27 punti di
   audio che arriva davvero all'orecchio, sulla stessa rete.
⛔ Ma il predicato chiedeva «Opus sotto 20‰» e ha dato **ROSSO**: Opus divide il
   rifiuto per 3,7, **non lo toglie**.  ⇒ Il codec e' la cura del COSTO, non del
   rifiuto: anche con un decimo dei byte la finestra si chiude lo stesso.
   Il confine resta dov'e' e il rosso resta scritto.

Uso (dal portatile):
    python3 banchi/09-b84-audio-silenzio.py --certifica    # ⛔ prima di tutto
    python3 banchi/09-b84-audio-silenzio.py terreno
    python3 banchi/09-b84-audio-silenzio.py costruisci     # i due binari
    python3 banchi/09-b84-audio-silenzio.py muto  [--secondi 25]
    python3 banchi/09-b84-audio-silenzio.py tono  [--secondi 25]
    python3 banchi/09-b84-audio-silenzio.py costo [--secondi 25]
    python3 banchi/09-b84-audio-silenzio.py stretta [--profilo casa-cattiva]
    python3 banchi/09-b84-audio-silenzio.py tutto
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ISOLAMENTO, e si scrive PRIMA di importare qualunque cosa: i moduli che
#    stanno sotto leggono l'ambiente al momento dell'import, non alla chiamata
#    (`LEZIONI.md` §1.26).
# ═══════════════════════════════════════════════════════════════════════════
PORTA = int(os.environ.get("PORTA", "7972"))
UTENTE = os.environ.get("UTENTE", "provanr9")
UID_B = int(os.environ.get("UID_B", "1072"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09nr9-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09nr9")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09nr9-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09nr9")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "nr9-audio-2026")
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
IND = os.environ.get("IND", "192.168.0.2")
FUORI = os.environ.get("FUORI", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad", "b84"))

# ⛔ Le porte che NON sono mie.  Si contano, non si toccano.
VIETATE = ("7900", "7910", "7920", "7971")
VIETATA_IFACE = "enp7s0"

for k, v in (("PORTA", str(PORTA)), ("UTENTE", UTENTE), ("UID_B", str(UID_B)),
             ("ALBERO", ALB), ("LAV", LAV), ("DENTRO_ALB", DENTRO_ALB),
             ("DENTRO_LAV", DENTRO_LAV), ("FUORI", FUORI), ("IND", IND),
             ("MACCHINA", MACCHINA), ("PAROLA_UTENTE", PAROLA_UTENTE)):
    os.environ[k] = v
os.makedirs(FUORI, exist_ok=True)


def _carica(nome, file_):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# ⛔ `09-b77` NON si tocca: si IMPORTA.  Ha il tono, il giudice dei campioni,
#    i profili del `netem` e 52 casi di `--certifica` verdi — riscriverne una
#    riga vorrebbe dire avere due giudici che possono divergere.
B77 = _carica("b77", "09-b77-audio-riordino.py")
RETE = B77.RETE            # root(), guasta(), tono_accendi/spegni, guardiano_*
LUCCHETTO = B77.LUCCHETTO

CHI = "09-b84"
BIN_SPENTA = "%s/src/remotix-spenta" % ALB
BIN_ACCESA = "%s/src/remotix-accesa" % ALB


def log(t):  print("\n\033[1m== %s\033[0m" % t)
def ok(t):   print("    \033[1;32mOK\033[0m  %s" % t)
def ko(t):   print("    \033[1;31mNO\033[0m  %s" % t)
def dub(t):  print("    \033[1;33m??\033[0m  %s" % t)
def inf(t):  print("    --  %s" % t)


# ═══════════════════════════════════════════════════════════════════════════
# I PREDICATI — SCRITTI PRIMA, E SONO FUNZIONI, NON PROSA
#
# ⛔ R13: un atteso in prosa resta vero «a leggerlo» qualunque numero esca.  Qui
#    ogni atteso e' `(s, a) -> (passa, perche)` — `s` sono i numeri del braccio
#    con la cura SPENTA, `a` quelli con la cura ACCESA — e `passa=None` vuol
#    dire «mi rifiuto di giudicare», che e' un esito SUO e non un verde.
# ═══════════════════════════════════════════════════════════════════════════
def _p(cond, perche):
    return (bool(cond), perche)


def _muto(perche):
    return (None, perche)


def _c(n, chiave):
    """Il valore, o `None` se non si e' letto.  ⛔ `None` non e' zero."""
    if not isinstance(n, dict):
        return None
    return n.get(chiave)


def a_il_riempimento_c_e(min_kbit=400.0, max_carico_kbit=5.0):
    """⭐ IL FATTO, misurato col braccio SPENTO — che e' il prodotto di oggi.

    ⛔ E' anche il CONTROLLO POSITIVO del banco: se qui non esce il riempimento,
       lo stimolo non stimola (il desktop suonava, o la sessione non aveva
       audio) e il braccio acceso non dimostrerebbe niente."""
    def f(s, a):
        k = _c(s, "kbit_s")
        c = _c(s, "carico_kbit_s")
        if k is None or c is None:
            return _muto("non ho letto kbit_s (%s) o carico_kbit_s (%s)" % (k, c))
        return _p(k >= min_kbit and c <= max_carico_kbit,
                  "cura SPENTA: %.1f kbit/s sul filo per %.2f kbit/s di carico "
                  "(atteso >= %.0f e <= %.1f)" % (k, c, min_kbit, max_carico_kbit))
    return f


def a_la_cura_taglia(fattore=8.0):
    """⭐ LA PREVISIONE CHE PUO' CADERE: la banda scende di almeno `fattore`."""
    def f(s, a):
        ks, ka = _c(s, "kbit_s"), _c(a, "kbit_s")
        if ks is None or ka is None:
            return _muto("kbit_s: spenta=%s accesa=%s" % (ks, ka))
        if ka <= 0:
            return _p(True, "cura ACCESA: 0 kbit/s (spenta %.1f)" % ks)
        return _p(ks / ka >= fattore,
                  "%.1f → %.1f kbit/s = %.1f× (atteso >= %.0f×)"
                  % (ks, ka, ks / ka, fattore))
    return f


def a_i_datagram_spariscono(tetto_s=2.0):
    """⭐ E si vede sull'ALTRO capo: il cliente non riceve piu' blocchi."""
    def f(s, a):
        ds, da = _c(s, "dgram_s"), _c(a, "dgram_s")
        if ds is None or da is None:
            return _muto("dgram_s: spenta=%s accesa=%s" % (ds, da))
        return _p(ds >= 40.0 and da <= tetto_s,
                  "datagram al secondo: %.1f → %.1f (atteso >= 40 e <= %.1f)"
                  % (ds, da, tetto_s))
    return f


def a_la_cura_ha_parlato():
    """⛔ «L'ho acceso» non e' «l'ha fatto»: il registro del PRODOTTO deve dire
       che la cura e' accesa E che ha taciuto dei blocchi.  ⚠ Senza, un binario
       sbagliato darebbe due giri identici col nome di due."""
    def f(s, a):
        if _c(a, "cura_dichiarata") != "accesa":
            return _p(False, "il registro del braccio ACCESO dichiara «%s»"
                             % _c(a, "cura_dichiarata"))
        if _c(s, "cura_dichiarata") != "spenta":
            return _p(False, "il registro del braccio SPENTO dichiara «%s»"
                             % _c(s, "cura_dichiarata"))
        t = _c(a, "taciuti")
        if t is None:
            return _muto("il registro non porta la riga del silenzio digitale")
        return _p(t > 0, "blocchi taciuti dal braccio acceso: %s (atteso > 0)" % t)
    return f


def a_il_suono_non_si_tocca(tolleranza=0.02):
    """⛔⛔ IL CONTROLLO CHE VALE PIU' DI TUTTI: sulla scena col TONO la cura non
        deve cambiare NIENTE — il tono non e' mai zero digitale.

    ⚠ Se questo dice rosso, la cura mangia suono e non esce dalla porta."""
    def f(s, a):
        cs, ca = _c(s, "copertura"), _c(a, "copertura")
        ps, pa = _c(s, "purezza_tono"), _c(a, "purezza_tono")
        if cs is None or ca is None:
            return _muto("copertura: spenta=%s accesa=%s" % (cs, ca))
        if abs(cs - ca) > tolleranza:
            return _p(False, "copertura %.4f → %.4f: la cura ha tolto suono"
                             % (cs, ca))
        if ps is None or pa is None:
            return _p(True, "copertura %.4f ≈ %.4f (il tono non si e' giudicato)"
                            % (cs, ca))
        return _p(abs(ps - pa) <= tolleranza * 5,
                  "copertura %.4f ≈ %.4f · tono %.3f ≈ %.3f" % (cs, ca, ps, pa))
    return f


def a_col_tono_tace_solo_il_primo(tetto=2):
    """⛔ LA CONTROPROVA DIRETTA: col tono acceso la cura non deve mordere.

    ⛔⭐ E IL CONFINE NON E' ZERO, ED E' UNA MISURA CHE HA CORRETTO IL BANCO —
        `[M]` 24 agosto 2026.  Il predicato chiedeva `taciuti == 0` e ha dato
        ROSSO con `taciuti = 1`.  Il registro dice quale:

          09:10:25.701  ⭐ PCM aperto …
          09:10:25.731  ⭐ silenzio DIGITALE: 1 blocchi non spediti su 1 entrati

        ⇒ E' il **primo blocco della sessione**, trenta millisecondi dopo che il
        codificatore si e' aperto e prima che i campioni del tono abbiano
        attraversato PipeWire.  ⚠ Non e' la cura che mangia suono: e' che
        all'inizio suono non ce n'e' ancora.
    ⛔ Il confine resta STRETTO (2 su ~5 000) apposta: se la cura cominciasse a
       tacere davvero, questo predicato lo vedrebbe subito."""
    def f(s, a):
        t = _c(a, "taciuti")
        e = _c(a, "entrati_cod")
        if t is None:
            return _muto("il registro non porta il conto della cura alla chiusura")
        return _p(t <= tetto,
                  "blocchi taciuti col tono acceso: %s su %s entrati "
                  "(atteso <= %d: solo quelli che precedono i primi campioni)"
                  % (t, e, tetto))
    return f


def a_il_prezzo_si_dichiara():
    """⚠ NON E' UN VERDE NE' UN ROSSO: e' il prezzo, e si scrive.

    Un buco voluto ha, dal lato di chi riceve, la stessa faccia di una perdita:
    i `mancati` del cliente crescono.  ⛔ Dichiararlo qui e' quel che impedisce
    che domani qualcuno legga quel numero come un guasto della rete."""
    def f(s, a):
        return _muto("PREZZO: `mancati` %s → %s.  Un blocco taciuto lascia lo "
                     "stesso salto di `istante` di uno perso: il numero non "
                     "distingue le due cose, e da oggi va letto sapendolo"
                     % (_c(s, "mancati"), _c(a, "mancati")))
    return f


def a_opus_costa_meno_del_pcm(fattore=10.0):
    """⭐ LA REFUTAZIONE, in un numero: il carico dell'audio in PCM contro Opus.

    ⛔ Si confronta il CARICO (i byte di §6.3), non i byte sul filo: sul filo il
       riempimento li pareggia, ed e' esattamente il difetto che questo banco
       ha trovato — confondere i due direbbe «PCM e Opus costano uguale»."""
    def f(p, o):
        cp, co = _c(p, "carico_kbit_s"), _c(o, "carico_kbit_s")
        if cp is None or co is None or co <= 0:
            return _muto("carico_kbit_s: pcm=%s opus=%s" % (cp, co))
        return _p(cp / co >= fattore,
                  "carico dell'audio: PCM %.1f kbit/s contro Opus %.2f = %.0f× "
                  "(atteso >= %.0f×)" % (cp, co, cp / co, fattore))
    return f


def a_il_pcm_si_fa_rifiutare(minimo=100):
    """⛔ IL CONTROLLO POSITIVO DELLA RETE STRETTA: col PCM il rifiuto c'e'.

    ⚠ Se il PCM non si fa rifiutare, il profilo non morde e il confronto con
      Opus non dimostra niente — sarebbe due volte lo stesso giro."""
    def f(p, o):
        r = _c(p, "rifiutati_server")
        if r is None:
            return _muto("il registro non porta i rifiutati del server")
        return _p(r >= minimo,
                  "PCM: %s blocchi rifiutati da ngtcp2 (atteso >= %d)" % (r, minimo))
    return f


def a_opus_regge_dove_il_pcm_cede(tetto_permille=20):
    """⭐ LA PREVISIONE: sullo STESSO `netem`, Opus si fa rifiutare in una
       frazione trascurabile di quel che si fa rifiutare il PCM.

    ⛔⛔ E LA PREVISIONE **NON HA RETTO** — `[M]` 24 agosto 2026, `casa-cattiva`,
        scena col tono, 25 s per codec, stesso `netem` per tutt'e due:

          PCM   3 135 spediti · 1 880 rifiutati = **375‰**
          Opus  1 127 spediti ·   126 rifiutati = **101‰**

        ⇒ Opus divide il rifiuto per **3,7**, non lo toglie.  Il confine di 20‰
        era mio e la misura l'ha smentito: **si lascia dov'e'** e si scrive il
        rosso, invece di spostarlo fino a farlo passare (`LEZIONI.md` §2.3).
        ⚠ Il fatto che resta: anche con un decimo dei byte la finestra si chiude
        lo stesso, quindi il codec **non e' la cura del rifiuto** — e' la cura
        del costo.  La cura del rifiuto, se c'e', sta nel trasporto."""
    def f(p, o):
        rp, sp = _c(p, "rifiutati_server"), _c(p, "spediti_server")
        ro, so = _c(o, "rifiutati_server"), _c(o, "spediti_server")
        if None in (rp, sp, ro, so) or (sp + rp) <= 0 or (so + ro) <= 0:
            return _muto("conti del server: pcm=%s/%s opus=%s/%s" % (rp, sp, ro, so))
        fp = 1000.0 * rp / (sp + rp)
        fo = 1000.0 * ro / (so + ro)
        return _p(fo <= tetto_permille,
                  "rifiutati: PCM %.0f‰ contro Opus %.0f‰ (atteso Opus <= %d‰)"
                  % (fp, fo, tetto_permille))
    return f


def a_la_copertura_risale(guadagno=0.10):
    """⭐⭐ LA GRANDEZZA CHE CONTA — quanto dell'audio PRODOTTO arriva davvero.

    ⛔⭐ E NON E' LA `copertura` DEI CAMPIONI, e la ragione e' che quella si
        calcola solo sul PCM (`09-b77.scaletta()` salta i blocchi che non sono
        codec 2, e questo banco non ha un decodificatore Opus).  Confrontare la
        copertura dei campioni del PCM con **niente** darebbe «non giudicato»
        proprio sulla domanda del mandato.

    ⭐ `copertura_filo` = **blocchi che la rete ha consegnato al cliente** diviso
       **blocchi che il server ha prodotto** (spediti + rifiutati + buttati).
       ⚠ Ci sta dentro anche la perdita della rete, e si dichiara: i due bracci
       stanno sotto lo STESSO `netem`, quindi la differenza fra loro resta di
       chi si fa rifiutare — ma il numero da solo non separa le due cause.
       ⛔ Per quello c'e' `a_opus_regge_dove_il_pcm_cede`, che guarda i soli
       rifiuti; questo guarda quel che arriva all'orecchio."""
    def f(p, o):
        cp, co = _c(p, "copertura_filo"), _c(o, "copertura_filo")
        if cp is None or co is None:
            return _muto("copertura_filo: pcm=%s opus=%s" % (cp, co))
        return _p(co - cp >= guadagno,
                  "copertura del filo: PCM %.4f → Opus %.4f (+%.4f, atteso >= +%.2f)"
                  % (cp, co, co - cp, guadagno))
    return f


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def root(comando, tetto=300):
    return RETE.root(comando, tetto)


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


R_RETE = re.compile(
    r"rete-quic \S+ da_ms=(\d+).*?spediti=(\d+) spediti_d=(\d+) "
    r"byte_spediti=(\d+).*?dgram_ok=(\d+)")


def rete_del_giro(riga0):
    """⭐ I BYTE SUL FILO LI DICE IL PRODOTTO, non una stima mia.

    La riga `rete-quic` porta `byte_spediti` (cumulativo per connessione) e
    `da_ms` (l'intervallo VERO fra una riga e l'altra).  ⇒ La banda e' la
    differenza fra la prima e l'ultima riga della finestra, divisa per la somma
    dei `da_ms` — non per il tempo che credevo di aver aspettato.

    ⛔ E si legge solo da `riga0` in poi, cosi' e' di QUESTO giro.
    ⚠ Meno di tre righe: si torna `None`, non zero (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'rete-quic '" % (riga0 + 1, LAV))
    righe = []
    for r in out.split("\n"):
        m = R_RETE.search(r)
        if m:
            righe.append(tuple(int(x) for x in m.groups()))
    if len(righe) < 3:
        return {"esito": "NIENTE DA LEGGERE — %d righe «rete-quic» in questo "
                         "giro (ne servono 3)" % len(righe), "righe": len(righe)}
    # ⛔ Si scarta la PRIMA riga: il suo `da_ms` copre anche la partenza della
    #    connessione, e la partenza non e' il regime che voglio misurare.
    ms = sum(r[0] for r in righe[1:])
    if ms <= 0:
        return {"esito": "somma dei da_ms nulla", "righe": len(righe)}
    return {
        "righe": len(righe),
        "secondi": round(ms / 1000.0, 2),
        "pkt_s": round((righe[-1][1] - righe[0][1]) * 1000.0 / ms, 2),
        "kbit_s": round((righe[-1][3] - righe[0][3]) * 8.0 / ms, 2),
        "dgram_s": round((righe[-1][4] - righe[0][4]) * 1000.0 / ms, 2),
        "byte_per_pkt": (None if righe[-1][1] == righe[0][1] else
                         round((righe[-1][3] - righe[0][3]) /
                               float(righe[-1][1] - righe[0][1]), 1)),
    }


def conti_del_server(riga0):
    """⛔ «La rete l'ha perso» e «il server non l'ha mai spedito» danno lo stesso
       numero dal lato del cliente.  Qui si legge il conto del SERVER."""
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio di .*conto "
                      "finale' | tail -1" % (riga0 + 1, LAV))
    r = out.strip()
    if not r:
        return {"esito": "NIENTE DA LEGGERE — nessun «conto finale»"}
    m = re.search(r"(\d+) blocchi spediti, (\d+) buttati.*?(\d+) rifiutati.*?"
                  r"(\d+) RIMANDATI", r)
    if not m:
        return {"esito": "riga trovata ma illeggibile", "riga": r[:160]}
    c = re.search(r"codec (\d+)\s*$", r)
    return {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
            "rifiutati": int(m.group(3)), "rimandati": int(m.group(4)),
            "codec": (int(c.group(1)) if c else None)}


def cura_del_registro(riga0):
    """⛔ L'INTERRUTTORE SI LEGGE DAL REGISTRO DEL PRODOTTO, non da quel che
       credo di aver acceso.  ⚠ `audio.c` scrive la riga anche quando la cura
       e' SPENTA, apposta: «la cura non c'e'» e «la cura c'e' e non ha fatto
       niente» devono avere due facce diverse (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'cura del silenzio digitale' | tail -1" % (riga0 + 1, LAV))
    dett = out.strip()
    stato = None
    if "ACCESA" in dett:
        stato = "accesa"
    elif "spenta" in dett:
        stato = "spenta"
    # ⛔ IL CONTO ESATTO E' QUELLO DELLA CHIUSURA, non quello della riga di
    #    dentro: quella esce alla prima e poi una ogni mille, quindi dice
    #    «almeno N».  ⚠ Leggere quella e chiamarla `taciuti` sarebbe un numero
    #    che sembra misurato — `[M]` 24 agosto 2026: 1 249 blocchi taciuti
    #    stampavano «1000».
    rc, out2, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                       "'conto della cura del silenzio' | tail -1" % (riga0 + 1, LAV))
    m = re.search(r"(\d+) blocchi taciuti su (\d+) entrati, (\d+) usciti", out2)
    return {"cura_dichiarata": stato,
            "taciuti": (int(m.group(1)) if m else None),
            "entrati_cod": (int(m.group(2)) if m else None),
            "usciti_cod": (int(m.group(3)) if m else None),
            "riga": dett[:120]}


DA_LEGGERE = {
    "sul_filo":   r"sul filo\s+(\d+)",
    "ricevuti":   r"·\s*ricevuti\s+(\d+)\s*·",
    "consegnati": r"consegnati\s+(\d+)",
    "mancati":    r"mancati\s+(\d+)",
    "carico":     r"·\s*(\d+)\s+byte di carico",
    "codec_cli":  r"byte di carico\s*·\s*codec\s+(\d+)",
}


def _num(testo, nome):
    """⛔ L'ULTIMA occorrenza — la riga dei conti arriva dopo tutte le altre — e
       un `None` vuol dire «non l'ho letto», non «zero»."""
    trovato = None
    for m in re.finditer(DA_LEGGERE[nome], testo):
        trovato = int(m.group(1))
    return trovato


# ═══════════════════════════════════════════════════════════════════════════
# I DUE BINARI, E IL SERVER CHE SI RIACCENDE SU UNO O SULL'ALTRO
# ═══════════════════════════════════════════════════════════════════════════
def md5(percorso):
    rc, out, _ = root("md5sum %s 2>/dev/null | cut -d' ' -f1" % percorso)
    s = out.strip()
    return s if len(s) == 32 else None


def costruisci_due():
    """⛔ I DUE BINARI: stesso albero, stessi sorgenti, un solo `-D`."""
    log("I DUE BINARI — un solo `-D` di differenza")
    copione = os.path.join(FUORI, "costruisci-due.sh")
    with open(copione, "w") as f:
        f.write(CORPO_COSTRUISCI)
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", copione,
                    "%s:%s/costruisci-due.sh" % (MACCHINA, ALB)], timeout=120)
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root 'ALB=%s bash "
                        "%s/costruisci-due.sh'" % (DENTRO_ALB, DENTRO_ALB), 1200)
    for r in (out + err).splitlines():
        if ("md5" in r or "INC letta" in r or "⛔" in r or
                r.strip().startswith(("5", "a", "0", "OK", "b", "c", "d", "e", "f"))
                and "/srv/src" in r):
            print("   %s" % r)
    ms, ma = md5(BIN_SPENTA), md5(BIN_ACCESA)
    if not ms or not ma:
        ko("⛔ uno dei due binari non c'e' (spenta=%s accesa=%s)" % (ms, ma))
        return False
    if ms == ma:
        ko("⛔⛔ I DUE BINARI SONO IDENTICI (%s): il `-D` non ha morso, e due "
           "giri con lo stesso binario direbbero «nessuna differenza»" % ms)
        return False
    ok("spenta md5 %s" % ms)
    ok("accesa md5 %s" % ma)
    return True


CORPO_COSTRUISCI = r'''#!/bin/bash
# ⛔ Le `INC`/`LIB` non si ricopiano: si LEGGONO da quel che `costruisci.sh`
#    stampa, o i due bracci divergerebbero per una riga che nessuno ha guardato.
set -uo pipefail
ALB=${ALB:-/srv/src/09nr9-src}
cd "$ALB/src" || exit 2
USCITA=$(PREFISSO=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 \
         NGHTTP3=/srv/src/b2/nghttp3 bash "$ALB/src/costruisci.sh" 2>&1)
[ -x "$ALB/src/remotix" ] || { echo "⛔ il braccio SPENTO non si e' costruito"; exit 2; }
cp -f "$ALB/src/remotix" "$ALB/src/remotix-spenta"
INC=$(echo "$USCITA" | sed -n 's/^ *-- *intestazioni: //p' | head -1)
LIB=$(echo "$USCITA" | sed -n 's/^ *-- *librerie: *//p' | head -1)
[ -n "$INC" ] || { echo "⛔ INC non letta da costruisci.sh"; exit 2; }
echo "INC letta: $INC"
rm -f "$ALB/src"/*.o "$ALB/src/remotix"
make -C "$ALB/src" GEMELLO="$ALB/banchi/rcp" \
  CFLAGS="-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter $INC -DAUDIO_SILENZIO_PREDEFINITO=1" \
  LDFLAGS="$LIB" tutto 2>&1 | tail -2
[ -x "$ALB/src/remotix" ] || { echo "⛔ il braccio ACCESO non si e' costruito"; exit 2; }
cp -f "$ALB/src/remotix" "$ALB/src/remotix-accesa"
cp -f "$ALB/src/remotix-spenta" "$ALB/src/remotix"
md5sum "$ALB/src/remotix-spenta" "$ALB/src/remotix-accesa" "$ALB/src/audio.c"
'''


def accendi(braccio):
    """⛔ Il binario si mette al posto di `remotix` e si riaccende l'unita'.
       ⚠ E si VERIFICA quale ci sia: copiare e credere e' la forma E1."""
    sorgente = BIN_ACCESA if braccio == "accesa" else BIN_SPENTA
    voluto = md5(sorgente)
    root("cp -f %s %s/src/remotix" % (sorgente, ALB))
    messo = md5("%s/src/remotix" % ALB)
    if messo != voluto:
        ko("⛔ il binario messo (%s) non e' quello voluto (%s)" % (messo, voluto))
        return None
    subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "accendi"],
                   capture_output=True, timeout=300,
                   env=dict(os.environ, UNITA=UNITA))
    for _ in range(50):
        rc2, o, _ = root("ss -uln 2>/dev/null | grep -c ':%d '" % PORTA)
        if o.strip() not in ("", "0"):
            break
        time.sleep(0.2)
    return voluto


def giro(braccio, scena, codec, secondi):
    """Un giro: braccio (spenta|accesa) · scena (muto|tono) · codec (pcm|opus)."""
    nome = "%s-%s-%s" % (braccio, scena, codec)
    j_fuori = os.path.join(FUORI, nome + ".jsonl")
    binario = accendi(braccio)
    if binario is None:
        return {"esito": "il binario del braccio «%s» non si e' messo" % braccio}

    if scena == "tono":
        # ⛔⭐ E L'ORDINE NON E' UN DETTAGLIO — `[M]` 24 agosto 2026, primo giro
        #     col tono: il sink «remotix» lo crea il FIGLIO, e il figlio nasce
        #     quando entra un cliente.  Su un server appena riacceso
        #     `pw-play --target remotix` non si lega a NIENTE, e il banco
        #     avrebbe misurato silenzio chiamandolo rete.  ⇒ Prima una sessione
        #     corta che fa nascere il palco (I4: gli sopravvive), poi il tono.
        if not RETE.innesca_sessione():
            return {"esito": "⛔ la sessione non si apre: non c'e' un sink su "
                             "cui suonare"}
        if not RETE.tono_accendi():
            return {"esito": "⛔ il tono NON suona nella sessione: un giudice "
                             "che legge silenzio accuserebbe la rete"}
    else:
        RETE.tono_spegni()

    riga0 = righe_registro()
    t0 = time.time()
    # ⛔⭐ E `opus` DA SOLO NON SI PUO' DICHIARARE — `[M]` 24 agosto 2026, primo
    #    giro: `congedo motivo=0x09 dettaglio=il client non dichiara pcm in
    #    audio.codec`.  §4.3 impone `pcm` a ENTRAMBI ed e' `rcp.c:2229` a farlo
    #    rispettare.  ⇒ Per avere Opus si dichiara **`opus,pcm`**, e il server
    #    sceglie il primo dell'ordine di preferenza del client.
    #    ⚠ Chiedere «solo opus» non da' un giro senza PCM: da' un giro senza
    #      NIENTE, e i suoi zeri avrebbero avuto la faccia di una misura.
    chiesto = "opus,pcm" if codec == "opus" else "pcm"
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec %s "
              "--audio-scrivi %s/b84-%s.jsonl --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, chiesto,
                 DENTRO_LAV, nome, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 240)
    uscita = out + err
    open(os.path.join(FUORI, nome + ".txt"), "w").write(uscita)
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/b84-%s.jsonl\" > %s"
                   % (MACCHINA, RETE.PAROLA_SUDO, LAV, nome, j_fuori),
                   shell=True)
    if scena == "tono":
        RETE.tono_spegni()

    rq = rete_del_giro(riga0)
    sv = conti_del_server(riga0)
    cu = cura_del_registro(riga0)
    n = {"braccio": braccio, "scena": scena, "codec": codec, "binario": binario,
         "secondi": round(time.time() - t0, 1),
         "sul_filo": _num(uscita, "sul_filo"),
         "ricevuti": _num(uscita, "ricevuti"),
         "consegnati": _num(uscita, "consegnati"),
         "mancati": _num(uscita, "mancati"),
         "carico": _num(uscita, "carico"),
         "codec_cli": _num(uscita, "codec_cli"),
         "spediti_server": sv.get("spediti"),
         "rifiutati_server": sv.get("rifiutati"),
         "buttati_server": sv.get("buttati"),
         "rimandati_server": sv.get("rimandati"),
         "codec_server": sv.get("codec"),
         "server": sv, "rete": rq}
    n.update({k: rq.get(k) for k in ("pkt_s", "kbit_s", "dgram_s", "byte_per_pkt")})
    n.update({k: cu.get(k) for k in ("cura_dichiarata", "taciuti",
                                     "entrati_cod", "usciti_cod")})
    # ⭐ Il carico VERO dell'audio: i byte di §6.3 che il cliente ha contato,
    #   sul tempo del giro.  ⛔ Non e' `kbit_s`: quello e' il filo, riempimento
    #   compreso, ed e' proprio la differenza fra i due che questo banco misura.
    if n["carico"] is not None and rq.get("secondi"):
        n["carico_kbit_s"] = round(n["carico"] * 8.0 / 1000.0 / rq["secondi"], 3)
    else:
        n["carico_kbit_s"] = None
    # ⭐⭐ LA COPERTURA DEL FILO — quanto del prodotto arriva, e vale per
    #    TUTT'E DUE i codec.  ⛔ `prodotti` e' il conto del SERVER (spediti +
    #    rifiutati + buttati): «non l'ho mai messo sul filo» e «la rete l'ha
    #    perso» finiscono tutt'e due qui dentro, ed e' voluto — la domanda e'
    #    quanto ne arriva, non di chi e' la colpa.
    if None not in (n["spediti_server"], n["rifiutati_server"],
                    n["buttati_server"], n["sul_filo"]):
        prodotti = (n["spediti_server"] + n["rifiutati_server"] +
                    n["buttati_server"])
        n["prodotti_server"] = prodotti
        n["copertura_filo"] = (round(n["sul_filo"] / float(prodotti), 4)
                               if prodotti > 0 else None)
    else:
        n["prodotti_server"] = None
        n["copertura_filo"] = None
    # ⭐ La seconda gamba, dai CAMPIONI: solo il PCM si giudica cosi'
    #   (`09-b77.scaletta()` salta i blocchi che non sono codec 2).
    sc = B77.scaletta(j_fuori) if codec == "pcm" else {
        "esito": "NON GIUDICATO — i campioni di Opus non si leggono senza "
                 "decodificarli, e questo banco non ha un decodificatore"}
    n["scaletta"] = sc
    n["copertura"] = sc.get("copertura")
    n["purezza_tono"] = sc.get("purezza_tono")
    n["blocchi"] = sc.get("blocchi")
    # ⛔⛔ E IL CODEC DEV'ESSERE QUELLO CHE HO CHIESTO, DETTO DAL SERVER.
    #     «L'ho dichiarato» non e' «l'ha scelto» (`LEZIONI.md` E1): §4.3 fa
    #     scegliere il SERVER dentro l'intersezione, e un giro «opus» finito in
    #     PCM sarebbe due volte lo stesso giro col nome di due.
    atteso = 1 if codec == "opus" else 2
    if n["codec_server"] is not None and n["codec_server"] != atteso:
        n["esito"] = ("⛔⛔ HO CHIESTO «%s» (codec %d) E IL SERVER HA NEGOZIATO "
                      "il codec %d" % (codec, atteso, n["codec_server"]))
    return n


def riga(n):
    def q(x, f="%s"):
        return "-" if x is None else (f % x)
    return ("%-7s %-5s %-5s | filo %s kbit/s · %s pkt/s · %s dgram/s · %s B/pkt "
            "| carico %s kbit/s (%s byte) | srv %s spediti %s rifiutati | "
            "cura %s taciuti %s | COP.FILO %s (cop %s tono %s) | manc %s"
            % (n.get("braccio"), n.get("scena"), n.get("codec"),
               q(n.get("kbit_s"), "%.1f"), q(n.get("pkt_s"), "%.1f"),
               q(n.get("dgram_s"), "%.1f"), q(n.get("byte_per_pkt"), "%.0f"),
               q(n.get("carico_kbit_s"), "%.2f"), q(n.get("carico")),
               q(n.get("spediti_server")), q(n.get("rifiutati_server")),
               q(n.get("cura_dichiarata")), q(n.get("taciuti")),
               q(n.get("copertura_filo"), "%.4f"),
               q(n.get("copertura"), "%.4f"), q(n.get("purezza_tono"), "%.3f"),
               q(n.get("mancati"))))


def giudica(titolo, atteso, s, a):
    log(titolo)
    inf(riga(s)); inf(riga(a))
    verdi = rossi = muti = 0
    for f in atteso:
        passa, perche = f(s, a)
        if passa is True:
            ok(perche); verdi += 1
        elif passa is False:
            ko(perche); rossi += 1
        else:
            dub(perche); muti += 1
    return verdi, rossi, muti


# ═══════════════════════════════════════════════════════════════════════════
# IL TERRENO
# ═══════════════════════════════════════════════════════════════════════════
def terreno_controlla():
    log("IL TERRENO — porta %d · utente %s (uid %d) · albero %s"
        % (PORTA, UTENTE, UID_B, ALB))
    guai = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % UTENTE)
    if "si" not in out:
        guai.append("l'utente «%s» non esiste" % UTENTE)
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("manca %s/parola (0600): D12 vieta la parola in argv" % LAV)
    for b, nome in ((BIN_SPENTA, "spenta"), (BIN_ACCESA, "accesa")):
        if not md5(b):
            guai.append("manca il binario del braccio %s (%s): «costruisci»"
                        % (nome, b))
    conto = []
    for p in VIETATE:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    inf("porte VIETATE (si contano, non si toccano): %s" % " ".join(conto))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % VIETATA_IFACE)
    inf("%s — NON si tocca: %s" % (VIETATA_IFACE, out.strip().split("\n")[0]))
    for g in guai:
        ko(g)
    if not guai:
        ok("il terreno c'e', ed e' mio")
    return not guai


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ LA CERTIFICAZIONE — il banco deve saper dare ROSSO
#
# ⛔⛔ Un banco che non ha mai dato rosso non e' uno strumento: e' una speranza
#      con dei numeri accanto.  Qui ogni predicato viene chiamato su numeri
#      FABBRICATI, e si pretende l'esito che deve dare.
# ═══════════════════════════════════════════════════════════════════════════
def _n(**kw):
    return dict(kw)


def certifica():
    esiti = []

    def caso(titolo, f, s, a, atteso):
        passa, perche = f(s, a)
        bene = (passa is atteso) if atteso is None else (passa == atteso)
        esiti.append(bene)
        (ok if bene else ko)("%s → %s  [%s]"
                             % (titolo, {True: "VERDE", False: "ROSSO",
                                         None: "NON GIUDICATO"}[passa], perche))

    log("1 · `a_il_riempimento_c_e` — il controllo positivo del fatto")
    f = a_il_riempimento_c_e()
    caso("589 kbit/s per 1,2 kbit/s di carico", f,
         _n(kbit_s=589.0, carico_kbit_s=1.2), {}, True)
    caso("⛔ 40 kbit/s: il riempimento NON c'e'", f,
         _n(kbit_s=40.0, carico_kbit_s=1.2), {}, False)
    caso("⛔ 589 kbit/s ma 300 di carico: sta suonando qualcosa", f,
         _n(kbit_s=589.0, carico_kbit_s=300.0), {}, False)
    caso("⚠ kbit_s non letto", f, _n(kbit_s=None, carico_kbit_s=1.2), {}, None)

    log("2 · `a_la_cura_taglia` — e non si accontenta di un miglioramento")
    f = a_la_cura_taglia(8.0)
    caso("589 → 12 kbit/s (49×)", f, _n(kbit_s=589.0), _n(kbit_s=12.0), True)
    caso("⛔ 589 → 200 kbit/s (2,9×): meglio, ma non e' la cura", f,
         _n(kbit_s=589.0), _n(kbit_s=200.0), False)
    caso("589 → 0 kbit/s", f, _n(kbit_s=589.0), _n(kbit_s=0.0), True)
    caso("⚠ manca un capo", f, _n(kbit_s=589.0), _n(kbit_s=None), None)

    log("3 · `a_i_datagram_spariscono` — l'altro capo del filo")
    f = a_i_datagram_spariscono()
    caso("50 → 0 datagram/s", f, _n(dgram_s=50.0), _n(dgram_s=0.0), True)
    caso("⛔ 50 → 30: la cura non ha morso", f,
         _n(dgram_s=50.0), _n(dgram_s=30.0), False)
    caso("⛔ 5 → 0: non c'era audio da prima", f,
         _n(dgram_s=5.0), _n(dgram_s=0.0), False)

    log("4 · `a_la_cura_ha_parlato` — «l'ho acceso» non e' «l'ha fatto»")
    f = a_la_cura_ha_parlato()
    caso("spenta/accesa, 1249 taciuti", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="accesa", taciuti=1249), True)
    caso("⛔ tutt'e due i bracci sullo stesso binario", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="spenta", taciuti=0), False)
    caso("⛔ accesa ma zero taciuti", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="accesa", taciuti=0), False)
    caso("⚠ il registro non ha la riga", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="accesa", taciuti=None), None)

    log("5 · ⛔⛔ `a_il_suono_non_si_tocca` — il predicato che protegge l'utente")
    f = a_il_suono_non_si_tocca()
    caso("copertura 0,998 → 0,997, tono 1,00 → 1,00", f,
         _n(copertura=0.998, purezza_tono=1.0),
         _n(copertura=0.997, purezza_tono=1.0), True)
    caso("⛔ copertura 0,998 → 0,700: la cura mangia suono", f,
         _n(copertura=0.998, purezza_tono=1.0),
         _n(copertura=0.700, purezza_tono=0.9), False)
    caso("⛔ copertura uguale ma il tono crolla", f,
         _n(copertura=0.998, purezza_tono=1.0),
         _n(copertura=0.998, purezza_tono=0.5), False)

    log("6 · `a_col_tono_tace_solo_il_primo` — la scena e' quella che credo?")
    f = a_col_tono_tace_solo_il_primo()
    caso("col tono, zero taciuti", f, {}, _n(taciuti=0), True)
    caso("⛔ col tono, 300 taciuti: la scena ha dei buchi di zero digitale", f,
         {}, _n(taciuti=300), False)

    log("7 · `a_opus_costa_meno_del_pcm` — la refutazione, in un numero")
    f = a_opus_costa_meno_del_pcm(10.0)
    caso("PCM 1555 contro Opus 1,2 kbit/s", f,
         _n(carico_kbit_s=1555.0), _n(carico_kbit_s=1.2), True)
    caso("⛔ PCM 1555 contro Opus 500: non e' un fattore dieci", f,
         _n(carico_kbit_s=1555.0), _n(carico_kbit_s=500.0), False)

    log("8 · `a_il_pcm_si_fa_rifiutare` — il controllo positivo della rete")
    f = a_il_pcm_si_fa_rifiutare(100)
    caso("1823 rifiutati", f, _n(rifiutati_server=1823), {}, True)
    caso("⛔ 4 rifiutati: il profilo non morde", f, _n(rifiutati_server=4), {}, False)
    caso("⚠ conto non letto", f, _n(rifiutati_server=None), {}, None)

    log("9 · `a_opus_regge_dove_il_pcm_cede`")
    f = a_opus_regge_dove_il_pcm_cede(20)
    caso("PCM 366‰ contro Opus 2‰", f,
         _n(rifiutati_server=1823, spediti_server=3160),
         _n(rifiutati_server=2, spediti_server=1240), True)
    caso("⛔ Opus 120‰: non regge", f,
         _n(rifiutati_server=1823, spediti_server=3160),
         _n(rifiutati_server=150, spediti_server=1100), False)

    log("10 · ⭐⭐ `a_la_copertura_risale` — la grandezza che conta")
    f = a_la_copertura_risale(0.10)
    caso("0,63 → 0,99", f, _n(copertura_filo=0.6264),
         _n(copertura_filo=0.99), True)
    caso("⛔ 0,63 → 0,66: dentro il rumore", f,
         _n(copertura_filo=0.6264), _n(copertura_filo=0.66), False)
    caso("⚠ una delle due non si e' giudicata", f,
         _n(copertura_filo=0.6264), _n(copertura_filo=None), None)

    log("11 · ⚠ `a_il_prezzo_si_dichiara` — non e' un verde e non e' un rosso")
    f = a_il_prezzo_si_dichiara()
    caso("il prezzo si scrive sempre", f, _n(mancati=0), _n(mancati=1200), None)

    log("ESITO DELLA CERTIFICAZIONE")
    if all(esiti):
        ok("%d casi su %d: i predicati sanno dare verde, rosso e «non giudico»"
           % (sum(esiti), len(esiti)))
        return True
    ko("%d casi su %d NON hanno dato l'esito atteso: il banco non e' uno "
       "strumento finche' questa riga e' rossa" % (len(esiti) - sum(esiti), len(esiti)))
    return False


# ═══════════════════════════════════════════════════════════════════════════
# LE MISURE
# ═══════════════════════════════════════════════════════════════════════════
def misura_muto(secondi):
    log("SCENA «MUTO» — desktop fermo, Opus negoziato, cura spenta contro accesa")
    inf("⛔ e' la scena NORMALE del prodotto: `[M]` sulla sessione vera "
        "dell'utente il carico dei datagram e' 3 byte, cioe' silenzio digitale")
    s = giro("spenta", "muto", "opus", secondi)
    a = giro("accesa", "muto", "opus", secondi)
    v, r, m = giudica("IL VERDETTO — scena muta",
                      [a_il_riempimento_c_e(), a_la_cura_taglia(8.0),
                       a_i_datagram_spariscono(), a_la_cura_ha_parlato(),
                       a_il_prezzo_si_dichiara()], s, a)
    return {"scena": "muto", "spenta": s, "accesa": a,
            "verdi": v, "rossi": r, "muti": m}


def misura_tono(secondi):
    log("SCENA «TONO» — 440 Hz nel sink, PCM (per il giudice dei campioni)")
    inf("⛔ e' il CONTROLLO che protegge l'utente: col tono acceso la cura non "
        "deve tacere niente, e la copertura non deve muoversi")
    s = giro("spenta", "tono", "pcm", secondi)
    a = giro("accesa", "tono", "pcm", secondi)
    v, r, m = giudica("IL VERDETTO — scena col tono",
                      [a_il_suono_non_si_tocca(), a_col_tono_tace_solo_il_primo()],
                      s, a)
    return {"scena": "tono", "spenta": s, "accesa": a,
            "verdi": v, "rossi": r, "muti": m}


def misura_costo(secondi):
    log("IL COSTO DEI DUE CODEC — PCM contro Opus, stessa scena, cura SPENTA")
    inf("⭐ e' la refutazione: i 2 463 kbit/s di `09-b81` e il 36 % di `09-b77` "
        "sono numeri del PCM, e il prodotto negozia Opus")
    p = giro("spenta", "muto", "pcm", secondi)
    o = giro("spenta", "muto", "opus", secondi)
    v, r, m = giudica("IL VERDETTO — quanto costa l'audio",
                      [a_opus_costa_meno_del_pcm(10.0)], p, o)
    return {"scena": "costo", "pcm": p, "opus": o, "verdi": v, "rossi": r, "muti": m}


def misura_stretta(nome_profilo, secondi):
    """⛔ QUI SI GUASTA LA RETE: lucchetto, `lo` soltanto, filtri sulla sola
       porta mia, guardiano staccato, e tutto mollato in un `finally`."""
    prof = None
    for p in B77.PROFILI:
        if p[0] == nome_profilo:
            prof = p
    if prof is None:
        ko("il profilo «%s» non e' in 09-b77" % nome_profilo)
        return None
    log("LA RETE STRETTA — profilo «%s», PCM contro Opus, cura SPENTA" % nome_profilo)
    inf("⛔ tutt'e due i giri sotto lo STESSO `netem`, messo una volta e "
        "lasciato in piedi: a cambiare c'e' solo il codec")
    LUCCHETTO.prendi(CHI, secondi=900, attesa=3600)
    try:
        RETE.guardiano_arma(900)
        RETE.guasta(prof[1])
        # ⛔ SCENA COL TONO, non muta: la domanda e' che cosa succede
        #    all'audio VERO quando la finestra si stringe.  Su una scena muta
        #    il PCM manderebbe 192 blocchi di zeri al secondo e il confronto
        #    misurerebbe il costo del silenzio, che e' un'altra cosa.
        p = giro("spenta", "tono", "pcm", secondi)
        o = giro("spenta", "tono", "opus", secondi)
    finally:
        try:
            RETE.rimetti()
        except Exception as e:
            ko("⛔ il `netem` non si e' tolto: %s" % e)
        try:
            RETE.guardiano_disarma()
        except Exception:
            pass
        LUCCHETTO.molla(CHI)
    v, r, m = giudica("IL VERDETTO — chi regge quando la finestra si stringe",
                      [a_il_pcm_si_fa_rifiutare(100),
                       a_opus_regge_dove_il_pcm_cede(20),
                       a_la_copertura_risale(0.10)], p, o)
    return {"scena": "stretta-%s" % nome_profilo, "pcm": p, "opus": o,
            "verdi": v, "rossi": r, "muti": m}


def principale():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("passo", nargs="?", default="stato",
                    choices=("stato", "terreno", "costruisci", "muto", "tono",
                             "costo", "stretta", "tutto"))
    ap.add_argument("--secondi", type=int, default=25)
    ap.add_argument("--profilo", default="casa-cattiva")
    ap.add_argument("--certifica", action="store_true")
    a = ap.parse_args()

    if a.certifica:
        sys.exit(0 if certifica() else 1)

    if a.passo == "stato":
        terreno_controlla()
        return
    if a.passo == "terreno":
        sys.exit(0 if terreno_controlla() else 2)
    if a.passo == "costruisci":
        sys.exit(0 if costruisci_due() else 2)

    if not terreno_controlla():
        ko("⛔ NON misuro su un terreno che non e' il mio")
        sys.exit(2)

    fuori = []
    if a.passo in ("muto", "tutto"):
        fuori.append(misura_muto(a.secondi))
    if a.passo in ("tono", "tutto"):
        fuori.append(misura_tono(a.secondi))
    if a.passo in ("costo", "tutto"):
        fuori.append(misura_costo(a.secondi))
    if a.passo in ("stretta", "tutto"):
        r = misura_stretta(a.profilo, a.secondi)
        if r:
            fuori.append(r)

    percorso = os.path.join(FUORI, "esiti.json")
    with open(percorso, "w") as f:
        json.dump(fuori, f, indent=1, ensure_ascii=False)
    log("IL VERDETTO DI TUTTO IL BANCO")
    V = sum(x["verdi"] for x in fuori)
    R = sum(x["rossi"] for x in fuori)
    M = sum(x["muti"] for x in fuori)
    inf("i numeri per esteso: %s" % percorso)
    (ok if R == 0 else ko)("%d verdi · %d rossi · %d non giudicati" % (V, R, M))
    sys.exit(0 if R == 0 else 1)


# ═══════════════════════════════════════════════════════════════════════════
# §PADDING — ⛔ LA META' DI CURA CHE NON E' MIA, DESCRITTA E NON SCRITTA
#
# `src/webtransport.c` e' di un altro agente.  Quel che segue e' la descrizione
# precisa, perche' la misura e' qui e la cura e' li'.
#
#   dove      `dgram_scrivi_uno()`, `src/webtransport.c:1613` (e la seconda
#             chiamata nel ciclo di riempimento, `:1647`)
#   che cosa  `ngtcp2_conn_writev_datagram(..., NGTCP2_WRITE_DATAGRAM_FLAG_MORE |
#             NGTCP2_WRITE_DATAGRAM_FLAG_PADDING, ...)`
#   il cambio mettere `PADDING` **solo quando c'e' davvero un lotto da
#             comporre** — cioe' quando la coda dei datagram ha piu' di un
#             blocco, o quando il video ha byte in coda da infilare nello stesso
#             pacchetto.  Con un datagram solo e la coda del video vuota, il
#             lotto GSO e' di un pacchetto e il riempimento non compra niente.
#   perche'   `[M]` 24 agosto 2026, questo banco: a desktop fermo e Opus
#             negoziato sono **50 datagram/s da 3 byte** che escono in **51
#             pacchetti/s da 1 444 byte** = **589 kbit/s** per **1,2 kbit/s** di
#             suono.  Il riempimento e' il 99,8 %.
#   il rischio ⚠ il riquadro di `:1581` dice perche' `PADDING` c'e': il manuale
#             di ngtcp2 avverte che un primo pacchetto corto **fa collassare
#             l'intero lotto GSO**.  ⇒ Non si toglie: si condiziona.  E la
#             prova che serve e' la stessa di allora — i blocchi rifiutati con
#             il video acceso, non solo la banda a riposo.
#   ⭐ e non   La cura di `audio.c` (il silenzio che non si spedisce) toglie
#     si       quei 50 datagram **alla radice**, quindi su una scena muta rende
#     escludono il `PADDING` irrilevante.  Ma su una scena che SUONA il
#              riempimento resta, e la' serve questa.
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    principale()
