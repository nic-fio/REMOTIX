package motore

import (
	"errors"
	"strings"
	"sync"
	"time"

	"github.com/godbus/dbus/v5"
)

// Bus: il D-Bus di sistema, aperto alla prima richiesta. Con systemd, logind e firewalld il motore
// parla da qui, mai lanciando systemctl, loginctl, busctl o firewall-cmd (DECISIONI §10.14).
// Senza bus (un contenitore, una macchina non partita con systemd) ogni richiesta dà un errore, e
// chi chiede lo tratta come SCONOSCIUTO — mai come «a posto».
type Bus struct {
	una  sync.Once
	conn *dbus.Conn
	err  error
}

func (b *Bus) c() (*dbus.Conn, error) {
	if b == nil {
		return nil, errors.New("nessun D-Bus")
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

// HaPadrone: qualcuno risponde a quel nome sul bus?
func (b *Bus) HaPadrone(nome string) (bool, error) {
	c, err := b.c()
	if err != nil {
		return false, err
	}
	var ok bool
	err = c.BusObject().Call("org.freedesktop.DBus.NameHasOwner", 0, nome).Store(&ok)
	return ok, err
}

// Proprieta legge una proprietà.
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

// Chiama un metodo e ne mette i risultati in «in».
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

// StatoAttivo: ActiveState di un'unità («inactive» se systemd non la ha caricata).
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
// (quel che fa systemctl enable/disable, senza lanciarlo).
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

// firewalldDBus: le regole vive su org.fedoraproject.FirewallD1.zone, quelle permanenti sulla
// zona di config (getZoneByName). Quel che fa firewall-cmd [--permanent] --add-port.
type firewalldDBus struct{ b *Bus }

func (f *firewalldDBus) Nome() string { return "firewalld" }

// Acceso: firewalld è sul bus e dice RUNNING.
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

func (f *firewalldDBus) HaPorta(zona, porta string, permanente bool) (bool, error) {
	p, proto := dividiPorta(porta)
	var ok bool
	if !permanente {
		err := f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.queryPort", []any{&ok}, zona, p, proto)
		return ok, err
	}
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return false, err
	}
	err = f.b.Chiama(fwNome, zp, fwNome+".config.zone.queryPort", []any{&ok}, p, proto)
	return ok, err
}

func (f *firewalldDBus) Aggiungi(zona, porta string, permanente bool) error {
	p, proto := dividiPorta(porta)
	if !permanente {
		var z string
		return f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.addPort", []any{&z}, zona, p, proto, int32(0))
	}
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return err
	}
	return f.b.Chiama(fwNome, zp, fwNome+".config.zone.addPort", nil, p, proto)
}

func (f *firewalldDBus) Togli(zona, porta string, permanente bool) error {
	p, proto := dividiPorta(porta)
	if !permanente {
		var z string
		return f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.removePort", []any{&z}, zona, p, proto)
	}
	zp, err := f.zonaConfig(zona)
	if err != nil {
		return err
	}
	return f.b.Chiama(fwNome, zp, fwNome+".config.zone.removePort", nil, p, proto)
}

// PorteVive: le porte (anche intervalli) aperte nella zona, per vedere l'intervallo 1025-65535 di
// Fedora Workstation, che queryPort non vede.
func (f *firewalldDBus) PorteVive(zona string) ([][]string, error) {
	var r [][]string
	err := f.b.Chiama(fwNome, fwPercorso, fwNome+".zone.getPorts", []any{&r}, zona)
	return r, err
}

// RiavviaSeAttiva: TryRestartUnit (quel che fa systemctl try-restart): riaccende l'unità solo se
// era accesa. I desktop sopravvivono al riavvio del servizio (§5.2, T2).
func (b *Bus) RiavviaSeAttiva(unita string) error {
	var job dbus.ObjectPath
	return b.Chiama(sdNome, sdPercorso, sdManager+".TryRestartUnit", []any{&job}, unita, "replace")
}

func (u *unitaDBus) Attiva(unita string) (string, error) { return u.b.StatoAttivo(unita) }

func (u *unitaDBus) job(metodo, unita string) error {
	var job dbus.ObjectPath
	return u.b.Chiama(sdNome, sdPercorso, sdManager+"."+metodo, []any{&job}, unita, "replace")
}

// Avvia: StartUnit, e si aspetta che l'unità diventi attiva (o fallisca), fino a 60 s.
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
	return errors.New(unita + ": non è diventata " + voluto + " in 60 s")
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

// sessioniDBus: logind. Elenco = ListSessions + la proprietà Service di ognuna.
type sessioniDBus struct{ b *Bus }

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
		sv, _ := serv.(string)
		st, _ := stato.(string)
		r = append(r, Sessione{ID: x.ID, Utente: x.Utente, Servizio: sv, Stato: st})
	}
	return r, nil
}

func (s *sessioniDBus) Segnale(id string, segnale int32) error {
	return s.b.Chiama("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.KillSession", nil, id, "all", segnale)
}

func (s *sessioniDBus) Termina(id string) error {
	return s.b.Chiama("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.TerminateSession", nil, id)
}
