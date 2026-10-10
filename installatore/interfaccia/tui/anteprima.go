package tui

import (
	"io"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/muesli/termenv"

	"remotix/installatore/interfaccia"
	"remotix/installatore/motore"
)

// The previews: every screen drawn with sample data (the same as the approved mockup,
// grafica/tui-mockup/index.html), to compare it with the mockup and for the frame tests.
// `remotix-install tui --preview` prints them; without colours if colori == false.

// Schermata: a preview.
type Schermata struct {
	Nome, Testo string
}

// Anteprime: the screens at a given width and height (alt 0 = as tall as needed, without
// scrolling).
func Anteprime(larg, alt int, colori bool) []Schermata {
	r := lipgloss.NewRenderer(io.Discard)
	if colori {
		r.SetColorProfile(termenv.TrueColor)
	} else {
		r.SetColorProfile(termenv.Ascii)
	}
	var out []Schermata
	for _, s := range esempi() {
		m := nuovoModello(nil, r)
		s.prepara(m)
		m.larg, m.alt = larg, alt
		if alt == 0 {
			corpo, _ := m.contenuto()
			m.alt = len(corpo) + 6
			if m.alt < altezzaMinima {
				m.alt = altezzaMinima
			}
		}
		out = append(out, Schermata{s.nome, m.View()})
	}
	return out
}

type esempio struct {
	nome    string
	prepara func(m *modello)
}

func vcEsempio() *interfaccia.VistaControllo {
	return &interfaccia.VistaControllo{
		Intestazione: "Debian GNU/Linux 13 · GNOME 48",
		Esito:        interfaccia.CONDIZIONI,
		Banner:       interfaccia.T("c.cond1.titolo"),
		Sotto:        interfaccia.T("c.cond.firewall", 7447),
		Righe: []interfaccia.Riga{
			{Etichetta: "System", Testo: "Debian 13 · certified", Stato: interfaccia.OK},
			{Etichetta: "Desktop", Testo: "GNOME · Wayland", Stato: interfaccia.OK},
			{Etichetta: "Graphics card", Testo: "Intel card · encodes video", Stato: interfaccia.OK},
			{Etichetta: "Video", Testo: interfaccia.T("t.video.ok"), Stato: interfaccia.DOPO},
			{Etichetta: "Sign-in", Testo: interfaccia.T("t.accesso.ok"), Stato: interfaccia.OK},
			{Etichetta: "Users", Testo: interfaccia.T("t.persone", 3), Stato: interfaccia.OK},
			{Etichetta: "Firewall", Testo: interfaccia.T("t.fw.admin", "firewalld", 7447), Stato: interfaccia.AVVISO},
			{Etichetta: "Port", Testo: interfaccia.T("t.porta.libera", 7447), Stato: interfaccia.OK},
			{Etichetta: "Permissions", Testo: interfaccia.T("t.permessi.n", 3), Stato: interfaccia.SISTEMO},
			{Etichetta: "Audio", Testo: interfaccia.T("t.audio"), Stato: interfaccia.DOPO},
		},
		Dettagli: "Debian GNU/Linux 13 (trixie) · renderD128 Intel i915 · encoding.routes=vaapi · catalog 2026.10.10.14",
	}
}

func vpEsempio() *interfaccia.VistaPiano {
	return &interfaccia.VistaPiano{
		Passi: []interfaccia.Passo{
			{Tipo: "packages", Titolo: interfaccia.T("a.pacchetti"), Breve: interfaccia.T("a.pacchetti.b"), Rev: interfaccia.CONSENSO},
			{Tipo: "groups", Breve: interfaccia.T("a.gruppi.b", "alice, bob and carol", "render, video"), Rev: interfaccia.OK},
			{Tipo: "service", Breve: interfaccia.T("a.servizio.b"), Rev: interfaccia.OK},
		},
		Pacchetti: []motore.Artefatto{
			{Nome: "remotix", Versione: "1.0-1", Origine: "file", Esito: "new"},
			{Nome: "libei1", Versione: "1.3.0-1", Origine: "debian/trixie", Esito: "new"},
			{Nome: "pipewire-bin", Versione: "1.4.2-1", Origine: "debian/trixie", Esito: "new"},
			{Nome: "labwc", Versione: "0.8.3-1", Origine: "debian/trixie", Esito: "new"},
			{Nome: "libva2", Versione: "2.22.0-3", Origine: "debian/trixie", Esito: "present"},
		},
		Dipendenze: map[string]string{"labwc": "XFCE"},
		Utenti:     []string{"alice", "bob", "carol"},
		Gruppi:     []string{"render", "video"},
		Porta:      "7447",
		Dettagli:   "packages (install-packages, best-effort) · group-alice-render (add-user-to-group, exact) · plan 20261010-0912",
	}
}

func esempi() []esempio {
	return []esempio{
		{"check", func(m *modello) { m.vc, m.schermo, m.passo = vcEsempio(), sControllo, pCheck }},
		{"check-missing", func(m *modello) {
			vc := vcEsempio()
			vc.Intestazione = "Fedora Linux 44 · KDE Plasma 6"
			vc.Esito, vc.Banner, vc.Sotto = interfaccia.BLOCCATA, interfaccia.T("c.manca.titolo"), interfaccia.T("c.manca.testo")
			vc.Righe[0].Testo = "Fedora 44 · compatible, not certified"
			vc.Righe[1].Testo = "KDE Plasma · Wayland"
			vc.Righe[2] = interfaccia.Riga{Etichetta: "Graphics card", Testo: interfaccia.T("m.RX-GPU-006"), Stato: interfaccia.MANCA}
			vc.Codici = []string{"RX-GPU-006"}
			m.vc, m.schermo, m.passo, m.fallito = vc, sControllo, pCheck, true
		}},
		{"plan", func(m *modello) {
			m.vc, m.vp, m.schermo, m.passo, m.porta = vcEsempio(), vpEsempio(), sPiano, pPlan, "7447"
		}},
		{"install", func(m *modello) {
			m.vc, m.vp = vcEsempio(), vpEsempio()
			m.av = interfaccia.NuovoAvanzamento(m.vp)
			for i := range m.av.Righe {
				switch {
				case i < 2:
					m.av.Righe[i].Stato = interfaccia.FATTA
				case i == 2:
					m.av.Righe[i].Stato = interfaccia.INCORSO
				}
			}
			m.schermo, m.passo = sAvanzamento, pInstall
		}},
		{"ready", func(m *modello) {
			m.vc = vcEsempio()
			m.pronto = &interfaccia.VistaPronto{
				Indirizzo: "https://192.168.0.2:7447/",
				Impronta:  "4F:1A:9C:2B:…:E2:07",
				Router:    interfaccia.T("pr.router", 7447, "192.168.0.2"),
				DaFare:    []string{interfaccia.T("pr.todo.chiusa", 7447, "firewalld, zone public")},
				Prove: []interfaccia.Riga{
					{Etichetta: interfaccia.T("pr.k.servizio"), Testo: interfaccia.T("pr.riuscita"), Stato: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.h264"), Testo: interfaccia.T("pr.riuscita"), Stato: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.pam"), Testo: interfaccia.T("pr.riuscita"), Stato: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.porta"), Testo: interfaccia.T("pr.fallita"), Stato: interfaccia.MALE},
					{Etichetta: interfaccia.T("pr.k.passi", 8, 8), Testo: interfaccia.T("pr.riuscita"), Stato: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.audio"), Testo: interfaccia.T("pr.primo"), Stato: interfaccia.DOPO},
				},
			}
			m.schermo, m.passo = sPronto, pReady
		}},
		{"stopped", func(m *modello) {
			m.fine = &interfaccia.VistaBloccata{Titolo: interfaccia.T("b.titolo.annullata"), Sotto: interfaccia.T("b.sotto.annullata"),
				Perche: "The package manager could not install labwc: no repository of this machine provides it.",
				Codice: "RX-PACCHETTI-005", Toccata: true}
			m.schermo, m.passo, m.fallito = sFine, pInstall, true
		}},
	}
}

// Testo: the previews one after the other, with the name on top.
func Testo(s []Schermata) string {
	var b strings.Builder
	for _, x := range s {
		b.WriteString("── " + x.Nome + "\n" + x.Testo + "\n\n")
	}
	return b.String()
}
