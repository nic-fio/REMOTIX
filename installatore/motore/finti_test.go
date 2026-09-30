package motore

// Una macchina finta sotto una cartella: /etc/group, /etc/passwd, i file veri, e systemd e
// firewalld finti fatti di file JSON (così lo stato sopravvive a un processo ucciso, come sulla
// macchina vera). Il motore non sa la differenza: usa le stesse interfacce.

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	"remotix/installatore/catalogo"
)

type gruppiFinti struct{ radice string }

func (g *gruppiFinti) file() string { return filepath.Join(g.radice, "etc/group") }

func (g *gruppiFinti) Membri(gruppo string) ([]string, string, bool, error) {
	t, err := LeggiGruppi(g.file())
	if err != nil {
		return nil, "", false, err
	}
	v, ok := t[gruppo]
	return DividiMembri(v[1]), v[0], ok, nil
}

func (g *gruppiFinti) GruppoPrimario(u string) (string, bool, error) {
	return LeggiUtente(filepath.Join(g.radice, "etc/passwd"), u)
}

// cambia riscrive la riga del gruppo mantenendo l'ordine dei membri (come gpasswd).
func (g *gruppiFinti) cambia(gruppo string, f func([]string) []string) error {
	b, err := os.ReadFile(g.file())
	if err != nil {
		return err
	}
	righe := strings.Split(strings.TrimSuffix(string(b), "\n"), "\n")
	for i, r := range righe {
		c := strings.Split(r, ":")
		if len(c) == 4 && c[0] == gruppo {
			var m []string
			for _, x := range strings.Split(c[3], ",") {
				if x != "" {
					m = append(m, x)
				}
			}
			c[3] = strings.Join(f(m), ",")
			righe[i] = strings.Join(c, ":")
		}
	}
	return ScriviAtomico(g.file(), []byte(strings.Join(righe, "\n")+"\n"), 0o644)
}

func (g *gruppiFinti) Aggiungi(u, gruppo string) error {
	return g.cambia(gruppo, func(m []string) []string { return append(m, u) })
}

func (g *gruppiFinti) Togli(u, gruppo string) error {
	return g.cambia(gruppo, func(m []string) []string {
		var r []string
		for _, x := range m {
			if x != u {
				r = append(r, x)
			}
		}
		return r
	})
}

// statoJSON: una mappa in un file (systemd e firewalld finti).
func leggiMappa(p string) map[string]bool {
	m := map[string]bool{}
	if b, err := os.ReadFile(p); err == nil {
		json.Unmarshal(b, &m)
	}
	return m
}

func scriviMappa(p string, m map[string]bool) error {
	b, _ := json.Marshal(m)
	return ScriviAtomico(p, b, 0o644)
}

type unitaFinte struct{ radice string }

func (u *unitaFinte) file() string { return filepath.Join(u.radice, "var/lib/finto-systemd.json") }

func (u *unitaFinte) Stato(n string) (string, error) {
	if _, err := os.Stat(filepath.Join(u.radice, "rompi-systemctl")); err == nil {
		return "", fmt.Errorf("systemctl: tempo scaduto (finto)")
	}
	if _, err := os.Stat(filepath.Join(u.radice, "etc/systemd/system", n)); err != nil {
		return "not-found", nil
	}
	if leggiMappa(u.file())[n] {
		return "enabled", nil
	}
	return "disabled", nil
}

func (u *unitaFinte) Abilita(n string) error {
	m := leggiMappa(u.file())
	m[n] = true
	return scriviMappa(u.file(), m)
}

func (u *unitaFinte) Disabilita(n string) error {
	m := leggiMappa(u.file())
	delete(m, n)
	return scriviMappa(u.file(), m)
}

type firewallFinto struct{ radice string }

func (f *firewallFinto) file() string { return filepath.Join(f.radice, "var/lib/finto-firewalld.json") }

func (f *firewallFinto) Nome() string {
	if b, err := os.ReadFile(filepath.Join(f.radice, "etc/finto-firewall")); err == nil {
		return strings.TrimSpace(string(b))
	}
	return "firewalld"
}
func (f *firewallFinto) ZonaPredefinita() (string, error) { return "public", nil }
func chiaveFw(z, p string, perm bool) string {
	if perm {
		return z + " " + p + " permanente"
	}
	return z + " " + p + " vive"
}
func (f *firewallFinto) HaPorta(z, p string, perm bool) (bool, error) {
	return leggiMappa(f.file())[chiaveFw(z, p, perm)], nil
}
func (f *firewallFinto) Aggiungi(z, p string, perm bool) error {
	m := leggiMappa(f.file())
	m[chiaveFw(z, p, perm)] = true
	return scriviMappa(f.file(), m)
}
func (f *firewallFinto) Togli(z, p string, perm bool) error {
	m := leggiMappa(f.file())
	delete(m, chiaveFw(z, p, perm))
	return scriviMappa(f.file(), m)
}

func nessunComando(time.Duration, string, ...string) (string, int, error) {
	return "", -1, exec.ErrNotFound
}

func ambienteFinto(radice string) *Ambiente {
	return &Ambiente{Radice: radice, Esegui: nessunComando, Famiglia: "finta",
		Gruppi: &gruppiFinti{radice}, Unita: &unitaFinte{radice}, Firewall: &firewallFinto{radice},
		Pacchetti: &gestoreFinto{radice}, Sessioni: &sessioniFinte{radice}}
}

// profiloFinto: una Debian 13 con GNOME, scheda Intel che codifica.
func profiloFinto() *Profilo {
	p := NuovoProfilo(7447)
	p.Creato = "2026-09-30T00:00:00Z"
	for k, v := range map[string]string{
		"distro.id": "debian", "distro.versione": "13", "distro.famiglia": "debian", "distro.nome": "Debian GNU/Linux 13 (trixie)",
		"distro.immutabile": "no", "sistema.architettura": "x86_64", "sistema.systemd": "si",
		"desktop.gnome": "48.7", "desktop.kde": "assente", "desktop.xfce": "assente", "desktop.lxqt": "assente",
		"scheda.nodi": "renderD128", "scheda.renderD128.driver": "i915", "scheda.renderD128.fornitore": "Intel",
		"scheda.nvidia_proprietaria": "no", "selinux": "assente", "firewall.tipo": "firewalld", "openssl.versione": "3.5.7",
		"gruppo.video": "gid=44", "caratteri.scalabili": "20",
	} {
		p.Rilevato(k, v, "finto")
	}
	p.Verificato("h264.scheda", "si", "finto")
	p.Ordina()
	return p
}

func catalogoProva(t testing.TB) *Catalogo {
	c, err := LeggiCatalogo(catalogo.Incorporato)
	if err != nil {
		t.Fatal(err)
	}
	return c
}

// prepara la macchina finta: la foto «prima» di ogni prova.
func preparaMacchina(t testing.TB, radice string) {
	file := map[string]string{
		"etc/group":                  "root:x:0:\nvideo:x:44:altro\nrender:x:991:\nprova:x:1000:\naltro:x:1001:\n",
		"etc/passwd":                 "root:x:0:0::/root:/bin/sh\nprova:x:1000:1000::/home/prova:/bin/sh\naltro:x:1001:1001::/home/altro:/bin/sh\n",
		"etc/remotix-esistente.conf": "vecchio contenuto dell'amministratore\n",
		"var/lib/finto-systemd.json": "{}",
		// una delle quattro regole c'era già: dopo l'annullamento deve restare
		"var/lib/finto-firewalld.json": `{"public 7447/tcp vive":true}`,
		// il pacchetto di REMOTIX (finto) e il deposito: libcomune c'è già a una versione vecchia
		// (sarà AGGIORNATA: INDIRETTA, resta), libnuova e labwc sono nuove
		"var/pacchetti/remotix.pkg":    `{"nome":"remotix","versione":"0.17.0-1","dipende":["libnuova","libcomune"]}`,
		"var/lib/finto-deposito.json":  `{"libnuova":{"versione":"1.0"},"libcomune":{"versione":"2.0"},"labwc":{"versione":"0.9","dipende":["libnuova"]}}`,
		"var/lib/finto-pacchetti.json": `{"libcomune":"1.0","bash":"5.2"}`,
		"var/lib/finto-attive.json":    "{}",
		// la pila PAM di REMOTIX (certifica.go la segue fino ai moduli)
		"etc/pam.d/remotix":            "auth required pam_unix.so\n@include common-account\n",
		"etc/pam.d/common-account":     "account required pam_unix.so\n-session optional pam_manca.so\n",
		"usr/lib/security/pam_unix.so": "",
		// la cintura spenta che il pacchetto porterebbe
		"usr/share/remotix/cinture/remotix-tasti.conf": "[Login]\nHandlePowerKey=ignore\n",
	}
	for p, c := range file {
		d := filepath.Join(radice, p)
		os.MkdirAll(filepath.Dir(d), 0o755)
		if err := os.WriteFile(d, []byte(c), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	os.Chmod(filepath.Join(radice, "etc/remotix-esistente.conf"), 0o640)
	os.MkdirAll(filepath.Join(radice, "etc/systemd/system"), 0o755)
}

// azioniDiProva: sette passi che coprono i casi: file nuovo in una cartella nuova, file che
// sovrascrive quello dell'amministratore, unità, gruppo nostro, gruppo PREESISTENTE, firewall con
// una regola già presente.
func azioniDiProva() []AzionePiano {
	return []AzionePiano{
		PianoPacchetti("pacchetti", "/var/pacchetti/remotix.pkg", Sha256([]byte(`{"nome":"remotix","versione":"0.17.0-1","dipende":["libnuova","libcomune"]}`)), "labwc"),
		PianoScriviFile("file-conf", "/etc/remotix/prova-motore.conf", "porta=7447\n", "0644"),
		PianoScriviFile("file-sovrascritto", "/etc/remotix-esistente.conf", "contenuto di REMOTIX\n", "0644"),
		PianoScriviFile("file-unita", "/etc/systemd/system/remotix-prova-motore.service", "[Unit]\nDescription=prova\n[Install]\nWantedBy=multi-user.target\n", "0644"),
		PianoUnita("unita", "remotix-prova-motore.service"),
		PianoGruppo("gruppo-video", "prova", "video"),
		PianoGruppo("gruppo-preesistente", "altro", "video"),
		PianoFirewall("firewall", "7447"),
		PianoCintura("cintura-tasti", "/usr/share/remotix/cinture/remotix-tasti.conf", "/etc/systemd/logind.conf.d/remotix-tasti.conf", "systemd-logind.service"),
		PianoAccendiServizio("servizio", "remotix-prova-motore.service", 0),
	}
}

// pianoDiProva scrive il piano approvato per la macchina finta, e ne restituisce il percorso.
func pianoDiProva(t testing.TB, radice, dove string, approvato bool) string {
	amb := ambienteFinto(radice)
	cat := catalogoProva(t)
	pn := &Piano{Formato: Formato, Oggetto: "piano", ID: "piano-prova", Creato: "2026-09-30T00:00:00Z", Mestiere: "prova-motore",
		Catalogo: RifCatalogo{cat.Versione, cat.Digest}, Azioni: azioniDiProva(),
		Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}}
	im, err := CalcolaImpronta(profiloFinto(), cat, pn.Azioni, pn.Dipende, &Contesto{Amb: amb})
	if err != nil {
		t.Fatal(err)
	}
	pn.Impronta = *im
	if approvato {
		pn.Approvazione = &Approvazione{Da: "prova", Ora: "2026-09-30T00:00:00Z", Modo: "da file", DigestPiano: pn.Digest()}
	}
	p := filepath.Join(dove, "piano.json")
	if err := ScriviJSON(p, pn); err != nil {
		t.Fatal(err)
	}
	return p
}

func motoreFinto(t testing.TB, radice, operazioni string) *Motore {
	return &Motore{Amb: ambienteFinto(radice), Cartella: operazioni, Catalogo: catalogoProva(t), Fonti: fontiProva(t),
		Esamina: profiloFinto, Adesso: func() time.Time { return time.Date(2026, 9, 30, 12, 0, 0, 0, time.UTC) }}
}

// foto: ogni file e cartella della macchina finta, con permessi e contenuto.
func foto(t testing.TB, radice string) map[string]string {
	r := map[string]string{}
	filepath.WalkDir(radice, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			t.Fatal(err)
		}
		rel, _ := filepath.Rel(radice, p)
		info, _ := d.Info()
		if d.IsDir() {
			r[rel+"/"] = info.Mode().String()
			return nil
		}
		b, _ := os.ReadFile(p)
		s := sha256.Sum256(b)
		r[rel] = info.Mode().String() + " " + hex.EncodeToString(s[:8])
		return nil
	})
	return r
}

func differenze(a, b map[string]string) []string {
	var d []string
	for k, v := range a {
		if b[k] != v {
			d = append(d, fmt.Sprintf("%s: %q → %q", k, v, b[k]))
		}
	}
	for k, v := range b {
		if _, ok := a[k]; !ok {
			d = append(d, fmt.Sprintf("%s: (non c'era) → %q", k, v))
		}
	}
	sort.Strings(d)
	return d
}
