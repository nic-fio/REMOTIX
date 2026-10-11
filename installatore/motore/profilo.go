package motore

import (
	"sort"
	"strings"
)

// StateDone: detected is not verified (§6.6.7).
type StateDone string

const (
	RILEVATO    StateDone = "DETECTED"
	VERIFICATO  StateDone = "VERIFIED"
	SCONOSCIUTO StateDone = "UNKNOWN"
)

// Fatto is a thing the PREFLIGHT knows (or knows it does not know) about the machine.
type Fatto struct {
	KeyId string    `json:"key"`
	Val   string    `json:"value"`
	Stato StateDone `json:"state"`
	Fonte string    `json:"source,omitempty"` // where it comes from: a file, a command
	Nota  string    `json:"note,omitempty"`
}

// Profilo of the machine: the first of the seven objects (§6.6.1).
type ProfileV struct {
	Formato  string      `json:"format"`
	Obj      string      `json:"object"` // "profile"
	Motore   string      `json:"engine"`
	Made     string      `json:"created"`
	Porta    int         `json:"port"`
	Fatti    []Fatto     `json:"facts"`
	Messages []Messaggio `json:"messages"`
	Comandi  []string    `json:"commands"` // the programs launched to find out (R41): closed list
}

// NewProfile is an empty profile with its header.
func NewProfile(porta int) *ProfileV {
	return &ProfileV{Formato: Formato, Obj: "profile", Motore: VersioneMotore, Made: ora(), Porta: porta, Comandi: []string{}}
}

// Metti adds or replaces a fact.
func (p *ProfileV) Place(f Fatto) {
	for i := range p.Fatti {
		if p.Fatti[i].KeyId == f.KeyId {
			p.Fatti[i] = f
			return
		}
	}
	p.Fatti = append(p.Fatti, f)
}

// Rilevato, Verificato, Sconosciuto: shortcuts for Metti.
func (p *ProfileV) Rilevato(chiave, valore, fonte string) {
	p.Place(Fatto{KeyId: chiave, Val: valore, Stato: RILEVATO, Fonte: fonte})
}
func (p *ProfileV) Verificato(chiave, valore, fonte string) {
	p.Place(Fatto{KeyId: chiave, Val: valore, Stato: VERIFICATO, Fonte: fonte})
}
func (p *ProfileV) Sconosciuto(chiave, nota string) {
	p.Place(Fatto{KeyId: chiave, Val: "", Stato: SCONOSCIUTO, Nota: nota})
}

// F returns a fact.
func (p *ProfileV) F(chiave string) (Fatto, bool) {
	for _, f := range p.Fatti {
		if f.KeyId == chiave {
			return f, true
		}
	}
	return Fatto{}, false
}

// V is the value of a known fact (RILEVATO or VERIFICATO); "" if missing or SCONOSCIUTO.
func (p *ProfileV) V(chiave string) string {
	f, ok := p.F(chiave)
	if !ok || f.Stato == SCONOSCIUTO {
		return ""
	}
	return f.Val
}

// Con adds a message to the profile.
func (p *ProfileV) Con(codice, dettaglio string) {
	p.Messages = append(p.Messages, Msg(codice, dettaglio))
}

// Ordina puts facts in key order: the same profile always gives the same text.
func (p *ProfileV) Sort() {
	sort.Slice(p.Fatti, func(i, j int) bool { return p.Fatti[i].KeyId < p.Fatti[j].KeyId })
}

// CompareVersions compares two «dotted» versions (1.25.0, 6.3.6, 3.5.1): -1, 0, 1. It strips
// the epoch (1:) and the package revision (-1, +dfsg, ~bpo). What is not a number counts as 0.
func CompareVersions(a, b string) int {
	pa, pb := versionNumbers(a), versionNumbers(b)
	for i := 0; i < len(pa) || i < len(pb); i++ {
		var x, y int
		if i < len(pa) {
			x = pa[i]
		}
		if i < len(pb) {
			y = pb[i]
		}
		if x != y {
			if x < y {
				return -1
			}
			return 1
		}
	}
	return 0
}

func versionNumbers(v string) []int {
	if i := strings.Index(v, ":"); i >= 0 {
		v = v[i+1:]
	}
	for _, sep := range []string{"-", "+", "~"} {
		if i := strings.Index(v, sep); i >= 0 {
			v = v[:i]
		}
	}
	var r []int
	for _, pezzo := range strings.Split(v, ".") {
		n := 0
		for _, c := range pezzo {
			if c < '0' || c > '9' {
				break
			}
			n = n*10 + int(c-'0')
		}
		r = append(r, n)
	}
	return r
}

// DESKTOP are REMOTIX's four desktops, in the order they are written everywhere.
var DESKTOP = []string{"gnome", "kde", "xfce", "lxqt"}

// NomeDesktop is the name to display.
func NomeDesktop(d string) string {
	switch d {
	case "gnome":
		return "GNOME"
	case "kde":
		return "KDE Plasma"
	case "xfce":
		return "XFCE"
	case "lxqt":
		return "LXQt"
	}
	return d
}

func siNo(b bool) string {
	if b {
		return "yes"
	}
	return "no"
}
