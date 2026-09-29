package motore

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// installaFinta: un'installazione (mestiere «installazione») sulla macchina finta, poi due sessioni
// aperte della stessa persona: una REMOTIX e una ssh.
func installaFinta(t *testing.T) *banco {
	b := nuovoBanco(t)
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Mestiere, p.Approvazione = "installazione", nil
	ScriviJSON(b.piano, &p)
	op, err := b.motore(t).Applica(b.piano, true, "prova")
	if err != nil || op.Stato != CONFERMATA_A_CONDIZIONI {
		t.Fatalf("installazione: %v %v", op.Stato, err)
	}
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-sessioni.json"),
		[]byte(`[{"ID":"c4","Utente":"prova","Servizio":"remotix","Stato":"active"},{"ID":"7","Utente":"prova","Servizio":"sshd","Stato":"active"}]`), 0o644)
	return b
}

func pianoDisinstallazione(t *testing.T, b *banco) string {
	pn, err := b.motore(t).PianoDisinstallazione(profiloFinto(), true)
	if err != nil {
		t.Fatal(err)
	}
	pn.Approvazione = &Approvazione{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "disinstalla.json")
	ScriviJSON(p, pn)
	return p
}

// ⭐ R6 e R43 in piccolo: la disinstallazione ripercorre il registro — la macchina torna com'era
// (salvo l'INDIRETTA dichiarata), la sessione REMOTIX è chiusa, quella ssh resta,
// installazione.json non c'è più. E uccisa a metà si riprende fino in fondo.
func TestDisinstallazione(t *testing.T) {
	punti := []string{"", "dopo-intenzione@disfa-servizio", "dopo-effetto@chiudi-sessioni",
		"dopo-intenzione@disfa-pacchetti", "file-a-meta@file-sovrascritto", "stato:APPLICATA@"}
	for _, punto := range punti {
		t.Run(nonVuoto(punto, "senza interruzioni"), func(t *testing.T) {
			b := installaFinta(t)
			pd := pianoDisinstallazione(t, b)
			var op *Operazione
			var err error
			if punto == "" {
				op, err = b.motore(t).Applica(pd, false, "prova")
			} else {
				uccidiIn(t, b.radice, b.operazioni, pd, "applica", punto)
				op, err = b.motore(t).Riprendi()
			}
			if err != nil || op.Stato != CONFERMATA {
				t.Fatalf("disinstallazione: %v %v %s", op.Stato, err, op.ultimoDettaglio())
			}
			dopo := foto(t, b.radice)
			delete(dopo, "var/lib/finto-sessioni.json")
			if d := differenzeDopoAnnullo(t, b.prima, dopo); len(d) > 0 {
				t.Fatalf("la macchina non è tornata com'era:\n%s", strings.Join(d, "\n"))
			}
			l, _ := (&sessioniFinte{b.radice}).Elenco()
			if len(l) != 1 || l[0].Servizio != "sshd" {
				t.Fatalf("sessioni dopo: %+v (attesa solo quella ssh)", l)
			}
			if _, err := b.motore(t).ControllaInstallazione(); CodiceDi(err) != "RX-INST-001" {
				t.Fatalf("installazione.json è rimasto: %v", err)
			}
		})
	}
}

// Una disinstallazione uccisa a metà e poi ANNULLATA torna all'installazione (i passi «disfa» si
// annullano rifacendo), tranne le sessioni chiuse: IRREVERSIBILE ⇒ ANNULLATA_IN_PARTE.
func TestDisinstallazioneAnnullata(t *testing.T) {
	b := installaFinta(t)
	installata := foto(t, b.radice)
	pd := pianoDisinstallazione(t, b)
	uccidiIn(t, b.radice, b.operazioni, pd, "applica", "dopo-fatta@disfa-cintura-tasti")
	op, err := b.motore(t).Annulla()
	if err != nil || op.Stato != ANNULLATA_IN_PARTE {
		t.Fatalf("%v %v", op.Stato, err)
	}
	dopo := foto(t, b.radice)
	delete(dopo, "var/lib/finto-sessioni.json")
	delete(installata, "var/lib/finto-sessioni.json")
	if d := differenze(installata, dopo); len(d) > 0 {
		t.Fatalf("non è tornata l'installazione:\n%s", strings.Join(d, "\n"))
	}
	if _, err := b.motore(t).ControllaInstallazione(); err != nil {
		t.Fatalf("l'installazione deve risultare ancora: %v", err)
	}
}
