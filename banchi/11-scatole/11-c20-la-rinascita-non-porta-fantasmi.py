#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c20 — ⭐⭐ «AFTER «LOG OUT» AND A NEW LOGIN, THE SCREEN DOES NOT FLICKER»
===========================================================================

    python3 11-c20-la-rinascita-non-porta-fantasmi.py --porta 8512
    python3 11-c20-la-rinascita-non-porta-fantasmi.py --porta 8512 --scena-che-lampeggia
    python3 11-c20-la-rinascita-non-porta-fantasmi.py --certifica

    what must be true         : the user logs out from the desktop menu and comes back
                                ⇒ the NEW session shows clean: ⛔ no
                                ghosts of the dead session
    where it starts from      : a new tenant, a session born, the
                                user's real gesture («Log out» from the menu), and
                                in the new session ⭐ **a DECLARED
                                scene** (`11-c20-scena.html`): it moves,
                                and its light does not change
    what it looks at          : two judges, and the first asks nothing of the
                                product
      P  pixels    the video of the SECOND login is decoded, and the mean
                   luminance of the frames is **ONE**.  If it alternates between
                   distant values, it is the flicker.
      R  log       after the rebirth the encoder says «throwing away the N
                   imported surfaces» for THIS tenant
    how I know it can give red: `--scena-che-lampeggia` — instead of the declared
                                scene **C3**'s one is started, which
                                alternates the background between blue (#0000FF) and yellow
                                (#FFFF00) ⇒ ⭐ the mean luminance jumps by
                                ~197 levels out of 255, and the PIXEL judge
                                **must** give red

---------------------------------------------------------------------------
⛔⛔ THE DEFECT THIS MESH WATCHES — 22 September 2026
---------------------------------------------------------------------------

The user's test on KDE with Chrome: after «Log out» and a new login the
screen alternated THREE images — the desktop, the logout screen of the
session BEFORE, and black.

`[M]` The buffer generation restarted from 0 with the new capture, the
encoder (which **stays** alive) did not throw away its cache, and the recycled
descriptors found again the surfaces of the dead session.
`[R]` `src/codificatore.c`, `butta_le_importate()`: *«a surface that
outlives the `pw_buffer` it described points to someone else's memory …
the symptom would be an OLD picture, with no error at all»*.

⇒ ⛔⛔ **«With no error at all»** is the reason a mesh is needed and the
  log is not enough: the product does not notice, the client does not
  notice, and ⭐ **the only one who notices is whoever LOOKS**.  This mesh
  looks in their place.

---------------------------------------------------------------------------
⭐⭐ FROM `13-w4` TO C20 — what changed, and why
---------------------------------------------------------------------------

This mesh is born from `banchi/13-w4-rinascita-senza-fantasmi.sh` (22 Sep
2026), which found the defect and measured it.  ⭐ Entering the net it had
to change three things — and they are exactly the three that separate a bench
written for one evening from a mesh that runs by itself for months:

  1. ⛔⛔ **THE INJECTED FAULT, which it did not have.**  Without it, the mesh proves
     nothing: the day the pixel judge stopped looking
     (an `ffmpeg` that changes output, a crooked threshold, an empty video read
     as «still») ⭐ it would say GREEN for ever, and nobody would know.
     ⇒ `--scena-che-lampeggia` puts a REAL flicker on the screen and
       demands red.  §3.6 of phase 11: *«every test of the list has,
       mandatorily, its injected fault, and that case must be
       run, not imagined»*.

  2. ⛔ **IT NO LONGER KNOWS WHAT PLASMA IS.**  `13-w4` waited for `plasmashell`,
     asked for `org.kde.Shutdown.logout` and watched `kwin_wayland` die:
     three names of ONE desktop inside the list of tests, which is precisely
     what this net does not allow (`fasi/11…` §3.7).
     ⇒ Now: the birth is read from the PRODUCT'S LOG (`negotiated
       format`, the same line as C1), the end too — ⚠ and in TWO forms,
       because the product has two and which of the two comes out depends on who
       dies with the gesture (see `RIGHE_FINITA` and `giudica_il_registro`) — ⭐ and
       the «Log out» gesture is
       ASKED OF THE MACHINE instead of guessed — with the same question
       the product asks (`src/sessione.c:285-310`: is there `startplasma-wayland`?
       is there `gnome-session`? is there `xfce4-session`?).

  3. ⛔ **THE TENANT HAS A NAME OF THE NET.**  `13-w4` called it `w4u$$`:
     outside the `c<n>[b]u<n>` name space, so ⛔ **the hook did not clear it
     out** and C19 did not see it.  ⇒ Here it is `c20u<n>`, and the two new
     meshes hold each other up.

⚠ `13-w4` stays in the repository: it is the document of the measurement of 22 September,
  and its diagnosis (the three alternating frames, the recycled descriptors) is not
  written anywhere else.

---------------------------------------------------------------------------
⚠ THE TWO NUMBERS OF THE PIXEL JUDGE, and where they come from
---------------------------------------------------------------------------

  · **8 levels** is how much two consecutive frames can differ in
    mean luminance without it being a flicker.  `[M]` 22 Sep 2026 on KDE: with a
    still desktop the tail of the video stays on **a single value**, and the flicker
    alternated between very distant values.  ⚠ The margin is wide on purpose: a
    tight threshold would catch the encoding noise.
  · **how many jumps are allowed depends on how long the tail is**: one
    every ten frames, at most three, ⭐ and **never fewer than one**.  ⛔ Between the
    end of the desktop startup and the tail there can be a panel that
    finishes drawing itself, and a red on that would be a false red.
  · ⚠ **HALF of the frames is not looked at**: the scene starts when the
    session has already been reborn, and `[M]` the first start of Firefox in a box
    exceeds 25 s (`LEZIONI.md` §1.45).  ⇒ The first part of the video is the
    bare desktop waiting for the browser, then there is the desktop→scene step, and
    only after that there is what this mesh wants to look at.  ⛔ «The first 30
    frames» were not enough: on kde that step falls around the thousandth.
  · ⛔ Below **40 decoded frames** no judgement is made: it is a **3**.
  · ⛔⛔ And if the **median** luminance of the tail stays below **40** *and* the
    screen is STILL, the screen is BLACK: the scene the mesh started
    did not arrive, ⇒ **3** and not a green.  ⚠ It is the same question C3 asks
    itself (*«is the scene I declared really on the screen?»*), and the reason is
    the same: ⭐ a black, still screen would pass *«the luminance is one»* with
    flying colours, that is the mesh would give away a green exactly when it has not
    seen anything.
    ⛔⛔ AND THE ORDER OF THE TWO CHECKS IS A DECISION: **first the flicker,
        then the black.**  `[M]` 23 Sep 2026, with the opposite order the injected
        fault came out **3** instead of red — C3's scene alternates blue
        (29) and yellow (226), so its MEDIAN is 17, and the mesh said
        «the screen is black, I do not judge» to a screen that was
        flickering under its eyes.  ⇒ A screen that ALTERNATES is never
        ambiguous, however dark it is: the real ghost is made exactly like that
        (desktop · logout screen · black).

  ⛔⛔ AND WHY THE SCENE IS NEEDED — `[M]` 23 September 2026, and it is the measurement
      that rewrote this mesh.  The second login, with the desktop STILL,
      delivers:

        | box | compositor | frames |
        |---|---|---|
        | **kde**  | KWin  | **1 800 in 45 s** |
        | **xfce** | labwc | ⛔ **7 in 60 s**  |

      ⇒ KWin delivers even without damage; labwc, like every compositor of the
        wlroots family, delivers only on DAMAGE (`fasi/09…` §3.1: 0,03
        frames/s with a still scene).  ⛔ On a still desktop this mesh
        would have been **3 for ever on xfce and on lxqt**, and a 3 that repeats
        is the cousin of the perpetual red (`LEZIONI.md` §1.49).
      ⭐ The cure is C3's: **the mesh puts the scene there, and
        declares it** — but here it must move WITHOUT changing the light, or the pixel
        judge would accuse the scene instead of the ghost.  It is in
        `11-c20-scena.html`, and there it is also written why the bands are
        two and not one.

⭐ And the flicker of the injected fault is DECLARED, not borrowed: the
  scene is `11-c3-scena.html`, which alternates the background between `#0000FF` (BT.601
  luminance ≈ 29) and `#FFFF00` (≈ 226).  ⇒ The jump is ~197 levels, that is
  ⭐ **twenty-four times** the threshold: a fault that passed by a hair would
  prove nothing.

Outcomes: 0 green · 1 red · 3 I could not look (⛔ it is NOT a red).
⛔ With `--scena-che-lampeggia` it reads THE OTHER WAY ROUND: 0 = the fault is SEEN.
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
# ⭐ THE TWO SCENES, and they are two on purpose (see the numbers box below).
#   · MINE moves and its light does NOT change   ⇒ the healthy run
#   · C3's alternates blue and yellow           ⇒ the INJECTED FAULT
SCENA_FERMA_DI_LUCE = os.path.join(QUI, "11-c20-scena.html")
SCENA_CHE_LAMPEGGIA = os.path.join(QUI, "11-c3-scena.html")

# ⭐ The product lines this mesh reads, in one place only: if the
#   product changes them, they are changed HERE (§1.47).
RIGA_NASCITA = "negotiated format"          # src/cattura.c
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE PRODUCT SAYS THE END OF THE GRAPHICAL SESSION IN TWO WAYS — and
#     which of the two depends on **who dies with the «Log out» gesture**, not on the name
#     of the desktop.
#
#   · the child SURVIVES the gesture  (KDE, XFCE: the compositor dies, not the
#     logind session)  ⇒ HE notices, «it was there and now it is not any more»
#         «the graphical session of «…» IS OVER»            src/figlio.c:2134
#   · the child DIES with the gesture  (GNOME: it is the LEADER process of the
#     logind session — it opens it with `pam_open_session` — and `gnome-session`
#     takes it away with signal 15)  ⇒ ⛔ it cannot report a fact that
#     kills it, and the PARENT says it at the moment it reaps it
#         «the stage of «…» has gone ⇒ the graphical session is over»
#                                                          src/main.c:1418
#
# ⛔⛔ AND THE SECOND IS NOT A FALLBACK TO LET GNOME PASS: it is written in the
#     product, in `src/main.c:1384-1396`, that at logout the child dies with
#     signal 15 and that **for this reason the child's line «never fired»**.
#     ⇒ Asking for only one meant demanding that the product said the
#       thing in the way of ONE desktop — and it is exactly the defect of `13-w4`
#       this mesh was born not to repeat (point 2 at the top of the file).
# `[M]` 23 Sep 2026, rete11-gnome: the gesture answers, the stage goes away in
#   0,1 s, the parent writes its line — and the mesh waited for the other one for
#   120 s and exited «I could not look».
# ═══════════════════════════════════════════════════════════════════════════
RIGHE_FINITA = (
    ("IS OVER", "the child survived and noticed"),
    ("has gone ⇒ the graphical session is over",
     "⛔ the child died with the gesture, and the parent said so while reaping it"),
)
RIGA_RINASCITA = "RESTARTING THE CAPTURE"       # src/figlio.c:8011
RIGA_BUTTA = re.compile(r"throwing away the (\d+) imported surfaces")  # src/codificatore.c
# ⭐ Who serves a session: «child spawned for «X»: pid N … serial M»
#   (`src/figlio.c:1744`).  ⛔ It serves to SAY, and not to deduce, that the
#   second login runs in a process DIFFERENT from the first one's.
RIGA_FIGLIO = re.compile(r"child spawned for «([^»]+)»: pid (\d+).*?"
                         r"serial (\d+)")

# ⚠ The numbers of the pixel judge — see the box at the top.
SOGLIA_SALTO = 8
FOTOGRAMMI_MINIMI = 40
# ⛔ Below this median luminance the screen is BLACK, and no judgement is made: a
#    still black and a frozen picture look exactly the same.
LUCE_MINIMA = 40
LARGHEZZA, ALTEZZA = 64, 24


def quanti_da_saltare(quanti):
    """⭐ The «before» not to look at: HALF of the frames.

    ⛔⛔ And half is not caution: the scene starts WHEN the session has
        already been reborn, and `[M]` the first start of Firefox in a box exceeds
        25 s (`LEZIONI.md` §1.45).  ⇒ The first part of the video is the bare
        desktop waiting for the browser, then there is the desktop→scene step, and only
        after that there is what this mesh wants to look at.
    ⚠ Cutting «the first 30 frames» was not enough: on kde that step falls
      around the thousandth.
    """
    return max(4, quanti // 2)


def salti_ammessi(quanti_coda):
    """⭐ How many jumps are not yet a flicker.

    ⛔ Not a fixed number: with a tail of 1 770 frames «3 jumps» is
       strict, with a tail of 10 it would allow a third of the
       screen to alternate.  ⚠ One however is always allowed: between the end
       of the startup and the tail there can be a panel that finishes
       drawing itself, and a red on that would be a false red.
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
# ⭐⭐ THE «LOG OUT» GESTURE, ASKED OF THE MACHINE — and not written per desktop.
#
# ⛔ The question is the SAME as the product's (`src/sessione.c:285-310`): which
#    graphical session is there in this box?  The product solves it by looking at
#    which programs exist, and here it is done the same way — ⇒ the day a box
#    changes desktop, this mesh follows it without anybody touching it.
# ⚠ And the gesture's command is the MENU's, not a `kill`: the mesh must
#   test the user's road, not a shortcut the product sees in
#   another way (`loginctl terminate-user` is not «Log out»).
# ═══════════════════════════════════════════════════════════════════════════
DESKTOP_E_GESTO = (
    # (name, marker that MUST be there, marker that must NOT be there, gesture)
    ("KDE Plasma", "startplasma-wayland", "gnome-session",
     "busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout"),
    ("GNOME", "gnome-session", None,
     "busctl --user call org.gnome.SessionManager /org/gnome/SessionManager "
     "org.gnome.SessionManager Logout u 1"),
    ("XFCE", "xfce4-session", None,
     "xfce4-session-logout --logout --fast"),
    # ⭐ LXQt — 24 Sep 2026, phase 14.  `[R]` The gesture is the D-Bus method that the
    #   LXQt «Log out» menu reaches, published by `lxqt-session` 2.1.1
    #   (trixie's, 2.1.1-1):
    #     service `org.lxqt.session`, object `/LXQtSession`
    #       https://github.com/lxqt/lxqt-session/blob/2.1.1/lxqt-session/src/sessionapplication.cpp
    #     interface `org.lxqt.session`, method `logout()` (Q_NOREPLY), which
    #     calls `m_manager->logout(true)`
    #       https://github.com/lxqt/lxqt-session/blob/2.1.1/lxqt-session/src/sessiondbusadaptor.h
    # ⛔ NOT `lxqt-leave --logout`: it opens a modal CONFIRMATION and waits for a click
    #    nobody gives ⇒ the mesh would exit 3 because of a dialog, not because of the
    #    product.
    # ⚠ The ORDER is not chance: it is AT THE END, so the three entries above are
    #   tried as before and choose as before.  And the markers do not
    #   clash: in the lxqt box there is no `xfce4-session` (nor
    #   `gnome-session`, nor `startplasma-wayland`), and in the other three there is
    #   no `lxqt-session` — ⇒ no entry captures another one's desktop.
    # ⚠ `--expect-reply=no`: the method is `Q_NOREPLY`, and Qt answers (if
    #   it answers) only AFTER `logout(true)` has stopped the modules — that is
    #   when `lxqt-session` is already exiting.  `[?]` Waiting for the answer,
    #   busctl would risk «Remote peer disconnected» and a code ≠ 0 ⇒ C20
    #   would say «the gesture did not answer» to a gesture that succeeded.  To be measured
    #   on the box.
    ("LXQt", "lxqt-session", None,
     "busctl --user --expect-reply=no call org.lxqt.session /LXQtSession "
     "org.lxqt.session logout"),
)


def come_si_esce():
    """⭐ (desktop name, gesture command) — or (None, why)."""
    def c_e(programma):
        r = sh("command -v %s >/dev/null 2>&1" % programma, 15)
        return r is not None and r.returncode == 0

    for nome, ci_vuole, non_ci_vuole, gesto in DESKTOP_E_GESTO:
        if not c_e(ci_vuole):
            continue
        if non_ci_vuole and c_e(non_ci_vuole):
            continue
        return nome, gesto
    return None, ("in this box there is neither startplasma-wayland, nor "
                  "gnome-session, nor xfce4-session, nor lxqt-session: I do not "
                  "know how «Log out» is said in here")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGES — PURE functions: `--certifica` goes through them without a machine.
# ═══════════════════════════════════════════════════════════════════════════
def giudica_i_pixel(luminanze):
    """⭐ (esito, salti, perche) from the sequence of mean luminances."""
    if luminanze is None:
        return 3, 0, "the video of the second login was not decoded"
    if len(luminanze) < FOTOGRAMMI_MINIMI:
        return 3, 0, ("only %d frames decoded (%d are needed): there is "
                      "no tail to look at"
                      % (len(luminanze), FOTOGRAMMI_MINIMI))
    coda = luminanze[quanti_da_saltare(len(luminanze)):]
    salti = sum(1 for a, b in zip(coda, coda[1:]) if abs(a - b) > SOGLIA_SALTO)
    ammessi = salti_ammessi(len(coda))
    valori = sorted(set(coda))
    mediana = sorted(coda)[len(coda) // 2]
    # ⚠ And MINIMUM, MEDIAN and MAXIMUM are printed besides the values: `[M]` 23 Sep
    #   2026 the first run printed only the eight lowest values, ⛔ and one
    #   could not tell whether the screen was black or only still — two things that a
    #   «the luminance is one» judge treats the same way.
    ordinata = sorted(coda)
    dice = ("%d frames, tail of %d: %d jumps beyond %d levels (%d are "
            "allowed) · luminance min %d · median %d · max %d · %d distinct "
            "values %s"
            % (len(luminanze), len(coda), salti, SOGLIA_SALTO, ammessi,
               ordinata[0], mediana, ordinata[-1],
               len(valori), valori[:6]))
    # ⛔⛔ AND THE ORDER OF THESE TWO CHECKS IS A DECISION, not chance:
    #     **first the flicker, then the black** — `[M]` 23 Sep 2026, and with the
    #     opposite order the injected fault came out **3** instead of red.
    #     C3's scene alternates blue (29) and yellow (226), ⇒ its MEDIAN is
    #     17: dark.  With the black check in front, the mesh said «the
    #     screen is black, I do not judge» to a screen that was flickering
    #     under its eyes.
    # ⇒ A screen that ALTERNATES is never ambiguous, however dark it is: the
    #   ghost is made like that (desktop · logout screen · black).  ⭐ It is
    #   the STILL black that cannot be told apart from a frozen picture,
    #   and only that becomes an «I could not look».
    if salti > ammessi:
        return 1, salti, ("the screen FLICKERS after the rebirth — " + dice)
    if mediana < LUCE_MINIMA:
        return 3, salti, ("the screen is BLACK and STILL (median luminance %d, "
                          "below %d): the scene I started did not arrive, "
                          "and a still black and a frozen picture look "
                          "the same — " % (mediana, LUCE_MINIMA) + dice)
    return 0, salti, ("with a still desktop the luminance is one — " + dice)


def chi_serviva(fetta, chi):
    """⭐ The pid of the child serving «chi» in this log slice — or None.

    ⚠ If there is more than one the LAST is taken: it is the one serving
      now.
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
    """⭐ (esito, quante, perche) from the log lines of THIS tenant.

    ═══════════════════════════════════════════════════════════════════════
    ⭐⭐ AND THE QUESTION IS DIFFERENT IN THE TWO CASES, because the DANGER is different.
    ⛔ It is not a threshold loosened to let GNOME pass: it is the same test
       asked of the fact that really has to be tested.

    `src/cattura.c:1318-1332`, the diagnosis of the real defect (22 Sep 2026, the
    user's test on KDE): *«after «Log out» and a new login the session
    is reborn IN THE SAME child: the capture is new, the encoder is not»* —
    ⇒ the recycled descriptors found again the surfaces of the dead session.

      · **the child SURVIVED** (KDE, XFCE) ⇒ the encoder is the
        SAME OBJECT as before, and the danger is all there: we demand that it
        threw away the cache — «throwing away the N imported surfaces».
        ⛔ If it did not throw it away it is RED, and it is the real defect.

      · **the child DIED with the gesture** (GNOME: it is the leader process
        of the logind session) ⇒ the encoder died with it, and ⛔ there is
        NO cache to throw away: the surfaces of the session before
        are in a process that no longer exists.
        ⭐ But saying it is not enough: we DEMAND THE PROOF, that is that the second
          login is served by a child with a **different pid** from the
          first one's.  ⛔ Without that pid no judgement (3), and if the pid were the
          same the child would not have died at all — ⇒ 3, the premise of the
          mesh does not hold.

    ⛔⛔ AND «RESTARTING THE CAPTURE» IS NOT LOOKED AT IN THE SECOND CASE: `[M]` 23 Sep
        2026 on rete11-gnome that line IS there anyway — the NEW child
        writes it, which at the first attempt does not find the stage and at the second does —
        ⇒ looking at it would mean reading a green from a line that talks about
        something else, which is the exact way a mesh stops looking.
    ═══════════════════════════════════════════════════════════════════════
    """
    if fetta is None:
        return 3, 0, "I could not read the server log"

    if figlio_morto:
        pid_adesso = chi_serviva(fetta, chi)
        if pid_adesso is None:
            return 3, 0, ("the child of «%s» had died with the «Log out» gesture and in the "
                          "log of the second login no other one is "
                          "born: I do not know who is serving this session"
                          % chi)
        if pid_di_prima is None:
            return 3, 0, ("I did not read the pid of the child of the FIRST login: "
                          "without it I cannot say that this one (%s) is another"
                          % pid_adesso)
        if pid_adesso == pid_di_prima:
            return 3, 0, ("the second login is served by the SAME child "
                          "as the first (pid %s), and the product had said it "
                          "was dead: the premise does not hold" % pid_adesso)
        return 0, 0, ("the child died with the gesture and the second login runs "
                      "in a NEW child (pid %s, before %s): the encoder "
                      "of the dead session no longer exists, and neither do its "
                      "surfaces"
                      % (pid_adesso, pid_di_prima))

    mie = [r for r in fetta if ("[%s]" % chi) in r]
    if not any(RIGA_RINASCITA in r for r in mie):
        return 3, 0, ("in the log there is no rebirth of the capture "
                      "(«%s») for «%s»: the new session was not born from an "
                      "old one, and there is nothing to judge"
                      % (RIGA_RINASCITA, chi))
    quante = 0
    for r in mie:
        m = RIGA_BUTTA.search(r)
        if m:
            quante += int(m.group(1))
    if quante > 0:
        return 0, quante, ("after the rebirth the encoder threw away %d "
                           "surfaces of the session before" % quante)
    return 1, 0, ("the capture was reborn but the encoder did NOT throw away the "
                  "cache: the surfaces of the dead session are still inside")


def giudizio(pixel, registro):
    """⭐ The mesh's outcome from the two judges.

    ⛔ A `3` from one of the two NEVER becomes a red: `LEZIONI.md` §1.49 —
       «I do not know» and «it does not hold» are two things, and confusing them is the way
       a net starts shouting while the product is perfectly fine.
    """
    ep, ip, _ = pixel
    er, ir, _ = registro
    if ep == 3 or er == 3:
        return 3
    if ep == 1 or er == 1:
        return 1
    return 0


def luminanze_dal_grezzo(dati):
    """⭐ The mean per frame from a gray 64x24 `rawvideo`."""
    n = LARGHEZZA * ALTEZZA
    if not dati or len(dati) < n:
        return None
    return [sum(dati[i * n:(i + 1) * n]) // n for i in range(len(dati) // n)]


# ═══════════════════════════════════════════════════════════════════════════
def sgombera(chi):
    sh("loginctl terminate-user %s >/dev/null 2>&1" % chi, 30)
    # ⛔ `[c]20u4` and not `c20u4`: `pkill -f` would catch the shell that is
    #    running it, and the shell would kill itself (22 Sep 2026).
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
    """⭐ We wait for the EVENT, not the clock.  Returns (quale, fetta).

    ⚠ `pezzi` is a piece of a line or a list of pieces: the first one that is
      seen wins, and **that one** is returned — so the caller can SAY which
      form the product used instead of just writing «I saw it».
    ⛔ A list is not a loosened threshold: it is the same question asked of the
       product in the forms in which the product can answer (RIGHE_FINITA).
    """
    if isinstance(pezzi, str):
        pezzi = (pezzi,)
    scadenza = time.time() + tetto
    fetta = []
    while time.time() < scadenza:
        righe = leggi(percorso)
        fetta = righe[segno:] if righe is not None else []
        for pezzo in pezzi:
            # ⚠ The name is in square brackets in the lines tagged per
            #   tenant, and in angle quotes in the parent's ones (the
            #   «IS OVER» line and the one of the stage that goes away): both
            #   forms are looked at.
            for r in fetta:
                if pezzo in r and (("[%s]" % chi) in r or ("«%s»" % chi) in r):
                    return pezzo, fetta
        time.sleep(0.5)
    return None, fetta


def il_cliente_c_e(porta, chi):
    """⛔⛔ `[c]20u2` AND NOT `c20u2`, and it is not a whim.

    The command line of the shell running this `pgrep` contains the name
    of the tenant ⇒ `pgrep -f` **catches itself**, and the wait «as long as the
    client is there» never ends.  ⚠ It is the same trap that on 22 Sep 2026
    made the shell kill itself (`11-gancio.sh`, `sgombera_inquilini`).
    ⭐ The square brackets count as an expression and not as text.
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
        return "(nothing)"
    return " ⏎ ".join(r.strip()[:90] for r in righe[-quante:] if r.strip())


def il_socket_di(chi):
    """⛔ The Wayland socket is LOOKED FOR, not guessed (§3.7)."""
    r = sh("id -u %s" % chi, 15)
    uid = (r.stdout or "").strip() if r else ""
    if not uid:
        return None, None
    rtd = "/run/user/%s" % uid
    r = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd, 15)
    d = (r.stdout or "").strip() if r else ""
    return rtd, (d or None)


def accendi_la_scena(chi, scena, applicazione, come, prefisso="   "):
    """⭐ Starts the DECLARED scene inside the freshly reborn session.

    ⛔⛔ AND IT IS STARTED IN BOTH RUNS, not only in the one with the fault —
        23 Sep 2026, and it is the measurement that decided it: the second login brings
        **1 800 frames in 45 s on kde** and **7 in 60 s on xfce**.  KWin
        delivers even with a still desktop, labwc (wlroots) delivers only on
        DAMAGE.  ⇒ Without a scene that moves, on xfce and on lxqt this
        mesh would have **nothing to look at**, for ever.
    ⭐ The scene of the healthy run (`11-c20-scena.html`) moves and its light does NOT
      change: all different frames, constant mean luminance.  ⇒ It is what
      the judge wants, and it is declared in that file.

    ⭐ `setsid` and stdin on `/dev/null`, like C3: without it, the browser gets
      SIGTTOU from the bench's terminal and stays stopped in `T` — `[M]` 22 Sep 2026,
      and it looked like a product that does not deliver.
    """
    # ═══════════════════════════════════════════════════════════════════
    # ⛔⛔ THE BROWSER'S PROVISION, AND IT COSTS A WHOLE RUN — 23 Sep 2026.
    #
    # `[M]` First run of the injected fault on kde: `firefox-esr` started
    # (`pgrep` found it), ⛔ and NOTHING arrived on the screen — 1800
    # frames, 0 jumps, the mesh said «the fault was not seen».
    # ⇒ The cause is the one C3 already paid for on 27 August 2026:
    #   `~/.cache/mozilla` -> `/tmp/mozilla`, left to ANOTHER tenant with
    #   mode 0700 ⇒ the browser stops on the profile choice window
    #   and never paints.  ⚠ An injected fault that does not bite because of the
    #   bench is worse than no fault: it says «the mesh is broken» while it is
    #   the bench that has not prepared the scene.
    # ⭐ The cure is in C2 (`cura_della_provvista`) and ⛔ NO copy of it is made
    #   here: the same rule in three files is three places to diverge from.
    # ═══════════════════════════════════════════════════════════════════
    c2 = _carica("11-c2-una-finestra-si-apre.py",
                 ("cura_della_provvista", "sgombra_il_mio_rimasuglio"))
    if c2 is None:
        return False, ("I cannot find `11-c2-una-finestra-si-apre.py` next to me: "
                       "the cure of the browser's provision comes from there, and "
                       "without it the scene does not start")
    fatto, perche_p = c2.cura_della_provvista(chi)
    if not fatto:
        return False, "the browser's provision is not ready: %s" % perche_p

    rtd, display = il_socket_di(chi)
    if display is None:
        return False, ("in %s there is no wayland socket: there is no "
                       "compositor the scene can talk to" % rtd)
    sh("setsid runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s --kiosk file://%s < /dev/null > /home/%s/.c20-scena.log 2>&1 &"
       % (chi, rtd, display, chi, applicazione, scena, chi), 30)
    for _ in range(40):
        r = sh("pgrep -u %s -f %s >/dev/null 2>&1" % (chi, applicazione), 15)
        if r is not None and r.returncode == 0:
            print("%s%s (%s on %s)"
                  % (prefisso, come, applicazione, os.path.basename(scena)))
            return True, ""
        time.sleep(0.25)
    return False, "the scene did not start: %s was not seen" % applicazione


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ Can the two judges say green, red and «I do not know»?"""
    guai = 0
    # ⭐ The healthy run: first the bare desktop (dark), then the step of the
    #   scene starting, then the scene — which moves and whose light does NOT
    #   change (~157, as `11-c20-scena.html` declares).
    sano = [20] * 100 + [157] * 100
    # ⚠ The encoding noise: ±3 levels, below the threshold ⇒ it is not a jump.
    rumore = [20] * 100 + [157 + (i % 7) - 3 for i in range(100)]
    # ⛔ The real flicker: blue (29) ⇄ yellow (226), like `11-c3-scena.html`.
    lampeggio = [20] * 100 + [29 if (i // 2) % 2 == 0 else 226
                              for i in range(100)]
    # ⚠ A single settling INSIDE the tail: it is NOT a flicker.
    assesta = [20] * 100 + [157] * 50 + [180] * 50
    # ⭐ The short tail of a compositor that delivers little (xfce/lxqt): 80
    #   frames in all, tail of 40.
    corto_sano = [20] * 40 + [150] * 40
    corto_lampeggio = [20] * 40 + [29 if (i // 2) % 2 == 0 else 226
                                   for i in range(40)]
    # ⛔⛔ AND THE CASE THAT MATTERS MOST: the BLACK, still screen.
    nero = [6] * 200
    # ⛔⛔ AND ITS EVIL TWIN, which on 23 Sep 2026 came out 3 instead of
    #   red: a DARK screen THAT ALTERNATES.  It is C3's scene seen by the
    #   capture (median 17) and it is also the shape of the real ghost.
    nero_che_alterna = [20] * 100 + [29 if (i // 2) % 2 == 0 else 6
                                     for i in range(100)]
    casi_pixel = [
        ("⭐ the declared scene, light ONE ⇒ GREEN", sano, 0),
        ("⭐ encoding noise below the threshold ⇒ GREEN", rumore, 0),
        ("⭐ a single settling (1 jump) ⇒ GREEN, ⛔ not a red", assesta, 0),
        ("⛔ the FLICKER (blue ⇄ yellow) ⇒ RED", lampeggio, 1),
        ("⭐ short tail (xfce/lxqt), light one ⇒ GREEN", corto_sano, 0),
        ("⛔ short tail that FLICKERS ⇒ RED all the same", corto_lampeggio, 1),
        ("⛔⛔ BLACK and STILL screen ⇒ 3 — ⛔ NEVER a green: the scene did not "
         "arrive", nero, 3),
        ("⛔⛔ dark screen that ALTERNATES ⇒ RED — ⛔ the flicker comes "
         "BEFORE the black", nero_che_alterna, 1),
        ("⚠ video too short (39 frames) ⇒ 3, ⛔ never a red",
         [157] * 39, 3),
        ("⚠ ffmpeg decoded nothing ⇒ 3", None, 3),
    ]
    print("== C20 — certification of the judgements (⛔ without touching the machine)")
    for nome, dato, atteso in casi_pixel:
        e = giudica_i_pixel(dato)[0]
        if e != atteso:
            guai += 1
        print("  %s PIXEL    %-62s outcome %s (expected %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    buono = ["figlio  [c20u1] ⭐⭐ RESTARTING THE CAPTURE: the stage came back",
             "codifica [c20u1] ⭐ throwing away the 4 imported surfaces: generation"]
    # ⭐ THE CHILD THAT SURVIVED — KDE, XFCE: the encoder is the same.
    casi_reg = [
        ("⭐ reborn, and the cache thrown away ⇒ GREEN", buono, 0),
        ("⛔ reborn and the cache NOT thrown away ⇒ RED", buono[:1], 1),
        ("⚠ no rebirth ⇒ 3, ⛔ never a red", buono[1:], 3),
        ("⚠ the lines belong to ANOTHER tenant ⇒ 3",
         [r.replace("c20u1", "c20u9") for r in buono], 3),
        ("⚠ the log cannot be read ⇒ 3", None, 3),
    ]
    for nome, dato, atteso in casi_reg:
        e = giudica_il_registro(dato, "c20u1", False, "111")[0]
        if e != atteso:
            guai += 1
        print("  %s LOG      %-62s outcome %s (expected %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    # ⭐⭐ THE CHILD THAT DIED WITH THE GESTURE — GNOME.  ⛔ Here green is NOT given away:
    #     the pid of a NEW child is demanded, and without it it is 3.
    nuovo = ["figlio  ⭐ child spawned for «c20u1»: pid 222, uid 4014, gid "
             "4014, serial 3.  ⛔ That it REALLY is that uid",
             "figlio  [c20u1] ⭐⭐ RESTARTING THE CAPTURE: the stage came back"]
    casi_morto = [
        ("⭐ NEW child (pid 222 ≠ 111) ⇒ GREEN", nuovo, "111", 0),
        ("⛔ no new child in the log ⇒ 3, ⛔ not a green",
         nuovo[1:], "111", 3),
        ("⛔ the SAME pid as before ⇒ 3: it had not died at all",
         nuovo, "222", 3),
        ("⚠ I do not know the pid of the first login ⇒ 3", nuovo, None, 3),
        ("⚠ the new child belongs to ANOTHER tenant ⇒ 3",
         [r.replace("c20u1", "c20u9") for r in nuovo], "111", 3),
        ("⚠ the log cannot be read ⇒ 3", None, "111", 3),
    ]
    for nome, dato, prima, atteso in casi_morto:
        e = giudica_il_registro(dato, "c20u1", True, prima)[0]
        if e != atteso:
            guai += 1
        print("  %s LOG/DEAD  %-61s outcome %s (expected %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    casi_somma = [
        ("⭐ both green ⇒ GREEN", (0, 0, ""), (0, 4, ""), 0),
        ("⛔ the pixels flicker ⇒ RED", (1, 60, ""), (0, 4, ""), 1),
        ("⛔ the cache not thrown away ⇒ RED", (0, 0, ""), (1, 0, ""), 1),
        ("⚠ an «I do not know» does NOT become a red", (3, 0, ""), (1, 0, ""), 3),
        ("⚠ nor from the other side", (1, 9, ""), (3, 0, ""), 3),
    ]
    for nome, p, r, atteso in casi_somma:
        e = giudizio(p, r)
        if e != atteso:
            guai += 1
        print("  %s SUM      %-62s outcome %s (expected %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    # ⭐ And the gesture: the table of desktops is tested by shape, not by trust.
    print("  %s the table of «Log out» gestures has %d desktops: %s"
          % ("OK " if len(DESKTOP_E_GESTO) == 4 else "NO ",
             len(DESKTOP_E_GESTO),
             ", ".join(d[0] for d in DESKTOP_E_GESTO)))
    print()
    if guai:
        print("⛔ %d cases of the judgements do NOT give what they must" % guai)
        return 1
    print("⭐ the two judges give green, red and «I do not know» where they must — and "
          "⛔ the declared\n   flicker (29 ⇄ 226) is red, while a "
          "single settling is not")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--scena-che-lampeggia", action="store_true",
                   help="⛔ THE INJECTED FAULT: in the second login C3's scene "
                        "is started ⇒ the screen really flickers, and the "
                        "pixel judge MUST give red")
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--scena", default=SCENA_FERMA_DI_LUCE,
                   help="the scene of the HEALTHY RUN: it moves, and its light does not "
                        "change")
    p.add_argument("--scena-guasta", default=SCENA_CHE_LAMPEGGIA,
                   help="the scene of the INJECTED FAULT: C3's, which "
                        "alternates blue and yellow")
    p.add_argument("--applicazione", default="firefox-esr")
    p.add_argument("--primo", type=float, default=90.0,
                   help="how long the FIRST client stays connected (it must "
                        "survive the «Log out»: the child notices "
                        "when someone is WATCHING)")
    # ⚠ 75 s, and the number comes from the BROWSER: the scene starts when the
    #   session has already been reborn, and `[M]` the first start of Firefox in a
    #   box exceeds 25 s (`LEZIONI.md` §1.45).  ⇒ The judge throws away the
    #   first half of the video, so the tail starts around the 37th second:
    #   a dozen seconds AFTER the scene is on the screen.
    p.add_argument("--secondo", type=float, default=75.0)
    p.add_argument("--attesa-nascita", type=float, default=120.0)
    # ⚠ 120 s and not 60: `[M]` 23 Sep 2026, on **xfce** the gesture answers at once
    #   but the session takes longer to really end — one run came out 3
    #   («the product did not declare the session over») and the next run,
    #   identical, declared it.  ⛔ A ceiling too tight produces 3s that
    #   look like the product's and are the bench's (§1.45).
    p.add_argument("--attesa-uscita", type=float, default=120.0)
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.porta:
        print("⛔ it wants `--porta` ⇒ I could not look")
        return 3
    if os.geteuid() != 0:
        print("⛔ it wants the administrator (it creates a tenant) ⇒ I could not "
              "look")
        return 3

    chi = "c20u%d" % random.randint(100, 999)
    innestato = (" ⛔ INJECTED FAULT: --scena-che-lampeggia"
                 if a.scena_che_lampeggia else "")
    print("== C20 — rebirth after «Log out» brings no ghosts (%s, port "
          "%d)%s" % (chi, a.porta, innestato))

    desktop, gesto = come_si_esce()
    if desktop is None:
        print("   ⛔ %s ⇒ I could not look" % gesto)
        return 3
    print("   the desktop of this box: %s — «Log out» is said like this:\n"
          "      %s" % (desktop, gesto))
    if leggi(a.registro) is None:
        print("   ⛔ I cannot read %s ⇒ I could not look" % a.registro)
        return 3
    # ⭐ The scene of this run: the declared one, or C3's if the
    #   fault is injected.  ⛔ Without the file nothing starts, and without a
    #   scene this mesh has nothing to judge ⇒ 3, not a green.
    scena = a.scena_guasta if a.scena_che_lampeggia else a.scena
    come = ("⛔ the flicker is on (#0000FF ⇄ #FFFF00)"
            if a.scena_che_lampeggia
            else "⭐ the scene is on: it moves, and its light does not change")
    if not os.path.exists(scena):
        print("   ⛔ the scene %s is missing ⇒ I could not look" % scena)
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
            print("   ⛔ I could not create the tenant ⇒ I could not "
                  "look")
            return 3
        # ⭐ The card groups: without them, the session is born blind and this
        #   mesh would say «I could not look» because of the bench.
        #   ⛔ And it is not rewritten here: it is the tool they all use (§1.47).
        c1 = _carica("11-c1-nasce-e-si-vede.py", ("garantisci_i_gruppi",))
        if c1 is None:
            print("   ⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me: "
                  "without the card groups\n      the session is born blind "
                  "⇒ I could not look")
            return 3
        eg, perche_g = c1.garantisci_i_gruppi(chi, "      ")
        if eg != 0:
            print("   ⛔ %s ⇒ I could not look" % perche_g)
            return 3

        # ── 1. THE FIRST LOGIN, and it stays connected during «Log out» ────
        # ⛔ `[M]` 22 Sep 2026: the child notices the logout when
        #    someone is WATCHING.  The user's gesture was exactly this.
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0
        sh("setsid python3 -u %s --indirizzo 127.0.0.1 --porta %d --utente %s "
           "--parola %s --resta %s < /dev/null > %s/uno.txt 2>&1 &"
           % (CLIENTE, a.porta, chi, PAROLA, a.primo, dove), 30)
        nato, fetta_uno = aspetta_la_riga(a.registro, segno, chi, RIGA_NASCITA,
                                          a.attesa_nascita)
        if not nato:
            print("   ⛔ in %d s the log did not say «%s» for «%s»: the "
                  "session was not born\n      ⇒ I could not look"
                  % (a.attesa_nascita, RIGA_NASCITA, chi))
            return 3
        # ⭐ WE NOTE WHO IS SERVING NOW, and it is needed later: if the «Log out»
        #   gesture kills the child (GNOME), the only proof that the surfaces
        #   of the dead session cannot survive is that the second
        #   login runs in a process with a pid DIFFERENT from this one.
        pid_di_prima = chi_serviva(fetta_uno, chi)
        print("   ⭐ first login: the session of «%s» was born, and the client "
              "is watching (served by child pid %s)"
              % (chi, pid_di_prima or "?"))
        time.sleep(10)

        # ── 2. «LOG OUT», the menu gesture ─────────────────────────────────
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0
        rtd, _ = il_socket_di(chi)
        r = sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s "
               "DBUS_SESSION_BUS_ADDRESS=unix:path=%s/bus %s"
               % (chi, rtd, rtd, gesto), 60)
        if r is None or r.returncode != 0:
            print("   ⛔ the «Log out» gesture of %s did not answer: %s ⇒ I could "
                  "not look"
                  % (desktop, ((r.stderr or r.stdout).strip().replace("\n", " ")[:120])
                     if r else "no answer"))
            return 3
        finita, _ = aspetta_la_riga(a.registro, segno, chi,
                                    [p for p, _d in RIGHE_FINITA],
                                    a.attesa_uscita)
        if not finita:
            print("   ⛔ %d s after «Log out» the product did not declare the "
                  "session over ⇒ I could not look\n"
                  "      and I waited for both of them: %s"
                  % (a.attesa_uscita,
                     " · ".join("«%s»" % p for p, _d in RIGHE_FINITA)))
            return 3
        # ⭐ We SAY which of the two forms the product used: it is the
        #   difference between «the child is alive» and «the child died with the
        #   gesture», and the log judge below depends on it.
        figlio_morto = (finita != RIGHE_FINITA[0][0])
        print("   ⭐ «Log out»: the product saw the graphical session end "
              "— %s" % dict(RIGHE_FINITA)[finita])
        # ⛔⛔ AND HERE WE WAIT FOR THE FIRST CLIENT TO HAVE REALLY LEFT.
        #    `[M]` 23 Sep 2026, first run: the wait was a fixed 30 s, the
        #    client stayed attached until its `--resta`, ⇒ the second
        #    login arrived while the first was still inside and the
        #    new session was not born: **outcome 3, and it was not the product's**.
        #    ⚠ The ceiling is tied to `--primo`, not borrowed: one knows
        #      when the first client would end by itself anyway.
        if not aspetta_che_il_cliente_se_ne_vada(a.porta, chi, a.primo + 30):
            print("   ⛔ the first client is still attached after %d s ⇒ I "
                  "could not look\n      its last line: %s"
                  % (a.primo + 30, coda_di(os.path.join(dove, "uno.txt"))))
            return 3
        print("   ⭐ the first client has left: %s"
              % coda_di(os.path.join(dove, "uno.txt"), 1))
        time.sleep(2)

        # ── 3. THE NEW LOGIN, with the video written ───────────────────────
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0
        sh("setsid python3 -u %s --indirizzo 127.0.0.1 --porta %d --utente %s "
           "--parola %s --resta %s --video-scrivi %s < /dev/null > %s/due.txt "
           "2>&1 &" % (CLIENTE, a.porta, chi, PAROLA, a.secondo, video, dove), 30)
        rinato, _ = aspetta_la_riga(a.registro, segno, chi, RIGA_NASCITA,
                                    a.attesa_nascita)
        if not rinato:
            print("   ⛔ in %d s the new session was not born ⇒ I could not "
                  "look\n      the second client says: %s"
                  % (a.attesa_nascita, coda_di(os.path.join(dove, "due.txt"))))
            return 3
        acceso, perche_s = accendi_la_scena(chi, scena, a.applicazione, come)
        if not acceso:
            print("   ⛔ %s ⇒ I could not look" % perche_s)
            return 3
        # ⚠ We wait for the client to have finished writing: the video is the
        #   only witness, and reading it half-way would be a shorter measurement.
        aspetta_che_il_cliente_se_ne_vada(a.porta, chi, a.secondo + 60)

        fetta = leggi(a.registro)
        fetta = fetta[segno:] if fetta is not None else None
        if not os.path.exists(video) or os.path.getsize(video) == 0:
            coda = ""
            t = leggi(os.path.join(dove, "due.txt"))
            if t:
                coda = t[-1].strip()[:110]
            print("   ⛔ the second login wrote no video (%s) ⇒ I could not "
                  "look" % coda)
            return 3
        print("   ⭐ second login: %d bytes of video"
              % os.path.getsize(video))

        # ── the judges ─────────────────────────────────────────────────────
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
            # ⛔ The other way round, and it is said out loud: here 0 is the good news.
            if esito == 1:
                print("⭐ THE INJECTED FAULT WAS SEEN — this mesh CAN "
                      "give red,\n   ⭐ and for the right reason: %s" % pixel[2])
                return 0
            if esito == 3:
                print("⚠ with the injected fault I could NOT look\n"
                      "   ⇒ outcome 3, not a green")
                return 3
            print("⛔⛔ THE INJECTED FAULT WAS NOT SEEN: the screen "
                  "really flickered\n   (blue ⇄ yellow) and the mesh said "
                  "green all the same.")
            return 1
        if esito == 0:
            # ⚠ And the second judge is quoted with ITS words: saying «the cache
            #   was thrown away» where the child had died with the gesture would be
            #   telling a fact that did not happen (on GNOME there was
            #   no cache to throw away — ⭐ there was a new process).
            print("⭐ GREEN — after «Log out» and the new login the screen is "
                  "clean\n   ⭐ and %s" % registro[2])
        elif esito == 1:
            print("⛔⛔ RED — %s"
                  % (pixel[2] if pixel[0] == 1 else registro[2]))
        else:
            print("⚠ I could not look — %s"
                  % (pixel[2] if pixel[0] == 3 else registro[2]))
        return esito
    finally:
        # ⛔ The `/tmp/mozilla` that the provision cure put there is removed
        #    ONLY if it was left to a tenant of mine: deleting the one of
        #    another mesh would make it fall (C14, the boxes in parallel).
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
