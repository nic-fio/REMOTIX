import re

from build import ROOT, c, file_map, p, rif, sorgenti, table

S = "src/"
M = "installatore/motore/"


def t(parole):
    """La traduzione inglese di un nome italiano, in testa al ruolo."""
    return f"(<i>{parole}</i>) "


def manuale():
    """I sorgenti del manuale: il generatore, lo stile, lo script e un file per capitolo, col suo titolo."""
    righe = [
        ("docs/sources/build.py", "Generates the manual: text, table and SVG figure helpers, numbering, the "
         "file map and project figures, and the " + c("--controlla") + " checks (Italian left, cited files, "
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
        (S + "figlio.c", t("child") + "One process per user that runs as that user and holds the stage: fork then exec, "
         "logind session, desktop start, capture, encoding and input inside it"),
        (S + "figlio.h", "Why the child exists (root cannot join the user's session bus), its invariants and the "
         "parent–child messages"),
        (S + "aiutante.c", t("helper") + "The PAM helper process: verifies passwords off the single thread"),
        (S + "aiutante.h", "Why the helper exists (PAM blocks 1–2 s per attempt), its three layers and invariant I3"),
        (S + "autenticazione.c", t("authentication") + "PAM conversation and the guard that starts from “denied”; no comparison with "
         "the process user"),
        (S + "sessione.c", t("session") + "Starts the headless graphical session with its virtual monitor, on GNOME, KDE, "
         "XFCE and LXQt; the session log in the user's home"),
        (S + "sessione.h", "The graphical session contract: born by REMOTIX, born with a monitor, and why it is "
         "not v1's copy"),
        (S + "sentinella.c", t("sentinel") + "Watches local graphical sessions through logind and emits the two local-session "
         "reasons"),
        (S + "sentinella.h", "Who watches local sessions and on whose behalf (SPECIFICHE §5.1)"),
        (S + "ritrovo.c", t("finding again") + "Finds live REMOTIX desktops that no child holds, after a service restart"),
        (S + "ritrovo.h", "Why found-again desktops exist (stopping the service does not kill desktops) and the "
         "criterion that recognises them"),
        (S + "budget.c", "The composition budget mechanism: per-user accounts, admission, degradation"),
        (S + "budget.h", "The reason behind every number of the budget (phase 10) and its interface"),
        (S + "registro.c", t("log") + "Writes log lines: instant, area, level, one place for all output"),
        (S + "registro.h", "The log contract: why a module and not " + c("printf") + ", areas and levels"),
        (S + "comando.c", t("command") + "The unlock command: a Unix control socket that lifts a ban and logs it"),
        (S + "comando.h", "Why unlocking is a socket and not a command-line option (RCP §4.4-bis)"),
    ]),
    ("Capture and desktop backends", [
        (S + "cattura.c", t("capture") + "Reads frames from the PipeWire node the compositor opened (GNOME, KDE), with the "
         "declared buffer type"),
        (S + "cattura.h", "The capture mandate: a frame delivered in memory with its declared, not inferred, "
         "buffer type"),
        (S + "mutter.c", "The D-Bus sequence that opens a virtual monitor and its stream on Mutter"),
        (S + "mutter.h", "The mandatory Mutter sequence and the penalty attached to each step"),
        (S + "kwin.c", "The stage on KDE Plasma: " + c("zkde_screencast_unstable_v1") + " on the virtual output, "
         "and the EIS input channel"),
        (S + "kwin.h", "What was carried over from v1 for KWin: capture protocol and input channel"),
        (S + "wlroots.c", "Capture on labwc (XFCE, LXQt) with screencopy: from the card via dmabuf, from "
         "memory as a declared fallback"),
        (S + "wlroots.h", "Why wlroots is the other direction: frames are pulled, not pushed, and there is no "
         "PipeWire node"),
        (S + "cursore.c", t("cursor") + "From PipeWire's cursor metadata to the cursor-shape message"),
        (S + "cursore.h", "The cursor-shape seam, from PipeWire to the wire"),
        (S + "forma.c", t("shape") + "The encoded cursor theme and its dictionary, shared by server and child"),
        (S + "forma.h", "How the real pointer shape reaches the browser where the compositor does not send it"),
        (S + "remotix-tasti.conf", t("keys") + "Second power belt: logind ignores the power, reboot, suspend and hibernate keys and the lid"),
        (S + "remotix-niente-spegnimento.rules", t("no power-off") + "First power belt: polkit rule so that nobody shuts the "
         "server down"),
    ]),
    ("Encoding", [
        (S + "codificatore.c", t("encoder") + "From the captured frame to the stream: picks the hardware path, keyframes, "
         "reads back what the encoder really produced"),
        (S + "codificatore.h", "What the encoder is and is not; the contract with capture and transport"),
        (S + "vadiretta.c", t("direct VA") + "H.264 and HEVC on the card with libva used directly: levels, headers bit by bit, "
         "per-frame encode"),
        (S + "vadiretta.h", "Why libva is used without libavcodec (ffmpeg left the product, phase 18)"),
        (S + "vulkanvideo.c", "H.264 and HEVC with Vulkan Video: device, profiles, session, parameters, "
         "per-frame encode"),
        (S + "vulkanvideo.h", "Why Vulkan Video (phase 19) and its rules"),
        (S + "vulkanvideo_rgb_nv12.comp", "Compute shader RGB → NV12/P010, BT.709 limited range, bit-identical to "
         + c("colori709.c")),
        (S + "vulkanvideo_rgb_nv12_spv.h", "The compiled SPIR-V of the shader (generated, not edited by hand)"),
        (S + "colori709.c", t("BT.709 colours") + "BGRx → YUV 4:2:0 BT.709 limited conversion without libswscale"),
        (S + "colori709.h", "Why the conversion is ours (phase 18) and its coefficients"),
        (S + "scrittore_bit.c", t("bit writer") + "Bit writer: Exp-Golomb, trailing bits, emulation prevention"),
        (S + "scrittore_bit.h", "Writing H.264/H.265 parameter sets field by field, as packed headers"),
    ]),
    ("Transport and protocol", [
        (S + "trasporto.c", t("transport") + "The UDP listener: QUIC with ngtcp2, connections, timers, datagrams"),
        (S + "trasporto.h", "The first of the two listeners on the same port (RCP §2.4)"),
        (S + "webtransport.c", "The WebTransport layer over HTTP/3 (nghttp3): extended CONNECT, streams, "
         "datagrams, and RCP on top"),
        (S + "webtransport.h", "Why the WebTransport layer is ours: neither library carries it server side"),
        (S + "rcp.c", "The RCP/1 state machine, server side: handshake, ban, farewell, every rule with its "
         "paragraph number"),
        (S + "rcp.h", "RCP messages, reasons, limits; knows RCP.md and nothing else"),
        (S + "pagina.c", t("page") + "The TCP listener: serves the page over HTTPS with the certificate fingerprint written in"),
        (S + "pagina.h", "The second listener, same port number, HTTP/1.1 only for the page"),
        (S + "tls.c", "The two TLS contexts, one per listener"),
        (S + "tls.h", "Why two contexts: two certificates (RCP §4.1-bis)"),
        (S + "certificati.c", t("certificates") + "Generates, rotates and loads the long-lived and session certificates"),
        (S + "certificati.h", "The two certificates and what confusing them costs"),
    ]),
    ("Input", [
        (S + "input.c", "Input reaches the desktop through libei (GNOME, KDE): pointer, buttons, wheel, keys"),
        (S + "input.h", "The input seam, from the wire to the desktop"),
        (S + "wlr_input.c", "Virtual keyboard and pointer on labwc, with the five silent traps marked"),
        (S + "wlr_input.h", "Input transport on wlroots, where libei does not exist"),
        (S + "tastiera.c", t("keyboard") + "From a character to the key positions that produce it on the session's layout"),
        (S + "tastiera.h", "The keyboard seam: characters on the wire, positions to the compositor"),
    ]),
    ("Audio and clipboard", [
        (S + "audio.c", "The Opus encoder"),
        (S + "audio.h", "The fixed audio format (RCP §5.3): Opus with PCM as the basis"),
        (S + "suono.c", t("sound") + "The virtual sink and the capture of its monitor on PipeWire"),
        (S + "suono.h", "The session's sound: why the sink must be created, session vs connection"),
        (S + "appunti.c", t("clipboard") + "The clipboard on Mutter, through the RemoteDesktop session"),
        (S + "appunti.h", "The clipboard seam, from desktop to wire and back"),
        (S + "appunti_kde.c", "The clipboard on KDE and labwc through the Wayland data-control protocol"),
        (S + "appunti_kde.h", "Data-control clipboard behind the same interface as " + c("appunti.h")),
    ]),
    ("The page", [
        (S + "pagina.html", "The whole browser client: login, WebTransport, RCP, WebCodecs video, Opus audio, "
         "input, clipboard, canvas and view"),
        (S + "opus-wasm/costruisci.sh", t("build") + "Builds the Opus WebAssembly decoder and embeds it in the page"),
        (S + "opus-wasm/decodifica.c", t("decode") + "The decoder compiled to WebAssembly: libopus, decode only, static buffers"),
        (S + "opus-wasm/opus.wasm.sha256", "Fingerprint of the embedded decoder"),
        (S + "opus-wasm/prova/confronta.mjs", t("prova = test; confronta = compare") + "Decodes test packets with the wasm extracted from the page"),
        (S + "opus-wasm/prova/prova.sh", "Compares the embedded decoder with native libopus"),
        (S + "opus-wasm/prova/riferimento.c", t("reference") + "Native reference: encodes test signals in the three Opus modes"),
    ]),
    ("Wayland protocols", [
        (S + "protocolli/ext-data-control-v1.xml", t("protocolli = protocols") + "Standard clipboard access protocol"),
        (S + "protocolli/linux-dmabuf-unstable-v1.xml", "Buffers shared with the card (wlroots capture)"),
        (S + "protocolli/virtual-keyboard-unstable-v1.xml", "Virtual keyboard (labwc input)"),
        (S + "protocolli/wlr-data-control-unstable-v1.xml", "wlroots clipboard access (KDE and labwc)"),
        (S + "protocolli/wlr-output-management-unstable-v1.xml", "Output size on labwc"),
        (S + "protocolli/wlr-screencopy-unstable-v1.xml", "Screen capture on labwc"),
        (S + "protocolli/wlr-virtual-pointer-unstable-v1.xml", "Virtual pointer (labwc input)"),
        (S + "protocolli/zkde-screencast-unstable-v1.xml", "KWin screen streams as PipeWire nodes"),
    ]),
    ("System files and server build", [
        (S + "remotix.pam", "PAM service for Debian and Ubuntu"),
        (S + "remotix.pam.arch", "PAM service for Arch, without " + c("@include")),
        (S + "remotix.pam.fedora", "PAM service for Fedora and the RHEL family: the system's sshd stack, "
         "root excluded"),
        (S + "remotix.pam.suse", "PAM service for openSUSE, installed under " + c("/usr/lib/pam.d")),
        (S + "Makefile", "Builds the server: declared dependencies, the twin check, the generated protocol headers"),
        (S + "Contenitore", t("container") + "The everyday build container, without sudo"),
        (S + "costruisci-in-contenitore.sh", t("build in container") + "Builds the server on the laptop inside that container"),
        (S + "costruisci.sh", "Builds the server inside the test machine's container"),
        (S + "provisiona.sh", t("provision") + "Puts the test machine in the state the product expects, and verifies it"),
        (S + "riavvia-7700.sh", t("restart") + "Restarts the test server on port 7700 with the page on disk"),
        (S + "riavvia-7900.sh", "Restarts the phase 9 test server on port 7900, with its own tree and unit"),
        (S + "costruzione/Contenitore.alma10", t("costruzione = build") + "Build container for AlmaLinux 10"),
        (S + "costruzione/Contenitore.arch", "Build container for Arch Linux"),
        (S + "costruzione/Contenitore.debian13", "Build container for Debian 13, the reference"),
        (S + "costruzione/Contenitore.fedora44", "Build container for Fedora 44"),
        (S + "costruzione/Contenitore.leap16", "Build container for openSUSE Leap 16"),
        (S + "costruzione/Contenitore.tumbleweed", "Build container for openSUSE Tumbleweed"),
        (S + "costruzione/Contenitore.ubuntu2404", "Ubuntu 24.04: only to see where it stops (OpenSSL 3.0)"),
        (S + "costruzione/Contenitore.ubuntu2604", "Build container for Ubuntu 26.04"),
        (S + "costruzione/costruisci-deb.sh", "Builds the .deb inside the target's container"),
        (S + "costruzione/costruisci-tutti.sh", t("build all") + "Builds REMOTIX for one, some or all targets"),
        (S + "costruzione/quic-statiche.sh", t("static QUIC") + "Builds ngtcp2 and nghttp3 from source, static, pinned versions"),
    ]),
    ("Installer engine (" + c("installatore/") + " = installer, " + c("motore/") + " = engine)", [
        ("installatore/cmd/remotix-install/main.go", "The command line: " + c("check") + ", " + c("install")
         + ", " + c("uninstall") + ", " + c("status") + ", " + c("tui") + " and the commands package scripts call"),
        ("installatore/cmd/remotix-install/interfacce.go", t("interfaces") + "Starts the text interface"),
        (M + "formato.go", t("format") + "Package entry: object format version, engine version, fingerprints"),
        (M + "stati.go", t("states") + "The operation states and the only valid transitions"),
        (M + "operazione.go", t("operation") + "The engine and an operation: lock, apply, resume, cancel, verify, certify"),
        (M + "registro.go", t("log") + "The write-ahead log: every line made durable before the next step"),
        (M + "eventi.go", t("events") + "What the engine says while working, as text or one JSON line per event"),
        (M + "fiducia.go", t("trust") + "Phase 0 TRUST: the catalogue is the engine's own, and where it came from"),
        (M + "preflight.go", "Examines the machine read-only: files, D-Bus, one closed list of commands"),
        (M + "profilo.go", t("profile") + "The machine profile and its facts, detected vs verified"),
        (M + "compatibilita.go", t("compatibility") + "The catalogue format and the compatibility assessment"),
        (M + "strade.go", t("routes") + "The hardware encoding paths and the verdict “at least one capable card”"),
        (M + "piano.go", t("plan") + "The machine fingerprint that binds a plan, and the plan object"),
        (M + "piano_installazione.go", t("installation plan") + "The install or upgrade plan: what is missing is said, not installed"),
        (M + "interfaccia.go", t("interface") + "The only question asked on this machine: the port, then yes to the plan"),
        (M + "azioni.go", t("actions") + "Reversibility, origin and check outcome of every action"),
        (M + "azioni_dichiarate.go", t("declared actions") + "Steps the engine knows but cannot run yet (the list is empty)"),
        (M + "azione_file.go", t("file action") + "Write a file atomically, with the old content saved for undo"),
        (M + "azione_gruppo.go", t("group action") + "Add a person to the card's groups; pre-existing membership is never removed"),
        (M + "azione_pacchetti.go", t("packages action") + "The package transaction: simulate, install, check, undo"),
        (M + "azione_registri_utente.go", t("user logs action") + "Remove the REMOTIX session log from every home at uninstall"),
        (M + "azione_servizio.go", t("service action") + "Enable and start the service on systemd's D-Bus, done only if the port answers"),
        (M + "azione_sessioni.go", t("sessions action") + "Close open REMOTIX sessions at uninstall, through logind"),
        (M + "azione_unita.go", t("unit action") + "Enable a systemd unit (kept, no new plan uses it)"),
        (M + "grafica_utente.go", t("user graphics") + "Stops the desktop units of a REMOTIX session in the user manager, never the "
         "whole user"),
        (M + "disinstalla.go", t("uninstall") + "Uninstall: walks the confirmed installation log backwards"),
        (M + "aggiornato.go", t("upgraded") + "After a system upgrade: records versions and re-checks certification"),
        (M + "certifica.go", t("certify") + "Platform certification: encode test, PAM stack resolved, every step checked"),
        (M + "gestore.go", t("manager") + "The distribution's package manager, launched from the closed list"),
        (M + "versioni.go", t("versions") + "Package version comparison as dpkg and rpmvercmp do it"),
        (M + "ambiente.go", t("environment") + "The closed list of programs the engine may launch, with absolute paths"),
        (M + "dbus.go", "The system D-Bus: systemd, logind and firewalld without their command-line tools"),
        (M + "archivio.go", t("archive") + "The single package: REMOTIX's packages per target inside the " + c(".run")),
        (M + "tabella.go", t("table") + "Generates the distribution and minimum-version tables from the catalogue"),
        (M + "codici.go", t("codes") + "The catalogue of stable " + c("RX-") + " codes, severity and nature"),
        (M + "lingua.go", t("language") + "English only for administrators; " + c("T()") + " looks texts up by key"),
        (M + "testi.go", t("texts") + "The engine's and command line's texts, in English"),
        (M + "certifica_test.go", "Certification on a deliberately broken machine never says green"),
        (M + "disinstalla_test.go", "Uninstall on the fake machine"),
        (M + "fiducia_test.go", "Phase 0 TRUST: the catalogue reads, this engine understands it"),
        (M + "finti_test.go", t("fakes") + "A fake machine under a folder: passwd, group, systemd and firewalld as JSON"),
        (M + "finti2_test.go", "The rest of the fake machine: package manager, unit state, logind sessions"),
        (M + "inglese_test.go", t("English") + "Finds Italian left in any administrator-facing string or catalogue text"),
        (M + "interfaccia_test.go", "The plan does not modify the system; exact packages before the question"),
        (M + "lingua_test.go", "Every code and key has its English text; every key used exists"),
        (M + "motore_test.go", t("engine") + "State transitions, code form, plan refused on a changed machine"),
        (M + "preflight_test.go", "Preflight on fake roots: each known defect with its code"),
        (M + "ripresa_test.go", t("resume") + "The engine killed at every point and resumed: the machine ends identical"),
        (M + "script_test.go", "The header of the single package file"),
        ("installatore/catalogo/catalogo.go", t("catalogue") + "Embeds the catalogue in the engine"),
        ("installatore/catalogo/catalogo.json", "The catalogue: supported combinations, minimum versions, "
         "packages, rules"),
    ]),
    ("Installer interface", [
        ("installatore/interfaccia/sessione.go", t("interfaccia = interface; sessione = session") + "The engine side of the interface: examine, plan, apply, as root"),
        ("installatore/interfaccia/vista.go", t("view") + "The engine's objects in plain words, for the screens"),
        ("installatore/interfaccia/testi.go", "The screens' texts, in English, from the approved mockup"),
        ("installatore/interfaccia/testi_test.go", "Every key used by the screens exists; plain words in the check"),
        ("installatore/interfaccia/tui/tui.go", "The terminal screens (Bubble Tea): fixed frame, Check › Plan › "
         "Install › Ready"),
        ("installatore/interfaccia/tui/anteprima.go", t("preview") + "Previews of every screen with sample data, for "
         + c("--preview")),
        ("installatore/interfaccia/tui/tui_test.go", "Frame width at 80 and 120 columns, no colour when asked"),
    ]),
    ("Installer build, single file and engine tests", [
        ("installatore/.gitignore", "Go cache and build output stay out of git"),
        ("installatore/go.mod", "The Go module and its pinned dependencies"),
        ("installatore/go.sum", "Checksums of the Go dependencies"),
        ("installatore/costruisci.sh", t("build") + "Builds the static engine and runs the tests in the official Go container"),
        ("installatore/run.sh", "The header of the single " + c(".run") + " file: checks, extracts, hands over "
         "to the engine"),
        ("installatore/prove/Contenitore.systemd", t("prove = tests; Contenitore = container") + "Fedora 44 with systemd running, for D-Bus actions"),
        ("installatore/prove/gruppi-desktop.sh", t("desktop groups") + "Asks each family's package manager whether the catalogue's "
         "desktop group names exist"),
        ("installatore/prove/impronta/main.go", t("fingerprint") + "Fingerprint of a folder, independent of the engine (test R1)"),
        ("installatore/prove/r1-contenitori.sh", t("R1 containers") + "R1 in containers: the check leaves " + c("/etc") + " identical"),
        ("installatore/prove/sul-server.sh", t("on the server") + "History: an engine round in a VM with commands that no longer exist"),
        ("installatore/prove/systemd-giro.sh", t("systemd round") + "History: an engine round in the systemd container, same reason"),
    ]),
    ("Packaging: Debian and Ubuntu", [
        ("packaging/debian/control", "Source and binary package, build and run dependencies"),
        ("packaging/debian/rules", "The .deb build, inside the target's container"),
        ("packaging/debian/copyright", "Copyright declaration of the package"),
        ("packaging/debian/source/format", "Native source format"),
        ("packaging/debian/remotix.service", "The service unit: runs as root, certificate, name"),
        ("packaging/debian/remotix.conf", "Packaged defaults; the administrator's choices go in "
         + c("/etc/remotix/remotix.conf.d/")),
        ("packaging/debian/remotix.tmpfiles", "The state and runtime directories"),
        ("packaging/debian/remotix.postinst", "After install: nothing switched on; on upgrade, try-restart"),
        ("packaging/debian/remotix.prerm", "Before removal: stops the service on remove only"),
        ("packaging/debian/remotix.postrm", "After removal: purge removes what the program created"),
        ("packaging/debian/remotix.ufw", "The ufw application profile, defined, not opened"),
        ("packaging/debian/remotix-niente-sospensione.conf", t("no suspend") + "Third power belt, shipped inert"),
        ("packaging/debian/remotix.lintian-overrides", "The page is the program, not documentation"),
        ("packaging/debian/org.kde.remotix.desktop", "Grants KWin's screencast interface to the binary"),
        ("packaging/debian/utenti-negati", t("denied users") + "Users that may never log in: root"),
    ]),
    ("Packaging: the RPM family", [
        ("packaging/rpm/remotix.spec", "One spec for Fedora, Alma, Tumbleweed and Leap, with conditional branches"),
        ("packaging/rpm/costruisci-rpm.sh", t("build rpm") + "Builds the .rpm in each target's container"),
        ("packaging/rpm/remotix.service", "The service unit, RPM family"),
        ("packaging/rpm/remotix.conf", "Packaged defaults"),
        ("packaging/rpm/remotix.tmpfiles", "The state and runtime directories"),
        ("packaging/rpm/remotix-firewalld.xml", "The firewalld service, defined, not opened"),
        ("packaging/rpm/remotix-niente-sospensione.conf", "Third power belt, shipped inert"),
        ("packaging/rpm/org.kde.remotix.desktop", "Grants KWin's screencast interface to the binary"),
        ("packaging/rpm/selinux/remotix.te", "The SELinux module: why it exists and the domain transition to the user"),
        ("packaging/rpm/selinux/remotix.fc", "SELinux file contexts"),
        ("packaging/rpm/selinux/remotix.if", "SELinux interface"),
        ("packaging/rpm/selinux/remotix_porta.cil", t("port") + "The port type for 7447 TCP and UDP, in CIL"),
    ]),
    ("Packaging: Arch", [
        ("packaging/arch/PKGBUILD", "The Arch package, built from the repository in the Arch container"),
        ("packaging/arch/costruisci.sh", t("build") + "Tarball of one commit, then makepkg and namcap"),
        ("packaging/arch/remotix.install", "Package scripts: nothing switched on"),
        ("packaging/arch/remotix.service", "The service unit, Arch"),
        ("packaging/arch/remotix.tmpfiles", "The state directory"),
        ("packaging/arch/remotix.firewalld.xml", "The firewalld service, defined, not opened"),
        ("packaging/arch/remotix-niente-sospensione.conf", "Third power belt, shipped inert"),
        ("packaging/arch/org.kde.remotix.desktop", "Grants KWin's screencast interface to the binary"),
        ("packaging/arch/utenti-negati", "Users that may never log in: root"),
    ]),
    ("Packaging: engine package and release", [
        ("packaging/rilascio.sh", t("release") + "The release command: builds everything and produces the single " + c(".run")),
        ("packaging/motore/pacchetti-motore.sh", t("motore = engine; pacchetti = packages") + "Packages the static engine for the three families"),
        ("packaging/motore/remotix-install.spec", "The engine package, RPM family"),
        ("packaging/motore/PKGBUILD", "The engine package, Arch"),
        ("packaging/motore/remotix-install.install", "Arch engine package scripts: post-upgrade check"),
        ("packaging/motore/README", "What the engine package is, for the administrator"),
        ("packaging/archivio/licenze.py", t("archivio = archive; licenze = licences") + "Collects the licence texts of everything REMOTIX ships"),
        ("packaging/archivio/sbom.py", "The SBOM of each product package"),
    ]),
    ("Manual sources", manuale()),
]

S1 = p("Every product file with its line count, recounted each time the manual is generated: the server, the "
       "page, the installer and its interface, the packaging of each family and the sources of this manual. "
       "The files kept out are the installer's vendored modules, the protocol headers generated at build time "
       "and binary images. If a file is missing from the map, or the map lists a file that no longer exists, "
       "generation stops — and so does " + c("build.py --controlla") + ". The role of each file is taken from "
       "its own header comment; for C modules the " + c(".h") + " carries the why and the " + c(".c")
       + " the how.",
       lead=True) + file_map(GRUPPI, "«TAB» — The project's files")

BANCHI = table(["Folder or prefix", "What it tests"], [
    "Root of " + c("banchi/") + ": one file per bench, results next to it",
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
     "drivers " + c("12-client-veri.py") + " and " + c("12-c20-veri.py") + " (" + c("veri") + " = real)"],
    [c("attrezzi-*.sh") + " (tools)", "Shared helpers: tenants, card groups, re-grafting the product into a bench"],
    [c("b*-esiti*.jsonl") + ", " + c("flusso-*.json") + ", " + c("pagina-*.rgb24"), "Results (" + c("esiti") + "), "
     "streams (" + c("flusso") + ") and decoded page pixels (" + c("pagina") + ") kept from phases 1–2"],
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
    [c("02-sessione-scene/") + " (session scenes)", "A black and a healthy scene for the session judge"],
    [c("07-b43-copie/"), "Expected and observed audio states (healthy, silence, frequency)"],
    "Machinery still run",
    [c("11-scatole/") + " (boxes)", "The safety net: four desktop boxes (and an xrdp one), the meshes C1–C24, the push hook"],
    [c("14-stress/"), "The first night-stress harness and its scenarios; superseded by " + c("16-stress/")],
    [c("15-suite/"), "The functional suite: about 30 user functions on 4 desktops with Firefox and Chrome"],
    [c("16-stress/"), "The stress ramp, the browser actors, the classifier, the xrdp comparison twin"],
    [c("17-distro/"), "Distribution VMs and boxes: install, reboot, system update, uninstall on 26 combinations"],
    [c("17-t2/") + ", " + c("17-t6/") + ", " + c("17-t7/") + ", " + c("17-t8/") + ", " + c("17-t9/"),
     "Installer stage benches: desktops surviving a stop (T2), PAM and SELinux (T6), upgrading without closing the desktops, which the new parent finds again (T7), "
     "faults and third-party repositories (T8), the interface (T9). T8 and T9 are history"],
    [c("18-a1/") + ", " + c("18-scheda/") + ", " + c("18-software/"), "Old vs new when ffmpeg left (" + c("scheda") + " = card): Opus "
     "without ffmpeg, libva direct vs ffmpeg on the card, the software path"],
    [c("19-vulkan/"), "Vulkan Video vs VA-API, the shader build, Chrome decoding of the result"],
    [c("19-nvidia/"), "The rented NVIDIA machine: container test and suite"],
    [c("19-android/"), "The Android phone over adb"],
    [c("rcp/"), "The twin copy of " + c("rcp.c") + ", " + c("rcp.h") + " and " + c("autenticazione.c")
     + ", byte-identical to " + c("src/") + " (checked by " + c("make") + ")"],
    [c("prodotto/") + " (product), " + c("sonda/") + " (probe)", "Smoke test of the server in the build container; a browser probe "
     "against it"],
    [c("ritrovati/") + " (found again)", "Bench files found outside the repository and saved, with a README"],
], "«TAB» — The bench folder, by folder")

S2 = p(c("banchi/") + " holds about 1,800 files and is described by folder, not file by file. The prefix of a "
       "file at the root is the number of the phase that wrote it; the folders with a name are either evidence "
       "kept next to a result or machinery that is still run. How to run them is in "
       + rif("Running the benches") + ".", lead=True) + BANCHI

CHAPTER = ("Appendix B — File map", [
    ("The project's files", S1),
    ("The bench files by folder", S2),
])
