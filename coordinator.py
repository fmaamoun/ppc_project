import time
import os
import signal
from ipc_utils import receive_obj_message
from common import LightState

# Global flags
last_state = None

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
    Assumes roads are labeled "N", "E", "S", "W" in clockwise order.
    """
    right_of = {"N": "E", "E": "S", "S": "W", "W": "N"}
    return vehicle.dest_road == right_of.get(vehicle.source_road)

def process_vehicle(vehicle, display_socket):
    """
    Processes a single vehicle by sending a pass update message.
    """
    send_update(display_socket, f"[COORDINATOR] ✅ {vehicle} PASSES.")

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

    Rule (for non-priority vehicles):
      - If one vehicle is turning right and the other is not, the turning-right vehicle passes first.
      - Otherwise, they are processed in FIFO order.
    """
    if is_turning_right(vehicle1) and not is_turning_right(vehicle2):
        process_vehicle(vehicle1, display_socket)
        process_vehicle(vehicle2, display_socket)
    elif is_turning_right(vehicle2) and not is_turning_right(vehicle1):
        process_vehicle(vehicle2, display_socket)
        process_vehicle(vehicle1, display_socket)
    else:
        process_vehicle(vehicle1, display_socket)
        process_vehicle(vehicle2, display_socket)

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
            process_vehicle(vehicle, display_socket)

def main(queues, shared_state, display_socket, lights_pid):
    """
    The coordinator process works as follows:
      1. Retrieve the current traffic lights state from shared_state.
      2. If the traffic lights change, send an update to the display.
      3. If the lights are green for one axis (NS or EW), attempt to non-blocking retrieve one vehicle
         from each of the two active queues.
      4. High-priority vehicles are processed immediately (solitary) and bypass pairing.
         For non-priority vehicles:
           - If vehicles from both opposite directions are available, process them as a pair using the turning-right rule.
           - If only one vehicle is available, process it individually.
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

            # After checking all active directions, process any remaining non-priority vehicles.
            if non_priority_vehicles:
                process_non_priority_vehicles(non_priority_vehicles, active_directions, display_socket)

        # Small delay to avoid a busy loop.
        time.sleep(0.1)
