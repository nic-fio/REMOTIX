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
		{"scheda che non codifica", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"nessuno","codificatore":"","nodo":"","motivo":"né VA-API né libx264"}`, 1)
			apri(b)
		}, "ROSSO"},
		{"solo il ripiego software", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"software","codificatore":"libx264","nodo":"","motivo":"niente VA-API"}`, 0)
			apri(b)
		}, "A_CONDIZIONI"},
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

// R29 anche nell'installazione: con la scheda che non codifica (né hardware né software) la
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
			return `{"esito":"nessuno","codificatore":"","nodo":"","motivo":"x"}`, 1, nil
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
