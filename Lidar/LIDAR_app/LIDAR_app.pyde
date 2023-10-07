from rplidar import RPLidar

# Spécifiez le port série que vous utilisez pour le LiDAR S1 (par exemple, '/dev/ttyUSB0' sur Linux)
port = 'COM8'  # Changez cela en fonction de votre configuration

# Créez une instance du LiDAR S1
lidar = RPLidar(port)

def setup():
    size(480, 120)

try:
    # Commencez la collecte de données
    lidar.connect()
    println("Lidar connectée")

    # Lisez et affichez les données
    for scan in lidar.iter_scans():
        for (_, angle, distance) in scan:
            print("Angle: ")
            print(String(angle))
            print("Distance:  , ") 
            println(String(distance))


except KeyboardInterrupt:
    pass

finally:
    # Arrêtez la rotation et déconnectez le LiDAR
    lidar.stop_motor()
    lidar.disconnect()
