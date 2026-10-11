package engine

import (
	"sort"
	"strings"
)

// StateDone: detected is not verified (§6.6.7).
type StateDone string

const (
	DETECTED    StateDone = "DETECTED"
	VERIFIED_DONE  StateDone = "VERIFIED"
	UNKNOWN StateDone = "UNKNOWN"
)

// Fatto is a thing the PREFLIGHT knows (or knows it does not know) about the machine.
type Fatto struct {
	KeyId string    `json:"key"`
	Val   string    `json:"value"`
	State StateDone `json:"state"`
	Source string    `json:"source,omitempty"` // where it comes from: a file, a command
	Nota  string    `json:"note,omitempty"`
}

// Profilo of the machine: the first of the seven objects (§6.6.1).
type ProfileV struct {
	Schema  string      `json:"format"`
	Obj      string      `json:"object"` // "profile"
	Engine   string      `json:"engine"`
	Made     string      `json:"created"`
	Porta    int         `json:"port"`
	Facts    []Fatto     `json:"facts"`
	Messages []Message `json:"messages"`
	Commands  []string    `json:"commands"` // the programs launched to find out (R41): closed list
}

// NewProfile is an empty profile with its header.
func NewProfile(port int) *ProfileV {
	return &ProfileV{Schema: Schema, Obj: "profile", Engine: EngineVersion, Made: now(), Porta: port, Commands: []string{}}
}

// Metti adds or replaces a fact.
func (p *ProfileV) Place(f Fatto) {
	for i := range p.Facts {
		if p.Facts[i].KeyId == f.KeyId {
			p.Facts[i] = f
			return
		}
	}
	p.Facts = append(p.Facts, f)
}

// Detected, Verified, Unknown: shortcuts for Metti.
func (p *ProfileV) Detected(key, value, source string) {
	p.Place(Fatto{KeyId: key, Val: value, State: DETECTED, Source: source})
}
func (p *ProfileV) Verified(key, value, source string) {
	p.Place(Fatto{KeyId: key, Val: value, State: VERIFIED_DONE, Source: source})
}
func (p *ProfileV) Unknown(key, note string) {
	p.Place(Fatto{KeyId: key, Val: "", State: UNKNOWN, Nota: note})
}

// F returns a fact.
func (p *ProfileV) F(key string) (Fatto, bool) {
	for _, f := range p.Facts {
		if f.KeyId == key {
			return f, true
		}
	}
	return Fatto{}, false
}

// V is the value of a known fact (DETECTED or VERIFIED_DONE); "" if missing or UNKNOWN.
func (p *ProfileV) V(key string) string {
	f, ok := p.F(key)
	if !ok || f.State == UNKNOWN {
		return ""
	}
	return f.Val
}

// Con adds a message to the profile.
func (p *ProfileV) Con(code, detail string) {
	p.Messages = append(p.Messages, Msg(code, detail))
}

// Ordina puts facts in key order: the same profile always gives the same text.
func (p *ProfileV) Sort() {
	sort.Slice(p.Facts, func(i, j int) bool { return p.Facts[i].KeyId < p.Facts[j].KeyId })
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
	for _, piece := range strings.Split(v, ".") {
		n := 0
		for _, c := range piece {
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

// DesktopName is the name to display.
func DesktopName(d string) string {
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
