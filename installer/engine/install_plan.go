package engine

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
)

// InstallOptions: the few things whoever installs chooses (§10: the port, who enters the card's
// groups) and where the packages come from (the single package, DECISIONI §10.36).
type InstallOptions struct {
	// Pacchetti: the packages/ folder of the .run (or, in the tests, any folder with
	// <target>/*.deb|*.rpm|*.pkg.tar.zst); "" ⇒ no package (RX-MANCA-004)
	Pacchetti string
	Utenti    []string // whom to put in the card's groups; empty ⇒ the machine's people
	Porta     int
	// Update: REMOTIX is already installed (a CONFIRMED installation): the plan puts only the
	// new packages of the .run; groups, port and service are already there
	Update bool
}

// InstallPlan: the plan of the installation (or upgrade) of REMOTIX (§6.0, redone on
// 10 Oct 2026 for DECISIONI §10.36). REMOTIX does NOT modify the system: no third-party repositories, drivers,
// desktops, firewalls or system belts. What is missing (Report.Missing) goes into the plan as
// BLOCKING and the operation stops before touching anything; the administrator provides it. The plan does:
// REMOTIX's packages from the .run (the manager takes the dependencies from the machine's repositories) →
// the card's groups (the exception the user wanted) → the port, if it is not the stock one →
// the switch-on. The manager simulates at once: the plan shows the exact packages before the question.
func InstallPlan(prof *ProfileV, rap *Report, cat *Catalog, env *Environment, o InstallOptions) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := strconv.Itoa(o.Porta)
	duty := "installation"
	if o.Update {
		duty = "upgrade"
	}
	pn := &Piano{Schema: Schema, Obj: "plan", ID: newID(), Made: now(), Duty: duty,
		Engine:  EngineRef{EngineVersion, EngineDigest()},
		Catalog: CatalogRef{cat.Ver, cat.Digest}, PlatformV: rap.PlatformV,
		Depends: []string{}, Consents: []string{}, Condizioni: []Condition{}, NotDone: []Message{}}

	// what is missing, and the reasons why REMOTIX does not work on this machine: they are stated, and it stops
	pn.NotDone = append(pn.NotDone, rap.Missing...)
	for _, m := range rap.Messages {
		if m.Severity == BLOCKING && !hasCode(pn.NotDone, m.Codice) {
			pn.NotDone = append(pn.NotDone, m)
		}
	}
	if !hasGoodDesktop(rap) && !rap.NoDesktop {
		for _, e := range rap.Desktop {
			for _, m := range e.Reasons {
				if !hasCode(pn.NotDone, m.Codice) {
					pn.NotDone = append(pn.NotDone, m)
				}
			}
		}
	}

	file, err := RunPackages(env, o.Pacchetti)
	if err != nil {
		pn.NotDone = append(pn.NotDone, Msg("RX-MANCA-004", err.Error()))
	} else {
		// the dependencies the desktop requires (labwc, wlr-randr, a font): with the manager, together
		pn.Azioni = append(pn.Azioni, PlanPackages("packages", strings.Join(file, ","), strings.Join(rap.DependencyNames(), ",")))
		pn.Dipendenze = rap.Dipendenze
	}
	// DECISIONS §10.50 (the exception to §10.36): the package brings an ACTIVE polkit rule; the
	// plan says so before the question, on install and on upgrade alike
	pn.Declared = append(pn.Declared, T("np.polkit"))
	if !o.Update {
		users := o.Utenti
		if len(users) == 0 {
			users = People(env)
		}
		groups := CardGroups(env)
		for _, u := range users {
			for _, g := range groups {
				pn.Azioni = append(pn.Azioni, PlanGroup("group-"+u+"-"+g, u, g))
			}
		}
		if len(groups) == 0 {
			pn.NotDone = append(pn.NotDone, Message{Severity: INFO, Testo: T("np.nessun_gruppo")})
		} else {
			pn.Declared = append(pn.Declared, T("np.groups", strings.Join(groups, ", ")))
		}
		// the chosen port (§6.4: the defaults in /usr, the choices in /etc): remotix.service reads it
		// from /etc/remotix/remotix.conf.d/*.conf. Only if it is not the stock one
		if o.Porta != 7447 {
			pn.Azioni = append(pn.Azioni, PlanWriteFile("port", "/etc/remotix/remotix.conf.d/port.conf", "REMOTIX_PORT="+ps+"\n", "0644"))
		}
		pn.Azioni = append(pn.Azioni, PlanStartService("service", "remotix.service", o.Porta))
		// the firewall is the administrator's (§10.36): it is stated, not opened
		switch g := env.Firewall.Nome(); g {
		case "none", "":
		default:
			pn.NotDone = append(pn.NotDone, Message{Severity: WARNING, Testo: T("np.firewall", g, ps)})
		}
		pn.NotDone = append(pn.NotDone, Message{Severity: INFO, Testo: T("np.sospensione")})
	}
	for _, e := range rap.Desktop {
		if e.Lvl != NOT_SUPPORTED && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			pn.Condizioni = append(pn.Condizioni, e.Condizioni...)
		}
	}
	// the manager's simulation: the exact packages, BEFORE the question. If the manager cannot
	// install (a dependency no repository of the machine provides), it says so here
	if !Blocked(pn) && env.Pacchetti != nil && len(file) > 0 {
		var genuine []string
		for _, f := range file {
			genuine = append(genuine, env.P(f))
		}
		ins, err := env.Pacchetti.Simulate(genuine, rap.DependencyNames())
		if err != nil {
			pn.NotDone = append(pn.NotDone, messageSimulate(err))
		}
		pn.Pacchetti = ins
	}
	im, err := ComputeFingerprint(prof, cat, pn.Azioni, pn.Depends, &Context{Env: env})
	if err != nil {
		return nil, err
	}
	pn.Fingerprint = *im
	return pn, nil
}

// hasGoodDesktop: at least one installed desktop that REMOTIX supports.
func hasGoodDesktop(rap *Report) bool {
	for _, e := range rap.Desktop {
		if e.Lvl != NOT_SUPPORTED && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			return true
		}
	}
	return false
}

// Bloccato: the plan has a BLOCKING message (what is missing): it is not applied.
func Blocked(p *Piano) bool {
	for _, m := range p.NotDone {
		if m.Severity == BLOCKING {
			return true
		}
	}
	return false
}

// NothingToDo: the simulation says the .run's packages are all already installed, at that
// version (an upgrade with the same .run).
func NothingToDo(p *Piano) bool {
	if len(p.Pacchetti) == 0 {
		return false
	}
	for _, a := range p.Pacchetti {
		if a.Outcome != "present" {
			return false
		}
	}
	return true
}

// RunPackages: the files of REMOTIX's packages for THIS distribution, in the folder
// packages/<target>/ of the .run. remotix-selinux only where there is the targeted policy (the remotix
// package requires it there, and elsewhere it would bring the whole policy along).
func RunPackages(a *Environment, dir string) ([]string, error) {
	if dir == "" {
		return nil, fmt.Errorf("no packages: run the REMOTIX .run file")
	}
	b := Target(a)
	entries, _ := filepath.Glob(filepath.Join(a.P(dir), b, "*"))
	var r []string
	selinux := false
	if st, err := os.Stat(a.P("/etc/selinux/targeted")); err == nil && st.IsDir() {
		selinux = true
	}
	for _, v := range entries {
		n := filepath.Base(v)
		if !strings.HasSuffix(n, ".deb") && !strings.HasSuffix(n, ".rpm") && !strings.HasSuffix(n, ".pkg.tar.zst") {
			continue
		}
		if strings.HasPrefix(n, "remotix-selinux") && !selinux {
			continue
		}
		abs, err := filepath.Abs(filepath.Join(dir, b, n))
		if err != nil {
			return nil, err
		}
		r = append(r, abs)
	}
	sort.Strings(r)
	if len(r) == 0 {
		return nil, fmt.Errorf("%s: no packages for %s", dir, b)
	}
	return r, nil
}

// People: the machine's human users (uid between UID_MIN and 60000, with a real shell).
func People(a *Environment) []string {
	min := uidMin(a)
	f, err := os.Open(a.P("/etc/passwd"))
	if err != nil {
		return nil
	}
	defer f.Close()
	var r []string
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) < 7 {
			continue
		}
		uid, _ := strconv.Atoi(c[2])
		if uid < min || uid >= 60000 || strings.HasSuffix(c[6], "nologin") || strings.HasSuffix(c[6], "false") {
			continue
		}
		r = append(r, c[0])
	}
	sort.Strings(r)
	return r
}

// CardGroups: the groups of the render nodes (/dev/dri/renderD*), root excluded — the same choice
// as the product's first-login enrolment (src/child.c, collect_card_groups(); DECISIONS §11.38): every
// compositor opens renderD* only, never card* (§11.4), so «video» is not added any more. The group is
// read from each node (DECISIONI §7.21: the numbers and even the names change from one machine to
// another).
func CardGroups(a *Environment) []string {
	gr, _ := ReadGroups(a.P("/etc/group"))
	name := map[string]string{}
	for n, v := range gr {
		name[v[0]] = n
	}
	seen_items := map[string]bool{}
	var r []string
	entries, _ := filepath.Glob(a.P("/dev/dri") + "/renderD*")
	for _, v := range entries {
		gid, ok := nodeGid(v)
		if !ok || gid == 0 {
			continue
		}
		n := name[strconv.Itoa(int(gid))]
		if n != "" && !seen_items[n] {
			seen_items[n] = true
			r = append(r, n)
		}
	}
	sort.Strings(r)
	return r
}

// nodeGid: the group that owns a device node (a variable so the tests can give their fake nodes
// the gid of a real distribution without being root).
var nodeGid = func(fpath string) (uint32, bool) {
	st, err := os.Stat(fpath)
	if err != nil {
		return 0, false
	}
	sys, ok := st.Sys().(*syscall.Stat_t)
	if !ok {
		return 0, false
	}
	return sys.Gid, true
}
