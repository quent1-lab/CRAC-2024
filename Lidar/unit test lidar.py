import unittest
import LidarScan

class TestLidarScan(unittest.TestCase):
    
    def test_taille_terrain(self):
        self.assertEqual(LidarScan.TAILLE_TERRAIN, (3000, 2000))
        
    def test_taille_fenetre(self):
        self.assertEqual(LidarScan.TAILLE_FENETRE, (900, 600))
        
    def test_bordure(self):
        self.assertEqual(LidarScan.BORDURE, 100)
        
    def test_x_depart(self):
        self.assertEqual(LidarScan.X_Depart, 450)
        
    def test_y_depart(self):
        self.assertEqual(LidarScan.Y_Depart, 300)
        
    def test_angle_robot(self):
        self.assertEqual(LidarScan.angle_Robot, 0)
        
    def test_color(self):
        self.assertEqual(LidarScan.color, (255, 0, 0))
        
if __name__ == '__main__':
    unittest.main()