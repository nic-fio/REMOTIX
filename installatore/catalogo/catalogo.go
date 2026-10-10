// Package catalogo porta dentro il motore il catalogo delle combinazioni di REMOTIX
// (fasi/17-l-installatore.md §6.6.8). Il file vero è catalogo.json, accanto: si modifica lì, e
// la tabella del manuale (§3.1) si genera da lì.
//
// ⭐ D11 semplificata (DECISIONI §10.21): il catalogo non ha una firma sua. Viaggia DENTRO il
// motore, e il motore dentro il pacchetto unico di REMOTIX (il .run, verificato con lo sha256
// pubblicato: DECISIONI §10.36) e poi nel pacchetto remotix-install installato. Un catalogo nuovo è
// un rilascio nuovo (packaging/rilascio.sh), con la «sequenza» più alta.
package catalogo

import _ "embed"

//go:embed catalogo.json
var Incorporato []byte
