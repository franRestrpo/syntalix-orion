"""
Módulo de Gestión de Plantillas para Syntalix-Orion.

Este módulo utiliza el motor de plantillas Jinja2 para facilitar la generación 
dinámica de archivos de configuración, manifiestos de Docker Stack y variables 
de orquestación.

Permite transformar metadatos y variables generadas en archivos físicos 
listos para ser procesados por Ansible o Docker.
"""

import os
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any

class TemplateManager:
    """
    Controlador central para el procesamiento de plantillas Jinja2.
    
    Encapsula la lógica de renderizado y proporciona métodos auxiliares para 
    estandarizar componentes comunes de infraestructura, como la configuración 
    de etiquetas para el proxy inverso Traefik.
    """

    def __init__(self):
        """Inicializa el entorno de renderizado con auto-escape de seguridad."""
        self.env = Environment(autoescape=True)

    def render_template(self, template_path: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Procesa una plantilla Jinja2 y guarda el resultado en un archivo físico.

        Args:
            template_path (str): Ruta completa al archivo de plantilla (.j2).
            context (Dict[str, Any]): Diccionario de datos para inyectar en la plantilla.
            output_path (str): Ruta de destino para el archivo generado.

        Raises:
            Exception: Si ocurre un error durante el renderizado o la escritura del archivo.
        """
        try:
            # Nota: El código original tenía una variable 'template' no definida
            # Corrigiendo para usar la ruta proporcionada
            with open(template_path, 'r', encoding='utf-8') as f:
                template = self.env.from_string(f.read())
                
            rendered_content = template.render(**context)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
                
            print(f"Plantilla renderizada exitosamente en {output_path}")
            
        except Exception as e:
            print(f"Error renderizando plantilla {template_path}: {str(e)}")
            raise

    def inject_traefik_labels(self, service_name: str, domain: str, port: int, enable_https: bool = True) -> list:
        """
        Genera una lista estandarizada de etiquetas Docker para el proxy Traefik.
        
        Facilita la exposición de servicios web con soporte automático para 
        TLS y resolución de certificados vía Let's Encrypt.

        Args:
            service_name (str): Nombre del servicio para los identificadores de routers.
            domain (str): Dominio DNS asignado al servicio.
            port (int): Puerto interno del contenedor donde escucha la aplicación.
            enable_https (bool): Si es True, configura TLS y el certresolver.

        Returns:
            list: Lista de cadenas de texto con el formato 'traefik.label=value'.
        """
        labels = [
            "traefik.enable=true",
            f"traefik.http.routers.{service_name}.rule=Host(`{domain}`)",
            f"traefik.http.services.{service_name}.loadbalancer.server.port={port}",
            f"traefik.http.routers.{service_name}.entrypoints=websecure",
        ]
        
        if enable_https:
            labels.append(f"traefik.http.routers.{service_name}.tls.certresolver=letsencryptresolver")
            labels.append(f"traefik.http.routers.{service_name}.tls=true")
            
        return labels
