import logging
import os
import threading
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import dbus

logger = logging.getLogger("BluezMonitor")

class BluezMonitor(QObject):
    connection_changed = pyqtSignal(bool, dict)
    battery_changed = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, target_mac: Optional[str] = os.environ.get("MOMENTUM_TW_MAC"), parent=None):
        super().__init__(parent)
        self.target_mac = target_mac.upper() if target_mac else None
        self.bus = None
        self.device_path: Optional[str] = None
        self.device_obj = None
        self.props_iface = None
        self.device_iface = None
        self.is_connected = False
        self.device_info: Dict[str, Any] = {}

        self._init_dbus()

        # Polling Timer for rock-solid state sync every 1.5s
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.check_status)
        self.poll_timer.start(1500)

    def _init_dbus(self):
        try:
            self.bus = dbus.SystemBus()
            self._find_device()
        except Exception as e:
            logger.error(f"Failed to initialize D-Bus: {e}")
            self.error_occurred.emit(f"D-Bus Fehler: {e}")

    def _find_device(self):
        if not self.bus:
            return False
        try:
            manager = dbus.Interface(self.bus.get_object('org.bluez', '/'), 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()

            for path, ifaces in objects.items():
                dev = ifaces.get('org.bluez.Device1')
                if dev:
                    addr = str(dev.get('Address', '')).upper()
                    name = str(dev.get('Name', dev.get('Alias', '')))
                    # Match by MAC or Name
                    if (self.target_mac and addr == self.target_mac) or ('MOMENTUM TW' in name.upper()):
                        self.device_path = path
                        self.target_mac = addr
                        self.device_obj = self.bus.get_object('org.bluez', path)
                        self.props_iface = dbus.Interface(self.device_obj, 'org.freedesktop.DBus.Properties')
                        self.device_iface = dbus.Interface(self.device_obj, 'org.bluez.Device1')
                        logger.info(f"Bound to Sennheiser device at {path} ({name}, {addr})")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error finding device: {e}")
            return False

    def check_status(self):
        if not self.device_path or not self.props_iface:
            if not self._find_device():
                if self.is_connected:
                    self.is_connected = False
                    self.connection_changed.emit(False, {})
                return

        try:
            props = self.props_iface.GetAll('org.bluez.Device1')
            connected = bool(props.get('Connected', False))
            name = str(props.get('Name', props.get('Alias', 'MOMENTUM TW 5')))
            mac = str(props.get('Address', self.target_mac))
            icon = str(props.get('Icon', 'audio-headset'))
            
            # Check BlueZ Battery1 if available
            bat = None
            try:
                bat_props = self.props_iface.GetAll('org.bluez.Battery1')
                if 'Percentage' in bat_props:
                    bat = int(bat_props['Percentage'])
            except dbus.DBusException:
                pass

            info = {
                "name": name,
                "mac": mac,
                "icon": icon,
                "connected": connected,
                "battery": bat,
                "path": self.device_path
            }
            self.device_info = info

            if connected != self.is_connected:
                self.is_connected = connected
                logger.info(f"Connection state changed: {connected}")
                self.connection_changed.emit(connected, info)

            if bat is not None:
                self.battery_changed.emit(bat)

        except dbus.DBusException as e:
            if self.is_connected:
                self.is_connected = False
                self.connection_changed.emit(False, {})
            self.device_path = None
            self.props_iface = None

    def connect_device(self):
        if not self.device_iface:
            self._find_device()
        if self.device_iface:
            def _do_connect():
                try:
                    logger.info("Attempting BlueZ Connect()...")
                    self.device_iface.Connect()
                    logger.info("BlueZ Connect succeeded")
                    self.check_status()
                except Exception as e:
                    logger.warning(f"BlueZ Connect failed: {e}")
                    self.error_occurred.emit(str(e))
            threading.Thread(target=_do_connect, daemon=True).start()

    def disconnect_device(self):
        if self.device_iface:
            def _do_disconnect():
                try:
                    logger.info("Attempting BlueZ Disconnect()...")
                    self.device_iface.Disconnect()
                    logger.info("BlueZ Disconnect succeeded")
                    self.check_status()
                except Exception as e:
                    logger.warning(f"BlueZ Disconnect failed: {e}")
                    self.error_occurred.emit(str(e))
            threading.Thread(target=_do_disconnect, daemon=True).start()
