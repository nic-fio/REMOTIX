from build import arrow, box, c, code, fig, note, p, rif, steps, sysf, table, text, tip, warn, zone

# ── 13.1 The log module ─────────────────────────────────────────────
FUNCTIONS = table(["Function / macro", "Writes", "Used by"], [
    [c("registro_dice(area, fmt, …)") + " (the log says)", "An event line, always", "Every module; the parent for "
     "lines that belong to no tenant"],
    [c("log_detail(area, fmt, …)"), "A detail line, only when " + c("--verbose")
     + " (chatter) is on", "Transport, capture, input, clipboard, the child's frame loop: lines that are many and "
     "useful only while hunting a defect"],
    [c("log_says_of(area, who, fmt, …)"), "An event line that carries the identity of one tenant",
     "The parent, which serves all sessions at once: " + c("webtransport.c") + ", " + c("rcp.c") + " through "
     + c("hook_log()") + " (the logging hook), the parent's half of " + c("child.c") + " (the per-user "
     "child), and " + c("keyboard.c") + " (keyboard) when the parent opens a layout"],
    [c("log_detail_of(area, who, fmt, …)"), "The same, detail level", "The parent (" + c("webtransport.c")
     + ", " + c("keyboard.c") + ")"],
    [c("log_identity(who)"), "Nothing: sets the identity of the whole process", "The per-user child, right "
     "after reading its " + c("argv") + " (" + c("child_alive()") + ")"],
    [c("log_chatter(on)") + " / " + c("log_verbose()"), "Nothing: switches and reads the detail "
     "level", c("main.c") + " and " + c("child.c") + " (option " + c("--verbose") + ")"],
    [c("log_journal(on)") + " / " + c("log_to_journal()"), "Nothing: opens the journal socket",
     c("main.c") + " and " + c("child.c") + " (option " + c("--journal") + ")"],
    [c("log_speakable_key(code)"), "Nothing: says whether a key code may be written", c("input.c")
     + " before naming a key"],
    [c("log_now_ms()"), "Nothing: monotonic milliseconds", "RCP clocks, ban, tenant clocks"],
], "«TAB» — The interface of " + c("src/log.h"))

S1 = p("Every line the server writes goes through one module, " + c("src/log.c") + " (≈300 lines). There is no "
       "scattered " + c("printf") + ": the four writing functions are macros over four " + c("_in") + " functions "
       "that add " + c("__FILE__") + " and " + c("__LINE__") + ", and all of them end in a single static function, "
       + c("riga()") + " (line).", lead=True) + \
    p("The reason is written at the top of " + c("log.h") + ": a log spread over twenty " + c("fprintf(stderr, …)")
      + " has neither a timestamp nor an area, and those two are what make a line readable to whoever hunts a defect "
      "six hours later. The second reason is a security check: the review item B13.2 asks that the password appear "
      "in no log, and only a single funnel makes «it is not there» verifiable instead of a hope "
      "(" + rif("What never enters the log") + ").") + FUNCTIONS + \
    p("The log is the main diagnostic instrument of the project (" + c("LESSONS.md") + " §2.7): most defects of "
      "REMOTIX were found by reading it, and several design rules below exist because the log once lied under "
      "load — which is exactly when it is needed.") + \
    note("a few places do not use the module and write straight to " + c("stderr") + ": " + c("authentication.c")
         + " (PAM authentication; it is also compiled into a test host, " + c("benches/01-b3-graft-rcp.py")
         + ", which has no " + c("log") + "), the child between " + c("fork") + " and " + c("exec") + " ("
         + c("become_and_exec()") + ", lines prefixed " + c("child:") + "), the usage text of "
         + c("help()") + ", the refusals of the command line in " + c("main()") + " (an unknown option, a "
         "missing " + c("--name") + ", a wrong " + c("--encoding-route") + "), and the KDE start-line helper "
         + c("remotix --kwin-nested") + " (" + c("kwin_nested_alive()") + ", lines prefixed "
         + c("remotix --kwin-nested:") + "), which runs as the user inside KWin's unit and writes to that "
         "unit's output, that is to the user's journal. These lines have no timestamp and never "
         "reach the journal through " + c("--journal") + ".", "Outside the funnel.")

# ── 13.2 Anatomy of a log line ───────────────────────────────────────────
S2 = p("A line is " + c("HH:MM:SS.mmm area [identity] body") + ": local wall-clock time with milliseconds, the area "
       "left-aligned in seven columns, the identity in brackets only when there is one, then the body.", lead=True) + \
    code("08:41:07.312 startup   ⭐ ready: https://server.lan:7447  —  the WebTransport session lives on /rcp/1 (RCP.md §2.2)\n"
         "08:41:19.884 rcp     [anna] PAM answered (request 3): admitted  ⭐ and the thread never stopped (DECISIONS.md §1.10)\n"
         "08:41:21.040 child  [anna] ⭐ FIRST CONNECTION: «anna» is not in the card's groups (render,video) and I am PUTTING it there, now …",
         "text", "Three log lines as the server writes them (binaries built before the English migration write "
         "the same lines in Italian)") + \
    table(["Rule", "Value", "Why"], [
        ["One " + c("write(2)") + " per line", "Header, body and newline in one buffer of 4096 bytes",
         "Until 21 Aug 2026 a line was three writes on an unbuffered " + c("stderr") + ". Parent and child append to "
         "the same file, and interleaved writes produced lines without a timestamp: measured on a real 3.0 MB log "
         "(28,035 lines), 23 orphan lines, 3 of the 80 «canvas requested» lines a tool counted (3.8 %). The tool "
         "died with " + c("ValueError") + "; worse, a count that silently loses 3.8 % still looks plausible."],
        ["Buffer of " + c("PIPE_BUF"), "4096 bytes", "Below " + c("PIPE_BUF") + " a single append write is atomic "
         "with respect to other processes. " + c("write(2)") + " is also async-signal-safe, which " + c("fprintf")
         + " is not, and has no buffer to flush."],
        ["Truncation is declared", "A body that does not fit ends with " + c("...") + " before the newline",
         "A cut line is visible; an interleaved line is not."],
        ["Identity at the head of the body", c("[name] ") + " after the area, never between time and area",
         "Readers split a line into time · area · body; a new field in the middle would shift the area. At the head "
         "of the body old readers keep working and new ones can strip it."],
        ["Identity sanitised", "Only " + c("0-9 A-Z a-z . _ - @ :") + "; anything else becomes " + c("_")
         + "; at most " + c("LOG_IDENTITY_MAX") + " = 48 characters",
         "A " + c("]") + " or a newline inside a name would split the line into two plausible and false lines — the "
         "defect the single-write rule had just removed."],
        ["No identity, no brackets", "The line goes out without " + c("[]"),
         "Not knowing is an outcome. A guessing classifier was wrong 96.4 % of the time, an abstaining one 0 % "
         "(" + rif("Whose line it is") + ")."],
        ["Write errors are ignored", c("(void)scritti"), "There is no place to report that the log cannot be "
         "written: the only channel would be the broken one."],
    ], "«TAB» — How " + c("riga()") + " builds and writes a line") + \
    p("The body follows a convention used across the whole code: a body that <b>starts</b> with " + c("⛔")
      + " is a fault, with " + c("⚠") + " a declared fallback or a warning, " + c("⭐") + " marks a notable fact "
      "(a decision in force, a cure that fired). Only the mark at the head of the body counts: many normal lines "
      "quote a " + c("⛔") + " in the middle, and the journal output reads only the head "
      "(" + rif("The systemd journal output") + ").") + \
    p("The time is " + c("CLOCK_REALTIME") + " in local time for the human reader; every interval the code measures "
      "uses " + c("log_now_ms()") + ", which is " + c("CLOCK_MONOTONIC") + ". The two are never mixed: the ban "
      "file, which must survive a restart, converts monotonic deadlines to epoch seconds when it is written "
      "(" + c("save_ban()") + " in " + c("rcp.c") + ").")

# ── 13.3 Log areas ───────────────────────────────────────────────────────
S3 = p("The area is the second column of every line and the " + c("REMOTIX_AREA") + " field in the journal. It exists "
       "to read the log by column when transport, protocol and session speak at the same time.", lead=True) + \
    table(["Area", "Constant", "Defined in", "Who writes it"], [
        [c("startup"), c("LOG_STARTUP"), c("log.h"), "Startup and shutdown of the parent (" + c("main.c")
         + ")"],
        [c("quic"), c("REG_QUIC"), c("log.h"), "QUIC and TLS: " + c("transport.c") + ", " + c("tls.c")],
        [c("wt"), c("REG_WT"), c("log.h"), "HTTP/3 and WebTransport, the parent's half of every session ("
         + c("webtransport.c") + ")"],
        [c("rcp"), c("REG_RCP"), c("log.h"), "The RCP state machine (through " + c("hook_log()")
         + "), the parent's side of the PAM helper (" + c("helper.c") + "), the unlock socket (" + c("command.c")
         + ")"],
        [c("page"), c("LOG_PAGE"), c("log.h"), "The TCP page server (" + c("page.c") + "): one summary line at most every 10 s for what it refused, evicted or closed"],
        [c("cert"), c("REG_CERT"), c("log.h"), "Certificate generation and rotation (" + c("certificates.c") + ")"],
        [c("session"), c("LOG_SESSION"), c("log.h"), "Birth and care of the desktop session ("
         + c("session.c") + "), the local-session guardian (" + c("sentinel.c") + " and its lines in " + c("main.c")
         + ")"],
        [c("video"), c("REG_VIDEO") + ", " + c("LOG_ENCODING"), c("log.h") + "; " + c("encoder.c") + ", "
         + c("vadirect.c") + ", " + c("vulkanvideo.c"), "Video encoding (" + c("LOG_ENCODING") + " is a local alias "
         "with the same text)"],
        [c("budget"), c("REG_BUDGET"), c("log.h"), "The composition budget: the value in force, the verdict on "
         "who knocks, the refusal (" + c("budget.c") + "). It has its own area so that «why was that user refused» "
         "is one column, not a sieve over " + c("wt") + " and " + c("child") + "."],
        [c("child"), c("LOG_CHILD"), c("child.h"), "The per-user child, and the parent's side of the child table "
         "(" + c("child.c") + ")"],
        [c("audio"), c("REG_AUDIO"), c("audio.c"), "The Opus encoder"],
        [c("sound"), c("LOG_SOUND"), c("sound.c"), "The PipeWire sink of the session"],
        [c("clipboard"), c("LOG_CLIPBOARD"), c("clipboard.h"), "Clipboard (" + c("clipboard.c") + ", " + c("clipboard_kde.c")
         + ")"],
        [c("keyboard"), c("LOG_KEYBOARD"), c("keyboard.c"), "Keyboard layouts and keymaps"],
        [c("capture"), c("AREA"), c("capture.c") + ", " + c("mutter.c") + ", " + c("kwin.c") + ", " + c("wlroots.c"),
         "Screen capture on every compositor; on KDE also the resize of KWin's labwc at a reattach"],
        [c("input"), c("AREA"), c("input.c") + ", " + c("wlr_input.c"), "Pointer and keyboard injection"],
        [c("cursor"), c("AREA"), c("cursor.c"), "The cursor shape sent to the page"],
        [c("shape"), c("AREA"), c("shape.c"), "The colour-coded cursor theme REMOTIX writes for the "
         "session and the dictionary that maps each colour back to a real cursor image"],
    ], "«TAB» — The areas, as of commit " + c("d0181ae")) + \
    note("the area is padded to seven characters (" + c("%-7s") + "); " + c("session") + " and " + c("keyboard")
         + " are longer and simply push the body one or two columns to the right. Tools that parse the log split on "
         "whitespace, not on column positions.")

# ── 13.4 Whose line it is ────────────────────────────────────────────────
S4 = p("With ten tenants on one machine a line that does not say whose it is sends the reader to look at somebody "
       "else's desktop. The identity in brackets is the user name, and it reaches the line by two roads because the "
       "processes are of two kinds.", lead=True) + \
    table(["Process", "How the identity arrives", "Effect"], [
        ["The per-user child: serves <b>one</b> session", c("log_identity(utente)") + " as the very first thing "
         "in " + c("child_alive()") + ", from " + c("argv[2]"), "Every line of that process carries the name — "
         "including lines of " + c("encoder.c") + " and " + c("audio.c") + ", which know nothing about "
         "sessions. It comes before the uid re-check, so even «I am not who I should be» is attributed."],
        ["The parent: serves <b>all</b> sessions", "Per line: " + c("log_says_of(area, utente, …)"),
         "A process-wide identity would always say the same thing, i.e. nothing. The per-line name wins over the "
         "process one; with neither, the line has no brackets."],
    ], "«TAB» — Two kinds of process, two roads for the identity") + \
    p("The measurement that led here (review item R10-A4, 25 Aug 2026, " + c("phases/10-multi-tenant-and-the-budget.md")
      + " §6.7): with four real GNOME sessions (57,121 lines in 90 s of steady state) only 4.2 % of the diagnostic "
      "lines said who was speaking, and the three largest families (" + c("fotogramma-spedito") + ", "
      + c("ciclo-cattura") + ", " + c("audio-blocchi") + ": frame sent, capture cycle, audio blocks) 0.0 %. With one scene in four switched off, the log "
      "showed that a series had stopped but named the session 0 times in 4, and a reader guessing the name was "
      "wrong 96 times in 100.") + \
    p("The identity is composed in one place only, " + c("riga()") + ": callers pass the bare name, never a "
      "ready-made " + c("[name]") + ", because two places writing the bracket would write it differently. It is a "
      "<b>copy</b> in a static buffer, not a pointer, since callers often pass an " + c("argv") + " element; and it "
      "does not cross " + c("exec") + ", which is why the child sets it again from its own command line.") + \
    warn("lines of " + c("rcp") + " in the parent carry the user name the client <b>claimed</b> in "
         + c("CREDENTIALS") + " (" + c("rcp_user()") + "), also before PAM has answered. A line of a refused attempt "
         "therefore names a user who may not exist; read the outcome line, not the bracket, to know who got in.",
         "A claimed name is not an authenticated name.")

# ── 13.5 Where the lines go ──────────────────────────────────────────────
DOVE = fig(
    zone(20, 12, 300, 250, "Processes")
    + box(40, 44, 260, 46, "Server parent (root)", "log module: stderr + journal", "navy")
    + box(40, 104, 260, 46, "PAM helper and grandchildren", "stderr only", "dark")
    + box(40, 164, 260, 46, "Per-user child", "log module: same stderr + journal", "blue")
    + box(40, 224 - 2, 260, 34, "Desktop programs", "", "light", 12)
    + zone(360, 12, 520, 250, "Destinations")
    + box(390, 44, 220, 46, "Unit output stream", "packaged service", "dark")
    + box(640, 44, 220, 46, "registro.log", "bench launch scripts", "grey")
    + box(390, 134, 470, 46, "systemd journal, native fields", "only with --journal; events, not detail", "blue")
    + box(390, 210, 470, 46, "session.log in the user's home", "XDG state dir; fallback XDG_RUNTIME_DIR", "light")
    + arrow(300, 60, 388, 60) + arrow(300, 127, 388, 72, "#475569")
    + arrow(300, 180, 388, 80, "#475569")
    + arrow(300, 76, 388, 150, "#0050C0", True) + arrow(300, 190, 388, 160, "#0050C0", True)
    + arrow(300, 239, 388, 233, "#3b82f6")
    + text(640, 112, "or, under the bench scripts, appended to a file", 11),
    900, 270, "«FIG» — Where each process writes: solid arrows are stderr, dashed arrows the native journal protocol")

S5 = p("The log has no file of its own: the server writes to its standard error, and whoever starts it decides where "
       "that goes. The child inherits descriptors 0, 1 and 2 across " + c("exec") + " on purpose, so parent and "
       "child lines land in the same stream and can be read in order.", lead=True) + DOVE + \
    table(["Stream", "Where it ends up", "Notes"], [
        ["Parent and child " + c("stderr"), "Packaged unit: the unit's output stream, i.e. the journal under "
         + c("remotix.service") + ". Bench scripts (" + c("src/restart-7700.sh") + ", " + c("src/restart-7900.sh")
         + "): " + c("systemd-run") + " with " + c("StandardError=append:…/registro.log"),
         "The file of the benches is what every measurement tool reads; the product never opens it itself."],
        ["Native journal datagrams", c("/run/systemd/journal/socket"), "Only with " + c("--journal") + "; see "
         + rif("The systemd journal output") + "."],
        ["PAM grandchild " + c("stderr"), "Same stream as the parent", "Lines start with " + c("RCP:")
         + " (" + c("authentication.c") + "); no timestamp, no journal fields."],
        ["Desktop session output", c("$XDG_STATE_HOME/remotix/session.log") + " (normally "
         + c("~/.local/state/remotix/session.log") + "), appended by the shell that starts the session",
         "Owned by the user. Fallback, declared in the log: " + c("$XDG_RUNTIME_DIR/remotix-session.log")
         + ", which dies with the session; with neither, the session starts without a log and the line says so. "
         "Uninstalling removes it from every home."],
    ], "«TAB» — The streams and their destinations") + \
    p("The session log used to be " + c("/tmp/remotix-sessione-<uid>.log") + ": a predictable name in a shared "
      "directory. Another user could create it first, and with " + c("fs.protected_regular") + " (on by default on "
      "Debian, Fedora and Arch) the shell's " + c("exec >>") + " on a foreign file failed and the desktop did not "
      "start; if the name was a symlink, REMOTIX wrote where it pointed. Since phase 17, "
      + c("log_session_path()") + " (the session log path, in " + c("session.c") + ") creates the "
      "directory with mode 0700 and checks that it is a real directory owned by the user and not writable by group "
      "or others, and opens the file with " + c("O_NOFOLLOW") + " at 0600, verifying it is a regular file owned by "
      "the user.")

# ── 13.6 The systemd journal output ──────────────────────────────────────
S6 = p("With " + c("--journal") + " every event line also goes to the systemd journal, with fields that can be "
       "filtered (" + c("DECISIONS.md") + " §9.1, phase 16 §12, commit " + c("62753e7") + "). The line on "
       + c("stderr") + " does not change and is not switched off: the journal is added, never substituted.",
       lead=True) + \
    table(["Field", "Content", "Query"], [
        [c("MESSAGE"), "The line without the time (the journal stamps its own); sent in the binary form "
         "(name, newline, 64-bit little-endian length, bytes), the only one that survives a newline inside the value",
         ""],
        [c("PRIORITY"), c("3") + " if the body starts with " + c("⛔") + ", " + c("4") + " with " + c("⚠") + ", "
         + c("6") + " otherwise", c("journalctl -t remotix -p warning")],
        [c("SYSLOG_IDENTIFIER"), c("remotix"), c("journalctl -t remotix")],
        [c("REMOTIX_AREA"), "The area (" + rif("Log areas") + ")", c("journalctl -t remotix REMOTIX_AREA=rcp")],
        [c("REMOTIX_TENANT"), "The sanitised identity (" + c("tenant") + " = tenant); the field is absent when "
         "the line has none",
         c("journalctl -t remotix REMOTIX_TENANT=anna")],
        [c("CODE_FILE") + ", " + c("CODE_LINE"), "Source file and line of the call, from the macros", ""],
    ], "«TAB» — The journal fields") + \
    table(["Choice", "Why"], [
        ["Native protocol, no " + c("libsystemd"), "One datagram " + c("KEY=value") + " per line on "
         + c("/run/systemd/journal/socket") + " (" + c("al_journal()") + "): no new dependency."],
        [c("SOCK_NONBLOCK") + " and " + c("MSG_DONTWAIT") + ", errors ignored", "A clogged, stopped or absent "
         "journal (a container) must not cost a single line nor stop the loop that serves the screens: "
         + c("stderr") + " has the line anyway."],
        [c("sendmsg") + " with the address every time, never " + c("connect"), "A connected datagram socket stays "
         "dead forever if journald restarts; an unconnected one finds the new journald at the next datagram."],
        ["Socket opened once, at switch-on", c("riga()") + " runs in several threads; two threads opening it "
         "together would leak a descriptor."],
        [c("REMOTIX_PAM_LOG_TAG"), "Set by the PAM helper in the environment of the process that checks one login (never read from the server's own environment): the six-hex tag of the name, the same one " + c("log_user()") + " writes, so that the line of the PAM check names nobody and still matches the server's lines."],
        [c("SOCK_CLOEXEC"), "The child is an " + c("execve") + " and opens its own; it learns about the journal from "
         "its command line (" + c("--journal") + ", like " + c("--verbose") + ")."],
        ["Detail lines are not sent", "With 16 sessions they are tens of thousands per minute; the journal's rate "
         "limit would throttle them, dropping exactly the events, and its work would end up inside the load "
         "measurements. The journal keeps events; detail stays in the stream."],
        ["Severity only from the head of the body", "Many normal lines quote " + c("⛔") + " in the middle "
         "(«ban: … ⛔ …»)."],
    ], "«TAB» — Design choices of the journal output") + \
    p("The child, after " + c("pam_open_session") + ", lives in the scope of the user's logind session, not in the "
      "server unit. Its lines are therefore not found by " + c("journalctl -u remotix") + ": the right query is by "
      "identifier.") + \
    code("journalctl -t remotix -f                         # everything, parent and children\n"
         "journalctl -t remotix -p warning --since today   # faults and fallbacks only\n"
         "journalctl -t remotix REMOTIX_TENANT=anna     # one tenant\n"
         "journalctl -t remotix REMOTIX_AREA=budget        # why somebody was refused\n"
         "journalctl -t remotix -o verbose -n 1            # see every field of the last line",
         "bash", "Reading the journal") + \
    p("At startup the parent declares the outcome: either " + c("log also in the systemd journal (--journal): …")
      + ", or " + c("⚠ --journal requested but the socket does not open (<errno>): the "
      "log stays ONLY here") + ". "
      "The journal is switched on before the first line, so the first line goes there too.") + \
    warn("all three packaged units start the server under systemd, whose default sends the unit's "
         + c("stderr") + " to the journal as well. With " + c("--journal") + " every event line of the parent is "
         "therefore in the journal <b>twice</b>: once from the output stream (no fields) and once native (with "
         "fields). Noted as open in " + c("phases/17-the-installer.md") + " (§13.1, the items left undone by task T3, "
         "point 3): the program should "
         "stay quiet on " + c("stderr") + " when " + c("JOURNAL_STREAM") + " is its " + c("stderr") + ". Not settled "
         "yet.", "Every line twice.") + \
    note("the help text of " + c("main.c") + " and the box in " + c("log.h") + " still say «7 for the "
         "detail lines». The code never sends detail lines to the journal, so priority 7 never occurs.",
         "Priority 7.")

# ── 13.7 What never enters the log ───────────────────────────────────────
S7 = p("Three things never enter any log at any level: passwords, what the user types, and the content of the "
       "screen. The first is a protocol rule (" + c("RCP.md") + " §4.4), the second a decision of phase 16 (25–26 Sep "
       "2026, " + c("DECISIONS.md") + " §9.2), the third follows from the first two: the only images the server writes are "
       "those of " + c("--survey") + ", a bench option.", lead=True) + \
    table(["What", "Rule in the code", "Where"], [
        ["The password", "Never formatted into a line — not even its exact length, removed from the arrival line "
         "because the log is a file that is kept (R9.8); the local copy is zeroed as soon as PAM answers; the copies "
         "in the receive buffer are zeroed when consumed (" + c("drain()") + ") and when the session is freed "
         "(" + c("rcp_free()") + "); the two copies in the PAM helper's socket buffers are zeroed after use",
         c("rcp.c") + ", " + c("helper.c")],
        ["The PAM conversation copy", "Duplicated with " + c("strdup") + " for libpam, which owns and frees it. "
         "Linux-PAM overwrites it in " + c("_pam_drop_reply()") + " before " + c("free()") + " (measured 10 Aug "
         "2026). A port to another PAM library must re-check this line.", c("authentication.c") + ", "
         + c("conversation()")],
        ["Typed characters", "Written as «a character», «key pressed/released»; never " + c("U+XXXX")
         + " nor the character; a character that cannot be produced is declared as an event, not which one",
         c("rcp.c") + ", " + c("keyboard.c") + ", " + c("input.c")],
        ["Key codes", "Only modifiers keep their evdev code: Ctrl 29/97, Shift 42/54, Alt 56/100, CapsLock 58, "
         "Meta 125/126 — they say nothing about the text and are exactly the keys that get stuck and need naming "
         "(" + c("RCP.md") + " §11). Mouse buttons keep their code too.",
         c("log_speakable_key()") + "; its twin " + c("speakable_key()") + " in " + c("rcp.c")],
        ["Text from the client in the page server", "The request line quoted in the log («GET … from») is reduced to printable ASCII, cut at 200 bytes with its length said, and the log itself turns every control byte (and DEL, the C1 controls, the bidi marks, the Unicode line separators) into a «?», so a target with a newline cannot forge a second line", c("page.c") + ", " + c("log.c")],
        ["Session identities", "Sanitised to user-name characters", c("riga()")],
    ], "«TAB» — The exclusions and where they are enforced") + \
    p("A sequence of evdev codes " + c("30, 48, 46") + " is a word: a key code <b>is</b> a character up to the "
      "layout. That is why the list of speakable keys is the only question a caller must ask before writing a code, "
      "and why its answer lives in one place. " + c("rcp.c") + " carries its own copy because it is also compiled "
      "without the server's log (" + c("benches/rcp/") + ").") + \
    warn("the zeroing of the local copy in " + c("rcp.c") + " is a plain " + c("memset") + ", which an optimising "
         "compiler may remove because the buffer is not read afterwards. The known cure is " + c("explicit_bzero()")
         + "; the code asks to inspect the assembly of the running binary first (suspicion R9.20). Not settled yet.",
         "An open question on the password.")

# ── 13.8 The startup declarations ────────────────────────────────────────
S8 = p("At startup the parent writes the value <b>in force</b> of every mechanism that changes what users see or "
       "that can close a session — switched on <b>and</b> switched off. A threshold that is off and a threshold that "
       "never fired produce the same log; a thirty-minute clock is never verified by waiting thirty minutes. The "
       "line is the verification (failure form E1, «written is not in force»).", lead=True) + \
    table(["Order", "Line (area)", "Written by"], [
        ["1", "Product banner; journal on, or why not (" + c("startup") + ")", c("main.c")],
        ["2", "Encoding probe in a separate process, then the codecs offered in " + c("HERE_I_AM") + " (the server's "
         "welcome message) — or " + c("⛔⛔ THIS SERVER CANNOT ENCODE VIDEO") + " with the reason (" + c("startup") + ")", c("child_video_capabilities()")],
        ["3", "The desktop of this machine (" + c("startup") + ")", c("session_desktop_explain()") + " (explains the "
         "desktop)"],
        ["4", "On KDE only: the KWin capture permission is there, or the code and the remedy (" + c("startup") + ")",
         c("kwin_check_permission()")],
        ["5", "The three clocks of " + c("RCP.md") + " §5.3: client silence 30 s (fixed), user inactivity, session "
         "abandonment",
         c("main.c")],
        ["6", "Ghost eviction: threshold and ON, or 0 and OFF «by hand»", c("main.c")],
        ["7", "Test tone, only when on", c("wt_audio_test()")],
        ["8", "Administrative session cap, and whether it was moved by hand", c("main.c")],
        ["9", "Composition budget and reserve (" + c("budget") + ")", c("budget_startup_line()")],
        ["10", "Video queue threshold (" + c("wt") + ")", c("wt_clear_threshold()")],
        ["11", "Frame-rhythm regulator — read after the threshold, because with the threshold off it can never "
         "fire and the line says so", c("wt_adaptive_rate()")],
        ["12", "Dead line: on/off, stall and silence values", c("wt_dead_line()")],
        ["13", "Ban file and number of addresses loaded; refusal to start if unreadable", c("main.c")],
        ["14", "PAM helper started with its pid, or missing: synchronous fallback declared", c("helper_turn_on()")
         + ", " + c("main.c")],
        ["15", "Child table switched on (cap, canvas size, path of the binary), or refused because the running binary "
         "was deleted or replaced (" + c("child") + ")", c("children_turn_on()")],
        ["16", "What the parent will pass to every child on its command line: quality climb, bandwidth floor, audio "
         "silence (" + c("child") + ")", c("children_phase9()")],
        ["17", "The effective uid and what it implies", c("main.c")],
        ["18", "Unlock socket opened, or why not", c("command_open()")],
        ["19", "PAM service file found, or " + c("⛔ the PAM service «remotix» DOES NOT EXIST"), c("look_pam_service()")],
        ["20", "Certificates: generated or reused, two fingerprints, session fingerprint (" + c("cert") + ")",
         c("certificates_prepare()")],
        ["21", "TLS contexts: QUIC (ALPN h3, TLS 1.3, 0-RTT off) and page", c("tls.c")],
        ["22", "Local-session guardian connected or not (" + c("session") + ")", c("main.c")],
        ["23", "Desktops found alive from a previous server (reattach pending)", c("found_again_at_startup()")],
        ["24", c("⭐ ready: https://<name>:<port>"), c("main.c")],
    ], "«TAB» — What the parent declares before serving, in order") + \
    p("While running, the parent adds one line per minute with the guardian's count (" + c("guardian: calls=… "
      "worst_ms=… tenants=… loop_gaps=… worst_gap_ms=…") + ": logind calls, worst call, tenants served, "
      "times the parent's loop fell behind, worst gap; constant " + c("GUARDIAN_COUNT_MS") + " = 60,000): a cumulative count, written once a minute instead of at every 2-second pass, which would be "
      "43,200 nearly identical lines a day. Every rotation of the session certificate is declared in " + c("cert")
      + ". At shutdown the parent writes how many QUIC connections were alive and whether the farewell "
      + c("0x0C SERVER_CLOSING") + " left on the wire within 4 s.")

# ── 13.9 Command-line options of the server ──────────────────────────────
OPT = table(["Option", "Default", "Lives in", "Meaning"], [
    "Network and files",
    [c("--address ADDR"), c("0.0.0.0"), "parent", "Address to listen on (UDP for QUIC, TCP for the page, same "
     "port)."],
    [c("--name NAME"), "the value of " + c("--address"), "parent", "Name or address written into the "
     "certificate's " + c("subjectAltName") + ". Mandatory when listening on " + c("0.0.0.0") + " or " + c("::")
     + ": a SAN that matches nothing gives a <i>different</i> browser warning, and some browsers offer no click "
     "to proceed. Exit 2 if missing."],
    [c("--port N"), c("7447"), "parent", "UDP and TCP port (" + c("RCP.md") + " §2.4)."],
    [c("--certificates DIR"), c("/var/lib/remotix/certificates"), "parent", "Directory of the two certificates, "
     "created 0700 if missing."],
    [c("--page FILE"), c("page.html") + " (relative)", "parent", "The page served over TCP."],
    [c("--ban-file FILE"), c("/var/lib/remotix/ban"), "parent", "Where the address "
     "ban survives restarts (format B2, no user name on disk)."],
    [c("--command-socket PATH"), "none", "parent", "Unix socket 0600 of the unlock command ("
     + rif("The unlock command socket") + "). Without it a ban ends only when its wait runs out (15 minutes, 1 hour or 12 hours)."],
    "Diagnostics",
    [c("--verbose"), "off", "parent and child", "Detail lines (" + c("log_detail") + "). Under it the key receipts of the input channel are logged in full (exact counts, and the slow keys one by one); without it the input log has one line per 10 s, only if something was slow and with no counts (a count after a password would be its length)."],
    [c("--journal"), "off (on in the packaged deb and rpm units)", "parent and child", "Events also to the journal "
     "(" + rif("The systemd journal output") + ")."],
    [c("--survey DIR"), "none", "parent and child", "Writes the captured frame (" + c("cattura.bgrx") + ") and the "
     "two encoded streams, for the pixel comparison of F2.6. Without it, not a byte more is written."],
    [c("--audio-test HZ"), "0 (off)", "parent", "Bench function: a test tone instead of the session's audio, "
     "declared in the log at every session."],
    [c("--encoding-route card|vulkan|vaapi"), c("card"), "parent and child", "Which card path encodes: "
     + c("card") + " chooses by capability (Vulkan Video if offered for the codec, else VA-API); the other two "
     "force a path for tests and diagnosis and fail saying so (no fallback). Any other value: exit 2."],
    "Clocks of RCP.md §5.3",
    [c("--inactivity-s N"), "1800 (30 min)", "parent", "User inactivity clock, in seconds so that the mechanism "
     "can be exercised in ten; 0 = off."],
    [c("--abandon-s N"), "3600 (60 min)", "parent", "Without input for that long, the graphical session is "
     "closed with the programs inside; 0 = off."],
    "Phase 9 (the five cures — queue threshold, rhythm regulator, dead line, ghost eviction, audio silence — are on "
    "since 24 Aug 2026, each with exactly one way to switch it off; quality climb and bandwidth floor stay off)",
    [c("--clear-threshold-ms N"), "100", "parent", "A stale delta in the video queue is dropped only if the queue "
     "does not drain within N ms; 0 = drop at every newer frame."],
    [c("--no-adaptive-rate"), "regulator on", "parent", "Switches off the frame-rhythm regulator."],
    [c("--no-dead-line"), "dead line on", "parent", "Switches off the dead-line closure."],
    [c("--dead-line-stall-ms N"), "5000", "parent", "Stall cause: ms without a frame going out while there is "
     "one to send; 0 = silence only."],
    [c("--dead-line-silence-s N"), "10", "parent", "Silence cause: s without a packet from the client; also "
     "turns on transport PINGs at half this value; 0 = stall only."],
    [c("--eviction-ms N"), "15000", "parent", "Ghost eviction: a seat held by a client silent for longer goes to a "
     "client of the <b>same</b> user who asks for it; 0 = off."],
    [c("--no-audio-silence"), "audio silence on", "parent and child", "Stops suppressing audio blocks that "
     "are all exactly zero."],
    [c("--quality-recovery"), "off", "child", "Quality climbs back one step after enough comfortable frames."],
    [c("--bandwidth-cap-mbit N"), "0 (off)", "child", "The bandwidth <b>floor</b> in Mbit/s from which wire, working "
     "point and reservoir derive; hardware only."],
    "Phase 10: capacity",
    [c("--budget-mpixel-s N"), "0 (off)", "parent", "Composition Mpixel/s this machine sustains. Off by default: "
     "the administrator declares a measured value; it never self-calibrates."],
    [c("--reserve F"), "0.5", "parent", "Share of a still tenant's worst case held in reserve (0 … 1)."],
    [c("--session-cap N"), "10", "parent", "Administrative cap on served users; refusals get " + c("0x0E")
     + ". Values below 1 are rejected with a line."],
    [c("--render-node /dev/dri/renderDN"), c("renderD128"), "parent → child", "The encoding card when the desktop does not say which card it draws on (the compositor's own answer, the " + c("linux-dmabuf") + " main device, is asked first and wins); also the card of the start-up test."],
    [c("--decoder-pace"), "off", "parent", "Declares the capability " + c("video.pace") + " (RCP.md §13): the page may then ask the server to encode fewer frames when its decoder falls behind. Off by default: nothing changes on the wire without it."],
    "Separate modes (first argument)",
    [c("--encoding-test [h264|hevc] [--node /dev/dri/renderDN] [--encoding-route …]") + " (encoding test; "
     + c("--node") + " = render node)", "—", "standalone", "Encodes one "
     "synthetic 256×256 frame on the card with the same choice as a real session and prints one JSON line. "
     "No network, no sessions, root not needed (the card groups are). Exit 0 card encodes · 1 card opens but no "
     "frame · 2 usage error · 3 no card can encode."],
    [c("--kwin-nested W H NODE -- <kwin_wayland_wrapper> …"), "—", "internal, KDE",
     "The start line of KWin on Plasma, written by REMOTIX into the drop-in of "
     + sysf("plasma-kwin_wayland.service") + ": starts a labwc without a screen at W×H and becomes KWin nested "
     "in it (" + rif("KDE Plasma sessions") + "). Runs as the user; opens nothing of the server. Never typed "
     "by hand. Exit 2 on a malformed line."],
    [c("--internal-child …"), "—", "internal", "The command line with which the binary re-executes itself as a "
     "per-user child. Never typed by hand; in " + c("ps") + " it marks a child, not a second server."],
], "«TAB» — Every option of " + c("src/main.c") + " (commit " + c("d0181ae") + ")")

S9 = p("The server is configured only by its command line. Every option is parsed in the single loop of "
       + c("main()") + "; an unknown option prints the usage text (" + c("help()") + ") and exits 2.", lead=True) + \
    OPT + \
    p("The column «lives in» matters because the child is an " + c("execve") + " with an environment built from "
      "scratch: a setting that the encoder or the audio encoder needs must be repeated on the child's command line, "
      "or it silently does not exist there. That cost a day on 16 Aug 2026: " + c("--verbose") + " was not "
      "passed, every detail line of the child vanished, and branches were believed «never taken» while they ran. "
      "The parent appends to the child's " + c("argv") + " only what differs from the default: " + c("--verbose")
      + ", " + c("--journal") + ", " + c("--quality-recovery") + ", " + c("--bandwidth-cap-mbit N") + ", "
      + c("--no-audio-silence") + " (negated, the same word the parent received) and " + c("--encoding-route X")
      + " when it is not " + c("card") + ".") + \
    code("remotix-child --internal-child <user> <uid> <gid> <width> <height> <serial> <rilievo-dir|-> [optional words]",
         "text", "The child's command line (written by become_and_exec(), read by child_alive())") + \
    table(["Removed switch", "What happens now", "Why it was removed"], [
        [c("-DAUDIO_SILENZIO_PREDEFINITO=1"), "Compile switch removed", "Replaced by " + c("--no-audio-silence")
         + " on the same binary: one road only."],
    ], "«TAB» — A switch that no longer exists") + \
    note("the options were renamed to English with no compatibility aliases (" + c("DECISIONS.md")
         + " §10.38): an old Italian name is an unknown option, usage and exit 2.", "Option names.")

# ── 13.10 Environment variables ──────────────────────────────────────────
S10 = p("REMOTIX reads almost nothing from the environment, on purpose: a cure that can be switched by an option and "
        "by a variable has two numbers that can diverge, and the child would not see the variable anyway. The "
        "complete list of names that start with " + c("REMOTIX_") + " in " + c("src/") + ", " + c("installer/")
        + " and " + c("packaging/") + ", leaving out the include guards of the headers (" + c("REMOTIX_*_H") + "):",
        lead=True) + \
    table(["Name", "Kind", "Read by", "Effect"], [
        [c("REMOTIX_PORT"), "Unit environment", c("remotix.service") + " (all three families)", "Expanded into "
         + c("--port") + ". Default 7447 in " + c("/usr/share/remotix/remotix.conf") + ". The installer writes " + c("REMOTIX_PORT=N") + " to " + c("/etc/remotix/remotix.conf.d/port.conf")
         + " only when the port is not 7447."],
        [c("REMOTIX_OPTIONS"), "Unit environment", c("remotix.service") + " (all three families)", "Extra options appended to the command line, "
         "e.g. " + c("--name 192.168.1.10") + " for users who connect by address (the last " + c("--name") + " wins). "
         "Empty by default."],
        [c("REMOTIX_VULKAN_CONVERSION"), "Process environment, bench only", c("vulkanvideo.c"),
         "Value " + c("copy") + " forces the copy path of the RGB→NV12 conversion even where the card accepts the shader "
         "writing the encoder input directly; used to measure it and to exercise the branch other cards take."],
        [c("REMOTIX_TEST_CHILD"), "Process environment, tests only", c("installer/engine/resume_test.go"),
         "Value " + c("1") + " makes the Go test binary act as the installer engine that the test kills with "
         "SIGKILL at every checkpoint and state transition, to prove resumption (R30)."],
        [c("REMOTIX_LABWC"), "Compile-time macro, not a variable", c("kwin.c"), "The exact path of the labwc "
         "that hosts KWin, set by " + c("make LABWC=…") + "; only the RHEL / Alma 10 package sets it ("
         + c("/usr/lib/remotix/labwc") + "). Without it, " + c("labwc") + " from " + c("PATH") + "."],
        [c("REMOTIX_SGOMBRA_SOGLIA_MS") + " (clearing threshold)", "Removed 23 Aug 2026", "nobody", "Temporary bridge for the video queue "
         "threshold, removed when " + c("--clear-threshold-ms") + " arrived."],
        [c("REMOTIX_AREA") + ", " + c("REMOTIX_TENANT"), "Journal fields, not variables", "—", "See "
         + rif("The systemd journal output") + "."],
        [c("REMOTIX_INPUT") + ", " + c("REMOTIX_POINTER") + ", " + c("REMOTIX_CLASSIC") + ", "
         + c("REMOTIX_SHORTCUTS"), "JavaScript globals of the page, not variables", c("page.html"),
         "The seams between the page's input, pointer, classic mode and shortcut modules."],
    ], "«TAB» — Every " + c("REMOTIX_*") + " name in the product") + \
    warn(c("REMOTIX_VULKAN_CONVERSION") + " is read with " + c("getenv") + " inside the encoder, but sessions encode "
         "in the per-user child, whose environment is composed from scratch by " + c("become_and_exec()") + " ("
         + c("HOME") + ", " + c("USER") + ", " + c("LOGNAME") + ", " + c("PATH") + ", an empty " + c("SHELL") + ", "
         + c("XDG_RUNTIME_DIR") + ", " + c("DBUS_SESSION_BUS_ADDRESS") + ", plus " + c("XDG_SESSION_ID") + " from "
         "PAM). The variable therefore reaches only the startup probe (a " + c("fork") + " of the parent) and "
         + c("remotix --encoding-test") + "; it never reaches a real session.", "It does not reach the sessions.") + \
    p("Other variables the code reads are the standard ones of the session it lives in: " + c("XDG_RUNTIME_DIR") + ", "
      + c("WAYLAND_DISPLAY") + ", " + c("DBUS_SESSION_BUS_ADDRESS") + ", " + c("XDG_CONFIG_DIRS") + ", "
      + c("XDG_DATA_DIRS") + ", " + c("XDG_STATE_HOME") + " (through GLib, for the session log), "
      + c("DCONF_PROFILE") + ", " + c("LANG") + ", " + c("PATH") + " and " + c("USER")
      + " (" + c("session.c") + ", " + c("kwin.c") + ", " + c("wlroots.c") + ", " + c("wlr_input.c") + ", "
      + c("child.c") + "). Variables used only by the test benches are documented with the benches.")

# ── 13.11 Diagnostic tools ───────────────────────────────────────────────
S11 = p("Besides the log, the product carries a few instruments for diagnosis. None of them is on in the packaged "
        "units except " + c("--journal") + ": bench options are kept off the shipped command line (review rule "
        "R13), and the build refuses to package a binary with the bench function compiled in ("
        + c("BENCH_ON") + " must be 0 in " + c("rcp.c") + ").", lead=True) + \
    table(["Instrument", "What it answers", "How"], [
        [c("--verbose"), "What the transport, capture and encoder are doing frame by frame",
         "Add to the command line (" + c("REMOTIX_OPTIONS") + " on deb/rpm). Detail lines never go to the journal."],
        [c("remotix --encoding-test"), "Can this card encode, by which path, which codecs?", "One JSON line: "
         + c('{"outcome":"hardware"|"nessuno","encoder":…,"strada":…,"nodo":…,"motivo":…,"codec":…,"offerti":…,'
             '"hevc":…,"h264":…,"hevc_strada":…,"h264_strada":…}')
         + " (outcome, encoder, card path, render node, reason, codec tried, codecs offered, and per codec the "
         "outcome and the path; several keys and the value " + c("nessuno") + ", none, are still Italian on "
         "this wire, which the installer reads). The installer runs it at the end of an installation."],
        [c("--survey DIR"), "Is the picture the page paints the picture that was captured?", "Writes the captured "
         "frame and the encoded streams for the pixel comparison benches."],
        [c("GET /fingerprint"), "Which session certificate is in force now?", "JSON "
         + c('{"algorithm":"sha-256","fingerprint":…,"hex":…,"rotations":N}') + " (algorithm, fingerprint, the "
         "same in hexadecimal, number of rotations)."],
        [c("PING") + " on the unlock socket", "Is the unlock command alive?", "Answers " + c("PONG")
         + " and writes a line; " + c("benches/01-b8-unblock.py") + " also prints which process answered "
         "(" + c("SO_PEERCRED") + " and " + c("/proc/<pid>/comm") + ")."],
        ["Child command line", "With which settings was this child born?", c("/proc/<pid>/cmdline")
         + " of " + c("remotix-child") + ": the optional words are there for whoever does not trust a log."],
        ["Guardian count", "Is logind slowing the loop?", "The per-minute " + c("guardian:") + " line."],
    ], "«TAB» — The instruments") + \
    steps([
        "Read the startup declarations (" + rif("The startup declarations") + "): most «it does not work» cases are "
        "already named there — no codec offered, no PAM service file, KWin permission missing, guardian not "
        "connected.",
        "Filter by tenant (" + c("REMOTIX_TENANT") + " or the bracket) and by area; read " + c("budget")
        + " for refusals, " + c("rcp") + " for the handshake, " + c("child") + " for the birth of the desktop.",
        "For a refused login, distinguish " + c("PAM REFUSED") + " (a real no) from "
        + c("⛔ PAM COULD NOT JUDGE") + " (a missing " + c("/etc/pam.d/remotix") + " or " + c("/etc/remotix/denied-users")
        + "): the client receives " + c("0x07") + " in both cases, the log does not.",
        "For a desktop that is born and shows nothing, look for the line of " + c("child") + " about the card groups (the groups that own the nodes in "
        + c("/dev/dri") + ")"
        + " and for " + c("session.log") + " in the user's home.",
        "On KDE, for a desktop that keeps its birth size at a reattach, look for "
        + c("⚠ §7.1 KDE: this Plasma session has no host for KWin") + " in " + c("child") + ", and for the "
        "start-line helper's lines in the user's journal ("
        + c("journalctl --user -u plasma-kwin_wayland") + ", as the user" + "): " + c("⛔ labwc is not installed")
        + " names the cause.",
        "Only then switch on " + c("--verbose") + ", for the shortest time that reproduces the defect.",
    ]) + \
    tip("a session that disappears always leaves a line with the numbers it was closed on: the dead line writes "
        + c("dead-line") + " with its stall or silence values, the clocks write the clock that expired, and the "
        "farewell code reaches the page. A disappearance without such a line is a defect of REMOTIX, by definition "
        "of invariant I1.", "No silent exits.")

CHAPTER = ("Logging and diagnostics", [
    ("The log module", S1),
    ("Anatomy of a log line", S2),
    ("Log areas", S3),
    ("Whose line it is", S4),
    ("Where the log lines go", S5),
    ("The systemd journal output", S6),
    ("What never enters the log", S7),
    ("The startup declarations", S8),
    ("Command-line options of the server", S9),
    ("Environment variables", S10),
    ("Diagnostic instruments", S11),
])
