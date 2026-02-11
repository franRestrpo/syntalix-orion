import os

def generate_stack_file(template_path, output_path, replacements):
    """
    Lee una plantilla YAML, reemplaza los marcadores y escribe el archivo final.
    """
    with open(template_path, "r") as f:
        content = f.read()

    for key, value in replacements.items():
        # Reemplazamos {{KEY}} con el valor
        content = content.replace(f"{{{{{key}}}}}", str(value))

    with open(output_path, "w") as f:
        f.write(content)
    
    print(f"Generado archivo de stack: {output_path}")

def generate_env_file(output_path, env_vars):
    """
    Genera un archivo .env con las variables proporcionadas.
    """
    with open(output_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"Generado archivo de entorno: {output_path}")