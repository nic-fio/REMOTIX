package engine

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// The platform certification (phase 7, §6.0; R29: on a machine broken on purpose it must
// never say green). Beyond the «controlla» of every step of the plan:
//   - codifica-h264: done by REMOTIX (`remotix --encoding-test`, operazione.go);
//   - pam-risolta: REMOTIX's login stack resolves — the file is there, every module and every included
//     file exist. ⚠ It is not «the stack refuses a non-existent user» (that would need loading PAM,
//     that is cgo or a new request to REMOTIX, §6.5-bis): it is the static part, and the name says so;
//   - porta-firewall (7b): the running firewall lets the TCP and UDP port through. A closed port
//     does not cancel the installation (opening it is the administrator's decision D6) but is never
//     green: non-required FAIL + C-AMMINISTRATORE; a firewall that cannot be read ⇒ UNKNOWN.

// PlatformChecks: the checks beyond the steps. has_failed = a REQUIRED check in FAIL.
func PlatformChecks(a *Environment, port int) (k []CheckReport, cond []Condition, has_failed bool) {
	c, cd := encodingTest(a)
	k = append(k, c)
	if cd != nil {
		cond = append(cond, *cd)
	}
	if c.Outcome == "FAIL" {
		has_failed = true
	}
	p := checkPAM(a)
	k = append(k, p)
	if p.Outcome == "FAIL" {
		has_failed = true
	} else if p.Outcome == "UNKNOWN" {
		cond = append(cond, Condition{Codice: "C-LIMITE", Testo: T("cond.pam_ignota", p.Detail)})
	}
	f, fc := checkPort(a, port)
	k = append(k, f)
	if fc != nil {
		cond = append(cond, *fc)
	}
	return
}

var pamModuleDirs = []string{"/usr/lib/security", "/usr/lib64/security", "/lib/security", "/lib64/security",
	"/usr/lib/x86_64-linux-gnu/security", "/lib/x86_64-linux-gnu/security", "/usr/lib/aarch64-linux-gnu/security"}

// checkPAM follows the stack from /etc/pam.d/remotix (or /usr/lib/pam.d/remotix).
func checkPAM(a *Environment) CheckReport {
	k := CheckReport{ID: "pam-resolved", What: T("ver.pam"), Requested: true}
	f := findPam(a, "remotix")
	if f == "" {
		k.Outcome, k.Detail = "FAIL", "the remotix file is missing in /etc/pam.d and /usr/lib/pam.d"
		return k
	}
	modules := 0
	seen_items := map[string]bool{}
	var fault string
	var segui func(file string, depth int)
	segui = func(file string, depth int) {
		if fault != "" || seen_items[file] || depth > 8 {
			return
		}
		seen_items[file] = true
		t, ok := load(a, file)
		if !ok {
			fault = file + " cannot be read"
			return
		}
		for _, line := range strings.Split(t, "\n") {
			line = strings.TrimSpace(line)
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			c := strings.Fields(line)
			if c[0] == "@include" && len(c) > 1 {
				g := findPam(a, c[1])
				if g == "" {
					fault = file + ": @include " + c[1] + " is missing"
					return
				}
				segui(g, depth+1)
				continue
			}
			if len(c) < 3 {
				continue
			}
			kind := strings.TrimPrefix(c[0], "-")
			if kind != "auth" && kind != "account" && kind != "session" && kind != "password" {
				continue
			}
			check, rest := c[1], c[2:]
			if strings.HasPrefix(check, "[") { // [success=1 default=ignore]
				for len(rest) > 0 && !strings.HasSuffix(check, "]") {
					check += " " + rest[0]
					rest = rest[1:]
				}
			}
			if len(rest) == 0 {
				continue
			}
			if check == "include" || check == "substack" {
				g := findPam(a, rest[0])
				if g == "" {
					fault = file + ": " + check + " " + rest[0] + " is missing"
					return
				}
				segui(g, depth+1)
				continue
			}
			mod := rest[0]
			optional := strings.HasPrefix(c[0], "-") // «-session»: the module may be missing
			if !pamModule(a, mod) && !optional {
				fault = file + ": the module " + mod + " is missing"
				return
			}
			modules++
		}
	}
	segui(f, 0)
	if fault != "" {
		k.Outcome, k.Detail = "FAIL", fault
		return k
	}
	k.Outcome, k.Detail = "PASS", f+": "+strconv.Itoa(modules)+" modules, all present"
	return k
}

func pamModule(a *Environment, m string) bool {
	if filepath.IsAbs(m) {
		_, err := os.Stat(a.P(m))
		return err == nil
	}
	for _, c := range pamModuleDirs {
		if _, err := os.Stat(a.P(filepath.Join(c, m))); err == nil {
			return true
		}
	}
	return false
}

func checkPort(a *Environment, port int) (CheckReport, *Condition) {
	ps := strconv.Itoa(port)
	k := CheckReport{ID: "firewall-port", What: T("ver.porta", ps), Requested: false}
	if a.Firewall == nil {
		k.Outcome, k.Detail = "UNKNOWN", "firewall not read"
		return k, &Condition{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
	}
	switch g := a.Firewall.Nome(); g {
	case "none":
		k.Outcome, k.Detail = "PASS", T("ver.porta_nessuno")
		return k, nil
	case "firewalld":
		zone, err := a.Firewall.DefaultZone()
		if err != nil {
			k.Outcome, k.Detail = "UNKNOWN", err.Error()
			return k, &Condition{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
		}
		var closed []string
		for _, proto := range []string{"tcp", "udp"} {
			ok, err := a.Firewall.HasPort(zone, ps+"/"+proto, false)
			if err != nil {
				k.Outcome, k.Detail = "UNKNOWN", err.Error()
				return k, &Condition{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
			}
			if !ok {
				if fw, isD := a.Firewall.(*firewalldDBus); isD {
					if ports, err := fw.LivePorts(zone); err == nil && portInRanges(ports, port, proto) {
						continue
					}
				}
				closed = append(closed, ps+"/"+proto)
			}
		}
		if len(closed) == 0 {
			k.Outcome, k.Detail = "PASS", "firewalld, zone "+zone+": open TCP and UDP"
			return k, nil
		}
		k.Outcome, k.Detail = "FAIL", "firewalld, zone "+zone+": closed "+strings.Join(closed, " ")
		return k, &Condition{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_chiusa", strings.Join(closed, " "))}
	default:
		k.Outcome, k.Detail = "UNKNOWN", g+": its rules are not evaluated yet"
		return k, &Condition{Codice: "C-AMMINISTRATORE", Testo: T("cond.porta_ignota", ps)}
	}
}

// Certification: the report of `remotix-install certify` (§6.6.11: the checks are redone
// on the confirmed installation, and it says what is still as it was then).
type Certification struct {
	Schema        string        `json:"format"`
	Obj           string        `json:"object"` // "certification"
	Operation     string        `json:"operation"`
	Verifications []CheckReport `json:"checks"`
	Condizioni    []Condition   `json:"conditions"`
	Outcome       string        `json:"result"` // GREEN · A_CONDIZIONI · RED
}

// Certify redoes, read-only, the checks of the confirmed installation.
func (m *Engine) Certify() (*Certification, error) {
	in, err := m.CheckInstallation()
	if err != nil {
		return nil, err
	}
	dir := filepath.Join(m.Folder, in.Operation)
	var pn Piano
	if err := ReadJSON(filepath.Join(dir, "plan.json"), &pn); err != nil {
		return nil, err
	}
	ev, err := ReadLog(filepath.Join(dir, "log.jsonl"))
	if err != nil {
		return nil, err
	}
	r := &Certification{Schema: Schema, Obj: "certification", Operation: in.Operation, Condizioni: []Condition{}}
	red := false
	for _, ap := range pn.Azioni {
		var intent *Event
		for i := range ev {
			if ev[i].Action == ap.ID && ev[i].Type == EvIntent {
				intent = &ev[i]
				break
			}
		}
		k := CheckReport{ID: ap.ID, What: ap.HowToVerify, Requested: true}
		a, err := NewAction(ap)
		switch {
		case err != nil || intent == nil:
			k.Outcome, k.Detail = "UNKNOWN", "no intention in the log"
		default:
			e, det, err := a.Check(&Context{Env: m.Env, Folder: dir, P: ap}, intent.Before)
			switch {
			case err != nil:
				k.Outcome, k.Detail = "UNKNOWN", err.Error()
			case e == COMPLETE:
				k.Outcome, k.Detail = "PASS", det
			default:
				k.Outcome, k.Detail = "FAIL", string(e)+": "+det
				red = true
			}
		}
		r.Verifications = append(r.Verifications, k)
	}
	port := m.Porta
	if port == 0 {
		port = 7447
	}
	k, cond, has_failed := PlatformChecks(m.Env, port)
	r.Verifications = append(r.Verifications, k...)
	r.Condizioni = append(r.Condizioni, cond...)
	allPass := true
	for _, x := range r.Verifications {
		if x.Outcome != "PASS" {
			allPass = false
		}
	}
	switch {
	case red || has_failed:
		r.Outcome = "RED"
	case allPass && len(r.Condizioni) == 0:
		r.Outcome = "GREEN"
	default:
		r.Outcome = "CONDITIONAL" // ⛔ UNKNOWN is never PASS, a condition is never green (R29, R32)
	}
	return r, nil
}
