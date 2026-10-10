package motore

import (
	"errors"
	"fmt"
)

// Gravita e Natura di un messaggio (§6.6.9).
type Gravita string
type Natura string

const (
	INFO      Gravita = "INFO"
	AVVISO    Gravita = "AVVISO"
	BLOCCANTE Gravita = "BLOCCANTE"

	ServeAzione       Natura = "SERVE_AZIONE"
	Riprovabile       Natura = "RIPROVABILE"
	Recuperabile      Natura = "RECUPERABILE"
	ServeAnnullamento Natura = "SERVE_ANNULLAMENTO"
	Fatale            Natura = "FATALE"
)

// Codice è una voce del catalogo dei codici: stabile, mai riusata per un altro significato.
type Codice struct {
	Gravita Gravita `json:"gravita"`
	Natura  Natura  `json:"natura"`
	Testo   string  `json:"testo"`
	Rimedio string  `json:"rimedio,omitempty"`
}

// Messaggio è un codice nel suo contesto: quel che la CLI stampa, il registro annota, il
// certificato conserva, e ogni futura interfaccia mostra (§6.6.9).
type Messaggio struct {
	Codice    string  `json:"codice"`
	Gravita   Gravita `json:"gravita"`
	Natura    Natura  `json:"natura"`
	Testo     string  `json:"testo"`
	Rimedio   string  `json:"rimedio,omitempty"`
	Dettaglio string  `json:"dettaglio,omitempty"`
}

// Codici: ⛔ un codice non si cambia di significato e non si riusa. Se un testo va corretto si
// corregge il testo; se il significato cambia, si prende un numero nuovo.
var Codici = map[string]Codice{
	// fase 0 — TRUST (§6.6.10)
	// ⛔ 001 e 005 sono RITIRATI con T8, 002 e 006…016 con D11 semplificata (una chiave sola, quella
	// dell'archivio, verificata dal gestore di pacchetti: DECISIONI §10.21); i codici non si riusano.
	// (Per 001 e 005: la firma c'era e si verificava sempre, --senza-firma non esiste
	//    più): restano qui perché i registri vecchi li nominano, e non si riusano.
	"RX-TRUST-001": {AVVISO, ServeAzione, "(retired in T8) The catalogue signature could not be verified yet: the engine proceeded only with --senza-firma.", ""},
	"RX-TRUST-002": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The catalogue had expired.", ""},
	"RX-TRUST-003": {BLOCCANTE, ServeAzione, "The catalogue requires a newer engine than this one.", "Update the system (the remotix-install package), or download install.sh again."},
	"RX-TRUST-004": {BLOCCANTE, Fatale, "The catalogue cannot be read or has an unknown format.", "Reinstall remotix-install from the REMOTIX archive, or download install.sh again; a catalogue given by hand must be fixed."},
	"RX-TRUST-005": {BLOCCANTE, ServeAzione, "(retired in T8) Trust in the catalogue was not verified and proceeding anyway was not requested.", ""},
	"RX-TRUST-006": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The catalogue (or the engine) had no chain A signature.", ""},
	"RX-TRUST-007": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The chain A signature did not match.", ""},
	"RX-TRUST-008": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The subkey was not certified by the chain A root key.", ""},
	"RX-TRUST-009": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The chain A subkey had expired.", ""},
	"RX-TRUST-010": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The chain A subkey was revoked.", ""},
	"RX-TRUST-011": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The archive catalogue was older than the stored one.", ""},
	"RX-TRUST-012": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The revocation list did not verify.", ""},
	"RX-TRUST-013": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The catalogue could not be downloaded from the archive.", ""},
	"RX-TRUST-014": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The engine did not match its chain A signature.", ""},
	"RX-TRUST-015": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The engine had no chain A signature next to it.", ""},
	"RX-TRUST-016": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The offline catalogue was older than the stored one.", ""},
	"RX-TRUST-017": {BLOCCANTE, ServeAzione, "The downloaded engine is not the published one: its sha256 is not the one written in install.sh or published next to it.", "Do not use this engine: download install.sh again from the REMOTIX site, check its sha256 against the published one (HTTPS), and run it again."},

	// fase 1 — PREFLIGHT
	"RX-DISTRO-001":  {BLOCCANTE, ServeAzione, "Cannot tell which distribution is installed (/etc/os-release is missing or unreadable).", ""},
	"RX-SYSTEMD-001": {BLOCCANTE, ServeAzione, "The machine was not booted with systemd: REMOTIX uses logind and the systemd user manager.", "REMOTIX does not run without systemd."},
	// ⛔ 001 RITIRATO con la fase 19 (DECISIONI §10.27: niente codifica sul processore): senza scheda
	// non c'è più un ripiego, c'è il rifiuto (003). I codici non si riusano.
	"RX-GPU-001": {INFO, ServeAzione, "(retired: phase 19, DECISIONS §10.27) There was no graphics card with a render node: encoding was in software.", ""},
	"RX-GPU-002": {AVVISO, ServeAzione, "The NVIDIA card uses the proprietary driver: it does not encode H.264 through VA-API; video goes through Vulkan Video, if its Vulkan driver (nvidia ICD) is there.", "Without the Vulkan ICD, video is encoded by another card of the machine, if it has a capable one (condition C-HARDWARE); otherwise REMOTIX is not installed (RX-GPU-004)."},
	// fase 19: il controllo della scheda (strade.go, VerdettoScheda) — BLOCCANTI, prima di toccare
	"RX-GPU-003":     {BLOCCANTE, ServeAzione, "No graphics card (no render node /dev/dri/renderD*): REMOTIX requires hardware-accelerated video encoding, and is not installed on this machine.", "Install it on a machine with an Intel or AMD card; in a virtual machine, give it a card (passthrough or vGPU). If the machine has a card, check that its driver is loaded."},
	"RX-GPU-004":     {BLOCCANTE, ServeAzione, "NVIDIA with the proprietary driver but without its Vulkan driver (no nvidia ICD): on this card REMOTIX encodes only with Vulkan Video, and without the driver it is not installed.", "Install the complete NVIDIA driver (with the Vulkan ICD, /usr/share/vulkan/icd.d/nvidia_icd.json), or an Intel or AMD card next to the NVIDIA: REMOTIX uses that one for video."},
	"RX-GPU-005":     {BLOCCANTE, ServeAzione, "No card of this machine can encode H.264 video for REMOTIX (Vulkan Video: AMD and NVIDIA; VA-API: Intel and AMD): REMOTIX is not installed.", "Install it on a machine with an Intel, AMD or NVIDIA card; in a virtual machine, give it the real card (passthrough or vGPU)."},
	"RX-GPU-006":     {BLOCCANTE, ServeAzione, "The card is there, but on this distribution its VA-API driver does not encode H.264, there is no driver to add that does, and it is not there in Vulkan Video (AMD: this distribution builds RADV without H.264; Intel does not encode in Vulkan by default): REMOTIX is not installed.", "The combinations that encode are in the compatibility report (e.g. AlmaLinux/RHEL: Intel with the RPM Fusion driver; AMD encodes on Debian, Ubuntu and Arch, and on Fedora and openSUSE with the third-party repository driver)."},
	"RX-H264-001":    {AVVISO, ServeAzione, "Whether the card encodes H.264 is not known yet: the check launches no programs, and the one-frame test runs after installation (7a), with the REMOTIX binary.", "The check stays UNKNOWN until then: it does not count as «fine»."},
	"RX-H264-002":    {AVVISO, ServeAzione, "The card did not encode the H.264 test frame.", "Check the card's VA-API driver."},
	"RX-H264-003":    {AVVISO, ServeAzione, "The card does not encode H.264: on Fedora and the RHEL family the driver with H.264 comes from RPM Fusion (Intel: intel-media-driver; AMD, Fedora only: mesa-va-drivers-freeworld).", "The command is in the compatibility report (condition C-DEPOSITO, decision D5)."},
	"RX-H264-004":    {AVVISO, ServeAzione, "The card does not encode H.264: on openSUSE with an AMD card the Packman Mesa is needed (the official Intel driver already encodes).", "The command is in the compatibility report (condition C-DEPOSITO, decision D5)."},
	"RX-H264-005":    {INFO, ServeAzione, "(retired: phase 19, DECISIONS §10.27) The software fallback (OpenH264) was missing.", ""},
	"RX-H264-006":    {BLOCCANTE, ServeAzione, "Without the external archive for video encoding REMOTIX is not installed (decision D5, DECISIONS §10.20): nothing was touched.", "Run the installation again giving consent to the archive (consenso.deposito.<name> = si)."},
	"RX-PAM-001":     {BLOCCANTE, ServeAzione, "The distribution's login stack cannot be found.", "Check the files in /etc/pam.d (or /usr/lib/pam.d on openSUSE)."},
	"RX-PAM-002":     {AVVISO, ServeAzione, "The distribution's login stack contains pam_faillock: three wrong passwords lock the account, even at the machine — for REMOTIX as for ssh.", "Decision D3: REMOTIX follows the system. Configured in /etc/security/faillock.conf; faillock --user NAME --reset unlocks."},
	"RX-PAM-003":     {INFO, ServeAzione, "A «remotix» login file already exists.", ""},
	"RX-PAM-004":     {AVVISO, ServeAzione, "The pam_systemd module cannot be found: without it the desktop does not start.", ""},
	"RX-SELINUX-001": {INFO, ServeAzione, "SELinux is active and enforcing.", "REMOTIX behaviour under SELinux is stage T6."},
	"RX-FW-001":      {AVVISO, ServeAzione, "The firewall is on and the REMOTIX port is not open in it.", "Open it (decision D6: the engine can do it, with consent)."},
	"RX-FW-002":      {AVVISO, ServeAzione, "The firewall state for the REMOTIX port could not be read.", "Reading the ufw and nftables rules requires root."},
	"RX-FW-003":      {AVVISO, ServeAzione, "The REMOTIX port is already taken by another program.", "Choose another port or stop that program."},
	"RX-FW-004":      {BLOCCANTE, ServeAzione, "This engine can open the port with firewalld and ufw: nftables is not done yet.", "Open the port by hand, with the given command."},
	"RX-FW-005":      {INFO, ServeAzione, "From this machine it cannot be known whether the port is reachable from the network (routers, external firewalls).", ""},
	"RX-LOGIND-001":  {AVVISO, ServeAzione, "logind kills the processes of users who log out (KillUserProcesses=yes): a REMOTIX desktop might die.", "Effect to be measured; declared for now."},
	"RX-LOGIND-002":  {INFO, ServeAzione, "The KillUserProcesses value could not be read from logind.", ""},
	"RX-GRUPPI-001":  {AVVISO, ServeAzione, "The «render» group does not exist on this machine.", ""},
	"RX-GRUPPI-002":  {BLOCCANTE, ServeAzione, "The requested group does not exist.", ""},
	"RX-GRUPPI-003":  {BLOCCANTE, ServeAzione, "The requested user does not exist.", ""},
	"RX-OPENSSL-001": {BLOCCANTE, ServeAzione, "OpenSSL is older than 3.5: QUIC is missing.", ""},
	"RX-OPENSSL-002": {AVVISO, ServeAzione, "The OpenSSL version could not be read.", ""},
	"RX-DESKTOP-001": {BLOCCANTE, ServeAzione, "This machine has no desktop supported by REMOTIX, and none was chosen for installation: REMOTIX is not installed.", "Answer yes to the desktop question (remotix-install approva --desktop gnome|kde|xfce|lxqt), or install one."},
	"RX-DESKTOP-002": {AVVISO, ServeAzione, "No supported desktop is installed: before installing you will be asked which one to add (condition C-DESKTOP).", ""},

	// fase 2 — COMPATIBILITY (§6.6.8)
	"RX-COMPAT-001": {BLOCCANTE, ServeAzione, "This distribution is outside REMOTIX.", ""},
	"RX-COMPAT-002": {BLOCCANTE, ServeAzione, "This distribution is not in the catalogue: whether REMOTIX runs on it is unknown.", ""},
	"RX-COMPAT-003": {BLOCCANTE, ServeAzione, "Immutable distributions are postponed until after phase 17 (decision D9).", ""},
	"RX-COMPAT-004": {BLOCCANTE, ServeAzione, "This combination is waiting for a decision by the user.", ""},
	"RX-COMPAT-005": {BLOCCANTE, ServeAzione, "This desktop is not supported on this distribution.", ""},
	"RX-COMPAT-006": {BLOCCANTE, ServeAzione, "The desktop version is older than the minimum.", ""},
	"RX-COMPAT-007": {BLOCCANTE, ServeAzione, "The machine lacks an indispensable requirement.", ""},

	// fasi 3-4 — PLANNING, CONSENT
	"RX-PIANO-001": {BLOCCANTE, ServeAzione, "The machine changed after the plan was made: the plan is no longer valid.", "Make the plan again on this machine (remotix-install piano)."},
	"RX-PIANO-002": {BLOCCANTE, Fatale, "The plan cannot be read or has an unknown format.", ""},
	"RX-PIANO-003": {BLOCCANTE, ServeAzione, "The plan was not approved: nothing is touched.", "Approve it with remotix-install approva, or with --approva."},
	"RX-PIANO-004": {BLOCCANTE, Fatale, "The plan contains a step this engine does not know.", ""},
	"RX-PIANO-005": {BLOCCANTE, ServeAzione, "The approval does not match this plan (the plan was changed afterwards).", "Approve the plan again."},

	// senza domande e senza rete (§6.6.12, T9)
	"RX-RISPOSTE-001": {BLOCCANTE, ServeAzione, "The answer file does not give a consent that this machine needs: unattended does not mean without consent, and a missing consent does not count as «yes». Nothing was touched.", "Add the indicated entry to the answer file, with «si» or «no» (the entries: remotix-install aiuto)."},
	"RX-RISPOSTE-002": {BLOCCANTE, Fatale, "The answer file cannot be read, has an unknown format or contains an unknown entry.", "Fix the file: the first entry is «formato = remotix-risposte/1»; the allowed entries are in remotix-install aiuto."},
	"RX-RISPOSTE-003": {BLOCCANTE, ServeAzione, "An answer in the file has a value that is not allowed on this machine.", "Fix the indicated value."},
	"RX-FUORI-001":    {BLOCCANTE, ServeAzione, "The offline bundle is not intact: a file is missing or is not the one prepared.", "Prepare it again (remotix-install prepara-fuori-linea) and copy it whole."},
	"RX-FUORI-002":    {BLOCCANTE, ServeAzione, "The offline bundle was prepared for another machine (different fingerprint or installed packages).", "Prepare it on a connected machine identical to this one (same distribution and same packages)."},
	"RX-FUORI-003":    {BLOCCANTE, ServeAzione, "Something the installation needs is missing from the offline bundle.", "Prepare it again on the reference machine, with the same answers."},
	"RX-FUORI-004":    {BLOCCANTE, ServeAzione, "Installation without a network is not done yet for this distribution family (zypper, pacman).", "Install from the network."},
	"RX-FUORI-005":    {BLOCCANTE, ServeAzione, "A third-party archive (Packman, EPEL) does not go into the offline bundle: its step downloads from the network.", "Install from the network: without that archive REMOTIX is not installed (D5, encoding on the card)."},

	// operazione, registro e ripresa (§6.6.2, §6.6.3)
	"RX-STATO-001":     {BLOCCANTE, Recuperabile, "There is an unfinished operation: it must be resumed or rolled back first.", "remotix-install riprendi, or remotix-install annulla."},
	"RX-STATO-002":     {BLOCCANTE, Fatale, "Invalid state transition: this is an engine defect.", ""},
	"RX-STATO-003":     {BLOCCANTE, Riprovabile, "Another engine is working right now.", "Wait for it to finish."},
	"RX-STATO-004":     {BLOCCANTE, ServeAzione, "There is no operation to resume or roll back.", ""},
	"RX-STATO-005":     {BLOCCANTE, ServeAzione, "The operation is in a final state: it is neither resumed nor rolled back (to remove REMOTIX, uninstall).", ""},
	"RX-RIPRESA-001":   {BLOCCANTE, ServeAzione, "The machine changed during the operation: a step already done is gone or was changed by someone else.", "Look at the log; then resume or roll back."},
	"RX-RIPRESA-002":   {BLOCCANTE, ServeAzione, "The operation stopped before touching the machine: there is nothing to resume.", "Run remotix-install applica with the plan again."},
	"RX-RIPRESA-003":   {INFO, Recuperabile, "The log ended with a half-written line (interruption): the line was removed.", ""},
	"RX-AZIONE-001":    {BLOCCANTE, ServeAnnullamento, "An installation step failed: the operation is being rolled back.", ""},
	"RX-AZIONE-002":    {BLOCCANTE, ServeAzione, "A step could not be rolled back: the machine did not fully return to how it was.", "The exact list of what remains is in the certificate."},
	"RX-AZIONE-003":    {BLOCCANTE, ServeAnnullamento, "A step's verification does not pass: the operation is being rolled back.", ""},
	"RX-AZIONE-004":    {BLOCCANTE, ServeAzione, "The plan contains a step this engine knows but cannot perform yet: stopping before touching the machine.", "The step arrives with phases 5-8 of the engine (T5)."},
	"RX-INST-001":      {INFO, ServeAzione, "Installation not certified by the installer (no CONFIRMED remotix-install operation): stated for information only.", ""},
	"RX-INST-002":      {AVVISO, ServeAzione, "After the update the machine check found problems.", "remotix-install verifica"},
	"RX-AZIONE-005":    {BLOCCANTE, ServeAzione, "An IRREVERSIBLE step cannot be rolled back.", ""},
	"RX-PACCHETTI-001": {BLOCCANTE, ServeAzione, "The package is not the plan's one (different sha256).", "Make the plan again with the right package."},
	"RX-PACCHETTI-002": {BLOCCANTE, ServeAzione, "Removing the REMOTIX packages would also remove someone else's package: nothing is touched.", "Check who depends on that package."},
	"RX-PACCHETTI-003": {BLOCCANTE, ServeAzione, "This family's package manager is not known to the engine.", ""},
	"RX-PACCHETTI-004": {BLOCCANTE, ServeAzione, "The package manager is half-way through an earlier transaction.", "Fix it with its own remedy (dpkg --configure -a, dnf, zypper verify) and retry."},
	"RX-PACCHETTI-006": {INFO, ServeAzione, "Some packages brought by REMOTIX stay: something that stays needs them (a package updated from the same archive, or a program installed later). Removing them would take it away too.", "If they are no longer needed, remove them by hand together with what needs them, with the package manager."},
	"RX-PACCHETTI-005": {BLOCCANTE, Riprovabile, "The transaction could not be resolved or downloaded: nothing was installed.", "Check the network and the repositories, then resume."},
	"RX-CINTURA-001":   {BLOCCANTE, ServeAzione, "The switched-off safety-belt file is missing (the package did not bring it).", ""},
	"RX-SYSTEMD-002":   {BLOCCANTE, ServeAzione, "The unit is masked: the administrator switched it off on purpose.", ""},
	"RX-SYSTEMD-003":   {BLOCCANTE, ServeAzione, "The unit does not exist.", ""},
	"RX-FILE-001":      {BLOCCANTE, ServeAzione, "The file was changed by someone else during the operation: it is not touched.", ""},
	"RX-AZIONE-006":    {BLOCCANTE, ServeAnnullamento, "The installation was stopped by the person installing: what was already done is rolled back.", ""},

	// le interfacce (T9, DECISIONI §10.14, §10.19): TUI e GUI
	"RX-UI-001": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) This build of remotix-install has no window (it is the static one, for machines without a desktop).", ""},
	"RX-UI-002": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) The window does not open: there is no graphical session (neither WAYLAND_DISPLAY nor DISPLAY), or its libraries do not answer.", ""},
	"RX-UI-003": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) The window does not run as administrator (root): it asks polkit for permissions itself, when needed.", ""},
	"RX-UI-004": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) Administrator permissions were not granted (polkit refused or the request was closed): nothing was touched.", ""},
	"RX-UI-005": {BLOCCANTE, ServeAzione, "The administrator part of the engine stopped.", "remotix-install stato tells where the operation is; remotix-install riprendi or annulla."},
	"RX-UI-006": {BLOCCANTE, ServeAzione, "The TUI needs a terminal and administrator permissions.", "sudo remotix-install tui"},

	// l'aggiornamento automatico (DECISIONI §10.10, T8)
	"RX-AGG-001": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) REMOTIX was at the latest version of its channel.", ""},
	"RX-AGG-002": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) A maintenance update was available.", ""},
	"RX-AGG-003": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) The new yearly version was available.", ""},
	"RX-AGG-004": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) An update was available, notice only.", ""},
	"RX-AGG-005": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) Automatic updates were switched off.", ""},
	"RX-AGG-006": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) REMOTIX was not installed by the installer: nothing to update.", ""},
	"RX-AGG-007": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) The archive did not answer during the update.", ""},
	"RX-AGG-008": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) On Arch the update would have been partial.", ""},
	"RX-AGG-009": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) The requested version was not in the archive.", ""},
	"RX-AGG-010": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) The update configuration could not be read.", ""},
	"RX-AGG-011": {INFO, ServeAzione, "(retired: D14, DECISIONS §10.23) Automatic updates were suspended after a rollback.", ""},
}

// Msg costruisce un messaggio da un codice. Un codice sconosciuto è un difetto del motore, e la
// prova TestCodiciUsatiEsistono lo trova prima che arrivi a qualcuno.
func Msg(codice, dettaglio string) Messaggio {
	c, ok := Codici[codice]
	if !ok {
		panic("unknown code: " + codice)
	}
	return Messaggio{Codice: codice, Gravita: c.Gravita, Natura: c.Natura, Testo: c.Testo, Rimedio: c.Rimedio, Dettaglio: dettaglio}
}

// ErroreRX è un errore che porta il suo codice stabile.
type ErroreRX struct{ M Messaggio }

func (e *ErroreRX) Error() string {
	if e.M.Dettaglio != "" {
		return fmt.Sprintf("%s: %s (%s)", e.M.Codice, e.M.Testo, e.M.Dettaglio)
	}
	return e.M.Codice + ": " + e.M.Testo
}

// Errore costruisce un errore con codice.
func Errore(codice, dettaglio string) error { return &ErroreRX{Msg(codice, dettaglio)} }

// CodiceDi estrae il codice da un errore, o "" se l'errore non ne ha.
func CodiceDi(err error) string {
	var e *ErroreRX
	if errors.As(err, &e) {
		return e.M.Codice
	}
	return ""
}
