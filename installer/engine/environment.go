package engine

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
// and every call is recorded (in the operation's log, or in the profile for «verify»: R41).
//
// ⚠ rpm, dpkg and dpkg-deb are in the list because they are the base of the managers (rpm's archive cannot
// be read without it; dpkg --audit and --configure -a are the remedy of §6.6.3). ffmpeg is NOT there
// (the coordinator's decision, 30 Sep): the test «the card encodes a frame» is done in 7a by the
// installed REMOTIX binary (`remotix --encoding-test`, to be done in the product: §6.5-bis).
var allowedPrograms = map[string][]string{
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

// ErrNotAllowed: the engine launches no programs outside the list.
var ErrNotAllowed = errors.New("program outside the engine's closed list (DECISIONS §10.14)")

// AllowedPrograms: the list, for the tests and for the manual.
func AllowedPrograms() []string {
	var r []string
	for n := range allowedPrograms {
		r = append(r, n)
	}
	sort.Strings(r)
	return r
}

// Esecutore launches a program of the list and returns its output, its exit code and an
// error only if it could not be launched (exec.ErrNotFound: it is not there — the case that makes a fact
// UNKNOWN, §6.6.7; ErrNotAllowed: outside the list).
type Executor func(time_limit time.Duration, name string, call_args ...string) (output string, code int, err error)

// allowedPath: the absolute path of a program of the list, if it is there.
func allowedPath(name string) (string, error) {
	cand, ok := allowedPrograms[name]
	if !ok {
		return "", ErrNotAllowed
	}
	for _, p := range cand {
		if st, err := os.Stat(p); err == nil && st.Mode().IsRegular() && st.Mode()&0o111 != 0 {
			return p, nil
		}
	}
	return "", exec.ErrNotFound
}

// runReally: absolute path, fixed arguments, minimal environment in the C local, no
// input, maximum time; and the record (R41).
func (a *Environment) runReally(time_limit time.Duration, name string, call_args ...string) (string, int, error) {
	fpath, err := allowedPath(name)
	if err != nil {
		a.annotate(name, call_args, -1, err)
		return "", -1, err
	}
	ctx, rollback := context.WithTimeout(context.Background(), time_limit)
	defer rollback()
	cmd := exec.CommandContext(ctx, fpath, call_args...)
	// ZYPP_LOCK_TIMEOUT: zypper waits for whoever holds it, like apt with DPkg::Lock::Timeout (busy.go)
	cmd.Env = []string{"LC_ALL=C", "PATH=/usr/sbin:/usr/bin:/sbin:/bin", "DEBIAN_FRONTEND=noninteractive",
		"ZYPP_LOCK_TIMEOUT=" + strconv.Itoa(int(BusyCap.Seconds()))}
	var output strings.Builder
	cmd.Stdout = &output
	cmd.Stderr = &output
	err = cmd.Run()
	code := 0
	var ee *exec.ExitError
	switch {
	case ctx.Err() == context.DeadlineExceeded:
		code, err = -1, ctx.Err()
	case errors.As(err, &ee):
		code, err = ee.ExitCode(), nil
	case err != nil:
		code = -1
	}
	a.annotate(fpath, call_args, code, err)
	return output.String(), code, err
}

func (a *Environment) annotate(fpath string, call_args []string, code int, err error) {
	if a.Annotate == nil {
		return
	}
	r := fpath + " " + strings.Join(call_args, " ") + " ⇒ " + strconv.Itoa(code)
	if err != nil {
		r += " (" + err.Error() + ")"
	}
	a.Annotate(r)
}

// GroupHandler reads and changes group membership.
type GroupHandler interface {
	// Membri: the group's explicit members, and whether the group exists.
	Members(group string) (members []string, gid string, path_exists bool, err error)
	// PrimaryGroup: the gid of the user's primary group, and whether the user exists.
	PrimaryGroup(user string) (gid string, path_exists bool, err error)
	Insert(user, group string) error
	Remove(user, group string) error
}

// UnitHandler enables, disables, starts and stops systemd units (over D-Bus).
type UnitHandler interface {
	// State: the state of the unit file (enabled, disabled, static, masked, not-found…), what
	// systemctl is-enabled calls by the same name.
	State(unit string) (string, error)
	Enable(unit string) error
	Disable(unit string) error
	// Active: ActiveState (active, inactive, failed…).
	Active(unit string) (string, error)
	Launch(unit string) error
	Stop(unit string) error
	Reload(unit string) error
	// the boot target (graphical.target / multi-user.target)
	Default() (string, error)
	SetDefault(target string) error
}

// Session: a logind session.
type Session struct {
	ID, User, Service, State, Type string
}

// SessionHandler: logind, over D-Bus.
type SessionHandler interface {
	Listing() ([]Session, error)
	Terminate(id string) error
	// Signal to the processes of ONE session (logind KillSession, who=all): it stays inside the session.
	Signal(id string, send_signal int32) error
	// Grafici: how many desktop processes the person has in their user manager.
	Charts(user string) (int, error)
	// CloseGraphical: stops the desktop's units in the user manager (graphical_user.go).
	CloseGraphical(user string) ([]string, error)
}

// FirewallHandler opens and closes a port. Today only firewalld (§6.6.4, T4's mandate).
type FirewallHandler interface {
	Nome() string // "firewalld", "ufw", "nftables", "none"
	DefaultZone() (string, error)
	HasPort(zone, port string, permanent bool) (bool, error) // port = "7447/tcp"
	Insert(zone, port string, permanent bool) error
	Remove(zone, port string, permanent bool) error
}

// Environment is everything the engine touches or reads of the machine. The tests build a fake one
// under a folder; the engine does not know the difference.
type Environment struct {
	Root    string // "/" on the real machine; for reading /etc, /sys, /proc, /usr, /var/lib
	Run    Executor
	Bus       *Bus // system D-Bus (nil in the tests)
	Famiglia  string
	Gruppi    GroupHandler
	Unita     UnitHandler
	Firewall  FirewallHandler
	Pacchetti Manager
	Sessioni  SessionHandler
	Annotate    func(line string) // every program launched (R41); nil = nobody listens
	Avvisa    func(m Message) // what the engine says while it waits (busy.go); nil = nobody listens
}

func (a *Environment) avvisa(m Message) {
	if a.Avvisa != nil {
		a.Avvisa(m)
	}
}

// P is a machine path seen from the environment's root.
func (a *Environment) P(fpath string) string {
	if a.Root == "" || a.Root == "/" {
		return fpath
	}
	return filepath.Join(a.Root, fpath)
}

// RealEnvironment is the machine the engine runs on.
func RealEnvironment() *Environment {
	a := &Environment{Root: "/", Bus: &Bus{}}
	a.Run = a.runReally
	a.Gruppi = &realGroups{a}
	a.Unita = &unitDBus{a.Bus}
	a.Firewall = chooseFirewall(a)
	a.Sessioni = &sessionsDBus{a.Bus, a}
	if m, _ := OsRelease(a); m != nil {
		a.Famiglia = Famiglia(m["ID"], m["ID_LIKE"])
	}
	a.Pacchetti = ChooseHandler(a, a.Famiglia)
	return a
}

// ReadGroups reads a file in the /etc/group format: name → (gid, members).
func ReadGroups(fpath string) (map[string][2]string, error) {
	f, err := os.Open(fpath)
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

// SplitMembers: "a,b,,c" → [a b c], sorted.
func SplitMembers(s string) []string {
	var m []string
	for _, x := range strings.Split(s, ",") {
		if x = strings.TrimSpace(x); x != "" {
			m = append(m, x)
		}
	}
	sort.Strings(m)
	return m
}

// ReadUser looks up a user in a file in the /etc/passwd format and gives their gid.
func ReadUser(fpath, user string) (gid string, path_exists bool, err error) {
	f, err := os.Open(fpath)
	if err != nil {
		return "", false, err
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) >= 4 && c[0] == user {
			return c[3], true, nil
		}
	}
	return "", false, s.Err()
}

// realGroups: /etc/group is read, changed with gpasswd (which also keeps gshadow and the lock
// of the account files: there is no stable D-Bus interface for local groups). Only local
// groups: they are the ones REMOTIX touches (§6.4).
type realGroups struct{ a *Environment }

func (g *realGroups) Members(group string) ([]string, string, bool, error) {
	t, err := ReadGroups(g.a.P("/etc/group"))
	if err != nil {
		return nil, "", false, err
	}
	v, ok := t[group]
	return SplitMembers(v[1]), v[0], ok, nil
}

func (g *realGroups) PrimaryGroup(user string) (string, bool, error) {
	return ReadUser(g.a.P("/etc/passwd"), user)
}

func (g *realGroups) Insert(user, group string) error {
	return runOrError(g.a, "gpasswd", "-a", user, group)
}

func (g *realGroups) Remove(user, group string) error {
	return runOrError(g.a, "gpasswd", "-d", user, group)
}

// firewallNotDone: nftables is recognised, but the engine cannot change it yet (T4's
// mandate): every change returns RX-FW-004, and the plan declares it beforehand. (ufw can, since T6.)
type firewallNotDone struct{ name string }

func (f *firewallNotDone) Nome() string                 { return f.name }
func (f *firewallNotDone) DefaultZone() (string, error) { return "", nil }
func (f *firewallNotDone) HasPort(string, string, bool) (bool, error) {
	return false, Error("RX-FW-004", f.name)
}
func (f *firewallNotDone) Insert(string, string, bool) error { return Error("RX-FW-004", f.name) }
func (f *firewallNotDone) Remove(string, string, bool) error  { return Error("RX-FW-004", f.name) }

// firewallUfw: ufw running (T6). With its program (closed list); a single level — ufw's rules
// are live and permanent together: «live» reads as «permanent» and does not change by itself.
// The rule: the application profile «REMOTIX» (the .deb package puts it in
// /etc/ufw/applications.d/remotix) if it is there and the port is its own, otherwise the port.
type firewallUfw struct{ a *Environment }

func (f *firewallUfw) Nome() string                 { return "ufw" }
func (f *firewallUfw) DefaultZone() (string, error) { return "", nil }

// Knows: the service profile is there (the file name is the service's).
func (f *firewallUfw) Knows(service string) (bool, error) {
	_, err := os.Stat(f.a.P("/etc/ufw/applications.d/" + service))
	return err == nil, nil
}

// ufwRule: «service:remotix» ⇒ «REMOTIX» (the profile name); «7447/tcp» stays as it is.
func ufwRule(port string) string {
	if s := serviceOf(port); s != "" {
		return strings.ToUpper(s)
	}
	return port
}

// HasPort: the rule is among those added (`ufw show added`, which answers even with ufw off).
func (f *firewallUfw) HasPort(_, port string, _ bool) (bool, error) {
	out, c, err := f.a.Run(time.Minute, "ufw", "show", "added")
	if err != nil {
		return false, err
	}
	if c != 0 {
		return false, fmt.Errorf("ufw show added: exit %d: %s", c, strings.TrimSpace(out))
	}
	want := "ufw allow " + ufwRule(port)
	for _, r := range strings.Split(out, "\n") {
		if strings.TrimSpace(r) == want {
			return true, nil
		}
	}
	return false, nil
}

func (f *firewallUfw) Insert(_, port string, permanent bool) error {
	if !permanent {
		return nil // a single level: the rule is put by the «permanent» step
	}
	return runOrError(f.a, "ufw", "allow", ufwRule(port))
}

func (f *firewallUfw) Remove(_, port string, permanent bool) error {
	if !permanent {
		return nil
	}
	return runOrError(f.a, "ufw", "delete", "allow", ufwRule(port))
}

// chooseFirewall: the running one. firewalld answers on the bus; ufw says it is on in its file;
// nftables as an active unit.
func chooseFirewall(a *Environment) FirewallHandler {
	if fw := (&firewalldDBus{a.Bus}); fw.Lit() {
		return fw
	}
	if b, err := os.ReadFile(a.P("/etc/ufw/ufw.conf")); err == nil && strings.Contains(string(b), "ENABLED=yes") {
		return &firewallUfw{a}
	}
	if s, err := a.Bus.ActiveState("nftables.service"); err == nil && s == "active" {
		return &firewallNotDone{"nftables"}
	}
	return &firewallNotDone{"none"}
}

func runOrError(a *Environment, name string, call_args ...string) error {
	out, c, err := a.Run(2*time.Minute, name, call_args...)
	if err != nil {
		return err
	}
	if c != 0 {
		return errors.New(name + " " + strings.Join(call_args, " ") + ": exit " + strconv.Itoa(c) + ": " + strings.TrimSpace(out))
	}
	return nil
}
