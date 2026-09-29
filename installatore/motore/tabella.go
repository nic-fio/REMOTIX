package motore

import (
	"fmt"
	"strings"
)

// TabellaVersioni genera dal catalogo le tabelle di §3.1 (le distribuzioni, i fuori, le versioni
// minime dei componenti). Il catalogo è la FONTE UNICA: il manuale tecnico si rigenera da qui a
// ogni rilascio, non si ricopia a mano.
func TabellaVersioni(c *Catalogo) string {
	var b strings.Builder
	fmt.Fprintf(&b, "*Generata da remotix-install catalogo --tabella, catalogo %s (scade il %s).*\n\n", c.Versione, c.Scadenza)
	fmt.Fprintf(&b, "**Le distribuzioni**\n\n| distribuzione | versione minima | stato | desktop | condizioni |\n|---|---|---|---|---|\n")
	for _, p := range c.Piattaforme {
		var desk, cond []string
		visti := map[string]bool{}
		metti := func(x string) {
			if !visti[x] {
				visti[x] = true
				cond = append(cond, x)
			}
		}
		if p.H264.Deposito != "" {
			metti("H.264: " + c.Depositi[p.H264.Deposito].Nome + " (" + c.Depositi[p.H264.Deposito].Decisione + ")")
		}
		for _, d := range DESKTOP {
			dc, ok := p.Desktop[d]
			if !ok || !dc.Supportato {
				continue
			}
			desk = append(desk, NomeDesktop(d))
			for _, k := range dc.Componenti {
				if k == "labwc" {
					continue // lo porta sempre il pacchetto per XFCE e LXQt: non è una particolarità
				}
				metti("`" + k + "` (" + NomeDesktop(d) + ")")
			}
			for _, k := range dc.Depositi {
				metti(c.Depositi[k].Nome + " (" + NomeDesktop(d) + ")")
			}
			for _, k := range dc.Limiti {
				metti(k)
			}
			// su openSUSE il pattern lxqt porta il carattere scalabile solo come raccomandato (§11.1)
			if d == "lxqt" && dc.ServeCarattere && p.Famiglia == "suse" {
				metti("un carattere scalabile per LXQt (`" + c.CarattereScalabile["suse"] + "`)")
			}
		}
		if len(cond) == 0 {
			cond = []string{"—"}
		}
		fmt.Fprintf(&b, "| %s | %s | %s | %s | %s |\n", p.Distribuzione, grassettoVersione(p.EtichettaVersione),
			statoPiattaforma(p), strings.Join(desk, ", "), strings.Join(cond, "; "))
	}
	for _, p := range c.Piattaforme {
		for _, d := range p.Derivate {
			v := d.VersioneMinima
			if v == "" {
				v = strings.Join(d.Versioni, ", ")
				if v == "*" {
					v = "rolling"
				}
			}
			nota := "come " + p.Distribuzione
			if d.Nota != "" {
				nota += "; " + d.Nota
			}
			fmt.Fprintf(&b, "| %s | %s | compatibile, non certificata | come %s | %s |\n", d.Nome, v, p.Nome, nota)
		}
	}
	fmt.Fprintf(&b, "\n**Fuori, e perché**\n\n")
	for _, e := range c.Escluse {
		fmt.Fprintf(&b, "- %s %s: %s\n", e.ID, strings.Join(e.Versioni, ", "), e.Motivo)
	}
	for _, x := range c.FuoriSempre {
		fmt.Fprintf(&b, "- %s\n", x)
	}
	fmt.Fprintf(&b, "\n**Le versioni minime dei componenti**\n\n| componente | minimo | perché |\n|---|---|---|\n")
	for _, k := range c.ComponentiMinimi {
		fmt.Fprintf(&b, "| %s | %s | %s |\n", k.Componente, k.Minimo, k.Perche)
	}
	return b.String()
}

func grassettoVersione(s string) string {
	primo, resto, _ := strings.Cut(s, " ")
	if resto != "" {
		return "**" + primo + "** " + resto
	}
	return "**" + primo + "**"
}

func statoPiattaforma(p Piattaforma) string {
	switch {
	case p.Matrice && p.GiroIntero != "":
		return "certificata (giro intero del " + p.GiroIntero + ")"
	case p.Matrice:
		return "nella matrice: certificata al giro intero (T10)"
	}
	return "analizzata, fuori dalla matrice"
}
