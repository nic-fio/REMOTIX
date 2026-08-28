---
name: come-guarda-nic-lo-schermo
description: "Da CHUWI/tty2 il quinto anello (xrdp+RemoteFX) NON c'è più: sessione GNOME Wayland locale, monitor DP-2 3440x1440. Le prove fatte prima del 17 ago sera passavano per quell'anello"
metadata:
  node_type: memory
  type: project
  originSessionId: defbf3a3-9ed8-459f-9f2a-dc508d102cbc
  modified: 2026-08-17T15:38:44.228Z
---

⭐ **17 agosto 2026, sera — Nic è FISICAMENTE davanti alla macchina.** `who` dà
`nicfio seat0 tty2`, `loginctl` dice `Type=wayland Remote=no`, e non c'è nessun
`Xorg :10`: **sessione GNOME Wayland nativa**. La macchina è **CHUWI Hi10 X1**
(`192.168.0.3`, Intel **N100**, 4 core, UHD Alder Lake-N) con **due uscite
accese**: `DP-2` **3440×1440** (il monitor su cui guarda) e `DSI-1` 800×1280
(il pannello del tablet, verticale).

⇒ **La catena torna a QUATTRO anelli**: compositore (su `192.168.0.2`) → nostro
codificatore → filo → Firefox+tela sul CHUWI → i suoi occhi. **Quel che vede
adesso sono i nostri pixel**, senza intermediari.

## ⛔ Ma il quinto anello è ESISTITO, e va tenuto per leggere il passato

Fino al 17 agosto ~17:30 la sessione grafica del CHUWI era `Xorg :10` avviato da
**xrdp** (2560×1080), guardata da Windows con un client RDP, e
`~/.xorgxrdp.10.log` diceva `got RFX capture` — **RemoteFX**, codec **a
tessere** con riscontro dei quadri, i cui guasti tipici sono alla lettera i due
sintomi riferiti (**blocchi rettangolari** e **immagine che smette di
aggiornarsi**). ⚠ Messo alla prova (`banchi/07-b47-controllo-xrdp.html`) aveva
**retto**, ma tutte le prove grafiche fino a quella sera sono passate di lì.

⛔ **E col RDP sono cambiate TRE cose insieme**, quindi un «adesso non si vede
più» non incolpa xrdp da solo: (1) l'anello RFX è sparito; (2) Firefox non gira
più su X11 ma su **Wayland**, con un percorso di composizione diverso; (3) la
CPU non porta più il codificatore RFX, e su un N100 l'AV1 in software la
saturava.

**How to apply:**
- un difetto **visivo** riferito da oggi in poi è **nostro o del browser**: non
  c'è più niente dopo la nostra tela;
- se un difetto visto prima del 17 sera **non si riproduce** adesso, non si
  scrive «era xrdp»: si scrive quale delle tre variabili è stata isolata;
- il testimone dal lato Linux resta utile, ma su Wayland `import -display :10`
  non vale più: si usa il testimone Marionette
  (`banchi/07-b46-testimone-disegno.py`) che tira giù **la tela** in PNG.

Vedi [[testimone-sul-desktop-vero]], [[la-prova-la-fa-lutente]],
[[prestazioni-sul-ferro-modesto]].
