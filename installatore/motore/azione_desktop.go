package motore

import (
	"os"
	"strings"
)

// installa-desktop: il desktop che manca (DECISIONI §10.7, R38), dagli archivi della distribuzione
// col suo gruppo di pacchetti ufficiale (lo stesso di `vesti`, §7.2), SENZA cambiare come parte la
// macchina: niente schermata d'accesso locale, niente avvio in grafica. È installa-pacchetti con
// in più la «grafica» di prima e dopo:
//   - prima: il bersaglio d'avvio e lo stato dei display manager conosciuti; su Debian e Ubuntu un
//     /usr/sbin/policy-rc.d nostro (esce 101: il meccanismo di Debian per dire agli script dei
//     pacchetti di NON accendere servizi durante la transazione), tolto subito dopo;
//   - dopo: il bersaglio d'avvio torna quello di prima; un display manager che l'installazione ha
//     abilitato si disabilita, uno che ha acceso si spegne. Il pacchetto del display manager
//     resta installato (i gruppi ufficiali lo esigono), spento: si dichiara.
// Reversibilità AL_MEGLIO (§10 del documento: toglierlo non rende la macchina identica).

func init() {
	registraTipo("install-desktop", func(p AzionePiano) (Azione, error) {
		q := p
		q.Parametri = map[string]string{"names": p.Parametri["names"], "no_graphics": "yes"}
		return nuovaPacchetti(q)
	})
}

// PianoDesktop prepara il passo del piano: i pacchetti vengono dal catalogo.
func PianoDesktop(id, desktop, nomi string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "install-desktop",
		Parametri:      map[string]string{"desktop": desktop, "names": nomi},
		Descrizione:    T("az.desktop", NomeDesktop(desktop)),
		ComeSiFa:       T("az.desktop.fa", NomeDesktop(desktop)),
		ComeSiVerifica: T("az.desktop.verifica"),
		ComeSiAnnulla:  T("az.desktop.annulla"),
		Reversibilita:  AL_MEGLIO,
	}
}

var displayManager = []string{"gdm.service", "gdm3.service", "sddm.service", "lightdm.service", "lxdm.service", "display-manager.service"}

const policyRcd = "/usr/sbin/policy-rc.d"
const policyRcdNostro = "#!/bin/sh\n# REMOTIX: no services started while the desktop is installed (removed right after)\nexit 101\n"

type primaGrafica struct {
	Predefinito string            `json:"default"`
	DM          map[string]string `json:"dm"`     // unità → "file attivo" di prima
	Debian      bool              `json:"debian"` // si usa policy-rc.d
}

func statoDM(c *Contesto, u string) string {
	f, err := c.Amb.Unita.Stato(u)
	if err != nil {
		f = "?"
	}
	a, err := c.Amb.Unita.Attiva(u)
	if err != nil {
		a = "?"
	}
	return f + " " + a
}

func fotografaGrafica(c *Contesto) (*primaGrafica, error) {
	d, err := c.Amb.Unita.Predefinito()
	if err != nil {
		return nil, err
	}
	g := &primaGrafica{Predefinito: d, DM: map[string]string{}, Debian: c.Amb.Famiglia == "debian"}
	for _, u := range displayManager {
		g.DM[u] = statoDM(c, u)
	}
	return g, nil
}

func (g *primaGrafica) prima(c *Contesto) error {
	if !g.Debian {
		return nil
	}
	if _, err := os.Stat(c.Amb.P(policyRcd)); err == nil {
		return nil // ce n'è già uno dell'amministratore: si usa il suo, non si tocca
	}
	return ScriviAtomico(c.Amb.P(policyRcd), []byte(policyRcdNostro), 0o755)
}

func (g *primaGrafica) togliPolicy(c *Contesto) {
	if b, err := os.ReadFile(c.Amb.P(policyRcd)); err == nil && string(b) == policyRcdNostro {
		os.Remove(c.Amb.P(policyRcd))
	}
}

// dopo: rimette come prima il bersaglio d'avvio e i display manager.
func (g *primaGrafica) dopo(c *Contesto) error {
	g.togliPolicy(c)
	if d, err := c.Amb.Unita.Predefinito(); err == nil && d != g.Predefinito {
		if err := c.Amb.Unita.ImpostaPredefinito(g.Predefinito); err != nil {
			return err
		}
	}
	for _, u := range displayManager {
		prima := strings.Fields(g.DM[u] + " ? ?")
		adesso := strings.Fields(statoDM(c, u) + " ? ?")
		if adesso[1] == "active" && prima[1] != "active" {
			if err := c.Amb.Unita.Ferma(u); err != nil {
				return err
			}
		}
		if adesso[0] == "enabled" && prima[0] != "enabled" && u != "display-manager.service" {
			if err := c.Amb.Unita.Disabilita(u); err != nil {
				return err
			}
		}
	}
	return nil
}

func (g *primaGrafica) rimetti(c *Contesto) error { return g.dopo(c) }

// aPosto: il bersaglio d'avvio e i display manager come prima (e nessun policy-rc.d nostro).
func (g *primaGrafica) aPosto(c *Contesto) (bool, string) {
	if b, err := os.ReadFile(c.Amb.P(policyRcd)); err == nil && string(b) == policyRcdNostro {
		return false, "ours is still there: " + policyRcd
	}
	if d, err := c.Amb.Unita.Predefinito(); err == nil && d != g.Predefinito {
		return false, "boot target " + d + ", before " + g.Predefinito
	}
	for _, u := range displayManager {
		prima := strings.Fields(g.DM[u] + " ? ?")
		adesso := strings.Fields(statoDM(c, u) + " ? ?")
		if (adesso[1] == "active" && prima[1] != "active") || (adesso[0] == "enabled" && prima[0] != "enabled" && u != "display-manager.service") {
			return false, u + " started or enabled by the installation"
		}
	}
	return true, ""
}

func (g *primaGrafica) comePrima(c *Contesto) (bool, string) { return g.aPosto(c) }
