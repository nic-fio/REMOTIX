package motore

import (
	"fmt"
	"sort"
	"strings"
)

// Quel che le interfacce (TUI e GUI, T9) chiedono al motore oltre ai sette oggetti: QUALI domande
// fare su questa macchina, e il piano dalle risposte date. ⛔ La decisione di che cosa chiedere e
// come le risposte diventano azioni sta QUI, nel motore, e usa le stesse regole del file di
// risposte (§6.6.12): le interfacce mostrano e raccolgono, non scelgono (§6.6.1, R36).

// Domande: le scelte di chi installa su QUESTA macchina (fasi/17 §10: quasi nessuna).
type Domande struct {
	// Porta: la predefinita (7447); si chiede sempre, una sola, vale per TCP e UDP
	Porta int `json:"porta"`
	// Firewall: "aperto" (firewalld lascia già passare la porta) · "chiuso" (firewalld acceso, la
	// porta no: consenso D6) · "nessuno" (firewalld spento o assente) · "altro:<nome>" (ufw, nft…:
	// il motore non lo tocca, lo dice)
	Firewall string `json:"firewall"`
	// Depositi: gli archivi di terzi che su questa macchina servono (D5), col nome da mostrare
	Depositi []DomandaDeposito `json:"depositi"`
	// Desktop: la scelta del desktop, solo se sulla macchina non ce n'è uno supportato
	Desktop *Scelta `json:"desktop,omitempty"`
	// Aggiornamenti: il consenso al timer si chiede solo se si installa da un archivio
	Aggiornamenti bool `json:"aggiornamenti"`
	// SenzaScheda: le persone a cui manca il permesso di usare la scheda (il motore le iscrive)
	SenzaScheda []string `json:"senza_scheda"`
	// Persone: chi potrà entrare (le persone della macchina; root è escluso)
	Persone []string `json:"persone"`
}

// DomandaDeposito: un archivio di terzi da chiedere, e per che cosa serve.
type DomandaDeposito struct {
	ID    string `json:"id"`   // rpmfusion · packman · epel
	Nome  string `json:"nome"` // «RPM Fusion (free)»
	Per   string `json:"per"`  // "h264" · "desktop"
	Serve bool   `json:"serve"`
}

// DomandeDaFare: le domande su questa macchina, dal profilo e dal rapporto (le stesse regole di
// OpzioniDaRisposte). desktopScelto conta per i depositi che chiede quel desktop.
func DomandeDaFare(prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, porta int, archivio bool, desktopScelto string) *Domande {
	if porta == 0 {
		porta = 7447
	}
	d := &Domande{Porta: porta, Aggiornamenti: archivio, Depositi: []DomandaDeposito{}, SenzaScheda: []string{}}
	d.Desktop = SceltaDesktop(rap)
	if d.Desktop != nil && desktopScelto == "" {
		desktopScelto = d.Desktop.Predefinita
	}
	per264 := ""
	if rap.pl != nil && !rap.pl.H264.SchedaDiSerie {
		per264 = rap.pl.H264.Deposito
	}
	for _, x := range DepositiDaChiedere(rap, prof, desktopScelto) {
		nome := x
		if cat != nil {
			if dc, ok := cat.Depositi[x]; ok && dc.Nome != "" {
				nome = dc.Nome
			}
		}
		per := "desktop"
		if x == per264 {
			per = "h264"
		}
		d.Depositi = append(d.Depositi, DomandaDeposito{ID: x, Nome: nome, Per: per, Serve: true})
	}
	g := "nessuno"
	if amb != nil && amb.Firewall != nil {
		g = amb.Firewall.Nome()
	}
	switch {
	case g == "firewalld" && prof.V(fmt.Sprintf("firewall.porta_%d_tcp", porta)) == "aperta" && prof.V(fmt.Sprintf("firewall.porta_%d_udp", porta)) == "aperta":
		d.Firewall = "aperto"
	case g == "firewalld":
		d.Firewall = "chiuso"
	case g == "nessuno" || g == "":
		d.Firewall = "nessuno"
	default:
		d.Firewall = "altro:" + g
	}
	if amb != nil {
		d.Persone = Persone(amb)
		gruppi := GruppiScheda(amb)
		gr, _ := LeggiGruppi(amb.P("/etc/group"))
		for _, u := range d.Persone {
			for _, g := range gruppi {
				if !contiene(DividiMembri(gr[g][1]), u) {
					d.SenzaScheda = append(d.SenzaScheda, u)
					break
				}
			}
		}
	}
	if d.Persone == nil {
		d.Persone = []string{}
	}
	return d
}

// VociDiserie: le risposte che un'interfaccia propone prima che si tocchi niente (i valori
// predefiniti di §10: gli aggiornamenti sì, il firewall aperto se serve, l'archivio
// per H.264 sì — «consigliato» —, il desktop di riferimento). Chi installa ne cambia solo alcune.
func (d *Domande) VociDiserie() map[string]string {
	v := map[string]string{"formato": FormatoRisposte, "porta": fmt.Sprint(d.Porta), "utenti": "tutti"}
	if d.Firewall == "chiuso" {
		v["consenso.firewall"] = "si"
	}
	for _, x := range d.Depositi {
		v["consenso.deposito."+x.ID] = "si"
	}
	if d.Aggiornamenti {
		v["consenso.aggiornamenti"] = "si"
	}
	if d.Desktop != nil {
		v["desktop"] = d.Desktop.Predefinita
	}
	return v
}

// TestoRisposte: le voci come un file di risposte (remotix-risposte/1), in ordine: così una scelta
// fatta nella finestra si può rifare senza domande su altre macchine.
func TestoRisposte(voci map[string]string) string {
	var k []string
	for x := range voci {
		if x != "formato" {
			k = append(k, x)
		}
	}
	sort.Strings(k)
	var b strings.Builder
	b.WriteString("formato = " + FormatoRisposte + "\n")
	for _, x := range k {
		b.WriteString(x + " = " + voci[x] + "\n")
	}
	return b.String()
}

// PianoDaScelte: il piano d'installazione dalle risposte date in un'interfaccia. Le stesse regole
// del file di risposte (OpzioniDaRisposte: che cosa serve su questa macchina, i valori ammessi),
// ma il piano NON porta il riferimento a un file né un'approvazione: il consenso lo dà chi guarda il
// piano, con un solo «conferma». Così la stessa installazione guidata dalla CLI (le opzioni), dalla
// TUI o dalla GUI dà lo stesso piano (R36). Un consenso che manca è un errore dell'interfaccia.
func PianoDaScelte(voci map[string]string, prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, o OpzioniInstallazione) (*Piano, error) {
	for k, v := range voci {
		if !vociNote[k] {
			return nil, Errore("RX-RISPOSTE-002", "voce sconosciuta «"+k+"»")
		}
		if strings.HasPrefix(k, "consenso.") {
			sn, ok := rispostaSiNo(v)
			if !ok {
				return nil, Errore("RX-RISPOSTE-003", k+" = «"+v+"»")
			}
			voci[k] = sn
		}
	}
	r := &FileRisposte{Percorso: "(interfaccia)", Voci: voci}
	o, rif, desktop, err := r.OpzioniDaRisposte(rap, prof, amb, o)
	if err != nil {
		return nil, err
	}
	if len(rif.Mancanti) > 0 {
		return nil, Errore("RX-RISPOSTE-001", strings.Join(rif.Mancanti, ", "))
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
	return p, nil
}
