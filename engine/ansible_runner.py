"""
Puente de Simulación de Ansible (Mock Runner) para Syntalix-Orion.

Este módulo proporciona una implementación simulada del corredor de Ansible 
diseñada para facilitar el desarrollo de la interfaz de usuario y las pruebas 
de integración sin necesidad de ejecutar comandos reales de infraestructura.

Funcionalidades:
    - Generación de eventos de log y progreso simulados.
    - Emulación de latencia de red y tiempos de procesamiento mediante asyncio.
    - Simulación aleatoria de fallos para probar la robustez de la UI.
    - Factoría dinámica para alternar entre el corredor real y el simulado.
"""

import asyncio
import random
import os
from typing import Any, Callable, Dict, Optional

# Definición de tipo para los callbacks de eventos
EventCallback = Callable[[Dict[str, Any]], None]


class AnsibleRunner:
    """
    Simulador de ejecución de Ansible orientado a eventos.
    
    Emite una secuencia de eventos estructurados que imitan el comportamiento 
    de un despliegue real, permitiendo validar la lógica de visualización 
    del Monitor de Despliegue.
    """

    def __init__(self, on_event: Optional[EventCallback] = None, debug: bool = False) -> None:
        """
        Inicializa una instancia del corredor simulado.

        Args:
            on_event (Optional[EventCallback]): Función de retorno para procesar 
                cada evento simulado.
            debug (bool): Si es True, genera eventos de depuración adicionales.
        """
        self._on_event = on_event or (lambda e: None)
        self._debug = bool(debug)

    async def run(self, config: Dict[str, Any], modules: list[str], debug: bool | None = None) -> None:
        """
        Inicia una secuencia de despliegue simulada de forma asíncrona.

        Args:
            config (Dict[str, Any]): Configuración de variables (simulada).
            modules (list[str]): Lista de módulos a 'instalar' (simulada).
            debug (bool): Sobrescribe la configuración de depuración.
        """
        if debug is not None:
            self._debug = bool(debug)

        total_steps = 4
        steps = [
            "Inventory & Preparation",
            "Connection Checks",
            "Running Playbooks",
            "Post-Deployment Validation",
        ]

        self._emit({"type": "log", "level": "info", "message": "Deployment started"})
        if self._debug:
            self._emit({"type": "log", "level": "debug", "message": "Debug mode enabled"})
            self._emit({"type": "log", "level": "debug", "message": f"Config: {config}"})
            self._emit({"type": "log", "level": "debug", "message": f"Modules: {modules}"})

        for i, step in enumerate(steps, start=1):
            await asyncio.sleep(1.0)
            if random.random() < 0.1:
                self._emit({"type": "log", "level": "error", "message": f"Error during: {step}", "stderr": "Traceback (simulado): ..."})
                self._emit({"type": "done", "success": False})
                return

            self._emit({"type": "log", "level": "info", "message": f"{step} completed"})
            if self._debug:
                self._emit({"type": "log", "level": "debug", "message": f"Step {i}/{total_steps} finished"})
            self._emit({"type": "progress", "value": int((i / total_steps) * 100)})

        self._emit({"type": "log", "level": "info", "message": "Deployment completed successfully"})
        self._emit({"type": "done", "success": True})

    def _emit(self, event: Dict[str, Any]) -> None:
        try:
            self._on_event(event)
        except Exception:
            # Never crash the UI; log silently
            pass


def get_runner(on_event: Optional[EventCallback] = None, debug: bool = False):
    """
    Factoría para obtener el corredor de Ansible adecuado según el entorno.
    
    Lee la variable de entorno 'RUNNER_MODE'. Si es 'real', intenta 
    instanciar el RealAnsibleRunner; de lo contrario, o si falla la carga, 
    retorna el simulador (AnsibleRunner).

    Args:
        on_event (Optional[EventCallback]): Función de retorno para eventos.
        debug (bool): Si es True, habilita modo depuración en el corredor.

    Returns:
        Union[RealAnsibleRunner, AnsibleRunner]: Instancia del corredor seleccionado.
    """
    mode = os.environ.get("RUNNER_MODE", "mock").lower()
    if mode == "real":
        try:
            from .ansible_runner_real import RealAnsibleRunner  # type: ignore
            return RealAnsibleRunner(on_event=on_event, debug=debug)
        except Exception:
            # Fallback to mock if real runner module is not available
            return AnsibleRunner(on_event=on_event, debug=debug)
    else:
        return AnsibleRunner(on_event=on_event, debug=debug)
