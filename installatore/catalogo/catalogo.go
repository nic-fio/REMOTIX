// Package catalogo brings into the engine the catalogue of REMOTIX's combinations
// (fasi/17-l-installatore.md §6.6.8). The real file is catalogo.json, next to this one: it is edited
// there, and the manual's table (§3.1) is generated from there.
//
// ⭐ D11 simplified (DECISIONI §10.21): the catalogue has no signature of its own. It travels INSIDE the
// engine, and the engine inside REMOTIX's single package (the .run, verified with the published
// sha256: DECISIONI §10.36) and then in the installed remotix-install package. A new catalogue is
// a new release (packaging/rilascio.sh), with a higher «sequence».
package catalogo

import _ "embed"

//go:embed catalogo.json
var Incorporato []byte
