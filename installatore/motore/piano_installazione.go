package motore

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
)

// OpzioniInstallazione: le poche cose che chi installa sceglie (§10: la porta, chi entra nei gruppi
// della scheda) e da dove vengono i pacchetti (il pacchetto unico, DECISIONI §10.36).
type OpzioniInstallazione struct {
	// Pacchetti: la cartella packages/ del .run (o, nelle prove, una cartella qualunque con
	// <bersaglio>/*.deb|*.rpm|*.pkg.tar.zst); "" ⇒ nessun pacchetto (RX-MANCA-004)
	Pacchetti string
	Utenti    []string // chi mettere nei gruppi della scheda; vuoto ⇒ le persone della macchina
	Porta     int
	// Aggiornamento: REMOTIX è già installato (un'installazione CONFERMATA): il piano mette solo i
	// pacchetti nuovi del .run; gruppi, porta e servizio ci sono già
	Aggiornamento bool
}

// PianoInstallazione: il piano dell'installazione (o dell'aggiornamento) di REMOTIX (§6.0, rifatto il
// 10 ott 2026 per DECISIONI §10.36). REMOTIX NON modifica il sistema: niente archivi di terzi, driver,
// desktop, firewall né cinture di sistema. Quel che manca (Rapporto.Mancano) va nel piano come
// BLOCCANTE e l'operazione si ferma prima di toccare niente; provvede l'amministratore. Il piano fa:
// i pacchetti di REMOTIX dal .run (le dipendenze le prende il gestore dagli archivi della macchina) →
// i gruppi della scheda (l'eccezione voluta dall'utente) → la porta, se non è quella di serie →
// l'accensione. Il gestore simula subito: il piano mostra i pacchetti esatti prima della domanda.
func PianoInstallazione(prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, o OpzioniInstallazione) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := strconv.Itoa(o.Porta)
	mestiere := "installation"
	if o.Aggiornamento {
		mestiere = "upgrade"
	}
	pn := &Piano{Formato: Formato, Oggetto: "plan", ID: nuovoID(), Creato: ora(), Mestiere: mestiere,
		Motore:   RifMotore{VersioneMotore, DigestMotore()},
		Catalogo: RifCatalogo{cat.Versione, cat.Digest}, Piattaforma: rap.Piattaforma,
		Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}}

	// quel che manca, e i motivi per cui su questa macchina REMOTIX non va: si dicono, e si ferma
	pn.NonFatto = append(pn.NonFatto, rap.Mancano...)
	for _, m := range rap.Messaggi {
		if m.Gravita == BLOCCANTE && !haCodice(pn.NonFatto, m.Codice) {
			pn.NonFatto = append(pn.NonFatto, m)
		}
	}
	if !haDesktopBuono(rap) && !rap.SenzaDesktop {
		for _, e := range rap.Desktop {
			for _, m := range e.Motivi {
				if !haCodice(pn.NonFatto, m.Codice) {
					pn.NonFatto = append(pn.NonFatto, m)
				}
			}
		}
	}

	file, err := PacchettiDelRun(amb, o.Pacchetti)
	if err != nil {
		pn.NonFatto = append(pn.NonFatto, Msg("RX-MANCA-004", err.Error()))
	} else {
		// le dipendenze che il desktop chiede (labwc, wlr-randr, un carattere): col gestore, insieme
		pn.Azioni = append(pn.Azioni, PianoPacchetti("packages", strings.Join(file, ","), strings.Join(rap.NomiDipendenze(), ",")))
		pn.Dipendenze = rap.Dipendenze
	}
	if !o.Aggiornamento {
		utenti := o.Utenti
		if len(utenti) == 0 {
			utenti = Persone(amb)
		}
		gruppi := GruppiScheda(amb)
		for _, u := range utenti {
			for _, g := range gruppi {
				pn.Azioni = append(pn.Azioni, PianoGruppo("group-"+u+"-"+g, u, g))
			}
		}
		if len(gruppi) == 0 {
			pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.nessun_gruppo")})
		} else {
			pn.Dichiarate = append(pn.Dichiarate, T("np.gruppi", strings.Join(gruppi, ", ")))
		}
		// la porta scelta (§6.4: i predefiniti in /usr, le scelte in /etc): remotix.service la legge
		// da /etc/remotix/remotix.conf.d/*.conf. Solo se non è quella di serie
		if o.Porta != 7447 {
			pn.Azioni = append(pn.Azioni, PianoScriviFile("port", "/etc/remotix/remotix.conf.d/porta.conf", "REMOTIX_PORTA="+ps+"\n", "0644"))
		}
		pn.Azioni = append(pn.Azioni, PianoAccendiServizio("service", "remotix.service", o.Porta))
		// il firewall è dell'amministratore (§10.36): lo si dice, non lo si apre
		switch g := amb.Firewall.Nome(); g {
		case "none", "":
		default:
			pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: AVVISO, Testo: T("np.firewall", g, ps)})
		}
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.sospensione")})
	}
	for _, e := range rap.Desktop {
		if e.Livello != NON_SUPPORTATA && e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown" {
			pn.Condizioni = append(pn.Condizioni, e.Condizioni...)
		}
	}
	// la simulazione del gestore: i pacchetti esatti, PRIMA della domanda. Se il gestore non sa
	// installare (una dipendenza che nessun archivio della macchina dà), lo dice qui
	if !Bloccato(pn) && amb.Pacchetti != nil && len(file) > 0 {
		var veri []string
		for _, f := range file {
			veri = append(veri, amb.P(f))
		}
		ins, err := amb.Pacchetti.Simula(veri, rap.NomiDipendenze())
		if err != nil {
			pn.NonFatto = append(pn.NonFatto, Msg("RX-PACCHETTI-005", err.Error()))
		}
		pn.Pacchetti = ins
	}
	im, err := CalcolaImpronta(prof, cat, pn.Azioni, pn.Dipende, &Contesto{Amb: amb})
	if err != nil {
		return nil, err
	}
	pn.Impronta = *im
	return pn, nil
}

// haDesktopBuono: almeno un desktop installato che REMOTIX sostiene.
func haDesktopBuono(rap *Rapporto) bool {
	for _, e := range rap.Desktop {
		if e.Livello != NON_SUPPORTATA && e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown" {
			return true
		}
	}
	return false
}

// Bloccato: il piano ha un messaggio BLOCCANTE (quel che manca): non si applica.
func Bloccato(p *Piano) bool {
	for _, m := range p.NonFatto {
		if m.Gravita == BLOCCANTE {
			return true
		}
	}
	return false
}

// NienteDaFare: la simulazione dice che i pacchetti del .run sono già tutti installati, a quella
// versione (un aggiornamento con lo stesso .run).
func NienteDaFare(p *Piano) bool {
	if len(p.Pacchetti) == 0 {
		return false
	}
	for _, a := range p.Pacchetti {
		if a.Esito != "present" {
			return false
		}
	}
	return true
}

// PacchettiDelRun: i file dei pacchetti di REMOTIX per QUESTA distribuzione, nella cartella
// packages/<bersaglio>/ del .run. remotix-selinux solo dove c'è la politica targeted (il pacchetto
// remotix lo chiede lì, e altrove porterebbe con sé la politica intera).
func PacchettiDelRun(a *Ambiente, dir string) ([]string, error) {
	if dir == "" {
		return nil, fmt.Errorf("no packages: run the REMOTIX .run file")
	}
	b := Bersaglio(a)
	voci, _ := filepath.Glob(filepath.Join(a.P(dir), b, "*"))
	var r []string
	selinux := false
	if st, err := os.Stat(a.P("/etc/selinux/targeted")); err == nil && st.IsDir() {
		selinux = true
	}
	for _, v := range voci {
		n := filepath.Base(v)
		if !strings.HasSuffix(n, ".deb") && !strings.HasSuffix(n, ".rpm") && !strings.HasSuffix(n, ".pkg.tar.zst") {
			continue
		}
		if strings.HasPrefix(n, "remotix-selinux") && !selinux {
			continue
		}
		abs, err := filepath.Abs(filepath.Join(dir, b, n))
		if err != nil {
			return nil, err
		}
		r = append(r, abs)
	}
	sort.Strings(r)
	if len(r) == 0 {
		return nil, fmt.Errorf("%s: no packages for %s", dir, b)
	}
	return r, nil
}

// Persone: gli utenti umani della macchina (uid fra UID_MIN e 60000, con una shell vera).
func Persone(a *Ambiente) []string {
	min := 1000
	for _, f := range []string{"/etc/login.defs", "/usr/etc/login.defs"} {
		if t, ok := leggi(a, f); ok {
			for _, r := range strings.Split(t, "\n") {
				c := strings.Fields(r)
				if len(c) == 2 && c[0] == "UID_MIN" {
					if n, err := strconv.Atoi(c[1]); err == nil {
						min = n
					}
				}
			}
			break
		}
	}
	f, err := os.Open(a.P("/etc/passwd"))
	if err != nil {
		return nil
	}
	defer f.Close()
	var r []string
	s := bufio.NewScanner(f)
	for s.Scan() {
		c := strings.Split(s.Text(), ":")
		if len(c) < 7 {
			continue
		}
		uid, _ := strconv.Atoi(c[2])
		if uid < min || uid >= 60000 || strings.HasSuffix(c[6], "nologin") || strings.HasSuffix(c[6], "false") {
			continue
		}
		r = append(r, c[0])
	}
	sort.Strings(r)
	return r
}

// GruppiScheda: i gruppi dei nodi della scheda (/dev/dri/card* e renderD*), root escluso
// (DECISIONI §7.21: i numeri cambiano da una macchina all'altra, si leggono dai nodi).
func GruppiScheda(a *Ambiente) []string {
	gr, _ := LeggiGruppi(a.P("/etc/group"))
	nome := map[string]string{}
	for n, v := range gr {
		nome[v[0]] = n
	}
	visti := map[string]bool{}
	var r []string
	voci, _ := filepath.Glob(a.P("/dev/dri") + "/*")
	for _, v := range voci {
		b := filepath.Base(v)
		if !strings.HasPrefix(b, "card") && !strings.HasPrefix(b, "renderD") {
			continue
		}
		st, err := os.Stat(v)
		if err != nil {
			continue
		}
		sys, ok := st.Sys().(*syscall.Stat_t)
		if !ok || sys.Gid == 0 {
			continue
		}
		n := nome[strconv.Itoa(int(sys.Gid))]
		if n != "" && !visti[n] {
			visti[n] = true
			r = append(r, n)
		}
	}
	sort.Strings(r)
	return r
}
