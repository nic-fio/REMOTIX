//go:build gui

package gui

import (
	"bytes"
	_ "embed"
	"image"
	"image/png"

	"gioui.org/font"
	"gioui.org/font/opentype"
	"gioui.org/op/paint"
	"gioui.org/text"
	"gioui.org/widget/material"
)

// I caratteri stanno DENTRO il binario (la finestra non dipende da quel che la distribuzione ha
// installato). Licenze: Sora e IBM Plex sono SIL Open Font License 1.1 (risorse/OFL-*.txt), che ne
// permette l'incorporazione in un programma, anche venduto, col testo della licenza accanto. Sora
// SemiBold è l'istanza a peso 600 del Sora variabile di Google Fonts (fontTools instancer): Sora
// non ha un «Reserved Font Name»; IBM Plex (che ne ha uno, «Plex») è usato senza modifiche.
// Il logo è grafica/logo/remotix-logo.png, ritagliato e ridotto a 136 px d'altezza.

//go:embed risorse/Sora-SemiBold.ttf
var soraSemiBold []byte

//go:embed risorse/IBMPlexSans-Regular.ttf
var plexRegular []byte

//go:embed risorse/IBMPlexSans-Medium.ttf
var plexMedium []byte

//go:embed risorse/IBMPlexSans-SemiBold.ttf
var plexSemiBold []byte

//go:embed risorse/IBMPlexMono-Regular.ttf
var monoRegular []byte

//go:embed risorse/IBMPlexMono-Medium.ttf
var monoMedium []byte

//go:embed risorse/logo.png
var logoPNG []byte

//go:embed risorse/OFL-Sora.txt
var LicenzaSora string

//go:embed risorse/OFL-IBMPlex.txt
var LicenzaPlex string

func caratteri() []font.FontFace {
	var r []font.FontFace
	for _, x := range []struct {
		dati []byte
		f    font.Font
	}{
		{soraSemiBold, fTitolo}, {plexRegular, fTesto}, {plexMedium, fMedio}, {plexSemiBold, fForte},
		{monoRegular, fMono}, {monoMedium, fMonoM},
	} {
		f, err := opentype.Parse(x.dati)
		if err != nil {
			panic(err)
		}
		r = append(r, font.FontFace{Font: x.f, Face: f})
	}
	return r
}

func tema() *material.Theme {
	th := material.NewTheme()
	th.Shaper = text.NewShaper(text.NoSystemFonts(), text.WithCollection(caratteri()))
	th.Face = "IBM Plex Sans"
	th.Palette.Fg = cNotte
	th.Palette.Bg = cFondo
	th.Palette.ContrastBg = cBlu
	return th
}

func logo() (paint.ImageOp, image.Point) {
	img, err := png.Decode(bytes.NewReader(logoPNG))
	if err != nil {
		panic(err)
	}
	return paint.NewImageOp(img), img.Bounds().Size()
}
