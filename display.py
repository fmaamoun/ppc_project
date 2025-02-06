import socket
import signal
import sys
from common import DISPLAY_HOST, DISPLAY_PORT

# Global variable to hold the server socket
server_socket = None
conn = None

# Utility function
def handle_shutdown(signum, frame):
    """Handles process termination signals to clean up sockets."""
    global server_socket, conn

    if conn:
        conn.close()
        print("[DISPLAY] Connection closed.")
    if server_socket:
        server_socket.close()
        print("[DISPLAY] Server socket closed.")

    sys.exit(0)  # Ensure process exits properly

# Server socket
def main():
    """
    Entry point for the display process.
    Sets up a TCP server on DISPLAY_HOST:DISPLAY_PORT and prints incoming messages.
    Ensures the socket is properly closed on shutdown.
    """
    global server_socket, conn

    # Register signal handlers for graceful termination
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Create a TCP socket server.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((DISPLAY_HOST, DISPLAY_PORT))
    server_socket.listen(1)
    print(f"[DISPLAY] Server listening on {DISPLAY_HOST}:{DISPLAY_PORT}. Waiting for connection...")

    try:
        # Wait for connection
        conn, addr = server_socket.accept()
        print(f"[DISPLAY] Connection established with {addr}.")

        # Handle connection
        while True:
            data = conn.recv(1024)
            if not data:
                break  # Connection closed by client
            messages = data.decode('utf-8').strip().split("\n")
            for msg in messages:
                if msg:
                    print(msg)

    except Exception as e:
        print(f"[DISPLAY] Error: {e}")
