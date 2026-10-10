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
	Fonti    *FontiFiducia // where the catalogue comes from, and what it is verified with (fiducia.go)
	Porta    int
	Esamina  func() *Profilo // PREFLIGHT; nil ⇒ Preflight(Amb, …)
	Ev       *Eventi
	Adesso   func() time.Time
	// Fermata: whoever installs has asked to stop (the «Cancel and put back as it was» button of TUI and
	// GUI). It is checked between one step and the next, never in the middle of a step: the step begun finishes,
	// then the operation goes to IN_ANNULLAMENTO (RX-AZIONE-006) and everything is undone from the log.
	Fermata   func() bool
	serratura *os.File
}

// Operazione: a folder in Cartella/<id>/ with the state, the log and the objects.
type Operazione struct {
	ID       string
	Cartella string
	Stato    Stato
	Reg      *Registro
	Piano    *Piano
	m        *Motore
}

// internal errors of the actions' loop
var (
	errFallita     = errors.New("an action failed")
	errConcorrente = errors.New("the machine changed during the operation")
	errFermata     = errors.New("stopped by whoever is installing")
)

func (m *Motore) adesso() time.Time {
	if m.Adesso != nil {
		return m.Adesso()
	}
	return time.Now()
}

// Profilo examines the machine (phase 1).
func (m *Motore) Profilo() *Profilo {
	if m.Esamina != nil {
		return m.Esamina()
	}
	return Preflight(m.Amb, OpzioniPreflight{Porta: m.Porta, Pacchetti: m.Catalogo.Componenti()})
}

// Componenti: the extra packages the catalogue wants to know whether they are there.
func (c *Catalogo) Componenti() []string {
	visti := map[string]bool{}
	var r []string
	for _, p := range c.Piattaforme {
		for _, d := range p.Desktop {
			for _, x := range d.Componenti {
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
func (m *Motore) Elenco() ([]*Operazione, error) {
	voci, err := os.ReadDir(m.Cartella)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var r []*Operazione
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

func (m *Motore) apri(id string) (*Operazione, error) {
	op := &Operazione{ID: id, Cartella: filepath.Join(m.Cartella, id), m: m}
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
func (op *Operazione) Finita() (bool, error) { return Finale(op.Stato), nil }

func (op *Operazione) apriRegistro() error {
	if op.Reg != nil {
		return nil
	}
	r, avvisi, err := ApriRegistro(filepath.Join(op.Cartella, "log.jsonl"))
	if err != nil {
		return err
	}
	op.Reg = r
	// every program launched by the engine while the operation is open goes into the log (R41)
	if op.m.Amb != nil {
		op.m.Amb.Annota = func(riga string) { r.Scrivi(Evento{Tipo: EvComando, Dettaglio: riga}) }
	}
	for _, a := range avvisi {
		op.m.Ev.Messaggio(op.ID, a)
		if err := r.Scrivi(Evento{Tipo: EvNota, Codice: a.Codice, Dettaglio: a.Dettaglio}); err != nil {
			return err
		}
	}
	return nil
}

// Aperta: the unfinished operation (at most one, by the rule of §6.6.2).
func (m *Motore) Aperta() (*Operazione, error) {
	ops, err := m.Elenco()
	if err != nil {
		return nil, err
	}
	var aperta *Operazione
	for _, op := range ops {
		fin, err := op.Finita()
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
func (op *Operazione) vai(a Stato, codice, dettaglio string) error {
	da := op.Stato
	if !Valida(da, a) {
		return Errore("RX-STATO-002", string(da)+" → "+string(a))
	}
	if err := ScriviAtomico(filepath.Join(op.Cartella, "state"), []byte(string(a)+"\n"), 0o600); err != nil {
		return err
	}
	op.Stato = a
	if err := op.Reg.Scrivi(Evento{Tipo: EvStato, Da: da, A: a, Codice: codice, Dettaglio: dettaglio}); err != nil {
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
func (op *Operazione) blocca(err error) error {
	codice := CodiceDi(err)
	det := err.Error()
	var e *ErroreRX
	if errors.As(err, &e) {
		op.m.Ev.Messaggio(op.ID, e.M)
		det = e.M.Dettaglio
	}
	if e2 := op.vai(BLOCCATA, codice, det); e2 != nil {
		return e2
	}
	return err
}

func (op *Operazione) scriviOggetto(nome string, v any) error {
	p := filepath.Join(op.Cartella, nome)
	if err := ScriviJSON(p, v); err != nil {
		return err
	}
	op.m.Ev.Oggetto(op.ID, strings.TrimSuffix(nome, ".json"), p)
	return nil
}

// Applica: phases 0-8 of the plan (§6.0), on the plan's actions only. approvaAMano = the consent
// given now by whoever launches the command (--approva), which is recorded as such.
func (m *Motore) Applica(percorsoPiano string, approvaAMano bool, chi string) (*Operazione, error) {
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
	if err := LeggiJSON(percorsoPiano, &piano); err != nil || piano.Oggetto != "plan" {
		if err == nil {
			err = fmt.Errorf("not a plan: object %q", piano.Oggetto)
		}
		return nil, Errore("RX-PIANO-002", err.Error())
	}

	// NEW
	op := &Operazione{ID: nuovoID(), m: m, Piano: &piano}
	op.Cartella = filepath.Join(m.Cartella, op.ID)
	if err := os.Mkdir(op.Cartella, 0o700); err != nil {
		return nil, err
	}
	if err := SincronizzaCartella(m.Cartella); err != nil {
		return nil, err
	}
	if err := ScriviAtomico(filepath.Join(op.Cartella, "state"), []byte(string(NUOVA)+"\n"), 0o600); err != nil {
		return nil, err
	}
	op.Stato = NUOVA
	if err := op.apriRegistro(); err != nil {
		return nil, err
	}
	if err := op.Reg.Scrivi(Evento{Tipo: EvStato, A: NUOVA, Dettaglio: "plan " + piano.ID}); err != nil {
		return nil, err
	}
	m.Ev.Stato(op.ID, "", NUOVA, T("ev.operazione", op.ID))
	if err := op.scriviOggetto("plan.json", &piano); err != nil {
		return nil, err
	}

	// 0 TRUST
	if m.Fonti == nil {
		return op, op.blocca(Errore("RX-TRUST-004", "no catalogue source"))
	}
	cat, fid, err := m.Fonti.Fidati(m.adesso())
	if e := op.scriviOggetto("trust.json", fid); e != nil {
		return op, e
	}
	for _, x := range fid.Messaggi {
		m.Ev.Messaggio(op.ID, x)
	}
	if err != nil {
		return op, op.blocca(err)
	}
	m.Catalogo = cat
	if err := op.vai(FIDATA, "", fmt.Sprintf("catalog %s (sequence %d): %s", cat.Versione, cat.Sequenza, fid.Fonte)); err != nil {
		return op, err
	}

	// 1 PREFLIGHT
	prof := m.Profilo()
	if err := op.scriviOggetto("profile.json", prof); err != nil {
		return op, err
	}
	if err := op.vai(ESAMINATA, "", ""); err != nil {
		return op, err
	}

	// 2 COMPATIBILITY
	rap := Valuta(m.Catalogo, prof)
	if err := op.scriviOggetto("compatibility.json", rap); err != nil {
		return op, err
	}
	if err := op.vai(VALUTATA, "", ""); err != nil {
		return op, err
	}

	// 3 PLANNING: does the plan hold on this machine? (fingerprint, R31)
	for _, ap := range piano.Azioni {
		if _, err := NuovaAzione(ap); err != nil {
			return op, op.blocca(err)
		}
	}
	im, err := CalcolaImpronta(prof, m.Catalogo, piano.Azioni, piano.Dipende, &Contesto{Amb: m.Amb, Cartella: op.Cartella})
	if err != nil {
		return op, op.blocca(err)
	}
	if im.Digest != piano.Impronta.Digest {
		tolti, aggiunti := DifferenzeImpronta(piano.Impronta.Elementi, im.Elementi)
		det := "in the plan: " + strings.Join(tolti, "; ") + " — now: " + strings.Join(aggiunti, "; ")
		if err := op.scriviOggetto("fingerprint-now.json", im); err != nil {
			return op, err
		}
		return op, op.blocca(Errore("RX-PIANO-001", det))
	}
	if err := op.vai(PIANIFICATA, "", "fingerprint "+im.Digest[:16]); err != nil {
		return op, err
	}

	// 4 CONSENT & SAFETY
	// what is missing (DECISIONI §10.36): the plan says it BLOCKING, and we stop before touching
	for _, x := range piano.NonFatto {
		if x.Gravita == BLOCCANTE {
			m.Ev.Messaggio(op.ID, x)
			return op, op.vai(BLOCCATA, x.Codice, x.Dettaglio)
		}
	}
	appr := piano.Approvazione
	switch {
	case appr != nil && appr.DigestPiano != piano.Digest():
		m.Ev.Messaggio(op.ID, Msg("RX-PIANO-005", ""))
		return op, op.vai(RIFIUTATA, "RX-PIANO-005", "")
	case appr == nil && !approvaAMano:
		m.Ev.Messaggio(op.ID, Msg("RX-PIANO-003", ""))
		return op, op.vai(RIFIUTATA, "RX-PIANO-003", "")
	case appr == nil:
		appr = &Approvazione{Da: chi, Ora: ora(), Modo: "by hand, --approve", DigestPiano: piano.Digest()}
	}
	if err := op.scriviOggetto("approval.json", appr); err != nil {
		return op, err
	}
	if err := op.vai(APPROVATA, "", appr.Modo+", by "+appr.Da); err != nil {
		return op, err
	}

	// the steps the engine knows but cannot execute yet: we stop BEFORE touching
	if nf := PassiNonFatti(&piano); len(nf) > 0 {
		return op, op.blocca(Errore("RX-AZIONE-004", strings.Join(nf, "; ")))
	}

	// 5 ACQUISITION: the trial actions ask for no packages; the resolved set is empty but there.
	if err := op.scriviOggetto("resolved-set.json", map[string]any{"format": Formato, "object": "resolved-set", "artifacts": []any{}}); err != nil {
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
func (m *Motore) Riprendi() (*Operazione, error) {
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
	if err := op.apriRegistro(); err != nil {
		return op, err
	}
	m.Ev.Stato(op.ID, op.Stato, op.Stato, T("ev.si_riprende"))
	switch op.Stato {
	case NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA:
		m.Ev.Messaggio(op.ID, Msg("RX-RIPRESA-002", string(op.Stato)))
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
func (m *Motore) Annulla() (*Operazione, error) {
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
	if err := op.apriRegistro(); err != nil {
		return op, err
	}
	switch op.Stato {
	case NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA:
		m.Ev.Messaggio(op.ID, Msg("RX-RIPRESA-002", string(op.Stato)))
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
func (op *Operazione) continua() error {
	for {
		switch op.Stato {
		case IN_ESECUZIONE:
			err := op.eseguiTutte()
			switch {
			case errors.Is(err, errConcorrente):
				return op.vai(INTERROTTA, "RX-RIPRESA-001", op.ultimoDettaglio())
			case errors.Is(err, errFermata):
				op.m.Ev.Messaggio(op.ID, Msg("RX-AZIONE-006", ""))
				if err := op.vai(IN_ANNULLAMENTO, "RX-AZIONE-006", ""); err != nil {
					return err
				}
			case errors.Is(err, errFallita):
				op.m.Ev.Messaggio(op.ID, Msg("RX-AZIONE-001", op.ultimoDettaglio()))
				if err := op.vai(IN_ANNULLAMENTO, "RX-AZIONE-001", op.ultimoDettaglio()); err != nil {
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
				op.m.Ev.Messaggio(op.ID, Msg("RX-AZIONE-003", ""))
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
			if err := op.scriviInstallazione(fin); err != nil {
				return err
			}
			if op.Piano.Mestiere == "uninstallation" {
				if err := os.Remove(op.m.PercorsoInstallazione()); err != nil && !os.IsNotExist(err) {
					return err
				}
			}
			if err := op.vai(fin, "", ""); err != nil {
				return err
			}
			if op.Piano.Mestiere == "uninstallation" {
				return op.m.PulisciStoria(op.Piano.Purge)
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
				op.m.Ev.Messaggio(op.ID, Msg("RX-AZIONE-002", strings.Join(resti, "; ")))
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

func (op *Operazione) ultimoDettaglio() string {
	for i := len(op.Reg.Eventi) - 1; i >= 0; i-- {
		e := op.Reg.Eventi[i]
		if e.Tipo == EvFallita || (e.Tipo == EvNota && e.Codice == "RX-RIPRESA-001") {
			return strings.TrimSpace(e.Azione + ": " + e.Dettaglio)
		}
	}
	return ""
}

// contesto: rolling back an installation is always purge — the
// machine as it was; the uninstallation carries its «purge» in the parameters of the undo steps.
func (op *Operazione) contesto(ap AzionePiano) *Contesto {
	return &Contesto{Amb: op.m.Amb, Cartella: op.Cartella, P: ap, Purge: true}
}

func (op *Operazione) fallita(ap AzionePiano, err error) error {
	codice := CodiceDi(err)
	if codice == "" {
		codice = "RX-AZIONE-001"
	}
	if e := op.Reg.Scrivi(Evento{Tipo: EvFallita, Azione: ap.ID, Codice: codice, Dettaglio: err.Error()}); e != nil {
		return e
	}
	op.m.Ev.Azione(op.ID, ap.ID, "FAILED", err.Error())
	return errFallita
}

func (op *Operazione) concorrente(ap AzionePiano, det string) error {
	if e := op.Reg.Scrivi(Evento{Tipo: EvNota, Azione: ap.ID, Codice: "RX-RIPRESA-001", Dettaglio: det}); e != nil {
		return e
	}
	op.m.Ev.Messaggio(op.ID, Msg("RX-RIPRESA-001", ap.ID+": "+det))
	return errConcorrente
}

// fatta: checks and records FATTA.
func (op *Operazione) fatta(az Azione, ap AzionePiano, prima json.RawMessage, nota string) error {
	esito, det, err := az.Controlla(op.contesto(ap), prima)
	if err != nil {
		return op.fallita(ap, err)
	}
	if esito != COMPLETO {
		return op.fallita(ap, Errore("RX-AZIONE-003", string(esito)+": "+det))
	}
	if err := op.Reg.Scrivi(Evento{Tipo: EvFatta, Azione: ap.ID, Dopo: jsonDi(map[string]string{"result": string(esito), "detail": det}), Dettaglio: nota}); err != nil {
		return err
	}
	op.m.Ev.Azione(op.ID, ap.ID, "DONE", strings.TrimSpace(nota+" "+det))
	punto("dopo-fatta", ap.ID)
	return nil
}

// eseguiTutte: phase 6 with the write-ahead log, and the resume of the table of
// §6.6.3 (the same road: a new operation is a resume with an empty log).
func (op *Operazione) eseguiTutte() error {
	for _, ap := range op.Piano.Azioni {
		az, err := NuovaAzione(ap)
		if err != nil {
			return op.fallita(ap, err)
		}
		c := op.contesto(ap)
		ult := op.Reg.Ultimo(ap.ID, EvIntenzione, EvFatta, EvFallita)
		if ult == nil && op.m.Fermata != nil && op.m.Fermata() {
			return errFermata
		}
		switch {
		case ult == nil: // nothing in the log: not begun ⇒ do it
			punto("prima-intenzione", ap.ID)
			prima, orig, err := az.Fotografa(c)
			if err != nil {
				return op.fallita(ap, err)
			}
			if err := op.Reg.Scrivi(Evento{Tipo: EvIntenzione, Azione: ap.ID, Prima: prima, Origine: orig}); err != nil {
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

		case ult.Tipo == EvIntenzione: // begun: maybe finished, maybe not, maybe half-done
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
					if err := r.Ripara(c, prima); err != nil {
						return op.fallita(ap, err)
					}
				} else if err := az.Annulla(c, prima); err != nil {
					return op.fallita(ap, err)
				}
			case ESTRANEO:
				return op.concorrente(ap, det)
			}
			if err := az.Fai(c, prima); err != nil {
				return op.fallita(ap, err)
			}
			if err := op.fatta(az, ap, prima, "resumed: done again"); err != nil {
				return err
			}

		case ult.Tipo == EvFatta: // finished and recorded: move on, but the effect must still be there
			prima := op.Reg.Intenzione(ap.ID).Prima
			esito, det, err := az.Controlla(c, prima)
			if err != nil {
				return op.fallita(ap, err)
			}
			if esito != COMPLETO {
				return op.concorrente(ap, "was FATTA, now "+string(esito)+": "+det)
			}

		case ult.Tipo == EvFallita:
			return errFallita
		}
	}
	return nil
}

// annullaTutte walks the actions backwards. Returns what could not be undone.
func (op *Operazione) annullaTutte() ([]string, error) {
	var resti []string
	az := op.Piano.Azioni
	for i := len(az) - 1; i >= 0; i-- {
		ap := az[i]
		intz := op.Reg.Intenzione(ap.ID)
		if intz == nil {
			continue // never begun: nothing to undo
		}
		if u := op.Reg.Ultimo(ap.ID, EvIntenzioneAnnulla, EvAnnullata, EvAnnullamentoFallito); u != nil && u.Tipo == EvAnnullata {
			continue
		}
		a, err := NuovaAzione(ap)
		if err != nil {
			return nil, err
		}
		c := op.contesto(ap)
		scrivi := func(t TipoEvento, codice, det string) error {
			op.m.Ev.Azione(op.ID, ap.ID, string(t), det)
			return op.Reg.Scrivi(Evento{Tipo: t, Azione: ap.ID, Codice: codice, Dettaglio: det})
		}
		if intz.Origine == PREESISTENTE {
			if err := scrivi(EvAnnullata, "", "PREEXISTING: left untouched"); err != nil {
				return nil, err
			}
			continue
		}
		if ok, det, err := a.Annullata(c, intz.Prima); err == nil && ok {
			if err := scrivi(EvAnnullata, "", "nothing to undo: "+det); err != nil {
				return nil, err
			}
			continue
		}
		if esito, det, err := a.Controlla(c, intz.Prima); err == nil && esito == ESTRANEO {
			resti = append(resti, ap.ID+": changed by someone else, left untouched ("+det+")")
			if err := scrivi(EvAnnullamentoFallito, "RX-RIPRESA-001", "CONCURRENT: "+det); err != nil {
				return nil, err
			}
			continue
		}
		if err := scrivi(EvIntenzioneAnnulla, "", ""); err != nil {
			return nil, err
		}
		punto("annulla-dopo-intenzione", ap.ID)
		errA := a.Annulla(c, intz.Prima)
		punto("annulla-dopo-effetto", ap.ID)
		ok, det, errB := a.Annullata(c, intz.Prima)
		if errA == nil && errB == nil && ok {
			if err := scrivi(EvAnnullata, "", det); err != nil {
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
		if err := scrivi(EvAnnullamentoFallito, "RX-AZIONE-002", motivo); err != nil {
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
	Richiesto bool   `json:"required"`
	Dettaglio string `json:"detail,omitempty"`
}

// RapportoVerifica: the sixth object.
type RapportoVerifica struct {
	Formato    string       `json:"format"`
	Oggetto    string       `json:"object"`
	Creato     string       `json:"created"`
	Controlli  []Controllo  `json:"checks"`
	Condizioni []Condizione `json:"conditions,omitempty"` // those born from verification (a declared UNKNOWN)
}

// verifica (phase 7, here reduced to the trial actions): every action rechecked. ⛔ UNKNOWN is not
// PASS: a required check that cannot answer leads to cancellation (the trial actions
// have no declared fallback).
func (op *Operazione) verifica() (bool, error) {
	rv := RapportoVerifica{Formato: Formato, Oggetto: "check", Creato: ora()}
	tutto := true
	for _, ap := range op.Piano.Azioni {
		a, err := NuovaAzione(ap)
		if err != nil {
			return false, err
		}
		k := Controllo{ID: ap.ID, Cosa: ap.ComeSiVerifica, Richiesto: true}
		intz := op.Reg.Intenzione(ap.ID)
		if intz == nil {
			k.Esito, k.Dettaglio = "UNKNOWN", "no intention in the log"
		} else if esito, det, err := a.Controlla(op.contesto(ap), intz.Prima); err != nil {
			k.Esito, k.Dettaglio = "UNKNOWN", err.Error()
		} else if esito == COMPLETO {
			k.Esito, k.Dettaglio = "PASS", det
		} else {
			k.Esito, k.Dettaglio = "FAIL", string(esito)+": "+det
		}
		if k.Esito != "PASS" {
			tutto = false
		}
		rv.Controlli = append(rv.Controlli, k)
	}
	// 7a: H.264 encoding is tested by REMOTIX itself (§6.5-bis). Required: FAIL (no card that
	// encodes: phase 19, no fallback) ⇒ cancellation; UNKNOWN ⇒ CONFERMATA_A_CONDIZIONI, never PASS
	// (§6.6.7).
	// and the PAM stack that resolves, and the port the firewall lets through (certifica.go, R29)
	if op.Piano.Mestiere == "installation" {
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
		rv.Controlli = append(rv.Controlli, k...)
		rv.Condizioni = append(rv.Condizioni, cond...)
		if fallito {
			tutto = false
		}
	}
	return tutto, op.scriviOggetto("check.json", rv)
}

// provaCodifica: `remotix --prova-codifica` (§6.5-bis; phase 19, no fallback to the processor): one
// JSON line {"esito":"hardware"|"nessuno","codificatore":…,"strada":"vulkan"|"vaapi"|"","nodo":…,
// "motivo":…,"codec":…,"offerti":…,"hevc":…,"h264":…,"hevc_strada":…,"h264_strada":…}; exit 0 if the card encoded the frame, 3 if NO
// card can encode (the encoder does not open: no node, no driver, driver without
// encoding — the declared refusal), 1 if the card opens but the frame does not come out, 2 usage
// error. The engine launches it as root (closed list). hardware ⇒ PASS; 3 or 1 ⇒ FAIL; a binary that
// does not know it or an unreadable answer ⇒ UNKNOWN (§6.6.7).
func provaCodifica(a *Ambiente) (Controllo, *Condizione) {
	k := Controllo{ID: "h264-encoding", Cosa: "remotix --prova-codifica (7a)", Richiesto: true}
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
		k.Esito, k.Dettaglio = "UNKNOWN", err.Error()
	case !letto || c == 2:
		k.Esito, k.Dettaglio = "UNKNOWN", T("ver.codifica_assente")+": "+ultimeRighe(out, 2)
	case c == 0 && r.Esito == "hardware":
		k.Esito, k.Dettaglio = "PASS", det
	case c == 3:
		k.Esito, k.Dettaglio = "FAIL", T("ver.nessuna_scheda", nonVuoto(r.Motivo, det))
	default:
		k.Esito, k.Dettaglio = "FAIL", det
	}
	if k.Esito == "UNKNOWN" {
		return k, &Condizione{Codice: "C-LIMITE", Testo: T("cond.codifica_ignota", k.Dettaglio)}
	}
	return k, nil
}

func (op *Operazione) condizioni() []Condizione {
	if op.Piano.Mestiere == "uninstallation" {
		return nil
	}
	var c []Condizione
	var rv RapportoVerifica
	if LeggiJSON(filepath.Join(op.Cartella, "check.json"), &rv) == nil {
		c = append(c, rv.Condizioni...)
	}
	var r Rapporto
	if err := LeggiJSON(filepath.Join(op.Cartella, "compatibility.json"), &r); err != nil {
		return c
	}
	for _, e := range r.Desktop {
		if e.Livello != NON_SUPPORTATA && e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown" {
			c = append(c, e.Condizioni...)
		}
	}
	return c
}

// Certificato: the seventh object (§6.6.11).
type Certificato struct {
	Formato       string       `json:"format"`
	Oggetto       string       `json:"object"`
	Creato        string       `json:"created"`
	Operazione    string       `json:"operation"`
	Stato         Stato        `json:"state"`
	Mestiere      string       `json:"kind"`
	Prodotto      string       `json:"product"`
	Motore        RifMotore    `json:"engine"`
	Catalogo      RifCatalogo  `json:"catalog"`
	Fiducia       string       `json:"trust"`
	DigestPiano   string       `json:"digest_plan"`
	DigestInsieme string       `json:"digest_resolved_set"`
	Impronta      string       `json:"fingerprint"`
	Controlli     []Controllo  `json:"checks"`
	Condizioni    []Condizione `json:"conditions"`
	Resti         []string     `json:"leftovers,omitempty"` // ANNULLATA_IN_PARTE: what remains, and why
	Indirette     []string     `json:"indirect"`            // INDIRECT changes declared (none, without packages)
}

func (op *Operazione) certificato(fin Stato, resti []string) error {
	var fid Fiducia
	LeggiJSON(filepath.Join(op.Cartella, "trust.json"), &fid)
	var rv RapportoVerifica
	LeggiJSON(filepath.Join(op.Cartella, "check.json"), &rv)
	ins, _ := Sha256File(filepath.Join(op.Cartella, "resolved-set.json"))
	fiducia := T("cert.fiducia_no")
	if fid.Catalogo.Digest != "" && len(fid.Messaggi) == 0 {
		fiducia = fmt.Sprintf("%s (sequence %d)", fid.Fonte, fid.Sequenza)
	}
	c := Certificato{Formato: Formato, Oggetto: "certificate", Creato: ora(), Operazione: op.ID, Stato: fin,
		Mestiere: op.Piano.Mestiere, Prodotto: T("cert.prodotto_prova"),
		Motore: RifMotore{VersioneMotore, DigestMotore()}, Catalogo: fid.Catalogo, Fiducia: fiducia,
		DigestPiano: op.Piano.Digest(), DigestInsieme: ins, Impronta: op.Piano.Impronta.Digest,
		Controlli: rv.Controlli, Condizioni: op.condizioni(), Resti: resti, Indirette: op.indirette()}
	if c.Condizioni == nil {
		c.Condizioni = []Condizione{}
	}
	if err := op.scriviOggetto("certificate.json", c); err != nil {
		return err
	}
	var t strings.Builder
	fmt.Fprintf(&t, "%s\n\n%s: %s\n%s: %s\n%s: %s (%s)\n%s: %s (%s)\n%s: %s\n%s: %s\n%s: %s\n",
		T("cert.titolo", op.ID), T("cert.stato"), c.Stato, T("cert.mestiere"), c.Mestiere, T("cert.motore"), c.Motore.Versione, c.Motore.Digest,
		T("cert.catalogo"), c.Catalogo.Versione, c.Catalogo.Digest, T("cert.fiducia"), c.Fiducia, T("cert.piano"), c.DigestPiano, T("cert.impronta"), c.Impronta)
	fmt.Fprintf(&t, "\n%s:\n", T("cert.controlli"))
	for _, k := range c.Controlli {
		fmt.Fprintf(&t, "  %-8s %s — %s\n", k.Esito, k.ID, k.Dettaglio)
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
type Installazione struct {
	Formato     string `json:"format"`
	Oggetto     string `json:"object"` // "installation"
	Operazione  string `json:"operation"`
	Stato       Stato  `json:"state"`
	Mestiere    string `json:"kind"`
	Certificato string `json:"certificate"`
	Scritto     string `json:"written"`
}

// PercorsoInstallazione: next to the operations folder.
func (m *Motore) PercorsoInstallazione() string {
	return filepath.Join(filepath.Dir(m.Cartella), "installation.json")
}

// scriviInstallazione: only for the kinds that really install the product. The trial plan
// of T4 does not write it: it did not install REMOTIX.
func (op *Operazione) scriviInstallazione(fin Stato) error {
	if op.Piano.Mestiere != "installation" {
		return nil
	}
	return ScriviJSON(op.m.PercorsoInstallazione(), Installazione{Formato: Formato, Oggetto: "installation",
		Operazione: op.ID, Stato: fin, Mestiere: op.Piano.Mestiere,
		Certificato: filepath.Join(op.Cartella, "certificate.json"), Scritto: ora()})
}

// ControllaInstallazione: what REMOTIX (and remotix-install aggiornato) asks at start-up.
// It holds only if the file is there, the operation it names exists and is CONFERMATA (even conditionally).
func (m *Motore) ControllaInstallazione() (*Installazione, error) {
	var in Installazione
	if err := LeggiJSON(m.PercorsoInstallazione(), &in); err != nil {
		return nil, Errore("RX-INST-001", err.Error())
	}
	op, err := m.apri(in.Operazione)
	if err != nil {
		return nil, Errore("RX-INST-001", "operation "+in.Operazione+" does not exist")
	}
	if op.Stato != CONFERMATA && op.Stato != CONFERMATA_A_CONDIZIONI {
		return nil, Errore("RX-INST-001", "operation "+in.Operazione+" is "+string(op.Stato))
	}
	return &in, nil
}

// indirette: what happened indirectly and remains (§6.6.4): the actions declare it; and the
// packages held back by an undo step (RX-PACCHETTI-006), which says so in its FATTA.
func (op *Operazione) indirette() []string {
	r := []string{}
	for _, e := range op.Reg.Eventi {
		var d map[string]string
		if e.Tipo == EvFatta && json.Unmarshal(e.Dopo, &d) == nil && strings.Contains(d["detail"], "[RX-PACCHETTI-006]") {
			_, x, _ := strings.Cut(d["detail"], "[RX-PACCHETTI-006] ")
			r = append(r, "RX-PACCHETTI-006 "+e.Azione+": "+x)
		}
	}
	for _, ap := range op.Piano.Azioni {
		intz := op.Reg.Intenzione(ap.ID)
		if intz == nil {
			continue
		}
		a, err := NuovaAzione(ap)
		if err != nil {
			continue
		}
		if d, ok := a.(Dichiarante); ok {
			r = append(r, d.Indirette(intz.Prima)...)
		}
	}
	return r
}
