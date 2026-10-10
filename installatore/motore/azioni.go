package motore

import (
	"encoding/json"
	"sort"
)

// Reversibilita: how far an action can be undone (§6.6.4).
type Reversibilita string

const (
	ESATTA         Reversibilita = "EXACT"
	AL_MEGLIO      Reversibilita = "BEST_EFFORT"
	CON_FOTOGRAFIA Reversibilita = "NEEDS_SNAPSHOT"
	IRREVERSIBILE  Reversibilita = "IRREVERSIBLE"
)

// Origine of a change: decides how far rolling back is authorised (§6.6.4).
type Origine string

const (
	DIRETTA      Origine = "DIRECT"
	INDIRETTA    Origine = "INDIRECT"
	PREESISTENTE Origine = "PREEXISTING"
	CONCORRENTE  Origine = "CONCURRENT"
)

// Esito of «controlla»: complete, absent, half-done (§6.6.3) — and a fourth case, which the
// check must be able to recognise so as not to cause damage: the effect belongs to someone else.
type Esito string

const (
	COMPLETO Esito = "COMPLETE"
	ASSENTE  Esito = "ABSENT"
	A_META   Esito = "HALF_DONE"
	ESTRANEO Esito = "FOREIGN" // neither our effect nor the before-state: a CONCURRENT change
)

// AzionePiano: an action as it stands in the plan — what, how it is done, how it is verified, how it is
// undone. The undo is born with the step (§6.0 point 3).
type AzionePiano struct {
	ID             string            `json:"id"`
	Tipo           string            `json:"type"`
	Parametri      map[string]string `json:"parameters"`
	Descrizione    string            `json:"description"`
	ComeSiFa       string            `json:"how_done"`
	ComeSiVerifica string            `json:"how_verified"`
	ComeSiAnnulla  string            `json:"how_rolled_back"`
	Reversibilita  Reversibilita     `json:"reversibility"`
	Consenso       string            `json:"consent,omitempty"` // the question, if the action has one of its own (D5, D6, IRREVERSIBLE)
}

// Contesto of a running action: the machine and the operation's folder (for the backups).
type Contesto struct {
	Amb      *Ambiente
	Cartella string
	P        AzionePiano
	// Purge: when undoing the packages the configuration is removed too. Rolling back
	// a failed installation is always purge (the machine as it was); uninstalling is purge only
	// if asked for (§6.5 point 3: remove keeps the configuration).
	Purge bool
}

// Riparabile: an action that, found half-done, is repaired with its tool's remedy instead of
// undoing and redoing (the package manager's transaction, §6.6.3).
type Riparabile interface {
	Ripara(c *Contesto, prima json.RawMessage) error
}

// Dichiarante: an action that leaves INDIRECT changes (§6.6.4) and declares them.
type Dichiarante interface {
	Indirette(prima json.RawMessage) []string
}

// Azione is the interface of §6.6.3-§6.6.4. Every method is idempotent: redoing it does not double
// the effect. «prima» is the before-state, taken ONCE by Fotografa and written in the log
// with the INTENTION.
type Azione interface {
	// Fotografa the before-state and says the origin (DIRETTA, or PREESISTENTE if the effect was already there).
	Fotografa(c *Contesto) (prima json.RawMessage, origine Origine, err error)
	Fai(c *Contesto, prima json.RawMessage) error
	// Controlla changes nothing: complete, absent, half-done, or foreign.
	Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error)
	// Annulla brings back to the before-state what is ours, and only that.
	Annulla(c *Contesto, prima json.RawMessage) error
	// Annullata: has the machine returned to the before-state (as far as the action is concerned)?
	Annullata(c *Contesto, prima json.RawMessage) (bool, string, error)
	// Vincoli: the elements of the binding fingerprint that the action touches or depends on (§6.6.5).
	Vincoli(c *Contesto) ([]string, error)
}

type costruttore func(p AzionePiano) (Azione, error)

var tipiAzione = map[string]costruttore{}

func registraTipo(tipo string, c costruttore) { tipiAzione[tipo] = c }

// NuovaAzione builds the action of a plan step.
func NuovaAzione(p AzionePiano) (Azione, error) {
	c, ok := tipiAzione[p.Tipo]
	if !ok {
		return nil, Errore("RX-PIANO-004", p.Tipo)
	}
	return c(p)
}

// TipiAzione: the types this engine knows.
func TipiAzione() []string {
	var r []string
	for t := range tipiAzione {
		r = append(r, t)
	}
	sort.Strings(r)
	return r
}

// PuntoDiProva is the hook of the interruption tests (R30 in small): the tests put in a
// function that kills the process at a precise point. ⛔ In the binary it is always nil: there is
// no way to switch it on from outside (no environment variables, no options) — R13.
var PuntoDiProva func(punto, azione string)

func punto(p, azione string) {
	if PuntoDiProva != nil {
		PuntoDiProva(p, azione)
	}
}

func jsonDi(v any) json.RawMessage { return json.RawMessage(JSONCanonico(v)) }
