// Package ui: what the TUI shows (T9, phases/17 §6.6.1, DECISIONI §10.14, §10.31).
//
//   - the SESSION: the engine's side, as root. It examines the machine, makes the plan (with the chosen
//     port), applies it. It is the engine and nothing else: the same functions as the command line (Preflight,
//     Evaluate, QuestionsToAsk, InstallPlan, Apply). The TUI, which runs as root in the terminal, uses it
//     directly (the GUI, which reached it through pkexec, was removed on 10 Oct: §10.31);
//   - the VIEW: the engine's objects told in plain words (view.go).
//
// ⛔ No installation logic here: what to ask and what to do is decided by the engine.
package ui

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

	"remotix/installer/engine"
)

// CheckReport: what the engine knows about the machine (phases 0-2), for the first screen.
type CheckReport struct {
	Trust  *engine.Trust   `json:"trust"`
	ProfileV *engine.ProfileV  `json:"profile"`
	Report *engine.Report  `json:"compatibility"`
	Questions  *engine.Questions   `json:"questions"`
	Error   *engine.Message `json:"error,omitempty"` // phase 0 does not pass: nothing more to show
}

// Outcome: how the operation ended.
type Outcome struct {
	Operation     string              `json:"operation"`
	State          engine.State        `json:"state"`
	Folder       string              `json:"dir"`
	Certificate    *engine.Certificate `json:"certificate,omitempty"`
	Messages       []engine.Message  `json:"messages"`
	Addresses      []string            `json:"addresses"`
	FingerprintTLS string              `json:"tls_fingerprint,omitempty"`
	Error         *engine.Message   `json:"error,omitempty"`
}

// Engine: what the interface can ask. The Session implements it (in this process, as root);
// the TUI tests put in a fake one.
type Engine interface {
	Check(port int) (*CheckReport, error)
	Piano(entries map[string]string) (*engine.Piano, error)
	Apply(digest string, events func(engine.PublicEvent)) (*Outcome, error)
	Stop()
	Close()
}

// Config: where the catalogue comes from and where to install (the same options as the command line).
type Config struct {
	Operations string
	// Fonti: phase 0 TRUST (the command line knows how to build it: the engine's catalogue)
	Fonti func() *engine.TrustSources
	// Base: the installation options that are not asked (the .run's packages folder)
	Base engine.InstallOptions
	// Chi: the person approving (for the log); Modo: from which interface
	Chi, Modo string
}

// Session: the engine, as root.
type Session struct {
	C      Config
	cat    *engine.Catalog
	fid    *engine.Trust
	env    *engine.Environment
	prof   *engine.ProfileV
	rap    *engine.Report
	port  int
	piano  *engine.Piano
	file   string
	stopped  atomic.Bool
	block sync.Mutex
}

// FreshSession: the engine for an interface.
func FreshSession(c Config) *Session { return &Session{C: c} }

func messageOf(err error) *engine.Message {
	var e *engine.ErrorRX
	if errors.As(err, &e) {
		m := e.M
		return &m
	}
	m := engine.Message{Codice: "RX-UI-005", Severity: engine.BLOCKING, Testo: err.Error()}
	return &m
}

// Check: phases 0-2 read-only (like «verify»), and the questions to ask.
func (s *Session) Check(port int) (*CheckReport, error) {
	s.block.Lock()
	defer s.block.Unlock()
	if port == 0 {
		port = 7447
	}
	cat, fid, err := s.C.Fonti().Trusted(time.Now())
	if err != nil {
		return &CheckReport{Trust: fid, Error: messageOf(err)}, nil
	}
	s.cat, s.fid = cat, fid
	s.env = engine.RealEnvironment()
	s.examine(port)
	return &CheckReport{Trust: fid, ProfileV: s.prof, Report: s.rap,
		Questions: engine.QuestionsToAsk(s.env, port)}, nil
}

func (s *Session) examine(port int) {
	s.port = port
	s.prof = engine.Preflight(s.env, engine.PreflightOptions{Porta: port, Pacchetti: s.cat.Components()})
	s.rap = engine.Evaluate(s.cat, s.prof)
}

// Piano: the plan with the chosen port (InstallPlan, like `install`), written in
// /var/lib/remotix/plans/. A port different from the one examined redoes the examination (the port is in the profile).
func (s *Session) Piano(entries map[string]string) (*engine.Piano, error) {
	s.block.Lock()
	defer s.block.Unlock()
	if s.cat == nil {
		return nil, errors.New("run the check first")
	}
	port, _ := strconv.Atoi(entries["port"])
	if port != 0 && port != s.port {
		s.examine(port)
	}
	o := s.C.Base
	o.Porta = s.port
	m := &engine.Engine{Env: s.env, Folder: s.C.Operations}
	if in, err := m.CheckInstallation(); err == nil && in != nil {
		o.Update = true
	}
	p, err := engine.InstallPlan(s.prof, s.rap, s.cat, s.env, o)
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(filepath.Dir(s.C.Operations), engine.PlansFolder)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return nil, err
	}
	s.file = filepath.Join(dir, p.ID+".json")
	if err := engine.WriteJSON(s.file, p); err != nil {
		return nil, err
	}
	s.piano = p
	return p, nil
}

// Apply: the consent (a single «confirm», on the plan with the digest the person saw) and the
// engine's phases 4-8; the events arrive while it works.
func (s *Session) Apply(digest string, events func(engine.PublicEvent)) (*Outcome, error) {
	s.block.Lock()
	defer s.block.Unlock()
	if s.piano == nil {
		return nil, errors.New("no plan")
	}
	if digest != s.piano.Digest() {
		return &Outcome{Error: messageOf(engine.Error("RX-PIANO-005", ""))}, nil
	}
	s.piano.Approval = &engine.Approval{Da: s.C.Chi, At: time.Now().UTC().Format(time.RFC3339),
		Modo: s.C.Modo, DigestPiano: s.piano.Digest()}
	if err := engine.WriteJSON(s.file, s.piano); err != nil {
		return nil, err
	}
	m := &engine.Engine{Env: s.env, Folder: s.C.Operations, Fonti: s.C.Fonti(), Porta: s.port,
		Ev: &engine.Events{W: &eventLines{f: events}, JSON: true}, Stopped: s.stopped.Load}
	op, err := m.Apply(s.file, false, s.C.Chi)
	es := &Outcome{Messages: []engine.Message{}}
	if op != nil {
		es.Operation, es.State, es.Folder = op.ID, op.State, op.Folder
		var c engine.Certificate
		if engine.ReadJSON(filepath.Join(op.Folder, "certificate.json"), &c) == nil {
			es.Certificate = &c
		}
	}
	if err != nil {
		es.Error = messageOf(err)
	}
	es.Addresses = Addresses()
	es.FingerprintTLS = FingerprintTLS("/var/lib/remotix/certificates/page.pem")
	return es, nil
}

// Stop: between one step and the next the operation stops and is undone (RX-AZIONE-006).
func (s *Session) Stop() { s.stopped.Store(true) }

// Close: nothing to close in this process.
func (s *Session) Close() {}

// eventLines: the engine's JSON events (one line each) become calls.
type eventLines struct {
	f   func(engine.PublicEvent)
	buf []byte
}

func (r *eventLines) Write(b []byte) (int, error) {
	r.buf = append(r.buf, b...)
	for {
		i := strings.IndexByte(string(r.buf), '\n')
		if i < 0 {
			return len(b), nil
		}
		var ev engine.PublicEvent
		if json.Unmarshal(r.buf[:i], &ev) == nil && r.f != nil {
			r.f(ev)
		}
		r.buf = r.buf[i+1:]
	}
}

// Addresses: the addresses to write in the welcome (first the non-loopback IPv4 ones), then the name.
func Addresses() []string {
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

// FingerprintTLS: the SHA-256 of the page's certificate (the one the browser shows), if there is one.
func FingerprintTLS(fpath string) string {
	b, err := os.ReadFile(fpath)
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
	var parts []string
	for i := 0; i < len(x); i += 2 {
		parts = append(parts, x[i:i+2])
	}
	return strings.Join(parts, ":")
}
