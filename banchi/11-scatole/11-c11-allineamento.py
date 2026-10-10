#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c11 — ⭐⭐ «THE BOXES ARE ALIGNED» — the mesh that looks at THE NET
===========================================================================

    python3 11-c11-allineamento.py
    python3 11-c11-allineamento.py --certifica

⛔ This mesh **does not test the product**: it tests that the comparisons between desktops
   are worth something.  ⭐ And it is the fault the user named FIRST,
   in his own words:

       *«for the numbers to be consistent the containers must be kept
         aligned.  If on the gnome container we have remotix v1 and on the
         kde container remotix v1.2 we crash.»*

   ⇒ `fasi/11…` D5, and mesh C11 of §4.2.

---------------------------------------------------------------------------
⛔⛔ AND WE LOOK AT WHAT IS INSIDE, NOT AT WHAT IS WRITTEN IN THE RECIPE
---------------------------------------------------------------------------

The first idea was to compare the **recipes**.  ⛔ It does not hold: the recipes are
different **on purpose** (every box has its own desktop), and a comparison that must
first «remove the different parts» becomes a comparison people argue about.

⭐ What really counts is not that the recipes resemble each other: it is that the
  **running boxes** agree on everything that is NOT the desktop.
  ⇒ Each is asked which version it has of every declared piece, and we look
    whether they answer the same thing.  «Written is not in force» (E1) applied
    to the environment: ⛔ a recipe rebuilt yesterday and one from a month ago can
    have the same text and different packages.

---------------------------------------------------------------------------
⭐ WHAT MUST BE THE SAME, and why each one
---------------------------------------------------------------------------

  the base           `debian:13` ⇒ a different distribution makes different numbers
  mesa / libva       ⛔ the ENCODER.  Two different mesas and the milliseconds
                     can no longer be compared
  pipewire           the capture path
  ffmpeg / libav*    what decodes when an image is judged
  firefox-esr        ⛔ C8's target: two different Firefoxes, two different
                     defects
  libc / libssl      the bottom of everything
  ⭐ THE PRODUCT      md5 of the binary: ⛔ **it is the reason this
                     mesh exists**.  A different binary per box and every comparison
                     between desktops is hot air

⛔ AND WHAT MUST **NOT** BE THE SAME, declared: the **desktop**.  Every
   box has its own, and that is the point.  ⇒ The desktop package is told by
   the ADAPTER, and this mesh prints it without comparing it.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ the running boxes are aligned
  1  ⛔ at least one piece has different versions across the boxes ⇒ red
  3  ⛔ I could not look (podman is not there, no box running,
     a box does not answer) — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import subprocess
import sys

# ⛔ The list is DECLARED here and printed in every outcome: «aligned» is a
#    verdict, and a verdict without its yardstick is an opinion.
DEVE_COMBACIARE = [
    ("la base", "base"),
    ("mesa-va-drivers", "pacchetto"),
    ("va-driver-all", "pacchetto"),
    ("libva2", "pacchetto"),
    # ⚠ The names carry the `t64` and it is NOT a detail: in Debian 13 the packages
    #   touched by the 64-bit time transition are called like that.  ⛔ The
    #   first draft asked for `libssl3` and `libpipewire-0.3-0`, which do NOT exist
    #   ⇒ it answered «?» for all, and ⛔ «?» equal for all PASSES the comparison.
    #   That is, three entries out of thirteen were looking at nothing.
    ("libpipewire-0.3-0t64", "pacchetto"),
    # ⭐ Added on 26 Aug 2026 with C5: `pw-play`/`pw-cli` live in
    #   `pipewire-bin`, and that is where C5 gets the sound from.  ⛔ Without this
    #   entry two boxes could have different audio tools and C11 stayed silent.
    ("pipewire-bin", "pacchetto"),
    ("libavcodec61", "pacchetto"),
    ("ffmpeg", "pacchetto"),
    ("firefox-esr", "pacchetto"),
    ("libc6", "pacchetto"),
    ("libssl3t64", "pacchetto"),
    ("libei1", "pacchetto"),
    ("libpci3", "pacchetto"),
    # ⭐ Added on 21 Sep 2026 (phase 13): C17's clipboard ARBITERS —
    #   `wl-clipboard` where the compositor has `data-control`, GTK4 (for
    #   `appunti-gtk.py`) where it does not.  Until yesterday they were only in gnome
    #   and kde, and ⛔ C11 did not see it: they were not in this list.
    # ⚠ THE CHOICE, written: inside the list, and not «it is enough to put them in all
    #   four recipes».  A recipe is not the box (E1): two boxes
    #   rebuilt on different days can have the arbiter in different
    #   versions, and then C17's green on one and red on the other would no
    #   longer say «it is the desktop».  ⛔ The PRICE, declared: until
    #   `rete11-xfce` and `rete11-lxqt` are rebuilt from the new
    #   recipe, here they answer «(not there)» and C11 gives RED — and it is a real
    #   red: those two boxes are not aligned with the others.
    ("wl-clipboard", "pacchetto"),
    ("python3-gi", "pacchetto"),
    ("gir1.2-gtk-4.0", "pacchetto"),
    ("il prodotto (md5)", "prodotto"),
]

DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def dentro(scatola, comando):
    """⛔ No nested `sh -c`: `LEZIONI.md` §1.46 — a command that loses its
       quotes runs nothing and returns 0."""
    p = subprocess.run(["podman", "exec", scatola, "/bin/sh", "-c", comando],
                       capture_output=True, text=True, timeout=90)
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def raccogli(scatola):
    """Returns the dictionary of that box, or ⛔ `None` if it does not answer."""
    vivo = subprocess.run(["podman", "inspect", "-f", "{{.State.Running}}", scatola],
                          capture_output=True, text=True)
    if vivo.returncode != 0 or vivo.stdout.strip() != "true":
        return None
    d = {}
    d["la base"] = dentro(scatola, "cat /etc/debian_version")
    for nome, che in DEVE_COMBACIARE:
        if che != "pacchetto":
            continue
        d[nome] = dentro(scatola, "dpkg-query -W -f='${Version}' %s 2>/dev/null "
                                  "|| echo '(not there)'" % nome)
    d["il prodotto (md5)"] = dentro(
        scatola, "md5sum /opt/remotix/remotix 2>/dev/null | cut -c1-12 "
                 "|| echo '(not inside yet)'")
    # ⚠ The desktop is PRINTED and not compared: it is the only thing that MUST
    #   be different.  And the adapter says it, not this file.
    pacco = dentro(scatola, ". /usr/local/lib/rete11/adattatore.sh 2>/dev/null "
                            "&& adattatore_pacchetto")
    d["_desktop"] = "%s %s" % (pacco or "?", dentro(
        scatola, "dpkg-query -W -f='${Version}' %s 2>/dev/null || echo ?"
                 % (pacco or "x")) or "?")
    return d


def giudica(tavola):
    """Given {box: {entry: value}}, says which entries do NOT match.

    ⛔ Returns `None` if there is not enough to judge: **a single box
       is not an alignment**, and calling it green would be the most convenient lie of
       this whole mesh.
    """
    presenti = {n: d for n, d in tavola.items() if d}
    if len(presenti) < 2:
        return None
    guai = []
    for nome, _che in DEVE_COMBACIARE:
        valori = {}
        for scatola, d in presenti.items():
            v = d.get(nome)
            valori.setdefault(v, []).append(scatola)
        # ⚠ An entry that NOBODY has (for example the product not yet put
        #   inside) is the same for all: it is not a misalignment.
        if len(valori) > 1:
            guai.append((nome, valori))
    return guai


def certifica():
    """⛔ We prove that the judge CAN give red — and that it can say «I do not know»."""
    casi = [
        ("two boxes agreeing on everything",
         {"a": {n: "1" for n, _ in DEVE_COMBACIARE},
          "b": {n: "1" for n, _ in DEVE_COMBACIARE}}, 0),
        ("⭐ the PRODUCT different — the fault the user named first",
         {"a": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "aaaa"}),
          "b": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "bbbb"})}, 1),
        ("mesa different: the milliseconds can no longer be compared",
         {"a": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"mesa-va-drivers": "25.0.7"}),
          "b": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"mesa-va-drivers": "25.1.0"})}, 1),
        ("⛔ a single box is NOT an alignment",
         {"a": {n: "1" for n, _ in DEVE_COMBACIARE}, "b": None}, None),
        ("⛔ no box running",
         {"a": None, "b": None}, None),
        ("an entry missing from ALL is not a misalignment",
         {"a": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "(not inside yet)"}),
          "b": dict({n: "1" for n, _ in DEVE_COMBACIARE},
                    **{"il prodotto (md5)": "(not inside yet)"})}, 0),
    ]
    print("== certification of the C11 judge ==")
    guai = 0
    for nome, tavola, atteso in casi:
        r = giudica(tavola)
        ottenuto = None if r is None else len(r)
        ok = ottenuto == atteso
        print("  %s  %-58s  misalignments=%s (expected %s)"
              % ("OK " if ok else "NO ", nome,
                 "I do not know" if ottenuto is None else ottenuto,
                 "I do not know" if atteso is None else atteso))
        if not ok:
            guai += 1
    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d wrong cases" % guai)
        return 1
    print("⭐ the judge sees the misalignment, and ⛔ does not call «aligned» two")
    print("   boxes of which one is not there")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--desktop", default=",".join(DESKTOP))
    p.add_argument("--prefisso", default="rete11-")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    # ⚠ `command` is a shell builtin, not a program: looking for it with
    #   `subprocess` gives `FileNotFoundError`.  We ask podman whether it is there.
    try:
        subprocess.run(["podman", "--version"], capture_output=True, timeout=30)
    # ⛔ `subprocess.TimeoutExpired` does NOT descend from `OSError`: without
    #    naming it, a command that hangs produces a traceback ⇒ Python exits **1**
    #    ⇒ the hook reads RED on a fault of the BENCH (`LEZIONI.md` §1.51, and
    #    the cure C10 already has in `radice_del_deposito()`).
    # ⚠ And this mesh is in the `rete` family, that is it fires at EVERY
    #   change, and it does ~76 `podman exec` on four boxes: it is precisely
    #   the one where a slow command is most likely.
    except (OSError, subprocess.SubprocessError):
        print("⛔ podman is not there or does not answer: ⇒ I could not look")
        sys.exit(3)

    nomi = [a.prefisso + d for d in a.desktop.split(",") if d]
    tavola = {n: raccogli(n) for n in nomi}

    print("== C11 — are the boxes aligned? ==")
    print("   ⛔ we look at what is INSIDE the running boxes, not at what")
    print("      is written in the recipes\n")
    accese = [n for n, d in tavola.items() if d]
    for n in nomi:
        d = tavola[n]
        print("   %-14s %s" % (n, ("desktop: %s" % d["_desktop"]) if d
                               else "⛔ off or not answering"))
    print()

    # ⛔⛔ AND BEFORE JUDGING: an entry NO box can answer
    #    is the same for all, so it **passes** — and it has looked at nothing.
    #    `[M]` 26 August 2026: three entries out of thirteen were like that (wrong names),
    #    and the green on them was worth nothing.  ⇒ It is declared.
    mute = [nome for nome, _ in DEVE_COMBACIARE
            if all((tavola[n] or {}).get(nome) in (None, "", "?")
                   for n in nomi if tavola[n])]
    r = giudica(tavola)
    if r is None:
        print("⛔ boxes running: %d — ⭐ and ONE ONLY is not an alignment."
              % len(accese))
        print("   ⇒ I could not look")
        sys.exit(3)

    # ⭐ The table is ALWAYS printed, green or red: it is what must be compared
    #   across the four boxes, and whoever reads must be able to see it.
    largh = max(len(n) for n, _ in DEVE_COMBACIARE)
    print("   %-*s  %s" % (largh, "entry", "  ".join("%-16s" % n for n in accese)))
    for nome, _che in DEVE_COMBACIARE:
        valori = [tavola[n].get(nome) or "?" for n in accese]
        segno = "  " if len(set(valori)) == 1 else "⛔"
        print(" %s %-*s  %s" % (segno, largh, nome,
                                "  ".join("%-16s" % v[:16] for v in valori)))
    print()
    if mute:
        print("⚠ ⛔ %d entries NO box can answer — and a silent entry"
              % len(mute))
        print("   PASSES the comparison without having looked at anything:")
        for nome in mute:
            print("     · %s" % nome)
        print("   ⇒ they must be fixed, or this mesh tells itself stories.\n")
    if r:
        print("⛔⛔ RED — %d entries do NOT match across the boxes:" % len(r))
        for nome, valori in r:
            print("   · %s" % nome)
            for v, chi in valori.items():
                print("       %-16s  %s" % (v, ", ".join(chi)))
        print()
        print("   ⇒ as long as it is like this, ⛔ **the comparisons between desktops are not valid**:")
        print("     a worse number would say «it is the desktop» when instead it is")
        print("     another version of something else (D5).")
        return 1
    print("⭐ the %d running boxes are aligned on all the %d declared entries"
          % (len(accese), len(DEVE_COMBACIARE)))
    print("⚠ and the DESKTOP is different in each, as it must be: that is the point.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
