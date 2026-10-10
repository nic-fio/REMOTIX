package motore

import (
	"encoding/json"
	"sort"
)

// Reversibilita: quanto un'azione si annulla (§6.6.4).
type Reversibilita string

const (
	ESATTA         Reversibilita = "EXACT"
	AL_MEGLIO      Reversibilita = "BEST_EFFORT"
	CON_FOTOGRAFIA Reversibilita = "NEEDS_SNAPSHOT"
	IRREVERSIBILE  Reversibilita = "IRREVERSIBLE"
)

// Origine di una modifica: decide fin dove il ritorno indietro è autorizzato (§6.6.4).
type Origine string

const (
	DIRETTA      Origine = "DIRECT"
	INDIRETTA    Origine = "INDIRECT"
	PREESISTENTE Origine = "PREEXISTING"
	CONCORRENTE  Origine = "CONCURRENT"
)

// Esito di «controlla»: completo, assente, a metà (§6.6.3) — e un quarto caso, che il
// controllo deve saper riconoscere per non fare danni: l'effetto è di qualcun altro.
type Esito string

const (
	COMPLETO Esito = "COMPLETE"
	ASSENTE  Esito = "ABSENT"
	A_META   Esito = "HALF_DONE"
	ESTRANEO Esito = "FOREIGN" // né il nostro effetto né lo stato di prima: modifica CONCORRENTE
)

// AzionePiano: un'azione come sta nel piano — che cosa, come si fa, come si verifica, come si
// annulla. L'annullamento nasce col passo (§6.0 punto 3).
type AzionePiano struct {
	ID             string            `json:"id"`
	Tipo           string            `json:"type"`
	Parametri      map[string]string `json:"parameters"`
	Descrizione    string            `json:"description"`
	ComeSiFa       string            `json:"how_done"`
	ComeSiVerifica string            `json:"how_verified"`
	ComeSiAnnulla  string            `json:"how_rolled_back"`
	Reversibilita  Reversibilita     `json:"reversibility"`
	Consenso       string            `json:"consent,omitempty"` // la domanda, se l'azione ne ha una sua (D5, D6, IRREVERSIBILE)
}

// Contesto di un'azione che gira: la macchina e la cartella dell'operazione (per i salvataggi).
type Contesto struct {
	Amb      *Ambiente
	Cartella string
	P        AzionePiano
	// Purge: nell'annullare i pacchetti si toglie anche la configurazione. Il ritorno indietro di
	// un'installazione fallita è sempre purge (la macchina com'era); la disinstallazione lo è solo
	// se lo si chiede (§6.5 punto 3: remove tiene la configurazione).
	Purge bool
}

// Riparabile: un'azione che, trovata a metà, si ripara col rimedio del suo strumento invece di
// annullare e rifare (la transazione del gestore di pacchetti, §6.6.3).
type Riparabile interface {
	Ripara(c *Contesto, prima json.RawMessage) error
}

// Dichiarante: un'azione che lascia modifiche INDIRETTE (§6.6.4) e le dichiara.
type Dichiarante interface {
	Indirette(prima json.RawMessage) []string
}

// Azione è l'interfaccia di §6.6.3-§6.6.4. Ogni metodo è idempotente: rifarlo non raddoppia
// l'effetto. «prima» è lo stato di prima, preso UNA volta da Fotografa e scritto nel registro
// con l'INTENZIONE.
type Azione interface {
	// Fotografa lo stato di prima e dice l'origine (DIRETTA, o PREESISTENTE se l'effetto c'era già).
	Fotografa(c *Contesto) (prima json.RawMessage, origine Origine, err error)
	Fai(c *Contesto, prima json.RawMessage) error
	// Controlla non cambia niente: completo, assente, a metà, o estraneo.
	Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error)
	// Annulla riporta allo stato di prima quel che è nostro, e solo quello.
	Annulla(c *Contesto, prima json.RawMessage) error
	// Annullata: la macchina è tornata allo stato di prima (per quel che riguarda l'azione)?
	Annullata(c *Contesto, prima json.RawMessage) (bool, string, error)
	// Vincoli: gli elementi dell'impronta vincolante che l'azione tocca o da cui dipende (§6.6.5).
	Vincoli(c *Contesto) ([]string, error)
}

type costruttore func(p AzionePiano) (Azione, error)

var tipiAzione = map[string]costruttore{}

func registraTipo(tipo string, c costruttore) { tipiAzione[tipo] = c }

// NuovaAzione costruisce l'azione di un passo del piano.
func NuovaAzione(p AzionePiano) (Azione, error) {
	c, ok := tipiAzione[p.Tipo]
	if !ok {
		return nil, Errore("RX-PIANO-004", p.Tipo)
	}
	return c(p)
}

// TipiAzione: i tipi che questo motore conosce.
func TipiAzione() []string {
	var r []string
	for t := range tipiAzione {
		r = append(r, t)
	}
	sort.Strings(r)
	return r
}

// PuntoDiProva è il gancio delle prove di interruzione (R30 in piccolo): le prove ci mettono una
// funzione che uccide il processo in un punto preciso. ⛔ Nel binario è sempre nil: non esiste
// nessun modo di accenderlo da fuori (niente variabili d'ambiente, niente opzioni) — R13.
var PuntoDiProva func(punto, azione string)

func punto(p, azione string) {
	if PuntoDiProva != nil {
		PuntoDiProva(p, azione)
	}
}

func jsonDi(v any) json.RawMessage { return json.RawMessage(JSONCanonico(v)) }
