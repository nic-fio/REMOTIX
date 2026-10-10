package motore

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// Engine: an instance of the engine on the machine (or on a fake machine, in the tests).
type Engine struct {
	Amb     *Environment
	Folder  string        // /var/lib/remotix/operations (in tests, any root)
	Catalog *Catalog      // the one chosen and verified by phase 0 TRUST (Sources)
	Sources *TrustSources // where the catalogue comes from, and what it is verified with (fiducia.go)
	Port    int
	Examine func() *Profile // PREFLIGHT; nil ⇒ Preflight(Amb, …)
	Ev      *Events
	Clock   func() time.Time
	// Stopped: whoever installs has asked to stop (the «Cancel and put back as it was» button of TUI and
	// GUI). It is checked between one step and the next, never in the middle of a step: the step begun finishes,
	// then the operation goes to ROLLING_BACK (RX-AZIONE-006) and everything is undone from the log.
	Stopped func() bool
	lock    *os.File
}

// Operation: a folder in Folder/<id>/ with the state, the log and the objects.
type Operation struct {
	ID     string
	Folder string
	State  State
	Reg    *Log
	Piano  *Piano
	m      *Engine
}

// internal errors of the actions' loop
var (
	errFailed     = errors.New("an action failed")
	errConcurrent = errors.New("the machine changed during the operation")
	errStopped    = errors.New("stopped by whoever is installing")
)

func (m *Engine) clock() time.Time {
	if m.Clock != nil {
		return m.Clock()
	}
	return time.Now()
}

// Profile examines the machine (phase 1).
func (m *Engine) Profile() *Profile {
	if m.Examine != nil {
		return m.Examine()
	}
	return Preflight(m.Amb, PreflightOptions{Port: m.Port, Packets: m.Catalog.Components()})
}

// Components: the extra packages the catalogue wants to know whether they are there.
func (c *Catalog) Components() []string {
	seen_items := map[string]bool{}
	var r []string
	for _, p := range c.Platforms {
		for _, d := range p.Desktop {
			for _, x := range d.Components {
				if !seen_items[x] {
					seen_items[x] = true
					r = append(r, x)
				}
			}
		}
	}
	sort.Strings(r)
	return r
}

// Block takes the engine's lock: only one at a time. The kernel releases it by itself if the
// process dies (flock), so resume never finds an orphan lock.
func (m *Engine) Block() error {
	if err := os.MkdirAll(m.Folder, 0o700); err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(m.Folder, ".lock"), os.O_RDWR|os.O_CREATE, 0o600)
	if err != nil {
		return err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		f.Close()
		return Error("RX-STATO-003", "")
	}
	m.lock = f
	return nil
}

// Sblocca releases the lock.
func (m *Engine) Sblocca() {
	if m.lock != nil {
		m.lock.Close()
		m.lock = nil
	}
}

// List: the operations that exist, from the oldest.
func (m *Engine) List() ([]*Operation, error) {
	entries, err := os.ReadDir(m.Folder)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var r []*Operation
	for _, v := range entries {
		if !v.IsDir() {
			continue
		}
		op, err := m.open_it(v.Name())
		if err != nil {
			return nil, err
		}
		r = append(r, op)
	}
	return r, nil
}

func (m *Engine) open_it(id string) (*Operation, error) {
	op := &Operation{ID: id, Folder: filepath.Join(m.Folder, id), m: m}
	b, err := os.ReadFile(filepath.Join(op.Folder, "state"))
	if err != nil {
		return nil, err
	}
	op.State = State(strings.TrimSpace(string(b)))
	var p Piano
	if err := ReadJSON(filepath.Join(op.Folder, "plan.json"), &p); err == nil {
		op.Piano = &p
	}
	return op, nil
}

// Ended: in a state one never leaves.
func (op *Operation) Ended() (bool, error) { return Finale(op.State), nil }

func (op *Operation) openLog() error {
	if op.Reg != nil {
		return nil
	}
	r, warnings, err := OpenLog(filepath.Join(op.Folder, "log.jsonl"))
	if err != nil {
		return err
	}
	op.Reg = r
	// every program launched by the engine while the operation is open goes into the log (R41)
	if op.m.Amb != nil {
		op.m.Amb.Annotate = func(row string) { r.Record(Event{Kind: EvCommand, Detail: row}) }
		// and what the engine says while it waits for the package manager (occupato.go)
		op.m.Amb.Avvisa = func(m Message) {
			op.m.Ev.Message(op.ID, m)
			r.Record(Event{Kind: EvNote, Code: m.Code, Detail: m.Detail})
		}
	}
	for _, a := range warnings {
		op.m.Ev.Message(op.ID, a)
		if err := r.Record(Event{Kind: EvNote, Code: a.Code, Detail: a.Detail}); err != nil {
			return err
		}
	}
	return nil
}

// Open: the unfinished operation (at most one, by the rule of §6.6.2).
func (m *Engine) Open() (*Operation, error) {
	ops, err := m.List()
	if err != nil {
		return nil, err
	}
	var is_open *Operation
	for _, op := range ops {
		fin, err := op.Ended()
		if err != nil {
			return nil, err
		}
		if !fin {
			is_open = op
		}
	}
	return is_open, nil
}

// go_to: a transition, only if it is in the design. First the state file (atomic), then the log
// line, then the event.
func (op *Operation) go_to(a State, code_v, detail string) error {
	da := op.State
	if !Valid(da, a) {
		return Error("RX-STATO-002", string(da)+" → "+string(a))
	}
	if err := WriteAtomic(filepath.Join(op.Folder, "state"), []byte(string(a)+"\n"), 0o600); err != nil {
		return err
	}
	op.State = a
	if err := op.Reg.Record(Event{Kind: EvState, Da: da, A: a, Code: code_v, Detail: detail}); err != nil {
		return err
	}
	det := detail
	if code_v != "" {
		det = strings.TrimSpace(code_v + " " + detail)
	}
	op.m.Ev.State(op.ID, da, a, det)
	spot("state:"+string(a), "")
	return nil
}

// block brings the operation to BLOCKED with the error's code.
func (op *Operation) block(err error) error {
	code_v := CodeOf(err)
	det := err.Error()
	var e *ErrorRX
	if errors.As(err, &e) {
		op.m.Ev.Message(op.ID, e.M)
		det = e.M.Detail
	}
	if e2 := op.go_to(BLOCKED, code_v, det); e2 != nil {
		return e2
	}
	return err
}

func (op *Operation) writeObject(label_name string, v any) error {
	p := filepath.Join(op.Folder, label_name)
	if err := WriteJSON(p, v); err != nil {
		return err
	}
	op.m.Ev.Object(op.ID, strings.TrimSuffix(label_name, ".json"), p)
	return nil
}

// Apply: phases 0-8 of the plan (§6.0), on the plan's actions only. approveManually = the consent
// given now by whoever launches the command (--approves), which is recorded as such.
func (m *Engine) Apply(planPath string, approveManually bool, chi string) (*Operation, error) {
	if err := m.Block(); err != nil {
		return nil, err
	}
	defer m.Sblocca()
	if ap, err := m.Open(); err != nil {
		return nil, err
	} else if ap != nil {
		return nil, Error("RX-STATO-001", ap.ID+" is "+string(ap.State))
	}
	var piano Piano
	if err := ReadJSON(planPath, &piano); err != nil || piano.Object != "plan" {
		if err == nil {
			err = fmt.Errorf("not a plan: object %q", piano.Object)
		}
		return nil, Error("RX-PIANO-002", err.Error())
	}

	// NEW
	op := &Operation{ID: newID(), m: m, Piano: &piano}
	op.Folder = filepath.Join(m.Folder, op.ID)
	if err := os.Mkdir(op.Folder, 0o700); err != nil {
		return nil, err
	}
	if err := SyncFolder(m.Folder); err != nil {
		return nil, err
	}
	if err := WriteAtomic(filepath.Join(op.Folder, "state"), []byte(string(NEW)+"\n"), 0o600); err != nil {
		return nil, err
	}
	op.State = NEW
	if err := op.openLog(); err != nil {
		return nil, err
	}
	if err := op.Reg.Record(Event{Kind: EvState, A: NEW, Detail: "plan " + piano.ID}); err != nil {
		return nil, err
	}
	m.Ev.State(op.ID, "", NEW, T("ev.operazione", op.ID))
	if err := op.writeObject("plan.json", &piano); err != nil {
		return nil, err
	}

	// 0 TRUST
	if m.Sources == nil {
		return op, op.block(Error("RX-TRUST-004", "no catalogue source"))
	}
	cat, fid, err := m.Sources.Trusted(m.clock())
	if e := op.writeObject("trust.json", fid); e != nil {
		return op, e
	}
	for _, x := range fid.Messages {
		m.Ev.Message(op.ID, x)
	}
	if err != nil {
		return op, op.block(err)
	}
	m.Catalog = cat
	if err := op.go_to(TRUSTED, "", fmt.Sprintf("catalog %s (sequence %d): %s", cat.Version, cat.Sequence, fid.Source)); err != nil {
		return op, err
	}

	// 1 PREFLIGHT
	prof := m.Profile()
	if err := op.writeObject("profile.json", prof); err != nil {
		return op, err
	}
	if err := op.go_to(EXAMINED, "", ""); err != nil {
		return op, err
	}

	// 2 COMPATIBILITY
	rap := Evaluate(m.Catalog, prof)
	if err := op.writeObject("compatibility.json", rap); err != nil {
		return op, err
	}
	if err := op.go_to(EVALUATED, "", ""); err != nil {
		return op, err
	}

	// 3 PLANNING: does the plan hold on this machine? (fingerprint, R31)
	for _, ap := range piano.Actions {
		if _, err := NewAction(ap); err != nil {
			return op, op.block(err)
		}
	}
	im, err := ComputeFingerprint(prof, m.Catalog, piano.Actions, piano.Depends, &Context{Amb: m.Amb, Folder: op.Folder})
	if err != nil {
		return op, op.block(err)
	}
	if im.Digest != piano.Fingerprint.Digest {
		removed, added := FingerprintDifferences(piano.Fingerprint.Elements, im.Elements)
		det := "in the plan: " + strings.Join(removed, "; ") + " — now: " + strings.Join(added, "; ")
		if err := op.writeObject("fingerprint-now.json", im); err != nil {
			return op, err
		}
		return op, op.block(Error("RX-PIANO-001", det))
	}
	if err := op.go_to(PLANNED, "", "fingerprint "+im.Digest[:16]); err != nil {
		return op, err
	}

	// 4 CONSENT & SAFETY
	// what is missing (DECISIONI §10.36): the plan says it BLOCKING, and we stop before touching
	for _, x := range piano.NotDone {
		if x.Severity == BLOCKING {
			m.Ev.Message(op.ID, x)
			return op, op.go_to(BLOCKED, x.Code, x.Detail)
		}
	}
	appr := piano.Approval
	switch {
	case appr != nil && appr.DigestPiano != piano.Digest():
		m.Ev.Message(op.ID, Msg("RX-PIANO-005", ""))
		return op, op.go_to(RIFIUTATA, "RX-PIANO-005", "")
	case appr == nil && !approveManually:
		m.Ev.Message(op.ID, Msg("RX-PIANO-003", ""))
		return op, op.go_to(RIFIUTATA, "RX-PIANO-003", "")
	case appr == nil:
		appr = &Approval{Da: chi, TimeNow: now(), Manner: "by hand, --approve", DigestPiano: piano.Digest()}
	}
	if err := op.writeObject("approval.json", appr); err != nil {
		return op, err
	}
	if err := op.go_to(APPROVED, "", appr.Manner+", by "+appr.Da); err != nil {
		return op, err
	}

	// the steps the engine knows but cannot execute yet: we stop BEFORE touching
	if nf := UnimplementedSteps(&piano); len(nf) > 0 {
		return op, op.block(Error("RX-AZIONE-004", strings.Join(nf, "; ")))
	}

	// 5 ACQUISITION: the trial actions ask for no packages; the resolved set is empty but there.
	if err := op.writeObject("resolved-set.json", map[string]any{"format": Schema, "object": "resolved-set", "artifacts": []any{}}); err != nil {
		return op, err
	}
	if err := op.go_to(ACQUIRED, "", ""); err != nil {
		return op, err
	}

	// 6 INSTALLATION
	if err := op.go_to(RUNNING, "", ""); err != nil {
		return op, err
	}
	return op, op.go_on()
}

// Resume: an interrupted operation is completed (§6.0 point 6, table of §6.6.3).
func (m *Engine) Resume() (*Operation, error) {
	if err := m.Block(); err != nil {
		return nil, err
	}
	defer m.Sblocca()
	op, err := m.Open()
	if err != nil {
		return nil, err
	}
	if op == nil {
		return nil, Error("RX-STATO-004", "")
	}
	if err := op.openLog(); err != nil {
		return op, err
	}
	m.Ev.State(op.ID, op.State, op.State, T("ev.si_riprende"))
	switch op.State {
	case NEW, TRUSTED, EXAMINED, EVALUATED, PLANNED, APPROVED, ACQUIRED:
		m.Ev.Message(op.ID, Msg("RX-RIPRESA-002", string(op.State)))
		return op, op.go_to(BLOCKED, "RX-RIPRESA-002", "was "+string(op.State))
	case RUNNING:
		if err := op.go_to(INTERRUPTED, "", ""); err != nil {
			return op, err
		}
		fallthrough
	case INTERRUPTED:
		if err := op.go_to(RUNNING, "", "resume"); err != nil {
			return op, err
		}
	}
	return op, op.go_on()
}

// Rollback: the open operation is undone by walking the log backwards.
func (m *Engine) Rollback() (*Operation, error) {
	if err := m.Block(); err != nil {
		return nil, err
	}
	defer m.Sblocca()
	op, err := m.Open()
	if err != nil {
		return nil, err
	}
	if op == nil {
		return nil, Error("RX-STATO-004", "")
	}
	if err := op.openLog(); err != nil {
		return op, err
	}
	switch op.State {
	case NEW, TRUSTED, EXAMINED, EVALUATED, PLANNED, APPROVED, ACQUIRED:
		m.Ev.Message(op.ID, Msg("RX-RIPRESA-002", string(op.State)))
		return op, op.go_to(BLOCKED, "RX-RIPRESA-002", string(op.State))
	case RUNNING:
		if err := op.go_to(INTERRUPTED, "", ""); err != nil {
			return op, err
		}
		fallthrough
	case INTERRUPTED, APPLIED, VERIFYING, VERIFIED:
		if err := op.go_to(ROLLING_BACK, "", T("op.requested")); err != nil {
			return op, err
		}
	}
	return op, op.go_on()
}

// go_on brings the operation from its current state to a final state (or INTERRUPTED).
func (op *Operation) go_on() error {
	for {
		switch op.State {
		case RUNNING:
			err := op.runAll()
			switch {
			case errors.Is(err, errConcurrent):
				return op.go_to(INTERRUPTED, "RX-RIPRESA-001", op.lastDetail())
			case errors.Is(err, errStopped):
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-006", ""))
				if err := op.go_to(ROLLING_BACK, "RX-AZIONE-006", ""); err != nil {
					return err
				}
			case errors.Is(err, errFailed):
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-001", op.lastDetail()))
				if err := op.go_to(ROLLING_BACK, "RX-AZIONE-001", op.lastDetail()); err != nil {
					return err
				}
			case err != nil:
				return err
			default:
				if err := op.go_to(APPLIED, "", ""); err != nil {
					return err
				}
			}
		case APPLIED:
			if err := op.go_to(VERIFYING, "", ""); err != nil {
				return err
			}
		case VERIFYING:
			ok, err := op.verify()
			if err != nil {
				return err
			}
			if ok {
				if err := op.go_to(VERIFIED, "", ""); err != nil {
					return err
				}
			} else {
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-003", ""))
				if err := op.go_to(ROLLING_BACK, "RX-AZIONE-003", ""); err != nil {
					return err
				}
			}
		case VERIFIED:
			cond := op.conditions()
			fin := CONFIRMED
			if len(cond) > 0 {
				fin = CONFIRMED_WITH_CONDITIONS
			}
			// the certificate BEFORE the final state: if the process dies in between, resume
			// finds VERIFIED and rewrites it; the other way round there would be a final state without a certificate
			if err := op.certificate(fin, nil); err != nil {
				return err
			}
			if err := op.writeInstallation(fin); err != nil {
				return err
			}
			if op.Piano.Duty == "uninstallation" {
				if err := os.Remove(op.m.InstallPath()); err != nil && !os.IsNotExist(err) {
					return err
				}
			}
			if err := op.go_to(fin, "", ""); err != nil {
				return err
			}
			if op.Piano.Duty == "uninstallation" {
				return op.m.CleanHistory(op.Piano.Purge)
			}
			return nil
		case ROLLING_BACK:
			remainders, err := op.rollbackAll()
			if err != nil {
				return err
			}
			fin := ROLLED_BACK
			if len(remainders) > 0 {
				fin = PARTIALLY_ROLLED_BACK
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-002", strings.Join(remainders, "; ")))
			}
			if err := op.certificate(fin, remainders); err != nil {
				return err
			}
			return op.go_to(fin, "", "")
		default:
			return nil
		}
	}
}

func (op *Operation) lastDetail() string {
	for i := len(op.Reg.Events) - 1; i >= 0; i-- {
		e := op.Reg.Events[i]
		if e.Kind == EvFailed || (e.Kind == EvNote && e.Code == "RX-RIPRESA-001") {
			return strings.TrimSpace(e.Action + ": " + e.Detail)
		}
	}
	return ""
}

// context: rolling back an installation is always purge — the
// machine as it was; the uninstallation carries its «purge» in the parameters of the undo steps.
func (op *Operation) context(ap PlanAction) *Context {
	return &Context{Amb: op.m.Amb, Folder: op.Folder, P: ap, Purge: true}
}

func (op *Operation) failed(ap PlanAction, err error) error {
	code_v := CodeOf(err)
	if code_v == "" {
		code_v = "RX-AZIONE-001"
	}
	if e := op.Reg.Record(Event{Kind: EvFailed, Action: ap.ID, Code: code_v, Detail: err.Error()}); e != nil {
		return e
	}
	op.m.Ev.Action(op.ID, ap.ID, "FAILED", err.Error())
	return errFailed
}

func (op *Operation) concurrent(ap PlanAction, det string) error {
	if e := op.Reg.Record(Event{Kind: EvNote, Action: ap.ID, Code: "RX-RIPRESA-001", Detail: det}); e != nil {
		return e
	}
	op.m.Ev.Message(op.ID, Msg("RX-RIPRESA-001", ap.ID+": "+det))
	return errConcurrent
}

// mark_done: checks and records DONE.
func (op *Operation) mark_done(az Action, ap PlanAction, before json.RawMessage, remark string) error {
	outcome, det, err := az.Verify(op.context(ap), before)
	if err != nil {
		return op.failed(ap, err)
	}
	if outcome != COMPLETE {
		return op.failed(ap, Error("RX-AZIONE-003", string(outcome)+": "+det))
	}
	if err := op.Reg.Record(Event{Kind: EvDone, Action: ap.ID, After: jsonDi(map[string]string{"result": string(outcome), "detail": det}), Detail: remark}); err != nil {
		return err
	}
	op.m.Ev.Action(op.ID, ap.ID, "DONE", strings.TrimSpace(remark+" "+det))
	spot("dopo-fatta", ap.ID)
	return nil
}

// runAll: phase 6 with the write-ahead log, and the resume of the table of
// §6.6.3 (the same road: a new operation is a resume with an empty log).
func (op *Operation) runAll() error {
	for _, ap := range op.Piano.Actions {
		az, err := NewAction(ap)
		if err != nil {
			return op.failed(ap, err)
		}
		c := op.context(ap)
		prev := op.Reg.Last(ap.ID, EvIntent, EvDone, EvFailed)
		if prev == nil && op.m.Stopped != nil && op.m.Stopped() {
			return errStopped
		}
		switch {
		case prev == nil: // nothing in the log: not begun ⇒ do it
			spot("prima-intenzione", ap.ID)
			before, orig, err := az.Snapshot(c)
			if err != nil {
				return op.failed(ap, err)
			}
			if err := op.Reg.Record(Event{Kind: EvIntent, Action: ap.ID, Before: before, Origin: orig}); err != nil {
				return err
			}
			op.m.Ev.Action(op.ID, ap.ID, "INTENT", string(orig))
			spot("dopo-intenzione", ap.ID)
			if err := az.Do(c, before); err != nil {
				return op.failed(ap, err)
			}
			spot("dopo-effetto", ap.ID)
			if err := op.mark_done(az, ap, before, ""); err != nil {
				return err
			}

		case prev.Kind == EvIntent: // begun: maybe finished, maybe not, maybe half-done
			before := op.Reg.Intent(ap.ID).Before
			outcome, det, err := az.Verify(c, before)
			if err != nil {
				return op.failed(ap, err)
			}
			op.m.Ev.Action(op.ID, ap.ID, "RESUMED", string(outcome)+": "+det)
			switch outcome {
			case COMPLETE:
				if err := op.mark_done(az, ap, before, "resumed: the effect was already there"); err != nil {
					return err
				}
				continue
			case A_META:
				// the package manager's transaction: first ITS remedy (§6.6.3), then redo;
				// the other actions: undo what is there and redo
				if r, ok := az.(Repairable); ok {
					if err := r.Repair(c, before); err != nil {
						return op.failed(ap, err)
					}
				} else if err := az.Rollback(c, before); err != nil {
					return op.failed(ap, err)
				}
			case FOREIGN:
				return op.concurrent(ap, det)
			}
			if err := az.Do(c, before); err != nil {
				return op.failed(ap, err)
			}
			if err := op.mark_done(az, ap, before, "resumed: done again"); err != nil {
				return err
			}

		case prev.Kind == EvDone: // finished and recorded: move on, but the effect must still be there
			before := op.Reg.Intent(ap.ID).Before
			outcome, det, err := az.Verify(c, before)
			if err != nil {
				return op.failed(ap, err)
			}
			if outcome != COMPLETE {
				return op.concurrent(ap, "was DONE, now "+string(outcome)+": "+det)
			}

		case prev.Kind == EvFailed:
			return errFailed
		}
	}
	return nil
}

// rollbackAll walks the actions backwards. Returns what could not be undone.
func (op *Operation) rollbackAll() ([]string, error) {
	var remainders []string
	az := op.Piano.Actions
	for i := len(az) - 1; i >= 0; i-- {
		ap := az[i]
		intent := op.Reg.Intent(ap.ID)
		if intent == nil {
			continue // never begun: nothing to undo
		}
		if u := op.Reg.Last(ap.ID, EvIntentRollback, EvCancelled, EvRollbackFailed); u != nil && u.Kind == EvCancelled {
			continue
		}
		a, err := NewAction(ap)
		if err != nil {
			return nil, err
		}
		c := op.context(ap)
		put_out := func(t EventType, code_v, det string) error {
			op.m.Ev.Action(op.ID, ap.ID, string(t), det)
			return op.Reg.Record(Event{Kind: t, Action: ap.ID, Code: code_v, Detail: det})
		}
		if intent.Origin == PREEXISTING {
			if err := put_out(EvCancelled, "", "PREEXISTING: left untouched"); err != nil {
				return nil, err
			}
			continue
		}
		if ok, det, err := a.Cancelled(c, intent.Before); err == nil && ok {
			if err := put_out(EvCancelled, "", "nothing to undo: "+det); err != nil {
				return nil, err
			}
			continue
		}
		if outcome, det, err := a.Verify(c, intent.Before); err == nil && outcome == FOREIGN {
			remainders = append(remainders, ap.ID+": changed by someone else, left untouched ("+det+")")
			if err := put_out(EvRollbackFailed, "RX-RIPRESA-001", "CONCURRENT: "+det); err != nil {
				return nil, err
			}
			continue
		}
		if err := put_out(EvIntentRollback, "", ""); err != nil {
			return nil, err
		}
		spot("annulla-dopo-intenzione", ap.ID)
		errA := a.Rollback(c, intent.Before)
		spot("annulla-dopo-effetto", ap.ID)
		ok, det, errB := a.Cancelled(c, intent.Before)
		if errA == nil && errB == nil && ok {
			if err := put_out(EvCancelled, "", det); err != nil {
				return nil, err
			}
			continue
		}
		motivo := det
		if errA != nil {
			motivo = errA.Error()
		} else if errB != nil {
			motivo = errB.Error()
		}
		remainders = append(remainders, ap.ID+": "+motivo)
		if err := put_out(EvRollbackFailed, "RX-AZIONE-002", motivo); err != nil {
			return nil, err
		}
	}
	return remainders, nil
}

// Check: a line of the verification report (§6.6.7).
type Check struct {
	ID        string `json:"id"`
	What      string `json:"what"`
	Outcome   string `json:"result"` // PASS · FAIL · UNKNOWN · N.A.
	Requested bool   `json:"required"`
	Detail    string `json:"detail,omitempty"`
}

// VerifyReport: the sixth object.
type VerifyReport struct {
	Schema     string      `json:"format"`
	Object     string      `json:"object"`
	Created    string      `json:"created"`
	Checks     []Check     `json:"checks"`
	Conditions []Condition `json:"conditions,omitempty"` // those born from verification (a declared UNKNOWN)
}

// verify (phase 7, here reduced to the trial actions): every action rechecked. ⛔ UNKNOWN is not
// PASS: a required check that cannot answer leads to cancellation (the trial actions
// have no declared fallback).
func (op *Operation) verify() (bool, error) {
	rv := VerifyReport{Schema: Schema, Object: "check", Created: now()}
	overall := true
	for _, ap := range op.Piano.Actions {
		a, err := NewAction(ap)
		if err != nil {
			return false, err
		}
		k := Check{ID: ap.ID, What: ap.HowToVerify, Requested: true}
		intent := op.Reg.Intent(ap.ID)
		if intent == nil {
			k.Outcome, k.Detail = "UNKNOWN", "no intention in the log"
		} else if outcome, det, err := a.Verify(op.context(ap), intent.Before); err != nil {
			k.Outcome, k.Detail = "UNKNOWN", err.Error()
		} else if outcome == COMPLETE {
			k.Outcome, k.Detail = "PASS", det
		} else {
			k.Outcome, k.Detail = "FAIL", string(outcome)+": "+det
		}
		if k.Outcome != "PASS" {
			overall = false
		}
		rv.Checks = append(rv.Checks, k)
	}
	// 7a: H.264 encoding is tested by REMOTIX itself (§6.5-bis). Required: FAIL (no card that
	// encodes: phase 19, no fallback) ⇒ cancellation; UNKNOWN ⇒ CONFIRMED_WITH_CONDITIONS, never PASS
	// (§6.6.7).
	// and the PAM stack that resolves, and the port the firewall lets through (certifica.go, R29)
	if op.Piano.Duty == "installation" {
		port := op.m.Port
		for _, ap := range op.Piano.Actions {
			if ap.Kind == "start-service" {
				if n, err := strconv.Atoi(ap.Parameters["port"]); err == nil && n > 0 {
					port = n
				}
			}
		}
		if port == 0 {
			port = 7447
		}
		k, cond, has_failed := PlatformChecks(op.m.Amb, port)
		rv.Checks = append(rv.Checks, k...)
		rv.Conditions = append(rv.Conditions, cond...)
		if has_failed {
			overall = false
		}
	}
	return overall, op.writeObject("check.json", rv)
}

// encodingTest: `remotix --encoding-test` (§6.5-bis; phase 19, no fallback to the processor): one
// JSON line {"outcome":"hardware"|"nobody","encoder":…,"route":"vulkan"|"vaapi"|"","node":…,
// "motivo":…,"codec":…,"offered":…,"hevc":…,"h264":…,"hevc_strada":…,"h264_strada":…}; exit 0 if the card encoded the frame, 3 if NO
// card can encode (the encoder does not open: no node, no driver, driver without
// encoding — the declared refusal), 1 if the card opens but the frame does not come out, 2 usage
// error. The engine launches it as root (closed list). hardware ⇒ PASS; 3 or 1 ⇒ FAIL; a binary that
// does not know it or an unreadable answer ⇒ UNKNOWN (§6.6.7).
func encodingTest(a *Environment) (Check, *Condition) {
	k := Check{ID: "h264-encoding", What: "remotix --encoding-test (7a)", Requested: true}
	out, c, err := a.Run(2*time.Minute, "remotix", "--encoding-test")
	var r struct {
		Outcome, Encoder, Route, Node, Motivo, Codec string
	}
	read := false
	for _, row := range strings.Split(out, "\n") {
		if strings.HasPrefix(strings.TrimSpace(row), "{") && json.Unmarshal([]byte(row), &r) == nil && r.Outcome != "" {
			read = true
		}
	}
	// ⭐ phase 19: `route` says WHICH route of the card did the encoding (vulkan/vaapi); a binary
	// that does not write it (phase 18) passes all the same: the outcome is what counts
	det := strings.Join(strings.Fields(r.Outcome+" "+r.Codec+" "+r.Encoder+" "+r.Route+" "+r.Node+" "+r.Motivo), " ")
	switch {
	case err != nil:
		k.Outcome, k.Detail = "UNKNOWN", err.Error()
	case !read || c == 2:
		k.Outcome, k.Detail = "UNKNOWN", T("ver.codifica_assente")+": "+lastLines(out, 2)
	case c == 0 && r.Outcome == "hardware":
		k.Outcome, k.Detail = "PASS", det
	case c == 3:
		k.Outcome, k.Detail = "FAIL", T("ver.nessuna_scheda", notEmpty(r.Motivo, det))
	default:
		k.Outcome, k.Detail = "FAIL", det
	}
	if k.Outcome == "UNKNOWN" {
		return k, &Condition{Code: "C-LIMITE", Text: T("cond.codifica_ignota", k.Detail)}
	}
	return k, nil
}

func (op *Operation) conditions() []Condition {
	if op.Piano.Duty == "uninstallation" {
		return nil
	}
	var c []Condition
	var rv VerifyReport
	if ReadJSON(filepath.Join(op.Folder, "check.json"), &rv) == nil {
		c = append(c, rv.Conditions...)
	}
	var r Report
	if err := ReadJSON(filepath.Join(op.Folder, "compatibility.json"), &r); err != nil {
		return c
	}
	for _, e := range r.Desktop {
		if e.Level != NOT_SUPPORTED && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			c = append(c, e.Conditions...)
		}
	}
	return c
}

// Certificate: the seventh object (§6.6.11).
type Certificate struct {
	Schema         string      `json:"format"`
	Object         string      `json:"object"`
	Created        string      `json:"created"`
	Operation      string      `json:"operation"`
	State          State       `json:"state"`
	Duty           string      `json:"kind"`
	Product        string      `json:"product"`
	Engine         EngineRef   `json:"engine"`
	Catalog        CatalogRef  `json:"catalog"`
	Attestation    string      `json:"trust"`
	DigestPiano    string      `json:"digest_plan"`
	DigestTogether string      `json:"digest_resolved_set"`
	Fingerprint    string      `json:"fingerprint"`
	Checks         []Check     `json:"checks"`
	Conditions     []Condition `json:"conditions"`
	Remainders     []string    `json:"leftovers,omitempty"` // PARTIALLY_ROLLED_BACK: what remains, and why
	Indirect       []string    `json:"indirect"`            // INDIRECT changes declared (none, without packages)
}

func (op *Operation) certificate(fin State, remainders []string) error {
	var fid Attestation
	ReadJSON(filepath.Join(op.Folder, "trust.json"), &fid)
	var rv VerifyReport
	ReadJSON(filepath.Join(op.Folder, "check.json"), &rv)
	ins, _ := Sha256File(filepath.Join(op.Folder, "resolved-set.json"))
	attestation := T("cert.fiducia_no")
	if fid.Catalog.Digest != "" && len(fid.Messages) == 0 {
		attestation = fmt.Sprintf("%s (sequence %d)", fid.Source, fid.Sequence)
	}
	c := Certificate{Schema: Schema, Object: "certificate", Created: now(), Operation: op.ID, State: fin,
		Duty: op.Piano.Duty, Product: T("cert.prodotto_prova"),
		Engine: EngineRef{EngineVersion, EngineDigest()}, Catalog: fid.Catalog, Attestation: attestation,
		DigestPiano: op.Piano.Digest(), DigestTogether: ins, Fingerprint: op.Piano.Fingerprint.Digest,
		Checks: rv.Checks, Conditions: op.conditions(), Remainders: remainders, Indirect: op.indirect()}
	if c.Conditions == nil {
		c.Conditions = []Condition{}
	}
	if err := op.writeObject("certificate.json", c); err != nil {
		return err
	}
	var t strings.Builder
	fmt.Fprintf(&t, "%s\n\n%s: %s\n%s: %s\n%s: %s (%s)\n%s: %s (%s)\n%s: %s\n%s: %s\n%s: %s\n",
		T("cert.heading", op.ID), T("cert.state"), c.State, T("cert.duty"), c.Duty, T("cert.motore"), c.Engine.Version, c.Engine.Digest,
		T("cert.catalogo"), c.Catalog.Version, c.Catalog.Digest, T("cert.attestation"), c.Attestation, T("cert.piano"), c.DigestPiano, T("cert.fingerprint"), c.Fingerprint)
	fmt.Fprintf(&t, "\n%s:\n", T("cert.checks"))
	for _, k := range c.Checks {
		fmt.Fprintf(&t, "  %-8s %s — %s\n", k.Outcome, k.ID, k.Detail)
	}
	fmt.Fprintf(&t, "\n%s:\n", T("cert.conditions"))
	if len(c.Conditions) == 0 {
		fmt.Fprintf(&t, "  %s\n", T("cert.nessuna"))
	}
	for _, k := range c.Conditions {
		fmt.Fprintf(&t, "  %s %s\n", k.Code, k.Text)
	}
	if len(remainders) > 0 {
		fmt.Fprintf(&t, "\n%s:\n", T("cert.non_annullato"))
		for _, r := range remainders {
			fmt.Fprintf(&t, "  %s\n", r)
		}
	}
	return WriteAtomic(filepath.Join(op.Folder, "certificate.txt"), []byte(t.String()), 0o600)
}

// Installation: the state REMOTIX checks at start-up (DECISIONI §10.12: the installer is the
// only way; the service does not start without a CONFIRMED operation, RX-INST-001). It sits next to
// the operations folder: /var/lib/remotix/installazione.json.
type Installation struct {
	Schema      string `json:"format"`
	Object      string `json:"object"` // "installation"
	Operation   string `json:"operation"`
	State       State  `json:"state"`
	Duty        string `json:"kind"`
	Certificate string `json:"certificate"`
	Written     string `json:"written"`
}

// InstallPath: next to the operations folder.
func (m *Engine) InstallPath() string {
	return filepath.Join(filepath.Dir(m.Folder), "installation.json")
}

// writeInstallation: only for the kinds that really install the product. The trial plan
// of T4 does not write it: it did not install REMOTIX.
func (op *Operation) writeInstallation(fin State) error {
	if op.Piano.Duty != "installation" {
		return nil
	}
	return WriteJSON(op.m.InstallPath(), Installation{Schema: Schema, Object: "installation",
		Operation: op.ID, State: fin, Duty: op.Piano.Duty,
		Certificate: filepath.Join(op.Folder, "certificate.json"), Written: now()})
}

// CheckInstallation: what REMOTIX (and remotix-install updated) asks at start-up.
// It holds only if the file is there, the operation it names exists and is CONFIRMED (even conditionally).
func (m *Engine) CheckInstallation() (*Installation, error) {
	var in Installation
	if err := ReadJSON(m.InstallPath(), &in); err != nil {
		return nil, Error("RX-INST-001", err.Error())
	}
	op, err := m.open_it(in.Operation)
	if err != nil {
		return nil, Error("RX-INST-001", "operation "+in.Operation+" does not exist")
	}
	if op.State != CONFIRMED && op.State != CONFIRMED_WITH_CONDITIONS {
		return nil, Error("RX-INST-001", "operation "+in.Operation+" is "+string(op.State))
	}
	return &in, nil
}

// indirect: what happened indirectly and remains (§6.6.4): the actions declare it; and the
// packages held back by an undo step (RX-PACCHETTI-006), which says so in its DONE.
func (op *Operation) indirect() []string {
	r := []string{}
	for _, e := range op.Reg.Events {
		var d map[string]string
		if e.Kind == EvDone && json.Unmarshal(e.After, &d) == nil && strings.Contains(d["detail"], "[RX-PACCHETTI-006]") {
			_, x, _ := strings.Cut(d["detail"], "[RX-PACCHETTI-006] ")
			r = append(r, "RX-PACCHETTI-006 "+e.Action+": "+x)
		}
	}
	for _, ap := range op.Piano.Actions {
		intent := op.Reg.Intent(ap.ID)
		if intent == nil {
			continue
		}
		a, err := NewAction(ap)
		if err != nil {
			continue
		}
		if d, ok := a.(Declarer); ok {
			r = append(r, d.Indirect(intent.Before)...)
		}
	}
	return r
}
