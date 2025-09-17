#!/bin/sh
# Ejemplo: inspecciona tus Arduinos y crea una regla udev (editar SERIAL)
echo "Lista de /dev/serial/by-id/:"
ls -l /dev/serial/by-id/
cat > /etc/udev/rules.d/99-arduinos.rules <<'EOF'
# Reemplaza ATTRS{serial} por el serial real que veas en /dev/serial/by-id/
SUBSYSTEM=="tty", ATTRS{serial}=="SERIAL_ARDUINO_SENSORES", SYMLINK+="arduino_sensores"
SUBSYSTEM=="tty", ATTRS{serial}=="SERIAL_ARDUINO_MOTORES",  SYMLINK+="arduino_motores"
EOF
echo "Reglas creadas en /etc/udev/rules.d/99-arduinos.rules (edita los seriales manualmente)."
