//go:build gui

// Package gui: la finestra dell'installatore, disegnata con Gio (DECISIONI §10.19) dal prototipo
// (grafica/installatore-prototipo/): cinque schermate, la variante senza desktop, la schermata
// «bloccata». Gira come l'utente (R37); il motore lo raggiunge rilanciando lo stesso eseguibile
// con pkexec (interfaccia.Cliente). Mostra gli oggetti del motore (interfaccia.Vista…) e raccoglie
// il consenso: nessuna logica d'installazione qui (§6.6.1, R36).
package gui

import (
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"gioui.org/app"
	"gioui.org/io/system"
	"gioui.org/layout"
	"gioui.org/op"
	"gioui.org/op/clip"
	"gioui.org/op/paint"
	"gioui.org/unit"
	"gioui.org/widget"
	"gioui.org/widget/material"

	"remotix/installatore/interfaccia"
	"remotix/installatore/motore"
)

// schermate
const (
	sAttesa = iota
	sControllo
	sScelte
	sPiano
	sAvanzamento
	sPronto
	sFine
)

// Finestra: lo stato di tutta la finestra.
type Finestra struct {
	th       *material.Theme
	logo     paint.ImageOp
	logoDim  image.Point
	mot      interfaccia.Motore
	invalida func()

	mu       sync.Mutex
	schermo  int
	attesa   string
	ctrl     *interfaccia.Controllo
	vc       *interfaccia.VistaControllo
	vs       *interfaccia.VistaScelte
	vp       *interfaccia.VistaPiano
	piano    *motore.Piano
	av       *interfaccia.Avanzamento
	eventi   []motore.EventoPubblico
	pronto   *interfaccia.VistaPronto
	fine     *interfaccia.VistaBloccata
	voci     map[string]string
	fermando bool
	nota     string // «Salvato in …»
	errPorta bool

	porta    widget.Editor
	opzioni  map[string][]*widget.Clickable
	sx, dx   widget.Clickable
	salva    widget.Clickable
	dett     widget.Clickable
	dettAp   bool
	reg      widget.Clickable
	regAp    bool
	lista    widget.List
	versioni widget.Clickable
	chiudi   bool
	portaUlt string
}

func nuova(mot interfaccia.Motore) *Finestra {
	f := &Finestra{th: tema(), mot: mot, opzioni: map[string][]*widget.Clickable{}}
	f.logo, f.logoDim = logo()
	f.porta.SingleLine = true
	f.porta.Filter = "0123456789"
	f.porta.MaxLen = 5
	f.lista.Axis = layout.Vertical
	return f
}

// Avvia apre la finestra. Va chiamata da main (Gio vuole il filo principale: app.Main).
func Avvia(mot interfaccia.Motore) error {
	f := nuova(mot)
	w := new(app.Window)
	// 1120×760 è il prototipo; 700 d'altezza perché ci stia anche su uno schermo 1280×800 col
	// pannello del desktop (`[M]` 30 set: su KDE il piede usciva dallo schermo). Il contenuto scorre.
	w.Option(app.Title(interfaccia.T("titolo.finestra")), app.Size(unit.Dp(1120), unit.Dp(700)),
		app.MinSize(unit.Dp(860), unit.Dp(560)))
	f.invalida = w.Invalidate
	errc := make(chan error, 1)
	go func() {
		errc <- f.giro(w)
		mot.Chiudi()
		os.Exit(0)
	}()
	f.controlla(7447)
	app.Main()
	return <-errc
}

func (f *Finestra) giro(w *app.Window) error {
	var ops op.Ops
	for {
		switch e := w.Event().(type) {
		case app.DestroyEvent:
			return e.Err
		case app.FrameEvent:
			gtx := app.NewContext(&ops, e)
			f.mu.Lock()
			f.disegna(gtx)
			chiudi := f.chiudi
			f.mu.Unlock()
			e.Frame(gtx.Ops)
			if chiudi {
				w.Perform(system.ActionClose)
			}
		}
	}
}

func (f *Finestra) aggiorna() {
	if f.invalida != nil {
		f.invalida()
	}
}

// ---- le chiamate al motore (in un filo a parte: la finestra non si blocca) -------------------

func (f *Finestra) controlla(porta int) {
	f.mu.Lock()
	f.schermo, f.attesa = sAttesa, interfaccia.T("attendi.permessi")
	f.mu.Unlock()
	go func() {
		c, err := f.mot.Controlla(porta)
		defer f.aggiorna() // dopo lo sblocco (i defer girano al contrario)
		f.mu.Lock()
		defer f.mu.Unlock()
		if err != nil {
			f.finisci(&interfaccia.Esito{Errore: messaggio(err)})
			return
		}
		f.metteControllo(c)
	}()
}

func messaggio(err error) *motore.Messaggio {
	if e, ok := err.(*motore.ErroreRX); ok {
		return &e.M
	}
	m := motore.Msg("RX-UI-005", err.Error())
	return &m
}

func (f *Finestra) metteControllo(c *interfaccia.Controllo) {
	f.ctrl = c
	f.vc = interfaccia.VistaDelControllo(c)
	if f.vc.Esito == interfaccia.BLOCCATA {
		f.fine, f.schermo = f.vc.Bloccata, sFine
		return
	}
	f.vs = interfaccia.VistaDelleScelte(c)
	f.voci = c.Domande.VociDiserie()
	f.porta.SetText(strconv.Itoa(c.Domande.Porta))
	f.portaUlt = f.porta.Text()
	f.schermo = sControllo
}

func (f *Finestra) chiediPiano() {
	voci := map[string]string{}
	for k, v := range f.voci {
		voci[k] = v
	}
	f.schermo, f.attesa = sAttesa, interfaccia.T("attendi.piano")
	go func() {
		p, err := f.mot.Piano(voci)
		defer f.aggiorna() // dopo lo sblocco (i defer girano al contrario)
		f.mu.Lock()
		defer f.mu.Unlock()
		if err != nil {
			f.finisci(&interfaccia.Esito{Errore: messaggio(err)})
			return
		}
		if m := interfaccia.BloccoNelPiano(p); m != nil {
			f.finisci(&interfaccia.Esito{Errore: m})
			return
		}
		f.piano = p
		f.vp = interfaccia.VistaDelPiano(p, f.ctrl.Profilo, interfaccia.NomiDepositi(f.ctrl.Domande))
		f.schermo = sPiano
	}()
}

func (f *Finestra) applica() {
	f.av = interfaccia.NuovoAvanzamento(f.vp)
	f.schermo = sAvanzamento
	digest := f.piano.Digest()
	go func() {
		es, err := f.mot.Applica(digest, func(ev motore.EventoPubblico) {
			f.mu.Lock()
			f.eventi = append(f.eventi, ev)
			f.av.Evento(ev)
			f.mu.Unlock()
			f.aggiorna()
		})
		defer f.aggiorna() // dopo lo sblocco (i defer girano al contrario)
		f.mu.Lock()
		defer f.mu.Unlock()
		if err != nil {
			f.finisci(&interfaccia.Esito{Errore: messaggio(err)})
			return
		}
		f.finisci(es)
	}()
}

// finisci: pronto, o una fine diversa (fermata, annullata, bloccata).
func (f *Finestra) finisci(es *interfaccia.Esito) {
	if es.Stato == motore.CONFERMATA || es.Stato == motore.CONFERMATA_A_CONDIZIONI {
		porta, _ := strconv.Atoi(f.voci["porta"])
		f.pronto = interfaccia.VistaDelPronto(es, f.vp, porta, interfaccia.DepositoVideo(f.ctrl.Domande, f.voci))
		f.schermo = sPronto
		return
	}
	if es.Errore == nil {
		es.Errore = interfaccia.UltimoMessaggio(f.eventi)
	}
	f.fine = interfaccia.VistaDellaFine(es, nil)
	f.schermo = sFine
}

// ---- il disegno ------------------------------------------------------------------------------

func (f *Finestra) disegna(gtx C) D {
	f.eventiInput(gtx)
	if f.schermo == sAttesa || f.schermo == sAvanzamento {
		// il motore lavora in un altro filo: si ridisegna da soli, anche se un Invalidate si perde
		gtx.Execute(op.InvalidateCmd{At: gtx.Now.Add(300 * time.Millisecond)})
	}
	pieno(gtx, image.Rectangle{Max: gtx.Constraints.Max}, cFondo)
	nav := f.schermo == sControllo || f.schermo == sScelte || f.schermo == sPiano || f.schermo == sAvanzamento
	return layout.Flex{Axis: layout.Vertical}.Layout(gtx,
		layout.Rigid(f.intestazione),
		layout.Flexed(1, func(gtx C) D {
			if !nav {
				return f.principale(gtx)
			}
			return layout.Flex{}.Layout(gtx,
				layout.Rigid(f.passi),
				layout.Flexed(1, f.principale))
		}),
		layout.Rigid(f.piede),
	)
}

func (f *Finestra) intestazione(gtx C) D {
	h := dp(gtx, 64)
	gtx.Constraints = layout.Exact(image.Pt(gtx.Constraints.Max.X, h))
	pieno(gtx, image.Rect(0, 0, gtx.Constraints.Max.X, h), cBianco)
	pieno(gtx, image.Rect(0, h-1, gtx.Constraints.Max.X, h), cBordo)
	testo := ""
	if f.vc != nil {
		testo = f.vc.Intestazione
	}
	return layout.Inset{Left: unit.Dp(28), Right: unit.Dp(28)}.Layout(gtx, func(gtx C) D {
		return layout.W.Layout(gtx, func(gtx C) D {
			return f.rigaIntestazione(gtx, testo)
		})
	})
}

func (f *Finestra) rigaIntestazione(gtx C, testo string) D {
	return layout.Flex{Alignment: layout.Middle}.Layout(gtx,
		layout.Rigid(func(gtx C) D {
			alt := dp(gtx, 34)
			lar := alt * f.logoDim.X / f.logoDim.Y
			gtx.Constraints = layout.Exact(image.Pt(lar, alt))
			return widget.Image{Src: f.logo, Fit: widget.Contain, Scale: float32(alt) / float32(f.logoDim.Y) / gtx.Metric.PxPerDp}.Layout(gtx)
		}),
		layout.Rigid(spazio(16, 0)),
		layout.Rigid(scrittaUna(f.th, fTitolo, 17, cNotte, interfaccia.T("intestazione"))),
		layout.Flexed(1, spazio(0, 0)),
		layout.Rigid(scrittaUna(f.th, fTesto, 13, cGrigio, testo)),
	)
}

func (f *Finestra) passi(gtx C) D {
	w := dp(gtx, 232)
	gtx.Constraints = layout.Exact(image.Pt(w, gtx.Constraints.Max.Y))
	pieno(gtx, image.Rectangle{Max: gtx.Constraints.Max}, cNav)
	pieno(gtx, image.Rect(w-1, 0, w, gtx.Constraints.Max.Y), cBordo)
	cur := map[int]int{sControllo: 1, sScelte: 2, sPiano: 3, sAvanzamento: 4}[f.schermo]
	var fl []layout.FlexChild
	for i := 1; i <= 5; i++ {
		i := i
		fl = append(fl, layout.Rigid(func(gtx C) D {
			var cerchio W
			nome := scrittaUna(f.th, fTesto, 15, cGrigio, interfaccia.T(fmt.Sprintf("passo.%d", i)))
			switch {
			case i < cur:
				cerchio = disco(26, cVerde, spunta(14, cBianco, 3))
			case i == cur:
				cerchio = disco(26, cBlu, scrittaUna(f.th, fForte, 13, cBianco, strconv.Itoa(i)))
				nome = scrittaUna(f.th, fForte, 15, cNotte, interfaccia.T(fmt.Sprintf("passo.%d", i)))
			default:
				cerchio = cerchioBordo(26, cCerchio, 1.5, scrittaUna(f.th, fTesto, 13, cGrigio, strconv.Itoa(i)))
			}
			voce := margine(10, 12, 10, 12, riga(12, layout.Rigid(cerchio), layout.Rigid(nome)))
			if i == cur {
				return scatola(cBianco, cBianco, 10, 0, larga(voce))(gtx)
			}
			return voce(gtx)
		}))
		fl = append(fl, layout.Rigid(spazio(0, 6)))
	}
	fl = append(fl, layout.Flexed(1, spazio(0, 0)))
	if f.schermo <= sPiano {
		fl = append(fl, layout.Rigid(scritta(f.th, fTesto, 12, cGrigio, interfaccia.T("passi.nota"))))
	}
	return layout.Inset{Top: unit.Dp(28), Bottom: unit.Dp(28), Left: unit.Dp(20), Right: unit.Dp(20)}.Layout(gtx, func(gtx C) D {
		return layout.Flex{Axis: layout.Vertical}.Layout(gtx, fl...)
	})
}

func (f *Finestra) piede(gtx C) D {
	h := dp(gtx, 76)
	gtx.Constraints = layout.Exact(image.Pt(gtx.Constraints.Max.X, h))
	pieno(gtx, image.Rect(0, 0, gtx.Constraints.Max.X, h), cBianco)
	pieno(gtx, image.Rect(0, 0, gtx.Constraints.Max.X, 1), cBordo)
	var sx, dx W
	T := interfaccia.T
	switch f.schermo {
	case sControllo:
		sx, dx = bottone(f.th, &f.sx, T("btn.annulla"), false, false), bottone(f.th, &f.dx, T("btn.avanti"), true, false)
	case sScelte:
		sx, dx = bottone(f.th, &f.sx, T("btn.indietro"), false, false), bottone(f.th, &f.dx, T("btn.avanti_piano"), true, f.errPorta)
	case sPiano:
		sx, dx = bottone(f.th, &f.sx, T("btn.indietro"), false, false), bottone(f.th, &f.dx, T("btn.conferma"), true, false)
	case sAvanzamento:
		t := T("btn.ferma")
		if f.fermando {
			t = T("btn.fermando")
		}
		sx = bottone(f.th, &f.sx, t, false, f.fermando || f.av == nil || f.av.Annulla)
	case sPronto:
		sx, dx = bottone(f.th, &f.sx, T("btn.registro"), false, false), bottone(f.th, &f.dx, T("btn.chiudi"), true, false)
	case sFine:
		sx, dx = bottone(f.th, &f.sx, T("btn.salva_rapp"), false, false), bottone(f.th, &f.dx, T("btn.chiudi"), true, false)
	}
	var fl []layout.FlexChild
	if sx != nil {
		fl = append(fl, layout.Rigid(sx))
	}
	if f.nota != "" {
		fl = append(fl, layout.Rigid(spazio(16, 0)), layout.Rigid(scrittaUna(f.th, fTesto, 13, cGrigio, f.nota)))
	}
	fl = append(fl, layout.Flexed(1, spazio(0, 0)))
	if dx != nil {
		fl = append(fl, layout.Rigid(dx))
	}
	return layout.Inset{Left: unit.Dp(28), Right: unit.Dp(28)}.Layout(gtx, func(gtx C) D {
		return layout.W.Layout(gtx, func(gtx C) D {
			gtx.Constraints.Min.X = gtx.Constraints.Max.X
			return layout.Flex{Alignment: layout.Middle}.Layout(gtx, fl...)
		})
	})
}

// principale: il contenuto della schermata, che scorre se non ci sta.
func (f *Finestra) principale(gtx C) D {
	var blocchi []W
	pad := [2]float32{28, 36}
	switch f.schermo {
	case sAttesa:
		return layout.Center.Layout(gtx, riga(12, layout.Rigid(anello(22, cBlu, 2.5, 0.75)),
			layout.Rigid(scrittaUna(f.th, fTesto, 15, cGrigio, f.attesa))))
	case sControllo:
		blocchi = f.controllo()
	case sScelte:
		blocchi = f.scelte(gtx)
	case sPiano:
		blocchi = f.pianoSchermo()
	case sAvanzamento:
		blocchi = f.avanzamento()
	case sPronto:
		blocchi, pad = f.prontoSchermo(), [2]float32{30, 40}
	case sFine:
		blocchi, pad = f.fineSchermo(), [2]float32{48, 64}
	}
	return layout.Inset{Top: unit.Dp(pad[0]), Bottom: unit.Dp(pad[0]), Left: unit.Dp(pad[1]), Right: unit.Dp(pad[1])}.Layout(gtx, func(gtx C) D {
		return material.List(f.th, &f.lista).Layout(gtx, len(blocchi), func(gtx C, i int) D {
			gtx.Constraints.Min.X = gtx.Constraints.Max.X
			if i > 0 {
				return layout.Inset{Top: unit.Dp(18)}.Layout(gtx, blocchi[i])
			}
			return blocchi[i](gtx)
		})
	})
}

func (f *Finestra) titolo(t, s string, sp float32) W {
	return colonna(6, scritta(f.th, fTitolo, sp, cNotte, t), scritta(f.th, fTesto, 15, cGrigio, s))
}

func (f *Finestra) dettagli(testo string) W {
	return func(gtx C) D {
		t := interfaccia.T("dettagli.mostra")
		if f.dettAp {
			t = interfaccia.T("dettagli.nascondi")
		}
		ws := []W{collegamento(f.th, &f.dett, t, 14)}
		if f.dettAp {
			ws = append(ws, scritta(f.th, fMono, 12, cGrigio, testo))
		}
		return colonna(8, ws...)(gtx)
	}
}

func coloriStato(s interfaccia.Stato) (fondo, testo color.NRGBA) {
	switch s {
	case interfaccia.OK:
		return cVerdeFondo, cVerde
	case interfaccia.CONSENSO:
		return cBadgeAmbra, cBadgeAmbraT
	case interfaccia.SISTEMO:
		return cBadgeBlu, cBluTesto
	case interfaccia.MALE:
		return cRossoFondo, cRosso
	}
	return cBadgeGrigio, cBadgeGrigT
}

func clipRR(gtx C, r image.Rectangle, raggio float32) clip.Op {
	return clip.UniformRRect(r, dp(gtx, raggio)).Op(gtx.Ops)
}

// ---- 1 · il controllo ------------------------------------------------------------------------

func (f *Finestra) controllo() []W {
	v := f.vc
	T := interfaccia.T
	var banner W
	if v.Esito == interfaccia.CONDIZIONI {
		banner = scatola(cAmbraFondo, cAmbraBordo, 12, 1, larga(margine(14, 18, 14, 18, riga(14,
			layout.Rigid(triangolo(22, cAmbraIcona)),
			layout.Flexed(1, colonna(2, scritta(f.th, fForte, 15, cAmbraTesto, v.Banner), scritta(f.th, fTesto, 14, cAmbraTesto, v.Sotto)))))))
	} else {
		banner = scatola(cVerdeFondo, rgb(0xB7E2CA), 12, 1, larga(margine(14, 18, 14, 18, riga(14,
			layout.Rigid(spunta(22, cVerde, 2.5)),
			layout.Flexed(1, colonna(2, scritta(f.th, fForte, 15, cVerde, v.Banner), scritta(f.th, fTesto, 14, cVerde, v.Sotto)))))))
	}
	tabella := func(gtx C) D {
		var righe []W
		for i, r := range v.Righe {
			r := r
			fondo, testo := coloriStato(r.Stato)
			cella := margine(11, 18, 11, 18, riga(16,
				layout.Rigid(fissa(190, scritta(f.th, fTesto, 14, cGrigio, r.Etichetta))),
				layout.Flexed(1, scritta(f.th, fTesto, 14, cNotte, r.Testo)),
				layout.Rigid(fissa(180, aDestra(pastiglia(f.th, fondo, testo, r.Stato.Cartellino()))))))
			cella = larga(cella)
			if r.Stato == interfaccia.CONSENSO {
				cella = fondoPieno(cRigaAmbra, cella)
			}
			if i < len(v.Righe)-1 {
				cella = lineaSotto(cRiga, cella)
			}
			righe = append(righe, cella)
		}
		return scatola(cBianco, cBordo, 12, 1, larga(colonna(0, righe...)))(gtx)
	}
	return []W{f.titolo(T("c.titolo"), T("c.sotto"), 26), banner, tabella, f.dettagli(v.Dettagli)}
}

// ---- 2 · le scelte ---------------------------------------------------------------------------

func (f *Finestra) clic(voce string, n int) []*widget.Clickable {
	cs := f.opzioni[voce]
	for len(cs) < n {
		cs = append(cs, new(widget.Clickable))
	}
	f.opzioni[voce] = cs
	return cs
}

func (f *Finestra) scheda(w W, pad [2]float32) W {
	return scatola(cBianco, cBordo, 12, 1, larga(margine(pad[0], pad[1], pad[0], pad[1], w)))
}

func (f *Finestra) opzione(c *widget.Clickable, o interfaccia.Opzione, scelto bool, pad [2]float32) W {
	return func(gtx C) D {
		bordo, fondo := cBordo, cBianco
		if scelto {
			bordo, fondo = cBlu, cScelto
		}
		titolo := scritta(f.th, fForte, 15, cNotte, o.Titolo)
		if o.Nota != "" {
			col := cGrigio
			if o.Verde {
				col = cVerde
			}
			titolo = rigaAlto(0, layout.Rigid(scrittaUna(f.th, fForte, 15, cNotte, o.Titolo+" ")),
				layout.Flexed(1, scritta(f.th, fMedio, 15, col, o.Nota)))
		}
		testo := colonna(3, titolo)
		if o.Testo != "" {
			testo = colonna(3, titolo, scritta(f.th, fTesto, 14, cGrigio, o.Testo))
		}
		corpo := scatola(fondo, bordo, 10, 1.5, larga(margine(pad[0], pad[1], pad[0], pad[1],
			rigaAlto(14, layout.Rigid(margine(2, 0, 0, 0, radio(scelto))), layout.Flexed(1, testo)))))
		return cliccabile(gtx, c, corpo)
	}
}

func (f *Finestra) domanda(d interfaccia.Domanda) W {
	cs := f.clic(d.Voce, len(d.Opzioni))
	scelta := f.voci[d.Voce]
	if d.Griglia {
		// i desktop: due colonne; «no» sotto, per tutta la larghezza
		return func(gtx C) D {
			var ops []W
			var no W
			for i, o := range d.Opzioni {
				w := f.opzione(cs[i], o, scelta == o.Valore, [2]float32{16, 16})
				if o.Valore == "no" {
					no = f.opzione(cs[i], o, scelta == o.Valore, [2]float32{14, 16})
					continue
				}
				ops = append(ops, w)
			}
			var righe []W
			righe = append(righe, scritta(f.th, fForte, 16, cNotte, d.Titolo))
			for i := 0; i < len(ops); i += 2 {
				a, b := ops[i], spazio(0, 0)
				if i+1 < len(ops) {
					b = ops[i+1]
				}
				righe = append(righe, func(gtx C) D {
					return layout.Flex{}.Layout(gtx, layout.Flexed(1, a), layout.Rigid(spazio(12, 0)), layout.Flexed(1, b))
				})
			}
			if no != nil {
				righe = append(righe, no)
			}
			return colonna(12, righe...)(gtx)
		}
	}
	var ws []W
	ws = append(ws, colonna(4, scritta(f.th, fForte, 16, cNotte, d.Titolo), scritta(f.th, fTesto, 14, cGrigio, d.Spiega)))
	for i, o := range d.Opzioni {
		ws = append(ws, f.opzione(cs[i], o, scelta == o.Valore, [2]float32{14, 16}))
	}
	return f.scheda(colonna(12, ws...), [2]float32{20, 22})
}

func (f *Finestra) scelte(gtx C) []W {
	v := f.vs
	T := interfaccia.T
	porta := func(gtx C) D {
		campo := scatola(cBianco, cBordoBtn, 10, 1, fissa(120, alta(44, func(gtx C) D {
			return layout.Inset{Left: unit.Dp(14), Right: unit.Dp(14)}.Layout(gtx, centraV(func(gtx C) D {
				e := material.Editor(f.th, &f.porta, "7447")
				e.Font, e.TextSize, e.Color = fMono, unit.Sp(16), cNotte
				e.LineHeightScale = 1
				return e.Layout(gtx)
			}))
		})))
		nota := scritta(f.th, fTesto, 14, cGrigio, T("sc.porta.nota"))
		if f.errPorta {
			nota = scritta(f.th, fForte, 14, cRosso, T("sc.porta.errata"))
		}
		ws := []W{scritta(f.th, fForte, 16, cNotte, T("sc.porta")), riga(14, layout.Rigid(campo), layout.Flexed(1, nota))}
		if v.PortaRiga != "" {
			if v.PortaVerde {
				ws = append(ws, riga(8, layout.Rigid(spunta(16, cVerde, 2.5)), layout.Flexed(1, scritta(f.th, fTesto, 14, cVerde, v.PortaRiga))))
			} else {
				ws = append(ws, scritta(f.th, fTesto, 14, cGrigio, v.PortaRiga))
			}
		}
		return f.scheda(colonna(10, ws...), [2]float32{20, 22})(gtx)
	}
	bl := []W{f.titolo(v.Titolo, v.Sotto, 26)}
	for _, d := range v.Domande {
		if d.Griglia {
			bl = append(bl, f.domanda(d))
		}
	}
	if !v.SenzaDesktop {
		bl = append(bl, porta)
	}
	for _, d := range v.Domande {
		if !d.Griglia {
			bl = append(bl, f.domanda(d))
		}
	}
	if v.SenzaDesktop {
		bl = append(bl, scritta(f.th, fTesto, 13, cGrigio, v.Nota), porta)
	}
	return bl
}

// ---- 3 · il piano ----------------------------------------------------------------------------

func (f *Finestra) pianoSchermo() []W {
	T := interfaccia.T
	testa := func(gtx C) D {
		return layout.Flex{Alignment: layout.End}.Layout(gtx,
			layout.Flexed(1, f.titolo(T("p.titolo"), T("p.sotto"), 26)),
			layout.Rigid(spazio(16, 0)),
			layout.Rigid(collegamento(f.th, &f.salva, T("btn.salva_piano"), 14)))
	}
	elenco := func(gtx C) D {
		var righe []W
		for i, p := range f.vp.Passi {
			p := p
			fondo, testo := coloriStato(p.Rev)
			titolo := scritta(f.th, fMedio, 15, cNotte, p.Titolo)
			if p.Nota != "" {
				titolo = rigaAlto(0, layout.Rigid(scrittaUna(f.th, fMedio, 15, cNotte, p.Titolo+" ")),
					layout.Flexed(1, scritta(f.th, fTesto, 15, cGrigio, p.Nota)))
			}
			cella := larga(margine(12, 18, 12, 18, riga(14,
				layout.Rigid(fissa(28, scrittaUna(f.th, fMono, 13, cGrigio, strconv.Itoa(i+1)))),
				layout.Flexed(1, colonna(2, titolo, scritta(f.th, fTesto, 13, cGrigio, p.Sotto))),
				layout.Rigid(fissa(170, aDestra(pastiglia(f.th, fondo, testo, p.Cartellino())))))))
			if i < len(f.vp.Passi)-1 {
				cella = lineaSotto(cRiga, cella)
			}
			righe = append(righe, cella)
		}
		return scatola(cBianco, cBordo, 12, 1, larga(colonna(0, righe...)))(gtx)
	}
	return []W{testa, elenco, scritta(f.th, fTesto, 13, cGrigio, T("p.nota")), f.dettagli(f.vp.Dettagli)}
}

// ---- 4 · l'avanzamento -----------------------------------------------------------------------

func (f *Finestra) avanzamento() []W {
	T := interfaccia.T
	punto, pc := f.av.Punto()
	barra := colonna(8,
		func(gtx C) D {
			return layout.Flex{}.Layout(gtx, layout.Flexed(1, scrittaUna(f.th, fForte, 14, cNotte, punto)),
				layout.Rigid(scrittaUna(f.th, fTesto, 14, cGrigio, fmt.Sprintf("%d %%", pc))))
		},
		func(gtx C) D {
			w, h := gtx.Constraints.Max.X, dp(gtx, 10)
			paint.FillShape(gtx.Ops, cBordo, clipRR(gtx, image.Rect(0, 0, w, h), 5))
			if pc > 0 {
				paint.FillShape(gtx.Ops, cBlu, clipRR(gtx, image.Rect(0, 0, w*pc/100, h), 5))
			}
			return D{Size: image.Pt(w, h)}
		})
	var righe []W
	for _, r := range f.av.Righe {
		var icona W
		col, fo := cNotte, fTesto
		switch r.Stato {
		case interfaccia.FATTA:
			icona = spunta(18, cVerde, 2.5)
		case interfaccia.INCORSO:
			icona, col, fo = anello(18, cBlu, 2.5, 0.75), cBluTesto, fForte
		case interfaccia.FALLITA:
			icona, col = croce(18, cRosso, 2.5), cRosso
		case interfaccia.ANNULLATA:
			icona, col = anello(18, cCerchio, 2, 1), cGrigio
		default:
			icona, col = anello(18, cCerchio, 2, 1), cGrigio
		}
		righe = append(righe, margine(7, 18, 7, 18, riga(12, layout.Rigid(icona), layout.Flexed(1, scritta(f.th, fo, 14, col, r.Testo)))))
	}
	lista := scatola(cBianco, cBordo, 12, 1, larga(margine(10, 0, 10, 0, colonna(2, righe...))))
	reg := func(gtx C) D {
		t := T("btn.registro")
		ws := []W{collegamento(f.th, &f.reg, t, 14)}
		if f.regAp {
			ws = append(ws, scritta(f.th, fMono, 12, cGrigio, ultime(f.av.Registro, 14)))
		}
		return colonna(8, ws...)(gtx)
	}
	return []W{f.titolo(T("av.titolo"), T("av.sotto"), 26), barra, lista, reg}
}

func ultime(r []string, n int) string {
	if len(r) > n {
		r = r[len(r)-n:]
	}
	return strings.Join(r, "\n")
}

// ---- 5 · pronto ------------------------------------------------------------------------------

func (f *Finestra) prontoSchermo() []W {
	T := interfaccia.T
	v := f.pronto
	if f.regAp {
		return []W{f.titolo(T("av.registro"), "", 22), scritta(f.th, fMono, 12, cGrigio, ultime(f.av.Registro, 400))}
	}
	testa := riga(18, layout.Rigid(disco(52, cVerde, spunta(28, cBianco, 2.5))),
		layout.Flexed(1, colonna(4, scritta(f.th, fTitolo, 28, cNotte, T("pr.titolo")), scritta(f.th, fTesto, 15, cGrigio, v.Sotto))))
	etichetta := func(s string) W { return scrittaUna(f.th, fForte, 13, cGrigio, strings.ToUpper(s)) }
	apri := []W{etichetta(T("pr.apri")), scritta(f.th, fMonoM, 20, cNotte, v.Indirizzo), scritta(f.th, fTesto, 14, cGrigio, T("pr.apri.t")),
		scritta(f.th, fTesto, 14, cGrigio, v.Router)}
	if v.Impronta != "" {
		apri = append(apri, func(gtx C) D {
			ws := []W{collegamento(f.th, &f.dett, T("pr.riconosci"), 13)}
			if f.dettAp {
				ws = append(ws, scritta(f.th, fTesto, 13, cGrigio, T("pr.impronta")), scritta(f.th, fMono, 11, cNotte, "SHA-256 "+v.Impronta))
			}
			return colonna(6, ws...)(gtx)
		})
	}
	chi := []W{etichetta(T("pr.chi")),
		scritta(f.th, fTesto, 15, cNotte, T("pr.chi.t")+" "+T("pr.chi.root")),
		scritta(f.th, fTesto, 14, cGrigio, T("pr.chi.t2"))}
	var cambi []W
	cambi = append(cambi, etichetta(T("pr.cambiato")))
	for _, c := range v.Cambiato {
		cambi = append(cambi, riga(8, layout.Rigid(scrittaUna(f.th, fTesto, 14, cNotte, "•")), layout.Flexed(1, scritta(f.th, fTesto, 14, cNotte, c))))
	}
	var prove []W
	prove = append(prove, etichetta(T("pr.prove")))
	for _, p := range v.Prove {
		col := cVerde
		switch p.Stato {
		case interfaccia.MALE:
			col = cRosso
		case interfaccia.DOPO, interfaccia.IGNOTO:
			col = cBadgeGrigT
		}
		prove = append(prove, riga(12, layout.Flexed(1, scritta(f.th, fTesto, 14, cNotte, p.Etichetta)), layout.Rigid(scrittaUna(f.th, fForte, 14, col, p.Testo))))
	}
	sch := func(gap float32, ws []W) W { return f.scheda(colonna(gap, ws...), [2]float32{20, 22}) }
	griglia := func(gtx C) D {
		// due righe di due schede, alte uguali per riga
		rigaDi := func(a, b W) W {
			return func(gtx C) D {
				return layout.Flex{}.Layout(gtx, layout.Flexed(1, a), layout.Rigid(spazio(16, 0)), layout.Flexed(1, b))
			}
		}
		return colonna(16, rigaDi(sch(10, apri), sch(10, chi)), rigaDi(sch(6, cambi), sch(6, prove)))(gtx)
	}
	return []W{testa, griglia, f.dettagli(v.Dettagli)}
}

// ---- la fine diversa da «pronto» -------------------------------------------------------------

func (f *Finestra) fineSchermo() []W {
	T := interfaccia.T
	v := f.fine
	fondo, segno := cRossoFondo, croce(26, cRosso, 2.5)
	if v.Toccata {
		fondo, segno = cAmbraFondo, triangolo(26, cAmbraIcona)
	}
	testa := riga(18, layout.Rigid(disco(52, fondo, segno)),
		layout.Flexed(1, colonna(4, scritta(f.th, fTitolo, 28, cNotte, v.Titolo), scritta(f.th, fTesto, 15, cGrigio, v.Sotto))))
	max := func(w W) W {
		return func(gtx C) D {
			if m := dp(gtx, 760); gtx.Constraints.Max.X > m {
				gtx.Constraints.Max.X = m
			}
			return w(gtx)
		}
	}
	var bl []W
	bl = append(bl, testa)
	if v.Perche != "" {
		ws := []W{scritta(f.th, fForte, 16, cNotte, T("b.perche")), scritta(f.th, fTesto, 15, cNotte, v.Perche)}
		sotto := v.Serve
		if v.Codice != "" {
			ws = append(ws, riga(8, layout.Rigid(scritta(f.th, fTesto, 14, cGrigio, sotto)), layout.Rigid(scrittaUna(f.th, fMono, 12, cGrigio, v.Codice))))
		}
		bl = append(bl, max(f.scheda(colonna(12, ws...), [2]float32{22, 24})))
	}
	if v.CheFare != "" {
		bl = append(bl, max(f.scheda(colonna(10, scritta(f.th, fForte, 16, cNotte, T("b.chefare")), scritta(f.th, fTesto, 15, cNotte, v.CheFare)), [2]float32{22, 24})))
	}
	if v.Dettagli != "" {
		bl = append(bl, f.dettagli(v.Dettagli))
	}
	if f.regAp && f.av != nil {
		bl = append(bl, scritta(f.th, fMono, 12, cGrigio, ultime(f.av.Registro, 400)))
	}
	return bl
}

// ---- l'input ---------------------------------------------------------------------------------

func (f *Finestra) eventiInput(gtx C) {
	f.nota = strings.TrimSpace(f.nota)
	if f.dett.Clicked(gtx) {
		f.dettAp = !f.dettAp
	}
	if f.reg.Clicked(gtx) {
		f.regAp = !f.regAp
	}
	// le scelte
	if f.vs != nil {
		for _, d := range f.vs.Domande {
			for i, c := range f.clic(d.Voce, len(d.Opzioni)) {
				if c.Clicked(gtx) {
					f.voci[d.Voce] = d.Opzioni[i].Valore
					if d.Voce == "desktop" {
						f.aggiornaDepositiDesktop()
					}
				}
			}
		}
	}
	for {
		_, ok := f.porta.Update(gtx)
		if !ok {
			break
		}
	}
	if t := f.porta.Text(); t != f.portaUlt && f.voci != nil {
		f.portaUlt = t
		p, ok := interfaccia.PortaValida(t)
		f.errPorta = !ok
		if ok {
			f.voci["porta"] = strconv.Itoa(p)
		}
	}
	if f.salva.Clicked(gtx) && f.piano != nil {
		f.salvaFile("remotix-piano-"+f.piano.ID+".json", f.piano)
	}
	sx, dx := f.sx.Clicked(gtx), f.dx.Clicked(gtx)
	switch f.schermo {
	case sControllo:
		if sx {
			f.chiudi = true
		}
		if dx {
			f.schermo = sScelte
		}
	case sScelte:
		if sx {
			f.schermo = sControllo
		}
		if dx && !f.errPorta {
			f.chiediPiano()
		}
	case sPiano:
		if sx {
			f.schermo = sScelte
		}
		if dx {
			f.applica()
		}
	case sAvanzamento:
		if sx && !f.fermando {
			f.fermando = true
			go f.mot.Ferma()
		}
	case sPronto:
		if sx {
			f.regAp = !f.regAp
		}
		if dx {
			f.chiudi = true
		}
	case sFine:
		if sx {
			f.salvaFile("remotix-rapporto.json", map[string]any{"fine": f.fine, "controllo": f.ctrl, "eventi": f.eventi})
		}
		if dx {
			f.chiudi = true
		}
	}
}

// aggiornaDepositiDesktop: cambiare desktop può cambiare gli archivi da chiedere (KDE su openSUSE
// chiede Packman…): lo dice il motore (DomandeDaFare), non la finestra. Qui si tengono le voci dei
// depositi che la vista delle scelte mostra già.
func (f *Finestra) aggiornaDepositiDesktop() {}

func (f *Finestra) salvaFile(nome string, v any) {
	dir, _ := os.UserHomeDir()
	if dir == "" {
		dir = "."
	}
	p := filepath.Join(dir, nome)
	b, _ := json.MarshalIndent(v, "", "  ")
	if err := os.WriteFile(p, b, 0o600); err != nil {
		f.nota = err.Error()
		return
	}
	f.nota = interfaccia.T("salvato", p)
}
