package motore

import (
	"encoding/json"
	"strings"
)

// aggiungi-utente-a-gruppo: a person in the card's group (§6.4, DECISIONI §7.21).
// EXACT reversibility; ⛔ whoever was already there (even as primary group) is PRE-EXISTING and
// rolling back never removes them (R33).
//
// parameters: utente, gruppo.

func init() { registraTipo("add-user-to-group", newGroup) }

// PlanGroup prepares the plan's step.
func PlanGroup(id, utente, gruppo string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "add-user-to-group",
		Parametri:     map[string]string{"user": utente, "group": gruppo},
		Description:   T("az.gruppo", utente, gruppo),
		ComeSiFa:      T("az.gruppo.fa", utente, gruppo),
		HowToVerify:   T("az.gruppo.verifica", utente, gruppo),
		HowToUndo:     T("az.gruppo.annulla", utente, gruppo),
		Reversibilita: ESATTA,
	}
}

type gruppo struct{ utente, gruppo string }

type beforeGroup struct {
	Origine Origine  `json:"origin"`
	Member  bool     `json:"member"`
	Main    bool     `json:"primary,omitempty"` // the group is their primary group
	Members []string `json:"members"`
}

func newGroup(p AzionePiano) (Azione, error) {
	return &gruppo{p.Parametri["user"], p.Parametri["group"]}, nil
}

// membro: is the user in the group (explicitly or as primary)?
func (g *gruppo) member(c *Contesto) (esplicito, principale bool, membri []string, err error) {
	membri, gid, esiste, err := c.Amb.Gruppi.Members(g.gruppo)
	if err != nil {
		return
	}
	if !esiste {
		err = Errore("RX-GRUPPI-002", g.gruppo)
		return
	}
	userGid, ok, err2 := c.Amb.Gruppi.PrimaryGroup(g.utente)
	if err2 != nil {
		err = err2
		return
	}
	if !ok {
		err = Errore("RX-GRUPPI-003", g.utente)
		return
	}
	for _, m := range membri {
		if m == g.utente {
			esplicito = true
		}
	}
	principale = userGid == gid
	return
}

func (g *gruppo) Vincoli(c *Contesto) ([]string, error) {
	membri, _, esiste, err := c.Amb.Gruppi.Members(g.gruppo)
	if err != nil {
		return nil, err
	}
	if !esiste {
		return []string{"group:" + g.gruppo + "=absent"}, nil
	}
	return []string{"group:" + g.gruppo + "=" + strings.Join(membri, ",")}, nil
}

func (g *gruppo) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	esp, is_primary, membri, err := g.member(c)
	if err != nil {
		return nil, "", err
	}
	p := beforeGroup{Origine: DIRETTA, Member: esp || is_primary, Main: is_primary, Members: membri}
	if p.Member {
		p.Origine = PREESISTENTE
	}
	return jsonDi(p), p.Origine, nil
}

func (g *gruppo) Fai(c *Contesto, prima json.RawMessage) error {
	var p beforeGroup
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	esp, _, _, err := g.member(c)
	if err != nil || esp {
		return err
	}
	return c.Amb.Gruppi.Add(g.utente, g.gruppo)
}

func (g *gruppo) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p beforeGroup
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	esp, is_primary, _, err := g.member(c)
	if err != nil {
		return "", "", err
	}
	if esp || is_primary {
		return COMPLETO, g.utente + " is in " + g.gruppo, nil
	}
	if p.Origine == PREESISTENTE {
		return ESTRANEO, g.utente + " was there and someone removed it", nil
	}
	return ASSENTE, g.utente + " is not in " + g.gruppo, nil
}

func (g *gruppo) Annulla(c *Contesto, prima json.RawMessage) error {
	var p beforeGroup
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil // ⛔ never (R33)
	}
	esp, _, _, err := g.member(c)
	if err != nil || !esp {
		return err
	}
	return c.Amb.Gruppi.Togli(g.utente, g.gruppo)
}

func (g *gruppo) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p beforeGroup
	if err := json.Unmarshal(prima, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "already there: left untouched", nil
	}
	esp, _, _, err := g.member(c)
	if err != nil {
		return false, "", err
	}
	if esp {
		return false, g.utente + " is still in " + g.gruppo, nil
	}
	return true, g.utente + " is no longer in " + g.gruppo, nil
}
