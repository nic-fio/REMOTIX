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
		m := map[string]string{"gpu.nodes": "renderD128", "gpu.renderD128.vendor": ""}
		for i, f := range forn {
			n := "renderD12" + string(rune('8'+i))
			m["gpu."+n+".vendor"] = f
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
		{"fedora", "44", map[string]string{"gpu.nodes": "none", "gpu.renderD128.vendor": ""}, "", "", false},
		{"opensuse-tumbleweed", "20260930", scheda("Intel"), "", "", false},
		{"opensuse-tumbleweed", "20260930", scheda("AMD"), "packman", "Mesa-dri,Mesa-libva,libvulkan_radeon", false},
		{"opensuse-leap", "16.0", scheda("AMD"), "packman", "Mesa-dri,Mesa-libva,libvulkan_radeon", false},
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
	p := profiloDi("fedora", "44", map[string]string{"repo.rpmfusion": "present"})
	rap := Valuta(cat, p)
	if got := DepositiDaChiedere(rap, p, ""); strings.Join(got, ",") != "rpmfusion" {
		t.Errorf("fedora Intel senza nonfree: %v", got)
	}
	p.Rilevato("repo.rpmfusion-nonfree", "present", "finto")
	if got := DepositiDaChiedere(rap, p, ""); len(got) != 0 {
		t.Errorf("fedora Intel con free e nonfree: %v", got)
	}
	// Alma: EPEL serve a REMOTIX stesso (RPM Fusion per EL lo vuole prima di sé), poi i driver; il
	// deposito Cisco di OpenH264 non c'è più (fase 19)
	a := profiloDi("almalinux", "10.1", nil)
	if got := DepositiDaChiedere(Valuta(cat, a), a, ""); strings.Join(got, ",") != "epel,rpmfusion" {
		t.Errorf("alma Intel: %v", got)
	}
}

// Il piano: il deposito col ramo nonfree per Intel, i driver da lì, e nient'altro nella transazione
// di REMOTIX (fase 19: niente OpenH264); un «no» a un deposito che serve ⇒ RX-H264-006.
func TestPianoSenzaFfmpeg(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	os.WriteFile(filepath.Join(radice, "remotix.rpm"), []byte("pacchetto finto"), 0o644)
	amb := ambienteFinto(radice)
	// «rpm -q» (i pezzi del deposito, per l'impronta): niente installato
	amb.Esegui = func(_ time.Duration, nome string, _ ...string) (string, int, error) { return "", 1, nil }
	cat := catalogoProva(t)
	fed := profiloDi("fedora", "44", nil)
	fed.Verificato("h264.gpu", "no", "finto")
	rap := Valuta(cat, fed)
	p, err := PianoInstallazione(fed, rap, cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.rpm", Porta: 7447, Depositi: []string{"rpmfusion"}})
	if err != nil {
		t.Fatal(err)
	}
	var dep, codec, pacchi *AzionePiano
	for i := range p.Azioni {
		switch a := &p.Azioni[i]; a.ID {
		case "repo-rpmfusion":
			dep = a
		case "codec":
			codec = a
		case "packages":
			pacchi = a
		}
	}
	if dep == nil || dep.Parametri["nonfree"] != "yes" {
		t.Errorf("il deposito RPM Fusion col ramo nonfree: %+v", dep)
	}
	if codec == nil || codec.Parametri["names"] != "intel-media-driver" || codec.Parametri["from"] != "rpmfusion" {
		t.Errorf("i driver da RPM Fusion: %+v", codec)
	}
	if pacchi == nil || pacchi.Parametri["names"] != "" {
		t.Errorf("solo il pacchetto di REMOTIX nella sua transazione: %+v", pacchi)
	}
	for _, m := range p.NonFatto {
		if m.Codice == "RX-H264-006" {
			t.Errorf("col consenso non si blocca: %+v", m)
		}
	}
	// Alma con EPEL ma senza il consenso a RPM Fusion (il driver Intel con H.264): BLOCCATA (D5)
	alma := profiloDi("almalinux", "10.1", map[string]string{"repo.epel": "present"})
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
	if !strings.Contains(bl, "RPM Fusion") || strings.Contains(bl, "OpenH264") {
		t.Errorf("alma senza RPM Fusion: %q", bl)
	}
}

// Il preflight: i driver di RPM Fusion nelle loro cartelle e la famiglia del driver dal pacchetto
// (fase 19: niente più OpenH264 da guardare).
func TestPreflightSenzaFfmpeg(t *testing.T) {
	casi := []struct {
		nome   string
		file   map[string]string
		fatti  map[string]string
		scheda string
	}{
		{"fedora Intel col driver ridotto",
			map[string]string{"usr/lib64/dri/iHD_drv_video.so": ""},
			map[string]string{"distro.family": "fedora", "package.libva-intel-media-driver": "26.2.4-1.fc44"}, "no"},
		{"fedora Intel col driver di RPM Fusion (dri-nonfree)",
			map[string]string{"usr/lib64/dri/iHD_drv_video.so": "", "usr/lib64/dri-nonfree/iHD_drv_video.so": ""},
			map[string]string{"distro.family": "fedora", "package.libva-intel-media-driver": "26.2.4-1.fc44", "package.intel-media-driver": "26.1.5-1.fc44"}, ""},
		{"openSUSE AMD con la Mesa ufficiale",
			map[string]string{"usr/lib64/dri/radeonsi_drv_video.so": ""},
			map[string]string{"distro.family": "suse", "gpu.renderD128.vendor": "AMD", "package.Mesa-dri": "26.2.3-1.1"}, "no"},
		{"openSUSE AMD con la Mesa di Packman",
			map[string]string{"usr/lib64/dri/radeonsi_drv_video.so": ""},
			map[string]string{"distro.family": "suse", "gpu.renderD128.vendor": "AMD", "package.Mesa-dri": "26.2.3-1699.2.pm.1"}, ""},
	}
	for _, c := range casi {
		a := &Ambiente{Radice: radiceFinta(t, c.file, nil), Esegui: nessunComando}
		p := NuovoProfilo(7447)
		p.Rilevato("gpu.renderD128.vendor", "Intel", "finto")
		for k, v := range c.fatti {
			p.Rilevato(k, v, "finto")
		}
		h264(a, p, c.fatti["distro.family"])
		f, _ := p.F("h264.gpu")
		if c.scheda == "" && f.Stato != SCONOSCIUTO || c.scheda != "" && (f.Stato != RILEVATO || f.Valore != c.scheda) {
			t.Errorf("%s: h264.scheda %+v, atteso %q", c.nome, f, c.scheda)
		}
	}
}

// I depositi della fase 18 nel preflight: il ramo nonfree VERO di RPM Fusion (non steam né
// nvidia-driver); il deposito Cisco di OpenH264 per EPEL, che una macchina può ancora avere, non è
// EPEL; e la fase 19 non lo guarda più.
func TestDepositiSenzaFfmpeg(t *testing.T) {
	steam := "[rpmfusion-nonfree-steam]\nname=steam\nbaseurl=https://x\nenabled=1\n"
	cisco := "[epel-cisco-openh264]\nmetalink=https://mirrors.fedoraproject.org/metalink?repo=epel-cisco-openh264-10\nenabled=1\n"
	for _, c := range []struct {
		file    map[string]string
		nonfree string
	}{
		{map[string]string{"etc/yum.repos.d/steam.repo": steam}, "absent"},
		{map[string]string{"etc/yum.repos.d/rpmfusion-nonfree.repo": "[rpmfusion-nonfree]\nmetalink=x\nenabled=1\n"}, "present"},
		{map[string]string{"etc/yum.repos.d/epel-cisco-openh264.repo": cisco}, "absent"},
	} {
		p := NuovoProfilo(7447)
		depositi(&Ambiente{Radice: radiceFinta(t, c.file, nil)}, p)
		if p.V("repo.rpmfusion-nonfree") != c.nonfree || p.V("repo.openh264") != "" {
			t.Errorf("%v: nonfree %q, openh264 %q; atteso %q e niente", c.file, p.V("repo.rpmfusion-nonfree"), p.V("repo.openh264"), c.nonfree)
		}
		if strings.Contains(strings.Join(mapKeys(c.file), ""), "epel-cisco") && p.V("repo.epel") == "present" {
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
