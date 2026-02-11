import subprocess
import os

def deploy(stack: str, compose_file: str, env_vars: dict = None):
    # Copiamos el entorno actual para no perder variables del sistema
    env = os.environ.copy()
    
    # Si se pasaron variables nuevas, las actualizamos/agregamos
    if env_vars:
        env.update(env_vars)

    subprocess.run(
        ["docker", "stack", "deploy", "--prune", "--resolve-image", "always", "-c", compose_file, stack],
        check=True,
        env=env
    )
