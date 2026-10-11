package engine

import (
	"encoding/json"
	"fmt"
	"io"
)

// Events: what the engine says while it works. Two forms, same content:
//   - JSON, one line per event (--eventi): it is the channel of the future TUIs and GUIs (§6.6.1, R36);
//   - plain text, for whoever watches the terminal.
//
// ⛔ The interfaces receive nothing that is not also in the objects on disk: the events
// say «it happened», the objects say «how it is».
type Events struct {
	W    io.Writer
	JSON bool
}

// Public event (one JSON line).
type PublicEvent struct {
	Schema    string   `json:"format"`
	At        string   `json:"time"`
	Event     string   `json:"event"` // state · action · message · object
	Operation string   `json:"operation,omitempty"`
	Da        State    `json:"from,omitempty"`
	A         State    `json:"to,omitempty"`
	Action    string   `json:"action,omitempty"`
	Phase     string   `json:"phase,omitempty"`
	Message   *Message `json:"message,omitempty"`
	Obj       string   `json:"object,omitempty"`
	RoutePath string   `json:"path,omitempty"`
	Detail    string   `json:"detail,omitempty"`
}

func (e *Events) write(ev PublicEvent, text string) {
	if e == nil || e.W == nil {
		return
	}
	if e.JSON {
		ev.Schema, ev.At = Schema, now()
		b, _ := json.Marshal(ev)
		fmt.Fprintln(e.W, string(b))
		return
	}
	fmt.Fprintln(e.W, text)
}

func stateName(s State) string { return T("state." + string(s)) }

func (e *Events) State(op string, da, a State, detail string) {
	t := "  → " + stateName(a)
	if detail != "" {
		t += " — " + detail
	}
	e.write(PublicEvent{Event: "state", Operation: op, Da: da, A: a, Detail: detail}, t)
}

func (e *Events) Action(op, action, phase, detail string) {
	t := "      " + action + ": " + phase
	if detail != "" {
		t += " (" + detail + ")"
	}
	e.write(PublicEvent{Event: "action", Operation: op, Action: action, Phase: phase, Detail: detail}, t)
}

func (e *Events) Message(op string, m Message) {
	t := fmt.Sprintf("  [%s] %s %s", m.Codice, m.Severity, m.Testo)
	if m.Detail != "" {
		t += " (" + m.Detail + ")"
	}
	if m.Remediation != "" {
		t += "\n      " + T("ev.rimedio") + ": " + m.Remediation
	}
	e.write(PublicEvent{Event: "message", Operation: op, Message: &m}, t)
}

func (e *Events) Obj(op, object, fpath string) {
	e.write(PublicEvent{Event: "object", Operation: op, Obj: object, RoutePath: fpath}, "      "+object+": "+fpath)
}
