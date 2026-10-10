package motore

import (
	"encoding/json"
	"strings"
)

// CatalogFormat is the catalogue's format version (different from the objects': the
// catalogue travels in the remotix-install package, §6.6.8).
const CatalogFormat = "remotix-catalogo/1"

// Catalog: the combinations and their rules (§3, §6.6.8).
type Catalog struct {
	Schema        string                       `json:"schema"`
	Version       string                       `json:"version_v"`
	Sequence      int                          `json:"sequence"`
	Emitted       string                       `json:"emesso"`
	EngineMinimum string                       `json:"motore_minimo"`
	Source        string                       `json:"source"`
	Requirements  CatalogRequirements          `json:"requisiti"`
	Repositories  map[string]RepositoryCatalog `json:"repositories"`
	Platforms     []Platform                   `json:"piattaforme"`
	Excluded      []Excluded                   `json:"escluse"`
	AlwaysOut     []string                     `json:"fuori_sempre"`
	MinComponents []MinComponent               `json:"componenti_minimi"`
	// ScalableFont: the font package per family, when the desktop runs under labwc
	// and the machine has none (a REMOTIX dependency, §10.36)
	ScalableFont map[string]string `json:"carattere_scalabile"`

	Digest     string `json:"-"` // sha256 of the bytes read
	Provenance string `json:"-"` // where it comes from (phase 0 TRUST): the package, the downloaded engine, given by hand
}

// MinComponent: a line of the table «minimum versions of the components» (§3.1).
type MinComponent struct {
	Component string `json:"component"`
	Minimum   string `json:"minimum"`
	Why       string `json:"reason_text"`
}

type CatalogRequirements struct {
	OpensslMinimum string `json:"openssl_minima"`
	KdeMinimum     string `json:"kde_minima"`
	GnomeMinimum   string `json:"gnome_minima"`
	XfceMinimum    string `json:"xfce_minima"`
	LxqtMinimum    string `json:"lxqt_minima"`
	Systemd        bool   `json:"systemd"`
}

// minDesktopVersion: the minimum version of a desktop.
func (r CatalogRequirements) minDesktopVersion(d string) string {
	return map[string]string{"gnome": r.GnomeMinimum, "kde": r.KdeMinimum, "xfce": r.XfceMinimum, "lxqt": r.LxqtMinimum}[d]
}

// RepositoryCatalog: a third-party repository a platform requires. The catalogue gives only its name:
// adding it is the administrator's job (DECISIONI §10.36), the engine says it is missing.
type RepositoryCatalog struct {
	Name string `json:"label_name"`
}

type Platform struct {
	ID           string       `json:"id"`
	Distrib      string       `json:"distrib"`
	Versions     []string     `json:"vers"`
	MinVersion   string       `json:"versione_minima,omitempty"`
	VersionLabel string       `json:"etichetta_versione"`
	Name         string       `json:"label_name"`
	Family       string       `json:"family"`
	Matrix       bool         `json:"matrix"`
	FullRound    string       `json:"giro_intero"` // date of the green full run (T10); "" = never
	Derived      []Derivative `json:"derivate,omitempty"`
	H264         H264Platform `json:"h264"`
	// Repositories: the repositories REMOTIX itself needs, on any desktop. Phase 19 (no
	// encoding on the processor): only EPEL on Alma remains, which RPM Fusion for EL (the Intel driver with
	// H.264) wants before itself; Cisco's OpenH264 and SVT-AV1 are gone. D5.
	Repositories []string                  `json:"repositories,omitempty"`
	Desktop      map[string]DesktopCatalog `json:"desktop"`
	Note         []string                  `json:"note,omitempty"`
}

type Derivative struct {
	ID         string   `json:"id"`
	Name       string   `json:"label_name"`
	Versions   []string `json:"vers"`
	MinVersion string   `json:"versione_minima,omitempty"`
	Note       string   `json:"remark,omitempty"`
}

// H264Platform: the platform's video encoding, WITHOUT ffmpeg (phase 18) and ONLY on the card
// (phase 19: no fallback to the processor). Since 10 Oct 2026 (DECISIONI §10.36) the engine installs no
// drivers or third-party repositories: the catalogue says only what the platform can do with its own
// packages, and the machine shows whether the driver that is there encodes (driverFamily, the 7a test).
type H264Platform struct {
	// AmdWithoutVaapi: on this platform Mesa has no VA-API (Alma/RHEL): AMD does not encode in VA-API
	AmdWithoutVaapi bool `json:"amd_senza_vaapi,omitempty"`
	// NoStockH264: the vendors whose VA-API driver, in the distribution's packages, is
	// built without H.264 (Fedora: Intel and AMD; Alma: Intel; openSUSE: AMD). It serves the manual
	// (catalog --table); the machine shows it by itself (driverFamily)
	NoStockH264 []string `json:"senza_h264_di_serie,omitempty"`
	// VulkanEncoding (phase 19, the «vulkan» route of strade.go): the vendors whose OFFICIAL Vulkan
	// driver on this platform encodes H.264/HEVC. Today only AMD (RADV), and only where Mesa is
	// built with the codecs (`[M]` 1 Oct 2026: Debian, Ubuntu, Arch). ⛔ Fedora, RHEL and openSUSE
	// build Mesa with `all_free`: there the official RADV does not encode. ⛔ Intel no: ANV encodes
	// only behind ANV_DEBUG (§10.27), it stays on VA-API. ⛔ NVIDIA no: the ICD belongs to the proprietary driver
	VulkanEncoding []string `json:"vulkan_codifica,omitempty"`
}

// encodesFor: a card vendor encodes H.264 via VA-API on this platform with the driver the
// machine HAS. driverWithout: for it there is only a driver built without H.264 (driverFamily): it does not
// encode, and the engine does not install another one (§10.36). Only Intel and AMD have the route.
func (h H264Platform) encodesFor(vendor string, driverWithout bool) bool {
	switch {
	case vendor != "Intel" && vendor != "AMD":
		return false
	case vendor == "AMD" && h.AmdWithoutVaapi:
		return false
	case driverWithout:
		return false
	}
	return true
}

// cardVendors: the vendors of the machine's cards (gpu_card.<node>.vendor); known=false if
// the profile names none (then we stay cautious: as if all were needed).
func cardVendors(p *Profile) (map[string]bool, bool) {
	r := map[string]bool{}
	for _, f := range p.Facts {
		if strings.HasPrefix(f.Key, "gpu.") && strings.HasSuffix(f.Key, ".vendor") && f.Value != "" {
			r[f.Value] = true
		}
	}
	return r, len(r) > 0
}

// MissingBaseRepositories: the repositories REMOTIX itself needs (Platform.Repositories) that are missing.
func MissingBaseRepositories(pl *Platform, p *Profile) []string {
	if pl == nil {
		return nil
	}
	var r []string
	for _, d := range pl.Repositories {
		if p.V("repo."+d) != "present" {
			r = append(r, d)
		}
	}
	return r
}

type DesktopCatalog struct {
	Supported  bool     `json:"supported"`
	Code       string   `json:"code_v,omitempty"`
	Pending    string   `json:"waiting,omitempty"` // a decision of the user still open
	Motivo     string   `json:"motivo,omitempty"`
	Components []string `json:"componenti,omitempty"`
	Limits     []string `json:"limiti,omitempty"`
	// Requires3D: the desktop does not work without the card's 3D acceleration (the why): condition
	// C-HARDWARE; without any card (no render node) NOT_SUPPORTED, RX-COMPAT-007
	Requires3D string `json:"richiede_3d,omitempty"`
	// NeedsCharacter: the desktop runs under labwc, which dies without a scalable font
	// (labwc #2525, §11.1)
	NeedsCharacter bool     `json:"serve_carattere,omitempty"`
	Note           []string `json:"note,omitempty"`
}

type Excluded struct {
	ID       string   `json:"id"`
	Versions []string `json:"vers"`
	Motivo   string   `json:"motivo"`
}

// ReadCatalog parses a catalogue and computes its digest.
func ReadCatalog(b []byte) (*Catalog, error) {
	var c Catalog
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, Error("RX-TRUST-004", err.Error())
	}
	if c.Schema != CatalogFormat {
		return nil, Error("RX-TRUST-004", "format "+c.Schema)
	}
	c.Digest = Sha256(b)
	return &c, nil
}

type CatalogRef struct {
	Version string `json:"version"`
	Digest  string `json:"digest"`
}

type EngineRef struct {
	Version string `json:"version"`
	Digest  string `json:"digest"`
}

// EngineDigest: sha256 of the running binary. ⚠ On the machine itself it does not hold against root
// (§6.6.11): it serves to say, afterwards, which engine did the operation.
func EngineDigest() string {
	d, err := Sha256File("/proc/self/exe")
	if err != nil || d == "" {
		return "unknown"
	}
	return d
}

// Condition: one of the conditions C-… of §6.6.8, with its remedy.
// Condition: one of the conditions C-… of §6.6.8: REMOTIX works, with a stated limit.
type Condition struct {
	Code string `json:"code"`
	Text string `json:"text"`
}

// Compatibility levels (§6.6.8).
const (
	CERTIFIED     = "CERTIFIED"
	COMPATIBLE    = "COMPATIBLE"
	NOT_SUPPORTED = "UNSUPPORTED"
)

// DesktopOutcome: the level for one desktop.
type DesktopOutcome struct {
	Desktop    string      `json:"desktop"`
	Name       string      `json:"name"`
	Installed  string      `json:"installed"` // version, "absent" or "unknown"
	Level      string      `json:"level"`
	Conditions []Condition `json:"conditions"`
	Reasons    []Message   `json:"reasons,omitempty"` // why NOT_SUPPORTED
	// Missing: what is missing on this machine for REMOTIX to run on this installed desktop
	// (DECISIONI §10.36: it is stated, the administrator provides it; the installation stops)
	Missing []string `json:"missing,omitempty"`
	// Depends: the distribution packages this desktop requires of REMOTIX (dependencies)
	Depends []string `json:"depends,omitempty"`
	Note    []string `json:"notes,omitempty"`
}

// Report of compatibility: the second object (§6.6.1).
type Report struct {
	Schema     string     `json:"format"`
	Object     string     `json:"object"` // "compatibility"
	Created    string     `json:"created"`
	Catalog    CatalogRef `json:"catalog"`
	Platform   string     `json:"platform"` // "Debian 13"
	pl         *Platform
	cat        *Catalog
	Recognized string           `json:"recognized"` // in the matrix · outside the matrix · derivative of … · excluded · unknown
	Desktop    []DesktopOutcome `json:"desktop"`
	NoDesktop  bool             `json:"no_desktop"` // no supported desktop installed
	// Missing: everything this machine is missing, BLOCKING (DECISIONI §10.36): REMOTIX does not
	// install anything of the system, it says so. Empty = it can be installed
	Missing []Message `json:"missing"`
	// Dependencies: the pieces the machine's desktop requires of REMOTIX (labwc, wlr-randr, a scalable
	// font): normal dependencies, the engine adds them to the packages to install and the manager
	// takes them from the distribution's repositories (the user, 10 Oct 2026, §10.36)
	Dependencies []Dependency `json:"dependencies"`
	Unknowns     []string     `json:"unknowns,omitempty"` // UNKNOWN facts that affect the judgement
	Messages     []Message    `json:"messages"`
	Note         []string     `json:"notes,omitempty"`
	// Lowest: for an excluded version, the first version of the same distribution that the
	// catalogue supports («at least Debian 13 is needed»: the «blocked» screen, T9)
	Lowest string `json:"minimum,omitempty"`
}

// Dependency: a distribution package REMOTIX requires for a desktop.
type Dependency struct {
	Name string `json:"name"`
	Why  string `json:"why"` // «XFCE»: for which desktop
}

// put: one more dependency (only once; the desktops that require it add up).
func (r *Report) put(label_name, reason_text string) {
	for i := range r.Dependencies {
		if r.Dependencies[i].Name == label_name {
			if !strings.Contains(r.Dependencies[i].Why, reason_text) {
				r.Dependencies[i].Why += ", " + reason_text
			}
			return
		}
	}
	r.Dependencies = append(r.Dependencies, Dependency{label_name, reason_text})
}

// DependencyNames: the names of the packages the manager is to install together with REMOTIX.
func (r *Report) DependencyNames() []string {
	var n []string
	for _, d := range r.Dependencies {
		n = append(n, d.Name)
	}
	return n
}

// beforeVersion: the oldest version of a distribution that the catalogue supports.
func (c *Catalog) beforeVersion(id string) string {
	min := ""
	for _, p := range c.Platforms {
		if p.ID != id {
			continue
		}
		for _, v := range p.Versions {
			if v != "*" && (min == "" || CompareVersions(v, min) < 0) {
				min = v
			}
		}
		if min != "" {
			return strings.TrimSpace(p.Distrib + " " + min)
		}
	}
	return min
}

func versionMatches(vers []string, v string) bool {
	for _, x := range vers {
		if x == "*" || x == v || strings.HasPrefix(v, x+".") {
			return true
		}
	}
	return false
}

// find the catalogue's platform by id and version; derivative = the real id is not the
// platform's but one of its derivatives'.
func (c *Catalog) find(id, version_v string) (pl *Platform, derivative *Derivative) {
	for i := range c.Platforms {
		p := &c.Platforms[i]
		if p.ID == id && versionMatches(p.Versions, version_v) {
			return p, nil
		}
	}
	for i := range c.Platforms {
		p := &c.Platforms[i]
		for j := range p.Derived {
			d := &p.Derived[j]
			if d.ID == id && versionMatches(d.Versions, version_v) {
				return p, d
			}
		}
	}
	return nil, nil
}

// Evaluate: phase 2 COMPATIBILITY, desktop by desktop.
func Evaluate(c *Catalog, p *Profile) *Report {
	r := &Report{Schema: Schema, Object: "compatibility", Created: now(),
		Catalog: CatalogRef{c.Version, c.Digest}}
	id, ver := p.V("distro.id"), p.V("distro.version")
	r.Platform = strings.TrimSpace(p.V("distro.name"))

	// reasons that hold for every desktop
	var all_v []Message
	for _, e := range c.Excluded {
		if e.ID == id && versionMatches(e.Versions, ver) {
			all_v = append(all_v, Msg("RX-COMPAT-001", e.Motivo))
			r.Recognized = T("comp.esclusa")
			r.Lowest = c.beforeVersion(id)
		}
	}
	if p.V("distro.immutable") == "yes" {
		all_v = append(all_v, Msg("RX-COMPAT-003", ""))
	}
	if c.Requirements.Systemd && p.V("system.systemd") == "no" {
		all_v = append(all_v, Msg("RX-COMPAT-007", "the machine did not boot with systemd"))
	}
	if v := p.V("openssl.version"); v != "" && CompareVersions(v, c.Requirements.OpensslMinimum) < 0 {
		all_v = append(all_v, Msg("RX-COMPAT-007", "OpenSSL "+v+", needed "+c.Requirements.OpensslMinimum))
	} else if v == "" {
		r.Unknowns = append(r.Unknowns, T("inc.openssl"))
	}
	pl, derivative := c.find(id, ver)
	r.pl, r.cat = pl, c
	if pl == nil && r.Recognized == "" {
		all_v = append(all_v, Msg("RX-COMPAT-002", id+" "+ver))
		r.Recognized = T("comp.sconosciuta")
	}
	if pl != nil {
		lowest, label_name := pl.MinVersion, pl.Name
		if derivative != nil {
			lowest, label_name = derivative.MinVersion, derivative.Name
		}
		if lowest != "" && CompareVersions(ver, lowest) < 0 {
			all_v = append(all_v, Msg("RX-COMPAT-001", label_name+": needs at least "+lowest))
		}
	}
	if pl != nil && r.Recognized == "" {
		switch {
		case derivative != nil:
			r.Recognized = T("comp.derivative", pl.Name)
		case pl.Matrix:
			r.Recognized = T("comp.nella_matrice", pl.Name)
		default:
			r.Recognized = T("comp.fuori_matrice", pl.Name)
		}
		r.Note = append(r.Note, pl.Note...)
	}

	// phase 19 (DECISIONI §10.27): no encoding on the processor — without a card that an active
	// route can make encode (strade.go), REMOTIX is not installed, on any desktop
	if cod, det := VerdictCard(pl, p); cod != "" {
		all_v = append(all_v, Msg(cod, det))
	}
	condH264 := conditionsH264(pl, p, r)
	// the repositories REMOTIX itself needs (EPEL on Alma): missing on every desktop
	for _, dep := range MissingBaseRepositories(pl, p) {
		r.Missing = append(r.Missing, Msg("RX-MANCA-002", notEmpty(c.Repositories[dep].Name, dep)))
	}
	nobody, possible := true, false
	for _, d := range DESKTOP {
		inst := p.V("desktop." + d)
		if f, ok := p.F("desktop." + d); ok && f.State == UNKNOWN {
			inst = "unknown"
			r.Unknowns = append(r.Unknowns, T("inc.desktop", DesktopName(d)))
		}
		installed := inst != "" && inst != "absent" && inst != "unknown"
		e := DesktopOutcome{Desktop: d, Name: DesktopName(d), Installed: inst, Conditions: []Condition{}}
		e.Reasons = append(e.Reasons, all_v...)
		if pl != nil {
			dc, ok := pl.Desktop[d]
			switch {
			case !ok:
				e.Reasons = append(e.Reasons, Msg("RX-COMPAT-005", ""))
			case !dc.Supported && dc.Pending != "":
				e.Reasons = append(e.Reasons, Msg(notEmpty(dc.Code, "RX-COMPAT-004"), dc.Motivo+" (decision "+dc.Pending+", open)"))
			case !dc.Supported:
				e.Reasons = append(e.Reasons, Msg(notEmpty(dc.Code, "RX-COMPAT-005"), dc.Motivo))
			default:
				e.Conditions = append(e.Conditions, condH264...)
				// the pieces the stock desktop does not bring (labwc, wlr-randr, a scalable
				// font): normal REMOTIX dependencies, the manager installs them together with it
				// (the user, 10 Oct: «let's treat the 3 components as normal dependencies of remotix»).
				// If the distribution does not have them, the manager's simulation says so, and it stops there
				for _, comp := range dc.Components {
					if p.V("package."+comp) == "absent" || p.V("package."+comp) == "" {
						e.Depends = append(e.Depends, comp)
					}
				}
				if dc.NeedsCharacter && p.V("fonts.scalable") == "0" {
					if car := c.ScalableFont[p.V("distro.family")]; car != "" {
						e.Depends = append(e.Depends, car)
					} else {
						e.Missing = append(e.Missing, T("missing.character"))
					}
				}
				for _, l := range dc.Limits {
					e.Conditions = append(e.Conditions, Condition{Code: "C-LIMITE", Text: l})
				}
				if dc.Requires3D != "" {
					if p.V("gpu.nodes") == "none" {
						e.Reasons = append(e.Reasons, Msg("RX-COMPAT-007", T("rsn.3d", DesktopName(d), dc.Requires3D)))
					} else {
						e.Conditions = append(e.Conditions, Condition{Code: "C-HARDWARE", Text: T("cond.3d", DesktopName(d), dc.Requires3D)})
					}
				}
				e.Note = append(e.Note, dc.Note...)
				if min := c.Requirements.minDesktopVersion(d); min != "" && inst != "" && inst[0] >= '0' && inst[0] <= '9' &&
					CompareVersions(inst, min) < 0 {
					e.Reasons = append(e.Reasons, Msg("RX-COMPAT-006", DesktopName(d)+" "+inst+", needed "+min))
				}
			}
		}
		switch {
		case len(e.Reasons) > 0:
			e.Level = NOT_SUPPORTED
			e.Conditions = []Condition{}
			e.Missing, e.Depends = nil, nil
		case pl != nil && pl.Matrix && derivative == nil && pl.FullRound != "":
			e.Level = CERTIFIED
		default:
			e.Level = COMPATIBLE
		}
		if !installed {
			e.Missing = nil // what a desktop that is not there is missing does not count
		}
		possible = possible || e.Level != NOT_SUPPORTED
		if e.Level != NOT_SUPPORTED && installed {
			nobody = false
			if len(e.Missing) > 0 {
				r.Missing = append(r.Missing, Msg("RX-MANCA-003", DesktopName(d)+": "+strings.Join(e.Missing, ", ")))
			}
			for _, n := range e.Depends {
				r.put(n, DesktopName(d))
			}
		}
		r.Desktop = append(r.Desktop, e)
	}

	// Without a supported desktop installed: REMOTIX does not install one (§10.36, supersedes §10.7):
	// it is missing, and we say which ones are fine (if one is possible on this machine: otherwise the reasons
	// for the refusal are enough)
	if nobody && possible {
		r.NoDesktop = true
		r.Missing = append(r.Missing, Msg("RX-MANCA-001", T("manca.desktop", c.Requirements.GnomeMinimum,
			c.Requirements.KdeMinimum, c.Requirements.XfceMinimum, c.Requirements.LxqtMinimum)))
	}
	if r.Missing == nil {
		r.Missing = []Message{}
	}
	for _, m := range p.Messages {
		if m.Severity != INFO {
			r.Messages = append(r.Messages, m)
		}
	}
	return r
}

func notEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

// conditionsH264: H.264 encoding, from the platform and from what the machine has shown: the
// cards that do not encode NEXT TO one that does (the machine without any capable one is already out,
// VerdictCard). ⛔ UNKNOWN is not PASS: if the test could not be done, no condition but
// a declared unknown — not an «all is well».
func conditionsH264(pl *Platform, p *Profile, r *Report) []Condition {
	var cc []Condition
	h, _ := p.F("h264.gpu")
	if h.State == CHECKED && h.Value == "yes" {
		return cc
	}
	// ⭐ phase 19: with the Vulkan ICD the proprietary NVIDIA encodes (route «vulkan») and is no longer out
	if p.V("gpu.nvidia_proprietary") == "yes" && !CardOnRoute("vulkan", "NVIDIA", pl, p) {
		cc = append(cc, Condition{Code: "C-HARDWARE", Text: T("cond.nvidia")})
	}
	if card_vendors, _ := cardVendors(p); pl != nil && pl.H264.AmdWithoutVaapi && card_vendors["AMD"] {
		cc = append(cc, Condition{Code: "C-HARDWARE", Text: T("cond.amd_senza_vaapi", pl.Name)})
	}
	if h.State == UNKNOWN {
		r.Unknowns = append(r.Unknowns, T("inc.h264", h.Note))
	}
	return cc
}
