package motore

import (
	"sort"
	"strings"
)

// StatoFatto: rilevato non è verificato (§6.6.7).
type StatoFatto string

const (
	RILEVATO    StatoFatto = "DETECTED"
	VERIFICATO  StatoFatto = "VERIFIED"
	SCONOSCIUTO StatoFatto = "UNKNOWN"
)

// Fatto è una cosa che il PREFLIGHT sa (o sa di non sapere) della macchina.
type Fatto struct {
	Chiave string     `json:"key"`
	Valore string     `json:"value"`
	Stato  StatoFatto `json:"state"`
	Fonte  string     `json:"source,omitempty"` // da dove viene: un file, un comando
	Nota   string     `json:"note,omitempty"`
}

// Profilo della macchina: il primo dei sette oggetti (§6.6.1).
type Profilo struct {
	Formato  string      `json:"format"`
	Oggetto  string      `json:"object"` // "profile"
	Motore   string      `json:"engine"`
	Creato   string      `json:"created"`
	Porta    int         `json:"port"`
	Fatti    []Fatto     `json:"facts"`
	Messaggi []Messaggio `json:"messages"`
	Comandi  []string    `json:"commands"` // i programmi lanciati per saperlo (R41): elenco chiuso
}

// NuovoProfilo è un profilo vuoto con la sua intestazione.
func NuovoProfilo(porta int) *Profilo {
	return &Profilo{Formato: Formato, Oggetto: "profile", Motore: VersioneMotore, Creato: ora(), Porta: porta, Comandi: []string{}}
}

// Metti aggiunge o sostituisce un fatto.
func (p *Profilo) Metti(f Fatto) {
	for i := range p.Fatti {
		if p.Fatti[i].Chiave == f.Chiave {
			p.Fatti[i] = f
			return
		}
	}
	p.Fatti = append(p.Fatti, f)
}

// Rilevato, Verificato, Sconosciuto: scorciatoie per Metti.
func (p *Profilo) Rilevato(chiave, valore, fonte string) {
	p.Metti(Fatto{Chiave: chiave, Valore: valore, Stato: RILEVATO, Fonte: fonte})
}
func (p *Profilo) Verificato(chiave, valore, fonte string) {
	p.Metti(Fatto{Chiave: chiave, Valore: valore, Stato: VERIFICATO, Fonte: fonte})
}
func (p *Profilo) Sconosciuto(chiave, nota string) {
	p.Metti(Fatto{Chiave: chiave, Valore: "", Stato: SCONOSCIUTO, Nota: nota})
}

// F restituisce un fatto.
func (p *Profilo) F(chiave string) (Fatto, bool) {
	for _, f := range p.Fatti {
		if f.Chiave == chiave {
			return f, true
		}
	}
	return Fatto{}, false
}

// V è il valore di un fatto noto (RILEVATO o VERIFICATO); "" se manca o è SCONOSCIUTO.
func (p *Profilo) V(chiave string) string {
	f, ok := p.F(chiave)
	if !ok || f.Stato == SCONOSCIUTO {
		return ""
	}
	return f.Valore
}

// Con aggiunge un messaggio al profilo.
func (p *Profilo) Con(codice, dettaglio string) {
	p.Messaggi = append(p.Messaggi, Msg(codice, dettaglio))
}

// Ordina mette fatti in ordine di chiave: lo stesso profilo dà sempre lo stesso testo.
func (p *Profilo) Ordina() {
	sort.Slice(p.Fatti, func(i, j int) bool { return p.Fatti[i].Chiave < p.Fatti[j].Chiave })
}

// ConfrontaVersioni confronta due versioni «a punti» (1.25.0, 6.3.6, 3.5.1): -1, 0, 1. Toglie
// l'epoca (1:) e la revisione del pacchetto (-1, +dfsg, ~bpo). Quel che non è un numero vale 0.
func ConfrontaVersioni(a, b string) int {
	pa, pb := numeriVersione(a), numeriVersione(b)
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

func numeriVersione(v string) []int {
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

// DESKTOP sono i quattro desktop di REMOTIX, nell'ordine in cui si scrivono dappertutto.
var DESKTOP = []string{"gnome", "kde", "xfce", "lxqt"}

// NomeDesktop è il nome da mostrare.
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
