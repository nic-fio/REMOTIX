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

// togli-registri-utente (the user's decision, 1 Oct 2026, which closes the open item of fasi/17
// §13.1): on uninstallation, in ALL homes, REMOTIX's session log is removed —
// `~/.local/state/remotix/sessione.log` (sessione.c) — and the folder `~/.local/state/remotix/` if
// it remains empty. ⛔ Only that, nothing else in the homes. The paths are declared in the plan (the
// «declared» ones) and in the certificate (the check's detail). EXACT reversibility: the files are
// saved in the operation's folder and, if the uninstallation is cancelled, put back byte
// by byte, with permissions and owner.

func init() { registraTipo("remove-user-logs", newRemoveLogs) }

const (
	userStateDir = ".local/state/remotix"
	sessionFile  = "sessione.log"
)

// UserLogs: the session logs that are in the homes NOW (absolute paths, in
// order), read from /etc/passwd: every account with a home, root included.
func UserLogs(a *Ambiente) []string {
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
		p := filepath.Join(c[5], userStateDir, sessionFile)
		if st, err := os.Lstat(a.P(p)); err == nil && st.Mode().IsRegular() {
			r = append(r, p)
		}
	}
	return r
}

// PlanRemoveLogs prepares the plan's step, with the paths found at planning time.
func PlanRemoveLogs(id string, paths []string) AzionePiano {
	elenco := T("az.registri.nessuno")
	if len(paths) > 0 {
		elenco = strings.Join(paths, ", ")
	}
	return AzionePiano{
		ID: id, Tipo: "remove-user-logs",
		Parametri:     map[string]string{},
		Description:   T("az.registri", "~/"+userStateDir+"/"+sessionFile, elenco),
		ComeSiFa:      T("az.registri.fa", "~/"+userStateDir),
		HowToVerify:   T("az.registri.verifica"),
		HowToUndo:     T("az.registri.annulla"),
		Reversibilita: ESATTA,
	}
}

type removeLogs struct{}

func newRemoveLogs(AzionePiano) (Azione, error) { return &removeLogs{}, nil }

// savedLog: a file as it was, and its folder (to put it back if it was removed).
type savedLog struct {
	Path       string `json:"path"`
	Sha        string `json:"sha256"`
	Modo       string `json:"mode"`
	Uid        int    `json:"uid"`
	Gid        int    `json:"gid"`
	Save       string `json:"backup"` // relative to the operation's folder
	FolderMode string `json:"dir_mode"`
	FolderUid  int    `json:"dir_uid"`
	FolderGid  int    `json:"dir_gid"`
}

type beforeLogs struct {
	Origine Origine    `json:"origin"`
	File    []savedLog `json:"file,omitempty"`
}

func (t *removeLogs) Vincoli(*Contesto) ([]string, error) { return nil, nil }

func (t *removeLogs) Fotografa(c *Contesto) (json.RawMessage, Origine, error) {
	p := beforeLogs{Origine: PREESISTENTE}
	for i, percorso := range UserLogs(c.Amb) {
		dest := c.Amb.P(percorso)
		_, sha, modo, uid, gid, err := stateFile(dest)
		if err != nil {
			return nil, "", err
		}
		b, err := os.ReadFile(dest)
		if err != nil {
			return nil, "", err
		}
		cart := filepath.Join(c.Cartella, "backups")
		if err := os.MkdirAll(cart, 0o700); err != nil {
			return nil, "", err
		}
		s := savedLog{Path: percorso, Sha: sha, Modo: fmt.Sprintf("%04o", modo), Uid: uid, Gid: gid,
			Save: filepath.Join("backups", c.P.ID+"-"+strconv.Itoa(i)+".before")}
		if err := ScriviAtomico(filepath.Join(c.Cartella, s.Save), b, 0o600); err != nil {
			return nil, "", err
		}
		if st, err := os.Stat(filepath.Dir(dest)); err == nil {
			s.FolderMode = fmt.Sprintf("%04o", st.Mode().Perm())
			if sys, ok := st.Sys().(*syscall.Stat_t); ok {
				s.FolderUid, s.FolderGid = int(sys.Uid), int(sys.Gid)
			}
		}
		p.File = append(p.File, s)
	}
	if len(p.File) > 0 {
		p.Origine = DIRETTA
	}
	return jsonDi(p), p.Origine, nil
}

func (t *removeLogs) leggi(prima json.RawMessage) (beforeLogs, error) {
	var p beforeLogs
	err := json.Unmarshal(prima, &p)
	return p, err
}

// Fai removes the photographed files, and each one's folder only if it remains empty. Idempotent.
func (t *removeLogs) Fai(c *Contesto, prima json.RawMessage) error {
	p, err := t.leggi(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	for _, s := range p.File {
		dest := c.Amb.P(s.Path)
		if err := os.Remove(dest); err != nil && !os.IsNotExist(err) {
			return err
		}
		SyncFolder(filepath.Dir(dest))
		if err := os.Remove(filepath.Dir(dest)); err == nil { // only if empty
			SyncFolder(filepath.Dir(filepath.Dir(dest)))
		}
	}
	return nil
}

// quanti: of the photographed files, how many are still there (and which).
func (t *removeLogs) quanti(c *Contesto, p beforeLogs) (ancora, tolti []string) {
	for _, s := range p.File {
		if _, err := os.Lstat(c.Amb.P(s.Path)); err == nil {
			ancora = append(ancora, s.Path)
		} else {
			tolti = append(tolti, s.Path)
		}
	}
	return
}

func (t *removeLogs) Controlla(c *Contesto, prima json.RawMessage) (Esito, string, error) {
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

// Annulla puts the saved files (and the folder, as it was) back where they are missing.
func (t *removeLogs) Annulla(c *Contesto, prima json.RawMessage) error {
	p, err := t.leggi(prima)
	if err != nil || p.Origine == PREESISTENTE {
		return err
	}
	for _, s := range p.File {
		dest := c.Amb.P(s.Path)
		if esiste, sha, _, _, _, err := stateFile(dest); err != nil {
			return err
		} else if esiste && sha == s.Sha {
			continue
		} else if esiste {
			return Errore("RX-FILE-001", s.Path)
		}
		dir := filepath.Dir(dest)
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			m, _ := strconv.ParseUint(notEmpty(s.FolderMode, "0700"), 8, 32)
			if err := os.MkdirAll(dir, os.FileMode(m)); err != nil {
				return err
			}
			os.Chmod(dir, os.FileMode(m))
			if os.Geteuid() == 0 {
				if err := os.Lchown(dir, s.FolderUid, s.FolderGid); err != nil {
					return err
				}
			}
		}
		b, err := os.ReadFile(filepath.Join(c.Cartella, s.Save))
		if err != nil {
			return err
		}
		m, _ := strconv.ParseUint(s.Modo, 8, 32)
		tmp := filepath.Join(dir, "."+filepath.Base(dest)+".remotix-nuovo")
		if err := writeInside(c, dest, tmp, b, os.FileMode(m), s.Uid, s.Gid, c.P.ID); err != nil {
			return err
		}
	}
	return nil
}

func (t *removeLogs) Annullata(c *Contesto, prima json.RawMessage) (bool, string, error) {
	p, err := t.leggi(prima)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREESISTENTE {
		return true, T("az.registri.nessuno"), nil
	}
	for _, s := range p.File {
		esiste, sha, _, _, _, err := stateFile(c.Amb.P(s.Path))
		if err != nil {
			return false, "", err
		}
		if !esiste || sha != s.Sha {
			return false, s.Path + ": " + T("az.registri.non_rimesso"), nil
		}
	}
	return true, T("az.registri.rimessi"), nil
}
