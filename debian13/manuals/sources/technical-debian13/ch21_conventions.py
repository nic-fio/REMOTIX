"""Chapter 21 — Conventions. Sources: CLAUDE.md, and what is observed in src/ (log.h, log.c, rcp.h, session.h, cid.h, msgrate.h,
Makefile), debian/, build/, prove/, boxes/ (older), server/, docs/. Counts were taken from the tree on 17 Nov 2026; the rows on build/, prove/, server/ and boxes/ were brought to 1.2.0 on 26 Nov 2026."""
from build import c, h4, note, p, rif, sysf, table, tip, ul, warn

# ── 21.1 ─────────────────────────────────────────────────────────────────────
S1 = p("The rules that are written are in " + c("CLAUDE.md") + ", seven lines of them. Everything else in this chapter is observed in the tree and "
       "said as an observation: where the code does not follow a rule, the chapter says so.", lead=True) + \
    table(["Rule (from CLAUDE.md)", "In practice"], [
        ["Debian trixie only; four desktops; no distribution detection or per-distribution code",
         "see " + rif("Where the code is Debian-specific") + ". A future distribution gets its own separate code"],
        ["code comments in English", "true of the comments. Some identifiers and file names still carry Italian words (next section)"],
        ["reuse the old code; when in doubt keep the old behaviour and note the doubt",
         "the source is the old product with the other distributions removed; many comments carry dates and decision references from its history"],
        ["the old repository is a read-only reference", "nothing in this tree writes to it; it is only named in comments"],
        ["the service is installed disabled and not started; the administrator enables it",
         c("debian/rules") + " passes " + c("--no-enable --no-start") + " to " + c("dh_installsystemd")],
        ["the owner decides how and when tests run", "the checks of " + c("prove/") + " are started by hand; nothing in the package or the build runs them"],
        ["licences ship in the package", c("LICENSE.md") + " is appended to " + c("debian/copyright") + " by " + c("build/build-deb-vm.sh") + " (and by the older " + c("build/build-deb.sh") + "); "
         + c("THIRD-PARTY-LICENSES") + " is installed under " + c("/usr/share/doc/remotix")],
    ], "«TAB» — The written rules and what the tree does with them")

# ── 21.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The text of the project is English: comments, log lines, messages, documents and the page. Italian survives in names, and the manual cites those "
       "names as code because they are the real ones.", lead=True) + \
    table(["Kind", "Convention", "Examples"], [
        "C code",
        ["file", "lower case, one word or snake_case, one module per " + c(".c") + " and " + c(".h") + " pair", c("rcp.c") + ", " + c("render_node.c") + ", " + c("vadirect.c")],
        ["function", "prefix = the module: " + c("rcp_") + ", " + c("wt_") + ", " + c("rootside_") + ", " + c("capture_") + ", "
         + c("session_") + ", " + c("transport_") + ", " + c("input_") + ", " + c("kwin_") + ", " + c("child_") + ", " + c("clipboard_") + ", " + c("budget_"),
         c("rcp_video_codec_set") + ", " + c("child_video_capabilities")],
        ["macro and constant", "UPPER_SNAKE; protocol numbers carry the protocol's prefix", c("T_HELLO") + ", " + c("RCP_SESSION_CAP") + ", " + c("BUDGET_STRAIN_DELAY_MS")],
        ["type", "opaque types are a " + c("typedef struct x x") + " in the header; some enumerations are CamelCase", c("cidkey") + ", " + c("rcp_session") + ", " + c("DesktopSession")],
        ["header guard", c("REMOTIX_<NAME>_H") + " in 45 of the 53 headers; the other eight use the bare " + c("<NAME>_H") + " (" + c("ROOTSIDE_PROTO_H") + ", " + c("BUDGET_H") + ")", c("REMOTIX_LOG_H") + ", " + c("REMOTIX_CID_H")],
        ["module split", "the WHY is in the header and the HOW in the source: " + c("vadirect.c") + " says \"the why is in vadirect.h\"; the same words open "
         + c("shape.c") + " and " + c("walls.c"), ""],
        ["small rules", "several one-rule headers hold the logic of a limit or a gate and are included by the big modules", c("hsrate.h") + ", " + c("msgrate.h") + ", " + c("cid.h")],
        "Public names",
        ["options", "kebab-case, long", c("--session-cap") + ", " + c("--budget-mpixel-s") + ", " + c("--command-socket")],
        ["environment", c("REMOTIX_") + " plus UPPER_SNAKE; read in the unit through " + c("EnvironmentFile"), c("REMOTIX_PORT") + ", " + c("REMOTIX_OPTIONS")],
        ["log areas", "short lower-case words", c("startup") + ", " + c("quic") + ", " + c("wt") + ", " + c("rcp") + ", " + c("page") + ", " + c("cert") + ", " + c("session")
         + ", " + c("video") + ", " + c("budget")],
        ["RCP message and reason names", "UPPER_SNAKE words of the protocol", c("HERE_I_AM") + ", " + c("TERMINATE_SESSION") + ", " + c("ALREADY_ACTIVE_REMOTELY")],
        "Other languages",
        ["page", "one file, " + c("src/page.html") + ", with the script inside; constants UPPER, functions mostly snake_case", c("AUDIO_BUFFER_MS") + ", " + c("CODEC_RCP")],
        ["shell", "tabs for indentation; " + c("set -uo pipefail") + " in the build script and in the server preparation script (no " + c("-e") + ": they test each step themselves) and " + c("set -euo pipefail") + " in the live-USB installer; one status line per step", c("build/build-deb-vm.sh") + ", " + c("server/prepara-server-vm.sh") + ", " + c("server/live-installa.sh")],
        ["python (prove/)", "four spaces, a docstring that says what the check proves and how to run it, verdict lines", c("prove/check-base.py")],
    ], "«TAB» — Naming as observed") + \
    h4("Italian that remains in identifiers") + \
    p("The comments were translated; some names were not. They are real names in the source, and the manual quotes them in code. The counts are of this tree.") + \
    ul([
        c("registro_dice()") + " is the macro every module calls to write a log line (1171 uses); the function behind it is " + c("log_says_in()") + ".",
        "In " + c("src/Makefile") + ": " + c("SORGENTI") + " (sources), " + c("OGGETTI") + " (objects), " + c("PROTOCOLLI") + " (protocols), " + c("GEMELLATI") + " (twinned files), "
        + c("MINIMI") + " (minimum versions), " + c("AVVERTIMENTI") + " (warnings), " + c("deps") + "'s variable " + c("stato") + ", and the generated " + c("GENERATI") + ".",
        "In " + c("rcp.c") + ": short variables such as " + c("lung") + " (length), and comments that name handlers " + c("tratta_*()") + " that no function of that name implements any more.",
        c("wt_chi") + " in the WebTransport module and " + c("codificatore_chiedi_chiave") + " in the encoder code.",
        "In the build and server scripts, output and folder names: " + sysf("costruzione.log") + ", " + sysf("immagine.log") + ", " + sysf("controlli.txt") + ", " + sysf("elenco.txt")
        + ", " + sysf("pacchetti/") + ", " + sysf("prove/") + ", " + c("prepara-server.sh") + ", " + c("fanwatch.py") + " is English.",
        "In the document headings: " + c("docs/DECISIONS.md") + " opens as \"DECISIONI\" and " + c("docs/SPECS.md") + " as \"SPECIFICHE\"; " + c("DECISIONS.md") + " refers to " + sysf("LEZIONI.md")
        + " (the file is " + c("LESSONS.md") + " here).",
    ]) + \
    note("Do not rename an Italian identifier as a side effect of another change. A name is public if a log line, a message, an option or a file name carries it; "
         "those are recorded in the documents as they are.", "Renaming.")

# ── 21.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The comments are long on purpose. A block comment states <b>why</b> a thing is the way it is, with the date, the source and the failure it prevents. "
       "The code is short next to its comments (about 102,000 lines of C and headers in " + c("src/") + " plus a page of 14,255 lines, most of it in a few large files: "
       + c("child.c") + " 12,347 lines, " + c("rcp.c") + " 10,466, " + c("webtransport.c") + " 9,582, " + c("session.c") + " 7,374).", lead=True) + \
    table(["Mark", "Meaning as the sources use it"], [
        ["a star", "a decision or a point of emphasis, usually with a date and a reference to a decision register"],
        ["a prohibition sign", "a hard rule, or a consequence that must not be lost; in a log line it also sets the severity (below)"],
        ["a warning sign", "a caveat, or the cost of a choice; in a log line it sets the warning severity"],
        ["an hourglass", "proposed, not normative, or waiting for the owner's judgement"],
        [c("[M]"), "measured by us, with the date"],
        [c("[R]"), "read in the code of a reference (a compositor, a library, a browser)"],
        [c("[S]"), "read in a specification"],
        [c("[?]"), "assumed, not yet verified"],
    ], "«TAB» — The marks in comments and documents") + \
    ul([
        "<b>The marks of evidence</b> come from " + sysf("CODER.md") + " §5 (cited by " + c("docs/SPECS.md") + " and " + c("docs/DECISIONS.md") + "; that file is not in this repository). "
        "A line in the specification without a mark is a product decision, not a technical fact.",
        "<b>References</b> are by section: " + c("DECISIONS.md") + " §x, " + c("RCP.md") + " §x, " + c("SPECS.md") + " §x. Audit findings are cited by identifier (for example R12.3). "
        "Citing a section that has moved is the usual way a comment goes stale.",
        "<b>The decision register</b> uses three marks for certainty: decided, derived and open (the header of " + c("docs/DECISIONS.md") + "). A derived entry is corrected "
        "without discussion if wrong; a decided one is reopened only by a measurement that contradicts it.",
        "<b>Comments are not always right.</b> The manual follows the rule that the code wins when the two disagree; the places where they were found to "
        "disagree are listed in " + rif("Appendix C — Known issues and open points") + ".",
        "<b>Dead references.</b> Many comments cite files that are not in this repository: " + sysf("CODER.md") + ", " + sysf("REVIEWER.md") + ", " + sysf("STUDIES.md") + ", the " + c("phases/")
        + " folder, " + c("benches/") + " and " + sysf("PHASES.md") + ". They are history, not instructions.",
    ])

# ── 21.4 ─────────────────────────────────────────────────────────────────────
S4 = p("The product is written to fail closed and to say so. The rules below are visible in the sources again and again; each names an example.", lead=True) + \
    table(["Convention", "Example in the tree"], [
        ["A failure is a no, never a maybe (invariant I3: the guard starts from denied).",
         "a login whose check request cannot be sent is refused at once, in " + c("rcp.h") + " (the " + c("ask_verify") + " hook returns false)"],
        ["A fallback or a degradation is declared in the log, so that an intended behaviour can be told from an accident.",
         c("log.h") + " opens with the rule; the ambiguity of two desktops installed is picked and declared"],
        ["What changes what the user sees is born off (invariant I6).", "the bench function is off by default; the budget knob is off by default (" + rif("Quality, degradation and budget") + ")"],
        ["Do not degrade whoever is inside to let someone in (invariant I1: never detach).", "when the budget is full the new session is refused with a reason; the first user is not slowed"],
        ["The session survives the client (invariant I4).", "a closed browser, a killed browser or a cut line leave the desktop running (" + rif("Startup and life cycle") + ")"],
        ["One session per user, remote; a second device is refused (invariant I2).", "reason 0x0F, tested by " + c("check-multiuser.py")],
        ["Count the cases: separate outcomes get separate names.", c("RCP_VIDEO_SENT") + " and the seven other outcomes of " + c("rcp_video_send") + " are eight, not two, "
         "so that the caller can tell \"re-encode smaller\" from \"send a keyframe\""],
        ["Bound everything.", "a whole-run deadline in the checks; ceilings on frames, texts, rates; " + c("_Static_assert") + " (12 in the tree) ties limits that must agree, for example "
         "the usermod limit against the spawn wait in " + c("child.c")],
        ["A message that is not understood is reported, never silently ignored.", "the log line says WHAT was not understood (RCP §3.1), and a protocol error closes with reason 0x0B"],
        ["Exit status carries meaning.", "the service stops its restart loop on 78, which is reserved for a real configuration error (comment in " + c("remotix.service") + ")"],
    ], "«TAB» — Error and fallback conventions") + \
    p("The invariants I1 to I7 are named in the comments and documents; their formal list is in " + sysf("CODER.md") + ", which is not in this tree. The ones whose wording is in "
      "files of the tree are the ones quoted here; do not assume the others from their number alone.")

# ── 21.5 ─────────────────────────────────────────────────────────────────────
S5 = p("Logging has one funnel, " + c("src/log.c") + ", so that rules about what is written can be checked in one place (" + rif("Logging and diagnostics")
       + " describes the mechanism). The conventions a writer of code has to follow:", lead=True) + \
    ul([
        "<b>Always through the macros.</b> " + c("registro_dice(area, fmt, ...)") + " for lines that are always written; " + c("log_detail(area, fmt, ...)") + " for chatter, written "
        "only with " + c("--verbose") + ". Never " + c("fprintf(stderr, ...)") + ". The macros add " + c("__FILE__") + " and " + c("__LINE__") + ", which go to the journal as "
        + c("CODE_FILE") + " and " + c("CODE_LINE") + ".",
        "<b>The first characters of a body set the severity.</b> In the journal, a body that starts with the prohibition mark is priority 3 (error), with the warning mark priority 4, "
        "anything else priority 6, and chatter 7 (" + c("log.c") + ", " + c("log.h") + "). Choose the mark deliberately: an expected event written with the error mark appears in "
        + c("journalctl -p err") + ". " + c("docs/REGISTRO-priorita.md") + " records the 17 Nov 2026 pass that moved routine lines down (33 patterns observed: 5 to info, 24 to warning, 4 left as errors).",
        "<b>The area is part of the call.</b> Use one of the areas declared in " + c("log.h") + " (" + c("LOG_STARTUP") + ", " + c("REG_QUIC") + ", " + c("REG_WT") + ", " + c("REG_RCP")
        + ", " + c("LOG_PAGE") + ", " + c("REG_CERT") + ", " + c("LOG_SESSION") + ", " + c("REG_VIDEO") + ", " + c("REG_BUDGET") + "); a new subject that is read as its own column gets its own area. "
        "The prefixes of these macro names are not uniform (LOG_ and REG_).",
        "<b>Whose line it is.</b> A process that serves one session sets its identity once with " + c("log_identity()") + "; the process that serves all of them passes the identity "
        "with the line through " + c("log_says_of()") + ". A line with no known owner goes out without brackets, never with an empty or a guessed name. The bracket is cut at "
        + c("LOG_IDENTITY_MAX") + " = 48.",
        "<b>Never log a secret or a keystroke.</b> Passwords appear in no line (the funnel exists so that this can be checked). Keys are logged as \"key\" with an evdev code, except "
        "the modifiers, decided by " + c("log_speakable_key()") + ". A typed user name is not logged before the verdict (tested by " + c("typed-names-not-logged") + ").",
        "<b>Rate-limit what a client can trigger.</b> Lines that a hostile or broken client can cause repeatedly are written with a counter and an interval (see the burst line "
        "of " + c("webtransport.c") + " in the priority register).",
        "<b>Say what, not \"error\".</b> A line names the thing that was not understood or that failed and, where there is one, the reason code.",
    ])

# ── 21.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The tree has a few fixed places and a few habits that follow from where a thing runs.", lead=True) + \
    table(["Folder", "Holds", "Note"], [
        [c("src/"), "the product: C sources and headers, " + c("Makefile") + ", " + c("page.html") + ", the PAM file, the polkit rules and helper, " + c("protocols/") + " (XML), "
         + c("opus-wasm/") + " (the audio decoder module)", "built only by " + c("debian/rules") + " on the build VM"],
        [c("debian/"), "packaging: control, rules, maintainer scripts, unit, tmpfiles, sysusers, AppArmor profile, ufw profile, KWin permission file, conf defaults", "the changelog and the licence text are added by the build script"],
        [c("build/"), "the build script for the build VM, the static-library script, and the older container script and image", "see " + rif("Build and release")],
        [c("boxes/"), "the older container test boxes (not used by the VM bench)", "see " + rif("Testing")],
        [c("prove/"), "the checks and their libraries, and " + c("banco-vm/") + " (the face the checks use for the virtual machines)", "run on the dev server"],
        [c("server/"), "dev server set-up, the virtual machine bench (" + c("vm-radeon.sh") + ", " + c("prepara-server-vm.sh") + "), the live-USB installer and the older single-VM and container files", "paths under " + sysf("/media/REMOTIX-DEBIAN")],
        [c("docs/"), "specification, protocol, decisions, lessons, inventories", "the common reference; not copied into this manual"],
        [c("manuals/"), "this manual and the user manual, generated from " + c("manuals/sources/"), "regenerated by " + c("manuals/sources/build.py") + ", checked with " + c("--check")],
        [c("LICENSE.md") + ", " + c("THIRD-PARTY-LICENSES") + ", " + c("licenses/"), "the two files are the licence texts that ship in the package; " + c("licenses/") + " holds one page (" + c("how-it-works.html") + ") that the build script does not copy into the package", "see " + rif("The package")],
    ], "«TAB» — The layout of the tree") + \
    ul([
        "<b>Temporary files never go to " + c("/tmp") + " on the dev server:</b> its root file system is in RAM. The checks keep their work folders in the folder the tree was copied to, on the persistent disk (the older build script set " + c("TMPDIR") + " under its work folder).",
        "<b>Nothing is deleted, moved or overwritten without the owner asking.</b> This binds the scripts too: the build script copies the tree and never edits the working tree.",
        "<b>Scripts print one status line per step</b> (" + c("OK") + " or " + c("FAIL") + ") and keep going where the next step is independent; destructive operations are named in the header "
        "(" + c("check-package.py") + " resets the box, " + c("fresh-vm.sh") + " removes the test users, " + c("check-ban.py") + " bans an address and always unblocks).",
        "<b>Generated files are marked.</b> " + c("vulkanvideo_rgb_nv12_spv.h") + " says in its first line that it is generated and not to be edited by hand.",
        "<b>The manual checks itself against the tree.</b> " + c("python3 manuals/sources/build.py --check") + " verifies that every function, file and " + c("REMOTIX_*") + " variable cited in code form exists, "
        "and flags Italian sentences.",
    ])

CHAPTER = ("Conventions", [
    ("The written rules and what the tree does with them", S1),
    ("Names, language and the Italian that remains", S2),
    ("Comments, marks and references", S3),
    ("Errors, fallbacks and invariants", S4),
    ("Logging conventions for a writer of code", S5),
    ("The layout of the tree and the habits around it", S6),
])
