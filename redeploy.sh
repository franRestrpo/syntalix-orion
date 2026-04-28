#!/bin/bash
# Syntalix-Orion - Script de Redespliegue
set -e

# Colores
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
    log "Entorno no encontrado. Ejecutando setup.sh..."
    sudo ./setup.sh
    exit 0
fi

log "Iniciando Syntalix-Orion V2..."

# Modo por defecto: local (Docker)
export RUNNER_MODE=${RUNNER_MODE:-real}
$PYTHON_CMD main.py local

if [ $? -eq 0 ]; then
    success "Despliegue completado."
else
    error "Error durante la ejecución."
fi
