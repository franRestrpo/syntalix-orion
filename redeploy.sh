#!/bin/bash
# Syntalix-Orion - Script de Redespliegue unificado con Ansible
set -e

# Configuración de Colores
VERDE="\e[32m"
AZUL="\e[34m"
RESET="\e[0m"

log() { echo -e "${AZUL}[REDEPLOY]${RESET} $1"; }
success() { echo -e "${VERDE}[OK]${RESET} $1"; }

VENV_DIR="$(pwd)/.venv"
ANSIBLE_CMD="$VENV_DIR/bin/ansible-playbook"

if [ ! -f "$ANSIBLE_CMD" ]; then
    log "Entorno virtual no encontrado. Ejecutando setup.sh primero..."
    sudo ./setup.sh
    exit 0
fi

log "Iniciando redespliegue de infraestructura y aplicaciones..."

# Ejecutar el playbook centrándose en el desplegador de aplicaciones
# Se pueden usar tags si se desea filtrar, pero aquí ejecutamos todo para asegurar consistencia
$ANSIBLE_CMD -i inventory.ini playbook.yml --diff

success "¡Redespliegue completado!"
