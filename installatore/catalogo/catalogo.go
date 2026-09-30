// Package catalogo porta dentro il motore il catalogo delle combinazioni di REMOTIX
// (fasi/17-l-installatore.md §6.6.8). Il file vero è catalogo.json, accanto: si modifica lì, e
// la tabella del manuale (§3.1) si genererà da lì.
//
// ⭐ T8: il catalogo incorporato ha la sua firma della catena A accanto (catalogo.json.firma), e il
// motore la verifica come quella di un catalogo scaricato: cambiare catalogo.json vuol dire
// rifirmarlo (installatore/strumenti/chiavi-a firma …), o TestCatalogoIncorporatoFirmato fallisce.
package catalogo

import _ "embed"

//go:embed catalogo.json
var Incorporato []byte

//go:embed catalogo.json.firma
var Firma []byte
