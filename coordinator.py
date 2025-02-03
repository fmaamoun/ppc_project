import time
import sys
import threading
import os
import signal
from collections import deque

from ipc_utils import receive_obj_message
from common import LightState

# -------------------------------------------------------------------
# Global Variables and Synchronization Primitives
# -------------------------------------------------------------------

# Chaque direction a sa propre file d'attente (FIFO) pour les véhicules normaux en attente.
waiting_vehicles = {
    "N": deque(),
    "S": deque(),
    "E": deque(),
    "W": deque()
}

# Verrou pour synchroniser l'accès à la structure waiting_vehicles.
waiting_lock = threading.Lock()

# Verrou pour garantir un accès exclusif lors de l'envoi d'updates via le socket d'affichage.
display_lock = threading.Lock()

# Événement signalant qu'un changement d'état du feu vient d'avoir lieu.
light_changed_event = threading.Event()


# -------------------------------------------------------------------
# Fonctions Utilitaires
# -------------------------------------------------------------------

def send_update(display_socket, message):
    """
    Envoie un message via le socket TCP.
    Utilise un verrou pour s'assurer qu'un seul thread écrit à la fois.
    """
    try:
        with display_lock:
            display_socket.sendall((message + "\n").encode("utf-8"))
    except Exception as exc:
        print(f"[COORDINATOR] Error sending update: {exc}")


def set_priority_light(direction):
    """
    Retourne un LightState où seule la direction spécifiée est verte.
    """
    if direction == "N":
        return LightState(north=1, south=0, east=0, west=0)
    elif direction == "S":
        return LightState(north=0, south=1, east=0, west=0)
    elif direction == "E":
        return LightState(north=0, south=0, east=1, west=0)
    elif direction == "W":
        return LightState(north=0, south=0, east=0, west=1)
    else:
        # Par défaut : nord/sud vert.
        return LightState(north=1, south=1, east=0, west=0)


def can_vehicle_proceed(vehicle, light_state):
    """
    Pour les véhicules normaux :
      - Si venant du Nord ou du Sud, le feu Nord doit être vert.
      - Si venant de l'Est ou de l'Ouest, le feu Est doit être vert.
    """
    if vehicle.source_road in ["N", "S"]:
        return light_state.north == 1
    else:
        return light_state.east == 1


# -------------------------------------------------------------------
# Fonctions des Threads
# -------------------------------------------------------------------

def process_direction(direction, queue, shared_state, display_socket, lights_pid):
    """
    Thread qui traite les véhicules d'une direction donnée.
      - Pour un véhicule à haute priorité, il attend que le thread monitor indique que le feu est passé en mode priorité,
        puis il envoie une update "PASSES" et signale le rétablissement du mode normal.
      - Pour les véhicules normaux, il vérifie si l'état actuel du feu leur permet de passer ; sinon, ils sont mis en attente.
    """
    while True:
        vehicle = receive_obj_message(queue, block=False)
        if vehicle is None:
            time.sleep(0.1)
            continue

        if vehicle.priority:
            send_update(
                display_socket,
                f"[COORDINATOR] 🚨 Priority Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} detected. Waiting for priority lights..."
            )
            desired_state = set_priority_light(vehicle.source_road)
            # Attend que le thread monitor ait signalé le changement.
            light_changed_event.wait()
            # Polling jusqu'à ce que l'état partagé corresponde à l'état de priorité désiré.
            while True:
                current_state = shared_state.get("state", None)
                if current_state == desired_state:
                    break
                time.sleep(0.05)
            send_update(
                display_socket,
                f"[COORDINATOR] 🚨 Priority Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} PASSES (priority light active)."
            )
            # Une fois le véhicule de priorité passé, on envoie SIGUSR2 au process de gestion des feux pour rétablir le mode normal.
            try:
                os.kill(lights_pid, signal.SIGUSR2)
            except Exception as exc:
                print(f"[COORDINATOR] Error sending SIGUSR2 to lights process: {exc}")
        else:
            current_state = shared_state.get("state", None)
            if can_vehicle_proceed(vehicle, current_state):
                send_update(
                    display_socket,
                    f"[COORDINATOR] ✅ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} PASSES."
                )
            else:
                send_update(
                    display_socket,
                    f"[COORDINATOR] ❌ Vehicle {vehicle.vehicle_id} from {vehicle.source_road} to {vehicle.dest_road} WAITS (red light)."
                )
                # Ajout du véhicule dans la file d'attente de manière FIFO.
                with waiting_lock:
                    waiting_vehicles[direction].append(vehicle)
        time.sleep(0.1)


def monitor_waiting(shared_state, display_socket):
    """
    Thread qui surveille les véhicules en attente.
    Lorsqu'un changement d'état du feu est détecté, il vérifie les véhicules en attente
    en respectant l'ordre FIFO : la première voiture dans la file est la première vérifiée.
    Si elle peut passer, elle est retirée de la file et un message est envoyé.
    Si elle ne peut pas passer, on n'examine pas les suivantes afin de respecter l'ordre.
    NOTE : La notification du changement d'état du feu a été supprimée ici afin d'éviter le doublon.
    """
    last_state = shared_state.get("state", None)
    while True:
        current_state = shared_state.get("state", None)
        if current_state is None:
            sys.exit(1)
        if current_state != last_state:
            last_state = current_state
            with waiting_lock:
                # Pour chaque direction, on vérifie la file d'attente.
                for direction in waiting_vehicles:
                    # Tant qu'il y a au moins un véhicule en attente et que le premier peut passer...
                    while waiting_vehicles[direction]:
                        front_vehicle = waiting_vehicles[direction][0]
                        if can_vehicle_proceed(front_vehicle, current_state):
                            waiting_vehicles[direction].popleft()  # Retirer le premier véhicule
                            send_update(
                                display_socket,
                                f"[COORDINATOR] ✅ Vehicle {front_vehicle.vehicle_id} from {front_vehicle.source_road} to {front_vehicle.dest_road} PASSES (was waiting)."
                            )
                        else:
                            # On ne vérifie pas les suivants pour respecter l'ordre FIFO.
                            break
        time.sleep(0.5)


def lights_monitor_thread(shared_state, display_socket):
    """
    Thread dédié à la surveillance de l'état du feu partagé.
    Il notifie immédiatement tout changement via l'événement light_changed_event.
    """
    last_state = shared_state.get("state", None)
    while True:
        current_state = shared_state.get("state", None)
        if current_state is None:
            time.sleep(0.1)
            continue
        if current_state != last_state:
            send_update(display_socket, f"[COORDINATOR] 🚦 Traffic light changed: {current_state}")
            last_state = current_state
            light_changed_event.set()
            # Fenêtre courte pour laisser le temps aux threads de détecter l'événement.
            time.sleep(0.1)
            light_changed_event.clear()
        time.sleep(0.05)


# -------------------------------------------------------------------
# Main du Coordinator
# -------------------------------------------------------------------

def main(queues, shared_state, display_socket, lights_pid):
    """
    Point d'entrée du process coordinator.
    Il démarre :
      - Un thread par direction pour traiter les véhicules entrants.
      - Un thread monitor_waiting pour vérifier les véhicules en attente.
      - Un lights_monitor_thread pour détecter et notifier immédiatement les changements de feu.
    Le process tourne indéfiniment.
    """
    send_update(display_socket, "[COORDINATOR] Started managing vehicle flow...")
    initial_state = shared_state.get("state", None)
    send_update(display_socket, f"[COORDINATOR] 🚦 Initial traffic light: {initial_state}")

    threads = []

    # Lancement d'un thread par direction.
    for direction in ["N", "S", "E", "W"]:
        t = threading.Thread(
            target=process_direction,
            args=(direction, queues[direction], shared_state, display_socket, lights_pid),
            name=f"Thread-{direction}",
            daemon=True
        )
        t.start()
        threads.append(t)

    # Lancement du thread monitor_waiting.
    t_wait = threading.Thread(
        target=monitor_waiting,
        args=(shared_state, display_socket),
        name="Monitor-Waiting",
        daemon=True
    )
    t_wait.start()
    threads.append(t_wait)

    # Lancement du lights_monitor_thread.
    t_lights = threading.Thread(
        target=lights_monitor_thread,
        args=(shared_state, display_socket),
        name="Lights-Monitor",
        daemon=True
    )
    t_lights.start()
    threads.append(t_lights)

    # Maintenir le process coordinator en vie.
    while True:
        time.sleep(1)
