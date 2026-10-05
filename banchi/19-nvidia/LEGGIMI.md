# Il banco NVIDIA — da leggere prima di noleggiare

Serve a provare REMOTIX su una scheda NVIDIA vera, in uno o due giorni di noleggio, senza
improvvisare: dal portatile si lancia un comando, il banco fa tutto da solo e riporta a casa le
evidenze. (`fasi/19-nvidia.md` §2.4.)

## Che cosa noleggiare

- **Una macchina intera, o una macchina virtuale con la scheda passata intera.** ⛔ Non un
  «contenitore con GPU» (tipo vast.ai, RunPod): lì non si è padroni della macchina, e REMOTIX
  vuole systemd, gli utenti veri e `/dev/dri`.
- **La scheda: NVIDIA serie RTX 20 / T4 o più nuova, col codificatore video.** Vanno bene T4, L4,
  L40S, A10, A16, RTX 4000/6000 Ada, RTX 30 e 40. ⛔ **Non A100, H100, H200**: sono schede da calcolo
  senza codificatore video, e il banco si fermerebbe subito.
- **Il sistema: Ubuntu 26.04 o Debian 13, se il noleggiatore li offre; altrimenti la Ubuntu più
  recente che offre, dalla 20.04 in su.** REMOTIX sulle Ubuntu vecchie non gira (la loro OpenSSL è
  troppo vecchia), ma il banco porta il sistema da solo alla 26.04 prima di cominciare, un salto alla
  volta: circa un'ora per salto (dalla 24.04 uno, dalla 22.04 due, dalla 20.04 tre) e i riavvii, che
  fa da sé. ⛔ La macchina si restituisce aggiornata: questo la pulizia non lo disfa.
- **Il driver NVIDIA 550 o più recente.** Se la macchina arriva senza, lo mette il banco (e la riavvia
  da solo una volta).
- **Accesso root via ssh**, oppure un utente con `sudo` senza parola d'ordine (per esempio `ubuntu`).
- Almeno 30 GB di disco libero e 8 GB di memoria (sotto i 12 GB il banco aggiunge da solo 4 GB di
  scorta sul disco, e li toglie alla fine). Il monitor non serve.

## Il giorno prima, sul portatile (una volta sola)

Dalla cartella di REMOTIX, sul ramo `fase-19`:

    bash banchi/19-nvidia/19-nvidia.sh prepara

Costruisce i pacchetti di REMOTIX e l'installatore, e mette tutto in una «valigia». Una ventina di
minuti.

## Il giorno del noleggio

    bash banchi/19-nvidia/19-nvidia.sh tutto INDIRIZZO

(con un utente diverso da root: `UTENTE=ubuntu bash banchi/19-nvidia/19-nvidia.sh tutto INDIRIZZO`;
con una chiave ssh particolare: `CHIAVE=~/.ssh/noleggio`.)

Il banco, in ordine: porta Ubuntu alla 26.04 se è più vecchia · guarda la scheda e il driver · mette il driver se manca · installa il desktop
leggero (XFCE) e i due browser · installa REMOTIX **con il suo installatore** · prova che codifichi
H.264 e HEVC sulla NVIDIA · fa girare il banco di confronto della codifica · fa girare le prove della
suite (accesso, prima immagine, aggiornamento dello schermo, tela all'attacco, video, stacco e
riattacco, riattacco a misura diversa) con Firefox e Chrome veri · impacchetta le evidenze e le porta
sul portatile, in `misure/19-nvidia/`.

Non serve restare davanti: se la connessione cade il banco continua, e lo si ritrova con
`bash banchi/19-nvidia/19-nvidia.sh segui INDIRIZZO`.

**Quanto dura, a occhio:** mezza giornata. Driver e programmi da mezz'ora a un'ora (dipende dalla rete
della macchina), il confronto della codifica fino a un'ora, la suite un paio d'ore. Un giorno di
noleggio basta; il secondo è margine.

## Alla fine

1. Le evidenze sono già sul portatile (`misure/19-nvidia/remotix-nv-….tar.gz`); dentro, `passi.txt`
   dice in una riga per passo che cosa è verde e che cosa no.
2. `bash banchi/19-nvidia/19-nvidia.sh pulisci INDIRIZZO` — toglie REMOTIX, gli utenti del banco,
   tutti i programmi messi dal banco (driver compreso, se l'aveva messo lui) e rimette i depositi
   com'erano. Si rifiuta se le evidenze non sono ancora state portate via.
3. Restituire la macchina.

## Se qualcosa va storto

- `bash banchi/19-nvidia/19-nvidia.sh stato INDIRIZZO` dice a che passo si è arrivati.
- Si riprende con `tutto` di nuovo: i passi già fatti si saltano.
- I controlli iniziali rossi fermano tutto (per esempio: la scheda non ha il codificatore, o il sistema
  non è Debian 13 / Ubuntu 22.04-26.04). Il perché è in `controlli.txt`, dentro le evidenze.
