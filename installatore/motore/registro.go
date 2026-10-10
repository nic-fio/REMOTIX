package motore

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// EventType: the lines of the write-ahead log (§6.6.3).
type EventType string

const (
	EvState          EventType = "STATE"
	EvIntent         EventType = "INTENT"
	EvDone           EventType = "DONE"
	EvFailed         EventType = "FAILED"
	EvIntentRollback EventType = "ROLLBACK_INTENT"
	EvCancelled      EventType = "ROLLED_BACK"
	EvRollbackFailed EventType = "ROLLBACK_FAILED"
	EvNote           EventType = "NOTE"
	EvCommand        EventType = "COMMAND" // a program of the closed list launched (R41)
)

// Event is a line of the log (registro.jsonl).
type Event struct {
	N       int             `json:"n"`
	TimeNow string          `json:"time"`
	Kind    EventType       `json:"type"`
	Action  string          `json:"action,omitempty"`
	Da      State           `json:"from,omitempty"`
	A       State           `json:"to,omitempty"`
	Before  json.RawMessage `json:"state_before,omitempty"`
	After   json.RawMessage `json:"state_after,omitempty"`
	Origin  Origin          `json:"origin,omitempty"`
	Code    string          `json:"code,omitempty"`
	Detail  string          `json:"detail,omitempty"`
}

// Log: the write-ahead log. Every line is written with fsync of the file (and of the
// folder on creation) BEFORE the engine takes the next step.
type Log struct {
	fpath  string
	f      *os.File
	Events []Event
}

// OpenLog reads the existing log (or creates one) and opens it for appending. A final line
// written halfway (the process killed while writing) is removed and reported: lines are
// written whole or not at all, and without its line the thing did not happen.
func OpenLog(fpath string) (*Log, []Message, error) {
	var warnings []Message
	r := &Log{fpath: fpath}
	b, err := os.ReadFile(fpath)
	fresh := os.IsNotExist(err)
	if err != nil && !fresh {
		return nil, nil, err
	}
	if len(b) > 0 && b[len(b)-1] != '\n' {
		cut := bytes.LastIndexByte(b, '\n') + 1
		if err := os.Truncate(fpath, int64(cut)); err != nil {
			return nil, nil, err
		}
		warnings = append(warnings, Msg("RX-RIPRESA-003", fmt.Sprintf("%d bytes removed", len(b)-cut)))
		b = b[:cut]
	}
	for i, row := range bytes.Split(bytes.TrimSuffix(b, []byte("\n")), []byte("\n")) {
		if len(row) == 0 {
			continue
		}
		var e Event
		if err := json.Unmarshal(row, &e); err != nil {
			return nil, nil, fmt.Errorf("%s: line %d broken: %w", fpath, i+1, err)
		}
		r.Events = append(r.Events, e)
	}
	f, err := os.OpenFile(fpath, os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0o600)
	if err != nil {
		return nil, nil, err
	}
	r.f = f
	if fresh {
		if err := f.Sync(); err != nil {
			return nil, nil, err
		}
		if err := SyncFolder(filepath.Dir(fpath)); err != nil {
			return nil, nil, err
		}
	}
	return r, warnings, nil
}

// Record appends a line and makes it durable before returning.
func (r *Log) Record(e Event) error {
	e.N = len(r.Events) + 1
	e.TimeNow = now()
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
	r.Events = append(r.Events, e)
	return nil
}

// Shut closes the file.
func (r *Log) Shut() error { return r.f.Close() }

// Last: the last line of an action among the given types (all if none).
func (r *Log) Last(action string, types ...EventType) *Event {
	for i := len(r.Events) - 1; i >= 0; i-- {
		e := &r.Events[i]
		if e.Action != action {
			continue
		}
		if len(types) == 0 {
			return e
		}
		for _, t := range types {
			if e.Kind == t {
				return e
			}
		}
	}
	return nil
}

// Intent: the FIRST intention of an action. The before-state that counts is that one: if
// resume re-photographed the machine after an effect had already happened, it would mistake a change
// of ours for a PRE-EXISTING one and would never undo it (§6.6.4).
func (r *Log) Intent(action string) *Event {
	for i := range r.Events {
		if r.Events[i].Action == action && r.Events[i].Kind == EvIntent {
			return &r.Events[i]
		}
	}
	return nil
}

// Touched: the log has at least one intention, that is the machine may have been changed.
func (r *Log) Touched() bool {
	for _, e := range r.Events {
		if e.Kind == EvIntent {
			return true
		}
	}
	return false
}
