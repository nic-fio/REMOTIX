package interfaccia

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"remotix/installatore/motore"
)

// The VIEW: the engine's objects in plain words, for the five screens and the variants
// (fasi/17 §10). The TUI draws these values and nothing else.

// State of a line: the colour of the label.
type State int

const (
	OK State = iota
	CONSENT
	FIX
	DOPO
	MALE
	UNKNOWN
	WARNING // does not stop: it is stated (the running firewall, the port in use)
	MISSING // stops: REMOTIX does not provide it, it says so (§10.36)
)

// Cartellino: the label text of a state, in the right-hand column of the check.
func (s State) Tag() string {
	return [...]string{T("s.ok"), T("s.consenso"), T("s.sistemo"), T("s.dopo"), T("s.male"), T("s.nonsi"),
		T("s.avviso"), T("s.manca")}[s]
}

// Line: a line of the check or of the tests.
type Line struct {
	Etichetta, Testo string
	State            State
}

// Outcome of the check.
type CheckOutcome int

const (
	READY CheckOutcome = iota
	CONDS
	BLOCKED
)

// CheckView: screen 1. With Outcome == BLOCKED and Righe filled it is «something is missing»: the lines
// with the MISSING label, and the codes; with Righe empty it is an ending (Blocked: distribution out…).
type CheckView struct {
	Header        string // «Fedora Linux 44 · Workstation · GNOME 50»
	Outcome       CheckOutcome
	Banner, Below string
	Righe         []Line
	Codes         []string // the RX codes of what is missing
	Dettagli      string
	Blocked       *BlockedView // if Outcome == BLOCKED
}

// BlockedView: a screen that ends (not supported, stopped, cancelled).
type BlockedView struct {
	Titolo, Below string
	Why, CheFare  string
	Needs         string // «At least Debian 13 is needed.»
	Codice        string
	Dettagli      string
	Toccata       bool // the machine was touched (cancelled): the circle is not red but amber
}

// ChoicesView: screen 2 — the port.
type ChoicesView struct {
	Titolo, Below string
	PortLine      string // the line under the port (green if there is no running firewall)
	PortGreen     bool
}

// Passo: a line of the plan, with the engine actions it gathers.
type Stride struct {
	Type                string // "packages" · "groups" · "service" · "other"
	Titolo, Nota, Below string
	Fatto               string // how the welcome says it
	Rev                 State  // OK = fully undone · CONSENT = partly · MALE = not undone
	Azioni              []string
	Breve               string // how the progress says it
}

// Cartellino of the reversibility.
func (p Stride) Tag() string {
	switch p.Rev {
	case OK:
		return T("rev.tutto")
	case MALE:
		return T("rev.no")
	}
	return T("rev.parte")
}

// VistaPiano: screen 3.
type VistaPiano struct {
	Steps    []Stride
	Dettagli string
	// Pacchetti: what the manager will do (its simulation), to show before the «yes»
	Pacchetti []engine.Artifact
	// Utenti and Gruppi: whom the engine enrolls in the card's groups, and in which
	Utenti, Gruppi []string
	// Porta: the service's, as the plan says it
	Porta string
	// Dipendenze: for the packages the desktop requires of REMOTIX, for which desktop
	Dipendenze map[string]string
}

// ---- 1 · the check ---------------------------------------------------------------------------

func distroName(prof *engine.ProfileV) string {
	id := prof.V("distro.id")
	switch id {
	case "debian":
		return "Debian"
	case "ubuntu":
		return "Ubuntu"
	case "fedora":
		return "Fedora"
	case "almalinux":
		return "AlmaLinux"
	case "arch":
		return "Arch Linux"
	case "opensuse-tumbleweed", "opensuse-leap", "opensuse":
		return "openSUSE"
	}
	n := prof.V("distro.name")
	if i := strings.IndexAny(n, " ("); i > 0 {
		return n[:i]
	}
	if n == "" {
		return "Linux"
	}
	return n
}

var desktopNames = map[string]string{"gnome": "GNOME", "kde": "KDE Plasma", "xfce": "XFCE", "lxqt": "LXQt"}

// DesktopName: the name to display.
func DesktopName(d string) string {
	if n, ok := desktopNames[d]; ok {
		return n
	}
	return d
}

func installed(e engine.DesktopOutcome) bool {
	return e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown"
}

// Header: the line at the top right.
func Header(prof *engine.ProfileV, rap *engine.Report) string {
	if prof == nil {
		return ""
	}
	n := prof.V("distro.name")
	if i := strings.Index(n, " ("); i > 0 {
		n = n[:i]
	}
	parts := []string{n}
	if v := prof.V("distro.variant"); v != "" {
		parts = append(parts, strings.ToUpper(v[:1])+v[1:])
	}
	var ds []string
	if rap != nil {
		for _, e := range rap.Desktop {
			if installed(e) {
				v := e.Installed
				if i := strings.Index(v, ":"); i > 0 { // Debian's epoch: «4:6.3.6-1»
					v = v[i+1:]
				}
				if i := strings.Index(v, "."); i > 0 {
					v = v[:i]
				}
				ds = append(ds, DesktopName(e.Desktop)+" "+v)
			}
		}
	}
	if len(ds) == 0 && rap != nil && rap.NoDesktop {
		ds = append(ds, "no desktop")
	}
	return strings.Join(append(parts, ds...), " · ")
}

func conditionOf(rap *engine.Report, code string) bool {
	for _, e := range rap.Desktop {
		if e.Lvl == engine.NOT_SUPPORTED || !installed(e) {
			continue
		}
		for _, k := range e.Condizioni {
			if k.Codice == code {
				return true
			}
		}
	}
	return false
}

func hasMessage(ms []engine.Message, code string) *engine.Message {
	for i := range ms {
		if ms[i].Codice == code {
			return &ms[i]
		}
	}
	return nil
}

// cardName: the card in plain words (driver and bus are in the technical details).
func cardName(prof *engine.ProfileV) string {
	nodes := strings.Fields(prof.V("gpu.nodes"))
	if len(nodes) == 0 {
		return ""
	}
	f := strings.ToLower(prof.V("gpu." + nodes[0] + ".vendor"))
	switch {
	case strings.Contains(f, "intel"):
		return T("t.scheda.marca", "Intel")
	case strings.Contains(f, "amd") || strings.Contains(f, "ati"):
		return T("t.scheda.marca", "AMD")
	case strings.Contains(f, "nvidia"):
		return T("t.scheda.marca", "NVIDIA")
	case strings.Contains(f, "virtio") || strings.Contains(f, "qxl") || strings.Contains(f, "vmware") || strings.Contains(f, "bochs"):
		return T("t.scheda.virtuale")
	}
	return T("t.scheda.generica")
}

// CheckReport: screen 1 from the engine's objects.
func NewCheckView(c *CheckReport) *CheckView {
	v := &CheckView{}
	if c.Error != nil || c.ProfileV == nil || c.Report == nil {
		m := c.Error
		if m == nil {
			x := engine.Msg("RX-UI-005", "")
			m = &x
		}
		v.Outcome = BLOCKED
		v.Blocked = &BlockedView{Titolo: T("b.titolo.fiducia"), Below: T("b.sotto.intatta"), Why: m.Testo,
			CheFare: m.Remediation, Codice: m.Codice, Dettagli: m.Detail}
		return v
	}
	prof, rap, dom := c.ProfileV, c.Report, c.Questions
	v.Header = Header(prof, rap)
	distro := distroName(prof)

	// blocked: no possible desktop (the distribution out, too old, excluded)
	possible := 0
	for _, e := range rap.Desktop {
		if e.Lvl != engine.NOT_SUPPORTED {
			possible++
		}
	}
	// what is missing (DECISIONI §10.36): REMOTIX does not install it, it says so; the administrator provides it.
	// The card that does not encode (RX-GPU-*) leaves no possible desktops, but it too is «missing».
	missing := append([]engine.Message{}, rap.Missing...)
	if possible == 0 {
		g := cardReason(rap)
		if g == nil || rap.Lowest != "" {
			v.Outcome = BLOCKED
			v.Blocked = viewNotSupported(prof, rap)
			return v
		}
		missing = append(missing, *g)
	}

	var lines []Line
	// system
	plat := strings.TrimSpace(distro + " " + prof.V("distro.version"))
	if strings.HasPrefix(rap.Recognized, strings.SplitN(engine.T("comp.nella_matrice", ""), " (", 2)[0]) {
		lines = append(lines, Line{T("r.sistema"), T("t.sistema.ok", plat), OK})
	} else {
		lines = append(lines, Line{T("r.sistema"), T("t.sistema.fuori", plat), DOPO})
	}
	// desktop
	var ds []string
	for _, e := range rap.Desktop {
		if installed(e) && (e.Lvl != engine.NOT_SUPPORTED || possible == 0) {
			ds = append(ds, DesktopName(e.Desktop))
		}
	}
	conditions := []string{}
	if len(ds) > 0 {
		lines = append(lines, Line{T("r.desktop"), T("t.desktop.ok", strings.Join(ds, ", ")), OK})
	}
	// card
	switch {
	case prof.V("gpu.nvidia_proprietary") == "yes":
		lines = append(lines, Line{T("r.scheda"), T("t.scheda.nvidia"), DOPO})
	case cardName(prof) == "":
		lines = append(lines, Line{T("r.scheda"), T("t.scheda.nessuna"), DOPO})
	default:
		lines = append(lines, Line{T("r.scheda"), T("t.scheda.ok", cardName(prof)), OK})
	}
	// video: the real test is after installation (7a)
	lines = append(lines, Line{T("r.video"), T("t.video.ok"), DOPO})
	// sign-in
	if m := hasMessage(prof.Messages, "RX-PAM-001"); m != nil {
		lines = append(lines, Line{T("r.accesso"), T("t.accesso.male"), MALE})
	} else {
		lines = append(lines, Line{T("r.accesso"), T("t.accesso.ok"), OK})
	}
	switch n := len(dom.People); {
	case n == 1:
		lines = append(lines, Line{T("r.persone"), T("t.persone.una"), OK})
	case n > 1:
		lines = append(lines, Line{T("r.persone"), T("t.persone", n), OK})
	}
	// protection
	switch {
	case prof.V("selinux") == "enforcing" || prof.V("selinux") == "permissive":
		lines = append(lines, Line{T("r.protezione"), T("t.prot.selinux"), OK})
	case prof.V("apparmor") != "" && prof.V("apparmor") != "absent" && prof.V("apparmor") != "no":
		lines = append(lines, Line{T("r.protezione"), T("t.prot.apparmor"), OK})
	default:
		lines = append(lines, Line{T("r.protezione"), T("t.prot.no"), OK})
	}
	// firewall: opening it is the administrator's job (§10.36)
	if dom.Firewall == "none" {
		lines = append(lines, Line{T("r.firewall"), T("t.fw.nessuno"), OK})
	} else {
		lines = append(lines, Line{T("r.firewall"), T("t.fw.admin", dom.Firewall, dom.Porta), WARNING})
		conditions = append(conditions, T("c.cond.firewall", dom.Porta))
	}
	// port
	p := dom.Porta
	if prof.V(fmt.Sprintf("port.%d.tcp_free", p)) == "no" || prof.V(fmt.Sprintf("port.%d.udp_free", p)) == "no" {
		lines = append(lines, Line{T("r.porta"), T("t.porta.occupata", p), WARNING})
		conditions = append(conditions, T("c.cond.porta", p))
	} else {
		lines = append(lines, Line{T("r.porta"), T("t.porta.libera", p), OK})
	}
	// permissions
	switch n := len(dom.NoCard); {
	case n == 0:
		lines = append(lines, Line{T("r.permessi"), T("t.permessi.ok"), OK})
	case n == 1:
		lines = append(lines, Line{T("r.permessi"), T("t.permessi.uno"), FIX})
	default:
		lines = append(lines, Line{T("r.permessi"), T("t.permessi.n", n), FIX})
	}
	lines = append(lines, Line{T("r.audio"), T("t.audio"), DOPO})
	v.Righe = lines
	v.Dettagli = checkDetails(prof, rap, c.Trust)

	if len(missing) > 0 {
		for _, m := range missing {
			v.Righe = withMissing(v.Righe, m)
			v.Codes = append(v.Codes, m.Codice)
		}
		v.Outcome = BLOCKED
		v.Banner, v.Below = T("c.manca.titolo"), T("c.manca.testo")
		v.Blocked = MissingView(missing)
		return v
	}

	switch len(conditions) {
	case 0:
		v.Outcome, v.Banner, v.Below = READY, T("c.ok.titolo"), ""
	case 1:
		v.Outcome, v.Banner, v.Below = CONDS, T("c.cond1.titolo"), conditions[0]
	default:
		v.Outcome, v.Banner, v.Below = CONDS, T("c.condN.titolo", len(conditions)), strings.Join(conditions, " ")
	}
	return v
}

// cardReason: the RX-GPU-* reason that leaves no possible desktops (the distribution works, the
// card or the driver that encodes is missing).
func cardReason(rap *engine.Report) *engine.Message {
	for _, e := range rap.Desktop {
		for i := range e.Reasons {
			if strings.HasPrefix(e.Reasons[i].Codice, "RX-GPU-") {
				return &e.Reasons[i]
			}
		}
	}
	for i := range rap.Messages {
		if strings.HasPrefix(rap.Messages[i].Codice, "RX-GPU-") && rap.Messages[i].Severity == engine.BLOCKING {
			return &rap.Messages[i]
		}
	}
	return nil
}

// labelForMissing: in which line of the check what is missing goes.
func labelForMissing(code string) string {
	switch {
	case strings.HasPrefix(code, "RX-GPU-"):
		return T("r.scheda")
	case code == "RX-MANCA-001":
		return T("r.desktop")
	case code == "RX-MANCA-002":
		return T("r.archivio")
	case code == "RX-MANCA-003":
		return T("r.pezzi")
	}
	return T("r.pacchetto")
}

// withMissing: the line of what is missing takes the place of the line with the same label (the
// «OK» card becomes «missing»), or is added after the desktop.
func withMissing(lines []Line, m engine.Message) []Line {
	et := labelForMissing(m.Codice)
	t := T("m." + m.Codice)
	if strings.HasPrefix(t, "⟨") {
		t = strings.TrimPrefix(m.Testo, "Missing: ")
	}
	if m.Detail != "" {
		t += ": " + m.Detail
	}
	r := Line{et, t, MISSING}
	for i := range lines {
		if lines[i].Etichetta == et {
			if lines[i].State == MISSING { // two missing items in the same line: one after the other
				return append(lines[:i+1], append([]Line{{"", t, MISSING}}, lines[i+1:]...)...)
			}
			lines[i] = r
			return lines
		}
	}
	pos := 1
	if pos > len(lines) {
		pos = len(lines)
	}
	return append(lines[:pos], append([]Line{r}, lines[pos:]...)...)
}

func checkDetails(prof *engine.ProfileV, rap *engine.Report, fid *engine.Trust) string {
	var d []string
	d = append(d, prof.V("distro.name"), rap.Recognized)
	for _, e := range rap.Desktop {
		if installed(e) {
			d = append(d, e.Desktop+" "+e.Installed+" "+e.Lvl)
		}
	}
	for _, n := range strings.Fields(prof.V("gpu.nodes")) {
		d = append(d, n+" "+prof.V("gpu."+n+".vendor")+" "+prof.V("gpu."+n+".driver"))
	}
	for _, k := range []string{"encoding.routes", "h264.gpu", "h264.driver_family", "encoding.vulkan", "pam.base", "selinux", "apparmor", "firewall.type", "firewall.zone"} {
		if x := prof.V(k); x != "" {
			d = append(d, k+"="+x)
		}
	}
	seen_items := map[string]bool{}
	for _, m := range append(append([]engine.Message{}, prof.Messages...), rap.Messages...) {
		if !seen_items[m.Codice] {
			seen_items[m.Codice] = true
			d = append(d, m.Codice)
		}
	}
	for _, e := range rap.Desktop {
		if installed(e) {
			for _, k := range e.Condizioni {
				if !seen_items[k.Codice] {
					seen_items[k.Codice] = true
					d = append(d, k.Codice)
				}
			}
		}
	}
	if fid != nil {
		d = append(d, fmt.Sprintf("catalog %s", rap.Catalog.Ver), "engine "+engine.EngineVersion)
	}
	var r []string
	for _, x := range d {
		if strings.TrimSpace(x) != "" {
			r = append(r, x)
		}
	}
	return strings.Join(r, " · ")
}

func viewNotSupported(prof *engine.ProfileV, rap *engine.Report) *BlockedView {
	distro := distroName(prof)
	b := &BlockedView{Below: T("b.sotto.intatta")}
	var reason *engine.Message
	for _, e := range rap.Desktop {
		if len(e.Reasons) > 0 {
			reason = &e.Reasons[0]
			break
		}
	}
	if reason == nil {
		for i := range rap.Messages {
			if rap.Messages[i].Severity == engine.BLOCKING {
				reason = &rap.Messages[i]
				break
			}
		}
	}
	if rap.Lowest != "" {
		// an excluded version of a distribution that REMOTIX supports in a newer version
		b.Titolo = T("b.titolo.versione", distro)
		b.Why = T("b.vecchia", strings.TrimSpace(distro+" "+prof.V("distro.version")))
		b.Needs = T("b.serve", rap.Lowest)
	} else {
		b.Titolo = T("b.titolo.distro")
		if reason != nil {
			b.Why = reason.Testo
			if strings.HasPrefix(reason.Codice, "RX-GPU-") {
				// phase 19: the distribution works, the card that encodes the video is missing
				b.Titolo = T("b.titolo.scheda")
			}
		}
	}
	if reason != nil {
		b.Codice = reason.Codice
		b.Dettagli = strings.TrimSpace(reason.Detail + " " + reason.Remediation)
		if reason.Remediation != "" {
			b.CheFare = reason.Remediation + " " + T("b.rilancia")
		}
	}
	if rap.Lowest != "" {
		b.CheFare = T("b.aggiorna", rap.Lowest) + " " + T("b.versioni")
	}
	if b.CheFare == "" {
		b.CheFare = T("b.versioni")
	}
	b.Dettagli = strings.TrimSpace(rap.PlatformV + " · " + rap.Recognized + " · " + b.Dettagli)
	return b
}

// MissingView: the «something is missing» screen — what, without saying how to provide it (§10.36).
func MissingView(m []engine.Message) *BlockedView {
	b := &BlockedView{Titolo: T("b.titolo.manca"), Below: T("b.sotto.intatta"), CheFare: T("b.manca.chefare")}
	var r, cod []string
	for _, x := range m {
		r = append(r, strings.TrimSpace(x.Testo+" "+x.Detail))
		cod = append(cod, x.Codice)
	}
	b.Why = "• " + strings.Join(r, "\n• ")
	b.Codice = strings.Join(cod, " ")
	return b
}

// ---- 2 · the choices -------------------------------------------------------------------------

// NewChoicesView: screen 2 — a single question, the port (§10.36: no repositories, firewalls or
// desktops to choose).
func NewChoicesView(c *CheckReport) *ChoicesView {
	dom := c.Questions
	v := &ChoicesView{Titolo: T("sc.titolo.1"), Below: T("sc.sotto")}
	if dom.Firewall == "none" {
		v.PortLine, v.PortGreen = T("sc.fw.nessuno"), true
	} else {
		v.PortLine = T("sc.fw.admin", dom.Firewall)
	}
	return v
}

func nr(n int) string {
	en := []string{"", "One", "Two", "Three", "Four", "Five", "Six"}
	if n >= len(en) {
		return fmt.Sprint(n)
	}
	return en[n]
}

// ValidPort: the number written in the box.
func ValidPort(s string) (int, bool) {
	p, err := strconv.Atoi(strings.TrimSpace(s))
	return p, err == nil && p >= 1 && p <= 65535
}

// ---- 3 · the plan ----------------------------------------------------------------------------

func worst(a State, r engine.Reversibility) State {
	var b State
	switch r {
	case engine.EXACT:
		b = OK
	case engine.IRREVERSIBLE:
		b = MALE
	default:
		b = CONSENT
	}
	if b == MALE || a == MALE {
		return MALE
	}
	if b == CONSENT || a == CONSENT {
		return CONSENT
	}
	return OK
}

func listing(names []string) string {
	if len(names) <= 1 {
		return strings.Join(names, "")
	}
	return strings.Join(names[:len(names)-1], ", ") + T("a.e") + names[len(names)-1]
}

// VistaDelPiano: the plan's actions gathered in steps told in plain words. The order is the
// plan's (the first step of each group decides where the group goes).
func VistaDelPiano(p *engine.Piano) *VistaPiano {
	v := &VistaPiano{}
	group := map[string]int{}
	var usersGroups []string
	seen_items := map[string]bool{}
	put := func(key string, create func() Stride, a engine.PlanAction) {
		i, ok := group[key]
		if !ok {
			v.Steps = append(v.Steps, create())
			i = len(v.Steps) - 1
			group[key] = i
			v.Steps[i].Rev = OK
		}
		v.Steps[i].Azioni = append(v.Steps[i].Azioni, a.ID)
		v.Steps[i].Rev = worst(v.Steps[i].Rev, a.Reversibility)
	}
	port := ""
	for _, a := range p.Azioni {
		switch {
		case a.Type == "install-packages":
			put("packages", func() Stride {
				return Stride{Type: "packages", Titolo: T("a.pacchetti"), Below: T("a.pacchetti.t"), Fatto: T("a.pacchetti.f"), Breve: T("a.pacchetti.b")}
			}, a)
		case a.Type == "add-user-to-group":
			if u := a.Parameters["user"]; !seen_items[u] {
				seen_items[u] = true
				usersGroups = append(usersGroups, u)
			}
			if g := a.Parameters["group"]; !seen_items["group:"+g] {
				seen_items["group:"+g] = true
				v.Gruppi = append(v.Gruppi, g)
			}
			put("gruppi", func() Stride { return Stride{Type: "groups"} }, a)
		case a.Type == "start-service":
			port = a.Parameters["port"]
			put(a.ID, func() Stride {
				return Stride{Type: "service", Titolo: T("a.servizio", port), Below: T("a.servizio.t"), Fatto: T("a.servizio.f", port), Breve: T("a.servizio.b")}
			}, a)
		default:
			put(a.ID, func() Stride {
				d := a.Description
				if d != "" {
					d = strings.ToUpper(d[:1]) + d[1:]
				}
				return Stride{Type: "other", Titolo: d, Fatto: d, Breve: d}
			}, a)
		}
	}
	if i, ok := group["gruppi"]; ok {
		chi := listing(usersGroups)
		f := T("a.gruppi.f", chi)
		if len(usersGroups) > 1 {
			f = T("a.gruppi.fn", chi)
		}
		v.Steps[i].Titolo, v.Steps[i].Below, v.Steps[i].Fatto = T("a.gruppi", chi), T("a.gruppi.t"), f
		v.Steps[i].Breve = T("a.gruppi.b", chi, strings.Join(v.Gruppi, ", "))
	}
	v.Utenti, v.Porta = usersGroups, port
	// the details: every engine action with its type, its undo and the fingerprint
	var d []string
	for _, a := range p.Azioni {
		d = append(d, a.ID+" ("+a.Type+", "+string(a.Reversibility)+")")
	}
	d = append(d, "plan "+p.ID, "fingerprint "+short(p.Fingerprint.Digest), "digest "+short(p.Digest()))
	for _, m := range p.NotDone {
		d = append(d, strings.TrimSpace(m.Codice+" "+m.Testo))
	}
	v.Dettagli = strings.Join(d, " · ")
	v.Pacchetti = p.Pacchetti
	v.Dipendenze = map[string]string{}
	for _, d := range p.Dipendenze {
		v.Dipendenze[d.Nome] = d.Why
	}
	return v
}

func short(s string) string {
	if len(s) > 16 {
		return s[:16] + "…"
	}
	return s
}

// ---- 4 · the progress ------------------------------------------------------------------------

// LineState of the progress.
type LineState int

const (
	WAIT LineState = iota
	IN_PROGRESS
	DONE
	FAILED
	ROLLED_BACK
)

// LineAv: a line of the progress.
type LineAv struct {
	Testo string
	State LineState
}

// Progress: the state of screen 4, updated by the engine's events (§6.6.1).
type Progress struct {
	Righe    []LineAv
	steps    []Stride
	action   map[string]int // action id → step index
	done     map[string]bool
	State    engine.State
	Log      []string
	Rollback bool // undoing in progress
}

// NewProgress: the lines from the plan's steps, plus the trust, the plan and the verification.
func NewProgress(vp *VistaPiano) *Progress {
	a := &Progress{steps: vp.Steps, action: map[string]int{}, done: map[string]bool{}}
	a.Righe = append(a.Righe, LineAv{Testo: T("av.fiducia")}, LineAv{Testo: T("av.piano")})
	for i, p := range vp.Steps {
		a.Righe = append(a.Righe, LineAv{Testo: p.Breve})
		for _, id := range p.Azioni {
			a.action[id] = i
		}
	}
	a.Righe = append(a.Righe, LineAv{Testo: T("av.verifica")})
	return a
}

// Event: an engine event.
func (a *Progress) Event(ev engine.PublicEvent) {
	line := ev.Event
	switch ev.Event {
	case "state":
		line = "→ " + string(ev.A)
		if ev.Detail != "" {
			line += " — " + ev.Detail
		}
		a.State = ev.A
		switch ev.A {
		case engine.NEW:
			a.Righe[0].State = IN_PROGRESS
		case engine.TRUSTED:
			a.Righe[0].State = DONE
			a.Righe[1].State = IN_PROGRESS
		case engine.PLANNED:
			a.Righe[1].State = DONE
		case engine.RUNNING:
			if len(a.Righe) > 3 && a.Righe[2].State == WAIT {
				a.Righe[2].State = IN_PROGRESS
			}
		case engine.VERIFYING:
			a.Righe[len(a.Righe)-1].State = IN_PROGRESS
		case engine.VERIFIED, engine.CONFIRMED, engine.CONFIRMED_WITH_CONDITIONS:
			a.Righe[len(a.Righe)-1].State = DONE
		case engine.ROLLING_BACK:
			a.Rollback = true
			for i := range a.Righe {
				if a.Righe[i].State == IN_PROGRESS {
					a.Righe[i].State = FAILED
				}
			}
		case engine.BLOCKED, engine.REFUSED:
			for i := range a.Righe {
				if a.Righe[i].State == IN_PROGRESS {
					a.Righe[i].State = FAILED
				}
			}
		}
	case "action":
		line = "   " + ev.Action + ": " + ev.Phase
		if ev.Detail != "" {
			line += " (" + truncate(ev.Detail, 160) + ")"
		}
		i, ok := a.action[ev.Action]
		if !ok {
			break
		}
		r := &a.Righe[i+2]
		switch ev.Phase {
		case "INTENT", "RESUMED":
			if !a.Rollback {
				r.State = IN_PROGRESS
			}
		case "DONE":
			a.done[ev.Action] = true
			all_of := true
			for _, id := range a.steps[i].Azioni {
				all_of = all_of && a.done[id]
			}
			if all_of {
				r.State = DONE
				// the next step starts now (its INTENTION arrives when downloading is over)
				if n := i + 3; n < len(a.Righe)-1 && a.Righe[n].State == WAIT && !a.Rollback {
					a.Righe[n].State = IN_PROGRESS
				}
			}
		case "FAILED":
			r.State = FAILED
		default: // ROLLED_BACK, and the rollback phases
			if a.Rollback {
				r.State = ROLLED_BACK
			}
		}
	case "message":
		if ev.Message != nil {
			line = "   [" + ev.Message.Codice + "] " + ev.Message.Testo
		}
	case "object":
		line = "   " + ev.Obj + ": " + ev.RoutePath
	}
	a.Log = append(a.Log, line)
}

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

// Punto: the step in progress («Step 4 of 7 · installing REMOTIX») and the percentage.
func (a *Progress) Spot() (string, int) {
	tot := len(a.Righe)
	done := 0
	cur := -1
	for i, r := range a.Righe {
		if r.State == DONE || r.State == ROLLED_BACK {
			done++
		}
		if r.State == IN_PROGRESS && cur < 0 {
			cur = i
		}
	}
	pc := done * 100 / tot
	if a.Rollback {
		return T("av.annullamento"), pc
	}
	n := len(a.steps)
	switch {
	case cur < 0 && done == tot:
		return T("av.fine"), 100
	case cur < 2:
		return T("av.inizio"), pc
	case cur >= 2+n:
		return T("av.verifica"), pc
	}
	t := a.steps[cur-2].Breve
	return T("av.passo", cur-1, n, t), pc
}

// ---- 5 · ready, and the other endings --------------------------------------------------------

// ReadyView: screen 5.
type ReadyView struct {
	Below       string
	Router      string // D6: the port to forward on the router, TCP and UDP
	Address     string
	Fingerprint string
	Cambiato    []string
	Prove       []Line
	Dettagli    string
	Condizioni  []string
	// DaFare: what is left to the administrator (the port the firewall closes, or that is unknown)
	DaFare []string
}

// NewReadyView: from the certificate, from the plan (the steps done) and from the outcome.
func NewReadyView(es *Outcome, vp *VistaPiano, port int) *ReadyView {
	v := &ReadyView{Below: T("pr.sotto")}
	addr := "[indirizzo]"
	if len(es.Addresses) > 0 {
		addr = es.Addresses[0]
	}
	v.Address = fmt.Sprintf("https://%s:%d/", addr, port)
	v.Router = T("pr.router", port, addr)
	v.Fingerprint = es.FingerprintTLS
	for _, p := range vp.Steps {
		v.Cambiato = append(v.Cambiato, p.Fatto)
	}
	c := es.Certificate
	if c != nil {
		steps, stepsOK := 0, 0
		stepsId := map[string]bool{}
		for _, p := range vp.Steps {
			for _, id := range p.Azioni {
				stepsId[id] = true
			}
		}
		outcome := func(e string) (string, State) {
			switch e {
			case "PASS":
				return T("pr.riuscita"), OK
			case "FAIL":
				return T("pr.fallita"), MALE
			}
			return T("pr.nonsi"), UNKNOWN
		}
		var others []Line
		for _, k := range c.Verifications {
			if k.Outcome == "N.A." {
				continue
			}
			t, s := outcome(k.Outcome)
			switch {
			case k.ID == "service":
				v.Prove = append(v.Prove, Line{T("pr.k.servizio"), t, s})
			case k.ID == "h264-encoding":
				v.Prove = append(v.Prove, Line{T("pr.k.h264"), t, s})
			case k.ID == "pam-resolved":
				v.Prove = append(v.Prove, Line{T("pr.k.pam"), t, s})
			case k.ID == "firewall-port":
				others = append(others, Line{T("pr.k.porta"), t, s})
				dove := k.Detail
				if i := strings.Index(dove, ":"); i > 0 {
					dove = dove[:i]
				}
				switch k.Outcome {
				case "FAIL":
					v.DaFare = append(v.DaFare, T("pr.todo.chiusa", port, dove))
				case "PASS":
				default:
					v.DaFare = append(v.DaFare, T("pr.todo.ignota", port, dove))
				}
			case stepsId[k.ID]:
				steps++
				if k.Outcome == "PASS" {
					stepsOK++
				}
			}
		}
		v.Prove = append(v.Prove, others...)
		if steps > 0 {
			s := OK
			t := T("pr.riuscita")
			if stepsOK < steps {
				s, t = MALE, T("pr.fallita")
			}
			v.Prove = append(v.Prove, Line{T("pr.k.steps", stepsOK, steps), t, s})
		}
		for _, k := range c.Condizioni {
			if k.Codice == "C-AMMINISTRATORE" { // the port: it goes in DaFare, stated in full
				continue
			}
			v.Condizioni = append(v.Condizioni, CommonCondition(k.Codice))
		}
		v.Dettagli = strings.Join([]string{es.Folder + "/certificate.json", "catalog " + c.Catalog.Ver,
			"engine " + c.Engine.Ver, string(c.State)}, " · ")
		for _, k := range c.Condizioni {
			v.Dettagli += " · " + k.Codice + ": " + k.Testo
		}
	}
	v.Prove = append(v.Prove, Line{T("pr.k.audio"), T("pr.primo"), DOPO})
	if len(v.Condizioni) > 0 {
		v.Below = T("pr.sotto.cond", v.Condizioni[0])
	}
	return v
}

// CommonCondition: a condition of the certificate in plain words (the engine's text, technical,
// is in the details).
func CommonCondition(code string) string {
	if _, ok := texts["cond."+code]; ok {
		return T("cond." + code)
	}
	return T("cond.altra")
}

// NewEndView: the endings that are not «ready» (BLOCKED, REFUSED, ROLLED_BACK…).
func NewEndView(es *Outcome, log []string) *BlockedView {
	b := &BlockedView{}
	var m *engine.Message
	if es.Error != nil {
		m = es.Error
	}
	// the most serious message among those seen in the log, if the outcome has none
	switch es.State {
	case engine.ROLLED_BACK:
		b.Titolo, b.Below, b.Toccata = T("b.titolo.annullata"), T("b.sotto.annullata"), true
	case engine.PARTIALLY_ROLLED_BACK:
		b.Titolo, b.Below, b.Toccata = T("b.titolo.parte"), T("b.sotto.parte"), true
	case engine.INTERRUPTED:
		b.Titolo, b.Below, b.Toccata = T("b.titolo.interrotta"), T("b.sotto.interrotta"), true
	case engine.BLOCKED, engine.REFUSED, "":
		b.Titolo, b.Below = T("b.titolo.fermo"), T("b.sotto.intatta")
	default:
		b.Titolo, b.Below = T("b.titolo.interrotta"), T("b.sotto.interrotta")
	}
	if m == nil && es.Certificate != nil && len(es.Certificate.Remainders) > 0 {
		b.Why = strings.Join(es.Certificate.Remainders, "; ")
	}
	if m != nil {
		if strings.HasPrefix(m.Codice, "RX-MANCA-") {
			b.Titolo = T("b.titolo.manca")
		}
		b.Why, b.CheFare, b.Codice = m.Testo, m.Remediation, m.Codice
		b.Dettagli = m.Detail
	}
	if es.Folder != "" {
		b.Dettagli = strings.TrimSpace(b.Dettagli + " · " + es.Folder + " · " + string(es.State))
	}
	return b
}

// BlockInPlan: what is missing, already in the plan (the manager's simulation that does not resolve, for
// example), to state at once instead of asking to confirm a plan the engine will refuse.
func BlockInPlan(p *engine.Piano) *engine.Message {
	for i := range p.NotDone {
		if p.NotDone[i].Severity == engine.BLOCKING {
			return &p.NotDone[i]
		}
	}
	return nil
}

// LastMessage: the most recent BLOCKING message among the events (to say why).
func LastMessage(evs []engine.PublicEvent) *engine.Message {
	for i := len(evs) - 1; i >= 0; i-- {
		if m := evs[i].Message; m != nil && m.Severity == engine.BLOCKING {
			return m
		}
	}
	return nil
}

// Sorted: the keys of a map, in order (to always write the entries the same way).
func Sorted(m map[string]string) []string {
	var k []string
	for x := range m {
		k = append(k, x)
	}
	sort.Strings(k)
	return k
}
