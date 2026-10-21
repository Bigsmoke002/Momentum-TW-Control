import os
import sys
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.theme import Theme

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "momentum-tw-control.desktop")
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SettingsView(QWidget):
    disconnect_requested = pyqtSignal()
    reconnect_requested = pyqtSignal()
    reset_eq_requested = pyqtSignal()
    reset_dsp_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._device_mac = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        title = QLabel("⚙️ Einstellungen & System-Verwaltung")
        title.setProperty("class", "Title")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("Desktop-Integration, System-Tray, Bluetooth-Verbindungsstatus & Hardware-Diagnose.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_MUTED};")
        layout.addWidget(subtitle)

        # Row 1: Desktop & Autostart Card + Bluetooth Actions Card
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        # Card 1: Desktop & Autostart
        auto_card = QFrame()
        auto_card.setProperty("class", "Card")
        ac_layout = QVBoxLayout(auto_card)
        ac_layout.setSpacing(12)

        ac_title = QLabel("DESKTOP-INTEGRATION & AUTOSTART")
        ac_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        ac_layout.addWidget(ac_title)

        self.cb_autostart = QCheckBox("Beim Systemstart im Hintergrund (Tray) ausführen")
        self.cb_autostart.setChecked(os.path.exists(AUTOSTART_FILE))
        self.cb_autostart.toggled.connect(self._on_autostart_toggled)
        ac_layout.addWidget(self.cb_autostart)

        as_desc = QLabel("Startet MOMENTUM Control unauffällig minimiert neben der KDE-Uhr.")
        as_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; margin-left: 24px;")
        as_desc.setWordWrap(True)
        ac_layout.addWidget(as_desc)

        self.cb_tray = QCheckBox("Beim Schließen [X] ins System-Tray minimieren")
        self.cb_tray.setChecked(True)
        ac_layout.addWidget(self.cb_tray)

        tray_desc = QLabel("Verhindert das versehentliche Beenden des Treibers und erhält Bluetooth-Sync.")
        tray_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED}; margin-left: 24px;")
        tray_desc.setWordWrap(True)
        ac_layout.addWidget(tray_desc)
        ac_layout.addStretch()

        row1.addWidget(auto_card)

        # Card 2: Bluetooth & Verbindung
        bt_card = QFrame()
        bt_card.setProperty("class", "Card")
        bc_layout = QVBoxLayout(bt_card)
        bc_layout.setSpacing(12)

        bc_title = QLabel("BLUETOOTH-VERWALTUNG")
        bc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        bc_layout.addWidget(bc_title)

        self.lbl_bt_status = QLabel("Status: --")
        self.lbl_bt_status.setStyleSheet("font-size: 13px; font-weight: 600; color: #00E676;")
        bc_layout.addWidget(self.lbl_bt_status)

        bt_desc = QLabel("Direkte BlueZ-Steuerung und Hardware-Synchronisation über PipeWire.")
        bt_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        bt_desc.setWordWrap(True)
        bc_layout.addWidget(bt_desc)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_resync = QPushButton("🔄 Re-Sync")
        self.btn_resync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_resync.setStyleSheet("padding: 6px 10px; font-size: 12px;")
        self.btn_resync.clicked.connect(self.reconnect_requested.emit)
        btn_row.addWidget(self.btn_resync)

        self.btn_open_bt = QPushButton("Bluetooth")
        self.btn_open_bt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_bt.setStyleSheet("padding: 6px 10px; font-size: 12px;")
        self.btn_open_bt.clicked.connect(self._open_system_bluetooth)
        btn_row.addWidget(self.btn_open_bt)

        self.btn_disconnect = QPushButton("Trennen")
        self.btn_disconnect.setProperty("class", "Danger")
        self.btn_disconnect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_disconnect.setStyleSheet("padding: 6px 10px; font-size: 12px;")
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)
        btn_row.addWidget(self.btn_disconnect)

        bc_layout.addLayout(btn_row)
        bc_layout.addStretch()

        row1.addWidget(bt_card)
        layout.addLayout(row1)

        # Row 2: Hardware- & Audio-Diagnose Table
        diag_card = QFrame()
        diag_card.setProperty("class", "Card")
        dc_layout = QVBoxLayout(diag_card)
        dc_layout.setSpacing(12)

        dc_header = QHBoxLayout()
        dc_title = QLabel("SYSTEM- & HARDWARE-DIAGNOSE")
        dc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        dc_header.addWidget(dc_title)
        dc_header.addStretch()

        self.lbl_diag_sync = QLabel("Letzter Sync: --:--:--")
        self.lbl_diag_sync.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        dc_header.addWidget(self.lbl_diag_sync)
        dc_layout.addLayout(dc_header)

        # Diagnostic Table
        self.table = QTableWidget(6, 2)
        self.table.setFixedHeight(210)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalHeaderLabels(["Parameter", "Aktueller Wert"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Theme.BG_DARK};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                gridline-color: {Theme.BORDER};
                color: #FFFFFF;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {Theme.BG_CARD_HOVER};
                color: #94A3B8;
                padding: 6px;
                font-weight: 700;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)

        diag_items = [
            ("Gerätemodell", "Sennheiser MOMENTUM True Wireless 5"),
            ("Bluetooth MAC-Adresse", "--"),
            ("Aktiver Audio-Codec", "Qualcomm aptX (48 kHz / 24-bit)"),
            ("Audio-Server", "PipeWire / WirePlumber"),
            ("Qualcomm GAIA v3 Kanal", "RFCOMM Kanal 12 (Befehle & ANC/Transparenz)"),
            ("Google FastPair Kanal", "RFCOMM Kanal 22 (Echtzeit Akku-Stream)")
        ]

        for row, (k, v) in enumerate(diag_items):
            item_k = QTableWidgetItem(k)
            item_k.setForeground(Qt.GlobalColor.white)
            item_v = QTableWidgetItem(v)
            item_v.setForeground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 0, item_k)
            self.table.setItem(row, 1, item_v)

        dc_layout.addWidget(self.table)
        layout.addWidget(diag_card)

        # Row 3: Maintenance & DSP Reset Card
        reset_card = QFrame()
        reset_card.setProperty("class", "Card")
        rc_layout = QHBoxLayout(reset_card)
        rc_layout.setSpacing(14)

        rc_v = QVBoxLayout()
        rc_title = QLabel("DSP & WERKSEINSTELLUNGEN ZURÜCKSETZEN")
        rc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 1px;")
        rc_v.addWidget(rc_title)

        rc_desc = QLabel("Setzt Hardware-Equalizer und EasyEffects-Filterprofile bei Fehlkonfigurationen zurück.")
        rc_desc.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MUTED};")
        rc_v.addWidget(rc_desc)
        rc_layout.addLayout(rc_v)
        rc_layout.addStretch()

        self.btn_reset_eq = QPushButton("EQ auf Neutral (0.0 dB)")
        self.btn_reset_eq.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_eq.clicked.connect(self.reset_eq_requested.emit)
        rc_layout.addWidget(self.btn_reset_eq)

        self.btn_reset_dsp = QPushButton("EasyEffects Reset")
        self.btn_reset_dsp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_dsp.clicked.connect(self.reset_dsp_requested.emit)
        rc_layout.addWidget(self.btn_reset_dsp)

        layout.addWidget(reset_card)
        layout.addStretch()

        # Write autostart file by default if not present
        if not os.path.exists(AUTOSTART_FILE):
            self._write_autostart_entry(True)

    def _open_system_bluetooth(self):
        """Attempts to open the desktop Bluetooth settings."""
        commands = [
            ["kcmshell6", "kcm_bluetooth"],
            ["kcmshell5", "kcm_bluetooth"],
            ["blueman-manager"],
            ["gnome-control-center", "bluetooth"]
        ]
        for cmd in commands:
            if shutil.which(cmd[0]):
                try:
                    subprocess.Popen(cmd)
                    return
                except Exception:
                    pass

    def _on_autostart_toggled(self, checked: bool):
        self._write_autostart_entry(checked)

    def _write_autostart_entry(self, enable: bool):
        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        if enable:
            entry = """[Desktop Entry]
Name=MOMENTUM TW Control
Comment=Sennheiser MOMENTUM True Wireless 5 Background Service
Exec={python} {app_dir}/app.py --tray
Icon={app_dir}/resources/icons/momentum.png
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Settings;
X-KDE-autostart-after=panel
""".format(python=sys.executable, app_dir=APP_DIR)
            try:
                with open(AUTOSTART_FILE, "w") as f:
                    f.write(entry)
            except Exception:
                pass
        else:
            if os.path.exists(AUTOSTART_FILE):
                try:
                    os.remove(AUTOSTART_FILE)
                except Exception:
                    pass

    def update_state(self, state: dict):
        last_sync = state.get("last_sync", "--:--:--")
        self.lbl_diag_sync.setText(f"Letzter Sync: {last_sync}")
        if state.get("connected", True):
            self.lbl_bt_status.setText(f"Status: Verbunden ({self._device_mac or '--'})")
            self.lbl_bt_status.setStyleSheet("font-size: 13px; font-weight: 600; color: #00E676;")
        else:
            self.lbl_bt_status.setText("Status: Getrennt")
            self.lbl_bt_status.setStyleSheet("font-size: 13px; font-weight: 600; color: #FF5252;")

    def set_device_mac(self, mac: str):
        """MAC-Adresse des erkannten Geräts anzeigen (nicht mehr fest im Code)"""
        self._device_mac = mac
        self.table.setItem(1, 1, QTableWidgetItem(mac or "--"))

    def update_codec_info(self, codec: str, rate: str):
        item = QTableWidgetItem(f"{codec} ({rate})")
        item.setForeground(Qt.GlobalColor.cyan)
        self.table.setItem(2, 1, item)
