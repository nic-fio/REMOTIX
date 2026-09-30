package motore

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
	"time"
)

// Impronta della macchina (§6.6.5): la parte vincolante decide se il piano vale ancora; quella
// annotata si registra e basta.
type Impronta struct {
	Elementi []string `json:"elementi"` // vincolanti, ordinati, uno per riga nel testo canonico
	Digest   string   `json:"digest"`   // sha256 del testo canonico
	Annotata []string `json:"annotata"`
}

// chiavi del profilo che entrano nell'impronta vincolante (prefissi). ⚠ Non i pacchetti in
// generale: solo quelli che il piano tocca o da cui dipende (Piano.Dipende).
var prefissiVincolanti = []string{
	"distro.id", "distro.versione", "distro.variante", "sistema.architettura", "sistema.systemd",
	"desktop.", "scheda.", "h264.", "selinux", "firewall.",
	"gruppo.video", "gruppo.render", "deposito.",
}

var prefissiAnnotati = []string{"sistema.nome", "sistema.kernel", "distro.nome"}

func haPrefisso(k string, pp []string) bool {
	for _, p := range pp {
		if strings.HasPrefix(k, p) {
			return true
		}
	}
	return false
}

// CalcolaImpronta dal profilo, dal catalogo e dalle azioni (i file, i gruppi, le unità, le regole
// che il piano tocca, con il loro stato adesso).
func CalcolaImpronta(p *Profilo, cat *Catalogo, azioni []AzionePiano, dipende []string, c *Contesto) (*Impronta, error) {
	im := &Impronta{}
	for _, f := range p.Fatti {
		v := f.Chiave + "=" + f.Valore + " [" + string(f.Stato) + "]"
		switch {
		case haPrefisso(f.Chiave, prefissiVincolanti):
			im.Elementi = append(im.Elementi, v)
		case haPrefisso(f.Chiave, prefissiAnnotati):
			im.Annotata = append(im.Annotata, v)
		}
	}
	for _, d := range dipende {
		im.Elementi = append(im.Elementi, "pacchetto."+d+"="+p.V("pacchetto."+d))
	}
	im.Elementi = append(im.Elementi, "motore="+VersioneMotore, "catalogo="+cat.Versione)
	for _, ap := range azioni {
		az, err := NuovaAzione(ap)
		if err != nil {
			return nil, err
		}
		cc := *c
		cc.P = ap
		v, err := az.Vincoli(&cc)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", ap.ID, err)
		}
		im.Elementi = append(im.Elementi, v...)
	}
	sort.Strings(im.Elementi)
	sort.Strings(im.Annotata)
	im.Digest = Sha256([]byte(strings.Join(im.Elementi, "\n") + "\n"))
	return im, nil
}

// DifferenzeImpronta: che cosa è cambiato (per dirlo, non solo per rifiutare — R31).
func DifferenzeImpronta(prima, dopo []string) (tolti, aggiunti []string) {
	a, b := map[string]bool{}, map[string]bool{}
	for _, x := range prima {
		a[x] = true
	}
	for _, x := range dopo {
		b[x] = true
	}
	for _, x := range prima {
		if !b[x] {
			tolti = append(tolti, x)
		}
	}
	for _, x := range dopo {
		if !a[x] {
			aggiunti = append(aggiunti, x)
		}
	}
	return
}

// Approvazione: il consenso, dato a mano o da file (§6.6.12). Vale solo per il piano col digest
// scritto qui.
type Approvazione struct {
	Da          string `json:"da"`
	Ora         string `json:"ora"`
	Modo        string `json:"modo"`
	DigestPiano string `json:"digest_piano"`
}

// Piano: il terzo oggetto (§6.6.1). Un documento: si salva, si legge, si approva, si applica.
type Piano struct {
	Formato      string        `json:"formato"`
	Oggetto      string        `json:"oggetto"` // "piano"
	ID           string        `json:"id"`
	Creato       string        `json:"creato"`
	Mestiere     string        `json:"mestiere"` // "prova-motore" in T4; poi installazione, aggiornamento, disinstallazione
	Motore       RifMotore     `json:"motore"`
	Catalogo     RifCatalogo   `json:"catalogo"`
	Piattaforma  string        `json:"piattaforma"`
	Impronta     Impronta      `json:"impronta"`
	Dipende      []string      `json:"dipende"` // pacchetti da cui il piano dipende (nell'impronta)
	Azioni       []AzionePiano `json:"azioni"`
	Consensi     []string      `json:"consensi"`   // le domande con una riga loro (D5, D6, IRREVERSIBILE)
	Scelte       []Scelta      `json:"scelte"`     // le domande con una risposta (il desktop, se manca)
	Condizioni   []Condizione  `json:"condizioni"` // quelle del rapporto che valgono per i desktop installati
	NonFatto     []Messaggio   `json:"non_fatto"`  // quel che il piano dichiara di non fare, e perché
	Approvazione *Approvazione `json:"approvazione,omitempty"`
	// Purge: disinstallazione --purge (anche la configurazione, e la storia del motore)
	Purge bool `json:"purge,omitempty"`
	// Archivio: l'archivio firmato di REMOTIX da cui si installa e si aggiorna (T8); la fase 0
	// TRUST ci scarica il catalogo del canale.
	Archivio *RifArchivio `json:"archivio,omitempty"`
	// Risposte: il piano viene da un file di risposte (senza domande, §6.6.12): il file, le voci, e i
	// consensi che mancano (se ce n'è uno, l'operazione è BLOCCATA: RX-RISPOSTE-001)
	Risposte *RifRisposte `json:"risposte,omitempty"`
}

// RifArchivio: l'archivio di REMOTIX (URL di base) e il canale (stabile, candidato).
type RifArchivio struct {
	URL    string `json:"url"`
	Canale string `json:"canale"`
}

// Digest del piano senza l'approvazione: è quel che l'approvazione firma.
func (p *Piano) Digest() string {
	c := *p
	c.Approvazione = nil
	return Sha256(JSONCanonico(c))
}

// Scelta: una domanda del consenso con una risposta fra opzioni date dal catalogo. Oggi una sola:
// quale desktop installare quando non ce n'è uno supportato (§10, DECISIONI §10.7).
type Scelta struct {
	ID          string   `json:"id"`
	Domanda     string   `json:"domanda"`
	Opzioni     []string `json:"opzioni"`
	Predefinita string   `json:"predefinita"` // vale se nessuno risponde (senza domande: §6.6.12)
	Risposta    string   `json:"risposta"`
	// Pacchetti: per ogni opzione, i pacchetti che la installano (dal catalogo)
	Pacchetti map[string]string `json:"pacchetti,omitempty"`
	// Componenti: per ogni opzione, i pezzi che quel desktop chiede a REMOTIX (labwc, wlr-randr,
	// breeze6-wallpapers, il carattere scalabile…): entrano nel piano insieme al desktop
	Componenti map[string]string `json:"componenti,omitempty"`
}

// Valore: la risposta data, o la predefinita.
func (s Scelta) Valore() string { return nonVuoto(s.Risposta, s.Predefinita) }

// Rispondi dà la risposta a una scelta e aggiorna il passo che ne dipende. Il digest del piano
// cambia: un'approvazione data prima non vale più.
func (p *Piano) Rispondi(id, risposta string) error {
	for i := range p.Scelte {
		s := &p.Scelte[i]
		if s.ID != id {
			continue
		}
		ok := false
		for _, o := range s.Opzioni {
			ok = ok || o == risposta
		}
		if !ok {
			return fmt.Errorf("%s: %q non è fra le opzioni %v", id, risposta, s.Opzioni)
		}
		s.Risposta = risposta
		if id == "desktop" {
			p.metteDesktop(risposta, s.Pacchetti[risposta], s.Componenti[risposta])
		}
		return nil
	}
	return fmt.Errorf("il piano non ha la scelta %q", id)
}

// metteDesktop: il passo «installa-desktop» c'è se la risposta è un desktop, non c'è se è «no».
func (p *Piano) metteDesktop(d, nomi, componenti string) {
	var az []AzionePiano
	dopoDepositi := 0
	for _, a := range p.Azioni {
		if a.Tipo != "installa-desktop" && a.ID != "componenti-desktop" {
			az = append(az, a)
			if a.Tipo == "aggiungi-deposito" {
				dopoDepositi = len(az)
			}
		}
	}
	if d != "no" {
		nuovi := []AzionePiano{PianoDesktop("desktop", d, nomi)}
		if componenti != "" {
			nuovi = append(nuovi, PianoPacchetti("componenti-desktop", "", "", componenti))
		}
		az = append(az[:dopoDepositi], append(nuovi, az[dopoDepositi:]...)...)
	}
	p.Azioni = az
}

func nuovoID() string {
	b := make([]byte, 4)
	rand.Read(b)
	return time.Now().UTC().Format("20060102T150405Z") + "-" + hex.EncodeToString(b)
}

// OpzioniPianoProva: il piano di prova di T4 (nessun pacchetto di REMOTIX: quelli sono delle
// linee B, C, D).
type OpzioniPianoProva struct {
	Utente       string   // chi mettere in «video»; vuoto ⇒ il passo non c'è
	ApriFirewall bool     // D6 aperta: il passo del firewall solo se chiesto
	Depositi     []string // archivi di terzi da aggiungere (prova dei depositi, D5)
	Pacchetti    string   // pacchetti dai depositi da far installare (prova del gestore)
	Porta        int
}

// PianoDiProva costruisce il piano con le quattro azioni di prova.
func PianoDiProva(prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, o OpzioniPianoProva) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := fmt.Sprint(o.Porta)
	pn := &Piano{Formato: Formato, Oggetto: "piano", ID: nuovoID(), Creato: ora(), Mestiere: "prova-motore",
		Motore:   RifMotore{VersioneMotore, DigestMotore()},
		Catalogo: RifCatalogo{cat.Versione, cat.Digest, cat.Scadenza}, Piattaforma: rap.Piattaforma,
		Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}}
	for _, d := range o.Depositi {
		cons := T("consenso.deposito", nonVuoto(cat.Depositi[d].Nome, d))
		pn.Azioni = append(pn.Azioni, PianoDeposito("deposito-"+d, d, nil, cons))
		pn.Consensi = append(pn.Consensi, cons)
	}
	if o.Pacchetti != "" {
		pn.Azioni = append(pn.Azioni, PianoPacchetti("pacchetti", "", "", o.Pacchetti))
	}
	pn.Azioni = append(pn.Azioni,
		PianoScriviFile("file-conf", "/etc/remotix/prova-motore.conf",
			"# REMOTIX — file di prova del motore d'installazione (fase 17, T4). Si può togliere.\nporta="+ps+"\n", "0644"),
		PianoScriviFile("file-unita", "/etc/systemd/system/remotix-prova-motore.service",
			"# REMOTIX — unità di prova del motore d'installazione (fase 17, T4): non fa niente.\n[Unit]\nDescription=REMOTIX, prova del motore d'installazione\n\n[Service]\nType=oneshot\nExecStart=/bin/true\n\n[Install]\nWantedBy=multi-user.target\n", "0644"),
		PianoUnita("unita", "remotix-prova-motore.service"),
	)
	switch g := amb.Firewall.Nome(); {
	case !o.ApriFirewall:
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.firewall_no", ps)})
	case g == "firewalld" || g == "ufw":
		a := PianoFirewall("firewall", ps)
		pn.Azioni = append(pn.Azioni, a)
		pn.Consensi = append(pn.Consensi, a.Consenso)
	case g == "nessuno":
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.firewall_nessuno")})
	default:
		pn.NonFatto = append(pn.NonFatto, Msg("RX-FW-004", T("np.firewall_mano", g, ps)))
	}
	// il gruppo per ultimo: con un utente che non esiste il passo fallisce DOPO tutti gli altri, e
	// l'operazione si annulla per intero (R28 dal vero)
	if o.Utente != "" {
		pn.Azioni = append(pn.Azioni, PianoGruppo("gruppo-video", o.Utente, "video"))
	} else {
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.utente")})
	}
	for _, e := range rap.Desktop {
		if e.Livello != NON_SUPPORTATA && e.Installato != "" && e.Installato != "assente" && e.Installato != "sconosciuto" {
			pn.Condizioni = append(pn.Condizioni, e.Condizioni...)
		}
	}
	pn.Scelte = []Scelta{}
	// Il piano di PROVA non installa REMOTIX: la domanda sul desktop (DECISIONI §10.7) non la fa,
	// la dichiara. I piani veri la fanno con SceltaDesktop (provata in TestSenzaDesktop).
	if s := SceltaDesktop(rap); s != nil {
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Codice: "RX-DESKTOP-002",
			Testo: T("np.desktop", strings.Join(s.Opzioni, ", "), s.Predefinita)})
	}
	c := &Contesto{Amb: amb}
	im, err := CalcolaImpronta(prof, cat, pn.Azioni, pn.Dipende, c)
	if err != nil {
		return nil, err
	}
	pn.Impronta = *im
	return pn, nil
}

// SceltaDesktop: la domanda in più quando non c'è un desktop supportato — i soli desktop che il
// catalogo dà per buoni su questa distribuzione, quello di riferimento già selezionato, e «no».
func SceltaDesktop(rap *Rapporto) *Scelta {
	if !rap.SenzaDesktop {
		return nil
	}
	s := &Scelta{ID: "desktop", Domanda: T("scelta.desktop"), Pacchetti: map[string]string{}, Componenti: map[string]string{}}
	for _, e := range rap.Desktop {
		if e.Livello == NON_SUPPORTATA {
			continue
		}
		if rap.pl != nil {
			s.Pacchetti[e.Desktop] = rap.pl.PacchettiDesktop[e.Desktop]
			dc := rap.pl.Desktop[e.Desktop]
			comp := append([]string{}, dc.Componenti...)
			if dc.ServeCarattere && rap.cat != nil {
				if car := rap.cat.CarattereScalabile[rap.pl.Famiglia]; car != "" {
					comp = append(comp, car)
				}
			}
			s.Componenti[e.Desktop] = strings.Join(comp, ",")
		}
		s.Opzioni = append(s.Opzioni, e.Desktop)
		if e.Riferimento || s.Predefinita == "" {
			s.Predefinita = e.Desktop
		}
	}
	if len(s.Opzioni) == 0 {
		return nil // niente da proporre: la distribuzione stessa è NON_SUPPORTATA
	}
	s.Opzioni = append(s.Opzioni, "no")
	return s
}
