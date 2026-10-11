package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// fakeInstall: an installation (kind «installation») on the fake machine, then two open
// sessions of the same person: a REMOTIX one and an ssh one.
func fakeInstall(t *testing.T) *banco {
	b := newBench(t)
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Duty, p.Approval = "installation", nil
	WriteJSON(b.piano, &p)
	op, err := b.motore(t).Applica(b.piano, true, "prova")
	if err != nil || op.Stato != CONFERMATA_A_CONDIZIONI {
		t.Fatalf("installation: %v %v", op.Stato, err)
	}
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-sessioni.json"),
		[]byte(`[{"ID":"c4","Utente":"prova","Servizio":"remotix","Stato":"closing","Tipo":"unspecified"},{"ID":"7","Utente":"prova","Servizio":"sshd","Stato":"active","Tipo":"tty"}]`), 0o644)
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-grafica.json"), []byte(`{"prova":18}`), 0o644)
	// REMOTIX at the first connection enrolled «altro» in «render» (and wrote it twice)
	(&fakeGroups{b.radice}).Add("altro", "render")
	riga := `{"formato":"remotix-gruppi/1","data":"2026-09-30","utente":"altro","uid":1001,"gruppo":"render","gid":991,"origine":"DIRETTA","da":"REMOTIX alla prima connessione"}` + "\n"
	os.WriteFile(filepath.Join(filepath.Dir(b.operazioni), EnrollmentsFile), []byte(riga+riga), 0o644)
	// the session logs REMOTIX wrote in the homes (sessione.c): «prova» has only that,
	// «altro» also has a file of its own in the same folder (which must stay), root nothing
	for _, u := range []string{"prova", "altro"} {
		d := filepath.Join(b.radice, "home", u, userStateDir)
		os.MkdirAll(d, 0o700)
		os.WriteFile(filepath.Join(d, sessionFile), []byte("2026-09-30 session of "+u+"\n"), 0o600)
	}
	os.WriteFile(filepath.Join(b.radice, "home/altro", userStateDir, "appunti.txt"), []byte("mine\n"), 0o600)
	return b
}

// logsAfter: «prova»'s home without the folder, «altro»'s with only its own file.
func logsAfter(t *testing.T, radice string) {
	t.Helper()
	if _, err := os.Stat(filepath.Join(radice, "home/prova", userStateDir)); !os.IsNotExist(err) {
		t.Fatalf("prova's state folder is still there (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(radice, "home/altro", userStateDir, sessionFile)); !os.IsNotExist(err) {
		t.Fatalf("altro's sessione.log is still there (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(radice, "home/altro", userStateDir, "appunti.txt")); err != nil {
		t.Fatalf("altro's file was NOT supposed to disappear: %v", err)
	}
}

func uninstallPlan(t *testing.T, b *banco) string {
	pn, err := b.motore(t).PianoDisinstallazione(fakeProfile(), true)
	if err != nil {
		t.Fatal(err)
	}
	if n := len(pn.Dichiarate); n != 1 || !strings.Contains(pn.Dichiarate[0], "/home/prova/.local/state/remotix/sessione.log, /home/altro/.local/state/remotix/sessione.log") {
		t.Fatalf("the plan must declare the session logs with the paths: %q", pn.Dichiarate)
	}
	if u := pn.Azioni[len(pn.Azioni)-1]; u.Tipo != "remove-user-logs" || !strings.Contains(u.Description, "/home/altro/") {
		t.Fatalf("the last step must remove the logs, with the paths: %+v", u)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "uninstall.json")
	WriteJSON(p, pn)
	return p
}

// ⭐ R6 and R43 in small: the uninstallation walks the log back — the machine goes back to how it was
// (except the declared INDIRETTA), the REMOTIX session is closed, the ssh one stays,
// installazione.json is gone. And killed halfway it is resumed to the end.
func TestUninstall(t *testing.T) {
	punti := []string{"", "dopo-intenzione@undo-service", "dopo-effetto@close-sessions",
		"dopo-intenzione@undo-packages", "file-a-meta@overwritten-file", "stato:APPLIED@"}
	for _, punto := range punti {
		t.Run(notEmpty(punto, "no interruption"), func(t *testing.T) {
			b := fakeInstall(t)
			pd := uninstallPlan(t, b)
			var op *Operation
			var err error
			if punto == "" {
				op, err = b.motore(t).Applica(pd, false, "prova")
			} else {
				killAt(t, b.radice, b.operazioni, pd, "applica", punto)
				op, err = b.motore(t).Riprendi()
			}
			if err != nil || op.Stato != CONFERMATA {
				t.Fatalf("uninstallation: %v %v %s", op.Stato, err, op.lastDetail())
			}
			if n, _ := (&fakeSessions{b.radice}).Graphical("prova"); n != 0 {
				t.Fatalf("%d desktop processes still alive", n)
			}
			logsAfter(t, b.radice)
			dopo := foto(t, b.radice)
			delete(dopo, "var/lib/finto-sessioni.json")
			delete(dopo, "var/lib/finto-grafica.json")
			for _, k := range []string{"home/", "home/altro/", "home/altro/.local/", "home/altro/.local/state/", "home/altro/.local/state/remotix/", "home/altro/.local/state/remotix/appunti.txt", "home/prova/", "home/prova/.local/", "home/prova/.local/state/"} {
				delete(dopo, k) // the homes: what is not REMOTIX's stays
			}
			if d := differencesAfterUndo(t, b.prima, dopo); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
			l, _ := (&fakeSessions{b.radice}).List()
			if len(l) != 1 || l[0].Servizio != "sshd" {
				t.Fatalf("sessions after: %+v (expected only the ssh one)", l)
			}
			if _, err := b.motore(t).CheckInstallation(); CodeOf(err) != "RX-INST-001" {
				t.Fatalf("installazione.json is still there: %v", err)
			}
			if _, err := os.Stat(b.operazioni); !os.IsNotExist(err) {
				t.Fatalf("--purge: the engine's history is still there (%v)", err)
			}
		})
	}
}

// An uninstallation killed halfway and then CANCELLED goes back to the installation (the «undo» steps
// are undone by redoing), except the closed sessions: IRREVERSIBLE ⇒ ANNULLATA_IN_PARTE.
func TestUninstallCancelled(t *testing.T) {
	b := fakeInstall(t)
	installata := foto(t, b.radice)
	pd := uninstallPlan(t, b)
	killAt(t, b.radice, b.operazioni, pd, "applica", "dopo-fatta@undo-unit")
	op, err := b.motore(t).Annulla()
	if err != nil || op.Stato != ANNULLATA_IN_PARTE {
		t.Fatalf("%v %v", op.Stato, err)
	}
	dopo := foto(t, b.radice)
	delete(dopo, "var/lib/finto-sessioni.json")
	delete(installata, "var/lib/finto-sessioni.json")
	delete(dopo, "var/lib/finto-grafica.json")
	delete(installata, "var/lib/finto-grafica.json")
	if d := differenze(installata, dopo); len(d) > 0 {
		t.Fatalf("the installation did not come back:\n%s", strings.Join(d, "\n"))
	}
	if _, err := b.motore(t).CheckInstallation(); err != nil {
		t.Fatalf("the installation must still be on record: %v", err)
	}
}

// Without --purge the history stays (for support), but without the cached packages.
func TestUninstallWithoutPurge(t *testing.T) {
	b := fakeInstall(t)
	pn, err := b.motore(t).PianoDisinstallazione(fakeProfile(), false)
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(p, pn)
	op, err := b.motore(t).Applica(p, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("%v %v", op.Stato, err)
	}
	ops, _ := filepath.Glob(filepath.Join(b.operazioni, "*", "log.jsonl"))
	cache, _ := filepath.Glob(filepath.Join(b.operazioni, "*", "cache"))
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
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-deposito.json"),
		[]byte(`{"libnuova":{"versione":"1.0"},"libcomune":{"versione":"2.0","dipende":["libnuova"]},"labwc":{"versione":"0.9","dipende":["libnuova"]}}`), 0o644)
	pn, err := b.motore(t).PianoDisinstallazione(fakeProfile(), false) // without purge: the certificate stays
	if err != nil {
		t.Fatal(err)
	}
	pn.Approval = &Approval{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	pd := filepath.Join(t.TempDir(), "d.json")
	WriteJSON(pd, pn)
	op, err := b.motore(t).Applica(pd, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("uninstallation: %v %v %s", op.Stato, err, op.lastDetail())
	}
	in := (&fakeManager{b.radice}).installati()
	if in["libnuova"] == "" || in["labwc"] != "" || in["remotix"] != "" || in["libcomune"] != "2.0" {
		t.Fatalf("packages after: %v (expected: libnuova held back, labwc and remotix removed)", in)
	}
	var c Certificate
	LeggiJSON(filepath.Join(op.Cartella, "certificate.json"), &c)
	if s := strings.Join(c.Indirect, "\n"); !strings.Contains(s, "RX-PACCHETTI-006") || !strings.Contains(s, "libnuova") || !strings.Contains(s, "libcomune") {
		t.Fatalf("the held-back libnuova is not declared in the certificate: %q", s)
	}
}
