package motore

import (
	"crypto/ed25519"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// La fase 0 TRUST (fasi/17-l-installatore.md §6.0 punto 1, §6.6.10), catena A.
//
// Da dove può venire il catalogo, e come si sceglie:
//   - FUORI LINEA, dato esplicitamente (--catalogo FILE, con FILE.firma): se c'è, è l'UNICO che si
//     guarda (§6.6.12: senza rete si procede solo così, mai saltando il controllo);
//   - altrimenti: quello INCORPORATO nel motore, quello MEMORIZZATO sulla macchina (l'ultimo
//     verificato, in /var/lib/remotix/fiducia/) e quello dell'ARCHIVIO (scaricato, se c'è un
//     archivio). Ognuno deve avere una firma valida: una firma sbagliata da qualunque fonte è
//     BLOCCATA, non «si prende un altro» — un catalogo alterato vuol dire che qualcuno ci sta
//     provando, e l'amministratore lo deve sapere. Fra i validi vince la SEQUENZA più alta;
//   - poi il vincitore deve essere fresco: non scaduto (RX-TRUST-002) e capito da questo motore
//     (RX-TRUST-003). ⛔ Non si ripiega su uno più vecchio: se il più recente è scaduto, il catalogo
//     va aggiornato.
//
// Le revoche vengono prima: l'elenco con la sequenza più alta fra incorporato, memorizzato e
// archivio (firmato dalla RADICE; un elenco non valido è BLOCCATA, RX-TRUST-012).
// Il catalogo vincitore (e le revoche) si MEMORIZZANO solo se Scrivi: «verifica» non scrive mai
// niente (R1).

// FontiFiducia: dove il motore cerca il catalogo e con che cosa lo verifica.
type FontiFiducia struct {
	Radici                           []ed25519.PublicKey
	Incorporato, FirmaIncorporata    []byte
	RevocheIncorporate, FirmaRevoche []byte
	Esplicito, FirmaEsplicita        string // --catalogo FILE [--firma-catalogo FILE]
	Archivio, Canale                 string // l'archivio di REMOTIX (URL di base) e il canale
	Memoria                          string // /var/lib/remotix/fiducia
	Scrivi                           bool
	Scarica                          func(url string) ([]byte, error) // nil ⇒ HTTP
	Motore                           string                           // il binario che gira ("" ⇒ /proc/self/exe)
}

// Fiducia è l'esito della fase 0 TRUST (oggetto fiducia.json dell'operazione).
type Fiducia struct {
	Catalogo        RifCatalogo `json:"catalogo"`
	Sequenza        int         `json:"sequenza"`
	Fonte           string      `json:"fonte"`
	Sottochiave     string      `json:"sottochiave"`
	Motore          RifMotore   `json:"motore"`
	FirmaMotore     string      `json:"firma_motore"`
	FirmaVerificata bool        `json:"firma_verificata"`
	Revoche         int         `json:"revoche"`
	Radice          string      `json:"radice"`
	Guardati        []Guardato  `json:"guardati"`
	Messaggi        []Messaggio `json:"messaggi"`
}

// Guardato: una fonte che TRUST ha guardato, e com'è andata.
type Guardato struct {
	Cosa     string `json:"cosa"` // catalogo · revoche · motore
	Fonte    string `json:"fonte"`
	Sequenza int    `json:"sequenza,omitempty"`
	Esito    string `json:"esito"`
}

type candidato struct {
	fonte       string
	dati, firma []byte
	cat         *Catalogo
	esito       *EsitoFirma
	rev         *Revoche
}

func (f *FontiFiducia) scarica(url string) ([]byte, error) {
	if f.Scarica != nil {
		return f.Scarica(url)
	}
	if p, ok := strings.CutPrefix(url, "file://"); ok {
		// l'archivio locale di un pacchetto fuori linea (§6.6.12): le firme si verificano come in linea
		return os.ReadFile(p)
	}
	cl := &http.Client{Timeout: 20 * time.Second}
	r, err := cl.Get(url)
	if err != nil {
		return nil, err
	}
	defer r.Body.Close()
	if r.StatusCode != 200 {
		return nil, fmt.Errorf("%s: %s", url, r.Status)
	}
	return io.ReadAll(io.LimitReader(r.Body, 8<<20))
}

// URLCatalogo: dove l'archivio pubblica il catalogo di un canale, e l'elenco delle revoche.
func URLCatalogo(archivio, canale string) (string, string) {
	a := strings.TrimRight(archivio, "/")
	return a + "/catalogo/" + nonVuoto(canale, "stabile") + "/catalogo.json", a + "/catalogo/revoche.json"
}

func leggiSeC(p string) []byte {
	b, _ := os.ReadFile(p)
	return b
}

// Fidati: la fase 0 TRUST. Restituisce il catalogo scelto e verificato, e l'esito (anche in caso
// d'errore, perché fiducia.json dice che cosa si è guardato).
func (f *FontiFiducia) Fidati(adesso time.Time) (*Catalogo, *Fiducia, error) {
	fid := &Fiducia{Motore: RifMotore{VersioneMotore, DigestMotore()}, Guardati: []Guardato{}, Messaggi: []Messaggio{}}
	if len(f.Radici) > 0 {
		fid.Radice = ImprontaChiave(f.Radici[0])
	}
	blocca := func(err error) (*Catalogo, *Fiducia, error) {
		if m, ok := err.(*ErroreRX); ok {
			fid.Messaggi = append(fid.Messaggi, m.M)
		}
		return nil, fid, err
	}
	uCat, uRev := "", ""
	if f.Archivio != "" && f.Esplicito == "" {
		uCat, uRev = URLCatalogo(f.Archivio, f.Canale)
	}

	// 1. le revoche
	var rev *Revoche
	var revCand []candidato
	revCand = append(revCand, candidato{fonte: "incorporato", dati: f.RevocheIncorporate, firma: f.FirmaRevoche})
	if f.Memoria != "" {
		if d := leggiSeC(filepath.Join(f.Memoria, "revoche.json")); d != nil {
			revCand = append(revCand, candidato{fonte: "memorizzato", dati: d, firma: leggiSeC(filepath.Join(f.Memoria, "revoche.json.firma"))})
		}
	}
	if uRev != "" {
		d, err1 := f.scarica(uRev)
		s, err2 := f.scarica(uRev + ".firma")
		if err1 == nil && err2 == nil {
			revCand = append(revCand, candidato{fonte: "archivio " + uRev, dati: d, firma: s})
		} else {
			fid.Guardati = append(fid.Guardati, Guardato{"revoche", "archivio " + uRev, 0, "non scaricato: " + primoErrore(err1, err2).Error()})
		}
	}
	for _, c := range revCand {
		if len(c.dati) == 0 && c.fonte == "incorporato" {
			continue // un motore di prova senza elenco incorporato
		}
		r, err := LeggiRevoche(f.Radici, c.dati, c.firma, adesso)
		if err != nil {
			fid.Guardati = append(fid.Guardati, Guardato{"revoche", c.fonte, 0, err.Error()})
			return blocca(err)
		}
		r.Fonte = c.fonte
		fid.Guardati = append(fid.Guardati, Guardato{"revoche", c.fonte, r.Sequenza, "valido"})
		if rev == nil || r.Sequenza > rev.Sequenza {
			rev = r
		}
	}
	if rev != nil {
		fid.Revoche = rev.Sequenza
	}

	// 2. il motore stesso: la sua firma, se l'ha accanto
	fid.FirmaMotore = f.firmaMotore(fid, adesso, rev)
	if fid.FirmaMotore == "NON VALIDA" {
		return blocca(Errore("RX-TRUST-014", fid.Guardati[len(fid.Guardati)-1].Esito))
	}

	// 3. il catalogo
	var cand []candidato
	if f.Esplicito != "" {
		fs := f.FirmaEsplicita
		if fs == "" {
			fs = f.Esplicito + ".firma"
		}
		d, err := os.ReadFile(f.Esplicito)
		if err != nil {
			return blocca(Errore("RX-TRUST-004", err.Error()))
		}
		cand = append(cand, candidato{fonte: "fuori linea " + f.Esplicito, dati: d, firma: leggiSeC(fs)})
	} else {
		cand = append(cand, candidato{fonte: "incorporato", dati: f.Incorporato, firma: f.FirmaIncorporata})
		if uCat != "" {
			d, err1 := f.scarica(uCat)
			s, err2 := f.scarica(uCat + ".firma")
			if err1 == nil && err2 == nil {
				cand = append(cand, candidato{fonte: "archivio " + uCat, dati: d, firma: s})
			} else {
				e := primoErrore(err1, err2)
				fid.Guardati = append(fid.Guardati, Guardato{"catalogo", "archivio " + uCat, 0, "non scaricato: " + e.Error()})
				fid.Messaggi = append(fid.Messaggi, Msg("RX-TRUST-013", e.Error()))
			}
		}
	}
	if f.Memoria != "" {
		if d := leggiSeC(filepath.Join(f.Memoria, "catalogo.json")); d != nil {
			cand = append(cand, candidato{fonte: "memorizzato", dati: d, firma: leggiSeC(filepath.Join(f.Memoria, "catalogo.json.firma"))})
		}
	}
	var scelto *candidato
	var memSeq int = -1
	var scartato error
	for i := range cand {
		c := &cand[i]
		e, err := VerificaFirma(f.Radici, c.dati, c.firma, "catalogo", adesso, rev)
		if err != nil {
			fid.Guardati = append(fid.Guardati, Guardato{"catalogo", c.fonte, 0, err.Error()})
			// il catalogo del motore o quello memorizzato firmati da una sottochiave poi REVOCATA o
			// SCADUTA non bloccano da soli: è la rotazione (§6.6.10), e il catalogo nuovo dell'archivio
			// li sostituisce. Si scartano; se non resta nessun catalogo valido, BLOCCATA con questo codice.
			// Qualunque altro rifiuto (alterato, radice sconosciuta) e ogni rifiuto di un catalogo
			// dell'archivio o dato a mano BLOCCA subito.
			cod := CodiceDi(err)
			if (c.fonte == "incorporato" || c.fonte == "memorizzato") && (cod == "RX-TRUST-009" || cod == "RX-TRUST-010") {
				if scartato == nil {
					scartato = err
				}
				continue
			}
			return blocca(err)
		}
		cat, err := LeggiCatalogo(c.dati)
		if err != nil {
			fid.Guardati = append(fid.Guardati, Guardato{"catalogo", c.fonte, 0, err.Error()})
			return blocca(err)
		}
		c.cat, c.esito = cat, e
		fid.Guardati = append(fid.Guardati, Guardato{"catalogo", c.fonte, cat.Sequenza, "firma valida (" + e.Sottochiave + "), versione " + cat.Versione})
		if c.fonte == "memorizzato" {
			memSeq = cat.Sequenza
		}
		if scelto == nil || cat.Sequenza > scelto.cat.Sequenza || (cat.Sequenza == scelto.cat.Sequenza && c.fonte != "memorizzato" && scelto.fonte == "memorizzato") {
			scelto = c
		}
	}
	if scelto == nil {
		return blocca(scartato)
	}
	if f.Esplicito != "" && memSeq >= 0 && cand[0].cat.Sequenza < memSeq {
		return blocca(Errore("RX-TRUST-016", fmt.Sprintf("dato %d, già verificato %d", cand[0].cat.Sequenza, memSeq)))
	}
	if f.Esplicito != "" {
		scelto = &cand[0]
	}
	for _, c := range cand {
		if strings.HasPrefix(c.fonte, "archivio") && c.cat != nil && c.cat.Sequenza < scelto.cat.Sequenza {
			fid.Messaggi = append(fid.Messaggi, Msg("RX-TRUST-011", fmt.Sprintf("archivio %d, già verificato %d", c.cat.Sequenza, scelto.cat.Sequenza)))
		}
	}
	cat := scelto.cat
	cat.Provenienza = scelto.fonte
	fid.Catalogo = RifCatalogo{cat.Versione, cat.Digest, cat.Scadenza}
	fid.Sequenza, fid.Fonte, fid.Sottochiave = cat.Sequenza, scelto.fonte, scelto.esito.Sottochiave

	// 4. fresco?
	if err := ControllaFreschezza(cat, adesso); err != nil {
		return blocca(err)
	}
	fid.FirmaVerificata = true

	// 5. si ricorda il più recente (mai in «verifica»)
	if f.Scrivi && f.Memoria != "" {
		if scelto.fonte != "memorizzato" && cat.Sequenza > memSeq {
			if err := memorizza(f.Memoria, "catalogo.json", scelto.dati, scelto.firma); err != nil {
				return blocca(err)
			}
		}
		if rev != nil && rev.Fonte != "memorizzato" && rev.Fonte != "incorporato" {
			for _, c := range revCand {
				if c.fonte == rev.Fonte {
					if err := memorizza(f.Memoria, "revoche.json", c.dati, c.firma); err != nil {
						return blocca(err)
					}
				}
			}
		}
	}
	return cat, fid, nil
}

func memorizza(dir, nome string, dati, firma []byte) error {
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return err
	}
	if err := ScriviAtomico(filepath.Join(dir, nome+".firma"), firma, 0o600); err != nil {
		return err
	}
	return ScriviAtomico(filepath.Join(dir, nome), dati, 0o600)
}

func primoErrore(e ...error) error {
	for _, x := range e {
		if x != nil {
			return x
		}
	}
	return nil
}

// firmaMotore: la firma della catena A del binario che gira, se ce l'ha accanto (<binario>.firma, o
// /usr/share/remotix-install/remotix-install.firma per quello del pacchetto). «verificata»,
// «assente» (INFO: l'ha verificato chi l'ha scaricato, o il gestore di pacchetti), «NON VALIDA».
// ⚠ Onestamente: un motore alterato può saltare anche questo controllo (§6.6.11); serve a dire,
// a chi guarda il certificato, con quale motore si è lavorato e se corrispondeva alla sua firma.
func (f *FontiFiducia) firmaMotore(fid *Fiducia, adesso time.Time, rev *Revoche) string {
	exe := f.Motore
	if exe == "" {
		exe, _ = os.Readlink("/proc/self/exe")
	}
	var firma []byte
	var dove string
	cand := []string{exe + ".firma"}
	if exe == "/usr/bin/remotix-install" {
		// il motore del pacchetto: la sua firma sta fra i dati del pacchetto (un file .firma in
		// /usr/bin non ci sta). `[M]` 30 set: prima valeva per ogni motore, e un motore copiato altrove
		// veniva confrontato con la firma di un altro binario
		cand = append(cand, "/usr/share/remotix-install/remotix-install.firma")
	}
	for _, p := range cand {
		if b, err := os.ReadFile(p); err == nil {
			firma, dove = b, p
			break
		}
	}
	if firma == nil {
		fid.Guardati = append(fid.Guardati, Guardato{"motore", exe, 0, "firma assente"})
		fid.Messaggi = append(fid.Messaggi, Msg("RX-TRUST-015", exe))
		return "assente"
	}
	dati, err := os.ReadFile(exe)
	if err != nil {
		fid.Guardati = append(fid.Guardati, Guardato{"motore", exe, 0, "il binario non si legge: " + err.Error()})
		return "NON VALIDA"
	}
	e, err := VerificaFirma(f.Radici, dati, firma, "motore", adesso, rev)
	if err != nil {
		fid.Guardati = append(fid.Guardati, Guardato{"motore", dove, 0, err.Error()})
		return "NON VALIDA"
	}
	fid.Guardati = append(fid.Guardati, Guardato{"motore", dove, 0, "firma valida (" + e.Sottochiave + ")"})
	return "verificata (" + e.Sottochiave + ")"
}

// ControllaFreschezza: il catalogo scelto non è scaduto e questo motore lo capisce.
func ControllaFreschezza(c *Catalogo, adesso time.Time) error {
	scad, err := time.Parse("2006-01-02", c.Scadenza)
	if err != nil {
		return Errore("RX-TRUST-004", "scadenza "+c.Scadenza)
	}
	if adesso.After(scad.Add(24 * time.Hour)) {
		return Errore("RX-TRUST-002", "scaduto il "+c.Scadenza)
	}
	if ConfrontaVersioni(VersioneMotore, c.MotoreMinimo) < 0 {
		return Errore("RX-TRUST-003", "serve "+c.MotoreMinimo+", questo è "+VersioneMotore)
	}
	return nil
}
