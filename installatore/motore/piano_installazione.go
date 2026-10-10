package motore

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
	// Packets: the packages/ folder of the .run (or, in the tests, any folder with
	// <target>/*.deb|*.rpm|*.pkg.tar.zst); "" ⇒ no package (RX-MANCA-004)
	Packets string
	Users   []string // whom to put in the card's groups; empty ⇒ the machine's people
	Port    int
	// Update: REMOTIX is already installed (a CONFIRMED installation): the plan puts only the
	// new packages of the .run; groups, port and service are already there
	Update bool
}

// PlanInstallation: the plan of the installation (or upgrade) of REMOTIX (§6.0, redone on
// 10 Oct 2026 for DECISIONI §10.36). REMOTIX does NOT modify the system: no third-party repositories, drivers,
// desktops, firewalls or system belts. What is missing (Report.Missing) goes into the plan as
// BLOCKING and the operation stops before touching anything; the administrator provides it. The plan does:
// REMOTIX's packages from the .run (the manager takes the dependencies from the machine's repositories) →
// the card's groups (the exception the user wanted) → the port, if it is not the stock one →
// the switch-on. The manager simulates at once: the plan shows the exact packages before the question.
func PlanInstallation(prof *Profile, rap *Report, cat *Catalog, amb *Environment, o InstallOptions) (*Piano, error) {
	if o.Port == 0 {
		o.Port = 7447
	}
	ps := strconv.Itoa(o.Port)
	duty := "installation"
	if o.Update {
		duty = "upgrade"
	}
	pn := &Piano{Schema: Schema, Object: "plan", ID: newID(), Created: now(), Duty: duty,
		Engine:  EngineRef{EngineVersion, EngineDigest()},
		Catalog: CatalogRef{cat.Version, cat.Digest}, Platform: rap.Platform,
		Depends: []string{}, Consents: []string{}, Conditions: []Condition{}, NotDone: []Message{}}

	// what is missing, and the reasons why REMOTIX does not work on this machine: they are stated, and it stops
	pn.NotDone = append(pn.NotDone, rap.Missing...)
	for _, m := range rap.Messages {
		if m.Severity == BLOCKING && !hasCode(pn.NotDone, m.Code) {
			pn.NotDone = append(pn.NotDone, m)
		}
	}
	if !hasGoodDesktop(rap) && !rap.NoDesktop {
		for _, e := range rap.Desktop {
			for _, m := range e.Reasons {
				if !hasCode(pn.NotDone, m.Code) {
					pn.NotDone = append(pn.NotDone, m)
				}
			}
		}
	}

	file, err := RunPackages(amb, o.Packets)
	if err != nil {
		pn.NotDone = append(pn.NotDone, Msg("RX-MANCA-004", err.Error()))
	} else {
		// the dependencies the desktop requires (labwc, wlr-randr, a font): with the manager, together
		pn.Actions = append(pn.Actions, PlanPackages("packages", strings.Join(file, ","), strings.Join(rap.DependencyNames(), ",")))
		pn.Dependencies = rap.Dependencies
	}
	if !o.Update {
		users := o.Users
		if len(users) == 0 {
			users = People(amb)
		}
		group_list := CardGroups(amb)
		for _, u := range users {
			for _, g := range group_list {
				pn.Actions = append(pn.Actions, PlanGroup("group-"+u+"-"+g, u, g))
			}
		}
		if len(group_list) == 0 {
			pn.NotDone = append(pn.NotDone, Message{Severity: INFO, Text: T("np.nessun_gruppo")})
		} else {
			pn.Declared = append(pn.Declared, T("np.group_list", strings.Join(group_list, ", ")))
		}
		// the chosen port (§6.4: the defaults in /usr, the choices in /etc): remotix.service reads it
		// from /etc/remotix/remotix.conf.d/*.conf. Only if it is not the stock one
		if o.Port != 7447 {
			pn.Actions = append(pn.Actions, PlanWriteFile("port", "/etc/remotix/remotix.conf.d/porta.conf", "REMOTIX_PORT="+ps+"\n", "0644"))
		}
		pn.Actions = append(pn.Actions, PlanStartService("service", "remotix.service", o.Port))
		// the firewall is the administrator's (§10.36): it is stated, not opened
		switch g := amb.Firewall.Name(); g {
		case "none", "":
		default:
			pn.NotDone = append(pn.NotDone, Message{Severity: WARNING, Text: T("np.firewall", g, ps)})
		}
		pn.NotDone = append(pn.NotDone, Message{Severity: INFO, Text: T("np.sospensione")})
	}
	for _, e := range rap.Desktop {
		if e.Level != NOT_SUPPORTED && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			pn.Conditions = append(pn.Conditions, e.Conditions...)
		}
	}
	// the manager's simulation: the exact packages, BEFORE the question. If the manager cannot
	// install (a dependency no repository of the machine provides), it says so here
	if !Blocked(pn) && amb.Packets != nil && len(file) > 0 {
		var genuine []string
		for _, f := range file {
			genuine = append(genuine, amb.P(f))
		}
		ins, err := amb.Packets.Simulate(genuine, rap.DependencyNames())
		if err != nil {
			pn.NotDone = append(pn.NotDone, messageSimulate(err))
		}
		pn.Packets = ins
	}
	im, err := ComputeFingerprint(prof, cat, pn.Actions, pn.Depends, &Context{Amb: amb})
	if err != nil {
		return nil, err
	}
	pn.Fingerprint = *im
	return pn, nil
}

// hasGoodDesktop: at least one installed desktop that REMOTIX supports.
func hasGoodDesktop(rap *Report) bool {
	for _, e := range rap.Desktop {
		if e.Level != NOT_SUPPORTED && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			return true
		}
	}
	return false
}

// Blocked: the plan has a BLOCKING message (what is missing): it is not applied.
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
	if len(p.Packets) == 0 {
		return false
	}
	for _, a := range p.Packets {
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
	min := 1000
	for _, f := range []string{"/etc/login.defs", "/usr/etc/login.defs"} {
		if t, ok := read_it(a, f); ok {
			for _, r := range strings.Split(t, "\n") {
				c := strings.Fields(r)
				if len(c) == 2 && c[0] == "UID_MIN" {
					if n, err := strconv.Atoi(c[1]); err == nil {
						min = n
					}
				}
			}
			break
		}
	}
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

// CardGroups: the groups of the card's nodes (/dev/dri/card* and renderD*), root excluded
// (DECISIONI §7.21: the numbers change from one machine to another, they are read from the nodes).
func CardGroups(a *Environment) []string {
	gr, _ := ReadGroups(a.P("/etc/group"))
	label_name := map[string]string{}
	for n, v := range gr {
		label_name[v[0]] = n
	}
	seen_items := map[string]bool{}
	var r []string
	entries, _ := filepath.Glob(a.P("/dev/dri") + "/*")
	for _, v := range entries {
		b := filepath.Base(v)
		if !strings.HasPrefix(b, "card") && !strings.HasPrefix(b, "renderD") {
			continue
		}
		st, err := os.Stat(v)
		if err != nil {
			continue
		}
		sys, ok := st.Sys().(*syscall.Stat_t)
		if !ok || sys.Gid == 0 {
			continue
		}
		n := label_name[strconv.Itoa(int(sys.Gid))]
		if n != "" && !seen_items[n] {
			seen_items[n] = true
			r = append(r, n)
		}
	}
	sort.Strings(r)
	return r
}
