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
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import re

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
        
        cmd = [
            "ansible-playbook",
            str(pb),
            "-i", str(inventory)
        ]
        
        if vars_file.exists():
            cmd.extend(["-e", f"@{vars_file}"])
        
        self._emit({"type": "log", "level": "info", "message": f"Ejecutando: {' '.join(cmd)}"})
        
        try:
            # Call subprocess inside a separate thread to not block the asyncio event loop
            def run_subprocess():
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=private_data_dir
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        clean_line = self._clean_ansi(line.rstrip())
                        self._emit({"type": "log", "level": "info", "message": clean_line})
                
                return process.wait()

            returncode = await asyncio.to_thread(run_subprocess)
            success = (returncode == 0)
            self._emit({"type": "done", "success": success})
            
        except FileNotFoundError:
            self._emit({"type": "log", "level": "error", "message": "ansible-playbook no encontrado en PATH."})
            self._emit({"type": "done", "success": False})
        except Exception as e:
            self._emit({"type": "log", "level": "error", "message": f"Error ejecutando Ansible: {e}", "stderr": str(e)})
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
