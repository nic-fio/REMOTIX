import re

from build import ROOT, c, file_map, p, rif, sorgenti, table

S = "src/"
M = "installer/engine/"


def manuale():
    """The manual's sources: the generator, the style, the script and one file per chapter, with its title."""
    righe = [
        ("docs/sources/build.py", "Generates the manual: text, table and SVG figure helpers, numbering, the "
         "file map and project figures, and the " + c("--check") + " checks (Italian left, cited files, "
         "functions, variables and codes)"),
        ("docs/sources/manual.js", "The script embedded in the page: sidebar, search, figure zoom"),
        ("docs/sources/style.css", "The common style sheet every manual page starts with"),
    ]
    capitoli = sorted(f for f in sorgenti() if f.startswith("docs/sources/") and f.endswith(".py")
                      and f != "docs/sources/build.py")
    for f in capitoli:
        m = re.search(r'^CHAPTER = \("([^"]+)"', (ROOT / f).read_text(), re.M)
        n = re.match(r"ch(\d\d)_", f.rsplit("/", 1)[-1])
        titolo = m.group(1) if m else "chapter source"
        righe.append((f, (f"Chapter {int(n.group(1))}: " if n else "") + titolo))
    return righe


GRUPPI = [
    ("Server core: processes, sessions, authentication", [
        (S + "main.c", "The server: options, the single " + c("poll") + " loop, the two listeners, the bridge "
         "between transport and children, the presence table and abandonment clock, found-again desktops"),
        (S + "child.c", "One process per user that runs as that user and holds the stage: fork then exec, "
         "logind session, desktop start, capture, encoding and input inside it"),
        (S + "child.h", "Why the child exists (root cannot join the user's session bus), its invariants and the "
         "parent–child messages"),
                (S + "rootside.h", "1.5 privilege separation (§11.50): the root side (PAM, desktop birth) and the network side's handle on it; one binary, one channel"),
        (S + "rootside.c", "The root side built against a hijacked network side: credentials and exact length on every packet, bounds on logins and births, the network side restarted if it breaks the rules"),
        (S + "rootside_proto.h", "The closed list of messages between the two sides (AUTH, SPAWN, CLOSE_ORPHAN, SIGNAL and the events): fixed sizes, magic and version"),
        (S + "walls.h", "The network side's walls, in plain words: private read-only mount namespace, no privileges, seccomp, SELinux domain"),
        (S + "walls.c", "Applies the walls in the fork, in the order that matters, and refuses to start the network side if one fails"),
        (S + "hsrate.h", "The rate of new QUIC handshakes (per address, per network, in all), apart from the caps on pending ones (audit R4)"),
        (S + "pagebucket.h", "The accept buckets of the page listener, apart so that a unit test can try them alone"),
        (S + "linebudget.h", "A budget of log lines per time window for the whole process: the first lines are written, the rest counted in one line at the end (audit R8, R12)"),
        (S + "lookup.h", "The CID map and the ring of used Retry tokens of the transport, hashed instead of scanned for every packet"),
        (S + "sigchld.h", "When the main loop reaps its children: on SIGCHLD (a flag set by a handler) plus a safety scan every second, not a waitpid per child per round"),
        (S + "render_grant.h", "The card for a user manager started before the card groups, without closing the user's sessions (§11.4), with the measurements"),
        (S + "render_grant.c", "Gives and takes back the ACL on the render nodes, with its record file; runs in the parent as root"),
        (S + "helper.c", "The PAM helper process: verifies passwords off the single thread"),
        (S + "helper.h", "Why the helper exists (PAM blocks 1–2 s per attempt), its three layers and invariant I3"),
        (S + "authentication.c", "PAM conversation and the guard that starts from “denied”; no comparison with "
         "the process user"),
        (S + "session.c", "Starts the headless graphical session with its virtual monitor, on GNOME, KDE, "
         "XFCE and LXQt; the session log in the user's home"),
        (S + "session.h", "The graphical session contract: born by REMOTIX, born with a monitor, and why it is "
         "not v1's copy"),
        (S + "sentinel.c", "Watches local graphical sessions through logind and emits the two local-session "
         "reasons"),
        (S + "sentinel.h", "Who watches local sessions and on whose behalf (SPECIFICHE §5.1)"),
        (S + "rediscover.c", "Finds live REMOTIX desktops that no child holds, after a service restart"),
        (S + "rediscover.h", "Why found-again desktops exist (stopping the service does not kill desktops) and the "
         "criterion that recognises them"),
        (S + "budget.c", "The composition budget mechanism: per-user accounts, admission, degradation"),
        (S + "budget.h", "The reason behind every number of the budget (phase 10) and its interface"),
        (S + "log.c", "Writes log lines: instant, area, level, one place for all output"),
        (S + "log.h", "The log contract: why a module and not " + c("printf") + ", areas and levels"),
        (S + "command.c", "The unlock command: a Unix control socket that lifts a ban and logs it"),
        (S + "command.h", "Why unlocking is a socket and not a command-line option (RCP §4.4-bis)"),
    ]),
    ("Capture and desktop backends", [
        (S + "capture.c", "Reads frames from the PipeWire node the compositor opened (GNOME, KDE), with the "
         "declared buffer type"),
        (S + "capture.h", "The capture mandate: a frame delivered in memory with its declared, not inferred, "
         "buffer type"),
        (S + "mutter.c", "The D-Bus sequence that opens a virtual monitor and its stream on Mutter"),
        (S + "mutter.h", "The mandatory Mutter sequence and the penalty attached to each step"),
        (S + "kwin.c", "The stage on KDE Plasma: " + c("zkde_screencast_unstable_v1") + " on the virtual output, "
         "and the EIS input channel"),
                (S + "unchanged.h", "Recognises a KWin frame that changes nothing from its damage, so it is not encoded (KDE delivers ~50 buffers a second, ~90 % identical)"),
        (S + "kwin.h", "What was carried over from v1 for KWin: capture protocol and input channel"),
        (S + "wlroots.c", "Capture on labwc (XFCE, LXQt) with screencopy: from the card via dmabuf, from "
         "memory as a declared fallback"),
        (S + "wlroots.h", "Why wlroots is the other direction: frames are pulled, not pushed, and there is no "
         "PipeWire node"),
        (S + "cursor.c", "From PipeWire's cursor metadata to the cursor-shape message"),
        (S + "cursor.h", "The cursor-shape seam, from PipeWire to the wire"),
        (S + "shape.c", "The encoded cursor theme and its dictionary, shared by server and child"),
        (S + "shape.h", "How the real pointer shape reaches the browser where the compositor does not send it"),
        (S + "remotix-power-keys.conf", "Second power belt: logind ignores the power, reboot, suspend and hibernate keys and the lid"),
        (S + "remotix-no-poweroff.rules", "The polkit rule, installed active by the packages: ordinary users cannot power off, "
         "restart or suspend the machine (DECISIONS §10.50)"),
    ]),
    ("Encoding", [
        (S + "encoder.c", "From the captured frame to the stream: picks the hardware path, keyframes, "
         "reads back what the encoder really produced"),
        (S + "encoder.h", "What the encoder is and is not; the contract with capture and transport"),
        (S + "vadirect.c", "H.264 and HEVC on the card with libva used directly: levels, headers bit by bit, "
         "per-frame encode"),
                (S + "render_node.h", "Which card encodes: the one the compositor draws on (linux-dmabuf main_device), not the first one the kernel numbered"),
        (S + "render_node.c", "From the compositor's device number to the render node through sysfs, no libdrm"),
        (S + "vadirect.h", "Why libva is used without libavcodec (ffmpeg left the product, phase 18)"),
        (S + "vulkanvideo.c", "H.264 and HEVC with Vulkan Video: device, profiles, session, parameters, "
         "per-frame encode"),
        (S + "vulkanvideo.h", "Why Vulkan Video (phase 19) and its rules"),
        (S + "vulkanvideo_rgb_nv12.comp", "Compute shader RGB → NV12/P010, BT.709 limited range, bit-identical to "
         + c("colors709.c")),
        (S + "vulkanvideo_rgb_nv12_spv.h", "The compiled SPIR-V of the shader (generated, not edited by hand)"),
        (S + "colors709.c", "BGRx → YUV 4:2:0 BT.709 limited conversion without libswscale"),
        (S + "colors709.h", "Why the conversion is ours (phase 18) and its coefficients"),
        (S + "bit_writer.c", "Bit writer: Exp-Golomb, trailing bits, emulation prevention"),
        (S + "bit_writer.h", "Writing H.264/H.265 parameter sets field by field, as packed headers"),
    ]),
    ("Transport and protocol", [
        (S + "transport.c", "The UDP listener: QUIC with ngtcp2, connections, timers, datagrams"),
        (S + "transport.h", "The first of the two listeners on the same port (RCP §2.4)"),
        (S + "webtransport.c", "The WebTransport layer over HTTP/3 (nghttp3): extended CONNECT, streams, "
         "datagrams, and RCP on top"),
                (S + "pktinfo.h", "The source address of a reply: the control message that makes a reply leave from the address the client wrote to (a socket bound to the wildcard otherwise lets the kernel choose)"),
        (S + "webtransport.h", "Why the WebTransport layer is ours: neither library carries it server side"),
        (S + "rcp.c", "The RCP/1 state machine, server side: handshake, ban, farewell, every rule with its "
         "paragraph number"),
        (S + "rcp.h", "RCP messages, reasons, limits; knows RCP.md and nothing else"),
        (S + "page.c", "The TCP listener: serves the page over HTTPS with the certificate fingerprint written in"),
        (S + "page.h", "The second listener, same port number, HTTP/1.1 only for the page"),
        (S + "tls.c", "The two TLS contexts, one per listener"),
        (S + "tls.h", "Why two contexts: two certificates (RCP §4.1-bis)"),
        (S + "certificates.c", "Generates, rotates and loads the long-lived and session certificates"),
        (S + "certificates.h", "The two certificates and what confusing them costs"),
    ]),
    ("Input", [
        (S + "input.c", "Input reaches the desktop through libei (GNOME, KDE): pointer, buttons, wheel, keys"),
        (S + "input.h", "The input seam, from the wire to the desktop"),
        (S + "wlr_input.c", "Virtual keyboard and pointer on labwc, with the five silent traps marked"),
        (S + "wlr_input.h", "Input transport on wlroots, where libei does not exist"),
        (S + "keyboard.c", "From a character to the key positions that produce it on the session's layout"),
        (S + "keyboard.h", "The keyboard seam: characters on the wire, positions to the compositor"),
    ]),
    ("Audio and clipboard", [
        (S + "audio.c", "The Opus encoder"),
        (S + "audio.h", "The fixed audio format (RCP §5.3): Opus with PCM as the basis"),
        (S + "sound.c", "The virtual sink and the capture of its monitor on PipeWire"),
        (S + "sound.h", "The session's sound: why the sink must be created, session vs connection"),
        (S + "clipboard.c", "The clipboard on Mutter, through the RemoteDesktop session"),
        (S + "clipboard.h", "The clipboard seam, from desktop to wire and back"),
        (S + "clipboard_kde.c", "The clipboard on KDE and labwc through the Wayland data-control protocol"),
        (S + "clipboard_kde.h", "Data-control clipboard behind the same interface as " + c("clipboard.h")),
    ]),
    ("The page", [
        (S + "page.html", "The whole browser client: login, WebTransport, RCP, WebCodecs video, Opus audio, "
         "input, clipboard, canvas and view"),
        (S + "opus-wasm/build.sh", "Builds the Opus WebAssembly decoder and embeds it in the page"),
        (S + "opus-wasm/decoder.c", "The decoder compiled to WebAssembly: libopus, decode only, static buffers"),
        (S + "opus-wasm/opus.wasm.sha256", "Fingerprint of the embedded decoder"),
        (S + "opus-wasm/test/compare.mjs", "Decodes test packets with the wasm extracted from the page"),
        (S + "opus-wasm/test/test.sh", "Compares the embedded decoder with native libopus"),
        (S + "opus-wasm/test/reference.c", "Native reference: encodes test signals in the three Opus modes"),
    ]),
    ("Wayland protocols", [
        (S + "protocols/ext-data-control-v1.xml", "Standard clipboard access protocol"),
        (S + "protocols/linux-dmabuf-unstable-v1.xml", "Buffers shared with the card (wlroots capture)"),
        (S + "protocols/virtual-keyboard-unstable-v1.xml", "Virtual keyboard (labwc input)"),
        (S + "protocols/wlr-data-control-unstable-v1.xml", "wlroots clipboard access (KDE and labwc)"),
        (S + "protocols/wlr-output-management-unstable-v1.xml", "Output size on labwc"),
        (S + "protocols/wlr-screencopy-unstable-v1.xml", "Screen capture on labwc"),
        (S + "protocols/wlr-virtual-pointer-unstable-v1.xml", "Virtual pointer (labwc input)"),
        (S + "protocols/wlr-layer-shell-unstable-v1.xml", "Layer surfaces: the nested KWin's «ticker», one transparent pixel on the labwc that hosts it (kwin.c)"),
        (S + "protocols/xdg-shell.xml", "The base protocol layer-shell names (xdg_popup)"),
        (S + "protocols/zkde-screencast-unstable-v1.xml", "KWin screen streams as PipeWire nodes"),
    ]),
    ("System files and server build", [
        (S + "remotix.pam", "PAM service for Debian and Ubuntu"),
        (S + "remotix.pam.arch", "PAM service for Arch, without " + c("@include")),
        (S + "remotix.pam.fedora", "PAM service for Fedora and the RHEL family: the system's sshd stack, "
         "root excluded"),
        (S + "remotix.pam.suse", "PAM service for openSUSE, installed under " + c("/usr/lib/pam.d")),
        (S + "Makefile", "Builds the server: declared dependencies, the twin check, the generated protocol headers"),
        (S + "Containerfile", "The everyday build container, without sudo"),
        (S + "build-in-container.sh", "Builds the server on the laptop inside that container"),
        (S + "build.sh", "Builds the server inside the test machine's container"),
        (S + "provision.sh", "Puts the test machine in the state the product expects, and verifies it"),
        (S + "restart-7700.sh", "Restarts the test server on port 7700 with the page on disk"),
        (S + "restart-7900.sh", "Restarts the phase 9 test server on port 7900, with its own tree and unit"),
        (S + "build-targets/Containerfile.alma10", "Build container for AlmaLinux 10"),
        (S + "build-targets/Containerfile.arch", "Build container for Arch Linux"),
        (S + "build-targets/Containerfile.debian13", "Build container for Debian 13, the reference"),
        (S + "build-targets/Containerfile.fedora44", "Build container for Fedora 44"),
        (S + "build-targets/Containerfile.leap16", "Build container for openSUSE Leap 16"),
        (S + "build-targets/Containerfile.tumbleweed", "Build container for openSUSE Tumbleweed"),
        (S + "build-targets/Containerfile.ubuntu2404", "Ubuntu 24.04: only to see where it stops (OpenSSL 3.0)"),
        (S + "build-targets/Containerfile.ubuntu2604", "Build container for Ubuntu 26.04"),
        (S + "build-targets/build-deb.sh", "Builds the .deb inside the target's container"),
        (S + "build-targets/build-all.sh", "Builds REMOTIX for one, some or all targets"),
        (S + "build-targets/quic-static.sh", "Builds ngtcp2 and nghttp3 from source, static, pinned versions"),
    ]),
    ("Installer engine (" + c("installer/") + " = installer, " + c("engine/") + " = engine)", [
        ("installer/cmd/remotix-install/main.go", "The command line: " + c("check") + ", " + c("install")
         + ", " + c("uninstall") + ", " + c("status") + ", " + c("tui") + " and the commands package scripts call"),
                ("installer/cmd/remotix-install/main_test.go", "The plan states the port before the question: chosen, stock, or none on an upgrade"),
        ("installer/cmd/remotix-install/tui.go", "Starts the text interface"),
        (M + "format.go", "Package entry: object format version, engine version, fingerprints"),
        (M + "states.go", "The operation states and the only valid transitions"),
        (M + "operation.go", "The engine and an operation: lock, apply, resume, cancel, verify, certify"),
        (M + "log.go", "The write-ahead log: every line made durable before the next step"),
        (M + "events.go", "What the engine says while working, as text or one JSON line per event"),
        (M + "trust.go", "Phase 0 TRUST: the catalogue is the engine's own, and where it came from"),
        (M + "preflight.go", "Examines the machine read-only: files, D-Bus, one closed list of commands"),
        (M + "profile.go", "The machine profile and its facts, detected vs verified"),
        (M + "compatibility.go", "The catalogue format and the compatibility assessment"),
        (M + "encoding_routes.go", "The hardware encoding paths and the verdict “at least one capable card”"),
        (M + "plan.go", "The machine fingerprint that binds a plan, and the plan object"),
        (M + "install_plan.go", "The install or upgrade plan: what is missing is said, not installed"),
        (M + "questions.go", "The only question asked on this machine: the port, then yes to the plan"),
        (M + "actions.go", "Reversibility, origin and check outcome of every action"),
        (M + "actions_declared.go", "Steps the engine knows but cannot run yet (the list is empty)"),
        (M + "action_file.go", "Write a file atomically, with the old content saved for undo"),
        (M + "busy.go", "Waits while another program holds the package manager's lock"),
        (M + "action_group.go", "Add a person to the card's groups; pre-existing membership is never removed"),
        (M + "action_packages.go", "The package transaction: simulate, install, check, undo"),
        (M + "action_user_logs.go", "Remove the REMOTIX session log from every home at uninstall"),
        (M + "action_service.go", "Enable and start the service on systemd's D-Bus, done only if the port answers"),
        (M + "action_sessions.go", "Close open REMOTIX sessions at uninstall, through logind"),
        (M + "action_unit.go", "Enable a systemd unit (kept, no new plan uses it)"),
        (M + "graphical_user.go", "Stops the desktop units of a REMOTIX session in the user manager, never the "
         "whole user"),
        (M + "uninstall.go", "Uninstall: walks the confirmed installation log backwards"),
        (M + "post_upgrade.go", "After a system upgrade: records versions and re-checks certification"),
        (M + "certify.go", "Platform certification: encode test, PAM stack resolved, every step checked"),
        (M + "package_manager.go", "The distribution's package manager, launched from the closed list"),
        (M + "versions.go", "Package version comparison as dpkg and rpmvercmp do it"),
        (M + "environment.go", "The closed list of programs the engine may launch, with absolute paths"),
        (M + "dbus.go", "The system D-Bus: systemd, logind and firewalld without their command-line tools"),
        (M + "archive.go", "The single package: REMOTIX's packages per target inside the " + c(".run")),
        (M + "version_table.go", "Generates the distribution and minimum-version tables from the catalogue"),
        (M + "codes.go", "The catalogue of stable " + c("RX-") + " codes, severity and nature"),
        (M + "language.go", "English only for administrators; " + c("T()") + " looks texts up by key"),
        (M + "texts.go", "The engine's and command line's texts, in English"),
                (M + "network_side.go", "The network side's system user (§11.50): the preflight refuses a person's account, the plan and the certification check the user and net/, the uninstall removes it"),
        (M + "action_render_grants.go", "The uninstall takes the render-node ACL entries recorded by the product back out (reversible if cancelled)"),
        (M + "network_side_test.go", "The network side user: preflight, rollback, certification, one unit only, uninstall"),
        (M + "card_groups_test.go", "Only the render nodes' groups are given to the user, never the card nodes"),
        (M + "render_grants_test.go", "The uninstall removes the render grants, puts them back if cancelled, and parses the record"),
        (M + "certify_test.go", "Certification on a deliberately broken machine never says green"),
        (M + "uninstall_test.go", "Uninstall on the fake machine"),
        (M + "epoch_test.go", "RPM epochs: an installed package with an epoch is not «missing»"),
        (M + "busy_test.go", "Who holds the package manager's lock, and the wait"),
        (M + "trust_test.go", "Phase 0 TRUST: the catalogue reads, this engine understands it"),
        (M + "fakes_test.go", "A fake machine under a folder: passwd, group, systemd and firewalld as JSON"),
        (M + "fakes2_test.go", "The rest of the fake machine: package manager, unit state, logind sessions"),
        (M + "english_test.go", "Finds Italian left in any administrator-facing string or catalogue text"),
        (M + "questions_test.go", "The plan does not modify the system; exact packages before the question"),
        (M + "language_test.go", "Every code and key has its English text; every key used exists"),
        (M + "engine_test.go", "State transitions, code form, plan refused on a changed machine"),
        (M + "preflight_test.go", "Preflight on fake roots: each known defect with its code"),
        (M + "resume_test.go", "The engine killed at every point and resumed: the machine ends identical"),
        (M + "script_test.go", "The header of the single package file"),
        ("installer/catalog/catalog.go", "Embeds the catalogue in the engine"),
        ("installer/catalog/catalog.json", "The catalogue: supported combinations, minimum versions, "
         "packages, rules"),
    ]),
    ("Installer interface", [
        ("installer/ui/session.go", "The engine side of the interface: examine, plan, apply, as root"),
        ("installer/ui/view.go", "The engine's objects in plain words, for the screens"),
        ("installer/ui/texts.go", "The screens' texts, in English, from the approved mockup"),
        ("installer/ui/texts_test.go", "Every key used by the screens exists; plain words in the check"),
        ("installer/ui/tui/tui.go", "The terminal screens (Bubble Tea): fixed frame, Check › Plan › "
         "Install › Ready"),
        ("installer/ui/tui/preview.go", "Previews of every screen with sample data, for "
         + c("--preview")),
        ("installer/ui/tui/tui_test.go", "Frame width at 80 and 120 columns, no colour when asked"),
    ]),
    ("Installer build, single file and engine tests", [
        ("installer/.gitignore", "Go cache and build output stay out of git"),
        ("installer/go.mod", "The Go module and its pinned dependencies"),
        ("installer/go.sum", "Checksums of the Go dependencies"),
        ("installer/build.sh", "Builds the static engine and runs the tests in the official Go container"),
        ("installer/run.sh", "The header of the single " + c(".run") + " file: checks, extracts, hands over "
         "to the engine"),
        ("installer/tests/Containerfile.systemd", "Fedora 44 with systemd running, for D-Bus actions"),
        ("installer/tests/desktop-groups.sh", "Asks each family's package manager whether the catalogue's "
         "desktop group names exist"),
        ("installer/tests/fingerprint/main.go", "Fingerprint of a folder, independent of the engine (test R1)"),
        ("installer/tests/r1-containers.sh", "R1 in containers: the check leaves " + c("/etc") + " identical"),
        ("installer/tests/on-server.sh", "History: an engine round in a VM with commands that no longer exist"),
        ("installer/tests/systemd-round.sh", "History: an engine round in the systemd container, same reason"),
    ]),
    ("Packaging: Debian and Ubuntu", [
        ("packaging/debian/control", "Source and binary package, build and run dependencies"),
        ("packaging/debian/rules", "The .deb build, inside the target's container"),
        ("packaging/debian/copyright", "Copyright declaration of the package"),
        ("packaging/debian/source/format", "Native source format"),
        ("packaging/debian/remotix.service", "The service unit: runs as root, certificate, name"),
                ("packaging/debian/remotix-net-move", "Moves the network side's files (certificates, ban) from the 1.0 place into net/ before the restart; byte-identical in the three packagings"),
        ("packaging/debian/remotix.service.split", "The unit the split build installs (the root side is the main PID, no User=); not active by default"),
        ("packaging/debian/remotix.sysusers", "The system user of the network side, no groups, no login; the same line in the three packagings"),
        ("packaging/debian/remotix.tmpfiles.split", "The directories of the split build: root state in /var/lib/remotix, the network side's in net/"),
        ("packaging/debian/remotix.conf", "Packaged defaults; the administrator's choices go in "
         + c("/etc/remotix/remotix.conf.d/")),
        ("packaging/debian/remotix.tmpfiles", "The state and runtime directories"),
        ("packaging/debian/remotix.postinst", "After install: nothing switched on; on upgrade, try-restart"),
        ("packaging/debian/remotix.prerm", "Before removal: stops the service on remove only"),
        ("packaging/debian/remotix.postrm", "After removal: purge removes what the program created"),
        ("packaging/debian/remotix.ufw", "The ufw application profile, defined, not opened"),
        ("packaging/debian/remotix-no-suspend.conf", "Third power belt, shipped inert"),
        ("packaging/debian/remotix.lintian-overrides", "The page is the program, not documentation"),
        ("packaging/debian/org.kde.remotix.desktop", "Grants KWin's screencast interface to the binary"),
        ("packaging/debian/denied-users", "Users that may never log in: root"),
    ]),
    ("Packaging: the RPM family", [
        ("packaging/rpm/remotix.spec", "One spec for Fedora, Alma, Tumbleweed and Leap, with conditional branches"),
        ("packaging/rpm/build-rpm.sh", "Builds the .rpm in each target's container"),
        ("packaging/rpm/remotix.service", "The service unit, RPM family"),
                ("packaging/rpm/remotix-net-move", "Moves the network side's files (certificates, ban) from the 1.0 place into net/ before the restart; byte-identical in the three packagings"),
        ("packaging/rpm/remotix.service.split", "The unit the split build installs (the root side is the main PID, no User=); not active by default"),
        ("packaging/rpm/remotix.sysusers", "The system user of the network side, no groups, no login; the same line in the three packagings"),
        ("packaging/rpm/remotix.tmpfiles.split", "The directories of the split build: root state in /var/lib/remotix, the network side's in net/"),
        ("packaging/rpm/remotix.conf", "Packaged defaults"),
        ("packaging/rpm/remotix.tmpfiles", "The state and runtime directories"),
        ("packaging/rpm/remotix-firewalld.xml", "The firewalld service, defined, not opened"),
        ("packaging/rpm/remotix-no-suspend.conf", "Third power belt, shipped inert"),
        ("packaging/rpm/org.kde.remotix.desktop", "Grants KWin's screencast interface to the binary"),
        ("packaging/rpm/selinux/remotix.te", "The SELinux module: why it exists and the domain transition to the user"),
        ("packaging/rpm/selinux/remotix.fc", "SELinux file contexts"),
                ("packaging/rpm/selinux/remotix.fc.split", "File contexts of the split build, with the network side's own directories"),
        ("packaging/rpm/selinux/remotix.te.split", "The SELinux module of the split build: the remotix_net_t domain of the network side"),
        ("packaging/rpm/selinux/remotix.if", "SELinux interface"),
        ("packaging/rpm/labwc/VERSIONS", "Our labwc for RHEL / Alma 10: version, tarball, sha256 and URL, pinned"),
        ("packaging/rpm/labwc/fetch.sh", "Fetches the labwc tarball and accepts it only if both checksums match"),
        ("packaging/rpm/selinux/remotix_portcon.cil", "The port type for 7447 TCP and UDP, in CIL"),
    ]),
    ("Packaging: Arch", [
        ("packaging/arch/PKGBUILD", "The Arch package, built from the repository in the Arch container"),
        ("packaging/arch/build.sh", "Tarball of one commit, then makepkg and namcap"),
                ("packaging/arch/remotix-net-move", "Moves the network side's files (certificates, ban) from the 1.0 place into net/ before the restart; byte-identical in the three packagings"),
        ("packaging/arch/remotix.service.split", "The unit the split build installs (the root side is the main PID, no User=); not active by default"),
        ("packaging/arch/remotix.sysusers", "The system user of the network side, no groups, no login; the same line in the three packagings"),
        ("packaging/arch/remotix.tmpfiles.split", "The directories of the split build: root state in /var/lib/remotix, the network side's in net/"),
        ("packaging/arch/remotix.install", "Package scripts: nothing switched on"),
        ("packaging/arch/remotix.service", "The service unit, Arch"),
        ("packaging/arch/remotix.conf", "Packaged defaults, as in the deb and rpm"),
        ("packaging/arch/remotix.tmpfiles", "The state directory"),
        ("packaging/arch/remotix.firewalld.xml", "The firewalld service, defined, not opened"),
        ("packaging/arch/remotix-no-suspend.conf", "Third power belt, shipped inert"),
        ("packaging/arch/org.kde.remotix.desktop", "Grants KWin's screencast interface to the binary"),
        ("packaging/arch/denied-users", "Users that may never log in: root"),
    ]),
    ("Packaging: engine package and release", [
        ("packaging/release.sh", "The release command: builds everything and produces the single " + c(".run")),
        ("packaging/engine/engine-packages.sh", "Packages the static engine for the three families"),
        ("packaging/engine/remotix-install.spec", "The engine package, RPM family"),
        ("packaging/engine/PKGBUILD", "The engine package, Arch"),
        ("packaging/engine/remotix-install.install", "Arch engine package scripts: post-upgrade check"),
        ("packaging/engine/README", "What the engine package is, for the administrator"),
        ("packaging/archive/licenses.py", "Collects the licence texts of everything REMOTIX ships"),
        ("packaging/archive/sbom.py", "The SBOM of each product package"),
    ]),
    ("Manual sources", manuale()),
]

S1 = p("Every product file with its line count, recounted each time the manual is generated: the server, the "
       "page, the installer and its interface, the packaging of each family and the sources of this manual. "
       "The files kept out are the installer's vendored modules, the protocol headers generated at build time "
       "and binary images. If a file is missing from the map, or the map lists a file that no longer exists, "
       "generation stops — and so does " + c("build.py --check") + ". The role of each file is taken from "
       "its own header comment; for C modules the " + c(".h") + " carries the why and the " + c(".c")
       + " the how.",
       lead=True) + file_map(GRUPPI, "«TAB» — The project's files")

BENCHES = table(["Folder or prefix", "What it tests"], [
    "Root of " + c("benches/") + ": one file per bench, results next to it",
    [c("00-*"), "The environment of phase 0: anchors, the first KWin and wlroots probes, atomic log, the GNOME "
     "session"],
    [c("01-*"), "The bare wire: QUIC and WebTransport probes (ngtcp2, quiche, lsquic), the RCP validator, "
     "handshake, ban, farewell and limits benches B0–B13, browser probe pages, the first phone runs"],
    [c("02-*"), "The first frame: capture, encoding (NAL and OBU readers), the child, PAM, the page decoder, "
     "pixel judges and the chain judgement"],
    [c("03-*"), "Motion: cadence, declared scenes, the mark, the palette of browser codecs"],
    [c("04-*"), "Control: input injection, keyboard, cursor, gestures, shortcuts, canvas geometry"],
    [c("05-*") + ", " + c("06-*"), "The sentinel, the session cycle, detach and reattach; canvas and view, "
     "compositor contention"],
    [c("07-*"), "Audio and clipboard, the Marionette driver, what the browser accepts, Android Firefox"],
    [c("08-*") + ", " + c("09-*") + ", " + c("10-*"), "Zero copy and VA surfaces; quality on bad networks and "
     "the " + c("netem") + " lock; multi-tenant capacity, the budget and the GPU lock"],
    [c("12-*") + ", " + c("13-*") + ", " + c("14-*"), "The KDE, XFCE and LXQt increments; the real-browser "
     "drivers " + c("12-real-clients.py") + " and " + c("12-c20-real.py") + " (" + c("veri") + " = real)"],
    [c("tools-*.sh") + " (tools)", "Shared helpers: tenants, card groups, re-grafting the product into a bench"],
    [c("b*-outcomes*.jsonl") + ", " + c("flusso-*.json") + ", " + c("pagina-*.rgb24"), "Results (" + c("outcomes") + "), "
     "streams (" + c("flusso") + ") and decoded page pixels (" + c("page") + ") kept from phases 1–2"],
    "Folders of evidence (results only)",
    [c("01-p5-copie*/") + " (" + c("copie") + " = copies)", "Browser screenshots of the phase 1 login runs: healthy, faulty, repaired"],
    [c("02-filo-prove/") + " (wire tests)", "RCP recordings, good and broken, for the wire validator"],
    [c("02-giudizio-catena-copie/") + ", " + c("02-montaggio-copie/") + ", " + c("02-pagina-misura-copie/")
     + ", " + c("02-pagina-vista-copie/"), "Screenshots (" + c("giudizio-catena") + " = chain judgement, " + c("montaggio") + " = assembly) of the first image chain, the first end-to-end run (the desktop in a browser "
     "tab), the page measure and the view"],
    [c("02-pagina-pixel/") + ", " + c("02-pagina-tela-pixel/"), "Decoded pixels from Chrome and Firefox per "
     "stream variant"],
    [c("02-pagina-sequenze/") + ", " + c("02-pagina-tela-sequenze/") + ", " + c("03-b16-sequenze/"),
     "Declared encoded sequences fed to the page"],
    [c("02-session-scenes/") + " (session scenes)", "A black and a healthy scene for the session judge"],
    [c("07-b43-copie/"), "Expected and observed audio states (healthy, silence, frequency)"],
    "Machinery still run",
    [c("11-boxes/") + " (boxes)", "The safety net: four desktop boxes (and an xrdp one), the meshes C1–C24, the push hook"],
    [c("14-stress/"), "The first night-stress harness and its scenarios; superseded by " + c("16-stress/")],
    [c("15-suite/"), "The functional suite: about 30 user functions on 4 desktops with Firefox and Chrome"],
    [c("16-stress/"), "The stress ramp, the browser actors, the classifier, the xrdp comparison twin"],
    [c("17-distro/"), "Distribution VMs and boxes: install, reboot, system update, uninstall on 26 combinations"],
    [c("17-t2/") + ", " + c("17-t6/") + ", " + c("17-t7/") + ", " + c("17-t8/"),
     "Installer stage benches: desktops surviving a stop (T2), PAM and SELinux (T6), upgrading without closing the desktops, which the new parent finds again (T7), "
     "faults and third-party repositories (T8). T8 is history"],
    [c("18-card/"), "The Chrome decoding page used by " + c("19-vulkan/") + " (the phase-18 comparisons were "
     "retired, " + c("DECISIONS.md") + " §10.44)"],
    [c("19-vulkan/"), "Vulkan Video vs VA-API, the shader build, Chrome decoding of the result"],
    [c("19-nvidia/"), "The rented NVIDIA machine: container test and suite"],
    [c("19-android/"), "The Android phone over adb"],
    [c("rcp/"), "The twin copy of " + c("rcp.c") + ", " + c("rcp.h") + " and " + c("authentication.c")
     + ", byte-identical to " + c("src/") + " (checked by " + c("make") + ")"],
    [c("prodotto/") + " (product), " + c("probe/") + " (probe)", "Smoke test of the server in the build container; a browser probe "
     "against it"],
    [c("ritrovati/") + " (found again)", "Bench files found outside the repository and saved, with a README"],
], "«TAB» — The bench folder, by folder")

S2 = p(c("benches/") + " holds about 1,800 files and is described by folder, not file by file. The prefix of a "
       "file at the root is the number of the phase that wrote it; the folders with a name are either evidence "
       "kept next to a result or machinery that is still run. How to run them is in "
       + rif("Running the benches") + ".", lead=True) + BENCHES

CHAPTER = ("Appendix B — File map", [
    ("The project's files", S1),
    ("The bench files by folder", S2),
])
