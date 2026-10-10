package motore

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// The UNINSTALLATION (§6.0, third kind; §6.5 point 3; R6): an operation like the others, with
// its plan, its consent, its log and its resume, which walks BACKWARDS through the
// log of the confirmed installation (installazione.json). Every step of then with origin
// DIRECT becomes an «undo» step: doing = its rollback, undoing = its make (if the
// uninstallation fails halfway, it goes back to the previous installation). PREEXISTING is never
// touched; the INDIRETTE are declared. Right after the service is switched off, the REMOTIX
// sessions still open are closed (chiudi-sessioni, §6.5-bis). On CONFIRMED uninstallation
// installazione.json is removed; the operations log stays (it is the machine's history,
// like dnf's).

func init() {
	registerType("undo", newUndo)
	registerType("remove-membership", newEnrollment)
}

// EnrollmentsFile: where REMOTIX records whom it enrolled in the groups at the first connection (figlio.c,
// §6.5-bis): origin DIRECT, the uninstallation removes them like those of the engine.
const EnrollmentsFile = "gruppi-iscritti.jsonl"

// Memberships: the (user, group) pairs of the file, without duplicates.
func (m *Engine) Memberships() [][2]string {
	b, err := os.ReadFile(filepath.Join(filepath.Dir(m.Folder), EnrollmentsFile))
	if err != nil {
		return nil
	}
	var r [][2]string
	seen_items := map[[2]string]bool{}
	for _, row := range strings.Split(string(b), "\n") {
		var x struct {
			Schema, Username, Grp, Origin string
		}
		if json.Unmarshal([]byte(row), &x) != nil || x.Schema != "remotix-gruppi/1" || x.Username == "" || x.Grp == "" {
			continue
		}
		k := [2]string{x.Username, x.Grp}
		if !seen_items[k] {
			seen_items[k] = true
			r = append(r, k)
		}
	}
	return r
}

// togli-iscrizione: the inverse of aggiungi-utente-a-gruppo, for the enrolments made by REMOTIX.
type enrollment struct{ g *grp }

func newEnrollment(p PlanAction) (Action, error) {
	return &enrollment{&grp{p.Parameters["user"], p.Parameters["group"]}}, nil
}

type beforeEnrollment struct {
	Origin Origin `json:"origin"`
}

func (i *enrollment) Constraints(c *Context) ([]string, error) { return i.g.Constraints(c) }
func (i *enrollment) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	esp, _, _, err := i.g.member(c)
	if err != nil {
		if CodeOf(err) == "RX-GRUPPI-003" || CodeOf(err) == "RX-GRUPPI-002" {
			return jsonDi(beforeEnrollment{PREEXISTING}), PREEXISTING, nil // the user or the group is gone
		}
		return nil, "", err
	}
	if !esp {
		return jsonDi(beforeEnrollment{PREEXISTING}), PREEXISTING, nil
	}
	return jsonDi(beforeEnrollment{DIRECT}), DIRECT, nil
}
func (i *enrollment) origin(before json.RawMessage) Origin {
	var p beforeEnrollment
	json.Unmarshal(before, &p)
	return p.Origin
}
func (i *enrollment) Do(c *Context, before json.RawMessage) error {
	if i.origin(before) == PREEXISTING {
		return nil
	}
	if esp, _, _, err := i.g.member(c); err != nil || !esp {
		return err
	}
	return c.Amb.Groups.Revoke(i.g.username, i.g.grp)
}
func (i *enrollment) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	if i.origin(before) == PREEXISTING {
		return COMPLETE, "nothing to remove", nil
	}
	esp, _, _, err := i.g.member(c)
	if err != nil {
		return "", "", err
	}
	if esp {
		return ABSENT, i.g.username + " is still in " + i.g.grp, nil
	}
	return COMPLETE, i.g.username + " is no longer in " + i.g.grp, nil
}
func (i *enrollment) Rollback(c *Context, before json.RawMessage) error {
	if i.origin(before) == PREEXISTING {
		return nil
	}
	if esp, _, _, err := i.g.member(c); err != nil || esp {
		return err
	}
	return c.Amb.Groups.Add(i.g.username, i.g.grp)
}
func (i *enrollment) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	if i.origin(before) == PREEXISTING {
		return true, "nothing to put back", nil
	}
	esp, _, _, err := i.g.member(c)
	return esp, "", err
}

// PlansFolder: the plans approved by whoever installs, next to the operations folder
// (/var/lib/remotix/plans): the command line and the TUI write them there.
const PlansFolder = "plans"

// CleanHistory, on CONFIRMED uninstallation (the coordinator's decision, 30 Sep): without purge the
// engine's history stays (for support) but without the cached packages; with purge it is removed
// entirely — the operations and the plans —, and /var/lib/remotix too if it remains empty.
func (m *Engine) CleanHistory(purge bool) error {
	if purge {
		for _, d := range []string{m.Folder, filepath.Join(filepath.Dir(m.Folder), PlansFolder)} {
			if err := os.RemoveAll(d); err != nil {
				return err
			}
		}
		os.Remove(filepath.Join(filepath.Dir(m.Folder), EnrollmentsFile)) // already undone by the plan
		// the recorded versions (aggiornato.go). ⚠ 10 Oct 2026, names in English (DECISIONI §10.35): removed the
		// cleanups of the files of the engines from before D11/D14 — no real installation ever wrote them
		os.Remove(filepath.Join(filepath.Dir(m.Folder), AnnotatedVersionsFile))
		os.Remove(filepath.Dir(m.Folder)) // only if empty
		return nil
	}
	entries, _ := filepath.Glob(filepath.Join(m.Folder, "*", "cache"))
	for _, v := range entries {
		if err := os.RemoveAll(v); err != nil {
			return err
		}
	}
	return nil
}

// ReadLog reads a log without opening it for writing.
func ReadLog(fpath string) ([]Event, error) {
	f, err := os.Open(fpath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var r []Event
	s := bufio.NewScanner(f)
	s.Buffer(make([]byte, 1<<20), 64<<20)
	for s.Scan() {
		var e Event
		if json.Unmarshal(s.Bytes(), &e) == nil {
			r = append(r, e)
		}
	}
	return r, s.Err()
}

type undo struct {
	op, action string
	purge      bool
}

func newUndo(p PlanAction) (Action, error) {
	return &undo{op: p.Parameters["operation"], action: p.Parameters["action"], purge: p.Parameters["purge"] == "yes"}, nil
}

type beforeUndo struct {
	Origin     Origin          `json:"origin"`
	BeforeOrig json.RawMessage `json:"original_before"`
}

// original: the action of then, its context (the operation folder of then, with the
// backups and the cache) and the before-state of then.
func (d *undo) original(c *Context) (Action, *Context, *Event, error) {
	dir := filepath.Join(filepath.Dir(c.Folder), d.op)
	var pn Piano
	if err := ReadJSON(filepath.Join(dir, "plan.json"), &pn); err != nil {
		return nil, nil, nil, err
	}
	var ap *PlanAction
	for i := range pn.Actions {
		if pn.Actions[i].ID == d.action {
			ap = &pn.Actions[i]
		}
	}
	if ap == nil {
		return nil, nil, nil, fmt.Errorf("undo: %s is not in the plan of %s", d.action, d.op)
	}
	ev, err := ReadLog(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, nil, nil, err
	}
	var intent *Event
	for i := range ev {
		if ev[i].Action == d.action && ev[i].Kind == EvIntent {
			intent = &ev[i]
			break
		}
	}
	a, err := NewAction(*ap)
	if err != nil {
		return nil, nil, nil, err
	}
	return a, &Context{Amb: c.Amb, Folder: dir, P: *ap, Purge: d.purge}, intent, nil
}

func (d *undo) Constraints(c *Context) ([]string, error) {
	a, cc, _, err := d.original(c)
	if err != nil {
		return nil, err
	}
	return a.Constraints(cc)
}

func (d *undo) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	_, _, intent, err := d.original(c)
	if err != nil {
		return nil, "", err
	}
	if intent == nil || intent.Origin == PREEXISTING {
		return jsonDi(beforeUndo{Origin: PREEXISTING}), PREEXISTING, nil
	}
	return jsonDi(beforeUndo{Origin: DIRECT, BeforeOrig: intent.Before}), DIRECT, nil
}

func (d *undo) read_it(c *Context, before json.RawMessage) (Action, *Context, beforeUndo, error) {
	var p beforeUndo
	if err := json.Unmarshal(before, &p); err != nil {
		return nil, nil, p, err
	}
	a, cc, _, err := d.original(c)
	return a, cc, p, err
}

func (d *undo) Do(c *Context, before json.RawMessage) error {
	a, cc, p, err := d.read_it(c, before)
	if err != nil || p.Origin == PREEXISTING {
		return err
	}
	return a.Rollback(cc, p.BeforeOrig)
}

func (d *undo) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	a, cc, p, err := d.read_it(c, before)
	if err != nil {
		return "", "", err
	}
	if p.Origin == PREEXISTING {
		return COMPLETE, "nothing to undo", nil
	}
	if ok, det, err := a.Cancelled(cc, p.BeforeOrig); err != nil {
		return "", "", err
	} else if ok {
		return COMPLETE, "undone: " + det, nil
	}
	e, det, err := a.Verify(cc, p.BeforeOrig)
	if err != nil {
		return "", "", err
	}
	switch e {
	case COMPLETE:
		return ABSENT, "still as the installation left it", nil
	case FOREIGN:
		return FOREIGN, det, nil
	}
	return A_META, det, nil
}

func (d *undo) Repair(c *Context, before json.RawMessage) error {
	a, cc, p, err := d.read_it(c, before)
	if err != nil {
		return err
	}
	if r, ok := a.(Repairable); ok {
		return r.Repair(cc, p.BeforeOrig)
	}
	return nil
}

// Rollback (an uninstallation that fails halfway): what was there is redone.
func (d *undo) Rollback(c *Context, before json.RawMessage) error {
	a, cc, p, err := d.read_it(c, before)
	if err != nil || p.Origin == PREEXISTING {
		return err
	}
	return a.Do(cc, p.BeforeOrig)
}

func (d *undo) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	a, cc, p, err := d.read_it(c, before)
	if err != nil {
		return false, "", err
	}
	if p.Origin == PREEXISTING {
		return true, "nothing to redo", nil
	}
	e, det, err := a.Verify(cc, p.BeforeOrig)
	return e == COMPLETE, det, err
}

func (d *undo) Indirect(before json.RawMessage) []string {
	var p beforeUndo
	if json.Unmarshal(before, &p) != nil || p.Origin == PREEXISTING {
		return nil
	}
	return nil // the installation's indirect changes stay declared in its certificate, taken up below
}

// UninstallPlan builds the plan from the log of the confirmed installation.
func (m *Engine) UninstallPlan(prof *Profile, purge bool) (*Piano, error) {
	in, err := m.CheckInstallation()
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(m.Folder, in.Operation)
	var orig Piano
	if err := ReadJSON(filepath.Join(dir, "plan.json"), &orig); err != nil {
		return nil, err
	}
	ev, err := ReadLog(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, err
	}
	origin := map[string]Origin{}
	for _, e := range ev {
		if e.Kind == EvIntent {
			if _, ok := origin[e.Action]; !ok {
				origin[e.Action] = e.Origin
			}
		}
	}
	pn := &Piano{Schema: Schema, Object: "plan", ID: newID(), Created: now(), Duty: "uninstallation", Purge: purge,
		Engine: EngineRef{EngineVersion, EngineDigest()}, Catalog: CatalogRef{m.Catalog.Version, m.Catalog.Digest},
		Platform: orig.Platform, Depends: []string{}, Consents: []string{}, Conditions: []Condition{}, NotDone: []Message{}}
	sess, _ := RemotixSessions(m.Amb)
	var users []string
	seen_items := map[string]bool{}
	for _, s := range sess {
		if !seen_items[s.Username] {
			seen_items[s.Username] = true
			users = append(users, s.Username)
		}
	}
	shut := PlanCloseSessions("close-sessions", len(sess), users)
	placed := false
	purgeS := map[bool]string{true: "yes", false: "no"}[purge]
	for i := len(orig.Actions) - 1; i >= 0; i-- {
		a := orig.Actions[i]
		o, mark_done := origin[a.ID]
		if !mark_done || o == PREEXISTING {
			continue
		}
		pn.Actions = append(pn.Actions, PlanAction{ID: "undo-" + a.ID, Kind: "undo",
			Parameters:    map[string]string{"operation": in.Operation, "action": a.ID, "purge": purgeS},
			Description:   T("az.undo", a.Description),
			ComeSiFa:      a.HowToUndo,
			HowToVerify:   T("az.undo.verify"),
			HowToUndo:     a.ComeSiFa,
			Reversibility: a.Reversibility})
		if a.Kind == "start-service" && !placed {
			pn.Actions = append(pn.Actions, shut)
			placed = true
		}
	}
	if !placed {
		pn.Actions = append([]PlanAction{shut}, pn.Actions...)
	}
	// the group enrolments made by REMOTIX at the first connection (DIRETTE), except those
	// the engine itself already has in one of its steps
	already := map[[2]string]bool{}
	for _, a := range orig.Actions {
		if a.Kind == "add-user-to-group" {
			already[[2]string{a.Parameters["user"], a.Parameters["group"]}] = true
		}
	}
	for _, k := range m.Memberships() {
		if already[k] {
			continue
		}
		pn.Actions = append(pn.Actions, PlanAction{ID: "membership-" + k[0] + "-" + k[1], Kind: "remove-membership",
			Parameters: map[string]string{"user": k[0], "group": k[1]}, Description: T("az.enrollment", k[0], k[1]),
			ComeSiFa: T("az.enrollment.fa"), HowToVerify: T("az.enrollment.verify"), HowToUndo: T("az.enrollment.rollback"),
			Reversibility: EXACT})
	}
	// the session logs in the homes (the user's decision, 1 Oct 2026): always, last,
	// with sessions closed; the current paths are declared
	logs := UserLogs(m.Amb)
	pn.Actions = append(pn.Actions, PlanRemoveLogs("user-logs", logs))
	listing := T("az.logs.nobody")
	if len(logs) > 0 {
		listing = strings.Join(logs, ", ")
	}
	pn.Declared = append(pn.Declared, T("az.logs.declared", listing))
	im, err := ComputeFingerprint(prof, m.Catalog, pn.Actions, pn.Depends, &Context{Amb: m.Amb, Folder: filepath.Join(m.Folder, "plan-in-progress")})
	if err != nil {
		return nil, err
	}
	pn.Fingerprint = *im
	return pn, nil
}
