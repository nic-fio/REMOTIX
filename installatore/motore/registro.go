package motore

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// TipoEvento: le righe del registro a scrittura anticipata (§6.6.3).
type TipoEvento string

const (
	EvStato               TipoEvento = "STATO"
	EvIntenzione          TipoEvento = "INTENZIONE"
	EvFatta               TipoEvento = "FATTA"
	EvFallita             TipoEvento = "FALLITA"
	EvIntenzioneAnnulla   TipoEvento = "INTENZIONE_ANNULLA"
	EvAnnullata           TipoEvento = "ANNULLATA"
	EvAnnullamentoFallito TipoEvento = "ANNULLAMENTO_FALLITO"
	EvNota                TipoEvento = "NOTA"
	EvComando             TipoEvento = "COMANDO" // un programma dell'elenco chiuso lanciato (R41)
)

// Evento è una riga del registro (registro.jsonl).
type Evento struct {
	N         int             `json:"n"`
	Ora       string          `json:"ora"`
	Tipo      TipoEvento      `json:"tipo"`
	Azione    string          `json:"azione,omitempty"`
	Da        Stato           `json:"da,omitempty"`
	A         Stato           `json:"a,omitempty"`
	Prima     json.RawMessage `json:"stato_prima,omitempty"`
	Dopo      json.RawMessage `json:"stato_dopo,omitempty"`
	Origine   Origine         `json:"origine,omitempty"`
	Codice    string          `json:"codice,omitempty"`
	Dettaglio string          `json:"dettaglio,omitempty"`
}

// Registro: il giornale a scrittura anticipata. Ogni riga si scrive con fsync del file (e della
// cartella alla creazione) PRIMA che il motore faccia il passo successivo.
type Registro struct {
	percorso string
	f        *os.File
	Eventi   []Evento
}

// ApriRegistro legge il registro che c'è (o ne crea uno) e lo apre in aggiunta. Una riga finale
// scritta a metà (il processo ucciso durante la scrittura) si toglie e si dice: le righe si
// scrivono intere o niente, e senza la sua riga la cosa non è avvenuta.
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
		avvisi = append(avvisi, Msg("RX-RIPRESA-003", fmt.Sprintf("%d byte tolti", len(b)-taglio)))
		b = b[:taglio]
	}
	for i, riga := range bytes.Split(bytes.TrimSuffix(b, []byte("\n")), []byte("\n")) {
		if len(riga) == 0 {
			continue
		}
		var e Evento
		if err := json.Unmarshal(riga, &e); err != nil {
			return nil, nil, fmt.Errorf("%s: riga %d rotta: %w", percorso, i+1, err)
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

// Scrivi aggiunge una riga e la rende durevole prima di tornare.
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

// Chiudi chiude il file.
func (r *Registro) Chiudi() error { return r.f.Close() }

// Ultimo: l'ultima riga di un'azione fra i tipi dati (tutti se nessuno).
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

// Intenzione: la PRIMA intenzione di un'azione. Lo stato di prima che conta è quello: se la
// ripresa rifotografasse la macchina dopo un effetto già avvenuto, scambierebbe una modifica
// nostra per una PREESISTENTE e non la annullerebbe più (§6.6.4).
func (r *Registro) Intenzione(azione string) *Evento {
	for i := range r.Eventi {
		if r.Eventi[i].Azione == azione && r.Eventi[i].Tipo == EvIntenzione {
			return &r.Eventi[i]
		}
	}
	return nil
}

// Toccata: il registro ha almeno un'intenzione, cioè la macchina può essere stata cambiata.
func (r *Registro) Toccata() bool {
	for _, e := range r.Eventi {
		if e.Tipo == EvIntenzione {
			return true
		}
	}
	return false
}
