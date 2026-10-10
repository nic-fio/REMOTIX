package motore

// Gli altri pezzi della macchina finta: un gestore di pacchetti (archivio installato e un
// deposito in file JSON, transazione che si può interrompere a metà), lo stato acceso/spento delle
// unità e il bersaglio d'avvio, le sessioni di logind.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"testing"
)

type pacchettoFinto struct {
	Versione string   `json:"versione"`
	Dipende  []string `json:"dipende,omitempty"`
}

type gestoreFinto struct{ radice string }

func (g *gestoreFinto) p(x string) string { return filepath.Join(g.radice, "var/lib", x) }

func leggiJSONFinto(p string, v any) {
	if b, err := os.ReadFile(p); err == nil {
		json.Unmarshal(b, v)
	}
}

func (g *gestoreFinto) installati() map[string]string {
	m := map[string]string{}
	leggiJSONFinto(g.p("finto-pacchetti.json"), &m)
	return m
}

func (g *gestoreFinto) deposito() map[string]pacchettoFinto {
	m := map[string]pacchettoFinto{}
	leggiJSONFinto(g.p("finto-deposito.json"), &m)
	return m
}

func (g *gestoreFinto) Nome() string { return "finto" }

func (g *gestoreFinto) Versioni(nomi []string) (map[string]string, error) {
	in := g.installati()
	r := map[string]string{}
	for _, n := range nomi {
		r[n] = in[n]
	}
	return r, nil
}

// chiusura: i pacchetti da installare (file + nomi + dipendenze), nell'ordine.
func (g *gestoreFinto) chiusura(file, nomi []string) ([]Artefatto, error) {
	dep := g.deposito()
	in := g.installati()
	var r []Artefatto
	visti := map[string]bool{}
	var visita func(n string, pk pacchettoFinto, origine, f string) error
	visita = func(n string, pk pacchettoFinto, origine, f string) error {
		if visti[n] {
			return nil
		}
		visti[n] = true
		for _, d := range pk.Dipende {
			dp, ok := dep[d]
			if !ok {
				return fmt.Errorf("dipendenza %s non nel deposito", d)
			}
			if err := visita(d, dp, "repo", ""); err != nil {
				return err
			}
		}
		if in[n] == pk.Versione {
			return nil
		}
		a := Artefatto{Nome: n, Versione: pk.Versione, Origine: origine, File: f, Esito: "new"}
		if in[n] != "" {
			a.Esito, a.Prima = "upgraded", in[n]
		}
		r = append(r, a)
		return nil
	}
	for _, f := range file {
		var pk struct {
			Nome string `json:"nome"`
			pacchettoFinto
		}
		leggiJSONFinto(f, &pk)
		if err := visita(pk.Nome, pk.pacchettoFinto, "file", f); err != nil {
			return nil, err
		}
	}
	for _, n := range nomi {
		pk, ok := dep[n]
		if !ok {
			return nil, fmt.Errorf("%s non nel deposito", n)
		}
		if err := visita(n, pk, "repo", ""); err != nil {
			return nil, err
		}
	}
	return r, nil
}

func (g *gestoreFinto) Risolvi(cache string, file, nomi []string) ([]Artefatto, error) {
	r, err := g.chiusura(file, nomi)
	sort.Slice(r, func(i, j int) bool { return r[i].Nome < r[j].Nome })
	return r, err
}

func (g *gestoreFinto) Installa(cache string, file, nomi []string) error {
	r, err := g.chiusura(file, nomi)
	if err != nil {
		return err
	}
	os.WriteFile(g.p("finto-pacchetti.transazione"), nil, 0o644)
	for i, a := range r {
		in := g.installati()
		in[a.Nome] = a.Versione
		b, _ := json.Marshal(in)
		if err := ScriviAtomico(g.p("finto-pacchetti.json"), b, 0o644); err != nil {
			return err
		}
		if a.Nome == "sddm" { // il postinst di un display manager: abilita, e accende se policy-rc.d non lo ferma
			os.WriteFile(filepath.Join(g.radice, "etc/systemd/system/sddm.service"), []byte("[Unit]\n"), 0o644)
			u := &unitaFinte{g.radice}
			u.Abilita("sddm.service")
			if _, err := os.Stat(filepath.Join(g.radice, "usr/sbin/policy-rc.d")); err != nil {
				u.Avvia("sddm.service")
			}
			u.ImpostaPredefinito("graphical.target")
		}
		if i == 0 {
			punto("pacchetti-a-meta", "")
		}
	}
	return os.Remove(g.p("finto-pacchetti.transazione"))
}

// SimulaTogli: chi dipende (anche di rimbalzo) dai nomi dati, fra gli installati.
func (g *gestoreFinto) SimulaTogli(nomi []string, purge bool) ([]string, error) {
	in := g.installati()
	dep := g.deposito()
	via := map[string]bool{}
	for _, n := range nomi {
		via[n] = true
	}
	var altri []string
	for cambiato := true; cambiato; {
		cambiato = false
		for _, n := range chiaviOrdinate(in) {
			if via[n] {
				continue
			}
			for _, d := range dep[n].Dipende {
				if via[d] {
					via[n], cambiato = true, true
					altri = append(altri, n)
					break
				}
			}
		}
	}
	return altri, nil
}

func (g *gestoreFinto) Togli(nomi []string, purge bool) error {
	in := g.installati()
	if err := soloLoro(g, nomi, purge); err != nil {
		return err
	}
	for _, n := range nomi {
		delete(in, n)
		if n == "sddm" {
			os.Remove(filepath.Join(g.radice, "etc/systemd/system/sddm.service"))
		}
	}
	b, _ := json.Marshal(in)
	return ScriviAtomico(g.p("finto-pacchetti.json"), b, 0o644)
}

func (g *gestoreFinto) Integro() (bool, string, error) {
	if _, err := os.Stat(g.p("finto-pacchetti.transazione")); err == nil {
		return false, "transazione a metà", nil
	}
	return true, "", nil
}

func (g *gestoreFinto) Ripara() error {
	os.Remove(g.p("finto-pacchetti.transazione"))
	return nil
}

// ---- unità: acceso/spento, bersaglio d'avvio

func (u *unitaFinte) attive() string { return filepath.Join(u.radice, "var/lib/finto-attive.json") }

func (u *unitaFinte) Attiva(n string) (string, error) {
	if leggiMappa(u.attive())[n] {
		return "active", nil
	}
	return "inactive", nil
}
func (u *unitaFinte) Avvia(n string) error {
	m := leggiMappa(u.attive())
	m[n] = true
	return scriviMappa(u.attive(), m)
}
func (u *unitaFinte) Ferma(n string) error {
	m := leggiMappa(u.attive())
	delete(m, n)
	return scriviMappa(u.attive(), m)
}
func (u *unitaFinte) Ricarica(string) error { return nil }
func (u *unitaFinte) Predefinito() (string, error) {
	b, err := os.ReadFile(filepath.Join(u.radice, "var/lib/finto-predefinito"))
	if err != nil {
		return "graphical.target", nil
	}
	return string(b), nil
}
func (u *unitaFinte) ImpostaPredefinito(b string) error {
	return ScriviAtomico(filepath.Join(u.radice, "var/lib/finto-predefinito"), []byte(b), 0o644)
}

// ---- sessioni di logind

type sessioniFinte struct{ radice string }

func (s *sessioniFinte) file() string { return filepath.Join(s.radice, "var/lib/finto-sessioni.json") }

func (s *sessioniFinte) Elenco() ([]Sessione, error) {
	var l []Sessione
	leggiJSONFinto(s.file(), &l)
	return l, nil
}

func (s *sessioniFinte) Segnale(id string, sg int32) error { return s.Termina(id) }

// il desktop nel gestore d'utente, finto: un numero di processi per persona
func (s *sessioniFinte) grafica() string {
	return filepath.Join(s.radice, "var/lib/finto-grafica.json")
}
func (s *sessioniFinte) Grafici(u string) (int, error) {
	m := map[string]int{}
	leggiJSONFinto(s.grafica(), &m)
	return m[u], nil
}
func (s *sessioniFinte) ChiudiGrafica(u string) ([]string, error) {
	m := map[string]int{}
	leggiJSONFinto(s.grafica(), &m)
	delete(m, u)
	b, _ := json.Marshal(m)
	return []string{"graphical-session.target"}, ScriviAtomico(s.grafica(), b, 0o644)
}

func (s *sessioniFinte) Termina(id string) error {
	l, _ := s.Elenco()
	var r []Sessione
	for _, x := range l {
		if x.ID != id {
			r = append(r, x)
		}
	}
	b, _ := json.Marshal(r)
	return ScriviAtomico(s.file(), b, 0o644)
}

// differenzeDopoAnnullo: la macchina com'era, SALVO l'unica modifica INDIRETTA che il piano di prova
// fa e che il ritorno indietro non disfa per regola (§6.6.4): libcomune aggiornata da 1.0 a 2.0.
func differenzeDopoAnnullo(t testing.TB, prima, dopo map[string]string) []string {
	agg := Sha256([]byte(`{"bash":"5.2","libcomune":"2.0"}`))
	k := "var/lib/finto-pacchetti.json"
	if dopo[k] == "-rw-r--r-- "+agg[:16] {
		p2 := map[string]string{}
		for x, v := range prima {
			p2[x] = v
		}
		p2[k] = dopo[k]
		return differenze(p2, dopo)
	}
	return differenze(prima, dopo)
}
