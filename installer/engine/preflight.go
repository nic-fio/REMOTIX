package engine

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
// (DECISIONI §10.14: closed list, environment.go), recorded in the profile. Test R1 checks it
// with the fingerprints of /etc before and after, in one container per family (tests/r1-containers.sh).

// PreflightOptions: the port to look at and the extra packages the catalogue wants to know about.
type PreflightOptions struct {
	Porta     int
	Pacchetti []string // components (labwc, gnome-session, the fonts…) requested by the catalogue
}

// Preflight builds the machine's profile.
func Preflight(a *Environment, o PreflightOptions) *ProfileV {
	if o.Porta == 0 {
		o.Porta = 7447
	}
	p := NewProfile(o.Porta)
	before := a.Annotate
	a.Annotate = func(r string) {
		p.Commands = append(p.Commands, r)
		if before != nil {
			before(r)
		}
	}
	defer func() { a.Annotate = before }()
	fam := distrib(a, p)
	system_wide(a, p)
	pk := PackageArchive(a, fam, append(append(desktopNames(fam), pinnedPackages...), o.Pacchetti...))
	desktop(a, p, fam, pk, o.Pacchetti)
	repositories(a, p)
	cards(a, p)
	encode(a, p, fam)
	security(a, p)
	firewall(a, p, o.Porta)
	pam(a, p, fam)
	openssl(a, p, fam, pk)
	logind(a, p)
	groups(a, p)
	characters(a, p)
	p.Sort()
	return p
}

// load a file of the machine; "" if it is not there.
func load(a *Environment, fpath string) (string, bool) {
	b, err := os.ReadFile(a.P(fpath))
	if err != nil {
		return "", false
	}
	return string(b), true
}

// OsRelease reads /etc/os-release (or /usr/lib/os-release).
func OsRelease(a *Environment) (map[string]string, string) {
	for _, f := range []string{"/etc/os-release", "/usr/lib/os-release"} {
		if t, ok := load(a, f); ok {
			m := map[string]string{}
			for _, line := range strings.Split(t, "\n") {
				k, v, ok := strings.Cut(strings.TrimSpace(line), "=")
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
	all_items := append([]string{id}, strings.Fields(idLike)...)
	for _, x := range all_items {
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

func distrib(a *Environment, p *ProfileV) string {
	m, source := OsRelease(a)
	if m == nil {
		p.Unknown("distro.id", "neither /etc/os-release nor /usr/lib/os-release")
		p.Con("RX-DISTRO-001", "")
		return ""
	}
	p.Detected("distro.id", m["ID"], source)
	p.Detected("distro.id_like", m["ID_LIKE"], source)
	p.Detected("distro.version", m["VERSION_ID"], source)
	p.Detected("distro.name", m["PRETTY_NAME"], source)
	p.Detected("distro.variant", m["VARIANT_ID"], source)
	fam := Famiglia(m["ID"], m["ID_LIKE"])
	p.Detected("distro.family", fam, "ID and ID_LIKE")
	// The immutable ones (§3, D9): read-only /usr, installation with a reboot.
	immutable := false
	imageSource := ""
	if _, err := os.Stat(a.P("/run/ostree-booted")); err == nil {
		immutable, imageSource = true, "/run/ostree-booted"
	}
	switch m["VARIANT_ID"] {
	case "silverblue", "kinoite", "sericea", "onyx", "cosmic-atomic":
		immutable, imageSource = true, "VARIANT_ID"
	}
	switch m["ID"] {
	case "ubuntu-core", "steamos", "aeon", "kalpa", "opensuse-microos":
		immutable, imageSource = true, "ID"
	}
	p.Detected("distro.immutable", siNo(immutable), imageSource)
	return fam
}

func system_wide(a *Environment, p *ProfileV) {
	arch := runtime.GOARCH
	switch arch {
	case "amd64":
		arch = "x86_64"
	case "arm64":
		arch = "aarch64"
	}
	p.Detected("system.arch", arch, "the engine itself")
	if k, ok := load(a, "/proc/sys/kernel/osrelease"); ok {
		p.Detected("system.kernel", strings.TrimSpace(k), "/proc/sys/kernel/osrelease")
	}
	// Booted with systemd: the folder systemd creates at boot (sd_booted()).
	if st, err := os.Stat(a.P("/run/systemd/system")); err == nil && st.IsDir() {
		p.Detected("system.systemd", "yes", "/run/systemd/system")
	} else {
		p.Detected("system.systemd", "no", "/run/systemd/system is missing")
		p.Con("RX-SYSTEMD-001", "")
	}
	if h, ok := load(a, "/proc/sys/kernel/hostname"); ok {
		p.Detected("system.name", strings.TrimSpace(h), "/proc/sys/kernel/hostname")
	}
}

// pinnedPackages: those the PREFLIGHT always looks at, beyond the desktops and the catalogue.
var pinnedPackages = []string{"labwc", "firewalld", "ufw", "nftables",
	"libssl3t64", "libssl3", "openssl-libs", "libopenssl3", "openssl",
	// the VA driver's family (§4.2, phase 18): full or reduced Intel, Mesa with or without codecs
	"intel-media-driver", "intel-media-driver-free", "libva-intel-media-driver", "intel-media-va-driver",
	"intel-media-va-driver-non-free", "mesa-va-drivers", "mesa-va-drivers-freeworld", "mesa-dri-drivers", "Mesa-dri"}

// driverFamily: from the installed package, whether the VA driver encodes H.264 (§4.2, phase 18). Fedora:
// libva-intel-media-driver (formerly intel-media-driver-free) and the official Mesa are built WITHOUT
// H.264 — `[M]` 30 Sep, from the binaries: 38 class names of AVC encoding against the 114 of the
// RPM Fusion driver; openSUSE: the official Intel driver is the full one (104-115, like RPM Fusion), the official
// Mesa is without h264/h265 («re-disable video codecs», Mesa-dri's changelog), Packman's
// (version «.pm.») with the codecs. Returns, for Intel and AMD, "with", "without" or "" (not recognised), and
// the description (f) for the fact h264.famiglia_driver. It writes nothing in the profile: the card
// verdict (encoding_routes.go) uses it too, inside Evaluate.
func driverFamily(p *ProfileV) (intel, amd string, f []string) {
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

func desktopNames(fam string) []string {
	var r []string
	for _, d := range DESKTOP {
		r = append(r, DesktopPackage(fam, d))
	}
	return r
}

// Pacchetti: the package manager's database, read once. dpkg and pacman from their files
// (formats stable for decades); rpm with ONE call «rpm -q» for all the names (its database
// cannot be read without it).
type Pacchetti struct {
	source   string
	versions map[string]string // name → version; absent = not installed
	read     bool
}

// PackageArchive reads the family's database for the given names.
func PackageArchive(a *Environment, fam string, names []string) *Pacchetti {
	pk := &Pacchetti{versions: map[string]string{}}
	switch fam {
	case "debian":
		pk.source = "/var/lib/dpkg/status"
		f, err := os.Open(a.P(pk.source))
		if err != nil {
			return pk
		}
		defer f.Close()
		sc := bufio.NewScanner(f)
		sc.Buffer(make([]byte, 1<<20), 1<<20)
		name, state, ver := "", "", ""
		flush := func() {
			if name != "" && strings.HasSuffix(state, " installed") {
				pk.versions[name] = ver
			}
			name, state, ver = "", "", ""
		}
		for sc.Scan() {
			r := sc.Text()
			switch {
			case r == "":
				flush()
			case strings.HasPrefix(r, "Package: "):
				name = strings.TrimPrefix(r, "Package: ")
			case strings.HasPrefix(r, "Status: "):
				state = strings.TrimPrefix(r, "Status: ")
			case strings.HasPrefix(r, "Version: "):
				ver = strings.TrimPrefix(r, "Version: ")
			}
		}
		flush()
		pk.read = sc.Err() == nil
	case "arch":
		pk.source = "/var/lib/pacman/local"
		entries, err := filepath.Glob(a.P(pk.source) + "/*/desc")
		if err != nil || len(entries) == 0 {
			return pk
		}
		for _, v := range entries {
			b, err := os.ReadFile(v)
			if err != nil {
				continue
			}
			r := strings.Split(string(b), "\n")
			name, ver := "", ""
			for i := 0; i+1 < len(r); i++ {
				switch r[i] {
				case "%NAME%":
					name = r[i+1]
				case "%VERSION%":
					ver = r[i+1]
				}
			}
			if name != "" {
				pk.versions[name] = ver
			}
		}
		pk.read = true
	case "fedora", "suse":
		pk.source = "rpm -q"
		arg := append([]string{"-q", "--qf", "%{NAME} %{VERSION}\\n"}, names...)
		out, _, err := a.Run(60*time.Second, "rpm", arg...)
		if err != nil {
			return pk
		}
		for _, r := range strings.Split(out, "\n") {
			c := strings.Fields(r)
			if len(c) == 2 && !strings.HasPrefix(r, "package ") {
				pk.versions[c[0]] = c[1]
			}
		}
		pk.read = true
	}
	return pk
}

// Versione: the version, "absent", or UNKNOWN if the database could not be read.
func (pk *Pacchetti) Ver(name string) (string, StateDone, string) {
	if !pk.read {
		return "", UNKNOWN, pk.source
	}
	if v, ok := pk.versions[name]; ok {
		return v, DETECTED, pk.source
	}
	return "absent", DETECTED, pk.source
}

// DesktopPackage: the package that says whether a desktop is there, and with what version.
func DesktopPackage(fam, d string) string {
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
var binaryDesktop = map[string]string{"gnome": "/usr/bin/gnome-shell", "kde": "/usr/bin/plasmashell", "xfce": "/usr/bin/xfce4-session", "lxqt": "/usr/bin/lxqt-session"}

func desktop(a *Environment, p *ProfileV, fam string, pk *Pacchetti, extra []string) {
	for _, d := range DESKTOP {
		name := DesktopPackage(fam, d)
		v, st, source := pk.Ver(name)
		if st == UNKNOWN {
			if _, err := os.Stat(a.P(binaryDesktop[d])); err == nil {
				p.Place(Fatto{KeyId: "desktop." + d, Val: "present", State: DETECTED, Source: binaryDesktop[d], Nota: "unknown version: the package database could not be read"})
			} else {
				p.Unknown("desktop."+d, "the package database could not be read ("+source+")")
			}
			continue
		}
		p.Place(Fatto{KeyId: "desktop." + d, Val: v, State: st, Source: source + " " + name})
	}
	seen_items := map[string]bool{}
	for _, name := range append(append([]string{}, pinnedPackages...), extra...) {
		if seen_items[name] {
			continue
		}
		seen_items[name] = true
		v, st, source := pk.Ver(name)
		if st == UNKNOWN {
			p.Unknown("package."+name, "the package database could not be read ("+source+")")
			continue
		}
		p.Place(Fatto{KeyId: "package." + name, Val: v, State: st, Source: source})
	}
}

// third-party repositories that matter for H.264 and for KDE on Alma (§4.2, §11.1).
//
// A repository is there if a SECTION of a .repo with its name is ENABLED (missing «enabled» = enabled,
// as for dnf and zypper). `[M]` 30 Sep, fedora44-gnome: before, the word in any file was enough,
// and fedora-workstation-repositories brings rpmfusion-nonfree-steam DISABLED ⇒ RPM Fusion «present»,
// no condition C-DEPOSITO, no consent asked, and REMOTIX without encoding (T9, R22).
var (
	repoHeader = regexp.MustCompile(`(?m)^\[([^\]]+)\]\s*$`)
	repoOff    = regexp.MustCompile(`(?mi)^enabled\s*=\s*(0|false|no)\s*$`)
)

func repositories(a *Environment, p *ProfileV) {
	search := func(key string, dirs []string, vale func(id string) bool) {
		is_on, off := "", ""
		for _, c := range dirs {
			entries, _ := filepath.Glob(a.P(c) + "/*.repo")
			for _, v := range entries {
				b, err := os.ReadFile(v)
				if err != nil {
					continue
				}
				t := string(b)
				rel := strings.TrimPrefix(v, strings.TrimSuffix(a.P("/"), "/"))
				idx := repoHeader.FindAllStringSubmatchIndex(t, -1)
				for i, m := range idx {
					id := strings.ToLower(t[m[2]:m[3]])
					if !vale(id) {
						continue
					}
					fine := len(t)
					if i+1 < len(idx) {
						fine = idx[i+1][0]
					}
					if repoOff.MatchString(t[m[1]:fine]) {
						off = rel + " [" + id + "] disabled"
					} else {
						is_on = rel + " [" + id + "]"
					}
				}
			}
		}
		switch {
		case is_on != "":
			p.Detected(key, "present", is_on)
		case off != "":
			p.Detected(key, "absent", off)
		default:
			p.Detected(key, "absent", strings.Join(dirs, " "))
		}
	}
	password := func(x string) func(string) bool {
		return func(id string) bool { return strings.Contains(id, x) }
	}
	// RPM Fusion: «free» (mesa-va-drivers-freeworld, AMD) and, separately, the real «nonfree» branch
	// (intel-media-driver, Intel: phase 18); the «nonfree» ones Fedora Workstation brings disabled (steam,
	// nvidia-driver) do not matter
	search("repo.rpmfusion", []string{"/etc/yum.repos.d"}, password("rpmfusion-free"))
	search("repo.rpmfusion-nonfree", []string{"/etc/yum.repos.d"}, func(id string) bool {
		return id == "rpmfusion-nonfree" || id == "rpmfusion-nonfree-updates"
	})
	// EPEL: not Cisco's OpenH264 repository for EPEL, which a machine may still have (phase 18)
	search("repo.epel", []string{"/etc/yum.repos.d"}, func(id string) bool {
		return strings.Contains(id, "epel") && !strings.Contains(id, "openh264")
	})
	search("repo.packman", []string{"/etc/zypp/repos.d"}, password("packman"))
}

// Scheda is a rendering node with its driver.
type GpuCard struct {
	Nodo, Driver, Fornitore, Gruppo, Modo string
}

var vendors = map[string]string{"0x8086": "Intel", "0x1002": "AMD", "0x10de": "NVIDIA", "0x1af4": "virtio", "0x1234": "QEMU", "0x15ad": "VMware"}

func cards(a *Environment, p *ProfileV) []GpuCard {
	gr, _ := ReadGroups(a.P("/etc/group"))
	groupOf := func(gid uint32) string {
		for n, v := range gr {
			if v[0] == strconv.Itoa(int(gid)) {
				return n
			}
		}
		return strconv.Itoa(int(gid))
	}
	entries, _ := filepath.Glob(a.P("/sys/class/drm/renderD*"))
	sort.Strings(entries)
	var r []GpuCard
	for _, v := range entries {
		s := GpuCard{Nodo: "/dev/dri/" + filepath.Base(v)}
		if l, err := os.Readlink(filepath.Join(v, "device", "driver")); err == nil {
			s.Driver = filepath.Base(l)
		}
		if f, err := os.ReadFile(filepath.Join(v, "device", "vendor")); err == nil {
			id := strings.TrimSpace(string(f))
			s.Fornitore = vendors[id]
			if s.Fornitore == "" {
				s.Fornitore = id
			}
		}
		if st, err := os.Stat(a.P(s.Nodo)); err == nil {
			if sys, ok := st.Sys().(*syscall.Stat_t); ok {
				s.Gruppo = groupOf(sys.Gid)
			}
			s.Modo = fmt.Sprintf("%04o", st.Mode().Perm())
		}
		r = append(r, s)
		k := "gpu." + filepath.Base(v)
		p.Detected(k+".driver", s.Driver, "/sys/class/drm")
		p.Detected(k+".vendor", s.Fornitore, "/sys/class/drm")
		p.Detected(k+".group", s.Gruppo, s.Nodo)
		p.Detected(k+".mode", s.Modo, s.Nodo)
	}
	var names []string
	for _, s := range r {
		names = append(names, filepath.Base(s.Nodo))
	}
	// without nodes the refusal is given by the card verdict (encoding_routes.go, RX-GPU-003)
	if len(names) == 0 {
		p.Detected("gpu.nodes", "none", "/sys/class/drm")
	} else {
		p.Detected("gpu.nodes", strings.Join(names, ","), "/sys/class/drm")
	}
	// NVIDIA with the proprietary driver: the module «nvidia» or its file in /proc (§4.2).
	nv := false
	source := ""
	if _, err := os.Stat(a.P("/proc/driver/nvidia/version")); err == nil {
		nv, source = true, "/proc/driver/nvidia/version"
	}
	if _, err := os.Stat(a.P("/sys/module/nvidia")); err == nil {
		nv, source = true, "/sys/module/nvidia"
	}
	for _, s := range r {
		if s.Driver == "nvidia" {
			nv, source = true, "driver of "+s.Nodo
		}
	}
	p.Detected("gpu.nvidia_proprietary", siNo(nv), source)
	if nv {
		p.Con("RX-GPU-002", "")
	}
	return r
}

// h264: «H.264 really available» is VERIFIED_DONE only if a frame was really
// encoded (§6.5 point 1, §6.6.7): the real test is done in 7a with REMOTIX's binary. Here we read
// what can be read without launching anything. ⭐ Phase 18 (without ffmpeg): the card encodes with
// libva and the distribution's VA driver — we look at the drivers (the dri folders, also
// RPM Fusion's dri-nonfree and dri-freeworld) and their family (driverFamily). Phase 19: it is the
// Detect of the «vaapi» route (encoding_routes.go), and there is no fallback to look at any more. The card stays
// SCONOSCIUTA except in the certain cases: no driver, or only drivers built without H.264.
func h264(a *Environment, p *ProfileV, fam string) {
	var driver []string
	seen_items := map[string]bool{}
	for _, g := range []string{"/usr/lib/*/dri/*_drv_video.so", "/usr/lib64/dri/*_drv_video.so", "/usr/lib/dri/*_drv_video.so",
		"/usr/lib64/dri-nonfree/*_drv_video.so", "/usr/lib64/dri-freeworld/*_drv_video.so"} {
		v, _ := filepath.Glob(a.P(g))
		for _, x := range v {
			n := strings.TrimSuffix(filepath.Base(x), "_drv_video.so")
			if !seen_items[n] {
				seen_items[n] = true
				driver = append(driver, n)
			}
		}
	}
	sort.Strings(driver)
	if len(driver) > 0 {
		p.Detected("h264.driver_va", strings.Join(driver, ","), "dri folders")
	} else {
		p.Detected("h264.driver_va", "none", "dri folders")
	}
	intel, amd, fd := driverFamily(p)
	if len(fd) == 0 {
		p.Unknown("h264.driver_family", "no known VA driver package")
	} else {
		p.Detected("h264.driver_family", strings.Join(fd, "; "), "installed packages")
	}
	note7a := "the test with a frame is done in 7a, with the REMOTIX binary"
	card_vendors, known := cardVendors(p)
	// the certain case: every Intel/AMD card of the machine has only a driver without H.264
	without := (card_vendors["Intel"] || card_vendors["AMD"]) && (!card_vendors["Intel"] || intel == "without") && (!card_vendors["AMD"] || amd == "without")
	// the driver codes (where to get it) only if there is a card of the route: without Intel or AMD
	// the reason is another one, and the verdict says it (RX-GPU-*)
	withCard := !known || card_vendors["Intel"] || card_vendors["AMD"]
	switch {
	case len(driver) == 0:
		p.Place(Fatto{KeyId: "h264.gpu", Val: "no", State: DETECTED, Source: "dri folders", Nota: "no VA-API driver"})
		if withCard {
			p.Con(codeH264(fam), "no VA-API driver")
		}
	case without:
		p.Place(Fatto{KeyId: "h264.gpu", Val: "no", State: DETECTED, Source: "installed packages", Nota: "VA driver without H.264: " + p.V("h264.driver_family")})
		p.Con(codeH264(fam), "VA driver without H.264")
	default:
		p.Unknown("h264.gpu", "driver "+strings.Join(driver, ",")+": "+note7a)
		if withCard {
			p.Con("RX-H264-001", "") // its text already says it: the detail would repeat it
		}
	}
}

func codeH264(fam string) string {
	switch fam {
	case "fedora":
		return "RX-H264-003"
	case "suse":
		return "RX-H264-004"
	}
	return "RX-H264-002"
}

func security(a *Environment, p *ProfileV) {
	if t, ok := load(a, "/sys/fs/selinux/enforce"); ok {
		v := "permissive"
		if strings.TrimSpace(t) == "1" {
			v = "enforcing"
			p.Con("RX-SELINUX-001", "")
		}
		p.Detected("selinux", v, "/sys/fs/selinux/enforce")
	} else {
		p.Detected("selinux", "absent", "/sys/fs/selinux")
	}
	if t, ok := load(a, "/sys/module/apparmor/parameters/enabled"); ok && strings.TrimSpace(t) == "Y" {
		p.Detected("apparmor", "enabled", "/sys/module/apparmor/parameters/enabled")
	} else {
		p.Detected("apparmor", "absent", "/sys/module/apparmor/parameters/enabled")
	}
}

// listeningPort reads /proc/net: is someone already listening on the port?
func listeningPort(a *Environment, port int, proto string) (bool, bool) {
	hex := fmt.Sprintf(":%04X", port)
	read := false
	for _, f := range []string{"/proc/net/" + proto, "/proc/net/" + proto + "6"} {
		t, ok := load(a, f)
		if !ok {
			continue
		}
		read = true
		for _, r := range strings.Split(t, "\n")[1:] {
			c := strings.Fields(r)
			if len(c) < 4 || !strings.HasSuffix(c[1], hex) {
				continue
			}
			if proto == "udp" || c[3] == "0A" { // 0A = LISTEN
				return true, true
			}
		}
	}
	return false, read
}

func firewall(a *Environment, p *ProfileV, port int) {
	ps := strconv.Itoa(port)
	for _, proto := range []string{"tcp", "udp"} {
		occ, read := listeningPort(a, port, proto)
		k := "port." + ps + "." + proto + "_free"
		if !read {
			p.Unknown(k, "/proc/net not readable")
			continue
		}
		p.Detected(k, siNo(!occ), "/proc/net/"+proto)
		if occ {
			p.Con("RX-FW-003", ps+"/"+proto)
		}
	}
	p.Place(Fatto{KeyId: "port." + ps + ".reachable", State: UNKNOWN, Nota: "another machine is needed to find out"})
	p.Con("RX-FW-005", "")

	// firewalld, over the bus
	fw := &firewalldDBus{a.Bus}
	if fw.Lit() {
		p.Detected("firewall.type", "firewalld", "D-Bus "+fwName)
		zone, err := fw.DefaultZone()
		if err != nil {
			p.Unknown("firewall.zone", err.Error())
			p.Con("RX-FW-002", err.Error())
			return
		}
		p.Detected("firewall.zone", zone, "D-Bus getDefaultZone")
		ports, _ := fw.LivePorts(zone)
		for _, proto := range []string{"tcp", "udp"} {
			k := "firewall.port_" + ps + "_" + proto
			ha, err := fw.HasPort(zone, ps+"/"+proto, false)
			if err != nil {
				p.Unknown(k, err.Error())
				p.Con("RX-FW-002", err.Error())
				continue
			}
			if !ha && portInRanges(ports, port, proto) {
				ha = true
			}
			v := "closed"
			if ha {
				v = "open"
			} else {
				p.Con("RX-FW-001", "firewalld, zone "+zone+", "+ps+"/"+proto)
			}
			p.Detected(k, v, "D-Bus queryPort and getPorts, zone "+zone)
		}
		return
	}
	// ufw: enabled in its file; the rules in its files (readable by root)
	if t, ok := load(a, "/etc/ufw/ufw.conf"); ok && strings.Contains(t, "ENABLED=yes") {
		p.Detected("firewall.type", "ufw", "/etc/ufw/ufw.conf")
		rules, ok4 := load(a, "/etc/ufw/user.rules")
		rules6, _ := load(a, "/etc/ufw/user6.rules")
		for _, proto := range []string{"tcp", "udp"} {
			k := "firewall.port_" + ps + "_" + proto
			if !ok4 {
				p.Unknown(k, "/etc/ufw/user.rules not readable (root needed)")
				continue
			}
			if ufwOpens(rules+rules6, ps, proto) {
				p.Detected(k, "open", "/etc/ufw/user.rules")
			} else {
				p.Detected(k, "closed", "/etc/ufw/user.rules")
				p.Con("RX-FW-001", "ufw, "+ps+"/"+proto)
			}
		}
		if !ok4 {
			p.Con("RX-FW-002", "ufw")
		}
		return
	}
	if s, err := a.Bus.ActiveState("nftables.service"); err == nil && s == "active" {
		p.Detected("firewall.type", "nftables", "D-Bus systemd: nftables.service active")
		for _, proto := range []string{"tcp", "udp"} {
			p.Unknown("firewall.port_"+ps+"_"+proto, "nftables rules are not evaluated yet")
		}
		p.Con("RX-FW-002", "nftables")
		return
	} else if err != nil {
		p.Unknown("firewall.type", "neither firewalld on the bus nor ufw running; systemd does not answer on the bus: "+err.Error())
		p.Con("RX-FW-002", "D-Bus: "+err.Error())
		return
	}
	p.Detected("firewall.type", "none", "neither firewalld nor ufw nor nftables running")
}

// ufwOpens: an ACCEPT rule for the port in ufw's files («### tuple ### allow tcp 7447 …» and the
// lines -A ufw-user-input … --dport 7447 -j ACCEPT; without a protocol it holds for both).
func ufwOpens(rules, ps, proto string) bool {
	for _, r := range strings.Split(rules, "\n") {
		if !strings.Contains(r, "--dport "+ps+" ") || !strings.Contains(r, "-j ACCEPT") {
			continue
		}
		if strings.Contains(r, "-p "+proto+" ") || !strings.Contains(r, "-p ") {
			return true
		}
	}
	return false
}

// portInRanges: Fedora Workstation opens 1025-65535 with a range (§11.1), and queryPort does not
// see it. ports: the [port, protocol] pairs of getPorts.
func portInRanges(ports [][]string, port int, proto string) bool {
	for _, v := range ports {
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
		if port >= x && port <= y {
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

func findPam(a *Environment, name string) string {
	for _, c := range []string{"/etc/pam.d/", "/usr/lib/pam.d/", "/usr/etc/pam.d/"} {
		if _, err := os.Stat(a.P(c + name)); err == nil {
			return c + name
		}
	}
	return ""
}

func pam(a *Environment, p *ProfileV, fam string) {
	base := PamBase(fam)
	if base == nil {
		p.Unknown("pam.base", "unknown family")
		return
	}
	var matches, missing_list []string
	faillock := false
	for _, n := range base {
		f := findPam(a, n)
		if f == "" {
			missing_list = append(missing_list, n)
			continue
		}
		matches = append(matches, f)
		if t, ok := load(a, f); ok {
			for _, r := range strings.Split(t, "\n") {
				r = strings.TrimSpace(r)
				if !strings.HasPrefix(r, "#") && strings.Contains(r, "pam_faillock") {
					faillock = true
				}
			}
		}
	}
	p.Detected("pam.base", strings.Join(matches, " "), "family "+fam)
	if len(missing_list) > 0 {
		p.Detected("pam.base_missing", strings.Join(missing_list, " "), "family "+fam)
		p.Con("RX-PAM-001", strings.Join(missing_list, " "))
	}
	p.Detected("pam.faillock", siNo(faillock), strings.Join(matches, " "))
	if faillock {
		p.Con("RX-PAM-002", "")
	}
	if f := findPam(a, "remotix"); f != "" {
		p.Detected("pam.remotix", f, f)
		p.Con("RX-PAM-003", f)
	} else {
		p.Detected("pam.remotix", "absent", "/etc/pam.d, /usr/lib/pam.d")
	}
	module := ""
	for _, g := range []string{"/usr/lib/security", "/usr/lib64/security", "/lib/security", "/lib64/security", "/usr/lib/*/security", "/lib/*/security"} {
		v, _ := filepath.Glob(a.P(g) + "/pam_systemd.so")
		if len(v) > 0 {
			module = strings.TrimPrefix(v[0], strings.TrimSuffix(a.P("/"), "/"))
			break
		}
	}
	if module != "" {
		p.Detected("pam.pam_systemd", module, module)
	} else {
		p.Detected("pam.pam_systemd", "absent", "PAM module directories")
		p.Con("RX-PAM-004", "")
	}
}

func openssl(a *Environment, p *ProfileV, fam string, pk *Pacchetti) {
	v, source := "", ""
	for _, name := range []string{"libssl3t64", "libssl3", "openssl-libs", "libopenssl3", "openssl"} {
		if pv, st, f := pk.Ver(name); st == DETECTED && pv != "absent" {
			v, source = pv, f+" "+name
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
							v, source = c[1], x
						}
					}
				}
			}
		}
	}
	if v == "" {
		p.Unknown("openssl.version", "neither the package nor the library")
		p.Con("RX-OPENSSL-002", "")
		return
	}
	p.Detected("openssl.version", v, source)
	if CompareVersions(v, "3.5.0") < 0 {
		p.Con("RX-OPENSSL-001", v)
	}
}

// logind: KillUserProcesses (§5.2). The live value is asked of logind (VERIFIED_DONE); if it does not
// answer, the configuration files are read in systemd's order (DETECTED); if none
// sets it, the build default holds, which cannot be seen from here (UNKNOWN).
func logind(a *Environment, p *ProfileV) {
	if x, err := a.Bus.Property("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.KillUserProcesses"); err == nil {
		if b, ok := x.(bool); ok {
			v := map[bool]string{true: "yes", false: "no"}[b]
			p.Verified("logind.kill_user_processes", v, "logind, D-Bus")
			if v == "yes" {
				p.Con("RX-LOGIND-001", "")
			}
			return
		}
	}
	value, source := "", ""
	readConf := func(f string) {
		t, ok := load(a, f)
		if !ok {
			return
		}
		for _, r := range strings.Split(t, "\n") {
			r = strings.TrimSpace(r)
			if k, v, ok := strings.Cut(r, "="); ok && strings.TrimSpace(k) == "KillUserProcesses" {
				value, source = strings.ToLower(strings.TrimSpace(v)), f
			}
		}
	}
	readConf("/usr/lib/systemd/logind.conf")
	readConf("/etc/systemd/logind.conf")
	// the drop-ins: by name, and for equal names /etc wins over /run over /usr/local/lib over /usr/lib
	chosen := map[string]string{}
	for _, c := range []string{"/usr/lib/systemd/logind.conf.d", "/usr/local/lib/systemd/logind.conf.d", "/run/systemd/logind.conf.d", "/etc/systemd/logind.conf.d"} {
		v, _ := filepath.Glob(a.P(c) + "/*.conf")
		for _, f := range v {
			chosen[filepath.Base(f)] = c + "/" + filepath.Base(f)
		}
	}
	var names []string
	for n := range chosen {
		names = append(names, n)
	}
	sort.Strings(names)
	for _, n := range names {
		readConf(chosen[n])
	}
	if value == "" {
		p.Unknown("logind.kill_user_processes", "no file sets it and logind did not answer: the build default applies")
		p.Con("RX-LOGIND-002", "")
		return
	}
	if value == "true" || value == "1" {
		value = "yes"
	}
	p.Detected("logind.kill_user_processes", value, source)
	if value == "yes" {
		p.Con("RX-LOGIND-001", source)
	}
}

func groups(a *Environment, p *ProfileV) {
	t, err := ReadGroups(a.P("/etc/group"))
	if err != nil {
		p.Unknown("group.video", err.Error())
		p.Unknown("group.render", err.Error())
		return
	}
	for _, g := range []string{"video", "render"} {
		v, ok := t[g]
		if !ok {
			p.Detected("group."+g, "absent", "/etc/group")
			if g == "render" {
				p.Con("RX-GRUPPI-001", "")
			}
			continue
		}
		p.Detected("group."+g, "gid="+v[0]+" members="+strings.Join(SplitMembers(v[1]), ","), "/etc/group")
	}
}

// fonts: labwc dies without a scalable font (labwc #2525, §11.1). fc-list is not
// launched (closed list): the vector font files in the system folders are counted.
func characters(a *Environment, p *ProfileV) {
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
	p.Place(Fatto{KeyId: "fonts.scalable", Val: strconv.Itoa(n), State: DETECTED, Source: "/usr/share/fonts", Nota: "ttf/otf/ttc/pfb files counted, not asked to fontconfig"})
}
