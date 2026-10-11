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
	Elements []string `json:"elements"` // binding, sorted, one per line in the canonical text
	Digest   string   `json:"digest"`   // sha256 of the canonical text
	Annotata []string `json:"recorded"`
}

// profile keys that enter the binding fingerprint (prefixes). ⚠ Not the packages in
// general: only those the plan touches or depends on (Piano.Dipende).
var bindingPrefixes = []string{
	"distro.id", "distro.version", "distro.variant", "system.arch", "system.systemd",
	"desktop.", "gpu.", "h264.", "selinux", "firewall.",
	"group.video", "group.render", "repo.",
}

var annotatedPrefixes = []string{"system.name", "system.kernel", "distro.name"}

func hasPrefix(k string, pp []string) bool {
	for _, p := range pp {
		if strings.HasPrefix(k, p) {
			return true
		}
	}
	return false
}

// CalcolaImpronta from the profile, the catalogue and the actions (the files, groups, units, rules
// the plan touches, with their state now).
func CalcolaImpronta(p *ProfileV, cat *Catalogo, azioni []AzionePiano, dipende []string, c *Contesto) (*Impronta, error) {
	im := &Impronta{}
	for _, f := range p.Fatti {
		v := f.KeyId + "=" + f.Val + " [" + string(f.Stato) + "]"
		switch {
		case hasPrefix(f.KeyId, bindingPrefixes):
			im.Elements = append(im.Elements, v)
		case hasPrefix(f.KeyId, annotatedPrefixes):
			im.Annotata = append(im.Annotata, v)
		}
	}
	for _, d := range dipende {
		im.Elements = append(im.Elements, "package."+d+"="+p.V("package."+d))
	}
	im.Elements = append(im.Elements, "engine="+VersioneMotore, "catalog="+cat.Ver)
	for _, ap := range azioni {
		az, err := NewAction(ap)
		if err != nil {
			return nil, err
		}
		cc := *c
		cc.P = ap
		v, err := az.Vincoli(&cc)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", ap.ID, err)
		}
		im.Elements = append(im.Elements, v...)
	}
	sort.Strings(im.Elements)
	sort.Strings(im.Annotata)
	im.Digest = Sha256([]byte(strings.Join(im.Elements, "\n") + "\n"))
	return im, nil
}

// FingerprintDifferences: what has changed (to say it, not only to refuse — R31).
func FingerprintDifferences(prima, dopo []string) (tolti, aggiunti []string) {
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
type Approval struct {
	Da          string `json:"from"`
	Ora         string `json:"time"`
	Modo        string `json:"mode"`
	DigestPiano string `json:"digest_plan"`
}

// Piano: the third object (§6.6.1). `install` builds it, shows it with the exact packages, asks
// and applies it; it stays in the operation's folder as a record of what was done.
type Piano struct {
	Formato    string        `json:"format"`
	Obj        string        `json:"object"` // "plan"
	ID         string        `json:"id"`
	Made       string        `json:"created"`
	Duty       string        `json:"kind"` // "engine-test" in T4; then installation, upgrade, uninstallation
	Motore     EngineRef     `json:"engine"`
	Catalogo   CatalogRef    `json:"catalog"`
	PlatformV  string        `json:"platform"`
	Impronta   Impronta      `json:"fingerprint"`
	Dipende    []string      `json:"depends"` // packages the plan depends on (in the fingerprint)
	Azioni     []AzionePiano `json:"actions"`
	Consents   []string      `json:"consents"`   // the questions with a line of their own (IRREVERSIBLE)
	Condizioni []Condizione  `json:"conditions"` // those of the report that apply to the installed desktops
	// NotDone: what the plan declares it does not do, and why. A BLOCKING message (what is
	// missing, RX-MANCA-*: §10.36) stops the operation before touching anything
	NotDone []Messaggio `json:"not_done"`
	// Dichiarate: what the plan does WITHOUT asking, stated beforehand (enrolment in the card's groups)
	Dichiarate []string `json:"declared,omitempty"`
	// Pacchetti: what the manager would do (its simulation, made at planning time): the plan
	// shows them before the question. When doing it, the manager simulates again (Fotografa)
	Pacchetti []Artefatto `json:"packages,omitempty"`
	// Dipendenze: the distribution packages REMOTIX requires for the machine's desktop
	// (labwc, wlr-randr, a font), and for which desktop: the plan shows them as such
	Dipendenze []Dependency `json:"dependencies,omitempty"`
	Approval   *Approval    `json:"approval,omitempty"`
	// Purge: uninstallation --purge (the configuration too, and the engine's history)
	Purge bool `json:"purge,omitempty"`
}

// Digest of the plan without the approval: it is what the approval signs.
func (p *Piano) Digest() string {
	c := *p
	c.Approval = nil
	return Sha256(CanonicalJSON(c))
}

func nuovoID() string {
	b := make([]byte, 4)
	rand.Read(b)
	return time.Now().UTC().Format("20060102T150405Z") + "-" + hex.EncodeToString(b)
}

// TestPlanOptions: the trial plan of T4 (no REMOTIX packages: those belong to
// lines B, C, D).
type TestPlanOptions struct {
	Utente    string // whom to put in «video»; empty ⇒ the step is not there
	Pacchetti string // packages from the machine's repositories to have installed (test of the manager)
	Porta     int
}

// TestPlan builds the plan with the four trial actions.
func TestPlan(prof *ProfileV, rap *Rapporto, cat *Catalogo, amb *Ambiente, o TestPlanOptions) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := fmt.Sprint(o.Porta)
	pn := &Piano{Formato: Formato, Obj: "plan", ID: nuovoID(), Made: ora(), Duty: "engine-test",
		Motore:   EngineRef{VersioneMotore, EngineDigest()},
		Catalogo: CatalogRef{cat.Ver, cat.Digest}, PlatformV: rap.PlatformV,
		Dipende: []string{}, Consents: []string{}, Condizioni: []Condizione{}, NotDone: []Messaggio{}}
	if o.Pacchetti != "" {
		pn.Azioni = append(pn.Azioni, PlanPackages("packages", "", o.Pacchetti))
	}
	pn.Azioni = append(pn.Azioni,
		PlanWriteFile("conf-file", "/etc/remotix/engine-test.conf",
			"# REMOTIX — installation engine test file (phase 17, T4). It can be removed.\nporta="+ps+"\n", "0644"),
		PlanWriteFile("unit-file", "/etc/systemd/system/remotix-engine-test.service",
			"# REMOTIX — installation engine test unit (phase 17, T4): it does nothing.\n[Unit]\nDescription=REMOTIX, installation engine test\n\n[Service]\nType=oneshot\nExecStart=/bin/true\n\n[Install]\nWantedBy=multi-user.target\n", "0644"),
		PlanUnit("unit", "remotix-engine-test.service"),
	)
	// the group last: with a user that does not exist the step fails AFTER all the others, and
	// the operation is cancelled entirely (R28 for real)
	if o.Utente != "" {
		pn.Azioni = append(pn.Azioni, PlanGroup("group-video", o.Utente, "video"))
	} else {
		pn.NotDone = append(pn.NotDone, Messaggio{Gravita: INFO, Testo: T("np.utente")})
	}
	for _, e := range rap.Desktop {
		if e.Lvl != NON_SUPPORTATA && e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown" {
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
