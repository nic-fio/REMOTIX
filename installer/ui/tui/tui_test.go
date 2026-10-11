package tui

import (
	"io"
	"strconv"
	"strings"
	"testing"

	"remotix/installer/engine"
	"remotix/installer/ui"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/charmbracelet/x/ansi"
	"github.com/muesli/termenv"
)

// The frame: every line of every screen is exactly as wide as the terminal, at 80 and at 120
// columns, with and without colours, as tall as needed and 24 lines tall (there the body scrolls); and the lines
// are as many as the height.
func TestBorderConstantWidth(t *testing.T) {
	for _, wid := range []int{80, 120} {
		for _, h := range []int{0, 24, minHeight} {
			for _, colors := range []bool{false, true} {
				for _, s := range Previews(wid, h, colors) {
					lines := strings.Split(s.Testo, "\n")
					if h > 0 && len(lines) != h {
						t.Errorf("%s %dx%d: %d lines", s.Nome, wid, h, len(lines))
					}
					for i, r := range lines {
						if w := ansi.StringWidth(r); w != wid {
							t.Errorf("%s %dx%d colors=%v, line %d: width %d: %q", s.Nome, wid, h, colors, i, w, ansi.Strip(r))
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
func TestWithoutColors(t *testing.T) {
	for _, s := range Previews(80, 0, false) {
		if strings.Contains(s.Testo, "38;2;") || strings.Contains(s.Testo, "38;5;") {
			t.Errorf("%s: colours with the Ascii profile", s.Nome)
		}
	}
}

// The mockup: the sentences the user approved are there, each in its screen.
func TestComeIlMockup(t *testing.T) {
	waits := map[string][]string{
		"check":         {"REMOTIX 0", "Installation", "● Check", "○ Plan", "System", "✓ OK", "! WARNING", "Nothing is missing.", "enter continue", "q quit"},
		"check-missing": {"✗ Check", "✗ MISSING", "no driver that encodes H.264", "REMOTIX cannot be installed yet.", "Provide what is missing, then run the installer again.", "RX-GPU-006"},
		"plan":          {"✓ Check", "● Plan", "Port", "[ 7447 ]", "TCP and UDP", "from this installer", "Dependencies of REMOTIX", "needed by REMOTIX for XFCE", "4 new · 0 upgraded · 1 already there", "Users added to groups render, video", "alice, bob, carol", "remotix.service, started after the final check", "Everything above is undone by remotix-install uninstall.", "Proceed? y yes · n no · tab edit port · d details"},
		"install":       {"● Install", "█", "✓ Catalogue", "◐ Installing the packages", "○ Starting remotix.service", "a stop and undo", "r log"},
		"ready":         {"✓ Ready", "✓ REMOTIX is running.", "OPEN IN A BROWSER", "https://192.168.0.2:7447/", "certificate SHA-256", "TO DO", "! Port 7447 TCP+UDP is closed by the firewall", "WHO CAN LOG IN", "root is excluded", "FINAL CHECKS", "Encoding on the graphics card", "enter close"},
		"stopped":       {"✗ The machine is back as it was", "WHY", "RX-PACCHETTI-005"},
	}
	for _, s := range Previews(80, 0, false) {
		flat := ansi.Strip(s.Testo)
		for _, a := range waits[s.Nome] {
			if !strings.Contains(flat, a) {
				t.Errorf("%s: %q missing in\n%s", s.Nome, a, flat)
			}
		}
	}
}

// Below 80 columns a single line that says so, never broken wrapping.
func TestTooTight(t *testing.T) {
	m := newModel(nil, lipgloss.NewRenderer(io.Discard))
	m.Update(tea.WindowSizeMsg{Width: 60, Height: 30})
	v := m.View()
	if strings.Contains(v, "\n") || !strings.Contains(v, "80 columns needed") || ansi.StringWidth(v) != 60 {
		t.Errorf("60 columns: %q", v)
	}
}

// The body longer than the screen scrolls inside the frame, and the keys line says where we are.
func TestScrolls(t *testing.T) {
	r := lipgloss.NewRenderer(io.Discard)
	r.SetColorProfile(termenv.Ascii)
	m := newModel(nil, r)
	examples()[2].prepare(m) // the plan
	m.wid, m.h = 80, minHeight
	before := m.View()
	if !strings.Contains(before, "↑↓ 1–") {
		t.Fatalf("no indicator:\n%s", before)
	}
	m.keystroke(tea.KeyMsg{Type: tea.KeyPgDown})
	after := m.View()
	if before == after || m.scroll == 0 {
		t.Errorf("page down does not scroll (scroll %d)", m.scroll)
	}
	m.keystroke(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("G")}) // any key does not break it
	m.scroll = 1 << 20
	m.View()
	if body, _ := m.content(); m.scroll != len(body)-m.bodyHeight() {
		t.Errorf("at the bottom: scroll %d, body %d, height %d", m.scroll, len(body), m.bodyHeight())
	}
}

// The port is typed with tab in the plan; a wrong number does not pass.
func TestPortInPlan(t *testing.T) {
	r := lipgloss.NewRenderer(io.Discard)
	m := newModel(nil, r)
	examples()[2].prepare(m)
	m.keystroke(tea.KeyMsg{Type: tea.KeyTab})
	if !m.modPort {
		t.Fatal("tab does not open the port")
	}
	for i := 0; i < 4; i++ {
		m.keystroke(tea.KeyMsg{Type: tea.KeyBackspace})
	}
	m.keystroke(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("0")})
	m.keystroke(tea.KeyMsg{Type: tea.KeyEnter})
	if !m.modPort || !strings.Contains(ansi.Strip(m.View()), "Enter a number between 1 and 65535.") {
		t.Errorf("port 0 accepted")
	}
	m.keystroke(tea.KeyMsg{Type: tea.KeyEsc})
	if m.modPort || m.port != "7447" {
		t.Errorf("esc: port %q, editing %v", m.port, m.modPort)
	}
}

// fakeEngine: records the port the check is asked for.
type fakeEngine struct{ port int }

func (f *fakeEngine) Check(port int) (*ui.CheckReport, error) {
	f.port = port
	return &ui.CheckReport{Questions: engine.QuestionsToAsk(nil, port)}, nil
}
func (f *fakeEngine) Piano(map[string]string) (*engine.Piano, error) { return nil, nil }
func (f *fakeEngine) Apply(string, func(engine.PublicEvent)) (*ui.Outcome, error) {
	return nil, nil
}
func (f *fakeEngine) Stop()  {}
func (f *fakeEngine) Close() {}

// --port N: the check examines N (not 7447) and the plan's box starts from N; without --port, 7447.
func TestPortFromCommandLine(t *testing.T) {
	for _, c := range []struct{ data, wait int }{{8640, 8640}, {0, 7447}, {70000, 7447}} {
		f := &fakeEngine{}
		m := newModel(f, lipgloss.NewRenderer(io.Discard))
		m.initial(c.data)
		msg := m.Init()()
		if f.port != c.wait {
			t.Errorf("--port %d: the check examined %d, want %d", c.data, f.port, c.wait)
		}
		m.Update(msg)
		if m.port != strconv.Itoa(c.wait) {
			t.Errorf("--port %d: the plan starts from %q, want %d", c.data, m.port, c.wait)
		}
	}
}
