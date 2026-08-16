#!/usr/bin/env python3
"""06-b34-leggi.py — il testimone, decodificato.

Legge il file che il testimone scrive DENTRO la sessione grafica — una riga
per carattere, «<nanosecondi> <byte UTF-8 in esadecimale>» — e ne fa una
stringa leggibile piu' il verdetto sui canarini.

    python3 06-b34-leggi.py /home/provat6/testimone.txt --atteso 'aèò\\@a'

===========================================================================
⛔⭐ IL CANARINO, E PERCHE' ESISTE
===========================================================================

`LEZIONI.md` §1.9 regola 1: *una lettura negata non e' una lettura che dice
zero*.  Qui il caso e' esattamente quello, ed e' costato mezz'ora il 16 agosto
2026: i primi tre giri del banco hanno dato **testimone vuoto**, e «il
carattere non e' arrivato» sembrava la misura.  ⛔ Non lo era: i caratteri
arrivavano benissimo — andavano nella **casella di ricerca dell'overview** di
GNOME Shell, perche' nessuna finestra aveva il fuoco.  ⭐ La prova e' una
fotografia del desktop con dentro «zya» scritto nella ricerca.

⇒ Da cui il canarino: ogni prova comincia e finisce con una **`a`**, che sta
  sul tasto **30 in `it`, `us` e `de`** (calcolato da `06-b34-tabella.c`).

    · canarini presenti  ⇒ il fuoco era sul testimone, e quel che sta in mezzo
                           E' una misura;
    · canarini assenti   ⇒ ⛔ la prova non e' ROSSA, e' **INVALIDA**: non si e'
                           misurata la tastiera, si e' misurato il fuoco.

⛔ Senza questo, «e' arrivato il carattere sbagliato» e «non e' arrivato
   niente perche' guardava altrove» hanno lo stesso aspetto — e il secondo si
   legge come il primo, cioe' si accusa il prodotto di un difetto del banco.
"""
import argparse
import sys

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# I nomi dei caratteri che non si vedono, perche' una riga di verdetto con
# dentro un a-capo vero e' una riga che si legge male.
NOMI = {"\n": "⏎", "\r": "⏎r", "\t": "⇥", "\x1b": "⎋", "\x7f": "⌫", " ": "␣"}


def leggi(percorso):
	righe = []
	with open(percorso, "r", encoding="utf-8", errors="replace") as f:
		for r in f:
			r = r.strip()
			# ⛔ `STTY` e' la RIGA CHE DICE SE IL TESTIMONE PUO' VEDERE LE
			#    SCORCIATOIE, e si salta come le altre righe di servizio.
			#    ⚠ `[M]` 16 agosto 2026: con `isig` acceso, un `Ctrl+Z` non
			#      arriva come byte — **sospende il testimone**, e il file resta
			#      vuoto.  Cioe' l'aspetto di «la scorciatoia non e' arrivata»
			#      quando invece e' arrivata benissimo.  ⇒ La riga si stampa,
			#      cosi' chi legge sa se quel vuoto e' una misura o un guasto
			#      dello strumento.
			if r.startswith("STTY"):
				print(f"    ⚙ {r}   (serve «-isig», o Ctrl+Z sospende il "
				      f"testimone invece di arrivare)")
				continue
			if not r or r.startswith(("PRONTO", "AZZERATO")):
				continue
			p = r.split()
			if len(p) != 2:
				continue
			try:
				ns = int(p[0])
				grezzo = bytes.fromhex(p[1])
			except ValueError:
				continue
			# ⚠ `errors="replace"`: un byte solo di una sequenza multibyte NON
			#   e' un carattere, ed e' meglio vederlo come tale che perderlo.
			righe.append((ns, p[1], grezzo.decode("utf-8", errors="replace")))
	return righe


def mostra(c):
	return NOMI.get(c, c)


def main():
	p = argparse.ArgumentParser(description="il testimone, decodificato")
	p.add_argument("file")
	p.add_argument("--atteso", default="",
	               help="la stringa attesa, canarini compresi")
	p.add_argument("--canarino", default="a",
	               help="il carattere che deve esserci in testa e in coda")
	p.add_argument("--dopo-ultimo", default="1b",
	               help="⛔ si butta tutto fino all'ULTIMA occorrenza di questo "
	                    "byte compresa (⎋ = 1b): e' il preludio che porta il "
	                    "fuoco sul testimone, non la misura.  «» = non buttare "
	                    "niente")
	p.add_argument("--zitto", action="store_true")
	a = p.parse_args()

	righe = leggi(a.file)

	# ⛔⭐ IL PRELUDIO NON E' LA MISURA, E SI BUTTA — 16 agosto 2026.
	#
	# Ogni prova comincia con tre ⎋, che servono a uscire dall'overview di
	# GNOME Shell e a portare il fuoco sul testimone (vedi il riquadro in
	# testa).  ⚠ Quelli che il testimone riceve — cioe' quelli mandati DOPO
	# che il fuoco e' arrivato — finiscono nel file come `1b`, e sono da uno a
	# tre a seconda di quanti ne e' servito: **un numero che non si puo'
	# conoscere non si mette in un atteso** (`LEZIONI.md` §1.9, quinta regola).
	#
	# ⇒ La misura comincia DOPO l'ultimo ⎋.  ⚠ E le sonde non contengono mai
	#   un ⎋, per costruzione: se ce ne fosse uno in mezzo, questa riga
	#   taglierebbe via la misura invece del preludio.
	if a.dopo_ultimo:
		ultimo = -1
		for i, (_, hx, _) in enumerate(righe):
			if hx == a.dopo_ultimo:
				ultimo = i
		if ultimo >= 0:
			buttate = ultimo + 1
			righe = righe[buttate:]
			if not a.zitto:
				print(f"    preludio: buttate {buttate} righe fino "
				      f"all'ultimo «{a.dopo_ultimo}» compreso")

	testo = "".join(c for _, _, c in righe)

	if not a.zitto:
		print(f"    testimone: {len(righe)} caratteri")
		for ns, hx, c in righe:
			print(f"      {ns}  {hx:<10s} «{mostra(c)}»")
	print(f"    ARRIVATO  «{''.join(mostra(c) for c in testo)}»")
	if a.atteso:
		print(f"    ATTESO    «{''.join(mostra(c) for c in a.atteso)}»")

	# ⛔ PRIMA il canarino, POI il confronto: se il canarino non c'e', il
	#    confronto non ha nessun significato e stamparlo sarebbe peggio che
	#    tacere — chi legge crederebbe a un rosso che non e' un rosso.
	if a.canarino:
		testa = testo[:1] == a.canarino
		coda = testo[-1:] == a.canarino
		if not (testa and coda):
			# ⛔⛔ E QUI CI SONO DUE STATI, NON UNO — `[M]` 16 agosto 2026, e
			#     li ha separati il controllo positivo.
			#
			# Col guasto «keymap letta una volta sola» innestato, la sonda e'
			# tornata **`ayzâ`**: la `\` mandata come tasto 41 su una sessione
			# tedesca e' il **circonflesso morto**, che si e' MANGIATO il
			# canarino di coda combinandocisi.  ⇒ Il canarino mancava, ma il
			# fuoco c'era eccome: chiamarla «INVALIDA» come una prova a
			# testimone vuoto vorrebbe dire buttare via la misura piu'
			# importante del banco.
			#
			# ⇒ Nessun carattere = il fuoco non c'era: **INVALIDA**.
			#   Qualche carattere ma canarino mangiato = **SOSPETTA**, e quel
			#   che e' arrivato si legge e conta.
			if not righe:
				print(f"    {GIALLO}⛔ INVALIDA: non e' arrivato NIENTE — il "
				      f"fuoco non era sul testimone, non si e' misurata la "
				      f"tastiera{GRIGIO}")
				print("VERDETTO INVALIDA")
				return 3
			print(f"    {GIALLO}⛔ SOSPETTA: il canarino «{a.canarino}» "
			      f"manca in {'testa' if not testa else ''}"
			      f"{' e ' if not testa and not coda else ''}"
			      f"{'coda' if not coda else ''}, ma dei caratteri SONO "
			      f"arrivati ({len(righe)}).{GRIGIO}")
			print(f"    {GIALLO}   ⇒ non e' «il fuoco era altrove»: e' che quel "
			      f"che e' arrivato non e' quel che si e' mandato — un tasto "
			      f"morto che si mangia il canarino e' gia' il guasto{GRIGIO}")
			if a.atteso:
				print(f"    {ROSSO}NON COMBACIA{GRIGIO}")
			print("VERDETTO SOSPETTA")
			return 1
		print(f"    {VERDE}canarini presenti{GRIGIO}: il fuoco era sul "
		      f"testimone, quel che sta in mezzo E' una misura")

	if a.atteso:
		if testo == a.atteso:
			print(f"    {VERDE}COMBACIA{GRIGIO}")
			print("VERDETTO COMBACIA")
			return 0
		print(f"    {ROSSO}NON COMBACIA{GRIGIO}")
		print("VERDETTO DIVERSO")
		return 1
	print("VERDETTO SOLO-LETTURA")
	return 0


if __name__ == "__main__":
	sys.exit(main())
