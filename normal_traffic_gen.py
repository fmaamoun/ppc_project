import time
import random
from common import VehicleMessage, NORMAL_GEN_INTERVAL
from ipc_utils import send_obj_message


def run_normal_traffic(queues):
    """
    Continuously generates and sends vehicle messages to simulate normal traffic.
    """
    vehicle_id = 0
    directions = ["N", "E", "S", "W"]

    while True:
        # Create and send vehicle
        vehicle_id += 1
        source = random.choice(directions)
        dest = random.choice([d for d in directions if d != source])
        vehicle = VehicleMessage(vehicle_id, source, dest)
        send_obj_message(queues[source], vehicle)

        # Wait
        time.sleep(NORMAL_GEN_INTERVAL)


def main(queues):
    """
    Entry point for the normal traffic generation process.
    """
    run_normal_traffic(queues)
