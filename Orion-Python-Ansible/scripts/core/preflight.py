"""
Módulo unificado de preflight checks para Syntalix-Orion.

Proporciona:
- Verificación de comandos disponibles
- Verificación de Docker y Swarm
- Validación de recursos del sistema (RAM, CPU, disco)
- Verificación de red Docker

Este módulo consolida la lógica de checks.py, resources.py y el antiguo preflight.py.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, Tuple

# Constantes de recursos mínimos
DEFAULT_NETWORK = "SyntalixNet"
MIN_RAM_GB = 2
MIN_CPU_CORES = 2
MIN_DISK_GB = 10


def get_platform() -> str:
    """Retorna el nombre de la plataforma."""
    return platform.system().lower()


def is_linux() -> bool:
    """Retorna True si es Linux."""
    return get_platform() == "linux"


def is_windows() -> bool:
    """Retorna True si es Windows."""
    return get_platform() == "windows"


def is_macos() -> bool:
    """Retorna True si es macOS."""
    return get_platform() == "darwin"


def cmd_exists(cmd: str) -> bool:
    """
    Verifica si un comando existe en el PATH.
    
    Args:
        cmd: Nombre del comando
        
    Returns:
        True si el comando existe
    """
    if is_windows():
        result = subprocess.run(
            f"where {cmd}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        result = subprocess.run(
            f"which {cmd}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    return result.returncode == 0


def require(cmd: str) -> None:
    """
    Verifica que un comando esté disponible, o termina con error.
    
    Args:
        cmd: Nombre del comando requerido
        
    Raises:
        SystemExit: Si el comando no está disponible
    """
    if not cmd_exists(cmd):
        sys.exit(f"ERROR: {cmd} no instalado o no en PATH")


def check_docker_available() -> Tuple[bool, Optional[str]]:
    """
    Verifica si Docker está disponible y en ejecución.
    
    Returns:
        Tupla (disponible, versión o mensaje de error)
    """
    if not cmd_exists("docker"):
        return False, "Docker no está instalado"
    
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        else:
            error_msg = result.stderr.strip() if result.stderr else "Error desconocido"
            return False, error_msg
    except Exception as e:
        return False, str(e)


def check_swarm_active() -> Tuple[bool, Optional[str]]:
    """
    Verifica si Docker Swarm está activo.
    
    Returns:
        Tupla (activo, estado)
    """
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Swarm.LocalNodeState}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            state = result.stdout.strip()
            return state == "active", state
        else:
            return False, "Error al verificar Swarm"
    except Exception as e:
        return False, str(e)


def check_network_exists(network_name: str) -> bool:
    """
    Verifica si existe una red Docker.
    
    Args:
        network_name: Nombre de la red
        
    Returns:
        True si la red existe
    """
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            networks = result.stdout.strip().split('\n')
            return network_name in networks
        return False
    except Exception:
        return False


def create_overlay_network(network_name: str, attachable: bool = True) -> bool:
    """
    Crea una red overlay para Docker Swarm.
    
    Args:
        network_name: Nombre de la red
        attachable: Si True, permite attaching de servicios standalone
        
    Returns:
        True si se creó exitosamente o ya existía
    """
    if check_network_exists(network_name):
        return True
    
    cmd = ["docker", "network", "create", "--driver=overlay"]
    if attachable:
        cmd.append("--attachable")
    cmd.append(network_name)
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def get_system_ram_gb() -> Optional[float]:
    """
    Obtiene la RAM total del sistema en GB.
    
    Returns:
        RAM en GB, o None si no se pudo obtener
    """
    if is_linux():
        try:
            with open("/proc/meminfo") as f:
                line = f.readline()
                kb = int(line.split()[1])
                return kb / 1024 / 1024
        except Exception:
            pass
    elif is_windows():
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.GlobalMemoryStatusEx()
            meminfo = ctypes.create_string_buffer(64)
            kernel32.GlobalMemoryStatusEx(meminfo)
            total = ctypes.c_ulonglong.from_buffer_copy(meminfo[0:8]).value
            return total / 1024 / 1024 / 1024
        except Exception:
            pass
    
    return None


def get_cpu_cores() -> int:
    """
    Obtiene el número de cores de CPU.
    
    Returns:
        Número de cores
    """
    return os.cpu_count() or 0


def get_disk_free_gb() -> Optional[float]:
    """
    Obtiene el espacio libre en disco en GB (directorio raíz).
    
    Returns:
        Espacio libre en GB, o None si no se pudo obtener
    """
    if is_linux():
        try:
            stat = os.statvfs("/")
            return (stat.f_frsize * stat.f_bavail) / 1024 / 1024 / 1024
        except Exception:
            pass
    elif is_windows():
        try:
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(os.getenv('SystemDrive', 'C:')),
                None, None, ctypes.byref(free_bytes)
            )
            return free_bytes.value / 1024 / 1024 / 1024
        except Exception:
            pass
    
    return None


def validate_resources(
    min_ram_gb: float = MIN_RAM_GB,
    min_cores: int = MIN_CPU_CORES,
    min_disk_gb: float = MIN_DISK_GB
) -> Tuple[bool, Optional[str]]:
    """
    Valida que los recursos del sistema sean suficientes.
    
    Args:
        min_ram_gb: RAM mínima requerida en GB
        min_cores: Cores mínimos requeridos
        min_disk_gb: Disco mínimo libre en GB
        
    Returns:
        Tupla (válido, mensaje de error o None)
    """
    # Validar RAM
    ram = get_system_ram_gb()
    if ram is not None and ram < min_ram_gb:
        return False, f"RAM insuficiente: {ram:.1f}GB < {min_ram_gb}GB requeridos"
    
    # Validar CPU
    cores = get_cpu_cores()
    if cores < min_cores:
        return False, f"CPU insuficiente: {cores} < {min_cores} cores requeridos"
    
    # Validar disco
    disk = get_disk_free_gb()
    if disk is not None and disk < min_disk_gb:
        return False, f"Disco insuficiente: {disk:.1f}GB < {min_disk_gb}GB requeridos"
    
    return True, None


def run_preflight_checks(
    require_swarm: bool = True,
    create_network: bool = True,
    network_name: str = DEFAULT_NETWORK,
    validate_sys: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Ejecuta todas las verificaciones preflight.
    
    Args:
        require_swarm: Verificar que Swarm esté activo
        create_network: Crear red si no existe
        network_name: Nombre de la red interna
        validate_sys: Validar recursos del sistema
        
    Returns:
        Tupla (éxito, mensaje de error o None)
    """
    # Verificar Docker
    docker_ok, docker_msg = check_docker_available()
    if not docker_ok:
        return False, f"Docker no disponible: {docker_msg}"
    
    # Verificar Swarm si se requiere
    if require_swarm:
        swarm_ok, swarm_msg = check_swarm_active()
        if not swarm_ok:
            return False, f"Docker Swarm no activo: {swarm_msg}"
    
    # Verificar/Crear red
    if not check_network_exists(network_name):
        if create_network:
            if not create_overlay_network(network_name):
                return False, f"No se pudo crear la red '{network_name}'"
        else:
            return False, f"Red '{network_name}' no existe"
    
    # Validar recursos del sistema
    if validate_sys:
        resources_ok, resources_msg = validate_resources()
        if not resources_ok:
            return False, resources_msg
    
    return True, None


__all__ = [
    "get_platform",
    "is_linux",
    "is_windows",
    "is_macos",
    "cmd_exists",
    "require",
    "check_docker_available",
    "check_swarm_active",
    "check_network_exists",
    "create_overlay_network",
    "get_system_ram_gb",
    "get_cpu_cores",
    "get_disk_free_gb",
    "validate_resources",
    "run_preflight_checks",
    "DEFAULT_NETWORK",
    "MIN_RAM_GB",
    "MIN_CPU_CORES",
    "MIN_DISK_GB",
]