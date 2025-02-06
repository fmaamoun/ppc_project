import time
import os
import signal
from ipc_utils import receive_obj_message
from common import LightState


# Global flags
last_state = None

# Utility functions
def send_update(display_socket, msg):
    """
    Sends a message to the display process.
    """
    try:
        display_socket.sendall((msg + "\n").encode("utf-8"))
    except Exception as exc:
        print(f"[COORDINATOR] Error sending update: {exc}")

def get_priority_light(direction):
    """
    Returns a LightState with green only for the given direction.
    """
    return LightState(
        north=1 if direction == "N" else 0,
        south=1 if direction == "S" else 0,
        east=1 if direction == "E" else 0,
        west=1 if direction == "W" else 0
    )

def is_turning_right(vehicle):
    """
    Returns True if the vehicle is turning right.
    """
    right_of = {"N": "E", "E": "S", "S": "W", "W": "N"}
    return vehicle.dest_road == right_of.get(vehicle.source_road)

# Process vehicle
def process_priority_vehicle(vehicle, shared_state, display_socket, lights_pid):
    """
    Processes a high-priority vehicle.
    """
    send_update(display_socket, "-------------------------------- Priority Solitary  --------------------------------")
    send_update(display_socket, f"[COORDINATOR] 🚨 High priority detected: {vehicle}.")
    desired_state = get_priority_light(vehicle.source_road)

    # Signal lights to change for the priority vehicle.
    shared_state['priority_direction'] = vehicle.source_road
    os.kill(lights_pid, signal.SIGUSR1)

    # Wait until the lights have changed to the desired state.
    while shared_state.get("state") != desired_state:
        time.sleep(0.05)
    global last_state
    last_state = shared_state.get("state")

    # Vehicle can pass.
    send_update(display_socket, f"[COORDINATOR] 🚦 Priority lights set: {shared_state.get('state')}")
    send_update(display_socket, f"[COORDINATOR] 🚨 {vehicle} PASSES.")

    # Signal lights to return to the normal cycle.
    os.kill(lights_pid, signal.SIGUSR2)

    # Wait until the lights state is no longer the priority state (back to normal).
    while shared_state.get("state") == desired_state:
        time.sleep(0.05)

def process_pair(vehicle1, vehicle2, display_socket):
    """
    Processes a pair of non-priority vehicles from opposite directions according to the turning-right rule.
    """
    if is_turning_right(vehicle2) and not is_turning_right(vehicle1):
        send_update(display_socket, f"[COORDINATOR] ✅ {vehicle2} PASSES.")
        send_update(display_socket, f"[COORDINATOR] ✅ {vehicle1} PASSES.")
    else:
        send_update(display_socket, f"[COORDINATOR] ✅ {vehicle1} PASSES.")
        send_update(display_socket, f"[COORDINATOR] ✅ {vehicle2} PASSES.")

def process_non_priority_vehicles(non_priority_vehicles, active_directions, display_socket):
    """
    Processes any collected non-priority vehicles:
      - If both active directions have a vehicle, process them as a pair.
      - Otherwise, process each individually.
    """
    if len(non_priority_vehicles) == 2:
        send_update(display_socket, "-------------------------------- Pair --------------------------------")
        d1, d2 = active_directions[0], active_directions[1]
        process_pair(non_priority_vehicles[d1], non_priority_vehicles[d2], display_socket)
    else:
        send_update(display_socket, "-------------------------------- Solitary  --------------------------------")
        for vehicle in non_priority_vehicles.values():
            send_update(display_socket, f"[COORDINATOR] ✅ {vehicle} PASSES.")

# Main
def main(queues, shared_state, display_socket, lights_pid):
    """
    Entry point for the coordinator process.
    Allows all vehicles (priority or not) to pass according to traffic regulations and the state of traffic lights.
    """
    # Print the initial traffic lights state.
    current_state = shared_state.get("state")
    send_update(display_socket, f"[COORDINATOR] 🚦 Initial traffic lights: {current_state}")
    global last_state
    last_state = current_state

    while True:
        # 1. Get the current traffic lights state.
        current_state = shared_state.get("state")

        # 2. If the traffic lights have changed, print the change.
        if current_state != last_state:
            send_update(display_socket,"---------------------------------------------------------------------------")
            send_update(display_socket, f"[COORDINATOR] 🚦 Traffic lights changed: {current_state}")
            last_state = current_state

        # 3. Determine active directions based on current lights.
        if current_state.north == 1 and current_state.south == 1:
            active_directions = ["N", "S"]
        elif current_state.east == 1 and current_state.west == 1:
            active_directions = ["E", "W"]
        else:
            active_directions = []

        if active_directions:
            non_priority_vehicles = {}
            # Retrieve vehicles from each active direction.
            for direction in active_directions:
                vehicle = receive_obj_message(queues[direction], block=False)
                if vehicle is not None:
                    # If a high-priority vehicle is detected, process any already collected
                    # non-priority vehicles just before processing the priority vehicle.
                    if hasattr(vehicle, "priority") and vehicle.priority:
                        if non_priority_vehicles:
                            process_non_priority_vehicles(non_priority_vehicles, active_directions, display_socket)
                            non_priority_vehicles = {}
                        process_priority_vehicle(vehicle, shared_state, display_socket, lights_pid)
                        break
                    else:
                        non_priority_vehicles[direction] = vehicle

            # After checking all active directions, process non-priority vehicles.
            if non_priority_vehicles:
                process_non_priority_vehicles(non_priority_vehicles, active_directions, display_socket)

        time.sleep(0.1) # 100 ms