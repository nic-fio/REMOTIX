package motore

import "encoding/json"

// The steps the engine KNOWS but cannot execute yet: they are in the plan (they are seen,
// approved, part of the fingerprint), but an operation containing one stops BEFORE touching
// the machine, with RX-AZIONE-004. Since the second part of T4 the steps of §10.12 are all real
// (packages, repositories, belts, service, desktop): the list is empty, the mechanism remains.

// notYetDoneWhy: type → what is missing to do it.
var notYetDoneWhy = map[string]string{}

func init() {
	for t := range notYetDoneWhy {
		registraTipo(t, func(p AzionePiano) (Azione, error) { return notYetDone{p.Tipo}, nil })
	}
}

type notYetDone struct{ tipo string }

func (n notYetDone) err() error {
	return Errore("RX-AZIONE-004", n.tipo+": "+notYetDoneWhy[n.tipo])
}

func (n notYetDone) Vincoli(*Contesto) ([]string, error) { return nil, nil }
func (n notYetDone) Fotografa(*Contesto) (json.RawMessage, Origine, error) {
	return nil, "", n.err()
}
func (n notYetDone) Fai(*Contesto, json.RawMessage) error { return n.err() }
func (n notYetDone) Controlla(*Contesto, json.RawMessage) (Esito, string, error) {
	return "", "", n.err()
}
func (n notYetDone) Annulla(*Contesto, json.RawMessage) error { return n.err() }
func (n notYetDone) Annullata(*Contesto, json.RawMessage) (bool, string, error) {
	return false, "", n.err()
}

// UnimplementedSteps: the plan's steps the engine cannot execute yet.
func UnimplementedSteps(p *Piano) []string {
	var r []string
	for _, a := range p.Azioni {
		if m, ok := notYetDoneWhy[a.Tipo]; ok {
			r = append(r, a.ID+" ("+a.Tipo+": "+m+")")
		}
	}
	return r
}
