import multiprocessing
import sys
import socket
import time
from ipc_utils import init_message_queues
from coordinator import main as coordinator_main
from display import main as display_main
from lights import main as lights_main
from normal_traffic_gen import main as normal_traffic_main
from priority_traffic_gen import main as priority_traffic_main
from common import DISPLAY_HOST, DISPLAY_PORT, LightState

def main():
    """
    Initializes all processes required for the simulation.
    """
    # 1. Start the display process first (TCP server).
    display_process = multiprocessing.Process(target=display_main, name="Display Process")
    display_process.start()
    print("[MAIN] Display process started.")

    # 2. Create a Manager for shared memory and initialize the traffic light state.
    manager = multiprocessing.Manager()
    shared_state = manager.dict()
    shared_state['state'] = LightState(north=1, south=1, east=0, west=0)  # Initial state
    shared_state['priority_direction'] = None  # Initial state

    # 3. Initialize the SysV IPC message queues.
    queues = init_message_queues()

    # 4. Start the lights process.
    lights_process = multiprocessing.Process(target=lights_main, args=(shared_state,), name="Lights Process")
    lights_process.start()
    print("[MAIN] Lights process started.")

    # 5. Start the normal traffic generation process.
    normal_process = multiprocessing.Process(target=normal_traffic_main, args=(queues,), name="Normal Traffic Process")
    normal_process.start()
    print("[MAIN] Normal traffic generation process started.")

    # 6. Start the priority traffic generation process
    priority_process = multiprocessing.Process(target=priority_traffic_main, args=(queues, lights_process.pid, shared_state), name="Priority Traffic Process")
    priority_process.start()
    print("[MAIN] Priority traffic generation process started.")

    # 7. Establish a TCP connection to the display process.
    connected = False
    max_retries = 10  # Retry limit
    retries = 0
    while not connected and retries < max_retries:
        try:
            display_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            display_socket.connect((DISPLAY_HOST, DISPLAY_PORT))
            connected = True
            print("[MAIN] Coordinator successfully connected to display process.")
        except Exception as e:
            print(f"[MAIN] Waiting for display process... {e}")
            retries += 1

    if not connected:
        print("[MAIN] Failed to connect to display process after several retries. Exiting.")
        sys.exit(1)

    # 8. Start the coordinator process.
    coordinator_process = multiprocessing.Process(
        target=coordinator_main,
        args=(queues, shared_state, display_socket, lights_process.pid),
        name="Coordinator Process"
    )
    coordinator_process.start()
    print("[MAIN] Coordinator process started.")

    # 9. Wait for all processes.
    coordinator_process.join()
    lights_process.join()
    normal_process.join()
    priority_process.join()
    display_process.join()

if __name__ == "__main__":
    main()