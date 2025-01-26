# common.py

from enum import Enum

# Par exemple, un énum pour représenter la couleur du feu
class LightColor(Enum):
    RED = 0
    GREEN = 1

# Structure de message pour les véhicules
class VehicleMessage:
    def __init__(self, vehicle_id, source_road, dest_road, priority=False):
        self.vehicle_id = vehicle_id
        self.source_road = source_road
        self.dest_road = dest_road
        self.priority = priority

# Constantes
NORMAL_GEN_INTERVAL = 2     # en secondes
PRIORITY_GEN_INTERVAL = 10  # en secondes
LIGHT_CHANGE_INTERVAL = 5   # en secondes
