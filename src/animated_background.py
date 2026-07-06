from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QLinearGradient, QPainter, QColor, QRadialGradient, QPen
from PyQt6.QtCore import QPointF, QTimer, Qt
import math

class AnimatedBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30fps

    def _tick(self):
        self._phase += 0.008
        self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        base_grad = QLinearGradient(0, 0, w, h)
        base_grad.setColorAt(0.0, QColor("#020810"))
        base_grad.setColorAt(0.5, QColor("#050d1a"))
        base_grad.setColorAt(1.0, QColor("#020c14"))
        painter.fillRect(0, 0, w, h, base_grad)

        cx1 = int(w * (0.15 + 0.12 * math.sin(self._phase)))
        cy1 = int(h * (0.2  + 0.10 * math.cos(self._phase * 0.7)))
        r1  = int(max(w, h) * 0.38)
        grad1 = QRadialGradient(QPointF(cx1, cy1), r1)
        grad1.setColorAt(0.0, QColor(0, 180, 255, 80))
        grad1.setColorAt(0.5, QColor(0, 100, 180, 30))
        grad1.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(grad1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx1, cy1), r1, r1)

        cx2 = int(w * (0.80 + 0.10 * math.cos(self._phase * 0.8)))
        cy2 = int(h * (0.70 + 0.12 * math.sin(self._phase * 1.1)))
        r2  = int(max(w, h) * 0.42)
        grad2 = QRadialGradient(QPointF(cx2, cy2), r2)
        grad2.setColorAt(0.0, QColor(0, 220, 130, 70))
        grad2.setColorAt(0.5, QColor(0, 140, 80,  25))
        grad2.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(grad2)
        painter.drawEllipse(QPointF(cx2, cy2), r2, r2)

        cx3 = int(w * (0.50 + 0.08 * math.sin(self._phase * 1.3 + 2)))
        cy3 = int(h * (0.45 + 0.08 * math.cos(self._phase * 0.9 + 1)))
        r3  = int(max(w, h) * 0.28)
        grad3 = QRadialGradient(QPointF(cx3, cy3), r3)
        grad3.setColorAt(0.0, QColor(60, 0, 180, 50))
        grad3.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(grad3)
        painter.drawEllipse(QPointF(cx3, cy3), r3, r3)

        grid_pen = QPen(QColor(0, 212, 255, 12))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        grid_size = 60
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)

        painter.end()