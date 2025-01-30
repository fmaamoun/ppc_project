import time
import multiprocessing
import sysv_ipc
from ipc_utils import (
    init_message_queues,
    receive_obj_message,
    init_shared_light_state,
    read_light_state
)
from normal_traffic_gen import main as normal_traffic_main
from lights import main as lights_main

def can_vehicle_proceed(vehicle, light_state):
    """
    Determines if a vehicle can proceed based on the traffic light state.
    Vehicles move only when the light is green.
    """
    if vehicle.source_road in ["N", "S"]:
        return light_state.north == 1  # North-South light must be green
    else:
        return light_state.east == 1  # East-West light must be green

def process_vehicles(queues, shm):
    """
    Continuously processes new vehicles and rechecks waiting ones when lights change.
    """
    print("[COORDINATOR] Started managing vehicle flow...")

    waiting_vehicles = []  # Store vehicles that couldn't pass
    last_light_state = read_light_state(shm)  # Initial light state

    while True:
        current_light_state = read_light_state(shm)  # Check current light state

        # 🚦 First, print light change **before handling vehicles**
        if current_light_state != last_light_state:
            print(f"[COORDINATOR] 🚦 Light changed: {current_light_state}")
            last_light_state = current_light_state  # Update last known light state

        # 🚗 Process waiting vehicles first
        new_waiting_vehicles = []
        for vehicle in waiting_vehicles:
            if can_vehicle_proceed(vehicle, current_light_state):
                print(f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} "
                      f"to {vehicle.dest_road} PASSES (Previously Waiting).")
            else:
                new_waiting_vehicles.append(vehicle)  # Still can't pass
        waiting_vehicles = new_waiting_vehicles  # Update waiting list

        # 🚗 Handle new vehicles immediately
        for direction in ["N", "S", "E", "W"]:
            vehicle = receive_obj_message(queues[direction], block=False)
            if vehicle:
                if can_vehicle_proceed(vehicle, current_light_state):
                    print(f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} "
                          f"to {vehicle.dest_road} PASSES.")
                else:
                    print(f"[COORDINATOR] ❌ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} "
                          f"to {vehicle.dest_road} WAITS (Red Light).")
                    waiting_vehicles.append(vehicle)  # Store in waiting list

        time.sleep(1)  # Avoid excessive CPU usage

def main():
    """
    Initializes message queues and shared memory,
    then starts vehicle processing and normal traffic generation.
    """
    queues = init_message_queues()
    shm = init_shared_light_state()

    # Start light process first
    lights_process = multiprocessing.Process(target=lights_main)
    lights_process.start()

    # Ensure lights have initialized memory before reading
    time.sleep(1)

    # Start normal traffic generation
    normal_process = multiprocessing.Process(target=normal_traffic_main, args=(queues,))
    normal_process.start()

    # Run the coordinator
    process_vehicles(queues, shm)

if __name__ == "__main__":
    main()
