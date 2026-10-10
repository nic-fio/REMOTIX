package motore

// R30 in small: the engine process really KILLED (SIGKILL, no defer, no cleanup)
// at every point of the table of §6.6.3 and at every state transition; then a new engine
// resumes and must reach CONFERMATA (or ANNULLATA, if cancelling) with the machine IDENTICAL to
// that of a run without interruptions (or to the one before). The killed process is this same
// test binary, relaunched with REMOTIX_PROVA_FIGLIO=1: the PuntoDiProva hook exists only
// in the tests.

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

func TestMain(m *testing.M) {
	if os.Getenv("REMOTIX_PROVA_FIGLIO") == "1" {
		figlio()
		return
	}
	os.Exit(m.Run())
}

// figlio: the engine that will be killed. It exits 3 if the point was never reached.
func figlio() {
	radice, operazioni := os.Getenv("RADICE"), os.Getenv("OPERAZIONI")
	bersaglio := os.Getenv("PUNTO")
	PuntoDiProva = func(p, a string) {
		if p+"@"+a == bersaglio {
			syscall.Kill(os.Getpid(), syscall.SIGKILL)
			select {}
		}
	}
	m := motoreFinto(&testing.T{}, radice, operazioni)
	if os.Getenv("FIREWALL") != "" {
		os.WriteFile(filepath.Join(radice, "etc/finto-firewall"), []byte(os.Getenv("FIREWALL")), 0o644)
	}
	var err error
	switch os.Getenv("COMANDO") {
	case "applica":
		_, err = m.Applica(os.Getenv("PIANO"), false, "prova")
	case "riprendi":
		_, err = m.Riprendi()
	case "annulla":
		_, err = m.Annulla()
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "figlio:", err)
	}
	os.Exit(3)
}

// uccidiIn launches the child and checks it died of SIGKILL at the requested point.
func uccidiIn(t *testing.T, radice, operazioni, piano, comando, punto string) {
	t.Helper()
	cmd := exec.Command(os.Args[0], "-test.run=^$")
	cmd.Env = append(os.Environ(), "REMOTIX_PROVA_FIGLIO=1", "RADICE="+radice, "OPERAZIONI="+operazioni,
		"PIANO="+piano, "COMANDO="+comando, "PUNTO="+punto)
	var errOut bytes.Buffer
	cmd.Stderr = &errOut
	err := cmd.Run()
	var ee *exec.ExitError
	if !errors.As(err, &ee) {
		t.Fatalf("%s %s: the child did not die (err=%v) %s", comando, punto, err, errOut.String())
	}
	if ws, ok := ee.Sys().(syscall.WaitStatus); !ok || !ws.Signaled() || ws.Signal() != syscall.SIGKILL {
		t.Fatalf("%s %s: the point was not reached (exit %v): %s", comando, punto, err, errOut.String())
	}
}

type banco struct {
	radice, operazioni, piano string
	prima                     map[string]string
}

func nuovoBanco(t *testing.T) *banco {
	d := t.TempDir()
	b := &banco{radice: filepath.Join(d, "macchina"), operazioni: filepath.Join(d, "operations")}
	os.MkdirAll(b.radice, 0o755)
	preparaMacchina(t, b.radice)
	b.piano = pianoDiProva(t, b.radice, d, true)
	b.prima = foto(t, b.radice)
	return b
}

func (b *banco) motore(t *testing.T) *Motore { return motoreFinto(t, b.radice, b.operazioni) }

// riferimento: the machine after a whole run without interruptions.
var riferimento map[string]string

func fotoRiferimento(t *testing.T) map[string]string {
	if riferimento != nil {
		return riferimento
	}
	b := nuovoBanco(t)
	op, err := b.motore(t).Applica(b.piano, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("run without interruptions: %v, state %v", err, op.Stato)
	}
	riferimento = foto(t, b.radice)
	return riferimento
}

// controllaRegistro: no action DONE twice, no duplicate INTENTION (double effect).
func controllaRegistro(t *testing.T, op *Operazione) {
	t.Helper()
	if err := op.apriRegistro(); err != nil {
		t.Fatal(err)
	}
	n := map[string]int{}
	for _, e := range op.Reg.Eventi {
		if e.Tipo == EvFatta || e.Tipo == EvIntenzione {
			n[string(e.Tipo)+" "+e.Azione]++
		}
	}
	for k, v := range n {
		if v > 1 {
			t.Errorf("%s: %d times", k, v)
		}
	}
}

func puntiApplica() []string {
	var pp []string
	for _, a := range azioniDiProva() {
		for _, p := range []string{"prima-intenzione", "dopo-intenzione", "dopo-effetto", "dopo-fatta"} {
			pp = append(pp, p+"@"+a.ID)
		}
		if a.Tipo == "write-file" {
			pp = append(pp, "file-a-meta@"+a.ID)
		}
	}
	for _, s := range []Stato{IN_ESECUZIONE, APPLICATA, IN_VERIFICA, VERIFICATA} {
		pp = append(pp, "stato:"+string(s)+"@")
	}
	return pp
}

// ⭐ Killed during application, resumed: CONFERMATA, and the machine as after a clean run.
func TestRipresaDopoInterruzione(t *testing.T) {
	rif := fotoRiferimento(t)
	for _, punto := range puntiApplica() {
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", punto)
			op, err := b.motore(t).Riprendi()
			if err != nil {
				t.Fatalf("resume: %v", err)
			}
			if op.Stato != CONFERMATA {
				t.Fatalf("state %s, expected CONFIRMED", op.Stato)
			}
			if d := differenze(rif, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("the machine is not that of the clean run:\n%s", strings.Join(d, "\n"))
			}
			if _, err := os.Stat(filepath.Join(op.Cartella, "certificate.json")); err != nil {
				t.Errorf("the certificate is missing: %v", err)
			}
			controllaRegistro(t, op)
		})
	}
}

// ⭐ Killed during application, then cancelled: ANNULLATA, and the machine as it was before,
// byte by byte (the firewall rule and the member of «video» that were there stay).
func TestAnnullaDopoInterruzione(t *testing.T) {
	for _, punto := range puntiApplica() {
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", punto)
			op, err := b.motore(t).Annulla()
			if err != nil {
				t.Fatalf("cancel: %v", err)
			}
			if op.Stato != ANNULLATA {
				t.Fatalf("state %s, expected ROLLED_BACK", op.Stato)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
		})
	}
}

// ⭐ Killed DURING the rollback (R30, last point): resume finishes the cancellation.
func TestInterruzioneDuranteAnnullamento(t *testing.T) {
	var punti []string
	for _, a := range azioniDiProva() {
		punti = append(punti, "annulla-dopo-intenzione@"+a.ID, "annulla-dopo-effetto@"+a.ID)
	}
	punti = append(punti, "file-a-meta@overwritten-file", "stato:INTERRUPTED@", "stato:ROLLING_BACK@")
	for _, punto := range punti {
		if punto == "annulla-dopo-intenzione@group-preexisting" || punto == "annulla-dopo-effetto@group-preexisting" {
			continue // PREESISTENTE: it has no undo, the point is not reached (tested below)
		}
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			// first an application killed halfway, so there is something to cancel
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@service")
			uccidiIn(t, b.radice, b.operazioni, b.piano, "annulla", punto)
			// resume: an IN_ANNULLAMENTO operation is resumed by cancelling; an INTERROTTA one
			// is cancelled again
			m := b.motore(t)
			ap, _ := m.Aperta()
			var op *Operazione
			var err error
			if ap.Stato == IN_ANNULLAMENTO {
				op, err = m.Riprendi()
			} else {
				op, err = m.Annulla()
			}
			if err != nil {
				t.Fatal(err)
			}
			if op.Stato != ANNULLATA {
				t.Fatalf("state %s, expected ROLLED_BACK", op.Stato)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("the machine did not go back to how it was:\n%s", strings.Join(d, "\n"))
			}
		})
	}
	t.Run("the PREEXISTING point is not reached", func(t *testing.T) {
		b := nuovoBanco(t)
		uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@service")
		cmd := exec.Command(os.Args[0], "-test.run=^$")
		cmd.Env = append(os.Environ(), "REMOTIX_PROVA_FIGLIO=1", "RADICE="+b.radice, "OPERAZIONI="+b.operazioni,
			"COMANDO=annulla", "PUNTO=annulla-dopo-intenzione@group-preexisting")
		err := cmd.Run()
		var ee *exec.ExitError
		if !errors.As(err, &ee) || ee.ExitCode() != 3 {
			t.Fatalf("expected: the child finishes without passing the point (exit 3), got %v", err)
		}
		if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
			t.Fatalf("%s", strings.Join(d, "\n"))
		}
	})
}

// Interrupted before touching the machine: resume says so and touches nothing.
func TestInterruzionePrimaDiToccare(t *testing.T) {
	for _, s := range []Stato{FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA} {
		t.Run(string(s), func(t *testing.T) {
			b := nuovoBanco(t)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "stato:"+string(s)+"@")
			op, err := b.motore(t).Riprendi()
			if err != nil || op.Stato != BLOCCATA {
				t.Fatalf("state %v, err %v; expected BLOCKED (RX-RIPRESA-002)", op.Stato, err)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("toccata: %s", strings.Join(d, "\n"))
			}
			// and it does not stay open: a new application starts
			if op2, err := b.motore(t).Applica(b.piano, false, "prova"); err != nil || op2.Stato != CONFERMATA {
				t.Fatalf("apply after: %v %v", op2, err)
			}
		})
	}
}

// A log line written halfway (process killed during the write): it is removed and resumed.
func TestRigaTroncata(t *testing.T) {
	b := nuovoBanco(t)
	uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-intenzione@unit")
	ap, _ := b.motore(t).Aperta()
	f, _ := os.OpenFile(filepath.Join(ap.Cartella, "log.jsonl"), os.O_APPEND|os.O_WRONLY, 0)
	f.WriteString(`{"n":99,"type":"FAT`)
	f.Close()
	op, err := b.motore(t).Riprendi()
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("%v %v", op.Stato, err)
	}
	trovata := false
	for _, e := range op.Reg.Eventi {
		if e.Codice == "RX-RIPRESA-003" {
			trovata = true
		}
	}
	if !trovata {
		t.Error("the truncated line was not declared (RX-RIPRESA-003)")
	}
}

// DONE but the effect is gone (last line of the table): INTERROTTA (RX-RIPRESA-001); then it is cancelled.
func TestModificaConcorrente(t *testing.T) {
	t.Run("group removed by others", func(t *testing.T) {
		b := nuovoBanco(t)
		uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@group-video")
		(&gruppiFinti{b.radice}).Togli("prova", "video")
		m := b.motore(t)
		op, err := m.Riprendi()
		if err != nil || op.Stato != INTERROTTA {
			t.Fatalf("state %v err %v, expected INTERRUPTED (RX-RIPRESA-001)", op.Stato, err)
		}
		if ap, _ := m.Aperta(); ap == nil {
			t.Fatal("INTERRUPTED must stay open")
		}
		op, err = m.Annulla()
		if err != nil || op.Stato != ANNULLATA {
			t.Fatalf("cancel: %v %v", op.Stato, err)
		}
		if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
			t.Fatalf("%s", strings.Join(d, "\n"))
		}
	})
	t.Run("file changed by the administrator", func(t *testing.T) {
		b := nuovoBanco(t)
		uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@unit")
		conf := filepath.Join(b.radice, "etc/remotix/engine-test.conf")
		os.WriteFile(conf, []byte("porta=9999 # messa a mano\n"), 0o644)
		m := b.motore(t)
		if op, _ := m.Riprendi(); op.Stato != INTERROTTA {
			t.Fatalf("state %v, expected INTERRUPTED", op.Stato)
		}
		op, err := m.Annulla()
		if err != nil || op.Stato != ANNULLATA_IN_PARTE {
			t.Fatalf("cancel: %v %v, expected PARTIALLY_ROLLED_BACK", op.Stato, err)
		}
		if c, _ := os.ReadFile(conf); string(c) != "porta=9999 # messa a mano\n" {
			t.Fatalf("the administrator's file was touched: %q", c)
		}
	})
}

// R28 in small: a step that fails (here: nftables, which the engine cannot change yet; ufw
// can since T6) ⇒
// the operation is cancelled entirely, and the machine is as it was.
// pianoCheFallisce: the trial plan with a last step that cannot succeed (a person who does not
// exist, RX-GRUPPI-003): everything done before is cancelled.
func pianoCheFallisce(t *testing.T, b *banco) string {
	p := pianoDiProva(t, b.radice, filepath.Dir(b.radice), false)
	var pn Piano
	LeggiJSON(p, &pn)
	pn.Azioni = append(pn.Azioni, PianoGruppo("ghost", "fantasma", "video"))
	im, err := CalcolaImpronta(profiloFinto(), catalogoProva(t), pn.Azioni, pn.Dipende, &Contesto{Amb: ambienteFinto(b.radice)})
	if err != nil {
		t.Fatal(err)
	}
	pn.Impronta = *im
	pn.Approvazione = &Approvazione{Da: "prova", Ora: "2026-09-30T00:00:00Z", Modo: "da file", DigestPiano: pn.Digest()}
	ScriviJSON(p, &pn)
	return p
}

func TestFallimentoAnnullaTutto(t *testing.T) {
	b := nuovoBanco(t)
	b.piano = pianoCheFallisce(t, b)
	b.prima = foto(t, b.radice)
	op, err := b.motore(t).Applica(b.piano, false, "prova")
	if err != nil || op.Stato != ANNULLATA {
		t.Fatalf("state %v err %v, expected ROLLED_BACK", op.Stato, err)
	}
	if u := op.Reg.Ultimo("ghost", EvFallita); u == nil || u.Codice != "RX-GRUPPI-003" {
		t.Fatalf("the failure does not carry RX-GRUPPI-003: %+v", u)
	}
	if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("%s", strings.Join(d, "\n"))
	}
	// and killed during that cancellation, then resumed
	for _, punto := range []string{"annulla-dopo-intenzione@unit", "annulla-dopo-effetto@overwritten-file", "stato:ROLLING_BACK@"} {
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			b.piano = pianoCheFallisce(t, b)
			b.prima = foto(t, b.radice)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", punto)
			op, err := b.motore(t).Riprendi()
			if err != nil || op.Stato != ANNULLATA {
				t.Fatalf("state %v err %v", op.Stato, err)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("%s", strings.Join(d, "\n"))
			}
		})
	}
}
