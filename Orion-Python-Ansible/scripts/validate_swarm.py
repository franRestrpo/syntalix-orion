import requests
import json
import os
import sys
from getpass import getpass

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")

def print_info(msg):
    print(f"{YELLOW}[INFO]{RESET} {msg}")

def print_error(msg):
    print(f"{RED}[ERROR]{RESET} {msg}")

def validate_swarm_connection(url, username, password):
    """
    Validates connection to Portainer and underlying Docker Swarm.
    Replicates logic from 'stack_editavel' in SetupOrion.sh
    """
    
    # 1. Clean URL
    url = url.rstrip('/')
    if not url.startswith('http'):
        url = f"https://{url}"
    
    print_info(f"Connecting to Portainer at: {url}")

    # 2. Authentication (Get JWT)
    auth_url = f"{url}/api/auth"
    try:
        auth_payload = {"username": username, "password": password}
        response = requests.post(auth_url, json=auth_payload, verify=False) # verify=False because local certs might be self-signed or traefik generated
        
        if response.status_code != 200:
            print_error(f"Authentication failed. Status: {response.status_code}")
            print_error(response.text)
            return False
            
        jwt_token = response.json().get('jwt')
        if not jwt_token:
            print_error("No JWT token received.")
            return False
            
        print_success("Authenticated with Portainer (JWT Token received)")
        
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

    # Headers for subsequent requests
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    # 3. Get Endpoints (Find Primary/Swarm Endpoint)
    endpoints_url = f"{url}/api/endpoints"
    try:
        response = requests.get(endpoints_url, headers=headers, verify=False)
        endpoints = response.json()
        
        target_endpoint = None
        
        # Logic to find the local/primary endpoint
        for endpoint in endpoints:
            # Usually Id 1 is primary, or check Type (1 = Docker, 2 = Agent)
            if endpoint.get('Name') == 'primary' or endpoint.get('Id') == 1:
                target_endpoint = endpoint
                break
        
        if not target_endpoint and len(endpoints) > 0:
            target_endpoint = endpoints[0]
            
        if not target_endpoint:
            print_error("No endpoints found in Portainer.")
            return False
            
        endpoint_id = target_endpoint.get('Id')
        print_success(f"Found Endpoint ID: {endpoint_id} (Name: {target_endpoint.get('Name')})")

    except Exception as e:
        print_error(f"Failed to fetch endpoints: {str(e)}")
        return False

    # 4. Validate Swarm Status
    # We check /docker/info via the Portainer proxy to see if Swarm is active
    docker_info_url = f"{url}/api/endpoints/{endpoint_id}/docker/info"
    try:
        response = requests.get(docker_info_url, headers=headers, verify=False)
        
        if response.status_code != 200:
            print_error(f"Failed to get Docker Info. Status: {response.status_code}")
            return False
            
        docker_info = response.json()
        swarm_info = docker_info.get('Swarm', {})
        
        # Check if LocalNodeState is 'active'
        node_state = swarm_info.get('LocalNodeState')
        
        if node_state == 'active':
            print_success(f"Docker Swarm is ACTIVE.")
            print_info(f"Nodes in Swarm: {swarm_info.get('Nodes')}")
            
            # Get Swarm ID (Required for stack deployment in Portainer API)
            # Sometimes it's in a different endpoint depending on Portainer version, 
            # but usually accessible here or via /docker/swarm
            swarm_id = swarm_info.get('Cluster', {}).get('ID')
            if not swarm_id:
                 # Fallback try
                 swarm_resp = requests.get(f"{url}/api/endpoints/{endpoint_id}/docker/swarm", headers=headers, verify=False)
                 if swarm_resp.status_code == 200:
                     swarm_id = swarm_resp.json().get('ID')

            print_success(f"Swarm Cluster ID: {swarm_id}")
            return True
        else:
            print_error(f"Docker Swarm is NOT active. State: {node_state}")
            return False

    except Exception as e:
        print_error(f"Failed to validate Swarm: {str(e)}")
        return False

if __name__ == "__main__":
    print("--- Portainer & Swarm API Validator ---")
    
    # Try to get from Env Vars first
    url = os.getenv("PORTAINER_URL")
    user = os.getenv("PORTAINER_USER")
    pwd = os.getenv("PORTAINER_PASS")

    if not url:
        url = input("Portainer URL (e.g., https://portainer.domain.com): ")
    if not user:
        user = input("Username: ")
    if not pwd:
        pwd = getpass("Password: ")

    if validate_swarm_connection(url, user, pwd):
        print("\n" + GREEN + ">>> COMMUNICATION ESTABLISHED SUCCESSFULLY <<<" + RESET)
        sys.exit(0)
    else:
        print("\n" + RED + ">>> COMMUNICATION FAILED <<<" + RESET)
        sys.exit(1)