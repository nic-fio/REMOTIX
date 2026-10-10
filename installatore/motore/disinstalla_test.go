package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// fakeInstall: an installation (kind «installation») on the fake machine, then two open
// sessions of the same person: a REMOTIX one and an ssh one.
func fakeInstall(t *testing.T) *bench {
	b := newBench(t)
	var p Piano
	ReadJSON(b.piano, &p)
	p.Duty, p.Approval = "installation", nil
	WriteJSON(b.piano, &p)
	op, err := b.motore(t).Apply(b.piano, true, "prova")
	if err != nil || op.State != CONFIRMED_WITH_CONDITIONS {
		t.Fatalf("installation: %v %v", op.State, err)
	}
	os.WriteFile(filepath.Join(b.root, "var/lib/finto-sessioni.json"),
		[]byte(`[{"ID":"c4","Username":"prova","Service":"remotix","State":"closing","Kind":"unspecified"},{"ID":"7","Username":"prova","Service":"sshd","State":"active","Kind":"tty"}]`), 0o644)
	os.WriteFile(filepath.Join(b.root, "var/lib/finto-grafica.json"), []byte(`{"prova":18}`), 0o644)
	// REMOTIX at the first connection enrolled «altro» in «render» (and wrote it twice)
	(&fakeGroups{b.root}).Add("other_one", "render")
	row := `{"schema":"remotix-gruppi/1","data":"2026-09-30","username":"other_one","uid":1001,"grp":"render","gid":991,"origin":"DIRECT","da":"REMOTIX alla prima connessione"}` + "\n"
	os.WriteFile(filepath.Join(filepath.Dir(b.operations), EnrollmentsFile), []byte(row+row), 0o644)
	// the session logs REMOTIX wrote in the homes (sessione.c): «prova» has only that,
	// «altro» also has a file of its own in the same folder (which must stay), root nothing
	for _, u := range []string{"prova", "other_one"} {
		d := filepath.Join(b.root, "home", u, userStateDir)
		os.MkdirAll(d, 0o700)
		os.WriteFile(filepath.Join(d, sessionFile), []byte("2026-09-30 session of "+u+"\n"), 0o600)
	}
	os.WriteFile(filepath.Join(b.root, "home/other_one", userStateDir, "appunti.txt"), []byte("mine\n"), 0o600)
	return b
}

// logsAfter: «prova»'s home without the folder, «altro»'s with only its own file.
func logsAfter(t *testing.T, root string) {
	t.Helper()
	if _, err := os.Stat(filepath.Join(root, "home/prova", userStateDir)); !os.IsNotExist(err) {
		t.Fatalf("prova's state folder is still there (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(root, "home/other_one", userStateDir, sessionFile)); !os.IsNotExist(err) {
		t.Fatalf("other_one's sessione.log is still there (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(root, "home/other_one", userStateDir, "appunti.txt")); err != nil {
		t.Fatalf("other_one's file was NOT supposed to disappear: %v", err)
	}
}

func uninstallPlan(t *testing.T, b *bench) string {
	pn, err := b.motore(t).UninstallPlan(fakeProfile(), true)
	if err != nil {
		t.Fatal(err)
	}
	if n := len(pn.Declared); n != 1 || !strings.Contains(pn.Declared[0], "/home/prova/.local/state/remotix/sessione.log, /home/other_one/.local/state/remotix/sessione.log") {
		t.Fatalf("the plan must declare the session logs with the paths: %q", pn.Declared)
	}
	if u := pn.Actions[len(pn.Actions)-1]; u.Kind != "remove-user-logs" || !strings.Contains(u.Description, "/home/other_one/") {
		t.Fatalf("the last step must remove the logs, with the paths: %+v", u)
	}
	pn.Approval = &Approval{Da: "prova", Manner: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "uninstall.json")
	WriteJSON(p, pn)
	return p
}

// ⭐ R6 and R43 in small: the uninstallation walks the log back — the machine goes back to how it was
// (except the declared INDIRECT), the REMOTIX session is closed, the ssh one stays,
// installazione.json is gone. And killed halfway it is resumed to the end.
func TestUninstall(t *testing.T) {
	points := []string{"", "dopo-intenzione@undo-service", "dopo-effetto@close-sessions",
		"dopo-intenzione@undo-packages", "file-a-meta@overwritten-file", "state:APPLIED@"}
	for _, spot := range points {
		t.Run(notEmpty(spot, "no interruption"), func(t *testing.T) {
			b := fakeInstall(t)
			pd := uninstallPlan(t, b)
			var op *Operation
			var err error
			if spot == "" {
				op, err = b.motore(t).Apply(pd, false, "prova")
			} else {
				killAt(t, b.root, b.operations, pd, "apply", spot)
				op, err = b.motore(t).Resume()
			}
			if err != nil || op.State != CONFIRMED {
				t.Fatalf("uninstallation: %v %v %s", op.State, err, op.lastDetail())
			}
			if n, _ := (&fakeSessions{b.root}).Graphical("prova"); n != 0 {
				t.Fatalf("%d desktop processes still alive", n)
			}
			logsAfter(t, b.root)
			after := picture(t, b.root)
			delete(after, "var/lib/finto-sessioni.json")
			delete(after, "var/lib/finto-grafica.json")
			for _, k := range []string{"home/", "home/other_one/", "home/other_one/.local/", "home/other_one/.local/state/", "home/other_one/.local/state/remotix/", "home/other_one/.local/state/remotix/appunti.txt", "home/prova/", "home/prova/.local/", "home/prova/.local/state/"} {
				delete(after, k) // the homes: what is not REMOTIX's stays
			}
			if d := differencesAfterUndo(t, b.before, after); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
			l, _ := (&fakeSessions{b.root}).List()
			if len(l) != 1 || l[0].Service != "sshd" {
				t.Fatalf("sessions after: %+v (expected only the ssh one)", l)
			}
			if _, err := b.motore(t).CheckInstallation(); CodeOf(err) != "RX-INST-001" {
				t.Fatalf("installazione.json is still there: %v", err)
			}
			if _, err := os.Stat(b.operations); !os.IsNotExist(err) {
				t.Fatalf("--purge: the engine's history is still there (%v)", err)
			}
		})
	}
}

// An uninstallation killed halfway and then CANCELLED goes back to the installation (the «undo» steps
// are undone by redoing), except the closed sessions: IRREVERSIBLE ⇒ PARTIALLY_ROLLED_BACK.
func TestUninstallCancelled(t *testing.T) {
	b := fakeInstall(t)
	is_installed := picture(t, b.root)
	pd := uninstallPlan(t, b)
	killAt(t, b.root, b.operations, pd, "apply", "dopo-fatta@undo-unit")
	op, err := b.motore(t).Rollback()
	if err != nil || op.State != PARTIALLY_ROLLED_BACK {
		t.Fatalf("%v %v", op.State, err)
	}
	after := picture(t, b.root)
	delete(after, "var/lib/finto-sessioni.json")
	delete(is_installed, "var/lib/finto-sessioni.json")
	delete(after, "var/lib/finto-grafica.json")
	delete(is_installed, "var/lib/finto-grafica.json")
	if d := differences(is_installed, after); len(d) > 0 {
		t.Fatalf("the installation did not come back:\n%s", strings.Join(d, "\n"))
	}
	if _, err := b.motore(t).CheckInstallation(); err != nil {
		t.Fatalf("the installation must still be on record: %v", err)
	}
}

// Without --purge the history stays (for support), but without the cached packages.
func TestUninstallWithoutPurge(t *testing.T) {
	b := fakeInstall(t)
	pn, err := b.motore(t).UninstallPlan(fakeProfile(), false)
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Manner: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(p, pn)
	op, err := b.motore(t).Apply(p, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatalf("%v %v", op.State, err)
	}
	ops, _ := filepath.Glob(filepath.Join(b.operations, "*", "log.jsonl"))
	cache, _ := filepath.Glob(filepath.Join(b.operations, "*", "cache"))
	if len(ops) != 2 || len(cache) != 0 {
		t.Fatalf("history: %d logs (expected 2), %d caches (expected 0)", len(ops), len(cache))
	}
}

// A NEW package that an UPGRADED package (which stays) requires is not removed: it is held back and
// declared (`[M]` 30 Sep, leap16-kde: Packman's upgraded libavcodec wants the new libx264, and
// `zypper rm` would have taken Plasma away). The uninstallation is confirmed all the same.
func TestUninstallKeeps(t *testing.T) {
	b := fakeInstall(t)
	// libcomune was UPGRADED by the installation (1.0 → 2.0) and 2.0 requires libnuova, NEW
	os.WriteFile(filepath.Join(b.root, "var/lib/finto-deposito.json"),
		[]byte(`{"libnuova":{"version_v":"1.0"},"libcomune":{"version_v":"2.0","depends":["libnuova"]},"labwc":{"version_v":"0.9","depends":["libnuova"]}}`), 0o644)
	pn, err := b.motore(t).UninstallPlan(fakeProfile(), false) // without purge: the certificate stays
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Manner: "da file", DigestPiano: pn.Digest()}
	pd := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(pd, pn)
	op, err := b.motore(t).Apply(pd, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatalf("uninstallation: %v %v %s", op.State, err, op.lastDetail())
	}
	in := (&fakeManager{b.root}).installed()
	if in["libnuova"] == "" || in["labwc"] != "" || in["remotix"] != "" || in["libcomune"] != "2.0" {
		t.Fatalf("packages after: %v (expected: libnuova held back, labwc and remotix removed)", in)
	}
	var c Certificate
	ReadJSON(filepath.Join(op.Folder, "certificate.json"), &c)
	if s := strings.Join(c.Indirect, "\n"); !strings.Contains(s, "RX-PACCHETTI-006") || !strings.Contains(s, "libnuova") || !strings.Contains(s, "libcomune") {
		t.Fatalf("the held-back libnuova is not declared in the certificate: %q", s)
	}
}
