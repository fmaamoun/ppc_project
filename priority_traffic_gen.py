import time
import random
from common import VehicleMessage, PRIORITY_GEN_INTERVAL
from ipc_utils import send_obj_message

def run_priority_traffic(queues, lights_pid):
    vehicle_id = 1000
    directions = ["N", "S", "E", "W"]

    while True:
        vehicle_id += 1
        source = random.choice(directions)
        dest = random.choice([d for d in directions if d != source])

        msg = VehicleMessage(vehicle_id, source, dest, priority=True)
        send_obj_message(queues[source], msg)

        # Envoie d'un signal au process des feux [à coder]

        time.sleep(PRIORITY_GEN_INTERVAL)

def main(queues, lights_pid):
    run_priority_traffic(queues, lights_pid)
