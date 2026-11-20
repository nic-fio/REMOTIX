# 14 - canvas-limits su xfce, riga rossa 5120x1440 (19 nov 2026)

## Conclusione
NÉ difetto del prodotto NÉ attesa sbagliata dello strumento nel senso supposto: è una finestra estranea (la finestra di errore di Ubuntu/apport, causata dal crash di `blueman-applet` nella sessione di prova dk5) che si apre sopra la finestra di prova a schermo intero. Quando c'è una finestra normale sopra, labwc non nasconde più il pannello di XFCE, che copre i 26 px in alto, dove sta il bordo bianco. Il canvas e il browser mostrano fedelmente quello che c'è.
Classificazione: **STRUMENTO/AMBIENTE** (rumore del box), non prodotto. Cura: vedi in fondo.

## Fatti misurati
1. Foto del FAIL: `prove/shots/desk-canvas-5120x1440-xfce-261119-060846.png` (3840x1440, la stessa dimensione attesa). Non esiste la `-first` (il nuovo tentativo scatta solo se la foto non è mai ferma).
   - Quadranti rosso/verde/blu/giallo al posto giusto, dimensione giusta, nessuna scalatura.
   - Bordo bianco presente a sinistra, destra e in basso (6 px, pixel 255,255,255 poi colore).
   - In alto i primi 26 px sono la barra del pannello XFCE (grigia, con orologio e vassoio): il bordo bianco in alto è coperto.
   - Al centro compare la finestra "Ubuntu - Sorry, Ubuntu 26.04 has experienced an internal error / Send problem report" (apport-gtk). La barra delle applicazioni mostra la voce "Ubuntu".
   - La foto precedente della stessa serie (5120x2880, stesso giro) è perfetta: niente pannello, niente finestra. Quindi la finestra di errore è comparsa fra le due scene.
2. Origine della finestra: `/var/crash/_usr_bin_blueman-applet.1010.crash` (utente dk5, Date 05:49:42 UTC) con Traceback in `TransferService._on_dbus_name_appeared` -> `GDBus NoReply: Message recipient disconnected` (il servizio obex di bluez nel box sparisce mentre blueman lo interroga). È una corsa fra servizi nel box, senza adattatore Bluetooth; non c'entra con REMOTIX. Anche la foto `desk-reattach-2-2560-xfce-261119-060846.png` dello stesso giro mostra la voce "Ubuntu" in barra.
3. Riesecuzione 8 volte di `check-desktop.py --box xfce --only canvas-limits --no-cap` (06:49-07:10, uscite `run1..8.out`): **1 FAIL su 8** (run1, 06:49:24, scena 5120x1440, stesso messaggio) e 7 PASS. Il FAIL è proprio il giro in cui `blueman-applet` ha avuto il crash (file .crash di 06:49:42 CET); nei 7 PASS non è nato nessun nuovo .crash (apport non riscrive un report già presente: il file è rimasto quello delle 05:49) né si è visto il dialogo. La foto del FAIL di run1 (`desk-canvas-5120x1440-xfce-261119-064924.png`) è identica alla prima: pannello in alto + finestra "Ubuntu".
4. Misura mirata (`diag-canvas-xfce/measure.py`, uscite `a1..a7.out`, dati `m-a*.json`): sessione dk5, sequenza breve (1280x720 -> 5120x2880 -> 5120x1440) 3 volte (a1, a3, a6), diretta (a4), sequenza completa delle 10 scene (a5, a7); a2 è fallita per un errore dello script (socket Wayland non ancora pronto), non contata. Dopo l'ultimo cambio di vista, SENZA input, foto del canvas ogni 0,5 s per 34 s + `grim`/`wlr-randr` dentro labwc ogni ~0,35 s:
   - Prima foto utile del canvas a 0,8-1,2 s dopo che la pagina ha "settle_view" (primo fotogramma + 3 s): già giusta e identica fino alla fine (68 foto per giro x 6 giri, **0 sbagliate**, bordo bianco in alto sempre 253-255).
   - `wlr-randr`: l'uscita è 3840x1440 in tutte le 140 letture di ogni giro; `grim` (strisce 1x40 px al centro in alto): bianco, bianco, nero... = identico al canvas del browser. Quindi labwc mostrava già l'immagine giusta e il browser la stessa nello stesso istante: nessun ultimo fotogramma mancante.
   - La finestra di prova si ridimensiona subito: `rx-geom.log` mostra size 1264x720 -> 3840x2160 -> 3840x1440 a ~18 s l'una dall'altra, ognuna al cambio di vista.
   - Dopo 1 px di mouse: nulla cambia (stesse righe).
   - Autoguarigione: non c'è nulla da guarire; l'immagine è giusta da subito. (La vecchia attesa fissa non fa differenza.)
5. Prova del meccanismo (fase 2 di ogni misura, 6 volte su 6): aprendo una normale finestra (`geom-window.py scene`, 1800x1000) sopra la finestra a schermo intero, **da 0,8 s dopo** il pannello XFCE compare in alto sopra il bordo bianco (pixel 73,78,75 / 37,30,25 al posto di 255 e 1,1,1; "edges WRONG", quadranti ok), identico al FAIL. Chiusa la finestra (kill), dopo ~1 s il bordo bianco in alto torna (254,253,255). Cioè qualsiasi finestra normale sopra una finestra a schermo intero fa riapparire il pannello: è il comportamento di labwc/XFCE, indipendente dal canvas.
6. Il vecchio strumento (`prove-giro2/check-desktop.py`) fa la stessa `look_frame` su una sola foto; il confronto dei file mostra differenze solo nelle attese (fisse 6 s + una foto; ora aspetta `ready` + due foto uguali). Con il dialogo presente avrebbe fallito allo stesso modo: nei 4 giri precedenti semplicemente `blueman-applet` non era andato in crash. (Il crash è raro e casuale: 2 sessioni su ~16 di questa mattina, la prima nel giro originale e una in run1.)

## Verdetto
- Prodotto: nessuna prova di difetto. Cattura, invio, adattamento dimensione OK in 6/6 misure.
- Strumento: l'attesa "ferma" non è la causa; il dichiarare FAIL senza ritentare una foto con una finestra estranea sopra è la parte fragile. Una foto ferma e sbagliata a causa di una finestra non voluta è rumore dell'ambiente.

## Cura proposta per `check_canvas` (NON applicata)
1. Prima di scattare, nel box: chiudere finestre estranee del dk5 (es. rimuovere `/var/crash`-notifiche con apport disabilitato nell'utente di prova, `export APPORT_...`/`pkill -u dk5 apport-gtk`) oppure prepararlo all'inizio: nascondere il pannello o disattivare `blueman` per gli utenti di prova (un `.desktop` autostart con `Hidden=true` in `~/.config/autostart/blueman.desktop`, come già si fa per altri semi dell'utente).
2. In `check_canvas`, se la foto è ferma e sbagliata, controllare con `ps -u dk5` / foto se esiste un'altra finestra (apport-gtk) e: o chiuderla e rifotografare una volta, dichiarandolo (come già per «mai ferma»), oppure BLOCKED con causa "finestra estranea (apport-gtk)", non FAIL del prodotto.
3. In ogni caso mantenere la foto `-first`.

## Stato del box
Nessuna sessione viva (loginctl: solo manager di root); `dk5` terminato. Aggiunti da me: `lavoro/diag-canvas-xfce/*`, 42 `prove/shots/diag-*.png` (nomi nuovi), pacchetto `grim` installato nel box xfce (apt). Il `.crash` di dk5 è rimasto (non toccato).
