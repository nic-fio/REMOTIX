package motore

import "encoding/json"

// abilita-unita: un'unità di systemd abilitata (§6.6.3), sul D-Bus di systemd (EnableUnitFiles e
// GetUnitFileState: quel che fanno systemctl enable e is-enabled, senza lanciarli, §10.14). Reversibilità ESATTA; un'unità già abilitata è PREESISTENTE e resta
// abilitata; un'unità mascherata non si tocca (l'amministratore l'ha spenta apposta).
//
// parametri: unita; avvia ("si": anche accesa subito; annullare la spegne e la disabilita). ⚠ Nessun
// piano nuovo lo usa più (era il timer degli aggiornamenti, tolto con D14, DECISIONI §10.23): resta
// perché la disinstallazione di un'installazione fatta prima sappia spegnere quel che aveva acceso.

func init() { registraTipo("abilita-unita", nuovaUnita) }

// PianoUnita prepara il passo del piano.
func PianoUnita(id, unita string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "abilita-unita",
		Parametri:      map[string]string{"unita": unita},
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
	Origine Origine `json:"origine"`
	Stato   string  `json:"stato"` // quel che diceva is-enabled
}

func nuovaUnita(p AzionePiano) (Azione, error) {
	return &unita{p.Parametri["unita"], p.Parametri["avvia"] == "si"}, nil
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
	return []string{"unita:" + u.nome + "=" + s}, nil
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
		return A_META, "enabled ma non accesa", nil
	case s == "enabled":
		return COMPLETO, "enabled", nil
	case p.Origine == PREESISTENTE:
		return ESTRANEO, "era abilitata, ora è " + s, nil
	case s == p.Stato:
		return ASSENTE, s, nil
	}
	return ESTRANEO, "era " + p.Stato + ", ora è " + s, nil
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
		return Errore("RX-RIPRESA-001", u.nome+" è "+s+": non l'abbiamo messa noi così")
	}
	return c.Amb.Unita.Disabilita(u.nome)
}

func (u *unita) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p primaUnita
	if err := json.Unmarshal(prima, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "era già abilitata: non si tocca", nil
	}
	s, err := c.Amb.Unita.Stato(u.nome)
	if err != nil {
		return false, "", err
	}
	// «annullata» = non più abilitata da noi (un passo dopo può averne tolto il file: not-found)
	return s != "enabled", s, nil
}
