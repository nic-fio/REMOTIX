package motore

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// chiudi-sessioni: alla disinstallazione, le sessioni REMOTIX ancora aperte si chiudono (DECISIONI
// §10.16, fasi/17 §6.5-bis, R43). Le trova logind: le sessioni col servizio PAM «remotix»
// (proprietà Service); le chiude logind (TerminateSession), che porta via i processi nati dentro.
// ⛔ SOLO quelle: niente TerminateUser né KillUser — una sessione locale o ssh della stessa persona
// resta. Gli utenti li ha avvisati l'amministratore; il piano, confermato una volta come ogni
// piano, porta solo questo passo. IRREVERSIBILE: il lavoro non salvato va perso, e un ritorno
// indietro non riapre niente.

func init() {
	registraTipo("chiudi-sessioni", func(AzionePiano) (Azione, error) { return chiudiSessioni{}, nil })
}

// ServizioPAM: il nome del servizio PAM di REMOTIX (/etc/pam.d/remotix).
const ServizioPAM = "remotix"

// PianoChiudiSessioni prepara il passo, dicendo quante sessioni ci sono adesso.
func PianoChiudiSessioni(id string, n int, utenti []string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "chiudi-sessioni",
		Parametri:      map[string]string{"servizio": ServizioPAM},
		Descrizione:    T("az.sessioni", n, strings.Join(utenti, ", ")),
		ComeSiFa:       T("az.sessioni.fa"),
		ComeSiVerifica: T("az.sessioni.verifica"),
		ComeSiAnnulla:  T("az.sessioni.annulla"),
		Reversibilita:  IRREVERSIBILE,
	}
}

// SessioniRemotix: le sessioni di logind col servizio PAM remotix.
func SessioniRemotix(a *Ambiente) ([]Sessione, error) {
	if a.Sessioni == nil {
		return nil, nil
	}
	l, err := a.Sessioni.Elenco()
	if err != nil {
		return nil, err
	}
	var r []Sessione
	for _, s := range l {
		if s.Servizio == ServizioPAM {
			r = append(r, s)
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].ID < r[j].ID })
	return r, nil
}

type chiudiSessioni struct{}

type primaSessioni struct {
	Origine  Origine  `json:"origine"`
	Sessioni []string `json:"sessioni"`
	Utenti   []string `json:"utenti"`
}

func (chiudiSessioni) Vincoli(*Contesto) ([]string, error) { return nil, nil } // cambiano da sole: non vincolano

func (chiudiSessioni) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	l, err := SessioniRemotix(c.Amb)
	if err != nil {
		return nil, "", err
	}
	p := primaSessioni{Origine: DIRETTA, Sessioni: []string{}, Utenti: []string{}}
	for _, s := range l {
		p.Sessioni = append(p.Sessioni, s.ID)
		p.Utenti = append(p.Utenti, s.Utente)
	}
	if len(l) == 0 {
		p.Origine = PREESISTENTE // niente da chiudere
	}
	return jsonDi(p), p.Origine, nil
}

// rimaste: le sessioni di prima ancora aperte. Una sessione «closing» il cui scope non ha più
// processi è chiusa (logind la toglie dall'elenco quando vuole): si guarda cgroup.procs, in sola
// lettura. ⚠ [M] 30 set, debian13-gnome: la sessione del figlio di REMOTIX è «closing» fin dalla
// nascita (§5.2) e il desktop GNOME vive nel gestore d'utente (user@<uid>.service), NON nello scope
// della sessione: TerminateSession porta via lo scope, non il desktop (annotato in §13.1).
func (chiudiSessioni) rimaste(c *Contesto, p primaSessioni) (int, error) {
	l, err := SessioniRemotix(c.Amb)
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
		if s.Stato == "closing" && scopeVuoto(c.Amb, s.ID) {
			continue
		}
		n++
	}
	return n, nil
}

// scopeVuoto: nessun processo in session-<id>.scope.
func scopeVuoto(a *Ambiente, id string) bool {
	v, _ := filepath.Glob(a.P("/sys/fs/cgroup/user.slice") + "/user-*.slice/session-" + id + ".scope/cgroup.procs")
	if len(v) == 0 {
		return true
	}
	b, err := os.ReadFile(v[0])
	return err == nil && strings.TrimSpace(string(b)) == ""
}

func (a chiudiSessioni) Fai(c *Contesto, prima json.RawMessage) error {
	var p primaSessioni
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	for _, id := range p.Sessioni {
		if err := c.Amb.Sessioni.Termina(id); err != nil && !strings.Contains(err.Error(), "No session") {
			return err
		}
	}
	// logind chiude in modo asincrono. ⚠ [M] 30 set, debian13-gnome: la sessione del figlio di
	// REMOTIX è «closing» dalla nascita (§5.2) e TerminateSession da sola NON svuota lo scope in 60
	// s. ⇒ dopo 10 s SIGTERM ai processi della sessione (KillSession, sempre dentro la sessione:
	// mai l'utente intero), dopo 20 s SIGKILL; fino a 60 s.
	for i := 0; i < 120; i++ {
		n, err := a.rimaste(c, p)
		if err != nil || n == 0 {
			return err
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
	return nil
}

func (a chiudiSessioni) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p primaSessioni
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	n, err := a.rimaste(c, p)
	if err != nil {
		return "", "", err
	}
	switch {
	case n == 0:
		return COMPLETO, "nessuna delle sessioni REMOTIX è ancora aperta", nil
	case n == len(p.Sessioni):
		return ASSENTE, "tutte ancora aperte", nil
	}
	return A_META, "alcune ancora aperte", nil
}

func (chiudiSessioni) Annulla(*Contesto, json.RawMessage) error {
	return Errore("RX-AZIONE-005", "chiudi-sessioni")
}

func (a chiudiSessioni) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p primaSessioni
	json.Unmarshal(prima, &p)
	if len(p.Sessioni) == 0 {
		return true, "non c'era niente da chiudere", nil
	}
	// se nessuna è stata chiusa davvero, non c'è niente di irreversibile da dichiarare
	if n, err := a.rimaste(c, p); err == nil && n == len(p.Sessioni) {
		return true, "nessuna sessione è stata chiusa", nil
	}
	return false, "IRREVERSIBILE: le sessioni chiuse non si riaprono", nil
}
