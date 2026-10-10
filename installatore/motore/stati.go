package motore

import "sort"

// Stato di un'operazione (§6.6.2).
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

// transizioni: le SOLE valide, quelle del disegno di §6.6.2. ⛔ nessuno stato si salta.
//
// BLOCCATA vuol dire SOLO «niente è stato toccato» (§6.6.2) ed è finale. Quando la macchina è già
// stata toccata e la ripresa trova un passo FATTO disfatto da altri (§6.6.3, ultima riga), lo stato
// è INTERROTTA col codice RX-RIPRESA-001: se ne esce con riprendi o annulla (decisione del
// coordinatore, 30 set). APPLICATA e VERIFICATA possono andare a IN_ANNULLAMENTO («rosso»).
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

// Valida dice se da → a è una transizione del disegno.
func Valida(da, a Stato) bool {
	for _, x := range transizioni[da] {
		if x == a {
			return true
		}
	}
	return false
}

// Finale: gli stati da cui non si esce.
func Finale(s Stato) bool {
	switch s {
	case CONFERMATA, CONFERMATA_A_CONDIZIONI, ANNULLATA, ANNULLATA_IN_PARTE, RIFIUTATA, BLOCCATA:
		return true
	}
	return false
}

// TuttiGliStati, in ordine alfabetico (per le prove).
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
