import sysv_ipc
import pickle
from common import VehicleMessage, LightState

# ----------------------------
# Constants for SysV IPC
# ----------------------------

# Message queue keys for the four road sections (North, South, East, West)
KEY_N = 1
KEY_S = 2
KEY_E = 3
KEY_W = 4

# Shared memory configuration
SHM_KEY = 5
SHM_SIZE = 1024  # 1KB shared memory

# ----------------------------
# Message Queue Functions
# ----------------------------

def init_message_queues() -> dict:
    """Initialize and clear message queues for N, S, E, W."""
    queues = {
        "N": sysv_ipc.MessageQueue(KEY_N, sysv_ipc.IPC_CREAT),
        "S": sysv_ipc.MessageQueue(KEY_S, sysv_ipc.IPC_CREAT),
        "E": sysv_ipc.MessageQueue(KEY_E, sysv_ipc.IPC_CREAT),
        "W": sysv_ipc.MessageQueue(KEY_W, sysv_ipc.IPC_CREAT)
    }

    # Empty all pending messages from previous executions
    for queue in queues.values():
        try:
            while True:
                queue.receive(block=False)  # Read and delete
        except sysv_ipc.BusyError:
            pass

    return queues

def send_obj_message(queue: sysv_ipc.MessageQueue, obj: VehicleMessage):
    """Send a pickled object to a SysV message queue."""
    queue.send(pickle.dumps(obj), type=1)

def receive_obj_message(queue: sysv_ipc.MessageQueue, block: bool = False):
    """Receive and unpickle an object from a SysV message queue."""
    try:
        data, _type = queue.receive(block=block)
        return pickle.loads(data)
    except sysv_ipc.BusyError:
        return None

# ----------------------------
# Shared Memory Functions
# ----------------------------

def init_shared_light_state() -> sysv_ipc.SharedMemory:
    """Initialize and clear the shared memory for traffic light state with default values."""
    shm = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, size=SHM_SIZE)

    # Ensure shared memory has a valid initial state
    shm.attach()
    raw_data = shm.read(SHM_SIZE).rstrip(b'\x00')
    if not raw_data:  # If empty, write an initial valid LightState
        initial_state = LightState(north=1, south=1, east=0, west=0)
        shm.write(pickle.dumps(initial_state))
    shm.detach()

    return shm


def write_light_state(shm: sysv_ipc.SharedMemory, obj: LightState):
    """Write a pickled object to shared memory after clearing it."""
    shm.attach()
    shm.write(b'\x00' * SHM_SIZE)  # Clear memory
    shm.write(pickle.dumps(obj))  # Write object
    shm.detach()

def read_light_state(shm: sysv_ipc.SharedMemory) -> LightState:
    """Read and unpickle an object from shared memory."""
    shm.attach()
    raw_data = shm.read(SHM_SIZE).rstrip(b'\x00')  # Remove null bytes
    shm.detach()
    return pickle.loads(raw_data)