package motore

import (
	"os"
	"path/filepath"
	"time"
)

// Phase 0 TRUST (fasi/17-l-installatore.md §6.0 point 1, §6.6.10), after simplified D11
// (DECISIONI §10.21, §10.36): no keys and no repository; the single package (the .run) is verified with
// the sha256 published on the site. The engine verifies no signatures of its own.
//
// The catalogue is the one the engine carries inside (catalogo/catalogo.json, embedded at
// build time): the same file travels in the remotix-install package and is updated with it. Who
// guarantees it is authentic is whoever delivered the engine:
//   - the package's engine (/usr/bin/remotix-install): installed by the .run;
//   - the engine inside the .run: the sha256 of the .run, published on the site, and that of its payload.
// A catalogue given by hand (--catalogo FILE) is the administrator's: it is used in place of the
// embedded one, and the certificate says so.
//
// One check remains: the catalogue can be read (RX-TRUST-004) and this engine understands it
// (RX-TRUST-003).

// FontiFiducia: where the catalogue comes from.
type FontiFiducia struct {
	Incorporato []byte // the catalogue inside the engine
	Esplicito   string // --catalogo FILE: given by hand by the administrator
	Motore      string // the running binary ("" ⇒ /proc/self/exe): it says who delivered it
}

// Fiducia is the outcome of phase 0 TRUST (object fiducia.json of the operation).
type Fiducia struct {
	Catalogo RifCatalogo `json:"catalog"`
	Sequenza int         `json:"sequence"`
	// Fonte: where the catalogue comes from, and who guarantees its authenticity.
	Fonte    string      `json:"source"`
	Motore   RifMotore   `json:"engine"`
	Messaggi []Messaggio `json:"messages"`
}

// MotoreDelPacchetto: where the remotix-install package puts the engine.
const MotoreDelPacchetto = "/usr/bin/remotix-install"

// chiHaConsegnato: the sentence saying who guarantees the running engine (and the catalogue it carries).
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

// Fidati: phase 0 TRUST. Returns the catalogue and the outcome (even on error, because
// fiducia.json says what was looked at).
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

// ControllaMotoreMinimo: this engine understands the catalogue.
func ControllaMotoreMinimo(c *Catalogo) error {
	if ConfrontaVersioni(VersioneMotore, c.MotoreMinimo) < 0 {
		return Errore("RX-TRUST-003", "needs "+c.MotoreMinimo+", this is "+VersioneMotore)
	}
	return nil
}
