package motore

import (
	"sort"
	"strings"
)

// StateDone: detected is not verified (§6.6.7).
type StateDone string

const (
	DETECTED StateDone = "DETECTED"
	CHECKED  StateDone = "VERIFIED"
	UNKNOWN  StateDone = "UNKNOWN"
)

// Done is a thing the PREFLIGHT knows (or knows it does not know) about the machine.
type Done struct {
	Key    string    `json:"key"`
	Value  string    `json:"value"`
	State  StateDone `json:"state"`
	Source string    `json:"source,omitempty"` // where it comes from: a file, a command
	Note   string    `json:"note,omitempty"`
}

// Profile of the machine: the first of the seven objects (§6.6.1).
type Profile struct {
	Schema   string    `json:"format"`
	Object   string    `json:"object"` // "profile"
	Engine   string    `json:"engine"`
	Created  string    `json:"created"`
	Port     int       `json:"port"`
	Facts    []Done    `json:"facts"`
	Messages []Message `json:"messages"`
	Commands []string  `json:"commands"` // the programs launched to find out (R41): closed list
}

// NewProfile is an empty profile with its header.
func NewProfile(port int) *Profile {
	return &Profile{Schema: Schema, Object: "profile", Engine: EngineVersion, Created: now(), Port: port, Commands: []string{}}
}

// Put adds or replaces a fact.
func (p *Profile) Put(f Done) {
	for i := range p.Facts {
		if p.Facts[i].Key == f.Key {
			p.Facts[i] = f
			return
		}
	}
	p.Facts = append(p.Facts, f)
}

// Detected, Verified, Unknown: shortcuts for Put.
func (p *Profile) Detected(key_id, value_v, source string) {
	p.Put(Done{Key: key_id, Value: value_v, State: DETECTED, Source: source})
}
func (p *Profile) Verified(key_id, value_v, source string) {
	p.Put(Done{Key: key_id, Value: value_v, State: CHECKED, Source: source})
}
func (p *Profile) Unknown(key_id, remark string) {
	p.Put(Done{Key: key_id, Value: "", State: UNKNOWN, Note: remark})
}

// F returns a fact.
func (p *Profile) F(key_id string) (Done, bool) {
	for _, f := range p.Facts {
		if f.Key == key_id {
			return f, true
		}
	}
	return Done{}, false
}

// V is the value of a known fact (DETECTED or CHECKED); "" if missing or UNKNOWN.
func (p *Profile) V(key_id string) string {
	f, ok := p.F(key_id)
	if !ok || f.State == UNKNOWN {
		return ""
	}
	return f.Value
}

// Con adds a message to the profile.
func (p *Profile) Con(code_v, detail string) {
	p.Messages = append(p.Messages, Msg(code_v, detail))
}

// Sort puts facts in key order: the same profile always gives the same text.
func (p *Profile) Sort() {
	sort.Slice(p.Facts, func(i, j int) bool { return p.Facts[i].Key < p.Facts[j].Key })
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
