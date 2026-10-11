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
	Formato    string     `json:"format"`
	Ora        string     `json:"time"`
	Evento     string     `json:"event"` // stato · azione · messaggio · oggetto
	Operazione string     `json:"operation,omitempty"`
	Da         Stato      `json:"from,omitempty"`
	A          Stato      `json:"to,omitempty"`
	Azione     string     `json:"action,omitempty"`
	Fase       string     `json:"phase,omitempty"`
	Messaggio  *Messaggio `json:"message,omitempty"`
	Obj        string     `json:"object,omitempty"`
	RoutePath  string     `json:"path,omitempty"`
	Dettaglio  string     `json:"detail,omitempty"`
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
	e.scrivi(PublicEvent{Evento: "state", Operazione: op, Da: da, A: a, Dettaglio: dettaglio}, t)
}

func (e *Eventi) Azione(op, azione, fase, dettaglio string) {
	t := "      " + azione + ": " + fase
	if dettaglio != "" {
		t += " (" + dettaglio + ")"
	}
	e.scrivi(PublicEvent{Evento: "action", Operazione: op, Azione: azione, Fase: fase, Dettaglio: dettaglio}, t)
}

func (e *Eventi) Messaggio(op string, m Messaggio) {
	t := fmt.Sprintf("  [%s] %s %s", m.Codice, m.Gravita, m.Testo)
	if m.Dettaglio != "" {
		t += " (" + m.Dettaglio + ")"
	}
	if m.Remediation != "" {
		t += "\n      " + T("ev.rimedio") + ": " + m.Remediation
	}
	e.scrivi(PublicEvent{Evento: "message", Operazione: op, Messaggio: &m}, t)
}

func (e *Eventi) Obj(op, oggetto, percorso string) {
	e.scrivi(PublicEvent{Evento: "object", Operazione: op, Obj: oggetto, RoutePath: percorso}, "      "+oggetto+": "+percorso)
}
