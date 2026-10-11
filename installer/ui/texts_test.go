package ui

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"remotix/installer/engine"
)

// Every key used by the screens (view and TUI) is there, in both languages (DECISIONI §10.15, R42).
func TestInterfaceTexts(t *testing.T) {
	re := regexp.MustCompile(`\bT\("([a-z0-9_.]+)"`)
	var file []string
	for _, g := range []string{"*.go", "tui/*.go"} {
		m, _ := filepath.Glob(g)
		file = append(file, m...)
	}
	used_count := 0
	for _, f := range file {
		if strings.HasSuffix(f, "_test.go") {
			continue
		}
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		for _, m := range re.FindAllStringSubmatch(string(b), -1) {
			k := m[1]
			if strings.HasPrefix(k, "comp.") || strings.HasPrefix(k, "cli.") || strings.HasSuffix(k, ".") { // the engine's, or composed
				continue
			}
			used_count++
			x, ok := texts[k]
			if !ok {
				t.Errorf("%s: the key %q is missing", f, k)
				continue
			}
			if x == "" {
				t.Errorf("%q: empty text", k)
			}
		}
	}
	if used_count < 50 {
		t.Errorf("only %d keys found: does the expression not see them?", used_count)
	}
}

// The check in plain words: no names of drivers or buses outside the technical details; the
// labels in English (DECISIONI §10.35).
func TestCheckViewCommonWords(t *testing.T) {
	prof := engine.NewProfile(7447)
	for k, v := range map[string]string{"distro.id": "fedora", "distro.version": "44", "distro.name": "Fedora Linux 44 (Workstation Edition)",
		"distro.variant": "workstation", "gpu.nodes": "renderD128", "gpu.renderD128.vendor": "virtio",
		"gpu.renderD128.driver": "virtio-pci", "selinux": "enforcing"} {
		prof.Detected(k, v, "prova")
	}
	rap := &engine.Report{Recognized: engine.T("comp.nella_matrice", "Fedora 44"),
		Desktop: []engine.DesktopOutcome{{Desktop: "gnome", Installed: "50.5", Lvl: engine.COMPATIBLE}}}
	dom := &engine.Questions{Porta: 7447, Firewall: "firewalld"}
	for _, l := range []string{"en"} {
		v := NewCheckView(&CheckReport{ProfileV: prof, Report: rap, Questions: dom})
		if v.Outcome != CONDS {
			t.Errorf("%s: outcome %v, expected conditional", l, v.Outcome)
		}
		for _, r := range v.Righe {
			if strings.Contains(r.Testo, "virtio") || strings.Contains(r.Testo, "renderD") || strings.Contains(r.Testo, "RX-") {
				t.Errorf("%s: technical word outside the details: %q", l, r.Testo)
			}
		}
		if !strings.Contains(v.Dettagli, "virtio-pci") {
			t.Errorf("%s: the driver is not in the details: %q", l, v.Dettagli)
		}
		if v.Header != "Fedora Linux 44 · Workstation · GNOME 50" {
			t.Errorf("%s: header %q", l, v.Header)
		}
	}
	s := NewChoicesView(&CheckReport{ProfileV: prof, Report: rap, Questions: dom})
	if s.Titolo != T("sc.titolo.1") || s.PortGreen {
		t.Errorf("choices: %q, green port %v (with the firewall on, opening it is the administrator's job)", s.Titolo, s.PortGreen)
	}
	// what is missing stops everything, and is stated without suggesting how to provide it (§10.36)
	rap.Missing = []engine.Message{engine.Msg("RX-MANCA-003", "XFCE: labwc")}
	v := NewCheckView(&CheckReport{ProfileV: prof, Report: rap, Questions: dom})
	if v.Outcome != BLOCKED || v.Blocked == nil || !strings.Contains(v.Blocked.Why, "labwc") {
		t.Errorf("missing: outcome %v, %+v", v.Outcome, v.Blocked)
	}
}
