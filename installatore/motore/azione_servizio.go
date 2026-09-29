package motore

import (
	"encoding/json"
	"strconv"
	"time"
)

// accendi-servizio: l'ACCENSIONE fra 7a e 7b (§6.0 punto 5): il servizio si abilita e si accende sul
// D-Bus di systemd (EnableUnitFiles, StartUnit) e si considera fatto solo se è attivo E la porta
// è in ascolto in TCP (la pagina) e UDP (QUIC). Reversibilità ESATTA: si spegne e si disabilita
// solo quel che ha fatto REMOTIX; un servizio già abilitato e acceso è PREESISTENTE.
//
// parametri: unita, porta.

func init() { registraTipo("accendi-servizio", nuovaServizio) }

// PianoAccendiServizio prepara il passo del piano.
func PianoAccendiServizio(id, unita string, porta int) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "accendi-servizio",
		Parametri:      map[string]string{"unita": unita, "porta": strconv.Itoa(porta)},
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
	Origine Origine `json:"origine"`
	File    string  `json:"file"`   // enabled, disabled…
	Attiva  string  `json:"attiva"` // active, inactive…
}

func nuovaServizio(p AzionePiano) (Azione, error) {
	n, _ := strconv.Atoi(p.Parametri["porta"])
	return &servizio{unita: nonVuoto(p.Parametri["unita"], "remotix.service"), porta: n}, nil
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
	return []string{"servizio:" + s.unita + "=" + f + " " + a}, nil
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
	// 7b: la porta si apre dopo l'avvio (il certificato si genera al primo avvio): si aspetta fino
	// a 60 s, poi «controlla» dirà com'è
	for i := 0; i < 120; i++ {
		if ok, _ := s.inAscolto(c); ok {
			break
		}
		time.Sleep(500 * time.Millisecond)
	}
	return nil
}

// inAscolto: la porta in TCP e UDP (7b). Senza porta nei parametri (le prove) non si guarda.
func (s *servizio) inAscolto(c *Contesto) (bool, string) {
	if s.porta == 0 {
		return true, ""
	}
	for _, proto := range []string{"tcp", "udp"} {
		if ok, letto := portaInAscolto(c.Amb, s.porta, proto); !ok || !letto {
			return false, strconv.Itoa(s.porta) + "/" + proto + " non in ascolto"
		}
	}
	return true, strconv.Itoa(s.porta) + " tcp e udp in ascolto"
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
			return A_META, "attivo ma " + det, nil
		}
	}
	if p.Origine == PREESISTENTE {
		return ESTRANEO, "era abilitato e acceso, ora " + f + " " + a, nil
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
		return true, "era già abilitato e acceso: non si tocca", nil
	}
	f, a, err := s.stato(c)
	if err != nil {
		return false, "", err
	}
	// «annullata» = il nostro effetto non c'è più: né abilitato né acceso da noi. Un passo dopo
	// (la disinstallazione che toglie il pacchetto) può portare l'unità a not-found: va bene lo stesso.
	ok := (p.File == "enabled" || f != "enabled") && (p.Attiva == "active" || a != "active")
	return ok, f + " " + a, nil
}
