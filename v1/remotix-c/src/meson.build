sorgenti = files(
  'altoparlante.c',
  'appunti.c',
  'appunti_mutter.c',
  'appunti_wlr.c',
  'autenticazione.c',
  'cattura.c',
  'codificatore.c',
  'compositore.c',
  'energia.c',
  'immagine.c',
  'input.c',
  'kwin.c',
  'main.c',
  'misura.c',
  'mutter.c',
  'palco.c',
  'registro.c',
  'rete.c',
  'sentinella.c',
  'superficie.c',
  'scambio.c',
  'server.c',
  'sessione.c',
  'suono.c',
  'tastiera.c',
  'uscita.c',
)

# Il protocollo di cattura di KWin, generato dall'XML.
#
# ⚠ L'XML e' la copia della VERSIONE 5, non l'ultima pubblicata: KWin 6.3.6
#   annuncia la 5 (`screencast_v1.cpp:18`) anche se compilato contro un
#   `plasma-wayland-protocols` che dichiara la 6.  Legare una versione che il
#   compositore non annuncia significa non legare affatto.
zkde_xml = 'protocolli/zkde-screencast-unstable-v1.xml'

zkde_intestazione = custom_target('zkde-screencast-client-header',
  input: zkde_xml,
  output: 'zkde-screencast-unstable-v1-client-protocol.h',
  command: [wayland_scanner, 'client-header', '@INPUT@', '@OUTPUT@'],
)

zkde_codice = custom_target('zkde-screencast-code',
  input: zkde_xml,
  output: 'zkde-screencast-unstable-v1-protocol.c',
  command: [wayland_scanner, 'private-code', '@INPUT@', '@OUTPUT@'],
)

# Lo stato dei tasti a scatto.  ⛔ Serve perche' su KWin libei NON lo consegna:
# `eis_device_keyboard_send_xkb_modifiers` non e' chiamato da nessuna parte
# (`kde.md` §7.2), quindi la riconciliazione scritta per GNOME li' non gira.
keystate_xml = 'protocolli/keystate.xml'

keystate_intestazione = custom_target('keystate-client-header',
  input: keystate_xml,
  output: 'keystate-client-protocol.h',
  command: [wayland_scanner, 'client-header', '@INPUT@', '@OUTPUT@'],
)

keystate_codice = custom_target('keystate-code',
  input: keystate_xml,
  output: 'keystate-protocol.c',
  command: [wayland_scanner, 'private-code', '@INPUT@', '@OUTPUT@'],
)

# Gli appunti su KWin (e domani su wlroots): `zwlr_data_control_manager_v1`.
#
# ⚠ L'XML e' la copia presa da KWin 6.3.6 — `src/wayland/protocols/` — cioe'
#   dalla versione che il compositore implementa davvero, con la stessa regola
#   dello screencast qui sopra.  Il protocollo e' di wlroots, non di KDE: e' il
#   motivo per cui l'implementazione si chiama `appunti_wlr.c` e non `_kwin`.
dctl_xml = 'protocolli/wlr-data-control-unstable-v1.xml'

dctl_intestazione = custom_target('wlr-data-control-client-header',
  input: dctl_xml,
  output: 'wlr-data-control-unstable-v1-client-protocol.h',
  command: [wayland_scanner, 'client-header', '@INPUT@', '@OUTPUT@'],
)

dctl_codice = custom_target('wlr-data-control-code',
  input: dctl_xml,
  output: 'wlr-data-control-unstable-v1-protocol.c',
  command: [wayland_scanner, 'private-code', '@INPUT@', '@OUTPUT@'],
)

executable('remotix',
  sorgenti, zkde_intestazione, zkde_codice, keystate_intestazione, keystate_codice,
  dctl_intestazione, dctl_codice,
  dependencies: dipendenze,
  c_args: ['-DPACCHETTO_VERSIONE="' + meson.project_version() + '"'],
  # Senza -rdynamic la traccia della pila stampa indirizzi nudi: i nomi delle
  # nostre funzioni non finiscono nella tabella dinamica, e un registro che
  # dice «+0x1a3f» non risponde alla domanda «da quale riga».
  export_dynamic: true,
  install: true,
)
