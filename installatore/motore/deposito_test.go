package motore

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Un deposito di terzi si annulla (disinstallazione): i pacchetti arrivati con lui che qualcosa che
// resta chiede si TRATTENGONO, e con loro resta il deposito — dichiarato con RX-PACCHETTI-006 (la
// regola della disinstallazione: si trattiene ciò che serve a chi resta). `[M]` T10, 30 set (fase 18,
// col deposito Cisco): fedora44-gnome-iso (libheif e mozilla-openh264 chiedono openh264), alma10-kde.
// Prima la disinstallazione si annullava con RX-PACCHETTI-002.

// comandiFinti: un Esecutore che risponde a rpm e dnf come su una Fedora con «installati»,
// dove «dipendenti» dice chi dipende da chi; annota le rimozioni vere in «tolti».
type comandiFinti struct {
	installati []string
	dipendenti map[string][]string
	tolti      []string
}

func (f *comandiFinti) esegui(_ time.Duration, nome string, arg ...string) (string, int, error) {
	a := strings.Join(arg, " ")
	switch {
	case nome == "rpm" && strings.HasPrefix(a, "-qa"):
		var b strings.Builder
		for _, x := range f.installati {
			b.WriteString(x + " 1.0-1\n")
		}
		return b.String(), 0, nil
	case nome == "rpm" && strings.HasPrefix(a, "-q --qf"):
		var b strings.Builder
		for _, n := range arg[3:] {
			for _, x := range f.installati {
				if x == n {
					b.WriteString(n + " 1.0-1\n")
				}
			}
		}
		return b.String(), 0, nil
	case nome == "rpm" && arg[0] == "-e":
		f.tolti = append(f.tolti, arg[1:]...)
		return "", 0, nil
	case nome == "dnf" && arg[0] == "remove" && arg[1] == "--assumeno":
		nomi := arg[3:]
		out := "Removing:\n"
		for _, n := range nomi {
			out += " " + n + "  x86_64  1.0-1  @finto  1 k\n"
		}
		dip := ""
		for _, n := range nomi {
			for _, d := range f.dipendenti[n] {
				dip += " " + d + "  x86_64  1.0-1  @finto  1 k\n"
			}
		}
		if dip != "" {
			out += "Removing dependent packages:\n" + dip
		}
		return out + "\nTransaction Summary\n", 0, nil
	case nome == "dnf" && arg[0] == "remove" && arg[1] == "-y":
		f.tolti = append(f.tolti, arg[3:]...)
		var resto []string
		for _, x := range f.installati {
			via := false
			for _, n := range arg[3:] {
				via = via || x == n
			}
			if !via {
				resto = append(resto, x)
			}
		}
		f.installati = resto
		return "", 0, nil
	case nome == "dnf" && arg[0] == "config-manager":
		f.tolti = append(f.tolti, "config-manager "+strings.Join(arg[1:], " "))
		return "", 0, nil
	}
	return "", 1, nil
}

func ambienteRpmFinto(t *testing.T, id string, f *comandiFinti) *Ambiente {
	t.Helper()
	r := t.TempDir()
	os.MkdirAll(filepath.Join(r, "etc/yum.repos.d"), 0o755)
	os.MkdirAll(filepath.Join(r, "etc/pki/rpm-gpg"), 0o755)
	os.WriteFile(filepath.Join(r, "etc/os-release"), []byte("ID="+id+"\nVERSION_ID=\"44\"\n"), 0o644)
	return &Ambiente{Radice: r, Esegui: f.esegui, Famiglia: "fedora"}
}

func TestDepositoTrattieneChiServe(t *testing.T) {
	// Fedora: RPM Fusion aggiunto da noi; il driver arrivato con lui (intel-media-driver) lo chiede
	// gstreamer1-vaapi, che resta. (Fase 18 il caso vero era openh264 dal deposito Cisco, uscito con
	// la fase 19: la regola è la stessa per ogni deposito di terzi.)
	f := &comandiFinti{installati: []string{"rpmfusion-free-release", "gstreamer1-vaapi", "remotix", "intel-media-driver"},
		dipendenti: map[string][]string{"intel-media-driver": {"gstreamer1-vaapi"}}}
	amb := ambienteRpmFinto(t, "fedora", f)
	d := &deposito{tipo: "rpmfusion", par: map[string]string{"type": "rpmfusion"}}
	c := &Contesto{Amb: amb, Purge: true}
	prima, _ := json.Marshal(primaDeposito{Origine: DIRETTA, Tipo: "rpmfusion",
		Stato: map[string]bool{"rpmfusion-free-release": false}, Rpm: []string{"gstreamer1-vaapi", "remotix", "rpmfusion-free-release"}})

	if err := d.Annulla(c, prima); err != nil {
		t.Fatalf("Annulla: %v", err)
	}
	if len(f.tolti) != 0 {
		t.Fatalf("niente doveva essere tolto (intel-media-driver lo chiede gstreamer1-vaapi, e il deposito resta): %v", f.tolti)
	}
	ok, det, err := d.Annullata(c, prima)
	if err != nil || !ok || !strings.Contains(det, "[RX-PACCHETTI-006]") || !strings.Contains(det, "intel-media-driver") || !strings.Contains(det, "gstreamer1-vaapi") {
		t.Fatalf("Annullata: %v %q %v", ok, det, err)
	}

	// nessuno lo chiede più: il driver e il deposito se ne vanno
	f2 := &comandiFinti{installati: []string{"rpmfusion-free-release", "remotix", "intel-media-driver"}, dipendenti: map[string][]string{}}
	c2 := &Contesto{Amb: ambienteRpmFinto(t, "fedora", f2), Purge: true}
	if err := d.Annulla(c2, prima); err != nil {
		t.Fatalf("Annulla 2: %v", err)
	}
	if s := strings.Join(f2.tolti, "|"); !strings.Contains(s, "intel-media-driver") || !strings.Contains(s, "rpmfusion-free-release") {
		t.Fatalf("attesi il driver e il deposito tolti: %v", f2.tolti)
	}
}

// dnf che non risolve la transazione (un pacchetto protetto la romperebbe): i nomi dei «Problem»
// sono i dipendenti, e il pacchetto si trattiene invece di far fallire `dnf remove -y`.
func TestDnfSimulaTogliProtetti(t *testing.T) {
	out := `Failed to resolve the transaction:
Problem 1: The operation would result in broken dependencies for the following protected packages: gnome-shell
Problem 2: installed package glycin-libs-2.1.5-1.fc44.x86_64 requires glycin-loaders(x86-64) = 2.1.5-1.fc44, but none of the providers can be installed
  - installed package glycin-loaders-2.1.5-1.fc44.x86_64 requires libheif.so.1()(64bit), but none of the providers can be installed
  - installed package gdk-pixbuf2-2.44.6^really2.44.4-3.fc44.x86_64 requires glycin-libs(x86-64) >= 2.0.1, but none of the providers can be installed
  - installed package libheif-1.23.5-3.fc44.x86_64 requires libopenh264.so.8()(64bit), but none of the providers can be installed
  - conflicting requests
  - problem with installed package
`
	amb := &Ambiente{Esegui: func(_ time.Duration, nome string, arg ...string) (string, int, error) {
		if nome == "dnf" && arg[0] == "remove" && arg[1] == "--assumeno" {
			return out, 1, nil
		}
		return "", 1, nil
	}}
	altri, err := (&gestoreDnf{amb}).SimulaTogli([]string{"openh264"}, true)
	if err != nil {
		t.Fatal(err)
	}
	s := strings.Join(altri, ",")
	for _, n := range []string{"gnome-shell", "glycin-libs", "glycin-loaders", "gdk-pixbuf2", "libheif"} {
		if !strings.Contains(s, n) {
			t.Fatalf("manca %s fra i dipendenti: %v", n, altri)
		}
	}
	if strings.Contains(s, "openh264") || nomeDaNevra("gdk-pixbuf2-2.44.6^really2.44.4-3.fc44.x86_64") != "gdk-pixbuf2" {
		t.Fatalf("%v %q", altri, nomeDaNevra("gdk-pixbuf2-2.44.6^really2.44.4-3.fc44.x86_64"))
	}
	// e trattenuti li tiene: via niente, resta openh264 col perché
	via, resta, err := trattenuti(&gestoreDnf{amb}, []string{"openh264"}, []string{"openh264"}, true)
	if err != nil || len(via) != 0 || len(resta) != 1 || !strings.Contains(resta[0], "gnome-shell") {
		t.Fatalf("via %v resta %v err %v", via, resta, err)
	}
}
