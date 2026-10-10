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
	p.Mestiere, p.Approvazione = "installation", nil
	ScriviJSON(b.piano, &p)
	op, err := b.motore(t).Applica(b.piano, true, "prova")
	if err != nil || op.Stato != CONFERMATA_A_CONDIZIONI {
		t.Fatalf("installazione: %v %v", op.Stato, err)
	}
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-sessioni.json"),
		[]byte(`[{"ID":"c4","Utente":"prova","Servizio":"remotix","Stato":"closing","Tipo":"unspecified"},{"ID":"7","Utente":"prova","Servizio":"sshd","Stato":"active","Tipo":"tty"}]`), 0o644)
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-grafica.json"), []byte(`{"prova":18}`), 0o644)
	// REMOTIX alla prima connessione ha iscritto «altro» a «render» (e l'ha scritto due volte)
	(&gruppiFinti{b.radice}).Aggiungi("altro", "render")
	riga := `{"formato":"remotix-gruppi/1","data":"2026-09-30","utente":"altro","uid":1001,"gruppo":"render","gid":991,"origine":"DIRETTA","da":"REMOTIX alla prima connessione"}` + "\n"
	os.WriteFile(filepath.Join(filepath.Dir(b.operazioni), FileIscrizioni), []byte(riga+riga), 0o644)
	// i registri di sessione che REMOTIX ha scritto nelle case (sessione.c): «prova» ha solo quello,
	// «altro» ha anche un file suo nella stessa cartella (che deve restare), root niente
	for _, u := range []string{"prova", "altro"} {
		d := filepath.Join(b.radice, "home", u, cartellaStatoUtente)
		os.MkdirAll(d, 0o700)
		os.WriteFile(filepath.Join(d, fileSessione), []byte("2026-09-30 sessione di "+u+"\n"), 0o600)
	}
	os.WriteFile(filepath.Join(b.radice, "home/altro", cartellaStatoUtente, "appunti.txt"), []byte("miei\n"), 0o600)
	return b
}

// registriDopo: la casa di «prova» senza cartella, quella di «altro» col solo file suo.
func registriDopo(t *testing.T, radice string) {
	t.Helper()
	if _, err := os.Stat(filepath.Join(radice, "home/prova", cartellaStatoUtente)); !os.IsNotExist(err) {
		t.Fatalf("la cartella di stato di prova è rimasta (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(radice, "home/altro", cartellaStatoUtente, fileSessione)); !os.IsNotExist(err) {
		t.Fatalf("il sessione.log di altro è rimasto (%v)", err)
	}
	if _, err := os.Stat(filepath.Join(radice, "home/altro", cartellaStatoUtente, "appunti.txt")); err != nil {
		t.Fatalf("il file di altro NON doveva sparire: %v", err)
	}
}

func pianoDisinstallazione(t *testing.T, b *banco) string {
	pn, err := b.motore(t).PianoDisinstallazione(profiloFinto(), true)
	if err != nil {
		t.Fatal(err)
	}
	if n := len(pn.Dichiarate); n != 1 || !strings.Contains(pn.Dichiarate[0], "/home/prova/.local/state/remotix/sessione.log, /home/altro/.local/state/remotix/sessione.log") {
		t.Fatalf("il piano deve dichiarare i registri di sessione coi percorsi: %q", pn.Dichiarate)
	}
	if u := pn.Azioni[len(pn.Azioni)-1]; u.Tipo != "remove-user-logs" || !strings.Contains(u.Descrizione, "/home/altro/") {
		t.Fatalf("l'ultimo passo deve togliere i registri, coi percorsi: %+v", u)
	}
	pn.Approvazione = &Approvazione{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "uninstall.json")
	ScriviJSON(p, pn)
	return p
}

// ⭐ R6 e R43 in piccolo: la disinstallazione ripercorre il registro — la macchina torna com'era
// (salvo l'INDIRETTA dichiarata), la sessione REMOTIX è chiusa, quella ssh resta,
// installazione.json non c'è più. E uccisa a metà si riprende fino in fondo.
func TestDisinstallazione(t *testing.T) {
	punti := []string{"", "dopo-intenzione@undo-service", "dopo-effetto@close-sessions",
		"dopo-intenzione@undo-packages", "file-a-meta@overwritten-file", "stato:APPLIED@"}
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
			if n, _ := (&sessioniFinte{b.radice}).Grafici("prova"); n != 0 {
				t.Fatalf("%d processi del desktop ancora vivi", n)
			}
			registriDopo(t, b.radice)
			dopo := foto(t, b.radice)
			delete(dopo, "var/lib/finto-sessioni.json")
			delete(dopo, "var/lib/finto-grafica.json")
			for _, k := range []string{"home/", "home/altro/", "home/altro/.local/", "home/altro/.local/state/", "home/altro/.local/state/remotix/", "home/altro/.local/state/remotix/appunti.txt", "home/prova/", "home/prova/.local/", "home/prova/.local/state/"} {
				delete(dopo, k) // le case: quel che non è di REMOTIX resta
			}
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
			if _, err := os.Stat(b.operazioni); !os.IsNotExist(err) {
				t.Fatalf("--purge: la storia del motore è rimasta (%v)", err)
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
	uccidiIn(t, b.radice, b.operazioni, pd, "applica", "dopo-fatta@undo-unit")
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
		t.Fatalf("non è tornata l'installazione:\n%s", strings.Join(d, "\n"))
	}
	if _, err := b.motore(t).ControllaInstallazione(); err != nil {
		t.Fatalf("l'installazione deve risultare ancora: %v", err)
	}
}

// Senza --purge la storia resta (per l'assistenza), ma senza i pacchetti in cache.
func TestDisinstallazioneSenzaPurge(t *testing.T) {
	b := installaFinta(t)
	pn, err := b.motore(t).PianoDisinstallazione(profiloFinto(), false)
	if err != nil {
		t.Fatal(err)
	}
	pn.Approvazione = &Approvazione{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	p := filepath.Join(t.TempDir(), "d.json")
	ScriviJSON(p, pn)
	op, err := b.motore(t).Applica(p, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("%v %v", op.Stato, err)
	}
	ops, _ := filepath.Glob(filepath.Join(b.operazioni, "*", "log.jsonl"))
	cache, _ := filepath.Glob(filepath.Join(b.operazioni, "*", "cache"))
	if len(ops) != 2 || len(cache) != 0 {
		t.Fatalf("storia: %d registri (attesi 2), %d cache (attese 0)", len(ops), len(cache))
	}
}

// Un pacchetto NUOVO che un pacchetto AGGIORNATO (che resta) chiede non si toglie: si trattiene e si
// dichiara (`[M]` 30 set, leap16-kde: la libavcodec di Packman aggiornata vuole la libx264 nuova, e
// `zypper rm` si sarebbe portato via Plasma). La disinstallazione si conferma lo stesso.
func TestDisinstallazioneTrattiene(t *testing.T) {
	b := installaFinta(t)
	// libcomune è stata AGGIORNATA dall'installazione (1.0 → 2.0) e la 2.0 chiede libnuova, NUOVA
	os.WriteFile(filepath.Join(b.radice, "var/lib/finto-deposito.json"),
		[]byte(`{"libnuova":{"versione":"1.0"},"libcomune":{"versione":"2.0","dipende":["libnuova"]},"labwc":{"versione":"0.9","dipende":["libnuova"]}}`), 0o644)
	pn, err := b.motore(t).PianoDisinstallazione(profiloFinto(), false) // senza purge: il certificato resta
	if err != nil {
		t.Fatal(err)
	}
	pn.Approvazione = &Approvazione{Da: "prova", Modo: "da file", DigestPiano: pn.Digest()}
	pd := filepath.Join(t.TempDir(), "d.json")
	ScriviJSON(pd, pn)
	op, err := b.motore(t).Applica(pd, false, "prova")
	if err != nil || op.Stato != CONFERMATA {
		t.Fatalf("disinstallazione: %v %v %s", op.Stato, err, op.ultimoDettaglio())
	}
	in := (&gestoreFinto{b.radice}).installati()
	if in["libnuova"] == "" || in["labwc"] != "" || in["remotix"] != "" || in["libcomune"] != "2.0" {
		t.Fatalf("pacchetti dopo: %v (atteso: libnuova trattenuta, labwc e remotix tolti)", in)
	}
	var c Certificato
	LeggiJSON(filepath.Join(op.Cartella, "certificate.json"), &c)
	if s := strings.Join(c.Indirette, "\n"); !strings.Contains(s, "RX-PACCHETTI-006") || !strings.Contains(s, "libnuova") || !strings.Contains(s, "libcomune") {
		t.Fatalf("la libnuova trattenuta non è dichiarata nel certificato: %q", s)
	}
}
