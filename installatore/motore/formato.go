// Package motore è il motore d'installazione di REMOTIX (fasi/17-l-installatore.md §6.0, §6.6).
//
// Il motore è l'unico posto dove sta la logica d'installazione: la CLI (remotix-install) è il
// motore stesso, e le future TUI e GUI (D12) parleranno con lui solo attraverso gli oggetti JSON
// di questo pacchetto e gli eventi JSON a una riga (eventi.go), mai con logica propria (R36).
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

// Formato è la versione di formato di tutti gli oggetti del motore (§6.6.1). Cambia solo se un
// oggetto cambia in modo che un lettore vecchio lo leggerebbe male.
const Formato = "remotix-install/1"

// VersioneMotore è la versione di questo motore; il catalogo dichiara la minima che lo capisce.
// Il comando di rilascio (packaging/rilascio.sh) la fissa uguale a quella del rilascio
// (-ldflags -X), la stessa dei pacchetti remotix e remotix-install.
var VersioneMotore = "0.1.0"

// ora restituisce l'istante in UTC, con i secondi: è quel che va nei registri.
func ora() string { return time.Now().UTC().Format(time.RFC3339Nano) }

// Sha256 è l'impronta esadecimale di un testo.
func Sha256(b []byte) string {
	s := sha256.Sum256(b)
	return hex.EncodeToString(s[:])
}

// Sha256File è l'impronta di un file; "" se il file non c'è.
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

// SincronizzaCartella fa fsync della cartella: senza, una rinomina o una creazione può sparire
// al salto della corrente anche se il file è stato sincronizzato (§6.6.3).
func SincronizzaCartella(cartella string) error {
	d, err := os.Open(cartella)
	if err != nil {
		return err
	}
	defer d.Close()
	return d.Sync()
}

// ScriviAtomico scrive un file senza mai lasciarlo a metà: nome temporaneo nella stessa cartella,
// fsync, rinomina, fsync della cartella. Chi legge vede o il vecchio o il nuovo, mai un pezzo.
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

// ScriviJSON scrive un oggetto del motore, in modo atomico e leggibile.
func ScriviJSON(percorso string, v any) error {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return ScriviAtomico(percorso, append(b, '\n'), 0o600)
}

// LeggiJSON legge un oggetto del motore e controlla la versione di formato, se l'oggetto la ha.
func LeggiJSON(percorso string, v any) error {
	b, err := os.ReadFile(percorso)
	if err != nil {
		return err
	}
	var intestazione struct {
		Formato string `json:"formato"`
	}
	if err := json.Unmarshal(b, &intestazione); err != nil {
		return fmt.Errorf("%s: not valid JSON: %w", percorso, err)
	}
	if intestazione.Formato != "" && intestazione.Formato != Formato {
		return fmt.Errorf("%s: format %q, this engine understands %q", percorso, intestazione.Formato, Formato)
	}
	return json.Unmarshal(b, v)
}

// JSONCanonico serializza in modo stabile (le mappe di Go escono già ordinate per chiave).
func JSONCanonico(v any) []byte {
	b, err := json.Marshal(v)
	if err != nil {
		panic(err) // solo tipi nostri: un errore qui è un difetto del motore
	}
	return b
}
