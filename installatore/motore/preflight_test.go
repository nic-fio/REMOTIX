package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// una radice finta per il PREFLIGHT: i file che legge, e nessun comando (tutti «non c'è»).
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
			// quel che manca (§10.36): al desktop, e alla macchina intera
			if len(e.Mancano) > 0 {
				c = append(c, "RX-MANCA-003")
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

// Fedora 44 con NVIDIA proprietaria, SELinux, pam_faillock: ogni difetto noto col suo codice (R2).
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
			t.Errorf("%s = %q, atteso %q", k, p.V(k), v)
		}
	}
	// nessun driver VA (NVIDIA proprietaria) ⇒ la scheda non codifica, RILEVATO. Mai «sì»
	if f, _ := p.F("h264.gpu"); f.Stato != RILEVATO || f.Valore != "no" {
		t.Errorf("h264.scheda senza driver VA: %+v", f)
	}
	codici := map[string]bool{}
	for _, m := range p.Messaggi {
		codici[m.Codice] = true
	}
	// fase 19: niente ripiego — la sola NVIDIA proprietaria è un rifiuto (RX-GPU-004), già nel
	// controllo preliminare; RPM Fusion (RX-H264-003) non c'entra, non è una scheda Intel o AMD
	for _, c := range []string{"RX-GPU-002", "RX-GPU-004", "RX-PAM-002", "RX-SELINUX-001", "RX-GRUPPI-001", "RX-LOGIND-001"} {
		if !codici[c] {
			t.Errorf("manca %s fra %v", c, codici)
		}
	}
	for _, c := range []string{"RX-H264-003", "RX-H264-005", "RX-GPU-001"} {
		if codici[c] {
			t.Errorf("%s non c'entra più: %v", c, codici)
		}
	}
	// fase 19: le due strade attive, Vulkan prima; qui senza nessun ICD ⇒ la NVIDIA resta fuori
	if p.V("encoding.routes") != "vulkan,vaapi" || p.V("encoding.vulkan") != "active" || p.V("encoding.vulkan.icd") != "none" {
		t.Errorf("le strade: %q, vulkan %q, icd %q", p.V("encoding.routes"), p.V("encoding.vulkan"), p.V("encoding.vulkan.icd"))
	}
	rap := Valuta(catalogoProva(t), p)
	for _, d := range DESKTOP {
		if got := condizioniDi(rap, d); !strings.HasPrefix(got, "UNSUPPORTED RX-GPU-004") {
			t.Errorf("%s su Fedora 44 con la sola NVIDIA proprietaria: %s", d, got)
		}
	}
	// la stessa macchina con una Intel accanto (il portatile «ibrido»): passa, e la NVIDIA si dice
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
		t.Errorf("gnome su Fedora 44 con Intel e NVIDIA: %s", got)
	}
}

// Fase 19 (DECISIONI §10.27): senza una scheda capace REMOTIX non si installa, e il controllo
// preliminare lo dice prima di toccare, col codice del caso; con una scheda Intel o AMD capace passa.
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
		{"nessuna scheda (VM senza scheda)", con(nil), "RX-GPU-003"},
		{"NVIDIA col driver proprietario", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": ""}), "RX-GPU-004"},
		{"scheda virtuale (virtio)", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x1af4\n"}), "RX-GPU-005"},
		{"Intel", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x8086\n", "usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so": ""}), ""},
		{"AMD", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x1002\n", "usr/lib/x86_64-linux-gnu/dri/radeonsi_drv_video.so": ""}), ""},
		{"fornitore illeggibile: decide la prova vera (7a)", con(map[string]string{"sys/class/drm/renderD128/device/.x": ""}), ""},
	} {
		p := Preflight(&Ambiente{Radice: radiceFinta(t, c.file, nil), Esegui: nessunComando}, OpzioniPreflight{})
		var gpu []string
		for _, m := range p.Messaggi {
			if m.Codice != "RX-GPU-002" && strings.HasPrefix(m.Codice, "RX-GPU-") {
				gpu = append(gpu, m.Codice)
				if m.Gravita != BLOCCANTE || !strings.HasPrefix(m.Testo, "Missing") {
					t.Errorf("%s: %s non è BLOCKING o non dice che cosa manca: %+v", c.nome, m.Codice, m)
				}
			}
		}
		if strings.Join(gpu, ",") != c.codice {
			t.Errorf("%s: %v, atteso %q", c.nome, gpu, c.codice)
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

// Il catalogo: la matrice di §3, le derivate, le escluse, le condizioni di §11.1.
func TestCatalogo(t *testing.T) {
	cat := catalogoProva(t)
	casi := []struct {
		id, ver, desktop string
		extra            map[string]string
		atteso           string
	}{
		{"debian", "13", "gnome", nil, "COMPATIBLE "},
		{"ubuntu", "24.04", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"}, // D7 chiusa: fuori
		{"linuxmint", "22", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"},
		{"linuxmint", "23", "gnome", map[string]string{"package.gnome-session": "50.0"}, "COMPATIBLE "},
		// D8 (30 set): REMOTIX avvia la sessione GNOME di serie (su Ubuntu «ubuntu»): gnome-session non
		// è più un componente da aggiungere, e non compare nel piano
		{"ubuntu", "26.04", "gnome", map[string]string{"package.gnome-session": "absent"}, "COMPATIBLE "},
		{"debian", "12", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"},
		{"almalinux", "10.1", "xfce", nil, "UNSUPPORTED RX-COMPAT-005"},
		{"almalinux", "10.0", "gnome", nil, "UNSUPPORTED RX-COMPAT-001"}, // serve la 10.1 (OpenSSL 3.5)
		// EPEL serve a REMOTIX stesso su Alma: manca (§10.36), e lo mette l'amministratore
		{"almalinux", "10.1", "kde", map[string]string{"desktop.kde": "6.4", "repo.epel": "absent", "repo.rpmfusion": "present"}, "COMPATIBLE RX-MANCA-002"},
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "absent", "repo.rpmfusion": "present"}, "COMPATIBLE RX-MANCA-002"},
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "present", "repo.rpmfusion": "present"}, "COMPATIBLE "}, // niente più OpenH264 di Cisco
		{"rocky", "10.1", "gnome", map[string]string{"repo.epel": "present", "repo.rpmfusion": "present"}, "COMPATIBLE "},
		// fase 19: su Alma la sola AMD non codifica (Mesa senza VA-API) ⇒ fuori; accanto a una Intel, si dice
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "present", "gpu.renderD128.vendor": "AMD"}, "UNSUPPORTED RX-GPU-006"},
		{"almalinux", "10.1", "gnome", map[string]string{"repo.epel": "present", "repo.rpmfusion": "present", "repo.rpmfusion-nonfree": "present",
			"gpu.nodes": "renderD128,renderD129", "gpu.renderD129.vendor": "AMD", "h264.gpu": "no"}, "COMPATIBLE C-HARDWARE"},
		// Fedora con la Mesa ufficiale (senza H.264) su AMD: manca un driver che codifica, e il motore
		// non lo installa (§10.36)
		{"fedora", "44", "gnome", map[string]string{"gpu.renderD128.vendor": "AMD", "package.mesa-va-drivers": "26.2", "h264.gpu": "no"}, "UNSUPPORTED RX-GPU-006"},
		// fase 19: senza una scheda capace REMOTIX non si installa, su nessun desktop
		{"debian", "13", "gnome", map[string]string{"gpu.renderD128.vendor": "virtio"}, "UNSUPPORTED RX-GPU-005"},
		{"debian", "13", "gnome", map[string]string{"gpu.renderD128.vendor": "NVIDIA", "gpu.nvidia_proprietary": "yes"}, "UNSUPPORTED RX-GPU-004"},
		{"debian", "13", "gnome", map[string]string{"gpu.nodes": "none"}, "UNSUPPORTED RX-GPU-003"},
		{"gentoo", "2.17", "gnome", nil, "UNSUPPORTED RX-COMPAT-002"},
		{"opensuse-tumbleweed", "20260930", "kde", map[string]string{"desktop.kde": "6.7", "package.breeze6-wallpapers": "absent"}, "COMPATIBLE RX-MANCA-003"},
		{"opensuse-leap", "16.0", "lxqt", map[string]string{"desktop.lxqt": "2.1", "package.labwc": "0.8.1", "package.wlr-randr": "0.4", "fonts.scalable": "0"}, "COMPATIBLE C-LIMITE,RX-MANCA-003"},
		// fase 19: il deposito Cisco di OpenH264 non si chiede più
		{"opensuse-tumbleweed", "20260930", "gnome", nil, "COMPATIBLE "},
		// Leap 16 + Plasma (KWin 6.4) chiede il 3D (T6 seguiti, KDE 487217): condizione; senza scheda, no
		// (e, dalla fase 19, senza scheda REMOTIX non si installa su nessun desktop)
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
			t.Errorf("%s %s %s: %q, atteso %q (%s)", c.id, c.ver, c.desktop, got, c.atteso, rap.Riconosciuta)
		}
	}
	// nessuna combinazione è CERTIFICATA finché il catalogo non registra un giro intero (T10)
	for _, pl := range cat.Piattaforme {
		if pl.GiroIntero != "" {
			t.Errorf("%s: giro intero registrato senza T10", pl.Nome)
		}
	}
}

// ⛔ UNKNOWN non è PASS anche nel giudizio: un H.264 non provato è un'incognita scritta.
func TestIncognite(t *testing.T) {
	p := profiloFinto()
	p.Sconosciuto("h264.gpu", "ffmpeg non c'è")
	rap := Valuta(catalogoProva(t), p)
	if len(rap.Incognite) == 0 || !strings.Contains(strings.Join(rap.Incognite, " "), "H.264") {
		t.Fatalf("incognite: %v", rap.Incognite)
	}
}

// La tabella del manuale (§3.1) si genera dal catalogo.
func TestTabellaVersioni(t *testing.T) {
	tab := TabellaVersioni(catalogoProva(t))
	for _, x := range []string{"| Debian | **13** (Trixie)", "Rocky Linux", "Ubuntu 24.04", "| OpenSSL | 3.5 |", "labwc #2525"} {
		if !strings.Contains(tab, x) {
			t.Errorf("la tabella non contiene %q:\n%s", x, tab)
		}
	}
}

// Fase 19, la strada «vulkan» attiva (DECISIONI §10.27): la NVIDIA col driver proprietario e il suo
// ICD passa (il video lo codifica Vulkan Video); senza l'ICD resta RX-GPU-004; l'AMD con l'ICD di RADV
// passa anche senza nessun driver VA; l'ICD di llvmpipe (lvp) non è una scheda.
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
		{"NVIDIA proprietaria con l'ICD", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": "",
			"usr/share/vulkan/icd.d/nvidia_icd.json": "{}"}), "nvidia", "NVIDIA", ""},
		{"NVIDIA proprietaria senza l'ICD", con(nvidia), "none", "", "RX-GPU-004"},
		{"NVIDIA proprietaria con l'ICD di llvmpipe soltanto", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x10de\n", "sys/module/nvidia/x": "",
			"usr/share/vulkan/icd.d/lvp_icd.x86_64.json": "{}"}), "lvp", "", "RX-GPU-004"},
		{"AMD con RADV e nessun driver VA", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x1002\n",
			"usr/share/vulkan/icd.d/radeon_icd.x86_64.json": "{}", "etc/vulkan/icd.d/radeon_icd.x86_64.json": "{}"}), "radeon", "AMD", ""},
		{"Intel con ANV: in Vulkan non conta, VA-API sì", con(map[string]string{"sys/class/drm/renderD128/device/vendor": "0x8086\n",
			"usr/share/vulkan/icd.d/intel_icd.x86_64.json": "{}", "usr/lib/x86_64-linux-gnu/dri/iHD_drv_video.so": ""}), "intel", "", ""},
	} {
		p := Preflight(&Ambiente{Radice: radiceFinta(t, c.file, nil), Esegui: nessunComando}, OpzioniPreflight{})
		if p.V("encoding.vulkan.icd") != c.icd {
			t.Errorf("%s: icd %q, atteso %q", c.nome, p.V("encoding.vulkan.icd"), c.icd)
		}
		if got := strings.Join(schedeVulkan(nil, p), ","); got != c.schede {
			t.Errorf("%s: schede vulkan %q, atteso %q", c.nome, got, c.schede)
		}
		var gpu []string
		for _, m := range p.Messaggi {
			if m.Codice != "RX-GPU-002" && strings.HasPrefix(m.Codice, "RX-GPU-") {
				gpu = append(gpu, m.Codice)
			}
		}
		if strings.Join(gpu, ",") != c.codice {
			t.Errorf("%s: %v, atteso %q", c.nome, gpu, c.codice)
		}
		rap := Valuta(catalogoProva(t), p)
		got := condizioniDi(rap, "gnome")
		if c.codice != "" && !strings.HasPrefix(got, "UNSUPPORTED "+c.codice) {
			t.Errorf("%s: gnome %s", c.nome, got)
		}
		if c.codice == "" && (strings.HasPrefix(got, "UNSUPPORTED") || strings.Contains(got, "C-HARDWARE")) {
			t.Errorf("%s: gnome %s (con Vulkan la scheda non è fuori)", c.nome, got)
		}
	}
}
