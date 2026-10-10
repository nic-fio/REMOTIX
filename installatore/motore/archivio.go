package motore

import (
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// L'ARCHIVIO di REMOTIX (T8, §6.5 punti 5-6, §6.6.10): gli archivi firmati (l'unica chiave) delle tre
// famiglie, generati da packaging/archivio/pubblica.sh. Qui: dove sta ciascuno, e che cosa il motore
// scrive sulla macchina perché il gestore di pacchetti lo usi — e SOLO per i pacchetti di REMOTIX:
//
//   - apt: la chiave in un file suo (/usr/share/keyrings/remotix-archive-keyring.asc, poi posseduto
//     dal pacchetto remotix-archive-keyring), il deposito deb822 con Signed-By (mai trusted.gpg.d:
//     la chiave vale per questo deposito e basta) e un PIN: dall'host dell'archivio si prendono solo
//     i pacchetti di REMOTIX (priorità -1 per tutto il resto, R18). L'host, non l'«Origin» del
//     Release: il Release lo scrive chi pubblica, l'host no;
//   - dnf: il .repo con gpgcheck=1, repo_gpgcheck=1, la chiave in /etc/pki/rpm-gpg e includepkgs coi
//     soli pacchetti di REMOTIX (R18). ⚠ rpm --import rende la chiave valida per rpm in generale:
//     rpm non sa legare una chiave a un deposito (limite della famiglia, dichiarato);
//   - pacman: un blocco [remotix] con SigLevel Required in /etc/pacman.conf (Arch non ha una
//     cartella di depositi: il blocco sta fra due righe di marca e si toglie da solo, il resto del
//     file non si tocca) e la chiave nel portachiavi di pacman (pacman-key --add, --lsign-key).
//     ⚠ Anche lì la chiave firmata localmente vale per ogni pacchetto: limite di pacman, dichiarato.
//
// I canali: «stabile» e «candidato» (§6.1); le versioni vecchie restano nell'archivio (R11).

// PacchettiArchivio: i soli pacchetti che l'archivio di REMOTIX può dare (il pin, includepkgs).
// remotix-selinux (T6, solo .rpm): lo tira remotix dove c'è la politica targeted — senza, dnf non
// lo trova nel nostro archivio (includepkgs) e la transazione non si risolve.
var PacchettiArchivio = []string{"remotix", "remotix-install", "remotix-archive-keyring", "remotix-selinux"}

// ChiaveApt: dove sta la chiave dell'archivio per apt (la stessa del pacchetto remotix-archive-keyring).
const ChiaveApt = "/usr/share/keyrings/remotix-archive-keyring.asc"

// Marche del blocco di pacman.conf.
const (
	inizioBloccoPacman = "# >>> remotix — added by remotix-install (do not edit between the two marker lines)"
	// marcaPacman: l'inizio della riga di marca, che la cerca. La riga intera era in italiano fino al
	// 10 ott 2026 (DECISIONI §10.35): una macchina installata prima si ritrova lo stesso.
	marcaPacman      = "# >>> remotix"
	fineBloccoPacman = "# <<< remotix"
)

// BersaglioArchivio: il nome della distribuzione nell'archivio (debian13, ubuntu2604, fedora44,
// alma10, tumbleweed, leap16, arch).
func BersaglioArchivio(a *Ambiente) string {
	m, _ := OsRelease(a)
	id, v := m["ID"], strings.ReplaceAll(m["VERSION_ID"], ".", "")
	switch {
	case id == "arch" || strings.Contains(m["ID_LIKE"], "arch"):
		return "arch"
	case id == "opensuse-tumbleweed":
		return "tumbleweed"
	case id == "opensuse-leap":
		return "leap" + strings.Split(m["VERSION_ID"], ".")[0]
	case id == "almalinux" || id == "rocky" || id == "rhel":
		return "alma" + strings.Split(m["VERSION_ID"], ".")[0]
	}
	return id + v
}

// ParametriArchivio: i parametri del passo aggiungi-deposito «archivio» per questa macchina.
func ParametriArchivio(a *Ambiente, base, canale, chiave, impronta string) (map[string]string, error) {
	base = strings.TrimRight(base, "/")
	u, err := url.Parse(base)
	// file:///…: l'archivio locale di un pacchetto fuori linea (§6.6.12, fuorilinea.go)
	if err != nil || (u.Host == "" && !(u.Scheme == "file" && strings.HasPrefix(u.Path, "/"))) {
		return nil, fmt.Errorf("the archive address is not a URL: %q", base)
	}
	canale = nonVuoto(canale, "stabile")
	b := BersaglioArchivio(a)
	p := map[string]string{"nome": "remotix", "archivio": base, "canale": canale, "chiave": chiave, "impronta": impronta,
		"host": u.Hostname(), "pacchetti": strings.Join(PacchettiArchivio, ",")}
	switch a.Famiglia {
	case "debian":
		p["url"], p["suite"], p["componenti"] = base+"/deb", b+"-"+canale, "main"
	case "fedora", "suse":
		p["url"] = base + "/rpm/" + canale + "/" + b + "/"
	case "arch":
		p["url"] = base + "/pacman/" + canale + "/$arch"
	default:
		return nil, Errore("RX-PACCHETTI-003", a.Famiglia)
	}
	return p, nil
}

// bloccoPacman: il blocco [remotix] di pacman.conf.
func bloccoPacman(url string) string {
	return inizioBloccoPacman + "\n[remotix]\nSigLevel = Required DatabaseRequired\nServer = " + url + "\n" + fineBloccoPacman + "\n"
}

// togliBlocco: il testo senza il blocco fra le marche (e senza la riga vuota messa prima).
func togliBlocco(t string) (string, bool) {
	i := strings.Index(t, marcaPacman)
	if i < 0 {
		return t, false
	}
	j := strings.Index(t[i:], fineBloccoPacman)
	if j < 0 {
		return t, false
	}
	fine := i + j + len(fineBloccoPacman)
	if fine < len(t) && t[fine] == '\n' {
		fine++
	}
	inizio := i
	if inizio > 0 && strings.HasSuffix(t[:inizio], "\n\n") {
		inizio--
	}
	return t[:inizio] + t[fine:], true
}

// pacmanConf: la configurazione di pacman col blocco (presente, o da mettere).
func (d *deposito) pacmanConf(c *Contesto) (string, bool, error) {
	b, err := os.ReadFile(c.Amb.P("/etc/pacman.conf"))
	if err != nil {
		return "", false, err
	}
	t := string(b)
	return t, strings.Contains(t, marcaPacman), nil
}

func (d *deposito) mettiBloccoPacman(c *Contesto) error {
	t, c2, err := d.pacmanConf(c)
	if err != nil || c2 {
		return err
	}
	if !strings.HasSuffix(t, "\n") {
		t += "\n"
	}
	return ScriviAtomico(c.Amb.P("/etc/pacman.conf"), []byte(t+"\n"+bloccoPacman(d.par["url"])), 0o644)
}

func (d *deposito) togliBloccoPacman(c *Contesto) error {
	t, c2, err := d.pacmanConf(c)
	if err != nil || !c2 {
		return err
	}
	senza, _ := togliBlocco(t)
	if err := ScriviAtomico(c.Amb.P("/etc/pacman.conf"), []byte(senza), 0o644); err != nil {
		return err
	}
	for _, f := range []string{"remotix.db", "remotix.db.sig", "remotix.files", "remotix.files.sig"} {
		os.Remove(c.Amb.P("/var/lib/pacman/sync/" + f))
	}
	return nil
}

// chiavePacman: la chiave dell'archivio è nel portachiavi di pacman?
func (d *deposito) chiavePacman(c *Contesto) (bool, error) {
	_, cod, err := c.Amb.Esegui(time.Minute, "pacman-key", "--list-keys", d.par["impronta"])
	if err != nil {
		return false, err
	}
	return cod == 0, nil
}

func (d *deposito) mettiChiavePacman(c *Contesto) error {
	f := filepath.Join(c.Cartella, "chiave-archivio.asc")
	if err := ScriviAtomico(f, []byte(d.par["chiave"]), 0o600); err != nil {
		return err
	}
	if _, err := esegui(c.Amb, time.Minute, "pacman-key", "--add", f); err != nil {
		return err
	}
	_, err := esegui(c.Amb, time.Minute, "pacman-key", "--lsign-key", d.par["impronta"])
	return err
}

// ConfSoloRemotix: una configurazione di pacman col SOLO deposito di REMOTIX, per rinfrescare il suo
// database senza rinfrescare gli altri (pacman -Sy li rinfrescherebbe tutti: il primo passo di un
// aggiornamento parziale, che Arch non sostiene).
func ConfSoloRemotix(a *Ambiente, dir string) (string, error) {
	b, err := os.ReadFile(a.P("/etc/pacman.conf"))
	if err != nil {
		return "", err
	}
	t := string(b)
	i := strings.Index(t, marcaPacman)
	if i < 0 {
		return "", fmt.Errorf("the [remotix] repository is not in /etc/pacman.conf")
	}
	j := strings.Index(t[i:], fineBloccoPacman)
	blocco := t[i : i+j]
	f := filepath.Join(dir, "pacman-solo-remotix.conf")
	if err := ScriviAtomico(f, []byte("[options]\nArchitecture = auto\n\n"+blocco), 0o600); err != nil {
		return "", err
	}
	return f, nil
}
