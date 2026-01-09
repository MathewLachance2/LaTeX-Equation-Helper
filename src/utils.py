
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
                # We have a caret
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
