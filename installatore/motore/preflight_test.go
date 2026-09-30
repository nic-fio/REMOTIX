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
	for k, v := range map[string]string{"distro.famiglia": "fedora", "selinux": "enforcing", "scheda.nvidia_proprietaria": "si",
		"scheda.renderD128.driver": "nvidia", "pam.faillock": "si", "desktop.gnome": "presente", "gruppo.render": "assente",
		"logind.kill_user_processes": "yes", "sistema.systemd": "si"} {
		if p.V(k) != v {
			t.Errorf("%s = %q, atteso %q", k, p.V(k), v)
		}
	}
	// senza libavcodec: H.264 SCONOSCIUTO dichiarato, mai «sì»
	if f, _ := p.F("h264.scheda"); f.Stato != SCONOSCIUTO {
		t.Errorf("h264.scheda senza ffmpeg: %+v", f)
	}
	codici := map[string]bool{}
	for _, m := range p.Messaggi {
		codici[m.Codice] = true
	}
	for _, c := range []string{"RX-GPU-002", "RX-H264-001", "RX-PAM-002", "RX-SELINUX-001", "RX-GRUPPI-001", "RX-LOGIND-001"} {
		if !codici[c] {
			t.Errorf("manca %s fra %v", c, codici)
		}
	}
	rap := Valuta(catalogoProva(t), p)
	if got := condizioniDi(rap, "gnome"); got != "COMPATIBILE C-DEPOSITO,C-HARDWARE,C-RIPIEGO" {
		t.Errorf("gnome su Fedora 44 con NVIDIA: %s", got)
	}
	if got := condizioniDi(rap, "xfce"); !strings.Contains(got, "C-COMPONENTE") {
		t.Errorf("xfce senza labwc: %s", got)
	}
}

func profiloDi(id, ver string, extra map[string]string) *Profilo {
	p := profiloFinto()
	p.Rilevato("distro.id", id, "finto")
	p.Rilevato("distro.versione", ver, "finto")
	p.Rilevato("distro.famiglia", Famiglia(id, ""), "finto")
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
		{"debian", "13", "gnome", nil, "COMPATIBILE "},
		{"ubuntu", "24.04", "gnome", nil, "NON_SUPPORTATA RX-COMPAT-001"}, // D7 chiusa: fuori
		{"linuxmint", "22", "gnome", nil, "NON_SUPPORTATA RX-COMPAT-001"},
		{"linuxmint", "23", "gnome", map[string]string{"pacchetto.gnome-session": "50.0"}, "COMPATIBILE "},
		// D8 (30 set): REMOTIX avvia la sessione GNOME di serie (su Ubuntu «ubuntu»): gnome-session non
		// è più un componente da aggiungere, e non compare nel piano
		{"ubuntu", "26.04", "gnome", map[string]string{"pacchetto.gnome-session": "assente"}, "COMPATIBILE "},
		{"debian", "12", "gnome", nil, "NON_SUPPORTATA RX-COMPAT-001"},
		{"almalinux", "10.1", "xfce", nil, "NON_SUPPORTATA RX-COMPAT-005"},
		{"almalinux", "10.0", "gnome", nil, "NON_SUPPORTATA RX-COMPAT-001"}, // serve la 10.1 (OpenSSL 3.5)
		{"almalinux", "10.1", "kde", map[string]string{"desktop.kde": "6.4", "deposito.epel": "assente", "deposito.rpmfusion": "presente"}, "COMPATIBILE C-DEPOSITO"},
		{"rocky", "10.1", "gnome", map[string]string{"deposito.rpmfusion": "presente"}, "COMPATIBILE "},
		{"gentoo", "2.17", "gnome", nil, "NON_SUPPORTATA RX-COMPAT-002"},
		{"opensuse-tumbleweed", "20260930", "kde", map[string]string{"desktop.kde": "6.7", "deposito.packman": "presente", "pacchetto.breeze6-wallpapers": "assente"}, "COMPATIBILE C-COMPONENTE"},
		{"opensuse-leap", "16.0", "lxqt", map[string]string{"desktop.lxqt": "2.1", "deposito.packman": "presente", "pacchetto.labwc": "0.8.1", "pacchetto.wlr-randr": "0.4", "caratteri.scalabili": "0"}, "COMPATIBILE C-COMPONENTE,C-LIMITE"},
		// Leap 16 + Plasma (KWin 6.4) chiede il 3D (T6 seguiti, KDE 487217): condizione; senza scheda, no
		{"opensuse-leap", "16.0", "kde", map[string]string{"desktop.kde": "6.4", "deposito.packman": "presente"}, "COMPATIBILE C-HARDWARE"},
		{"opensuse-leap", "16.0", "kde", map[string]string{"desktop.kde": "6.4", "deposito.packman": "presente", "scheda.nodi": "nessuno"}, "NON_SUPPORTATA RX-COMPAT-007"},
		{"opensuse-tumbleweed", "20260930", "kde", map[string]string{"desktop.kde": "6.7", "deposito.packman": "presente", "scheda.nodi": "nessuno"}, "COMPATIBILE C-COMPONENTE"},
		{"debian", "13", "kde", map[string]string{"desktop.kde": "5.27"}, "NON_SUPPORTATA RX-COMPAT-006"},
		{"debian", "13", "gnome", map[string]string{"sistema.systemd": "no"}, "NON_SUPPORTATA RX-COMPAT-007"},
		{"debian", "13", "gnome", map[string]string{"distro.immutabile": "si"}, "NON_SUPPORTATA RX-COMPAT-003"},
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
	p.Sconosciuto("h264.scheda", "ffmpeg non c'è")
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
