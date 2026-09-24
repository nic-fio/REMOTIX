#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c24 — ⭐⭐ «"ESCI" CHIUDE LA SESSIONE, SEMPRE — non 19 volte su 20»
===========================================================================

    python3 11-c24-l-esci-chiude-sempre.py --porta 8514              # 10 giri
    python3 11-c24-l-esci-chiude-sempre.py --porta 8514 --giri 20
    python3 11-c24-l-esci-chiude-sempre.py --porta 8514 --rientra-subito
    python3 11-c24-l-esci-chiude-sempre.py --certifica

    che cosa deve essere vero : l'utente sceglie «Esci» dal menu del desktop
                                ⇒ la sessione FINISCE e ⛔ NON RINASCE da sola
                                — ogni volta, qualunque sia il momento in cui
                                l'utente lo sceglie
    da dove parte             : per ogni giro un inquilino NUOVO (`c24u<n>`),
                                il cliente Python che guarda, la nascita fatta
                                dal figlio, K secondi di sessione, e il gesto
                                «Esci» del MENU (la tavola `DESKTOP_E_GESTO`
                                di C20, ⛔ importata e non copiata)
    che cosa guarda           : il REGISTRO DEL PRODOTTO e il CLIENTE, per T
                                secondi dopo il gesto
      F  finita    il prodotto dichiara la sessione finita (una delle due
                   forme di C20, `RIGHE_FINITA`) o il cliente e' congedato
                   con 0x10
      N  nascita   ⛔ per QUESTO inquilino, dopo il gesto, NON compare «LA
                   FACCIO NASCERE» ne' un secondo «formato negoziato»
    come so che sa dare rosso : `--rientra-subito` (vedi il riquadro del
                                guasto): dopo «Esci» si riattacca un cliente
                                per lo stesso inquilino ⇒ una sessione NASCE
                                davvero dentro la finestra di T secondi, e la
                                maglia DEVE dire rosso

---------------------------------------------------------------------------
⛔⛔ IL DIFETTO CHE QUESTA MAGLIA SORVEGLIA — 24 settembre 2026
---------------------------------------------------------------------------

Su LXQt «Esci» faceva RINASCERE la sessione invece di chiuderla.  `[M]` 16
volte su 20 col binario di ieri, **1 su 20** con quello di stamattina: e' una
GARA, e l'esito dipende dal momento in cui l'utente sceglie «Esci».

`[R]` `src/figlio.c`, «C'ERA E ADESSO NON C'E' PIU'»: il figlio distingue una
sessione che non c'e' MAI stata (⇒ la fa nascere) da una che c'era e l'utente
ha chiuso (⇒ ⛔ NON la rifa', congeda chi guarda con 0x10).  La distinzione
sta tutta in `vista_viva`: se la sessione muore PRIMA che il figlio l'abbia
vista viva, per lui «non c'e' mai stata», e scrive «LA FACCIO NASCERE».
⇒ E' una finestra di tempo, e il gesto dell'utente puo' caderci dentro.

⛔⛔ E PERCHE' C20 NON BASTAVA: C20 fa «Esci» **UNA** volta per scatola, sempre
    allo stesso momento.  Una gara da 1 su 20 le passa accanto 19 volte su 20
    ⇒ la rete era verde col difetto dentro.  ⭐ Qui i giri sono N (predefinito
    10) e il momento del gesto CAMBIA a ogni giro (`ATTESE_K`: 8, 10, 12, 15 s
    a rotazione), perche' la finestra della gara e' nel TEMPO.
⚠ 10 giri non sono una garanzia contro una gara da 1 su 20 (la prende con
  probabilita' ~40%): sono il tetto di tempo della rete (5 minuti per
  scatola).  ⭐ Per una caccia vera: `--giri 40`.  E la gara di IERI (16 su 20)
  10 giri la prendono con certezza pratica.

---------------------------------------------------------------------------
⛔⛔ IL GUASTO INNESTATO — e perche' NON e' «uccidere il compositore»
---------------------------------------------------------------------------

La prima idea era: invece del gesto, SIGKILL al compositore dell'inquilino
⇒ il palco cade senza che l'utente abbia chiuso ⇒ «deve rinascere».
⛔ **E' sbagliata, ed e' il prodotto a dirlo.**  `src/figlio.c`, nello stesso
riquadro «C'ERA E ADESSO NON C'E' PIU'»:

    «⚠ E lo stesso vale se il compositore e' MORTO da solo: dal nostro lato
     e' indistinguibile da un logout, e il comportamento giusto e' lo stesso
     — dirlo a chi guarda invece di far ricomparire un desktop che l'utente
     aveva chiuso.»

⇒ Col compositore ucciso il prodotto SANO **non** rinasce: la maglia direbbe
  verde, e il guasto innestato «non visto» accuserebbe la maglia di un
  comportamento che e' una decisione del prodotto.  Un guasto che il prodotto
  sano non puo' produrre non prova niente.

⭐ Il guasto scelto: `--rientra-subito`.  Il giro e' identico (gesto «Esci»
  vero, stessa attesa K), e appena il prodotto ha dichiarato la sessione
  finita la maglia RIATTACCA un secondo cliente per lo stesso inquilino.  Per
  il prodotto e' un attacco nuovo ⇒ fa nascere una sessione (e fa bene:
  `DECISIONI.md` §4.1-quater, «la prossima nasce al prossimo attacco») ⇒ nel
  registro, per quell'inquilino e dentro la finestra di T secondi, compaiono
  **esattamente le righe del difetto**: «LA FACCIO NASCERE» e un secondo
  «formato negoziato».
  ⚠ Che cosa prova e che cosa no, detto chiaro: prova che il giudice LEGGE la
    rinascita dopo «Esci» e la chiama rosso.  Non prova che sappia distinguere
    una rinascita spontanea da una chiesta — ⭐ e non deve saperlo: nel giro
    sano la maglia non riattacca MAI dentro la finestra, ⇒ ogni nascita che vi
    compare e' del prodotto.
  ⚠ E non ricompila niente: il difetto vero sta in una variabile del figlio, e
    da fuori non lo si rimette.

---------------------------------------------------------------------------
⚠ I NUMERI, e da dove vengono
---------------------------------------------------------------------------

  · **T = 10 s** di guardia dopo il gesto.  `[M]` 24 set 2026 su rete11-lxqt
    (binario 6e29da97, senza la cura): la rinascita compare entro pochi
    secondi dal gesto — il figlio legge lo stato della sessione a ogni
    tentativo di palco, e al primo che la trova MORTA la fa nascere.
    ⚠ Da rimisurare se la cadenza dei tentativi cambia.
  · **tetto della nascita 60 s**: e' l'inizio di ogni giro, e se non nasce la
    maglia non ha niente da giudicare ⇒ 3.
  · ⛔ **5 minuti per scatola** e' il tetto della rete: `durata_prevista()` lo
    calcola PRIMA di partire e lo stampa, e dopo stampa quel che e' durato.

---------------------------------------------------------------------------
⭐ LE MISURE CHE LA TENGONO IN PIEDI — 25 settembre 2026 (fase 15, G10)
---------------------------------------------------------------------------

  · binario ATTUALE 7dfd6a96, pagina 87268f13, 10 giri:
      rete11-lxqt  VERDE 10 su 10 (234 s) · rete11-xfce  VERDE 10 su 10 (236 s)
  · ⛔ CONTROPROVA col binario VECCHIO 6e29da97 (senza la cura 43345ea), sulla
    scatola di sviluppo rete15-lxqt (8534, stessa immagine lxqt c9f631cb,
    accesa apposta e rispenta): ROSSO — rinata 6 volte su 10 (5 al secondo
    accesso, 1 al primo; un giro «?»), 265 s.
  · guasto innestato `--rientra-subito` su rete11-lxqt, binario attuale:
    VISTO, rinata 2 su 2 (45 s).
  ⚠ Sulle scatole condivise la maglia gira da una copia in /tmp della scatola
    (il cliente e C20 si cercano anche in /opt/remotix): ⛔ /opt/remotix e'
    il prodotto, e non lo si tocca per far girare un banco.

Esiti: 0 verde (N su N) · 1 rosso (anche UNA rinascita) · 3 non ho potuto
guardare (⛔ NON e' un rosso).
⛔ Con `--rientra-subito` si legge AL CONTRARIO: 0 = il guasto e' VISTO.
"""
import argparse
import importlib.util
import os
import random
import re
import signal
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
# ⚠ Il cliente si cerca come C20 e C1: accanto a me, poi dove la scatola li
#   mette (`/opt/remotix`).  Cosi' la maglia gira anche da una copia fuori da
#   `/opt/remotix` (⛔ il prodotto delle scatole condivise non si tocca).
CLIENTE = next((os.path.join(b, "01-b3-cliente.py")
                for b in (QUI, os.path.dirname(QUI), "/opt/remotix", "/rete11/prodotto")
                if os.path.exists(os.path.join(b, "01-b3-cliente.py"))),
               os.path.join(QUI, "01-b3-cliente.py"))
REGISTRO = "/var/lib/rete11/registro.log"
PAROLA = "provanic2026"


def _carica(nome_file):
    """⭐ C20 e C1 si IMPORTANO: la tavola dei gesti, le righe della fine, lo
    sgombero e i gruppi della scheda stanno la', e una copia qui sarebbe un
    posto in piu' da cui divergere (§1.47)."""
    for base in (QUI, os.path.dirname(QUI), "/opt/remotix", "/rete11"):
        perc = os.path.join(base, nome_file)
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location(
            "importato_" + re.sub(r"\W", "_", nome_file), perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        return m
    return None


C20 = _carica("11-c20-la-rinascita-non-porta-fantasmi.py")

# ⭐ Le righe del prodotto che questa maglia legge, in un posto solo.
#   ⛔ La NASCITA si riconosce in due modi, e bastano tutt'e due da soli:
#     «LA FACCIO NASCERE»  il figlio decide di farla nascere  src/figlio.c
#     «formato negoziato»  la cattura e' partita             src/cattura.c
#   ⇒ Dopo il gesto nessuna delle due deve comparire per questo inquilino.
RIGA_FACCIO_NASCERE = "LA FACCIO NASCERE"
RIGA_NASCITA = "formato negoziato"
# ⭐ Il congedo come lo stampa il cliente (`01-b3-cliente.py`, «sessione chiusa
#   dal server, codice 0x10»).  E' il secondo testimone della fine: quello che
#   vede chi GUARDA, non quel che il prodotto racconta di se'.
RIGA_CONGEDO = re.compile(r"codice 0x10\b")

# ⭐ Il momento del gesto CAMBIA a ogni giro.
ATTESE_K = (8.0, 10.0, 12.0, 15.0)
GUARDIA_T = 10.0
TETTO_NASCITA = 60.0
TETTO_SCATOLA = 300.0
# ⭐ Quanti «Esci» di fila fa ogni inquilino (vedi `un_inquilino`).
ACCESSI = 2
# ⚠ Quel che costa oltre a K e T, `[M]` 24 set 2026 sulle quattro scatole:
#   un accesso (nascita + attesa che il cliente congedato se ne vada) e un
#   inquilino (creazione, gruppi, sgombero).  Servono SOLO a dichiarare la
#   durata prima di partire: i tetti veri sono TETTO_NASCITA e i 15 s
#   dell'uscita del cliente.
SPESA_ACCESSO = 3.0
SPESA_INQUILINO = 3.0


def attesa_del_giro(n, attese=None):
    """⭐ K del giro n (da 0): a rotazione su `ATTESE_K`."""
    attese = attese or ATTESE_K
    return attese[n % len(attese)]


def durata_prevista(giri, guardia=GUARDIA_T, accessi=ACCESSI, attese=None,
                    spesa_accesso=SPESA_ACCESSO,
                    spesa_inquilino=SPESA_INQUILINO):
    """⭐ I secondi di N giri («Esci»), dichiarati prima di partire — pura."""
    inquilini = -(-giri // max(1, accessi))
    return (sum(spesa_accesso + attesa_del_giro(n, attese) + guardia
                for n in range(giri)) + inquilini * spesa_inquilino)


def e_di(riga, chi):
    """⚠ Il nome sta fra parentesi quadre nelle righe marcate per inquilino, e
    fra virgolette basse in quelle del padre e nella «LA FACCIO NASCERE»."""
    return ("[%s]" % chi) in riga or ("«%s»" % chi) in riga


def righe_finita():
    """Le due forme della fine, da C20 — o quelle scritte qui se C20 manca
    (e allora `main()` esce 3 prima di usarle)."""
    if C20 is not None:
        return [p for p, _d in C20.RIGHE_FINITA]
    return []


def giudica_il_giro(fetta, chi, detto_dal_cliente, finite=None):
    """⭐ (esito, perche) di UN giro, dalle righe di registro scritte DOPO il
    gesto e da quel che ha stampato il cliente — pura.

      · una NASCITA per questo inquilino dopo il gesto     ⇒ 1, ROSSO
      · la fine dichiarata (registro) o il congedo 0x10     ⇒ 0, VERDE
      · ne' l'una ne' l'altra                               ⇒ 3

    ⛔ La nascita si guarda PRIMA della fine: nel difetto misurato le due
       possono esserci tutt'e due (il prodotto dice «e' finita» e poi, al
       tentativo dopo, «la faccio nascere»), e un verde letto sulla prima
       riga sarebbe proprio il difetto che passa.
    """
    if finite is None:
        finite = righe_finita()
    if fetta is None:
        return 3, "non ho potuto leggere il registro del server"
    mie = [r for r in fetta if e_di(r, chi)]
    nascite = [r for r in mie
               if RIGA_FACCIO_NASCERE in r or RIGA_NASCITA in r]
    if nascite:
        return 1, ("dopo «Esci» la sessione di «%s» RINASCE (%d righe; la "
                   "prima: %s)" % (chi, len(nascite), nascite[0].strip()[:110]))
    finita = next((p for p in finite if any(p in r for r in mie)), None)
    congedo = bool(RIGA_CONGEDO.search(detto_dal_cliente or ""))
    if finita or congedo:
        return 0, ("finita%s%s, e nessuna nascita dopo"
                   % ((" («%s»)" % finita) if finita else "",
                      " · il cliente congedato con 0x10" if congedo else ""))
    return 3, ("dopo «Esci» il prodotto non ha dichiarato la sessione finita, "
               "il cliente non e' stato congedato, e non e' rinata: non so "
               "che cosa sia successo")


def esito_dei_giri(esiti):
    """⭐ L'esito della maglia dagli esiti dei giri — pura.

    ⛔ Anche UNA rinascita e' rosso: la gara si prende una volta su venti, e
       chiederne due sarebbe chiedere alla gara di farsi vedere due volte.
    ⚠ Un 3 non diventa verde: se un giro non ha potuto guardare, N su N non
      c'e' ⇒ 3 (salvo un rosso, che resta rosso: una rinascita VISTA vale piu'
      di un giro non guardato).
    """
    if not esiti:
        return 3
    if 1 in esiti:
        return 1
    if 3 in esiti:
        return 3
    return 0


def esito_col_guasto(esito):
    """⛔ Col guasto innestato si legge al contrario — pura."""
    return {1: 0, 0: 1}.get(esito, 3)


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    guai = 0

    def p(nome, ottenuto, atteso):
        nonlocal guai
        if ottenuto != atteso:
            guai += 1
        print("  %s %-66s %s (atteso %s)"
              % ("OK " if ottenuto == atteso else "NO ", nome, ottenuto, atteso))

    print("== C24 — certificazione dei giudizi (⛔ senza toccare la macchina)")
    fin = ["E' FINITA", "se n'e' andato ⇒ la sessione grafica e' finita"]
    finita_f = ["figlio  ⭐ §7.6: la sessione grafica di «c24u1» E' FINITA "
                "(nessun client l'ha chiesta)"]
    finita_p = ["padre  ⭐ §7.6: il palco di «c24u1» se n'e' andato ⇒ la "
                "sessione grafica e' finita: congedati 1 client con 0x10"]
    rinasce = ["figlio  [c24u1] ⭐ nessuna sessione grafica per «c24u1»: LA "
               "FACCIO NASCERE io (tela 1920x1080)"]
    negozia = ["cattura [c24u1] ⭐ formato negoziato: 1920x1080 BGRx"]
    congedo = "   [wt]   sessione chiusa dal server, codice 0x10 = ?"
    g = lambda f, c="": giudica_il_giro(f, "c24u1", c, fin)[0]
    p("⭐ finita (il figlio lo dice) ⇒ VERDE", g(finita_f), 0)
    p("⭐ finita (lo dice il padre, GNOME) ⇒ VERDE", g(finita_p), 0)
    p("⭐ niente nel registro ma il cliente congedato 0x10 ⇒ VERDE",
      g([], congedo), 0)
    p("⛔ finita E poi «LA FACCIO NASCERE» ⇒ ROSSO", g(finita_f + rinasce), 1)
    p("⛔ finita E poi un secondo «formato negoziato» ⇒ ROSSO",
      g(finita_p + negozia, congedo), 1)
    p("⛔ rinasce senza mai dire finita ⇒ ROSSO", g(rinasce), 1)
    p("⚠ la rinascita e' di un ALTRO inquilino ⇒ VERDE per questo",
      g(finita_f + [r.replace("c24u1", "c24u9") for r in rinasce]), 0)
    p("⚠ «c24u1» non e' «c24u10» ⇒ la rinascita di c24u10 non conta",
      g(finita_f + [r.replace("c24u1", "c24u10") for r in rinasce]), 0)
    p("⚠ niente di niente ⇒ 3, ⛔ mai un verde", g([]), 3)
    p("⚠ il registro non si legge ⇒ 3", g(None), 3)
    p("⚠ un codice 0x100 non e' 0x10 ⇒ 3",
      g([], "sessione chiusa dal server, codice 0x100"), 3)

    p("⭐ 10 verdi ⇒ 0", esito_dei_giri([0] * 10), 0)
    p("⛔ 9 verdi e UNA rinascita ⇒ 1", esito_dei_giri([0] * 9 + [1]), 1)
    p("⚠ 9 verdi e un 3 ⇒ 3, ⛔ non un verde", esito_dei_giri([0] * 9 + [3]), 3)
    p("⛔ un rosso e un 3 ⇒ 1: la rinascita vista resta",
      esito_dei_giri([3, 1, 0]), 1)
    p("⚠ nessun giro ⇒ 3", esito_dei_giri([]), 3)
    p("⛔ guasto visto (1) ⇒ 0", esito_col_guasto(1), 0)
    p("⛔ guasto NON visto (0) ⇒ 1", esito_col_guasto(0), 1)
    p("⚠ guasto non guardato (3) ⇒ 3", esito_col_guasto(3), 3)

    p("⭐ K a rotazione: 8, 10, 12, 15, 8",
      [attesa_del_giro(n) for n in range(5)], [8.0, 10.0, 12.0, 15.0, 8.0])
    p("⭐ 10 giri a 2 accessi sono 5 inquilini", -(-10 // ACCESSI), 5)
    p("⛔ 10 giri stanno nel tetto di %d s" % TETTO_SCATOLA,
      durata_prevista(10) <= TETTO_SCATOLA, True)
    p("⭐ C20 si importa, e la sua tavola ha i quattro desktop",
      (C20 is not None and len(C20.DESKTOP_E_GESTO) == 4), True)
    p("⭐ e le due forme della fine vengono da C20", len(righe_finita()), 2)
    print()
    if guai:
        print("⛔ %d casi NON danno quel che devono" % guai)
        return 1
    print("⭐ il giudice dice verde, rosso e «non lo so» dove deve — e ⛔ una "
          "rinascita dopo\n   la fine dichiarata e' rosso, non verde")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def attacca(porta, chi, resta, uscita, tela=(1920, 1080)):
    """⭐ Il cliente Python che guarda: un processo nostro, che si ferma col
    suo `Popen` (⛔ niente `pkill -f` col nome: pescherebbe se stesso)."""
    f = open(uscita, "w")
    return subprocess.Popen(
        ["python3", "-u", CLIENTE, "--indirizzo", "127.0.0.1", "--porta",
         str(porta), "--utente", chi, "--parola", PAROLA, "--resta",
         str(resta), "--larghezza", str(tela[0]), "--altezza", str(tela[1])],
        stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT,
        start_new_session=True)


def ferma(proc):
    if proc is None:
        return
    try:
        proc.kill()
        proc.wait(10)
    except (OSError, subprocess.TimeoutExpired):
        pass


def leggi_testo(percorso):
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def un_accesso(i, k, chi, a, gesto, desktop, dove, clienti):
    """⭐ (esito, perche) di UN accesso: attacco, nascita, K secondi, «Esci»,
    T secondi di guardia."""
    uscita = os.path.join(dove, "%s-%d.txt" % (chi, i))
    righe = C20.leggi(a.registro)
    segno = len(righe) if righe is not None else 0
    cli = attacca(a.porta, chi, TETTO_NASCITA + k + a.guardia + 30, uscita,
                  a.tela)
    clienti.append(cli)
    nato, _ = C20.aspetta_la_riga(a.registro, segno, chi, RIGA_NASCITA,
                                  TETTO_NASCITA)
    if not nato:
        return 3, ("in %d s la sessione di %s (accesso %d) non e' nata: %s"
                   % (TETTO_NASCITA, chi, i + 1, C20.coda_di(uscita)))

    # ── K secondi di sessione, poi «Esci» dal menu ────────────────────────
    time.sleep(k)
    righe = C20.leggi(a.registro)
    segno = len(righe) if righe is not None else 0
    rtd, _ = C20.il_socket_di(chi)
    t_gesto = time.time()
    r = C20.sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s "
               "DBUS_SESSION_BUS_ADDRESS=unix:path=%s/bus %s"
               % (chi, rtd, rtd, gesto), 20)
    if r is None or r.returncode != 0:
        return 3, ("il gesto «Esci» di %s non ha risposto: %s"
                   % (desktop, ((r.stderr or r.stdout).strip()
                                .replace("\n", " ")[:100]) if r else
                      "nessuna risposta"))

    # ── T secondi di guardia (⛔ tutti: il verde e' un'ASSENZA) ───────────
    #    ⛔ Col guasto innestato, appena la fine e' dichiarata si riattacca
    #       un cliente per lo stesso inquilino, DENTRO la finestra.
    if a.rientra_subito:
        finita, _ = C20.aspetta_la_riga(a.registro, segno, chi,
                                        righe_finita(), a.guardia - 2)
        if finita:
            clienti.append(attacca(a.porta, chi, a.guardia + 10,
                                   uscita + ".guasto", a.tela))
            print("      ⛔ guasto innestato: fine dichiarata, riattacco %s "
                  "dopo %.1f s" % (chi, time.time() - t_gesto))
    resto = a.guardia - (time.time() - t_gesto)
    if resto > 0:
        time.sleep(resto)
    fetta = C20.leggi(a.registro)
    fetta = fetta[segno:] if fetta is not None else None
    return giudica_il_giro(fetta, chi, leggi_testo(uscita))


def un_inquilino(primo, quanti, a, gesto, desktop, dove):
    """⭐ [(esito, perche, secondi)] di UN inquilino nuovo, che fa `quanti`
    «Esci» di fila — i giri `primo`, `primo+1`, … della maglia.

    ⛔⛔ E GLI ACCESSI PER INQUILINO SONO DUE, e il secondo e' quello che conta
        di piu' — `[M]` 24 set 2026 su rete11-lxqt (binario senza la cura):
        con UN accesso per inquilino **16 «Esci» su 16 verdi**; con due,
        **5 rinascite su 5 inquilini** (4 al secondo accesso, 1 al primo).
        Il primo accesso nasce in un figlio NUOVO; il secondo nasce nel figlio
        SOPRAVVISSUTO all'«Esci» di prima — l'utente che esce e rientra — ed
        e' li' che il montaggio legge la sessione MORTA e lascia spenta «vista
        viva» (il riquadro in testa).
    ⚠ Dopo un giro non verde l'inquilino si lascia: la sua sessione e' in uno
      stato che il giro dopo non saprebbe da dove prendere.
    """
    t0 = time.time()
    chi = "c24u%d" % random.randint(100, 999)
    clienti = []
    fuori = []
    try:
        C20.sgombera(chi)
        r = C20.sh("useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                   % (chi, chi, PAROLA), 60)
        if r is None or r.returncode != 0:
            return [(3, "non ho potuto creare l'inquilino %s" % chi,
                     time.time() - t0)]
        c1 = _carica("11-c1-nasce-e-si-vede.py")
        if c1 is None or not callable(getattr(c1, "garantisci_i_gruppi", None)):
            return [(3, "non trovo `11-c1-nasce-e-si-vede.py`: senza i gruppi "
                        "della scheda la sessione nasce cieca", time.time() - t0)]
        eg, perche_g = c1.garantisci_i_gruppi(chi, "      ")
        if eg != 0:
            return [(3, perche_g, time.time() - t0)]
        for i in range(quanti):
            k = attesa_del_giro(primo + i, a.attese)
            esito, perche = un_accesso(i, k, chi, a, gesto, desktop, dove,
                                       clienti)
            fuori.append((esito, "%s accesso %d · K=%.0f s · %s"
                          % (chi, i + 1, k, perche), time.time() - t0))
            t0 = time.time()
            if esito != 0:
                break
            # ⚠ Il cliente di prima e' stato congedato: si aspetta che se ne
            #   sia andato davvero, o il prossimo accesso arriva mentre il
            #   primo e' ancora dentro (C20, 23 set 2026).
            C20.aspetta_che_il_cliente_se_ne_vada(a.porta, chi, 15)
        return fuori
    finally:
        for c in clienti:
            ferma(c)
        C20.sgombera(chi)
        for f in os.listdir(dove):
            if f.startswith(chi + "-"):
                try:
                    os.unlink(os.path.join(dove, f))
                except OSError:
                    pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--giri", type=int, default=0,
                   help="quanti «Esci» (predefinito 10; 2 col guasto)")
    p.add_argument("--guardia", type=float, default=GUARDIA_T,
                   help="T: i secondi dopo il gesto in cui non deve nascere "
                        "niente")
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--accessi", type=int, default=2,
                   help="quanti «Esci» di fila per inquilino (il secondo nasce "
                        "nel figlio sopravvissuto al primo)")
    p.add_argument("--attese", default="",
                   help="K a rotazione, in secondi: «5,6,8,10»")
    p.add_argument("--tela", default="1920x1080",
                   help="la tela del cliente, LxA")
    p.add_argument("--rientra-subito", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: dopo la fine dichiarata si "
                        "riattacca un cliente ⇒ la sessione rinasce davvero "
                        "nella finestra, e la maglia DEVE dare rosso")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    try:
        a.tela = tuple(int(x) for x in a.tela.lower().split("x", 1))
        a.attese = tuple(float(x) for x in a.attese.split(",") if x.strip())
    except ValueError:
        print("⛔ `--tela` vuole LxA e `--attese` dei secondi ⇒ non ho potuto "
              "guardare")
        return 3
    # ⛔ Un SIGTERM (il `timeout` del gancio) deve passare dai `finally`: senza,
    #    l'inquilino del giro resta vivo nella scatola con la sua sessione —
    #    `[M]` 24 set 2026, rete11-xfce, un `c24u` rimasto dopo il tetto.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(3))
    if C20 is None:
        print("⛔ non trovo `11-c20-la-rinascita-non-porta-fantasmi.py` accanto "
              "a me: la tavola dei gesti «Esci» sta la' ⇒ non ho potuto guardare")
        return 3
    if not a.porta:
        print("⛔ vuole `--porta` ⇒ non ho potuto guardare")
        return 3
    if os.geteuid() != 0:
        print("⛔ vuole l'amministratore (crea gli inquilini) ⇒ non ho potuto "
              "guardare")
        return 3
    giri = a.giri or (2 if a.rientra_subito else 10)

    desktop, gesto = C20.come_si_esce()
    if desktop is None:
        print("⛔ %s ⇒ non ho potuto guardare" % gesto)
        return 3
    if C20.leggi(a.registro) is None:
        print("⛔ non leggo %s ⇒ non ho potuto guardare" % a.registro)
        return 3
    accessi = max(1, a.accessi)
    previsti = durata_prevista(giri, a.guardia, accessi, a.attese)
    print("== C24 — «Esci» chiude la sessione, sempre (%s, porta %d, %d giri)%s"
          % (desktop, a.porta, giri,
             " ⛔ GUASTO INNESTATO: --rientra-subito" if a.rientra_subito
             else ""))
    print("   «Esci» si dice cosi': %s" % gesto)
    print("   durata prevista: ~%.0f s (%d giri = %d inquilini × %d accessi; "
          "ogni giro %.0f s + K + T=%.0f s)%s"
          % (previsti, giri, -(-giri // accessi), accessi, SPESA_ACCESSO,
             a.guardia,
                  "" if previsti <= TETTO_SCATOLA else
                  "  ⚠ OLTRE il tetto di %.0f s della rete" % TETTO_SCATOLA))

    dove = "/tmp/c24.%d" % os.getpid()
    os.makedirs(dove, exist_ok=True)
    t0 = time.time()
    esiti = []
    try:
        while len(esiti) < giri:
            for e, perche, s in un_inquilino(len(esiti),
                                             min(accessi, giri - len(esiti)),
                                             a, gesto, desktop, dove):
                esiti.append(e)
                print("   giro %2d  %-5s %4.0f s  %s"
                      % (len(esiti), {0: "VERDE", 1: "ROSSO", 3: "?"}[e], s,
                         perche), flush=True)
    finally:
        # ⚠ Qui non si accende nessun browser ⇒ niente `/tmp/mozilla` da
        #   togliere: gli inquilini li ha gia' sgomberati ogni giro.
        try:
            os.rmdir(dove)
        except OSError:
            pass

    esito = esito_dei_giri(esiti)
    rinate, verdi = esiti.count(1), esiti.count(0)
    print()
    print("   durata: %.0f s (prevista ~%.0f s)" % (time.time() - t0, previsti))
    if a.rientra_subito:
        fuori = esito_col_guasto(esito)
        if fuori == 0:
            print("⭐ IL GUASTO INNESTATO E' STATO VISTO — rinata %d volte su "
                  "%d: questa maglia SA dare rosso" % (rinate, giri))
        elif fuori == 1:
            print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: la sessione e' "
                  "rinata davvero\n   (un attacco nuovo) e la maglia ha detto "
                  "verde")
        else:
            print("⚠ col guasto innestato NON ho potuto guardare ⇒ 3")
        return fuori
    if esito == 0:
        print("⭐ VERDE — «Esci» ha chiuso la sessione %d volte su %d, e non e' "
              "rinata" % (verdi, giri))
    elif esito == 1:
        print("⛔⛔ ROSSO — dopo «Esci» la sessione e' RINATA %d volte su %d"
              % (rinate, giri))
    else:
        print("⚠ non ho potuto guardare — %d giri su %d senza esito"
              % (esiti.count(3), giri))
    return esito


if __name__ == "__main__":
    sys.exit(main())
