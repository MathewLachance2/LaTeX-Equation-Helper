# LaTeX Equation Helper

A robust, "Word-like" desktop equation editor that allows you to visually edit mathematical formulas and automatically copies the resulting LaTeX code to your clipboard.

![Icon](Queens%20LaTeX%20Tool-min.ico)

## Features

-   **Visual Editing**: Uses [MathQuill](http://mathquill.com/) to provide a WYSIWYG (What You See Is What You Get) interface. You see formattted math (fractions, roots, exponents) while you type, not raw code.
-   **Global Hotkey**: Press **`Ctrl + Alt + E`** anywhere in Windows to summon the editor instantly at your cursor position.
-   **Smart Positioning**: The window attempts to appear right next to your text cursor (caret). If no text field is active, it appears at your mouse cursor.
-   **Immediate Output**: Pressing **Enter** in the editor validates the equation and copies the LaTeX string to your clipboard, ready to paste.
-   **Standardized**: Produces clean, compatible LaTeX code.
-   **Portable**: Distributed as a single, standalone executable file. No Python installation required.

## How to Run

1.  Navigate to the `dist` folder.
2.  Double-click **`LaTeXHelper.exe`**.
3.  A small "Control Window" will appear, indicating the app is running.
    *   *Note*: The app enforces a "Single Instance" rule. If you try to run it twice, it will warn you.
4.  Click into any text field (Word, Browser, Notepad, etc.).
5.  Press **`Ctrl + Alt + E`**.
6.  Type your equation.
7.  Press **Enter** to finish and copy to clipboard.
8.  To quit, simply close the "Control Window".

## How it Works (Technical Overview)

The application is built using **Python 3.14** and **PySide6 (Qt for Python)**. It bridges the gap between a desktop application and a web-based math editor.

### Core Components

*   **`src/main.py`**: The entry point.
    *   **Single Instance Check**: Uses `QSharedMemory` to ensure only one copy of the app runs at a time.
    *   **High DPI Support**: specific Qt attributes are set to ensure the interface looks crisp on 4K monitors and laptops with scaling (125%, 150%).
    *   **Hotkey Listener**: Uses the `keyboard` library to listen for `Ctrl+Alt+E` globally.

*   **`src/gui.py`**: The heart of the user interface.
    *   **`OverlayWindow`**: A **frameless, transparent** window. It hosts a `QWebEngineView` (a Chromium-based browser widget) to display the HTML editor. It handles the logic for appearing/disappearing and "following" the user's cursor.
    *   **`ControlWindow`**: A standard window that provides user feedback (Run status) and a clean exit point.
    *   **`Backend`**: A `QObject` that sets up a `QWebChannel`. This allows Python to talk to JavaScript and vice-versa (e.g., JS tells Python "User pressed Enter with this equation").

*   **`src/editor.html` & `src/lib/`**: The web frontend.
    *   Contains the **MathQuill** library (CSS/JS).
    *   Provides the input field that interprets keystrokes (like typing `/` for fraction, `sqrt` for root) and renders them visually.

*   **`src/utils.py`**: Windows integration.
    *   **Caret Detection**: Uses the Windows C API (`user32.dll`) via `ctypes` to calculate the exact `x,y` coordinates of the blinking text cursor. This allows the overlay to spawn precisely where you are typing.
    *   **Clipboard**: Handles copying the final string to the system clipboard.

### Build System

The project is packaged using **PyInstaller**.
*   **Command**: `pyinstaller --onefile --windowed ...`
*   **Result**: A monolithic `.exe` file that bundles the Python interpreter, Qt libraries, and all project assets (HTML/CSS/Fonts) into a temporary filesystem (`_MEIPASS`), allowing it to run on any Windows machine.

### Known Problems
