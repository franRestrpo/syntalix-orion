#!/bin/bash

set -e

VERDE="\e[32m"
AZUL="\e[34m"
ROJO="\e[91m"
AMARILLO="\e[93m"
RESET="\e[0m"

log() { echo -e "${AZUL}[SETUP]${RESET} $1" | tee -a setup.log; }
success() { echo -e "${VERDE}[OK]${RESET} $1" | tee -a setup.log; }
warn() { echo -e "${AMARILLO}[WARN]${RESET} $1" | tee -a setup.log; }
error() { echo -e "${ROJO}[ERROR]${RESET} $1" | tee -a setup.log; exit 1; }

echo "=== Syntalix-Orion V2 Setup $(date) ===" > setup.log

if [ "$EUID" -ne 0 ]; then
  error "Este script debe ejecutarse como root (sudo -i)"
fi

log "Iniciando preparación del entorno Syntalix-Orion V2..."

SYS_DEPS="python3 python3-venv python3-pip git sshpass curl"

export DEBIAN_FRONTEND=noninteractive

log "Actualizando repositorios..."
apt-get update -qq >> setup.log 2>&1

log "Instalando dependencias base (Python, Git, etc.)..."
apt-get install -y $SYS_DEPS >> setup.log 2>&1 || error "Fallo al instalar dependencias ($SYS_DEPS). Revisa setup.log."

if ! command -v docker &> /dev/null; then
    log "Docker no encontrado. Instalando motor Docker oficial..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh >> setup.log 2>&1 || error "Fallo al instalar Docker. Revisa setup.log."
    rm -f get-docker.sh
else
    log "Docker ya está instalado."
fi

log "Iniciando y habilitando servicio Docker..."
systemctl enable --now docker >> setup.log 2>&1 || warn "No se pudo habilitar Docker (¿Estás en un entorno sin systemd?)"
success "Sistema y Docker configurados."

VENV_DIR="$(pwd)/.venv"

if [ ! -d "$VENV_DIR" ]; then
    log "Creando entorno virtual de Python..."
    python3 -m venv "$VENV_DIR" || error "No se pudo crear el virtualenv"
else
    log "Entorno virtual ya existe."
fi

PIP_CMD="$VENV_DIR/bin/pip"

log "Instalando dependencias Python..."
$PIP_CMD install --upgrade pip > /dev/null

if ! command -v uv &> /dev/null; then
    log "Instalando uv (gestor de paquetes moderno)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh >> setup.log 2>&1
    UV_CMD="$HOME/.cargo/bin/uv"
else
    UV_CMD="uv"
fi

log "Instalando Syntalix-Orion como paquete editable..."
cd "$(dirname "$0")"
$VENV_DIR/bin/python -m pip install -e . >> setup.log 2>&1 || error "Fallo al instalar el paquete. Revisa setup.log."

success "Entorno Python configurado."

log "Instalando colecciones de Ansible Galaxy..."
$VENV_DIR/bin/ansible-galaxy collection install -r requirements.yml > /dev/null 2>&1 || warn "Fallo al instalar colecciones de Ansible."
success "Colecciones de Ansible instaladas."

log "Ejecutando validaciones pre-vuelo..."

PYTHON_VERSION=$($VENV_DIR/bin/python --version 2>&1)
log "Python: $PYTHON_VERSION"

log "Verificando instalación del paquete..."
if $VENV_DIR/bin/python -c "import syntalix_orion" 2>/dev/null; then
    success "Paquete syntalix_orion instalado correctamente."
else
    error "El paquete no se instaló correctamente."
fi

success "Validaciones completadas."

log "Iniciando Syntalix-Orion V2..."
echo "=============================================="

RUNNER_MODE=${RUNNER_MODE:-real}
export RUNNER_MODE

if [[ "$1" == "--deploy" || "$1" == "-d" ]]; then
    if [ -f "secrets/.env" ]; then
        log "Modo desatendido: Ejecutando Ansible Playbook directamente..."
        $VENV_DIR/bin/ansible-playbook -i inventory.ini site.yml -e @secrets/.env
        if [ $? -eq 0 ]; then
            success "Despliegue finalizado correctamente."
            exit 0
        else
            error "Error durante el despliegue con Ansible."
        fi
    else
        error "No se encontró secrets/.env. Ejecuta primero sin --deploy para configurarlo en la TUI."
    fi
fi

$VENV_DIR/bin/orion

if [ $? -eq 0 ]; then
    echo "=============================================="
    success "Syntalix-Orion finalizado correctamente."
else
    error "Error durante la ejecución."
fi