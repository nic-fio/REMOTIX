// Package tui: le schermate dell'installatore nel terminale (Bubble Tea), per chi lavora via ssh o
// dalla console (fasi/17 §6.6.1). Le STESSE schermate della finestra, dalle stesse viste
// (interfaccia.Vista…), sulla stessa sessione del motore; gira da root nel terminale.
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

	"remotix/installatore/interfaccia"
	"remotix/installatore/motore"
)

const (
	sAttesa = iota
	sControllo
	sScelte
	sPiano
	sAvanzamento
	sPronto
	sFine
)

var (
	stBlu      = lipgloss.NewStyle().Foreground(lipgloss.Color("#0A5FE0")).Bold(true)
	stTitolo   = lipgloss.NewStyle().Bold(true)
	stGrigio   = lipgloss.NewStyle().Foreground(lipgloss.Color("#8C97AD"))
	stVerde    = lipgloss.NewStyle().Foreground(lipgloss.Color("#1E9E5A")).Bold(true)
	stAmbra    = lipgloss.NewStyle().Foreground(lipgloss.Color("#C98A00")).Bold(true)
	stRosso    = lipgloss.NewStyle().Foreground(lipgloss.Color("#D0342C")).Bold(true)
	stSistemo  = lipgloss.NewStyle().Foreground(lipgloss.Color("#3B82F6")).Bold(true)
	stScelto   = lipgloss.NewStyle().Foreground(lipgloss.Color("#0A5FE0")).Bold(true)
	stCursore  = lipgloss.NewStyle().Reverse(true)
	stRiquadro = lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("#8C97AD")).Padding(0, 1)
)

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

type voce struct {
	domanda int // -1 = la porta
	opzione int
}

type modello struct {
	mot      interfaccia.Motore
	prog     *tea.Program
	schermo  int
	attesa   string
	ctrl     *interfaccia.Controllo
	vc       *interfaccia.VistaControllo
	vs       *interfaccia.VistaScelte
	vp       *interfaccia.VistaPiano
	piano    *motore.Piano
	av       *interfaccia.Avanzamento
	eventi   []motore.EventoPubblico
	pronto   *interfaccia.VistaPronto
	fine     *interfaccia.VistaBloccata
	voci     map[string]string
	porta    string
	cur      int
	dett     bool
	reg      bool
	fermando bool
	nota     string
	larg     int
	esito    *interfaccia.Esito
}

// Avvia: la TUI sulla sessione del motore. Il codice d'uscita segue quello della CLI (0 se
// l'installazione è CONFERMATA).
func Avvia(mot interfaccia.Motore) (int, error) {
	m := &modello{mot: mot, schermo: sAttesa, attesa: interfaccia.T("attendi.controllo"), larg: 100}
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

func (m *modello) finisci(es *interfaccia.Esito) {
	m.esito = es
	if es.Stato == motore.CONFERMATA || es.Stato == motore.CONFERMATA_A_CONDIZIONI {
		porta, _ := strconv.Atoi(m.voci["port"])
		m.pronto = interfaccia.VistaDelPronto(es, m.vp, porta, interfaccia.DepositoVideo(m.ctrl.Domande, m.voci))
		m.schermo = sPronto
		return
	}
	if es.Errore == nil {
		es.Errore = interfaccia.UltimoMessaggio(m.eventi)
	}
	m.fine = interfaccia.VistaDellaFine(es, nil)
	m.schermo = sFine
}

// le voci della schermata delle scelte, in fila (la porta, poi ogni opzione di ogni domanda)
func (m *modello) fila() []voce {
	f := []voce{{-1, 0}}
	for i, d := range m.vs.Domande {
		for j := range d.Opzioni {
			f = append(f, voce{i, j})
		}
	}
	return f
}

func (m *modello) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch x := msg.(type) {
	case tea.WindowSizeMsg:
		m.larg = x.Width
	case msgControllo:
		if x.err != nil {
			m.finisci(&interfaccia.Esito{Errore: messaggio(x.err)})
			return m, nil
		}
		m.ctrl = x.c
		m.vc = interfaccia.VistaDelControllo(x.c)
		if m.vc.Esito == interfaccia.BLOCCATA {
			m.fine, m.schermo = m.vc.Bloccata, sFine
			return m, nil
		}
		m.vs = interfaccia.VistaDelleScelte(x.c)
		m.voci = x.c.Domande.VociDiserie()
		m.porta = strconv.Itoa(x.c.Domande.Porta)
		m.schermo = sControllo
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
		m.vp = interfaccia.VistaDelPiano(x.p, m.ctrl.Profilo, interfaccia.NomiDepositi(m.ctrl.Domande))
		m.schermo = sPiano
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
	if s == "ctrl+c" || (s == "q" && m.schermo != sAvanzamento && m.schermo != sScelte) {
		if m.schermo == sAvanzamento {
			return m, nil // mentre lavora non si esce: si ferma con «a»
		}
		return m, tea.Quit
	}
	switch s {
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
	case sControllo:
		if s == "enter" {
			m.schermo, m.cur = sScelte, 0
		}
	case sScelte:
		f := m.fila()
		v := f[m.cur]
		switch s {
		case "up", "k":
			if m.cur > 0 {
				m.cur--
			}
		case "down", "j", "tab":
			if m.cur < len(f)-1 {
				m.cur++
			}
		case " ":
			if v.domanda >= 0 {
				d := m.vs.Domande[v.domanda]
				m.voci[d.Voce] = d.Opzioni[v.opzione].Valore
			}
		case "backspace":
			if v.domanda < 0 && len(m.porta) > 0 {
				m.porta = m.porta[:len(m.porta)-1]
			}
		case "esc":
			m.schermo = sControllo
		case "q":
			return m, tea.Quit
		case "enter":
			if v.domanda >= 0 {
				d := m.vs.Domande[v.domanda]
				m.voci[d.Voce] = d.Opzioni[v.opzione].Valore
			}
			p, ok := interfaccia.PortaValida(m.porta)
			if !ok {
				return m, nil
			}
			m.voci["port"] = strconv.Itoa(p)
			voci := map[string]string{}
			for a, b := range m.voci {
				voci[a] = b
			}
			m.schermo, m.attesa = sAttesa, interfaccia.T("attendi.piano")
			return m, func() tea.Msg {
				p, err := m.mot.Piano(voci)
				return msgPiano{p, err}
			}
		default:
			if v.domanda < 0 && len(s) == 1 && s[0] >= '0' && s[0] <= '9' && len(m.porta) < 5 {
				m.porta += s
			}
		}
	case sPiano:
		switch s {
		case "esc":
			m.schermo = sScelte
		case "s":
			m.salva("remotix-plan-"+m.piano.ID+".json", m.piano)
		case "enter":
			m.av = interfaccia.NuovoAvanzamento(m.vp)
			m.schermo = sAvanzamento
			digest := m.piano.Digest()
			return m, func() tea.Msg {
				es, err := m.mot.Applica(digest, func(ev motore.EventoPubblico) { m.prog.Send(msgEvento{ev}) })
				return msgEsito{es, err}
			}
		}
	case sAvanzamento:
		if s == "a" && !m.fermando {
			m.fermando = true
			go m.mot.Ferma()
		}
	case sPronto, sFine:
		if s == "enter" {
			return m, tea.Quit
		}
		if s == "s" && m.schermo == sFine {
			m.salva("remotix-report.json", map[string]any{"end": m.fine, "check": m.ctrl, "events": m.eventi})
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

// ---- il disegno ------------------------------------------------------------------------------

func cartellino(s interfaccia.Stato) string {
	t := "[" + s.Cartellino() + "]"
	switch s {
	case interfaccia.OK:
		return stVerde.Render(t)
	case interfaccia.CONSENSO:
		return stAmbra.Render(t)
	case interfaccia.SISTEMO:
		return stSistemo.Render(t)
	case interfaccia.MALE:
		return stRosso.Render(t)
	}
	return stGrigio.Render(t)
}

func (m *modello) a(s string) string {
	w := m.larg - 4
	if w < 40 {
		w = 40
	}
	return lipgloss.NewStyle().Width(w).Render(s)
}

func (m *modello) View() string {
	T := interfaccia.T
	var b strings.Builder
	testa := stBlu.Render("REMOTIX") + " · " + stTitolo.Render(T("intestazione"))
	if m.vc != nil && m.vc.Intestazione != "" {
		testa += stGrigio.Render("  —  " + m.vc.Intestazione)
	}
	b.WriteString(testa + "\n")
	cur := map[int]int{sControllo: 1, sScelte: 2, sPiano: 3, sAvanzamento: 4, sPronto: 5}[m.schermo]
	if cur > 0 {
		var ps []string
		for i := 1; i <= 5; i++ {
			n := fmt.Sprintf("%d %s", i, T(fmt.Sprintf("passo.%d", i)))
			switch {
			case i < cur:
				ps = append(ps, stVerde.Render("✓ "+n))
			case i == cur:
				ps = append(ps, stBlu.Render("● "+n))
			default:
				ps = append(ps, stGrigio.Render("○ "+n))
			}
		}
		b.WriteString(strings.Join(ps, stGrigio.Render("  ›  ")) + "\n")
	}
	b.WriteString("\n")
	switch m.schermo {
	case sAttesa:
		b.WriteString(m.attesa + "\n")
	case sControllo:
		m.viewControllo(&b)
	case sScelte:
		m.viewScelte(&b)
	case sPiano:
		m.viewPiano(&b)
	case sAvanzamento:
		m.viewAvanzamento(&b)
	case sPronto:
		m.viewPronto(&b)
	case sFine:
		m.viewFine(&b)
	}
	if m.nota != "" {
		b.WriteString("\n" + stGrigio.Render(m.nota) + "\n")
	}
	return b.String()
}

func (m *modello) tasti(ts ...string) string {
	return "\n" + stGrigio.Render(strings.Join(ts, " · ")) + "\n"
}

func (m *modello) viewControllo(b *strings.Builder) {
	T := interfaccia.T
	v := m.vc
	b.WriteString(stTitolo.Render(T("c.titolo")) + "\n" + stGrigio.Render(T("c.sotto")) + "\n\n")
	st := stVerde
	if v.Esito == interfaccia.CONDIZIONI {
		st = stAmbra
	}
	b.WriteString(stRiquadro.Render(st.Render(v.Banner)+"\n"+m.a(v.Sotto)) + "\n\n")
	for _, r := range v.Righe {
		b.WriteString(fmt.Sprintf("  %-24s %-62s %s\n", r.Etichetta, r.Testo, cartellino(r.Stato)))
	}
	if m.dett {
		b.WriteString("\n" + stGrigio.Render(m.a(v.Dettagli)) + "\n")
	}
	b.WriteString(m.tasti(T("btn.avanti")+": invio", T("tui.dettagli"), "q "+strings.ToLower(T("btn.annulla"))))
}

func (m *modello) viewScelte(b *strings.Builder) {
	T := interfaccia.T
	v := m.vs
	b.WriteString(stTitolo.Render(v.Titolo) + "\n" + stGrigio.Render(m.a(v.Sotto)) + "\n\n")
	f := m.fila()
	sel := f[m.cur]
	// la porta
	porta := m.porta
	if sel.domanda < 0 {
		porta = stCursore.Render(porta + "▏")
	}
	b.WriteString(stTitolo.Render(T("sc.porta")) + "\n  " + T("tui.porta") + porta + "   " + stGrigio.Render(T("sc.porta.nota")) + "\n")
	if _, ok := interfaccia.PortaValida(m.porta); !ok {
		b.WriteString("  " + stRosso.Render(T("sc.porta.errata")) + "\n")
	}
	if v.PortaRiga != "" {
		st := stGrigio
		if v.PortaVerde {
			st = stVerde
		}
		b.WriteString("  " + st.Render(v.PortaRiga) + "\n")
	}
	for i, d := range v.Domande {
		b.WriteString("\n" + stTitolo.Render(d.Titolo) + "\n")
		if d.Spiega != "" {
			b.WriteString(stGrigio.Render(m.a(d.Spiega)) + "\n")
		}
		for j, o := range d.Opzioni {
			pallino := "( )"
			if m.voci[d.Voce] == o.Valore {
				pallino = stScelto.Render("(•)")
			}
			t := o.Titolo
			if o.Nota != "" {
				t += " " + stVerde.Render(o.Nota)
			}
			r := "  " + pallino + " " + t
			if sel.domanda == i && sel.opzione == j {
				r = stCursore.Render(">") + r[1:]
			}
			b.WriteString(r + "\n")
			if o.Testo != "" {
				b.WriteString("        " + stGrigio.Render(o.Testo) + "\n")
			}
		}
	}
	if v.Nota != "" {
		b.WriteString("\n" + stGrigio.Render(m.a(v.Nota)) + "\n")
	}
	b.WriteString(m.tasti(T("tui.tasti")))
}

func (m *modello) viewPiano(b *strings.Builder) {
	T := interfaccia.T
	b.WriteString(stTitolo.Render(T("p.titolo")) + "\n" + stGrigio.Render(m.a(T("p.sotto"))) + "\n\n")
	for i, p := range m.vp.Passi {
		st := stVerde
		switch p.Rev {
		case interfaccia.CONSENSO:
			st = stAmbra
		case interfaccia.MALE:
			st = stRosso
		}
		t := p.Titolo
		if p.Nota != "" {
			t += " " + stGrigio.Render(p.Nota)
		}
		b.WriteString(fmt.Sprintf("  %d  %s  %s\n", i+1, t, st.Render("["+p.Cartellino()+"]")))
		if p.Sotto != "" {
			b.WriteString("     " + stGrigio.Render(p.Sotto) + "\n")
		}
	}
	b.WriteString("\n" + stGrigio.Render(m.a(T("p.nota"))) + "\n")
	if m.dett {
		b.WriteString("\n" + stGrigio.Render(m.a(m.vp.Dettagli)) + "\n")
	}
	b.WriteString(m.tasti(T("tui.conferma"), "s: "+strings.ToLower(T("btn.salva_piano")), T("tui.dettagli"), "esc "+strings.ToLower(T("btn.indietro"))))
}

func (m *modello) viewAvanzamento(b *strings.Builder) {
	T := interfaccia.T
	b.WriteString(stTitolo.Render(T("av.titolo")) + "\n" + stGrigio.Render(m.a(T("av.sotto"))) + "\n\n")
	punto, pc := m.av.Punto()
	w := 50
	pieni := w * pc / 100
	b.WriteString(stTitolo.Render(punto) + fmt.Sprintf("  %d %%\n", pc))
	b.WriteString(stBlu.Render(strings.Repeat("█", pieni)) + stGrigio.Render(strings.Repeat("░", w-pieni)) + "\n\n")
	for _, r := range m.av.Righe {
		switch r.Stato {
		case interfaccia.FATTA:
			b.WriteString("  " + stVerde.Render("✓") + " " + r.Testo + "\n")
		case interfaccia.INCORSO:
			b.WriteString("  " + stBlu.Render("◐ "+r.Testo) + "\n")
		case interfaccia.FALLITA:
			b.WriteString("  " + stRosso.Render("✗ "+r.Testo) + "\n")
		case interfaccia.ANNULLATA:
			b.WriteString("  " + stGrigio.Render("↺ "+r.Testo) + "\n")
		default:
			b.WriteString("  " + stGrigio.Render("○ "+r.Testo) + "\n")
		}
	}
	if m.reg {
		b.WriteString("\n" + stGrigio.Render(ultime(m.av.Registro, 12)) + "\n")
	}
	f := T("tui.ferma")
	if m.fermando {
		f = T("btn.fermando")
	}
	b.WriteString(m.tasti(f, T("tui.registro")))
}

func ultime(r []string, n int) string {
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return strings.Join(r, "\n")
}

func (m *modello) viewPronto(b *strings.Builder) {
	T := interfaccia.T
	v := m.pronto
	b.WriteString(stVerde.Render("✓ "+T("pr.titolo")) + "\n" + stGrigio.Render(m.a(v.Sotto)) + "\n\n")
	b.WriteString(stTitolo.Render(strings.ToUpper(T("pr.apri"))) + "\n  " + stBlu.Render(v.Indirizzo) + "\n  " + stGrigio.Render(T("pr.apri.t")) + "\n  " + stGrigio.Render(v.Router) + "\n")
	if v.Impronta != "" {
		b.WriteString("  " + stGrigio.Render(T("pr.impronta")+" SHA-256 "+v.Impronta) + "\n")
	}
	b.WriteString("\n" + stTitolo.Render(strings.ToUpper(T("pr.chi"))) + "\n  " + T("pr.chi.t") + " " + stTitolo.Render(T("pr.chi.root")) + "\n  " + stGrigio.Render(T("pr.chi.t2")) + "\n")
	b.WriteString("\n" + stTitolo.Render(strings.ToUpper(T("pr.cambiato"))) + "\n")
	for _, c := range v.Cambiato {
		b.WriteString("  • " + c + "\n")
	}
	b.WriteString("\n" + stTitolo.Render(strings.ToUpper(T("pr.prove"))) + "\n")
	for _, p := range v.Prove {
		st := stVerde
		switch p.Stato {
		case interfaccia.MALE:
			st = stRosso
		case interfaccia.DOPO, interfaccia.IGNOTO:
			st = stGrigio
		}
		b.WriteString(fmt.Sprintf("  %-52s %s\n", p.Etichetta, st.Render(p.Testo)))
	}
	if m.dett {
		b.WriteString("\n" + stGrigio.Render(m.a(v.Dettagli)) + "\n")
	}
	if m.reg {
		b.WriteString("\n" + stGrigio.Render(ultime(m.av.Registro, 20)) + "\n")
	}
	b.WriteString(m.tasti(T("tui.chiudi"), T("tui.registro"), T("tui.dettagli")))
}

func (m *modello) viewFine(b *strings.Builder) {
	T := interfaccia.T
	v := m.fine
	st := stRosso
	if v.Toccata {
		st = stAmbra
	}
	b.WriteString(st.Render("✗ "+v.Titolo) + "\n" + stGrigio.Render(m.a(v.Sotto)) + "\n\n")
	if v.Perche != "" {
		b.WriteString(stTitolo.Render(T("b.perche")) + "\n" + m.a(v.Perche) + "\n")
		if v.Serve != "" || v.Codice != "" {
			b.WriteString(stGrigio.Render(strings.TrimSpace(v.Serve+"  "+v.Codice)) + "\n")
		}
		b.WriteString("\n")
	}
	if v.CheFare != "" {
		b.WriteString(stTitolo.Render(T("b.chefare")) + "\n" + m.a(v.CheFare) + "\n")
	}
	if m.dett && v.Dettagli != "" {
		b.WriteString("\n" + stGrigio.Render(m.a(v.Dettagli)) + "\n")
	}
	if m.reg && m.av != nil {
		b.WriteString("\n" + stGrigio.Render(ultime(m.av.Registro, 20)) + "\n")
	}
	b.WriteString(m.tasti(T("tui.chiudi"), "s: "+strings.ToLower(T("btn.salva_rapp")), T("tui.dettagli")))
}
