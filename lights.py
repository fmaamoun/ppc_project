import time
import signal

from common import LightState, LIGHT_CHANGE_INTERVAL

# Global flags
priority_override = False     # True when a SIGUSR1 is received, meaning "go to priority"
in_priority_mode = False      # True when we are currently in priority mode
just_restored = False         # True when a SIGUSR2 has just been received, forcing a restoration

def handle_priority_signal(signum, frame):
    """
    Sets a flag indicating we should enter priority mode exactly once.
    """
    global priority_override
    priority_override = True

def handle_restore_signal(signum, frame):
    """
    Restores normal mode immediately (SIGUSR2).
    """
    global in_priority_mode, just_restored
    in_priority_mode = False
    just_restored = True

def set_priority_light(direction):
    """
    Returns a LightState where only 'direction' is green.
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
        # Fallback to north/south green
        return LightState(north=1, south=1, east=0, west=0)

def toggle_lights(state: LightState) -> LightState:
    """
    Normal toggle: If N/S is green, switch to E/W; if E/W is green, switch to N/S.
    """
    return LightState(
        north=1 - state.north,
        south=1 - state.south,
        east=1 - state.east,
        west=1 - state.west
    )

def main(shared_state):
    """
    Lights process that:
      - Listens for SIGUSR1 => enter priority mode (once),
      - Listens for SIGUSR2 => restore normal mode immediately,
      - Otherwise toggles lights in normal cycles.

    La boucle principale vérifie toutes les 100ms afin de réagir rapidement aux signaux.
    """
    global priority_override, in_priority_mode, just_restored

    signal.signal(signal.SIGUSR1, handle_priority_signal)
    signal.signal(signal.SIGUSR2, handle_restore_signal)

    # État initial normal : N/S vert, E/W rouge
    state = LightState(north=1, south=1, east=0, west=0)
    shared_state["state"] = state

    step_time = 0.1  # Vérification toutes les 100 ms
    elapsed = 0.0    # Temps écoulé dans l'état normal actuel

    while True:
        # Si nous venons juste de restaurer le mode normal, on remet immédiatement l'état normal.
        if just_restored:
            # Ici, on choisit l'état normal par défaut (celui d'initialisation) :
            state = LightState(north=1, south=1, east=0, west=0)
            shared_state["state"] = state
            elapsed = 0.0
            just_restored = False

        # Si nous ne sommes PAS en mode priorité :
        if not in_priority_mode:
            # Vérifier si un SIGUSR1 a été reçu pour passer en mode priorité.
            if priority_override:
                priority_override = False
                in_priority_mode = True

                # Lecture de la direction désirée depuis shared_state (par défaut "N")
                direction = shared_state.get("priority_direction", "N")
                prio_state = set_priority_light(direction)
                shared_state["state"] = prio_state
            else:
                # Fonctionnement normal : on bascule d'état après LIGHT_CHANGE_INTERVAL
                if elapsed >= LIGHT_CHANGE_INTERVAL:
                    state = toggle_lights(state)
                    shared_state["state"] = state
                    elapsed = 0.0

                time.sleep(step_time)
                elapsed += step_time
        else:
            # En mode priorité, on ne fait rien d'autre que d'attendre le signal de restauration.
            time.sleep(step_time)
