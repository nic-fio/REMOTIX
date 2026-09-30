//go:build gui

package gui

import (
	"image"
	"image/color"
	"math"

	"gioui.org/f32"
	"gioui.org/font"
	"gioui.org/io/pointer"
	"gioui.org/layout"
	"gioui.org/op"
	"gioui.org/op/clip"
	"gioui.org/op/paint"
	"gioui.org/text"
	"gioui.org/unit"
	"gioui.org/widget"
	"gioui.org/widget/material"
)

// I colori del prototipo (dal logo: blu #0A5FE0, blu notte #0B1433, fondo #F5F7FB).
func rgb(x uint32) color.NRGBA {
	return color.NRGBA{R: uint8(x >> 16), G: uint8(x >> 8), B: uint8(x), A: 0xff}
}

var (
	cBlu         = rgb(0x0A5FE0)
	cBluTesto    = rgb(0x0A4FC0)
	cNotte       = rgb(0x0B1433)
	cFondo       = rgb(0xF5F7FB)
	cBianco      = rgb(0xFFFFFF)
	cNav         = rgb(0xEEF2F8)
	cBordo       = rgb(0xDCE3EE)
	cRiga        = rgb(0xEEF1F6)
	cGrigio      = rgb(0x4A5570)
	cCerchio     = rgb(0x8C97AD)
	cBordoBtn    = rgb(0xC7D0DF)
	cVerde       = rgb(0x0F6B40)
	cVerdeFondo  = rgb(0xE7F6EE)
	cAmbraFondo  = rgb(0xFFF4DF)
	cAmbraBordo  = rgb(0xF1D39A)
	cAmbraTesto  = rgb(0x5C3800)
	cAmbraIcona  = rgb(0x7A4A00)
	cBadgeAmbra  = rgb(0xFFF1D6)
	cBadgeAmbraT = rgb(0x6B4100)
	cRigaAmbra   = rgb(0xFFFBF3)
	cBadgeBlu    = rgb(0xEAF1FE)
	cBadgeGrigio = rgb(0xEEF0F4)
	cBadgeGrigT  = rgb(0x3E4658)
	cRossoFondo  = rgb(0xFDECEA)
	cRosso       = rgb(0x9B1C12)
	cScelto      = rgb(0xF2F7FF)
	cVerdeScelto = rgb(0xEAF7F0)
)

// I caratteri: Sora per i titoli, IBM Plex Sans per il testo, IBM Plex Mono per i codici.
var (
	fTitolo = font.Font{Typeface: "Sora", Weight: font.SemiBold}
	fTesto  = font.Font{Typeface: "IBM Plex Sans"}
	fMedio  = font.Font{Typeface: "IBM Plex Sans", Weight: font.Medium}
	fForte  = font.Font{Typeface: "IBM Plex Sans", Weight: font.SemiBold}
	fMono   = font.Font{Typeface: "IBM Plex Mono"}
	fMonoM  = font.Font{Typeface: "IBM Plex Mono", Weight: font.Medium}
)

type (
	C = layout.Context
	D = layout.Dimensions
	W = layout.Widget
)

// scritta: un testo col suo carattere, dimensione e colore.
func scritta(th *material.Theme, f font.Font, sp float32, c color.NRGBA, s string) W {
	return func(gtx C) D {
		gtx.Constraints.Min.Y = 0
		l := material.Label(th, unit.Sp(sp), s)
		l.Font, l.Color = f, c
		l.LineHeightScale = 1.35
		return l.Layout(gtx)
	}
}

func scrittaUna(th *material.Theme, f font.Font, sp float32, c color.NRGBA, s string) W {
	return func(gtx C) D {
		gtx.Constraints.Min.Y = 0
		l := material.Label(th, unit.Sp(sp), s)
		l.Font, l.Color, l.MaxLines = f, c, 1
		return l.Layout(gtx)
	}
}

func dp(gtx C, v float32) int { return gtx.Dp(unit.Dp(v)) }

// rettangolo pieno.
func pieno(gtx C, r image.Rectangle, c color.NRGBA) {
	paint.FillShape(gtx.Ops, c, clip.Rect(r).Op())
}

// scatola: sfondo arrotondato con bordo, dietro il contenuto (che decide la misura).
func scatola(fondo, bordo color.NRGBA, raggio, spessore float32, w W) W {
	return func(gtx C) D {
		m := op.Record(gtx.Ops)
		d := w(gtx)
		call := m.Stop()
		r := image.Rectangle{Max: d.Size}
		rg := dp(gtx, raggio)
		if m := min(d.Size.X, d.Size.Y) / 2; rg > m {
			rg = m
		}
		if bordo.A > 0 && spessore > 0 {
			paint.FillShape(gtx.Ops, bordo, clip.UniformRRect(r, rg).Op(gtx.Ops))
			s := int(math.Round(float64(spessore * gtx.Metric.PxPerDp)))
			if s < 1 {
				s = 1
			}
			r = r.Inset(s)
			rg -= s
			if rg < 0 {
				rg = 0
			}
		}
		paint.FillShape(gtx.Ops, fondo, clip.UniformRRect(r, rg).Op(gtx.Ops))
		call.Add(gtx.Ops)
		return d
	}
}

// larga: il contenuto riempie la larghezza disponibile.
func larga(w W) W {
	return func(gtx C) D {
		gtx.Constraints.Min.X = gtx.Constraints.Max.X
		return w(gtx)
	}
}

// centraV: il contenuto al centro, in verticale, dell'altezza minima data (la casella della porta).
func centraV(w W) W {
	return func(gtx C) D {
		h := gtx.Constraints.Min.Y
		gtx.Constraints.Min.Y = 0
		m := op.Record(gtx.Ops)
		d := w(gtx)
		c := m.Stop()
		off := (h - d.Size.Y) / 2
		if off < 0 {
			off = 0
		}
		t := op.Offset(image.Pt(0, off)).Push(gtx.Ops)
		c.Add(gtx.Ops)
		t.Pop()
		return D{Size: image.Pt(d.Size.X, max(h, d.Size.Y)), Baseline: d.Baseline}
	}
}

// fissa: larghezza fissa.
func fissa(v float32, w W) W {
	return func(gtx C) D {
		x := dp(gtx, v)
		gtx.Constraints.Min.X, gtx.Constraints.Max.X = x, x
		return w(gtx)
	}
}

func alta(v float32, w W) W {
	return func(gtx C) D {
		y := dp(gtx, v)
		gtx.Constraints.Min.Y, gtx.Constraints.Max.Y = y, y
		return w(gtx)
	}
}

// spazio: vuoto; dentro un Flexed riempie quel che gli si dà.
func spazio(x, y float32) W {
	return func(gtx C) D {
		return D{Size: image.Pt(max(gtx.Constraints.Min.X, dp(gtx, x)), max(gtx.Constraints.Min.Y, dp(gtx, y)))}
	}
}

func margine(t, r, b, l float32, w W) W {
	return func(gtx C) D {
		return layout.Inset{Top: unit.Dp(t), Right: unit.Dp(r), Bottom: unit.Dp(b), Left: unit.Dp(l)}.Layout(gtx, w)
	}
}

// colonna: widget uno sotto l'altro con uno spazio fra loro.
func colonna(gap float32, ws ...W) W {
	return func(gtx C) D {
		var fl []layout.FlexChild
		for i, w := range ws {
			if w == nil {
				continue
			}
			if i > 0 && len(fl) > 0 {
				fl = append(fl, layout.Rigid(spazio(0, gap)))
			}
			fl = append(fl, layout.Rigid(w))
		}
		return layout.Flex{Axis: layout.Vertical}.Layout(gtx, fl...)
	}
}

// pastiglia: il cartellino (A posto, Serve il tuo consenso…).
func pastiglia(th *material.Theme, fondo, testo color.NRGBA, s string) W {
	return scatola(fondo, color.NRGBA{}, 999, 0, margine(4, 10, 4, 10, scrittaUna(th, fForte, 12, testo, s)))
}

// ---- icone (percorsi del prototipo, su 24 unità) -----------------------------------------------

func tracciato(gtx C, s float32, c color.NRGBA, spess float32, costruisci func(p *clip.Path, k float32)) D {
	px := float32(dp(gtx, s))
	k := px / 24
	var p clip.Path
	p.Begin(gtx.Ops)
	costruisci(&p, k)
	paint.FillShape(gtx.Ops, c, clip.Stroke{Path: p.End(), Width: spess * k}.Op())
	return D{Size: image.Pt(int(px), int(px))}
}

func spunta(s float32, c color.NRGBA, spess float32) W {
	return func(gtx C) D {
		return tracciato(gtx, s, c, spess, func(p *clip.Path, k float32) {
			p.MoveTo(f32.Pt(20*k, 6*k))
			p.LineTo(f32.Pt(9*k, 17*k))
			p.LineTo(f32.Pt(4*k, 12*k))
		})
	}
}

func croce(s float32, c color.NRGBA, spess float32) W {
	return func(gtx C) D {
		return tracciato(gtx, s, c, spess, func(p *clip.Path, k float32) {
			p.MoveTo(f32.Pt(18*k, 6*k))
			p.LineTo(f32.Pt(6*k, 18*k))
			p.MoveTo(f32.Pt(6*k, 6*k))
			p.LineTo(f32.Pt(18*k, 18*k))
		})
	}
}

func triangolo(s float32, c color.NRGBA) W {
	return func(gtx C) D {
		return tracciato(gtx, s, c, 2, func(p *clip.Path, k float32) {
			p.MoveTo(f32.Pt(12*k, 3.2*k))
			p.LineTo(f32.Pt(21.6*k, 19.6*k))
			p.LineTo(f32.Pt(2.4*k, 19.6*k))
			p.Close()
			p.MoveTo(f32.Pt(12*k, 9*k))
			p.LineTo(f32.Pt(12*k, 13*k))
			p.MoveTo(f32.Pt(12*k, 16.6*k))
			p.LineTo(f32.Pt(12*k, 17.4*k))
		})
	}
}

// cerchio vuoto (passo in attesa) o arco (passo in corso).
func anello(s float32, c color.NRGBA, spess float32, parte float32) W {
	return func(gtx C) D {
		return tracciato(gtx, s, c, spess, func(p *clip.Path, k float32) {
			r := float32(8)
			if parte < 1 {
				r = 9
			}
			cx, cy := 12*k, 12*k
			p.MoveTo(f32.Pt(cx+r*k, cy))
			centro := f32.Pt(-r*k, 0)
			p.Arc(centro, centro, float32(2*math.Pi)*parte)
		})
	}
}

// disco pieno col contenuto al centro (i numeri dei passi, la spunta grande).
func disco(d float32, fondo color.NRGBA, dentro W) W {
	return func(gtx C) D {
		s := dp(gtx, d)
		paint.FillShape(gtx.Ops, fondo, clip.Ellipse(image.Rect(0, 0, s, s)).Op(gtx.Ops))
		gtx.Constraints = layout.Exact(image.Pt(s, s))
		layout.Center.Layout(gtx, dentro)
		return D{Size: image.Pt(s, s)}
	}
}

// cerchio con bordo (i passi futuri).
func cerchioBordo(d float32, bordo color.NRGBA, spess float32, dentro W) W {
	return func(gtx C) D {
		s := dp(gtx, d)
		paint.FillShape(gtx.Ops, bordo, clip.Ellipse(image.Rect(0, 0, s, s)).Op(gtx.Ops))
		b := int(math.Round(float64(spess * gtx.Metric.PxPerDp)))
		if b < 1 {
			b = 1
		}
		paint.FillShape(gtx.Ops, cNav, clip.Ellipse(image.Rect(b, b, s-b, s-b)).Op(gtx.Ops))
		gtx.Constraints = layout.Exact(image.Pt(s, s))
		layout.Center.Layout(gtx, dentro)
		return D{Size: image.Pt(s, s)}
	}
}

// radio: il pallino delle scelte.
func radio(scelto bool) W {
	return func(gtx C) D {
		s := dp(gtx, 20)
		if scelto {
			paint.FillShape(gtx.Ops, cBlu, clip.Ellipse(image.Rect(0, 0, s, s)).Op(gtx.Ops))
			b := dp(gtx, 2)
			paint.FillShape(gtx.Ops, cBianco, clip.Ellipse(image.Rect(b, b, s-b, s-b)).Op(gtx.Ops))
			q := dp(gtx, 5)
			paint.FillShape(gtx.Ops, cBlu, clip.Ellipse(image.Rect(q, q, s-q, s-q)).Op(gtx.Ops))
		} else {
			paint.FillShape(gtx.Ops, cCerchio, clip.Ellipse(image.Rect(0, 0, s, s)).Op(gtx.Ops))
			b := dp(gtx, 1.5)
			paint.FillShape(gtx.Ops, cBianco, clip.Ellipse(image.Rect(b, b, s-b, s-b)).Op(gtx.Ops))
		}
		return D{Size: image.Pt(s, s)}
	}
}

// cliccabile: un'area che si clicca, con la manina.
func cliccabile(gtx C, c *widget.Clickable, w W) D {
	return c.Layout(gtx, func(gtx C) D {
		d := w(gtx)
		defer clip.Rect(image.Rectangle{Max: d.Size}).Push(gtx.Ops).Pop()
		pointer.CursorPointer.Add(gtx.Ops)
		return d
	})
}

// bottone: primario (blu pieno) o secondario (bordo grigio).
func bottone(th *material.Theme, c *widget.Clickable, s string, primario, spento bool) W {
	return func(gtx C) D {
		fondo, bordo, testo, f, pad := cBianco, cBordoBtn, cNotte, fMedio, float32(20)
		if primario {
			fondo, bordo, testo, f, pad = cBlu, cBlu, cBianco, fForte, 24
		}
		if spento {
			fondo, bordo, testo = cBadgeGrigio, cBordo, cCerchio
		}
		corpo := scatola(fondo, bordo, 10, 1, alta(44, func(gtx C) D {
			return layout.Inset{Left: unit.Dp(pad), Right: unit.Dp(pad)}.Layout(gtx, func(gtx C) D {
				return layout.Center.Layout(gtx, scrittaUna(th, f, 15, testo, s))
			})
		}))
		if spento {
			return corpo(gtx)
		}
		return cliccabile(gtx, c, corpo)
	}
}

// collegamento: testo blu cliccabile.
func collegamento(th *material.Theme, c *widget.Clickable, s string, sp float32) W {
	return func(gtx C) D { return cliccabile(gtx, c, scrittaUna(th, fTesto, sp, cBlu, s)) }
}

// riga orizzontale con allineamento al centro.
func riga(gap float32, ws ...layout.FlexChild) W {
	return func(gtx C) D {
		var fl []layout.FlexChild
		for i, w := range ws {
			if i > 0 {
				fl = append(fl, layout.Rigid(spazio(gap, 0)))
			}
			fl = append(fl, w)
		}
		return layout.Flex{Alignment: layout.Middle}.Layout(gtx, fl...)
	}
}

// rigaAlto: come riga, allineata in alto.
func rigaAlto(gap float32, ws ...layout.FlexChild) W {
	return func(gtx C) D {
		var fl []layout.FlexChild
		for i, w := range ws {
			if i > 0 {
				fl = append(fl, layout.Rigid(spazio(gap, 0)))
			}
			fl = append(fl, w)
		}
		return layout.Flex{Alignment: layout.Start}.Layout(gtx, fl...)
	}
}

// aDestra: il contenuto allineato a destra nello spazio dato.
func aDestra(w W) W {
	return func(gtx C) D {
		gtx.Constraints.Min.X = gtx.Constraints.Max.X
		return layout.E.Layout(gtx, w)
	}
}

// lineaSotto: una riga di 1 px sotto il contenuto (le righe delle tabelle).
func lineaSotto(c color.NRGBA, w W) W {
	return func(gtx C) D {
		d := w(gtx)
		pieno(gtx, image.Rect(0, d.Size.Y-1, d.Size.X, d.Size.Y), c)
		return d
	}
}

// fondoPieno: un fondo rettangolare dietro il contenuto.
func fondoPieno(c color.NRGBA, w W) W {
	return func(gtx C) D {
		m := op.Record(gtx.Ops)
		d := w(gtx)
		call := m.Stop()
		pieno(gtx, image.Rectangle{Max: d.Size}, c)
		call.Add(gtx.Ops)
		return d
	}
}

var _ = text.Start
