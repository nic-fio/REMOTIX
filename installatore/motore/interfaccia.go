package motore

// What the interfaces (CLI and TUI) ask the engine beyond the seven objects: what to tell whoever
// installs on THIS machine. Since 10 Oct 2026 (DECISIONI §10.36) the only question is the port, plus the
// «yes» to the plan: no third-party repositories, firewalls or desktops to choose — what is missing is stated.

// Domande: what is shown and asked on this machine.
type Questions struct {
	// Porta: the default (7447); always asked, just one, valid for TCP and UDP
	Porta int `json:"port"`
	// Firewall: the name of the running firewall ("none" if none): opening the port is the administrator's job
	Firewall string `json:"firewall"`
	// NoCard: the people lacking permission to use the card (the engine enrolls them)
	NoCard []string `json:"no_gpu"`
	// Persone: who will be able to log in (the machine's people; root is excluded)
	People []string `json:"people"`
}

// DomandeDaFare: what is shown on this machine.
func DomandeDaFare(amb *Ambiente, porta int) *Questions {
	if porta == 0 {
		porta = 7447
	}
	d := &Questions{Porta: porta, Firewall: "none", NoCard: []string{}, People: []string{}}
	if amb == nil {
		return d
	}
	if amb.Firewall != nil && amb.Firewall.Nome() != "" {
		d.Firewall = amb.Firewall.Nome()
	}
	if p := People(amb); p != nil {
		d.People = p
	}
	gruppi := GruppiScheda(amb)
	gr, _ := ReadGroups(amb.P("/etc/group"))
	for _, u := range d.People {
		for _, g := range gruppi {
			if !contiene(SplitMembers(gr[g][1]), u) {
				d.NoCard = append(d.NoCard, u)
				break
			}
		}
	}
	return d
}
