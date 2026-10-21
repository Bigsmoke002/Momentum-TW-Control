from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

class TelemetryCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setStyleSheet(f"""
            QFrame.Card {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
                padding: 10px 14px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        layout.addWidget(self.title_lbl)

        self.val_lbl = QLabel("--")
        self.val_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {Theme.PRIMARY};")
        layout.addWidget(self.val_lbl)

        self.sub_lbl = QLabel("Warte auf Hardware...")
        self.sub_lbl.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(self.sub_lbl)

    def set_data(self, val: str, sub: str, color: str = Theme.PRIMARY):
        self.val_lbl.setText(val)
        self.val_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {color};")
        self.sub_lbl.setText(sub)


class TelemetryView(QWidget):
    sync_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        v_h = QVBoxLayout()
        title = QLabel("Hardware-Telemetrie & Live-Diagnose")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        v_h.addWidget(title)

        subtitle = QLabel("Echtzeit-Rückmeldungen, Registerzustände und Protokoll-Stream der MOMENTUM TW 5.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED};")
        v_h.addWidget(subtitle)
        header.addLayout(v_h)
        header.addStretch()

        btn_sync = QPushButton("🔄 Hardware abfragen (Poll)")
        btn_sync.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sync.clicked.connect(self.sync_requested.emit)
        header.addWidget(btn_sync)

        layout.addLayout(header)

        # Cards Grid (2 rows x 4 cols)
        grid = QGridLayout()
        grid.setSpacing(10)

        self.c_mode = TelemetryCard("Geräuschkontrolle")
        self.c_wind = TelemetryCard("Wind-Reduktion")
        self.c_bass = TelemetryCard("Bass-Boost")
        self.c_eq = TelemetryCard("Hardware-DSP EQ")
        self.c_pause = TelemetryCard("Trageerkennung")
        self.c_protect = TelemetryCard("Akkupflege")
        self.c_power = TelemetryCard("Abschalt-Timer")
        self.c_battery = TelemetryCard("FastPair Akkus")

        grid.addWidget(self.c_mode, 0, 0)
        grid.addWidget(self.c_wind, 0, 1)
        grid.addWidget(self.c_bass, 0, 2)
        grid.addWidget(self.c_eq, 0, 3)
        grid.addWidget(self.c_pause, 1, 0)
        grid.addWidget(self.c_protect, 1, 1)
        grid.addWidget(self.c_power, 1, 2)
        grid.addWidget(self.c_battery, 1, 3)

        layout.addLayout(grid)

        # Live Protocol Terminal Header
        log_header = QHBoxLayout()
        log_title = QLabel("ECHTZEIT-PROTOKOLLSTREAM (RFCOMM & GAIA v3)")
        log_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        log_header.addWidget(log_title)
        log_header.addStretch()

        self.lbl_packet_count = QLabel("0 Pakete empfangen")
        self.lbl_packet_count.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        log_header.addWidget(self.lbl_packet_count)

        btn_clear = QPushButton("Log leeren")
        btn_clear.setFixedHeight(24)
        btn_clear.setStyleSheet(f"font-size: 11px; padding: 2px 10px; background: {Theme.BG_CARD}; border: 1px solid {Theme.BORDER};")
        btn_clear.clicked.connect(self._clear_log)
        log_header.addWidget(btn_clear)

        layout.addLayout(log_header)

        # Terminal Log Output
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet(f"""
            QTextEdit {{
                background-color: #060B12;
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                color: #E2E8F0;
                font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
                font-size: 11px;
                padding: 10px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(self.terminal, stretch=1)

        self.packet_count = 0

    def add_telemetry_event(self, event: dict):
        self.packet_count += 1
        self.lbl_packet_count.setText(f"{self.packet_count} Ereignisse")

        ts = event.get("timestamp", "--:--:--")
        cat = event.get("category", "Info")
        cmd = event.get("cmd", "")
        title = event.get("title", "")
        msg = event.get("message", "")
        lvl = event.get("level", "info")

        # Color mapping
        tag_color = "#00D2FF"
        if lvl == "success":
            tag_color = "#00E676"
        elif lvl == "warning":
            tag_color = "#FFD600"
        elif lvl == "error":
            tag_color = "#FF5252"

        line_html = (
            f"<span style='color: #64748B;'>[{ts}]</span> "
            f"<span style='color: {tag_color}; font-weight: 700;'>[{cat} {cmd}]</span> "
            f"<span style='color: #FFFFFF; font-weight: 600;'>{title}:</span> "
            f"<span style='color: #94A3B8;'>{msg}</span>"
        )
        self.terminal.append(line_html)
        
        # Scroll to bottom
        sb = self.terminal.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_hardware_state(self, state: dict):
        # 1. Mode
        anc = state.get("anc", False)
        trans_s = state.get("transparency_state", False)
        trans_lvl = state.get("transparency_level", 70)
        mode = state.get("mode", "off")

        if mode == "anc" or anc:
            self.c_mode.set_data("ANC Aktiv", "Außengeräusche eliminiert (0x1A85)", Theme.ACCENT_GREEN)
        elif mode == "transparency" or trans_s:
            self.c_mode.set_data(f"Transparenz {trans_lvl}%", f"Mikrofone aktiv (0x1901)", Theme.PRIMARY)
        else:
            self.c_mode.set_data("Passiv (Aus)", "Keine aktive Filterung (0x1B04)", "#94A3B8")

        # 2. Wind
        wind = state.get("anti_wind", "off").upper()
        self.c_wind.set_data(wind, "Windgeräuschfilter (0x1A81)", Theme.PRIMARY if wind != "OFF" else "#94A3B8")

        # 3. Bass Boost
        bb = state.get("bass_boost", False)
        self.c_bass.set_data("AKTIV" if bb else "AUS", "Hardware Sub-Bass (0x1089)", Theme.ACCENT_GREEN if bb else "#94A3B8")

        # 4. EQ Bands
        bands = state.get("eq_bands", [12, 12, 12, 12, 12])
        if len(bands) >= 5:
            dbs = [(b - 12) * 0.5 for b in bands[:5]]
            db_str = " | ".join(f"{g:+.1f}" for g in dbs)
            self.c_eq.set_data(f"[{db_str}] dB", "5-Band DSP (0x1082)", Theme.PRIMARY)

        # 5. Smart Pause
        sp = state.get("smart_pause", True)
        self.c_pause.set_data("AKTIV" if sp else "AUS", "Infrarot-Sensor (0x090D)", Theme.ACCENT_GREEN if sp else "#94A3B8")

        # 6. Battery Protect
        bp = state.get("battery_protect", False)
        self.c_protect.set_data("80% LIMIT" if bp else "STANDARD (100%)", "Zellenschutz (0x1113)", Theme.PRIMARY if bp else "#94A3B8")

        # 7. Auto Power Off
        apo = state.get("auto_power_off", 30)
        self.c_power.set_data(f"{apo} Min" if apo > 0 else "DEAKTIVIERT", "Standby-Timer (0x1114)", Theme.PRIMARY)

    def update_batteries(self, l_pct: int, l_chg: bool, r_pct: int, r_chg: bool, c_pct: int, c_chg: bool):
        l_s = f"{l_pct}%{'⚡' if l_chg else ''}" if l_pct >= 0 else "N/A"
        r_s = f"{r_pct}%{'⚡' if r_chg else ''}" if r_pct >= 0 else "N/A"
        c_s = f"{c_pct}%{'⚡' if c_chg else ''}" if c_pct >= 0 else "N/A"
        self.c_battery.set_data(f"L:{l_s} R:{r_s} C:{c_s}", "Google Fast Pair Stream (Ch 22)", Theme.PRIMARY)

    def _clear_log(self):
        self.terminal.clear()
        self.packet_count = 0
        self.lbl_packet_count.setText("0 Pakete empfangen")
