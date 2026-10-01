package motore

import (
	"encoding/json"
	"sort"
	"strings"
)

// FormatoCatalogo è la versione di formato del catalogo (diversa da quella degli oggetti: il
// catalogo viaggia nel pacchetto remotix-install, §6.6.8).
const FormatoCatalogo = "remotix-catalogo/1"

// Catalogo: le combinazioni e le loro regole (§3, §6.6.8).
type Catalogo struct {
	Formato            string                      `json:"formato"`
	Versione           string                      `json:"versione"`
	Sequenza           int                         `json:"sequenza"`
	Emesso             string                      `json:"emesso"`
	MotoreMinimo       string                      `json:"motore_minimo"`
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

type DepositoCatalogo struct {
	Nome      string            `json:"nome"`
	Decisione string            `json:"decisione"`
	Comandi   map[string]string `json:"comandi"`
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
	Depositi         []string                   `json:"depositi,omitempty"`
	Desktop          map[string]DesktopCatalogo `json:"desktop"`
	PacchettiDesktop map[string]string          `json:"pacchetti_desktop"` // desktop → pacchetti (virgole) per installarlo
	Note             []string                   `json:"note,omitempty"`
}

type Derivata struct {
	ID             string   `json:"id"`
	Nome           string   `json:"nome"`
	Versioni       []string `json:"versioni"`
	VersioneMinima string   `json:"versione_minima,omitempty"`
	Nota           string   `json:"nota,omitempty"`
}

// H264Piattaforma: la codifica video della piattaforma, SENZA ffmpeg (fase 18) e SOLO sulla scheda
// (fase 19: niente ripiego sul processore): libva e il driver VA della distribuzione, la strada
// «vaapi» di strade.go. ⭐ Il deposito di terzi serve
// ai DRIVER, e dipende dal fornitore della scheda (`[M]` 30 set, dai binari dei driver nelle
// immagini podman): Fedora toglie H.264 sia dal driver Intel (libva-intel-media-driver) sia da Mesa
// ⇒ RPM Fusion per entrambi (Intel: intel-media-driver, nel ramo NONFREE; AMD:
// mesa-va-drivers-freeworld); openSUSE toglie H.264 solo da Mesa ⇒ Packman solo per AMD; Alma su
// AMD non ha VA-API affatto.
type H264Piattaforma struct {
	SchedaDiSerie bool   `json:"scheda_di_serie"` // ogni scheda Intel/AMD codifica coi pacchetti ufficiali
	Deposito      string `json:"deposito,omitempty"`
	Comando       string `json:"comando,omitempty"`
	AmdSenzaVaapi bool   `json:"amd_senza_vaapi,omitempty"`
	// PacchettiScheda: fornitore (come in scheda.*.fornitore: Intel, AMD) → i driver da Deposito,
	// separati da virgola (dopo il consenso, D5). Un fornitore che non c'è codifica di serie, o non
	// codifica affatto (AmdSenzaVaapi).
	PacchettiScheda map[string]string `json:"pacchetti_scheda,omitempty"`
	// Nonfree: i fornitori il cui driver sta nel ramo «nonfree» del deposito (RPM Fusion: il driver
	// Intel completo)
	Nonfree []string `json:"nonfree,omitempty"`
}

// codificaPer: un fornitore di schede codifica H.264 via VA-API su questa piattaforma, coi pacchetti
// ufficiali o col driver che il catalogo prende dal deposito di terzi (D5). driverSenza: la macchina
// ha per lui solo un driver costruito senza H.264 (famigliaDriver). Solo Intel e AMD hanno la strada.
func (h H264Piattaforma) codificaPer(fornitore string, driverSenza bool) bool {
	switch {
	case fornitore != "Intel" && fornitore != "AMD":
		return false
	case fornitore == "AMD" && h.AmdSenzaVaapi:
		return false
	case driverSenza && !h.SchedaDiSerie:
		// il driver che c'è non codifica: serve quello del deposito, se il catalogo lo nomina
		return h.Deposito != "" && h.PacchettiScheda[fornitore] != ""
	}
	return true
}

// fornitoriScheda: i fornitori delle schede della macchina (scheda.<nodo>.fornitore); noti=false se
// il profilo non ne dice nessuno (allora si resta prudenti: come se servissero tutti).
func fornitoriScheda(p *Profilo) (map[string]bool, bool) {
	r := map[string]bool{}
	for _, f := range p.Fatti {
		if strings.HasPrefix(f.Chiave, "scheda.") && strings.HasSuffix(f.Chiave, ".fornitore") && f.Valore != "" {
			r[f.Valore] = true
		}
	}
	return r, len(r) > 0
}

// PerLaScheda: che cosa chiede la codifica sulla scheda SU QUESTA MACCHINA: il deposito di terzi (""
// se non serve), i driver da prendere lì e se serve il suo ramo nonfree. Senza schede non serve
// niente; con schede di fornitori che il catalogo non nomina (NVIDIA, virtio…) nemmeno.
func (h H264Piattaforma) PerLaScheda(p *Profilo) (deposito string, pacchetti []string, nonfree bool) {
	if h.Deposito == "" || h.SchedaDiSerie || p.V("scheda.nodi") == "nessuno" {
		return "", nil, false
	}
	forn, noti := fornitoriScheda(p)
	var nomi []string
	for f := range h.PacchettiScheda {
		if !noti || forn[f] {
			nomi = append(nomi, f)
		}
	}
	if !noti && len(h.PacchettiScheda) == 0 {
		return h.Deposito, nil, len(h.Nonfree) > 0
	}
	sort.Strings(nomi)
	visti := map[string]bool{}
	for _, f := range nomi {
		for _, x := range dividiVirgole(h.PacchettiScheda[f]) {
			if !visti[x] {
				visti[x] = true
				pacchetti = append(pacchetti, x)
			}
		}
		if contiene(h.Nonfree, f) {
			nonfree = true
		}
	}
	if len(pacchetti) == 0 {
		return "", nil, false
	}
	return h.Deposito, pacchetti, nonfree
}

// depositoPresente: il deposito c'è, acceso (e, se serve, col suo ramo nonfree).
func depositoPresente(p *Profilo, d string, nonfree bool) bool {
	return p.V("deposito."+d) == "presente" && (!nonfree || p.V("deposito."+d+"-nonfree") == "presente")
}

// DepositoScheda: il deposito di terzi che la scheda di QUESTA macchina chiede e che manca ("" se
// non ne chiede, o se c'è già).
func DepositoScheda(pl *Piattaforma, p *Profilo) string {
	if pl == nil {
		return ""
	}
	d, _, nf := pl.H264.PerLaScheda(p)
	if d == "" || depositoPresente(p, d, nf) {
		return ""
	}
	return d
}

// DepositiBaseMancanti: i depositi che servono a REMOTIX stesso (Piattaforma.Depositi) e mancano.
func DepositiBaseMancanti(pl *Piattaforma, p *Profilo) []string {
	if pl == nil {
		return nil
	}
	var r []string
	for _, d := range pl.Depositi {
		if p.V("deposito."+d) != "presente" {
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
	Depositi   []string `json:"depositi,omitempty"`
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
		return nil, Errore("RX-TRUST-004", "formato "+c.Formato)
	}
	c.Digest = Sha256(b)
	return &c, nil
}

type RifCatalogo struct {
	Versione string `json:"versione"`
	Digest   string `json:"digest"`
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
	// Minima: per una versione esclusa, la prima versione della stessa distribuzione che il
	// catalogo sostiene («serve almeno Debian 13»: la schermata «bloccata», T9)
	Minima string `json:"minima,omitempty"`
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
	r := &Rapporto{Formato: Formato, Oggetto: "compatibilita", Creato: ora(),
		Catalogo: RifCatalogo{c.Versione, c.Digest}}
	id, ver := p.V("distro.id"), p.V("distro.versione")
	fam := p.V("distro.famiglia")
	r.Piattaforma = strings.TrimSpace(p.V("distro.nome"))

	// motivi che valgono per ogni desktop
	var tutti []Messaggio
	for _, e := range c.Escluse {
		if e.ID == id && versioneCombacia(e.Versioni, ver) {
			tutti = append(tutti, Msg("RX-COMPAT-001", e.Motivo))
			r.Riconosciuta = T("comp.esclusa")
			r.Minima = c.primaVersione(id)
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

	// fase 19 (DECISIONI §10.27): niente codifica sul processore — senza una scheda che una strada
	// attiva sappia far codificare (strade.go), REMOTIX non si installa, su nessun desktop
	if cod, det := VerdettoScheda(pl, p); cod != "" {
		tutti = append(tutti, Msg(cod, det))
	}
	condH264 := condizioniH264(c, pl, p, fam, r)
	// i depositi che servono a REMOTIX stesso (su Alma EPEL, per RPM Fusion), su ogni desktop
	var condBase []Condizione
	for _, dep := range DepositiBaseMancanti(pl, p) {
		dd := c.Depositi[dep]
		condBase = append(condBase, Condizione{Codice: "C-DEPOSITO",
			Testo: T("cond.deposito_base", nonVuoto(dd.Nome, dep)), Rimedio: dd.Comandi[pl.H264.Comando], Decisione: dd.Decisione})
	}
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
				e.Condizioni = append(e.Condizioni, condBase...)
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
					if p.V("deposito."+dep) != "presente" && !contiene(pl.Depositi, dep) {
						dd := c.Depositi[dep]
						e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-DEPOSITO",
							Testo: T("cond.deposito_desktop", NomeDesktop(d), dd.Nome), Rimedio: dd.Comandi["rhel"], Decisione: dd.Decisione})
					}
				}
				for _, l := range dc.Limiti {
					e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-LIMITE", Testo: l})
				}
				if dc.Richiede3D != "" {
					if p.V("scheda.nodi") == "nessuno" {
						e.Motivi = append(e.Motivi, Msg("RX-COMPAT-007", T("mot.3d", NomeDesktop(d), dc.Richiede3D)))
					} else {
						e.Condizioni = append(e.Condizioni, Condizione{Codice: "C-HARDWARE", Testo: T("cond.3d", NomeDesktop(d), dc.Richiede3D)})
					}
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

// condizioniH264: la codifica H.264, dalla piattaforma e da quel che la macchina ha mostrato. Fase
// 19: niente ripiego — qui restano il deposito dei driver (D5) e le schede che non codificano.
// ⛔ UNKNOWN non è PASS: se la prova non si è potuta fare, niente condizione ma un'incognita
// dichiarata — non un «va tutto bene».
func condizioniH264(c *Catalogo, pl *Piattaforma, p *Profilo, fam string, r *Rapporto) []Condizione {
	var cc []Condizione
	h, _ := p.F("h264.scheda")
	if h.Stato == VERIFICATO && h.Valore == "si" {
		return cc
	}
	// il deposito dei driver, solo se la scheda di QUESTA macchina lo chiede (fase 18: Packman solo
	// per AMD; RPM Fusion per Intel e AMD, niente per NVIDIA o senza scheda)
	if dep := DepositoScheda(pl, p); dep != "" {
		d := c.Depositi[dep]
		cc = append(cc, Condizione{Codice: "C-DEPOSITO",
			Testo:     T("cond.deposito_h264", d.Nome),
			Rimedio:   d.Comandi[pl.H264.Comando],
			Decisione: d.Decisione})
	}
	// fase 19: una scheda che non codifica ACCANTO a una che sì (la macchina senza nessuna capace è
	// già fuori, VerdettoScheda): la si dice, e il video lo fa l'altra
	// ⭐ fase 19: con l'ICD Vulkan la NVIDIA proprietaria codifica (strada «vulkan») e non è più fuori
	if p.V("scheda.nvidia_proprietaria") == "si" && !SchedaSullaStrada("vulkan", "NVIDIA", pl, p) {
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
