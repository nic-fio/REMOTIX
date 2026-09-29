package motore

import (
	"encoding/json"
	"sort"
	"strings"
)

// regola-firewall: la porta di REMOTIX aperta nel firewall acceso, TCP (la pagina) e UDP (QUIC).
// Se aprirla o solo dirla è la decisione D6, aperta: il motore sa fare tutte e due le cose, e il
// passo entra nel piano solo se chi fa il piano lo chiede, con una riga di consenso sua.
// Oggi solo firewalld, sul suo D-Bus (§10.14); ufw e nftables sono riconosciuti e dichiarati non
// fatti (RX-FW-004).
// Si cambiano sia le regole vive sia quelle permanenti, e si annullano le sole che abbiamo messo.
//
// parametri: porta ("7447"), protocolli ("tcp,udp"), zona (vuota = la predefinita, letta alla
// fotografia e poi fissata nello stato di prima).

func init() { registraTipo("regola-firewall", nuovaFirewall) }

// PianoFirewall prepara il passo del piano.
func PianoFirewall(id, porta string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "regola-firewall",
		Parametri:      map[string]string{"porta": porta, "protocolli": "tcp,udp"},
		Descrizione:    T("az.fw", porta),
		ComeSiFa:       T("az.fw.fa", porta),
		ComeSiVerifica: T("az.fw.verifica"),
		ComeSiAnnulla:  T("az.fw.annulla"),
		Reversibilita:  ESATTA,
		Consenso:       T("az.fw.consenso", porta),
	}
}

type firewallAz struct {
	porta      string
	protocolli []string
	zona       string
}

type primaFirewall struct {
	Origine  Origine         `json:"origine"`
	Gestore  string          `json:"gestore"`
	Zona     string          `json:"zona"`
	Presenti map[string]bool `json:"presenti"` // "7447/tcp vive" → c'era già
}

func nuovaFirewall(p AzionePiano) (Azione, error) {
	f := &firewallAz{porta: p.Parametri["porta"], zona: p.Parametri["zona"]}
	for _, x := range strings.Split(nonVuoto(p.Parametri["protocolli"], "tcp,udp"), ",") {
		f.protocolli = append(f.protocolli, strings.TrimSpace(x))
	}
	return f, nil
}

// regole: le chiavi «porta/proto vive|permanente».
func (f *firewallAz) regole() []string {
	var r []string
	for _, p := range f.protocolli {
		r = append(r, f.porta+"/"+p+" vive", f.porta+"/"+p+" permanente")
	}
	sort.Strings(r)
	return r
}

func dividiRegola(k string) (string, bool) {
	porta, tipo, _ := strings.Cut(k, " ")
	return porta, tipo == "permanente"
}

func (f *firewallAz) leggi(c *Contesto, zona string) (map[string]bool, error) {
	r := map[string]bool{}
	for _, k := range f.regole() {
		porta, perm := dividiRegola(k)
		ha, err := c.Amb.Firewall.HaPorta(zona, porta, perm)
		if err != nil {
			return nil, err
		}
		r[k] = ha
	}
	return r, nil
}

func (f *firewallAz) zonaAdesso(c *Contesto) (string, error) {
	if f.zona != "" {
		return f.zona, nil
	}
	return c.Amb.Firewall.ZonaPredefinita()
}

func (f *firewallAz) Vincoli(c *Contesto) ([]string, error) {
	g := c.Amb.Firewall.Nome()
	if g != "firewalld" {
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
	v := []string{"firewall=firewalld zona=" + zona}
	for _, k := range f.regole() {
		v = append(v, "firewall:"+zona+":"+k+"="+siNo(r[k]))
	}
	return v, nil
}

func (f *firewallAz) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	if g := c.Amb.Firewall.Nome(); g != "firewalld" {
		return nil, "", Errore("RX-FW-004", g)
	}
	zona, err := f.zonaAdesso(c)
	if err != nil {
		return nil, "", err
	}
	r, err := f.leggi(c, zona)
	if err != nil {
		return nil, "", err
	}
	p := primaFirewall{Origine: PREESISTENTE, Gestore: "firewalld", Zona: zona, Presenti: r}
	for _, v := range r {
		if !v {
			p.Origine = DIRETTA
		}
	}
	return jsonDi(p), p.Origine, nil
}

func leggiPrimaFw(prima json.RawMessage) (primaFirewall, error) {
	var p primaFirewall
	err := json.Unmarshal(prima, &p)
	return p, err
}

func (f *firewallAz) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaFw(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	adesso, err := f.leggi(c, p.Zona)
	if err != nil {
		return err
	}
	for _, k := range f.regole() {
		if adesso[k] {
			continue
		}
		porta, perm := dividiRegola(k)
		if err := c.Amb.Firewall.Aggiungi(p.Zona, porta, perm); err != nil {
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
	adesso, err := f.leggi(c, p.Zona)
	if err != nil {
		return "", "", err
	}
	tutte, comePrima, mancaUnaDiPrima := true, true, false
	for _, k := range f.regole() {
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
	adesso, err := f.leggi(c, p.Zona)
	if err != nil {
		return err
	}
	for _, k := range f.regole() {
		if p.Presenti[k] || !adesso[k] {
			continue // quella di prima non si tocca; quella che non c'è non si toglie
		}
		porta, perm := dividiRegola(k)
		if err := c.Amb.Firewall.Togli(p.Zona, porta, perm); err != nil {
			return err
		}
	}
	return nil
}

func (f *firewallAz) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := leggiPrimaFw(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "c'erano già: non si toccano", nil
	}
	adesso, err := f.leggi(c, p.Zona)
	if err != nil {
		return false, "", err
	}
	for _, k := range f.regole() {
		if !p.Presenti[k] && adesso[k] {
			return false, "c'è ancora " + k, nil
		}
	}
	return true, "com'era prima", nil
}
