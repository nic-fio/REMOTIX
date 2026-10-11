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

// TrustSources: where the catalogue comes from.
type TrustSources struct {
	Incorporato []byte // the catalogue inside the engine
	Esplicito   string // --catalogo FILE: given by hand by the administrator
	Motore      string // the running binary ("" ⇒ /proc/self/exe): it says who delivered it
}

// Fiducia is the outcome of phase 0 TRUST (object fiducia.json of the operation).
type Attestation struct {
	Catalogo CatalogRef `json:"catalog"`
	Sequence int        `json:"sequence"`
	// Fonte: where the catalogue comes from, and who guarantees its authenticity.
	Source   string    `json:"source"`
	Motore   EngineRef `json:"engine"`
	Messages []Message `json:"messages"`
}

// PackagedEngine: where the remotix-install package puts the engine.
const PackagedEngine = "/usr/bin/remotix-install"

// whoDelivered: the sentence saying who guarantees the running engine (and the catalogue it carries).
func (f *TrustSources) whoDelivered() string {
	exe := f.Motore
	if exe == "" {
		exe, _ = os.Readlink("/proc/self/exe")
	}
	if filepath.Clean(exe) == PackagedEngine {
		return T("fid.pacchetto")
	}
	return T("fid.scaricato", exe)
}

// Fidati: phase 0 TRUST. Returns the catalogue and the outcome (even on error, because
// fiducia.json says what was looked at).
func (f *TrustSources) Trusted(adesso time.Time) (*Catalogo, *Attestation, error) {
	fid := &Attestation{Motore: EngineRef{VersioneMotore, EngineDigest()}, Messages: []Message{}}
	blocca := func(err error) (*Catalogo, *Attestation, error) {
		if m, ok := err.(*ErrorRX); ok {
			fid.Messages = append(fid.Messages, m.M)
		}
		return nil, fid, err
	}
	dati, fonte := f.Incorporato, f.whoDelivered()
	if f.Esplicito != "" {
		d, err := os.ReadFile(f.Esplicito)
		if err != nil {
			return blocca(Errore("RX-TRUST-004", err.Error()))
		}
		dati, fonte = d, T("fid.a_mano", f.Esplicito)
	}
	cat, err := ReadCatalog(dati)
	if err != nil {
		fid.Source = fonte
		return blocca(err)
	}
	cat.Provenance = fonte
	fid.Catalogo = CatalogRef{cat.Version, cat.Digest}
	fid.Sequence, fid.Source = cat.Sequence, fonte
	if err := CheckMinEngine(cat); err != nil {
		return blocca(err)
	}
	return cat, fid, nil
}

// CheckMinEngine: this engine understands the catalogue.
func CheckMinEngine(c *Catalogo) error {
	if CompareVersions(VersioneMotore, c.EngineMinimum) < 0 {
		return Errore("RX-TRUST-003", "needs "+c.EngineMinimum+", this is "+VersioneMotore)
	}
	return nil
}
