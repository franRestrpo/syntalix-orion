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


# Constantes de directorios
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "orion.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """
    Formateador para la generación de logs en formato JSON estructurado.
    
    Ideal para su uso en entornos de producción donde los logs son consumidos 
    por sistemas externos como ELK Stack, Loki o CloudWatch.
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
    """Formateador legible con información estructurada."""
    
    # Colores para terminal
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[1;91m', # Bold Red
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
    Motor de gestión de registros (Logger) para Syntalix-Orion.
    
    Esta clase implementa el patrón factoría para proporcionar instancias de 
    logging pre-configuradas con handlers de archivo, consola y formateadores 
    según la configuración global definida.
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
        Configura el sistema de logging global.
        
        Args:
            log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directorio para archivos de log
            max_size: Tamaño máximo de cada archivo de log
            backup_count: Número de backups a mantener
            json_format: Usar formato JSON en lugar de texto legible
            use_colors: Usar colores en la salida de terminal
        """
        cls._config = {
            "log_level": getattr(logging, log_level.upper(), logging.INFO),
            "log_dir": log_dir or LOG_DIR,
            "max_size": max_size,
            "backup_count": backup_count,
            "json_format": json_format,
            "use_colors": use_colors,
        }
        
        # Crear directorio de logs si existe
        if cls._config["log_dir"]:
            try:
                cls._config["log_dir"].mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtiene un logger configurado.
        
        Args:
            name: Nombre del logger (generalmente __name__)
            
        Returns:
            Logger configurado
        """
        try:
            if not cls._initialized:
                try:
                    cls.configure()
                except Exception as e:
                    # Fallback: usar logger básico pero al menos registrar el error
                    import sys
                    print(f"WARNING: Error configurando logger: {e}", file=sys.stderr)
                    
        except Exception:
            pass
            
            if name in cls._instances:
                return cls._instances[name]
        except Exception:
            pass
        
        # Fallback: logger básico
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
            logger.addHandler(handler)
        return logger

    @classmethod
    def add_file_handler(
        cls,
        logger: logging.Logger,
        filename: str,
        level: int = logging.DEBUG,
    ) -> logging.FileHandler:
        """
        Añade un handler de archivo adicional a un logger.
        
        Args:
            logger: Logger al que añadir el handler
            filename: Nombre del archivo de log
            level: Nivel mínimo de log
            
        Returns:
            Handler añadido
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
