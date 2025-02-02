import socket
from common import DISPLAY_HOST, DISPLAY_PORT

def main():
    """
    Entry point for the display process.

    Sets up a TCP server on DISPLAY_HOST:DISPLAY_PORT and prints incoming messages.
    """
    # Create a TCP socket server.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((DISPLAY_HOST, DISPLAY_PORT))
    server_socket.listen(1)
    print(f"[DISPLAY] Server listening on {DISPLAY_HOST}:{DISPLAY_PORT}. Waiting for connection...")

    conn, addr = server_socket.accept()
    print(f"[DISPLAY] Connection established with {addr}.")

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break  # Connection closed
            messages = data.decode('utf-8').strip().split("\n")
            for msg in messages:
                if msg:
                    print(msg)
    except KeyboardInterrupt:
        print("[DISPLAY] Shutting down display server.")
    except Exception as e:
        print(f"[DISPLAY] Error: {e}")
    finally:
        conn.close()
        server_socket.close()