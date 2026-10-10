from build import (arrow, box, c, code, fig, flow, note, p, rif, seq, steps, table, term, text, tip, ul,
                   warn, zone)

# ── 16.1 ─────────────────────────────────────────────────────────────────────
LAYERS = fig(
    zone(20, 40, 860, 92, "On the laptop, at every build and before every push")
    + box(40, 70, 190, 48, "Twin check", "src/ vs banchi/rcp/, in make", "navy")
    + box(250, 70, 190, 48, "Installer tests", "go vet + go test", "navy")
    + box(460, 70, 190, 48, "Manual check", "build.py --controlla", "navy")
    + box(670, 70, 190, 48, "C10 C12 C13 C15 C16", "the net that needs git", "navy")
    + arrow(450, 134, 450, 160)
    + zone(20, 162, 860, 92, "On the test machine, in containers with the real graphics card")
    + box(40, 192, 250, 48, "Safety net (banchi/11-scatole)", "24 meshes, 4 desktop boxes", "blue")
    + box(325, 192, 250, 48, "Functional suite (banchi/15-suite)", "4 desktops x 2 real browsers", "blue")
    + box(610, 192, 250, 48, "Stress (banchi/16-stress)", "1 to 16 users per box", "blue")
    + arrow(450, 256, 450, 282)
    + zone(20, 284, 860, 92, "Elsewhere: other machines and devices")
    + box(40, 314, 250, 48, "Distributions (banchi/17-distro)", "QEMU VMs and boxes", "dark")
    + box(325, 314, 250, 48, "NVIDIA bench (banchi/19-nvidia)", "a rented machine", "dark")
    + box(610, 314, 250, 48, "Android bench (banchi/19-android)", "the user's phone, adb", "dark"),
    900, 390, "«FIG» — The layers of testing, from the cheapest to the most expensive")

S1 = p("REMOTIX has no unit-test suite in the usual sense: the C server talks to compositors, the GPU, PAM, "
       "logind and real browsers, and almost every defect the project has paid for lived in that contact, "
       "not inside a pure function. What it has instead is a large body of <i>benches</i> in "
       + c("banchi/") + " — about 1,800 files kept by git — and three of them grown into permanent "
       "machinery: the safety net, the functional suite and the stress campaign.", lead=True) + LAYERS + \
    table(["Layer", "Where", "Runs", "What it proves"], [
        ["Twin check", c("src/Makefile") + " target " + c("impronte"), "every " + c("make"),
         c("rcp.c") + ", " + c("rcp.h") + " and " + c("autenticazione.c") + " are byte-identical in "
         + c("src/") + " and " + c("banchi/rcp/") + "; otherwise the build stops"],
        ["Installer tests", c("installatore/costruisci.sh prove"), "on demand, in the official Go container",
         "the engine's state machine, register, resume, every " + c("RX-") + " code used exists, every "
         "administrator-facing text is English"],
        ["Manual check", c("python3 docs/sources/build.py --controlla"), "before committing the manual",
         "cited files, functions, " + c("REMOTIX_*") + " variables and " + c("RX-") + " codes exist; no Italian left"],
        ["Safety net", c("banchi/11-scatole/"), c("pre-push") + " hook, or by name",
         "a session is born from scratch and is seen; input, sound, clipboard, detach, cleanup, logging"],
        ["Functional suite", c("banchi/15-suite/"), "before a phase closes (about 2 hours)",
         "what the user does: 30-odd functions on 4 desktops with Firefox and Chrome"],
        ["Stress", c("banchi/16-stress/"), "overnight campaigns", "how many users stay GREEN, per desktop and card"],
        ["Distributions", c("banchi/17-distro/"), "before declaring a release ready",
         "install, reboot, update to the next release, uninstall on 26 distribution × desktop combinations"],
        ["Encoders and devices", c("banchi/18-*") + ", " + c("banchi/19-*"), "when the encoder or a platform changes",
         "old vs new encoder paths, Vulkan vs VA-API, NVIDIA, Android"],
    ], "«TAB» — What tests REMOTIX, and when") + \
    p("Two convictions shape all of it, and both were paid for. First, <b>the bench is the first suspect</b> ("
      + c("REVIEWER.md") + " §1): the project never stalled on a hard problem, it stalled every time on a "
      "measurement that did not measure what everyone believed (" + c("LEZIONI.md") + " §10). Second, <b>a "
      "check that has never been seen red is not a check</b>: every predicate carries, in " + c("--certifica")
      + ", the case that makes it fail, and that case is run, not imagined (" + c("CODER.md") + " §3.3-bis).") + \
    note("nothing in this chapter is a performance number. Capacity and speed results are tied to the "
         "hardware and date they were measured on and belong to " + rif("Performance and capacity") + ".", "Scope.")

# ── 16.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The bench folder is a record, not a toolbox: most files were written for one phase, measured once and "
       "kept next to their results. The prefix of a file is the number of the phase that wrote it; the "
       "folders are the machinery that is still run.", lead=True) + \
    table(["Prefix or folder", "Phase", "What lives there"], [
        "Historical benches (one file per bench, results in *.jsonl next to them)",
        [c("00-") + ", " + c("01-"), "0 environment, 1 the bare wire",
         "transport probes against ngtcp2, quiche and lsquic, the RCP validator (" + c("01-b4-validatore.py")
         + "), the handshake, ban and farewell benches B1–B13, the browser probe pages"],
        [c("02-"), "2 the first frame", "capture, encoding, the page decoder, PAM, the first pixel judges"],
        [c("03-"), "3 motion", "cadence, declared scenes, the mark (" + c("03-marca.py") + ")"],
        [c("04-"), "4 control", "input injection, keyboard, cursor, the first shortcuts"],
        [c("05-") + ", " + c("06-"), "5 the session, 6 canvas and view", "the sentinel, detach and reattach, canvas geometry"],
        [c("07-"), "7 audio and clipboard", "Opus, the clipboard in both directions, the Marionette client "
         + c("07-b46-marionette.py")],
        [c("08-") + ", " + c("09-") + ", " + c("10-"), "8 zero copy, 9 quality, 10 multi-tenant",
         "bad networks, the " + c("netem") + " lock " + c("09-lucchetto.py") + ", the budget, the GPU lock"],
        [c("12-") + ", " + c("13-") + ", " + c("14-"), "12 KDE, 13 XFCE, 14 LXQt",
         "the real-browser drivers " + c("12-client-veri.py") + " and " + c("12-c20-veri.py")
         + ", the increment probes of each desktop"],
        [c("attrezzi-*.sh"), "all", "shared helpers, e.g. " + c("attrezzi-gruppi-scheda.sh") + " (the "
         + c("video") + "/" + c("render") + " groups every bench tenant needs)"],
        "Machinery that is still run",
        [c("11-scatole/"), "11", "the safety net: four desktop boxes, the meshes, the hook " + c("11-gancio.sh")],
        [c("14-stress/"), "14", "the first night-stress harness, run from the tablet; superseded by " + c("16-stress/")],
        [c("15-suite/"), "15", "the functional suite with real browsers, its register and defect list"],
        [c("16-stress/"), "16, 20", "the stress ramp, the actors, the classifier; the xrdp comparison twin"],
        [c("17-distro/") + ", " + c("17-t2/") + " … " + c("17-t9/"), "17", "distribution VMs and boxes, the benches of "
         "the installer's milestones T2–T9 (T4, T8 and T9 are kept as history and are not run, except "
         + c("t8-browser.py") + ", which T10 still uses)"],
        [c("18-a1/") + ", " + c("18-scheda/") + ", " + c("18-software/"), "18", "old-vs-new comparisons when ffmpeg "
         "left the product"],
        [c("19-vulkan/") + ", " + c("19-nvidia/") + ", " + c("19-android/"), "19", "Vulkan Video vs VA-API, the NVIDIA "
         "rental bench, the Android phone bench"],
        [c("rcp/"), "1", "the twin copy of the RCP module, compiled into the ngtcp2 example server"],
        [c("prodotto/") + ", " + c("sonda/"), "1–2", "smoke test of the server inside the build container; a real "
         "browser probe against it"],
        [c("ritrovati/"), "—", "five bench files found outside the repository on 28 Aug 2026 and saved, with a README"],
    ], "«TAB» — The bench folder") + \
    p("Historical benches are not maintained: they call helpers, paths and binaries of their time. They are kept "
      "because their results are cited by " + c("FASI.md") + " and " + c("DECISIONI.md") + ", and because a "
      "verdict must stay re-readable next to the code that produced it.") + \
    tip("to find the bench behind a number in a document, search for the bench identifier (B12, C8, F-018, "
        "R19…) in " + c("banchi/") + "; the file header says what it measures, from where it starts and how it "
        "knows it can say red.")

# ── 16.3 ─────────────────────────────────────────────────────────────────────
S3 = p("Every bench and every mesh speaks the same small language. The rules are short; each one exists "
       "because its absence once produced a wrong verdict that looked right.", lead=True) + \
    table(["Exit code", "Meaning", "Retried?"], [
        [c("0"), "a judgement: it holds", "never"],
        [c("1"), "a judgement: it does not hold", "never"],
        [c("2"), "the test setup does not hold, or the usage is wrong", "never: a bad setup is inspected"],
        [c("3"), "could not look: something did not speak (with the reason)", "never"],
        [c("4"), "the turn never came (the card lock was not obtained)", "yes"],
    ], "«TAB» — The exit codes of benches and meshes") + \
    p("Code 3 is not requeued on purpose: re-running until the wanted number appears is how the project once "
      "had to withdraw two conclusions. A single 3 is neutral; <b>a frequent 3 is a bench defect</b>. The "
      "functional suite maps the same three judgements onto PASS, FAIL and BLOCKED, and a BLOCKED always "
      "carries its reason.") + \
    table(["Rule", "Why (the defect it prevents)"], [
        ["<b>Certify before believing.</b> " + c("--certifica") + " runs the pure judges on synthetic inputs, "
         "including the cases that must give red and the ones that must <i>stay</i> green",
         "Phase 9: nine bench defects in a row, and none made a bench fail — all made it silent or green "
         "(" + c("LEZIONI.md") + " §1.29)"],
        ["<b>An injected fault per check</b>, run for real (exit code reversed: 0 means the fault was seen)",
         "a net that can no longer say red looks exactly like a net that finds nothing"],
        ["<b>" + c("None") + " is not zero.</b> Could not read and nothing happened never share a face",
         "five benches once counted zero frames because a broken regular expression returned 0"],
        ["<b>The scene is declared and moving.</b> A compositor sends a frame only when something changes",
         "every frames-per-second figure taken between phase 3 and phase 9 was thrown away"],
        ["<b>Look at the pixel, not the counter.</b> A frame counter weighs nothing; a photograph of the canvas "
         "does", "process counts said 1 with and without a window (phase 11)"],
        ["<b>Real browsers certify; the Python client only diagnoses</b>",
         "the user's rule of 23 Sep 2026; the Python client hid a defect that only browsers showed"],
        ["<b>Start from zero.</b> A new user, a new session, never a reused one",
         "the session born blind stayed invisible for days because every test reused a session that already had a monitor"],
        ["<b>Whoever opens, closes</b> — scenes, browsers, tenants, in a " + c("finally")
         + ", even when the bench falls", "ten terminals and ten infinite loops left on a person's desktop (" + c("LEZIONI.md") + " §9-ter)"],
        ["<b>Silence is not success.</b> A bench that prints nothing did not succeed",
         "a command nested three times lost its quotes, ran nothing and returned 0 (" + c("LEZIONI.md") + " §1.46)"],
    ], "«TAB» — The rules every bench follows") + \
    p("<b>Isolation.</b> Benches share one test machine, so they count everything they could share: port, ban "
      "file, socket, working directory, tree, user, uid and shared-memory name (" + c("LEZIONI.md")
      + " §1.24, §1.26). Two benches on the same port once killed each other silently, and the survivor's probe "
      "kept knocking with its credentials until the server banned the machine's own address for twelve hours. "
      "Tenants created by benches are named " + c("c<n>u<n>") + " (regular expression "
      + c("^c[0-9]+b?u[0-9]+$") + "), so that cleanup and C19 recognise them and never touch a person's account.") + \
    table(["Lock", "File", "Protects"], [
        [c("netem") + " lock", c("09-lucchetto.py"), "the queueing discipline on " + c("lo") + ": two benches "
         "degrading the network together would erase each other's root qdisc. Taken with " + c("mkdir")
         + " (atomic even over ssh), with an expiry written inside; an expired lock is broken <i>and the break is "
         "declared</i>"],
        ["GPU lock", "the same module, another directory", "measurements that need the card alone; a mesh whose "
         "turn never came exits 4"],
        ["Box lock", c("/media/REMOTIX/rete11/.scatole.lock") + " (" + c("flock") + ")", "the four boxes: taken by "
         + c("15-giro.py") + " (the suite round), " + c("16-salita.py") + " (the stress climb) and " + c("11-gancio.sh")
         + " (the hook); the holder writes its name "
         "inside, children inherit the right through an environment variable, and tenant cleanup does nothing "
         "without it"],
    ], "«TAB» — The three locks") + \
    warn("the box lock exists because a " + c("git push") + " during a suite round once made the hook clean up "
         "every bench tenant — including the ones the suite had just created — and the failed logins got the test "
         "machine's address banned for 12 hours (29 Sep 2026). After the lock: a 60-minute short round with a "
         "push in the middle gave 368 PASS, 0 FAIL, 0 BLOCKED.", "Why the boxes are locked.")

# ── 16.4 ─────────────────────────────────────────────────────────────────────
S4 = p("The safety net runs in four containers, one per desktop, on the test machine itself — not in virtual "
       "machines, because a VM takes the real graphics card away, and every number of the project comes from "
       "that card (decision D1 of phase 11).", lead=True) + \
    table(["Box", "Recipe", "Desktop inside", "Port"], [
        [c("rete11-gnome"), c("Contenitore.gnome"), "GNOME Shell (Mutter)", "8511"],
        [c("rete11-kde"), c("Contenitore.kde"), "Plasma (KWin)", "8512"],
        [c("rete11-xfce"), c("Contenitore.xfce"), "XFCE on labwc", "8513"],
        [c("rete11-lxqt"), c("Contenitore.lxqt"), "LXQt on labwc", "8514"],
        [c("rete11-<d>-xrdp"), c("Contenitore.xrdp"), "the same desktop on X11 under Debian's xrdp", "—"],
    ], "«TAB» — The boxes (" + c("Contenitore.<d>") + " is the Containerfile of each box)") + \
    p("The four desktop recipes start from " + c("debian:13") + " (" + c("Contenitore.xrdp") + " is built on top of "
      "a desktop box's image) and boot " + c("systemd") + " as PID 1. Three rules keep "
      "them honest. <b>R1</b>: one binary, built once, copied into all four — and its libraries taken from where "
      "the real server takes them (a box once ran the right binary against a same-named " + c("libngtcp2.so.16")
      + " of another version, started cleanly and died at the first client with " + c("Unreachable")
      + "). <b>R2</b>: recipes declare exact versions; «the latest available» is a date disguised as a "
      "version. <b>R3</b>: alignment is <i>verified</i> by mesh C11 on the running boxes, not trusted from the "
      "recipes.") + \
    table(["Permission", "What breaks without it"], [
        [c("--systemd=always"), "the question of step 0 cannot even be asked"],
        [c("--device") + " card and render node", "the real card; " + c("11-accendi.sh") + " (switch on) maps exactly one card "
         "(Intel or the Radeon) as " + c("card0") + "/" + c("renderD128") + ", and also under its real name, because "
         "libdrm rebuilds the name from the minor number"],
        [c("--cap-add=AUDIT_CONTROL") + ", " + c("AUDIT_WRITE"), c("pam_loginuid.so") + " is " + c("required")
         + " on Debian and fails; the user manager never starts"],
        [c("--network=host"), "not a choice: " + c("netavark") + " could not apply its rules on this host. The price "
         "is that boxes share the host's ports, hence one port each"],
        [c("--cap-add=SYS_ADMIN"), "the polkit service exits with " + c("217/USER") + ", " + c("gnome-shell")
         + " waits four 25 s timeouts, and the session looks blind for about 97 s (27 Aug 2026). This permission "
         "brings the box <i>closer</i> to the real machine"],
        [c("SYS_NICE") + ", " + c("WAKE_ALARM") + " (KDE only)", c("kwin_wayland") + " and powerdevil carry file "
         "capabilities; an executable whose capability is outside the container's set does not start at all"],
    ], "«TAB» — Every extra permission, justified by what breaks without it") + \
    p("<code>--privileged</code> was refused on purpose: it would have made everything pass and taught nothing. "
      "Removing " + c("pam_loginuid") + " from the PAM stack was refused too: it would have tested a PAM chain "
      "different from the one shipped. Each recipe also carries a unit that reads the group number of the "
      "render node at boot and aligns the " + c("render") + " group to it (pinning the host's number would make "
      "a box that works here and is silent elsewhere), and " + c("STOPSIGNAL SIGRTMIN+3") + ": with "
      + c("systemd") + " as PID 1 the default " + c("SIGTERM") + " is ignored and " + c("podman stop") + " waited "
      "its whole timeout.") + \
    p("<b>Step 0</b> (" + c("11-passo0.sh") + ") validated the container before anything was built on it: the "
      "first process is systemd; logind knows the user and opens a session; linger starts the user manager "
      "without a login; a user unit starts inside the session; when the session closes, children really die; "
      + c("/run/user/<uid>") + " exists and belongs to this box; the session bus answers; a compositor "
      "announces an output and a real client draws; the card and the hardware encoder are reachable. Measured "
      "on 26 Aug 2026: 18 verdicts green out of 18, on all four boxes.") + \
    p("<b>Adapters</b> keep the list of checks blind to the desktop. Each box carries, at the same path, a "
      "short " + c("adattatore.<d>.sh") + " (adapter) that answers three questions — what is your name, which package "
      "do you come from, how do I start you — for example " + c("WLR_BACKENDS=headless") + " for labwc where "
      "Mutter wants " + c("--headless") + " and KWin " + c("--virtual") + ". The boundary is written in phase 11 "
      "§3.7: an adapter says how to start and look at a desktop, never how the product behaves; an adapter "
      "that starts containing product behaviour is a per-compositor exception in disguise.") + \
    code("""bash 11-accendi.sh costruisci gnome     # rebuild the image from the recipe
bash 11-accendi.sh accendi gnome        # throw the box away and start a fresh one
bash 11-accendi.sh prodotto gnome       # copy binary and page in
bash 11-accendi.sh server gnome         # start the product server on the box's port
bash 11-accendi.sh c4 kde --senza-tasto # one mesh, with its injected fault
bash 11-accendi.sh impronta gnome       # the fingerprint (R3)
bash 11-accendi.sh bilancio gnome       # server, tenants, /tmp: what is there now""",
         "bash", "The verbs of 11-accendi.sh (on the test machine, as root)")

# ── 16.5 ─────────────────────────────────────────────────────────────────────
S5 = p("The checks of the net are called meshes (" + c("maglie") + " in the code) and are numbered C1–C24. "
       "The columns that matter are the third and the fourth: <i>where it starts from</i> and <i>what it looks "
       "at</i>, because those were the two that explained the three failures that created the net.", lead=True) + \
    table(["Mesh", "What must be true", "Looks at", "How it knows it can say red"], [
        "The product",
        [c("C1"), "the session is born and is seen — from zero: a never-used user, a new session",
         "the server's own report of the monitor, then the image: the mark present and the image not degenerate",
         "a session without a monitor ⇒ red; colours shifted on purpose ⇒ must stay green"],
        [c("C2"), "a window opens", "the pixel, never the process count",
         c("--applicazione-che-muore") + " (the application dies); " + c("--finestra-che-non-si-apre") + " (alive, never paints)"],
        [c("C3"), "frames arrive and the scene changes", "consecutive frames differ; not collapsed",
         c("--fotogramma-ripetuto") + " (repeated frame), " + c("--codificatore-fermo") + " (stopped encoder); "
         + c("--scena-ferma") + " (still scene) is the negative control and must not be red"],
        [c("C4"), "a key reaches the screen", "image · key · image, and only the expected zone changes",
         c("--senza-tasto") + " (no key), " + c("--scena-sorda") + " (a scene that ignores keys)"],
        [c("C5"), "sound is there and is not silence", "RMS of the samples reaching the client: threshold "
         "328/32767 (−40 dBFS), at least 200 blocks, at least 50 % above threshold", c("--senza-sorgente") + " (no sound source)"],
        [c("C6"), "detach and find it again", "the child's pid and the windows in the image after reattaching",
         c("--uccidi-la-sessione") + " (kill the session)"],
        [c("C7"), "everything closes and nothing remains", "fingerprint before and after: processes, sockets, "
         "units, the card", c("--lascia-un-processo") + " (leave a process behind); " + c("--solo-distacco") + " (detach only) must stay green (I4)"],
        [c("C8"), "the second user opens the browser", "Firefox paints a full-screen " + c("#FF00FF")
         + " page: ±48 per channel, at least 25 % of the image", c("--senza-cura") + " (without the cure): only the <i>second</i> "
         "user must fail, or the test is void"],
        [c("C8b"), "and that page is seen from the client", "the difference between the first frame "
         "(no page) and the last (page)", c("--senza-cura")],
        [c("C9"), "every log line says whose it is", "two tenants alive together; every mandatory line names one",
         c("--togli-nome") + " (strip the name) on a copy of the log slice"],
        [c("C10"), "the twin copies of RCP match", "the files listed in " + c("src/Makefile") + ", byte by byte",
         "a copy with one byte changed"],
        [c("C17"), "the clipboard works both ways, also for whoever reattaches",
         "A device→session, B session→device, R a reattaching client gets it", c("--senza-copia") + " (no copy)"],
        [c("C18"), "the product adds a new user to the card's groups", "groups before, the log during, groups after",
         c("--senza-usermod") + " (no " + c("usermod") + ")"],
        [c("C20"), "after «Log Out» and a new login the screen does not flicker",
         "luminance of the second login's frames; the encoder discards the old ones", c("--scena-che-lampeggia") + " (a flashing scene)"],
        [c("C21"), "the real pointer shape reaches the browser", "the cursor image the page gives the browser",
         c("--forma-sbagliata") + " (expectations shifted by one)"],
        [c("C22"), "a window edge can be dragged", "the right edge in the canvas photograph, before and after",
         c("--senza-pulsante") + " (no button press)"],
        [c("C23"), "Shift+arrows select, and Shift does not stick", "the remote field read from the photograph",
         c("--senza-maiusc") + " (no Shift)"],
        [c("C24"), "«Log Out» ends the session every time, not 19 times out of 20",
         "the product's log and the client, for T seconds after the gesture, 10 rounds at varying times",
         c("--rientra-subito") + " (log in again at once)"],
        "The net itself",
        [c("C11"), "all boxes are aligned", "what is installed <i>inside</i> the running boxes: base, Mesa, libva, "
         "PipeWire, Firefox, libc… and the product's md5; only the desktop must differ",
         "counts the entries no box can answer (an unanswered entry passes any comparison)"],
        [c("C12"), "the hook is alive", "installed, executable, and really ran recently (dry runs do not count)",
         "11 certification cases"],
        [c("C13"), "the certification is recent", "in the last rounds a fault was injected and seen",
         "red if the red came from another mesh, naming the mesh that missed the fault"],
        [c("C14"), "the boxes do not disturb each other", "the same probe alone and in parallel, same verdict",
         c("--smentisci") + " (disprove) forces different fingerprints ⇒ 4 red out of 4"],
        [c("C15"), "the remote half really runs", "the merged register: a mesh that needed a box reached a verdict",
         "with the test machine off for good, C12 and C13 stay green; C15 goes red"],
        [c("C16"), "the documents do not lie about the repository", "no line coordinates into our code; every "
         "cited path exists (or carries an external mark); no dead links; one single resume header",
         "exceptions only in " + c("11-c16-eccezioni.txt") + ", each with where the file really is"],
        [c("C19"), "nothing of the net survives in a box", "users, homes and processes in the net's name space",
         c("--lascia-un-inquilino") + " (leave a tenant), " + c("--lascia-una-casa") + " (leave a home)"],
    ], "«TAB» — The meshes of the safety net") + \
    p("Images are judged with three poor checks and no knowledge of what a desktop looks like: a mark with a "
      "declared tolerance (compositors apply colour profiles, and H.264 4:2:0 subsamples exactly the chroma); "
      "an image that is not degenerate (not all black, not one colour, varied enough); and the expected zone "
      "changing when it must. Pixel-by-pixel comparison with a reference rots in a week and was rejected, and so "
      "was computer vision: a tolerance and a histogram were enough, and if one day they are not, that decision "
      "will come with a measurement. The image judge itself is shared — C8 imports " + c("10-f1-testimone.py")
      + " rather than keeping a second judge that could diverge in silence.") + \
    p("The net proved its worth before it was finished. Pointed at the code of 25 Aug 2026 it went red on its "
      "own on both acceptance defects — the session born blind and the second user whose browser does not "
      "start — and the injected fault exposed three bench defects that would otherwise have passed for product "
      "defects. Its full round on 27 Aug 2026 (7,896 s, four boxes) gave 57 green verdicts, 23 injected faults "
      "seen out of 25, and no bench red. Its first red from the product was two log lines in "
      + c("src/tastiera.c") + " that did not name their tenant; its most valuable one was the sound reaching "
      "the client at one fortieth of its rate on GNOME only — audible and loud, so no eye would have noticed.") + \
    note("for weeks a number — «ten new sessions out of ten are born without a monitor» — governed the order of "
         "work. It came from one mesh whose green branch was unreachable. An agent asked to <i>disprove</i> it "
         "found that in ten minutes; the true cause was that bench users were not in the " + c("video")
         + " and " + c("render") + " groups (17 sessions out of 17 see with the groups, 0 out of 4 without). "
         "Rule (" + c("LEZIONI.md") + " §1.53): when a red resists for days, first ask whether the test can say green.",
         "The lesson of C1.")

# ── 16.6 ─────────────────────────────────────────────────────────────────────
HOOK = seq([("Laptop", "git repository", "navy"), ("11-gancio.sh", "decide", "blue"),
            ("Test machine", "boxes and card", "dark")], [
    (0, 1, "git push: pre-push hook"),
    (1, 1, "changed paths ⇒ family"),
    (1, 1, "local half: C10, its fault, C15"),
    (1, 2, "systemd-run unit rete11-gancio.service"),
    (2, 2, "meshes run in the boxes"),
    (2, 1, "exit code file and register", True),
    (1, 0, "merged register, one line per round", True),
], "«FIG» — The two halves of the hook: decide where git is, run where the boxes are", width=820)

S6 = p("The net runs by itself: " + c("11-gancio.sh") + " is installed as a git " + c("pre-push")
       + " hook and decides what to run <b>from the paths that changed</b>, not from anyone's good will. "
       "A hook that asks «do you want to run the net?» does not run on the day one is in a hurry, and those are "
       "the days things break.", lead=True) + HOOK + \
    table(["Family", "Triggered by", "What runs", "Cost"], [
        [c("desktop-nuovo") + " (new desktop)", "a new " + c("Contenitore.<name>") + " added (wins over everything)",
         "everything on the new box, then C1×2 on the old ones, then " + c("rete-intera"), "hours"],
        [c("funziona") + " (it works)", c("src/") + " or " + c("web/") + " changed", "C10 and its fault, C11, C1(gnome)×2 — under a "
         "180 s ceiling", "173 s measured on 26 Aug 2026"],
        [c("rete-intera") + " (whole net)", c("11-accendi.sh") + ", a recipe, " + c("11-c8-*") + " or " + c("11-c14-*"),
         c("rete") + " plus C14, which takes all four boxes", "about 800 s"],
        [c("rete") + " (net)", "anything else under " + c("banchi/"), "C10 and its fault, C11, C12, C13, C15, C16",
         "about 11 s on the test machine, 1 s on the laptop"],
        [c("carte") + " (papers)", c("*.md") + " files and nothing under " + c("src/") + ", " + c("web/") + " or " + c("banchi/"), "C16", "0.79 s"],
        [c("niente") + " (nothing)", "anything else (the installer, the manual sources…)", "nothing, and the hook says so", "—"],
        [c("tutto") + " (everything)", "only by name (" + c("--famiglia tutto") + "), before closing a phase",
         "boxes rebuilt clean; per box: step 0, C1×10, C8, C5, C7, C9, C18 each with its fault, the product meshes, "
         "C19; then " + c("rete-intera"), "hours (7,896 s on 27 Aug 2026)"],
        [c("suite"), "only by name", "the functional suite with its technical layer", "about 2 hours"],
    ], "«TAB» — The families of the hook") + \
    p("The fast family has a hard ceiling of <b>180 s</b>: above five minutes a hook starts being switched off, "
      "above ten it certainly is. When time runs out <b>meshes are cut, the ceiling is not raised</b>, and the "
      "cuts are written at the top of the script with their cost — C8, the most important mesh, is not looked "
      "at on every push, and that is declared as the most expensive cut. A mesh that does not fit is skipped "
      "and the skip is logged; it is never truncated, because truncation would produce a red that is not the "
      "product's.") + \
    p("Each round appends one line to " + c("11-gancio-registro.jsonl") + ": where it ran, the trigger, the "
      "family, every mesh with exit code and seconds, whether a fault was injected and seen. The file is in git "
      "with " + c("merge=union") + " in " + c(".gitattributes") + ", because the two halves write it on two "
      "machines and lines are only ever added. A dry run (" + c("--secco") + ") writes its line with "
      + c("\"secco\": true") + " and C12/C13 ignore it — otherwise one dry run would let the net claim to be alive "
      "for a week.") + \
    table(["Desktop", "Capabilities opened"], [
        [c("gnome") + ", " + c("kde") + ", " + c("xfce") + ", " + c("lxqt"), c("immagine input appunti forma")],
        ["any other", "none: all product meshes skip, and the log says the product does not know that desktop"],
    ], "«TAB» — The capability gate (" + c("11-capacita-del-prodotto.sh") + ")") + \
    p("Product meshes C2, C3, C4, C6, C8b, C17 and C20–C23 (C24 runs under the gate of C20) ask the gate whether the desktop has what they need "
      "(image, input, clipboard, shape) and, if not, skip with the missing capability in the register. A "
      "capability is opened only in the increment in which the mesh that judges it has given green <i>and</i> "
      "seen its fault — not when the code exists. The gate never softens a judgement: a mesh that passes runs "
      "with the same arguments, thresholds and faults as before. C1, C5, C7, C9, C18 and C19 do not pass through "
      "it: they run on every box and say «could not look» on their own.") + \
    table(["Case", "Rule"], [
        ["red in the fast family", "blocks: fixed before moving on"],
        ["intermittent red", "is a red. «Sometimes it happens» often means «it always happens, it waits for the moment»"],
        ["repeated 3", "a single 3 is neutral; a frequent 3 is a bench defect"],
        ["false alarm", "may be declared only once understood, and is written down; a test with repeated false alarms is fixed or removed"],
        ["a test that catches nothing", "is removed, and the reason written; it is not left to die of disuse"],
    ], "«TAB» — The red policy (phase 11 §5.2)") + \
    code("""bash banchi/11-scatole/11-gancio.sh decidi                     # what it would do, and why
bash banchi/11-scatole/11-gancio.sh gira --famiglia rete
bash banchi/11-scatole/11-gancio.sh gira --famiglia tutto --scatola gnome
bash banchi/11-scatole/11-gancio.sh remoto                     # decide here, run there, report back
bash banchi/11-scatole/11-gancio.sh installa pre-push
bash banchi/11-scatole/11-gancio.sh registro 10                # the last 10 rounds""",
         "bash", "Running the hook")

# ── 16.7 ─────────────────────────────────────────────────────────────────────
S7 = p("The net is written against defects of birth, visibility, basic function and correctness between two "
       "users. It is deliberately not a performance net, not a browser-compatibility net and not an endurance "
       "test, and the gaps are written so that nobody trusts it too much.", lead=True) + \
    table(["Class", "Why it stays out"], [
        ["subtle visual regressions", "the image checks are poor on purpose, or they rot"],
        ["slow memory leaks", "need an endurance test (the last 30-minute step of the stress ramp covers part of it)"],
        ["races that depend on timing", "the net runs in quiet conditions (C24 varies the moment of its gesture for exactly this reason)"],
        ["degraded networks", "phase 9 has its own benches; the suite simulates a dead line, nothing more"],
        ["browsers", "the net uses the Python client and Firefox ESR inside the box; real Firefox and Chrome are the suite's job"],
        ["fine audio and video quality", "the user's judgement (invariant I8)"],
        ["desktop updates", "half covered: C11 sees that a recipe changed, not that the new desktop behaves worse"],
        ["<b>performance regressions</b>", "no bench compares yesterday with today: a frame that gets slower without anything breaking passes"],
    ], "«TAB» — What the net does not catch")

# ── 16.8 ─────────────────────────────────────────────────────────────────────
ROUND = flow([("Round 1", "8 suites + technical layer", "blue"), ("Defects", "D-001…, classes A–D", "amber"),
              ("Clean-up", "product and bench cures", "navy"), ("Freeze", "no change allowed", "dark"),
              ("Round 2", "must give zero defects", "green")],
             "«FIG» — The cycle of the functional suite (phase 15)")

S8 = p("On 24 Sep 2026 the user tried the product by hand and found six defects the net had not seen: the "
       "window edge that cannot be grabbed, Shift+arrow, a stripe in Firefox, the click one pixel off in Chrome, "
       "the lock icon of LXQt, «Log Out» that resurrected the LXQt session. The net looks at the pieces (the frame "
       "arrives, the key reaches the server); the suite looks at <b>what the user does</b>: select a text, grab "
       "an edge, log out.", lead=True) + ROUND + \
    p("The user's decisions of that evening frame it: the suite replaces the full net, leaving under it only "
      "a short technical layer (C7, C9, C14, C18, C19); browsers are real, Firefox and Chrome on the server, "
      "real windows; the Python client does not certify; every test has its injected fault and lasts less than "
      "10 minutes; and the cycle is round 1 ⇒ defect list ⇒ clean-up ⇒ <b>a complete round 2 with zero "
      "defects</b>, with product and tests frozen in between. If round 2 finds a defect, it is fixed and round 2 "
      "is redone in full, not just the red test.") + \
    table(["ID", "Function", "Test file"], [
        ["F-001 · F-002", "login and session creation; first image", c("15-f001-accesso-e-prima-immagine.py")],
        ["F-003", "the screen updates", c("15-f003-lo-schermo-si-aggiorna.py")],
        ["F-004", "mouse: move, left and right click, double click, drag", c("15-f004-il-mouse.py")],
        ["F-005 · F-006", "pointer shape; resizing from the edge (C21, C22 imported)",
         c("15-f005-forma-del-puntatore.py") + ", " + c("15-f006-il-bordo-si-trascina.py")],
        ["F-007 · F-008", "special keys; modifiers and combinations (C23 imported)",
         c("15-f007-tasti-speciali.py") + ", " + c("15-f008-modificatori.py")],
        ["F-009", "layout, accents, AltGr with the Italian layout", c("15-f009-accenti-e-altgr.py")],
        ["F-010", "desktop shortcuts work; dangerous ones (lock) do not", c("15-f010-scorciatoie-del-desktop.py")],
        ["F-011", "the canvas at attach: size, no stripe, full background", c("15-f011-la-tela-all-attacco.py")],
        ["F-012 · F-012B · F-013", "audio; audio after «Log Out»; video with sound",
         c("15-f012-audio.py") + ", " + c("15-f012b-audio-dopo-esci.py") + ", " + c("15-f013-video.py")],
        ["F-014 · F-015 · C/D", "clipboard both ways, also copied on the client computer",
         c("15-f014-appunti.py") + ", " + c("15-f014c-appunti-dal-computer.py")],
        ["F-016 · F-017 · P-A · P-F", "detach and reattach at the same size", c("15-f016-stacco-e-riattacco.py")],
        ["F-018 · P-C · F-018b · F-018c", "reattach at a different size; windows kept inside the screen",
         c("15-f018-riattacco-a-misura-diversa.py") + ", " + c("15-f018b-finestre-dentro-al-riattacco.py")],
        ["F-019 · P-B · P-D", "the line drops (simulated with nftables), re-entry", c("15-f019-la-rete-cade.py")],
        ["F-020 · P-E", "browser closed abruptly, then a new connection", c("15-f020-browser-chiuso-di-colpo.py")],
        ["F-021", "«Log Out» from the menu", c("15-f021-esci.py")],
        ["F-022 · F-023 · F-024 · F-024b", "silence, inactivity and abandonment clocks (shortened); a session never touched",
         c("15-f022-orologi.py") + ", " + c("15-f024b-sessione-mai-toccata.py")],
        ["F-025 · F-026", "same user from two tabs (ghost, eviction); several users together",
         c("15-f025-stesso-utente-due-schede.py") + ", " + c("15-f026-piu-utenti-insieme.py")],
        ["F-027 · F-028 · N-1 · N-3 · N-4", "wrong password, ban, negative cases",
         c("15-f027-parola-e-ban.py") + ", " + c("15-n027-negative.py")],
        ["F-029 · F-030", "no dangerous menu entries; the screen never blanks or locks (11 minutes)",
         c("15-f029-voci-pericolose-assenti.py") + ", " + c("15-f030-schermo-sempre-acceso.py")],
        ["F-031 · F-031B · F-032", "touch (the user, on Android); user settings untouched; the user's shell",
         c("15-f031-tocco.py") + ", " + c("15-f031b-impostazioni-intatte.py") + ", " + c("15-f032-la-shell-dell-utente.py")],
    ], "«TAB» — The suite's functions and the files that test them") + \
    p("Every test is a script " + c("15-fNNN-<name>.py") + " that declares, as plain text lines, what it "
      "looks at: " + c("FUNZIONI = (…)") + ", and if needed " + c("PER_BROWSER = False") + " (runs once, with "
      "Firefox), " + c("LUNGA = True") + " (runs in parallel with the others of its desktop) and "
      + c("SERVER = \"15-g7-server.sh\"") + " (needs its own server). The common base " + c("suite.py")
      + " gives them one language: " + c("--scatola") + ", " + c("--browser") + " (one only), " + c("--guasto")
      + " (after the healthy pass, the pass with the injected fault in the same session), "
      + c("--certifica") + ", " + c("--evidenze") + ", " + c("--porte-base") + "; 4K by default. Each judged "
      "function prints one " + c("SUITE {…}") + " line; the exit code is 0 all PASS, 1 a FAIL or a fault not "
      "seen, 3 a BLOCKED and no FAIL.") + \
    p("Groups G7 and G8 start a <b>second server</b> per box, on ports 8611–8614 and 8621–8624, with "
      "shortened clocks or with their own ban file, socket and log, so that a ban test never bans the "
      "machine for the others. The dead line is simulated on the server with a private nftables table that "
      "drops the UDP of the test's port only.") + \
    p(c("15-giro.py") + " runs a round on the server: it finds the " + c("15-f*.py") + " and " + c("15-n*.py")
      + " (negative) tests, runs the four desktops in parallel (one queue each, Firefox then Chrome, distinct debugging "
      "ports), kills any test after 10 minutes as BLOCKED, refuses to start if a person (anyone who is not a "
      "bench tenant) has a session in a box, and with " + c("--strato-tecnico") + " (technical layer) adds C7, C9, C18, C19 per box "
      "and C14 at the end. Each desktop has its own headless labwc at 3840×2160 (" + c("15-compositori.sh")
      + "): in a shared compositor Chrome windows covered each other, and a covered Chrome window does not "
      "repaint — one screenshot hung for 17 minutes.") + \
    table(["Field", "Example"], [
        [c("giro") + " (round) · " + c("passata") + " (pass)", c("1") + ", " + c("2") + ", " + c("bonifica") + " (clean-up) · " + c("sana") + " (healthy) or " + c("guasto") + " (faulted)"],
        [c("test") + " / " + c("funzione") + " (function)", c("T-018-kde-firefox") + " / " + c("F-018")],
        [c("desktop") + " · " + c("browser") + " · " + c("versione"), c("kde") + " · " + c("firefox") + " · " + c("140.16.0")],
        [c("binario") + " (binary) · " + c("pagina") + " (page) · " + c("commit"), "md5 prefixes of binary and page, the commit"],
        [c("esito") + " (outcome) · " + c("ragione") + " (reason)", "PASS, FAIL or BLOCKED; one sentence, mandatory for FAIL and BLOCKED"],
        [c("atteso") + " (expected) · " + c("osservato") + " (observed)", "the two sentences of the test case"],
        [c("guasto_visto") + " (fault seen)", "true or false on the faulted pass"],
        [c("evidenze") + " (evidence) · " + c("difetto") + " (defect)", "paths of photos, logs and console; " + c("D-007") + " if a defect was opened or touched"],
    ], "«TAB» — One line of the suite register (" + c("banchi/15-suite/registro.jsonl") + ", append-only)") + \
    p("Defects go to " + c("difetti.jsonl") + " (the defect list) with a class — <b>A</b> true regression, <b>B</b> one desktop's "
      "assumption in common code, <b>C</b> bench defect, <b>D</b> wrong invariant (never as a shortcut) — a "
      "state, the measured cause, the commit of the cure and the test that guards it from then on. The report "
      "(" + c("15-rapporto.py") + ", " + c("--testo") + " or " + c("--html") + ") is generated from the register, "
      "never written by hand: the function × desktop × browser matrix with the last verdict, the defects, and for "
      "every FAIL or BLOCKED the reason and its evidence.") + \
    table(["Round", "Executions", "Result"], [
        ["round 1, 25 Sep 2026", "609 (305 healthy, 304 faulted)", "42 FAIL and 7 BLOCKED on the healthy pass, "
         "no injected fault escaped; 14 defects (8 of the product, 3 of the bench, 3 to investigate), 21 entries by the "
         "end of the clean-up (14 of the product, 7 of the bench)"],
        ["round 2, 25 Sep 2026 (frozen at " + c("d121715") + ")", "657 (329 healthy, 328 faulted), technical layer included",
         "<b>329 PASS out of 329, 328 faults seen out of 328</b> — the gate of phase 15 passed"],
    ], "«TAB» — The two rounds of phase 15 (test machine, 4 desktops, Firefox 140 and Chrome 154, 3840×2160)") + \
    p("The bench entries were each a green or a red that was not the product's: a "
      "pixel judge tried only on the most colourful wallpaper (XFCE's is black), C9 not knowing the new "
      + c("forma") + " log area, cleanup not done between meshes, an empty log slice read as «not read», a "
      "shortened clock shorter than XFCE's 4K start, fixed pauses synchronised with the animation they were "
      "watching. The product cures of the clean-up — session «resumed» reported correctly, the page saying "
      "that the line dropped, the abandonment clock starting at birth, KDE starting empty, the keyboard layout "
      "reaching KWin, our own Opus decoder in WebAssembly, user settings left untouched — are described in the "
      "chapters of the parts they changed.")

# ── 16.9 ─────────────────────────────────────────────────────────────────────
S9 = p("Real browsers are driven without WebDriver servers: Firefox through <b>Marionette</b>, the protocol "
       "Firefox speaks by itself, and Chrome through the <b>DevTools protocol</b> (CDP). The drivers live in "
       + c("12-client-veri.py") + " and are imported, never copied, by the suite, the stress actors and "
       "the phone bench.", lead=True) + \
    p(c("07-b46-marionette.py") + " is a minimal Marionette client: frames are " + c("length:json") + ", commands "
      "are " + c("[0, id, command, parameters]") + ", answers " + c("[1, id, error, result]") + ". The bench uses "
      + c("WebDriver:NewSession") + " with " + c("acceptInsecureCerts") + ", " + c("WebDriver:Navigate") + ", "
      + c("WebDriver:ExecuteScript") + " and its async form, " + c("WebDriver:SetWindowRect") + " and "
      + c("WebDriver:TakeScreenshot") + " with an element id (Marionette has no element-screenshot command). "
      "Chrome is photographed with " + c("Page.captureScreenshot") + ".") + \
    table(["Point", "What is checked", "Read from"], [
        ["a", "the page opens (certificate accepted) and the login form is there", "the DOM"],
        ["b", "with user and password the page is admitted", c("REMOTIX.schermo.sessione") + " and " + c("#esito")],
        ["c", "first frame: canvas pixels not degenerate within the ceiling", "a photograph of the canvas"],
        ["d", "continuity: frames keep arriving with a declared scene", c("REMOTIX.schermo.conti.dipinti")],
        ["e", "input: a key and a move+click reach the server", "a wrapper around " + c("window.REMOTIX_INPUT")
         + ", the server log, or " + c("REMOTIX.giro") + " (a frame that carries back input id N proves all inputs up to N were applied)"],
        ["f", "JavaScript and network errors, and the page's own «⛔» lines", "console and " + c("#registro")],
        ["g", "reconnection: reload, log in again, first frame again", "as a–c"],
    ], "«TAB» — The seven checks of " + c("12-client-veri.py")) + \
    p("Pixels are read from a <b>photograph</b> taken by the browser, never with " + c("getImageData")
      + ": the canvas may be " + c("bitmaprenderer") + " or transferred to a worker, and reading it from the document "
      "sees nothing — or, worse, the backing store instead of the screen (" + c("LEZIONI.md") + " §1.16). "
      "Headless runs are declared as such: without a GPU, decoding and painting are in software, so they judge "
      "behaviour, not numbers. Default ports: Marionette 2851, Chrome DevTools 9341, Android DevTools 9342 "
      "(through " + c("adb forward") + "); " + c("--porte-base") + " moves them so that four desktops can run "
      "in parallel. The certification proves that a port with no server is red, that a wrong password is red "
      "<i>by refusal</i> (consuming one login attempt, which counts for the ban), and that a black canvas is "
      "degenerate while a gradient is not.") + \
    warn("the stress actors originally stamped the time of keys typed in Firefox from the return of the "
         "Marionette action chain; a chain held back placed keys after their own echo, and «longest freeze» took "
         "the next caret blink (~1.1 s). Since phase 20 the page itself stamps gestures with a capturing "
         + c("keydown") + "/" + c("pointerdown") + "/" + c("wheel") + " probe, and " + c("16-riclassifica.py")
         + " recomputes past levels from the page's own round-trip data.", "Marionette time is not page time.")

# ── 16.10 ────────────────────────────────────────────────────────────────────
RAMP = flow([("Prepare", "clean box, ceiling 17", "dark"), ("Climb", "1 → 4 → 8 → 12 → 16", "blue"),
             ("Work", "10 min, cumulative", "blue"), ("Check", "last 2 min", "navy"),
             ("Classify", "GREEN · DEGRADED · FAIL", "green")],
            "«FIG» — One climb of the stress campaign (the last step lasts 30 minutes)")

S10 = p("Phase 16 asks how much load REMOTIX carries while still working. Clients run <b>on the server "
        "itself</b> — the tablet's graphics and Wi-Fi would be the bottleneck — so every result is a lower bound: "
        "«N users on this server, which meanwhile also runs the N browsers».", lead=True) + RAMP + \
    p("Each user is an independent <b>actor</b> (" + c("16-attore.py") + "): its own process, browser, labwc "
      "compositor and clock, no conductor. Odd users drive Firefox, even users Chrome; tenants are "
      + c("c16<NNN>u<N>") + ", created and always removed by the actor, with exactly one login "
      "attempt so that a ban is impossible. Actors are programs, not AI agents: an agent would set the rhythm "
      "of input by its own thinking time and never repeat itself, while a seed per user makes every climb "
      "different inside and identical across campaigns. The four workloads (" + c("16-lavori.py") + ") are "
      "fixed by the user number.") + \
    table(["Users", "Profile", "What it does, in a loop"], [
        ["1, 5, 9, 13", "A browsing", "Firefox ESR in kiosk mode inside the session, on four local pages that log their "
         "loads, scrolls and clicks; the check is that log"],
        ["2, 6, 10, 14", "B file manager", "creates and deletes folders in " + c("~/prova16") + ", opens and closes windows"],
        ["3, 7, 11, 15", "C terminal", c("ls") + ", " + c("find") + ", " + c("top") + ", a scrolling file — typed on the browser's keyboard"],
        ["4, 8, 12, 16", "D video", "a 4K video full screen for the whole climb (a fixed local file if the online source changes)"],
    ], "«TAB» — The four workloads") + \
    table(["Measure (per session)", "GREEN", "DEGRADED", "FAIL"], [
        ["input → frame delay, product side, p95", "≤ 50 ms", "50–150 ms", "> 150 ms, or input lost"],
        ["frames skipped by the page", "≤ 2 %", "2–10 %", "> 10 %"],
        ["longest freeze with work going on", "≤ 1 s", "1–3 s", "> 3 s, or image stopped"],
        ["holes in the video chain (key requests)", "0", "≤ 1 per minute", "> 1 per minute"],
        ["video users: frames painted per second, f = video rate", "≥ 0.8·f", "0.4·f – 0.8·f", "< 0.4·f"],
        ["video users: audible sound", "≥ 99 %", "95–99 %", "< 95 %"],
        ["birth of a new user (login → first frame)", "≤ 5 s", "5–15 s", "> 15 s, or refused"],
        ["short functional check", "all PASS", "—", "one FAIL"],
        ["dropped session, restart, RCP/QUIC error that detaches", "none", "—", "any"],
        ["memory growth of the " + c("remotix") + " and " + c("sessioni") + " (sessions) process sets", "≤ 5 %", "5–15 %", "> 15 % and growing"],
    ], "«TAB» — The thresholds, approved by the user on 25 Sep 2026 and frozen (" + c("SOGLIE") + " in " + c("16-classifica.py") + ")") + \
    p("A level is GREEN if every session is GREEN, FAIL if one is FAIL; «significant DEGRADED» (more than a "
      "quarter of sessions, or one measure past the middle of its band) stops the climb for diagnosis and a "
      "repetition under the same conditions. A FAIL starts a bisection between the last good step and the "
      "broken one, precise to one user. If 4K fails the whole climb is redone at 3K (3200×1800), then 2K, then "
      "Full HD. The delay that classifies is the product's own share: the p95, over the judging window, of the "
      "per-second p95 values the child writes for its own work (copy → bytes out, frames of that second only), "
      "plus 9 ms, the constructive ceiling of the input leg (the child's 8 ms poll); the child's «capture → bytes "
      "out» lines and the page's round trip are recorded, the latter as the experienced delay, but do not classify.") + \
    p("Resources are sampled once a second by " + c("16-risorse.py") + " (as root, or it declares what it could "
      "not read) for three process sets — " + c("remotix") + ", " + c("sessioni") + ", " + c("browser") + " — with "
      "PSS memory and per-process GPU engine use from " + c("/proc/<pid>/fdinfo") + ". A high resource "
      "alone is never a FAIL: classification comes from behaviour, and resources explain it. At every level "
      + c("16-controllo-corto.py") + " opens one extra session (the 17th at the top step, hence a session ceiling "
      "of 17 during the campaign) and runs reduced F-004, F-007, F-003 and F-014.") + \
    p("Campaigns run unattended overnight as a queue (" + c("16-coda.sh") + " the queue, " + c("16-campagna.sh") + " one campaign) "
      "inside a " + c("systemd-run") + " unit with three settings that are not optional: "
      + c("OOMPolicy=continue") + " (a browser killed for memory is a red step to measure, not the end of the night), "
      + c("TimeoutStopSec=1200") + " and " + c("KillMode=mixed") + " (the queue alone receives the stop and lets "
      "the climb clean up). After the machine froze with RAM exhausted at 16 users on 28 Sep 2026, "
      + c("earlyoom") + " was added to the test machine's recipe, preferring browsers as victims. Results are "
      "generated by " + c("16-rapporto.py") + " — the final desktop × card matrix, the curves, the bottlenecks.") + \
    p("For the comparison with xrdp (phase 20) the bench has a twin: " + c("16-attore-rdp.py") + " drives "
      "the same four workloads with the same seeds through " + c("xfreerdp3") + " in a private Xvfb per user ("
      + c("16-compositori-rdp.sh") + "), with XTEST for input and XDamage for paint times, against the "
      + c("-xrdp") + " boxes, so that " + c("16-classifica.py") + " reads both with the same thresholds. "
      + c("14-stress/") + " is the earlier, tablet-driven night harness of phase 14; its client that never stays "
      "still (removed on 10 Oct 2026 with the other benches of closed phases) found that a server heartbeat was postponed by every "
      "input message, freezing the screen for minutes under a moving mouse.")

# ── 16.11 ────────────────────────────────────────────────────────────────────
S11 = p("Phase 17 tests REMOTIX where an administrator would install it: on the official images of each "
        "distribution, in virtual machines with real kernels, SELinux, firewalls and boots — and, since VMs have "
        "no graphics card, in boxes for everything that needs the encoder.", lead=True) + \
    table(["Piece", "What it is"], [
        [c("17-vm.sh"), "QEMU directly, no libvirt, no root; user-mode network with port forwarding; the disk is an "
         "overlay on the untouched official cloud image. Machines are " + c("<distro>-<desktop>") + "; ssh on "
         + c("2300 + 10·N + k") + ", REMOTIX on " + c("7500 + 10·N + k") + " (k: bare 0, gnome 1, kde 2, xfce 3, lxqt 4). "
         "Verbs: " + c("crea") + " (create), " + c("avvia") + " (start), " + c("vesti") + " (dress: installs the desktop group), " + c("ssh") + ", "
         + c("ferma") + " (stop), " + c("riavvia") + " (a real reboot, checked through " + c("boot_id") + "), "
         + c("fotografa") + "/" + c("torna") + " (snapshot/restore), " + c("azzera") + " (reset to the base image)"],
        ["states", "<b>BASE</b> the cloud image after cloud-init · <b>DESKTOP</b> plus the distribution's official desktop "
         "group (snapshot " + c("cliente") + ", customer) · <b>ISO</b> installed from the official ISO with its automatic installer "
         "(answers in " + c("iso-risposte/") + ", differences from DESKTOP in " + c("iso-differenze.md") + "). If a verdict differs "
         "between DESKTOP and ISO, ISO is the truth"],
        [c("17-t10.sh"), "the script of one machine: back to the snapshot, fingerprints of " + c("/etc") + ", " + c("/usr")
         + ", groups, units and firewall; install from the release's single " + c(".run") + " file; a real browser logs in and "
         "sees the desktop; real reboot and login again; update to REMOTIX release N+1 (the next " + c(".run") + ") with a "
         "browser attached and the desktop alive; uninstall with purge and compare fingerprints"],
        [c("17-t10-giro.sh"), "the same over many machines, four at a time"],
        [c("17-amministratore.sh"), "plays the administrator before installing (third-party repositories, drivers with "
         "H.264): since 10 Oct 2026 REMOTIX does not modify the system and " + c("check") + " says what is missing"],
        [c("17-carico.sh"), "how many VMs fit together: 8 did not (memory), 4 was kept"],
        [c("scatole/17-scatola.sh"), "a matrix machine as a box with the server's card and the same verbs; one recipe "
         "per distribution with the desktop as argument; ssh on " + c("8600+10n+k") + ", REMOTIX on " + c("8800+10n+k")
         + " (+100 on the Radeon); up to four together"],
    ], "«TAB» — The distribution bench") + \
    p("On 30 Sep – 1 Oct 2026 the full T10 round passed on <b>32 machines out of 32</b> (26 desktop images and 6 "
      "ISO installs), the two KDE combinations whose KWin produces no screencast without 3D in a VM being run "
      "in boxes with the real card. The requirements behind it are numbered R1–R43 in phase 17 §8: the check "
      "touches nothing (fingerprints of " + c("/etc") + " before and after, also in " + c("prove/r1-contenitori.sh")
      + "), every known fault is reported with its stable code, uninstalling undoes everything REMOTIX did and "
      "nothing else (a user already in " + c("video") + " stays there), an update with users connected closes no "
      "desktop, SELinux enforcing logs no denial, PAM behaves as sshd on every family, bench markers are absent "
      "from the package, an interrupted installation resumes.") + \
    note("since phase 19 the installer refuses a machine without a card that encodes, so the daily round must move "
         "to the boxes. On 10 Oct 2026 the box recipes for the 26 combinations (one per distribution, with the desktop "
         "as argument) were written but none had been built yet (they are built on the test machine, after the xrdp "
         "campaign). Not settled yet: the first full round in boxes.",
         "Boxes for all combinations.") + \
    p(c("17-t2/") + " measured what kills desktops when the service stops (nothing does, 29 Sep 2026); "
      + c("17-t6/") + " PAM, SELinux and firewall per family; " + c("17-t7/") + " updating without closing "
      "desktops on the four boxes. " + c("17-t4-motore.sh") + ", " + c("17-t8/") + " and " + c("17-t9/")
      + " test an installer that no longer exists (separate plan and apply, signed archive, answer files) and are "
      "kept as history; their headers say so and they are not run — except " + c("t8-browser.py") + ", the browser "
      "that stays attached during the update, which " + c("17-t10.sh") + " still uses.")

# ── 16.12 ────────────────────────────────────────────────────────────────────
S12 = p("When an encoder path changes, the old path stays alive as a term of comparison until the new one has "
        "been measured against it on the same frames.", lead=True) + \
    table(["Folder", "Compares", "How it judges"], [
        [c("18-a1/"), "the old " + c("audio.c") + " (through libavcodec, copied verbatim from the starting commit) and the new one (libopus directly)",
         "same input, both outputs, plus decoding in Chrome"],
        [c("18-scheda/"), "the old VA-API path through libavcodec and the new direct libva path (" + c("vadiretta.c") + ")",
         "streams, logs and " + c("esiti.jsonl") + " per test, a table (" + c("18-tabella.py") + "), Chrome decoding"],
        [c("18-software/"), "the old software fallback against OpenH264 and SVT-AV1 called directly",
         "colours, encoding, events, refusals on the same desktop scene"],
        [c("19-vulkan/"), "Vulkan Video (" + c("vulkanvideo.c") + ") against VA-API on the same card, and the integrated "
         "engine that chooses by capability", c("ffmpeg") + "/" + c("ffprobe") + " only as measuring tools (PSNR, SSIM, "
         "profile, level), plus a Chrome decoding test"],
        [c("19-nvidia/"), "REMOTIX on a rented NVIDIA machine", "one command prepares a bundle on the laptop; on the rental "
         "day it upgrades the OS if needed, installs the driver, XFCE, browsers and REMOTIX with its installer, proves "
         "H.264 and HEVC on the card, runs the encoder comparison and part of the suite, brings evidence home, then cleans up"],
        [c("19-android/"), "ten suite tests on the user's own phone with Chrome, through adb",
         "the same judges as the suite; never during a phone call; the phone is put back as it was"],
    ], "«TAB» — Encoder and platform benches") + \
    p("Three small folders complete the picture. " + c("rcp/") + " holds the twin of the RCP module that phase 1 "
      "grafted into ngtcp2's example server; the build of the product refuses to compile if the two copies "
      "differ, and " + c("GEMELLO=nessuno") + " (twin = none) must be declared to build without the comparison. "
      + c("prodotto/") + " has the smoke test of the server inside the build container (" + c("fumo.sh") + ", smoke) and "
      "its pages; " + c("sonda/") + " a real-browser probe that collects what the page saw.")

# ── 16.13 ────────────────────────────────────────────────────────────────────
S13 = p("Benches are written and compiled on the laptop; they run on the test machine, where the card, the "
        "boxes and the browsers are. The test machine's root filesystem lives in RAM: after a reboot the "
        "recipe in the project notes restores packages, keys and boxes, and everything persistent sits under "
        + c("/media/REMOTIX") + ".", lead=True) + \
    table(["Path on the test machine", "Contents"], [
        [c("/media/REMOTIX/rete11"), "the safety-net tree, the box images' context, the remote half of the hook"],
        [c("/media/REMOTIX/src/controllo"), "the benches copied by " + c("15-porta.sh") + " (carry over) for the suite and the real-browser meshes"],
        [c("/media/REMOTIX/misure/fase15"), "the suite register and per-round evidence"],
        [c("/media/REMOTIX/misure/fase16"), "the stress campaigns, one folder per climb and level"],
        [c("/media/REMOTIX/vm17"), "the distribution VMs"],
    ], "«TAB» — Where benches live on the test machine") + \
    term("""
# from the laptop: the safety net, decided here and run there
$ bash banchi/11-scatole/11-gancio.sh remoto
# from the laptop: copy the suite to the server
$ bash banchi/15-suite/15-porta.sh
# on the server, as the bench user: rebuild the boxes (only when nobody is testing by hand)
$ bash /media/REMOTIX/src/controllo/banchi/15-suite/15-rifai-scatole.sh
$ python3 /media/REMOTIX/src/controllo/banchi/15-suite/15-giro.py --elenco
$ python3 /media/REMOTIX/src/controllo/banchi/15-suite/15-giro.py --giro 3 --strato-tecnico
# one test, with real browsers
$ bash banchi/15-suite/15-una.sh --remoto 15-f001-accesso-e-prima-immagine.py --scatola gnome --browser firefox --guasto
# the report, generated from the register
$ python3 banchi/15-suite/15-rapporto.py --registro banchi/15-suite/registro.jsonl --difetti banchi/15-suite/difetti.jsonl --giro 2 --testo
# a stress climb, without doing anything (the plan)
$ python3 16-salita.py --scatola gnome --campagna prova-4k-gnome --misura 4k --secco
""", "Typical commands") + \
    warn("rebuilding boxes kills every session inside them, including a person's. The suite refuses to start if "
         "anyone who is not a bench tenant is logged in; rebuilding needs the user's go-ahead. And never restart "
         "the product server while the user is measuring by hand.", "The boxes are also where people test.") + \
    ul([
        "Build first, then run: a bench run against a stale binary or page measures the wrong thing; the register "
        "records binary and page md5 for this reason.",
        "Look at the scene before calling anyone to judge it: a counter is not looking.",
        "Close your own manual test users before starting a full round: the net reads the whole log, including "
        "lines that are not its own (C9 once went red on a leftover session, class C).",
        "Measurements are not run in parallel on the same hardware; development and reading are. A bench must "
        "refuse to measure if the machine is not idle, rather than declare the load in a note nobody reads.",
    ])

CHAPTER = ("Testing", [
    ("How REMOTIX is tested", S1),
    ("The bench folder", S2),
    ("Rules every bench follows", S3),
    ("The boxes of the safety net", S4),
    ("The meshes C1 to C24", S5),
    ("When the net runs: the hook", S6),
    ("What the net does not catch", S7),
    ("The functional suite", S8),
    ("Driving real browsers", S9),
    ("Stress and capacity benches", S10),
    ("The distribution bench", S11),
    ("Encoder and platform benches", S12),
    ("Running the benches", S13),
])
