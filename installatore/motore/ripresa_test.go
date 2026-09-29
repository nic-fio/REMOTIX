package motore

// R30 in piccolo: il processo del motore UCCISO davvero (SIGKILL, niente defer, niente pulizia)
// in ogni punto della tabella di §6.6.3 e in ogni transizione di stato; poi un motore nuovo
// riprende e deve arrivare a CONFERMATA (o ANNULLATA, se si annulla) con la macchina IDENTICA a
// quella di un giro senza interruzioni (o a quella di prima). Il processo ucciso è questo stesso
// binario di prova, rilanciato con REMOTIX_PROVA_FIGLIO=1: il gancio PuntoDiProva esiste solo
// nelle prove.

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

// figlio: il motore che verrà ucciso. Esce 3 se il punto non è mai stato raggiunto.
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

// uccidiIn lancia il figlio e controlla che sia morto di SIGKILL nel punto chiesto.
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
		t.Fatalf("%s %s: il figlio non è morto (err=%v) %s", comando, punto, err, errOut.String())
	}
	if ws, ok := ee.Sys().(syscall.WaitStatus); !ok || !ws.Signaled() || ws.Signal() != syscall.SIGKILL {
		t.Fatalf("%s %s: il punto non è stato raggiunto (uscita %v): %s", comando, punto, err, errOut.String())
	}
}

type banco struct {
	radice, operazioni, piano string
	prima                     map[string]string
}

func nuovoBanco(t *testing.T) *banco {
	d := t.TempDir()
	b := &banco{radice: filepath.Join(d, "macchina"), operazioni: filepath.Join(d, "operazioni")}
	os.MkdirAll(b.radice, 0o755)
	preparaMacchina(t, b.radice)
	b.piano = pianoDiProva(t, b.radice, d, true)
	b.prima = foto(t, b.radice)
	return b
}

func (b *banco) motore(t *testing.T) *Motore { return motoreFinto(t, b.radice, b.operazioni) }

// riferimento: la macchina dopo un giro intero senza interruzioni.
var riferimento map[string]string

func fotoRiferimento(t *testing.T) map[string]string {
	if riferimento != nil {
		return riferimento
	}
	b := nuovoBanco(t)
	op, err := b.motore(t).Applica(b.piano, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("giro senza interruzioni: %v, stato %v", err, op.Stato)
	}
	riferimento = foto(t, b.radice)
	return riferimento
}

// controllaRegistro: nessuna azione FATTA due volte, nessuna INTENZIONE doppia (effetto doppio).
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
			t.Errorf("%s: %d volte", k, v)
		}
	}
}

func puntiApplica() []string {
	var pp []string
	for _, a := range azioniDiProva() {
		for _, p := range []string{"prima-intenzione", "dopo-intenzione", "dopo-effetto", "dopo-fatta"} {
			pp = append(pp, p+"@"+a.ID)
		}
		if a.Tipo == "scrivi-file" {
			pp = append(pp, "file-a-meta@"+a.ID)
		}
	}
	for _, s := range []Stato{IN_ESECUZIONE, APPLICATA, IN_VERIFICA, VERIFICATA} {
		pp = append(pp, "stato:"+string(s)+"@")
	}
	return pp
}

// ⭐ Ucciso durante l'applicazione, ripreso: CONFERMATA, e la macchina come dopo un giro pulito.
func TestRipresaDopoInterruzione(t *testing.T) {
	rif := fotoRiferimento(t)
	for _, punto := range puntiApplica() {
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", punto)
			op, err := b.motore(t).Riprendi()
			if err != nil {
				t.Fatalf("riprendi: %v", err)
			}
			if op.Stato != CONFERMATA {
				t.Fatalf("stato %s, atteso CONFERMATA", op.Stato)
			}
			if d := differenze(rif, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("la macchina non è quella del giro pulito:\n%s", strings.Join(d, "\n"))
			}
			if _, err := os.Stat(filepath.Join(op.Cartella, "certificato.json")); err != nil {
				t.Errorf("manca il certificato: %v", err)
			}
			controllaRegistro(t, op)
		})
	}
}

// ⭐ Ucciso durante l'applicazione, poi annullato: ANNULLATA, e la macchina com'era prima,
// byte per byte (la regola del firewall e il membro di «video» che c'erano restano).
func TestAnnullaDopoInterruzione(t *testing.T) {
	for _, punto := range puntiApplica() {
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", punto)
			op, err := b.motore(t).Annulla()
			if err != nil {
				t.Fatalf("annulla: %v", err)
			}
			if op.Stato != ANNULLATA {
				t.Fatalf("stato %s, atteso ANNULLATA", op.Stato)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("la macchina non è tornata com'era:\n%s", strings.Join(d, "\n"))
			}
		})
	}
}

// ⭐ Ucciso DURANTE il ritorno indietro (R30, ultimo punto): la ripresa finisce l'annullamento.
func TestInterruzioneDuranteAnnullamento(t *testing.T) {
	var punti []string
	for _, a := range azioniDiProva() {
		punti = append(punti, "annulla-dopo-intenzione@"+a.ID, "annulla-dopo-effetto@"+a.ID)
	}
	punti = append(punti, "file-a-meta@file-sovrascritto", "stato:INTERROTTA@", "stato:IN_ANNULLAMENTO@")
	for _, punto := range punti {
		if punto == "annulla-dopo-intenzione@gruppo-preesistente" || punto == "annulla-dopo-effetto@gruppo-preesistente" {
			continue // PREESISTENTE: non ha un annullamento, il punto non si raggiunge (lo si prova sotto)
		}
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			// prima un'applicazione uccisa a metà, così c'è qualcosa da annullare
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@servizio")
			uccidiIn(t, b.radice, b.operazioni, b.piano, "annulla", punto)
			// la ripresa: un'operazione IN_ANNULLAMENTO si riprende annullando; una INTERROTTA la
			// si annulla di nuovo
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
				t.Fatalf("stato %s, atteso ANNULLATA", op.Stato)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("la macchina non è tornata com'era:\n%s", strings.Join(d, "\n"))
			}
		})
	}
	t.Run("il punto PREESISTENTE non si raggiunge", func(t *testing.T) {
		b := nuovoBanco(t)
		uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@servizio")
		cmd := exec.Command(os.Args[0], "-test.run=^$")
		cmd.Env = append(os.Environ(), "REMOTIX_PROVA_FIGLIO=1", "RADICE="+b.radice, "OPERAZIONI="+b.operazioni,
			"COMANDO=annulla", "PUNTO=annulla-dopo-intenzione@gruppo-preesistente")
		err := cmd.Run()
		var ee *exec.ExitError
		if !errors.As(err, &ee) || ee.ExitCode() != 3 {
			t.Fatalf("atteso: il figlio finisce senza passare dal punto (uscita 3), invece %v", err)
		}
		if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
			t.Fatalf("%s", strings.Join(d, "\n"))
		}
	})
}

// Interrotta prima di toccare la macchina: la ripresa lo dice e non tocca niente.
func TestInterruzionePrimaDiToccare(t *testing.T) {
	for _, s := range []Stato{FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA} {
		t.Run(string(s), func(t *testing.T) {
			b := nuovoBanco(t)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "stato:"+string(s)+"@")
			op, err := b.motore(t).Riprendi()
			if err != nil || op.Stato != BLOCCATA {
				t.Fatalf("stato %v, err %v; atteso BLOCCATA (RX-RIPRESA-002)", op.Stato, err)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("toccata: %s", strings.Join(d, "\n"))
			}
			// e non resta aperta: un'applicazione nuova parte
			if op2, err := b.motore(t).Applica(b.piano, false, "prova"); err != nil || op2.Stato != CONFERMATA {
				t.Fatalf("applica dopo: %v %v", op2, err)
			}
		})
	}
}

// Una riga del registro scritta a metà (processo ucciso durante la write): si toglie e si riprende.
func TestRigaTroncata(t *testing.T) {
	b := nuovoBanco(t)
	uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-intenzione@unita")
	ap, _ := b.motore(t).Aperta()
	f, _ := os.OpenFile(filepath.Join(ap.Cartella, "registro.jsonl"), os.O_APPEND|os.O_WRONLY, 0)
	f.WriteString(`{"n":99,"tipo":"FAT`)
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
		t.Error("la riga troncata non è stata dichiarata (RX-RIPRESA-003)")
	}
}

// FATTA ma l'effetto non c'è più (ultima riga della tabella): INTERROTTA (RX-RIPRESA-001); poi si annulla.
func TestModificaConcorrente(t *testing.T) {
	t.Run("gruppo tolto da altri", func(t *testing.T) {
		b := nuovoBanco(t)
		uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@gruppo-video")
		(&gruppiFinti{b.radice}).Togli("prova", "video")
		m := b.motore(t)
		op, err := m.Riprendi()
		if err != nil || op.Stato != INTERROTTA {
			t.Fatalf("stato %v err %v, atteso INTERROTTA (RX-RIPRESA-001)", op.Stato, err)
		}
		if ap, _ := m.Aperta(); ap == nil {
			t.Fatal("INTERROTTA deve restare aperta")
		}
		op, err = m.Annulla()
		if err != nil || op.Stato != ANNULLATA {
			t.Fatalf("annulla: %v %v", op.Stato, err)
		}
		if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
			t.Fatalf("%s", strings.Join(d, "\n"))
		}
	})
	t.Run("file cambiato dall'amministratore", func(t *testing.T) {
		b := nuovoBanco(t)
		uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@unita")
		conf := filepath.Join(b.radice, "etc/remotix/prova-motore.conf")
		os.WriteFile(conf, []byte("porta=9999 # messa a mano\n"), 0o644)
		m := b.motore(t)
		if op, _ := m.Riprendi(); op.Stato != INTERROTTA {
			t.Fatalf("stato %v, atteso INTERROTTA", op.Stato)
		}
		op, err := m.Annulla()
		if err != nil || op.Stato != ANNULLATA_IN_PARTE {
			t.Fatalf("annulla: %v %v, atteso ANNULLATA_IN_PARTE", op.Stato, err)
		}
		if c, _ := os.ReadFile(conf); string(c) != "porta=9999 # messa a mano\n" {
			t.Fatalf("il file dell'amministratore è stato toccato: %q", c)
		}
	})
}

// R28 in piccolo: un passo che fallisce (qui: ufw, che il motore non sa ancora cambiare) ⇒
// l'operazione si annulla per intero, e la macchina è com'era.
func TestFallimentoAnnullaTutto(t *testing.T) {
	b := nuovoBanco(t)
	os.WriteFile(filepath.Join(b.radice, "etc/finto-firewall"), []byte("ufw"), 0o644)
	b.piano = pianoDiProva(t, b.radice, filepath.Dir(b.radice), true)
	b.prima = foto(t, b.radice)
	op, err := b.motore(t).Applica(b.piano, false, "prova")
	if err != nil || op.Stato != ANNULLATA {
		t.Fatalf("stato %v err %v, atteso ANNULLATA", op.Stato, err)
	}
	if u := op.Reg.Ultimo("firewall", EvFallita); u == nil || u.Codice != "RX-FW-004" {
		t.Fatalf("il fallimento non porta RX-FW-004: %+v", u)
	}
	if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("%s", strings.Join(d, "\n"))
	}
	// e ucciso durante quell'annullamento, poi ripreso
	for _, punto := range []string{"annulla-dopo-intenzione@unita", "annulla-dopo-effetto@file-sovrascritto", "stato:IN_ANNULLAMENTO@"} {
		t.Run(punto, func(t *testing.T) {
			b := nuovoBanco(t)
			os.WriteFile(filepath.Join(b.radice, "etc/finto-firewall"), []byte("ufw"), 0o644)
			b.piano = pianoDiProva(t, b.radice, filepath.Dir(b.radice), true)
			b.prima = foto(t, b.radice)
			uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", punto)
			op, err := b.motore(t).Riprendi()
			if err != nil || op.Stato != ANNULLATA {
				t.Fatalf("stato %v err %v", op.Stato, err)
			}
			if d := differenzeDopoAnnullo(t, b.prima, foto(t, b.radice)); len(d) > 0 {
				t.Fatalf("%s", strings.Join(d, "\n"))
			}
		})
	}
}
