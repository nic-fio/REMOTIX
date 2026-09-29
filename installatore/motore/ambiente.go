package motore

import (
	"bufio"
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

// L'installatore è UN programma solo (DECISIONI §10.14): con systemd, logind e firewalld parla
// dall'interno, via D-Bus (dbus.go); lancia SOLO i programmi di questo elenco chiuso — dove manca
// un'interfaccia stabile: il gestore di pacchetti e gpasswd/usermod —, col percorso assoluto,
// e ogni chiamata si annota (nel registro dell'operazione, o nel profilo per «verifica»: R41).
//
// ⚠ rpm, dpkg e dpkg-deb stanno nell'elenco perché sono la base dei gestori (l'archivio di rpm non
// si legge senza di lui; dpkg --audit e --configure -a sono il rimedio di §6.6.3). ffmpeg NON c'è
// (decisione del coordinatore, 30 set): la prova «la scheda codifica un fotogramma» la fa in 7a il
// binario di REMOTIX installato (`remotix --prova-codifica`, da fare nel prodotto: §6.5-bis).
var programmiAmmessi = map[string][]string{
	"apt-get":  {"/usr/bin/apt-get"},
	"dnf":      {"/usr/bin/dnf", "/usr/bin/dnf5"},
	"zypper":   {"/usr/bin/zypper"},
	"pacman":   {"/usr/bin/pacman"},
	"rpm":      {"/usr/bin/rpm", "/bin/rpm"},
	"dpkg":     {"/usr/bin/dpkg"},
	"dpkg-deb": {"/usr/bin/dpkg-deb"},
	"remotix":  {"/usr/libexec/remotix/remotix"},
	"gpasswd":  {"/usr/bin/gpasswd", "/usr/sbin/gpasswd", "/bin/gpasswd", "/sbin/gpasswd"},
	"usermod":  {"/usr/sbin/usermod", "/usr/bin/usermod", "/sbin/usermod"},
}

// ErrNonAmmesso: il motore non lancia programmi fuori dall'elenco.
var ErrNonAmmesso = errors.New("programma fuori dall'elenco chiuso del motore (DECISIONI §10.14)")

// ProgrammiAmmessi: l'elenco, per le prove e per il manuale.
func ProgrammiAmmessi() []string {
	var r []string
	for n := range programmiAmmessi {
		r = append(r, n)
	}
	sort.Strings(r)
	return r
}

// Esecutore lancia un programma dell'elenco e ne restituisce l'uscita, il codice d'uscita e un
// errore solo se non si è potuto lanciare (exec.ErrNotFound: non c'è — il caso che fa un fatto
// SCONOSCIUTO, §6.6.7; ErrNonAmmesso: fuori dall'elenco).
type Esecutore func(tempo time.Duration, nome string, argomenti ...string) (uscita string, codice int, err error)

// percorsoAmmesso: il percorso assoluto di un programma dell'elenco, se c'è.
func percorsoAmmesso(nome string) (string, error) {
	cand, ok := programmiAmmessi[nome]
	if !ok {
		return "", ErrNonAmmesso
	}
	for _, p := range cand {
		if st, err := os.Stat(p); err == nil && st.Mode().IsRegular() && st.Mode()&0o111 != 0 {
			return p, nil
		}
	}
	return "", exec.ErrNotFound
}

// eseguiDavvero: percorso assoluto, argomenti fissi, ambiente minimo in lingua C, niente
// ingresso, tempo massimo; e l'annotazione (R41).
func (a *Ambiente) eseguiDavvero(tempo time.Duration, nome string, argomenti ...string) (string, int, error) {
	percorso, err := percorsoAmmesso(nome)
	if err != nil {
		a.annota(nome, argomenti, -1, err)
		return "", -1, err
	}
	ctx, annulla := context.WithTimeout(context.Background(), tempo)
	defer annulla()
	cmd := exec.CommandContext(ctx, percorso, argomenti...)
	cmd.Env = []string{"LC_ALL=C", "PATH=/usr/sbin:/usr/bin:/sbin:/bin", "DEBIAN_FRONTEND=noninteractive"}
	var uscita strings.Builder
	cmd.Stdout = &uscita
	cmd.Stderr = &uscita
	err = cmd.Run()
	codice := 0
	var ee *exec.ExitError
	switch {
	case ctx.Err() == context.DeadlineExceeded:
		codice, err = -1, ctx.Err()
	case errors.As(err, &ee):
		codice, err = ee.ExitCode(), nil
	case err != nil:
		codice = -1
	}
	a.annota(percorso, argomenti, codice, err)
	return uscita.String(), codice, err
}

func (a *Ambiente) annota(percorso string, argomenti []string, codice int, err error) {
	if a.Annota == nil {
		return
	}
	r := percorso + " " + strings.Join(argomenti, " ") + " ⇒ " + strconv.Itoa(codice)
	if err != nil {
		r += " (" + err.Error() + ")"
	}
	a.Annota(r)
}

// GestoreGruppi legge e cambia l'appartenenza ai gruppi.
type GestoreGruppi interface {
	// Membri: i membri espliciti del gruppo, e se il gruppo esiste.
	Membri(gruppo string) (membri []string, gid string, esiste bool, err error)
	// GruppoPrimario: il gid del gruppo principale dell'utente, e se l'utente esiste.
	GruppoPrimario(utente string) (gid string, esiste bool, err error)
	Aggiungi(utente, gruppo string) error
	Togli(utente, gruppo string) error
}

// GestoreUnita abilita, disabilita, accende e spegne le unità di systemd (sul D-Bus).
type GestoreUnita interface {
	// Stato: lo stato del file dell'unità (enabled, disabled, static, masked, not-found…), quel che
	// systemctl is-enabled chiama con lo stesso nome.
	Stato(unita string) (string, error)
	Abilita(unita string) error
	Disabilita(unita string) error
	// Attiva: ActiveState (active, inactive, failed…).
	Attiva(unita string) (string, error)
	Avvia(unita string) error
	Ferma(unita string) error
	Ricarica(unita string) error
	// il bersaglio d'avvio (graphical.target / multi-user.target)
	Predefinito() (string, error)
	ImpostaPredefinito(bersaglio string) error
}

// Sessione: una sessione di logind.
type Sessione struct {
	ID, Utente, Servizio, Stato, Tipo string
}

// GestoreSessioni: logind, sul D-Bus.
type GestoreSessioni interface {
	Elenco() ([]Sessione, error)
	Termina(id string) error
	// Segnale ai processi di UNA sessione (logind KillSession, who=all): resta dentro la sessione.
	Segnale(id string, segnale int32) error
	// Grafici: quanti processi del desktop ha la persona nel suo gestore d'utente.
	Grafici(utente string) (int, error)
	// ChiudiGrafica: ferma le unità del desktop nel gestore d'utente (grafica_utente.go).
	ChiudiGrafica(utente string) ([]string, error)
}

// GestoreFirewall apre e chiude una porta. Oggi solo firewalld (§6.6.4, mandato di T4).
type GestoreFirewall interface {
	Nome() string // "firewalld", "ufw", "nftables", "nessuno"
	ZonaPredefinita() (string, error)
	HaPorta(zona, porta string, permanente bool) (bool, error) // porta = "7447/tcp"
	Aggiungi(zona, porta string, permanente bool) error
	Togli(zona, porta string, permanente bool) error
}

// Ambiente è tutto quel che il motore tocca o legge della macchina. Le prove ne costruiscono uno
// finto sotto una cartella; il motore non sa la differenza.
type Ambiente struct {
	Radice    string // "/" sulla macchina vera; per leggere /etc, /sys, /proc, /usr, /var/lib
	Esegui    Esecutore
	Bus       *Bus // D-Bus di sistema (nil nelle prove)
	Famiglia  string
	Gruppi    GestoreGruppi
	Unita     GestoreUnita
	Firewall  GestoreFirewall
	Pacchetti Gestore
	Sessioni  GestoreSessioni
	Annota    func(riga string) // ogni programma lanciato (R41); nil = nessuno ascolta
}

// P è un percorso della macchina visto dalla radice dell'ambiente.
func (a *Ambiente) P(percorso string) string {
	if a.Radice == "" || a.Radice == "/" {
		return percorso
	}
	return filepath.Join(a.Radice, percorso)
}

// AmbienteVero è la macchina su cui il motore gira.
func AmbienteVero() *Ambiente {
	a := &Ambiente{Radice: "/", Bus: &Bus{}}
	a.Esegui = a.eseguiDavvero
	a.Gruppi = &gruppiVeri{a}
	a.Unita = &unitaDBus{a.Bus}
	a.Firewall = scegliFirewall(a)
	a.Sessioni = &sessioniDBus{a.Bus, a}
	if m, _ := OsRelease(a); m != nil {
		a.Famiglia = Famiglia(m["ID"], m["ID_LIKE"])
	}
	a.Pacchetti = ScegliGestore(a, a.Famiglia)
	return a
}

// LeggiGruppi legge un file nel formato di /etc/group: nome → (gid, membri).
func LeggiGruppi(percorso string) (map[string][2]string, error) {
	f, err := os.Open(percorso)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := map[string][2]string{}
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) < 4 || strings.HasPrefix(c[0], "#") {
			continue
		}
		r[c[0]] = [2]string{c[2], c[3]}
	}
	return r, s.Err()
}

// DividiMembri: "a,b,,c" → [a b c], ordinati.
func DividiMembri(s string) []string {
	var m []string
	for _, x := range strings.Split(s, ",") {
		if x = strings.TrimSpace(x); x != "" {
			m = append(m, x)
		}
	}
	sort.Strings(m)
	return m
}

// LeggiUtente cerca un utente in un file nel formato di /etc/passwd e ne dà il gid.
func LeggiUtente(percorso, utente string) (gid string, esiste bool, err error) {
	f, err := os.Open(percorso)
	if err != nil {
		return "", false, err
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) >= 4 && c[0] == utente {
			return c[3], true, nil
		}
	}
	return "", false, s.Err()
}

// gruppiVeri: si legge /etc/group, si cambia con gpasswd (che tiene anche gshadow e la serratura
// dei file dei conti: non c'è un'interfaccia D-Bus stabile per i gruppi locali). Solo i gruppi
// locali: sono quelli che REMOTIX tocca (§6.4).
type gruppiVeri struct{ a *Ambiente }

func (g *gruppiVeri) Membri(gruppo string) ([]string, string, bool, error) {
	t, err := LeggiGruppi(g.a.P("/etc/group"))
	if err != nil {
		return nil, "", false, err
	}
	v, ok := t[gruppo]
	return DividiMembri(v[1]), v[0], ok, nil
}

func (g *gruppiVeri) GruppoPrimario(utente string) (string, bool, error) {
	return LeggiUtente(g.a.P("/etc/passwd"), utente)
}

func (g *gruppiVeri) Aggiungi(utente, gruppo string) error {
	return eseguiOErrore(g.a, "gpasswd", "-a", utente, gruppo)
}

func (g *gruppiVeri) Togli(utente, gruppo string) error {
	return eseguiOErrore(g.a, "gpasswd", "-d", utente, gruppo)
}

// firewallNonFatto: ufw e nftables sono riconosciuti, ma il motore non li sa ancora cambiare
// (mandato di T4): ogni cambio restituisce RX-FW-004, e il piano lo dichiara prima.
type firewallNonFatto struct{ nome string }

func (f *firewallNonFatto) Nome() string                     { return f.nome }
func (f *firewallNonFatto) ZonaPredefinita() (string, error) { return "", nil }
func (f *firewallNonFatto) HaPorta(string, string, bool) (bool, error) {
	return false, Errore("RX-FW-004", f.nome)
}
func (f *firewallNonFatto) Aggiungi(string, string, bool) error { return Errore("RX-FW-004", f.nome) }
func (f *firewallNonFatto) Togli(string, string, bool) error    { return Errore("RX-FW-004", f.nome) }

// scegliFirewall: quello acceso. firewalld risponde sul bus; ufw si dice acceso nel suo file;
// nftables come unità attiva.
func scegliFirewall(a *Ambiente) GestoreFirewall {
	if fw := (&firewalldDBus{a.Bus}); fw.Acceso() {
		return fw
	}
	if b, err := os.ReadFile(a.P("/etc/ufw/ufw.conf")); err == nil && strings.Contains(string(b), "ENABLED=yes") {
		return &firewallNonFatto{"ufw"}
	}
	if s, err := a.Bus.StatoAttivo("nftables.service"); err == nil && s == "active" {
		return &firewallNonFatto{"nftables"}
	}
	return &firewallNonFatto{"nessuno"}
}

func eseguiOErrore(a *Ambiente, nome string, argomenti ...string) error {
	out, c, err := a.Esegui(2*time.Minute, nome, argomenti...)
	if err != nil {
		return err
	}
	if c != 0 {
		return errors.New(nome + " " + strings.Join(argomenti, " ") + ": uscita " + strconv.Itoa(c) + ": " + strings.TrimSpace(out))
	}
	return nil
}
