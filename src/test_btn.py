import RPi.GPIO as GPIO
import time

# Utilisez la numérotation des broches du BCM
GPIO.setmode(GPIO.BCM)

# Définissez le pin 18 comme une entrée et activez la résistance de pull-up interne
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    # Si le bouton est appuyé (c'est-à-dire que l'entrée est faible)
    if GPIO.input(16) == GPIO.LOW:
        print("Bouton appuyé!")
        time.sleep(0.2)  # Debounce time

# N'oubliez pas de nettoyer à la fin de votre script
GPIO.cleanup()