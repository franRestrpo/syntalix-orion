from checks import require, swarm_active, network_exists
from resources import validate
from constants import DEFAULT_NETWORK

def run(network_name=DEFAULT_NETWORK):
    require("docker")
    swarm_active()
    network_exists(network_name)
    validate()
