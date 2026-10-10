// Package interfaccia: what the TUI shows (T9, fasi/17 §6.6.1, DECISIONI §10.14, §10.31).
//
//   - the SESSION: the engine's side, as root. It examines the machine, makes the plan (with the chosen
//     port), applies it. It is the engine and nothing else: the same functions as the command line (Preflight,
//     Valuta, DomandeDaFare, PianoInstallazione, Applica). The TUI, which runs as root in the terminal, uses it
//     directly (the GUI, which reached it through pkexec, was removed on 10 Oct: §10.31);
//   - the VIEW: the engine's objects told in plain words (vista.go).
//
// ⛔ No installation logic here: what to ask and what to do is decided by the engine.
package interfaccia

import (
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"errors"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"remotix/installatore/motore"
)

// Controllo: what the engine knows about the machine (phases 0-2), for the first screen.
type Controllo struct {
	Fiducia  *motore.Fiducia   `json:"trust"`
	Profilo  *motore.Profilo   `json:"profile"`
	Rapporto *motore.Rapporto  `json:"compatibility"`
	Domande  *motore.Domande   `json:"questions"`
	Errore   *motore.Messaggio `json:"error,omitempty"` // phase 0 does not pass: nothing more to show
}

// Esito: how the operation ended.
type Esito struct {
	Operazione  string              `json:"operation"`
	Stato       motore.Stato        `json:"state"`
	Cartella    string              `json:"dir"`
	Certificato *motore.Certificato `json:"certificate,omitempty"`
	Messaggi    []motore.Messaggio  `json:"messages"`
	Indirizzi   []string            `json:"addresses"`
	ImprontaTLS string              `json:"tls_fingerprint,omitempty"`
	Errore      *motore.Messaggio   `json:"error,omitempty"`
}

// Motore: what the interface can ask. The Sessione implements it (in this process, as root);
// the TUI tests put in a fake one.
type Motore interface {
	Controlla(porta int) (*Controllo, error)
	Piano(voci map[string]string) (*motore.Piano, error)
	Applica(digest string, eventi func(motore.EventoPubblico)) (*Esito, error)
	Ferma()
	Chiudi()
}

// Config: where the catalogue comes from and where to install (the same options as the command line).
type Config struct {
	Operazioni string
	// Fonti: phase 0 TRUST (the command line knows how to build it: the engine's catalogue)
	Fonti func() *motore.FontiFiducia
	// Base: the installation options that are not asked (the .run's packages folder)
	Base motore.OpzioniInstallazione
	// Chi: the person approving (for the log); Modo: from which interface
	Chi, Modo string
}

// Sessione: the engine, as root.
type Sessione struct {
	C      Config
	cat    *motore.Catalogo
	fid    *motore.Fiducia
	amb    *motore.Ambiente
	prof   *motore.Profilo
	rap    *motore.Rapporto
	porta  int
	piano  *motore.Piano
	file   string
	fermo  atomic.Bool
	blocco sync.Mutex
}

// NuovaSessione: the engine for an interface.
func NuovaSessione(c Config) *Sessione { return &Sessione{C: c} }

func messaggioDi(err error) *motore.Messaggio {
	var e *motore.ErroreRX
	if errors.As(err, &e) {
		m := e.M
		return &m
	}
	m := motore.Messaggio{Codice: "RX-UI-005", Gravita: motore.BLOCCANTE, Testo: err.Error()}
	return &m
}

// Controlla: phases 0-2 read-only (like «verifica»), and the questions to ask.
func (s *Sessione) Controlla(porta int) (*Controllo, error) {
	s.blocco.Lock()
	defer s.blocco.Unlock()
	if porta == 0 {
		porta = 7447
	}
	cat, fid, err := s.C.Fonti().Fidati(time.Now())
	if err != nil {
		return &Controllo{Fiducia: fid, Errore: messaggioDi(err)}, nil
	}
	s.cat, s.fid = cat, fid
	s.amb = motore.AmbienteVero()
	s.esamina(porta)
	return &Controllo{Fiducia: fid, Profilo: s.prof, Rapporto: s.rap,
		Domande: motore.DomandeDaFare(s.amb, porta)}, nil
}

func (s *Sessione) esamina(porta int) {
	s.porta = porta
	s.prof = motore.Preflight(s.amb, motore.OpzioniPreflight{Porta: porta, Pacchetti: s.cat.Componenti()})
	s.rap = motore.Valuta(s.cat, s.prof)
}

// Piano: the plan with the chosen port (PianoInstallazione, like `install`), written in
// /var/lib/remotix/plans/. A port different from the one examined redoes the examination (the port is in the profile).
func (s *Sessione) Piano(voci map[string]string) (*motore.Piano, error) {
	s.blocco.Lock()
	defer s.blocco.Unlock()
	if s.cat == nil {
		return nil, errors.New("run the check first")
	}
	porta, _ := strconv.Atoi(voci["port"])
	if porta != 0 && porta != s.porta {
		s.esamina(porta)
	}
	o := s.C.Base
	o.Porta = s.porta
	m := &motore.Motore{Amb: s.amb, Cartella: s.C.Operazioni}
	if in, err := m.ControllaInstallazione(); err == nil && in != nil {
		o.Aggiornamento = true
	}
	p, err := motore.PianoInstallazione(s.prof, s.rap, s.cat, s.amb, o)
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(filepath.Dir(s.C.Operazioni), "plans")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return nil, err
	}
	s.file = filepath.Join(dir, p.ID+".json")
	if err := motore.ScriviJSON(s.file, p); err != nil {
		return nil, err
	}
	s.piano = p
	return p, nil
}

// Applica: the consent (a single «confirm», on the plan with the digest the person saw) and the
// engine's phases 4-8; the events arrive while it works.
func (s *Sessione) Applica(digest string, eventi func(motore.EventoPubblico)) (*Esito, error) {
	s.blocco.Lock()
	defer s.blocco.Unlock()
	if s.piano == nil {
		return nil, errors.New("no plan")
	}
	if digest != s.piano.Digest() {
		return &Esito{Errore: messaggioDi(motore.Errore("RX-PIANO-005", ""))}, nil
	}
	s.piano.Approvazione = &motore.Approvazione{Da: s.C.Chi, Ora: time.Now().UTC().Format(time.RFC3339),
		Modo: s.C.Modo, DigestPiano: s.piano.Digest()}
	if err := motore.ScriviJSON(s.file, s.piano); err != nil {
		return nil, err
	}
	m := &motore.Motore{Amb: s.amb, Cartella: s.C.Operazioni, Fonti: s.C.Fonti(), Porta: s.porta,
		Ev: &motore.Eventi{W: &righeEventi{f: eventi}, JSON: true}, Fermata: s.fermo.Load}
	op, err := m.Applica(s.file, false, s.C.Chi)
	es := &Esito{Messaggi: []motore.Messaggio{}}
	if op != nil {
		es.Operazione, es.Stato, es.Cartella = op.ID, op.Stato, op.Cartella
		var c motore.Certificato
		if motore.LeggiJSON(filepath.Join(op.Cartella, "certificate.json"), &c) == nil {
			es.Certificato = &c
		}
	}
	if err != nil {
		es.Errore = messaggioDi(err)
	}
	es.Indirizzi = Indirizzi()
	es.ImprontaTLS = ImprontaTLS("/var/lib/remotix/certificati/pagina.pem")
	return es, nil
}

// Ferma: between one step and the next the operation stops and is undone (RX-AZIONE-006).
func (s *Sessione) Ferma() { s.fermo.Store(true) }

// Chiudi: nothing to close in this process.
func (s *Sessione) Chiudi() {}

// righeEventi: the engine's JSON events (one line each) become calls.
type righeEventi struct {
	f   func(motore.EventoPubblico)
	buf []byte
}

func (r *righeEventi) Write(b []byte) (int, error) {
	r.buf = append(r.buf, b...)
	for {
		i := strings.IndexByte(string(r.buf), '\n')
		if i < 0 {
			return len(b), nil
		}
		var ev motore.EventoPubblico
		if json.Unmarshal(r.buf[:i], &ev) == nil && r.f != nil {
			r.f(ev)
		}
		r.buf = r.buf[i+1:]
	}
}

// Indirizzi: the addresses to write in the welcome (first the non-loopback IPv4 ones), then the name.
func Indirizzi() []string {
	var r []string
	if ifs, err := net.Interfaces(); err == nil {
		for _, i := range ifs {
			if i.Flags&net.FlagUp == 0 || i.Flags&net.FlagLoopback != 0 {
				continue
			}
			addrs, _ := i.Addrs()
			for _, a := range addrs {
				if n, ok := a.(*net.IPNet); ok && n.IP.To4() != nil {
					r = append(r, n.IP.String())
				}
			}
		}
	}
	if h, err := os.Hostname(); err == nil && h != "" {
		r = append(r, h)
	}
	return r
}

// ImprontaTLS: the SHA-256 of the page's certificate (the one the browser shows), if there is one.
func ImprontaTLS(percorso string) string {
	b, err := os.ReadFile(percorso)
	if err != nil {
		return ""
	}
	blk, _ := pem.Decode(b)
	if blk == nil {
		return ""
	}
	if _, err := x509.ParseCertificate(blk.Bytes); err != nil {
		return ""
	}
	h := sha256.Sum256(blk.Bytes)
	x := strings.ToUpper(hex.EncodeToString(h[:]))
	var parti []string
	for i := 0; i < len(x); i += 2 {
		parti = append(parti, x[i:i+2])
	}
	return strings.Join(parti, ":")
}
