package motore

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// installa-pacchetti: la transazione del gestore di pacchetti (§6.0 regola 1, §6.6.6).
//
//   - Fotografa (prima dell'intenzione) = ACQUISITION: il file del piano si copia nella cache
//     dell'operazione e si confronta col suo sha256; il gestore RISOLVE la transazione, SCARICA
//     tutto e verifica; l'INSIEME RISOLTO (nome, versione, origine, sha256, nuovo/aggiornato) va
//     nell'intenzione del registro e in insieme-risolto.json. Una rete che cade qui ferma
//     l'operazione prima di installare qualunque cosa.
//   - Fai: il gestore installa quell'insieme DALLA CACHE, senza scaricare.
//   - Controlla: ogni pacchetto alla versione risolta ⇒ completo; nessuno dei nuovi ⇒ assente;
//     altrimenti (o il gestore a metà di una transazione) ⇒ a metà.
//   - Ripara (a metà, alla ripresa): il rimedio del gestore (dpkg --configure -a…), poi si rifà.
//   - Annulla: si tolgono i pacchetti NUOVI, e solo quelli (il gestore simula prima: se ne
//     toglierebbe altri, si ferma); quelli AGGIORNATI restano aggiornati e si dichiarano
//     (INDIRETTA, §6.6.4). Reversibilità AL_MEGLIO.
//
// parametri: file (percorsi di pacchetti locali, facoltativi, separati da virgola: una transazione
// sola — T6: remotix e remotix-selinux insieme), sha256 (uno per file, nello stesso ordine), nomi
// (separati da virgola, dai depositi), senza_grafica ("si" per il desktop: vedi azione_desktop.go).

func init() { registraTipo("installa-pacchetti", nuovaPacchetti) }

// PianoPacchettiDa: pacchetti presi da un deposito preciso (la libavcodec di Packman: su openSUSE
// sostituisce quella della distribuzione, e zypper lo fa solo con --from e il cambio di fornitore).
func PianoPacchettiDa(id, nomi, deposito string) AzionePiano {
	a := PianoPacchetti(id, "", "", nomi)
	a.Parametri["da"] = deposito
	return a
}

// PianoPacchetti prepara il passo del piano.
func PianoPacchetti(id, file, sha, nomi string) AzionePiano {
	var basi []string
	for _, f := range dividiVirgole(file) {
		basi = append(basi, filepath.Base(f))
	}
	cosa := strings.TrimSpace(strings.Join(basi, " ") + " " + nomi)
	return AzionePiano{
		ID: id, Tipo: "installa-pacchetti",
		Parametri:      map[string]string{"file": file, "sha256": sha, "nomi": nomi},
		Descrizione:    T("az.pacchetti", cosa),
		ComeSiFa:       T("az.pacchetti.fa"),
		ComeSiVerifica: T("az.pacchetti.verifica"),
		ComeSiAnnulla:  T("az.pacchetti.annulla"),
		Reversibilita:  AL_MEGLIO,
	}
}

type pacchetti struct {
	da           string   // un deposito da cui prenderli (zypper: --from, cambiando fornitore)
	file, sha    []string // i pacchetti locali e i loro sha256, nello stesso ordine
	nomi         []string
	senzaGrafica bool
}

type primaPacchetti struct {
	Origine Origine       `json:"origine"`
	Gestore string        `json:"gestore"`
	Cache   string        `json:"cache"`
	File    string        `json:"file,omitempty"`       // il file nella cache (il primo)
	Altri   []string      `json:"altri_file,omitempty"` // gli altri file nella cache (T6)
	Nomi    []string      `json:"nomi"`
	Insieme []Artefatto   `json:"insieme_risolto"`
	Grafica *primaGrafica `json:"grafica,omitempty"`
}

func nuovaPacchetti(p AzionePiano) (Azione, error) {
	a := &pacchetti{file: dividiVirgole(p.Parametri["file"]), sha: dividiVirgole(p.Parametri["sha256"]),
		senzaGrafica: p.Parametri["senza_grafica"] == "si", da: p.Parametri["da"]}
	for _, n := range strings.Split(p.Parametri["nomi"], ",") {
		if n = strings.TrimSpace(n); n != "" {
			a.nomi = append(a.nomi, n)
		}
	}
	if len(a.file) != len(a.sha) {
		return nil, fmt.Errorf("installa-pacchetti: %d file e %d sha256", len(a.file), len(a.sha))
	}
	return a, nil
}

func (a *pacchetti) gestore(c *Contesto) (Gestore, error) {
	if c.Amb.Pacchetti == nil {
		return nil, Errore("RX-PACCHETTI-003", c.Amb.Famiglia)
	}
	if d, ok := c.Amb.Pacchetti.(interface{ Da(string) Gestore }); ok && a.da != "" {
		return d.Da(a.da), nil
	}
	return c.Amb.Pacchetti, nil
}

func (a *pacchetti) Vincoli(c *Contesto) ([]string, error) {
	// il desktop: lo stato dei desktop è già nell'impronta (desktop.* del profilo), e il passo
	// cambia con la RISPOSTA alla scelta (approva --desktop): non deve cambiare l'impronta
	if a.senzaGrafica {
		return nil, nil
	}
	g, err := a.gestore(c)
	if err != nil {
		return nil, err
	}
	var v []string
	for i, f := range a.file {
		v = append(v, "pacchetto-file:"+filepath.Base(f)+"="+a.sha[i])
	}
	ver, err := g.Versioni(a.nomi)
	if err != nil {
		return nil, err
	}
	for _, n := range a.nomi {
		v = append(v, "pacchetto:"+n+"="+nonVuoto(ver[n], "assente"))
	}
	return v, nil
}

// copia i file del piano nella cache dell'operazione, e controlla che siano quelli del piano.
func (a *pacchetti) inCache(c *Contesto) (string, []string, error) {
	// una cartella per passo: due passi di pacchetti nella stessa operazione non si mescolano
	// ([M] 30 set, fedora44-gnome: il codec e remotix nella stessa cartella ⇒ due versioni)
	cache := filepath.Join(c.Cartella, "cache", c.P.ID)
	if err := os.MkdirAll(cache, 0o700); err != nil {
		return "", nil, err
	}
	var r []string
	for i, f := range a.file {
		dest, err := unoInCache(c, cache, f, a.sha[i])
		if err != nil {
			return "", nil, err
		}
		r = append(r, dest)
	}
	if len(r) > 0 {
		if err := SincronizzaCartella(cache); err != nil {
			return "", nil, err
		}
	}
	return cache, r, nil
}

func unoInCache(c *Contesto, cache, file, sha string) (string, error) {
	dest := filepath.Join(cache, filepath.Base(file))
	if s, _ := Sha256File(dest); s == sha {
		return dest, nil
	}
	in, err := os.Open(c.Amb.P(file))
	if err != nil {
		return "", err
	}
	defer in.Close()
	tmp := dest + ".parziale"
	out, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o600)
	if err != nil {
		return "", err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		return "", err
	}
	out.Sync()
	out.Close()
	if s, _ := Sha256File(tmp); s != sha {
		os.Remove(tmp)
		return "", Errore("RX-PACCHETTI-001", file+": sha256 "+s)
	}
	return dest, os.Rename(tmp, dest)
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
	cache, file, err := a.inCache(c)
	if err != nil {
		return nil, "", err
	}
	ins, err := g.Risolvi(cache, file, a.nomi)
	if err != nil {
		return nil, "", Errore("RX-PACCHETTI-005", err.Error())
	}
	p := primaPacchetti{Origine: PREESISTENTE, Gestore: g.Nome(), Cache: cache, Nomi: a.nomi, Insieme: ins}
	if len(file) > 0 {
		p.File, p.Altri = file[0], file[1:]
	}
	for _, x := range ins {
		if x.Esito != "presente" {
			p.Origine = DIRETTA
		}
	}
	if a.senzaGrafica {
		gr, err := fotografaGrafica(c)
		if err != nil {
			return nil, "", err
		}
		p.Grafica = gr
	}
	if err := ScriviJSON(filepath.Join(c.Cartella, "insieme-risolto-"+c.P.ID+".json"),
		map[string]any{"formato": Formato, "oggetto": "insieme-risolto", "azione": c.P.ID, "gestore": g.Nome(), "artefatti": ins}); err != nil {
		return nil, "", err
	}
	return jsonDi(p), p.Origine, nil
}

func leggiPrimaPacchetti(prima json.RawMessage) (primaPacchetti, error) {
	var p primaPacchetti
	err := json.Unmarshal(prima, &p)
	return p, err
}

func (p primaPacchetti) file() []string {
	if p.File == "" {
		return nil
	}
	return append([]string{p.File}, p.Altri...)
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
	if a.senzaGrafica && p.Grafica != nil {
		if err := p.Grafica.prima(c); err != nil {
			return err
		}
	}
	errI := g.Installa(p.Cache, p.file(), p.Nomi)
	if a.senzaGrafica && p.Grafica != nil {
		if err := p.Grafica.dopo(c); err != nil && errI == nil {
			errI = err
		}
	}
	return errI
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
	agg := versioniAggiornate(c.Cartella)
	for _, x := range p.Insieme {
		v := ver[x.Nome]
		if versioneUguale(v, x.Versione) || (agg[x.Nome] != "" && versioneUguale(v, agg[x.Nome])) {
			completi++
		}
		if x.Esito == "nuovo" && v != "" {
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
		return A_META, "il gestore è a metà: " + det, nil
	}
	completi, nuovi, err := a.conta(c, p)
	if err != nil {
		return "", "", err
	}
	if a.senzaGrafica && p.Grafica != nil {
		if ok, det := p.Grafica.aPosto(c); !ok && completi == len(p.Insieme) {
			return A_META, det, nil
		}
	}
	switch {
	case completi == len(p.Insieme):
		return COMPLETO, fmt.Sprintf("%d pacchetti alla versione risolta", completi), nil
	case nuovi == 0 && completi == 0:
		return ASSENTE, "nessuno dei pacchetti nuovi", nil
	case nuovi == 0:
		return ASSENTE, "nessuno dei pacchetti nuovi (gli aggiornati restano)", nil
	}
	return A_META, fmt.Sprintf("%d di %d", completi, len(p.Insieme)), nil
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
	var togli []string
	for _, x := range p.Insieme {
		if x.Esito == "nuovo" && ver[x.Nome] != "" {
			togli = append(togli, x.Nome)
		}
	}
	if len(togli) > 0 {
		if err := g.Togli(togli, c.Purge); err != nil {
			return err
		}
	}
	if a.senzaGrafica && p.Grafica != nil {
		return p.Grafica.rimetti(c)
	}
	return nil
}

func (a *pacchetti) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "c'erano già: non si toccano", nil
	}
	_, nuovi, err := a.conta(c, p)
	if err != nil {
		return false, "", err
	}
	if nuovi > 0 {
		return false, fmt.Sprintf("%d pacchetti nuovi ancora installati", nuovi), nil
	}
	if a.senzaGrafica && p.Grafica != nil {
		if ok, det := p.Grafica.comePrima(c); !ok {
			return false, det, nil
		}
	}
	return true, "i pacchetti nuovi non ci sono più", nil
}

// Indirette: i pacchetti AGGIORNATI per noi restano aggiornati (§6.6.4): si dichiarano.
func (a *pacchetti) Indirette(prima json.RawMessage) []string {
	p, err := leggiPrimaPacchetti(prima)
	if err != nil {
		return nil
	}
	var r []string
	for _, x := range p.Insieme {
		if x.Esito == "aggiornato" {
			r = append(r, x.Nome+" "+x.Prima+" → "+x.Versione)
		}
	}
	return r
}
