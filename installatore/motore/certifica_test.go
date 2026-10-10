package motore

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// R29 in small: certification on a machine broken on purpose never says GREEN.
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
		{"healthy, card that encodes", func(b *banco, m *Motore) { m.Amb.Esegui = buona; apri(b) }, "GREEN"},
		// phase 19: the Vulkan Video route (AMD, NVIDIA) is «hardware» like VA-API
		{"healthy, card that encodes in Vulkan", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"hardware","codificatore":"h264_vulkan","strada":"vulkan","nodo":"/dev/dri/renderD129","motivo":"","codec":"h264","offerti":"hevc,h264","hevc":"hardware","h264":"hardware","hevc_strada":"vulkan","h264_strada":"vulkan"}`, 0)
			apri(b)
		}, "GREEN"},
		{"card that opens but does not encode the frame", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"nessuno","codificatore":"h264_vaapi","nodo":"/dev/dri/renderD128","motivo":"the frame does not come out","codec":"h264","offerti":"","hevc":"nessuno","h264":"nessuno"}`, 1)
			apri(b)
		}, "RED"},
		// phase 19: no fallback to the processor — no capable card (exit 3) is RED, never conditional
		{"no card can encode (exit 3)", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"nessuno","codificatore":"","nodo":"","motivo":"no render node","codec":"h264","offerti":"","hevc":"nessuno","h264":"nessuno"}`, 3)
			apri(b)
		}, "RED"},
		// an old binary that still says «software»: it is not the card ⇒ RED
		{"the old software fallback", func(b *banco, m *Motore) {
			m.Amb.Esegui = codifica(`{"esito":"software","codificatore":"libx264","nodo":"","motivo":"no VA-API"}`, 0)
			apri(b)
		}, "RED"},
		{"encoding test that does not answer", func(b *banco, m *Motore) { apri(b) }, "CONDITIONAL"},
		{"PAM broken (module removed)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "usr/lib/security/pam_unix.so"))
		}, "RED"},
		{"PAM broken (include removed)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "etc/pam.d/common-account"))
		}, "RED"},
		{"PAM removed", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "etc/pam.d/remotix"))
		}, "RED"},
		{"port closed by the firewall: opening it is the administrator's job (§10.36)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			f := &firewallFinto{b.radice}
			f.Togli("public", "7447/tcp", false)
			f.Togli("public", "7447/udp", false)
		}, "CONDITIONAL"},
		{"firewall that cannot be read (ufw)", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			os.WriteFile(filepath.Join(b.radice, "etc/finto-firewall"), []byte("ufw"), 0o644)
		}, "CONDITIONAL"},
		{"a step undone by others", func(b *banco, m *Motore) {
			m.Amb.Esegui = buona
			apri(b)
			os.Remove(filepath.Join(b.radice, "etc/remotix/engine-test.conf"))
		}, "RED"},
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
				t.Fatalf("outcome %s, expected %s: %+v %+v", r.Esito, c.atteso, r.Controlli, r.Condizioni)
			}
		})
	}
}

// R29 in the installation too: with the card that does not encode (phase 19: and there is no fallback) the
// verification is red and the installation is cancelled.
func TestInstallazioneSchedaGuasta(t *testing.T) {
	b := nuovoBanco(t)
	var p Piano
	LeggiJSON(b.piano, &p)
	p.Mestiere, p.Approvazione = "installation", nil
	ScriviJSON(b.piano, &p)
	m := b.motore(t)
	m.Amb.Esegui = func(_ time.Duration, nome string, _ ...string) (string, int, error) {
		if nome == "remotix" {
			return `{"esito":"nessuno","codificatore":"","nodo":"","motivo":"no render node"}`, 3, nil
		}
		return nessunComando(0, nome)
	}
	op, err := m.Applica(b.piano, true, "prova")
	if err != nil || op.Stato != ANNULLATA {
		t.Fatalf("%v %v", op.Stato, err)
	}
}

// The port closed by the firewall (opening it is the administrator's job, §10.36): never PASS, and a condition
// that says so, without commands.
func TestPortaChiusa(t *testing.T) {
	b := nuovoBanco(t)
	k, c := controllaPorta(ambienteFinto(b.radice), 7447)
	if k.Esito != "FAIL" || k.Richiesto || c == nil || c.Codice != "C-AMMINISTRATORE" || c.Testo == "" {
		t.Fatalf("%+v %+v", k, c)
	}
}

// D14 (DECISIONI §10.23): REMOTIX and the dependencies are upgraded with the system. After an upgrade
// (versions newer than those installed then) the certification stays green; a rollback
// done with the manager's commands is «half-done» until `remotix-install aggiornato` records the versions.
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
	if e := esito("upgraded by the system", map[string]string{"remotix": "0.17.0-2", "libcomune": "2.1"}); e != "GREEN" {
		t.Fatalf("after the system upgrade: %s", e)
	}
	if e := esito("rolled back, not recorded", map[string]string{"remotix": "0.16.0-1"}); e != "RED" {
		t.Fatalf("a rollback not recorded: %s", e)
	}
	if v, err := m.AnnotaVersioni(); err != nil || v["remotix"] != "0.16.0-1" {
		t.Fatalf("record: %v %v", v, err)
	}
	if e := esito("rolled back, recorded", map[string]string{"remotix": "0.16.0-1"}); e != "GREEN" {
		t.Fatalf("a rollback recorded by «aggiornato»: %s", e)
	}
}
