import os, sys
from constants import MIN_RAM_GB, MIN_CPU_CORES, MIN_DISK_GB

def _ram_gb():
    with open("/proc/meminfo") as f:
        return int(f.readline().split()[1]) // 1024 // 1024

def _cpu():
    return os.cpu_count()

def _disk_gb():
    stat = os.statvfs("/")
    return (stat.f_frsize * stat.f_blocks) // 1024 // 1024 // 1024

def validate():
    if _ram_gb() < MIN_RAM_GB:
        sys.exit("ERROR: RAM insuficiente")

    if _cpu() < MIN_CPU_CORES:
        sys.exit("ERROR: CPU insuficiente")

    if _disk_gb() < MIN_DISK_GB:
        sys.exit("ERROR: Disco insuficiente")
