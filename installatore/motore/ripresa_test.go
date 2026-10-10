package motore

// R30 in small: the engine process really KILLED (SIGKILL, no defer, no cleanup)
// at every point of the table of §6.6.3 and at every state transition; then a new engine
// resumes and must reach CONFIRMED (or ROLLED_BACK, if cancelling) with the machine IDENTICAL to
// that of a run without interruptions (or to the one before). The killed process is this same
// test binary, relaunched with REMOTIX_TEST_CHILD=1: the TestPoint hook exists only
// in the tests.

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

func TestMain(m *testing.M) {
	if os.Getenv("REMOTIX_TEST_CHILD") == "1" {
		child()
		return
	}
	os.Exit(m.Run())
}

// child: the engine that will be killed. It exits 3 if the point was never reached.
func child() {
	root, operations := os.Getenv("ROOT"), os.Getenv("OPERAZIONI")
	target := os.Getenv("PUNTO")
	TestPoint = func(p, a string) {
		if p+"@"+a == target {
			syscall.Kill(os.Getpid(), syscall.SIGKILL)
			select {}
		}
	}
	m := fakeEngine(&testing.T{}, root, operations)
	if os.Getenv("FIREWALL") != "" {
		os.WriteFile(filepath.Join(root, "etc/finto-firewall"), []byte(os.Getenv("FIREWALL")), 0o644)
	}
	var err error
	switch os.Getenv("CMD") {
	case "apply":
		_, err = m.Apply(os.Getenv("PIANO"), false, "prova")
	case "continue_it":
		_, err = m.Resume()
	case "rollback":
		_, err = m.Rollback()
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "child:", err)
	}
	os.Exit(3)
}

// killAt launches the child and checks it died of SIGKILL at the requested point.
func killAt(t *testing.T, root, operations, piano, command, spot string) {
	t.Helper()
	cmd := exec.Command(os.Args[0], "-test.run=^$")
	cmd.Env = append(os.Environ(), "REMOTIX_TEST_CHILD=1", "ROOT="+root, "OPERAZIONI="+operations,
		"PIANO="+piano, "CMD="+command, "PUNTO="+spot)
	var errOut bytes.Buffer
	cmd.Stderr = &errOut
	err := cmd.Run()
	var ee *exec.ExitError
	if !errors.As(err, &ee) {
		t.Fatalf("%s %s: the child did not die (err=%v) %s", command, spot, err, errOut.String())
	}
	if ws, ok := ee.Sys().(syscall.WaitStatus); !ok || !ws.Signaled() || ws.Signal() != syscall.SIGKILL {
		t.Fatalf("%s %s: the point was not reached (exit %v): %s", command, spot, err, errOut.String())
	}
}

type bench struct {
	root, operations, piano string
	before                  map[string]string
}

func newBench(t *testing.T) *bench {
	d := t.TempDir()
	b := &bench{root: filepath.Join(d, "host"), operations: filepath.Join(d, "operations")}
	os.MkdirAll(b.root, 0o755)
	prepareMachine(t, b.root)
	b.piano = testPlan(t, b.root, d, true)
	b.before = picture(t, b.root)
	return b
}

func (b *bench) motore(t *testing.T) *Engine { return fakeEngine(t, b.root, b.operations) }

// reference: the machine after a whole run without interruptions.
var reference map[string]string

func referencePhoto(t *testing.T) map[string]string {
	if reference != nil {
		return reference
	}
	b := newBench(t)
	op, err := b.motore(t).Apply(b.piano, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatalf("run without interruptions: %v, state %v", err, op.State)
	}
	reference = picture(t, b.root)
	return reference
}

// checkLog: no action DONE twice, no duplicate INTENTION (double effect).
func checkLog(t *testing.T, op *Operation) {
	t.Helper()
	if err := op.openLog(); err != nil {
		t.Fatal(err)
	}
	n := map[string]int{}
	for _, e := range op.Reg.Events {
		if e.Kind == EvDone || e.Kind == EvIntent {
			n[string(e.Kind)+" "+e.Action]++
		}
	}
	for k, v := range n {
		if v > 1 {
			t.Errorf("%s: %d times", k, v)
		}
	}
}

func pointsApply() []string {
	var pp []string
	for _, a := range testActions() {
		for _, p := range []string{"prima-intenzione", "dopo-intenzione", "dopo-effetto", "dopo-fatta"} {
			pp = append(pp, p+"@"+a.ID)
		}
		if a.Kind == "write-file" {
			pp = append(pp, "file-a-meta@"+a.ID)
		}
	}
	for _, s := range []State{RUNNING, APPLIED, VERIFYING, VERIFIED} {
		pp = append(pp, "state:"+string(s)+"@")
	}
	return pp
}

// ⭐ Killed during application, resumed: CONFIRMED, and the machine as after a clean run.
func TestResumeAfterInterruption(t *testing.T) {
	ref := referencePhoto(t)
	for _, spot := range pointsApply() {
		t.Run(spot, func(t *testing.T) {
			b := newBench(t)
			killAt(t, b.root, b.operations, b.piano, "apply", spot)
			op, err := b.motore(t).Resume()
			if err != nil {
				t.Fatalf("resume: %v", err)
			}
			if op.State != CONFIRMED {
				t.Fatalf("state %s, expected CONFIRMED", op.State)
			}
			if d := differences(ref, picture(t, b.root)); len(d) > 0 {
				t.Fatalf("the machine is not that of the clean run:\n%s", strings.Join(d, "\n"))
			}
			if _, err := os.Stat(filepath.Join(op.Folder, "certificate.json")); err != nil {
				t.Errorf("the certificate is missing: %v", err)
			}
			checkLog(t, op)
		})
	}
}

// ⭐ Killed during application, then cancelled: ROLLED_BACK, and the machine as it was before,
// byte by byte (the firewall rule and the member of «video» that were there stay).
func TestRollbackAfterInterruption(t *testing.T) {
	for _, spot := range pointsApply() {
		t.Run(spot, func(t *testing.T) {
			b := newBench(t)
			killAt(t, b.root, b.operations, b.piano, "apply", spot)
			op, err := b.motore(t).Rollback()
			if err != nil {
				t.Fatalf("cancel: %v", err)
			}
			if op.State != ROLLED_BACK {
				t.Fatalf("state %s, expected ROLLED_BACK", op.State)
			}
			if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
		})
	}
}

// ⭐ Killed DURING the rollback (R30, last point): resume finishes the cancellation.
func TestInterruptionDuringRollback(t *testing.T) {
	var points []string
	for _, a := range testActions() {
		points = append(points, "annulla-dopo-intenzione@"+a.ID, "annulla-dopo-effetto@"+a.ID)
	}
	points = append(points, "file-a-meta@overwritten-file", "state:INTERRUPTED@", "state:ROLLING_BACK@")
	for _, spot := range points {
		if spot == "annulla-dopo-intenzione@group-preexisting" || spot == "annulla-dopo-effetto@group-preexisting" {
			continue // PREEXISTING: it has no undo, the point is not reached (tested below)
		}
		t.Run(spot, func(t *testing.T) {
			b := newBench(t)
			// first an application killed halfway, so there is something to cancel
			killAt(t, b.root, b.operations, b.piano, "apply", "dopo-fatta@service")
			killAt(t, b.root, b.operations, b.piano, "rollback", spot)
			// resume: an ROLLING_BACK operation is resumed by cancelling; an INTERRUPTED one
			// is cancelled again
			m := b.motore(t)
			ap, _ := m.Open()
			var op *Operation
			var err error
			if ap.State == ROLLING_BACK {
				op, err = m.Resume()
			} else {
				op, err = m.Rollback()
			}
			if err != nil {
				t.Fatal(err)
			}
			if op.State != ROLLED_BACK {
				t.Fatalf("state %s, expected ROLLED_BACK", op.State)
			}
			if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
		})
	}
	t.Run("the PREEXISTING point is not reached", func(t *testing.T) {
		b := newBench(t)
		killAt(t, b.root, b.operations, b.piano, "apply", "dopo-fatta@service")
		cmd := exec.Command(os.Args[0], "-test.run=^$")
		cmd.Env = append(os.Environ(), "REMOTIX_TEST_CHILD=1", "ROOT="+b.root, "OPERAZIONI="+b.operations,
			"CMD=rollback", "PUNTO=annulla-dopo-intenzione@group-preexisting")
		err := cmd.Run()
		var ee *exec.ExitError
		if !errors.As(err, &ee) || ee.ExitCode() != 3 {
			t.Fatalf("expected: the child finishes without passing the point (exit 3), got %v", err)
		}
		if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
			t.Fatalf("%s", strings.Join(d, "\n"))
		}
	})
}

// Interrupted before touching the machine: resume says so and touches nothing.
func TestInterruptBeforeTouching(t *testing.T) {
	for _, s := range []State{TRUSTED, EXAMINED, EVALUATED, PLANNED, APPROVED, ACQUIRED} {
		t.Run(string(s), func(t *testing.T) {
			b := newBench(t)
			killAt(t, b.root, b.operations, b.piano, "apply", "state:"+string(s)+"@")
			op, err := b.motore(t).Resume()
			if err != nil || op.State != BLOCKED {
				t.Fatalf("state %v, err %v; expected BLOCKED (RX-RIPRESA-002)", op.State, err)
			}
			if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
				t.Fatalf("toccata: %s", strings.Join(d, "\n"))
			}
			// and it does not stay open: a new application starts
			if op2, err := b.motore(t).Apply(b.piano, false, "prova"); err != nil || op2.State != CONFIRMED {
				t.Fatalf("apply after: %v %v", op2, err)
			}
		})
	}
}

// A log line written halfway (process killed during the write): it is removed and resumed.
func TestTruncatedLine(t *testing.T) {
	b := newBench(t)
	killAt(t, b.root, b.operations, b.piano, "apply", "dopo-intenzione@unit")
	ap, _ := b.motore(t).Open()
	f, _ := os.OpenFile(filepath.Join(ap.Folder, "log.jsonl"), os.O_APPEND|os.O_WRONLY, 0)
	f.WriteString(`{"n":99,"type":"FAT`)
	f.Close()
	op, err := b.motore(t).Resume()
	if err != nil || op.State != CONFIRMED {
		t.Fatalf("%v %v", op.State, err)
	}
	found_at := false
	for _, e := range op.Reg.Events {
		if e.Code == "RX-RIPRESA-003" {
			found_at = true
		}
	}
	if !found_at {
		t.Error("the truncated line was not declared (RX-RIPRESA-003)")
	}
}

// DONE but the effect is gone (last line of the table): INTERRUPTED (RX-RIPRESA-001); then it is cancelled.
func TestConcurrentModification(t *testing.T) {
	t.Run("group removed by others", func(t *testing.T) {
		b := newBench(t)
		killAt(t, b.root, b.operations, b.piano, "apply", "dopo-fatta@group-video")
		(&fakeGroups{b.root}).Revoke("prova", "video")
		m := b.motore(t)
		op, err := m.Resume()
		if err != nil || op.State != INTERRUPTED {
			t.Fatalf("state %v err %v, expected INTERRUPTED (RX-RIPRESA-001)", op.State, err)
		}
		if ap, _ := m.Open(); ap == nil {
			t.Fatal("INTERRUPTED must stay open")
		}
		op, err = m.Rollback()
		if err != nil || op.State != ROLLED_BACK {
			t.Fatalf("cancel: %v %v", op.State, err)
		}
		if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
			t.Fatalf("%s", strings.Join(d, "\n"))
		}
	})
	t.Run("file changed by the administrator", func(t *testing.T) {
		b := newBench(t)
		killAt(t, b.root, b.operations, b.piano, "apply", "dopo-fatta@unit")
		conf := filepath.Join(b.root, "etc/remotix/engine-test.conf")
		os.WriteFile(conf, []byte("port=9999 # placed a mano\n"), 0o644)
		m := b.motore(t)
		if op, _ := m.Resume(); op.State != INTERRUPTED {
			t.Fatalf("state %v, expected INTERRUPTED", op.State)
		}
		op, err := m.Rollback()
		if err != nil || op.State != PARTIALLY_ROLLED_BACK {
			t.Fatalf("cancel: %v %v, expected PARTIALLY_ROLLED_BACK", op.State, err)
		}
		if c, _ := os.ReadFile(conf); string(c) != "port=9999 # placed a mano\n" {
			t.Fatalf("the administrator's file was touched: %q", c)
		}
	})
}

// R28 in small: a step that fails (here: nftables, which the engine cannot change yet; ufw
// can since T6) ⇒
// the operation is cancelled entirely, and the machine is as it was.
// failingPlan: the trial plan with a last step that cannot succeed (a person who does not
// exist, RX-GRUPPI-003): everything done before is cancelled.
func failingPlan(t *testing.T, b *bench) string {
	p := testPlan(t, b.root, filepath.Dir(b.root), false)
	var pn Piano
	ReadJSON(p, &pn)
	pn.Actions = append(pn.Actions, PlanGroup("ghost", "fantasma", "video"))
	im, err := ComputeFingerprint(fakeProfile(), catalogTest(t), pn.Actions, pn.Depends, &Context{Amb: fakeEnvironment(b.root)})
	if err != nil {
		t.Fatal(err)
	}
	pn.Fingerprint = *im
	pn.Approval = &Approval{Da: "prova", TimeNow: "2026-09-30T00:00:00Z", Manner: "da file", DigestPiano: pn.Digest()}
	WriteJSON(p, &pn)
	return p
}

func TestFailureRollsBackAll(t *testing.T) {
	b := newBench(t)
	b.piano = failingPlan(t, b)
	b.before = picture(t, b.root)
	op, err := b.motore(t).Apply(b.piano, false, "prova")
	if err != nil || op.State != ROLLED_BACK {
		t.Fatalf("state %v err %v, expected ROLLED_BACK", op.State, err)
	}
	if u := op.Reg.Last("ghost", EvFailed); u == nil || u.Code != "RX-GRUPPI-003" {
		t.Fatalf("the failure does not carry RX-GRUPPI-003: %+v", u)
	}
	if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
		t.Fatalf("%s", strings.Join(d, "\n"))
	}
	// and killed during that cancellation, then resumed
	for _, spot := range []string{"annulla-dopo-intenzione@unit", "annulla-dopo-effetto@overwritten-file", "state:ROLLING_BACK@"} {
		t.Run(spot, func(t *testing.T) {
			b := newBench(t)
			b.piano = failingPlan(t, b)
			b.before = picture(t, b.root)
			killAt(t, b.root, b.operations, b.piano, "apply", spot)
			op, err := b.motore(t).Resume()
			if err != nil || op.State != ROLLED_BACK {
				t.Fatalf("state %v err %v", op.State, err)
			}
			if d := differencesAfterUndo(t, b.before, picture(t, b.root)); len(d) > 0 {
				t.Fatalf("%s", strings.Join(d, "\n"))
			}
		})
	}
}
