import multiprocessing
import sys
import socket
import threading
from ipc_utils import init_message_queues
from coordinator import main as coordinator_main
from display import main as display_main
from lights import main as lights_main
from normal_traffic_gen import main as normal_traffic_main
from priority_traffic_gen import main as priority_traffic_main
from common import DISPLAY_HOST, DISPLAY_PORT


def stop_processes(processes, queues, shared_state):
    """
    Terminates all running processes gracefully and cleans up resources.
    """
    print("[MAIN] Terminating all processes...")

    # Terminate all processes
    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join()

    # Remove all message queues
    for queue in queues.values():
        try:
            queue.remove()
            print(f"[MAIN] Removed message queue {queue.key}")
        except Exception as e:
            print(f"[MAIN] Error removing message queue {queue.key}: {e}")

    # Clear shared state
    shared_state.clear()
    print("[MAIN] Shared state cleared.")

    print("[MAIN] All processes and resources cleaned up.")


def listen_for_exit(processes, queues, shared_state):
    """
    Waits for user input and stops all processes when 'j' is pressed.
    """
    while True:
        key = input()
        if key.lower() == 'j':
            stop_processes(processes, queues, shared_state)
            sys.exit(0)


def main():
    """
    Initializes all processes required for the simulation.
    """
    processes = []

    # Start the display process first (TCP server).
    display_process = multiprocessing.Process(target=display_main, name="Display Process")
    display_process.start()
    processes.append(display_process)
    print("[MAIN] Display process started.")

    # Create a Manager for shared memory
    manager = multiprocessing.Manager()
    shared_state = manager.dict()

    # Initialize the SysV IPC message queues.
    queues = init_message_queues()

    # Start the lights process.
    lights_process = multiprocessing.Process(target=lights_main, args=(shared_state,), name="Lights Process")
    lights_process.start()
    processes.append(lights_process)
    print("[MAIN] Lights process started.")

    # Start the normal traffic generation process.
    normal_process = multiprocessing.Process(target=normal_traffic_main, args=(queues,), name="Normal Traffic Process")
    normal_process.start()
    processes.append(normal_process)
    print("[MAIN] Normal traffic generation process started.")

    # Start the priority traffic generation process
    priority_process = multiprocessing.Process(target=priority_traffic_main, args=(queues, shared_state),
                                               name="Priority Traffic Process")
    priority_process.start()
    processes.append(priority_process)
    print("[MAIN] Priority traffic generation process started.")

    # Establish a TCP connection to the display process.
    display_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    display_socket.connect((DISPLAY_HOST, DISPLAY_PORT))

    # Start the coordinator process.
    coordinator_process = multiprocessing.Process(
        target=coordinator_main,
        args=(queues, shared_state, display_socket, lights_process.pid),
        name="Coordinator Process"
    )
    coordinator_process.start()
    processes.append(coordinator_process)
    print("[MAIN] Coordinator process started.")

    # Start a separate thread to listen for user input to stop processes
    input_thread = threading.Thread(target=listen_for_exit, args=(processes, queues, shared_state),
                                    daemon=True)
    input_thread.start()

    # Wait for all processes.
    for process in processes:
        process.join()


if __name__ == "__main__":
    main()
