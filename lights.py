import time
import sysv_ipc
from common import LightState, LIGHT_CHANGE_INTERVAL
from ipc_utils import init_shared_light_state, write_light_state


def toggle_lights(state: LightState) -> LightState:
    """Reverses traffic light state."""
    return LightState(north=1 - state.north, south=1 - state.south, east=1 - state.east, west=1 - state.west)

def main():
    """Manages the traffic light cycle and notifies updates."""
    shm = init_shared_light_state()
    state = LightState(north=1, south=1, east=0, west=0)

    while True:
        time.sleep(LIGHT_CHANGE_INTERVAL)
        state = toggle_lights(state)  # Change light status
        write_light_state(shm, state)

if __name__ == "__main__":
    main()
