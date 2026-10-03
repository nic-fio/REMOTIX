# Le prove Android sul tuo telefono (fase 19 §5)

**Che cosa fa.** Le 10 prove di `fasi/19-nvidia.md` §5.1 le fa da solo, sul tuo telefono, con **Chrome**,
verso le scatole del server. Sono le stesse prove della suite, con gli stessi giudici: Chrome del telefono
prende il posto di quello del server, e basta. Giro pieno su GNOME (righe 1-10), giro corto su KDE, XFCE e
LXQt (righe 1, 2, 6, 9).

**Che cosa serve.** Phonestra aperto sul portatile (il telefono visto da adb), telefono **sbloccato**,
sulla stessa rete, possibilmente in carica. Le scatole accese e nessun altro giro sul server.

**Come si lancia** (dal portatile, nella cartella di REMOTIX):

    bash banchi/19-android/19-android.sh controlla       # telefono, chiamate, Chrome, server: tutto a posto?
    bash banchi/19-android/19-android.sh prova tutte     # tutte e 10 (circa un'ora e mezza)
    bash banchi/19-android/19-android.sh prova 7         # una riga sola, su GNOME
    bash banchi/19-android/19-android.sh prova 2 --desktop kde

**Il telefono resta tuo.**
- Apre **solo Chrome**, in schede sue, solo verso `192.168.0.2`. Le tue schede le annota all'inizio e non
  le tocca; alla fine chiude le sue e controlla che le tue ci siano tutte.
- **Mai durante una chiamata**: prima di ogni gesto guarda; se squilla, si ferma e aspetta (fino a 20
  minuti), poi rifà la prova interrotta.
- Per la durata del giro lo schermo non si spegne da solo, e nella prova 7 il telefono **si gira da sé**
  (verticale → orizzontale → verticale). Alla fine rimette tutto com'era: rotazione automatica, tempo di
  spegnimento, e Chrome chiuso se lo era.
- La prova 8 **chiude Chrome di colpo**: le schede normali tornano da sole, quelle **in incognito no** —
  chiudile prima, se ne hai.
- Se lo interrompi (Ctrl-C) rimette a posto il telefono da sé; se si interrompe male:
  `bash banchi/19-android/19-android.sh ripristina`.

**Dove finiscono i risultati.** Nel registro della suite, sul server, in
`/media/REMOTIX/misure/fase19-android/registro.jsonl` (browser «telefono»), con le fotografie della tela
e della pagina del telefono accanto. Alla fine lo script stampa il riassunto e il comando del rapporto.

**Due cose dette chiare.** La prova 9 (rete che cade) non spegne il Wi-Fi del telefono — si perderebbe il
collegamento con adb — ma taglia la linea dal lato del server, come fa la suite. Le prove 3-10 scrivono e
cliccano come mouse e tastiera (il caso DeX); il **dito vero** (tocco, trascinamento col dito) è la prova 2,
che guarda anche la **tastiera a schermo**: chiusa da sola, aperta e richiusa dal bottoncino ⌨ (lo stato lo
legge da Android).
