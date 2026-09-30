package motore

import (
	"os"
	"path/filepath"
	"time"
)

// La fase 0 TRUST (fasi/17-l-installatore.md §6.0 punto 1, §6.6.10), dopo D11 semplificata
// (DECISIONI §10.21): UNA chiave sola, quella che firma i pacchetti e l'archivio di REMOTIX, e la
// verifica il gestore di pacchetti. Il motore non verifica firme sue.
//
// Il catalogo è quello che il motore porta dentro (catalogo/catalogo.json, incorporato alla
// costruzione): lo stesso file viaggia nel pacchetto remotix-install e si aggiorna con lui. Chi
// garantisce che è autentico è chi ha consegnato il motore:
//   - il motore del pacchetto (/usr/bin/remotix-install): il gestore di pacchetti, dall'archivio
//     firmato;
//   - il motore scaricato da install.sh: il suo sha256, pubblicato accanto e scaricato in HTTPS;
//     install.sh stesso l'amministratore lo verifica con lo sha256 pubblicato sul sito.
// Un catalogo dato a mano (--catalogo FILE) è dell'amministratore: si usa al posto di quello
// incorporato, e il certificato lo dice.
//
// Resta un solo controllo: il catalogo si legge (RX-TRUST-004) e questo motore lo capisce
// (RX-TRUST-003).

// FontiFiducia: da dove viene il catalogo.
type FontiFiducia struct {
	Incorporato []byte // il catalogo dentro il motore
	Esplicito   string // --catalogo FILE: dato a mano dall'amministratore
	Motore      string // il binario che gira ("" ⇒ /proc/self/exe): dice chi l'ha consegnato
}

// Fiducia è l'esito della fase 0 TRUST (oggetto fiducia.json dell'operazione).
type Fiducia struct {
	Catalogo RifCatalogo `json:"catalogo"`
	Sequenza int         `json:"sequenza"`
	// Fonte: da dove viene il catalogo, e chi ne garantisce l'autenticità.
	Fonte    string      `json:"fonte"`
	Motore   RifMotore   `json:"motore"`
	Messaggi []Messaggio `json:"messaggi"`
}

// MotoreDelPacchetto: dove il pacchetto remotix-install mette il motore.
const MotoreDelPacchetto = "/usr/bin/remotix-install"

// chiHaConsegnato: la frase che dice chi garantisce il motore che gira (e il catalogo che porta).
func (f *FontiFiducia) chiHaConsegnato() string {
	exe := f.Motore
	if exe == "" {
		exe, _ = os.Readlink("/proc/self/exe")
	}
	if filepath.Clean(exe) == MotoreDelPacchetto {
		return T("fid.pacchetto")
	}
	return T("fid.scaricato", exe)
}

// Fidati: la fase 0 TRUST. Restituisce il catalogo e l'esito (anche in caso d'errore, perché
// fiducia.json dice che cosa si è guardato).
func (f *FontiFiducia) Fidati(adesso time.Time) (*Catalogo, *Fiducia, error) {
	fid := &Fiducia{Motore: RifMotore{VersioneMotore, DigestMotore()}, Messaggi: []Messaggio{}}
	blocca := func(err error) (*Catalogo, *Fiducia, error) {
		if m, ok := err.(*ErroreRX); ok {
			fid.Messaggi = append(fid.Messaggi, m.M)
		}
		return nil, fid, err
	}
	dati, fonte := f.Incorporato, f.chiHaConsegnato()
	if f.Esplicito != "" {
		d, err := os.ReadFile(f.Esplicito)
		if err != nil {
			return blocca(Errore("RX-TRUST-004", err.Error()))
		}
		dati, fonte = d, T("fid.a_mano", f.Esplicito)
	}
	cat, err := LeggiCatalogo(dati)
	if err != nil {
		fid.Fonte = fonte
		return blocca(err)
	}
	cat.Provenienza = fonte
	fid.Catalogo = RifCatalogo{cat.Versione, cat.Digest}
	fid.Sequenza, fid.Fonte = cat.Sequenza, fonte
	if err := ControllaMotoreMinimo(cat); err != nil {
		return blocca(err)
	}
	return cat, fid, nil
}

// ControllaMotoreMinimo: questo motore capisce il catalogo.
func ControllaMotoreMinimo(c *Catalogo) error {
	if ConfrontaVersioni(VersioneMotore, c.MotoreMinimo) < 0 {
		return Errore("RX-TRUST-003", "serve "+c.MotoreMinimo+", questo è "+VersioneMotore)
	}
	return nil
}
