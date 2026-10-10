package motore

import (
	"errors"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

// The distribution's package manager (§6.0, rule 1): it is IT that puts and removes the files
// of the packages; the engine decides, asks, checks and undoes. The engine launches it from the closed
// list (ambiente.go), never a shell.
//
// The set (§6.6.6, simplified on 10 Oct 2026, DECISIONI §10.36: «don't reinvent the wheel»):
// Simulate asks the manager what it would do — the exact list (name, version, architecture,
// origin, and what happens: new, upgraded from…, already present), which the plan shows BEFORE the
// question. Install lets the manager work as always: it resolves, downloads from the repositories the
// machine has, verifies the signatures. The engine has no cache and no sha256 of its own for the packages. Revoke simulates
// first and refuses if it would remove something not in the list (someone else's package that in the
// meantime depends on it): the managers' autoremove would also remove earlier orphans, belonging to others.
//
// Every method that launches the manager first waits for another program holding it (occupato.go).
//
// Tried on the VMs: apt (Debian 13) and dnf (Alma 10). zypper and pacman are written in the same
// shape but NOT yet tried on a real machine.

// Artifact: a line of the resolved set.
type Artifact struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Arch    string `json:"arch,omitempty"`
	Origin  string `json:"origin"`           // "file" (from the single package) or the machine's repository
	Outcome string `json:"result"`           // "new" · "upgraded" · "present"
	Before  string `json:"before,omitempty"` // the previous version, if upgraded
}

// Handler: the family's package manager.
type Handler interface {
	Name() string
	// Versions: the installed version for every name ("" = not installed).
	Versions(names []string) (map[string]string, error)
	// Simulate: what the manager would install, without touching anything. file = local packages (from the
	// single package), names = packages from the machine's repositories.
	Simulate(file, names []string) ([]Artifact, error)
	// Install: the manager installs, with the dependencies from the machine's repositories.
	Install(file, names []string) error
	// SimulateRemove: what the manager would remove BEYOND the given names (whoever depends on them), without
	// touching anything.
	SimulateRemove(names []string, purge bool) ([]string, error)
	// Revoke the given names, and only those (purge: the configuration too): if it would remove others,
	// RX-PACCHETTI-002 and nothing removed.
	Revoke(names []string, purge bool) error
	// Intact: the manager is not halfway through a transaction.
	Intact() (bool, string, error)
	// Repair: the manager's own remedy after an interruption (§6.6.3).
	Repair() error
}

// ChooseHandler: the family's one.
func ChooseHandler(a *Environment, fam string) Handler {
	switch fam {
	case "debian":
		return &aptManager{a}
	case "fedora":
		return &dnfManager{a}
	case "suse":
		return &zypperManager{a}
	case "arch":
		return &pacmanManager{a}
	}
	return nil
}

func execute(a *Environment, time_limit time.Duration, label_name string, arg ...string) (string, error) {
	out, c, err := a.Run(time_limit, label_name, arg...)
	if err != nil {
		return out, err
	}
	if c != 0 {
		return out, fmt.Errorf("%s %s: exit %d: %s", label_name, strings.Join(arg, " "), c, lastLines(out, 6))
	}
	return out, nil
}

func lastLines(s string, n int) string {
	r := strings.Split(strings.TrimSpace(s), "\n")
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return strings.Join(r, " | ")
}

const managerTimeout = 45 * time.Minute

// ---------------------------------------------------------------- apt (Debian, Ubuntu)

type aptManager struct{ a *Environment }

func (g *aptManager) Name() string { return "apt" }

var aptOptions = []string{"-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold", "-o", "APT::Get::Assume-Yes=true",
	"-o", "DPkg::Lock::Timeout=" + strconv.Itoa(int(BusyCap.Seconds()))}

func (g *aptManager) Versions(names []string) (map[string]string, error) {
	pk := PackageArchive(g.a, "debian", names)
	if !pk.read {
		return nil, errors.New("the dpkg database cannot be read")
	}
	r := map[string]string{}
	for _, n := range names {
		r[n] = pk.vers[n]
	}
	return r, nil
}

// «Inst name [old] (new repository [arch])»
var aptInst = regexp.MustCompile(`^Inst (\S+)(?: \[(\S+)\])? \((\S+) (.*?) \[(\S+)\]\)`)

func (g *aptManager) call_args(file, names []string) []string {
	return append(append([]string{}, file...), names...)
}

func (g *aptManager) Simulate(file, names []string) ([]Artifact, error) {
	if err := waitHandler(g.a, "debian"); err != nil {
		return nil, err
	}
	sim := func() (string, error) {
		return execute(g.a, managerTimeout, "apt-get", append(append([]string{"-s", "install"}, aptOptions...), g.call_args(file, names)...)...)
	}
	out, err := sim()
	if err != nil { // stale lists: they are refreshed (the repositories' signed metadata) and it is retried
		if _, e2 := execute(g.a, managerTimeout, "apt-get", "update"); e2 != nil {
			return nil, err
		}
		if out, err = sim(); err != nil {
			return nil, err
		}
	}
	local := map[string]bool{}
	for _, f := range file {
		if n, v, e := g.header(f); e == nil {
			local[n+" "+v] = true
		}
	}
	var r []Artifact
	for _, row := range strings.Split(out, "\n") {
		if strings.HasPrefix(row, "Remv ") || strings.HasPrefix(row, "Purg ") {
			return nil, fmt.Errorf("the transaction would remove a package: %s", row)
		}
		m := aptInst.FindStringSubmatch(row)
		if m == nil {
			continue
		}
		a := Artifact{Name: m[1], Version: m[3], Arch: m[5], Origin: m[4], Outcome: "new"}
		if m[2] != "" {
			a.Outcome, a.Before = "upgraded", m[2]
		}
		if local[a.Name+" "+a.Version] {
			a.Origin = "file"
		}
		r = append(r, a)
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Name < r[j].Name })
	return r, nil
}

// header of a local .deb (name, version), read with dpkg-deb.
func (g *aptManager) header(f string) (string, string, error) {
	out, err := execute(g.a, time.Minute, "dpkg-deb", "-W", "--showformat=${Package} ${Version}", f)
	if err != nil {
		return "", "", err
	}
	c := strings.Fields(out)
	if len(c) != 2 {
		return "", "", fmt.Errorf("dpkg-deb: %q", out)
	}
	return c[0], c[1], nil
}

// Install: apt installs the local files and downloads the dependencies from the machine's repositories.
func (g *aptManager) Install(file, names []string) error {
	if err := waitHandler(g.a, "debian"); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "apt-get", append(append([]string{"install"}, aptOptions...), g.call_args(file, names)...)...)
	return err
}

var aptRemove = regexp.MustCompile(`^(?:Remv|Purg) (\S+)`)

func aptVerb(purge bool) string {
	if purge {
		return "purge"
	}
	return "remove"
}

func (g *aptManager) SimulateRemove(names []string, purge bool) ([]string, error) {
	if err := waitHandler(g.a, "debian"); err != nil {
		return nil, err
	}
	out, err := execute(g.a, managerTimeout, "apt-get", append(append([]string{"-s", aptVerb(purge)}, aptOptions...), names...)...)
	if err != nil {
		return nil, err
	}
	var others []string
	for _, row := range strings.Split(out, "\n") {
		if m := aptRemove.FindStringSubmatch(row); m != nil {
			others = append(others, m[1])
		}
	}
	return notIn(others, names), nil
}

func (g *aptManager) Revoke(names []string, purge bool) error {
	if err := onlyThese(g, names, purge); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "apt-get", append(append([]string{aptVerb(purge)}, aptOptions...), names...)...)
	return err
}

// fuoriDa: the names of «tutti» that are not in «nomi» (without repetitions). An rpm key is removed
// by version (gpg-pubkey-…), and dnf shows it by name.
func notIn(all_v, names []string) []string {
	ours := map[string]bool{}
	for _, n := range names {
		ours[n] = true
		if strings.HasPrefix(n, "gpg-pubkey-") {
			ours["gpg-pubkey"] = true
		}
	}
	var r []string
	for _, n := range all_v {
		if !ours[n] {
			ours[n] = true
			r = append(r, n)
		}
	}
	return r
}

// onlyThese: the guard of Revoke — the manager would remove only the given names.
func onlyThese(g Handler, names []string, purge bool) error {
	others, err := g.SimulateRemove(names, purge)
	if err != nil {
		return err
	}
	if len(others) > 0 {
		return Error("RX-PACCHETTI-002", strings.Join(others, ", "))
	}
	return nil
}

func (g *aptManager) Intact() (bool, string, error) {
	out, c, err := g.a.Run(time.Minute, "dpkg", "--audit")
	if err != nil {
		return false, "", err
	}
	if c != 0 || strings.TrimSpace(out) != "" {
		return false, lastLines(out, 3), nil
	}
	return true, "", nil
}

func (g *aptManager) Repair() error {
	if err := waitHandler(g.a, "debian"); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "dpkg", "--configure", "-a")
	return err
}

// ---------------------------------------------------------------- dnf (Fedora, RHEL, Alma)

type dnfManager struct{ a *Environment }

func (g *dnfManager) Name() string { return "dnf" }

// rpmEVR: rpm's [epoch:]version-release, written as dnf and zypper write it in the transaction they
// resolve («1:1.7.0-9.fc44»; no epoch, no «:»). ⚠ Without the epoch the installed packages never matched
// the resolved ones that have one: `[M]` installa-91, fedora44, 10 Oct — «packages: HALF_DONE 104 of 112»,
// the 8 missing exactly libglvnd ×4, libogg, libtheora, libvisual, libvorbis.
const rpmEVR = `%|EPOCH?{%{EPOCH}:}|%{VERSION}-%{RELEASE}`

func rpmVersions(a *Environment, names []string) (map[string]string, error) {
	r := map[string]string{}
	if len(names) == 0 {
		return r, nil
	}
	out, _, err := a.Run(time.Minute, "rpm", append([]string{"-q", "--qf", `%{NAME} ` + rpmEVR + `\n`}, names...)...)
	if err != nil {
		return nil, err
	}
	for _, n := range names {
		r[n] = ""
	}
	for _, row := range strings.Split(out, "\n") {
		c := strings.Fields(row)
		if len(c) == 2 && !strings.HasPrefix(row, "package ") {
			r[c[0]] = c[1]
		}
	}
	return r, nil
}

func (g *dnfManager) Versions(names []string) (map[string]string, error) {
	return rpmVersions(g.a, names)
}

// Simulate: dnf's transaction with --assumeno (dnf 4 and dnf 5 write the table in the same
// order: name, architecture, version, repository). What gets installed, upgraded or
// DOWNGRADED is taken (a downgrade is an INDIRECT change like an upgrade); «@commandline» is a
// file of the single package.
func (g *dnfManager) Simulate(file, names []string) ([]Artifact, error) {
	if err := waitHandler(g.a, "fedora"); err != nil {
		return nil, err
	}
	out, c, err := g.a.Run(managerTimeout, "dnf", append([]string{"install", "--assumeno", "--setopt=localpkg_gpgcheck=0"}, append(append([]string{}, file...), names...)...)...)
	if err != nil {
		return nil, err
	}
	if !strings.Contains(out, "Transaction Summary") {
		if strings.Contains(out, "Nothing to do") {
			return g.present(file, names)
		}
		return nil, fmt.Errorf("dnf install --assumeno: exit %d: %s", c, lastLines(out, 6))
	}
	var r []Artifact
	in := false
	seen_items := map[string]bool{}
	for _, row := range strings.Split(out, "\n") {
		t := strings.TrimSpace(row)
		if strings.HasSuffix(t, ":") && !strings.HasPrefix(row, " ") {
			in = strings.HasPrefix(t, "Installing") || strings.HasPrefix(t, "Upgrading") || strings.HasPrefix(t, "Downgrading")
			continue
		}
		f := strings.Fields(t)
		if !in || len(f) < 4 || !arcs[f[1]] || seen_items[f[0]] {
			continue
		}
		seen_items[f[0]] = true
		ver := strings.TrimPrefix(f[2], "0:")
		a := Artifact{Name: f[0], Version: ver, Arch: f[1], Origin: f[3], Outcome: "new"}
		if f[3] == "@commandline" {
			a.Origin = "file"
		}
		r = append(r, a)
	}
	before, err := rpmVersions(g.a, namesOf(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := before[r[i].Name]; p != "" {
			r[i].Outcome, r[i].Before = "upgraded", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Name < r[j].Name })
	return r, nil
}

var arcs = map[string]bool{"x86_64": true, "noarch": true, "i686": true, "aarch64": true}

// present: nothing to do — the files' packages, already installed at the same version.
func (g *dnfManager) present(file, names []string) ([]Artifact, error) {
	var r []Artifact
	for _, f := range file {
		out, err := execute(g.a, time.Minute, "rpm", "-qp", "--qf", `RX %{NAME} `+rpmEVR+` %{ARCH}\n`, f)
		if err != nil {
			return nil, err
		}
		for _, row := range strings.Split(out, "\n") {
			if c := strings.Fields(row); len(c) == 4 && c[0] == "RX" {
				r = append(r, Artifact{Name: c[1], Version: c[2], Arch: c[3], Origin: "file", Outcome: "present"})
			}
		}
	}
	for _, n := range names {
		r = append(r, Artifact{Name: n, Origin: "repo", Outcome: "present"})
	}
	return r, nil
}

func namesOf(r []Artifact) []string {
	var n []string
	for _, a := range r {
		n = append(n, a.Name)
	}
	return n
}

// Install: dnf installs the files of the single package (without an rpm signature: the .run's sha256
// guarantees them) and takes the dependencies from the machine's repositories, with their signatures.
func (g *dnfManager) Install(file, names []string) error {
	if err := waitHandler(g.a, "fedora"); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "dnf", append([]string{"install", "-y", "--setopt=localpkg_gpgcheck=0"}, append(append([]string{}, file...), names...)...)...)
	return err
}

func (g *dnfManager) SimulateRemove(names []string, purge bool) ([]string, error) {
	if err := waitHandler(g.a, "fedora"); err != nil {
		return nil, err
	}
	// dnf remove also removes whoever depends on these: it is checked with --assumeno
	out, _, err := g.a.Run(managerTimeout, "dnf", append([]string{"remove", "--assumeno", "--setopt=clean_requirements_on_remove=0"}, names...)...)
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
		others := notIn(dnfProblems(out), names)
		if len(others) == 0 {
			return nil, fmt.Errorf("dnf remove --assumeno %s: %s", strings.Join(names, " "), lastLines(out, 6))
		}
		return others, nil
	}
	var all_v []string
	in := false
	for _, row := range strings.Split(out, "\n") {
		t := strings.TrimSpace(row)
		if strings.HasPrefix(t, "Removing") || strings.HasPrefix(t, "Rimozione") {
			in = true
			continue
		}
		if in && (t == "" || strings.HasPrefix(t, "Transaction Summary") || strings.HasPrefix(t, "Riepilogo")) {
			in = false
		}
		if c := strings.Fields(t); in && len(c) >= 3 && !strings.HasSuffix(c[0], ":") {
			all_v = append(all_v, c[0])
		}
	}
	return notIn(all_v, names), nil
}

// dnfProblems: the packages named in the «Problem» lines of a dnf solver that does not resolve — the protected ones
// («protected packages: a, b») and the installed ones that need what is being removed («installed
// package NEVRA requires …»); the NEVRA goes back to a name.
func dnfProblems(out string) []string {
	var r []string
	for _, row := range strings.Split(out, "\n") {
		t := strings.TrimSpace(row)
		if _, after, ok := strings.Cut(t, "protected packages: "); ok {
			for _, n := range strings.Split(after, ",") {
				if n = strings.TrimSpace(n); n != "" {
					r = append(r, n)
				}
			}
			continue
		}
		for _, mark := range []string{"installed package ", "il pacchetto installato "} {
			if _, after, ok := strings.Cut(t, mark); ok {
				if f := strings.Fields(after); len(f) > 0 {
					r = append(r, nameFromNevra(f[0]))
				}
			}
		}
	}
	return notIn(r, nil)
}

// nameFromNevra: «libheif-1.23.5-3.fc44.x86_64» → «libheif» (strip the architecture, then version and release).
func nameFromNevra(nevra string) string {
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

func (g *dnfManager) Revoke(names []string, purge bool) error {
	if err := onlyThese(g, names, purge); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "dnf", append([]string{"remove", "-y", "--setopt=clean_requirements_on_remove=0"}, names...)...)
	return err
}

func (g *dnfManager) Intact() (bool, string, error) {
	// a half-done rpm transaction leaves duplicate packages (two versions of the same one)
	out, c, err := g.a.Run(time.Minute, "rpm", "-qa", "--qf", `%{NAME}.%{ARCH}\n`)
	if err != nil {
		return false, "", err
	}
	if c != 0 {
		return false, lastLines(out, 3), nil
	}
	seen_items := map[string]bool{}
	for _, n := range strings.Fields(out) {
		if seen_items[n] && !strings.HasPrefix(n, "gpg-pubkey") && !strings.HasPrefix(n, "kernel") {
			return false, "duplicate: " + n, nil
		}
		seen_items[n] = true
	}
	return true, "", nil
}

// Repair: dnf repeats the transaction; here we go back to a coherent state by removing the duplicates.
func (g *dnfManager) Repair() error {
	if err := waitHandler(g.a, "fedora"); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "dnf", "remove", "-y", "--duplicates")
	return err
}

// ---------------------------------------------------------------- zypper (openSUSE) — not tried

type zypperManager struct {
	a *Environment
}

// fileArg: the files of the single package have no rpm signature (the .run's sha256 guarantees them):
// zypper would refuse them ([M] 30 Sep, tumbleweed-kde: «Signature verification failed [6-File is
// unsigned]»). ⚠ It applies ONLY to those files; the repositories' packages stay verified by zypper.
func (g *zypperManager) fileArg(file []string) []string {
	if len(file) == 0 {
		return nil
	}
	return []string{"--allow-unsigned-rpm"}
}

func (g *zypperManager) Name() string { return "zypper" }

func (g *zypperManager) Versions(names []string) (map[string]string, error) {
	return rpmVersions(g.a, names)
}

func (g *zypperManager) Simulate(file, names []string) ([]Artifact, error) {
	if err := waitHandler(g.a, "suse"); err != nil {
		return nil, err
	}
	out, err := execute(g.a, managerTimeout, "zypper", append([]string{"--non-interactive", "--xmlout", "install", "--dry-run"}, append(append(g.fileArg(file), file...), names...)...)...)
	if err != nil {
		return nil, err
	}
	var r []Artifact
	re := regexp.MustCompile(`<solvable type="package" name="([^"]+)" edition="([^"]+)" arch="([^"]+)"`)
	for _, m := range re.FindAllStringSubmatch(out, -1) {
		r = append(r, Artifact{Name: m[1], Version: m[2], Arch: m[3], Origin: "repo", Outcome: "new"})
	}
	before, err := rpmVersions(g.a, namesOf(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := before[r[i].Name]; p != "" {
			r[i].Outcome, r[i].Before = "upgraded", p
		}
	}
	return r, nil
}

func (g *zypperManager) Install(file, names []string) error {
	if err := waitHandler(g.a, "suse"); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "zypper", append([]string{"--non-interactive", "install"}, append(append(g.fileArg(file), file...), names...)...)...)
	return err
}

var zypperSolvable = regexp.MustCompile(`<solvable type="package" name="([^"]+)"`)

func (g *zypperManager) SimulateRemove(names []string, purge bool) ([]string, error) {
	if err := waitHandler(g.a, "suse"); err != nil {
		return nil, err
	}
	out, err := execute(g.a, managerTimeout, "zypper", append([]string{"--non-interactive", "--xmlout", "remove", "--dry-run"}, names...)...)
	if err != nil {
		return nil, err
	}
	var all_v []string
	for _, m := range zypperSolvable.FindAllStringSubmatch(out, -1) {
		all_v = append(all_v, m[1])
	}
	return notIn(all_v, names), nil
}

func (g *zypperManager) Revoke(names []string, purge bool) error {
	if err := onlyThese(g, names, purge); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "zypper", append([]string{"--non-interactive", "remove"}, names...)...)
	return err
}

func (g *zypperManager) Intact() (bool, string, error) {
	out, c, err := g.a.Run(managerTimeout, "zypper", "--non-interactive", "verify", "--dry-run")
	if err != nil {
		return false, "", err
	}
	return c == 0, lastLines(out, 2), nil
}

func (g *zypperManager) Repair() error {
	if err := waitHandler(g.a, "suse"); err != nil {
		return err
	}
	_, err := execute(g.a, managerTimeout, "zypper", "--non-interactive", "verify")
	return err
}

// ---------------------------------------------------------------- pacman (Arch) — not tried

type pacmanManager struct{ a *Environment }

func (g *pacmanManager) Name() string { return "pacman" }

func (g *pacmanManager) Versions(names []string) (map[string]string, error) {
	pk := PackageArchive(g.a, "arch", names)
	if !pk.read {
		return nil, errors.New("the pacman database cannot be read")
	}
	r := map[string]string{}
	for _, n := range names {
		r[n] = pk.vers[n]
	}
	return r, nil
}

func (g *pacmanManager) Simulate(file, names []string) ([]Artifact, error) {
	if err := waitHandler(g.a, "arch"); err != nil {
		return nil, err
	}
	// the whole transaction (the files of the single package and the repositories' packages, with the
	// dependencies): pacman -U/-S --print says what it would install, without touching anything
	var line_list []string
	if len(file) > 0 {
		out, err := execute(g.a, managerTimeout, "pacman", append([]string{"-U", "--needed", "--print", "--print-format", "%n %v %a %r %l"}, file...)...)
		if err != nil {
			return nil, err
		}
		line_list = append(line_list, strings.Split(out, "\n")...)
	}
	if len(names) > 0 {
		out, err := execute(g.a, managerTimeout, "pacman", append([]string{"-S", "--needed", "--print", "--print-format", "%n %v %a %r %l"}, names...)...)
		if err != nil {
			return nil, err
		}
		line_list = append(line_list, strings.Split(out, "\n")...)
	}
	var r []Artifact
	seen_items := map[string]bool{}
	for _, row := range line_list {
		c := strings.Fields(row)
		if len(c) != 5 || seen_items[c[0]] {
			continue
		}
		seen_items[c[0]] = true
		a := Artifact{Name: c[0], Version: c[1], Arch: c[2], Origin: c[3], Outcome: "new"}
		if strings.HasPrefix(c[4], "file://") || strings.HasPrefix(c[4], "/") {
			a.Origin = "file"
		}
		r = append(r, a)
	}
	before, err := g.Versions(namesOf(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := before[r[i].Name]; p != "" {
			r[i].Outcome, r[i].Before = "upgraded", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Name < r[j].Name })
	return r, nil
}

func (g *pacmanManager) Install(file, names []string) error {
	if err := waitHandler(g.a, "arch"); err != nil {
		return err
	}
	if len(names) > 0 {
		if _, err := execute(g.a, managerTimeout, "pacman", append([]string{"-S", "--needed", "--noconfirm"}, names...)...); err != nil {
			return err
		}
	}
	if len(file) == 0 {
		return nil
	}
	// -U takes the files' dependencies from the machine's repositories
	_, err := execute(g.a, managerTimeout, "pacman", append([]string{"-U", "--needed", "--noconfirm"}, file...)...)
	return err
}

func (g *pacmanManager) SimulateRemove(names []string, purge bool) ([]string, error) {
	if err := waitHandler(g.a, "arch"); err != nil {
		return nil, err
	}
	// ⚠ pacman -R does not remove whoever depends: if someone depends, the simulation FAILS and says so
	// («removing X breaks dependency 'X' required by Y»): whoever depends is Y
	out, c, err := g.a.Run(managerTimeout, "pacman", append([]string{"-R", "--print", "--print-format", "%n"}, names...)...)
	if err != nil {
		return nil, err
	}
	if c != 0 {
		var r []string
		for _, m := range pacmanBreaks.FindAllStringSubmatch(out, -1) {
			r = append(r, m[1])
		}
		if len(r) == 0 {
			return nil, fmt.Errorf("pacman -R --print: exit %d: %s", c, lastLines(out, 6))
		}
		return notIn(r, names), nil
	}
	return notIn(strings.Fields(out), names), nil
}

var pacmanBreaks = regexp.MustCompile(`required by (\S+)`)

func (g *pacmanManager) Revoke(names []string, purge bool) error {
	if err := onlyThese(g, names, purge); err != nil {
		return err
	}
	arg := []string{"-R", "--noconfirm"}
	if purge {
		arg = []string{"-Rn", "--noconfirm"}
	}
	_, err := execute(g.a, managerTimeout, "pacman", append(arg, names...)...)
	return err
}

func (g *pacmanManager) Intact() (bool, string, error) {
	// a running pacman holds db.lck: it is waited for. If it is still there, no pacman has it open
	if err := waitHandler(g.a, "arch"); err != nil {
		return false, "", err
	}
	if _, err := os.Stat(g.a.P("/var/lib/pacman/db.lck")); err == nil {
		return false, "/var/lib/pacman/db.lck is there and no program has it open (left by a pacman that stopped half-way)", nil
	}
	return true, "", nil
}

// Repair: the lock file left by a killed pacman is removed (no program has it open: waitHandler
// waited for it), then pacman -Dk checks the database.
func (g *pacmanManager) Repair() error {
	if err := waitHandler(g.a, "arch"); err != nil {
		return err
	}
	os.Remove(g.a.P("/var/lib/pacman/db.lck"))
	_, err := execute(g.a, managerTimeout, "pacman", "-Dk")
	return err
}
