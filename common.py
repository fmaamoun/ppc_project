# Time intervals (in seconds)
NORMAL_GEN_INTERVAL = 3          # Interval for generating normal vehicles
LIGHT_CHANGE_INTERVAL = 10       # Interval for traffic light changes

# Socket configuration for the display process
DISPLAY_HOST = "localhost"
DISPLAY_PORT = 9999

class LightState:
    """
    Represents the state of the traffic lights at the intersection.
    Each direction is represented by an integer (1 for green, 0 for red).
    For this simulation, the North-South lights are identical and opposite
    to the East-West lights.
    """
    def __init__(self, north=1, south=1, east=0, west=0):
        self.north = north
        self.south = south
        self.east = east
        self.west = west

    def __eq__(self, other):
        if isinstance(other, LightState):
            return (self.north == other.north and
                    self.south == other.south and
                    self.east == other.east and
                    self.west == other.west)
        return False

    def __repr__(self):
        return f"LightState(N={self.north}, S={self.south}, E={self.east}, W={self.west})"

class VehicleMessage:
    """
    Represents a vehicle's information.

    Attributes:
      vehicle_id: Unique identifier for the vehicle.
      source_road: The road section where the vehicle comes from ('N', 'S', 'E', or 'W').
      dest_road: The road section where the vehicle is headed.
      priority: Boolean flag indicating if the vehicle is high-priority (not used in this version).
    """
    def __init__(self, vehicle_id: int, source_road: str, dest_road: str, priority=False):
        self.vehicle_id = vehicle_id
        self.source_road = source_road
        self.dest_road = dest_road
        self.priority = priority

    def __repr__(self):
        return (f"VehicleMessage(ID={self.vehicle_id}, "
                f"From={self.source_road} -> To={self.dest_road}, "
                f"Priority={self.priority})")
