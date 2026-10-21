from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class DisconnectedView(QWidget):
    connect_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main Card
        card = QFrame()
        card.setProperty("class", "Card")
        card.setFixedWidth(540)
        card.setStyleSheet(f"""
            QFrame.Card {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 16px;
                padding: 36px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Headphone Graphic Icon
        icon_box = QLabel("🎧")
        icon_box.setStyleSheet("""
            font-size: 64px;
            background-color: rgba(255, 82, 82, 0.08);
            border: 2px dashed rgba(255, 82, 82, 0.3);
            border-radius: 48px;
            padding: 16px;
            margin-bottom: 8px;
        """)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setFixedSize(96, 96)
        card_layout.addWidget(icon_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Kopfhörer nicht verbunden")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Deine MOMENTUM TW 5 wurden nicht erkannt oder sind im Standby.\n"
            "Bitte nimm die Earbuds aus dem Ladecase oder aktiviere Bluetooth."
        )
        desc.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED}; line-height: 140%;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        card_layout.addSpacing(12)

        # Status Hint
        self.status_msg = QLabel("Bereit zum Verbinden")
        self.status_msg.setStyleSheet(f"font-size: 11px; color: {Theme.PRIMARY};")
        self.status_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_msg)

        card_layout.addSpacing(8)

        # Connect Button
        self.btn_connect = QPushButton("Verbindung herstellen")
        self.btn_connect.setProperty("class", "Primary")
        self.btn_connect.setFixedSize(220, 42)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self._on_connect_click)
        card_layout.addWidget(self.btn_connect, alignment=Qt.AlignmentFlag.AlignCenter)

        # Tip
        tip = QLabel("Tipp: Die Kopfhörer verbinden sich automatisch, sobald sie aus dem Case genommen werden.")
        tip.setStyleSheet("font-size: 11px; color: #64748B; font-style: italic; margin-top: 10px;")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(tip)

        layout.addWidget(card)

    def _on_connect_click(self):
        self.status_msg.setText("Verbindung wird aufgebaut...")
        self.btn_connect.setEnabled(False)
        self.connect_clicked.emit()

    def reset_button(self):
        self.btn_connect.setEnabled(True)
        self.status_msg.setText("Bereit zum Verbinden")
