
# Le LIDAR

Ce projet à été créer afin de répondre au besoin lié à la coupe de robotique de France 2024. Avec pour thème : Farming Mars

## Structure du projet

Le projet est organisé en plusieurs dossiers :

- `Lidar` : Contient le code principal pour le fonctionnement du LIDAR. Le fichier `LidarScan.py` est le point d'entrée du programme.
- `Tests` : Contient des scripts de test pour vérifier le bon fonctionnement du code.
- `Data` : Contient les données générées par le LIDAR.

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
Les deux appareils doivent être connecté au même réseau WIFI (Attention à bien modifier l'adresse IP du serveur sur le fichier lidar_Raso.py).

Dans l'ordre, il faut lancer :
 - le programme python LidarScan.py sur l'ordinateur (car c'est le serveur)
```bash
  python Lidar/LidarScan.py
```
 - Le programme python lidar_Rasp.py sur la Raspberry Pi
```bash
  python Lidar/lidar_Rasp.py
```

## Authors

- [@quent1-lab](https://github.com/quent1-lab)

