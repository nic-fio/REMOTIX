package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// a fake root for the PREFLIGHT: the files it reads, and no command (all «not there»).
func radiceFinta(t *testing.T, file map[string]string, collegamenti map[string]string) string {
	r := t.TempDir()
	for p, c := range file {
		d := filepath.Join(r, p)
		os.MkdirAll(filepath.Dir(d), 0o755)
		if err := os.WriteFile(d, []byte(c), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	for p, dest := range collegamenti {
		d := filepath.Join(r, p)
		os.MkdirAll(filepath.Dir(d), 0o755)
		if err := os.Symlink(dest, d); err != nil {
			t.Fatal(err)
		}
	}
	return r
}

func condizioniDi(r *Rapporto, d string) string {
	for _, e := range r.Desktop {
		if e.Desktop == d {
			var c []string
			for _, k := range e.Condizioni {
				c = append(c, k.Codice)
			}
			for _, m := range e.Motivi {
				c = append(c, m.Codice)
			}
			// what is missing (§10.36): for the desktop, and for the whole machine
			if len(e.Mancano) > 0 {
				c = append(c, "RX-MANCA-003")
			}
			// the pieces the desktop requires: REMOTIX dependencies, the manager installs them
			if len(e.Dipende) > 0 {
				c = append(c, "DEP("+strings.Join(e.Dipende, ",")+")")
			}
			for _, m := range r.Mancano {
				if m.Codice != "RX-MANCA-003" && e.Livello != NON_SUPPORTATA {
					c = append(c, m.Codice)
				}
			}
			return e.Livello + " " + strings.Join(c, ",")
		}
	}
	return ""
}

// Fedora 44 with proprietary NVIDIA, SELinux, pam_faillock: every known defect with its code (R2).
func TestPreflightFedoraNvidia(t *testing.T) {
	r := radiceFinta(t, map[string]string{
		"etc/os-release":                           "ID=fedora\nVERSION_ID=44\nPRETTY_NAME=\"Fedora Linux 44 (Workstation Edition)\"\n",
		"sys/fs/selinux/enforce":                   "1",
		"sys/class/drm/renderD128/device/vendor":   "0x10de\n",
		"proc/driver/nvidia/version":               "NVRM version: 580\n",
		"etc/group":                                "video:x:39:\n",
		"etc/pam.d/password-auth":                  "auth required pam_faillock.so preauth\n",
		"etc/pam.d/postlogin":                      "",
		"etc/pam.d/system-auth":                    "",
		"usr/bin/gnome-shell":                      "",
		"run/systemd/system/.x":                    "",
		"usr/lib64/security/pam_systemd.so":        "",
		"etc/systemd/logind.conf.d/50-uccidi.conf": "[Login]\nKillUserProcesses=yes\n",
	}, map[string]string{"sys/class/drm/renderD128/device/driver": "../../../bus/pci/drivers/nvidia"})
	a := &Ambiente{Radice: r, Esegui: nessunComando}
	p := Preflight(a, OpzioniPreflight{})
	for k, v := range map[string]string{"distro.family": "fedora", "selinux": "enforcing", "gpu.nvidia_proprietary": "yes",
		"gpu.renderD128.driver": "nvidia", "pam.faillock": "yes", "desktop.gnome": "present", "group.render": "absent",
		"logind.kill_user_processes": "yes", "system.systemd": "yes"} {
		if p.V(k) != v {
			t.Errorf("%s = %q, expected %q", k, p.V(k), v)
		}
	}
	// no VA driver (proprietary NVIDIA) ⇒ the card does not encode, RILEVATO. Never «yes»
	if f, _ := p.F("h264.gpu"); f.Stato != RILEVATO || f.Valore != "no" {
		t.Errorf("h264.scheda without a VA driver: %+v", f)
	}
	codici := map[string]bool{}
	for _, m := range p.Messaggi {
		codici[m.Codice] = true
	}
	// phase 19: no fallback — a proprietary NVIDIA alone is a refusal (RX-GPU-004), already in the
	// preliminary check; RPM Fusion (RX-H264-003) does not matter, it is not an Intel or AMD card
	for _, c := range []string{"RX-GPU-002", "RX-GPU-004", "RX-PAM-002", "RX-SELINUX-001", "RX-GRUPPI-001", "RX-LOGIND-001"} {
		if !codici[c] {
			t.Errorf("%s missing among %v", c, codici)
		}
	}
	for _, c := range []string{"RX-H264-003", "RX-H264-005", "RX-GPU-001"} {
		if codici[c] {
			t.Errorf("%s no longer applies: %v", c, codici)
		}
	}
	// phase 19: the two active routes, Vulkan first; here without any ICD ⇒ the NVIDIA stays out
	if p.V("encoding.routes") != "vulkan,vaapi" || p.V("encoding.vulkan") != "active" || p.V("encoding.vulkan.icd") != "none" {
		t.Errorf("the routes: %q, vulkan %q, icd %q", p.V("encoding.routes"), p.V("encoding.vulkan"), p.V("encoding.vulkan.icd"))
	}
	rap := Valuta(catalogoProva(t), p)
	for _, d := range DESKTOP {
		if got := condizioniDi(rap, d); !strings.HasPrefix(got, "UNSUPPORTED RX-GPU-004") {
			t.Errorf("%s on Fedora 44 with only the proprietary NVIDIA: %s", d, got)
		}
	}
	// the same machine with an Intel next to it (the «hybrid» laptop): it passes, and the NVIDIA is stated
	r2 := radiceFinta(t, map[string]string{
		"etc/os-release":                         "ID=fedora\nVERSION_ID=44\n",
		"sys/class/drm/renderD128/device/vendor": "0x8086\n",
		"sys/class/drm/renderD129/device/vendor": "0x10de\n",
		"proc/driver/nvidia/version":             "NVRM version: 580\n",
		"run/systemd/system/.x":                  "",
		"usr/bin/gnome-shell":                    "",
	}, nil)
	p2 := Preflight(&Ambiente{Radice: r2, Esegui: nessunComando}, OpzioniPreflight{})
	for _, m := range p2.Messaggi {
		if strings.HasPrefix(m.Codice, "RX-GPU-00") && m.Codice != "RX-GPU-002" {
			t.Errorf("Intel + NVIDIA: %s", m.Codice)
		}
	}
	if got := condizioniDi(Valuta(catalogoProva(t), p2), "gnome"); got != "COMPATIBLE C-HARDWARE" {
		t.Errorf("gnome on Fedora 44 with Intel and NVIDIA: %s", got)
	}
}

// Phase 19 (DECISIONI §10.27): without a capable card REMOTIX is not installed, and the preliminary
// check says so before touching, with the case's code; with a capable Intel or AMD card it passes.
func TestPreflightSenzaSchedaCapace(t *testing.T) {
	base := map[string]string{"etc/os-release": "ID=debian\nVERSION_ID=13\n", "run/systemd/system/.x": "", "usr/bin/gnome-shell": ""}
	con := func(extra map[string]string) map[string]string {
		m := map[string]string{}
		for k, v := range base {
			m[k] = v
		}
		for k, v := range extra {
			m[k] = v
		}
		return m
	}
	for _, c := range []struct {
		nome   string
		file   map[string]string
		codice string
	}{
		{"no card (VM without a card)", con(nil), "RX-GPU-003"},
		{"NVIDIA with the proprietary driver", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": ""}), "RX-GPU-004"},
		{"virtual card (virtio)", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x1af4\n"}), "RX-GPU-005"},
		{"Intel", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x8086\n", "usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so": ""}), ""},
		{"AMD", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x1002\n", "usr/lib/x86_64-linux-gnu/dri/radeonsi_drv_video.so": ""}), ""},
		{"unreadable vendor: the real test decides (7a)", con(map[string]string{"sys/class/drm/renderD128/device/.x": ""}), ""},
	} {
		p := Preflight(&Ambiente{Radice: radiceFinta(t, c.file, nil), Esegui: nessunComando}, OpzioniPreflight{})
		var gpu []string
		for _, m := range p.Messaggi {
			if m.Codice != "RX-GPU-002" && strings.HasPrefix(m.Codice, "RX-GPU-") {
				gpu = append(gpu, m.Codice)
				if m.Gravita != BLOCCANTE || !strings.HasPrefix(m.Testo, "Missing") {
					t.Errorf("%s: %s is not BLOCKING or does not say what is missing: %+v", c.nome, m.Codice, m)
				}
			}
		}
		if strings.Join(gpu, ",") != c.codice {
			t.Errorf("%s: %v, expected %q", c.nome, gpu, c.codice)
		}
		rap := Valuta(catalogoProva(t), p)
		got := condizioniDi(rap, "gnome")
		if c.codice != "" && !strings.HasPrefix(got, "UNSUPPORTED "+c.codice) {
			t.Errorf("%s: gnome %s", c.nome, got)
		}
		if c.codice == "" && strings.HasPrefix(got, "UNSUPPORTED") {
			t.Errorf("%s: gnome %s", c.nome, got)
		}
	}
}

func profiloDi(id, ver string, extra map[string]string) *Profilo {
	p := profiloFinto()
	p.Rilevato("distro.id", id, "finto")
	p.Rilevato("distro.version", ver, "finto")
	p.Rilevato("distro.family", Famiglia(id, ""), "finto")
	for k, v := range extra {
		p.Rilevato(k, v, "finto")
	}
	return p
}

// The catalogue: the matrix of §3, the derivatives, the excluded ones, the conditions of §11.1.
func TestCatalogo(t *testing.T) {
	cat := catalogoProva(t)
	casi := []struct {
		id, ver, desktop string
		extra            map[string]string
		atteso           string
	}{
		{"debian", "13", "gnome", nil, "COMPATIBLE "},
		{"ubuntu", "24.04", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"}, // D7 closed: out
		{"linuxmint", "22", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"},
		{"linuxmint", "23", "gnome", map[string]string{"package.gnome-session": "50.0"}, "COMPATIBLE "},
		// D8 (30 Sep): REMOTIX starts the stock GNOME session (on Ubuntu «ubuntu»): gnome-session is no
		// longer a component to add, and does not appear in the plan
		{"ubuntu", "26.04", "gnome", map[string]string{"package.gnome-session": "absent"}, "COMPATIBLE "},
		{"debian", "12", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"},
		{"almalinux", "10.1", "xfce", nil, "UNSUPPORTED RX-COMPAT-005"},
		{"almalinux", "10.0", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"}, // 10.1 is needed (OpenSSL 3.5)
		// EPEL is needed by REMOTIX itself on Alma: missing (§10.36), and the administrator adds it
		{"almalinux", "10.1", "kde", map[string]string{"desktop.kde": "6.4", "repo.epel": "absent", "repo.rpmfusion": "present"}, "COMPATIBLE RX-MANCA-002"},
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "absent", "repo.rpmfusion": "present"}, "COMPATIBLE RX-MANCA-002"},
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "present", "repo.rpmfusion": "present"}, "COMPATIBLE "}, // no more Cisco OpenH264
		{"rocky", "10.1", "gnome", map[string]string{"repo.epel": "present", "repo.rpmfusion": "present"}, "COMPATIBLE "},
		// phase 19: on Alma an AMD alone does not encode (Mesa without VA-API) ⇒ out; next to an Intel, it is stated
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "present", "gpu.renderD128.vendor": "AMD"}, "UNSUPPORTED RX-GPU-006"},
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "present", "repo.rpmfusion": "present", "repo.rpmfusion-nonfree": "present",
			"gpu.nodes": "renderD128,renderD129", "gpu.renderD129.vendor": "AMD", "h264.gpu": "no"}, "COMPATIBLE C-HARDWARE"},
		// Fedora with the official Mesa (without H.264) on AMD: a driver that encodes is missing, and the engine
		// does not install it (§10.36)
		{"fedora", "44", "gnome", map[string]string{"gpu.renderD128.vendor": "AMD", "package.mesa-va-drivers": "26.2", "h264.gpu": "no"}, "UNSUPPORTED RX-GPU-006"},
		// phase 19: without a capable card REMOTIX is not installed, on any desktop
		{"debian", "13", "gnome", map[string]string{"gpu.renderD128.vendor": "virtio"}, "UNSUPPORTED RX-GPU-005"},
		{"debian", "13", "gnome", map[string]string{"gpu.renderD128.vendor": "NVIDIA", "gpu.nvidia_proprietary": "yes"}, "UNSUPPORTED RX-GPU-004"},
		{"debian", "13", "gnome", map[string]string{"gpu.nodes": "none"}, "UNSUPPORTED RX-GPU-003"},
		{"gentoo", "2.17", "gnome", nil, "UNSUPPORTED RX-COMPAT-002"},
		{"opensuse-tumbleweed", "20260930", "kde", map[string]string{"desktop.kde": "6.7", "package.breeze6-wallpapers": "absent"}, "COMPATIBLE DEP(breeze6-wallpapers)"},
		{"opensuse-leap", "16.0", "lxqt", map[string]string{"desktop.lxqt": "2.1", "package.labwc": "0.8.1", "package.wlr-randr": "0.4", "fonts.scalable": "0"}, "COMPATIBLE C-LIMITE,DEP(google-droid-fonts)"},
		// phase 19: Cisco's OpenH264 repository is no longer requested
		{"opensuse-tumbleweed", "20260930", "gnome", nil, "COMPATIBLE "},
		// Leap 16 + Plasma (KWin 6.4) requires 3D (T6 follow-ups, KDE 487217): a condition; without a card, no
		// (and, since phase 19, without a card REMOTIX is not installed on any desktop)
		{"opensuse-leap", "16.0", "kde", map[string]string{"desktop.kde": "6.4"}, "COMPATIBLE C-HARDWARE"},
		{"opensuse-leap", "16.0", "kde", map[string]string{"desktop.kde": "6.4", "gpu.nodes": "none"}, "UNSUPPORTED RX-GPU-003,RX-COMPAT-007"},
		{"opensuse-tumbleweed", "20260930", "kde", map[string]string{"desktop.kde": "6.7", "gpu.nodes": "none"}, "UNSUPPORTED RX-GPU-003"},
		{"debian", "13", "kde", map[string]string{"desktop.kde": "5.27"}, "UNSUPPORTED RX-COMPAT-006"},
		{"debian", "13", "gnome", map[string]string{"system.systemd": "no"}, "UNSUPPORTED RX-COMPAT-007"},
		{"debian", "13", "gnome", map[string]string{"distro.immutable": "yes"}, "UNSUPPORTED RX-COMPAT-003"},
	}
	for _, c := range casi {
		rap := Valuta(cat, profiloDi(c.id, c.ver, c.extra))
		if got := condizioniDi(rap, c.desktop); got != c.atteso {
			t.Errorf("%s %s %s: %q, expected %q (%s)", c.id, c.ver, c.desktop, got, c.atteso, rap.Riconosciuta)
		}
	}
	// no combination is CERTIFIED until the catalogue records a full run (T10)
	for _, pl := range cat.Piattaforme {
		if pl.GiroIntero != "" {
			t.Errorf("%s: full run recorded without T10", pl.Nome)
		}
	}
}

// ⛔ UNKNOWN is not PASS in the judgement either: an untested H.264 is a written unknown.
func TestIncognite(t *testing.T) {
	p := profiloFinto()
	p.Sconosciuto("h264.gpu", "ffmpeg is not there")
	rap := Valuta(catalogoProva(t), p)
	if len(rap.Incognite) == 0 || !strings.Contains(strings.Join(rap.Incognite, " "), "H.264") {
		t.Fatalf("unknowns: %v", rap.Incognite)
	}
}

// The manual's table (§3.1) is generated from the catalogue.
func TestTabellaVersioni(t *testing.T) {
	tab := TabellaVersioni(catalogoProva(t))
	for _, x := range []string{"| Debian | **13** (Trixie)", "Rocky Linux", "Ubuntu 24.04", "| OpenSSL | 3.5 |", "labwc #2525"} {
		if !strings.Contains(tab, x) {
			t.Errorf("the table does not contain %q:\n%s", x, tab)
		}
	}
}

// Phase 19, the «vulkan» route active (DECISIONI §10.27): the NVIDIA with the proprietary driver and its
// ICD passes (Vulkan Video encodes the video); without the ICD it stays RX-GPU-004; the AMD with RADV's ICD
// passes even without any VA driver; llvmpipe's ICD (lvp) is not a card.
func TestStradaVulkan(t *testing.T) {
	base := map[string]string{"etc/os-release": "ID=debian\nVERSION_ID=13\n", "run/systemd/system/.x": "", "usr/bin/gnome-shell": ""}
	con := func(extra map[string]string) map[string]string {
		m := map[string]string{}
		for k, v := range base {
			m[k] = v
		}
		for k, v := range extra {
			m[k] = v
		}
		return m
	}
	nvidia := map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": ""}
	for _, c := range []struct {
		nome   string
		file   map[string]string
		icd    string
		schede string
		codice string
	}{
		{"proprietary NVIDIA with the ICD", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": "",
			"usr/share/vulkan/icd.d/nvidia_icd.json": "{}"}), "nvidia", "NVIDIA", ""},
		{"proprietary NVIDIA without the ICD", con(nvidia), "none", "", "RX-GPU-004"},
		{"proprietary NVIDIA with only llvmpipe's ICD", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": "",
			"usr/share/vulkan/icd.d/lvp_icd.x86_64.json": "{}"}), "lvp", "", "RX-GPU-004"},
		{"AMD with RADV and no VA driver", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x1002\n",
			"usr/share/vulkan/icd.d/radeon_icd.x86_64.json": "{}", "etc/vulkan/icd.d/radeon_icd.x86_64.json": "{}"}), "radeon", "AMD", ""},
		{"Intel with ANV: it does not count in Vulkan, VA-API does", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x8086\n",
			"usr/share/vulkan/icd.d/intel_icd.x86_64.json": "{}", "usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so": ""}), "intel", "", ""},
	} {
		p := Preflight(&Ambiente{Radice: radiceFinta(t, c.file, nil), Esegui: nessunComando}, OpzioniPreflight{})
		if p.V("encoding.vulkan.icd") != c.icd {
			t.Errorf("%s: icd %q, expected %q", c.nome, p.V("encoding.vulkan.icd"), c.icd)
		}
		if got := strings.Join(schedeVulkan(nil, p), ","); got != c.schede {
			t.Errorf("%s: vulkan cards %q, expected %q", c.nome, got, c.schede)
		}
		var gpu []string
		for _, m := range p.Messaggi {
			if m.Codice != "RX-GPU-002" && strings.HasPrefix(m.Codice, "RX-GPU-") {
				gpu = append(gpu, m.Codice)
			}
		}
		if strings.Join(gpu, ",") != c.codice {
			t.Errorf("%s: %v, expected %q", c.nome, gpu, c.codice)
		}
		rap := Valuta(catalogoProva(t), p)
		got := condizioniDi(rap, "gnome")
		if c.codice != "" && !strings.HasPrefix(got, "UNSUPPORTED "+c.codice) {
			t.Errorf("%s: gnome %s", c.nome, got)
		}
		if c.codice == "" && (strings.HasPrefix(got, "UNSUPPORTED") || strings.Contains(got, "C-HARDWARE")) {
			t.Errorf("%s: gnome %s (with Vulkan the card is not out)", c.nome, got)
		}
	}
}
