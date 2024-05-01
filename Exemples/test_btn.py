import time
import gpiozero

button = gpiozero.Button(16, pull_up=True)

if __name__ == '__main__':
    while True:
        if button.is_pressed:
            print("Button is pressed")
        else:
            print("Button is not pressed")
        time.sleep(0.5)
