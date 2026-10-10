package motore

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// The platform certification (phase 7, §6.0; R29: on a machine broken on purpose it must
// never say green). Beyond the «controlla» of every step of the plan:
//   - codifica-h264: done by REMOTIX (`remotix --prova-codifica`, operazione.go);
//   - pam-risolta: REMOTIX's login stack resolves — the file is there, every module and every included
//     file exist. ⚠ It is not «the stack refuses a non-existent user» (that would need loading PAM,
//     that is cgo or a new request to REMOTIX, §6.5-bis): it is the static part, and the name says so;
//   - porta-firewall (7b): the running firewall lets the TCP and UDP port through. A closed port
//     does not cancel the installation (opening it is the administrator's decision D6) but is never
//     green: non-required FAIL + C-AMMINISTRATORE; a firewall that cannot be read ⇒ UNKNOWN.

// ControlliPiattaforma: the checks beyond the steps. fallito = a REQUIRED check in FAIL.
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

// controllaPAM follows the stack from /etc/pam.d/remotix (or /usr/lib/pam.d/remotix).
func controllaPAM(a *Ambiente) Controllo {
	k := Controllo{ID: "pam-resolved", Cosa: T("ver.pam"), Richiesto: true}
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
			facoltativo := strings.HasPrefix(c[0], "-") // «-session»: the module may be missing
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
	k := Controllo{ID: "firewall-port", Cosa: T("ver.porta", ps), Richiesto: false}
	if a.Firewall == nil {
		k.Esito, k.Dettaglio = "UNKNOWN", "firewall not read"
		return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
	}
	switch g := a.Firewall.Nome(); g {
	case "none":
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
			k.Esito, k.Dettaglio = "PASS", "firewalld, zone "+zona+": open TCP and UDP"
			return k, nil
		}
		k.Esito, k.Dettaglio = "FAIL", "firewalld, zone "+zona+": closed "+strings.Join(chiuse, " ")
		return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_chiusa", strings.Join(chiuse, " "))}
	default:
		k.Esito, k.Dettaglio = "UNKNOWN", g+": its rules are not evaluated yet"
		return k, &Condizione{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
	}
}

// Certificazione: the report of `remotix-install certifica` (§6.6.11: the checks are redone
// on the confirmed installation, and it says what is still as it was then).
type Certificazione struct {
	Formato    string       `json:"format"`
	Oggetto    string       `json:"object"` // "certification"
	Operazione string       `json:"operation"`
	Controlli  []Controllo  `json:"checks"`
	Condizioni []Condizione `json:"conditions"`
	Esito      string       `json:"result"` // VERDE · A_CONDIZIONI · ROSSO
}

// Certifica redoes, read-only, the checks of the confirmed installation.
func (m *Motore) Certifica() (*Certificazione, error) {
	in, err := m.ControllaInstallazione()
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(m.Cartella, in.Operazione)
	var pn Piano
	if err := LeggiJSON(filepath.Join(dir, "plan.json"), &pn); err != nil {
		return nil, err
	}
	ev, err := LeggiRegistro(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, err
	}
	r := &Certificazione{Formato: Formato, Oggetto: "certification", Operazione: in.Operazione, Condizioni: []Condizione{}}
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
		r.Esito = "RED"
	case tuttiPass && len(r.Condizioni) == 0:
		r.Esito = "GREEN"
	default:
		r.Esito = "CONDITIONAL" // ⛔ UNKNOWN is never PASS, a condition is never green (R29, R32)
	}
	return r, nil
}
