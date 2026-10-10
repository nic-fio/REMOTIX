package motore

import (
	"bufio"
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// PREFLIGHT (phase 1, §6.0): knowing the system, READ-ONLY (R1). In here no
// function writes, creates, renames or changes permissions. Files are read (/etc, /sys, /proc, the
// dpkg and pacman databases, the libraries); logind, systemd and firewalld are asked over D-Bus
// (reads only: properties, queries); the only program launched is «rpm -q» on the RPM families
// (DECISIONI §10.14: closed list, ambiente.go), recorded in the profile. Test R1 checks it
// with the fingerprints of /etc before and after, in one container per family (prove/r1-contenitori.sh).

// OpzioniPreflight: the port to look at and the extra packages the catalogue wants to know about.
type OpzioniPreflight struct {
	Porta     int
	Pacchetti []string // components (labwc, gnome-session, the fonts…) requested by the catalogue
}

// Preflight builds the machine's profile.
func Preflight(a *Ambiente, o OpzioniPreflight) *Profilo {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	p := NuovoProfilo(o.Porta)
	prima := a.Annota
	a.Annota = func(r string) {
		p.Comandi = append(p.Comandi, r)
		if prima != nil {
			prima(r)
		}
	}
	defer func() { a.Annota = prima }()
	fam := distribuzione(a, p)
	sistema(a, p)
	pk := ArchivioPacchetti(a, fam, append(append(nomiDesktop(fam), pacchettiFissi...), o.Pacchetti...))
	desktop(a, p, fam, pk, o.Pacchetti)
	depositi(a, p)
	schede(a, p)
	codifica(a, p, fam)
	sicurezza(a, p)
	firewall(a, p, o.Porta)
	pam(a, p, fam)
	openssl(a, p, fam, pk)
	logind(a, p)
	gruppi(a, p)
	caratteri(a, p)
	p.Ordina()
	return p
}

// leggi a file of the machine; "" if it is not there.
func leggi(a *Ambiente, percorso string) (string, bool) {
	b, err := os.ReadFile(a.P(percorso))
	if err != nil {
		return "", false
	}
	return string(b), true
}

// OsRelease reads /etc/os-release (or /usr/lib/os-release).
func OsRelease(a *Ambiente) (map[string]string, string) {
	for _, f := range []string{"/etc/os-release", "/usr/lib/os-release"} {
		if t, ok := leggi(a, f); ok {
			m := map[string]string{}
			for _, riga := range strings.Split(t, "\n") {
				k, v, ok := strings.Cut(strings.TrimSpace(riga), "=")
				if !ok || strings.HasPrefix(k, "#") {
					continue
				}
				m[k] = strings.Trim(v, `"'`)
			}
			return m, f
		}
	}
	return nil, ""
}

// Famiglia: debian, fedora (RHEL and derivatives too), arch, suse, or "".
func Famiglia(id, idLike string) string {
	tutti := append([]string{id}, strings.Fields(idLike)...)
	for _, x := range tutti {
		switch x {
		case "debian", "ubuntu":
			return "debian"
		case "fedora", "rhel", "centos", "almalinux", "rocky":
			return "fedora"
		case "arch", "archlinux":
			return "arch"
		case "suse", "opensuse", "sles", "opensuse-tumbleweed", "opensuse-leap":
			return "suse"
		}
	}
	return ""
}

func distribuzione(a *Ambiente, p *Profilo) string {
	m, fonte := OsRelease(a)
	if m == nil {
		p.Sconosciuto("distro.id", "neither /etc/os-release nor /usr/lib/os-release")
		p.Con("RX-DISTRO-001", "")
		return ""
	}
	p.Rilevato("distro.id", m["ID"], fonte)
	p.Rilevato("distro.id_like", m["ID_LIKE"], fonte)
	p.Rilevato("distro.version", m["VERSION_ID"], fonte)
	p.Rilevato("distro.name", m["PRETTY_NAME"], fonte)
	p.Rilevato("distro.variant", m["VARIANT_ID"], fonte)
	fam := Famiglia(m["ID"], m["ID_LIKE"])
	p.Rilevato("distro.family", fam, "ID and ID_LIKE")
	// The immutable ones (§3, D9): read-only /usr, installation with a reboot.
	immutabile := false
	fonteImm := ""
	if _, err := os.Stat(a.P("/run/ostree-booted")); err == nil {
		immutabile, fonteImm = true, "/run/ostree-booted"
	}
	switch m["VARIANT_ID"] {
	case "silverblue", "kinoite", "sericea", "onyx", "cosmic-atomic":
		immutabile, fonteImm = true, "VARIANT_ID"
	}
	switch m["ID"] {
	case "ubuntu-core", "steamos", "aeon", "kalpa", "opensuse-microos":
		immutabile, fonteImm = true, "ID"
	}
	p.Rilevato("distro.immutable", siNo(immutabile), fonteImm)
	return fam
}

func sistema(a *Ambiente, p *Profilo) {
	arch := runtime.GOARCH
	switch arch {
	case "amd64":
		arch = "x86_64"
	case "arm64":
		arch = "aarch64"
	}
	p.Rilevato("system.arch", arch, "the engine itself")
	if k, ok := leggi(a, "/proc/sys/kernel/osrelease"); ok {
		p.Rilevato("system.kernel", strings.TrimSpace(k), "/proc/sys/kernel/osrelease")
	}
	// Booted with systemd: the folder systemd creates at boot (sd_booted()).
	if st, err := os.Stat(a.P("/run/systemd/system")); err == nil && st.IsDir() {
		p.Rilevato("system.systemd", "yes", "/run/systemd/system")
	} else {
		p.Rilevato("system.systemd", "no", "/run/systemd/system is missing")
		p.Con("RX-SYSTEMD-001", "")
	}
	if h, ok := leggi(a, "/proc/sys/kernel/hostname"); ok {
		p.Rilevato("system.name", strings.TrimSpace(h), "/proc/sys/kernel/hostname")
	}
}

// pacchettiFissi: those the PREFLIGHT always looks at, beyond the desktops and the catalogue.
var pacchettiFissi = []string{"labwc", "firewalld", "ufw", "nftables",
	"libssl3t64", "libssl3", "openssl-libs", "libopenssl3", "openssl",
	// the VA driver's family (§4.2, phase 18): full or reduced Intel, Mesa with or without codecs
	"intel-media-driver", "intel-media-driver-free", "libva-intel-media-driver", "intel-media-va-driver",
	"intel-media-va-driver-non-free", "mesa-va-drivers", "mesa-va-drivers-freeworld", "mesa-dri-drivers", "Mesa-dri"}

// famigliaDriver: from the installed package, whether the VA driver encodes H.264 (§4.2, phase 18). Fedora:
// libva-intel-media-driver (formerly intel-media-driver-free) and the official Mesa are built WITHOUT
// H.264 — `[M]` 30 Sep, from the binaries: 38 class names of AVC encoding against the 114 of the
// RPM Fusion driver; openSUSE: the official Intel driver is the full one (104-115, like RPM Fusion), the official
// Mesa is without h264/h265 («re-disable video codecs», Mesa-dri's changelog), Packman's
// (version «.pm.») with the codecs. Returns, for Intel and AMD, "with", "without" or "" (not recognised), and
// the description (f) for the fact h264.famiglia_driver. It writes nothing in the profile: the card
// verdict (strade.go) uses it too, inside Valuta.
func famigliaDriver(p *Profilo) (intel, amd string, f []string) {
	c := func(n string) bool { v := p.V("package." + n); return v != "" && v != "absent" }
	fam := p.V("distro.family")
	switch {
	case c("intel-media-driver") || c("intel-media-va-driver-non-free") || c("intel-media-va-driver"):
		intel = "with"
		f = append(f, "intel (iHD, with H.264)")
	case c("libva-intel-media-driver") || c("intel-media-driver-free"):
		intel = "without"
		f = append(f, "libva-intel-media-driver of Fedora/RHEL (no H.264 encoding)")
	}
	switch {
	case c("mesa-va-drivers-freeworld"):
		amd = "with"
		f = append(f, "mesa freeworld (radeonsi with H.264)")
	case fam == "fedora" && (c("mesa-va-drivers") || c("mesa-dri-drivers")):
		amd = "without"
		f = append(f, "Mesa of Fedora/RHEL (no H.264)")
	case fam == "suse" && c("Mesa-dri") && strings.Contains(p.V("package.Mesa-dri"), ".pm."):
		amd = "with"
		f = append(f, "Mesa from Packman (radeonsi with H.264)")
	case fam == "suse" && c("Mesa-dri"):
		amd = "without"
		f = append(f, "Mesa of openSUSE (no H.264)")
	case fam == "debian" && c("mesa-va-drivers"):
		amd = "with"
		f = append(f, "mesa-va-drivers (radeonsi with H.264)")
	}
	return
}

func nomiDesktop(fam string) []string {
	var r []string
	for _, d := range DESKTOP {
		r = append(r, PacchettoDesktop(fam, d))
	}
	return r
}

// Pacchetti: the package manager's database, read once. dpkg and pacman from their files
// (formats stable for decades); rpm with ONE call «rpm -q» for all the names (its database
// cannot be read without it).
type Pacchetti struct {
	fonte    string
	versioni map[string]string // name → version; absent = not installed
	letto    bool
}

// ArchivioPacchetti reads the family's database for the given names.
func ArchivioPacchetti(a *Ambiente, fam string, nomi []string) *Pacchetti {
	pk := &Pacchetti{versioni: map[string]string{}}
	switch fam {
	case "debian":
		pk.fonte = "/var/lib/dpkg/status"
		f, err := os.Open(a.P(pk.fonte))
		if err != nil {
			return pk
		}
		defer f.Close()
		sc := bufio.NewScanner(f)
		sc.Buffer(make([]byte, 1<<20), 1<<20)
		nome, stato, ver := "", "", ""
		chiudi := func() {
			if nome != "" && strings.HasSuffix(stato, " installed") {
				pk.versioni[nome] = ver
			}
			nome, stato, ver = "", "", ""
		}
		for sc.Scan() {
			r := sc.Text()
			switch {
			case r == "":
				chiudi()
			case strings.HasPrefix(r, "Package: "):
				nome = strings.TrimPrefix(r, "Package: ")
			case strings.HasPrefix(r, "Status: "):
				stato = strings.TrimPrefix(r, "Status: ")
			case strings.HasPrefix(r, "Version: "):
				ver = strings.TrimPrefix(r, "Version: ")
			}
		}
		chiudi()
		pk.letto = sc.Err() == nil
	case "arch":
		pk.fonte = "/var/lib/pacman/local"
		voci, err := filepath.Glob(a.P(pk.fonte) + "/*/desc")
		if err != nil || len(voci) == 0 {
			return pk
		}
		for _, v := range voci {
			b, err := os.ReadFile(v)
			if err != nil {
				continue
			}
			r := strings.Split(string(b), "\n")
			nome, ver := "", ""
			for i := 0; i+1 < len(r); i++ {
				switch r[i] {
				case "%NAME%":
					nome = r[i+1]
				case "%VERSION%":
					ver = r[i+1]
				}
			}
			if nome != "" {
				pk.versioni[nome] = ver
			}
		}
		pk.letto = true
	case "fedora", "suse":
		pk.fonte = "rpm -q"
		arg := append([]string{"-q", "--qf", "%{NAME} %{VERSION}\\n"}, nomi...)
		out, _, err := a.Esegui(60*time.Second, "rpm", arg...)
		if err != nil {
			return pk
		}
		for _, r := range strings.Split(out, "\n") {
			c := strings.Fields(r)
			if len(c) == 2 && !strings.HasPrefix(r, "package ") {
				pk.versioni[c[0]] = c[1]
			}
		}
		pk.letto = true
	}
	return pk
}

// Versione: the version, "absent", or SCONOSCIUTO if the database could not be read.
func (pk *Pacchetti) Versione(nome string) (string, StatoFatto, string) {
	if !pk.letto {
		return "", SCONOSCIUTO, pk.fonte
	}
	if v, ok := pk.versioni[nome]; ok {
		return v, RILEVATO, pk.fonte
	}
	return "absent", RILEVATO, pk.fonte
}

// PacchettoDesktop: the package that says whether a desktop is there, and with what version.
func PacchettoDesktop(fam, d string) string {
	switch d {
	case "gnome":
		return "gnome-shell"
	case "kde":
		if fam == "suse" {
			return "plasma6-workspace"
		}
		return "plasma-workspace"
	case "xfce":
		return "xfce4-session"
	case "lxqt":
		return "lxqt-session"
	}
	return ""
}

// fallback binaries to know whether a desktop is there when the package manager does not answer.
var binarioDesktop = map[string]string{"gnome": "/usr/bin/gnome-shell", "kde": "/usr/bin/plasmashell", "xfce": "/usr/bin/xfce4-session", "lxqt": "/usr/bin/lxqt-session"}

func desktop(a *Ambiente, p *Profilo, fam string, pk *Pacchetti, extra []string) {
	for _, d := range DESKTOP {
		nome := PacchettoDesktop(fam, d)
		v, st, fonte := pk.Versione(nome)
		if st == SCONOSCIUTO {
			if _, err := os.Stat(a.P(binarioDesktop[d])); err == nil {
				p.Metti(Fatto{Chiave: "desktop." + d, Valore: "present", Stato: RILEVATO, Fonte: binarioDesktop[d], Nota: "unknown version: the package database could not be read"})
			} else {
				p.Sconosciuto("desktop."+d, "the package database could not be read ("+fonte+")")
			}
			continue
		}
		p.Metti(Fatto{Chiave: "desktop." + d, Valore: v, Stato: st, Fonte: fonte + " " + nome})
	}
	visti := map[string]bool{}
	for _, nome := range append(append([]string{}, pacchettiFissi...), extra...) {
		if visti[nome] {
			continue
		}
		visti[nome] = true
		v, st, fonte := pk.Versione(nome)
		if st == SCONOSCIUTO {
			p.Sconosciuto("package."+nome, "the package database could not be read ("+fonte+")")
			continue
		}
		p.Metti(Fatto{Chiave: "package." + nome, Valore: v, Stato: st, Fonte: fonte})
	}
}

// third-party repositories that matter for H.264 and for KDE on Alma (§4.2, §11.1).
//
// A repository is there if a SECTION of a .repo with its name is ENABLED (missing «enabled» = enabled,
// as for dnf and zypper). `[M]` 30 Sep, fedora44-gnome: before, the word in any file was enough,
// and fedora-workstation-repositories brings rpmfusion-nonfree-steam DISABLED ⇒ RPM Fusion «present»,
// no condition C-DEPOSITO, no consent asked, and REMOTIX without encoding (T9, R22).
var (
	intestazioneRepo = regexp.MustCompile(`(?m)^\[([^\]]+)\]\s*$`)
	repoSpento       = regexp.MustCompile(`(?mi)^enabled\s*=\s*(0|false|no)\s*$`)
)

func depositi(a *Ambiente, p *Profilo) {
	cerca := func(chiave string, cartelle []string, vale func(id string) bool) {
		acceso, spenti := "", ""
		for _, c := range cartelle {
			voci, _ := filepath.Glob(a.P(c) + "/*.repo")
			for _, v := range voci {
				b, err := os.ReadFile(v)
				if err != nil {
					continue
				}
				t := string(b)
				rel := strings.TrimPrefix(v, strings.TrimSuffix(a.P("/"), "/"))
				idx := intestazioneRepo.FindAllStringSubmatchIndex(t, -1)
				for i, m := range idx {
					id := strings.ToLower(t[m[2]:m[3]])
					if !vale(id) {
						continue
					}
					fine := len(t)
					if i+1 < len(idx) {
						fine = idx[i+1][0]
					}
					if repoSpento.MatchString(t[m[1]:fine]) {
						spenti = rel + " [" + id + "] disabled"
					} else {
						acceso = rel + " [" + id + "]"
					}
				}
			}
		}
		switch {
		case acceso != "":
			p.Rilevato(chiave, "present", acceso)
		case spenti != "":
			p.Rilevato(chiave, "absent", spenti)
		default:
			p.Rilevato(chiave, "absent", strings.Join(cartelle, " "))
		}
	}
	parola := func(x string) func(string) bool {
		return func(id string) bool { return strings.Contains(id, x) }
	}
	// RPM Fusion: «free» (mesa-va-drivers-freeworld, AMD) and, separately, the real «nonfree» branch
	// (intel-media-driver, Intel: phase 18); the «nonfree» ones Fedora Workstation brings disabled (steam,
	// nvidia-driver) do not matter
	cerca("repo.rpmfusion", []string{"/etc/yum.repos.d"}, parola("rpmfusion-free"))
	cerca("repo.rpmfusion-nonfree", []string{"/etc/yum.repos.d"}, func(id string) bool {
		return id == "rpmfusion-nonfree" || id == "rpmfusion-nonfree-updates"
	})
	// EPEL: not Cisco's OpenH264 repository for EPEL, which a machine may still have (phase 18)
	cerca("repo.epel", []string{"/etc/yum.repos.d"}, func(id string) bool {
		return strings.Contains(id, "epel") && !strings.Contains(id, "openh264")
	})
	cerca("repo.packman", []string{"/etc/zypp/repos.d"}, parola("packman"))
}

// Scheda is a rendering node with its driver.
type Scheda struct {
	Nodo, Driver, Fornitore, Gruppo, Modo string
}

var fornitori = map[string]string{"0x8086": "Intel", "0x1002": "AMD", "0x10de": "NVIDIA", "0x1af4": "virtio", "0x1234": "QEMU", "0x15ad": "VMware"}

func schede(a *Ambiente, p *Profilo) []Scheda {
	gr, _ := LeggiGruppi(a.P("/etc/group"))
	gruppoDi := func(gid uint32) string {
		for n, v := range gr {
			if v[0] == strconv.Itoa(int(gid)) {
				return n
			}
		}
		return strconv.Itoa(int(gid))
	}
	voci, _ := filepath.Glob(a.P("/sys/class/drm/renderD*"))
	sort.Strings(voci)
	var r []Scheda
	for _, v := range voci {
		s := Scheda{Nodo: "/dev/dri/" + filepath.Base(v)}
		if l, err := os.Readlink(filepath.Join(v, "device", "driver")); err == nil {
			s.Driver = filepath.Base(l)
		}
		if f, err := os.ReadFile(filepath.Join(v, "device", "vendor")); err == nil {
			id := strings.TrimSpace(string(f))
			s.Fornitore = fornitori[id]
			if s.Fornitore == "" {
				s.Fornitore = id
			}
		}
		if st, err := os.Stat(a.P(s.Nodo)); err == nil {
			if sys, ok := st.Sys().(*syscall.Stat_t); ok {
				s.Gruppo = gruppoDi(sys.Gid)
			}
			s.Modo = fmt.Sprintf("%04o", st.Mode().Perm())
		}
		r = append(r, s)
		k := "gpu." + filepath.Base(v)
		p.Rilevato(k+".driver", s.Driver, "/sys/class/drm")
		p.Rilevato(k+".vendor", s.Fornitore, "/sys/class/drm")
		p.Rilevato(k+".group", s.Gruppo, s.Nodo)
		p.Rilevato(k+".mode", s.Modo, s.Nodo)
	}
	var nomi []string
	for _, s := range r {
		nomi = append(nomi, filepath.Base(s.Nodo))
	}
	// without nodes the refusal is given by the card verdict (strade.go, RX-GPU-003)
	if len(nomi) == 0 {
		p.Rilevato("gpu.nodes", "none", "/sys/class/drm")
	} else {
		p.Rilevato("gpu.nodes", strings.Join(nomi, ","), "/sys/class/drm")
	}
	// NVIDIA with the proprietary driver: the module «nvidia» or its file in /proc (§4.2).
	nv := false
	fonte := ""
	if _, err := os.Stat(a.P("/proc/driver/nvidia/version")); err == nil {
		nv, fonte = true, "/proc/driver/nvidia/version"
	}
	if _, err := os.Stat(a.P("/sys/module/nvidia")); err == nil {
		nv, fonte = true, "/sys/module/nvidia"
	}
	for _, s := range r {
		if s.Driver == "nvidia" {
			nv, fonte = true, "driver of "+s.Nodo
		}
	}
	p.Rilevato("gpu.nvidia_proprietary", siNo(nv), fonte)
	if nv {
		p.Con("RX-GPU-002", "")
	}
	return r
}

// h264: «H.264 really available» is VERIFICATO only if a frame was really
// encoded (§6.5 point 1, §6.6.7): the real test is done in 7a with REMOTIX's binary. Here we read
// what can be read without launching anything. ⭐ Phase 18 (without ffmpeg): the card encodes with
// libva and the distribution's VA driver — we look at the drivers (the dri folders, also
// RPM Fusion's dri-nonfree and dri-freeworld) and their family (famigliaDriver). Phase 19: it is the
// Rileva of the «vaapi» route (strade.go), and there is no fallback to look at any more. The card stays
// SCONOSCIUTA except in the certain cases: no driver, or only drivers built without H.264.
func h264(a *Ambiente, p *Profilo, fam string) {
	var driver []string
	visti := map[string]bool{}
	for _, g := range []string{"/usr/lib/*/dri/*_drv_video.so", "/usr/lib64/dri/*_drv_video.so", "/usr/lib/dri/*_drv_video.so",
		"/usr/lib64/dri-nonfree/*_drv_video.so", "/usr/lib64/dri-freeworld/*_drv_video.so"} {
		v, _ := filepath.Glob(a.P(g))
		for _, x := range v {
			n := strings.TrimSuffix(filepath.Base(x), "_drv_video.so")
			if !visti[n] {
				visti[n] = true
				driver = append(driver, n)
			}
		}
	}
	sort.Strings(driver)
	if len(driver) > 0 {
		p.Rilevato("h264.driver_va", strings.Join(driver, ","), "dri folders")
	} else {
		p.Rilevato("h264.driver_va", "none", "dri folders")
	}
	intel, amd, fd := famigliaDriver(p)
	if len(fd) == 0 {
		p.Sconosciuto("h264.driver_family", "no known VA driver package")
	} else {
		p.Rilevato("h264.driver_family", strings.Join(fd, "; "), "installed packages")
	}
	nota7a := "the test with a frame is done in 7a, with the REMOTIX binary"
	forn, noti := fornitoriScheda(p)
	// the certain case: every Intel/AMD card of the machine has only a driver without H.264
	senza := (forn["Intel"] || forn["AMD"]) && (!forn["Intel"] || intel == "without") && (!forn["AMD"] || amd == "without")
	// the driver codes (where to get it) only if there is a card of the route: without Intel or AMD
	// the reason is another one, and the verdict says it (RX-GPU-*)
	conScheda := !noti || forn["Intel"] || forn["AMD"]
	switch {
	case len(driver) == 0:
		p.Metti(Fatto{Chiave: "h264.gpu", Valore: "no", Stato: RILEVATO, Fonte: "dri folders", Nota: "no VA-API driver"})
		if conScheda {
			p.Con(codiceH264(fam), "no VA-API driver")
		}
	case senza:
		p.Metti(Fatto{Chiave: "h264.gpu", Valore: "no", Stato: RILEVATO, Fonte: "installed packages", Nota: "VA driver without H.264: " + p.V("h264.driver_family")})
		p.Con(codiceH264(fam), "VA driver without H.264")
	default:
		p.Sconosciuto("h264.gpu", "driver "+strings.Join(driver, ",")+": "+nota7a)
		if conScheda {
			p.Con("RX-H264-001", "") // its text already says it: the detail would repeat it
		}
	}
}

func codiceH264(fam string) string {
	switch fam {
	case "fedora":
		return "RX-H264-003"
	case "suse":
		return "RX-H264-004"
	}
	return "RX-H264-002"
}

func sicurezza(a *Ambiente, p *Profilo) {
	if t, ok := leggi(a, "/sys/fs/selinux/enforce"); ok {
		v := "permissive"
		if strings.TrimSpace(t) == "1" {
			v = "enforcing"
			p.Con("RX-SELINUX-001", "")
		}
		p.Rilevato("selinux", v, "/sys/fs/selinux/enforce")
	} else {
		p.Rilevato("selinux", "absent", "/sys/fs/selinux")
	}
	if t, ok := leggi(a, "/sys/module/apparmor/parameters/enabled"); ok && strings.TrimSpace(t) == "Y" {
		p.Rilevato("apparmor", "enabled", "/sys/module/apparmor/parameters/enabled")
	} else {
		p.Rilevato("apparmor", "absent", "/sys/module/apparmor/parameters/enabled")
	}
}

// portaInAscolto reads /proc/net: is someone already listening on the port?
func portaInAscolto(a *Ambiente, porta int, proto string) (bool, bool) {
	esa := fmt.Sprintf(":%04X", porta)
	letto := false
	for _, f := range []string{"/proc/net/" + proto, "/proc/net/" + proto + "6"} {
		t, ok := leggi(a, f)
		if !ok {
			continue
		}
		letto = true
		for _, r := range strings.Split(t, "\n")[1:] {
			c := strings.Fields(r)
			if len(c) < 4 || !strings.HasSuffix(c[1], esa) {
				continue
			}
			if proto == "udp" || c[3] == "0A" { // 0A = LISTEN
				return true, true
			}
		}
	}
	return false, letto
}

func firewall(a *Ambiente, p *Profilo, porta int) {
	ps := strconv.Itoa(porta)
	for _, proto := range []string{"tcp", "udp"} {
		occ, letto := portaInAscolto(a, porta, proto)
		k := "port." + ps + "." + proto + "_free"
		if !letto {
			p.Sconosciuto(k, "/proc/net not readable")
			continue
		}
		p.Rilevato(k, siNo(!occ), "/proc/net/"+proto)
		if occ {
			p.Con("RX-FW-003", ps+"/"+proto)
		}
	}
	p.Metti(Fatto{Chiave: "port." + ps + ".reachable", Stato: SCONOSCIUTO, Nota: "another machine is needed to find out"})
	p.Con("RX-FW-005", "")

	// firewalld, over the bus
	fw := &firewalldDBus{a.Bus}
	if fw.Acceso() {
		p.Rilevato("firewall.type", "firewalld", "D-Bus "+fwNome)
		zona, err := fw.ZonaPredefinita()
		if err != nil {
			p.Sconosciuto("firewall.zone", err.Error())
			p.Con("RX-FW-002", err.Error())
			return
		}
		p.Rilevato("firewall.zone", zona, "D-Bus getDefaultZone")
		porte, _ := fw.PorteVive(zona)
		for _, proto := range []string{"tcp", "udp"} {
			k := "firewall.port_" + ps + "_" + proto
			ha, err := fw.HaPorta(zona, ps+"/"+proto, false)
			if err != nil {
				p.Sconosciuto(k, err.Error())
				p.Con("RX-FW-002", err.Error())
				continue
			}
			if !ha && portaInIntervalli(porte, porta, proto) {
				ha = true
			}
			v := "closed"
			if ha {
				v = "open"
			} else {
				p.Con("RX-FW-001", "firewalld, zone "+zona+", "+ps+"/"+proto)
			}
			p.Rilevato(k, v, "D-Bus queryPort and getPorts, zone "+zona)
		}
		return
	}
	// ufw: enabled in its file; the rules in its files (readable by root)
	if t, ok := leggi(a, "/etc/ufw/ufw.conf"); ok && strings.Contains(t, "ENABLED=yes") {
		p.Rilevato("firewall.type", "ufw", "/etc/ufw/ufw.conf")
		regole, ok4 := leggi(a, "/etc/ufw/user.rules")
		regole6, _ := leggi(a, "/etc/ufw/user6.rules")
		for _, proto := range []string{"tcp", "udp"} {
			k := "firewall.port_" + ps + "_" + proto
			if !ok4 {
				p.Sconosciuto(k, "/etc/ufw/user.rules not readable (root needed)")
				continue
			}
			if ufwApre(regole+regole6, ps, proto) {
				p.Rilevato(k, "open", "/etc/ufw/user.rules")
			} else {
				p.Rilevato(k, "closed", "/etc/ufw/user.rules")
				p.Con("RX-FW-001", "ufw, "+ps+"/"+proto)
			}
		}
		if !ok4 {
			p.Con("RX-FW-002", "ufw")
		}
		return
	}
	if s, err := a.Bus.StatoAttivo("nftables.service"); err == nil && s == "active" {
		p.Rilevato("firewall.type", "nftables", "D-Bus systemd: nftables.service active")
		for _, proto := range []string{"tcp", "udp"} {
			p.Sconosciuto("firewall.port_"+ps+"_"+proto, "nftables rules are not evaluated yet")
		}
		p.Con("RX-FW-002", "nftables")
		return
	} else if err != nil {
		p.Sconosciuto("firewall.type", "neither firewalld on the bus nor ufw running; systemd does not answer on the bus: "+err.Error())
		p.Con("RX-FW-002", "D-Bus: "+err.Error())
		return
	}
	p.Rilevato("firewall.type", "none", "neither firewalld nor ufw nor nftables running")
}

// ufwApre: an ACCEPT rule for the port in ufw's files («### tuple ### allow tcp 7447 …» and the
// lines -A ufw-user-input … --dport 7447 -j ACCEPT; without a protocol it holds for both).
func ufwApre(regole, ps, proto string) bool {
	for _, r := range strings.Split(regole, "\n") {
		if !strings.Contains(r, "--dport "+ps+" ") || !strings.Contains(r, "-j ACCEPT") {
			continue
		}
		if strings.Contains(r, "-p "+proto+" ") || !strings.Contains(r, "-p ") {
			return true
		}
	}
	return false
}

// portaInIntervalli: Fedora Workstation opens 1025-65535 with a range (§11.1), and queryPort does not
// see it. porte: the [port, protocol] pairs of getPorts.
func portaInIntervalli(porte [][]string, porta int, proto string) bool {
	for _, v := range porte {
		if len(v) != 2 || v[1] != proto {
			continue
		}
		da, a, isInt := strings.Cut(v[0], "-")
		x, e1 := strconv.Atoi(da)
		if e1 != nil {
			continue
		}
		y := x
		if isInt {
			if y2, e2 := strconv.Atoi(a); e2 == nil {
				y = y2
			}
		}
		if porta >= x && porta <= y {
			return true
		}
	}
	return false
}

// PamBase: the files of the family's stack that REMOTIX's file relies on (§4.3).
func PamBase(fam string) []string {
	switch fam {
	case "debian":
		return []string{"common-auth", "common-account", "common-session", "common-password"}
	case "fedora":
		return []string{"password-auth", "postlogin", "system-auth"}
	case "suse":
		return []string{"common-auth", "common-account", "common-session", "common-password", "postlogin-auth", "postlogin-session"}
	case "arch":
		return []string{"system-remote-login", "system-auth"}
	}
	return nil
}

func trovaPam(a *Ambiente, nome string) string {
	for _, c := range []string{"/etc/pam.d/", "/usr/lib/pam.d/", "/usr/etc/pam.d/"} {
		if _, err := os.Stat(a.P(c + nome)); err == nil {
			return c + nome
		}
	}
	return ""
}

func pam(a *Ambiente, p *Profilo, fam string) {
	base := PamBase(fam)
	if base == nil {
		p.Sconosciuto("pam.base", "unknown family")
		return
	}
	var trovati, mancanti []string
	faillock := false
	for _, n := range base {
		f := trovaPam(a, n)
		if f == "" {
			mancanti = append(mancanti, n)
			continue
		}
		trovati = append(trovati, f)
		if t, ok := leggi(a, f); ok {
			for _, r := range strings.Split(t, "\n") {
				r = strings.TrimSpace(r)
				if !strings.HasPrefix(r, "#") && strings.Contains(r, "pam_faillock") {
					faillock = true
				}
			}
		}
	}
	p.Rilevato("pam.base", strings.Join(trovati, " "), "family "+fam)
	if len(mancanti) > 0 {
		p.Rilevato("pam.base_missing", strings.Join(mancanti, " "), "family "+fam)
		p.Con("RX-PAM-001", strings.Join(mancanti, " "))
	}
	p.Rilevato("pam.faillock", siNo(faillock), strings.Join(trovati, " "))
	if faillock {
		p.Con("RX-PAM-002", "")
	}
	if f := trovaPam(a, "remotix"); f != "" {
		p.Rilevato("pam.remotix", f, f)
		p.Con("RX-PAM-003", f)
	} else {
		p.Rilevato("pam.remotix", "absent", "/etc/pam.d, /usr/lib/pam.d")
	}
	modulo := ""
	for _, g := range []string{"/usr/lib/security", "/usr/lib64/security", "/lib/security", "/lib64/security", "/usr/lib/*/security", "/lib/*/security"} {
		v, _ := filepath.Glob(a.P(g) + "/pam_systemd.so")
		if len(v) > 0 {
			modulo = strings.TrimPrefix(v[0], strings.TrimSuffix(a.P("/"), "/"))
			break
		}
	}
	if modulo != "" {
		p.Rilevato("pam.pam_systemd", modulo, modulo)
	} else {
		p.Rilevato("pam.pam_systemd", "absent", "PAM module directories")
		p.Con("RX-PAM-004", "")
	}
}

func openssl(a *Ambiente, p *Profilo, fam string, pk *Pacchetti) {
	v, fonte := "", ""
	for _, nome := range []string{"libssl3t64", "libssl3", "openssl-libs", "libopenssl3", "openssl"} {
		if pv, st, f := pk.Versione(nome); st == RILEVATO && pv != "absent" {
			v, fonte = pv, f+" "+nome
			break
		}
	}
	if v == "" { // from the library itself: the string «OpenSSL 3.x.y»
		for _, g := range []string{"/usr/lib/*/libssl.so.3", "/usr/lib64/libssl.so.3", "/usr/lib/libssl.so.3"} {
			l, _ := filepath.Glob(a.P(g))
			for _, x := range l {
				if b, err := os.ReadFile(x); err == nil {
					if i := bytes.Index(b, []byte("OpenSSL 3.")); i >= 0 {
						c := strings.Fields(string(b[i : i+24]))
						if len(c) >= 2 {
							v, fonte = c[1], x
						}
					}
				}
			}
		}
	}
	if v == "" {
		p.Sconosciuto("openssl.version", "neither the package nor the library")
		p.Con("RX-OPENSSL-002", "")
		return
	}
	p.Rilevato("openssl.version", v, fonte)
	if ConfrontaVersioni(v, "3.5.0") < 0 {
		p.Con("RX-OPENSSL-001", v)
	}
}

// logind: KillUserProcesses (§5.2). The live value is asked of logind (VERIFICATO); if it does not
// answer, the configuration files are read in systemd's order (RILEVATO); if none
// sets it, the build default holds, which cannot be seen from here (SCONOSCIUTO).
func logind(a *Ambiente, p *Profilo) {
	if x, err := a.Bus.Proprieta("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.KillUserProcesses"); err == nil {
		if b, ok := x.(bool); ok {
			v := map[bool]string{true: "yes", false: "no"}[b]
			p.Verificato("logind.kill_user_processes", v, "logind, D-Bus")
			if v == "yes" {
				p.Con("RX-LOGIND-001", "")
			}
			return
		}
	}
	valore, fonte := "", ""
	leggiConf := func(f string) {
		t, ok := leggi(a, f)
		if !ok {
			return
		}
		for _, r := range strings.Split(t, "\n") {
			r = strings.TrimSpace(r)
			if k, v, ok := strings.Cut(r, "="); ok && strings.TrimSpace(k) == "KillUserProcesses" {
				valore, fonte = strings.ToLower(strings.TrimSpace(v)), f
			}
		}
	}
	leggiConf("/usr/lib/systemd/logind.conf")
	leggiConf("/etc/systemd/logind.conf")
	// the drop-ins: by name, and for equal names /etc wins over /run over /usr/local/lib over /usr/lib
	scelti := map[string]string{}
	for _, c := range []string{"/usr/lib/systemd/logind.conf.d", "/usr/local/lib/systemd/logind.conf.d", "/run/systemd/logind.conf.d", "/etc/systemd/logind.conf.d"} {
		v, _ := filepath.Glob(a.P(c) + "/*.conf")
		for _, f := range v {
			scelti[filepath.Base(f)] = c + "/" + filepath.Base(f)
		}
	}
	var nomi []string
	for n := range scelti {
		nomi = append(nomi, n)
	}
	sort.Strings(nomi)
	for _, n := range nomi {
		leggiConf(scelti[n])
	}
	if valore == "" {
		p.Sconosciuto("logind.kill_user_processes", "no file sets it and logind did not answer: the build default applies")
		p.Con("RX-LOGIND-002", "")
		return
	}
	if valore == "true" || valore == "1" {
		valore = "yes"
	}
	p.Rilevato("logind.kill_user_processes", valore, fonte)
	if valore == "yes" {
		p.Con("RX-LOGIND-001", fonte)
	}
}

func gruppi(a *Ambiente, p *Profilo) {
	t, err := LeggiGruppi(a.P("/etc/group"))
	if err != nil {
		p.Sconosciuto("group.video", err.Error())
		p.Sconosciuto("group.render", err.Error())
		return
	}
	for _, g := range []string{"video", "render"} {
		v, ok := t[g]
		if !ok {
			p.Rilevato("group."+g, "absent", "/etc/group")
			if g == "render" {
				p.Con("RX-GRUPPI-001", "")
			}
			continue
		}
		p.Rilevato("group."+g, "gid="+v[0]+" members="+strings.Join(DividiMembri(v[1]), ","), "/etc/group")
	}
}

// fonts: labwc dies without a scalable font (labwc #2525, §11.1). fc-list is not
// launched (closed list): the vector font files in the system folders are counted.
func caratteri(a *Ambiente, p *Profilo) {
	n := 0
	for _, c := range []string{"/usr/share/fonts", "/usr/local/share/fonts"} {
		filepath.WalkDir(a.P(c), func(_ string, d os.DirEntry, err error) error {
			if err == nil && !d.IsDir() {
				switch strings.ToLower(filepath.Ext(d.Name())) {
				case ".ttf", ".otf", ".ttc", ".otc", ".pfb", ".pfa":
					n++
				}
			}
			return nil
		})
	}
	p.Metti(Fatto{Chiave: "fonts.scalable", Valore: strconv.Itoa(n), Stato: RILEVATO, Fonte: "/usr/share/fonts", Nota: "ttf/otf/ttc/pfb files counted, not asked to fontconfig"})
}
