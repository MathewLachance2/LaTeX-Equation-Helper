import sys
import threading
import keyboard
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import Signal, QObject, Slot
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

from gui import OverlayWindow 

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

def create_icon(color):
    """Creates a simple circular icon with the given color."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setBrush(QColor(color))
    painter.setPen(QColor("transparent")) # No border
    painter.drawEllipse(0, 0, 64, 64)
    painter.end()
    return QIcon(pixmap)

class SystemTrayApp(QObject):
    def __init__(self, app, listener, window):
        super().__init__()
        self.app = app
        self.listener = listener
        self.window = window

        # Ensure app doesn't close when window closes
        self.app.setQuitOnLastWindowClosed(False)

        # Create Tray Icon
        self.tray_icon = QSystemTrayIcon()
        self.icon_active = create_icon("#4CAF50") # Green
        self.icon_inactive = create_icon("#F44336") # Red
        
        self.tray_icon.setIcon(self.icon_active)
        self.tray_icon.setVisible(True)
        self.tray_icon.setToolTip("LaTeX Equation Helper")

        # Create Menu
        self.menu = QMenu()
        
        # Actions
        self.toggle_action = self.menu.addAction("Active")
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(True)
        self.toggle_action.triggered.connect(self.toggle_active)
        
        self.menu.addSeparator()
        
        self.quit_action = self.menu.addAction("Quit")
        self.quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(self.menu)

        # Start Listening
        self.listener.start()

    def toggle_active(self):
        if self.toggle_action.isChecked():
            self.listener.start()
            self.tray_icon.setIcon(self.icon_active)
            self.tray_icon.setToolTip("LaTeX Equation Helper (Active)")
        else:
            self.listener.stop()
            self.tray_icon.setIcon(self.icon_inactive)
            self.tray_icon.setToolTip("LaTeX Equation Helper (Inactive)")

    def quit_app(self):
        self.listener.stop()
        self.tray_icon.hide() # Cleanup icon
        self.app.quit()

def main():
    app = QApplication(sys.argv)
    
    print("Equation Tool Started...")
    
    listener = HotkeyListener()
    window = OverlayWindow()
    
    # Connect signal to window show slot
    listener.show_signal.connect(window.activate)

    # Initialize System Tray
    tray = SystemTrayApp(app, listener, window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
