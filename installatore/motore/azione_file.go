package motore

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"syscall"
)

// scrivi-file: a configuration file, always written to a temporary name and then renamed
// (never half-written, §6.6.3). EXACT reversibility: the previous content is saved in the operation's
// folder and put back byte by byte, with permissions and owner.
//
// parameters: fpath (absolute), content, manner (octal, "0644"), uid and gid (default 0).

func init() { registerType("write-file", newWriteFile) }

// PlanWriteFile prepares the plan's step.
func PlanWriteFile(id, fpath, content, manner string) PlanAction {
	return PlanAction{
		ID: id, Kind: "write-file",
		Parameters:    map[string]string{"path": fpath, "content": content, "mode": manner},
		Description:   T("az.file", fpath),
		ComeSiFa:      T("az.file.fa", "."+filepath.Base(fpath)+".remotix-nuovo"),
		HowToVerify:   T("az.file.verify"),
		HowToUndo:     T("az.file.rollback"),
		Reversibility: EXACT,
	}
}

type writeFile struct {
	fpath    string
	content  []byte
	manner   os.FileMode
	uid, gid int
}

type beforeFile struct {
	Origin      Origin   `json:"origin"`
	Existed     bool     `json:"existed"`
	Sha         string   `json:"sha256,omitempty"`
	Manner      string   `json:"mode,omitempty"`
	Uid         int      `json:"uid"`
	Gid         int      `json:"gid"`
	Save        string   `json:"backup,omitempty"` // relative to the operation's folder
	CreatedDirs []string `json:"created_dirs,omitempty"`
}

func newWriteFile(p PlanAction) (Action, error) {
	s := &writeFile{fpath: p.Parameters["path"], content: []byte(p.Parameters["content"])}
	if !filepath.IsAbs(s.fpath) {
		return nil, fmt.Errorf("scrivi-file: path not absolute: %q", s.fpath)
	}
	m, err := strconv.ParseUint(notEmpty(p.Parameters["mode"], "0644"), 8, 32)
	if err != nil {
		return nil, fmt.Errorf("scrivi-file: manner %q: %w", p.Parameters["mode"], err)
	}
	s.manner = os.FileMode(m)
	s.uid, _ = strconv.Atoi(notEmpty(p.Parameters["uid"], "0"))
	s.gid, _ = strconv.Atoi(notEmpty(p.Parameters["gid"], "0"))
	return s, nil
}

func (s *writeFile) dest(c *Context) string { return c.Amb.P(s.fpath) }
func (s *writeFile) tmp(c *Context) string {
	return filepath.Join(filepath.Dir(s.dest(c)), "."+filepath.Base(s.fpath)+".remotix-nuovo")
}

// state of the file now: exists, sha, mode.
func stateFile(fpath string) (bool, string, os.FileMode, int, int, error) {
	st, err := os.Lstat(fpath)
	if os.IsNotExist(err) {
		return false, "", 0, 0, 0, nil
	}
	if err != nil {
		return false, "", 0, 0, 0, err
	}
	if !st.Mode().IsRegular() {
		return true, "", 0, 0, 0, Error("RX-FILE-001", fpath+" is not a regular file (link or other): left untouched")
	}
	b, err := os.ReadFile(fpath)
	if err != nil {
		return false, "", 0, 0, 0, err
	}
	uid, gid := 0, 0
	if sys, ok := st.Sys().(*syscall.Stat_t); ok {
		uid, gid = int(sys.Uid), int(sys.Gid)
	}
	return true, Sha256(b), st.Mode().Perm(), uid, gid, nil
}

func (s *writeFile) Constraints(c *Context) ([]string, error) {
	path_exists, sha, _, _, _, err := stateFile(s.dest(c))
	if err != nil {
		return nil, err
	}
	if !path_exists {
		sha = "absent"
	}
	return []string{"file:" + s.fpath + "=" + sha}, nil
}

func (s *writeFile) Snapshot(c *Context) (json.RawMessage, Origin, error) {
	path_exists, sha, manner, uid, gid, err := stateFile(s.dest(c))
	if err != nil {
		return nil, "", err
	}
	p := beforeFile{Origin: DIRECT, Existed: path_exists, Sha: sha, Uid: uid, Gid: gid}
	if path_exists {
		p.Manner = fmt.Sprintf("%04o", manner)
		if sha == Sha256(s.content) && manner == s.manner {
			p.Origin = PREEXISTING
			return jsonDi(p), p.Origin, nil
		}
		b, err := os.ReadFile(s.dest(c))
		if err != nil {
			return nil, "", err
		}
		cart := filepath.Join(c.Folder, "backups")
		if err := os.MkdirAll(cart, 0o700); err != nil {
			return nil, "", err
		}
		p.Save = filepath.Join("backups", c.P.ID+".before")
		if err := WriteAtomic(filepath.Join(c.Folder, p.Save), b, 0o600); err != nil {
			return nil, "", err
		}
	}
	// the missing folders, from the highest
	for d := filepath.Dir(s.fpath); d != "/" && d != "."; d = filepath.Dir(d) {
		if _, err := os.Stat(c.Amb.P(d)); err == nil {
			break
		}
		p.CreatedDirs = append([]string{d}, p.CreatedDirs...)
	}
	return jsonDi(p), p.Origin, nil
}

// writeInside: temporary with the fixed name (so «controlla» recognises it: half-done), fsync,
// permissions, owner, rename, fsync of the folder.
func writeInside(c *Context, dest, tmp string, data_v []byte, manner os.FileMode, uid, gid int, actionId string) error {
	f, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o600)
	if err != nil {
		return err
	}
	if _, err := f.Write(data_v); err != nil {
		f.Close()
		return err
	}
	if err := f.Chmod(manner); err != nil {
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
	spot("file-a-meta", actionId)
	if err := os.Rename(tmp, dest); err != nil {
		return err
	}
	return SyncFolder(filepath.Dir(dest))
}

func (s *writeFile) Do(c *Context, before json.RawMessage) error {
	var p beforeFile
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origin == PREEXISTING {
		return nil
	}
	for _, d := range p.CreatedDirs {
		if err := os.Mkdir(c.Amb.P(d), 0o755); err != nil && !os.IsExist(err) {
			return err
		}
		if err := SyncFolder(filepath.Dir(c.Amb.P(d))); err != nil {
			return err
		}
	}
	return writeInside(c, s.dest(c), s.tmp(c), s.content, s.manner, s.uid, s.gid, c.P.ID)
}

// asBefore: is the file as it was before the action?
func (s *writeFile) asBefore(c *Context, p beforeFile) (bool, error) {
	path_exists, sha, manner, _, _, err := stateFile(s.dest(c))
	if err != nil {
		return false, err
	}
	if !p.Existed {
		return !path_exists, nil
	}
	return path_exists && sha == p.Sha && fmt.Sprintf("%04o", manner) == p.Manner, nil
}

func (s *writeFile) Verify(c *Context, before json.RawMessage) (Outcome, string, error) {
	var p beforeFile
	if err := json.Unmarshal(before, &p); err != nil {
		return "", "", err
	}
	path_exists, sha, manner, _, _, err := stateFile(s.dest(c))
	if err != nil {
		return "", "", err
	}
	our := path_exists && sha == Sha256(s.content) && manner == s.manner
	if p.Origin == PREEXISTING {
		if our {
			return COMPLETE, "already there, identical", nil
		}
		return FOREIGN, "the file that was already there has been changed", nil
	}
	if _, err := os.Lstat(s.tmp(c)); err == nil {
		return A_META, "the temporary file is there: " + filepath.Base(s.tmp(c)), nil
	}
	if our {
		return COMPLETE, "sha256 " + sha[:12], nil
	}
	if ok, err := s.asBefore(c, p); err != nil {
		return "", "", err
	} else if ok {
		return ABSENT, "as it was before", nil
	}
	return FOREIGN, "neither our content nor the previous one", nil
}

func (s *writeFile) Rollback(c *Context, before json.RawMessage) error {
	var p beforeFile
	if err := json.Unmarshal(before, &p); err != nil {
		return err
	}
	if p.Origin == PREEXISTING {
		return nil
	}
	if err := os.Remove(s.tmp(c)); err != nil && !os.IsNotExist(err) {
		return err
	}
	path_exists, sha, manner, _, _, err := stateFile(s.dest(c))
	if err != nil {
		return err
	}
	our := path_exists && sha == Sha256(s.content) && manner == s.manner
	alreadyBefore, err := s.asBefore(c, p)
	if err != nil {
		return err
	}
	switch {
	case alreadyBefore:
	case !our:
		return Error("RX-FILE-001", s.fpath)
	case p.Existed:
		b, err := os.ReadFile(filepath.Join(c.Folder, p.Save))
		if err != nil {
			return err
		}
		m, _ := strconv.ParseUint(p.Manner, 8, 32)
		if err := writeInside(c, s.dest(c), s.tmp(c), b, os.FileMode(m), p.Uid, p.Gid, c.P.ID); err != nil {
			return err
		}
	default:
		if err := os.Remove(s.dest(c)); err != nil && !os.IsNotExist(err) {
			return err
		}
		if err := SyncFolder(filepath.Dir(s.dest(c))); err != nil {
			return err
		}
	}
	for i := len(p.CreatedDirs) - 1; i >= 0; i-- {
		d := c.Amb.P(p.CreatedDirs[i])
		if err := os.Remove(d); err == nil {
			SyncFolder(filepath.Dir(d))
		}
	}
	return nil
}

func (s *writeFile) Cancelled(c *Context, before json.RawMessage) (bool, string, error) {
	var p beforeFile
	if err := json.Unmarshal(before, &p); err != nil {
		return false, "", err
	}
	if p.Origin == PREEXISTING {
		return true, "already there: left untouched", nil
	}
	if _, err := os.Lstat(s.tmp(c)); err == nil {
		return false, "the temporary file is still there", nil
	}
	ok, err := s.asBefore(c, p)
	if err != nil || !ok {
		return false, "the file is not as it was", err
	}
	for _, d := range p.CreatedDirs {
		if entries, err := os.ReadDir(c.Amb.P(d)); err == nil && len(entries) == 0 {
			return false, "the empty directory is still there: " + d, nil
		}
	}
	return true, "as it was before", nil
}
