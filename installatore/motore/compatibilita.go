package motore

import (
	"encoding/json"
	"strings"
)

// FormatoCatalogo è la versione di formato del catalogo (diversa da quella degli oggetti: il
// catalogo viaggia nel pacchetto remotix-install, §6.6.8).
const FormatoCatalogo = "remotix-catalogo/1"

// Catalogo: le combinazioni e le loro regole (§3, §6.6.8).
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
	// CarattereScalabile: il pacchetto del carattere per famiglia, quando il desktop gira sotto labwc
	// e la macchina non ne ha nessuno (una dipendenza di REMOTIX, §10.36)
	CarattereScalabile map[string]string `json:"carattere_scalabile"`

	Digest      string `json:"-"` // sha256 dei byte letti
	Provenienza string `json:"-"` // da dove viene (fase 0 TRUST): il pacchetto, il motore scaricato, dato a mano
}

// ComponenteMinimo: una riga della tabella «versioni minime dei componenti» (§3.1).
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

// minimaDesktop: la versione minima di un desktop.
func (r RequisitiCatalogo) minimaDesktop(d string) string {
	return map[string]string{"gnome": r.GnomeMinima, "kde": r.KdeMinima, "xfce": r.XfceMinima, "lxqt": r.LxqtMinima}[d]
}

// DepositoCatalogo: un archivio di terzi che una piattaforma chiede. Il catalogo ne dà solo il nome:
// aggiungerlo è dell'amministratore (DECISIONI §10.36), il motore dice che manca.
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
	GiroIntero        string          `json:"giro_intero"` // data del giro intero verde (T10); "" = mai
	Derivate          []Derivata      `json:"derivate,omitempty"`
	H264              H264Piattaforma `json:"h264"`
	// Depositi: gli archivi che servono a REMOTIX stesso, su qualunque desktop. Fase 19 (niente
	// codifica sul processore): resta solo EPEL su Alma, che RPM Fusion per EL (il driver Intel con
	// H.264) vuole prima di sé; OpenH264 di Cisco e SVT-AV1 sono usciti. D5.
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

// H264Piattaforma: la codifica video della piattaforma, SENZA ffmpeg (fase 18) e SOLO sulla scheda
// (fase 19: niente ripiego sul processore). Dal 10 ott 2026 (DECISIONI §10.36) il motore non installa
// driver né archivi di terzi: il catalogo dice soltanto che cosa la piattaforma sa fare coi suoi
// pacchetti, e la macchina mostra se il driver che c'è codifica (famigliaDriver, la prova di 7a).
type H264Piattaforma struct {
	// AmdSenzaVaapi: su questa piattaforma Mesa non ha VA-API (Alma/RHEL): la AMD non codifica in VA-API
	AmdSenzaVaapi bool `json:"amd_senza_vaapi,omitempty"`
	// SenzaH264DiSerie: i fornitori il cui driver VA-API, nei pacchetti della distribuzione, è
	// costruito senza H.264 (Fedora: Intel e AMD; Alma: Intel; openSUSE: AMD). Serve al manuale
	// (catalog --table); la macchina lo mostra da sé (famigliaDriver)
	SenzaH264DiSerie []string `json:"senza_h264_di_serie,omitempty"`
	// VulkanCodifica (fase 19, la strada «vulkan» di strade.go): i fornitori il cui driver Vulkan
	// UFFICIALE di questa piattaforma codifica H.264/HEVC. Oggi solo AMD (RADV), e solo dove Mesa è
	// costruita coi codec (`[M]` 1 ott 2026: Debian, Ubuntu, Arch). ⛔ Fedora, RHEL e openSUSE
	// costruiscono Mesa con `all_free`: lì la RADV ufficiale non codifica. ⛔ Intel no: ANV codifica
	// solo dietro ANV_DEBUG (§10.27), resta a VA-API. ⛔ NVIDIA no: l'ICD è del driver proprietario
	VulkanCodifica []string `json:"vulkan_codifica,omitempty"`
}

// codificaPer: un fornitore di schede codifica H.264 via VA-API su questa piattaforma col driver che
// la macchina HA. driverSenza: per lui c'è solo un driver costruito senza H.264 (famigliaDriver): non
// codifica, e il motore non ne installa un altro (§10.36). Solo Intel e AMD hanno la strada.
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

// fornitoriScheda: i fornitori delle schede della macchina (scheda.<nodo>.fornitore); noti=false se
// il profilo non ne dice nessuno (allora si resta prudenti: come se servissero tutti).
func fornitoriScheda(p *Profilo) (map[string]bool, bool) {
	r := map[string]bool{}
	for _, f := range p.Fatti {
		if strings.HasPrefix(f.Chiave, "gpu.") && strings.HasSuffix(f.Chiave, ".vendor") && f.Valore != "" {
			r[f.Valore] = true
		}
	}
	return r, len(r) > 0
}

// DepositiBaseMancanti: i depositi che servono a REMOTIX stesso (Piattaforma.Depositi) e mancano.
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
	InAttesa   string   `json:"in_attesa,omitempty"` // una decisione dell'utente ancora aperta
	Motivo     string   `json:"motivo,omitempty"`
	Componenti []string `json:"componenti,omitempty"`
	Limiti     []string `json:"limiti,omitempty"`
	// Richiede3D: il desktop non va senza l'accelerazione 3D della scheda (il perché): condizione
	// C-HARDWARE; senza nessuna scheda (nessun nodo di rendering) NON_SUPPORTATA, RX-COMPAT-007
	Richiede3D string `json:"richiede_3d,omitempty"`
	// ServeCarattere: il desktop gira sotto labwc, che muore senza un carattere scalabile
	// (labwc #2525, §11.1)
	ServeCarattere bool     `json:"serve_carattere,omitempty"`
	Note           []string `json:"note,omitempty"`
}

type Esclusa struct {
	ID       string   `json:"id"`
	Versioni []string `json:"versioni"`
	Motivo   string   `json:"motivo"`
}

// LeggiCatalogo interpreta un catalogo e ne calcola il digest.
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

// DigestMotore: sha256 del binario che gira. ⚠ Sulla macchina stessa non vale contro root
// (§6.6.11): serve a dire, a posteriori, quale motore ha fatto l'operazione.
func DigestMotore() string {
	d, err := Sha256File("/proc/self/exe")
	if err != nil || d == "" {
		return "unknown"
	}
	return d
}

// Condizione: una delle condizioni C-… di §6.6.8, col suo rimedio.
// Condizione: una delle condizioni C-… di §6.6.8: REMOTIX funziona, con un limite detto.
type Condizione struct {
	Codice string `json:"code"`
	Testo  string `json:"text"`
}

// Livelli di compatibilità (§6.6.8).
const (
	CERTIFICATA    = "CERTIFIED"
	COMPATIBILE    = "COMPATIBLE"
	NON_SUPPORTATA = "UNSUPPORTED"
)

// EsitoDesktop: il livello per un desktop.
type EsitoDesktop struct {
	Desktop    string       `json:"desktop"`
	Nome       string       `json:"name"`
	Installato string       `json:"installed"` // versione, "absent" o "unknown"
	Livello    string       `json:"level"`
	Condizioni []Condizione `json:"conditions"`
	Motivi     []Messaggio  `json:"reasons,omitempty"` // perché NON_SUPPORTATA
	// Mancano: quel che manca su questa macchina perché REMOTIX giri su questo desktop installato
	// (DECISIONI §10.36: lo si dice, provvede l'amministratore; l'installazione si ferma)
	Mancano []string `json:"missing,omitempty"`
	// Dipende: i pacchetti della distribuzione che questo desktop chiede a REMOTIX (dipendenze)
	Dipende []string `json:"depends,omitempty"`
	Note    []string `json:"notes,omitempty"`
}

// Rapporto di compatibilità: il secondo oggetto (§6.6.1).
type Rapporto struct {
	Formato      string      `json:"format"`
	Oggetto      string      `json:"object"` // "compatibility"
	Creato       string      `json:"created"`
	Catalogo     RifCatalogo `json:"catalog"`
	Piattaforma  string      `json:"platform"` // "Debian 13"
	pl           *Piattaforma
	cat          *Catalogo
	Riconosciuta string         `json:"recognized"` // matrice · fuori matrice · derivata di … · esclusa · sconosciuta
	Desktop      []EsitoDesktop `json:"desktop"`
	SenzaDesktop bool           `json:"no_desktop"` // nessun desktop supportato installato
	// Mancano: tutto quel che manca a questa macchina, BLOCCANTE (DECISIONI §10.36): REMOTIX non
	// installa niente del sistema, lo dice. Vuoto = si può installare
	Mancano []Messaggio `json:"missing"`
	// Dipendenze: i pezzi che il desktop della macchina chiede a REMOTIX (labwc, wlr-randr, un carattere
	// scalabile): dipendenze normali, il motore li aggiunge ai pacchetti da installare e il gestore li
	// prende dagli archivi della distribuzione (utente, 10 ott 2026, §10.36)
	Dipendenze []Dipendenza `json:"dependencies"`
	Incognite  []string     `json:"unknowns,omitempty"` // fatti SCONOSCIUTI che toccano il giudizio
	Messaggi   []Messaggio  `json:"messages"`
	Note       []string     `json:"notes,omitempty"`
	// Minima: per una versione esclusa, la prima versione della stessa distribuzione che il
	// catalogo sostiene («serve almeno Debian 13»: la schermata «bloccata», T9)
	Minima string `json:"minimum,omitempty"`
}

// Dipendenza: un pacchetto della distribuzione che REMOTIX chiede per un desktop.
type Dipendenza struct {
	Nome   string `json:"name"`
	Perche string `json:"why"` // «XFCE»: per quale desktop
}

// metti: una dipendenza in più (una volta sola; i desktop che la chiedono si sommano).
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

// NomiDipendenze: i nomi dei pacchetti da far installare al gestore insieme a REMOTIX.
func (r *Rapporto) NomiDipendenze() []string {
	var n []string
	for _, d := range r.Dipendenze {
		n = append(n, d.Nome)
	}
	return n
}

// primaVersione: la versione più vecchia di una distribuzione che il catalogo sostiene.
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

// trova la piattaforma del catalogo per id e versione; derivata = l'id vero non è quello della
// piattaforma ma di una sua derivata.
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

// Valuta: fase 2 COMPATIBILITY, desktop per desktop.
func Valuta(c *Catalogo, p *Profilo) *Rapporto {
	r := &Rapporto{Formato: Formato, Oggetto: "compatibility", Creato: ora(),
		Catalogo: RifCatalogo{c.Versione, c.Digest}}
	id, ver := p.V("distro.id"), p.V("distro.version")
	r.Piattaforma = strings.TrimSpace(p.V("distro.name"))

	// motivi che valgono per ogni desktop
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

	// fase 19 (DECISIONI §10.27): niente codifica sul processore — senza una scheda che una strada
	// attiva sappia far codificare (strade.go), REMOTIX non si installa, su nessun desktop
	if cod, det := VerdettoScheda(pl, p); cod != "" {
		tutti = append(tutti, Msg(cod, det))
	}
	condH264 := condizioniH264(pl, p, r)
	// i depositi che servono a REMOTIX stesso (su Alma EPEL): mancano su ogni desktop
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
				e.Motivi = append(e.Motivi, Msg(nonVuoto(dc.Codice, "RX-COMPAT-004"), dc.Motivo+" (decisione "+dc.InAttesa+", open)"))
			case !dc.Supportato:
				e.Motivi = append(e.Motivi, Msg(nonVuoto(dc.Codice, "RX-COMPAT-005"), dc.Motivo))
			default:
				e.Condizioni = append(e.Condizioni, condH264...)
				// i pezzi che il desktop di serie non porta (labwc, wlr-randr, un carattere
				// scalabile): dipendenze normali di REMOTIX, li installa il gestore insieme a lui
				// (utente, 10 ott: «trattiamo i 3 componenti come normali dipendenze di remotix»).
				// Se la distribuzione non li ha, lo dice la simulazione del gestore, e lì si ferma
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
			e.Mancano = nil // quel che manca a un desktop che non c'è non conta
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

	// Senza un desktop supportato installato: REMOTIX non ne installa uno (§10.36, supera §10.7):
	// manca, e si dice quali vanno bene (se su questa macchina uno è possibile: altrimenti i motivi
	// del rifiuto bastano)
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

// condizioniH264: la codifica H.264, dalla piattaforma e da quel che la macchina ha mostrato: le
// schede che non codificano ACCANTO a una che sì (la macchina senza nessuna capace è già fuori,
// VerdettoScheda). ⛔ UNKNOWN non è PASS: se la prova non si è potuta fare, niente condizione ma
// un'incognita dichiarata — non un «va tutto bene».
func condizioniH264(pl *Piattaforma, p *Profilo, r *Rapporto) []Condizione {
	var cc []Condizione
	h, _ := p.F("h264.gpu")
	if h.Stato == VERIFICATO && h.Valore == "yes" {
		return cc
	}
	// ⭐ fase 19: con l'ICD Vulkan la NVIDIA proprietaria codifica (strada «vulkan») e non è più fuori
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
