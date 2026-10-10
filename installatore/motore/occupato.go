package motore

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// The package manager busy with another program. On a Debian just switched on, unattended-upgrades
// holds dpkg's lock for minutes and apt-get fails at once («Could not get lock /var/lib/dpkg/lock-frontend.
// It is held by process … (unattended-upgr)»). Before launching the manager the engine looks at who holds
// its locks, says so (RX-PACCHETTI-007) and waits up to TettoOccupato; beyond it, it stops having touched
// nothing (RX-PACCHETTI-008).
//
// Where the manager can wait by itself it is told to (DECISIONI §10.36), for the moment between the
// look and the launch: apt with DPkg::Lock::Timeout, zypper with ZYPP_LOCK_TIMEOUT (ambiente.go). They do
// not cover everything, hence the look: `apt-get update` fails at once on the lists' lock even with
// the option (apt 3.0.3, [M] 10 Oct, debian13 container), dnf 4 waits without a limit, dnf 5 and pacman
// do not wait.
//
// Who holds a lock, by its kind:
//   - "lock": a kernel lock (fcntl or flock) on the file — /proc/locks, by inode;
//   - "pid": a file with the holder's pid inside (dnf 4, zypper) — if that process is alive;
//   - "open": a file that exists while it is held (pacman's db.lck) — whoever has it open. A db.lck
//     that nobody has open was left by a pacman that died: it is not a wait, and the engine does not
//     remove it (Integro says so: RX-PACCHETTI-004).

type lucchetto struct{ percorso, tipo string }

var lucchetti = map[string][]lucchetto{
	"debian": {{"/var/lib/dpkg/lock-frontend", "lock"}, {"/var/lib/dpkg/lock", "lock"},
		{"/var/lib/apt/lists/lock", "lock"}, {"/var/cache/apt/archives/lock", "lock"}},
	// /var/lib/rpm is a link to /usr/lib/sysimage/rpm on the newer ones: the same inode, looked at twice
	"fedora": {{"/var/lib/rpm/.rpm.lock", "lock"}, {"/usr/lib/sysimage/rpm/.rpm.lock", "lock"},
		{"/run/dnf/rpmtransaction.lock", "lock"},                                            // dnf 5
		{"/var/lib/dnf/rpmdb_lock.pid", "pid"}, {"/var/cache/dnf/metadata_lock.pid", "pid"}, // dnf 4
		{"/var/cache/dnf/download_lock.pid", "pid"}},
	"suse": {{"/run/zypp.pid", "pid"}, {"/var/lib/rpm/.rpm.lock", "lock"}, {"/usr/lib/sysimage/rpm/.rpm.lock", "lock"}},
	"arch": {{"/var/lib/pacman/db.lck", "open"}},
}

// TettoOccupato: how long the engine waits for a busy manager. Automatic updates on a machine just
// switched on take a few minutes; beyond this it is something else, and the person decides.
var TettoOccupato = 15 * time.Minute

var passoOccupato = 2 * time.Second

// attendiGestore: while another program holds the family's manager, the engine says who (once for each
// holder) and waits; beyond TettoOccupato, RX-PACCHETTI-008.
func attendiGestore(a *Ambiente, fam string) error {
	fine := time.Now().Add(TettoOccupato)
	detto := ""
	for {
		chi := chiTiene(a, fam)
		if chi == "" {
			return nil
		}
		if time.Now().After(fine) {
			return Errore("RX-PACCHETTI-008", chi)
		}
		if chi != detto {
			a.avvisa(Msg("RX-PACCHETTI-007", fmt.Sprintf("%s; waiting up to %s", chi, TettoOccupato)))
			detto = chi
		}
		time.Sleep(passoOccupato)
	}
}

// chiTiene: «pid 1234 (unattended-upgr) holds /var/lib/dpkg/lock-frontend», or "" if the manager is free.
func chiTiene(a *Ambiente, fam string) string {
	for _, l := range lucchetti[fam] {
		var pid []int
		switch l.tipo {
		case "lock":
			pid = pidDiBlocco(a, l.percorso)
		case "pid":
			pid = pidDiFile(a, l.percorso)
		case "open":
			pid = chiApre(a, l.percorso)
		}
		for _, p := range pid {
			if p > 0 && p != os.Getpid() {
				return fmt.Sprintf("pid %d (%s) holds %s", p, nomeProcesso(a, p), l.percorso)
			}
		}
	}
	return ""
}

// pidDiBlocco: the holders of a kernel lock on the file. /proc/locks: «3: POSIX ADVISORY WRITE 1234
// 00:8a:858800 0 EOF»; the «->» lines are those waiting, not holding. Only the inode is compared: on
// btrfs the device in stat is not the one in /proc/locks.
func pidDiBlocco(a *Ambiente, percorso string) []int {
	st, err := os.Stat(a.P(percorso))
	if err != nil {
		return nil
	}
	s, ok := st.Sys().(*syscall.Stat_t)
	if !ok {
		return nil
	}
	b, err := os.ReadFile(a.P("/proc/locks"))
	if err != nil {
		return nil
	}
	ino := ":" + strconv.FormatUint(s.Ino, 10)
	var r []int
	for _, riga := range strings.Split(string(b), "\n") {
		c := strings.Fields(riga)
		if len(c) < 6 || c[1] == "->" || !strings.HasSuffix(c[5], ino) {
			continue
		}
		if p, err := strconv.Atoi(c[4]); err == nil {
			r = append(r, p)
		}
	}
	return r
}

// pidDiFile: the pid written in the file, if that process is alive.
func pidDiFile(a *Ambiente, percorso string) []int {
	b, err := os.ReadFile(a.P(percorso))
	if err != nil {
		return nil
	}
	p, err := strconv.Atoi(strings.TrimSpace(string(b)))
	if err != nil {
		return nil
	}
	if _, err := os.Stat(a.P("/proc/" + strconv.Itoa(p))); err != nil {
		return nil
	}
	return []int{p}
}

// chiApre: the processes that have the file open (its absolute path among their /proc/<pid>/fd).
func chiApre(a *Ambiente, percorso string) []int {
	if _, err := os.Stat(a.P(percorso)); err != nil {
		return nil
	}
	fd, _ := filepath.Glob(a.P("/proc/[0-9]*/fd/*"))
	var r []int
	for _, f := range fd {
		if l, err := os.Readlink(f); err == nil && l == percorso {
			if p, err := strconv.Atoi(filepath.Base(filepath.Dir(filepath.Dir(f)))); err == nil {
				r = append(r, p)
			}
		}
	}
	return r
}

func nomeProcesso(a *Ambiente, pid int) string {
	b, err := os.ReadFile(a.P("/proc/" + strconv.Itoa(pid) + "/comm"))
	if err != nil {
		return "?"
	}
	return strings.TrimSpace(string(b))
}
