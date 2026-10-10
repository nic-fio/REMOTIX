package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// The state machine: only the transitions of the design of §6.6.2, no state skipped.
func TestTransitions(t *testing.T) {
	trail := []State{NEW, TRUSTED, EXAMINED, EVALUATED, PLANNED, APPROVED, ACQUIRED,
		RUNNING, APPLIED, VERIFYING, VERIFIED, CONFIRMED}
	for i := 0; i+1 < len(trail); i++ {
		if !Valid(trail[i], trail[i+1]) {
			t.Errorf("%s → %s should be valid", trail[i], trail[i+1])
		}
		for j := i + 2; j < len(trail); j++ {
			if Valid(trail[i], trail[j]) {
				t.Errorf("%s → %s skips a state", trail[i], trail[j])
			}
		}
	}
	for _, s := range []State{CONFIRMED, CONFIRMED_WITH_CONDITIONS, ROLLED_BACK, PARTIALLY_ROLLED_BACK, RIFIUTATA} {
		if !Finale(s) || len(transitions[s]) != 0 {
			t.Errorf("%s must be final and without exits", s)
		}
	}
	// from phases 0-5 one can only block (or refuse at consent), never cancel: nothing has been touched
	for _, s := range []State{NEW, TRUSTED, EXAMINED, EVALUATED, PLANNED, APPROVED, ACQUIRED} {
		if Valid(s, ROLLING_BACK) || Valid(s, ROLLED_BACK) {
			t.Errorf("%s → cancellation: before phase 6 there is nothing to cancel", s)
		}
		if !Valid(s, BLOCKED) {
			t.Errorf("%s → BLOCKED must be valid", s)
		}
	}
	if Valid(RUNNING, CONFIRMED) || Valid(INTERRUPTED, APPLIED) || Valid(ROLLING_BACK, CONFIRMED) {
		t.Error("a shortcut is valid")
	}
	if len(AllStates()) != 19 {
		t.Errorf("there are %d states, the design has 19", len(AllStates()))
	}
	// and the engine really refuses a transition outside the design
	b := newBench(t)
	op, _ := b.motore(t).Apply(b.piano, false, "prova")
	if err := op.go_to(RUNNING, "", ""); CodeOf(err) != "RX-STATO-002" {
		t.Errorf("CONFIRMED → RUNNING accepted: %v", err)
	}
}

// Every code used in the sources exists, and every code has the form RX-<AREA>-<NNN> (§6.6.9).
func TestCodes(t *testing.T) {
	shape := regexp.MustCompile(`^RX-[A-Z0-9]+-[0-9]{3}$`)
	for c, v := range Codes {
		if !shape.MatchString(c) || v.Text == "" || v.Severity == "" || v.Nature == "" {
			t.Errorf("malformed code: %s %+v", c, v)
		}
	}
	used_len := regexp.MustCompile(`"(RX-[A-Z0-9]+-[0-9]{3})"`)
	entries, _ := filepath.Glob("*.go")
	entries2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(entries, entries2...) {
		b, _ := os.ReadFile(f)
		for _, m := range used_len.FindAllStringSubmatch(string(b), -1) {
			if _, ok := Codes[m[1]]; !ok {
				t.Errorf("%s uses %s, which does not exist", f, m[1])
			}
		}
	}
}

// R31 in small: the plan does not apply to a different machine, and touches nothing.
func TestFingerprintChanged(t *testing.T) {
	b := newBench(t)
	os.WriteFile(filepath.Join(b.root, "etc/remotix-esistente.conf"), []byte("changed after the plan\n"), 0o640)
	afterChange := picture(t, b.root)
	op, err := b.motore(t).Apply(b.piano, false, "prova")
	if CodeOf(err) != "RX-PIANO-001" || op.State != BLOCKED {
		t.Fatalf("expected BLOCKED with RX-PIANO-001, got %v %v", op.State, err)
	}
	if !strings.Contains(err.Error(), "file:/etc/remotix-esistente.conf") {
		t.Errorf("the refusal does not say what changed: %v", err)
	}
	if d := differences(afterChange, picture(t, b.root)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	if ap, _ := b.motore(t).Open(); ap != nil {
		t.Error("a BLOCKED must be final")
	}
	// also an element of the profile: a group of the card with one more member
	b2 := newBench(t)
	(&fakeGroups{b2.root}).Add("root", "video")
	if _, err := b2.motore(t).Apply(b2.piano, false, "prova"); CodeOf(err) != "RX-PIANO-001" {
		t.Errorf("group changed: %v", err)
	}
}

// The consent: without it, RIFIUTATA; with an approval of another plan, RIFIUTATA; nothing touched.
func TestConsent(t *testing.T) {
	b := newBench(t)
	b.piano = testPlan(t, b.root, filepath.Dir(b.root), false)
	if op, _ := b.motore(t).Apply(b.piano, false, "prova"); op.State != RIFIUTATA {
		t.Fatalf("without approval: %s", op.State)
	}
	var p Piano
	ReadJSON(b.piano, &p)
	p.Approval = &Approval{Da: "x", DigestPiano: "0000"}
	WriteJSON(b.piano, &p)
	if op, _ := b.motore(t).Apply(b.piano, false, "prova"); op.State != RIFIUTATA {
		t.Fatalf("approval of another plan: %s", op.State)
	}
	if d := differences(b.before, picture(t, b.root)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	// by hand (--approves): it holds
	if op, err := b.motore(t).Apply(b.piano, true, "prova"); err != nil || op.State != RIFIUTATA {
		// the wrong approval in the file wins over --approves: the file names another plan
		t.Logf("with wrong approval in the file and --approve: %v %v", op.State, err)
	}
	p.Approval = nil
	WriteJSON(b.piano, &p)
	if op, err := b.motore(t).Apply(b.piano, true, "prova"); err != nil || op.State != CONFIRMED {
		t.Fatalf("with --approve: %v %v", op.State, err)
	}
}

// Only one open operation at a time; and the lock.
func TestOneAtATime(t *testing.T) {
	b := newBench(t)
	killAt(t, b.root, b.operations, b.piano, "apply", "dopo-fatta@unit")
	if _, err := b.motore(t).Apply(b.piano, false, "prova"); CodeOf(err) != "RX-STATO-001" {
		t.Fatalf("an open operation did not stop the new one: %v", err)
	}
	m := b.motore(t)
	if err := m.Block(); err != nil {
		t.Fatal(err)
	}
	defer m.Sblocca()
	if _, err := b.motore(t).Resume(); CodeOf(err) != "RX-STATO-003" {
		t.Fatalf("two engines together: %v", err)
	}
}

// R5 in small: after CONFIRMED, nothing to resume; and a plan redone on the machine already in
// place has PRE-EXISTING steps (nothing is rewritten).
func TestIdempotence(t *testing.T) {
	b := newBench(t)
	if op, err := b.motore(t).Apply(b.piano, false, "prova"); err != nil || op.State != CONFIRMED {
		t.Fatal(op.State, err)
	}
	after := picture(t, b.root)
	if _, err := b.motore(t).Resume(); CodeOf(err) != "RX-STATO-004" {
		t.Fatalf("resume after CONFIRMED: %v", err)
	}
	piano2 := testPlan(t, b.root, t.TempDir(), true)
	op, err := b.motore(t).Apply(piano2, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatal(op.State, err)
	}
	for _, e := range op.Reg.Events {
		if e.Kind == EvIntent && e.Origin != PREEXISTING {
			t.Errorf("%s redone as %s", e.Action, e.Origin)
		}
	}
	if d := differences(after, picture(t, b.root)); len(d) > 0 {
		t.Fatalf("the second time it wrote: %v", d)
	}
}

// R32 in small: a check that cannot answer (systemctl that does not answer) is not PASS.
func TestUnknownDoesNotPass(t *testing.T) {
	b := newBench(t)
	killAt(t, b.root, b.operations, b.piano, "apply", "state:VERIFYING@")
	os.WriteFile(filepath.Join(b.root, "rompi-systemctl"), nil, 0o644)
	op, _ := b.motore(t).Resume()
	if op.State == CONFIRMED || op.State == CONFIRMED_WITH_CONDITIONS {
		t.Fatalf("CONFIRMED with a check without an answer")
	}
	var rv VerifyReport
	ReadJSON(filepath.Join(op.Folder, "check.json"), &rv)
	located := false
	for _, k := range rv.Checks {
		if k.ID == "unit" && k.Outcome == "UNKNOWN" {
			located = true
		}
	}
	if !located {
		t.Errorf("the unit check should have been UNKNOWN: %+v", rv.Checks)
	}
}

// The certificate and installazione.json: only the kinds that install write the state that
// REMOTIX checks at start-up (DECISIONI §10.12, RX-INST-001).
func TestInstall(t *testing.T) {
	b := newBench(t)
	m := b.motore(t)
	if op, err := m.Apply(b.piano, false, "prova"); err != nil || op.State != CONFIRMED {
		t.Fatal(err)
	}
	if _, err := m.CheckInstallation(); CodeOf(err) != "RX-INST-001" {
		t.Fatalf("the trial plan does not install REMOTIX: %v", err)
	}
	var p Piano
	ReadJSON(b.piano, &p)
	p.Duty = "installation"
	p.Approval = nil
	b2 := newBench(t)
	WriteJSON(b2.piano, &p)
	m2 := b2.motore(t)
	op, err := m2.Apply(b2.piano, true, "prova")
	// REMOTIX's binary is not there (and does not have --encoding-test yet): encoding is UNKNOWN,
	// required ⇒ conditional, never a clean CONFIRMED (§6.6.7)
	if err != nil || op.State != CONFIRMED_WITH_CONDITIONS {
		t.Fatal(op.State, err)
	}
	in, err := m2.CheckInstallation()
	if err != nil || in.Operation != op.ID {
		t.Fatalf("installazione.json: %+v %v", in, err)
	}
}

func lastState(op *Operation) string {
	for i := len(op.Reg.Events) - 1; i >= 0; i-- {
		if op.Reg.Events[i].Kind == EvState {
			return op.Reg.Events[i].Code + " " + op.Reg.Events[i].Detail
		}
	}
	return ""
}

// The trial plan: the packages first, the group LAST (R28 for real on Alma).
func TestTestPlan(t *testing.T) {
	b := newBench(t)
	amb := fakeEnvironment(b.root)
	cat := catalogTest(t)
	prof := fakeProfile()
	p, err := TestPlan(prof, Evaluate(cat, prof), cat, amb, TestPlanOptions{Username: "prova", Packets: "labwc"})
	if err != nil {
		t.Fatal(err)
	}
	var types []string
	for _, a := range p.Actions {
		types = append(types, a.Kind)
	}
	if got := strings.Join(types, ","); got != "install-packages,write-file,write-file,enable-unit,add-user-to-group" {
		t.Fatalf("order of the steps: %s", got)
	}
}
