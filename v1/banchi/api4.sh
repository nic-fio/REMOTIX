echo "=== simboli che spediscono error info ==="
nm -D --defined-only /usr/lib/x86_64-linux-gnu/libfreerdp3.so.3 2>/dev/null | grep -iE "error_info|errinfo" | head
echo "=== freerdp_peer: Close / Disconnect ==="
grep -n -B6 "Close;\|Disconnect;" /usr/include/freerdp3/freerdp/peer.h | head -40
