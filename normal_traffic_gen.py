import time
import random
from common import VehicleMessage, NORMAL_GEN_INTERVAL
from ipc_utils import send_obj_message

def run_normal_traffic(queues):
    vehicle_id = 0
    directions = ["N", "S", "E", "W"]

    while True:
        vehicle_id += 1
        source = random.choice(directions)
        dest = random.choice([d for d in directions if d != source])

        vehicle = VehicleMessage(vehicle_id, source, dest)
        send_obj_message(queues[source], vehicle)

        time.sleep(NORMAL_GEN_INTERVAL)

def main(queues):
    run_normal_traffic(queues)