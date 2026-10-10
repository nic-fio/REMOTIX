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

// Formato is the format version of all the engine's objects (§6.6.1). It changes only if an
// object changes so that an old reader would misread it.
const Formato = "remotix-install/3"

// VersioneMotore is the version of this engine; the catalogue declares the minimum that understands it.
// The release command (packaging/rilascio.sh) sets it equal to the release's
// (-ldflags -X), the same as the remotix and remotix-install packages.
var VersioneMotore = "0.1.0"

// ora returns the instant in UTC, with seconds: it is what goes into the logs.
func ora() string { return time.Now().UTC().Format(time.RFC3339Nano) }

// Sha256 is the hexadecimal fingerprint of a text.
func Sha256(b []byte) string {
	s := sha256.Sum256(b)
	return hex.EncodeToString(s[:])
}

// Sha256File is the fingerprint of a file; "" if the file is not there.
func Sha256File(percorso string) (string, error) {
	b, err := os.ReadFile(percorso)
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return Sha256(b), nil
}

// SincronizzaCartella fsyncs the folder: without it, a rename or a creation can vanish
// on a power cut even if the file was synced (§6.6.3).
func SincronizzaCartella(cartella string) error {
	d, err := os.Open(cartella)
	if err != nil {
		return err
	}
	defer d.Close()
	return d.Sync()
}

// ScriviAtomico writes a file without ever leaving it half-written: temporary name in the same folder,
// fsync, rename, fsync of the folder. A reader sees either the old or the new, never a piece.
func ScriviAtomico(percorso string, dati []byte, modo os.FileMode) error {
	cartella := filepath.Dir(percorso)
	tmp, err := os.CreateTemp(cartella, "."+filepath.Base(percorso)+".tmp-*")
	if err != nil {
		return err
	}
	nomeTmp := tmp.Name()
	pulisci := func() { tmp.Close(); os.Remove(nomeTmp) }
	if _, err := tmp.Write(dati); err != nil {
		pulisci()
		return err
	}
	if err := tmp.Chmod(modo); err != nil {
		pulisci()
		return err
	}
	if err := tmp.Sync(); err != nil {
		pulisci()
		return err
	}
	if err := tmp.Close(); err != nil {
		os.Remove(nomeTmp)
		return err
	}
	if err := os.Rename(nomeTmp, percorso); err != nil {
		os.Remove(nomeTmp)
		return err
	}
	return SincronizzaCartella(cartella)
}

// ScriviJSON writes an engine object, atomically and readably.
func ScriviJSON(percorso string, v any) error {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return ScriviAtomico(percorso, append(b, '\n'), 0o600)
}

// LeggiJSON reads an engine object and checks the format version, if the object has one.
func LeggiJSON(percorso string, v any) error {
	b, err := os.ReadFile(percorso)
	if err != nil {
		return err
	}
	var intestazione struct {
		Formato string `json:"format"`
	}
	if err := json.Unmarshal(b, &intestazione); err != nil {
		return fmt.Errorf("%s: not valid JSON: %w", percorso, err)
	}
	if intestazione.Formato != "" && intestazione.Formato != Formato {
		return fmt.Errorf("%s: format %q, this engine understands %q", percorso, intestazione.Formato, Formato)
	}
	return json.Unmarshal(b, v)
}

// JSONCanonico serialises stably (Go's maps already come out sorted by key).
func JSONCanonico(v any) []byte {
	b, err := json.Marshal(v)
	if err != nil {
		panic(err) // only our types: an error here is a defect of the engine
	}
	return b
}
