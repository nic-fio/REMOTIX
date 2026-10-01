package motore

import (
	"path/filepath"
	"sort"
	"strings"
)

// Le strade della codifica sulla scheda (fase 19, DECISIONI §10.27). REMOTIX codifica SOLO sulla
// scheda («niente cpu senza scheda», parola dell'utente): senza una scheda capace non si installa,
// e il controllo preliminare lo dice prima di toccare niente, con la ragione. La strada si sceglie
// per CAPACITÀ, non per marca; il verdetto è «almeno una strada attiva ha una scheda capace».
//
//   - «vulkan» (Vulkan Video): la prima per §10.27 — AMD (RADV), NVIDIA, Intel quando Mesa la rende
//     stabile. ⚠ DICHIARATA, NON ATTIVA: REMOTIX non la usa ancora. Quando c'è, si accende QUI:
//     Attiva=true, Rileva che scrive i fatti codifica.vulkan.* e Schede che li legge. Il resto
//     (Valuta, i codici RX-GPU-*, le interfacce) non cambia.
//   - «vaapi» (VA-API, libva): oggi Intel e AMD, col driver della distribuzione o con quello del
//     deposito di terzi che il catalogo nomina (H264Piattaforma, D5).

// StradaCodifica: un modo di far codificare H.264 alla scheda.
type StradaCodifica struct {
	Nome string
	// Attiva: REMOTIX la usa già. Una strada dichiarata e non attiva rileva, ma non salva nessuna
	// macchina dal rifiuto
	Attiva bool
	// Rileva: in PREFLIGHT, in sola lettura (R1): scrive i fatti della strada nel profilo
	Rileva func(a *Ambiente, p *Profilo, fam string)
	// Schede: i fornitori delle schede di QUESTA macchina che la strada sa far codificare su questa
	// piattaforma (pl nil: il catalogo non c'è ancora, si giudica dal solo profilo). Una scheda il cui
	// driver arriva da un deposito di terzi conta: il «no» al deposito lo ferma D5 (RX-H264-006).
	// Una scheda che c'è ma non si sa di che fornitore conta come «?»: la prova vera è in 7a
	Schede func(pl *Piattaforma, p *Profilo) []string
}

// StradeCodifica: nell'ordine di preferenza di §10.27.
var StradeCodifica = []StradaCodifica{
	{Nome: "vulkan", Attiva: false, Rileva: rilevaVulkan, Schede: func(*Piattaforma, *Profilo) []string { return nil }},
	{Nome: "vaapi", Attiva: true, Rileva: h264, Schede: schedeVaapi},
}

// codifica: le strade in PREFLIGHT, poi il verdetto col solo profilo (il catalogo lo rifà in Valuta,
// dove sa anche quali driver la distribuzione può dare).
func codifica(a *Ambiente, p *Profilo, fam string) {
	var attive []string
	for _, s := range StradeCodifica {
		s.Rileva(a, p, fam)
		if s.Attiva {
			attive = append(attive, s.Nome)
		}
	}
	p.Rilevato("codifica.strade", strings.Join(attive, ","), "strade.go (fase 19)")
	if cod, det := VerdettoScheda(nil, p); cod != "" {
		p.Con(cod, det)
	}
}

// rilevaVulkan: la strada dichiarata. Si annotano i driver Vulkan (i file ICD) perché la fase 19
// parta da quel che le macchine hanno; nessun verdetto.
func rilevaVulkan(a *Ambiente, p *Profilo, _ string) {
	var icd []string
	for _, g := range []string{"/usr/share/vulkan/icd.d/*.json", "/etc/vulkan/icd.d/*.json"} {
		v, _ := filepath.Glob(a.P(g))
		for _, x := range v {
			icd = append(icd, strings.TrimSuffix(filepath.Base(x), ".json"))
		}
	}
	sort.Strings(icd)
	nota := "strada dichiarata, non ancora attiva in REMOTIX (fase 19, Vulkan Video)"
	if len(icd) > 0 {
		nota += "; ICD: " + strings.Join(icd, ",")
	}
	p.Metti(Fatto{Chiave: "codifica.vulkan", Valore: "non attiva", Stato: RILEVATO, Fonte: "/usr/share/vulkan/icd.d", Nota: nota})
}

// schedeVaapi: le schede Intel e AMD che codificano H.264 via VA-API su questa piattaforma.
func schedeVaapi(pl *Piattaforma, p *Profilo) []string {
	if p.V("scheda.nodi") == "nessuno" {
		return nil
	}
	forn, noti := fornitoriScheda(p)
	if !noti {
		return []string{"?"}
	}
	intel, amd, _ := famigliaDriver(p)
	senza := map[string]bool{"Intel": intel == "senza", "AMD": amd == "senza"}
	var r []string
	for _, f := range []string{"Intel", "AMD"} {
		if !forn[f] {
			continue
		}
		if pl != nil && !pl.H264.codificaPer(f, senza[f]) {
			continue
		}
		r = append(r, f)
	}
	return r
}

// VerdettoScheda: il controllo della scheda (fase 19). "" se almeno una strada ATTIVA ha una scheda
// capace (o se non si sa: i nodi non letti non sono un rifiuto); altrimenti il codice BLOCCANTE e il
// dettaglio, dal caso più preciso al più generale.
func VerdettoScheda(pl *Piattaforma, p *Profilo) (codice, dettaglio string) {
	nodi := p.V("scheda.nodi")
	if nodi == "" {
		return "", ""
	}
	for _, s := range StradeCodifica {
		if s.Attiva && len(s.Schede(pl, p)) > 0 {
			return "", ""
		}
	}
	forn, _ := fornitoriScheda(p)
	var nomi []string
	for f := range forn {
		nomi = append(nomi, f)
	}
	sort.Strings(nomi)
	switch {
	case nodi == "nessuno":
		return "RX-GPU-003", ""
	case p.V("scheda.nvidia_proprietaria") == "si":
		return "RX-GPU-004", strings.Join(nomi, ", ")
	case forn["Intel"] || forn["AMD"]:
		// c'è una scheda della strada VA-API, ma su questa piattaforma non codifica e nessun driver
		// del catalogo la completa (AMD su RHEL e derivate; un driver senza H.264 e niente da aggiungere)
		var d []string
		if pl != nil && pl.H264.AmdSenzaVaapi && forn["AMD"] {
			d = append(d, "AMD su "+pl.Nome+": Mesa costruita senza VA-API")
		}
		if f := p.V("h264.famiglia_driver"); f != "" {
			d = append(d, f)
		}
		return "RX-GPU-006", strings.Join(d, "; ")
	}
	return "RX-GPU-005", strings.Join(nomi, ", ")
}
