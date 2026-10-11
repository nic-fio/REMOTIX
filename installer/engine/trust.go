package engine

import (
	"os"
	"path/filepath"
	"time"
)

// Phase 0 TRUST (phases/17-the-installer.md §6.0 point 1, §6.6.10), after simplified D11
// (DECISIONI §10.21, §10.36): no keys and no repository; the single package (the .run) is verified with
// the sha256 published on the site. The engine verifies no signatures of its own.
//
// The catalogue is the one the engine carries inside (catalog/catalog.json, embedded at
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
	Explicit    string // --catalogo FILE: given by hand by the administrator
	Engine      string // the running binary ("" ⇒ /proc/self/exe): it says who delivered it
}

// Trust is the outcome of phase 0 TRUST (object trust.json of the operation).
type Trust struct {
	Catalog  CatalogRef `json:"catalog"`
	Sequence int        `json:"sequence"`
	// Source: where the catalogue comes from, and who guarantees its authenticity.
	Source   string    `json:"source"`
	Engine   EngineRef `json:"engine"`
	Messages []Message `json:"messages"`
}

// PackagedEngine: where the remotix-install package puts the engine.
const PackagedEngine = "/usr/bin/remotix-install"

// whoDelivered: the sentence saying who guarantees the running engine (and the catalogue it carries).
func (f *TrustSources) whoDelivered() string {
	exe := f.Engine
	if exe == "" {
		exe, _ = os.Readlink("/proc/self/exe")
	}
	if filepath.Clean(exe) == PackagedEngine {
		return T("fid.pacchetto")
	}
	return T("fid.scaricato", exe)
}

// Trusted: phase 0 TRUST. Returns the catalogue and the outcome (even on error, because
// trust.json says what was looked at).
func (f *TrustSources) Trusted(t_now time.Time) (*Catalog, *Trust, error) {
	fid := &Trust{Engine: EngineRef{EngineVersion, EngineDigest()}, Messages: []Message{}}
	block := func(err error) (*Catalog, *Trust, error) {
		if m, ok := err.(*ErrorRX); ok {
			fid.Messages = append(fid.Messages, m.M)
		}
		return nil, fid, err
	}
	data, source := f.Incorporato, f.whoDelivered()
	if f.Explicit != "" {
		d, err := os.ReadFile(f.Explicit)
		if err != nil {
			return block(Error("RX-TRUST-004", err.Error()))
		}
		data, source = d, T("fid.a_mano", f.Explicit)
	}
	cat, err := ReadCatalog(data)
	if err != nil {
		fid.Source = source
		return block(err)
	}
	cat.Provenance = source
	fid.Catalog = CatalogRef{cat.Ver, cat.Digest}
	fid.Sequence, fid.Source = cat.Sequence, source
	if err := CheckMinEngine(cat); err != nil {
		return block(err)
	}
	return cat, fid, nil
}

// CheckMinEngine: this engine understands the catalogue.
func CheckMinEngine(c *Catalog) error {
	if CompareVersions(EngineVersion, c.EngineMinimum) < 0 {
		return Error("RX-TRUST-003", "needs "+c.EngineMinimum+", this is "+EngineVersion)
	}
	return nil
}
