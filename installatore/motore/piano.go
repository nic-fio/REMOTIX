package engine

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
	"time"
)

// Fingerprint of the machine (§6.6.5): the binding part decides whether the plan still holds; the
// annotated one is only recorded.
type Fingerprint struct {
	Elements  []string `json:"elements"` // binding, sorted, one per line in the canonical text
	Digest    string   `json:"digest"`   // sha256 of the canonical text
	Annotated []string `json:"recorded"`
}

// profile keys that enter the binding fingerprint (prefixes). ⚠ Not the packages in
// general: only those the plan touches or depends on (Piano.Depends).
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

// ComputeFingerprint from the profile, the catalogue and the actions (the files, groups, units, rules
// the plan touches, with their state now).
func ComputeFingerprint(p *ProfileV, cat *Catalog, actions []PlanAction, depends []string, c *Context) (*Fingerprint, error) {
	im := &Fingerprint{}
	for _, f := range p.Facts {
		v := f.KeyId + "=" + f.Val + " [" + string(f.State) + "]"
		switch {
		case hasPrefix(f.KeyId, bindingPrefixes):
			im.Elements = append(im.Elements, v)
		case hasPrefix(f.KeyId, annotatedPrefixes):
			im.Annotated = append(im.Annotated, v)
		}
	}
	for _, d := range depends {
		im.Elements = append(im.Elements, "package."+d+"="+p.V("package."+d))
	}
	im.Elements = append(im.Elements, "engine="+EngineVersion, "catalog="+cat.Ver)
	for _, ap := range actions {
		az, err := NewAction(ap)
		if err != nil {
			return nil, err
		}
		cc := *c
		cc.P = ap
		v, err := az.Constraints(&cc)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", ap.ID, err)
		}
		im.Elements = append(im.Elements, v...)
	}
	sort.Strings(im.Elements)
	sort.Strings(im.Annotated)
	im.Digest = Sha256([]byte(strings.Join(im.Elements, "\n") + "\n"))
	return im, nil
}

// FingerprintDifferences: what has changed (to say it, not only to refuse — R31).
func FingerprintDifferences(before, after []string) (removed, added []string) {
	a, b := map[string]bool{}, map[string]bool{}
	for _, x := range before {
		a[x] = true
	}
	for _, x := range after {
		b[x] = true
	}
	for _, x := range before {
		if !b[x] {
			removed = append(removed, x)
		}
	}
	for _, x := range after {
		if !a[x] {
			added = append(added, x)
		}
	}
	return
}

// Approvazione: the «yes» of whoever installs, to the question of `install` or in the TUI (DECISIONI §10.36:
// no answers file). It holds only for the plan with the digest written here.
type Approval struct {
	Da          string `json:"from"`
	At          string `json:"time"`
	Modo        string `json:"mode"`
	DigestPiano string `json:"digest_plan"`
}

// Piano: the third object (§6.6.1). `install` builds it, shows it with the exact packages, asks
// and applies it; it stays in the operation's folder as a record of what was done.
type Piano struct {
	Schema      string       `json:"format"`
	Obj         string       `json:"object"` // "plan"
	ID          string       `json:"id"`
	Made        string       `json:"created"`
	Duty        string       `json:"kind"` // "engine-test" in T4; then installation, upgrade, uninstallation
	Engine      EngineRef    `json:"engine"`
	Catalog     CatalogRef   `json:"catalog"`
	PlatformV   string       `json:"platform"`
	Fingerprint Fingerprint  `json:"fingerprint"`
	Depends     []string     `json:"depends"` // packages the plan depends on (in the fingerprint)
	Azioni      []PlanAction `json:"actions"`
	Consents    []string     `json:"consents"`   // the questions with a line of their own (IRREVERSIBLE)
	Condizioni  []Condition  `json:"conditions"` // those of the report that apply to the installed desktops
	// NotDone: what the plan declares it does not do, and why. A BLOCKING message (what is
	// missing, RX-MANCA-*: §10.36) stops the operation before touching anything
	NotDone []Message `json:"not_done"`
	// Declared: what the plan does WITHOUT asking, stated beforehand (enrolment in the card's groups)
	Declared []string `json:"declared,omitempty"`
	// Pacchetti: what the manager would do (its simulation, made at planning time): the plan
	// shows them before the question. When doing it, the manager simulates again (Snapshot)
	Pacchetti []Artifact `json:"packages,omitempty"`
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

func newID() string {
	b := make([]byte, 4)
	rand.Read(b)
	return time.Now().UTC().Format("20060102T150405Z") + "-" + hex.EncodeToString(b)
}

// TestPlanOptions: the trial plan of T4 (no REMOTIX packages: those belong to
// lines B, C, D).
type TestPlanOptions struct {
	User      string // whom to put in «video»; empty ⇒ the step is not there
	Pacchetti string // packages from the machine's repositories to have installed (test of the manager)
	Porta     int
}

// TestPlan builds the plan with the four trial actions.
func TestPlan(prof *ProfileV, rap *Report, cat *Catalog, env *Environment, o TestPlanOptions) (*Piano, error) {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	ps := fmt.Sprint(o.Porta)
	pn := &Piano{Schema: Schema, Obj: "plan", ID: newID(), Made: now(), Duty: "engine-test",
		Engine:  EngineRef{EngineVersion, EngineDigest()},
		Catalog: CatalogRef{cat.Ver, cat.Digest}, PlatformV: rap.PlatformV,
		Depends: []string{}, Consents: []string{}, Condizioni: []Condition{}, NotDone: []Message{}}
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
	if o.User != "" {
		pn.Azioni = append(pn.Azioni, PlanGroup("group-video", o.User, "video"))
	} else {
		pn.NotDone = append(pn.NotDone, Message{Severity: INFO, Testo: T("np.utente")})
	}
	for _, e := range rap.Desktop {
		if e.Lvl != NOT_SUPPORTED && e.Installed != "" && e.Installed != "absent" && e.Installed != "unknown" {
			pn.Condizioni = append(pn.Condizioni, e.Condizioni...)
		}
	}
	c := &Context{Env: env}
	im, err := ComputeFingerprint(prof, cat, pn.Azioni, pn.Depends, c)
	if err != nil {
		return nil, err
	}
	pn.Fingerprint = *im
	return pn, nil
}
