package engine

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

// The desktop of a REMOTIX session does not live entirely in the session's scope: [M] 30 Sep,
// debian13-gnome and debian13+LXQt — gnome-shell, kwin, the portals and the desktop's services are
// units of the USER MANAGER (user@UID.service). Rule §10.16 says «REMOTIX sessions and their
// processes», and together «never the user's other processes»: the engine talks to the user
// manager over D-Bus (its private socket /run/user/UID/systemd/private, which systemd opens to root)
// and stops ONLY the desktop's units — never the whole user@UID, never TerminateUser.
//
// Which ones: graphical-session.target (with what depends on it), plus every unit of the user
// manager that has a process born INSIDE the desktop — recognised by its environment, which carries
// WAYLAND_DISPLAY or DISPLAY (the desktop exports them into the user manager; pipewire and the other
// services born earlier, without graphics, do not have them and stay). The engine does it only if the person
// has no other graphical session open (a local desktop in front of the monitor).

// GraphicalProcess: a desktop process in the user manager, with its unit.
type GraphicalProcess struct {
	PID   int
	Unita string
	Nome  string
}

// GraphicalProcesses reads /proc: the uid's processes inside user@UID.service with WAYLAND_DISPLAY or
// DISPLAY in the environment.
func GraphicalProcesses(a *Environment, uid int) []GraphicalProcess {
	var r []GraphicalProcess
	entries, _ := filepath.Glob(a.P("/proc") + "/[0-9]*")
	search := fmt.Sprintf("/user@%d.service/", uid)
	for _, v := range entries {
		pid, err := strconv.Atoi(filepath.Base(v))
		if err != nil {
			continue
		}
		cg, err := os.ReadFile(v + "/cgroup")
		if err != nil {
			continue
		}
		c := strings.TrimSpace(string(cg))
		i := strings.Index(c, search)
		if i < 0 || strings.HasSuffix(c, "/init.scope") {
			continue
		}
		env, err := os.ReadFile(v + "/environ")
		if err != nil {
			continue
		}
		graphical := false
		for _, x := range strings.Split(string(env), "\x00") {
			if strings.HasPrefix(x, "WAYLAND_DISPLAY=") || strings.HasPrefix(x, "DISPLAY=") {
				graphical = true
			}
		}
		if !graphical {
			continue
		}
		name, _ := os.ReadFile(v + "/comm")
		r = append(r, GraphicalProcess{PID: pid, Unita: filepath.Base(c), Nome: strings.TrimSpace(string(name))})
	}
	sort.Slice(r, func(i, j int) bool { return r[i].PID < r[j].PID })
	return r
}

// shared: user-manager units that needs the whole person (the session bus, with
// the services activated «the old way» inside): they are not stopped; only the graphical processes are reported.
var shared = map[string]bool{"dbus.service": true, "dbus-broker.service": true, "init.scope": true}

// userManager: the direct connection to systemd's user manager.
func userManager(uid int) (*dbus.Conn, error) {
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

func uidDi(a *Environment, user string) (int, error) {
	f, err := os.ReadFile(a.P("/etc/passwd"))
	if err != nil {
		return 0, err
	}
	for _, r := range strings.Split(string(f), "\n") {
		c := strings.Split(r, ":")
		if len(c) >= 3 && c[0] == user {
			return strconv.Atoi(c[2])
		}
	}
	return 0, Error("RX-GRUPPI-003", user)
}

// CloseGraphicalUser: stops graphical-session.target and the units with graphical processes; removes
// WAYLAND_DISPLAY and DISPLAY from the manager's environment (later activations are not born «in the
// desktop»); after 15 s, to whatever remains, SIGKILL to its unit (KillUnit). Returns the stopped units.
func CloseGraphicalUser(a *Environment, user string) ([]string, error) {
	uid, err := uidDi(a, user)
	if err != nil {
		return nil, err
	}
	conn, err := userManager(uid)
	if err != nil {
		return nil, err
	}
	defer conn.Close()
	o := conn.Object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
	m := "org.freedesktop.systemd1.Manager."
	var job dbus.ObjectPath
	unit := map[string]bool{"graphical-session.target": true}
	for _, p := range GraphicalProcesses(a, uid) {
		unit[p.Unita] = true
	}
	var stopped []string
	for u := range unit {
		if shared[u] { // the session bus belongs to the whole person: only the desktop's processes are stopped
			continue
		}
		if err := o.Call(m+"StopUnit", 0, u, "replace").Store(&job); err == nil {
			stopped = append(stopped, u)
		}
	}
	send_signal := func(sg syscall.Signal) {
		for _, p := range GraphicalProcesses(a, uid) {
			if shared[p.Unita] {
				syscall.Kill(p.PID, sg)
			}
		}
	}
	send_signal(syscall.SIGTERM)
	o.Call(m+"UnsetEnvironment", 0, []string{"WAYLAND_DISPLAY", "DISPLAY"})
	for i := 0; i < 30 && len(GraphicalProcesses(a, uid)) > 0; i++ {
		time.Sleep(500 * time.Millisecond)
	}
	send_signal(syscall.SIGKILL)
	for _, p := range GraphicalProcesses(a, uid) {
		if !shared[p.Unita] {
			o.Call(m+"KillUnit", 0, p.Unita, "all", int32(9))
		}
	}
	sort.Strings(stopped)
	return stopped, nil
}
