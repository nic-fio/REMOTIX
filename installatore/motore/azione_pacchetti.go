package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// installa-pacchetti: la transazione del gestore di pacchetti (§6.0 regola 1, §6.6.6; dal 10 ott
// 2026 senza cache né sha256 nostri: «non reinventare la ruota», DECISIONI §10.36).
//
//   - Fotografa (prima dell'intenzione): il gestore SIMULA la transazione; l'insieme (nome, versione,
//     origine, nuovo/aggiornato) va nell'intenzione del registro e in resolved-set-<passo>.json.
//   - Fai: il gestore installa — i file del pacchetto unico, con le dipendenze dagli archivi della
//     macchina, scaricate e verificate da lui.
//   - Controlla: ogni pacchetto alla versione simulata (o più nuova) ⇒ completo; nessuno dei nuovi ⇒
//     assente; altrimenti (o il gestore a metà di una transazione) ⇒ a metà.
//   - Ripara: il rimedio del gestore (dpkg --configure -a…), che serve prima di annullare.
//   - Annulla: si tolgono i pacchetti NUOVI, e solo quelli (il gestore simula prima: se ne
//     toglierebbe altri, li trattiene); quelli AGGIORNATI restano aggiornati e si dichiarano
//     (INDIRETTA, §6.6.4). Reversibilità AL_MEGLIO.
//
// parametri: file (percorsi dei pacchetti del .run, separati da virgola: una transazione sola),
// names (separati da virgola, dagli archivi della macchina).

func init() { registraTipo("install-packages", nuovaPacchetti) }

// PianoPacchetti prepara il passo del piano.
func PianoPacchetti(id, file, nomi string) AzionePiano {
	var basi []string
	for _, f := range dividiVirgole(file) {
		basi = append(basi, filepath.Base(f))
	}
	cosa := strings.TrimSpace(strings.Join(basi, " ") + " " + nomi)
	return AzionePiano{
		ID: id, Tipo: "install-packages",
		Parametri:      map[string]string{"file": file, "names": nomi},
		Descrizione:    T("az.pacchetti", cosa),
		ComeSiFa:       T("az.pacchetti.fa"),
		ComeSiVerifica: T("az.pacchetti.verifica"),
		ComeSiAnnulla:  T("az.pacchetti.annulla"),
		Reversibilita:  AL_MEGLIO,
	}
}

type pacchetti struct {
	file, nomi []string
}

type primaPacchetti struct {
	Origine Origine     `json:"origin"`
	Gestore string      `json:"manager"`
	File    []string    `json:"files,omitempty"`
	Nomi    []string    `json:"names"`
	Insieme []Artefatto `json:"resolved_set"`
}

func nuovaPacchetti(p AzionePiano) (Azione, error) {
	return &pacchetti{file: dividiVirgole(p.Parametri["file"]), nomi: dividiVirgole(p.Parametri["names"])}, nil
}

func (a *pacchetti) gestore(c *Contesto) (Gestore, error) {
	if c.Amb.Pacchetti == nil {
		return nil, Errore("RX-PACCHETTI-003", c.Amb.Famiglia)
	}
	return c.Amb.Pacchetti, nil
}

// Vincoli: le versioni installate adesso dei pacchetti nominati, e i file del pacchetto unico (per
// nome: il .run è uno, e il suo sha256 lo garantisce intero).
func (a *pacchetti) Vincoli(c *Contesto) ([]string, error) {
	g, err := a.gestore(c)
	if err != nil {
		return nil, err
	}
	var v []string
	for _, f := range a.file {
		v = append(v, "package-file:"+filepath.Base(f))
	}
	ver, err := g.Versioni(a.nomi)
	if err != nil {
		return nil, err
	}
	for _, n := range a.nomi {
		v = append(v, "package:"+n+"="+nonVuoto(ver[n], "absent"))
	}
	return v, nil
}

// veri: i percorsi dei file sulla macchina (nelle prove, sotto la radice finta).
func veri(c *Contesto, file []string) []string {
	var r []string
	for _, f := range file {
		r = append(r, c.Amb.P(f))
	}
	return r
}

// dividiVirgole: «a,b» ⇒ [a b]; vuoto ⇒ nessuno.
func dividiVirgole(s string) []string {
	var r []string
	for _, x := range strings.Split(s, ",") {
		if x = strings.TrimSpace(x); x != "" {
			r = append(r, x)
		}
	}
	return r
}

func (a *pacchetti) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	g, err := a.gestore(c)
	if err != nil {
		return nil, "", err
	}
	if ok, det, err := g.Integro(); err != nil {
		return nil, "", err
	} else if !ok {
		return nil, "", Errore("RX-PACCHETTI-004", det)
	}
	for _, f := range a.file {
		if _, err := os.Stat(c.Amb.P(f)); err != nil {
			return nil, "", Errore("RX-PACCHETTI-001", f+": "+err.Error())
		}
	}
	ins, err := g.Simula(veri(c, a.file), a.nomi)
	if err != nil {
		return nil, "", Errore("RX-PACCHETTI-005", err.Error())
	}
	p := primaPacchetti{Origine: PREESISTENTE, Gestore: g.Nome(), File: a.file, Nomi: a.nomi, Insieme: ins}
	for _, x := range ins {
		if x.Esito != "present" {
			p.Origine = DIRETTA
		}
	}
	if err := ScriviJSON(filepath.Join(c.Cartella, "resolved-set-"+c.P.ID+".json"),
		map[string]any{"format": Formato, "object": "resolved-set", "action": c.P.ID, "manager": g.Nome(), "artifacts": ins}); err != nil {
		return nil, "", err
	}
	return jsonDi(p), p.Origine, nil
}

func leggiPrimaPacchetti(prima json.RawMessage) (primaPacchetti, error) {
	var p primaPacchetti
	err := json.Unmarshal(prima, &p)
	return p, err
}

func (a *pacchetti) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	g, err := a.gestore(c)
	if err != nil {
		return err
	}
	return g.Installa(veri(c, p.File), p.Nomi)
}

// stato dei pacchetti dell'insieme, adesso.
func (a *pacchetti) conta(c *Contesto, p primaPacchetti) (completi, nuoviPresenti int, err error) {
	g, err := a.gestore(c)
	if err != nil {
		return 0, 0, err
	}
	ver, err := g.Versioni(nomiDi(p.Insieme))
	if err != nil {
		return 0, 0, err
	}
	// D14 (DECISIONI §10.23): REMOTIX e le sue dipendenze si aggiornano col sistema. Un pacchetto
	// dell'insieme è «completo» alla versione risolta, a una PIÙ NUOVA (l'ha portata un aggiornamento
	// del sistema), o a quella annotata dall'ultimo `remotix-install aggiornato` (un ritorno indietro
	// fatto coi comandi del gestore)
	agg := versioniAggiornate(c.Cartella)
	for _, x := range p.Insieme {
		v := ver[x.Nome]
		if versioneUguale(v, x.Versione) || (agg[x.Nome] != "" && versioneUguale(v, agg[x.Nome])) ||
			(v != "" && x.Versione != "" && ConfrontaPacchetti(c.Amb.Famiglia, v, x.Versione) > 0) {
			completi++
		}
		if x.Esito == "new" && v != "" {
			nuoviPresenti++
		}
	}
	return completi, nuoviPresenti, nil
}

// versioneUguale: dpkg dice «1:2.3-1», rpm «2.3-1»; l'epoca «0:» non conta.
func versioneUguale(a, b string) bool {
	return strings.TrimPrefix(a, "0:") == strings.TrimPrefix(b, "0:")
}

func (a *pacchetti) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil {
		return "", "", err
	}
	g, err := a.gestore(c)
	if err != nil {
		return "", "", err
	}
	if ok, det, err := g.Integro(); err != nil {
		return "", "", err
	} else if !ok {
		return A_META, "the package manager is half way: " + det, nil
	}
	completi, nuovi, err := a.conta(c, p)
	if err != nil {
		return "", "", err
	}
	switch {
	case completi == len(p.Insieme):
		return COMPLETO, fmt.Sprintf("%d packages at the resolved version", completi), nil
	case nuovi == 0 && completi == 0:
		return ASSENTE, "none of the new packages", nil
	case nuovi == 0:
		return ASSENTE, "none of the new packages (the upgraded ones stay)", nil
	}
	return A_META, fmt.Sprintf("%d of %d", completi, len(p.Insieme)), nil
}

func (a *pacchetti) Ripara(c *Contesto, prima json.RawMessage) error {
	g, err := a.gestore(c)
	if err != nil {
		return err
	}
	if ok, _, err := g.Integro(); err == nil && ok {
		return nil
	}
	return g.Ripara()
}

func (a *pacchetti) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	g, err := a.gestore(c)
	if err != nil {
		return err
	}
	if ok, _, err := g.Integro(); err == nil && !ok {
		if err := g.Ripara(); err != nil {
			return err
		}
	}
	ver, err := g.Versioni(nomiDi(p.Insieme))
	if err != nil {
		return err
	}
	var nuovi []string
	for _, x := range p.Insieme {
		if x.Esito == "new" && ver[x.Nome] != "" {
			nuovi = append(nuovi, x.Nome)
		}
	}
	togli, _, err := trattenuti(g, nuovi, nuovi, c.Purge)
	if err != nil {
		return err
	}
	if len(togli) > 0 {
		return g.Togli(togli, c.Purge)
	}
	return nil
}

func (a *pacchetti) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "already there: left untouched", nil
	}
	g, err := a.gestore(c)
	if err != nil {
		return false, "", err
	}
	ver, err := g.Versioni(nomiDi(p.Insieme))
	if err != nil {
		return false, "", err
	}
	var tutti, ancora []string
	for _, x := range p.Insieme {
		if x.Esito == "new" {
			tutti = append(tutti, x.Nome)
			if ver[x.Nome] != "" {
				ancora = append(ancora, x.Nome)
			}
		}
	}
	via, resta, err := trattenuti(g, ancora, tutti, c.Purge)
	if err != nil {
		return false, "", err
	}
	if len(via) > 0 {
		return false, fmt.Sprintf("%d new packages still installed", len(via)), nil
	}
	if len(resta) > 0 {
		return true, "[RX-PACCHETTI-006] " + T("pacchetti.trattenuti", strings.Join(resta, ", ")), nil
	}
	return true, "the new packages are gone", nil
}

// trattenuti: dei pacchetti NUOVI da togliere, quelli che si possono togliere e quelli che restano
// perché qualcosa che resta li chiede — un pacchetto AGGIORNATO dallo stesso passo, o un programma
// installato dopo.
// Toglierli si porterebbe via anche lui (`[M]` 30 set, leap16-kde: `zypper rm` di libx264 & c.
// trascinava 53 pacchetti, Plasma compreso). ⇒ Non si tolgono, e si dichiarano (§6.6.4: quel che
// resta di indiretto si dice). Un pacchetto è trattenuto se toglierlo DA SOLO toglierebbe qualcosa
// fuori da «nostri» (i nuovi dello stesso passo): chi dipende da lui di rimbalzo lo trattiene anche
// lui, perché la simulazione del gestore segue tutta la catena.
func trattenuti(g Gestore, candidati, nostri []string, purge bool) (via, resta []string, err error) {
	if len(candidati) == 0 {
		return nil, nil, nil
	}
	altri, err := g.SimulaTogli(candidati, purge)
	if err != nil {
		return nil, nil, err
	}
	if len(fuoriDa(altri, nostri)) == 0 {
		return candidati, nil, nil
	}
	for _, n := range candidati {
		a, err := g.SimulaTogli([]string{n}, purge)
		if err != nil {
			return nil, nil, err
		}
		if len(fuoriDa(a, nostri)) > 0 {
			resta = append(resta, n+" ("+T("pacchetti.chiesto_da", strings.Join(fuoriDa(a, nostri), ", "))+")")
		} else {
			via = append(via, n)
		}
	}
	return via, resta, nil
}

// Indirette: i pacchetti AGGIORNATI per noi restano aggiornati (§6.6.4): si dichiarano.
func (a *pacchetti) Indirette(prima json.RawMessage) []string {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil {
		return nil
	}
	var r []string
	for _, x := range p.Insieme {
		if x.Esito == "upgraded" {
			r = append(r, x.Nome+" "+x.Prima+" → "+x.Versione)
		}
	}
	return r
}
