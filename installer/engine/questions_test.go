package engine

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// singlePackage: the packages/ folder of a fake .run, with the REMOTIX package for the Debian 13
// of the fake machine (the fake manager reads the JSON: it depends on libnuova and libcomune).
func singlePackage(t *testing.T, root string) string {
	d := filepath.Join(root, "run/packages/debian13")
	os.MkdirAll(d, 0o755)
	if err := os.WriteFile(filepath.Join(d, "remotix_0.17.0-1_amd64.deb"),
		[]byte(`{"nome":"remotix","versione":"0.17.0-1","dipende":["libnuova","libcomune"]}`), 0o644); err != nil {
		t.Fatal(err)
	}
	return "/run/packages"
}

// DECISIONI §10.36: the plan does not modify the system — no repositories, firewalls, belts or desktops;
// the exact packages from the manager's simulation, before the question; the card's groups
// declared; the running firewall is stated, not opened.
func TestPlanDoesNotModifySystem(t *testing.T) {
	root := t.TempDir()
	prepareMachine(t, root)
	env := fakeEnvironment(root)
	prof := fakeProfile()
	cat := catalogTest(t)
	rap := Evaluate(cat, prof)
	p, err := InstallPlan(prof, rap, cat, env, InstallOptions{Pacchetti: singlePackage(t, root), Porta: 7447})
	if err != nil {
		t.Fatal(err)
	}
	if Blocked(p) {
		t.Fatalf("plan blocked: %+v", p.NotDone)
	}
	for _, a := range p.Azioni {
		switch a.Type {
		case "install-packages", "add-user-to-group", "write-file", "start-service":
		default:
			t.Errorf("the plan modifies the system with %s (%s)", a.ID, a.Type)
		}
	}
	outcomes := map[string]string{}
	for _, x := range p.Pacchetti {
		outcomes[x.Nome] = x.Outcome
	}
	if outcomes["remotix"] != "new" || outcomes["libnuova"] != "new" || outcomes["libcomune"] != "upgraded" {
		t.Errorf("the manager's simulation: %+v", p.Pacchetti)
	}
	fw := false
	for _, m := range p.NotDone {
		fw = fw || (m.Severity == WARNING && strings.Contains(m.Testo, "firewalld"))
	}
	if !fw {
		t.Errorf("the running firewall must be stated: %+v", p.NotDone)
	}
	// without the .run: the package is missing, and the plan stops
	q, err := InstallPlan(prof, rap, cat, env, InstallOptions{Porta: 7447})
	if err != nil || !Blocked(q) || !hasCode(q.NotDone, "RX-MANCA-004") {
		t.Errorf("without packages: %v %+v", err, q)
	}
}

// What is missing is stated and stops everything (DECISIONI §10.36): without a desktop RX-MANCA-001, on Alma without
// EPEL RX-MANCA-002 — without packages or commands suggested. labwc, wlr-randr and the font on the other hand
// are not missing: they are REMOTIX dependencies, in the plan (the user, 10 Oct). And a BLOCKING plan
// applied leads to BLOCKED without touching anything.
func TestMissingStopsAll(t *testing.T) {
	cat := catalogTest(t)
	cases := []struct {
		id, ver string
		extra   map[string]string
		code    string
	}{
		{"debian", "13", map[string]string{"desktop.gnome": "absent"}, "RX-MANCA-001"},
		{"almalinux", "10.1", map[string]string{"repo.epel": "absent"}, "RX-MANCA-002"},
	}
	for _, c := range cases {
		rap := Evaluate(cat, profileOf(c.id, c.ver, c.extra))
		if !hasCode(rap.Missing, c.code) {
			t.Errorf("%s %v: missing %s, the report says %+v", c.id, c.extra, c.code, rap.Missing)
		}
		for _, m := range rap.Missing {
			for _, x := range []string{"sudo", "dnf ", "apt ", "zypper", "pacman"} {
				if strings.Contains(m.Testo+m.Detail+m.Remediation, x) {
					t.Errorf("%s: the message suggests a command (%q): %+v", c.code, x, m)
				}
			}
		}
	}

	// XFCE without labwc, wlr-randr and fonts: no «missing», three dependencies with the desktop requiring them
	rap := Evaluate(cat, profileOf("debian", "13", map[string]string{"desktop.gnome": "absent", "desktop.xfce": "4.20.1",
		"package.labwc": "absent", "package.wlr-randr": "absent", "fonts.scalable": "0", "distro.family": "debian"}))
	if len(rap.Missing) > 0 {
		t.Errorf("XFCE without labwc: missing %+v", rap.Missing)
	}
	if got := strings.Join(rap.DependencyNames(), ","); got != "labwc,wlr-randr,fonts-dejavu-core" || rap.Dipendenze[0].Why != "XFCE" {
		t.Errorf("XFCE without labwc: dependencies %+v", rap.Dipendenze)
	}

	b := newBench(t)
	m := b.engine(t)
	var p Piano
	ReadJSON(b.piano, &p)
	p.NotDone = append(p.NotDone, Msg("RX-MANCA-003", "XFCE: labwc"))
	p.Approval = &Approval{Da: "prova", Modo: "a mano", DigestPiano: p.Digest()}
	WriteJSON(b.piano, &p)
	op, err := m.Apply(b.piano, false, "prova")
	if op == nil || op.State != BLOCKED || !strings.Contains(lastState(op), "RX-MANCA-003") {
		t.Errorf("missing: %v %v", op, err)
	}
	if d := differences(b.before, photo(t, b.root)); len(d) > 0 {
		t.Errorf("missing: the machine was touched: %v", d)
	}
}

// Stopping halfway (the «Cancel and put back as it was» button): between one step and the next, then everything is
// undone from the log (RX-AZIONE-006) and the machine goes back to how it was.
func TestStoppedByInstaller(t *testing.T) {
	b := newBench(t)
	m := b.engine(t)
	n := 0
	m.Stopped = func() bool { n++; return n > 2 } // after two steps
	op, err := m.Apply(b.piano, true, "prova")
	if op == nil || op.State != ROLLED_BACK {
		t.Fatalf("fermata: %v %v", op, err)
	}
	if d := differencesAfterUndo(t, b.before, photo(t, b.root)); len(d) > 0 {
		t.Errorf("stopped: the machine did not go back to how it was: %v", d)
	}
	if err := op.openLog(); err != nil {
		t.Fatal(err)
	}
	seen := false
	for _, e := range op.Reg.Events {
		seen = seen || (e.Type == EvState && e.A == ROLLING_BACK && e.Codice == "RX-AZIONE-006")
	}
	if !seen {
		t.Errorf("stopped: ROLLING_BACK with RX-AZIONE-006 is not in the log")
	}
}

// The chosen port ends up in the plan: a file in /etc/remotix/remotix.conf.d (remotix.service
// reads it), BEFORE the switch-on; with the stock one no file (`[M]` 30 Sep, leap16-kde in a
// box: the service started on 7447 and the engine verified it on 8532).
func TestPlanChosenPort(t *testing.T) {
	root := t.TempDir()
	prepareMachine(t, root)
	bundle := singlePackage(t, root)
	env := fakeEnvironment(root)
	prof := fakeProfile()
	cat := catalogTest(t)
	rap := Evaluate(cat, prof)
	for _, port := range []int{7447, 8531} {
		p, err := InstallPlan(prof, rap, cat, env, InstallOptions{Pacchetti: bundle, Porta: port})
		if err != nil {
			t.Fatal(err)
		}
		file, service := -1, -1
		for i, a := range p.Azioni {
			switch {
			case a.ID == "port" && a.Type == "write-file":
				file = i
				if a.Parameters["path"] != "/etc/remotix/remotix.conf.d/port.conf" || a.Parameters["content"] != "REMOTIX_PORT=8531\n" {
					t.Errorf("port %d: the file is %v", port, a.Parameters)
				}
			case a.Type == "start-service":
				service = i
			}
		}
		switch {
		case port == 7447 && file != -1:
			t.Errorf("stock port: no file in /etc, but there is one")
		case port != 7447 && file == -1:
			t.Errorf("port %d: the file in /etc/remotix/remotix.conf.d is missing", port)
		case file != -1 && file > service:
			t.Errorf("port %d: the file must be written BEFORE the switch-on (%d > %d)", port, file, service)
		}
	}
}
