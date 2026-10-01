package motore

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// R29 in piccolo: la certificazione su una macchina guasta apposta non dice mai VERDE.
func TestCertificaGuasti(t *testing.T) {
	codifica := func(json string, uscita int) Esecutore {
		return func(_ time.Duration, nome string, _ ...string) (string, int, error) {
			if nome == "remotix" {
				return json, uscita, nil
			}
			return nessunComando(0, nome)
		}
	}
	buona := codifica(`{"esito":"hardware","codificatore":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":""}`, 0)
	apri := func(b *banco) { (&firewallFinto{b.radice}).Aggiungi("public", "7447/udp", false) }
	casi := []struct {
		nome   string
		guasta func(b *banco, m *Motore)
		atteso string
	}{
		{"sana, scheda che codifica", func(b *banco, m *Motore) { m.Amb.Esegui = buona; apri(b) }, "VERDE"},
		// fase 19: la strada Vulkan Video (AMD, NVIDIA) è «hardware» come VA-API
		{"sana, scheda che codifica in Vulkan", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"hardware","codificatore":"h264_vulkan","strada":"vulkan","nodo":"/dev/dri/renderD129","motivo":"","codec":"h264","offerti":"hevc,h264","hevc":"hardware","h264":"hardware","hevc_strada":"vulkan","h264_strada":"vulkan"}`, 0)
			apri(b)
		}, "VERDE"},
		{"scheda che si apre ma non codifica il fotogramma", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"nessuno","codificatore":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":"il fotogramma non esce","codec":"h264","offerti":"","hevc":"nessuno","h264":"nessuno"}`, 1)
			apri(b)
		}, "ROSSO"},
		// fase 19: niente ripiego sul processore — nessuna scheda capace (uscita 3) è ROSSO, mai a condizioni
		{"nessuna scheda sa codificare (uscita 3)", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"nessuno","codificatore":"","nodo":"","motivo":"nessun nodo di rendering","codec":"h264","offerti":"","hevc":"nessuno","h264":"nessuno"}`, 3)
			apri(b)
		}, "ROSSO"},
		// un binario vecchio che dice ancora «software»: non è la scheda ⇒ ROSSO
		{"il vecchio ripiego software", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"software","codificatore":"libx264","nodo":"","motivo":"niente VA-API"}`, 0)
			apri(b)
		}, "ROSSO"},
		{"prova di codifica che non risponde", func(b *banco, m *Motore) { apri(b) }, "A_CONDIZIONI"},
		{"PAM rotto (modulo tolto)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "usr/lib/security/pam_unix.so"))
		}, "ROSSO"},
		{"PAM rotto (inclusione tolta)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "etc/pam.d/common-account"))
		}, "ROSSO"},
		{"PAM tolto", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "etc/pam.d/remotix"))
		}, "ROSSO"},
		{"porta richiusa da altri dopo l'installazione", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			f := &firewallFinto{b.radice}
			f.Togli("public", "7447/tcp", false)
			f.Togli("public", "7447/udp", false)
		}, "ROSSO"},
		{"firewall che non si sa leggere (ufw)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			os.WriteFile(filepath.Join(b.radice, "etc/finto-firewall"), []byte("ufw"), 0o644)
		}, "A_CONDIZIONI"},
		{"un passo disfatto da altri", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "etc/remotix/prova-motore.conf"))
		}, "ROSSO"},
	}
	for _, c := range casi {
		t.Run(c.nome, func(t *testing.T) {
			b := installaFinta(t)
			m := b.motore(t)
			c.guasta(b, m)
			r, err := m.Certifica()
			if err != nil {
				t.Fatal(err)
			}
			if r.Esito != c.atteso {
				t.Fatalf("esito %s, atteso %s: %+v %+v", r.Esito, c.atteso, r.Controlli, r.Condizioni)
			}
		})
	}
}

// R29 anche nell'installazione: con la scheda che non codifica (fase 19: e non c'è ripiego) la
// verifica è rossa e l'installazione si annulla.
func TestInstallazioneSchedaGuasta(t *testing.T) {
	b := nuovoBanco(t)
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Mestiere, p.Approvazione = "installazione", nil
	ScriviJSON(b.piano, &p)
	m := b.motore(t)
	m.Amb.Esegui = func(_ time.Duration, nome string, _ ...string) (string, int, error) {
		if nome == "remotix" {
			return `{"esito":"nessuno","codificatore":"","nodo":"","motivo":"nessun nodo di rendering"}`, 3, nil
		}
		return nessunComando(0, nome)
	}
	op, err := m.Applica(b.piano, true, "prova")
	if err != nil || op.Stato != ANNULLATA {
		t.Fatalf("%v %v", op.Stato, err)
	}
}

// La porta chiusa dal firewall (l'amministratore non ha voluto aprirla, D6): mai PASS, e una
// condizione col comando che la apre.
func TestPortaChiusa(t *testing.T) {
	b := nuovoBanco(t)
	k, c := controllaPorta(ambienteFinto(b.radice), 7447)
	if k.Esito != "FAIL" || k.Richiesto || c == nil || c.Codice != "C-AMMINISTRATORE" || c.Rimedio == "" {
		t.Fatalf("%+v %+v", k, c)
	}
}

// D14 (DECISIONI §10.23): REMOTIX e le dipendenze si aggiornano col sistema. Dopo un aggiornamento
// (versioni più nuove di quelle installate allora) la certificazione resta verde; un ritorno indietro
// fatto coi comandi del gestore è «a metà» finché `remotix-install aggiornato` non annota le versioni.
func TestCertificaDopoAggiornamento(t *testing.T) {
	b := installaFinta(t)
	m := b.motore(t)
	m.Amb.Esegui = func(_ time.Duration, nome string, _ ...string) (string, int, error) {
		if nome == "remotix" {
			return `{"esito":"hardware","codificatore":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":""}`, 0, nil
		}
		return nessunComando(0, nome)
	}
	(&firewallFinto{b.radice}).Aggiungi("public", "7447/udp", false)
	pk := filepath.Join(b.radice, "var/lib/finto-pacchetti.json")
	in := map[string]string{}
	leggiJSONFinto(pk, &in)
	esito := func(cosa string, v map[string]string) string {
		t.Helper()
		x := map[string]string{}
		for k, y := range in {
			x[k] = y
		}
		for k, y := range v {
			x[k] = y
		}
		ScriviJSON(pk, x)
		r, err := m.Certifica()
		if err != nil {
			t.Fatal(cosa, err)
		}
		return r.Esito
	}
	if e := esito("aggiornato dal sistema", map[string]string{"remotix": "0.17.0-2", "libcomune": "2.1"}); e != "VERDE" {
		t.Fatalf("dopo l'aggiornamento del sistema: %s", e)
	}
	if e := esito("tornato indietro, non annotato", map[string]string{"remotix": "0.16.0-1"}); e != "ROSSO" {
		t.Fatalf("un ritorno indietro non annotato: %s", e)
	}
	if v, err := m.AnnotaVersioni(); err != nil || v["remotix"] != "0.16.0-1" {
		t.Fatalf("annota: %v %v", v, err)
	}
	if e := esito("tornato indietro, annotato", map[string]string{"remotix": "0.16.0-1"}); e != "VERDE" {
		t.Fatalf("un ritorno indietro annotato da «aggiornato»: %s", e)
	}
}
