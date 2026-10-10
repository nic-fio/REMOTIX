// Package interfaccia: what the TUI shows (T9, fasi/17 §6.6.1, DECISIONI §10.14, §10.31).
//
//   - the SESSION: the engine's side, as root. It examines the machine, makes the plan (with the chosen
//     port), applies it. It is the engine and nothing else: the same functions as the command line (Preflight,
//     Evaluate, QuestionsToAsk, PlanInstallation, Apply). The TUI, which runs as root in the terminal, uses it
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

// Check: what the engine knows about the machine (phases 0-2), for the first screen.
type Check struct {
	Attestation *motore.Attestation `json:"trust"`
	Profile     *motore.Profile     `json:"profile"`
	Report      *motore.Report      `json:"compatibility"`
	Questions   *motore.Questions   `json:"questions"`
	Error       *motore.Message     `json:"error,omitempty"` // phase 0 does not pass: nothing more to show
}

// Outcome: how the operation ended.
type Outcome struct {
	Operation      string              `json:"operation"`
	State          motore.State        `json:"state"`
	Folder         string              `json:"dir"`
	Certificate    *motore.Certificate `json:"certificate,omitempty"`
	Messages       []motore.Message    `json:"messages"`
	Addresses      []string            `json:"addresses"`
	FingerprintTLS string              `json:"tls_fingerprint,omitempty"`
	Error          *motore.Message     `json:"error,omitempty"`
}

// Engine: what the interface can ask. The Session implements it (in this process, as root);
// the TUI tests put in a fake one.
type Engine interface {
	Verify(port int) (*Check, error)
	Piano(entries map[string]string) (*motore.Piano, error)
	Apply(digest string, events func(motore.PublicEvent)) (*Outcome, error)
	Stop()
	Shut()
}

// Config: where the catalogue comes from and where to install (the same options as the command line).
type Config struct {
	Operations string
	// Sources: phase 0 TRUST (the command line knows how to build it: the engine's catalogue)
	Sources func() *motore.TrustSources
	// Base: the installation options that are not asked (the .run's packages folder)
	Base motore.InstallOptions
	// Chi: the person approving (for the log); Manner: from which interface
	Chi, Manner string
}

// Session: the engine, as root.
type Session struct {
	C       Config
	cat     *motore.Catalog
	fid     *motore.Attestation
	amb     *motore.Environment
	prof    *motore.Profile
	rap     *motore.Report
	port    int
	piano   *motore.Piano
	file    string
	stopped atomic.Bool
	block   sync.Mutex
}

// NewSession: the engine for an interface.
func NewSession(c Config) *Session { return &Session{C: c} }

func messageOf(err error) *motore.Message {
	var e *motore.ErrorRX
	if errors.As(err, &e) {
		m := e.M
		return &m
	}
	m := motore.Message{Code: "RX-UI-005", Severity: motore.BLOCKING, Text: err.Error()}
	return &m
}

// Verify: phases 0-2 read-only (like «verifica»), and the questions to ask.
func (s *Session) Verify(port int) (*Check, error) {
	s.block.Lock()
	defer s.block.Unlock()
	if port == 0 {
		port = 7447
	}
	cat, fid, err := s.C.Sources().Trusted(time.Now())
	if err != nil {
		return &Check{Attestation: fid, Error: messageOf(err)}, nil
	}
	s.cat, s.fid = cat, fid
	s.amb = motore.RealEnvironment()
	s.examine(port)
	return &Check{Attestation: fid, Profile: s.prof, Report: s.rap,
		Questions: motore.QuestionsToAsk(s.amb, port)}, nil
}

func (s *Session) examine(port int) {
	s.port = port
	s.prof = motore.Preflight(s.amb, motore.PreflightOptions{Port: port, Packets: s.cat.Components()})
	s.rap = motore.Evaluate(s.cat, s.prof)
}

// Piano: the plan with the chosen port (PlanInstallation, like `install`), written in
// /var/lib/remotix/plans/. A port different from the one examined redoes the examination (the port is in the profile).
func (s *Session) Piano(entries map[string]string) (*motore.Piano, error) {
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
	o.Port = s.port
	m := &motore.Engine{Amb: s.amb, Folder: s.C.Operations}
	if in, err := m.CheckInstallation(); err == nil && in != nil {
		o.Update = true
	}
	p, err := motore.PlanInstallation(s.prof, s.rap, s.cat, s.amb, o)
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(filepath.Dir(s.C.Operations), motore.PlansFolder)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return nil, err
	}
	s.file = filepath.Join(dir, p.ID+".json")
	if err := motore.WriteJSON(s.file, p); err != nil {
		return nil, err
	}
	s.piano = p
	return p, nil
}

// Apply: the consent (a single «confirm», on the plan with the digest the person saw) and the
// engine's phases 4-8; the events arrive while it works.
func (s *Session) Apply(digest string, events func(motore.PublicEvent)) (*Outcome, error) {
	s.block.Lock()
	defer s.block.Unlock()
	if s.piano == nil {
		return nil, errors.New("no plan")
	}
	if digest != s.piano.Digest() {
		return &Outcome{Error: messageOf(motore.Error("RX-PIANO-005", ""))}, nil
	}
	s.piano.Approval = &motore.Approval{Da: s.C.Chi, TimeNow: time.Now().UTC().Format(time.RFC3339),
		Manner: s.C.Manner, DigestPiano: s.piano.Digest()}
	if err := motore.WriteJSON(s.file, s.piano); err != nil {
		return nil, err
	}
	m := &motore.Engine{Amb: s.amb, Folder: s.C.Operations, Sources: s.C.Sources(), Port: s.port,
		Ev: &motore.Events{W: &eventLines{f: events}, JSON: true}, Stopped: s.stopped.Load}
	op, err := m.Apply(s.file, false, s.C.Chi)
	es := &Outcome{Messages: []motore.Message{}}
	if op != nil {
		es.Operation, es.State, es.Folder = op.ID, op.State, op.Folder
		var c motore.Certificate
		if motore.ReadJSON(filepath.Join(op.Folder, "certificate.json"), &c) == nil {
			es.Certificate = &c
		}
	}
	if err != nil {
		es.Error = messageOf(err)
	}
	es.Addresses = Addresses()
	es.FingerprintTLS = FingerprintTLS("/var/lib/remotix/certificates/page_v.pem")
	return es, nil
}

// Stop: between one step and the next the operation stops and is undone (RX-AZIONE-006).
func (s *Session) Stop() { s.stopped.Store(true) }

// Shut: nothing to close in this process.
func (s *Session) Shut() {}

// eventLines: the engine's JSON events (one line each) become calls.
type eventLines struct {
	f   func(motore.PublicEvent)
	buf []byte
}

func (r *eventLines) Write(b []byte) (int, error) {
	r.buf = append(r.buf, b...)
	for {
		i := strings.IndexByte(string(r.buf), '\n')
		if i < 0 {
			return len(b), nil
		}
		var ev motore.PublicEvent
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
