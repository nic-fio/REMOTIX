#!/bin/bash
#
# Anticipo della fase 11: REMOTIX diventa un servizio di SISTEMA.
#
# ⛔ PERCHE' NON BASTA SPOSTARLO DI SLICE, e non e' un'opinione: l'unita'
#    `gnome-session-shutdown.target` lo dice da se', in un commento —
#
#       «Allow exit.target to start even if this unit is started with
#        replace-irreversibly.»
#
#    L'uscita di GNOME finisce con `exit.target` sul GESTORE UTENTE, che ferma
#    `user@1000.service` per intero.  Sotto quel ramo non sopravvive niente:
#    provato in `session-N.scope`, in `app.slice` e in `background.slice`, e in
#    tutti e tre REMOTIX riceve SIGTERM 250 ms dopo l'annuncio dell'uscita.
#
#    L'unico posto fuori tiro e' `system.slice`.
set -eu

sudo tee /etc/systemd/system/remotix.service >/dev/null <<'UNITA'
[Unit]
Description=REMOTIX — server RDP per Linux
After=network.target systemd-logind.service

[Service]
Type=simple
User=nicfio
# Le opzioni si mettono qui, cosi' il banco puo' accendere --senza-autenticazione
# senza toccare l'unita'.
EnvironmentFile=-/etc/default/remotix
# I due indirizzi che REMOTIX non puo' indovinare: dove vive il runtime
# dell'utente e su quale bus parlare.  Esistono sempre perche' l'utente ha il
# linger acceso — senza, sparirebbero appena si chiude l'ultima sessione.
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
ExecStart=/home/nicfio/remotix --porta 3389 $REMOTIX_OPZIONI
Restart=on-failure
RestartSec=2
# ⛔ LA PRIORITA' DI TEMPO REALE PER L'AUDIO, e non e' un lusso.
#
# Il servizio gira come utente, e un processo con RLIMIT_RTPRIO a zero — il
# valore predefinito — NON PUO' chiedere SCHED_FIFO: PipeWire ci prova, gli
# viene negato, e il suo «data-loop» resta a priorita' normale.  Li' dentro
# gira la raccolta dei campioni dal monitor del sink, che deve rispettare un
# quanto di pochi millisecondi mentre nello stesso processo il codificatore
# video si prende un core per decine.
#
# Misurato il 5 agosto 2026 con lo schermo sotto carico: senza il limite la
# cattura perdeva campioni e deformava l'onda (picco 3299 invece di 3000); con
# il limite l'onda torna esatta e quel che il client suona coincide con quel
# che consegniamo, campione per campione.  REFERENCE.md R26.
#
# Venti e' una priorita' modesta: sotto quella dei thread audio del kernel,
# sopra qualunque cosa faccia il codificatore.
LimitRTPRIO=20
LimitNICE=-11
# system.slice, cioe' FUORI dall'albero dell'utente: e' tutto il punto.
Slice=system.slice
StandardOutput=append:/home/nicfio/remotix.log
StandardError=append:/home/nicfio/remotix.log

[Install]
WantedBy=multi-user.target
UNITA

# Il linger tiene in piedi /run/user/1000 e il bus di sessione anche quando
# l'utente non ha alcuna sessione aperta: senza, REMOTIX non avrebbe con chi
# parlare fra un collegamento e l'altro.
sudo loginctl enable-linger nicfio
sudo systemctl daemon-reload
sudo systemctl enable remotix.service >/dev/null 2>&1
echo "unita' installata"
