package motore

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// attiva-cintura: una delle tre cinture (DECISIONI §4.7: la macchina non si spegne, non si
// sospende, i tasti non la spengono) accesa in /etc copiando il file SPENTO che il pacchetto porta
// in /usr/share/remotix/cinture/ (DECISIONI §10.12). Se accenderle sempre o chiederlo è la
// decisione D4, aperta: il passo porta una riga di consenso sua. Reversibilità ESATTA: è
// scrivi-file col contenuto preso dalla sorgente al momento di farlo (il pacchetto arriva nella
// stessa operazione), salvato nella cartella dell'operazione perché la ripresa non dipenda da lui.
// Dopo averla messa e dopo averla tolta si ricarica chi la legge (systemd-logind, sul D-Bus).
//
// parametri: sorgente, percorso, modo, ricarica (un'unità da ricaricare, facoltativa).

func init() { registraTipo("attiva-cintura", nuovaCintura) }

// Le tre cinture: sorgente nel pacchetto → posto in /etc, e chi va ricaricato.
var Cinture = []struct{ ID, Sorgente, Percorso, Ricarica string }{
	{"cintura-spegnimento", "/usr/share/remotix/cinture/50-remotix-niente-spegnimento.rules", "/etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules", ""},
	{"cintura-tasti", "/usr/share/remotix/cinture/remotix-tasti.conf", "/etc/systemd/logind.conf.d/remotix-tasti.conf", "systemd-logind.service"},
	{"cintura-sospensione", "/usr/share/remotix/cinture/remotix-niente-sospensione.conf", "/etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf", ""},
}

// PianoCintura prepara il passo del piano.
func PianoCintura(id, sorgente, destinazione, ricarica string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "attiva-cintura",
		Parametri:      map[string]string{"sorgente": sorgente, "percorso": destinazione, "modo": "0644", "ricarica": ricarica},
		Descrizione:    T("az.cintura", destinazione),
		ComeSiFa:       T("az.cintura.fa", sorgente, destinazione),
		ComeSiVerifica: T("az.cintura.verifica"),
		ComeSiAnnulla:  T("az.cintura.annulla"),
		Reversibilita:  ESATTA,
	}
}

type cintura struct {
	f                  *scriviFile
	sorgente, ricarica string
}

type primaCintura struct {
	Origine Origine         `json:"origine"`
	Nuovo   string          `json:"nuovo"` // la copia della sorgente, relativa alla cartella dell'operazione
	File    json.RawMessage `json:"file"`  // lo stato di prima del file di destinazione
}

func nuovaCintura(p AzionePiano) (Azione, error) {
	q := p
	q.Parametri = map[string]string{"percorso": p.Parametri["percorso"], "modo": p.Parametri["modo"]}
	f, err := nuovaScriviFile(q)
	if err != nil {
		return nil, err
	}
	return &cintura{f: f.(*scriviFile), sorgente: p.Parametri["sorgente"], ricarica: p.Parametri["ricarica"]}, nil
}

func (a *cintura) Vincoli(c *Contesto) ([]string, error) { return a.f.Vincoli(c) }

func (a *cintura) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	b, err := os.ReadFile(c.Amb.P(a.sorgente))
	if err != nil {
		return nil, "", Errore("RX-CINTURA-001", a.sorgente)
	}
	nuovo := filepath.Join("salvataggi", c.P.ID+".nuovo")
	if err := os.MkdirAll(filepath.Join(c.Cartella, "salvataggi"), 0o700); err != nil {
		return nil, "", err
	}
	if err := ScriviAtomico(filepath.Join(c.Cartella, nuovo), b, 0o600); err != nil {
		return nil, "", err
	}
	a.f.contenuto = b
	pf, orig, err := a.f.Fotografa(c)
	if err != nil {
		return nil, "", err
	}
	return jsonDi(primaCintura{Origine: orig, Nuovo: nuovo, File: pf}), orig, nil
}

func (a *cintura) carica(c *Contesto, prima json.RawMessage) (primaCintura, error) {
	var p primaCintura
	if err := json.Unmarshal(prima, &p); err != nil {
		return p, err
	}
	b, err := os.ReadFile(filepath.Join(c.Cartella, p.Nuovo))
	if err != nil {
		return p, err
	}
	a.f.contenuto = b
	return p, nil
}

func (a *cintura) ricaricaSe(c *Contesto) error {
	if a.ricarica == "" {
		return nil
	}
	return c.Amb.Unita.Ricarica(a.ricarica)
}

func (a *cintura) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := a.carica(c, prima)
	if err != nil {
		return err
	}
	if err := a.f.Fai(c, p.File); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	return a.ricaricaSe(c)
}

func (a *cintura) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	p, err := a.carica(c, prima)
	if err != nil {
		return "", "", err
	}
	return a.f.Controlla(c, p.File)
}

func (a *cintura) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := a.carica(c, prima)
	if err != nil {
		return err
	}
	if err := a.f.Annulla(c, p.File); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	return a.ricaricaSe(c)
}

func (a *cintura) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := a.carica(c, prima)
	if err != nil {
		return false, "", err
	}
	return a.f.Annullata(c, p.File)
}
