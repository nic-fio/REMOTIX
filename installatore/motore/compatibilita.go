package motore

import (
	"encoding/json"
	"strings"
)

// FormatoCatalogo is the catalogue's format version (different from the objects': the
// catalogue travels in the remotix-install package, §6.6.8).
const FormatoCatalogo = "remotix-catalogo/1"

// Catalogo: the combinations and their rules (§3, §6.6.8).
type Catalogo struct {
	Formato          string                      `json:"formato"`
	Versione         string                      `json:"versione"`
	Sequenza         int                         `json:"sequenza"`
	Emesso           string                      `json:"emesso"`
	MotoreMinimo     string                      `json:"motore_minimo"`
	Fonte            string                      `json:"fonte"`
	Requisiti        RequisitiCatalogo           `json:"requisiti"`
	Depositi         map[string]DepositoCatalogo `json:"depositi"`
	Piattaforme      []Piattaforma               `json:"piattaforme"`
	Escluse          []Esclusa                   `json:"escluse"`
	FuoriSempre      []string                    `json:"fuori_sempre"`
	ComponentiMinimi []ComponenteMinimo          `json:"componenti_minimi"`
	// CarattereScalabile: the font package per family, when the desktop runs under labwc
	// and the machine has none (a REMOTIX dependency, §10.36)
	CarattereScalabile map[string]string `json:"carattere_scalabile"`

	Digest      string `json:"-"` // sha256 of the bytes read
	Provenienza string `json:"-"` // where it comes from (phase 0 TRUST): the package, the downloaded engine, given by hand
}

// ComponenteMinimo: a line of the table «minimum versions of the components» (§3.1).
type ComponenteMinimo struct {
	Componente string `json:"componente"`
	Minimo     string `json:"minimo"`
	Perche     string `json:"perche"`
}

type RequisitiCatalogo struct {
	OpensslMinima string `json:"openssl_minima"`
	KdeMinima     string `json:"kde_minima"`
	GnomeMinima   string `json:"gnome_minima"`
	XfceMinima    string `json:"xfce_minima"`
	LxqtMinima    string `json:"lxqt_minima"`
	Systemd       bool   `json:"systemd"`
}

// minimaDesktop: the minimum version of a desktop.
func (r RequisitiCatalogo) minimaDesktop(d string) string {
	return map[string]string{"gnome": r.GnomeMinima, "kde": r.KdeMinima, "xfce": r.XfceMinima, "lxqt": r.LxqtMinima}[d]
}

// DepositoCatalogo: a third-party repository a platform requires. The catalogue gives only its name:
// adding it is the administrator's job (DECISIONI §10.36), the engine says it is missing.
type DepositoCatalogo struct {
	Nome string `json:"nome"`
}

type Piattaforma struct {
	ID                string          `json:"id"`
	Distribuzione     string          `json:"distribuzione"`
	Versioni          []string        `json:"versioni"`
	VersioneMinima    string          `json:"versione_minima,omitempty"`
	EtichettaVersione string          `json:"etichetta_versione"`
	Nome              string          `json:"nome"`
	Famiglia          string          `json:"famiglia"`
	Matrice           bool            `json:"matrice"`
	GiroIntero        string          `json:"giro_intero"` // date of the green full run (T10); "" = never
	Derivate          []Derivata      `json:"derivate,omitempty"`
	H264              H264Piattaforma `json:"h264"`
	// Depositi: the repositories REMOTIX itself needs, on any desktop. Phase 19 (no
	// encoding on the processor): only EPEL on Alma remains, which RPM Fusion for EL (the Intel driver with
	// H.264) wants before itself; Cisco's OpenH264 and SVT-AV1 are gone. D5.
	Depositi []string                   `json:"depositi,omitempty"`
	Desktop  map[string]DesktopCatalogo `json:"desktop"`
	Note     []string                   `json:"note,omitempty"`
}

type Derivata struct {
	ID             string   `json:"id"`
	Nome           string   `json:"nome"`
	Versioni       []string `json:"versioni"`
	VersioneMinima string   `json:"versione_minima,omitempty"`
	Nota           string   `json:"nota,omitempty"`
}

// H264Piattaforma: the platform's video encoding, WITHOUT ffmpeg (phase 18) and ONLY on the card
// (phase 19: no fallback to the processor). Since 10 Oct 2026 (DECISIONI §10.36) the engine installs no
// drivers or third-party repositories: the catalogue says only what the platform can do with its own
// packages, and the machine shows whether the driver that is there encodes (famigliaDriver, the 7a test).
type H264Piattaforma struct {
	// AmdSenzaVaapi: on this platform Mesa has no VA-API (Alma/RHEL): AMD does not encode in VA-API
	AmdSenzaVaapi bool `json:"amd_senza_vaapi,omitempty"`
	// SenzaH264DiSerie: the vendors whose VA-API driver, in the distribution's packages, is
	// built without H.264 (Fedora: Intel and AMD; Alma: Intel; openSUSE: AMD). It serves the manual
	// (catalog --table); the machine shows it by itself (famigliaDriver)
	SenzaH264DiSerie []string `json:"senza_h264_di_serie,omitempty"`
	// VulkanCodifica (phase 19, the «vulkan» route of strade.go): the vendors whose OFFICIAL Vulkan
	// driver on this platform encodes H.264/HEVC. Today only AMD (RADV), and only where Mesa is
	// built with the codecs (`[M]` 1 Oct 2026: Debian, Ubuntu, Arch). ⛔ Fedora, RHEL and openSUSE
	// build Mesa with `all_free`: there the official RADV does not encode. ⛔ Intel no: ANV encodes
	// only behind ANV_DEBUG (§10.27), it stays on VA-API. ⛔ NVIDIA no: the ICD belongs to the proprietary driver
	VulkanCodifica []string `json:"vulkan_codifica,omitempty"`
}

// codificaPer: a card vendor encodes H.264 via VA-API on this platform with the driver the
// machine HAS. driverSenza: for it there is only a driver built without H.264 (famigliaDriver): it does not
// encode, and the engine does not install another one (§10.36). Only Intel and AMD have the route.
func (h H264Piattaforma) codificaPer(fornitore string, driverSenza bool) bool {
	switch {
	case fornitore != "Intel" && fornitore != "AMD":
		return false
	case fornitore == "AMD" && h.AmdSenzaVaapi:
		return false
	case driverSenza:
		return false
	}
	return true
}

// fornitoriScheda: the vendors of the machine's cards (scheda.<nodo>.fornitore); noti=false if
// the profile names none (then we stay cautious: as if all were needed).
func fornitoriScheda(p *Profilo) (map[string]bool, bool) {
	r := map[string]bool{}
	for _, f := range p.Fatti {
		if strings.HasPrefix(f.Chiave, "gpu.") && strings.HasSuffix(f.Chiave, ".vendor") && f.Valore != "" {
			r[f.Valore] = true
		}
	}
	return r, len(r) > 0
}

// DepositiBaseMancanti: the repositories REMOTIX itself needs (Piattaforma.Depositi) that are missing.
func DepositiBaseMancanti(pl *Piattaforma, p *Profilo) []string {
	if pl == nil {
		return nil
	}
	var r []string
	for _, d := range pl.Depositi {
		if p.V("repo."+d) != "present" {
			r = append(r, d)
		}
	}
	return r
}

type DesktopCatalogo struct {
	Supportato bool     `json:"supportato"`
	Codice     string   `json:"codice,omitempty"`
	InAttesa   string   `json:"in_attesa,omitempty"` // a decision of the user still open
	Motivo     string   `json:"motivo,omitempty"`
	Componenti []string `json:"componenti,omitempty"`
	Limiti     []string `json:"limiti,omitempty"`
	// Richiede3D: the desktop does not work without the card's 3D acceleration (the why): condition
	// C-HARDWARE; without any card (no render node) NON_SUPPORTATA, RX-COMPAT-007
	Richiede3D string `json:"richiede_3d,omitempty"`
	// ServeCarattere: the desktop runs under labwc, which dies without a scalable font
	// (labwc #2525, §11.1)
	ServeCarattere bool     `json:"serve_carattere,omitempty"`
	Note           []string `json:"note,omitempty"`
}

type Esclusa struct {
	ID       string   `json:"id"`
	Versioni []string `json:"versioni"`
	Motivo   string   `json:"motivo"`
}

// LeggiCatalogo parses a catalogue and computes its digest.
func LeggiCatalogo(b []byte) (*Catalogo, error) {
	var c Catalogo
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, Errore("RX-TRUST-004", err.Error())
	}
	if c.Formato != FormatoCatalogo {
		return nil, Errore("RX-TRUST-004", "format "+c.Formato)
	}
	c.Digest = Sha256(b)
	return &c, nil
}

type RifCatalogo struct {
	Versione string `json:"version"`
	Digest   string `json:"digest"`
}

type RifMotore struct {
	Versione string `json:"version"`
	Digest   string `json:"digest"`
}

// DigestMotore: sha256 of the running binary. ⚠ On the machine itself it does not hold against root
// (§6.6.11): it serves to say, afterwards, which engine did the operation.
func DigestMotore() string {
	d, err := Sha256File("/proc/self/exe")
	if err != nil || d == "" {
		return "unknown"
	}
	return d
}

// Condizione: one of the conditions C-… of §6.6.8, with its remedy.
// Condizione: one of the conditions C-… of §6.6.8: REMOTIX works, with a stated limit.
type Condizione struct {
	Codice string `json:"code"`
	Testo  string `json:"text"`
}

// Compatibility levels (§6.6.8).
const (
	CERTIFICATA    = "CERTIFIED"
	COMPATIBILE    = "COMPATIBLE"
	NON_SUPPORTATA = "UNSUPPORTED"
)

// EsitoDesktop: the level for one desktop.
type EsitoDesktop struct {
	Desktop    string       `json:"desktop"`
	Nome       string       `json:"name"`
	Installato string       `json:"installed"` // version, "absent" or "unknown"
	Livello    string       `json:"level"`
	Condizioni []Condizione `json:"conditions"`
	Motivi     []Messaggio  `json:"reasons,omitempty"` // why NON_SUPPORTATA
	// Mancano: what is missing on this machine for REMOTIX to run on this installed desktop
	// (DECISIONI §10.36: it is stated, the administrator provides it; the installation stops)
	Mancano []string `json:"missing,omitempty"`
	// Dipende: the distribution packages this desktop requires of REMOTIX (dependencies)
	Dipende []string `json:"depends,omitempty"`
	Note    []string `json:"notes,omitempty"`
}

// Rapporto of compatibility: the second object (§6.6.1).
type Rapporto struct {
	Formato      string      `json:"format"`
	Oggetto      string      `json:"object"` // "compatibility"
	Creato       string      `json:"created"`
	Catalogo     RifCatalogo `json:"catalog"`
	Piattaforma  string      `json:"platform"` // "Debian 13"
	pl           *Piattaforma
	cat          *Catalogo
	Riconosciuta string         `json:"recognized"` // in the matrix · outside the matrix · derivative of … · excluded · unknown
	Desktop      []EsitoDesktop `json:"desktop"`
	SenzaDesktop bool           `json:"no_desktop"` // no supported desktop installed
	// Mancano: everything this machine is missing, BLOCKING (DECISIONI §10.36): REMOTIX does not
	// install anything of the system, it says so. Empty = it can be installed
	Mancano []Messaggio `json:"missing"`
	// Dipendenze: the pieces the machine's desktop requires of REMOTIX (labwc, wlr-randr, a scalable
	// font): normal dependencies, the engine adds them to the packages to install and the manager
	// takes them from the distribution's repositories (the user, 10 Oct 2026, §10.36)
	Dipendenze []Dipendenza `json:"dependencies"`
	Incognite  []string     `json:"unknowns,omitempty"` // UNKNOWN facts that affect the judgement
	Messaggi   []Messaggio  `json:"messages"`
	Note       []string     `json:"notes,omitempty"`
	// Minima: for an excluded version, the first version of the same distribution that the
	// catalogue supports («at least Debian 13 is needed»: the «blocked» screen, T9)
	Minima string `json:"minimum,omitempty"`
}

// Dipendenza: a distribution package REMOTIX requires for a desktop.
type Dipendenza struct {
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
	r.Dipendenze = append(r.Dipendenze, Dipendenza{nome, perche})
}

// NomiDipendenze: the names of the packages the manager is to install together with REMOTIX.
func (r *Rapporto) NomiDipendenze() []string {
	var n []string
	for _, d := range r.Dipendenze {
		n = append(n, d.Nome)
	}
	return n
}

// primaVersione: the oldest version of a distribution that the catalogue supports.
func (c *Catalogo) primaVersione(id string) string {
	min := ""
	for _, p := range c.Piattaforme {
		if p.ID != id {
			continue
		}
		for _, v := range p.Versioni {
			if v != "*" && (min == "" || ConfrontaVersioni(v, min) < 0) {
				min = v
			}
		}
		if min != "" {
			return strings.TrimSpace(p.Distribuzione + " " + min)
		}
	}
	return min
}

func versioneCombacia(versioni []string, v string) bool {
	for _, x := range versioni {
		if x == "*" || x == v || strings.HasPrefix(v, x+".") {
			return true
		}
	}
	return false
}

// trova the catalogue's platform by id and version; derivata = the real id is not the
// platform's but one of its derivatives'.
func (c *Catalogo) trova(id, versione string) (pl *Piattaforma, derivata *Derivata) {
	for i := range c.Piattaforme {
		p := &c.Piattaforme[i]
		if p.ID == id && versioneCombacia(p.Versioni, versione) {
			return p, nil
		}
	}
	for i := range c.Piattaforme {
		p := &c.Piattaforme[i]
		for j := range p.Derivate {
			d := &p.Derivate[j]
			if d.ID == id && versioneCombacia(d.Versioni, versione) {
				return p, d
			}
		}
	}
	return nil, nil
}

// Valuta: phase 2 COMPATIBILITY, desktop by desktop.
func Valuta(c *Catalogo, p *Profilo) *Rapporto {
	r := &Rapporto{Formato: Formato, Oggetto: "compatibility", Creato: ora(),
		Catalogo: RifCatalogo{c.Versione, c.Digest}}
	id, ver := p.V("distro.id"), p.V("distro.version")
	r.Piattaforma = strings.TrimSpace(p.V("distro.name"))

	// reasons that hold for every desktop
	var tutti []Messaggio
	for _, e := range c.Escluse {
		if e.ID == id && versioneCombacia(e.Versioni, ver) {
			tutti = append(tutti, Msg("RX-COMPAT-001", e.Motivo))
			r.Riconosciuta = T("comp.esclusa")
			r.Minima = c.primaVersione(id)
		}
	}
	if p.V("distro.immutable") == "yes" {
		tutti = append(tutti, Msg("RX-COMPAT-003", ""))
	}
	if c.Requisiti.Systemd && p.V("system.systemd") == "no" {
		tutti = append(tutti, Msg("RX-COMPAT-007", "the machine did not boot with systemd"))
	}
	if v := p.V("openssl.version"); v != "" && ConfrontaVersioni(v, c.Requisiti.OpensslMinima) < 0 {
		tutti = append(tutti, Msg("RX-COMPAT-007", "OpenSSL "+v+", needed "+c.Requisiti.OpensslMinima))
	} else if v == "" {
		r.Incognite = append(r.Incognite, T("inc.openssl"))
	}
	pl, derivata := c.trova(id, ver)
	r.pl, r.cat = pl, c
	if pl == nil && r.Riconosciuta == "" {
		tutti = append(tutti, Msg("RX-COMPAT-002", id+" "+ver))
		r.Riconosciuta = T("comp.sconosciuta")
	}
	if pl != nil {
		minima, nome := pl.VersioneMinima, pl.Nome
		if derivata != nil {
			minima, nome = derivata.VersioneMinima, derivata.Nome
		}
		if minima != "" && ConfrontaVersioni(ver, minima) < 0 {
			tutti = append(tutti, Msg("RX-COMPAT-001", nome+": needs at least "+minima))
		}
	}
	if pl != nil && r.Riconosciuta == "" {
		switch {
		case derivata != nil:
			r.Riconosciuta = T("comp.derivata", pl.Nome)
		case pl.Matrice:
			r.Riconosciuta = T("comp.nella_matrice", pl.Nome)
		default:
			r.Riconosciuta = T("comp.fuori_matrice", pl.Nome)
		}
		r.Note = append(r.Note, pl.Note...)
	}

	// phase 19 (DECISIONI §10.27): no encoding on the processor — without a card that an active
	// route can make encode (strade.go), REMOTIX is not installed, on any desktop
	if cod, det := VerdettoScheda(pl, p); cod != "" {
		tutti = append(tutti, Msg(cod, det))
	}
	condH264 := condizioniH264(pl, p, r)
	// the repositories REMOTIX itself needs (EPEL on Alma): missing on every desktop
	for _, dep := range DepositiBaseMancanti(pl, p) {
		r.Mancano = append(r.Mancano, Msg("RX-MANCA-002", nonVuoto(c.Depositi[dep].Nome, dep)))
	}
	nessuno, possibile := true, false
	for _, d := range DESKTOP {
		inst := p.V("desktop." + d)
		if f, ok := p.F("desktop." + d); ok && f.Stato == SCONOSCIUTO {
			inst = "unknown"
			r.Incognite = append(r.Incognite, T("inc.desktop", NomeDesktop(d)))
		}
		installato := inst != "" && inst != "absent" && inst != "unknown"
		e := EsitoDesktop{Desktop: d, Nome: NomeDesktop(d), Installato: inst, Condizioni: []Condizione{}}
		e.Motivi = append(e.Motivi, tutti...)
		if pl != nil {
			dc, ok := pl.Desktop[d]
			switch {
			case !ok:
				e.Motivi = append(e.Motivi, Msg("RX-COMPAT-005", ""))
			case !dc.Supportato && dc.InAttesa != "":
				e.Motivi = append(e.Motivi, Msg(nonVuoto(dc.Codice, "RX-COMPAT-004"), dc.Motivo+" (decision "+dc.InAttesa+", open)"))
			case !dc.Supportato:
				e.Motivi = append(e.Motivi, Msg(nonVuoto(dc.Codice, "RX-COMPAT-005"), dc.Motivo))
			default:
				e.Condizioni = append(e.Condizioni, condH264...)
				// the pieces the stock desktop does not bring (labwc, wlr-randr, a scalable
				// font): normal REMOTIX dependencies, the manager installs them together with it
				// (the user, 10 Oct: «let's treat the 3 components as normal dependencies of remotix»).
				// If the distribution does not have them, the manager's simulation says so, and it stops there
				for _, comp := range dc.Componenti {
					if p.V("package."+comp) == "absent" || p.V("package."+comp) == "" {
						e.Dipende = append(e.Dipende, comp)
					}
				}
				if dc.ServeCarattere && p.V("fonts.scalable") == "0" {
					if car := c.CarattereScalabile[p.V("distro.family")]; car != "" {
						e.Dipende = append(e.Dipende, car)
					} else {
						e.Mancano = append(e.Mancano, T("manca.carattere"))
					}
				}
				for _, l := range dc.Limiti {
					e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-LIMITE", Testo: l})
				}
				if dc.Richiede3D != "" {
					if p.V("gpu.nodes") == "none" {
						e.Motivi = append(e.Motivi, Msg("RX-COMPAT-007", T("mot.3d", NomeDesktop(d), dc.Richiede3D)))
					} else {
						e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-HARDWARE", Testo: T("cond.3d", NomeDesktop(d), dc.Richiede3D)})
					}
				}
				e.Note = append(e.Note, dc.Note...)
				if min := c.Requisiti.minimaDesktop(d); min != "" && inst != "" && inst[0] >= '0' && inst[0] <= '9' &&
					ConfrontaVersioni(inst, min) < 0 {
					e.Motivi = append(e.Motivi, Msg("RX-COMPAT-006", NomeDesktop(d)+" "+inst+", needed "+min))
				}
			}
		}
		switch {
		case len(e.Motivi) > 0:
			e.Livello = NON_SUPPORTATA
			e.Condizioni = []Condizione{}
			e.Mancano, e.Dipende = nil, nil
		case pl != nil && pl.Matrice && derivata == nil && pl.GiroIntero != "":
			e.Livello = CERTIFICATA
		default:
			e.Livello = COMPATIBILE
		}
		if !installato {
			e.Mancano = nil // what a desktop that is not there is missing does not count
		}
		possibile = possibile || e.Livello != NON_SUPPORTATA
		if e.Livello != NON_SUPPORTATA && installato {
			nessuno = false
			if len(e.Mancano) > 0 {
				r.Mancano = append(r.Mancano, Msg("RX-MANCA-003", NomeDesktop(d)+": "+strings.Join(e.Mancano, ", ")))
			}
			for _, n := range e.Dipende {
				r.metti(n, NomeDesktop(d))
			}
		}
		r.Desktop = append(r.Desktop, e)
	}

	// Without a supported desktop installed: REMOTIX does not install one (§10.36, supersedes §10.7):
	// it is missing, and we say which ones are fine (if one is possible on this machine: otherwise the reasons
	// for the refusal are enough)
	if nessuno && possibile {
		r.SenzaDesktop = true
		r.Mancano = append(r.Mancano, Msg("RX-MANCA-001", T("manca.desktop", c.Requisiti.GnomeMinima,
			c.Requisiti.KdeMinima, c.Requisiti.XfceMinima, c.Requisiti.LxqtMinima)))
	}
	if r.Mancano == nil {
		r.Mancano = []Messaggio{}
	}
	for _, m := range p.Messaggi {
		if m.Gravita != INFO {
			r.Messaggi = append(r.Messaggi, m)
		}
	}
	return r
}

func nonVuoto(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

// condizioniH264: H.264 encoding, from the platform and from what the machine has shown: the
// cards that do not encode NEXT TO one that does (the machine without any capable one is already out,
// VerdettoScheda). ⛔ UNKNOWN is not PASS: if the test could not be done, no condition but
// a declared unknown — not an «all is well».
func condizioniH264(pl *Piattaforma, p *Profilo, r *Rapporto) []Condizione {
	var cc []Condizione
	h, _ := p.F("h264.gpu")
	if h.Stato == VERIFICATO && h.Valore == "yes" {
		return cc
	}
	// ⭐ phase 19: with the Vulkan ICD the proprietary NVIDIA encodes (route «vulkan») and is no longer out
	if p.V("gpu.nvidia_proprietary") == "yes" && !SchedaSullaStrada("vulkan", "NVIDIA", pl, p) {
		cc = append(cc, Condizione{Codice: "C-HARDWARE", Testo: T("cond.nvidia")})
	}
	if forn, _ := fornitoriScheda(p); pl != nil && pl.H264.AmdSenzaVaapi && forn["AMD"] {
		cc = append(cc, Condizione{Codice: "C-HARDWARE", Testo: T("cond.amd_senza_vaapi", pl.Nome)})
	}
	if h.Stato == SCONOSCIUTO {
		r.Incognite = append(r.Incognite, T("inc.h264", h.Nota))
	}
	return cc
}
