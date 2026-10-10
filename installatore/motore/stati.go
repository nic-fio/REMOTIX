package motore

import "sort"

// State of an operation (§6.6.2).
type Stato string

const (
	NUOVA                   Stato = "NEW"
	FIDATA                  Stato = "TRUSTED"
	ESAMINATA               Stato = "EXAMINED"
	VALUTATA                Stato = "ASSESSED"
	PIANIFICATA             Stato = "PLANNED"
	APPROVATA               Stato = "APPROVED"
	ACQUISITA               Stato = "ACQUIRED"
	IN_ESECUZIONE           Stato = "RUNNING"
	INTERROTTA              Stato = "INTERRUPTED"
	APPLICATA               Stato = "APPLIED"
	IN_VERIFICA             Stato = "VERIFYING"
	VERIFICATA              Stato = "VERIFIED"
	CONFERMATA              Stato = "CONFIRMED"
	CONFERMATA_A_CONDIZIONI Stato = "CONFIRMED_WITH_CONDITIONS"
	IN_ANNULLAMENTO         Stato = "ROLLING_BACK"
	ANNULLATA               Stato = "ROLLED_BACK"
	ANNULLATA_IN_PARTE      Stato = "PARTIALLY_ROLLED_BACK"
	BLOCCATA                Stato = "BLOCKED"
	RIFIUTATA               Stato = "REFUSED"
)

// transizioni: the ONLY valid ones, those of the design of §6.6.2. ⛔ no state is skipped.
//
// BLOCCATA means ONLY «nothing has been touched» (§6.6.2) and is final. When the machine has already
// been touched and resume finds a DONE step undone by others (§6.6.3, last line), the state
// is INTERROTTA with the code RX-RIPRESA-001: one leaves it with riprendi or annulla (the
// coordinator's decision, 30 Sep). APPLICATA and VERIFICATA can go to IN_ANNULLAMENTO («red»).
var transizioni = map[Stato][]Stato{
	NUOVA:           {FIDATA, BLOCCATA},
	FIDATA:          {ESAMINATA, BLOCCATA},
	ESAMINATA:       {VALUTATA, BLOCCATA},
	VALUTATA:        {PIANIFICATA, BLOCCATA},
	PIANIFICATA:     {APPROVATA, RIFIUTATA, BLOCCATA},
	APPROVATA:       {ACQUISITA, BLOCCATA},
	ACQUISITA:       {IN_ESECUZIONE, BLOCCATA},
	IN_ESECUZIONE:   {APPLICATA, INTERROTTA, IN_ANNULLAMENTO},
	INTERROTTA:      {IN_ESECUZIONE, IN_ANNULLAMENTO},
	APPLICATA:       {IN_VERIFICA, IN_ANNULLAMENTO},
	IN_VERIFICA:     {VERIFICATA, IN_ANNULLAMENTO},
	VERIFICATA:      {CONFERMATA, CONFERMATA_A_CONDIZIONI, IN_ANNULLAMENTO},
	IN_ANNULLAMENTO: {ANNULLATA, ANNULLATA_IN_PARTE},
}

// Valida says whether da → a is a transition of the design.
func Valida(da, a Stato) bool {
	for _, x := range transizioni[da] {
		if x == a {
			return true
		}
	}
	return false
}

// Finale: the states one never leaves.
func Finale(s Stato) bool {
	switch s {
	case CONFERMATA, CONFERMATA_A_CONDIZIONI, ANNULLATA, ANNULLATA_IN_PARTE, RIFIUTATA, BLOCCATA:
		return true
	}
	return false
}

// TuttiGliStati, in alphabetical order (for the tests).
func TuttiGliStati() []Stato {
	visti := map[Stato]bool{}
	for da, aa := range transizioni {
		visti[da] = true
		for _, a := range aa {
			visti[a] = true
		}
	}
	var r []Stato
	for s := range visti {
		r = append(r, s)
	}
	sort.Slice(r, func(i, j int) bool { return r[i] < r[j] })
	return r
}
