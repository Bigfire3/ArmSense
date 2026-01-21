# hardware/sensor_manager.py
import time
import board
import busio
import adafruit_bno055
import adafruit_tca9548a
from ArmSense.config import *
from ArmSense.utils import q_mult, q_conjugate

# Fallback für Config
try:
    JUMP_LIMIT = MAX_ANGLE_JUMP
except NameError:
    JUMP_LIMIT = 25.0 

try:
    OUTLIER_LIMIT = MAX_OUTLIERS
except NameError:
    OUTLIER_LIMIT = 5

class SensorManager:
    def __init__(self):
        self.sensors = {}
        self.offsets = {}
        self.dummy_mode = False
        self.is_calibrated = False 
        
        # Init Offsets with Identity Quaternion (w, x, y, z)
        for name in SENSOR_MAPPING.keys():
            self.offsets[name] = (1, 0, 0, 0)
        
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
            self.tca = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDRESS)
            self._init_sensors()
        except Exception as e:
            print(f"[HAL] Hardware Fehler: {e}")
            print("[HAL] Starte im Simulations-Modus")
            self.dummy_mode = True

        if not self.dummy_mode:
            print("[HAL] Warte auf Sensoren...")
            time.sleep(2.0)

        self.calibrate_zero() 

    def _init_sensors(self):
        for name, channel in SENSOR_MAPPING.items():
            try:
                print(f"[HAL] Init Sensor '{name}' auf Kanal {channel}...")
                bno = adafruit_bno055.BNO055_I2C(self.tca[channel], address=BNO_ADDRESS)
                self.sensors[name] = bno
            except Exception as e:
                print(f"[HAL] Fehler bei Sensor '{name}': {e}")

    def calibrate_zero(self):
        """Quaternion Calibration: Set current pose as identity (0,0,0)"""
        print("[HAL] Kalibriere Nullpunkt (Arm haengt)...")
        if self.dummy_mode: return

        for name, sensor in self.sensors.items():
            try:
                # Read raw quaternion
                q_raw = sensor.quaternion
                if q_raw and q_raw[0] is not None:
                    # offset = conjugate(raw) -> result = offset * raw = id
                    self.offsets[name] = q_conjugate(q_raw)
                    print(f"[HAL] {name} calibrated.")
                else:
                    print(f"[HAL] Warnung: Kein Wert von {name} fuer Kalibrierung.")
            except Exception as e:
                print(f"[HAL] Fehler bei Kalibrierung {name}: {e}")
        
        self.is_calibrated = True

    def get_data(self):
        data = {}
        # Dummy data: Identity quaternion (w=1)
        if self.dummy_mode: 
            return {
                "base": (1, 0, 0, 0), 
                "arm": (1, 0, 0, 0)
            }

        for name, sensor in self.sensors.items():
            try:
                # Get raw (w, x, y, z)
                q_raw = sensor.quaternion
                if q_raw and q_raw[0] is not None:
                    # Apply calibration: q_cal = q_offset * q_raw
                    offset = self.offsets.get(name, (1, 0, 0, 0))
                    q_cal = q_mult(offset, q_raw)
                    data[name] = q_cal
                else:
                    # Fallback to identity or last known? 
                    data[name] = (1, 0, 0, 0)
            except OSError:
                 data[name] = (1, 0, 0, 0)
        
        # Fill missing
        for name in SENSOR_MAPPING.keys():
            if name not in data: data[name] = (1, 0, 0, 0)
                
        return data
