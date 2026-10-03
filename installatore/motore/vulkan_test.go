package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Fase 19: il driver Vulkan della scheda dal catalogo (vulkan_scheda). `[M]` 1 ott 2026 nelle immagini
// podman: la RADV ufficiale codifica dove Mesa è costruita coi codec (Debian e Ubuntu
// mesa-vulkan-drivers, Arch vulkan-radeon — lì solo un optdepends); Fedora, RHEL e openSUSE la
// costruiscono «all_free» (senza H.264): Fedora e Alma niente, openSUSE la RADV di Packman insieme al
// resto della sua Mesa. Intel mai (resta a VA-API), NVIDIA mai in automatico (solo nel rimedio).
func TestVulkanDelCatalogo(t *testing.T) {
	cat := catalogoProva(t)
	scheda := func(f string) map[string]string {
		return map[string]string{"scheda.nodi": "renderD128", "scheda.renderD128.fornitore": f}
	}
	for _, c := range []struct {
		id, ver, forn, vulkan string
	}{
		{"debian", "13", "AMD", "mesa-vulkan-drivers"},
		{"debian", "13", "Intel", ""},
		{"debian", "13", "NVIDIA", ""},
		{"ubuntu", "26.04", "AMD", "mesa-vulkan-drivers"},
		{"arch", "rolling", "AMD", "vulkan-radeon"},
		{"arch", "rolling", "Intel", ""},
		{"arch", "rolling", "NVIDIA", ""},
		{"fedora", "44", "AMD", ""},
		{"almalinux", "10.1", "AMD", ""},
		{"opensuse-tumbleweed", "20260930", "AMD", ""},
		{"opensuse-leap", "16.0", "AMD", ""},
	} {
		p := profiloDi(c.id, c.ver, scheda(c.forn))
		rap := Valuta(cat, p)
		if rap.pl == nil {
			t.Fatalf("%s %s: piattaforma sconosciuta", c.id, c.ver)
		}
		if got := strings.Join(rap.pl.H264.VulkanPerLaScheda(p), ","); got != c.vulkan {
			t.Errorf("%s %s: driver Vulkan %q, atteso %q", c.id, c.forn, got, c.vulkan)
		}
	}
	// senza schede, o senza sapere di che fornitore, niente
	if got := (H264Piattaforma{VulkanScheda: map[string]string{"AMD": "x"}}).VulkanPerLaScheda(profiloDi("arch", "rolling",
		map[string]string{"scheda.nodi": "nessuno", "scheda.renderD128.fornitore": ""})); len(got) != 0 {
		t.Errorf("senza schede: %v", got)
	}

	// il verdetto: AMD su Arch SENZA l'ICD conta (il motore installa vulkan-radeon); AMD su Alma CON
	// l'ICD di RADV no (la RADV di RHEL non ha H.264, e VA-API su AMD lì non c'è) ⇒ RX-GPU-006
	arch := profiloDi("arch", "rolling", map[string]string{"scheda.renderD128.fornitore": "AMD", "codifica.vulkan.icd": "nessuno"})
	ra := Valuta(cat, arch)
	if got := strings.Join(schedeVulkan(ra.pl, arch), ","); got != "AMD" {
		t.Errorf("arch AMD senza ICD: schede vulkan %q", got)
	}
	if cod, det := VerdettoScheda(ra.pl, arch); cod != "" {
		t.Errorf("arch AMD senza ICD: %s %s", cod, det)
	}
	alma := profiloDi("almalinux", "10.1", map[string]string{"scheda.renderD128.fornitore": "AMD", "codifica.vulkan.icd": "lvp,radeon"})
	rl := Valuta(cat, alma)
	if got := schedeVulkan(rl.pl, alma); len(got) != 0 {
		t.Errorf("alma AMD con RADV: schede vulkan %v", got)
	}
	if cod, _ := VerdettoScheda(rl.pl, alma); cod != "RX-GPU-006" {
		t.Errorf("alma AMD con RADV: %q, atteso RX-GPU-006", cod)
	}
	// senza catalogo si giudica dal solo ICD, come prima
	if got := strings.Join(schedeVulkan(nil, alma), ","); got != "AMD" {
		t.Errorf("senza catalogo, AMD con l'ICD radeon: %q", got)
	}
	// NVIDIA proprietaria senza ICD: il rimedio nomina il pacchetto della distribuzione
	nv := profiloDi("debian", "13", map[string]string{"scheda.renderD128.fornitore": "NVIDIA",
		"scheda.nvidia_proprietaria": "si", "codifica.vulkan.icd": "nessuno"})
	if cod, det := VerdettoScheda(Valuta(cat, nv).pl, nv); cod != "RX-GPU-004" || !strings.Contains(det, "nvidia-vulkan-icd") {
		t.Errorf("debian NVIDIA senza ICD: %q %q", cod, det)
	}
}

// Il piano: su Arch con una AMD il passo «vulkan» chiede vulkan-radeon; con una Intel il passo non c'è.
func TestPianoVulkan(t *testing.T) {
	radice := t.TempDir()
	preparaMacchina(t, radice)
	os.WriteFile(filepath.Join(radice, "remotix.pkg.tar.zst"), []byte("pacchetto finto"), 0o644)
	amb := ambienteFinto(radice)
	amb.Esegui = func(_ time.Duration, _ string, _ ...string) (string, int, error) { return "", 1, nil }
	cat := catalogoProva(t)
	for _, c := range []struct{ forn, atteso string }{{"AMD", "vulkan-radeon"}, {"Intel", ""}} {
		p := profiloDi("arch", "rolling", map[string]string{"scheda.renderD128.fornitore": c.forn})
		pn, err := PianoInstallazione(p, Valuta(cat, p), cat, amb, OpzioniInstallazione{Pacchetto: "/remotix.pkg.tar.zst", Porta: 7447})
		if err != nil {
			t.Fatal(err)
		}
		got := ""
		for _, a := range pn.Azioni {
			if a.ID == "vulkan" {
				got = a.Parametri["nomi"]
			}
		}
		if got != c.atteso {
			t.Errorf("arch %s: passo vulkan %q, atteso %q", c.forn, got, c.atteso)
		}
	}
}
