grep -oE '\bei_[a-z0-9_]+ *\(' /usr/include/libei-1.0/libei.h | tr -d ' (' | sort -u | tr '\n' ' '
echo
echo "=== EVENT TYPES ==="
sed -n '/enum ei_event_type/,/};/p' /usr/include/libei-1.0/libei.h
echo "=== DEVICE CAPS ==="
sed -n '/enum ei_device_capability/,/};/p' /usr/include/libei-1.0/libei.h
