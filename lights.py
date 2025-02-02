import time
from common import LightState, LIGHT_CHANGE_INTERVAL

def toggle_lights(state: LightState) -> LightState:
    """
    Toggles the traffic light state.

    For example, if North-South is green (1) and East-West is red (0),
    toggling will set North-South to red and East-West to green, and vice versa.
    """
    return LightState(
        north=1 - state.north,
        south=1 - state.south,
        east=1 - state.east,
        west=1 - state.west
    )

def main(shared_state):
    """
    Entry point for the lights process.

    Args:
        shared_state: A Manager dictionary used to store the traffic light state.
    """
    # Initialize the lights: North-South green, East-West red.
    state = LightState(north=1, south=1, east=0, west=0)
    shared_state['state'] = state

    while True:
        time.sleep(LIGHT_CHANGE_INTERVAL)
        state = toggle_lights(state)
        shared_state['state'] = state