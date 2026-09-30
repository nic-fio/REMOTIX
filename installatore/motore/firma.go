package motore

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// La CATENA A della fiducia (fasi/17-l-installatore.md §6.6.10): il motore e il catalogo.
//
//   - la RADICE è una chiave ed25519 fuori linea: la sua parte pubblica è scritta nel motore
//     (installatore/chiavi/radice-A.pub), e firma solo due cose: i certificati delle SOTTOCHIAVI e
//     l'elenco delle REVOCHE;
//   - una SOTTOCHIAVE ha un identificativo e un periodo di validità (dal … al, un anno: D11), e firma
//     gli oggetti: il catalogo, il motore;
//   - la FIRMA di un oggetto è un file JSON separato accanto a lui (`<file>.firma`), col suo
//     certificato di sottochiave dentro: si verifica senza rete e senza altri file.
//
// ⛔ La catena A non ha niente in comune con la catena B (GPG: i pacchetti e gli archivi, verificati
// dal gestore di pacchetti): chiavi diverse, formati diversi, e il messaggio firmato nomina la catena.
// ⚠ Stdlib soltanto (crypto/ed25519): il motore resta un binario statico senza dipendenze nuove.

// FormatoFirma, FormatoSottochiave, FormatoRevoche: le versioni di formato della catena A.
const (
	FormatoFirma       = "remotix-firma/1"
	FormatoSottochiave = "remotix-sottochiave/1"
	FormatoRevoche     = "remotix-revoche/1"
	CatenaA            = "A"
)

// Sottochiave: il certificato di una sottochiave, firmato dalla radice.
type Sottochiave struct {
	Catena      string `json:"catena"`
	ID          string `json:"id"`
	Pubblica    string `json:"pubblica"` // base64 della chiave pubblica ed25519
	Dal         string `json:"dal"`      // AAAA-MM-GG, compreso
	Al          string `json:"al"`       // AAAA-MM-GG, compreso
	FirmaRadice string `json:"firma_radice"`
}

// FileFirma: il contenuto di `<file>.firma`.
type FileFirma struct {
	Formato string `json:"formato"`
	Catena  string `json:"catena"`
	// Oggetto: che cosa si firma («catalogo», «motore», «revoche»): una firma del motore non vale
	// per un catalogo con lo stesso digest, e viceversa.
	Oggetto string `json:"oggetto"`
	Sha256  string `json:"sha256"`
	Firmato string `json:"firmato"`
	// Sottochiave: chi ha firmato. Assente solo per le REVOCHE, che firma la radice stessa (una
	// sottochiave revocata non deve poter firmare l'elenco che la revoca).
	Sottochiave *Sottochiave `json:"sottochiave,omitempty"`
	Firma       string       `json:"firma"`
}

// Revoche: l'elenco firmato delle sottochiavi revocate (cumulativo: la sequenza più alta vince).
type Revoche struct {
	Formato  string   `json:"formato"`
	Catena   string   `json:"catena"`
	Sequenza int      `json:"sequenza"`
	Emesso   string   `json:"emesso"`
	Revocate []Revoca `json:"revocate"`
	Digest   string   `json:"-"`
	Fonte    string   `json:"-"`
}

// Revoca: una sottochiave revocata, e perché.
type Revoca struct {
	ID     string `json:"id"`
	Motivo string `json:"motivo"`
}

// MessaggioSottochiave: il testo che la radice firma per certificare una sottochiave.
func MessaggioSottochiave(s *Sottochiave) []byte {
	return []byte(FormatoSottochiave + "\n" + s.Catena + "\n" + s.ID + "\n" + s.Pubblica + "\n" + s.Dal + "\n" + s.Al + "\n")
}

// MessaggioFirma: il testo che una sottochiave (o la radice, per le revoche) firma per un oggetto.
func MessaggioFirma(catena, oggetto, sha string) []byte {
	return []byte(FormatoFirma + "\n" + catena + "\n" + oggetto + "\n" + sha + "\n")
}

// LeggiRadici: le radici della catena A da un testo (una chiave pubblica base64 per riga; # commenti).
func LeggiRadici(testo string) ([]ed25519.PublicKey, error) {
	var r []ed25519.PublicKey
	for _, riga := range strings.Split(testo, "\n") {
		riga = strings.TrimSpace(riga)
		if riga == "" || strings.HasPrefix(riga, "#") {
			continue
		}
		b, err := base64.StdEncoding.DecodeString(riga)
		if err != nil || len(b) != ed25519.PublicKeySize {
			return nil, fmt.Errorf("radice della catena A illeggibile: %q", riga)
		}
		r = append(r, ed25519.PublicKey(b))
	}
	if len(r) == 0 {
		return nil, fmt.Errorf("nessuna radice della catena A")
	}
	return r, nil
}

// ImprontaChiave: le prime 16 cifre esadecimali dello sha256 della chiave pubblica (per il manuale e
// per i messaggi: «radice 3f2a…»).
func ImprontaChiave(k []byte) string { return Sha256(k)[:16] }

func verificaCon(radici []ed25519.PublicKey, msg, firma []byte) bool {
	for _, r := range radici {
		if ed25519.Verify(r, msg, firma) {
			return true
		}
	}
	return false
}

func giorno(s string) (time.Time, error) { return time.Parse("2006-01-02", s) }

// EsitoFirma: chi ha firmato un oggetto verificato.
type EsitoFirma struct {
	Sottochiave string `json:"sottochiave"`
	Dal         string `json:"dal,omitempty"`
	Al          string `json:"al,omitempty"`
	Firmato     string `json:"firmato,omitempty"`
}

// VerificaFirma controlla la firma della catena A di un oggetto. Ogni rifiuto ha il suo codice:
// RX-TRUST-006 (la firma non c'è o non si legge), 007 (non corrisponde: oggetto alterato, o firma
// d'altro), 008 (la sottochiave non è certificata da una radice nota), 009 (sottochiave fuori dal
// suo periodo), 010 (sottochiave revocata).
func VerificaFirma(radici []ed25519.PublicKey, dati, firma []byte, oggetto string, adesso time.Time, rev *Revoche) (*EsitoFirma, error) {
	if len(firma) == 0 {
		return nil, Errore("RX-TRUST-006", oggetto)
	}
	var f FileFirma
	if err := json.Unmarshal(firma, &f); err != nil || f.Formato != FormatoFirma {
		return nil, Errore("RX-TRUST-006", oggetto+": la firma non si legge")
	}
	if f.Catena != CatenaA || f.Oggetto != oggetto {
		return nil, Errore("RX-TRUST-007", fmt.Sprintf("%s: firma della catena %q per l'oggetto %q", oggetto, f.Catena, f.Oggetto))
	}
	if Sha256(dati) != f.Sha256 {
		return nil, Errore("RX-TRUST-007", oggetto+": il contenuto non è quello firmato (sha256 "+Sha256(dati)[:16]+"…, firmato "+abbrevia(f.Sha256)+")")
	}
	sig, err := base64.StdEncoding.DecodeString(f.Firma)
	if err != nil {
		return nil, Errore("RX-TRUST-007", oggetto+": firma illeggibile")
	}
	msg := MessaggioFirma(f.Catena, f.Oggetto, f.Sha256)
	if f.Sottochiave == nil {
		// solo le revoche le firma la radice direttamente
		if oggetto != "revoche" || !verificaCon(radici, msg, sig) {
			return nil, Errore("RX-TRUST-008", oggetto+": firmato senza una sottochiave certificata")
		}
		return &EsitoFirma{Sottochiave: "radice", Firmato: f.Firmato}, nil
	}
	if oggetto == "revoche" {
		// una sottochiave non firma l'elenco che potrebbe revocarla
		return nil, Errore("RX-TRUST-008", "revoche firmate da una sottochiave, non dalla radice")
	}
	s := f.Sottochiave
	sr, err1 := base64.StdEncoding.DecodeString(s.FirmaRadice)
	pub, err2 := base64.StdEncoding.DecodeString(s.Pubblica)
	if err1 != nil || err2 != nil || len(pub) != ed25519.PublicKeySize || s.Catena != CatenaA ||
		!verificaCon(radici, MessaggioSottochiave(s), sr) {
		return nil, Errore("RX-TRUST-008", oggetto+": la sottochiave «"+s.ID+"» non è certificata da una radice nota")
	}
	dal, e1 := giorno(s.Dal)
	al, e2 := giorno(s.Al)
	if e1 != nil || e2 != nil {
		return nil, Errore("RX-TRUST-009", s.ID+": periodo illeggibile")
	}
	if adesso.Before(dal) || adesso.After(al.Add(24*time.Hour)) {
		return nil, Errore("RX-TRUST-009", s.ID+" vale dal "+s.Dal+" al "+s.Al)
	}
	if rev != nil {
		for _, x := range rev.Revocate {
			if x.ID == s.ID {
				return nil, Errore("RX-TRUST-010", s.ID+": "+x.Motivo+" (elenco "+fmt.Sprint(rev.Sequenza)+")")
			}
		}
	}
	if !ed25519.Verify(ed25519.PublicKey(pub), msg, sig) {
		return nil, Errore("RX-TRUST-007", oggetto+": la firma non è della sottochiave «"+s.ID+"»")
	}
	return &EsitoFirma{Sottochiave: s.ID, Dal: s.Dal, Al: s.Al, Firmato: f.Firmato}, nil
}

// LeggiRevoche verifica (firma della radice) e interpreta un elenco di revoche.
func LeggiRevoche(radici []ed25519.PublicKey, dati, firma []byte, adesso time.Time) (*Revoche, error) {
	if _, err := VerificaFirma(radici, dati, firma, "revoche", adesso, nil); err != nil {
		return nil, Errore("RX-TRUST-012", err.Error())
	}
	var r Revoche
	if err := json.Unmarshal(dati, &r); err != nil || r.Formato != FormatoRevoche || r.Catena != CatenaA {
		return nil, Errore("RX-TRUST-012", "formato")
	}
	r.Digest = Sha256(dati)
	return &r, nil
}

func abbrevia(s string) string {
	if len(s) > 16 {
		return s[:16] + "…"
	}
	return s
}

// ---- dalla parte di chi firma (lo strumento installatore/strumenti/chiavi-a, mai nel motore
// installato: la radice è fuori linea, e le sottochiavi stanno sulla macchina che pubblica)

// CertificaSottochiave: la radice firma il certificato di una sottochiave.
func CertificaSottochiave(radice ed25519.PrivateKey, id string, pub ed25519.PublicKey, dal, al string) *Sottochiave {
	s := &Sottochiave{Catena: CatenaA, ID: id, Pubblica: base64.StdEncoding.EncodeToString(pub), Dal: dal, Al: al}
	s.FirmaRadice = base64.StdEncoding.EncodeToString(ed25519.Sign(radice, MessaggioSottochiave(s)))
	return s
}

// Firma: il file .firma di un oggetto. s == nil ⇒ firma della radice (solo per le revoche).
func Firma(chiave ed25519.PrivateKey, s *Sottochiave, oggetto string, dati []byte, quando string) []byte {
	f := FileFirma{Formato: FormatoFirma, Catena: CatenaA, Oggetto: oggetto, Sha256: Sha256(dati), Firmato: quando, Sottochiave: s}
	f.Firma = base64.StdEncoding.EncodeToString(ed25519.Sign(chiave, MessaggioFirma(f.Catena, f.Oggetto, f.Sha256)))
	b, _ := json.MarshalIndent(f, "", "  ")
	return append(b, '\n')
}
