
import os
import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
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

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "editor.html")
        self.webview.setUrl(QUrl.fromLocalFile(file_path))
        
        self.layout.addWidget(self.webview)
        self.resize(400, 100)

    def activate(self):
        # Move to cursor/caret position
        from utils import get_caret_position
        
        caret_pos = get_caret_position()
        
        if caret_pos:
            self.move(caret_pos[0], caret_pos[1])
        else:
            cursor_pos = QCursor.pos()
            self.move(cursor_pos.x(), cursor_pos.y())
        
        self.show()
        self.raise_()
        self.activateWindow()
        self.webview.setFocus()
        self.webview.page().runJavaScript("if(typeof latexField !== 'undefined') latexField.focus();")
        
        # Clear page state
        self.webview.page().runJavaScript("if(typeof latexField !== 'undefined') latexField.latex('');")

    def submit_equation(self, latex_text):
        from utils import copy_to_clipboard, paste_clipboard

        print(f"Submitting: {latex_text}")
        copy_to_clipboard(latex_text)
        
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
