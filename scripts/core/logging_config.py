"""
Módulo de Configuración de Logging Estructurado para Syntalix-Orion.

Este módulo implementa una infraestructura de registro de eventos robusta y 
altamente configurable, diseñada para facilitar la depuración y auditoría 
del sistema.

Características principales:
    - Salida dual: Registro simultáneo en consola y archivos locales.
    - Rotación de archivos: Gestión automática de espacio en disco (10MB por archivo).
    - Formateo Inteligente: Soporte para colores en terminal y formato JSON estructurado.
    - Contexto Dinámico: Capacidad de inyectar metadatos adicionales en tiempo de ejecución.
"""

import os
import sys
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


# Constantes de directorios (Resolviendo la raíz del proyecto)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "orion.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """
    Formateador para la Generación de Registros en Formato Estructurado (JSON).
    
    Optimizado para la ingesta de datos por parte de sistemas de agregación de logs 
    (ej: Grafana Loki, ELK Stack). Garantiza que cada entrada sea un objeto 
    JSON válido con metadatos técnicos completos.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Añadir información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Añadir campos extra
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, default=str)


class StructuredFormatter(logging.Formatter):
    """
    Formateador de Alta Legibilidad para Terminales Interactivas.
    
    Proporciona una salida visualmente organizada con soporte para códigos de 
    colores ANSI, facilitando la identificación inmediata de niveles críticos 
    durante la operación manual del sistema.
    """
    
    # Paleta de colores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[92m',       # Verde
        'WARNING': '\033[93m',    # Amarillo
        'ERROR': '\033[91m',      # Rojo
        'CRITICAL': '\033[1;91m', # Rojo Negrita
        'RESET': '\033[0m',
    }
    
    def __init__(self, use_colors: bool = True, include_extra: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        # Componente de tiempo
        timestamp = self.formatTime(record, "%H:%M:%S")
        
        # Componente de nivel con color
        level = record.levelname
        if self.use_colors and level in self.COLORS:
            level_str = f"{self.COLORS[level]}{level:8}{self.COLORS['RESET']}"
        else:
            level_str = f"{level:8}"
        
        # Componente de logger
        logger_name = record.name.split('.')[-1]  # Solo el nombre corto
        if len(logger_name) > 15:
            logger_name = logger_name[:12] + "..."
        
        # Mensaje base
        msg = record.getMessage()
        
        # Construir mensaje
        parts = [f"[{timestamp}] {level_str} [{logger_name:15}] {msg}"]
        
        # Añadir campos extra si existen
        if self.include_extra and hasattr(record, 'extra_data'):
            extra_parts = []
            for key, value in record.extra_data.items():
                extra_parts.append(f"{key}={value}")
            if extra_parts:
                parts.append("  └ " + " | ".join(extra_parts))
        
        # Añadir info de excepción
        if record.exc_info:
            parts.append(f"    Exception: {self.formatException(record.exc_info)}")
        
        return "\n".join(parts)


class OrionLogger:
    """
    Factoría de Gestión de Registros (Logging Engine).
    
    Implementa un modelo de configuración centralizada que orquestra múltiples 
    manejadores (handlers) de salida. Garantiza la persistencia de eventos en 
    disco y su visualización en tiempo real.
    """
    
    _instances: Dict[str, logging.Logger] = {}
    _initialized = False
    _config: Dict[str, Any] = {}
    
    @classmethod
    def configure(
        cls,
        log_level: str = "INFO",
        log_dir: Optional[Path] = None,
        max_size: int = MAX_LOG_SIZE,
        backup_count: int = BACKUP_COUNT,
        json_format: bool = False,
        use_colors: bool = True,
    ) -> None:
        """
        Establece la configuración global para el subsistema de logging.
        
        Args:
            log_level (str): Nivel de severidad mínimo para capturar.
            log_dir (Path, optional): Directorio raíz para archivos físicos.
            max_size (int): Límite de bytes antes de realizar rotación de archivo.
            backup_count (int): Cantidad de archivos históricos a conservar.
            json_format (bool): Habilita la salida estructurada para ingesta de datos.
            use_colors (bool): Activa la paleta ANSI en la salida de consola.
        """
        cls._config = {
            "log_level": getattr(logging, log_level.upper(), logging.INFO),
            "log_dir": log_dir or LOG_DIR,
            "max_size": max_size,
            "backup_count": backup_count,
            "json_format": json_format,
            "use_colors": use_colors,
        }
        
        # Crear directorio de logs si no existe
        if cls._config["log_dir"]:
            try:
                cls._config["log_dir"].mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        
        cls._initialized = True
        
        # Configurar el logger raíz (root logger) para actuar como concentrador central
        root_logger = logging.getLogger()
        root_logger.setLevel(cls._config["log_level"])
        
        # Limpiar handlers previos para evitar duplicidad de registros
        root_logger.handlers = []
        
        # 1. Manejador de Consola (Tiempo Real)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter(use_colors=cls._config["use_colors"]))
        root_logger.addHandler(console_handler)
        
        # 2. Manejador de Archivo (Persistencia)
        if cls._config["log_dir"]:
            log_file_path = cls._config["log_dir"] / "orion.log"
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=log_file_path,
                    maxBytes=cls._config["max_size"],
                    backupCount=cls._config["backup_count"],
                    encoding='utf-8'
                )
                
                if cls._config["json_format"]:
                    file_handler.setFormatter(JSONFormatter())
                else:
                    file_handler.setFormatter(StructuredFormatter(use_colors=False))
                    
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"WARNING: No se pudo configurar la persistencia de logs en ({log_file_path}): {e}", file=sys.stderr)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Recupera una instancia de logger configurada por nombre.
        
        Args:
            name (str): Nombre único del logger (generalmente __name__).
            
        Returns:
            logging.Logger: Instancia lista para emitir registros.
        """
        if not cls._initialized:
            try:
                cls.configure()
            except Exception as e:
                import sys
                print(f"WARNING: Error en la inicialización tardía del logger: {e}", file=sys.stderr)
                
        return logging.getLogger(name)

    @classmethod
    def add_file_handler(
        cls,
        logger: logging.Logger,
        filename: str,
        level: int = logging.DEBUG,
    ) -> logging.FileHandler:
        """
        Vincula un manejador de archivo adicional a un logger existente.
        
        Args:
            logger (logging.Logger): Instancia a la que se le añade la persistencia.
            filename (str): Nombre del archivo de log secundario.
            level (int): Nivel de filtrado para este manejador específico.
            
        Returns:
            logging.FileHandler: El manejador creado y vinculado.
        """
        handler = logging.FileHandler(
            cls._config.get("log_dir", LOG_DIR) / filename,
            encoding='utf-8',
        )
        handler.setLevel(level)
        
        if cls._config.get("json_format", False):
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(StructuredFormatter(use_colors=False))
        
        logger.addHandler(handler)
        return handler


def get_logger(name: str) -> logging.Logger:
    """
    Función helper para obtener un logger configurado.
    
    Uso:
        from core.logging_config import get_logger
        logger = get_logger(__name__)
    """
    return OrionLogger.get_logger(name)


def get_log_dir() -> Path:
    """Retorna el directorio de logs."""
    if OrionLogger._initialized:
        return OrionLogger._config.get("log_dir", LOG_DIR)
    return LOG_DIR


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
) -> None:
    """
    Función de utilidad para la inicialización rápida del sistema de logging.
    
    Debe llamarse al inicio de la ejecución del programa para garantizar que 
    todos los componentes utilicen la configuración de registro correcta.

    Args:
        log_level (str): Nivel de detalle deseado (DEBUG, INFO, WARNING, ERROR).
        log_dir (Optional[Path]): Carpeta donde se almacenarán los archivos físicos 
            de log. Si no se especifica, usa el directorio por defecto del proyecto.
    """
    OrionLogger.configure(
        log_level=log_level,
        log_dir=log_dir,
    )


class LogContext:
    """
    Context manager para añadir datos extra a los logs.
    
    Uso:
        logger = get_logger(__name__)
        with LogContext(logger, user="admin", action="deploy"):
            logger.info("Deploy initiated")  # Logs incluirán user=admin, action=deploy
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        **extra_data: Any,
    ):
        self.logger = logger
        self.extra_data = extra_data
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_data = self.extra_data
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, *args):
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


__all__ = [
    "OrionLogger",
    "get_logger",
    "setup_logging",
    "get_log_dir",
    "LogContext",
    "JSONFormatter",
    "StructuredFormatter",
]
