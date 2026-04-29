#!/bin/bash

# Configuración de Colores
VERDE="\e[32m"
AZUL="\e[34m"
ROJO="\e[91m"
AMARILLO="\e[93m"
RESET="\e[0m"

log() { echo -e "${AZUL}[SETUP]${RESET} $1"; }
success() { echo -e "${VERDE}[OK]${RESET} $1"; }
warn() { echo -e "${AMARILLO}[WARN]${RESET} $1"; }
error() { echo -e "${ROJO}[ERROR]${RESET} $1"; exit 1; }

# 1. Validación de Root
if [ "$EUID" -ne 0 ]; then
  error "Este script debe ejecutarse como root (sudo -i)"
fi

log "Iniciando preparación del entorno Syntalix-Orion V2..."

# 2. Instalación de dependencias del SISTEMA
SYS_DEPS="python3 python3-venv python3-pip git sshpass curl"

log "Actualizando repositorios..."
apt-get update -qq > /dev/null

log "Instalando dependencias base..."
apt-get install -y $SYS_DEPS > /dev/null 2>&1 || error "Fallo al instalar dependencias ($SYS_DEPS)"
success "Dependencias del sistema instaladas."

# 3. Creación del Entorno Virtual
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

# Dependencias principales
$PIP_CMD install ansible ansible-runner pyyaml > /dev/null

# SDKs y utilities
$PIP_CMD install docker requests websocket-client jsondiff > /dev/null

# Textual UI
$PIP_CMD install textual > /dev/null

# Nuevas dependencias V2
$PIP_CMD install bcrypt pydantic jinja2 > /dev/null

success "Entorno Python configurado."

# 4. Validaciones Pre-vuelo
log "Ejecutando validaciones pre-vuelo..."

# Verificar Python
PYTHON_VERSION=$($VENV_DIR/bin/python --version 2>&1)
log "Python: $PYTHON_VERSION"

# Verificar pip
log "Verificando paquetes instalados..."
REQUIRED_PKGS="ansible textual pyyaml pydantic bcrypt jinja2"
MISSING=""

for pkg in $REQUIRED_PKGS; do
    if ! $VENV_DIR/bin/python -c "import $pkg" 2>/dev/null; then
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    warn "Paquetes faltantes:$MISSING - instalando..."
    $PIP_CMD install $MISSING > /dev/null
fi

success "Validaciones completadas."

# 5. Ejecutar Syntalix-Orion
log "Iniciando Syntalix-Orion V2..."
echo "=============================================="

# Por defecto modo local
RUNNER_MODE=${RUNNER_MODE:-real}
export RUNNER_MODE

$VENV_DIR/bin/python main.py local

if [ $? -eq 0 ]; then
    echo "=============================================="
    success "Syntalix-Orion finalizado correctamente."
else
    error "Error durante la ejecución."
fi