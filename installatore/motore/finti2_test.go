package motore

// The other pieces of the fake machine: a package manager (installed database and a
// repository in JSON files, a transaction that can be interrupted halfway), the on/off state of the
// units and the boot target, logind's sessions.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"testing"
)

type fakePackage struct {
	Version string   `json:"versione"`
	Depends []string `json:"dipende,omitempty"`
}

type fakeManager struct{ radice string }

func (g *fakeManager) p(x string) string { return filepath.Join(g.radice, "var/lib", x) }

func readJSONFake(p string, v any) {
	if b, err := os.ReadFile(p); err == nil {
		json.Unmarshal(b, v)
	}
}

func (g *fakeManager) installati() map[string]string {
	m := map[string]string{}
	readJSONFake(g.p("finto-pacchetti.json"), &m)
	return m
}

func (g *fakeManager) deposito() map[string]fakePackage {
	m := map[string]fakePackage{}
	readJSONFake(g.p("finto-deposito.json"), &m)
	return m
}

func (g *fakeManager) Nome() string { return "finto" }

func (g *fakeManager) Versions(nomi []string) (map[string]string, error) {
	in := g.installati()
	r := map[string]string{}
	for _, n := range nomi {
		r[n] = in[n]
	}
	return r, nil
}

// chiusura: the packages to install (files + names + dependencies), in order.
func (g *fakeManager) chiusura(file, nomi []string) ([]Artifact, error) {
	dep := g.deposito()
	in := g.installati()
	var r []Artifact
	visti := map[string]bool{}
	var visit func(n string, pk fakePackage, origine, f string) error
	visit = func(n string, pk fakePackage, origine, f string) error {
		if visti[n] {
			return nil
		}
		visti[n] = true
		for _, d := range pk.Depends {
			dp, ok := dep[d]
			if !ok {
				return fmt.Errorf("dependency %s not in the repository", d)
			}
			if err := visit(d, dp, "repo", ""); err != nil {
				return err
			}
		}
		if in[n] == pk.Version {
			return nil
		}
		a := Artifact{Nome: n, Version: pk.Version, Origine: origine, Esito: "new"}
		if in[n] != "" {
			a.Esito, a.Prima = "upgraded", in[n]
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
	for _, n := range nomi {
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

func (g *fakeManager) Simula(file, nomi []string) ([]Artifact, error) {
	r, err := g.chiusura(file, nomi)
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, err
}

func (g *fakeManager) Installa(file, nomi []string) error {
	r, err := g.chiusura(file, nomi)
	if err != nil {
		return err
	}
	os.WriteFile(g.p("finto-pacchetti.transazione"), nil, 0o644)
	for i, a := range r {
		in := g.installati()
		in[a.Nome] = a.Version
		b, _ := json.Marshal(in)
		if err := ScriviAtomico(g.p("finto-pacchetti.json"), b, 0o644); err != nil {
			return err
		}
		if a.Nome == "sddm" { // a display manager's postinst: enables, and starts if policy-rc.d does not stop it
			os.WriteFile(filepath.Join(g.radice, "etc/systemd/system/sddm.service"), []byte("[Unit]\n"), 0o644)
			u := &fakeUnits{g.radice}
			u.Enable("sddm.service")
			if _, err := os.Stat(filepath.Join(g.radice, "usr/sbin/policy-rc.d")); err != nil {
				u.Start("sddm.service")
			}
			u.SetDefault("graphical.target")
		}
		if i == 0 {
			punto("pacchetti-a-meta", "")
		}
	}
	return os.Remove(g.p("finto-pacchetti.transazione"))
}

// SimulaTogli: whoever depends (also in turn) on the given names, among the installed ones.
func (g *fakeManager) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	in := g.installati()
	dep := g.deposito()
	via := map[string]bool{}
	for _, n := range nomi {
		via[n] = true
	}
	var altri []string
	for cambiato := true; cambiato; {
		cambiato = false
		for _, n := range sortedKeys(in) {
			if via[n] {
				continue
			}
			for _, d := range dep[n].Depends {
				if via[d] {
					via[n], cambiato = true, true
					altri = append(altri, n)
					break
				}
			}
		}
	}
	return altri, nil
}

func (g *fakeManager) Togli(nomi []string, purge bool) error {
	in := g.installati()
	if err := onlyThese(g, nomi, purge); err != nil {
		return err
	}
	for _, n := range nomi {
		delete(in, n)
		if n == "sddm" {
			os.Remove(filepath.Join(g.radice, "etc/systemd/system/sddm.service"))
		}
	}
	b, _ := json.Marshal(in)
	return ScriviAtomico(g.p("finto-pacchetti.json"), b, 0o644)
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

func (u *fakeUnits) attive() string { return filepath.Join(u.radice, "var/lib/finto-attive.json") }

func (u *fakeUnits) Attiva(n string) (string, error) {
	if readMap(u.attive())[n] {
		return "active", nil
	}
	return "inactive", nil
}
func (u *fakeUnits) Start(n string) error {
	m := readMap(u.attive())
	m[n] = true
	return writeMap(u.attive(), m)
}
func (u *fakeUnits) Ferma(n string) error {
	m := readMap(u.attive())
	delete(m, n)
	return writeMap(u.attive(), m)
}
func (u *fakeUnits) Reload(string) error { return nil }
func (u *fakeUnits) Default() (string, error) {
	b, err := os.ReadFile(filepath.Join(u.radice, "var/lib/finto-predefinito"))
	if err != nil {
		return "graphical.target", nil
	}
	return string(b), nil
}
func (u *fakeUnits) SetDefault(b string) error {
	return ScriviAtomico(filepath.Join(u.radice, "var/lib/finto-predefinito"), []byte(b), 0o644)
}

// ---- logind's sessions

type fakeSessions struct{ radice string }

func (s *fakeSessions) file() string { return filepath.Join(s.radice, "var/lib/finto-sessioni.json") }

func (s *fakeSessions) List() ([]Sessione, error) {
	var l []Sessione
	readJSONFake(s.file(), &l)
	return l, nil
}

func (s *fakeSessions) Signal(id string, sg int32) error { return s.Terminate(id) }

// the desktop in the user manager, fake: a number of processes per person
func (s *fakeSessions) grafica() string {
	return filepath.Join(s.radice, "var/lib/finto-grafica.json")
}
func (s *fakeSessions) Graphical(u string) (int, error) {
	m := map[string]int{}
	readJSONFake(s.grafica(), &m)
	return m[u], nil
}
func (s *fakeSessions) CloseGraphical(u string) ([]string, error) {
	m := map[string]int{}
	readJSONFake(s.grafica(), &m)
	delete(m, u)
	b, _ := json.Marshal(m)
	return []string{"graphical-session.target"}, ScriviAtomico(s.grafica(), b, 0o644)
}

func (s *fakeSessions) Terminate(id string) error {
	l, _ := s.List()
	var r []Sessione
	for _, x := range l {
		if x.ID != id {
			r = append(r, x)
		}
	}
	b, _ := json.Marshal(r)
	return ScriviAtomico(s.file(), b, 0o644)
}

// differencesAfterUndo: the machine as it was, EXCEPT the only INDIRECT change the trial plan
// makes and that rolling back does not undo by rule (§6.6.4): libcomune upgraded from 1.0 to 2.0.
func differencesAfterUndo(t testing.TB, prima, dopo map[string]string) []string {
	agg := Sha256([]byte(`{"bash":"5.2","libcomune":"2.0"}`))
	k := "var/lib/finto-pacchetti.json"
	if dopo[k] == "-rw-r--r-- "+agg[:16] {
		p2 := map[string]string{}
		for x, v := range prima {
			p2[x] = v
		}
		p2[k] = dopo[k]
		return differenze(p2, dopo)
	}
	return differenze(prima, dopo)
}
