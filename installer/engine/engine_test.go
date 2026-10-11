package engine

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
		if !ValidTransition(trail[i], trail[i+1]) {
			t.Errorf("%s → %s should be valid", trail[i], trail[i+1])
		}
		for j := i + 2; j < len(trail); j++ {
			if ValidTransition(trail[i], trail[j]) {
				t.Errorf("%s → %s skips a state", trail[i], trail[j])
			}
		}
	}
	for _, s := range []State{CONFIRMED, CONFIRMED_WITH_CONDITIONS, ROLLED_BACK, PARTIALLY_ROLLED_BACK, REFUSED} {
		if !Finale(s) || len(transitions[s]) != 0 {
			t.Errorf("%s must be final and without exits", s)
		}
	}
	// from phases 0-5 one can only block (or refuse at consent), never cancel: nothing has been touched
	for _, s := range []State{NEW, TRUSTED, EXAMINED, EVALUATED, PLANNED, APPROVED, ACQUIRED} {
		if ValidTransition(s, ROLLING_BACK) || ValidTransition(s, ROLLED_BACK) {
			t.Errorf("%s → cancellation: before phase 6 there is nothing to cancel", s)
		}
		if !ValidTransition(s, BLOCKED) {
			t.Errorf("%s → BLOCKED must be valid", s)
		}
	}
	if ValidTransition(RUNNING, CONFIRMED) || ValidTransition(INTERRUPTED, APPLIED) || ValidTransition(ROLLING_BACK, CONFIRMED) {
		t.Error("a shortcut is valid")
	}
	if len(AllStates()) != 19 {
		t.Errorf("there are %d states, the design has 19", len(AllStates()))
	}
	// and the engine really refuses a transition outside the design
	b := newBench(t)
	op, _ := b.engine(t).Apply(b.piano, false, "prova")
	if err := op.navigate(RUNNING, "", ""); CodeOf(err) != "RX-STATO-002" {
		t.Errorf("CONFIRMED → RUNNING accepted: %v", err)
	}
}

// Every code used in the sources exists, and every code has the form RX-<AREA>-<NNN> (§6.6.9).
func TestCodes(t *testing.T) {
	shape := regexp.MustCompile(`^RX-[A-Z0-9]+-[0-9]{3}$`)
	for c, v := range Codes {
		if !shape.MatchString(c) || v.Testo == "" || v.Severity == "" || v.Nature == "" {
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
	afterChange := photo(t, b.root)
	op, err := b.engine(t).Apply(b.piano, false, "prova")
	if CodeOf(err) != "RX-PIANO-001" || op.State != BLOCKED {
		t.Fatalf("expected BLOCKED with RX-PIANO-001, got %v %v", op.State, err)
	}
	if !strings.Contains(err.Error(), "file:/etc/remotix-esistente.conf") {
		t.Errorf("the refusal does not say what changed: %v", err)
	}
	if d := differences(afterChange, photo(t, b.root)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	if ap, _ := b.engine(t).IsOpen(); ap != nil {
		t.Error("a BLOCKED must be final")
	}
	// also an element of the profile: a group of the card with one more member
	b2 := newBench(t)
	(&fakeGroups{b2.root}).Insert("root", "video")
	if _, err := b2.engine(t).Apply(b2.piano, false, "prova"); CodeOf(err) != "RX-PIANO-001" {
		t.Errorf("group changed: %v", err)
	}
}

// The consent: without it, REFUSED; with an approval of another plan, REFUSED; nothing touched.
func TestConsent(t *testing.T) {
	b := newBench(t)
	b.piano = testPlan(t, b.root, filepath.Dir(b.root), false)
	if op, _ := b.engine(t).Apply(b.piano, false, "prova"); op.State != REFUSED {
		t.Fatalf("without approval: %s", op.State)
	}
	var p Piano
	ReadJSON(b.piano, &p)
	p.Approval = &Approval{Da: "x", DigestPiano: "0000"}
	WriteJSON(b.piano, &p)
	if op, _ := b.engine(t).Apply(b.piano, false, "prova"); op.State != REFUSED {
		t.Fatalf("approval of another plan: %s", op.State)
	}
	if d := differences(b.before, photo(t, b.root)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	// by hand (--approva): it holds
	if op, err := b.engine(t).Apply(b.piano, true, "prova"); err != nil || op.State != REFUSED {
		// the wrong approval in the file wins over --approva: the file names another plan
		t.Logf("with wrong approval in the file and --approve: %v %v", op.State, err)
	}
	p.Approval = nil
	WriteJSON(b.piano, &p)
	if op, err := b.engine(t).Apply(b.piano, true, "prova"); err != nil || op.State != CONFIRMED {
		t.Fatalf("with --approve: %v %v", op.State, err)
	}
}

// Only one open operation at a time; and the lock.
func TestOneAtATime(t *testing.T) {
	b := newBench(t)
	killAt(t, b.root, b.operations, b.piano, "applica", "dopo-fatta@unit")
	if _, err := b.engine(t).Apply(b.piano, false, "prova"); CodeOf(err) != "RX-STATO-001" {
		t.Fatalf("an open operation did not stop the new one: %v", err)
	}
	m := b.engine(t)
	if err := m.Block(); err != nil {
		t.Fatal(err)
	}
	defer m.Unlock()
	if _, err := b.engine(t).Resume(); CodeOf(err) != "RX-STATO-003" {
		t.Fatalf("two engines together: %v", err)
	}
}

// R5 in small: after CONFIRMED, nothing to resume; and a plan redone on the machine already in
// place has PRE-EXISTING steps (nothing is rewritten).
func TestIdempotence(t *testing.T) {
	b := newBench(t)
	if op, err := b.engine(t).Apply(b.piano, false, "prova"); err != nil || op.State != CONFIRMED {
		t.Fatal(op.State, err)
	}
	after := photo(t, b.root)
	if _, err := b.engine(t).Resume(); CodeOf(err) != "RX-STATO-004" {
		t.Fatalf("resume after CONFIRMED: %v", err)
	}
	piano2 := testPlan(t, b.root, t.TempDir(), true)
	op, err := b.engine(t).Apply(piano2, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatal(op.State, err)
	}
	for _, e := range op.Reg.Events {
		if e.Type == EvIntent && e.Origine != PREEXISTING {
			t.Errorf("%s redone as %s", e.Action, e.Origine)
		}
	}
	if d := differences(after, photo(t, b.root)); len(d) > 0 {
		t.Fatalf("the second time it wrote: %v", d)
	}
}

// R32 in small: a check that cannot answer (systemctl that does not answer) is not PASS.
func TestUnknownDoesNotPass(t *testing.T) {
	b := newBench(t)
	killAt(t, b.root, b.operations, b.piano, "applica", "stato:VERIFYING@")
	os.WriteFile(filepath.Join(b.root, "rompi-systemctl"), nil, 0o644)
	op, _ := b.engine(t).Resume()
	if op.State == CONFIRMED || op.State == CONFIRMED_WITH_CONDITIONS {
		t.Fatalf("CONFIRMED with a check without an answer")
	}
	var rv VerifyReport
	ReadJSON(filepath.Join(op.Folder, "check.json"), &rv)
	found := false
	for _, k := range rv.Verifications {
		if k.ID == "unit" && k.Outcome == "UNKNOWN" {
			found = true
		}
	}
	if !found {
		t.Errorf("the unit check should have been UNKNOWN: %+v", rv.Verifications)
	}
}

// The certificate and installation.json: only the kinds that install write the state that
// REMOTIX checks at start-up (DECISIONI §10.12, RX-INST-001).
func TestInstall(t *testing.T) {
	b := newBench(t)
	m := b.engine(t)
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
	m2 := b2.engine(t)
	op, err := m2.Apply(b2.piano, true, "prova")
	// REMOTIX's binary is not there (and does not have --encoding-test yet): encoding is UNKNOWN,
	// required ⇒ conditional, never a clean CONFIRMED (§6.6.7)
	if err != nil || op.State != CONFIRMED_WITH_CONDITIONS {
		t.Fatal(op.State, err)
	}
	in, err := m2.CheckInstallation()
	if err != nil || in.Operation != op.ID {
		t.Fatalf("installation.json: %+v %v", in, err)
	}
}

func lastState(op *Operation) string {
	for i := len(op.Reg.Events) - 1; i >= 0; i-- {
		if op.Reg.Events[i].Type == EvState {
			return op.Reg.Events[i].Codice + " " + op.Reg.Events[i].Detail
		}
	}
	return ""
}

// The trial plan: the packages first, the group LAST (R28 for real on Alma).
func TestTestPlan(t *testing.T) {
	b := newBench(t)
	env := fakeEnvironment(b.root)
	cat := catalogTest(t)
	prof := fakeProfile()
	p, err := TestPlan(prof, Evaluate(cat, prof), cat, env, TestPlanOptions{User: "prova", Pacchetti: "labwc"})
	if err != nil {
		t.Fatal(err)
	}
	var types []string
	for _, a := range p.Azioni {
		types = append(types, a.Type)
	}
	if got := strings.Join(types, ","); got != "install-packages,write-file,write-file,enable-unit,add-user-to-group" {
		t.Fatalf("order of the steps: %s", got)
	}
}
