#!/bin/bash

# Configuración de Colores
VERDE="\e[32m"
AZUL="\e[34m"
ROJO="\e[91m"
AMARILLO="\e[93m"
RESET="\e[0m"

log() { echo -e "${AZUL}[SETUP]${RESET} $1" | tee -a setup.log; }
success() { echo -e "${VERDE}[OK]${RESET} $1" | tee -a setup.log; }
warn() { echo -e "${AMARILLO}[WARN]${RESET} $1" | tee -a setup.log; }
error() { echo -e "${ROJO}[ERROR]${RESET} $1" | tee -a setup.log; exit 1; }

# Inicializar log
echo "=== Inicio de Instalación Syntalix-Orion $(date) ===" > setup.log

# 1. Validación de Root
if [ "$EUID" -ne 0 ]; then
  error "Este script debe ejecutarse como root (sudo -i)"
fi

log "Iniciando preparación del entorno Syntalix-Orion V2..."

# 2. Instalación de dependencias del SISTEMA
SYS_DEPS="python3 python3-venv python3-pip git sshpass curl docker.io"

log "Actualizando repositorios..."
apt-get update -qq > /dev/null

log "Instalando dependencias base y Docker..."
apt-get install -y $SYS_DEPS > /dev/null 2>&1 || error "Fallo al instalar dependencias ($SYS_DEPS). Revisa los logs del sistema."

log "Iniciando y habilitando servicio Docker..."
systemctl enable --now docker > /dev/null 2>&1 || warn "No se pudo habilitar Docker (¿Estás en un entorno sin systemd?)"
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

# Instalar Colecciones de Ansible requeridas
log "Instalando colecciones de Ansible Galaxy..."
$VENV_DIR/bin/ansible-galaxy collection install -r requirements.yml > /dev/null
success "Colecciones de Ansible instaladas."

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

# Si se pasa el flag --deploy y ya existe ansible_vars.yml, despliega directo
if [[ "$1" == "--deploy" || "$1" == "-d" ]]; then
    if [ -f "ansible_vars.yml" ]; then
        log "Modo desatendido: Ejecutando Ansible Playbook directamente..."
        $VENV_DIR/bin/ansible-playbook -i inventory.ini site.yml -e @ansible_vars.yml
        if [ $? -eq 0 ]; then
            success "Despliegue finalizado correctamente."
            exit 0
        else
            error "Error durante el despliegue con Ansible."
        fi
    else
        error "No se encontró ansible_vars.yml. Ejecuta primero sin --deploy para generarlo en la TUI."
    fi
fi

$VENV_DIR/bin/python main.py local

if [ $? -eq 0 ]; then
    echo "=============================================="
    success "Syntalix-Orion finalizado correctamente."
else
    error "Error durante la ejecución."
fi