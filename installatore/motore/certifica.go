package motore

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// La certificazione della piattaforma (fase 7, §6.0; R29: su una macchina guasta apposta non deve
// mai dire verde). Oltre al «controlla» di ogni passo del piano:
//   - codifica-h264: la fa REMOTIX (`remotix --prova-codifica`, operazione.go);
//   - pam-risolta: la pila d'accesso di REMOTIX si risolve — il file c'è, ogni modulo e ogni file
//     incluso esistono. ⚠ Non è «la pila rifiuta un utente inesistente» (servirebbe caricare PAM,
//     cioè cgo o una richiesta nuova a REMOTIX, §6.5-bis): è la parte statica, e lo dice il nome;
//   - porta-firewall (7b): il firewall acceso lascia passare la porta TCP e UDP. Una porta chiusa
//     non annulla l'installazione (aprirla è la decisione D6 dell'amministratore) ma non è mai
//     verde: FAIL non richiesto + C-AMMINISTRATORE; un firewall che non si sa leggere ⇒ UNKNOWN.

// ControlliPiattaforma: i controlli oltre ai passi. fallito = un controllo RICHIESTO in FAIL.
func ControlliPiattaforma(a *Ambiente, porta int) (k []Controllo, cond []Condizione, fallito bool) {
	c, cd := provaCodifica(a)
	k = append(k, c)
	if cd != nil {
		cond = append(cond, *cd)
	}
	if c.Esito == "FAIL" {
		fallito = true
	}
	p := controllaPAM(a)
	k = append(k, p)
	if p.Esito == "FAIL" {
		fallito = true
	} else if p.Esito == "UNKNOWN" {
		cond = append(cond, Condizione{Codice: "C-LIMITE", Testo: T("cond.pam_ignota", p.Dettaglio)})
	}
	f, fc := controllaPorta(a, porta)
	k = append(k, f)
	if fc != nil {
		cond = append(cond, *fc)
	}
	return
}

var cartelleModuliPAM = []string{"/usr/lib/security", "/usr/lib64/security", "/lib/security", "/lib64/security",
	"/usr/lib/x86_64-linux-gnu/security", "/lib/x86_64-linux-gnu/security", "/usr/lib/aarch64-linux-gnu/security"}

// controllaPAM segue la pila da /etc/pam.d/remotix (o /usr/lib/pam.d/remotix).
func controllaPAM(a *Ambiente) Controllo {
	k := Controllo{ID: "pam-risolta", Cosa: T("ver.pam"), Richiesto: true}
	f := trovaPam(a, "remotix")
	if f == "" {
		k.Esito, k.Dettaglio = "FAIL", "the remotix file is missing in /etc/pam.d and /usr/lib/pam.d"
		return k
	}
	moduli := 0
	visti := map[string]bool{}
	var guasto string
	var segui func(file string, profondita int)
	segui = func(file string, profondita int) {
		if guasto != "" || visti[file] || profondita > 8 {
			return
		}
		visti[file] = true
		t, ok := leggi(a, file)
		if !ok {
			guasto = file + " cannot be read"
			return
		}
		for _, riga := range strings.Split(t, "\n") {
			riga = strings.TrimSpace(riga)
			if riga == "" || strings.HasPrefix(riga, "#") {
				continue
			}
			c := strings.Fields(riga)
			if c[0] == "@include" && len(c) > 1 {
				g := trovaPam(a, c[1])
				if g == "" {
					guasto = file + ": @include " + c[1] + " is missing"
					return
				}
				segui(g, profondita+1)
				continue
			}
			if len(c) < 3 {
				continue
			}
			tipo := strings.TrimPrefix(c[0], "-")
			if tipo != "auth" && tipo != "account" && tipo != "session" && tipo != "password" {
				continue
			}
			controllo, resto := c[1], c[2:]
			if strings.HasPrefix(controllo, "[") { // [success=1 default=ignore]
				for len(resto) > 0 && !strings.HasSuffix(controllo, "]") {
					controllo += " " + resto[0]
					resto = resto[1:]
				}
			}
			if len(resto) == 0 {
				continue
			}
			if controllo == "include" || controllo == "substack" {
				g := trovaPam(a, resto[0])
				if g == "" {
					guasto = file + ": " + controllo + " " + resto[0] + " is missing"
					return
				}
				segui(g, profondita+1)
				continue
			}
			mod := resto[0]
			facoltativo := strings.HasPrefix(c[0], "-") // «-session»: il modulo può mancare
			if !moduloPAM(a, mod) && !facoltativo {
				guasto = file + ": the module " + mod + " is missing"
				return
			}
			moduli++
		}
	}
	segui(f, 0)
	if guasto != "" {
		k.Esito, k.Dettaglio = "FAIL", guasto
		return k
	}
	k.Esito, k.Dettaglio = "PASS", f+": "+strconv.Itoa(moduli)+" modules, all present"
	return k
}

func moduloPAM(a *Ambiente, m string) bool {
	if filepath.IsAbs(m) {
		_, err := os.Stat(a.P(m))
		return err == nil
	}
	for _, c := range cartelleModuliPAM {
		if _, err := os.Stat(a.P(filepath.Join(c, m))); err == nil {
			return true
		}
	}
	return false
}

func controllaPorta(a *Ambiente, porta int) (Controllo, *Condizione) {
	ps := strconv.Itoa(porta)
	k := Controllo{ID: "porta-firewall", Cosa: T("ver.porta", ps), Richiesto: false}
	if a.Firewall == nil {
		k.Esito, k.Dettaglio = "UNKNOWN", "firewall not read"
		return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
	}
	switch g := a.Firewall.Nome(); g {
	case "nessuno":
		k.Esito, k.Dettaglio = "PASS", T("ver.porta_nessuno")
		return k, nil
	case "firewalld":
		zona, err := a.Firewall.ZonaPredefinita()
		if err != nil {
			k.Esito, k.Dettaglio = "UNKNOWN", err.Error()
			return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
		}
		var chiuse []string
		for _, proto := range []string{"tcp", "udp"} {
			ok, err := a.Firewall.HaPorta(zona, ps+"/"+proto, false)
			if err != nil {
				k.Esito, k.Dettaglio = "UNKNOWN", err.Error()
				return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
			}
			if !ok {
				if fw, isD := a.Firewall.(*firewalldDBus); isD {
					if porte, err := fw.PorteVive(zona); err == nil && portaInIntervalli(porte, porta, proto) {
						continue
					}
				}
				chiuse = append(chiuse, ps+"/"+proto)
			}
		}
		if len(chiuse) == 0 {
			k.Esito, k.Dettaglio = "PASS", "firewalld, zona "+zona+": aperta TCP e UDP"
			return k, nil
		}
		k.Esito, k.Dettaglio = "FAIL", "firewalld, zona "+zona+": chiusa "+strings.Join(chiuse, " ")
		return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_chiusa", strings.Join(chiuse, " ")),
			Rimedio: "firewall-cmd --permanent --add-port=" + ps + "/tcp --add-port=" + ps + "/udp && firewall-cmd --reload"}
	default:
		k.Esito, k.Dettaglio = "UNKNOWN", g+": its rules are not evaluated yet"
		return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
	}
}

// Certificazione: il rapporto di `remotix-install certifica` (§6.6.11: si rifanno i controlli
// sull'installazione confermata, e si dice che cosa è ancora come allora).
type Certificazione struct {
	Formato    string       `json:"formato"`
	Oggetto    string       `json:"oggetto"` // "certificazione"
	Operazione string       `json:"operazione"`
	Controlli  []Controllo  `json:"controlli"`
	Condizioni []Condizione `json:"condizioni"`
	Esito      string       `json:"esito"` // VERDE · A_CONDIZIONI · ROSSO
}

// Certifica rifà, in sola lettura, i controlli dell'installazione confermata.
func (m *Motore) Certifica() (*Certificazione, error) {
	in, err := m.ControllaInstallazione()
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(m.Cartella, in.Operazione)
	var pn Piano
	if err := LeggiJSON(filepath.Join(dir, "piano.json"), &pn); err != nil {
		return nil, err
	}
	ev, err := LeggiRegistro(filepath.Join(dir, "registro.jsonl"))
	if err != nil {
		return nil, err
	}
	r := &Certificazione{Formato: Formato, Oggetto: "certificazione", Operazione: in.Operazione, Condizioni: []Condizione{}}
	rosso := false
	for _, ap := range pn.Azioni {
		var intz *Evento
		for i := range ev {
			if ev[i].Azione == ap.ID && ev[i].Tipo == EvIntenzione {
				intz = &ev[i]
				break
			}
		}
		k := Controllo{ID: ap.ID, Cosa: ap.ComeSiVerifica, Richiesto: true}
		a, err := NuovaAzione(ap)
		switch {
		case err != nil || intz == nil:
			k.Esito, k.Dettaglio = "UNKNOWN", "no intention in the log"
		default:
			e, det, err := a.Controlla(&Contesto{Amb: m.Amb, Cartella: dir, P: ap}, intz.Prima)
			switch {
			case err != nil:
				k.Esito, k.Dettaglio = "UNKNOWN", err.Error()
			case e == COMPLETO:
				k.Esito, k.Dettaglio = "PASS", det
			default:
				k.Esito, k.Dettaglio = "FAIL", string(e)+": "+det
				rosso = true
			}
		}
		r.Controlli = append(r.Controlli, k)
	}
	porta := m.Porta
	if porta == 0 {
		porta = 7447
	}
	k, cond, fallito := ControlliPiattaforma(m.Amb, porta)
	r.Controlli = append(r.Controlli, k...)
	r.Condizioni = append(r.Condizioni, cond...)
	tuttiPass := true
	for _, x := range r.Controlli {
		if x.Esito != "PASS" {
			tuttiPass = false
		}
	}
	switch {
	case rosso || fallito:
		r.Esito = "ROSSO"
	case tuttiPass && len(r.Condizioni) == 0:
		r.Esito = "VERDE"
	default:
		r.Esito = "A_CONDIZIONI" // ⛔ UNKNOWN non è mai PASS, una condizione non è mai verde (R29, R32)
	}
	return r, nil
}
