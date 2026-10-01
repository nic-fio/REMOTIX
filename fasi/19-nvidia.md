# Fase 19 — La codifica sempre sulla scheda: Vulkan per primo

*Aperta il **1 ottobre 2026** (`DECISIONI.md` §10.27). Requisito dell'utente: su una macchina con una scheda
capace di codificare, REMOTIX codifica **sulla scheda**, NVIDIA compresa. Oggi su NVIDIA si ripiega sul
processore (OpenH264).*

## 1. La strada (decisa il 1 ott, `DECISIONI.md` §10.27)

Si sceglie **per capacità**, all'avvio, non per marca:

| ordine | strada | oggi la usano |
|---|---|---|
| 1 | **Vulkan Video** (H.264 per Firefox, HEVC per Chrome) | AMD (RADV, `[M]` Mesa 25.0.7), NVIDIA (driver proprietario) |
| 2 | **VA-API** (`src/vadiretta.c`, com'è oggi) | Intel integrata e Arc (in Vulkan solo sperimentale, `[M]` Mesa 26.2.3) |
| — | ⛔ niente processore | senza scheda capace REMOTIX non si installa |

## 2. Il lavoro
1. La strada Vulkan (codifica H.264 e HEVC, copia zero da dmabuf, conversione dei colori sulla scheda), provata
   sulla Radeon contro VA-API: flusso dello stesso tipo, qualità e tempi non peggiori.
2. Via il ripiego software (`src/ripiego.c`, `src/colori709.c` se non serve più alla strada dalla memoria,
   OpenH264, SVT-AV1) dal prodotto, dai pacchetti, dal catalogo e dal motore dell'installatore; il controllo
   preliminare rifiuta senza una scheda capace, con la ragione.  ⭐ Fatto dalla linea 1 (§3);
   `src/colori709.c` RESTA: serve alla strada «dalla memoria» di VA-API.
3. **La rete anti-regressione** (parola dell'utente, 1 ott: *«bisognerà rivedere tutti i 4 DE per evitare che uno
   di loro smetta di funzionare»*): la suite completa della fase 15 gira **due volte** sulle 4 scatole (GNOME, KDE,
   XFCE, LXQt), coi browser veri in 4K — **Intel = VA-API** (niente deve rompersi di ciò che oggi è verde) e
   **Radeon = Vulkan** (la scheda passata alle scatole come nella fase 16, `--scheda amd`). Un desktop è a posto
   solo se è verde in tutti e due i giri. T10 ridotto al rifiuto pulito nelle VM; le prove complete
   dell'installatore nei contenitori con la scheda vera.
4. ❓ NVIDIA: serve una scheda vera (nel server, o macchina in affitto).

## 3. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| `9162e76` | **via il ripiego su CPU dal prodotto**: tolti `src/ripiego.c/.h` (OpenH264 via dlopen, SVT-AV1), il confine `sw_*` di `codificatore.c`, `codificatore_ripiego_software/_software_pronto/_software_rimedio`, `CRF_SOFTWARE`, `--software` di `--prova-codifica`, AV1 dal rilievo. `codificatore_di()` apre solo `h264_vaapi`/`hevc_vaapi`; un altro nome si rifiuta con la ragione. `--prova-codifica`: esito `hardware`\|`nessuno`, niente `rimedio`, codici **0** scheda · **1** si apre ma non esce · **2** uso · **3** nessuna scheda. All'avvio il server lo dichiara (*«QUESTO SERVER NON SA CODIFICARE VIDEO»*, con la ragione per codec) e l'`ECCOMI` non offre codec. Makefile: via openh264/SvtAv1Enc da CFLAGS, LIBS, `MINIMI` e intestazioni controllate (`-ldl` resta: libselinux in `figlio.c`). `colori709.c` RESTA (strada «dalla memoria»). Contenitori di costruzione e scatole senza le due librerie; `costruisci-tutti.sh` rifiuta un `ldd` che le nomina. Banchi 18-*: compilano senza `src/ripiego.c` (18-software lo prende da git `6bacca7`, come storia) | `DECISIONI.md` §10.27: *«niente cpu senza scheda»*, *«eliminare la questione della codifica su cpu senza scheda»*, indipendenza da ffmpeg e altri pezzi per le licenze | `[M]` 1 ott, sul server (`/media/REMOTIX/src/f19-cpu`): `--prova-codifica` Intel renderD128 H.264 e HEVC = `hardware`, codice 0; Radeon renderD129 H.264 e HEVC = `hardware`, codice 0; `--nodo /dev/dri/renderD199` = `nessuno`, codice **3**; `--software` = uso, codice 2. Server su 7633 col driver VA nascosto (`LIBVA_DRIVERS_PATH` vuota): riga ⛔⛔ all'avvio, `offerti` vuoto; con la scheda `«hevc,h264»`. `ldd` del binario (contenitore) senza openh264/SvtAv1 | no |
| `35e3b44` | **via OpenH264 e SVT-AV1 dai pacchetti**: `debian/control` (Build-Depends, Recommends `libopenh264-8 \| libopenh264-cisco8`), `remotix.spec` (BuildRequires, `Recommends: openh264` su Fedora e Alma), `PKGBUILD` (depends `openh264`, `svt-av1`), il testo delle licenze | come sopra | — (si costruiscono col rilascio) | no |
| `2246cbc` | **via OpenH264 e SVT-AV1 dall'installatore, e il controllo preliminare che rifiuta senza scheda**: catalogo 2026.10.01.9 (seq. 9) senza il deposito `openh264`, `software_di_serie`, `pacchetti_software`; motore senza il tipo di deposito «openh264» (`fedora-cisco-openh264`, `epel-cisco-openh264`, `repo-openh264`), `deposito.resta_epel`, i fatti `h264.software`/`h264.openh264`, le condizioni C-RIPIEGO; `consenso.deposito.openh264` ritirato (un file vecchio finisce fra le «superflue»); RX-H264-005 e RX-GPU-001 ritirati, RX-FUORI-005 riscritto senza ripiego. ⭐ `motore/strade.go`: la tabella `StradeCodifica` (vulkan dichiarata e non attiva, vaapi attiva) e `VerdettoScheda` — per aggiungere Vulkan basta `Attiva: true` con la sua `Rileva`/`Schede`. Codici nuovi BLOCCANTI: **RX-GPU-003** nessuna scheda, **RX-GPU-004** solo NVIDIA col driver proprietario (arriva con la strada Vulkan), **RX-GPU-005** nessuna Intel/AMD (virtio, VMware, nouveau), **RX-GPU-006** Intel/AMD che su questa distro non codifica senza driver da aggiungere (oggi AMD su Alma). La scheda che si completa con un deposito di terzi resta un avviso col consenso (D5). La prova dopo l'installazione: uscita 3 = FAIL. EPEL su Alma RESTA (KDE, RPM Fusion EL): esce solo la parte SVT-AV1 | `DECISIONI.md` §10.27 | `[M]` `installatore/costruisci.sh prove`: **205 PASS**, 0 FAIL, `go vet`/`gofmt` puliti; controprova: col verdetto che non rifiuta mai, tre prove diventano rosse. ⚠ Non rimisurato se `intel-media-driver` di RPM Fusion EL tiri dipendenze da EPEL. ⚠ Una macchina installata col motore della fase 18 col passo «openh264» nel registro non si disinstalla col motore nuovo (solo scatole di laboratorio) | no |
| (questo commit) | **la tela al massimo 4096×2304** (era 7680×4320): `RCP_TELA_L/A_MASSIMA` in `rcp.h` (e il gemello `banchi/rcp/`), `TELA_L/A_MASSIMA` in `pagina.html`, `RCP.md` §4.5, `SPECIFICHE.md` §6.1-bis. ⭐ **Sopra il massimo non si rifiuta: si riduce** — il lato che sfora va al massimo, l'altro resta (5120×2880 → 4096×2304, 5120×1440 → 4096×1440), con la riga «⚠ RIPIEGO DICHIARATO (§4.5)» nel registro, in `ATTACCA` (prima era `ERRORE_PROTOCOLLO`) e in `ADATTA_TELA` (prima `TELA(MISURA_FUORI_LIMITI)`, ora `TELA(ADATTATA)` alla misura ridotta). Sotto il minimo (320×240) e il dispari restano rifiutati come prima. La pagina chiede già lei al più il massimo, con la stessa regola (`tela_da_chiedere()`); il massimo è una costante del protocollo, non un campo dell'`ECCOMI` (il filo non cambia). Il controllo della misura massima del driver in `codificatore.c` RESTA: è del driver, non del protocollo | decisione dell'utente, 1 ott: *«4096 max di larghezza va benissimo, non ho mai preteso di più»* — H.264 su Intel (`EncSliceLP`) si ferma a 4096 px per lato e Firefox su Linux riceve solo H.264; 2304 = 16:9 a 4096 e `MaxFS` dei livelli H.264 5.1/5.2 (36 864 macroblocchi) | `[M]` 1 ott, portatile: `rcp_misura_ammessa()` diretta — 3840×2160 e 4096×2304 uguali, 5120×2880 e 7680×4320 → 4096×2304, 5120×1440 → 4096×1440, 319×240 rifiutata; `tela_da_chiedere()` della pagina (node) dà gli stessi numeri; costruzione nel contenitore e sul server (`enter.sh`) pulita. ⚠ **NON provato un attacco vero** (cliente Python o Chrome) sul prodotto acceso: le parole d'ordine di `prova`/`prova2` sono cambiate il 29 set e quella in `credenziali-banchi` è respinta da PAM. ⚠ Banchi vecchi che pretendono il rifiuto sopra 7680 (`04-b31` caso 5, `06-b36` casi 14-15, `06-b35`, `06-b38`, `06-b40`, `01-b4`) non aggiornati | no |
