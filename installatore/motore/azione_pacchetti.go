package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// installa-pacchetti: the package manager's transaction (§6.0 rule 1, §6.6.6; since 10 Oct
// 2026 without caches or sha256 of our own: «don't reinvent the wheel», DECISIONI §10.36).
//
//   - Fotografa (before the intention): the manager SIMULATES the transaction; the set (name, version,
//     origin, new/upgraded) goes into the log's intention and into resolved-set-<passo>.json.
//   - Fai: the manager installs — the files of the single package, with the dependencies from the
//     machine's repositories, downloaded and verified by it.
//   - Controlla: every package at the simulated version (or newer) ⇒ complete; none of the new ones ⇒
//     absent; otherwise (or the manager halfway through a transaction) ⇒ half-done.
//   - Ripara: the manager's remedy (dpkg --configure -a…), needed before undoing.
//   - Annulla: the NEW packages are removed, and only those (the manager simulates first: if it
//     would remove others, it holds them back); the UPGRADED ones stay upgraded and are declared
//     (INDIRETTA, §6.6.4). Reversibility AL_MEGLIO.
//
// parameters: file (paths of the .run's packages, comma-separated: a single transaction),
// names (comma-separated, from the machine's repositories).

func init() { registraTipo("install-packages", nuovaPacchetti) }

// PianoPacchetti prepares the plan's step.
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

// Vincoli: the versions installed now of the named packages, and the files of the single package (by
// name: the .run is one, and its sha256 guarantees it whole).
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

// veri: the paths of the files on the machine (in the tests, under the fake root).
func veri(c *Contesto, file []string) []string {
	var r []string
	for _, f := range file {
		r = append(r, c.Amb.P(f))
	}
	return r
}

// dividiVirgole: «a,b» ⇒ [a b]; empty ⇒ none.
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

// state of the set's packages, now.
func (a *pacchetti) conta(c *Contesto, p primaPacchetti) (completi, nuoviPresenti int, err error) {
	g, err := a.gestore(c)
	if err != nil {
		return 0, 0, err
	}
	ver, err := g.Versioni(nomiDi(p.Insieme))
	if err != nil {
		return 0, 0, err
	}
	// D14 (DECISIONI §10.23): REMOTIX and its dependencies are upgraded with the system. A package
	// of the set is «complete» at the resolved version, at a NEWER one (a system upgrade
	// brought it), or at the one recorded by the last `remotix-install aggiornato` (a rollback
	// done with the manager's commands)
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

// versioneUguale: dpkg says «1:2.3-1», rpm «2.3-1»; the epoch «0:» does not count.
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

// trattenuti: of the NEW packages to remove, those that can be removed and those that stay
// because something that stays requires them — a package UPGRADED by the same step, or a program
// installed later.
// Removing them would take that away too (`[M]` 30 Sep, leap16-kde: `zypper rm` of libx264 & co.
// dragged 53 packages, Plasma included). ⇒ They are not removed, and they are declared (§6.6.4: what
// remains indirectly is stated). A package is held back if removing it ALONE would remove something
// outside «ours» (the new ones of the same step): whoever depends on it in turn holds it back
// too, because the manager's simulation follows the whole chain.
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

// Indirette: the packages UPGRADED for us stay upgraded (§6.6.4): they are declared.
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
