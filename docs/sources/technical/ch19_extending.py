from build import arrow, box, c, code, fig, note, p, rif, steps, table, text, tip, ul, warn, zone

# ── 19.1 ─────────────────────────────────────────────────────────────────────
GATES = fig(
    box(20, 40, 120, 52, "CP0", "baseline: full net", "dark")
    + box(160, 40, 120, 52, "CP1", "increment defined", "navy")
    + box(300, 40, 120, 52, "CP2", "observed, not deduced", "navy")
    + box(440, 40, 120, 52, "CP3", "minimal change", "blue")
    + box(580, 40, 120, 52, "CP4", "proof on the new one", "blue")
    + box(720, 40, 160, 52, "Clients and net", "real browsers, full net", "green")
    + "".join(arrow(x, 66, x + 18, 66) for x in (141, 281, 421, 561, 701))
    + arrow(800, 94, 800, 130) + arrow(800, 130, 80, 130) + arrow(80, 130, 80, 96)
    + text(440, 124, "checkpoint commit, then the next increment", 11.5, "#334155"),
    900, 150, "«FIG» — The gates every increment passes (phases 12–14)")

S1 = p("REMOTIX has been extended three times in the same way: KDE, XFCE and LXQt were each added "
       "while the desktops already served had to keep every certified capability. The method that made "
       "this work is more important than any single file it touched, and it is the first thing to reuse.",
       lead=True) + GATES + \
    table(["Gate", "What it requires"], [
        ["CP0", "the baseline: the full safety net on all boxes, the same binary everywhere"],
        ["CP1", "the increment is defined: objective, invariant, modules, proof on the new desktop, client proof, "
         "regressions to watch on the old ones, criterion"],
        ["CP2", "old and new desktops <b>observed</b> on the point of the increment, and the difference written — "
         "nothing deduced"],
        ["CP3", "the minimal change designed: files, why, and what of the old desktops stays as it is"],
        ["CP4", "the proof on the new desktop actually run, on a declared scene, with a <b>negative control</b> "
         "(the old binary on the same scene must not pass)"],
        ["clients", "Firefox and Chrome on Linux when the increment touches the path"],
        ["net", "the full net, old desktops unchanged, injected faults still caught"],
        ["checkpoint", "a commit that can be resumed"],
    ], "«TAB» — The gates of an increment") + \
    p("A red on a desktop already served is <b>a regression until proven otherwise</b>, and it is classified: "
      "A true regression · B one desktop's assumption hidden in common code · C bench defect · D wrong "
      "invariant (never as a shortcut). Each increment is small enough that a red has one suspect. When the "
      "change to common code cannot be separated from the new desktop's code, phase 11 §3.3 asks to split it "
      "in three steps — common changes first, proved on the old desktops; then the new desktop's code, which "
      "the old ones do not cross; then switching the new box on — and to declare it when the split is "
      "impossible, because from then on a red has two suspects.") + \
    note("there are no per-compositor feature switches. What the product offers is asked of all four desktops "
         "identically (" + c("DECISIONI.md") + " (the decision register) §0.5, §5.1-bis); a function that "
         "one desktop cannot give leaves the product instead of living behind a switch — live canvas resizing "
         "left on 17 Aug 2026 because KWin 6.3 could not do it. Per-desktop code exists only for <i>how</i>: how "
         "a session starts, which protocol captures, which channel injects input.", "The rule that bounds every extension.")

# ── 19.2 ─────────────────────────────────────────────────────────────────────
TOUCH = fig(
    zone(20, 40, 420, 300, "In the product (src/)")
    + box(40, 74, 380, 40, "Recognition", "riconosci_desktop(), enum appended", "navy", 12)
    + box(40, 122, 380, 40, "Session", "environment, start line, alive, Log Out, settings", "navy", 12)
    + box(40, 170, 380, 40, "Stage and capture", "Mutter · KWin · wlroots source behind the capture", "blue", 12)
    + box(40, 218, 380, 40, "Input and clipboard", "libei · virtual keyboard and pointer · data-control", "blue", 12)
    + box(40, 266, 380, 40, "Cursor shape, SESSIONE name", "forma.c, wt_desktop()", "blue", 12)
    + zone(460, 40, 420, 300, "Around the product")
    + box(480, 74, 380, 40, "Safety-net box", "Contenitore.<d>, adapter, port", "dark", 12)
    + box(480, 122, 380, 40, "Capability gate", "one row per desktop, opened late", "dark", 12)
    + box(480, 170, 380, 40, "Suite, stress, phone", "desktop lists, workloads, Log Out gesture", "dark", 12)
    + box(480, 218, 380, 40, "Installer", "package names, catalogue, components", "amber", 12)
    + box(480, 266, 380, 40, "Documents", "study, phase document, decisions", "amber", 12),
    900, 350, "«FIG» — Where a new desktop touches REMOTIX")

S2 = p("A desktop is not a module of REMOTIX: it is a set of answers spread across the session code, the "
       "child process and the capture, input and clipboard paths. Each family of compositors answers "
       "differently; inside a family almost everything is shared.", lead=True) + TOUCH + \
    table(["Question", "GNOME (Mutter)", "KDE (KWin)", "XFCE, LXQt (labwc, wlroots)"], [
        ["how the session is recognised", c("gnome-session") + " in " + c("PATH"), c("startplasma-wayland")
         + " and no " + c("gnome-session"), c("xfce4-session") + " / " + c("lxqt-session") + "; " + c("labwc")
         + " is a precondition, never the marker"],
        ["who is the compositor", "a systemd user unit, drop-in " + c("--headless"), "a systemd user unit, drop-in "
         + c("--virtual --width W --height H"), c("labwc") + " started by us, " + c("WLR_BACKENDS=headless")
         + "; no unit, so " + c("scrivi_dropin()") + " (write the drop-in) has nothing to act on"],
        ["monitor at birth", "none until a consumer attaches (" + c("RecordVirtual") + ")", "one, the size of the first client, fixed",
         "one, 1280×720, resized through " + c("zwlr_output_manager_v1")],
        ["capture", "D-Bus ScreenCast, PipeWire pushes", c("zkde_screencast_unstable_v1") + ", PipeWire pushes; "
         "needs a " + c(".desktop") + " permission", c("zwlr_screencopy_manager_v1") + " v3: we pull one frame per request"],
        ["input", "libei through " + c("ConnectToEIS"), "libei through KWin's " + c("connectToEIS"),
         "no libei on wlroots: " + c("zwp_virtual_keyboard_v1") + " and " + c("zwlr_virtual_pointer_v1")
         + ", modifiers written by us"],
        ["clipboard", "Mutter's RemoteDesktop session (" + c("EnableClipboard") + ", " + c("appunti.c") + " (clipboard))", "data-control (" + c("appunti_kde.c") + ")", "the same file, a second entry point ("
         + c("appunti_kde_apri_wlroots()") + ")"],
    ], "«TAB» — The three families") + \
    p("The product's touch points, in the order an increment meets them:") + steps([
        "<b>Recognition</b> — " + c("riconosci_desktop()") + " (recognise the desktop) in " + c("src/sessione.c") + ", decided once per "
        "process and read through " + c("sessione_desktop()") + ". It is a search, not an arbitration: one machine, "
        "one desktop (" + c("DECISIONI.md") + " §0.6). A new desktop gets a new value of " + c("SessioneDesktop")
        + " <b>appended at the end</b>: the value travels as a " + c("uint32_t") + " between parent and child, and "
        "moving 0 or 1 would break that boundary. Its branch goes after the existing ones so that no machine served "
        "today changes behaviour; an ambiguous machine is resolved as before and <i>declared</i> in the log.",
        "<b>Every implicit negation</b> — " + c("sessione.c") + " and " + c("figlio.c") + " (the per-user child) were written as «if KDE … "
        "else GNOME». Adding a value turns every " + c("else") + " into «GNOME or the new one» without a compiler "
        "warning; phase 13 counted thirteen of them. Each must become explicit, and family predicates exist for "
        "the facts that belong to the compositor rather than the session (" + c("sessione_su_wlroots()") + ", “is the session on wlroots?”).",
        "<b>The session</b> — environment composed from scratch, one variable at a time (" + c("CODER.md")
        + " §4.5); the start line; how «alive» is read (a name on the bus, the compositor's unit, or neither); the "
        "«Log Out» gesture the product recognises; the user-settings rule (only lock, reboot, suspend and standby "
        "may be written to the user's settings, everything else lives only in the remote session, "
        + c("DECISIONI.md") + " §8.2); dangerous menu entries hidden; the guard against a second session.",
        "<b>The stage</b> — " + c("figlio.c") + " opens Mutter (" + c("mutter_apri()") + ", open Mutter), KWin ("
        + c("kwin_apri()") + ") or nothing (on wlroots the source is the capture itself), then calls "
        + c("cattura_avvia()") + " (start the capture) or " + c("cattura_avvia_wlr()") + ". A pull-model source entered <i>under</i> the "
        "capture interface, not beside it: the 35 call sites in " + c("figlio.c") + " did not change.",
        "<b>Input and clipboard</b> — " + c("input.c") + " with libei, or " + c("wlr_input.c") + "; "
        + c("appunti_apri_kde()") + " or " + c("appunti_apri_wlroots()") + " (open the clipboard), both in " + c("appunti.c")
        + " and both handing over to " + c("appunti_kde.c") + ".",
        "<b>The name on the wire</b> — " + c("main.c") + " maps the desktop to the name sent in " + c("SESSIONE")
        + " (the session message, " + c("wt_desktop()") + "); a desktop the product does not recognise is reported as "
        + c("sconosciuto") + " (unknown).",
        "<b>Cursor shape</b> — the real pointer shape reaches the browser on all four desktops: Mutter sends it in "
        "the cursor metadata; on KDE and labwc, where the compositor draws the pointer into the image, "
        + c("forma.c") + " (shape) writes an encoded cursor theme whose colours say which shape was asked for, read "
        "from the metadata on KDE (" + c("cursore.c") + ") and through a 3×3 probe on labwc (" + c("wlroots.c")
        + "); a new desktop must give it too, or the shape leaves the product for everybody.",
    ]) + \
    warn("phase 13 found that " + c("unita_inattiva()") + " (unit inactive), the guard against a second session, asks systemd "
         "whether the compositor's unit is stopped — and an <i>unknown</i> unit counts as stopped. On a desktop "
         "whose compositor is not a unit, a guard paid for on 16 Aug 2026 would not have failed: it would have "
         "vanished. Before reusing a guard, ask what fact it reads, and whether that fact exists on the new "
         "desktop.", "Guards that evaporate.")

# ── 19.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The three additions are the worked example. Each row is an increment that passed all the gates; "
       "the surprises column is the part worth reading before the next desktop.", lead=True) + \
    table(["Increment", "What it added", "Surprises, and how they were met"], [
        "KDE Plasma — phase 12, 18–20 Sep 2026 (the baseline protected: GNOME)",
        ["1 · Plasma is born", "recognition; Plasma's environment (" + c("XDG_MENU_PREFIX=plasma-")
         + "); a KWin drop-in carrying the client's size; the KDE logout", "the box did not contain Plasma (only "
         + c("kwin-wayland") + "); installing it by hand in the running box broke " + c("polkit") + " — the box "
         "rebuilt from its recipe did not. Plasma took 2.59 s to appear; the negative control (old binary) never "
         "started it"],
        ["2 · the image arrives", "a new " + c("kwin.c") + " (capture only, from v1), the protocol XML and "
         + c("wayland-scanner") + " in the Makefile, the stage branch in " + c("figlio.c"),
         "the screencast global is hidden unless a " + c(".desktop") + " declares " + c("X-KDE-Wayland-Interfaces")
         + " with " + c("Exec=") + " on the canonical binary; KWin 6.3.6 cannot resize its virtual output, so "
         "the capture asks the output's size (" + c("misura_del_palco") + ", the stage's size) and the page rescales; the first 2.4 s "
         "are Plasma's splash screen, which fooled the bench's «before» photograph"],
        ["3 · mouse and keyboard", "KWin's " + c("connectToEIS") + " and the pointer region by geometry",
         "the wheel needs " + c("scroll_discrete") + " in 120-unit steps on KWin; C3's «encoder stopped» fault landed "
         "on the splash screen and was skipped on KDE, declared"],
        ["4–13", "the bench sees KDE as GNOME (C2, C8b), clipboard, screen never blanking, C17, the card's groups "
         "set by the product (C18), the user's manual tests",
         "the box needed " + c("SYS_NICE") + " (" + c("kwin_wayland") + " carries " + c("cap_sys_nice=ep") + ") and "
         + c("WAKE_ALARM") + " (powerdevil); the " + c("render") + " group did not exist in a Plasma image"],
        "XFCE — phase 13, 20–23 Sep 2026 (protected: GNOME and KDE)",
        ["1 · XFCE is born", "a third enum value; <b>the silent fallback to GNOME removed</b>: a machine with no "
         "known desktop now says so and starts nothing", "before, a solo-XFCE machine was declared «GNOME by "
         "fallback» and the log accused a foreign drop-in and Mutter — two innocents — while the cause was "
         "written once, at startup"],
        ["2 · the image arrives", c("wlroots.c") + ": screencopy v3 pulled per frame, and "
         + c("zwlr_output_manager_v1") + " v4 for the size; " + c("cattura_avvia_wlr()"),
         "labwc gives " + c("XBGR8888") + ", i.e. R G B X in memory, while the encoder expected B G R X: the "
         "bench's first image had orange folders that looked plausible (Adwaita's are blue). Phase 13's cure was to "
         "<i>ask</i> for a format already understood; later the code found that labwc offers only "
         + c("XBGR8888") + " and that branch could never fire, so " + c("wlroots.c") + " now translates the "
         + c("wl_shm") + " format and the encoder is told the channel order (" + c("CODIFICATORE_PIXEL_RGBX") + ")"],
        ["3, 5", "input through virtual keyboard and pointer (" + c("wlr_input.c") + "); the clipboard through "
         "a second entry point of " + c("appunti_kde.c"),
         "libei does not exist on wlroots (checked by absence, with a positive control); the capability gate "
         "(" + c("11-capacita-del-prodotto.sh") + ", the product's capabilities) was created so that meshes open per capability, not per desktop name"],
        "LXQt — phase 14, 24 Sep 2026 (protected: GNOME, KDE and XFCE)",
        ["1 · recognised, born, seen", c("SESSIONE_DESKTOP_LXQT = 4") + " appended; five " + c("figlio.c")
         + " tests turned into " + c("sessione_su_wlroots()") + "; our own " + c("rc.xml") + " and autostart",
         "Debian 13 has no package that starts LXQt on Wayland: the product writes the labwc start line itself, "
         "without the upstream script's autostart (which would blank the screen after 5 minutes); the idle "
         "watcher needs two settings, or the daemon re-enables it. Developed on a fifth box (port 8524) so the four "
         "official ones stayed intact"],
        ["2–3", "icons and no dangerous entries; the wallpaper born at the client's size",
         "a race: pcmanfm-qt computed its wallpaper before the output was resized; cure: " + c("wlr-randr")
         + " runs before " + c("exec lxqt-session") + " (1 defect in 20 before, 0 in 20 after at 1400×914)"],
        ["the user's evening", "pointer shape and edge drag on all desktops, Shift+arrows, «Log Out» that resurrected the session",
         "13–16 resurrections in 20 on LXQt: a race between the session manager dying and the child having seen it "
         "alive; the stage is no longer mounted until the session manager is on the bus (20 exits out of 20). "
         "Each fix got a mesh: C21, C22, C23, C24"],
    ], "«TAB» — How KDE, XFCE and LXQt were added") + \
    p("Two lessons recur. <b>The second desktop asks for what the first did not</b> — a file capability, a group, "
      "a permission — and the symptom never resembles the cause; finding it in the box before the phase cost ten "
      "minutes instead of a wrong diagnosis. And <b>the first desktop is not the reference</b>: when C5 went red on "
      "GNOME only, it was GNOME that behaved differently, and without the other three boxes the number would have "
      "been read as «sound works like this».")

# ── 19.4 ─────────────────────────────────────────────────────────────────────
S4 = p("Most of the work of a new desktop is outside " + c("src/") + ". The order below is the one phases "
       "11–14 settled on; each step has a reason that was paid for.", lead=True) + steps([
    "<b>Study first.</b> Answer the fifteen questions of " + c("LEZIONI.md") + " (lessons) §3 (how capture is asked without "
    "a portal, push or pull, is it behind a permission, can that permission be withdrawn while running, does it "
    "draw on the GPU without a monitor, what does resolution cost…) in " + c("STUDI.md") + " (studies), and before that "
    "ask who in the world already does this on that desktop (§9 step 0: the KDE study missed KRdp because it "
    "searched only the repositories already cloned).",
    "<b>Check the environment before the compositor.</b> Session of class " + c("user") + ", seat and ACLs, the "
    + c("video") + "/" + c("render") + " groups, the card, " + c("XDG_*") + " variables read from "
    + c("pam_systemd") + " and never invented (" + c("LEZIONI.md") + " §9-bis): on GNOME, four times out of five "
    "what failed was the environment.",
    "<b>The box.</b> A " + c("Contenitore.&lt;name&gt;") + " (container recipe) from " + c("debian:13") + " with exact versions, the "
    "desktop's real packages (not only the compositor), the clipboard tools of the other boxes, the render-group "
    "unit and " + c("STOPSIGNAL SIGRTMIN+3") + "; extra permissions only for that desktop and each justified by what "
    "breaks without it.",
    "<b>The adapter</b> " + c("adattatore.&lt;name&gt;.sh") + " — name, package, how to start — and nothing about "
    "how the product behaves.",
    "<b>A port</b> in the map of " + c("11-accendi.sh") + " (switch on a box; 8511–8514 are taken, unknown desktops get 8519) and "
    "the name in " + c("DESKTOP_NOTI") + " (known desktops) of " + c("11-gancio.sh") + " (the pre-push hook). Adding a recipe triggers the "
    + c("desktop-nuovo") + " (new desktop) family on the next push: everything on the new box, regression on the old ones, C14.",
    "<b>Step 0</b> in the new box: 18 verdicts, all green, before anything else.",
    "<b>A fault of its own.</b> Every new desktop enters with at least one plausible, invented fault that the "
    "net must see (phase 11 §3.6): the net is certified against the past, and a new desktop brings its own defects.",
    "<b>The capability gate.</b> A row in " + c("capacita_del_desktop") + " (the desktop's capabilities) of " + c("11-capacita-del-prodotto.sh")
    + ": empty at first, so every product mesh skips with a reason; each capability (" + c("immagine") + " image, "
    + c("input") + ", " + c("appunti") + " clipboard, " + c("forma") + " pointer shape) is opened in the increment in which its mesh is green "
    "<i>and</i> its fault was seen.",
    "<b>The «Log Out» gesture</b> of the desktop in the table C20 and C24 share (" + c("DESKTOP_E_GESTO")
    + ", desktop and gesture): it is the desktop's gesture, not a capability of the product.",
    "<b>The suite</b> — the desktop list of " + c("15-giro.py") + " (the suite round), a headless labwc in " + c("15-compositori.sh")
    + ", and the tests that depend on the desktop's applications (file manager and terminal names, menu photographs, "
    "settings that must stay untouched in " + c("15-f031b-impostazioni-intatte.py") + ", settings intact).",
    "<b>Stress</b> — the B and C workloads of " + c("16-lavori.py") + " (the workloads) name the desktop's file manager and terminal; "
    "LXQt needed " + c("qterminal -e bash") + " and a different delete gesture in pcmanfm-qt.",
    "<b>The installer</b> — the package that marks the desktop on each family (" + c("PacchettoDesktop") + ", desktop package), its "
    "display name (" + c("NomeDesktop") + ", desktop name), the catalogue's " + c("desktop") + " entry per platform with the "
    "components it needs under labwc, and the 26-combination matrix of the distribution bench.",
])

# ── 19.5 ─────────────────────────────────────────────────────────────────────
S5 = p("RCP/1 is closed by design: a receiver that does not understand something <b>must</b> close with "
       + c("ERRORE_PROTOCOLLO") + " (protocol error; " + c("RCP.md") + " §3), and inside a major version one grows only through "
       "capabilities, never by adding fields to existing messages. A new mandatory type is a new major version.",
       lead=True) + \
    table(["High byte of the type", "Channel", "Types in use"], [
        [c("0x00"), "control: only the first bidirectional stream of the session", c("CIAO") + " (hello) " + c("0x0001")
         + " … " + c("TERMINA_SESSIONE") + " (end the session) " + c("0x0011")],
        [c("0x01"), "input, client to server", c("PUNTATORE") + " (pointer) " + c("0x0101") + " … " + c("POSIZIONE_TASTO")
         + " (key position) " + c("0x0105")],
        [c("0x02"), "clipboard", c("APPUNTI_ANNUNCIO") + ", " + c("APPUNTI_CHIEDI") + ", " + c("APPUNTI_TESTO")
         + " (announce, ask, text: " + c("0x0201") + "–" + c("0x0203") + ")"],
        [c("0x03"), "video: a 28-byte header and no framing, only on unidirectional streams opened by the server",
         c("0x0301") + " key frame, " + c("0x0302") + " delta frame (the header's type field)"],
        [c("0x04"), "audio: datagrams only", c("0x0401") + ", the only one defined"],
    ], "«TAB» — The channel is the high byte of the type (" + c("RCP.md") + " §2.5); any other high byte is a protocol error") + steps([
    "<b>Write it in " + c("RCP.md") + " first</b>: number, name, direction, body in the elementary types of §6.0 "
    "(big-endian, no alignment, no padding), when it is valid, the answer, what happens to other sessions of "
    "the same user. The rule in the code says it plainly: whoever changes a rule changes " + c("RCP.md")
    + " first, or the two separate in silence.",
    "<b>Decide how an old peer reacts.</b> A peer that does not know the type closes the connection. Since page "
    "and server ship together this is acceptable for a message only one side sends on an explicit gesture ("
    + c("TERMINA_SESSIONE") + ", 15 Aug 2026); for anything a client must be able to omit, add a capability in "
    + c("CIAO") + "/" + c("ECCOMI") + " (here I am; §4.3: names " + c("a-z0-9._") + ", unknown names ignored).",
    "<b>If it tolerates anything</b>, add the line to the list of exceptions in §3 in the same moment — the "
    "list was found incomplete twice, and a client written from §3 closed exactly the sessions the other "
    "sections saved.",
    "<b>Server</b>: the constant in the type enum of " + c("src/rcp.c") + ", the exact body length checked "
    "<i>before</i> allocating, the state in which it is accepted, the handler, a log line saying what was not "
    "understood when it is refused.",
    "<b>The twin</b>: copy the same change into " + c("banchi/rcp/") + ". The build compares " + c("rcp.c")
    + ", " + c("rcp.h") + " and " + c("autenticazione.c") + " byte by byte and refuses to compile if they differ; "
    "mesh C10 checks the same on the laptop.",
    "<b>Page</b>: the type in the " + c("TIPO") + " (type) table of " + c("src/pagina.html") + " (or " + c("TIPO_INPUT")
    + "), the encoder or decoder with " + c("DataView") + " in network order, and the page's own handling of the "
    "refusal.",
    "<b>Validate against the document, not against the other side</b>: two programs written by the same hand "
    "that agree confirm nothing. " + c("01-b4-validatore.py") + " (the B4 wire validator) was written from " + c("RCP.md")
    + " alone and found a contradiction inside the document (the underscore in capability names, §4.3); bench B5, "
    "also reading only the document, found a second one two days later (§9 against §2.2).",
    "<b>Tests</b>: the suite function that exercises the gesture, real browsers, and the description in the "
    "message tables of this manual (" + rif("The RCP/1 protocol") + ", " + rif("Appendix A — Data structures and messages") + ").",
]) + \
    warn("a field added to an existing message «because it is compatible» is exactly what §9 forbids. The day an "
         "old phone stays behind, either the version was written well, or one discovers that the extra field "
         "broke it.", "Compatibility is not a feeling.")

# ── 19.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The installer's " + c("check") + " is a read-only inspection (phase PREFLIGHT) that builds a "
       "<b>profile</b> of facts, and a compatibility step that turns facts into verdicts with stable codes. A "
       "new check touches both, and the tests that guard their contracts.", lead=True) + steps([
    "<b>Read a fact</b> in " + c("installatore/motore/preflight.go") + ": a small function called from "
    + c("Preflight()") + " that records " + c("Rilevato()") + ", " + c("Verificato()") + " or "
    + c("Sconosciuto()") + " (detected, verified, unknown) on the profile. It may read files, ask logind, systemd and firewalld over D-Bus "
    "(properties and queries only), and nothing else: the only program ever launched is " + c("rpm -q")
    + " on RPM families, from a closed list annotated in the profile. <b>Nothing is written</b> — R1 compares "
    "fingerprints of " + c("/etc") + " before and after, in a container per family (" + c("prove/r1-contenitori.sh")
    + ", R1 in containers). An unreadable source is " + c("UNKNOWN") + ", never an empty value.",
    "<b>A code</b>, if the fact can be a problem: an entry in " + c("Codici") + " (codes) of " + c("motore/codici.go")
    + " with the form " + c("RX-&lt;AREA&gt;-&lt;NNN&gt;") + ", a severity (INFO, WARNING, BLOCKING), a nature "
    "(ACTION_NEEDED, RETRYABLE, RECOVERABLE, ROLLBACK_NEEDED, FATAL), an English text and, when there is one, the "
    "remedy. A code never changes meaning and is never reused: a retired code stays with a «retired» text "
    "because old registers name it (" + c("RX-GPU-001") + " is an example).",
    "<b>Attach it</b> where it belongs: " + c("Con()") + " (“with”) on the profile for a preflight message, or the "
    "verdict in " + c("compatibilita.go") + " (compatibility; e.g. " + c("fonts.scalable") + " = 0 under labwc adds a font package to "
    "the dependencies, or a missing item); administrator-facing sentences go through " + c("T()") + " and "
    + c("motore/testi.go") + " (texts).",
    "<b>Tests</b>: " + c("TestCodici") + " fails if a code used in the sources is missing or malformed; the "
    "English tests (" + c("inglese_test.go") + ") fail if any text that reaches the administrator looks Italian; " + c("preflight_test.go")
    + " builds fake machines (a Fedora with NVIDIA, a machine without a capable card) and asserts the codes. Run "
    "them with " + c("installatore/costruisci.sh prove") + " (go vet and go test in the official Go container).",
    "<b>A broken machine on purpose</b> (R2, R29): the check must report the fault with its code and its remedy, "
    "and the certification must never say green on a broken machine. UNKNOWN is never PASS (R32).",
    "<b>The manual</b>: the code in " + rif("The installer") + " — this manual's check refuses any " + c("RX-")
    + " code it cannot find in the installer's sources.",
])

# ── 19.7 ─────────────────────────────────────────────────────────────────────
S7 = p("A new bench is cheap to write and expensive to trust. The checklist below is what a reviewer asks "
       "before believing its first verdict (" + c("REVIEWER.md") + " §1).", lead=True) + \
    table(["Question", "What «yes» looks like"], [
        ["Where does it start from?", "from zero: a new tenant " + c("c&lt;n&gt;u&lt;n&gt;") + ", a new session, "
         "the box as the product would find it"],
        ["What does it look at?", "the pixel, the bytes reaching the client, the field's value — not a counter "
         "or the sender's log"],
        ["How does it know it can say red?", "an injected fault, run, with the exit code reversed; for a judge, "
         "the red cases <i>and</i> the cases that must stay green in " + c("--certifica") + " (certify)"],
        ["Can it tell zero from failure?", "a reading it could not take returns " + c("None") + " and the bench "
         "exits 3 with the reason"],
        ["Does it have a positive control?", "the tool finds something that is certainly there before concluding "
         "that something is absent"],
        ["Is the scene declared and moving?", "a scene file or a declared " + c("--scena") + " (scene), started and "
         "stopped by the bench in a " + c("finally")],
        ["What does it share?", "port, ban file, socket, directory, user, uid, shared-memory name — counted, and "
         "the bench refuses to measure on a busy machine"],
        ["Where does it live in the net?", "a family in " + c("11-gancio.sh") + " with its cost declared; the "
         "capability it needs in the gate; its tenants recognised by C19 and by the cleanup"],
        ["Has it run once, for real?", c("bash -n") + " proves nothing: a function that did not exist exited "
         "127 and the round went on without its first mesh"],
    ], "«TAB» — Before trusting a new bench or mesh") + \
    tip("when a new bench turns green at the first attempt, the right suspicion is not «well done» but «am I "
        "re-writing a bench that already exists?». Four clipboard benches once all typed " + c("Ctrl+V")
        + " and none tried the menu's Paste: one bench per <i>entry path</i>, not per function (" + c("LEZIONI.md")
        + " §1.18).")

CHAPTER = ("Extending REMOTIX", [
    ("The increment method", S1),
    ("A new desktop: the product side", S2),
    ("The worked example: KDE, XFCE, LXQt", S3),
    ("A new desktop: the benches and the installer", S4),
    ("A new RCP message", S5),
    ("A new installer check", S6),
    ("A new bench or mesh", S7),
])
