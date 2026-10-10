from build import c, code, note, p, rif, steps, table, term, tip, ul, warn

# ── 20.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX is written in Italian and speaks English. The project's own language — documents, "
       "comments, names in the code, commit messages, reports — is Italian; everything a customer or an "
       "administrator reads is English. The line is drawn by what the reader is, not by the file type.",
       lead=True) + \
    table(["Italian", "English"], [
        ["documents: " + c("README.md") + ", " + c("SPECIFICHE.md") + ", " + c("RCP.md") + ", " + c("DECISIONI.md")
         + ", " + c("LEZIONI.md") + ", " + c("FASI.md") + ", phase documents, studies",
         "the browser page: login, warnings, errors, and the texts the server sends to the page ("
         + c("DECISIONI.md") + " §10.32, 5 Oct 2026)"],
        ["comments and identifiers: " + c("palco") + ", " + c("cattura") + ", " + c("sentinella") + ", "
         + c("appunti") + ", " + c("figlio") + ", " + c("riconosci_desktop") + "…",
         "the installer: TUI, messages, " + c("RX-") + " code texts, catalogue texts, lines written into system files "
         "(§10.35, 10 Oct 2026)"],
        ["benches, their output, registers and reports", "this manual: generated from " + c("docs/sources/")
         + ", checked for leftover Italian (§10.37)"],
        ["commit messages", "command names and options of the installer (" + c("check") + ", " + c("install")
         + ", …)"],
    ], "«TAB» — Which language goes where") + \
    p("Why the split: the product is meant for system administrators outside Italy, and one interface is "
      "written and tested once; the project's reasoning, on the other hand, lives in a long Italian record "
      "that the code cites section by section, and translating names would sever those links. Two consequences "
      "for a maintainer: in this manual, Italian names appear only as code (they are the real names in the "
      "sources); and administrator-facing texts live in one place per program — "
      + c("installatore/motore/testi.go") + ", " + c("installatore/interfaccia/testi.go") + ", the page's own "
      "strings — so that another language can be added later without hunting for them.") + \
    note("REMOTIX does not translate or touch the desktops. Users see their programs and their desktop in the "
         "machine's language; only REMOTIX's own text is English (§10.35).", "The desktops keep their language.") + \
    p("A detail of style in C and shell sources: accented letters are written with an apostrophe in comments "
      "and messages (" + c("e'") + ", " + c("puo'") + ", " + c("perche'") + "). Inside " + c("${…:?…}")
      + " and inside double-quoted shell strings an apostrophe is not style but a hazard — see "
      + rif("Rules for code and scripts") + ".")

# ── 20.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Every statement of fact in the project carries a mark that says how much it is worth. The marks are "
       "used everywhere — documents, comments, commit messages, bench headers — and they are the first thing "
       "to read in any sentence.", lead=True) + \
    table(["Mark", "Meaning", "What may rest on it"], [
        [c("[M]"), "measured by us, on the hardware, with the date", "a decision"],
        [c("[R]"), "read in the code of a reference (Mutter, KWin, wlroots, a browser…)", "a decision, if the code is the one that runs"],
        [c("[S]"), "read in a specification", "a design, to be measured"],
        [c("[?]"), "assumed, <b>not yet measured</b>", "only a provisional decision, written as such"],
    ], "«TAB» — The evidence marks (" + c("CODER.md") + " §5)") + \
    p("A decision resting on a " + c("[?]") + " is a decision taken halfway (" + c("LEZIONI.md") + " §2.3-quater); "
      "the difference between «the user said yes» and «a consequence I drew» is exactly what the marks keep. "
      "When a measurement contradicts a document, the document is updated <b>at the same moment</b>, with the "
      "date and the source: a reference that ages in silence is worse than no reference.") + \
    ul([
        "<b>Numbers come with their hardware and date.</b> The project's numbers come from one test machine with "
        "an integrated Intel GPU and, for some campaigns, an AMD Radeon RX 6800; a number without its machine "
        "is not citable. A number measured under load comes with the load (" + c("LEZIONI.md") + " §1.26).",
        "<b>Historical measurements are flagged.</b> When ffmpeg left the product (phase 18) the measurements it "
        "invalidated were removed, and the documents that keep older numbers carry a banner saying they are "
        "historical, measured on the machine of that time.",
        "<b>External code is marked</b> in documents with " + c("⟨v1⟩") + ", " + c("⟨mutter⟩") + ", "
        + c("⟨kwin⟩") + " and similar, so that mesh C16 knows a cited path lives outside the repository.",
        "<b>No line coordinates into our own code</b> (" + c("src/&lt;file&gt;.c:&lt;line&gt;") + ") in documents: a coordinate "
        "right today is wrong next week and cannot be told apart. Cite the file and the name, which move with "
        "the code. Mesh C16 enforces it on every push that touches documents.",
    ])

# ── 20.3 ─────────────────────────────────────────────────────────────────────
S3 = p(c("DECISIONI.md") + " does not explain and does not persuade: it <b>records</b>. A decision taken aloud "
       "and not written is one nobody remembers in two weeks, and the first doubt reopens it from scratch.",
       lead=True) + \
    table(["Mark", "Meaning", "How it changes"], [
        ["✅ Decided", "the user said yes, explicitly", "reopened only by a measurement that contradicts it — and then "
         "rewritten at the same moment, with date and source"],
        ["🔸 Derived", "a logical consequence of a ✅, written but never pronounced", "corrected without discussion "
         "if wrong; becomes ✅ when the user confirms it"],
        ["❓ Open", "a question asked, the answer not given yet — not a decision but a hole", "when answered it "
         "<b>moves</b> to the section it belongs to and changes mark; one does not answer at the bottom"],
    ], "«TAB» — The marks of the decision register") + \
    p("Each entry says <b>what</b>, <b>when</b>, <b>why</b> and <b>with what certainty</b>, usually with the "
      "user's own words. Newer sections supersede older ones; a superseded entry is not deleted but marked "
      "«⛔ superseded by §x», so that its reasoning stays readable and nobody revives it by accident (for "
      "example §10.15, a bilingual installer, superseded by §10.35). Before proposing an alternative, check "
      "that it was not already rejected — Flatpak and AppImage (§10.11), live canvas resizing (§5.1-bis), a "
      "graphical installer window (§10.31) and per-compositor targets (§0.5) all were, with reasons.") + \
    ul([
        "<b>Decisions live in " + c("DECISIONI.md") + ", once.</b> Phase documents, " + c("README.md") + " and "
        "this manual refer to them; they do not copy them. Eleven registers are eleven places to search, and "
        "sooner or later two contradict each other.",
        "<b>The «later» has its own place:</b> " + c("MASTERPLAN.md") + " lists work for when the product is "
        "finished. Every entry must say <b>what it costs never to do it</b>; an entry whose «never» costs nothing "
        "is deleted. Anything that must happen before the end goes into a phase, not there.",
        "<b>Open questions</b> are §7 of " + c("DECISIONI.md") + ": holes in the thinking, not work items.",
    ])

# ── 20.4 ─────────────────────────────────────────────────────────────────────
S4 = p("The project keeps few, large documents, read in a fixed order. Agents' reports are not kept: in "
       "August 2026 ninety-four report files were removed by the user's decision, and what mattered in them "
       "had been moved into the documents below.", lead=True) + \
    table(["#", "Document", "What it holds"], [
        ["1", c("LEZIONI.md"), "the method: how to measure, test and learn — inherited from v1, which stalled every time on "
         "a measurement that did not measure what was believed. Its §0 is the five lessons worth more than all the rest"],
        ["2", c("SPECIFICHE.md"), "what the product does and does not do"],
        ["3", c("RCP.md"), "how the two sides talk; the arbiter of the wire"],
        ["4", c("PIANO.md"), "the phases in order, each with its bench and closing criterion"],
        ["5", c("DECISIONI.md"), "why: every decision with date, author and certainty"],
        ["6", c("MASTERPLAN.md"), "what is done at the end, and what it costs never to do it"],
        ["—", c("CODER.md") + ", " + c("REVIEWER.md"), "the rules of whoever writes and whoever looks for contradictions; read before touching anything"],
        ["—", c("STUDI.md"), "readings of the code of GNOME, KDE, XFCE, LXQt, Cinnamon, the web platform and xpra, done before writing"],
        ["—", c("FASI.md") + " and " + c("fasi/"), "what was done, phase by phase; a phase's document is opened when the phase opens"],
    ], "«TAB» — The documents, in reading order") + \
    p("A phase document is <b>opened at the start and filled as the work goes</b>; written at the end it would "
      "be an account, in which measurements are remembered rather than recorded. Its skeleton is fixed by "
      + c("PIANO.md") + " §0.2:") + \
    code("""# Fase N — <title>
Opened on <date> · Closed on <date>
## Che cosa deve produrre        one line, and what the user sees and judges
## Il banco                      written BEFORE developing, with its positive control
## Che cosa è stato sviluppato   files, lines, what they are for
## Le misure                     expected · measured · date, the scene next to every number
## Che cosa NON ha funzionato    dead ends, with the reason, embarrassing ones included
## Le decisioni prodotte         links to DECISIONI.md, never copies
## Che cosa resta [?]            what the phase leaves open, declared
## Il giudizio dell'utente       the user's real sentence, with the date""", "text", "The skeleton of a phase document (headings as they are written)") + \
    p("Four rules of the plan go with it: decisions once, in " + c("DECISIONI.md") + "; «what did not work» is "
      "filled even when it looks bad — the seven dead ends of v1 in " + c("LEZIONI.md") + " §8 exist only because "
      "failures were written; <b>a phase closes on a measurement judged by the user</b>, not on a complete "
      "document (invariant I8); and the bench is certified before it is believed. And one consequence worth "
      "more than the rules: <i>if you cannot write the bench at the start, you have not understood the phase yet.</i>")

# ── 20.5 ─────────────────────────────────────────────────────────────────────
S5 = p("Work is done by two kinds of agent with opposite jobs, under rules written in " + c("CODER.md")
       + " and " + c("REVIEWER.md") + ". Every rule on one side has its check on the other; a rule without a "
       "check is unverified, a check without a rule is checking something nobody asked for.", lead=True) + \
    table(["#", "Invariant", "What the reviewer blocks"], [
        ["I1", "the frame rate drops only when a measurement shows the line cannot carry it, always declared in "
         "the log; below the minimum, frames drop — never resolution, never the connection",
         "any reduction for prudence or saving, any silent degradation, any path that disconnects instead of slowing"],
        ["I2", "one graphical session per user; the local session wins; a second connection is refused with a clear message",
         "any path to a second graphical session"],
        ["I3", "authentication starts from denied: no pixel and no command without the validator",
         "any path to a pixel or an input event that skips the validator"],
        ["I4", "the stage (capture, control, virtual monitor) belongs to the session, not the connection; it survives detach",
         "code that dismantles the stage on disconnect"],
        ["I5", "volume belongs to the session; whoever connects finds it at maximum", "a volume level that survives reconnection"],
        ["I6", "what changes what the user <i>sees</i> stays behind a switch, off, until the user has looked",
         "a perceptible change shipped without that switch"],
        ["I7", "protection against a known defect lives in the program, not in a configuration line that can be lost",
         "a protection entrusted to configuration"],
        ["I8", "the measure is what the user sees, not the number a bench prints", "a visual validation done only on the bench"],
    ], "«TAB» — The invariants (" + c("CODER.md") + " §2, " + c("REVIEWER.md") + " §3)") + \
    p("The reviewer <b>finds contradictions, not truths</b>: every verdict has the form «this contradicts X», "
      "never «this is right», and a green review is declared as «found nothing», not as approval. A finding "
      "has a fixed shape — where, what it contradicts, <b>how it is demonstrated</b> (a concrete input, not a "
      "hypothesis), and a mark: " + c("[R]") + " confirmed by an existing rule, corrected; " + c("[?]")
      + " a suspicion, handed to the writer to <i>measure</i>; " + c("[M]") + " only if actually run. The "
      "reviewer does not measure, does not rewrite and does not supplement what the code omits. The writer "
      "does not ask the reviewer to measure, and does not rewrite code on a " + c("[?]") + " before measuring it.") + \
    table(["When", "On what", "Why there"], [
        ["as soon as the bench exists, before the product", "the bench", "a defect in the product is found by a good bench; "
         "a defect in the bench is found by nothing, and poisons every later measurement because it gives confidence"],
        ["when the code exists, before measuring it", "the product", "measuring code that already contradicts a written rule is time spent learning what was known"],
        ["before closing the phase", "the phase document", "every number has its scene, failures are there, no " + c("[?]") + " was silently promoted"],
    ], "«TAB» — The three moments of review (" + c("PIANO.md") + " §0.4)") + \
    p("Review weighs more here than in a usual project because dropping RDP removed the external arbiter: "
      + c("mstsc") + " used to complain for free when the specification was misread, and two programs written by "
      "the same hand that agree confirm nothing. Three things replace it, none sufficient alone: " + c("RCP.md")
      + " (the written arbiter), the wire validator (the mechanical one) and adversarial review (the only one that "
      "can notice that client and server share the same misunderstanding). In practice reviewers are sent <b>to "
      "disprove</b>: the mandate «try to prove me wrong» found the unreachable green branch of C1 in ten minutes "
      "after it had governed the order of work for weeks.") + \
    table(["#", "Form of error", "How it shows"], [
        ["E1", "necessary taken for sufficient", "«it opened a render node, so it renders on the GPU»"],
        ["E2", "a component that decides by itself", "the encoder falls back to the CPU without saying so; two measurements under one label"],
        ["E3", "a function does more than its name says", "a «set error» that logs but does not send"],
        ["E4", "an order assumed interchangeable", "a sequence with one valid order, each permutation punished by a different error"],
        ["E5", "a «fact» that was an unmeasured deduction", "a decision with a reason nobody verified"],
        ["E6", "the sender deduced instead of asked", "three wrong diagnoses of who killed the server; ask the kernel"],
        ["E7", "verified on the sending side", "the log says «I called it», not «the byte arrived»"],
        ["E8", "silence taken for zero", "«empty» and «forbidden» look the same"],
        ["E9", "a start-up sample taken for the steady state", "the first frames repaint everything"],
        ["E10", "a green test on the wrong client", "the only client that tolerates the defect"],
        ["E11", "leaning on a mechanism that exists in four versions", "the cure is a configuration line, different per desktop, rewritten by a daemon"],
        ["E12", "a deduction instead of a message", "«if two were in flight, which one does this answer?»"],
        ["E13", "a wait sized for one loop, paid by all the others", "a 250 ms frame wait became 136 ms median on every click"],
        ["E14", "the bench is silent instead of red", "the most frequent of all: nine bench defects out of nine in phase 9"],
        ["E15", "the wrong quantity, ordering the cases backwards", "a loss ratio that measured reordering; test the quantity on the two known extremes first"],
    ], "«TAB» — The catalogue of error forms (" + c("REVIEWER.md") + " §2)")

# ── 20.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The numbers are set by the user and the technique serves them (" + c("CODER.md") + " §1): minimum 480p "
       "at 25 fps with 24-bit colour, a guarantee of service; desired 4K at 60 fps with 10 bits per channel; "
       "and, since 9 Aug 2026, a ceiling of 50 ms and a target of 40 ms from input received to frame sent, "
       "counting only the part that is ours. Upwards the desired filters choices; downwards the minimum binds "
       "them; and delay weighs more than frames.", lead=True) + \
    table(["Rule", "In short"], [
        ["Depend, do not rewrite", "every component we write is maintained forever; use the system's mechanisms ("
         + c("logind") + ", PAM, PipeWire, libei, xkbcommon, QUIC)"],
        ["Depend on the compositor, not on its surroundings", "the compositor must be followed (only it delivers frames and "
         "takes input); screen lockers, idle daemons, power managers and display managers come in four versions — "
         "when doing it ourselves once is cheaper, we do it ourselves (the lock and idle handling are REMOTIX's)"],
        ["Degrade, do not fail — and declare it", "every missing dependency has a fallback, and a silent fallback is two behaviours under one label"],
        ["Talk to the compositor directly", "no portal where it means authorisation dialogs: an unattended service cannot click them"],
        ["Never wait inside the asynchronous loop", "not even in a destructor that joins a thread: a hidden wait stops every connection on that thread"],
        ["Compose a session's environment from scratch", "one variable at a time; an inherited wrong locale can stop every application"],
        ["Silence is not zero, green is not true", "a counter must be able to see the defect it looks for"],
        ["One way to switch each cure", "the cures of phase 9 are on by default and switch off only with their command-line option — no "
         "environment variable, no build switch: two ways to switch one cure are two numbers that diverge"],
        ["No per-compositor feature switches", "a function one desktop cannot give leaves the product (" + c("DECISIONI.md")
         + " §5.1-bis); per-desktop code only for how to start, capture and inject"],
        ["A protection lives in the program", "invariant I7: a fix in a configuration file is lost with the file"],
    ], "«TAB» — Rules for writing the product (" + c("CODER.md") + " §4)") + \
    p("Comments carry the <b>why</b> next to the how, and the source of the why: a section of " + c("RCP.md")
      + " or " + c("DECISIONI.md") + ", a lesson, a measurement with its date. The sources are long because of "
      "this, and deliberately so: the record of what was tried and failed sits next to the line it protects.") + \
    code("""U=${1:?serve l'utente}            # ⛔ the apostrophe OPENS a quotation…
PROFILO=${2:?serve il profilo}    # …and this line ends up INSIDE the string""",
         "bash", "The script trap of 25 Aug 2026 (CODER.md §4-bis)") + \
    p("The apostrophe swallowed four lines up to the next " + c("'") + ", which sat in a comment; " + c("PROFILO=")
      + " never ran, and the script died much later on an unrelated line — and " + c("bash -n") + " passed, "
      "because the syntax was valid. Hence two rules for scripts: no apostrophes inside " + c("${…:?…}")
      + " or double-quoted strings, and <b>a syntax check is not a test</b>: a new script is run at least once and "
      "one looks at what it <i>produced</i>, not at its exit code. Benches call commands through arrays, never "
      "through nested " + c("sh -c") + ", since a command that lost its quotes ran nothing and returned 0.")

# ── 20.7 ─────────────────────────────────────────────────────────────────────
S7 = p("Every commit leaves the project built, checked and documented. The list is short because most of "
       "it runs by itself; what does not run by itself is the part that is forgotten.", lead=True) + steps([
    "<b>The product builds</b>: " + c("make") + " in " + c("src/") + " (inside the build container — see "
    + rif("Build and release") + "). The build first compares the twin RCP files with " + c("banchi/rcp/")
    + " and stops if they differ; " + c("GEMELLO=nessuno") + " builds without the comparison only when declared.",
    "<b>The installer's tests</b>, if " + c("installatore/") + " changed: " + c("installatore/costruisci.sh prove")
    + " (go vet and go test: state machine, register, resume, codes, English texts).",
    "<b>The documents are updated in the same commit</b> as the change they describe: the phase document "
    "(a measurement with its date and scene), " + c("DECISIONI.md") + " if something was decided, the chapter of "
    "this manual that describes the behaviour.",
    "<b>The manual</b>, if " + c("docs/sources/") + " changed: " + c("python3 docs/sources/build.py --controlla")
    + ", then " + c("python3 docs/sources/build.py") + " to regenerate the published page in " + c("docs/") + ". "
    "The check fails on cited files, functions, " + c("REMOTIX_*") + " variables or " + c("RX-") + " codes that do "
    "not exist, on undocumented " + c("REMOTIX_*") + " variables read by the product, on broken internal links, "
    "and on Italian left in the text or in figure labels.",
    "<b>Push</b>: the " + c("pre-push") + " hook (" + c("11-gancio.sh") + ") picks the family from the paths "
    "that changed — documents only run C16 in under a second; " + c("banchi/") + " runs the net's own checks; "
    + c("src/") + " runs the fast family under its 180 s ceiling — and appends its line to the hook's register, "
    "which is committed like any file.",
    "<b>Before closing a phase</b>, by name: " + c("--famiglia tutto") + " or the functional suite, which no path "
    "can infer.",
]) + \
    table(["Prefix", "Used for"], [
        ["🧪", "benches and tests"], ["📋", "documents and decisions"], ["📊", "measurements and their reading"],
        ["🧰", "tools, the installer"], ["🎨", "design and mockups"], ["📦", "packaging"],
    ], "«TAB» — Commit message prefixes, as the history uses them") + \
    p("Commit messages are Italian, start with an emoji that says what kind of change it is, and cite the "
      "section of the document they implement (for example «📋 DECISIONI §10.35: …»). This is a practice of "
      "the history, not a written rule.") + \
    warn("the test machine is shared with long measurement campaigns and with the user's own manual tests. "
         "Never restart the product server, rebuild a box or run a heavy family there while a campaign or a "
         "person is using it; the box lock and the suite's «is a person logged in?» guard exist because it "
         "happened. Credentials for it are read from a file outside the repository and never committed.",
         "Do not disturb the test machine.")

CHAPTER = ("Conventions", [
    ("Italian inside, English outside", S1),
    ("Evidence marks", S2),
    ("The decision register", S3),
    ("The documents of the project", S4),
    ("Writer and reviewer", S5),
    ("Rules for code and scripts", S6),
    ("Before every commit", S7),
])
