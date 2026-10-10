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
	AFTER
	MALE
	UNKNOWN
	WARNING // does not stop: it is stated (the running firewall, the port in use)
	MISSING // stops: REMOTIX does not provide it, it says so (§10.36)
)

// Tag: the label text of a state, in the right-hand column of the check.
func (s State) Tag() string {
	return [...]string{T("s.ok"), T("s.consenso"), T("s.sistemo"), T("s.after"), T("s.male"), T("s.nonsi"),
		T("s.warning"), T("s.missing")}[s]
}

// Line: a line of the check or of the tests.
type Line struct {
	Label, Text string
	State       State
}

// Outcome of the check.
type CheckOutcome int

const (
	READY CheckOutcome = iota
	CONDITIONS
	BLOCKED
)

// CheckView: screen 1. With Outcome == BLOCKED and Lines filled it is «something is missing»: the lines
// with the MISSING label, and the codes; with Lines empty it is an ending (Blocked: distribution out…).
type CheckView struct {
	Header        string // «Fedora Linux 44 · Workstation · GNOME 50»
	Outcome       CheckOutcome
	Banner, Below string
	Lines         []Line
	Codes         []string // the RX codes of what is missing
	Details       string
	Blocked       *BlockedView // if Outcome == BLOCKED
}

// BlockedView: a screen that ends (not supported, stopped, cancelled).
type BlockedView struct {
	Title, Below  string
	Why, WhatToDo string
	Needs         string // «At least Debian 13 is needed.»
	Code          string
	Details       string
	Touched       bool // the machine was touched (cancelled): the circle is not red but amber
}

// ChoicesView: screen 2 — the port.
type ChoicesView struct {
	Title, Below string
	PortLine     string // the line under the port (green if there is no running firewall)
	PortGreen    bool
}

// Step: a line of the plan, with the engine actions it gathers.
type Step struct {
	Kind               string // "packages" · "groups" · "service" · "other"
	Title, Note, Below string
	Done               string // how the welcome says it
	Rev                State  // OK = fully undone · CONSENT = partly · MALE = not undone
	Actions            []string
	Brief              string // how the progress says it
}

// Tag of the reversibility.
func (p Step) Tag() string {
	switch p.Rev {
	case OK:
		return T("rev.overall")
	case MALE:
		return T("rev.no")
	}
	return T("rev.part")
}

// VistaPiano: screen 3.
type VistaPiano struct {
	Steps   []Step
	Details string
	// Packets: what the manager will do (its simulation), to show before the «yes»
	Packets []motore.Artifact
	// Users and Groups: whom the engine enrolls in the card's groups, and in which
	Users, Groups []string
	// Port: the service's, as the plan says it
	Port string
	// Dependencies: for the packages the desktop requires of REMOTIX, for which desktop
	Dependencies map[string]string
}

// ---- 1 · the check ---------------------------------------------------------------------------

func distroName(prof *motore.Profile) string {
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

func installed(e motore.DesktopOutcome) bool {
	return e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown"
}

// Header: the line at the top right.
func Header(prof *motore.Profile, rap *motore.Report) string {
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

func conditionOf(rap *motore.Report, code_v string) bool {
	for _, e := range rap.Desktop {
		if e.Level == motore.NOT_SUPPORTED || !installed(e) {
			continue
		}
		for _, k := range e.Conditions {
			if k.Code == code_v {
				return true
			}
		}
	}
	return false
}

func hasMessage(ms []motore.Message, code_v string) *motore.Message {
	for i := range ms {
		if ms[i].Code == code_v {
			return &ms[i]
		}
	}
	return nil
}

// cardName: the card in plain words (driver and bus are in the technical details).
func cardName(prof *motore.Profile) string {
	nodes := strings.Fields(prof.V("gpu.nodes"))
	if len(nodes) == 0 {
		return ""
	}
	f := strings.ToLower(prof.V("gpu." + nodes[0] + ".vendor"))
	switch {
	case strings.Contains(f, "intel"):
		return T("t.gpu_card.mark", "Intel")
	case strings.Contains(f, "amd") || strings.Contains(f, "ati"):
		return T("t.gpu_card.mark", "AMD")
	case strings.Contains(f, "nvidia"):
		return T("t.gpu_card.mark", "NVIDIA")
	case strings.Contains(f, "virtio") || strings.Contains(f, "qxl") || strings.Contains(f, "vmware") || strings.Contains(f, "bochs"):
		return T("t.gpu_card.virtuale")
	}
	return T("t.gpu_card.generica")
}

// Check: screen 1 from the engine's objects.
func NewCheckView(c *Check) *CheckView {
	v := &CheckView{}
	if c.Error != nil || c.Profile == nil || c.Report == nil {
		m := c.Error
		if m == nil {
			x := motore.Msg("RX-UI-005", "")
			m = &x
		}
		v.Outcome = BLOCKED
		v.Blocked = &BlockedView{Title: T("b.heading.attestation"), Below: T("b.below.intatta"), Why: m.Text,
			WhatToDo: m.Remediation, Code: m.Code, Details: m.Detail}
		return v
	}
	prof, rap, dom := c.Profile, c.Report, c.Questions
	v.Header = Header(prof, rap)
	distro := distroName(prof)

	// blocked: no possible desktop (the distribution out, too old, excluded)
	possible := 0
	for _, e := range rap.Desktop {
		if e.Level != motore.NOT_SUPPORTED {
			possible++
		}
	}
	// what is missing (DECISIONI §10.36): REMOTIX does not install it, it says so; the administrator provides it.
	// The card that does not encode (RX-GPU-*) leaves no possible desktops, but it too is «missing».
	missing := append([]motore.Message{}, rap.Missing...)
	if possible == 0 {
		g := cardReason(rap)
		if g == nil || rap.Lowest != "" {
			v.Outcome = BLOCKED
			v.Blocked = viewNotSupported(prof, rap)
			return v
		}
		missing = append(missing, *g)
	}

	var line_list []Line
	// system
	plat := strings.TrimSpace(distro + " " + prof.V("distro.version"))
	if strings.HasPrefix(rap.Recognized, strings.SplitN(motore.T("comp.nella_matrice", ""), " (", 2)[0]) {
		line_list = append(line_list, Line{T("r.system_wide"), T("t.system_wide.ok", plat), OK})
	} else {
		line_list = append(line_list, Line{T("r.system_wide"), T("t.system_wide.outside", plat), AFTER})
	}
	// desktop
	var ds []string
	for _, e := range rap.Desktop {
		if installed(e) && (e.Level != motore.NOT_SUPPORTED || possible == 0) {
			ds = append(ds, DesktopName(e.Desktop))
		}
	}
	conditions := []string{}
	if len(ds) > 0 {
		line_list = append(line_list, Line{T("r.desktop"), T("t.desktop.ok", strings.Join(ds, ", ")), OK})
	}
	// card
	switch {
	case prof.V("gpu.nvidia_proprietary") == "yes":
		line_list = append(line_list, Line{T("r.gpu_card"), T("t.gpu_card.nvidia"), AFTER})
	case cardName(prof) == "":
		line_list = append(line_list, Line{T("r.gpu_card"), T("t.gpu_card.nessuna"), AFTER})
	default:
		line_list = append(line_list, Line{T("r.gpu_card"), T("t.gpu_card.ok", cardName(prof)), OK})
	}
	// video: the real test is after installation (7a)
	line_list = append(line_list, Line{T("r.video"), T("t.video.ok"), AFTER})
	// sign-in
	if m := hasMessage(prof.Messages, "RX-PAM-001"); m != nil {
		line_list = append(line_list, Line{T("r.access"), T("t.access.male"), MALE})
	} else {
		line_list = append(line_list, Line{T("r.access"), T("t.access.ok"), OK})
	}
	switch n := len(dom.People); {
	case n == 1:
		line_list = append(line_list, Line{T("r.people"), T("t.people.una"), OK})
	case n > 1:
		line_list = append(line_list, Line{T("r.people"), T("t.people", n), OK})
	}
	// protection
	switch {
	case prof.V("selinux") == "enforcing" || prof.V("selinux") == "permissive":
		line_list = append(line_list, Line{T("r.protezione"), T("t.prot.selinux"), OK})
	case prof.V("apparmor") != "" && prof.V("apparmor") != "absent" && prof.V("apparmor") != "no":
		line_list = append(line_list, Line{T("r.protezione"), T("t.prot.apparmor"), OK})
	default:
		line_list = append(line_list, Line{T("r.protezione"), T("t.prot.no"), OK})
	}
	// firewall: opening it is the administrator's job (§10.36)
	if dom.Firewall == "none" {
		line_list = append(line_list, Line{T("r.firewall"), T("t.fw.nobody"), OK})
	} else {
		line_list = append(line_list, Line{T("r.firewall"), T("t.fw.admin", dom.Firewall, dom.Port), WARNING})
		conditions = append(conditions, T("c.cond.firewall", dom.Port))
	}
	// port
	p := dom.Port
	if prof.V(fmt.Sprintf("port.%d.tcp_free", p)) == "no" || prof.V(fmt.Sprintf("port.%d.udp_free", p)) == "no" {
		line_list = append(line_list, Line{T("r.port"), T("t.port.busy", p), WARNING})
		conditions = append(conditions, T("c.cond.port", p))
	} else {
		line_list = append(line_list, Line{T("r.port"), T("t.port.free_fn", p), OK})
	}
	// permissions
	switch n := len(dom.NoCard); {
	case n == 0:
		line_list = append(line_list, Line{T("r.permessi"), T("t.permessi.ok"), OK})
	case n == 1:
		line_list = append(line_list, Line{T("r.permessi"), T("t.permessi.uno"), FIX})
	default:
		line_list = append(line_list, Line{T("r.permessi"), T("t.permessi.n", n), FIX})
	}
	line_list = append(line_list, Line{T("r.audio"), T("t.audio"), AFTER})
	v.Lines = line_list
	v.Details = checkDetails(prof, rap, c.Attestation)

	if len(missing) > 0 {
		for _, m := range missing {
			v.Lines = withMissing(v.Lines, m)
			v.Codes = append(v.Codes, m.Code)
		}
		v.Outcome = BLOCKED
		v.Banner, v.Below = T("c.missing.heading"), T("c.missing.body_text")
		v.Blocked = MissingView(missing)
		return v
	}

	switch len(conditions) {
	case 0:
		v.Outcome, v.Banner, v.Below = READY, T("c.ok.heading"), ""
	case 1:
		v.Outcome, v.Banner, v.Below = CONDITIONS, T("c.cond1.heading"), conditions[0]
	default:
		v.Outcome, v.Banner, v.Below = CONDITIONS, T("c.condN.heading", len(conditions)), strings.Join(conditions, " ")
	}
	return v
}

// cardReason: the RX-GPU-* reason that leaves no possible desktops (the distribution works, the
// card or the driver that encodes is missing).
func cardReason(rap *motore.Report) *motore.Message {
	for _, e := range rap.Desktop {
		for i := range e.Reasons {
			if strings.HasPrefix(e.Reasons[i].Code, "RX-GPU-") {
				return &e.Reasons[i]
			}
		}
	}
	for i := range rap.Messages {
		if strings.HasPrefix(rap.Messages[i].Code, "RX-GPU-") && rap.Messages[i].Severity == motore.BLOCKING {
			return &rap.Messages[i]
		}
	}
	return nil
}

// labelForMissing: in which line of the check what is missing goes.
func labelForMissing(code_v string) string {
	switch {
	case strings.HasPrefix(code_v, "RX-GPU-"):
		return T("r.gpu_card")
	case code_v == "RX-MANCA-001":
		return T("r.desktop")
	case code_v == "RX-MANCA-002":
		return T("r.archive")
	case code_v == "RX-MANCA-003":
		return T("r.pieces")
	}
	return T("r.pack")
}

// withMissing: the line of what is missing takes the place of the line with the same label (the
// «OK» card becomes «missing»), or is added after the desktop.
func withMissing(line_list []Line, m motore.Message) []Line {
	et := labelForMissing(m.Code)
	t := T("m." + m.Code)
	if strings.HasPrefix(t, "⟨") {
		t = strings.TrimPrefix(m.Text, "Missing: ")
	}
	if m.Detail != "" {
		t += ": " + m.Detail
	}
	r := Line{et, t, MISSING}
	for i := range line_list {
		if line_list[i].Label == et {
			if line_list[i].State == MISSING { // two missing items in the same line: one after the other
				return append(line_list[:i+1], append([]Line{{"", t, MISSING}}, line_list[i+1:]...)...)
			}
			line_list[i] = r
			return line_list
		}
	}
	pos := 1
	if pos > len(line_list) {
		pos = len(line_list)
	}
	return append(line_list[:pos], append([]Line{r}, line_list[pos:]...)...)
}

func checkDetails(prof *motore.Profile, rap *motore.Report, fid *motore.Attestation) string {
	var d []string
	d = append(d, prof.V("distro.name"), rap.Recognized)
	for _, e := range rap.Desktop {
		if installed(e) {
			d = append(d, e.Desktop+" "+e.Installed+" "+e.Level)
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
	for _, m := range append(append([]motore.Message{}, prof.Messages...), rap.Messages...) {
		if !seen_items[m.Code] {
			seen_items[m.Code] = true
			d = append(d, m.Code)
		}
	}
	for _, e := range rap.Desktop {
		if installed(e) {
			for _, k := range e.Conditions {
				if !seen_items[k.Code] {
					seen_items[k.Code] = true
					d = append(d, k.Code)
				}
			}
		}
	}
	if fid != nil {
		d = append(d, fmt.Sprintf("catalog %s", rap.Catalog.Version), "engine "+motore.EngineVersion)
	}
	var r []string
	for _, x := range d {
		if strings.TrimSpace(x) != "" {
			r = append(r, x)
		}
	}
	return strings.Join(r, " · ")
}

func viewNotSupported(prof *motore.Profile, rap *motore.Report) *BlockedView {
	distro := distroName(prof)
	b := &BlockedView{Below: T("b.below.intatta")}
	var motivo *motore.Message
	for _, e := range rap.Desktop {
		if len(e.Reasons) > 0 {
			motivo = &e.Reasons[0]
			break
		}
	}
	if motivo == nil {
		for i := range rap.Messages {
			if rap.Messages[i].Severity == motore.BLOCKING {
				motivo = &rap.Messages[i]
				break
			}
		}
	}
	if rap.Lowest != "" {
		// an excluded version of a distribution that REMOTIX supports in a newer version
		b.Title = T("b.heading.version_v", distro)
		b.Why = T("b.old", strings.TrimSpace(distro+" "+prof.V("distro.version")))
		b.Needs = T("b.needs", rap.Lowest)
	} else {
		b.Title = T("b.heading.distro")
		if motivo != nil {
			b.Why = motivo.Text
			if strings.HasPrefix(motivo.Code, "RX-GPU-") {
				// phase 19: the distribution works, the card that encodes the video is missing
				b.Title = T("b.heading.gpu_card")
			}
		}
	}
	if motivo != nil {
		b.Code = motivo.Code
		b.Details = strings.TrimSpace(motivo.Detail + " " + motivo.Remediation)
		if motivo.Remediation != "" {
			b.WhatToDo = motivo.Remediation + " " + T("b.rilancia")
		}
	}
	if rap.Lowest != "" {
		b.WhatToDo = T("b.do_update", rap.Lowest) + " " + T("b.vers")
	}
	if b.WhatToDo == "" {
		b.WhatToDo = T("b.vers")
	}
	b.Details = strings.TrimSpace(rap.Platform + " · " + rap.Recognized + " · " + b.Details)
	return b
}

// MissingView: the «something is missing» screen — what, without saying how to provide it (§10.36).
func MissingView(m []motore.Message) *BlockedView {
	b := &BlockedView{Title: T("b.heading.missing"), Below: T("b.below.intatta"), WhatToDo: T("b.missing.chefare")}
	var r, cod []string
	for _, x := range m {
		r = append(r, strings.TrimSpace(x.Text+" "+x.Detail))
		cod = append(cod, x.Code)
	}
	b.Why = "• " + strings.Join(r, "\n• ")
	b.Code = strings.Join(cod, " ")
	return b
}

// ---- 2 · the choices -------------------------------------------------------------------------

// NewChoicesView: screen 2 — a single question, the port (§10.36: no repositories, firewalls or
// desktops to choose).
func NewChoicesView(c *Check) *ChoicesView {
	dom := c.Questions
	v := &ChoicesView{Title: T("sc.heading.1"), Below: T("sc.below")}
	if dom.Firewall == "none" {
		v.PortLine, v.PortGreen = T("sc.fw.nobody"), true
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

func worst(a State, r motore.Reversibility) State {
	var b State
	switch r {
	case motore.EXACT:
		b = OK
	case motore.IRREVERSIBLE:
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
func VistaDelPiano(p *motore.Piano) *VistaPiano {
	v := &VistaPiano{}
	grp := map[string]int{}
	var usersGroups []string
	seen_items := map[string]bool{}
	put := func(key_id string, create func() Step, a motore.PlanAction) {
		i, ok := grp[key_id]
		if !ok {
			v.Steps = append(v.Steps, create())
			i = len(v.Steps) - 1
			grp[key_id] = i
			v.Steps[i].Rev = OK
		}
		v.Steps[i].Actions = append(v.Steps[i].Actions, a.ID)
		v.Steps[i].Rev = worst(v.Steps[i].Rev, a.Reversibility)
	}
	port := ""
	for _, a := range p.Actions {
		switch {
		case a.Kind == "install-packages":
			put("packages", func() Step {
				return Step{Kind: "packages", Title: T("a.packets"), Below: T("a.packets.t"), Done: T("a.packets.f"), Brief: T("a.packets.b")}
			}, a)
		case a.Kind == "add-user-to-group":
			if u := a.Parameters["user"]; !seen_items[u] {
				seen_items[u] = true
				usersGroups = append(usersGroups, u)
			}
			if g := a.Parameters["group"]; !seen_items["group:"+g] {
				seen_items["group:"+g] = true
				v.Groups = append(v.Groups, g)
			}
			put("group_list", func() Step { return Step{Kind: "groups"} }, a)
		case a.Kind == "start-service":
			port = a.Parameters["port"]
			put(a.ID, func() Step {
				return Step{Kind: "service", Title: T("a.service", port), Below: T("a.service.t"), Done: T("a.service.f", port), Brief: T("a.service.b")}
			}, a)
		default:
			put(a.ID, func() Step {
				d := a.Description
				if d != "" {
					d = strings.ToUpper(d[:1]) + d[1:]
				}
				return Step{Kind: "other", Title: d, Done: d, Brief: d}
			}, a)
		}
	}
	if i, ok := grp["group_list"]; ok {
		chi := listing(usersGroups)
		f := T("a.group_list.f", chi)
		if len(usersGroups) > 1 {
			f = T("a.group_list.fn", chi)
		}
		v.Steps[i].Title, v.Steps[i].Below, v.Steps[i].Done = T("a.group_list", chi), T("a.group_list.t"), f
		v.Steps[i].Brief = T("a.group_list.b", chi, strings.Join(v.Groups, ", "))
	}
	v.Users, v.Port = usersGroups, port
	// the details: every engine action with its type, its undo and the fingerprint
	var d []string
	for _, a := range p.Actions {
		d = append(d, a.ID+" ("+a.Kind+", "+string(a.Reversibility)+")")
	}
	d = append(d, "plan "+p.ID, "fingerprint "+short(p.Fingerprint.Digest), "digest "+short(p.Digest()))
	for _, m := range p.NotDone {
		d = append(d, strings.TrimSpace(m.Code+" "+m.Text))
	}
	v.Details = strings.Join(d, " · ")
	v.Packets = p.Packets
	v.Dependencies = map[string]string{}
	for _, d := range p.Dependencies {
		v.Dependencies[d.Name] = d.Why
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

// StateLine of the progress.
type StateLine int

const (
	WAIT StateLine = iota
	IN_PROGRESS
	DONE
	FAILED
	ROLLED_BACK
)

// LineAv: a line of the progress.
type LineAv struct {
	Text  string
	State StateLine
}

// Progress: the state of screen 4, updated by the engine's events (§6.6.1).
type Progress struct {
	Lines    []LineAv
	steps    []Step
	action   map[string]int // action id → step index
	done     map[string]bool
	State    motore.State
	Log      []string
	Rollback bool // undoing in progress
}

// NewProgress: the lines from the plan's steps, plus the trust, the plan and the verification.
func NewProgress(vp *VistaPiano) *Progress {
	a := &Progress{steps: vp.Steps, action: map[string]int{}, done: map[string]bool{}}
	a.Lines = append(a.Lines, LineAv{Text: T("av.attestation")}, LineAv{Text: T("av.piano")})
	for i, p := range vp.Steps {
		a.Lines = append(a.Lines, LineAv{Text: p.Brief})
		for _, id := range p.Actions {
			a.action[id] = i
		}
	}
	a.Lines = append(a.Lines, LineAv{Text: T("av.verify")})
	return a
}

// Event: an engine event.
func (a *Progress) Event(ev motore.PublicEvent) {
	row := ev.Event
	switch ev.Event {
	case "state":
		row = "→ " + string(ev.A)
		if ev.Detail != "" {
			row += " — " + ev.Detail
		}
		a.State = ev.A
		switch ev.A {
		case motore.NEW:
			a.Lines[0].State = IN_PROGRESS
		case motore.TRUSTED:
			a.Lines[0].State = DONE
			a.Lines[1].State = IN_PROGRESS
		case motore.PLANNED:
			a.Lines[1].State = DONE
		case motore.RUNNING:
			if len(a.Lines) > 3 && a.Lines[2].State == WAIT {
				a.Lines[2].State = IN_PROGRESS
			}
		case motore.VERIFYING:
			a.Lines[len(a.Lines)-1].State = IN_PROGRESS
		case motore.VERIFIED, motore.CONFIRMED, motore.CONFIRMED_WITH_CONDITIONS:
			a.Lines[len(a.Lines)-1].State = DONE
		case motore.ROLLING_BACK:
			a.Rollback = true
			for i := range a.Lines {
				if a.Lines[i].State == IN_PROGRESS {
					a.Lines[i].State = FAILED
				}
			}
		case motore.BLOCKED, motore.RIFIUTATA:
			for i := range a.Lines {
				if a.Lines[i].State == IN_PROGRESS {
					a.Lines[i].State = FAILED
				}
			}
		}
	case "action":
		row = "   " + ev.Action + ": " + ev.Phase
		if ev.Detail != "" {
			row += " (" + truncate(ev.Detail, 160) + ")"
		}
		i, ok := a.action[ev.Action]
		if !ok {
			break
		}
		r := &a.Lines[i+2]
		switch ev.Phase {
		case "INTENT", "RESUMED":
			if !a.Rollback {
				r.State = IN_PROGRESS
			}
		case "DONE":
			a.done[ev.Action] = true
			all_of := true
			for _, id := range a.steps[i].Actions {
				all_of = all_of && a.done[id]
			}
			if all_of {
				r.State = DONE
				// the next step starts now (its INTENTION arrives when downloading is over)
				if n := i + 3; n < len(a.Lines)-1 && a.Lines[n].State == WAIT && !a.Rollback {
					a.Lines[n].State = IN_PROGRESS
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
			row = "   [" + ev.Message.Code + "] " + ev.Message.Text
		}
	case "object":
		row = "   " + ev.Object + ": " + ev.Path
	}
	a.Log = append(a.Log, row)
}

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

// Spot: the step in progress («Step 4 of 7 · installing REMOTIX») and the percentage.
func (a *Progress) Spot() (string, int) {
	tot := len(a.Lines)
	done := 0
	cur := -1
	for i, r := range a.Lines {
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
		return T("av.start"), pc
	case cur >= 2+n:
		return T("av.verify"), pc
	}
	t := a.steps[cur-2].Brief
	return T("av.step", cur-1, n, t), pc
}

// ---- 5 · ready, and the other endings --------------------------------------------------------

// ReadyView: screen 5.
type ReadyView struct {
	Below       string
	Router      string // D6: the port to forward on the router, TCP and UDP
	Address     string
	Fingerprint string
	Changed     []string
	Prove       []Line
	Details     string
	Conditions  []string
	// Todo: what is left to the administrator (the port the firewall closes, or that is unknown)
	Todo []string
}

// NewReadyView: from the certificate, from the plan (the steps done) and from the outcome.
func NewReadyView(es *Outcome, vp *VistaPiano, port int) *ReadyView {
	v := &ReadyView{Below: T("pr.below")}
	addr := "[address]"
	if len(es.Addresses) > 0 {
		addr = es.Addresses[0]
	}
	v.Address = fmt.Sprintf("https://%s:%d/", addr, port)
	v.Router = T("pr.router", port, addr)
	v.Fingerprint = es.FingerprintTLS
	for _, p := range vp.Steps {
		v.Changed = append(v.Changed, p.Done)
	}
	c := es.Certificate
	if c != nil {
		steps, stepsOK := 0, 0
		stepsId := map[string]bool{}
		for _, p := range vp.Steps {
			for _, id := range p.Actions {
				stepsId[id] = true
			}
		}
		outcome := func(e string) (string, State) {
			switch e {
			case "PASS":
				return T("pr.succeeded"), OK
			case "FAIL":
				return T("pr.failed"), MALE
			}
			return T("pr.nonsi"), UNKNOWN
		}
		var other_ones []Line
		for _, k := range c.Checks {
			if k.Outcome == "N.A." {
				continue
			}
			t, s := outcome(k.Outcome)
			switch {
			case k.ID == "service":
				v.Prove = append(v.Prove, Line{T("pr.k.service"), t, s})
			case k.ID == "h264-encoding":
				v.Prove = append(v.Prove, Line{T("pr.k.h264"), t, s})
			case k.ID == "pam-resolved":
				v.Prove = append(v.Prove, Line{T("pr.k.pam"), t, s})
			case k.ID == "firewall-port":
				other_ones = append(other_ones, Line{T("pr.k.port"), t, s})
				dove := k.Detail
				if i := strings.Index(dove, ":"); i > 0 {
					dove = dove[:i]
				}
				switch k.Outcome {
				case "FAIL":
					v.Todo = append(v.Todo, T("pr.todo.is_closed", port, dove))
				case "PASS":
				default:
					v.Todo = append(v.Todo, T("pr.todo.ignota", port, dove))
				}
			case stepsId[k.ID]:
				steps++
				if k.Outcome == "PASS" {
					stepsOK++
				}
			}
		}
		v.Prove = append(v.Prove, other_ones...)
		if steps > 0 {
			s := OK
			t := T("pr.succeeded")
			if stepsOK < steps {
				s, t = MALE, T("pr.failed")
			}
			v.Prove = append(v.Prove, Line{T("pr.k.steps", stepsOK, steps), t, s})
		}
		for _, k := range c.Conditions {
			if k.Code == "C-AMMINISTRATORE" { // the port: it goes in Todo, stated in full
				continue
			}
			v.Conditions = append(v.Conditions, CommonCondition(k.Code))
		}
		v.Details = strings.Join([]string{es.Folder + "/certificate.json", "catalog " + c.Catalog.Version,
			"engine " + c.Engine.Version, string(c.State)}, " · ")
		for _, k := range c.Conditions {
			v.Details += " · " + k.Code + ": " + k.Text
		}
	}
	v.Prove = append(v.Prove, Line{T("pr.k.audio"), T("pr.first"), AFTER})
	if len(v.Conditions) > 0 {
		v.Below = T("pr.below.cond", v.Conditions[0])
	}
	return v
}

// CommonCondition: a condition of the certificate in plain words (the engine's text, technical,
// is in the details).
func CommonCondition(code_v string) string {
	if _, ok := texts["cond."+code_v]; ok {
		return T("cond." + code_v)
	}
	return T("cond.the_other")
}

// NewEndView: the endings that are not «ready» (BLOCKED, RIFIUTATA, ROLLED_BACK…).
func NewEndView(es *Outcome, logbook []string) *BlockedView {
	b := &BlockedView{}
	var m *motore.Message
	if es.Error != nil {
		m = es.Error
	}
	// the most serious message among those seen in the log, if the outcome has none
	switch es.State {
	case motore.ROLLED_BACK:
		b.Title, b.Below, b.Touched = T("b.heading.annullata"), T("b.below.annullata"), true
	case motore.PARTIALLY_ROLLED_BACK:
		b.Title, b.Below, b.Touched = T("b.heading.part"), T("b.below.part"), true
	case motore.INTERRUPTED:
		b.Title, b.Below, b.Touched = T("b.heading.interrotta"), T("b.below.interrotta"), true
	case motore.BLOCKED, motore.RIFIUTATA, "":
		b.Title, b.Below = T("b.heading.stopped"), T("b.below.intatta")
	default:
		b.Title, b.Below = T("b.heading.interrotta"), T("b.below.interrotta")
	}
	if m == nil && es.Certificate != nil && len(es.Certificate.Remainders) > 0 {
		b.Why = strings.Join(es.Certificate.Remainders, "; ")
	}
	if m != nil {
		if strings.HasPrefix(m.Code, "RX-MANCA-") {
			b.Title = T("b.heading.missing")
		}
		b.Why, b.WhatToDo, b.Code = m.Text, m.Remediation, m.Code
		b.Details = m.Detail
	}
	if es.Folder != "" {
		b.Details = strings.TrimSpace(b.Details + " · " + es.Folder + " · " + string(es.State))
	}
	return b
}

// BlockInPlan: what is missing, already in the plan (the manager's simulation that does not resolve, for
// example), to state at once instead of asking to confirm a plan the engine will refuse.
func BlockInPlan(p *motore.Piano) *motore.Message {
	for i := range p.NotDone {
		if p.NotDone[i].Severity == motore.BLOCKING {
			return &p.NotDone[i]
		}
	}
	return nil
}

// LastMessage: the most recent BLOCKING message among the events (to say why).
func LastMessage(evs []motore.PublicEvent) *motore.Message {
	for i := len(evs) - 1; i >= 0; i-- {
		if m := evs[i].Message; m != nil && m.Severity == motore.BLOCKING {
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
