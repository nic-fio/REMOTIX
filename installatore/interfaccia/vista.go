package interfaccia

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"remotix/installatore/motore"
)

// The VIEW: the engine's objects in plain words, for the five screens and the variants
// (fasi/17 §10). The TUI draws these values and nothing else.

// Stato of a line: the colour of the label.
type Stato int

const (
	OK Stato = iota
	CONSENSO
	SISTEMO
	DOPO
	MALE
	IGNOTO
	AVVISO // does not stop: it is stated (the running firewall, the port in use)
	MANCA  // stops: REMOTIX does not provide it, it says so (§10.36)
)

// Cartellino: the label text of a state, in the right-hand column of the check.
func (s Stato) Cartellino() string {
	return [...]string{T("s.ok"), T("s.consenso"), T("s.sistemo"), T("s.dopo"), T("s.male"), T("s.nonsi"),
		T("s.avviso"), T("s.manca")}[s]
}

// Riga: a line of the check or of the tests.
type Riga struct {
	Etichetta, Testo string
	Stato            Stato
}

// Esito of the check.
type EsitoControllo int

const (
	PRONTA EsitoControllo = iota
	CONDIZIONI
	BLOCCATA
)

// VistaControllo: screen 1. With Esito == BLOCCATA and Righe filled it is «something is missing»: the lines
// with the MANCA label, and the codes; with Righe empty it is an ending (Bloccata: distribution out…).
type VistaControllo struct {
	Intestazione  string // «Fedora Linux 44 · Workstation · GNOME 50»
	Esito         EsitoControllo
	Banner, Sotto string
	Righe         []Riga
	Codici        []string // the RX codes of what is missing
	Dettagli      string
	Bloccata      *VistaBloccata // if Esito == BLOCCATA
}

// VistaBloccata: a screen that ends (not supported, stopped, cancelled).
type VistaBloccata struct {
	Titolo, Sotto   string
	Perche, CheFare string
	Serve           string // «At least Debian 13 is needed.»
	Codice          string
	Dettagli        string
	Toccata         bool // the machine was touched (cancelled): the circle is not red but amber
}

// VistaScelte: screen 2 — the port.
type VistaScelte struct {
	Titolo, Sotto string
	PortaRiga     string // the line under the port (green if there is no running firewall)
	PortaVerde    bool
}

// Passo: a line of the plan, with the engine actions it gathers.
type Passo struct {
	Tipo                string // "packages" · "groups" · "service" · "other"
	Titolo, Nota, Sotto string
	Fatto               string // how the welcome says it
	Rev                 Stato  // OK = fully undone · CONSENSO = partly · MALE = not undone
	Azioni              []string
	Breve               string // how the progress says it
}

// Cartellino of the reversibility.
func (p Passo) Cartellino() string {
	switch p.Rev {
	case OK:
		return T("rev.tutto")
	case MALE:
		return T("rev.no")
	}
	return T("rev.parte")
}

// VistaPiano: screen 3.
type VistaPiano struct {
	Passi    []Passo
	Dettagli string
	// Pacchetti: what the manager will do (its simulation), to show before the «yes»
	Pacchetti []motore.Artefatto
	// Utenti and Gruppi: whom the engine enrolls in the card's groups, and in which
	Utenti, Gruppi []string
	// Porta: the service's, as the plan says it
	Porta string
	// Dipendenze: for the packages the desktop requires of REMOTIX, for which desktop
	Dipendenze map[string]string
}

// ---- 1 · the check ---------------------------------------------------------------------------

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

// NomeDesktop: the name to display.
func NomeDesktop(d string) string {
	if n, ok := nomiDesktop[d]; ok {
		return n
	}
	return d
}

func installato(e motore.EsitoDesktop) bool {
	return e.Installato != "" && e.Installato != "absent" && e.Installato != "unknown"
}

// Intestazione: the line at the top right.
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
				if i := strings.Index(v, ":"); i > 0 { // Debian's epoch: «4:6.3.6-1»
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

// nomeScheda: the card in plain words (driver and bus are in the technical details).
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

// Controllo: screen 1 from the engine's objects.
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

	// blocked: no possible desktop (the distribution out, too old, excluded)
	possibili := 0
	for _, e := range rap.Desktop {
		if e.Livello != motore.NON_SUPPORTATA {
			possibili++
		}
	}
	// what is missing (DECISIONI §10.36): REMOTIX does not install it, it says so; the administrator provides it.
	// The card that does not encode (RX-GPU-*) leaves no possible desktops, but it too is «missing».
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
	// system
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
	// card
	switch {
	case prof.V("gpu.nvidia_proprietary") == "yes":
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.nvidia"), DOPO})
	case nomeScheda(prof) == "":
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.nessuna"), DOPO})
	default:
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.ok", nomeScheda(prof)), OK})
	}
	// video: the real test is after installation (7a)
	righe = append(righe, Riga{T("r.video"), T("t.video.ok"), DOPO})
	// sign-in
	if m := haMessaggio(prof.Messaggi, "RX-PAM-001"); m != nil {
		righe = append(righe, Riga{T("r.accesso"), T("t.accesso.male"), MALE})
	} else {
		righe = append(righe, Riga{T("r.accesso"), T("t.accesso.ok"), OK})
	}
	switch n := len(dom.Persone); {
	case n == 1:
		righe = append(righe, Riga{T("r.persone"), T("t.persone.una"), OK})
	case n > 1:
		righe = append(righe, Riga{T("r.persone"), T("t.persone", n), OK})
	}
	// protection
	switch {
	case prof.V("selinux") == "enforcing" || prof.V("selinux") == "permissive":
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.selinux"), OK})
	case prof.V("apparmor") != "" && prof.V("apparmor") != "absent" && prof.V("apparmor") != "no":
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.apparmor"), OK})
	default:
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.no"), OK})
	}
	// firewall: opening it is the administrator's job (§10.36)
	if dom.Firewall == "none" {
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.nessuno"), OK})
	} else {
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.admin", dom.Firewall, dom.Porta), AVVISO})
		condizioni = append(condizioni, T("c.cond.firewall", dom.Porta))
	}
	// port
	p := dom.Porta
	if prof.V(fmt.Sprintf("port.%d.tcp_free", p)) == "no" || prof.V(fmt.Sprintf("port.%d.udp_free", p)) == "no" {
		righe = append(righe, Riga{T("r.porta"), T("t.porta.occupata", p), AVVISO})
		condizioni = append(condizioni, T("c.cond.porta", p))
	} else {
		righe = append(righe, Riga{T("r.porta"), T("t.porta.libera", p), OK})
	}
	// permissions
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

// motivoScheda: the RX-GPU-* reason that leaves no possible desktops (the distribution works, the
// card or the driver that encodes is missing).
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

// etichettaMancanza: in which line of the check what is missing goes.
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

// conMancanza: the line of what is missing takes the place of the line with the same label (the
// «OK» card becomes «missing»), or is added after the desktop.
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
			if righe[i].Stato == MANCA { // two missing items in the same line: one after the other
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
		// an excluded version of a distribution that REMOTIX supports in a newer version
		b.Titolo = T("b.titolo.versione", distro)
		b.Perche = T("b.vecchia", strings.TrimSpace(distro+" "+prof.V("distro.version")))
		b.Serve = T("b.serve", rap.Minima)
	} else {
		b.Titolo = T("b.titolo.distro")
		if motivo != nil {
			b.Perche = motivo.Testo
			if strings.HasPrefix(motivo.Codice, "RX-GPU-") {
				// phase 19: the distribution works, the card that encodes the video is missing
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

// VistaMancano: the «something is missing» screen — what, without saying how to provide it (§10.36).
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

// ---- 2 · the choices -------------------------------------------------------------------------

// VistaDelleScelte: screen 2 — a single question, the port (§10.36: no repositories, firewalls or
// desktops to choose).
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

// PortaValida: the number written in the box.
func PortaValida(s string) (int, bool) {
	p, err := strconv.Atoi(strings.TrimSpace(s))
	return p, err == nil && p >= 1 && p <= 65535
}

// ---- 3 · the plan ----------------------------------------------------------------------------

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

// VistaDelPiano: the plan's actions gathered in steps told in plain words. The order is the
// plan's (the first step of each group decides where the group goes).
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
	// the details: every engine action with its type, its undo and the fingerprint
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

// ---- 4 · the progress ------------------------------------------------------------------------

// StatoRiga of the progress.
type StatoRiga int

const (
	ATTESA StatoRiga = iota
	INCORSO
	FATTA
	FALLITA
	ANNULLATA
)

// RigaAv: a line of the progress.
type RigaAv struct {
	Testo string
	Stato StatoRiga
}

// Avanzamento: the state of screen 4, updated by the engine's events (§6.6.1).
type Avanzamento struct {
	Righe    []RigaAv
	passi    []Passo
	azione   map[string]int // action id → step index
	fatte    map[string]bool
	Stato    motore.Stato
	Registro []string
	Annulla  bool // undoing in progress
}

// NuovoAvanzamento: the lines from the plan's steps, plus the trust, the plan and the verification.
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

// Evento: an engine event.
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
				// the next step starts now (its INTENTION arrives when downloading is over)
				if n := i + 3; n < len(a.Righe)-1 && a.Righe[n].Stato == ATTESA && !a.Annulla {
					a.Righe[n].Stato = INCORSO
				}
			}
		case "FAILED":
			r.Stato = FALLITA
		default: // ANNULLATA, and the rollback phases
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

// Punto: the step in progress («Step 4 of 7 · installing REMOTIX») and the percentage.
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

// ---- 5 · ready, and the other endings --------------------------------------------------------

// VistaPronto: screen 5.
type VistaPronto struct {
	Sotto      string
	Router     string // D6: the port to forward on the router, TCP and UDP
	Indirizzo  string
	Impronta   string
	Cambiato   []string
	Prove      []Riga
	Dettagli   string
	Condizioni []string
	// DaFare: what is left to the administrator (the port the firewall closes, or that is unknown)
	DaFare []string
}

// VistaDelPronto: from the certificate, from the plan (the steps done) and from the outcome.
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
			if k.Codice == "C-AMMINISTRATORE" { // the port: it goes in DaFare, stated in full
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

// CondizioneComune: a condition of the certificate in plain words (the engine's text, technical,
// is in the details).
func CondizioneComune(codice string) string {
	if _, ok := testi["cond."+codice]; ok {
		return T("cond." + codice)
	}
	return T("cond.altra")
}

// VistaDellaFine: the endings that are not «ready» (BLOCCATA, RIFIUTATA, ANNULLATA…).
func VistaDellaFine(es *Esito, registro []string) *VistaBloccata {
	b := &VistaBloccata{}
	var m *motore.Messaggio
	if es.Errore != nil {
		m = es.Errore
	}
	// the most serious message among those seen in the log, if the outcome has none
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

// BloccoNelPiano: what is missing, already in the plan (the manager's simulation that does not resolve, for
// example), to state at once instead of asking to confirm a plan the engine will refuse.
func BloccoNelPiano(p *motore.Piano) *motore.Messaggio {
	for i := range p.NonFatto {
		if p.NonFatto[i].Gravita == motore.BLOCCANTE {
			return &p.NonFatto[i]
		}
	}
	return nil
}

// UltimoMessaggio: the most recent BLOCKING message among the events (to say why).
func UltimoMessaggio(evs []motore.EventoPubblico) *motore.Messaggio {
	for i := len(evs) - 1; i >= 0; i-- {
		if m := evs[i].Messaggio; m != nil && m.Gravita == motore.BLOCCANTE {
			return m
		}
	}
	return nil
}

// Ordinate: the keys of a map, in order (to always write the entries the same way).
func Ordinate(m map[string]string) []string {
	var k []string
	for x := range m {
		k = append(k, x)
	}
	sort.Strings(k)
	return k
}
