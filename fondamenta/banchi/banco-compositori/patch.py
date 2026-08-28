import re, sys
p = '/media/REMOTIX/src/remotix-c/src/main.c'
s = open(p).read()
vecchio = "static gint fotogrammi = 30;"
nuovo = """/*
 * ⛔ SESSANTA, NON TRENTA, E IL PERCHE' STA IN R32 DI REFERENCE.md.
 *
 *    Questo numero e' il massimo che si dichiara a PipeWire, e Mutter ne
 *    consegna circa sei decimi: dichiarandone 30 ne arrivavano 18 — i famosi
 *    diciotto fotogrammi al secondo, che per due mesi sono stati cercati nel
 *    codificatore, nel protocollo e nella rete, ed erano scritti qui.
 *
 *    Misurato il 7 agosto 2026, sulla catena intera e fino al client: da 18,7 a
 *    32,4 fotogrammi al secondo a 1080p, cioe' il MINIMO di §3.1 di
 *    SPECIFICA.md superato.  Verificato dall'utente su tutti e tre i client —
 *    xfreerdp3, mstsc (AVC420 in GPU, 29-33) e RDM (RemoteFX Progressive, 23-29).
 *
 *    Oltre i 60 non si guadagna niente: dichiarandone 120 Mutter ne consegna
 *    sempre 37.
 *
 * ⚠ E STA QUI, NON IN /etc/default/remotix.  Quel file vive in RAM e si perde a
 *   ogni riavvio: il 7 agosto la riga che teneva spenta la copia zero e' sparita
 *   cosi', e l'utente si e' ritrovato in faccia un difetto noto.  Un valore da
 *   cui dipende quel che si vede non si affida a una riga che si puo' perdere.
 */
static gint fotogrammi = 60;"""
if vecchio not in s:
    sys.exit("riga non trovata")
open(p, 'w').write(s.replace(vecchio, nuovo, 1))
print("main.c aggiornato")
