#!/usr/bin/env python3
"""Prova di fumo dei guasti di B11: si guarda che il server MENTA davvero.

⛔ Non prova la pagina — prova il BANCO.  Se il server guasto non mentisse, i
   dodici casi di B11 fallirebbero tutti per la ragione sbagliata, e il rosso
   finirebbe sulla pagina invece che sull'innesto.
"""
import asyncio, importlib.util, os, struct, sys
QUI = "/srv/src"
spec = importlib.util.spec_from_file_location("b5", os.path.join(QUI, "01-b5-violazioni.py"))
b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)

class A: indirizzo, porta, utente, parola = "192.168.0.2", 7447, "prova", "parola-di-prova"

async def uno(guasto):
    voci = b5.BUONE + [("banco.guasto", guasto)]
    g, cli, st = await b5.apri(A)
    fuori = []
    try:
        cli.apri_controllo()
        cli.manda(b5.ciao(voci))
        for _ in range(4):
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=6)
            if m is None: fuori.append("FIN"); break
            tipo, corpo, _x = m
            fuori.append(f"{tipo:#06x}:{corpo[:12].hex()}")
            if tipo == 0x0002:
                cli.manda(b5.inquadra(3, b5.s(A.utente) + b5.s(A.parola)))
            elif tipo == 0x0004:
                cli.manda(b5.attacca())
            elif tipo in (0x0007, 0x000c, 0x0005):
                pass
    except Exception as e:
        fuori.append(f"{type(e).__name__}")
    finally:
        await g.__aexit__(None, None, None)
    print(f"  {guasto:26s} {' | '.join(fuori)}")

async def main():
    for gu in ["nessuno", "eccomi-versione-2", "capacita-sconosciuta",
               "misura-massima-in-eccomi", "tipo-sconosciuto",
               "congedo-motivo-zero", "sessione-tela-dispari",
               "sessione-desktop-kde"]:
        await uno(gu)
asyncio.run(main())
