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
	sdNome     = "org.freedesktop.systemd1"
	sdPercorso = "/org/freedesktop/systemd1"
	sdManager  = "org.freedesktop.systemd1.Manager"
	fwNome     = "org.fedoraproject.FirewallD1"
	fwPercorso = "/org/fedoraproject/FirewallD1"
)

// HaPadrone: does someone answer to that name on the bus?
func (b *Bus) HaPadrone(nome string) (bool, error) {
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
func (b *Bus) Chiama(nome, percorso, metodo string, in []any, args ...any) error {
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
	if err := b.Chiama(sdNome, sdPercorso, sdManager+".GetUnit", []any{&p}, unita); err != nil {
		if strings.Contains(err.Error(), "not loaded") || isNome(err, "org.freedesktop.systemd1.NoSuchUnit") {
			return "inactive", nil
		}
		return "", err
	}
	v, err := b.Proprieta(sdNome, string(p), "org.freedesktop.systemd1.Unit.ActiveState")
	if err != nil {
		return "", err
	}
	s, _ := v.(string)
	return s, nil
}

func isNome(err error, nome string) bool {
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

// unitaDBus: systemd1.Manager — GetUnitFileState, EnableUnitFiles, DisableUnitFiles, Reload
// (what systemctl enable/disable does, without launching it).
type unitaDBus struct{ b *Bus }

func (u *unitaDBus) Stato(unita string) (string, error) {
	var s string
	err := u.b.Chiama(sdNome, sdPercorso, sdManager+".GetUnitFileState", []any{&s}, unita)
	if err != nil {
		if isNome(err, "org.freedesktop.DBus.Error.FileNotFound") || isNome(err, "org.freedesktop.systemd1.NoSuchUnit") ||
			strings.Contains(err.Error(), "No such file") {
			return "not-found", nil
		}
		return "", err
	}
	return s, nil
}

type cambioUnita struct{ Tipo, File, Destinazione string }

func (u *unitaDBus) Abilita(unita string) error {
	var info bool
	var cambi []cambioUnita
	if err := u.b.Chiama(sdNome, sdPercorso, sdManager+".EnableUnitFiles", []any{&info, &cambi}, []string{unita}, false, false); err != nil {
		return err
	}
	return u.b.Chiama(sdNome, sdPercorso, sdManager+".Reload", nil)
}

func (u *unitaDBus) Disabilita(unita string) error {
	var cambi []cambioUnita
	if err := u.b.Chiama(sdNome, sdPercorso, sdManager+".DisableUnitFiles", []any{&cambi}, []string{unita}, false); err != nil {
		return err
	}
	return u.b.Chiama(sdNome, sdPercorso, sdManager+".Reload", nil)
}

// firewalldDBus: the live rules on org.fedoraproject.FirewallD1.zone, the permanent ones on the
// config zone (getZoneByName). What firewall-cmd [--permanent] --add-port does.
type firewalldDBus struct{ b *Bus }

func (f *firewalldDBus) Nome() string { return "firewalld" }

// Acceso: firewalld is on the bus and says RUNNING.
func (f *firewalldDBus) Acceso() bool {
	if ok, err := f.b.HaPadrone(fwNome); err != nil || !ok {
		return false
	}
	v, err := f.b.Proprieta(fwNome, fwPercorso, fwNome+".state")
	s, _ := v.(string)
	return err == nil && s == "RUNNING"
}

func (f *firewalldDBus) ZonaPredefinita() (string, error) {
	var z string
	err := f.b.Chiama(fwNome, fwPercorso, fwNome+".getDefaultZone", []any{&z})
	return z, err
}

func (f *firewalldDBus) zonaConfig(zona string) (string, error) {
	var p dbus.ObjectPath
	err := f.b.Chiama(fwNome, fwPercorso+"/config", fwNome+".config.getZoneByName", []any{&p}, zona)
	return string(p), err
}

func dividiPorta(porta string) (string, string) {
	p, proto, _ := strings.Cut(porta, "/")
	return p, proto
}

// servizioDi: «servizio:remotix» ⇒ «remotix»; a port ⇒ "".
func servizioDi(regola string) string {
	s, _ := strings.CutPrefix(regola, "service:")
	if s == regola {
		return ""
	}
	return s
}

// HaPorta: is the rule (a port «7447/tcp», or a service «servizio:remotix») there, live or permanent?
func (f *firewalldDBus) HaPorta(zona, porta string, permanente bool) (bool, error) {
	var ok bool
	s := servizioDi(porta)
	p, proto := dividiPorta(porta)
	if !permanente {
		if s != "" {
			err := f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.queryService", []any{&ok}, zona, s)
			return ok, err
		}
		err := f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.queryPort", []any{&ok}, zona, p, proto)
		return ok, err
	}
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return false, err
	}
	if s != "" {
		err = f.b.Chiama(fwNome, zp, fwNome+".config.zone.queryService", []any{&ok}, s)
		return ok, err
	}
	err = f.b.Chiama(fwNome, zp, fwNome+".config.zone.queryPort", []any{&ok}, p, proto)
	return ok, err
}

func (f *firewalldDBus) Aggiungi(zona, porta string, permanente bool) error {
	s := servizioDi(porta)
	p, proto := dividiPorta(porta)
	if !permanente {
		var z string
		if s != "" {
			return f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.addService", []any{&z}, zona, s, int32(0))
		}
		return f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.addPort", []any{&z}, zona, p, proto, int32(0))
	}
	return f.AggiornaPermanente(zona, []string{porta}, nil)
}

func (f *firewalldDBus) Togli(zona, porta string, permanente bool) error {
	s := servizioDi(porta)
	p, proto := dividiPorta(porta)
	if !permanente {
		var z string
		if s != "" {
			return f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.removeService", []any{&z}, zona, s)
		}
		return f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.removePort", []any{&z}, zona, p, proto)
	}
	return f.AggiornaPermanente(zona, nil, []string{porta})
}

// Conosce: firewalld knows the service both in the live rules and in the permanent ones. `[M]` T6:
// a new file in /usr/lib/firewalld/services is seen by neither of the two until the reload.
func (f *firewalldDBus) Conosce(servizio string) (bool, error) {
	var vive, perm []string
	if err := f.b.Chiama(fwNome, fwPercorso, fwNome+".listServices", []any{&vive}); err != nil {
		return false, err
	}
	if err := f.b.Chiama(fwNome, fwPercorso+"/config", fwNome+".config.getServiceNames", []any{&perm}); err != nil {
		return false, err
	}
	return slices.Contains(vive, servizio) && slices.Contains(perm, servizio), nil
}

type portaFw struct{ Porta, Proto string }

// impostazioni: the zone's permanent ports and services (getSettings2), and the rest as text
// in order, for the fingerprint.
func (f *firewalldDBus) impostazioni(zp string) (map[string]dbus.Variant, error) {
	var m map[string]dbus.Variant
	err := f.b.Chiama(fwNome, zp, fwNome+".config.zone.getSettings2", []any{&m})
	return m, err
}

func portePermanenti(m map[string]dbus.Variant) []portaFw {
	var r []portaFw
	if v, ok := m["ports"]; ok {
		if l, ok := v.Value().([][]any); ok {
			for _, x := range l {
				if len(x) == 2 {
					a, _ := x[0].(string)
					b, _ := x[1].(string)
					r = append(r, portaFw{a, b})
				}
			}
		}
	}
	return r
}

func serviziPermanenti(m map[string]dbus.Variant) []string {
	if v, ok := m["services"]; ok {
		if l, ok := v.Value().([]string); ok {
			return l
		}
	}
	return nil
}

// togliRegole: the ports and services without the given rules.
func togliRegole(porte []portaFw, servizi []string, via []string) ([]portaFw, []string) {
	fuori := map[string]bool{}
	for _, r := range via {
		fuori[r] = true
	}
	var p2 []portaFw
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

// StatoPermanente: the fingerprint of the zone's permanent settings (minus «senza»), in an
// order that does not depend on firewalld; and whether the zone is the stock one (the property «default»:
// `[M]` false for public.xml in /etc/firewalld/zones, true for work.xml in /usr/lib).
func (f *firewalldDBus) StatoPermanente(zona string, senza []string) (string, bool, error) {
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return "", false, err
	}
	m, err := f.impostazioni(zp)
	if err != nil {
		return "", false, err
	}
	porte, servizi := togliRegole(portePermanenti(m), serviziPermanenti(m), senza)
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
	v, err := f.b.Proprieta(fwNome, zp, fwNome+".config.zone.default")
	if err != nil {
		return "", false, err
	}
	diSerie, _ := v.(bool)
	return hex.EncodeToString(h[:]), diSerie, nil
}

// AggiornaPermanente: the permanent rules added and removed in ONE write (update2 with only the
// keys «ports» and «services»: firewalld keeps the others as they were). ⚠ One write per rule makes
// <zona>.xml.old appear (firewalld copies the file that was there before rewriting it).
func (f *firewalldDBus) AggiornaPermanente(zona string, aggiungi, togli []string) error {
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return err
	}
	m, err := f.impostazioni(zp)
	if err != nil {
		return err
	}
	porte, servizi := togliRegole(portePermanenti(m), serviziPermanenti(m), togli)
	for _, r := range aggiungi {
		if s := servizioDi(r); s != "" {
			if !slices.Contains(servizi, s) {
				servizi = append(servizi, s)
			}
			continue
		}
		p, proto := dividiPorta(r)
		if !slices.Contains(porte, portaFw{p, proto}) {
			porte = append(porte, portaFw{p, proto})
		}
	}
	if porte == nil {
		porte = []portaFw{}
	}
	if servizi == nil {
		servizi = []string{}
	}
	nuove := map[string]dbus.Variant{"ports": dbus.MakeVariant(porte), "services": dbus.MakeVariant(servizi)}
	return f.b.Chiama(fwNome, zp, fwNome+".config.zone.update2", nil, nuove)
}

// RimettiDiSerie: the zone goes back to the one in /usr/lib/firewalld/zones (loadDefaults: the file in /etc
// goes away).
func (f *firewalldDBus) RimettiDiSerie(zona string) error {
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return err
	}
	return f.b.Chiama(fwNome, zp, fwNome+".config.zone.loadDefaults", nil)
}

// PorteVive: the ports (ranges too) open in the zone, to see Fedora Workstation's range 1025-65535,
// which queryPort does not see.
func (f *firewalldDBus) PorteVive(zona string) ([][]string, error) {
	var r [][]string
	err := f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.getPorts", []any{&r}, zona)
	return r, err
}

// RiavviaSeAttiva: TryRestartUnit (what systemctl try-restart does): restarts the unit only if
// it was running. The desktops survive the service restart (§5.2, T2).
func (b *Bus) RiavviaSeAttiva(unita string) error {
	var job dbus.ObjectPath
	return b.Chiama(sdNome, sdPercorso, sdManager+".TryRestartUnit", []any{&job}, unita, "replace")
}

func (u *unitaDBus) Attiva(unita string) (string, error) { return u.b.StatoAttivo(unita) }

func (u *unitaDBus) job(metodo, unita string) error {
	var job dbus.ObjectPath
	return u.b.Chiama(sdNome, sdPercorso, sdManager+"."+metodo, []any{&job}, unita, "replace")
}

// Avvia: StartUnit, and waits for the unit to become active (or fail), up to 60 s.
func (u *unitaDBus) Avvia(unita string) error {
	if err := u.job("StartUnit", unita); err != nil {
		return err
	}
	return u.aspetta(unita, "active")
}

func (u *unitaDBus) Ferma(unita string) error {
	if err := u.job("StopUnit", unita); err != nil {
		return err
	}
	return u.aspetta(unita, "inactive")
}

func (u *unitaDBus) aspetta(unita, voluto string) error {
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

func (u *unitaDBus) Ricarica(unita string) error { return u.job("ReloadUnit", unita) }

func (u *unitaDBus) Predefinito() (string, error) {
	var s string
	err := u.b.Chiama(sdNome, sdPercorso, sdManager+".GetDefaultTarget", []any{&s})
	return s, err
}

func (u *unitaDBus) ImpostaPredefinito(b string) error {
	var cambi []cambioUnita
	return u.b.Chiama(sdNome, sdPercorso, sdManager+".SetDefaultTarget", []any{&cambi}, b, true)
}

// sessioniDBus: logind. List = ListSessions + the Service property of each one.
type sessioniDBus struct {
	b *Bus
	a *Ambiente
}

func (s *sessioniDBus) Grafici(utente string) (int, error) {
	uid, err := uidDi(s.a, utente)
	if err != nil {
		return 0, err
	}
	return len(ProcessiGrafici(s.a, uid)), nil
}

func (s *sessioniDBus) ChiudiGrafica(utente string) ([]string, error) {
	return ChiudiGraficaUtente(s.a, utente)
}

type sessioneLogind struct {
	ID     string
	UID    uint32
	Utente string
	Posto  string
	Via    dbus.ObjectPath
}

func (s *sessioniDBus) Elenco() ([]Sessione, error) {
	var l []sessioneLogind
	if err := s.b.Chiama("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.ListSessions", []any{&l}); err != nil {
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

func (s *sessioniDBus) Segnale(id string, segnale int32) error {
	return s.b.Chiama("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.KillSession", nil, id, "all", segnale)
}

func (s *sessioniDBus) Termina(id string) error {
	return s.b.Chiama("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.TerminateSession", nil, id)
}
