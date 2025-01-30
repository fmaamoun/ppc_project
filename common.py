# ----------------------------
# Constants for Traffic System
# ----------------------------

NORMAL_GEN_INTERVAL = 3  # Vehicle generation interval (seconds)
PRIORITY_GEN_INTERVAL = 15  # Priority vehicle interval (seconds)
LIGHT_CHANGE_INTERVAL = 10  # Traffic light change interval (seconds)

# ----------------------------
# Light State Class
# ----------------------------

class LightState:
    """Represents the state of traffic lights at an intersection."""

    def __init__(self, north=1, south=1, east=0, west=0):
        """Initialize traffic light states for each direction."""
        self.north = north
        self.south = south
        self.east = east
        self.west = west

    def __eq__(self, other):
        """Compare two LightState objects."""
        if isinstance(other, LightState):
            return (self.north == other.north and
                    self.south == other.south and
                    self.east == other.east and
                    self.west == other.west)
        return False  # If `other` is not a LightState, they are not equal

    def __repr__(self):
        """Return a string representation of the LightState."""
        return f"LightState(N={self.north}, S={self.south}, E={self.east}, W={self.west})"

# ----------------------------
# Vehicle Message Class
# ----------------------------

class VehicleMessage:
    """Represents a vehicle's movement and priority status."""

    def __init__(self, vehicle_id: int, source_road: str, dest_road: str, priority=False):
        """Initialize vehicle attributes: ID, source, destination, and priority."""
        self.vehicle_id = vehicle_id
        self.source_road = source_road
        self.dest_road = dest_road
        self.priority = priority

    def __repr__(self):
        """Return a string representation of the VehicleMessage."""
        return f"VehicleMessage(ID={self.vehicle_id}, From={self.source_road} → To={self.dest_road}, Priority={self.priority})"
