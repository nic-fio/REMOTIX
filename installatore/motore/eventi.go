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
type EventoPubblico struct {
	Formato    string     `json:"format"`
	Ora        string     `json:"time"`
	Evento     string     `json:"event"` // stato · azione · messaggio · oggetto
	Operazione string     `json:"operation,omitempty"`
	Da         Stato      `json:"from,omitempty"`
	A          Stato      `json:"to,omitempty"`
	Azione     string     `json:"action,omitempty"`
	Fase       string     `json:"phase,omitempty"`
	Messaggio  *Messaggio `json:"message,omitempty"`
	Oggetto    string     `json:"object,omitempty"`
	Percorso   string     `json:"path,omitempty"`
	Dettaglio  string     `json:"detail,omitempty"`
}

func (e *Eventi) scrivi(ev EventoPubblico, testo string) {
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

func nomeStato(s Stato) string { return T("state." + string(s)) }

func (e *Eventi) Stato(op string, da, a Stato, dettaglio string) {
	t := "  → " + nomeStato(a)
	if dettaglio != "" {
		t += " — " + dettaglio
	}
	e.scrivi(EventoPubblico{Evento: "state", Operazione: op, Da: da, A: a, Dettaglio: dettaglio}, t)
}

func (e *Eventi) Azione(op, azione, fase, dettaglio string) {
	t := "      " + azione + ": " + fase
	if dettaglio != "" {
		t += " (" + dettaglio + ")"
	}
	e.scrivi(EventoPubblico{Evento: "action", Operazione: op, Azione: azione, Fase: fase, Dettaglio: dettaglio}, t)
}

func (e *Eventi) Messaggio(op string, m Messaggio) {
	t := fmt.Sprintf("  [%s] %s %s", m.Codice, m.Gravita, m.Testo)
	if m.Dettaglio != "" {
		t += " (" + m.Dettaglio + ")"
	}
	if m.Rimedio != "" {
		t += "\n      " + T("ev.rimedio") + ": " + m.Rimedio
	}
	e.scrivi(EventoPubblico{Evento: "message", Operazione: op, Messaggio: &m}, t)
}

func (e *Eventi) Oggetto(op, oggetto, percorso string) {
	e.scrivi(EventoPubblico{Evento: "object", Operazione: op, Oggetto: oggetto, Percorso: percorso}, "      "+oggetto+": "+percorso)
}
