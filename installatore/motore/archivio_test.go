package motore

import (
	"strings"
	"testing"
)

// Il blocco di pacman.conf: si toglie SOLO lui, il resto del file resta byte per byte.
func TestBloccoPacman(t *testing.T) {
	prima := "[options]\nHoldPkg = pacman glibc\n\n[core]\nInclude = /etc/pacman.d/mirrorlist\n"
	con := prima + "\n" + bloccoPacman("http://10.0.2.2:8717/pacman/stabile/$arch")
	senza, ok := togliBlocco(con)
	if !ok || senza != prima {
		t.Fatalf("blocco tolto male:\n%q\n%q", senza, prima)
	}
	if _, ok := togliBlocco(prima); ok {
		t.Errorf("un blocco trovato dove non c'è")
	}
}

// I file dell'archivio per apt: Signed-By sul file della chiave, il pin sull'HOST (R18).
func TestFileArchivioApt(t *testing.T) {
	d := &deposito{tipo: "archive", par: map[string]string{"url": "http://10.0.2.2:8717/deb", "suite": "debian13-stabile",
		"key": "CHIAVE", "host": "10.0.2.2", "packages": "remotix,remotix-install,remotix-archive-keyring,remotix-selinux"}}
	f := d.fileArchivio(&Contesto{Amb: &Ambiente{Famiglia: "debian"}})
	if len(f) != 3 || !f[0].presenza || !strings.Contains(f[1].contenuto, "Signed-By: "+ChiaveApt) ||
		!strings.Contains(f[2].contenuto, "Pin: origin \"10.0.2.2\"\nPin-Priority: -1") ||
		strings.Index(f[2].contenuto, "Package: remotix ") > strings.Index(f[2].contenuto, "Package: *") {
		t.Fatalf("file per apt: %+v", f)
	}
	g := d.fileArchivio(&Contesto{Amb: &Ambiente{Famiglia: "fedora"}})
	if len(g) != 2 || !strings.Contains(g[1].contenuto, "includepkgs=remotix remotix-install remotix-archive-keyring remotix-selinux") ||
		!strings.Contains(g[1].contenuto, "repo_gpgcheck=1") {
		t.Fatalf("file per dnf: %+v", g)
	}
}
