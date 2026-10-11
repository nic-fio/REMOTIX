package motore

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"slices"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/godbus/dbus/v5"
)

// Bus: the system D-Bus, opened at the first request. The engine talks to systemd, logind and firewalld
// from here, never by launching systemctl, loginctl, busctl or firewall-cmd (DECISIONI §10.14).
// Without a bus (a container, a machine not booted with systemd) every request gives an error, and
// the caller treats it as SCONOSCIUTO — never as «all right».
type Bus struct {
	una  sync.Once
	conn *dbus.Conn
	err  error
}

func (b *Bus) c() (*dbus.Conn, error) {
	if b == nil {
		return nil, errors.New("no D-Bus")
	}
	b.una.Do(func() { b.conn, b.err = dbus.ConnectSystemBus() })
	return b.conn, b.err
}

const (
	sdName    = "org.freedesktop.systemd1"
	sdPath    = "/org/freedesktop/systemd1"
	sdManager = "org.freedesktop.systemd1.Manager"
	fwName    = "org.fedoraproject.FirewallD1"
	fwPath    = "/org/fedoraproject/FirewallD1"
)

// HasOwner: does someone answer to that name on the bus?
func (b *Bus) HasOwner(nome string) (bool, error) {
	c, err := b.c()
	if err != nil {
		return false, err
	}
	var ok bool
	err = c.BusObject().Call("org.freedesktop.DBus.NameHasOwner", 0, nome).Store(&ok)
	return ok, err
}

// Proprieta reads a property.
func (b *Bus) Proprieta(nome, percorso, proprieta string) (any, error) {
	c, err := b.c()
	if err != nil {
		return nil, err
	}
	v, err := c.Object(nome, dbus.ObjectPath(percorso)).GetProperty(proprieta)
	if err != nil {
		return nil, err
	}
	return v.Value(), nil
}

// Chiama a method and put its results into «in».
func (b *Bus) Invoke(nome, percorso, metodo string, in []any, args ...any) error {
	c, err := b.c()
	if err != nil {
		return err
	}
	call := c.Object(nome, dbus.ObjectPath(percorso)).Call(metodo, 0, args...)
	if call.Err != nil {
		return call.Err
	}
	if len(in) > 0 {
		return call.Store(in...)
	}
	return nil
}

// StatoAttivo: ActiveState of a unit («inactive» if systemd has not loaded it).
func (b *Bus) StatoAttivo(unita string) (string, error) {
	var p dbus.ObjectPath
	if err := b.Invoke(sdName, sdPath, sdManager+".GetUnit", []any{&p}, unita); err != nil {
		if strings.Contains(err.Error(), "not loaded") || isName(err, "org.freedesktop.systemd1.NoSuchUnit") {
			return "inactive", nil
		}
		return "", err
	}
	v, err := b.Proprieta(sdName, string(p), "org.freedesktop.systemd1.Unit.ActiveState")
	if err != nil {
		return "", err
	}
	s, _ := v.(string)
	return s, nil
}

func isName(err error, nome string) bool {
	var e dbus.Error
	if errors.As(err, &e) {
		return e.Name == nome
	}
	var pe *dbus.Error
	if errors.As(err, &pe) {
		return pe.Name == nome
	}
	return false
}

// unitDBus: systemd1.Manager — GetUnitFileState, EnableUnitFiles, DisableUnitFiles, Reload
// (what systemctl enable/disable does, without launching it).
type unitDBus struct{ b *Bus }

func (u *unitDBus) Stato(unita string) (string, error) {
	var s string
	err := u.b.Invoke(sdName, sdPath, sdManager+".GetUnitFileState", []any{&s}, unita)
	if err != nil {
		if isName(err, "org.freedesktop.DBus.Error.FileNotFound") || isName(err, "org.freedesktop.systemd1.NoSuchUnit") ||
			strings.Contains(err.Error(), "No such file") {
			return "not-found", nil
		}
		return "", err
	}
	return s, nil
}

type changeUnit struct{ Tipo, File, Destinazione string }

func (u *unitDBus) Abilita(unita string) error {
	var info bool
	var cambi []changeUnit
	if err := u.b.Invoke(sdName, sdPath, sdManager+".EnableUnitFiles", []any{&info, &cambi}, []string{unita}, false, false); err != nil {
		return err
	}
	return u.b.Invoke(sdName, sdPath, sdManager+".Reload", nil)
}

func (u *unitDBus) Disabilita(unita string) error {
	var cambi []changeUnit
	if err := u.b.Invoke(sdName, sdPath, sdManager+".DisableUnitFiles", []any{&cambi}, []string{unita}, false); err != nil {
		return err
	}
	return u.b.Invoke(sdName, sdPath, sdManager+".Reload", nil)
}

// firewalldDBus: the live rules on org.fedoraproject.FirewallD1.zone, the permanent ones on the
// config zone (getZoneByName). What firewall-cmd [--permanent] --add-port does.
type firewalldDBus struct{ b *Bus }

func (f *firewalldDBus) Nome() string { return "firewalld" }

// Acceso: firewalld is on the bus and says RUNNING.
func (f *firewalldDBus) Lit() bool {
	if ok, err := f.b.HasOwner(fwName); err != nil || !ok {
		return false
	}
	v, err := f.b.Proprieta(fwName, fwPath, fwName+".state")
	s, _ := v.(string)
	return err == nil && s == "RUNNING"
}

func (f *firewalldDBus) DefaultZone() (string, error) {
	var z string
	err := f.b.Invoke(fwName, fwPath, fwName+".getDefaultZone", []any{&z})
	return z, err
}

func (f *firewalldDBus) zoneConfig(zona string) (string, error) {
	var p dbus.ObjectPath
	err := f.b.Invoke(fwName, fwPath+"/config", fwName+".config.getZoneByName", []any{&p}, zona)
	return string(p), err
}

func splitPort(porta string) (string, string) {
	p, proto, _ := strings.Cut(porta, "/")
	return p, proto
}

// serviceOf: «servizio:remotix» ⇒ «remotix»; a port ⇒ "".
func serviceOf(regola string) string {
	s, _ := strings.CutPrefix(regola, "service:")
	if s == regola {
		return ""
	}
	return s
}

// HasPort: is the rule (a port «7447/tcp», or a service «servizio:remotix») there, live or permanent?
func (f *firewalldDBus) HasPort(zona, porta string, permanente bool) (bool, error) {
	var ok bool
	s := serviceOf(porta)
	p, proto := splitPort(porta)
	if !permanente {
		if s != "" {
			err := f.b.Invoke(fwName, fwPath, fwName+".zone.queryService", []any{&ok}, zona, s)
			return ok, err
		}
		err := f.b.Invoke(fwName, fwPath, fwName+".zone.queryPort", []any{&ok}, zona, p, proto)
		return ok, err
	}
	zp, err := f.zoneConfig(zona)
	if err != nil {
		return false, err
	}
	if s != "" {
		err = f.b.Invoke(fwName, zp, fwName+".config.zone.queryService", []any{&ok}, s)
		return ok, err
	}
	err = f.b.Invoke(fwName, zp, fwName+".config.zone.queryPort", []any{&ok}, p, proto)
	return ok, err
}

func (f *firewalldDBus) Insert(zona, porta string, permanente bool) error {
	s := serviceOf(porta)
	p, proto := splitPort(porta)
	if !permanente {
		var z string
		if s != "" {
			return f.b.Invoke(fwName, fwPath, fwName+".zone.addService", []any{&z}, zona, s, int32(0))
		}
		return f.b.Invoke(fwName, fwPath, fwName+".zone.addPort", []any{&z}, zona, p, proto, int32(0))
	}
	return f.UpdatePermanent(zona, []string{porta}, nil)
}

func (f *firewalldDBus) Togli(zona, porta string, permanente bool) error {
	s := serviceOf(porta)
	p, proto := splitPort(porta)
	if !permanente {
		var z string
		if s != "" {
			return f.b.Invoke(fwName, fwPath, fwName+".zone.removeService", []any{&z}, zona, s)
		}
		return f.b.Invoke(fwName, fwPath, fwName+".zone.removePort", []any{&z}, zona, p, proto)
	}
	return f.UpdatePermanent(zona, nil, []string{porta})
}

// Conosce: firewalld knows the service both in the live rules and in the permanent ones. `[M]` T6:
// a new file in /usr/lib/firewalld/services is seen by neither of the two until the reload.
func (f *firewalldDBus) Conosce(servizio string) (bool, error) {
	var vive, perm []string
	if err := f.b.Invoke(fwName, fwPath, fwName+".listServices", []any{&vive}); err != nil {
		return false, err
	}
	if err := f.b.Invoke(fwName, fwPath+"/config", fwName+".config.getServiceNames", []any{&perm}); err != nil {
		return false, err
	}
	return slices.Contains(vive, servizio) && slices.Contains(perm, servizio), nil
}

type portFw struct{ Porta, Proto string }

// impostazioni: the zone's permanent ports and services (getSettings2), and the rest as text
// in order, for the fingerprint.
func (f *firewalldDBus) impostazioni(zp string) (map[string]dbus.Variant, error) {
	var m map[string]dbus.Variant
	err := f.b.Invoke(fwName, zp, fwName+".config.zone.getSettings2", []any{&m})
	return m, err
}

func permanentPorts(m map[string]dbus.Variant) []portFw {
	var r []portFw
	if v, ok := m["ports"]; ok {
		if l, ok := v.Value().([][]any); ok {
			for _, x := range l {
				if len(x) == 2 {
					a, _ := x[0].(string)
					b, _ := x[1].(string)
					r = append(r, portFw{a, b})
				}
			}
		}
	}
	return r
}

func permanentServices(m map[string]dbus.Variant) []string {
	if v, ok := m["services"]; ok {
		if l, ok := v.Value().([]string); ok {
			return l
		}
	}
	return nil
}

// removeRules: the ports and services without the given rules.
func removeRules(porte []portFw, servizi []string, via []string) ([]portFw, []string) {
	fuori := map[string]bool{}
	for _, r := range via {
		fuori[r] = true
	}
	var p2 []portFw
	for _, p := range porte {
		if !fuori[p.Porta+"/"+p.Proto] {
			p2 = append(p2, p)
		}
	}
	var s2 []string
	for _, s := range servizi {
		if !fuori["service:"+s] {
			s2 = append(s2, s)
		}
	}
	return p2, s2
}

// StatePermanent: the fingerprint of the zone's permanent settings (minus «senza»), in an
// order that does not depend on firewalld; and whether the zone is the stock one (the property «default»:
// `[M]` false for public.xml in /etc/firewalld/zones, true for work.xml in /usr/lib).
func (f *firewalldDBus) StatePermanent(zona string, senza []string) (string, bool, error) {
	zp, err := f.zoneConfig(zona)
	if err != nil {
		return "", false, err
	}
	m, err := f.impostazioni(zp)
	if err != nil {
		return "", false, err
	}
	porte, servizi := removeRules(permanentPorts(m), permanentServices(m), senza)
	var righe []string
	for k, v := range m {
		if k != "ports" && k != "services" {
			righe = append(righe, k+"="+v.String())
		}
	}
	for _, p := range porte {
		righe = append(righe, "port="+p.Porta+"/"+p.Proto)
	}
	for _, s := range servizi {
		righe = append(righe, "service="+s)
	}
	sort.Strings(righe)
	h := sha256.Sum256([]byte(strings.Join(righe, "\n")))
	v, err := f.b.Proprieta(fwName, zp, fwName+".config.zone.default")
	if err != nil {
		return "", false, err
	}
	diSerie, _ := v.(bool)
	return hex.EncodeToString(h[:]), diSerie, nil
}

// UpdatePermanent: the permanent rules added and removed in ONE write (update2 with only the
// keys «ports» and «services»: firewalld keeps the others as they were). ⚠ One write per rule makes
// <zona>.xml.old appear (firewalld copies the file that was there before rewriting it).
func (f *firewalldDBus) UpdatePermanent(zona string, aggiungi, togli []string) error {
	zp, err := f.zoneConfig(zona)
	if err != nil {
		return err
	}
	m, err := f.impostazioni(zp)
	if err != nil {
		return err
	}
	porte, servizi := removeRules(permanentPorts(m), permanentServices(m), togli)
	for _, r := range aggiungi {
		if s := serviceOf(r); s != "" {
			if !slices.Contains(servizi, s) {
				servizi = append(servizi, s)
			}
			continue
		}
		p, proto := splitPort(r)
		if !slices.Contains(porte, portFw{p, proto}) {
			porte = append(porte, portFw{p, proto})
		}
	}
	if porte == nil {
		porte = []portFw{}
	}
	if servizi == nil {
		servizi = []string{}
	}
	nuove := map[string]dbus.Variant{"ports": dbus.MakeVariant(porte), "services": dbus.MakeVariant(servizi)}
	return f.b.Invoke(fwName, zp, fwName+".config.zone.update2", nil, nuove)
}

// ResetToDefaults: the zone goes back to the one in /usr/lib/firewalld/zones (loadDefaults: the file in /etc
// goes away).
func (f *firewalldDBus) ResetToDefaults(zona string) error {
	zp, err := f.zoneConfig(zona)
	if err != nil {
		return err
	}
	return f.b.Invoke(fwName, zp, fwName+".config.zone.loadDefaults", nil)
}

// LivePorts: the ports (ranges too) open in the zone, to see Fedora Workstation's range 1025-65535,
// which queryPort does not see.
func (f *firewalldDBus) LivePorts(zona string) ([][]string, error) {
	var r [][]string
	err := f.b.Invoke(fwName, fwPath, fwName+".zone.getPorts", []any{&r}, zona)
	return r, err
}

// RestartIfActive: TryRestartUnit (what systemctl try-restart does): restarts the unit only if
// it was running. The desktops survive the service restart (§5.2, T2).
func (b *Bus) RestartIfActive(unita string) error {
	var job dbus.ObjectPath
	return b.Invoke(sdName, sdPath, sdManager+".TryRestartUnit", []any{&job}, unita, "replace")
}

func (u *unitDBus) Attiva(unita string) (string, error) { return u.b.StatoAttivo(unita) }

func (u *unitDBus) job(metodo, unita string) error {
	var job dbus.ObjectPath
	return u.b.Invoke(sdName, sdPath, sdManager+"."+metodo, []any{&job}, unita, "replace")
}

// Avvia: StartUnit, and waits for the unit to become active (or fail), up to 60 s.
func (u *unitDBus) Launch(unita string) error {
	if err := u.job("StartUnit", unita); err != nil {
		return err
	}
	return u.aspetta(unita, "active")
}

func (u *unitDBus) Ferma(unita string) error {
	if err := u.job("StopUnit", unita); err != nil {
		return err
	}
	return u.aspetta(unita, "inactive")
}

func (u *unitDBus) aspetta(unita, voluto string) error {
	for i := 0; i < 120; i++ {
		s, err := u.b.StatoAttivo(unita)
		if err != nil {
			return err
		}
		if s == voluto || (voluto == "inactive" && s == "failed") {
			return nil
		}
		if voluto == "active" && s == "failed" {
			return errors.New(unita + ": failed")
		}
		time.Sleep(500 * time.Millisecond)
	}
	return errors.New(unita + ": did not become " + voluto + " in 60 s")
}

func (u *unitDBus) Ricarica(unita string) error { return u.job("ReloadUnit", unita) }

func (u *unitDBus) Predefinito() (string, error) {
	var s string
	err := u.b.Invoke(sdName, sdPath, sdManager+".GetDefaultTarget", []any{&s})
	return s, err
}

func (u *unitDBus) SetDefault(b string) error {
	var cambi []changeUnit
	return u.b.Invoke(sdName, sdPath, sdManager+".SetDefaultTarget", []any{&cambi}, b, true)
}

// sessionsDBus: logind. List = ListSessions + the Service property of each one.
type sessionsDBus struct {
	b *Bus
	a *Ambiente
}

func (s *sessionsDBus) Charts(utente string) (int, error) {
	uid, err := uidDi(s.a, utente)
	if err != nil {
		return 0, err
	}
	return len(GraphicalProcesses(s.a, uid)), nil
}

func (s *sessionsDBus) CloseGraphical(utente string) ([]string, error) {
	return CloseGraphicalUser(s.a, utente)
}

type sessionLogind struct {
	ID     string
	UID    uint32
	Utente string
	Posto  string
	Via    dbus.ObjectPath
}

func (s *sessionsDBus) Listing() ([]Sessione, error) {
	var l []sessionLogind
	if err := s.b.Invoke("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.ListSessions", []any{&l}); err != nil {
		return nil, err
	}
	var r []Sessione
	for _, x := range l {
		serv, _ := s.b.Proprieta("org.freedesktop.login1", string(x.Via), "org.freedesktop.login1.Session.Service")
		stato, _ := s.b.Proprieta("org.freedesktop.login1", string(x.Via), "org.freedesktop.login1.Session.State")
		tipo, _ := s.b.Proprieta("org.freedesktop.login1", string(x.Via), "org.freedesktop.login1.Session.Type")
		sv, _ := serv.(string)
		st, _ := stato.(string)
		tp, _ := tipo.(string)
		r = append(r, Sessione{ID: x.ID, Utente: x.Utente, Servizio: sv, Stato: st, Tipo: tp})
	}
	return r, nil
}

func (s *sessionsDBus) Segnale(id string, segnale int32) error {
	return s.b.Invoke("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.KillSession", nil, id, "all", segnale)
}

func (s *sessionsDBus) Terminate(id string) error {
	return s.b.Invoke("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.TerminateSession", nil, id)
}
