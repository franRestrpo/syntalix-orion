"""
Repositorio de Estado (StateRepository) - Syntalix-Orion.

Implementa el patrón de repositorio para centralizar la persistencia de estado.
Utiliza el patrón de escritura atómica (Write-and-Rename) para garantizar que
los archivos de configuración nunca queden corruptos.

Características:
    - Escritura atómica con archivos temporales + os.replace()
    - Protocolo Write-and-Verify para contraseñas Category C
    - Backups automáticos antes de sobreescribir
    - Transaccionalidad: si falla .env, no se modifica state.json
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from syntalix_orion.core.logging_config import get_logger
from syntalix_orion.core.security import validate_password_strength, _is_user_facing_password

logger = get_logger(__name__)


class StatePersistenceError(Exception):
    """Error crítico cuando la persistencia de estado falla."""
    pass


class StateRepository:
    """
    Repositorio unificado para persistencia de estado.

    Maneja tanto el estado de selección (state.json) como los secretos
    (secrets/.env) de forma atómica y segura.

    Uso:
        >>> repo = StateRepository()
        >>> repo.save_secrets({"TRAEFIK__PASSWORD": "secret123"})
        >>> state = repo.load_selection()
    """

    def __init__(
        self,
        state_file: str = "state.json",
        secrets_dir: str = "secrets",
        secrets_file: str = ".env"
    ):
        """
        Inicializa el repositorio.

        Args:
            state_file: Nombre del archivo de estado JSON.
            secrets_dir: Directorio de secretos.
            secrets_file: Nombre del archivo de variables de entorno.
        """
        self._state_file = Path(state_file)
        self._secrets_dir = Path(secrets_dir)
        self._secrets_file = self._secrets_dir / secrets_file
        self._backup_dir = self._secrets_dir / "backups"

    @property
    def secrets_env_path(self) -> Path:
        """Ruta completa al archivo de secretos."""
        return self._secrets_file

    @property
    def state_file_path(self) -> Path:
        """Ruta completa al archivo de estado."""
        return self._state_file

    def _ensure_dirs(self) -> None:
        """Asegura que los directorios necesarios existan."""
        self._secrets_dir.mkdir(parents=True, exist_ok=True)
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Crea un backup del archivo antes de sobreescribirlo.

        Args:
            file_path: Ruta del archivo a respaldar.

        Returns:
            Path del backup creado o None si no se pudo crear.
        """
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path = self._backup_dir / backup_name

        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup creado: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"No se pudo crear backup: {e}")
            return None

    def save_secrets_atomic(
        self,
        env_vars: Dict[str, str],
        skip_verify: bool = False
    ) -> bool:
        """
        Guarda secretos usando el patrón Write-and-Rename (atómico).

        Args:
            env_vars: Diccionario de variables a persistir.
            skip_verify: Si True, omite la verificación post-escritura.

        Returns:
            True si la escritura fue exitosa.

        Raises:
            StatePersistenceError: Si la verificación falla.
        """
        self._ensure_dirs()

        processed_vars: Dict[str, str] = {}

        for key, value in env_vars.items():
            if value in (None, "None", "null", ""):
                continue

            # Convert value to string to handle cases where it might be a list (like ansible_enabled_roles)
            if isinstance(value, list):
                # Representing python lists as JSON strings for .env files is usually safest
                value_str = json.dumps(value)
            else:
                value_str = str(value)
                
            sanitized = value_str.strip()

            if _is_user_facing_password(key):
                is_valid, error_msg = validate_password_strength(sanitized)
                if not is_valid:
                    raise StatePersistenceError(
                        f"Contraseña inválida para {key}: {error_msg}"
                    )
                logger.info(f"Category C password validado para {key}")

            processed_vars[key] = sanitized

        tmp_file = self._secrets_file.with_suffix('.env.tmp')

        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                for key, value in processed_vars.items():
                    f.write(f"{key}={value}\n")

            try:
                os.chmod(tmp_file, 0o600)
            except Exception as e:
                logger.warning(f"No se pudieron establecer permisos 600 en {tmp_file}: {e}")

            os.replace(tmp_file, self._secrets_file)
            logger.info(f"Secretos guardados atómicamente en {self._secrets_file}")

            if not skip_verify:
                verified_vars = self.load_secrets()
                for key, value in processed_vars.items():
                    disk_value = verified_vars.get(key)
                    # Si era una lista que convertimos a JSON string para guardar, la recarga (load_secrets) 
                    # podr haberla reconvertido en lista. Comparamos los strings o ignoramos si coinciden conceptualmente.
                    if disk_value != value:
                        if isinstance(disk_value, list):
                            try:
                                import json
                                if json.loads(value) == disk_value:
                                    continue
                            except:
                                pass
                        raise StatePersistenceError(
                            f"Verificacin fallida para {key}: "
                            f"memoria='{value}' disco='{disk_value}'"
                        )

            return True

        except StatePersistenceError:
            raise
        except Exception as e:
            logger.error(f"Error al guardar secretos: {e}")
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            raise StatePersistenceError(f"Error al guardar secretos: {e}")

    def load_secrets(self) -> Dict[str, str]:
        """
        Carga los secretos desde el archivo .env.

        Returns:
            Diccionario de variables de entorno cargadas.
        """
        env_vars: Dict[str, Any] = {}

        if not self._secrets_file.exists():
            return env_vars

        try:
            with open(self._secrets_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if value in ("None", "null", ""):
                            continue
                        
                        # Try to parse JSON strings back to python lists
                        if value.startswith('[') and value.endswith(']'):
                            try:
                                import json
                                value = json.loads(value)
                            except:
                                pass
                                
                        env_vars[key] = value
        except Exception as e:
            logger.error(f"Error al leer secretos: {e}")

        return env_vars

    def save_selection(
        self,
        selected_apps: list,
        auto_dependencies: Optional[list] = None,
        user_variables: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Guarda el estado de selección de aplicaciones.

        Args:
            selected_apps: Lista de IDs de apps seleccionadas.
            auto_dependencies: Lista de IDs de dependencias automáticas.
            user_variables: Variables ingresadas por el usuario.

        Returns:
            True si el guardado fue exitoso.
        """
        self._create_backup(self._state_file)

        state_data = {
            "selected_apps": list(selected_apps),
            "auto_dependencies": list(auto_dependencies) if auto_dependencies else [],
            "user_variables": user_variables if user_variables else {},
            "saved_at": datetime.now().isoformat()
        }

        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, default=str)
            logger.info(f"Estado guardado en {self._state_file}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar estado: {e}")
            return False

    def load_selection(self) -> Dict[str, Any]:
        """
        Carga el estado de selección desde el archivo.

        Returns:
            Diccionario con el estado de selección.
        """
        if not self._state_file.exists():
            return {
                "selected_apps": [],
                "auto_dependencies": [],
                "user_variables": {}
            }

        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar estado: {e}")
            return {
                "selected_apps": [],
                "auto_dependencies": [],
                "user_variables": {}
            }

    def save_full_state(
        self,
        selected_apps: list,
        env_vars: Dict[str, str],
        auto_dependencies: Optional[list] = None
    ) -> bool:
        """
        Guarda estado completo de forma atómica.

        Primero guarda los secretos, si falla hace rollback.
        Solo guarda state.json si secretos se persistieron correctamente.

        Args:
            selected_apps: Lista de apps seleccionadas.
            env_vars: Variables de entorno a guardar.
            auto_dependencies: Lista de dependencias automáticas.

        Returns:
            True si todo se guardó correctamente.

        Raises:
            StatePersistenceError: Si falla la escritura de secretos.
        """
        self.save_secrets_atomic(env_vars)

        if not self.save_selection(selected_apps, auto_dependencies, env_vars):
            raise StatePersistenceError("Fallo al guardar estado de selección")

        return True

    def clear_state(self) -> bool:
        """
        Limpia todo el estado persistido.

        Returns:
            True si la limpieza fue exitosa.
        """
        try:
            if self._state_file.exists():
                self._create_backup(self._state_file)
                self._state_file.unlink()
            if self._secrets_file.exists():
                self._create_backup(self._secrets_file)
                self._secrets_file.unlink()
            logger.info("Estado limpiado exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error al limpiar estado: {e}")
            return False


def get_repository() -> StateRepository:
    """Obtiene una instancia del repositorio de estado."""
    return StateRepository()