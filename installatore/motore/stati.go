package motore

import "sort"

// Stato di un'operazione (§6.6.2).
type Stato string

const (
	NUOVA                   Stato = "NUOVA"
	FIDATA                  Stato = "FIDATA"
	ESAMINATA               Stato = "ESAMINATA"
	VALUTATA                Stato = "VALUTATA"
	PIANIFICATA             Stato = "PIANIFICATA"
	APPROVATA               Stato = "APPROVATA"
	ACQUISITA               Stato = "ACQUISITA"
	IN_ESECUZIONE           Stato = "IN_ESECUZIONE"
	INTERROTTA              Stato = "INTERROTTA"
	APPLICATA               Stato = "APPLICATA"
	IN_VERIFICA             Stato = "IN_VERIFICA"
	VERIFICATA              Stato = "VERIFICATA"
	CONFERMATA              Stato = "CONFERMATA"
	CONFERMATA_A_CONDIZIONI Stato = "CONFERMATA_A_CONDIZIONI"
	IN_ANNULLAMENTO         Stato = "IN_ANNULLAMENTO"
	ANNULLATA               Stato = "ANNULLATA"
	ANNULLATA_IN_PARTE      Stato = "ANNULLATA_IN_PARTE"
	BLOCCATA                Stato = "BLOCCATA"
	RIFIUTATA               Stato = "RIFIUTATA"
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
