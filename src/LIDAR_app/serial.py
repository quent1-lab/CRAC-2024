#!/usr/bin/python
# -*- coding: latin-1 -*-
add_library('serial')

myPort = None  # Créez une variable globale pour le port série

def setup():
    global myPort
    try:
        # Configuration du port série
        print(Serial.list())
        portIndex = 4
        LF = 10
        print("Connexion à", Serial.list()[portIndex])
        myPort = Serial(this, Serial.list()[portIndex], 256000)
        myPort.bufferUntil(LF)
    except SerialException as e:
        print("Erreur lors de la configuration du port série:", e)
        exit()  # Quitte l'application en cas d'erreur

def draw():
    pass

def serialEvent(evt):
    inString = evt.readString()
    print(inString)

def send_data(data):
    global myPort
    if myPort is not None:
        try:
            myPort.write(data)  # Envoie les données
        except Exception as e:
            print("Erreur lors de l'envoi des données:", e)

def read_data():
    global myPort
    if myPort is not None:
        try:
            while myPort.available() > 0:
                inString = myPort.readStringUntil('\n')  # Lecture des données jusqu'à un saut de ligne
                if inString:
                    inString = inString.strip()  # Supprimer les caractères de nouvelle ligne
                    return inString
        except Exception as e:
            print("Erreur lors de la lecture des données:", e)
    return None

def SerialException():
    pass
