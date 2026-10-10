package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"syscall"
)

// scrivi-file: un file di configurazione, scritto sempre su un nome temporaneo e poi rinominato
// (mai a metà, §6.6.3). Reversibilità ESATTA: il contenuto di prima si salva nella cartella
// dell'operazione e si rimette byte per byte, coi permessi e il proprietario.
//
// parametri: percorso (assoluto), contenuto, modo (ottale, "0644"), uid e gid (predefiniti 0).

func init() { registraTipo("write-file", nuovaScriviFile) }

// PianoScriviFile prepara il passo del piano.
func PianoScriviFile(id, percorso, contenuto, modo string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "write-file",
		Parametri:      map[string]string{"path": percorso, "content": contenuto, "mode": modo},
		Descrizione:    T("az.file", percorso),
		ComeSiFa:       T("az.file.fa", "."+filepath.Base(percorso)+".remotix-nuovo"),
		ComeSiVerifica: T("az.file.verifica"),
		ComeSiAnnulla:  T("az.file.annulla"),
		Reversibilita:  ESATTA,
	}
}

type scriviFile struct {
	percorso  string
	contenuto []byte
	modo      os.FileMode
	uid, gid  int
}

type primaFile struct {
	Origine        Origine  `json:"origin"`
	Esisteva       bool     `json:"existed"`
	Sha            string   `json:"sha256,omitempty"`
	Modo           string   `json:"mode,omitempty"`
	Uid            int      `json:"uid"`
	Gid            int      `json:"gid"`
	Salvataggio    string   `json:"backup,omitempty"` // relativo alla cartella dell'operazione
	CartelleCreate []string `json:"created_dirs,omitempty"`
}

func nuovaScriviFile(p AzionePiano) (Azione, error) {
	s := &scriviFile{percorso: p.Parametri["path"], contenuto: []byte(p.Parametri["content"])}
	if !filepath.IsAbs(s.percorso) {
		return nil, fmt.Errorf("scrivi-file: path not absolute: %q", s.percorso)
	}
	m, err := strconv.ParseUint(nonVuoto(p.Parametri["mode"], "0644"), 8, 32)
	if err != nil {
		return nil, fmt.Errorf("scrivi-file: modo %q: %w", p.Parametri["mode"], err)
	}
	s.modo = os.FileMode(m)
	s.uid, _ = strconv.Atoi(nonVuoto(p.Parametri["uid"], "0"))
	s.gid, _ = strconv.Atoi(nonVuoto(p.Parametri["gid"], "0"))
	return s, nil
}

func (s *scriviFile) dest(c *Contesto) string { return c.Amb.P(s.percorso) }
func (s *scriviFile) tmp(c *Contesto) string {
	return filepath.Join(filepath.Dir(s.dest(c)), "."+filepath.Base(s.percorso)+".remotix-nuovo")
}

// stato del file adesso: esiste, sha, modo.
func statoFile(percorso string) (bool, string, os.FileMode, int, int, error) {
	st, err := os.Lstat(percorso)
	if os.IsNotExist(err) {
		return false, "", 0, 0, 0, nil
	}
	if err != nil {
		return false, "", 0, 0, 0, err
	}
	if !st.Mode().IsRegular() {
		return true, "", 0, 0, 0, Errore("RX-FILE-001", percorso+" is not a regular file (link or other): left untouched")
	}
	b, err := os.ReadFile(percorso)
	if err != nil {
		return false, "", 0, 0, 0, err
	}
	uid, gid := 0, 0
	if sys, ok := st.Sys().(*syscall.Stat_t); ok {
		uid, gid = int(sys.Uid), int(sys.Gid)
	}
	return true, Sha256(b), st.Mode().Perm(), uid, gid, nil
}

func (s *scriviFile) Vincoli(c *Contesto) ([]string, error) {
	esiste, sha, _, _, _, err := statoFile(s.dest(c))
	if err != nil {
		return nil, err
	}
	if !esiste {
		sha = "absent"
	}
	return []string{"file:" + s.percorso + "=" + sha}, nil
}

func (s *scriviFile) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	esiste, sha, modo, uid, gid, err := statoFile(s.dest(c))
	if err != nil {
		return nil, "", err
	}
	p := primaFile{Origine: DIRETTA, Esisteva: esiste, Sha: sha, Uid: uid, Gid: gid}
	if esiste {
		p.Modo = fmt.Sprintf("%04o", modo)
		if sha == Sha256(s.contenuto) && modo == s.modo {
			p.Origine = PREESISTENTE
			return jsonDi(p), p.Origine, nil
		}
		b, err := os.ReadFile(s.dest(c))
		if err != nil {
			return nil, "", err
		}
		cart := filepath.Join(c.Cartella, "backups")
		if err := os.MkdirAll(cart, 0o700); err != nil {
			return nil, "", err
		}
		p.Salvataggio = filepath.Join("backups", c.P.ID+".before")
		if err := ScriviAtomico(filepath.Join(c.Cartella, p.Salvataggio), b, 0o600); err != nil {
			return nil, "", err
		}
	}
	// le cartelle che mancano, dalla più alta
	for d := filepath.Dir(s.percorso); d != "/" && d != "."; d = filepath.Dir(d) {
		if _, err := os.Stat(c.Amb.P(d)); err == nil {
			break
		}
		p.CartelleCreate = append([]string{d}, p.CartelleCreate...)
	}
	return jsonDi(p), p.Origine, nil
}

// scriviDentro: temporaneo col nome fisso (così «controlla» lo riconosce: a metà), fsync,
// permessi, proprietario, rinomina, fsync della cartella.
func scriviDentro(c *Contesto, dest, tmp string, dati []byte, modo os.FileMode, uid, gid int, idAzione string) error {
	f, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o600)
	if err != nil {
		return err
	}
	if _, err := f.Write(dati); err != nil {
		f.Close()
		return err
	}
	if err := f.Chmod(modo); err != nil {
		f.Close()
		return err
	}
	if os.Geteuid() == 0 {
		if err := f.Chown(uid, gid); err != nil {
			f.Close()
			return err
		}
	}
	if err := f.Sync(); err != nil {
		f.Close()
		return err
	}
	if err := f.Close(); err != nil {
		return err
	}
	punto("file-a-meta", idAzione)
	if err := os.Rename(tmp, dest); err != nil {
		return err
	}
	return SincronizzaCartella(filepath.Dir(dest))
}

func (s *scriviFile) Fai(c *Contesto, prima json.RawMessage) error {
	var p primaFile
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	for _, d := range p.CartelleCreate {
		if err := os.Mkdir(c.Amb.P(d), 0o755); err != nil && !os.IsExist(err) {
			return err
		}
		if err := SincronizzaCartella(filepath.Dir(c.Amb.P(d))); err != nil {
			return err
		}
	}
	return scriviDentro(c, s.dest(c), s.tmp(c), s.contenuto, s.modo, s.uid, s.gid, c.P.ID)
}

// comePrima: il file è com'era prima dell'azione?
func (s *scriviFile) comePrima(c *Contesto, p primaFile) (bool, error) {
	esiste, sha, modo, _, _, err := statoFile(s.dest(c))
	if err != nil {
		return false, err
	}
	if !p.Esisteva {
		return !esiste, nil
	}
	return esiste && sha == p.Sha && fmt.Sprintf("%04o", modo) == p.Modo, nil
}

func (s *scriviFile) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
	var p primaFile
	if err := json.Unmarshal(prima, &p); err != nil {
		return "", "", err
	}
	esiste, sha, modo, _, _, err := statoFile(s.dest(c))
	if err != nil {
		return "", "", err
	}
	nostro := esiste && sha == Sha256(s.contenuto) && modo == s.modo
	if p.Origine == PREESISTENTE {
		if nostro {
			return COMPLETO, "already there, identical", nil
		}
		return ESTRANEO, "the file that was already there has been changed", nil
	}
	if _, err := os.Lstat(s.tmp(c)); err == nil {
		return A_META, "the temporary file is there: " + filepath.Base(s.tmp(c)), nil
	}
	if nostro {
		return COMPLETO, "sha256 " + sha[:12], nil
	}
	if ok, err := s.comePrima(c, p); err != nil {
		return "", "", err
	} else if ok {
		return ASSENTE, "as it was before", nil
	}
	return ESTRANEO, "neither our content nor the previous one", nil
}

func (s *scriviFile) Annulla(c *Contesto, prima json.RawMessage) error {
	var p primaFile
	if err := json.Unmarshal(prima, &p); err != nil {
		return err
	}
	if p.Origine == PREESISTENTE {
		return nil
	}
	if err := os.Remove(s.tmp(c)); err != nil && !os.IsNotExist(err) {
		return err
	}
	esiste, sha, modo, _, _, err := statoFile(s.dest(c))
	if err != nil {
		return err
	}
	nostro := esiste && sha == Sha256(s.contenuto) && modo == s.modo
	giaPrima, err := s.comePrima(c, p)
	if err != nil {
		return err
	}
	switch {
	case giaPrima:
	case !nostro:
		return Errore("RX-FILE-001", s.percorso)
	case p.Esisteva:
		b, err := os.ReadFile(filepath.Join(c.Cartella, p.Salvataggio))
		if err != nil {
			return err
		}
		m, _ := strconv.ParseUint(p.Modo, 8, 32)
		if err := scriviDentro(c, s.dest(c), s.tmp(c), b, os.FileMode(m), p.Uid, p.Gid, c.P.ID); err != nil {
			return err
		}
	default:
		if err := os.Remove(s.dest(c)); err != nil && !os.IsNotExist(err) {
			return err
		}
		if err := SincronizzaCartella(filepath.Dir(s.dest(c))); err != nil {
			return err
		}
	}
	for i := len(p.CartelleCreate) - 1; i >= 0; i-- {
		d := c.Amb.P(p.CartelleCreate[i])
		if err := os.Remove(d); err == nil {
			SincronizzaCartella(filepath.Dir(d))
		}
	}
	return nil
}

func (s *scriviFile) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	var p primaFile
	if err := json.Unmarshal(prima, &p); err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, "already there: left untouched", nil
	}
	if _, err := os.Lstat(s.tmp(c)); err == nil {
		return false, "the temporary file is still there", nil
	}
	ok, err := s.comePrima(c, p)
	if err != nil || !ok {
		return false, "the file is not as it was", err
	}
	for _, d := range p.CartelleCreate {
		if voci, err := os.ReadDir(c.Amb.P(d)); err == nil && len(voci) == 0 {
			return false, "the empty directory is still there: " + d, nil
		}
	}
	return true, "as it was before", nil
}
