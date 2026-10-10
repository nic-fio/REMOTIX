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
	Elementi []string `json:"elements"` // vincolanti, ordinati, uno per riga nel testo canonico
	Digest   string   `json:"digest"`   // sha256 del testo canonico
	Annotata []string `json:"recorded"`
}

// chiavi del profilo che entrano nell'impronta vincolante (prefissi). ⚠ Non i pacchetti in
// generale: solo quelli che il piano tocca o da cui dipende (Piano.Dipende).
var prefissiVincolanti = []string{
	"distro.id", "distro.version", "distro.variant", "system.arch", "system.systemd",
	"desktop.", "gpu.", "h264.", "selinux", "firewall.",
	"group.video", "group.render", "repo.",
}

var prefissiAnnotati = []string{"system.name", "system.kernel", "distro.name"}

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
		im.Elementi = append(im.Elementi, "package."+d+"="+p.V("package."+d))
	}
	im.Elementi = append(im.Elementi, "engine="+VersioneMotore, "catalog="+cat.Versione)
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

// Approvazione: il «sì» di chi installa, alla domanda di `install` o nella TUI (DECISIONI §10.36:
// niente file di risposte). Vale solo per il piano col digest scritto qui.
type Approvazione struct {
	Da          string `json:"from"`
	Ora         string `json:"time"`
	Modo        string `json:"mode"`
	DigestPiano string `json:"digest_plan"`
}

// Piano: il terzo oggetto (§6.6.1). `install` lo costruisce, lo mostra coi pacchetti esatti, chiede
// e lo applica; resta nella cartella dell'operazione come documento di quel che è stato fatto.
type Piano struct {
	Formato     string        `json:"format"`
	Oggetto     string        `json:"object"` // "plan"
	ID          string        `json:"id"`
	Creato      string        `json:"created"`
	Mestiere    string        `json:"kind"` // "engine-test" in T4; poi installazione, aggiornamento, disinstallazione
	Motore      RifMotore     `json:"engine"`
	Catalogo    RifCatalogo   `json:"catalog"`
	Piattaforma string        `json:"platform"`
	Impronta    Impronta      `json:"fingerprint"`
	Dipende     []string      `json:"depends"` // pacchetti da cui il piano dipende (nell'impronta)
	Azioni      []AzionePiano `json:"actions"`
	Consensi    []string      `json:"consents"`   // le domande con una riga loro (IRREVERSIBILE)
	Condizioni  []Condizione  `json:"conditions"` // quelle del rapporto che valgono per i desktop installati
	// NonFatto: quel che il piano dichiara di non fare, e perché. Un messaggio BLOCCANTE (quel che
	// manca, RX-MANCA-*: §10.36) ferma l'operazione prima di toccare niente
	NonFatto []Messaggio `json:"not_done"`
	// Dichiarate: quel che il piano fa SENZA chiedere, detto prima (l'iscrizione ai gruppi della scheda)
	Dichiarate []string `json:"declared,omitempty"`
	// Pacchetti: che cosa farebbe il gestore (la sua simulazione, fatta al momento del piano): il piano
	// li mostra prima della domanda. Al momento di fare il gestore simula di nuovo (Fotografa)
	Pacchetti []Artefatto `json:"packages,omitempty"`
	// Dipendenze: i pacchetti della distribuzione che REMOTIX chiede per il desktop della macchina
	// (labwc, wlr-randr, un carattere), e per quale desktop: il piano li mostra come tali
	Dipendenze   []Dipendenza  `json:"dependencies,omitempty"`
	Approvazione *Approvazione `json:"approval,omitempty"`
	// Purge: disinstallazione --purge (anche la configurazione, e la storia del motore)
	Purge bool `json:"purge,omitempty"`
}

// Digest del piano senza l'approvazione: è quel che l'approvazione firma.
func (p *Piano) Digest() string {
	c := *p
	c.Approvazione = nil
	return Sha256(JSONCanonico(c))
}

func nuovoID() string {
	b := make([]byte, 4)
	rand.Read(b)
	return time.Now().UTC().Format("20060102T150405Z") + "-" + hex.EncodeToString(b)
}

// OpzioniPianoProva: il piano di prova di T4 (nessun pacchetto di REMOTIX: quelli sono delle
// linee B, C, D).
type OpzioniPianoProva struct {
	Utente    string // chi mettere in «video»; vuoto ⇒ il passo non c'è
	Pacchetti string // pacchetti degli archivi della macchina da far installare (prova del gestore)
	Porta     int
}

// PianoDiProva costruisce il piano con le quattro azioni di prova.
func PianoDiProva(prof *Profilo, rap *Rapporto, cat *Catalogo, amb *Ambiente, o OpzioniPianoProva) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := fmt.Sprint(o.Porta)
	pn := &Piano{Formato: Formato, Oggetto: "plan", ID: nuovoID(), Creato: ora(), Mestiere: "engine-test",
		Motore:   RifMotore{VersioneMotore, DigestMotore()},
		Catalogo: RifCatalogo{cat.Versione, cat.Digest}, Piattaforma: rap.Piattaforma,
		Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}}
	if o.Pacchetti != "" {
		pn.Azioni = append(pn.Azioni, PianoPacchetti("packages", "", o.Pacchetti))
	}
	pn.Azioni = append(pn.Azioni,
		PianoScriviFile("conf-file", "/etc/remotix/engine-test.conf",
			"# REMOTIX — installation engine test file (phase 17, T4). It can be removed.\nporta="+ps+"\n", "0644"),
		PianoScriviFile("unit-file", "/etc/systemd/system/remotix-engine-test.service",
			"# REMOTIX — installation engine test unit (phase 17, T4): it does nothing.\n[Unit]\nDescription=REMOTIX, installation engine test\n\n[Service]\nType=oneshot\nExecStart=/bin/true\n\n[Install]\nWantedBy=multi-user.target\n", "0644"),
		PianoUnita("unit", "remotix-engine-test.service"),
	)
	// il gruppo per ultimo: con un utente che non esiste il passo fallisce DOPO tutti gli altri, e
	// l'operazione si annulla per intero (R28 dal vero)
	if o.Utente != "" {
		pn.Azioni = append(pn.Azioni, PianoGruppo("group-video", o.Utente, "video"))
	} else {
		pn.NonFatto = append(pn.NonFatto, Messaggio{Gravita: INFO, Testo: T("np.utente")})
	}
	for _, e := range rap.Desktop {
		if e.Livello != NON_SUPPORTATA && e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown" {
			pn.Condizioni = append(pn.Condizioni, e.Condizioni...)
		}
	}
	c := &Contesto{Amb: amb}
	im, err := CalcolaImpronta(prof, cat, pn.Azioni, pn.Dipende, c)
	if err != nil {
		return nil, err
	}
	pn.Impronta = *im
	return pn, nil
}
