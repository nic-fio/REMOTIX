from build import c, code, note, p, rif, table, tip, ul, warn

# Every number in this chapter comes from the phase 20 campaigns (7–10 Oct 2026), read from the files of
# /media/REMOTIX/misure/fase16 and from banchi/16-stress/16-rapporto.py; fasi/20-le-prestazioni.md §8 holds
# the same tables with the details.


def cell(remotix, xrdp):
    """One cell of the comparison: REMOTIX in bold, then xrdp; each as «true GREEN / good»."""
    return f"<b>{remotix}</b> · {xrdp}"


# ── 1. What was measured ──────────────────────────────────────────────────
S1 = p("This chapter answers one question for whoever maintains REMOTIX: <b>how much load does the product carry "
       "while still working</b>, on which hardware, and how does that compare with xrdp, the X11 remote desktop "
       "server most Linux administrators would otherwise install. Every figure was measured once, on one machine, "
       "between 7 and 10 October 2026, and is tied to that hardware and that date.", lead=True) + \
    table(["", "Value"], [
        ["Machine", "Intel Core i5-13500T (14 cores, 20 threads), <b>31 GB</b> RAM, Debian 13, kernel 7.0"],
        ["Card 1", "<b>Intel UHD 770, the GPU integrated in the processor</b> — REMOTIX encodes with VA-API"],
        ["Card 2", "<b>AMD Radeon RX 6800</b> (a 2020 high-end gaming card) — REMOTIX encodes with Vulkan Video, "
         "RADV 25.0.7 as shipped by Debian 13"],
        ["REMOTIX", "commit " + c("716e35b") + ", admission budget off (" + c("--budget-mpixel-s 0") + "), session "
         "ceiling raised to 17 so that the short check fits at the top step; clients Firefox 153.4 ESR and Chrome 154"],
        ["xrdp", "0.10.1-3.1+deb13u2 with xorgxrdp 1:0.10.2-1, Debian's configuration untouched (" + c("dpkg --verify")
         + " clean); RemoteFX compression on the CPU (Debian builds xrdp without H.264); clients FreeRDP 3.15.0"],
        ["Desktops", "GNOME, KDE Plasma, XFCE, LXQt — each in its own box; xrdp runs the same boxes on X11"],
        ["Screen sizes", "4K (3840×2160), 3K (3200×1800), 2K (2560×1440), Full HD (1920×1080)"],
        ["Campaigns", c("intel-f20") + ", " + c("amd-f20") + " (REMOTIX, 7–9 Oct) · " + c("intel-x20") + ", "
         + c("amd-x20") + " (xrdp, 9 Oct 17:47 → 10 Oct 16:09 UTC) — 64 climbs in all"],
    ], "«TAB» — The hardware and the software under test") + \
    warn("these are the numbers of <i>this</i> machine, and the Intel card is an integrated one. They are design "
         "evidence, not promises: " + c("DECISIONI.md") + " §10.26 keeps them out of " + c("SPECIFICHE.md")
         + ", and nothing here should be read as the capacity of a different machine.", "Declare the hardware.")

# ── 2. The bench, the scene, the classes ─────────────────────────────────
S2 = p("The bench is the stress harness of " + c("banchi/16-stress/") + ", described in "
       + rif("Stress and capacity benches") + ". In short: real browsers on the server, one per user, each in its "
       "own headless compositor, drive real desktops with input sent through the page; four fixed workloads rotate "
       "by user number; every session and every level is classified against frozen thresholds.", lead=True) + \
    table(["Workload", "Users", "What it does"], [
        ["A browsing", "1, 5, 9, 13", "Firefox ESR in kiosk mode inside the session: loads, scrolls, clicks"],
        ["B file manager", "2, 6, 10, 14", "creates and deletes folders, opens and closes windows"],
        ["C terminal", "3, 7, 11, 15", "types commands, scrolls a file"],
        ["D video", "4, 8, 12, 16", "a local 4K film (Blender Foundation, CC-BY) at 30 frames/s, full screen, for the whole level"],
    ], "«TAB» — The scene, identical for REMOTIX and xrdp") + \
    p("<b>The climb.</b> Steps of 1 → 4 → 8 → 12 → 16 users, 10 minutes each (30 at the last), a repetition of any "
      "significant DEGRADED, and a bisection to one user between the last good step and the broken one. At every "
      "step one more session (user 99) logs in and runs the short functional check: a level where nobody else can "
      "get in is not a healthy level. If 4K breaks, the climb is redone at 3K, then 2K, then Full HD.") + \
    p("<b>Two numbers per climb</b>, both written by " + c("16-coda.sh") + " in the queue log:") + \
    ul(["<b>true GREEN</b> (" + c("ultimo GREEN vero") + "): the highest level where <i>every</i> session is GREEN "
        "— the «optimal up to» of the public table;",
        "<b>good</b> (" + c("buono") + "): the highest level the climb passed, admitting a non-significant DEGRADED "
        "(at most one session in four, inside the first half of its band) — the «holds up to»."]) + \
    p("A level is FAIL if one session is FAIL, which includes the short check. The thresholds (input → frame delay, "
      "frames skipped, longest freeze, video frames painted per second, audible sound, birth time, drops, memory "
      "growth) are those of " + c("SOGLIE") + " in " + c("16-classifica.py") + ", approved on 25 Sep 2026 and "
      "frozen; the table is in " + rif("Stress and capacity benches") + ".") + \
    note("until 10 Oct 2026 the actor rebuilt the time of Firefox's keystrokes from the return of the Marionette "
         "chain; a held-back chain moved keys after their own echo and produced false freezes of ~1.1 s (the next "
         "cursor blink). The probe the actor injects now stamps every " + c("keydown") + " in the page clock, and "
         + c("16-riclassifica.py") + " re-judges finished climbs from their files. Run on all 32 REMOTIX climbs "
         "(every one exited 0), it changed exactly three cells: Intel GNOME 3K 1 → 4, Intel XFCE 3K 4 → 8, Intel "
         "XFCE Full HD 1 → 12. The tables below are re-judged. Chrome, which types through CDP with real times, "
         "never had the defect, and neither does the xrdp actor (XTEST).", "The Firefox freeze, cured.")

# ── 3. Capacity per card and desktop ──────────────────────────────────────
INTEL = table(["Desktop", "4K", "3K", "2K", "Full HD"], [
    ["GNOME", cell("1 / 1", "— / —"), cell("4 / 4", "1 / 1"), cell("4 / 8", "1 / 1"), cell("11 / 11", "5 / 5")],
    ["KDE", cell("3 / 3", "— / —"), cell("1 / 5", "1 / 1"), cell("4 / 8", "1 / 1"), cell("10 / 10", "1 / 1")],
    ["XFCE", cell("4 / 8", "— / —"), cell("8 / 8", "1 / 1"), cell("10 / 10", "3 / 3"), cell("12 / 12", "6 / 6")],
    ["LXQt", cell("7 / 7", "— / —"), cell("8 / 8", "1 / 1"), cell("10 / 10", "3 / 3"), cell("11 / 11", "6 / 6")],
], "«TAB» — Intel UHD 770 (integrated): users that hold, <b>REMOTIX</b> · xrdp, each as true GREEN / good")

AMD = table(["Desktop", "4K", "3K", "2K", "Full HD"], [
    ["GNOME", cell("— / —", "— / —"), cell("4 / 10", "1 / 1"), cell("11 / 11", "1 / 1"), cell("11 / 11", "4 / 6")],
    ["KDE", cell("— / —", "— / —"), cell("4 / 9", "1 / 1"), cell("15 / 15", "1 / 1"), cell("15 / 15", "1 / 1")],
    ["XFCE", cell("2 / 2", "— / —"), cell("12 / 13", "1 / 1"), cell("15 / 15", "3 / 3"), cell("15 / 15", "6 / 6")],
    ["LXQt", cell("3 / 3", "— / —"), cell("15 / 15", "1 / 1"), cell("15 / 15", "3 / 3"), cell("15 / 15", "6 / 6")],
], "«TAB» — AMD Radeon RX 6800: users that hold, <b>REMOTIX</b> · xrdp, each as true GREEN / good")

S3 = p("Each cell gives REMOTIX first, in bold, then xrdp; «—» means not even one user. The xrdp figures carry the "
       "shared-memory note of " + rif("REMOTIX against xrdp") + ".", lead=True) + INTEL + AMD + \
    ul(["<b>15 is the bench's ceiling, not the Radeon's.</b> In the seven cells at 15 the 16-user level fails only "
        "because the 17th session, the short check, paints nothing within 90 s; the sixteen working users are all "
        "GREEN (for example " + c("amd-f20-fhd-xfce") + ", level 16 repeated: 16 GREEN, 1 FAIL — the check).",
        "<b>Radeon 4K on GNOME and KDE is the driver.</b> RADV 25.0.7 accepts the " + c("ULTRA_LOW_LATENCY")
        + " tuning that " + c("src/vulkanvideo.c") + " asks for but does not pass it to the firmware: frames come "
        "out in groups, and one user's delay is 51–56 ms against a 50 ms threshold. The Debian backport of Mesa "
        "26.1.6 brings GNOME 4K to 4 users (1 user: 21 ms); the product stays on the driver Debian 13 ships.",
        "<b>The public table</b> (" + c("fasi/20-le-prestazioni.md") + " §5) is the range over the four desktops:"])

S3 += table(["Card and path", "Screen", "Optimal up to (true GREEN)", "Holds up to (good)"], [
    "i5-13500T, 31 GB · Intel UHD 770 (integrated) · VA-API",
    ["", "4K", "1–7 users", "1–8 users"],
    ["", "3K", "1–8", "4–8"],
    ["", "2K", "4–10", "8–10"],
    ["", "Full HD", "10–12", "10–12"],
    "i5-13500T, 31 GB · AMD Radeon RX 6800 · Vulkan",
    ["", "4K", "0–3", "0–3"],
    ["", "3K", "4–15", "9–15"],
    ["", "2K", "11–15", "11–15"],
    ["", "Full HD", "11–15", "11–15"],
], "«TAB» — The public capacity table, worst to best desktop")

# ── 4. What limits ───────────────────────────────────────────────────────
S4 = p("At the first level that is not GREEN, " + c("16-rapporto.py") + " names the busiest resource and the "
       "process sets that consume it. The answer is almost never the " + c("remotix") + " process.", lead=True) + \
    table(["Where it gives way", "Cells", "What saturates"], [
        ["The GPU's <b>render engine</b> (composition)", "Intel: KDE at 4K, 3K and 2K; XFCE 4K",
         "98–99 % busy, 58–69 % of it the desktops' compositors and 25–31 % the bench's browsers"],
        ["The machine's <b>RAM</b>", "Intel: the other cells; Radeon: GNOME at every size",
         "98–99 % used at the break; ~5 GB of it are the 11–12 client browsers the bench runs on the same server"],
        ["The GPU's <b>video engine</b> (encoding)", "Radeon: KDE, XFCE and LXQt at 2K, 3K and Full HD",
         "about 100 % at 14–16 users, mostly " + c("remotix") + "'s own encoder"],
        ["The <b>driver</b>", "Radeon 4K GNOME and KDE", "RADV 25.0.7, see above"],
    ], "«TAB» — The bottlenecks of the REMOTIX climbs") + \
    p("This is the physics of " + c("DECISIONI.md") + " §4.6-nonies, seen again on all four desktops: on the "
      "integrated card the neck is <b>composition</b>, upstream of REMOTIX, and its currency is the composed pixel. "
      "That is why the admission budget of " + c("src/budget.c") + " (" + c("SPECIFICHE.md") + " §5.5; "
      + rif("The composition budget") + ") counts composed Mpixel/s and the delay of those already inside, and "
      "refuses a newcomer with " + c("BUDGET_PIENO") + " rather than slowing everyone down. The campaigns ran with "
      "the budget <i>off</i> on purpose, to find the cliff; the product's default ceiling is 10 sessions ("
      + c("--tetto-sessioni") + ").") + \
    tip("to switch the budget on for a machine like this one, take the composed Mpixel/s of the last true GREEN "
        "level of the desktop and size you serve, and pass it to " + c("--budget-mpixel-s") + " as described in "
        + rif("Configuring quality and capacity") + ". On the Radeon the encoder, not composition, is what fills "
        "first: the budget then protects a resource it does not count directly, and the ceiling is the simpler "
        "lever.", "Using the numbers.")

# ── 5. REMOTIX against xrdp ───────────────────────────────────────────────
S5 = p("xrdp ran the same scene, the same steps and the same thresholds, in the same desktop boxes switched to X11 "
       "(" + c("Contenitore.xrdp") + "), driven by " + c("16-attore-rdp.py") + ": FreeRDP in a private Xvfb per "
       "user, XTEST for input, XDamage for paint times. Three things cannot be compared by construction: skipped "
       "frames, holes in the video chain and audible sound do not exist on the xrdp side; the delay is compared only "
       "as seen by the viewer.", lead=True) + \
    table(["At 4 users", "REMOTIX Intel", "REMOTIX Radeon", "xrdp Intel", "xrdp Radeon"], [
        ["Machine CPU, Full HD", "10.9–12.5 %", "10.4–12.5 %", "18.1–31.8 %", "18.2–31.0 %"],
        ["Machine CPU, 2K", "11.2–13.3 %", "10.7–13.0 %", "23.0–38.6 %", "23.0–40.3 %"],
        ["Server-side cores, Full HD (GNOME · KDE · XFCE · LXQt)", "0.93 · 1.11 · 1.08 · 1.05",
         "0.95 · 1.10 · 1.10 · 1.07", "4.31 · 3.22 · 1.61 · 1.53", "4.16 · 3.18 · 1.63 · 1.54"],
        ["Server-side memory (PSS), Full HD", "2.4 · 3.1 · 1.8 · 1.9 GB", "2.7 · 3.5 · 2.0 · 2.0 GB",
         "4.1 · 4.8 · 2.9 · 2.8 GB", "4.1 · 4.8 · 2.9 · 2.8 GB"],
        ["Video user, frames painted per second (film at 30)", "29.0–30.3 on every GREEN level", "the same",
         "23.1–24.9 on every level", "the same"],
    ], "«TAB» — Cost and video at equal work («server side» = the server plus the users' desktops and applications)") + \
    ul(["<b>Under load REMOTIX is lighter.</b> xrdp spends 1.5 to 4.6 times the server-side cores (the most on "
        "GNOME: Mutter on X11, xorgxrdp's capture and RemoteFX all on the CPU) and 1.3 to 1.7 times the memory. "
        "REMOTIX moves the work to the card. With a single user xrdp is the cheaper one on XFCE and LXQt (1.9–2.6 % "
        "of the machine against 4.3–4.9 %): a FreeRDP client weighs less than a browser. The gap opens with load.",
        "<b>Video.</b> xrdp loses about one frame in five or six at every level, alone or loaded: RemoteFX on the "
        "processor is the ceiling, not the load. It sits right on the GREEN threshold (0.8 × 30 = 24) and falls "
        "below it on GNOME 2K with 4 users (DEGRADED). REMOTIX paints the full 30 with no frame skipped until the "
        "break level. (On KDE the page counts 53–58 paints per second: the compositor's repaints, not the film's frames.)",
        "<b>Delay with one user is even.</b> Key → image p95: Intel Full HD 36–39 ms REMOTIX against 33–44 xrdp; "
        "Intel 4K 53–67 against 33–55, xrdp ahead on XFCE and LXQt; Radeon 2K and Full HD 33–45 against 32–45. "
        "The meter favours xrdp: the page's round trip includes decoding and painting in the browser, XDamage on "
        "Xvfb does not. REMOTIX's advantage is holding up under load, not one user's response."]) + \
    p("<b>Where xrdp breaks, and the shared-memory wall.</b> Most xrdp failures are not the working users: they "
      "are the next session failing to start. xorgxrdp captures each session into a shared-memory area of "
      "<b>width × height × 4 bytes</b> (the " + c("rdpClientConAllocateSharedMemory") + " lines in "
      + c("journal-scatola.log") + "), and when " + c("/dev/shm") + " is full the new session's Xorg dies with "
      + c("Caught signal 7 (Bus error)") + " in " + c("rdpCapture") + " (" + c("diagnosi-sessione.txt") + " of the "
      "short check). The boxes are started by " + c("11-accendi.sh") + " without " + c("--shm-size") + ", so they "
      "get podman's default of 64 MiB, and the arithmetic matches the climbs step by step:") + \
    table(["Screen", "Bytes per session (logged)", "Sessions that fit in 64 MiB", "Users + check", "xrdp measured on XFCE, LXQt"], [
        ["4K", "33,423,360", "1 (the second fits by a hair and fails)", "0 + 1", "—"],
        ["3K", "23,756,800", "2", "1 + 1", "1"],
        ["2K", "15,073,280", "4", "3 + 1", "3"],
        ["Full HD", "8,355,840", "7 (the eighth fits by a hair and fails)", "6 + 1", "6"],
    ], "«TAB» — The shared-memory wall of xorgxrdp in the test boxes") + \
    p("On XFCE and LXQt the wall <i>is</i> xrdp's limit; on GNOME and KDE xrdp gives way earlier for reasons of its "
      "own (GNOME: delay p95 of 67 ms with 2 users at 2K, 40–42 % of the machine's CPU with 6 at Full HD; KDE: input "
      "lost, 3 actions out of 3 without effect with 2 users at 3K, 2K and Full HD, on both cards).") + \
    warn("this is a difference of architecture, and it is how the project reads it: xorgxrdp needs width × height "
         "× 4 bytes of shared memory per session, REMOTIX needs none — frames travel from the card to the encoder "
         "as DMA-BUFs, and the few memory buffers it does use (the fallback path of " + c("src/wlroots.c") + ", the "
         "keymap) come from " + c("memfd_create") + ", which does not live in " + c("/dev/shm") + " — and in the <i>same</i> boxes, "
         "with the <i>same</i> 64 MiB, REMOTIX admitted 16 users. In the user's words (10 Oct 2026): «4K is a limit "
         "for everyone … the numbers speak clearly: REMOTIX is more efficient and performs better than xrdp thanks "
         "to its newer architecture». Declare it next to every xrdp capacity figure all the same: on an ordinary "
         "installation " + c("/dev/shm") + " is half the RAM (16 GB here) and the wall is not there, so the xrdp "
         "cells for XFCE and LXQt are a <b>lower bound</b> set by the box. The verdict on CPU, memory and video "
         "does not depend on it: it was measured on the users who were inside.", "The 64 MiB wall.")

# ── 6. Limits of the measurements ─────────────────────────────────────────
S6 = p("What the numbers above do not say, and why.", lead=True) + \
    ul(["<b>One machine</b>, and a modest one where it matters: the Intel card is the integrated UHD 770.",
        "<b>The clients run on the server.</b> Up to 16 real browsers for REMOTIX (≈ 5 GB of RAM at 11–12 users: the "
        "memory that runs out on the Intel at 2K and Full HD), FreeRDP for xrdp (1.8–2.4 cores at 4 users, decoding "
        "RemoteFX). REMOTIX's numbers are therefore a lower bound; the network is not measured (everything goes "
        "through " + c("lo") + ").",
        "<b>The bench's ceiling</b> is 16 users plus the check; seven Radeon cells stop at 15 because of the 17th session.",
        "<b>The memory guard</b> of the xrdp climbs (the level closes below 3 GiB free) was never reached by xrdp "
        "(at most 40 % used). REMOTIX had no such guard; on the Intel it would have fired at the break levels, where "
        "the level is already FAIL.",
        "<b>Not comparable:</b> skipped frames, video-chain holes and audio exist only on the REMOTIX side; GPU "
        "engine readings are empty for xrdp; the delay is compared only as seen by the viewer.",
        "<b>The 64 MiB wall</b> cuts xrdp's XFCE and LXQt cells (" + rif("REMOTIX against xrdp") + ").",
        "<b>The driver decides two cells</b>: on the Radeon at 4K, GNOME and KDE stop at RADV 25.0.7, not at REMOTIX."])

# ── 7. Repeating the measurements ────────────────────────────────────────
S7 = p("A campaign is a queue of climbs that runs unattended on the test machine for one to two days per card. "
       "Never run it while someone uses the machine, and never two at once: performance is not measured in parallel.",
       lead=True) + \
    code("""
# on the test machine, as nicfio: the two REMOTIX campaigns, Intel then Radeon
sudo systemd-run --unit=r20-campagna --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \\
     -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue \\
     bash /media/REMOTIX/src/controllo/banchi/16-stress/16-campagna.sh intel-f20 amd-f20

# the same for xrdp: every climb gets --sistema xrdp, and the queue must never be the OOM victim
sudo systemd-run --unit=r20-xrdp --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 -E REMOTIX_16_SISTEMA=xrdp \\
     -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue -p OOMScoreAdjust=-900 \\
     bash /media/REMOTIX/src/controllo/banchi/16-stress/16-campagna.sh intel-x20 amd-x20

# stop between two climbs, or now
touch /media/REMOTIX/misure/fase16/FERMA
sudo systemctl stop r20-campagna
""", "bash", "Starting and stopping a campaign") + \
    table(["Step", "What to do", "Why"], [
        ["Before", "Build the binary, copy it to " + c("rete11/prodotto") + " and write " + c("VERSIONE")
         + " next to it (" + c("<commit> <md5 of 8>") + "); run the short regression suite of phase 15 on the four "
         "desktops; check the machine is empty (no tenants, no leftover compositors or browsers)",
         "a climb reads the product's commit from there; a red suite means nothing is measured"],
        ["During", "Read " + c("coda-<label>.log") + ": one line per climb with «good», «break» and «true GREEN», "
         "and the estimate of the hours left", "a stalled machine loses its root in RAM and the ssh key"],
        ["After", c("16-rapporto.py --registro <register> --campagne intel-f20 amd-f20 --testo"),
         "the matrix, the curve of every climb and the bottleneck at the first non-GREEN level"],
        ["After", c("16-riclassifica.py --salita <climb>") + " for every climb measured before the keystroke cure",
         "writes " + c("riclassificata.json") + " next to the data and exits 2 if the re-judgement is not the climb's own"],
    ], "«TAB» — A campaign, before, during and after") + \
    p("Results land in " + c("/media/REMOTIX/misure/fase16/<label>-<size>-<desktop>/") + ": " + c("salita.jsonl")
      + " (one line per level), and per level " + c("classifica.log") + ", " + c("risorse.jsonl") + ", the server and "
      "box journals and the actors' " + c("stato.jsonl") + ". The registers " + c("registro.jsonl") + " and "
      + c("registro-xrdp.jsonl") + " in " + c("banchi/16-stress/") + " accumulate every classification; for a "
      "repeated level the last one wins.") + \
    note("the measurement folders are treated as read-only evidence. When an analysis has to write beside the "
         "data without touching it, build a shadow tree — a real directory per climb and per level, with symbolic "
         "links to every original file — and run " + c("16-riclassifica.py") + " on that: this is how the "
         "re-judgement described in " + rif("The bench, the scene and the classes") + " was produced on 10 Oct 2026.",
         "Read-only data.") + \
    p("A full matrix costs about 22 hours of machine on the Intel and 28 on the Radeon for REMOTIX, about 11 and 11 "
      "for xrdp (it breaks earlier). The phases that produced these figures are " + c("fasi/16-stress-e-capacita.md")
      + " (method and thresholds) and " + c("fasi/20-le-prestazioni.md") + " (this campaign, its anomalies and the "
      "comparison).")

CHAPTER = ("Performance and capacity", [
    ("What was measured, and on what", S1),
    ("The bench, the scene and the classes", S2),
    ("Capacity per card and desktop", S3),
    ("What limits capacity", S4),
    ("REMOTIX against xrdp", S5),
    ("Limits of the measurements", S6),
    ("Repeating the measurements", S7),
])
