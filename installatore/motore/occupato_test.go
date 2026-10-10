package motore

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"
)

// macchinaOccupata: a fake root where process 4242 «unattended-upgr» holds dpkg's frontend lock.
func macchinaOccupata(t *testing.T) (*Ambiente, string) {
	r := t.TempDir()
	scrivi := func(p, s string) {
		os.MkdirAll(filepath.Dir(filepath.Join(r, p)), 0o755)
		os.WriteFile(filepath.Join(r, p), []byte(s), 0o644)
	}
	scrivi("var/lib/dpkg/lock-frontend", "")
	st, _ := os.Stat(filepath.Join(r, "var/lib/dpkg/lock-frontend"))
	ino := st.Sys().(*syscall.Stat_t).Ino
	// a line of someone waiting («->») does not count, and neither does another inode
	locks := fmt.Sprintf("1: POSIX  ADVISORY  WRITE 777 00:8a:%d 0 EOF\n2: -> POSIX  ADVISORY  WRITE 778 00:8a:%d 0 EOF\n3: POSIX  ADVISORY  WRITE 4242 00:8a:%d 0 EOF\n", ino+1, ino, ino)
	scrivi("proc/locks", locks)
	scrivi("proc/4242/comm", "unattended-upgr\n")
	return &Ambiente{Radice: r}, r
}

func TestChiTieneIlGestore(t *testing.T) {
	a, r := macchinaOccupata(t)
	if c := chiTiene(a, "debian"); c != "pid 4242 (unattended-upgr) holds /var/lib/dpkg/lock-frontend" {
		t.Fatalf("holder: %q", c)
	}
	// dnf 4 / zypper: the pid in the file, only if that process is alive
	os.MkdirAll(filepath.Join(r, "run"), 0o755)
	os.WriteFile(filepath.Join(r, "run/zypp.pid"), []byte("4242\n"), 0o644)
	if c := chiTiene(a, "suse"); !strings.HasPrefix(c, "pid 4242 (unattended-upgr)") {
		t.Fatalf("zypper: %q", c)
	}
	os.WriteFile(filepath.Join(r, "run/zypp.pid"), []byte("999\n"), 0o644)
	if c := chiTiene(a, "suse"); c != "" {
		t.Fatalf("a dead pid holds nothing: %q", c)
	}
	// pacman: whoever has db.lck open; a db.lck nobody has open is not a wait (Integro says it)
	os.MkdirAll(filepath.Join(r, "var/lib/pacman"), 0o755)
	os.WriteFile(filepath.Join(r, "var/lib/pacman/db.lck"), nil, 0o644)
	if c := chiTiene(a, "arch"); c != "" {
		t.Fatalf("stale db.lck: %q", c)
	}
	g := &gestorePacman{a}
	if ok, det, err := g.Integro(); err != nil || ok || !strings.Contains(det, "no program has it open") {
		t.Fatalf("stale db.lck: %v %q %v", ok, det, err)
	}
	if _, err := os.Stat(filepath.Join(r, "var/lib/pacman/db.lck")); err != nil {
		t.Fatal("the stale db.lck must stay: it is not the engine's to remove")
	}
	os.MkdirAll(filepath.Join(r, "proc/4242/fd"), 0o755)
	os.Symlink("/var/lib/pacman/db.lck", filepath.Join(r, "proc/4242/fd/3"))
	if c := chiTiene(a, "arch"); !strings.HasPrefix(c, "pid 4242 ") {
		t.Fatalf("pacman: %q", c)
	}
}

// The manager busy: the engine says who, waits; when it is free it goes on, beyond the cap it stops
// without launching the manager.
func TestAttendeIlGestore(t *testing.T) {
	tetto, passo := TettoOccupato, passoOccupato
	defer func() { TettoOccupato, passoOccupato = tetto, passo }()
	TettoOccupato, passoOccupato = 300*time.Millisecond, 10*time.Millisecond
	a, r := macchinaOccupata(t)
	var detti []Messaggio
	a.Avvisa = func(m Messaggio) { detti = append(detti, m) }
	lanciati := 0
	a.Esegui = func(time.Duration, string, ...string) (string, int, error) { lanciati++; return "", 0, nil }
	g := &gestoreApt{a}

	if err := g.Installa(nil, []string{"x"}); CodiceDi(err) != "RX-PACCHETTI-008" || !strings.Contains(err.Error(), "unattended-upgr") {
		t.Fatalf("beyond the cap: %v", err)
	}
	if lanciati != 0 {
		t.Fatalf("apt-get launched %d times while busy", lanciati)
	}
	if len(detti) != 1 || detti[0].Codice != "RX-PACCHETTI-007" || !strings.Contains(detti[0].Dettaglio, "pid 4242 (unattended-upgr)") {
		t.Fatalf("said once, with who: %+v", detti)
	}
	// the plan: blocked with the reason, not with «cannot install» (RX-PACCHETTI-005)
	if _, err := g.Simula(nil, []string{"x"}); messaggioSimula(err).Codice != "RX-PACCHETTI-008" {
		t.Fatalf("simulation: %v", err)
	}

	// it frees itself while the engine waits: it goes on
	go func() {
		time.Sleep(50 * time.Millisecond)
		os.WriteFile(filepath.Join(r, "proc/locks"), nil, 0o644)
	}()
	if err := g.Installa(nil, []string{"x"}); err != nil || lanciati != 1 {
		t.Fatalf("after the wait: %v, launched %d", err, lanciati)
	}
}

// uninstall --purge: nothing of the engine stays in /var/lib/remotix, plans included.
func TestPurgeTogliePiani(t *testing.T) {
	r := t.TempDir()
	base := filepath.Join(r, "var/lib/remotix")
	for _, f := range []string{"operations/20261010-1/plan.json", CartellaPiani + "/p1.json", FileVersioniAnnotate, FileIscrizioni} {
		os.MkdirAll(filepath.Dir(filepath.Join(base, f)), 0o700)
		os.WriteFile(filepath.Join(base, f), []byte("{}"), 0o600)
	}
	m := &Motore{Cartella: filepath.Join(base, "operations")}
	if err := m.PulisciStoria(true); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(base); !os.IsNotExist(err) {
		v, _ := filepath.Glob(filepath.Join(base, "*"))
		t.Fatalf("/var/lib/remotix stays: %v", v)
	}
}
