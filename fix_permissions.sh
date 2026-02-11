#!/bin/bash
# Script para corregir permisos del entorno virtual si fue creado por root

VENV_DIR=".venv"

# Detectar el usuario real si se ejecuta con sudo
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_GROUP=$(id -gn "$SUDO_USER")
else
    REAL_USER=$(whoami)
    REAL_GROUP=$(id -gn)
fi

echo "Corrigiendo permisos en $VENV_DIR para el usuario $REAL_USER..."

if [ -d "$VENV_DIR" ]; then
    # Cambiar el propietario al usuario real
    chown -R "$REAL_USER:$REAL_GROUP" "$VENV_DIR"
    
    if [ $? -eq 0 ]; then
        echo "Permisos corregidos exitosamente."
        # Asegurar permisos de escritura
        chmod -R u+w "$VENV_DIR"
    else
        echo "Error al cambiar permisos. Asegúrate de ejecutar este script con sudo."
        exit 1
    fi
else
    echo "El directorio $VENV_DIR no existe."
fi