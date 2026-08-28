#!/usr/bin/env python3
"""Conta i «flash» in una registrazione grezza dello schermo del client.

Un flash non e' un cambiamento: e' un fotogramma che se ne va e TORNA.  Chi
conta le differenze fra fotogrammi consecutivi conta anche il testo che scorre,
e non distingue le due cose.  Qui un fotogramma e' un flash quando differisce
molto sia da chi lo precede sia da chi lo segue, MENTRE quei due si assomigliano
fra loro: cioe' quando l'immagine e' tornata dov'era.

    flash.py <file grezzo> <larghezza> <altezza>
"""
import sys

def main():
    percorso, larg, alt = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    passo = larg * alt
    with open(percorso, "rb") as f:
        dati = f.read()
    n = len(dati) // passo
    if n < 3:
        print("troppo pochi fotogrammi: %d" % n)
        return
    fot = [dati[i * passo:(i + 1) * passo] for i in range(n)]

    # Si guarda un pixel ogni 7: la media non cambia e il conto costa un settimo.
    campione = range(0, passo, 7)

    def scarto(a, b):
        s = 0
        for k in campione:
            d = a[k] - b[k]
            s += d if d > 0 else -d
        return s / len(campione)

    def media(a):
        return sum(a[k] for k in campione) / len(campione)

    d = [0.0] * n
    for i in range(1, n):
        d[i] = scarto(fot[i], fot[i - 1])

    ordinati = sorted(d[1:])
    mediana = ordinati[len(ordinati) // 2]
    soglia = max(8.0, mediana * 4)

    flash = []
    for i in range(1, n - 1):
        if d[i] < soglia or d[i + 1] < soglia:
            continue
        # l'immagine e' tornata dov'era: prima e dopo si assomigliano
        if scarto(fot[i + 1], fot[i - 1]) < d[i] / 2:
            flash.append((i, round(d[i], 1), round(media(fot[i]), 1)))

    # ⛔ LA PROVA CHE LA MISURA ABBIA MISURATO QUALCOSA.
    #
    #    Senza, «FLASH=0» e «non ho registrato niente» sono la stessa riga — ed
    #    e' la lezione della fase 8: un banco verde mentre il difetto c'era.
    #    Uno scarto mediano di zero e' NORMALE (un desktop cambia solo mentre
    #    qualcuno lo tocca); quel che non deve essere zero e' il numero di
    #    fotogrammi che cambiano.
    mossi = sum(1 for x in d[1:] if x > 1.0)

    # E i lampi di luminosita': un fotogramma la cui luce se ne va e torna,
    # anche quando il contenuto non e' cambiato abbastanza da farsi contare.
    lum = [media(f) for f in fot]
    lampi = [i for i in range(1, n - 1)
             if abs(lum[i] - lum[i - 1]) > 15 and abs(lum[i] - lum[i + 1]) > 15
             and abs(lum[i + 1] - lum[i - 1]) < 8]

    neri = [i for i in range(n) if lum[i] < 8]

    print("fotogrammi=%d  cambiati=%d  scarto massimo=%.1f  mediano=%.2f  soglia=%.1f"
          % (n, mossi, max(d), mediana, soglia))
    if mossi < 5:
        print("MISURA NULLA: la scena non si e' mossa, il conto dei flash non vale niente")
    print("FLASH=%d" % len(flash))
    for i, s, m in flash[:12]:
        print("   fotogramma %4d  scarto %6.1f  luminosita' media %5.1f" % (i, s, m))
    print("LAMPI DI LUMINOSITA'=%d" % len(lampi))
    print("quasi neri=%d" % len(neri))


main()
