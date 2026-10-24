package tui

import (
	"io"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/muesli/termenv"

	"remotix/installer/engine"
	"remotix/installer/ui"
)

// The previews: every screen drawn with sample data (the same as the approved mockup,
// design/tui-mockup/index.html), to compare it with the mockup and for the frame tests.
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

func vcExample() *ui.CheckView {
	return &ui.CheckView{
		Header:  "Debian GNU/Linux 13 · GNOME 48",
		Outcome: ui.CONDS,
		Banner:  ui.T("c.cond1.titolo"),
		Below:   ui.T("c.cond.firewall", 7447),
		Righe: []ui.Line{
			{Etichetta: "System", Testo: "Debian 13 · certified", State: ui.OK},
			{Etichetta: "Desktop", Testo: "GNOME · Wayland", State: ui.OK},
			{Etichetta: "Graphics card", Testo: "Intel card · encodes video", State: ui.OK},
			{Etichetta: "Video", Testo: ui.T("t.video.ok"), State: ui.DOPO},
			{Etichetta: "Sign-in", Testo: ui.T("t.accesso.ok"), State: ui.OK},
			{Etichetta: "Users", Testo: ui.T("t.persone", 3), State: ui.OK},
			{Etichetta: "Firewall", Testo: ui.T("t.fw.admin", "firewalld", 7447), State: ui.WARNING},
			{Etichetta: "Port", Testo: ui.T("t.porta.libera", 7447), State: ui.OK},
			{Etichetta: "Permissions", Testo: ui.T("t.permessi.n", 3), State: ui.FIX},
			{Etichetta: "Audio", Testo: ui.T("t.audio"), State: ui.DOPO},
		},
		Dettagli: "Debian GNU/Linux 13 (trixie) · renderD128 Intel i915 · encoding.routes=vaapi · catalog 2026.10.10.14",
	}
}

func vpExample() *ui.VistaPiano {
	return &ui.VistaPiano{
		Steps: []ui.Stride{
			{Type: "packages", Titolo: ui.T("a.pacchetti"), Breve: ui.T("a.pacchetti.b"), Rev: ui.CONSENT},
			{Type: "groups", Breve: ui.T("a.gruppi.b", "alice, bob and carol", "render"), Rev: ui.OK},
			{Type: "service", Breve: ui.T("a.servizio.b"), Rev: ui.OK},
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
		Gruppi:     []string{"render"},
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
			vc.Outcome, vc.Banner, vc.Below = ui.BLOCKED, ui.T("c.manca.titolo"), ui.T("c.manca.testo")
			vc.Righe[0].Testo = "Fedora 44 · compatible, not certified"
			vc.Righe[1].Testo = "KDE Plasma · Wayland"
			vc.Righe[2] = ui.Line{Etichetta: "Graphics card", Testo: ui.T("m.RX-GPU-006"), State: ui.MISSING}
			vc.Codes = []string{"RX-GPU-006"}
			m.vc, m.screen, m.step, m.has_failed = vc, sCheck, pCheck, true
		}},
		{"plan", func(m *model) {
			m.vc, m.vp, m.screen, m.step, m.port = vcExample(), vpExample(), sPiano, pPlan, "7447"
		}},
		{"install", func(m *model) {
			m.vc, m.vp = vcExample(), vpExample()
			m.av = ui.NewProgress(m.vp)
			for i := range m.av.Righe {
				switch {
				case i < 2:
					m.av.Righe[i].State = ui.DONE
				case i == 2:
					m.av.Righe[i].State = ui.IN_PROGRESS
				}
			}
			m.screen, m.step = sProgress, pInstall
		}},
		{"ready", func(m *model) {
			m.vc = vcExample()
			m.ready = &ui.ReadyView{
				Address:     "https://192.168.0.2:7447/",
				Fingerprint: "4F:1A:9C:2B:…:E2:07",
				Router:      ui.T("pr.router", 7447, "192.168.0.2"),
				DaFare:      []string{ui.T("pr.todo.chiusa", 7447, "firewalld, zone public")},
				Prove: []ui.Line{
					{Etichetta: ui.T("pr.k.servizio"), Testo: ui.T("pr.riuscita"), State: ui.OK},
					{Etichetta: ui.T("pr.k.h264"), Testo: ui.T("pr.riuscita"), State: ui.OK},
					{Etichetta: ui.T("pr.k.pam"), Testo: ui.T("pr.riuscita"), State: ui.OK},
					{Etichetta: ui.T("pr.k.porta"), Testo: ui.T("pr.fallita"), State: ui.MALE},
					{Etichetta: ui.T("pr.k.steps", 8, 8), Testo: ui.T("pr.riuscita"), State: ui.OK},
					{Etichetta: ui.T("pr.k.audio"), Testo: ui.T("pr.primo"), State: ui.DOPO},
				},
			}
			m.screen, m.step = sReady, pReady
		}},
		{"stopped", func(m *model) {
			m.fine = &ui.BlockedView{Title: ui.T("b.titolo.annullata"), Below: ui.T("b.sotto.annullata"),
				Why:  "The package manager could not install labwc: no repository of this machine provides it.",
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
