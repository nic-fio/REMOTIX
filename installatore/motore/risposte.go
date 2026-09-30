package motore

import (
	"bufio"
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// Il FILE DI RISPOSTE: l'installazione senza domande (fasi/17-l-installatore.md §6.0 regola 3,
// §6.5 punto 10, §6.6.12, R21). Il consenso è DATO PRIMA, in un file; il motore lo trasforma nel
// piano, e il piano porta con sé le risposte (testo, sha256, voce per voce) e le scrive nel
// registro dell'operazione come ogni altro piano.
//
// ⛔ Senza domande NON vuol dire senza consenso: ogni consenso che su QUESTA macchina servirebbe
// (l'archivio di terzi D5, solo dove serve; il firewall D6, solo se firewalld è
// acceso; gli aggiornamenti automatici, solo dall'archivio) deve avere nel file una risposta
// esplicita, «si» o «no». Se ne manca uno il piano si fa lo stesso (per mostrarlo), ma
// l'operazione è BLOCCATA con RX-RISPOSTE-001, prima di toccare niente: mai un «sì» per scelta
// tacita. Una voce sconosciuta (un errore di battitura in un consenso) ferma tutto: RX-RISPOSTE-002.
//
// Il formato (remotix-risposte/1), testo semplice, una voce per riga, «#» per i commenti:
//
//	formato = remotix-risposte/1          # obbligatoria, sempre la prima voce che si guarda
//	lingua = it                           # it · en (DECISIONI §10.15; se manca: la lingua del sistema)
//	porta = 7447                          # TCP (la pagina) e UDP (QUIC); se manca: 7447
//	archivio = https://…                  # l'archivio di REMOTIX (o --archivio); canale = stabile · candidato
//	utenti = tutti                        # chi mettere nei gruppi della scheda: «tutti» o nomi separati da virgola
//	desktop = gnome                       # SOLO se sulla macchina manca un desktop supportato: gnome · kde ·
//	                                      #   xfce · lxqt · no. Se manca la voce: quello di riferimento della
//	                                      #   distribuzione (fasi/17 §10, parola dell'utente)
//	                                      # (consenso.cinture: RITIRATA — D4, le cinture sempre; in un file
//	                                      #  vecchio si annota fra le «superflue» e non conta)
//	consenso.firewall = si                # D6: aprire la porta nel firewall (serve solo se firewalld è acceso)
//	consenso.deposito.rpmfusion = si      # D5: un archivio di terzi (rpmfusion, packman, epel), solo dove serve
//	consenso.aggiornamenti = si           # il timer degli aggiornamenti automatici (DECISIONI §10.10, D14)
//
// Valori dei consensi: «si» (anche «sì», «yes») o «no». Una voce data dove non serve (il firewall su
// una macchina senza firewalld) si annota e non fa niente.

// FormatoRisposte: la versione del formato del file di risposte.
const FormatoRisposte = "remotix-risposte/1"

// FileRisposte: il file letto e controllato.
type FileRisposte struct {
	Percorso string
	Testo    []byte
	Sha256   string
	Voci     map[string]string
}

// RifRisposte: che cosa del file di risposte entra nel piano (e quindi nel suo digest e nel registro).
type RifRisposte struct {
	Formato string            `json:"formato"`
	File    string            `json:"file"`
	Sha256  string            `json:"sha256"`
	Voci    map[string]string `json:"voci"`
	// Predefinite: le scelte (non i consensi) prese dal valore predefinito perché il file taceva
	Predefinite []string `json:"predefinite"`
	// Mancanti: i consensi che su questa macchina servono e che il file non dà ⇒ BLOCCATA
	Mancanti []string `json:"mancanti"`
	// Superflue: voci date dove non servono (annotate, senza effetto)
	Superflue []string `json:"superflue"`
}

var vociNote = map[string]bool{
	"formato": true, "lingua": true, "porta": true, "archivio": true, "canale": true, "utenti": true,
	"desktop": true, "consenso.cinture": true, "consenso.firewall": true, "consenso.aggiornamenti": true,
	"consenso.deposito.epel": true, "consenso.deposito.rpmfusion": true, "consenso.deposito.packman": true,
}

// LeggiRisposte legge e controlla il file: formato, voci conosciute, valori ammessi. Non guarda la
// macchina (quello lo fa OpzioniDaRisposte).
func LeggiRisposte(percorso string) (*FileRisposte, error) {
	b, err := os.ReadFile(percorso)
	if err != nil {
		return nil, Errore("RX-RISPOSTE-002", err.Error())
	}
	abs, _ := filepath.Abs(percorso)
	r := &FileRisposte{Percorso: abs, Testo: b, Sha256: Sha256(b), Voci: map[string]string{}}
	s := bufio.NewScanner(bytes.NewReader(b))
	n := 0
	for s.Scan() {
		n++
		riga := s.Text()
		if i := strings.Index(riga, "#"); i >= 0 {
			riga = riga[:i]
		}
		riga = strings.TrimSpace(riga)
		if riga == "" {
			continue
		}
		k, v, ok := strings.Cut(riga, "=")
		k, v = strings.ToLower(strings.TrimSpace(k)), strings.TrimSpace(v)
		if !ok || k == "" {
			return nil, Errore("RX-RISPOSTE-002", fmt.Sprintf("riga %d: «%s» non è «voce = valore»", n, s.Text()))
		}
		if !vociNote[k] {
			return nil, Errore("RX-RISPOSTE-002", fmt.Sprintf("riga %d: voce sconosciuta «%s»", n, k))
		}
		if _, doppia := r.Voci[k]; doppia {
			return nil, Errore("RX-RISPOSTE-002", fmt.Sprintf("riga %d: «%s» data due volte", n, k))
		}
		if strings.HasPrefix(k, "consenso.") {
			sn, ok := rispostaSiNo(v)
			if !ok {
				return nil, Errore("RX-RISPOSTE-003", fmt.Sprintf("riga %d: %s = «%s» (si · no)", n, k, v))
			}
			v = sn
		}
		r.Voci[k] = v
	}
	if f := r.Voci["formato"]; f != FormatoRisposte {
		return nil, Errore("RX-RISPOSTE-002", fmt.Sprintf("formato «%s», serve «%s»", f, FormatoRisposte))
	}
	if v, ok := r.Voci["lingua"]; ok && v != "it" && v != "en" {
		return nil, Errore("RX-RISPOSTE-003", "lingua = «"+v+"» (it · en)")
	}
	if v, ok := r.Voci["porta"]; ok {
		if p, err := strconv.Atoi(v); err != nil || p < 1 || p > 65535 {
			return nil, Errore("RX-RISPOSTE-003", "porta = «"+v+"»")
		}
	}
	if v, ok := r.Voci["canale"]; ok && v != "stabile" && v != "candidato" {
		return nil, Errore("RX-RISPOSTE-003", "canale = «"+v+"» (stabile · candidato)")
	}
	if v, ok := r.Voci["desktop"]; ok {
		ok2 := v == "no"
		for _, d := range DESKTOP {
			ok2 = ok2 || v == d
		}
		if !ok2 {
			return nil, Errore("RX-RISPOSTE-003", "desktop = «"+v+"» (gnome · kde · xfce · lxqt · no)")
		}
	}
	return r, nil
}

func rispostaSiNo(v string) (string, bool) {
	switch strings.ToLower(v) {
	case "si", "sì", "yes", "y", "s":
		return "si", true
	case "no", "n":
		return "no", true
	}
	return "", false
}

// Porta: la porta del file (0 se non c'è).
func (r *FileRisposte) Porta() int {
	p, _ := strconv.Atoi(r.Voci["porta"])
	return p
}

// DepositiDaChiedere: gli archivi di terzi che su questa macchina servono (D5): quello di H.264 se la
// scheda di serie non basta, e quelli dei desktop installati (o di quello che si installerà).
func DepositiDaChiedere(rap *Rapporto, prof *Profilo, desktopScelto string) []string {
	visti := map[string]bool{}
	var r []string
	metti := func(d string) {
		if d != "" && !visti[d] && prof.V("deposito."+d) != "presente" {
			visti[d] = true
			r = append(r, d)
		}
	}
	if rap.pl == nil {
		return nil
	}
	if !rap.pl.H264.SchedaDiSerie {
		metti(rap.pl.H264.Deposito)
	}
	for _, e := range rap.Desktop {
		installato := e.Installato != "" && e.Installato != "assente" && e.Installato != "sconosciuto"
		if e.Livello == NON_SUPPORTATA || (!installato && e.Desktop != desktopScelto) {
			continue
		}
		for _, d := range rap.pl.Desktop[e.Desktop].Depositi {
			metti(d)
		}
	}
	sort.Strings(r)
	return r
}

// OpzioniDaRisposte: dal file e dalla macchina, le opzioni del piano d'installazione e il
// riferimento alle risposte (coi consensi mancanti). o porta già archivio, canale, chiave e
// impronta della riga di comando; il file non li cambia se sono dati (una differenza è un errore).
func (r *FileRisposte) OpzioniDaRisposte(rap *Rapporto, prof *Profilo, amb *Ambiente, o OpzioniInstallazione) (OpzioniInstallazione, *RifRisposte, string, error) {
	rif := &RifRisposte{Formato: FormatoRisposte, File: r.Percorso, Sha256: r.Sha256, Voci: r.Voci,
		Predefinite: []string{}, Mancanti: []string{}, Superflue: []string{}}
	if a := r.Voci["archivio"]; a != "" {
		if o.Archivio != "" && strings.TrimRight(o.Archivio, "/") != strings.TrimRight(a, "/") {
			return o, nil, "", Errore("RX-RISPOSTE-003", "archivio: il file dice «"+a+"», la riga di comando «"+o.Archivio+"»")
		}
		o.Archivio = a
	}
	if c := r.Voci["canale"]; c != "" {
		o.Canale = c
	}
	if p := r.Porta(); p != 0 {
		if o.Porta != 0 && o.Porta != 7447 && o.Porta != p {
			return o, nil, "", Errore("RX-RISPOSTE-003", fmt.Sprintf("porta: il file dice %d, la riga di comando %d", p, o.Porta))
		}
		o.Porta = p
	} else {
		rif.Predefinite = append(rif.Predefinite, "porta = 7447")
	}
	switch u := r.Voci["utenti"]; u {
	case "", "tutti":
		if u == "" {
			rif.Predefinite = append(rif.Predefinite, "utenti = tutti")
		}
		o.Utenti = nil
	default:
		for _, x := range strings.Split(u, ",") {
			if x = strings.TrimSpace(x); x != "" {
				o.Utenti = append(o.Utenti, x)
			}
		}
	}

	// un consenso: la risposta c'è ⇒ vale; manca ⇒ si annota fra i mancanti (e intanto vale «no»)
	consenso := func(k string, serve bool) bool {
		v, dato := r.Voci[k]
		switch {
		case !serve && dato:
			rif.Superflue = append(rif.Superflue, k)
			return false
		case !serve:
			return false
		case !dato:
			rif.Mancanti = append(rif.Mancanti, k)
			return false
		}
		return v == "si"
	}

	// il desktop, se manca (una SCELTA con la sua predefinita: fasi/17 §10)
	desktop := ""
	if s := SceltaDesktop(rap); s != nil {
		desktop = r.Voci["desktop"]
		if desktop == "" {
			desktop = s.Predefinita
			rif.Predefinite = append(rif.Predefinite, "desktop = "+desktop)
		} else {
			ok := false
			for _, x := range s.Opzioni {
				ok = ok || x == desktop
			}
			if !ok {
				return o, nil, "", Errore("RX-RISPOSTE-003", fmt.Sprintf("desktop = «%s»: su questa macchina le scelte sono %v", desktop, s.Opzioni))
			}
		}
	} else if _, dato := r.Voci["desktop"]; dato {
		rif.Superflue = append(rif.Superflue, "desktop")
	}

	if _, dato := r.Voci["consenso.cinture"]; dato { // D4: sempre; la voce vecchia si dice e non conta
		rif.Superflue = append(rif.Superflue, "consenso.cinture ("+T("risposte.cinture_ignorata")+")")
	}
	o.ApriFirewall = consenso("consenso.firewall", amb.Firewall != nil && amb.Firewall.Nome() == "firewalld")
	o.SenzaTimer = !consenso("consenso.aggiornamenti", o.Archivio != "")
	servono := map[string]bool{}
	for _, d := range DepositiDaChiedere(rap, prof, desktop) {
		servono[d] = true
	}
	o.Depositi = nil
	for _, d := range []string{"epel", "packman", "rpmfusion"} {
		if consenso("consenso.deposito."+d, servono[d]) {
			o.Depositi = append(o.Depositi, d)
		}
	}
	return o, rif, desktop, nil
}

// PianoDaRisposte: il piano d'installazione dal file di risposte. Il piano porta le risposte; se
// non manca nessun consenso, porta anche l'approvazione DEL FILE (il consenso dato prima, §6.6.12),
// col suo sha256; se ne manca uno, niente approvazione e Applica lo ferma (RX-RISPOSTE-001).
func PianoDaRisposte(r *FileRisposte, prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, o OpzioniInstallazione) (*Piano, error) {
	o, rif, desktop, err := r.OpzioniDaRisposte(rap, prof, amb, o)
	if err != nil {
		return nil, err
	}
	p, err := PianoInstallazione(prof, rap, cat, amb, o)
	if err != nil {
		return nil, err
	}
	if desktop != "" {
		if err := p.Rispondi("desktop", desktop); err != nil {
			return nil, err
		}
	}
	p.Risposte = rif
	if len(rif.Mancanti) == 0 {
		p.Approvazione = &Approvazione{Da: "file di risposte", Ora: ora(),
			Modo:        "senza domande: file di risposte " + r.Percorso + " (sha256 " + r.Sha256[:16] + "…)",
			DigestPiano: p.Digest()}
	}
	return p, nil
}
