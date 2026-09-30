// Package chiavi porta dentro il motore la parte PUBBLICA dell'unica chiave di REMOTIX
// (DECISIONI §10.21, D11 semplificata): quella che firma i pacchetti e l'archivio. Il motore la
// scrive per il gestore di pacchetti quando aggiunge l'archivio di REMOTIX (apt Signed-By, dnf
// gpgkey, pacman-key). ⛔ Il motore NON la usa per fidarsi di niente: la verifica la fa il gestore
// di pacchetti.
//
// ⚠ È la chiave DI PROVA della fase 17 (la privata sta fuori dal deposito, in
// .chiavi/b del progetto, ignorata da git); la vera, e dove si custodisce, si decidono con D10.
package chiavi

import (
	_ "embed"
	"strings"
)

//go:embed archivio.asc
var Archivio string

//go:embed archivio.impronta
var improntaArchivio string

// ImprontaArchivio: l'impronta (fingerprint) della chiave dell'archivio.
func ImprontaArchivio() string { return strings.TrimSpace(improntaArchivio) }
