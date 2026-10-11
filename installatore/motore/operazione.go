package motore

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// Motore: an instance of the engine on the machine (or on a fake machine, in the tests).
type Motore struct {
	Amb      *Ambiente
	Cartella string        // /var/lib/remotix/operazioni (in tests, any root)
	Catalogo *Catalogo     // the one chosen and verified by phase 0 TRUST (Fonti)
	Fonti    *TrustSources // where the catalogue comes from, and what it is verified with (fiducia.go)
	Porta    int
	Esamina  func() *Profile // PREFLIGHT; nil ⇒ Preflight(Amb, …)
	Ev       *Eventi
	Adesso   func() time.Time
	// Fermata: whoever installs has asked to stop (the «Cancel and put back as it was» button of TUI and
	// GUI). It is checked between one step and the next, never in the middle of a step: the step begun finishes,
	// then the operation goes to IN_ANNULLAMENTO (RX-AZIONE-006) and everything is undone from the log.
	Fermata   func() bool
	serratura *os.File
}

// Operazione: a folder in Cartella/<id>/ with the state, the log and the objects.
type Operation struct {
	ID       string
	Cartella string
	Stato    Stato
	Reg      *Registro
	Piano    *Piano
	m        *Motore
}

// internal errors of the actions' loop
var (
	errFailed     = errors.New("an action failed")
	errConcurrent = errors.New("the machine changed during the operation")
	errStopped    = errors.New("stopped by whoever is installing")
)

func (m *Motore) adesso() time.Time {
	if m.Adesso != nil {
		return m.Adesso()
	}
	return time.Now()
}

// Profilo examines the machine (phase 1).
func (m *Motore) Profile() *Profile {
	if m.Esamina != nil {
		return m.Esamina()
	}
	return Preflight(m.Amb, PreflightOptions{Porta: m.Porta, Pacchetti: m.Catalogo.Components()})
}

// Componenti: the extra packages the catalogue wants to know whether they are there.
func (c *Catalogo) Components() []string {
	visti := map[string]bool{}
	var r []string
	for _, p := range c.Platforms {
		for _, d := range p.Desktop {
			for _, x := range d.Components {
				if !visti[x] {
					visti[x] = true
					r = append(r, x)
				}
			}
		}
	}
	sort.Strings(r)
	return r
}

// Blocca takes the engine's lock: only one at a time. The kernel releases it by itself if the
// process dies (flock), so resume never finds an orphan lock.
func (m *Motore) Blocca() error {
	if err := os.MkdirAll(m.Cartella, 0o700); err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(m.Cartella, ".serratura"), os.O_RDWR|os.O_CREATE, 0o600)
	if err != nil {
		return err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		f.Close()
		return Errore("RX-STATO-003", "")
	}
	m.serratura = f
	return nil
}

// Sblocca releases the lock.
func (m *Motore) Sblocca() {
	if m.serratura != nil {
		m.serratura.Close()
		m.serratura = nil
	}
}

// Elenco: the operations that exist, from the oldest.
func (m *Motore) List() ([]*Operation, error) {
	voci, err := os.ReadDir(m.Cartella)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var r []*Operation
	for _, v := range voci {
		if !v.IsDir() {
			continue
		}
		op, err := m.apri(v.Name())
		if err != nil {
			return nil, err
		}
		r = append(r, op)
	}
	return r, nil
}

func (m *Motore) apri(id string) (*Operation, error) {
	op := &Operation{ID: id, Cartella: filepath.Join(m.Cartella, id), m: m}
	b, err := os.ReadFile(filepath.Join(op.Cartella, "state"))
	if err != nil {
		return nil, err
	}
	op.Stato = Stato(strings.TrimSpace(string(b)))
	var p Piano
	if err := LeggiJSON(filepath.Join(op.Cartella, "plan.json"), &p); err == nil {
		op.Piano = &p
	}
	return op, nil
}

// Finita: in a state one never leaves.
func (op *Operation) Ended() (bool, error) { return Finale(op.Stato), nil }

func (op *Operation) openLog() error {
	if op.Reg != nil {
		return nil
	}
	r, avvisi, err := OpenLog(filepath.Join(op.Cartella, "log.jsonl"))
	if err != nil {
		return err
	}
	op.Reg = r
	// every program launched by the engine while the operation is open goes into the log (R41)
	if op.m.Amb != nil {
		op.m.Amb.Annota = func(riga string) { r.Scrivi(Event{Tipo: EvCommand, Detail: riga}) }
		// and what the engine says while it waits for the package manager (occupato.go)
		op.m.Amb.Avvisa = func(m Message) {
			op.m.Ev.Message(op.ID, m)
			r.Scrivi(Event{Tipo: EvNote, Codice: m.Codice, Detail: m.Detail})
		}
	}
	for _, a := range avvisi {
		op.m.Ev.Message(op.ID, a)
		if err := r.Scrivi(Event{Tipo: EvNote, Codice: a.Codice, Detail: a.Detail}); err != nil {
			return err
		}
	}
	return nil
}

// Aperta: the unfinished operation (at most one, by the rule of §6.6.2).
func (m *Motore) Aperta() (*Operation, error) {
	ops, err := m.List()
	if err != nil {
		return nil, err
	}
	var aperta *Operation
	for _, op := range ops {
		fin, err := op.Ended()
		if err != nil {
			return nil, err
		}
		if !fin {
			aperta = op
		}
	}
	return aperta, nil
}

// vai: a transition, only if it is in the design. First the state file (atomic), then the log
// line, then the event.
func (op *Operation) vai(a Stato, codice, dettaglio string) error {
	da := op.Stato
	if !Valida(da, a) {
		return Errore("RX-STATO-002", string(da)+" → "+string(a))
	}
	if err := ScriviAtomico(filepath.Join(op.Cartella, "state"), []byte(string(a)+"\n"), 0o600); err != nil {
		return err
	}
	op.Stato = a
	if err := op.Reg.Scrivi(Event{Tipo: EvState, Da: da, A: a, Codice: codice, Detail: dettaglio}); err != nil {
		return err
	}
	det := dettaglio
	if codice != "" {
		det = strings.TrimSpace(codice + " " + dettaglio)
	}
	op.m.Ev.Stato(op.ID, da, a, det)
	punto("stato:"+string(a), "")
	return nil
}

// blocca brings the operation to BLOCCATA with the error's code.
func (op *Operation) blocca(err error) error {
	codice := CodeOf(err)
	det := err.Error()
	var e *ErrorRX
	if errors.As(err, &e) {
		op.m.Ev.Message(op.ID, e.M)
		det = e.M.Detail
	}
	if e2 := op.vai(BLOCCATA, codice, det); e2 != nil {
		return e2
	}
	return err
}

func (op *Operation) writeObject(nome string, v any) error {
	p := filepath.Join(op.Cartella, nome)
	if err := WriteJSON(p, v); err != nil {
		return err
	}
	op.m.Ev.Object(op.ID, strings.TrimSuffix(nome, ".json"), p)
	return nil
}

// Applica: phases 0-8 of the plan (§6.0), on the plan's actions only. approveManually = the consent
// given now by whoever launches the command (--approva), which is recorded as such.
func (m *Motore) Applica(planPath string, approveManually bool, chi string) (*Operation, error) {
	if err := m.Blocca(); err != nil {
		return nil, err
	}
	defer m.Sblocca()
	if ap, err := m.Aperta(); err != nil {
		return nil, err
	} else if ap != nil {
		return nil, Errore("RX-STATO-001", ap.ID+" is "+string(ap.Stato))
	}
	var piano Piano
	if err := LeggiJSON(planPath, &piano); err != nil || piano.Object != "plan" {
		if err == nil {
			err = fmt.Errorf("not a plan: object %q", piano.Object)
		}
		return nil, Errore("RX-PIANO-002", err.Error())
	}

	// NEW
	op := &Operation{ID: nuovoID(), m: m, Piano: &piano}
	op.Cartella = filepath.Join(m.Cartella, op.ID)
	if err := os.Mkdir(op.Cartella, 0o700); err != nil {
		return nil, err
	}
	if err := SyncFolder(m.Cartella); err != nil {
		return nil, err
	}
	if err := ScriviAtomico(filepath.Join(op.Cartella, "state"), []byte(string(NUOVA)+"\n"), 0o600); err != nil {
		return nil, err
	}
	op.Stato = NUOVA
	if err := op.openLog(); err != nil {
		return nil, err
	}
	if err := op.Reg.Scrivi(Event{Tipo: EvState, A: NUOVA, Detail: "plan " + piano.ID}); err != nil {
		return nil, err
	}
	m.Ev.Stato(op.ID, "", NUOVA, T("ev.operazione", op.ID))
	if err := op.writeObject("plan.json", &piano); err != nil {
		return nil, err
	}

	// 0 TRUST
	if m.Fonti == nil {
		return op, op.blocca(Errore("RX-TRUST-004", "no catalogue source"))
	}
	cat, fid, err := m.Fonti.Trusted(m.adesso())
	if e := op.writeObject("trust.json", fid); e != nil {
		return op, e
	}
	for _, x := range fid.Messages {
		m.Ev.Message(op.ID, x)
	}
	if err != nil {
		return op, op.blocca(err)
	}
	m.Catalogo = cat
	if err := op.vai(FIDATA, "", fmt.Sprintf("catalog %s (sequence %d): %s", cat.Version, cat.Sequence, fid.Source)); err != nil {
		return op, err
	}

	// 1 PREFLIGHT
	prof := m.Profile()
	if err := op.writeObject("profile.json", prof); err != nil {
		return op, err
	}
	if err := op.vai(ESAMINATA, "", ""); err != nil {
		return op, err
	}

	// 2 COMPATIBILITY
	rap := Valuta(m.Catalogo, prof)
	if err := op.writeObject("compatibility.json", rap); err != nil {
		return op, err
	}
	if err := op.vai(VALUTATA, "", ""); err != nil {
		return op, err
	}

	// 3 PLANNING: does the plan hold on this machine? (fingerprint, R31)
	for _, ap := range piano.Azioni {
		if _, err := NewAction(ap); err != nil {
			return op, op.blocca(err)
		}
	}
	im, err := CalcolaImpronta(prof, m.Catalogo, piano.Azioni, piano.Depends, &Contesto{Amb: m.Amb, Cartella: op.Cartella})
	if err != nil {
		return op, op.blocca(err)
	}
	if im.Digest != piano.Impronta.Digest {
		tolti, aggiunti := FingerprintDifferences(piano.Impronta.Elements, im.Elements)
		det := "in the plan: " + strings.Join(tolti, "; ") + " — now: " + strings.Join(aggiunti, "; ")
		if err := op.writeObject("fingerprint-now.json", im); err != nil {
			return op, err
		}
		return op, op.blocca(Errore("RX-PIANO-001", det))
	}
	if err := op.vai(PIANIFICATA, "", "fingerprint "+im.Digest[:16]); err != nil {
		return op, err
	}

	// 4 CONSENT & SAFETY
	// what is missing (DECISIONI §10.36): the plan says it BLOCKING, and we stop before touching
	for _, x := range piano.NotDone {
		if x.Severity == BLOCCANTE {
			m.Ev.Message(op.ID, x)
			return op, op.vai(BLOCCATA, x.Codice, x.Detail)
		}
	}
	appr := piano.Approval
	switch {
	case appr != nil && appr.DigestPiano != piano.Digest():
		m.Ev.Message(op.ID, Msg("RX-PIANO-005", ""))
		return op, op.vai(RIFIUTATA, "RX-PIANO-005", "")
	case appr == nil && !approveManually:
		m.Ev.Message(op.ID, Msg("RX-PIANO-003", ""))
		return op, op.vai(RIFIUTATA, "RX-PIANO-003", "")
	case appr == nil:
		appr = &Approval{Da: chi, Ora: ora(), Modo: "by hand, --approve", DigestPiano: piano.Digest()}
	}
	if err := op.writeObject("approval.json", appr); err != nil {
		return op, err
	}
	if err := op.vai(APPROVATA, "", appr.Modo+", by "+appr.Da); err != nil {
		return op, err
	}

	// the steps the engine knows but cannot execute yet: we stop BEFORE touching
	if nf := UnimplementedSteps(&piano); len(nf) > 0 {
		return op, op.blocca(Errore("RX-AZIONE-004", strings.Join(nf, "; ")))
	}

	// 5 ACQUISITION: the trial actions ask for no packages; the resolved set is empty but there.
	if err := op.writeObject("resolved-set.json", map[string]any{"format": Formato, "object": "resolved-set", "artifacts": []any{}}); err != nil {
		return op, err
	}
	if err := op.vai(ACQUISITA, "", ""); err != nil {
		return op, err
	}

	// 6 INSTALLATION
	if err := op.vai(IN_ESECUZIONE, "", ""); err != nil {
		return op, err
	}
	return op, op.continua()
}

// Riprendi: an interrupted operation is completed (§6.0 point 6, table of §6.6.3).
func (m *Motore) Riprendi() (*Operation, error) {
	if err := m.Blocca(); err != nil {
		return nil, err
	}
	defer m.Sblocca()
	op, err := m.Aperta()
	if err != nil {
		return nil, err
	}
	if op == nil {
		return nil, Errore("RX-STATO-004", "")
	}
	if err := op.openLog(); err != nil {
		return op, err
	}
	m.Ev.Stato(op.ID, op.Stato, op.Stato, T("ev.si_riprende"))
	switch op.Stato {
	case NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA:
		m.Ev.Message(op.ID, Msg("RX-RIPRESA-002", string(op.Stato)))
		return op, op.vai(BLOCCATA, "RX-RIPRESA-002", "was "+string(op.Stato))
	case IN_ESECUZIONE:
		if err := op.vai(INTERROTTA, "", ""); err != nil {
			return op, err
		}
		fallthrough
	case INTERROTTA:
		if err := op.vai(IN_ESECUZIONE, "", "resume"); err != nil {
			return op, err
		}
	}
	return op, op.continua()
}

// Annulla: the open operation is undone by walking the log backwards.
func (m *Motore) Annulla() (*Operation, error) {
	if err := m.Blocca(); err != nil {
		return nil, err
	}
	defer m.Sblocca()
	op, err := m.Aperta()
	if err != nil {
		return nil, err
	}
	if op == nil {
		return nil, Errore("RX-STATO-004", "")
	}
	if err := op.openLog(); err != nil {
		return op, err
	}
	switch op.Stato {
	case NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA:
		m.Ev.Message(op.ID, Msg("RX-RIPRESA-002", string(op.Stato)))
		return op, op.vai(BLOCCATA, "RX-RIPRESA-002", string(op.Stato))
	case IN_ESECUZIONE:
		if err := op.vai(INTERROTTA, "", ""); err != nil {
			return op, err
		}
		fallthrough
	case INTERROTTA, APPLICATA, IN_VERIFICA, VERIFICATA:
		if err := op.vai(IN_ANNULLAMENTO, "", T("op.chiesto")); err != nil {
			return op, err
		}
	}
	return op, op.continua()
}

// continua brings the operation from its current state to a final state (or INTERROTTA).
func (op *Operation) continua() error {
	for {
		switch op.Stato {
		case IN_ESECUZIONE:
			err := op.eseguiTutte()
			switch {
			case errors.Is(err, errConcurrent):
				return op.vai(INTERROTTA, "RX-RIPRESA-001", op.lastDetail())
			case errors.Is(err, errStopped):
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-006", ""))
				if err := op.vai(IN_ANNULLAMENTO, "RX-AZIONE-006", ""); err != nil {
					return err
				}
			case errors.Is(err, errFailed):
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-001", op.lastDetail()))
				if err := op.vai(IN_ANNULLAMENTO, "RX-AZIONE-001", op.lastDetail()); err != nil {
					return err
				}
			case err != nil:
				return err
			default:
				if err := op.vai(APPLICATA, "", ""); err != nil {
					return err
				}
			}
		case APPLICATA:
			if err := op.vai(IN_VERIFICA, "", ""); err != nil {
				return err
			}
		case IN_VERIFICA:
			ok, err := op.verifica()
			if err != nil {
				return err
			}
			if ok {
				if err := op.vai(VERIFICATA, "", ""); err != nil {
					return err
				}
			} else {
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-003", ""))
				if err := op.vai(IN_ANNULLAMENTO, "RX-AZIONE-003", ""); err != nil {
					return err
				}
			}
		case VERIFICATA:
			cond := op.condizioni()
			fin := CONFERMATA
			if len(cond) > 0 {
				fin = CONFERMATA_A_CONDIZIONI
			}
			// the certificate BEFORE the final state: if the process dies in between, resume
			// finds VERIFICATA and rewrites it; the other way round there would be a final state without a certificate
			if err := op.certificato(fin, nil); err != nil {
				return err
			}
			if err := op.writeInstallation(fin); err != nil {
				return err
			}
			if op.Piano.Duty == "uninstallation" {
				if err := os.Remove(op.m.InstallPath()); err != nil && !os.IsNotExist(err) {
					return err
				}
			}
			if err := op.vai(fin, "", ""); err != nil {
				return err
			}
			if op.Piano.Duty == "uninstallation" {
				return op.m.CleanHistory(op.Piano.Purge)
			}
			return nil
		case IN_ANNULLAMENTO:
			resti, err := op.annullaTutte()
			if err != nil {
				return err
			}
			fin := ANNULLATA
			if len(resti) > 0 {
				fin = ANNULLATA_IN_PARTE
				op.m.Ev.Message(op.ID, Msg("RX-AZIONE-002", strings.Join(resti, "; ")))
			}
			if err := op.certificato(fin, resti); err != nil {
				return err
			}
			return op.vai(fin, "", "")
		default:
			return nil
		}
	}
}

func (op *Operation) lastDetail() string {
	for i := len(op.Reg.Eventi) - 1; i >= 0; i-- {
		e := op.Reg.Eventi[i]
		if e.Tipo == EvFailed || (e.Tipo == EvNote && e.Codice == "RX-RIPRESA-001") {
			return strings.TrimSpace(e.Azione + ": " + e.Detail)
		}
	}
	return ""
}

// contesto: rolling back an installation is always purge — the
// machine as it was; the uninstallation carries its «purge» in the parameters of the undo steps.
func (op *Operation) contesto(ap AzionePiano) *Contesto {
	return &Contesto{Amb: op.m.Amb, Cartella: op.Cartella, P: ap, Purge: true}
}

func (op *Operation) fallita(ap AzionePiano, err error) error {
	codice := CodeOf(err)
	if codice == "" {
		codice = "RX-AZIONE-001"
	}
	if e := op.Reg.Scrivi(Event{Tipo: EvFailed, Azione: ap.ID, Codice: codice, Detail: err.Error()}); e != nil {
		return e
	}
	op.m.Ev.Azione(op.ID, ap.ID, "FAILED", err.Error())
	return errFailed
}

func (op *Operation) concurrent(ap AzionePiano, det string) error {
	if e := op.Reg.Scrivi(Event{Tipo: EvNote, Azione: ap.ID, Codice: "RX-RIPRESA-001", Detail: det}); e != nil {
		return e
	}
	op.m.Ev.Message(op.ID, Msg("RX-RIPRESA-001", ap.ID+": "+det))
	return errConcurrent
}

// fatta: checks and records FATTA.
func (op *Operation) fatta(az Azione, ap AzionePiano, prima json.RawMessage, nota string) error {
	esito, det, err := az.Controlla(op.contesto(ap), prima)
	if err != nil {
		return op.fallita(ap, err)
	}
	if esito != COMPLETO {
		return op.fallita(ap, Errore("RX-AZIONE-003", string(esito)+": "+det))
	}
	if err := op.Reg.Scrivi(Event{Tipo: EvDone, Azione: ap.ID, Dopo: jsonDi(map[string]string{"result": string(esito), "detail": det}), Detail: nota}); err != nil {
		return err
	}
	op.m.Ev.Azione(op.ID, ap.ID, "DONE", strings.TrimSpace(nota+" "+det))
	punto("dopo-fatta", ap.ID)
	return nil
}

// eseguiTutte: phase 6 with the write-ahead log, and the resume of the table of
// §6.6.3 (the same road: a new operation is a resume with an empty log).
func (op *Operation) eseguiTutte() error {
	for _, ap := range op.Piano.Azioni {
		az, err := NewAction(ap)
		if err != nil {
			return op.fallita(ap, err)
		}
		c := op.contesto(ap)
		ult := op.Reg.Last(ap.ID, EvIntent, EvDone, EvFailed)
		if ult == nil && op.m.Fermata != nil && op.m.Fermata() {
			return errStopped
		}
		switch {
		case ult == nil: // nothing in the log: not begun ⇒ do it
			punto("prima-intenzione", ap.ID)
			prima, orig, err := az.Fotografa(c)
			if err != nil {
				return op.fallita(ap, err)
			}
			if err := op.Reg.Scrivi(Event{Tipo: EvIntent, Azione: ap.ID, Prima: prima, Origine: orig}); err != nil {
				return err
			}
			op.m.Ev.Azione(op.ID, ap.ID, "INTENT", string(orig))
			punto("dopo-intenzione", ap.ID)
			if err := az.Fai(c, prima); err != nil {
				return op.fallita(ap, err)
			}
			punto("dopo-effetto", ap.ID)
			if err := op.fatta(az, ap, prima, ""); err != nil {
				return err
			}

		case ult.Tipo == EvIntent: // begun: maybe finished, maybe not, maybe half-done
			prima := op.Reg.Intenzione(ap.ID).Prima
			esito, det, err := az.Controlla(c, prima)
			if err != nil {
				return op.fallita(ap, err)
			}
			op.m.Ev.Azione(op.ID, ap.ID, "RESUMED", string(esito)+": "+det)
			switch esito {
			case COMPLETO:
				if err := op.fatta(az, ap, prima, "resumed: the effect was already there"); err != nil {
					return err
				}
				continue
			case A_META:
				// the package manager's transaction: first ITS remedy (§6.6.3), then redo;
				// the other actions: undo what is there and redo
				if r, ok := az.(Riparabile); ok {
					if err := r.Repair(c, prima); err != nil {
						return op.fallita(ap, err)
					}
				} else if err := az.Annulla(c, prima); err != nil {
					return op.fallita(ap, err)
				}
			case ESTRANEO:
				return op.concurrent(ap, det)
			}
			if err := az.Fai(c, prima); err != nil {
				return op.fallita(ap, err)
			}
			if err := op.fatta(az, ap, prima, "resumed: done again"); err != nil {
				return err
			}

		case ult.Tipo == EvDone: // finished and recorded: move on, but the effect must still be there
			prima := op.Reg.Intenzione(ap.ID).Prima
			esito, det, err := az.Controlla(c, prima)
			if err != nil {
				return op.fallita(ap, err)
			}
			if esito != COMPLETO {
				return op.concurrent(ap, "was FATTA, now "+string(esito)+": "+det)
			}

		case ult.Tipo == EvFailed:
			return errFailed
		}
	}
	return nil
}

// annullaTutte walks the actions backwards. Returns what could not be undone.
func (op *Operation) annullaTutte() ([]string, error) {
	var resti []string
	az := op.Piano.Azioni
	for i := len(az) - 1; i >= 0; i-- {
		ap := az[i]
		intent := op.Reg.Intenzione(ap.ID)
		if intent == nil {
			continue // never begun: nothing to undo
		}
		if u := op.Reg.Last(ap.ID, EvIntentRollback, EvCancelled, EvRollbackFailed); u != nil && u.Tipo == EvCancelled {
			continue
		}
		a, err := NewAction(ap)
		if err != nil {
			return nil, err
		}
		c := op.contesto(ap)
		scrivi := func(t EventType, codice, det string) error {
			op.m.Ev.Azione(op.ID, ap.ID, string(t), det)
			return op.Reg.Scrivi(Event{Tipo: t, Azione: ap.ID, Codice: codice, Detail: det})
		}
		if intent.Origine == PREESISTENTE {
			if err := scrivi(EvCancelled, "", "PREEXISTING: left untouched"); err != nil {
				return nil, err
			}
			continue
		}
		if ok, det, err := a.Annullata(c, intent.Prima); err == nil && ok {
			if err := scrivi(EvCancelled, "", "nothing to undo: "+det); err != nil {
				return nil, err
			}
			continue
		}
		if esito, det, err := a.Controlla(c, intent.Prima); err == nil && esito == ESTRANEO {
			resti = append(resti, ap.ID+": changed by someone else, left untouched ("+det+")")
			if err := scrivi(EvRollbackFailed, "RX-RIPRESA-001", "CONCURRENT: "+det); err != nil {
				return nil, err
			}
			continue
		}
		if err := scrivi(EvIntentRollback, "", ""); err != nil {
			return nil, err
		}
		punto("annulla-dopo-intenzione", ap.ID)
		errA := a.Annulla(c, intent.Prima)
		punto("annulla-dopo-effetto", ap.ID)
		ok, det, errB := a.Annullata(c, intent.Prima)
		if errA == nil && errB == nil && ok {
			if err := scrivi(EvCancelled, "", det); err != nil {
				return nil, err
			}
			continue
		}
		motivo := det
		if errA != nil {
			motivo = errA.Error()
		} else if errB != nil {
			motivo = errB.Error()
		}
		resti = append(resti, ap.ID+": "+motivo)
		if err := scrivi(EvRollbackFailed, "RX-AZIONE-002", motivo); err != nil {
			return nil, err
		}
	}
	return resti, nil
}

// Controllo: a line of the verification report (§6.6.7).
type Controllo struct {
	ID        string `json:"id"`
	Cosa      string `json:"what"`
	Esito     string `json:"result"` // PASS · FAIL · UNKNOWN · N.A.
	Requested bool   `json:"required"`
	Detail    string `json:"detail,omitempty"`
}

// VerifyReport: the sixth object.
type VerifyReport struct {
	Formato    string      `json:"format"`
	Object     string      `json:"object"`
	Created    string      `json:"created"`
	Checks     []Controllo `json:"checks"`
	Condizioni []Condition `json:"conditions,omitempty"` // those born from verification (a declared UNKNOWN)
}

// verifica (phase 7, here reduced to the trial actions): every action rechecked. ⛔ UNKNOWN is not
// PASS: a required check that cannot answer leads to cancellation (the trial actions
// have no declared fallback).
func (op *Operation) verifica() (bool, error) {
	rv := VerifyReport{Formato: Formato, Object: "check", Created: ora()}
	tutto := true
	for _, ap := range op.Piano.Azioni {
		a, err := NewAction(ap)
		if err != nil {
			return false, err
		}
		k := Controllo{ID: ap.ID, Cosa: ap.HowToVerify, Requested: true}
		intent := op.Reg.Intenzione(ap.ID)
		if intent == nil {
			k.Esito, k.Detail = "UNKNOWN", "no intention in the log"
		} else if esito, det, err := a.Controlla(op.contesto(ap), intent.Prima); err != nil {
			k.Esito, k.Detail = "UNKNOWN", err.Error()
		} else if esito == COMPLETO {
			k.Esito, k.Detail = "PASS", det
		} else {
			k.Esito, k.Detail = "FAIL", string(esito)+": "+det
		}
		if k.Esito != "PASS" {
			tutto = false
		}
		rv.Checks = append(rv.Checks, k)
	}
	// 7a: H.264 encoding is tested by REMOTIX itself (§6.5-bis). Required: FAIL (no card that
	// encodes: phase 19, no fallback) ⇒ cancellation; UNKNOWN ⇒ CONFERMATA_A_CONDIZIONI, never PASS
	// (§6.6.7).
	// and the PAM stack that resolves, and the port the firewall lets through (certifica.go, R29)
	if op.Piano.Duty == "installation" {
		porta := op.m.Porta
		for _, ap := range op.Piano.Azioni {
			if ap.Tipo == "start-service" {
				if n, err := strconv.Atoi(ap.Parametri["port"]); err == nil && n > 0 {
					porta = n
				}
			}
		}
		if porta == 0 {
			porta = 7447
		}
		k, cond, fallito := ControlliPiattaforma(op.m.Amb, porta)
		rv.Checks = append(rv.Checks, k...)
		rv.Condizioni = append(rv.Condizioni, cond...)
		if fallito {
			tutto = false
		}
	}
	return tutto, op.writeObject("check.json", rv)
}

// provaCodifica: `remotix --prova-codifica` (§6.5-bis; phase 19, no fallback to the processor): one
// JSON line {"esito":"hardware"|"nessuno","codificatore":…,"strada":"vulkan"|"vaapi"|"","nodo":…,
// "motivo":…,"codec":…,"offerti":…,"hevc":…,"h264":…,"hevc_strada":…,"h264_strada":…}; exit 0 if the card encoded the frame, 3 if NO
// card can encode (the encoder does not open: no node, no driver, driver without
// encoding — the declared refusal), 1 if the card opens but the frame does not come out, 2 usage
// error. The engine launches it as root (closed list). hardware ⇒ PASS; 3 or 1 ⇒ FAIL; a binary that
// does not know it or an unreadable answer ⇒ UNKNOWN (§6.6.7).
func provaCodifica(a *Ambiente) (Controllo, *Condition) {
	k := Controllo{ID: "h264-encoding", Cosa: "remotix --prova-codifica (7a)", Requested: true}
	out, c, err := a.Esegui(2*time.Minute, "remotix", "--prova-codifica")
	var r struct {
		Esito, Codificatore, Strada, Nodo, Motivo, Codec string
	}
	letto := false
	for _, riga := range strings.Split(out, "\n") {
		if strings.HasPrefix(strings.TrimSpace(riga), "{") && json.Unmarshal([]byte(riga), &r) == nil && r.Esito != "" {
			letto = true
		}
	}
	// ⭐ phase 19: `strada` says WHICH route of the card did the encoding (vulkan/vaapi); a binary
	// that does not write it (phase 18) passes all the same: the outcome is what counts
	det := strings.Join(strings.Fields(r.Esito+" "+r.Codec+" "+r.Codificatore+" "+r.Strada+" "+r.Nodo+" "+r.Motivo), " ")
	switch {
	case err != nil:
		k.Esito, k.Detail = "UNKNOWN", err.Error()
	case !letto || c == 2:
		k.Esito, k.Detail = "UNKNOWN", T("ver.codifica_assente")+": "+lastLines(out, 2)
	case c == 0 && r.Esito == "hardware":
		k.Esito, k.Detail = "PASS", det
	case c == 3:
		k.Esito, k.Detail = "FAIL", T("ver.nessuna_scheda", notEmpty(r.Motivo, det))
	default:
		k.Esito, k.Detail = "FAIL", det
	}
	if k.Esito == "UNKNOWN" {
		return k, &Condition{Codice: "C-LIMITE", Testo: T("cond.codifica_ignota", k.Detail)}
	}
	return k, nil
}

func (op *Operation) condizioni() []Condition {
	if op.Piano.Duty == "uninstallation" {
		return nil
	}
	var c []Condition
	var rv VerifyReport
	if LeggiJSON(filepath.Join(op.Cartella, "check.json"), &rv) == nil {
		c = append(c, rv.Condizioni...)
	}
	var r Rapporto
	if err := LeggiJSON(filepath.Join(op.Cartella, "compatibility.json"), &r); err != nil {
		return c
	}
	for _, e := range r.Desktop {
		if e.Level != NON_SUPPORTATA && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			c = append(c, e.Condizioni...)
		}
	}
	return c
}

// Certificato: the seventh object (§6.6.11).
type Certificate struct {
	Formato        string      `json:"format"`
	Object         string      `json:"object"`
	Created        string      `json:"created"`
	Operation      string      `json:"operation"`
	Stato          Stato       `json:"state"`
	Duty           string      `json:"kind"`
	Product        string      `json:"product"`
	Motore         EngineRef   `json:"engine"`
	Catalogo       CatalogRef  `json:"catalog"`
	Attestation    string      `json:"trust"`
	DigestPiano    string      `json:"digest_plan"`
	DigestTogether string      `json:"digest_resolved_set"`
	Impronta       string      `json:"fingerprint"`
	Checks         []Controllo `json:"checks"`
	Condizioni     []Condition `json:"conditions"`
	Remainders     []string    `json:"leftovers,omitempty"` // ANNULLATA_IN_PARTE: what remains, and why
	Indirect       []string    `json:"indirect"`            // INDIRECT changes declared (none, without packages)
}

func (op *Operation) certificato(fin Stato, resti []string) error {
	var fid Attestation
	LeggiJSON(filepath.Join(op.Cartella, "trust.json"), &fid)
	var rv VerifyReport
	LeggiJSON(filepath.Join(op.Cartella, "check.json"), &rv)
	ins, _ := Sha256File(filepath.Join(op.Cartella, "resolved-set.json"))
	fiducia := T("cert.fiducia_no")
	if fid.Catalogo.Digest != "" && len(fid.Messages) == 0 {
		fiducia = fmt.Sprintf("%s (sequence %d)", fid.Source, fid.Sequence)
	}
	c := Certificate{Formato: Formato, Object: "certificate", Created: ora(), Operation: op.ID, Stato: fin,
		Duty: op.Piano.Duty, Product: T("cert.prodotto_prova"),
		Motore: EngineRef{VersioneMotore, EngineDigest()}, Catalogo: fid.Catalogo, Attestation: fiducia,
		DigestPiano: op.Piano.Digest(), DigestTogether: ins, Impronta: op.Piano.Impronta.Digest,
		Checks: rv.Checks, Condizioni: op.condizioni(), Remainders: resti, Indirect: op.indirect()}
	if c.Condizioni == nil {
		c.Condizioni = []Condition{}
	}
	if err := op.writeObject("certificate.json", c); err != nil {
		return err
	}
	var t strings.Builder
	fmt.Fprintf(&t, "%s\n\n%s: %s\n%s: %s\n%s: %s (%s)\n%s: %s (%s)\n%s: %s\n%s: %s\n%s: %s\n",
		T("cert.titolo", op.ID), T("cert.stato"), c.Stato, T("cert.mestiere"), c.Duty, T("cert.motore"), c.Motore.Version, c.Motore.Digest,
		T("cert.catalogo"), c.Catalogo.Version, c.Catalogo.Digest, T("cert.fiducia"), c.Attestation, T("cert.piano"), c.DigestPiano, T("cert.impronta"), c.Impronta)
	fmt.Fprintf(&t, "\n%s:\n", T("cert.controlli"))
	for _, k := range c.Checks {
		fmt.Fprintf(&t, "  %-8s %s — %s\n", k.Esito, k.ID, k.Detail)
	}
	fmt.Fprintf(&t, "\n%s:\n", T("cert.condizioni"))
	if len(c.Condizioni) == 0 {
		fmt.Fprintf(&t, "  %s\n", T("cert.nessuna"))
	}
	for _, k := range c.Condizioni {
		fmt.Fprintf(&t, "  %s %s\n", k.Codice, k.Testo)
	}
	if len(resti) > 0 {
		fmt.Fprintf(&t, "\n%s:\n", T("cert.non_annullato"))
		for _, r := range resti {
			fmt.Fprintf(&t, "  %s\n", r)
		}
	}
	return ScriviAtomico(filepath.Join(op.Cartella, "certificate.txt"), []byte(t.String()), 0o600)
}

// Installazione: the state REMOTIX checks at start-up (DECISIONI §10.12: the installer is the
// only way; the service does not start without a CONFERMATA operation, RX-INST-001). It sits next to
// the operations folder: /var/lib/remotix/installazione.json.
type Installation struct {
	Formato     string `json:"format"`
	Object      string `json:"object"` // "installation"
	Operation   string `json:"operation"`
	Stato       Stato  `json:"state"`
	Duty        string `json:"kind"`
	Certificate string `json:"certificate"`
	Written     string `json:"written"`
}

// InstallPath: next to the operations folder.
func (m *Motore) InstallPath() string {
	return filepath.Join(filepath.Dir(m.Cartella), "installation.json")
}

// writeInstallation: only for the kinds that really install the product. The trial plan
// of T4 does not write it: it did not install REMOTIX.
func (op *Operation) writeInstallation(fin Stato) error {
	if op.Piano.Duty != "installation" {
		return nil
	}
	return WriteJSON(op.m.InstallPath(), Installation{Formato: Formato, Object: "installation",
		Operation: op.ID, Stato: fin, Duty: op.Piano.Duty,
		Certificate: filepath.Join(op.Cartella, "certificate.json"), Written: ora()})
}

// CheckInstallation: what REMOTIX (and remotix-install aggiornato) asks at start-up.
// It holds only if the file is there, the operation it names exists and is CONFERMATA (even conditionally).
func (m *Motore) CheckInstallation() (*Installation, error) {
	var in Installation
	if err := LeggiJSON(m.InstallPath(), &in); err != nil {
		return nil, Errore("RX-INST-001", err.Error())
	}
	op, err := m.apri(in.Operation)
	if err != nil {
		return nil, Errore("RX-INST-001", "operation "+in.Operation+" does not exist")
	}
	if op.Stato != CONFERMATA && op.Stato != CONFERMATA_A_CONDIZIONI {
		return nil, Errore("RX-INST-001", "operation "+in.Operation+" is "+string(op.Stato))
	}
	return &in, nil
}

// indirette: what happened indirectly and remains (§6.6.4): the actions declare it; and the
// packages held back by an undo step (RX-PACCHETTI-006), which says so in its FATTA.
func (op *Operation) indirect() []string {
	r := []string{}
	for _, e := range op.Reg.Eventi {
		var d map[string]string
		if e.Tipo == EvDone && json.Unmarshal(e.Dopo, &d) == nil && strings.Contains(d["detail"], "[RX-PACCHETTI-006]") {
			_, x, _ := strings.Cut(d["detail"], "[RX-PACCHETTI-006] ")
			r = append(r, "RX-PACCHETTI-006 "+e.Azione+": "+x)
		}
	}
	for _, ap := range op.Piano.Azioni {
		intent := op.Reg.Intenzione(ap.ID)
		if intent == nil {
			continue
		}
		a, err := NewAction(ap)
		if err != nil {
			continue
		}
		if d, ok := a.(Declarer); ok {
			r = append(r, d.Indirect(intent.Prima)...)
		}
	}
	return r
}
