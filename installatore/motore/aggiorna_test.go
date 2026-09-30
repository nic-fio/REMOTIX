package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// La configurazione degli aggiornamenti: il predefinito è la PROPOSTA di D14, il file vince, un
// valore sbagliato è un errore col suo codice (mai un ripiego in silenzio).
func TestConfAggiornamenti(t *testing.T) {
	r := t.TempDir()
	a := &Ambiente{Radice: r}
	c, err := LeggiConfAggiornamenti(a)
	if err != nil || c.Automatico != "manutenzione" || !strings.Contains(c.Da["automatico"], "D14") {
		t.Fatalf("predefinito: %v %+v", err, c)
	}
	os.MkdirAll(filepath.Join(r, "etc/remotix"), 0o755)
	os.WriteFile(filepath.Join(r, FileConfAggiornamenti), []byte("# prova\nautomatico = avviso\n"), 0o644)
	if c, err = LeggiConfAggiornamenti(a); err != nil || c.Automatico != "avviso" || c.Da["automatico"] != FileConfAggiornamenti {
		t.Fatalf("dal file: %v %+v", err, c)
	}
	os.WriteFile(filepath.Join(r, FileConfAggiornamenti), []byte("automatico = sempre\n"), 0o644)
	if _, err = LeggiConfAggiornamenti(a); CodiceDi(err) != "RX-AGG-010" {
		t.Fatalf("valore sbagliato: %v", err)
	}
}

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
	d := &deposito{tipo: "archivio", par: map[string]string{"url": "http://10.0.2.2:8717/deb", "suite": "debian13-stabile",
		"chiave": "CHIAVE", "host": "10.0.2.2", "pacchetti": "remotix,remotix-install,remotix-archive-keyring"}}
	f := d.fileArchivio(&Contesto{Amb: &Ambiente{Famiglia: "debian"}})
	if len(f) != 3 || !f[0].presenza || !strings.Contains(f[1].contenuto, "Signed-By: "+ChiaveApt) ||
		!strings.Contains(f[2].contenuto, "Pin: origin \"10.0.2.2\"\nPin-Priority: -1") ||
		strings.Index(f[2].contenuto, "Package: remotix ") > strings.Index(f[2].contenuto, "Package: *") {
		t.Fatalf("file per apt: %+v", f)
	}
	g := d.fileArchivio(&Contesto{Amb: &Ambiente{Famiglia: "fedora"}})
	if len(g) != 2 || !strings.Contains(g[1].contenuto, "includepkgs=remotix remotix-install remotix-archive-keyring") ||
		!strings.Contains(g[1].contenuto, "repo_gpgcheck=1") {
		t.Fatalf("file per dnf: %+v", g)
	}
}
