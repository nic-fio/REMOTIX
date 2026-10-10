package motore

import "encoding/json"

// The steps the engine KNOWS but cannot execute yet: they are in the plan (they are seen,
// approved, part of the fingerprint), but an operation containing one stops BEFORE touching
// the machine, with RX-AZIONE-004. Since the second part of T4 the steps of §10.12 are all real
// (packages, repositories, belts, service, desktop): the list is empty, the mechanism remains.

// nonAncoraFatti: type → what is missing to do it.
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

// PassiNonFatti: the plan's steps the engine cannot execute yet.
func PassiNonFatti(p *Piano) []string {
	var r []string
	for _, a := range p.Azioni {
		if m, ok := nonAncoraFatti[a.Tipo]; ok {
			r = append(r, a.ID+" ("+a.Tipo+": "+m+")")
		}
	}
	return r
}
