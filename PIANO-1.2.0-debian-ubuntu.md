# REMOTIX 1.2.0 per Debian 13 e Ubuntu 26.04 — consegna per la prossima sessione

Scritto il 25 nov 2026, a fine lavoro su Fedora. NON è ancora un piano approvato: è il punto di partenza.
Sostituisce nel numero di versione il vecchio `PIANO-1.0.2-debian-ubuntu.md` (mai approvato: le sue due correzioni
confluiscono qui).

## Che cosa ha deciso il proprietario (25 nov 2026)

- Fedora 45 esce come **1.2.0**. Anche Debian 13 e Ubuntu 26.04 passano alla **1.2.0**, per tenere allineato il codice.
- Perimetro, parole sue: «allineare il più possibile, tenendo conto di: specificità della distro e versione di KDE».
- Si lavora sulle macchine virtuali con la Radeon; niente contenitori (nemmeno per costruire i `.deb`).
- Su KDE, nella chiusura per accesso locale, la chiusura gentile aspetta 5 secondi (deciso su Fedora).
- Nei file di licenza non deve restare alcun riferimento a materiale che il pacchetto non contiene.
- Sua stima: almeno tre giorni per distribuzione.

## Che cosa c'è già

- **Studio delle differenze**: `STUDIO-1.2.0-differenze.md` (30 voci di codice classificate: 9 portabili così come
  sono, 3 da adattare, 10 specifiche di Fedora, 4 legate al KDE nuovo di Fedora, 4 dubbie; più 13 voci «Ubuntu le ha,
  Debian no»). Da leggere per primo.
- **Banco di Debian**: quattro macchine virtuali pulite (GNOME 48.7, Plasma 6.3.6, XFCE 4.20, LXQt 2.1.1) in
  `/media/REMOTIX-DEBIAN/vm-radeon/`, istantanea `pulito`; script e scheda in `debian13/server/` (`vm-radeon.sh`,
  `prepara-server-vm.sh`, `VM-BANCO.md`). Dopo un riavvio del server: `prepara-server-vm.sh`.
- **Immagini**: in `/media/DOWNLOAD` del server le quattro live di Debian 13.8.0 e le quattro di Ubuntu 26.04.1.
- **Fedora come riferimento**: `fedora45/` (codice, `PIANO.md`, registro dei problemi F1–F36, manuali 1.2.0).

## Che cosa manca prima di cominciare

1. Banco di Ubuntu: quattro macchine virtuali (lo script esiste: `ubuntu26.04/server/vm-radeon.sh`, da riprovare).
2. Una macchina virtuale di costruzione per i `.deb` di ciascuna distribuzione (oggi `build/build-deb.sh` usa i
   contenitori, vietati): sul modello di `fedora45/build/build-rpm.sh`.
3. Uno script per le prove da chiavetta su Debian (c'è per Ubuntu e per Fedora: `server/live-installa.sh`).

## Scoperta dello studio da tenere presente

Debian è indietro anche rispetto a Ubuntu: il lavoro fatto su Ubuntu il 18-19 novembre non è nel codice di Debian.
Allineare Debian vuol dire prima portarla al livello di Ubuntu, poi aggiungere ciò che viene da Fedora.

## Domande per il proprietario (con la mia raccomandazione)

1. Debian va portata prima al livello di Ubuntu e poi allineata a Fedora? **Sì** per le parti generali; le parti
   misurate solo sulle versioni di GNOME e KDE di Ubuntu solo se sono controlli fatti al momento dell'uso, dichiarate
   «non provate su Debian».
2. Quanto provare. **Proposta**: prove di base su tutti gli otto desktop, «il locale chiude il remoto» con programmi
   aperti sulle quattro schermate di accesso di ciascuna distribuzione, giro completo su GNOME e KDE, aggiornamento
   dalla 1.0.1, poi le sue prove da chiavetta. Come e quando lo decide lui.
3. Sezione «Requirements» in apertura anche nei manuali utente di Debian e Ubuntu? **Sì, breve.**
4. GNOME, XFCE e LXQt restano senza «ultima difesa», come su Fedora? **Sì**, ma con la prova a programmi aperti anche
   su di loro; si interviene solo se fallisce.

## Ordine di lavoro proposto

Prima Ubuntu (più vicina a Fedora), poi Debian. I due banchi si preparano in parallelo; le prove con la Radeon vanno
in fila (una sola scheda). Per ogni distribuzione: piano nel suo `PIANO.md` → OK del proprietario → codice →
revisore → pacchetto → banco → chiavetta → manuali → sito.

## Regole da non dimenticare

- Mai cambiare il comportamento del prodotto senza l'OK del proprietario; mai cancellare o sovrascrivere senza ordine.
- «Il locale chiude il remoto» si prova sempre con programmi aperti nel desktop remoto e su macchina vera prima di
  pubblicare (registro F36 di Fedora).
- Ogni problema chiuso o rinviato va nel registro dei problemi della sua distribuzione.

## Aggiunte del 25 nov, notte

- **Sito**: regola del proprietario — «I problemi dello sviluppo stanno su github. Sul sito solo le novità delle varie
  versioni». Le pagine sono state rifatte in locale (`~/remotix-1.2.0-fedora/sito-nuovo/`); alla 1.2.0 di Debian e
  Ubuntu le loro pagine prendono solo la voce di novità della versione.
- **NVIDIA**: i manuali pubblicati di Debian e Ubuntu (e `docs/SPECS.md`, `DECISIONS.md`) dicono ancora che NVIDIA non
  è mai stata provata. È falso: è stata misurata su una RTX 4090 il 5-6 ott 2026 su Ubuntu 26.04 (commenti `[M]` nel
  codice). Da correggere come nei manuali di Fedora; Vulkan Video va descritta come strada generale, non «di NVIDIA».
