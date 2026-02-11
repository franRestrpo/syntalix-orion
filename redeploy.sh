#!/bin/bash
set -e

# Remove existing stacks
echo "Removing Portainer and Traefik stacks..."
docker stack rm portainer || true
docker stack rm traefik || true

echo "Waiting for removal (15s)..."
for i in {15..1}; do echo -n "$i " && sleep 1; done
echo ""

# Create missing volume if needed
if ! docker volume ls -q | grep -q "^volume_swarm_shared$"; then
    echo "Creating missing volume: volume_swarm_shared"
    docker volume create volume_swarm_shared
fi

# Ensure other volumes exist
if ! docker volume ls -q | grep -q "^portainer_data$"; then
    echo "Creating missing volume: portainer_data"
    docker volume create portainer_data
fi

if ! docker volume ls -q | grep -q "^volume_swarm_certificates$"; then
    echo "Creating missing volume: volume_swarm_certificates"
    docker volume create volume_swarm_certificates
fi

# Ensure network exists
if ! docker network ls --format '{{.Name}}' | grep -q "^SyntalixNet$"; then
    echo "Creating missing network: SyntalixNet"
    docker network create --driver=overlay SyntalixNet
fi

# Deploy Traefik
echo "Deploying Traefik..."
docker stack deploy -c deploy/traefik_stack.yml traefik

# Deploy Portainer
echo "Deploying Portainer..."
docker stack deploy -c deploy/portainer_stack.yml portainer

echo "Done!"
