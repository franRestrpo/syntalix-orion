import os
import secrets
import string
import bcrypt
from typing import Dict, Any, List
from getpass import getpass

class ConfigManager:
    def __init__(self):
        self.variables: Dict[str, str] = {}

    def load_variables(self, manifest: Dict[str, Any]) -> Dict[str, str]:
        """
        Procesa las variables definidas en el manifiesto:
        1. Carga variables existentes desde el archivo .env si existe.
        2. Pregunta al usuario si desea mantener los valores actuales.
        3. Solicita o genera las variables faltantes.
        """
        service_id = manifest.get('id', manifest.get('name', 'service')).lower()
        deploy_dir = os.path.join(os.getcwd(), 'deploy')
        env_path = os.path.join(deploy_dir, f"{service_id}.env")
        
        existing_vars = self.load_env_file(env_path)
        keep_existing = False
        
        if existing_vars:
            print(f"\n[INFO] Configuration detected for {manifest['name']} in {env_path}")
            try:
                choice = input("Do you want to keep existing values? (Y/n): ").strip().lower()
                keep_existing = (choice != 'n')
            except EOFError:
                keep_existing = True

        config_vars = {}
        
        # Procesar variables definidas en el manifiesto
        if 'variables' in manifest:
            for var_name, var_def in manifest['variables'].items():
                # Si queremos mantener y la variable existe, la usamos
                if keep_existing and var_name in existing_vars:
                    config_vars[var_name] = existing_vars[var_name]
                    continue

                var_type = var_def.get('type', 'string')
                required = var_def.get('required', True)
                # Usar valor previo como default si existe
                default = existing_vars.get(var_name, var_def.get('default', ''))
                description = var_def.get('description', f"Enter value for {var_name}")

                if var_type == 'secret':
                    # Generar secreto automáticamente si no se pide input o si el usuario lo prefiere
                    if var_def.get('auto_generate', True) and not existing_vars.get(var_name):
                        value = self._generate_secret(length=var_def.get('length', 32))
                        print(f"Generated secret for {var_name}")
                    elif existing_vars.get(var_name) and keep_existing:
                        value = existing_vars[var_name]
                    else:
                        value = self._prompt_secret(var_name, description)
                    
                    # Aplicar transformación si es necesario (ej: bcrypt para htpasswd)
                    if var_def.get('transform') == 'bcrypt' and not value.startswith('$2b$'):
                        hashed = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt())
                        value = hashed.decode('utf-8')
                        print(f"Hashed secret for {var_name}")
                    
                    config_vars[var_name] = value
                
                else:
                    config_vars[var_name] = self._prompt_input(var_name, description, default, required)

        self.variables.update(config_vars)
        return config_vars

    def load_env_file(self, env_path: str) -> Dict[str, str]:
        """Lee un archivo .env y devuelve un diccionario de variables."""
        env_vars = {}
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not read existing .env file: {e}")
        return env_vars
def _prompt_input(self, var_name: str, description: str, default: str, required: bool) -> str:
        """Solicita input estándar al usuario."""
        while True:
            prompt_text = f"{description} [{default}]: " if default else f"{description}: "
            try:
                value = input(prompt_text).strip()
            except EOFError:
                print("\n[DEBUG] EOFError detected. Using default or failing.")
                if default:
                    return default
                raise

            if not value and default:
                return default
            
            if not value and required:
                print(f"Error: {var_name} is required.")
                continue
                
            return value

    def _prompt_secret(self, var_name: str, description: str) -> str:
        """Solicita un secreto de forma oculta."""
        while True:
            try:
                value = getpass(f"{description}: ").strip()
            except EOFError:
                print("\n[DEBUG] EOFError detected. Failing.")
                raise

            if value:
                return value
            print(f"Error: {var_name} is required.")

    def _generate_secret(self, length: int = 32) -> str:
        """Genera una cadena aleatoria segura."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(length))

    def generate_env_file(self, output_path: str, variables: Dict[str, str]) -> None:
        """Escribe las variables en un archivo .env."""
        with open(output_path, 'w') as f:
            for key, value in variables.items():
                f.write(f"{key}={value}\n")
        print(f"Configuration saved to {output_path}")