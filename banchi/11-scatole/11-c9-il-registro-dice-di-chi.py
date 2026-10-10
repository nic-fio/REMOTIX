#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c9 — ⭐⭐ «THE LOG SAYS WHO IS SPEAKING» — the multi-tenant mesh
===========================================================================

    python3 11-c9-il-registro-dice-di-chi.py --porta 8514
    python3 11-c9-il-registro-dice-di-chi.py --certifica
    python3 11-c9-il-registro-dice-di-chi.py --togli-nome tutto   (the fault)

⛔ Why it exists, in one line: **the product is multi-tenant**.  With two
   sessions alive together, a line without a name is a line that **cannot be
   attributed** — and the diagnosis becomes guessing.

`[M]` 25 August 2026, `fasi/10-…md` §6.7, and it is the measurement that gave birth to
the cure R10-A4: with **four** real sessions, only **4.2 %** of the diagnosis
lines said who was speaking, and whoever tried to guess the name **got it wrong
96 times out of 100** — i.e. sent people to look at someone else's desktop.

---------------------------------------------------------------------------
⛔⛔ THE HARDEST RULE IS **WHICH LINE MUST CARRY THE NAME**
---------------------------------------------------------------------------

And the two convenient answers are both wrong, each in its own way:

  «ALL»              ⛔ false, and gives **red forever**: the start-up lines
                     precede any tenant, and naming one would be
                     inventing it.  `LEZIONI.md` §1.49 — a red that cannot be
                     made green is worse than no mesh.
  «THOSE THAT        ⛔ empty: it can **never** give red.  `LEZIONI.md` §1.44
   HAVE IT»          — the predicate that could not fail and had the look of
                     one that passes.

⇒ ⭐ **The mandatory set must be DECLARED, and defended.**  This is ours.

  A LINE IS MANDATORY IF BOTH HOLD:

    1. ⭐ **it sits in the WINDOW** — i.e. in the log slice that goes from the
       mark placed **before** opening the two tenants until the end.
       ⛔ The window is NOT guessed from the content: it is the slice, and that is all.
       ⇒ The server start-up stays outside **by construction**, not by a rule
         that has to recognise it — and it is the reason why this mesh cannot
         give the perpetual red of §1.49.
       ⚠ And there is a price, declared: this way C9 judges **only what
         happened while it was watching**.  An old log is judged with
         `--da-file`, and then the window is the whole file (it is said).

    2. ⭐ **its AREA is a session area** — an area that exists only
       because a session exists:

           figlio · sessione · video · cattura · cursore · input ·
           audio · suono · tastiera · appunti

  AND WHAT IS **EXEMPT**, with the reason for each — ⛔ no exemption
  for convenience:

    · ⛔ **outside the window** — there is no tenant to name.
    · ⛔ **the SERVER areas**: `avvio` `cert` `budget`.  They speak of the
      machine, not of a tenant: the budget in force is **everyone's**, and so is the
      certificate.  ⚠ And `budget` stays exempt **even when it names one**
      («verdict for «c9u1»»): the area speaks of the server, the line is a verdict.
    · ⚠ **the GREETING areas**: `quic` `wt` `rcp` `pagina`.  ⛔ The same area
      serves **two moments**: the handshake — when the user has not
      named themselves yet, and `wt_chi()` returns `""` **on purpose** (`webtransport.c`
      §897: whoever does not know keeps quiet) — and the dialogue afterwards, which has the name.
      ⇒ From the line alone the two moments **cannot be told apart**, and an obligation here
        would be a red on a line that is right to keep quiet.
      ⭐ That is why they are not mandatory, ⛔ **but they are counted and printed separately**:
        it is there that the defect would go back into hiding, and an exemption that
        cannot be seen is an exemption nobody notices.
    · ⭐ **the SUMMARY lines ABOUT EVERYONE**, and they are ONE family only, named
      in full below (`SEGNI_DI_RIEPILOGO`): the guardian's line carries
      `inquilini=N`, i.e. it is a count **about everyone** — naming one would be
      **false**.  ⚠ Without this exemption C9 would give **one red per minute**,
      forever, on a line that is right.

---------------------------------------------------------------------------
⭐ AND «HAVING THE NAME» MEANS TWO THINGS, AND THEY ARE COUNTED SEPARATELY
---------------------------------------------------------------------------

  1. ⭐ **in the identity brackets** — `HH:MM:SS.mmm area   [name] body`.
     It is the canonical form: it is composed by `registro.c riga()`, in one place only, and
     a tool reads it by column.
  2. ⚠ **only in the body** — the line says «c9u1» in the middle of the prose, between
     guillemets, and the brackets are not there.

⛔ The second **counts as attributable** — a man reading the log knows
   who is being spoken of, and calling it red would be a false alarm on 1 line in 4
   (`[M]` below).  ⚠ **But it is fragile**, and it must be said: the prose changes when
   someone rewrites a message, the brackets do not.  ⇒ Its count is printed,
   always, ⭐ **and this mesh delivers it as a FINDING, not as a verdict**.

`[M]` 26 August 2026, box `rete11-lxqt`, two tenants alive together
(`c9u1`, `c9u2`) for 45 s, 5 752 lines of slice, server with `--parlantina`:

       mandatory lines                    5 490
       with the name IN THE BRACKETS      4 084   (74.4 %)
       with the name ONLY IN THE BODY     1 402   (25.5 %)  ⚠ all from the PARENT
       ⛔ WITHOUT A NAME ANYWHERE             4   (0.1 %) ⇒ **RED**
       attributed to c9u1 / c9u2        2 799 / 2 687   ⭐ the strong form holds

⛔⛔ AND THE FOUR ARE A REAL DEFECT OF THE PRODUCT, not of the bench.  Here are the
    eight real lines, taken from the slice of the official round — ⭐ and they read
    by themselves (the product's text of the time; 10 Oct 2026, in English):

       20:19:47.887 rcp      [c9u1] rate of [127.0.0.1]:40258: arretrato…
       20:19:47.895 tastiera modifier 7: key 100 is preferred to 84…
       20:19:47.895 tastiera layout in force: it [Italian]
       20:19:47.895 rcp      [c9u1] slot TAKEN by c9u1 via […]:40258 (1)
       …
       20:19:49.914 figlio   [c9u2] without a stage and SOMEONE IS WATCHING…
       20:19:49.918 tastiera modifier 7: key 100 is preferred to 84…
       20:19:49.918 tastiera layout in force: it [Italian]
       20:19:49.918 rcp      [c9u2] slot TAKEN by c9u2 via […]:46239 (2)

    `[R]` `tastiera.c:486` (`registro_dice`) and `:342` (`registro_dettaglio`)
    write **in the PARENT**, which has no process identity — and in the parent
    the identity belongs to the LINE, not to the process (`registro.h`).  Neither of the
    two goes through `registro_dice_di()`.
    ⇒ Two lines per tenant, **identical word for word**, and with two
      tenants alive ⛔ **there is no way of saying which is whose**: the second
      pair could be attributed to `c9u1` with the same plausibility.
    ⭐ With ONE tenant only they were attributed by exclusion — ⛔ **and it is
      exactly the reason why this mesh opens TWO.**
    ⇒ The cure lies in two lines: `registro_dice_di(REG_TASTIERA, chi, …)` and
      `registro_dettaglio_di(…)`, with the name the parent already has in hand
      (it is the same one it writes in the `rcp` line two milliseconds later).

---------------------------------------------------------------------------
⚠ AND THE CHATTER — what changes, and what does not
---------------------------------------------------------------------------

`11-accendi.sh server` starts the product with `--parlantina`, and that option
switches on `registro_dettaglio*()`.  ⛔ **The question must be asked, and the answer is
measured instead of deduced.**

`[M]` 26 August 2026, same box, same two tenants, control round
with the server restarted **without** `--parlantina`:

                              with chatter       without
       lines of the slice           5 752        4 158
       mandatory lines              5 490        3 990
       with name in brackets        4 084        2 586   (74.4 % → 64.8 %)
       with name only in the body   1 402        1 402   ⭐ IDENTICAL
       ⛔ WITHOUT A NAME                4            2
       outcome                          1            1   ⭐ red both

⭐ **THE VERDICT DOES NOT CHANGE: red in both modes.**  ⚠ But the count does,
   and the two things must be said together:

  · `tastiera.c:486` («layout in force») is `registro_dice()` ⇒ it comes out
    **always**, and it is the red that holds without chatter;
  · `tastiera.c:342` («modifier N: key … is preferred…») is `registro_dettaglio()`
    ⇒ ⛔ **without chatter it does not exist**, and with it there are two more red lines;
  · ⭐ the 1 402 lines «only in the body» are **the very same**: the defect
    of the parent is not a fact of the chatter, it is a fact of the parent.

⇒ ⭐ **With the chatter more lines are looked at** — and they are precisely those that
   `[M]` §6.7 measured at 0.0 % before the cure R10-A4.  ⛔ Whoever runs C9
   on a silent server is not measuring a different thing: **they are measuring
   less of it**, and the percentage with the name in the brackets drops by 10 points because
   the detail lines disappear, which almost all have the name.
   ⚠ The hook runs it with the server of `11-accendi.sh`, i.e. **with** the
     chatter: it is the condition in which the numbers above were taken.

---------------------------------------------------------------------------
⛔ THE GRAFTED FAULT — and here it can be done **on the real data**
---------------------------------------------------------------------------

  · `--certifica` : ⭐ mandatory, **fabricated** logs: one with the name
    (⇒ green), one without (⇒ red), one empty (⇒ 3, «I do not know»), plus the cases
    that keep the mandatory set honest (§1.44, §1.49).
  · `--togli-nome parentesi|corpo|tutto` : ⭐⭐ **the fault on the REAL data, without
    recompiling the product**.  The normal round is opened, and the slice just
    read is defaced in memory before being judged:
        `parentesi` removes `[name] ` right after the area — the canonical form;
        `corpo`     replaces the name inside the prose;
        `tutto`     both ⇒ ⛔ it must turn RED on almost everything.
    ⚠ The log on disk **is not touched**: the copy is defaced.
    `[M]` 26 August 2026, on the real slice of the official round (5 490 mandatory
    lines), lines left WITHOUT A NAME:
        no fault       →      4   (0.1 %)   ⇒ red, and it is the real defect
        `corpo`        →  1 406  (25.6 %)   ⚠ the brackets hold on their own
        `parentesi`    →  3 614  (65.8 %)   ⚠ 1 876 repeat it in the prose
        `tutto`        →  5 490 (100.0 %)   ⛔ all red
    ⇒ ⭐ The judge **can** give red on the real data, and the four numbers are
      **different from each other**: i.e. it is really looking at **two** places, not one
      that pretends to be two.

⭐ And the half that always gets forgotten (`LEZIONI.md` §1.49): the opposite direction
   is tested too — **with the fault removed, it is green again**.  The certification does it.

---------------------------------------------------------------------------
⛔ WHAT C9 DOES **NOT** LOOK AT — and it must be written, or someone will trust it too much
---------------------------------------------------------------------------

  · ⛔ **it does not look at whether the name is THE RIGHT ONE**: it looks at it being there.  A line
    of `c9u1` marked `[c9u2]` is green for C9.  ⚠ Catching it would mean
    knowing what every session was doing, i.e. another mesh.
  · ⛔ **it does not look at the greeting areas** (`quic` `wt` `rcp` `pagina`): it counts them
    and prints them, it does not judge them — the reason is written above.
  · ⛔ **it does not look at the content of the line**: whether it is useful, true or complete
    is none of its business.
  · ⛔ **it does not look at the lines the log did NOT write**: if a whole family
    of messages disappeared, C9 would say green on what remains.
  · ⚠ **it does not look beyond the window**: what happened before the mark
    is not judged (and with `--da-file` the window is the whole file, which is
    another thing and is said).

---------------------------------------------------------------------------
⚠ THE TIME, measured instead of estimated

`[M]` 26 August 2026: **50 seconds** the real round (`--resta 45`), less than a
second the certification.  ⛔ In the fast family **it does not fit**: the ceiling is
180 s and it is already full at 153 (§5.1).  ⇒ C9 sits in `tutto` and in `desktop-nuovo`,
and the hook declares it.  ⚠ Whoever wants it shorter can lower `--resta`, ⛔ but
should know what they are buying: fewer lines looked at, not another test.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)

  0  ⭐ every mandatory line says who is speaking
  1  ⛔ at least one mandatory line cannot be attributed  ⇒ red
  3  ⛔ I could not look — the log is not there, the slice is empty,
     ⛔ **the mandatory set is EMPTY** (§1.44: an empty set is not a
     green), or the two tenants did not both get in (⭐ the strong
     form is TWO, and with one only this mesh has not tested what it says
     it tests) — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «WAS THE CLIENT ADMITTED?» — ⛔ THE PREDICATE IS IMPORTED, NOT
#     REWRITTEN.  Its home is `11-c1-nasce-e-si-vede.py`, and there is ONE (§1.47).
#
# ⛔ Until 27 August 2026 there was `"AMMESSO" in uscita` here, ⭐ and it could not
#    say no: `[R]` `01-b3-cliente.py` prints that word also in the **two
#    refusal messages** — «CONGEDO instead of AMMESSO: reason …» (:1315) and
#    «expected AMMESSO, arrived …» (:1322) — and prints them on **stdout**, which
#    is exactly where it looked.  ⇒ A predicate that cannot fail,
#    `LEZIONI.md` §1.44: the mesh believed it had got in **even when it had been
#    turned away**, and then judged the darkness that followed as a defect of the
#    product.
# ⚠ It was in FIVE meshes with the same line.  ⇒ Curing it five times would have
#   been creating five places to diverge from again (§1.47): it lives in C1, and
#   the other four import it from there.
# ⛔ And if it cannot be imported we exit **3** and say so, ⇒ ⛔ we do not
#   silently fall back on the poor predicate — which is the defect itself.
# ═══════════════════════════════════════════════════════════════════════════
_QUI_C1 = os.path.dirname(os.path.abspath(__file__))
_C1 = None


def _carica_c1():
    """⛔ It is a LOADER, not a judge: it finds the file, it decides nothing.

    ⚠ It is looked for next to me (inside the box everything is in `/opt/remotix`) and
      one level up, as C2, C3 and C6 do with their imported judges.
    """
    for p in (os.path.join(_QUI_C1, "11-c1-nasce-e-si-vede.py"),
              os.path.join(os.path.dirname(_QUI_C1), "11-scatole",
                           "11-c1-nasce-e-si-vede.py")):
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location("c1_ammissione", p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ We VERIFY that what is needed is there, instead of trusting the name
        #    of the file (`CODER.md` §3.9).
        if not callable(getattr(m, "e_stato_ammesso", None)):
            return None
        if not callable(getattr(m, "certifica_ammissione", None)):
            return None
        # ⭐ And from C1 also comes the guarantee of the card's groups: same
        #    reason, same single place (§1.47).
        for mestiere in ("garantisci_i_gruppi", "verdetto_gruppi",
                         "certifica_gruppi"):
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_dell_ammissione():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   comes the predicate «was the client ADMITTED?» — which lives")
        print("   in one place only on purpose (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔ `False` is not a product red: a client turned away is a client
       turned away, and the caller exits **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ THE CARD'S GROUPS — ⛔ and this too lives in one place only (C1).

    Returns `(esito, perche)`: `0` = the tenant sees and it can be measured,
    `3` = ⛔ it is NOT measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification.  ⭐ `[M]` without the groups
       of the `/dev/dri` nodes the session is born BLIND — 0 of 4, never in 90 s, zero
       frames — and this mesh would have measured the darkness calling it
       a product defect (`fasi/10-…` §7.4).
    ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids from the NODES and
       reads back comparing the numbers.  ⛔ No copy of it is made here (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ THE MANDATORY SET, DECLARED HERE AND PRINTED IN EVERY OUTCOME.
#    A verdict without its yardstick is an opinion (C11, same rule).
# ---------------------------------------------------------------------------

# The areas that exist only because a session exists.  ⭐ Taken from the
# product's `#define`s: `registro.h` (REG_*) plus the four `#define AREA` of
# `cattura.c`, `mutter.c` (= "cattura"), `cursore.c` and `input.c`.
AREE_DI_SESSIONE = ("figlio", "sessione", "video", "cattura", "cursore",
                    "input", "audio", "suono", "tastiera", "appunti",
                    # ⭐ phase 14 (src/forma.c, 24 Sep 2026): the dictionary of the
                    #   cursor shape, written by the child WITH the name
                    #   of the tenant.  `[M]` round 1 of the suite, 25 Sep: without
                    #   this entry C9 gave 3 on kde, xfce and lxqt (D-012).
                    "forma")

# ⚠ The same area serves the greeting and the dialogue: they are not judged, they are counted.
AREE_DEL_SALUTO = ("quic", "wt", "rcp", "pagina")

# ⛔ They speak of the machine, not of a tenant.
#
# ⚠⚠ AND THE THREE LISTS ARE EXHAUSTIVE **BY DECLARATION**: an area that is not
#    in any of the three is not exempt — it is a hole, and `analizza` counts it and
#    NAMES it (see there).  ⛔ Copying the product's list by hand is the
#    structural defect of this mesh: C10 **reads** the list from the
#    source of truth (`src/Makefile`), here there is no single place to
#    read — the `#define`s are in `registro.h`, in `figlio.h`, in
#    `appunti.h` and in four scattered `#define AREA`.  ⇒ The defence is not
#    the list: it is that what the list does not know **is seen**.
AREE_DEL_SERVER = ("avvio", "cert", "budget")

# ⭐ The ONLY exemption by content, and it must be named in full: a line that
#    carries a count ABOUT ALL the tenants cannot name one.
#    `sessione guardiano: chiamate=0 … inquilini=2 …` comes out every 60 s.
SEGNI_DI_RIEPILOGO = ("inquilini=",)

# ⛔ The product's line, taken to the letter from `registro.c riga()`:
#       "%s.%03ld %-7s [%s] "   or   "%s.%03ld %-7s "
#    ⚠ The identity is recognised ONLY right after the area.  It is needed, and it shows:
#      «tastiera layout in force: it [Italian]» has a bracket at the end,
#      ⛔ and calling it identity would mean attributing that line to a
#      tenant called «Italian» — i.e. a green bought with an error.
#    ⚠ The characters allowed are those `registro.c` lets through when
#      it cleans the identifier: everything else becomes `_`.
RIGA = re.compile(r"^(\d\d:\d\d:\d\d\.\d\d\d) (\S+) +"
                  r"(?:\[([0-9A-Za-z._@:\-]{1,48})\] )?(.*)$")


class Conto(object):
    """The count, and it is always printed — green or red."""

    def __init__(self):
        self.totali = 0
        self.orfane = 0          # ⛔ lines without a timestamp (registro.c)
        self.obbligate = 0
        self.parentesi = 0
        self.solo_corpo = 0
        self.senza = []          # (area, body) of the red lines
        self.esenti_area = 0
        self.esenti_riepilogo = 0
        self.saluto = 0
        self.saluto_con_nome = 0
        self.per_inquilino = {}  # name -> how many mandatory lines of its own
        self.altri_nomi = {}     # brackets with a name NOT declared
        # ⛔⛔ The areas that NONE of the three lists knows — see `analizza`.
        #     `area -> how many lines`, ⭐ and they are printed BY NAME.
        self.sconosciute = {}

    def righe_sconosciute(self):
        return sum(self.sconosciute.values())


def analizza(testo, nomi):
    """⭐ The judge, and it touches neither network nor disk: it is certified.

    `testo` is **the window** (the slice), `nomi` the DECLARED tenants.
    ⛔ Returns `None` if there is nothing to look at: «I do not know» is not zero.
    """
    if not testo:
        return None
    c = Conto()
    for r in testo.splitlines():
        if not r:
            continue
        c.totali += 1
        m = RIGA.match(r)
        if not m:
            # ⛔ Orphan line: `registro.c` declares that under load two
            #    writes could overlap, and the cure of 21 August
            #    2026 (a single `write` per line) exists for this.  ⚠ A
            #    line of which one does not even know the area is not judgeable:
            #    it is counted separately, and NOT counted as green.
            c.orfane += 1
            continue
        _quando, area, ident, corpo = m.group(1), m.group(2), m.group(3), m.group(4)
        nel_corpo = next((n for n in nomi if n and n in corpo), None)

        if area in AREE_DEL_SALUTO:
            c.saluto += 1
            if ident or nel_corpo:
                c.saluto_con_nome += 1
            continue
        if area not in AREE_DI_SESSIONE:
            # ═══════════════════════════════════════════════════════════════
            # ⛔⛔ AND AN AREA THAT NONE OF THE THREE LISTS KNOWS **IS NOT**
            #     «server stuff».
            #
            # ⚠ Until 27 Aug 2026 there was only `c.esenti_area += 1` here, and
            #   `stampa_conto` presented the count under the label
            #   *«exempt — server areas (avvio cert budget)»*.  ⇒ Everything
            #   that was not in the three lists ended up **mute** inside
            #   that line: `[D]` five hundred lines of an invented area
            #   gave verdict **0** — ⛔ C9 green on 500 lines it had not
            #   looked at, with the face it has when it looks.
            #
            # ⭐ And the irony is that this mesh already has the right sentence
            #   written at the top, for the greeting areas: **an exemption that
            #   cannot be seen is an exemption nobody notices.**
            # ⇒ Now an unknown area is NAMED and COUNTED separately, and
            #   gives outcome **3** — not a red (it is not the product's fault), and
            #   ⛔ above all not a green.  ⚠ It is not a perpetual red
            #   (§1.49): it goes off as soon as someone puts the new area in the
            #   right list, which is exactly the gesture needed.
            # ═══════════════════════════════════════════════════════════════
            if area in AREE_DEL_SERVER:
                c.esenti_area += 1
            else:
                c.sconosciute[area] = c.sconosciute.get(area, 0) + 1
            continue
        if any(s in corpo for s in SEGNI_DI_RIEPILOGO):
            c.esenti_riepilogo += 1
            continue

        c.obbligate += 1
        if ident:
            c.parentesi += 1
            if ident in nomi:
                c.per_inquilino[ident] = c.per_inquilino.get(ident, 0) + 1
            else:
                # ⚠ Attributed, but to someone I had not declared: it is said.
                c.altri_nomi[ident] = c.altri_nomi.get(ident, 0) + 1
        elif nel_corpo:
            c.solo_corpo += 1
            c.per_inquilino[nel_corpo] = c.per_inquilino.get(nel_corpo, 0) + 1
        else:
            c.senza.append((area, corpo))
    return c


def verdetto_ammissione(quanti_ammessi, quanti_aperti):
    """⭐⭐ «Do I have enough tenants to do the test I say I do?»

    ⛔ Separated from the rest on purpose, like `verdetto()`: a rule that reads in
       ten lines and is CERTIFIED is worth more than an `if` in the middle of `main`.

    Returns `(esito, perche)` — `0` means «go on», ⛔ not «green».

    ⭐ The strong form of C9 is **TWO tenants alive TOGETHER**.  If they did not
       both get in, that test was not done — ⛔ and not done does not
       mean failed: a client TURNED AWAY is not a broken product.
    ⚠ `quanti_aperti == 0` means `--da-file`: I did not open them myself, I do not
      demand anything.
    """
    if quanti_aperti == 0:
        return 0, "I did not open the tenants myself: I judge what is there"
    if quanti_ammessi < quanti_aperti:
        return 3, ("%d tenants out of %d got in: the strong form — TWO alive "
                   "together — was not tested" % (quanti_ammessi,
                                                  quanti_aperti))
    return 0, "all the opened tenants got in"


def verdetto(c, quanti_attesi):
    """From the count to the outcome of §4.5.  ⛔ Separated from the analysis on purpose: so the
       rule on «I do not know» reads in ten lines and is certified.

       `quanti_attesi` = how many tenants the bench opened ITSELF.  ⭐ 0 means
       «I did not open them myself» (`--da-file`), and then the strong form is not
       demanded: what is there is judged.
    """
    if c is None:
        return 3, "the log slice is empty: there is nothing to look at"
    if c.totali and c.orfane == c.totali:
        return 3, ("all %d lines are orphans (no timestamp): "
                   "I do not even know which area they belong to" % c.totali)
    # ⛔⛔ THE GUARDIAN OF §1.44, and it is the most important line of this
    #    function: an EMPTY mandatory set would pass any check.
    #    «Zero mandatory lines, zero without a name» looks exactly like a
    #    green, and has looked at nothing.
    if c.obbligate == 0:
        return 3, ("⛔ NO mandatory line in the window: the judgement "
                   "would be green without having looked at anything (LEZIONI §1.44)")
    # ⛔⛔ AND THE ORDER OF THESE TWO CHECKS IS NOT INDIFFERENT — 26 August
    #    2026, ⭐ and it was found by the certification of this very mesh.
    #
    #    In the first draft the «strong form» guard came FIRST.  ⇒ With the
    #    grafted fault (`--togli-nome tutto`) no line names anyone any more,
    #    so «the tenants that speak» are ZERO, ⛔ and the mesh
    #    answered **3** where it had to answer **1**: i.e. the case «the name
    #    is removed ⇒ red» — the reason why C9 exists — did not give red.
    #
    # ⭐ THE RULE, and it is wider than the bug: **a RED does not need the
    #    strong form to be believed; a GREEN does.**  If a mandatory line
    #    cannot be attributed, that is a fact, and it holds even if only one
    #    tenant got in.  The strong form serves to say that the GREEN was
    #    earned with two tenants alive together, not with one.
    # ⇒ That is why the red is decided first, and the guard stays below.
    if c.senza:
        return 1, ("%d mandatory lines out of %d cannot be attributed"
                   % (len(c.senza), c.obbligate))
    # ⛔⛔ AND A GREEN IS NOT GIVEN ON LINES THAT COULD NOT BE CLASSIFIED.
    #    ⚠ It sits AFTER the red, by the same rule as above: a red found
    #      is a judgement already given and it is not watered down into «I do not know».
    if c.sconosciute:
        return 3, ("⛔ %d lines of %d areas I do NOT know how to classify (%s): they "
                   "are neither judged nor exempt, and a green that ignores them "
                   "would be a green that has not looked at them (§1.44)"
                   % (c.righe_sconosciute(), len(c.sconosciute),
                      " ".join(sorted(c.sconosciute))))
    if quanti_attesi >= 2 and len(c.per_inquilino) < 2:
        return 3, ("⭐ the strong form is TWO tenants together, and in the "
                   "window %d speaks: a GREEN like that is not earned"
                   % len(c.per_inquilino))
    return 0, "all %d mandatory lines say who is speaking" % c.obbligate


# ---------------------------------------------------------------------------
# ⛔ THE FAULT ON THE REAL DATA — without recompiling the product, and without touching
#    the log on disk: **the in-memory copy** is defaced.
# ---------------------------------------------------------------------------
def sfregia(testo, nomi, come):
    if come in ("parentesi", "tutto"):
        testo = re.sub(r"^(\d\d:\d\d:\d\d\.\d\d\d \S+ +)"
                       r"\[[0-9A-Za-z._@:\-]{1,48}\] ", r"\1",
                       testo, flags=re.M)
    if come in ("corpo", "tutto"):
        for n in nomi:
            if n:
                testo = testo.replace(n, "x" * len(n))
    return testo


# ---------------------------------------------------------------------------
def stampa_conto(c, nomi, esito, perche):
    print()
    print("  ⭐ THE COUNT — and it is always printed, green or red:")
    print("     total lines in the window          %6d" % c.totali)
    if c.orfane:
        print("     ⚠ of which ORPHANS (no time)       %6d   ⛔ not judgeable"
              % c.orfane)
    print("     ⛔ MANDATORY lines                  %6d" % c.obbligate)
    if c.obbligate:
        print("        · with the name IN THE BRACKETS  %6d   (%4.1f %%)"
              % (c.parentesi, 100.0 * c.parentesi / c.obbligate))
        print("        · with the name ONLY IN THE BODY %6d   (%4.1f %%)  ⚠"
              % (c.solo_corpo, 100.0 * c.solo_corpo / c.obbligate))
        print("        · ⛔ WITHOUT A NAME              %6d   (%4.1f %%)"
              % (len(c.senza), 100.0 * len(c.senza) / c.obbligate))
    print("     exempt — server areas              %6d   (%s)"
          % (c.esenti_area, " ".join(AREE_DEL_SERVER)))
    # ⛔⛔ And the areas nobody knows are printed BY NAME, always: an
    #     exemption that cannot be seen is an exemption nobody notices.
    if c.sconosciute:
        print("     ⛔⛔ AREAS I CANNOT CLASSIFY       %6d   lines, in %d areas"
              % (c.righe_sconosciute(), len(c.sconosciute)))
        for area, q in sorted(c.sconosciute.items(), key=lambda x: -x[1]):
            print("        · %-12s %6d   ⛔ neither mandatory nor exempt: nobody"
                  " has ever judged it" % (area, q))
        print("        ⇒ it must be put in one of the three lists at the top of this")
        print("          mesh (session · greeting · server).")
    print("     exempt — summaries about EVERYONE  %6d   (they carry «%s»)"
          % (c.esenti_riepilogo, "» «".join(SEGNI_DI_RIEPILOGO)))
    print("     ⚠ greeting areas, NOT judged       %6d   of which with the name %d"
          % (c.saluto, c.saluto_con_nome))
    print("       (%s — the same area serves the handshake and the dialogue)"
          % " ".join(AREE_DEL_SALUTO))
    print()
    print("  ⭐ and the STRONG FORM — mandatory lines attributed, per tenant:")
    for n in nomi:
        print("       %-12s %6d" % (n, c.per_inquilino.get(n, 0)))
    for n, q in sorted(c.altri_nomi.items()):
        print("       ⚠ %-10s %6d   (name NOT declared to this mesh)" % (n, q))
    print()
    if c.solo_corpo:
        print("  ⚠ FINDING, not verdict: %d mandatory lines (%.1f %%) name"
              % (c.solo_corpo, 100.0 * c.solo_corpo / max(1, c.obbligate)))
        print("    the tenant ONLY in the prose, not in the identity brackets.")
        print("    ⛔ They are attributable — a man who reads knows who is meant —")
        print("       but the prose changes when someone rewrites a message,")
        print("       and the brackets do not.  ⇒ It is counted, and not judged.")
        print()
    if c.senza:
        print("  ⛔⛔ RED — %d mandatory lines can NOT be attributed."
              % len(c.senza))
        print("     ⭐ And with TWO tenants alive it is not a detail: they are lines")
        print("        identical word for word, one per tenant, and there is no")
        print("        way to say which is whose.")
        viste = {}
        for area, corpo in c.senza:
            chiave = (area, re.sub(r"\d+", "N", corpo)[:110])
            viste[chiave] = viste.get(chiave, 0) + 1
        for (area, corpo), q in sorted(viste.items(), key=lambda x: -x[1])[:12]:
            print("       %4d × %-9s %s" % (q, area, corpo))
    print()
    print("  outcome %d — %s" % (esito, perche))


# ---------------------------------------------------------------------------
def certifica():
    """⛔ The judge must be able to say GREEN, RED and «I DO NOT KNOW» — and it must be
       run, not imagined (§3.6).

       ⚠ And it declares what it covers: **the reading and the rule**.  ⛔ It does NOT cover
         that the product writes the right lines, nor that the name is the
         real one — see «what C9 does not look at» at the top.
    """
    N = ["c9u1", "c9u2"]
    # ⚠ The bodies follow the English text of the product (10 Oct 2026); the judge
    #   does not read them except for the names, so the verdicts do not change.
    sano = (
        "20:07:42.262 rcp     [c9u1] ammesso utente=c9u1 da=[127.0.0.1]:58048\n"
        "20:07:44.294 figlio  [c9u1] entering the stage mounting (canvas 1920x1080)\n"
        "20:07:44.301 figlio  [c9u2] entering the stage mounting (canvas 1920x1080)\n"
        "20:07:45.100 sessione [c9u1] monitor 1/1: connettore «Meta-0»\n"
        "20:07:45.200 cattura [c9u2] canvas REQUESTED from the producer: 1920x1080\n")

    casi = [
        # name, text, expected, expected outcome, extra check (or None)
        ("⭐ all mandatory lines have the name", sano, 2, 0, None),
        # ⛔ THE FAULT: the brackets are removed ⇒ it must turn red.
        ("⛔ the name is removed from the brackets ⇒ RED",
         sfregia(sano, N, "tutto"), 2, 1, None),
        # ⭐ And the half that gets forgotten (LEZIONI §1.49): with the fault removed,
        #    it is green again.  It is the SAME text as before, not defaced.
        ("⭐ and with the fault removed it is GREEN again (§1.49)", sano, 2, 0, None),
        ("⛔ empty log ⇒ «I do not know», not green", "", 2, 3, None),
        # ⛔ §1.44: only start-up lines.  «All» would say red; «those that have
        #    it» would say green.  ⭐ The right answer is «I do not know».
        ("⛔ only START-UP lines: none mandatory ⇒ «I do not know» (§1.44)",
         "15:20:51.193 avvio   REMOTIX — phase 1, the bare wire\n"
         "15:20:51.195 cert    ⭐ two certificates, two fingerprints\n"
         "15:20:51.196 quic    listening over UDP on 0.0.0.0:8514\n", 2, 3, None),
        # ⛔⛔ THE CASE THAT EXPLAINS WHY THE WINDOW IS THE SLICE, and it must be read.
        #    `avvio` and `cert` are exempt by AREA, so they do not bother.
        #    ⛔ But «figlio ⭐ children table on» is the `figlio` area — a
        #       session area — written by the PARENT at start-up, when no tenant
        #       exists yet.  ⇒ Inside a window it is a RED, and it would be a
        #       red forever (§1.49).
        #    ⭐ The cure is not an exception: it is that the normal window starts
        #       AFTER the mark, and that line never enters it.  With `--da-file`
        #       it does, and it is the declared price of that mode.
        ("⛔ with --da-file the START-UP enters the window and gives red: it is the price",
         "15:20:51.193 avvio   REMOTIX — phase 1, the bare wire\n"
         "15:20:51.194 figlio  ⭐ children table on: up to 10\n" + sano,
         2, 1, lambda c: len(c.senza) == 1 and c.esenti_area == 1),
        # ⛔ The guardian's summary line: exempt, or it would be a red per
        #    minute forever.
        ("⭐ the summary about EVERYONE is exempt (or it is a red per minute)",
         sano + "20:08:45.559 sessione guardiano: chiamate=2 inquilini=2 "
                "giri_fermi=0\n", 2, 0,
         lambda c: c.esenti_riepilogo == 1),
        # ⚠ The name only in the prose: attributable, counted separately.
        ("⚠ name ONLY in the body ⇒ green, but counted separately",
         sano + "20:07:46.000 figlio  «c9u1»: the stage for the canvas 1920x1080 "
                "is NOT there YET\n", 2, 0,
         lambda c: c.solo_corpo == 1),
        # ⛔ THE REAL TRAP, and it comes from the measured data: a bracket at the END
        #    is not an identity.  If it were, this line would be attributed to
        #    a tenant called «Italian» ⇒ a green bought with an error.
        ("⛔ «it [Italian]» is NOT an identity ⇒ RED (the real line)",
         sano + "20:07:42.270 tastiera layout in force: it [Italian]\n",
         2, 1, lambda c: len(c.senza) == 1),
        # ⛔ The greeting areas without a name are not red — and they are counted.
        ("⛔ a GREETING line without a name is not red (and it is counted)",
         sano + "20:07:41.261 quic    new connection from [127.0.0.1]:58048\n",
         2, 0, lambda c: c.saluto == 2 and c.saluto_con_nome == 1),
        # ⛔ The server areas: exempt even when they name someone.
        ("⛔ `budget verdict for «c9u1»` is exempt: the area is the server's",
         sano + "20:07:42.250 budget  verdict for «c9u1»: ⭐ AMMESSO\n",
         2, 0, lambda c: c.esenti_area == 1 and not c.sconosciute),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ THE CASE THAT WAS MISSING BEFORE TODAY, and it would have caught the defect of
        #     27 Aug 2026: a NEW session area — a `#define REG_…` that
        #     tomorrow someone adds to the product — fell among the «exempt —
        #     server areas» **without saying anything**.  `[D]` 500 lines of
        #     an area never seen gave verdict **0**.
        # ⚠ The 2 mandatory lines of the healthy text are there and are fine: the
        #   point is precisely that the green would have been «earned» on two
        #   lines ignoring the other five hundred.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ 500 lines of an area NEVER SEEN ⇒ «I do not know», ⛔ NOT a green",
         sano + "".join("20:09:%02d.%03d penna   [c9u1] traccia %d\n"
                        % (i // 60, i % 1000, i) for i in range(500)),
         2, 3, lambda c: c.sconosciute.get("penna") == 500
                         and c.esenti_area == 0),

        ("⛔ and ONE line of an unknown area is enough: there is no threshold",
         sano + "20:09:01.000 penna   [c9u1] traccia 1\n", 2, 3,
         lambda c: c.sconosciute.get("penna") == 1),

        # ⭐ And the half that gets forgotten (§1.49): with the area put in the
        #   right list, the 3 goes off.  ⚠ Here it is simulated exactly so: the
        #   unknown area is `avvio`, which is already in the server's list.
        ("⭐ …and a KNOWN area of the server does not trigger anything (§1.49)",
         sano + "20:09:01.000 avvio   any start-up line\n", 2, 0,
         lambda c: not c.sconosciute and c.esenti_area == 1),

        # ⛔ A real red wins over «I do not know»: the order of the two checks
        #    is that one, and it must be tested instead of remembered.
        ("⛔ an unknown area does NOT water down a red already found",
         sano + "20:09:01.000 penna   [c9u1] traccia 1\n"
                "20:07:42.270 tastiera layout in force: it [Italian]\n",
         2, 1, lambda c: c.sconosciute.get("penna") == 1 and len(c.senza) == 1),
        # ⭐ THE STRONG FORM: two opened, only one speaks ⇒ «I do not know».
        ("⭐ two opened and only one speaks ⇒ «I do not know», NOT green",
         "20:07:44.294 figlio  [c9u1] entering the stage mounting\n", 2, 3, None),
        # ⚠ ...but with --da-file (none opened by me) a single one is fine.
        ("⚠ with --da-file (0 opened by me) a single tenant is judgeable",
         "20:07:44.294 figlio  [c9u1] entering the stage mounting\n", 0, 0, None),
        # ⛔ Orphan lines: all orphans ⇒ I do not know.
        ("⛔ all lines orphan ⇒ «I do not know»",
         "the stage for the canvas 1920x1080 is NOT there YET\nanother broken line\n",
         2, 3, None),
        # ⚠ A name NOT declared: attributed, not «without a name».
        ("⚠ a bracket with an undeclared name is ATTRIBUTED",
         sano + "20:07:44.500 figlio  [provanic7] entering the stage mounting\n", 2, 0,
         lambda c: c.altri_nomi.get("provanic7") == 1 and not c.senza),
        # ⭐ The fault on the REAL DATA, «corpo» direction: the brackets stay, and the
        #    line stays attributable ⇒ green.  It serves to prove that the two
        #    forms are really counted separately.
        ("⭐ only the BODY defaced: the brackets hold ⇒ green",
         sfregia(sano, N, "corpo"), 0, 0, None),
    ]

    print("== certification of C9's judge ==")
    print("   ⛔ it covers THE READING AND THE RULE — not that the product writes the")
    print("      right lines, nor that the name is the real one (see the top)\n")
    guai = 0
    for nome, testo, attesi, atteso, extra in casi:
        c = analizza(testo, N)
        e, perche = verdetto(c, attesi)
        ok = (e == atteso) and (extra is None or (c is not None and extra(c)))
        print("  %s  %-62s  outcome %d (expected %d)"
              % ("OK " if ok else "NO ", nome[:62], e, atteso))
        if not ok:
            guai += 1
            print("        ⛔ why: %s" % perche)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE ADMISSION GUARD — ⛔ the case that was missing before today.
    #    C9 opens TWO tenants: if the server turns them away, the log stays
    #    empty and the old verdict would have charged it to the PRODUCT.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("  ── the admission guard: how many REALLY got in")
    casi_amm = [
        ("⭐ both got in ⇒ go on", 2, 2, 0),
        ("⛔ only one of two ⇒ 3, the strong form was not tested", 1, 2, 3),
        ("⛔ neither of the two (turned away) ⇒ 3, ⛔ NOT a red", 0, 2, 3),
        ("⚠ `--da-file`: I did not open them myself ⇒ what is there is judged",
         0, 0, 0),
        ("⭐ three of three ⇒ go on (it is not nailed down to two)", 3, 3, 0),
    ]
    for nome, amm, ape, atteso in casi_amm:
        e, perche = verdetto_ammissione(amm, ape)
        ok = e == atteso
        if not ok:
            guai += 1
        print("  %s  %-62s  outcome %d (expected %d)"
              % ("OK " if ok else "NO ", nome[:62], e, atteso))

    # ⭐⭐ AND THE «AMMESSO» PREDICATE — it lives in C1, and it is certified with C1's cases:
    #    ⛔ a copy of the cases here would be a second place to diverge from.
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C9")
    guai += guai_amm

    # ⭐⭐ AND THE CARD GROUPS CASES — ⛔ the other case that was missing:
    #    a tenant without the groups of the nodes ⇒ «I could not look», ⛔
    #    never red.  They live in C1 with the step they certify.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C9")
    guai += guai_gr

    quanti = len(casi) + len(casi_amm) + quanti_amm + quanti_gr
    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d cases out of %d wrong"
              % (guai, quanti))
        return 1
    print("⭐ %d cases out of %d: the judge can say green, red and «I do not know»."
          % (quanti, quanti))
    print("⛔ And it can say «I do not know» even when the mandatory set is EMPTY —")
    print("   which is the way a mesh stops looking without saying so.")
    return 0


# ---------------------------------------------------------------------------
def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def apri_inquilini(a, nomi):
    """⭐ THE STRONG FORM: the two are opened TOGETHER, not one after the other.

    ⛔ And «from zero» includes «from zero with respect to myself of yesterday»: the user is
       deleted **before** creating it, or from the second round on it is no longer
       new (`LEZIONI.md`, C1, 26 August 2026).
    Returns (segno, ammessi) or (None, …) if the terrain does not hold.
    """
    for chi in nomi:
        subprocess.run(
            ["/bin/sh", "-c",
             "loginctl terminate-user %s 2>/dev/null; "
             "pkill -KILL -u %s 2>/dev/null; "
             "userdel -r %s 2>/dev/null; rm -rf /home/%s"
             % (chi, chi, chi, chi)], capture_output=True, text=True)
        # ⛔ The card's groups are no longer inside the `useradd`: they are given by
        #    the tool, which READS them from the `/dev/dri` nodes and then READS BACK.
        fatto = subprocess.run(
            ["/bin/sh", "-c",
             "useradd -m -s /bin/bash %s && "
             "printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
            capture_output=True, text=True)
        if fatto.returncode != 0:
            print("⛔ I cannot create the tenant «%s»: %s"
                  % (chi, fatto.stderr.strip()[:90]))
            return None, []
        # ⛔⛔ AND WITHOUT THE CARD'S GROUPS WE DO NOT MEASURE: `[M]` the session
        #     is born blind, and a log that names nobody because nobody
        #     has ever seen anything is not an attribution defect.
        #     ⇒ `None` ⇒ the caller exits **2/3**, ⛔ never red.
        e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="  ")
        if e_gr != 0:
            print("  %s" % perche_gr)
            return None, []

    # ⛔ We mark WHERE we are in the log BEFORE opening: the window is the
    #    slice, and so the server start-up stays outside by construction.
    #
    # ⛔⛔ AND THE MARK IS TAKEN IN CHARACTERS, NOT IN BYTES — 26 August 2026, and
    #    this line cost a FALSE GREEN, the first real round.
    #
    #    The first draft said `segno = os.path.getsize(...)`, i.e. **bytes**,
    #    and then cut `fetta = testo[segno:]`, i.e. **characters**.  ⛔ The
    #    log of this product is full of ⭐ ⛔ ⚠ «» — three bytes each —
    #    so the cut fell **much further on** than the mark: `[M]` the slice
    #    lost its first lines, ⛔ among them the two `tastiera` lines that
    #    are the only real red of this box.
    #    ⇒ The mesh said **0 lines without a name, outcome 0 — green**, while the
    #      log on disk had them, at 20:17:47 and at 20:17:49.
    #
    # ⚠ And the signal that made it be discovered is printed below: **1 ORPHAN
    #   line**.  A cut in the middle of a line produces exactly one, and
    #   a slice taken at a newline produces none.  ⇒ The orphan count
    #   is not an ornament: it is the warning light that the cut is wrong.
    testo = leggi(a.registro)
    if testo is None:
        return None, []
    segno = len(testo)

    processi = []
    for chi in nomi:
        processi.append((chi, subprocess.Popen(
            ["python3", a.cliente, "--indirizzo", a.indirizzo,
             "--porta", str(a.porta), "--utente", chi, "--parola", a.parola,
             "--resta", str(a.resta)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
        # ⚠ A small and DECLARED offset: two `ATTACCA` in the same
        #   millisecond are not the test one wants to do — the test is «two
        #   ALIVE TOGETHER», and they stay together for the whole `--resta`.
        time.sleep(a.sfasamento)

    ammessi = []
    for chi, q in processi:
        try:
            uscita, _ = q.communicate(timeout=max(120, a.resta * 4))
        except subprocess.TimeoutExpired:
            q.kill()
            uscita = ""
        # ⛔ NOT `"AMMESSO" in uscita`: the word is also in the two refusals, and
        #    it arrives on stdout — see `e_stato_ammesso()` at the top.
        #    ⚠ Here the defect bit twice: C9 opens **two** tenants, and
        #    with two refusals the `ammessi` list would have been full while the
        #    log stayed empty ⇒ a red invented on the product.
        stato = e_stato_ammesso(uscita)
        if stato is True:
            ammessi.append(chi)
        else:
            coda = [r.strip() for r in (uscita or "").strip().splitlines()
                    if r.strip() and not r.startswith("==")]
            print("  ⛔ «%s» %s — %s"
                  % (chi, "was TURNED AWAY" if stato is False
                     else "said NOTHING",
                     coda[-1][:80] if coda else "and did not say why"))
    return segno, ammessi


def sgombra(nomi):
    """⭐ Of ONE'S OWN folder only, by name: never a global pattern —
       in phase 10 a global `pkill -f` risked killing the work of
       another test in progress."""
    for chi in nomi:
        subprocess.run(["loginctl", "terminate-user", chi],
                       capture_output=True, text=True)
    time.sleep(1.0)
    for chi in nomi:
        subprocess.run(["pkill", "-KILL", "-u", chi],
                       capture_output=True, text=True)


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inquilini", default="c9u1,c9u2",
                   help="⭐ TWO, and together: it is the strong form of the mesh")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8514)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--resta", type=float, default=45.0,
                   help="how long they stay alive TOGETHER")
    p.add_argument("--sfasamento", type=float, default=2.0,
                   help="how long passes between opening the first and the second")
    p.add_argument("--da-file", default="",
                   help="⚠ judges an already written log instead of opening "
                        "two tenants: ⛔ then the WINDOW is the whole file")
    p.add_argument("--salva-fetta", default="",
                   help="⭐ writes the judged slice here: ⛔ a verdict that "
                        "cannot be reread cannot be contested")
    p.add_argument("--togli-nome", default="no",
                   choices=("no", "parentesi", "corpo", "tutto"),
                   help="⛔ THE GRAFTED FAULT ON THE REAL DATA, without "
                        "recompiling: it defaces the in-memory COPY of the slice")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    nomi = [n for n in a.inquilini.split(",") if n]

    print("== C9 — does the log say WHO is speaking? ==")
    print("   ⭐ the strong form: TWO tenants alive TOGETHER (%s), and every line"
          % ", ".join(nomi))
    print("      that concerns a session must say WHICH of the two.")
    print()
    print("   the MANDATORY set, declared:")
    print("     session areas    : %s" % " ".join(AREE_DI_SESSIONE))
    print("     exempt (server)  : %s" % " ".join(AREE_DEL_SERVER))
    print("     not judged       : %s   ⚠ the greeting does not have a name yet"
          % " ".join(AREE_DEL_SALUTO))
    print("     exempt by count  : the lines that carry «%s»"
          % "» «".join(SEGNI_DI_RIEPILOGO))
    print()

    quanti_attesi = 0
    if a.da_file:
        fetta = leggi(a.da_file)
        if fetta is None:
            print("⛔ I cannot read %s ⇒ I could not look" % a.da_file)
            sys.exit(3)
        print("   ⚠ --da-file: the window is the WHOLE file «%s»." % a.da_file)
        print("     ⛔ So the start-up lines are inside too, which are")
        print("        exempt by area — but a file that contains no")
        print("        mandatory line will give «I do not know», and not a green.")
    else:
        if not os.path.exists(a.cliente):
            print("⛔ I cannot find the test client «%s»" % a.cliente)
            print("   ⇒ I could not look")
            sys.exit(3)
        if leggi(a.registro) is None:
            print("⛔ I cannot read the log «%s»" % a.registro)
            print("   ⇒ I could not look")
            sys.exit(3)
        if len(nomi) < 2:
            print("⛔ TWO tenants are needed: with only one this mesh would not")
            print("   test what it says it tests  ⇒ wrong usage")
            sys.exit(2)

        print("   I open the two, port %d, and they stay alive together %.0f s…"
              % (a.porta, a.resta))
        segno, ammessi = apri_inquilini(a, nomi)
        if segno is None:
            print("⛔ the terrain does not hold: I could not prepare the")
            print("   tenants  ⇒ 2")
            sgombra(nomi)
            sys.exit(2)
        print("   admitted: %s" % (", ".join(ammessi) if ammessi else "⛔ nobody"))
        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ THE GUARD THAT WAS NOT THERE — and without it the cure of «AMMESSO»
        #     would have served no purpose in this mesh.
        #
        # `ammessi` was only printed: ⇒ with the two clients TURNED AWAY C9
        # went on, found the log slice empty or halved, and exited
        # with a verdict on the PRODUCT.  ⛔ The strong form of C9 is «TWO
        # tenants alive TOGETHER»: if they did not both get in, it was not
        # tested — and not tested does not mean broken.
        # ⇒ Outcome **3**, ⛔ and it is not a red (§4.5).
        # ═══════════════════════════════════════════════════════════════════
        e_amm, perche_amm = verdetto_ammissione(len(ammessi), len(nomi))
        if e_amm != 0:
            print()
            print("  ⛔ %s," % perche_amm)
            print("     so there is nothing whose attribution to judge.")
            print("  ⇒ I could not look, outcome %d — ⛔ and a client"
                  % e_amm)
            print("     TURNED AWAY is not a broken product (§4.5, §1.51).")
            sgombra(nomi)
            sys.exit(e_amm)
        fetta = leggi(a.registro)
        fetta = fetta[segno:] if fetta is not None else None
        sgombra(nomi)
        quanti_attesi = len(nomi)

    if a.salva_fetta and fetta is not None:
        try:
            with open(a.salva_fetta, "w") as f:
                f.write(fetta)
            print("   ⭐ judged slice written in «%s» (%d lines): the verdict"
                  % (a.salva_fetta, len(fetta.splitlines())))
            print("      can be reread, and therefore contested.")
        except OSError as e:
            print("   ⚠ I could not save the slice: %s" % e)

    prima = None
    if a.togli_nome != "no":
        prima = analizza(fetta, nomi)
        fetta = sfregia(fetta or "", nomi, a.togli_nome)
        print()
        print("   ⛔⛔ GRAFTED FAULT ON THE REAL DATA: «%s»" % a.togli_nome)
        print("      the log on disk was NOT touched: what is defaced is")
        print("      the in-memory copy.  ⇒ The judgement below MUST be")
        print("      redder than the real one, or this mesh cannot bite.")
        if prima is not None:
            print("      (without fault: %d mandatory, %d without a name)"
                  % (prima.obbligate, len(prima.senza)))

    c = analizza(fetta, nomi)
    esito, perche = verdetto(c, quanti_attesi)
    if c is None:
        print()
        print("  ⛔ %s" % perche)
        print("  outcome 3 — and ⛔ it is not a red (§4.5).")
        sys.exit(3)
    stampa_conto(c, nomi, esito, perche)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ WITH THE GRAFTED FAULT THE OUTCOME IS READ BACKWARDS — and without these
    #     lines C13 becomes a lie.
    #
    # `11-gancio.sh`, in `esegui_maglia`, writes in the log
    # `ha_visto_il_guasto: true` when a grafted mesh exits **0**.  ⛔ The
    # first draft of this mesh exited with the raw verdict (**1**), i.e.
    # precisely in the round of the red it would have written `ha_visto_il_guasto: false`.
    # `[M]` 26 August 2026, first round of the wiring: caught this way.
    #
    # ⭐⭐ AND INVERTING IS NOT ENOUGH, and this is the part that matters: C9 today is
    #    red **even without the fault** (the two lines of `src/tastiera.c`).  ⇒ A
    #    simple «red ⇒ seen» would say «the fault was seen» even if
    #    the injection had done NOTHING, and the certification of the net
    #    would rest on a defect of the product instead of on the injected fault.
    #    ⛔ It is the form of error of `LEZIONI.md` §1.44: a predicate that cannot
    #      fail.
    # ⇒ TWO things are demanded: the verdict is red, **and** the lines without a name
    #   are more than those the real defect had left.
    # ═══════════════════════════════════════════════════════════════════════
    if a.togli_nome != "no":
        senza_prima = len(prima.senza) if prima is not None else 0
        senza_dopo = len(c.senza)
        print()
        print("   ⛔ THE GRAFTED FAULT — and here the outcome is read BACKWARDS")
        print("      lines without a name: %d without the fault  ⇒  %d with the fault"
              % (senza_prima, senza_dopo))
        if esito == 1 and senza_dopo > senza_prima:
            print("   ⭐ THE FAULT WAS SEEN — C9 can still say red,")
            print("      and the red comes FROM THE FAULT, not from the defect that was already there.")
            sys.exit(0)
        if esito == 1:
            print("   ⛔⛔ red, but NOT because of the fault: the lines without a")
            print("      name are the same as before ⇒ the injection did not bite.")
            sys.exit(1)
        # ⛔⛔ AND ONLY 0 AND 1 ARE INVERTED — `LEZIONI.md` §4.5, and C7 already did it
        #     the right way three files further on.  ⚠ Until 27 Aug 2026 here
        #     it exited **1** whatever had happened: a grafted round
        #     that could not look (the two tenants do not get in ⇒
        #     `verdetto` returns 3) said on screen *«I looked and it does not hold»*,
        #     which is false.  ⇒ 2 and 3 are not judgements, and they are let
        #     through as they are.
        if esito == 0:
            print("   ⛔⛔ THE FAULT WAS **NOT** SEEN: the name was removed")
            print("      from all the lines and C9 still says GREEN.")
            sys.exit(1)
        print("   ⚠ I COULD NOT LOOK (outcome %d) — ⛔ and this is NOT «the"
              % esito)
        print("     fault was not seen»: it is a test that did not run.")
        print("     ⇒ I exit %d, and 2 and 3 are not turned upside down (§4.5)." % esito)
        sys.exit(esito)

    sys.exit(esito)


if __name__ == "__main__":
    main()
