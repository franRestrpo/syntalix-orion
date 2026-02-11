#!/bin/bash
# Syntalix-Orion - Script de Desinstalación Completa
set -e

# Configuración de Colores
ROJO="\e[91m"
VERDE="\e[32m"
AZUL="\e[34m"
AMARILLO="\e[33m"
RESET="\e[0m"

log() { echo -e "${AZUL}[UNINSTALL]${RESET} $1"; }
warn() { echo -e "${AMARILLO}[WARN]${RESET} $1"; }
success() { echo -e "${VERDE}[OK]${RESET} $1"; }
error() { echo -e "${ROJO}[ERROR]${RESET} $1"; exit 1; }

# Confirmación inicial
echo -e "${ROJO}⚠️ ADVERTENCIA: Esto eliminará todos los servicios y stacks desplegados en Docker Swarm.${RESET}"
read -p "¿Estás seguro de que deseas continuar? (s/N): " confirm
if [[ ! $confirm =~ ^[sS]$ ]]; then
    log "Desinstalación cancelada."
    exit 0
fi

# 1. Obtener lista de stacks activos
log "Buscando stacks activos..."
STACKS=$(docker stack ls --format "{{.Name}}")

if [ -z "$STACKS" ]; then
    warn "No se encontraron stacks activos para eliminar."
else
    for stack in $STACKS; do
        log "Eliminando stack: $stack..."
        docker stack rm "$stack"
    done
    success "Todos los stacks han sido solicitados para eliminación."
fi

# 2. Limpieza de volúmenes (Opcional)
read -p "¿Deseas eliminar también los VOLÚMENES de datos? (¡Esto es IRREVERSIBLE!) (y/N): " del_volumes
if [[ $del_volumes =~ ^[yY]$ ]]; then
    log "Eliminando volúmenes no utilizados..."
    docker volume prune -f
    success "Volúmenes eliminados."
fi

# 3. Limpieza de archivos de despliegue
read -p "¿Deseas eliminar los archivos de configuración en el directorio 'deploy/'? (y/N): " del_configs
if [[ $del_configs =~ ^[yY]$ ]]; then
    log "Limpiando directorio deploy/..."
    if [ -d "deploy" ]; then
        rm -rf deploy/*
        success "Archivos de configuración eliminados."
    else
        warn "El directorio deploy/ no existe."
    fi
fi

# 4. Limpieza de redes (Opcional)
read -p "¿Deseas eliminar la red SyntalixNet? (y/N): " del_net
if [[ $del_net =~ ^[yY]$ ]]; then
    log "Eliminando red SyntalixNet..."
    docker network rm SyntalixNet || warn "No se pudo eliminar la red (puede que aún existan servicios cerrándose)."
fi

success "Proceso de desinstalación finalizado."
echo -e "${AMARILLO}Nota: Algunos recursos de Docker Swarm pueden tardar unos segundos en liberarse completamente.${RESET}"
