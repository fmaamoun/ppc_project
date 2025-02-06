import time
import signal
from common import LightState, LIGHT_CHANGE_INTERVAL


# Global flags
priority_mode = False
priority_requested = False
just_restored = False

# Utility functions
def handle_priority(signum, frame):
    """
    Triggered by SIGUSR1: request to switch to priority mode.
    """
    global priority_requested
    priority_requested = True

def handle_restore(signum, frame):
    """
    Triggered by SIGUSR2: restore normal mode immediately.
    """
    global priority_mode, just_restored
    priority_mode = False
    just_restored = True

def set_priority_light(direction):
    """
    Returns a LightState that is green only for the specified direction.
    """
    state = {
        "N": LightState(1, 0, 0, 0),
        "S": LightState(0, 1, 0, 0),
        "E": LightState(0, 0, 1, 0),
        "W": LightState(0, 0, 0, 1)
    }
    return state.get(direction)

def toggle_lights(state):
    """
    Toggles between N/S and E/W green lights.
    """
    return LightState(
        north=1 - state.north,
        south=1 - state.south,
        east=1 - state.east,
        west=1 - state.west
    )

# Main
def main(shared_state):
    """
    Entry point for the lights process.
    """
    global priority_mode, priority_requested, just_restored

    # Set up signal handlers
    signal.signal(signal.SIGUSR1, handle_priority)
    signal.signal(signal.SIGUSR2, handle_restore)

    # Initial normal state: N/S green, E/W red
    current_state = LightState(1, 1, 0, 0)
    shared_state["state"] = current_state

    step_time = 0.1  # 100 ms
    elapsed = 0.0

    while True:
        # If we've just restored, reset to the default normal state
        if just_restored:
            current_state = LightState(1, 1, 0, 0)
            shared_state["state"] = current_state
            elapsed = 0.0
            just_restored = False

        # If we are not in priority mode, either check for priority or handle normal toggling
        if not priority_mode:
            if priority_requested:
                priority_requested = False
                priority_mode = True
                direction = shared_state.get("priority_direction", "N")
                current_state = set_priority_light(direction)
                shared_state["state"] = current_state
            else:
                # Normal mode: switch lights after the configured interval
                if elapsed >= LIGHT_CHANGE_INTERVAL:
                    current_state = toggle_lights(current_state)
                    shared_state["state"] = current_state
                    elapsed = 0.0
                time.sleep(step_time)
                elapsed += step_time
        else:
            # In priority mode, wait for a restore signal
            time.sleep(step_time)
