package engine

import (
	"encoding/json"
	"strings"
)

// aggiungi-utente-a-gruppo: a person in the card's group (§6.4, DECISIONI §7.21).
// EXACT reversibility; ⛔ whoever was already there (even as primary group) is PRE-EXISTING and
// rolling back never removes them (R33).
//
// parameters: user, group.

func init() { registerType("add-user-to-group", newGroup) }

// PlanGroup prepares the plan's step.
func PlanGroup(id, user, group string) PlanAction {
	return PlanAction{
		ID: id, Type: "add-user-to-group",
		Parameters:     map[string]string{"user": user, "group": group},
		Description:   T("az.group", user, group),
		ComeSiFa:      T("az.group.fa", user, group),
		HowToVerify:   T("az.group.verifica", user, group),
		HowToUndo:     T("az.group.annulla", user, group),
		Reversibility: EXACT,
	}
}

type group struct{ user, group string }

type beforeGroup struct {
	Origine    Origine  `json:"origin"`
	Member     bool     `json:"member"`
	Main bool     `json:"primary,omitempty"` // the group is their primary group
	Members    []string `json:"members"`
}

func newGroup(p PlanAction) (Action, error) {
	return &group{p.Parameters["user"], p.Parameters["group"]}, nil
}

// member: is the user in the group (explicitly or as primary)?
func (g *group) member(c *Context) (explicit, main bool, members []string, err error) {
	members, gid, path_exists, err := c.Env.Gruppi.Members(g.group)
	if err != nil {
		return
	}
	if !path_exists {
		err = Error("RX-GRUPPI-002", g.group)
		return
	}
	userGid, ok, err2 := c.Env.Gruppi.PrimaryGroup(g.user)
	if err2 != nil {
		err = err2
		return
	}
	if !ok {
		err = Error("RX-GRUPPI-003", g.user)
		return
	}
	for _, m := range members {
		if m == g.user {
			explicit = true
		}
	}
	main = userGid == gid
	return
}

func (g *group) Constraints(c *Context) ([]string, error) {
	members, _, path_exists, err := c.Env.Gruppi.Members(g.group)
	if err != nil {
		return nil, err
	}
	if !path_exists {
		return []string{"group:" + g.group + "=absent"}, nil
	}
	return []string{"group:" + g.group + "=" + strings.Join(members, ",")}, nil
}

func (g *group) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	esp, is_primary, members, err := g.member(c)
	if err != nil {
		return nil, "", err
	}
	p := beforeGroup{Origine: DIRECT, Member: esp || is_primary, Main: is_primary, Members: members}
	if p.Member {
		p.Origine = PREEXISTING
	}
	return jsonDi(p), p.Origine, nil
}

func (g *group) Do(c *Context, before json.RawMessage) error {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origine == PREEXISTING {
		return nil
	}
	esp, _, _, err := g.member(c)
	if err != nil || esp {
		return err
	}
	return c.Env.Gruppi.Insert(g.user, g.group)
}

func (g *group) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return "", "", err
	}
	esp, is_primary, _, err := g.member(c)
	if err != nil {
		return "", "", err
	}
	if esp || is_primary {
		return COMPLETE, g.user + " is in " + g.group, nil
	}
	if p.Origine == PREEXISTING {
		return FOREIGN, g.user + " was there and someone removed it", nil
	}
	return ABSENT, g.user + " is not in " + g.group, nil
}

func (g *group) Rollback(c *Context, before json.RawMessage) error {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origine == PREEXISTING {
		return nil // ⛔ never (R33)
	}
	esp, _, _, err := g.member(c)
	if err != nil || !esp {
		return err
	}
	return c.Env.Gruppi.Remove(g.user, g.group)
}

func (g *group) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
	var p beforeGroup
	if err := json.Unmarshal(before, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREEXISTING {
		return true, "already there: left untouched", nil
	}
	esp, _, _, err := g.member(c)
	if err != nil {
		return false, "", err
	}
	if esp {
		return false, g.user + " is still in " + g.group, nil
	}
	return true, g.user + " is no longer in " + g.group, nil
}
