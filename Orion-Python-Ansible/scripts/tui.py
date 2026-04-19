#!/usr/bin/env python3
"""
Syntalix-Orion V2 - Terminal User Interface (TUI)

Interfaz gráfica de terminal interactiva para la gestión de despliegue
de aplicaciones en Docker Swarm mediante Ansible.

Arquitectura:
- Backend: DependencyGraph + Pydantic models (ya implementado)
- Frontend: Textual TUI (este archivo)

Uso:
    cd scripts
    python tui.py

Dependencias:
    pip install textual

Autor: Syntalix-Orion Team
Versión: 2.0.0
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

# =============================================================================
# CONFIGURACIÓN DE RUTAS
# =============================================================================

# Agregar directorio raíz al path para imports
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# IMPORTS - MÓDULOS DEL PROYECTO
# =============================================================================

# Imports de apps_metadata (ubicado en la raíz del proyecto)
try:
    from apps_metadata import APP_METADATA
except ImportError:
    # Fallback para cuando se ejecuta desde otro directorio
    apps_metadata_path = PROJECT_ROOT / "apps_metadata.py"
    if apps_metadata_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("apps_metadata", str(apps_metadata_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        APP_METADATA = module.APP_METADATA
    else:
        raise ImportError("No se encontró apps_metadata.py")

# Imports de core (ubicado en scripts/core/)
from core.dependency_graph import DependencyGraph
from core.models import load_app_catalog, AppMetadata
from core.security import mask_secret
from core.logging_config import get_logger, setup_logging

# =============================================================================
# IMPORTS - TEXTUAL
# =============================================================================

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Static,
    Checkbox,
    Button,
)


# =============================================================================
# CONSTANTES Y CONFIGURACIÓN
# =============================================================================

# Orden de categorías para mostrar en el panel izquierdo
# NOTA: "Data" no se muestra - las apps de datos se despliegan como dependencias
CATEGORY_ORDER: List[str] = [
    "Core",
    "AI",
    "Automation",
    "Communication",
    "Management",
]

# Categorías que se auto-seleccionan y deshabilitan
CORE_CATEGORIES: Set[str] = {"Core"}

# Umbral de RAM para warnings visuales
RAM_WARNING_THRESHOLD: int = 6000  # MB


# =============================================================================
# ESTILOS CSS INTEGRADOS
# =============================================================================

CSS = """
/* Layout principal */
Screen {
    background: $surface;
}

#main-container {
    height: 100%;
    layout: horizontal;
}

/* Panel izquierdo: catálogo de apps */
#left-panel {
    width: 45%;
    height: 100%;
    border-right: solid $primary;
    padding: 1 2;
}

#left-panel Checkbox {
    margin: 0;
}

#left-panel .category-header {
    text-style: bold;
    color: $accent;
    margin-top: 1;
    margin-bottom: 0;
    padding: 0 1;
}

#left-panel .app-item {
    padding: 0 2;
    margin: 0;
}

/* Panel derecho: monitor de estado */
#right-panel {
    width: 55%;
    height: 100%;
    padding: 1 2;
}

#status-display {
    height: 60%;
    padding: 1;
    border: solid $primary;
    margin-bottom: 1;
}

#action-container {
    height: auto;
    align: center bottom;
    padding: 1;
}

/* Widgets de información */
.info-label {
    color: $text-muted;
}

.status-header {
    text-style: bold;
    color: $accent;
}

.ram-ok {
    color: $success;
    text-style: bold;
}

.ram-warning {
    color: $error;
    text-style: bold;
}

.deploy-order {
    color: $text;
}

.disabled-checkbox {
    opacity: 0.6;
}

/* Botón de acción */
#deploy-button {
    width: 100%;
}
"""


# =============================================================================
# MODELO DE DATOS PARA LA UI
# =============================================================================

@dataclass
class CategoryGroup:
    """Grupo de aplicaciones por categoría."""
    name: str
    apps: List[AppMetadata]
    is_mandatory: bool  # True para categorías Core (auto-seleccionadas)


@dataclass
class DeploymentResult:
    """Resultado del cálculo de despliegue."""
    selected_apps: List[str]
    plan: List[str]
    ram_total_mb: int
    vars_generated: Dict[str, str]
    has_warning: bool
    warning_message: Optional[str] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    @property
    def ram_status_class(self) -> str:
        """Retorna la clase CSS según estado de RAM."""
        return "ram-ok" if self.ram_total_mb < RAM_WARNING_THRESHOLD else "ram-warning"

    @property
    def ram_status_icon(self) -> str:
        """Retorna icono según estado de RAM."""
        return "[OK]" if self.ram_total_mb < RAM_WARNING_THRESHOLD else "[WARN]"

    def to_markdown(self) -> str:
        """
        Genera representación Markdown del resultado.
        """
        lines = []

        # Encabezado
        lines.append("## [OK] Plan de Despliegue")
        lines.append("")

        # Resumen
        lines.append("### Resumen")
        lines.append(f"- **Apps seleccionadas:** {len(self.selected_apps)}")
        lines.append(f"- **Roles total a instalar:** {len(self.plan)}")
        lines.append(f"- **RAM estimada:** {self.ram_status_icon} {self.ram_total_mb} MB")
        lines.append("")

        # Advertencia de RAM si aplica
        if self.has_warning:
            lines.append(f"[WARN] **{self.warning_message}**")
            lines.append("")

        # Orden de despliegue
        lines.append("### [REV] Orden de Despliegue")
        lines.append("")

        for i, app_id in enumerate(self.plan, 1):
            meta = self._get_app_metadata(app_id)
            name = meta.name if meta else app_id
            is_dep = app_id in self.dependencies
            badge = "[DEP]" if is_dep else "[SEL]"
            lines.append(f"{i}. {badge} **{name}**")

        lines.append("")
        lines.append("---")
        lines.append("*Usa Ctrl+D para desplegar*")

        return "\n".join(lines)

    def _get_app_metadata(self, app_id: str) -> Optional[AppMetadata]:
        """Obtiene metadatos de una app por ID."""
        # Esta método será configurado después
        return None


# =============================================================================
# APLICACIÓN PRINCIPAL
# =============================================================================

class OrionTUI(App):
    """
    Aplicación TUI para Syntalix-Orion V2.

    Proporciona una interfaz visual interactiva para:
    - Seleccionar aplicaciones a desplegar
    - Visualizar grafo de dependencias en tiempo real
    - Iniciar el despliegue con seguridad

    Herencia: textual.app.App

    Atributos de clase:
        BINDINGS: Bindings de teclado globales
        CSS: Estilos integrados de la aplicación

    Ejemplo:
        >>> app = OrionTUI()
        >>> app.run()
    """

    # Bindings de teclado
    BINDINGS = [
        Binding("ctrl+d", "deploy", "Desplegar", show=True),
        Binding("ctrl+q", "quit", "Salir", show=True),
        Binding("ctrl+r", "refresh", "Recalcular", show=True),
    ]

    # Estilos CSS
    CSS = CSS

    # Título de la aplicación
    TITLE = "[RUN] Syntalix-Orion V2"
    SUB_TITLE = "Gestor de Despliegue de Infraestructura"

    def __init__(self) -> None:
        """
        Inicializa la aplicación TUI.

        Carga y valida el catálogo de aplicaciones usando Pydantic,
        inicializa el DependencyGraph, y prepara el estado de la UI.
        """
        super().__init__()

        # =============================================================
        # CARGA SEGURA DE DATOS - SIN DICCIONARIOS CRUDOS
        # =============================================================

        logger.info("Inicializando TUI - Cargando catalogo de aplicaciones")

        # Cargar y validar catálogo usando Pydantic
        # Esto garantiza que todos los datos cumplen el esquema definido
        self.catalog: Dict[str, AppMetadata] = load_app_catalog(APP_METADATA)
        logger.info(
            f"Catalogo cargado: {len(self.catalog)} aplicaciones",
            extra={"app_count": len(self.catalog)}
        )

        # Inicializar DependencyGraph
        # Crear un diccionario simple para el grafo
        catalog_dict = {}
        for app_id, app in self.catalog.items():
            catalog_dict[app_id] = app.model_dump()

        self.dependency_graph = DependencyGraph(catalog=catalog_dict)

        # Estado de la aplicación
        self.selected_apps: Set[str] = set()
        self.category_groups: List[CategoryGroup] = []
        self.deployment_result: Optional[DeploymentResult] = None
        self.is_deploying: bool = False

        # Preparar grupos por categoría
        self._prepare_category_groups()

        logger.info("TUI inicializada correctamente")

    def _prepare_category_groups(self) -> None:
        """
        Prepara los grupos de aplicaciones organizados por categoría.

        El orden de visualización sigue CATEGORY_ORDER, y las categorías
        Core se auto-seleccionan.
        """
        # Agrupar apps por categoría
        category_apps: Dict[str, List[AppMetadata]] = {}
        for app_id, app in self.catalog.items():
            if app.category not in category_apps:
                category_apps[app.category] = []
            category_apps[app.category].append(app)

        # Crear grupos en el orden definido
        self.category_groups = []
        for category in CATEGORY_ORDER:
            if category in category_apps:
                is_mandatory = category in CORE_CATEGORIES
                group = CategoryGroup(
                    name=category,
                    apps=sorted(category_apps[category], key=lambda a: a.name),
                    is_mandatory=is_mandatory
                )
                self.category_groups.append(group)

                # Auto-seleccionar apps de categorías Core
                if is_mandatory:
                    for app in group.apps:
                        self.selected_apps.add(app.id)

        logger.debug(f"Grupos de categoria preparados: {len(self.category_groups)}")

    def _get_initial_status_message(self) -> str:
        """Genera el mensaje de estado inicial."""
        return """## [INIT] Estado Inicial

Selecciona las aplicaciones que deseas desplegar
usando los checkboxes del panel izquierdo.

**Apps Core** estan pre-seleccionadas (obligatorias).

---

[INFO] **Atajos de teclado:**
- `Ctrl+R`: Recalcular plan
- `Ctrl+D`: Desplegar
- `Ctrl+Q`: Salir

---
*El plan se actualizara automaticamente al seleccionar apps*
"""

    def compose(self) -> ComposeResult:
        """
        Compone los widgets de la interfaz.

        Estructura:
        - Header: Titulo de la aplicacion
        - Contenedor horizontal principal
          - Panel izquierdo (45%): Catalogo de checkboxes
          - Panel derecho (55%): Monitor de estado y boton
        - Footer: Bindings y ayuda
        """
        # Cabecera
        yield Header()

        # Contenedor principal con paneles
        with Horizontal(id="main-container"):
            # Panel izquierdo: Catalogo de aplicaciones
            with VerticalScroll(id="left-panel"):
                yield Static("[PKG] **Catalogo de Aplicaciones**", id="catalog-title")
                yield Static("", id="catalog-subtitle")

                # Generar checkboxes por categoria
                for group in self.category_groups:
                    # Encabezado de categoria
                    icon = "[Wrench]" if group.is_mandatory else "[BOX]"
                    yield Static(
                        f"\n{icon} **{group.name}**",
                        classes="category-header"
                    )

                    # Checkboxes de aplicaciones
                    for app in group.apps:
                        checkbox = Checkbox(
                            f"{app.name} (v{app.version}) - {app.ram_mb}MB",
                            value=app.id in self.selected_apps,
                            disabled=group.is_mandatory,
                            id=f"checkbox-{app.id}"
                        )
                        # Tooltip con descripcion
                        checkbox.tooltip = f"ID: {app.id}\nRAM: {app.ram_mb}MB"
                        yield checkbox

            # Panel derecho: Monitor de estado
            with Vertical(id="right-panel"):
                yield Static("## [STAT] Monitor de Despliegue", id="monitor-title")
                yield Static("", id="monitor-spacer")

                # Widget de estado (Markdown)
                with VerticalScroll(id="status-display"):
                    yield Static(
                        self._get_initial_status_message(),
                        id="status-content",
                        markup=True
                    )

                # Contenedor de accion
                with Vertical(id="action-container"):
                    yield Static("---")
                    yield Button(
                        "[RUN] Generar vars.yml e Instalar",
                        id="deploy-button",
                        variant="primary"
                    )

        # Pie de pagina
        yield Footer()

    def on_mount(self) -> None:
        """
        Manejador del evento de montaje.

        Se ejecuta cuando la aplicacion esta lista para renderizar.
        """
        logger.info("Aplicacion montada, actualizando estado inicial")
        self._update_deployment_result()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """
        Manejador del evento de cambio de checkbox.

        Actualiza el estado de seleccion y recalcula el grafo de dependencias.

        Args:
            event: Evento de cambio de checkbox
        """
        # Extraer el ID de la app desde el ID del widget
        checkbox_id = event.checkbox.id
        if not checkbox_id or not checkbox_id.startswith("checkbox-"):
            return

        app_id = checkbox_id.replace("checkbox-", "")

        # Actualizar seleccion
        if event.checkbox.value:
            self.selected_apps.add(app_id)
            logger.debug(f"App seleccionada: {app_id}")
        else:
            # No permitir deseleccionar apps Core
            if event.checkbox.disabled:
                event.checkbox.value = True  # Forzar seleccion
                logger.debug(f"App Core no puede deseleccionarse: {app_id}")
            else:
                self.selected_apps.discard(app_id)
                logger.debug(f"App deseleccionada: {app_id}")

        # Recalcular grafo
        self._update_deployment_result()

    def _update_deployment_result(self) -> None:
        """
        Recalcula el grafo de dependencias y actualiza el panel de estado.

        Este metodo:
        1. Llama a dependency_graph.plan_with_vars_multi()
        2. Genera el resultado en formato Markdown
        3. Actualiza el widget de estado
        """
        if not self.selected_apps:
            status_text = self._get_initial_status_message()
            self.deployment_result = None
        else:
            # Calcular plan usando el DependencyGraph
            selected_list = list(self.selected_apps)
            logger.info(
                "Calculando plan de despliegue",
                extra={"apps": selected_list, "count": len(selected_list)}
            )

            try:
                # Obtener resultado del grafo
                result = self.dependency_graph.plan_with_vars_multi(selected_list)

                # Crear DeploymentResult
                ram_total = result.get("ram_mb_total", 0)
                plan = result.get("plan", [])
                vars_gen = result.get("vars", {})
                dependencies = result.get("dependencies", [])

                # Verificar umbral de RAM
                has_warning = ram_total > RAM_WARNING_THRESHOLD
                warning_msg = None
                if has_warning:
                    warning_msg = (
                        f"La RAM total ({ram_total}MB) excede el umbral "
                        f"recomendado de {RAM_WARNING_THRESHOLD}MB"
                    )
                    logger.warning("Umbral de RAM excedido", extra={
                        "ram_mb": ram_total,
                        "threshold": RAM_WARNING_THRESHOLD
                    })

                # Crear resultado
                self.deployment_result = DeploymentResult(
                    selected_apps=selected_list,
                    plan=plan,
                    ram_total_mb=ram_total,
                    vars_generated=vars_gen,
                    has_warning=has_warning,
                    warning_message=warning_msg,
                    dependencies=dependencies
                )

                status_text = self.deployment_result.to_markdown()

            except Exception as e:
                logger.error(f"Error calculando plan: {e}")
                status_text = f"""## [ERROR] Error

No se pudo calcular el plan de despliegue:

```
{str(e)}
```

Por favor, revisa las dependencias seleccionadas."""

        # Actualizar widget de estado
        try:
            status_widget = self.query_one("#status-content", Static)
            status_widget.update(status_text)
        except Exception:
            logger.error("No se encontro el widget de estado")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Manejador del evento de presion de boton.

        Inicia el proceso de despliegue con logging seguro.

        Args:
            event: Evento de boton presionado
        """
        button_id = event.button.id

        if button_id == "deploy-button":
            self._start_deployment()

    def _start_deployment(self) -> None:
        """
        Inicia el proceso de despliegue.

        Esta fase:
        1. Verifica que haya apps seleccionadas
        2. Muestra mensaje de inicio en el panel
        3. Simula el logging seguro de contrasenas generadas
        4. (Futuro) Ejecutara el playbook de Ansible
        """
        if self.is_deploying:
            logger.warning("Despliegue ya en progreso")
            return

        if not self.deployment_result or not self.selected_apps:
            self._show_error("No hay aplicaciones seleccionadas para desplegar")
            return

        self.is_deploying = True
        logger.info(
            "INICIANDO DESPLIEGUE",
            extra={
                "apps": list(self.selected_apps),
                "plan_size": len(self.deployment_result.plan),
                "ram_total": self.deployment_result.ram_total_mb
            }
        )

        # Mensaje de inicio
        status_widget = self.query_one("#status-content", Static)
        status_widget.update("""## [HOURGLASS] Despliegue en Progreso

Espera mientras se procesa el despliegue...

[INFO] Verificando configuracion...
[INFO] Validando dependencias...
[INFO] Generando variables de entorno...

""")

        # Simular procesamiento y mostrar logging seguro
        self._process_with_secure_logging()

    def _process_with_secure_logging(self) -> None:
        """
        Procesa el despliegue con logging seguro.

        Demuestra el uso de mask_secret() para proteger
        contrasenas sensibles en los logs.
        """
        if not self.deployment_result:
            return

        vars_gen = self.deployment_result.vars_generated

        # Filtrar solo variables secretas para demo
        secrets = {k: v for k, v in vars_gen.items() if "PASSWORD" in k or "SECRET" in k or "KEY" in k}

        # Generar lineas de log seguro
        log_lines = ["## [LOCK] Variables Generadas (Seguras)", "", "```",]

        if secrets:
            log_lines.append("[INFO] Generando contrasenas seguras...")
            for key, value in list(secrets.items())[:5]:  # Solo mostrar 5
                masked = mask_secret(value, visible_chars=4)
                log_lines.append(f"[SECURE] {key} = {masked}")
            log_lines.append(f"[INFO] Total secretos generados: {len(secrets)}")
        else:
            log_lines.append("[INFO] No se requieren secretos adicionales")

        log_lines.append("```")
        log_lines.append("")
        log_lines.append("---")
        log_lines.append("")
        log_lines.append("**OK** **Generacion completada**")
        log_lines.append("")
        log_lines.append("En un entorno de produccion, esto:")
        log_lines.append("1. Generaria `vars.yml` con Ansible Vault")
        log_lines.append("2. Ejecutaria `ansible-playbook site.yml`")
        log_lines.append("3. Monitorearia el estado de los servicios")
        log_lines.append("")
        log_lines.append("*Simulacion: presiona Ctrl+Q para salir*")

        # Actualizar widget
        status_widget = self.query_one("#status-content", Static)
        status_widget.update("\n".join(log_lines))

        # Resetear estado
        self.is_deploying = False

        logger.info("Procesamiento seguro completado")

    def _show_error(self, message: str) -> None:
        """
        Muestra un mensaje de error en el panel de estado.

        Args:
            message: Mensaje de error a mostrar
        """
        status_widget = self.query_one("#status-content", Static)
        status_widget.update(f"""## [X] Error

{message}

---""")

    def action_deploy(self) -> None:
        """
        Accion de despliegue (binding Ctrl+D).
        """
        logger.debug("Accion deploy triggered por Ctrl+D")
        self._start_deployment()

    def action_refresh(self) -> None:
        """
        Accion de refrescar/recalcular (binding Ctrl+R).
        """
        logger.debug("Accion refresh triggered por Ctrl+R")
        self._update_deployment_result()
        self.notify("Plan recalculado [OK]")

    def action_quit(self) -> None:
        """
        Accion de salir (binding Ctrl+Q).
        """
        logger.info("Usuario solicito salir de la aplicacion")
        self.exit()


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def main() -> None:
    """
    Punto de entrada principal para la TUI.

    Inicializa logging y ejecuta la aplicacion Textual.
    """
    # Configurar logging antes de iniciar
    setup_logging("INFO")

    logger.info("=" * 60)
    logger.info("Iniciando Syntalix-Orion TUI v2.0")
    logger.info("=" * 60)

    try:
        app = OrionTUI()
        app.run()
    except KeyboardInterrupt:
        logger.info("Aplicacion interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        raise
    finally:
        logger.info("Aplicacion finalizada")


if __name__ == "__main__":
    main()
