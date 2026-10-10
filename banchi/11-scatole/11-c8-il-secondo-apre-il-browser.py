#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c8 — ⭐⭐⭐ «THE SECOND USER OPENS THE BROWSER»
===========================================================================

    python3 11-c8-il-secondo-apre-il-browser.py
    python3 11-c8-il-secondo-apre-il-browser.py --senza-cura
    python3 11-c8-il-secondo-apre-il-browser.py --certifica

⛔ It is ACCEPTANCE TEST B of phase 11.  ⭐ It is also, according to both external
   reviewers, **the most important test of the list** — and in the first draft it was
   also the hardest to run.  ⇒ The user untied the knot on 26
   August 2026 (`DECISIONI.md` §4.6-terdecies):

       *«As far as I am concerned a container can even have 10 users,
         it is a figure already measured with GNOME.»*

   ⇒ ⭐ **C8 sits in a box, with TWO tenants.**  Not ten: the question is
     CORRECTNESS with several users, not capacity — that is already measured and
     is not redone.

---------------------------------------------------------------------------
⛔⛔ THE FAULT THIS MESH MUST CATCH — and whose fault it is
---------------------------------------------------------------------------

`DECISIONI.md` §4.6-undecies, and the user's correction that changes its
target:

  · `/etc/skel/.cache` of that machine is a LINK to `/tmp`.
    ⭐⭐ And **IT IS NOT A FAULT**: it is a **deliberate choice** of the owner about
    how his operating system must work.  ⛔ There is nothing to
    repair, and this test does not repair it.
  · ⛔ **The defect is OURS**: it is the product that creates the tenants with
    `useradd -m`, which copies the skeleton ⇒ they are ALL born writing in the
    same place.  Firefox keeps the local profile under `$HOME/.cache/mozilla`
    = `/tmp/mozilla`, and ⛔ **the first one who opens the browser takes it with mode
    0700**: from the second on the profile is not born, and the window that opens
    says *«Your Firefox profile cannot be loaded»*.

⇒ ⭐ **The target of the test is not the link**: it is *«does the second user
  open the browser, yes or no?»*, on a machine configured as its
  owner wants it.  ⛔ Looking at the link would be looking at the CAUSE we
  believe we know instead of the EFFECT we care about — and the cure
  could change without the test noticing.

---------------------------------------------------------------------------
⭐ HOW IT JUDGES — in the PIXEL, and without knowing what a desktop looks like
---------------------------------------------------------------------------

⛔ The process count is of no use: `[M]` it said «1» with the window and without.
⛔ «Firefox is alive» is of no use: in the fault Firefox **is alive**, and shows an
   error dialog.

⇒ The test opens in the browser a page of **colour `#FF00FF`** (`11-c8-pagina.html`)
  and looks at **how much of the screen has turned that colour**, with a **declared
  tolerance** — because compositors apply profiles and rescaling, and a
  `#FF00FF` comes back slightly different (§4.3, Gemini's finding).

And we look **BEFORE and AFTER**, not only after:

    before: the session is alive and the desktop is DRAWN (judge of 10-f1)
    after : a wide slice of the screen is the colour of the page

⛔ The «before» is not ceremony: without it, a desktop that is not even born would give
   the very same outcome as a browser that does not start — ⚠ two different faults
   with the same face, which is the way this project has already lost
   two diagnoses.

---------------------------------------------------------------------------
⛔ HOW I KNOW IT CAN SAY RED — `--senza-cura`
---------------------------------------------------------------------------

`fasi/11…` §4.1, column «how I know it can say red»: *«the provisioning cure is
undone ⇒ red»*.

  without `--senza-cura` the tenants receive the cure of `src/provisiona.sh`:
                        a REAL `~/.cache`, their own folder, mode 0700
  with `--senza-cura`   ⛔ the cure is NOT applied: the two are born as the
                        code of 25 August 2026 made them ⇒ **the second must give
                        RED**, or this mesh is useless

⚠ And it prepares the terrain by itself: the box starts with a clean
  `/etc/skel`, and this test puts the link to `/tmp` in it — ⛔ i.e.
  **it reproduces the configuration of the real machine**, which is the only one on
  which the question makes sense.  ⇒ Testing on a clean skeleton would mean
  answering an easier question than the real one (§3.5).

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: BOTH tenants opened the browser
  1  I looked: at least one did NOT make it             ⇒ red
  3  ⛔ I could not look (the server was not there, the judge was not there,
     no frame arrived) — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 IS THE HOME OF THE TWO STEPS COMMON TO ALL NINE MESHES — §1.47
#
# ⛔ It is not convenience: a line repeated in nine files is **nine places to
#    diverge from**, and they had already diverged.  From `11-c1-nasce-e-si-vede.py`:
#
#   · `e_stato_ammesso(coda)`   — «was the client ADMITTED?», which ⛔ is not
#        the word inside a text: the client prints it also in the TWO refusal
#        messages, and on stdout (`01-b3-cliente.py:1315`, `:1322`, `:2560`).
#   · `garantisci_i_gruppi(chi)` — the groups of the `/dev/dri` nodes, ⛔ without
#        which `[M]` the session is born BLIND (0 of 4, zero frames,
#        `fasi/10-…` §7.4) and this mesh would measure the darkness.
#
# ⛔ If C1 does not load we exit **3** and say so: ⛔ we do not silently fall back
#    on a poorer judgement.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_C1 = ("e_stato_ammesso", "certifica_ammissione",
                "garantisci_i_gruppi", "verdetto_gruppi", "certifica_gruppi")
_C1 = None


def _carica_c1():
    """⛔ It is a LOADER, not a judge: it finds the file, it decides nothing.

    ⚠ It is looked for next to me (in the box everything is in `/opt/remotix`) and one
      level up, because in the repository this mesh sits in
      `banchi/11-scatole/`.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "11-c1-nasce-e-si-vede.py")
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location("c1_comune", perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ We VERIFY that what is needed is there, we do not trust the name of the
        #    file (`CODER.md` §3.9).
        for mestiere in _MESTIERI_C1:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   come the admission predicate and the guarantee of the")
        print("   card's groups — which live in one place only (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔ `False` is not a product red: a client turned away is a client
       turned away, and the caller says «I could not look» (**3**).
    """
    return casa_di_c1().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ THE CARD'S GROUPS — `(esito, perche)`; `0` = it can be measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification — E1, «written is not in
       force».  ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids
       from the NODES and reads back comparing the numbers.  ⛔ No copy of it is made here.
    """
    return casa_di_c1().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ THE COLOUR OF THE TARGET AND ITS TOLERANCE — declared here and printed in
#    every outcome, because «the browser drew» is a verdict, and a
#    verdict without its yardstick is an opinion.
#
# ⚠ The tolerance is NOT generic prudence: `fasi/11…` §4.3 accepts Gemini's
#   finding — compositors apply colour profiles, the chain goes through
#   an H.264 encoding in 4:2:0 (which subsamples precisely the chroma, i.e. the
#   channel where the whole difference between magenta and non-magenta lies), and demanding
#   the exact colour would mean a test already dead.
# ⛔ And the tolerance is CALIBRATED, not chosen: `--certifica` contains the case
#   «colour shifted by as much as the tolerance allows ⇒ must stay GREEN» — which
#   is the same guard C1 has on the image threshold.
# ---------------------------------------------------------------------------
COLORE = (0xFF, 0x00, 0xFF)
TOLLERANZA = 48          # per channel, in levels 0..255
FRAZIONE_MINIMA = 0.25   # how much of the screen must be that colour

# ⚠ 0.25 and not 0.90: between the window edge, the GNOME bar and the
#   decorations, the full-screen browser never covers everything.  ⛔ And a
#   threshold too high would break at the first desktop with a wider bar,
#   i.e. precisely at phase 12 — which is what this phase exists to avoid.


def giudice_immagini():
    """⭐ The pixel judge is IMPORTED, not rewritten.

    ⛔ `10-f1-testimone.py` is already calibrated on the real thing (25 August 2026: black
       desktop measured, threshold of «near-black» put in the middle of the gap between the two
       worlds).  Rewriting a copy here would mean having two judges that
       can diverge silently — and the day they diverge, the red would be
       given by the wrong one.
    ⇒ If it is not there, this test exits **3**: «I could not look».  ⛔ We do not
      fall back on a poorer judgement without saying so.
    """
    perc = os.path.join(QUI, "10-f1-testimone.py")
    if not os.path.exists(perc):
        return None
    spec = importlib.util.spec_from_file_location("testimone10f1", perc)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception:
        return None
    return m


def frazione_del_colore(percorso, colore=COLORE, tolleranza=TOLLERANZA):
    """How much of the image is of the colour looked for, within the tolerance.

    ⛔ Returns **`None`** if it could not look — a file that is not there, an empty
       file, `numpy`/`Pillow` missing, a truncated PNG.  ⚠ `None` is not
       «zero»: «I did not look» and «I looked and it was not there» are two
       different things, and this project has already paid for confusing them.
    """
    if not percorso or not os.path.exists(percorso) \
            or os.path.getsize(percorso) == 0:
        return None
    try:
        import numpy as np
        from PIL import Image
        img = np.asarray(Image.open(percorso).convert("RGB")).astype("int16")
    except Exception:
        return None
    if img.ndim != 3 or img.shape[2] != 3 or img.size == 0:
        return None
    # ⚠ The distance is taken **channel by channel** (max norm) and not
    #   as a sum: a sum would let through a colour very wrong on a single
    #   channel, provided it is right on the other two.
    scarto = np.abs(img - np.array(colore, dtype="int16")).max(axis=2)
    return float((scarto <= tolleranza).mean())


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE JUDGE'S CERTIFICATION — it proves that it CAN give red, and green
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ And it declares what it covers and what it does not.

    COVERS: the pixel reader — that the colour is found when it is there, that it is NOT
    found when it is not, ⭐ that an image **shifted by as much as the
    tolerance allows** stays GREEN (or the threshold is too tight and the mesh
    gets thrown away in two weeks), and that «I did not look» returns `None`.
    ⛔ DOES NOT COVER: that the browser really started.  That is said by
    `--senza-cura` on the real thing, and it is the other half of the acceptance test.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("⛔ numpy or Pillow is missing: I cannot even certify myself")
        print("   ⇒ I could not look")
        return 3
    import tempfile

    lav = tempfile.mkdtemp(prefix="c8cert-")

    def dipingi(nome, riempi, macchia=None):
        a = np.zeros((216, 384, 3), dtype="uint8")
        a[:, :] = riempi
        if macchia is not None:
            a[80:136, 100:284] = macchia
        p = os.path.join(lav, nome + ".png")
        Image.fromarray(a).save(p)
        return p

    # ⭐ The cases, and each one is there for a reason that can be said in one line.
    casi = []
    # 1. the whole page is there: the browser drew
    casi.append(("whole page",
                 dipingi("a", COLORE, (0, 0, 0)), True))
    # 2. the desktop without browser: no magenta
    casi.append(("desktop without browser",
                 dipingi("b", (58, 62, 70), (200, 200, 200)), False))
    # 3. ⭐ THE CASE THAT CALIBRATES THE THRESHOLD: the colour comes back SHIFTED —
    #    colour profiles, 4:2:0, rescaling.  It must stay GREEN.
    spostato = tuple(min(255, max(0, c + s))
                     for c, s in zip(COLORE, (-30, +30, -30)))
    casi.append(("colour shifted by %s (must be GREEN)" % (spostato,),
                 dipingi("c", spostato, (0, 0, 0)), True))
    # 4. and one shifted TOO MUCH must not pass, or the tolerance no longer separates
    troppo = (0xFF, 0x90, 0xFF)
    casi.append(("colour shifted TOO MUCH %s (must be RED)" % (troppo,),
                 dipingi("d", troppo, (0, 0, 0)), False))
    # 5. the black screen: it is a red, not an «I do not know»
    casi.append(("black screen", dipingi("e", (0, 0, 0)), False))
    # 6. ⛔ the window is there but covers little: below the minimum fraction
    piccola = np.zeros((216, 384, 3), dtype="uint8")
    piccola[:, :] = (58, 62, 70)
    piccola[10:40, 10:80] = COLORE          # ~2.7 % of the screen
    pp = os.path.join(lav, "f.png")
    Image.fromarray(piccola).save(pp)
    casi.append(("a small spot is not a page", pp, False))

    print("== certification of C8's judge ==")
    print("   colour %s · tolerance ±%d per channel · minimum fraction %.2f"
          % (COLORE, TOLLERANZA, FRAZIONE_MINIMA))
    guai = 0
    for nome, png, atteso in casi:
        fr = frazione_del_colore(png)
        visto = (fr is not None and fr >= FRAZIONE_MINIMA)
        ok = (visto == atteso)
        print("  %s  %-52s  fraction=%s  ⇒ %s (expected %s)"
              % ("OK " if ok else "NO ", nome,
                 "unknown" if fr is None else "%.3f" % fr,
                 "page" if visto else "nothing",
                 "page" if atteso else "nothing"))
        if not ok:
            guai += 1

    # 7. ⛔ And the case worth more than all: «I could not look» must be
    #    `None`, not zero.  A file that is not there is NOT a screen without a page.
    for nome, perc in (("the file is not there", os.path.join(lav, "manca.png")),
                       ("the file is empty", os.path.join(lav, "vuoto.png"))):
        if "empty" in nome:
            open(perc, "wb").close()
        fr = frazione_del_colore(perc)
        ok = fr is None
        print("  %s  %-52s  fraction=%s  ⇒ %s (expected «I do not know»)"
              % ("OK " if ok else "NO ", nome,
                 "unknown" if fr is None else "%.3f" % fr,
                 "unknown" if fr is None else "a number"))
        if not ok:
            guai += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE CARD'S GROUPS — ⛔ the case that was missing before today.
    #
    # ⛔ A tenant outside the groups of the `/dev/dri` nodes makes a
    #    BLIND session be born (`[M]` 0 of 4, zero frames, `fasi/10-…` §7.4) ⇒
    #    this mesh would measure the darkness.  ⭐ It is demanded that it says «I could
    #    not look», ⛔ and NEVER red: it is a fault of the BENCH (§1.51).
    # ⚠ The cases live in C1, with the step they certify: ⛔ a copy here
    #   would be a second place to diverge from (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    guai_gr, _quanti_gr = casa_di_c1().certifica_gruppi("C8")
    guai += guai_gr

    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d cases wrong" % guai)
        return 1
    print("⭐ the judge sees the page when it is there, does not see it when it is not,")
    print("   ⭐ withstands a colour shift, and says «I do not know» instead of zero")
    print("   ⭐ and the CARD'S GROUPS: a tenant that cannot see makes it say "
          "«I could not look», ⛔ never red")
    print("⚠ and this certification covers THE READER, not the browser (see the top)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# THE TERRAIN — it is prepared, and ⛔ it is VERIFIED to be in force (E1)
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=120):
    return subprocess.run(["/bin/sh", "-c", comando],
                          capture_output=True, text=True, timeout=secondi)


def sgombra_il_posto_condiviso(base):
    """⛔ «From zero» also means: **what the previous round left**.

    `[M]` The defect lives in `/tmp/mozilla`, which the first tenant takes with
    mode 0700.  ⇒ If it stayed there from the previous round, the FIRST tenant of the
    new round would fail like the second — i.e. the test would say red for the
    wrong reason, and whoever reads would conclude something false.

    ⚠⚠ And ONLY what belongs to a tenant of THIS test is removed.  ⛔ A
       plain `rm -rf /tmp/mozilla` would delete anyone else's profile —
       and it is exactly the rule `src/provisiona.sh` gave itself
       («do not touch the `/tmp/mozilla` of whoever already has it: it is not ours and
       we do not know who uses it»).  Here it holds the same: outside the box this line
       would be damage.
    """
    p = "/tmp/mozilla"
    chi = sh("stat -c %%U %s 2>/dev/null" % p).stdout.strip()
    if not chi:
        return None
    if not chi.startswith(base):
        return "⚠ %s belongs to «%s», who is not a tenant of this test: I do NOT touch it" % (p, chi)
    sh("rm -rf %s" % p)
    return "cleared %s, which had been left to «%s» from the previous round" % (p, chi)


def prepara_lo_scheletro():
    """⭐ Reproduces the configuration of the REAL MACHINE: `/etc/skel/.cache`
    as a link to `/tmp`.

    ⛔ And it is not «introducing a fault»: it is a **choice of the owner of the
       machine**, and the test that runs on a clean skeleton answers an
       easier question than the real one.
    """
    sh("rm -rf /etc/skel/.cache && ln -s /tmp /etc/skel/.cache")
    r = sh("readlink /etc/skel/.cache")
    return r.stdout.strip()


def crea(chi, parola):
    """Creates the tenant **as the product creates it**: `useradd -m`.

    ⛔ `-m` copies the skeleton, and it is precisely the step from which the
       defect is born.  Using a cleaner road here would mean testing a
       product different from the one delivered.
    """
    sh("loginctl terminate-user %s 2>/dev/null; pkill -KILL -u %s 2>/dev/null; "
       "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi, chi, chi))
    # ⛔⛔ THE CARD'S GROUPS ARE NO LONGER INSIDE THE `useradd`.
    #     `usermod -aG video,render` nailed down two names — which belong to ONE
    #     distribution — and ⛔ **did not read back**: a successful `usermod` does not
    #     mean «it is in there» (E1, «written is not in force»).
    # ⭐ They are given by `attrezzi-gruppi-scheda.sh`, which READS them from the `/dev/dri` nodes and
    #   then VERIFIES comparing the numbers.  ⇒ Here there is no longer any group
    #   name and no number.
    # ⛔ And without them, `[M]` the session is born BLIND (0 of 4, zero frames,
    #   `fasi/10-…` §7.4): this mesh would measure the darkness and call it
    #   a product defect.  ⇒ We do not measure: the caller exits **3**.
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
    if r.returncode != 0:
        return False, (r.stderr or "").strip()[:120]
    e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="      ")
    if e_gr != 0:
        return False, perche_gr
    return True, ""


def applica_la_cura(chi):
    """⭐ The same lines as `src/provisiona.sh`, and not a paraphrase of them.

    ⚠ `/etc/skel` is not touched and the `/tmp/mozilla` of whoever already has it
      is not touched: a real `~/.cache` is given ONLY to the users we create.
    """
    c = "/home/%s/.cache" % chi
    sh("[ -L %s ] && rm -f %s; mkdir -p %s; chown %s:%s %s; chmod 700 %s"
       % (c, c, c, chi, chi, c, c))


def sa_scrivere_nella_cache(chi):
    """⛔ «written is not in force» (E1): the link is not looked at, we
       TRY TO WRITE.

    ⚠⚠ AND WE WRITE IN `~/.cache/**mozilla**`, not in `~/.cache` — and it is a
       correction, not a detail.  `[M]` 26 August 2026: the first draft
       tried to write in `~/.cache`, which with the link is `/tmp`, ⛔ and
       `/tmp` is writable by anyone (mode 1777).  ⇒ The predicate said
       **yes** also to the second tenant, i.e. **it never saw the defect**.
    ⭐ The place that bites is `/tmp/mozilla`, which the FIRST one takes with mode 0700
      — and it is exactly the measurement of `src/provisiona.sh`: *«from `provanic3`,
      `mkdir -p ~/.cache/mozilla` → Permission denied»*.
    """
    r = sh("su -s /bin/sh -c 'mkdir -p ~/.cache/mozilla/.prova-c8 && "
           "rmdir ~/.cache/mozilla/.prova-c8' %s" % chi)
    return r.returncode == 0


# ═══════════════════════════════════════════════════════════════════════════
# THE GRAB — attaching to the session and pulling a PNG out of it, ⛔ IN HERE
# ═══════════════════════════════════════════════════════════════════════════
def scatta(chi, parola, fuori, a, resta):
    """Returns (png|None, how_many_frames|None, why).

    ⛔ Three outcomes and not two: «the PNG is there», «no frame arrived»,
       «the frames arrived but no image was made of them» — and the last
       two are *«I did not look»*, not «the screen was empty».
    """
    flusso = fuori + ".264"
    for f in (flusso, fuori):
        if os.path.exists(f):
            os.unlink(f)
    r = subprocess.run(
        ["python3", "-u", a.cliente,
         "--indirizzo", a.indirizzo, "--porta", str(a.porta),
         "--utente", chi, "--parola", parola,
         "--video-scrivi", flusso, "--resta", str(resta)],
        capture_output=True, text=True, timeout=int(resta) + 120)
    coda = (r.stdout or "") + (r.stderr or "")
    quanti = None
    for riga in coda.splitlines():
        if "[vid]" in riga and "no frame" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    # ⛔⛔ BEFORE BLAMING THE WIRE, WE LOOK AT WHETHER THE CLIENT GOT IN.
    #
    # ⚠ Until 27 August 2026 this mesh did not ask at all: ⇒ a
    #   credentials REFUSAL came out as *«no frame arrived from the
    #   wire»* — an accusation against the wire for a client that had not even got in.
    #   ⛔ The outcome was already right (**3**, not a red), ⭐ but the word was not, and
    #   a wrong diagnosis costs as much as a wrong verdict: whoever reads goes
    #   looking for the fault in the place the bench pointed to.
    # ⛔ And the predicate is NOT `"AMMESSO" in coda`: the client prints that
    #    word also in the two refusal messages (`e_stato_ammesso()` at the top).
    ammesso = e_stato_ammesso(coda)
    if ammesso is not True:
        return None, None, (
            "the client was TURNED AWAY by the server" if ammesso is False
            else "the test client said nothing: I do not know whether it "
                 "got in")
    if not quanti:
        return None, None, ("no frame arrived from the wire "
                            "(session not opened, or stage that does not deliver)")
    # ⛔ `-update 1` keeps the LAST frame: it is what the desktop shows
    #    now.  The first would be the opening keyframe, i.e. a second ago.
    d = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
           % (flusso, fuori), secondi=180)
    if d.returncode != 0 or not os.path.exists(fuori) \
            or os.path.getsize(fuori) == 0:
        return None, quanti, ("%d frames arrived but ffmpeg did not make "
                              "an image of them" % quanti)
    return fuori, quanti, None


def rende_la_pagina_da_solo(chi, a, fuori):
    """⭐⭐ TEST A — *«the browser renders the page»*, ⛔ **without the stage in between**.

    Firefox takes a photograph of itself (`--screenshot`), as a user, on the
    machine as it is configured.  ⇒ The judgement stays **in the pixel** — the page
    is there or it is not — and ⭐ **it catches exactly the defect of §4.6-undecies**:
    to photograph, Firefox must first **make its profile**, and with the
    shared `~/.cache` the second tenant cannot.

    ⛔⛔ AND WHY IT EXISTS, which is the part that must be written instead of hidden.
    The full form of C8 wants the page seen **through the product**, i.e.
    inside the remote session (`rende_la_pagina_nella_sessione`, test B).
    ⚠ That today **cannot be measured**: `[M]` 26 August 2026, inside the
    box **no** new GNOME session is born with a monitor — it is the
    OPEN defect of phase 10 §7.4 («the session that is born blind»), which sits
    **upstream** of C8 and which C1 exists precisely to catch.
    ⇒ ⭐ A black desktop does not testify about the browser: calling that «red of
      C8» would mean blaming the browser for something that happened **before
      the browser existed**.

    ⛔ And the limit is declared, so as not to pass this test off as the other:
      here the browser draws **in its own window**, not **in the remote
      session**.  ⇒ What this test can NOT see is a defect that
      arose between the browser and the stage.  ⚠ It does not replace it: **it precedes it**.
    """
    if os.path.exists(fuori):
        os.unlink(fuori)
    # ⚠ `HOME` explicit and not inherited: the defect lives inside `$HOME/.cache`,
    #   and a test that looked at the wrong home would say green forever.
    # ⛔⛔ AND THE CEILING IS ITS OWN, not that of test B — `[M]` 26 August 2026,
    #    and it cost us a false red.  The first draft reused
    #    `--attesa-browser` (25 s): ⛔ the FIRST start of Firefox in a cold
    #    box does not fit in it, and the test gave **RED TO BOTH**
    #    tenants, with the cure and without.
    #    ⚠ I.e. the bench gave red for the wrong reason — and with a red
    #      like that the acceptance test of the grafted fault is worth nothing, because it no longer
    #      distinguishes the fault from the bench.  ⇒ `LEZIONI.md` §1.41.
    #
    # ⚠⚠ AND THE CEILING GOVERNS A DIFFERENT THING FROM WHAT IT SEEMS — correction
    #    of 26 August 2026, found by C14's bench and not by this one.
    #    `[M]` With `timeout 1`, Firefox exits with **124** (killed) ⛔ **and the PNG
    #    is there anyway, 30 135 bytes**: it writes the image and then lingers
    #    before closing.  ⇒ This ceiling does not limit **the screenshot**: it limits **the exit
    #    of the browser**.
    #    ⭐ The judgement stays right, and for a reason that must be said: we look at
    #      the **file**, not at the exit code — a browser that drew has
    #      drawn, even if it was then killed while taking its leave.
    #    ⛔ But the ceiling stays wide anyway: the first start in a cold
    #      box must be able to get as far as the drawing, and on that the ceiling
    #      really BITES.
    #
    # ⛔⛔ AND THE IMAGE IS WRITTEN IN ITS OWN FOLDER, not in ours.
    #    `[M]` 26 August 2026, and it cost us a second false red: the
    #    bench's working folder belongs to `root` with mode 0755, and Firefox runs
    #    as a USER ⇒ ⛔ it could not write there, and produced no image.
    #    ⚠ The bench read it as «the browser did not draw» — i.e. ⛔ **the
    #      bench gave red to itself and attributed it to the product**.
    #    ⇒ It takes the screenshot in its own home, and root carries it out afterwards.
    suo = "/home/%s/.c8-scatto.png" % chi
    sh("rm -f %s" % suo)
    r = sh("runuser -u %s -- env HOME=/home/%s MOZ_HEADLESS=1 "
           "timeout %d %s --headless --screenshot %s file://%s"
           % (chi, chi, int(a.attesa_scatto), a.browser, suo, a.pagina),
           secondi=int(a.attesa_scatto) + 30)
    coda = ((r.stdout or "") + (r.stderr or "")).strip()
    if os.path.exists(suo) and os.path.getsize(suo):
        sh("cp -f %s %s" % (suo, fuori))
    return fuori if os.path.exists(fuori) and os.path.getsize(fuori) else None, coda[-200:]


def apri_il_browser(chi, a):
    """Switches on the browser INSIDE the tenant's session.

    ⛔ The Wayland socket is SEARCHED for, not guessed: the name depends on how
       the compositor was born, and nailing down `wayland-0` here would mean a
       test that works on one desktop and stays silent on the others — i.e. exactly
       the defect this phase exists not to introduce.
    """
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, "I do not know the uid of %s" % chi
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    display = soc.stdout.strip()
    if not display:
        return None, ("in %s there is no wayland socket: the session does not have "
                      "a compositor the browser can talk to" % rtd)
    comando = (
        # ⛔ `setsid` + stdin closed: without it, the browser ends up in a BACKGROUND
        #    process group of the terminal that launched the net and the first
        #    `tcsetattr` gets it a SIGTTOU ⇒ it stays in state `T` from the first
        #    instant (22 Sep 2026, seen in C3 on all three boxes).
        "setsid runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
        "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
        "%s --kiosk file://%s < /dev/null > /tmp/c8-%s.log 2>&1 &"
        % (chi, rtd, display, chi, a.browser, a.pagina, chi))
    sh(comando, secondi=30)
    return display, None


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente-base", default="c8u")
    p.add_argument("--quanti", type=int, default=2,
                   help="⛔ TWO, and not ten: the question is correctness with "
                        "several tenants, not capacity (D2 corrected)")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--pagina", default="/opt/remotix/11-c8-pagina.html")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--lavoro", default="/var/lib/rete11/c8")
    p.add_argument("--resta-prima", type=float, default=25.0,
                   help="how long to stay attached for the first screenshot: the stage "
                        "is born in ~13 s, and a short deadline would give «I do not know»")
    p.add_argument("--resta-dopo", type=float, default=10.0)
    p.add_argument("--attesa-browser", type=float, default=25.0,
                   help="how long the browser is given to draw the page")
    p.add_argument("--senza-cura", action="store_true",
                   help="⛔ THE GRAFTED FAULT: the provisioning cure is not "
                        "applied. The second tenant MUST give red")
    p.add_argument("--attesa-scatto", type=float, default=120.0,
                   help="how long test A is given. ⛔ Wide on purpose: the FIRST "
                        "start of Firefox in a cold box exceeds 25 s, and "
                        "a tight ceiling gives a red that is not the product's")
    p.add_argument("--senza-sessione", action="store_true",
                   help="skips test B (the page seen FROM THE CLIENT). ⚠ To be "
                        "used when it is already known that sessions are born blind: "
                        "it saves two minutes and changes no judgement")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it has to create two tenants")
        sys.exit(2)

    # ── the terrain, and the three things without which we do not judge ────
    giudice = giudice_immagini()
    if giudice is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    if not os.path.exists(a.pagina):
        print("⛔ I cannot find the target page: %s" % a.pagina)
        print("   ⇒ I could not look")
        sys.exit(3)
    # ⚠ The test client serves ONLY test B.  ⭐ And this is the reason
    #   why test A runs in ANY box, even in one where the
    #   product is not even there: it does not look through the product.
    if not a.senza_sessione and not os.path.exists(a.cliente):
        print("⛔ I cannot find the test client: %s" % a.cliente)
        print("   ⇒ I could not look (⚠ with --senza-sessione it would not be needed)")
        sys.exit(3)
    if sh("command -v %s" % a.browser).returncode != 0:
        print("⛔ the box does not have %s: I cannot ask anyone to "
              "open a page" % a.browser)
        print("   ⇒ I could not look")
        sys.exit(3)
    if sh("command -v ffmpeg").returncode != 0:
        print("⛔ the box does not have ffmpeg: the frames do not become "
              "an image")
        print("   ⇒ I could not look")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)
    dove = prepara_lo_scheletro()
    resto = sgombra_il_posto_condiviso(a.utente_base)

    print("== C8 — the second user opens the browser ==")
    print("   %d tenants · port %d · page %s"
          % (a.quanti, a.porta, os.path.basename(a.pagina)))
    print("   terrain: /etc/skel/.cache -> %s  (the configuration of the "
          "real machine)" % (dove or "⛔ I COULD NOT PUT IT THERE"))
    print("   provisioning cure: %s"
          % ("⛔ NOT APPLIED (grafted fault: the second MUST give red)"
             if a.senza_cura else "applied, as src/provisiona.sh"))
    print("   yardstick: colour %s ±%d, at least %.0f%% of the screen"
          % (COLORE, TOLLERANZA, FRAZIONE_MINIMA * 100))
    if resto:
        print("   %s" % resto)
    print()
    if not dove:
        print("⛔ I could not prepare the skeleton: the terrain does not hold")
        sys.exit(2)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ TWO TESTS, AND NOT ONE — and the reason must be read before the numbers
    #
    #   A · «the browser renders the page»          ⭐ it is measured TODAY
    #       Firefox photographs itself, as a user, on the machine as it is
    #       configured.  It catches the defect of §4.6-undecies in full: to
    #       photograph it must first make its profile.
    #
    #   B · «and the page is seen FROM THE CLIENT»  ⚠ today it is not measured
    #       the same page, looked at through the product.  ⛔ `[M]` 26
    #       August 2026: inside the box NO new GNOME session is born
    #       with a monitor — it is the OPEN defect of phase 10 §7.4, which sits
    #       UPSTREAM of C8.  ⇒ Test B says «I could not look» and
    #       NAMES the why; ⛔ it does not become a red of C8, because a
    #       black desktop does not testify about the browser.
    #
    # ⭐ And the mesh's outcome is decided by **A**.  ⚠ B can make it worse — if
    #   it reaches a judgement and that judgement is red — ⛔ never better.
    # ═══════════════════════════════════════════════════════════════════════
    esiti = []
    for n in range(1, a.quanti + 1):
        chi = "%s%d" % (a.utente_base, n)
        fatto, perche = crea(chi, a.parola)
        if not fatto:
            print("  %-6s  ?   I could not create it: %s" % (chi, perche))
            esiti.append({"chi": chi, "a": None, "b": None})
            continue
        if not a.senza_cura:
            applica_la_cura(chi)
        scrive = sa_scrivere_nella_cache(chi)

        # ── TEST A ─────────────────────────────────────────────────────────
        pa = os.path.join(a.lavoro, "%s-A.png" % chi)
        png_a, detto = rende_la_pagina_da_solo(chi, a, pa)
        fra = frazione_del_colore(png_a) if png_a else None
        # ⛔ «the profile is there» is not enough: with the link to `/tmp` that
        #    folder is SHARED, and the second tenant would see in it the
        #    profile of the FIRST.  ⇒ We look at WHOSE it is.
        prof = sh("ls -d /home/%s/.cache/mozilla/firefox/*/ 2>/dev/null | head -1"
                  % chi).stdout.strip()
        padrone = sh("stat -c %%U /home/%s/.cache/mozilla 2>/dev/null" % chi).stdout.strip()
        if not prof:
            profilo = "⛔ NEVER BORN"
        elif padrone and padrone != chi:
            profilo = "⛔ it belongs to «%s»" % padrone
        else:
            profilo = "its own"
        if fra is None:
            vista_a = False
            comeche = ("⛔ the browser did not even produce an image"
                       if png_a is None else "⛔ the image could not be read")
        else:
            vista_a = fra >= FRAZIONE_MINIMA
            comeche = "the page covers %.1f%% of the image" % (fra * 100)
        print("  %-6s  A  %-3s  %-42s  (profile: %s · can write in "
              "~/.cache/mozilla: %s)"
              % (chi, "YES" if vista_a else "NO", comeche, profilo,
                 "yes" if scrive else "⛔ NO"))
        if not vista_a and detto:
            # ⭐ The reason next to the symptom: «it did not draw» alone
            #   hides three different faults, and the browser says its own.
            print("            ⛔ it says: %s" % detto.replace("\n", " ")[:160])

        # ── TEST B ─────────────────────────────────────────────────────────
        vista_b = None
        motivo_b = ""
        if a.senza_sessione:
            motivo_b = "not asked for (--senza-sessione)"
        else:
            png1 = os.path.join(a.lavoro, "%s-B-prima.png" % chi)
            p1, f1, err1 = scatta(chi, a.parola, png1, a, a.resta_prima)
            g1 = giudice.giudica(p1) if p1 else None
            if g1 is None:
                motivo_b = ("⛔ I could not look at the desktop BEFORE: %s"
                            % (err1 or "unreadable image"))
            elif g1["verdetto"] in ("nero", "quasi-nero"):
                motivo_b = ("⛔ the desktop is «%s» BEFORE the browser: it is the "
                            "defect of phase 10 §7.4, not C8" % g1["verdetto"])
            else:
                display, err = apri_il_browser(chi, a)
                if display is None:
                    motivo_b = "⛔ I could not switch on the browser: %s" % err
                else:
                    time.sleep(a.attesa_browser)
                    png2 = os.path.join(a.lavoro, "%s-B-dopo.png" % chi)
                    p2, f2, err2 = scatta(chi, a.parola, png2, a, a.resta_dopo)
                    frb = frazione_del_colore(p2) if p2 else None
                    if frb is None:
                        motivo_b = ("⛔ I could not look at the desktop AFTER: %s"
                                    % (err2 or "unreadable image"))
                    else:
                        vista_b = frb >= FRAZIONE_MINIMA
                        motivo_b = ("the page covers %.1f%% of the screen "
                                    "(desktop before: %s · frames %s/%s)"
                                    % (frb * 100, g1["verdetto"], f1, f2))
        print("  %-6s  B  %-3s  %s"
              % (chi, "YES" if vista_b else ("NO" if vista_b is False else "?"),
                 motivo_b))

        esiti.append({"chi": chi, "a": vista_a, "b": vista_b})
        sh("pkill -KILL -u %s 2>/dev/null; loginctl terminate-user %s 2>/dev/null"
           % (chi, chi))
        time.sleep(1.5)

    # ═══════════════════════════════════════════════════════════════════════
    print()
    ra = sum(1 for e in esiti if e["a"] is True)
    fa = sum(1 for e in esiti if e["a"] is False)
    ia = sum(1 for e in esiti if e["a"] is None)
    rb = sum(1 for e in esiti if e["b"] is True)
    fb = sum(1 for e in esiti if e["b"] is False)
    ib = sum(1 for e in esiti if e["b"] is None)
    # ⛔ THESE TWO SUMMARY LINES STAY IN ITALIAN FOR NOW: `11-c14-…py` reads the
    #    «A · …» one with a regular expression (`RIGA_A`), and its certification
    #    quotes the «B · …» one.  ⇒ They change together with C14, not before.
    print("  A · il browser rende la pagina    : %d si' · ⛔ %d no · %d non giudicati"
          % (ra, fa, ia))
    print("  B · e la pagina si vede DAL CLIENTE: %d si' · ⛔ %d no · %d non giudicati"
          % (rb, fb, ib))

    if a.senza_cura:
        # ⛔ With the grafted fault the outcome is READ BACKWARDS: here green is
        #    a red.  ⭐ A net that can no longer give red has
        #    exactly the look of a net that finds nothing (C13).
        print()
        if fa + fb >= 1:
            print("⭐ THE GRAFTED FAULT WAS SEEN: %d tenants out of %d did not "
                  "open the browser.  ⇒ this mesh CAN say red" % (fa, len(esiti)))
            # ⛔ And it is also said WHO: if the FIRST had given red, the test
            #    would be measuring something else (for example a leftover of the
            #    previous round), and the acceptance test would not count.
            primi = [e["chi"] for e in esiti if e["a"] is False]
            print("   ⇒ they did not make it: %s" % ", ".join(primi))
            if esiti and esiti[0]["a"] is False:
                print("   ⚠ ⛔ BUT THE FIRST FAILED TOO: the expected fault bites from the "
                      "SECOND on.  ⇒ either the shared place was already dirty, or "
                      "what is being measured is not the defect of §4.6-undecies")
                return 1
            return 0
        if ia + (ib if not a.senza_sessione else 0) and not (ra or rb):
            print("⛔ I could not judge: I cannot say whether the fault "
                  "would have been seen")
            return 3
        print("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: everyone opened the "
              "browser even without the cure.")
        print("    ⇒ either the cure was not needed, or this mesh does not look in the right "
              "place — and in both cases it cannot be trusted.")
        return 1

    if fa or fb:
        print("⛔ RED: %d tenants out of %d did not open the browser"
              % (fa + fb, len(esiti)))
        return 1
    if ia:
        print("⛔ I could not look at %d tenants out of %d in test A" % (ia, len(esiti)))
        return 3
    print("⭐ all %d tenants opened the browser and the page is seen"
          % len(esiti))
    if ib:
        print("⚠ and test B (the page seen FROM THE CLIENT) could not "
              "judge %d of them: the why is written above, and ⛔ it is not a green"
              % ib)
    return 0

if __name__ == "__main__":
    sys.exit(main())
