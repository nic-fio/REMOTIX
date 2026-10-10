package motore

// testi: il catalogo dei testi del motore e della riga di comando, in inglese (DECISIONI §10.35).
// Le chiavi sono stabili; i %s e %d seguono fmt.Sprintf.
var testi = map[string]string{
	// stati (§6.6.2), come li dice l'avanzamento
	"state.NEW":                       "new",
	"state.TRUSTED":                   "trust checked",
	"state.EXAMINED":                  "machine examined",
	"state.ASSESSED":                  "compatibility assessed",
	"state.PLANNED":                   "plan checked",
	"state.APPROVED":                  "plan approved",
	"state.ACQUIRED":                  "everything needed is ready",
	"state.RUNNING":                   "applying the plan",
	"state.INTERRUPTED":               "found interrupted",
	"state.APPLIED":                   "plan applied",
	"state.VERIFYING":                 "verifying",
	"state.VERIFIED":                  "verified",
	"state.CONFIRMED":                 "CONFIRMED",
	"state.CONFIRMED_WITH_CONDITIONS": "CONFIRMED WITH CONDITIONS",
	"state.ROLLING_BACK":              "rolling back",
	"state.ROLLED_BACK":               "ROLLED BACK: the machine is as it was",
	"state.PARTIALLY_ROLLED_BACK":     "PARTLY ROLLED BACK",
	"state.BLOCKED":                   "BLOCKED",
	"state.REFUSED":                   "REFUSED: nothing was touched",
	"ev.rimedio":                      "remedy",
	"ev.si_riprende":                  "resuming",
	"ev.operazione":                   "operation %s",

	// compatibilità (§6.6.8)
	"comp.nella_matrice":    "in the matrix (%s)",
	"comp.fuori_matrice":    "analysed, outside the matrix (%s)",
	"comp.derivata":         "derivative of %s (compatible, not certified)",
	"comp.esclusa":          "excluded",
	"comp.sconosciuta":      "unknown",
	"cond.componente":       "the installer adds «%s», which the stock desktop does not bring",
	"cond.carattere":        "no scalable font: without one, labwc dies (labwc #2525)",
	"cond.deposito_desktop": "%s comes from %s",
	"cond.deposito_h264":    "H.264 on the card only with the driver from %s",
	"cond.deposito_base":    "REMOTIX on this distribution only with %s (the card driver repository needs it)",
	"cond.nvidia":           "NVIDIA with the proprietary driver and without its Vulkan driver (ICD): no encoding on this card, video is encoded by the other card",
	"cond.amd_senza_vaapi":  "on %s Mesa has no VA-API: the AMD card does not encode, video is encoded by the other card",
	"pacchetti.trattenuti":  "the new packages are gone, except those kept because something that stays needs them: %s",
	"pacchetti.chiesto_da":  "needed by %s",
	"repo.trattenuto":       "the %s repository stays enabled: packages taken from it are needed by what stays — %s",
	"repo.ancora":           "%d packages that came with the repository are still installed: %s",
	"cond.3d":               "%s requires the card's 3D acceleration: %s",
	"mot.3d":                "%s requires 3D acceleration, and the machine has no card (no render node): %s",
	"cond.desktop":          "%s is not there: the installer adds it from the distribution's archives, without a local login screen, only with consent",
	"cond.desktop_rimedio":  "answer «yes» to the desktop question; «no» ⇒ REMOTIX is not installed (RX-DESKTOP-001)",
	"inc.openssl":           "OpenSSL version",
	"inc.desktop":           "desktop %s",
	"inc.h264":              "H.264 on the card (%s)",
	"scelta.desktop":        "This machine has no desktop supported by REMOTIX: install one? (if not, REMOTIX is not installed)",

	// il piano di prova e i passi (§6.6.4)
	"np.desktop":          "no supported desktop: a real installation would ask here which one to add (%s; proposed %s)",
	"np.utente":           "no user given (--users): there is no «video» group step",
	"np.firewall_no":      "port %s is not opened in the firewall: not requested (--open-firewall; decision D6 open)",
	"np.firewall_nessuno": "no firewall on: nothing to open",
	"np.firewall_mano":    "%s: open port %s TCP and UDP by hand",

	"az.file":                         "write %s",
	"az.file.fa":                      "the existing file (if any) is saved, the new one is written to «%s» next to it, fsync, and renamed over it",
	"az.file.verifica":                "file sha256 and permissions equal to the plan's",
	"az.file.annulla":                 "the saved file is put back (or removed, if it was not there), and created directories if left empty",
	"az.gruppo":                       "add %s to the %s group",
	"az.gruppo.fa":                    "gpasswd -a %s %s (unless already there: then nothing, recorded as PRE-EXISTING)",
	"az.gruppo.verifica":              "%s among the members of %s",
	"az.gruppo.annulla":               "gpasswd -d %s %s, only if REMOTIX added them",
	"az.unita":                        "enable the unit %s",
	"az.unita.fa":                     "EnableUnitFiles %s on systemd's D-Bus (without starting it)",
	"az.unita.verifica":               "unit file state of %s = enabled",
	"az.unita.annulla":                "DisableUnitFiles %s, if it was not enabled before",
	"az.fw":                           "open port %s (TCP and UDP) in the firewall",
	"az.fw.fa":                        "the remotix service if the firewall already knows it, otherwise ports %s/tcp and /udp, runtime and permanent: firewalld on its D-Bus (default zone), ufw with its command",
	"az.fw.verifica":                  "the runtime and permanent rules are there",
	"az.fw.annulla":                   "only the rules added by REMOTIX are removed; a firewalld zone that was the stock one goes back to stock",
	"az.fw.consenso":                  "Open port %s (TCP and UDP) in the firewall? (decision D6, open)",
	"az.desktop":                      "install %s from the distribution's archives",
	"az.desktop.fa":                   "the distribution's package group for %s, without a display manager and without graphical.target: at the monitor the machine stays as it was",
	"az.desktop.verifica":             "the installed packages, and the stage starting headless",
	"az.desktop.annulla":              "packages installed for us that nobody else wants are removed; upgraded ones stay (INDIRECT, declared)",
	"az.cintura":                      "switch on the safety belt %s",
	"az.cintura.fa":                   "copy of %s to %s (temporary + rename), recording the administrator's file if there was one",
	"az.cintura.verifica":             "sha256 equal to the source",
	"az.cintura.annulla":              "the file is removed (or the administrator's one is put back)",
	"az.cintura.dichiarata":           "The three safety belts are always switched on (D4, DECISIONS §4.7): remotely and at the monitor the machine cannot be shut down or suspended, and the keys do not power it off; only root can.",
	"risposte.aggiornamenti_ignorata": "consent.updates is ignored: REMOTIX is updated with the system (D14)",
	"risposte.openh264_ignorata":      "consent.repo.openh264 is ignored: no more encoding on the processor, nor the OpenH264 repository (phase 19)",
	"risposte.cinture_ignorata":       "consent.guards is ignored: the safety belts are always switched on (D4)",
	"az.servizio":                     "enable and start remotix.service",
	"az.servizio.fa":                  "EnableUnitFiles and StartUnit of remotix.service, after the checks with the service stopped (7a)",
	"az.servizio.verifica":            "active, the port answers on TCP and UDP (7b)",
	"az.servizio.annulla":             "StopUnit and DisableUnitFiles of remotix.service",

	"az.pacchetti":                  "have the distribution's package manager install %s",
	"az.pacchetti.fa":               "the transaction is resolved, everything downloaded and verified (resolved set in the log), then the manager installs from the cache, offline",
	"az.pacchetti.verifica":         "every package of the resolved set installed at its version, manager not half-way",
	"az.pacchetti.annulla":          "the manager removes the NEW packages, and only those (simulating first); upgraded ones stay and are declared",
	"az.deposito":                   "add the %s archive",
	"az.deposito.fa.archive":        "the archive key (chain B) and the source naming it: apt Signed-By + a pin taking only REMOTIX packages from the archive; dnf gpgcheck, repo_gpgcheck, includepkgs; pacman a [remotix] block with SigLevel Required and the key in pacman-key",
	"az.deposito.fa.epel":           "dnf install epel-release, and the CRB repository enabled",
	"az.deposito.fa.rpmfusion":      "dnf install of the rpmfusion-free-release package for the machine's version (and rpmfusion-nonfree-release if the Intel card needs it)",
	"az.deposito.fa.packman":        "zypper addrepo of Packman (priority 90) and refresh with its key",
	"az.deposito.verifica":          "the archive configured",
	"az.deposito.annulla.archive":   "the files are removed (and the key from rpm or pacman-key; the block from pacman.conf)",
	"az.deposito.annulla.epel":      "epel-release is removed and CRB goes back; packages taken from it stay (declared)",
	"az.deposito.annulla.rpmfusion": "the rpmfusion-free-release and rpmfusion-nonfree-release we added are removed; packages taken from it stay (declared)",
	"az.deposito.annulla.packman":   "zypper removerepo packman; packages taken from it and the key stay (declared)",
	"ind.deposito":                  "repository %s removed: packages taken from it and upgrades stay",
	"consent.repo":                  "Add the third-party archive %s (for video or for the desktop)? (decision D5)",
	"az.sessioni":                   "close the REMOTIX sessions still open (%d: %s)",
	"az.sessioni.fa":                "logind TerminateSession on the sessions with PAM service «remotix» only: the same people's local or ssh sessions stay",
	"az.sessioni.verifica":          "none of those sessions is still open",
	"az.sessioni.annulla":           "IRREVERSIBLE: unsaved work is lost, sessions do not reopen",
	"az.disfa":                      "undo: %s",
	"az.disfa.verifica":             "as it was before the installation",
	"np.nessun_gruppo":              "no card node with a group: nobody to add",
	"cond.codifica_ignota":          "H.264 encoding on the card was not tested by REMOTIX (%s): it is not confirmed",
	"ver.nessuna_scheda":            "no card can encode: the card's encoder does not open (%s)",
	"az.iscrizione":                 "remove %s from the %s group (added by REMOTIX at first connection)",
	"az.iscrizione.fa":              "gpasswd -d, if still in the group",
	"az.iscrizione.verifica":        "no longer in the group",
	"az.iscrizione.annulla":         "gpasswd -a (added back)",
	"az.registri":                   "remove the REMOTIX session log (%s) from every user's home — now: %s",
	"az.registri.fa":                "only sessione.log is removed, and the %s folder if left empty; nothing else in the homes",
	"az.registri.verifica":          "none of those files is left",
	"az.registri.annulla":           "put back byte for byte, with permissions and owner (copies in the operation folder)",
	"az.registri.dichiarata":        "uninstalling removes ~/.local/state/remotix/sessione.log from every home (and the folder if left empty) — %s",
	"az.registri.nessuno":           "no session log in any home",
	"az.registri.tolti":             "removed: %s",
	"az.registri.ancora":            "still in the homes: %s",
	"az.registri.non_rimesso":       "not back as it was",
	"az.registri.rimessi":           "the session logs are back",
	"ver.pam":                       "the REMOTIX login stack resolves (files, includes, modules)",
	"ver.porta":                     "the firewall lets port %s TCP and UDP through",
	"ver.porta_nessuno":             "no firewall on",
	"cond.pam_ignota":               "the login stack could not be checked (%s)",
	"cond.porta_ignota":             "unknown whether the firewall lets port %s through: check by hand",
	"cond.porta_chiusa":             "the firewall closes %s: REMOTIX cannot be reached from outside until it is opened (D6)",
	"cli.certifica":                 "Certification of installation %s: %s",
	"ver.codifica_assente":          "the REMOTIX encoding test gave no readable answer",

	// operazione e certificato
	"op.chiesto":          "requested by the administrator",
	"op.no_desktop":       "answer «no» to the desktop question",
	"cert.titolo":         "REMOTIX — certificate of operation %s",
	"cert.stato":          "final state",
	"cert.mestiere":       "job",
	"cert.motore":         "engine",
	"cert.catalogo":       "catalogue",
	"cert.fiducia":        "trust",
	"cert.piano":          "plan",
	"cert.impronta":       "fingerprint",
	"cert.controlli":      "checks",
	"cert.condizioni":     "conditions",
	"cert.nessuna":        "none",
	"cert.non_annullato":  "NOT ROLLED BACK",
	"cert.prodotto_prova": "none: engine test plan (T4)",
	"cert.fiducia_no":     "the catalogue could NOT be used: the operation stopped at phase 0",

	// riga di comando
	"cli.uso": `remotix-install — the REMOTIX installation engine (version %s, format %s)

  remotix-install check     [--json] [--port N] [--catalog FILE]
        examines the machine, WITHOUT TOUCHING ANYTHING, and says what REMOTIX can do on it
  remotix-install plan      [--output FILE] [--users NAME] [--open-firewall] [--json]
        prepares an engine TEST plan
  remotix-install plan --install --package FILE [--users A,B] [--extra-repos epel,rpmfusion,packman]
                            [--open-firewall]
        prepares the REMOTIX INSTALLATION plan
  remotix-install uninstall [--purge]     prepares the uninstallation plan (from the log)
  remotix-install approve   PLAN-FILE [--desktop gnome|kde|xfce|lxqt|no]
        writes the consent of whoever runs it into the plan (to apply it without questions)
  remotix-install apply     PLAN-FILE [--approve] [--events]
        applies the plan: stops if the machine is not the plan's machine
  remotix-install resume    [--events]    completes an interrupted operation
  remotix-install rollback  [--events]    rolls back an unfinished operation
  remotix-install status                  the operations and their state
  remotix-install post-upgrade            for the package scripts after a version change:
        records the versions, says whether the installation is certified and whether there is a BLOCKING problem
  remotix-install certify   [--json]      runs the installation checks again (GREEN, CONDITIONAL, RED)
  REMOTIX is updated with the system (apt upgrade, dnf upgrade, zypper up, pacman -Syu): the engine
        has no update command; to go back, the package manager commands
  remotix-install catalog   [--table]     the catalogue in use (--table: the tables of §3.1)

  UNATTENDED and OFFLINE (§6.6.12):
  remotix-install install --answers FILE [--archive URL | --offline DIR] [--events]
        plan from the answer file, logged, and applied: a missing consent ⇒ BLOCKED
        (RX-RISPOSTE-001). Without --answers: shows the plan and asks for one confirmation at the terminal
  remotix-install plan --install --answers FILE [...]   only the plan (to read, or to carry
        approved to machines with the same fingerprint: remotix-install apply PLAN-FILE)
  remotix-install prepare-offline --archive URL (--answers FILE | --plan FILE) --output DIR
        on a CONNECTED machine identical to the offline one: the offline bundle (engine,
        resolved set, signed repository metadata); there: remotix-install install --offline DIR
  the answer file (format remotix-answers/2), one entry per line, «#» comment:
        format = remotix-answers/2   port = 7447   archive = URL   channel = stable|candidate
        users = all|a,b   desktop = gnome|kde|xfce|lxqt|no (only if a desktop is missing)
        consent.firewall = yes|no
        consent.repo.rpmfusion|packman|epel = yes|no
        (every consent that machine needs must be given, «yes» or «no»)

  common options: --state-dir DIR (default /var/lib/remotix/operations), --catalog FILE (given by hand),
  --events: the events as JSON, one line each (for the interfaces)
`,
	"cli.titolo":             "REMOTIX — machine check (read only: nothing was touched)",
	"cli.distribuzione":      "Distribution",
	"cli.catalogo":           "Catalogue: %s",
	"cli.desktop":            "The desktops:",
	"cli.non_installato":     "not installed",
	"cli.non_si_sa":          "unknown whether present",
	"cli.installato":         "installed (%s)",
	"cli.proposto":           "  ← the one proposed if one is installed",
	"cli.perche":             "why",
	"cli.condizione":         "condition",
	"cli.comando":            "command",
	"cli.decisione":          "(decision %s, open)",
	"cli.nota":               "note",
	"cli.senza_desktop":      "  ⚠ No supported desktop is installed: before installing REMOTIX you will be asked whether\n    to add one (if the answer is no, REMOTIX is not installed: RX-DESKTOP-001).",
	"cli.incognite":          "What could NOT be found out (it does not count as «fine»):",
	"cli.avvisi":             "Warnings and problems:",
	"cli.fatti":              "The facts (DETECTED = seen; VERIFIED = actually tested; UNKNOWN = unknown):",
	"cli.piano_scritto":      "Plan (%s) %s written to %s",
	"cli.piano_macchina":     "Machine: %s — fingerprint %s (%d binding elements)",
	"cli.piano_passo":        "%d. %s  [%s, %s]\n   done by: %s\n   verified by: %s\n   rolled back by: %s\n",
	"cli.consenso":           "consent required: %s",
	"cli.non_fatto":          "not done: %s %s %s",
	"cli.per_applicarlo":     "To apply it: remotix-install approve %s && remotix-install apply %s",
	"cli.gia_approvato":      "Already approved (%s): it is applied as it is, also on other machines with the same fingerprint: remotix-install apply %s",
	"cli.risposte":           "From the answer file %s (sha256 %s): %d entries",
	"cli.risposte_predef":    "  choices the file does not state, at their default: %s",
	"cli.risposte_superflue": "  entries with no effect on this machine: %s",
	"cli.risposte_mancanti":  "  ⛔ consents that are needed and that the file does NOT give: %s — the operation will be BLOCKED (RX-RISPOSTE-001)",
	"cli.conferma":           "Apply this plan? Type «yes» to confirm: ",
	"cli.non_confermato":     "not confirmed: nothing was touched",
	"cli.dichiarato":         "always done: %s",
	"cli.router":             "From outside the local network: forward port %d, TCP and UDP, on the router to this machine (REMOTIX does not do it by itself: no UPnP).",
	"cli.senza_terminale":    "no terminal to ask for confirmation: an unattended installation needs --answers FILE (§6.6.12)",
	"cli.fuori_linea":        "Offline bundle %s: %s, channel %s, %d artefacts, %d files verified, prepared on %s",
	"cli.preparato":          "Offline bundle ready in %s: %d artefacts, %d files (%d MB). Reference machine fingerprint %s, %d packages.",
	"cli.approvato":          "Plan %s approved by %s (digest %s)",
	"cli.serve_piano":        "%s: the plan file is needed",
	"cli.operazione":         "operation %s: %s",
	"cli.nessuna_op":         "no operation in %s",
	"cli.aperta":             "  ← open: resume or roll back",
	"cli.certificata":        "installation certified by the installer: operation %s %s",
	"cli.fiducia":            "Trust: catalogue %s, sequence %d — %s",
	"cli.col_sistema":        "REMOTIX is updated with the system (DECISIONS §10.23): apt upgrade · dnf upgrade · zypper up · pacman -Syu.\nTo go back to a previous version, use the package manager commands:\n  apt install remotix=VERSION remotix-install=VERSION   (the versions: apt list -a remotix)\n  dnf downgrade remotix remotix-install\n  zypper install --oldpackage remotix-VERSION remotix-install-VERSION\n  pacman -U /var/cache/pacman/pkg/remotix-VERSION-x86_64.pkg.tar.zst (or from the archive)\nThe service restarts without closing the desktops; afterwards, remotix-install certify.\n",
	"cli.versioni_annotate":  "REMOTIX versions recorded: %s",
	"fid.pacchetto":          "the catalogue of the remotix-install package (guaranteed by the package manager, from the signed REMOTIX archive)",
	"fid.scaricato":          "the catalogue of the engine %s (downloaded by install.sh, which checks it against the published sha256)",
	"fid.a_mano":             "the catalogue given by hand: %s (the administrator's)",
	"cli.catalogo_info":      "catalogue %s (sequence %d), issued on %s, minimum engine %s\ndigest %s\n%s\n",
}
