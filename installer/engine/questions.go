package engine

// What the interfaces (CLI and TUI) ask the engine beyond the seven objects: what to tell whoever
// installs on THIS machine. Since 10 Oct 2026 (DECISIONI §10.36) the only question is the port, plus the
// «yes» to the plan: no third-party repositories, firewalls or desktops to choose — what is missing is stated.

// Questions: what is shown and asked on this machine.
type Questions struct {
	// Porta: the default (7447); always asked, just one, valid for TCP and UDP
	Porta int `json:"port"`
	// Firewall: the name of the running firewall ("none" if none): opening the port is the administrator's job
	Firewall string `json:"firewall"`
	// NoCard: the people lacking permission to use the card (the engine enrolls them)
	NoCard []string `json:"no_gpu"`
	// People: who will be able to log in (the machine's people; root is excluded)
	People []string `json:"people"`
}

// QuestionsToAsk: what is shown on this machine.
func QuestionsToAsk(env *Environment, port int) *Questions {
	if port == 0 {
		port = 7447
	}
	d := &Questions{Porta: port, Firewall: "none", NoCard: []string{}, People: []string{}}
	if env == nil {
		return d
	}
	if env.Firewall != nil && env.Firewall.Nome() != "" {
		d.Firewall = env.Firewall.Nome()
	}
	if p := People(env); p != nil {
		d.People = p
	}
	groups := CardGroups(env)
	gr, _ := ReadGroups(env.P("/etc/group"))
	for _, u := range d.People {
		for _, g := range groups {
			if !contains(SplitMembers(gr[g][1]), u) {
				d.NoCard = append(d.NoCard, u)
				break
			}
		}
	}
	return d
}
