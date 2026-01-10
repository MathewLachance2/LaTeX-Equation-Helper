
import subprocess
import ctypes
from ctypes import windll, byref, Structure, c_long, c_ulong, c_void_p

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class GUITHREADINFO(Structure):
    _fields_ = [
        ("cbSize", c_ulong),
        ("flags", c_ulong),
        ("hwndActive", c_void_p),
        ("hwndFocus", c_void_p),
        ("hwndCapture", c_void_p),
        ("hwndMenuOwner", c_void_p),
        ("hwndMoveSize", c_void_p),
        ("hwndCaret", c_void_p),
        ("rcCaret", c_long * 4) # RECT
    ]

def get_caret_position():
    """
    Tries to get the caret position from the foreground window.
    Returns (x, y) or None.
    """
    try:
        user32 = windll.user32
        
        # Get foreground window
        hwnd = user32.GetForegroundWindow()
        
        # Get thread ID of the foreground window
        tid = user32.GetWindowThreadProcessId(hwnd, None)
        
        # Get GUI thread info
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        
        if user32.GetGUIThreadInfo(tid, byref(gui_info)):
            if gui_info.hwndCaret:
                # Check for "Ghost" carets (0 width/height often implies hidden/fake)
                width = gui_info.rcCaret[2] - gui_info.rcCaret[0]
                height = gui_info.rcCaret[3] - gui_info.rcCaret[1]
                
                if width <= 0 or height <= 0:
                    return None

                # We have a valid caret
                point = POINT(gui_info.rcCaret[0], gui_info.rcCaret[1])
                user32.ClientToScreen(gui_info.hwndCaret, byref(point))
                return (point.x, point.y)
    except Exception as e:
        print(f"Error getting caret: {e}")
    
    return None

def copy_to_clipboard(text):
    import pyperclip
    pyperclip.copy(text)

def paste_clipboard():
    import keyboard
    # Simulate ctrl+v
    keyboard.send('ctrl+v')

def calculate_safe_position(target_x, target_y, win_width, win_height, screen_geo):
    """
    Calculates a safe (x, y) position for the window ensuring it stays within screen bounds.
    
    Args:
        target_x (int): Desired X position (usually cursor X).
        target_y (int): Desired Y position (usually cursor Y).
        win_width (int): Window width.
        win_height (int): Window height.
        screen_geo (tuple or generic object): (x, y, width, height) of the available screen area. 
                                              Can be a PySide6 QRect or a simple tuple/object with these attributes.
    
    Returns:
        (x, y): Adjusted coordinates.
    """
    # handle both dict/object/tuple for screen_geo for flexibility in testing
    if hasattr(screen_geo, 'x'):
        s_x, s_y, s_w, s_h = screen_geo.x(), screen_geo.y(), screen_geo.width(), screen_geo.height()
    else:
        s_x, s_y, s_w, s_h = screen_geo
        
    final_x = target_x
    final_y = target_y
    
    # Right edge check
    if final_x + win_width > s_x + s_w:
        final_x = (s_x + s_w) - win_width
        
    # Bottom edge check
    if final_y + win_height > s_y + s_h:
        # Try to position it above the cursor if it hits bottom
        # Assuming target_y was the bottom of cursor, maybe move it up by height + buffer?
        # For simple clamping:
        final_y = (s_y + s_h) - win_height

    # Left edge check (must be after right check to prioritize left visibility if window is huge)
    if final_x < s_x:
        final_x = s_x
        
    # Top edge check
    if final_y < s_y:
        final_y = s_y
        
    return int(final_x), int(final_y)

def validate_latex(latex: str) -> str:
    """
    Validates and cleans LaTeX. 
    1. Checks for balanced braces.
    2. Strips whitespace.
    
    Returns the cleaned latex if valid, else raises ValueError (or returns original if we want to be permissive).
    For this tool, we will return the cleaned string, but warn if unbalanced.
    """
    if not latex:
        return ""
        
    cleaned = latex.strip()
    
    # Check braces
    balance = 0
    for char in cleaned:
        if char == '{':
            balance += 1
        elif char == '}':
            balance -= 1
            if balance < 0:
                print(f"Warning: LaTeX has unbalanced closing brace: {cleaned}")
                # We could try to fix it, but MathQuill usually prevents this.
                break
    
    if balance > 0:
        print(f"Warning: LaTeX has {balance} unclosed braces: {cleaned}")
        # Append missing braces?
        cleaned += '}' * balance
        
    return cleaned
