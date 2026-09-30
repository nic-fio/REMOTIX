package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// aggiungi-deposito: un archivio di pacchetti in più (§6.0 punto 4: aggiungere un deposito cambia
// già la macchina ⇒ è un passo del piano, col registro, prima dei pacchetti).
//
//   - «archivio»: l'archivio FIRMATO di REMOTIX con la SUA chiave, valida solo per lui (§6.5
//     punto 6, R18: Signed-By su apt, gpgkey + import in rpm su dnf e zypper; mai trusted.gpg.d).
//     ESATTA: i file (e la chiave in rpm o in pacman), tolti come non c'erano; su Arch un blocco in
//     /etc/pacman.conf fra due righe di marca. Il perché di ogni pezzo: archivio.go (T8).
//   - «epel» (Alma/RHEL: SVT-AV1, KDE), «rpmfusion» (Fedora, Alma: i driver con H.264; col ramo
//     nonfree se la scheda è Intel), «packman» (openSUSE con scheda AMD: la Mesa coi codec),
//     «openh264» (OpenH264 di Cisco, il ripiego software: Fedora lo accende, Alma lo scrive — il
//     deposito Cisco per EPEL, firmato con la chiave di EPEL —, openSUSE lo aggiunge): archivi di
//     TERZI, col consenso (D5, riga sua). AL_MEGLIO: il deposito si toglie, ma i pacchetti presi da
//     lì e gli aggiornamenti restano (si dichiara). Fase 18 (senza ffmpeg).
//
// parametri: tipo; per «archivio»: nome, url, chiave (il testo della chiave pubblica, armatura
// ASCII), suite, componenti; per «rpmfusion»: nonfree ("si": anche rpmfusion-nonfree-release).

func init() { registraTipo("aggiungi-deposito", nuovaDeposito) }

// PianoDeposito prepara il passo del piano.
func PianoDeposito(id, tipo string, par map[string]string, consenso string) AzionePiano {
	p := map[string]string{"tipo": tipo}
	for k, v := range par {
		p[k] = v
	}
	rev := AL_MEGLIO
	if tipo == "archivio" {
		rev = ESATTA
	}
	return AzionePiano{
		ID: id, Tipo: "aggiungi-deposito", Parametri: p,
		Descrizione:    T("az.deposito", nonVuoto(par["nome"], tipo)),
		ComeSiFa:       T("az.deposito.fa." + tipo),
		ComeSiVerifica: T("az.deposito.verifica"),
		ComeSiAnnulla:  T("az.deposito.annulla." + tipo),
		Reversibilita:  rev,
		Consenso:       consenso,
	}
}

type deposito struct {
	tipo string
	par  map[string]string
}

type primaDeposito struct {
	Origine Origine           `json:"origine"`
	Tipo    string            `json:"tipo"`
	Stato   map[string]bool   `json:"stato"`          // i pezzi, c'erano prima?
	File    map[string]string `json:"file,omitempty"` // archivio: percorso → prima dello scrivi-file
	Chiavi  []string          `json:"chiavi,omitempty"`
	// Rpm: i pacchetti rpm di prima (anche le chiavi gpg-pubkey): quel che il pacchetto del deposito
	// si porta dietro (dipendenze deboli, la chiave della distribuzione importata al primo uso) si
	// riconosce e si toglie. [M] 30 set, Alma 10: epel-release porta selinux-policy-*-extra.
	Rpm []string `json:"rpm,omitempty"`
}

func nuovaDeposito(p AzionePiano) (Azione, error) {
	d := &deposito{tipo: p.Parametri["tipo"], par: p.Parametri}
	switch d.tipo {
	case "archivio", "epel", "rpmfusion", "packman", "openh264":
		return d, nil
	}
	return nil, fmt.Errorf("aggiungi-deposito: tipo %q sconosciuto", d.tipo)
}

// ---- i pezzi di un deposito di terzi, per famiglia

func (d *deposito) majorVersione(c *Contesto) string {
	m, _ := OsRelease(c.Amb)
	v, _, _ := strings.Cut(m["VERSION_ID"], ".")
	return v
}

func (d *deposito) rhel(c *Contesto) bool {
	m, _ := OsRelease(c.Amb)
	return m["ID"] != "fedora"
}

// pezzi: nome → (c'è adesso?)
func (d *deposito) pezzi(c *Contesto) (map[string]bool, error) {
	r := map[string]bool{}
	switch d.tipo {
	case "epel":
		v, err := rpmVersioni(c.Amb, []string{"epel-release"})
		if err != nil {
			return nil, err
		}
		r["epel-release"] = v["epel-release"] != ""
		r["crb"] = repoAcceso(c, "crb")
	case "rpmfusion":
		v, err := rpmVersioni(c.Amb, []string{"rpmfusion-free-release", "rpmfusion-nonfree-release"})
		if err != nil {
			return nil, err
		}
		r["rpmfusion-free-release"] = v["rpmfusion-free-release"] != ""
		if d.par["nonfree"] == "si" {
			r["rpmfusion-nonfree-release"] = v["rpmfusion-nonfree-release"] != ""
		}
	case "openh264":
		switch {
		case c.Amb.Famiglia == "suse":
			r["repo-openh264"] = zypperOpenH264(c) != ""
		case d.rhel(c):
			_, err := os.Stat(c.Amb.P(fileCiscoEpel))
			r[fileCiscoEpel] = err == nil
		default:
			r["fedora-cisco-openh264"] = repoAcceso(c, "fedora-cisco-openh264")
		}
	case "packman":
		_, err := os.Stat(c.Amb.P("/etc/zypp/repos.d/packman.repo"))
		r["packman"] = err == nil
	case "archivio":
		for _, f := range d.fileArchivio(c) {
			sha, _ := Sha256File(c.Amb.P(f.percorso))
			if f.presenza {
				r[f.percorso] = sha != ""
			} else {
				r[f.percorso] = sha == Sha256([]byte(f.contenuto))
			}
		}
		if c.Amb.Famiglia == "arch" {
			_, c2, err := d.pacmanConf(c)
			if err != nil {
				return nil, err
			}
			r["pacman.conf [remotix]"] = c2
			k, err := d.chiavePacman(c)
			if err != nil {
				return nil, err
			}
			r["pacman-key "+d.par["impronta"]] = k
		}
	}
	return r, nil
}

// repoAcceso: una sezione [nome] con enabled=1 in /etc/yum.repos.d.
func repoAcceso(c *Contesto, nome string) bool {
	voci, _ := filepath.Glob(c.Amb.P("/etc/yum.repos.d") + "/*.repo")
	re := regexp.MustCompile(`(?m)^\[` + regexp.QuoteMeta(nome) + `\]\s*$`)
	for _, v := range voci {
		b, _ := os.ReadFile(v)
		t := string(b)
		i := re.FindStringIndex(t)
		if i == nil {
			continue
		}
		sez := t[i[1]:]
		if j := strings.Index(sez, "\n["); j >= 0 {
			sez = sez[:j]
		}
		return regexp.MustCompile(`(?m)^enabled\s*=\s*(1|true|yes)\s*$`).MatchString(sez)
	}
	return false
}

// fileCiscoEpel: il deposito Cisco di OpenH264 per EPEL (Alma/RHEL 10): lo scrive il motore.
const fileCiscoEpel = "/etc/yum.repos.d/epel-cisco-openh264.repo"

// ContenutoCiscoEpel: il file del deposito, come quello che EPEL 9 portava in epel-release. `[M]` 30
// set, alma10: metalink epel-cisco-openh264-10 ⇒ codecs.fedoraproject.org/openh264/epel/10,
// openh264-2.5.1 (libopenh264.so.7) installato con la firma verificata dalla chiave di EPEL 10.
func ContenutoCiscoEpel(major string) string {
	return "# epel-cisco-openh264 — aggiunto da remotix-install (OpenH264 di Cisco, il ripiego video)\n" +
		"[epel-cisco-openh264]\nname=Extra Packages for Enterprise Linux " + major + " - Cisco OpenH264 - $basearch\n" +
		"metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-cisco-openh264-$releasever_major&arch=$basearch\n" +
		"enabled=1\ngpgcheck=1\ngpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-" + major + "\n"
}

// zypperOpenH264: il file del deposito OpenH264 di openSUSE, acceso ("" se non c'è): repo-openh264
// (Tumbleweed) o openSUSE:repo-openh264 (Leap 16, dal servizio «openSUSE»), `[M]` 30 set.
func zypperOpenH264(c *Contesto) string {
	voci, _ := filepath.Glob(c.Amb.P("/etc/zypp/repos.d") + "/*.repo")
	for _, v := range voci {
		b, _ := os.ReadFile(v)
		t := string(b)
		if strings.Contains(t, "codecs.opensuse.org/openh264") && !repoSpento.MatchString(t) {
			return v
		}
	}
	return ""
}

// accendiRepo: enabled=1/0 di un deposito dnf che c'è già (Fedora: fedora-cisco-openh264, del
// pacchetto fedora-repos).
func (d *deposito) accendiRepo(c *Contesto, id string, acceso bool) error {
	v := "0"
	if acceso {
		v = "1"
	}
	if _, err := os.Stat(c.Amb.P("/usr/bin/dnf5")); err == nil {
		_, err := esegui(c.Amb, 5*time.Minute, "dnf", "config-manager", "setopt", id+".enabled="+v)
		return err
	}
	verbo := "--set-disabled"
	if acceso {
		verbo = "--set-enabled"
	}
	_, err := esegui(c.Amb, 5*time.Minute, "dnf", "config-manager", verbo, id)
	return err
}

func (d *deposito) crb(c *Contesto, acceso bool) error {
	v := "0"
	if acceso {
		v = "1"
	}
	if _, err := os.Stat(c.Amb.P("/usr/bin/dnf5")); err == nil {
		_, err := esegui(c.Amb, 5*time.Minute, "dnf", "config-manager", "setopt", "crb.enabled="+v)
		return err
	}
	verbo := "--set-disabled"
	if acceso {
		verbo = "--set-enabled"
	}
	_, err := esegui(c.Amb, 5*time.Minute, "dnf", "config-manager", verbo, "crb")
	return err
}

// fileArchivio: un file dell'archivio di REMOTIX. presenza: basta che ci sia (la chiave di apt: dopo
// l'installazione la possiede il pacchetto remotix-archive-keyring, che la aggiorna quando la
// sottochiave ruota — il motore non deve vederla come «cambiata da altri»).
type fileArchivio struct {
	percorso, contenuto string
	presenza            bool
}

// fileArchivio: i file dell'archivio di REMOTIX per la famiglia, col loro contenuto (archivio.go).
func (d *deposito) fileArchivio(c *Contesto) []fileArchivio {
	nome := nonVuoto(d.par["nome"], "remotix")
	chiave := d.par["chiave"]
	pacchetti := strings.ReplaceAll(nonVuoto(d.par["pacchetti"], strings.Join(PacchettiArchivio, ",")), ",", " ")
	switch c.Amb.Famiglia {
	case "debian":
		k := ChiaveApt
		r := []fileArchivio{{k, chiave, true}, {"/etc/apt/sources.list.d/" + nome + ".sources",
			"# " + nome + " — aggiunto da remotix-install\nTypes: deb\nURIs: " + d.par["url"] + "\nSuites: " + nonVuoto(d.par["suite"], "stabile") +
				"\nComponents: " + nonVuoto(d.par["componenti"], "main") + "\nSigned-By: " + k + "\n", false}}
		if d.par["host"] != "" {
			// R18: dall'host dell'archivio SOLO i pacchetti di REMOTIX. Il record col nome dei
			// pacchetti viene prima di quello generale (apt usa il primo che corrisponde).
			r = append(r, fileArchivio{"/etc/apt/preferences.d/" + nome + ".pref",
				"# " + nome + " — aggiunto da remotix-install: l'archivio di REMOTIX vale solo per i pacchetti di REMOTIX (R18)\n" +
					"Package: " + pacchetti + "\nPin: origin \"" + d.par["host"] + "\"\nPin-Priority: 500\n\n" +
					"Package: *\nPin: origin \"" + d.par["host"] + "\"\nPin-Priority: -1\n", false})
		} else if strings.HasPrefix(d.par["url"], "file:") {
			// l'archivio LOCALE di un pacchetto fuori linea: un deposito locale non ha un host (per apt
			// «origin» è vuota, come per ogni altro deposito locale). Si lega all'Origin del suo Release,
			// che è firmato con la nostra chiave: vale solo per l'archivio di REMOTIX (R18)
			r = append(r, fileArchivio{"/etc/apt/preferences.d/" + nome + ".pref",
				"# " + nome + " — aggiunto da remotix-install: l'archivio di REMOTIX vale solo per i pacchetti di REMOTIX (R18)\n" +
					"Package: " + pacchetti + "\nPin: release o=REMOTIX\nPin-Priority: 500\n\n" +
					"Package: *\nPin: release o=REMOTIX\nPin-Priority: -1\n", false})
		}
		return r
	case "fedora", "suse":
		k := "/etc/pki/rpm-gpg/RPM-GPG-KEY-" + nome
		dir := "/etc/yum.repos.d/"
		if c.Amb.Famiglia == "suse" {
			dir = "/etc/zypp/repos.d/"
		}
		inc := ""
		if (d.par["host"] != "" || strings.HasPrefix(d.par["url"], "file:")) && c.Amb.Famiglia == "fedora" {
			inc = "includepkgs=" + pacchetti + "\n" // R18: dal nostro archivio solo i nostri pacchetti
		}
		return []fileArchivio{{k, chiave, false}, {dir + nome + ".repo",
			"# " + nome + " — aggiunto da remotix-install\n[" + nome + "]\nname=" + nome + "\nbaseurl=" + d.par["url"] +
				"\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=file://" + k + "\n" + inc, false}}
	case "arch":
		return []fileArchivio{} // il blocco in pacman.conf e pacman-key: archivio.go
	}
	return nil
}

func (d *deposito) scrittori(c *Contesto) ([]*scriviFile, error) {
	var r []*scriviFile
	for _, f := range d.fileArchivio(c) {
		s, err := nuovaScriviFile(AzionePiano{Parametri: map[string]string{"percorso": f.percorso, "contenuto": f.contenuto, "modo": "0644"}})
		if err != nil {
			return nil, err
		}
		r = append(r, s.(*scriviFile))
	}
	if len(r) == 0 && c.Amb.Famiglia != "arch" {
		return nil, Errore("RX-AZIONE-004", "aggiungi-deposito archivio su "+c.Amb.Famiglia)
	}
	return r, nil
}

// sottocontesto: ogni file dell'archivio ha il suo salvataggio.
func sotto(c *Contesto, i int) *Contesto {
	cc := *c
	cc.P.ID = fmt.Sprintf("%s.%d", c.P.ID, i)
	return &cc
}

func chiaviRpm(c *Contesto) (map[string]bool, error) {
	out, _, err := c.Amb.Esegui(time.Minute, "rpm", "-q", "gpg-pubkey", "--qf", `%{NAME}-%{VERSION}-%{RELEASE}\n`)
	if err != nil {
		return nil, err
	}
	r := map[string]bool{}
	for _, x := range strings.Fields(out) {
		if strings.HasPrefix(x, "gpg-pubkey-") {
			r[x] = true
		}
	}
	return r, nil
}

func (d *deposito) Vincoli(c *Contesto) ([]string, error) {
	p, err := d.pezzi(c)
	if err != nil {
		return nil, err
	}
	var v []string
	for k, x := range p {
		v = append(v, "deposito:"+d.tipo+":"+k+"="+siNo(x))
	}
	return v, nil
}

func (d *deposito) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	st, err := d.pezzi(c)
	if err != nil {
		return nil, "", err
	}
	p := primaDeposito{Origine: PREESISTENTE, Tipo: d.tipo, Stato: st}
	for _, v := range st {
		if !v {
			p.Origine = DIRETTA
		}
	}
	if d.tipo == "epel" || d.tipo == "rpmfusion" || d.tipo == "packman" || d.tipo == "openh264" {
		tutti, err := rpmTutti(c)
		if err != nil {
			return nil, "", err
		}
		p.Rpm = tutti
	}
	if d.tipo == "archivio" {
		sc, err := d.scrittori(c)
		if err != nil {
			return nil, "", err
		}
		p.File = map[string]string{}
		for i, s := range sc {
			pf, _, err := s.Fotografa(sotto(c, i))
			if err != nil {
				return nil, "", err
			}
			p.File[s.percorso] = string(pf)
		}
		if c.Amb.Famiglia == "fedora" || c.Amb.Famiglia == "suse" {
			k, err := chiaviRpm(c)
			if err != nil {
				return nil, "", err
			}
			for x := range k {
				p.Chiavi = append(p.Chiavi, x)
			}
		}
	}
	return jsonDi(p), p.Origine, nil
}

func leggiPrimaDeposito(b json.RawMessage) (primaDeposito, error) {
	var p primaDeposito
	err := json.Unmarshal(b, &p)
	return p, err
}

func (d *deposito) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaDeposito(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	adesso, err := d.pezzi(c)
	if err != nil {
		return err
	}
	switch d.tipo {
	case "epel":
		if !adesso["epel-release"] {
			if _, err := esegui(c.Amb, tempoGestore, "dnf", "install", "-y", "epel-release"); err != nil {
				return err
			}
		}
		if err := importaChiavi(c, "epel-release"); err != nil {
			return err
		}
		if !adesso["crb"] {
			return d.crb(c, true)
		}
	case "rpmfusion":
		for _, ramo := range []string{"free", "nonfree"} {
			nome := "rpmfusion-" + ramo + "-release"
			if v, chiesto := adesso[nome]; !chiesto || v {
				continue
			}
			u := URLRpmFusionRamo(c.Amb, ramo)
			arg := []string{"install", "-y", u}
			chiave := "rpmfusion" // il nome nel pacchetto fuori linea: «rpmfusion» (free), «rpmfusion-nonfree»
			if ramo == "nonfree" {
				chiave = "rpmfusion-nonfree"
			}
			if f := FileTerzi(c.Amb, chiave); f != "" {
				// senza rete: lo stesso pacchetto, dal pacchetto fuori linea (verificato col suo sha256
				// quando il pacchetto si è letto); nessun deposito si consulta
				arg = []string{"install", "-y", "--disablerepo=*", f}
			}
			if _, err := esegui(c.Amb, tempoGestore, "dnf", arg...); err != nil {
				return err
			}
		}
		if err := importaChiavi(c, "rpmfusion-free-release"); err != nil {
			return err
		}
		if _, chiesto := adesso["rpmfusion-nonfree-release"]; chiesto {
			return importaChiavi(c, "rpmfusion-nonfree-release")
		}
	case "openh264":
		switch {
		case c.Amb.Famiglia == "suse":
			if !adesso["repo-openh264"] {
				m, _ := OsRelease(c.Amb)
				u := "http://codecs.opensuse.org/openh264/openSUSE_Tumbleweed"
				if strings.Contains(m["ID"], "leap") {
					v, _, _ := strings.Cut(m["VERSION_ID"], ".")
					u = "https://codecs.opensuse.org/openh264/openSUSE_Leap_" + v
				}
				if _, err := esegui(c.Amb, 5*time.Minute, "zypper", "--non-interactive", "addrepo", "-f", u, "repo-openh264"); err != nil {
					return err
				}
				_, err := esegui(c.Amb, tempoGestore, "zypper", "--non-interactive", "--gpg-auto-import-keys", "refresh", "repo-openh264")
				return err
			}
		case d.rhel(c):
			if !adesso[fileCiscoEpel] {
				// il deposito Cisco per EPEL: nessun pacchetto lo configura (epel-release 10 porta solo
				// epel ed epel-testing, `[M]` 30 set). Firmato con la chiave di EPEL, che c'è già
				// (EPEL viene prima: è un deposito di REMOTIX anche lui, su Alma)
				f := c.Amb.P(fileCiscoEpel)
				if err := os.WriteFile(f+".remotix", []byte(ContenutoCiscoEpel(d.majorVersione(c))), 0o644); err != nil {
					return err
				}
				if err := os.Rename(f+".remotix", f); err != nil {
					return err
				}
				if err := importaChiavi(c, "epel-release"); err != nil {
					return err
				}
			}
		default:
			if !adesso["fedora-cisco-openh264"] {
				return d.accendiRepo(c, "fedora-cisco-openh264", true)
			}
		}
	case "packman":
		if !adesso["packman"] {
			m, _ := OsRelease(c.Amb)
			dir := "openSUSE_Tumbleweed"
			if strings.Contains(m["ID"], "leap") {
				dir = "openSUSE_Leap_" + m["VERSION_ID"]
			}
			if _, err := esegui(c.Amb, 5*time.Minute, "zypper", "--non-interactive", "addrepo", "-cfp", "90",
				"https://ftp.gwdg.de/pub/linux/misc/packman/suse/"+dir+"/", "packman"); err != nil {
				return err
			}
			_, err := esegui(c.Amb, tempoGestore, "zypper", "--non-interactive", "--gpg-auto-import-keys", "refresh", "packman")
			return err
		}
	case "archivio":
		sc, err := d.scrittori(c)
		if err != nil {
			return err
		}
		for i, s := range sc {
			if err := s.Fai(sotto(c, i), json.RawMessage(p.File[s.percorso])); err != nil {
				return err
			}
		}
		switch c.Amb.Famiglia {
		case "fedora", "suse":
			if _, err := esegui(c.Amb, time.Minute, "rpm", "--import", sc[0].percorso); err != nil {
				return err
			}
			if c.Amb.Famiglia == "fedora" {
				// repo_gpgcheck: dnf5 verifica i metadati con un portachiavi SUO, e la chiave la importa
				// chiedendo. `[M]` 30 set, fedora44-gnome: con --assumeno (la risoluzione) la domanda ha
				// risposta «no», il deposito si salta e remotix «No match». Qui si risponde sì alla SOLA
				// chiave del file che il motore ha appena scritto (gpgkey=file://…).
				if _, err := esegui(c.Amb, tempoGestore, "dnf", "makecache", "-y", "--repo=remotix"); err != nil {
					return err
				}
			}
		case "arch":
			if !adesso["pacman-key "+d.par["impronta"]] {
				if err := d.mettiChiavePacman(c); err != nil {
					return err
				}
			}
			if err := d.mettiBloccoPacman(c); err != nil {
				return err
			}
			// il SOLO database di REMOTIX (gli altri non si rinfrescano: niente aggiornamento parziale)
			conf, err := ConfSoloRemotix(c.Amb, c.Cartella)
			if err != nil {
				return err
			}
			if _, err := esegui(c.Amb, tempoGestore, "pacman", "--config", conf, "-Sy"); err != nil {
				return err
			}
		}
	}
	return nil
}

func (d *deposito) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	p, err := leggiPrimaDeposito(prima)
	if err != nil {
		return "", "", err
	}
	adesso, err := d.pezzi(c)
	if err != nil {
		return "", "", err
	}
	tutti, comePrima := true, true
	for k, v := range adesso {
		if !v {
			tutti = false
		}
		if v != p.Stato[k] {
			comePrima = false
		}
	}
	switch {
	case tutti:
		return COMPLETO, "deposito " + d.tipo + " presente", nil
	case p.Origine == PREESISTENTE:
		return ESTRANEO, "c'era e qualcuno l'ha tolto", nil
	case comePrima:
		return ASSENTE, "com'era prima", nil
	}
	return A_META, fmt.Sprint(adesso), nil
}

func (d *deposito) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaDeposito(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	adesso, err := d.pezzi(c)
	if err != nil {
		return err
	}
	var chiavi []string
	if d.tipo != "archivio" {
		// PRIMA i pacchetti arrivati col deposito. Quelli che chi resta chiede si TRATTENGONO, e con
		// loro resta anche il DEPOSITO (chi li chiede continua a riceverne gli aggiornamenti): la
		// regola della disinstallazione, la stessa di RX-PACCHETTI-006 in installa-pacchetti. `[M]`
		// 30 set (T10): alma10-kde — ark, dolphin, plasma-desktop… chiedono openh264;
		// fedora44-gnome-iso — libheif e mozilla-openh264. Prima ci si fermava con RX-PACCHETTI-002 e
		// la disinstallazione si annullava.
		var via, resta []string
		via, resta, chiavi, err = d.trattenutiArrivati(c, p)
		if err != nil {
			return err
		}
		if len(via) > 0 {
			if err := (&gestoreDnf{c.Amb}).Togli(via, true); err != nil {
				return err
			}
		}
		if len(resta) > 0 || (d.tipo == "epel" && d.ciscoNostro(c)) {
			return nil // il deposito (e le chiavi) restano: Annullata lo dichiara
		}
	}
	switch d.tipo {
	case "epel":
		if adesso["crb"] && !p.Stato["crb"] {
			if err := d.crb(c, false); err != nil {
				return err
			}
		}
		if adesso["epel-release"] && !p.Stato["epel-release"] {
			if err := (&gestoreDnf{c.Amb}).Togli([]string{"epel-release"}, true); err != nil {
				return err
			}
		}
	case "rpmfusion":
		// prima nonfree (chiede free), poi free
		for _, nome := range []string{"rpmfusion-nonfree-release", "rpmfusion-free-release"} {
			if adesso[nome] && !p.Stato[nome] {
				if err := (&gestoreDnf{c.Amb}).Togli([]string{nome}, true); err != nil {
					return err
				}
			}
		}
	case "openh264":
		switch {
		case c.Amb.Famiglia == "suse":
			if adesso["repo-openh264"] && !p.Stato["repo-openh264"] {
				if _, err := esegui(c.Amb, 5*time.Minute, "zypper", "--non-interactive", "removerepo", "repo-openh264"); err != nil {
					return err
				}
			}
		case d.rhel(c):
			if adesso[fileCiscoEpel] && !p.Stato[fileCiscoEpel] {
				if err := os.Remove(c.Amb.P(fileCiscoEpel)); err != nil && !os.IsNotExist(err) {
					return err
				}
			}
		default:
			if adesso["fedora-cisco-openh264"] && !p.Stato["fedora-cisco-openh264"] {
				if err := d.accendiRepo(c, "fedora-cisco-openh264", false); err != nil {
					return err
				}
			}
		}
	case "packman":
		if adesso["packman"] && !p.Stato["packman"] {
			if _, err := esegui(c.Amb, 5*time.Minute, "zypper", "--non-interactive", "removerepo", "packman"); err != nil {
				return err
			}
		}
	case "archivio":
		sc, err := d.scrittori(c)
		if err != nil {
			return err
		}
		for i := len(sc) - 1; i >= 0; i-- {
			if err := sc[i].Annulla(sotto(c, i), json.RawMessage(p.File[sc[i].percorso])); err != nil {
				return err
			}
		}
		if c.Amb.Famiglia == "arch" {
			if err := d.togliBloccoPacman(c); err != nil {
				return err
			}
			if adesso["pacman-key "+d.par["impronta"]] && !p.Stato["pacman-key "+d.par["impronta"]] {
				if _, err := esegui(c.Amb, time.Minute, "pacman-key", "--delete", d.par["impronta"]); err != nil {
					return err
				}
			}
		}
		if c.Amb.Famiglia == "fedora" || c.Amb.Famiglia == "suse" {
			k, err := chiaviRpm(c)
			if err != nil {
				return err
			}
			prima := map[string]bool{}
			for _, x := range p.Chiavi {
				prima[x] = true
			}
			for x := range k {
				if !prima[x] {
					if _, err := esegui(c.Amb, time.Minute, "rpm", "-e", x); err != nil {
						return err
					}
				}
			}
		}
	}
	// le chiavi importate da dnf al primo uso: dnf non le toglie ([M] 30 set, Alma 10: «remove»
	// esce 0 e le lascia), rpm -e sì
	for _, k := range chiavi {
		if _, err := esegui(c.Amb, time.Minute, "rpm", "-e", k); err != nil {
			return err
		}
	}
	return nil
}

func (d *deposito) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := leggiPrimaDeposito(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "c'era già: non si tocca", nil
	}
	if d.tipo != "archivio" {
		via, resta, _, err := d.trattenutiArrivati(c, p)
		if err != nil {
			return false, "", err
		}
		if len(via) > 0 {
			return false, T("deposito.ancora", len(via), strings.Join(via, ", ")), nil
		}
		if len(resta) > 0 {
			return true, "[RX-PACCHETTI-006] " + T("deposito.trattenuto", d.tipo, strings.Join(resta, ", ")), nil
		}
		if d.tipo == "epel" && d.ciscoNostro(c) {
			return true, "[RX-PACCHETTI-006] " + T("deposito.resta_epel"), nil
		}
	}
	adesso, err := d.pezzi(c)
	if err != nil {
		return false, "", err
	}
	for k, v := range adesso {
		if v && !p.Stato[k] {
			return false, k + " c'è ancora", nil
		}
	}
	return true, "com'era prima", nil
}

// Indirette: un deposito di terzi tolto non toglie quel che se n'è preso (§6.6.4).
func (d *deposito) Indirette(prima json.RawMessage) []string {
	if d.tipo == "archivio" {
		return nil
	}
	return []string{T("ind.deposito", d.tipo)}
}

// rpmTutti: i pacchetti installati per NOME; le chiavi (tutte «gpg-pubkey») per nome-versione-rilascio.
func rpmTutti(c *Contesto) ([]string, error) {
	out, err := esegui(c.Amb, time.Minute, "rpm", "-qa", "--qf", `%{NAME} %{VERSION}-%{RELEASE}\n`)
	if err != nil {
		return nil, err
	}
	var r []string
	for _, riga := range strings.Split(out, "\n") {
		f := strings.Fields(riga)
		switch {
		case len(f) != 2:
		case f[0] == "gpg-pubkey":
			r = append(r, f[0]+"-"+f[1])
		default:
			r = append(r, f[0])
		}
	}
	return r, nil
}

// arrivati: i pacchetti arrivati col deposito (non c'erano prima) e ancora installati, e le chiavi
// gpg-pubkey importate da dnf al primo uso.
func (d *deposito) arrivati(c *Contesto, p primaDeposito) (nuovi, chiavi []string, err error) {
	if p.Rpm == nil {
		return nil, nil, nil
	}
	adesso, err := rpmTutti(c)
	if err != nil {
		return nil, nil, err
	}
	prima := map[string]bool{}
	for _, x := range p.Rpm {
		prima[x] = true
	}
	for _, x := range adesso {
		switch {
		case prima[x]:
		case strings.HasPrefix(x, "gpg-pubkey-"):
			chiavi = append(chiavi, x) // [M] 30 set: zypper --gpg-auto-import-keys importa quella di Packman
		case d.tipo == "packman" || (d.tipo == "openh264" && c.Amb.Famiglia == "suse"):
			// Packman (e il deposito OpenH264 di openSUSE) non porta pacchetti da sé: quel che c'è di
			// nuovo l'ha portato altro, e zypper non è gestoreDnf
		default:
			nuovi = append(nuovi, x)
		}
	}
	return nuovi, chiavi, nil
}

// trattenutiArrivati: degli arrivati, quelli che si tolgono («via») e quelli che RESTANO perché li
// chiede qualcosa che resta (la simulazione del gestore, come `trattenuti` di installa-pacchetti).
// Se ne resta uno, resta anche il deposito: lo decide Annulla, lo dichiara Annullata.
func (d *deposito) trattenutiArrivati(c *Contesto, p primaDeposito) (via, resta, chiavi []string, err error) {
	nuovi, chiavi, err := d.arrivati(c, p)
	if err != nil || len(nuovi) == 0 {
		return nil, nil, chiavi, err
	}
	via, resta, err = trattenuti(&gestoreDnf{c.Amb}, nuovi, nuovi, true)
	return via, resta, chiavi, err
}

// ciscoNostro: il file del deposito Cisco per EPEL c'è ed è il nostro (trattenuto con i suoi
// pacchetti): la sua chiave è quella di epel-release, che allora resta anche lui.
func (d *deposito) ciscoNostro(c *Contesto) bool {
	b, err := os.ReadFile(c.Amb.P(fileCiscoEpel))
	return err == nil && strings.HasPrefix(string(b), "# epel-cisco-openh264 — aggiunto da remotix-install")
}

// importaChiavi: le chiavi che il pacchetto del deposito porta (/etc/pki/rpm-gpg/…) si importano in
// rpm SUBITO: i pacchetti del deposito il motore li installa dalla sua cartella, e dnf li verifica
// solo se la chiave è già nell'archivio ([M] 30 set, fedora44-gnome: «The repository does not have
// any OpenPGP keys configured»). Si tolgono all'annullamento (togliArrivati, rpm -e).
func importaChiavi(c *Contesto, pacchetto string) error {
	out, err := esegui(c.Amb, time.Minute, "rpm", "-ql", pacchetto)
	if err != nil {
		return err
	}
	for _, f := range strings.Fields(out) {
		if strings.HasPrefix(f, "/etc/pki/rpm-gpg/") && strings.Contains(f, "RPM-GPG-KEY") && !strings.HasSuffix(f, "/") {
			if st, e := os.Stat(c.Amb.P(f)); e != nil || st.IsDir() {
				continue
			}
			if _, err := esegui(c.Amb, time.Minute, "rpm", "--import", f); err != nil {
				return err
			}
		}
	}
	return nil
}
