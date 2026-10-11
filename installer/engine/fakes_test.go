package engine

// A fake machine under a folder: /etc/group, /etc/passwd, the real files, and fake systemd and
// firewalld made of JSON files (so that the state survives a killed process, as on the
// real machine). The engine does not know the difference: it uses the same interfaces.

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	"remotix/installer/catalog"
)

type fakeGroups struct{ root string }

func (g *fakeGroups) file() string { return filepath.Join(g.root, "etc/group") }

func (g *fakeGroups) Members(group string) ([]string, string, bool, error) {
	t, err := ReadGroups(g.file())
	if err != nil {
		return nil, "", false, err
	}
	v, ok := t[group]
	return SplitMembers(v[1]), v[0], ok, nil
}

func (g *fakeGroups) PrimaryGroup(u string) (string, bool, error) {
	return ReadUser(filepath.Join(g.root, "etc/passwd"), u)
}

// change rewrites the group's line keeping the members' order (like gpasswd).
func (g *fakeGroups) change(group string, f func([]string) []string) error {
	b, err := os.ReadFile(g.file())
	if err != nil {
		return err
	}
	lines := strings.Split(strings.TrimSuffix(string(b), "\n"), "\n")
	for i, r := range lines {
		c := strings.Split(r, ":")
		if len(c) == 4 && c[0] == group {
			var m []string
			for _, x := range strings.Split(c[3], ",") {
				if x != "" {
					m = append(m, x)
				}
			}
			c[3] = strings.Join(f(m), ",")
			lines[i] = strings.Join(c, ":")
		}
	}
	return WriteAtomic(g.file(), []byte(strings.Join(lines, "\n")+"\n"), 0o644)
}

func (g *fakeGroups) Insert(u, group string) error {
	return g.change(group, func(m []string) []string { return append(m, u) })
}

func (g *fakeGroups) Remove(u, group string) error {
	return g.change(group, func(m []string) []string {
		var r []string
		for _, x := range m {
			if x != u {
				r = append(r, x)
			}
		}
		return r
	})
}

// statoJSON: a map in a file (fake systemd and firewalld).
func readMap(p string) map[string]bool {
	m := map[string]bool{}
	if b, err := os.ReadFile(p); err == nil {
		json.Unmarshal(b, &m)
	}
	return m
}

func writeMap(p string, m map[string]bool) error {
	b, _ := json.Marshal(m)
	return WriteAtomic(p, b, 0o644)
}

type fakeUnits struct{ root string }

func (u *fakeUnits) file() string { return filepath.Join(u.root, "var/lib/finto-systemd.json") }

func (u *fakeUnits) State(n string) (string, error) {
	if _, err := os.Stat(filepath.Join(u.root, "rompi-systemctl")); err == nil {
		return "", fmt.Errorf("systemctl: timed out (fake)")
	}
	if _, err := os.Stat(filepath.Join(u.root, "etc/systemd/system", n)); err != nil {
		return "not-found", nil
	}
	if readMap(u.file())[n] {
		return "enabled", nil
	}
	return "disabled", nil
}

func (u *fakeUnits) Enable(n string) error {
	m := readMap(u.file())
	m[n] = true
	return writeMap(u.file(), m)
}

func (u *fakeUnits) Disable(n string) error {
	m := readMap(u.file())
	delete(m, n)
	return writeMap(u.file(), m)
}

type fakeFirewall struct{ root string }

func (f *fakeFirewall) file() string { return filepath.Join(f.root, "var/lib/finto-firewalld.json") }

func (f *fakeFirewall) Nome() string {
	if b, err := os.ReadFile(filepath.Join(f.root, "etc/finto-firewall")); err == nil {
		return strings.TrimSpace(string(b))
	}
	return "firewalld"
}
func (f *fakeFirewall) DefaultZone() (string, error) { return "public", nil }
func keyFw(z, p string, perm bool) string {
	if perm {
		return z + " " + p + " permanente"
	}
	return z + " " + p + " vive"
}
func (f *fakeFirewall) HasPort(z, p string, perm bool) (bool, error) {
	return readMap(f.file())[keyFw(z, p, perm)], nil
}
func (f *fakeFirewall) Insert(z, p string, perm bool) error {
	m := readMap(f.file())
	m[keyFw(z, p, perm)] = true
	return writeMap(f.file(), m)
}
func (f *fakeFirewall) Remove(z, p string, perm bool) error {
	m := readMap(f.file())
	delete(m, keyFw(z, p, perm))
	return writeMap(f.file(), m)
}

func noCommand(time.Duration, string, ...string) (string, int, error) {
	return "", -1, exec.ErrNotFound
}

func fakeEnvironment(root string) *Environment {
	return &Environment{Root: root, Run: noCommand, Famiglia: "finta",
		Gruppi: &fakeGroups{root}, Unita: &fakeUnits{root}, Firewall: &fakeFirewall{root},
		Pacchetti: &fakeManager{root}, Sessioni: &fakeSessions{root}}
}

// fakeProfile: a Debian 13 with GNOME, an Intel card that encodes.
func fakeProfile() *ProfileV {
	p := NewProfile(7447)
	p.Made = "2026-09-30T00:00:00Z"
	for k, v := range map[string]string{
		"distro.id": "debian", "distro.version": "13", "distro.family": "debian", "distro.name": "Debian GNU/Linux 13 (trixie)",
		"distro.immutable": "no", "system.arch": "x86_64", "system.systemd": "yes",
		"desktop.gnome": "48.7", "desktop.kde": "absent", "desktop.xfce": "absent", "desktop.lxqt": "absent",
		"gpu.nodes": "renderD128", "gpu.renderD128.driver": "i915", "gpu.renderD128.vendor": "Intel",
		"gpu.nvidia_proprietary": "no", "selinux": "absent", "firewall.type": "firewalld", "openssl.version": "3.5.7",
		"group.video": "gid=44", "fonts.scalable": "20",
	} {
		p.Detected(k, v, "finto")
	}
	p.Verified("h264.gpu", "yes", "finto")
	p.Sort()
	return p
}

func catalogTest(t testing.TB) *Catalog {
	c, err := ReadCatalog(catalog.Incorporato)
	if err != nil {
		t.Fatal(err)
	}
	return c
}

// prepare the fake machine: the «before» photo of every test.
func prepareMachine(t testing.TB, root string) {
	file := map[string]string{
		"etc/group":                  "root:x:0:\nvideo:x:44:altro\nrender:x:991:\nprova:x:1000:\naltro:x:1001:\n",
		"etc/passwd":                 "root:x:0:0::/root:/bin/sh\nprova:x:1000:1000::/home/prova:/bin/sh\naltro:x:1001:1001::/home/altro:/bin/sh\n",
		"etc/remotix-esistente.conf": "the administrator's old content\n",
		"etc/os-release":             "ID=debian\nVERSION_ID=\"13\"\nNAME=\"Debian GNU/Linux\"\n",
		"var/lib/finto-systemd.json": "{}",
		// one of the four rules was already there: after the cancellation it must remain
		"var/lib/finto-firewalld.json": `{"public 7447/tcp vive":true}`,
		// REMOTIX's (fake) package and the repository: libcomune is already there at an old version
		// (it will be UPGRADED: INDIRECT, it stays), libnuova and labwc are new
		"var/pacchetti/remotix.pkg":    `{"nome":"remotix","versione":"0.17.0-1","dipende":["libnuova","libcomune"]}`,
		"var/lib/finto-deposito.json":  `{"libnuova":{"versione":"1.0"},"libcomune":{"versione":"2.0"},"labwc":{"versione":"0.9","dipende":["libnuova"]}}`,
		"var/lib/finto-pacchetti.json": `{"libcomune":"1.0","bash":"5.2"}`,
		"var/lib/finto-attive.json":    "{}",
		// REMOTIX's PAM stack (certify.go follows it down to the modules)
		"etc/pam.d/remotix":            "auth required pam_unix.so\n@include common-account\n",
		"etc/pam.d/common-account":     "account required pam_unix.so\n-session optional pam_manca.so\n",
		"usr/lib/security/pam_unix.so": "",
	}
	for p, c := range file {
		d := filepath.Join(root, p)
		os.MkdirAll(filepath.Dir(d), 0o755)
		if err := os.WriteFile(d, []byte(c), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	os.Chmod(filepath.Join(root, "etc/remotix-esistente.conf"), 0o640)
	os.MkdirAll(filepath.Join(root, "etc/systemd/system"), 0o755)
}

// testActions: the steps covering the cases: packages (files and dependencies), new file in a
// new folder, file overwriting the administrator's, unit, our group, PRE-EXISTING
// group, service.
func testActions() []PlanAction {
	return []PlanAction{
		PlanPackages("packages", "/var/pacchetti/remotix.pkg", "labwc"),
		PlanWriteFile("conf-file", "/etc/remotix/engine-test.conf", "porta=7447\n", "0644"),
		PlanWriteFile("overwritten-file", "/etc/remotix-esistente.conf", "REMOTIX's content\n", "0644"),
		PlanWriteFile("unit-file", "/etc/systemd/system/remotix-engine-test.service", "[Unit]\nDescription=prova\n[Install]\nWantedBy=multi-user.target\n", "0644"),
		PlanUnit("unit", "remotix-engine-test.service"),
		PlanGroup("group-video", "prova", "video"),
		PlanGroup("group-preexisting", "altro", "video"),
		PlanStartService("service", "remotix-engine-test.service", 0),
	}
}

// testPlan writes the approved plan for the fake machine, and returns its path.
func testPlan(t testing.TB, root, dove string, approved bool) string {
	env := fakeEnvironment(root)
	cat := catalogTest(t)
	pn := &Piano{Schema: Schema, Obj: "plan", ID: "piano-prova", Made: "2026-09-30T00:00:00Z", Duty: "engine-test",
		Catalog: CatalogRef{cat.Ver, cat.Digest}, Azioni: testActions(),
		Depends: []string{}, Consents: []string{}, Condizioni: []Condition{}, NotDone: []Message{}}
	im, err := ComputeFingerprint(fakeProfile(), cat, pn.Azioni, pn.Depends, &Context{Env: env})
	if err != nil {
		t.Fatal(err)
	}
	pn.Fingerprint = *im
	if approved {
		pn.Approval = &Approval{Da: "prova", At: "2026-09-30T00:00:00Z", Modo: "da file", DigestPiano: pn.Digest()}
	}
	p := filepath.Join(dove, "plan.json")
	if err := WriteJSON(p, pn); err != nil {
		t.Fatal(err)
	}
	return p
}

func fakeEngine(t testing.TB, root, operations string) *Engine {
	return &Engine{Env: fakeEnvironment(root), Folder: operations, Catalog: catalogTest(t), Fonti: testSources(t),
		Examine: fakeProfile, Clock: func() time.Time { return time.Date(2026, 9, 30, 12, 0, 0, 0, time.UTC) }}
}

// photo: every file and folder of the fake machine, with permissions and content.
func photo(t testing.TB, root string) map[string]string {
	r := map[string]string{}
	filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			t.Fatal(err)
		}
		rel, _ := filepath.Rel(root, p)
		info, _ := d.Info()
		if d.IsDir() {
			r[rel+"/"] = info.Mode().String()
			return nil
		}
		b, _ := os.ReadFile(p)
		s := sha256.Sum256(b)
		r[rel] = info.Mode().String() + " " + hex.EncodeToString(s[:8])
		return nil
	})
	return r
}

func differences(a, b map[string]string) []string {
	var d []string
	for k, v := range a {
		if b[k] != v {
			d = append(d, fmt.Sprintf("%s: %q → %q", k, v, b[k]))
		}
	}
	for k, v := range b {
		if _, ok := a[k]; !ok {
			d = append(d, fmt.Sprintf("%s: (was not there) → %q", k, v))
		}
	}
	sort.Strings(d)
	return d
}
