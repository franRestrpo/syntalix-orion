#!/bin/bash
# Syntalix-Orion - Script de Redespliegue unificado con Ansible
set -e

# Configuración de Colores
VERDE="\e[32m"
AZUL="\e[34m"
ROJO="\e[91m"
RESET="\e[0m"

log() { echo -e "${AZUL}[REDEPLOY]${RESET} $1"; }
success() { echo -e "${VERDE}[OK]${RESET} $1"; }
error() { echo -e "${ROJO}[ERROR]${RESET} $1"; exit 1; }

VENV_DIR="$(pwd)/.venv"
PYTHON_CMD="$VENV_DIR/bin/python"

if [ ! -f "$PYTHON_CMD" ]; then
    log "Entorno virtual no encontrado. Ejecutando setup.sh primero..."
    sudo ./setup.sh
    exit 0
fi

log "Iniciando redespliegue interactivo con la Interfaz de Terminal (TUI)..."

# Lanzar la TUI usando el entorno virtual con el runner en modo real
export RUNNER_MODE=real
$PYTHON_CMD main.py

if [ $? -eq 0 ]; then
    success "¡Redespliegue finalizado o TUI cerrada correctamente!"
else
    error "Hubo un error durante la ejecución."
fi
