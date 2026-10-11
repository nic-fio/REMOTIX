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
// `remotix-install tui --preview` prints them; without colours if colors == false.

// Screen: a preview.
type Screen struct {
	Nome, Testo string
}

// Previews: the screens at a given width and height (h 0 = as tall as needed, without
// scrolling).
func Previews(wid, h int, colors bool) []Screen {
	r := lipgloss.NewRenderer(io.Discard)
	if colors {
		r.SetColorProfile(termenv.TrueColor)
	} else {
		r.SetColorProfile(termenv.Ascii)
	}
	var out []Screen
	for _, s := range examples() {
		m := newModel(nil, r)
		s.prepare(m)
		m.wid, m.h = wid, h
		if h == 0 {
			body, _ := m.content()
			m.h = len(body) + 6
			if m.h < minHeight {
				m.h = minHeight
			}
		}
		out = append(out, Screen{s.name, m.View()})
	}
	return out
}

type example struct {
	name    string
	prepare func(m *model)
}

func vcExample() *interfaccia.CheckView {
	return &interfaccia.CheckView{
		Header: "Debian GNU/Linux 13 · GNOME 48",
		Outcome:        interfaccia.CONDS,
		Banner:       interfaccia.T("c.cond1.titolo"),
		Below:        interfaccia.T("c.cond.firewall", 7447),
		Righe: []interfaccia.Line{
			{Etichetta: "System", Testo: "Debian 13 · certified", State: interfaccia.OK},
			{Etichetta: "Desktop", Testo: "GNOME · Wayland", State: interfaccia.OK},
			{Etichetta: "Graphics card", Testo: "Intel card · encodes video", State: interfaccia.OK},
			{Etichetta: "Video", Testo: interfaccia.T("t.video.ok"), State: interfaccia.DOPO},
			{Etichetta: "Sign-in", Testo: interfaccia.T("t.accesso.ok"), State: interfaccia.OK},
			{Etichetta: "Users", Testo: interfaccia.T("t.persone", 3), State: interfaccia.OK},
			{Etichetta: "Firewall", Testo: interfaccia.T("t.fw.admin", "firewalld", 7447), State: interfaccia.WARNING},
			{Etichetta: "Port", Testo: interfaccia.T("t.porta.libera", 7447), State: interfaccia.OK},
			{Etichetta: "Permissions", Testo: interfaccia.T("t.permessi.n", 3), State: interfaccia.FIX},
			{Etichetta: "Audio", Testo: interfaccia.T("t.audio"), State: interfaccia.DOPO},
		},
		Dettagli: "Debian GNU/Linux 13 (trixie) · renderD128 Intel i915 · encoding.routes=vaapi · catalog 2026.10.10.14",
	}
}

func vpExample() *interfaccia.VistaPiano {
	return &interfaccia.VistaPiano{
		Steps: []interfaccia.Stride{
			{Type: "packages", Titolo: interfaccia.T("a.pacchetti"), Breve: interfaccia.T("a.pacchetti.b"), Rev: interfaccia.CONSENT},
			{Type: "groups", Breve: interfaccia.T("a.gruppi.b", "alice, bob and carol", "render, video"), Rev: interfaccia.OK},
			{Type: "service", Breve: interfaccia.T("a.servizio.b"), Rev: interfaccia.OK},
		},
		Pacchetti: []engine.Artifact{
			{Nome: "remotix", Ver: "1.0-1", Origine: "file", Outcome: "new"},
			{Nome: "libei1", Ver: "1.3.0-1", Origine: "debian/trixie", Outcome: "new"},
			{Nome: "pipewire-bin", Ver: "1.4.2-1", Origine: "debian/trixie", Outcome: "new"},
			{Nome: "labwc", Ver: "0.8.3-1", Origine: "debian/trixie", Outcome: "new"},
			{Nome: "libva2", Ver: "2.22.0-3", Origine: "debian/trixie", Outcome: "present"},
		},
		Dipendenze: map[string]string{"labwc": "XFCE"},
		Utenti:     []string{"alice", "bob", "carol"},
		Gruppi:     []string{"render", "video"},
		Porta:      "7447",
		Dettagli:   "packages (install-packages, best-effort) · group-alice-render (add-user-to-group, exact) · plan 20261010-0912",
	}
}

func examples() []example {
	return []example{
		{"check", func(m *model) { m.vc, m.screen, m.step = vcExample(), sCheck, pCheck }},
		{"check-missing", func(m *model) {
			vc := vcExample()
			vc.Header = "Fedora Linux 44 · KDE Plasma 6"
			vc.Outcome, vc.Banner, vc.Below = interfaccia.BLOCKED, interfaccia.T("c.manca.titolo"), interfaccia.T("c.manca.testo")
			vc.Righe[0].Testo = "Fedora 44 · compatible, not certified"
			vc.Righe[1].Testo = "KDE Plasma · Wayland"
			vc.Righe[2] = interfaccia.Line{Etichetta: "Graphics card", Testo: interfaccia.T("m.RX-GPU-006"), State: interfaccia.MISSING}
			vc.Codes = []string{"RX-GPU-006"}
			m.vc, m.screen, m.step, m.has_failed = vc, sCheck, pCheck, true
		}},
		{"plan", func(m *model) {
			m.vc, m.vp, m.screen, m.step, m.port = vcExample(), vpExample(), sPiano, pPlan, "7447"
		}},
		{"install", func(m *model) {
			m.vc, m.vp = vcExample(), vpExample()
			m.av = interfaccia.NewProgress(m.vp)
			for i := range m.av.Righe {
				switch {
				case i < 2:
					m.av.Righe[i].State = interfaccia.DONE
				case i == 2:
					m.av.Righe[i].State = interfaccia.IN_PROGRESS
				}
			}
			m.screen, m.step = sProgress, pInstall
		}},
		{"ready", func(m *model) {
			m.vc = vcExample()
			m.ready = &interfaccia.ReadyView{
				Address: "https://192.168.0.2:7447/",
				Fingerprint:  "4F:1A:9C:2B:…:E2:07",
				Router:    interfaccia.T("pr.router", 7447, "192.168.0.2"),
				DaFare:    []string{interfaccia.T("pr.todo.chiusa", 7447, "firewalld, zone public")},
				Prove: []interfaccia.Line{
					{Etichetta: interfaccia.T("pr.k.servizio"), Testo: interfaccia.T("pr.riuscita"), State: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.h264"), Testo: interfaccia.T("pr.riuscita"), State: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.pam"), Testo: interfaccia.T("pr.riuscita"), State: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.porta"), Testo: interfaccia.T("pr.fallita"), State: interfaccia.MALE},
					{Etichetta: interfaccia.T("pr.k.steps", 8, 8), Testo: interfaccia.T("pr.riuscita"), State: interfaccia.OK},
					{Etichetta: interfaccia.T("pr.k.audio"), Testo: interfaccia.T("pr.primo"), State: interfaccia.DOPO},
				},
			}
			m.screen, m.step = sReady, pReady
		}},
		{"stopped", func(m *model) {
			m.fine = &interfaccia.BlockedView{Title: interfaccia.T("b.titolo.annullata"), Below: interfaccia.T("b.sotto.annullata"),
				Why: "The package manager could not install labwc: no repository of this machine provides it.",
				Code: "RX-PACCHETTI-005", Touched: true}
			m.screen, m.step, m.has_failed = sFine, pInstall, true
		}},
	}
}

// Testo: the previews one after the other, with the name on top.
func Testo(s []Screen) string {
	var b strings.Builder
	for _, x := range s {
		b.WriteString("── " + x.Nome + "\n" + x.Testo + "\n\n")
	}
	return b.String()
}
