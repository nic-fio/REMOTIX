package engine

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
// the caller treats it as UNKNOWN — never as «all right».
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
func (b *Bus) HasOwner(name string) (bool, error) {
	c, err := b.c()
	if err != nil {
		return false, err
	}
	var ok bool
	err = c.BusObject().Call("org.freedesktop.DBus.NameHasOwner", 0, name).Store(&ok)
	return ok, err
}

// Property reads a property.
func (b *Bus) Property(name, fpath, property string) (any, error) {
	c, err := b.c()
	if err != nil {
		return nil, err
	}
	v, err := c.Object(name, dbus.ObjectPath(fpath)).GetProperty(property)
	if err != nil {
		return nil, err
	}
	return v.Value(), nil
}

// Chiama a method and put its results into «in».
func (b *Bus) Invoke(name, fpath, method string, in []any, args ...any) error {
	c, err := b.c()
	if err != nil {
		return err
	}
	call := c.Object(name, dbus.ObjectPath(fpath)).Call(method, 0, args...)
	if call.Err != nil {
		return call.Err
	}
	if len(in) > 0 {
		return call.Store(in...)
	}
	return nil
}

// ActiveState: ActiveState of a unit («inactive» if systemd has not loaded it).
func (b *Bus) ActiveState(unit string) (string, error) {
	var p dbus.ObjectPath
	if err := b.Invoke(sdName, sdPath, sdManager+".GetUnit", []any{&p}, unit); err != nil {
		if strings.Contains(err.Error(), "not loaded") || isName(err, "org.freedesktop.systemd1.NoSuchUnit") {
			return "inactive", nil
		}
		return "", err
	}
	v, err := b.Property(sdName, string(p), "org.freedesktop.systemd1.Unit.ActiveState")
	if err != nil {
		return "", err
	}
	s, _ := v.(string)
	return s, nil
}

func isName(err error, name string) bool {
	var e dbus.Error
	if errors.As(err, &e) {
		return e.Name == name
	}
	var pe *dbus.Error
	if errors.As(err, &pe) {
		return pe.Name == name
	}
	return false
}

// unitDBus: systemd1.Manager — GetUnitFileState, EnableUnitFiles, DisableUnitFiles, Reload
// (what systemctl enable/disable does, without launching it).
type unitDBus struct{ b *Bus }

func (u *unitDBus) State(unit string) (string, error) {
	var s string
	err := u.b.Invoke(sdName, sdPath, sdManager+".GetUnitFileState", []any{&s}, unit)
	if err != nil {
		if isName(err, "org.freedesktop.DBus.Error.FileNotFound") || isName(err, "org.freedesktop.systemd1.NoSuchUnit") ||
			strings.Contains(err.Error(), "No such file") {
			return "not-found", nil
		}
		return "", err
	}
	return s, nil
}

type changeUnit struct{ Type, File, Destination string }

func (u *unitDBus) Enable(unit string) error {
	var info bool
	var changes []changeUnit
	if err := u.b.Invoke(sdName, sdPath, sdManager+".EnableUnitFiles", []any{&info, &changes}, []string{unit}, false, false); err != nil {
		return err
	}
	return u.b.Invoke(sdName, sdPath, sdManager+".Reload", nil)
}

func (u *unitDBus) Disable(unit string) error {
	var changes []changeUnit
	if err := u.b.Invoke(sdName, sdPath, sdManager+".DisableUnitFiles", []any{&changes}, []string{unit}, false); err != nil {
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
	v, err := f.b.Property(fwName, fwPath, fwName+".state")
	s, _ := v.(string)
	return err == nil && s == "RUNNING"
}

func (f *firewalldDBus) DefaultZone() (string, error) {
	var z string
	err := f.b.Invoke(fwName, fwPath, fwName+".getDefaultZone", []any{&z})
	return z, err
}

func (f *firewalldDBus) zoneConfig(zone string) (string, error) {
	var p dbus.ObjectPath
	err := f.b.Invoke(fwName, fwPath+"/config", fwName+".config.getZoneByName", []any{&p}, zone)
	return string(p), err
}

func splitPort(port string) (string, string) {
	p, proto, _ := strings.Cut(port, "/")
	return p, proto
}

// serviceOf: «service:remotix» ⇒ «remotix»; a port ⇒ "".
func serviceOf(rule string) string {
	s, _ := strings.CutPrefix(rule, "service:")
	if s == rule {
		return ""
	}
	return s
}

// HasPort: is the rule (a port «7447/tcp», or a service «service:remotix») there, live or permanent?
func (f *firewalldDBus) HasPort(zone, port string, permanent bool) (bool, error) {
	var ok bool
	s := serviceOf(port)
	p, proto := splitPort(port)
	if !permanent {
		if s != "" {
			err := f.b.Invoke(fwName, fwPath, fwName+".zone.queryService", []any{&ok}, zone, s)
			return ok, err
		}
		err := f.b.Invoke(fwName, fwPath, fwName+".zone.queryPort", []any{&ok}, zone, p, proto)
		return ok, err
	}
	zp, err := f.zoneConfig(zone)
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

func (f *firewalldDBus) Insert(zone, port string, permanent bool) error {
	s := serviceOf(port)
	p, proto := splitPort(port)
	if !permanent {
		var z string
		if s != "" {
			return f.b.Invoke(fwName, fwPath, fwName+".zone.addService", []any{&z}, zone, s, int32(0))
		}
		return f.b.Invoke(fwName, fwPath, fwName+".zone.addPort", []any{&z}, zone, p, proto, int32(0))
	}
	return f.UpdatePermanent(zone, []string{port}, nil)
}

func (f *firewalldDBus) Remove(zone, port string, permanent bool) error {
	s := serviceOf(port)
	p, proto := splitPort(port)
	if !permanent {
		var z string
		if s != "" {
			return f.b.Invoke(fwName, fwPath, fwName+".zone.removeService", []any{&z}, zone, s)
		}
		return f.b.Invoke(fwName, fwPath, fwName+".zone.removePort", []any{&z}, zone, p, proto)
	}
	return f.UpdatePermanent(zone, nil, []string{port})
}

// Knows: firewalld knows the service both in the live rules and in the permanent ones. `[M]` T6:
// a new file in /usr/lib/firewalld/services is seen by neither of the two until the reload.
func (f *firewalldDBus) Knows(service string) (bool, error) {
	var vive, perm []string
	if err := f.b.Invoke(fwName, fwPath, fwName+".listServices", []any{&vive}); err != nil {
		return false, err
	}
	if err := f.b.Invoke(fwName, fwPath+"/config", fwName+".config.getServiceNames", []any{&perm}); err != nil {
		return false, err
	}
	return slices.Contains(vive, service) && slices.Contains(perm, service), nil
}

type portFw struct{ Porta, Proto string }

// settings: the zone's permanent ports and services (getSettings2), and the rest as text
// in order, for the fingerprint.
func (f *firewalldDBus) settings(zp string) (map[string]dbus.Variant, error) {
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
func removeRules(ports []portFw, services []string, via []string) ([]portFw, []string) {
	report := map[string]bool{}
	for _, r := range via {
		report[r] = true
	}
	var p2 []portFw
	for _, p := range ports {
		if !report[p.Porta+"/"+p.Proto] {
			p2 = append(p2, p)
		}
	}
	var s2 []string
	for _, s := range services {
		if !report["service:"+s] {
			s2 = append(s2, s)
		}
	}
	return p2, s2
}

// StatePermanent: the fingerprint of the zone's permanent settings (minus «without»), in an
// order that does not depend on firewalld; and whether the zone is the stock one (the property «default»:
// `[M]` false for public.xml in /etc/firewalld/zones, true for work.xml in /usr/lib).
func (f *firewalldDBus) StatePermanent(zone string, without []string) (string, bool, error) {
	zp, err := f.zoneConfig(zone)
	if err != nil {
		return "", false, err
	}
	m, err := f.settings(zp)
	if err != nil {
		return "", false, err
	}
	ports, services := removeRules(permanentPorts(m), permanentServices(m), without)
	var lines []string
	for k, v := range m {
		if k != "ports" && k != "services" {
			lines = append(lines, k+"="+v.String())
		}
	}
	for _, p := range ports {
		lines = append(lines, "port="+p.Porta+"/"+p.Proto)
	}
	for _, s := range services {
		lines = append(lines, "service="+s)
	}
	sort.Strings(lines)
	h := sha256.Sum256([]byte(strings.Join(lines, "\n")))
	v, err := f.b.Property(fwName, zp, fwName+".config.zone.default")
	if err != nil {
		return "", false, err
	}
	stock, _ := v.(bool)
	return hex.EncodeToString(h[:]), stock, nil
}

// UpdatePermanent: the permanent rules added and removed in ONE write (update2 with only the
// keys «ports» and «services»: firewalld keeps the others as they were). ⚠ One write per rule makes
// <zone>.xml.old appear (firewalld copies the file that was there before rewriting it).
func (f *firewalldDBus) UpdatePermanent(zone string, add, remove []string) error {
	zp, err := f.zoneConfig(zone)
	if err != nil {
		return err
	}
	m, err := f.settings(zp)
	if err != nil {
		return err
	}
	ports, services := removeRules(permanentPorts(m), permanentServices(m), remove)
	for _, r := range add {
		if s := serviceOf(r); s != "" {
			if !slices.Contains(services, s) {
				services = append(services, s)
			}
			continue
		}
		p, proto := splitPort(r)
		if !slices.Contains(ports, portFw{p, proto}) {
			ports = append(ports, portFw{p, proto})
		}
	}
	if ports == nil {
		ports = []portFw{}
	}
	if services == nil {
		services = []string{}
	}
	new_ones := map[string]dbus.Variant{"ports": dbus.MakeVariant(ports), "services": dbus.MakeVariant(services)}
	return f.b.Invoke(fwName, zp, fwName+".config.zone.update2", nil, new_ones)
}

// ResetToDefaults: the zone goes back to the one in /usr/lib/firewalld/zones (loadDefaults: the file in /etc
// goes away).
func (f *firewalldDBus) ResetToDefaults(zone string) error {
	zp, err := f.zoneConfig(zone)
	if err != nil {
		return err
	}
	return f.b.Invoke(fwName, zp, fwName+".config.zone.loadDefaults", nil)
}

// LivePorts: the ports (ranges too) open in the zone, to see Fedora Workstation's range 1025-65535,
// which queryPort does not see.
func (f *firewalldDBus) LivePorts(zone string) ([][]string, error) {
	var r [][]string
	err := f.b.Invoke(fwName, fwPath, fwName+".zone.getPorts", []any{&r}, zone)
	return r, err
}

// RestartIfActive: TryRestartUnit (what systemctl try-restart does): restarts the unit only if
// it was running. The desktops survive the service restart (§5.2, T2).
func (b *Bus) RestartIfActive(unit string) error {
	var job dbus.ObjectPath
	return b.Invoke(sdName, sdPath, sdManager+".TryRestartUnit", []any{&job}, unit, "replace")
}

func (u *unitDBus) Active(unit string) (string, error) { return u.b.ActiveState(unit) }

func (u *unitDBus) job(method, unit string) error {
	var job dbus.ObjectPath
	return u.b.Invoke(sdName, sdPath, sdManager+"."+method, []any{&job}, unit, "replace")
}

// Avvia: StartUnit, and waits for the unit to become active (or fail), up to 60 s.
func (u *unitDBus) Launch(unit string) error {
	if err := u.job("StartUnit", unit); err != nil {
		return err
	}
	return u.wait_until(unit, "active")
}

func (u *unitDBus) Stop(unit string) error {
	if err := u.job("StopUnit", unit); err != nil {
		return err
	}
	return u.wait_until(unit, "inactive")
}

func (u *unitDBus) wait_until(unit, wanted string) error {
	for i := 0; i < 120; i++ {
		s, err := u.b.ActiveState(unit)
		if err != nil {
			return err
		}
		if s == wanted || (wanted == "inactive" && s == "failed") {
			return nil
		}
		if wanted == "active" && s == "failed" {
			return errors.New(unit + ": failed")
		}
		time.Sleep(500 * time.Millisecond)
	}
	return errors.New(unit + ": did not become " + wanted + " in 60 s")
}

func (u *unitDBus) Reload(unit string) error { return u.job("ReloadUnit", unit) }

func (u *unitDBus) Default() (string, error) {
	var s string
	err := u.b.Invoke(sdName, sdPath, sdManager+".GetDefaultTarget", []any{&s})
	return s, err
}

func (u *unitDBus) SetDefault(b string) error {
	var changes []changeUnit
	return u.b.Invoke(sdName, sdPath, sdManager+".SetDefaultTarget", []any{&changes}, b, true)
}

// sessionsDBus: logind. List = ListSessions + the Service property of each one.
type sessionsDBus struct {
	b *Bus
	a *Environment
}

func (s *sessionsDBus) Charts(user string) (int, error) {
	uid, err := uidDi(s.a, user)
	if err != nil {
		return 0, err
	}
	return len(GraphicalProcesses(s.a, uid)), nil
}

func (s *sessionsDBus) CloseGraphical(user string) ([]string, error) {
	return CloseGraphicalUser(s.a, user)
}

type sessionLogind struct {
	ID    string
	UID   uint32
	User  string
	Posto string
	Via   dbus.ObjectPath
}

func (s *sessionsDBus) Listing() ([]Session, error) {
	var l []sessionLogind
	if err := s.b.Invoke("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.ListSessions", []any{&l}); err != nil {
		return nil, err
	}
	var r []Session
	for _, x := range l {
		serv, _ := s.b.Property("org.freedesktop.login1", string(x.Via), "org.freedesktop.login1.Session.Service")
		state, _ := s.b.Property("org.freedesktop.login1", string(x.Via), "org.freedesktop.login1.Session.State")
		kind, _ := s.b.Property("org.freedesktop.login1", string(x.Via), "org.freedesktop.login1.Session.Type")
		sv, _ := serv.(string)
		st, _ := state.(string)
		tp, _ := kind.(string)
		r = append(r, Session{ID: x.ID, User: x.User, Service: sv, State: st, Type: tp})
	}
	return r, nil
}

func (s *sessionsDBus) Signal(id string, send_signal int32) error {
	return s.b.Invoke("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.KillSession", nil, id, "all", send_signal)
}

func (s *sessionsDBus) Terminate(id string) error {
	return s.b.Invoke("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.TerminateSession", nil, id)
}
