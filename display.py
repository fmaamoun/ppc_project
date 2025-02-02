# display.py
import sysv_ipc
import sys

DISPLAY_QUEUE_KEY = 0x1111  # La même clé utilisée dans coordinator.py

def main():
    # On essaye de se connecter à la file de messages déjà créée par coordinator
    try:
        display_queue = sysv_ipc.MessageQueue(DISPLAY_QUEUE_KEY)
    except sysv_ipc.ExistentialError:
        print(f"[DISPLAY] Erreur : impossible d'accéder à la file de messages {hex(DISPLAY_QUEUE_KEY)}.")
        sys.exit(1)

    print("[DISPLAY] Connected to display queue. Waiting for updates... (Ctrl+C pour quitter)")

    try:
        while True:
            # On attend un message de type=1 (celui envoyé par coordinator)
            # La méthode receive retourne (message_bytes, msg_type)
            message_bytes, msg_type = display_queue.receive(type=1)
            if message_bytes:
                message_str = message_bytes.decode('utf-8')
                print(message_str)
    except KeyboardInterrupt:
        print("[DISPLAY] Arrêt par l'utilisateur, fermeture...")

    # Éventuellement on peut appeler display_queue.remove() si on veut détruire la queue,
    # mais souvent on laisse coordinator gérer ça (ou la laisser exister).
    # display_queue.remove()

if __name__ == "__main__":
    main()
