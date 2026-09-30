package motore

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// L'AGGIORNAMENTO AUTOMATICO (DECISIONI §10.10, T8) e il RITORNO INDIETRO (R11).
//
// ⛔ Il motore non scarica né sostituisce da sé il binario di REMOTIX: chiede al GESTORE DI
// PACCHETTI della distribuzione di portare i pacchetti di REMOTIX alle versioni scelte, dall'archivio
// firmato di REMOTIX (catena B, verificata dal gestore). Poi verifica e, se il servizio era acceso,
// controlla che sia ripartito — il servizio nuovo ritrova i desktop vivi (T7): nessun desktop si
// chiude. Ogni aggiornamento è un'OPERAZIONE del motore (mestiere «aggiornamento») col suo piano,
// il suo registro e il suo certificato; se la verifica non passa si torna alle versioni di prima.
//
// Il timer (remotix-aggiorna.timer, nel pacchetto remotix-install, inerte finché il motore non lo
// accende all'installazione) lancia ogni giorno `remotix-install aggiorna --dal-timer`.
//
// ⭐ D14 NON è decisa: tutto è CONFIGURABILE in /etc/remotix/aggiornamenti.conf, e il predefinito è
// la PROPOSTA di D14 (fasi/17 §10): «manutenzione» = sicurezza e ricostruzioni si applicano da sole,
// la versione annuale la sceglie l'amministratore. Le altre scelte: «tutto», «avviso» (solo avviso,
// l'alternativa di D14), «spento». La regola che distingue le due cose è VersioneAnnuale
// (versioni.go): cambia X.Y di X.Y.Z ⇒ annuale; cambia Z o la revisione del pacchetto ⇒ manutenzione.
// remotix-install e remotix-archive-keyring (il motore e la chiave) sono sempre manutenzione: la
// chiave deve seguire la rotazione della sottochiave.

// FileConfAggiornamenti: la configurazione dell'amministratore (facoltativa).
const FileConfAggiornamenti = "/etc/remotix/aggiornamenti.conf"

// ConfAggiornamenti: la configurazione in vigore, e da dove viene ogni voce.
type ConfAggiornamenti struct {
	Automatico string            `json:"automatico"` // manutenzione · tutto · avviso · spento
	Da         map[string]string `json:"da"`         // voce → «predefinito (proposta D14)» o il file
}

// ModiAutomatico: i valori ammessi, col loro significato (per --mostra e per il manuale).
var ModiAutomatico = map[string]string{
	"manutenzione": "sicurezza e ricostruzioni si applicano da sole; la versione annuale la sceglie l'amministratore (proposta D14, predefinito)",
	"tutto":        "si applica da solo anche la versione annuale",
	"avviso":       "niente si applica da solo: il timer avvisa soltanto (l'alternativa di D14)",
	"spento":       "il timer non controlla niente",
}

// LeggiConfAggiornamenti: i predefiniti, poi il file dell'amministratore che vince.
func LeggiConfAggiornamenti(a *Ambiente) (*ConfAggiornamenti, error) {
	c := &ConfAggiornamenti{Automatico: "manutenzione", Da: map[string]string{"automatico": "predefinito (proposta D14)"}}
	f, err := os.Open(a.P(FileConfAggiornamenti))
	if os.IsNotExist(err) {
		return c, nil
	}
	if err != nil {
		return nil, Errore("RX-AGG-010", err.Error())
	}
	defer f.Close()
	s := bufio.NewScanner(f)
	n := 0
	for s.Scan() {
		n++
		riga := strings.TrimSpace(s.Text())
		if riga == "" || strings.HasPrefix(riga, "#") {
			continue
		}
		k, v, ok := strings.Cut(riga, "=")
		k, v = strings.TrimSpace(k), strings.TrimSpace(v)
		switch {
		case !ok:
			return nil, Errore("RX-AGG-010", fmt.Sprintf("riga %d: %q", n, riga))
		case k == "automatico":
			if _, ok := ModiAutomatico[v]; !ok {
				return nil, Errore("RX-AGG-010", fmt.Sprintf("riga %d: automatico = %q (ammessi: manutenzione, tutto, avviso, spento)", n, v))
			}
			c.Automatico, c.Da[k] = v, FileConfAggiornamenti
		default:
			return nil, Errore("RX-AGG-010", fmt.Sprintf("riga %d: voce sconosciuta %q", n, k))
		}
	}
	return c, s.Err()
}

// ---------------------------------------------------------------- il passo del piano

// aggiorna-pacchetti: i pacchetti di REMOTIX portati a versioni ESATTE dall'archivio di REMOTIX
// (più nuove: aggiornamento; più vecchie: ritorno indietro, R11). Reversibilità ESATTA per i
// pacchetti di REMOTIX (le versioni di prima restano nell'archivio: si torna a quelle); le
// dipendenze che il gestore aggiorna nel frattempo restano (INDIRETTE, dichiarate).
//
// parametri: versioni ("remotix=0.17.0-2+deb13,remotix-install=…"), archivio (l'URL del deposito
// della famiglia), tipo (manutenzione · annuale · ritorno).

func init() { registraTipo("aggiorna-pacchetti", nuovaAggiorna) }

// PianoAggiornaPacchetti prepara il passo.
func PianoAggiornaPacchetti(id string, voluti map[string]string, archivio, tipo string) AzionePiano {
	var v []string
	for _, n := range chiaviOrdinate(voluti) {
		v = append(v, n+"="+voluti[n])
	}
	return AzionePiano{ID: id, Tipo: "aggiorna-pacchetti",
		Parametri:      map[string]string{"versioni": strings.Join(v, ","), "archivio": archivio, "tipo": tipo},
		Descrizione:    T("az.aggiorna", tipo, strings.Join(v, ", ")),
		ComeSiFa:       T("az.aggiorna.fa"),
		ComeSiVerifica: T("az.aggiorna.verifica"),
		ComeSiAnnulla:  T("az.aggiorna.annulla"),
		Reversibilita:  ESATTA}
}

type aggiorna struct {
	voluti   map[string]string
	archivio string
	tipo     string
}

type primaAggiorna struct {
	Origine     Origine           `json:"origine"`
	Prima       map[string]string `json:"prima"`  // le versioni installate prima
	Voluti      map[string]string `json:"voluti"` // quelle del piano
	Insieme     []Artefatto       `json:"insieme_risolto"`
	Servizio    string            `json:"servizio"` // ActiveState di remotix.service prima
	Sessioni    int               `json:"sessioni"` // le sessioni REMOTIX aperte prima (i desktop che devono restare)
	Salvataggio string            `json:"salvataggio,omitempty"`
}

func nuovaAggiorna(p AzionePiano) (Azione, error) {
	a := &aggiorna{voluti: map[string]string{}, archivio: p.Parametri["archivio"], tipo: p.Parametri["tipo"]}
	for _, x := range strings.Split(p.Parametri["versioni"], ",") {
		if n, v, ok := strings.Cut(strings.TrimSpace(x), "="); ok && n != "" && v != "" {
			a.voluti[n] = v
		}
	}
	if len(a.voluti) == 0 {
		return nil, fmt.Errorf("aggiorna-pacchetti: nessuna versione")
	}
	return a, nil
}

func (a *aggiorna) agg(c *Contesto) (Aggiornatore, error) {
	g := ScegliAggiornatore(c.Amb)
	if g == nil {
		return nil, Errore("RX-PACCHETTI-003", c.Amb.Famiglia)
	}
	return g, nil
}

func (a *aggiorna) installate(c *Contesto) (map[string]string, error) {
	if c.Amb.Pacchetti == nil {
		return nil, Errore("RX-PACCHETTI-003", c.Amb.Famiglia)
	}
	return c.Amb.Pacchetti.Versioni(chiaviOrdinate(a.voluti))
}

func uguali(fam string, x, y map[string]string, nomi map[string]string) bool {
	for n := range nomi {
		if x[n] == "" || y[n] == "" {
			if x[n] != y[n] {
				return false
			}
			continue
		}
		if ConfrontaPacchetti(fam, x[n], y[n]) != 0 {
			return false
		}
	}
	return true
}

func (a *aggiorna) Vincoli(c *Contesto) ([]string, error) {
	v, err := a.installate(c)
	if err != nil {
		return nil, err
	}
	var r []string
	for _, n := range chiaviOrdinate(a.voluti) {
		r = append(r, "pacchetto:"+n+"="+nonVuoto(v[n], "assente"))
	}
	return r, nil
}

func (a *aggiorna) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	prima, err := a.installate(c)
	if err != nil {
		return nil, "", err
	}
	p := primaAggiorna{Origine: DIRETTA, Prima: prima, Voluti: a.voluti}
	if uguali(c.Amb.Famiglia, prima, a.voluti, a.voluti) {
		p.Origine = PREESISTENTE
		return jsonDi(p), p.Origine, nil
	}
	g, err := a.agg(c)
	if err != nil {
		return nil, "", err
	}
	if ok, det, err := c.Amb.Pacchetti.Integro(); err != nil {
		return nil, "", err
	} else if !ok {
		return nil, "", Errore("RX-PACCHETTI-004", det)
	}
	cache := filepath.Join(c.Cartella, "cache", c.P.ID)
	if err := os.MkdirAll(cache, 0o700); err != nil {
		return nil, "", err
	}
	ins, err := g.Prepara(cache, a.voluti, a.archivio)
	if err != nil {
		return nil, "", err
	}
	p.Insieme = ins
	if c.Amb.Unita != nil {
		p.Servizio, _ = c.Amb.Unita.Attiva("remotix.service")
	}
	if s, err := SessioniRemotix(c.Amb); err == nil {
		p.Sessioni = len(s)
	}
	// §6.5 punto 5: prima di cambiare versione si salva /etc/remotix (la versione N−1 legge la
	// configurazione della N; il salvataggio è per l'amministratore, il motore non lo rimette da sé)
	p.Salvataggio = filepath.Join("salvataggio-"+c.P.ID, "etc-remotix")
	if err := copiaAlbero(c.Amb.P("/etc/remotix"), filepath.Join(c.Cartella, p.Salvataggio)); err != nil {
		return nil, "", err
	}
	if err := ScriviJSON(filepath.Join(c.Cartella, "insieme-risolto-"+c.P.ID+".json"),
		map[string]any{"formato": Formato, "oggetto": "insieme-risolto", "azione": c.P.ID, "artefatti": ins}); err != nil {
		return nil, "", err
	}
	return jsonDi(p), p.Origine, nil
}

func leggiPrimaAggiorna(b json.RawMessage) (primaAggiorna, error) {
	var p primaAggiorna
	err := json.Unmarshal(b, &p)
	return p, err
}

// porta i pacchetti a «voluti»; poi, se il servizio era acceso, deve esserlo ancora (il pacchetto lo
// riaccende da sé, try-restart: se non l'ha fatto, lo riaccende il motore).
func (a *aggiorna) porta(c *Contesto, p primaAggiorna, voluti map[string]string) error {
	g, err := a.agg(c)
	if err != nil {
		return err
	}
	cache := filepath.Join(c.Cartella, "cache", c.P.ID)
	if err := g.Porta(cache, voluti, a.archivio); err != nil {
		return err
	}
	if p.Servizio == "active" && c.Amb.Unita != nil {
		if s, _ := c.Amb.Unita.Attiva("remotix.service"); s != "active" {
			return c.Amb.Unita.Avvia("remotix.service")
		}
	}
	return nil
}

func (a *aggiorna) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaAggiorna(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	return a.porta(c, p, a.voluti)
}

func (a *aggiorna) servizioOk(c *Contesto, p primaAggiorna) (bool, string) {
	if p.Servizio != "active" || c.Amb.Unita == nil {
		return true, ""
	}
	s, _ := c.Amb.Unita.Attiva("remotix.service")
	if s != "active" {
		return false, "remotix.service è " + s
	}
	return true, ""
}

func (a *aggiorna) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	p, err := leggiPrimaAggiorna(prima)
	if err != nil {
		return "", "", err
	}
	ora, err := a.installate(c)
	if err != nil {
		return "", "", err
	}
	if ok, det, err := c.Amb.Pacchetti.Integro(); err == nil && !ok {
		return A_META, "il gestore è a metà: " + det, nil
	}
	switch {
	case uguali(c.Amb.Famiglia, ora, a.voluti, a.voluti):
		if ok, det := a.servizioOk(c, p); !ok {
			return A_META, det, nil
		}
		return COMPLETO, "versioni " + jsonCompatto(ora), nil
	case uguali(c.Amb.Famiglia, ora, p.Prima, a.voluti):
		return ASSENTE, "versioni di prima", nil
	}
	return A_META, "versioni " + jsonCompatto(ora), nil
}

func (a *aggiorna) Ripara(c *Contesto, prima json.RawMessage) error {
	if c.Amb.Pacchetti == nil {
		return nil
	}
	if ok, _, err := c.Amb.Pacchetti.Integro(); err == nil && !ok {
		return c.Amb.Pacchetti.Ripara()
	}
	return nil
}

// Annulla: si torna alle versioni di prima (dall'archivio, che le conserva; o dalla cache).
func (a *aggiorna) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaAggiorna(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	if err := a.Ripara(c, prima); err != nil {
		return err
	}
	ora, err := a.installate(c)
	if err != nil {
		return err
	}
	if uguali(c.Amb.Famiglia, ora, p.Prima, a.voluti) {
		return nil
	}
	indietro := map[string]string{}
	for n, v := range p.Prima {
		if v != "" {
			indietro[n] = v
		}
	}
	return a.porta(c, p, indietro)
}

func (a *aggiorna) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := leggiPrimaAggiorna(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "erano già a quelle versioni", nil
	}
	ora, err := a.installate(c)
	if err != nil {
		return false, "", err
	}
	if uguali(c.Amb.Famiglia, ora, p.Prima, a.voluti) {
		return true, "versioni di prima", nil
	}
	return false, "versioni " + jsonCompatto(ora), nil
}

// Indirette: le dipendenze che la transazione ha aggiornato restano (§6.6.4).
func (a *aggiorna) Indirette(prima json.RawMessage) []string {
	p, err := leggiPrimaAggiorna(prima)
	if err != nil {
		return nil
	}
	var r []string
	for _, x := range p.Insieme {
		if _, nostro := a.voluti[x.Nome]; !nostro && x.Esito != "nuovo" {
			r = append(r, x.Nome+" "+x.Prima+" → "+x.Versione)
		}
	}
	return r
}

func jsonCompatto(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}

// copiaAlbero: una copia dei file normali (e delle cartelle) di un albero piccolo; niente se manca.
func copiaAlbero(da, a string) error {
	if _, err := os.Stat(da); os.IsNotExist(err) {
		return nil
	}
	return filepath.Walk(da, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(da, p)
		dest := filepath.Join(a, rel)
		switch {
		case info.IsDir():
			return os.MkdirAll(dest, 0o700)
		case info.Mode().IsRegular():
			in, err := os.Open(p)
			if err != nil {
				return err
			}
			defer in.Close()
			out, err := os.OpenFile(dest, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o600)
			if err != nil {
				return err
			}
			if _, err := io.Copy(out, in); err != nil {
				out.Close()
				return err
			}
			return out.Close()
		}
		return nil
	})
}

// ---------------------------------------------------------------- il mestiere «aggiornamento»

// OpzioniAggiorna: che cosa si chiede.
type OpzioniAggiorna struct {
	DalTimer  bool   // il timer: vale la configurazione (il consenso dato prima, §6.6.12)
	Controlla bool   // solo guardare: niente si applica
	Applica   bool   // l'amministratore applica la manutenzione anche se la configurazione dice «avviso»
	Annuale   bool   // l'amministratore sceglie la versione annuale
	Versione  string // una versione precisa di remotix (anche più vecchia: il ritorno indietro, R11)
	Chi       string
}

// RapportoAggiorna: che cosa il controllo ha trovato e che cosa ne è stato.
type RapportoAggiorna struct {
	Formato      string              `json:"formato"`
	Oggetto      string              `json:"oggetto"` // "aggiornamento"
	Creato       string              `json:"creato"`
	Conf         *ConfAggiornamenti  `json:"configurazione"`
	Archivio     string              `json:"archivio"`
	Canale       string              `json:"canale"`
	Installate   map[string]string   `json:"installate"`
	Disponibili  map[string][]string `json:"disponibili"`
	Manutenzione map[string]string   `json:"manutenzione,omitempty"` // la più nuova con lo stesso X.Y
	Annuale      map[string]string   `json:"annuale,omitempty"`      // una X.Y nuova
	Scelte       map[string]string   `json:"scelte,omitempty"`       // quel che si applica
	Tipo         string              `json:"tipo,omitempty"`
	Catalogo     string              `json:"catalogo,omitempty"`
	Messaggi     []Messaggio         `json:"messaggi"`
	Operazione   string              `json:"operazione,omitempty"`
	Stato        Stato               `json:"stato,omitempty"`
}

// ArchivioInstallato: l'archivio e il canale dell'installazione confermata (dal suo piano).
func (m *Motore) ArchivioInstallato() (*RifArchivio, map[string]string, error) {
	in, err := m.ControllaInstallazione()
	if err != nil {
		return nil, nil, err
	}
	var pn Piano
	if err := LeggiJSON(filepath.Join(m.Cartella, in.Operazione, "piano.json"), &pn); err != nil {
		return nil, nil, err
	}
	for _, a := range pn.Azioni {
		if a.Tipo == "aggiungi-deposito" && a.Parametri["tipo"] == "archivio" {
			return &RifArchivio{URL: a.Parametri["archivio"], Canale: a.Parametri["canale"]}, a.Parametri, nil
		}
	}
	return nil, nil, Errore("RX-AGG-006", "l'installazione "+in.Operazione+" non viene dall'archivio di REMOTIX")
}

// Aggiorna: il controllo (e, se va applicato, l'operazione) dell'aggiornamento.
func (m *Motore) Aggiorna(o OpzioniAggiorna) (*RapportoAggiorna, *Operazione, error) {
	r := &RapportoAggiorna{Formato: Formato, Oggetto: "aggiornamento", Creato: ora(), Messaggi: []Messaggio{}}
	conf, err := LeggiConfAggiornamenti(m.Amb)
	if err != nil {
		return r, nil, err
	}
	r.Conf = conf
	if o.DalTimer && conf.Automatico == "spento" {
		r.Messaggi = append(r.Messaggi, Msg("RX-AGG-005", ""))
		return r, nil, nil
	}
	arc, par, err := m.ArchivioInstallato()
	if err != nil {
		return r, nil, Errore("RX-AGG-006", err.Error())
	}
	r.Archivio, r.Canale = arc.URL, arc.Canale
	repo := strings.ReplaceAll(par["url"], "$arch", "x86_64")

	// la fiducia: il catalogo del canale, verificato e memorizzato (si aggiorna da solo, §10.10).
	// ⚠ Se non si verifica, il controllo dei pacchetti continua: se c'è da applicare, l'operazione
	// nasce e la sua fase 0 la ferma (BLOCCATA, niente toccato, lo stato resta nella storia); se non
	// c'è niente da applicare, l'errore esce così com'è.
	var errT error
	if m.Fonti != nil {
		f := *m.Fonti
		f.Archivio, f.Canale, f.Scrivi = arc.URL, arc.Canale, true
		cat, fid, err := f.Fidati(m.adesso())
		r.Messaggi = append(r.Messaggi, fid.Messaggi...)
		if err != nil {
			errT = err
		} else {
			m.Catalogo = cat
			r.Catalogo = fmt.Sprintf("%s (sequenza %d, %s)", cat.Versione, cat.Sequenza, fid.Fonte)
		}
	}
	if m.Catalogo == nil {
		return r, nil, errT
	}

	g := ScegliAggiornatore(m.Amb)
	if g == nil || m.Amb.Pacchetti == nil {
		return r, nil, Errore("RX-PACCHETTI-003", m.Amb.Famiglia)
	}
	if err := m.Blocca(); err != nil {
		return r, nil, err
	}
	errR := g.Rinfresca(repo)
	var disp map[string][]string
	if errR == nil {
		disp, errR = g.Disponibili(PacchettiArchivio, repo)
	}
	inst, errV := m.Amb.Pacchetti.Versioni(PacchettiArchivio)
	m.Sblocca()
	if errR != nil {
		return r, nil, errR
	}
	if errV != nil {
		return r, nil, errV
	}
	fam := m.Amb.Famiglia
	r.Installate, r.Disponibili = map[string]string{}, disp
	r.Manutenzione, r.Annuale, r.Scelte = map[string]string{}, map[string]string{}, map[string]string{}
	for _, n := range PacchettiArchivio {
		iv := inst[n]
		if iv == "" {
			continue
		}
		r.Installate[n] = iv
		for _, v := range disp[n] {
			if ConfrontaPacchetti(fam, v, iv) <= 0 {
				continue
			}
			if n != "remotix" || !Annuale(iv, v) {
				r.Manutenzione[n] = v // le versioni sono in ordine: resta la più nuova
			} else {
				r.Annuale[n] = v
			}
		}
	}

	switch {
	case o.Versione != "":
		if !contiene(disp["remotix"], o.Versione) {
			return r, nil, Errore("RX-AGG-009", "remotix "+o.Versione+" (ci sono: "+strings.Join(disp["remotix"], ", ")+")")
		}
		r.Scelte["remotix"] = o.Versione
		r.Tipo = "ritorno"
		if ConfrontaPacchetti(fam, o.Versione, r.Installate["remotix"]) > 0 {
			r.Tipo = "aggiornamento a mano"
		}
	default:
		for n, v := range r.Manutenzione {
			r.Scelte[n] = v
		}
		r.Tipo = "manutenzione"
		annualeSi := o.Annuale || (o.DalTimer && conf.Automatico == "tutto")
		if len(r.Annuale) > 0 {
			if annualeSi {
				for n, v := range r.Annuale {
					r.Scelte[n] = v
				}
				r.Tipo = "annuale"
			} else {
				r.Messaggi = append(r.Messaggi, Msg("RX-AGG-003", "remotix "+r.Annuale["remotix"]))
			}
		}
		if len(r.Scelte) > 0 && r.Tipo == "manutenzione" {
			r.Messaggi = append(r.Messaggi, Msg("RX-AGG-002", jsonCompatto(r.Scelte)))
		}
		if len(r.Scelte) == 0 && len(r.Annuale) == 0 {
			r.Messaggi = append(r.Messaggi, Msg("RX-AGG-001", jsonCompatto(r.Installate)))
		}
	}
	if o.Controlla || len(r.Scelte) == 0 {
		return r, nil, errT
	}
	if o.DalTimer && conf.Automatico == "avviso" {
		r.Messaggi = append(r.Messaggi, Msg("RX-AGG-004", jsonCompatto(r.Scelte)))
		return r, nil, errT
	}

	// il piano dell'aggiornamento, col consenso dato prima (timer) o adesso (l'amministratore)
	prof := m.Profilo()
	pn := &Piano{Formato: Formato, Oggetto: "piano", ID: nuovoID(), Creato: ora(), Mestiere: "aggiornamento",
		Motore: RifMotore{VersioneMotore, DigestMotore()}, Catalogo: RifCatalogo{m.Catalogo.Versione, m.Catalogo.Digest, m.Catalogo.Scadenza},
		Piattaforma: Valuta(m.Catalogo, prof).Piattaforma, Archivio: arc, Dipende: []string{}, Consensi: []string{}, Condizioni: []Condizione{},
		NonFatto: []Messaggio{}, Scelte: []Scelta{},
		Azioni: []AzionePiano{PianoAggiornaPacchetti("aggiorna", r.Scelte, repo, r.Tipo)}}
	im, err := CalcolaImpronta(prof, m.Catalogo, pn.Azioni, pn.Dipende, &Contesto{Amb: m.Amb, Cartella: filepath.Join(m.Cartella, "piano-in-costruzione")})
	if err != nil {
		return r, nil, err
	}
	pn.Impronta = *im
	modo := T("agg.consenso_ora", o.Chi)
	if o.DalTimer {
		modo = T("agg.consenso_prima", conf.Automatico, conf.Da["automatico"])
	}
	pn.Approvazione = &Approvazione{Da: nonVuoto(o.Chi, "remotix-aggiorna.timer"), Ora: ora(), Modo: modo, DigestPiano: pn.Digest()}
	dir := filepath.Join(filepath.Dir(m.Cartella), "aggiornamenti")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return r, nil, err
	}
	pp := filepath.Join(dir, "piano-"+pn.ID+".json")
	if err := ScriviJSON(pp, pn); err != nil {
		return r, nil, err
	}
	op, err := m.Applica(pp, false, pn.Approvazione.Da)
	if op != nil {
		r.Operazione, r.Stato = op.ID, op.Stato
	}
	return r, op, err
}

// scriviAggiornate: a un aggiornamento CONFERMATO, le versioni nuove dei pacchetti di REMOTIX. Le
// legge il «controlla» dei pacchetti dell'installazione (azione_pacchetti.go), che altrimenti
// vedrebbe una versione diversa da quella installata allora e la direbbe «a metà».
func (op *Operazione) scriviAggiornate() error {
	v := map[string]string{}
	for _, ap := range op.Piano.Azioni {
		if ap.Tipo != "aggiorna-pacchetti" {
			continue
		}
		a, err := nuovaAggiorna(ap)
		if err != nil {
			return err
		}
		for n, x := range a.(*aggiorna).voluti {
			v[n] = x
		}
	}
	return ScriviJSON(filepath.Join(filepath.Dir(op.m.Cartella), "aggiornamenti.json"),
		map[string]any{"formato": Formato, "oggetto": "versioni-aggiornate", "operazione": op.ID, "versioni": v, "scritto": ora()})
}

// versioniAggiornate: quelle scritte dall'ultimo aggiornamento confermato (vuoto se nessuno).
func versioniAggiornate(cartellaOp string) map[string]string {
	var x struct {
		Versioni map[string]string `json:"versioni"`
	}
	LeggiJSON(filepath.Join(filepath.Dir(filepath.Dir(cartellaOp)), "aggiornamenti.json"), &x)
	return x.Versioni
}
