import socket
import threading
import time
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger("FastPairClient")

class FastPairBatteryClient(QObject):
    # Signals: left_pct, left_chg, right_pct, right_chg, case_pct, case_chg
    battery_stream_updated = pyqtSignal(int, bool, int, bool, int, bool)
    status_changed = pyqtSignal(str)

    def __init__(self, mac: str, channel: int = 22, parent=None):
        super().__init__(parent)
        self.mac = mac
        self.channel = channel
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.sock: Optional[socket.socket] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            self.thread = None

    def _parse_battery_byte(self, b: int):
        if b == 0x7F:
            return -1, False # -1 indicates not present / unknown
        charging = bool(b & 0x80)
        percentage = b & 0x7F
        return percentage, charging

    def _run(self):
        logger.info(f"FastPair battery client starting on {self.mac} Ch {self.channel}")
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                self.sock.settimeout(3.0)
                self.sock.connect((self.mac, self.channel))
                self.status_changed.emit("Verbunden mit FastPair Stream")
                logger.info("Connected to FastPair RFCOMM stream")

                buffer = bytearray()
                while self.running:
                    try:
                        chunk = self.sock.recv(1024)
                        if not chunk:
                            break
                        buffer.extend(chunk)

                        # Process all frames in buffer
                        while len(buffer) >= 4:
                            grp = buffer[0]
                            code = buffer[1]
                            length = int.from_bytes(buffer[2:4], "big")
                            total_len = 4 + length
                            if len(buffer) < total_len:
                                break # Wait for more data
                            
                            payload = buffer[4:total_len]
                            buffer = buffer[total_len:]

                            if grp == 0x03 and code == 0x03 and len(payload) >= 3:
                                l_pct, l_chg = self._parse_battery_byte(payload[0])
                                r_pct, r_chg = self._parse_battery_byte(payload[1])
                                c_pct, c_chg = self._parse_battery_byte(payload[2])
                                logger.debug(f"Battery: L={l_pct}% (chg={l_chg}), R={r_pct}% (chg={r_chg}), Case={c_pct}% (chg={c_chg})")
                                self.battery_stream_updated.emit(l_pct, l_chg, r_pct, r_chg, c_pct, c_chg)

                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.debug(f"Socket read exception: {e}")
                        break

            except Exception as e:
                logger.debug(f"FastPair connect error: {e}")
                self.status_changed.emit("FastPair getrennt, erneuter Versuch...")
            finally:
                if self.sock:
                    try:
                        self.sock.close()
                    except Exception:
                        pass
                    self.sock = None

            if self.running:
                time.sleep(3.0) # Retry interval

        logger.info("FastPair client stopped")
