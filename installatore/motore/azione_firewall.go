package motore

import (
	"encoding/json"
	"os"
	"sort"
	"strings"
)

// regola-firewall: la porta di REMOTIX aperta nel firewall acceso, TCP (la pagina) e UDP (QUIC).
// Il passo entra nel piano solo se chi fa il piano lo chiede, con una riga di consenso sua (D6).
// firewalld sul suo D-Bus (§10.14); ufw col suo programma (T6: ufw non ha un D-Bus); nftables
// riconosciuto e dichiarato non fatto (RX-FW-004).
// Si cambiano sia le regole vive sia quelle permanenti, e si annullano le sole che abbiamo messo.
//
// ⭐ T6 — la FORMA della regola, decisa alla fotografia e scritta nello stato di prima (così
//    l'annullamento toglie esattamente quel che si è messo):
//   - «servizio»: il servizio `remotix` che il pacchetto definisce (/usr/lib/firewalld/services,
//     il profilo di ufw), se il firewall lo CONOSCE già e la porta è la 7447;
//   - «porte»: 7447/tcp e 7447/udp. `[M]` 30 set, Alma 10 e Fedora 44: firewalld 2.4 NON vede un
//     servizio nuovo finché non si ricarica (`INVALID_SERVICE: remotix` subito dopo l'installazione,
//     anche nella configurazione permanente), e ricaricarlo butterebbe le regole vive degli altri
//     (podman, libvirt): il motore non ricarica, e alla prima installazione apre le porte.
// ⭐ T6 — il file della zona. Le regole permanenti si scrivono in UNA volta (update2 della zona): due
//    scritture fanno a firewalld il file `<zona>.xml.old`. All'annullamento, se la zona prima era
//    quella di serie (nessun file in /etc/firewalld/zones) e, tolte le nostre, le sue impostazioni
//    sono le stesse di prima, si rimette la zona di serie (loadDefaults): il file in /etc sparisce, e
//    non resta niente — il «resto public.xml» delle linee.
//
// parametri: porta ("7447"), protocolli ("tcp,udp"), servizio ("remotix", se la porta è quella
// del servizio), zona (vuota = la predefinita, letta alla fotografia e poi fissata).

func init() { registraTipo("regola-firewall", nuovaFirewall) }

// PortaDelServizio: la porta scritta nella definizione del servizio `remotix` (firewalld, ufw).
const PortaDelServizio = "7447"

// PianoFirewall prepara il passo del piano.
func PianoFirewall(id, porta string) AzionePiano {
	par := map[string]string{"porta": porta, "protocolli": "tcp,udp"}
	if porta == PortaDelServizio {
		par["servizio"] = "remotix"
	}
	return AzionePiano{
		ID: id, Tipo: "regola-firewall",
		Parametri:      par,
		Descrizione:    T("az.fw", porta),
		ComeSiFa:       T("az.fw.fa", porta),
		ComeSiVerifica: T("az.fw.verifica"),
		ComeSiAnnulla:  T("az.fw.annulla"),
		Reversibilita:  ESATTA,
		Consenso:       T("az.fw.consenso", porta),
	}
}

// firewallServizi: un firewall che sa dire se conosce un servizio (firewalld, ufw).
type firewallServizi interface {
	Conosce(servizio string) (bool, error)
}

// firewallPermanente: un firewall che scrive le regole permanenti in una volta sola e sa rimettere
// la zona di serie (firewalld).
type firewallPermanente interface {
	// StatoPermanente: l'impronta delle impostazioni permanenti della zona, tolte le regole
	// «senza»; e se la zona è quella di serie (nessun file suo in /etc).
	StatoPermanente(zona string, senza []string) (impronta string, diSerie bool, err error)
	AggiornaPermanente(zona string, aggiungi, togli []string) error
	RimettiDiSerie(zona string) error
}

type firewallAz struct {
	porta      string
	protocolli []string
	servizio   string
	zona       string
}

type primaFirewall struct {
	Origine  Origine         `json:"origine"`
	Gestore  string          `json:"gestore"`
	Zona     string          `json:"zona"`
	Presenti map[string]bool `json:"presenti"` // "7447/tcp vive" → c'era già
	// T6: "servizio" o "" (le porte); la zona di serie e l'impronta delle sue impostazioni permanenti
	Forma    string `json:"forma,omitempty"`
	DiSerie  bool   `json:"zona_di_serie,omitempty"`
	Impronta string `json:"impronta_permanente,omitempty"`
	// T6: <zona>.xml.old c'era già (se no, quello che loadDefaults lascia è nato da noi)
	CeraOld bool `json:"cera_old,omitempty"`
}

func nuovaFirewall(p AzionePiano) (Azione, error) {
	f := &firewallAz{porta: p.Parametri["porta"], zona: p.Parametri["zona"], servizio: p.Parametri["servizio"]}
	for _, x := range strings.Split(nonVuoto(p.Parametri["protocolli"], "tcp,udp"), ",") {
		f.protocolli = append(f.protocolli, strings.TrimSpace(x))
	}
	return f, nil
}

// regoleDi: le chiavi «regola vive|permanente» di una forma.
func (f *firewallAz) regoleDi(forma string) []string {
	var r []string
	if forma == "servizio" {
		r = []string{"servizio:" + f.servizio + " vive", "servizio:" + f.servizio + " permanente"}
	} else {
		for _, p := range f.protocolli {
			r = append(r, f.porta+"/"+p+" vive", f.porta+"/"+p+" permanente")
		}
	}
	sort.Strings(r)
	return r
}

// regole: le porte (la forma dei vincoli del piano: il servizio, prima dell'installazione, il
// firewall non lo conosce ancora).
func (f *firewallAz) regole() []string { return f.regoleDi("") }

func dividiRegola(k string) (string, bool) {
	porta, tipo, _ := strings.Cut(k, " ")
	return porta, tipo == "permanente"
}

func (f *firewallAz) leggiForma(c *Contesto, zona, forma string) (map[string]bool, error) {
	r := map[string]bool{}
	for _, k := range f.regoleDi(forma) {
		porta, perm := dividiRegola(k)
		ha, err := c.Amb.Firewall.HaPorta(zona, porta, perm)
		if err != nil {
			return nil, err
		}
		r[k] = ha
	}
	return r, nil
}

func (f *firewallAz) leggi(c *Contesto, zona string) (map[string]bool, error) {
	return f.leggiForma(c, zona, "")
}

func (f *firewallAz) zonaAdesso(c *Contesto) (string, error) {
	if f.zona != "" {
		return f.zona, nil
	}
	return c.Amb.Firewall.ZonaPredefinita()
}

// fileOld: la copia che firewalld fa del file di una zona prima di riscriverlo o toglierlo.
func fileOld(zona string) string { return "/etc/firewalld/zones/" + zona + ".xml.old" }

// ammesso: i firewall che il motore sa cambiare.
func ammesso(g string) bool { return g == "firewalld" || g == "ufw" }

func (f *firewallAz) Vincoli(c *Contesto) ([]string, error) {
	g := c.Amb.Firewall.Nome()
	if !ammesso(g) {
		return []string{"firewall=" + g}, nil
	}
	zona, err := f.zonaAdesso(c)
	if err != nil {
		return nil, err
	}
	r, err := f.leggi(c, zona)
	if err != nil {
		return nil, err
	}
	v := []string{"firewall=" + g + " zona=" + zona}
	for _, k := range f.regole() {
		v = append(v, "firewall:"+zona+":"+k+"="+siNo(r[k]))
	}
	return v, nil
}

// forma: il servizio se il firewall lo conosce già, le porte altrimenti.
func (f *firewallAz) forma(c *Contesto) (string, error) {
	fs, ok := c.Amb.Firewall.(firewallServizi)
	if f.servizio == "" || !ok {
		return "", nil
	}
	sa, err := fs.Conosce(f.servizio)
	if err != nil || !sa {
		return "", err
	}
	return "servizio", nil
}

func (f *firewallAz) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	g := c.Amb.Firewall.Nome()
	if !ammesso(g) {
		return nil, "", Errore("RX-FW-004", g)
	}
	zona, err := f.zonaAdesso(c)
	if err != nil {
		return nil, "", err
	}
	forma, err := f.forma(c)
	if err != nil {
		return nil, "", err
	}
	// la porta già aperta (anche in parte) resta nella sua forma: le porte, e le si completa
	if forma == "servizio" {
		rp, err := f.leggiForma(c, zona, "")
		if err != nil {
			return nil, "", err
		}
		for _, v := range rp {
			if v {
				forma = ""
			}
		}
	}
	r, err := f.leggiForma(c, zona, forma)
	if err != nil {
		return nil, "", err
	}
	p := primaFirewall{Origine: PREESISTENTE, Gestore: g, Zona: zona, Presenti: r, Forma: forma}
	for _, v := range r {
		if !v {
			p.Origine = DIRETTA
		}
	}
	if fp, ok := c.Amb.Firewall.(firewallPermanente); ok && p.Origine == DIRETTA {
		if p.Impronta, p.DiSerie, err = fp.StatoPermanente(zona, nil); err != nil {
			return nil, "", err
		}
		if _, err := os.Stat(c.Amb.P(fileOld(zona))); err == nil {
			p.CeraOld = true
		}
	}
	return jsonDi(p), p.Origine, nil
}

func leggiPrimaFw(prima json.RawMessage) (primaFirewall, error) {
	var p primaFirewall
	err := json.Unmarshal(prima, &p)
	return p, err
}

// nostre: le regole (senza « vive»/« permanente») di un livello che mancavano prima.
func (f *firewallAz) mancanti(p primaFirewall, adesso map[string]bool, permanente, cheCiSono bool) []string {
	var r []string
	for _, k := range f.regoleDi(p.Forma) {
		porta, perm := dividiRegola(k)
		if perm != permanente || p.Presenti[k] || adesso[k] != cheCiSono {
			continue
		}
		r = append(r, porta)
	}
	return r
}

func (f *firewallAz) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaFw(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	adesso, err := f.leggiForma(c, p.Zona, p.Forma)
	if err != nil {
		return err
	}
	for _, porta := range f.mancanti(p, adesso, false, false) {
		if err := c.Amb.Firewall.Aggiungi(p.Zona, porta, false); err != nil {
			return err
		}
	}
	perm := f.mancanti(p, adesso, true, false)
	if len(perm) == 0 {
		return nil
	}
	if fp, ok := c.Amb.Firewall.(firewallPermanente); ok {
		return fp.AggiornaPermanente(p.Zona, perm, nil)
	}
	for _, porta := range perm {
		if err := c.Amb.Firewall.Aggiungi(p.Zona, porta, true); err != nil {
			return err
		}
	}
	return nil
}

func (f *firewallAz) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	p, err := leggiPrimaFw(prima)
	if err != nil {
		return "", "", err
	}
	adesso, err := f.leggiForma(c, p.Zona, p.Forma)
	if err != nil {
		return "", "", err
	}
	tutte, comePrima, mancaUnaDiPrima := true, true, false
	for _, k := range f.regoleDi(p.Forma) {
		if !adesso[k] {
			tutte = false
		}
		if adesso[k] != p.Presenti[k] {
			comePrima = false
		}
		if p.Presenti[k] && !adesso[k] {
			mancaUnaDiPrima = true
		}
	}
	switch {
	case tutte:
		return COMPLETO, "tutte le regole ci sono", nil
	case mancaUnaDiPrima:
		return ESTRANEO, "manca una regola che c'era già prima", nil
	case comePrima:
		return ASSENTE, "com'era prima", nil
	}
	return A_META, "alcune regole sì, altre no", nil
}

func (f *firewallAz) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaFw(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	adesso, err := f.leggiForma(c, p.Zona, p.Forma)
	if err != nil {
		return err
	}
	// quella di prima non si tocca; quella che non c'è non si toglie
	for _, porta := range f.mancanti(p, adesso, false, true) {
		if err := c.Amb.Firewall.Togli(p.Zona, porta, false); err != nil {
			return err
		}
	}
	perm := f.mancanti(p, adesso, true, true)
	if len(perm) == 0 {
		return nil
	}
	fp, ok := c.Amb.Firewall.(firewallPermanente)
	if !ok {
		for _, porta := range perm {
			if err := c.Amb.Firewall.Togli(p.Zona, porta, true); err != nil {
				return err
			}
		}
		return nil
	}
	if p.DiSerie && p.Impronta != "" {
		imp, _, err := fp.StatoPermanente(p.Zona, perm)
		if err != nil {
			return err
		}
		if imp == p.Impronta {
			// tolte le nostre, la zona è quella di prima, che era quella di serie: il file in /etc
			// l'abbiamo fatto nascere noi, e se ne va
			if err := fp.RimettiDiSerie(p.Zona); err != nil {
				return err
			}
			// ⚠ `[M]` 30 set, alma10-gnome «cliente»: loadDefaults non cancella il file della zona, lo
			//   RINOMINA in <zona>.xml.old. Se prima non c'era, quel file è la zona con le NOSTRE
			//   regole: si toglie (solo se le contiene davvero).
			if !p.CeraOld {
				vecchio := c.Amb.P(fileOld(p.Zona))
				if b, err := os.ReadFile(vecchio); err == nil && (strings.Contains(string(b), `"`+f.porta+`"`) || (f.servizio != "" && strings.Contains(string(b), `"`+f.servizio+`"`))) {
					return os.Remove(vecchio)
				}
			}
			return nil
		}
	}
	return fp.AggiornaPermanente(p.Zona, nil, perm)
}

func (f *firewallAz) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := leggiPrimaFw(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "c'erano già: non si toccano", nil
	}
	adesso, err := f.leggiForma(c, p.Zona, p.Forma)
	if err != nil {
		return false, "", err
	}
	for _, k := range f.regoleDi(p.Forma) {
		if !p.Presenti[k] && adesso[k] {
			return false, "c'è ancora " + k, nil
		}
	}
	return true, "com'era prima", nil
}
