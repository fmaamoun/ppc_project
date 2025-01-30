import multiprocessing
import sysv_ipc
from ipc_utils import init_shared_light_state, read_light_state
from lights import main as light_main

SEM_KEY = 6  # Clé de la sémaphore

def wait_for_light_update(shm, sem):
    """
    Attend un signal de mise à jour et lit l'état des feux.
    """
    while True:
        sem.acquire()  # Bloque jusqu'à une mise à jour
        state = read_light_state(shm)
        print(f"[TEST] Light State Updated: {state}")

def main():
    # Initialisation mémoire partagée et sémaphore
    shm = init_shared_light_state()
    sem = sysv_ipc.Semaphore(SEM_KEY, sysv_ipc.IPC_CREAT)

    # Démarre le processus des feux de circulation
    light_process = multiprocessing.Process(target=light_main)
    light_process.start()

    # Attend et affiche chaque mise à jour des feux
    wait_for_light_update(shm, sem)

if __name__ == "__main__":
    main()
