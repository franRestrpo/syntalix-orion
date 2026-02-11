#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from core.registry import ServiceRegistry
from core.config import ConfigManager
from core.templating import TemplateManager

def main():
    # Inicializar componentes
    base_dir = Path(__file__).parent
    registry = ServiceRegistry(base_dir / "registry")
    config_manager = ConfigManager()
    template_manager = TemplateManager()

    # Escanear registro de servicios
    try:
        registry.scan_registry()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Mostrar menú de categorías y servicios
    categories = registry.get_categories()
    
    while True:
        print("\n=== Orion Service Installer (Modular V2) ===")
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category}")
        print("0. Exit")

        try:
            choice = input("\nSelect a category: ").strip()
        except EOFError:
            print("\n[DEBUG] EOFError detected. Exiting.")
            break
        
        if choice == '0':
            break
            
        try:
            cat_index = int(choice) - 1
            if 0 <= cat_index < len(categories):
                selected_category = categories[cat_index]
                services = registry.get_services_by_category(selected_category)
                
                print(f"\n--- {selected_category} Services ---")
                for i, service in enumerate(services, 1):
                    print(f"{i}. {service['name']} (v{service['version']})")
                print("0. Back")
                
                try:
                    srv_choice = input("\nSelect a service to install: ").strip()
                except EOFError:
                    print("\n[DEBUG] EOFError detected. Exiting.")
                    break
                
                if srv_choice == '0':
                    continue
                    
                srv_index = int(srv_choice) - 1
                if 0 <= srv_index < len(services):
                    selected_service = services[srv_index]
                    install_service(selected_service, config_manager, template_manager)
                else:
                    print("Invalid service selection.")
            else:
                print("Invalid category selection.")
        except ValueError:
            print("Please enter a valid number.")

def ensure_network(network_name):
    import subprocess
    try:
        # Check if network exists
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", f"name={network_name}", "--format", "{{.Name}}"],
            capture_output=True, text=True
        )
        if network_name not in result.stdout.strip():
            print(f"Creating network '{network_name}'...")
            subprocess.run(
                ["docker", "network", "create", "--driver=overlay", "--attachable", network_name],
                check=True
            )
            print(f"✅ Network '{network_name}' created.")
        else:
            print(f"ℹ️ Network '{network_name}' already exists.")
    except Exception as e:
        print(f"⚠️ Failed to check/create network: {e}")

def install_service(service_manifest, config_manager, template_manager):
    print(f"\nInstalling {service_manifest['name']}...")
    
    # 1. Cargar y solicitar variables
    variables = config_manager.load_variables(service_manifest)
    
    # 2. Ensure network exists if defined
    if "INTERNAL_NETWORK" in variables:
        ensure_network(variables["INTERNAL_NETWORK"])

    # 3. Preparar directorio de despliegue
    deploy_dir = Path.cwd() / "deploy"
    deploy_dir.mkdir(exist_ok=True)
    
    # 4. Generar archivo .env
    env_path = deploy_dir / f"{service_manifest['id']}.env"
    config_manager.generate_env_file(str(env_path), variables)
    
    # 5. Renderizar Stack File
    template_path = Path(service_manifest['path']) / "stack.yml.j2"
    output_path = deploy_dir / f"{service_manifest['id']}_stack.yml"
    
    try:
        template_manager.render_template(str(template_path), variables, str(output_path))
        print(f"✅ Stack file generated at: {output_path}")
        print(f"✅ Env file generated at: {env_path}")
        print(f"🚀 To deploy run: cd deploy && docker stack deploy -c {output_path.name} {service_manifest['id']}")
    except Exception as e:
        print(f"❌ Error generating stack file: {e}")
    except EOFError:
        # Manejar EOFError para entornos no interactivos
        print("\n[DEBUG] EOFError detected. This is expected in non-interactive environments.")
        return

if __name__ == "__main__":
    main()
