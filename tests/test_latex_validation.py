
import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import validate_latex

class TestLaTeXValidation(unittest.TestCase):
    def test_basic_valid(self):
        self.assertEqual(validate_latex(r"\alpha"), r"\alpha")
        self.assertEqual(validate_latex(r"\frac{1}{2}"), r"\frac{1}{2}")
    
    def test_whitespace(self):
        self.assertEqual(validate_latex("  x + y  "), "x + y")
    
    def test_unbalanced_braces_missing_closing(self):
        # Should append '}'
        self.assertEqual(validate_latex(r"\frac{1}{2"), r"\frac{1}{2}")
        
    def test_unbalanced_braces_extra_closing(self):
        # Should warn but keep as is (since negative balance logic in our code just breaks loop)
        # Actually logic says: if balance < 0: break. So it stops checking.
        # But it returns 'cleaned'.
        self.assertEqual(validate_latex(r"x}"), r"x}")

if __name__ == '__main__':
    unittest.main()
