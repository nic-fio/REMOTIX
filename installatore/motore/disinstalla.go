package motore

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// La DISINSTALLAZIONE (§6.0, terzo mestiere; §6.5 punto 3; R6): un'operazione come le altre, col
// suo piano, il suo consenso, il suo registro e la sua ripresa, che ripercorre ALL'INDIETRO il
// registro dell'installazione confermata (installazione.json). Ogni passo di allora con origine
// DIRETTA diventa un passo «disfa»: fare = il suo annulla, annullare = il suo fai (se la
// disinstallazione fallisce a metà, si torna all'installazione di prima). PREESISTENTE non si
// tocca mai; le INDIRETTE si dichiarano. Subito dopo lo spegnimento del servizio si chiudono le
// sessioni REMOTIX ancora aperte (chiudi-sessioni, §6.5-bis). A disinstallazione CONFERMATA
// installazione.json si toglie; il registro delle operazioni resta (è la storia della macchina,
// come quella di dnf).

func init() {
	registraTipo("disfa", nuovaDisfa)
	registraTipo("togli-iscrizione", nuovaIscrizione)
}

// FileIscrizioni: dove REMOTIX annota chi ha iscritto ai gruppi alla prima connessione (figlio.c,
// §6.5-bis): origine DIRETTA, la disinstallazione le toglie come quelle del motore.
const FileIscrizioni = "gruppi-iscritti.jsonl"

// Iscrizioni: le coppie (utente, gruppo) del file, senza doppioni.
func (m *Motore) Iscrizioni() [][2]string {
	b, err := os.ReadFile(filepath.Join(filepath.Dir(m.Cartella), FileIscrizioni))
	if err != nil {
		return nil
	}
	var r [][2]string
	visti := map[[2]string]bool{}
	for _, riga := range strings.Split(string(b), "\n") {
		var x struct {
			Formato, Utente, Gruppo, Origine string
		}
		if json.Unmarshal([]byte(riga), &x) != nil || x.Formato != "remotix-gruppi/1" || x.Utente == "" || x.Gruppo == "" {
			continue
		}
		k := [2]string{x.Utente, x.Gruppo}
		if !visti[k] {
			visti[k] = true
			r = append(r, k)
		}
	}
	return r
}

// togli-iscrizione: l'inverso di aggiungi-utente-a-gruppo, per le iscrizioni fatte da REMOTIX.
type iscrizione struct{ g *gruppo }

func nuovaIscrizione(p AzionePiano) (Azione, error) {
	return &iscrizione{&gruppo{p.Parametri["utente"], p.Parametri["gruppo"]}}, nil
}

type primaIscrizione struct {
	Origine Origine `json:"origine"`
}

func (i *iscrizione) Vincoli(c *Contesto) ([]string, error) { return i.g.Vincoli(c) }
func (i *iscrizione) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	esp, _, _, err := i.g.membro(c)
	if err != nil {
		if CodiceDi(err) == "RX-GRUPPI-003" || CodiceDi(err) == "RX-GRUPPI-002" {
			return jsonDi(primaIscrizione{PREESISTENTE}), PREESISTENTE, nil // l'utente o il gruppo non c'è più
		}
		return nil, "", err
	}
	if !esp {
		return jsonDi(primaIscrizione{PREESISTENTE}), PREESISTENTE, nil
	}
	return jsonDi(primaIscrizione{DIRETTA}), DIRETTA, nil
}
func (i *iscrizione) origine(prima json.RawMessage) Origine {
	var p primaIscrizione
	json.Unmarshal(prima, &p)
	return p.Origine
}
func (i *iscrizione) Fai(c *Contesto, prima json.RawMessage) error {
	if i.origine(prima) == PREESISTENTE {
		return nil
	}
	if esp, _, _, err := i.g.membro(c); err != nil || !esp {
		return err
	}
	return c.Amb.Gruppi.Togli(i.g.utente, i.g.gruppo)
}
func (i *iscrizione) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	if i.origine(prima) == PREESISTENTE {
		return COMPLETO, "niente da togliere", nil
	}
	esp, _, _, err := i.g.membro(c)
	if err != nil {
		return "", "", err
	}
	if esp {
		return ASSENTE, i.g.utente + " è ancora in " + i.g.gruppo, nil
	}
	return COMPLETO, i.g.utente + " non è più in " + i.g.gruppo, nil
}
func (i *iscrizione) Annulla(c *Contesto, prima json.RawMessage) error {
	if i.origine(prima) == PREESISTENTE {
		return nil
	}
	if esp, _, _, err := i.g.membro(c); err != nil || esp {
		return err
	}
	return c.Amb.Gruppi.Aggiungi(i.g.utente, i.g.gruppo)
}
func (i *iscrizione) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	if i.origine(prima) == PREESISTENTE {
		return true, "niente da rimettere", nil
	}
	esp, _, _, err := i.g.membro(c)
	return esp, "", err
}

// PulisciStoria, a disinstallazione CONFERMATA (decisione del coordinatore, 30 set): senza purge la
// storia del motore resta (per l'assistenza) ma senza i pacchetti in cache; con purge si toglie
// tutta, e anche /var/lib/remotix se resta vuota.
func (m *Motore) PulisciStoria(purge bool) error {
	if purge {
		if err := os.RemoveAll(m.Cartella); err != nil {
			return err
		}
		os.Remove(filepath.Join(filepath.Dir(m.Cartella), FileIscrizioni)) // già disfatte dal piano
		// T8: il catalogo memorizzato, le versioni aggiornate, i piani degli aggiornamenti
		os.RemoveAll(filepath.Join(filepath.Dir(m.Cartella), "fiducia"))
		os.RemoveAll(filepath.Join(filepath.Dir(m.Cartella), "aggiornamenti"))
		os.Remove(filepath.Join(filepath.Dir(m.Cartella), "aggiornamenti.json"))
		os.Remove(filepath.Join(filepath.Dir(m.Cartella), "aggiornamenti-sospesi.json"))
		os.Remove(filepath.Dir(m.Cartella)) // solo se vuota
		return nil
	}
	voci, _ := filepath.Glob(filepath.Join(m.Cartella, "*", "cache"))
	for _, v := range voci {
		if err := os.RemoveAll(v); err != nil {
			return err
		}
	}
	return nil
}

// LeggiRegistro legge un registro senza aprirlo in scrittura.
func LeggiRegistro(percorso string) ([]Evento, error) {
	f, err := os.Open(percorso)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var r []Evento
	s := bufio.NewScanner(f)
	s.Buffer(make([]byte, 1<<20), 64<<20)
	for s.Scan() {
		var e Evento
		if json.Unmarshal(s.Bytes(), &e) == nil {
			r = append(r, e)
		}
	}
	return r, s.Err()
}

type disfa struct {
	op, azione string
	purge      bool
}

func nuovaDisfa(p AzionePiano) (Azione, error) {
	return &disfa{op: p.Parametri["operazione"], azione: p.Parametri["azione"], purge: p.Parametri["purge"] == "si"}, nil
}

type primaDisfa struct {
	Origine   Origine         `json:"origine"`
	PrimaOrig json.RawMessage `json:"prima_originale"`
}

// originale: l'azione di allora, il suo contesto (la cartella dell'operazione di allora, coi
// salvataggi e la cache) e lo stato di prima di allora.
func (d *disfa) originale(c *Contesto) (Azione, *Contesto, *Evento, error) {
	dir := filepath.Join(filepath.Dir(c.Cartella), d.op)
	var pn Piano
	if err := LeggiJSON(filepath.Join(dir, "piano.json"), &pn); err != nil {
		return nil, nil, nil, err
	}
	var ap *AzionePiano
	for i := range pn.Azioni {
		if pn.Azioni[i].ID == d.azione {
			ap = &pn.Azioni[i]
		}
	}
	if ap == nil {
		return nil, nil, nil, fmt.Errorf("disfa: %s non è nel piano di %s", d.azione, d.op)
	}
	ev, err := LeggiRegistro(filepath.Join(dir, "registro.jsonl"))
	if err != nil {
		return nil, nil, nil, err
	}
	var intz *Evento
	for i := range ev {
		if ev[i].Azione == d.azione && ev[i].Tipo == EvIntenzione {
			intz = &ev[i]
			break
		}
	}
	a, err := NuovaAzione(*ap)
	if err != nil {
		return nil, nil, nil, err
	}
	return a, &Contesto{Amb: c.Amb, Cartella: dir, P: *ap, Purge: d.purge}, intz, nil
}

func (d *disfa) Vincoli(c *Contesto) ([]string, error) {
	a, cc, _, err := d.originale(c)
	if err != nil {
		return nil, err
	}
	return a.Vincoli(cc)
}

func (d *disfa) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	_, _, intz, err := d.originale(c)
	if err != nil {
		return nil, "", err
	}
	if intz == nil || intz.Origine == PREESISTENTE {
		return jsonDi(primaDisfa{Origine: PREESISTENTE}), PREESISTENTE, nil
	}
	return jsonDi(primaDisfa{Origine: DIRETTA, PrimaOrig: intz.Prima}), DIRETTA, nil
}

func (d *disfa) leggi(c *Contesto, prima json.RawMessage) (Azione, *Contesto, primaDisfa, error) {
	var p primaDisfa
	if err := json.Unmarshal(prima, &p); err != nil {
		return nil, nil, p, err
	}
	a, cc, _, err := d.originale(c)
	return a, cc, p, err
}

func (d *disfa) Fai(c *Contesto, prima json.RawMessage) error {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	return a.Annulla(cc, p.PrimaOrig)
}

func (d *disfa) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREESISTENTE {
		return COMPLETO, "niente da disfare", nil
	}
	if ok, det, err := a.Annullata(cc, p.PrimaOrig); err != nil {
		return "", "", err
	} else if ok {
		return COMPLETO, "disfatto: " + det, nil
	}
	e, det, err := a.Controlla(cc, p.PrimaOrig)
	if err != nil {
		return "", "", err
	}
	switch e {
	case COMPLETO:
		return ASSENTE, "ancora come l'aveva messo l'installazione", nil
	case ESTRANEO:
		return ESTRANEO, det, nil
	}
	return A_META, det, nil
}

func (d *disfa) Ripara(c *Contesto, prima json.RawMessage) error {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil {
		return err
	}
	if r, ok := a.(Riparabile); ok {
		return r.Ripara(cc, p.PrimaOrig)
	}
	return nil
}

// Annulla (una disinstallazione che fallisce a metà): si rifà quel che c'era.
func (d *disfa) Annulla(c *Contesto, prima json.RawMessage) error {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	return a.Fai(cc, p.PrimaOrig)
}

func (d *disfa) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	a, cc, p, err := d.leggi(c, prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "niente da rifare", nil
	}
	e, det, err := a.Controlla(cc, p.PrimaOrig)
	return e == COMPLETO, det, err
}

func (d *disfa) Indirette(prima json.RawMessage) []string {
	var p primaDisfa
	if json.Unmarshal(prima, &p) != nil || p.Origine == PREESISTENTE {
		return nil
	}
	return nil // le indirette dell'installazione restano dichiarate nel suo certificato, ripreso sotto
}

// PianoDisinstallazione costruisce il piano dal registro dell'installazione confermata.
func (m *Motore) PianoDisinstallazione(prof *Profilo, purge bool) (*Piano, error) {
	in, err := m.ControllaInstallazione()
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(m.Cartella, in.Operazione)
	var orig Piano
	if err := LeggiJSON(filepath.Join(dir, "piano.json"), &orig); err != nil {
		return nil, err
	}
	ev, err := LeggiRegistro(filepath.Join(dir, "registro.jsonl"))
	if err != nil {
		return nil, err
	}
	origine := map[string]Origine{}
	for _, e := range ev {
		if e.Tipo == EvIntenzione {
			if _, ok := origine[e.Azione]; !ok {
				origine[e.Azione] = e.Origine
			}
		}
	}
	pn := &Piano{Formato: Formato, Oggetto: "piano", ID: nuovoID(), Creato: ora(), Mestiere: "disinstallazione", Purge: purge,
		Motore: RifMotore{VersioneMotore, DigestMotore()}, Catalogo: RifCatalogo{m.Catalogo.Versione, m.Catalogo.Digest, m.Catalogo.Scadenza},
		Piattaforma: orig.Piattaforma, Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{}, NonFatto: []Messaggio{}, Scelte: []Scelta{}}
	sess, _ := SessioniRemotix(m.Amb)
	var utenti []string
	visti := map[string]bool{}
	for _, s := range sess {
		if !visti[s.Utente] {
			visti[s.Utente] = true
			utenti = append(utenti, s.Utente)
		}
	}
	chiudi := PianoChiudiSessioni("chiudi-sessioni", len(sess), utenti)
	messa := false
	purgeS := map[bool]string{true: "si", false: "no"}[purge]
	for i := len(orig.Azioni) - 1; i >= 0; i-- {
		a := orig.Azioni[i]
		o, fatta := origine[a.ID]
		if !fatta || o == PREESISTENTE {
			continue
		}
		pn.Azioni = append(pn.Azioni, AzionePiano{ID: "disfa-" + a.ID, Tipo: "disfa",
			Parametri:      map[string]string{"operazione": in.Operazione, "azione": a.ID, "purge": purgeS},
			Descrizione:    T("az.disfa", a.Descrizione),
			ComeSiFa:       a.ComeSiAnnulla,
			ComeSiVerifica: T("az.disfa.verifica"),
			ComeSiAnnulla:  a.ComeSiFa,
			Reversibilita:  a.Reversibilita})
		if a.Tipo == "accendi-servizio" && !messa {
			pn.Azioni = append(pn.Azioni, chiudi)
			messa = true
		}
	}
	if !messa {
		pn.Azioni = append([]AzionePiano{chiudi}, pn.Azioni...)
	}
	// le iscrizioni ai gruppi fatte da REMOTIX alla prima connessione (DIRETTE), tranne quelle
	// che il motore stesso ha già in un suo passo
	gia := map[[2]string]bool{}
	for _, a := range orig.Azioni {
		if a.Tipo == "aggiungi-utente-a-gruppo" {
			gia[[2]string{a.Parametri["utente"], a.Parametri["gruppo"]}] = true
		}
	}
	for _, k := range m.Iscrizioni() {
		if gia[k] {
			continue
		}
		pn.Azioni = append(pn.Azioni, AzionePiano{ID: "iscrizione-" + k[0] + "-" + k[1], Tipo: "togli-iscrizione",
			Parametri: map[string]string{"utente": k[0], "gruppo": k[1]}, Descrizione: T("az.iscrizione", k[0], k[1]),
			ComeSiFa: T("az.iscrizione.fa"), ComeSiVerifica: T("az.iscrizione.verifica"), ComeSiAnnulla: T("az.iscrizione.annulla"),
			Reversibilita: ESATTA})
	}
	im, err := CalcolaImpronta(prof, m.Catalogo, pn.Azioni, pn.Dipende, &Contesto{Amb: m.Amb, Cartella: filepath.Join(m.Cartella, "piano-in-costruzione")})
	if err != nil {
		return nil, err
	}
	pn.Impronta = *im
	return pn, nil
}
