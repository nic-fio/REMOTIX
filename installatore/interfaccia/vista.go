package interfaccia

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"remotix/installatore/motore"
)

// La VISTA: gli oggetti del motore in parole comuni, per le cinque schermate e le varianti
// (fasi/17 §10). TUI e GUI disegnano questi valori e nient'altro: così dicono le stesse cose.

// Stato di una riga: il colore del cartellino.
type Stato int

const (
	OK Stato = iota
	CONSENSO
	SISTEMO
	DOPO
	MALE
	IGNOTO
)

// Cartellino: il testo del cartellino di uno stato.
func (s Stato) Cartellino() string {
	return [...]string{T("s.ok"), T("s.consenso"), T("s.sistemo"), T("s.dopo"), T("s.male"), T("s.nonsi")}[s]
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

// VistaControllo: la schermata 1.
type VistaControllo struct {
	Intestazione  string // «Fedora Linux 44 · Workstation · GNOME 50»
	Esito         EsitoControllo
	Banner, Sotto string
	Righe         []Riga
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

// Opzione: una risposta possibile.
type Opzione struct {
	Valore, Titolo, Nota, Testo string
	Verde                       bool // la nota è «consigliato» (verde)
}

// Domanda: una domanda della schermata delle scelte, con la voce del file di risposte che riempie.
type Domanda struct {
	Voce, Titolo, Spiega string
	Opzioni              []Opzione
	Griglia              bool // i desktop: due colonne
}

// VistaScelte: la schermata 2 (o la variante «nessun desktop»).
type VistaScelte struct {
	Titolo, Sotto string
	SenzaDesktop  bool
	PortaRiga     string // la riga sotto la porta (verde se il firewall non va toccato)
	PortaVerde    bool
	Domande       []Domanda
	Nota          string
}

// Passo: una riga del piano, con le azioni del motore che raccoglie.
type Passo struct {
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
	n := prof.V("distro.nome")
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
	return e.Installato != "" && e.Installato != "assente" && e.Installato != "sconosciuto"
}

// Intestazione: la riga in alto a destra.
func Intestazione(prof *motore.Profilo, rap *motore.Rapporto) string {
	if prof == nil {
		return ""
	}
	n := prof.V("distro.nome")
	if i := strings.Index(n, " ("); i > 0 {
		n = n[:i]
	}
	parti := []string{n}
	if v := prof.V("distro.variante"); v != "" {
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
		if motore.LinguaAttuale() == motore.IT {
			ds = append(ds, "nessun desktop")
		} else {
			ds = append(ds, "no desktop")
		}
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
	nodi := strings.Fields(prof.V("scheda.nodi"))
	if len(nodi) == 0 {
		return ""
	}
	f := strings.ToLower(prof.V("scheda." + nodi[0] + ".fornitore"))
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
	if possibili == 0 {
		v.Esito = BLOCCATA
		v.Bloccata = vistaNonSupportata(prof, rap)
		return v
	}

	var righe []Riga
	// sistema
	piatt := strings.TrimSpace(distro + " " + prof.V("distro.versione"))
	// il rapporto è scritto nella lingua di questa sessione (la stessa, passata con --lingua)
	if strings.HasPrefix(rap.Riconosciuta, strings.SplitN(motore.T("comp.nella_matrice", ""), " (", 2)[0]) {
		righe = append(righe, Riga{T("r.sistema"), T("t.sistema.ok", piatt), OK})
	} else {
		righe = append(righe, Riga{T("r.sistema"), T("t.sistema.fuori", piatt), DOPO})
	}
	// desktop
	var ds []string
	for _, e := range rap.Desktop {
		if installato(e) && e.Livello != motore.NON_SUPPORTATA {
			ds = append(ds, NomeDesktop(e.Desktop))
		}
	}
	condizioni := []string{}
	if len(ds) > 0 {
		righe = append(righe, Riga{T("r.desktop"), T("t.desktop.ok", strings.Join(ds, ", ")), OK})
	} else {
		righe = append(righe, Riga{T("r.desktop"), T("t.desktop.nessuno"), CONSENSO})
		condizioni = append(condizioni, T("c.cond.desktop"))
	}
	// scheda
	switch {
	case prof.V("scheda.nvidia_proprietaria") == "si":
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.nvidia"), DOPO})
	case nomeScheda(prof) == "":
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.nessuna"), DOPO})
	default:
		righe = append(righe, Riga{T("r.scheda"), T("t.scheda.ok", nomeScheda(prof)), OK})
	}
	// video
	video := false
	for _, x := range dom.Depositi {
		if x.Per == "h264" {
			video = true
		}
	}
	switch {
	case video:
		righe = append(righe, Riga{T("r.video"), T("t.video.deposito", distro), CONSENSO})
		condizioni = append(condizioni, T("c.cond.video", distro))
	default:
		righe = append(righe, Riga{T("r.video"), T("t.video.ok"), DOPO})
	}
	// accesso
	if m := haMessaggio(prof.Messaggi, "RX-PAM-001"); m != nil {
		righe = append(righe, Riga{T("r.accesso"), T("t.accesso.male"), MALE})
	} else {
		righe = append(righe, Riga{T("r.accesso"), T("t.accesso.ok"), OK})
	}
	// protezione
	switch {
	case prof.V("selinux") == "enforcing" || prof.V("selinux") == "permissive":
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.selinux"), OK})
	case prof.V("apparmor") != "" && prof.V("apparmor") != "assente" && prof.V("apparmor") != "no":
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.apparmor"), OK})
	default:
		righe = append(righe, Riga{T("r.protezione"), T("t.prot.no"), OK})
	}
	// firewall
	switch {
	case dom.Firewall == "aperto":
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.aperto"), OK})
	case dom.Firewall == "chiuso":
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.chiuso"), CONSENSO})
		condizioni = append(condizioni, T("c.cond.firewall"))
	case dom.Firewall == "nessuno":
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.nessuno"), OK})
	default:
		righe = append(righe, Riga{T("r.firewall"), T("t.fw.altro", strings.TrimPrefix(dom.Firewall, "altro:")), DOPO})
	}
	// porta
	p := dom.Porta
	if prof.V(fmt.Sprintf("porta.%d.tcp_libera", p)) == "no" || prof.V(fmt.Sprintf("porta.%d.udp_libera", p)) == "no" {
		righe = append(righe, Riga{T("r.porta"), T("t.porta.occupata", p), CONSENSO})
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

	switch len(condizioni) {
	case 0:
		v.Esito, v.Banner, v.Sotto = PRONTA, T("c.ok.titolo"), T("c.ok.testo")
	case 1:
		v.Esito, v.Banner, v.Sotto = CONDIZIONI, T("c.cond1.titolo"), condizioni[0]
	default:
		v.Esito, v.Banner, v.Sotto = CONDIZIONI, T("c.condN.titolo", len(condizioni)), strings.Join(condizioni, " ")
	}
	v.Dettagli = dettagliControllo(prof, rap, c.Fiducia)
	return v
}

func dettagliControllo(prof *motore.Profilo, rap *motore.Rapporto, fid *motore.Fiducia) string {
	var d []string
	d = append(d, prof.V("distro.nome"), rap.Riconosciuta)
	for _, e := range rap.Desktop {
		if installato(e) {
			d = append(d, e.Desktop+" "+e.Installato+" "+e.Livello)
		}
	}
	for _, n := range strings.Fields(prof.V("scheda.nodi")) {
		d = append(d, n+" "+prof.V("scheda."+n+".fornitore")+" "+prof.V("scheda."+n+".driver"))
	}
	for _, k := range []string{"codifica.strade", "h264.scheda", "h264.famiglia_driver", "codifica.vulkan", "pam.base", "selinux", "apparmor", "firewall.tipo", "firewall.zona"} {
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
		d = append(d, fmt.Sprintf("catalogo %s", rap.Catalogo.Versione), "motore "+motore.VersioneMotore)
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
		b.Perche = T("b.vecchia", strings.TrimSpace(distro+" "+prof.V("distro.versione")))
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

// ---- 2 · le scelte ---------------------------------------------------------------------------

// VistaDelleScelte: la schermata 2, dalle domande del motore.
func VistaDelleScelte(c *Controllo) *VistaScelte {
	prof, dom := c.Profilo, c.Domande
	distro := nomeDistro(prof)
	v := &VistaScelte{Sotto: T("sc.sotto")}
	switch {
	case dom.Firewall == "aperto":
		v.PortaRiga, v.PortaVerde = T("sc.fw.aperto"), true
	case dom.Firewall == "nessuno":
		v.PortaRiga, v.PortaVerde = T("sc.fw.nessuno"), true
	case strings.HasPrefix(dom.Firewall, "altro:"):
		v.PortaRiga = T("sc.fw.altro", strings.TrimPrefix(dom.Firewall, "altro:"))
	}
	if dom.Desktop != nil {
		v.SenzaDesktop = true
		v.Titolo, v.Sotto = T("nd.titolo"), T("nd.sotto", distro)
		d := Domanda{Voce: "desktop", Titolo: T("nd.quale"), Griglia: true}
		for _, o := range dom.Desktop.Opzioni {
			if o == "no" {
				continue
			}
			op := Opzione{Valore: o, Titolo: T("nd." + o), Testo: T("nd." + o + ".t")}
			if o == dom.Desktop.Predefinita {
				op.Nota, op.Verde = T("nd.rif", distro), true
			}
			d.Opzioni = append(d.Opzioni, op)
		}
		d.Opzioni = append(d.Opzioni, Opzione{Valore: "no", Titolo: T("nd.no"), Testo: T("nd.no.t")})
		v.Domande = append(v.Domande, d)
		v.Nota = T("nd.nota", distro)
	}
	for _, x := range dom.Depositi {
		if x.Per == "h264" {
			no := T("sc.video.no.t") // D5: senza, REMOTIX non si installa
			v.Domande = append(v.Domande, Domanda{Voce: "consenso.deposito." + x.ID, Titolo: T("sc.video.titolo"),
				Spiega: T("sc.video.spiega", distro, x.Nome, distro), Opzioni: []Opzione{
					{Valore: "si", Titolo: T("sc.video.si", x.Nome), Nota: T("sc.consigliato"), Verde: true, Testo: T("sc.video.si.t")},
					{Valore: "no", Titolo: T("sc.video.no"), Testo: no}}})
		} else {
			v.Domande = append(v.Domande, Domanda{Voce: "consenso.deposito." + x.ID, Titolo: T("sc.dep.titolo", x.Nome),
				Spiega: T("sc.dep.spiega", distro, x.Nome), Opzioni: []Opzione{
					{Valore: "si", Titolo: T("sc.dep.si", x.Nome), Nota: T("sc.consigliato"), Verde: true},
					{Valore: "no", Titolo: T("sc.dep.no"), Testo: T("sc.dep.no.t")}}})
		}
	}
	if dom.Firewall == "chiuso" {
		v.Domande = append(v.Domande, Domanda{Voce: "consenso.firewall", Titolo: T("sc.fw.titolo"), Spiega: T("sc.fw.spiega"),
			Opzioni: []Opzione{{Valore: "si", Titolo: T("sc.fw.si"), Nota: T("sc.consigliato"), Verde: true, Testo: T("sc.fw.si.t")},
				{Valore: "no", Titolo: T("sc.fw.no"), Testo: T("sc.fw.no.t")}}})
	}
	if v.Titolo == "" {
		n := 1 + len(v.Domande) // la porta, più le domande
		switch n {
		case 1:
			v.Titolo = T("sc.titolo.1")
		case 2:
			v.Titolo = T("sc.titolo.2")
		default:
			v.Titolo = T("sc.titolo.n", numero(n))
		}
	}
	return v
}

func numero(n int) string {
	it := []string{"", "Una", "Due", "Tre", "Quattro", "Cinque", "Sei"}
	en := []string{"", "One", "Two", "Three", "Four", "Five", "Six"}
	if n >= len(it) {
		return fmt.Sprint(n)
	}
	if motore.LinguaAttuale() == motore.IT {
		return it[n]
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
func VistaDelPiano(p *motore.Piano, prof *motore.Profilo, catDepositi map[string]string) *VistaPiano {
	v := &VistaPiano{}
	distro := "Linux"
	if prof != nil {
		distro = nomeDistro(prof)
	}
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
		case a.Tipo == "aggiungi-deposito" && a.ID == "archivio-remotix":
			metti(a.ID, func() Passo {
				return Passo{Titolo: T("a.archivio"), Sotto: T("a.archivio.t"), Fatto: T("a.archivio.f"), Breve: T("a.archivio.f")}
			}, a)
		case a.Tipo == "aggiungi-deposito":
			id := strings.TrimPrefix(a.ID, "deposito-")
			nome := id
			if n := catDepositi[id]; n != "" {
				nome = n
			}
			metti(a.ID, func() Passo {
				return Passo{Titolo: T("a.deposito", nome), Nota: T("a.acconsentito"), Sotto: T("a.deposito.t"), Fatto: T("a.deposito.f", nome), Breve: T("a.deposito.f", nome)}
			}, a)
		case a.Tipo == "installa-pacchetti" && a.ID == "codec":
			metti(a.ID, func() Passo {
				return Passo{Titolo: T("a.codec"), Sotto: T("a.codec.t", distro), Fatto: T("a.codec.f"), Breve: T("a.codec.f")}
			}, a)
		case a.Tipo == "installa-desktop":
			d := NomeDesktop(a.Parametri["desktop"])
			metti("desktop", func() Passo {
				return Passo{Titolo: T("a.desktop", d), Sotto: T("a.desktop.t", distro), Fatto: T("a.desktop.f", d), Breve: T("a.desktop.f", d)}
			}, a)
		case a.Tipo == "installa-pacchetti" && (a.ID == "componenti" || a.ID == "componenti-desktop"):
			metti("componenti", func() Passo {
				return Passo{Titolo: T("a.componenti"), Sotto: T("a.componenti.t"), Fatto: T("a.componenti.f"), Breve: T("a.componenti.f")}
			}, a)
		case a.Tipo == "installa-pacchetti":
			metti("pacchetti", func() Passo {
				return Passo{Titolo: T("a.pacchetti"), Sotto: T("a.pacchetti.t"), Fatto: T("a.pacchetti.f"), Breve: T("a.pacchetti.f")}
			}, a)
		case a.Tipo == "aggiungi-utente-a-gruppo":
			if u := a.Parametri["utente"]; !visti[u] {
				visti[u] = true
				utentiGruppi = append(utentiGruppi, u)
			}
			metti("gruppi", func() Passo { return Passo{} }, a)
		case a.Tipo == "attiva-cintura":
			metti("cinture", func() Passo {
				return Passo{Titolo: T("a.cinture"), Sotto: T("a.cinture.t"), Fatto: T("a.cinture.f"), Breve: T("a.cinture.f")}
			}, a)
		case a.Tipo == "regola-firewall":
			ps := a.Parametri["porta"]
			metti(a.ID, func() Passo {
				return Passo{Titolo: T("a.firewall", ps), Nota: T("a.acconsentito"), Sotto: T("a.firewall.t"), Fatto: T("a.firewall.f", ps), Breve: T("a.firewall.f", ps)}
			}, a)
		case a.Tipo == "accendi-servizio":
			porta = a.Parametri["porta"]
			metti(a.ID, func() Passo {
				return Passo{Titolo: T("a.servizio", porta), Sotto: T("a.servizio.t"), Fatto: T("a.servizio.f", porta), Breve: T("a.servizio.f", porta)}
			}, a)
		default:
			metti(a.ID, func() Passo {
				d := a.Descrizione
				if d != "" {
					d = strings.ToUpper(d[:1]) + d[1:]
				}
				return Passo{Titolo: d, Fatto: d, Breve: d}
			}, a)
		}
	}
	if i, ok := gruppo["gruppi"]; ok {
		chi := elenco(utentiGruppi)
		f := T("a.gruppi.f", chi)
		if len(utentiGruppi) > 1 {
			f = T("a.gruppi.fn", chi)
		}
		v.Passi[i].Titolo, v.Passi[i].Sotto, v.Passi[i].Fatto, v.Passi[i].Breve = T("a.gruppi", chi), T("a.gruppi.t"), f, f
	}
	// i dettagli: ogni azione del motore col suo tipo, il suo annullamento e l'impronta
	var d []string
	for _, a := range p.Azioni {
		d = append(d, a.ID+" ("+a.Tipo+", "+string(a.Reversibilita)+")")
	}
	d = append(d, "piano "+p.ID, "impronta "+short(p.Impronta.Digest), "digest "+short(p.Digest()))
	for _, m := range p.NonFatto {
		d = append(d, strings.TrimSpace(m.Codice+" "+m.Testo))
	}
	v.Dettagli = strings.Join(d, " · ")
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
		a.Righe = append(a.Righe, RigaAv{Testo: fmt.Sprintf("%d · %s", i+1, p.Breve)})
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
	case "stato":
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
	case "azione":
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
		case "INTENZIONE", "RIPRESA":
			if !a.Annulla {
				r.Stato = INCORSO
			}
		case "FATTA":
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
		case "FALLITA":
			r.Stato = FALLITA
		default: // ANNULLATA, e le fasi del ritorno indietro
			if a.Annulla {
				r.Stato = ANNULLATA
			}
		}
	case "messaggio":
		if ev.Messaggio != nil {
			riga = "   [" + ev.Messaggio.Codice + "] " + ev.Messaggio.Testo
		}
	case "oggetto":
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
}

// VistaDelPronto: dal certificato, dal piano (i passi fatti) e dall'esito.
func VistaDelPronto(es *Esito, vp *VistaPiano, porta int, depositoVideo string) *VistaPronto {
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
			case k.ID == "servizio":
				v.Prove = append(v.Prove, Riga{T("pr.k.servizio"), t, s})
			case k.ID == "codifica-h264":
				v.Prove = append(v.Prove, Riga{T("pr.k.h264"), t, s})
			case k.ID == "pam-risolta":
				v.Prove = append(v.Prove, Riga{T("pr.k.pam"), t, s})
			case k.ID == "porta-firewall":
				altre = append(altre, Riga{T("pr.k.porta"), t, s})
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
			v.Condizioni = append(v.Condizioni, CondizioneComune(k.Codice))
		}
		v.Dettagli = strings.Join([]string{es.Cartella + "/certificato.json", "catalogo " + c.Catalogo.Versione,
			"motore " + c.Motore.Versione, string(c.Stato)}, " · ")
		for _, k := range c.Condizioni {
			v.Dettagli += " · " + k.Codice + ": " + k.Testo
		}
	}
	v.Prove = append(v.Prove, Riga{T("pr.k.audio"), T("pr.primo"), DOPO})
	switch {
	case depositoVideo != "":
		v.Sotto = T("pr.sotto.dep", depositoVideo)
	case len(v.Condizioni) > 0:
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
		if m.Codice == "RX-DESKTOP-001" {
			b.Titolo = T("b.titolo.desktop")
		}
		if m.Codice == "RX-H264-006" {
			b.Titolo = T("b.titolo.video")
		}
		b.Perche, b.CheFare, b.Codice = m.Testo, m.Rimedio, m.Codice
		b.Dettagli = m.Dettaglio
	}
	if es.Cartella != "" {
		b.Dettagli = strings.TrimSpace(b.Dettagli + " · " + es.Cartella + " · " + string(es.Stato))
	}
	return b
}

// BloccoNelPiano: un «no» che ferma tutto già nel piano (D5: l'archivio della codifica), da dire
// subito invece di chiedere la conferma di un piano che il motore rifiuterà.
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

// DepositoVideo: il nome dell'archivio per H.264 a cui si è acconsentito, se c'è.
func DepositoVideo(dom *motore.Domande, voci map[string]string) string {
	for _, x := range dom.Depositi {
		if x.Per == "h264" && voci["consenso.deposito."+x.ID] == "si" {
			return x.Nome
		}
	}
	return ""
}

// NomiDepositi: id → nome, per il piano.
func NomiDepositi(dom *motore.Domande) map[string]string {
	r := map[string]string{}
	if dom == nil {
		return r
	}
	for _, x := range dom.Depositi {
		r[x.ID] = x.Nome
	}
	return r
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
