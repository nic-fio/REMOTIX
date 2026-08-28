---
name: remotix-oltre-rdp
description: "REMOTIX — discussione APERTA e parcheggiata il 7 agosto 2026: lasciare RDP. Il criterio dell'utente, le tre strade, la domanda che ne chiude una gratis, e la correzione sui 18 fps"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2a0517e7-89e9-4d34-9714-c2d00ae6c5ce
  modified: 2026-08-07T16:11:19.601Z
---

Il **7 agosto 2026, a sera**, l'utente ha aperto una chiacchierata — dichiarata tale, senza
lavoro — su **sviluppare un protocollo nostro con client e server**, e l'ha **parcheggiata
per riprenderla più tardi**. La sua posizione, che è la cosa da non perdere:

> *«Sono stufo di andare incontro a problemi per colpa di protocolli che non si capisce bene
> come funzionano. Io ho le mie esigenze: se qualcosa le soddisfa bene, altrimenti il software
> ce lo scriviamo.»*

E prima, sul foglio bianco: *«comincio ad avere il prurito»*. È lo stesso capovolgimento di
[[remotix-requisito-prestazione]] un livello più in su — **le esigenze vengono prima del
protocollo**, non il contrario.

## Le tre strade sul tavolo

| | Costo | Muove i due numeri? |
|---|---|---|
| **Restare su RDP** | zero | il minimo sì (sta a monte del filo), il desiderato no: EGFX è tappato all'H.264, e il client Android di riferimento non lo decodifica |
| **Protocollo nostro + tre client** | **3-4 volte tutto il costruito finora**, più manutenzione per sempre, e cambia §1 della specifica (REMOTIX non è più «client RDP standard») | sì, ma solo dopo aver risolto la cattura comunque |
| **Protocollo Sunshine/Moonlight sul nostro host** ⭐ | una «fase 2 nuova», grande | **la strada più corta ai 60 fps a 4K**: decodifica hardware su Android è la loro strada normale |

## La terza, per come si terrebbe in piedi

**Non si forka il client.** Si implementa il loro protocollo sul **nostro** host e ci si collega
i client ufficiali presi dal negozio, vanilla; appunti e ridimensionamento a caldo non esistono
nella versione uno. Il fork si decide dopo averla usata. Così cade anche mezza questione della
licenza (GPL): implementare un protocollo non è portarsi in casa il codice di un host.

Il pezzo che **resterebbe nostro e non si butta** è quasi tutto REMOTIX: sessione GNOME senza
monitor, `RecordVirtual`, libei, logind, PAM, il sink audio inventato, gli appunti via Mutter. È
la parte che a Sunshine su GNOME **manca**.

E in dote: dall'altra parte del filo ci sarebbe un client **aperto e ricompilabile**, cioè il
banco migliore che il progetto abbia mai avuto — con mstsc uno schermo nero è un indovinello,
lì è una `printf`.

## ⛔ La domanda che chiude la terza strada GRATIS, e va fatta per prima

**Sunshine cattura una sessione GNOME senza monitor SENZA chiedere un permesso a video?** La sua
strada su Wayland passa storicamente per il **portale**, che §2 della specifica rifiuta per un
servizio non presidiato. Se non c'è una via diretta al compositore, quel che dovremmo scrivere
noi è di nuovo tutto, e la questione si chiude senza spendere niente. Un pomeriggio di banco,
[[remotix-prove-sul-banco-non-sull-utente]].

## ⛔ Correzione: i 18 fps NON misurano il compositore

Detto male da me in questa conversazione, e l'utente ha avuto ragione a dubitarne
(*«i compositor moderni su MESA non hanno prestazioni così scarse»*). Verificato il 7 agosto:

- **la trappola dei gruppi è chiusa**: il gestore systemd dell'utente ha `44 (video)` e
  `991 (render)`, quindi la Shell apre `/dev/dri` e GNOME **compone sulla GPU**, non in software
  (§8.6-ter di `REFERENCE.md`);
- **18 non è un nostro tetto**: a PipeWire dichiariamo **30** (`main.c:136`, `--fotogrammi`);
- **della misura non è dichiarata la scena**, e Mutter manda un fotogramma solo quando qualcosa
  cambia: una scena mossa a colpi di tastiera non misura una portata. **Tutte** le misure di
  fotogrammi sul desktop vero hanno questo vizio.

Quel che il 18 prova è **solo** che il collo di bottiglia non è né il protocollo né il
codificatore.

> ✅ **MISURATO la sera del 7 agosto 2026, e la risposta è una terza: nessuno dei due candidati.**
> I 18 sono **la cadenza che dichiariamo noi**: a PipeWire chiediamo 30 e Mutter ne dà 18;
> chiedendone 60 ne dà 37. Il tetto che resta a 37 è di Mutter — il client disegna 60 su uno schermo
> a 60 Hz — e **KWin (60) e wlroots (61) non ce l'hanno**. `REFERENCE.md` **R32**.
>
> **Ricaduta su questa discussione**: la terza strada (Sunshine/Moonlight) resta la più corta ai 60
> fps a 4K *sul filo*, ma non risolverebbe da sola il tetto della cattura, che sta a monte del
> protocollo. La strada più corta ai 60 misurata finora è **cambiare compositore**, non protocollo.

**Contro-prova che l'età di RDP non è il tappo**: `gnome-remote-desktop` punta a 60
(`TARGET_SURFACE_REFRESH_RATE`) e xrdp dichiara `h264_frame_interval=16` ms, cioè ancora 60 —
sullo stesso stack Wayland/Mesa.

Vedi [[remotix-metodo-documentazione]] e [[remotix-fase9-ripresa]].
