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
    log "Forzando eliminación de configuración cacheada en volúmenes críticos (n8n, postgres)..."
    docker run --rm -v n8n_n8n_data:/home/node/.n8n alpine rm -rf /home/node/.n8n/* 2>/dev/null || true
    docker run --rm -v n8n_data:/home/node/.n8n alpine rm -rf /home/node/.n8n/* 2>/dev/null || true
    docker run --rm -v postgres_pgvector_postgres_data:/var/lib/postgresql/data alpine rm -rf /var/lib/postgresql/data/* 2>/dev/null || true
    docker run --rm -v postgres_data:/var/lib/postgresql/data alpine rm -rf /var/lib/postgresql/data/* 2>/dev/null || true

    log "Eliminando volúmenes de Docker no utilizados..."
    docker volume prune -f
    success "Volúmenes eliminados."
fi

# 3. Limpieza de archivos de despliegue y estado de la TUI
read -p "¿Deseas eliminar los archivos de configuración (deploy/), secretos y el estado de la TUI? (y/N): " del_configs
if [[ $del_configs =~ ^[yY]$ ]]; then
    log "Limpiando directorio deploy/..."
    if [ -d "deploy" ]; then
        rm -rf deploy/*
        success "Archivos de configuración (stacks) eliminados."
    else
        warn "El directorio deploy/ no existe."
    fi

    log "Limpiando estado y memoria de la TUI..."
    if [ -f "state.json" ]; then
        rm -f state.json
        success "Archivo state.json eliminado (memoria de la TUI borrada)."
    fi

    if [ -d "secrets" ]; then
        rm -rf secrets/.env
        rm -rf secrets/backups/*
        success "Archivos de secretos (.env y backups) eliminados."
    fi
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
