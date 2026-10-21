import socket
import threading
import queue
import time
import datetime
import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger("GaiaClient")

MAGIC = b"\xFF\x03"
VENDOR_SENNHEISER = 0x0495

# Command IDs (Sennheiser Momentum GAIA v3)
CMD_REGISTER_NOTIFICATION = 0x0007

# Equalizer & Bass Boost
CMD_SET_EQ_PARAM = 0x1001
CMD_GET_EQ_PARAM = 0x1002
CMD_SET_BASS_BOOST = 0x1008
CMD_GET_BASS_BOOST = 0x1009

# Battery Protection & Timer
CMD_SET_BATTERY_PROTECT = 0x1013
CMD_GET_BATTERY_PROTECT = 0x1013
CMD_SET_AUTO_POWER_OFF = 0x1014
CMD_GET_AUTO_POWER_OFF = 0x1014

# Transparent-Hearing (Group 0x18xx)
CMD_SET_TRANSPARENT_HEARING = 0x1804
CMD_GET_TRANSPARENT_HEARING = 0x1805

# ANC & Modes (Group 0x1Axx)
CMD_SET_MODE = 0x1A00
CMD_GET_MODE = 0x1A01
CMD_SET_TRANSPARENCY_LEVEL = 0x1A02
CMD_GET_TRANSPARENCY_LEVEL = 0x1A03
CMD_SET_ANC_STATUS = 0x1A04
CMD_GET_ANC_STATUS = 0x1A05

# Smart Sensors & Calling (Group 0x08xx)
CMD_SET_SMART_PAUSE = 0x080C
CMD_GET_SMART_PAUSE = 0x080D
CMD_SET_COMFORT_CALL = 0x0814
CMD_GET_COMFORT_CALL = 0x0815


class GaiaClient(QObject):
    state_updated = pyqtSignal(dict)
    telemetry_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, mac: str, channels=(12, 13), parent=None):
        super().__init__(parent)
        self.mac = mac
        self.channels = channels
        self.sock: Optional[socket.socket] = None
        self.running = False
        
        self.send_lock = threading.Lock()
        self.cmd_queue = queue.Queue()
        
        self.reader_thread: Optional[threading.Thread] = None
        self.worker_thread: Optional[threading.Thread] = None
        self._watchdog_counter = 0
        self._watchdog_pause_until = 0.0

        self.state: Dict[str, Any] = {
            "mode": "anc", # "anc", "transparency", "off"
            "anc": True,
            "transparency_state": False,
            "transparency_level": 70,
            "anti_wind": "off",
            "adaptive_anc": False,
            "bass_boost": False,
            "eq_bands": [12, 12, 12, 12, 12],
            "smart_pause": True,
            "comfort_call": False,
            "battery_protect": False,
            "auto_power_off": 30,
            "last_sync": "--:--:--"
        }

    def start(self):
        if self.running:
            return
        self.running = True
        self.worker_thread = threading.Thread(target=self._connection_worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.running = False
        self.cmd_queue.put(None)
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.connection_changed.emit(False)

    def _build_packet(self, cmd: int, payload: bytes = b"") -> bytes:
        return MAGIC + len(payload).to_bytes(2, "big") + VENDOR_SENNHEISER.to_bytes(2, "big") + cmd.to_bytes(2, "big") + payload

    def _send_packet(self, cmd: int, payload: bytes = b""):
        """Sends a packet asynchronously without blocking the caller."""
        if not self.sock or not self.running:
            return
        try:
            pkt = self._build_packet(cmd, payload)
            with self.send_lock:
                self.sock.sendall(pkt)
        except Exception as e:
            logger.warning(f"Error sending GAIA cmd 0x{cmd:04X}: {e}")

    def _connection_worker(self):
        while self.running:
            if not self.sock:
                connected = False
                for ch in self.channels:
                    try:
                        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                        s.settimeout(3.0)
                        s.connect((self.mac, ch))
                        s.settimeout(None)
                        self.sock = s
                        logger.info(f"Connected to GAIA on RFCOMM Ch {ch}")
                        connected = True
                        break
                    except Exception:
                        try:
                            s.close()
                        except Exception:
                            pass
                
                if not connected:
                    time.sleep(3.0)
                    continue

                # Start Reader Thread
                self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
                self.reader_thread.start()
                self.connection_changed.emit(True)

                self._emit_telemetry("System", "0x0001", "Verbindung hergestellt", f"GAIA v3 Kanal {ch} aktiv", "success")

                # Initial full state fetch
                self._fetch_all_state()

            # Process command queue: drain all pending commands with small 40ms gap
            try:
                item = self.cmd_queue.get(timeout=0.6)
                if item is None:
                    continue
                cmd, payload = item
                self._send_packet(cmd, payload)

                # Drain remaining queued commands immediately
                while not self.cmd_queue.empty():
                    time.sleep(0.04)
                    nxt = self.cmd_queue.get_nowait()
                    if nxt is not None:
                        c, p = nxt
                        self._send_packet(c, p)

            except queue.Empty:
                # Watchdog polling cycle when idle
                self._poll_watchdog()
            except Exception as e:
                logger.warning(f"Error in GAIA worker queue: {e}")

    def _poll_watchdog(self):
        """Asynchronously triggers state queries. Responses are handled in _reader_loop."""
        if not self.sock or not self.running:
            return

        # Do NOT poll if user recently clicked a command
        if time.time() < self._watchdog_pause_until:
            return

        # Poll Transparent-Hearing (0x1805) and ANC (0x1A05) to detect earbud touch button presses
        self._send_packet(CMD_GET_TRANSPARENT_HEARING)
        time.sleep(0.04)
        self._send_packet(CMD_GET_ANC_STATUS)

        # Secondary check every 6 cycles (~4s)
        self._watchdog_counter += 1
        if self._watchdog_counter % 6 == 0:
            time.sleep(0.04)
            self._send_packet(CMD_GET_TRANSPARENCY_LEVEL)
            time.sleep(0.04)
            self._send_packet(CMD_GET_BASS_BOOST)
            time.sleep(0.04)
            self._send_packet(CMD_GET_MODE)

    def _reader_loop(self):
        buf = bytearray()
        logger.info("GAIA Reader thread started")
        while self.running and self.sock:
            try:
                chunk = self.sock.recv(1024)
                if not chunk:
                    logger.info("GAIA socket closed by peer")
                    break
                buf.extend(chunk)

                while len(buf) >= 8:
                    if buf[:2] != MAGIC:
                        idx = buf.find(MAGIC, 1)
                        if idx == -1:
                            buf.clear()
                            break
                        buf = buf[idx:]
                        continue

                    plen = int.from_bytes(buf[2:4], "big")
                    tot = 8 + plen
                    if len(buf) < tot:
                        break

                    cmd = int.from_bytes(buf[6:8], "big")
                    payload = bytes(buf[8:tot])
                    buf = buf[tot:]

                    try:
                        self._handle_incoming_packet(cmd, payload)
                    except Exception as pe:
                        logger.error(f"Error handling GAIA packet 0x{cmd:04X}: {pe}", exc_info=True)

            except Exception as e:
                logger.warning(f"GAIA socket read exception: {e}")
                break

        logger.info("GAIA Reader thread finished")
        if self.running:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.connection_changed.emit(False)

    def _emit_telemetry(self, cat: str, cmd_hex: str, title: str, message: str, level: str = "info"):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        event = {
            "timestamp": now_str,
            "category": cat,
            "cmd": cmd_hex,
            "title": title,
            "message": message,
            "level": level
        }
        self.telemetry_received.emit(event)

    def _handle_incoming_packet(self, cmd: int, payload: bytes):
        cmd_hex = f"0x{cmd:04X}"
        updated = False

        # Command Execution ACKs (empty payload) - ignore so they do not corrupt parsed state
        if cmd in (0x1904, 0x1B02, 0x1B04, 0x1B00, 0x1108, 0x1101, 0x090C, 0x0914):
            return

        # Transparent-Hearing Response (0x1905) or Notification (0x1885)
        if cmd in (0x1905, 0x1885):
            val = bool(payload[0]) if payload else False
            old_th = self.state["transparency_state"]
            self.state["transparency_state"] = val

            if val:
                self.state["mode"] = "transparency"
            else:
                if self.state["anc"]:
                    self.state["mode"] = "anc"
                else:
                    self.state["mode"] = "off"

            if val != old_th:
                self._emit_telemetry("Touch-Taste", cmd_hex, "Transparenz geändert", "Transparenzmodus AKTIV" if val else "Transparenzmodus AUS", "success")
            updated = True

        # ANC Status Response (0x1B05) or Notification (0x1A85)
        elif cmd in (0x1A85, 0x1B05):
            val = bool(payload[0]) if payload else False
            old_anc = self.state["anc"]
            self.state["anc"] = val

            if not val:
                if not self.state["transparency_state"]:
                    self.state["mode"] = "off"
            else:
                if not self.state["transparency_state"]:
                    self.state["mode"] = "anc"

            if val != old_anc:
                self._emit_telemetry("Touch-Taste", cmd_hex, "ANC-Status geändert", "ANC AKTIV" if val else "ANC AUS (Passiv)", "success")
            updated = True

        # Transparency Level Response (0x1B03) or Notification (0x1A83)
        elif cmd in (0x1B03, 0x1A83):
            val = int(payload[0]) if payload else 70
            if val > 0:
                self.state["transparency_level"] = val
                self._emit_telemetry("Transparenz", cmd_hex, "Pegel synchronisiert", f"Transparenz auf {val}%", "info")
                updated = True

        # Modes Response (0x1B01) or Notification (0x1A81)
        elif cmd in (0x1A81, 0x1B01):
            i = 0
            while i + 1 < len(payload):
                feat = payload[i]
                fval = payload[i+1]
                if feat == 0x01: # Anti-wind
                    w_map = {0: "off", 1: "max", 2: "auto"}
                    self.state["anti_wind"] = w_map.get(fval, "off")
                    self._emit_telemetry("Modus", cmd_hex, "Anti-Wind bestätigt", f"Anti-Wind: {self.state['anti_wind'].upper()}", "info")
                elif feat == 0x03: # Adaptive ANC
                    self.state["adaptive_anc"] = bool(fval)
                    self._emit_telemetry("Modus", cmd_hex, "Adaptives ANC bestätigt", "Adaptives ANC AKTIV" if fval else "Adaptives ANC AUS", "info")
                i += 2
            updated = True

        # Bass Boost Ack (0x1109) or Notification (0x1089)
        elif cmd in (0x1089, 0x1109):
            val = bool(payload[0]) if payload else False
            old_bb = self.state["bass_boost"]
            self.state["bass_boost"] = val
            if val != old_bb:
                self._emit_telemetry("Klang", cmd_hex, "Bass-Boost bestätigt", "Hardware Bass-Boost AKTIV" if val else "Hardware Bass-Boost AUS", "success" if val else "info")
            updated = True

        # Equalizer Bands Ack (0x1102) or Notification (0x1082)
        elif cmd in (0x1082, 0x1102):
            if len(payload) >= 5:
                self.state["eq_bands"] = list(payload[:5])
                dbs = [(b - 12) * 0.5 for b in self.state["eq_bands"]]
                db_str = ", ".join(f"{g:+.1f}dB" for g in dbs)
                self._emit_telemetry("Klang", cmd_hex, "Hardware-EQ synchronisiert", f"DSP: [{db_str}]", "success")
                updated = True

        # Smart Pause Ack (0x090D)
        elif cmd == 0x090D:
            val = bool(payload[0]) if payload else True
            self.state["smart_pause"] = val
            updated = True

        # Comfort Call Ack (0x0915)
        elif cmd == 0x0915:
            val = bool(payload[0]) if payload else False
            self.state["comfort_call"] = val
            updated = True

        # Battery Protect Ack (0x1113)
        elif cmd == 0x1113:
            val = bool(payload[1]) if len(payload) >= 2 else bool(payload[0]) if payload else False
            self.state["battery_protect"] = val
            updated = True

        # Auto Power Off Ack (0x1114)
        elif cmd == 0x1114:
            mins = int.from_bytes(payload[:2], "big") if len(payload) >= 2 else 30
            self.state["auto_power_off"] = mins
            updated = True

        if updated:
            self.state["last_sync"] = datetime.datetime.now().strftime("%H:%M:%S")
            self.state_updated.emit(dict(self.state))

    def _fetch_all_state(self):
        # Asynchronously send queries for all registers
        self._send_packet(CMD_GET_TRANSPARENT_HEARING)
        time.sleep(0.04)
        self._send_packet(CMD_GET_ANC_STATUS)
        time.sleep(0.04)
        self._send_packet(CMD_GET_TRANSPARENCY_LEVEL)
        time.sleep(0.04)
        self._send_packet(CMD_GET_MODE)
        time.sleep(0.04)
        self._send_packet(CMD_GET_BASS_BOOST)
        time.sleep(0.04)
        self._send_packet(CMD_GET_EQ_PARAM, bytes([0]))
        time.sleep(0.04)
        self._send_packet(CMD_GET_SMART_PAUSE)
        time.sleep(0.04)
        self._send_packet(CMD_GET_COMFORT_CALL)
        time.sleep(0.04)
        self._send_packet(CMD_GET_BATTERY_PROTECT)
        time.sleep(0.04)
        self._send_packet(CMD_GET_AUTO_POWER_OFF)

    def set_noise_mode(self, mode: str, transparency_level: int = 70):
        """
        Exclusive 3-way noise control on Sennheiser MOMENTUM:
        - 'transparency': Transparent-Hearing ON (0x1804=1), ANC DSP ON (0x1A04=1), Level (0x1A02=level)
        - 'anc': Transparent-Hearing OFF (0x1804=0), ANC DSP ON (0x1A04=1)
        - 'off': Transparent-Hearing OFF (0x1804=0), ANC DSP OFF (0x1A04=0)
        """
        level = max(10, min(100, int(transparency_level)))
        logger.info(f"Queuing Set Noise Mode: {mode} (trans_level={level})")
        self.state["mode"] = mode
        # Pause watchdog for 2.5 seconds to allow hardware to switch cleanly
        self._watchdog_pause_until = time.time() + 2.5

        if mode == "transparency":
            self.state["transparency_state"] = True
            self.state["anc"] = True
            self.state["transparency_level"] = level
            self.cmd_queue.put((CMD_SET_ANC_STATUS, bytes([1])))
            self.cmd_queue.put((CMD_SET_TRANSPARENCY_LEVEL, bytes([level])))
            self.cmd_queue.put((CMD_SET_TRANSPARENT_HEARING, bytes([1])))
            self._emit_telemetry("Befehl", "0x1804", "Transparenz aktivieren", f"Sende Transparenz=1 ({level}%), ANC=1", "info")

        elif mode == "anc":
            self.state["transparency_state"] = False
            self.state["anc"] = True
            self.cmd_queue.put((CMD_SET_TRANSPARENT_HEARING, bytes([0])))
            self.cmd_queue.put((CMD_SET_ANC_STATUS, bytes([1])))
            self._emit_telemetry("Befehl", "0x1A04", "ANC aktivieren", "Sende ANC=1, Transparenz=0", "info")

        else: # "off"
            self.state["transparency_state"] = False
            self.state["anc"] = False
            self.cmd_queue.put((CMD_SET_TRANSPARENT_HEARING, bytes([0])))
            self.cmd_queue.put((CMD_SET_ANC_STATUS, bytes([0])))
            self._emit_telemetry("Befehl", "0x1A04", "Geräuschkontrolle Aus", "Sende ANC=0, Transparenz=0 (Passiv)", "info")

        self.state_updated.emit(dict(self.state))

    def set_transparency_level(self, level: int):
        level = max(0, min(100, int(level)))
        self.state["transparency_level"] = level
        self._watchdog_pause_until = time.time() + 1.5
        if self.state["mode"] == "transparency":
            self.cmd_queue.put((CMD_SET_TRANSPARENCY_LEVEL, bytes([level])))
            self._emit_telemetry("Befehl", "0x1A02", "Transparenz-Pegel", f"Setze Transparenz auf {level}%", "info")
        self.state_updated.emit(dict(self.state))

    def set_anti_wind(self, mode: str):
        val = 0
        if mode == "max":
            val = 1
        elif mode == "auto":
            val = 2
        self.state["anti_wind"] = mode
        self.cmd_queue.put((CMD_SET_MODE, bytes([0x01, val])))
        self._emit_telemetry("Befehl", "0x1A00", "Anti-Wind ändern", f"Setze Anti-Wind auf {mode.upper()}", "info")
        self.state_updated.emit(dict(self.state))

    def set_adaptive_anc(self, enabled: bool):
        self.state["adaptive_anc"] = enabled
        self.cmd_queue.put((CMD_SET_MODE, bytes([0x03, 1 if enabled else 0])))
        self._emit_telemetry("Befehl", "0x1A00", "Adaptives ANC", f"Setze Adaptives ANC auf {enabled}", "info")
        self.state_updated.emit(dict(self.state))

    def set_bass_boost(self, enabled: bool):
        self.state["bass_boost"] = enabled
        self.cmd_queue.put((CMD_SET_BASS_BOOST, bytes([1 if enabled else 0])))
        self._emit_telemetry("Befehl", "0x1008", "Bass-Boost", f"Setze Hardware Bass-Boost auf {enabled}", "info")
        self.state_updated.emit(dict(self.state))

    def set_hardware_eq(self, band_idx: int, val: int):
        val = max(0, min(24, int(val)))
        self.cmd_queue.put((CMD_SET_EQ_PARAM, bytes([band_idx, val])))
        self._emit_telemetry("Befehl", "0x1001", "Hardware-EQ", f"Band {band_idx} = {val} ({(val-12)*0.5:+.1f}dB)", "info")

    def set_smart_pause(self, enabled: bool):
        self.state["smart_pause"] = enabled
        self.cmd_queue.put((CMD_SET_SMART_PAUSE, bytes([1 if enabled else 0])))
        self._emit_telemetry("Befehl", "0x080C", "Smart Pause", f"Setze Trageerkennung auf {enabled}", "info")
        self.state_updated.emit(dict(self.state))

    def set_comfort_call(self, enabled: bool):
        self.state["comfort_call"] = enabled
        self.cmd_queue.put((CMD_SET_COMFORT_CALL, bytes([1 if enabled else 0])))
        self._emit_telemetry("Befehl", "0x0814", "Comfort Call", f"Setze Comfort Call auf {enabled}", "info")
        self.state_updated.emit(dict(self.state))

    def set_battery_protection(self, enabled: bool):
        self.state["battery_protect"] = enabled
        self.cmd_queue.put((CMD_SET_BATTERY_PROTECT, bytes([0x00, 1 if enabled else 0])))
        self._emit_telemetry("Befehl", "0x1013", "Akkuschutz", f"Setze Akkuschutz auf {enabled}", "info")
        self.state_updated.emit(dict(self.state))

    def set_auto_power_off(self, minutes: int):
        self.state["auto_power_off"] = minutes
        self.cmd_queue.put((CMD_SET_AUTO_POWER_OFF, minutes.to_bytes(2, "big")))
        self._emit_telemetry("Befehl", "0x1014", "Auto Power-Off", f"Setze Abschalt-Timer auf {minutes} Min", "info")
        self.state_updated.emit(dict(self.state))

    def refresh_state(self):
        self._emit_telemetry("Sync", "0x0002", "Hardware-Abfrage", "Lese alle Register neu aus...", "info")
        self._fetch_all_state()
