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
        1. Solicita al usuario las variables requeridas (user_input).
        2. Genera automáticamente las variables de tipo 'secret' o 'generated'.
        3. Carga valores por defecto si no se proporciona entrada.
        """
        config_vars = {}
        
        # Procesar variables definidas en el manifiesto
        if 'variables' in manifest:
            for var_name, var_def in manifest['variables'].items():
                var_type = var_def.get('type', 'string')
                required = var_def.get('required', True)
                default = var_def.get('default', '')
                description = var_def.get('description', f"Enter value for {var_name}")

                if var_type == 'secret':
                    # Generar secreto automáticamente si no se pide input o si el usuario lo prefiere
                    if var_def.get('auto_generate', True):
                        value = self._generate_secret(length=var_def.get('length', 32))
                        print(f"Generated secret for {var_name}")
                    else:
                        value = self._prompt_secret(var_name, description)
                    
                    # Aplicar transformación si es necesario (ej: bcrypt para htpasswd)
                    if var_def.get('transform') == 'bcrypt':
                        # Traefik basic auth espera user:hash, pero el template ya pone user:.
                        # Aquí solo devolvemos el hash.
                        # bcrypt.hashpw devuelve bytes, decodificamos a string.
                        # bcrypt genera un salt y lo incluye en el hash.
                        hashed = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt())
                        value = hashed.decode('utf-8')
                        print(f"Hashed secret for {var_name}")
                    
                    config_vars[var_name] = value
                
                elif var_type == 'domain':
                    config_vars[var_name] = self._prompt_input(var_name, description, default, required)
                    # Aquí se podría añadir validación de dominio
                
                elif var_type == 'email':
                    config_vars[var_name] = self._prompt_input(var_name, description, default, required)
                    # Aquí se podría añadir validación de email

                else:
                    # Tipo string por defecto
                    config_vars[var_name] = self._prompt_input(var_name, description, default, required)

        self.variables.update(config_vars)
        return config_vars

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