# Arborescence v0

```
.
├── main.py
├── normal_traffic_gen.py
├── priority_traffic_gen.py
├── coordinator.py
├── lights.py
├── display.py
├── ipc_utils.py
├── common.py
└── README.md
```

- **main.py**  
  Point d’entrée qui lance et arrête proprement tous les processus.  
- **normal_traffic_gen.py**  
  Génère le trafic “normal”.  
- **priority_traffic_gen.py**  
  Génère le trafic “prioritaire” et envoie un signal au process `lights`.  
- **coordinator.py**  
  Gère la logique de passage pour tous les véhicules, interagit avec l’état des feux et lit les messages depuis les files.  
- **lights.py**  
  Gère les états des feux de circulation (partagé en mémoire) et réagit aux signaux pour laisser passer les véhicules prioritaires.  
- **display.py**  
  Affiche l’état du carrefour en temps réel (communication par socket).  
- **ipc_utils.py**  
  Module utilitaire contenant les fonctions d’initialisation et de gestion des files de messages, mémoire partagée, signaux, etc.  
- **common.py**  
  Contient d’éventuelles constantes, énumérations, structures de données partagées (par exemple la définition du format des messages).  
