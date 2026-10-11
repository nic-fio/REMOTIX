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
	registraTipo("close-sessions", func(AzionePiano) (Azione, error) { return closeSessions{}, nil })
}

// PAMService: the name of REMOTIX's PAM service (/etc/pam.d/remotix).
const PAMService = "remotix"

// PlanCloseSessions prepares the step, saying how many sessions there are now.
func PlanCloseSessions(id string, n int, utenti []string) AzionePiano {
	d := T("az.sessioni.nessuna") // the step stays: one may open before it runs
	if n > 0 {
		d = T("az.sessioni", n, strings.Join(utenti, ", "))
	}
	return AzionePiano{
		ID: id, Tipo: "close-sessions",
		Parametri:     map[string]string{"service": PAMService},
		Descrizione:   d,
		ComeSiFa:      T("az.sessioni.fa"),
		HowToVerify:   T("az.sessioni.verifica"),
		HowToUndo:     T("az.sessioni.annulla"),
		Reversibilita: IRREVERSIBILE,
	}
}

// RemotixSessions: logind's sessions with the PAM service remotix.
func RemotixSessions(a *Ambiente) ([]Sessione, error) {
	if a.Sessioni == nil {
		return nil, nil
	}
	l, err := a.Sessioni.Listing()
	if err != nil {
		return nil, err
	}
	var r []Sessione
	for _, s := range l {
		if s.Servizio == PAMService {
			r = append(r, s)
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].ID < r[j].ID })
	return r, nil
}

type closeSessions struct{}

type beforeSessions struct {
	Origine  Origine  `json:"origin"`
	Sessioni []string `json:"sessions"`
	Utenti   []string `json:"users"`
	// Grafica: the people without another graphical session (a local desktop): for them the
	// desktop in the user manager is closed too (grafica_utente.go)
	Gfx []string `json:"graphical"`
}

func (closeSessions) Vincoli(*Contesto) ([]string, error) { return nil, nil } // they change by themselves: they do not bind

func (closeSessions) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	l, err := RemotixSessions(c.Amb)
	if err != nil {
		return nil, "", err
	}
	p := beforeSessions{Origine: DIRETTA, Sessioni: []string{}, Utenti: []string{}}
	for _, s := range l {
		p.Sessioni = append(p.Sessioni, s.ID)
		p.Utenti = append(p.Utenti, s.Utente)
	}
	tutte, err := c.Amb.Sessioni.Listing()
	if err != nil {
		return nil, "", err
	}
	visti := map[string]bool{}
	for _, s := range l {
		if visti[s.Utente] {
			continue
		}
		visti[s.Utente] = true
		altra := false
		for _, x := range tutte {
			if x.Utente == s.Utente && x.Servizio != PAMService && (x.Tipo == "wayland" || x.Tipo == "x11") {
				altra = true
			}
		}
		if !altra {
			p.Gfx = append(p.Gfx, s.Utente)
		}
	}
	if len(l) == 0 {
		p.Origine = PREESISTENTE // nothing to close
	}
	return jsonDi(p), p.Origine, nil
}

// remainingGraphical: the desktop processes still alive in the user manager of the people in Grafica.
func (closeSessions) remainingGraphical(c *Contesto, p beforeSessions) int {
	n := 0
	for _, u := range p.Gfx {
		if k, err := c.Amb.Sessioni.Charts(u); err == nil {
			n += k
		}
	}
	return n
}

// rimaste: the earlier sessions still open. A «closing» session whose scope has no more
// processes is closed (logind removes it from the list when it likes): cgroup.procs is looked at,
// read-only. ⚠ [M] 30 Sep, debian13-gnome: the session of REMOTIX's child is «closing» from
// birth (§5.2) and the GNOME desktop lives in the user manager (user@<uid>.service), NOT in the
// session's scope: TerminateSession takes away the scope, not the desktop (noted in §13.1).
func (closeSessions) rimaste(c *Contesto, p beforeSessions) (int, error) {
	l, err := RemotixSessions(c.Amb)
	if err != nil {
		return 0, err
	}
	nostre := map[string]bool{}
	for _, id := range p.Sessioni {
		nostre[id] = true
	}
	n := 0
	for _, s := range l {
		if !nostre[s.ID] {
			continue
		}
		if s.Stato == "closing" && emptyScope(c.Amb, s.ID) {
			continue
		}
		n++
	}
	return n, nil
}

// emptyScope: no process in session-<id>.scope.
func emptyScope(a *Ambiente, id string) bool {
	v, _ := filepath.Glob(a.P("/sys/fs/cgroup/user.slice") + "/user-*.slice/session-" + id + ".scope/cgroup.procs")
	if len(v) == 0 {
		return true
	}
	b, err := os.ReadFile(v[0])
	return err == nil && strings.TrimSpace(string(b)) == ""
}

func (a closeSessions) Fai(c *Contesto, prima json.RawMessage) error {
	var p beforeSessions
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	for _, id := range p.Sessioni {
		if err := c.Amb.Sessioni.Terminate(id); err != nil && !strings.Contains(err.Error(), "No session") {
			return err
		}
	}
	// logind closes asynchronously. ⚠ [M] 30 Sep, debian13-gnome: the session of REMOTIX's
	// child is «closing» from birth (§5.2) and TerminateSession alone does NOT empty the scope in 60
	// s. ⇒ after 10 s SIGTERM to the session's processes (KillSession, always inside the session:
	// never the whole user), after 20 s SIGKILL; up to 60 s.
	for i := 0; i < 120; i++ {
		n, err := a.rimaste(c, p)
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
			for _, id := range p.Sessioni {
				c.Amb.Sessioni.Segnale(id, sg)
			}
		}
		time.Sleep(500 * time.Millisecond)
	}
	// the desktop in the user manager (§10.16: «REMOTIX sessions and their processes»)
	for _, u := range p.Gfx {
		if _, err := c.Amb.Sessioni.CloseGraphical(u); err != nil {
			return err
		}
	}
	return nil
}

func (a closeSessions) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p beforeSessions
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	n, err := a.rimaste(c, p)
	if err != nil {
		return "", "", err
	}
	g := a.remainingGraphical(c, p)
	switch {
	case n == 0 && g == 0:
		return COMPLETO, "none of the REMOTIX sessions is still open, no desktop process", nil
	case n == 0:
		return A_META, fmt.Sprintf("%d desktop processes still alive in the user manager", g), nil
	case n == len(p.Sessioni):
		return ASSENTE, "all still open", nil
	}
	return A_META, "some still open", nil
}

func (closeSessions) Annulla(*Contesto, json.RawMessage) error {
	return Errore("RX-AZIONE-005", "close-sessions")
}

func (a closeSessions) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p beforeSessions
	json.Unmarshal(prima, &p)
	if len(p.Sessioni) == 0 {
		return true, "there was nothing to close", nil
	}
	// if none was really closed, there is nothing irreversible to declare
	if n, err := a.rimaste(c, p); err == nil && n == len(p.Sessioni) {
		return true, "no session was closed", nil
	}
	return false, "IRREVERSIBLE: closed sessions are not reopened", nil
}
