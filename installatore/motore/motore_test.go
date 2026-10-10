package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// The state machine: only the transitions of the design of §6.6.2, no state skipped.
func TestTransizioni(t *testing.T) {
	cammino := []Stato{NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA,
		IN_ESECUZIONE, APPLICATA, IN_VERIFICA, VERIFICATA, CONFERMATA}
	for i := 0; i+1 < len(cammino); i++ {
		if !Valida(cammino[i], cammino[i+1]) {
			t.Errorf("%s → %s should be valid", cammino[i], cammino[i+1])
		}
		for j := i + 2; j < len(cammino); j++ {
			if Valida(cammino[i], cammino[j]) {
				t.Errorf("%s → %s skips a state", cammino[i], cammino[j])
			}
		}
	}
	for _, s := range []Stato{CONFERMATA, CONFERMATA_A_CONDIZIONI, ANNULLATA, ANNULLATA_IN_PARTE, RIFIUTATA} {
		if !Finale(s) || len(transizioni[s]) != 0 {
			t.Errorf("%s must be final and without exits", s)
		}
	}
	// from phases 0-5 one can only block (or refuse at consent), never cancel: nothing has been touched
	for _, s := range []Stato{NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA} {
		if Valida(s, IN_ANNULLAMENTO) || Valida(s, ANNULLATA) {
			t.Errorf("%s → cancellation: before phase 6 there is nothing to cancel", s)
		}
		if !Valida(s, BLOCCATA) {
			t.Errorf("%s → BLOCKED must be valid", s)
		}
	}
	if Valida(IN_ESECUZIONE, CONFERMATA) || Valida(INTERROTTA, APPLICATA) || Valida(IN_ANNULLAMENTO, CONFERMATA) {
		t.Error("a shortcut is valid")
	}
	if len(TuttiGliStati()) != 19 {
		t.Errorf("there are %d states, the design has 19", len(TuttiGliStati()))
	}
	// and the engine really refuses a transition outside the design
	b := nuovoBanco(t)
	op, _ := b.motore(t).Applica(b.piano, false, "prova")
	if err := op.vai(IN_ESECUZIONE, "", ""); CodiceDi(err) != "RX-STATO-002" {
		t.Errorf("CONFIRMED → RUNNING accepted: %v", err)
	}
}

// Every code used in the sources exists, and every code has the form RX-<AREA>-<NNN> (§6.6.9).
func TestCodici(t *testing.T) {
	forma := regexp.MustCompile(`^RX-[A-Z0-9]+-[0-9]{3}$`)
	for c, v := range Codici {
		if !forma.MatchString(c) || v.Testo == "" || v.Gravita == "" || v.Natura == "" {
			t.Errorf("malformed code: %s %+v", c, v)
		}
	}
	usati := regexp.MustCompile(`"(RX-[A-Z0-9]+-[0-9]{3})"`)
	voci, _ := filepath.Glob("*.go")
	voci2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(voci, voci2...) {
		b, _ := os.ReadFile(f)
		for _, m := range usati.FindAllStringSubmatch(string(b), -1) {
			if _, ok := Codici[m[1]]; !ok {
				t.Errorf("%s uses %s, which does not exist", f, m[1])
			}
		}
	}
}

// R31 in small: the plan does not apply to a different machine, and touches nothing.
func TestImprontaCambiata(t *testing.T) {
	b := nuovoBanco(t)
	os.WriteFile(filepath.Join(b.radice, "etc/remotix-esistente.conf"), []byte("cambiato dopo il piano\n"), 0o640)
	dopoCambio := foto(t, b.radice)
	op, err := b.motore(t).Applica(b.piano, false, "prova")
	if CodiceDi(err) != "RX-PIANO-001" || op.Stato != BLOCCATA {
		t.Fatalf("expected BLOCKED with RX-PIANO-001, got %v %v", op.Stato, err)
	}
	if !strings.Contains(err.Error(), "file:/etc/remotix-esistente.conf") {
		t.Errorf("the refusal does not say what changed: %v", err)
	}
	if d := differenze(dopoCambio, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	if ap, _ := b.motore(t).Aperta(); ap != nil {
		t.Error("a BLOCKED must be final")
	}
	// also an element of the profile: a group of the card with one more member
	b2 := nuovoBanco(t)
	(&gruppiFinti{b2.radice}).Aggiungi("root", "video")
	if _, err := b2.motore(t).Applica(b2.piano, false, "prova"); CodiceDi(err) != "RX-PIANO-001" {
		t.Errorf("group changed: %v", err)
	}
}

// The consent: without it, RIFIUTATA; with an approval of another plan, RIFIUTATA; nothing touched.
func TestConsenso(t *testing.T) {
	b := nuovoBanco(t)
	b.piano = pianoDiProva(t, b.radice, filepath.Dir(b.radice), false)
	if op, _ := b.motore(t).Applica(b.piano, false, "prova"); op.Stato != RIFIUTATA {
		t.Fatalf("without approval: %s", op.Stato)
	}
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Approvazione = &Approvazione{Da: "x", DigestPiano: "0000"}
	ScriviJSON(b.piano, &p)
	if op, _ := b.motore(t).Applica(b.piano, false, "prova"); op.Stato != RIFIUTATA {
		t.Fatalf("approval of another plan: %s", op.Stato)
	}
	if d := differenze(b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	// by hand (--approva): it holds
	if op, err := b.motore(t).Applica(b.piano, true, "prova"); err != nil || op.Stato != RIFIUTATA {
		// the wrong approval in the file wins over --approva: the file names another plan
		t.Logf("with wrong approval in the file and --approve: %v %v", op.Stato, err)
	}
	p.Approvazione = nil
	ScriviJSON(b.piano, &p)
	if op, err := b.motore(t).Applica(b.piano, true, "prova"); err != nil || op.Stato != CONFERMATA {
		t.Fatalf("with --approve: %v %v", op.Stato, err)
	}
}

// Only one open operation at a time; and the lock.
func TestUnaAllaVolta(t *testing.T) {
	b := nuovoBanco(t)
	uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@unit")
	if _, err := b.motore(t).Applica(b.piano, false, "prova"); CodiceDi(err) != "RX-STATO-001" {
		t.Fatalf("an open operation did not stop the new one: %v", err)
	}
	m := b.motore(t)
	if err := m.Blocca(); err != nil {
		t.Fatal(err)
	}
	defer m.Sblocca()
	if _, err := b.motore(t).Riprendi(); CodiceDi(err) != "RX-STATO-003" {
		t.Fatalf("two engines together: %v", err)
	}
}

// R5 in small: after CONFERMATA, nothing to resume; and a plan redone on the machine already in
// place has PRE-EXISTING steps (nothing is rewritten).
func TestIdempotenza(t *testing.T) {
	b := nuovoBanco(t)
	if op, err := b.motore(t).Applica(b.piano, false, "prova"); err != nil || op.Stato != CONFERMATA {
		t.Fatal(op.Stato, err)
	}
	dopo := foto(t, b.radice)
	if _, err := b.motore(t).Riprendi(); CodiceDi(err) != "RX-STATO-004" {
		t.Fatalf("resume after CONFIRMED: %v", err)
	}
	piano2 := pianoDiProva(t, b.radice, t.TempDir(), true)
	op, err := b.motore(t).Applica(piano2, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatal(op.Stato, err)
	}
	for _, e := range op.Reg.Eventi {
		if e.Tipo == EvIntenzione && e.Origine != PREESISTENTE {
			t.Errorf("%s redone as %s", e.Azione, e.Origine)
		}
	}
	if d := differenze(dopo, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("the second time it wrote: %v", d)
	}
}

// R32 in small: a check that cannot answer (systemctl that does not answer) is not PASS.
func TestSconosciutoNonPassa(t *testing.T) {
	b := nuovoBanco(t)
	uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "stato:VERIFYING@")
	os.WriteFile(filepath.Join(b.radice, "rompi-systemctl"), nil, 0o644)
	op, _ := b.motore(t).Riprendi()
	if op.Stato == CONFERMATA || op.Stato == CONFERMATA_A_CONDIZIONI {
		t.Fatalf("CONFIRMED with a check without an answer")
	}
	var rv RapportoVerifica
	LeggiJSON(filepath.Join(op.Cartella, "check.json"), &rv)
	trovato := false
	for _, k := range rv.Controlli {
		if k.ID == "unit" && k.Esito == "UNKNOWN" {
			trovato = true
		}
	}
	if !trovato {
		t.Errorf("the unit check should have been UNKNOWN: %+v", rv.Controlli)
	}
}

// The certificate and installazione.json: only the kinds that install write the state that
// REMOTIX checks at start-up (DECISIONI §10.12, RX-INST-001).
func TestInstallazione(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	if op, err := m.Applica(b.piano, false, "prova"); err != nil || op.Stato != CONFERMATA {
		t.Fatal(err)
	}
	if _, err := m.ControllaInstallazione(); CodiceDi(err) != "RX-INST-001" {
		t.Fatalf("the trial plan does not install REMOTIX: %v", err)
	}
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Mestiere = "installation"
	p.Approvazione = nil
	b2 := nuovoBanco(t)
	ScriviJSON(b2.piano, &p)
	m2 := b2.motore(t)
	op, err := m2.Applica(b2.piano, true, "prova")
	// REMOTIX's binary is not there (and does not have --prova-codifica yet): encoding is UNKNOWN,
	// required ⇒ conditional, never a clean CONFERMATA (§6.6.7)
	if err != nil || op.Stato != CONFERMATA_A_CONDIZIONI {
		t.Fatal(op.Stato, err)
	}
	in, err := m2.ControllaInstallazione()
	if err != nil || in.Operazione != op.ID {
		t.Fatalf("installazione.json: %+v %v", in, err)
	}
}

func ultimoStato(op *Operazione) string {
	for i := len(op.Reg.Eventi) - 1; i >= 0; i-- {
		if op.Reg.Eventi[i].Tipo == EvStato {
			return op.Reg.Eventi[i].Codice + " " + op.Reg.Eventi[i].Dettaglio
		}
	}
	return ""
}

// The trial plan: the packages first, the group LAST (R28 for real on Alma).
func TestPianoDiProva(t *testing.T) {
	b := nuovoBanco(t)
	amb := ambienteFinto(b.radice)
	cat := catalogoProva(t)
	prof := profiloFinto()
	p, err := PianoDiProva(prof, Valuta(cat, prof), cat, amb, OpzioniPianoProva{Utente: "prova", Pacchetti: "labwc"})
	if err != nil {
		t.Fatal(err)
	}
	var tipi []string
	for _, a := range p.Azioni {
		tipi = append(tipi, a.Tipo)
	}
	if got := strings.Join(tipi, ","); got != "install-packages,write-file,write-file,enable-unit,add-user-to-group" {
		t.Fatalf("order of the steps: %s", got)
	}
}
