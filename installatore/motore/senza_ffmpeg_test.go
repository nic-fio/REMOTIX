package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Fase 18 (senza ffmpeg): il deposito dei DRIVER dipende dal fornitore della scheda — `[M]` 30 set,
// dai binari dei driver: Fedora toglie H.264 da Intel e da Mesa (RPM Fusion per tutti e due, Intel nel
// ramo nonfree), openSUSE solo da Mesa (Packman solo con AMD), Alma su AMD non ha VA-API.
func TestDepositoPerFornitore(t *testing.T) {
	cat := catalogoProva(t)
	scheda := func(forn ...string) map[string]string {
		m := map[string]string{"scheda.nodi": "renderD128", "scheda.renderD128.fornitore": ""}
		for i, f := range forn {
			n := "renderD12" + string(rune('8'+i))
			m["scheda."+n+".fornitore"] = f
		}
		return m
	}
	casi := []struct {
		id, ver  string
		extra    map[string]string
		deposito string
		pacchi   string
		nonfree  bool
	}{
		{"fedora", "44", scheda("Intel"), "rpmfusion", "intel-media-driver", true},
		{"fedora", "44", scheda("AMD"), "rpmfusion", "mesa-va-drivers-freeworld", false},
		{"fedora", "44", scheda("Intel", "AMD"), "rpmfusion", "mesa-va-drivers-freeworld,intel-media-driver", true},
		{"fedora", "44", scheda("NVIDIA"), "", "", false},
		{"fedora", "44", map[string]string{"scheda.nodi": "nessuno", "scheda.renderD128.fornitore": ""}, "", "", false},
		{"opensuse-tumbleweed", "20260930", scheda("Intel"), "", "", false},
		{"opensuse-tumbleweed", "20260930", scheda("AMD"), "packman", "Mesa-dri,Mesa-libva", false},
		{"opensuse-leap", "16.0", scheda("AMD"), "packman", "Mesa-dri,Mesa-libva", false},
		{"almalinux", "10.1", scheda("Intel"), "rpmfusion", "intel-media-driver", true},
		{"almalinux", "10.1", scheda("AMD"), "", "", false},
		{"debian", "13", scheda("AMD"), "", "", false},
		{"arch", "rolling", scheda("Intel"), "", "", false},
	}
	for _, c := range casi {
		p := profiloDi(c.id, c.ver, c.extra)
		rap := Valuta(cat, p)
		if rap.pl == nil {
			t.Fatalf("%s %s: piattaforma sconosciuta", c.id, c.ver)
		}
		d, pk, nf := rap.pl.H264.PerLaScheda(p)
		if d != c.deposito || strings.Join(pk, ",") != c.pacchi || nf != c.nonfree {
			t.Errorf("%s %v: %q %v %v, attesi %q %q %v", c.id, c.extra, d, pk, nf, c.deposito, c.pacchi, c.nonfree)
		}
	}
	// RPM Fusion «free» c'è ma il ramo nonfree no: con Intel si chiede lo stesso
	p := profiloDi("fedora", "44", map[string]string{"deposito.rpmfusion": "presente", "deposito.openh264": "presente"})
	rap := Valuta(cat, p)
	if got := DepositiDaChiedere(rap, p, ""); strings.Join(got, ",") != "rpmfusion" {
		t.Errorf("fedora Intel senza nonfree: %v", got)
	}
	p.Rilevato("deposito.rpmfusion-nonfree", "presente", "finto")
	if got := DepositiDaChiedere(rap, p, ""); len(got) != 0 {
		t.Errorf("fedora Intel con free e nonfree: %v", got)
	}
	// Alma: EPEL e OpenH264 di Cisco servono a REMOTIX stesso, prima dei driver
	a := profiloDi("almalinux", "10.1", nil)
	if got := DepositiDaChiedere(Valuta(cat, a), a, ""); strings.Join(got, ",") != "epel,openh264,rpmfusion" {
		t.Errorf("alma Intel: %v", got)
	}
}

// Il piano: il deposito col ramo nonfree per Intel, i driver da lì, OpenH264 vero per nome nella
// transazione di REMOTIX quando la macchina non l'ha; un «no» a un deposito che serve ⇒ RX-H264-006.
func TestPianoSenzaFfmpeg(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	os.WriteFile(filepath.Join(radice, "remotix.rpm"), []byte("pacchetto finto"), 0o644)
	amb := ambienteFinto(radice)
	// «rpm -q» (i pezzi del deposito, per l'impronta): niente installato
	amb.Esegui = func(_ time.Duration, nome string, _ ...string) (string, int, error) { return "", 1, nil }
	cat := catalogoProva(t)
	fed := profiloDi("fedora", "44", map[string]string{"deposito.openh264": "presente", "h264.software": "no"})
	fed.Verificato("h264.scheda", "no", "finto")
	rap := Valuta(cat, fed)
	p, err := PianoInstallazione(fed, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.rpm", Porta: 7447, Depositi: []string{"rpmfusion"}})
	if err != nil {
		t.Fatal(err)
	}
	var dep, codec, pacchi *AzionePiano
	for i := range p.Azioni {
		switch a := &p.Azioni[i]; a.ID {
		case "deposito-rpmfusion":
			dep = a
		case "codec":
			codec = a
		case "pacchetti":
			pacchi = a
		}
	}
	if dep == nil || dep.Parametri["nonfree"] != "si" {
		t.Errorf("il deposito RPM Fusion col ramo nonfree: %+v", dep)
	}
	if codec == nil || codec.Parametri["nomi"] != "intel-media-driver" || codec.Parametri["da"] != "rpmfusion" {
		t.Errorf("i driver da RPM Fusion: %+v", codec)
	}
	if pacchi == nil || pacchi.Parametri["nomi"] != "openh264" {
		t.Errorf("OpenH264 vero nella transazione di REMOTIX: %+v", pacchi)
	}
	for _, m := range p.NonFatto {
		if m.Codice == "RX-H264-006" {
			t.Errorf("col consenso non si blocca: %+v", m)
		}
	}
	// OpenH264 c'è già (vero): non si chiede per nome
	fed.Rilevato("h264.software", "si", "finto")
	p, err = PianoInstallazione(fed, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.rpm", Porta: 7447, Depositi: []string{"rpmfusion"}})
	if err != nil {
		t.Fatal(err)
	}
	for _, a := range p.Azioni {
		if a.ID == "pacchetti" && a.Parametri["nomi"] != "" {
			t.Errorf("OpenH264 c'è: %+v", a)
		}
	}
	// Alma senza il consenso a OpenH264 di Cisco: BLOCCATA (D5)
	alma := profiloDi("almalinux", "10.1", map[string]string{"deposito.epel": "presente"})
	p, err = PianoInstallazione(alma, Valuta(cat, alma), cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.rpm", Porta: 7447})
	if err != nil {
		t.Fatal(err)
	}
	bl := ""
	for _, m := range p.NonFatto {
		if m.Codice == "RX-H264-006" {
			bl += m.Dettaglio + ";"
		}
	}
	if !strings.Contains(bl, "OpenH264") {
		t.Errorf("alma senza OpenH264 di Cisco: %q", bl)
	}
}

// Il preflight: i driver di RPM Fusion nelle loro cartelle, la famiglia del driver dal pacchetto, e
// OpenH264 vero distinto dalla copia vuota (noopenh264: 11-14 KB contro più di 1 MB, `[M]` 30 set).
func TestPreflightSenzaFfmpeg(t *testing.T) {
	grande := strings.Repeat("x", 1200*1024)
	casi := []struct {
		nome     string
		file     map[string]string
		fatti    map[string]string
		scheda   string
		software string
	}{
		{"fedora Intel col driver ridotto, OpenH264 vero",
			map[string]string{"usr/lib64/dri/iHD_drv_video.so": "", "usr/lib64/libopenh264.so.2.6.0": grande},
			map[string]string{"distro.famiglia": "fedora", "pacchetto.libva-intel-media-driver": "26.2.4-1.fc44"}, "no", "si"},
		{"fedora Intel col driver di RPM Fusion (dri-nonfree), la copia vuota",
			map[string]string{"usr/lib64/dri/iHD_drv_video.so": "", "usr/lib64/dri-nonfree/iHD_drv_video.so": "", "usr/lib64/libopenh264.so.2.6.0": "vuota"},
			map[string]string{"distro.famiglia": "fedora", "pacchetto.libva-intel-media-driver": "26.2.4-1.fc44", "pacchetto.intel-media-driver": "26.1.5-1.fc44"}, "", "no"},
		{"openSUSE AMD con la Mesa ufficiale",
			map[string]string{"usr/lib64/dri/radeonsi_drv_video.so": ""},
			map[string]string{"distro.famiglia": "suse", "scheda.renderD128.fornitore": "AMD", "pacchetto.Mesa-dri": "26.2.3-1.1"}, "no", "no"},
		{"openSUSE AMD con la Mesa di Packman",
			map[string]string{"usr/lib64/dri/radeonsi_drv_video.so": ""},
			map[string]string{"distro.famiglia": "suse", "scheda.renderD128.fornitore": "AMD", "pacchetto.Mesa-dri": "26.2.3-1699.2.pm.1"}, "", "no"},
	}
	for _, c := range casi {
		a := &Ambiente{Radice: radiceFinta(t, c.file, nil), Esegui: nessunComando}
		p := NuovoProfilo(7447)
		p.Rilevato("scheda.renderD128.fornitore", "Intel", "finto")
		for k, v := range c.fatti {
			p.Rilevato(k, v, "finto")
		}
		h264(a, p, c.fatti["distro.famiglia"])
		f, _ := p.F("h264.scheda")
		if c.scheda == "" && f.Stato != SCONOSCIUTO || c.scheda != "" && (f.Stato != RILEVATO || f.Valore != c.scheda) {
			t.Errorf("%s: h264.scheda %+v, atteso %q", c.nome, f, c.scheda)
		}
		if p.V("h264.software") != c.software {
			t.Errorf("%s: h264.software %q, atteso %q", c.nome, p.V("h264.software"), c.software)
		}
	}
}

// I depositi della fase 18 nel preflight: il ramo nonfree VERO di RPM Fusion (non steam né
// nvidia-driver) e OpenH264 di Cisco su Fedora, Alma e openSUSE.
func TestDepositiSenzaFfmpeg(t *testing.T) {
	steam := "[rpmfusion-nonfree-steam]\nname=steam\nbaseurl=https://x\nenabled=1\n"
	for _, c := range []struct {
		file           map[string]string
		nonfree, cisco string
	}{
		{map[string]string{"etc/yum.repos.d/steam.repo": steam}, "assente", "assente"},
		{map[string]string{"etc/yum.repos.d/rpmfusion-nonfree.repo": "[rpmfusion-nonfree]\nmetalink=x\nenabled=1\n"}, "presente", "assente"},
		{map[string]string{"etc/yum.repos.d/fedora-cisco-openh264.repo": "[fedora-cisco-openh264]\nenabled=1\n[fedora-cisco-openh264-debuginfo]\nenabled=0\n"}, "assente", "presente"},
		{map[string]string{"etc/yum.repos.d/fedora-cisco-openh264.repo": "[fedora-cisco-openh264]\nenabled=0\n"}, "assente", "assente"},
		{map[string]string{"etc/yum.repos.d/epel-cisco-openh264.repo": ContenutoCiscoEpel("10")}, "assente", "presente"},
		{map[string]string{"etc/zypp/repos.d/openSUSE:repo-openh264.repo": "[openSUSE:repo-openh264]\nenabled=1\nbaseurl=https://codecs.opensuse.org/openh264/openSUSE_Leap_16\n"}, "assente", "presente"},
	} {
		p := NuovoProfilo(7447)
		depositi(&Ambiente{Radice: radiceFinta(t, c.file, nil)}, p)
		if p.V("deposito.rpmfusion-nonfree") != c.nonfree || p.V("deposito.openh264") != c.cisco {
			t.Errorf("%v: nonfree %q, openh264 %q; attesi %q %q", c.file, p.V("deposito.rpmfusion-nonfree"), p.V("deposito.openh264"), c.nonfree, c.cisco)
		}
		if strings.Contains(strings.Join(mapKeys(c.file), ""), "epel-cisco") && p.V("deposito.epel") == "presente" {
			t.Errorf("il deposito Cisco per EPEL non è EPEL")
		}
	}
}

func mapKeys(m map[string]string) []string {
	var r []string
	for k := range m {
		r = append(r, k)
	}
	return r
}
