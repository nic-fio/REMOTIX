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
	sAttesa = iota
	sControllo
	sPiano
	sAvanzamento
	sPronto
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
	larghezzaMinima = 80
	altezzaMinima   = 12
	colEtichetta    = 18 // the column of the check's labels
	colStato        = 12 // the column of the state labels
)

// tema: the mockup's colours. lipgloss brings them down by itself to 256 or 16 colours depending on the terminal, and to
// none with NO_COLOR (termenv.EnvColorProfile).
type tema struct {
	blu, verde, ambra, rosso, grigio, cornice, forte, campo lipgloss.Style
}

func nuovoTema(r *lipgloss.Renderer) tema {
	c := func(hex string) lipgloss.Style { return r.NewStyle().Foreground(lipgloss.Color(hex)) }
	return tema{
		blu:     c("#5A9BFF").Bold(true),
		verde:   c("#3EC27E").Bold(true),
		ambra:   c("#E3A82F").Bold(true),
		rosso:   c("#F0625A").Bold(true),
		grigio:  c("#7D889C"),
		cornice: c("#3A4457"),
		forte:   r.NewStyle().Bold(true),
		campo:   r.NewStyle().Reverse(true),
	}
}

type (
	msgControllo struct {
		c   *interfaccia.Controllo
		err error
	}
	msgPiano struct {
		p   *motore.Piano
		err error
	}
	msgEvento struct{ ev motore.EventoPubblico }
	msgEsito  struct {
		es  *interfaccia.Esito
		err error
	}
)

type modello struct {
	mot      interfaccia.Motore
	prog     *tea.Program
	t        tema
	schermo  int
	passo    int  // the step of the top line
	fallito  bool // the step stopped (red ✗)
	attesa   string
	ctrl     *interfaccia.Controllo
	vc       *interfaccia.VistaControllo
	vp       *interfaccia.VistaPiano
	piano    *motore.Piano
	av       *interfaccia.Avanzamento
	eventi   []motore.EventoPubblico
	pronto   *interfaccia.VistaPronto
	fine     *interfaccia.VistaBloccata
	porta    string
	modPorta bool   // the port is being typed
	vecchia  string // the previous port, for esc
	dett     bool
	reg      bool
	fermando bool
	nota     string
	larg     int
	alt      int
	scorri   int
	esito    *interfaccia.Esito
}

// Avvia: the TUI on the engine's session. The exit code follows the CLI's (0 if
// the installation is CONFERMATA).
func Avvia(mot interfaccia.Motore) (int, error) {
	m := nuovoModello(mot, lipgloss.DefaultRenderer())
	p := tea.NewProgram(m, tea.WithAltScreen())
	m.prog = p
	if _, err := p.Run(); err != nil {
		return 1, err
	}
	if m.esito != nil {
		fmt.Printf("%s\n  %s\n", motore.T("cli.operazione", m.esito.Operazione, m.esito.Stato), m.esito.Cartella)
		if m.esito.Stato == motore.CONFERMATA || m.esito.Stato == motore.CONFERMATA_A_CONDIZIONI {
			return 0, nil
		}
	}
	return 1, nil
}

func nuovoModello(mot interfaccia.Motore, r *lipgloss.Renderer) *modello {
	return &modello{mot: mot, t: nuovoTema(r), schermo: sAttesa, passo: pCheck,
		attesa: interfaccia.T("attendi.controllo"), porta: "7447", larg: larghezzaMinima, alt: 24}
}

func (m *modello) Init() tea.Cmd {
	return func() tea.Msg {
		c, err := m.mot.Controlla(7447)
		return msgControllo{c, err}
	}
}

func messaggio(err error) *motore.Messaggio {
	if e, ok := err.(*motore.ErroreRX); ok {
		return &e.M
	}
	x := motore.Msg("RX-UI-005", err.Error())
	return &x
}

func (m *modello) vai(schermo int) {
	m.schermo, m.scorri = schermo, 0
}

func (m *modello) finisci(es *interfaccia.Esito) {
	m.esito = es
	if es.Stato == motore.CONFERMATA || es.Stato == motore.CONFERMATA_A_CONDIZIONI {
		porta, _ := strconv.Atoi(m.porta)
		m.pronto = interfaccia.VistaDelPronto(es, m.vp, porta)
		m.passo = pReady
		m.vai(sPronto)
		return
	}
	if es.Errore == nil {
		es.Errore = interfaccia.UltimoMessaggio(m.eventi)
	}
	m.fine, m.fallito = interfaccia.VistaDellaFine(es, nil), true
	m.vai(sFine)
}

// chiediPiano: the plan for the typed port (the engine re-examines the machine if it changes).
func (m *modello) chiediPiano() tea.Cmd {
	voci := map[string]string{"port": m.porta}
	m.passo, m.attesa = pPlan, interfaccia.T("attendi.piano")
	m.vai(sAttesa)
	return func() tea.Msg {
		p, err := m.mot.Piano(voci)
		return msgPiano{p, err}
	}
}

func (m *modello) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch x := msg.(type) {
	case tea.WindowSizeMsg:
		m.larg, m.alt = x.Width, x.Height
	case msgControllo:
		if x.err != nil {
			m.finisci(&interfaccia.Esito{Errore: messaggio(x.err)})
			return m, nil
		}
		m.ctrl = x.c
		m.vc = interfaccia.VistaDelControllo(x.c)
		if x.c.Domande != nil {
			m.porta = strconv.Itoa(x.c.Domande.Porta)
		}
		if m.vc.Esito == interfaccia.BLOCCATA && len(m.vc.Righe) == 0 {
			m.fine, m.fallito = m.vc.Bloccata, true
			m.vai(sFine)
			return m, nil
		}
		m.fallito = m.vc.Esito == interfaccia.BLOCCATA
		m.vai(sControllo)
	case msgPiano:
		if x.err != nil {
			m.finisci(&interfaccia.Esito{Errore: messaggio(x.err)})
			return m, nil
		}
		if b := interfaccia.BloccoNelPiano(x.p); b != nil {
			m.finisci(&interfaccia.Esito{Errore: b})
			return m, nil
		}
		m.piano = x.p
		m.vp = interfaccia.VistaDelPiano(x.p)
		m.vai(sPiano)
	case msgEvento:
		m.eventi = append(m.eventi, x.ev)
		m.av.Evento(x.ev)
	case msgEsito:
		if x.err != nil {
			m.finisci(&interfaccia.Esito{Errore: messaggio(x.err)})
			return m, nil
		}
		m.finisci(x.es)
	case tea.KeyMsg:
		return m.tasto(x)
	}
	return m, nil
}

func (m *modello) tasto(k tea.KeyMsg) (tea.Model, tea.Cmd) {
	s := k.String()
	if s == "ctrl+c" {
		if m.schermo == sAvanzamento {
			return m, nil // while it works one cannot quit: it is stopped with «a», which puts things back as they were
		}
		return m, tea.Quit
	}
	if m.modPorta {
		return m.tastoPorta(s)
	}
	switch s {
	case "up", "k":
		m.scorri--
		return m, nil
	case "down", "j":
		m.scorri++
		return m, nil
	case "pgup":
		m.scorri -= m.altCorpo() - 1
		return m, nil
	case "pgdown", " ":
		m.scorri += m.altCorpo() - 1
		return m, nil
	case "home":
		m.scorri = 0
		return m, nil
	case "end":
		m.scorri = 1 << 20
		return m, nil
	case "d":
		m.dett = !m.dett
		return m, nil
	case "r":
		if m.schermo == sAvanzamento || m.schermo == sPronto || m.schermo == sFine {
			m.reg = !m.reg
			return m, nil
		}
	}
	switch m.schermo {
	case sAttesa:
		if s == "q" {
			return m, tea.Quit
		}
	case sControllo:
		switch s {
		case "q":
			return m, tea.Quit
		case "enter":
			if m.vc.Esito != interfaccia.BLOCCATA {
				return m, m.chiediPiano()
			}
		}
	case sPiano:
		switch s {
		case "y", "Y":
			m.av = interfaccia.NuovoAvanzamento(m.vp)
			m.passo = pInstall
			m.vai(sAvanzamento)
			digest := m.piano.Digest()
			return m, func() tea.Msg {
				es, err := m.mot.Applica(digest, func(ev motore.EventoPubblico) { m.prog.Send(msgEvento{ev}) })
				return msgEsito{es, err}
			}
		case "n", "N", "q":
			return m, tea.Quit // nothing has been touched
		case "tab":
			m.modPorta, m.vecchia = true, m.porta
		}
	case sAvanzamento:
		if s == "a" && !m.fermando {
			m.fermando = true
			go m.mot.Ferma()
		}
	case sPronto, sFine:
		switch s {
		case "enter", "q":
			return m, tea.Quit
		case "s":
			if m.schermo == sFine {
				m.salva("remotix-report.json", map[string]any{"end": m.fine, "check": m.ctrl, "events": m.eventi})
			}
		}
	}
	return m, nil
}

// tastoPorta: the port box, in the plan.
func (m *modello) tastoPorta(s string) (tea.Model, tea.Cmd) {
	switch s {
	case "esc":
		m.modPorta, m.porta = false, m.vecchia
	case "backspace":
		if len(m.porta) > 0 {
			m.porta = m.porta[:len(m.porta)-1]
		}
	case "enter", "tab":
		p, ok := interfaccia.PortaValida(m.porta)
		if !ok {
			return m, nil
		}
		m.modPorta, m.porta = false, strconv.Itoa(p)
		if m.porta != m.vecchia {
			return m, m.chiediPiano()
		}
	default:
		if len(s) == 1 && s[0] >= '0' && s[0] <= '9' && len(m.porta) < 5 {
			m.porta += s
		}
	}
	return m, nil
}

func (m *modello) salva(nome string, v any) {
	dir := "."
	if h, err := os.UserHomeDir(); err == nil {
		dir = h
	}
	p := filepath.Join(dir, nome)
	b, _ := json.MarshalIndent(v, "", "  ")
	if err := os.WriteFile(p, b, 0o600); err != nil {
		m.nota = err.Error()
		return
	}
	m.nota = interfaccia.T("salvato", p)
}

// ---- the frame -------------------------------------------------------------------------------

func (m *modello) interna() int { return m.larg - 4 } // «│ » and « │»

func (m *modello) altCorpo() int { return m.alt - 6 } // head, steps, two separators, keys, bottom

// riempi: a line exactly n columns long (cut with «…» if longer).
func riempi(s string, n int) string {
	w := ansi.StringWidth(s)
	if w > n {
		s = ansi.Truncate(s, n, "…")
		w = ansi.StringWidth(s)
	}
	return s + strings.Repeat(" ", n-w)
}

func (m *modello) View() string {
	if m.larg < larghezzaMinima {
		return riempi(interfaccia.T("tui.stretto", larghezzaMinima), m.larg)
	}
	if m.alt < altezzaMinima {
		return riempi(interfaccia.T("tui.basso", altezzaMinima), m.larg)
	}
	corpo, tasti := m.contenuto()
	return m.cornice(corpo, tasti)
}

func (m *modello) cornice(corpo []string, tasti string) string {
	t, w, in := m.t, m.larg, m.interna()
	bordo := t.cornice.Render
	var r []string
	// the head: «╭─ REMOTIX 1.0 · Installation ───── Debian 13 · GNOME 48 ─╮»
	sx := t.blu.Render("REMOTIX") + t.forte.Render(" "+motore.VersioneMotore+" · "+interfaccia.T("intestazione"))
	dx := ""
	if m.vc != nil {
		dx = m.vc.Intestazione
	}
	resto := w - 6 - ansi.StringWidth(sx) // «╭─ » sx « » … «─╮»
	if dx != "" {
		dx = ansi.Truncate(dx, resto-4, "…")
		resto -= ansi.StringWidth(dx) + 2
		r = append(r, bordo("╭─ ")+sx+bordo(" "+strings.Repeat("─", resto)+" ")+t.grigio.Render(dx)+bordo(" ─╮"))
	} else {
		r = append(r, bordo("╭─ ")+sx+bordo(" "+strings.Repeat("─", resto+1)+"╮"))
	}
	riga := func(s string) string { return bordo("│") + " " + riempi(s, in) + " " + bordo("│") }
	sep := bordo("├" + strings.Repeat("─", w-2) + "┤")
	r = append(r, riga(m.passi()), sep)
	// the body, which scrolls
	h := m.altCorpo()
	massimo := len(corpo) - h
	if massimo < 0 {
		massimo = 0
	}
	if m.scorri > massimo {
		m.scorri = massimo
	}
	if m.scorri < 0 {
		m.scorri = 0
	}
	for i := 0; i < h; i++ {
		s := ""
		if j := m.scorri + i; j < len(corpo) {
			s = corpo[j]
		}
		r = append(r, riga(s))
	}
	// the keys, and on the right where we are if the body is longer than the screen
	if massimo > 0 {
		pos := t.grigio.Render(fmt.Sprintf("↑↓ %d–%d / %d", m.scorri+1, m.scorri+h, len(corpo)))
		spazio := in - ansi.StringWidth(pos) - 1
		tasti = riempi(tasti, spazio) + " " + pos
	}
	r = append(r, sep, riga(tasti), bordo("╰"+strings.Repeat("─", w-2)+"╯"))
	return strings.Join(r, "\n")
}

func (m *modello) passi() string {
	t := m.t
	nomi := []string{interfaccia.T("passo.1"), interfaccia.T("passo.2"), interfaccia.T("passo.3"), interfaccia.T("passo.4")}
	var ps []string
	for i, n := range nomi {
		switch {
		case i < m.passo:
			ps = append(ps, t.verde.Render("✓ "+n))
		case i == m.passo && m.fallito:
			ps = append(ps, t.rosso.Render("✗ "+n))
		case i == m.passo && m.schermo == sPronto:
			ps = append(ps, t.verde.Render("✓ "+n))
		case i == m.passo:
			ps = append(ps, t.blu.Render("● "+n))
		default:
			ps = append(ps, t.grigio.Render("○ "+n))
		}
	}
	return strings.Join(ps, t.grigio.Render("  ›  "))
}

// tasti: «enter continue · d details · q quit», the key in bold and the rest grey.
func (m *modello) tasti(coppie ...string) string {
	var r []string
	for i := 0; i+1 < len(coppie); i += 2 {
		r = append(r, m.t.forte.Render(coppie[i])+m.t.grigio.Render(" "+coppie[i+1]))
	}
	return strings.Join(r, m.t.grigio.Render(" · "))
}

// ---- the body lines --------------------------------------------------------------------------

// par: a text wrapped inside the frame, indented, all in one style.
func (m *modello) par(testo string, st lipgloss.Style, rientro int) []string {
	if testo == "" {
		return nil
	}
	w := m.interna() - rientro
	var r []string
	for _, l := range strings.Split(ansi.Wrap(testo, w, ""), "\n") {
		r = append(r, strings.Repeat(" ", rientro)+st.Render(l))
	}
	return r
}

// colonne: label, text (wrapped in its column) and state label on the right.
func (m *modello) colonne(et, testo, cart string, st lipgloss.Style) []string {
	tw := m.interna() - colEtichetta - colStato - 1
	ls := strings.Split(ansi.Wrap(testo, tw, ""), "\n")
	var r []string
	for i, l := range ls {
		e, c := "", ""
		if i == 0 {
			e, c = et, st.Render(cart)
		}
		r = append(r, riempi(e, colEtichetta)+riempi(l, tw)+" "+c)
	}
	return r
}

func (m *modello) stileStato(s interfaccia.Stato) lipgloss.Style {
	switch s {
	case interfaccia.OK:
		return m.t.verde
	case interfaccia.AVVISO, interfaccia.CONSENSO:
		return m.t.ambra
	case interfaccia.SISTEMO:
		return m.t.blu
	case interfaccia.MALE, interfaccia.MANCA:
		return m.t.rosso
	}
	return m.t.grigio
}

// contenuto: the body of the current screen and the keys line.
func (m *modello) contenuto() ([]string, string) {
	T := interfaccia.T
	c := []string{""}
	var tasti string
	switch m.schermo {
	case sAttesa:
		c = append(c, m.par(m.attesa, m.t.forte, 0)...)
		tasti = m.tasti("q", T("k.esci"))
	case sControllo:
		c = append(c, m.corpoControllo()...)
		if m.vc.Esito == interfaccia.BLOCCATA {
			tasti = m.tasti("q", T("k.esci"), "d", T("k.dettagli"))
		} else {
			tasti = m.tasti("enter", T("k.avanti"), "d", T("k.dettagli"), "q", T("k.esci"))
		}
	case sPiano:
		c = append(c, m.corpoPiano()...)
		if m.modPorta {
			tasti = m.tasti("enter", T("k.porta.ok"), "esc", T("k.porta.no"))
		} else {
			tasti = m.t.forte.Render(T("k.procedi")) + " " + m.t.verde.Render("y") + m.t.grigio.Render(" "+T("k.si")+" · ") +
				m.t.rosso.Render("n") + m.t.grigio.Render(" "+T("k.no")+" · ") + m.tasti("tab", T("k.porta"), "d", T("k.dettagli"))
		}
	case sAvanzamento:
		c = append(c, m.corpoAvanzamento()...)
		if m.fermando {
			tasti = m.t.ambra.Render(T("btn.fermando"))
		} else {
			tasti = m.tasti("a", T("k.ferma"), "r", T("k.registro"))
		}
	case sPronto:
		c = append(c, m.corpoPronto()...)
		tasti = m.tasti("enter", T("k.chiudi"), "r", T("k.registro"), "d", T("k.dettagli"))
	case sFine:
		c = append(c, m.corpoFine()...)
		tasti = m.tasti("enter", T("k.chiudi"), "s", T("k.salva"), "d", T("k.dettagli"))
	}
	if m.nota != "" {
		c = append(c, "")
		c = append(c, m.par(m.nota, m.t.grigio, 0)...)
	}
	return append(c, ""), tasti
}

func (m *modello) corpoControllo() []string {
	T := interfaccia.T
	v := m.vc
	var c []string
	for _, r := range v.Righe {
		c = append(c, m.colonne(r.Etichetta, r.Testo, r.Stato.Cartellino(), m.stileStato(r.Stato))...)
	}
	c = append(c, "")
	if v.Esito == interfaccia.BLOCCATA {
		c = append(c, m.par(v.Banner, m.t.rosso, 0)...)
		c = append(c, m.par(v.Sotto, lipgloss.NewStyle(), 0)...)
		c = append(c, m.par(strings.Join(v.Codici, " "), m.t.grigio, 0)...)
	} else {
		c = append(c, m.par(v.Banner, m.t.forte, 0)...)
		c = append(c, m.par(v.Sotto, m.t.grigio, 0)...)
	}
	if m.dett {
		c = append(c, "", m.t.forte.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, m.t.grigio, 2)...)
	}
	return c
}

func (m *modello) corpoPiano() []string {
	T := interfaccia.T
	t, v := m.t, m.vp
	var c []string
	// the port, the only choice
	campo := "[ " + m.porta + " ]"
	if m.modPorta {
		campo = "[ " + m.porta + "▏]"
	}
	c = append(c, t.forte.Render(riempi(T("p.porta"), 10))+t.campo.Render(campo)+t.grigio.Render("   "+T("p.porta.t")))
	if _, ok := interfaccia.PortaValida(m.porta); !ok {
		c = append(c, t.rosso.Render(T("sc.porta.errata")))
	}
	// the exact packages, from the manager's simulation: REMOTIX (from the .run), then its dependencies
	// (from the distribution's repositories; labwc, wlr-randr and the font with the desktop requiring them)
	nuovi, aggiornati, presenti := 0, 0, 0
	var nostri, dip []string
	for _, a := range v.Pacchetti {
		nota := a.Origine
		if a.Origine == "file" {
			nota = ""
		}
		if why, ok := v.Dipendenze[a.Nome]; ok {
			nota = T("p.per", why)
		}
		var r string
		switch a.Esito {
		case "new":
			nuovi++
			r = "  " + t.verde.Render("+") + " " + riempi(a.Nome, 22) + riempi(a.Versione, 18) + t.grigio.Render(nota)
		case "upgraded":
			aggiornati++
			r = "  " + t.blu.Render("↑") + " " + riempi(a.Nome, 22) + riempi(a.Versione, 18) + t.grigio.Render(T("p.da.prima", a.Prima))
		default:
			presenti++
			continue
		}
		if a.Origine == "file" {
			nostri = append(nostri, r)
		} else {
			dip = append(dip, r)
		}
	}
	if len(nostri) > 0 {
		c = append(c, "", t.forte.Render("REMOTIX")+t.grigio.Render("   "+T("p.da.run")))
		c = append(c, nostri...)
	}
	if len(dip) > 0 {
		c = append(c, "", t.forte.Render(T("p.dipendenze"))+t.grigio.Render("   "+T("p.dipendenze.t")))
		c = append(c, dip...)
	}
	if len(v.Pacchetti) > 0 {
		c = append(c, t.grigio.Render("    "+T("p.totale", nuovi, aggiornati, presenti)))
	}
	// the people in the card's groups, the service, the other steps
	var altri []string
	irreversibili := []string{}
	for _, p := range v.Passi {
		if p.Rev == interfaccia.MALE {
			irreversibili = append(irreversibili, p.Titolo)
		}
		switch p.Tipo {
		case "groups":
			g := T("p.gruppi", strings.Join(v.Gruppi, ", "))
			if len(v.Gruppi) > 1 {
				g = T("p.gruppi.n", strings.Join(v.Gruppi, ", "))
			}
			c = append(c, "", t.forte.Render(g)+"   "+strings.Join(v.Utenti, ", "))
		case "service":
			c = append(c, "", t.forte.Render(T("p.servizio"))+"   "+T("p.servizio.t"))
		case "other":
			altri = append(altri, p.Titolo)
		}
	}
	if len(altri) > 0 {
		c = append(c, "", t.forte.Render(T("p.altro")))
		for _, a := range altri {
			c = append(c, m.par("· "+a, lipgloss.NewStyle(), 2)...)
		}
	}
	c = append(c, "")
	if len(irreversibili) == 0 {
		c = append(c, t.grigio.Render(T("p.annulla"))+t.blu.Render("remotix-install uninstall")+t.grigio.Render("."))
	} else {
		c = append(c, m.par(T("p.annulla.non", strings.Join(irreversibili, "; ")), t.ambra, 0)...)
	}
	if m.dett {
		c = append(c, "", t.forte.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, t.grigio, 2)...)
	}
	return c
}

func (m *modello) corpoAvanzamento() []string {
	T := interfaccia.T
	t := m.t
	punto, pc := m.av.Punto()
	in := m.interna()
	perc := fmt.Sprintf("%d %%", pc)
	c := []string{riempi(t.forte.Render(punto), in-ansi.StringWidth(perc)) + perc}
	pieni := in * pc / 100
	c = append(c, t.blu.Render(strings.Repeat("█", pieni))+t.grigio.Render(strings.Repeat("░", in-pieni)), "")
	for _, r := range m.av.Righe {
		switch r.Stato {
		case interfaccia.FATTA:
			c = append(c, "  "+t.verde.Render("✓")+" "+r.Testo)
		case interfaccia.INCORSO:
			c = append(c, "  "+t.blu.Render("◐ "+r.Testo))
		case interfaccia.FALLITA:
			c = append(c, "  "+t.rosso.Render("✗ "+r.Testo))
		case interfaccia.ANNULLATA:
			c = append(c, "  "+t.grigio.Render("↺ "+r.Testo))
		default:
			c = append(c, "  "+t.grigio.Render("○ "+r.Testo))
		}
	}
	if m.reg {
		c = append(c, "", t.forte.Render(T("h.registro")))
		for _, l := range ultime(m.av.Registro, 200) {
			c = append(c, m.par(l, t.grigio, 2)...)
		}
	}
	return c
}

func ultime(r []string, n int) []string {
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return r
}

func (m *modello) corpoPronto() []string {
	T := interfaccia.T
	t, v := m.t, m.pronto
	c := []string{t.verde.Render("✓ " + T("pr.titolo")), ""}
	c = append(c, t.forte.Render(T("h.apri")), "  "+t.blu.Render(v.Indirizzo))
	if v.Impronta != "" {
		c = append(c, m.par(T("pr.impronta", v.Impronta), t.grigio, 2)...)
	}
	c = append(c, m.par(T("pr.apri.t"), t.grigio, 2)...)
	c = append(c, "", t.forte.Render(T("h.dafare")))
	for _, d := range v.DaFare {
		c = append(c, m.puntoAvviso(d)...)
	}
	for _, d := range v.Condizioni {
		c = append(c, m.puntoAvviso(d)...)
	}
	c = append(c, m.par(v.Router, t.grigio, 4)...)
	c = append(c, "", t.forte.Render(T("h.chi")))
	c = append(c, m.par(T("pr.chi.t"), lipgloss.NewStyle(), 2)...)
	c = append(c, "", t.forte.Render(T("h.prove")))
	for _, p := range v.Prove {
		c = append(c, "  "+riempi(p.Etichetta, 36)+m.stileStato(p.Stato).Render(p.Testo))
	}
	if m.dett {
		c = append(c, "", t.forte.Render(T("h.cambiato")))
		for _, x := range v.Cambiato {
			c = append(c, m.par("· "+x, lipgloss.NewStyle(), 2)...)
		}
		c = append(c, "", t.forte.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, t.grigio, 2)...)
	}
	if m.reg && m.av != nil {
		c = append(c, "", t.forte.Render(T("h.registro")))
		for _, l := range ultime(m.av.Registro, 200) {
			c = append(c, m.par(l, t.grigio, 2)...)
		}
	}
	return c
}

// puntoAvviso: «  ! text» in amber, wrapped under the text.
func (m *modello) puntoAvviso(s string) []string {
	r := m.par(s, lipgloss.NewStyle(), 4)
	if len(r) > 0 {
		r[0] = "  " + m.t.ambra.Render("!") + " " + strings.TrimPrefix(r[0], "    ")
	}
	return r
}

func (m *modello) corpoFine() []string {
	T := interfaccia.T
	t, v := m.t, m.fine
	st := t.rosso
	if v.Toccata {
		st = t.ambra
	}
	c := m.par("✗ "+v.Titolo, st, 0)
	c = append(c, m.par(v.Sotto, t.grigio, 0)...)
	if v.Perche != "" {
		c = append(c, "", t.forte.Render(T("h.perche")))
		for _, l := range strings.Split(v.Perche, "\n") {
			c = append(c, m.par(l, lipgloss.NewStyle(), 2)...)
		}
		if x := strings.TrimSpace(v.Serve + "  " + v.Codice); x != "" {
			c = append(c, m.par(x, t.grigio, 2)...)
		}
	}
	if v.CheFare != "" {
		c = append(c, "", t.forte.Render(T("h.chefare")))
		c = append(c, m.par(v.CheFare, lipgloss.NewStyle(), 2)...)
	}
	if m.dett && v.Dettagli != "" {
		c = append(c, "", t.forte.Render(T("h.dettagli")))
		c = append(c, m.par(v.Dettagli, t.grigio, 2)...)
	}
	if m.reg && m.av != nil {
		c = append(c, "", t.forte.Render(T("h.registro")))
		for _, l := range ultime(m.av.Registro, 200) {
			c = append(c, m.par(l, t.grigio, 2)...)
		}
	}
	return c
}
