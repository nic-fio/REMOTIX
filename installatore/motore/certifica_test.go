package motore

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// R29 in small: certification on a machine broken on purpose never says GREEN.
func TestCertifyFaults(t *testing.T) {
	encoding := func(json string, out_dir int) Executor {
		return func(_ time.Duration, label_name string, _ ...string) (string, int, error) {
			if label_name == "remotix" {
				return json, out_dir, nil
			}
			return noCommand(0, label_name)
		}
	}
	good_one := encoding(`{"outcome":"hardware","encoder":"h264_vaapi","node":"/dev/dri/renderD128","motivo":""}`, 0)
	open_it := func(b *bench) { (&fakeFirewall{b.root}).Add("public", "7447/udp", false) }
	cases := []struct {
		label_name   string
		broken       func(b *bench, m *Engine)
		expected_val string
	}{
		{"healthy, card that encodes", func(b *bench, m *Engine) { m.Amb.Run = good_one; open_it(b) }, "GREEN"},
		// phase 19: the Vulkan Video route (AMD, NVIDIA) is «hardware» like VA-API
		{"healthy, card that encodes in Vulkan", func(b *bench, m *Engine) {
			m.Amb.Run = encoding(`{"outcome":"hardware","encoder":"h264_vulkan","route":"vulkan","node":"/dev/dri/renderD129","motivo":"","codec":"h264","offered":"hevc,h264","hevc":"hardware","h264":"hardware","hevc_route":"vulkan","h264_route":"vulkan"}`, 0)
			open_it(b)
		}, "GREEN"},
		{"card that opens but does not encode the frame", func(b *bench, m *Engine) {
			m.Amb.Run = encoding(`{"outcome":"nobody","encoder":"h264_vaapi","node":"/dev/dri/renderD128","motivo":"the frame does not come out","codec":"h264","offered":"","hevc":"nobody","h264":"nobody"}`, 1)
			open_it(b)
		}, "RED"},
		// phase 19: no fallback to the processor — no capable card (exit 3) is RED, never conditional
		{"no card can encode (exit 3)", func(b *bench, m *Engine) {
			m.Amb.Run = encoding(`{"outcome":"nobody","encoder":"","node":"","motivo":"no render node","codec":"h264","offered":"","hevc":"nobody","h264":"nobody"}`, 3)
			open_it(b)
		}, "RED"},
		// an old binary that still says «software»: it is not the card ⇒ RED
		{"the old software fallback", func(b *bench, m *Engine) {
			m.Amb.Run = encoding(`{"outcome":"software","encoder":"libx264","node":"","motivo":"no VA-API"}`, 0)
			open_it(b)
		}, "RED"},
		{"encoding test that does not answer", func(b *bench, m *Engine) { open_it(b) }, "CONDITIONAL"},
		{"PAM broken (module removed)", func(b *bench, m *Engine) {
			m.Amb.Run = good_one
			open_it(b)
			os.Remove(filepath.Join(b.root, "usr/lib/security/pam_unix.so"))
		}, "RED"},
		{"PAM broken (include removed)", func(b *bench, m *Engine) {
			m.Amb.Run = good_one
			open_it(b)
			os.Remove(filepath.Join(b.root, "etc/pam.d/common-account"))
		}, "RED"},
		{"PAM removed", func(b *bench, m *Engine) {
			m.Amb.Run = good_one
			open_it(b)
			os.Remove(filepath.Join(b.root, "etc/pam.d/remotix"))
		}, "RED"},
		{"port closed by the firewall: opening it is the administrator's job (§10.36)", func(b *bench, m *Engine) {
			m.Amb.Run = good_one
			f := &fakeFirewall{b.root}
			f.Revoke("public", "7447/tcp", false)
			f.Revoke("public", "7447/udp", false)
		}, "CONDITIONAL"},
		{"firewall that cannot be read (ufw)", func(b *bench, m *Engine) {
			m.Amb.Run = good_one
			os.WriteFile(filepath.Join(b.root, "etc/finto-firewall"), []byte("ufw"), 0o644)
		}, "CONDITIONAL"},
		{"a step undone by others", func(b *bench, m *Engine) {
			m.Amb.Run = good_one
			open_it(b)
			os.Remove(filepath.Join(b.root, "etc/remotix/engine-test.conf"))
		}, "RED"},
	}
	for _, c := range cases {
		t.Run(c.label_name, func(t *testing.T) {
			b := fakeInstall(t)
			m := b.motore(t)
			c.broken(b, m)
			r, err := m.Certify()
			if err != nil {
				t.Fatal(err)
			}
			if r.Outcome != c.expected_val {
				t.Fatalf("outcome %s, expected %s: %+v %+v", r.Outcome, c.expected_val, r.Checks, r.Conditions)
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
	m := b.motore(t)
	m.Amb.Run = func(_ time.Duration, label_name string, _ ...string) (string, int, error) {
		if label_name == "remotix" {
			return `{"outcome":"nobody","encoder":"","node":"","motivo":"no render node"}`, 3, nil
		}
		return noCommand(0, label_name)
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
	if k.Outcome != "FAIL" || k.Requested || c == nil || c.Code != "C-AMMINISTRATORE" || c.Text == "" {
		t.Fatalf("%+v %+v", k, c)
	}
}

// D14 (DECISIONI §10.23): REMOTIX and the dependencies are upgraded with the system. After an upgrade
// (versions newer than those installed then) the certification stays green; a rollback
// done with the manager's commands is «half-done» until `remotix-install updated` records the versions.
func TestCertifyAfterUpdate(t *testing.T) {
	b := fakeInstall(t)
	m := b.motore(t)
	m.Amb.Run = func(_ time.Duration, label_name string, _ ...string) (string, int, error) {
		if label_name == "remotix" {
			return `{"outcome":"hardware","encoder":"h264_vaapi","node":"/dev/dri/renderD128","motivo":""}`, 0, nil
		}
		return noCommand(0, label_name)
	}
	(&fakeFirewall{b.root}).Add("public", "7447/udp", false)
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
		t.Fatalf("a rollback recorded by «updated»: %s", e)
	}
}
