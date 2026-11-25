"""Chapter 21 — Conventions (Fedora 45 tree). Sources: CLAUDE.md of fedora45/, and what is observed in src/ (log.h, log.c, rcp.h, session.h, cid.h, msgrate.h,
Makefile), rpm/, selinux/, build/, prove/, server/, docs/. Counts were retaken in this tree on 25 Nov 2026."""
from build import c, h4, note, p, rif, sysf, table, tip, ul, warn

# ── 21.1 ──────────────────────────────────────────────────────────────
S1 = p("The rules that are written are in " + c("CLAUDE.md") + ", nineteen lines in this tree, written for Fedora 45. Everything else in this chapter is observed in the tree and said as an observation: where the code does not "
       "follow a rule, the chapter says so.", lead=True) + \
    table(["Rule (from CLAUDE.md)", "In practice in this tree"], [
        ["Fedora 45 only; no distribution detection; never touch the folders of the other distributions; change only what Fedora requires",
         "the tree is a separate copy, started on 21 Nov 2026 from the Ubuntu one. The product does read the machine for session names and the distribution's session; see " + rif("Where the code depends on the distribution")
         + " and " + rif("The one-distribution rule")],
        ["development goes one desktop at a time: GNOME, then KDE (KWin 6.8 alone, no patched labwc), XFCE, LXQt", "the order of the plan (" + c("PIANO.md") + "); the studies are in " + c("studio/") + " (1 to 4 one per desktop, 5 the KDE project)"],
        ["code comments in English", "true of the comments. Some identifiers and file names still carry Italian words (next section), and so do the notes of the work (" + c("docs/REGISTRO-problemi.md")
         + ", " + c("PIANO.md") + ", " + c("studio/") + ")"],
        ["every closed or postponed problem gets a register entry", "the entries F1 to F36 of " + c("docs/REGISTRO-problemi.md") + "; the entries A to E are inherited from Ubuntu and were not tried on Fedora"],
        ["SELinux stays enforcing; the package ships its own policy module", c("selinux/remotix.te") + ", " + c(".fc") + ", " + c(".if") + " are built by the spec; every right is written one by one with its reason in the " + c(".te") + " and was verified in enforcing, never with permissive mode or " + c("semodule -DB") + " (F27, F28)"],
        ["the service is installed disabled", c("%systemd_post") + " in the spec and the Fedora preset (" + c("disable *") + "): the service stays off until the administrator runs " + c("systemctl enable --now remotix")],
        ["NO containers, no podman: build and test only on the VMs of server/vm-radeon.sh", "the package is built by " + c("build/build-rpm.sh") + " on the VM " + c("costruzione") + "; the tests run on the four desktop VMs (" + rif("The VM bench") + ")"],
        ["the checks are started by hand", "the checks of " + c("prove/") + " are started by hand; nothing in the package or the build runs them"],
        ["test VMs start from the snapshot codec", "a clean install plus the RPM Fusion codecs, which REMOTIX requires on Fedora (decision D1)"],
        ["licences ship in the package", "the spec installs " + c("LICENSE.md") + " (" + c("%license") + ") and " + c("THIRD-PARTY-LICENSES") + " (" + c("%doc") + "); "
         + c("licenses/how-it-works.html") + " is not installed by the spec"],
    ], "«TAB» — The written rules and what the tree does with them")

# ── 21.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The text of the product is English: comments, log lines, messages and the page. Italian survives in names, and in the working documents of the "
       "project; the manual cites those names as code because they are the real ones.", lead=True) + \
    table(["Kind", "Convention", "Examples"], [
        "C code",
        ["file", "lower case, one word or snake_case, one module per " + c(".c") + " and " + c(".h") + " pair", c("rcp.c") + ", " + c("render_node.c") + ", " + c("vadirect.c")],
        ["function", "prefix = the module: " + c("rcp_") + ", " + c("wt_") + ", " + c("rootside_") + ", " + c("capture_") + ", "
         + c("session_") + ", " + c("transport_") + ", " + c("input_") + ", " + c("kwin_") + ", " + c("child_") + ", " + c("clipboard_") + ", " + c("budget_"),
         c("rcp_video_codec_set") + ", " + c("child_video_capabilities")],
        ["macro and constant", "UPPER_SNAKE; protocol numbers carry the protocol's prefix", c("T_HELLO") + ", " + c("RCP_SESSION_CAP") + ", " + c("BUDGET_STRAIN_DELAY_MS")],
        ["type", "opaque types are a " + c("typedef struct x x") + " in the header; some enumerations are CamelCase", c("cidkey") + ", " + c("rcp_session") + ", " + c("DesktopSession")],
        ["header guard", c("REMOTIX_<NAME>_H") + " in 45 of the 53 headers that have an <code>#ifndef</code> guard; the other eight use the bare " + c("<NAME>_H") + " (" + c("ROOTSIDE_PROTO_H") + ", " + c("BUDGET_H") + "); "
         "of the 59 headers, five use " + c("#pragma once") + " and the generated shader header has no guard", c("REMOTIX_LOG_H") + ", " + c("REMOTIX_CID_H")],
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
        ["shell", "tabs for indentation; one status line per step in the server script; the build script tests each step itself", c("build/build-rpm.sh") + ", " + c("server/prepara-server.sh")],
        ["python (prove/)", "four spaces, a docstring that says what the check proves and how to run it, verdict lines", c("prove/check-base.py")],
    ], "«TAB» — Naming as observed") + \
    h4("Italian that remains in identifiers") + \
    p("The comments were translated; some names were not. They are real names in the source, and the manual quotes them in code. The counts are of this tree.") + \
    ul([
        c("registro_dice()") + " is the macro every module calls to write a log line (the string " + c("registro_dice(") + " occurs 1,264 times in " + c("src/*.c") + " and " + c("src/*.h") + ", the definition included, counted with " + c("grep -o") + " on 25 Nov 2026); the function behind it is " + c("log_says_in()") + ".",
        "In " + c("src/Makefile") + ": " + c("SORGENTI") + " (sources), " + c("OGGETTI") + " (objects), " + c("PROTOCOLLI") + " (protocols), " + c("GEMELLATI") + " (twinned files), "
        + c("MINIMI") + " (minimum versions), " + c("AVVERTIMENTI") + " (warnings), " + c("deps") + "'s variable " + c("stato") + ", and the generated " + c("GENERATI") + ".",
        "In " + c("rcp.c") + ": short variables such as " + c("lung") + " (length), and comments that name handlers " + c("tratta_*()") + " that no function of that name implements any more.",
        c("wt_chi") + " in the WebTransport module and " + c("codificatore_chiedi_chiave") + " in the encoder code.",
        "In the build and server scripts, output and folder names: " + sysf("controlli.txt") + " (the checks of the finished package), the VM " + c("costruzione") + " (build), " + sysf("pacchetti/") + " (packages), " + c("prepara-server.sh") + ". " + c("fanwatch.py") + " is English.",
        "The VM script " + c("server/vm-radeon.sh") + " and its commands, all Italian names quoted as they are: " + c("crea") + " create, " + c("accendi") + " switch on, " + c("spegni") + " switch off, "
        + c("ssh") + ", " + c("stato") + " state, " + c("prova-avvio") + " start-up test, " + c("schermo") + " screendump, " + c("tasti") + " keys, " + c("scrivi") + " type, " + c("istantanea") + " snapshot, " + c("ripristina") + " restore; also " + c("server/live-installa.sh") + " (installer for a live image), "
        + c("prove/giro-selinux.sh") + ", " + c("giro-xfce-radeon.sh") + " and " + c("giro-lxqt-radeon.sh") + " (<i>giro</i> = round); the bench variables " + c("RX_BANCO") + " (<i>banco</i> = bench), " + c("RX_TEMPO") + " (<i>tempo</i> = time factor), " + c("RX_KEEP") + " (read by " + c("hold.py") + ") and " + c("RX_BAN_ADDR")
        + "; the variables " + c("PACCHETTO") + " (package) and " + c("UTENTI") + " (users) of " + c("live-installa.sh") + "; the VM snapshots " + c("pulito") + " (clean), " + c("codec") + " and " + c("consegna-finale-<desktop>") + " (final delivery); the names of the test packages, a short word and a number ("
        + c("h1") + ", " + c("i2") + ", " + c("g6") + "); and the folders " + sysf("/media/REMOTIX-FEDORA/pacchetti") + " (packages), " + sysf("vm-radeon") + " and " + sysf("studio") + " on the dev server.",
        "In the document headings: " + c("docs/DECISIONS.md") + " opens as \"DECISIONI\" and " + c("docs/SPECS.md") + " as \"SPECIFICHE\"; " + c("DECISIONS.md") + " refers to " + sysf("LEZIONI.md")
        + " (the file is " + c("LESSONS.md") + " here).",
    ]) + \
    note("Do not rename an Italian identifier as a side effect of another change. A name is public if a log line, a message, an option or a file name carries it; "
         "those are recorded in the documents as they are.", "Renaming.")

# ── 21.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The comments are long on purpose. A block comment states <b>why</b> a thing is the way it is, with the date, the source and the failure it prevents. "
       "The code is short next to its comments (106,970 lines of C and headers in " + c("src/") + " plus a page of 14,326 lines, most of it in a few large files: "
       + c("child.c") + " 12,992 lines, " + c("rcp.c") + " 10,485, " + c("webtransport.c") + " 9,618, " + c("session.c") + " 8,842; counted with " + c("wc -l") + " in this tree on 25 Nov 2026).", lead=True) + \
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
        "<b>Measurements carry a date and a machine.</b> The " + c("[M]") + " marks of the Fedora work name where the figure was taken (for example the VM " + c("kde") + " or the real machine booted from the live stick); marks inherited from the Ubuntu tree name Ubuntu machines (for example " + c("rx-kde") + "); a mark without a machine is not a figure to quote.",
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
         c("log.h") + " opens with the rule; the ambiguity of two desktops installed is picked and declared; the dconf model says \"DECLARED FALLBACK, D-015\" when it goes back to the 1.0.0 behaviour, and the KWin stage says it too when KWin does not answer in time (F13)"],
        ["What changes what the user sees is born off (invariant I6).", "the bench function is off by default; the budget knob is off by default (" + rif("Quality, degradation and budget") + ")"],
        ["Do not degrade whoever is inside to let someone in (invariant I1: never detach).", "when the budget is full the new session is refused with a reason; the first user is not slowed"],
        ["The session survives the client (invariant I4).", "a closed browser, a killed browser or a cut line leave the desktop running (" + rif("Startup and life cycle") + ")"],
        ["One session per user, remote; a second device is refused (invariant I2).", "reason 0x0F, tested by " + c("check-multiuser.py")],
        ["Count the cases: separate outcomes get separate names.", c("RCP_VIDEO_SENT") + " and the seven other outcomes of " + c("rcp_video_send") + " are eight, not two, "
         "so that the caller can tell \"re-encode smaller\" from \"send a keyframe\""],
        ["Bound everything.", "a whole-run deadline in the checks; ceilings on frames, texts, rates; " + c("_Static_assert") + " (12 in the tree) ties limits that must agree, for example "
         "the usermod limit against the spawn wait in " + c("child.c")],
        ["A message that is not understood is reported, never silently ignored.", "the log line says WHAT was not understood (RCP §3.1), and a protocol error closes with reason 0x0B"],
        ["With SELinux on, an error in making the user's context REFUSES the login: nothing is left to run in the wrong domain.", "the child exits with 44 (no context like a local login's), 45 (the exec context could not be set), 46 (the next exec would not leave " + c("remotix_t") + ") or 47 (the session keyring could not be made), and the log says REFUSED (" + c("child.c") + "; F25, F31)"],
        ["A file of another package is adopted only if it is proven to be this transaction's: in doubt, touch nothing and say so.", "an " + c(".rpmnew") + " of sddm is adopted by " + c("remotix-pam-hook") + " only if its signature is the one the RPM database holds now and not the old one (F21); if the PAM block does not come back, the hook changes nothing and warns (F6)"],
        ["A line that must refuse is written so that a failure refuses.", c("onerr=fail") + " on the " + c("pam_listfile") + " line of " + c("remotix.pam") + ": if the list of denied users cannot be read, nobody enters"],
        ["Exit status carries meaning.", "the service stops its restart loop on 78, which is reserved for a real configuration error (" + c("RestartPreventExitStatus=78") + " in " + c("rpm/remotix.service") + ")"],
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
        "<b>Say what, not \"error\".</b> A line names the thing that was not understood or that failed and, where there is one, the reason code. Two lines of this tree show it: the "
        "verdict that names the missing " + c("labwc") + " package in " + c("delivery_verdict()") + ", and the line that " + c("close_why()") + " in " + c("transport.c") + " writes for every closed connection: who closed it (the peer, we, or nobody), the type and code of the error, the TLS alert with its name (for example 46 certificate_unknown), and whether the handshake had completed (F23, F31).",
    ])

# ── 21.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The tree has a few fixed places and a few habits that follow from where a thing runs.", lead=True) + \
    table(["Folder", "Holds", "Note"], [
        [c("src/"), "the product: C sources and headers, " + c("Makefile") + ", " + c("page.html") + ", the PAM file, the polkit rules and helper, " + c("remotix-pam-hook") + ", " + c("protocols/") + " (XML, among them the two KDE output protocols), "
         + c("opus-wasm/") + " (the audio decoder module)", "built by the spec in the build VM"],
        [c("rpm/"), "packaging: " + c("remotix.spec") + ", the unit, tmpfiles, sysusers, defaults, the firewalld service, denied users, the needrestart and no-suspend drop-ins, the KWin permission file", "see " + rif("The package")],
        [c("selinux/"), "the policy module: " + c("remotix.te") + ", " + c("remotix.fc") + ", " + c("remotix.if"), "built by the spec with the SELinux devel makefile"],
        [c("build/"), "the build script " + c("build-rpm.sh") + " and the static QUIC libraries script " + c("quic-static.sh"), "see " + rif("Build and release")],
        [c("prove/"), "the checks and their libraries; " + c("prove/banco-vm/") + " holds the four scripts of the VM bench", "run on the dev server"],
        [c("server/"), "dev server set-up (" + c("prepara-server.sh") + "), the VM bench script " + c("vm-radeon.sh") + " and " + c("live-installa.sh") + " for a live image", "paths under " + sysf("/media/REMOTIX-FEDORA")],
        [c("studio/"), "the studies of the four desktops on Fedora 45 (1 to 4), the KDE project (5) and " + c("manuali/") + " (the work lists of the manuals): Markdown, in Italian; not in the file map of this manual", "history of the port; not copied into this manual"],
        [c("docs/"), "specification, protocol, decisions, lessons, the register of problems and the inherited inventories (Ubuntu and Debian history)", "the common reference; not copied into this manual"],
        [c("manuals/"), "this manual and the user manual, generated from " + c("manuals/sources/"), "regenerated by " + c("manuals/sources/build.py") + ", checked with " + c("--check")],
        [c("LICENSE.md") + ", " + c("THIRD-PARTY-LICENSES") + ", " + c("licenses/"), "the two files ship in the package; " + c("licenses/") + " holds one page (" + c("how-it-works.html") + ") that the spec does not install", "see " + rif("The package")],
    ], "«TAB» — The layout of the tree") + \
    ul([
        "<b>Temporary files never go to " + c("/tmp") + " on the dev server:</b> its root file system is in RAM. " + c("build-rpm.sh") + " reads " + c("TMPDIR") + " (default " + c("/tmp") + ") for its stage folder; whether the work folder of the build VM obeys the rule was not verified.",
        "<b>Nothing is deleted, moved or overwritten without the owner asking.</b> This binds the scripts too: the build script copies the tree and never edits the working tree, and the header of " + c("server/vm-radeon.sh") + " lists the few files it removes or overwrites, all its own, and says that " + c("crea") + " refuses to touch an existing disk.",
        "<b>Scripts print one status line per step</b> (" + c("OK") + " or " + c("FAIL") + ") and keep going where the next step is independent; destructive operations are named in the header "
        "(" + c("check-ban.py") + " bans an address and always unblocks; " + c("hold.py") + " without " + c("RX_KEEP=1") + " closes all the sessions of the user it logs in).",
        "<b>Generated files are marked.</b> " + c("vulkanvideo_rgb_nv12_spv.h") + " says in its first line that it is generated and not to be edited by hand.",
        "<b>The manual checks itself against the tree.</b> " + c("python3 manuals/sources/build.py --check") + " verifies that every function, file and " + c("REMOTIX_*") + " variable cited in code form exists, "
        "and flags Italian sentences.",
    ])


# ── 21.7 ─────────────────────────────────────────────────────────────────────
S7 = p("A few conventions are shared with the Ubuntu tree and a few are new on Fedora. Each comes from a failure of the work.", lead=True) + \
    table(["Convention", "Where it is visible", "Why"], [
        ["A check that cannot decide says so with its own verdict, never with a pass: <b>SKIP</b> (it cannot be done on this bench) and <b>NOTE</b> (a fact, not a verdict). A round in which nothing passed ends with "
         "\"NO CHECK PRODUCED A PASS\", and a round run with " + c("--only") + " says \"PARTIAL RUN\" and exits with 3.",
         c("prove/all.sh") + ", the lines " + c("prelocal/real-greeter") + ", " + c("ban/other-addresses") + " and " + c("package") + " of the VM bench", "a green that hides what was left out is the failure that register B3 describes"],
        ["The question \"is the desktop alive\" has three answers: " + c("SESSION_LIFE_ALIVE") + ", " + c("SESSION_LIFE_DEAD") + " and " + c("SESSION_LIFE_UNKNOWN") + ". Whoever acts on \"dead\" must use "
         + c("session_life()") + "; \"I could not look\" is not \"closed\".", c("src/session.h") + ", " + c("src/session.c") + ", " + c("src/child.c"),
         "register C5 and E3: two places that still read a failed look as \"closed\" are listed in " + rif("Fedora: open points")],
        ["Every SELinux right is written one by one in the " + c(".te") + " with its reason, and verified in enforcing with the policy as it is, never in permissive mode and never with " + c("semodule -DB") + ". The wall is tried by a negative test: the domain " + c("remotix_net_t") + ", run as root with all capabilities, must be refused each forbidden action, and each refusal must leave an AVC line.",
         c("selinux/remotix.te") + ", " + c("prove/wall-selinux.sh") + ", " + c("prove/wall-neg-domain.py"), "F27, F28: a search in permissive mode with the dontaudit rules off loses lines; a refusal by the Unix permissions leaves no AVC and would prove nothing (F24)"],
        ["A declared fallback is a log line that names the decision (for example D-015, or the KWin fallback of F13) and the date, so that a fallback can be told from an accident.", c("src/session.c") + ", " + c("src/kwin.c"),
         "the dconf model and the KWin stage keep a behaviour as a fallback and say so"],
        ["A problem raised by a reviewer in the code carries a letter or a tag in the comment next to the date: on Fedora the findings of the review are lettered (K, L, M, N, O in F34 and F35; N5 is inherited from the Ubuntu work).", c("src/child.c") + ", " + c("src/input.c") + ", " + c("src/session.c"), "so that a later reader can find the finding in the register"],
        ["The bench has a name for each kind of machine (" + c("RX_BANCO=vm") + " for the virtual machines) and a factor for the slower ones (" + c("RX_TEMPO") + ", an integer, never zero and never a free text).",
         c("prove/all.sh") + ", " + c("prove/lib.py"), "a slower bench must not turn a deadline into \"no deadline\" by a wrong value"],
        ["The name of a test package is a short word and a number (" + c("h1") + ", " + c("i2") + "); its files are kept in " + sysf("/media/REMOTIX-FEDORA/pacchetti/<name>/") + " and the logs of a round in a folder of the dev server.", c("server/") + ", " + c("PIANO.md"),
         "so that a round can be told from another; the logs are kept outside the tree"],
        ["<b>One behaviour for every distribution.</b> The remote session is the local login minus the harms of a shared server; a difference of Fedora is listed and carried to the others, not left as a private fix, and a cure born on Fedora that is good for all is not applied to the other trees without a plan.", c("PIANO.md") + " (22 and 23 Nov 2026), " + sysf("PIANO-1.0.2-debian-ubuntu.md"), "the owner's rule of uniform behaviour"],
        ["<b>A problem closed or postponed gets a register entry</b>, and an entry that adds a rule for a new distribution ends with a line \"on a new distribution\" (F36: try the local login ALWAYS with programs open in the remote desktop).", c("docs/REGISTRO-problemi.md"), c("CLAUDE.md") + " of this tree"],
    ], "«TAB» — Conventions of the Fedora tree")

CHAPTER = ("Conventions", [
    ("The written rules and what the tree does with them", S1),
    ("Names, language and the Italian that remains", S2),
    ("Comments, marks and references", S3),
    ("Errors, fallbacks and invariants", S4),
    ("Logging conventions for a writer of code", S5),
    ("The layout of the tree and the habits around it", S6),
    ("Conventions of the Fedora tree", S7),
])
