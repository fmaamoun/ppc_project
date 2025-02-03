import time
import random
import os
import signal
from common import VehicleMessage, PRIORITY_GEN_INTERVAL
from ipc_utils import send_obj_message


def send_priority_signal(lights_pid):
    """
    Sends a SIGUSR1 signal to the lights process to indicate a high-priority vehicle is approaching.
    """
    try:
        os.kill(lights_pid, signal.SIGUSR1)
    except ProcessLookupError:
        print("[PRIORITY_GEN] Error: Lights process not found!")


def run_priority_traffic(queues, lights_pid, shared_state):
    """
    Generates high-priority vehicles at a defined interval.
    Sends them to the appropriate message queue.
    Before sending the signal, stores the vehicle's source in the shared state so that
    the lights process knows which direction to set to green.
    """
    vehicle_id = 0  # You can choose negative IDs for priority vehicles.
    directions = ["N", "S", "E", "W"]

    while True:
        time.sleep(PRIORITY_GEN_INTERVAL)
        vehicle_id -= 1
        source = random.choice(directions)
        dest = random.choice([d for d in directions if d != source])
        vehicle = VehicleMessage(vehicle_id, source, dest, priority=True)
        send_obj_message(queues[source], vehicle)

        # Store the requested priority direction in the shared state.
        shared_state['priority_direction'] = source

        # Notify the lights process.
        send_priority_signal(lights_pid)


def main(queues, lights_pid, shared_state):
    run_priority_traffic(queues, lights_pid, shared_state)
