from PyQt6.QtWidgets import QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve

from src.drawn_buttons import TitleBarButton
from src.styles import ACCENT, BG_DARK

class TitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {BG_DARK}; border-bottom: 2px solid {ACCENT};")

        layout = QHBoxLayout(self)

        self.title_label = QLabel("СИСТЕМА ЗА АНАЛИЗ НА ИЗСТРЕЛИ")
        self.title_label.setStyleSheet(
            f"color: {ACCENT}; font-weight: bold; border: none;"
            " font-size: 14px; font-family: 'Consolas';"
        )
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.btn_min = TitleBarButton("minimize")
        self.btn_min.clicked.connect(self.window().showMinimized)
        layout.addWidget(self.btn_min)
        
        self.btn_close = TitleBarButton("close")
        self.btn_close.clicked.connect(self.window().close)
        layout.addWidget(self.btn_close)

        self.is_visible = False
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def slide_in(self):
        if self.is_visible: return
        self.is_visible = True
        w = self.parent().width()
        self.anim.setStartValue(QRect(0, -40, w, 40))
        self.anim.setEndValue(QRect(0, 0, w, 40))
        self.anim.start()

    def slide_out(self):
        if not self.is_visible: return
        self.is_visible = False
        w = self.parent().width()
        self.anim.setStartValue(QRect(0, 0, w, 40))
        self.anim.setEndValue(QRect(0, -40, w, 40))
        self.anim.start()