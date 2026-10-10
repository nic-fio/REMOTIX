package interfaccia

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"remotix/installatore/motore"
)

// La VISTA: gli oggetti del motore in parole comuni, per le cinque schermate e le varianti
// (fasi/17 §10). La TUI disegna questi valori e nient'altro.

// Stato di una riga: il colore del cartellino.
type Stato int

const (
	OK Stato = iota
	CONSENSO
	SISTEMO
	DOPO
	MALE
	IGNOTO
	AVVISO // non ferma: lo si dice (il firewall acceso, la porta occupata)
	MANCA  // ferma: REMOTIX non lo mette, lo dice (§10.36)
)

// Cartellino: il testo del cartellino di uno stato, nella colonna di destra del controllo.
func (s Stato) Cartellino() string {
	return [...]string{T("s.ok"), T("s.consenso"), T("s.sistemo"), T("s.dopo"), T("s.male"), T("s.nonsi"),
		T("s.avviso"), T("s.manca")}[s]
}

// Riga: una riga del controllo o delle prove.
type Riga struct {
	Etichetta, Testo string
	Stato            Stato
}

// Esito del controllo.
type EsitoControllo int

const (
	PRONTA EsitoControllo = iota
	CONDIZIONI
	BLOCCATA
)

// VistaControllo: la schermata 1. Con Esito == BLOCCATA e Righe piene è «manca qualcosa»: le righe
// col cartellino MANCA, e i codici; con Righe vuote è una fine (Bloccata: distribuzione fuori…).
type VistaControllo struct {
	Intestazione  string // «Fedora Linux 44 · Workstation · GNOME 50»
	Esito         EsitoControllo
	Banner, Sotto string
	Righe         []Riga
	Codici        []string // i codici RX di quel che manca
	Dettagli      string
	Bloccata      *VistaBloccata // se Esito == BLOCCATA
}

// VistaBloccata: una schermata che finisce (non supportata, fermata, annullata).
type VistaBloccata struct {
	Titolo, Sotto   string
	Perche, CheFare string
	Serve           string // «Serve almeno Debian 13.»
	Codice          string
	Dettagli        string
	Toccata         bool // la macchina è stata toccata (annullata): il cerchio non è rosso ma ambra
}

// VistaScelte: la schermata 2 — la porta.
type VistaScelte struct {
	Titolo, Sotto string
	PortaRiga     string // la riga sotto la porta (verde se non c'è un firewall acceso)
	PortaVerde    bool
}

// Passo: una riga del piano, con le azioni del motore che raccoglie.
type Passo struct {
	Tipo                string // "packages" · "groups" · "service" · "other"
	Titolo, Nota, Sotto string
	Fatto               string // come lo dice il benvenuto
	Rev                 Stato  // OK = si annulla del tutto · CONSENSO = in parte · MALE = non si annulla
	Azioni              []string
	Breve               string // come lo dice l'avanzamento
}

// Cartellino della reversibilità.
func (p Passo) Cartellino() string {
	switch p.Rev {
	case OK:
		return T("rev.tutto")
	case MALE:
		return T("rev.no")
	}
	return T("rev.parte")
}

// VistaPiano: la schermata 3.
type VistaPiano struct {
	Passi    []Passo
	Dettagli string
	// Pacchetti: che cosa farà il gestore (la sua simulazione), da mostrare prima del «sì»
	Pacchetti []motore.Artefatto
	// Utenti e Gruppi: chi il motore iscrive ai gruppi della scheda, e a quali
	Utenti, Gruppi []string
	// Porta: quella del servizio, come la dice il piano
	Porta string
	// Dipendenze: per i pacchetti che il desktop chiede a REMOTIX, per quale desktop
	Dipendenze map[string]string
}

// ---- 1 · il controllo ------------------------------------------------------------------------

func nomeDistro(prof *motore.Profilo) string {
	id := prof.V("distro.id")
	switch id {
	case "debian":
		return "Debian"
	case "ubuntu":
		return "Ubuntu"
	case "fedora":
		return "Fedora"
	case "almalinux":
		return "AlmaLinux"
	case "arch":
		return "Arch Linux"
	case "opensuse-tumbleweed", "opensuse-leap", "opensuse":
		return "openSUSE"
	}
	n := prof.V("distro.name")
	if i := strings.IndexAny(n, " ("); i > 0 {
		return n[:i]
	}
	if n == "" {
		return "Linux"
	}
	return n
}

var nomiDesktop = map[string]string{"gnome": "GNOME", "kde": "KDE Plasma", "xfce": "XFCE", "lxqt": "LXQt"}

// NomeDesktop: il nome da mostrare.
func NomeDesktop(d string) string {
	if n, ok := nomiDesktop[d]; ok {
		return n
	}
	return d
}

func installato(e motore.EsitoDesktop) bool {
	return e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown"
}

// Intestazione: la riga in alto a destra.
func Intestazione(prof *motore.Profilo, rap *motore.Rapporto) string {
	if prof == nil {
		return ""
	}
	n := prof.V("distro.name")
	if i := strings.Index(n, " ("); i > 0 {
		n = n[:i]
	}
	parti := []string{n}
	if v := prof.V("distro.variant"); v != "" {
		parti = append(parti, strings.ToUpper(v[:1])+v[1:])
	}
	var ds []string
	if rap != nil {
		for _, e := range rap.Desktop {
			if installato(e) {
				v := e.Installato
				if i := strings.Index(v, ":"); i > 0 { // l'epoca di Debian: «4:6.3.6-1»
					v = v[i+1:]
				}
				if i := strings.Index(v, "."); i > 0 {
					v = v[:i]
				}
				ds = append(ds, NomeDesktop(e.Desktop)+" "+v)
			}
		}
	}
	if len(ds) == 0 && rap != nil && rap.SenzaDesktop {
		ds = append(ds, "no desktop")
	}
	return strings.Join(append(parti, ds...), " · ")
}

func condizioneDi(rap *motore.Rapporto, codice string) bool {
	for _, e := range rap.Desktop {
		if e.Livello == motore.NON_SUPPORTATA || !installato(e) {
			continue
		}
		for _, k := range e.Condizioni {
			if k.Codice == codice {
				return true
			}
		}
	}
	return false
}

func haMessaggio(ms []motore.Messaggio, codice string) *motore.Messaggio {
	for i := range ms {
		if ms[i].Codice == codice {
			return &ms[i]
		}
	}
	return nil
}

// nomeScheda: la scheda in parole comuni (driver e bus stanno nei dettagli tecnici).
func nomeScheda(prof *motore.Profilo) string {
	nodi := strings.Fields(prof.V("gpu.nodes"))
	if len(nodi) == 0 {
		return ""
	}
	f := strings.ToLower(prof.V("gpu." + nodi[0] + ".vendor"))
	switch {
	case strings.Contains(f, "intel"):
		return T("t.scheda.marca", "Intel")
	case strings.Contains(f, "amd") || strings.Contains(f, "ati"):
		return T("t.scheda.marca", "AMD")
	case strings.Contains(f, "nvidia"):
		return T("t.scheda.marca", "NVIDIA")
	case strings.Contains(f, "virtio") || strings.Contains(f, "qxl") || strings.Contains(f, "vmware") || strings.Contains(f, "bochs"):
		return T("t.scheda.virtuale")
	}
	return T("t.scheda.generica")
}

// Controllo: la schermata 1 dagli oggetti del motore.
func VistaDelControllo(c *Controllo) *VistaControllo {
	v := &VistaControllo{}
	if c.Errore != nil || c.Profilo == nil || c.Rapporto == nil {
		m := c.Errore
		if m == nil {
			x := motore.Msg("RX-UI-005", "")
			m = &x
		}
		v.Esito = BLOCCATA
		v.Bloccata = &VistaBloccata{Titolo: T("b.titolo.fiducia"), Sotto: T("b.sotto.intatta"), Perche: m.Testo,
			CheFare: m.Rimedio, Codice: m.Codice, Dettagli: m.Dettaglio}
		return v
	}
	prof, rap, dom := c.Profilo, c.Rapporto, c.Domande
	v.Intestazione = Intestazione(prof, rap)
	distro := nomeDistro(prof)

	// bloccata: nessun desktop possibile (la distribuzione fuori, troppo vecchia, esclusa)
	possibili := 0
	for _, e := range rap.Desktop {
		if e.Livello != motore.NON_SUPPORTATA {
			possibili++
		}
	}
	// quel che manca (DECISIONI §10.36): REMOTIX non lo installa, lo dice; provvede l'amministratore.
	// La scheda che non codifica (RX-GPU-*) lascia senza desktop possibili, ma è anche lei «manca».
	mancano := append([]motore.Messaggio{}, rap.Mancano...)
	if possibili == 0 {
		g := motivoScheda(rap)
		if g == nil || rap.Minima != "" {
			v.Esito = BLOCCATA
			v.Bloccata = vistaNonSupportata(prof, rap)
			return v
		}
		mancano = append(mancano, *g)
	}

	var righe []Riga
	// sistema
	piatt := strings.TrimSpace(distro + " " + prof.V("distro.version"))
	if strings.HasPrefix(rap.Riconosciuta, strings.SplitN(motore.T("comp.nella_matrice", ""), " (", 2)[0]) {
		righe = append(righe, Riga{T("r.sistema"), T("t.sistema.ok", piatt), OK})
	} else {
		righe = append(righe, Riga{T("r.sistema"), T("t.sistema.fuori", piatt), DOPO})
	}
	// desktop
	var ds []string
	for _, e := range rap.Desktop {
		if installato(e) && (e.Livello != motore.NON_SUPPORTATA || possibili == 0) {
			ds = append(ds, NomeDesktop(e.Desktop))
		}
	}
	condizioni := []string{}
	if len(ds) > 0 {
		righe = append(righe, Riga{T("r.desktop"), T("t.desktop.ok", strings.Join(ds, ", ")), OK})
	}
	// scheda
	switch {
	case prof.V("gpu.nvidia_proprietary") == "yes":
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.nvidia"), DOPO})
	case nomeScheda(prof) == "":
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.nessuna"), DOPO})
	default:
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.ok", nomeScheda(prof)), OK})
	}
	// video: la prova vera è dopo l'installazione (7a)
	righe = append(righe, Riga{T("r.video"), T("t.video.ok"), DOPO})
	// accesso
	if m := haMessaggio(prof.Messaggi, "RX-PAM-001"); m != nil {
		righe = append(righe, Riga{T("r.accesso"), T("t.accesso.male"), MALE})
	} else {
		righe = append(righe, Riga{T("r.accesso"), T("t.accesso.ok"), OK})
	}
	if n := len(dom.Persone); n > 0 {
		righe = append(righe, Riga{T("r.persone"), T("t.persone", n), OK})
	}
	// protezione
	switch {
	case prof.V("selinux") == "enforcing" || prof.V("selinux") == "permissive":
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.selinux"), OK})
	case prof.V("apparmor") != "" && prof.V("apparmor") != "absent" && prof.V("apparmor") != "no":
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.apparmor"), OK})
	default:
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.no"), OK})
	}
	// firewall: aprirlo è dell'amministratore (§10.36)
	if dom.Firewall == "none" {
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.nessuno"), OK})
	} else {
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.admin", dom.Firewall, dom.Porta), AVVISO})
		condizioni = append(condizioni, T("c.cond.firewall", dom.Porta))
	}
	// porta
	p := dom.Porta
	if prof.V(fmt.Sprintf("port.%d.tcp_free", p)) == "no" || prof.V(fmt.Sprintf("port.%d.udp_free", p)) == "no" {
		righe = append(righe, Riga{T("r.porta"), T("t.porta.occupata", p), AVVISO})
		condizioni = append(condizioni, T("c.cond.porta", p))
	} else {
		righe = append(righe, Riga{T("r.porta"), T("t.porta.libera", p), OK})
	}
	// permessi
	switch n := len(dom.SenzaScheda); {
	case n == 0:
		righe = append(righe, Riga{T("r.permessi"), T("t.permessi.ok"), OK})
	case n == 1:
		righe = append(righe, Riga{T("r.permessi"), T("t.permessi.uno"), SISTEMO})
	default:
		righe = append(righe, Riga{T("r.permessi"), T("t.permessi.n", n), SISTEMO})
	}
	righe = append(righe, Riga{T("r.audio"), T("t.audio"), DOPO})
	v.Righe = righe
	v.Dettagli = dettagliControllo(prof, rap, c.Fiducia)

	if len(mancano) > 0 {
		for _, m := range mancano {
			v.Righe = conMancanza(v.Righe, m)
			v.Codici = append(v.Codici, m.Codice)
		}
		v.Esito = BLOCCATA
		v.Banner, v.Sotto = T("c.manca.titolo"), T("c.manca.testo")
		v.Bloccata = VistaMancano(mancano)
		return v
	}

	switch len(condizioni) {
	case 0:
		v.Esito, v.Banner, v.Sotto = PRONTA, T("c.ok.titolo"), ""
	case 1:
		v.Esito, v.Banner, v.Sotto = CONDIZIONI, T("c.cond1.titolo"), condizioni[0]
	default:
		v.Esito, v.Banner, v.Sotto = CONDIZIONI, T("c.condN.titolo", len(condizioni)), strings.Join(condizioni, " ")
	}
	return v
}

// motivoScheda: il motivo RX-GPU-* che lascia senza desktop possibili (la distribuzione va, manca la
// scheda o il driver che codifica).
func motivoScheda(rap *motore.Rapporto) *motore.Messaggio {
	for _, e := range rap.Desktop {
		for i := range e.Motivi {
			if strings.HasPrefix(e.Motivi[i].Codice, "RX-GPU-") {
				return &e.Motivi[i]
			}
		}
	}
	for i := range rap.Messaggi {
		if strings.HasPrefix(rap.Messaggi[i].Codice, "RX-GPU-") && rap.Messaggi[i].Gravita == motore.BLOCCANTE {
			return &rap.Messaggi[i]
		}
	}
	return nil
}

// etichettaMancanza: in quale riga del controllo va quel che manca.
func etichettaMancanza(codice string) string {
	switch {
	case strings.HasPrefix(codice, "RX-GPU-"):
		return T("r.scheda")
	case codice == "RX-MANCA-001":
		return T("r.desktop")
	case codice == "RX-MANCA-002":
		return T("r.archivio")
	case codice == "RX-MANCA-003":
		return T("r.pezzi")
	}
	return T("r.pacchetto")
}

// conMancanza: la riga di quel che manca prende il posto della riga con la stessa etichetta (la
// scheda «OK» diventa «manca»), o si aggiunge dopo il desktop.
func conMancanza(righe []Riga, m motore.Messaggio) []Riga {
	et := etichettaMancanza(m.Codice)
	t := T("m." + m.Codice)
	if strings.HasPrefix(t, "⟨") {
		t = strings.TrimPrefix(m.Testo, "Missing: ")
	}
	if m.Dettaglio != "" {
		t += ": " + m.Dettaglio
	}
	r := Riga{et, t, MANCA}
	for i := range righe {
		if righe[i].Etichetta == et {
			if righe[i].Stato == MANCA { // due mancanze nella stessa riga: una dopo l'altra
				return append(righe[:i+1], append([]Riga{{"", t, MANCA}}, righe[i+1:]...)...)
			}
			righe[i] = r
			return righe
		}
	}
	pos := 1
	if pos > len(righe) {
		pos = len(righe)
	}
	return append(righe[:pos], append([]Riga{r}, righe[pos:]...)...)
}

func dettagliControllo(prof *motore.Profilo, rap *motore.Rapporto, fid *motore.Fiducia) string {
	var d []string
	d = append(d, prof.V("distro.name"), rap.Riconosciuta)
	for _, e := range rap.Desktop {
		if installato(e) {
			d = append(d, e.Desktop+" "+e.Installato+" "+e.Livello)
		}
	}
	for _, n := range strings.Fields(prof.V("gpu.nodes")) {
		d = append(d, n+" "+prof.V("gpu."+n+".vendor")+" "+prof.V("gpu."+n+".driver"))
	}
	for _, k := range []string{"encoding.routes", "h264.gpu", "h264.driver_family", "encoding.vulkan", "pam.base", "selinux", "apparmor", "firewall.type", "firewall.zone"} {
		if x := prof.V(k); x != "" {
			d = append(d, k+"="+x)
		}
	}
	visti := map[string]bool{}
	for _, m := range append(append([]motore.Messaggio{}, prof.Messaggi...), rap.Messaggi...) {
		if !visti[m.Codice] {
			visti[m.Codice] = true
			d = append(d, m.Codice)
		}
	}
	for _, e := range rap.Desktop {
		if installato(e) {
			for _, k := range e.Condizioni {
				if !visti[k.Codice] {
					visti[k.Codice] = true
					d = append(d, k.Codice)
				}
			}
		}
	}
	if fid != nil {
		d = append(d, fmt.Sprintf("catalog %s", rap.Catalogo.Versione), "engine "+motore.VersioneMotore)
	}
	var r []string
	for _, x := range d {
		if strings.TrimSpace(x) != "" {
			r = append(r, x)
		}
	}
	return strings.Join(r, " · ")
}

func vistaNonSupportata(prof *motore.Profilo, rap *motore.Rapporto) *VistaBloccata {
	distro := nomeDistro(prof)
	b := &VistaBloccata{Sotto: T("b.sotto.intatta")}
	var motivo *motore.Messaggio
	for _, e := range rap.Desktop {
		if len(e.Motivi) > 0 {
			motivo = &e.Motivi[0]
			break
		}
	}
	if motivo == nil {
		for i := range rap.Messaggi {
			if rap.Messaggi[i].Gravita == motore.BLOCCANTE {
				motivo = &rap.Messaggi[i]
				break
			}
		}
	}
	if rap.Minima != "" {
		// una versione esclusa di una distribuzione che REMOTIX sostiene in una versione più nuova
		b.Titolo = T("b.titolo.versione", distro)
		b.Perche = T("b.vecchia", strings.TrimSpace(distro+" "+prof.V("distro.version")))
		b.Serve = T("b.serve", rap.Minima)
	} else {
		b.Titolo = T("b.titolo.distro")
		if motivo != nil {
			b.Perche = motivo.Testo
			if strings.HasPrefix(motivo.Codice, "RX-GPU-") {
				// fase 19: la distribuzione va, manca la scheda che codifica il video
				b.Titolo = T("b.titolo.scheda")
			}
		}
	}
	if motivo != nil {
		b.Codice = motivo.Codice
		b.Dettagli = strings.TrimSpace(motivo.Dettaglio + " " + motivo.Rimedio)
		if motivo.Rimedio != "" {
			b.CheFare = motivo.Rimedio + " " + T("b.rilancia")
		}
	}
	if rap.Minima != "" {
		b.CheFare = T("b.aggiorna", rap.Minima) + " " + T("b.versioni")
	}
	if b.CheFare == "" {
		b.CheFare = T("b.versioni")
	}
	b.Dettagli = strings.TrimSpace(rap.Piattaforma + " · " + rap.Riconosciuta + " · " + b.Dettagli)
	return b
}

// VistaMancano: la schermata «manca qualcosa» — che cosa, senza dire come metterlo (§10.36).
func VistaMancano(m []motore.Messaggio) *VistaBloccata {
	b := &VistaBloccata{Titolo: T("b.titolo.manca"), Sotto: T("b.sotto.intatta"), CheFare: T("b.manca.chefare")}
	var r, cod []string
	for _, x := range m {
		r = append(r, strings.TrimSpace(x.Testo+" "+x.Dettaglio))
		cod = append(cod, x.Codice)
	}
	b.Perche = "• " + strings.Join(r, "\n• ")
	b.Codice = strings.Join(cod, " ")
	return b
}

// ---- 2 · le scelte ---------------------------------------------------------------------------

// VistaDelleScelte: la schermata 2 — una domanda sola, la porta (§10.36: niente archivi, firewall o
// desktop da scegliere).
func VistaDelleScelte(c *Controllo) *VistaScelte {
	dom := c.Domande
	v := &VistaScelte{Titolo: T("sc.titolo.1"), Sotto: T("sc.sotto")}
	if dom.Firewall == "none" {
		v.PortaRiga, v.PortaVerde = T("sc.fw.nessuno"), true
	} else {
		v.PortaRiga = T("sc.fw.admin", dom.Firewall)
	}
	return v
}

func numero(n int) string {
	en := []string{"", "One", "Two", "Three", "Four", "Five", "Six"}
	if n >= len(en) {
		return fmt.Sprint(n)
	}
	return en[n]
}

// PortaValida: il numero scritto nella casella.
func PortaValida(s string) (int, bool) {
	p, err := strconv.Atoi(strings.TrimSpace(s))
	return p, err == nil && p >= 1 && p <= 65535
}

// ---- 3 · il piano ----------------------------------------------------------------------------

func peggiore(a Stato, r motore.Reversibilita) Stato {
	var b Stato
	switch r {
	case motore.ESATTA:
		b = OK
	case motore.IRREVERSIBILE:
		b = MALE
	default:
		b = CONSENSO
	}
	if b == MALE || a == MALE {
		return MALE
	}
	if b == CONSENSO || a == CONSENSO {
		return CONSENSO
	}
	return OK
}

func elenco(nomi []string) string {
	if len(nomi) <= 1 {
		return strings.Join(nomi, "")
	}
	return strings.Join(nomi[:len(nomi)-1], ", ") + T("a.e") + nomi[len(nomi)-1]
}

// VistaDelPiano: le azioni del piano raccolte in passi detti in parole comuni. L'ordine è quello
// del piano (il primo passo di ogni gruppo decide dove sta il gruppo).
func VistaDelPiano(p *motore.Piano) *VistaPiano {
	v := &VistaPiano{}
	gruppo := map[string]int{}
	var utentiGruppi []string
	visti := map[string]bool{}
	metti := func(chiave string, crea func() Passo, a motore.AzionePiano) {
		i, ok := gruppo[chiave]
		if !ok {
			v.Passi = append(v.Passi, crea())
			i = len(v.Passi) - 1
			gruppo[chiave] = i
			v.Passi[i].Rev = OK
		}
		v.Passi[i].Azioni = append(v.Passi[i].Azioni, a.ID)
		v.Passi[i].Rev = peggiore(v.Passi[i].Rev, a.Reversibilita)
	}
	porta := ""
	for _, a := range p.Azioni {
		switch {
		case a.Tipo == "install-packages":
			metti("packages", func() Passo {
				return Passo{Tipo: "packages", Titolo: T("a.pacchetti"), Sotto: T("a.pacchetti.t"), Fatto: T("a.pacchetti.f"), Breve: T("a.pacchetti.b")}
			}, a)
		case a.Tipo == "add-user-to-group":
			if u := a.Parametri["user"]; !visti[u] {
				visti[u] = true
				utentiGruppi = append(utentiGruppi, u)
			}
			if g := a.Parametri["group"]; !visti["group:"+g] {
				visti["group:"+g] = true
				v.Gruppi = append(v.Gruppi, g)
			}
			metti("gruppi", func() Passo { return Passo{Tipo: "groups"} }, a)
		case a.Tipo == "start-service":
			porta = a.Parametri["port"]
			metti(a.ID, func() Passo {
				return Passo{Tipo: "service", Titolo: T("a.servizio", porta), Sotto: T("a.servizio.t"), Fatto: T("a.servizio.f", porta), Breve: T("a.servizio.b")}
			}, a)
		default:
			metti(a.ID, func() Passo {
				d := a.Descrizione
				if d != "" {
					d = strings.ToUpper(d[:1]) + d[1:]
				}
				return Passo{Tipo: "other", Titolo: d, Fatto: d, Breve: d}
			}, a)
		}
	}
	if i, ok := gruppo["gruppi"]; ok {
		chi := elenco(utentiGruppi)
		f := T("a.gruppi.f", chi)
		if len(utentiGruppi) > 1 {
			f = T("a.gruppi.fn", chi)
		}
		v.Passi[i].Titolo, v.Passi[i].Sotto, v.Passi[i].Fatto = T("a.gruppi", chi), T("a.gruppi.t"), f
		v.Passi[i].Breve = T("a.gruppi.b", chi, strings.Join(v.Gruppi, ", "))
	}
	v.Utenti, v.Porta = utentiGruppi, porta
	// i dettagli: ogni azione del motore col suo tipo, il suo annullamento e l'impronta
	var d []string
	for _, a := range p.Azioni {
		d = append(d, a.ID+" ("+a.Tipo+", "+string(a.Reversibilita)+")")
	}
	d = append(d, "plan "+p.ID, "fingerprint "+short(p.Impronta.Digest), "digest "+short(p.Digest()))
	for _, m := range p.NonFatto {
		d = append(d, strings.TrimSpace(m.Codice+" "+m.Testo))
	}
	v.Dettagli = strings.Join(d, " · ")
	v.Pacchetti = p.Pacchetti
	v.Dipendenze = map[string]string{}
	for _, d := range p.Dipendenze {
		v.Dipendenze[d.Nome] = d.Perche
	}
	return v
}

func short(s string) string {
	if len(s) > 16 {
		return s[:16] + "…"
	}
	return s
}

// ---- 4 · l'avanzamento -----------------------------------------------------------------------

// StatoRiga dell'avanzamento.
type StatoRiga int

const (
	ATTESA StatoRiga = iota
	INCORSO
	FATTA
	FALLITA
	ANNULLATA
)

// RigaAv: una riga dell'avanzamento.
type RigaAv struct {
	Testo string
	Stato StatoRiga
}

// Avanzamento: lo stato della schermata 4, aggiornato dagli eventi del motore (§6.6.1).
type Avanzamento struct {
	Righe    []RigaAv
	passi    []Passo
	azione   map[string]int // id azione → indice del passo
	fatte    map[string]bool
	Stato    motore.Stato
	Registro []string
	Annulla  bool // si sta annullando
}

// NuovoAvanzamento: le righe dai passi del piano, più la fiducia, il piano e la verifica.
func NuovoAvanzamento(vp *VistaPiano) *Avanzamento {
	a := &Avanzamento{passi: vp.Passi, azione: map[string]int{}, fatte: map[string]bool{}}
	a.Righe = append(a.Righe, RigaAv{Testo: T("av.fiducia")}, RigaAv{Testo: T("av.piano")})
	for i, p := range vp.Passi {
		a.Righe = append(a.Righe, RigaAv{Testo: p.Breve})
		for _, id := range p.Azioni {
			a.azione[id] = i
		}
	}
	a.Righe = append(a.Righe, RigaAv{Testo: T("av.verifica")})
	return a
}

// Evento: un evento del motore.
func (a *Avanzamento) Evento(ev motore.EventoPubblico) {
	riga := ev.Evento
	switch ev.Evento {
	case "state":
		riga = "→ " + string(ev.A)
		if ev.Dettaglio != "" {
			riga += " — " + ev.Dettaglio
		}
		a.Stato = ev.A
		switch ev.A {
		case motore.NUOVA:
			a.Righe[0].Stato = INCORSO
		case motore.FIDATA:
			a.Righe[0].Stato = FATTA
			a.Righe[1].Stato = INCORSO
		case motore.PIANIFICATA:
			a.Righe[1].Stato = FATTA
		case motore.IN_ESECUZIONE:
			if len(a.Righe) > 3 && a.Righe[2].Stato == ATTESA {
				a.Righe[2].Stato = INCORSO
			}
		case motore.IN_VERIFICA:
			a.Righe[len(a.Righe)-1].Stato = INCORSO
		case motore.VERIFICATA, motore.CONFERMATA, motore.CONFERMATA_A_CONDIZIONI:
			a.Righe[len(a.Righe)-1].Stato = FATTA
		case motore.IN_ANNULLAMENTO:
			a.Annulla = true
			for i := range a.Righe {
				if a.Righe[i].Stato == INCORSO {
					a.Righe[i].Stato = FALLITA
				}
			}
		case motore.BLOCCATA, motore.RIFIUTATA:
			for i := range a.Righe {
				if a.Righe[i].Stato == INCORSO {
					a.Righe[i].Stato = FALLITA
				}
			}
		}
	case "action":
		riga = "   " + ev.Azione + ": " + ev.Fase
		if ev.Dettaglio != "" {
			riga += " (" + tronca(ev.Dettaglio, 160) + ")"
		}
		i, ok := a.azione[ev.Azione]
		if !ok {
			break
		}
		r := &a.Righe[i+2]
		switch ev.Fase {
		case "INTENT", "RESUMED":
			if !a.Annulla {
				r.Stato = INCORSO
			}
		case "DONE":
			a.fatte[ev.Azione] = true
			tutte := true
			for _, id := range a.passi[i].Azioni {
				tutte = tutte && a.fatte[id]
			}
			if tutte {
				r.Stato = FATTA
				// il passo dopo comincia adesso (la sua INTENZIONE arriva a scaricamento finito)
				if n := i + 3; n < len(a.Righe)-1 && a.Righe[n].Stato == ATTESA && !a.Annulla {
					a.Righe[n].Stato = INCORSO
				}
			}
		case "FAILED":
			r.Stato = FALLITA
		default: // ANNULLATA, e le fasi del ritorno indietro
			if a.Annulla {
				r.Stato = ANNULLATA
			}
		}
	case "message":
		if ev.Messaggio != nil {
			riga = "   [" + ev.Messaggio.Codice + "] " + ev.Messaggio.Testo
		}
	case "object":
		riga = "   " + ev.Oggetto + ": " + ev.Percorso
	}
	a.Registro = append(a.Registro, riga)
}

func tronca(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

// Punto: il passo in corso («Passo 4 di 7 · installo REMOTIX») e la percentuale.
func (a *Avanzamento) Punto() (string, int) {
	tot := len(a.Righe)
	fatte := 0
	cur := -1
	for i, r := range a.Righe {
		if r.Stato == FATTA || r.Stato == ANNULLATA {
			fatte++
		}
		if r.Stato == INCORSO && cur < 0 {
			cur = i
		}
	}
	pc := fatte * 100 / tot
	if a.Annulla {
		return T("av.annullamento"), pc
	}
	n := len(a.passi)
	switch {
	case cur < 0 && fatte == tot:
		return T("av.fine"), 100
	case cur < 2:
		return T("av.inizio"), pc
	case cur >= 2+n:
		return T("av.verifica"), pc
	}
	t := a.passi[cur-2].Breve
	return T("av.passo", cur-1, n, t), pc
}

// ---- 5 · pronto, e gli altri finali ----------------------------------------------------------

// VistaPronto: la schermata 5.
type VistaPronto struct {
	Sotto      string
	Router     string // D6: la porta da inoltrare sul router, TCP e UDP
	Indirizzo  string
	Impronta   string
	Cambiato   []string
	Prove      []Riga
	Dettagli   string
	Condizioni []string
	// DaFare: quel che resta all'amministratore (la porta che il firewall chiude, o che non si sa)
	DaFare []string
}

// VistaDelPronto: dal certificato, dal piano (i passi fatti) e dall'esito.
func VistaDelPronto(es *Esito, vp *VistaPiano, porta int) *VistaPronto {
	v := &VistaPronto{Sotto: T("pr.sotto")}
	ind := "[indirizzo]"
	if len(es.Indirizzi) > 0 {
		ind = es.Indirizzi[0]
	}
	v.Indirizzo = fmt.Sprintf("https://%s:%d/", ind, porta)
	v.Router = T("pr.router", porta, ind)
	v.Impronta = es.ImprontaTLS
	for _, p := range vp.Passi {
		v.Cambiato = append(v.Cambiato, p.Fatto)
	}
	c := es.Certificato
	if c != nil {
		passi, passiOK := 0, 0
		idPassi := map[string]bool{}
		for _, p := range vp.Passi {
			for _, id := range p.Azioni {
				idPassi[id] = true
			}
		}
		esito := func(e string) (string, Stato) {
			switch e {
			case "PASS":
				return T("pr.riuscita"), OK
			case "FAIL":
				return T("pr.fallita"), MALE
			}
			return T("pr.nonsi"), IGNOTO
		}
		var altre []Riga
		for _, k := range c.Controlli {
			if k.Esito == "N.A." {
				continue
			}
			t, s := esito(k.Esito)
			switch {
			case k.ID == "service":
				v.Prove = append(v.Prove, Riga{T("pr.k.servizio"), t, s})
			case k.ID == "h264-encoding":
				v.Prove = append(v.Prove, Riga{T("pr.k.h264"), t, s})
			case k.ID == "pam-resolved":
				v.Prove = append(v.Prove, Riga{T("pr.k.pam"), t, s})
			case k.ID == "firewall-port":
				altre = append(altre, Riga{T("pr.k.porta"), t, s})
				dove := k.Dettaglio
				if i := strings.Index(dove, ":"); i > 0 {
					dove = dove[:i]
				}
				switch k.Esito {
				case "FAIL":
					v.DaFare = append(v.DaFare, T("pr.todo.chiusa", porta, dove))
				case "PASS":
				default:
					v.DaFare = append(v.DaFare, T("pr.todo.ignota", porta, dove))
				}
			case idPassi[k.ID]:
				passi++
				if k.Esito == "PASS" {
					passiOK++
				}
			}
		}
		v.Prove = append(v.Prove, altre...)
		if passi > 0 {
			s := OK
			t := T("pr.riuscita")
			if passiOK < passi {
				s, t = MALE, T("pr.fallita")
			}
			v.Prove = append(v.Prove, Riga{T("pr.k.passi", passiOK, passi), t, s})
		}
		for _, k := range c.Condizioni {
			if k.Codice == "C-AMMINISTRATORE" { // la porta: sta in DaFare, detta per intero
				continue
			}
			v.Condizioni = append(v.Condizioni, CondizioneComune(k.Codice))
		}
		v.Dettagli = strings.Join([]string{es.Cartella + "/certificate.json", "catalog " + c.Catalogo.Versione,
			"engine " + c.Motore.Versione, string(c.Stato)}, " · ")
		for _, k := range c.Condizioni {
			v.Dettagli += " · " + k.Codice + ": " + k.Testo
		}
	}
	v.Prove = append(v.Prove, Riga{T("pr.k.audio"), T("pr.primo"), DOPO})
	if len(v.Condizioni) > 0 {
		v.Sotto = T("pr.sotto.cond", v.Condizioni[0])
	}
	return v
}

// CondizioneComune: una condizione del certificato in parole comuni (il testo del motore, tecnico,
// sta nei dettagli).
func CondizioneComune(codice string) string {
	if _, ok := testi["cond."+codice]; ok {
		return T("cond." + codice)
	}
	return T("cond.altra")
}

// VistaDellaFine: i finali che non sono «pronto» (BLOCCATA, RIFIUTATA, ANNULLATA…).
func VistaDellaFine(es *Esito, registro []string) *VistaBloccata {
	b := &VistaBloccata{}
	var m *motore.Messaggio
	if es.Errore != nil {
		m = es.Errore
	}
	// il messaggio più grave fra quelli visti nel registro, se l'esito non ne ha
	switch es.Stato {
	case motore.ANNULLATA:
		b.Titolo, b.Sotto, b.Toccata = T("b.titolo.annullata"), T("b.sotto.annullata"), true
	case motore.ANNULLATA_IN_PARTE:
		b.Titolo, b.Sotto, b.Toccata = T("b.titolo.parte"), T("b.sotto.parte"), true
	case motore.INTERROTTA:
		b.Titolo, b.Sotto, b.Toccata = T("b.titolo.interrotta"), T("b.sotto.interrotta"), true
	case motore.BLOCCATA, motore.RIFIUTATA, "":
		b.Titolo, b.Sotto = T("b.titolo.fermo"), T("b.sotto.intatta")
	default:
		b.Titolo, b.Sotto = T("b.titolo.interrotta"), T("b.sotto.interrotta")
	}
	if m == nil && es.Certificato != nil && len(es.Certificato.Resti) > 0 {
		b.Perche = strings.Join(es.Certificato.Resti, "; ")
	}
	if m != nil {
		if strings.HasPrefix(m.Codice, "RX-MANCA-") {
			b.Titolo = T("b.titolo.manca")
		}
		b.Perche, b.CheFare, b.Codice = m.Testo, m.Rimedio, m.Codice
		b.Dettagli = m.Dettaglio
	}
	if es.Cartella != "" {
		b.Dettagli = strings.TrimSpace(b.Dettagli + " · " + es.Cartella + " · " + string(es.Stato))
	}
	return b
}

// BloccoNelPiano: quel che manca, già nel piano (la simulazione del gestore che non risolve, per
// esempio), da dire subito invece di chiedere la conferma di un piano che il motore rifiuterà.
func BloccoNelPiano(p *motore.Piano) *motore.Messaggio {
	for i := range p.NonFatto {
		if p.NonFatto[i].Gravita == motore.BLOCCANTE {
			return &p.NonFatto[i]
		}
	}
	return nil
}

// UltimoMessaggio: il messaggio BLOCCANTE più recente fra gli eventi (per dire il perché).
func UltimoMessaggio(evs []motore.EventoPubblico) *motore.Messaggio {
	for i := len(evs) - 1; i >= 0; i-- {
		if m := evs[i].Messaggio; m != nil && m.Gravita == motore.BLOCCANTE {
			return m
		}
	}
	return nil
}

// Ordinate: le chiavi di una mappa, in ordine (per scrivere le voci sempre uguali).
func Ordinate(m map[string]string) []string {
	var k []string
	for x := range m {
		k = append(k, x)
	}
	sort.Strings(k)
	return k
}
