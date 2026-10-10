package tui

import (
	"io"
	"strings"
	"testing"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/x/ansi"
	"github.com/muesli/termenv"
)

// The frame: every line of every screen is exactly as wide as the terminal, at 80 and at 120
// columns, with and without colours, as tall as needed and 24 lines tall (there the body scrolls); and the lines
// are as many as the height.
func TestCorniceLarghezzaCostante(t *testing.T) {
	for _, larg := range []int{80, 120} {
		for _, alt := range []int{0, 24, altezzaMinima} {
			for _, colori := range []bool{false, true} {
				for _, s := range Anteprime(larg, alt, colori) {
					righe := strings.Split(s.Testo, "\n")
					if alt > 0 && len(righe) != alt {
						t.Errorf("%s %dx%d: %d lines", s.Nome, larg, alt, len(righe))
					}
					for i, r := range righe {
						if w := ansi.StringWidth(r); w != larg {
							t.Errorf("%s %dx%d colori=%v, line %d: width %d: %q", s.Nome, larg, alt, colori, i, w, ansi.Strip(r))
						}
					}
					if strings.Contains(s.Testo, "⟨") {
						t.Errorf("%s: a text key is missing: %s", s.Nome, s.Testo)
					}
				}
			}
		}
	}
}

// Without colours (NO_COLOR, or a terminal that does not have them) no colour remains; bold does.
func TestSenzaColori(t *testing.T) {
	for _, s := range Anteprime(80, 0, false) {
		if strings.Contains(s.Testo, "38;2;") || strings.Contains(s.Testo, "38;5;") {
			t.Errorf("%s: colours with the Ascii profile", s.Nome)
		}
	}
}

// The mockup: the sentences the user approved are there, each in its screen.
func TestComeIlMockup(t *testing.T) {
	attese := map[string][]string{
		"check":         {"REMOTIX 0", "Installation", "● Check", "○ Plan", "System", "✓ OK", "! WARNING", "Nothing is missing.", "enter continue", "q quit"},
		"check-missing": {"✗ Check", "✗ MISSING", "no driver that encodes H.264", "REMOTIX cannot be installed yet.", "Provide what is missing, then run the installer again.", "RX-GPU-006"},
		"plan":          {"✓ Check", "● Plan", "Port", "[ 7447 ]", "TCP and UDP", "from this installer", "Dependencies of REMOTIX", "needed by REMOTIX for XFCE", "4 new · 0 upgraded · 1 already there", "Users added to groups render, video", "alice, bob, carol", "remotix.service, started after the final check", "Everything above is undone by remotix-install uninstall.", "Proceed? y yes · n no · tab edit port · d details"},
		"install":       {"● Install", "█", "✓ Catalogue", "◐ Installing the packages", "○ Starting remotix.service", "a stop and undo", "r log"},
		"ready":         {"✓ Ready", "✓ REMOTIX is running.", "OPEN IN A BROWSER", "https://192.168.0.2:7447/", "certificate SHA-256", "TO DO", "! Port 7447 TCP+UDP is closed by the firewall", "WHO CAN LOG IN", "root is excluded", "FINAL CHECKS", "Encoding on the graphics card", "enter close"},
		"stopped":       {"✗ The machine is back as it was", "WHY", "RX-PACCHETTI-005"},
	}
	for _, s := range Anteprime(80, 0, false) {
		piatto := ansi.Strip(s.Testo)
		for _, a := range attese[s.Nome] {
			if !strings.Contains(piatto, a) {
				t.Errorf("%s: %q missing in\n%s", s.Nome, a, piatto)
			}
		}
	}
}

// Below 80 columns a single line that says so, never broken wrapping.
func TestTroppoStretto(t *testing.T) {
	m := nuovoModello(nil, lipgloss.NewRenderer(io.Discard))
	m.Update(tea.WindowSizeMsg{Width: 60, Height: 30})
	v := m.View()
	if strings.Contains(v, "\n") || !strings.Contains(v, "80 columns needed") || ansi.StringWidth(v) != 60 {
		t.Errorf("60 columns: %q", v)
	}
}

// The body longer than the screen scrolls inside the frame, and the keys line says where we are.
func TestScorre(t *testing.T) {
	r := lipgloss.NewRenderer(io.Discard)
	r.SetColorProfile(termenv.Ascii)
	m := nuovoModello(nil, r)
	esempi()[2].prepara(m) // the plan
	m.larg, m.alt = 80, altezzaMinima
	prima := m.View()
	if !strings.Contains(prima, "↑↓ 1–") {
		t.Fatalf("no indicator:\n%s", prima)
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyPgDown})
	dopo := m.View()
	if prima == dopo || m.scorri == 0 {
		t.Errorf("page down does not scroll (scorri %d)", m.scorri)
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("G")}) // any key does not break it
	m.scorri = 1 << 20
	m.View()
	if corpo, _ := m.contenuto(); m.scorri != len(corpo)-m.altCorpo() {
		t.Errorf("at the bottom: scorri %d, body %d, height %d", m.scorri, len(corpo), m.altCorpo())
	}
}

// The port is typed with tab in the plan; a wrong number does not pass.
func TestPortaNelPiano(t *testing.T) {
	r := lipgloss.NewRenderer(io.Discard)
	m := nuovoModello(nil, r)
	esempi()[2].prepara(m)
	m.tasto(tea.KeyMsg{Type: tea.KeyTab})
	if !m.modPorta {
		t.Fatal("tab does not open the port")
	}
	for i := 0; i < 4; i++ {
		m.tasto(tea.KeyMsg{Type: tea.KeyBackspace})
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("0")})
	m.tasto(tea.KeyMsg{Type: tea.KeyEnter})
	if !m.modPorta || !strings.Contains(ansi.Strip(m.View()), "Enter a number between 1 and 65535.") {
		t.Errorf("port 0 accepted")
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyEsc})
	if m.modPorta || m.porta != "7447" {
		t.Errorf("esc: port %q, editing %v", m.porta, m.modPorta)
	}
}
