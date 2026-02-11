#!/usr/bin/env python3
import requests
import json
import os
import sys
from pathlib import Path

# Configuración
PORTAINER_URL = os.getenv("PORTAINER_URL", "https://portainer.example.com")
API_KEY = os.getenv("PORTAINER_API_KEY")
ENDPOINT_ID = 1  # ID del endpoint (entorno) de Docker Swarm, usualmente 1

def deploy_stack(stack_name, stack_file_path):
    if not API_KEY:
        print("Error: PORTAINER_API_KEY environment variable is not set.")
        sys.exit(1)

    print(f"Deploying stack '{stack_name}' from {stack_file_path} to {PORTAINER_URL}...")

    # Leer contenido del archivo Stack
    try:
        with open(stack_file_path, 'r') as f:
            stack_content = f.read()
    except FileNotFoundError:
        print(f"Error: Stack file not found at {stack_file_path}")
        sys.exit(1)

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # 1. Verificar si el stack ya existe
    stacks_url = f"{PORTAINER_URL}/api/stacks"
    response = requests.get(stacks_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error listing stacks: {response.status_code} - {response.text}")
        sys.exit(1)

    existing_stack = next((s for s in response.json() if s['Name'] == stack_name), None)

    if existing_stack:
        print(f"Stack '{stack_name}' exists (ID: {existing_stack['Id']}). Updating...")
        # Update Stack
        update_url = f"{PORTAINER_URL}/api/stacks/{existing_stack['Id']}?endpointId={ENDPOINT_ID}"
        payload = {
            "stackFileContent": stack_content,
            "prune": True,
            "pullImage": True
        }
        response = requests.put(update_url, headers=headers, json=payload)
    else:
        print(f"Stack '{stack_name}' does not exist. Creating...")
        # Create Stack (Swarm)
        # type=1 for Swarm, method=string
        create_url = f"{PORTAINER_URL}/api/stacks?type=1&method=string&endpointId={ENDPOINT_ID}"
        payload = {
            "name": stack_name,
            "stackFileContent": stack_content
        }
        response = requests.post(create_url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print(f"✅ Stack '{stack_name}' deployed successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error deploying stack: {response.status_code} - {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python portainer_deploy.py <stack_name> <path_to_stack_file>")
        print("Example: python portainer_deploy.py traefik ../deploy/traefik_stack.yml")
        sys.exit(1)
    
    deploy_stack(sys.argv[1], sys.argv[2])