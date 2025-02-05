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


def run_priority_traffic(queues, shared_state):
    """
    Continuously generates and sends priority vehicle messages to simulate priority traffic.
    """
    vehicle_id = 0
    directions = ["N", "S", "E", "W"]

    while True:
        # Wait
        time.sleep(PRIORITY_GEN_INTERVAL)

        # Create and send vehicle
        vehicle_id -= 1
        source = random.choice(directions)
        dest = random.choice([d for d in directions if d != source])
        vehicle = VehicleMessage(vehicle_id, source, dest, priority=True)
        send_obj_message(queues[source], vehicle)

        # Store the requested priority direction in the shared state.
        shared_state['priority_direction'] = source


def main(queues, shared_state):
    """
    Entry point for the priority traffic generation process.
    """
    run_priority_traffic(queues, shared_state)
