from PyQt6.QtWidgets import QAbstractButton
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QFont
from PyQt6.QtCore import Qt, QRectF, QPointF


class PlayerButton(QAbstractButton):
    def __init__(self, kind: str, color: str = "#00d4ff", size: int = 40, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = QColor(color)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._pressed = False
        self._active = False
        self.setToolTip({"play": "Пусни", "pause": "Пауза", "stop": "Спри"}.get(kind, kind))

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self.update()

    def is_active(self) -> bool:
        return self._active

    def enterEvent(self, _):
        self._hovered = True
        self.update()

    def leaveEvent(self, _):
        self._hovered = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 1

        if self._active:
            bg = QColor(self.color.red(), self.color.green(), self.color.blue(), 70)
            border = self.color
            pen_width = 2.0
        elif self._pressed:
            bg = QColor(self.color.red(), self.color.green(), self.color.blue(), 60)
            border = self.color
            pen_width = 1.2
        elif self._hovered:
            bg = QColor(self.color.red(), self.color.green(), self.color.blue(), 30)
            border = QColor(self.color.red(), self.color.green(), self.color.blue(), 200)
            pen_width = 1.2
        else:
            bg = QColor(255, 255, 255, 8)
            border = QColor(255, 255, 255, 40)
            pen_width = 1.2

        p.setBrush(bg)
        pen = QPen(border, pen_width)
        p.setPen(pen)
        p.drawEllipse(QPointF(cx, cy), r, r)

        icon_color = self.color if (self._active or self._hovered or self._pressed) else QColor(200, 220, 235)
        p.setBrush(icon_color)
        p.setPen(Qt.PenStyle.NoPen)
        ir = r * 0.38

        if self.kind == "play":
            path = QPainterPath()
            path.moveTo(cx - ir * 0.7, cy - ir)
            path.lineTo(cx + ir * 0.9, cy)
            path.lineTo(cx - ir * 0.7, cy + ir)
            path.closeSubpath()
            p.drawPath(path)

        elif self.kind == "pause":
            bar_w = ir * 0.45
            gap   = ir * 0.35
            p.drawRoundedRect(QRectF(cx - gap - bar_w, cy - ir, bar_w, ir * 2), 2, 2)
            p.drawRoundedRect(QRectF(cx + gap,         cy - ir, bar_w, ir * 2), 2, 2)

        elif self.kind == "stop":
            s = ir * 1.3
            p.drawRoundedRect(QRectF(cx - s / 2, cy - s / 2, s, s), 3, 3)

        p.end()

class TitleBarButton(QAbstractButton):
    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._pressed = False
        self.color = QColor("#00d4ff")

    def enterEvent(self, _):
        self._hovered = True; self.update()
    def leaveEvent(self, _):
        self._hovered = False; self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pressed = True; self.update()
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e):
        self._pressed = False; self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        if self._pressed:
            p.fillRect(0, 0, w, h, QColor(255, 0, 0, 150) if self.kind == "close" else QColor(255, 255, 255, 50))
        elif self._hovered:
            p.fillRect(0, 0, w, h, QColor(255, 0, 0, 200) if self.kind == "close" else QColor(255, 255, 255, 30))

        # Настройка на химикалката (контура)
        icon_color = QColor("white") if self._hovered else self.color
        pen = QPen(icon_color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        
        cx, cy = w / 2, h / 3
        r = 6
        
        if self.kind == "minimize":
            p.drawLine(int(cx - r), int(cy + r/2), int(cx + r), int(cy + r/2))
        elif self.kind == "close":
            p.drawLine(int(cx - r), int(cy - r), int(cx + r), int(cy + r))
            p.drawLine(int(cx - r), int(cy + r), int(cx + r), int(cy - r))
            
        p.end()

class SidebarButton(QAbstractButton):
    def __init__(self, kind: str, text: str, parent=None):
        super().__init__(parent)
        self.kind = kind
        self._text = text
        self.setFixedHeight(45)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._hovered = False
        self._compact = False

    def enterEvent(self, _):
        self._hovered = True; self.update()
    def leaveEvent(self, _):
        self._hovered = False; self.update()

    def set_compact(self, compact: bool):
        self._compact = compact
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self.isChecked():
            p.fillRect(0, 0, w, h, QColor(0, 212, 255, 35))
            p.fillRect(0, 0, 4, h, QColor(0, 212, 255))
        elif self._hovered:
            p.fillRect(0, 0, w, h, QColor(0, 212, 255, 15))
            p.fillRect(0, 0, 4, h, QColor(0, 212, 255, 100))

        cx, cy = 35, h / 2
        r = 10

        if w < 100 or self._compact:
            cx, cy = w / 2, h / 2
        
        icon_color = QColor("#00d4ff") if self.isChecked() or self._hovered else QColor("#7ab3cc")
        pen = QPen(icon_color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)

        if self.kind == "ai":
            p.drawEllipse(QPointF(cx, cy), r*0.4, r*0.4)
            p.drawEllipse(QPointF(cx, cy), r, r)
            p.drawLine(int(cx), int(cy - r), int(cx), int(cy + r))
            p.drawLine(int(cx - r), int(cy), int(cx + r), int(cy))
        
        elif self.kind == "custom":
            gap = r * 0.6
            p.drawLine(int(cx - r), int(cy - gap), int(cx + r), int(cy - gap))
            p.drawEllipse(QPointF(cx - gap/2, cy - gap), 2, 2)
            p.drawLine(int(cx - r), int(cy), int(cx + r), int(cy))
            p.drawEllipse(QPointF(cx + gap/2, cy), 2, 2)
            p.drawLine(int(cx - r), int(cy + gap), int(cx + r), int(cy + gap))
            p.drawEllipse(QPointF(cx - gap, cy + gap), 2, 2)
            
        elif self.kind == "compare":
            p.drawLine(int(cx - r*0.6), int(cy + r*0.8), int(cx + r*0.6), int(cy + r*0.8))
            p.drawLine(int(cx), int(cy + r*0.8), int(cx), int(cy - r*0.5))
            p.drawLine(int(cx - r*0.8), int(cy - r*0.5), int(cx + r*0.8), int(cy - r*0.5))
            p.drawLine(int(cx - r*0.8), int(cy - r*0.5), int(cx - r*0.8), int(cy + r*0.3))
            p.drawLine(int(cx + r*0.8), int(cy - r*0.5), int(cx + r*0.8), int(cy + r*0.3))
            p.drawLine(int(cx - r*1.2), int(cy + r*0.3), int(cx - r*0.4), int(cy + r*0.3))
            p.drawLine(int(cx + r*0.4), int(cy + r*0.3), int(cx + r*1.2), int(cy + r*0.3))

        if w > 100 and not self._compact:
            p.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            p.drawText(
                QRectF(cx + 25, 0, w - cx - 25, h), 
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, 
                self._text
            )
            
        p.end()