package motore

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
	"time"
)

// Impronta of the machine (§6.6.5): the binding part decides whether the plan still holds; the
// annotated one is only recorded.
type Impronta struct {
	Elementi []string `json:"elements"` // binding, sorted, one per line in the canonical text
	Digest   string   `json:"digest"`   // sha256 of the canonical text
	Annotata []string `json:"recorded"`
}

// profile keys that enter the binding fingerprint (prefixes). ⚠ Not the packages in
// general: only those the plan touches or depends on (Piano.Dipende).
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

// CalcolaImpronta from the profile, the catalogue and the actions (the files, groups, units, rules
// the plan touches, with their state now).
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

// DifferenzeImpronta: what has changed (to say it, not only to refuse — R31).
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

// Approvazione: the «yes» of whoever installs, to the question of `install` or in the TUI (DECISIONI §10.36:
// no answers file). It holds only for the plan with the digest written here.
type Approvazione struct {
	Da          string `json:"from"`
	Ora         string `json:"time"`
	Modo        string `json:"mode"`
	DigestPiano string `json:"digest_plan"`
}

// Piano: the third object (§6.6.1). `install` builds it, shows it with the exact packages, asks
// and applies it; it stays in the operation's folder as a record of what was done.
type Piano struct {
	Formato     string        `json:"format"`
	Oggetto     string        `json:"object"` // "plan"
	ID          string        `json:"id"`
	Creato      string        `json:"created"`
	Mestiere    string        `json:"kind"` // "engine-test" in T4; then installation, upgrade, uninstallation
	Motore      RifMotore     `json:"engine"`
	Catalogo    RifCatalogo   `json:"catalog"`
	Piattaforma string        `json:"platform"`
	Impronta    Impronta      `json:"fingerprint"`
	Dipende     []string      `json:"depends"` // packages the plan depends on (in the fingerprint)
	Azioni      []AzionePiano `json:"actions"`
	Consensi    []string      `json:"consents"`   // the questions with a line of their own (IRREVERSIBLE)
	Condizioni  []Condizione  `json:"conditions"` // those of the report that apply to the installed desktops
	// NonFatto: what the plan declares it does not do, and why. A BLOCKING message (what is
	// missing, RX-MANCA-*: §10.36) stops the operation before touching anything
	NonFatto []Messaggio `json:"not_done"`
	// Dichiarate: what the plan does WITHOUT asking, stated beforehand (enrolment in the card's groups)
	Dichiarate []string `json:"declared,omitempty"`
	// Pacchetti: what the manager would do (its simulation, made at planning time): the plan
	// shows them before the question. When doing it, the manager simulates again (Fotografa)
	Pacchetti []Artefatto `json:"packages,omitempty"`
	// Dipendenze: the distribution packages REMOTIX requires for the machine's desktop
	// (labwc, wlr-randr, a font), and for which desktop: the plan shows them as such
	Dipendenze   []Dipendenza  `json:"dependencies,omitempty"`
	Approvazione *Approvazione `json:"approval,omitempty"`
	// Purge: uninstallation --purge (the configuration too, and the engine's history)
	Purge bool `json:"purge,omitempty"`
}

// Digest of the plan without the approval: it is what the approval signs.
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

// OpzioniPianoProva: the trial plan of T4 (no REMOTIX packages: those belong to
// lines B, C, D).
type OpzioniPianoProva struct {
	Utente    string // whom to put in «video»; empty ⇒ the step is not there
	Pacchetti string // packages from the machine's repositories to have installed (test of the manager)
	Porta     int
}

// PianoDiProva builds the plan with the four trial actions.
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
	// the group last: with a user that does not exist the step fails AFTER all the others, and
	// the operation is cancelled entirely (R28 for real)
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
