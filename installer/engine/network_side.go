package engine

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

// THE NETWORK SIDE'S USER (1.5, DECISIONS §11.50). The service starts as root (the root side: PAM,
// the desktops' birth) and forks the network side, which drops itself to the system user
// `remotix` and keeps its files in /var/lib/remotix/net. The PACKAGE creates the user (sysusers.d)
// and moves 1.0's certificates/ and ban into net/ before the restart (remotix-net-move); the engine
// only:
//   - refuses, in the preflight, a machine where `remotix` is a PERSON's account (sysusers' «u»
//     would silently reuse it, and the network side would run as that person): RX-NETUSER-001;
//   - says, in post-upgrade and in the certification, whether the user is there and net/ is
//     its own (RX-NETUSER-002, -003; check «network-side»);
//   - removes the user and its group with `uninstall --purge` (the user, 16 Oct 2026); a plain
//     uninstallation keeps it, and the plan declares it.

const (
	NetUser      = "remotix"
	NetDir       = "/var/lib/remotix/net"
	netSysusers  = "/usr/lib/sysusers.d/remotix.conf"
	netStateRoot = "/var/lib/remotix"
)

// netOld: what 1.0 kept in /var/lib/remotix, which the package moves into net/.
var netOld = []string{"certificates", "ban"}

// Account: a line of /etc/passwd.
type Account struct {
	Name, Gecos, Home, Shell string
	Uid, Gid                 int
}

// ReadAccount looks a user up in the machine's /etc/passwd.
func ReadAccount(a *Environment, name string) (Account, bool) {
	t, ok := load(a, "/etc/passwd")
	if !ok {
		return Account{}, false
	}
	for _, line := range strings.Split(t, "\n") {
		c := strings.Split(line, ":")
		if len(c) < 7 || c[0] != name {
			continue
		}
		uid, e1 := strconv.Atoi(c[2])
		gid, e2 := strconv.Atoi(c[3])
		if e1 != nil || e2 != nil {
			continue
		}
		return Account{Name: c[0], Uid: uid, Gid: gid, Gecos: c[4], Home: c[5], Shell: c[6]}, true
	}
	return Account{}, false
}

// uidMin: UID_MIN of login.defs (1000 if not said).
func uidMin(a *Environment) int {
	for _, f := range []string{"/etc/login.defs", "/usr/etc/login.defs"} {
		if t, ok := load(a, f); ok {
			for _, r := range strings.Split(t, "\n") {
				c := strings.Fields(r)
				if len(c) == 2 && c[0] == "UID_MIN" {
					if n, err := strconv.Atoi(c[1]); err == nil {
						return n
					}
				}
			}
			break
		}
	}
	return 1000
}

func loginShell(sh string) bool {
	return sh != "" && !strings.HasSuffix(sh, "/nologin") && !strings.HasSuffix(sh, "/false")
}

// personHome: a home that is a real folder of its own (not /, not REMOTIX's state).
func personHome(a *Environment, h string) bool {
	switch filepath.Clean(h) {
	case ".", "/", "/nonexistent", "/var/empty", netStateRoot, NetDir, "/run/remotix", "/run/remotix/net":
		return false
	}
	st, err := os.Stat(a.P(h))
	return err == nil && st.IsDir()
}

// PersonAccount: why the account is a person's and not a system user ("" = it is a system user).
func PersonAccount(a *Environment, u Account) string {
	var why []string
	if u.Uid >= uidMin(a) && u.Uid < 60000 {
		why = append(why, fmt.Sprintf("uid %d ≥ UID_MIN %d", u.Uid, uidMin(a)))
	}
	if loginShell(u.Shell) {
		why = append(why, "login shell "+u.Shell)
	}
	if personHome(a, u.Home) {
		why = append(why, "home "+u.Home)
	}
	return strings.Join(why, ", ")
}

// netUser (preflight, read only): the account named remotix, if there is one.
func netUser(a *Environment, p *ProfileV) {
	u, ok := ReadAccount(a, NetUser)
	if !ok {
		p.Detected("user.remotix", "absent", "/etc/passwd")
		return
	}
	if why := PersonAccount(a, u); why != "" {
		p.Detected("user.remotix", "person uid="+strconv.Itoa(u.Uid), "/etc/passwd")
		p.Con("RX-NETUSER-001", why)
		return
	}
	p.Detected("user.remotix", "system uid="+strconv.Itoa(u.Uid), "/etc/passwd")
}

// NetworkSide: is the network side's user there, and is net/ its own? ok=false with the message
// code; applies=false when the installed REMOTIX package has no sysusers file (before 1.5: a
// downgrade to 1.0 is allowed, §10.23, and has nothing to check).
func NetworkSide(a *Environment) (applies bool, code, detail string) {
	if _, err := os.Stat(a.P(netSysusers)); err != nil {
		return false, "", T("net.prima")
	}
	u, ok := ReadAccount(a, NetUser)
	if !ok {
		return true, "RX-NETUSER-002", "/etc/passwd"
	}
	if why := PersonAccount(a, u); why != "" {
		return true, "RX-NETUSER-001", why
	}
	var wrong []string
	st, err := os.Lstat(a.P(NetDir))
	switch {
	case err != nil:
		return true, "RX-NETUSER-003", NetDir + ": " + T("net.manca")
	case !st.IsDir():
		return true, "RX-NETUSER-003", NetDir + ": " + T("net.non_cartella")
	case st.Mode().Perm() != 0o700:
		wrong = append(wrong, fmt.Sprintf("%s %04o", NetDir, st.Mode().Perm()))
	}
	filepath.WalkDir(a.P(NetDir), func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.Type()&fs.ModeSymlink != 0 || len(wrong) >= 5 {
			return nil
		}
		if i, err := d.Info(); err == nil {
			if s, ok := i.Sys().(*syscall.Stat_t); ok && (int(s.Uid) != u.Uid || int(s.Gid) != u.Gid) {
				r, _ := filepath.Rel(a.P("/"), p)
				wrong = append(wrong, fmt.Sprintf("/%s %d:%d", r, s.Uid, s.Gid))
			}
		}
		return nil
	})
	if len(wrong) > 0 {
		return true, "RX-NETUSER-003", T("net.non_suoi", NetUser, u.Uid, strings.Join(wrong, ", "))
	}
	var left []string
	for _, n := range netOld {
		if _, err := os.Lstat(a.P(filepath.Join(netStateRoot, n))); err == nil {
			left = append(left, filepath.Join(netStateRoot, n))
		}
	}
	if len(left) > 0 {
		return true, "RX-NETUSER-003", T("net.non_spostati", strings.Join(left, ", "))
	}
	return true, "", T("net.ok", NetUser, u.Uid)
}

// checkNetworkSide: the certification's check (certify.go). Required: a network side that
// cannot read its ban file stops the server.
func checkNetworkSide(a *Environment) CheckReport {
	k := CheckReport{ID: "network-side", What: T("ver.rete"), Requested: true}
	applies, code, det := NetworkSide(a)
	switch {
	case !applies || code == "":
		k.Outcome, k.Detail = "PASS", det
	default:
		k.Outcome, k.Detail = "FAIL", code+" "+Codes[code].Testo+" ("+det+")"
	}
	return k
}

// ---------------------------------------------------------------- remove-system-user

// remove-system-user (uninstall --purge only): the user remotix and its group, after the packages
// are gone. ⛔ Never a person's account (PersonAccount): that one is PRE-EXISTING. BEST_EFFORT: the
// rollback (an uninstallation that fails halfway) creates them again with the same uid and gid.

func init() { registerType("remove-system-user", newRemoveSystemUser) }

// PlanRemoveSystemUser: the step, if the user is there now and is a system user ("" otherwise).
func PlanRemoveSystemUser(a *Environment, id string) (PlanAction, bool) {
	u, ok := ReadAccount(a, NetUser)
	if !ok || PersonAccount(a, u) != "" {
		return PlanAction{}, false
	}
	return PlanAction{
		ID: id, Type: "remove-system-user",
		Parameters:    map[string]string{"user": NetUser},
		Description:   T("az.utente", NetUser, u.Uid),
		ComeSiFa:      T("az.utente.fa", NetUser),
		HowToVerify:   T("az.utente.verifica", NetUser),
		HowToUndo:     T("az.utente.annulla", NetUser, u.Uid, u.Gid),
		Reversibility: BEST_EFFORT,
	}, true
}

type removeSystemUser struct{ user string }

func newRemoveSystemUser(p PlanAction) (Action, error) {
	if p.Parameters["user"] != NetUser {
		return nil, fmt.Errorf("remove-system-user: only %s, not %q", NetUser, p.Parameters["user"])
	}
	return &removeSystemUser{p.Parameters["user"]}, nil
}

type beforeSystemUser struct {
	Origine Origine `json:"origin"`
	User    bool    `json:"user"`
	Group   bool    `json:"group"`
	Uid     int     `json:"uid"`
	Gid     int     `json:"gid"`
	Gecos   string  `json:"gecos,omitempty"`
	Home    string  `json:"home,omitempty"`
	Shell   string  `json:"shell,omitempty"`
}

func (r *removeSystemUser) Constraints(*Context) ([]string, error) { return nil, nil }

func (r *removeSystemUser) present(c *Context) (user, group bool, err error) {
	_, user = ReadAccount(c.Env, r.user)
	g, err := ReadGroups(c.Env.P("/etc/group"))
	if err != nil {
		return false, false, err
	}
	_, group = g[r.user]
	return user, group, nil
}

func (r *removeSystemUser) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	p := beforeSystemUser{Origine: PREEXISTING}
	user, group, err := r.present(c)
	if err != nil {
		return nil, "", err
	}
	u, _ := ReadAccount(c.Env, r.user)
	if user && PersonAccount(c.Env, u) != "" {
		return jsonDi(p), PREEXISTING, nil // a person's: never touched
	}
	if g, err := ReadGroups(c.Env.P("/etc/group")); err == nil && group {
		p.Gid, _ = strconv.Atoi(g[r.user][0])
	}
	if user {
		p.Uid, p.Gid, p.Gecos, p.Home, p.Shell = u.Uid, u.Gid, u.Gecos, u.Home, u.Shell
	}
	p.User, p.Group = user, group
	if user || group {
		p.Origine = DIRECT
	}
	return jsonDi(p), p.Origine, nil
}

func (r *removeSystemUser) load(before json.RawMessage) (beforeSystemUser, error) {
	var p beforeSystemUser
	err := json.Unmarshal(before, &p)
	return p, err
}

// Do: userdel, then groupdel if the group is still there (userdel removes it only under
// USERGROUPS_ENAB). Idempotent.
func (r *removeSystemUser) Do(c *Context, before json.RawMessage) error {
	p, err := r.load(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	user, _, err := r.present(c)
	if err != nil {
		return err
	}
	if user {
		if err := runOrError(c.Env, "userdel", r.user); err != nil {
			return err
		}
	}
	if _, group, err := r.present(c); err != nil {
		return err
	} else if group {
		return runOrError(c.Env, "groupdel", r.user)
	}
	return nil
}

func (r *removeSystemUser) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	p, err := r.load(before)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREEXISTING {
		return COMPLETE, T("az.utente.nulla"), nil
	}
	user, group, err := r.present(c)
	switch {
	case err != nil:
		return "", "", err
	case !user && !group:
		return COMPLETE, T("az.utente.tolto", r.user), nil
	case user == p.User && group == p.Group:
		return ABSENT, T("az.utente.ancora", r.user), nil
	}
	return A_META, T("az.utente.ancora", r.user), nil
}

func (r *removeSystemUser) Rollback(c *Context, before json.RawMessage) error {
	p, err := r.load(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	user, group, err := r.present(c)
	if err != nil {
		return err
	}
	if p.Group && !group {
		if err := runOrError(c.Env, "groupadd", "-r", "-g", strconv.Itoa(p.Gid), r.user); err != nil {
			return err
		}
	}
	if p.User && !user {
		return runOrError(c.Env, "useradd", "-r", "-M", "-u", strconv.Itoa(p.Uid), "-g", strconv.Itoa(p.Gid),
			"-d", notEmpty(p.Home, "/"), "-s", notEmpty(p.Shell, "/usr/sbin/nologin"), "-c", p.Gecos, r.user)
	}
	return nil
}

func (r *removeSystemUser) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
	p, err := r.load(before)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREEXISTING {
		return true, T("az.utente.nulla"), nil
	}
	u, user := ReadAccount(c.Env, r.user)
	_, group, err := r.present(c)
	if err != nil {
		return false, "", err
	}
	if user != p.User || group != p.Group || (user && u.Uid != p.Uid) {
		return false, T("az.utente.non_rimesso", r.user), nil
	}
	return true, T("az.utente.rimesso", r.user, p.Uid), nil
}
