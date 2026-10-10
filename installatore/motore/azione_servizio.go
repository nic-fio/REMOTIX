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
// parameters: unit, port.

func init() { registerType("start-service", newService) }

// PlanStartService prepares the plan's step.
func PlanStartService(id, unit string, port int) PlanAction {
	return PlanAction{
		ID: id, Kind: "start-service",
		Parameters:    map[string]string{"unit": unit, "port": strconv.Itoa(port)},
		Description:   T("az.service"),
		ComeSiFa:      T("az.service.fa"),
		HowToVerify:   T("az.service.verify"),
		HowToUndo:     T("az.service.rollback"),
		Reversibility: EXACT,
	}
}

type service struct {
	unit string
	port int
}

type beforeService struct {
	Origin Origin `json:"origin"`
	File   string `json:"file"`   // enabled, disabled…
	Active string `json:"active"` // active, inactive…
}

func newService(p PlanAction) (Action, error) {
	n, _ := strconv.Atoi(p.Parameters["port"])
	return &service{unit: notEmpty(p.Parameters["unit"], "remotix.service"), port: n}, nil
}

func (s *service) state(c *Context) (string, string, error) {
	f, err := c.Amb.Unit.State(s.unit)
	if err != nil {
		return "", "", err
	}
	a, err := c.Amb.Unit.Active(s.unit)
	return f, a, err
}

func (s *service) Constraints(c *Context) ([]string, error) {
	f, a, err := s.state(c)
	if err != nil {
		return nil, err
	}
	return []string{"service:" + s.unit + "=" + f + " " + a}, nil
}

func (s *service) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	f, a, err := s.state(c)
	if err != nil {
		return nil, "", err
	}
	switch f {
	case "masked", "masked-runtime":
		return nil, "", Error("RX-SYSTEMD-002", s.unit)
	case "not-found":
		return nil, "", Error("RX-SYSTEMD-003", s.unit)
	}
	p := beforeService{Origin: DIRECT, File: f, Active: a}
	if f == "enabled" && a == "active" {
		p.Origin = PREEXISTING
	}
	return jsonDi(p), p.Origin, nil
}

func (s *service) Do(c *Context, before json.RawMessage) error {
	var p beforeService
	if err := json.Unmarshal(before, &p); err != nil || p.Origin == PREEXISTING {
		return err
	}
	f, a, err := s.state(c)
	if err != nil {
		return err
	}
	if f != "enabled" {
		if err := c.Amb.Unit.Enable(s.unit); err != nil {
			return err
		}
	}
	if a != "active" {
		if err := c.Amb.Unit.Start(s.unit); err != nil {
			return err
		}
	}
	// 7b: the port opens after start-up (the certificate is generated at first start): we wait up
	// to 60 s, then «controlla» will say how it is
	for i := 0; i < 120; i++ {
		if ok, _ := s.listening(c); ok {
			break
		}
		time.Sleep(500 * time.Millisecond)
	}
	return nil
}

// listening: the port on TCP and UDP (7b). Without a port in the parameters (the tests) it is not checked.
func (s *service) listening(c *Context) (bool, string) {
	if s.port == 0 {
		return true, ""
	}
	for _, proto := range []string{"tcp", "udp"} {
		if ok, read := listeningPort(c.Amb, s.port, proto); !ok || !read {
			return false, strconv.Itoa(s.port) + "/" + proto + " not listening"
		}
	}
	return true, strconv.Itoa(s.port) + " tcp and udp listening"
}

func (s *service) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	var p beforeService
	if err := json.Unmarshal(before, &p); err != nil {
		return "", "", err
	}
	f, a, err := s.state(c)
	if err != nil {
		return "", "", err
	}
	if f == "enabled" && a == "active" {
		if ok, det := s.listening(c); ok {
			return COMPLETE, "enabled, active, " + det, nil
		} else if p.Origin != PREEXISTING {
			return A_META, "active but " + det, nil
		}
	}
	if p.Origin == PREEXISTING {
		return FOREIGN, "was enabled and running, now " + f + " " + a, nil
	}
	if f == p.File && a == p.Active {
		return ABSENT, f + " " + a, nil
	}
	return A_META, f + " " + a, nil
}

func (s *service) Rollback(c *Context, before json.RawMessage) error {
	var p beforeService
	if err := json.Unmarshal(before, &p); err != nil || p.Origin == PREEXISTING {
		return err
	}
	f, a, err := s.state(c)
	if err != nil {
		return err
	}
	if a != "inactive" && p.Active != "active" {
		if err := c.Amb.Unit.Stop(s.unit); err != nil {
			return err
		}
	}
	if f == "enabled" && p.File != "enabled" {
		return c.Amb.Unit.Disable(s.unit)
	}
	return nil
}

func (s *service) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	var p beforeService
	if err := json.Unmarshal(before, &p); err != nil {
		return false, "", err
	}
	if p.Origin == PREEXISTING {
		return true, "already enabled and running: left untouched", nil
	}
	f, a, err := s.state(c)
	if err != nil {
		return false, "", err
	}
	// «cancelled» = our effect is gone: neither enabled nor started by us. A later step
	// (the uninstallation that removes the package) can bring the unit to not-found: that is fine too.
	ok := (p.File == "enabled" || f != "enabled") && (p.Active == "active" || a != "active")
	return ok, f + " " + a, nil
}
