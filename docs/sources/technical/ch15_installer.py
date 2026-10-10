"""Chapter 15 — The installer (remotix-install). Sources: installatore/ (cmd, motore, interfaccia,
catalogo, run.sh, costruisci.sh), DECISIONI §10.12-10.36, fasi/17-l-installatore.md §6.6.16.
The RX- code table and the supported-versions tables are generated from the sources at build time."""
import html
import json
import re

from build import (ROOT, arrow, box, c, code, esc, fig, flow, note, p, path, pill, rif, seq, steps, table, text,
                   tip, tree, ui, ul, warn, zone)

INST = ROOT / "installatore"


# ── Generated from the sources ─────────────────────────────────────────────
def _go_string(s):
    return s.replace('\\"', '"').replace("\\\\", "\\")


GRAVITA = {"INFO": "INFO", "AVVISO": "WARNING", "BLOCCANTE": "BLOCKING"}
NATURA = {"ServeAzione": "ACTION_NEEDED", "Riprovabile": "RETRYABLE", "Recuperabile": "RECOVERABLE",
          "ServeAnnullamento": "ROLLBACK_NEEDED", "Fatale": "FATAL"}
AREE = {
    "TRUST": "Phase 0 — trust in the catalogue",
    "DISTRO": "Phase 1 — the distribution",
    "SYSTEMD": "systemd (phase 1: booted with systemd; operation: the unit)",
    "GPU": "Phase 1 — the graphics card and its encoder",
    "H264": "Phase 1 — H.264 encoding on the card",
    "PAM": "Phase 1 — the login stack",
    "SELINUX": "Phase 1 — SELinux",
    "FW": "Phase 1 — firewall and port",
    "LOGIND": "Phase 1 — logind",
    "GRUPPI": "Graphics-card groups",
    "OPENSSL": "Phase 1 — OpenSSL",
    "DESKTOP": "Desktop (retired with the engine-installed desktop)",
    "COMPAT": "Phase 2 — compatibility",
    "MANCA": "Phase 2 — what is missing (DECISIONS §10.36)",
    "PIANO": "Phases 3-4 — plan and consent",
    "RISPOSTE": "Answer file (retired with §10.36)",
    "FUORI": "Offline bundle (retired with §10.36)",
    "STATO": "Operation state",
    "RIPRESA": "Resume after an interruption",
    "AZIONE": "Plan steps",
    "INST": "Installation marker and post-upgrade",
    "PACCHETTI": "Package manager",
    "CINTURA": "System guards (retired with §10.36)",
    "FILE": "Files written by the engine",
    "UI": "Interfaces (TUI; GUI codes retired)",
    "AGG": "Automatic updates (retired with D14, §10.23)",
}


def codici_rx():
    """The code catalogue, read from installatore/motore/codici.go, with the files that raise each code."""
    src = (INST / "motore" / "codici.go").read_text()
    rx = re.compile(r'"(RX-[A-Z0-9]+-\d{3})":\s*\{(\w+),\s*(\w+),\s*"((?:[^"\\]|\\.)*)",\s*"((?:[^"\\]|\\.)*)"\}')
    files = [f for f in sorted(INST.rglob("*.go")) if "vendor" not in f.parts and not f.name.endswith("_test.go")
             and f.name != "codici.go"]
    righe = {f: [r for r in f.read_text().splitlines() if not r.strip().startswith("//")] for f in files}
    out = []
    for cod, grav, nat, testo, rimedio in rx.findall(src):
        dove = sorted({f.name for f, rr in righe.items() if any(cod in r for r in rr)})
        out.append(dict(code=cod, area=cod.split("-")[1], sev=GRAVITA.get(grav, grav), nat=NATURA.get(nat, nat),
                        text=_go_string(testo), remedy=_go_string(rimedio), where=dove,
                        retired=testo.startswith("(retired")))
    return out


CODICI = codici_rx()


def tabella_codici():
    rows, area = [], None
    for k in CODICI:
        if k["area"] != area:
            area = k["area"]
            rows.append(c("RX-" + area) + " · " + esc(AREE.get(area, area)))
        stato = pill("retired", "off") if k["retired"] else pill(k["sev"], {"BLOCKING": "snooze", "WARNING": "wait"}
                                                                   .get(k["sev"], "info"))
        testo = esc(k["text"]) + (("<br><i>Remedy:</i> " + esc(k["remedy"])) if k["remedy"] else "")
        dove = ", ".join(c(w) for w in k["where"]) or "—"
        rows.append([c(k["code"]), stato, esc(k["nat"]), testo, dove])
    return table(["Code", "Severity", "Nature", "Text (as printed) and remedy", "Raised in"], rows,
                 "«TAB» — Every " + c("RX-") + " code of the engine, generated from " + c("installatore/motore/codici.go")
                 + f" ({len(CODICI)} codes, {sum(not k['retired'] for k in CODICI)} in force, "
                 + f"{sum(k['retired'] for k in CODICI)} retired)")


CAT = json.loads((INST / "catalogo" / "catalogo.json").read_text())
NOMI_DESKTOP = {"gnome": "GNOME", "kde": "KDE Plasma", "xfce": "XFCE", "lxqt": "LXQt"}


def tabella_piattaforme():
    """The same logic as TabellaVersioni() (motore/tabella.go), in HTML."""
    rows = []
    for pl in CAT["piattaforme"]:
        cond, visti = [], set()

        def metti(x):
            if x not in visti:
                visti.add(x)
                cond.append(x)
        h = pl.get("h264", {})
        if h.get("senza_h264_di_serie"):
            metti("H.264 on " + " and ".join(h["senza_h264_di_serie"]) + ": a VA-API driver with H.264 is not in the "
                  "distribution's packages")
        if h.get("amd_senza_vaapi"):
            metti("AMD: Mesa without VA-API")
        if h.get("vulkan_codifica"):
            metti("Vulkan Video encodes on " + ", ".join(h["vulkan_codifica"]) + " with the official driver")
        for d in pl.get("depositi", []):
            metti(esc(CAT["depositi"].get(d, {}).get("nome", d)) + " enabled")
        desk = []
        for d in ("gnome", "kde", "xfce", "lxqt"):
            dc = pl["desktop"].get(d)
            if not dc or not dc.get("supportato"):
                continue
            desk.append(NOMI_DESKTOP[d])
            for k in dc.get("componenti", []):
                metti(c(k) + " (" + NOMI_DESKTOP[d] + ")")
            for k in dc.get("limiti", []):
                metti(esc(k))
            if dc.get("richiede_3d"):
                metti(NOMI_DESKTOP[d] + ": needs 3D acceleration")
        stato = ("certified (full run " + pl["giro_intero"] + ")" if pl.get("matrice") and pl.get("giro_intero")
                 else "in the matrix, not yet certified (no full run)" if pl.get("matrice")
                 else "analysed, outside the matrix")
        rows.append([esc(pl["nome"]), esc(pl.get("etichetta_versione", ", ".join(pl["versioni"]))), stato,
                     ", ".join(desk), "; ".join(cond) or "—"])
    for pl in CAT["piattaforme"]:
        for d in pl.get("derivate", []):
            v = d.get("versione_minima") or ", ".join(d["versioni"]).replace("*", "rolling")
            rows.append([esc(d["nome"]), esc(v), "compatible, not certified", "as " + esc(pl["nome"]),
                         esc(d.get("nota", "—"))])
    return table(["Distribution", "Version", "Status", "Desktops", "Conditions"], rows,
                 "«TAB» — The platforms of the catalogue " + c(CAT["versione"]) + " (sequence " + str(CAT["sequenza"])
                 + "), generated from " + c("installatore/catalogo/catalogo.json"))


def tabella_escluse():
    rows = [[c(e["id"]), esc(", ".join(e["versioni"])), esc(e["motivo"])] for e in CAT["escluse"]]
    rows += [["—", "—", esc(x)] for x in CAT["fuori_sempre"]]
    return table(["os-release ID", "Versions", "Why it is out"], rows,
                 "«TAB» — Excluded platforms (" + c("escluse") + " and " + c("fuori_sempre") + " of the catalogue)")


def tabella_minimi():
    rows = [[esc(k["componente"]), esc(k["minimo"]), esc(k["perche"])] for k in CAT["componenti_minimi"]]
    r = CAT["requisiti"]
    rows.append(["<b>Checked by the engine</b>", "OpenSSL " + esc(r["openssl_minima"]) + " · GNOME " + esc(r["gnome_minima"])
                 + " · KDE " + esc(r["kde_minima"]) + " · XFCE " + esc(r["xfce_minima"]) + " · LXQt "
                 + esc(r["lxqt_minima"]) + " · systemd required", c("requisiti") + ": RX-COMPAT-006 / RX-COMPAT-007"])
    return table(["Component", "Minimum", "Why"], rows,
                 "«TAB» — Minimum component versions (" + c("componenti_minimi") + " and " + c("requisiti") + ")")


# ── Sections ──────────────────────────────────────────────────────────────
S_INTRO = p("REMOTIX is installed by one program, " + c("remotix-install") + ", delivered inside one file, "
            + c("remotix-X.Y.Z-R.run") + ". It examines the machine, says what is missing, shows the exact packages the "
            "distribution's package manager would install, asks once, installs, verifies and starts the service. It also "
            "uninstalls, and re-checks an installation later. It is a statically linked Go binary (no cgo), with the "
            "catalogue of supported platforms compiled in.", lead=True) + \
    table(["Principle", "What it means in the code", "Decision"], [
        ["<b>REMOTIX does not modify the system</b>", "The engine never adds repositories, drivers, desktops, desktop "
         "components the distribution lacks, firewall rules or system guards. " + c("check") + " says what is missing "
         "(RX-MANCA-001…004, RX-GPU-003…006) without suggesting packages or commands, and " + c("install") + " stops "
         "before touching anything.", "DECISIONS §10.36"],
        ["<b>One deliberate exception</b>", "People are added to the groups of the card nodes (" + c("/dev/dri/card*")
         + ", " + c("renderD*") + ") automatically, at installation and at the first connection: without them a remote "
         "desktop cannot use the card.", "§10.36, §7.21"],
        ["<b>One program, monolithic</b>", "Engine, command line and TUI in one executable. systemd, logind and firewalld "
         "are reached over D-Bus; external programs only from a closed list, with absolute paths, each call logged.",
         "§10.14"],
        ["<b>The package manager installs</b>", "Files are put on disk by " + c("apt") + ", " + c("dnf") + ", "
         + c("zypper") + " or " + c("pacman") + ", never copied by the engine; resolution, signatures, dependencies are "
         "theirs. The engine has no package cache and no sha256 of its own for packages.", "§6.0 rule 1, §10.36"],
        ["<b>Rolling back is ours</b>", "Every step is written to a write-ahead log before it runs, with how to verify "
         "and how to undo it; an interrupted installation is rolled back, never resumed half way.", "§6.6.3, §10.36"],
        ["<b>One file, no repository</b>", "The " + c(".run") + " carries the engine and the REMOTIX packages of every "
         "supported distribution; dependencies come from the repositories the machine already has. Upgrading = running "
         "the newer " + c(".run") + ".", "§10.36 (supersedes the signed archive of §10.21/§10.23)"],
        ["<b>English only</b>", "Every text the administrator reads is in English; code names, comments and "
         "the catalogue's keys stay Italian.", "§10.32, §10.35"],
        ["<b>Two interfaces</b>", "The command line and a TUI on the same engine; the GUI was removed on 10 Oct 2026.",
         "§10.31"],
    ], "«TAB» — The rules the installer is built on") + \
    note("the design went through several shapes between 29 Sep and 10 Oct 2026 (signed archive, "
         + "an install.sh script, answer files, offline bundles, plan/approve/apply, a Gio GUI, an Italian/English "
         "interface). Only the current shape is described here; the retired codes in "
         + rif("The RX- code catalogue") + " are the visible trace of the old ones and must never be reused.",
         "History.")

SOURCE_TREE = tree([
    "installatore/",
    "├── cmd/remotix-install/  # main.go: the commands; interfacce.go: tui",
    "├── motore/               # the engine: the only place with installation logic",
    "│   ├── operazione.go     # Motore, Applica/Riprendi/Annulla, the state walk, certificate",
    "│   ├── stati.go          # the 19 states and their valid transitions",
    "│   ├── registro.go       # the write-ahead log (log.jsonl)",
    "│   ├── eventi.go         # events: text for the terminal, JSON lines for the TUI",
    "│   ├── preflight.go      # phase 1, read only: the machine profile",
    "│   ├── strade.go         # the encoding routes (vulkan, vaapi) and the card verdict",
    "│   ├── compatibilita.go  # the catalogue model and phase 2 (Valuta)",
    "│   ├── piano.go          # Piano, fingerprint, approval",
    "│   ├── piano_installazione.go  # the installation / upgrade plan",
    "│   ├── azione_*.go       # the step types (packages, groups, files, units, service…)",
    "│   ├── disinstalla.go    # the uninstallation plan and the undo step",
    "│   ├── gestore.go        # apt, dnf, zypper, pacman adapters",
    "│   ├── certifica.go      # platform checks (PAM, firewall) and status",
    "│   ├── ambiente.go       # the machine: closed program list, groups, units",
    "│   ├── dbus.go           # systemd, logind, firewalld over D-Bus",
    "│   ├── codici.go         # the RX- code catalogue",
    "│   └── testi.go          # the engine's English texts, T(key)",
    "├── interfaccia/          # the view: Session (sessione.go), Vista* (vista.go), texts",
    "│   └── tui/              # Bubble Tea screens, --preview",
    "├── catalogo/             # catalogo.json, embedded with go:embed",
    "├── prove/                # R1 proof in containers, fingerprint tool, history",
    "├── vendor/               # Go modules: the build is offline",
    "├── run.sh                # the header of the .run file",
    "└── costruisci.sh         # build and tests in the golang:1.25 container",
], "«FIG» — The installer source tree (" + c("vendor/") + " excluded from the line counts)")

LAYERS = fig(
    zone(20, 14, 860, 92, "Interfaces — no installation logic (R36)")
    + box(40, 44, 250, 50, "Command line", "cmd/remotix-install/main.go", "navy")
    + box(325, 44, 250, 50, "TUI", "interfaccia/tui (Bubble Tea)", "navy")
    + box(610, 44, 250, 50, "Session and views", "interfaccia/sessione.go, vista.go", "blue")
    + arrow(165, 96, 165, 132) + arrow(450, 96, 450, 132) + arrow(735, 96, 735, 132)
    + zone(20, 134, 860, 92, "Engine — package motore")
    + box(40, 164, 190, 50, "Phases 0-2", "trust, preflight, compatibility", "blue")
    + box(250, 164, 190, 50, "Plan", "steps with do / check / undo", "blue")
    + box(460, 164, 190, 50, "Operation", "states, log, rollback", "blue")
    + box(670, 164, 190, 50, "Certificate", "checks, conditions", "blue")
    + arrow(450, 216, 450, 252)
    + zone(20, 254, 860, 92, "Ambiente — everything the engine reads or changes")
    + box(40, 284, 190, 50, "Files", "/etc, /sys, /proc, dpkg/pacman db", "dark")
    + box(250, 284, 190, 50, "D-Bus", "systemd, logind, firewalld", "dark")
    + box(460, 284, 190, 50, "Closed program list", "package managers, gpasswd", "dark")
    + box(670, 284, 190, 50, "remotix --prova-codifica", "the product tests the card", "amber"),
    900, 352, "«FIG» — The installer's layers: interfaces show and ask, the engine decides, the Ambiente touches the machine")

S_LAYOUT = p("The installer is one Go module, " + c("remotix/installatore") + " (" + c("go.mod") + ": Go 1.25, Bubble Tea "
             "1.3.10, lipgloss 1.1.0, godbus 5.2.2). Every dependency is vendored, and the build runs with "
             + c("GOFLAGS=-mod=vendor GOPROXY=off CGO_ENABLED=0") + ": it never touches the network and the result runs on "
             "every distribution before any package is installed.", lead=True) + SOURCE_TREE + LAYERS + \
    p("The engine is the only package with installation logic. The interfaces read the engine's objects and events and "
      "collect a single consent; they never choose packages, repositories or rollbacks. In tests the "
      + c("Ambiente") + " is a fake rooted in a temporary folder (" + c("Radice") + "), so the same engine code runs "
      "against a fake machine (" + c("finti_test.go") + ", " + c("finti2_test.go") + ").")

CMD_ROWS = [
    [c("check"), c("--port N") + ", " + c("--json"), "Phases 0-2, read only: trust, profile, compatibility report, what "
     "is missing, warnings, every fact with its state. Does not need root (some facts become UNKNOWN without it).",
     "0 if nothing is missing and at least one installed desktop is supported; 1 otherwise; 2 bad options"],
    [c("install"), c("--port N") + ", " + c("--users A,B"), "Root. Settles an unfinished operation first, builds the plan "
     "(upgrade if a CONFIRMED installation exists), lets the package manager simulate, prints the plan, asks "
     + c("Proceed? [y/N]") + " on stdin, applies.", "0 if CONFIRMED or CONFIRMED_WITH_CONDITIONS, or nothing to do; 1 "
     "otherwise"],
    [c("uninstall"), c("--purge"), "Root. Completes an unfinished uninstallation or rolls back an unfinished "
     "installation; otherwise builds the uninstallation plan from the installation's log and asks "
     + c("Remove REMOTIX? [y/N]") + ".", "0 if confirmed; 1 otherwise"],
    [c("status"), c("--json"), "Lists the operations (an open one is marked), then re-runs the installation's checks: "
     "GREEN, CONDITIONAL or RED.", "0 only if GREEN"],
    [c("tui"), c("--port N"), "Root and a terminal on stdin (else RX-UI-006). The same installation in a text interface.",
     "as " + c("install")],
    [c("catalog") + " (hidden)", c("--table"), "Catalogue version, sequence, issue date, minimum engine, digest, source; "
     "with " + c("--table") + " the supported-versions tables in Markdown.", "0"],
    [c("post-upgrade") + " (hidden)", "—", "Called by the package scripts at every version change: records the installed "
     "REMOTIX versions, prints whether the installation is still certified and any BLOCKING reason (RX-INST-002).",
     "always 0: it never makes the package manager fail"],
    [c("version") + ", " + c("help"), "—", "Engine version and object format; usage text.", "0"],
]

S_COMMANDS = p("Since 10 Oct 2026 the command line has four public commands plus " + c("tui") + " (DECISIONS §10.36: "
               "from fourteen down to five). Options can come before or after positional arguments (" + c("argomenti()")
               + " re-parses after each one).", lead=True) + \
    table(["Command", "Options", "What it does", "Exit code"], CMD_ROWS, "«TAB» — The commands of "
          + c("remotix-install")) + \
    table(["Option", "Default", "Meaning"], [
        [c("--state-dir DIR"), c("/var/lib/remotix/operations"), "Where operations are kept; plans go to "
         + c("../plans") + ", the installation marker to " + c("../installation.json") + "."],
        [c("--catalog FILE"), "the embedded one", "A catalogue given by hand: the administrator's responsibility, and the "
         "trust record says so."],
        [c("--port N"), "7447", "The REMOTIX port, TCP (page) and UDP (QUIC)."],
        [c("--bundle DIR"), "—", "The " + c("packages/") + " folder of the " + c(".run") + "; passed by the " + c(".run")
         + " itself to " + c("install") + " and " + c("tui") + "."],
    ], "«TAB» — Options common to every command (" + c("comuni") + " in " + c("main.go") + ")") + \
    warn("DECISIONS §10.36 lists " + c("prepare-offline") + " among the five commands; the code has no such command "
         "(RX-FUORI-001…005 are retired: “the .run file is already offline”). The " + c(".run") + " carries only "
         "REMOTIX's own packages: dependencies still come from the machine's repositories.", "Doc vs code.") + \
    p("The " + c(".run") + " wraps these: " + c("sudo sh remotix-X.Y.Z-R.run") + " runs " + c("install") + "; "
      + c("check") + " and " + c("tui") + " are passed through, and " + c("version") + " prints the release "
      "(" + rif("The .run file format") + ").")

S_RUN_FLOW = flow([
    ("The .run file", "run.sh: sha256, extract", "navy"),
    ("remotix-install", "install --bundle …", "blue"),
    ("Check + plan", "phases 0-3, simulation", "blue"),
    ("Proceed? [y/N]", "one consent", "amber"),
    ("Packages", "the manager installs", "dark"),
    ("Start, verify", "service, then checks", "green"),
], "«FIG» — An installation from the .run file", width=900)

S_RUNTIME = p("What happens when the administrator runs the " + c(".run") + ". The engine stays on the machine afterwards "
              "as the " + c("remotix-install") + " package, so " + c("status") + " and " + c("uninstall") + " work "
              "without the " + c(".run") + ".", lead=True) + S_RUN_FLOW + steps([
    c("run.sh") + " checks it is root (for " + c("install") + " and " + c("tui") + "), extracts the payload into "
    + c("/var/tmp/remotix-run.XXXXXX") + ", verifies the payload sha256 written in the header by the release, and runs "
    + c("remotix-install install --bundle <dir>/packages") + ". The folder is removed on exit.",
    c("sistemaAperta()") + ": an unfinished operation is rolled back (installation, upgrade) or completed "
    "(uninstallation) first; then the command starts again from scratch, with no automatic retry.",
    "Phase 0 TRUST and phase 1 PREFLIGHT (" + rif("Phase 1: the machine profile") + "), phase 2 COMPATIBILITY "
    "(" + rif("Phase 2: compatibility and what is missing") + ").",
    c("PianoInstallazione()") + " (" + rif("The installation plan") + "): the REMOTIX files for this distribution "
    "are picked from " + c("packages/<target>/") + " (" + c("PacchettiDelRun()") + ", " + c("Bersaglio()") + "), and the "
    "package manager simulates the transaction with the desktop dependencies.",
    "The plan is printed: steps with their reversibility, then “What the package manager will do (its own simulation)”, "
    "the declared group enrolment, conditions, and what is not done. A BLOCKING item ends here: “REMOTIX is not "
    "installed: nothing was touched.”",
    c("Proceed? [y/N]") + " is read from stdin; only " + c("y") + " or " + c("yes") + " proceed. The plan is written "
    "to " + c("/var/lib/remotix/plans/<id>.json") + " and applied with the consent recorded as “by hand, --approve”, by "
    + c("SUDO_USER") + " (or " + c("USER") + ", " + c("LOGNAME") + ", the uid).",
    c("Motore.Applica()") + " walks the states (" + rif("Operation states") + "); at the end the CLI prints the "
    "operation and its folder and, for an installation, the router reminder: forward the port TCP and UDP (no UPnP).",
]) + note("on a machine where a CONFIRMED installation exists the same command is an <b>upgrade</b>: the plan holds only "
          "the package step (groups, port and service are already there). If the simulation says every file of the "
          + c(".run") + " is already installed at that version, it prints “REMOTIX X is already installed: nothing to "
          "do.” and exits 0.", "Upgrade.")

STATI = fig(
    "".join(box(16 + i * 126, 30, 112, 40, s, "", "blue", 11.5) for i, s in enumerate(
        ["NEW", "TRUSTED", "EXAMINED", "ASSESSED", "PLANNED", "APPROVED", "ACQUIRED"]))
    + "".join(arrow(16 + i * 126 + 113, 50, 16 + (i + 1) * 126 - 1, 50) for i in range(6))
    + box(268, 96, 364, 40, "BLOCKED · REFUSED", "", "amber", 12)
    + arrow(198, 72, 300, 94, "#d97706", True) + arrow(576, 72, 520, 94, "#d97706", True)
    + text(450, 152, "final; from phases 0-5: nothing was touched", 10.5, "#9a3412")
    + path([(828, 72), (828, 172), (72, 172), (72, 192)], "#0050C0")
    + text(760, 165, "6 INSTALLATION", 10.5, "#003a90", "700")
    + box(16, 194, 112, 40, "RUNNING", "", "navy", 11.5)
    + box(196, 194, 112, 40, "APPLIED", "", "navy", 11.5)
    + box(376, 194, 112, 40, "VERIFYING", "", "navy", 11.5)
    + box(556, 194, 112, 40, "VERIFIED", "", "navy", 11.5)
    + box(716, 182, 168, 34, "CONFIRMED", "", "green", 11.5)
    + box(716, 222, 168, 34, "CONFIRMED_WITH_CONDITIONS", "", "green", 9.5)
    + arrow(129, 214, 195, 214) + arrow(309, 214, 375, 214) + arrow(489, 214, 555, 214)
    + arrow(669, 210, 715, 199) + arrow(669, 218, 715, 238)
    + box(16, 300, 112, 40, "INTERRUPTED", "", "dark", 10.5)
    + arrow(58, 236, 58, 298, "#475569", True) + arrow(86, 298, 86, 236, "#475569")
    + box(196, 300, 472, 40, "ROLLING_BACK — the log walked backwards", "", "amber", 11.5)
    + arrow(129, 320, 195, 320) + arrow(120, 236, 230, 298, "#d97706")
    + arrow(252, 236, 300, 298, "#d97706") + arrow(432, 236, 432, 298, "#d97706") + arrow(612, 236, 560, 298, "#d97706")
    + box(716, 284, 168, 34, "ROLLED_BACK", "", "dark", 11.5)
    + box(716, 324, 168, 34, "PARTIALLY_ROLLED_BACK", "", "dark", 10)
    + arrow(669, 314, 715, 302) + arrow(669, 328, 715, 340),
    900, 370, "«FIG» — The operation states (stati.go): solid arrows are the only valid transitions; orange: the rollback")

S_STATES = p("An operation (installation, upgrade, uninstallation) has an identifier — the UTC time plus 4 random bytes, "
             "e.g. " + c("20261010T081500Z-1a2b3c4d") + " (" + c("nuovoID()") + ") — and one state, kept in "
             + c("<state-dir>/<id>/state") + ". " + c("Valida()") + " allows only the transitions of the design; any other "
             "is RX-STATO-002, an engine defect. No state is skipped.", lead=True) + STATI + \
    table(["State", "Progress text", "Final", "Meaning"], [
        [c("NEW"), "new", "", "Folder created, plan copied in."],
        [c("TRUSTED"), "trust checked", "", "Phase 0: catalogue read and understood (" + c("trust.json") + ")."],
        [c("EXAMINED"), "machine examined", "", "Phase 1: " + c("profile.json") + "."],
        [c("ASSESSED"), "compatibility assessed", "", "Phase 2: " + c("compatibility.json") + "."],
        [c("PLANNED"), "plan checked", "", "Phase 3: every step type known, fingerprint recomputed and equal "
         "(else BLOCKED, RX-PIANO-001)."],
        [c("APPROVED"), "plan approved", "", "Phase 4: no BLOCKING item, approval matching the plan digest ("
         + c("approval.json") + ")."],
        [c("ACQUIRED"), "everything needed is ready", "", "Phase 5: " + c("resolved-set.json") + " written (the real "
         "resolution happens inside the package step)."],
        [c("RUNNING"), "applying the plan", "", "Phase 6: the steps, through the write-ahead log."],
        [c("INTERRUPTED"), "found interrupted", "", "A run died in RUNNING, or a step done earlier was undone by someone "
         "else (RX-RIPRESA-001)."],
        [c("APPLIED"), "plan applied", "", "Every step DONE."],
        [c("VERIFYING"), "verifying", "", "Phase 7: every step re-checked, plus the platform checks."],
        [c("VERIFIED"), "verified", "", "Every required check PASS."],
        [c("CONFIRMED"), "CONFIRMED", pill("final", "ok"), "Installed and verified, no condition."],
        [c("CONFIRMED_WITH_CONDITIONS"), "CONFIRMED WITH CONDITIONS", pill("final", "ok"), "Installed and verified, "
         "with conditions (" + c("C-…") + ") that stay in the certificate."],
        [c("ROLLING_BACK"), "rolling back", "", "The log walked backwards (" + c("annullaTutte()") + ")."],
        [c("ROLLED_BACK"), "ROLLED BACK: the machine is as it was", pill("final", "off"), "Everything REMOTIX did is "
         "undone."],
        [c("PARTIALLY_ROLLED_BACK"), "PARTLY ROLLED BACK", pill("final", "off"), "Some step could not be undone; the "
         "exact list is in the certificate (RX-AZIONE-002)."],
        [c("BLOCKED"), "BLOCKED", pill("final", "off"), "Nothing was touched; the code says why."],
        [c("REFUSED"), "REFUSED: nothing was touched", pill("final", "off"), "No (valid) consent: RX-PIANO-003 or "
         "RX-PIANO-005."],
    ], "«TAB» — States: name in the files, text printed by the progress (" + c("state.*") + " in "
       + c("testi.go") + ")") + \
    p("Only one engine runs at a time: " + c("Blocca()") + " takes an exclusive " + c("flock") + " on "
      + c("<state-dir>/.serratura") + " (RX-STATO-003 if busy); the kernel releases it if the process dies, so a "
      "resume never finds an orphan lock. At most one operation is ever open, and " + c("Applica()") + " refuses to "
      "start next to one (RX-STATO-001).") + \
    note("installed is not certified. CONFIRMED_WITH_CONDITIONS on a COMPATIBLE platform is a successful installation, "
         "but not a certified combination; and an UNKNOWN check never counts as PASS (" + rif("Verification and the certificate")
         + ").", "Rule.")

FILES_TREE = tree([
    "/var/lib/remotix/",
    "├── operations/            # --state-dir",
    "│   ├── .serratura         # flock: one engine at a time",
    "│   └── <id>/              # one folder per operation",
    "│       ├── state          # the current state, one line (atomic rename)",
    "│       ├── log.jsonl      # the write-ahead log",
    "│       ├── plan.json · trust.json · profile.json · compatibility.json",
    "│       ├── approval.json · resolved-set.json · resolved-set-<step>.json",
    "│       ├── check.json     # the verification report",
    "│       ├── certificate.json · certificate.txt",
    "│       ├── fingerprint-now.json   # only when the fingerprint did not match",
    "│       └── <backups>      # copies taken by write-file and remove-user-logs",
    "├── plans/<id>.json        # the plan as approved by install / the TUI",
    "├── installation.json      # marker: the CONFIRMED installation operation",
    "├── recorded-versions.json # written by post-upgrade",
    "├── gruppi-iscritti.jsonl  # written by the product at first connection",
    "├── certificati/ · ban     # the product's own state (package scripts)",
], "«FIG» — What the engine (and the product) keep under " + c("/var/lib/remotix"))

S_OBJECTS = p("The engine produces and consumes seven JSON objects, all with " + c('"format": "remotix-install/3"')
              + " (" + c("Formato") + " in " + c("formato.go") + ") and an " + c("object") + " field. "
              + c("LeggiJSON()") + " refuses an object of another format; every write goes through "
              + c("ScriviAtomico()") + ": temporary name in the same folder, " + c("fsync") + ", rename, "
              + c("fsync") + " of the folder — a reader sees the old file or the new one, never half.", lead=True) + \
    table(["Object", "File", "Produced by", "Contents"], [
        ["Machine profile", c("profile.json"), "PREFLIGHT", "Every fact with state DETECTED, VERIFIED or UNKNOWN, its source "
         "and note; the messages; the programs run."],
        ["Compatibility report", c("compatibility.json"), "COMPATIBILITY", "Per desktop: level, conditions, reasons; "
         "what is missing; dependencies; unknowns; catalogue reference."],
        ["Plan", c("plan.json"), "PLANNING", "Kind (installation, upgrade, uninstallation), steps, fingerprint, "
         "conditions, " + c("not_done") + ", " + c("declared") + ", the simulated " + c("packages") + ", "
         + c("dependencies") + ", " + c("approval") + "."],
        ["Resolved set", c("resolved-set-<step>.json"), "the package step", "Name, version, architecture, origin "
         "(" + c("file") + " or the repository), result (new, upgraded, present) — from the manager's simulation."],
        ["Execution log", c("log.jsonl"), "INSTALLATION and rollback", "The write-ahead log, one event per line."],
        ["Verification report", c("check.json"), "VERIFICATION", "Each check with PASS, FAIL, UNKNOWN or N.A., "
         "required or not; conditions born from verification."],
        ["Certificate", c("certificate.json") + " + " + c(".txt"), "COMMIT / ROLLBACK", "Final state, kind, engine "
         "version and digest, catalogue version and digest, trust, plan digest, resolved-set digest, fingerprint, "
         "checks, conditions, leftovers, indirect changes."],
    ], "«TAB» — The seven objects of the engine") + FILES_TREE + \
    p("The plan digest (" + c("Piano.Digest()") + ") is the sha256 of the canonical JSON of the plan <i>without</i> the "
      "approval; the approval carries that digest, so a plan changed after it was shown is refused (RX-PIANO-005).") + \
    warn("the certificate's " + c("product") + " field is always the text “none: engine test plan (T4)” ("
         + c("cert.prodotto_prova") + "), a leftover of the T4 test plan; the installed product version is not "
         "written in it.", "Known gap.")

WAL = seq([("Engine", "eseguiTutte()", "navy"), ("log.jsonl", "write-ahead log", "dark"), ("Step", "Azione", "blue"),
           ("Machine", "files, D-Bus, manager", "dark")], [
    (0, 2, "Fotografa(): state before, origin"),
    (0, 1, "INTENT {state_before, origin} + fsync"),
    (0, 2, "Fai(before)"),
    (2, 3, "the effect"),
    (0, 2, "Controlla(): COMPLETE?"),
    (0, 1, "DONE {result, detail} + fsync"),
    ("sep", "after a crash: the last line of each step decides"),
    (0, 2, "INTENT without DONE → Controlla()"),
    (2, 0, "COMPLETE → DONE · ABSENT → redo · HALF_DONE → repair/undo, redo", True),
], "«FIG» — One step through the write-ahead log", width=900)

S_LOG = p("Every step runs in four beats, and the log records them before the engine moves on: " + c("Registro.Scrivi()")
          + " appends one JSON line and calls " + c("fsync") + " before returning; a new log also syncs its folder.",
          lead=True) + WAL + \
    table(["Last line of the step", "What happened", "What the walk does"], [
        ["none", "not started", "Takes the state before, writes INTENT, does it, checks, writes DONE."],
        [c("INTENT") + " without " + c("DONE"), "started; maybe finished, maybe not, maybe half", "Calls "
         + c("Controlla()") + ": COMPLETE ⇒ writes DONE; ABSENT ⇒ does it again; HALF_DONE ⇒ the package step "
         "runs the manager's own repair (" + c("Riparabile") + "), others are undone, then redone; FOREIGN ⇒ "
         "INTERRUPTED with RX-RIPRESA-001."],
        [c("DONE"), "finished", "Re-checks it is still COMPLETE; if not, someone undid it: INTERRUPTED, RX-RIPRESA-001."],
        [c("FAILED"), "failed", "The operation goes to ROLLING_BACK (RX-AZIONE-001)."],
    ], "«TAB» — How the walk reads the log (" + c("eseguiTutte()") + ")") + \
    table(["Event", "Written when"], [
        [c("STATE"), "every transition (" + c("from") + ", " + c("to") + ", code, detail)"],
        [c("INTENT"), "before a step acts, with " + c("state_before") + " and " + c("origin")],
        [c("DONE") + " · " + c("FAILED"), "after the step, with " + c("state_after") + " or the code"],
        [c("ROLLBACK_INTENT") + " · " + c("ROLLED_BACK") + " · " + c("ROLLBACK_FAILED"), "the same three beats while undoing"],
        [c("NOTE"), "a message attached to the operation (e.g. RX-RIPRESA-003, RX-RIPRESA-001)"],
        [c("COMMAND"), "every program of the closed list run while the operation is open (R41)"],
    ], "«TAB» — The event types of " + c("log.jsonl")) + \
    p("A line cut in half by a crash is removed when the log is reopened and reported as RX-RIPRESA-003: lines are "
      "whole or absent, and without its line a thing did not happen. The <i>first</i> INTENT of a step is the one that "
      "counts (" + c("Registro.Intenzione()") + "): re-photographing the machine after an effect would mistake our own "
      "change for a PREEXISTING one and never undo it.") + \
    p("Rolling back (" + c("annullaTutte()") + ") walks the steps in reverse: a step never started is skipped, a "
      "PREEXISTING one is left untouched, one that is already undone is recorded as such, one changed by someone else "
      "is left and listed; otherwise ROLLBACK_INTENT, " + c("Annulla()") + ", " + c("Annullata()") + ". Whatever could "
      "not be undone makes the final state PARTIALLY_ROLLED_BACK.") + \
    p("The engine tests kill the process at named points (" + c("PuntoDiProva") + ": before/after intent, after effect, "
      "after done, during rollback) and resume (" + c("ripresa_test.go") + "). In the shipped binary the hook is always "
      "nil: no variable or option can turn it on (R13).")

S_ACTIONS = p("A plan step (" + c("AzionePiano") + ") carries its id, type, parameters, a description, and three texts "
              "written when the plan is made: how it is done, how it is verified, how it is rolled back. Undo is born "
              "with the step. Each type implements " + c("Azione") + ": " + c("Fotografa") + ", " + c("Fai") + ", "
              + c("Controlla") + " (COMPLETE, ABSENT, HALF_DONE or FOREIGN), " + c("Annulla") + ", " + c("Annullata")
              + ", " + c("Vincoli") + " (its fingerprint elements). Every method is idempotent.", lead=True) + \
    table(["Type", "Reversibility", "Do", "Undo", "Used by"], [
        [c("install-packages"), "BEST_EFFORT", "The manager installs the " + c(".run") + " files and the named "
         "dependencies in one transaction; the simulation done in " + c("Fotografa") + " is the resolved set.",
         "Removes the NEW packages only, after simulating; upgraded ones stay and are declared INDIRECT.",
         "installation, upgrade"],
        [c("add-user-to-group"), "EXACT", c("gpasswd -a user group") + "; already a member (also as primary group) ⇒ "
         "PREEXISTING.", c("gpasswd -d") + ", only if REMOTIX added them.", "installation"],
        [c("write-file"), "EXACT", "Saves the old file, writes " + c(".<name>.remotix-nuovo") + ", fsync, rename.",
         "Puts the saved file back byte for byte (or removes it), removes created folders left empty.",
         "installation (non-default port)"],
        [c("start-service"), "EXACT", c("EnableUnitFiles") + " and " + c("StartUnit") + " on D-Bus; done only when "
         "active and the port listens on TCP and UDP (waits up to 60 s: the certificate is generated at first start).",
         c("StopUnit") + ", " + c("DisableUnitFiles") + " — only what REMOTIX did.", "installation"],
        [c("enable-unit"), "EXACT", c("EnableUnitFiles") + " (optionally start).", c("DisableUnitFiles") + " if it was not "
         "enabled.", "no new plan (kept to undo older installations)"],
        [c("close-sessions"), "IRREVERSIBLE", "logind " + c("TerminateSession") + " on sessions whose PAM service is "
         + c("remotix") + "; SIGTERM after 10 s, SIGKILL after 20 s (" + c("KillSession") + ", inside the session); "
         "the desktop units of the user manager are stopped for people with no other graphical session.",
         "none: unsaved work is lost", "uninstallation"],
        [c("undo"), "as the original step", "The original step's " + c("Annulla") + ", with its folder and its "
         "state before.", "The original step's " + c("Fai") + " (a failed uninstallation reinstalls).", "uninstallation"],
        [c("remove-membership"), "EXACT", c("gpasswd -d") + " for a group enrolment the product recorded at first "
         "connection.", c("gpasswd -a") + ".", "uninstallation"],
        [c("remove-user-logs"), "EXACT", "Removes " + c("~/.local/state/remotix/sessione.log") + " in every home "
         "(and the folder if left empty), after copying it into the operation folder.", "Puts the files back with "
         "permissions and owner.", "uninstallation"],
    ], "«TAB» — The step types the engine registers (" + c("registraTipo()") + ")") + \
    table(["Reversibility", "Meaning"], [
        [c("EXACT"), "Back to the state before, byte for byte."],
        [c("BEST_EFFORT"), "Back, but not necessarily to the same state (a dependency removed only if nobody else needs it)."],
        [c("NEEDS_SNAPSHOT"), "Reversible only with a system snapshot. No current step uses it."],
        [c("IRREVERSIBLE"), "Cannot be undone; it has its own line in the plan."],
    ], "«TAB» — Reversibility classes (" + c("Reversibilita") + ")") + \
    table(["Origin", "Example", "Rollback"], [
        [c("DIRECT"), "a person put in " + c("render") + " by REMOTIX", "undoes it"],
        [c("INDIRECT"), "a library upgraded because REMOTIX needs the new one", "never downgrades it: declares it in the "
         "certificate"],
        [c("PREEXISTING"), "the person was already in " + c("video"), "never touches it"],
        [c("CONCURRENT"), "the administrator changed the same thing meanwhile (FOREIGN)", "never touches it; the "
         "operation stops"],
    ], "«TAB» — The origin of a change decides how far rollback may go (§6.6.4)") + \
    p("The promise, as the code implements it: everything REMOTIX did directly is undone; what happened indirectly is "
      "declared; what was there before is not touched. " + c("azioni_dichiarate.go") + " keeps a mechanism for step types "
      "the engine knows but cannot run yet (RX-AZIONE-004, stopping before touching anything); its list is empty today.")

S_FINGERPRINT = p("A plan is valid only on the machine it was made on. Before applying, " + c("CalcolaImpronta()")
                  + " recomputes the binding fingerprint and compares its digest with the plan's; a difference blocks "
                  "with RX-PIANO-001 and writes " + c("fingerprint-now.json") + ", and the detail lists what was in the "
                  "plan and what is there now.", lead=True) + \
    table(["Binding — if it changes, the plan is void", "Recorded only"], [
        ["profile facts with prefix " + ", ".join(c(x) for x in ["distro.id", "distro.version", "distro.variant",
         "system.arch", "system.systemd", "desktop.", "gpu.", "h264.", "selinux", "firewall.", "group.video",
         "group.render", "repo."]), c("system.name") + ", " + c("system.kernel") + ", " + c("distro.name")],
        [c("package.<name>") + " for the packages the plan depends on; " + c("engine=") + " and " + c("catalog=")
         + " versions", ""],
        ["each step's " + c("Vincoli()") + ": the version of every named dependency, the " + c(".run") + " file names, "
         "unit and service states, file sha256, group membership", ""],
    ], "«TAB» — The machine fingerprint (" + c("piano.go") + ")") + \
    p("The digest is the sha256 of the sorted elements, one per line. With the " + c("install") + " flow the plan is made "
      "and applied seconds apart, so the check catches a machine changed between the question and the answer; it is "
      "also why the plan stays in the operation folder as a document of what was done.")

FACTS = [
    [c("distro.id") + ", " + c("distro.id_like") + ", " + c("distro.version") + ", " + c("distro.variant") + ", "
     + c("distro.name") + ", " + c("distro.family") + ", " + c("distro.immutable"), c("/etc/os-release") + " or "
     + c("/usr/lib/os-release") + "; family from ID and ID_LIKE; immutable from " + c("/run/ostree-booted") + ", "
     "VARIANT_ID or ID", "RX-DISTRO-001"],
    [c("system.arch") + ", " + c("system.kernel") + ", " + c("system.systemd") + ", " + c("system.name"),
     "the engine's GOARCH, " + c("/proc/sys/kernel") + ", " + c("/run/systemd/system"), "RX-SYSTEMD-001"],
    [c("desktop.<gnome|kde|xfce|lxqt>") + ", " + c("package.<name>"), "dpkg status file, pacman local db, one "
     + c("rpm -q") + " call on RPM families; binaries as a fallback", "—"],
    [c("repo.rpmfusion") + ", " + c("repo.rpmfusion-nonfree") + ", " + c("repo.epel") + ", " + c("repo.packman"),
     "an <i>enabled</i> section of a " + c(".repo") + " file (a disabled " + c("rpmfusion-nonfree-steam") + " does not "
     "count: measured on fedora44-gnome, 30 Sep)", "RX-MANCA-002 (phase 2)"],
    [c("gpu.<node>.driver") + ", " + c(".vendor") + ", " + c(".group") + ", " + c(".mode") + ", " + c("gpu.nodes")
     + ", " + c("gpu.nvidia_proprietary"), c("/sys/class/drm") + ", the node's group and mode; the " + c("nvidia")
     + " module", "RX-GPU-002…006"],
    [c("encoding.routes") + ", " + c("encoding.vulkan.icd") + ", " + c("h264.driver_va") + ", "
     + c("h264.driver_family") + ", " + c("h264.gpu"), "Vulkan ICD files, VA driver folders, the installed driver "
     "packages (" + c("famigliaDriver()") + ")", "RX-H264-001…004"],
    [c("selinux") + ", " + c("apparmor"), c("/sys/fs/selinux/enforce") + ", the apparmor module parameter",
     "RX-SELINUX-001"],
    [c("port.N.tcp_free") + ", " + c("port.N.udp_free") + ", " + c("port.N.reachable"), c("/proc/net/tcp*") + ", "
     + c("/proc/net/udp*") + "; reachability is always UNKNOWN", "RX-FW-003, RX-FW-005"],
    [c("firewall.type") + ", " + c("firewall.zone") + ", " + c("firewall.port_N_proto"), "firewalld over D-Bus; ufw "
     "files (root needed); nftables seen through systemd", "RX-FW-001, RX-FW-002"],
    [c("pam.base") + ", " + c("pam.base_missing") + ", " + c("pam.faillock") + ", " + c("pam.remotix") + ", "
     + c("pam.pam_systemd"), "the family's login stack files and module folders", "RX-PAM-001…004"],
    [c("openssl.version"), "the package, or the library", "RX-OPENSSL-001/002"],
    [c("logind.kill_user_processes"), "logind over D-Bus (VERIFIED), else the configuration files (DETECTED)",
     "RX-LOGIND-001/002"],
    [c("group.video") + ", " + c("group.render"), c("/etc/group"), "RX-GRUPPI-001"],
    [c("fonts.scalable"), "count of ttf/otf/ttc/pfb files in the font folders (no " + c("fc-list") + ": closed list)",
     "drives the font dependency"],
]

S_PREFLIGHT = p("Phase 1 builds the machine profile in <b>read-only</b> mode (R1): no function in "
                + c("preflight.go") + " writes, creates, renames or changes permissions. It reads files, asks systemd, "
                "logind and firewalld over D-Bus (properties and queries only), and runs one program, " + c("rpm -q")
                + " on RPM families, recorded in the profile. The proof is " + c("installatore/prove/r1-contenitori.sh")
                + ": a fingerprint of " + c("/etc") + " before and after " + c("check") + ", in one container per "
                "family, must be identical.", lead=True) + \
    table(["Facts", "Source", "Codes it can raise"], FACTS, "«TAB» — The facts of the profile (" + c("Preflight()")
          + ")") + \
    p("Each fact has a state: <b>DETECTED</b> (seen: “PipeWire is installed”), <b>VERIFIED</b> (actually tested: “the "
      "card encoded a frame”) or <b>UNKNOWN</b> (the tool is missing, permission denied, time out). The rule the whole "
      "engine follows: a DETECTED fact never makes a PASS, and UNKNOWN is never “fine” — it is the lesson of GNOME 50's "
      "false green (fasi/17 §5.1).") + \
    table(["Program", "Path(s)", "Why it is allowed"], [
        [c("apt-get") + ", " + c("dnf") + " (" + c("dnf5") + "), " + c("zypper") + ", " + c("pacman"), "absolute",
         "the package managers: rule 1 of the engine"],
        [c("rpm") + ", " + c("dpkg") + ", " + c("dpkg-deb"), "absolute", "the base of the managers: rpm's database cannot "
         "be read without it; " + c("dpkg --audit") + " and " + c("--configure -a") + " are the repair"],
        [c("gpasswd"), "absolute", "group membership (keeps gshadow and the lock)"],
        [c("ufw"), "absolute", "ufw has no D-Bus: reading its rules (" + c("ufw show added") + ")"],
        [c("remotix"), c("/usr/libexec/remotix/remotix") + ", " + c("/usr/lib/remotix/remotix") + " (Arch)",
         c("--prova-codifica") + ", the encoding test of 7a"],
        [c("apt-cache") + ", " + c("pacman-key") + ", " + c("usermod"), "absolute", "still in the list, no longer called "
         "by any code path (leftovers of the signed archive and of T6)"],
    ], "«TAB» — The closed list of programs (" + c("programmiAmmessi") + " in " + c("ambiente.go") + ")") + \
    p("Every call goes through " + c("eseguiDavvero()") + ": absolute path, fixed arguments, an environment of three "
      "variables (" + c("LC_ALL=C") + ", a fixed " + c("PATH") + ", " + c("DEBIAN_FRONTEND=noninteractive") + "), no "
      "stdin, a timeout (45 minutes for the package managers), and an annotation " + c("path args ⇒ exit") + " in the "
      "profile or in the log. A name outside the list returns " + c("ErrNonAmmesso") + " without running anything.")

S_ROUTES = p("REMOTIX encodes only on the graphics card (DECISIONS §10.27: “no CPU without a card”), so a machine "
             "without a card that can encode is refused before anything is touched. The route is chosen by capability, "
             "not by brand: " + c("StradeCodifica") + " lists them in order of preference, and the verdict is “at least "
             "one active route has a capable card”.", lead=True) + \
    table(["Route", "Cards", "What the engine reads (no program, no device opened)"], [
        [c("vulkan") + " (Vulkan Video, tried first by the product)", "AMD with the RADV ICD where the distribution's "
         "Mesa encodes (catalogue " + c("vulkan_codifica") + "); NVIDIA with the proprietary driver and its ICD",
         "ICD files in " + c("/usr/share/vulkan/icd.d") + " and " + c("/etc/vulkan/icd.d") + " → "
         + c("encoding.vulkan.icd")],
        [c("vaapi") + " (VA-API, libva)", "Intel and AMD, unless the platform's Mesa has no VA-API "
         "(" + c("amd_senza_vaapi") + ") or the installed driver is a build without H.264", "VA driver folders and the "
         "driver packages: " + c("famigliaDriver()") + " tells “with”, “without” or unknown"],
    ], "«TAB» — The encoding routes (" + c("strade.go") + ")") + \
    table(["Verdict (" + c("VerdettoScheda()") + ")", "When"], [
        ["none (go on)", "an active route has a capable card — or the nodes could not be read (not a refusal)"],
        ["RX-GPU-003", "no render node at all"],
        ["RX-GPU-004", "NVIDIA with the proprietary driver and no nvidia ICD (it encodes only through Vulkan)"],
        ["RX-GPU-006", "an Intel or AMD card is there but no route makes it encode (AMD on RHEL; a VA driver built "
         "without H.264; no RADV with codecs)"],
        ["RX-GPU-005", "any other card"],
    ], "«TAB» — The card verdict, from the most precise case to the most general") + \
    p("Intel is never counted on the Vulkan route: ANV encodes only behind " + c("ANV_DEBUG=video-encode") + ", "
      "experimental (§10.27). Which route really encoded is known only after installation, from the " + c("strada")
      + " field of " + c("remotix --prova-codifica") + " (" + rif("Verification and the certificate") + "). The minimum "
      "Mesa with RADV encoding by default is not measured (Mesa 25.0.7 works, measured 1 Oct 2026 on the test server's "
      "Radeon RX 6800).") + \
    warn(c("codiceH264()") + " in " + c("preflight.go") + " still raises RX-H264-003 (Fedora) and RX-H264-004 (openSUSE), "
         "which " + c("codici.go") + " marks as retired by §10.36: where a driver warning was meant, the "
         "administrator reads an INFO line with a “(retired…)” text. The verdict above is what blocks; these lines are "
         "cosmetic.", "Code defect.")

S_COMPAT = p("Phase 2 (" + c("Valuta()") + ") judges the machine against the catalogue, desktop by desktop, and "
             "collects in one list everything that is missing. An empty list means REMOTIX can be installed.", lead=True) + \
    steps([
        "Reasons that hold for every desktop: an excluded version (RX-COMPAT-001, with the first supported version of "
        "that distribution), an immutable system (RX-COMPAT-003), no systemd or OpenSSL below "
        + c(CAT["requisiti"]["openssl_minima"]) + " (RX-COMPAT-007), a platform not in the catalogue (RX-COMPAT-002), a "
        "derivative below its minimum, and the card verdict.",
        "Platform repositories REMOTIX itself needs (on Alma: EPEL): each missing one is RX-MANCA-002.",
        "For each supported desktop: the conditions of H.264, the desktop's components that are absent become "
        "<b>dependencies</b> (labwc, wlr-randr, breeze6-wallpapers), a scalable font is added when the desktop runs "
        "under labwc and " + c("fonts.scalable") + " is 0 (the catalogue's " + c("carattere_scalabile") + " for the "
        "family, e.g. " + c(CAT["carattere_scalabile"]["debian"]) + "), limits become " + c("C-LIMITE") + ", a 3D need "
        "becomes " + c("C-HARDWARE") + " (or a refusal with no node), and a version below the minimum is RX-COMPAT-006.",
        "The level: UNSUPPORTED if there is any reason; CERTIFIED only on a matrix platform (not a derivative) whose "
        "catalogue entry records a full green run (" + c("giro_intero") + "); COMPATIBLE otherwise.",
        "Missing pieces of an <i>installed</i> supported desktop become RX-MANCA-003; no installed supported desktop at "
        "all, when one is possible, is RX-MANCA-001 with the minimum versions.",
    ]) + \
    table(["Condition", "Meaning", "Where it comes from today"], [
        [c("C-LIMITE"), "a function is missing or not confirmed", "catalogue " + c("limiti") + "; encoding or PAM check "
         "UNKNOWN"],
        [c("C-HARDWARE"), "a card requirement", c("richiede_3d") + " (KDE on Leap 16); an NVIDIA card left out"],
        [c("C-AMMINISTRATORE"), "a manual step is needed", "the firewall closes the port, or cannot be read"],
    ], "«TAB» — Conditions in use (the older " + c("C-DEPOSITO") + ", " + c("C-COMPONENTE") + ", " + c("C-RIPIEGO")
       + ", " + c("C-DESKTOP") + " of §6.6.8 are no longer produced)") + \
    note("every desktop of every platform is COMPATIBLE today, none CERTIFIED: the catalogue's " + c("giro_intero")
         + " is empty everywhere because the full run (T10) on the 26 combinations has not been done with this engine. "
         "The matrix platforms are “in the matrix, not yet certified”.", "Current state.") + \
    p("Desktop dependencies are ordinary dependencies of REMOTIX (user's decision of 10 Oct 2026): they are passed to "
      "the same package-manager transaction, shown under “Dependencies of REMOTIX” with “needed by REMOTIX for XFCE”, "
      "and if the distribution does not have them the simulation fails and the plan stops with RX-PACCHETTI-005.")

S_CATALOGUE = p("The catalogue is " + c("installatore/catalogo/catalogo.json") + ", embedded in the binary with "
                + c("go:embed") + " (" + c("catalogo.go") + "). It is data, so its keys stay Italian and its format is "
                + c(CAT["formato"]) + "; its texts (reasons, notes, limits) are English. A new catalogue is a new release "
                "with a higher " + c("sequenza") + ".", lead=True) + \
    table(["Key", "Contents"], [
        [c("formato") + ", " + c("versione") + ", " + c("sequenza") + ", " + c("emesso"), "format, version (date-based, "
         "e.g. " + c(CAT["versione"]) + "), sequence, issue date"],
        [c("motore_minimo"), "the oldest engine that understands it (RX-TRUST-003 otherwise)"],
        [c("requisiti"), "OpenSSL and desktop minimums, systemd required"],
        [c("depositi"), "third-party repositories by key, with a display name"],
        [c("piattaforme"), "id (os-release ID), versions, label, family, " + c("matrice") + ", " + c("giro_intero")
         + ", derivatives, H.264 facts, repositories, desktops (" + c("supportato") + ", " + c("componenti") + ", "
         + c("limiti") + ", " + c("richiede_3d") + ", " + c("serve_carattere") + ", notes)"],
        [c("escluse") + ", " + c("fuori_sempre"), "excluded versions with the reason; what is always out"],
        [c("componenti_minimi"), "the table of minimum component versions for the manual"],
        [c("carattere_scalabile"), "the font package per family"],
    ], "«TAB» — The catalogue's keys (" + c("Catalogo") + " in " + c("compatibilita.go") + ")") + \
    tabella_piattaforme() + tabella_escluse() + tabella_minimi() + \
    warn("Linux Mint 23 is a compatible derivative in the catalogue, but " + c("Bersaglio()") + " maps its os-release to "
         + c("linuxmint23") + ", a folder the " + c(".run") + " does not have: the plan stops with RX-MANCA-004. Fedora 43 "
         "(outside the matrix) has the same fate. Rocky and RHEL map to " + c("alma10") + ", Manjaro and EndeavourOS to "
         + c("arch") + " through ID_LIKE.", "Code finding.") + \
    p("The catalogue's component minimums and the build's disagree on two libraries: libei 1.3 here, 1.1 in "
      + c("src/Makefile") + ", " + c("packaging/debian/control") + " and " + c("packaging/rpm/remotix.spec") + "; "
      "libopus 1.4 here, 1.3 in the Makefile. Not settled yet: which one is the real floor.")

S_PLAN = p(c("PianoInstallazione()") + " is the whole installation policy in one function. REMOTIX does not modify the "
           "system, so the plan has few steps; everything else is said, not done.", lead=True) + \
    table(["#", "Step / item", "Condition", "Notes"], [
        ["—", "BLOCKING items in " + c("not_done"), "anything in " + c("Rapporto.Mancano") + ", any BLOCKING message, "
         "the reasons of the desktops if none is usable", "the plan is still built and shown, then not applied"],
        ["1", c("packages") + " — " + c("install-packages"), "the " + c(".run") + " has files for this target", "the REMOTIX files (" + c("remotix-selinux") + " only where " + c("/etc/selinux/targeted")
         + " exists) plus the desktop dependencies, in one transaction; RX-MANCA-004 if no file"],
        ["2", c("group-<user>-<group>") + " — " + c("add-user-to-group"), "not an upgrade", "every user of " + c("--users")
         + ", or every person of the machine (uid between " + c("UID_MIN") + " and 60000, a real shell), times every "
         "non-root group of the card nodes; declared in the plan"],
        ["3", c("port") + " — " + c("write-file"), "port ≠ 7447", c("/etc/remotix/remotix.conf.d/porta.conf")
         + " with " + c("REMOTIX_PORTA=N") + " (read by " + c("remotix.service") + " as an EnvironmentFile)"],
        ["4", c("service") + " — " + c("start-service"), "not an upgrade", c("remotix.service") + ", started after the "
         "checks that do not need it"],
        ["—", "firewall notice (WARNING)", "a firewall is on", "opening port N TCP and UDP is the administrator's job"],
        ["—", "suspend notice (INFO)", "always", "REMOTIX does not change how the machine suspends or powers off"],
    ], "«TAB» — The installation plan, in order") + \
    p("With the steps built, the package manager simulates the transaction (" + c("Gestore.Simula()") + "); its exact "
      "list (name, version, architecture, origin, new / upgraded / present) goes into the plan and is printed "
      "<i>before</i> the question. If the manager cannot resolve it, the plan carries RX-PACCHETTI-005 with the "
      "manager's own words. At execution the package step simulates again in " + c("Fotografa") + " and records that "
      "result as the resolved set.") + \
    note("the TUI asks only for the port and the “yes”. Repositories, the firewall, the desktop, guards and drivers "
         "are not questions any more: what is missing is said and the installation stops (§10.36).", "One question.") + \
    p("Not settled yet: whether the card groups shrink to " + c("render") + " only — " + c("video") + " also grants "
      + c("/dev/fb*") + " and webcams (§10.36); until it is measured on the four desktops the engine enrols every "
      "non-root group it finds on " + c("/dev/dri/card*") + " and " + c("renderD*") + ".")

S_MANAGERS = p("Each family has an adapter (" + c("Gestore") + " in " + c("gestore.go") + ", chosen by "
               + c("ScegliGestore()") + "): versions, simulate, install, simulate-remove, remove only the named "
               "packages, integrity, and the manager's own repair. Files from the " + c(".run") + " carry no rpm "
               "signature (the " + c(".run") + " sha256 vouches for them); packages from the machine's repositories are "
               "verified by the manager as usual.", lead=True) + \
    table(["", "apt (Debian, Ubuntu)", "dnf 4/5 (Fedora, Alma)", "zypper (openSUSE)", "pacman (Arch)"], [
        ["Simulate", c("apt-get -s install") + "; on error " + c("apt-get update") + " once and retry; a " + c("Remv")
         + " line refuses", c("dnf install --assumeno --setopt=localpkg_gpgcheck=0") + "; the table after "
         "“Transaction Summary”; " + c("@commandline") + " = file", c("zypper --xmlout install --dry-run")
         + " (+ " + c("--allow-unsigned-rpm") + " for files)", c("pacman -U/-S --needed --print")],
        ["Install", c("apt-get install") + " with " + c("--force-confdef/confold") + ", assume yes",
         c("dnf install -y") + ", local files unsigned", c("zypper --non-interactive install"),
         c("pacman -S --needed") + " for names, then " + c("-U") + " for files"],
        ["Who else would go", c("apt-get -s remove|purge"), c("dnf remove --assumeno") + "; when the solver fails, the "
         "packages named in its “Problem” lines", c("zypper remove --dry-run"), c("pacman -R --print") + "; on failure "
         "“required by X”"],
        ["Integrity", c("dpkg --audit"), "no duplicate " + c("name.arch") + " in " + c("rpm -qa"),
         c("zypper verify --dry-run"), "no " + c("/var/lib/pacman/db.lck")],
        ["Repair", c("dpkg --configure -a"), c("dnf remove --duplicates"), c("zypper verify"), "remove the stale lock, "
         "then " + c("pacman -Dk")],
        ["Tested on a real machine", "yes (VMs)", "yes on Alma (dnf 4); Fedora dnf 5 with the same parser, not re-run",
         "no", "no"],
    ], "«TAB» — The four package-manager adapters") + \
    p("Removal never uses the managers' autoremove: it would also take orphans that were there before and are not ours. "
      "Instead " + c("trattenuti()") + " simulates removing the NEW packages; those whose removal would drag along "
      "something outside our set (an upgraded package, a program installed later) are <b>kept</b> and declared "
      "(RX-PACCHETTI-006). The reason is measured: on leap16-kde (30 Sep) " + c("zypper rm") + " of a codec library "
      "would have removed 53 packages, Plasma included. A " + c("Togli()") + " that would remove anything else stops "
      "with RX-PACCHETTI-002.") + \
    warn("the text " + c("az.pacchetti.fa") + " printed as “how it is done” still describes the retired design (“resolved, "
         "everything downloaded and verified … installs from the cache, offline”). The code installs through the "
         "manager, which downloads dependencies from the machine's repositories.", "Doc vs code.")

S_VERIFY = p("Phase 7 re-runs every step's " + c("Controlla()") + " and, for an installation, the platform checks of "
             + c("ControlliPiattaforma()") + ". It runs after <i>every</i> step, the service start included.", lead=True) + \
    warn("§6.0 of fasi/17 designs the checks that do not need the service (7a: the encoding test, PAM) to run "
         "<i>before</i> switching it on, and the live ones (7b) after, so that most errors appear while undoing is "
         "cheap and nobody is connected; the step texts still say “after the checks with the service stopped (7a)”. "
         "In the code " + c("start-service") + " is an ordinary step of phase 6, and " + c("verifica()") + " runs all "
         "checks afterwards: the encoding test runs with the service already on.", "Doc vs code.") + \
    table(["Check id", "What", "Required", "PASS / FAIL / UNKNOWN"], [
        ["each step id", "the step's “how it is verified”", "yes", "COMPLETE ⇒ PASS; other ⇒ FAIL; an error ⇒ UNKNOWN"],
        [c("h264-encoding"), c("remotix --prova-codifica") + " (7a): one line of JSON (" + c("esito") + ", "
         + c("strada") + ", " + c("nodo") + ", …)", "yes", "exit 0 and “hardware” ⇒ PASS; exit 3 (no card can encode) "
         "or 1 ⇒ FAIL → rollback; unreadable answer ⇒ UNKNOWN + " + c("C-LIMITE")],
        [c("pam-resolved"), "the " + c("remotix") + " PAM file and every " + c("@include") + ", " + c("include")
         + ", " + c("substack") + " and module exist (8 levels deep; " + c("-session") + " modules optional)", "yes",
         "a missing file or module ⇒ FAIL; it does not load PAM (that would need cgo)"],
        [c("firewall-port"), "the firewall lets the port through, TCP and UDP (7b)", "no", "no firewall ⇒ PASS; "
         "firewalld zone open (also port ranges) ⇒ PASS; closed ⇒ FAIL + " + c("C-AMMINISTRATORE") + "; ufw, nftables "
         "or unreadable ⇒ UNKNOWN + " + c("C-AMMINISTRATORE")],
    ], "«TAB» — The verification checks") + \
    p("A required FAIL sends the operation to ROLLING_BACK (RX-AZIONE-003). Conditions from verification and from the "
      "compatibility report make the final state CONFIRMED_WITH_CONDITIONS. The certificate is written <i>before</i> "
      "the final state: if the process dies between the two, the resume finds VERIFIED and writes it again. Then "
      + c("installation.json") + " points to the operation (installations only).") + \
    table(["Result of " + c("status"), "When"], [
        [pill("GREEN", "ok"), "every check PASS and no condition"],
        [pill("CONDITIONAL", "snooze"), "no FAIL among the steps and no required FAIL, but an UNKNOWN or a condition"],
        [pill("RED", "off"), "a step no longer COMPLETE, or a required platform check FAIL"],
    ], "«TAB» — " + c("Certifica()") + ": the installation's checks re-run later, read only") + \
    p("Who can log in is shown at the end (TUI “WHO CAN LOG IN”): any account that can log in by ssh, with its "
      "password; root is excluded by " + c("/etc/remotix/utenti-negati") + ". The page certificate fingerprint shown is "
      "the SHA-256 of " + c("/var/lib/remotix/certificati/pagina.pem") + ".")

S_UNINSTALL = p("Uninstalling is an operation like the others, with its plan, consent, log and resume. "
                + c("PianoDisinstallazione()") + " reads the plan and log of the operation named by "
                + c("installation.json") + " and walks it backwards.", lead=True) + \
    steps([
        "For each step of the installation that was started and is not PREEXISTING, an " + c("undo") + " step: doing it "
        "is the original's undo, undoing it is the original's do — a failed uninstallation reinstalls.",
        "Right after the undo of the service, " + c("close-sessions") + ": the sessions logind lists with PAM service "
        + c("remotix") + " are terminated; a local or ssh session of the same person stays (§10.16). The administrator "
        "warns people beforehand with their own means; there is no extra question. It is IRREVERSIBLE.",
        "For each group enrolment the product recorded at first connection in " + c("/var/lib/remotix/gruppi-iscritti.jsonl")
        + " (format " + c("remotix-gruppi/1") + ", written by " + c("figlio.c") + ") that the engine did not do itself, "
        "a " + c("remove-membership") + " step.",
        "Last, " + c("remove-user-logs") + ": " + c("~/.local/state/remotix/sessione.log") + " in every home, declared "
        "in the plan with the current list.",
        "On CONFIRMED: " + c("installation.json") + " is removed; without " + c("--purge") + " the operations history "
        "stays (for support); with " + c("--purge") + " the operations folder, the enrolment file, "
        + c("recorded-versions.json") + " and " + c("/var/lib/remotix") + " if empty go too.",
    ]) + \
    p("Removing the packages removes the NEW packages of the installation's resolved set, " + c("remotix-install")
      + " included (the running engine keeps its open file). The rollback of a failed <i>installation</i> always "
      "purges; an uninstallation purges the configuration only with " + c("--purge") + " (like " + c("apt purge") + ").") + \
    warn("the uninstallation plan is built only from the original installation operation. Packages that an "
         "<i>upgrade</i> operation added as NEW (a dependency a later release needs) are in the upgrade's resolved set, "
         "not in the installation's, and are not removed by " + c("uninstall") + ".", "Code finding.")

S_INTERRUPTED = p("An operation that did not reach a final state is never left as it is and never resumed half way "
                  "(§10.36: “I don't like the idea of leaving a system half way”). " + c("sistemaAperta()") + " runs at "
                  "the start of " + c("install") + ", " + c("tui") + " and " + c("uninstall") + ".", lead=True) + \
    table(["Open operation", "What happens", "Then"], [
        ["installation or upgrade", c("Motore.Annulla()") + ": from RUNNING it passes INTERRUPTED, then ROLLING_BACK; "
         "the package step first runs the manager's repair (e.g. " + c("dpkg --configure -a") + ")",
         "the command starts again from scratch, with its own plan and question"],
        ["uninstallation", c("Motore.Riprendi()") + ": completed through the same walk", "same"],
        ["stopped before touching (NEW…ACQUIRED)", "BLOCKED with RX-RIPRESA-002", "same"],
    ], "«TAB» — Settling an unfinished operation") + \
    p("If the rollback itself cannot finish, the command stops with RX-STATO-001 and the operation's state. "
      + c("status") + " marks an open operation with “← open: remotix-install install rolls it back”.")

S_UPGRADES = p("REMOTIX is upgraded by running the newer " + c(".run") + ": " + c("install") + " sees the CONFIRMED "
               "installation and makes an <b>upgrade</b> plan with the package step only. There is no timer and no "
               "update command of ours (D14, §10.23).", lead=True) + \
    p("Packages can also change under the engine (an administrator's " + c("apt upgrade") + " pulling a dependency, a "
      "downgrade with the manager's commands). The package scripts call " + c("remotix-install post-upgrade") + ", "
      "which records the installed versions of " + c("remotix") + ", " + c("remotix-install") + ", "
      + c("remotix-selinux") + " in " + c("recorded-versions.json") + ". The package step's " + c("Controlla()")
      + " accepts a package at the resolved version, at a <i>newer</i> one (compared with the dpkg or rpmvercmp "
      "algorithm of " + c("versioni.go") + "), or at the recorded one — so " + c("status") + " stays GREEN after a "
      "legitimate system update or a rollback with the manager.") + \
    table(["Package", "Hook", "What it does"], [
        [c("remotix") + " .deb", c("postinst configure") + " with an old version", c("try-restart") + " (debhelper), "
         "then " + c("post-upgrade") + " if the engine is there"],
        [c("remotix") + " .rpm", c("%postun") + " / " + c("%posttrans"), "restart only if it was running; then "
         + c("post-upgrade")],
        [c("remotix") + " Arch", c("post_upgrade"), c("systemctl try-restart") + ", then " + c("post-upgrade")],
        [c("remotix-install"), "postinst / " + c("%posttrans") + " / " + c("post_upgrade"), c("post-upgrade")],
    ], "«TAB» — Who calls " + c("post-upgrade") + "; it always exits 0") + \
    p("The service restart does not close the desktops: they live outside the unit (" + c("KillMode=mixed")
      + ", desktops started with " + c("setsid --fork") + "), and the new server finds them again (T2, measured 10 runs "
      "out of 10 on 29 Sep 2026, fasi/17 §5.2).")

S_TRUST = p("Phase 0 answers one question: is the catalogue the right one, and does this engine understand it? After "
            "D11 was simplified (§10.21) and the signed archive was dropped (§10.36), there are no keys of our own.",
            lead=True) + \
    table(["What", "Who vouches for it", "How"], [
        ["the " + c(".run") + " file", "the administrator", "the sha256 published next to it on the REMOTIX site, over HTTPS"],
        ["the payload inside it", c("run.sh"), "the payload sha256 written into the header by the release"],
        ["the engine and its catalogue", "whoever delivered the engine", c("/usr/bin/remotix-install") + ": “the "
         "catalogue of the installed remotix-install package”; otherwise “from the REMOTIX .run file, whose sha256 is "
         "published”"],
        ["a catalogue given with " + c("--catalog"), "the administrator", "recorded as such in " + c("trust.json")
         + " and in the certificate"],
        ["dependencies from the machine's repositories", "the package manager", "the distribution's signatures, as "
         "always"],
    ], "«TAB» — The chain of trust") + \
    p("What remains for the engine: the catalogue must parse and have format " + c(CAT["formato"]) + " (RX-TRUST-004), "
      "and " + c("VersioneMotore") + " must be at least " + c("motore_minimo") + " (RX-TRUST-003). No expiry, no "
      "catalogue stored on the machine. RX-TRUST-001, 002 and 005…017 are retired. Honestly: the sha256 is worth what "
      "the site that publishes it is worth.")

TUI_CHECK = """╭─ REMOTIX 0.1.0 · Installation ────────────── Debian GNU/Linux 13 · GNOME 48 ─╮
│ ● Check  ›  ○ Plan  ›  ○ Install  ›  ○ Ready                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ System            Debian 13 · certified                         ✓ OK         │
│ Desktop           GNOME · Wayland                               ✓ OK         │
│ Graphics card     Intel card · encodes video                    ✓ OK         │
│ Video             tested on the card at the end of the          · LATER      │
│                   installation                                               │
│ Firewall          firewalld is on: open port 7447 yourself      ! WARNING    │
│ Permissions       3 people will get permission to use the       + WILL FIX   │
│                   graphics card                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ enter continue · d details · q quit                                          │
╰──────────────────────────────────────────────────────────────────────────────╯"""

TUI_PLAN = """│ Port      [ 7447 ]   TCP and UDP                                             │
│                                                                              │
│ REMOTIX   from this installer                                                │
│   + remotix               1.0-1                                              │
│                                                                              │
│ Dependencies of REMOTIX   from the distribution's own repositories           │
│   + libei1                1.3.0-1           debian/trixie                    │
│   + labwc                 0.8.3-1           needed by REMOTIX for XFCE       │
│     4 new · 0 upgraded · 1 already there                                     │
│                                                                              │
│ Users added to groups render, video   alice, bob, carol                      │
│ Service   remotix.service, started after the final check                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Proceed? y yes · n no · tab edit port · d details                            │"""

S_TUI = p("The TUI (" + c("remotix-install tui") + ", or " + c("sudo sh remotix-X.Y.Z-R.run tui") + ") is the "
          "“professional” interface of §10.31, for administrators on ssh or the console. It is Bubble Tea and lipgloss, "
          "drawn on the mockup the user approved on 10 Oct 2026 (" + c("grafica/tui-mockup/index.html") + "): a fixed "
          "frame as wide as the terminal (at least 80 columns and 12 lines, else a line says so), four steps Check › "
          "Plan › Install › Ready, a body that scrolls inside the frame, the keys at the bottom.", lead=True) + \
    code(TUI_CHECK, "text", "remotix-install tui --preview 80 — the check screen (sample data, shortened)") + \
    code(TUI_PLAN, "text", "the plan screen (body only)") + \
    table(["Screen", "Keys", "Notes"], [
        ["Check", ui("enter") + " continue (not when something is missing) · " + ui("d") + " details · " + ui("q")
         + " quit", "one row per subject (system, desktop, card, video, sign-in, users, firewall, port, permissions, "
         "audio) with a tag: OK, WARNING, MISSING, WILL FIX, LATER"],
        ["Plan", ui("y") + " yes · " + ui("n") + " no · " + ui("tab") + " edit port · " + ui("d") + " details",
         "the port box accepts digits; a new port re-examines the machine and re-plans; the packages are the manager's "
         "simulation"],
        ["Install", ui("a") + " stop and undo · " + ui("r") + " log", c("Ctrl+C") + " is ignored while working; "
         + ui("a") + " sets " + c("Motore.Fermata") + ": the current step finishes, then everything is undone "
         "(RX-AZIONE-006)"],
        ["Ready / end", ui("enter") + " close · " + ui("r") + " log · " + ui("d") + " details; on the end screens "
         + ui("s") + " save the report", "addresses, certificate fingerprint, to-do (firewall, router), who can log in, final checks; "
         + ui("s") + " writes " + c("remotix-report.json")],
    ], "«TAB» — TUI screens and keys (" + c("tui.go") + "); arrows, " + ui("j") + "/" + ui("k") + ", PgUp/PgDn, "
       "Home/End scroll") + \
    p("The TUI talks to the engine through " + c("interfaccia.Motore") + ", implemented by " + c("Sessione")
      + " in the same root process: " + c("Controlla(porta)") + " (phases 0-2 and " + c("DomandeDaFare()") + "), "
      + c("Piano(voci)") + " (" + c("PianoInstallazione()") + ", written to " + c("plans/") + "), "
      + c("Applica(digest, eventi)") + " — the approval is recorded only if the digest is the one shown — and "
      + c("Ferma()") + ". Events reach the screen as the engine's JSON lines, parsed by " + c("righeEventi")
      + ". " + c("vista.go") + " turns engine objects into plain words (“Graphics card”, “Sign-in”), grouping steps "
      "(the groups of one person = one row) with the real reversibility tag.") + \
    p("Colours come from the mockup and degrade by themselves to 256 or 16 colours, and to none with " + c("NO_COLOR")
      + " (" + c("termenv") + "); bold stays. " + c("remotix-install tui --preview N") + " prints every screen at width "
      "N with sample data, without root and without touching anything — the way to compare with the mockup and the "
      "basis of " + c("tui_test.go") + ". Not shown because the engine does not know them: the size of the packages "
      "(the simulations do not give it) and automatic suspend as a check row.")

S_TEXTS = p("All texts live in catalogues, not in the code: " + c("motore/codici.go") + " (message and remedy of each "
            "code), " + c("motore/testi.go") + " (states, steps, CLI, certificate; looked up with " + c("T(key, args…)")
            + "), " + c("interfaccia/testi.go") + " (the TUI). A missing key prints " + c("⟨key⟩") + " and is found by "
            + c("TestTesti") + ". " + c("inglese_test.go") + " fails on any Italian word or accented letter in the "
            "strings of the code and of the catalogue.", lead=True) + \
    table(["Rule", "Why"], [
        ["A code is never reused for another meaning; a wrong text is corrected, a new meaning takes a new number.",
         "The same code is in the CLI, the log, the certificate, this manual and support conversations."],
        ["Retired codes stay in " + c("codici.go") + " with a “(retired …)” text.", "Old logs name them."],
        [c("Msg()") + " panics on an unknown code; " + c("TestCodiciUsatiEsistono") + " finds it first.",
         "An unknown code is an engine defect."],
        ["Every message has a severity (INFO, WARNING, BLOCKING) and a nature (ACTION_NEEDED, RETRYABLE, RECOVERABLE, "
         "ROLLBACK_NEEDED, FATAL).", "The CLI sorts warnings by severity; BLOCKING items stop a plan."],
    ], "«TAB» — How messages are written") + \
    note("the codes keep their Italian area names (" + c("RX-MANCA") + ", " + c("RX-PIANO") + ", " + c("RX-GRUPPI")
         + "…): they are identifiers, decided in §10.35 not to change. So are the " + c("C-…") + " conditions and the "
         "catalogue keys.", "Identifiers.")

S_CODES = p("The table is generated from " + c("installatore/motore/codici.go") + " when the manual is built; the last "
            "column lists the non-test files whose code mentions the code (comments excluded). A code in force with no "
            "file is defined but never raised; a retired code with a file is still raised somewhere.", lead=True) + \
    tabella_codici()

S_TESTS = p("The engine's tests run with " + c("installatore/costruisci.sh prove") + ": " + c("gofmt -l") + ", "
            + c("go vet") + " and " + c("go test") + " in the " + c("golang:1.25") + " container, offline. The release "
            "refuses to continue on any " + c("FAIL") + " or " + c("gofmt:") + " line (" + rif("The release command")
            + ").", lead=True) + \
    table(["File", "What it proves"], [
        [c("motore_test.go"), "states and transitions, the walk on a fake machine, certificate"],
        [c("ripresa_test.go"), "interruptions at every named point and the resume / rollback (R30 in small)"],
        [c("preflight_test.go"), "facts on fake roots for each family; read-only behaviour"],
        [c("disinstalla_test.go"), "uninstallation plan, enrolments, logs in homes"],
        [c("certifica_test.go"), "PAM resolution and firewall checks never green on a broken machine (R29)"],
        [c("fiducia_test.go"), "catalogue source and minimum engine"],
        [c("interfaccia_test.go") + ", " + c("tui_test.go") + ", " + c("testi_test.go"), "what the interfaces show, the "
         "frame at 80 and 120 columns, colours off"],
        [c("inglese_test.go") + ", " + c("lingua_test.go"), "no Italian in texts, English only"],
        [c("script_test.go"), "the " + c("run.sh") + " header"],
    ], "«TAB» — The engine's tests") + \
    p("What the containers cannot prove — real cards, systemd, firewalls, the four package managers on real "
      "distributions — is the job of the distribution boxes and VMs of " + c("banchi/17-distro/") + " ("
      + rif("Testing") + "). Not settled yet, from fasi/17 §6.6.16: the simulation and installation with the " + c(".run")
      + " files on zypper and pacman have never run on a real machine; " + c("install") + " to the end on the 26 "
      "combinations, the upgrade with a browser connected, and the interrupted install/uninstall are still to be run "
      "on the hardware.")

CHAPTER = ("The installer", [
    ("The installer at a glance", S_INTRO),
    ("Installer source layout", S_LAYOUT),
    ("The installer commands", S_COMMANDS),
    ("An installation from the .run file", S_RUNTIME),
    ("Operation states", S_STATES),
    ("Engine objects and files on disk", S_OBJECTS),
    ("The write-ahead log and resume", S_LOG),
    ("Plan steps, reversibility and origin", S_ACTIONS),
    ("The machine fingerprint", S_FINGERPRINT),
    ("Phase 1: the machine profile", S_PREFLIGHT),
    ("Encoding routes and the card verdict", S_ROUTES),
    ("Phase 2: compatibility and what is missing", S_COMPAT),
    ("The catalogue of platforms", S_CATALOGUE),
    ("The installation plan", S_PLAN),
    ("Package manager adapters", S_MANAGERS),
    ("Verification and the certificate", S_VERIFY),
    ("Uninstallation", S_UNINSTALL),
    ("Unfinished operations", S_INTERRUPTED),
    ("Upgrades and post-upgrade", S_UPGRADES),
    ("Phase 0: trust", S_TRUST),
    ("The installer TUI", S_TUI),
    ("Installer messages and texts", S_TEXTS),
    ("The RX- code catalogue", S_CODES),
    ("Testing the installer", S_TESTS),
])
