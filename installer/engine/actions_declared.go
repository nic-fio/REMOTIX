package engine

import "encoding/json"

// The steps the engine KNOWS but cannot execute yet: they are in the plan (they are seen,
// approved, part of the fingerprint), but an operation containing one stops BEFORE touching
// the machine, with RX-AZIONE-004. Since the second part of T4 the steps of §10.12 are all real
// (packages, repositories, belts, service, desktop): the list is empty, the mechanism remains.

// notYetDoneWhy: type → what is missing to do it.
var notYetDoneWhy = map[string]string{}

func init() {
	for t := range notYetDoneWhy {
		registerType(t, func(p PlanAction) (Action, error) { return notYetDone{p.Type}, nil })
	}
}

type notYetDone struct{ kind string }

func (n notYetDone) err() error {
	return Error("RX-AZIONE-004", n.kind+": "+notYetDoneWhy[n.kind])
}

func (n notYetDone) Constraints(*Context) ([]string, error) { return nil, nil }
func (n notYetDone) Snapshot(*Context) (json.RawMessage, Origine, error) {
	return nil, "", n.err()
}
func (n notYetDone) Do(*Context, json.RawMessage) error { return n.err() }
func (n notYetDone) Check(*Context, json.RawMessage) (Outcome, string, error) {
	return "", "", n.err()
}
func (n notYetDone) Rollback(*Context, json.RawMessage) error { return n.err() }
func (n notYetDone) RolledBack(*Context, json.RawMessage) (bool, string, error) {
	return false, "", n.err()
}

// UnimplementedSteps: the plan's steps the engine cannot execute yet.
func UnimplementedSteps(p *Piano) []string {
	var r []string
	for _, a := range p.Azioni {
		if m, ok := notYetDoneWhy[a.Type]; ok {
			r = append(r, a.ID+" ("+a.Type+": "+m+")")
		}
	}
	return r
}
