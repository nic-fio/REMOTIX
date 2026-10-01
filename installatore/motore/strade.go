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
//   - «vulkan» (Vulkan Video): la prima per §10.27 — AMD con RADV (`[M]` 1 ott 2026: Radeon RX
//     6800, Mesa 25.0.7, H.264 e HEVC sul server), NVIDIA col driver proprietario (`[?]` non provata:
//     nel laboratorio non c'è), Intel quando Mesa la rende stabile (oggi ANV codifica solo dietro
//     ANV_DEBUG=video-encode: resta a VA-API). ⭐ ATTIVA dal 1 ott 2026: il prodotto la prova PRIMA
//     di VA-API (`src/codificatore.c`, `h264_scheda`/`hevc_scheda`) e `remotix --prova-codifica`
//     dice quale strada ha codificato (`strada`).
//   - «vaapi» (VA-API, libva): Intel e AMD, col driver della distribuzione o con quello del
//     deposito di terzi che il catalogo nomina (H264Piattaforma, D5).
//
// ⛔ Il controllo preliminare NON lancia programmi e NON apre la scheda (R1, RX-H264-001): qui si
// legge quel che c'è sul disco (i driver VA, i driver Vulkan). La prova VERA — un fotogramma
// codificato — la fa il binario di REMOTIX in 7a, dopo l'installazione, ed è lei che vale.

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
	{Nome: "vulkan", Attiva: true, Rileva: rilevaVulkan, Schede: schedeVulkan},
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

// rilevaVulkan: la sonda della strada Vulkan Video, in sola lettura: i driver Vulkan installati sono i
// file ICD del loader (/usr/share/vulkan/icd.d, /etc/vulkan/icd.d), e il nome del file dice il driver
// — `radeon_icd.x86_64.json` (RADV, AMD), `nvidia_icd.json` (il driver proprietario),
// `intel_icd.x86_64.json` (ANV), `lvp_icd` (llvmpipe: niente video), `virtio_icd`… Si scrive l'elenco
// normalizzato (senza `_icd` e senza l'architettura) in codifica.vulkan.icd; «nessuno» se non c'è
// nessun file: il loader non vedrebbe nessuna scheda, e la strada qui non c'è.
func rilevaVulkan(a *Ambiente, p *Profilo, _ string) {
	visti := map[string]bool{}
	var icd []string
	for _, g := range []string{"/usr/share/vulkan/icd.d/*.json", "/etc/vulkan/icd.d/*.json"} {
		v, _ := filepath.Glob(a.P(g))
		for _, x := range v {
			n := nomeICD(filepath.Base(x))
			if n != "" && !visti[n] {
				visti[n] = true
				icd = append(icd, n)
			}
		}
	}
	sort.Strings(icd)
	valore := strings.Join(icd, ",")
	if valore == "" {
		valore = "nessuno"
	}
	p.Rilevato("codifica.vulkan.icd", valore, "/usr/share/vulkan/icd.d")
	p.Metti(Fatto{Chiave: "codifica.vulkan", Valore: "attiva", Stato: RILEVATO, Fonte: "strade.go (fase 19)",
		Nota: "Vulkan Video, provata PRIMA di VA-API dal prodotto; la prova vera è in 7a (remotix --prova-codifica, campo strada)"})
}

// nomeICD: «radeon_icd.x86_64.json» → «radeon», «nvidia_icd.json» → «nvidia»; "" se non è un ICD.
func nomeICD(file string) string {
	n := strings.TrimSuffix(file, ".json")
	i := strings.Index(n, "_icd")
	if i < 0 {
		return ""
	}
	return n[:i]
}

// schedeVulkan: i fornitori delle schede di questa macchina che Vulkan Video sa far codificare: AMD con
// l'ICD di RADV (`radeon`), NVIDIA col driver proprietario e il suo ICD (`nvidia`). ⛔ Intel NO: ANV
// codifica solo dietro ANV_DEBUG=video-encode (sperimentale, §10.27) ⇒ resta a VA-API. Una scheda
// senza il suo ICD non conta: il loader non la vedrebbe, e la prova di 7a direbbe «nessuno».
// ⚠ Che l'ICD ci sia non vuol dire che codifichi: `[?]` la versione minima di Mesa con la codifica RADV
// di serie non è misurata (`[M]` 25.0.7 sì); chi lo dice è 7a.
func schedeVulkan(_ *Piattaforma, p *Profilo) []string {
	if p.V("scheda.nodi") == "nessuno" {
		return nil
	}
	forn, noti := fornitoriScheda(p)
	if !noti {
		return nil
	}
	icd := map[string]bool{}
	for _, n := range strings.Split(p.V("codifica.vulkan.icd"), ",") {
		icd[n] = true
	}
	var r []string
	if forn["AMD"] && icd["radeon"] {
		r = append(r, "AMD")
	}
	if forn["NVIDIA"] && icd["nvidia"] && p.V("scheda.nvidia_proprietaria") == "si" {
		r = append(r, "NVIDIA")
	}
	return r
}

// SchedaSullaStrada: la strada `nome` (attiva) sa far codificare una scheda del fornitore `f` su
// questa macchina. Serve a chi deve dire se una scheda resta FUORI (la condizione C-HARDWARE della
// NVIDIA): con Vulkan la NVIDIA proprietaria col suo ICD non è più fuori.
func SchedaSullaStrada(nome, f string, pl *Piattaforma, p *Profilo) bool {
	for _, s := range StradeCodifica {
		if s.Nome != nome || !s.Attiva {
			continue
		}
		for _, x := range s.Schede(pl, p) {
			if x == f {
				return true
			}
		}
	}
	return false
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
		// la NVIDIA proprietaria codifica SOLO in Vulkan: se si è qui, il suo ICD non c'è
		return "RX-GPU-004", strings.Join(nomi, ", ") + "; ICD Vulkan: " + nonVuoto(p.V("codifica.vulkan.icd"), "nessuno")
	case forn["Intel"] || forn["AMD"]:
		// c'è una scheda della strada VA-API, ma su questa piattaforma non codifica e nessun driver
		// del catalogo la completa (AMD su RHEL e derivate; un driver senza H.264 e niente da aggiungere)
		// — e in Vulkan non c'è (AMD senza l'ICD di RADV; Intel non c'è di serie)
		var d []string
		if pl != nil && pl.H264.AmdSenzaVaapi && forn["AMD"] {
			d = append(d, "AMD su "+pl.Nome+": Mesa costruita senza VA-API")
		}
		if f := p.V("h264.famiglia_driver"); f != "" {
			d = append(d, f)
		}
		d = append(d, "ICD Vulkan: "+nonVuoto(p.V("codifica.vulkan.icd"), "nessuno"))
		return "RX-GPU-006", strings.Join(d, "; ")
	}
	return "RX-GPU-005", strings.Join(nomi, ", ")
}
