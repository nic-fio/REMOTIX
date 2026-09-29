package motore

import (
	"encoding/json"
	"strings"
)

// aggiungi-utente-a-gruppo: una persona nel gruppo della scheda (§6.4, DECISIONI §7.21).
// Reversibilità ESATTA; ⛔ chi c'era già (anche come gruppo principale) è PREESISTENTE e il
// ritorno indietro non lo toglie mai (R33).
//
// parametri: utente, gruppo.

func init() { registraTipo("aggiungi-utente-a-gruppo", nuovaGruppo) }

// PianoGruppo prepara il passo del piano.
func PianoGruppo(id, utente, gruppo string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "aggiungi-utente-a-gruppo",
		Parametri:      map[string]string{"utente": utente, "gruppo": gruppo},
		Descrizione:    T("az.gruppo", utente, gruppo),
		ComeSiFa:       T("az.gruppo.fa", utente, gruppo),
		ComeSiVerifica: T("az.gruppo.verifica", utente, gruppo),
		ComeSiAnnulla:  T("az.gruppo.annulla", utente, gruppo),
		Reversibilita:  ESATTA,
	}
}

type gruppo struct{ utente, gruppo string }

type primaGruppo struct {
	Origine    Origine  `json:"origine"`
	Membro     bool     `json:"membro"`
	Principale bool     `json:"principale,omitempty"` // il gruppo è il suo gruppo principale
	Membri     []string `json:"membri"`
}

func nuovaGruppo(p AzionePiano) (Azione, error) {
	return &gruppo{p.Parametri["utente"], p.Parametri["gruppo"]}, nil
}

// membro: l'utente è nel gruppo (esplicito o come principale)?
func (g *gruppo) membro(c *Contesto) (esplicito, principale bool, membri []string, err error) {
	membri, gid, esiste, err := c.Amb.Gruppi.Membri(g.gruppo)
	if err != nil {
		return
	}
	if !esiste {
		err = Errore("RX-GRUPPI-002", g.gruppo)
		return
	}
	gidUtente, ok, err2 := c.Amb.Gruppi.GruppoPrimario(g.utente)
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
	principale = gidUtente == gid
	return
}

func (g *gruppo) Vincoli(c *Contesto) ([]string, error) {
	membri, _, esiste, err := c.Amb.Gruppi.Membri(g.gruppo)
	if err != nil {
		return nil, err
	}
	if !esiste {
		return []string{"gruppo:" + g.gruppo + "=assente"}, nil
	}
	return []string{"gruppo:" + g.gruppo + "=" + strings.Join(membri, ",")}, nil
}

func (g *gruppo) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	esp, princ, membri, err := g.membro(c)
	if err != nil {
		return nil, "", err
	}
	p := primaGruppo{Origine: DIRETTA, Membro: esp || princ, Principale: princ, Membri: membri}
	if p.Membro {
		p.Origine = PREESISTENTE
	}
	return jsonDi(p), p.Origine, nil
}

func (g *gruppo) Fai(c *Contesto, prima json.RawMessage) error {
	var p primaGruppo
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	esp, _, _, err := g.membro(c)
	if err != nil || esp {
		return err
	}
	return c.Amb.Gruppi.Aggiungi(g.utente, g.gruppo)
}

func (g *gruppo) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p primaGruppo
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	esp, princ, _, err := g.membro(c)
	if err != nil {
		return "", "", err
	}
	if esp || princ {
		return COMPLETO, g.utente + " è in " + g.gruppo, nil
	}
	if p.Origine == PREESISTENTE {
		return ESTRANEO, g.utente + " c'era e qualcuno l'ha tolto", nil
	}
	return ASSENTE, g.utente + " non è in " + g.gruppo, nil
}

func (g *gruppo) Annulla(c *Contesto, prima json.RawMessage) error {
	var p primaGruppo
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil // ⛔ mai (R33)
	}
	esp, _, _, err := g.membro(c)
	if err != nil || !esp {
		return err
	}
	return c.Amb.Gruppi.Togli(g.utente, g.gruppo)
}

func (g *gruppo) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p primaGruppo
	if err := json.Unmarshal(prima, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "c'era già: non si tocca", nil
	}
	esp, _, _, err := g.membro(c)
	if err != nil {
		return false, "", err
	}
	if esp {
		return false, g.utente + " è ancora in " + g.gruppo, nil
	}
	return true, g.utente + " non è più in " + g.gruppo, nil
}
