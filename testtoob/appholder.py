import sys
from PyQt5.QtCore import Qt, QPoint, QUrl  # Import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWebEngineWidgets import QWebEngineView  # Import QWebEngineView
import os
os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'

class TaskbarWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Remove the native title bar
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)  # Allow minimize and maximize buttons
        self.setStyleSheet("background-color: black; border: none;")
        
        # Create a main layout (custom top bar + content area)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to ensure top bar is at the top

        # Create the custom title bar
        title_bar = QWidget()
        title_bar.setAutoFillBackground(True)
        title_bar.setFixedHeight(50)

        # Set the background color of the title bar to black
        palette = title_bar.palette()
        palette.setColor(QPalette.Window, QColor('black'))
        title_bar.setPalette(palette)

        # Title bar layout and widgets
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)  # Remove any spacing in the title bar
        title = QLabel("App Holder Boilerplate")
        title.setStyleSheet("color: white; font-size: 16px; padding-left: 10px;")  # White text

        # Add control buttons to the custom title bar
        close_button = QPushButton("✖")
        close_button.setStyleSheet("background-color: black; color: white; border: none; padding-right: 10px;")
        close_button.clicked.connect(self.close)

        minimize_button = QPushButton("➖")
        minimize_button.setStyleSheet("background-color: black; color: white; border: none;")
        minimize_button.clicked.connect(self.showMinimized)

        maximize_button = QPushButton("⬜")
        maximize_button.setStyleSheet("background-color: black; color: white; border: none;")
        maximize_button.clicked.connect(self.toggle_maximized)

        title_layout.addWidget(title)
        title_layout.addStretch()  # Push buttons to the right
        title_layout.addWidget(minimize_button)
        title_layout.addWidget(maximize_button)
        title_layout.addWidget(close_button)

        title_bar.setLayout(title_layout)

        # Add title bar to the main layout
        layout.addWidget(title_bar)

        # WebEngineView setup
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://g7iq8yzca8gn.share.zrok.io"))  # Convert the URL string to QUrl

        # Add the browser to the main layout
        layout.addWidget(self.browser)

        # Set the main layout to a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set initial window size
        self.resize(800, 600)

        # Window dragging (override mousePressEvent and mouseMoveEvent on title bar)
        self.old_pos = None
        title_bar.mousePressEvent = self.title_mouse_press_event
        title_bar.mouseMoveEvent = self.title_mouse_move_event

    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # Custom drag logic
    def title_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton and not self.isMaximized():
            self.old_pos = event.globalPos()

    def title_mouse_move_event(self, event):
        if self.old_pos and event.buttons() & Qt.LeftButton and not self.isMaximized():
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Initialize and show the window
    window = TaskbarWindow()
    window.show()  # Use show() instead of showMaximized() for custom sizing
    sys.exit(app.exec_())
