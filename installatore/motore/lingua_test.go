package motore

import (
	"os"
	"path/filepath"
	"regexp"
	"testing"
)

// DECISIONI §10.15: la lingua dall'ambiente, nell'ordine LANGUAGE, LC_ALL, LC_MESSAGES, LANG.
func TestLinguaDaAmbiente(t *testing.T) {
	casi := []struct {
		env    map[string]string
		attesa Lingua
	}{
		{map[string]string{"LANG": "it_IT.UTF-8"}, IT},
		{map[string]string{"LANG": "en_US.UTF-8"}, EN},
		{map[string]string{}, EN},
		{map[string]string{"LANGUAGE": "it:en", "LANG": "en_US.UTF-8"}, IT},
		{map[string]string{"LANGUAGE": "de", "LANG": "it_IT.UTF-8"}, EN}, // la prima indicata decide
		{map[string]string{"LC_ALL": "C", "LANG": "it_IT.UTF-8"}, EN},
		{map[string]string{"LC_MESSAGES": "it_CH.UTF-8"}, IT},
	}
	for _, c := range casi {
		if got := LinguaDaAmbiente(func(k string) string { return c.env[k] }); got != c.attesa {
			t.Errorf("%v: %s, attesa %s", c.env, got, c.attesa)
		}
	}
}

// Ogni codice ha il suo inglese; ogni chiave usata esiste, con tutte e due le lingue.
func TestTesti(t *testing.T) {
	for c := range Codici {
		if e, ok := codiciInglese[c]; !ok || e[0] == "" {
			t.Errorf("%s senza inglese", c)
		}
		if (Codici[c].Rimedio == "") != (codiciInglese[c][1] == "") {
			t.Errorf("%s: rimedio in una lingua sola", c)
		}
	}
	for c := range codiciInglese {
		if _, ok := Codici[c]; !ok {
			t.Errorf("%s in inglese ma non in italiano", c)
		}
	}
	for k, v := range testi {
		if v.It == "" || v.En == "" {
			t.Errorf("%s: una lingua vuota", k)
		}
	}
	usate := regexp.MustCompile(`\bT\("([^"]+)"\s*[,)]`)
	voci, _ := filepath.Glob("*.go")
	voci2, _ := filepath.Glob("../cmd/remotix-install/*.go")
	for _, f := range append(voci, voci2...) {
		b, _ := os.ReadFile(f)
		for _, m := range usate.FindAllStringSubmatch(string(b), -1) {
			if _, ok := testi[m[1]]; !ok {
				t.Errorf("%s usa la chiave %q, che non c'è", f, m[1])
			}
		}
	}
	for _, s := range TuttiGliStati() {
		if _, ok := testi["stato."+string(s)]; !ok {
			t.Errorf("manca il nome dello stato %s", s)
		}
	}
	ImpostaLingua("en")
	if Msg("RX-PIANO-001", "").Testo != codiciInglese["RX-PIANO-001"][0] {
		t.Error("in inglese il messaggio resta italiano")
	}
	ImpostaLingua("it")
	if Msg("RX-PIANO-001", "").Testo != Codici["RX-PIANO-001"].Testo {
		t.Error("in italiano il messaggio non è italiano")
	}
	linguaAttuale = LinguaDaAmbiente(os.Getenv)
}
