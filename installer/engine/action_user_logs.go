package engine

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

// togli-registri-utente (the user's decision, 1 Oct 2026, which closes the open item of phases/17
// §13.1): on uninstallation, in ALL homes, REMOTIX's session log is removed —
// `~/.local/state/remotix/session.log` (session.c) — and the folder `~/.local/state/remotix/` if
// it remains empty. ⛔ Only that, nothing else in the homes. The paths are declared in the plan (the
// «declared» ones) and in the certificate (the check's detail). EXACT reversibility: the files are
// saved in the operation's folder and, if the uninstallation is cancelled, put back byte
// by byte, with permissions and owner.

func init() { registerType("remove-user-logs", newRemoveLogs) }

const (
	userStateDir = ".local/state/remotix"
	sessionFile  = "session.log"
)

// UserLogs: the session logs that are in the homes NOW (absolute paths, in
// order), read from /etc/passwd: every account with a home, root included.
func UserLogs(a *Environment) []string {
	f, err := os.ReadFile(a.P("/etc/passwd"))
	if err != nil {
		return nil
	}
	var r []string
	seen_items := map[string]bool{}
	for _, line := range strings.Split(string(f), "\n") {
		c := strings.Split(line, ":")
		if len(c) < 7 || c[5] == "" || c[5] == "/" || seen_items[c[5]] {
			continue
		}
		seen_items[c[5]] = true
		p := filepath.Join(c[5], userStateDir, sessionFile)
		if st, err := os.Lstat(a.P(p)); err == nil && st.Mode().IsRegular() {
			r = append(r, p)
		}
	}
	return r
}

// PlanRemoveLogs prepares the plan's step, with the paths found at planning time.
func PlanRemoveLogs(id string, paths []string) PlanAction {
	listing := T("az.registri.nessuno")
	if len(paths) > 0 {
		listing = strings.Join(paths, ", ")
	}
	return PlanAction{
		ID: id, Type: "remove-user-logs",
		Parameters:     map[string]string{},
		Description:   T("az.registri", "~/"+userStateDir+"/"+sessionFile, listing),
		ComeSiFa:      T("az.registri.fa", "~/"+userStateDir),
		HowToVerify:   T("az.registri.verifica"),
		HowToUndo:     T("az.registri.annulla"),
		Reversibility: EXACT,
	}
}

type removeLogs struct{}

func newRemoveLogs(PlanAction) (Action, error) { return &removeLogs{}, nil }

// savedLog: a file as it was, and its folder (to put it back if it was removed).
type savedLog struct {
	RoutePath   string `json:"path"`
	Sha         string `json:"sha256"`
	Modo        string `json:"mode"`
	Uid         int    `json:"uid"`
	Gid         int    `json:"gid"`
	Save string `json:"backup"` // relative to the operation's folder
	DirMode     string `json:"dir_mode"`
	DirUid      int    `json:"dir_uid"`
	DirGid      int    `json:"dir_gid"`
}

type beforeLogs struct {
	Origine Origine    `json:"origin"`
	File    []savedLog `json:"file,omitempty"`
}

func (t *removeLogs) Constraints(*Context) ([]string, error) { return nil, nil }

func (t *removeLogs) Snapshot(c *Context) (json.RawMessage, Origine, error) {
	p := beforeLogs{Origine: PREEXISTING}
	for i, fpath := range UserLogs(c.Env) {
		dest := c.Env.P(fpath)
		_, sha, mode, uid, gid, err := stateFile(dest)
		if err != nil {
			return nil, "", err
		}
		b, err := os.ReadFile(dest)
		if err != nil {
			return nil, "", err
		}
		cart := filepath.Join(c.Folder, "backups")
		if err := os.MkdirAll(cart, 0o700); err != nil {
			return nil, "", err
		}
		s := savedLog{RoutePath: fpath, Sha: sha, Modo: fmt.Sprintf("%04o", mode), Uid: uid, Gid: gid,
			Save: filepath.Join("backups", c.P.ID+"-"+strconv.Itoa(i)+".before")}
		if err := WriteAtomic(filepath.Join(c.Folder, s.Save), b, 0o600); err != nil {
			return nil, "", err
		}
		if st, err := os.Stat(filepath.Dir(dest)); err == nil {
			s.DirMode = fmt.Sprintf("%04o", st.Mode().Perm())
			if sys, ok := st.Sys().(*syscall.Stat_t); ok {
				s.DirUid, s.DirGid = int(sys.Uid), int(sys.Gid)
			}
		}
		p.File = append(p.File, s)
	}
	if len(p.File) > 0 {
		p.Origine = DIRECT
	}
	return jsonDi(p), p.Origine, nil
}

func (t *removeLogs) load(before json.RawMessage) (beforeLogs, error) {
	var p beforeLogs
	err := json.Unmarshal(before, &p)
	return p, err
}

// Do removes the photographed files, and each one's folder only if it remains empty. Idempotent.
func (t *removeLogs) Do(c *Context, before json.RawMessage) error {
	p, err := t.load(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	for _, s := range p.File {
		dest := c.Env.P(s.RoutePath)
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

// amount: of the photographed files, how many are still there (and which).
func (t *removeLogs) amount(c *Context, p beforeLogs) (still, removed []string) {
	for _, s := range p.File {
		if _, err := os.Lstat(c.Env.P(s.RoutePath)); err == nil {
			still = append(still, s.RoutePath)
		} else {
			removed = append(removed, s.RoutePath)
		}
	}
	return
}

func (t *removeLogs) Check(c *Context, before json.RawMessage) (Outcome, string, error) {
	p, err := t.load(before)
	if err != nil {
		return "", "", err
	}
	if p.Origine == PREEXISTING {
		return COMPLETE, T("az.registri.nessuno"), nil
	}
	still, removed := t.amount(c, p)
	switch {
	case len(still) == 0:
		return COMPLETE, T("az.registri.removed", strings.Join(removed, ", ")), nil
	case len(removed) == 0:
		return ABSENT, T("az.registri.still", strings.Join(still, ", ")), nil
	}
	return A_META, T("az.registri.still", strings.Join(still, ", ")), nil
}

// Rollback puts the saved files (and the folder, as it was) back where they are missing.
func (t *removeLogs) Rollback(c *Context, before json.RawMessage) error {
	p, err := t.load(before)
	if err != nil || p.Origine == PREEXISTING {
		return err
	}
	for _, s := range p.File {
		dest := c.Env.P(s.RoutePath)
		if path_exists, sha, _, _, _, err := stateFile(dest); err != nil {
			return err
		} else if path_exists && sha == s.Sha {
			continue
		} else if path_exists {
			return Error("RX-FILE-001", s.RoutePath)
		}
		dir := filepath.Dir(dest)
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			m, _ := strconv.ParseUint(notEmpty(s.DirMode, "0700"), 8, 32)
			if err := os.MkdirAll(dir, os.FileMode(m)); err != nil {
				return err
			}
			os.Chmod(dir, os.FileMode(m))
			if os.Geteuid() == 0 {
				if err := os.Lchown(dir, s.DirUid, s.DirGid); err != nil {
					return err
				}
			}
		}
		b, err := os.ReadFile(filepath.Join(c.Folder, s.Save))
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

func (t *removeLogs) RolledBack(c *Context, before json.RawMessage) (bool, string, error) {
	p, err := t.load(before)
	if err != nil {
		return false, "", err
	}
	if p.Origine == PREEXISTING {
		return true, T("az.registri.nessuno"), nil
	}
	for _, s := range p.File {
		path_exists, sha, _, _, _, err := stateFile(c.Env.P(s.RoutePath))
		if err != nil {
			return false, "", err
		}
		if !path_exists || sha != s.Sha {
			return false, s.RoutePath + ": " + T("az.registri.non_rimesso"), nil
		}
	}
	return true, T("az.registri.rimessi"), nil
}
