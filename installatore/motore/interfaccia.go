package motore

// Quel che le interfacce (CLI e TUI) chiedono al motore oltre ai sette oggetti: che cosa dire a chi
// installa su QUESTA macchina. Dal 10 ott 2026 (DECISIONI §10.36) l'unica domanda è la porta, più il
// «sì» al piano: niente archivi di terzi, firewall o desktop da scegliere — quel che manca si dice.

// Domande: quel che si mostra e si chiede su questa macchina.
type Domande struct {
	// Porta: la predefinita (7447); si chiede sempre, una sola, vale per TCP e UDP
	Porta int `json:"port"`
	// Firewall: il nome del firewall acceso ("none" se nessuno): aprire la porta è dell'amministratore
	Firewall string `json:"firewall"`
	// SenzaScheda: le persone a cui manca il permesso di usare la scheda (il motore le iscrive)
	SenzaScheda []string `json:"no_gpu"`
	// Persone: chi potrà entrare (le persone della macchina; root è escluso)
	Persone []string `json:"people"`
}

// DomandeDaFare: quel che si mostra su questa macchina.
func DomandeDaFare(amb *Ambiente, porta int) *Domande {
	if porta == 0 {
		porta = 7447
	}
	d := &Domande{Porta: porta, Firewall: "none", SenzaScheda: []string{}, Persone: []string{}}
	if amb == nil {
		return d
	}
	if amb.Firewall != nil && amb.Firewall.Nome() != "" {
		d.Firewall = amb.Firewall.Nome()
	}
	if p := Persone(amb); p != nil {
		d.Persone = p
	}
	gruppi := GruppiScheda(amb)
	gr, _ := LeggiGruppi(amb.P("/etc/group"))
	for _, u := range d.Persone {
		for _, g := range gruppi {
			if !contiene(DividiMembri(gr[g][1]), u) {
				d.SenzaScheda = append(d.SenzaScheda, u)
				break
			}
		}
	}
	return d
}
