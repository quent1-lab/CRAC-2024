
# Le LIDAR

Ce projet à été créer afin de répondre au besoin lié à la coupe de robotique de France 2024. Avec pour thème : Farming Mars

## Structure du projet

Le projet est organisé en plusieurs dossiers :

- `Lidar` : Contient le code python principal pour le fonctionnement du LIDAR. 
- `Lidarobot` : Contient le code C++ de la base roulante
- `PCB_CAN` : Contient le projet de la carte PCB CAN
- `Rapport S3` : Contient le rapport de projet
- `WIFI` : Contient des scripts simple pour tester la communication par socket et le principe du multitâche
- `CAN` : Contient un scripts simple pour tester la communication CAN
- `3D démonstrateur` : Contient les fichers STL et les GCODE correspondant à l'imprimante Ender-3 v2

## Installation

Vous pouvez cloner le projet via git en utilisant la commande suivante :

```bash
  git clone https://github.com/quent1-lab/CRAC-2024
```

Ensuite, naviguez dans le dossier du projet et installez les dépendances nécessaires avec pip :
```bash
  pip install -r requirements.txt
```
    
## Déploiement

Le fonctionnement de cette version du code nécessite un ordinateur connecté en série avec la base roulante, et le lidar connecté à la Raspberry Pi. 
Les deux appareils doivent être connecté au même réseau WIFI (Attention à bien modifier l'adresse IP du serveur sur le fichier `lidar_Raso.py`).

Dans l'ordre, il faut lancer :
 - le programme python `LidarScan.py` sur l'ordinateur (car c'est le serveur)
```bash
  python Lidar/LidarScan.py
```
 - Le programme python `lidar_Raso.py` sur la Raspberry Pi
```bash
  python Lidar/lidar_Rasp.py
```

## Authors

- [@quent1-lab](https://github.com/quent1-lab)

