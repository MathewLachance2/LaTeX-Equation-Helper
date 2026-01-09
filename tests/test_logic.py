
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from converter import COMMAND_MAP, convert_to_latex, get_replacement, check_heuristic_replacements

def test_replacements():
    assert get_replacement(r'\alpha') == 'α'
    assert get_replacement(r'\Delta') == 'Δ'
    assert get_replacement(r'\invalid') is None

def test_heuristics():
    assert check_heuristic_replacements('1/2') == r'\frac{1}{2}'
    assert check_heuristic_replacements('a/b') == r'\frac{a}{b}'
    assert check_heuristic_replacements('1/2/3') is None # Only simple fractions for now
    assert check_heuristic_replacements(r'\alpha/b') is None # Avoid backslashes

def test_conversion():
    # Test Mixed content
    mixed = "α + β"
    latex = convert_to_latex(mixed)
    assert latex == r'\alpha + \beta'
    
    # Test plain text
    assert convert_to_latex("Hello") == "Hello"
    
    # Test already latex? (Ideally shouldn't happen if input is controlled, but good to know)
    # Our converter maps unicode to keys. '\' char stays '\'.
    assert convert_to_latex(r'\alpha') == r'\alpha' 
    # If user types "\alpha" -> space -> "α", then submits, we get "\alpha".
    # If user types "\alpha" without space, it stays "\alpha". 
    # Our converter logic: iterate chars. if char in UNICODE_MAP, swap.
    # So "\alpha" (text) becomes "\alpha" (latex) because '\', 'a', 'l'... are not in map.
    # Wait, check logic.
    pass

if __name__ == "__main__":
    test_replacements()
    test_heuristics()
    test_conversion()
    print("Tests passed!")
