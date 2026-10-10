package motore

import (
	"slices"
	"strings"
	"testing"
)

// zonaFinta: una zona di firewalld con le regole vive e permanenti, il file in /etc (nasce alla
// prima scrittura permanente, come in firewalld) e il conto delle scritture (T6).
type zonaFinta struct {
	conosce   bool
	vive      map[string]bool
	perm      []string // le regole permanenti, in ordine
	altro     string   // un'altra impostazione permanente (l'amministratore la cambia)
	fileInEtc bool
	scritture int
	diSerie   int // quante volte è stata rimessa di serie
}

func nuovaZonaFinta(conosce, fileInEtc bool) *zonaFinta {
	return &zonaFinta{conosce: conosce, vive: map[string]bool{}, perm: []string{"service:ssh"}, fileInEtc: fileInEtc}
}

func (z *zonaFinta) Nome() string                     { return "firewalld" }
func (z *zonaFinta) ZonaPredefinita() (string, error) { return "public", nil }
func (z *zonaFinta) HaPorta(_, r string, perm bool) (bool, error) {
	if perm {
		return slices.Contains(z.perm, r), nil
	}
	return z.vive[r], nil
}
func (z *zonaFinta) Aggiungi(_, r string, perm bool) error {
	if perm {
		return z.AggiornaPermanente("", []string{r}, nil)
	}
	z.vive[r] = true
	return nil
}
func (z *zonaFinta) Togli(_, r string, perm bool) error {
	if perm {
		return z.AggiornaPermanente("", nil, []string{r})
	}
	delete(z.vive, r)
	return nil
}
func (z *zonaFinta) Conosce(string) (bool, error) { return z.conosce, nil }
func (z *zonaFinta) StatoPermanente(_ string, senza []string) (string, bool, error) {
	var r []string
	for _, x := range z.perm {
		if !slices.Contains(senza, x) {
			r = append(r, x)
		}
	}
	slices.Sort(r)
	return strings.Join(r, ",") + "|" + z.altro, !z.fileInEtc, nil
}
func (z *zonaFinta) AggiornaPermanente(_ string, agg, togli []string) error {
	var r []string
	for _, x := range z.perm {
		if !slices.Contains(togli, x) {
			r = append(r, x)
		}
	}
	for _, x := range agg {
		if !slices.Contains(r, x) {
			r = append(r, x)
		}
	}
	z.perm = r
	z.fileInEtc = true
	z.scritture++
	return nil
}
func (z *zonaFinta) RimettiDiSerie(string) error {
	z.perm, z.altro, z.fileInEtc = []string{"service:ssh"}, "", false
	z.diSerie++
	return nil
}

func provaFirewall(t *testing.T, z *zonaFinta, tocca func()) (*firewallAz, primaFirewall) {
	t.Helper()
	a, err := nuovaFirewall(PianoFirewall("firewall", "7447"))
	if err != nil {
		t.Fatal(err)
	}
	f := a.(*firewallAz)
	c := &Contesto{Amb: &Ambiente{Firewall: z}}
	prima, orig, err := f.Fotografa(c)
	if err != nil || orig != DIRETTA {
		t.Fatalf("fotografa: %v %v", orig, err)
	}
	if err := f.Fai(c, prima); err != nil {
		t.Fatal(err)
	}
	if e, det, _ := f.Controlla(c, prima); e != COMPLETO {
		t.Fatalf("dopo Fai: %v %s", e, det)
	}
	if tocca != nil {
		tocca()
	}
	if err := f.Annulla(c, prima); err != nil {
		t.Fatal(err)
	}
	if ok, det, _ := f.Annullata(c, prima); !ok {
		t.Fatalf("dopo Annulla: %s", det)
	}
	p, _ := leggiPrimaFw(prima)
	return f, p
}

// T6: il servizio quando firewalld lo conosce; UNA scrittura permanente; la zona di serie torna di
// serie (il file in /etc se ne va: niente «resto public.xml»).
func TestFirewallServizioZonaDiSerie(t *testing.T) {
	z := nuovaZonaFinta(true, false)
	_, p := provaFirewall(t, z, nil)
	if p.Forma != "service" || !p.DiSerie {
		t.Fatalf("forma %q, di serie %v", p.Forma, p.DiSerie)
	}
	if z.scritture != 1 || z.diSerie != 1 || z.fileInEtc || len(z.vive) != 0 {
		t.Fatalf("scritture %d, rimessa di serie %d, file in /etc %v, vive %v", z.scritture, z.diSerie, z.fileInEtc, z.vive)
	}
}

// Il servizio che firewalld non conosce ancora (installato adesso, niente reload): le porte.
func TestFirewallPorteSenzaServizio(t *testing.T) {
	z := nuovaZonaFinta(false, true) // e la zona ha già il suo file in /etc (Alma, Tumbleweed dall'ISO)
	_, p := provaFirewall(t, z, nil)
	if p.Forma != "" || p.DiSerie {
		t.Fatalf("forma %q, di serie %v", p.Forma, p.DiSerie)
	}
	if z.diSerie != 0 || !slices.Equal(z.perm, []string{"service:ssh"}) || z.scritture != 2 {
		t.Fatalf("rimessa di serie %d, permanenti %v, scritture %d", z.diSerie, z.perm, z.scritture)
	}
}

// L'amministratore ha cambiato la zona dopo di noi: la sua modifica resta, si tolgono le sole nostre.
func TestFirewallZonaCambiataDopo(t *testing.T) {
	z := nuovaZonaFinta(true, false)
	_, _ = provaFirewall(t, z, func() { z.altro = "masquerade" })
	if z.diSerie != 0 || z.altro != "masquerade" || !slices.Equal(z.perm, []string{"service:ssh"}) {
		t.Fatalf("rimessa di serie %d, altro %q, permanenti %v", z.diSerie, z.altro, z.perm)
	}
}
