import multiprocessing
import time
import sysv_ipc

from normal_traffic_gen import main as normal_main
from priority_traffic_gen import main as priority_main
from ipc_utils import init_message_queues, receive_obj_message



def read_queues(queues):
    """
    Reads messages from queues (N, S, E, W) and prints them.
    Runs concurrently with normal traffic generation.
    """
    print("[TEST] Started reading messages from queues...")

    while True:
        for direction in ["N", "S", "E", "W"]:
            vehicle = receive_obj_message(queues[direction], block=False)
            if vehicle is not None:
                print(f"[TEST] Received VehicleMessage: id={vehicle.vehicle_id}, "
                      f"source={vehicle.source_road}, dest={vehicle.dest_road}, "
                      f"priority={vehicle.priority}")
        time.sleep(1)  # Avoid excessive CPU usage

def main():
    # Initialize message queues
    queues = init_message_queues()

    # Start normal.py's main function in a separate process
    normal_process = multiprocessing.Process(target=normal_main, args=(queues,))
    normal_process.start()

    priority_process = multiprocessing.Process(target=priority_main, args=(queues,1))
    priority_process.start()

    try:
        # Start reading queues
        read_queues(queues)
    except KeyboardInterrupt:
        print("\n[TEST] Stopping processes...")
        normal_process.terminate()
        normal_process.join()
        print("[TEST] Process terminated.")

if __name__ == "__main__":
    main()
