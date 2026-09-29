package motore

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/godbus/dbus/v5"
)

// Il desktop di una sessione REMOTIX non vive tutto nello scope della sessione: [M] 30 set,
// debian13-gnome e debian13+LXQt — gnome-shell, kwin, i portali e i servizi del desktop sono
// unità del GESTORE D'UTENTE (user@UID.service). La regola §10.16 dice «le sessioni REMOTIX e i
// loro processi», e insieme «mai gli altri processi dell'utente»: il motore parla col gestore
// d'utente sul D-Bus (il suo socket privato /run/user/UID/systemd/private, che systemd apre a root)
// e ferma SOLO le unità del desktop — mai user@UID intero, mai TerminateUser.
//
// Quali sono: graphical-session.target (con quel che ne dipende), più ogni unità del gestore
// d'utente che ha un processo nato DENTRO il desktop — riconosciuto dal suo ambiente, che porta
// WAYLAND_DISPLAY o DISPLAY (il desktop li esporta nel gestore d'utente; pipewire e gli altri
// servizi nati prima, senza grafica, non li hanno e restano). Il motore lo fa solo se la persona
// non ha un'altra sessione grafica aperta (un desktop locale davanti al monitor).

// ProcessoGrafico: un processo del desktop nel gestore d'utente, con la sua unità.
type ProcessoGrafico struct {
	PID   int
	Unita string
	Nome  string
}

// ProcessiGrafici legge /proc: i processi dell'uid dentro user@UID.service con WAYLAND_DISPLAY o
// DISPLAY nell'ambiente.
func ProcessiGrafici(a *Ambiente, uid int) []ProcessoGrafico {
	var r []ProcessoGrafico
	voci, _ := filepath.Glob(a.P("/proc") + "/[0-9]*")
	cerca := fmt.Sprintf("/user@%d.service/", uid)
	for _, v := range voci {
		pid, err := strconv.Atoi(filepath.Base(v))
		if err != nil {
			continue
		}
		cg, err := os.ReadFile(v + "/cgroup")
		if err != nil {
			continue
		}
		c := strings.TrimSpace(string(cg))
		i := strings.Index(c, cerca)
		if i < 0 || strings.HasSuffix(c, "/init.scope") {
			continue
		}
		env, err := os.ReadFile(v + "/environ")
		if err != nil {
			continue
		}
		grafico := false
		for _, x := range strings.Split(string(env), "\x00") {
			if strings.HasPrefix(x, "WAYLAND_DISPLAY=") || strings.HasPrefix(x, "DISPLAY=") {
				grafico = true
			}
		}
		if !grafico {
			continue
		}
		nome, _ := os.ReadFile(v + "/comm")
		r = append(r, ProcessoGrafico{PID: pid, Unita: filepath.Base(c), Nome: strings.TrimSpace(string(nome))})
	}
	sort.Slice(r, func(i, j int) bool { return r[i].PID < r[j].PID })
	return r
}

// condivisa: unità del gestore d'utente che servono a tutta la persona (il bus di sessione, con
// dentro i servizi attivati «alla vecchia»): non si fermano; si segnalano i soli processi grafici.
var condivisa = map[string]bool{"dbus.service": true, "dbus-broker.service": true, "init.scope": true}

// gestoreUtente: la connessione diretta al gestore d'utente di systemd.
func gestoreUtente(uid int) (*dbus.Conn, error) {
	conn, err := dbus.Dial(fmt.Sprintf("unix:path=/run/user/%d/systemd/private", uid))
	if err != nil {
		return nil, err
	}
	if err := conn.Auth(nil); err != nil {
		conn.Close()
		return nil, err
	}
	return conn, nil
}

func uidDi(a *Ambiente, utente string) (int, error) {
	f, err := os.ReadFile(a.P("/etc/passwd"))
	if err != nil {
		return 0, err
	}
	for _, r := range strings.Split(string(f), "\n") {
		c := strings.Split(r, ":")
		if len(c) >= 3 && c[0] == utente {
			return strconv.Atoi(c[2])
		}
	}
	return 0, Errore("RX-GRUPPI-003", utente)
}

// ChiudiGraficaUtente: ferma graphical-session.target e le unità coi processi grafici; toglie
// WAYLAND_DISPLAY e DISPLAY dall'ambiente del gestore (le attivazioni dopo non nascono «nel
// desktop»); dopo 15 s, a chi resta, SIGKILL alla sua unità (KillUnit). Restituisce le unità fermate.
func ChiudiGraficaUtente(a *Ambiente, utente string) ([]string, error) {
	uid, err := uidDi(a, utente)
	if err != nil {
		return nil, err
	}
	conn, err := gestoreUtente(uid)
	if err != nil {
		return nil, err
	}
	defer conn.Close()
	o := conn.Object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
	m := "org.freedesktop.systemd1.Manager."
	var job dbus.ObjectPath
	unita := map[string]bool{"graphical-session.target": true}
	for _, p := range ProcessiGrafici(a, uid) {
		unita[p.Unita] = true
	}
	var fermate []string
	for u := range unita {
		if condivisa[u] { // il bus di sessione è di tutta la persona: si fermano solo i processi del desktop
			continue
		}
		if err := o.Call(m+"StopUnit", 0, u, "replace").Store(&job); err == nil {
			fermate = append(fermate, u)
		}
	}
	segnale := func(sg syscall.Signal) {
		for _, p := range ProcessiGrafici(a, uid) {
			if condivisa[p.Unita] {
				syscall.Kill(p.PID, sg)
			}
		}
	}
	segnale(syscall.SIGTERM)
	o.Call(m+"UnsetEnvironment", 0, []string{"WAYLAND_DISPLAY", "DISPLAY"})
	for i := 0; i < 30 && len(ProcessiGrafici(a, uid)) > 0; i++ {
		time.Sleep(500 * time.Millisecond)
	}
	segnale(syscall.SIGKILL)
	for _, p := range ProcessiGrafici(a, uid) {
		if !condivisa[p.Unita] {
			o.Call(m+"KillUnit", 0, p.Unita, "all", int32(9))
		}
	}
	sort.Strings(fermate)
	return fermate, nil
}
