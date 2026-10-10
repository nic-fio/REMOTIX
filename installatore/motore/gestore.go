package motore

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Il gestore di pacchetti della distribuzione (§6.0, regola 1): è LUI che mette e toglie i file
// dei pacchetti; il motore decide, chiede, controlla e annulla. Il motore lo lancia dall'elenco
// chiuso (ambiente.go), mai una shell.
//
// L'insieme risolto (§6.6.6): Risolvi simula la transazione, scarica tutto e verifica, e dà
// l'elenco esatto (nome, versione, architettura, origine, sha256, e che cosa succede: nuovo,
// aggiornato da…, già presente). Installa installa ESATTAMENTE quello, dalla cache, senza
// scaricare niente al momento. Togli simula prima e rifiuta se toglierebbe qualcosa che non è
// nell'elenco (un pacchetto di altri che nel frattempo ne dipende).
//
// Provati sulle VM: apt (Debian 13) e dnf (Alma 10). zypper e pacman sono scritti con la stessa
// forma ma NON ancora provati su una macchina vera.

// Artefatto: una riga dell'insieme risolto.
type Artefatto struct {
	Nome     string `json:"nome"`
	Versione string `json:"versione"`
	Arch     string `json:"arch,omitempty"`
	Origine  string `json:"origine"`          // "file" (dal piano) o il deposito
	File     string `json:"file,omitempty"`   // il file nella cache
	Sha256   string `json:"sha256,omitempty"` // del file nella cache
	Esito    string `json:"esito"`            // "nuovo" · "aggiornato" · "presente"
	Prima    string `json:"prima,omitempty"`  // la versione di prima, se aggiornato
}

// Gestore: il gestore di pacchetti della famiglia.
type Gestore interface {
	Nome() string
	// Versioni: la versione installata per ogni nome ("" = non installato).
	Versioni(nomi []string) (map[string]string, error)
	// Risolvi: simula, scarica nella cache, verifica. file = pacchetti locali (percorsi nella cache
	// dell'operazione), nomi = pacchetti dai depositi.
	Risolvi(cache string, file, nomi []string) ([]Artefatto, error)
	// Installa l'insieme risolto dalla cache, senza scaricare.
	Installa(cache string, file, nomi []string) error
	// SimulaTogli: che cosa toglierebbe il gestore OLTRE ai nomi dati (chi ne dipende), senza
	// toccare niente.
	SimulaTogli(nomi []string, purge bool) ([]string, error)
	// Togli i nomi dati, e solo quelli (purge: anche la configurazione): se ne toglierebbe altri,
	// RX-PACCHETTI-002 e niente tolto.
	Togli(nomi []string, purge bool) error
	// Integro: il gestore non è a metà di una transazione.
	Integro() (bool, string, error)
	// Ripara: il rimedio del gestore stesso dopo un'interruzione (§6.6.3).
	Ripara() error
}

// ScegliGestore: quello della famiglia.
func ScegliGestore(a *Ambiente, fam string) Gestore {
	switch fam {
	case "debian":
		return &gestoreApt{a}
	case "fedora":
		return &gestoreDnf{a}
	case "suse":
		return &gestoreZypper{a: a}
	case "arch":
		return &gestorePacman{a}
	}
	return nil
}

func esegui(a *Ambiente, tempo time.Duration, nome string, arg ...string) (string, error) {
	out, c, err := a.Esegui(tempo, nome, arg...)
	if err != nil {
		return out, err
	}
	if c != 0 {
		return out, fmt.Errorf("%s %s: uscita %d: %s", nome, strings.Join(arg, " "), c, ultimeRighe(out, 6))
	}
	return out, nil
}

func ultimeRighe(s string, n int) string {
	r := strings.Split(strings.TrimSpace(s), "\n")
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return strings.Join(r, " | ")
}

const tempoGestore = 45 * time.Minute

// ---------------------------------------------------------------- apt (Debian, Ubuntu)

type gestoreApt struct{ a *Ambiente }

func (g *gestoreApt) Nome() string { return "apt" }

var aptOpzioni = []string{"-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold", "-o", "APT::Get::Assume-Yes=true"}

func (g *gestoreApt) Versioni(nomi []string) (map[string]string, error) {
	pk := ArchivioPacchetti(g.a, "debian", nomi)
	if !pk.letto {
		return nil, errors.New("the dpkg database cannot be read")
	}
	r := map[string]string{}
	for _, n := range nomi {
		r[n] = pk.versioni[n]
	}
	return r, nil
}

// «Inst nome [vecchia] (nuova deposito [arch])»
var aptInst = regexp.MustCompile(`^Inst (\S+)(?: \[(\S+)\])? \((\S+) (.*?) \[(\S+)\]\)`)

func (g *gestoreApt) argomenti(file, nomi []string) []string {
	return append(append([]string{}, file...), nomi...)
}

func (g *gestoreApt) Risolvi(cache string, file, nomi []string) ([]Artefatto, error) {
	sim := func() (string, error) {
		return esegui(g.a, tempoGestore, "apt-get", append(append([]string{"-s", "install"}, aptOpzioni...), g.argomenti(file, nomi)...)...)
	}
	out, err := sim()
	if err != nil { // elenchi vecchi: si aggiornano (i metadati firmati dei depositi) e si riprova
		if _, e2 := esegui(g.a, tempoGestore, "apt-get", "update"); e2 != nil {
			return nil, err
		}
		if out, err = sim(); err != nil {
			return nil, err
		}
	}
	var r []Artefatto
	for _, riga := range strings.Split(out, "\n") {
		if strings.HasPrefix(riga, "Remv ") || strings.HasPrefix(riga, "Purg ") {
			return nil, fmt.Errorf("the transaction would remove a package: %s", riga)
		}
		m := aptInst.FindStringSubmatch(riga)
		if m == nil {
			continue
		}
		a := Artefatto{Nome: m[1], Versione: m[3], Arch: m[5], Origine: m[4], Esito: "nuovo"}
		if m[2] != "" {
			a.Esito, a.Prima = "aggiornato", m[2]
		}
		r = append(r, a)
	}
	// scaricare tutto PRIMA di toccare (§6.0 punto 4): apt verifica ogni file contro i metadati firmati
	if _, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"install", "--download-only"}, aptOpzioni...), g.argomenti(file, nomi)...)...); err != nil {
		return nil, err
	}
	locali := map[string]string{}
	for _, f := range file {
		n, v, e := g.intestazione(f)
		if e == nil {
			locali[n+" "+v] = f
		}
	}
	for i := range r {
		a := &r[i]
		if f, ok := locali[a.Nome+" "+a.Versione]; ok {
			a.Origine, a.File = "file", f
		} else {
			a.File = filepath.Join("/var/cache/apt/archives", a.Nome+"_"+strings.ReplaceAll(a.Versione, ":", "%3a")+"_"+a.Arch+".deb")
		}
		sha, err := Sha256File(g.a.P(a.File))
		if err != nil || sha == "" {
			return nil, fmt.Errorf("%s: the downloaded file is missing (%v)", a.File, err)
		}
		a.Sha256 = sha
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

// intestazione di un .deb locale (nome, versione), letta con dpkg-deb.
func (g *gestoreApt) intestazione(f string) (string, string, error) {
	out, err := esegui(g.a, time.Minute, "dpkg-deb", "-W", "--showformat=${Package} ${Version}", f)
	if err != nil {
		return "", "", err
	}
	c := strings.Fields(out)
	if len(c) != 2 {
		return "", "", fmt.Errorf("dpkg-deb: %q", out)
	}
	return c[0], c[1], nil
}

// Installa: tutto è già nella cache di apt (Risolvi l'ha scaricato e verificato), e apt non
// riscarica quel che c'è. ⚠ `--no-download` NON si può usare: con un .deb locale apt 3.0 si ferma
// con «Internal Error, Pathname to install is not absolute» ([M] 30 set, Debian 13). Che sia
// proprio l'insieme risolto lo garantisce «controlla», che confronta ogni versione.
func (g *gestoreApt) Installa(cache string, file, nomi []string) error {
	_, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"install"}, aptOpzioni...), g.argomenti(file, nomi)...)...)
	return err
}

var aptTogli = regexp.MustCompile(`^(?:Remv|Purg) (\S+)`)

func aptVerbo(purge bool) string {
	if purge {
		return "purge"
	}
	return "remove"
}

func (g *gestoreApt) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	out, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{"-s", aptVerbo(purge)}, aptOpzioni...), nomi...)...)
	if err != nil {
		return nil, err
	}
	var altri []string
	for _, riga := range strings.Split(out, "\n") {
		if m := aptTogli.FindStringSubmatch(riga); m != nil {
			altri = append(altri, m[1])
		}
	}
	return fuoriDa(altri, nomi), nil
}

func (g *gestoreApt) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	_, err := esegui(g.a, tempoGestore, "apt-get", append(append([]string{aptVerbo(purge)}, aptOpzioni...), nomi...)...)
	return err
}

// fuoriDa: i nomi di «tutti» che non sono in «nomi» (senza ripetizioni). Una chiave rpm si toglie
// per versione (gpg-pubkey-…), e dnf la mostra per nome.
func fuoriDa(tutti, nomi []string) []string {
	nostri := map[string]bool{}
	for _, n := range nomi {
		nostri[n] = true
		if strings.HasPrefix(n, "gpg-pubkey-") {
			nostri["gpg-pubkey"] = true
		}
	}
	var r []string
	for _, n := range tutti {
		if !nostri[n] {
			nostri[n] = true
			r = append(r, n)
		}
	}
	return r
}

// soloLoro: la guardia di Togli — il gestore toglierebbe soltanto i nomi dati.
func soloLoro(g Gestore, nomi []string, purge bool) error {
	altri, err := g.SimulaTogli(nomi, purge)
	if err != nil {
		return err
	}
	if len(altri) > 0 {
		return Errore("RX-PACCHETTI-002", strings.Join(altri, ", "))
	}
	return nil
}

func (g *gestoreApt) Integro() (bool, string, error) {
	out, c, err := g.a.Esegui(time.Minute, "dpkg", "--audit")
	if err != nil {
		return false, "", err
	}
	if c != 0 || strings.TrimSpace(out) != "" {
		return false, ultimeRighe(out, 3), nil
	}
	return true, "", nil
}

func (g *gestoreApt) Ripara() error {
	_, err := esegui(g.a, tempoGestore, "dpkg", "--configure", "-a")
	return err
}

// ---------------------------------------------------------------- dnf (Fedora, RHEL, Alma)

type gestoreDnf struct{ a *Ambiente }

func (g *gestoreDnf) Nome() string { return "dnf" }

func rpmVersioni(a *Ambiente, nomi []string) (map[string]string, error) {
	r := map[string]string{}
	if len(nomi) == 0 {
		return r, nil
	}
	out, _, err := a.Esegui(time.Minute, "rpm", append([]string{"-q", "--qf", `%{NAME} %{VERSION}-%{RELEASE}\n`}, nomi...)...)
	if err != nil {
		return nil, err
	}
	for _, n := range nomi {
		r[n] = ""
	}
	for _, riga := range strings.Split(out, "\n") {
		c := strings.Fields(riga)
		if len(c) == 2 && !strings.HasPrefix(riga, "package ") {
			r[c[0]] = c[1]
		}
	}
	return r, nil
}

func (g *gestoreDnf) Versioni(nomi []string) (map[string]string, error) {
	return rpmVersioni(g.a, nomi)
}

// Risolvi: dnf scarica l'intera chiusura in una cartella nostra (--destdir) verificando le somme dei
// metadati; l'elenco si legge dai file con rpm -qp. I pacchetti già installati alla stessa
// versione dnf non li scarica: sono «presente».
func (g *gestoreDnf) Risolvi(cache string, file, nomi []string) ([]Artefatto, error) {
	dest := filepath.Join(cache, "rpm")
	if err := os.MkdirAll(g.a.P(dest), 0o700); err != nil {
		return nil, err
	}
	if _, err := os.Stat(g.a.P("/usr/bin/dnf5")); err == nil {
		// dnf5 (Fedora 41+): «install --downloadonly» non ha --destdir ([M] 30 set, fedora44-gnome):
		// la transazione si legge da «install --assumeno», poi «download» dei pacchetti dei depositi
		if err := g.scaricaDnf5(dest, file, nomi); err != nil {
			return nil, err
		}
	} else {
		arg := append([]string{"install", "-y", "--downloadonly", "--destdir", dest}, append(append([]string{}, file...), nomi...)...)
		if _, err := esegui(g.a, tempoGestore, "dnf", arg...); err != nil {
			return nil, err
		}
	}
	voci, _ := filepath.Glob(g.a.P(dest) + "/*.rpm")
	for _, f := range file { // il file locale: dnf non lo copia
		voci = append(voci, g.a.P(f))
	}
	var r []Artefatto
	visti := map[string]bool{}
	for _, v := range voci {
		// ⚠ rpm scrive anche gli avvisi («NOKEY» se la chiave del deposito non è ancora importata)
		// nella stessa uscita: si prende solo la riga con la marca
		out, err := esegui(g.a, time.Minute, "rpm", "-qp", "--qf", `RX %{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n`, v)
		if err != nil {
			return nil, err
		}
		var c []string
		for _, riga := range strings.Split(out, "\n") {
			if f := strings.Fields(riga); len(f) == 4 && f[0] == "RX" {
				c = f[1:]
			}
		}
		if len(c) != 3 || visti[c[0]] {
			continue
		}
		visti[c[0]] = true
		sha, _ := Sha256File(v)
		rel := strings.TrimPrefix(v, strings.TrimSuffix(g.a.P("/"), "/"))
		a := Artefatto{Nome: c[0], Versione: c[1], Arch: c[2], Origine: "deposito", File: rel, Sha256: sha, Esito: "nuovo"}
		for _, f := range file {
			if g.a.P(f) == v {
				a.Origine = "file"
			}
		}
		r = append(r, a)
	}
	prima, err := rpmVersioni(g.a, nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "aggiornato", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

var archi = map[string]bool{"x86_64": true, "noarch": true, "i686": true, "aarch64": true}

func (g *gestoreDnf) scaricaDnf5(dest string, file, nomi []string) error {
	out, c, err := g.a.Esegui(tempoGestore, "dnf", append([]string{"install", "--assumeno"}, append(append([]string{}, file...), nomi...)...)...)
	if err != nil {
		return err
	}
	if !strings.Contains(out, "Transaction Summary") {
		if strings.Contains(out, "Nothing to do") {
			return nil
		}
		return fmt.Errorf("dnf install --assumeno: uscita %d: %s", c, ultimeRighe(out, 6))
	}
	var nevra []string
	in := false
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		// le sezioni della tabella di dnf5: si prende quel che si installa, aggiorna o RETROCEDE
		// (una retrocessione è una modifica INDIRETTA come un aggiornamento), mai «Skipping
		// packages with conflicts» ([M] 30 set: lì c'era la libavcodec-freeworld più nuova)
		if strings.HasSuffix(t, ":") && !strings.HasPrefix(riga, " ") {
			in = strings.HasPrefix(t, "Installing") || strings.HasPrefix(t, "Upgrading") || strings.HasPrefix(t, "Downgrading")
			continue
		}
		f := strings.Fields(t)
		if !in || len(f) < 4 || !archi[f[1]] || f[3] == "@commandline" {
			continue
		}
		ver := f[2]
		if strings.HasPrefix(ver, "0:") {
			ver = ver[2:]
		}
		nevra = append(nevra, f[0]+"-"+ver+"."+f[1])
	}
	if len(nevra) == 0 {
		return nil
	}
	if _, err = esegui(g.a, tempoGestore, "dnf", append([]string{"download", "--destdir", dest}, nevra...)...); err != nil {
		return err
	}
	// [M] 30 set, fedora44-gnome: «download» ha lasciato anche un'altra versione dello stesso
	// pacchetto: nella cartella resta SOLO l'insieme della transazione
	voluti := map[string]bool{}
	for _, n := range nevra {
		voluti[n+".rpm"] = true
	}
	voci, _ := filepath.Glob(g.a.P(dest) + "/*.rpm")
	for _, v := range voci {
		if !voluti[filepath.Base(v)] {
			os.Remove(v)
		}
	}
	return nil
}

func nomiDi(r []Artefatto) []string {
	var n []string
	for _, a := range r {
		n = append(n, a.Nome)
	}
	return n
}

// Installa: i file scaricati, dalla cartella nostra, senza rete (-C); la firma dei pacchetti dei
// depositi la verifica rpm (localpkg_gpgcheck: la chiave l'ha importata aggiungi-deposito o dnf
// stesso al primo pacchetto del deposito).
func (g *gestoreDnf) Installa(cache string, file, nomi []string) error {
	voci, _ := filepath.Glob(g.a.P(filepath.Join(cache, "rpm")) + "/*.rpm")
	var arg []string
	for _, v := range voci {
		arg = append(arg, strings.TrimPrefix(v, strings.TrimSuffix(g.a.P("/"), "/")))
	}
	// prima le dipendenze dei depositi, con la loro firma verificata; poi il file del piano, che
	// il motore ha verificato col suo sha256 (senza firma rpm finché l'archivio firmato non c'è, T8)
	if len(arg) > 0 {
		if _, err := esegui(g.a, tempoGestore, "dnf", append([]string{"install", "-y", "-C", "--setopt=localpkg_gpgcheck=1"}, arg...)...); err != nil {
			return err
		}
	}
	if len(file) == 0 {
		return nil
	}
	_, err := esegui(g.a, tempoGestore, "dnf", append([]string{"install", "-y", "-C", "--setopt=localpkg_gpgcheck=0"}, file...)...)
	return err
}

func (g *gestoreDnf) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	// dnf remove toglie anche chi dipende da questi: si guarda con --assumeno
	out, _, err := g.a.Esegui(tempoGestore, "dnf", append([]string{"remove", "--assumeno", "--setopt=clean_requirements_on_remove=0"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	// ⚠ --assumeno esce 1 ANCHE quando la simulazione riesce («Operation aborted»): il codice non
	// dice niente, il testo sì. Se il solver non risolve — togliere questi romperebbe un pacchetto
	// PROTETTO, o uno installato che ne ha bisogno — non c'è la sezione «Removing»: i nomi stanno
	// nei «Problem», e sono loro i dipendenti (i nomi dati si trattengono). `[M]` T10, 30 set,
	// fedora44-gnome-iso (fase 18, col deposito Cisco): openh264 ← libheif ← glycin-loaders ← gdk-pixbuf2 ← gnome-shell (protetto);
	// prima si leggeva «nessun dipendente» e `dnf remove -y` falliva.
	if strings.Contains(out, "Failed to resolve the transaction") || strings.Contains(out, "Impossibile risolvere la transazione") {
		altri := fuoriDa(problemiDnf(out), nomi)
		if len(altri) == 0 {
			return nil, fmt.Errorf("dnf remove --assumeno %s: %s", strings.Join(nomi, " "), ultimeRighe(out, 6))
		}
		return altri, nil
	}
	var tutti []string
	in := false
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		if strings.HasPrefix(t, "Removing") || strings.HasPrefix(t, "Rimozione") {
			in = true
			continue
		}
		if in && (t == "" || strings.HasPrefix(t, "Transaction Summary") || strings.HasPrefix(t, "Riepilogo")) {
			in = false
		}
		if c := strings.Fields(t); in && len(c) >= 3 && !strings.HasSuffix(c[0], ":") {
			tutti = append(tutti, c[0])
		}
	}
	return fuoriDa(tutti, nomi), nil
}

// problemiDnf: i pacchetti nominati nei «Problem» di un solver dnf che non risolve — i protetti
// («protected packages: a, b») e gli installati che hanno bisogno di quel che si toglie («installed
// package NEVRA requires …»); il NEVRA torna nome.
func problemiDnf(out string) []string {
	var r []string
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		if _, dopo, ok := strings.Cut(t, "protected packages: "); ok {
			for _, n := range strings.Split(dopo, ",") {
				if n = strings.TrimSpace(n); n != "" {
					r = append(r, n)
				}
			}
			continue
		}
		for _, marca := range []string{"installed package ", "il pacchetto installato "} {
			if _, dopo, ok := strings.Cut(t, marca); ok {
				if f := strings.Fields(dopo); len(f) > 0 {
					r = append(r, nomeDaNevra(f[0]))
				}
			}
		}
	}
	return fuoriDa(r, nil)
}

// nomeDaNevra: «libheif-1.23.5-3.fc44.x86_64» → «libheif» (via l'architettura, poi versione e rilascio).
func nomeDaNevra(nevra string) string {
	s := nevra
	if i := strings.LastIndex(s, "."); i > 0 {
		s = s[:i]
	}
	for range 2 {
		if i := strings.LastIndex(s, "-"); i > 0 {
			s = s[:i]
		}
	}
	return s
}

func (g *gestoreDnf) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	_, err := esegui(g.a, tempoGestore, "dnf", append([]string{"remove", "-y", "--setopt=clean_requirements_on_remove=0"}, nomi...)...)
	return err
}

func (g *gestoreDnf) Integro() (bool, string, error) {
	// una transazione rpm a metà lascia i pacchetti doppi (due versioni dello stesso)
	out, c, err := g.a.Esegui(time.Minute, "rpm", "-qa", "--qf", `%{NAME}.%{ARCH}\n`)
	if err != nil {
		return false, "", err
	}
	if c != 0 {
		return false, ultimeRighe(out, 3), nil
	}
	visti := map[string]bool{}
	for _, n := range strings.Fields(out) {
		if visti[n] && !strings.HasPrefix(n, "gpg-pubkey") && !strings.HasPrefix(n, "kernel") {
			return false, "doppio: " + n, nil
		}
		visti[n] = true
	}
	return true, "", nil
}

// Ripara: dnf ripete la transazione; qui si torna a uno stato coerente togliendo i doppi.
func (g *gestoreDnf) Ripara() error {
	_, err := esegui(g.a, tempoGestore, "dnf", "remove", "-y", "--duplicates")
	return err
}

// ---------------------------------------------------------------- zypper (openSUSE) — non provato

type gestoreZypper struct {
	a  *Ambiente
	da string // --from <deposito> --allow-vendor-change
}

func (g *gestoreZypper) Da(d string) Gestore { return &gestoreZypper{g.a, d} }

// fileArg: il pacchetto del piano è verificato dal motore (sha256 del piano approvato, §6.6.6) e
// finché l'archivio firmato non c'è (T8) non ha una firma rpm: zypper lo rifiuterebbe
// ([M] 30 set, tumbleweed-kde: «Signature verification failed [6-File is unsigned]»).
// ⚠ Vale SOLO per i file del piano; i pacchetti dei depositi restano verificati da zypper.
func (g *gestoreZypper) fileArg(file []string) []string {
	if len(file) == 0 {
		return nil
	}
	return []string{"--allow-unsigned-rpm"}
}

func (g *gestoreZypper) daArg() []string {
	if g.da == "" {
		return nil
	}
	return []string{"--from", g.da, "--allow-vendor-change"}
}

func (g *gestoreZypper) Nome() string { return "zypper" }

func (g *gestoreZypper) Versioni(nomi []string) (map[string]string, error) {
	return rpmVersioni(g.a, nomi)
}

func (g *gestoreZypper) Risolvi(cache string, file, nomi []string) ([]Artefatto, error) {
	arg := append(append([]string{"--non-interactive", "install", "--download-only"}, g.daArg()...), append(append(g.fileArg(file), file...), nomi...)...)
	if _, err := esegui(g.a, tempoGestore, "zypper", arg...); err != nil {
		return nil, err
	}
	out, err := esegui(g.a, tempoGestore, "zypper", append(append([]string{"--non-interactive", "--xmlout", "install", "--dry-run"}, g.daArg()...), append(append(g.fileArg(file), file...), nomi...)...)...)
	if err != nil {
		return nil, err
	}
	var r []Artefatto
	re := regexp.MustCompile(`<solvable type="package" name="([^"]+)" edition="([^"]+)" arch="([^"]+)"`)
	for _, m := range re.FindAllStringSubmatch(out, -1) {
		r = append(r, Artefatto{Nome: m[1], Versione: m[2], Arch: m[3], Origine: "deposito", Esito: "nuovo"})
	}
	prima, err := rpmVersioni(g.a, nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "aggiornato", p
		}
	}
	return r, nil
}

func (g *gestoreZypper) Installa(cache string, file, nomi []string) error {
	_, err := esegui(g.a, tempoGestore, "zypper", append(append([]string{"--non-interactive", "--no-refresh", "install"}, g.daArg()...), append(append(g.fileArg(file), file...), nomi...)...)...)
	return err
}

var zypperSolvibile = regexp.MustCompile(`<solvable type="package" name="([^"]+)"`)

func (g *gestoreZypper) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	out, err := esegui(g.a, tempoGestore, "zypper", append([]string{"--non-interactive", "--xmlout", "remove", "--dry-run"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	var tutti []string
	for _, m := range zypperSolvibile.FindAllStringSubmatch(out, -1) {
		tutti = append(tutti, m[1])
	}
	return fuoriDa(tutti, nomi), nil
}

func (g *gestoreZypper) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	_, err := esegui(g.a, tempoGestore, "zypper", append([]string{"--non-interactive", "remove"}, nomi...)...)
	return err
}

func (g *gestoreZypper) Integro() (bool, string, error) {
	out, c, err := g.a.Esegui(tempoGestore, "zypper", "--non-interactive", "verify", "--dry-run")
	if err != nil {
		return false, "", err
	}
	return c == 0, ultimeRighe(out, 2), nil
}

func (g *gestoreZypper) Ripara() error {
	_, err := esegui(g.a, tempoGestore, "zypper", "--non-interactive", "verify")
	return err
}

// ---------------------------------------------------------------- pacman (Arch) — non provato

type gestorePacman struct{ a *Ambiente }

func (g *gestorePacman) Nome() string { return "pacman" }

func (g *gestorePacman) Versioni(nomi []string) (map[string]string, error) {
	pk := ArchivioPacchetti(g.a, "arch", nomi)
	if !pk.letto {
		return nil, errors.New("the pacman database cannot be read")
	}
	r := map[string]string{}
	for _, n := range nomi {
		r[n] = pk.versioni[n]
	}
	return r, nil
}

func (g *gestorePacman) Risolvi(cache string, file, nomi []string) ([]Artefatto, error) {
	// la transazione intera (i file del piano e i pacchetti dei depositi, con le dipendenze):
	// pacman -U/-S --print dice che cosa installerebbe, senza toccare niente
	var righe []string
	if len(file) > 0 {
		out, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-U", "--needed", "--print", "--print-format", "%n %v %a %r %l"}, file...)...)
		if err != nil {
			return nil, err
		}
		righe = append(righe, strings.Split(out, "\n")...)
	}
	if len(nomi) > 0 {
		out, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-S", "--needed", "--print", "--print-format", "%n %v %a %r %l"}, nomi...)...)
		if err != nil {
			return nil, err
		}
		righe = append(righe, strings.Split(out, "\n")...)
	}
	var r []Artefatto
	var daScaricare []string
	visti := map[string]bool{}
	for _, riga := range righe {
		c := strings.Fields(riga)
		if len(c) != 5 || visti[c[0]] {
			continue
		}
		visti[c[0]] = true
		a := Artefatto{Nome: c[0], Versione: c[1], Arch: c[2], Origine: c[3], Esito: "nuovo"}
		if strings.HasPrefix(c[4], "file://") || strings.HasPrefix(c[4], "/") {
			a.Origine, a.File = "file", strings.TrimPrefix(c[4], "file://")
		} else {
			a.File = filepath.Join("/var/cache/pacman/pkg", filepath.Base(c[4]))
			daScaricare = append(daScaricare, c[0])
		}
		r = append(r, a)
	}
	if len(daScaricare) > 0 {
		if _, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-Sw", "--noconfirm"}, daScaricare...)...); err != nil {
			return nil, err
		}
	}
	prima, err := g.Versioni(nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		r[i].Sha256, _ = Sha256File(g.a.P(r[i].File))
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "aggiornato", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

func (g *gestorePacman) Installa(cache string, file, nomi []string) error {
	// i pacchetti dei depositi sono già nella cache di pacman (-Sw in Risolvi): -S li prende da lì
	if len(nomi) > 0 {
		if _, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-S", "--needed", "--noconfirm"}, nomi...)...); err != nil {
			return err
		}
	}
	if len(file) == 0 {
		return nil
	}
	_, err := esegui(g.a, tempoGestore, "pacman", append([]string{"-U", "--needed", "--noconfirm"}, file...)...)
	return err
}

func (g *gestorePacman) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	// ⚠ pacman -R non toglie chi dipende: se qualcuno dipende, la simulazione FALLISCE e lo dice
	// («removing X breaks dependency 'X' required by Y»): chi dipende è Y
	out, c, err := g.a.Esegui(tempoGestore, "pacman", append([]string{"-R", "--print", "--print-format", "%n"}, nomi...)...)
	if err != nil {
		return nil, err
	}
	if c != 0 {
		var r []string
		for _, m := range pacmanRompe.FindAllStringSubmatch(out, -1) {
			r = append(r, m[1])
		}
		if len(r) == 0 {
			return nil, fmt.Errorf("pacman -R --print: uscita %d: %s", c, ultimeRighe(out, 6))
		}
		return fuoriDa(r, nomi), nil
	}
	return fuoriDa(strings.Fields(out), nomi), nil
}

var pacmanRompe = regexp.MustCompile(`required by (\S+)`)

func (g *gestorePacman) Togli(nomi []string, purge bool) error {
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	arg := []string{"-R", "--noconfirm"}
	if purge {
		arg = []string{"-Rn", "--noconfirm"}
	}
	_, err := esegui(g.a, tempoGestore, "pacman", append(arg, nomi...)...)
	return err
}

func (g *gestorePacman) Integro() (bool, string, error) {
	if _, err := os.Stat(g.a.P("/var/lib/pacman/db.lck")); err == nil {
		return false, "/var/lib/pacman/db.lck is there", nil
	}
	return true, "", nil
}

// Ripara: il file di blocco lasciato da un pacman ucciso si toglie (nessun pacman gira: lo
// garantisce la serratura del motore), poi pacman -Dk controlla l'archivio.
func (g *gestorePacman) Ripara() error {
	os.Remove(g.a.P("/var/lib/pacman/db.lck"))
	_, err := esegui(g.a, tempoGestore, "pacman", "-Dk")
	return err
}
