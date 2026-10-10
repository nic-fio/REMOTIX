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

// PREFLIGHT (fase 1, §6.0): conoscere il sistema, in SOLA LETTURA (R1). Qui dentro nessuna
// funzione scrive, crea, rinomina o cambia permessi. Si leggono file (/etc, /sys, /proc, gli
// archivi di dpkg e pacman, le librerie); si chiede sul D-Bus a logind, systemd e firewalld
// (solo letture: proprietà, query); l'unico programma lanciato è «rpm -q» sulle famiglie RPM
// (DECISIONI §10.14: elenco chiuso, ambiente.go), annotato nel profilo. La prova R1 lo controlla
// con le impronte di /etc prima e dopo, in un contenitore per famiglia (prove/r1-contenitori.sh).

// OpzioniPreflight: la porta da guardare e i pacchetti in più che il catalogo vuole sapere.
type OpzioniPreflight struct {
	Porta     int
	Pacchetti []string // componenti (labwc, gnome-session, i caratteri…) chiesti dal catalogo
}

// Preflight costruisce il profilo della macchina.
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

// leggi un file della macchina; "" se non c'è.
func leggi(a *Ambiente, percorso string) (string, bool) {
	b, err := os.ReadFile(a.P(percorso))
	if err != nil {
		return "", false
	}
	return string(b), true
}

// OsRelease legge /etc/os-release (o /usr/lib/os-release).
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

// Famiglia: debian, fedora (anche RHEL e derivate), arch, suse, o "".
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
	p.Rilevato("distro.versione", m["VERSION_ID"], fonte)
	p.Rilevato("distro.nome", m["PRETTY_NAME"], fonte)
	p.Rilevato("distro.variante", m["VARIANT_ID"], fonte)
	fam := Famiglia(m["ID"], m["ID_LIKE"])
	p.Rilevato("distro.famiglia", fam, "ID e ID_LIKE")
	// Le immutabili (§3, D9): /usr in sola lettura, installazione con riavvio.
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
	p.Rilevato("distro.immutabile", siNo(immutabile), fonteImm)
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
	p.Rilevato("sistema.architettura", arch, "the engine itself")
	if k, ok := leggi(a, "/proc/sys/kernel/osrelease"); ok {
		p.Rilevato("sistema.kernel", strings.TrimSpace(k), "/proc/sys/kernel/osrelease")
	}
	// Partita con systemd: la cartella che systemd crea all'avvio (sd_booted()).
	if st, err := os.Stat(a.P("/run/systemd/system")); err == nil && st.IsDir() {
		p.Rilevato("sistema.systemd", "si", "/run/systemd/system")
	} else {
		p.Rilevato("sistema.systemd", "no", "/run/systemd/system is missing")
		p.Con("RX-SYSTEMD-001", "")
	}
	if h, ok := leggi(a, "/proc/sys/kernel/hostname"); ok {
		p.Rilevato("sistema.nome", strings.TrimSpace(h), "/proc/sys/kernel/hostname")
	}
}

// pacchettiFissi: quelli che il PREFLIGHT guarda sempre, oltre ai desktop e al catalogo.
var pacchettiFissi = []string{"labwc", "firewalld", "ufw", "nftables",
	"libssl3t64", "libssl3", "openssl-libs", "libopenssl3", "openssl",
	// la famiglia del driver VA (§4.2, fase 18): Intel completo o ridotto, Mesa coi codec o senza
	"intel-media-driver", "intel-media-driver-free", "libva-intel-media-driver", "intel-media-va-driver",
	"intel-media-va-driver-non-free", "mesa-va-drivers", "mesa-va-drivers-freeworld", "mesa-dri-drivers", "Mesa-dri"}

// famigliaDriver: dal pacchetto installato, se il driver VA codifica H.264 (§4.2, fase 18). Fedora:
// libva-intel-media-driver (già intel-media-driver-free) e la Mesa ufficiale sono costruiti SENZA
// H.264 — `[M]` 30 set, dai binari: 38 nomi di classe della codifica AVC contro i 114 del driver di
// RPM Fusion; openSUSE: il driver Intel ufficiale è quello completo (104-115, come RPM Fusion), la Mesa
// ufficiale è senza h264/h265 («re-disable video codecs», changelog di Mesa-dri), quella di Packman
// (versione «.pm.») coi codec. Torna, per Intel e AMD, "con", "senza" o "" (non riconosciuto), e
// la descrizione (f) per il fatto h264.famiglia_driver. Non scrive niente nel profilo: la usa anche
// il verdetto sulla scheda (strade.go), dentro Valuta.
func famigliaDriver(p *Profilo) (intel, amd string, f []string) {
	c := func(n string) bool { v := p.V("pacchetto." + n); return v != "" && v != "assente" }
	fam := p.V("distro.famiglia")
	switch {
	case c("intel-media-driver") || c("intel-media-va-driver-non-free") || c("intel-media-va-driver"):
		intel = "con"
		f = append(f, "intel (iHD, with H.264)")
	case c("libva-intel-media-driver") || c("intel-media-driver-free"):
		intel = "senza"
		f = append(f, "libva-intel-media-driver of Fedora/RHEL (no H.264 encoding)")
	}
	switch {
	case c("mesa-va-drivers-freeworld"):
		amd = "con"
		f = append(f, "mesa freeworld (radeonsi with H.264)")
	case fam == "fedora" && (c("mesa-va-drivers") || c("mesa-dri-drivers")):
		amd = "senza"
		f = append(f, "Mesa of Fedora/RHEL (no H.264)")
	case fam == "suse" && c("Mesa-dri") && strings.Contains(p.V("pacchetto.Mesa-dri"), ".pm."):
		amd = "con"
		f = append(f, "Mesa from Packman (radeonsi with H.264)")
	case fam == "suse" && c("Mesa-dri"):
		amd = "senza"
		f = append(f, "Mesa of openSUSE (no H.264)")
	case fam == "debian" && c("mesa-va-drivers"):
		amd = "con"
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

// Pacchetti: l'archivio del gestore di pacchetti, letto una volta. dpkg e pacman dai loro file
// (formati stabili da decenni); rpm con UNA chiamata «rpm -q» per tutti i nomi (il suo archivio
// non si legge senza di lui).
type Pacchetti struct {
	fonte    string
	versioni map[string]string // nome → versione; assente = non installato
	letto    bool
}

// ArchivioPacchetti legge l'archivio della famiglia per i nomi dati.
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

// Versione: la versione, "assente", o SCONOSCIUTO se l'archivio non si è letto.
func (pk *Pacchetti) Versione(nome string) (string, StatoFatto, string) {
	if !pk.letto {
		return "", SCONOSCIUTO, pk.fonte
	}
	if v, ok := pk.versioni[nome]; ok {
		return v, RILEVATO, pk.fonte
	}
	return "assente", RILEVATO, pk.fonte
}

// PacchettoDesktop: il pacchetto che dice se un desktop c'è, e con che versione.
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

// binari di ripiego per sapere se un desktop c'è quando il gestore di pacchetti non risponde.
var binarioDesktop = map[string]string{"gnome": "/usr/bin/gnome-shell", "kde": "/usr/bin/plasmashell", "xfce": "/usr/bin/xfce4-session", "lxqt": "/usr/bin/lxqt-session"}

func desktop(a *Ambiente, p *Profilo, fam string, pk *Pacchetti, extra []string) {
	for _, d := range DESKTOP {
		nome := PacchettoDesktop(fam, d)
		v, st, fonte := pk.Versione(nome)
		if st == SCONOSCIUTO {
			if _, err := os.Stat(a.P(binarioDesktop[d])); err == nil {
				p.Metti(Fatto{Chiave: "desktop." + d, Valore: "presente", Stato: RILEVATO, Fonte: binarioDesktop[d], Nota: "unknown version: the package database could not be read"})
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
			p.Sconosciuto("pacchetto."+nome, "the package database could not be read ("+fonte+")")
			continue
		}
		p.Metti(Fatto{Chiave: "pacchetto." + nome, Valore: v, Stato: st, Fonte: fonte})
	}
}

// depositi di terzi che contano per H.264 e per KDE su Alma (§4.2, §11.1).
//
// Un deposito c'è se una SEZIONE di un .repo col suo nome è ACCESA («enabled» che manca = acceso,
// come per dnf e zypper). `[M]` 30 set, fedora44-gnome: prima bastava la parola in un file qualunque,
// e fedora-workstation-repositories porta rpmfusion-nonfree-steam SPENTO ⇒ RPM Fusion «presente»,
// nessuna condizione C-DEPOSITO, nessun consenso chiesto, e REMOTIX senza codifica (T9, R22).
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
						spenti = rel + " [" + id + "] spento"
					} else {
						acceso = rel + " [" + id + "]"
					}
				}
			}
		}
		switch {
		case acceso != "":
			p.Rilevato(chiave, "presente", acceso)
		case spenti != "":
			p.Rilevato(chiave, "assente", spenti)
		default:
			p.Rilevato(chiave, "assente", strings.Join(cartelle, " "))
		}
	}
	parola := func(x string) func(string) bool {
		return func(id string) bool { return strings.Contains(id, x) }
	}
	// RPM Fusion: «free» (mesa-va-drivers-freeworld, AMD) e, a parte, il ramo «nonfree» vero e proprio
	// (intel-media-driver, Intel: fase 18); i «nonfree» che Fedora Workstation porta spenti (steam,
	// nvidia-driver) non c'entrano
	cerca("deposito.rpmfusion", []string{"/etc/yum.repos.d"}, parola("rpmfusion-free"))
	cerca("deposito.rpmfusion-nonfree", []string{"/etc/yum.repos.d"}, func(id string) bool {
		return id == "rpmfusion-nonfree" || id == "rpmfusion-nonfree-updates"
	})
	// EPEL: non il deposito Cisco di OpenH264 per EPEL, che una macchina può ancora avere (fase 18)
	cerca("deposito.epel", []string{"/etc/yum.repos.d"}, func(id string) bool {
		return strings.Contains(id, "epel") && !strings.Contains(id, "openh264")
	})
	cerca("deposito.packman", []string{"/etc/zypp/repos.d"}, parola("packman"))
}

// Scheda è un nodo di disegno col suo driver.
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
		k := "scheda." + filepath.Base(v)
		p.Rilevato(k+".driver", s.Driver, "/sys/class/drm")
		p.Rilevato(k+".fornitore", s.Fornitore, "/sys/class/drm")
		p.Rilevato(k+".gruppo", s.Gruppo, s.Nodo)
		p.Rilevato(k+".modo", s.Modo, s.Nodo)
	}
	var nomi []string
	for _, s := range r {
		nomi = append(nomi, filepath.Base(s.Nodo))
	}
	// senza nodi il rifiuto lo dà il verdetto sulla scheda (strade.go, RX-GPU-003)
	if len(nomi) == 0 {
		p.Rilevato("scheda.nodi", "nessuno", "/sys/class/drm")
	} else {
		p.Rilevato("scheda.nodi", strings.Join(nomi, ","), "/sys/class/drm")
	}
	// NVIDIA col driver proprietario: il modulo «nvidia» o il suo file in /proc (§4.2).
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
	p.Rilevato("scheda.nvidia_proprietaria", siNo(nv), fonte)
	if nv {
		p.Con("RX-GPU-002", "")
	}
	return r
}

// h264: «H.264 davvero disponibile» è VERIFICATO solo se un fotogramma è stato codificato
// davvero (§6.5 punto 1, §6.6.7): la prova vera si fa in 7a col binario di REMOTIX. Qui si legge
// quel che si può leggere senza lanciare niente. ⭐ Fase 18 (senza ffmpeg): la scheda codifica con
// libva e il driver VA della distribuzione — si guardano i driver (le cartelle dri, anche
// dri-nonfree e dri-freeworld di RPM Fusion) e la loro famiglia (famigliaDriver). Fase 19: è la
// Rileva della strada «vaapi» (strade.go), e non c'è più un ripiego da guardare. La scheda resta
// SCONOSCIUTA salvo i casi certi: nessun driver, o solo driver costruiti senza H.264.
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
		p.Rilevato("h264.driver_va", strings.Join(driver, ","), "cartelle dri")
	} else {
		p.Rilevato("h264.driver_va", "nessuno", "cartelle dri")
	}
	intel, amd, fd := famigliaDriver(p)
	if len(fd) == 0 {
		p.Sconosciuto("h264.famiglia_driver", "no known VA driver package")
	} else {
		p.Rilevato("h264.famiglia_driver", strings.Join(fd, "; "), "installed packages")
	}
	nota7a := "the test with a frame is done in 7a, with the REMOTIX binary"
	forn, noti := fornitoriScheda(p)
	// il caso certo: ogni scheda Intel/AMD della macchina ha solo un driver senza H.264
	senza := (forn["Intel"] || forn["AMD"]) && (!forn["Intel"] || intel == "senza") && (!forn["AMD"] || amd == "senza")
	// i codici del driver (dove prenderlo) solo se c'è una scheda della strada: senza Intel né AMD
	// il motivo è un altro, e lo dice il verdetto (RX-GPU-*)
	conScheda := !noti || forn["Intel"] || forn["AMD"]
	switch {
	case len(driver) == 0:
		p.Metti(Fatto{Chiave: "h264.scheda", Valore: "no", Stato: RILEVATO, Fonte: "cartelle dri", Nota: "no VA-API driver"})
		if conScheda {
			p.Con(codiceH264(fam), "no VA-API driver")
		}
	case senza:
		p.Metti(Fatto{Chiave: "h264.scheda", Valore: "no", Stato: RILEVATO, Fonte: "installed packages", Nota: "VA driver without H.264: " + p.V("h264.famiglia_driver")})
		p.Con(codiceH264(fam), "VA driver without H.264")
	default:
		p.Sconosciuto("h264.scheda", "driver "+strings.Join(driver, ",")+": "+nota7a)
		if conScheda {
			p.Con("RX-H264-001", nota7a)
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
		p.Rilevato("selinux", "assente", "/sys/fs/selinux")
	}
	if t, ok := leggi(a, "/sys/module/apparmor/parameters/enabled"); ok && strings.TrimSpace(t) == "Y" {
		p.Rilevato("apparmor", "attivo", "/sys/module/apparmor/parameters/enabled")
	} else {
		p.Rilevato("apparmor", "assente", "/sys/module/apparmor/parameters/enabled")
	}
}

// portaInAscolto legge /proc/net: qualcuno ascolta già sulla porta?
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
		k := "porta." + ps + "." + proto + "_libera"
		if !letto {
			p.Sconosciuto(k, "/proc/net not readable")
			continue
		}
		p.Rilevato(k, siNo(!occ), "/proc/net/"+proto)
		if occ {
			p.Con("RX-FW-003", ps+"/"+proto)
		}
	}
	p.Metti(Fatto{Chiave: "porta." + ps + ".raggiungibile", Stato: SCONOSCIUTO, Nota: "another machine is needed to find out"})
	p.Con("RX-FW-005", "")

	// firewalld, sul bus
	fw := &firewalldDBus{a.Bus}
	if fw.Acceso() {
		p.Rilevato("firewall.tipo", "firewalld", "D-Bus "+fwNome)
		zona, err := fw.ZonaPredefinita()
		if err != nil {
			p.Sconosciuto("firewall.zona", err.Error())
			p.Con("RX-FW-002", err.Error())
			return
		}
		p.Rilevato("firewall.zona", zona, "D-Bus getDefaultZone")
		porte, _ := fw.PorteVive(zona)
		for _, proto := range []string{"tcp", "udp"} {
			k := "firewall.porta_" + ps + "_" + proto
			ha, err := fw.HaPorta(zona, ps+"/"+proto, false)
			if err != nil {
				p.Sconosciuto(k, err.Error())
				p.Con("RX-FW-002", err.Error())
				continue
			}
			if !ha && portaInIntervalli(porte, porta, proto) {
				ha = true
			}
			v := "chiusa"
			if ha {
				v = "aperta"
			} else {
				p.Con("RX-FW-001", "firewalld, zona "+zona+", "+ps+"/"+proto)
			}
			p.Rilevato(k, v, "D-Bus queryPort e getPorts, zona "+zona)
		}
		return
	}
	// ufw: acceso nel suo file; le regole nei suoi file (leggibili da root)
	if t, ok := leggi(a, "/etc/ufw/ufw.conf"); ok && strings.Contains(t, "ENABLED=yes") {
		p.Rilevato("firewall.tipo", "ufw", "/etc/ufw/ufw.conf")
		regole, ok4 := leggi(a, "/etc/ufw/user.rules")
		regole6, _ := leggi(a, "/etc/ufw/user6.rules")
		for _, proto := range []string{"tcp", "udp"} {
			k := "firewall.porta_" + ps + "_" + proto
			if !ok4 {
				p.Sconosciuto(k, "/etc/ufw/user.rules not readable (root needed)")
				continue
			}
			if ufwApre(regole+regole6, ps, proto) {
				p.Rilevato(k, "aperta", "/etc/ufw/user.rules")
			} else {
				p.Rilevato(k, "chiusa", "/etc/ufw/user.rules")
				p.Con("RX-FW-001", "ufw, "+ps+"/"+proto)
			}
		}
		if !ok4 {
			p.Con("RX-FW-002", "ufw")
		}
		return
	}
	if s, err := a.Bus.StatoAttivo("nftables.service"); err == nil && s == "active" {
		p.Rilevato("firewall.tipo", "nftables", "D-Bus systemd: nftables.service attiva")
		for _, proto := range []string{"tcp", "udp"} {
			p.Sconosciuto("firewall.porta_"+ps+"_"+proto, "nftables rules are not evaluated yet")
		}
		p.Con("RX-FW-002", "nftables")
		return
	} else if err != nil {
		p.Sconosciuto("firewall.tipo", "neither firewalld on the bus nor ufw running; systemd does not answer on the bus: "+err.Error())
		p.Con("RX-FW-002", "D-Bus: "+err.Error())
		return
	}
	p.Rilevato("firewall.tipo", "nessuno", "neither firewalld nor ufw nor nftables running")
}

// ufwApre: una regola ACCEPT per la porta nei file di ufw («### tuple ### allow tcp 7447 …» e le
// righe -A ufw-user-input … --dport 7447 -j ACCEPT; senza protocollo vale per tutti e due).
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

// portaInIntervalli: Fedora Workstation apre 1025-65535 con un intervallo (§11.1), e queryPort non
// lo vede. porte: le coppie [porta, protocollo] di getPorts.
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

// PamBase: i file della pila della famiglia su cui il file di REMOTIX si appoggia (§4.3).
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
	p.Rilevato("pam.base", strings.Join(trovati, " "), "famiglia "+fam)
	if len(mancanti) > 0 {
		p.Rilevato("pam.base_mancanti", strings.Join(mancanti, " "), "famiglia "+fam)
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
		p.Rilevato("pam.remotix", "assente", "/etc/pam.d, /usr/lib/pam.d")
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
		p.Rilevato("pam.pam_systemd", "assente", "PAM module directories")
		p.Con("RX-PAM-004", "")
	}
}

func openssl(a *Ambiente, p *Profilo, fam string, pk *Pacchetti) {
	v, fonte := "", ""
	for _, nome := range []string{"libssl3t64", "libssl3", "openssl-libs", "libopenssl3", "openssl"} {
		if pv, st, f := pk.Versione(nome); st == RILEVATO && pv != "assente" {
			v, fonte = pv, f+" "+nome
			break
		}
	}
	if v == "" { // dalla libreria stessa: la stringa «OpenSSL 3.x.y»
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
		p.Sconosciuto("openssl.versione", "neither the package nor the library")
		p.Con("RX-OPENSSL-002", "")
		return
	}
	p.Rilevato("openssl.versione", v, fonte)
	if ConfrontaVersioni(v, "3.5.0") < 0 {
		p.Con("RX-OPENSSL-001", v)
	}
}

// logind: KillUserProcesses (§5.2). Il valore vivo si chiede a logind (VERIFICATO); se non
// risponde, si leggono i file di configurazione nell'ordine di systemd (RILEVATO); se nessuno lo
// imposta, vale il predefinito della compilazione, che da qui non si vede (SCONOSCIUTO).
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
	// i drop-in: per nome, e a parità di nome vince /etc su /run su /usr/local/lib su /usr/lib
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
		p.Sconosciuto("gruppo.video", err.Error())
		p.Sconosciuto("gruppo.render", err.Error())
		return
	}
	for _, g := range []string{"video", "render"} {
		v, ok := t[g]
		if !ok {
			p.Rilevato("gruppo."+g, "assente", "/etc/group")
			if g == "render" {
				p.Con("RX-GRUPPI-001", "")
			}
			continue
		}
		p.Rilevato("gruppo."+g, "gid="+v[0]+" membri="+strings.Join(DividiMembri(v[1]), ","), "/etc/group")
	}
}

// caratteri: labwc muore senza un carattere scalabile (labwc #2525, §11.1). Non si lancia
// fc-list (elenco chiuso): si contano i file di caratteri vettoriali nelle cartelle di sistema.
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
	p.Metti(Fatto{Chiave: "caratteri.scalabili", Valore: strconv.Itoa(n), Stato: RILEVATO, Fonte: "/usr/share/fonts", Nota: "ttf/otf/ttc/pfb files counted, not asked to fontconfig"})
}
