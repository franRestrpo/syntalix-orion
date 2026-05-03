"""
Motor de Ejecución Real de Ansible para Syntalix-Orion.

Este módulo implementa el corredor (runner) oficial que utiliza la librería 
'ansible-runner' de Python para ejecutar playbooks de forma programática.

Características:
    - Ejecución asíncrona de playbooks maestros (site.yml, deploy.yml).
    - Gestión de directorios de datos privados para Ansible.
    - Captura y retransmisión de eventos del ciclo de vida de Ansible.
    - Mecanismo de fallback seguro en caso de que las dependencias de Ansible 
      no estén presentes en el entorno.
"""

import asyncio
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import re

# Configurar logger local para el archivo de salida
runner_logger = logging.getLogger("ansible_runner")
runner_logger.setLevel(logging.DEBUG)
log_file = Path(__file__).parent.parent / "logs" / "ansible_runner.log"
log_file.parent.mkdir(exist_ok=True)
fh = logging.FileHandler(log_file)
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
runner_logger.addHandler(fh)

EventCallback = Callable[[Dict[str, Any]], None]

class RealAnsibleRunner:
    def __init__(self, on_event: Optional[EventCallback] = None, debug: bool = False) -> None:
        self._on_event = on_event or (lambda e: None)
        self._debug = bool(debug)

    def _clean_ansi(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    async def run(self, config: Dict[str, Any], modules: list[str], debug: bool | None = None) -> None:
        if debug is not None:
            self._debug = bool(debug)

        # Encontrar la raíz del proyecto para asegurar que encuentre site.yml
        engine_dir = Path(__file__).parent.absolute()
        project_root = engine_dir.parent
        private_data_dir = str(project_root)

        pb = project_root / "site.yml"
        if not pb.exists():
            pb = project_root / "playbook.yml"
        
        if not pb.exists():
            self._emit({"type": "log", "level": "warning", "message": "No playbook found (site.yml / playbook.yml)."})
            self._emit({"type": "done", "success": False})
            return

        inventory = project_root / "inventory.ini"
        if not inventory.exists():
            inventory = project_root / "hosts" # fallback
            
        # Generar un archivo temporal seguro para inyectar las variables a Ansible
        import json
        import tempfile
        
        vars_file = Path(private_data_dir) / ".ansible_vars.json"
        try:
            with open(vars_file, "w") as f:
                json.dump(config, f)
            os.chmod(vars_file, 0o600)
        except Exception as e:
            self._emit({"type": "log", "level": "warning", "message": f"No se pudo crear .ansible_vars.json: {e}"})
        
        # Resolver la ruta correcta de ansible-playbook desde el entorno virtual activo
        python_bin_dir = Path(sys.executable).parent
        ansible_bin = str(python_bin_dir / "ansible-playbook")
        
        # Fallback a PATH global si no se encuentra en el venv (poco probable pero seguro)
        if not os.path.exists(ansible_bin):
            runner_logger.warning(f"ansible-playbook no encontrado en {python_bin_dir}. Usando PATH global.")
            ansible_bin = "ansible-playbook"
            
        cmd = [
            ansible_bin,
            str(pb),
            "-i", str(inventory)
        ]
        
        if vars_file.exists():
            cmd.extend(["-e", f"@{vars_file}"])
        
        msg_cmd = f"Ejecutando: {' '.join(cmd)}"
        self._emit({"type": "log", "level": "info", "message": msg_cmd})
        runner_logger.info(msg_cmd)
        
        try:
            # Call subprocess inside a separate thread to not block the asyncio event loop
            def run_subprocess():
                env = os.environ.copy()
                env["ANSIBLE_STDOUT_CALLBACK"] = "default"
                env["ANSIBLE_CALLBACK_RESULT_FORMAT"] = "yaml"
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=private_data_dir,
                    env=env
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        clean_line = self._clean_ansi(line.rstrip())
                        self._emit({"type": "log", "level": "info", "message": clean_line})
                        runner_logger.info(f"ANSIBLE: {clean_line}")
                
                return process.wait()

            returncode = await asyncio.to_thread(run_subprocess)
            success = (returncode == 0)
            runner_logger.info(f"Ansible finalizado con código: {returncode}")
            self._emit({"type": "done", "success": success})
            
        except FileNotFoundError as e:
            err_msg = f"ansible-playbook no encontrado: {e}"
            runner_logger.error(err_msg)
            self._emit({"type": "log", "level": "error", "message": err_msg})
            self._emit({"type": "done", "success": False})
        except Exception as e:
            err_msg = f"Error ejecutando Ansible: {e}"
            runner_logger.error(err_msg, exc_info=True)
            self._emit({"type": "log", "level": "error", "message": err_msg, "stderr": str(e)})
            self._emit({"type": "done", "success": False})
        finally:
            if vars_file.exists():
                try:
                    vars_file.unlink()
                except Exception:
                    pass

    def _emit(self, event: Dict[str, Any]) -> None:
        try:
            self._on_event(event)
        except Exception:
            pass
