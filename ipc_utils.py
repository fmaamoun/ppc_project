import sys
import pickle
import sysv_ipc


# Define unique keys for each road section's message queue.
QUEUE_KEYS = {
    'N': 0x2000,
    'S': 0x2001,
    'E': 0x2002,
    'W': 0x2003
}

def init_message_queues():
    """
    Initialize message queues for each road section using SysV IPC.
    Returns a dictionary mapping each direction ('N', 'S', 'E', 'W') to its MessageQueue.
    """
    queues = {}
    for direction, key in QUEUE_KEYS.items():
        try:
            queues[direction] = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)
        except sysv_ipc.Error as e:
            print(f"[IPC_UTILS] Error creating message queue for {direction}: {e}")
            sys.exit(1)
    return queues

def send_obj_message(queue, obj):
    """
    Serialize and send an object through the provided SysV IPC MessageQueue.
    """
    try:
        data = pickle.dumps(obj)
        queue.send(data, type=1)
    except Exception as e:
        print(f"[IPC_UTILS] Error sending object: {e}")

def receive_obj_message(queue, block=True):
    """
    Receives an object message from a given queue.
    Returns the deserialized object if the message is successfully received.
    If blocking is disabled and no message is available, returns None.
    """
    try:
        message, mtype = queue.receive(type=0, block=block)
        obj = pickle.loads(message)
        return obj
    except sysv_ipc.BusyError:
        return None
    except Exception as e:
        print(f"[IPC_UTILS] Error receiving message: {e}")
        return None