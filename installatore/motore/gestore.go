package motore

import (
	"errors"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strings"
	"time"
)

// The distribution's package manager (§6.0, rule 1): it is IT that puts and removes the files
// of the packages; the engine decides, asks, checks and undoes. The engine launches it from the closed
// list (ambiente.go), never a shell.
//
// The set (§6.6.6, simplified on 10 Oct 2026, DECISIONI §10.36: «don't reinvent the wheel»):
// Simula asks the manager what it would do — the exact list (name, version, architecture,
// origin, and what happens: new, upgraded from…, already present), which the plan shows BEFORE the
// question. Installa lets the manager work as always: it resolves, downloads from the repositories the
// machine has, verifies the signatures. The engine has no cache and no sha256 of its own for the packages. Togli simulates
// first and refuses if it would remove something not in the list (someone else's package that in the
// meantime depends on it): the managers' autoremove would also remove earlier orphans, belonging to others.
//
// Tried on the VMs: apt (Debian 13) and dnf (Alma 10). zypper and pacman are written in the same
// shape but NOT yet tried on a real machine.

// Artefatto: a line of the resolved set.
type Artefatto struct {
	Nome     string `json:"name"`
	Versione string `json:"version"`
	Arch     string `json:"arch,omitempty"`
	Origine  string `json:"origin"`           // "file" (from the single package) or the machine's repository
	Esito    string `json:"result"`           // "new" · "upgraded" · "present"
	Prima    string `json:"before,omitempty"` // the previous version, if upgraded
}

// Gestore: the family's package manager.
type Gestore interface {
	Nome() string
	// Versioni: the installed version for every name ("" = not installed).
	Versioni(nomi []string) (map[string]string, error)
	// Simula: what the manager would install, without touching anything. file = local packages (from the
	// single package), nomi = packages from the machine's repositories.
	Simula(file, nomi []string) ([]Artefatto, error)
	// Installa: the manager installs, with the dependencies from the machine's repositories.
	Installa(file, nomi []string) error
	// SimulaTogli: what the manager would remove BEYOND the given names (whoever depends on them), without
	// touching anything.
	SimulaTogli(nomi []string, purge bool) ([]string, error)
	// Togli the given names, and only those (purge: the configuration too): if it would remove others,
	// RX-PACCHETTI-002 and nothing removed.
	Togli(nomi []string, purge bool) error
	// Integro: the manager is not halfway through a transaction.
	Integro() (bool, string, error)
	// Ripara: the manager's own remedy after an interruption (§6.6.3).
	Ripara() error
}

// ScegliGestore: the family's one.
func ScegliGestore(a *Ambiente, fam string) Gestore {
	switch fam {
	case "debian":
		return &gestoreApt{a}
	case "fedora":
		return &gestoreDnf{a}
	case "suse":
		return &gestoreZypper{a}
	case "arch":
		return &gestorePacman{a}
	}
	return nil
}

func esegui(a *Ambiente, tempo time.Duration, nome string, arg ...string) (string, error) {
	out, c, err := a.Esegui(tempo, nome, arg...)
	if err != nil {
		return out, err
	}
	if c != 0 {
		return out, fmt.Errorf("%s %s: exit %d: %s", nome, strings.Join(arg, " "), c, ultimeRighe(out, 6))
	}
	return out, nil
}

func ultimeRighe(s string, n int) string {
	r := strings.Split(strings.TrimSpace(s), "\n")
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return strings.Join(r, " | ")
}

const tempoGestore = 45 * time.Minute

// ---------------------------------------------------------------- apt (Debian, Ubuntu)

type gestoreApt struct{ a *Ambiente }

func (g *gestoreApt) Nome() string { return "apt" }

var aptOpzioni = []string{"-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold", "-o", "APT::Get::Assume-Yes=true"}

func (g *gestoreApt) Versioni(nomi []string) (map[string]string, error) {
	pk := ArchivioPacchetti(g.a, "debian", nomi)
	if !pk.letto {
		return nil, errors.New("the dpkg database cannot be read")
	}
	r := map[string]string{}
	for _, n := range nomi {
		r[n] = pk.versioni[n]
	}
	return r, nil
}

// «Inst name [old] (new repository [arch])»
var aptInst = regexp.MustCompile(`^Inst (\S+)(?: \[(\S+)\])? \((\S+) (.*?) \[(\S+)\]\)`)

func (g *gestoreApt) argomenti(file, nomi []string) []string {
	return append(append([]string{}, file...), nomi...)
}

func (g *gestoreApt) Simula(file, nomi []string) ([]Artefatto, error) {
	sim := func() (string, error) {
		return esegui(g.a, tempoGestore, "apt-get", append(append([]string{"-s", "install"}, aptOpzioni...), g.argomenti(file, nomi)...)...)
	}
	out, err := sim()
	if err != nil { // stale lists: they are refreshed (the repositories' signed metadata) and it is retried
		if _, e2 := esegui(g.a, tempoGestore, "apt-get", "update"); e2 != nil {
			return nil, err
		}
		if out, err = sim(); err != nil {
			return nil, err
		}
	}
	locali := map[string]bool{}
	for _, f := range file {
		if n, v, e := g.intestazione(f); e == nil {
			locali[n+" "+v] = true
		}
	}
	var r []Artefatto
	for _, riga := range strings.Split(out, "\n") {
		if strings.HasPrefix(riga, "Remv ") || strings.HasPrefix(riga, "Purg ") {
			return nil, fmt.Errorf("the transaction would remove a package: %s", riga)
		}
		m := aptInst.FindStringSubmatch(riga)
		if m == nil {
			continue
		}
		a := Artefatto{Nome: m[1], Versione: m[3], Arch: m[5], Origine: m[4], Esito: "new"}
		if m[2] != "" {
			a.Esito, a.Prima = "upgraded", m[2]
		}
		if locali[a.Nome+" "+a.Versione] {
			a.Origine = "file"
		}
		r = append(r, a)
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

// header of a local .deb (name, version), read with dpkg-deb.
func (g *gestoreApt) intestazione(f string) (string, string, error) {
	out, err := esegui(g.a, time.Minute, "dpkg-deb", "-W", "--showformat=${Package} ${Version}", f)
	if err != nil {
		return "", "", err
	}
	c := strings.Fields(out)
	if len(c) != 2 {
		return "", "", fmt.Errorf("dpkg-deb: %q", out)
	}
	return c[0], c[1], nil
}

// Installa: apt installs the local files and downloads the dependencies from the machine's repositories.
func (g *gestoreApt) Installa(file, nomi []string) error {
	_, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"install"}, aptOpzioni...), g.argomenti(file, nomi)...)...)
	return err
}

var aptTogli = regexp.MustCompile(`^(?:Remv|Purg) (\S+)`)

func aptVerbo(purge bool) string {
	if purge {
		return "purge"
	}
	return "remove"
}

func (g *gestoreApt) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	out, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"-s", aptVerbo(purge)}, aptOpzioni...), nomi...)...)
	if err != nil {
		return nil, err
	}
	var altri []string
	for _, riga := range strings.Split(out, "\n") {
		if m := aptTogli.FindStringSubmatch(riga); m != nil {
			altri = append(altri, m[1])
		}
	}
	return fuoriDa(altri, nomi), nil
}

func (g *gestoreApt) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	_, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{aptVerbo(purge)}, aptOpzioni...), nomi...)...)
	return err
}

// fuoriDa: the names of «tutti» that are not in «nomi» (without repetitions). An rpm key is removed
// by version (gpg-pubkey-…), and dnf shows it by name.
func fuoriDa(tutti, nomi []string) []string {
	nostri := map[string]bool{}
	for _, n := range nomi {
		nostri[n] = true
		if strings.HasPrefix(n, "gpg-pubkey-") {
			nostri["gpg-pubkey"] = true
		}
	}
	var r []string
	for _, n := range tutti {
		if !nostri[n] {
			nostri[n] = true
			r = append(r, n)
		}
	}
	return r
}

// soloLoro: the guard of Togli — the manager would remove only the given names.
func soloLoro(g Gestore, nomi []string, purge bool) error {
	altri, err := g.SimulaTogli(nomi, purge)
	if err != nil {
		return err
	}
	if len(altri) > 0 {
		return Errore("RX-PACCHETTI-002", strings.Join(altri, ", "))
	}
	return nil
}

func (g *gestoreApt) Integro() (bool, string, error) {
	out, c, err := g.a.Esegui(time.Minute, "dpkg", "--audit")
	if err != nil {
		return false, "", err
	}
	if c != 0 || strings.TrimSpace(out) != "" {
		return false, ultimeRighe(out, 3), nil
	}
	return true, "", nil
}

func (g *gestoreApt) Ripara() error {
	_, err := esegui(g.a, tempoGestore, "dpkg", "--configure", "-a")
	return err
}

// ---------------------------------------------------------------- dnf (Fedora, RHEL, Alma)

type gestoreDnf struct{ a *Ambiente }

func (g *gestoreDnf) Nome() string { return "dnf" }

func rpmVersioni(a *Ambiente, nomi []string) (map[string]string, error) {
	r := map[string]string{}
	if len(nomi) == 0 {
		return r, nil
	}
	out, _, err := a.Esegui(time.Minute, "rpm", append([]string{"-q", "--qf", `%{NAME} %{VERSION}-%{RELEASE}\n`}, nomi...)...)
	if err != nil {
		return nil, err
	}
	for _, n := range nomi {
		r[n] = ""
	}
	for _, riga := range strings.Split(out, "\n") {
		c := strings.Fields(riga)
		if len(c) == 2 && !strings.HasPrefix(riga, "package ") {
			r[c[0]] = c[1]
		}
	}
	return r, nil
}

func (g *gestoreDnf) Versioni(nomi []string) (map[string]string, error) {
	return rpmVersioni(g.a, nomi)
}

// Simula: dnf's transaction with --assumeno (dnf 4 and dnf 5 write the table in the same
// order: name, architecture, version, repository). What gets installed, upgraded or
// DOWNGRADED is taken (a downgrade is an INDIRECT change like an upgrade); «@commandline» is a
// file of the single package.
func (g *gestoreDnf) Simula(file, nomi []string) ([]Artefatto, error) {
	out, c, err := g.a.Esegui(tempoGestore, "dnf", append([]string{"install", "--assumeno", "--setopt=localpkg_gpgcheck=0"}, append(append([]string{}, file...), nomi...)...)...)
	if err != nil {
		return nil, err
	}
	if !strings.Contains(out, "Transaction Summary") {
		if strings.Contains(out, "Nothing to do") {
			return g.presenti(file, nomi)
		}
		return nil, fmt.Errorf("dnf install --assumeno: exit %d: %s", c, ultimeRighe(out, 6))
	}
	var r []Artefatto
	in := false
	visti := map[string]bool{}
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		if strings.HasSuffix(t, ":") && !strings.HasPrefix(riga, " ") {
			in = strings.HasPrefix(t, "Installing") || strings.HasPrefix(t, "Upgrading") || strings.HasPrefix(t, "Downgrading")
			continue
		}
		f := strings.Fields(t)
		if !in || len(f) < 4 || !archi[f[1]] || visti[f[0]] {
			continue
		}
		visti[f[0]] = true
		ver := strings.TrimPrefix(f[2], "0:")
		a := Artefatto{Nome: f[0], Versione: ver, Arch: f[1], Origine: f[3], Esito: "new"}
		if f[3] == "@commandline" {
			a.Origine = "file"
		}
		r = append(r, a)
	}
	prima, err := rpmVersioni(g.a, nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "upgraded", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

var archi = map[string]bool{"x86_64": true, "noarch": true, "i686": true, "aarch64": true}

// presenti: nothing to do — the files' packages, already installed at the same version.
func (g *gestoreDnf) presenti(file, nomi []string) ([]Artefatto, error) {
	var r []Artefatto
	for _, f := range file {
		out, err := esegui(g.a, time.Minute, "rpm", "-qp", "--qf", `RX %{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n`, f)
		if err != nil {
			return nil, err
		}
		for _, riga := range strings.Split(out, "\n") {
			if c := strings.Fields(riga); len(c) == 4 && c[0] == "RX" {
				r = append(r, Artefatto{Nome: c[1], Versione: c[2], Arch: c[3], Origine: "file", Esito: "present"})
			}
		}
	}
	for _, n := range nomi {
		r = append(r, Artefatto{Nome: n, Origine: "repo", Esito: "present"})
	}
	return r, nil
}

func nomiDi(r []Artefatto) []string {
	var n []string
	for _, a := range r {
		n = append(n, a.Nome)
	}
	return n
}

// Installa: dnf installs the files of the single package (without an rpm signature: the .run's sha256
// guarantees them) and takes the dependencies from the machine's repositories, with their signatures.
func (g *gestoreDnf) Installa(file, nomi []string) error {
	_, err := esegui(g.a, tempoGestore, "dnf", append([]string{"install", "-y", "--setopt=localpkg_gpgcheck=0"}, append(append([]string{}, file...), nomi...)...)...)
	return err
}

func (g *gestoreDnf) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	// dnf remove also removes whoever depends on these: it is checked with --assumeno
	out, _, err := g.a.Esegui(tempoGestore, "dnf", append([]string{"remove", "--assumeno", "--setopt=clean_requirements_on_remove=0"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	// ⚠ --assumeno exits 1 EVEN when the simulation succeeds («Operation aborted»): the code says
	// nothing, the text does. If the solver does not resolve — removing these would break a
	// PROTECTED package, or an installed one that needs them — there is no «Removing» section: the names are
	// in the «Problem» lines, and they are the dependents (the given names are held back). `[M]` T10, 30 Sep,
	// fedora44-gnome-iso (phase 18, with the Cisco repository): openh264 ← libheif ← glycin-loaders ← gdk-pixbuf2 ← gnome-shell (protected);
	// before, «no dependents» was read and `dnf remove -y` failed.
	if strings.Contains(out, "Failed to resolve the transaction") || strings.Contains(out, "Impossibile risolvere la transazione") {
		altri := fuoriDa(problemiDnf(out), nomi)
		if len(altri) == 0 {
			return nil, fmt.Errorf("dnf remove --assumeno %s: %s", strings.Join(nomi, " "), ultimeRighe(out, 6))
		}
		return altri, nil
	}
	var tutti []string
	in := false
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		if strings.HasPrefix(t, "Removing") || strings.HasPrefix(t, "Rimozione") {
			in = true
			continue
		}
		if in && (t == "" || strings.HasPrefix(t, "Transaction Summary") || strings.HasPrefix(t, "Riepilogo")) {
			in = false
		}
		if c := strings.Fields(t); in && len(c) >= 3 && !strings.HasSuffix(c[0], ":") {
			tutti = append(tutti, c[0])
		}
	}
	return fuoriDa(tutti, nomi), nil
}

// problemiDnf: the packages named in the «Problem» lines of a dnf solver that does not resolve — the protected ones
// («protected packages: a, b») and the installed ones that need what is being removed («installed
// package NEVRA requires …»); the NEVRA goes back to a name.
func problemiDnf(out string) []string {
	var r []string
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		if _, dopo, ok := strings.Cut(t, "protected packages: "); ok {
			for _, n := range strings.Split(dopo, ",") {
				if n = strings.TrimSpace(n); n != "" {
					r = append(r, n)
				}
			}
			continue
		}
		for _, marca := range []string{"installed package ", "il pacchetto installato "} {
			if _, dopo, ok := strings.Cut(t, marca); ok {
				if f := strings.Fields(dopo); len(f) > 0 {
					r = append(r, nomeDaNevra(f[0]))
				}
			}
		}
	}
	return fuoriDa(r, nil)
}

// nomeDaNevra: «libheif-1.23.5-3.fc44.x86_64» → «libheif» (strip the architecture, then version and release).
func nomeDaNevra(nevra string) string {
	s := nevra
	if i := strings.LastIndex(s, "."); i > 0 {
		s = s[:i]
	}
	for range 2 {
		if i := strings.LastIndex(s, "-"); i > 0 {
			s = s[:i]
		}
	}
	return s
}

func (g *gestoreDnf) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	_, err := esegui(g.a, tempoGestore, "dnf", append([]string{"remove", "-y", "--setopt=clean_requirements_on_remove=0"}, nomi...)...)
	return err
}

func (g *gestoreDnf) Integro() (bool, string, error) {
	// a half-done rpm transaction leaves duplicate packages (two versions of the same one)
	out, c, err := g.a.Esegui(time.Minute, "rpm", "-qa", "--qf", `%{NAME}.%{ARCH}\n`)
	if err != nil {
		return false, "", err
	}
	if c != 0 {
		return false, ultimeRighe(out, 3), nil
	}
	visti := map[string]bool{}
	for _, n := range strings.Fields(out) {
		if visti[n] && !strings.HasPrefix(n, "gpg-pubkey") && !strings.HasPrefix(n, "kernel") {
			return false, "duplicate: " + n, nil
		}
		visti[n] = true
	}
	return true, "", nil
}

// Ripara: dnf repeats the transaction; here we go back to a coherent state by removing the duplicates.
func (g *gestoreDnf) Ripara() error {
	_, err := esegui(g.a, tempoGestore, "dnf", "remove", "-y", "--duplicates")
	return err
}

// ---------------------------------------------------------------- zypper (openSUSE) — not tried

type gestoreZypper struct {
	a *Ambiente
}

// fileArg: the files of the single package have no rpm signature (the .run's sha256 guarantees them):
// zypper would refuse them ([M] 30 Sep, tumbleweed-kde: «Signature verification failed [6-File is
// unsigned]»). ⚠ It applies ONLY to those files; the repositories' packages stay verified by zypper.
func (g *gestoreZypper) fileArg(file []string) []string {
	if len(file) == 0 {
		return nil
	}
	return []string{"--allow-unsigned-rpm"}
}

func (g *gestoreZypper) Nome() string { return "zypper" }

func (g *gestoreZypper) Versioni(nomi []string) (map[string]string, error) {
	return rpmVersioni(g.a, nomi)
}

func (g *gestoreZypper) Simula(file, nomi []string) ([]Artefatto, error) {
	out, err := esegui(g.a, tempoGestore, "zypper", append([]string{"--non-interactive", "--xmlout", "install", "--dry-run"}, append(append(g.fileArg(file), file...), nomi...)...)...)
	if err != nil {
		return nil, err
	}
	var r []Artefatto
	re := regexp.MustCompile(`<solvable type="package" name="([^"]+)" edition="([^"]+)" arch="([^"]+)"`)
	for _, m := range re.FindAllStringSubmatch(out, -1) {
		r = append(r, Artefatto{Nome: m[1], Versione: m[2], Arch: m[3], Origine: "repo", Esito: "new"})
	}
	prima, err := rpmVersioni(g.a, nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "upgraded", p
		}
	}
	return r, nil
}

func (g *gestoreZypper) Installa(file, nomi []string) error {
	_, err := esegui(g.a, tempoGestore, "zypper", append([]string{"--non-interactive", "install"}, append(append(g.fileArg(file), file...), nomi...)...)...)
	return err
}

var zypperSolvibile = regexp.MustCompile(`<solvable type="package" name="([^"]+)"`)

func (g *gestoreZypper) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	out, err := esegui(g.a, tempoGestore, "zypper", append([]string{"--non-interactive", "--xmlout", "remove", "--dry-run"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	var tutti []string
	for _, m := range zypperSolvibile.FindAllStringSubmatch(out, -1) {
		tutti = append(tutti, m[1])
	}
	return fuoriDa(tutti, nomi), nil
}

func (g *gestoreZypper) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	_, err := esegui(g.a, tempoGestore, "zypper", append([]string{"--non-interactive", "remove"}, nomi...)...)
	return err
}

func (g *gestoreZypper) Integro() (bool, string, error) {
	out, c, err := g.a.Esegui(tempoGestore, "zypper", "--non-interactive", "verify", "--dry-run")
	if err != nil {
		return false, "", err
	}
	return c == 0, ultimeRighe(out, 2), nil
}

func (g *gestoreZypper) Ripara() error {
	_, err := esegui(g.a, tempoGestore, "zypper", "--non-interactive", "verify")
	return err
}

// ---------------------------------------------------------------- pacman (Arch) — not tried

type gestorePacman struct{ a *Ambiente }

func (g *gestorePacman) Nome() string { return "pacman" }

func (g *gestorePacman) Versioni(nomi []string) (map[string]string, error) {
	pk := ArchivioPacchetti(g.a, "arch", nomi)
	if !pk.letto {
		return nil, errors.New("the pacman database cannot be read")
	}
	r := map[string]string{}
	for _, n := range nomi {
		r[n] = pk.versioni[n]
	}
	return r, nil
}

func (g *gestorePacman) Simula(file, nomi []string) ([]Artefatto, error) {
	// the whole transaction (the files of the single package and the repositories' packages, with the
	// dependencies): pacman -U/-S --print says what it would install, without touching anything
	var righe []string
	if len(file) > 0 {
		out, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-U", "--needed", "--print", "--print-format", "%n %v %a %r %l"}, file...)...)
		if err != nil {
			return nil, err
		}
		righe = append(righe, strings.Split(out, "\n")...)
	}
	if len(nomi) > 0 {
		out, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-S", "--needed", "--print", "--print-format", "%n %v %a %r %l"}, nomi...)...)
		if err != nil {
			return nil, err
		}
		righe = append(righe, strings.Split(out, "\n")...)
	}
	var r []Artefatto
	visti := map[string]bool{}
	for _, riga := range righe {
		c := strings.Fields(riga)
		if len(c) != 5 || visti[c[0]] {
			continue
		}
		visti[c[0]] = true
		a := Artefatto{Nome: c[0], Versione: c[1], Arch: c[2], Origine: c[3], Esito: "new"}
		if strings.HasPrefix(c[4], "file://") || strings.HasPrefix(c[4], "/") {
			a.Origine = "file"
		}
		r = append(r, a)
	}
	prima, err := g.Versioni(nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "upgraded", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

func (g *gestorePacman) Installa(file, nomi []string) error {
	if len(nomi) > 0 {
		if _, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-S", "--needed", "--noconfirm"}, nomi...)...); err != nil {
			return err
		}
	}
	if len(file) == 0 {
		return nil
	}
	// -U takes the files' dependencies from the machine's repositories
	_, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-U", "--needed", "--noconfirm"}, file...)...)
	return err
}

func (g *gestorePacman) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	// ⚠ pacman -R does not remove whoever depends: if someone depends, the simulation FAILS and says so
	// («removing X breaks dependency 'X' required by Y»): whoever depends is Y
	out, c, err := g.a.Esegui(tempoGestore, "pacman", append([]string{"-R", "--print", "--print-format", "%n"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	if c != 0 {
		var r []string
		for _, m := range pacmanRompe.FindAllStringSubmatch(out, -1) {
			r = append(r, m[1])
		}
		if len(r) == 0 {
			return nil, fmt.Errorf("pacman -R --print: exit %d: %s", c, ultimeRighe(out, 6))
		}
		return fuoriDa(r, nomi), nil
	}
	return fuoriDa(strings.Fields(out), nomi), nil
}

var pacmanRompe = regexp.MustCompile(`required by (\S+)`)

func (g *gestorePacman) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	arg := []string{"-R", "--noconfirm"}
	if purge {
		arg = []string{"-Rn", "--noconfirm"}
	}
	_, err := esegui(g.a, tempoGestore, "pacman", append(arg, nomi...)...)
	return err
}

func (g *gestorePacman) Integro() (bool, string, error) {
	if _, err := os.Stat(g.a.P("/var/lib/pacman/db.lck")); err == nil {
		return false, "/var/lib/pacman/db.lck is there", nil
	}
	return true, "", nil
}

// Ripara: the lock file left by a killed pacman is removed (no pacman is running: the
// engine's lock guarantees it), then pacman -Dk checks the database.
func (g *gestorePacman) Ripara() error {
	os.Remove(g.a.P("/var/lib/pacman/db.lck"))
	_, err := esegui(g.a, tempoGestore, "pacman", "-Dk")
	return err
}
