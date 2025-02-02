# coordinator.py
import time
import multiprocessing
import sys
import sysv_ipc

# On importe les fonctions/méthodes existantes
# - init_message_queues : pour initialiser les queues des véhicules
# - receive_obj_message : pour lire un véhicule depuis la queue appropriée
# - init_shared_light_state : pour initialiser la mémoire partagée (état des feux)
# - read_light_state : pour lire l'état des feux depuis la mémoire partagée
from ipc_utils import (
    init_message_queues,
    receive_obj_message,
    init_shared_light_state,
    read_light_state
)
from normal_traffic_gen import main as normal_traffic_main
from lights import main as lights_main

# Définissons une clé pour la file de messages "display"
DISPLAY_QUEUE_KEY = 0x1111  # À réutiliser dans display.py

def can_vehicle_proceed(vehicle, light_state):
    """
    Détermine si un véhicule peut passer (feu vert) ou doit attendre (feu rouge).
    """
    if vehicle.source_road in ["N", "S"]:
        return light_state.north == 1  # Feu Nord-Sud doit être vert
    else:
        return light_state.east == 1   # Feu Est-Ouest doit être vert

def process_vehicles(queues, shm, display_queue):
    """
    Gère le flux de véhicules :
      - lit l'état du feu,
      - traite les véhicules en attente et nouveaux véhicules,
      - envoie des messages dans display_queue pour l'affichage.
    """

    def send_update(msg):
        """
        Envoie un message dans la file display_queue (type=1).
        On encode la chaîne en UTF-8.
        """
        try:
            display_queue.send(msg.encode('utf-8'), type=1)
        except sysv_ipc.ExistentialError:
            print("[COORDINATOR] Erreur: la file d'affichage n'existe plus.")
            sys.exit(1)

    send_update("[COORDINATOR] Started managing vehicle flow...")

    waiting_vehicles = []  # Liste des véhicules en attente
    last_light_state = read_light_state(shm)

    while True:
        current_light_state = read_light_state(shm)

        # Vérifier si le feu a changé
        if current_light_state != last_light_state:
            send_update(f"[COORDINATOR] 🚦 Light changed: {current_light_state}")
            last_light_state = current_light_state

        # 1. Gérer les véhicules déjà en attente
        new_waiting_vehicles = []
        for vehicle in waiting_vehicles:
            if can_vehicle_proceed(vehicle, current_light_state):
                send_update(
                    f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} "
                    f"to {vehicle.dest_road} PASSES (Previously Waiting)."
                )
            else:
                new_waiting_vehicles.append(vehicle)
        waiting_vehicles = new_waiting_vehicles

        # 2. Récupérer les nouveaux véhicules des 4 directions
        for direction in ["N", "S", "E", "W"]:
            vehicle = receive_obj_message(queues[direction], block=False)
            if vehicle:
                if can_vehicle_proceed(vehicle, current_light_state):
                    send_update(
                        f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} "
                        f"to {vehicle.dest_road} PASSES."
                    )
                else:
                    send_update(
                        f"[COORDINATOR] ❌ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} "
                        f"to {vehicle.dest_road} WAITS (Red Light)."
                    )
                    waiting_vehicles.append(vehicle)

        time.sleep(1)  # Petite pause pour éviter de tourner trop vite

def main():
    """
    Point d'entrée du coordinator :
      - on initialise tout,
      - on lance les processus lights + traffic,
      - on rentre dans la boucle de process_vehicles.
    """
    # 1. Création / récupération des queues pour le trafic
    queues = init_message_queues()

    # 2. Mémoire partagée pour les feux
    shm = init_shared_light_state()

    # 3. Création (ou récupération) de la queue d'affichage
    #    IPC_CREAT : crée la queue si elle n'existe pas, sinon l'ouvre
    #    On évite IPC_EXCL pour ne pas bloquer si la queue existe déjà
    try:
        display_queue = sysv_ipc.MessageQueue(DISPLAY_QUEUE_KEY, sysv_ipc.IPC_CREAT)
    except sysv_ipc.ExistentialError:
        print(f"[COORDINATOR] Impossible de créer/ouvrir la file de messages {hex(DISPLAY_QUEUE_KEY)}")
        sys.exit(1)

    # 4. Lancement du processus de gestion des feux
    lights_process = multiprocessing.Process(target=lights_main)
    lights_process.start()

    # 5. Attendre un peu pour s'assurer que lights_main ait bien initialisé la mémoire
    time.sleep(1)

    # 6. Lancement du processus de génération de trafic
    normal_process = multiprocessing.Process(target=normal_traffic_main, args=(queues,))
    normal_process.start()

    # 7. On démarre la boucle principale qui gère les véhicules
    process_vehicles(queues, shm, display_queue)

if __name__ == "__main__":
    main()
