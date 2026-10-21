#!/usr/bin/env python3
import sys
import os
import datetime
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QSystemTrayIcon, QMenu, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction, QCloseEvent
from PyQt6.QtCore import Qt, QTimer

from ui.theme import Theme
from ui.sidebar import Sidebar
from ui.views.disconnected_view import DisconnectedView
from ui.views.dashboard_view import DashboardView
from ui.views.anc_view import AncView
from ui.views.sound_view import SoundView
from ui.views.smart_features_view import SmartFeaturesView
from ui.views.telemetry_view import TelemetryView
from ui.views.settings_view import SettingsView

from backend.bluez_monitor import BluezMonitor
from backend.fastpair_client import FastPairBatteryClient
from backend.gaia_client import GaiaClient
from audio.spatial_audio import AudioEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MomentumApp")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(APP_DIR, "resources", "icons", "momentum.png")

class MomentumMainWindow(QMainWindow):
    def __init__(self, start_in_tray: bool = False):
        super().__init__()
        self.setWindowTitle("Sennheiser MOMENTUM TW 5 Control")
        self.setMinimumSize(960, 680)
        self.resize(1050, 720)

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        # Central Root Stack
        self.root_stack = QStackedWidget(self)
        self.setCentralWidget(self.root_stack)

        # 1. Disconnected View (Index 0)
        self.disconnected_view = DisconnectedView(self)
        self.root_stack.addWidget(self.disconnected_view)

        # 2. Connected Main Container (Index 1)
        self.connected_widget = QWidget(self)
        conn_layout = QHBoxLayout(self.connected_widget)
        conn_layout.setContentsMargins(0, 0, 0, 0)
        conn_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.connected_widget)
        conn_layout.addWidget(self.sidebar)

        # Tab Stack
        self.tab_stack = QStackedWidget(self.connected_widget)
        conn_layout.addWidget(self.tab_stack)

        # Views
        self.dashboard_view = DashboardView(self)
        self.anc_view = AncView(self)
        self.sound_view = SoundView(self)
        self.smart_view = SmartFeaturesView(self) # Tab 3: Smart Features & Akku
        self.telemetry_view = TelemetryView(self) # Tab 4: Telemetrie & Logs
        self.settings_view = SettingsView(self)   # Tab 5: Allgemeine Einstellungen

        self.tab_stack.addWidget(self.dashboard_view) # Index 0
        self.tab_stack.addWidget(self.anc_view)       # Index 1
        self.tab_stack.addWidget(self.sound_view)     # Index 2
        self.tab_stack.addWidget(self.smart_view)     # Index 3
        self.tab_stack.addWidget(self.telemetry_view) # Index 4
        self.tab_stack.addWidget(self.settings_view)  # Index 5

        self.root_stack.addWidget(self.connected_widget)

        # Backends
        self.bluez = BluezMonitor(parent=self)
        self.fastpair = None
        self.gaia = None
        self.active_mac = None  # wird beim Verbinden aus BlueZ übernommen

        # Setup System Tray
        self._init_tray()

        # Wire Signals
        self._wire_signals()

        # Start with Disconnected state by default
        self.root_stack.setCurrentIndex(0)

        # Volume Watchdog Timer (every 500ms) to detect earbud volume hold gestures
        self.volume_timer = QTimer(self)
        self.volume_timer.timeout.connect(self._check_volume_sync)
        self.volume_timer.start(500)

        # MPRIS Media Watchdog to log Play/Pause & track changes from earbud touch
        self._init_mpris_monitor()

        # Initial BlueZ check
        QTimer.singleShot(200, self.bluez.check_status)

        if not start_in_tray:
            self.show()

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        if os.path.exists(ICON_PATH):
            self.tray.setIcon(QIcon(ICON_PATH))
        
        self.tray_menu = QMenu()
        
        act_open = QAction("Öffnen / Einblenden", self)
        act_open.triggered.connect(self.show_and_activate)
        self.tray_menu.addAction(act_open)

        self.tray_menu.addSeparator()

        act_anc = QAction("ANC Aktivieren", self)
        act_anc.triggered.connect(lambda: self._set_anc_mode("anc"))
        self.tray_menu.addAction(act_anc)

        act_trans = QAction("Transparenzmodus", self)
        act_trans.triggered.connect(lambda: self._set_anc_mode("transparency"))
        self.tray_menu.addAction(act_trans)

        act_off = QAction("Geräuschkontrolle Aus", self)
        act_off.triggered.connect(lambda: self._set_anc_mode("off"))
        self.tray_menu.addAction(act_off)

        self.tray_menu.addSeparator()

        act_quit = QAction("Beenden", self)
        act_quit.triggered.connect(self.quit_application)
        self.tray_menu.addAction(act_quit)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_activate()

    def show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _wire_signals(self):
        # Sidebar Navigation
        self.sidebar.tab_changed.connect(self._on_tab_changed)

        # Disconnected View
        self.disconnected_view.connect_clicked.connect(self.bluez.connect_device)

        # BlueZ Monitor
        self.bluez.connection_changed.connect(self._on_connection_changed)

        # Dashboard View
        self.dashboard_view.volume_changed.connect(AudioEngine.set_master_volume)
        self.dashboard_view.anc_mode_requested.connect(self._set_anc_mode)
        self.dashboard_view.loudness_boost_toggled.connect(self._on_dashboard_boost_toggled)

        # ANC View
        self.anc_view.mode_requested.connect(self._set_anc_mode)
        self.anc_view.transparency_level_changed.connect(self._on_transparency_level_changed)
        self.anc_view.anti_wind_changed.connect(self._on_anti_wind_changed)
        self.anc_view.adaptive_anc_changed.connect(self._on_adaptive_anc_changed)

        # Sound View
        self.sound_view.bass_boost_changed.connect(self._on_bass_boost_changed)
        self.sound_view.spatial_audio_changed.connect(AudioEngine.toggle_spatial_audio)
        self.sound_view.loudness_boost_changed.connect(self._on_sound_view_boost_changed)
        self.sound_view.eq_changed.connect(self._on_eq_changed)

        # Smart Features View
        self.smart_view.smart_pause_changed.connect(self._on_smart_pause_changed)
        self.smart_view.comfort_call_changed.connect(self._on_comfort_call_changed)
        self.smart_view.battery_protect_changed.connect(self._on_battery_protect_changed)
        self.smart_view.auto_power_off_changed.connect(self._on_auto_power_off_changed)
        self.smart_view.play_find_tone_requested.connect(AudioEngine.play_find_tone)

        # Settings View
        self.settings_view.disconnect_requested.connect(self.bluez.disconnect_device)
        self.settings_view.reconnect_requested.connect(self._refresh_hardware)
        self.settings_view.reset_eq_requested.connect(lambda: self.sound_view.apply_preset("Neutral"))
        self.settings_view.reset_dsp_requested.connect(self._on_reset_dsp_requested)

        # Telemetry View
        self.telemetry_view.sync_requested.connect(self._refresh_hardware)

    def _on_dashboard_boost_toggled(self, enabled: bool):
        gain = self.sound_view.current_boost_gain
        self.sound_view.set_boost_ui(enabled, gain)
        AudioEngine.toggle_loudness_boost(enabled, gain)
        self._log_boost_telemetry(enabled, gain)

    def _on_sound_view_boost_changed(self, enabled: bool, gain: float):
        self.dashboard_view.set_boost_ui_state(enabled)
        AudioEngine.toggle_loudness_boost(enabled, gain)
        self._log_boost_telemetry(enabled, gain)

    def _log_boost_telemetry(self, enabled: bool, gain: float):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.telemetry_view.add_telemetry_event({
            "timestamp": now_str,
            "category": "Audio-DSP",
            "cmd": "LOUDNESS",
            "title": f"Studio-Maximizer {'AKTIV (+%.1f dB)' % gain if enabled else 'DEAKTIVIERT'}",
            "message": f"Preamp +{gain:.1f} dB mit Lookahead-Limiter (Ceiling -0.5 dBFS)" if enabled else "Standardpegel wiederhergestellt",
            "level": "info"
        })

    def _on_reset_dsp_requested(self):
        AudioEngine.toggle_spatial_audio(False)
        AudioEngine.toggle_loudness_boost(False)
        self.sound_view.cb_spatial.setChecked(False)
        self.sound_view.set_boost_ui(False)
        self.dashboard_view.set_boost_ui_state(False)

    def _on_tab_changed(self, idx: int):
        target = min(idx, self.tab_stack.count() - 1)
        self.tab_stack.setCurrentIndex(target)

    def _on_connection_changed(self, connected: bool, info: dict):
        logger.info(f"Connection state updated: {connected}, {info}")
        self.sidebar.set_connected(connected)

        if connected:
            self.root_stack.setCurrentIndex(1)
            mac = info.get("mac", self.active_mac)
            self.active_mac = mac
            self.settings_view.set_device_mac(mac)

            # Start RFCOMM Streams
            if not self.fastpair:
                self.fastpair = FastPairBatteryClient(mac, channel=22, parent=self)
                self.fastpair.battery_stream_updated.connect(self._on_battery_stream)
                self.fastpair.start()

            if not self.gaia:
                self.gaia = GaiaClient(mac, parent=self)
                self.gaia.state_updated.connect(self._on_gaia_state)
                self.gaia.telemetry_received.connect(self.telemetry_view.add_telemetry_event)
                self.gaia.start()

            # Query Audio metrics
            codec_info = AudioEngine.get_bluetooth_codec_info(mac)
            self.sidebar.update_codec_info(codec_info["codec"], f"{codec_info['rate']} • {codec_info['format']}")
            self.settings_view.update_codec_info(codec_info["codec"], f"{codec_info['rate']} • {codec_info['format']}")
            
            # Sync volume
            current_vol = AudioEngine.get_master_volume()
            self.dashboard_view.set_volume_display(current_vol)

            self.tray.setToolTip(f"MOMENTUM TW 5: Verbunden ({codec_info['codec']})")
        else:
            self.root_stack.setCurrentIndex(0)
            self.disconnected_view.reset_button()
            
            if self.fastpair:
                self.fastpair.stop()
                self.fastpair = None
            if self.gaia:
                self.gaia.stop()
                self.gaia = None

            self.tray.setToolTip("MOMENTUM TW 5: Nicht verbunden")

    def _on_battery_stream(self, l_pct: int, l_chg: bool, r_pct: int, r_chg: bool, c_pct: int, c_chg: bool):
        self.dashboard_view.update_batteries(l_pct, l_chg, r_pct, r_chg, c_pct, c_chg)
        self.telemetry_view.update_batteries(l_pct, l_chg, r_pct, r_chg, c_pct, c_chg)
        
        # Log to telemetry terminal
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        l_s = f"{l_pct}%{' (⚡)' if l_chg else ''}" if l_pct >= 0 else "Standby"
        r_s = f"{r_pct}%{' (⚡)' if r_chg else ''}" if r_pct >= 0 else "Standby"
        c_s = f"{c_pct}%{' (⚡)' if c_chg else ''}" if c_pct >= 0 else "Standby"
        
        self.telemetry_view.add_telemetry_event({
            "timestamp": now_str,
            "category": "FastPair",
            "cmd": "0x0303",
            "title": "Akku-Telemetrie",
            "message": f"Links: {l_s}, Rechts: {r_s}, Ladecase: {c_s}",
            "level": "info"
        })

        self.tray.setToolTip(f"MOMENTUM TW 5\nL: {l_s} | R: {r_s} | Case: {c_s}")

    def _on_gaia_state(self, state: dict):
        self.anc_view.update_state(state)
        self.sound_view.update_state(state)
        self.smart_view.update_state(state)
        self.settings_view.update_state(state)
        self.telemetry_view.update_hardware_state(state)

        # Update dashboard quick controls
        mode = state.get("mode", "off")
        self.dashboard_view.set_anc_ui_mode(mode)

    def _set_anc_mode(self, mode: str):
        if not self.gaia:
            return
        trans_level = self.anc_view.trans_slider.value()
        self.gaia.set_noise_mode(mode, trans_level)
        self.dashboard_view.set_anc_ui_mode(mode)
        self.anc_view.set_ui_mode(mode)

    def _on_transparency_level_changed(self, level: int):
        if self.gaia:
            self.gaia.set_transparency_level(level)

    def _on_anti_wind_changed(self, mode: str):
        if self.gaia:
            self.gaia.set_anti_wind(mode)

    def _on_adaptive_anc_changed(self, enabled: bool):
        if self.gaia:
            self.gaia.set_adaptive_anc(enabled)

    def _on_bass_boost_changed(self, enabled: bool):
        if self.gaia:
            self.gaia.set_bass_boost(enabled)

    def _on_eq_changed(self, values: list):
        # 1. Update PipeWire/EasyEffects combined DSP preset
        AudioEngine.set_equalizer(values)
        # 2. Write straight to Qualcomm on-chip hardware EQ
        if self.gaia:
            for idx, val in enumerate(values[:5]):
                # Map -6.0 .. +6.0 dB to 0 .. 24 (12 is 0 dB)
                hw_val = int(round((val + 6.0) * 2.0))
                self.gaia.set_hardware_eq(idx, hw_val)

    def _on_smart_pause_changed(self, enabled: bool):
        if self.gaia:
            self.gaia.set_smart_pause(enabled)

    def _on_comfort_call_changed(self, enabled: bool):
        if self.gaia:
            self.gaia.set_comfort_call(enabled)

    def _on_battery_protect_changed(self, enabled: bool):
        if self.gaia:
            self.gaia.set_battery_protection(enabled)

    def _on_auto_power_off_changed(self, minutes: int):
        if self.gaia:
            self.gaia.set_auto_power_off(minutes)

    def _check_volume_sync(self):
        """Monitors system volume changes triggered by touching & holding the earbud buttons."""
        if self.root_stack.currentIndex() != 1:
            return
        current_vol = AudioEngine.get_master_volume()
        current_pct = int(round(current_vol * 100))
        displayed_pct = self.dashboard_view.vol_slider.value()

        if abs(current_pct - displayed_pct) >= 2:
            self.dashboard_view.set_volume_display(current_vol)
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.telemetry_view.add_telemetry_event({
                "timestamp": now_str,
                "category": "Touch-Taste",
                "cmd": "AVRCP",
                "title": "Lautstärke am Hörer geändert",
                "message": f"Lautstärke auf {current_pct}% angepasst",
                "level": "info"
            })

    def _init_mpris_monitor(self):
        """Monitors media player playback and title changes triggered by earbud touch buttons."""
        try:
            import dbus
            from dbus.mainloop.glib import DBusGMainLoop
            bus = dbus.SessionBus()

            def on_prop_changed(interface, changed_props, invalidated_props):
                if not self.gaia or not self.gaia.running:
                    return
                now_str = datetime.datetime.now().strftime("%H:%M:%S")
                if "PlaybackStatus" in changed_props:
                    status = str(changed_props["PlaybackStatus"])
                    self.telemetry_view.add_telemetry_event({
                        "timestamp": now_str,
                        "category": "Touch-Taste",
                        "cmd": "AVRCP",
                        "title": "Mediensteuerung am Hörer",
                        "message": f"Status: {status.upper()}",
                        "level": "info"
                    })
                elif "Metadata" in changed_props:
                    meta = changed_props["Metadata"]
                    title = meta.get("xesam:title", "")
                    artist = meta.get("xesam:artist", [""])[0] if isinstance(meta.get("xesam:artist"), list) else meta.get("xesam:artist", "")
                    if title:
                        self.telemetry_view.add_telemetry_event({
                            "timestamp": now_str,
                            "category": "Touch-Taste",
                            "cmd": "AVRCP",
                            "title": "Track gewechselt",
                            "message": f"{artist} - {title}" if artist else str(title),
                            "level": "info"
                        })

            bus.add_signal_receiver(
                on_prop_changed,
                dbus_interface="org.freedesktop.DBus.Properties",
                signal_name="PropertiesChanged",
                path="/org/mpris/MediaPlayer2"
            )
        except Exception as e:
            logger.debug(f"MPRIS monitor init note: {e}")

    def _refresh_hardware(self):
        if self.gaia:
            self.gaia.refresh_state()
        self.bluez.check_status()

    def closeEvent(self, event: QCloseEvent):
        if self.settings_view.cb_tray.isChecked():
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "MOMENTUM TW 5 Control",
                "Die App läuft im Hintergrund im System-Tray weiter.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.quit_application()

    def quit_application(self):
        if self.fastpair:
            self.fastpair.stop()
        if self.gaia:
            self.gaia.stop()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MomentumTWControl")
    app.setStyleSheet(Theme.STYLESHEET)

    start_in_tray = "--tray" in sys.argv or "--minimized" in sys.argv
    window = MomentumMainWindow(start_in_tray=start_in_tray)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
