// Package interfaccia: quel che la TUI mostra (T9, fasi/17 §6.6.1, DECISIONI §10.14, §10.31).
//
//   - la SESSIONE: il lato del motore, da root. Esamina la macchina, fa il piano dalle risposte,
//     lo applica. È il motore e basta: le stesse funzioni della riga di comando (Preflight, Valuta,
//     DomandeDaFare, PianoDaScelte, Applica). La TUI, che gira da root nel terminale, la usa
//     direttamente (la GUI, che la raggiungeva con pkexec, è stata tolta il 10 ott: §10.31);
//   - la VISTA: gli oggetti del motore detti in parole comuni (vista.go).
//
// ⛔ Nessuna logica d'installazione qui: che cosa chiedere e che cosa fare lo decide il motore.
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

// Controllo: quel che il motore sa della macchina (fasi 0-2), per la prima schermata.
type Controllo struct {
	Fiducia  *motore.Fiducia   `json:"fiducia"`
	Profilo  *motore.Profilo   `json:"profilo"`
	Rapporto *motore.Rapporto  `json:"compatibilita"`
	Domande  *motore.Domande   `json:"domande"`
	Errore   *motore.Messaggio `json:"errore,omitempty"` // la fase 0 non passa: niente da mostrare oltre
}

// Esito: com'è finita l'operazione.
type Esito struct {
	Operazione  string              `json:"operazione"`
	Stato       motore.Stato        `json:"stato"`
	Cartella    string              `json:"cartella"`
	Certificato *motore.Certificato `json:"certificato,omitempty"`
	Messaggi    []motore.Messaggio  `json:"messaggi"`
	Indirizzi   []string            `json:"indirizzi"`
	ImprontaTLS string              `json:"impronta_tls,omitempty"`
	Errore      *motore.Messaggio   `json:"errore,omitempty"`
}

// Motore: quel che l'interfaccia può chiedere. La realizza la Sessione (in questo processo, da root);
// le prove della TUI ne mettono una finta.
type Motore interface {
	Controlla(porta int) (*Controllo, error)
	Piano(voci map[string]string) (*motore.Piano, error)
	Applica(digest string, eventi func(motore.EventoPubblico)) (*Esito, error)
	Ferma()
	Chiudi()
}

// Config: da dove viene il catalogo e dove si installa (le stesse opzioni della riga di comando).
type Config struct {
	Operazioni string
	Archivio   string
	Canale     string
	// Fonti: la fase 0 TRUST (la riga di comando sa costruirla: il catalogo del motore)
	Fonti func() *motore.FontiFiducia
	// Base: le opzioni d'installazione che non si chiedono (archivio, chiave dell'archivio)
	Base motore.OpzioniInstallazione
	// Chi: la persona che approva (per il registro); Modo: da quale interfaccia
	Chi, Modo string
}

// Sessione: il motore, da root.
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

// NuovaSessione: il motore per un'interfaccia.
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

// Controlla: fasi 0-2 in sola lettura (come «verifica»), e le domande da fare.
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
		Domande: motore.DomandeDaFare(s.prof, s.rap, cat, s.amb, porta, s.C.Base.Archivio != "", "")}, nil
}

func (s *Sessione) esamina(porta int) {
	s.porta = porta
	s.prof = motore.Preflight(s.amb, motore.OpzioniPreflight{Porta: porta, Pacchetti: s.cat.Componenti()})
	s.rap = motore.Valuta(s.cat, s.prof)
}

// Piano: il piano dalle risposte (PianoDaScelte), scritto in /var/lib/remotix/piani/ come quello
// della riga di comando. Una porta diversa da quella esaminata rifà l'esame (la porta è nel profilo).
func (s *Sessione) Piano(voci map[string]string) (*motore.Piano, error) {
	s.blocco.Lock()
	defer s.blocco.Unlock()
	if s.cat == nil {
		return nil, errors.New("prima il controllo")
	}
	porta, _ := strconv.Atoi(voci["porta"])
	if porta != 0 && porta != s.porta {
		s.esamina(porta)
	}
	o := s.C.Base
	o.Porta = s.porta
	p, err := motore.PianoDaScelte(voci, s.prof, s.rap, s.cat, s.amb, o)
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(filepath.Dir(s.C.Operazioni), "piani")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return nil, err
	}
	s.file = filepath.Join(dir, "piano-"+p.ID+".json")
	if err := motore.ScriviJSON(s.file, p); err != nil {
		return nil, err
	}
	s.piano = p
	return p, nil
}

// Applica: il consenso (un solo «conferma», sul piano col digest che la persona ha visto) e le
// fasi 4-8 del motore; gli eventi arrivano mentre lavora.
func (s *Sessione) Applica(digest string, eventi func(motore.EventoPubblico)) (*Esito, error) {
	s.blocco.Lock()
	defer s.blocco.Unlock()
	if s.piano == nil {
		return nil, errors.New("nessun piano")
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
		if motore.LeggiJSON(filepath.Join(op.Cartella, "certificato.json"), &c) == nil {
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

// Ferma: fra un passo e l'altro l'operazione si ferma e si annulla (RX-AZIONE-006).
func (s *Sessione) Ferma() { s.fermo.Store(true) }

// Chiudi: niente da chiudere in questo processo.
func (s *Sessione) Chiudi() {}

// righeEventi: gli eventi JSON del motore (una riga ciascuno) diventano chiamate.
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

// Indirizzi: gli indirizzi da scrivere nel benvenuto (prima gli IPv4 non di loopback), poi il nome.
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

// ImprontaTLS: lo SHA-256 del certificato della pagina (quello che il browser mostra), se c'è.
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
