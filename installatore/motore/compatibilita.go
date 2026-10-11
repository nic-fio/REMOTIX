package motore

import (
	"encoding/json"
	"strings"
)

// CatalogFormat is the catalogue's format version (different from the objects': the
// catalogue travels in the remotix-install package, §6.6.8).
const CatalogFormat = "remotix-catalogo/1"

// Catalogo: the combinations and their rules (§3, §6.6.8).
type Catalogo struct {
	Formato       string                       `json:"formato"`
	Version       string                       `json:"versione"`
	Sequence      int                          `json:"sequenza"`
	Emitted       string                       `json:"emesso"`
	EngineMinimum string                       `json:"motore_minimo"`
	Source        string                       `json:"fonte"`
	Requirements  CatalogRequirements          `json:"requisiti"`
	Repositories  map[string]RepositoryCatalog `json:"depositi"`
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
	Component string `json:"componente"`
	Minimum   string `json:"minimo"`
	Perche    string `json:"perche"`
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
	Nome string `json:"nome"`
}

type Platform struct {
	ID           string          `json:"id"`
	Distrib      string          `json:"distribuzione"`
	Versions     []string        `json:"versioni"`
	MinVersion   string          `json:"versione_minima,omitempty"`
	VersionLabel string          `json:"etichetta_versione"`
	Nome         string          `json:"nome"`
	Famiglia     string          `json:"famiglia"`
	Matrix       bool            `json:"matrice"`
	FullRound    string          `json:"giro_intero"` // date of the green full run (T10); "" = never
	Derived      []Derivative    `json:"derivate,omitempty"`
	H264         H264Piattaforma `json:"h264"`
	// Depositi: the repositories REMOTIX itself needs, on any desktop. Phase 19 (no
	// encoding on the processor): only EPEL on Alma remains, which RPM Fusion for EL (the Intel driver with
	// H.264) wants before itself; Cisco's OpenH264 and SVT-AV1 are gone. D5.
	Repositories []string                  `json:"depositi,omitempty"`
	Desktop      map[string]DesktopCatalog `json:"desktop"`
	Note         []string                  `json:"note,omitempty"`
}

type Derivative struct {
	ID         string   `json:"id"`
	Nome       string   `json:"nome"`
	Versions   []string `json:"versioni"`
	MinVersion string   `json:"versione_minima,omitempty"`
	Nota       string   `json:"nota,omitempty"`
}

// H264Piattaforma: the platform's video encoding, WITHOUT ffmpeg (phase 18) and ONLY on the card
// (phase 19: no fallback to the processor). Since 10 Oct 2026 (DECISIONI §10.36) the engine installs no
// drivers or third-party repositories: the catalogue says only what the platform can do with its own
// packages, and the machine shows whether the driver that is there encodes (famigliaDriver, the 7a test).
type H264Piattaforma struct {
	// AmdWithoutVaapi: on this platform Mesa has no VA-API (Alma/RHEL): AMD does not encode in VA-API
	AmdWithoutVaapi bool `json:"amd_senza_vaapi,omitempty"`
	// NoStockH264: the vendors whose VA-API driver, in the distribution's packages, is
	// built without H.264 (Fedora: Intel and AMD; Alma: Intel; openSUSE: AMD). It serves the manual
	// (catalog --table); the machine shows it by itself (famigliaDriver)
	NoStockH264 []string `json:"senza_h264_di_serie,omitempty"`
	// VulkanEncoding (phase 19, the «vulkan» route of strade.go): the vendors whose OFFICIAL Vulkan
	// driver on this platform encodes H.264/HEVC. Today only AMD (RADV), and only where Mesa is
	// built with the codecs (`[M]` 1 Oct 2026: Debian, Ubuntu, Arch). ⛔ Fedora, RHEL and openSUSE
	// build Mesa with `all_free`: there the official RADV does not encode. ⛔ Intel no: ANV encodes
	// only behind ANV_DEBUG (§10.27), it stays on VA-API. ⛔ NVIDIA no: the ICD belongs to the proprietary driver
	VulkanEncoding []string `json:"vulkan_codifica,omitempty"`
}

// encodesFor: a card vendor encodes H.264 via VA-API on this platform with the driver the
// machine HAS. driverWithout: for it there is only a driver built without H.264 (famigliaDriver): it does not
// encode, and the engine does not install another one (§10.36). Only Intel and AMD have the route.
func (h H264Piattaforma) encodesFor(fornitore string, driverWithout bool) bool {
	switch {
	case fornitore != "Intel" && fornitore != "AMD":
		return false
	case fornitore == "AMD" && h.AmdWithoutVaapi:
		return false
	case driverWithout:
		return false
	}
	return true
}

// cardVendors: the vendors of the machine's cards (scheda.<nodo>.fornitore); noti=false if
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

// MissingBaseRepositories: the repositories REMOTIX itself needs (Piattaforma.Depositi) that are missing.
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
	Supported  bool     `json:"supportato"`
	Codice     string   `json:"codice,omitempty"`
	Pending    string   `json:"in_attesa,omitempty"` // a decision of the user still open
	Motivo     string   `json:"motivo,omitempty"`
	Components []string `json:"componenti,omitempty"`
	Limits     []string `json:"limiti,omitempty"`
	// Requires3D: the desktop does not work without the card's 3D acceleration (the why): condition
	// C-HARDWARE; without any card (no render node) NON_SUPPORTATA, RX-COMPAT-007
	Requires3D string `json:"richiede_3d,omitempty"`
	// NeedsCharacter: the desktop runs under labwc, which dies without a scalable font
	// (labwc #2525, §11.1)
	NeedsCharacter bool     `json:"serve_carattere,omitempty"`
	Note           []string `json:"note,omitempty"`
}

type Excluded struct {
	ID       string   `json:"id"`
	Versions []string `json:"versioni"`
	Motivo   string   `json:"motivo"`
}

// ReadCatalog parses a catalogue and computes its digest.
func ReadCatalog(b []byte) (*Catalogo, error) {
	var c Catalogo
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, Errore("RX-TRUST-004", err.Error())
	}
	if c.Formato != CatalogFormat {
		return nil, Errore("RX-TRUST-004", "format "+c.Formato)
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

// Condizione: one of the conditions C-… of §6.6.8, with its remedy.
// Condizione: one of the conditions C-… of §6.6.8: REMOTIX works, with a stated limit.
type Condition struct {
	Codice string `json:"code"`
	Testo  string `json:"text"`
}

// Compatibility levels (§6.6.8).
const (
	CERTIFICATA    = "CERTIFIED"
	COMPATIBILE    = "COMPATIBLE"
	NON_SUPPORTATA = "UNSUPPORTED"
)

// DesktopOutcome: the level for one desktop.
type DesktopOutcome struct {
	Desktop    string      `json:"desktop"`
	Nome       string      `json:"name"`
	Installed  string      `json:"installed"` // version, "absent" or "unknown"
	Level      string      `json:"level"`
	Condizioni []Condition `json:"conditions"`
	Reasons    []Message   `json:"reasons,omitempty"` // why NON_SUPPORTATA
	// Mancano: what is missing on this machine for REMOTIX to run on this installed desktop
	// (DECISIONI §10.36: it is stated, the administrator provides it; the installation stops)
	Mancano []string `json:"missing,omitempty"`
	// Dipende: the distribution packages this desktop requires of REMOTIX (dependencies)
	Depends []string `json:"depends,omitempty"`
	Note    []string `json:"notes,omitempty"`
}

// Rapporto of compatibility: the second object (§6.6.1).
type Rapporto struct {
	Formato    string     `json:"format"`
	Object     string     `json:"object"` // "compatibility"
	Created    string     `json:"created"`
	Catalogo   CatalogRef `json:"catalog"`
	Platform   string     `json:"platform"` // "Debian 13"
	pl         *Platform
	cat        *Catalogo
	Recognized string           `json:"recognized"` // in the matrix · outside the matrix · derivative of … · excluded · unknown
	Desktop    []DesktopOutcome `json:"desktop"`
	NoDesktop  bool             `json:"no_desktop"` // no supported desktop installed
	// Mancano: everything this machine is missing, BLOCKING (DECISIONI §10.36): REMOTIX does not
	// install anything of the system, it says so. Empty = it can be installed
	Mancano []Message `json:"missing"`
	// Dipendenze: the pieces the machine's desktop requires of REMOTIX (labwc, wlr-randr, a scalable
	// font): normal dependencies, the engine adds them to the packages to install and the manager
	// takes them from the distribution's repositories (the user, 10 Oct 2026, §10.36)
	Dipendenze []Dependency `json:"dependencies"`
	Unknowns   []string     `json:"unknowns,omitempty"` // UNKNOWN facts that affect the judgement
	Messages   []Message    `json:"messages"`
	Note       []string     `json:"notes,omitempty"`
	// Minima: for an excluded version, the first version of the same distribution that the
	// catalogue supports («at least Debian 13 is needed»: the «blocked» screen, T9)
	Minima string `json:"minimum,omitempty"`
}

// Dipendenza: a distribution package REMOTIX requires for a desktop.
type Dependency struct {
	Nome   string `json:"name"`
	Perche string `json:"why"` // «XFCE»: for which desktop
}

// metti: one more dependency (only once; the desktops that require it add up).
func (r *Rapporto) metti(nome, perche string) {
	for i := range r.Dipendenze {
		if r.Dipendenze[i].Nome == nome {
			if !strings.Contains(r.Dipendenze[i].Perche, perche) {
				r.Dipendenze[i].Perche += ", " + perche
			}
			return
		}
	}
	r.Dipendenze = append(r.Dipendenze, Dependency{nome, perche})
}

// DependencyNames: the names of the packages the manager is to install together with REMOTIX.
func (r *Rapporto) DependencyNames() []string {
	var n []string
	for _, d := range r.Dipendenze {
		n = append(n, d.Nome)
	}
	return n
}

// beforeVersion: the oldest version of a distribution that the catalogue supports.
func (c *Catalogo) beforeVersion(id string) string {
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

func versionMatches(versioni []string, v string) bool {
	for _, x := range versioni {
		if x == "*" || x == v || strings.HasPrefix(v, x+".") {
			return true
		}
	}
	return false
}

// trova the catalogue's platform by id and version; derivata = the real id is not the
// platform's but one of its derivatives'.
func (c *Catalogo) trova(id, versione string) (pl *Platform, derivata *Derivative) {
	for i := range c.Platforms {
		p := &c.Platforms[i]
		if p.ID == id && versionMatches(p.Versions, versione) {
			return p, nil
		}
	}
	for i := range c.Platforms {
		p := &c.Platforms[i]
		for j := range p.Derived {
			d := &p.Derived[j]
			if d.ID == id && versionMatches(d.Versions, versione) {
				return p, d
			}
		}
	}
	return nil, nil
}

// Valuta: phase 2 COMPATIBILITY, desktop by desktop.
func Valuta(c *Catalogo, p *Profile) *Rapporto {
	r := &Rapporto{Formato: Formato, Object: "compatibility", Created: ora(),
		Catalogo: CatalogRef{c.Version, c.Digest}}
	id, ver := p.V("distro.id"), p.V("distro.version")
	r.Platform = strings.TrimSpace(p.V("distro.name"))

	// reasons that hold for every desktop
	var tutti []Message
	for _, e := range c.Excluded {
		if e.ID == id && versionMatches(e.Versions, ver) {
			tutti = append(tutti, Msg("RX-COMPAT-001", e.Motivo))
			r.Recognized = T("comp.esclusa")
			r.Minima = c.beforeVersion(id)
		}
	}
	if p.V("distro.immutable") == "yes" {
		tutti = append(tutti, Msg("RX-COMPAT-003", ""))
	}
	if c.Requirements.Systemd && p.V("system.systemd") == "no" {
		tutti = append(tutti, Msg("RX-COMPAT-007", "the machine did not boot with systemd"))
	}
	if v := p.V("openssl.version"); v != "" && CompareVersions(v, c.Requirements.OpensslMinimum) < 0 {
		tutti = append(tutti, Msg("RX-COMPAT-007", "OpenSSL "+v+", needed "+c.Requirements.OpensslMinimum))
	} else if v == "" {
		r.Unknowns = append(r.Unknowns, T("inc.openssl"))
	}
	pl, derivata := c.trova(id, ver)
	r.pl, r.cat = pl, c
	if pl == nil && r.Recognized == "" {
		tutti = append(tutti, Msg("RX-COMPAT-002", id+" "+ver))
		r.Recognized = T("comp.sconosciuta")
	}
	if pl != nil {
		minima, nome := pl.MinVersion, pl.Nome
		if derivata != nil {
			minima, nome = derivata.MinVersion, derivata.Nome
		}
		if minima != "" && CompareVersions(ver, minima) < 0 {
			tutti = append(tutti, Msg("RX-COMPAT-001", nome+": needs at least "+minima))
		}
	}
	if pl != nil && r.Recognized == "" {
		switch {
		case derivata != nil:
			r.Recognized = T("comp.derivata", pl.Nome)
		case pl.Matrix:
			r.Recognized = T("comp.nella_matrice", pl.Nome)
		default:
			r.Recognized = T("comp.fuori_matrice", pl.Nome)
		}
		r.Note = append(r.Note, pl.Note...)
	}

	// phase 19 (DECISIONI §10.27): no encoding on the processor — without a card that an active
	// route can make encode (strade.go), REMOTIX is not installed, on any desktop
	if cod, det := VerdettoScheda(pl, p); cod != "" {
		tutti = append(tutti, Msg(cod, det))
	}
	condH264 := conditionsH264(pl, p, r)
	// the repositories REMOTIX itself needs (EPEL on Alma): missing on every desktop
	for _, dep := range MissingBaseRepositories(pl, p) {
		r.Mancano = append(r.Mancano, Msg("RX-MANCA-002", notEmpty(c.Repositories[dep].Nome, dep)))
	}
	nessuno, possibile := true, false
	for _, d := range DESKTOP {
		inst := p.V("desktop." + d)
		if f, ok := p.F("desktop." + d); ok && f.Stato == SCONOSCIUTO {
			inst = "unknown"
			r.Unknowns = append(r.Unknowns, T("inc.desktop", NomeDesktop(d)))
		}
		installato := inst != "" && inst != "absent" && inst != "unknown"
		e := DesktopOutcome{Desktop: d, Nome: NomeDesktop(d), Installed: inst, Condizioni: []Condition{}}
		e.Reasons = append(e.Reasons, tutti...)
		if pl != nil {
			dc, ok := pl.Desktop[d]
			switch {
			case !ok:
				e.Reasons = append(e.Reasons, Msg("RX-COMPAT-005", ""))
			case !dc.Supported && dc.Pending != "":
				e.Reasons = append(e.Reasons, Msg(notEmpty(dc.Codice, "RX-COMPAT-004"), dc.Motivo+" (decision "+dc.Pending+", open)"))
			case !dc.Supported:
				e.Reasons = append(e.Reasons, Msg(notEmpty(dc.Codice, "RX-COMPAT-005"), dc.Motivo))
			default:
				e.Condizioni = append(e.Condizioni, condH264...)
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
						e.Mancano = append(e.Mancano, T("manca.carattere"))
					}
				}
				for _, l := range dc.Limits {
					e.Condizioni = append(e.Condizioni, Condition{Codice: "C-LIMITE", Testo: l})
				}
				if dc.Requires3D != "" {
					if p.V("gpu.nodes") == "none" {
						e.Reasons = append(e.Reasons, Msg("RX-COMPAT-007", T("mot.3d", NomeDesktop(d), dc.Requires3D)))
					} else {
						e.Condizioni = append(e.Condizioni, Condition{Codice: "C-HARDWARE", Testo: T("cond.3d", NomeDesktop(d), dc.Requires3D)})
					}
				}
				e.Note = append(e.Note, dc.Note...)
				if min := c.Requirements.minDesktopVersion(d); min != "" && inst != "" && inst[0] >= '0' && inst[0] <= '9' &&
					CompareVersions(inst, min) < 0 {
					e.Reasons = append(e.Reasons, Msg("RX-COMPAT-006", NomeDesktop(d)+" "+inst+", needed "+min))
				}
			}
		}
		switch {
		case len(e.Reasons) > 0:
			e.Level = NON_SUPPORTATA
			e.Condizioni = []Condition{}
			e.Mancano, e.Depends = nil, nil
		case pl != nil && pl.Matrix && derivata == nil && pl.FullRound != "":
			e.Level = CERTIFICATA
		default:
			e.Level = COMPATIBILE
		}
		if !installato {
			e.Mancano = nil // what a desktop that is not there is missing does not count
		}
		possibile = possibile || e.Level != NON_SUPPORTATA
		if e.Level != NON_SUPPORTATA && installato {
			nessuno = false
			if len(e.Mancano) > 0 {
				r.Mancano = append(r.Mancano, Msg("RX-MANCA-003", NomeDesktop(d)+": "+strings.Join(e.Mancano, ", ")))
			}
			for _, n := range e.Depends {
				r.metti(n, NomeDesktop(d))
			}
		}
		r.Desktop = append(r.Desktop, e)
	}

	// Without a supported desktop installed: REMOTIX does not install one (§10.36, supersedes §10.7):
	// it is missing, and we say which ones are fine (if one is possible on this machine: otherwise the reasons
	// for the refusal are enough)
	if nessuno && possibile {
		r.NoDesktop = true
		r.Mancano = append(r.Mancano, Msg("RX-MANCA-001", T("manca.desktop", c.Requirements.GnomeMinimum,
			c.Requirements.KdeMinimum, c.Requirements.XfceMinimum, c.Requirements.LxqtMinimum)))
	}
	if r.Mancano == nil {
		r.Mancano = []Message{}
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
// VerdettoScheda). ⛔ UNKNOWN is not PASS: if the test could not be done, no condition but
// a declared unknown — not an «all is well».
func conditionsH264(pl *Platform, p *Profile, r *Rapporto) []Condition {
	var cc []Condition
	h, _ := p.F("h264.gpu")
	if h.Stato == VERIFICATO && h.Value == "yes" {
		return cc
	}
	// ⭐ phase 19: with the Vulkan ICD the proprietary NVIDIA encodes (route «vulkan») and is no longer out
	if p.V("gpu.nvidia_proprietary") == "yes" && !SchedaSullaStrada("vulkan", "NVIDIA", pl, p) {
		cc = append(cc, Condition{Codice: "C-HARDWARE", Testo: T("cond.nvidia")})
	}
	if card_vendors, _ := cardVendors(p); pl != nil && pl.H264.AmdWithoutVaapi && card_vendors["AMD"] {
		cc = append(cc, Condition{Codice: "C-HARDWARE", Testo: T("cond.amd_senza_vaapi", pl.Nome)})
	}
	if h.Stato == SCONOSCIUTO {
		r.Unknowns = append(r.Unknowns, T("inc.h264", h.Nota))
	}
	return cc
}
