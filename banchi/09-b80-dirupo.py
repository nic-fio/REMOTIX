#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b80-dirupo — **DOVE STA IL GRADINO**, e con che incertezza.

    porta 7950 · sonda 7959… · utente `provanr5` (uid 1050)
    albero `/media/REMOTIX/src/09nr5-src` · lavoro `/media/REMOTIX/tmp/09nr5`
    unita' `remotix-7950` · ban-file e socket suoi

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ DA DOVE NASCE — UNA CONTRADDIZIONE, NON UNA MISURA CHE MANCA
═══════════════════════════════════════════════════════════════════════════════

`banchi/09-b76-rete-cattiva.py` e' stato fatto girare **due volte il 23 agosto
2026** sugli stessi profili, e le due griglie non coincidono sui profili miti:

    | profilo       | primo giro (51b5994) | secondo giro (HEAD) |
    |---------------|----------------------|---------------------|
    | liscio        | 39,97                | 39,88               |
    | ritardo-30    | 40,11                | 39,44               |
    | ⛔ perdita-0,5 | **40,06** · 0 chiavi | ⛔ **19,27** · spirale |
    | ⛔ perdita-1   | **9,56**             | **12,32**           |
    | jitter-5      | 39,30                | 31,45               |
    | raffica-1     | 23,94                | 29,47               |
    | perdita-3     | 4,03                 | 8,58                |

⭐ **Quel che sopravvive comunque**, perche' non dipende dal punto esatto: la
   FORMA e' la stessa — linea sana a ~40 fotogrammi/s, un **dirupo** entro il
   primo punto percentuale di perdita, la spirale di chiavi come meccanismo, e
   il jitter che morde **senza perdere un pacchetto**.

⛔ **Quel che NON si puo' piu' dire e' DOVE stia il gradino**: il primo giro lo
   metteva fra lo 0,36 % e lo 0,94 % di perdita vera; il secondo lo mette
   **prima dello 0,36 %**.  ⇒ Ed e' il numero che conta di piu' di tutta la
   fase, perche' e' quello che dice **su che rete il prodotto smette di
   funzionare**.

Le differenze note fra i due giri sono almeno tre, e nessuna e' stata isolata:

  1. **binario diverso** — `HEAD` porta le righe `rete-quic`, cioe' una
     `registro_dice` in piu' al secondo per sessione;
  2. la **macchina e' stata riavviata** in mezzo (rootfs in RAM);
  3. il **terreno e' stato ricostruito**.

`[?]` E ce n'e' una quarta che nessuno aveva scritto, e questo banco la misura:
     **quanto era carica la macchina**.  Su `192.168.0.2` girano fino a otto
     agenti insieme; due griglie prese a ore diverse hanno visto due macchine
     diverse, e nessuna delle due l'ha annotato.

⇒ `[?]` Non si sa quale delle quattro, ne' se sia semplicemente **rumore fra
  due giri**.  **E' questo che il banco separa.**

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ L'ORDINE DEI PASSI NON E' UNA COMODITA': E' L'ARGOMENTO
═══════════════════════════════════════════════════════════════════════════════

⛔ **Non ha senso confrontare due binari se non si sa quanto vale il rumore fra
   due giri dello STESSO binario.**  Una griglia «prima/dopo» presa senza quel
   numero non da' un rosso: da' una differenza, e chi la legge le attribuisce la
   causa che aveva in mente prima di guardarla.  E' `LEZIONI.md` §1.26 detta sul
   tempo invece che sullo spazio.

⇒ **1 · LA RIPETIBILITA' PRIMA DELLA GRIGLIA.**  Tre giri identici di
     `ritardo-15` e tre di `perdita-0,5`, stesso binario, stesso terreno, di
     seguito.  Il numero che ne esce — **la dispersione** — e' il METRO con cui
     tutto il resto si giudica, e si scrive PRIMA di guardare qualunque altra
     cosa.

  ⚠ E se la dispersione su `perdita-0,5` fosse dell'ordine della differenza fra
    19 e 40, **la contraddizione sarebbe gia' sciolta**: non erano due binari
    diversi, era **un profilo instabile** — e allora la domanda diventa *perche'*
    e' instabile, che e' una scoperta piu' interessante di un numero.
    ⇒ `p_rumore_spiega()`, e il suo verde e il suo rosso sono scritti sotto.

⇒ **2 · LA GRIGLIA FINE.**  Una scala fitta di perdita —
     **0 · 0,1 · 0,2 · 0,3 · 0,5 · 0,75 · 1,0 · 1,5 %** — e la perdita si
     **LEGGE dalla sonda a ogni casella**, non si assume: a queste frazioni la
     differenza fra chiesto e ottenuto conta piu' che altrove.

  ⭐ Il numero che si cerca e' DOPPIO, e le due meta' possono non coincidere:
       a) **a che perdita vera la quota di chiavi lascia lo zero** (§3.3: la
          spirale, che e' il MECCANISMO);
       b) **a che perdita vera i fotogrammi/s scendono sotto 25** (`DECISIONI.md`
          §2.1, che e' il PAVIMENTO).
     ⚠ Se non coincidono, **e' un fatto, non un errore**: vuol dire che la
       spirale comincia prima di farsi vedere sulla scala, ed e' esattamente
       quel che un meccanismo fa prima di diventare un sintomo.

⇒ **3 · IL BINARIO, SOLO SE SERVE ANCORA.**  Se dopo 1 e 2 la differenza fra i
     due giri NON e' spiegata dal rumore, si isola il binario: stessa griglia
     fine, `51b5994` contro `HEAD`, sullo **stesso terreno e nella stessa ora**,
     e con l'`md5` di tutt'e due dichiarato.
     `[?]` Il sospetto da verificare per primo e' che **la riga `rete-quic`
     costi**: e' una `registro_dice` in piu' al secondo, e il registro si scrive
     su disco.
     ⚠ Se invece 1 spiega tutto, **questo passo NON si fa**: isolare una
       differenza che non esiste costa un'ora e produce un numero che sembra
       significare qualcosa.

═══════════════════════════════════════════════════════════════════════════════
⛔ CHE COSA NON E' RISCRITTO — si importa `09-b76`, che e' fatto bene
═══════════════════════════════════════════════════════════════════════════════

`09-b76-rete-cattiva.py` ha **49 casi di `--certifica` verdi** e porta gia'
tutto quel che serve qui: i profili, la **sonda della perdita** (8 000 pacchetti
numerati attraverso lo stesso `netem`), la lettura dei contatori del `qdisc`, la
riduzione della consegna, i testimoni della connessione, le righe `rete-quic`, i
predicati del singolo giro.  ⇒ **Non se ne ricopia una riga**: si importa, e
si controlla che abbia preso il MIO ambiente — che e' la stessa disciplina con
cui lui importa `09-b70`.

⛔ E per la stessa ragione **non si tocca** `09-b76`: ha una griglia certificata
   e altri la stanno leggendo.  Quel che questo banco aggiunge sta tutto qui.

⭐ QUEL CHE QUESTO BANCO AGGIUNGE, e che in `09-b76` non c'era:

  1. **la stessa cella girata piu' volte** — `09-b76` gira ogni profilo UNA
     volta, e una misura sola non ha incertezza: ha solo un valore;
  2. **il carico della macchina misurato attorno a ogni giro** — `[?]` la
     quarta differenza fra i due giri del 23 agosto, quella che nessuno aveva
     scritto;
  3. **il denominatore girato due volte, in apertura e in chiusura** — se i due
     zeri non coincidono, la macchina e' derivata DURANTE la griglia e la
     griglia intera e' contaminata.  ⛔ Senza questo, una deriva lenta si
     leggerebbe come un gradino;
  4. una **sonda piu' fitta**: `SONDA_PACCHETTI=20000` invece di 8 000, perche'
     a 0,1 % di perdita 8 000 pacchetti ne perdono **otto**, e otto non
     misurano un decimo di punto percentuale.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna `(passa, perche)`
═══════════════════════════════════════════════════════════════════════════════

`passa` vale `None` quando il banco **rifiuta di giudicare**, che e' un terzo
esito e non un verde educato (`CODER.md` §3.10).

  **R · `p_ripetibile()`** — tre giri identici stanno dentro il **10 %** di
  semi-escursione sulla mediana.  ⚠ La soglia e' *sufficiente, non giusta*: e'
  il DOPPIO del 5 % che `09-b70` stima come rumore fra due giri, e resta
  comunque molto sotto il 35 % che separerebbe 19,27 da 40,06.

  **S · `p_rumore_spiega()`** — ⭐⭐ **IL PREDICATO PER CUI QUESTO BANCO
  ESISTE**: il rumore misurato spiega la contraddizione del 23 agosto?
    · **rosso** = SI', la spiega ⇒ non erano due binari, era **un profilo
      instabile**, e la griglia di `09-b76` non puo' localizzare nessun gradino;
    · **verde** = NO ⇒ i due giri differivano davvero, e la causa va cercata
      altrove (il binario, il riavvio, il terreno, il carico).
  ⛔ Il rosso qui NON e' un rosso sul prodotto: e' un rosso sullo **strumento**
     del 23 agosto, ed e' l'esito piu' utile dei due.

  **G · `p_gradino_bracchettato()`** — la scala fine mostra un **gradino** e non
  una nuvola: ordinate per perdita VERA, le celle sane stanno tutte prima e le
  rotte tutte dopo.
    · **rosso** = una cella sana compare DOPO una rotta ⇒ non e' un gradino, e
      dire «il dirupo sta fra X e Y» sarebbe inventare un confine;
    · **muto** = sono tutte sane (il gradino sta SOPRA la scala) o tutte rotte
      (sta SOTTO): in nessuno dei due casi la scala lo contiene, e un banco che
      desse un numero lo stesso mentirebbe.

  **U · `p_due_gruppi_uguali()`** — due gruppi di giri differiscono per meno del
  rumore.  ⭐ Serve DUE volte, e la seconda e' quella che chiude la fase:
    · **il denominatore**: lo zero di apertura contro lo zero di chiusura ⇒
      rosso = la macchina e' derivata durante la griglia;
    · **il binario**: `51b5994` contro `HEAD` ⇒ rosso = **il binario conta**.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE CURE DEL PRODOTTO RESTANO SPENTE
═══════════════════════════════════════════════════════════════════════════════

`--sgombra-soglia-ms` e `--ritmo-adattivo` sono dietro interruttore per
l'invariante I6 e l'utente non le ha ancora guardate.  ⇒ Questa griglia e' il
**denominatore**: dice dove sta il dirupo **senza cure**, e senza di lei nessuna
cura ha un numero da battere.

I CODICI D'USCITA
    0   CONFORME · 1 NON CONFORME (c'e' un rosso) · 2 uso/terreno/rete
    3   ⛔ NON HO NIENTE DA GIUDICARE — un giro o un predicato si e' rifiutato

Uso (dal portatile):
    python3 banchi/09-b80-dirupo.py --certifica     ⭐ senza macchina
    python3 banchi/09-b80-dirupo.py terreno
    python3 banchi/09-b80-dirupo.py ripetibilita [--giri 3]
    python3 banchi/09-b80-dirupo.py griglia
    ALBERO=/media/REMOTIX/src/09nr5b-src DENTRO_ALB=/srv/src/09nr5b-src \
        python3 banchi/09-b80-dirupo.py griglia --marca 51b5994
    python3 banchi/09-b80-dirupo.py binario --a HEAD --b 51b5994
    python3 banchi/09-b80-dirupo.py rimetti
"""
import argparse, importlib.util, json, os, statistics, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ L'ISOLAMENTO, SCRITTO PRIMA DELL'IMPORT CHE LO LEGGE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b76` lega le sue costanti all'ambiente **all'import** (e `09-b70` e
#    `07-b65` dentro di lui).  ⇒ L'ambiente si mette QUI, prima di caricarlo: un
#    import fatto e poi corretto scriverebbe nel lavoro di un altro agente e
#    guasterebbe la porta di un altro banco, e la rete e' l'unica cosa che,
#    sbagliata, fa male a chi non c'entra.
#
# ⛔ Le 7900, 7910, 7920 sono termini di paragone gia' misurati e NON si
#    toccano.  Mia e' la **7950**; la sonda sceglie fra le 7959…7955.
PORTA = os.environ.setdefault("PORTA", "7950")
PORTA = int(PORTA)
os.environ.setdefault("PORTE_SONDA", "7959,7958,7957,7956,7955")
UTENTE = os.environ.setdefault("UTENTE", "provanr5")
UID_B = int(os.environ.setdefault("UID_B", "1050"))
MACCHINA = os.environ.setdefault("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.setdefault("PAROLA_SUDO", "nicfio")
IND = os.environ.setdefault("IND", "192.168.0.2")
LAV = os.environ.setdefault("LAV", "/media/REMOTIX/tmp/09nr5")
ALB = os.environ.setdefault("ALBERO", "/media/REMOTIX/src/09nr5-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/" + os.path.basename(ALB))
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/09nr5")
# ⛔ La memoria condivisa della scena e' MIA: `shm_open` di un file che
#    appartiene a un altro utente da' EACCES e la scena muore all'avvio — un
#    guasto che assomiglia in tutto a «il compositore non consegna».
os.environ.setdefault("SHM", "/09nr5")
FUORI = os.environ.setdefault("FUORI", "/tmp/09-b80")
# ⭐ La sonda piu' fitta (⇒ §«QUEL CHE QUESTO BANCO AGGIUNGE», punto 4).
os.environ.setdefault("SONDA_PACCHETTI", "20000")

QUI = os.path.dirname(os.path.abspath(__file__))
DEV = "lo"
VIETATA = "enp7s0"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


B76 = None
B70 = None
RETE = None
LUC = None

CHI = "09-b80"        # ⛔ il nome col quale prendo il lucchetto del netem


def importa(con_macchina=True):
    """⛔⛔ E POI SI CONTROLLA CHE ABBIA PRESO IL MIO AMBIENTE.

    ⚠ Non e' una cerimonia: `09-b76` ha i suoi valori scritti nei `setdefault`,
      e un `setdefault` che arriva PRIMO vince.  Se per qualsiasi ragione il mio
      non fosse arrivato primo, girerei sulla porta **7930** — cioe' dentro il
      banco di un altro agente — e i numeri sarebbero plausibili e falsi.
    """
    global B76, B70, RETE, LUC
    B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))
    guai = []
    for nome, mio, suo in (("porta", PORTA, B76.PORTA), ("utente", UTENTE, B76.UTENTE),
                           ("uid", UID_B, B76.UID_B), ("lavoro", LAV, B76.LAV),
                           ("albero", ALB, B76.ALB), ("shm", "/09nr5", B76.SHM)):
        if mio != suo:
            guai.append("%s: il modulo ha «%s», il mio e' «%s»" % (nome, suo, mio))
    if 7930 in [B76.PORTA] or B76.UTENTE == "provanr1":
        guai.append("⛔ girerei dentro il banco di 09-b76: NON misuro")
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import di 09-b76 non ha preso il mio "
                         "ambiente — " + " · ".join(guai))
    if not con_macchina:
        B76.importa_finto()
        B70 = B76.B70
        return
    B70 = B76.importa()
    RETE = B76.RETE
    LUC = B76.LUC
    if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
        raise SystemExit("⛔ NON TOCCO LA RETE: il modulo della rete ha porta %d, "
                         "dev «%s», vietata «%s»"
                         % (RETE.PORTA, RETE.DEV, RETE.VIETATA))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ LA SCALA FINE — e il ritardo e' LO STESSO su tutte le caselle
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ E questa e' la differenza che rende la scala leggibile.  In `09-b76` il
#     denominatore e' `ritardo-30` (30 ms) e le caselle di perdita hanno
#     `delay 15ms`: fra il denominatore e la prima casella cambiano **due cose**
#     insieme — il ritardo E la perdita — ed e' il modo piu' educato in cui una
#     griglia mente (`LEZIONI.md` §1.26).  Qui il ritardo e' **15 ms ovunque** e
#     l'unica cosa che si muove e' la perdita.
#
# ⛔ E c'e' sempre un ritardo, anche a perdita zero: senza un giro di rete la
#    finestra di congestione non si riempie e il pacer non si accorge di niente
#    (`09-b70` riga ~322).
RITARDO_SCALA_MS = 15
SCALA = [0.0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5]     # % di perdita CHIESTA

# ── le soglie, in un posto solo, e ciascuna con la sua ragione ─────────────
SOGLIA_RIPETIBILE = 0.10
# ⚠ *sufficiente, non giusta*: e' il DOPPIO del 5 % che `09-b70` stima come
#   rumore fra due giri, e resta molto sotto il 35 % che separa 19,27 da 40,06.
#   ⛔ Una soglia piu' stretta darebbe rosso sul rumore normale della macchina;
#     una piu' larga non separerebbe piu' il rumore dalla contraddizione.

# ⭐ LA CONTRADDIZIONE, IN NUMERI, PRESA DALLA TABELLA IN TESTA — e si scrive
#    qui perche' `p_rumore_spiega()` ci si confronta, e un predicato che si
#    confrontasse con un numero deciso dopo aver guardato la misura non
#    giudicherebbe niente.
#    semi-escursione / mediana dei due giri del 23 agosto 2026:
CONTRADDIZIONE = {
    "perdita-0,5": (40.06, 19.27),   # ⇒ 0,350
    "ritardo":     (40.11, 39.44),   # ⇒ 0,008  (`ritardo-30`, il controllo)
}

PAVIMENTO_FPS = 25.0      # `DECISIONI.md` §2.1 — il fondo della scala
SOGLIA_CHIAVI = 1         # §3.3 — «la quota di chiavi LASCIA LO ZERO»
# ⛔ Il criterio e' letteralmente «lascia lo zero», non «supera il tot per
#    cento»: `[M]` 23 ago 2026 i profili sani di `09-b76` hanno **0 chiavi** a
#    regime (la prima chiave sta nella scaldata, che `09-b70.misura()` toglie).
#    ⇒ La prima chiave a regime E' il primo segno della spirale di §5.2.
#    ⚠ E il numero si stampa sempre accanto al giudizio: una prima chiave sola
#      e trecento chiavi sono due fatti diversi dietro lo stesso «rotto».


def _v_ritardo_puro(nominale_ms):
    """⭐ Il denominatore della MIA scala: tardi ma in ordine, e senza perdita.

    ⛔ Non e' `09-b76._v_ritardo`, e per una ragione sola: quello e' inchiodato
       a 30 ms (`25 <= mediano <= 40`) perche' il denominatore di quel banco e'
       `ritardo-30`.  Il mio e' a 15 ms, come **tutte** le caselle della scala.
       ⇒ Stessa forma, stesse soglie di `09-b76` (`CODA_MIA_MAX_PC`), altro
         centro.
    """
    def verifica(s):
        med = s.get("ritardo_mediano_ms", 0)
        if not (0.5 * nominale_ms <= med <= 2.0 * nominale_ms + 10.0):
            return (None, "il ritardo mediano misurato e' %.2f ms e ne avevo "
                          "chiesti %d: NON uso come denominatore un profilo che "
                          "non e' quello che credo" % (med, nominale_ms))
        if s["persi_pc"] > B76.CODA_MIA_MAX_PC:
            return (False, "il denominatore ha perso il %.2f %%: e' la MIA coda "
                           "che butta, e ogni casella della scala e' "
                           "contaminata" % s["persi_pc"])
        if s["fuori_ordine_pc"] > 0.5:
            return (False, "il denominatore ha il %.1f %% di pacchetti fuori "
                           "ordine: non e' liscio" % s["fuori_ordine_pc"])
        return (True, "ritardo mediano %.2f ms, ZERO persi (%d su %d), ZERO "
                      "disordine: il denominatore e' pulito"
                % (med, s["persi"], s["quanti"]))
    return verifica


def casella(chiesto_pc):
    """(nome, regole netem, verifica) per una casella della scala fine."""
    if chiesto_pc <= 0:
        return ("perdita-0,00", ["delay", "%dms" % RITARDO_SCALA_MS],
                _v_ritardo_puro(RITARDO_SCALA_MS))
    nome = ("perdita-%.2f" % chiesto_pc).replace(".", ",")
    return (nome, ["delay", "%dms" % RITARDO_SCALA_MS, "loss",
                   "%g%%" % chiesto_pc],
            B76._v_perdita(chiesto_pc))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ I DUE CRITERI DI ROTTURA — e sono DUE, e possono non coincidere
# ═══════════════════════════════════════════════════════════════════════════
def rotto_chiavi(c):
    """⭐ «la quota di chiavi lascia lo zero» — §3.3 / §5.2, il MECCANISMO."""
    return c.get("chiavi") is not None and c["chiavi"] >= SOGLIA_CHIAVI


def rotto_pavimento(c):
    """`DECISIONI.md` §2.1 — il PAVIMENTO della scala, che e' il SINTOMO."""
    return c.get("fps") is not None and c["fps"] < PAVIMENTO_FPS


CRITERI = [("⭐ la quota di chiavi lascia lo ZERO (§3.3: la spirale — il "
            "MECCANISMO)", rotto_chiavi),
           ("il ritmo scende sotto il pavimento di %.0f/s (§2.1 — il SINTOMO)"
            % PAVIMENTO_FPS, rotto_pavimento)]


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I PREDICATI — SCRITTI PRIMA, e ne torna `(passa, perche)`
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def dispersione(valori):
    """⛔ Non giudica: riduce.  ⇒ `(mediana, semi_escursione, frazione)`, oppure
       `(None, None, None)` se non c'e' abbastanza da ridurre.

    ⚠ **Semi-escursione, non deviazione standard**, e la ragione e' che tre giri
      sono tre: una deviazione standard su tre campioni e' un numero che sembra
      una statistica e non lo e'.  L'escursione (max − min) su tre giri dice
      quel che dice — «tanto sono stati diversi» — e non promette altro.
    """
    v = [x for x in valori if x is not None]
    if len(v) < 2:
        return (None, None, None)
    med = statistics.median(v)
    semi = (max(v) - min(v)) / 2.0
    return (med, semi, (semi / med) if med else None)


def p_ripetibile(nome, valori, soglia=SOGLIA_RIPETIBILE):
    """**R · TRE GIRI IDENTICI DANNO LO STESSO NUMERO?**

    ⛔ E' il primo predicato di tutti perche' e' il METRO: senza, «la griglia A
       differisce dalla griglia B» non e' un fatto, e' una frase.
    ⚠ Meno di tre giri non si giudicano: due valori hanno sempre una
      escursione, e non c'e' modo di sapere se e' il rumore o l'eccezione.
    """
    v = [x for x in valori if x is not None]
    if len(v) < 3:
        return _muto("«%s»: ho %d giri validi su %d, e sotto i tre non c'e' "
                     "dispersione da misurare — c'e' solo una differenza"
                     % (nome, len(v), len(valori)))
    med, semi, fraz = dispersione(v)
    coda = ("mediana %.2f · escursione %.2f–%.2f · semi-escursione %.2f = "
            "%.1f %% della mediana · giri: %s"
            % (med, min(v), max(v), semi, fraz * 100,
               ", ".join("%.2f" % x for x in v)))
    if fraz > soglia:
        return _no("⛔ «%s» NON E' RIPETIBILE: %s — sopra il %.0f %% dichiarato. "
                   "⚠ Un profilo cosi' non localizza nessun gradino: ogni "
                   "confronto che lo attraversa misura il rumore"
                   % (nome, coda, soglia * 100))
    return _si("«%s» e' ripetibile: %s (sotto il %.0f %% dichiarato)"
               % (nome, coda, soglia * 100))


def p_rumore_spiega(nome, fraz_rumore, coppia):
    """**S · ⭐⭐ IL PREDICATO PER CUI QUESTO BANCO ESISTE.**

    Il rumore fra tre giri identici spiega la differenza fra i due giri del 23
    agosto 2026?

      · **rosso** = SI', la spiega ⇒ non erano due binari diversi, era **un
        profilo instabile**, e la griglia di `09-b76` non puo' localizzare
        nessun gradino.  ⛔ Non e' un rosso sul prodotto: e' un rosso sullo
        STRUMENTO, ed e' l'esito piu' utile dei due;
      · **verde** = NO ⇒ i due giri differivano davvero, e la causa va cercata
        altrove (il binario, il riavvio, il terreno, il carico).

    ⚠ E il confronto e' fra due **frazioni**, non fra due fotogrammi al secondo:
      19,27 e 40,06 non si confrontano con «2 fotogrammi di rumore», si
      confrontano con «il 35 % di semi-escursione».
    """
    if fraz_rumore is None:
        return _muto("«%s»: senza dispersione misurata non posso dire se il "
                     "rumore spieghi qualcosa" % nome)
    a, b = coppia
    med_c = statistics.median([a, b])
    fraz_c = (abs(a - b) / 2.0) / med_c if med_c else None
    if fraz_c is None:
        return _muto("la contraddizione del 23 agosto non ha una mediana")
    coda = ("il rumore misurato oggi vale il %.1f %% · la contraddizione del 23 "
            "agosto (%.2f contro %.2f) vale il %.1f %%"
            % (fraz_rumore * 100, a, b, fraz_c * 100))
    if fraz_rumore >= fraz_c:
        return _no("⛔⛔ IL RUMORE SPIEGA LA CONTRADDIZIONE: %s ⇒ «%s» e' un "
                   "profilo INSTABILE, e i due giri del 23 agosto non erano due "
                   "binari diversi: erano lo stesso banco due volte. ⚠ La "
                   "griglia di 09-b76 non localizza nessun gradino su questo "
                   "profilo" % (coda, nome))
    return _si("il rumore NON spiega la contraddizione: %s ⇒ i due giri del 23 "
               "agosto differivano davvero, e la causa e' altrove" % coda)


def p_gradino_bracchettato(celle, criterio, come_si_chiama):
    """**G · LA SCALA MOSTRA UN GRADINO, O UNA NUVOLA?**

    ⛔ Ordinate per perdita **VERA** (quella della sonda, non quella chiesta:
       a queste frazioni chiesto e ottenuto non coincidono), le celle sane
       devono stare tutte PRIMA e le rotte tutte DOPO.

      · **rosso** = una cella sana compare dopo una rotta ⇒ non e' un gradino,
        e dire «il dirupo sta fra X e Y» sarebbe inventare un confine;
      · **muto** = tutte sane (il gradino sta SOPRA la scala) o tutte rotte
        (sta SOTTO).  ⛔ In nessuno dei due casi la scala lo contiene, e un
        banco che desse un numero lo stesso mentirebbe.
      · **verde** = il gradino c'e', ed e' **bracchettato** fra l'ultima sana e
        la prima rotta.  ⚠ La larghezza della forbice si stampa: e' l'unica
        incertezza onesta su «dove sta il dirupo».
    """
    buone = [c for c in celle
             if c.get("esito") == "misurato" and c.get("vera_pc") is not None]
    if len(buone) < 3:
        return _muto("ho %d celle misurate su %d: sotto le tre non c'e' nessuna "
                     "scala da leggere" % (len(buone), len(celle)))
    buone = sorted(buone, key=lambda c: c["vera_pc"])
    stati = [bool(criterio(c)) for c in buone]
    riga = " · ".join("%.3f%%:%s" % (c["vera_pc"], "ROTTA" if s else "sana")
                      for c, s in zip(buone, stati))
    if not any(stati):
        return _muto("⚠ NESSUNA cella e' rotta secondo «%s»: il gradino sta "
                     "SOPRA la mia scala (che arriva a %.3f %% di perdita "
                     "vera), e non lo invento — %s"
                     % (come_si_chiama, buone[-1]["vera_pc"], riga))
    if all(stati):
        return _muto("⚠ TUTTE le celle sono rotte secondo «%s», compreso il "
                     "denominatore a %.3f %%: il gradino sta SOTTO la mia "
                     "scala, e non lo invento — %s"
                     % (come_si_chiama, buone[0]["vera_pc"], riga))
    primo_rotto = stati.index(True)
    if False in stati[primo_rotto:]:
        return _no("⛔ NON E' UN GRADINO, E' UNA NUVOLA: dopo la prima cella "
                   "rotta ne torna una sana — %s. ⚠ Su una scala cosi' «il "
                   "dirupo sta fra X e Y» sarebbe un confine inventato" % riga)
    basso = buone[primo_rotto - 1]["vera_pc"] if primo_rotto else 0.0
    alto = buone[primo_rotto]["vera_pc"]
    return _si("⭐ IL GRADINO C'E' ED E' BRACCHETTATO fra **%.3f %%** e "
               "**%.3f %%** di perdita vera (forbice %.3f punti) secondo «%s» — "
               "%s" % (basso, alto, alto - basso, come_si_chiama, riga))


def p_due_gruppi_uguali(nome_a, va, nome_b, vb, fraz_rumore, che_cosa):
    """**U · DUE GRUPPI DI GIRI DIFFERISCONO PER MENO DEL RUMORE?**

    ⭐ Serve DUE volte, e sono due domande diverse con la stessa forma:

      1. **il denominatore** — lo zero di apertura contro lo zero di chiusura.
         ⛔ Rosso = la macchina e' derivata DURANTE la griglia, e allora una
            deriva lenta si sarebbe letta come un gradino;
      2. **il binario** — `51b5994` contro `HEAD`.  Rosso = **il binario conta**.

    ⚠ E il metro e' sempre lo stesso: il rumore misurato al passo 1.  Un
      confronto che si desse un metro suo non sarebbe piu' confrontabile con
      gli altri.
    """
    ma, _, _ = dispersione(va)
    mb, _, _ = dispersione(vb)
    if ma is None or mb is None:
        return _muto("%s: uno dei due gruppi ha meno di due giri validi "
                     "(«%s» %s · «%s» %s)"
                     % (che_cosa, nome_a, len(va), nome_b, len(vb)))
    if fraz_rumore is None:
        return _muto("%s: senza il rumore misurato non ho metro per dire se la "
                     "differenza conti" % che_cosa)
    med = statistics.median([ma, mb])
    fraz = abs(ma - mb) / med if med else None
    coda = ("«%s» %.2f contro «%s» %.2f = %.1f %% di differenza, contro un "
            "rumore del %.1f %%" % (nome_a, ma, nome_b, mb, fraz * 100,
                                    fraz_rumore * 100))
    if fraz > fraz_rumore:
        return _no("⛔ %s — LA DIFFERENZA E' PIU' GRANDE DEL RUMORE: %s"
                   % (che_cosa, coda))
    return _si("%s — la differenza sta dentro il rumore: %s" % (che_cosa, coda))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL CARICO DELLA MACCHINA — `[?]` la quarta differenza, che nessuno aveva
#    scritto
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Su `192.168.0.2` girano fino a otto agenti insieme.  Due griglie prese a
#    ore diverse hanno visto due macchine diverse, e nessuna delle due
#    l'ha annotato.  ⇒ Qui si legge attorno a OGNI giro, e si stampa accanto al
#    numero: se la dispersione seguisse il carico, la risposta sarebbe li'.
#
# ⚠ Si legge da `/proc/stat`, che e' cumulativo dall'avvio: il numero che conta
#   e' la DIFFERENZA fra prima e dopo, non il valore assoluto.
def _istante_cpu():
    try:
        rc, out, _ = RETE.rem("cat /proc/stat /proc/loadavg", 30)
    except Exception:
        return None
    prima = None
    carico = None
    for riga in out.splitlines():
        if riga.startswith("cpu ") and prima is None:
            v = [int(x) for x in riga.split()[1:]]
            fermo = v[3] + (v[4] if len(v) > 4 else 0)     # idle + iowait
            prima = (sum(v) - fermo, sum(v))
        elif riga and riga[0].isdigit():
            carico = riga.split()[0]
    return (prima, carico) if prima else None


def _cpu_fra(a, b):
    """(percentuale occupata, carico di partenza) — o `(None, None)`."""
    if not a or not b:
        return (None, None)
    (ba, ta), c = a[0], a[1]
    (bb, tb), _ = b[0], b[1]
    dt = tb - ta
    if dt <= 0:
        return (None, c)
    return (round(100.0 * (bb - ba) / dt, 1), c)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ UNA CELLA — il giro solo, con la sua sonda e i suoi predicati
# ═══════════════════════════════════════════════════════════════════════════
GIRO_N = [0]


def cella(nome, regole, verifica, secondi, etichetta=""):
    """⛔ Fa quel che fa il ciclo di `09-b76.principale()` su UN profilo, e non
       una riga di piu': niente coppia I1, niente scena ferma.  ⇒ Le funzioni
       sono le SUE, l'ordine e' il suo, e quel che cambia e' che questa si puo'
       chiamare tre volte di fila sullo stesso profilo.
    """
    etichetta = etichetta or nome
    _log("%s" % etichetta)
    ok, q = RETE.stringi(B76._regole(regole))
    if not ok:
        _ko(q)
        return {"cella": nome, "etichetta": etichetta,
                "esito": "NON HO NIENTE DA GIUDICARE — tc ha rifiutato la regola"}
    B76.filtri_sonda()
    riletta = B76.regola_riletta()
    passa_r, perche_r = B76.controlla_regola(regole, riletta)
    (_ok if passa_r else _ko)("la regola: %s" % perche_r)
    if not passa_r:
        return {"cella": nome, "etichetta": etichetta, "regola_riletta": riletta,
                "esito": "NON HO NIENTE DA GIUDICARE — la regola installata non "
                         "e' quella chiesta"}

    # ⭐ PRIMA la sonda, POI il giro: cosi' i contatori del qdisc che leggo
    #   attorno al giro non portano dentro i pacchetti della sonda.
    s = B76.sonda_gira()
    B76.stampa_sonda(s)
    passa_g, perche_g = B76.p_guasto_messo(nome, verifica, s)
    (_ok if passa_g else (_dub if passa_g is None else _ko))(
        "IL GUASTO E' STATO MESSO: %s" % perche_g)

    usc = B76.scena_accendi("barra")
    if not usc:
        _ko("la scena non parte: NON giudico questa cella")
        B76.scena_spegni()
        return {"cella": nome, "etichetta": etichetta, "sonda": s,
                "guasto": {"passa": passa_g, "perche": perche_g},
                "esito": "NON HO NIENTE DA GIUDICARE — la scena non e' partita"}

    prima_q = B76.conti_qdisc()
    prima_c = _istante_cpu()
    riga0 = B76.righe_registro()
    # ⛔ Il nome del giro porta un contatore: e' lui a battezzare il file della
    #    traccia (`LAV/<nome>.rcpreg`), e tre giri identici che si chiamassero
    #    tutti uguale si sovrascriverebbero — con l'ultimo che sembra il primo.
    GIRO_N[0] += 1
    n = B70.giro("%s-g%03d" % (nome, GIRO_N[0]), "barra", B70.TELA_PIENA,
                 secondi)
    dopo_c = _istante_cpu()
    dopo_q = B76.conti_qdisc()
    B76.scena_spegni()
    n["testimoni"] = B76.testimoni_connessione(riga0, n)
    n["quic"] = B76.leggi_rete_quic(riga0)
    B70.stampa_giro(n)
    B76.stampa_consegna(n)
    B76.stampa_testimoni(n["testimoni"])
    B76.stampa_terza_gamba(n, n["quic"])
    delta = None
    if prima_q and dopo_q:
        delta = {k: dopo_q[k] - prima_q[k] for k in prima_q}
    cpu_pc, carico = _cpu_fra(prima_c, dopo_c)
    _inf("MACCHINA cpu occupata durante il giro: %s %% · carico all'inizio: %s"
         % (cpu_pc if cpu_pc is not None else "NON LETTA", carico or "?"))

    # ── i predicati del singolo giro, e sono quelli di `09-b76` ─────────────
    pred = []
    for etich, (passa, perche) in (
            ("⛔ la CONNESSIONE non e' caduta (§3.3/§8.3)",
             B76.p_connessione_viva(n.get("testimoni"))),
            ("⭐⭐ la CONSEGNA non si e' fermata",
             B76.p_consegna_non_si_ferma(n)),
            ("⛔ la MIA coda non butta niente di suo",
             B76.p_coda_mia(nome, not regole or "loss" not in regole, delta))):
        (_ok if passa else (_dub if passa is None else _ko))("%s: %s"
                                                             % (etich, perche))
        pred.append({"predicato": etich, "passa": passa, "perche": perche})

    c = (n.get("consegna") or {})
    return {"cella": nome, "etichetta": etichetta,
            "chiesto_pc": _chiesto_da(regole),
            "vera_pc": s["persi_pc"] if B76._ha_sondato(s) else None,
            "raffica_media": s.get("raffica_media") if B76._ha_sondato(s) else None,
            "regola_riletta": riletta,
            "esito": n.get("esito"),
            "fps": n.get("fps"), "fps_min": n.get("fps_finestra_min"),
            "chiavi": n.get("chiavi"), "delta_fot": n.get("delta"),
            "quota_delta": n.get("quota_delta"),
            "copertura": c.get("copertura"), "buco_max_s": c.get("buco_max_s"),
            "deriva_fine_ms": n.get("deriva_fine_ms"),
            "non_spediti": (n.get("server") or {}).get("non_spediti"),
            "cwnd_mediana": (n.get("quic") or {}).get("cwnd_mediana"),
            "cpu_pc": cpu_pc, "carico": carico,
            "qdisc": delta, "sonda": s,
            "guasto": {"passa": passa_g, "perche": perche_g},
            "predicati": pred}


def _chiesto_da(regole):
    for i, x in enumerate(regole):
        if x == "loss" and i + 1 < len(regole):
            try:
                return float(regole[i + 1].rstrip("%"))
            except ValueError:
                return None
    return 0.0


def riga_cella(c):
    return ("   %-16s chiesto %5s %%  VERA %7s %%  |  %6s /s  peggior sec %5s  "
            "|  chiavi %5s  delta %5s  |  copertura %5s  buco %5s s  |  cpu %5s %%"
            % (c.get("etichetta", c.get("cella")),
               c.get("chiesto_pc"), c.get("vera_pc"),
               c.get("fps"), c.get("fps_min"), c.get("chiavi"),
               c.get("quota_delta"), c.get("copertura"), c.get("buco_max_s"),
               c.get("cpu_pc")))


def stampa_griglia(titolo, celle):
    _log(titolo)
    for c in celle:
        if c.get("esito") == "misurato":
            print(riga_cella(c))
        else:
            _dub("%-16s %s" % (c.get("etichetta"), c.get("esito")))


def salva(nome, roba):
    os.makedirs(FUORI, exist_ok=True)
    p = os.path.join(FUORI, nome)
    with open(p, "w") as f:
        json.dump(roba, f, ensure_ascii=False, indent=1)
    _inf("scritto in %s" % p)
    return p


def leggi(nome):
    p = os.path.join(FUORI, nome)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL CONTROLLO POSITIVO — «come fa questo banco a sapere di saper vedere?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«un banco che non sa vedere il difetto che cerca non ha
#    diritto al verde»*.  ⇒ Qui si fabbricano numeri e si controlla che i
#    quattro predicati diano quel che e' scritto PRIMA — verde, rosso **e muto**.
def _c(vera, fps, chiavi, esito="misurato"):
    """Una cella finta, con i soli campi che i predicati guardano."""
    return {"cella": "finta", "etichetta": "finta", "vera_pc": vera,
            "fps": fps, "chiavi": chiavi, "esito": esito}


def certifica():
    print("⭐ CERTIFICAZIONE DEL BANCO DEL DIRUPO — l'atteso e' scritto PRIMA\n")
    print("   ⛔ Nessun contatto con la macchina di prova: qui si prova lo "
          "STRUMENTO,\n      non il prodotto.\n")
    importa(con_macchina=False)
    verde = True
    n = [0]

    def caso(titolo, atteso, avuto):
        n[0] += 1
        passa, perche = avuto
        ok = (passa is atteso) if atteso is None else (passa == atteso)
        print("  %2d · %s" % (n[0], titolo))
        print("       atteso %-5s   avuto %-5s   %s"
              % (atteso, passa, perche[:150]))
        if ok:
            _ok("come scritto")
        else:
            _ko("⛔ IL BANCO NON SA VEDERE QUEL CHE DICE DI CERCARE")
        return ok

    # ── R · p_ripetibile ───────────────────────────────────────────────────
    _log("R · «tre giri identici danno lo stesso numero?»")
    verde &= caso("tre giri stretti (39,9 · 40,1 · 40,0) ⇒ VERDE", True,
                  p_ripetibile("finto", [39.9, 40.1, 40.0]))
    verde &= caso("⛔ tre giri come la contraddizione (40,1 · 19,3 · 30,0) ⇒ "
                  "ROSSO", False, p_ripetibile("finto", [40.1, 19.3, 30.0]))
    verde &= caso("⭐ il rosso arriva ANCHE senza un crollo, al 12 % "
                  "(40 · 35 · 44) ⇒ ROSSO", False,
                  p_ripetibile("finto", [40.0, 35.0, 44.0]))
    verde &= caso("⚠ il caso al confine: 10 % esatto (40 · 36 · 44) ⇒ VERDE "
                  "(la soglia non e' stretta)", True,
                  p_ripetibile("finto", [40.0, 36.0, 44.0]))
    verde &= caso("⛔ due giri soli ⇒ MUTO (una differenza non e' una "
                  "dispersione)", None, p_ripetibile("finto", [40.0, 20.0]))
    verde &= caso("⛔ tre giri di cui uno non ha misurato ⇒ MUTO", None,
                  p_ripetibile("finto", [40.0, 39.0, None]))

    # ── S · p_rumore_spiega ────────────────────────────────────────────────
    _log("S · ⭐⭐ «il rumore spiega la contraddizione del 23 agosto?»")
    verde &= caso("rumore 2 % contro una contraddizione del 35 % ⇒ VERDE (non "
                  "la spiega)", True,
                  p_rumore_spiega("perdita-0,5", 0.02,
                                  CONTRADDIZIONE["perdita-0,5"]))
    verde &= caso("⛔⛔ rumore 40 % contro una contraddizione del 35 % ⇒ ROSSO "
                  "(era un profilo instabile)", False,
                  p_rumore_spiega("perdita-0,5", 0.40,
                                  CONTRADDIZIONE["perdita-0,5"]))
    verde &= caso("⚠ rumore 1 % contro la contraddizione del RITARDO (0,8 %) ⇒ "
                  "ROSSO: anche una contraddizione piccola si spiega col "
                  "rumore, se il rumore e' piu' grande", False,
                  p_rumore_spiega("ritardo", 0.01, CONTRADDIZIONE["ritardo"]))
    verde &= caso("⛔ senza dispersione misurata ⇒ MUTO", None,
                  p_rumore_spiega("perdita-0,5", None,
                                  CONTRADDIZIONE["perdita-0,5"]))

    # ── G · p_gradino_bracchettato ─────────────────────────────────────────
    _log("G · «la scala mostra un gradino, o una nuvola?»")
    sano_poi_rotto = [_c(0.00, 40.0, 0), _c(0.09, 39.8, 0), _c(0.21, 39.5, 0),
                      _c(0.48, 19.0, 88), _c(0.97, 12.0, 240)]
    passa, perche = p_gradino_bracchettato(sano_poi_rotto, rotto_chiavi,
                                           "le chiavi")
    verde &= caso("⭐ tre sane poi due rotte ⇒ VERDE, e la forbice e' "
                  "0,21–0,48", True, (passa, perche))
    if passa and not ("0.210" in perche and "0.480" in perche):
        _ko("⛔ la forbice stampata non e' quella attesa"); verde = False
    else:
        _ok("la forbice e' quella attesa")
    nuvola = [_c(0.00, 40.0, 0), _c(0.09, 18.0, 90), _c(0.21, 39.5, 0),
              _c(0.48, 19.0, 88), _c(0.97, 12.0, 240)]
    verde &= caso("⛔ una sana DOPO una rotta ⇒ ROSSO (e' una nuvola, non un "
                  "gradino)", False,
                  p_gradino_bracchettato(nuvola, rotto_chiavi, "le chiavi"))
    verde &= caso("⛔ tutte sane ⇒ MUTO (il gradino sta SOPRA la scala)", None,
                  p_gradino_bracchettato(
                      [_c(0.00, 40.0, 0), _c(0.09, 39.8, 0), _c(0.21, 39.5, 0)],
                      rotto_chiavi, "le chiavi"))
    verde &= caso("⛔ tutte rotte, denominatore compreso ⇒ MUTO (sta SOTTO)",
                  None, p_gradino_bracchettato(
                      [_c(0.00, 12.0, 40), _c(0.09, 11.0, 90), _c(0.21, 9.0, 99)],
                      rotto_chiavi, "le chiavi"))
    verde &= caso("⛔ due sole celle misurate ⇒ MUTO", None,
                  p_gradino_bracchettato([_c(0.00, 40.0, 0), _c(0.48, 19.0, 88)],
                                         rotto_chiavi, "le chiavi"))
    verde &= caso("⛔ celle che non hanno misurato NON contano nella scala ⇒ "
                  "MUTO con tre finte su cinque", None,
                  p_gradino_bracchettato(
                      [_c(0.00, 40.0, 0), _c(0.09, None, None, "NON HO NIENTE"),
                       _c(0.21, None, None, "NON HO NIENTE")],
                      rotto_chiavi, "le chiavi"))
    # ⭐⭐ E IL CASO CHE VALE PER DUE: i due criteri possono NON coincidere, ed
    #    e' un fatto, non un errore.  Qui la spirale e' gia' partita e il
    #    pavimento tiene ancora.
    misto = [_c(0.00, 40.0, 0), _c(0.09, 39.8, 0), _c(0.21, 38.0, 12),
             _c(0.48, 33.0, 90), _c(0.97, 12.0, 240)]
    pa, ca = p_gradino_bracchettato(misto, rotto_chiavi, "le chiavi")
    pb, cb = p_gradino_bracchettato(misto, rotto_pavimento, "il pavimento")
    verde &= caso("⭐⭐ le CHIAVI lasciano lo zero gia' a 0,21 % ⇒ VERDE",
                  True, (pa, ca))
    verde &= caso("⭐⭐ …e il PAVIMENTO regge fino a 0,97 % ⇒ VERDE, con una "
                  "forbice DIVERSA: le due soglie non coincidono, ed e' un "
                  "fatto", True, (pb, cb))
    if pa and pb and ("0.090" in ca and "0.210" in ca) and \
            ("0.480" in cb and "0.970" in cb):
        _ok("⭐ le due forbici sono diverse, e il banco lo dice invece di "
            "sceglierne una")
    else:
        _ko("⛔ il banco non separa le due soglie"); verde = False

    # ── U · p_due_gruppi_uguali ────────────────────────────────────────────
    _log("U · «due gruppi di giri differiscono per meno del rumore?»")
    verde &= caso("due zeri d'apertura e chiusura uguali ⇒ VERDE", True,
                  p_due_gruppi_uguali("apertura", [40.0, 39.8], "chiusura",
                                      [39.9, 40.1], 0.05, "IL DENOMINATORE"))
    verde &= caso("⛔ la chiusura e' calata del 25 % ⇒ ROSSO (la macchina e' "
                  "derivata durante la griglia)", False,
                  p_due_gruppi_uguali("apertura", [40.0, 39.8], "chiusura",
                                      [30.0, 30.2], 0.05, "IL DENOMINATORE"))
    verde &= caso("⛔ il binario nuovo rende il 20 % in meno ⇒ ROSSO (il "
                  "binario conta)", False,
                  p_due_gruppi_uguali("51b5994", [40.0, 40.2], "HEAD",
                                      [32.0, 32.2], 0.05, "IL BINARIO"))
    verde &= caso("⛔ un gruppo con un giro solo ⇒ MUTO", None,
                  p_due_gruppi_uguali("a", [40.0], "b", [39.0, 39.2], 0.05,
                                      "IL BINARIO"))
    verde &= caso("⛔ senza rumore misurato ⇒ MUTO (non ho metro)", None,
                  p_due_gruppi_uguali("a", [40.0, 40.1], "b", [39.0, 39.2],
                                      None, "IL BINARIO"))

    # ── i due criteri di rottura, esercitati da soli ───────────────────────
    _log("⛔ I DUE CRITERI DI ROTTURA, esercitati da soli")
    prove = [("una chiave sola a regime E' la spirale che parte",
              rotto_chiavi(_c(0.5, 39.0, 1)), True),
             ("zero chiavi non e' spirale", rotto_chiavi(_c(0.5, 39.0, 0)), False),
             ("⛔ «chiavi non lette» non e' «zero chiavi»",
              rotto_chiavi(_c(0.5, 39.0, None)), False),
             ("24,9/s e' sotto il pavimento", rotto_pavimento(_c(0.5, 24.9, 0)), True),
             ("25,0/s NON e' sotto il pavimento",
              rotto_pavimento(_c(0.5, 25.0, 0)), False),
             ("⛔ «fps non letti» non e' «zero fps»",
              rotto_pavimento(_c(0.5, None, 0)), False)]
    for titolo, avuto, atteso in prove:
        n[0] += 1
        print("  %2d · %s — atteso %s, avuto %s" % (n[0], titolo, atteso, avuto))
        if avuto == atteso:
            _ok("come scritto")
        else:
            _ko("⛔ il criterio non fa quel che dice"); verde = False

    # ── la riduzione della dispersione ─────────────────────────────────────
    _log("⛔ LA RIDUZIONE DELLA DISPERSIONE (semi-escursione, non deviazione)")
    med, semi, fraz = dispersione([40.06, 19.27])
    n[0] += 1
    atteso = (40.06 - 19.27) / 2.0 / statistics.median([40.06, 19.27])
    print("  %2d · la contraddizione del 23 agosto vale %.4f (atteso %.4f)"
          % (n[0], fraz, atteso))
    if abs(fraz - atteso) < 1e-9 and abs(fraz - 0.350) < 0.002:
        _ok("⭐ il 35 % scritto in testa e' il numero che esce dalla riduzione")
    else:
        _ko("⛔ il numero in testa e la riduzione non coincidono"); verde = False
    n[0] += 1
    print("  %2d · un valore solo non ha dispersione" % n[0])
    if dispersione([40.0]) == (None, None, None):
        _ok("come scritto: (None, None, None)")
    else:
        _ko("⛔ un valore solo ha prodotto una dispersione"); verde = False

    # ── il metro, e il suo pavimento ───────────────────────────────────────
    _log("⛔ IL METRO — «ciascuno col suo, e mai piu' fine del 5 %»")
    for titolo, avuto, atteso in (
            ("un rumore dello 0,4 % non fa scendere il metro sotto il 5 %",
             metro(0.004), METRO_MINIMO),
            ("un rumore del 14,8 % resta 14,8 %", metro(0.148), 0.148),
            ("⛔ «rumore non misurato» resta None, non diventa il pavimento",
             metro(None), None)):
        n[0] += 1
        print("  %2d · %s — atteso %s, avuto %s" % (n[0], titolo, atteso, avuto))
        if avuto == atteso:
            _ok("come scritto")
        else:
            _ko("⛔ il metro non fa quel che dice"); verde = False

    # ── l'unione dei giri di una casella ───────────────────────────────────
    _log("⭐⭐ L'UNIONE DEI GIRI DI UNA CASELLA — «1 rotta su 2» e' il CONFINE, "
         "non un errore")
    u = unisci([_c(0.48, 36.7, 0), _c(0.52, 28.2, 47)], "perdita-0,50", 0.5)
    n[0] += 1
    print("  %2d · due giri discordi (36,7 senza chiavi · 28,2 con 47) ⇒ "
          "mediana %.2f, chiavi %s, «1 su 2 rotte» sulle chiavi"
          % (n[0], u["fps"], u["chiavi"]))
    if (u["esito"] == "misurato" and abs(u["fps"] - 32.45) < 0.01
            and u["rotte"][CRITERI[0][0]] == 1 and u["giri_validi"] == 2
            and abs(u["vera_pc"] - 0.5) < 0.001):
        _ok("⭐ la casella porta la mediana E il disaccordo, e non ne nasconde "
            "nessuno dei due")
    else:
        _ko("⛔ l'unione perde il disaccordo dentro la casella"); verde = False
    n[0] += 1
    u2 = unisci([_c(0.48, 40.0, 0), _c(0.0, None, None, "NON HO NIENTE")],
                "x", 0.5)
    print("  %2d · un giro su due non ha misurato ⇒ la casella vive con un giro "
          "solo, e lo DICE (validi %s su %s)"
          % (n[0], u2["giri_validi"], u2["giri"]))
    if u2["esito"] == "misurato" and u2["giri_validi"] == 1 and u2["giri"] == 2:
        _ok("come scritto")
    else:
        _ko("⛔ la casella non dichiara quanti giri l'hanno fatta"); verde = False
    n[0] += 1
    u3 = unisci([_c(0.0, None, None, "NON HO NIENTE")], "x", 0.5)
    print("  %2d · nessun giro valido ⇒ la casella NON GIUDICA (non «zero»)"
          % n[0])
    if u3["esito"].startswith("NON HO NIENTE"):
        _ok("come scritto")
    else:
        _ko("⛔ una casella senza giri ha prodotto un numero"); verde = False

    print()
    if verde:
        _ok("⭐ %d casi: il banco sa dare VERDE, ROSSO e MUTO dove e' scritto"
            % n[0])
    else:
        _ko("⛔ IL BANCO NON HA DIRITTO AL VERDE: c'e' un caso che non fa quel "
            "che dice")
    return 0 if verde else 1


# ═══════════════════════════════════════════════════════════════════════════
# LA META' CHE PARLA CON LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def apparecchia():
    """⛔ Tutto quel che deve stare in piedi PRIMA di prendere il lucchetto: i
       copioni, la porta della sonda, il terreno.  ⚠ Prendere il lucchetto e poi
       scoprire che manca il terreno vorrebbe dire tenere fermi gli altri agenti
       per un guasto mio."""
    if not B76.spedisci_sonda():
        _ko("i copioni non si sono scritti in %s" % LAV)
        return False
    if B76.scegli_porta_sonda() is None:
        _ko("⛔ nessuna delle mie porte per la sonda e' libera: NON misuro, "
            "perche' senza sonda non so se il guasto sia stato messo")
        return False
    _ok("la sonda e il lettore sono in %s · la sonda usera' la porta %d"
        % (LAV, B76.PORTA_SONDA))
    return B76.B70.terreno_controlla()


def stato_macchina():
    """⭐ COM'ERA LA MACCHINA QUANDO HO COMINCIATO — e si scrive, non si ricorda.

    ⛔ `[M]` 23 ago 2026: `09-b76` ha lasciato acceso il server 7930, `09-b79` il
       7940, `09-b70` il 7809.  Un server acceso e FERMO non e' un banco che
       gira, ma se qualcuno ci si attaccasse i miei numeri sarebbero sporchi.
    """
    _log("COM'E' LA MACCHINA ADESSO — si dichiara, e non si ricorda")
    rc, out, _ = RETE.rem("cat /proc/loadavg; nproc; "
                          "systemctl list-units --no-legend 'remotix-*' "
                          "| awk '{print $1, $4}'; echo ---; "
                          "ss -lnu 2>/dev/null | grep -oE ':(7[89][0-9][0-9])' "
                          "| sort -u | tr '\\n' ' '", 60)
    for riga in out.splitlines():
        _inf(riga.strip())
    return out


def misura_gruppo(nome, regole, verifica, secondi, quanti, marca=""):
    """N giri IDENTICI di seguito, sullo stesso `netem`.

    ⛔ La regola si rimette a ogni giro (`RETE.stringi` fa `del root` + `add`),
       e non e' uno spreco: `[M]` 23 ago 2026 `tc qdisc change` e' APPICCICOSO, e
       un giro che ereditasse la regola del precedente misurerebbe una rete che
       nessuno ha chiesto.
    """
    fuori = []
    for i in range(quanti):
        et = "%s · giro %d/%d%s" % (nome, i + 1, quanti,
                                    (" [%s]" % marca) if marca else "")
        fuori.append(cella(nome, regole, verifica, secondi, etichetta=et))
        rinnova_se_serve()
    return fuori


SCADENZA = [0.0]
AFFITTO = 900


def rinnova_se_serve():
    """⛔ Gli affitti si prendono CORTI e si rinnovano: ci sono altri agenti in
       coda, e un affitto lungo li ferma anche quando ho finito."""
    if time.time() > SCADENZA[0] - 400:
        if B76.rinnova(CHI, AFFITTO):
            SCADENZA[0] = time.time() + AFFITTO
            _inf("⛔ affitto del lucchetto rinnovato per %d s" % AFFITTO)
        else:
            raise SystemExit("⛔ il lucchetto non e' piu' mio: MI FERMO")


def valori(celle, chiave="fps"):
    return [c.get(chiave) if c.get("esito") == "misurato" else None
            for c in celle]


METRO_MINIMO = 0.05
# ⛔⛔ IL PAVIMENTO DEL METRO, e non e' prudenza: e' il 5 % che `09-b70` dichiara
#     come rumore fra due giri.  `[M]` 23 ago 2026 il mio denominatore ha una
#     dispersione dello **0,4 %** su tre giri — e un metro cosi' fine darebbe
#     ROSSO al primo respiro della macchina, cioe' misurerebbe il rumore e lo
#     chiamerebbe deriva.  ⇒ Il metro non scende mai sotto il 5 %.


def metro(fraz):
    """⛔ Il metro per confrontare due gruppi e' il rumore del profilo **che si
       sta confrontando**, mai quello del profilo piu' instabile della giornata.

    ⚠ `[M]` 23 ago 2026: il denominatore ha lo 0,4 % di dispersione e
      `perdita-0,5` ne ha il 14,8 %.  Usare il 14,8 % per giudicare il
      denominatore assolverebbe una deriva vera del 10 %; usare lo 0,4 % per
      giudicare `perdita-0,5` darebbe rosso a ogni confronto.  ⇒ Ciascuno col suo.
    """
    if fraz is None:
        return None
    return max(fraz, METRO_MINIMO)


def unisci(celle, nome, chiesto_pc):
    """⭐⭐ PIU' GIRI DELLA STESSA CASELLA DIVENTANO UNA CASELLA SOLA — e questa
       funzione esiste per un difetto che avrei avuto senza.

    ⛔ Se i giri entrassero nella scala uno per uno, due giri della STESSA
       casella che non concordano sul criterio farebbero fallire il controllo di
       monotonia di `p_gradino_bracchettato()`, e il banco direbbe *«non e' un
       gradino, e' una nuvola»* per un disaccordo **dentro** una casella, che e'
       tutt'altro fatto: e' l'incertezza della casella, non il disordine della
       scala.
    ⇒ Si riduce **alla mediana**, e si conserva accanto quanti giri erano rotti
      su quanti: `[M]` 23 ago 2026 la dispersione dei fotogrammi/s a 0,5 % di
      perdita e' del **14,8 %**, e una casella che dicesse un numero solo
      fingerebbe una precisione che non ha.

    ⚠ E una casella «1 rotta su 2» NON e' un errore: e' **il confine stesso**, e
      si stampa cosi'.
    """
    buone = [c for c in celle if c.get("esito") == "misurato"]
    u = {"cella": nome, "etichetta": nome, "chiesto_pc": chiesto_pc,
         "giri": len(celle), "giri_validi": len(buone), "dettaglio": celle}
    if not buone:
        u["esito"] = ("NON HO NIENTE DA GIUDICARE — nessuno dei %d giri di "
                      "questa casella ha misurato" % len(celle))
        return u
    def med(ch):
        v = [c.get(ch) for c in buone if c.get(ch) is not None]
        return round(statistics.median(v), 3) if v else None
    u["esito"] = "misurato"
    for ch in ("vera_pc", "fps", "fps_min", "chiavi", "quota_delta",
               "copertura", "buco_max_s", "cpu_pc", "non_spediti"):
        u[ch] = med(ch)
    u["fps_giri"] = [c.get("fps") for c in buone]
    u["chiavi_giri"] = [c.get("chiavi") for c in buone]
    u["vera_giri"] = [c.get("vera_pc") for c in buone]
    _, _, u["dispersione_fps"] = dispersione(u["fps_giri"])
    # ⭐ Quante rotte su quante, per ciascuno dei due criteri: e' l'incertezza
    #   della casella, ed e' l'unica cosa onesta da scrivere accanto a una
    #   mediana presa su due o tre giri.
    u["rotte"] = {come: sum(1 for c in buone if criterio(c))
                  for come, criterio in CRITERI}
    return u


def passo_ripetibilita(a):
    """⛔⛔ **1 · LA RIPETIBILITA' PRIMA DELLA GRIGLIA** (⇒ §in testa)."""
    nome0, reg0, ver0 = casella(0.0)
    nome5, reg5, ver5 = casella(0.5)
    fuori = {"passo": "ripetibilita", "quando": time.strftime("%F %T"),
             "secondi": a.secondi, "giri": a.giri, "albero": ALB,
             "md5": impronta_binario(), "gruppi": {}}
    fuori["gruppi"][nome0] = misura_gruppo(nome0, reg0, ver0, a.secondi, a.giri)
    fuori["gruppi"][nome5] = misura_gruppo(nome5, reg5, ver5, a.secondi, a.giri)
    return fuori


def giudica_ripetibilita(d):
    """⛔ Il METRO, e si scrive PRIMA di guardare qualunque altra cosa."""
    rossi, muti = [], []
    rumore = {}
    _log("⭐⭐ LA DISPERSIONE FRA GIRI IDENTICI — il METRO di tutto il resto")
    for nome, celle in d["gruppi"].items():
        stampa_griglia("«%s» · %d giri identici" % (nome, len(celle)), celle)
        v = valori(celle, "fps")
        passa, perche = p_ripetibile(nome, v)
        (_ok if passa else (_dub if passa is None else _ko))(
            "R · %s" % perche)
        if passa is False:
            rossi.append("R · %s" % nome)
        elif passa is None:
            muti.append("R · %s — %s" % (nome, perche[:90]))
        med, semi, fraz = dispersione(v)
        rumore[nome] = fraz
        # ⭐ E la dispersione delle CHIAVI accanto a quella dei fotogrammi: se il
        #   ritmo fosse stabile e le chiavi no, il profilo sarebbe instabile
        #   nel MECCANISMO prima che nel sintomo.
        vk = valori(celle, "chiavi")
        _inf("chiavi nei %d giri: %s" % (len(vk), vk))
        _inf("cpu occupata nei giri: %s %%" % valori(celle, "cpu_pc"))
        _inf("perdita VERA nei giri: %s %%" % valori(celle, "vera_pc"))

    # ── S · il predicato per cui questo banco esiste ────────────────────────
    _log("S · ⭐⭐ IL RUMORE SPIEGA LA CONTRADDIZIONE DEL 23 AGOSTO?")
    for nome, fraz in rumore.items():
        chiave = "perdita-0,5" if "0,50" in nome else "ritardo"
        passa, perche = p_rumore_spiega(nome, fraz, CONTRADDIZIONE[chiave])
        (_ok if passa else (_dub if passa is None else _ko))("S · %s" % perche)
        if passa is False:
            rossi.append("S · %s — il rumore spiega la contraddizione" % nome)
        elif passa is None:
            muti.append("S · %s — %s" % (nome, perche[:90]))
    return rumore, rossi, muti


def passo_griglia(a):
    """⛔ **2 · LA GRIGLIA FINE** — e il denominatore si gira DUE volte, in
       apertura e in chiusura (⇒ §«QUEL CHE QUESTO BANCO AGGIUNGE», punto 3)."""
    fuori = {"passo": "griglia", "quando": time.strftime("%F %T"),
             "secondi": a.secondi, "albero": ALB, "marca": a.marca,
             "md5": impronta_binario(), "scala": SCALA, "celle": [],
             "apertura": [], "chiusura": []}
    nome0, reg0, ver0 = casella(0.0)
    fuori["giri_per_casella"] = a.giri
    fuori["apertura"] = misura_gruppo(nome0, reg0, ver0, a.secondi, a.giri,
                                      marca="APERTURA")
    for chiesto in SCALA:
        nome, reg, ver = casella(chiesto)
        if chiesto == 0.0:
            # ⭐ Lo zero della scala E' il gruppo d'apertura: non si gira due
            #   volte per finta.
            fuori["celle"].append(unisci(fuori["apertura"], nome, 0.0))
            continue
        fuori["celle"].append(
            unisci(misura_gruppo(nome, reg, ver, a.secondi, a.giri),
                   nome, chiesto))
    fuori["chiusura"] = misura_gruppo(nome0, reg0, ver0, a.secondi, a.giri,
                                      marca="CHIUSURA")
    return fuori


def giudica_griglia(d, rumore):
    rossi, muti = [], []
    stampa_griglia("⭐ LA GRIGLIA FINE — la perdita e' quella VERA, letta dalla "
                   "sonda a ogni casella", d["celle"])
    _log("⚠ L'INCERTEZZA DI OGNI CASELLA — quanti giri su quanti erano rotti")
    for c in d["celle"]:
        if c.get("esito") != "misurato":
            continue
        _inf("%-14s VERA %6s %%  fps %s (dispersione %s)  chiavi %s  ⇒ %s"
             % (c["cella"], c["vera_pc"], c["fps_giri"],
                ("%.1f %%" % (c["dispersione_fps"] * 100))
                if c.get("dispersione_fps") is not None else "?",
                c["chiavi_giri"],
                " · ".join("%s: %d/%d rotte" % (come.split("(")[0].strip()[:22],
                                                n, c["giri_validi"])
                           for come, n in c["rotte"].items())))

    # ── U · il denominatore regge? ─────────────────────────────────────────
    _log("U · IL DENOMINATORE HA RETTO PER TUTTA LA GRIGLIA?")
    passa, perche = p_due_gruppi_uguali(
        "zero d'apertura", valori(d["apertura"], "fps"),
        "zero di chiusura", valori(d["chiusura"], "fps"),
        metro(rumore.get(casella(0.0)[0])), "IL DENOMINATORE")
    (_ok if passa else (_dub if passa is None else _ko))("U · %s" % perche)
    if passa is False:
        rossi.append("U · il denominatore e' derivato durante la griglia: ogni "
                     "gradino di questa scala puo' essere la deriva")
    elif passa is None:
        muti.append("U · il denominatore — %s" % perche[:90])

    # ── G · dove sta il gradino, secondo i DUE criteri ──────────────────────
    _log("G · ⭐⭐ DOVE STA IL GRADINO — e i criteri sono DUE")
    forbici = {}
    for come_si_chiama, criterio in CRITERI:
        passa, perche = p_gradino_bracchettato(d["celle"], criterio,
                                               come_si_chiama)
        (_ok if passa else (_dub if passa is None else _ko))("G · %s" % perche)
        forbici[come_si_chiama] = (passa, perche)
        if passa is False:
            rossi.append("G · %s — non e' un gradino" % come_si_chiama)
        elif passa is None:
            muti.append("G · %s — %s" % (come_si_chiama, perche[:90]))
    return forbici, rossi, muti


def impronta_binario():
    try:
        rc, out, _ = RETE.rem("md5sum %s/src/remotix" % ALB, 60)
        return out.strip().split()[0] if out.strip() else None
    except Exception:
        return None


def con_lucchetto(quanti_giri, secondi, attesa, lavoro):
    """⛔⛔ IL LUCCHETTO — il `netem` su `lo` e' UNO SOLO per tutta la macchina.

    Chi non ce la fa si FERMA, non misura lo stesso: un altro banco che guasta
    la stessa `lo` non da' un rosso, da' **un numero plausibile e falso**
    (`LEZIONI.md` §1.26).
    """
    try:
        LUC.prendi(CHI, secondi=AFFITTO, attesa=attesa)
    except Exception as e:
        _ko("⛔ NON MISURO: %s" % e)
        return None
    SCADENZA[0] = time.time() + AFFITTO
    RETE.guardiano_arma(min(7200, quanti_giri * (secondi + 140) + 900))
    try:
        _inf("apro una sessione corta per far nascere il palco e il monitor")
        if not B70.innesca_sessione():
            _ko("la sessione non si apre: non misuro")
            return None
        return lavoro()
    finally:
        # ⛔ Il `finally`, e non e' una precauzione: se salto di qui con una
        #    `netem` addosso, la macchina resta guasta per tutti gli altri.
        B76.scena_spegni()
        _log("⛔ LA RETE SI RIMETTE COM'ERA")
        if not RETE.rimetti():
            _ko("⛔ la rete NON e' tornata com'era: si rimette a mano con "
                "«rimetti»")
        LUC.molla(CHI)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "ripetibilita", "griglia", "binario",
                            "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca. Non tocca la macchina di prova")
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--giri", type=int, default=3,
                   help="quanti giri identici per gruppo (⛔ sotto i tre il "
                        "banco tace: due valori non sono una dispersione)")
    p.add_argument("--attesa", type=int, default=1800,
                   help="quanti secondi aspetto il lucchetto del netem")
    p.add_argument("--marca", default="",
                   help="il nome del binario in questa griglia (es. «51b5994»)")
    p.add_argument("--a", default="HEAD", help="binario: la marca del primo")
    p.add_argument("--b", default="51b5994", help="binario: la marca del secondo")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("serve un passo, oppure --certifica")

    os.makedirs(FUORI, exist_ok=True)
    importa()

    if a.passo in ("rimetti", "stato"):
        stato_macchina()
        _log("la rete della macchina di prova — dev «%s», porta %d" % (DEV, PORTA))
        return 0 if RETE.rimetti() else 2

    if a.passo == "terreno":
        ok = B76.spedisci_sonda()
        return 0 if (B70.terreno_controlla() and ok) else 2

    _log("09-b80 · IL DIRUPO — porta %d · dev «%s» · albero %s" % (PORTA, DEV, ALB))
    print("   ⛔ «%s» (ssh + la sessione dell'utente) NON si tocca" % VIETATA)
    print("   ⛔ le cure del prodotto restano SPENTE: questa griglia e' il "
          "DENOMINATORE")
    stato_macchina()
    _inf("impronta del binario: %s" % impronta_binario())
    if not apparecchia():
        return 2

    rossi, muti = [], []

    # ═══ 1 · LA RIPETIBILITA' ═════════════════════════════════════════════
    if a.passo == "ripetibilita":
        d = con_lucchetto(2 * a.giri, a.secondi, a.attesa,
                          lambda: passo_ripetibilita(a))
        if d is None:
            return 2
        salva("09-b80-ripetibilita%s.json" % (("-" + a.marca) if a.marca else ""), d)
        rumore, r, m = giudica_ripetibilita(d)
        rossi += r
        muti += m
        d["rumore"] = rumore
        salva("09-b80-ripetibilita%s.json" % (("-" + a.marca) if a.marca else ""), d)

    # ═══ 2 · LA GRIGLIA FINE ══════════════════════════════════════════════
    elif a.passo in ("griglia", "binario"):
        rip = leggi("09-b80-ripetibilita.json")
        rumore = {}
        if rip and rip.get("rumore"):
            # ⛔ Il metro NON e' uno solo: e' quello del profilo che si sta
            #    confrontando (⇒ `metro()`).  Un metro unico preso dal profilo
            #    piu' instabile assolverebbe una deriva vera del denominatore.
            rumore = rip["rumore"]
            _inf("⭐ il metro viene dal passo «ripetibilita» del %s: %s"
                 % (rip.get("quando"),
                    " · ".join("%s %s" % (k, ("%.1f %%" % (v * 100))
                                          if v is not None else "?")
                               for k, v in rumore.items())))
            _inf("⛔ e non scende mai sotto il %.0f %% (il rumore fra due giri "
                 "dichiarato da 09-b70)" % (METRO_MINIMO * 100))
        else:
            _dub("⚠ non trovo %s/09-b80-ripetibilita.json: la griglia si gira "
                 "lo stesso, ma i confronti che hanno bisogno del metro "
                 "TACERANNO" % FUORI)

        if a.passo == "griglia":
            d = con_lucchetto(len(SCALA) + 2, a.secondi, a.attesa,
                              lambda: passo_griglia(a))
            if d is None:
                return 2
            nome = "09-b80-griglia%s.json" % (("-" + a.marca) if a.marca else "")
            salva(nome, d)
            forbici, r, m = giudica_griglia(d, rumore)
            rossi += r
            muti += m
        else:
            # ═══ 3 · IL BINARIO — e si legge, non si rimisura ══════════════
            _log("U · ⭐ IL BINARIO C'ENTRA? — «%s» contro «%s»" % (a.a, a.b))
            da = leggi("09-b80-griglia-%s.json" % a.a)
            db = leggi("09-b80-griglia-%s.json" % a.b)
            if not da or not db:
                _ko("⛔ mi mancano le due griglie da confrontare: si girano con "
                    "«griglia --marca %s» e «griglia --marca %s»" % (a.a, a.b))
                return 2
            _inf("«%s» md5 %s · %s" % (a.a, da.get("md5"), da.get("quando")))
            _inf("«%s» md5 %s · %s" % (a.b, db.get("md5"), db.get("quando")))
            if da.get("md5") == db.get("md5"):
                _ko("⛔ I DUE BINARI HANNO LO STESSO md5: non sto confrontando "
                    "due binari, sto confrontando la stessa griglia due volte")
                return 2
            stampa_griglia("«%s»" % a.a, da["celle"])
            stampa_griglia("«%s»" % a.b, db["celle"])
            # ⛔ Il metro di ogni casella e' il rumore del profilo che le
            #    somiglia: lo ZERO col rumore dello zero, le caselle con perdita
            #    col rumore di `perdita-0,50`.  ⚠ Un metro solo per tutta la
            #    scala assolverebbe il binario dove la scala e' stabile, e lo
            #    accuserebbe dove non lo e'.
            nome0, nome5 = casella(0.0)[0], casella(0.5)[0]
            for chiesto in SCALA:
                nome = casella(chiesto)[0]
                ca = [c for c in da["celle"] if c["cella"] == nome]
                cb = [c for c in db["celle"] if c["cella"] == nome]
                # ⭐ E si confrontano i GIRI, non le mediane: due mediane
                #   confrontate perdono per strada l'unica cosa che dice se la
                #   differenza conti.
                va = sum((c.get("fps_giri") or [c.get("fps")] for c in ca), [])
                vb = sum((c.get("fps_giri") or [c.get("fps")] for c in cb), [])
                passa, perche = p_due_gruppi_uguali(
                    a.a, va, a.b, vb,
                    metro(rumore.get(nome0 if chiesto == 0 else nome5)),
                    "IL BINARIO su «%s»" % nome)
                (_ok if passa else (_dub if passa is None else _ko))(
                    "U · %s" % perche)
                if passa is False:
                    rossi.append("U · il binario conta su «%s»" % nome)
                elif passa is None:
                    muti.append("U · «%s» — %s" % (nome, perche[:90]))
            for come, criterio in CRITERI:
                for etich, d2 in ((a.a, da), (a.b, db)):
                    passa, perche = p_gradino_bracchettato(d2["celle"], criterio,
                                                           come)
                    (_ok if passa else (_dub if passa is None else _ko))(
                        "G · [%s] %s" % (etich, perche))

    _log("IL VERDETTO — %d rossi · %d non giudicati" % (len(rossi), len(muti)))
    for r in rossi:
        _ko(r)
    for m in muti:
        _dub(m)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ tutti i predicati hanno fatto quel che era scritto prima")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
