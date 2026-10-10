package motore

import (
	"encoding/json"
	"strings"
)

// aggiungi-utente-a-gruppo: a person in the card's group (§6.4, DECISIONI §7.21).
// EXACT reversibility; ⛔ whoever was already there (even as primary group) is PRE-EXISTING and
// rolling back never removes them (R33).
//
// parameters: username, grp.

func init() { registerType("add-user-to-group", newGroup) }

// PlanGroup prepares the plan's step.
func PlanGroup(id, username, grp string) PlanAction {
	return PlanAction{
		ID: id, Kind: "add-user-to-group",
		Parameters:    map[string]string{"user": username, "group": grp},
		Description:   T("az.grp", username, grp),
		ComeSiFa:      T("az.grp.fa", username, grp),
		HowToVerify:   T("az.grp.verify", username, grp),
		HowToUndo:     T("az.grp.rollback", username, grp),
		Reversibility: EXACT,
	}
}

type grp struct{ username, grp string }

type beforeGroup struct {
	Origin  Origin   `json:"origin"`
	Member  bool     `json:"member"`
	Main    bool     `json:"primary,omitempty"` // the group is their primary group
	Members []string `json:"members"`
}

func newGroup(p PlanAction) (Action, error) {
	return &grp{p.Parameters["user"], p.Parameters["group"]}, nil
}

// member: is the user in the group (explicitly or as primary)?
func (g *grp) member(c *Context) (explicit, primary bool, members []string, err error) {
	members, gid, path_exists, err := c.Amb.Groups.Members(g.grp)
	if err != nil {
		return
	}
	if !path_exists {
		err = Error("RX-GRUPPI-002", g.grp)
		return
	}
	userGid, ok, err2 := c.Amb.Groups.PrimaryGroup(g.username)
	if err2 != nil {
		err = err2
		return
	}
	if !ok {
		err = Error("RX-GRUPPI-003", g.username)
		return
	}
	for _, m := range members {
		if m == g.username {
			explicit = true
		}
	}
	primary = userGid == gid
	return
}

func (g *grp) Constraints(c *Context) ([]string, error) {
	members, _, path_exists, err := c.Amb.Groups.Members(g.grp)
	if err != nil {
		return nil, err
	}
	if !path_exists {
		return []string{"group:" + g.grp + "=absent"}, nil
	}
	return []string{"group:" + g.grp + "=" + strings.Join(members, ",")}, nil
}

func (g *grp) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	esp, is_primary, members, err := g.member(c)
	if err != nil {
		return nil, "", err
	}
	p := beforeGroup{Origin: DIRECT, Member: esp || is_primary, Main: is_primary, Members: members}
	if p.Member {
		p.Origin = PREEXISTING
	}
	return jsonDi(p), p.Origin, nil
}

func (g *grp) Do(c *Context, before json.RawMessage) error {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origin == PREEXISTING {
		return nil
	}
	esp, _, _, err := g.member(c)
	if err != nil || esp {
		return err
	}
	return c.Amb.Groups.Add(g.username, g.grp)
}

func (g *grp) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return "", "", err
	}
	esp, is_primary, _, err := g.member(c)
	if err != nil {
		return "", "", err
	}
	if esp || is_primary {
		return COMPLETE, g.username + " is in " + g.grp, nil
	}
	if p.Origin == PREEXISTING {
		return FOREIGN, g.username + " was there and someone removed it", nil
	}
	return ABSENT, g.username + " is not in " + g.grp, nil
}

func (g *grp) Rollback(c *Context, before json.RawMessage) error {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origin == PREEXISTING {
		return nil // ⛔ never (R33)
	}
	esp, _, _, err := g.member(c)
	if err != nil || !esp {
		return err
	}
	return c.Amb.Groups.Revoke(g.username, g.grp)
}

func (g *grp) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return false, "", err
	}
	if p.Origin == PREEXISTING {
		return true, "already there: left untouched", nil
	}
	esp, _, _, err := g.member(c)
	if err != nil {
		return false, "", err
	}
	if esp {
		return false, g.username + " is still in " + g.grp, nil
	}
	return true, g.username + " is no longer in " + g.grp, nil
}
