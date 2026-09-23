#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c20 — ⭐⭐ «DOPO «ESCI» E UN NUOVO ACCESSO, LO SCHERMO NON LAMPEGGIA»
===========================================================================

    python3 11-c20-la-rinascita-non-porta-fantasmi.py --porta 8512
    python3 11-c20-la-rinascita-non-porta-fantasmi.py --porta 8512 --scena-che-lampeggia
    python3 11-c20-la-rinascita-non-porta-fantasmi.py --certifica

    che cosa deve essere vero : l'utente esce dal menu del desktop e rientra
                                ⇒ la sessione NUOVA si vede pulita: ⛔ niente
                                fantasmi della sessione morta
    da dove parte             : un inquilino nuovo, una sessione nata, il
                                gesto vero dell'utente («Esci» dal menu), e
                                nella sessione nuova ⭐ **una scena
                                DICHIARATA** (`11-c20-scena.html`): si muove,
                                e la sua luce non cambia
    che cosa guarda           : due giudici, e il primo non chiede niente al
                                prodotto
      P  pixel     il video del SECONDO accesso si decodifica, e la luminanza
                   media dei fotogrammi e' **UNA**.  Se alterna fra valori
                   lontani, e' il lampeggio.
      R  registro  dopo la rinascita il codificatore dice «butto le N
                   superfici importate» per QUESTO inquilino
    come so che sa dare rosso : `--scena-che-lampeggia` — al posto della scena
                                dichiarata si accende quella di **C3**, che
                                alterna il fondo fra blu (#0000FF) e giallo
                                (#FFFF00) ⇒ ⭐ la luminanza media salta di
                                ~197 livelli su 255, e il giudice dei PIXEL
                                **deve** dare rosso

---------------------------------------------------------------------------
⛔⛔ IL DIFETTO CHE QUESTA MAGLIA SORVEGLIA — 22 settembre 2026
---------------------------------------------------------------------------

La prova dell'utente su KDE con Chrome: dopo «Esci» e un nuovo accesso lo
schermo alternava TRE immagini — il desktop, la schermata d'uscita della
sessione di PRIMA, e il nero.

`[M]` La generazione dei buffer ripartiva da 0 con la cattura nuova, il
codificatore (che **resta** vivo) non buttava la sua cache, e i descrittori
riciclati ritrovavano le superfici della sessione morta.
`[R]` `src/codificatore.c`, `butta_le_importate()`: *«una superficie che
sopravvive al `pw_buffer` che descriveva punta a memoria di qualcun altro …
il sintomo sarebbe un'immagine VECCHIA, senza nessun errore»*.

⇒ ⛔⛔ **«Senza nessun errore»** e' la ragione per cui serve una maglia e non
  basta il registro: il prodotto non se ne accorge, il cliente non se ne
  accorge, e ⭐ **l'unico che se ne accorge e' chi GUARDA**.  Questa maglia
  guarda al posto suo.

---------------------------------------------------------------------------
⭐⭐ DA `13-w4` A C20 — che cosa e' cambiato, e perche'
---------------------------------------------------------------------------

Questa maglia nasce da `banchi/13-w4-rinascita-senza-fantasmi.sh` (22 set
2026), che ha trovato il difetto e l'ha misurato.  ⭐ Entrando nella rete ha
dovuto cambiare tre cose — e sono esattamente le tre che separano un banco
scritto per una sera da una maglia che gira da sola per mesi:

  1. ⛔⛔ **IL GUASTO INNESTATO, che non aveva.**  Senza, la maglia non prova
     niente: il giorno che il giudice dei pixel smettesse di guardare
     (un `ffmpeg` che cambia uscita, una soglia storta, un video vuoto letto
     come «fermo») ⭐ direbbe VERDE per sempre, e nessuno lo saprebbe.
     ⇒ `--scena-che-lampeggia` mette sullo schermo un lampeggio VERO e
       pretende il rosso.  §3.6 della fase 11: *«ogni prova della lista ha,
       obbligatoriamente, il suo guasto innestato, e quel caso va fatto
       girare, non immaginato»*.

  2. ⛔ **NON SA PIU' CHE COSA SIA PLASMA.**  `13-w4` aspettava `plasmashell`,
     chiedeva `org.kde.Shutdown.logout` e guardava morire `kwin_wayland`:
     tre nomi di UN desktop dentro la lista delle prove, che e' precisamente
     quel che questa rete non ammette (`fasi/11…` §3.7).
     ⇒ Adesso: la nascita si legge dal REGISTRO DEL PRODOTTO (`formato
       negoziato`, la stessa riga di C1), la fine pure — ⚠ e in DUE forme,
       perche' il prodotto ne ha due e quale delle due esca dipende da chi
       muore col gesto (vedi `RIGHE_FINITA` e `giudica_il_registro`) — ⭐ e
       il gesto «Esci» si
       CHIEDE ALLA MACCHINA invece di indovinarlo — con la stessa domanda che
       fa il prodotto (`src/sessione.c:285-310`: c'e' `startplasma-wayland`?
       c'e' `gnome-session`? c'e' `xfce4-session`?).

  3. ⛔ **L'INQUILINO HA UN NOME DELLA RETE.**  `13-w4` lo chiamava `w4u$$`:
     fuori dallo spazio di nomi `c<n>[b]u<n>`, quindi ⛔ **il gancio non lo
     sgomberava** e C19 non lo vedeva.  ⇒ Qui e' `c20u<n>`, e le due maglie
     nuove si tengono in piedi a vicenda.

⚠ `13-w4` resta nel deposito: e' il documento della misura del 22 settembre,
  e la sua diagnosi (i tre fotogrammi alternati, i descrittori riciclati) non
  sta scritta da nessun'altra parte.

---------------------------------------------------------------------------
⚠ I DUE NUMERI DEL GIUDICE DEI PIXEL, e da dove vengono
---------------------------------------------------------------------------

  · **8 livelli** e' quanto due fotogrammi consecutivi possono differire in
    luminanza media senza che sia un lampeggio.  `[M]` 22 set 2026 su KDE: a
    desktop fermo la coda del video sta su **un solo valore**, e il lampeggio
    alternava fra valori lontanissimi.  ⚠ Il margine e' largo apposta: una
    soglia stretta prenderebbe il rumore della codifica.
  · **quanti salti si concedono dipende da quanto e' lunga la coda**: uno
    ogni dieci fotogrammi, al massimo tre, ⭐ e **mai meno di uno**.  ⛔ Fra la
    fine dell'avvio del desktop e la coda ci puo' stare un pannello che
    finisce di disegnarsi, e un rosso su quello sarebbe un rosso falso.
  · ⚠ **la META' dei fotogrammi non si guarda**: la scena si accende quando la
    sessione e' gia' rinata, e `[M]` il primo avvio di Firefox in una scatola
    passa i 25 s (`LEZIONI.md` §1.45).  ⇒ La prima parte del video e' il
    desktop nudo che aspetta il browser, poi c'e' il gradino desktop→scena, e
    solo dopo c'e' quel che questa maglia vuole guardare.  ⛔ «I primi 30
    fotogrammi» non bastavano: su kde quel gradino cade intorno al millesimo.
  · ⛔ Sotto i **40 fotogrammi decodificati** non si giudica: e' un **3**.
  · ⛔⛔ E se la luminanza **mediana** della coda resta sotto **40** *e* lo
    schermo e' FERMO, lo schermo e' NERO: la scena che la maglia ha acceso non
    e' arrivata, ⇒ **3** e non un verde.  ⚠ E' la stessa domanda che si fa C3
    (*«la scena che ho dichiarato e' davvero sullo schermo?»*), e la ragione e'
    la stessa: ⭐ uno schermo nero e fermo passerebbe *«la luminanza e' una»* a
    mani basse, cioe' la maglia regalerebbe un verde proprio quando non ha
    visto niente.
    ⛔⛔ E L'ORDINE DEI DUE CONTROLLI E' UNA DECISIONE: **prima il lampeggio,
        poi il nero.**  `[M]` 23 set 2026, col verso opposto il guasto
        innestato usciva **3** invece che rosso — la scena di C3 alterna blu
        (29) e giallo (226), quindi la sua MEDIANA e' 17, e la maglia diceva
        «lo schermo e' nero, non giudico» a uno schermo che le stava
        lampeggiando sotto gli occhi.  ⇒ Uno schermo che ALTERNA non e' mai
        ambiguo, per quanto scuro sia: il fantasma vero e' fatto proprio cosi'
        (desktop · schermata d'uscita · nero).

  ⛔⛔ E PERCHE' LA SCENA CI VUOLE — `[M]` 23 settembre 2026, ed e' la misura
      che ha riscritto questa maglia.  Il secondo accesso, a desktop FERMO,
      consegna:

        | scatola | compositore | fotogrammi |
        |---|---|---|
        | **kde**  | KWin  | **1 800 in 45 s** |
        | **xfce** | labwc | ⛔ **7 in 60 s**  |

      ⇒ KWin consegna anche senza danno; labwc, come ogni compositore della
        famiglia wlroots, consegna solo sul DANNO (`fasi/09…` §3.1: 0,03
        fotogrammi/s a scena ferma).  ⛔ Su un desktop fermo questa maglia
        sarebbe stata **3 per sempre su xfce e su lxqt**, e un 3 che si ripete
        e' il cugino del rosso perpetuo (`LEZIONI.md` §1.49).
      ⭐ La cura e' quella di C3: **la scena la mette la maglia, e la
        dichiara** — ma qui deve muoversi SENZA cambiare la luce, o il giudice
        dei pixel accuserebbe la scena invece del fantasma.  Sta in
        `11-c20-scena.html`, e li' c'e' scritto anche perche' le bande sono
        due e non una.

⭐ E il lampeggio del guasto innestato e' DICHIARATO, non preso a prestito: la
  scena e' `11-c3-scena.html`, che alterna il fondo fra `#0000FF` (luminanza
  BT.601 ≈ 29) e `#FFFF00` (≈ 226).  ⇒ Il salto e' di ~197 livelli, cioe'
  ⭐ **ventiquattro volte** la soglia: un guasto che passasse per un pelo non
  proverebbe niente.

Esiti: 0 verde · 1 rosso · 3 non ho potuto guardare (⛔ NON e' un rosso).
⛔ Con `--scena-che-lampeggia` si legge AL CONTRARIO: 0 = il guasto e' VISTO.
"""
import argparse
import importlib.util
import os
import random
import re
import subprocess
import sys
import tempfile
import time

QUI = os.path.dirname(os.path.abspath(__file__))
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")
REGISTRO = "/var/lib/rete11/registro.log"
PAROLA = "provanic2026"
# ⭐ LE DUE SCENE, e sono due apposta (vedi il riquadro dei numeri qui sotto).
#   · la MIA si muove e la sua luce NON cambia   ⇒ il giro sano
#   · quella di C3 alterna blu e giallo          ⇒ il GUASTO INNESTATO
SCENA_FERMA_DI_LUCE = os.path.join(QUI, "11-c20-scena.html")
SCENA_CHE_LAMPEGGIA = os.path.join(QUI, "11-c3-scena.html")

# ⭐ Le righe del prodotto che questa maglia legge, in un posto solo: se il
#   prodotto le cambia, si cambia QUI (§1.47).
RIGA_NASCITA = "formato negoziato"          # src/cattura.c
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA FINE DELLA SESSIONE GRAFICA IL PRODOTTO LA DICE IN DUE MODI — e
#     quale dei due dipende da **chi muore col gesto «Esci»**, non dal nome
#     del desktop.
#
#   · il figlio SOPRAVVIVE al gesto  (KDE, XFCE: muore il compositore, non la
#     sessione di logind)  ⇒ se ne accorge LUI, «c'era e adesso non c'e' piu'»
#         «la sessione grafica di «…» E' FINITA»          src/figlio.c:2134
#   · il figlio MUORE col gesto  (GNOME: e' lui il processo GUIDA della
#     sessione di logind — la apre con `pam_open_session` — e `gnome-session`
#     se lo porta via col segnale 15)  ⇒ ⛔ non puo' riferire un fatto che lo
#     uccide, e lo dice il PADRE nel momento in cui lo raccoglie
#         «il palco di «…» se n'e' andato ⇒ la sessione grafica e' finita»
#                                                          src/main.c:1418
#
# ⛔⛔ E LA SECONDA NON E' UN RIPIEGO PER FAR PASSARE GNOME: sta scritta nel
#     prodotto, in `src/main.c:1384-1396`, che al logout il figlio muore col
#     segnale 15 e che **per questo la riga del figlio «non e' mai scattata»**.
#     ⇒ Chiederne una sola voleva dire pretendere che il prodotto dicesse la
#       cosa nel modo di UN desktop — ed e' esattamente il difetto di `13-w4`
#       che questa maglia era nata per non rifare (punto 2 in testa al file).
# `[M]` 23 set 2026, rete11-gnome: il gesto risponde, il palco se ne va in
#   0,1 s, il padre scrive la sua riga — e la maglia aspettava l'altra per
#   120 s e usciva «non ho potuto guardare».
# ═══════════════════════════════════════════════════════════════════════════
RIGHE_FINITA = (
    ("E' FINITA", "il figlio e' sopravvissuto e se n'e' accorto"),
    ("se n'e' andato ⇒ la sessione grafica e' finita",
     "⛔ il figlio e' morto col gesto, e l'ha detto il padre raccogliendolo"),
)
RIGA_RINASCITA = "RIAVVIO LA CATTURA"       # src/figlio.c:8011
RIGA_BUTTA = re.compile(r"butto le (\d+) superfici importate")  # src/codificatore.c
# ⭐ Chi serve una sessione: «figlio generato per «X»: pid N … matricola M»
#   (`src/figlio.c:1744`).  ⛔ Serve per DIRE, e non per dedurre, che il
#   secondo accesso gira in un processo DIVERSO da quello del primo.
RIGA_FIGLIO = re.compile(r"figlio generato per «([^»]+)»: pid (\d+).*?"
                         r"matricola (\d+)")

# ⚠ I numeri del giudice dei pixel — vedi il riquadro in testa.
SOGLIA_SALTO = 8
FOTOGRAMMI_MINIMI = 40
# ⛔ Sotto questa luminanza mediana lo schermo e' NERO, e non si giudica: un
#    nero fermo e un'immagine congelata hanno lo stesso identico aspetto.
LUCE_MINIMA = 40
LARGHEZZA, ALTEZZA = 64, 24


def quanti_da_saltare(quanti):
    """⭐ Il «prima» da non guardare: la META' dei fotogrammi.

    ⛔⛔ E la meta' non e' prudenza: la scena si accende QUANDO la sessione e'
        gia' rinata, e `[M]` il primo avvio di Firefox in una scatola passa i
        25 s (`LEZIONI.md` §1.45).  ⇒ La prima parte del video e' il desktop
        nudo che aspetta il browser, poi c'e' il gradino desktop→scena, e solo
        dopo c'e' quel che questa maglia vuole guardare.
    ⚠ Tagliare «i primi 30 fotogrammi» non bastava: su kde quel gradino cade
      intorno al millesimo.
    """
    return max(4, quanti // 2)


def salti_ammessi(quanti_coda):
    """⭐ Quanti salti non sono ancora un lampeggio.

    ⛔ Non un numero fisso: con una coda di 1 770 fotogrammi «3 salti» e'
       severo, con una coda di 10 sarebbe permettere che un terzo dello
       schermo alterni.  ⚠ Uno pero' si concede sempre: fra la fine
       dell'avvio e la coda ci puo' stare un pannello che finisce di
       disegnarsi, e un rosso su quello sarebbe un rosso falso.
    """
    return max(1, min(3, quanti_coda // 10))


def sh(riga, secondi=60):
    try:
        return subprocess.run(["/bin/sh", "-c", riga], capture_output=True,
                              text=True, timeout=secondi)
    except (subprocess.TimeoutExpired, OSError):
        return None


def _carica(nome_file, mestieri):
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
        for mestiere in mestieri:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ IL GESTO «ESCI», CHIESTO ALLA MACCHINA — e non scritto per desktop.
#
# ⛔ La domanda e' la STESSA del prodotto (`src/sessione.c:285-310`): quale
#    sessione grafica c'e' in questa scatola?  Il prodotto la risolve guardando
#    quali programmi esistono, e qui si fa uguale — ⇒ il giorno che una scatola
#    cambia desktop, questa maglia lo segue senza che nessuno la tocchi.
# ⚠ E il comando del gesto e' quello del MENU, non un `kill`: la maglia deve
#   provare la strada dell'utente, non una scorciatoia che il prodotto vede in
#   un altro modo (`loginctl terminate-user` non e' «Esci»).
# ═══════════════════════════════════════════════════════════════════════════
DESKTOP_E_GESTO = (
    # (nome, marcatore che DEVE esserci, marcatore che NON deve esserci, gesto)
    ("KDE Plasma", "startplasma-wayland", "gnome-session",
     "busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout"),
    ("GNOME", "gnome-session", None,
     "busctl --user call org.gnome.SessionManager /org/gnome/SessionManager "
     "org.gnome.SessionManager Logout u 1"),
    ("XFCE", "xfce4-session", None,
     "xfce4-session-logout --logout --fast"),
)


def come_si_esce():
    """⭐ (nome del desktop, comando del gesto) — o (None, perche')."""
    def c_e(programma):
        r = sh("command -v %s >/dev/null 2>&1" % programma, 15)
        return r is not None and r.returncode == 0

    for nome, ci_vuole, non_ci_vuole, gesto in DESKTOP_E_GESTO:
        if not c_e(ci_vuole):
            continue
        if non_ci_vuole and c_e(non_ci_vuole):
            continue
        return nome, gesto
    return None, ("in questa scatola non c'e' ne' startplasma-wayland, ne' "
                  "gnome-session, ne' xfce4-session: non so come si dice "
                  "«Esci» qui dentro")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GIUDICI — funzioni PURE: `--certifica` le attraversa senza macchina.
# ═══════════════════════════════════════════════════════════════════════════
def giudica_i_pixel(luminanze):
    """⭐ (esito, salti, perche) dalla successione delle luminanze medie."""
    if luminanze is None:
        return 3, 0, "il video del secondo accesso non si e' decodificato"
    if len(luminanze) < FOTOGRAMMI_MINIMI:
        return 3, 0, ("solo %d fotogrammi decodificati (ne servono %d): non "
                      "c'e' una coda da guardare"
                      % (len(luminanze), FOTOGRAMMI_MINIMI))
    coda = luminanze[quanti_da_saltare(len(luminanze)):]
    salti = sum(1 for a, b in zip(coda, coda[1:]) if abs(a - b) > SOGLIA_SALTO)
    ammessi = salti_ammessi(len(coda))
    valori = sorted(set(coda))
    mediana = sorted(coda)[len(coda) // 2]
    # ⚠ E si stampano MINIMA, MEDIANA e MASSIMA oltre ai valori: `[M]` 23 set
    #   2026 il primo giro stampava i soli otto valori piu' bassi, ⛔ e non si
    #   poteva capire se lo schermo fosse nero o solo fermo — due cose che un
    #   giudice «la luminanza e' una» tratta allo stesso modo.
    ordinata = sorted(coda)
    dice = ("%d fotogrammi, coda di %d: %d salti oltre %d livelli (ne sono "
            "ammessi %d) · luminanza min %d · mediana %d · max %d · %d valori "
            "distinti %s"
            % (len(luminanze), len(coda), salti, SOGLIA_SALTO, ammessi,
               ordinata[0], mediana, ordinata[-1],
               len(valori), valori[:6]))
    # ⛔⛔ E L'ORDINE DI QUESTI DUE CONTROLLI E' UNA DECISIONE, non un caso:
    #     **prima il lampeggio, poi il nero** — `[M]` 23 set 2026, e col verso
    #     opposto il guasto innestato usciva **3** invece che rosso.
    #     La scena di C3 alterna blu (29) e giallo (226), ⇒ la sua MEDIANA e'
    #     17: scura.  Col controllo del nero davanti, la maglia diceva «lo
    #     schermo e' nero, non giudico» a uno schermo che stava lampeggiando
    #     sotto i suoi occhi.
    # ⇒ Uno schermo che ALTERNA non e' mai ambiguo, per quanto scuro sia: il
    #   fantasma e' fatto cosi' (desktop · schermata d'uscita · nero).  ⭐ E'
    #   il nero **FERMO** che non si sa distinguere da un'immagine congelata,
    #   e solo quello diventa un «non ho potuto guardare».
    if salti > ammessi:
        return 1, salti, ("lo schermo LAMPEGGIA dopo la rinascita — " + dice)
    if mediana < LUCE_MINIMA:
        return 3, salti, ("lo schermo e' NERO e FERMO (luminanza mediana %d, "
                          "sotto %d): la scena che ho acceso non e' arrivata, "
                          "e un nero fermo e un'immagine congelata hanno lo "
                          "stesso aspetto — " % (mediana, LUCE_MINIMA) + dice)
    return 0, salti, ("a desktop fermo la luminanza e' una — " + dice)


def chi_serviva(fetta, chi):
    """⭐ Il pid del figlio che serve «chi» in questa fetta di registro — o None.

    ⚠ Se ce n'e' piu' d'uno si prende l'ULTIMO: e' quello che sta servendo
      adesso.
    """
    if not fetta:
        return None
    pid = None
    for r in fetta:
        m = RIGA_FIGLIO.search(r)
        if m and m.group(1) == chi:
            pid = m.group(2)
    return pid


def giudica_il_registro(fetta, chi, figlio_morto, pid_di_prima):
    """⭐ (esito, quante, perche) dalle righe di registro di QUESTO inquilino.

    ═══════════════════════════════════════════════════════════════════════
    ⭐⭐ E LA DOMANDA E' DIVERSA NEI DUE CASI, perche' e' diverso il PERICOLO.
    ⛔ Non e' una soglia allentata per far passare GNOME: e' la stessa prova
       chiesta al fatto che c'e' davvero da provare.

    `src/cattura.c:1318-1332`, la diagnosi del difetto vero (22 set 2026, la
    prova dell'utente su KDE): *«dopo «Esci» e un nuovo accesso la sessione
    rinasce NELLO STESSO figlio: la cattura e' nuova, il codificatore no»* —
    ⇒ i descrittori riciclati ritrovavano le superfici della sessione morta.

      · **il figlio e' SOPRAVVISSUTO** (KDE, XFCE) ⇒ il codificatore e' lo
        STESSO OGGETTO di prima, e il pericolo c'e' tutto: si pretende che
        abbia buttato la cache — «butto le N superfici importate».
        ⛔ Se non l'ha buttata e' ROSSO, ed e' il difetto vero.

      · **il figlio e' MORTO col gesto** (GNOME: e' lui il processo guida
        della sessione di logind) ⇒ il codificatore e' morto con lui, e ⛔ non
        c'e' NESSUNA cache da buttare: le superfici della sessione di prima
        stanno in un processo che non esiste piu'.
        ⭐ Ma non basta dirlo: si PRETENDE LA PROVA, e cioe' che il secondo
          accesso sia servito da un figlio col **pid diverso** da quello del
          primo.  ⛔ Senza quel pid non si giudica (3), e se il pid fosse lo
          stesso il figlio non sarebbe morto affatto — ⇒ 3, la premessa della
          maglia non regge.

    ⛔⛔ E NON SI GUARDA «RIAVVIO LA CATTURA» NEL SECONDO CASO: `[M]` 23 set
        2026 su rete11-gnome quella riga C'E' lo stesso — la scrive il figlio
        NUOVO che al primo tentativo non trova il palco e al secondo si' —
        ⇒ guardarla vorrebbe dire leggere un verde da una riga che parla
        d'altro, che e' il modo esatto in cui una maglia smette di guardare.
    ═══════════════════════════════════════════════════════════════════════
    """
    if fetta is None:
        return 3, 0, "non ho potuto leggere il registro del server"

    if figlio_morto:
        pid_adesso = chi_serviva(fetta, chi)
        if pid_adesso is None:
            return 3, 0, ("il figlio di «%s» era morto col gesto «Esci» e nel "
                          "registro del secondo accesso non ne nasce nessun "
                          "altro: non so chi stia servendo questa sessione"
                          % chi)
        if pid_di_prima is None:
            return 3, 0, ("non ho letto il pid del figlio del PRIMO accesso: "
                          "senza non posso dire che questo (%s) sia un altro"
                          % pid_adesso)
        if pid_adesso == pid_di_prima:
            return 3, 0, ("il secondo accesso e' servito dallo STESSO figlio "
                          "del primo (pid %s), e il prodotto aveva detto che "
                          "era morto: la premessa non regge" % pid_adesso)
        return 0, 0, ("il figlio e' morto col gesto e il secondo accesso gira "
                      "in un figlio NUOVO (pid %s, prima %s): il codificatore "
                      "della sessione morta non esiste piu', e le sue "
                      "superfici nemmeno"
                      % (pid_adesso, pid_di_prima))

    mie = [r for r in fetta if ("[%s]" % chi) in r]
    if not any(RIGA_RINASCITA in r for r in mie):
        return 3, 0, ("nel registro non c'e' nessuna rinascita della cattura "
                      "(«%s») per «%s»: la sessione nuova non e' nata da una "
                      "vecchia, e non c'e' niente da giudicare"
                      % (RIGA_RINASCITA, chi))
    quante = 0
    for r in mie:
        m = RIGA_BUTTA.search(r)
        if m:
            quante += int(m.group(1))
    if quante > 0:
        return 0, quante, ("dopo la rinascita il codificatore ha buttato %d "
                           "superfici della sessione di prima" % quante)
    return 1, 0, ("la cattura e' rinata ma il codificatore NON ha buttato la "
                  "cache: le superfici della sessione morta sono ancora dentro")


def giudizio(pixel, registro):
    """⭐ L'esito della maglia dai due giudici.

    ⛔ Un `3` di uno dei due non diventa MAI un rosso: `LEZIONI.md` §1.49 —
       «non lo so» e «non regge» sono due cose, e confonderle e' il modo in cui
       una rete comincia a gridare mentre il prodotto sta benissimo.
    """
    ep, ip, _ = pixel
    er, ir, _ = registro
    if ep == 3 or er == 3:
        return 3
    if ep == 1 or er == 1:
        return 1
    return 0


def luminanze_dal_grezzo(dati):
    """⭐ La media per fotogramma da un `rawvideo` gray 64x24."""
    n = LARGHEZZA * ALTEZZA
    if not dati or len(dati) < n:
        return None
    return [sum(dati[i * n:(i + 1) * n]) // n for i in range(len(dati) // n)]


# ═══════════════════════════════════════════════════════════════════════════
def sgombera(chi):
    sh("loginctl terminate-user %s >/dev/null 2>&1" % chi, 30)
    # ⛔ `[c]20u4` e non `c20u4`: `pkill -f` pescherebbe il guscio che lo sta
    #    eseguendo, e il guscio si ucciderebbe da solo (22 set 2026).
    sh("pkill -CONT -f 'runuser -u [%s]%s ' 2>/dev/null" % (chi[0], chi[1:]), 20)
    sh("pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null" % (chi[0], chi[1:]), 20)
    sh("pkill -KILL -u %s >/dev/null 2>&1" % chi, 20)
    time.sleep(0.5)
    sh("userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1"
       % (chi, chi), 40)
    sh("rm -rf /home/%s" % chi, 20)


def leggi(percorso):
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except OSError:
        return None


def aspetta_la_riga(percorso, segno, chi, pezzi, tetto):
    """⭐ Si aspetta l'EVENTO, non l'orologio.  Torna (quale, fetta).

    ⚠ `pezzi` e' un pezzo di riga oppure un elenco di pezzi: il primo che si
      vede vince, e si torna **quello** — cosi' chi chiama puo' DIRE quale
      forma ha usato il prodotto invece di scrivere solo «l'ho visto».
    ⛔ Un elenco non e' una soglia allentata: e' la stessa domanda posta al
       prodotto nelle forme in cui il prodotto sa rispondere (RIGHE_FINITA).
    """
    if isinstance(pezzi, str):
        pezzi = (pezzi,)
    scadenza = time.time() + tetto
    fetta = []
    while time.time() < scadenza:
        righe = leggi(percorso)
        fetta = righe[segno:] if righe is not None else []
        for pezzo in pezzi:
            # ⚠ Il nome sta fra parentesi quadre nelle righe marcate per
            #   inquilino, e fra virgolette basse in quelle del padre (la
            #   riga «E' FINITA» e quella del palco che se ne va): si
            #   guardano tutt'e due le forme.
            for r in fetta:
                if pezzo in r and (("[%s]" % chi) in r or ("«%s»" % chi) in r):
                    return pezzo, fetta
        time.sleep(0.5)
    return None, fetta


def il_cliente_c_e(porta, chi):
    """⛔⛔ `[c]20u2` E NON `c20u2`, e non e' un vezzo.

    La riga di comando del guscio che esegue questo `pgrep` contiene il nome
    dell'inquilino ⇒ `pgrep -f` **pesca se stesso**, e l'attesa «finche' il
    cliente c'e'» non finisce mai.  ⚠ E' la stessa trappola che il 22 set 2026
    faceva uccidere il guscio da solo (`11-gancio.sh`, `sgombera_inquilini`).
    ⭐ Le parentesi quadre valgono come espressione e non come testo.
    """
    r = sh("pgrep -f 'porta %d --utente [%s]%s' >/dev/null 2>&1"
           % (porta, chi[0], chi[1:]), 15)
    return r is not None and r.returncode == 0


def aspetta_che_il_cliente_se_ne_vada(porta, chi, tetto):
    scadenza = time.time() + tetto
    while time.time() < scadenza:
        if not il_cliente_c_e(porta, chi):
            return True
        time.sleep(0.5)
    return False


def coda_di(percorso, quante=3):
    righe = leggi(percorso)
    if not righe:
        return "(niente)"
    return " ⏎ ".join(r.strip()[:90] for r in righe[-quante:] if r.strip())


def il_socket_di(chi):
    """⛔ Il socket di Wayland si CERCA, non si indovina (§3.7)."""
    r = sh("id -u %s" % chi, 15)
    uid = (r.stdout or "").strip() if r else ""
    if not uid:
        return None, None
    rtd = "/run/user/%s" % uid
    r = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd, 15)
    d = (r.stdout or "").strip() if r else ""
    return rtd, (d or None)


def accendi_la_scena(chi, scena, applicazione, come, prefisso="   "):
    """⭐ Accende la scena DICHIARATA dentro la sessione appena rinata.

    ⛔⛔ E SI ACCENDE IN TUTT'E DUE I GIRI, non solo in quello col guasto —
        23 set 2026, ed e' la misura che l'ha deciso: il secondo accesso porta
        **1 800 fotogrammi in 45 s su kde** e **7 in 60 s su xfce**.  KWin
        consegna anche a desktop fermo, labwc (wlroots) consegna solo sul
        DANNO.  ⇒ Senza una scena che si muova, su xfce e su lxqt questa
        maglia non avrebbe **niente da guardare**, per sempre.
    ⭐ La scena del giro sano (`11-c20-scena.html`) si muove e la sua luce NON
      cambia: fotogrammi tutti diversi, luminanza media costante.  ⇒ E' quel
      che il giudice vuole, ed e' dichiarato in quel file.

    ⭐ `setsid` e stdin su `/dev/null`, come C3: senza, il browser prende
      SIGTTOU dal terminale del banco e resta fermo in `T` — `[M]` 22 set 2026,
      e sembrava un prodotto che non consegna.
    """
    # ═══════════════════════════════════════════════════════════════════
    # ⛔⛔ LA PROVVISTA DEL BROWSER, E COSTA UN GIRO INTERO — 23 set 2026.
    #
    # `[M]` Primo giro del guasto innestato su kde: `firefox-esr` partiva
    # (`pgrep` lo trovava), ⛔ e sullo schermo non arrivava NIENTE — 1800
    # fotogrammi, 0 salti, la maglia diceva «il guasto non e' stato visto».
    # ⇒ La causa e' quella che C3 ha gia' pagato il 27 agosto 2026:
    #   `~/.cache/mozilla` -> `/tmp/mozilla`, rimasto a un ALTRO inquilino a
    #   modo 0700 ⇒ il browser si ferma sulla finestra di scelta del profilo
    #   e non dipinge mai.  ⚠ Un guasto innestato che non morde per colpa del
    #   banco e' peggio di nessun guasto: dice «la maglia e' rotta» mentre e'
    #   il banco a non aver preparato la scena.
    # ⭐ La cura sta in C2 (`cura_della_provvista`) e ⛔ NON se ne fa una copia
    #   qui: la stessa regola in tre file sono tre posti da cui divergere.
    # ═══════════════════════════════════════════════════════════════════
    c2 = _carica("11-c2-una-finestra-si-apre.py",
                 ("cura_della_provvista", "sgombra_il_mio_rimasuglio"))
    if c2 is None:
        return False, ("non trovo `11-c2-una-finestra-si-apre.py` accanto a me: "
                       "da li' viene la cura della provvista del browser, e "
                       "senza la scena non si accende")
    fatto, perche_p = c2.cura_della_provvista(chi)
    if not fatto:
        return False, "la provvista del browser non e' pronta: %s" % perche_p

    rtd, display = il_socket_di(chi)
    if display is None:
        return False, ("in %s non c'e' nessun socket wayland: non c'e' un "
                       "compositore a cui la scena possa parlare" % rtd)
    sh("setsid runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s --kiosk file://%s < /dev/null > /home/%s/.c20-scena.log 2>&1 &"
       % (chi, rtd, display, chi, applicazione, scena, chi), 30)
    for _ in range(40):
        r = sh("pgrep -u %s -f %s >/dev/null 2>&1" % (chi, applicazione), 15)
        if r is not None and r.returncode == 0:
            print("%s%s (%s su %s)"
                  % (prefisso, come, applicazione, os.path.basename(scena)))
            return True, ""
        time.sleep(0.25)
    return False, "la scena non si e' accesa: %s non si e' visto" % applicazione


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ I due giudici sanno dire verde, rosso e «non lo so»?"""
    guai = 0
    # ⭐ Il giro sano: prima il desktop nudo (scuro), poi il gradino della
    #   scena che si accende, poi la scena — che si muove e la cui luce NON
    #   cambia (~157, come dichiara `11-c20-scena.html`).
    sano = [20] * 100 + [157] * 100
    # ⚠ Il rumore della codifica: ±3 livelli, sotto la soglia ⇒ non e' un salto.
    rumore = [20] * 100 + [157 + (i % 7) - 3 for i in range(100)]
    # ⛔ Il lampeggio vero: blu (29) ⇄ giallo (226), come `11-c3-scena.html`.
    lampeggio = [20] * 100 + [29 if (i // 2) % 2 == 0 else 226
                              for i in range(100)]
    # ⚠ Un assestamento solo DENTRO la coda: NON e' un lampeggio.
    assesta = [20] * 100 + [157] * 50 + [180] * 50
    # ⭐ La coda corta di un compositore che consegna poco (xfce/lxqt): 80
    #   fotogrammi in tutto, coda di 40.
    corto_sano = [20] * 40 + [150] * 40
    corto_lampeggio = [20] * 40 + [29 if (i // 2) % 2 == 0 else 226
                                   for i in range(40)]
    # ⛔⛔ E IL CASO CHE VALE PIU' DI TUTTI: lo schermo NERO e fermo.
    nero = [6] * 200
    # ⛔⛔ E IL SUO GEMELLO CATTIVO, che il 23 set 2026 usciva 3 invece che
    #   rosso: uno schermo SCURO CHE ALTERNA.  E' la scena di C3 vista dalla
    #   cattura (mediana 17) ed e' anche la forma del fantasma vero.
    nero_che_alterna = [20] * 100 + [29 if (i // 2) % 2 == 0 else 6
                                     for i in range(100)]
    casi_pixel = [
        ("⭐ la scena dichiarata, luce UNA ⇒ VERDE", sano, 0),
        ("⭐ rumore della codifica sotto la soglia ⇒ VERDE", rumore, 0),
        ("⭐ un assestamento solo (1 salto) ⇒ VERDE, ⛔ non un rosso", assesta, 0),
        ("⛔ il LAMPEGGIO (blu ⇄ giallo) ⇒ ROSSO", lampeggio, 1),
        ("⭐ coda corta (xfce/lxqt), luce una ⇒ VERDE", corto_sano, 0),
        ("⛔ coda corta che LAMPEGGIA ⇒ ROSSO lo stesso", corto_lampeggio, 1),
        ("⛔⛔ schermo NERO e FERMO ⇒ 3 — ⛔ MAI un verde: la scena non e' "
         "arrivata", nero, 3),
        ("⛔⛔ schermo scuro che ALTERNA ⇒ ROSSO — ⛔ il lampeggio viene "
         "PRIMA del nero", nero_che_alterna, 1),
        ("⚠ video troppo corto (39 fotogrammi) ⇒ 3, ⛔ mai un rosso",
         [157] * 39, 3),
        ("⚠ ffmpeg non ha decodificato niente ⇒ 3", None, 3),
    ]
    print("== C20 — certificazione dei giudizi (⛔ senza toccare la macchina)")
    for nome, dato, atteso in casi_pixel:
        e = giudica_i_pixel(dato)[0]
        if e != atteso:
            guai += 1
        print("  %s PIXEL    %-62s esito %s (atteso %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    buono = ["figlio  [c20u1] ⭐⭐ RIAVVIO LA CATTURA: il palco e' tornato",
             "codifica [c20u1] ⭐ butto le 4 superfici importate: generazione"]
    # ⭐ IL FIGLIO SOPRAVVISSUTO — KDE, XFCE: il codificatore e' lo stesso.
    casi_reg = [
        ("⭐ rinata, e la cache buttata ⇒ VERDE", buono, 0),
        ("⛔ rinata e la cache NON buttata ⇒ ROSSO", buono[:1], 1),
        ("⚠ nessuna rinascita ⇒ 3, ⛔ mai un rosso", buono[1:], 3),
        ("⚠ le righe sono di un ALTRO inquilino ⇒ 3",
         [r.replace("c20u1", "c20u9") for r in buono], 3),
        ("⚠ il registro non si legge ⇒ 3", None, 3),
    ]
    for nome, dato, atteso in casi_reg:
        e = giudica_il_registro(dato, "c20u1", False, "111")[0]
        if e != atteso:
            guai += 1
        print("  %s REGISTRO %-62s esito %s (atteso %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    # ⭐⭐ IL FIGLIO MORTO COL GESTO — GNOME.  ⛔ Qui il verde NON si regala:
    #     si pretende il pid di un figlio NUOVO, e senza quello e' 3.
    nuovo = ["figlio  ⭐ figlio generato per «c20u1»: pid 222, uid 4014, gid "
             "4014, matricola 3.  ⛔ Che sia DAVVERO quell'uid",
             "figlio  [c20u1] ⭐⭐ RIAVVIO LA CATTURA: il palco e' tornato"]
    casi_morto = [
        ("⭐ figlio NUOVO (pid 222 ≠ 111) ⇒ VERDE", nuovo, "111", 0),
        ("⛔ nessun figlio nuovo nel registro ⇒ 3, ⛔ non un verde",
         nuovo[1:], "111", 3),
        ("⛔ lo STESSO pid di prima ⇒ 3: non era morto affatto",
         nuovo, "222", 3),
        ("⚠ non so il pid del primo accesso ⇒ 3", nuovo, None, 3),
        ("⚠ il figlio nuovo e' di un ALTRO inquilino ⇒ 3",
         [r.replace("c20u1", "c20u9") for r in nuovo], "111", 3),
        ("⚠ il registro non si legge ⇒ 3", None, "111", 3),
    ]
    for nome, dato, prima, atteso in casi_morto:
        e = giudica_il_registro(dato, "c20u1", True, prima)[0]
        if e != atteso:
            guai += 1
        print("  %s REG/MORTO %-61s esito %s (atteso %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    casi_somma = [
        ("⭐ tutt'e due verdi ⇒ VERDE", (0, 0, ""), (0, 4, ""), 0),
        ("⛔ i pixel lampeggiano ⇒ ROSSO", (1, 60, ""), (0, 4, ""), 1),
        ("⛔ la cache non buttata ⇒ ROSSO", (0, 0, ""), (1, 0, ""), 1),
        ("⚠ un «non lo so» NON diventa un rosso", (3, 0, ""), (1, 0, ""), 3),
        ("⚠ e nemmeno dall'altra parte", (1, 9, ""), (3, 0, ""), 3),
    ]
    for nome, p, r, atteso in casi_somma:
        e = giudizio(p, r)
        if e != atteso:
            guai += 1
        print("  %s SOMMA    %-62s esito %s (atteso %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    # ⭐ E il gesto: la tavola dei desktop si prova per forma, non per fiducia.
    print("  %s la tavola dei gesti «Esci» ha %d desktop: %s"
          % ("OK " if len(DESKTOP_E_GESTO) == 3 else "NO ",
             len(DESKTOP_E_GESTO),
             ", ".join(d[0] for d in DESKTOP_E_GESTO)))
    print()
    if guai:
        print("⛔ %d casi dei giudizi NON danno quel che devono" % guai)
        return 1
    print("⭐ i due giudici danno verde, rosso e «non lo so» dove devono — e "
          "⛔ il lampeggio\n   dichiarato (29 ⇄ 226) e' rosso, mentre un "
          "assestamento solo non lo e'")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--scena-che-lampeggia", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: nel secondo accesso si accende "
                        "la scena di C3 ⇒ lo schermo lampeggia davvero, e il "
                        "giudice dei pixel DEVE dare rosso")
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--scena", default=SCENA_FERMA_DI_LUCE,
                   help="la scena del GIRO SANO: si muove, e la sua luce non "
                        "cambia")
    p.add_argument("--scena-guasta", default=SCENA_CHE_LAMPEGGIA,
                   help="la scena del GUASTO INNESTATO: quella di C3, che "
                        "alterna blu e giallo")
    p.add_argument("--applicazione", default="firefox-esr")
    p.add_argument("--primo", type=float, default=90.0,
                   help="quanto resta collegato il PRIMO cliente (deve "
                        "sopravvivere all'«Esci»: il figlio se ne accorge "
                        "quando qualcuno GUARDA)")
    # ⚠ 75 s, e il numero viene dal BROWSER: la scena si accende quando la
    #   sessione e' gia' rinata, e `[M]` il primo avvio di Firefox in una
    #   scatola passa i 25 s (`LEZIONI.md` §1.45).  ⇒ Il giudice butta via la
    #   prima meta' del video, quindi la coda comincia intorno al 37° secondo:
    #   una dozzina di secondi DOPO che la scena e' sullo schermo.
    p.add_argument("--secondo", type=float, default=75.0)
    p.add_argument("--attesa-nascita", type=float, default=120.0)
    # ⚠ 120 s e non 60: `[M]` 23 set 2026, su **xfce** il gesto risponde subito
    #   ma la sessione ci mette di piu' a finire davvero — un giro e' uscito 3
    #   («il prodotto non ha dichiarato la sessione finita») e il giro dopo,
    #   identico, l'ha dichiarata.  ⛔ Un tetto troppo stretto produce dei 3 che
    #   sembrano del prodotto e sono del banco (§1.45).
    p.add_argument("--attesa-uscita", type=float, default=120.0)
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.porta:
        print("⛔ vuole `--porta` ⇒ non ho potuto guardare")
        return 3
    if os.geteuid() != 0:
        print("⛔ vuole l'amministratore (crea un inquilino) ⇒ non ho potuto "
              "guardare")
        return 3

    chi = "c20u%d" % random.randint(100, 999)
    innestato = (" ⛔ GUASTO INNESTATO: --scena-che-lampeggia"
                 if a.scena_che_lampeggia else "")
    print("== C20 — la rinascita dopo «Esci» non porta fantasmi (%s, porta "
          "%d)%s" % (chi, a.porta, innestato))

    desktop, gesto = come_si_esce()
    if desktop is None:
        print("   ⛔ %s ⇒ non ho potuto guardare" % gesto)
        return 3
    print("   il desktop di questa scatola: %s — «Esci» si dice cosi':\n"
          "      %s" % (desktop, gesto))
    if leggi(a.registro) is None:
        print("   ⛔ non leggo %s ⇒ non ho potuto guardare" % a.registro)
        return 3
    # ⭐ La scena di questo giro: quella dichiarata, o quella di C3 se il
    #   guasto e' innestato.  ⛔ Senza il file non si accende niente, e senza
    #   scena questa maglia non ha di che giudicare ⇒ 3, non un verde.
    scena = a.scena_guasta if a.scena_che_lampeggia else a.scena
    come = ("⛔ il lampeggio e' acceso (#0000FF ⇄ #FFFF00)"
            if a.scena_che_lampeggia
            else "⭐ la scena e' accesa: si muove, e la sua luce non cambia")
    if not os.path.exists(scena):
        print("   ⛔ manca la scena %s ⇒ non ho potuto guardare" % scena)
        return 3

    dove = tempfile.mkdtemp(prefix="c20.")
    video = os.path.join(dove, "video.h264")
    grezzo = os.path.join(dove, "luma.raw")
    primo = None
    try:
        sgombera(chi)
        r = sh("useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
               % (chi, chi, PAROLA), 60)
        if r is None or r.returncode != 0:
            print("   ⛔ non ho potuto creare l'inquilino ⇒ non ho potuto "
                  "guardare")
            return 3
        # ⭐ I gruppi della scheda: senza, la sessione nasce cieca e questa
        #   maglia direbbe «non ho potuto guardare» per colpa del banco.
        #   ⛔ E non si riscrive qui: e' l'attrezzo che usano tutte (§1.47).
        c1 = _carica("11-c1-nasce-e-si-vede.py", ("garantisci_i_gruppi",))
        if c1 is None:
            print("   ⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me: "
                  "senza i gruppi della scheda\n      la sessione nasce cieca "
                  "⇒ non ho potuto guardare")
            return 3
        eg, perche_g = c1.garantisci_i_gruppi(chi, "      ")
        if eg != 0:
            print("   ⛔ %s ⇒ non ho potuto guardare" % perche_g)
            return 3

        # ── 1. IL PRIMO ACCESSO, e resta collegato durante «Esci» ──────────
        # ⛔ `[M]` 22 set 2026: il figlio si accorge dell'uscita quando
        #    qualcuno GUARDA.  Il gesto dell'utente era proprio questo.
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0
        sh("setsid python3 -u %s --indirizzo 127.0.0.1 --porta %d --utente %s "
           "--parola %s --resta %s < /dev/null > %s/uno.txt 2>&1 &"
           % (CLIENTE, a.porta, chi, PAROLA, a.primo, dove), 30)
        nato, fetta_uno = aspetta_la_riga(a.registro, segno, chi, RIGA_NASCITA,
                                          a.attesa_nascita)
        if not nato:
            print("   ⛔ in %d s il registro non ha detto «%s» per «%s»: la "
                  "sessione non e' nata\n      ⇒ non ho potuto guardare"
                  % (a.attesa_nascita, RIGA_NASCITA, chi))
            return 3
        # ⭐ SI SEGNA CHI STA SERVENDO ADESSO, e serve dopo: se il gesto
        #   «Esci» uccide il figlio (GNOME), l'unica prova che le superfici
        #   della sessione morta non possono sopravvivere e' che il secondo
        #   accesso giri in un processo con un pid DIVERSO da questo.
        pid_di_prima = chi_serviva(fetta_uno, chi)
        print("   ⭐ primo accesso: la sessione di «%s» e' nata, e il cliente "
              "guarda (la serve il figlio pid %s)"
              % (chi, pid_di_prima or "?"))
        time.sleep(10)

        # ── 2. «ESCI», il gesto del menu ───────────────────────────────────
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0
        rtd, _ = il_socket_di(chi)
        r = sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s "
               "DBUS_SESSION_BUS_ADDRESS=unix:path=%s/bus %s"
               % (chi, rtd, rtd, gesto), 60)
        if r is None or r.returncode != 0:
            print("   ⛔ il gesto «Esci» di %s non ha risposto: %s ⇒ non ho "
                  "potuto guardare"
                  % (desktop, ((r.stderr or r.stdout).strip().replace("\n", " ")[:120])
                     if r else "nessuna risposta"))
            return 3
        finita, _ = aspetta_la_riga(a.registro, segno, chi,
                                    [p for p, _d in RIGHE_FINITA],
                                    a.attesa_uscita)
        if not finita:
            print("   ⛔ %d s dopo «Esci» il prodotto non ha dichiarato la "
                  "sessione finita ⇒ non ho potuto guardare\n"
                  "      e le ho aspettate tutt'e due: %s"
                  % (a.attesa_uscita,
                     " · ".join("«%s»" % p for p, _d in RIGHE_FINITA)))
            return 3
        # ⭐ Si DICE quale delle due forme ha usato il prodotto: e' la
        #   differenza fra «il figlio e' vivo» e «il figlio e' morto col
        #   gesto», e il giudice del registro qui sotto ne dipende.
        figlio_morto = (finita != RIGHE_FINITA[0][0])
        print("   ⭐ «Esci»: il prodotto ha visto finire la sessione grafica "
              "— %s" % dict(RIGHE_FINITA)[finita])
        # ⛔⛔ E QUI SI ASPETTA CHE IL PRIMO CLIENTE SE NE SIA ANDATO DAVVERO.
        #    `[M]` 23 set 2026, primo giro: l'attesa era di 30 s fissi, il
        #    cliente e' rimasto attaccato fino ai suoi `--resta`, ⇒ il secondo
        #    accesso e' arrivato mentre il primo era ancora dentro e la
        #    sessione nuova non e' nata: **esito 3, e non era del prodotto**.
        #    ⚠ Il tetto e' legato a `--primo`, non preso a prestito: si sa
        #      quando il primo cliente finirebbe comunque da se'.
        if not aspetta_che_il_cliente_se_ne_vada(a.porta, chi, a.primo + 30):
            print("   ⛔ il primo cliente e' ancora attaccato dopo %d s ⇒ non "
                  "ho potuto guardare\n      la sua ultima riga: %s"
                  % (a.primo + 30, coda_di(os.path.join(dove, "uno.txt"))))
            return 3
        print("   ⭐ il primo cliente se n'e' andato: %s"
              % coda_di(os.path.join(dove, "uno.txt"), 1))
        time.sleep(2)

        # ── 3. IL NUOVO ACCESSO, col video scritto ─────────────────────────
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0
        sh("setsid python3 -u %s --indirizzo 127.0.0.1 --porta %d --utente %s "
           "--parola %s --resta %s --video-scrivi %s < /dev/null > %s/due.txt "
           "2>&1 &" % (CLIENTE, a.porta, chi, PAROLA, a.secondo, video, dove), 30)
        rinato, _ = aspetta_la_riga(a.registro, segno, chi, RIGA_NASCITA,
                                    a.attesa_nascita)
        if not rinato:
            print("   ⛔ in %d s la sessione nuova non e' nata ⇒ non ho potuto "
                  "guardare\n      il secondo cliente dice: %s"
                  % (a.attesa_nascita, coda_di(os.path.join(dove, "due.txt"))))
            return 3
        acceso, perche_s = accendi_la_scena(chi, scena, a.applicazione, come)
        if not acceso:
            print("   ⛔ %s ⇒ non ho potuto guardare" % perche_s)
            return 3
        # ⚠ Si aspetta che il cliente abbia finito di scrivere: il video e' il
        #   solo testimone, e leggerlo a meta' sarebbe una misura piu' corta.
        aspetta_che_il_cliente_se_ne_vada(a.porta, chi, a.secondo + 60)

        fetta = leggi(a.registro)
        fetta = fetta[segno:] if fetta is not None else None
        if not os.path.exists(video) or os.path.getsize(video) == 0:
            coda = ""
            t = leggi(os.path.join(dove, "due.txt"))
            if t:
                coda = t[-1].strip()[:110]
            print("   ⛔ il secondo accesso non ha scritto video (%s) ⇒ non ho "
                  "potuto guardare" % coda)
            return 3
        print("   ⭐ secondo accesso: %d byte di video"
              % os.path.getsize(video))

        # ── i giudici ──────────────────────────────────────────────────────
        r = sh("ffmpeg -v error -i %s -vf scale=%d:%d,format=gray -f rawvideo "
               "%s" % (video, LARGHEZZA, ALTEZZA, grezzo), 180)
        luminanze = None
        if r is not None and os.path.exists(grezzo):
            try:
                with open(grezzo, "rb") as f:
                    luminanze = luminanze_dal_grezzo(f.read())
            except OSError:
                luminanze = None
        pixel = giudica_i_pixel(luminanze)
        registro = giudica_il_registro(fetta, chi, figlio_morto, pid_di_prima)
        esito = giudizio(pixel, registro)
        print("   P %-3s %s" % ("SI" if pixel[0] == 0 else
                                ("NO" if pixel[0] == 1 else "?"), pixel[2]))
        print("   R %-3s %s" % ("SI" if registro[0] == 0 else
                                ("NO" if registro[0] == 1 else "?"), registro[2]))

        print()
        if a.scena_che_lampeggia:
            # ⛔ Al contrario, e si dice a voce: qui lo 0 e' la buona notizia.
            if esito == 1:
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO — questa maglia SA "
                      "dare rosso,\n   ⭐ e per la ragione giusta: %s" % pixel[2])
                return 0
            if esito == 3:
                print("⚠ col guasto innestato NON ho potuto guardare\n"
                      "   ⇒ esito 3, non un verde")
                return 3
            print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: lo schermo "
                  "lampeggiava davvero\n   (blu ⇄ giallo) e la maglia ha detto "
                  "verde lo stesso.")
            return 1
        if esito == 0:
            # ⚠ E il secondo giudice si cita con le SUE parole: dire «la cache
            #   e' stata buttata» dove il figlio era morto col gesto sarebbe
            #   raccontare un fatto che non e' successo (su GNOME non c'era
            #   nessuna cache da buttare — ⭐ c'era un processo nuovo).
            print("⭐ VERDE — dopo «Esci» e il nuovo accesso lo schermo e' "
                  "pulito\n   ⭐ e %s" % registro[2])
        elif esito == 1:
            print("⛔⛔ ROSSO — %s"
                  % (pixel[2] if pixel[0] == 1 else registro[2]))
        else:
            print("⚠ non ho potuto guardare — %s"
                  % (pixel[2] if pixel[0] == 3 else registro[2]))
        return esito
    finally:
        # ⛔ Il `/tmp/mozilla` che la cura della provvista ha messo si toglie
        #    SOLO se e' rimasto a un inquilino mio: cancellare quello di
        #    un'altra maglia la farebbe cadere (C14, le scatole in parallelo).
        c2 = _carica("11-c2-una-finestra-si-apre.py",
                     ("cura_della_provvista", "sgombra_il_mio_rimasuglio"))
        if c2 is not None:
            riga = c2.sgombra_il_mio_rimasuglio("c20u")
            if riga:
                print("   %s" % riga)
        sgombera(chi)
        try:
            for n in os.listdir(dove):
                os.unlink(os.path.join(dove, n))
            os.rmdir(dove)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
