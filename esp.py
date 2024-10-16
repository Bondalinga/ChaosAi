from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QTimer
import sys
import threading

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Overlay")
        self.setGeometry(0, 0, QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height())
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.showFullScreen()
        self.bboxes = []

        # Update overlay periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # Update every 50 ms

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(52, 174, 235))

        # Draw bounding boxes if available
        if self.bboxes:
            for bbox in self.bboxes:
                painter.drawRect(bbox['left'], bbox['top'], bbox['width'], bbox['height'])

    def update_bboxes(self, bboxes):
        self.bboxes = bboxes
        # Call update() to trigger a repaint
        QTimer.singleShot(0, self.update)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    sys.exit(app.exec_())
