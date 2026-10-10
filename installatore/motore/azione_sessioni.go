package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// chiudi-sessioni: on uninstallation, the REMOTIX sessions still open are closed (DECISIONI
// §10.16, fasi/17 §6.5-bis, R43). logind finds them: the sessions with the PAM service «remotix»
// (property Service); logind closes them (TerminateSession), which takes away the processes born inside.
// ⛔ ONLY those: no TerminateUser or KillUser — a local or ssh session of the same person
// stays. The administrator has warned the users; the plan, confirmed once like every
// plan, carries only this step. IRREVERSIBLE: unsaved work is lost, and a rollback
// reopens nothing.

func init() {
	registerType("close-sessions", func(PlanAction) (Action, error) { return closeSessions{}, nil })
}

// PAMService: the name of REMOTIX's PAM service (/etc/pam.d/remotix).
const PAMService = "remotix"

// PlanCloseSessions prepares the step, saying how many sessions there are now.
func PlanCloseSessions(id string, n int, users []string) PlanAction {
	d := T("az.sessions.nessuna") // the step stays: one may open before it runs
	if n > 0 {
		d = T("az.sessions", n, strings.Join(users, ", "))
	}
	return PlanAction{
		ID: id, Kind: "close-sessions",
		Parameters:    map[string]string{"service": PAMService},
		Description:   d,
		ComeSiFa:      T("az.sessions.fa"),
		HowToVerify:   T("az.sessions.verify"),
		HowToUndo:     T("az.sessions.rollback"),
		Reversibility: IRREVERSIBLE,
	}
}

// RemotixSessions: logind's sessions with the PAM service remotix.
func RemotixSessions(a *Environment) ([]Session, error) {
	if a.Sessions == nil {
		return nil, nil
	}
	l, err := a.Sessions.List()
	if err != nil {
		return nil, err
	}
	var r []Session
	for _, s := range l {
		if s.Service == PAMService {
			r = append(r, s)
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].ID < r[j].ID })
	return r, nil
}

type closeSessions struct{}

type beforeSessions struct {
	Origin   Origin   `json:"origin"`
	Sessions []string `json:"sessions"`
	Users    []string `json:"users"`
	// Graphical: the people without another graphical session (a local desktop): for them the
	// desktop in the user manager is closed too (grafica_utente.go)
	Graphical []string `json:"graphical"`
}

func (closeSessions) Constraints(*Context) ([]string, error) { return nil, nil } // they change by themselves: they do not bind

func (closeSessions) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	l, err := RemotixSessions(c.Amb)
	if err != nil {
		return nil, "", err
	}
	p := beforeSessions{Origin: DIRECT, Sessions: []string{}, Users: []string{}}
	for _, s := range l {
		p.Sessions = append(p.Sessions, s.ID)
		p.Users = append(p.Users, s.Username)
	}
	all_of, err := c.Amb.Sessions.List()
	if err != nil {
		return nil, "", err
	}
	seen_items := map[string]bool{}
	for _, s := range l {
		if seen_items[s.Username] {
			continue
		}
		seen_items[s.Username] = true
		the_other := false
		for _, x := range all_of {
			if x.Username == s.Username && x.Service != PAMService && (x.Kind == "wayland" || x.Kind == "x11") {
				the_other = true
			}
		}
		if !the_other {
			p.Graphical = append(p.Graphical, s.Username)
		}
	}
	if len(l) == 0 {
		p.Origin = PREEXISTING // nothing to close
	}
	return jsonDi(p), p.Origin, nil
}

// remainingGraphical: the desktop processes still alive in the user manager of the people in Graphical.
func (closeSessions) remainingGraphical(c *Context, p beforeSessions) int {
	n := 0
	for _, u := range p.Graphical {
		if k, err := c.Amb.Sessions.Graphical(u); err == nil {
			n += k
		}
	}
	return n
}

// left: the earlier sessions still open. A «closing» session whose scope has no more
// processes is closed (logind removes it from the list when it likes): cgroup.procs is looked at,
// read-only. ⚠ [M] 30 Sep, debian13-gnome: the session of REMOTIX's child is «closing» from
// birth (§5.2) and the GNOME desktop lives in the user manager (user@<uid>.service), NOT in the
// session's scope: TerminateSession takes away the scope, not the desktop (noted in §13.1).
func (closeSessions) left(c *Context, p beforeSessions) (int, error) {
	l, err := RemotixSessions(c.Amb)
	if err != nil {
		return 0, err
	}
	owned := map[string]bool{}
	for _, id := range p.Sessions {
		owned[id] = true
	}
	n := 0
	for _, s := range l {
		if !owned[s.ID] {
			continue
		}
		if s.State == "closing" && emptyScope(c.Amb, s.ID) {
			continue
		}
		n++
	}
	return n, nil
}

// emptyScope: no process in session-<id>.scope.
func emptyScope(a *Environment, id string) bool {
	v, _ := filepath.Glob(a.P("/sys/fs/cgroup/user.slice") + "/user-*.slice/session-" + id + ".scope/cgroup.procs")
	if len(v) == 0 {
		return true
	}
	b, err := os.ReadFile(v[0])
	return err == nil && strings.TrimSpace(string(b)) == ""
}

func (a closeSessions) Do(c *Context, before json.RawMessage) error {
	var p beforeSessions
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	for _, id := range p.Sessions {
		if err := c.Amb.Sessions.Terminate(id); err != nil && !strings.Contains(err.Error(), "No session") {
			return err
		}
	}
	// logind closes asynchronously. ⚠ [M] 30 Sep, debian13-gnome: the session of REMOTIX's
	// child is «closing» from birth (§5.2) and TerminateSession alone does NOT empty the scope in 60
	// s. ⇒ after 10 s SIGTERM to the session's processes (KillSession, always inside the session:
	// never the whole user), after 20 s SIGKILL; up to 60 s.
	for i := 0; i < 120; i++ {
		n, err := a.left(c, p)
		if err != nil {
			return err
		}
		if n == 0 {
			break
		}
		if i == 20 || i == 40 {
			sg := int32(15)
			if i == 40 {
				sg = 9
			}
			for _, id := range p.Sessions {
				c.Amb.Sessions.Signal(id, sg)
			}
		}
		time.Sleep(500 * time.Millisecond)
	}
	// the desktop in the user manager (§10.16: «REMOTIX sessions and their processes»)
	for _, u := range p.Graphical {
		if _, err := c.Amb.Sessions.CloseGraphical(u); err != nil {
			return err
		}
	}
	return nil
}

func (a closeSessions) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	var p beforeSessions
	if err := json.Unmarshal(before, &p); err != nil {
		return "", "", err
	}
	n, err := a.left(c, p)
	if err != nil {
		return "", "", err
	}
	g := a.remainingGraphical(c, p)
	switch {
	case n == 0 && g == 0:
		return COMPLETE, "none of the REMOTIX sessions is still open, no desktop process", nil
	case n == 0:
		return A_META, fmt.Sprintf("%d desktop processes still alive in the user manager", g), nil
	case n == len(p.Sessions):
		return ABSENT, "all still open", nil
	}
	return A_META, "some still open", nil
}

func (closeSessions) Rollback(*Context, json.RawMessage) error {
	return Error("RX-AZIONE-005", "close-sessions")
}

func (a closeSessions) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	var p beforeSessions
	json.Unmarshal(before, &p)
	if len(p.Sessions) == 0 {
		return true, "there was nothing to close", nil
	}
	// if none was really closed, there is nothing irreversible to declare
	if n, err := a.left(c, p); err == nil && n == len(p.Sessions) {
		return true, "no session was closed", nil
	}
	return false, "IRREVERSIBLE: closed sessions are not reopened", nil
}
