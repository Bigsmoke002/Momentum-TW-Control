from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSlider, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class ModeCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon_str: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_active = False

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        h_top = QHBoxLayout()
        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 24px;")
        h_top.addWidget(icon_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        h_top.addWidget(self.title_lbl)
        h_top.addStretch()
        layout.addLayout(h_top)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        self.set_active(False)

    def mousePressEvent(self, event):
        self.clicked.emit()

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.setStyleSheet(f"""
                QFrame.Card {{
                    background-color: rgba(0, 210, 255, 0.08);
                    border: 2px solid {Theme.PRIMARY};
                    border-radius: 12px;
                    padding: 14px;
                }}
            """)
            self.title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {Theme.PRIMARY};")
        else:
            self.setStyleSheet(f"""
                QFrame.Card {{
                    background-color: {Theme.BG_CARD};
                    border: 1px solid {Theme.BORDER};
                    border-radius: 12px;
                    padding: 14px;
                }}
            """)
            self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")


class AncView(QWidget):
    mode_requested = pyqtSignal(str) # "anc", "transparency", "off"
    transparency_level_changed = pyqtSignal(int)
    anti_wind_changed = pyqtSignal(str) # "off", "auto", "max"
    adaptive_anc_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        title = QLabel("Geräuschkontrolle & Transparenz")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("Aktive Geräuschunterdrückung (ANC) und Transparenzmodus nach deinen Bedürfnissen regeln.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(subtitle)

        # Live Hardware Confirmation Banner
        self.hw_banner = QFrame()
        self.hw_banner.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 210, 255, 0.05);
                border: 1px solid rgba(0, 210, 255, 0.2);
                border-radius: 8px;
                padding: 6px 12px;
            }}
        """)
        hw_layout = QHBoxLayout(self.hw_banner)
        hw_layout.setContentsMargins(10, 6, 10, 6)
        hw_layout.setSpacing(8)

        self.hw_dot = QLabel("●")
        self.hw_dot.setStyleSheet("color: #00E676; font-size: 12px;")
        hw_layout.addWidget(self.hw_dot)

        self.hw_text = QLabel("Hardware-Rückmeldung: ANC Aktiv (0x1A85)")
        self.hw_text.setStyleSheet("font-size: 12px; font-weight: 600; color: #E2E8F0;")
        hw_layout.addWidget(self.hw_text)
        hw_layout.addStretch()

        self.hw_time = QLabel("Synchronisiert um --:--:--")
        self.hw_time.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        hw_layout.addWidget(self.hw_time)

        layout.addWidget(self.hw_banner)

        # Mode Selection Row (3 Cards)
        modes_row = QHBoxLayout()
        modes_row.setSpacing(14)

        self.card_anc = ModeCard("🛡️", "Geräuschunterdrückung (ANC)", "Blendet Außengeräusche effektiv aus für ungestörten Klanggenuss.")
        self.card_anc.clicked.connect(lambda: self._select_mode("anc", user_initiated=True))
        modes_row.addWidget(self.card_anc)

        self.card_trans = ModeCard("🎙️", "Transparenzmodus", "Schleift Umweltgeräusche und Stimmen klar über die Mikrofone ein.")
        self.card_trans.clicked.connect(lambda: self._select_mode("transparency", user_initiated=True))
        modes_row.addWidget(self.card_trans)

        self.card_off = ModeCard("⭕", "Aus (Passiv)", "ANC und Transparenz deaktiviert. Nur passive Abdichtung im Ohr.")
        self.card_off.clicked.connect(lambda: self._select_mode("off", user_initiated=True))
        modes_row.addWidget(self.card_off)

        layout.addLayout(modes_row)

        # Transparency Level Slider Card
        self.trans_card = QFrame()
        self.trans_card.setProperty("class", "Card")
        tc_layout = QVBoxLayout(self.trans_card)
        tc_layout.setSpacing(12)

        tc_header = QHBoxLayout()
        tc_title = QLabel("TRANSPARENZ-INTENSITÄT")
        tc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        tc_header.addWidget(tc_title)
        tc_header.addStretch()

        self.trans_val_lbl = QLabel("70 %")
        self.trans_val_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {Theme.PRIMARY};")
        tc_header.addWidget(self.trans_val_lbl)
        tc_layout.addLayout(tc_header)

        self.trans_slider = QSlider(Qt.Orientation.Horizontal)
        self.trans_slider.setRange(0, 100)
        self.trans_slider.setValue(70)
        self.trans_slider.valueChanged.connect(self._on_trans_slider_changed)
        tc_layout.addWidget(self.trans_slider)

        tc_desc = QLabel("Regelt stufenlos über Hardware-Register 0x1A02, wie viele Außengeräusche eingeleitet werden.")
        tc_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        tc_layout.addWidget(tc_desc)

        layout.addWidget(self.trans_card)

        # Advanced Settings Card
        adv_card = QFrame()
        adv_card.setProperty("class", "Card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.setSpacing(16)

        adv_title = QLabel("ERWEITERTE OPTIONEN")
        adv_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        adv_layout.addWidget(adv_title)

        # Anti-Wind Selection
        wind_row = QHBoxLayout()
        w_v = QVBoxLayout()
        w_title = QLabel("🌬️ Windgeräusch-Reduktion (Anti-Wind)")
        w_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #FFFFFF;")
        w_v.addWidget(w_title)
        w_desc = QLabel("Unterdrückt störendes Windrauschen an den Außenmikrofonen.")
        w_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        w_v.addWidget(w_desc)
        wind_row.addLayout(w_v)
        wind_row.addStretch()

        self.btn_wind_off = QPushButton("Aus")
        self.btn_wind_off.clicked.connect(lambda: self._select_anti_wind("off", user_initiated=True))
        wind_row.addWidget(self.btn_wind_off)

        self.btn_wind_auto = QPushButton("Auto")
        self.btn_wind_auto.clicked.connect(lambda: self._select_anti_wind("auto", user_initiated=True))
        wind_row.addWidget(self.btn_wind_auto)

        self.btn_wind_max = QPushButton("Max")
        self.btn_wind_max.clicked.connect(lambda: self._select_anti_wind("max", user_initiated=True))
        wind_row.addWidget(self.btn_wind_max)

        adv_layout.addLayout(wind_row)

        # Adaptive ANC Checkbox
        adap_row = QHBoxLayout()
        self.cb_adaptive = QCheckBox("Adaptives ANC (Automatische Umgebungsanpassung)")
        self.cb_adaptive.toggled.connect(self.adaptive_anc_changed.emit)
        adap_row.addWidget(self.cb_adaptive)
        adv_layout.addLayout(adap_row)

        layout.addWidget(adv_card)
        layout.addStretch()

        # Initial UI visual
        self._select_mode("anc", user_initiated=False)
        self._select_anti_wind("off", user_initiated=False)

    def set_ui_mode(self, mode: str):
        self._select_mode(mode, user_initiated=False)

    def _select_mode(self, mode: str, user_initiated: bool = True):
        self.card_anc.set_active(mode == "anc")
        self.card_trans.set_active(mode == "transparency")
        self.card_off.set_active(mode == "off")
        self.trans_card.setEnabled(mode == "transparency")

        if user_initiated:
            self.mode_requested.emit(mode)

    def _on_trans_slider_changed(self, val: int):
        self.trans_val_lbl.setText(f"{val} %")
        if self.card_trans.is_active:
            self.transparency_level_changed.emit(val)

    def _select_anti_wind(self, mode: str, user_initiated: bool = True):
        active_style = f"background: {Theme.PRIMARY_GRADIENT}; color: #050B14; font-weight: 700; border: none;"
        for b in [self.btn_wind_off, self.btn_wind_auto, self.btn_wind_max]:
            b.setStyleSheet("")
        if mode == "auto":
            self.btn_wind_auto.setStyleSheet(active_style)
        elif mode == "max":
            self.btn_wind_max.setStyleSheet(active_style)
        else:
            self.btn_wind_off.setStyleSheet(active_style)

        if user_initiated:
            self.anti_wind_changed.emit(mode)

    def update_state(self, state: dict):
        mode = state.get("mode", "anc")
        anc = state.get("anc", False)
        trans_state = state.get("transparency_state", False)
        trans_lvl = state.get("transparency_level", 70)
        anti_wind = state.get("anti_wind", "off")
        adaptive = state.get("adaptive_anc", False)
        last_sync = state.get("last_sync", "--:--:--")

        # Resolve mode
        if mode == "anc" or (anc and not trans_state):
            self._select_mode("anc", user_initiated=False)
            self.hw_dot.setStyleSheet("color: #00E676; font-size: 12px;")
            self.hw_text.setText("Hardware bestätigt: Geräuschunterdrückung AKTIV (0x1A85 ON)")
        elif mode == "transparency" or trans_state:
            self._select_mode("transparency", user_initiated=False)
            self.trans_slider.blockSignals(True)
            self.trans_slider.setValue(trans_lvl)
            self.trans_val_lbl.setText(f"{trans_lvl} %")
            self.trans_slider.blockSignals(False)
            self.hw_dot.setStyleSheet("color: #00D2FF; font-size: 12px;")
            self.hw_text.setText(f"Hardware bestätigt: Transparenz AKTIV ({trans_lvl}%) (0x1901 ON)")
        else:
            self._select_mode("off", user_initiated=False)
            self.hw_dot.setStyleSheet("color: #94A3B8; font-size: 12px;")
            self.hw_text.setText("Hardware bestätigt: Geräuschkontrolle AUS (Passiver Modus)")

        self.hw_time.setText(f"Synchronisiert um {last_sync}")

        self._select_anti_wind(anti_wind, user_initiated=False)
        self.cb_adaptive.blockSignals(True)
        self.cb_adaptive.setChecked(adaptive)
        self.cb_adaptive.blockSignals(False)
