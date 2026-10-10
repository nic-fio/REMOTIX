package motore

import "encoding/json"

// abilita-unita: an enabled systemd unit (§6.6.3), over systemd's D-Bus (EnableUnitFiles and
// GetUnitFileState: what systemctl enable and is-enabled do, without launching them, §10.14). EXACT reversibility; a unit already enabled is PRE-EXISTING and stays
// enabled; a masked unit is not touched (the administrator turned it off on purpose).
//
// parameters: unita; avvia ("yes": also started at once; cancelling stops and disables it). ⚠ No
// new plan uses it any more (it was the updates timer, removed with D14, DECISIONI §10.23): it stays
// so that uninstalling an installation made earlier knows how to stop what it had started.

func init() { registraTipo("enable-unit", nuovaUnita) }

// PianoUnita prepares the plan's step.
func PianoUnita(id, unita string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "enable-unit",
		Parametri:      map[string]string{"unit": unita},
		Descrizione:    T("az.unita", unita),
		ComeSiFa:       T("az.unita.fa", unita),
		ComeSiVerifica: T("az.unita.verifica", unita),
		ComeSiAnnulla:  T("az.unita.annulla", unita),
		Reversibilita:  ESATTA,
	}
}

type unita struct {
	nome  string
	avvia bool
}

type primaUnita struct {
	Origine Origine `json:"origin"`
	Stato   string  `json:"state"` // what is-enabled said
}

func nuovaUnita(p AzionePiano) (Azione, error) {
	return &unita{p.Parametri["unit"], p.Parametri["start"] == "yes"}, nil
}

func (u *unita) attiva(c *Contesto) bool {
	a, err := c.Amb.Unita.Attiva(u.nome)
	return err == nil && a == "active"
}

func (u *unita) Vincoli(c *Contesto) ([]string, error) {
	s, err := c.Amb.Unita.Stato(u.nome)
	if err != nil {
		return nil, err
	}
	return []string{"unit:" + u.nome + "=" + s}, nil
}

func (u *unita) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	s, err := c.Amb.Unita.Stato(u.nome)
	if err != nil {
		return nil, "", err
	}
	switch s {
	case "masked", "masked-runtime":
		return nil, "", Errore("RX-SYSTEMD-002", u.nome)
	case "not-found":
		return nil, "", Errore("RX-SYSTEMD-003", u.nome)
	}
	p := primaUnita{Origine: DIRETTA, Stato: s}
	if s == "enabled" {
		p.Origine = PREESISTENTE
	}
	return jsonDi(p), p.Origine, nil
}

func (u *unita) Fai(c *Contesto, prima json.RawMessage) error {
	var p primaUnita
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	if err := c.Amb.Unita.Abilita(u.nome); err != nil {
		return err
	}
	if u.avvia && !u.attiva(c) {
		return c.Amb.Unita.Avvia(u.nome)
	}
	return nil
}

func (u *unita) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p primaUnita
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	s, err := c.Amb.Unita.Stato(u.nome)
	if err != nil {
		return "", "", err
	}
	switch {
	case s == "enabled" && u.avvia && !u.attiva(c):
		return A_META, "enabled but not running", nil
	case s == "enabled":
		return COMPLETO, "enabled", nil
	case p.Origine == PREESISTENTE:
		return ESTRANEO, "was enabled, now " + s, nil
	case s == p.Stato:
		return ASSENTE, s, nil
	}
	return ESTRANEO, "was " + p.Stato + ", now " + s, nil
}

func (u *unita) Annulla(c *Contesto, prima json.RawMessage) error {
	var p primaUnita
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	s, err := c.Amb.Unita.Stato(u.nome)
	if err != nil {
		return err
	}
	if u.avvia && u.attiva(c) {
		if err := c.Amb.Unita.Ferma(u.nome); err != nil {
			return err
		}
	}
	if s == p.Stato {
		return nil
	}
	if s != "enabled" {
		return Errore("RX-RIPRESA-001", u.nome+" is "+s+": we did not set it that way")
	}
	return c.Amb.Unita.Disabilita(u.nome)
}

func (u *unita) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p primaUnita
	if err := json.Unmarshal(prima, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "already enabled: left untouched", nil
	}
	s, err := c.Amb.Unita.Stato(u.nome)
	if err != nil {
		return false, "", err
	}
	// «cancelled» = no longer enabled by us (a later step may have removed its file: not-found)
	return s != "enabled", s, nil
}
