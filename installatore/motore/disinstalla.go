package engine

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
// log of the confirmed installation (installation.json). Every step of then with origin
// DIRECT becomes an «undo» step: doing = its rollback, undoing = its run_traced (if the
// uninstallation fails halfway, it goes back to the previous installation). PREEXISTING is never
// touched; the INDIRETTE are declared. Right after the service is switched off, the REMOTIX
// sessions still open are closed (chiudi-sessioni, §6.5-bis). On CONFIRMED uninstallation
// installation.json is removed; the operations log stays (it is the machine's history,
// like dnf's).

func init() {
	registerType("undo", newUndo)
	registerType("remove-membership", newMembership)
}

// EnrollmentsFile: where REMOTIX records whom it enrolled in the groups at the first connection (figlio.c,
// §6.5-bis): origin DIRECT, the uninstallation removes them like those of the engine.
const EnrollmentsFile = "group-enrollments.jsonl"

// Iscrizioni: the (user, group) pairs of the file, without duplicates.
func (m *Engine) Memberships() [][2]string {
	b, err := os.ReadFile(filepath.Join(filepath.Dir(m.Folder), EnrollmentsFile))
	if err != nil {
		return nil
	}
	var r [][2]string
	seen_items := map[[2]string]bool{}
	for _, line := range strings.Split(string(b), "\n") {
		var x struct {
			Format, User, Group, Origin string
		}
		if json.Unmarshal([]byte(line), &x) != nil || x.Format != "remotix-enrollments/1" || x.User == "" || x.Group == "" {
			continue
		}
		k := [2]string{x.User, x.Group}
		if !seen_items[k] {
			seen_items[k] = true
			r = append(r, k)
		}
	}
	return r
}

// togli-iscrizione: the inverse of aggiungi-utente-a-gruppo, for the enrolments made by REMOTIX.
type enrollment struct{ g *group }

func newMembership(p PlanAction) (Action, error) {
	return &enrollment{&group{p.Parameters["user"], p.Parameters["group"]}}, nil
}

type beforeMembership struct {
	Origine Origine `json:"origin"`
}

func (i *enrollment) Constraints(c *Context) ([]string, error) { return i.g.Constraints(c) }
func (i *enrollment) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	esp, _, _, err := i.g.member(c)
	if err != nil {
		if CodeOf(err) == "RX-GRUPPI-003" || CodeOf(err) == "RX-GRUPPI-002" {
			return jsonDi(beforeMembership{PREEXISTING}), PREEXISTING, nil // the user or the group is gone
		}
		return nil, "", err
	}
	if !esp {
		return jsonDi(beforeMembership{PREEXISTING}), PREEXISTING, nil
	}
	return jsonDi(beforeMembership{DIRECT}), DIRECT, nil
}
func (i *enrollment) origin(before json.RawMessage) Origine {
	var p beforeMembership
	json.Unmarshal(before, &p)
	return p.Origine
}
func (i *enrollment) Do(c *Context, before json.RawMessage) error {
	if i.origin(before) == PREEXISTING {
		return nil
	}
	if esp, _, _, err := i.g.member(c); err != nil || !esp {
		return err
	}
	return c.Env.Gruppi.Remove(i.g.user, i.g.group)
}
func (i *enrollment) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	if i.origin(before) == PREEXISTING {
		return COMPLETE, "nothing to remove", nil
	}
	esp, _, _, err := i.g.member(c)
	if err != nil {
		return "", "", err
	}
	if esp {
		return ABSENT, i.g.user + " is still in " + i.g.group, nil
	}
	return COMPLETE, i.g.user + " is no longer in " + i.g.group, nil
}
func (i *enrollment) Rollback(c *Context, before json.RawMessage) error {
	if i.origin(before) == PREEXISTING {
		return nil
	}
	if esp, _, _, err := i.g.member(c); err != nil || esp {
		return err
	}
	return c.Env.Gruppi.Insert(i.g.user, i.g.group)
}
func (i *enrollment) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
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
	Origine    Origine         `json:"origin"`
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
	for i := range pn.Azioni {
		if pn.Azioni[i].ID == d.action {
			ap = &pn.Azioni[i]
		}
	}
	if ap == nil {
		return nil, nil, nil, fmt.Errorf("disfa: %s is not in the plan of %s", d.action, d.op)
	}
	ev, err := ReadLog(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, nil, nil, err
	}
	var intent *Event
	for i := range ev {
		if ev[i].Action == d.action && ev[i].Type == EvIntent {
			intent = &ev[i]
			break
		}
	}
	a, err := NewAction(*ap)
	if err != nil {
		return nil, nil, nil, err
	}
	return a, &Context{Env: c.Env, Folder: dir, P: *ap, Purge: d.purge}, intent, nil
}

func (d *undo) Constraints(c *Context) ([]string, error) {
	a, cc, _, err := d.original(c)
	if err != nil {
		return nil, err
	}
	return a.Constraints(cc)
}

func (d *undo) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	_, _, intent, err := d.original(c)
	if err != nil {
		return nil, "", err
	}
	if intent == nil || intent.Origine == PREEXISTING {
		return jsonDi(beforeUndo{Origine: PREEXISTING}), PREEXISTING, nil
	}
	return jsonDi(beforeUndo{Origine: DIRECT, BeforeOrig: intent.Before}), DIRECT, nil
}

func (d *undo) load(c *Context, before json.RawMessage) (Action, *Context, beforeUndo, error) {
	var p beforeUndo
	if err := json.Unmarshal(before, &p); err != nil {
		return nil, nil, p, err
	}
	a, cc, _, err := d.original(c)
	return a, cc, p, err
}

func (d *undo) Do(c *Context, before json.RawMessage) error {
	a, cc, p, err := d.load(c, before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	return a.Rollback(cc, p.BeforeOrig)
}

func (d *undo) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	a, cc, p, err := d.load(c, before)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREEXISTING {
		return COMPLETE, "nothing to undo", nil
	}
	if ok, det, err := a.RolledBack(cc, p.BeforeOrig); err != nil {
		return "", "", err
	} else if ok {
		return COMPLETE, "undone: " + det, nil
	}
	e, det, err := a.Check(cc, p.BeforeOrig)
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
	a, cc, p, err := d.load(c, before)
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
	a, cc, p, err := d.load(c, before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	return a.Do(cc, p.BeforeOrig)
}

func (d *undo) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
	a, cc, p, err := d.load(c, before)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREEXISTING {
		return true, "nothing to redo", nil
	}
	e, det, err := a.Check(cc, p.BeforeOrig)
	return e == COMPLETE, det, err
}

func (d *undo) Indirect(before json.RawMessage) []string {
	var p beforeUndo
	if json.Unmarshal(before, &p) != nil || p.Origine == PREEXISTING {
		return nil
	}
	return nil // the installation's indirect changes stay declared in its certificate, taken up below
}

// UninstallPlan builds the plan from the log of the confirmed installation.
func (m *Engine) UninstallPlan(prof *ProfileV, purge bool) (*Piano, error) {
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
	origin := map[string]Origine{}
	for _, e := range ev {
		if e.Type == EvIntent {
			if _, ok := origin[e.Action]; !ok {
				origin[e.Action] = e.Origine
			}
		}
	}
	pn := &Piano{Schema: Schema, Obj: "plan", ID: newID(), Made: now(), Duty: "uninstallation", Purge: purge,
		Engine: EngineRef{EngineVersion, EngineDigest()}, Catalog: CatalogRef{m.Catalog.Ver, m.Catalog.Digest},
		PlatformV: orig.PlatformV, Depends: []string{}, Consents: []string{}, Condizioni: []Condition{}, NotDone: []Message{}}
	sess, _ := RemotixSessions(m.Env)
	var users []string
	seen_items := map[string]bool{}
	for _, s := range sess {
		if !seen_items[s.User] {
			seen_items[s.User] = true
			users = append(users, s.User)
		}
	}
	closeStep := PlanCloseSessions("close-sessions", len(sess), users)
	placed := false
	purgeS := map[bool]string{true: "yes", false: "no"}[purge]
	for i := len(orig.Azioni) - 1; i >= 0; i-- {
		a := orig.Azioni[i]
		o, mark_done := origin[a.ID]
		if !mark_done || o == PREEXISTING {
			continue
		}
		pn.Azioni = append(pn.Azioni, PlanAction{ID: "undo-" + a.ID, Type: "undo",
			Parameters:    map[string]string{"operation": in.Operation, "action": a.ID, "purge": purgeS},
			Description:   T("az.disfa", a.Description),
			ComeSiFa:      a.HowToUndo,
			HowToVerify:   T("az.disfa.verifica"),
			HowToUndo:     a.ComeSiFa,
			Reversibility: a.Reversibility})
		if a.Type == "start-service" && !placed {
			pn.Azioni = append(pn.Azioni, closeStep)
			placed = true
		}
	}
	if !placed {
		pn.Azioni = append([]PlanAction{closeStep}, pn.Azioni...)
	}
	// the group enrolments made by REMOTIX at the first connection (DIRETTE), except those
	// the engine itself already has in one of its steps
	already := map[[2]string]bool{}
	for _, a := range orig.Azioni {
		if a.Type == "add-user-to-group" {
			already[[2]string{a.Parameters["user"], a.Parameters["group"]}] = true
		}
	}
	for _, k := range m.Memberships() {
		if already[k] {
			continue
		}
		pn.Azioni = append(pn.Azioni, PlanAction{ID: "membership-" + k[0] + "-" + k[1], Type: "remove-membership",
			Parameters: map[string]string{"user": k[0], "group": k[1]}, Description: T("az.iscrizione", k[0], k[1]),
			ComeSiFa: T("az.iscrizione.fa"), HowToVerify: T("az.iscrizione.verifica"), HowToUndo: T("az.iscrizione.annulla"),
			Reversibility: EXACT})
	}
	// the session logs in the homes (the user's decision, 1 Oct 2026): always, last,
	// with sessions closed; the current paths are declared
	logs := UserLogs(m.Env)
	pn.Azioni = append(pn.Azioni, PlanRemoveLogs("user-logs", logs))
	listing := T("az.registri.nessuno")
	if len(logs) > 0 {
		listing = strings.Join(logs, ", ")
	}
	pn.Declared = append(pn.Declared, T("az.registri.dichiarata", listing))
	im, err := ComputeFingerprint(prof, m.Catalog, pn.Azioni, pn.Depends, &Context{Env: m.Env, Folder: filepath.Join(m.Folder, "plan-in-progress")})
	if err != nil {
		return nil, err
	}
	pn.Fingerprint = *im
	return pn, nil
}
