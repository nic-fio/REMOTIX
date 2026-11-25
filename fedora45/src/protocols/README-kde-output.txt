kde-output-device-v2.xml and kde-output-management-v2.xml (KDE Plasma, KWin 6.8: output devices and output configuration)
-------------------------------------------------------------------------------------------------------------------------
Taken UNMODIFIED from plasma-wayland-protocols (https://invent.kde.org/libraries/plasma-wayland-protocols),
branch master, commit cd65734cccdf2c60b2e446b0e6416400e697755d (2026-11-19), files src/protocols/kde-output-device-v2.xml
(last changed by 344524df9ec2, 2026-09-21) and src/protocols/kde-output-management-v2.xml (last changed by 6e072eda6f69,
2026-07-06, «Allow specifying custom modes with CVT timings»).  Interface versions: kde_output_management_v2 22 (add_cvt needs
22), kde_output_device_v2 / kde_output_device_registry_v2 26.  Licence: MIT-CMU (SPDX line in each file; the text is in THIRD-PARTY-LICENSES).
The Fedora package plasma-wayland-protocols 1.23.0 does NOT ship these two files, hence the copy.
They are used by src/kwin.c (kwin_output_resize()) to change the size of KWin's output (`kwin_wayland --virtual`) at run time.
