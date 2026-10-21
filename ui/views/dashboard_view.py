from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QSlider, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class BatteryCard(QFrame):
    def __init__(self, title: str, icon_str: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setStyleSheet(f"""
            QFrame.Card {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
                padding: 14px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header Row
        h_row = QHBoxLayout()
        self.icon_lbl = QLabel(icon_str)
        self.icon_lbl.setStyleSheet("font-size: 18px;")
        h_row.addWidget(self.icon_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #94A3B8;")
        h_row.addWidget(self.title_lbl)
        h_row.addStretch()

        self.badge = QLabel("Aktiv")
        self.badge.setStyleSheet("""
            background-color: rgba(0, 230, 118, 0.12);
            color: #00E676;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        h_row.addWidget(self.badge)
        layout.addLayout(h_row)

        # Value
        self.val_lbl = QLabel("-- %")
        self.val_lbl.setStyleSheet("font-size: 26px; font-weight: 800; color: #FFFFFF;")
        layout.addWidget(self.val_lbl)

        # Progress
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Subtext
        self.sub_lbl = QLabel("Wird synchronisiert...")
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #64748B;")
        layout.addWidget(self.sub_lbl)

    def set_battery(self, pct: int, charging: bool = False):
        if pct < 0:
            self.val_lbl.setText("Standby")
            self.val_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #94A3B8;")
            self.progress.setValue(100)
            self.progress.setStyleSheet("QProgressBar::chunk { background: #353D4E; }")
            self.sub_lbl.setText("Im Ladecase / Standby")
            self.badge.setText("Bereit")
            self.badge.setStyleSheet("background-color: rgba(148, 163, 184, 0.15); color: #94A3B8;")
            return

        self.val_lbl.setText(f"{pct} %")
        self.val_lbl.setStyleSheet("font-size: 26px; font-weight: 800; color: #FFFFFF;")
        self.progress.setValue(pct)

        # Color coding
        if charging:
            color = Theme.ACCENT_GREEN
            self.badge.setText("⚡ Lädt")
            self.badge.setStyleSheet("background-color: rgba(0, 230, 118, 0.2); color: #00E676;")
            self.sub_lbl.setText("Wird aufgeladen...")
        elif pct > 30:
            color = Theme.PRIMARY
            self.badge.setText("In Betrieb")
            self.badge.setStyleSheet("background-color: rgba(0, 210, 255, 0.12); color: #00D2FF;")
            self.sub_lbl.setText("Optimaler Ladestand")
        else:
            color = Theme.ACCENT_RED
            self.badge.setText("Niedrig")
            self.badge.setStyleSheet("background-color: rgba(255, 82, 82, 0.2); color: #FF5252;")
            self.sub_lbl.setText("Bitte bald aufladen")

        self.progress.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}")


class DashboardView(QWidget):
    anc_mode_requested = pyqtSignal(str) # "anc", "transparency", "off"
    bass_boost_toggled = pyqtSignal(bool)
    volume_changed = pyqtSignal(float)
    loudness_boost_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header Banner
        header = QHBoxLayout()
        v_h = QVBoxLayout()
        title = QLabel("Dashboard & Status")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        v_h.addWidget(title)

        self.subtitle = QLabel("MOMENTUM TW 5 • Verbunden über aptX (48 kHz)")
        self.subtitle.setStyleSheet("font-size: 13px; color: #00D2FF; font-weight: 500;")
        v_h.addWidget(self.subtitle)
        header.addLayout(v_h)
        header.addStretch()
        layout.addLayout(header)

        # Battery Cards Row
        bat_grid = QGridLayout()
        bat_grid.setSpacing(14)

        self.card_left = BatteryCard("Linker Earbud (L)", "🟢")
        self.card_right = BatteryCard("Rechter Earbud (R)", "🟢")
        self.card_case = BatteryCard("Ladecase", "📦")

        bat_grid.addWidget(self.card_left, 0, 0)
        bat_grid.addWidget(self.card_right, 0, 1)
        bat_grid.addWidget(self.card_case, 0, 2)
        layout.addLayout(bat_grid)

        # Quick Controls Card
        qc_card = QFrame()
        qc_card.setProperty("class", "Card")
        qc_layout = QVBoxLayout(qc_card)
        qc_layout.setSpacing(16)

        qc_title = QLabel("SCHNELLEINSTELLUNGEN")
        qc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        qc_layout.addWidget(qc_title)

        # Volume Row
        vol_row = QHBoxLayout()
        vol_lbl = QLabel("🔊 Systemlautstärke")
        vol_lbl.setStyleSheet("font-size: 13px; font-weight: 600; min-width: 140px;")
        vol_row.addWidget(vol_lbl)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 200) # up to 200% volume overdrive
        self.vol_slider.setValue(100)
        self.vol_slider.valueChanged.connect(self._on_vol_slider_changed)
        vol_row.addWidget(self.vol_slider)

        self.vol_val_lbl = QLabel("100 %")
        self.vol_val_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #00D2FF; min-width: 90px;")
        vol_row.addWidget(self.vol_val_lbl)

        self.btn_boost = QPushButton("🚀 Studio-Boost")
        self.btn_boost.setCheckable(True)
        self.btn_boost.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_boost.setToolTip("Aktiviert den EasyEffects Studio Preamp (+6 dB) mit transparentem Brickwall-Limiter")
        self.btn_boost.toggled.connect(self._on_boost_btn_toggled)
        vol_row.addWidget(self.btn_boost)

        qc_layout.addLayout(vol_row)

        # ANC Mode Buttons Row
        anc_row = QHBoxLayout()
        anc_lbl = QLabel("🛡️ Geräuschkontrolle")
        anc_lbl.setStyleSheet("font-size: 13px; font-weight: 600; min-width: 140px;")
        anc_row.addWidget(anc_lbl)

        self.btn_anc = QPushButton("ANC Ein")
        self.btn_anc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_anc.clicked.connect(lambda: self.anc_mode_requested.emit("anc"))
        anc_row.addWidget(self.btn_anc)

        self.btn_trans = QPushButton("Transparenz")
        self.btn_trans.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans.clicked.connect(lambda: self.anc_mode_requested.emit("transparency"))
        anc_row.addWidget(self.btn_trans)

        self.btn_off = QPushButton("Aus (Normal)")
        self.btn_off.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_off.clicked.connect(lambda: self.anc_mode_requested.emit("off"))
        anc_row.addWidget(self.btn_off)

        anc_row.addStretch()
        qc_layout.addLayout(anc_row)

        layout.addWidget(qc_card)

        # Audio Specs Detail Card
        spec_card = QFrame()
        spec_card.setProperty("class", "Card")
        spec_layout = QGridLayout(spec_card)
        spec_layout.setSpacing(12)

        specs = [
            ("Übertragungsstandard", "Bluetooth 5.4 LE / Classic"),
            ("Aktiver Audio-Codec", "Qualcomm aptX™ (A2DP)"),
            ("Signalauflösung", "48.000 Hz • 24-Bit PCM"),
            ("Latenzmodus", "Niedrige Latenz (< 80 ms)")
        ]
        for idx, (label, val) in enumerate(specs):
            row = idx // 2
            col = (idx % 2) * 2
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 12px; color: #64748B;")
            vlbl = QLabel(val)
            vlbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #F8FAFC;")
            spec_layout.addWidget(lbl, row, col)
            spec_layout.addWidget(vlbl, row, col + 1)

        layout.addWidget(spec_card)
        layout.addStretch()

    def _on_vol_slider_changed(self, val: int):
        if val > 150:
            self.vol_val_lbl.setText(f"{val} % (OVERDRIVE)")
            self.vol_val_lbl.setStyleSheet("font-size: 12px; font-weight: 800; color: #FF5252; min-width: 105px;")
        elif val > 100:
            self.vol_val_lbl.setText(f"{val} % (Boost)")
            self.vol_val_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #FFB300; min-width: 105px;")
        else:
            self.vol_val_lbl.setText(f"{val} %")
            self.vol_val_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #00D2FF; min-width: 105px;")
        self.volume_changed.emit(val / 100.0)

    def set_volume_display(self, vol: float):
        val = int(vol * 100)
        self.vol_slider.blockSignals(True)
        self.vol_slider.setValue(val)
        self.vol_slider.blockSignals(False)
        if val > 150:
            self.vol_val_lbl.setText(f"{val} % (OVERDRIVE)")
            self.vol_val_lbl.setStyleSheet("font-size: 12px; font-weight: 800; color: #FF5252; min-width: 105px;")
        elif val > 100:
            self.vol_val_lbl.setText(f"{val} % (Boost)")
            self.vol_val_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #FFB300; min-width: 105px;")
        else:
            self.vol_val_lbl.setText(f"{val} %")
            self.vol_val_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #00D2FF; min-width: 105px;")

    def _on_boost_btn_toggled(self, checked: bool):
        self.set_boost_ui_state(checked)
        self.loudness_boost_toggled.emit(checked)

    def set_boost_ui_state(self, enabled: bool):
        self.btn_boost.blockSignals(True)
        self.btn_boost.setChecked(enabled)
        self.btn_boost.blockSignals(False)
        if enabled:
            self.btn_boost.setStyleSheet("background: #9D4EDD; color: #FFFFFF; font-weight: 700; border: none; border-radius: 6px; padding: 6px 12px;")
            self.btn_boost.setText("🚀 Boost: AKTIV (+6dB)")
        else:
            self.btn_boost.setStyleSheet("")
            self.btn_boost.setText("🚀 Studio-Boost")

    def update_batteries(self, l_pct: int, l_chg: bool, r_pct: int, r_chg: bool, c_pct: int, c_chg: bool):
        self.card_left.set_battery(l_pct, l_chg)
        self.card_right.set_battery(r_pct, r_chg)
        self.card_case.set_battery(c_pct, c_chg)

    def set_anc_ui_mode(self, mode: str):
        # Reset styles
        for b in [self.btn_anc, self.btn_trans, self.btn_off]:
            b.setStyleSheet("")
        
        active_style = f"background: {Theme.PRIMARY_GRADIENT}; color: #050B14; font-weight: 700; border: none;"
        if mode == "anc":
            self.btn_anc.setStyleSheet(active_style)
        elif mode == "transparency":
            self.btn_trans.setStyleSheet(active_style)
        else:
            self.btn_off.setStyleSheet(active_style)
