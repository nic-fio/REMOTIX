#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c18 — ⭐ «THE PRODUCT SETS THE CARD GROUPS»
===========================================================================

    python3 11-c18-i-gruppi-li-mette-il-prodotto.py --porta 8511
    python3 11-c18-i-gruppi-li-mette-il-prodotto.py --porta 8511 --senza-usermod
    python3 11-c18-i-gruppi-li-mette-il-prodotto.py --certifica

    what must be true         : a NEW user, who is not in the groups of the
                                `/dev/dri` nodes, connects — and **the
                                product puts them there**, by itself, at the first
                                connection (`DECISIONI.md` §7.21, decided
                                by the user on 20 September 2026)
    where it starts from      : a new tenant, ⛔ **WITHOUT** the groups
    what it looks at          : three facts, each with its own name
      G  before     `id -nG` does NOT contain the groups of the card's nodes
      I  during     the server log says «FIRST CONNECTION … I am PUTTING
                    it there» with the name of THIS tenant
      D  after      `id -nG` now CONTAINS them, and the log says
                    «is in the card's groups … can see in hardware»
    how I know it can give red: `--senza-usermod` — for the length of the run
                                `usermod` is moved to another name: the product cannot
                                enrol anyone ⇒ **I and D red**

⛔⛔ WHY THIS MESH EXISTS, and it is a hole that was seen only today.

    The fact it covers is the only one of the product that **all the other meshes
    hide**: every mesh calls `garantisci_i_gruppi(chi)` BEFORE
    connecting (`11-c1`, and from there C3, C4, C7, C9, C17…), that is it gives the groups
    to the tenant **with its own hands**.  ⇒ When the client arrives, the product
    has nothing left to enrol, its line never comes out, and ⛔ **the whole net
    can be green with that piece of the product broken**.
    ⚠ And it is not a defect of those meshes: they must measure something else, and a
      blind tenant would make them exit with an «I could not look» (§1.51).
      ⇒ The hole is closed by adding a mesh, not by changing theirs.

⭐⭐ AND IT HOLDS ON ALL DESKTOPS, not only on kde — and it is the user's point
    of 21 September 2026: *«it must work for all the DEs, not only for
    KDE»*.  The code that enrols (`src/figlio.c`, `iscrivi_ai_gruppi_della_
    scheda`) lives in the **parent**, runs as root **after PAM** and **before the fork**:
    it does not even know which compositor will be born.  ⇒ There is no branch per
    desktop to test — there is one thing only, and it must be tested **on every box**.
    `[M]` 22 Sep 2026, with REAL browsers and a real window, tenants without groups:
      · gnome  Firefox 140 PASS · Chrome 153 PASS ⇒ `sgruppig`/`sgruppic` from
        «only itself» to «video render», first frame in 1,6 s and 1,2 s
      · xfce   Firefox 140 PASS · Chrome 153 PASS ⇒ `sgruppix`/`sgruppiy`
        likewise, 0,6 s and 0,9 s
      · kde    already `[M]` on 20 Sep 2026 (`DECISIONI.md` §7.21, user
        `senzagr`: with the previous binary zero frames, with the new one 105)

⛔ THIS MESH DOES NOT JUDGE THE FRAMES.  That the session sees is the job
   of C1 and C3; here the frames are printed as a FINDING, because whoever reads the
   log must be able to tell «enrolled and sees» from «enrolled and does not see».
   ⚠ Judging them here would mean two meshes giving red for the same
     fact, and the day that red arrived nobody would know whose it is.

Outcomes: 0 green · 1 red · 3 I could not look (⛔ it is NOT a red).
⛔ With `--senza-usermod` it reads THE OTHER WAY ROUND: 0 = the fault was SEEN.
"""
import argparse
import os
import random
import re
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")
REGISTRO = "/var/lib/rete11/registro.log"
PAROLA = "provanic2026"

# ⛔ The group in which `gpu-udev.sh` puts the EXCLUDED card: nobody must
#    be in it, ⇒ it does not count among the groups the product must give.
#    ⚠ It is the same rule as `src/provisiona.sh`: the excluded card exists
#    so that the measurements are always made on the same one (`gid_della_scheda`).
GRUPPO_ESCLUSO = "remotix-nogpu"

# ⭐ The two product lines this mesh reads, and they are in one place
#    only because if the product changes them they are changed HERE (§1.47).
#    `[R]` `src/figlio.c`, `iscrivi_ai_gruppi_della_scheda` and `gruppi_della_scheda`.
RIGA_ISCRIZIONE = "FIRST CONNECTION"
RIGA_VEDE = "in the card's groups"
RIGA_CIECO = "IS NOT IN THE CARD'S GROUP"
# ⚠ The log is in UTF-8 and the product writes straight apostrophes: the line
#   «IS NOT IN THE CARD'S GROUP» is searched as it is, without normalising anything.

# ⛔ The two places where the product looks for `usermod` (`src/figlio.c`,
#    `comando_da_root`): the injected fault must hide BOTH of them, or
#    the product finds the second and the fault does not bite.
POSTI_USERMOD = ("/usr/sbin/usermod", "/sbin/usermod")
CODA_NASCOSTO = ".c18-nascosto"


def corri(argv, tempo=30, **kw):
    """A command, or `None` if the time ran out.  ⛔ It never raises."""
    try:
        return subprocess.run(argv, capture_output=True, text=True,
                              timeout=tempo, **kw)
    except (subprocess.TimeoutExpired, OSError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE GROUPS ARE ASKED OF THE NODES — and this is the project's rule, not
#     a convenience.  `video` and `render` are the names of ONE distribution;
#     what counts is the **gid** that the kernel and udev put on
#     `/dev/dri/cardN` and `/dev/dri/renderDN` of THIS machine.
#     `[R]` `src/provisiona.sh`, `gid_della_scheda()`; `src/figlio.c`,
#     `raccogli_gruppi_scheda()`.  ⛔ Three places that read the same thing
#     in the same way: if they diverge, the judgement diverges.
# ═══════════════════════════════════════════════════════════════════════════
def gid_escluso():
    r = corri(["getent", "group", GRUPPO_ESCLUSO], 10)
    if r is None or r.returncode != 0:
        return None
    pezzi = (r.stdout or "").strip().split(":")
    return pezzi[2] if len(pezzi) > 2 else None


def gruppi_dei_nodi(cartella="/dev/dri"):
    """⭐ (nomi, perche') — the NAMES of the groups of the card's nodes.

    ⛔ Empty list and a reason when it cannot be known: without the nodes this
       mesh has nothing to look at, and it is a **3**, not a red — a
       machine without a card is not a broken product.
    """
    if not os.path.isdir(cartella):
        return [], "%s is not there: this box has no nodes of the card" % cartella
    escluso = gid_escluso()
    gid = []
    for nome in sorted(os.listdir(cartella)):
        if not re.match(r"^(card|renderD)[0-9]+$", nome):
            continue
        try:
            g = str(os.stat(os.path.join(cartella, nome)).st_gid)
        except OSError:
            continue
        if escluso is not None and g == escluso:
            continue
        if g not in gid:
            gid.append(g)
    if not gid:
        return [], ("no readable `cardN`/`renderDN` node in %s: I do not know "
                    "which groups the product should give" % cartella)
    nomi = []
    for g in gid:
        r = corri(["getent", "group", g], 10)
        if r is None or r.returncode != 0 or not (r.stdout or "").strip():
            return [], ("the gid %s of the nodes has no name in /etc/group: "
                        "not even the product could enrol anyone in it" % g)
        n = r.stdout.split(":")[0]
        if n not in nomi:
            nomi.append(n)
    return nomi, ""


def gruppi_di(chi):
    """The user's groups NOW, read from the system.  `None` = I do not know."""
    r = corri(["id", "-nG", chi], 10)
    if r is None or r.returncode != 0:
        return None
    return (r.stdout or "").split()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGEMENT — a PURE function, so `--certifica` goes through it without
#   touching either the machine or the product.
# ═══════════════════════════════════════════════════════════════════════════
def giudizio(attesi, prima, dopo, fetta, chi):
    """⭐ (esito, faccia_g, faccia_i, faccia_d, perche) from the FACTS.

    `attesi` the names the product must give · `prima`/`dopo` the tenant's
    groups · `fetta` the log lines of THIS run.
    ⛔ No file reading in here: only facts already gathered.
    """
    if not attesi:
        return 3, "?", "?", "?", "I do not know which groups the product should give"
    if prima is None or dopo is None:
        return 3, "?", "?", "?", "I could not read the tenant's groups"

    # ── G: before it must NOT be there, or this mesh is looking at something else ──
    gia = [g for g in attesi if g in prima]
    if gia:
        return 3, "NO", "?", "?", (
            "«%s» was ALREADY in the groups %s before connecting: someone put it "
            "there (the `useradd` skeleton? another mesh?) ⇒ the product "
            "had nothing to enrol and this run proves nothing"
            % (chi, ", ".join(gia)))

    righe_mie = [r for r in fetta if ("[%s]" % chi) in r]
    iscritto = any(RIGA_ISCRIZIONE in r for r in righe_mie)
    vede = any(RIGA_VEDE in r and RIGA_CIECO not in r for r in righe_mie)
    cieco = any(RIGA_CIECO in r for r in righe_mie)
    mancanti = [g for g in attesi if g not in dopo]

    # ⛔ No line of this tenant ⇒ the client never reached
    #    the child: it is not a red of the product, it is a run not done.
    if not righe_mie:
        return 3, "SI", "?", "?", (
            "in the log there is no line of «%s»: the client did not "
            "reach the child, and without a session there is no enrolment to "
            "look at" % chi)

    faccia_i = "SI" if iscritto else "NO"
    faccia_d = "SI" if (not mancanti and vede) else "NO"
    if iscritto and not mancanti and vede:
        return 0, "SI", faccia_i, faccia_d, (
            "«%s» arrived without the groups, the product put it there "
            "(%s) and the session can see in hardware"
            % (chi, ", ".join(attesi)))

    perche = []
    if not iscritto:
        perche.append("«%s» is missing from the log: the product did NOT try to "
                      "enrol it" % RIGA_ISCRIZIONE)
    if mancanti:
        perche.append("after the connection «%s» is NOT in the groups %s (has: %s)"
                      % (chi, ", ".join(mancanti), " ".join(dopo) or "nothing"))
    if cieco:
        perche.append("the product declares the session BLIND («%s»)" % RIGA_CIECO)
    elif not vede:
        perche.append("the line «%s» is missing: the product does not declare that this "
                      "session sees" % RIGA_VEDE)
    return 1, "SI", faccia_i, faccia_d, "; ".join(perche)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE INJECTED FAULT — and it is injected into the MACHINE, not the product.
#
# ⭐ Hiding `usermod` is the most honest way to take from the product the
#   possibility of enrolling: the binary is not touched, the log is not
#   touched, the tenant is not touched.  ⇒ The product does exactly what it
#   would do, and fails where it must fail.
# ⚠ And it is ALWAYS PUT BACK, even if the run dies half-way: the `finally`
#   of `main`, plus a tidy-up at the start of the next run — because a
#   `usermod` left hidden would make blind all the meshes that come
#   after, and that is precisely the defect this net is made not to have.
# ═══════════════════════════════════════════════════════════════════════════
def nascondi_usermod():
    """⛔ Returns the list of what it moved (to be put back)."""
    spostati = []
    for p in POSTI_USERMOD:
        if os.path.exists(p) and not os.path.islink(p):
            if corri(["mv", p, p + CODA_NASCOSTO], 10) is not None:
                spostati.append(p)
    return spostati


def rimetti_usermod():
    """⭐ Always, and without asking: what it finds hidden it puts back."""
    rimessi = []
    for p in POSTI_USERMOD:
        if os.path.exists(p + CODA_NASCOSTO):
            corri(["mv", p + CODA_NASCOSTO, p], 10)
            rimessi.append(p)
    return rimessi


def sgombera(chi):
    corri(["loginctl", "terminate-user", chi], 20)
    for _ in range(40):
        r = corri(["pgrep", "-u", chi], 5)
        if r is None or r.returncode != 0:
            break
        time.sleep(0.25)
    corri(["pkill", "-KILL", "-u", chi], 5)
    corri(["userdel", "-r", chi], 20)


def leggi(percorso):
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except OSError:
        return None


def certifica():
    """⛔ Can the mesh give red? It is tested on the JUDGEMENT, without a machine."""
    guai = 0
    casi = [
        ("⭐ no groups before, enrolled and in the groups after ⇒ GREEN",
         (["video", "render"], ["c18u1"], ["c18u1", "video", "render"],
          ["figlio  [c18u1] ⭐ FIRST CONNECTION: «c18u1» is not in the card's groups",
           "figlio  [c18u1] ⭐ is in the card's groups (render, video)"]), 0),
        ("⛔ the product does not even try to enrol it ⇒ RED",
         (["video", "render"], ["c18u1"], ["c18u1"],
          ["figlio  [c18u1] ⛔⛔ «c18u1» IS NOT IN THE CARD'S GROUP «video»"]), 1),
        ("⛔ it tries and does not succeed (usermod hidden) ⇒ RED",
         (["video", "render"], ["c18u1"], ["c18u1"],
          ["figlio  [c18u1] ⭐ FIRST CONNECTION: «c18u1» is not in the card's groups",
           "figlio  [c18u1] ⛔ I could not enrol «c18u1»"]), 1),
        ("⛔ half enrolled (one of the two groups is missing) ⇒ RED",
         (["video", "render"], ["c18u1"], ["c18u1", "video"],
          ["figlio  [c18u1] ⭐ FIRST CONNECTION: «c18u1» is not in the card's groups"]), 1),
        ("⚠ it was ALREADY in the groups before ⇒ 3, ⛔ never green (proves nothing)",
         (["video", "render"], ["c18u1", "video", "render"],
          ["c18u1", "video", "render"],
          ["figlio  [c18u1] ⭐ is in the card's groups (render, video)"]), 3),
        ("⚠ no line of the tenant in the log ⇒ 3, ⛔ never red",
         (["video", "render"], ["c18u1"], ["c18u1"],
          ["figlio  [altro] ⭐ FIRST CONNECTION: «altro» is not in the card's groups"]), 3),
        ("⚠ card nodes not readable ⇒ 3, ⛔ never red",
         ([], ["c18u1"], ["c18u1"], []), 3),
        ("⚠ the tenant's groups cannot be read ⇒ 3",
         (["video"], None, None, []), 3),
    ]
    print("== C18 — certification of the judgement (⛔ without touching the machine)")
    for nome, argomenti, atteso in casi:
        attesi, prima, dopo, fetta = argomenti
        e = giudizio(attesi, prima, dopo, fetta, "c18u1")[0]
        segno = "OK " if e == atteso else "NO "
        if e != atteso:
            guai += 1
        print("  %s %-62s outcome %s (expected %s)" % (segno, nome, e, atteso))
    # ⭐ And the fault's two tools are tested by NAME, not by trust: a
    #   `usermod` that is not put back is a broken box for all the meshes.
    print("  %s %-62s %s"
          % ("OK " if len(POSTI_USERMOD) == 2 else "NO ",
             "⛔ the fault hides ALL the places of `usermod`",
             " ".join(POSTI_USERMOD)))
    print()
    if guai:
        print("⛔ %d cases of the judgement do NOT give what they must" % guai)
        return 1
    print("⭐ the judgement gives green, red and «I do not know» where it must — and the real "
          "case (arrived without groups, left with them) is the first")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--senza-usermod", action="store_true",
                   help="⛔ THE INJECTED FAULT: `usermod` disappears for the "
                        "length of the run ⇒ the product cannot enrol")
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--resta", type=float, default=12.0)
    p.add_argument("--attesa", type=float, default=45.0,
                   help="how long the child's line in the log is waited for")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.porta:
        print("⛔ it wants `--porta` ⇒ I could not look")
        return 3
    if os.geteuid() != 0:
        print("⛔ it wants the administrator (it creates a tenant) ⇒ I could not look")
        return 3

    chi = "c18u%d" % random.randint(100, 999)
    innestato = " ⛔ INJECTED FAULT: --senza-usermod" if a.senza_usermod else ""
    print("== C18 — the card groups are set by the PRODUCT (%s, port %d)%s"
          % (chi, a.porta, innestato))

    # ⭐ First of all: if a dead run left `usermod` hidden, it is
    #    put back BEFORE measuring — otherwise this run would measure the
    #    leftover of yesterday's run and call it a defect of the product.
    rimessi = rimetti_usermod()
    if rimessi:
        print("   ⚠ a previous run had left %s hidden: put back"
              % ", ".join(rimessi))

    attesi, perche_nodi = gruppi_dei_nodi()
    if not attesi:
        print("   ⛔ %s ⇒ I could not look" % perche_nodi)
        return 3
    print("   the groups of the card's nodes, READ NOW: %s" % ", ".join(attesi))

    sgombera(chi)
    fatto = corri(["/bin/sh", "-c",
                   "useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                   % (chi, chi, PAROLA)], 60)
    if fatto is None or fatto.returncode != 0:
        print("   ⛔ I could not create the tenant ⇒ I could not look")
        return 3

    spostati = []
    try:
        prima = gruppi_di(chi)
        print("   G  before: %s" % (" ".join(prima) if prima else "I do not know"))

        if a.senza_usermod:
            spostati = nascondi_usermod()
            if not spostati:
                print("   ⛔ I could not hide `usermod`: the fault is not "
                      "injected ⇒ I could not look")
                return 3
            print("   ⛔ hidden: %s" % ", ".join(spostati))

        # ⛔ We mark WHERE we are in the log BEFORE connecting: the judgement
        #    looks only at the slice of THIS run (the lesson of phase 9).
        righe = leggi(a.registro)
        segno = len(righe) if righe is not None else 0

        r = corri(["python3", "-u", CLIENTE, "--indirizzo", "127.0.0.1",
                   "--porta", str(a.porta), "--utente", chi,
                   "--parola", PAROLA, "--resta", str(a.resta)],
                  max(90, a.resta * 6))
        if r is None:
            print("   ⛔ the client did not finish in time ⇒ I could not look")
            return 3

        # ⭐ We wait for the EVENT, not the clock: the child's line comes out when
        #   the parent has spawned it, and how long it takes is not up to us.
        fetta, scadenza = [], time.time() + a.attesa
        while time.time() < scadenza:
            dopo_righe = leggi(a.registro)
            fetta = dopo_righe[segno:] if dopo_righe is not None else []
            if any(("[%s]" % chi) in x and
                   (RIGA_ISCRIZIONE in x or RIGA_VEDE in x or RIGA_CIECO in x)
                   for x in fetta):
                break
            time.sleep(0.5)

        dopo = gruppi_di(chi)
        print("   D  after:  %s" % (" ".join(dopo) if dopo else "I do not know"))
        esito, fg, fi, fd, perche = giudizio(attesi, prima, dopo, fetta, chi)

        # ⭐ The FINDING on frames: it is printed, ⛔ not judged (see at the top).
        fot = None
        for riga in fetta:
            m = re.search(r"sent (\d+)", riga)
            if ("[%s]" % chi) in riga and m:
                fot = int(m.group(1))
        print("   G %-3s I %-3s D %-3s" % (fg, fi, fd))
        print("   ⚠ FINDING, not verdict: frames sent to «%s»: %s"
              % (chi, "I do not know" if fot is None else fot))
        for riga in fetta:
            if ("[%s]" % chi) in riga and (RIGA_ISCRIZIONE in riga or
                                           RIGA_VEDE in riga or RIGA_CIECO in riga):
                print("   log: %s" % riga.strip()[:150])

        print()
        if a.senza_usermod:
            # ⛔ The other way round, and it is said out loud: here 0 is the good news.
            if esito == 1:
                print("⭐ THE INJECTED FAULT WAS SEEN — this mesh CAN "
                      "give red,\n   ⭐ and for the right reason: %s" % perche)
                return 0
            if esito == 3:
                print("⚠ with the injected fault I could NOT look: %s\n"
                      "   ⇒ outcome 3, not a green" % perche)
                return 3
            print("⛔⛔ THE INJECTED FAULT WAS NOT SEEN: `usermod` was "
                  "hidden and the mesh\n   said green all the same.")
            return 1
        if esito == 0:
            print("⭐ GREEN — %s" % perche)
        elif esito == 1:
            print("⛔⛔ RED — %s" % perche)
        else:
            print("⚠ I could not look — %s" % perche)
        return esito
    finally:
        # ⛔ In order: first `usermod` goes back to its place (does `userdel` need it?
        #    no, but ANYONE who comes after does), then the tenant is cleared out.
        rimetti_usermod()
        if spostati:
            print("   ⭐ `usermod` put back in its place")
        sgombera(chi)


if __name__ == "__main__":
    sys.exit(main())
