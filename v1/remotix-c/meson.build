project('remotix', 'c',
  version: '0.1.0',
  meson_version: '>= 1.1',
  default_options: [
    'c_std=gnu11',
    'warning_level=2',
    'buildtype=debugoptimized',
  ],
)

cc = meson.get_compiler('c')

# Avvisi in piu' rispetto a warning_level=2.  Non sono pignoleria: in un server
# che parla un protocollo binario, una conversione implicita fra interi di
# larghezza diversa e' esattamente il genere di difetto che si manifesta come
# «un client su tre non disegna» invece che come errore.
avvisi = [
  '-Wshadow',
  '-Wpointer-arith',
  '-Wstrict-prototypes',
  '-Wmissing-prototypes',
  '-Wformat=2',
  '-Wno-unused-parameter',
]
add_project_arguments(cc.get_supported_arguments(avvisi), language: 'c')

# ---------------------------------------------------------------------------
# Dipendenze
#
# Sono dichiarate tutte da subito, anche quelle che lo scheletro non usa
# ancora: un pacchetto di sviluppo mancante deve farsi vedere adesso, non fra
# tre fasi quando serve davvero.
# ---------------------------------------------------------------------------
freerdp        = dependency('freerdp3',        version: '>= 3.0')
freerdp_server = dependency('freerdp-server3', version: '>= 3.0')
winpr          = dependency('winpr3',          version: '>= 3.0')
glib           = dependency('glib-2.0',        version: '>= 2.74')
gio            = dependency('gio-2.0',         version: '>= 2.74')
pipewire       = dependency('libpipewire-0.3', version: '>= 1.0')

# libei: il trasporto dell'input verso il compositore, deciso il 4 agosto 2026
# (§5.8 di SPECIFICA.md).  xkbcommon serve a leggere la disposizione di
# tastiera che libei consegna: e' cio' che permette di tradurre gli eventi
# Unicode, che su Android sono la strada principale.
libei          = dependency('libei-1.0',       version: '>= 1.0')

# wayland-client: su KDE la cattura NON passa da D-Bus.  KWin non ha alcun
# servizio D-Bus di screencast — cercato in tutto l'albero della 6.3.6, non c'e'
# (`kde.md` §16) — e il protocollo `zkde_screencast_unstable_v1` vive dove
# vivono i protocolli Wayland.  Il codice del protocollo lo genera
# `wayland-scanner` dall'XML in `src/protocolli/`, che e' la copia della v5:
# quella che KWin 6.3.6 annuncia davvero, non quella che il pacchetto dichiara.
wayland        = dependency('wayland-client',  version: '>= 1.20')
wayland_scanner = find_program('wayland-scanner')

# libavcodec: il codificatore H.264, scelto PER NOME a runtime (fase 9, §3.1 di
# SPECIFICA.md).  REMOTIX non parla ne' a VA-API ne' a NVENC: parla a
# libavcodec, e il costruttore e' una stringa — `h264_vaapi`, `h264_qsv`,
# `h264_nvenc`, `libx264`.  libswscale fa la sola conversione BGRx → NV12, che
# e' l'ultimo pezzo rimasto in CPU sul percorso accelerato.
# libdrm: serve solo per `drm_fourcc.h`, cioe' per i nomi dei formati e dei
# modificatori con cui si chiede a Mutter un DMA-BUF invece di un buffer in
# memoria ordinaria (fase 9).  Non si chiama una sua funzione.
libdrm         = dependency('libdrm',          version: '>= 2.4')
# libva: la copia di REGIONE fra superfici della scheda.  Serve alla correzione
# del 7 agosto 2026 (R29): il DMA-BUF che Mutter presta non e' un fotogramma
# intero ma un «diff» — solo le regioni danneggiate sono fresche — e le regioni
# vanno deposte su una superficie di accumulo.  libavfilter non sa farlo: i suoi
# filtri lavorano sul fotogramma intero.
libva          = dependency('libva',           version: '>= 1.16')
libavcodec     = dependency('libavcodec',      version: '>= 60')
libavutil      = dependency('libavutil',       version: '>= 58')
libswscale     = dependency('libswscale',      version: '>= 7')
# libavfilter: serve a UNA cosa sola, e importante — deporre il fotogramma
# catturato dentro la superficie allineata che R4 pretende, sulla scheda.  La
# conversione della scheda sa cambiare formato, non sa riempire un bordo.
libavfilter    = dependency('libavfilter',     version: '>= 10')

# gdk-pixbuf: serve agli APPUNTI, non alla grafica.  I client RDP chiedono le
# immagini in CF_DIB e basta — il client di FreeRDP mappa perfino image/png su
# CF_DIB (`xf_cliprdr.c`) — mentre le applicazioni di GNOME copiano in PNG.
# Senza un convertitore, «copia immagine» funzionerebbe solo fra programmi che
# gia' parlano BMP, cioe' quasi nessuno.
gdkpixbuf      = dependency('gdk-pixbuf-2.0',  version: '>= 2.40')
xkbcommon      = dependency('xkbcommon',       version: '>= 1.0')
systemd        = dependency('libsystemd')

# PAM non ha un file pkg-config su Debian: si cerca la libreria e si verifica
# che l'intestazione ci sia, altrimenti l'errore arriverebbe al collegamento.
# libm: serve a `lround` nella conversione della rotella.  Su glibc recenti le
# funzioni matematiche stanno ancora in una libreria a parte, e il collegatore
# non la aggiunge da se': l'errore che si ottiene — «DSO missing from command
# line» — non nomina ne' la funzione ne' il file.
libm = cc.find_library('m', required: false)

pam = cc.find_library('pam', required: true)
if not cc.has_header('security/pam_appl.h')
  error('manca security/pam_appl.h: installare libpam0g-dev')
endif

dipendenze = [
  freerdp, freerdp_server, winpr,
  glib, gio,
  pipewire, systemd, pam,
  libei, wayland, xkbcommon, gdkpixbuf, libm,
  libavcodec, libavutil, libswscale, libavfilter, libdrm, libva,
]

subdir('src')

summary({
  'FreeRDP':  freerdp.version(),
  'GLib':     glib.version(),
  'PipeWire': pipewire.version(),
  'libavcodec': libavcodec.version(),
  'libei':    libei.version(),
}, section: 'Dipendenze')
