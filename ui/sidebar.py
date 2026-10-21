from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class Sidebar(QWidget):
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(230)
        self.current_tab = 0
        self.nav_buttons = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(6)

        # Branding Header
        brand_label = QLabel("SENNHEISER")
        brand_label.setStyleSheet("font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #00D2FF;")
        layout.addWidget(brand_label)

        title_label = QLabel("MOMENTUM TW 5")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;")
        layout.addWidget(title_label)

        # Status Pill
        self.status_pill = QFrame()
        self.status_pill.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 82, 82, 0.12);
                border: 1px solid rgba(255, 82, 82, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        pill_layout = QHBoxLayout(self.status_pill)
        pill_layout.setContentsMargins(6, 3, 6, 3)
        pill_layout.setSpacing(6)

        self.dot = QLabel("●")
        self.dot.setStyleSheet("color: #FF5252; font-size: 10px;")
        pill_layout.addWidget(self.dot)

        self.status_text = QLabel("Getrennt")
        self.status_text.setStyleSheet("color: #FF5252; font-size: 11px; font-weight: 600;")
        pill_layout.addWidget(self.status_text)
        pill_layout.addStretch()

        layout.addWidget(self.status_pill)
        layout.addSpacing(10)

        # Navigation Buttons
        tabs = [
            ("🏠", "Übersicht"),
            ("🛡️", "ANC && Transparenz"),
            ("🎧", "Klang && Atmos"),
            ("⚡", "Smart Features"),
            ("📡", "Telemetrie && Logs"),
            ("⚙️", "Einstellungen")
        ]

        for idx, (icon, text) in enumerate(tabs):
            btn = QPushButton(f"{icon}  {text}")
            btn.setProperty("class", "NavBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.select_tab(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Bottom Mini Info Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        ic_layout = QVBoxLayout(self.info_card)
        ic_layout.setContentsMargins(8, 8, 8, 8)
        ic_layout.setSpacing(4)

        lbl = QLabel("AUDIO CODEC")
        lbl.setStyleSheet("font-size: 10px; color: #64748B; font-weight: 700; letter-spacing: 1px;")
        ic_layout.addWidget(lbl)

        self.codec_label = QLabel("Qualcomm aptX")
        self.codec_label.setStyleSheet("font-size: 12px; color: #00D2FF; font-weight: 600;")
        ic_layout.addWidget(self.codec_label)

        self.rate_label = QLabel("48 kHz • 24-bit")
        self.rate_label.setStyleSheet("font-size: 11px; color: #94A3B8;")
        ic_layout.addWidget(self.rate_label)

        layout.addWidget(self.info_card)

        # Default select tab 0
        self.select_tab(0)

    def select_tab(self, index: int):
        self.current_tab = index
        for idx, btn in enumerate(self.nav_buttons):
            active = "true" if idx == index else "false"
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.tab_changed.emit(index)

    def set_connected(self, connected: bool):
        if connected:
            self.status_pill.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 230, 118, 0.12);
                    border: 1px solid rgba(0, 230, 118, 0.3);
                    border-radius: 6px;
                }
            """)
            self.dot.setStyleSheet("color: #00E676; font-size: 10px;")
            self.status_text.setText("Verbunden")
            self.status_text.setStyleSheet("color: #00E676; font-size: 11px; font-weight: 600;")
        else:
            self.status_pill.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 82, 82, 0.12);
                    border: 1px solid rgba(255, 82, 82, 0.3);
                    border-radius: 6px;
                }
            """)
            self.dot.setStyleSheet("color: #FF5252; font-size: 10px;")
            self.status_text.setText("Getrennt")
            self.status_text.setStyleSheet("color: #FF5252; font-size: 11px; font-weight: 600;")

    def update_codec_info(self, codec: str, rate: str):
        self.codec_label.setText(codec)
        self.rate_label.setText(rate)
