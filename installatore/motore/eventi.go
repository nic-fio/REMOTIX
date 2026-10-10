package motore

import (
	"encoding/json"
	"fmt"
	"io"
)

// Events: what the engine says while it works. Two forms, same content:
//   - JSON, one line per event (--events): it is the channel of the future TUIs and GUIs (§6.6.1, R36);
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
	TimeNow   string   `json:"time"`
	Event     string   `json:"event"` // state · action · message · object
	Operation string   `json:"operation,omitempty"`
	Da        State    `json:"from,omitempty"`
	A         State    `json:"to,omitempty"`
	Action    string   `json:"action,omitempty"`
	Phase     string   `json:"phase,omitempty"`
	Message   *Message `json:"message,omitempty"`
	Object    string   `json:"object,omitempty"`
	Path      string   `json:"path,omitempty"`
	Detail    string   `json:"detail,omitempty"`
}

func (e *Events) put_out(ev PublicEvent, body_text string) {
	if e == nil || e.W == nil {
		return
	}
	if e.JSON {
		ev.Schema, ev.TimeNow = Schema, now()
		b, _ := json.Marshal(ev)
		fmt.Fprintln(e.W, string(b))
		return
	}
	fmt.Fprintln(e.W, body_text)
}

func stateName(s State) string { return T("state." + string(s)) }

func (e *Events) State(op string, da, a State, detail string) {
	t := "  → " + stateName(a)
	if detail != "" {
		t += " — " + detail
	}
	e.put_out(PublicEvent{Event: "state", Operation: op, Da: da, A: a, Detail: detail}, t)
}

func (e *Events) Action(op, action, phase, detail string) {
	t := "      " + action + ": " + phase
	if detail != "" {
		t += " (" + detail + ")"
	}
	e.put_out(PublicEvent{Event: "action", Operation: op, Action: action, Phase: phase, Detail: detail}, t)
}

func (e *Events) Message(op string, m Message) {
	t := fmt.Sprintf("  [%s] %s %s", m.Code, m.Severity, m.Text)
	if m.Detail != "" {
		t += " (" + m.Detail + ")"
	}
	if m.Remediation != "" {
		t += "\n      " + T("ev.remediation") + ": " + m.Remediation
	}
	e.put_out(PublicEvent{Event: "message", Operation: op, Message: &m}, t)
}

func (e *Events) Object(op, object, fpath string) {
	e.put_out(PublicEvent{Event: "object", Operation: op, Object: object, Path: fpath}, "      "+object+": "+fpath)
}
