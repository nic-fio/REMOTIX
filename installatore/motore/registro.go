package motore

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// TipoEvento: the lines of the write-ahead log (§6.6.3).
type TipoEvento string

const (
	EvStato               TipoEvento = "STATE"
	EvIntenzione          TipoEvento = "INTENT"
	EvFatta               TipoEvento = "DONE"
	EvFallita             TipoEvento = "FAILED"
	EvIntenzioneAnnulla   TipoEvento = "ROLLBACK_INTENT"
	EvAnnullata           TipoEvento = "ROLLED_BACK"
	EvAnnullamentoFallito TipoEvento = "ROLLBACK_FAILED"
	EvNota                TipoEvento = "NOTE"
	EvComando             TipoEvento = "COMMAND" // a program of the closed list launched (R41)
)

// Evento is a line of the log (registro.jsonl).
type Evento struct {
	N         int             `json:"n"`
	Ora       string          `json:"time"`
	Tipo      TipoEvento      `json:"type"`
	Azione    string          `json:"action,omitempty"`
	Da        Stato           `json:"from,omitempty"`
	A         Stato           `json:"to,omitempty"`
	Prima     json.RawMessage `json:"state_before,omitempty"`
	Dopo      json.RawMessage `json:"state_after,omitempty"`
	Origine   Origine         `json:"origin,omitempty"`
	Codice    string          `json:"code,omitempty"`
	Dettaglio string          `json:"detail,omitempty"`
}

// Registro: the write-ahead log. Every line is written with fsync of the file (and of the
// folder on creation) BEFORE the engine takes the next step.
type Registro struct {
	percorso string
	f        *os.File
	Eventi   []Evento
}

// ApriRegistro reads the existing log (or creates one) and opens it for appending. A final line
// written halfway (the process killed while writing) is removed and reported: lines are
// written whole or not at all, and without its line the thing did not happen.
func ApriRegistro(percorso string) (*Registro, []Messaggio, error) {
	var avvisi []Messaggio
	r := &Registro{percorso: percorso}
	b, err := os.ReadFile(percorso)
	nuovo := os.IsNotExist(err)
	if err != nil && !nuovo {
		return nil, nil, err
	}
	if len(b) > 0 && b[len(b)-1] != '\n' {
		taglio := bytes.LastIndexByte(b, '\n') + 1
		if err := os.Truncate(percorso, int64(taglio)); err != nil {
			return nil, nil, err
		}
		avvisi = append(avvisi, Msg("RX-RIPRESA-003", fmt.Sprintf("%d bytes removed", len(b)-taglio)))
		b = b[:taglio]
	}
	for i, riga := range bytes.Split(bytes.TrimSuffix(b, []byte("\n")), []byte("\n")) {
		if len(riga) == 0 {
			continue
		}
		var e Evento
		if err := json.Unmarshal(riga, &e); err != nil {
			return nil, nil, fmt.Errorf("%s: line %d broken: %w", percorso, i+1, err)
		}
		r.Eventi = append(r.Eventi, e)
	}
	f, err := os.OpenFile(percorso, os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0o600)
	if err != nil {
		return nil, nil, err
	}
	r.f = f
	if nuovo {
		if err := f.Sync(); err != nil {
			return nil, nil, err
		}
		if err := SincronizzaCartella(filepath.Dir(percorso)); err != nil {
			return nil, nil, err
		}
	}
	return r, avvisi, nil
}

// Scrivi appends a line and makes it durable before returning.
func (r *Registro) Scrivi(e Evento) error {
	e.N = len(r.Eventi) + 1
	e.Ora = ora()
	b, err := json.Marshal(e)
	if err != nil {
		return err
	}
	if _, err := r.f.Write(append(b, '\n')); err != nil {
		return err
	}
	if err := r.f.Sync(); err != nil {
		return err
	}
	r.Eventi = append(r.Eventi, e)
	return nil
}

// Chiudi closes the file.
func (r *Registro) Chiudi() error { return r.f.Close() }

// Ultimo: the last line of an action among the given types (all if none).
func (r *Registro) Ultimo(azione string, tipi ...TipoEvento) *Evento {
	for i := len(r.Eventi) - 1; i >= 0; i-- {
		e := &r.Eventi[i]
		if e.Azione != azione {
			continue
		}
		if len(tipi) == 0 {
			return e
		}
		for _, t := range tipi {
			if e.Tipo == t {
				return e
			}
		}
	}
	return nil
}

// Intenzione: the FIRST intention of an action. The before-state that counts is that one: if
// resume re-photographed the machine after an effect had already happened, it would mistake a change
// of ours for a PRE-EXISTING one and would never undo it (§6.6.4).
func (r *Registro) Intenzione(azione string) *Evento {
	for i := range r.Eventi {
		if r.Eventi[i].Azione == azione && r.Eventi[i].Tipo == EvIntenzione {
			return &r.Eventi[i]
		}
	}
	return nil
}

// Toccata: the log has at least one intention, that is the machine may have been changed.
func (r *Registro) Toccata() bool {
	for _, e := range r.Eventi {
		if e.Tipo == EvIntenzione {
			return true
		}
	}
	return false
}
