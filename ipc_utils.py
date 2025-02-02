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

    Returns:
        A dictionary mapping each direction ('N', 'S', 'E', 'W') to its MessageQueue.
    """
    queues = {}
    for direction, key in QUEUE_KEYS.items():
        try:
            queues[direction] = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)
        except sysv_ipc.Error as e:
            print(f"[IPC_UTILS] Error creating message queue for {direction}: {e}")
            sys.exit(1)
    return queues

def send_obj_message(queue, obj, msg_type=1):
    """
    Serialize and send an object through the provided SysV IPC MessageQueue.

    Args:
        queue: A sysv_ipc.MessageQueue instance.
        obj: Python object to serialize and send.
        msg_type: The message type (default is 1).
    """
    try:
        data = pickle.dumps(obj)
        queue.send(data, type=msg_type)
    except Exception as e:
        print(f"[IPC_UTILS] Error sending object: {e}")


def receive_obj_message(queue, block=True, msg_type=0):
    """
    Receive and deserialize an object from a SysV IPC MessageQueue.

    Args:
        queue: A sysv_ipc.MessageQueue instance.
        block: If True, block until a message is available; otherwise, return None.
        msg_type: The message type to receive (0 means any type).

    Returns:
        The deserialized Python object if a message is received; otherwise, None.
    """
    try:
        if block:
            message, mtype = queue.receive(type=msg_type)
        else:
            message, mtype = queue.receive(type=msg_type, block=False)  # No timeout

        obj = pickle.loads(message)
        return obj
    except sysv_ipc.BusyError:
        return None
    except Exception as e:
        print(f"[IPC_UTILS] Error receiving message: {e}")
        return None

