package motore

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Aggiornatore: quel che l'aggiornamento automatico (e il ritorno indietro, R11) chiede al gestore
// di pacchetti della famiglia, e SOLO per l'archivio di REMOTIX (DECISIONI §10.10: è il gestore di
// pacchetti che aggiorna; il motore non scarica né sostituisce file da sé).
type Aggiornatore interface {
	// Rinfresca i metadati del SOLO archivio di REMOTIX (gli altri depositi non si toccano: il
	// timer non deve fare da aggiornatore della macchina). Il gestore verifica la firma
	// dell'archivio (catena B): un archivio alterato è un errore qui (R17).
	Rinfresca(archivio string) error
	// Disponibili: le versioni di ogni pacchetto che l'archivio (o la cache, per pacman) offre.
	Disponibili(nomi []string, archivio string) (map[string][]string, error)
	// Prepara: risolve e scarica la transazione verso le versioni volute (anche più vecchie) e ne
	// dà l'insieme risolto; niente è installato.
	Prepara(cache string, voluti map[string]string, archivio string) ([]Artefatto, error)
	// Porta: installa esattamente quelle versioni (aggiornando o tornando indietro).
	Porta(cache string, voluti map[string]string, archivio string) error
}

// ScegliAggiornatore: quello della famiglia (nil se la famiglia non è ancora fatta: openSUSE).
func ScegliAggiornatore(a *Ambiente) Aggiornatore {
	switch a.Famiglia {
	case "debian":
		return &aggApt{a}
	case "fedora":
		return &aggDnf{a}
	case "arch":
		return &aggPacman{a}
	}
	return nil
}

func ordinaVersioni(fam string, v []string) {
	sort.Slice(v, func(i, j int) bool { return ConfrontaPacchetti(fam, v[i], v[j]) < 0 })
}

func chiaviOrdinate(m map[string]string) []string {
	var k []string
	for x := range m {
		k = append(k, x)
	}
	sort.Strings(k)
	return k
}

// ---------------------------------------------------------------- apt

type aggApt struct{ a *Ambiente }

// soloRemotix: le opzioni che fanno leggere ad apt il SOLO deposito di REMOTIX (una cartella con il
// suo .sources), e List-Cleanup=0 perché apt non butti gli elenchi degli altri depositi.
func (g *aggApt) soloRemotix() ([]string, func(), error) {
	d, err := os.MkdirTemp(g.a.P("/run"), "remotix-install-apt-")
	if err != nil {
		return nil, nil, err
	}
	b, err := os.ReadFile(g.a.P("/etc/apt/sources.list.d/remotix.sources"))
	if err == nil {
		err = os.WriteFile(filepath.Join(d, "remotix.sources"), b, 0o644)
	}
	if err != nil {
		os.RemoveAll(d)
		return nil, nil, err
	}
	dentro := strings.TrimPrefix(d, strings.TrimSuffix(g.a.P("/"), "/"))
	return []string{"-o", "Dir::Etc::SourceList=/dev/null", "-o", "Dir::Etc::SourceParts=" + dentro, "-o", "APT::Get::List-Cleanup=0"},
		func() { os.RemoveAll(d) }, nil
}

func (g *aggApt) Rinfresca(archivio string) error {
	o, via, err := g.soloRemotix()
	if err != nil {
		return err
	}
	defer via()
	out, c, err := g.a.Esegui(tempoGestore, "apt-get", append(o, "update")...)
	if err != nil {
		return err
	}
	// apt esce 0 anche se un deposito non si verifica («W: … is not signed», «E: The repository …
	// is not signed» su versioni vecchie): si guarda il testo
	if c != 0 || regexp.MustCompile(`(?m)^(E:|W: GPG error|W: .*(not signed|NO_PUBKEY|BADSIG|Hash Sum mismatch|File has unexpected size))`).MatchString(out) {
		return Errore("RX-AGG-007", ultimeRighe(out, 4))
	}
	return nil
}

// «   remotix | 0.17.0-2+deb13 | http://10.0.2.2:8717/deb debian13-stabile/main amd64 Packages»
var aptMadison = regexp.MustCompile(`^\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s`)

func (g *aggApt) Disponibili(nomi []string, archivio string) (map[string][]string, error) {
	out, err := esegui(g.a, time.Minute, "apt-cache", append([]string{"madison"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	r := map[string][]string{}
	for _, riga := range strings.Split(out, "\n") {
		if m := aptMadison.FindStringSubmatch(riga); m != nil && strings.HasPrefix(m[3], strings.TrimRight(archivio, "/")) {
			r[m[1]] = append(r[m[1]], m[2])
		}
	}
	for n := range r {
		ordinaVersioni("debian", r[n])
	}
	return r, nil
}

func aptVoluti(v map[string]string) []string {
	var r []string
	for _, n := range chiaviOrdinate(v) {
		r = append(r, n+"="+v[n])
	}
	return r
}

func (g *aggApt) Prepara(cache string, voluti map[string]string, archivio string) ([]Artefatto, error) {
	arg := append(append([]string{"-s", "install", "--allow-downgrades"}, aptOpzioni...), aptVoluti(voluti)...)
	out, err := esegui(g.a, tempoGestore, "apt-get", arg...)
	if err != nil {
		return nil, Errore("RX-AGG-009", ultimeRighe(out, 3))
	}
	var r []Artefatto
	for _, riga := range strings.Split(out, "\n") {
		if strings.HasPrefix(riga, "Remv ") || strings.HasPrefix(riga, "Purg ") {
			return nil, fmt.Errorf("la transazione toglierebbe un pacchetto: %s", riga)
		}
		m := aptInst.FindStringSubmatch(riga)
		if m == nil {
			continue
		}
		a := Artefatto{Nome: m[1], Versione: m[3], Arch: m[5], Origine: m[4], Esito: "nuovo"}
		if m[2] != "" {
			a.Esito, a.Prima = "aggiornato", m[2]
			if confrontaDeb(m[3], m[2]) < 0 {
				a.Esito = "retrocesso"
			}
		}
		r = append(r, a)
	}
	if _, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"install", "--download-only", "--allow-downgrades"}, aptOpzioni...), aptVoluti(voluti)...)...); err != nil {
		return nil, err
	}
	for i := range r {
		a := &r[i]
		a.File = filepath.Join("/var/cache/apt/archives", a.Nome+"_"+strings.ReplaceAll(a.Versione, ":", "%3a")+"_"+a.Arch+".deb")
		a.Sha256, _ = Sha256File(g.a.P(a.File))
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

func (g *aggApt) Porta(cache string, voluti map[string]string, archivio string) error {
	_, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"install", "--allow-downgrades"}, aptOpzioni...), aptVoluti(voluti)...)...)
	return err
}

// ---------------------------------------------------------------- dnf

type aggDnf struct{ a *Ambiente }

func (g *aggDnf) Rinfresca(archivio string) error {
	out, c, err := g.a.Esegui(tempoGestore, "dnf", "makecache", "--repo=remotix", "--refresh")
	if err != nil {
		return err
	}
	if c != 0 {
		return Errore("RX-AGG-007", ultimeRighe(out, 4))
	}
	return nil
}

func (g *aggDnf) Disponibili(nomi []string, archivio string) (map[string][]string, error) {
	out, err := esegui(g.a, tempoGestore, "dnf", append([]string{"repoquery", "-C", "--repo=remotix", "--queryformat", "RX %{name} %{evr}\n"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	r := map[string][]string{}
	visti := map[string]bool{}
	for _, riga := range strings.Split(out, "\n") {
		f := strings.Fields(riga)
		if len(f) == 3 && f[0] == "RX" && !visti[f[1]+" "+f[2]] {
			visti[f[1]+" "+f[2]] = true
			r[f[1]] = append(r[f[1]], strings.TrimPrefix(f[2], "0:"))
		}
	}
	for n := range r {
		ordinaVersioni("fedora", r[n])
	}
	return r, nil
}

func (g *aggDnf) cartella(cache string) string { return filepath.Join(cache, "rpm") }

func (g *aggDnf) Prepara(cache string, voluti map[string]string, archivio string) ([]Artefatto, error) {
	d := g.cartella(cache)
	os.RemoveAll(g.a.P(d))
	if err := os.MkdirAll(g.a.P(d), 0o700); err != nil {
		return nil, err
	}
	var nevr []string
	for _, n := range chiaviOrdinate(voluti) {
		nevr = append(nevr, n+"-"+voluti[n])
	}
	if out, err := esegui(g.a, tempoGestore, "dnf", append([]string{"download", "--repo=remotix", "--destdir", d}, nevr...)...); err != nil {
		return nil, Errore("RX-AGG-009", ultimeRighe(out, 3)+" "+err.Error())
	}
	prima, err := rpmVersioni(g.a, chiaviOrdinate(voluti))
	if err != nil {
		return nil, err
	}
	voci, _ := filepath.Glob(g.a.P(d) + "/*.rpm")
	var r []Artefatto
	for _, v := range voci {
		out, err := esegui(g.a, time.Minute, "rpm", "-qp", "--qf", `RX %{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n`, v)
		if err != nil {
			return nil, err
		}
		for _, riga := range strings.Split(out, "\n") {
			f := strings.Fields(riga)
			if len(f) != 4 || f[0] != "RX" {
				continue
			}
			sha, _ := Sha256File(v)
			a := Artefatto{Nome: f[1], Versione: f[2], Arch: f[3], Origine: "remotix", Sha256: sha, Esito: "nuovo",
				File: strings.TrimPrefix(v, strings.TrimSuffix(g.a.P("/"), "/"))}
			if p := prima[f[1]]; p != "" {
				a.Esito, a.Prima = "aggiornato", p
				if confrontaRpm(f[2], p) < 0 {
					a.Esito = "retrocesso"
				}
			}
			r = append(r, a)
		}
	}
	if len(r) != len(voluti) {
		return nil, Errore("RX-AGG-009", fmt.Sprintf("scaricati %d pacchetti su %d", len(r), len(voluti)))
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

// Porta: i file scaricati e verificati, con la firma controllata da rpm (localpkg_gpgcheck=1: la
// chiave l'ha importata aggiungi-deposito); «downgrade» per quelli che tornano indietro (R11).
func (g *aggDnf) Porta(cache string, voluti map[string]string, archivio string) error {
	ins, err := g.Prepara(cache, voluti, archivio)
	if err != nil {
		return err
	}
	var su, giu []string
	for _, a := range ins {
		switch a.Esito {
		case "retrocesso":
			giu = append(giu, a.File)
		default:
			su = append(su, a.File)
		}
	}
	if len(giu) > 0 {
		if _, err := esegui(g.a, tempoGestore, "dnf", append([]string{"downgrade", "-y", "--setopt=localpkg_gpgcheck=1"}, giu...)...); err != nil {
			return err
		}
	}
	if len(su) > 0 {
		if _, err := esegui(g.a, tempoGestore, "dnf", append([]string{"install", "-y", "--setopt=localpkg_gpgcheck=1"}, su...)...); err != nil {
			return err
		}
	}
	return nil
}

// ---------------------------------------------------------------- pacman

type aggPacman struct{ a *Ambiente }

func (g *aggPacman) Rinfresca(archivio string) error {
	d, err := os.MkdirTemp(g.a.P("/run"), "remotix-install-pacman-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(d)
	conf, err := ConfSoloRemotix(g.a, d)
	if err != nil {
		return err
	}
	dentro := strings.TrimPrefix(conf, strings.TrimSuffix(g.a.P("/"), "/"))
	out, c, err := g.a.Esegui(tempoGestore, "pacman", "--config", dentro, "-Sy")
	if err != nil {
		return err
	}
	if c != 0 {
		return Errore("RX-AGG-007", ultimeRighe(out, 4))
	}
	return nil
}

// Disponibili: il database di pacman ha UNA versione per pacchetto (la più nuova del canale); le
// vecchie sono nella cache di pacman (/var/cache/pacman/pkg) e nell'archivio, per nome di file.
func (g *aggPacman) Disponibili(nomi []string, archivio string) (map[string][]string, error) {
	out, err := esegui(g.a, time.Minute, "pacman", "-Sl", "remotix")
	if err != nil {
		return nil, err
	}
	voluti := map[string]bool{}
	for _, n := range nomi {
		voluti[n] = true
	}
	r := map[string][]string{}
	for _, riga := range strings.Split(out, "\n") {
		f := strings.Fields(riga)
		if len(f) >= 3 && f[0] == "remotix" && voluti[f[1]] {
			r[f[1]] = append(r[f[1]], f[2])
		}
	}
	for n := range voluti {
		voci, _ := filepath.Glob(g.a.P("/var/cache/pacman/pkg") + "/" + n + "-*.pkg.tar.zst")
		re := regexp.MustCompile("^" + regexp.QuoteMeta(n) + `-([^-]+-[^-]+)-[^-]+\.pkg\.tar\.zst$`)
		for _, v := range voci {
			if m := re.FindStringSubmatch(filepath.Base(v)); m != nil && !contiene(r[n], m[1]) {
				r[n] = append(r[n], m[1])
			}
		}
		ordinaVersioni("arch", r[n])
	}
	return r, nil
}

func contiene(l []string, x string) bool {
	for _, y := range l {
		if y == x {
			return true
		}
	}
	return false
}

// fonte: il pacchetto di una versione — dalla cache se c'è (il ritorno indietro «pacman -U dalla
// cache»), altrimenti dall'archivio (le versioni vecchie restano lì, con la loro .sig).
func (g *aggPacman) fonte(n, v, archivio string) string {
	f := "/var/cache/pacman/pkg/" + n + "-" + v + "-x86_64.pkg.tar.zst"
	if _, err := os.Stat(g.a.P(f)); err == nil {
		return f
	}
	return strings.TrimRight(archivio, "/") + "/" + n + "-" + v + "-x86_64.pkg.tar.zst"
}

func (g *aggPacman) Prepara(cache string, voluti map[string]string, archivio string) ([]Artefatto, error) {
	disp, err := g.Disponibili(chiaviOrdinate(voluti), archivio)
	if err != nil {
		return nil, err
	}
	prima, err := (&gestorePacman{g.a}).Versioni(chiaviOrdinate(voluti))
	if err != nil {
		return nil, err
	}
	var perS []string
	var r []Artefatto
	for _, n := range chiaviOrdinate(voluti) {
		v := voluti[n]
		a := Artefatto{Nome: n, Versione: v, Arch: "x86_64", Origine: "remotix", Esito: "nuovo"}
		if p := prima[n]; p != "" {
			a.Esito, a.Prima = "aggiornato", p
			if confrontaRpm(v, p) < 0 {
				a.Esito = "retrocesso"
			}
		}
		if l := disp[n]; len(l) > 0 && l[len(l)-1] == v && !strings.HasPrefix(g.fonte(n, v, archivio), "/") {
			perS = append(perS, n) // la versione del database: pacman -S
		}
		a.File = g.fonte(n, v, archivio)
		r = append(r, a)
	}
	if len(perS) > 0 {
		// ⛔ niente aggiornamento parziale: la transazione deve toccare SOLO pacchetti di REMOTIX
		out, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-S", "--print", "--print-format", "%n %v %r"}, perS...)...)
		if err != nil {
			return nil, err
		}
		for _, riga := range strings.Split(out, "\n") {
			f := strings.Fields(riga)
			if len(f) == 3 && f[2] != "remotix" {
				return nil, Errore("RX-AGG-008", riga)
			}
		}
		if _, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-Sw", "--noconfirm"}, perS...)...); err != nil {
			return nil, err
		}
		for i := range r {
			r[i].File = g.fonte(r[i].Nome, r[i].Versione, archivio)
		}
	}
	for i := range r {
		if strings.HasPrefix(r[i].File, "/") {
			r[i].Sha256, _ = Sha256File(g.a.P(r[i].File))
		}
	}
	return r, nil
}

// Porta: pacman -U dei file (dalla cache, o dall'archivio: pacman scarica anche la .sig e la
// verifica, RemoteFileSigLevel = Required).
func (g *aggPacman) Porta(cache string, voluti map[string]string, archivio string) error {
	ins, err := g.Prepara(cache, voluti, archivio)
	if err != nil {
		return err
	}
	var f []string
	for _, a := range ins {
		f = append(f, a.File)
	}
	_, err = esegui(g.a, tempoGestore, "pacman", append([]string{"-U", "--noconfirm"}, f...)...)
	return err
}
