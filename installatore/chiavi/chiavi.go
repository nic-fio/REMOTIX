// Package chiavi porta dentro il motore le parti PUBBLICHE delle due catene di fiducia
// (fasi/17-l-installatore.md §6.6.10):
//
//   - radice-A.pub: la chiave madre della catena A (il motore e il catalogo), ed25519. Il motore
//     verifica con lei i certificati delle sottochiavi e l'elenco delle revoche;
//   - revoche.json(+.firma): l'elenco delle sottochiavi revocate noto quando il motore è uscito
//     (quello scaricato con il catalogo, se più recente, lo sostituisce);
//   - archivio.asc: la chiave pubblica della catena B (i pacchetti e gli archivi, GPG), che il
//     motore scrive per il gestore di pacchetti quando aggiunge l'archivio di REMOTIX. ⛔ Il motore
//     NON la usa per fidarsi di niente: la verifica della catena B la fa il gestore di pacchetti.
//
// ⚠ T8: sono chiavi DI PROVA, generate apposta per le prove (le private stanno fuori dal deposito).
// Le chiavi vere, e dove si custodisce la madre, sono la decisione D11.
package chiavi

import (
	_ "embed"
	"strings"
)

//go:embed radice-A.pub
var RadiceA string

//go:embed revoche.json
var Revoche []byte

//go:embed revoche.json.firma
var FirmaRevoche []byte

//go:embed archivio.asc
var Archivio string

//go:embed archivio.impronta
var improntaArchivio string

// ImprontaArchivio: l'impronta (fingerprint) della chiave madre della catena B.
func ImprontaArchivio() string { return strings.TrimSpace(improntaArchivio) }
