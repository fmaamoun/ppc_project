from enum import Enum

# Enum to represent traffic light color
class LightColor(Enum):
    RED = 0
    GREEN = 1

# Message structure for vehicles
class VehicleMessage:
    def __init__(self, vehicle_id, source_road, dest_road, priority=False):
        self.vehicle_id = vehicle_id
        self.source_road = source_road
        self.dest_road = dest_road
        self.priority = priority

# Constants
NORMAL_GEN_INTERVAL = 10     # in seconds
PRIORITY_GEN_INTERVAL = 15  # in seconds
LIGHT_CHANGE_INTERVAL = 5   # in seconds
