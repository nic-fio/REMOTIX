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
	Name, Text string
}

// Previews: the screens at a given width and height (alt_h 0 = as tall as needed, without
// scrolling).
func Previews(wid, alt_h int, colors bool) []Screen {
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
		m.wid, m.alt_h = wid, alt_h
		if alt_h == 0 {
			body_el, _ := m.content()
			m.alt_h = len(body_el) + 6
			if m.alt_h < minHeight {
				m.alt_h = minHeight
			}
		}
		out = append(out, Screen{s.label_name, m.View()})
	}
	return out
}

type example struct {
	label_name string
	prepare    func(m *model)
}

func vcExample() *interfaccia.CheckView {
	return &interfaccia.CheckView{
		Header:  "Debian GNU/Linux 13 · GNOME 48",
		Outcome: interfaccia.CONDITIONS,
		Banner:  interfaccia.T("c.cond1.heading"),
		Below:   interfaccia.T("c.cond.firewall", 7447),
		Lines: []interfaccia.Line{
			{Label: "System", Text: "Debian 13 · certified", State: interfaccia.OK},
			{Label: "Desktop", Text: "GNOME · Wayland", State: interfaccia.OK},
			{Label: "Graphics card", Text: "Intel card · encodes video", State: interfaccia.OK},
			{Label: "Video", Text: interfaccia.T("t.video.ok"), State: interfaccia.AFTER},
			{Label: "Sign-in", Text: interfaccia.T("t.access.ok"), State: interfaccia.OK},
			{Label: "Users", Text: interfaccia.T("t.people", 3), State: interfaccia.OK},
			{Label: "Firewall", Text: interfaccia.T("t.fw.admin", "firewalld", 7447), State: interfaccia.WARNING},
			{Label: "Port", Text: interfaccia.T("t.port.free_fn", 7447), State: interfaccia.OK},
			{Label: "Permissions", Text: interfaccia.T("t.permessi.n", 3), State: interfaccia.FIX},
			{Label: "Audio", Text: interfaccia.T("t.audio"), State: interfaccia.AFTER},
		},
		Details: "Debian GNU/Linux 13 (trixie) · renderD128 Intel i915 · encoding.routes=vaapi · catalog 2026.10.10.14",
	}
}

func vpExample() *interfaccia.VistaPiano {
	return &interfaccia.VistaPiano{
		Steps: []interfaccia.Step{
			{Kind: "packages", Title: interfaccia.T("a.packets"), Brief: interfaccia.T("a.packets.b"), Rev: interfaccia.CONSENT},
			{Kind: "groups", Brief: interfaccia.T("a.group_list.b", "alice, bob and carol", "render, video"), Rev: interfaccia.OK},
			{Kind: "service", Brief: interfaccia.T("a.service.b"), Rev: interfaccia.OK},
		},
		Packets: []motore.Artifact{
			{Name: "remotix", Version: "1.0-1", Origin: "file", Outcome: "new"},
			{Name: "libei1", Version: "1.3.0-1", Origin: "debian/trixie", Outcome: "new"},
			{Name: "pipewire-bin", Version: "1.4.2-1", Origin: "debian/trixie", Outcome: "new"},
			{Name: "labwc", Version: "0.8.3-1", Origin: "debian/trixie", Outcome: "new"},
			{Name: "libva2", Version: "2.22.0-3", Origin: "debian/trixie", Outcome: "present"},
		},
		Dependencies: map[string]string{"labwc": "XFCE"},
		Users:        []string{"alice", "bob", "carol"},
		Groups:       []string{"render", "video"},
		Port:         "7447",
		Details:      "packages (install-packages, best-effort) · group-alice-render (add-user-to-group, exact) · plan 20261010-0912",
	}
}

func examples() []example {
	return []example{
		{"check", func(m *model) { m.vc, m.display_screen, m.step = vcExample(), sCheck, pCheck }},
		{"check-missing", func(m *model) {
			vc := vcExample()
			vc.Header = "Fedora Linux 44 · KDE Plasma 6"
			vc.Outcome, vc.Banner, vc.Below = interfaccia.BLOCKED, interfaccia.T("c.missing.heading"), interfaccia.T("c.missing.body_text")
			vc.Lines[0].Text = "Fedora 44 · compatible, not certified"
			vc.Lines[1].Text = "KDE Plasma · Wayland"
			vc.Lines[2] = interfaccia.Line{Label: "Graphics card", Text: interfaccia.T("m.RX-GPU-006"), State: interfaccia.MISSING}
			vc.Codes = []string{"RX-GPU-006"}
			m.vc, m.display_screen, m.step, m.has_failed = vc, sCheck, pCheck, true
		}},
		{"plan", func(m *model) {
			m.vc, m.vp, m.display_screen, m.step, m.port = vcExample(), vpExample(), sPiano, pPlan, "7447"
		}},
		{"install", func(m *model) {
			m.vc, m.vp = vcExample(), vpExample()
			m.av = interfaccia.NewProgress(m.vp)
			for i := range m.av.Lines {
				switch {
				case i < 2:
					m.av.Lines[i].State = interfaccia.DONE
				case i == 2:
					m.av.Lines[i].State = interfaccia.IN_PROGRESS
				}
			}
			m.display_screen, m.step = sProgress, pInstall
		}},
		{"ready", func(m *model) {
			m.vc = vcExample()
			m.ready = &interfaccia.ReadyView{
				Address:     "https://192.168.0.2:7447/",
				Fingerprint: "4F:1A:9C:2B:…:E2:07",
				Router:      interfaccia.T("pr.router", 7447, "192.168.0.2"),
				Todo:        []string{interfaccia.T("pr.todo.is_closed", 7447, "firewalld, zone public")},
				Prove: []interfaccia.Line{
					{Label: interfaccia.T("pr.k.service"), Text: interfaccia.T("pr.succeeded"), State: interfaccia.OK},
					{Label: interfaccia.T("pr.k.h264"), Text: interfaccia.T("pr.succeeded"), State: interfaccia.OK},
					{Label: interfaccia.T("pr.k.pam"), Text: interfaccia.T("pr.succeeded"), State: interfaccia.OK},
					{Label: interfaccia.T("pr.k.port"), Text: interfaccia.T("pr.failed"), State: interfaccia.MALE},
					{Label: interfaccia.T("pr.k.steps", 8, 8), Text: interfaccia.T("pr.succeeded"), State: interfaccia.OK},
					{Label: interfaccia.T("pr.k.audio"), Text: interfaccia.T("pr.first"), State: interfaccia.AFTER},
				},
			}
			m.display_screen, m.step = sReady, pReady
		}},
		{"stopped", func(m *model) {
			m.fine = &interfaccia.BlockedView{Title: interfaccia.T("b.heading.annullata"), Below: interfaccia.T("b.below.annullata"),
				Why:  "The package manager could not install labwc: no repository of this machine provides it.",
				Code: "RX-PACCHETTI-005", Touched: true}
			m.display_screen, m.step, m.has_failed = sFine, pInstall, true
		}},
	}
}

// Text: the previews one after the other, with the name on top.
func Text(s []Screen) string {
	var b strings.Builder
	for _, x := range s {
		b.WriteString("── " + x.Name + "\n" + x.Text + "\n\n")
	}
	return b.String()
}
