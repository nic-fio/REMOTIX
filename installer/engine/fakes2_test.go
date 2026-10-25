package engine

// The other pieces of the fake machine: a package manager (installed database and a
// repository in JSON files, a transaction that can be interrupted halfway), the on/off state of the
// units and the boot target, logind's sessions.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"testing"
)

type fakePackage struct {
	Ver     string   `json:"versione"`
	Depends []string `json:"dipende,omitempty"`
}

type fakeManager struct{ root string }

func (g *fakeManager) p(x string) string { return filepath.Join(g.root, "var/lib", x) }

func readJSONFake(p string, v any) {
	if b, err := os.ReadFile(p); err == nil {
		json.Unmarshal(b, v)
	}
}

func (g *fakeManager) installs() map[string]string {
	m := map[string]string{}
	readJSONFake(g.p("finto-pacchetti.json"), &m)
	return m
}

func (g *fakeManager) repository() map[string]fakePackage {
	m := map[string]fakePackage{}
	readJSONFake(g.p("finto-deposito.json"), &m)
	return m
}

func (g *fakeManager) Nome() string { return "finto" }

func (g *fakeManager) Vers(names []string) (map[string]string, error) {
	in := g.installs()
	r := map[string]string{}
	for _, n := range names {
		r[n] = in[n]
	}
	return r, nil
}

// closing: the packages to install (files + names + dependencies), in order.
func (g *fakeManager) closing(file, names []string) ([]Artifact, error) {
	dep := g.repository()
	in := g.installs()
	var r []Artifact
	seen_items := map[string]bool{}
	var visit func(n string, pk fakePackage, origin, f string) error
	visit = func(n string, pk fakePackage, origin, f string) error {
		if seen_items[n] {
			return nil
		}
		seen_items[n] = true
		for _, d := range pk.Depends {
			dp, ok := dep[d]
			if !ok {
				return fmt.Errorf("dependency %s not in the repository", d)
			}
			if err := visit(d, dp, "repo", ""); err != nil {
				return err
			}
		}
		if in[n] == pk.Ver {
			return nil
		}
		a := Artifact{Nome: n, Ver: pk.Ver, Origine: origin, Outcome: "new"}
		if in[n] != "" {
			a.Outcome, a.Before = "upgraded", in[n]
		}
		r = append(r, a)
		return nil
	}
	for _, f := range file {
		var pk struct {
			Nome string `json:"nome"`
			fakePackage
		}
		readJSONFake(f, &pk)
		if err := visit(pk.Nome, pk.fakePackage, "file", f); err != nil {
			return nil, err
		}
	}
	for _, n := range names {
		pk, ok := dep[n]
		if !ok {
			return nil, fmt.Errorf("%s not in the repository", n)
		}
		if err := visit(n, pk, "repo", ""); err != nil {
			return nil, err
		}
	}
	return r, nil
}

func (g *fakeManager) Simulate(file, names []string) ([]Artifact, error) {
	r, err := g.closing(file, names)
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, err
}

func (g *fakeManager) Install(file, names []string) error {
	r, err := g.closing(file, names)
	if err != nil {
		return err
	}
	os.WriteFile(g.p("finto-pacchetti.transazione"), nil, 0o644)
	for i, a := range r {
		in := g.installs()
		in[a.Nome] = a.Ver
		b, _ := json.Marshal(in)
		if err := WriteAtomic(g.p("finto-pacchetti.json"), b, 0o644); err != nil {
			return err
		}
		if a.Nome == "remotix" { // the REMOTIX package, when the test says so: its sysusers file, and the account its postinst makes
			if _, err := os.Stat(g.p("finto-crea-utente-rete")); err == nil {
				os.MkdirAll(filepath.Join(g.root, filepath.Dir(netSysusers)[1:]), 0o755)
				os.WriteFile(filepath.Join(g.root, netSysusers[1:]), []byte("u remotix - \"REMOTIX network side\" / /usr/sbin/nologin\n"), 0o644)
				// ⭐ What the package's postinst also leaves (tmpfiles.d): /var/lib/remotix/net, 0700, the network user's own — the
				// post-install «network-side» check (RX-NETUSER-003) fails without it.  A test cannot chown to uid 990, so the
				// account is made with the test's own uid/gid (as `netMachine()` does), and a system user by login.defs' UID_MIN.
				ownUid, ownGid := os.Getuid(), os.Getgid()
				if ownUid == 0 || ownGid == 0 {
					ownUid, ownGid = 990, 990 // root can chown anything; and uid/gid 0 is never the network user's (PersonAccount)
				}
				uid, gid := strconv.Itoa(ownUid), strconv.Itoa(ownGid)
				os.MkdirAll(filepath.Join(g.root, NetDir[1:]), 0o700)
				os.Chmod(filepath.Join(g.root, NetDir[1:]), 0o700)
				// ⚠ login.defs is OVERWRITTEN here (only when this package is the one that makes the network user): the fake
				// «prova» at uid 1000 no longer counts as a person in THIS test only — nothing here may rely on it being one.
				// (And a test run as root has uid 0, which is root's, not ours: use 990.)
				os.WriteFile(filepath.Join(g.root, "etc/login.defs"), []byte("UID_MIN "+strconv.Itoa(ownUid+1)+"\n"), 0o644)
				for f, line := range map[string]string{"etc/passwd": "remotix:x:" + uid + ":" + gid + ":REMOTIX network side:/:/usr/sbin/nologin\n", "etc/group": "remotix:x:" + gid + ":\n"} {
					if h, err := os.OpenFile(filepath.Join(g.root, f), os.O_APPEND|os.O_WRONLY, 0o644); err == nil {
						h.WriteString(line)
						h.Close()
					}
				}
			}
		}
		if a.Nome == "sddm" { // a display manager's postinst: enables, and starts if policy-rc.d does not stop it
			os.WriteFile(filepath.Join(g.root, "etc/systemd/system/sddm.service"), []byte("[Unit]\n"), 0o644)
			u := &fakeUnits{g.root}
			u.Enable("sddm.service")
			if _, err := os.Stat(filepath.Join(g.root, "usr/sbin/policy-rc.d")); err != nil {
				u.Launch("sddm.service")
			}
			u.SetDefault("graphical.target")
		}
		if i == 0 {
			spot("pacchetti-a-meta", "")
		}
	}
	return os.Remove(g.p("finto-pacchetti.transazione"))
}

// SimulateRemove: whoever depends (also in turn) on the given names, among the installed ones.
func (g *fakeManager) SimulateRemove(names []string, purge bool) ([]string, error) {
	in := g.installs()
	dep := g.repository()
	via := map[string]bool{}
	for _, n := range names {
		via[n] = true
	}
	var others []string
	for changed := true; changed; {
		changed = false
		for _, n := range sortedKeys(in) {
			if via[n] {
				continue
			}
			for _, d := range dep[n].Depends {
				if via[d] {
					via[n], changed = true, true
					others = append(others, n)
					break
				}
			}
		}
	}
	return others, nil
}

func (g *fakeManager) Remove(names []string, purge bool) error {
	in := g.installs()
	if err := onlyThese(g, names, purge); err != nil {
		return err
	}
	for _, n := range names {
		delete(in, n)
		if n == "sddm" {
			os.Remove(filepath.Join(g.root, "etc/systemd/system/sddm.service"))
		}
	}
	b, _ := json.Marshal(in)
	return WriteAtomic(g.p("finto-pacchetti.json"), b, 0o644)
}

func (g *fakeManager) Intact() (bool, string, error) {
	if _, err := os.Stat(g.p("finto-pacchetti.transazione")); err == nil {
		return false, "transaction halfway", nil
	}
	return true, "", nil
}

func (g *fakeManager) Repair() error {
	os.Remove(g.p("finto-pacchetti.transazione"))
	return nil
}

// ---- units: on/off, boot target

func (u *fakeUnits) enabled_ones() string { return filepath.Join(u.root, "var/lib/finto-attive.json") }

func (u *fakeUnits) Active(n string) (string, error) {
	if readMap(u.enabled_ones())[n] {
		return "active", nil
	}
	return "inactive", nil
}
func (u *fakeUnits) Launch(n string) error {
	m := readMap(u.enabled_ones())
	m[n] = true
	return writeMap(u.enabled_ones(), m)
}
func (u *fakeUnits) Stop(n string) error {
	m := readMap(u.enabled_ones())
	delete(m, n)
	return writeMap(u.enabled_ones(), m)
}
func (u *fakeUnits) Reload(string) error { return nil }
func (u *fakeUnits) Default() (string, error) {
	b, err := os.ReadFile(filepath.Join(u.root, "var/lib/finto-predefinito"))
	if err != nil {
		return "graphical.target", nil
	}
	return string(b), nil
}
func (u *fakeUnits) SetDefault(b string) error {
	return WriteAtomic(filepath.Join(u.root, "var/lib/finto-predefinito"), []byte(b), 0o644)
}

// ---- logind's sessions

type fakeSessions struct{ root string }

func (s *fakeSessions) file() string { return filepath.Join(s.root, "var/lib/finto-sessioni.json") }

func (s *fakeSessions) Listing() ([]Session, error) {
	var l []Session
	readJSONFake(s.file(), &l)
	return l, nil
}

func (s *fakeSessions) Signal(id string, sg int32) error { return s.Terminate(id) }

// the desktop in the user manager, fake: a number of processes per person
func (s *fakeSessions) graphical() string {
	return filepath.Join(s.root, "var/lib/finto-grafica.json")
}
func (s *fakeSessions) Charts(u string) (int, error) {
	m := map[string]int{}
	readJSONFake(s.graphical(), &m)
	return m[u], nil
}
func (s *fakeSessions) CloseGraphical(u string) ([]string, error) {
	m := map[string]int{}
	readJSONFake(s.graphical(), &m)
	delete(m, u)
	b, _ := json.Marshal(m)
	return []string{"graphical-session.target"}, WriteAtomic(s.graphical(), b, 0o644)
}

func (s *fakeSessions) Terminate(id string) error {
	l, _ := s.Listing()
	var r []Session
	for _, x := range l {
		if x.ID != id {
			r = append(r, x)
		}
	}
	b, _ := json.Marshal(r)
	return WriteAtomic(s.file(), b, 0o644)
}

// differencesAfterUndo: the machine as it was, EXCEPT the only INDIRECT change the trial plan
// makes and that rolling back does not undo by rule (§6.6.4): libcomune upgraded from 1.0 to 2.0.
func differencesAfterUndo(t testing.TB, before, after map[string]string) []string {
	add := Sha256([]byte(`{"bash":"5.2","libcomune":"2.0"}`))
	k := "var/lib/finto-pacchetti.json"
	if after[k] == "-rw-r--r-- "+add[:16] {
		p2 := map[string]string{}
		for x, v := range before {
			p2[x] = v
		}
		p2[k] = after[k]
		return differences(p2, after)
	}
	return differences(before, after)
}
