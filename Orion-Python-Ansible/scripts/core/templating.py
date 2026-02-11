import os
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any

class TemplateManager:
    def __init__(self):
        self.env = Environment(autoescape=True)

    def render_template(self, template_path: str, context: Dict[str, Any], output_path: str) -> None:
        """
        Renderiza una plantilla Jinja2 con el contexto dado y guarda el resultado.
        
        Args:
            template_path: Ruta al archivo de plantilla (ej: stack.yml.j2)
            context: Diccionario con las variables para reemplazar en la plantilla
            output_path: Ruta donde guardar el archivo generado
        """
        try:
            # Configurar el loader para el directorio de la plantilla específica
            template_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)
            
            env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
            template = env.get_template(template_file)
            
            rendered_content = template.render(**context)
            
            with open(output_path, 'w') as f:
                f.write(rendered_content)
                
            print(f"Template rendered successfully to {output_path}")
            
        except Exception as e:
            print(f"Error rendering template {template_path}: {str(e)}")
            raise

    def inject_traefik_labels(self, service_name: str, domain: str, port: int, enable_https: bool = True) -> str:
        """
        Helper para generar etiquetas de Traefik estándar.
        Puede ser llamado desde dentro de las plantillas Jinja2 si se pasa al contexto.
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