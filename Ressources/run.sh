#!/bin/bash

# Vérifier les processus en cours et tuer les processus Python
echo "Vérification des processus en cours..."
ps aux | grep python | grep -v grep | awk '{print $2}' | xargs kill -9
echo "Processus Python terminés."

# Chemin du répertoire git
GIT_DIR="/home/crac2/CRAC-2024"

# Vérifier si le répertoire git existe
if [ -d "$GIT_DIR" ]; then
    # Se déplacer dans le répertoire git
    cd "$GIT_DIR" || exit
    # Effectuer un git pull
    git reset --hard
    git pull origin main

else
    echo "Le répertoire git n'existe pas : $GIT_DIR"
    exit 1
fi

# Exécuter une commande spécifique
python3 src/BusCOM.py & python3 src/CAN.py & python3 src/IHM_Robot.py &

exit 0
