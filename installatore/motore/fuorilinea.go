package motore

import (
	"bufio"
	"crypto/sha512"
	"encoding/hex"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Il PACCHETTO FUORI LINEA: l'installazione senza rete (fasi/17-l-installatore.md §6.5 punto 10,
// §6.6.12, R22).
//
// Si prepara su una macchina COLLEGATA che ha la stessa impronta della macchina senza rete (la
// «macchina di riferimento», come per il piano approvato: stessa distribuzione, stessi pacchetti):
//
//	remotix-install prepara-fuori-linea --archivio URL (--risposte FILE | --piano FILE) --uscita DIR
//
// e contiene, in una cartella sola:
//
//	fuori-linea.json          il manifesto: l'impronta della macchina di riferimento (quella vincolante
//	                          del piano e l'elenco esatto dei pacchetti installati), l'INSIEME RISOLTO
//	                          (ogni artefatto con nome, versione, sha256) e ogni file con il suo sha256
//	archivio/                 la parte dell'archivio di REMOTIX che serve: il motore col suo sha256 (il
//	                          catalogo sta dentro di lui), la chiave pubblica, e il deposito della
//	                          famiglia coi suoi METADATI FIRMATI (InRelease; repomd.xml.asc) e i soli
//	                          pacchetti che servono
//	distro/apt/<n>/           (apt) una copia PARZIALE di ogni deposito della distribuzione: il suo
//	                          InRelease firmato dalla distribuzione, gli indici Packages che quell'InRelease
//	                          certifica, e nel pool i soli .deb che alla macchina mancano
//	distro/rpm/<azione>/      (dnf) i .rpm che alla macchina mancano, firmati uno per uno dalla distribuzione
//
// Sulla macchina senza rete il motore lo usa come ARCHIVIO LOCALE (file://…/archivio: il deposito di
// REMOTIX punta lì) e le firme si verificano COME IN LINEA:
//   - apt: il gestore legge i depositi del pacchetto (e solo quelli, con una configurazione
//     temporanea: niente cambia nelle sorgenti della macchina) e verifica InRelease con la chiave della
//     distribuzione (Signed-By, lo stesso file di prima), gli indici con InRelease, ogni .deb con
//     l'indice — la stessa catena di una installazione in linea;
//   - dnf: ogni .rpm si installa con la verifica della sua firma (localpkg_gpgcheck=1), come in linea
//     (gpgcheck=1: i metadati di Fedora non sono firmati nemmeno in linea); quelli di REMOTIX con la
//     chiave dell'archivio, i metadati del deposito di REMOTIX con repo_gpgcheck (repomd.xml.asc).
//
// ⛔ Un pacchetto preparato per un'altra impronta si RIFIUTA (RX-FUORI-002), come un piano (R31); un
// file del pacchetto alterato o mancante si rifiuta prima di toccare la macchina (RX-FUORI-001).
// ⭐ RPM Fusion (Fedora, D5) ENTRA nel pacchetto, se il piano lo ha col consenso: porta i driver con
// H.264 della scheda (fase 18: niente più ffmpeg; fase 19: niente ripiego sul processore). Il
// pacchetto porta rpmfusion-free-release (e rpmfusion-nonfree-release se la scheda è Intel),
// scaricati in https come li scarica il passo in linea, e i driver risolti; si installano con la firma verificata (la chiave la porta il release).
// ⚠ Limiti dichiarati: zypper e pacman non ancora (RX-FUORI-004); Packman ed EPEL non entrano nel
// pacchetto: il loro passo scarica dalla rete (RX-FUORI-005).

// PacchettoFuoriLinea: il manifesto del pacchetto fuori linea.
type PacchettoFuoriLinea struct {
	Formato   string      `json:"format"`
	Oggetto   string      `json:"object"` // "offline-bundle"
	Creato    string      `json:"created"`
	Motore    RifMotore   `json:"engine"`
	Catalogo  RifCatalogo `json:"catalog"`
	Origine   string      `json:"origin"` // l'archivio da cui è stato preparato
	Canale    string      `json:"channel"`
	Bersaglio string      `json:"target"`
	Famiglia  string      `json:"family"`
	// Impronta: quella vincolante della macchina di riferimento (il profilo, il motore, il catalogo:
	// CalcolaImpronta senza azioni); Pacchetti: TUTTI i pacchetti installati, nome=versione. La macchina
	// senza rete deve combaciare con entrambe: l'insieme risolto dipende da quel che c'è già.
	Impronta        Impronta           `json:"fingerprint"`
	Pacchetti       []string           `json:"packages"`
	DigestPacchetti string             `json:"digest_packages"`
	Azioni          []AzioneFuoriLinea `json:"actions"`
	Artefatti       []Artefatto        `json:"artifacts"` // l'insieme risolto (File relativo alla cartella)
	Apt             []SorgenteApt      `json:"apt,omitempty"`
	// Terzi: gli archivi di terzi che il pacchetto porta (rpmfusion → il file del release)
	Terzi map[string]string `json:"third_party,omitempty"`
	File  []FileFuoriLinea  `json:"file"`
	Dir   string            `json:"-"`
}

// AzioneFuoriLinea: un passo di pacchetti del piano, e i suoi artefatti (dnf: i file da installare).
type AzioneFuoriLinea struct {
	ID        string   `json:"id"`
	Nomi      []string `json:"names"`
	Artefatti []string `json:"artifacts"` // i File di Artefatti che servono a questo passo
}

// SorgenteApt: un deposito della distribuzione, copiato in parte.
type SorgenteApt struct {
	Dir        string   `json:"dir"` // relativa alla cartella del pacchetto
	URI        string   `json:"uri"` // da dove veniva (Repo-URI di apt)
	Suite      string   `json:"suite"`
	Componenti []string `json:"components"`
	SignedBy   string   `json:"signed_by,omitempty"`
}

// FileFuoriLinea: un file del pacchetto.
type FileFuoriLinea struct {
	File   string `json:"file"`
	Sha256 string `json:"sha256"`
	Byte   int64  `json:"bytes"`
}

const nomeManifesto = "offline.json"

// ImprontaMacchina: l'impronta vincolante della macchina senza le azioni di un piano, e tutti i
// suoi pacchetti.
func ImprontaMacchina(prof *Profilo, cat *Catalogo, amb *Ambiente) (*Impronta, []string, error) {
	im, err := CalcolaImpronta(prof, cat, nil, nil, &Contesto{Amb: amb})
	if err != nil {
		return nil, nil, err
	}
	pk, err := ElencoPacchetti(amb)
	return im, pk, err
}

// ElencoPacchetti: nome=versione di tutti i pacchetti installati, in ordine.
func ElencoPacchetti(a *Ambiente) ([]string, error) {
	var r []string
	switch a.Famiglia {
	case "debian", "arch":
		pk := ArchivioPacchetti(a, a.Famiglia, nil)
		if !pk.letto {
			return nil, fmt.Errorf("the package database cannot be read (%s)", pk.fonte)
		}
		for n, v := range pk.versioni {
			r = append(r, n+"="+v)
		}
	case "fedora", "suse":
		out, err := esegui(a, 2*time.Minute, "rpm", "-qa", "--qf", `%{NAME}.%{ARCH}=%{EPOCHNUM}:%{VERSION}-%{RELEASE}\n`)
		if err != nil {
			return nil, err
		}
		for _, x := range strings.Fields(out) {
			r = append(r, x)
		}
	default:
		return nil, Errore("RX-PACCHETTI-003", a.Famiglia)
	}
	sort.Strings(r)
	return r, nil
}

// LeggiFuoriLinea legge il manifesto e verifica OGNI file del pacchetto col suo sha256.
func LeggiFuoriLinea(dir string) (*PacchettoFuoriLinea, error) {
	abs, err := filepath.Abs(dir)
	if err != nil {
		return nil, err
	}
	var fl PacchettoFuoriLinea
	if err := LeggiJSON(filepath.Join(abs, nomeManifesto), &fl); err != nil || fl.Oggetto != "offline-bundle" {
		if err == nil {
			err = fmt.Errorf("oggetto %q", fl.Oggetto)
		}
		return nil, Errore("RX-FUORI-001", err.Error())
	}
	fl.Dir = abs
	var male []string
	for _, f := range fl.File {
		sha, err := Sha256File(filepath.Join(abs, f.File))
		switch {
		case err != nil:
			male = append(male, f.File+": "+err.Error())
		case sha == "":
			male = append(male, f.File+": missing")
		case sha != f.Sha256:
			male = append(male, f.File+": sha256 "+sha[:16]+"…, atteso "+f.Sha256[:min(16, len(f.Sha256))]+"…")
		}
	}
	if len(male) > 0 {
		if len(male) > 6 {
			male = append(male[:6], fmt.Sprintf("… and %d more", len(male)-6))
		}
		return nil, Errore("RX-FUORI-001", strings.Join(male, "; "))
	}
	return &fl, nil
}

// URLArchivio: l'archivio locale del pacchetto, come lo vede il motore.
func (fl *PacchettoFuoriLinea) URLArchivio() string {
	return "file://" + filepath.Join(fl.Dir, "archive")
}

// DaURLArchivio: la cartella del pacchetto fuori linea da un archivio file://…/archivio ("" se non lo è).
func DaURLArchivio(u string) string {
	p, ok := strings.CutPrefix(strings.TrimRight(u, "/"), "file://")
	if !ok || filepath.Base(p) != "archive" {
		return ""
	}
	d := filepath.Dir(p)
	if _, err := os.Stat(filepath.Join(d, nomeManifesto)); err != nil {
		return ""
	}
	return d
}

// Combacia: la macchina è quella per cui il pacchetto è stato preparato? (RX-FUORI-002, coi dettagli)
func (fl *PacchettoFuoriLinea) Combacia(prof *Profilo, cat *Catalogo, amb *Ambiente) error {
	im, pk, err := ImprontaMacchina(prof, cat, amb)
	if err != nil {
		return err
	}
	var det []string
	if im.Digest != fl.Impronta.Digest {
		t, a := DifferenzeImpronta(fl.Impronta.Elementi, im.Elementi)
		det = append(det, "fingerprint — in the bundle: "+strings.Join(primi(t, 6), "; ")+" — here: "+strings.Join(primi(a, 6), "; "))
	}
	if d := Sha256([]byte(strings.Join(pk, "\n"))); d != fl.DigestPacchetti {
		t, a := DifferenzeImpronta(fl.Pacchetti, pk)
		det = append(det, fmt.Sprintf("packages — only in the bundle (%d): %s — only here (%d): %s", len(t), strings.Join(primi(t, 6), " "), len(a), strings.Join(primi(a, 6), " ")))
	}
	if len(det) > 0 {
		return Errore("RX-FUORI-002", strings.Join(det, " · "))
	}
	return nil
}

func primi(x []string, n int) []string {
	if len(x) > n {
		return append(append([]string{}, x[:n]...), "…")
	}
	return x
}

// UsaFuoriLinea: il motore lavora col pacchetto fuori linea (il gestore di pacchetti prende tutto da lì).
func (m *Motore) UsaFuoriLinea(fl *PacchettoFuoriLinea) error {
	if m.Amb == nil || m.Amb.Pacchetti == nil {
		return Errore("RX-PACCHETTI-003", "")
	}
	if fl.Famiglia != m.Amb.Famiglia {
		return Errore("RX-FUORI-002", "family "+fl.Famiglia+", this machine "+m.Amb.Famiglia)
	}
	m.FuoriLinea = fl
	if _, gia := m.Amb.Pacchetti.(*gestoreFuoriLinea); !gia {
		m.Amb.Pacchetti = &gestoreFuoriLinea{Gestore: m.Amb.Pacchetti, a: m.Amb, fl: fl}
	}
	return nil
}

// ---------------------------------------------------------------- il gestore, fuori linea

type gestoreFuoriLinea struct {
	Gestore
	a  *Ambiente
	fl *PacchettoFuoriLinea
}

func (g *gestoreFuoriLinea) artefatto(nome, versione string) *Artefatto {
	for i := range g.fl.Artefatti {
		x := &g.fl.Artefatti[i]
		if x.Nome == nome && (versione == "" || x.Versione == versione || strings.TrimPrefix(x.Versione, "0:") == versione) {
			return x
		}
	}
	return nil
}

// aptOpz: una configurazione di apt che vede SOLO i depositi del pacchetto (distribuzione e REMOTIX),
// con liste sue nella cache dell'operazione. Le sorgenti e le preferenze della macchina non si toccano.
func (g *gestoreFuoriLinea) aptOpz(cache string) ([]string, error) {
	liste, vuota := filepath.Join(cache, "apt-liste"), filepath.Join(cache, "apt-vuota")
	for _, d := range []string{filepath.Join(liste, "partial"), vuota} {
		if err := os.MkdirAll(g.a.P(d), 0o755); err != nil {
			return nil, err
		}
	}
	var b strings.Builder
	b.WriteString("# REMOTIX — the repositories of the offline bundle " + g.fl.Dir + " (for this operation only)\n")
	// target=Packages: solo gli indici che il pacchetto porta. Altri pacchetti della macchina aggiungono
	// indici in /etc/apt/apt.conf.d (appstream: DEP-11 e icone; apt-file: Contents) e apt li
	// cercherebbe: `[M]` 30 set, debian13-gnome, «Failed to fetch …/dep11/icons-48x48.tar»
	for _, s := range g.fl.Apt {
		opz := "[target=Packages] "
		if s.SignedBy != "" {
			opz = "[signed-by=" + s.SignedBy + " target=Packages] "
		}
		fmt.Fprintf(&b, "deb %sfile:%s %s %s\n", opz, filepath.Join(g.fl.Dir, s.Dir), s.Suite, strings.Join(s.Componenti, " "))
	}
	fmt.Fprintf(&b, "deb [signed-by=%s target=Packages] file:%s %s-%s main\n", ChiaveApt, filepath.Join(g.fl.Dir, "archive", "deb"), g.fl.Bersaglio, g.fl.Canale)
	elenco := filepath.Join(cache, "offline.list")
	if err := ScriviAtomico(g.a.P(elenco), []byte(b.String()), 0o644); err != nil {
		return nil, err
	}
	return []string{"-o", "Dir::Etc::SourceList=" + elenco, "-o", "Dir::Etc::SourceParts=" + vuota,
		"-o", "Dir::State::Lists=" + liste, "-o", "Dir::Etc::PreferencesParts=" + vuota,
		"-o", "Acquire::By-Hash=no", "-o", "Acquire::Languages=none", "-o", "APT::Sandbox::User=root"}, nil
}

func (g *gestoreFuoriLinea) Risolvi(cache string, file, nomi []string) ([]Artefatto, error) {
	if len(file) > 0 {
		return nil, Errore("RX-FUORI-003", "a package from a file cannot go into an offline installation")
	}
	switch g.a.Famiglia {
	case "debian":
		return g.risolviApt(cache, nomi)
	case "fedora":
		return g.risolviDnf(cache, nomi)
	}
	return nil, Errore("RX-FUORI-004", g.a.Famiglia)
}

func (g *gestoreFuoriLinea) risolviApt(cache string, nomi []string) ([]Artefatto, error) {
	opz, err := g.aptOpz(cache)
	if err != nil {
		return nil, err
	}
	// i metadati firmati del pacchetto: InRelease della distribuzione e di REMOTIX, verificati da apt
	out, err := esegui(g.a, tempoGestore, "apt-get", append([]string{"update"}, opz...)...)
	if err != nil {
		return nil, err
	}
	if strings.Contains(out, "\nW: ") || strings.HasPrefix(out, "W: ") || strings.Contains(out, "\nE: ") {
		return nil, fmt.Errorf("apt-get update (offline): %s", ultimeRighe(out, 6))
	}
	out, err = esegui(g.a, tempoGestore, "apt-get", append(append(append([]string{"-s", "install"}, aptOpzioni...), opz...), nomi...)...)
	if err != nil {
		return nil, err
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
		x := g.artefatto(m[1], m[3])
		if x == nil {
			return nil, Errore("RX-FUORI-003", m[1]+" "+m[3])
		}
		a := *x
		a.File = filepath.Join(g.fl.Dir, x.File)
		if sha, _ := Sha256File(g.a.P(a.File)); sha != x.Sha256 {
			return nil, Errore("RX-FUORI-001", x.File)
		}
		a.Esito, a.Prima = "nuovo", ""
		if m[2] != "" {
			a.Esito, a.Prima = "upgraded", m[2]
		}
		r = append(r, a)
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

func chiaveNomi(n []string) string {
	c := append([]string{}, n...)
	sort.Strings(c)
	return strings.Join(c, ",")
}

func (g *gestoreFuoriLinea) risolviDnf(cache string, nomi []string) ([]Artefatto, error) {
	var az *AzioneFuoriLinea
	for i := range g.fl.Azioni {
		if chiaveNomi(g.fl.Azioni[i].Nomi) == chiaveNomi(nomi) {
			az = &g.fl.Azioni[i]
		}
	}
	if az == nil {
		return nil, Errore("RX-FUORI-003", strings.Join(nomi, ","))
	}
	dest := filepath.Join(cache, "rpm")
	if err := os.MkdirAll(g.a.P(dest), 0o700); err != nil {
		return nil, err
	}
	var r []Artefatto
	for _, f := range az.Artefatti {
		var x *Artefatto
		for i := range g.fl.Artefatti {
			if g.fl.Artefatti[i].File == f {
				x = &g.fl.Artefatti[i]
			}
		}
		if x == nil {
			return nil, Errore("RX-FUORI-003", f)
		}
		a := *x
		a.File = filepath.Join(dest, filepath.Base(f))
		if err := copiaFile(filepath.Join(g.fl.Dir, f), g.a.P(a.File)); err != nil {
			return nil, err
		}
		if sha, _ := Sha256File(g.a.P(a.File)); sha != x.Sha256 {
			return nil, Errore("RX-FUORI-001", f)
		}
		r = append(r, a)
	}
	prima, err := rpmVersioni(g.a, nomiDi(r))
	if err != nil {
		return nil, err
	}
	for i := range r {
		r[i].Esito, r[i].Prima = "nuovo", ""
		if p := prima[r[i].Nome]; p != "" {
			r[i].Esito, r[i].Prima = "upgraded", p
		}
	}
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, nil
}

func (g *gestoreFuoriLinea) Installa(cache string, file, nomi []string) error {
	switch g.a.Famiglia {
	case "debian":
		opz, err := g.aptOpz(cache)
		if err != nil {
			return err
		}
		_, err = esegui(g.a, tempoGestore, "apt-get", append(append(append([]string{"install"}, aptOpzioni...), opz...), nomi...)...)
		return err
	case "fedora":
		voci, _ := filepath.Glob(g.a.P(filepath.Join(cache, "rpm")) + "/*.rpm")
		if len(voci) == 0 {
			return nil
		}
		var arg []string
		for _, v := range voci {
			arg = append(arg, strings.TrimPrefix(v, strings.TrimSuffix(g.a.P("/"), "/")))
		}
		// nessun deposito (niente rete, niente metadati da rinfrescare): i file, e la firma di ognuno
		// verificata da rpm con le chiavi della macchina (la distribuzione; REMOTIX, importata dal
		// passo dell'archivio)
		_, err := esegui(g.a, tempoGestore, "dnf", append([]string{"install", "-y", "--disablerepo=*", "--setopt=localpkg_gpgcheck=1"}, arg...)...)
		return err
	}
	return Errore("RX-FUORI-004", g.a.Famiglia)
}

func copiaFile(da, a string) error {
	in, err := os.Open(da)
	if err != nil {
		return err
	}
	defer in.Close()
	if err := os.MkdirAll(filepath.Dir(a), 0o755); err != nil {
		return err
	}
	tmp := a + ".parziale"
	out, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		os.Remove(tmp)
		return err
	}
	if err := out.Sync(); err != nil {
		out.Close()
		return err
	}
	out.Close()
	return os.Rename(tmp, a)
}

// ---------------------------------------------------------------- la preparazione (macchina collegata)

// OpzioniPrepara: come preparare il pacchetto.
type OpzioniPrepara struct {
	Archivio, Canale string
	Uscita           string
	ChiaveArchivio   string // la chiave pubblica dell'archivio (armatura ASCII)
	Scarica          func(url string) ([]byte, error)
}

type preparazione struct {
	o   OpzioniPrepara
	amb *Ambiente
	fl  *PacchettoFuoriLinea
	dir string
	lav string
	ev  func(string)
}

func (p *preparazione) scarica(u string) ([]byte, error) {
	if p.o.Scarica != nil {
		return p.o.Scarica(u)
	}
	return scaricaURL(u, 512<<20)
}

// scaricaURL: http(s) o file://.
func scaricaURL(u string, limite int64) ([]byte, error) {
	if f, ok := strings.CutPrefix(u, "file://"); ok {
		return os.ReadFile(f)
	}
	cl := &http.Client{Timeout: 5 * time.Minute}
	r, err := cl.Get(u)
	if err != nil {
		return nil, err
	}
	defer r.Body.Close()
	if r.StatusCode != 200 {
		return nil, fmt.Errorf("%s: %s", u, r.Status)
	}
	return io.ReadAll(io.LimitReader(r.Body, limite))
}

// scriviIn: un file nella cartella del pacchetto (percorso relativo).
func (p *preparazione) scriviIn(rel string, dati []byte) error {
	f := filepath.Join(p.dir, rel)
	if err := os.MkdirAll(filepath.Dir(f), 0o755); err != nil {
		return err
	}
	return os.WriteFile(f, dati, 0o644)
}

func (p *preparazione) daArchivio(rel string) ([]byte, error) {
	b, err := p.scarica(strings.TrimRight(p.o.Archivio, "/") + "/" + rel)
	if err != nil {
		return nil, err
	}
	return b, p.scriviIn(filepath.Join("archive", rel), b)
}

// PreparaFuoriLinea: il pacchetto fuori linea per QUESTA macchina (la macchina di riferimento,
// collegata) e per i passi di pacchetti del piano. Il piano stesso non entra: sulla macchina senza
// rete si rifà (dal file di risposte, o a mano) con l'archivio locale del pacchetto.
func PreparaFuoriLinea(amb *Ambiente, prof *Profilo, cat *Catalogo, piano *Piano, o OpzioniPrepara, ev func(string)) (*PacchettoFuoriLinea, error) {
	if ev == nil {
		ev = func(string) {}
	}
	o.Canale = nonVuoto(o.Canale, "stable")
	if amb.Famiglia != "debian" && amb.Famiglia != "fedora" {
		return nil, Errore("RX-FUORI-004", amb.Famiglia)
	}
	var terzi []string
	for _, a := range piano.Azioni {
		if a.Tipo == "add-repo" && a.Parametri["type"] != "archive" {
			if a.Parametri["type"] != "rpmfusion" || amb.Famiglia != "fedora" {
				return nil, Errore("RX-FUORI-005", a.Parametri["type"])
			}
			terzi = append(terzi, "rpmfusion")
			if a.Parametri["nonfree"] == "yes" {
				terzi = append(terzi, "rpmfusion-nonfree")
			}
		}
		if a.Tipo == "install-packages" && a.Parametri["file"] != "" {
			return nil, Errore("RX-FUORI-003", "a package from a file ("+a.Parametri["file"]+")")
		}
	}
	dir, err := filepath.Abs(o.Uscita)
	if err != nil {
		return nil, err
	}
	if voci, _ := os.ReadDir(dir); len(voci) > 0 {
		return nil, fmt.Errorf("%s is not empty", dir)
	}
	p := &preparazione{o: o, amb: amb, dir: dir, lav: filepath.Join(dir, ".lavoro"), ev: ev}
	if err := os.MkdirAll(p.lav, 0o700); err != nil {
		return nil, err
	}
	defer os.RemoveAll(p.lav)
	p.fl = &PacchettoFuoriLinea{Formato: Formato, Oggetto: "offline-bundle", Creato: ora(),
		Motore: RifMotore{VersioneMotore, DigestMotore()}, Catalogo: RifCatalogo{cat.Versione, cat.Digest},
		Origine: strings.TrimRight(o.Archivio, "/"), Canale: o.Canale, Bersaglio: BersaglioArchivio(amb), Famiglia: amb.Famiglia,
		Azioni: []AzioneFuoriLinea{}, Artefatti: []Artefatto{}, File: []FileFuoriLinea{}}

	// l'impronta della macchina di riferimento
	im, pk, err := ImprontaMacchina(prof, cat, amb)
	if err != nil {
		return nil, err
	}
	p.fl.Impronta, p.fl.Pacchetti, p.fl.DigestPacchetti = *im, pk, Sha256([]byte(strings.Join(pk, "\n")))

	// il motore (col suo sha256 pubblicato accanto: il catalogo viaggia dentro di lui) e la chiave
	// pubblica dell'archivio — il motore si verifica QUI (un archivio alterato si scopre prima di
	// portarlo via); la catena dei pacchetti la verifica il gestore, sulla macchina senza rete come in
	// linea (D11 semplificata, DECISIONI §10.21)
	ev("the engine and the archive key")
	mot, err := p.daArchivio("engine/remotix-install")
	if err != nil {
		return nil, err
	}
	sha, err := p.daArchivio("engine/remotix-install.sha256")
	if err != nil {
		return nil, err
	}
	if f := strings.Fields(string(sha)); len(f) == 0 || f[0] != Sha256(mot) {
		return nil, Errore("RX-TRUST-017", "engine/remotix-install: sha256 "+Sha256(mot)[:16]+"…, published "+strings.TrimSpace(string(sha)))
	}
	for _, k := range []string{"keys/remotix-archive.asc", "keys/README"} {
		if _, err := p.daArchivio(k); err != nil && !strings.HasSuffix(k, "README") {
			return nil, err
		}
	}

	// i passi di pacchetti del piano, nell'ordine
	var passi []AzioneFuoriLinea
	for _, a := range piano.Azioni {
		if a.Tipo != "install-packages" && a.Tipo != "install-desktop" {
			continue
		}
		var n []string
		for _, x := range strings.Split(a.Parametri["names"], ",") {
			if x = strings.TrimSpace(x); x != "" {
				n = append(n, x)
			}
		}
		if len(n) > 0 {
			passi = append(passi, AzioneFuoriLinea{ID: a.ID, Nomi: n, Artefatti: []string{}})
		}
	}
	switch amb.Famiglia {
	case "debian":
		err = p.apt(passi)
	case "fedora":
		err = p.dnf(passi, terzi)
	}
	if err != nil {
		return nil, err
	}

	// ogni file, col suo sha256
	ev("file fingerprints")
	err = filepath.WalkDir(dir, func(f string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			if f == p.lav {
				return filepath.SkipDir
			}
			return nil
		}
		rel, _ := filepath.Rel(dir, f)
		if rel == nomeManifesto {
			return nil
		}
		sha, err := Sha256File(f)
		if err != nil {
			return err
		}
		st, _ := d.Info()
		p.fl.File = append(p.fl.File, FileFuoriLinea{File: rel, Sha256: sha, Byte: st.Size()})
		return nil
	})
	if err != nil {
		return nil, err
	}
	sort.Slice(p.fl.File, func(i, j int) bool { return p.fl.File[i].File < p.fl.File[j].File })
	if err := os.RemoveAll(p.lav); err != nil {
		return nil, err
	}
	if err := ScriviJSON(filepath.Join(dir, nomeManifesto), p.fl); err != nil {
		return nil, err
	}
	os.Chmod(filepath.Join(dir, nomeManifesto), 0o644)
	p.fl.Dir = dir
	return p.fl, nil
}

// ---- apt: le sorgenti della macchina + l'archivio di REMOTIX, in una configurazione temporanea

var aptURI = regexp.MustCompile(`^'([^']+)' (\S+) (\d+) (\S+):(\S+)`)

func (p *preparazione) apt(passi []AzioneFuoriLinea) error {
	a := p.amb
	parti, liste, archivi, vuota := filepath.Join(p.lav, "parti"), filepath.Join(p.lav, "liste"), filepath.Join(p.lav, "archivi"), filepath.Join(p.lav, "vuota")
	for _, d := range []string{parti, filepath.Join(liste, "partial"), filepath.Join(archivi, "partial"), vuota} {
		if err := os.MkdirAll(d, 0o755); err != nil {
			return err
		}
	}
	// le sorgenti della macchina, così come sono (copie), più quella di REMOTIX
	voci, _ := filepath.Glob(a.P("/etc/apt/sources.list.d") + "/*")
	for _, v := range voci {
		if strings.HasSuffix(v, ".list") || strings.HasSuffix(v, ".sources") {
			if err := copiaFile(v, filepath.Join(parti, filepath.Base(v))); err != nil {
				return err
			}
		}
	}
	chiave := filepath.Join(p.lav, "remotix-archive.asc")
	if err := os.WriteFile(chiave, []byte(p.o.ChiaveArchivio), 0o644); err != nil {
		return err
	}
	suite := p.fl.Bersaglio + "-" + p.fl.Canale
	baseDeb := p.fl.Origine + "/deb/"
	if err := os.WriteFile(filepath.Join(parti, "zz-remotix-offline.sources"), []byte("Types: deb\nURIs: "+p.fl.Origine+"/deb\nSuites: "+suite+
		"\nComponents: main\nSigned-By: "+chiave+"\n"), 0o644); err != nil {
		return err
	}
	opz := []string{"-o", "Dir::Etc::SourceParts=" + parti, "-o", "Dir::State::Lists=" + liste,
		"-o", "Dir::Cache::Archives=" + archivi, "-o", "Dir::Etc::PreferencesParts=" + vuota, "-o", "APT::Sandbox::User=root"}
	p.ev("apt-get update (the machine's sources and the REMOTIX archive)")
	if out, err := esegui(a, tempoGestore, "apt-get", append([]string{"update"}, opz...)...); err != nil {
		return err
	} else if strings.Contains(out, "\nE: ") || strings.Contains(out, "\nW: ") {
		return fmt.Errorf("apt-get update: %s", ultimeRighe(out, 6))
	}
	var tutti []string
	for i := range passi {
		tutti = append(tutti, passi[i].Nomi...)
	}
	p.ev("risoluzione: " + strings.Join(tutti, " "))
	sim, err := esegui(a, tempoGestore, "apt-get", append(append(append([]string{"-s", "install"}, aptOpzioni...), opz...), tutti...)...)
	if err != nil {
		return err
	}
	uris, err := esegui(a, tempoGestore, "apt-get", append(append(append([]string{"install", "--print-uris", "-qq"}, aptOpzioni...), opz...), tutti...)...)
	if err != nil {
		return err
	}
	if _, err := esegui(a, tempoGestore, "apt-get", append(append(append([]string{"install", "--download-only"}, aptOpzioni...), opz...), tutti...)...); err != nil {
		return err
	}
	// gli indici dei depositi (quelli che apt ha appena verificato), per la copia parziale
	it, err := esegui(a, time.Minute, "apt-get", append([]string{"indextargets"}, opz...)...)
	if err != nil {
		return err
	}
	type dep struct {
		n     int
		uri   string
		suite string
		comp  map[string]bool
		sb    string
	}
	depositi := map[string]*dep{} // repo-uri + suite
	basi := map[string]int{}      // repo-uri → n
	for _, rec := range strings.Split(it, "\n\n") {
		k := map[string]string{}
		for _, riga := range strings.Split(rec, "\n") {
			if c, v, ok := strings.Cut(riga, ": "); ok {
				k[c] = v
			}
		}
		if k["Identifier"] != "Packages" || k["Target-Of"] != "deb" {
			continue
		}
		ru := k["Repo-URI"]
		if strings.HasPrefix(ru, baseDeb) {
			continue // REMOTIX: lo si prende dall'archivio così com'è, sotto
		}
		if _, ok := basi[ru]; !ok {
			basi[ru] = len(basi)
		}
		key := ru + " " + k["Release"]
		d := depositi[key]
		if d == nil {
			d = &dep{n: basi[ru], uri: ru, suite: k["Release"], comp: map[string]bool{}, sb: k["Signed-By"]}
			depositi[key] = d
		}
		d.comp[k["Component"]] = true
		rel := filepath.Join("distro", "apt", fmt.Sprint(d.n), "dists", d.suite)
		fn := k["Filename"]
		dati, err := os.ReadFile(fn)
		if err != nil {
			return fmt.Errorf("indice %s: %w", fn, err)
		}
		if err := p.scriviIn(filepath.Join(rel, k["MetaKey"]), dati); err != nil {
			return err
		}
		inr := strings.TrimSuffix(fn, strings.ReplaceAll(k["MetaKey"], "/", "_")) + "InRelease"
		ib, err := os.ReadFile(inr)
		if err != nil {
			return fmt.Errorf("InRelease of %s %s: %w (a repository without InRelease is not accepted)", ru, d.suite, err)
		}
		if err := p.scriviIn(filepath.Join(rel, "InRelease"), ib); err != nil {
			return err
		}
	}
	for _, d := range depositi {
		var comp []string
		for c := range d.comp {
			comp = append(comp, c)
		}
		sort.Strings(comp)
		p.fl.Apt = append(p.fl.Apt, SorgenteApt{Dir: filepath.Join("distro", "apt", fmt.Sprint(d.n)), URI: d.uri, Suite: d.suite, Componenti: comp, SignedBy: d.sb})
	}
	sort.Slice(p.fl.Apt, func(i, j int) bool { return p.fl.Apt[i].Dir+p.fl.Apt[i].Suite < p.fl.Apt[j].Dir+p.fl.Apt[j].Suite })

	// i .deb scaricati, al loro posto nel pool; il loro hash contro quello dell'indice firmato
	versioni := map[string][2]string{} // file → nome, versione (dalla simulazione)
	for _, riga := range strings.Split(sim, "\n") {
		if m := aptInst.FindStringSubmatch(riga); m != nil {
			versioni[m[1]] = [2]string{m[3], m[5]}
		}
	}
	for _, riga := range strings.Split(uris, "\n") {
		m := aptURI.FindStringSubmatch(strings.TrimSpace(riga))
		if m == nil {
			continue
		}
		u, fn, algo, hash := m[1], m[2], strings.ToUpper(m[4]), strings.ToLower(m[5])
		dati, err := os.ReadFile(filepath.Join(archivi, fn))
		if err != nil {
			return fmt.Errorf("%s not downloaded: %w", fn, err)
		}
		switch algo {
		case "SHA256":
			if Sha256(dati) != hash {
				return fmt.Errorf("%s: sha256 differs from the index", fn)
			}
		case "SHA512":
			s := sha512.Sum512(dati)
			if hex.EncodeToString(s[:]) != hash {
				return fmt.Errorf("%s: sha512 differs from the index", fn)
			}
		}
		var rel string
		if r, ok := strings.CutPrefix(u, baseDeb); ok {
			rel = filepath.Join("archive", "deb", r)
		} else {
			for ru, n := range basi {
				if r, ok := strings.CutPrefix(u, ru); ok {
					rel = filepath.Join("distro", "apt", fmt.Sprint(n), r)
				}
			}
		}
		if rel == "" {
			return fmt.Errorf("%s: does not come from any known repository", u)
		}
		rel, _ = url.PathUnescape(rel)
		if err := p.scriviIn(rel, dati); err != nil {
			return err
		}
		nome := strings.SplitN(fn, "_", 2)[0]
		v := versioni[nome]
		p.fl.Artefatti = append(p.fl.Artefatti, Artefatto{Nome: nome, Versione: v[0], Arch: v[1], Origine: u, File: rel, Sha256: Sha256(dati), Esito: "new"})
	}
	sort.Slice(p.fl.Artefatti, func(i, j int) bool { return p.fl.Artefatti[i].Nome < p.fl.Artefatti[j].Nome })
	for i := range passi {
		p.fl.Azioni = append(p.fl.Azioni, passi[i])
	}

	// l'archivio di REMOTIX della famiglia: i metadati firmati (InRelease, Release, Release.gpg e gli
	// indici che certificano)
	p.ev("the signed metadata of the REMOTIX archive (" + suite + ")")
	inr, err := p.daArchivio("deb/dists/" + suite + "/InRelease")
	if err != nil {
		return err
	}
	for _, f := range []string{"Release", "Release.gpg"} {
		if _, err := p.daArchivio("deb/dists/" + suite + "/" + f); err != nil {
			return err
		}
	}
	for _, x := range fileDiRelease(string(inr)) {
		b, err := p.daArchivio("deb/dists/" + suite + "/" + x[1])
		if err != nil {
			continue // Release elenca anche file che l'archivio non pubblica
		}
		if Sha256(b) != x[0] {
			return fmt.Errorf("REMOTIX archive: %s differs from InRelease", x[1])
		}
	}
	return nil
}

// fileDiRelease: la sezione SHA256 di un Release: (sha256, percorso).
func fileDiRelease(t string) [][2]string {
	var r [][2]string
	in := false
	s := bufio.NewScanner(strings.NewReader(t))
	for s.Scan() {
		riga := s.Text()
		if strings.HasPrefix(riga, "SHA256:") {
			in = true
			continue
		}
		if in && !strings.HasPrefix(riga, " ") {
			in = false
		}
		if c := strings.Fields(riga); in && len(c) == 3 {
			r = append(r, [2]string{c[0], c[2]})
		}
	}
	return r
}

// ---- dnf: la transazione di ogni passo (cumulativa), scaricata in una cartella per passo

// URLRpmFusion: il pacchetto che configura RPM Fusion (free) — lo stesso del passo in linea.
func URLRpmFusion(a *Ambiente) string { return URLRpmFusionRamo(a, "free") }

// URLRpmFusionRamo: il pacchetto che configura un ramo di RPM Fusion («free» o «nonfree»).
func URLRpmFusionRamo(a *Ambiente, ramo string) string {
	m, _ := OsRelease(a)
	v, _, _ := strings.Cut(m["VERSION_ID"], ".")
	if m["ID"] != "fedora" {
		return "https://mirrors.rpmfusion.org/" + ramo + "/el/rpmfusion-" + ramo + "-release-" + v + ".noarch.rpm"
	}
	return "https://mirrors.rpmfusion.org/" + ramo + "/fedora/rpmfusion-" + ramo + "-release-" + v + ".noarch.rpm"
}

// FileTerzi: il file di un archivio di terzi nel pacchetto fuori linea in uso ("" se non si lavora
// fuori linea, o se il pacchetto non lo porta).
func FileTerzi(a *Ambiente, nome string) string {
	g, ok := a.Pacchetti.(*gestoreFuoriLinea)
	if !ok || g.fl.Terzi[nome] == "" {
		return ""
	}
	return filepath.Join(g.fl.Dir, g.fl.Terzi[nome])
}

func (p *preparazione) dnf(passi []AzioneFuoriLinea, terzi []string) error {
	a := p.amb
	repos := filepath.Join(p.lav, "repos")
	if err := os.MkdirAll(repos, 0o755); err != nil {
		return err
	}
	for _, t := range terzi { // rpmfusion(-nonfree): il release nel pacchetto, e i suoi depositi per risolvere
		ramo := "free"
		if t == "rpmfusion-nonfree" {
			ramo = "nonfree"
		}
		u := URLRpmFusionRamo(a, ramo)
		p.ev("RPM Fusion: " + u)
		b, err := p.scarica(u)
		if err != nil {
			return err
		}
		rel := filepath.Join("third-party", t, filepath.Base(u))
		if err := p.scriviIn(rel, b); err != nil {
			return err
		}
		if p.fl.Terzi == nil {
			p.fl.Terzi = map[string]string{}
		}
		p.fl.Terzi[t] = rel
		// solo per risolvere e scaricare (le firme dei codec le verifica rpm sulla macchina senza
		// rete, con la chiave che il release porta)
		if err := os.WriteFile(filepath.Join(repos, t+"-fuori-linea.repo"), []byte(
			"["+t+"-fl]\nname=RPM Fusion "+ramo+" (offline preparation)\nmetalink=https://mirrors.rpmfusion.org/metalink?repo="+ramo+"-fedora-$releasever&arch=$basearch\nenabled=1\ngpgcheck=0\n\n"+
				"["+t+"-updates-fl]\nname=RPM Fusion "+ramo+" updates (offline preparation)\nmetalink=https://mirrors.rpmfusion.org/metalink?repo="+ramo+"-fedora-updates-released-$releasever&arch=$basearch\nenabled=1\ngpgcheck=0\n"), 0o644); err != nil {
			return err
		}
	}
	base := p.fl.Origine + "/rpm/" + p.fl.Canale + "/" + p.fl.Bersaglio + "/"
	// solo per RISOLVERE e scaricare: le firme dei .rpm le verifica rpm sulla macchina senza rete
	// (localpkg_gpgcheck=1); qui si controllano i digest dei metadati
	if err := os.WriteFile(filepath.Join(repos, "remotix-offline.repo"), []byte("[remotix-fuori-linea]\nname=REMOTIX (offline preparation)\nbaseurl="+base+
		"\nenabled=1\ngpgcheck=0\nrepo_gpgcheck=0\nincludepkgs="+strings.Join(PacchettiArchivio, " ")+"\n"), 0o644); err != nil {
		return err
	}
	rd := "--setopt=reposdir=/etc/yum.repos.d," + repos
	var cumul []string
	visti := map[string]bool{}
	for i := range passi {
		cumul = append(cumul, passi[i].Nomi...)
		p.ev("risoluzione: " + strings.Join(cumul, " "))
		out, c, err := a.Esegui(tempoGestore, "dnf", append([]string{"install", "--assumeno", rd}, cumul...)...)
		if err != nil {
			return err
		}
		nevra, err := nevraTransazione(out, c)
		if err != nil {
			return err
		}
		var nuovi []string
		for _, n := range nevra {
			if !visti[n] {
				visti[n] = true
				nuovi = append(nuovi, n)
			}
		}
		rel := filepath.Join("distro", "rpm", passi[i].ID)
		dest := filepath.Join(p.dir, rel)
		if err := os.MkdirAll(dest, 0o755); err != nil {
			return err
		}
		if len(nuovi) > 0 {
			if _, err := esegui(a, tempoGestore, "dnf", append([]string{"download", rd, "--destdir", dest}, nuovi...)...); err != nil {
				return err
			}
		}
		voluti := map[string]bool{}
		for _, n := range nuovi {
			voluti[n+".rpm"] = true
		}
		voci, _ := filepath.Glob(dest + "/*.rpm")
		for _, v := range voci {
			if !voluti[filepath.Base(v)] {
				os.Remove(v)
				continue
			}
			out, err := esegui(a, time.Minute, "rpm", "-qp", "--nosignature", "--qf", `RX %{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n`, v)
			if err != nil {
				return err
			}
			var c []string
			for _, riga := range strings.Split(out, "\n") {
				if f := strings.Fields(riga); len(f) == 4 && f[0] == "RX" {
					c = f[1:]
				}
			}
			if len(c) != 3 {
				return fmt.Errorf("%s: rpm -qp does not answer", v)
			}
			sha, _ := Sha256File(v)
			r := filepath.Join(rel, filepath.Base(v))
			org := "distribuzione"
			for _, n := range PacchettiArchivio {
				if c[0] == n {
					org = "remotix"
				}
			}
			p.fl.Artefatti = append(p.fl.Artefatti, Artefatto{Nome: c[0], Versione: c[1], Arch: c[2], Origine: org, File: r, Sha256: sha, Esito: "new"})
			passi[i].Artefatti = append(passi[i].Artefatti, r)
			if org == "remotix" { // anche nell'archivio locale, dove il deposito di REMOTIX lo cerca
				b, _ := os.ReadFile(v)
				if err := p.scriviIn(filepath.Join("archive", "rpm", p.fl.Canale, p.fl.Bersaglio, filepath.Base(v)), b); err != nil {
					return err
				}
			}
		}
		sort.Strings(passi[i].Artefatti)
		p.fl.Azioni = append(p.fl.Azioni, passi[i])
	}
	sort.Slice(p.fl.Artefatti, func(i, j int) bool { return p.fl.Artefatti[i].Nome < p.fl.Artefatti[j].Nome })

	// i metadati firmati del deposito di REMOTIX (repo_gpgcheck: repomd.xml.asc)
	p.ev("the signed metadata of the REMOTIX archive (" + p.fl.Bersaglio + ")")
	pre := "rpm/" + p.fl.Canale + "/" + p.fl.Bersaglio + "/repodata/"
	md, err := p.daArchivio(pre + "repomd.xml")
	if err != nil {
		return err
	}
	if _, err := p.daArchivio(pre + "repomd.xml.asc"); err != nil {
		return err
	}
	for _, m := range regexp.MustCompile(`href="repodata/([^"]+)"`).FindAllStringSubmatch(string(md), -1) {
		if _, err := p.daArchivio(pre + m[1]); err != nil {
			return err
		}
	}
	return nil
}

// nevraTransazione: i pacchetti che una transazione di dnf (install --assumeno) installerebbe,
// aggiornerebbe o retrocederebbe, come nome-versione.arch.
func nevraTransazione(out string, c int) ([]string, error) {
	if !strings.Contains(out, "Transaction Summary") && !strings.Contains(out, "Riepilogo") {
		if strings.Contains(out, "Nothing to do") {
			return nil, nil
		}
		return nil, fmt.Errorf("dnf install --assumeno: exit %d: %s", c, ultimeRighe(out, 6))
	}
	var nevra []string
	in := false
	for _, riga := range strings.Split(out, "\n") {
		t := strings.TrimSpace(riga)
		if strings.HasSuffix(t, ":") && !strings.HasPrefix(riga, " ") {
			in = strings.HasPrefix(t, "Installing") || strings.HasPrefix(t, "Upgrading") || strings.HasPrefix(t, "Downgrading")
			continue
		}
		f := strings.Fields(t)
		if !in || len(f) < 4 || !archi[f[1]] || f[3] == "@commandline" {
			continue
		}
		ver := f[2]
		if _, dopo, ok := strings.Cut(ver, ":"); ok { // l'epoca non sta nel nome del file
			ver = dopo
		}
		nevra = append(nevra, f[0]+"-"+ver+"."+f[1])
	}
	return nevra, nil
}
