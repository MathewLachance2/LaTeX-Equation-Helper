import os
import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, Slot, QUrl, QObject
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel

class Backend(QObject):
    submitSignal = Signal(str)
    cancelSignal = Signal()

    @Slot(str)
    def submit_latex(self, latex):
        print(f"Received LaTeX: {latex}")
        self.submitSignal.emit(latex)

    @Slot()
    def cancel(self):
        print("Cancelled")
        self.cancelSignal.emit()

class ControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaTeX Helper Control")
        # Prevent resizing by setting fixed size
        self.setFixedSize(300, 150)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status Label
        self.status_label = QLabel("LaTeX Helper is Running")
        self.status_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Instruction Label
        self.instr_label = QLabel("Press Ctrl + Alt + E to open editor")
        self.instr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.instr_label)
        
        # Quit Information
        self.quit_info = QLabel("Close this window to quit application")
        self.quit_info.setStyleSheet("color: gray; font-size: 10px;")
        self.quit_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.quit_info)
        
    def closeEvent(self, event):
        # Quit the entire application when this window is closed
        QGuiApplication.instance().quit()

class DragHandle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(200, 200, 200, 0.5); border-top-left-radius: 8px; border-top-right-radius: 8px;")
        self.setFixedHeight(24)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        title = QLabel("LaTeX Helper")
        title.setStyleSheet("color: black; font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: black; border: none; font-weight: bold; }
            QPushButton:hover { color: red; }
        """)
        close_btn.clicked.connect(self.close_window)
        layout.addWidget(close_btn)

    def close_window(self):
        if self.window():
            self.window().hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window().oldPos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            # check if oldPos exists on window, though it should since we init it
            if hasattr(self.window(), 'oldPos'):
                delta = event.globalPosition().toPoint() - self.window().oldPos
                self.window().move(self.window().x() + delta.x(), self.window().y() + delta.y())
                self.window().oldPos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

class GlobalKeyFilter(QObject):
    def __init__(self, target_window):
        super().__init__()
        self.target_window = target_window

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                print("Global Escape Detected")
                self.target_window.hide()
                return True
        return super().eventFilter(obj, event)

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Install global key filter
        self.key_filter = GlobalKeyFilter(self)
        self.installEventFilter(self.key_filter)
        
        # Transparent background for the window
        self.setStyleSheet("background: transparent;")
        
        # for drag logic
        self.oldPos = None

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Drag Handle
        self.drag_handle = DragHandle(self)
        self.layout.addWidget(self.drag_handle)
        
        # Web Engine View
        self.webview = QWebEngineView()
        self.webview.setAttribute(Qt.WA_TranslucentBackground)
        self.webview.page().setBackgroundColor(Qt.transparent)
        
        # Configure Settings
        settings = self.webview.settings()
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        # settings.setAttribute(settings.WebAttribute.WebSecurityEnabled, False) # Uncomment if still blocked
        
        # Setup WebChannel
        self.channel = QWebChannel()
        self.backend = Backend()
        self.backend.submitSignal.connect(self.submit_equation)
        self.backend.cancelSignal.connect(self.hide)
        self.channel.registerObject("backend", self.backend)
        self.webview.page().setWebChannel(self.channel)
        
        # Install key filter on webview to intercept Escape
        self.webview.installEventFilter(self.key_filter)
        if self.webview.focusProxy():
            self.webview.focusProxy().installEventFilter(self.key_filter)
        
        # Load local HTML
        # Load local HTML
        if hasattr(sys, '_MEIPASS'):
            file_path = os.path.join(sys._MEIPASS, "editor.html")
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, "editor.html")
        self.webview.setUrl(QUrl.fromLocalFile(file_path))
        
        self.layout.addWidget(self.webview)
        self.resize(400, 100)

    def activate(self):
        # Fix: Prevent multiple activations if already visible
        if self.isVisible():
            print("Overlay already visible, ignoring activation.")
            return

        # Move to cursor/caret position
        from utils import get_caret_position, calculate_safe_position
        
        caret_pos = get_caret_position()
        
        target_x = 0
        target_y = 0
        
        if caret_pos:
            target_x, target_y = caret_pos
        else:
            cursor_pos = QCursor.pos()
            target_x, target_y = cursor_pos.x(), cursor_pos.y()
            
        # Get screen geometry for the target point
        from PySide6.QtCore import QPoint
        # Use target_x/target_y (Physical) to find the screen
        # Note: screenAt expects Global Logical coords, but usually Physical works okay for finding WHICH screen 
        # if they aren't wildly different, or we can use QCursor.pos which is logical.
        # Let's try finding the screen first.
        screen = QGuiApplication.screenAt(QPoint(target_x, target_y)) 
        
        if not screen:
            screen = QGuiApplication.screenAt(QCursor.pos())

        if not screen:
            screen = QGuiApplication.primaryScreen()

        # CONVERT PHYSICAL TO LOGICAL
        # Windows API (utils.py) returns Physical pixels. Qt expects Logical pixels.
        if caret_pos and screen: 
            dpr = screen.devicePixelRatio()
            if dpr > 1.0:
                print(f"High DPI Detected (Scale: {dpr}). Converting {target_x},{target_y}...")
                target_x = int(target_x / dpr)
                target_y = int(target_y / dpr)
                print(f"New Logical Coords: {target_x},{target_y}")
            
        avail_geo = screen.availableGeometry()
        
        # Calculate safe position
        final_x, final_y = calculate_safe_position(
            target_x, target_y, 
            self.width(), self.height(), 
            avail_geo
        )
        
        self.move(final_x, final_y)
        
        self.show()
        self.raise_()
        self.activateWindow()
        self.webview.setFocus()
        self.webview.page().runJavaScript("if(typeof latexField !== 'undefined') latexField.focus();")
        
        # Clear page state
        self.webview.page().runJavaScript("if(typeof latexField !== 'undefined') latexField.latex('');")

    def submit_equation(self, latex_text):
        from utils import copy_to_clipboard, paste_clipboard, validate_latex

        print(f"Submitting: {latex_text}")
        
        # Validate/Clean
        cleaned_latex = validate_latex(latex_text)
        
        copy_to_clipboard(cleaned_latex)
        
        self.hide()
        # Small delay to allow window switch
        import time
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, paste_clipboard)
    
    # Must keep reference to backend else it gets GC'd and QWebChannel fails silently
    # backend is already self.backend

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
