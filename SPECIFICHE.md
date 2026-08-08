REMOTIX_V2 e' l'evoluzione naturale del precedente progetto REMOTIX, ne eredita alcune caratteristiche (alcune gia' sviluppate) e ne sviluppa di nuove ed inedite.
REMOTIX_V2 e' composto da 2 parti: una parte server e una client. Il server supporta esclusivamente SO Linux. Il client sara' destinato ad ambienti Linux e Adroid. == NO WINDOWS ==

Ecco le funzionalita' di Remotix-server:
- Distro agnostic
- Protocollo RDP proprietario
- Supporto nativo Wayland (no X11) e supporto per le applicazioni scritte per X11 (tramite Xwayland)
- Supporto per i seguenti DE:
  > GNOME
  > KDE
  > XFCE
  > LXQT
  > CINNAMON (?)
- Supporto Systemd
- Accelerazione HW (HEVC e AV1) tramite librerie Mesa/Vulkan (GPU agnostic) e encoder FFMPEG
- Audio Opus e PCM
- Supporto Microfono (non urgente)
- Trasporto: supporto QUIC/TLS
- Risoluzione schermo fino a 4K
- Sessioni persistenti (anche in multi-res, ovvero se chiudo una sessione in 720P devo poterla riprendere anche in 4K (e viceversa) e la risoluzione si adatta).
- sessioni multi-tenant (ogni utente del sistema puo' avere la sua connessione RDP separata dagli altri)
- Autenticazione PAM (rate limiting)
- Supporto per connessioni con queste tipologie:
  > banda minima 30 mbps
  > Valori di ping, jitter e perdita pacchetti abbastanza importanti
- Performance audio/video: minimo accettabile 480P, 25 fps, colore 24 bit, target 4K, 60 fps, colore 32 bit (best effort)
- Predisposizione futura al supporto multi-monitor
- Supporto alla clipboard testuale server-client

VINCOLI.
Un utente del sistema puo' avere innumerevoli sessioni testuali (ssh/tty) attive contemporaneamente, ma solo 1 grafica attiva (locale/remota) - Sessioni testuali e grafiche convivono contemporaneamente
Se un utente con sessione grafica locale attiva avvia anche una sessione RDP, la sessione RDP viene rifiutata con un messaggio di errore
Se un utente con sessione grafica RDP attiva avvia una sessione grafica locale, questa ha la priorita' e la sessione RDP viene killata

METODOLOGIA
Lo sviluppo del progetto dovra' essere portato avanti da 2 tipologie di agenti: Coder e Reviewer. Ho preparato 2 documenti in cui vengono riportate le regole che coder e reviewer devono seguire per svolgere il proprio lavoro. I documenti sono nella mia home

LICENZA
Da decidere sotto che tipo di licenza sviluppare il progetto
