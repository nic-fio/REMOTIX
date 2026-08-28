#!/usr/bin/env python3
"""Innesta / toglie il guasto 03-b16 sulla pagina dell'ALBERO DI PROVA.

  python3 innesta.py applica
  python3 innesta.py togli

⛔ L'appiglio e il sostituto si LEGGONO dal catalogo di casa con importlib —
   non si ricopiano a mano.  E si contano prima: dev'essere esattamente uno.
⛔ Tocca SOLO /home/nicfio/b16-albero/src/pagina.html.
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

CATALOGO = Path("/home/nicfio/Documenti/REMOTIX_V2/banchi/01-b12-guasti.py")
PAGINA = Path("/home/nicfio/b16-albero/src/pagina.html")
DI_CASA = "ec169e5d7232ca6a17202593983e61451bc3df9e3b6b90e5f227394945739962"


def catalogo():
    s = importlib.util.spec_from_file_location("b12", str(CATALOGO))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def principale():
    verso = sys.argv[1]
    g = catalogo().GUASTI["03-b16"]
    appiglio, sostituto = g["appiglio"], g["sostituto"]
    print(f"catalogo: {CATALOGO}")
    print(f"appiglio  ({len(appiglio)} car.): {appiglio!r}")
    print(f"sostituto ({len(sostituto)} car.): {sostituto!r}")
    print(f"dove (catalogo): {g['dove']}")
    print(f"marca dichiarata in catalogo: {g['marca']!r}")
    print(f"atteso_sano: {g['atteso_sano']}")

    testo = PAGINA.read_text()
    print(f"\npagina: {PAGINA}\nsha256 prima: {sha(PAGINA)}")

    if verso == "applica":
        # ⛔ l'appiglio LUNGO dev'essere esattamente uno; e si conta anche
        #    quello CORTO, per far vedere la trappola che la nota descrive.
        corto = "overflow-y: scroll"
        print(f"occorrenze appiglio LUNGO:  {testo.count(appiglio)}")
        print(f"occorrenze appiglio CORTO ({corto!r}): {testo.count(corto)}")
        if testo.count(appiglio) != 1:
            print("⛔ l'appiglio non e' unico: NON innesto")
            return 2
        nuovo = testo.replace(appiglio, sostituto, 1)
        assert nuovo != testo
        PAGINA.write_text(nuovo)
        print(f"sha256 dopo:  {sha(PAGINA)}")
        # ⛔ e si verifica DOVE e' finito: dentro il codice, non nel commento
        i = nuovo.index(sostituto.split("\n")[0])
        riga = nuovo[:i].count("\n") + 1
        print(f"il sostituto e' entrato alla riga {riga}")
        print(f"occorrenze appiglio corto rimaste: {nuovo.count(corto)}")
        return 0

    if verso == "togli":
        print(f"occorrenze sostituto: {testo.count(sostituto)}")
        if testo.count(sostituto) != 1:
            print("⛔ il sostituto non e' unico: NON tolgo")
            return 2
        nuovo = testo.replace(sostituto, appiglio, 1)
        PAGINA.write_text(nuovo)
        d = sha(PAGINA)
        print(f"sha256 dopo:  {d}")
        print(f"sha256 di casa: {DI_CASA}")
        print("IDENTICA BYTE PER BYTE" if d == DI_CASA else "⛔ NON TORNATA IDENTICA")
        return 0 if d == DI_CASA else 3

    print("uso: innesta.py applica|togli")
    return 1


if __name__ == "__main__":
    sys.exit(principale())
