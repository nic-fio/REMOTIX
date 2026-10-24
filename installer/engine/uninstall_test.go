package engine

import (
	"encoding/json"
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
	op, err := b.engine(t).Apply(b.piano, true, "prova")
	if err != nil || op.State != CONFIRMED_WITH_CONDITIONS {
		t.Fatalf("installation: %v %v", op.State, err)
	}
	os.WriteFile(filepath.Join(b.root, "var/lib/finto-sessioni.json"),
		[]byte(`[{"ID":"c4","User":"prova","Service":"remotix","State":"closing","Type":"unspecified"},{"ID":"7","User":"prova","Service":"sshd","State":"active","Type":"tty"}]`), 0o644)
	os.WriteFile(filepath.Join(b.root, "var/lib/finto-grafica.json"), []byte(`{"prova":18}`), 0o644)
	// REMOTIX at the first connection enrolled «other» in «render» (and wrote it twice)
	(&fakeGroups{b.root}).Insert("altro", "render")
	line := `{"format":"remotix-enrollments/1","time":"2026-09-30","user":"altro","uid":1001,"group":"render","gid":991,"origin":"DIRECT","by":"REMOTIX at first connection"}` + "\n"
	os.WriteFile(filepath.Join(filepath.Dir(b.operations), EnrollmentsFile), []byte(line+line), 0o644)
	// the session logs REMOTIX wrote in the homes (session.c): «prova» has only that,
	// «other» also has a file of its own in the same folder (which must stay), root nothing
	for _, u := range []string{"prova", "altro"} {
		d := filepath.Join(b.root, "home", u, userStateDir)
		os.MkdirAll(d, 0o700)
		os.WriteFile(filepath.Join(d, sessionFile), []byte("2026-09-30 session of "+u+"\n"), 0o600)
	}
	os.WriteFile(filepath.Join(b.root, "home/altro", userStateDir, "appunti.txt"), []byte("mine\n"), 0o600)
	return b
}

// logsAfter: «prova»'s home without the folder, «other»'s with only its own file.
func logsAfter(t *testing.T, root string) {
	t.Helper()
	if _, err := os.Stat(filepath.Join(root, "home/prova", userStateDir)); !os.IsNotExist(err) {
		t.Fatalf("prova's state folder is still there (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(root, "home/altro", userStateDir, sessionFile)); !os.IsNotExist(err) {
		t.Fatalf("altro's session.log is still there (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(root, "home/altro", userStateDir, "appunti.txt")); err != nil {
		t.Fatalf("altro's file was NOT supposed to disappear: %v", err)
	}
}

func uninstallPlan(t *testing.T, b *bench) string {
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), true)
	if err != nil {
		t.Fatal(err)
	}
	if n := len(pn.Declared); n != 1 || !strings.Contains(pn.Declared[0], "/home/prova/.local/state/remotix/session.log, /home/altro/.local/state/remotix/session.log") {
		t.Fatalf("the plan must declare the session logs with the paths: %q", pn.Declared)
	}
	if u := pn.Azioni[len(pn.Azioni)-1]; u.Type != "remove-user-logs" || !strings.Contains(u.Description, "/home/altro/") {
		t.Fatalf("the last step must remove the logs, with the paths: %+v", u)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "uninstall.json")
	WriteJSON(p, pn)
	return p
}

// ⭐ R6 and R43 in small: the uninstallation walks the log back — the machine goes back to how it was
// (except the declared INDIRECT), the REMOTIX session is closed, the ssh one stays,
// installation.json is gone. And killed halfway it is resumed to the end.
func TestUninstall(t *testing.T) {
	points := []string{"", "dopo-intenzione@undo-service", "dopo-effetto@close-sessions",
		"dopo-intenzione@undo-packages", "file-a-meta@overwritten-file", "stato:APPLIED@"}
	for _, spot := range points {
		t.Run(notEmpty(spot, "no interruption"), func(t *testing.T) {
			b := fakeInstall(t)
			pd := uninstallPlan(t, b)
			var op *Operation
			var err error
			if spot == "" {
				op, err = b.engine(t).Apply(pd, false, "prova")
			} else {
				killAt(t, b.root, b.operations, pd, "applica", spot)
				op, err = b.engine(t).Resume()
			}
			if err != nil || op.State != CONFIRMED {
				t.Fatalf("uninstallation: %v %v %s", op.State, err, op.lastDetail())
			}
			if n, _ := (&fakeSessions{b.root}).Charts("prova"); n != 0 {
				t.Fatalf("%d desktop processes still alive", n)
			}
			logsAfter(t, b.root)
			after := photo(t, b.root)
			delete(after, "var/lib/finto-sessioni.json")
			delete(after, "var/lib/finto-grafica.json")
			for _, k := range []string{"home/", "home/altro/", "home/altro/.local/", "home/altro/.local/state/", "home/altro/.local/state/remotix/", "home/altro/.local/state/remotix/appunti.txt", "home/prova/", "home/prova/.local/", "home/prova/.local/state/"} {
				delete(after, k) // the homes: what is not REMOTIX's stays
			}
			if d := differencesAfterUndo(t, b.before, after); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
			l, _ := (&fakeSessions{b.root}).Listing()
			if len(l) != 1 || l[0].Service != "sshd" {
				t.Fatalf("sessions after: %+v (expected only the ssh one)", l)
			}
			if _, err := b.engine(t).CheckInstallation(); CodeOf(err) != "RX-INST-001" {
				t.Fatalf("installation.json is still there: %v", err)
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
	is_installed := photo(t, b.root)
	pd := uninstallPlan(t, b)
	killAt(t, b.root, b.operations, pd, "applica", "dopo-fatta@undo-unit")
	op, err := b.engine(t).Rollback()
	if err != nil || op.State != PARTIALLY_ROLLED_BACK {
		t.Fatalf("%v %v", op.State, err)
	}
	after := photo(t, b.root)
	delete(after, "var/lib/finto-sessioni.json")
	delete(is_installed, "var/lib/finto-sessioni.json")
	delete(after, "var/lib/finto-grafica.json")
	delete(is_installed, "var/lib/finto-grafica.json")
	if d := differences(is_installed, after); len(d) > 0 {
		t.Fatalf("the installation did not come back:\n%s", strings.Join(d, "\n"))
	}
	if _, err := b.engine(t).CheckInstallation(); err != nil {
		t.Fatalf("the installation must still be on record: %v", err)
	}
}

// Without --purge the history stays (for support), but without the cached packages.
func TestUninstallWithoutPurge(t *testing.T) {
	b := fakeInstall(t)
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), false)
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(p, pn)
	op, err := b.engine(t).Apply(p, false, "prova")
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
		[]byte(`{"libnuova":{"versione":"1.0"},"libcomune":{"versione":"2.0","dipende":["libnuova"]},"labwc":{"versione":"0.9","dipende":["libnuova"]}}`), 0o644)
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), false) // without purge: the certificate stays
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	pd := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(pd, pn)
	op, err := b.engine(t).Apply(pd, false, "prova")
	if err != nil || op.State != CONFIRMED {
		t.Fatalf("uninstallation: %v %v %s", op.State, err, op.lastDetail())
	}
	in := (&fakeManager{b.root}).installs()
	if in["libnuova"] == "" || in["labwc"] != "" || in["remotix"] != "" || in["libcomune"] != "2.0" {
		t.Fatalf("packages after: %v (expected: libnuova held back, labwc and remotix removed)", in)
	}
	var c Certificate
	ReadJSON(filepath.Join(op.Folder, "certificate.json"), &c)
	if s := strings.Join(c.Indirect, "\n"); !strings.Contains(s, "RX-PACCHETTI-006") || !strings.Contains(s, "libnuova") || !strings.Contains(s, "libcomune") {
		t.Fatalf("the held-back libnuova is not declared in the certificate: %q", s)
	}
}

// fakeUpgrade: a confirmed upgrade, later than the installation, whose plan carries one step that
// adds «user» to «group» (origin DIRECT in its log). With no log file when `withLog` is false.
func fakeUpgrade(t *testing.T, b *bench, id, user, group string, withLog bool) {
	t.Helper()
	d := filepath.Join(b.operations, id)
	if err := os.MkdirAll(d, 0o755); err != nil {
		t.Fatal(err)
	}
	step := PlanGroup("group-"+user+"-"+group, user, group)
	WriteJSON(filepath.Join(d, "plan.json"), &Piano{Schema: Schema, Obj: "plan", ID: id, Duty: "upgrade", Azioni: []PlanAction{step}})
	os.WriteFile(filepath.Join(d, "state"), []byte(string(CONFIRMED)+"\n"), 0o600)
	if withLog {
		line, _ := json.Marshal(Event{N: 1, Type: EvIntent, Action: step.ID, Origine: DIRECT})
		os.WriteFile(filepath.Join(d, "log.jsonl"), append(line, '\n'), 0o600)
	}
}

func countSteps(pn *Piano, id string) int {
	n := 0
	for _, a := range pn.Azioni {
		if a.ID == id {
			n++
		}
	}
	return n
}

// An installation plus an upgrade that added a group: the group is undone ONCE (by the upgrade's
// own step), even if the enrolment file of REMOTIX lists the same pair.
func TestUninstallUpgradeGroupOnce(t *testing.T) {
	b := fakeInstall(t)
	up := "99991231T235959Z-00000000"
	fakeUpgrade(t, b, up, "nuovo", "render", true)
	line := `{"format":"remotix-enrollments/1","time":"2026-10-01","user":"nuovo","uid":1002,"group":"render","gid":991,"origin":"DIRECT","by":"REMOTIX at first connection"}` + "\n"
	f := filepath.Join(filepath.Dir(b.operations), EnrollmentsFile)
	old, _ := os.ReadFile(f)
	os.WriteFile(f, append(old, []byte(line)...), 0o644)
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), true)
	if err != nil {
		t.Fatal(err)
	}
	if n := countSteps(pn, "undo-"+up+"-group-nuovo-render"); n != 1 {
		t.Fatalf("the upgrade's group step must appear once, found %d", n)
	}
	if n := countSteps(pn, "membership-nuovo-render"); n != 0 {
		t.Fatalf("the same group must not be removed a second time as a membership (%d)", n)
	}
	if n := countSteps(pn, "membership-altro-render"); n != 1 {
		t.Fatalf("the unrelated enrolment must stay (%d)", n)
	}
}

// An upgrade whose log cannot be read is DECLARED in the plan, not silently skipped.
func TestUninstallUpgradeLogUnreadable(t *testing.T) {
	b := fakeInstall(t)
	up := "99991231T235959Z-00000000"
	fakeUpgrade(t, b, up, "nuovo", "render", false)
	pn, err := b.engine(t).UninstallPlan(fakeProfile(), true)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, d := range pn.Declared {
		if strings.Contains(d, up) && strings.Contains(d, "NOT in this plan") {
			found = true
		}
	}
	if !found {
		t.Fatalf("the unreadable log of the upgrade must be declared: %q", pn.Declared)
	}
	if n := countSteps(pn, "undo-"+up+"-group-nuovo-render"); n != 0 {
		t.Fatalf("nothing can be undone from a log that is not there (%d)", n)
	}
}
