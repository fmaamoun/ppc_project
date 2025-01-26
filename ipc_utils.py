import sysv_ipc
import pickle

# Define keys for 4 message queues (N, S, E, W)
KEY_N = 1
KEY_S = 2
KEY_E = 3
KEY_W = 4

# Key for the shared memory
# SHM_KEY = 5

def init_message_queues():
    """
    Initializes and returns a dictionary of SysV MessageQueue for N, S, E, W.
    """
    return {
        "N": sysv_ipc.MessageQueue(KEY_N, sysv_ipc.IPC_CREAT),
        "S": sysv_ipc.MessageQueue(KEY_S, sysv_ipc.IPC_CREAT),
        "E": sysv_ipc.MessageQueue(KEY_E, sysv_ipc.IPC_CREAT),
        "W": sysv_ipc.MessageQueue(KEY_W, sysv_ipc.IPC_CREAT)
    }

def send_obj_message(queue, obj):
    """
    Sends the object in the SysV message queue.
    """
    queue.send(pickle.dumps(obj), type=1)

def receive_obj_message(queue, block=False):
    """
    Reads a message from the SysV message queue,
    deserializes it using pickle, and returns a VehicleMessage object.
    """
    try:
        data, _type = queue.receive(block=block)
        obj = pickle.loads(data)
        return obj
    except sysv_ipc.BusyError:
        return None