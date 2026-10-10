package motore

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// The UNINSTALLATION (§6.0, third kind; §6.5 point 3; R6): an operation like the others, with
// its plan, its consent, its log and its resume, which walks BACKWARDS through the
// log of the confirmed installation (installazione.json). Every step of then with origin
// DIRETTA becomes an «undo» step: doing = its annulla, undoing = its fai (if the
// uninstallation fails halfway, it goes back to the previous installation). PREESISTENTE is never
// touched; the INDIRETTE are declared. Right after the service is switched off, the REMOTIX
// sessions still open are closed (chiudi-sessioni, §6.5-bis). On CONFIRMED uninstallation
// installazione.json is removed; the operations log stays (it is the machine's history,
// like dnf's).

func init() {
	registraTipo("undo", nuovaDisfa)
	registraTipo("remove-membership", nuovaIscrizione)
}

// FileIscrizioni: where REMOTIX records whom it enrolled in the groups at the first connection (figlio.c,
// §6.5-bis): origin DIRETTA, the uninstallation removes them like those of the engine.
const FileIscrizioni = "gruppi-iscritti.jsonl"

// Iscrizioni: the (user, group) pairs of the file, without duplicates.
func (m *Motore) Iscrizioni() [][2]string {
	b, err := os.ReadFile(filepath.Join(filepath.Dir(m.Cartella), FileIscrizioni))
	if err != nil {
		return nil
	}
	var r [][2]string
	visti := map[[2]string]bool{}
	for _, riga := range strings.Split(string(b), "\n") {
		var x struct {
			Formato, Utente, Gruppo, Origine string
		}
		if json.Unmarshal([]byte(riga), &x) != nil || x.Formato != "remotix-gruppi/1" || x.Utente == "" || x.Gruppo == "" {
			continue
		}
		k := [2]string{x.Utente, x.Gruppo}
		if !visti[k] {
			visti[k] = true
			r = append(r, k)
		}
	}
	return r
}

// togli-iscrizione: the inverse of aggiungi-utente-a-gruppo, for the enrolments made by REMOTIX.
type iscrizione struct{ g *gruppo }

func nuovaIscrizione(p AzionePiano) (Azione, error) {
	return &iscrizione{&gruppo{p.Parametri["user"], p.Parametri["group"]}}, nil
}

type primaIscrizione struct {
	Origine Origine `json:"origin"`
}

func (i *iscrizione) Vincoli(c *Contesto) ([]string, error) { return i.g.Vincoli(c) }
func (i *iscrizione) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	esp, _, _, err := i.g.membro(c)
	if err != nil {
		if CodiceDi(err) == "RX-GRUPPI-003" || CodiceDi(err) == "RX-GRUPPI-002" {
			return jsonDi(primaIscrizione{PREESISTENTE}), PREESISTENTE, nil // the user or the group is gone
		}
		return nil, "", err
	}
	if !esp {
		return jsonDi(primaIscrizione{PREESISTENTE}), PREESISTENTE, nil
	}
	return jsonDi(primaIscrizione{DIRETTA}), DIRETTA, nil
}
func (i *iscrizione) origine(prima json.RawMessage) Origine {
	var p primaIscrizione
	json.Unmarshal(prima, &p)
	return p.Origine
}
func (i *iscrizione) Fai(c *Contesto, prima json.RawMessage) error {
	if i.origine(prima) == PREESISTENTE {
		return nil
	}
	if esp, _, _, err := i.g.membro(c); err != nil || !esp {
		return err
	}
	return c.Amb.Gruppi.Togli(i.g.utente, i.g.gruppo)
}
func (i *iscrizione) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	if i.origine(prima) == PREESISTENTE {
		return COMPLETO, "nothing to remove", nil
	}
	esp, _, _, err := i.g.membro(c)
	if err != nil {
		return "", "", err
	}
	if esp {
		return ASSENTE, i.g.utente + " is still in " + i.g.gruppo, nil
	}
	return COMPLETO, i.g.utente + " is no longer in " + i.g.gruppo, nil
}
func (i *iscrizione) Annulla(c *Contesto, prima json.RawMessage) error {
	if i.origine(prima) == PREESISTENTE {
		return nil
	}
	if esp, _, _, err := i.g.membro(c); err != nil || esp {
		return err
	}
	return c.Amb.Gruppi.Aggiungi(i.g.utente, i.g.gruppo)
}
func (i *iscrizione) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	if i.origine(prima) == PREESISTENTE {
		return true, "nothing to put back", nil
	}
	esp, _, _, err := i.g.membro(c)
	return esp, "", err
}

// CartellaPiani: the plans approved by whoever installs, next to the operations folder
// (/var/lib/remotix/plans): the command line and the TUI write them there.
const CartellaPiani = "plans"

// PulisciStoria, on CONFIRMED uninstallation (the coordinator's decision, 30 Sep): without purge the
// engine's history stays (for support) but without the cached packages; with purge it is removed
// entirely — the operations and the plans —, and /var/lib/remotix too if it remains empty.
func (m *Motore) PulisciStoria(purge bool) error {
	if purge {
		for _, d := range []string{m.Cartella, filepath.Join(filepath.Dir(m.Cartella), CartellaPiani)} {
			if err := os.RemoveAll(d); err != nil {
				return err
			}
		}
		os.Remove(filepath.Join(filepath.Dir(m.Cartella), FileIscrizioni)) // already undone by the plan
		// the recorded versions (aggiornato.go). ⚠ 10 Oct 2026, names in English (DECISIONI §10.35): removed the
		// cleanups of the files of the engines from before D11/D14 — no real installation ever wrote them
		os.Remove(filepath.Join(filepath.Dir(m.Cartella), FileVersioniAnnotate))
		os.Remove(filepath.Dir(m.Cartella)) // only if empty
		return nil
	}
	voci, _ := filepath.Glob(filepath.Join(m.Cartella, "*", "cache"))
	for _, v := range voci {
		if err := os.RemoveAll(v); err != nil {
			return err
		}
	}
	return nil
}

// LeggiRegistro reads a log without opening it for writing.
func LeggiRegistro(percorso string) ([]Evento, error) {
	f, err := os.Open(percorso)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var r []Evento
	s := bufio.NewScanner(f)
	s.Buffer(make([]byte, 1<<20), 64<<20)
	for s.Scan() {
		var e Evento
		if json.Unmarshal(s.Bytes(), &e) == nil {
			r = append(r, e)
		}
	}
	return r, s.Err()
}

type disfa struct {
	op, azione string
	purge      bool
}

func nuovaDisfa(p AzionePiano) (Azione, error) {
	return &disfa{op: p.Parametri["operation"], azione: p.Parametri["action"], purge: p.Parametri["purge"] == "yes"}, nil
}

type primaDisfa struct {
	Origine   Origine         `json:"origin"`
	PrimaOrig json.RawMessage `json:"original_before"`
}

// originale: the action of then, its context (the operation folder of then, with the
// backups and the cache) and the before-state of then.
func (d *disfa) originale(c *Contesto) (Azione, *Contesto, *Evento, error) {
	dir := filepath.Join(filepath.Dir(c.Cartella), d.op)
	var pn Piano
	if err := LeggiJSON(filepath.Join(dir, "plan.json"), &pn); err != nil {
		return nil, nil, nil, err
	}
	var ap *AzionePiano
	for i := range pn.Azioni {
		if pn.Azioni[i].ID == d.azione {
			ap = &pn.Azioni[i]
		}
	}
	if ap == nil {
		return nil, nil, nil, fmt.Errorf("disfa: %s is not in the plan of %s", d.azione, d.op)
	}
	ev, err := LeggiRegistro(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, nil, nil, err
	}
	var intz *Evento
	for i := range ev {
		if ev[i].Azione == d.azione && ev[i].Tipo == EvIntenzione {
			intz = &ev[i]
			break
		}
	}
	a, err := NuovaAzione(*ap)
	if err != nil {
		return nil, nil, nil, err
	}
	return a, &Contesto{Amb: c.Amb, Cartella: dir, P: *ap, Purge: d.purge}, intz, nil
}

func (d *disfa) Vincoli(c *Contesto) ([]string, error) {
	a, cc, _, err := d.originale(c)
	if err != nil {
		return nil, err
	}
	return a.Vincoli(cc)
}

func (d *disfa) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	_, _, intz, err := d.originale(c)
	if err != nil {
		return nil, "", err
	}
	if intz == nil || intz.Origine == PREESISTENTE {
		return jsonDi(primaDisfa{Origine: PREESISTENTE}), PREESISTENTE, nil
	}
	return jsonDi(primaDisfa{Origine: DIRETTA, PrimaOrig: intz.Prima}), DIRETTA, nil
}

func (d *disfa) leggi(c *Contesto, prima json.RawMessage) (Azione, *Contesto, primaDisfa, error) {
	var p primaDisfa
	if err := json.Unmarshal(prima, &p); err != nil {
		return nil, nil, p, err
	}
	a, cc, _, err := d.originale(c)
	return a, cc, p, err
}

func (d *disfa) Fai(c *Contesto, prima json.RawMessage) error {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	return a.Annulla(cc, p.PrimaOrig)
}

func (d *disfa) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREESISTENTE {
		return COMPLETO, "nothing to undo", nil
	}
	if ok, det, err := a.Annullata(cc, p.PrimaOrig); err != nil {
		return "", "", err
	} else if ok {
		return COMPLETO, "undone: " + det, nil
	}
	e, det, err := a.Controlla(cc, p.PrimaOrig)
	if err != nil {
		return "", "", err
	}
	switch e {
	case COMPLETO:
		return ASSENTE, "still as the installation left it", nil
	case ESTRANEO:
		return ESTRANEO, det, nil
	}
	return A_META, det, nil
}

func (d *disfa) Ripara(c *Contesto, prima json.RawMessage) error {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil {
		return err
	}
	if r, ok := a.(Riparabile); ok {
		return r.Ripara(cc, p.PrimaOrig)
	}
	return nil
}

// Annulla (an uninstallation that fails halfway): what was there is redone.
func (d *disfa) Annulla(c *Contesto, prima json.RawMessage) error {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	return a.Fai(cc, p.PrimaOrig)
}

func (d *disfa) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "nothing to redo", nil
	}
	e, det, err := a.Controlla(cc, p.PrimaOrig)
	return e == COMPLETO, det, err
}

func (d *disfa) Indirette(prima json.RawMessage) []string {
	var p primaDisfa
	if json.Unmarshal(prima, &p) != nil || p.Origine == PREESISTENTE {
		return nil
	}
	return nil // the installation's indirect changes stay declared in its certificate, taken up below
}

// PianoDisinstallazione builds the plan from the log of the confirmed installation.
func (m *Motore) PianoDisinstallazione(prof *Profilo, purge bool) (*Piano, error) {
	in, err := m.ControllaInstallazione()
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(m.Cartella, in.Operazione)
	var orig Piano
	if err := LeggiJSON(filepath.Join(dir, "plan.json"), &orig); err != nil {
		return nil, err
	}
	ev, err := LeggiRegistro(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, err
	}
	origine := map[string]Origine{}
	for _, e := range ev {
		if e.Tipo == EvIntenzione {
			if _, ok := origine[e.Azione]; !ok {
				origine[e.Azione] = e.Origine
			}
		}
	}
	pn := &Piano{Formato: Formato, Oggetto: "plan", ID: nuovoID(), Creato: ora(), Mestiere: "uninstallation", Purge: purge,
		Motore: RifMotore{VersioneMotore, DigestMotore()}, Catalogo: RifCatalogo{m.Catalogo.Versione, m.Catalogo.Digest},
		Piattaforma: orig.Piattaforma, Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}}
	sess, _ := SessioniRemotix(m.Amb)
	var utenti []string
	visti := map[string]bool{}
	for _, s := range sess {
		if !visti[s.Utente] {
			visti[s.Utente] = true
			utenti = append(utenti, s.Utente)
		}
	}
	chiudi := PianoChiudiSessioni("close-sessions", len(sess), utenti)
	messa := false
	purgeS := map[bool]string{true: "yes", false: "no"}[purge]
	for i := len(orig.Azioni) - 1; i >= 0; i-- {
		a := orig.Azioni[i]
		o, fatta := origine[a.ID]
		if !fatta || o == PREESISTENTE {
			continue
		}
		pn.Azioni = append(pn.Azioni, AzionePiano{ID: "undo-" + a.ID, Tipo: "undo",
			Parametri:      map[string]string{"operation": in.Operazione, "action": a.ID, "purge": purgeS},
			Descrizione:    T("az.disfa", a.Descrizione),
			ComeSiFa:       a.ComeSiAnnulla,
			ComeSiVerifica: T("az.disfa.verifica"),
			ComeSiAnnulla:  a.ComeSiFa,
			Reversibilita:  a.Reversibilita})
		if a.Tipo == "start-service" && !messa {
			pn.Azioni = append(pn.Azioni, chiudi)
			messa = true
		}
	}
	if !messa {
		pn.Azioni = append([]AzionePiano{chiudi}, pn.Azioni...)
	}
	// the group enrolments made by REMOTIX at the first connection (DIRETTE), except those
	// the engine itself already has in one of its steps
	gia := map[[2]string]bool{}
	for _, a := range orig.Azioni {
		if a.Tipo == "add-user-to-group" {
			gia[[2]string{a.Parametri["user"], a.Parametri["group"]}] = true
		}
	}
	for _, k := range m.Iscrizioni() {
		if gia[k] {
			continue
		}
		pn.Azioni = append(pn.Azioni, AzionePiano{ID: "membership-" + k[0] + "-" + k[1], Tipo: "remove-membership",
			Parametri: map[string]string{"user": k[0], "group": k[1]}, Descrizione: T("az.iscrizione", k[0], k[1]),
			ComeSiFa: T("az.iscrizione.fa"), ComeSiVerifica: T("az.iscrizione.verifica"), ComeSiAnnulla: T("az.iscrizione.annulla"),
			Reversibilita: ESATTA})
	}
	// the session logs in the homes (the user's decision, 1 Oct 2026): always, last,
	// with sessions closed; the current paths are declared
	registri := RegistriUtente(m.Amb)
	pn.Azioni = append(pn.Azioni, PianoTogliRegistri("user-logs", registri))
	elenco := T("az.registri.nessuno")
	if len(registri) > 0 {
		elenco = strings.Join(registri, ", ")
	}
	pn.Dichiarate = append(pn.Dichiarate, T("az.registri.dichiarata", elenco))
	im, err := CalcolaImpronta(prof, m.Catalogo, pn.Azioni, pn.Dipende, &Contesto{Amb: m.Amb, Cartella: filepath.Join(m.Cartella, "plan-in-progress")})
	if err != nil {
		return nil, err
	}
	pn.Impronta = *im
	return pn, nil
}
