package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// La macchina a stati: solo le transizioni del disegno di §6.6.2, nessuno stato saltato.
func TestTransizioni(t *testing.T) {
	cammino := []Stato{NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA,
		IN_ESECUZIONE, APPLICATA, IN_VERIFICA, VERIFICATA, CONFERMATA}
	for i := 0; i+1 < len(cammino); i++ {
		if !Valida(cammino[i], cammino[i+1]) {
			t.Errorf("%s → %s dovrebbe valere", cammino[i], cammino[i+1])
		}
		for j := i + 2; j < len(cammino); j++ {
			if Valida(cammino[i], cammino[j]) {
				t.Errorf("%s → %s salta uno stato", cammino[i], cammino[j])
			}
		}
	}
	for _, s := range []Stato{CONFERMATA, CONFERMATA_A_CONDIZIONI, ANNULLATA, ANNULLATA_IN_PARTE, RIFIUTATA} {
		if !Finale(s) || len(transizioni[s]) != 0 {
			t.Errorf("%s deve essere finale e senza uscite", s)
		}
	}
	// dalle fasi 0-5 si può solo bloccare (o rifiutare dal consenso), mai annullare: niente è stato toccato
	for _, s := range []Stato{NUOVA, FIDATA, ESAMINATA, VALUTATA, PIANIFICATA, APPROVATA, ACQUISITA} {
		if Valida(s, IN_ANNULLAMENTO) || Valida(s, ANNULLATA) {
			t.Errorf("%s → annullamento: prima della fase 6 non c'è niente da annullare", s)
		}
		if !Valida(s, BLOCCATA) {
			t.Errorf("%s → BLOCKED deve valere", s)
		}
	}
	if Valida(IN_ESECUZIONE, CONFERMATA) || Valida(INTERROTTA, APPLICATA) || Valida(IN_ANNULLAMENTO, CONFERMATA) {
		t.Error("una scorciatoia è valida")
	}
	if len(TuttiGliStati()) != 19 {
		t.Errorf("gli stati sono %d, il disegno ne ha 19", len(TuttiGliStati()))
	}
	// e il motore rifiuta davvero una transizione fuori disegno
	b := nuovoBanco(t)
	op, _ := b.motore(t).Applica(b.piano, false, "prova")
	if err := op.vai(IN_ESECUZIONE, "", ""); CodiceDi(err) != "RX-STATO-002" {
		t.Errorf("CONFIRMED → RUNNING accettata: %v", err)
	}
}

// Ogni codice usato nei sorgenti esiste, e ogni codice ha la forma RX-<AREA>-<NNN> (§6.6.9).
func TestCodici(t *testing.T) {
	forma := regexp.MustCompile(`^RX-[A-Z0-9]+-[0-9]{3}$`)
	for c, v := range Codici {
		if !forma.MatchString(c) || v.Testo == "" || v.Gravita == "" || v.Natura == "" {
			t.Errorf("codice malformato: %s %+v", c, v)
		}
	}
	usati := regexp.MustCompile(`"(RX-[A-Z0-9]+-[0-9]{3})"`)
	voci, _ := filepath.Glob("*.go")
	voci2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(voci, voci2...) {
		b, _ := os.ReadFile(f)
		for _, m := range usati.FindAllStringSubmatch(string(b), -1) {
			if _, ok := Codici[m[1]]; !ok {
				t.Errorf("%s usa %s, che non esiste", f, m[1])
			}
		}
	}
}

// R31 in piccolo: il piano non si applica a una macchina diversa, e non tocca niente.
func TestImprontaCambiata(t *testing.T) {
	b := nuovoBanco(t)
	os.WriteFile(filepath.Join(b.radice, "etc/remotix-esistente.conf"), []byte("cambiato dopo il piano\n"), 0o640)
	dopoCambio := foto(t, b.radice)
	op, err := b.motore(t).Applica(b.piano, false, "prova")
	if CodiceDi(err) != "RX-PIANO-001" || op.Stato != BLOCCATA {
		t.Fatalf("atteso BLOCKED con RX-PIANO-001, invece %v %v", op.Stato, err)
	}
	if !strings.Contains(err.Error(), "file:/etc/remotix-esistente.conf") {
		t.Errorf("il rifiuto non dice che cosa è cambiato: %v", err)
	}
	if d := differenze(dopoCambio, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	if ap, _ := b.motore(t).Aperta(); ap != nil {
		t.Error("una BLOCKED deve essere finale")
	}
	// anche un elemento del profilo: un gruppo della scheda con un membro in più
	b2 := nuovoBanco(t)
	(&gruppiFinti{b2.radice}).Aggiungi("root", "video")
	if _, err := b2.motore(t).Applica(b2.piano, false, "prova"); CodiceDi(err) != "RX-PIANO-001" {
		t.Errorf("gruppo cambiato: %v", err)
	}
}

// Il consenso: senza, RIFIUTATA; con un'approvazione di un altro piano, RIFIUTATA; niente toccato.
func TestConsenso(t *testing.T) {
	b := nuovoBanco(t)
	b.piano = pianoDiProva(t, b.radice, filepath.Dir(b.radice), false)
	if op, _ := b.motore(t).Applica(b.piano, false, "prova"); op.Stato != RIFIUTATA {
		t.Fatalf("senza approvazione: %s", op.Stato)
	}
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Approvazione = &Approvazione{Da: "x", DigestPiano: "0000"}
	ScriviJSON(b.piano, &p)
	if op, _ := b.motore(t).Applica(b.piano, false, "prova"); op.Stato != RIFIUTATA {
		t.Fatalf("approvazione di un altro piano: %s", op.Stato)
	}
	if d := differenze(b.prima, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("toccata: %v", d)
	}
	// a mano (--approva): vale
	if op, err := b.motore(t).Applica(b.piano, true, "prova"); err != nil || op.Stato != RIFIUTATA {
		// l'approvazione sbagliata nel file vince su --approva: il file dice un altro piano
		t.Logf("con approvazione sbagliata nel file e --approve: %v %v", op.Stato, err)
	}
	p.Approvazione = nil
	ScriviJSON(b.piano, &p)
	if op, err := b.motore(t).Applica(b.piano, true, "prova"); err != nil || op.Stato != CONFERMATA {
		t.Fatalf("con --approve: %v %v", op.Stato, err)
	}
}

// Una sola operazione aperta alla volta; e la serratura.
func TestUnaAllaVolta(t *testing.T) {
	b := nuovoBanco(t)
	uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "dopo-fatta@unit")
	if _, err := b.motore(t).Applica(b.piano, false, "prova"); CodiceDi(err) != "RX-STATO-001" {
		t.Fatalf("un'operazione aperta non ha fermato la nuova: %v", err)
	}
	m := b.motore(t)
	if err := m.Blocca(); err != nil {
		t.Fatal(err)
	}
	defer m.Sblocca()
	if _, err := b.motore(t).Riprendi(); CodiceDi(err) != "RX-STATO-003" {
		t.Fatalf("due motori insieme: %v", err)
	}
}

// R5 in piccolo: dopo CONFERMATA, niente da riprendere; e un piano rifatto sulla macchina già a
// posto ha i passi PREESISTENTI (niente si riscrive).
func TestIdempotenza(t *testing.T) {
	b := nuovoBanco(t)
	if op, err := b.motore(t).Applica(b.piano, false, "prova"); err != nil || op.Stato != CONFERMATA {
		t.Fatal(op.Stato, err)
	}
	dopo := foto(t, b.radice)
	if _, err := b.motore(t).Riprendi(); CodiceDi(err) != "RX-STATO-004" {
		t.Fatalf("riprendi dopo CONFIRMED: %v", err)
	}
	piano2 := pianoDiProva(t, b.radice, t.TempDir(), true)
	op, err := b.motore(t).Applica(piano2, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatal(op.Stato, err)
	}
	for _, e := range op.Reg.Eventi {
		if e.Tipo == EvIntenzione && e.Origine != PREESISTENTE {
			t.Errorf("%s rifatta come %s", e.Azione, e.Origine)
		}
	}
	if d := differenze(dopo, foto(t, b.radice)); len(d) > 0 {
		t.Fatalf("la seconda volta ha scritto: %v", d)
	}
}

// R32 in piccolo: un controllo che non sa rispondere (systemctl che non risponde) non è PASS.
func TestSconosciutoNonPassa(t *testing.T) {
	b := nuovoBanco(t)
	uccidiIn(t, b.radice, b.operazioni, b.piano, "applica", "stato:VERIFYING@")
	os.WriteFile(filepath.Join(b.radice, "rompi-systemctl"), nil, 0o644)
	op, _ := b.motore(t).Riprendi()
	if op.Stato == CONFERMATA || op.Stato == CONFERMATA_A_CONDIZIONI {
		t.Fatalf("CONFIRMED con un controllo senza risposta")
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
		t.Errorf("il controllo dell'unità doveva essere UNKNOWN: %+v", rv.Controlli)
	}
}

// Il certificato e installazione.json: solo i mestieri che installano scrivono lo stato che
// REMOTIX controlla all'avvio (DECISIONI §10.12, RX-INST-001).
func TestInstallazione(t *testing.T) {
	b := nuovoBanco(t)
	m := b.motore(t)
	if op, err := m.Applica(b.piano, false, "prova"); err != nil || op.Stato != CONFERMATA {
		t.Fatal(err)
	}
	if _, err := m.ControllaInstallazione(); CodiceDi(err) != "RX-INST-001" {
		t.Fatalf("il piano di prova non installa REMOTIX: %v", err)
	}
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Mestiere = "installation"
	p.Approvazione = nil
	b2 := nuovoBanco(t)
	ScriviJSON(b2.piano, &p)
	m2 := b2.motore(t)
	op, err := m2.Applica(b2.piano, true, "prova")
	// il binario di REMOTIX non c'è (e non ha ancora --prova-codifica): la codifica è UNKNOWN,
	// richiesta ⇒ a condizioni, mai CONFERMATA pulita (§6.6.7)
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

// Il piano di prova: i pacchetti in testa, il gruppo per ULTIMO (R28 dal vero su Alma).
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
		t.Fatalf("ordine dei passi: %s", got)
	}
}
