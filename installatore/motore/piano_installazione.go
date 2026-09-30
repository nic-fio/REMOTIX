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

// OpzioniInstallazione: le poche cose che chi installa sceglie (§10: la porta; i consensi D5 e
// D6; e — finché D4 è aperta — le cinture).
type OpzioniInstallazione struct {
	Pacchetto    string // il pacchetto di REMOTIX da un file locale (le prove di T3-T5); oppure:
	Archivio     string // l'archivio firmato di REMOTIX (T8): URL di base
	Canale       string // stabile (predefinito) o candidato
	Chiave       string // la chiave pubblica della catena B (armatura ASCII), e la sua impronta
	Impronta     string
	SenzaTimer   bool     // niente aggiornamenti automatici (il timer resta spento)
	Utenti       []string // chi mettere nei gruppi della scheda; vuoto ⇒ le persone della macchina
	Depositi     []string // archivi di terzi col consenso (D5): epel, rpmfusion, packman
	ApriFirewall bool     // D6
	Porta        int
}

// PianoInstallazione: il piano della prima installazione (§6.0, colonna «prima installazione»):
// depositi → desktop (se manca) → pacchetti → gruppi → cinture → firewall → accensione.
func PianoInstallazione(prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, o OpzioniInstallazione) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := strconv.Itoa(o.Porta)
	pn := &Piano{Formato: Formato, Oggetto: "piano", ID: nuovoID(), Creato: ora(), Mestiere: "installazione",
		Motore:   RifMotore{VersioneMotore, DigestMotore()},
		Catalogo: RifCatalogo{cat.Versione, cat.Digest, cat.Scadenza}, Piattaforma: rap.Piattaforma,
		Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}, Scelte: []Scelta{}}

	if o.Archivio != "" {
		par, err := ParametriArchivio(amb, o.Archivio, o.Canale, o.Chiave, o.Impronta)
		if err != nil {
			return nil, err
		}
		pn.Archivio = &RifArchivio{URL: par["archivio"], Canale: par["canale"]}
		pn.Azioni = append(pn.Azioni, PianoDeposito("archivio-remotix", "archivio", par, ""))
	}
	for _, d := range o.Depositi {
		dc := cat.Depositi[d]
		cons := T("consenso.deposito", nonVuoto(dc.Nome, d))
		pn.Azioni = append(pn.Azioni, PianoDeposito("deposito-"+d, d, nil, cons))
		pn.Consensi = append(pn.Consensi, cons)
		// la libavcodec coi codec da quel deposito (§4.2, §11.1 C)
		if rap.pl != nil && rap.pl.H264.Deposito == d && rap.pl.H264.PacchettiCodec != "" {
			pn.Azioni = append(pn.Azioni, PianoPacchettiDa("codec", rap.pl.H264.PacchettiCodec, d))
		}
	}
	// D5 (DECISIONI §10.20): senza l'archivio che porta la codifica H.264, REMOTIX non si installa. Il
	// piano lo dice (BLOCCANTE, col nome dell'archivio) e Applica si ferma prima di toccare niente
	if rap.pl != nil && !rap.pl.H264.SchedaDiSerie && rap.pl.H264.Deposito != "" &&
		prof.V("deposito."+rap.pl.H264.Deposito) != "presente" && !contiene(o.Depositi, rap.pl.H264.Deposito) {
		d := rap.pl.H264.Deposito
		pn.NonFatto = append(pn.NonFatto, Msg("RX-H264-006", nonVuoto(cat.Depositi[d].Nome, d)))
	}
	if s := SceltaDesktop(rap); s != nil {
		pn.Scelte = append(pn.Scelte, *s)
		pn.Consensi = append(pn.Consensi, s.Domanda)
		pn.metteDesktop(s.Predefinita, s.Pacchetti[s.Predefinita], s.Componenti[s.Predefinita])
	}
	switch {
	case o.Archivio != "":
		// dall'archivio: il prodotto, il motore (col timer degli aggiornamenti) e, su apt, la chiave
		nomi := "remotix,remotix-install"
		if amb.Famiglia == "debian" {
			nomi += ",remotix-archive-keyring"
		}
		pn.Azioni = append(pn.Azioni, PianoPacchetti("pacchetti", "", "", nomi))
	case o.Pacchetto != "":
		abs, err := filepath.Abs(o.Pacchetto)
		if err != nil {
			return nil, err
		}
		sha, err := Sha256File(amb.P(abs))
		if err != nil || sha == "" {
			return nil, fmt.Errorf("%s: %v", abs, err)
		}
		pn.Azioni = append(pn.Azioni, PianoPacchetti("pacchetti", abs, sha, ""))
	default:
		return nil, fmt.Errorf("serve l'archivio di REMOTIX (--archivio URL) o un pacchetto (--pacchetto FILE)")
	}
	// i pezzi che il desktop di serie non porta (C-COMPONENTE: labwc, breeze6-wallpapers, un
	// carattere scalabile…): li aggiunge il motore, dopo il pacchetto
	var comp []string
	visti := map[string]bool{}
	for _, e := range rap.Desktop {
		if e.Livello == NON_SUPPORTATA || e.Installato == "" || e.Installato == "assente" || e.Installato == "sconosciuto" {
			continue
		}
		for _, k := range e.Condizioni {
			if k.Codice == "C-COMPONENTE" && k.Componente != "" && !visti[k.Componente] {
				visti[k.Componente] = true
				comp = append(comp, k.Componente)
			}
		}
	}
	if len(comp) > 0 {
		pn.Azioni = append(pn.Azioni, PianoPacchetti("componenti", "", "", strings.Join(comp, ",")))
	}

	utenti := o.Utenti
	if len(utenti) == 0 {
		utenti = Persone(amb)
	}
	gruppi := GruppiScheda(amb)
	for _, u := range utenti {
		for _, g := range gruppi {
			pn.Azioni = append(pn.Azioni, PianoGruppo("gruppo-"+u+"-"+g, u, g))
		}
	}
	if len(gruppi) == 0 {
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.nessun_gruppo")})
	}
	// D4 (DECISIONI §4.7, 15 ago 2026): le tre cinture SEMPRE, senza consenso; il piano lo dichiara
	for _, c := range Cinture {
		pn.Azioni = append(pn.Azioni, PianoCintura(c.ID, c.Sorgente, c.Percorso, c.Ricarica))
	}
	pn.Dichiarate = append(pn.Dichiarate, T("az.cintura.dichiarata"))
	switch g := amb.Firewall.Nome(); {
	case !o.ApriFirewall && g == "firewalld":
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: AVVISO, Testo: T("np.firewall_no", ps)})
	case !o.ApriFirewall:
	case g == "firewalld":
		a := PianoFirewall("firewall", ps)
		pn.Azioni = append(pn.Azioni, a)
		pn.Consensi = append(pn.Consensi, a.Consenso)
	case g == "nessuno":
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.firewall_nessuno")})
	default:
		pn.NonFatto = append(pn.NonFatto, Msg("RX-FW-004", T("np.firewall_mano", g, ps)))
	}
	pn.Azioni = append(pn.Azioni, PianoAccendiServizio("servizio", "remotix.service", o.Porta))
	// gli aggiornamenti automatici (DECISIONI §10.10): il timer del pacchetto remotix-install, spento
	// finché non lo accende il motore — col consenso, che dice che cosa si applicherà da solo (D14)
	if o.Archivio != "" && !o.SenzaTimer {
		cons := T("consenso.aggiornamenti")
		pn.Azioni = append(pn.Azioni, PianoUnitaAccesa("aggiornamenti", "remotix-aggiorna.timer", cons))
		pn.Consensi = append(pn.Consensi, cons)
	}

	for _, e := range rap.Desktop {
		if e.Livello != NON_SUPPORTATA && e.Installato != "" && e.Installato != "assente" && e.Installato != "sconosciuto" {
			pn.Condizioni = append(pn.Condizioni, e.Condizioni...)
		}
	}
	im, err := CalcolaImpronta(prof, cat, pn.Azioni, pn.Dipende, &Contesto{Amb: amb})
	if err != nil {
		return nil, err
	}
	pn.Impronta = *im
	return pn, nil
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
