package motore

import (
	"encoding/json"
	"strings"
	"time"
)

// FormatoCatalogo è la versione di formato del catalogo (diversa da quella degli oggetti: il
// catalogo si pubblica a parte, con la sua scadenza, §6.6.8).
const FormatoCatalogo = "remotix-catalogo/1"

// Catalogo: le combinazioni e le loro regole (§3, §6.6.8).
type Catalogo struct {
	Formato            string                      `json:"formato"`
	Versione           string                      `json:"versione"`
	Sequenza           int                         `json:"sequenza"`
	Emesso             string                      `json:"emesso"`
	Scadenza           string                      `json:"scadenza"`
	MotoreMinimo       string                      `json:"motore_minimo"`
	Firma              FirmaCatalogo               `json:"firma"`
	Fonte              string                      `json:"fonte"`
	Requisiti          RequisitiCatalogo           `json:"requisiti"`
	Depositi           map[string]DepositoCatalogo `json:"depositi"`
	Installa           map[string]string           `json:"installa"`
	CarattereScalabile map[string]string           `json:"carattere_scalabile"`
	DesktopRiferimento map[string]string           `json:"desktop_di_riferimento"`
	Piattaforme        []Piattaforma               `json:"piattaforme"`
	Escluse            []Esclusa                   `json:"escluse"`
	FuoriSempre        []string                    `json:"fuori_sempre"`
	ComponentiMinimi   []ComponenteMinimo          `json:"componenti_minimi"`

	Digest string `json:"-"` // sha256 dei byte letti
}

// FirmaCatalogo: il catalogo si aggiorna da solo, senza un REMOTIX nuovo (DECISIONI §10.10), con
// la firma in un file separato. Schema e chiavi: catena A (§6.6.10), D11.
type FirmaCatalogo struct {
	Separata string `json:"separata"`
	Schema   string `json:"schema"`
	Nota     string `json:"nota"`
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

type DepositoCatalogo struct {
	Nome      string            `json:"nome"`
	Decisione string            `json:"decisione"`
	Comandi   map[string]string `json:"comandi"`
}

type Piattaforma struct {
	ID                string                     `json:"id"`
	Distribuzione     string                     `json:"distribuzione"`
	Versioni          []string                   `json:"versioni"`
	VersioneMinima    string                     `json:"versione_minima,omitempty"`
	EtichettaVersione string                     `json:"etichetta_versione"`
	Nome              string                     `json:"nome"`
	Famiglia          string                     `json:"famiglia"`
	Matrice           bool                       `json:"matrice"`
	GiroIntero        string                     `json:"giro_intero"` // data del giro intero verde (T10); "" = mai
	Derivate          []Derivata                 `json:"derivate,omitempty"`
	H264              H264Piattaforma            `json:"h264"`
	Desktop           map[string]DesktopCatalogo `json:"desktop"`
	PacchettiDesktop  map[string]string          `json:"pacchetti_desktop"` // desktop → pacchetti (virgole) per installarlo
	Note              []string                   `json:"note,omitempty"`
}

type Derivata struct {
	ID             string   `json:"id"`
	Nome           string   `json:"nome"`
	Versioni       []string `json:"versioni"`
	VersioneMinima string   `json:"versione_minima,omitempty"`
	Nota           string   `json:"nota,omitempty"`
}

type H264Piattaforma struct {
	SchedaDiSerie   bool   `json:"scheda_di_serie"`
	SoftwareDiSerie bool   `json:"software_di_serie"`
	Deposito        string `json:"deposito,omitempty"`
	Comando         string `json:"comando,omitempty"`
	AmdSenzaVaapi   bool   `json:"amd_senza_vaapi,omitempty"`
	// PacchettiCodec: la libavcodec coi codec, dal deposito di terzi (dopo il consenso, D5)
	PacchettiCodec string `json:"pacchetti_codec,omitempty"`
}

type DesktopCatalogo struct {
	Supportato bool     `json:"supportato"`
	Codice     string   `json:"codice,omitempty"`
	InAttesa   string   `json:"in_attesa,omitempty"` // una decisione dell'utente ancora aperta
	Motivo     string   `json:"motivo,omitempty"`
	Componenti []string `json:"componenti,omitempty"`
	Depositi   []string `json:"depositi,omitempty"`
	Limiti     []string `json:"limiti,omitempty"`
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
		return nil, Errore("RX-TRUST-004", "formato "+c.Formato)
	}
	c.Digest = Sha256(b)
	return &c, nil
}

// Fiducia è l'esito della fase 0 TRUST.
type Fiducia struct {
	Catalogo            RifCatalogo `json:"catalogo"`
	Motore              RifMotore   `json:"motore"`
	FirmaVerificata     bool        `json:"firma_verificata"`
	ProcedutoSenzaFirma bool        `json:"proceduto_senza_firma"`
	Messaggi            []Messaggio `json:"messaggi"`
}

type RifCatalogo struct {
	Versione string `json:"versione"`
	Digest   string `json:"digest"`
	Scadenza string `json:"scadenza"`
}

type RifMotore struct {
	Versione string `json:"versione"`
	Digest   string `json:"digest"`
}

// DigestMotore: sha256 del binario che gira. ⚠ Sulla macchina stessa non vale contro root
// (§6.6.11): serve a dire, a posteriori, quale motore ha fatto l'operazione.
func DigestMotore() string {
	d, err := Sha256File("/proc/self/exe")
	if err != nil || d == "" {
		return "sconosciuto"
	}
	return d
}

// VerificaFiducia: fase 0 TRUST. Freschezza e versione minima si controllano davvero; la firma
// non esiste ancora (catena A, §6.6.10: modello scritto, custodia e chiavi con D11 e T8), e il
// motore lo DICE: senza --senza-firma si blocca, con --senza-firma procede e lo annota.
func VerificaFiducia(c *Catalogo, adesso time.Time, senzaFirma bool) (*Fiducia, error) {
	f := &Fiducia{
		Catalogo: RifCatalogo{c.Versione, c.Digest, c.Scadenza},
		Motore:   RifMotore{VersioneMotore, DigestMotore()},
	}
	scad, err := time.Parse("2006-01-02", c.Scadenza)
	if err != nil {
		return f, Errore("RX-TRUST-004", "scadenza "+c.Scadenza)
	}
	if adesso.After(scad.Add(24 * time.Hour)) {
		return f, Errore("RX-TRUST-002", "scaduto il "+c.Scadenza)
	}
	if ConfrontaVersioni(VersioneMotore, c.MotoreMinimo) < 0 {
		return f, Errore("RX-TRUST-003", "serve "+c.MotoreMinimo+", questo è "+VersioneMotore)
	}
	f.Messaggi = append(f.Messaggi, Msg("RX-TRUST-001", ""))
	if !senzaFirma {
		return f, Errore("RX-TRUST-005", "")
	}
	f.ProcedutoSenzaFirma = true
	return f, nil
}

// Condizione: una delle condizioni C-… di §6.6.8, col suo rimedio.
type Condizione struct {
	Codice    string `json:"codice"`
	Testo     string `json:"testo"`
	Rimedio   string `json:"rimedio,omitempty"`
	Decisione string `json:"decisione,omitempty"` // la decisione dell'utente che la riguarda, se aperta
	// Componente: per C-COMPONENTE, il pacchetto che l'installatore aggiunge (va nel piano)
	Componente string `json:"componente,omitempty"`
}

// Livelli di compatibilità (§6.6.8).
const (
	CERTIFICATA    = "CERTIFICATA"
	COMPATIBILE    = "COMPATIBILE"
	NON_SUPPORTATA = "NON_SUPPORTATA"
)

// EsitoDesktop: il livello per un desktop.
type EsitoDesktop struct {
	Desktop     string       `json:"desktop"`
	Nome        string       `json:"nome"`
	Installato  string       `json:"installato"` // versione, "assente" o "sconosciuto"
	Livello     string       `json:"livello"`
	Condizioni  []Condizione `json:"condizioni"`
	Motivi      []Messaggio  `json:"motivi,omitempty"` // perché NON_SUPPORTATA
	Note        []string     `json:"note,omitempty"`
	Riferimento bool         `json:"riferimento,omitempty"` // il desktop già scelto se se ne installa uno
}

// Rapporto di compatibilità: il secondo oggetto (§6.6.1).
type Rapporto struct {
	Formato      string      `json:"formato"`
	Oggetto      string      `json:"oggetto"` // "compatibilita"
	Creato       string      `json:"creato"`
	Catalogo     RifCatalogo `json:"catalogo"`
	Piattaforma  string      `json:"piattaforma"` // "Debian 13"
	pl           *Piattaforma
	cat          *Catalogo
	Riconosciuta string         `json:"riconosciuta"` // matrice · fuori matrice · derivata di … · esclusa · sconosciuta
	Desktop      []EsitoDesktop `json:"desktop"`
	SenzaDesktop bool           `json:"senza_desktop"`       // nessun desktop supportato installato (§10 e R38)
	Incognite    []string       `json:"incognite,omitempty"` // fatti SCONOSCIUTI che toccano il giudizio
	Messaggi     []Messaggio    `json:"messaggi"`
	Note         []string       `json:"note,omitempty"`
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
	r := &Rapporto{Formato: Formato, Oggetto: "compatibilita", Creato: ora(),
		Catalogo: RifCatalogo{c.Versione, c.Digest, c.Scadenza}}
	id, ver := p.V("distro.id"), p.V("distro.versione")
	fam := p.V("distro.famiglia")
	r.Piattaforma = strings.TrimSpace(p.V("distro.nome"))

	// motivi che valgono per ogni desktop
	var tutti []Messaggio
	for _, e := range c.Escluse {
		if e.ID == id && versioneCombacia(e.Versioni, ver) {
			tutti = append(tutti, Msg("RX-COMPAT-001", e.Motivo))
			r.Riconosciuta = T("comp.esclusa")
		}
	}
	if p.V("distro.immutabile") == "si" {
		tutti = append(tutti, Msg("RX-COMPAT-003", ""))
	}
	if c.Requisiti.Systemd && p.V("sistema.systemd") == "no" {
		tutti = append(tutti, Msg("RX-COMPAT-007", "la macchina non è partita con systemd"))
	}
	if v := p.V("openssl.versione"); v != "" && ConfrontaVersioni(v, c.Requisiti.OpensslMinima) < 0 {
		tutti = append(tutti, Msg("RX-COMPAT-007", "OpenSSL "+v+", serve "+c.Requisiti.OpensslMinima))
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
			tutti = append(tutti, Msg("RX-COMPAT-001", nome+": serve almeno la "+minima))
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

	condH264 := condizioniH264(c, pl, p, fam, r)
	nessuno := true
	for _, d := range DESKTOP {
		inst := p.V("desktop." + d)
		if f, ok := p.F("desktop." + d); ok && f.Stato == SCONOSCIUTO {
			inst = "sconosciuto"
			r.Incognite = append(r.Incognite, T("inc.desktop", NomeDesktop(d)))
		}
		e := EsitoDesktop{Desktop: d, Nome: NomeDesktop(d), Installato: inst, Condizioni: []Condizione{}}
		e.Motivi = append(e.Motivi, tutti...)
		if pl != nil {
			dc, ok := pl.Desktop[d]
			switch {
			case !ok:
				e.Motivi = append(e.Motivi, Msg("RX-COMPAT-005", ""))
			case !dc.Supportato && dc.InAttesa != "":
				e.Motivi = append(e.Motivi, Msg(nonVuoto(dc.Codice, "RX-COMPAT-004"), dc.Motivo+" (decisione "+dc.InAttesa+", aperta)"))
			case !dc.Supportato:
				e.Motivi = append(e.Motivi, Msg(nonVuoto(dc.Codice, "RX-COMPAT-005"), dc.Motivo))
			default:
				e.Condizioni = append(e.Condizioni, condH264...)
				for _, comp := range dc.Componenti {
					if p.V("pacchetto."+comp) == "assente" || p.V("pacchetto."+comp) == "" {
						e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-COMPONENTE",
							Testo:   T("cond.componente", comp),
							Rimedio: c.Installa[fam] + " " + comp, Componente: comp})
					}
				}
				car := c.CarattereScalabile[fam]
				if dc.ServeCarattere && (p.V("caratteri.scalabili") == "0" ||
					(p.V("caratteri.scalabili") == "" && p.V("pacchetto."+car) == "assente")) {
					e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-COMPONENTE",
						Testo:   T("cond.carattere"),
						Rimedio: c.Installa[fam] + " " + car, Componente: car})
				}
				for _, dep := range dc.Depositi {
					if p.V("deposito."+dep) != "presente" {
						dd := c.Depositi[dep]
						e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-DEPOSITO",
							Testo: T("cond.deposito_desktop", NomeDesktop(d), dd.Nome), Rimedio: dd.Comandi["rhel"], Decisione: dd.Decisione})
					}
				}
				for _, l := range dc.Limiti {
					e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-LIMITE", Testo: l})
				}
				e.Note = append(e.Note, dc.Note...)
				if min := c.Requisiti.minimaDesktop(d); min != "" && inst != "" && inst[0] >= '0' && inst[0] <= '9' &&
					ConfrontaVersioni(inst, min) < 0 {
					e.Motivi = append(e.Motivi, Msg("RX-COMPAT-006", NomeDesktop(d)+" "+inst+", serve "+min))
				}
			}
		}
		switch {
		case len(e.Motivi) > 0:
			e.Livello = NON_SUPPORTATA
			e.Condizioni = []Condizione{}
		case pl != nil && pl.Matrice && derivata == nil && pl.GiroIntero != "":
			e.Livello = CERTIFICATA
		default:
			e.Livello = COMPATIBILE
		}
		if e.Livello != NON_SUPPORTATA && inst != "" && inst != "assente" && inst != "sconosciuto" {
			nessuno = false
		}
		r.Desktop = append(r.Desktop, e)
	}

	// Senza un desktop supportato (§10, DECISIONI §10.7, R38): la domanda in più, col desktop di
	// riferimento già selezionato. La risposta NON la dà il motore qui: la dà chi installa.
	if nessuno {
		r.SenzaDesktop = true
		r.Messaggi = append(r.Messaggi, Msg("RX-DESKTOP-002", ""))
		rif := c.DesktopRiferimento[id]
		if rif == "" && pl != nil {
			rif = c.DesktopRiferimento[pl.ID]
		}
		for i := range r.Desktop {
			e := &r.Desktop[i]
			if e.Livello == NON_SUPPORTATA {
				continue
			}
			e.Riferimento = e.Desktop == rif
			e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-DESKTOP",
				Testo:   T("cond.desktop", NomeDesktop(e.Desktop)),
				Rimedio: T("cond.desktop_rimedio")})
		}
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

// condizioniH264: la codifica H.264, dalla piattaforma e da quel che la macchina ha mostrato.
// ⛔ UNKNOWN non è PASS: se la prova non si è potuta fare, niente condizione ma un'incognita
// dichiarata — non un «va tutto bene».
func condizioniH264(c *Catalogo, pl *Piattaforma, p *Profilo, fam string, r *Rapporto) []Condizione {
	var cc []Condizione
	h, _ := p.F("h264.scheda")
	if h.Stato == VERIFICATO && h.Valore == "si" {
		return cc
	}
	if pl != nil && !pl.H264.SchedaDiSerie && pl.H264.Deposito != "" && p.V("deposito."+pl.H264.Deposito) != "presente" {
		d := c.Depositi[pl.H264.Deposito]
		cc = append(cc, Condizione{Codice: "C-DEPOSITO",
			Testo:     T("cond.deposito_h264", d.Nome),
			Rimedio:   d.Comandi[pl.H264.Comando],
			Decisione: d.Decisione})
	}
	if p.V("scheda.nvidia_proprietaria") == "si" {
		cc = append(cc, Condizione{Codice: "C-HARDWARE", Testo: T("cond.nvidia")})
		cc = append(cc, Condizione{Codice: "C-RIPIEGO", Testo: T("cond.ripiego")})
		return cc
	}
	if pl != nil && pl.H264.AmdSenzaVaapi {
		for _, f := range p.Fatti {
			if strings.HasSuffix(f.Chiave, ".fornitore") && f.Valore == "AMD" {
				cc = append(cc, Condizione{Codice: "C-RIPIEGO", Testo: T("cond.ripiego_amd", pl.Nome)})
				return cc
			}
		}
	}
	switch {
	case p.V("scheda.nodi") == "nessuno":
		cc = append(cc, Condizione{Codice: "C-RIPIEGO", Testo: T("cond.ripiego_senza")})
	case h.Stato != SCONOSCIUTO && h.Valore == "no":
		cc = append(cc, Condizione{Codice: "C-RIPIEGO", Testo: T("cond.ripiego_no")})
	case h.Stato == SCONOSCIUTO:
		r.Incognite = append(r.Incognite, T("inc.h264", h.Nota))
	}
	return cc
}
