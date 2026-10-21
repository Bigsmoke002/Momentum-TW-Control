from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QCheckBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class SmartFeaturesView(QWidget):
    smart_pause_changed = pyqtSignal(bool)
    comfort_call_changed = pyqtSignal(bool)
    battery_protect_changed = pyqtSignal(bool)
    auto_power_off_changed = pyqtSignal(int)
    play_find_tone_requested = pyqtSignal(str) # "left", "right"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        title = QLabel("Smart Features & Akkupflege")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("Sennheiser Sensortechnologie, Trageerkennung, Akkuschutz und Suchton-Ortung.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(subtitle)

        # Row 1: Smart Sensors & Akkupflege
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        # Smart Earbud Features Card
        smart_card = QFrame()
        smart_card.setProperty("class", "Card")
        sc_layout = QVBoxLayout(smart_card)
        sc_layout.setSpacing(12)

        sc_title = QLabel("SMART FUNKTIONEN (IN-EAR SENSOREN)")
        sc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        sc_layout.addWidget(sc_title)

        self.cb_smart_pause = QCheckBox("Trageerkennung / Smart Pause aktivieren")
        self.cb_smart_pause.setChecked(True)
        self.cb_smart_pause.toggled.connect(self.smart_pause_changed.emit)
        sc_layout.addWidget(self.cb_smart_pause)

        sp_desc = QLabel("Infrarotsensor pausiert Musik automatisch, sobald ein Ohrhörer herausgenommen wird.")
        sp_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; margin-left: 24px;")
        sp_desc.setWordWrap(True)
        sc_layout.addWidget(sp_desc)

        self.cb_comfort_call = QCheckBox("Comfort Call (Eigenstimmen-Rückkopplung)")
        self.cb_comfort_call.setChecked(False)
        self.cb_comfort_call.toggled.connect(self.comfort_call_changed.emit)
        sc_layout.addWidget(self.cb_comfort_call)

        cc_desc = QLabel("Leitet die eigene Stimme bei Anrufen oder Discord dezent ins Ohr, für ein natürliches Gesprächsgefühl.")
        cc_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; margin-left: 24px;")
        cc_desc.setWordWrap(True)
        sc_layout.addWidget(cc_desc)
        top_row.addWidget(smart_card)

        # Akkuschutz & Power Management Card
        pwr_card = QFrame()
        pwr_card.setProperty("class", "Card")
        pc_layout = QVBoxLayout(pwr_card)
        pc_layout.setSpacing(12)

        pc_title = QLabel("AKKUPFLEGE & ENERGIE")
        pc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        pc_layout.addWidget(pc_title)

        self.cb_bat_protect = QCheckBox("Akkuschutz-Modus (Battery Protection)")
        self.cb_bat_protect.setChecked(False)
        self.cb_bat_protect.toggled.connect(self.battery_protect_changed.emit)
        pc_layout.addWidget(self.cb_bat_protect)

        bp_desc = QLabel("Begrenzt die Ladespannung auf 80%, schont die Lithium-Zellen und verdoppelt die Akkulebensdauer.")
        bp_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; margin-left: 24px;")
        bp_desc.setWordWrap(True)
        pc_layout.addWidget(bp_desc)

        # Auto Power Off Row
        apo_row = QHBoxLayout()
        apo_lbl = QLabel("Automatisches Abschalten:")
        apo_lbl.setStyleSheet("font-size: 12px; color: #FFFFFF;")
        apo_row.addWidget(apo_lbl)

        self.combo_apo = QComboBox()
        self.combo_apo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.BG_CARD_HOVER};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                color: #FFFFFF;
                padding: 4px 10px;
                font-size: 12px;
            }}
        """)
        self.combo_apo.addItems(["Nie", "15 Minuten", "30 Minuten", "60 Minuten"])
        self.combo_apo.setCurrentIndex(2) # 30 min
        self.combo_apo.currentIndexChanged.connect(self._on_apo_changed)
        apo_row.addWidget(self.combo_apo)
        apo_row.addStretch()
        pc_layout.addLayout(apo_row)

        top_row.addWidget(pwr_card)
        layout.addLayout(top_row)

        # Row 2: Find My Earbuds & Touch Gesten Guide
        mid_row = QHBoxLayout()
        mid_row.setSpacing(14)

        # Find My Earbuds Card
        find_card = QFrame()
        find_card.setProperty("class", "Card")
        fc_layout = QVBoxLayout(find_card)
        fc_layout.setSpacing(10)

        fc_title = QLabel("SUCHFUNKTION (FIND MY EARBUDS)")
        fc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        fc_layout.addWidget(fc_title)

        fc_desc = QLabel("Spielt einen akustischen Hochfrequenz-Suchton gezielt auf einem Hörer ab, um ihn schnell wiederzufinden:")
        fc_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        fc_desc.setWordWrap(True)
        fc_layout.addWidget(fc_desc)

        btn_box = QHBoxLayout()
        btn_find_l = QPushButton("🔊 Linker Hörer")
        btn_find_l.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_find_l.clicked.connect(lambda: self.play_find_tone_requested.emit("left"))
        btn_box.addWidget(btn_find_l)

        btn_find_r = QPushButton("🔊 Rechter Hörer")
        btn_find_r.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_find_r.clicked.connect(lambda: self.play_find_tone_requested.emit("right"))
        btn_box.addWidget(btn_find_r)
        fc_layout.addLayout(btn_box)
        mid_row.addWidget(find_card)

        # Touch Gesten Guide Card
        touch_card = QFrame()
        touch_card.setProperty("class", "Card")
        tc_layout = QVBoxLayout(touch_card)
        tc_layout.setSpacing(6)

        tc_title = QLabel("TOUCH-BEDIENUNG (ÜBERSICHT)")
        tc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        tc_layout.addWidget(tc_title)

        t_grid = QGridLayout()
        t_grid.setSpacing(6)
        gestures = [
            ("1x Tippen:", "Links: Transparenz / ANC", "Rechts: Play / Pause"),
            ("2x Tippen:", "Links: Vorheriger Track", "Rechts: Nächster Track"),
            ("3x Tippen:", "Links: Sprachassistent", "Rechts: Sound-Modus"),
            ("Halten:", "Links: Lautstärke leiser", "Rechts: Lautstärke lauter")
        ]
        for row, (action, l_desc, r_desc) in enumerate(gestures):
            albl = QLabel(action)
            albl.setStyleSheet("font-size: 11px; font-weight: 700; color: #00D2FF;")
            llbl = QLabel(l_desc)
            llbl.setStyleSheet("font-size: 11px; color: #F1F5F9;")
            rlbl = QLabel(r_desc)
            rlbl.setStyleSheet("font-size: 11px; color: #F1F5F9;")
            t_grid.addWidget(albl, row, 0)
            t_grid.addWidget(llbl, row, 1)
            t_grid.addWidget(rlbl, row, 2)
        tc_layout.addLayout(t_grid)
        mid_row.addWidget(touch_card)

        layout.addLayout(mid_row)
        layout.addStretch()

    def _on_apo_changed(self, idx: int):
        mapping = {0: 0, 1: 15, 2: 30, 3: 60}
        mins = mapping.get(idx, 30)
        self.auto_power_off_changed.emit(mins)

    def update_state(self, state: dict):
        sp = state.get("smart_pause", True)
        cc = state.get("comfort_call", False)
        bp = state.get("battery_protect", False)
        apo = state.get("auto_power_off", 30)

        self.cb_smart_pause.blockSignals(True)
        self.cb_smart_pause.setChecked(sp)
        self.cb_smart_pause.blockSignals(False)

        self.cb_comfort_call.blockSignals(True)
        self.cb_comfort_call.setChecked(cc)
        self.cb_comfort_call.blockSignals(False)

        self.cb_bat_protect.blockSignals(True)
        self.cb_bat_protect.setChecked(bp)
        self.cb_bat_protect.blockSignals(False)

        self.combo_apo.blockSignals(True)
        if apo == 0:
            self.combo_apo.setCurrentIndex(0)
        elif apo <= 15:
            self.combo_apo.setCurrentIndex(1)
        elif apo <= 30:
            self.combo_apo.setCurrentIndex(2)
        else:
            self.combo_apo.setCurrentIndex(3)
        self.combo_apo.blockSignals(False)
