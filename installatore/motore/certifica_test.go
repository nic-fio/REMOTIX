package engine

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// R29 in small: certification on a machine broken on purpose never says GREEN.
func TestCertifyFaults(t *testing.T) {
	encode := func(json string, output int) Executor {
		return func(_ time.Duration, name string, _ ...string) (string, int, error) {
			if name == "remotix" {
				return json, output, nil
			}
			return noCommand(0, name)
		}
	}
	good_one := encode(`{"outcome":"hardware","encoder":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":""}`, 0)
	do_open := func(b *bench) { (&fakeFirewall{b.root}).Insert("public", "7447/udp", false) }
	cases := []struct {
		name   string
		broken func(b *bench, m *Engine)
		expected string
	}{
		{"healthy, card that encodes", func(b *bench, m *Engine) { m.Env.Run = good_one; do_open(b) }, "GREEN"},
		// phase 19: the Vulkan Video route (AMD, NVIDIA) is «hardware» like VA-API
		{"healthy, card that encodes in Vulkan", func(b *bench, m *Engine) {
			m.Env.Run = encode(`{"outcome":"hardware","encoder":"h264_vulkan","strada":"vulkan","nodo":"/dev/dri/renderD129","motivo":"","codec":"h264","offerti":"hevc,h264","hevc":"hardware","h264":"hardware","hevc_strada":"vulkan","h264_strada":"vulkan"}`, 0)
			do_open(b)
		}, "GREEN"},
		{"card that opens but does not encode the frame", func(b *bench, m *Engine) {
			m.Env.Run = encode(`{"outcome":"nessuno","encoder":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":"the frame does not come out","codec":"h264","offerti":"","hevc":"nessuno","h264":"nessuno"}`, 1)
			do_open(b)
		}, "RED"},
		// phase 19: no fallback to the processor — no capable card (exit 3) is RED, never conditional
		{"no card can encode (exit 3)", func(b *bench, m *Engine) {
			m.Env.Run = encode(`{"outcome":"nessuno","encoder":"","nodo":"","motivo":"no render node","codec":"h264","offerti":"","hevc":"nessuno","h264":"nessuno"}`, 3)
			do_open(b)
		}, "RED"},
		// an old binary that still says «software»: it is not the card ⇒ RED
		{"the old software fallback", func(b *bench, m *Engine) {
			m.Env.Run = encode(`{"outcome":"software","encoder":"libx264","nodo":"","motivo":"no VA-API"}`, 0)
			do_open(b)
		}, "RED"},
		{"encoding test that does not answer", func(b *bench, m *Engine) { do_open(b) }, "CONDITIONAL"},
		{"PAM broken (module removed)", func(b *bench, m *Engine) {
			m.Env.Run = good_one
			do_open(b)
			os.Remove(filepath.Join(b.root, "usr/lib/security/pam_unix.so"))
		}, "RED"},
		{"PAM broken (include removed)", func(b *bench, m *Engine) {
			m.Env.Run = good_one
			do_open(b)
			os.Remove(filepath.Join(b.root, "etc/pam.d/common-account"))
		}, "RED"},
		{"PAM removed", func(b *bench, m *Engine) {
			m.Env.Run = good_one
			do_open(b)
			os.Remove(filepath.Join(b.root, "etc/pam.d/remotix"))
		}, "RED"},
		{"port closed by the firewall: opening it is the administrator's job (§10.36)", func(b *bench, m *Engine) {
			m.Env.Run = good_one
			f := &fakeFirewall{b.root}
			f.Remove("public", "7447/tcp", false)
			f.Remove("public", "7447/udp", false)
		}, "CONDITIONAL"},
		{"firewall that cannot be read (ufw)", func(b *bench, m *Engine) {
			m.Env.Run = good_one
			os.WriteFile(filepath.Join(b.root, "etc/finto-firewall"), []byte("ufw"), 0o644)
		}, "CONDITIONAL"},
		{"a step undone by others", func(b *bench, m *Engine) {
			m.Env.Run = good_one
			do_open(b)
			os.Remove(filepath.Join(b.root, "etc/remotix/engine-test.conf"))
		}, "RED"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			b := fakeInstall(t)
			m := b.engine(t)
			c.broken(b, m)
			r, err := m.Certify()
			if err != nil {
				t.Fatal(err)
			}
			if r.Outcome != c.expected {
				t.Fatalf("outcome %s, expected %s: %+v %+v", r.Outcome, c.expected, r.Verifications, r.Condizioni)
			}
		})
	}
}

// R29 in the installation too: with the card that does not encode (phase 19: and there is no fallback) the
// verification is red and the installation is cancelled.
func TestInstallBrokenCard(t *testing.T) {
	b := newBench(t)
	var p Piano
	ReadJSON(b.piano, &p)
	p.Duty, p.Approval = "installation", nil
	WriteJSON(b.piano, &p)
	m := b.engine(t)
	m.Env.Run = func(_ time.Duration, name string, _ ...string) (string, int, error) {
		if name == "remotix" {
			return `{"outcome":"nessuno","encoder":"","nodo":"","motivo":"no render node"}`, 3, nil
		}
		return noCommand(0, name)
	}
	op, err := m.Apply(b.piano, true, "prova")
	if err != nil || op.State != ROLLED_BACK {
		t.Fatalf("%v %v", op.State, err)
	}
}

// The port closed by the firewall (opening it is the administrator's job, §10.36): never PASS, and a condition
// that says so, without commands.
func TestClosedPort(t *testing.T) {
	b := newBench(t)
	k, c := checkPort(fakeEnvironment(b.root), 7447)
	if k.Outcome != "FAIL" || k.Requested || c == nil || c.Codice != "C-AMMINISTRATORE" || c.Testo == "" {
		t.Fatalf("%+v %+v", k, c)
	}
}

// D14 (DECISIONI §10.23): REMOTIX and the dependencies are upgraded with the system. After an upgrade
// (versions newer than those installed then) the certification stays green; a rollback
// done with the manager's commands is «half-done» until `remotix-install post-upgrade` records the versions.
func TestCertifyAfterUpdate(t *testing.T) {
	b := fakeInstall(t)
	m := b.engine(t)
	m.Env.Run = func(_ time.Duration, name string, _ ...string) (string, int, error) {
		if name == "remotix" {
			return `{"outcome":"hardware","encoder":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":""}`, 0, nil
		}
		return noCommand(0, name)
	}
	(&fakeFirewall{b.root}).Insert("public", "7447/udp", false)
	pk := filepath.Join(b.root, "var/lib/finto-pacchetti.json")
	in := map[string]string{}
	readJSONFake(pk, &in)
	outcome := func(what string, v map[string]string) string {
		t.Helper()
		x := map[string]string{}
		for k, y := range in {
			x[k] = y
		}
		for k, y := range v {
			x[k] = y
		}
		WriteJSON(pk, x)
		r, err := m.Certify()
		if err != nil {
			t.Fatal(what, err)
		}
		return r.Outcome
	}
	if e := outcome("upgraded by the system", map[string]string{"remotix": "0.17.0-2", "libcomune": "2.1"}); e != "GREEN" {
		t.Fatalf("after the system upgrade: %s", e)
	}
	if e := outcome("rolled back, not recorded", map[string]string{"remotix": "0.16.0-1"}); e != "RED" {
		t.Fatalf("a rollback not recorded: %s", e)
	}
	if v, err := m.AnnotateVersions(); err != nil || v["remotix"] != "0.16.0-1" {
		t.Fatalf("record: %v %v", v, err)
	}
	if e := outcome("rolled back, recorded", map[string]string{"remotix": "0.16.0-1"}); e != "GREEN" {
		t.Fatalf("a rollback recorded by «aggiornato»: %s", e)
	}
}
