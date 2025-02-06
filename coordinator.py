import time
import os
import signal
from ipc_utils import receive_obj_message
from common import LightState


# Global flags
last_state = None
unexpected_vehicle = None


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

# Function to process a high-priority vehicle
def process_priority_vehicle(queue, shared_state, display_socket, lights_pid):
    """
    Processes a high-priority vehicle.
    """
    send_update(display_socket, f"[COORDINATOR] 🚨 High priority on the way.")

    # Skip non-priority vehicles until the priority vehicle arrives.
    vehicle = receive_obj_message(queue)
    while not vehicle.priority:
        send_update(display_socket, "-------------------------------- Solitary  --------------------------------")
        send_update(display_socket, f"[COORDINATOR] ✅ {vehicle} PASSES.")
        vehicle = receive_obj_message(queue)

    # Allow priority vehicle to pass.
    send_update(display_socket, "---------------------------- Priority Solitary ----------------------------")
    send_update(display_socket, f"[COORDINATOR] 🚨 {vehicle} PASSES.")

    # Signal lights to return to the normal cycle.
    os.kill(lights_pid, signal.SIGUSR2)

    # Wait until the lights state is no longer the priority state (back to normal).
    desired_state = get_priority_light(vehicle.source_road)
    while shared_state.get("state") == desired_state:
        time.sleep(0.05)

# Functions to process non-priority vehicles
def process_pair(vehicle1, vehicle2, display_socket):
    """
    Processes a pair of non-priority vehicles from opposite directions according to the turning-right rule.
    """
    if vehicle2.is_turning_right() and not vehicle1.is_turning_right():
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
    global unexpected_vehicle
    global last_state

    # Initialize and log the traffic lights state.
    current_state = shared_state.get("state")
    send_update(display_socket, f"[COORDINATOR] 🚦 Initial traffic lights: {current_state}")
    last_state = current_state

    while True:
        # Get the current traffic lights state.
        current_state = shared_state.get("state")

        # If the traffic lights have changed, print the change.
        if current_state != last_state:
            last_state = current_state
            send_update(display_socket,"---------------------------------------------------------------------------")

            # Handle priority vehicle passage if priority lights are active
            if last_state.is_priority_vehicle_light():
                send_update(display_socket, f"[COORDINATOR] 🚦 Priority lights set: {current_state}")
                if not unexpected_vehicle:
                    active_direction = current_state.get_active_directions()[0]
                    process_priority_vehicle(queues[active_direction], shared_state, display_socket, lights_pid)
                    continue
                else:
                    # Allow priority vehicle to pass.
                    send_update(display_socket, f"[COORDINATOR] 🚨 High priority on the way.")
                    send_update(display_socket,"---------------------------- Priority Solitary ----------------------------")
                    send_update(display_socket, f"[COORDINATOR] 🚨 {unexpected_vehicle} PASSES.")
                    unexpected_vehicle = None

                    # Signal lights to return to the normal cycle.
                    os.kill(lights_pid, signal.SIGUSR2)

                    # Wait until the lights state is no longer the priority state (back to normal).
                    while shared_state.get("state") == last_state:
                        time.sleep(0.05)

            else:
                send_update(display_socket, f"[COORDINATOR] 🚦 Traffic lights changed: {current_state}")

        # If no priority vehicle on the way.
        # Determine active directions from the current light state.
        active_directions = current_state.get_active_directions()

        if active_directions:
            non_priority_vehicles = {}
            # Retrieve vehicles from each active direction.
            for direction in active_directions:
                vehicle = receive_obj_message(queues[direction], block=False)
                if vehicle is not None:
                    if vehicle.priority:
                        unexpected_vehicle = vehicle
                    else:
                        non_priority_vehicles[direction] = vehicle

            # After checking all active directions, process non-priority vehicles.
            if non_priority_vehicles:
                process_non_priority_vehicles(non_priority_vehicles, active_directions, display_socket)

        time.sleep(0.1)  # 100 msj