package motore

import (
	"encoding/json"
	"strconv"
	"time"
)

// accendi-servizio: the SWITCH-ON between 7a and 7b (§6.0 point 5): the service is enabled and started over
// systemd's D-Bus (EnableUnitFiles, StartUnit) and counts as done only if it is active AND the port
// is listening on TCP (the page) and UDP (QUIC). EXACT reversibility: only what REMOTIX did is
// stopped and disabled; a service already enabled and running is PRE-EXISTING.
//
// parameters: unita, porta.

func init() { registraTipo("start-service", nuovaServizio) }

// PianoAccendiServizio prepares the plan's step.
func PianoAccendiServizio(id, unita string, porta int) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "start-service",
		Parametri:      map[string]string{"unit": unita, "port": strconv.Itoa(porta)},
		Descrizione:    T("az.servizio"),
		ComeSiFa:       T("az.servizio.fa"),
		ComeSiVerifica: T("az.servizio.verifica"),
		ComeSiAnnulla:  T("az.servizio.annulla"),
		Reversibilita:  ESATTA,
	}
}

type servizio struct {
	unita string
	porta int
}

type primaServizio struct {
	Origine Origine `json:"origin"`
	File    string  `json:"file"`   // enabled, disabled…
	Attiva  string  `json:"active"` // active, inactive…
}

func nuovaServizio(p AzionePiano) (Azione, error) {
	n, _ := strconv.Atoi(p.Parametri["port"])
	return &servizio{unita: nonVuoto(p.Parametri["unit"], "remotix.service"), porta: n}, nil
}

func (s *servizio) stato(c *Contesto) (string, string, error) {
	f, err := c.Amb.Unita.Stato(s.unita)
	if err != nil {
		return "", "", err
	}
	a, err := c.Amb.Unita.Attiva(s.unita)
	return f, a, err
}

func (s *servizio) Vincoli(c *Contesto) ([]string, error) {
	f, a, err := s.stato(c)
	if err != nil {
		return nil, err
	}
	return []string{"service:" + s.unita + "=" + f + " " + a}, nil
}

func (s *servizio) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	f, a, err := s.stato(c)
	if err != nil {
		return nil, "", err
	}
	switch f {
	case "masked", "masked-runtime":
		return nil, "", Errore("RX-SYSTEMD-002", s.unita)
	case "not-found":
		return nil, "", Errore("RX-SYSTEMD-003", s.unita)
	}
	p := primaServizio{Origine: DIRETTA, File: f, Attiva: a}
	if f == "enabled" && a == "active" {
		p.Origine = PREESISTENTE
	}
	return jsonDi(p), p.Origine, nil
}

func (s *servizio) Fai(c *Contesto, prima json.RawMessage) error {
	var p primaServizio
	if err := json.Unmarshal(prima, &p); err != nil || p.Origine == PREESISTENTE {
		return err
	}
	f, a, err := s.stato(c)
	if err != nil {
		return err
	}
	if f != "enabled" {
		if err := c.Amb.Unita.Abilita(s.unita); err != nil {
			return err
		}
	}
	if a != "active" {
		if err := c.Amb.Unita.Avvia(s.unita); err != nil {
			return err
		}
	}
	// 7b: the port opens after start-up (the certificate is generated at first start): we wait up
	// to 60 s, then «controlla» will say how it is
	for i := 0; i < 120; i++ {
		if ok, _ := s.inAscolto(c); ok {
			break
		}
		time.Sleep(500 * time.Millisecond)
	}
	return nil
}

// inAscolto: the port on TCP and UDP (7b). Without a port in the parameters (the tests) it is not checked.
func (s *servizio) inAscolto(c *Contesto) (bool, string) {
	if s.porta == 0 {
		return true, ""
	}
	for _, proto := range []string{"tcp", "udp"} {
		if ok, letto := portaInAscolto(c.Amb, s.porta, proto); !ok || !letto {
			return false, strconv.Itoa(s.porta) + "/" + proto + " not listening"
		}
	}
	return true, strconv.Itoa(s.porta) + " tcp and udp listening"
}

func (s *servizio) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p primaServizio
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	f, a, err := s.stato(c)
	if err != nil {
		return "", "", err
	}
	if f == "enabled" && a == "active" {
		if ok, det := s.inAscolto(c); ok {
			return COMPLETO, "enabled, active, " + det, nil
		} else if p.Origine != PREESISTENTE {
			return A_META, "active but " + det, nil
		}
	}
	if p.Origine == PREESISTENTE {
		return ESTRANEO, "was enabled and running, now " + f + " " + a, nil
	}
	if f == p.File && a == p.Attiva {
		return ASSENTE, f + " " + a, nil
	}
	return A_META, f + " " + a, nil
}

func (s *servizio) Annulla(c *Contesto, prima json.RawMessage) error {
	var p primaServizio
	if err := json.Unmarshal(prima, &p); err != nil || p.Origine == PREESISTENTE {
		return err
	}
	f, a, err := s.stato(c)
	if err != nil {
		return err
	}
	if a != "inactive" && p.Attiva != "active" {
		if err := c.Amb.Unita.Ferma(s.unita); err != nil {
			return err
		}
	}
	if f == "enabled" && p.File != "enabled" {
		return c.Amb.Unita.Disabilita(s.unita)
	}
	return nil
}

func (s *servizio) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p primaServizio
	if err := json.Unmarshal(prima, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "already enabled and running: left untouched", nil
	}
	f, a, err := s.stato(c)
	if err != nil {
		return false, "", err
	}
	// «cancelled» = our effect is gone: neither enabled nor started by us. A later step
	// (the uninstallation that removes the package) can bring the unit to not-found: that is fine too.
	ok := (p.File == "enabled" || f != "enabled") && (p.Attiva == "active" || a != "active")
	return ok, f + " " + a, nil
}
