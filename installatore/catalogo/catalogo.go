// Package catalogo porta dentro il motore il catalogo delle combinazioni di REMOTIX
// (fasi/17-l-installatore.md §6.6.8). Il file vero è catalogo.json, accanto: si modifica lì, e
// la tabella del manuale (§3.1) si genererà da lì.
package catalogo

import _ "embed"

//go:embed catalogo.json
var Incorporato []byte
