from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSlider, QCheckBox, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class SoundView(QWidget):
    bass_boost_changed = pyqtSignal(bool)
    spatial_audio_changed = pyqtSignal(bool)
    loudness_boost_changed = pyqtSignal(bool, float) # (enabled, gain_db)
    eq_changed = pyqtSignal(list) # list of 5 float dB values

    PRESETS = {
        "Neutral": [0.0, 0.0, 0.0, 0.0, 0.0],
        "Bass Boost": [4.5, 3.0, 0.0, 1.0, 2.0],
        "Podcast / Sprache": [-2.0, -1.0, 3.5, 2.0, 0.0],
        "Kino & Film": [4.0, 1.5, -1.0, 2.0, 3.5],
        "Rock / Pop": [3.0, 1.0, -0.5, 2.0, 3.0],
        "🚀 Max Overdrive": [6.0, 5.0, 4.0, 5.0, 6.0]
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_boost_gain = 6.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        title = QLabel("Klang & Raumakustik")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("Hardware-Klangprofile, Qualcomm 5-Band DSP Equalizer, 3D-Bühnenerweiterung und Studio Loudness Maximizer.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(subtitle)

        # Hardware DSP Status Banner
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
        self.hw_dot.setStyleSheet("color: #00D2FF; font-size: 12px;")
        hw_layout.addWidget(self.hw_dot)

        self.hw_text = QLabel("Hardware-DSP: Bass-Boost AUS • Hardware-EQ synchronisiert")
        self.hw_text.setStyleSheet("font-size: 12px; font-weight: 600; color: #E2E8F0;")
        hw_layout.addWidget(self.hw_text)
        hw_layout.addStretch()

        self.hw_time = QLabel("Synchronisiert um --:--:--")
        self.hw_time.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        hw_layout.addWidget(self.hw_time)

        layout.addWidget(self.hw_banner)

        # Enhancement Cards (Bass Boost, Spatial Audio, Studio Loudness Boost)
        enh_row = QHBoxLayout()
        enh_row.setSpacing(14)

        # Bass Boost Card
        bb_card = QFrame()
        bb_card.setProperty("class", "Card")
        bb_l = QVBoxLayout(bb_card)
        bb_l.setSpacing(8)

        bb_h = QHBoxLayout()
        bb_lbl = QLabel("🔊 Qualcomm Bass-Boost")
        bb_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        bb_h.addWidget(bb_lbl)
        bb_h.addStretch()

        self.cb_bass = QCheckBox()
        self.cb_bass.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_bass.toggled.connect(self._on_bass_toggled)
        bb_h.addWidget(self.cb_bass)
        bb_l.addLayout(bb_h)

        bb_desc = QLabel("Schaltet die Sub-Bass-Verstärkung direkt im Kopfhörer-Chip (Register 0x1008) verzerrungsfrei ein.")
        bb_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        bb_desc.setWordWrap(True)
        bb_l.addWidget(bb_desc)
        enh_row.addWidget(bb_card)

        # Spatial Audio Card
        sp_card = QFrame()
        sp_card.setProperty("class", "Card")
        sp_l = QVBoxLayout(sp_card)
        sp_l.setSpacing(8)

        sp_h = QHBoxLayout()
        sp_lbl = QLabel("🌌 3D Spatial Audio")
        sp_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        sp_h.addWidget(sp_lbl)
        sp_h.addStretch()

        self.cb_spatial = QCheckBox()
        self.cb_spatial.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_spatial.toggled.connect(self._on_spatial_toggled)
        sp_h.addWidget(self.cb_spatial)
        sp_l.addLayout(sp_h)

        sp_desc = QLabel("Binaurales Stereo-Widening über PipeWire/EasyEffects. Schaltet beim Deaktivieren sauber ab.")
        sp_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        sp_desc.setWordWrap(True)
        sp_l.addWidget(sp_desc)
        enh_row.addWidget(sp_card)

        # Studio Loudness Maximizer Card
        boost_card = QFrame()
        boost_card.setProperty("class", "Card")
        boost_l = QVBoxLayout(boost_card)
        boost_l.setSpacing(8)

        boost_h = QHBoxLayout()
        boost_lbl = QLabel("🚀 Loudness Maximizer")
        boost_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFFFFF;")
        boost_h.addWidget(boost_lbl)
        boost_h.addStretch()

        self.cb_boost = QCheckBox()
        self.cb_boost.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_boost.toggled.connect(self._on_boost_toggled)
        boost_h.addWidget(self.cb_boost)
        boost_l.addLayout(boost_h)

        boost_desc = QLabel("Preamp (+6 bis +12 dB) mit Brickwall-Limiter. Verhindert digitales Clipping bei hoher Lautstärke.")
        boost_desc.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_MUTED};")
        boost_desc.setWordWrap(True)
        boost_l.addWidget(boost_desc)

        gain_row = QHBoxLayout()
        gain_row.setSpacing(6)
        self.gain_buttons = {}
        for g_val in [3.0, 6.0, 9.0, 12.0]:
            btn = QPushButton(f"+{int(g_val)}dB")
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, g=g_val: self._set_gain_val(g))
            gain_row.addWidget(btn)
            self.gain_buttons[g_val] = btn
        boost_l.addLayout(gain_row)
        enh_row.addWidget(boost_card)

        layout.addLayout(enh_row)

        # 5-Band Equalizer Card
        eq_card = QFrame()
        eq_card.setProperty("class", "Card")
        eq_layout = QVBoxLayout(eq_card)
        eq_layout.setSpacing(16)

        eq_h = QHBoxLayout()
        eq_title = QLabel("5-BAND QUALCOMM HARDWARE & SYSTEM EQUALIZER")
        eq_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        eq_h.addWidget(eq_title)
        eq_h.addStretch()

        btn_reset = QPushButton("Neutral (Flat)")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(lambda: self.apply_preset("Neutral"))
        eq_h.addWidget(btn_reset)
        eq_layout.addLayout(eq_h)

        # Presets Row
        presets_row = QHBoxLayout()
        self.preset_buttons = {}
        for name in self.PRESETS.keys():
            btn = QPushButton(name.replace("&", "&&"))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self.apply_preset(n))
            presets_row.addWidget(btn)
            self.preset_buttons[name] = btn
        presets_row.addStretch()
        eq_layout.addLayout(presets_row)

        # Sliders Row
        sliders_row = QHBoxLayout()
        sliders_row.setSpacing(28)
        sliders_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.bands = [
            ("63 Hz", "Bass"),
            ("250 Hz", "Tief-Mitten"),
            ("1 kHz", "Mitten"),
            ("4 kHz", "Präsenz"),
            ("8 kHz", "Brillanz")
        ]
        self.sliders = []
        self.val_labels = []

        for freq, label in self.bands:
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.setSpacing(6)

            # Value indicator
            vlbl = QLabel("0.0 dB")
            vlbl.setStyleSheet("font-size: 11px; color: #00D2FF; font-weight: 600;")
            vlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(vlbl)
            self.val_labels.append(vlbl)

            # Vertical Slider (-6 to +6 dB, step 0.5)
            s = QSlider(Qt.Orientation.Vertical)
            s.setFixedHeight(140)
            s.setRange(-12, 12) # -6.0 to +6.0 dB in 0.5 steps
            s.setValue(0)
            s.valueChanged.connect(self._on_eq_slider_changed)
            col.addWidget(s, alignment=Qt.AlignmentFlag.AlignCenter)
            self.sliders.append(s)

            # Frequency Label
            flbl = QLabel(freq)
            flbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #FFFFFF;")
            flbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(flbl)

            # Desc Label
            dlbl = QLabel(label)
            dlbl.setStyleSheet("font-size: 10px; color: #64748B;")
            dlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(dlbl)

            sliders_row.addLayout(col)

        eq_layout.addLayout(sliders_row)
        layout.addWidget(eq_card)
        layout.addStretch()

        # Initialize default +6dB gain selection
        self._set_gain_val(6.0)

        # Default Neutral
        self.apply_preset("Neutral")

    def _set_gain_val(self, g: float):
        self.current_boost_gain = g
        for val, btn in self.gain_buttons.items():
            if abs(val - g) < 0.1:
                btn.setStyleSheet(f"background: {Theme.PRIMARY_GRADIENT}; color: #050B14; font-weight: 700; border: none; border-radius: 4px;")
            else:
                btn.setStyleSheet("")
        if self.cb_boost.isChecked():
            self.loudness_boost_changed.emit(True, self.current_boost_gain)

    def _on_boost_toggled(self, checked: bool):
        self.loudness_boost_changed.emit(checked, self.current_boost_gain)

    def set_boost_ui(self, enabled: bool, gain_db: float = 6.0):
        self.cb_boost.blockSignals(True)
        self.cb_boost.setChecked(enabled)
        self.cb_boost.blockSignals(False)
        self._set_gain_val(gain_db)

    def _on_bass_toggled(self, checked: bool):
        self.bass_boost_changed.emit(checked)

    def _on_spatial_toggled(self, checked: bool):
        self.spatial_audio_changed.emit(checked)

    def _on_eq_slider_changed(self):
        values = []
        for s, vlbl in zip(self.sliders, self.val_labels):
            db = s.value() * 0.5
            sign = "+" if db > 0 else ""
            vlbl.setText(f"{sign}{db:.1f} dB")
            values.append(db)
        self.eq_changed.emit(values)

    def apply_preset(self, name: str):
        if name in self.PRESETS:
            vals = self.PRESETS[name]
            for s, db in zip(self.sliders, vals):
                s.blockSignals(True)
                s.setValue(int(db / 0.5))
                s.blockSignals(False)
            self._on_eq_slider_changed()

            for n, b in self.preset_buttons.items():
                if n == name:
                    b.setStyleSheet(f"background: {Theme.PRIMARY_GRADIENT}; color: #050B14; font-weight: 700; border: none;")
                else:
                    b.setStyleSheet("")

    def set_bass_boost_ui(self, enabled: bool):
        self.cb_bass.blockSignals(True)
        self.cb_bass.setChecked(enabled)
        self.cb_bass.blockSignals(False)

    def update_state(self, state: dict):
        bb = state.get("bass_boost", False)
        self.set_bass_boost_ui(bb)

        bands = state.get("eq_bands", [12, 12, 12, 12, 12])
        last_sync = state.get("last_sync", "--:--:--")

        bb_str = "AKTIV (0x1089)" if bb else "AUS"
        self.hw_text.setText(f"Hardware-DSP: Bass-Boost {bb_str} • Hardware-EQ im Chip synchronisiert (0x1082)")
        self.hw_time.setText(f"Synchronisiert um {last_sync}")
