package motore

import (
	"errors"
	"fmt"
)

// Gravita and Natura of a message (§6.6.9).
type Gravita string
type Natura string

const (
	INFO      Gravita = "INFO"
	AVVISO    Gravita = "WARNING"
	BLOCCANTE Gravita = "BLOCKING"

	ServeAzione       Natura = "ACTION_NEEDED"
	Riprovabile       Natura = "RETRYABLE"
	Recuperabile      Natura = "RECOVERABLE"
	ServeAnnullamento Natura = "ROLLBACK_NEEDED"
	Fatale            Natura = "FATAL"
)

// Codice is an entry of the codes catalogue: stable, never reused for another meaning.
type Codice struct {
	Gravita Gravita `json:"severity"`
	Natura  Natura  `json:"nature"`
	Testo   string  `json:"text"`
	Rimedio string  `json:"remedy,omitempty"`
}

// Messaggio is a code in its context: what the CLI prints, the log records, the
// certificate keeps, and every future interface shows (§6.6.9).
type Messaggio struct {
	Codice    string  `json:"code"`
	Gravita   Gravita `json:"severity"`
	Natura    Natura  `json:"nature"`
	Testo     string  `json:"text"`
	Rimedio   string  `json:"remedy,omitempty"`
	Dettaglio string  `json:"detail,omitempty"`
}

// Codici: ⛔ a code never changes meaning and is never reused. If a text must be corrected,
// the text is corrected; if the meaning changes, a new number is taken.
var Codici = map[string]Codice{
	// phase 0 — TRUST (§6.6.10)
	// ⛔ 001 and 005 are RETIRED with T8, 002 and 006…016 with simplified D11 (a single key, the
	// repository's, verified by the package manager: DECISIONI §10.21); codes are not reused.
	// (For 001 and 005: the signature was there and was always verified, --senza-firma no longer
	//    exists): they stay here because old logs name them, and they are not reused.
	"RX-TRUST-001": {AVVISO, ServeAzione, "(retired in T8) The catalogue signature could not be verified yet: the engine proceeded only with --senza-firma.", ""},
	"RX-TRUST-002": {INFO, ServeAzione, "(retired: D11 simplified, DECISIONS §10.21) The catalogue had expired.", ""},
	"RX-TRUST-003": {BLOCCANTE, ServeAzione, "The catalogue requires a newer engine than this one.", "Use the .run file of a newer REMOTIX release."},
	"RX-TRUST-004": {BLOCCANTE, Fatale, "The catalogue cannot be read or has an unknown format.", "Download the .run file again and check its sha256; a catalogue given by hand must be fixed."},
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
	"RX-TRUST-017": {INFO, ServeAzione, "(retired: DECISIONS §10.36) The downloaded engine was not the published one (install.sh is gone: REMOTIX comes as one .run file).", ""},

	// phase 1 — PREFLIGHT
	"RX-DISTRO-001":  {BLOCCANTE, ServeAzione, "Cannot tell which distribution is installed (/etc/os-release is missing or unreadable).", ""},
	"RX-SYSTEMD-001": {BLOCCANTE, ServeAzione, "The machine was not booted with systemd: REMOTIX uses logind and the systemd user manager.", "REMOTIX does not run without systemd."},
	// ⛔ 001 RETIRED with phase 19 (DECISIONI §10.27: no encoding on the processor): without a card
	// there is no fallback any more, there is the refusal (003). Codes are not reused.
	"RX-GPU-001": {INFO, ServeAzione, "(retired: phase 19, DECISIONS §10.27) There was no graphics card with a render node: encoding was in software.", ""},
	"RX-GPU-002": {AVVISO, ServeAzione, "The NVIDIA card uses the proprietary driver: it does not encode H.264 through VA-API; video goes through Vulkan Video, if its Vulkan driver (nvidia ICD) is there.", ""},
	// phase 19: the card check (strade.go, VerdettoScheda) — BLOCKING, before touching
	"RX-GPU-003":     {BLOCCANTE, ServeAzione, "Missing: a graphics card (no render node /dev/dri/renderD*). REMOTIX requires hardware-accelerated video encoding, and is not installed on this machine.", ""},
	"RX-GPU-004":     {BLOCCANTE, ServeAzione, "Missing: the Vulkan driver of the NVIDIA card (no nvidia ICD). With the proprietary driver this card encodes only with Vulkan Video: the proprietary driver 550 or newer with its Vulkan ICD is required, or an Intel or AMD card that encodes.", ""},
	"RX-GPU-005":     {BLOCCANTE, ServeAzione, "Missing: a card that encodes H.264 video (Vulkan Video: AMD and NVIDIA; VA-API: Intel and AMD). REMOTIX is not installed on this machine.", ""},
	"RX-GPU-006":     {BLOCCANTE, ServeAzione, "Missing: a driver that encodes H.264 for this card. The VA-API driver on this machine is built without H.264, and the card does not encode in Vulkan Video here (AMD: needs the RADV Vulkan driver with video codecs; Intel does not encode in Vulkan by default).", ""},
	"RX-H264-001":    {AVVISO, ServeAzione, "Whether the card encodes H.264 is not known yet: the check launches no programs, and the one-frame test runs after installation (7a), with the REMOTIX binary.", "The check stays UNKNOWN until then: it does not count as «fine»."},
	"RX-H264-002":    {AVVISO, ServeAzione, "The card did not encode the H.264 test frame.", ""},
	"RX-H264-003":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) The card did not encode H.264 without a driver from RPM Fusion (the engine no longer adds archives or drivers).", ""},
	"RX-H264-004":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) The AMD card did not encode H.264 on openSUSE without the Packman Mesa (the engine no longer adds archives or drivers).", ""},
	"RX-H264-005":    {INFO, ServeAzione, "(retired: phase 19, DECISIONS §10.27) The software fallback (OpenH264) was missing.", ""},
	"RX-H264-006":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) Without the external archive for video encoding REMOTIX was not installed (the engine no longer adds archives).", ""},
	"RX-PAM-001":     {BLOCCANTE, ServeAzione, "The distribution's login stack cannot be found.", "Check the files in /etc/pam.d (or /usr/lib/pam.d on openSUSE)."},
	"RX-PAM-002":     {AVVISO, ServeAzione, "The distribution's login stack contains pam_faillock: three wrong passwords lock the account, even at the machine — for REMOTIX as for ssh.", "Decision D3: REMOTIX follows the system. Configured in /etc/security/faillock.conf; faillock --user NAME --reset unlocks."},
	"RX-PAM-003":     {INFO, ServeAzione, "A «remotix» login file already exists.", ""},
	"RX-PAM-004":     {AVVISO, ServeAzione, "The pam_systemd module cannot be found: without it the desktop does not start.", ""},
	"RX-SELINUX-001": {INFO, ServeAzione, "SELinux is active and enforcing.", "REMOTIX behaviour under SELinux is stage T6."},
	"RX-FW-001":      {AVVISO, ServeAzione, "The firewall is on and the REMOTIX port is not open in it: from other machines REMOTIX cannot be reached.", ""},
	"RX-FW-002":      {AVVISO, ServeAzione, "The firewall state for the REMOTIX port could not be read.", "Reading the ufw and nftables rules requires root."},
	"RX-FW-003":      {AVVISO, ServeAzione, "The REMOTIX port is already taken by another program.", "Choose another port or stop that program."},
	"RX-FW-004":      {INFO, ServeAzione, "(retired: DECISIONS §10.36) The engine could open the port with firewalld and ufw only (the engine no longer opens the firewall).", ""},
	"RX-FW-005":      {INFO, ServeAzione, "From this machine it cannot be known whether the port is reachable from the network (routers, external firewalls).", ""},
	"RX-LOGIND-001":  {AVVISO, ServeAzione, "logind kills the processes of users who log out (KillUserProcesses=yes): a REMOTIX desktop might die.", "Effect to be measured; declared for now."},
	"RX-LOGIND-002":  {INFO, ServeAzione, "The KillUserProcesses value could not be read from logind.", ""},
	"RX-GRUPPI-001":  {AVVISO, ServeAzione, "The «render» group does not exist on this machine.", ""},
	"RX-GRUPPI-002":  {BLOCCANTE, ServeAzione, "The requested group does not exist.", ""},
	"RX-GRUPPI-003":  {BLOCCANTE, ServeAzione, "The requested user does not exist.", ""},
	"RX-OPENSSL-001": {BLOCCANTE, ServeAzione, "OpenSSL is older than 3.5: QUIC is missing.", ""},
	"RX-OPENSSL-002": {AVVISO, ServeAzione, "The OpenSSL version could not be read.", ""},
	"RX-DESKTOP-001": {INFO, ServeAzione, "(retired: DECISIONS §10.36) No desktop was chosen for installation (the engine no longer installs a desktop).", ""},
	"RX-DESKTOP-002": {INFO, ServeAzione, "(retired: DECISIONS §10.36) No supported desktop was installed and the engine asked which one to add (now RX-MANCA-001).", ""},

	// phase 2 — COMPATIBILITY (§6.6.8)
	"RX-COMPAT-001": {BLOCCANTE, ServeAzione, "This distribution is outside REMOTIX.", ""},
	"RX-COMPAT-002": {BLOCCANTE, ServeAzione, "This distribution is not in the catalogue: whether REMOTIX runs on it is unknown.", ""},
	"RX-COMPAT-003": {BLOCCANTE, ServeAzione, "Immutable distributions are postponed until after phase 17 (decision D9).", ""},
	"RX-COMPAT-004": {BLOCCANTE, ServeAzione, "This combination is waiting for a decision by the user.", ""},
	"RX-COMPAT-005": {BLOCCANTE, ServeAzione, "This desktop is not supported on this distribution.", ""},
	"RX-COMPAT-006": {BLOCCANTE, ServeAzione, "The desktop version is older than the minimum.", ""},
	"RX-COMPAT-007": {BLOCCANTE, ServeAzione, "The machine lacks an indispensable requirement.", ""},
	// DECISIONI §10.36: REMOTIX does not modify the system — what is missing is stated, and the
	// administrator provides it (no packages or commands suggested)
	"RX-MANCA-001": {BLOCCANTE, ServeAzione, "Missing: a supported desktop. REMOTIX does not install one.", ""},
	"RX-MANCA-002": {BLOCCANTE, ServeAzione, "Missing: a repository that REMOTIX's dependencies come from on this distribution.", ""},
	"RX-MANCA-003": {BLOCCANTE, ServeAzione, "Missing: packages a desktop needs to run under REMOTIX.", ""},
	"RX-MANCA-004": {BLOCCANTE, ServeAzione, "Missing: the REMOTIX package for this distribution in this .run file.", ""},

	// phases 3-4 — PLANNING, CONSENT
	"RX-PIANO-001": {BLOCCANTE, ServeAzione, "The machine changed after the plan was made: the plan is no longer valid.", "Run remotix-install install again."},
	"RX-PIANO-002": {BLOCCANTE, Fatale, "The plan cannot be read or has an unknown format.", ""},
	"RX-PIANO-003": {BLOCCANTE, ServeAzione, "The plan was not approved: nothing is touched.", ""},
	"RX-PIANO-004": {BLOCCANTE, Fatale, "The plan contains a step this engine does not know.", ""},
	"RX-PIANO-005": {BLOCCANTE, ServeAzione, "The approval does not match this plan (the plan was changed afterwards).", "Run remotix-install install again."},

	// without questions and without network (§6.6.12, T9)
	"RX-RISPOSTE-001": {INFO, ServeAzione, "(retired: DECISIONS §10.36) The answer file did not give a needed consent (there is no answer file any more).", ""},
	"RX-RISPOSTE-002": {INFO, ServeAzione, "(retired: DECISIONS §10.36) The answer file could not be read (there is no answer file any more).", ""},
	"RX-RISPOSTE-003": {INFO, ServeAzione, "(retired: DECISIONS §10.36) An answer in the file had a value not allowed (there is no answer file any more).", ""},
	"RX-FUORI-001":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) The offline bundle was not intact (prepare-offline is gone: the .run file is already offline).", ""},
	"RX-FUORI-002":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) The offline bundle was prepared for another machine (prepare-offline is gone: the .run file is already offline).", ""},
	"RX-FUORI-003":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) Something was missing from the offline bundle (prepare-offline is gone: the .run file is already offline).", ""},
	"RX-FUORI-004":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) Offline installation was not done for zypper and pacman (prepare-offline is gone: the .run file is already offline).", ""},
	"RX-FUORI-005":    {INFO, ServeAzione, "(retired: DECISIONS §10.36) A third-party archive could not go into the offline bundle (prepare-offline is gone: the .run file is already offline).", ""},

	// operation, log and resume (§6.6.2, §6.6.3)
	"RX-STATO-001":     {BLOCCANTE, Recuperabile, "There is an unfinished operation.", "remotix-install install rolls an unfinished installation back first; remotix-install uninstall completes an unfinished uninstallation."},
	"RX-STATO-002":     {BLOCCANTE, Fatale, "Invalid state transition: this is an engine defect.", ""},
	"RX-STATO-003":     {BLOCCANTE, Riprovabile, "Another engine is working right now.", "Wait for it to finish."},
	"RX-STATO-004":     {BLOCCANTE, ServeAzione, "There is no operation to resume or roll back.", ""},
	"RX-STATO-005":     {BLOCCANTE, ServeAzione, "The operation is in a final state: it is neither resumed nor rolled back (to remove REMOTIX, uninstall).", ""},
	"RX-RIPRESA-001":   {BLOCCANTE, ServeAzione, "The machine changed during the operation: a step already done is gone or was changed by someone else.", "Look at the log; remotix-install install rolls the operation back."},
	"RX-RIPRESA-002":   {BLOCCANTE, ServeAzione, "The operation stopped before touching the machine: there is nothing to resume.", "Run remotix-install install again."},
	"RX-RIPRESA-003":   {INFO, Recuperabile, "The log ended with a half-written line (interruption): the line was removed.", ""},
	"RX-AZIONE-001":    {BLOCCANTE, ServeAnnullamento, "An installation step failed: the operation is being rolled back.", ""},
	"RX-AZIONE-002":    {BLOCCANTE, ServeAzione, "A step could not be rolled back: the machine did not fully return to how it was.", "The exact list of what remains is in the certificate."},
	"RX-AZIONE-003":    {BLOCCANTE, ServeAnnullamento, "A step's verification does not pass: the operation is being rolled back.", ""},
	"RX-AZIONE-004":    {BLOCCANTE, ServeAzione, "The plan contains a step this engine knows but cannot perform yet: stopping before touching the machine.", "The step arrives with phases 5-8 of the engine (T5)."},
	"RX-INST-001":      {INFO, ServeAzione, "Installation not certified by the installer (no CONFIRMED remotix-install operation): stated for information only.", ""},
	"RX-INST-002":      {AVVISO, ServeAzione, "After the update the machine check found problems.", "remotix-install check"},
	"RX-AZIONE-005":    {BLOCCANTE, ServeAzione, "An IRREVERSIBLE step cannot be rolled back.", ""},
	"RX-PACCHETTI-001": {BLOCCANTE, ServeAzione, "The package is not the plan's one (different sha256).", "Run remotix-install install again."},
	"RX-PACCHETTI-002": {BLOCCANTE, ServeAzione, "Removing the REMOTIX packages would also remove someone else's package: nothing is touched.", "Check who depends on that package."},
	"RX-PACCHETTI-003": {BLOCCANTE, ServeAzione, "This family's package manager is not known to the engine.", ""},
	"RX-PACCHETTI-004": {BLOCCANTE, ServeAzione, "The package manager is half-way through an earlier transaction.", ""},
	"RX-PACCHETTI-006": {INFO, ServeAzione, "Some packages brought by REMOTIX stay: something that stays needs them (a package updated from the same archive, or a program installed later). Removing them would take it away too.", "If they are no longer needed, remove them by hand together with what needs them, with the package manager."},
	"RX-PACCHETTI-005": {BLOCCANTE, Riprovabile, "The package manager cannot install REMOTIX on this machine: nothing was installed.", "The detail says what the package manager is missing (a dependency that no configured repository provides, a conflict)."},
	"RX-CINTURA-001":   {INFO, ServeAzione, "(retired: DECISIONS §10.36) The switched-off safety-belt file was missing (the engine no longer enables system safety belts).", ""},
	"RX-SYSTEMD-002":   {BLOCCANTE, ServeAzione, "The unit is masked: the administrator switched it off on purpose.", ""},
	"RX-SYSTEMD-003":   {BLOCCANTE, ServeAzione, "The unit does not exist.", ""},
	"RX-FILE-001":      {BLOCCANTE, ServeAzione, "The file was changed by someone else during the operation: it is not touched.", ""},
	"RX-AZIONE-006":    {BLOCCANTE, ServeAnnullamento, "The installation was stopped by the person installing: what was already done is rolled back.", ""},

	// the interfaces (T9, DECISIONI §10.14, §10.19): TUI and GUI
	"RX-UI-001": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) This build of remotix-install has no window (it is the static one, for machines without a desktop).", ""},
	"RX-UI-002": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) The window does not open: there is no graphical session (neither WAYLAND_DISPLAY nor DISPLAY), or its libraries do not answer.", ""},
	"RX-UI-003": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) The window does not run as administrator (root): it asks polkit for permissions itself, when needed.", ""},
	"RX-UI-004": {INFO, ServeAzione, "(retired: DECISIONS §10.31, no GUI) Administrator permissions were not granted (polkit refused or the request was closed): nothing was touched.", ""},
	"RX-UI-005": {BLOCCANTE, ServeAzione, "The administrator part of the engine stopped.", "remotix-install status tells where the operation is."},
	"RX-UI-006": {BLOCCANTE, ServeAzione, "The TUI needs a terminal and administrator permissions.", "sudo remotix-install tui"},

	// automatic updating (DECISIONI §10.10, T8)
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

// Msg builds a message from a code. An unknown code is a defect of the engine, and the
// test TestCodiciUsatiEsistono finds it before it reaches anyone.
func Msg(codice, dettaglio string) Messaggio {
	c, ok := Codici[codice]
	if !ok {
		panic("unknown code: " + codice)
	}
	return Messaggio{Codice: codice, Gravita: c.Gravita, Natura: c.Natura, Testo: c.Testo, Rimedio: c.Rimedio, Dettaglio: dettaglio}
}

// ErroreRX is an error carrying its stable code.
type ErroreRX struct{ M Messaggio }

func (e *ErroreRX) Error() string {
	if e.M.Dettaglio != "" {
		return fmt.Sprintf("%s: %s (%s)", e.M.Codice, e.M.Testo, e.M.Dettaglio)
	}
	return e.M.Codice + ": " + e.M.Testo
}

// Errore builds an error with a code.
func Errore(codice, dettaglio string) error { return &ErroreRX{Msg(codice, dettaglio)} }

// CodiceDi extracts the code from an error, or "" if the error has none.
func CodiceDi(err error) string {
	var e *ErroreRX
	if errors.As(err, &e) {
		return e.M.Codice
	}
	return ""
}
