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

// La cornice: ogni riga di ogni schermata è larga esattamente quanto il terminale, a 80 e a 120
// colonne, con e senza colori, alta quanto serve e alta 24 righe (lì il corpo scorre); e le righe
// sono tante quante l'altezza.
func TestCorniceLarghezzaCostante(t *testing.T) {
	for _, larg := range []int{80, 120} {
		for _, alt := range []int{0, 24, altezzaMinima} {
			for _, colori := range []bool{false, true} {
				for _, s := range Anteprime(larg, alt, colori) {
					righe := strings.Split(s.Testo, "\n")
					if alt > 0 && len(righe) != alt {
						t.Errorf("%s %dx%d: %d righe", s.Nome, larg, alt, len(righe))
					}
					for i, r := range righe {
						if w := ansi.StringWidth(r); w != larg {
							t.Errorf("%s %dx%d colori=%v, riga %d: larga %d: %q", s.Nome, larg, alt, colori, i, w, ansi.Strip(r))
						}
					}
					if strings.Contains(s.Testo, "⟨") {
						t.Errorf("%s: una chiave dei testi manca: %s", s.Nome, s.Testo)
					}
				}
			}
		}
	}
}

// Senza colori (NO_COLOR, o un terminale che non li ha) non resta nessun colore; il grassetto sì.
func TestSenzaColori(t *testing.T) {
	for _, s := range Anteprime(80, 0, false) {
		if strings.Contains(s.Testo, "38;2;") || strings.Contains(s.Testo, "38;5;") {
			t.Errorf("%s: colori con il profilo Ascii", s.Nome)
		}
	}
}

// Il mockup: le frasi che l'utente ha approvato ci sono, ognuna nella sua schermata.
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
				t.Errorf("%s: manca %q in\n%s", s.Nome, a, piatto)
			}
		}
	}
}

// Sotto 80 colonne una riga sola che lo dice, mai a capo rotti.
func TestTroppoStretto(t *testing.T) {
	m := nuovoModello(nil, lipgloss.NewRenderer(io.Discard))
	m.Update(tea.WindowSizeMsg{Width: 60, Height: 30})
	v := m.View()
	if strings.Contains(v, "\n") || !strings.Contains(v, "80 columns needed") || ansi.StringWidth(v) != 60 {
		t.Errorf("60 colonne: %q", v)
	}
}

// Il corpo più lungo dello schermo scorre dentro la cornice, e la riga dei tasti dice dove si è.
func TestScorre(t *testing.T) {
	r := lipgloss.NewRenderer(io.Discard)
	r.SetColorProfile(termenv.Ascii)
	m := nuovoModello(nil, r)
	esempi()[2].prepara(m) // il piano
	m.larg, m.alt = 80, altezzaMinima
	prima := m.View()
	if !strings.Contains(prima, "↑↓ 1–") {
		t.Fatalf("niente indicatore:\n%s", prima)
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyPgDown})
	dopo := m.View()
	if prima == dopo || m.scorri == 0 {
		t.Errorf("pagina giù non scorre (scorri %d)", m.scorri)
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("G")}) // un tasto qualunque non rompe
	m.scorri = 1 << 20
	m.View()
	if corpo, _ := m.contenuto(); m.scorri != len(corpo)-m.altCorpo() {
		t.Errorf("in fondo: scorri %d, corpo %d, alto %d", m.scorri, len(corpo), m.altCorpo())
	}
}

// La porta si scrive con tab nel piano; un numero sbagliato non passa.
func TestPortaNelPiano(t *testing.T) {
	r := lipgloss.NewRenderer(io.Discard)
	m := nuovoModello(nil, r)
	esempi()[2].prepara(m)
	m.tasto(tea.KeyMsg{Type: tea.KeyTab})
	if !m.modPorta {
		t.Fatal("tab non apre la porta")
	}
	for i := 0; i < 4; i++ {
		m.tasto(tea.KeyMsg{Type: tea.KeyBackspace})
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("0")})
	m.tasto(tea.KeyMsg{Type: tea.KeyEnter})
	if !m.modPorta || !strings.Contains(ansi.Strip(m.View()), "Enter a number between 1 and 65535.") {
		t.Errorf("porta 0 accettata")
	}
	m.tasto(tea.KeyMsg{Type: tea.KeyEsc})
	if m.modPorta || m.porta != "7447" {
		t.Errorf("esc: porta %q, modifica %v", m.porta, m.modPorta)
	}
}
