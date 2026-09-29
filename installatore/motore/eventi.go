package motore

import (
	"encoding/json"
	"fmt"
	"io"
)

// Eventi: quel che il motore dice mentre lavora. Due forme, stesso contenuto:
//   - JSON, una riga per evento (--eventi): è il canale delle future TUI e GUI (§6.6.1, R36);
//   - testo in italiano semplice, per chi guarda il terminale.
//
// ⛔ Le interfacce non ricevono niente che non stia anche negli oggetti su disco: gli eventi
// dicono «è successo», gli oggetti dicono «com'è».
type Eventi struct {
	W    io.Writer
	JSON bool
}

// Evento pubblico (JSON a riga).
type EventoPubblico struct {
	Formato    string     `json:"formato"`
	Ora        string     `json:"ora"`
	Evento     string     `json:"evento"` // stato · azione · messaggio · oggetto
	Operazione string     `json:"operazione,omitempty"`
	Da         Stato      `json:"da,omitempty"`
	A          Stato      `json:"a,omitempty"`
	Azione     string     `json:"azione,omitempty"`
	Fase       string     `json:"fase,omitempty"`
	Messaggio  *Messaggio `json:"messaggio,omitempty"`
	Oggetto    string     `json:"oggetto,omitempty"`
	Percorso   string     `json:"percorso,omitempty"`
	Dettaglio  string     `json:"dettaglio,omitempty"`
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

func nomeStato(s Stato) string { return T("stato." + string(s)) }

func (e *Eventi) Stato(op string, da, a Stato, dettaglio string) {
	t := "  → " + nomeStato(a)
	if dettaglio != "" {
		t += " — " + dettaglio
	}
	e.scrivi(EventoPubblico{Evento: "stato", Operazione: op, Da: da, A: a, Dettaglio: dettaglio}, t)
}

func (e *Eventi) Azione(op, azione, fase, dettaglio string) {
	t := "      " + azione + ": " + fase
	if dettaglio != "" {
		t += " (" + dettaglio + ")"
	}
	e.scrivi(EventoPubblico{Evento: "azione", Operazione: op, Azione: azione, Fase: fase, Dettaglio: dettaglio}, t)
}

func (e *Eventi) Messaggio(op string, m Messaggio) {
	t := fmt.Sprintf("  [%s] %s %s", m.Codice, m.Gravita, m.Testo)
	if m.Dettaglio != "" {
		t += " (" + m.Dettaglio + ")"
	}
	if m.Rimedio != "" {
		t += "\n      " + T("ev.rimedio") + ": " + m.Rimedio
	}
	e.scrivi(EventoPubblico{Evento: "messaggio", Operazione: op, Messaggio: &m}, t)
}

func (e *Eventi) Oggetto(op, oggetto, percorso string) {
	e.scrivi(EventoPubblico{Evento: "oggetto", Operazione: op, Oggetto: oggetto, Percorso: percorso}, "      "+oggetto+": "+percorso)
}
