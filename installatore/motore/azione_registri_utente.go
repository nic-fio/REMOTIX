package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

// togli-registri-utente (decisione dell'utente, 1 ott 2026, che chiude la voce aperta di fasi/17
// §13.1): alla disinstallazione si toglie, in TUTTE le case, il registro della sessione di REMOTIX —
// `~/.local/state/remotix/sessione.log` (sessione.c) — e la cartella `~/.local/state/remotix/` se
// resta vuota. ⛔ Solo quello, nient'altro nelle case. I percorsi si dichiarano nel piano (le
// «dichiarate») e nel certificato (il dettaglio del controllo). Reversibilità ESATTA: i file si
// salvano nella cartella dell'operazione e, se la disinstallazione si annulla, si rimettono byte
// per byte, coi permessi e il proprietario.

func init() { registraTipo("togli-registri-utente", nuovaTogliRegistri) }

const (
	cartellaStatoUtente = ".local/state/remotix"
	fileSessione        = "sessione.log"
)

// RegistriUtente: i registri di sessione che ci sono ADESSO nelle case (percorsi assoluti, in
// ordine), lette da /etc/passwd: ogni conto con una casa, root compreso.
func RegistriUtente(a *Ambiente) []string {
	f, err := os.ReadFile(a.P("/etc/passwd"))
	if err != nil {
		return nil
	}
	var r []string
	visti := map[string]bool{}
	for _, riga := range strings.Split(string(f), "\n") {
		c := strings.Split(riga, ":")
		if len(c) < 7 || c[5] == "" || c[5] == "/" || visti[c[5]] {
			continue
		}
		visti[c[5]] = true
		p := filepath.Join(c[5], cartellaStatoUtente, fileSessione)
		if st, err := os.Lstat(a.P(p)); err == nil && st.Mode().IsRegular() {
			r = append(r, p)
		}
	}
	return r
}

// PianoTogliRegistri prepara il passo del piano, coi percorsi trovati al momento del piano.
func PianoTogliRegistri(id string, percorsi []string) AzionePiano {
	elenco := T("az.registri.nessuno")
	if len(percorsi) > 0 {
		elenco = strings.Join(percorsi, ", ")
	}
	return AzionePiano{
		ID: id, Tipo: "togli-registri-utente",
		Parametri:      map[string]string{},
		Descrizione:    T("az.registri", "~/"+cartellaStatoUtente+"/"+fileSessione, elenco),
		ComeSiFa:       T("az.registri.fa", "~/"+cartellaStatoUtente),
		ComeSiVerifica: T("az.registri.verifica"),
		ComeSiAnnulla:  T("az.registri.annulla"),
		Reversibilita:  ESATTA,
	}
}

type togliRegistri struct{}

func nuovaTogliRegistri(AzionePiano) (Azione, error) { return &togliRegistri{}, nil }

// registroSalvato: un file com'era, e la sua cartella (per rimetterla se si è tolta).
type registroSalvato struct {
	Percorso     string `json:"percorso"`
	Sha          string `json:"sha256"`
	Modo         string `json:"modo"`
	Uid          int    `json:"uid"`
	Gid          int    `json:"gid"`
	Salvataggio  string `json:"salvataggio"` // relativo alla cartella dell'operazione
	CartellaModo string `json:"cartella_modo"`
	CartellaUid  int    `json:"cartella_uid"`
	CartellaGid  int    `json:"cartella_gid"`
}

type primaRegistri struct {
	Origine Origine           `json:"origine"`
	File    []registroSalvato `json:"file,omitempty"`
}

func (t *togliRegistri) Vincoli(*Contesto) ([]string, error) { return nil, nil }

func (t *togliRegistri) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	p := primaRegistri{Origine: PREESISTENTE}
	for i, percorso := range RegistriUtente(c.Amb) {
		dest := c.Amb.P(percorso)
		_, sha, modo, uid, gid, err := statoFile(dest)
		if err != nil {
			return nil, "", err
		}
		b, err := os.ReadFile(dest)
		if err != nil {
			return nil, "", err
		}
		cart := filepath.Join(c.Cartella, "salvataggi")
		if err := os.MkdirAll(cart, 0o700); err != nil {
			return nil, "", err
		}
		s := registroSalvato{Percorso: percorso, Sha: sha, Modo: fmt.Sprintf("%04o", modo), Uid: uid, Gid: gid,
			Salvataggio: filepath.Join("salvataggi", c.P.ID+"-"+strconv.Itoa(i)+".prima")}
		if err := ScriviAtomico(filepath.Join(c.Cartella, s.Salvataggio), b, 0o600); err != nil {
			return nil, "", err
		}
		if st, err := os.Stat(filepath.Dir(dest)); err == nil {
			s.CartellaModo = fmt.Sprintf("%04o", st.Mode().Perm())
			if sys, ok := st.Sys().(*syscall.Stat_t); ok {
				s.CartellaUid, s.CartellaGid = int(sys.Uid), int(sys.Gid)
			}
		}
		p.File = append(p.File, s)
	}
	if len(p.File) > 0 {
		p.Origine = DIRETTA
	}
	return jsonDi(p), p.Origine, nil
}

func (t *togliRegistri) leggi(prima json.RawMessage) (primaRegistri, error) {
	var p primaRegistri
	err := json.Unmarshal(prima, &p)
	return p, err
}

// Fai toglie i file fotografati, e la cartella di ciascuno solo se resta vuota. Idempotente.
func (t *togliRegistri) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := t.leggi(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	for _, s := range p.File {
		dest := c.Amb.P(s.Percorso)
		if err := os.Remove(dest); err != nil && !os.IsNotExist(err) {
			return err
		}
		SincronizzaCartella(filepath.Dir(dest))
		if err := os.Remove(filepath.Dir(dest)); err == nil { // solo se vuota
			SincronizzaCartella(filepath.Dir(filepath.Dir(dest)))
		}
	}
	return nil
}

// quanti: dei file fotografati, quanti ci sono ancora (e quali).
func (t *togliRegistri) quanti(c *Contesto, p primaRegistri) (ancora, tolti []string) {
	for _, s := range p.File {
		if _, err := os.Lstat(c.Amb.P(s.Percorso)); err == nil {
			ancora = append(ancora, s.Percorso)
		} else {
			tolti = append(tolti, s.Percorso)
		}
	}
	return
}

func (t *togliRegistri) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	p, err := t.leggi(prima)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREESISTENTE {
		return COMPLETO, T("az.registri.nessuno"), nil
	}
	ancora, tolti := t.quanti(c, p)
	switch {
	case len(ancora) == 0:
		return COMPLETO, T("az.registri.tolti", strings.Join(tolti, ", ")), nil
	case len(tolti) == 0:
		return ASSENTE, T("az.registri.ancora", strings.Join(ancora, ", ")), nil
	}
	return A_META, T("az.registri.ancora", strings.Join(ancora, ", ")), nil
}

// Annulla rimette i file salvati (e la cartella, com'era) dove mancano.
func (t *togliRegistri) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := t.leggi(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	for _, s := range p.File {
		dest := c.Amb.P(s.Percorso)
		if esiste, sha, _, _, _, err := statoFile(dest); err != nil {
			return err
		} else if esiste && sha == s.Sha {
			continue
		} else if esiste {
			return Errore("RX-FILE-001", s.Percorso)
		}
		dir := filepath.Dir(dest)
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			m, _ := strconv.ParseUint(nonVuoto(s.CartellaModo, "0700"), 8, 32)
			if err := os.MkdirAll(dir, os.FileMode(m)); err != nil {
				return err
			}
			os.Chmod(dir, os.FileMode(m))
			if os.Geteuid() == 0 {
				if err := os.Lchown(dir, s.CartellaUid, s.CartellaGid); err != nil {
					return err
				}
			}
		}
		b, err := os.ReadFile(filepath.Join(c.Cartella, s.Salvataggio))
		if err != nil {
			return err
		}
		m, _ := strconv.ParseUint(s.Modo, 8, 32)
		tmp := filepath.Join(dir, "."+filepath.Base(dest)+".remotix-nuovo")
		if err := scriviDentro(c, dest, tmp, b, os.FileMode(m), s.Uid, s.Gid, c.P.ID); err != nil {
			return err
		}
	}
	return nil
}

func (t *togliRegistri) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := t.leggi(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, T("az.registri.nessuno"), nil
	}
	for _, s := range p.File {
		esiste, sha, _, _, _, err := statoFile(c.Amb.P(s.Percorso))
		if err != nil {
			return false, "", err
		}
		if !esiste || sha != s.Sha {
			return false, s.Percorso + ": " + T("az.registri.non_rimesso"), nil
		}
	}
	return true, T("az.registri.rimessi"), nil
}
