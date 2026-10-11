package engine

import (
	"encoding/json"
	"sort"
)

// Reversibility: how far an action can be undone (§6.6.4).
type Reversibility string

const (
	EXACT          Reversibility = "EXACT"
	BEST_EFFORT    Reversibility = "BEST_EFFORT"
	NEEDS_SNAPSHOT Reversibility = "NEEDS_SNAPSHOT"
	IRREVERSIBLE   Reversibility = "IRREVERSIBLE"
)

// Origine of a change: decides how far rolling back is authorised (§6.6.4).
type Origine string

const (
	DIRECT      Origine = "DIRECT"
	INDIRECT    Origine = "INDIRECT"
	PREEXISTING Origine = "PREEXISTING"
	CONCURRENT  Origine = "CONCURRENT"
)

// Outcome of «check»: complete, absent, half-done (§6.6.3) — and a fourth case, which the
// check must be able to recognise so as not to cause damage: the effect belongs to someone else.
type Outcome string

const (
	COMPLETE Outcome = "COMPLETE"
	ABSENT   Outcome = "ABSENT"
	A_META   Outcome = "HALF_DONE"
	FOREIGN  Outcome = "FOREIGN" // neither our effect nor the before-state: a CONCURRENT change
)

// PlanAction: an action as it stands in the plan — what, how it is done, how it is verified, how it is
// undone. The undo is born with the step (§6.0 point 3).
type PlanAction struct {
	ID            string            `json:"id"`
	Type          string            `json:"type"`
	Parameters    map[string]string `json:"parameters"`
	Description   string            `json:"description"`
	ComeSiFa      string            `json:"how_done"`
	HowToVerify   string            `json:"how_verified"`
	HowToUndo     string            `json:"how_rolled_back"`
	Reversibility Reversibility     `json:"reversibility"`
	Consent       string            `json:"consent,omitempty"` // the question, if the action has one of its own (D5, D6, IRREVERSIBLE)
}

// Context of a running action: the machine and the operation's folder (for the backups).
type Context struct {
	Env    *Environment
	Folder string
	P      PlanAction
	// Purge: when undoing the packages the configuration is removed too. Rolling back
	// a failed installation is always purge (the machine as it was); uninstalling is purge only
	// if asked for (§6.5 point 3: remove keeps the configuration).
	Purge bool
}

// Repairable: an action that, found half-done, is repaired with its tool's remedy instead of
// undoing and redoing (the package manager's transaction, §6.6.3).
type Repairable interface {
	Repair(c *Context, before json.RawMessage) error
}

// Dichiarante: an action that leaves INDIRECT changes (§6.6.4) and declares them.
type Declarer interface {
	Indirect(before json.RawMessage) []string
}

// Action is the interface of §6.6.3-§6.6.4. Every method is idempotent: redoing it does not double
// the effect. «before» is the before-state, taken ONCE by Snapshot and written in the log
// with the INTENTION.
type Action interface {
	// Snapshot the before-state and says the origin (DIRECT, or PREEXISTING if the effect was already there).
	Snapshot(c *Context) (before json.RawMessage, origin Origine, err error)
	Do(c *Context, before json.RawMessage) error
	// Check changes nothing: complete, absent, half-done, or foreign.
	Check(c *Context, before json.RawMessage) (Outcome, string, error)
	// Rollback brings back to the before-state what is ours, and only that.
	Rollback(c *Context, before json.RawMessage) error
	// RolledBack: has the machine returned to the before-state (as far as the action is concerned)?
	RolledBack(c *Context, before json.RawMessage) (bool, string, error)
	// Constraints: the elements of the binding fingerprint that the action touches or depends on (§6.6.5).
	Constraints(c *Context) ([]string, error)
}

type builder func(p PlanAction) (Action, error)

var actionTypes = map[string]builder{}

func registerType(kind string, c builder) { actionTypes[kind] = c }

// NewAction builds the action of a plan step.
func NewAction(p PlanAction) (Action, error) {
	c, ok := actionTypes[p.Type]
	if !ok {
		return nil, Error("RX-PIANO-004", p.Type)
	}
	return c(p)
}

// ActionTypes: the types this engine knows.
func ActionTypes() []string {
	var r []string
	for t := range actionTypes {
		r = append(r, t)
	}
	sort.Strings(r)
	return r
}

// TestPoint is the hook of the interruption tests (R30 in small): the tests put in a
// function that kills the process at a precise point. ⛔ In the binary it is always nil: there is
// no way to switch it on from outside (no environment variables, no options) — R13.
var TestPoint func(spot, action string)

func spot(p, action string) {
	if TestPoint != nil {
		TestPoint(p, action)
	}
}

func jsonDi(v any) json.RawMessage { return json.RawMessage(CanonicalJSON(v)) }
