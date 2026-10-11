package motore

import (
	"encoding/json"
	"fmt"
	"io"
)

// Eventi: what the engine says while it works. Two forms, same content:
//   - JSON, one line per event (--eventi): it is the channel of the future TUIs and GUIs (§6.6.1, R36);
//   - plain text, for whoever watches the terminal.
//
// ⛔ The interfaces receive nothing that is not also in the objects on disk: the events
// say «it happened», the objects say «how it is».
type Eventi struct {
	W    io.Writer
	JSON bool
}

// Public event (one JSON line).
type PublicEvent struct {
	Formato   string   `json:"format"`
	Ora       string   `json:"time"`
	Event     string   `json:"event"` // stato · azione · messaggio · oggetto
	Operation string   `json:"operation,omitempty"`
	Da        Stato    `json:"from,omitempty"`
	A         Stato    `json:"to,omitempty"`
	Azione    string   `json:"action,omitempty"`
	Fase      string   `json:"phase,omitempty"`
	Message   *Message `json:"message,omitempty"`
	Object    string   `json:"object,omitempty"`
	Path      string   `json:"path,omitempty"`
	Detail    string   `json:"detail,omitempty"`
}

func (e *Eventi) scrivi(ev PublicEvent, testo string) {
	if e == nil || e.W == nil {
		return
	}
	if e.JSON {
		ev.Formato, ev.Ora = Formato, ora()
		b, _ := json.Marshal(ev)
		fmt.Fprintln(e.W, string(b))
		return
	}
	fmt.Fprintln(e.W, testo)
}

func stateName(s Stato) string { return T("state." + string(s)) }

func (e *Eventi) Stato(op string, da, a Stato, dettaglio string) {
	t := "  → " + stateName(a)
	if dettaglio != "" {
		t += " — " + dettaglio
	}
	e.scrivi(PublicEvent{Event: "state", Operation: op, Da: da, A: a, Detail: dettaglio}, t)
}

func (e *Eventi) Azione(op, azione, fase, dettaglio string) {
	t := "      " + azione + ": " + fase
	if dettaglio != "" {
		t += " (" + dettaglio + ")"
	}
	e.scrivi(PublicEvent{Event: "action", Operation: op, Azione: azione, Fase: fase, Detail: dettaglio}, t)
}

func (e *Eventi) Message(op string, m Message) {
	t := fmt.Sprintf("  [%s] %s %s", m.Codice, m.Severity, m.Testo)
	if m.Detail != "" {
		t += " (" + m.Detail + ")"
	}
	if m.Remediation != "" {
		t += "\n      " + T("ev.rimedio") + ": " + m.Remediation
	}
	e.scrivi(PublicEvent{Event: "message", Operation: op, Message: &m}, t)
}

func (e *Eventi) Object(op, oggetto, percorso string) {
	e.scrivi(PublicEvent{Event: "object", Operation: op, Object: oggetto, Path: percorso}, "      "+oggetto+": "+percorso)
}
