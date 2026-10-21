import subprocess
import os
import json
import logging
import wave
import math
import struct
from typing import Optional, Dict, List

logger = logging.getLogger("SpatialAudio")

EASYEFFECTS_DIR = os.path.expanduser("~/.local/share/easyeffects/output")

class AudioEngine:
    _current_eq: List[float] = [0.0, 0.0, 0.0, 0.0, 0.0]
    _spatial_enabled: bool = False
    _loudness_boost_enabled: bool = False
    _loudness_boost_gain: float = 6.0 # in dB

    @classmethod
    def init_presets(cls):
        """Ensures that base presets (Momentum_Off and Momentum_DSP) always exist."""
        try:
            os.makedirs(EASYEFFECTS_DIR, exist_ok=True)
            
            # 1. Momentum_Off: Empty preset to completely bypass all processing
            off_path = os.path.join(EASYEFFECTS_DIR, "Momentum_Off.json")
            off_preset = {
                "output": {
                    "blocklist": [],
                    "plugins_order": []
                }
            }
            with open(off_path, "w") as f:
                json.dump(off_preset, f, indent=2)

            # 2. Base Momentum_DSP
            dsp_path = os.path.join(EASYEFFECTS_DIR, "Momentum_DSP.json")
            if not os.path.exists(dsp_path):
                with open(dsp_path, "w") as f:
                    json.dump(off_preset, f, indent=2)
                    
            logger.info("Initialized EasyEffects base presets successfully")
        except Exception as e:
            logger.warning(f"Could not initialize EasyEffects presets: {e}")

    @staticmethod
    def get_master_volume() -> float:
        try:
            out = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], text=True)
            parts = out.strip().split()
            if len(parts) >= 2 and parts[0] == "Volume:":
                return float(parts[1])
        except Exception as e:
            logger.debug(f"Failed to get volume: {e}")
        return 1.0

    @staticmethod
    def set_master_volume(vol: float):
        # Allow up to 2.0 (200% volume overdrive)
        vol = max(0.0, min(2.0, vol))
        try:
            subprocess.run(["wpctl", "set-volume", "-l", "2.0", "@DEFAULT_AUDIO_SINK@", f"{vol:.2f}"], check=False)
        except Exception as e:
            logger.debug(f"Failed to set volume: {e}")

    @staticmethod
    def get_bluetooth_codec_info(mac: Optional[str] = None) -> Dict[str, str]:
        info = {
            "codec": "aptX",
            "rate": "48000 Hz",
            "format": "24-bit PCM"
        }
        try:
            out = subprocess.check_output(["pactl", "list", "sinks"], text=True)
            target = False
            mac_key = mac.replace(":", "_") if mac else None
            for line in out.splitlines():
                if (mac_key and mac_key in line) or "MOMENTUM" in line:
                    target = True
                if target:
                    if "api.bluez5.codec =" in line:
                        codec_val = line.split("=")[-1].strip().strip('"')
                        info["codec"] = codec_val.upper()
                    elif "Sample Specification:" in line:
                        parts = line.split(":")[-1].strip().split()
                        for p in parts:
                            if "Hz" in p:
                                info["rate"] = p
                            elif "s24" in p:
                                info["format"] = "24-bit"
                            elif "s16" in p:
                                info["format"] = "16-bit"
                    if "Name:" in line and target and not ((mac_key and mac_key in line) or "MOMENTUM" in line):
                        break
        except Exception as e:
            logger.debug(f"Error querying codec info: {e}")
        return info

    @classmethod
    def apply_dsp(cls):
        """Builds and loads the combined EasyEffects preset with active DSP components."""
        os.makedirs(EASYEFFECTS_DIR, exist_ok=True)
        plugins = []
        output_dict: Dict = {"blocklist": []}

        # 1. Equalizer plugin if any band != 0.0
        has_eq = any(abs(g) > 0.05 for g in cls._current_eq)
        if has_eq:
            freqs = [63.0, 250.0, 1000.0, 4000.0, 8000.0]
            bands = {}
            for i, (f, g) in enumerate(zip(freqs, cls._current_eq)):
                bands[f"band{i}"] = {
                    "frequency": f,
                    "gain": float(g),
                    "mode": "RLC (BT)",
                    "mute": False,
                    "q": 1.41,
                    "slope": "x1",
                    "solo": False,
                    "type": "Bell"
                }
            output_dict["equalizer"] = {
                "input-gain": 0.0,
                "output-gain": 0.0,
                "left": bands,
                "right": bands
            }
            plugins.append("equalizer")

        # 2. Stereo Widener (3D Spatializer / Atmos effect)
        if cls._spatial_enabled:
            output_dict["stereo_tools"] = {
                "stereo-base": 1.45,
                "s-level": 1.2
            }
            plugins.append("stereo_tools")

        # 3. Studio Loudness Overdrive (Preamp + Transparent Brickwall Limiter)
        if cls._loudness_boost_enabled:
            output_dict["preamp"] = {
                "input-gain": 0.0,
                "output-gain": float(cls._loudness_boost_gain)
            }
            plugins.append("preamp")

            output_dict["limiter"] = {
                "limit": -0.5,
                "lookahead": 5.0,
                "release": 20.0,
                "attack": 5.0
            }
            plugins.append("limiter")

        output_dict["plugins_order"] = plugins

        try:
            if not plugins:
                # Bypass completely
                subprocess.run(["easyeffects", "-l", "Momentum_Off"], check=False)
                logger.info("EasyEffects: All DSP plugins disabled (Momentum_Off)")
            else:
                dsp_path = os.path.join(EASYEFFECTS_DIR, "Momentum_DSP.json")
                with open(dsp_path, "w") as f:
                    json.dump({"output": output_dict}, f, indent=2)
                subprocess.run(["easyeffects", "-l", "Momentum_DSP"], check=False)
                logger.info(f"EasyEffects: Loaded Momentum_DSP with plugins {plugins}")
        except Exception as e:
            logger.warning(f"Failed to apply EasyEffects preset: {e}")

    @classmethod
    def set_equalizer(cls, values: List[float]):
        """Sets 5-band EQ values and updates the DSP pipeline."""
        if len(values) >= 5:
            cls._current_eq = [float(v) for v in values[:5]]
            cls.apply_dsp()

    @classmethod
    def toggle_spatial_audio(cls, enabled: bool) -> bool:
        """Toggles 3D Spatial Audio and instantly updates or removes stereo_tools from EasyEffects."""
        logger.info(f"Setting 3D Spatial Audio mode: {enabled}")
        cls._spatial_enabled = enabled
        cls.apply_dsp()
        return True

    @classmethod
    def toggle_loudness_boost(cls, enabled: bool, gain_db: float = 6.0) -> bool:
        """Toggles Studio Loudness Overdrive Maximizer (+6 dB to +12 dB with brickwall limiter)."""
        logger.info(f"Setting Loudness Boost mode: {enabled}, gain: +{gain_db} dB")
        cls._loudness_boost_enabled = enabled
        cls._loudness_boost_gain = float(gain_db)
        cls.apply_dsp()
        return True

    @classmethod
    def set_loudness_boost_gain(cls, gain_db: float):
        """Updates the loudness boost gain."""
        cls._loudness_boost_gain = float(gain_db)
        if cls._loudness_boost_enabled:
            cls.apply_dsp()

    @staticmethod
    def play_find_tone(earbud: str = "both"):
        """Plays an acoustic locator chirp on the specified earbud ('left', 'right', 'both')."""
        def _play():
            filename = f"/tmp/find_earbud_{earbud}.wav"
            sample_rate = 48000
            duration = 1.5
            n_samples = int(sample_rate * duration)
            try:
                with wave.open(filename, 'w') as wf:
                    wf.setnchannels(2)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    frames = bytearray()
                    for i in range(n_samples):
                        t = i / sample_rate
                        # Fast chirp tone sweeps from 800Hz to 1800Hz
                        f = 800 + 1000 * (t % 0.3) / 0.3
                        pulse = math.sin(2 * math.pi * 5 * t)
                        if pulse > 0:
                            s = int(32767 * 0.35 * math.sin(2 * math.pi * f * t))
                        else:
                            s = 0
                        l = s if earbud in ["left", "both"] else 0
                        r = s if earbud in ["right", "both"] else 0
                        frames.extend(struct.pack('<hh', l, r))
                    wf.writeframes(frames)
                subprocess.run(["pw-play", filename], check=False)
            except Exception as e:
                logger.warning(f"Error playing find tone: {e}")

        import threading
        threading.Thread(target=_play, daemon=True).start()

# Initialize base presets immediately
AudioEngine.init_presets()
