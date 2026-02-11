import subprocess, sys
from constants import DEFAULT_NETWORK
from utils import cmd_exists

def require(cmd: str):
    if not cmd_exists(cmd):
        sys.exit(f"ERROR: {cmd} no instalado")

def swarm_active():
    state = subprocess.getoutput(
        "docker info --format '{{.Swarm.LocalNodeState}}'"
    )
    if state != "active":
        sys.exit("ERROR: Docker Swarm no activo (Ansible debe inicializarlo)")

def network_exists(name=DEFAULT_NETWORK):
    out = subprocess.getoutput(
        f"docker network ls --format '{{{{.Name}}}}' | grep -w {name}"
    )
    if not out:
        print(f"Red '{name}' no encontrada. Creando...")
        subprocess.run(
            ["docker", "network", "create", "--driver=overlay", name],
            check=True
        )
