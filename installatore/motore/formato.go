// Package motore is REMOTIX's installation engine (fasi/17-l-installatore.md §6.0, §6.6).
//
// The engine is the only place where the installation logic lives: the CLI (remotix-install) is the
// engine itself, and the future TUIs and GUIs (D12) will talk to it only through the JSON objects
// of this package and the one-line JSON events (eventi.go), never with logic of their own (R36).
package motore

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// Schema is the format version of all the engine's objects (§6.6.1). It changes only if an
// object changes so that an old reader would misread it.
const Schema = "remotix-install/3"

// EngineVersion is the version of this engine; the catalogue declares the minimum that understands it.
// The release command (packaging/rilascio.sh) sets it equal to the release's
// (-ldflags -X), the same as the remotix and remotix-install packages.
var EngineVersion = "0.1.0"

// now returns the instant in UTC, with seconds: it is what goes into the logs.
func now() string { return time.Now().UTC().Format(time.RFC3339Nano) }

// Sha256 is the hexadecimal fingerprint of a text.
func Sha256(b []byte) string {
	s := sha256.Sum256(b)
	return hex.EncodeToString(s[:])
}

// Sha256File is the fingerprint of a file; "" if the file is not there.
func Sha256File(fpath string) (string, error) {
	b, err := os.ReadFile(fpath)
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return Sha256(b), nil
}

// SyncFolder fsyncs the folder: without it, a rename or a creation can vanish
// on a power cut even if the file was synced (§6.6.3).
func SyncFolder(folder string) error {
	d, err := os.Open(folder)
	if err != nil {
		return err
	}
	defer d.Close()
	return d.Sync()
}

// WriteAtomic writes a file without ever leaving it half-written: temporary name in the same folder,
// fsync, rename, fsync of the folder. A reader sees either the old or the new, never a piece.
func WriteAtomic(fpath string, data_v []byte, manner os.FileMode) error {
	folder := filepath.Dir(fpath)
	tmp, err := os.CreateTemp(folder, "."+filepath.Base(fpath)+".tmp-*")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	clean := func() { tmp.Close(); os.Remove(tmpName) }
	if _, err := tmp.Write(data_v); err != nil {
		clean()
		return err
	}
	if err := tmp.Chmod(manner); err != nil {
		clean()
		return err
	}
	if err := tmp.Sync(); err != nil {
		clean()
		return err
	}
	if err := tmp.Close(); err != nil {
		os.Remove(tmpName)
		return err
	}
	if err := os.Rename(tmpName, fpath); err != nil {
		os.Remove(tmpName)
		return err
	}
	return SyncFolder(folder)
}

// WriteJSON writes an engine object, atomically and readably.
func WriteJSON(fpath string, v any) error {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return WriteAtomic(fpath, append(b, '\n'), 0o600)
}

// ReadJSON reads an engine object and checks the format version, if the object has one.
func ReadJSON(fpath string, v any) error {
	b, err := os.ReadFile(fpath)
	if err != nil {
		return err
	}
	var header struct {
		Schema string `json:"format"`
	}
	if err := json.Unmarshal(b, &header); err != nil {
		return fmt.Errorf("%s: not valid JSON: %w", fpath, err)
	}
	if header.Schema != "" && header.Schema != Schema {
		return fmt.Errorf("%s: format %q, this engine understands %q", fpath, header.Schema, Schema)
	}
	return json.Unmarshal(b, v)
}

// CanonicalJSON serialises stably (Go's maps already come out sorted by key).
func CanonicalJSON(v any) []byte {
	b, err := json.Marshal(v)
	if err != nil {
		panic(err) // only our types: an error here is a defect of the engine
	}
	return b
}
