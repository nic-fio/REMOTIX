grep -nE "GetVirtualKeyCodeFromVirtualScanCode|GetKeycodeFromVirtualKeyCode|WINPR_KEYCODE_TYPE|KBDEXT" /usr/include/winpr3/winpr/input.h | head -20
echo "=== FLAGS RDP ==="
grep -nE "define (KBD_FLAGS|PTR_FLAGS|PTR_XFLAGS|KBD_SYNC)_[A-Z0-9_]+" /usr/include/freerdp3/freerdp/input.h | head -40
echo "=== rdpInput callbacks ==="
grep -nE "pKeyboardEvent|pUnicodeKeyboardEvent|pMouseEvent|pExtendedMouseEvent|pSynchronizeEvent|pRelMouseEvent" /usr/include/freerdp3/freerdp/input.h | head -20
