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
//     ESATTA: due file (e la chiave in rpm), tolti come non c'erano. pacman: non ancora fatto.
//   - «epel» (Alma/RHEL, KDE), «rpmfusion» (Fedora, Alma: H.264), «packman» (openSUSE: H.264):
//     archivi di TERZI, col consenso (D5, riga sua). AL_MEGLIO: il deposito si toglie, ma i
//     pacchetti presi da lì e gli aggiornamenti restano (si dichiara).
//
// parametri: tipo; per «archivio»: nome, url, chiave (il testo della chiave pubblica, armatura
// ASCII), suite, componenti.

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
	case "archivio", "epel", "rpmfusion", "packman":
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
		v, err := rpmVersioni(c.Amb, []string{"rpmfusion-free-release"})
		if err != nil {
			return nil, err
		}
		r["rpmfusion-free-release"] = v["rpmfusion-free-release"] != ""
	case "packman":
		_, err := os.Stat(c.Amb.P("/etc/zypp/repos.d/packman.repo"))
		r["packman"] = err == nil
	case "archivio":
		for _, f := range d.fileArchivio(c) {
			sha, _ := Sha256File(c.Amb.P(f.percorso))
			r[f.percorso] = sha == Sha256([]byte(f.contenuto))
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

type fileArchivio struct{ percorso, contenuto string }

// fileArchivio: i due file dell'archivio di REMOTIX per la famiglia, col loro contenuto.
func (d *deposito) fileArchivio(c *Contesto) []fileArchivio {
	nome := nonVuoto(d.par["nome"], "remotix")
	chiave := d.par["chiave"]
	switch c.Amb.Famiglia {
	case "debian":
		k := "/usr/share/keyrings/" + nome + "-archive-keyring.asc"
		return []fileArchivio{{k, chiave}, {"/etc/apt/sources.list.d/" + nome + ".sources",
			"# " + nome + " — aggiunto da remotix-install\nTypes: deb\nURIs: " + d.par["url"] + "\nSuites: " + nonVuoto(d.par["suite"], "stabile") +
				"\nComponents: " + nonVuoto(d.par["componenti"], "main") + "\nSigned-By: " + k + "\n"}}
	case "fedora", "suse":
		k := "/etc/pki/rpm-gpg/RPM-GPG-KEY-" + nome
		dir := "/etc/yum.repos.d/"
		if c.Amb.Famiglia == "suse" {
			dir = "/etc/zypp/repos.d/"
		}
		return []fileArchivio{{k, chiave}, {dir + nome + ".repo",
			"# " + nome + " — aggiunto da remotix-install\n[" + nome + "]\nname=" + nome + "\nbaseurl=" + d.par["url"] +
				"\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=file://" + k + "\n"}}
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
	if len(r) == 0 {
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
	if d.tipo == "epel" || d.tipo == "rpmfusion" {
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
		if c.Amb.Famiglia != "debian" {
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
		if !adesso["crb"] {
			return d.crb(c, true)
		}
	case "rpmfusion":
		if !adesso["rpmfusion-free-release"] {
			u := "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-" + d.majorVersione(c) + ".noarch.rpm"
			if d.rhel(c) {
				u = "https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-" + d.majorVersione(c) + ".noarch.rpm"
			}
			_, err := esegui(c.Amb, tempoGestore, "dnf", "install", "-y", u)
			return err
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
		if c.Amb.Famiglia != "debian" {
			if _, err := esegui(c.Amb, time.Minute, "rpm", "--import", sc[0].percorso); err != nil {
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
		return d.togliArrivati(c, p)
	case "rpmfusion":
		if adesso["rpmfusion-free-release"] && !p.Stato["rpmfusion-free-release"] {
			if err := (&gestoreDnf{c.Amb}).Togli([]string{"rpmfusion-free-release"}, true); err != nil {
				return err
			}
		}
		return d.togliArrivati(c, p)
	case "packman":
		if adesso["packman"] && !p.Stato["packman"] {
			_, err := esegui(c.Amb, 5*time.Minute, "zypper", "--non-interactive", "removerepo", "packman")
			return err
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
		if c.Amb.Famiglia != "debian" {
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

// togliArrivati: i pacchetti arrivati col deposito (e non c'erano prima) si tolgono, coi controlli
// di Togli (se toglierli portasse via altro, ci si ferma).
func (d *deposito) togliArrivati(c *Contesto, p primaDeposito) error {
	if p.Rpm == nil {
		return nil
	}
	adesso, err := rpmTutti(c)
	if err != nil {
		return err
	}
	prima := map[string]bool{}
	for _, x := range p.Rpm {
		prima[x] = true
	}
	var nuovi, chiavi []string
	for _, x := range adesso {
		switch {
		case prima[x]:
		case strings.HasPrefix(x, "gpg-pubkey-"):
			chiavi = append(chiavi, x)
		default:
			nuovi = append(nuovi, x)
		}
	}
	if len(nuovi) > 0 {
		if err := (&gestoreDnf{c.Amb}).Togli(nuovi, true); err != nil {
			return err
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
