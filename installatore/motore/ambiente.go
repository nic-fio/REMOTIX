package motore

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

// The installer is ONE single program (DECISIONI §10.14): it talks to systemd, logind and firewalld
// from inside, via D-Bus (dbus.go); it launches ONLY the programs of this closed list — where a
// stable interface is missing: the package manager and gpasswd/usermod —, with the absolute path,
// and every call is recorded (in the operation's log, or in the profile for «verifica»: R41).
//
// ⚠ rpm, dpkg and dpkg-deb are in the list because they are the base of the managers (rpm's archive cannot
// be read without it; dpkg --audit and --configure -a are the remedy of §6.6.3). ffmpeg is NOT there
// (the coordinator's decision, 30 Sep): the test «the card encodes a frame» is done in 7a by the
// installed REMOTIX binary (`remotix --prova-codifica`, to be done in the product: §6.5-bis).
var programmiAmmessi = map[string][]string{
	"apt-get": {"/usr/bin/apt-get"},
	// apt-cache: the versions REMOTIX's repository offers (madison), for upgrading (T8)
	"apt-cache": {"/usr/bin/apt-cache"},
	"dnf":       {"/usr/bin/dnf", "/usr/bin/dnf5"},
	"zypper":    {"/usr/bin/zypper"},
	"pacman":    {"/usr/bin/pacman"},
	// pacman-key: pacman's keyring (the key of REMOTIX's repository, T8). It is the manager's official
	// tool: pacman has no interface for keys without it.
	"pacman-key": {"/usr/bin/pacman-key"},
	"rpm":        {"/usr/bin/rpm", "/bin/rpm"},
	"dpkg":       {"/usr/bin/dpkg"},
	"dpkg-deb":   {"/usr/bin/dpkg-deb"},
	"remotix":    {"/usr/libexec/remotix/remotix", "/usr/lib/remotix/remotix"}, // Arch: /usr/lib (PKGBUILD)
	"gpasswd":    {"/usr/bin/gpasswd", "/usr/sbin/gpasswd", "/bin/gpasswd", "/sbin/gpasswd"},
	"usermod":    {"/usr/sbin/usermod", "/usr/bin/usermod", "/sbin/usermod"},
	// ufw: REMOTIX's port in Ubuntu's firewall (T6). ufw has no D-Bus: its program is
	// the only interface (the same argument as pacman-key).
	"ufw": {"/usr/sbin/ufw", "/sbin/ufw"},
}

// ErrNonAmmesso: the engine launches no programs outside the list.
var ErrNonAmmesso = errors.New("program outside the engine's closed list (DECISIONS §10.14)")

// ProgrammiAmmessi: the list, for the tests and for the manual.
func ProgrammiAmmessi() []string {
	var r []string
	for n := range programmiAmmessi {
		r = append(r, n)
	}
	sort.Strings(r)
	return r
}

// Esecutore launches a program of the list and returns its output, its exit code and an
// error only if it could not be launched (exec.ErrNotFound: it is not there — the case that makes a fact
// SCONOSCIUTO, §6.6.7; ErrNonAmmesso: outside the list).
type Esecutore func(tempo time.Duration, nome string, argomenti ...string) (uscita string, codice int, err error)

// percorsoAmmesso: the absolute path of a program of the list, if it is there.
func percorsoAmmesso(nome string) (string, error) {
	cand, ok := programmiAmmessi[nome]
	if !ok {
		return "", ErrNonAmmesso
	}
	for _, p := range cand {
		if st, err := os.Stat(p); err == nil && st.Mode().IsRegular() && st.Mode()&0o111 != 0 {
			return p, nil
		}
	}
	return "", exec.ErrNotFound
}

// eseguiDavvero: absolute path, fixed arguments, minimal environment in the C locale, no
// input, maximum time; and the record (R41).
func (a *Ambiente) eseguiDavvero(tempo time.Duration, nome string, argomenti ...string) (string, int, error) {
	percorso, err := percorsoAmmesso(nome)
	if err != nil {
		a.annota(nome, argomenti, -1, err)
		return "", -1, err
	}
	ctx, annulla := context.WithTimeout(context.Background(), tempo)
	defer annulla()
	cmd := exec.CommandContext(ctx, percorso, argomenti...)
	// ZYPP_LOCK_TIMEOUT: zypper waits for whoever holds it, like apt with DPkg::Lock::Timeout (occupato.go)
	cmd.Env = []string{"LC_ALL=C", "PATH=/usr/sbin:/usr/bin:/sbin:/bin", "DEBIAN_FRONTEND=noninteractive",
		"ZYPP_LOCK_TIMEOUT=" + strconv.Itoa(int(TettoOccupato.Seconds()))}
	var uscita strings.Builder
	cmd.Stdout = &uscita
	cmd.Stderr = &uscita
	err = cmd.Run()
	codice := 0
	var ee *exec.ExitError
	switch {
	case ctx.Err() == context.DeadlineExceeded:
		codice, err = -1, ctx.Err()
	case errors.As(err, &ee):
		codice, err = ee.ExitCode(), nil
	case err != nil:
		codice = -1
	}
	a.annota(percorso, argomenti, codice, err)
	return uscita.String(), codice, err
}

func (a *Ambiente) annota(percorso string, argomenti []string, codice int, err error) {
	if a.Annota == nil {
		return
	}
	r := percorso + " " + strings.Join(argomenti, " ") + " ⇒ " + strconv.Itoa(codice)
	if err != nil {
		r += " (" + err.Error() + ")"
	}
	a.Annota(r)
}

// GestoreGruppi reads and changes group membership.
type GestoreGruppi interface {
	// Membri: the group's explicit members, and whether the group exists.
	Membri(gruppo string) (membri []string, gid string, esiste bool, err error)
	// GruppoPrimario: the gid of the user's primary group, and whether the user exists.
	GruppoPrimario(utente string) (gid string, esiste bool, err error)
	Aggiungi(utente, gruppo string) error
	Togli(utente, gruppo string) error
}

// GestoreUnita enables, disables, starts and stops systemd units (over D-Bus).
type GestoreUnita interface {
	// Stato: the state of the unit file (enabled, disabled, static, masked, not-found…), what
	// systemctl is-enabled calls by the same name.
	Stato(unita string) (string, error)
	Abilita(unita string) error
	Disabilita(unita string) error
	// Attiva: ActiveState (active, inactive, failed…).
	Attiva(unita string) (string, error)
	Avvia(unita string) error
	Ferma(unita string) error
	Ricarica(unita string) error
	// the boot target (graphical.target / multi-user.target)
	Predefinito() (string, error)
	ImpostaPredefinito(bersaglio string) error
}

// Sessione: a logind session.
type Sessione struct {
	ID, Utente, Servizio, Stato, Tipo string
}

// GestoreSessioni: logind, over D-Bus.
type GestoreSessioni interface {
	Elenco() ([]Sessione, error)
	Termina(id string) error
	// Segnale to the processes of ONE session (logind KillSession, who=all): it stays inside the session.
	Segnale(id string, segnale int32) error
	// Grafici: how many desktop processes the person has in their user manager.
	Grafici(utente string) (int, error)
	// ChiudiGrafica: stops the desktop's units in the user manager (grafica_utente.go).
	ChiudiGrafica(utente string) ([]string, error)
}

// GestoreFirewall opens and closes a port. Today only firewalld (§6.6.4, T4's mandate).
type GestoreFirewall interface {
	Nome() string // "firewalld", "ufw", "nftables", "none"
	ZonaPredefinita() (string, error)
	HaPorta(zona, porta string, permanente bool) (bool, error) // porta = "7447/tcp"
	Aggiungi(zona, porta string, permanente bool) error
	Togli(zona, porta string, permanente bool) error
}

// Ambiente is everything the engine touches or reads of the machine. The tests build a fake one
// under a folder; the engine does not know the difference.
type Ambiente struct {
	Radice    string // "/" on the real machine; for reading /etc, /sys, /proc, /usr, /var/lib
	Esegui    Esecutore
	Bus       *Bus // system D-Bus (nil in the tests)
	Famiglia  string
	Gruppi    GestoreGruppi
	Unita     GestoreUnita
	Firewall  GestoreFirewall
	Pacchetti Gestore
	Sessioni  GestoreSessioni
	Annota    func(riga string) // every program launched (R41); nil = nobody listens
	Avvisa    func(m Messaggio) // what the engine says while it waits (occupato.go); nil = nobody listens
}

func (a *Ambiente) avvisa(m Messaggio) {
	if a.Avvisa != nil {
		a.Avvisa(m)
	}
}

// P is a machine path seen from the environment's root.
func (a *Ambiente) P(percorso string) string {
	if a.Radice == "" || a.Radice == "/" {
		return percorso
	}
	return filepath.Join(a.Radice, percorso)
}

// AmbienteVero is the machine the engine runs on.
func AmbienteVero() *Ambiente {
	a := &Ambiente{Radice: "/", Bus: &Bus{}}
	a.Esegui = a.eseguiDavvero
	a.Gruppi = &gruppiVeri{a}
	a.Unita = &unitaDBus{a.Bus}
	a.Firewall = scegliFirewall(a)
	a.Sessioni = &sessioniDBus{a.Bus, a}
	if m, _ := OsRelease(a); m != nil {
		a.Famiglia = Famiglia(m["ID"], m["ID_LIKE"])
	}
	a.Pacchetti = ScegliGestore(a, a.Famiglia)
	return a
}

// LeggiGruppi reads a file in the /etc/group format: name → (gid, members).
func LeggiGruppi(percorso string) (map[string][2]string, error) {
	f, err := os.Open(percorso)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := map[string][2]string{}
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) < 4 || strings.HasPrefix(c[0], "#") {
			continue
		}
		r[c[0]] = [2]string{c[2], c[3]}
	}
	return r, s.Err()
}

// DividiMembri: "a,b,,c" → [a b c], sorted.
func DividiMembri(s string) []string {
	var m []string
	for _, x := range strings.Split(s, ",") {
		if x = strings.TrimSpace(x); x != "" {
			m = append(m, x)
		}
	}
	sort.Strings(m)
	return m
}

// LeggiUtente looks up a user in a file in the /etc/passwd format and gives their gid.
func LeggiUtente(percorso, utente string) (gid string, esiste bool, err error) {
	f, err := os.Open(percorso)
	if err != nil {
		return "", false, err
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) >= 4 && c[0] == utente {
			return c[3], true, nil
		}
	}
	return "", false, s.Err()
}

// gruppiVeri: /etc/group is read, changed with gpasswd (which also keeps gshadow and the lock
// of the account files: there is no stable D-Bus interface for local groups). Only local
// groups: they are the ones REMOTIX touches (§6.4).
type gruppiVeri struct{ a *Ambiente }

func (g *gruppiVeri) Membri(gruppo string) ([]string, string, bool, error) {
	t, err := LeggiGruppi(g.a.P("/etc/group"))
	if err != nil {
		return nil, "", false, err
	}
	v, ok := t[gruppo]
	return DividiMembri(v[1]), v[0], ok, nil
}

func (g *gruppiVeri) GruppoPrimario(utente string) (string, bool, error) {
	return LeggiUtente(g.a.P("/etc/passwd"), utente)
}

func (g *gruppiVeri) Aggiungi(utente, gruppo string) error {
	return eseguiOErrore(g.a, "gpasswd", "-a", utente, gruppo)
}

func (g *gruppiVeri) Togli(utente, gruppo string) error {
	return eseguiOErrore(g.a, "gpasswd", "-d", utente, gruppo)
}

// firewallNonFatto: nftables is recognised, but the engine cannot change it yet (T4's
// mandate): every change returns RX-FW-004, and the plan declares it beforehand. (ufw can, since T6.)
type firewallNonFatto struct{ nome string }

func (f *firewallNonFatto) Nome() string                     { return f.nome }
func (f *firewallNonFatto) ZonaPredefinita() (string, error) { return "", nil }
func (f *firewallNonFatto) HaPorta(string, string, bool) (bool, error) {
	return false, Errore("RX-FW-004", f.nome)
}
func (f *firewallNonFatto) Aggiungi(string, string, bool) error { return Errore("RX-FW-004", f.nome) }
func (f *firewallNonFatto) Togli(string, string, bool) error    { return Errore("RX-FW-004", f.nome) }

// firewallUfw: ufw running (T6). With its program (closed list); a single level — ufw's rules
// are live and permanent together: «live» reads as «permanent» and does not change by itself.
// The rule: the application profile «REMOTIX» (the .deb package puts it in
// /etc/ufw/applications.d/remotix) if it is there and the port is its own, otherwise the port.
type firewallUfw struct{ a *Ambiente }

func (f *firewallUfw) Nome() string                     { return "ufw" }
func (f *firewallUfw) ZonaPredefinita() (string, error) { return "", nil }

// Conosce: the service profile is there (the file name is the service's).
func (f *firewallUfw) Conosce(servizio string) (bool, error) {
	_, err := os.Stat(f.a.P("/etc/ufw/applications.d/" + servizio))
	return err == nil, nil
}

// ufwRegola: «servizio:remotix» ⇒ «REMOTIX» (the profile name); «7447/tcp» stays as it is.
func ufwRegola(porta string) string {
	if s := servizioDi(porta); s != "" {
		return strings.ToUpper(s)
	}
	return porta
}

// HaPorta: the rule is among those added (`ufw show added`, which answers even with ufw off).
func (f *firewallUfw) HaPorta(_, porta string, _ bool) (bool, error) {
	out, c, err := f.a.Esegui(time.Minute, "ufw", "show", "added")
	if err != nil {
		return false, err
	}
	if c != 0 {
		return false, fmt.Errorf("ufw show added: exit %d: %s", c, strings.TrimSpace(out))
	}
	voglio := "ufw allow " + ufwRegola(porta)
	for _, r := range strings.Split(out, "\n") {
		if strings.TrimSpace(r) == voglio {
			return true, nil
		}
	}
	return false, nil
}

func (f *firewallUfw) Aggiungi(_, porta string, permanente bool) error {
	if !permanente {
		return nil // a single level: the rule is put by the «permanent» step
	}
	return eseguiOErrore(f.a, "ufw", "allow", ufwRegola(porta))
}

func (f *firewallUfw) Togli(_, porta string, permanente bool) error {
	if !permanente {
		return nil
	}
	return eseguiOErrore(f.a, "ufw", "delete", "allow", ufwRegola(porta))
}

// scegliFirewall: the running one. firewalld answers on the bus; ufw says it is on in its file;
// nftables as an active unit.
func scegliFirewall(a *Ambiente) GestoreFirewall {
	if fw := (&firewalldDBus{a.Bus}); fw.Acceso() {
		return fw
	}
	if b, err := os.ReadFile(a.P("/etc/ufw/ufw.conf")); err == nil && strings.Contains(string(b), "ENABLED=yes") {
		return &firewallUfw{a}
	}
	if s, err := a.Bus.StatoAttivo("nftables.service"); err == nil && s == "active" {
		return &firewallNonFatto{"nftables"}
	}
	return &firewallNonFatto{"none"}
}

func eseguiOErrore(a *Ambiente, nome string, argomenti ...string) error {
	out, c, err := a.Esegui(2*time.Minute, nome, argomenti...)
	if err != nil {
		return err
	}
	if c != 0 {
		return errors.New(nome + " " + strings.Join(argomenti, " ") + ": exit " + strconv.Itoa(c) + ": " + strings.TrimSpace(out))
	}
	return nil
}
