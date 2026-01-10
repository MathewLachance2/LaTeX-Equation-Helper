
import sys
import os
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import calculate_safe_position

class MockRect:
    def __init__(self, x, y, w, h):
        self._x = x
        self._y = y
        self._w = w
        self._h = h
    
    def x(self): return self._x
    def y(self): return self._y
    def width(self): return self._w
    def height(self): return self._h

class TestWindowLogic(unittest.TestCase):
    
    def test_center_screen(self):
        # 1920x1080 screen
        screen = MockRect(0, 0, 1920, 1080)
        win_w, win_h = 400, 100
        
        # Cursor at 500, 500 -> Should stay there
        x, y = calculate_safe_position(500, 500, win_w, win_h, screen)
        self.assertEqual(x, 500)
        self.assertEqual(y, 500)

    def test_right_edge_overflow(self):
        screen = MockRect(0, 0, 1920, 1080)
        win_w, win_h = 400, 100
        
        # Cursor at 1900, 500. 1900 + 400 = 2300 > 1920.
        # Should be shifted to 1920 - 400 = 1520.
        x, y = calculate_safe_position(1900, 500, win_w, win_h, screen)
        self.assertEqual(x, 1520)
        self.assertEqual(y, 500)

    def test_bottom_edge_overflow(self):
        screen = MockRect(0, 0, 1920, 1080)
        win_w, win_h = 400, 100
        
        # Cursor at 500, 1050. 1050 + 100 = 1150 > 1080.
        # Should be shifted to 1080 - 100 = 980.
        x, y = calculate_safe_position(500, 1050, win_w, win_h, screen)
        self.assertEqual(x, 500)
        self.assertEqual(y, 980)

    def test_top_left_overflow(self):
        # Multi-monitor setup might have negative coords, but let's assume single primary for now 
        # or simple negative check if screen starts at 0,0
        screen = MockRect(0, 0, 1920, 1080)
        win_w, win_h = 400, 100
        
        # Cursor at -50, -50
        x, y = calculate_safe_position(-50, -50, win_w, win_h, screen)
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)
        
    def test_tuple_geometry(self):
        # Verify it works with simple tuple (x, y, w, h)
        screen_tuple = (0, 0, 800, 600)
        win_w, win_h = 200, 100
        
        x, y = calculate_safe_position(700, 100, win_w, win_h, screen_tuple)
        self.assertEqual(x, 600) # 800 - 200

if __name__ == '__main__':
    unittest.main()
