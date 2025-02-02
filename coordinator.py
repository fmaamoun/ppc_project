import time
import sys
from ipc_utils import receive_obj_message


def can_vehicle_proceed(vehicle, light_state):
    """
    Determines whether a vehicle can pass based on the current traffic light state.

    Vehicles from the North or South require a green light in the North-South direction.
    Vehicles from the East or West require a green light in the East-West direction.
    """
    if vehicle.source_road in ["N", "S"]:
        return light_state.north == 1
    else:
        return light_state.east == 1


def process_vehicles(queues, shared_state, display_socket):
    """
    Main loop to process vehicles:
      - Reads the current traffic light state.
      - Processes vehicles from the SysV IPC message queues and those waiting.
      - Sends status updates to the display process via the TCP socket.
    """

    def send_update(message):
        """
        Sends an update message to the display process over the TCP socket.
        """
        try:
            display_socket.sendall((message + "\n").encode('utf-8'))
        except Exception as e:
            print(f"[COORDINATOR] Error sending update: {e}")

    send_update("[COORDINATOR] Started managing vehicle flow...")
    waiting_vehicles = []  # List to hold vehicles waiting for a green light

    last_light_state = shared_state.get('state', None)
    send_update(f"[COORDINATOR] 🚦 Traffic light changed: {last_light_state}")

    while True:
        current_light_state = shared_state.get('state', None)
        if current_light_state is None:
            sys.exit(1)

        # Check for traffic light state change.
        if current_light_state != last_light_state:
            send_update(f"[COORDINATOR] 🚦 Traffic light changed: {current_light_state}")
            last_light_state = current_light_state

            # Process vehicles that were waiting.
            new_waiting = []
            for vehicle in waiting_vehicles:
                if can_vehicle_proceed(vehicle, current_light_state):
                    send_update(
                        f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} PASSES (was waiting).")
                else:
                    new_waiting.append(vehicle)
            waiting_vehicles = new_waiting

        # Process newly arrived vehicles from each direction.
        for direction in ["N", "S", "E", "W"]:
            # Continue receiving all messages from the queue in non-blocking mode.
            while True:
                vehicle = receive_obj_message(queues[direction], block=False)
                if vehicle is None:
                    break
                if can_vehicle_proceed(vehicle, current_light_state):
                    send_update(
                        f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} PASSES.")
                else:
                    send_update(
                        f"[COORDINATOR] ❌ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} WAITS (red light).")
                    waiting_vehicles.append(vehicle)

        time.sleep(1)  # Small delay to avoid busy looping


def main(queues, shared_state, display_socket):
    """
    Entry point for the coordinator process.

    - Reads messages from SysV IPC queues.
    - Reads shared memory for traffic light state.
    - Sends real-time status updates to the display process.
    """
    process_vehicles(queues, shared_state, display_socket)