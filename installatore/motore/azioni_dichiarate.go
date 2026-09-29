package motore

import "encoding/json"

// I passi che il motore CONOSCE ma non sa ancora eseguire: stanno nel piano (si vedono, si
// approvano, sono nell'impronta), ma un'operazione che ne contiene uno si ferma PRIMA di toccare
// la macchina, con RX-AZIONE-004. Dalla seconda parte di T4 i passi di §10.12 sono tutti veri
// (pacchetti, depositi, cinture, servizio, desktop): l'elenco è vuoto, il meccanismo resta.

// nonAncoraFatti: tipo → che cosa manca per farlo.
var nonAncoraFatti = map[string]string{}

func init() {
	for t := range nonAncoraFatti {
		registraTipo(t, func(p AzionePiano) (Azione, error) { return nonAncoraFatta{p.Tipo}, nil })
	}
}

type nonAncoraFatta struct{ tipo string }

func (n nonAncoraFatta) err() error {
	return Errore("RX-AZIONE-004", n.tipo+": "+nonAncoraFatti[n.tipo])
}

func (n nonAncoraFatta) Vincoli(*Contesto) ([]string, error) { return nil, nil }
func (n nonAncoraFatta) Fotografa(*Contesto) (json.RawMessage, Origine, error) {
	return nil, "", n.err()
}
func (n nonAncoraFatta) Fai(*Contesto, json.RawMessage) error { return n.err() }
func (n nonAncoraFatta) Controlla(*Contesto, json.RawMessage) (Esito, string, error) {
	return "", "", n.err()
}
func (n nonAncoraFatta) Annulla(*Contesto, json.RawMessage) error { return n.err() }
func (n nonAncoraFatta) Annullata(*Contesto, json.RawMessage) (bool, string, error) {
	return false, "", n.err()
}

// PassiNonFatti: i passi del piano che il motore non sa ancora eseguire.
func PassiNonFatti(p *Piano) []string {
	var r []string
	for _, a := range p.Azioni {
		if m, ok := nonAncoraFatti[a.Tipo]; ok {
			r = append(r, a.ID+" ("+a.Tipo+": "+m+")")
		}
	}
	return r
}
