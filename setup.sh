#!/bin/bash

# Configuración de Colores
VERDE="\e[32m"
AZUL="\e[34m"
ROJO="\e[91m"
RESET="\e[0m"

log() { echo -e "${AZUL}[SETUP]${RESET} $1"; }
success() { echo -e "${VERDE}[OK]${RESET} $1"; }
error() { echo -e "${ROJO}[ERROR]${RESET} $1"; exit 1; }

# 1. Validación de Root
# Necesario para instalar paquetes del sistema (git, python3-venv)
if [ "$EUID" -ne 0 ]; then
  error "Este script debe ejecutarse como root (sudo -i)"
fi

log "Iniciando preparación del entorno de despliegue..."

# 2. Instalación de dependencias del SISTEMA (Prerrequisitos para Python/Ansible)
# No instalamos ansible aquí, solo lo necesario para crear el entorno.
SYS_DEPS="python3 python3-venv python3-pip git sshpass"

log "Actualizando repositorios e instalando dependencias base..."
apt-get update -qq > /dev/null
apt-get install -y $SYS_DEPS > /dev/null 2>&1 || error "Fallo al instalar dependencias del sistema ($SYS_DEPS)"
success "Dependencias del sistema instaladas."

# 3. Creación del Entorno Virtual (.venv)
VENV_DIR="$(pwd)/.venv"

if [ ! -d "$VENV_DIR" ]; then
    log "Creando entorno virtual de Python en $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || error "No se pudo crear el virtualenv"
else
    log "El entorno virtual ya existe. Usando el existente."
fi

# 4. Instalación de Herramientas dentro del VENV
# Usamos la ruta absoluta al pip del entorno virtual para no activar/desactivar
PIP_CMD="$VENV_DIR/bin/pip"

log "Instalando Ansible y librerías necesarias dentro del entorno virtual..."
# Instalamos 'ansible' (core + community), 'docker' (SDK para módulos) y 'requests'
$PIP_CMD install --upgrade pip > /dev/null
$PIP_CMD install ansible docker requests websocket-client jsondiff pyyaml

#$PIP_CMD install --force-reinstall ansible docker requests websocket-client jsondiff pyyaml

# Forzamos la reinstalación de requests y el SDK de docker para asegurar compatibilidad
log "Forzando actualización de librerías críticas..."
$PIP_CMD install --upgrade requests docker > /dev/null 2>&1

success "Entorno Python listo (Ansible + Docker SDK instalados)."

# 5. Ejecución del Playbook
PLAYBOOK="playbook.yml"
ANSIBLE_CMD="$VENV_DIR/bin/ansible-playbook"

if [ ! -f "$PLAYBOOK" ]; then
    error "No se encuentra el archivo $PLAYBOOK en este directorio."
fi

log "Lanzando orquestación con Ansible..."
echo "-----------------------------------------------------"

# Ejecutamos ansible-playbook usando el binario del entorno virtual
# Esto asegura que use las librerías que acabamos de instalar
# Se usa --diff para ver cambios en plantillas y archivos .env
$ANSIBLE_CMD -i inventory.ini "$PLAYBOOK" --diff

if [ $? -eq 0 ]; then
    echo "-----------------------------------------------------"
    success "¡Despliegue finalizado correctamente!"
    echo -e "${VERDE}Tu infraestructura está lista.${RESET}"
else
    error "Hubo un error durante la ejecución del playbook."
fi