import sys
import threading
import keyboard
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Signal, QObject, QSharedMemory

from gui import OverlayWindow, ControlWindow

class HotkeyListener(QObject):
    show_signal = Signal()

    def __init__(self):
        super().__init__()
        self.hook = None
        self.is_active = False

    def start(self):
        if not self.is_active:
            # TODO: Make hotkey configurable? For now hardcoded per plan.
            self.hook = keyboard.add_hotkey('ctrl+alt+e', self.on_hotkey)
            self.is_active = True
            print("Hotkey Listener Started")

    def stop(self):
        if self.is_active and self.hook:
            keyboard.remove_hotkey(self.hook)
            self.hook = None
            self.is_active = False
            print("Hotkey Listener Stopped")

    def on_hotkey(self):
        print("Hotkey triggered!")
        self.show_signal.emit()

def main():
    # Enable High DPI Scaling
    from PySide6.QtCore import Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    
    # Single Instance Check
    shared_memory = QSharedMemory("LaTeXEquationHelperInstanceID")
    if not shared_memory.create(1):
        # Already exists
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Already Running")
        msg.setText("LaTeX Equation Helper is already running.")
        msg.exec()
        sys.exit(0)
    
    print("Equation Tool Started...")
    
    # Create windows
    listener = HotkeyListener()
    overlay_window = OverlayWindow()
    control_window = ControlWindow()
    
    # Connect signals
    listener.show_signal.connect(overlay_window.activate)
    
    # Start Listening immediately
    listener.start()
    
    # Show Control Window
    control_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
