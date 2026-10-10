package motore

import "encoding/json"

// abilita-unita: an enabled systemd unit (§6.6.3), over systemd's D-Bus (EnableUnitFiles and
// GetUnitFileState: what systemctl enable and is-enabled do, without launching them, §10.14). EXACT reversibility; a unit already enabled is PRE-EXISTING and stays
// enabled; a masked unit is not touched (the administrator turned it off on purpose).
//
// parameters: unit; start ("yes": also started at once; cancelling stops and disables it). ⚠ No
// new plan uses it any more (it was the updates timer, removed with D14, DECISIONI §10.23): it stays
// so that uninstalling an installation made earlier knows how to stop what it had started.

func init() { registerType("enable-unit", newUnit) }

// PlanUnit prepares the plan's step.
func PlanUnit(id, unit string) PlanAction {
	return PlanAction{
		ID: id, Kind: "enable-unit",
		Parameters:    map[string]string{"unit": unit},
		Description:   T("az.unit", unit),
		ComeSiFa:      T("az.unit.fa", unit),
		HowToVerify:   T("az.unit.verify", unit),
		HowToUndo:     T("az.unit.rollback", unit),
		Reversibility: EXACT,
	}
}

type unit struct {
	label_name string
	start      bool
}

type beforeUnit struct {
	Origin Origin `json:"origin"`
	State  string `json:"state"` // what is-enabled said
}

func newUnit(p PlanAction) (Action, error) {
	return &unit{p.Parameters["unit"], p.Parameters["start"] == "yes"}, nil
}

func (u *unit) live(c *Context) bool {
	a, err := c.Amb.Unit.Active(u.label_name)
	return err == nil && a == "active"
}

func (u *unit) Constraints(c *Context) ([]string, error) {
	s, err := c.Amb.Unit.State(u.label_name)
	if err != nil {
		return nil, err
	}
	return []string{"unit:" + u.label_name + "=" + s}, nil
}

func (u *unit) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	s, err := c.Amb.Unit.State(u.label_name)
	if err != nil {
		return nil, "", err
	}
	switch s {
	case "masked", "masked-runtime":
		return nil, "", Error("RX-SYSTEMD-002", u.label_name)
	case "not-found":
		return nil, "", Error("RX-SYSTEMD-003", u.label_name)
	}
	p := beforeUnit{Origin: DIRECT, State: s}
	if s == "enabled" {
		p.Origin = PREEXISTING
	}
	return jsonDi(p), p.Origin, nil
}

func (u *unit) Do(c *Context, before json.RawMessage) error {
	var p beforeUnit
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origin == PREEXISTING {
		return nil
	}
	if err := c.Amb.Unit.Enable(u.label_name); err != nil {
		return err
	}
	if u.start && !u.live(c) {
		return c.Amb.Unit.Start(u.label_name)
	}
	return nil
}

func (u *unit) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	var p beforeUnit
	if err := json.Unmarshal(before, &p); err != nil {
		return "", "", err
	}
	s, err := c.Amb.Unit.State(u.label_name)
	if err != nil {
		return "", "", err
	}
	switch {
	case s == "enabled" && u.start && !u.live(c):
		return A_META, "enabled but not running", nil
	case s == "enabled":
		return COMPLETE, "enabled", nil
	case p.Origin == PREEXISTING:
		return FOREIGN, "was enabled, now " + s, nil
	case s == p.State:
		return ABSENT, s, nil
	}
	return FOREIGN, "was " + p.State + ", now " + s, nil
}

func (u *unit) Rollback(c *Context, before json.RawMessage) error {
	var p beforeUnit
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origin == PREEXISTING {
		return nil
	}
	s, err := c.Amb.Unit.State(u.label_name)
	if err != nil {
		return err
	}
	if u.start && u.live(c) {
		if err := c.Amb.Unit.Stop(u.label_name); err != nil {
			return err
		}
	}
	if s == p.State {
		return nil
	}
	if s != "enabled" {
		return Error("RX-RIPRESA-001", u.label_name+" is "+s+": we did not set it that way")
	}
	return c.Amb.Unit.Disable(u.label_name)
}

func (u *unit) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	var p beforeUnit
	if err := json.Unmarshal(before, &p); err != nil {
		return false, "", err
	}
	if p.Origin == PREEXISTING {
		return true, "already enabled: left untouched", nil
	}
	s, err := c.Amb.Unit.State(u.label_name)
	if err != nil {
		return false, "", err
	}
	// «cancelled» = no longer enabled by us (a later step may have removed its file: not-found)
	return s != "enabled", s, nil
}
