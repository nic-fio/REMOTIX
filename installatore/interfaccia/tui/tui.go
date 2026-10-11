// Package tui: the installer's screens in the terminal (Bubble Tea), for whoever works over ssh or
// from the console (fasi/17 §6.6.1), from the interface views (Vista…), on the engine's session;
// it runs as root in the terminal. The design is the mockup approved by the user on 10 Oct 2026
// (grafica/tui-mockup/index.html): a fixed frame as wide as the terminal (at least 80 columns),
// four steps Check › Plan › Install › Ready, the content scrolling inside the frame, the keys
// at the bottom. A single question, the port, and the «yes» to the plan (DECISIONI §10.36).
package tui

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/x/ansi"

	"remotix/installatore/interfaccia"
	"remotix/installatore/motore"
)

const (
	sWait = iota
	sCheck
	sPiano
	sProgress
	sReady
	sFine
)

// The steps of the top line.
const (
	pCheck = iota
	pPlan
	pInstall
	pReady
)

const (
	minWidth  = 80
	minHeight = 12
	labelCol  = 18 // the column of the check's labels
	stateCol  = 12 // the column of the state labels
)

// theme: the mockup's colours. lipgloss brings them down by itself to 256 or 16 colours depending on the terminal, and to
// none with NO_COLOR (termenv.EnvColorProfile).
type theme struct {
	blue, green, amber, red, gray, border, strong, field lipgloss.Style
}

func newTheme(r *lipgloss.Renderer) theme {
	c := func(hex string) lipgloss.Style { return r.NewStyle().Foreground(lipgloss.Color(hex)) }
	return theme{
		blue:   c("#5A9BFF").Bold(true),
		green:  c("#3EC27E").Bold(true),
		amber:  c("#E3A82F").Bold(true),
		red:    c("#F0625A").Bold(true),
		gray:   c("#7D889C"),
		border: c("#3A4457"),
		strong: r.NewStyle().Bold(true),
		field:  r.NewStyle().Reverse(true),
	}
}

type (
	msgCheck struct {
		c   *interfaccia.CheckReport
		err error
	}
	msgPiano struct {
		p   *engine.Piano
		err error
	}
	msgEvent   struct{ ev engine.PublicEvent }
	msgOutcome struct {
		es  *interfaccia.Outcome
		err error
	}
)

type model struct {
	rsn        interfaccia.Engine
	prog       *tea.Program
	t          theme
	screen     int
	step       int  // the step of the top line
	has_failed bool // the step stopped (red ✗)
	wait       string
	ctrl       *interfaccia.CheckReport
	vc         *interfaccia.CheckView
	vp         *interfaccia.VistaPiano
	piano      *engine.Piano
	av         *interfaccia.Progress
	events     []engine.PublicEvent
	ready      *interfaccia.ReadyView
	fine       *interfaccia.BlockedView
	port       string
	modPort    bool   // the port is being typed
	old        string // the previous port, for esc
	details    bool
	reg        bool
	stopping   bool
	note       string
	wid        int
	h          int
	scroll     int
	outcome    *interfaccia.Outcome
}

// Avvia: the TUI on the engine's session, starting from the port given with --port (the check
// examines that one; tab still changes it in the plan). The exit code follows the CLI's (0 if
// the installation is CONFIRMED).
func Launch(rsn interfaccia.Engine, port int) (int, error) {
	m := newModel(rsn, lipgloss.DefaultRenderer())
	m.initial(port)
	p := tea.NewProgram(m, tea.WithAltScreen())
	m.prog = p
	if _, err := p.Run(); err != nil {
		return 1, err
	}
	if m.outcome != nil {
		fmt.Printf("%s\n  %s\n", engine.T("cli.operazione", m.outcome.Operation, m.outcome.State), m.outcome.Folder)
		if m.outcome.State == engine.CONFIRMED || m.outcome.State == engine.CONFIRMED_WITH_CONDITIONS {
			return 0, nil
		}
	}
	return 1, nil
}

func newModel(rsn interfaccia.Engine, r *lipgloss.Renderer) *model {
	return &model{rsn: rsn, t: newTheme(r), screen: sWait, step: pCheck,
		wait: interfaccia.T("attendi.controllo"), port: "7447", wid: minWidth, h: 24}
}

// initial: the starting port (--port); 0 or out of range keeps 7447.
func (m *model) initial(port int) {
	if port > 0 && port <= 65535 {
		m.port = strconv.Itoa(port)
	}
}

func (m *model) Init() tea.Cmd {
	port, _ := strconv.Atoi(m.port)
	return func() tea.Msg {
		c, err := m.rsn.Check(port)
		return msgCheck{c, err}
	}
}

func message(err error) *engine.Message {
	if e, ok := err.(*engine.ErrorRX); ok {
		return &e.M
	}
	x := engine.Msg("RX-UI-005", err.Error())
	return &x
}

func (m *model) navigate(screen int) {
	m.screen, m.scroll = screen, 0
}

func (m *model) finish(es *interfaccia.Outcome) {
	m.outcome = es
	if es.State == engine.CONFIRMED || es.State == engine.CONFIRMED_WITH_CONDITIONS {
		port, _ := strconv.Atoi(m.port)
		m.ready = interfaccia.NewReadyView(es, m.vp, port)
		m.step = pReady
		m.navigate(sReady)
		return
	}
	if es.Error == nil {
		es.Error = interfaccia.LastMessage(m.events)
	}
	m.fine, m.has_failed = interfaccia.NewEndView(es, nil), true
	m.navigate(sFine)
}

// askPlan: the plan for the typed port (the engine re-examines the machine if it changes).
func (m *model) askPlan() tea.Cmd {
	entries := map[string]string{"port": m.port}
	m.step, m.wait = pPlan, interfaccia.T("attendi.piano")
	m.navigate(sWait)
	return func() tea.Msg {
		p, err := m.rsn.Piano(entries)
		return msgPiano{p, err}
	}
}

func (m *model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch x := msg.(type) {
	case tea.WindowSizeMsg:
		m.wid, m.h = x.Width, x.Height
	case msgCheck:
		if x.err != nil {
			m.finish(&interfaccia.Outcome{Error: message(x.err)})
			return m, nil
		}
		m.ctrl = x.c
		m.vc = interfaccia.NewCheckView(x.c)
		if x.c.Questions != nil {
			m.port = strconv.Itoa(x.c.Questions.Porta)
		}
		if m.vc.Outcome == interfaccia.BLOCKED && len(m.vc.Righe) == 0 {
			m.fine, m.has_failed = m.vc.Blocked, true
			m.navigate(sFine)
			return m, nil
		}
		m.has_failed = m.vc.Outcome == interfaccia.BLOCKED
		m.navigate(sCheck)
	case msgPiano:
		if x.err != nil {
			m.finish(&interfaccia.Outcome{Error: message(x.err)})
			return m, nil
		}
		if b := interfaccia.BlockInPlan(x.p); b != nil {
			m.finish(&interfaccia.Outcome{Error: b})
			return m, nil
		}
		m.piano = x.p
		m.vp = interfaccia.VistaDelPiano(x.p)
		m.navigate(sPiano)
	case msgEvent:
		m.events = append(m.events, x.ev)
		m.av.Event(x.ev)
	case msgOutcome:
		if x.err != nil {
			m.finish(&interfaccia.Outcome{Error: message(x.err)})
			return m, nil
		}
		m.finish(x.es)
	case tea.KeyMsg:
		return m.keystroke(x)
	}
	return m, nil
}

func (m *model) keystroke(k tea.KeyMsg) (tea.Model, tea.Cmd) {
	s := k.String()
	if s == "ctrl+c" {
		if m.screen == sProgress {
			return m, nil // while it works one cannot quit: it is stopped with «a», which puts things back as they were
		}
		return m, tea.Quit
	}
	if m.modPort {
		return m.portKey(s)
	}
	switch s {
	case "up", "k":
		m.scroll--
		return m, nil
	case "down", "j":
		m.scroll++
		return m, nil
	case "pgup":
		m.scroll -= m.bodyHeight() - 1
		return m, nil
	case "pgdown", " ":
		m.scroll += m.bodyHeight() - 1
		return m, nil
	case "home":
		m.scroll = 0
		return m, nil
	case "end":
		m.scroll = 1 << 20
		return m, nil
	case "d":
		m.details = !m.details
		return m, nil
	case "r":
		if m.screen == sProgress || m.screen == sReady || m.screen == sFine {
			m.reg = !m.reg
			return m, nil
		}
	}
	switch m.screen {
	case sWait:
		if s == "q" {
			return m, tea.Quit
		}
	case sCheck:
		switch s {
		case "q":
			return m, tea.Quit
		case "enter":
			if m.vc.Outcome != interfaccia.BLOCKED {
				return m, m.askPlan()
			}
		}
	case sPiano:
		switch s {
		case "y", "Y":
			m.av = interfaccia.NewProgress(m.vp)
			m.step = pInstall
			m.navigate(sProgress)
			digest := m.piano.Digest()
			return m, func() tea.Msg {
				es, err := m.rsn.Apply(digest, func(ev engine.PublicEvent) { m.prog.Send(msgEvent{ev}) })
				return msgOutcome{es, err}
			}
		case "n", "N", "q":
			return m, tea.Quit // nothing has been touched
		case "tab":
			m.modPort, m.old = true, m.port
		}
	case sProgress:
		if s == "a" && !m.stopping {
			m.stopping = true
			go m.rsn.Stop()
		}
	case sReady, sFine:
		switch s {
		case "enter", "q":
			return m, tea.Quit
		case "s":
			if m.screen == sFine {
				m.save("remotix-report.json", map[string]any{"end": m.fine, "check": m.ctrl, "events": m.events})
			}
		}
	}
	return m, nil
}

// portKey: the port box, in the plan.
func (m *model) portKey(s string) (tea.Model, tea.Cmd) {
	switch s {
	case "esc":
		m.modPort, m.port = false, m.old
	case "backspace":
		if len(m.port) > 0 {
			m.port = m.port[:len(m.port)-1]
		}
	case "enter", "tab":
		p, ok := interfaccia.ValidPort(m.port)
		if !ok {
			return m, nil
		}
		m.modPort, m.port = false, strconv.Itoa(p)
		if m.port != m.old {
			return m, m.askPlan()
		}
	default:
		if len(s) == 1 && s[0] >= '0' && s[0] <= '9' && len(m.port) < 5 {
			m.port += s
		}
	}
	return m, nil
}

func (m *model) save(name string, v any) {
	dir := "."
	if h, err := os.UserHomeDir(); err == nil {
		dir = h
	}
	p := filepath.Join(dir, name)
	b, _ := json.MarshalIndent(v, "", "  ")
	if err := os.WriteFile(p, b, 0o600); err != nil {
		m.note = err.Error()
		return
	}
	m.note = interfaccia.T("salvato", p)
}

// ---- the frame -------------------------------------------------------------------------------

func (m *model) internal() int { return m.wid - 4 } // «│ » and « │»

func (m *model) bodyHeight() int { return m.h - 6 } // head, steps, two separators, keys, bottom

// fill: a line exactly n columns long (cut with «…» if longer).
func fill(s string, n int) string {
	w := ansi.StringWidth(s)
	if w > n {
		s = ansi.Truncate(s, n, "…")
		w = ansi.StringWidth(s)
	}
	return s + strings.Repeat(" ", n-w)
}

func (m *model) View() string {
	if m.wid < minWidth {
		return fill(interfaccia.T("tui.stretto", minWidth), m.wid)
	}
	if m.h < minHeight {
		return fill(interfaccia.T("tui.basso", minHeight), m.wid)
	}
	body, keys := m.content()
	return m.border(body, keys)
}

func (m *model) border(body []string, keys string) string {
	t, w, in := m.t, m.wid, m.internal()
	edge := t.border.Render
	var r []string
	// the head: «╭─ REMOTIX 1.0 · Installation ───── Debian 13 · GNOME 48 ─╮»
	sx := t.blue.Render("REMOTIX") + t.strong.Render(" "+engine.EngineVersion+" · "+interfaccia.T("intestazione"))
	dx := ""
	if m.vc != nil {
		dx = m.vc.Header
	}
	rest := w - 6 - ansi.StringWidth(sx) // «╭─ » sx « » … «─╮»
	if dx != "" {
		dx = ansi.Truncate(dx, rest-4, "…")
		rest -= ansi.StringWidth(dx) + 2
		r = append(r, edge("╭─ ")+sx+edge(" "+strings.Repeat("─", rest)+" ")+t.gray.Render(dx)+edge(" ─╮"))
	} else {
		r = append(r, edge("╭─ ")+sx+edge(" "+strings.Repeat("─", rest+1)+"╮"))
	}
	line := func(s string) string { return edge("│") + " " + fill(s, in) + " " + edge("│") }
	sep := edge("├" + strings.Repeat("─", w-2) + "┤")
	r = append(r, line(m.steps()), sep)
	// the body, which scrolls
	h := m.bodyHeight()
	maximum := len(body) - h
	if maximum < 0 {
		maximum = 0
	}
	if m.scroll > maximum {
		m.scroll = maximum
	}
	if m.scroll < 0 {
		m.scroll = 0
	}
	for i := 0; i < h; i++ {
		s := ""
		if j := m.scroll + i; j < len(body) {
			s = body[j]
		}
		r = append(r, line(s))
	}
	// the keys, and on the right where we are if the body is longer than the screen
	if maximum > 0 {
		pos := t.gray.Render(fmt.Sprintf("↑↓ %d–%d / %d", m.scroll+1, m.scroll+h, len(body)))
		space := in - ansi.StringWidth(pos) - 1
		keys = fill(keys, space) + " " + pos
	}
	r = append(r, sep, line(keys), edge("╰"+strings.Repeat("─", w-2)+"╯"))
	return strings.Join(r, "\n")
}

func (m *model) steps() string {
	t := m.t
	names := []string{interfaccia.T("passo.1"), interfaccia.T("passo.2"), interfaccia.T("passo.3"), interfaccia.T("passo.4")}
	var ps []string
	for i, n := range names {
		switch {
		case i < m.step:
			ps = append(ps, t.green.Render("✓ "+n))
		case i == m.step && m.has_failed:
			ps = append(ps, t.red.Render("✗ "+n))
		case i == m.step && m.screen == sReady:
			ps = append(ps, t.green.Render("✓ "+n))
		case i == m.step:
			ps = append(ps, t.blue.Render("● "+n))
		default:
			ps = append(ps, t.gray.Render("○ "+n))
		}
	}
	return strings.Join(ps, t.gray.Render("  ›  "))
}

// keys: «enter continue · d details · q quit», the key in bold and the rest grey.
func (m *model) keys(pairs ...string) string {
	var r []string
	for i := 0; i+1 < len(pairs); i += 2 {
		r = append(r, m.t.strong.Render(pairs[i])+m.t.gray.Render(" "+pairs[i+1]))
	}
	return strings.Join(r, m.t.gray.Render(" · "))
}

// ---- the body lines --------------------------------------------------------------------------

// par: a text wrapped inside the frame, indented, all in one style.
func (m *model) par(text string, st lipgloss.Style, reentry int) []string {
	if text == "" {
		return nil
	}
	w := m.internal() - reentry
	var r []string
	for _, l := range strings.Split(ansi.Wrap(text, w, ""), "\n") {
		r = append(r, strings.Repeat(" ", reentry)+st.Render(l))
	}
	return r
}

// columns: label, text (wrapped in its column) and state label on the right.
func (m *model) columns(et, text, cart string, st lipgloss.Style) []string {
	tw := m.internal() - labelCol - stateCol - 1
	ls := strings.Split(ansi.Wrap(text, tw, ""), "\n")
	var r []string
	for i, l := range ls {
		e, c := "", ""
		if i == 0 {
			e, c = et, st.Render(cart)
		}
		r = append(r, fill(e, labelCol)+fill(l, tw)+" "+c)
	}
	return r
}

func (m *model) styleState(s interfaccia.State) lipgloss.Style {
	switch s {
	case interfaccia.OK:
		return m.t.green
	case interfaccia.WARNING, interfaccia.CONSENT:
		return m.t.amber
	case interfaccia.FIX:
		return m.t.blue
	case interfaccia.MALE, interfaccia.MISSING:
		return m.t.red
	}
	return m.t.gray
}

// content: the body of the current screen and the keys line.
func (m *model) content() ([]string, string) {
	T := interfaccia.T
	c := []string{""}
	var keys string
	switch m.screen {
	case sWait:
		c = append(c, m.par(m.wait, m.t.strong, 0)...)
		keys = m.keys("q", T("k.esci"))
	case sCheck:
		c = append(c, m.bodyCheck()...)
		if m.vc.Outcome == interfaccia.BLOCKED {
			keys = m.keys("q", T("k.esci"), "d", T("k.dettagli"))
		} else {
			keys = m.keys("enter", T("k.avanti"), "d", T("k.dettagli"), "q", T("k.esci"))
		}
	case sPiano:
		c = append(c, m.bodyPlan()...)
		if m.modPort {
			keys = m.keys("enter", T("k.porta.ok"), "esc", T("k.porta.no"))
		} else {
			keys = m.t.strong.Render(T("k.procedi")) + " " + m.t.green.Render("y") + m.t.gray.Render(" "+T("k.si")+" · ") +
				m.t.red.Render("n") + m.t.gray.Render(" "+T("k.no")+" · ") + m.keys("tab", T("k.porta"), "d", T("k.dettagli"))
		}
	case sProgress:
		c = append(c, m.bodyProgress()...)
		if m.stopping {
			keys = m.t.amber.Render(T("btn.fermando"))
		} else {
			keys = m.keys("a", T("k.ferma"), "r", T("k.registro"))
		}
	case sReady:
		c = append(c, m.bodyReady()...)
		keys = m.keys("enter", T("k.chiudi"), "r", T("k.registro"), "d", T("k.dettagli"))
	case sFine:
		c = append(c, m.bodyEnd()...)
		keys = m.keys("enter", T("k.chiudi"), "s", T("k.salva"), "d", T("k.dettagli"))
	}
	if m.note != "" {
		c = append(c, "")
		c = append(c, m.par(m.note, m.t.gray, 0)...)
	}
	return append(c, ""), keys
}

func (m *model) bodyCheck() []string {
	T := interfaccia.T
	v := m.vc
	var c []string
	for _, r := range v.Righe {
		c = append(c, m.columns(r.Etichetta, r.Testo, r.State.Tag(), m.styleState(r.State))...)
	}
	c = append(c, "")
	if v.Outcome == interfaccia.BLOCKED {
		c = append(c, m.par(v.Banner, m.t.red, 0)...)
		c = append(c, m.par(v.Below, lipgloss.NewStyle(), 0)...)
		c = append(c, m.par(strings.Join(v.Codes, " "), m.t.gray, 0)...)
	} else {
		c = append(c, m.par(v.Banner, m.t.strong, 0)...)
		c = append(c, m.par(v.Below, m.t.gray, 0)...)
	}
	if m.details {
		c = append(c, "", m.t.strong.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, m.t.gray, 2)...)
	}
	return c
}

func (m *model) bodyPlan() []string {
	T := interfaccia.T
	t, v := m.t, m.vp
	var c []string
	// the port, the only choice
	field := "[ " + m.port + " ]"
	if m.modPort {
		field = "[ " + m.port + "▏]"
	}
	c = append(c, t.strong.Render(fill(T("p.porta"), 10))+t.field.Render(field)+t.gray.Render("   "+T("p.porta.t")))
	if _, ok := interfaccia.ValidPort(m.port); !ok {
		c = append(c, t.red.Render(T("sc.porta.errata")))
	}
	// the exact packages, from the manager's simulation: REMOTIX (from the .run), then its dependencies
	// (from the distribution's repositories; labwc, wlr-randr and the font with the desktop requiring them)
	newcomers, updated, present := 0, 0, 0
	var our, dip []string
	for _, a := range v.Pacchetti {
		note := a.Origine
		if a.Origine == "file" {
			note = ""
		}
		if why, ok := v.Dipendenze[a.Nome]; ok {
			note = T("p.per", why)
		}
		var r string
		switch a.Outcome {
		case "new":
			newcomers++
			r = "  " + t.green.Render("+") + " " + fill(a.Nome, 22) + fill(a.Ver, 18) + t.gray.Render(note)
		case "upgraded":
			updated++
			r = "  " + t.blue.Render("↑") + " " + fill(a.Nome, 22) + fill(a.Ver, 18) + t.gray.Render(T("p.da.prima", a.Before))
		default:
			present++
			continue
		}
		if a.Origine == "file" {
			our = append(our, r)
		} else {
			dip = append(dip, r)
		}
	}
	if len(our) > 0 {
		c = append(c, "", t.strong.Render("REMOTIX")+t.gray.Render("   "+T("p.da.run")))
		c = append(c, our...)
	}
	if len(dip) > 0 {
		c = append(c, "", t.strong.Render(T("p.dipendenze"))+t.gray.Render("   "+T("p.dipendenze.t")))
		c = append(c, dip...)
	}
	if len(v.Pacchetti) > 0 {
		c = append(c, t.gray.Render("    "+T("p.totale", newcomers, updated, present)))
	}
	// the people in the card's groups, the service, the other steps
	var others []string
	irreversible := []string{}
	for _, p := range v.Steps {
		if p.Rev == interfaccia.MALE {
			irreversible = append(irreversible, p.Titolo)
		}
		switch p.Type {
		case "groups":
			g := T("p.gruppi", strings.Join(v.Gruppi, ", "))
			if len(v.Gruppi) > 1 {
				g = T("p.gruppi.n", strings.Join(v.Gruppi, ", "))
			}
			c = append(c, "", t.strong.Render(g)+"   "+strings.Join(v.Utenti, ", "))
		case "service":
			c = append(c, "", t.strong.Render(T("p.servizio"))+"   "+T("p.servizio.t"))
		case "other":
			others = append(others, p.Titolo)
		}
	}
	if len(others) > 0 {
		c = append(c, "", t.strong.Render(T("p.altro")))
		for _, a := range others {
			c = append(c, m.par("· "+a, lipgloss.NewStyle(), 2)...)
		}
	}
	c = append(c, "")
	if len(irreversible) == 0 {
		c = append(c, t.gray.Render(T("p.annulla"))+t.blue.Render("remotix-install uninstall")+t.gray.Render("."))
	} else {
		c = append(c, m.par(T("p.annulla.non", strings.Join(irreversible, "; ")), t.amber, 0)...)
	}
	if m.details {
		c = append(c, "", t.strong.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, t.gray, 2)...)
	}
	return c
}

func (m *model) bodyProgress() []string {
	T := interfaccia.T
	t := m.t
	spot, pc := m.av.Spot()
	in := m.internal()
	path := fmt.Sprintf("%d %%", pc)
	c := []string{fill(t.strong.Render(spot), in-ansi.StringWidth(path)) + path}
	pieni := in * pc / 100
	c = append(c, t.blue.Render(strings.Repeat("█", pieni))+t.gray.Render(strings.Repeat("░", in-pieni)), "")
	for _, r := range m.av.Righe {
		switch r.State {
		case interfaccia.DONE:
			c = append(c, "  "+t.green.Render("✓")+" "+r.Testo)
		case interfaccia.IN_PROGRESS:
			c = append(c, "  "+t.blue.Render("◐ "+r.Testo))
		case interfaccia.FAILED:
			c = append(c, "  "+t.red.Render("✗ "+r.Testo))
		case interfaccia.ROLLED_BACK:
			c = append(c, "  "+t.gray.Render("↺ "+r.Testo))
		default:
			c = append(c, "  "+t.gray.Render("○ "+r.Testo))
		}
	}
	if m.reg {
		c = append(c, "", t.strong.Render(T("h.registro")))
		for _, l := range last(m.av.Log, 200) {
			c = append(c, m.par(l, t.gray, 2)...)
		}
	}
	return c
}

func last(r []string, n int) []string {
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return r
}

func (m *model) bodyReady() []string {
	T := interfaccia.T
	t, v := m.t, m.ready
	c := []string{t.green.Render("✓ " + T("pr.titolo")), ""}
	c = append(c, t.strong.Render(T("h.apri")), "  "+t.blue.Render(v.Address))
	if v.Fingerprint != "" {
		c = append(c, m.par(T("pr.impronta", v.Fingerprint), t.gray, 2)...)
	}
	c = append(c, m.par(T("pr.apri.t"), t.gray, 2)...)
	c = append(c, "", t.strong.Render(T("h.dafare")))
	for _, d := range v.DaFare {
		c = append(c, m.pointWarning(d)...)
	}
	for _, d := range v.Condizioni {
		c = append(c, m.pointWarning(d)...)
	}
	c = append(c, m.par(v.Router, t.gray, 4)...)
	c = append(c, "", t.strong.Render(T("h.chi")))
	c = append(c, m.par(T("pr.chi.t"), lipgloss.NewStyle(), 2)...)
	c = append(c, "", t.strong.Render(T("h.prove")))
	for _, p := range v.Prove {
		c = append(c, "  "+fill(p.Etichetta, 36)+m.styleState(p.State).Render(p.Testo))
	}
	if m.details {
		c = append(c, "", t.strong.Render(T("h.cambiato")))
		for _, x := range v.Cambiato {
			c = append(c, m.par("· "+x, lipgloss.NewStyle(), 2)...)
		}
		c = append(c, "", t.strong.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, t.gray, 2)...)
	}
	if m.reg && m.av != nil {
		c = append(c, "", t.strong.Render(T("h.registro")))
		for _, l := range last(m.av.Log, 200) {
			c = append(c, m.par(l, t.gray, 2)...)
		}
	}
	return c
}

// pointWarning: «  ! text» in amber, wrapped under the text.
func (m *model) pointWarning(s string) []string {
	r := m.par(s, lipgloss.NewStyle(), 4)
	if len(r) > 0 {
		r[0] = "  " + m.t.amber.Render("!") + " " + strings.TrimPrefix(r[0], "    ")
	}
	return r
}

func (m *model) bodyEnd() []string {
	T := interfaccia.T
	t, v := m.t, m.fine
	st := t.red
	if v.Touched {
		st = t.amber
	}
	c := m.par("✗ "+v.Title, st, 0)
	c = append(c, m.par(v.Below, t.gray, 0)...)
	if v.Why != "" {
		c = append(c, "", t.strong.Render(T("h.perche")))
		for _, l := range strings.Split(v.Why, "\n") {
			c = append(c, m.par(l, lipgloss.NewStyle(), 2)...)
		}
		if x := strings.TrimSpace(v.Needs + "  " + v.Code); x != "" {
			c = append(c, m.par(x, t.gray, 2)...)
		}
	}
	if v.WhatToDo != "" {
		c = append(c, "", t.strong.Render(T("h.chefare")))
		c = append(c, m.par(v.WhatToDo, lipgloss.NewStyle(), 2)...)
	}
	if m.details && v.Details != "" {
		c = append(c, "", t.strong.Render(T("h.dettagli")))
		c = append(c, m.par(v.Details, t.gray, 2)...)
	}
	if m.reg && m.av != nil {
		c = append(c, "", t.strong.Render(T("h.registro")))
		for _, l := range last(m.av.Log, 200) {
			c = append(c, m.par(l, t.gray, 2)...)
		}
	}
	return c
}
