# hardware/sensor_manager.py
import time
import board
import busio
import adafruit_bno055
import adafruit_tca9548a
from config import *

# Fallback für Config
try:
    JUMP_LIMIT = MAX_ANGLE_JUMP
except NameError:
    JUMP_LIMIT = 25.0 

class SensorManager:
    def __init__(self):
        self.sensors = {}
        self.offsets = {}
        self.dummy_mode = False
        
        # Speicher für Glitch-Filter
        self.last_valid_data = {}
        for name in SENSOR_MAPPING.keys():
            self.last_valid_data[name] = (0, 0, 0)
        
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA, frequency=I2C_FREQ)
            self.tca = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDRESS)
            self._init_sensors()
        except Exception as e:
            print(f"[HAL] Hardware Fehler: {e}")
            print("[HAL] Starte im Simulations-Modus")
            self.dummy_mode = True

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
        """Standard-Kalibrierung: Setzt aktuelle Position auf (0,0,0)"""
        print("[HAL] Kalibriere Nullpunkt (Arm haengt)...")
        self._calibrate_common(targets={"base": (0,0,0), "arm": (0,0,0)})

    def calibrate_reference_pose(self):
        """
        Referenz-Kalibrierung (Taste 1): 
        Setzt Base auf (0,0,0) und Arm auf (90,0,0)
        """
        print("[HAL] Kalibriere Referenz-Pose (Taste 1)...")
        # Hier definieren wir die Zielwerte für die aktuelle Haltung
        targets = {
            "base": (0, 0, 0),
            "arm":  (90, 0, 0)  # H=90, R=0, P=0
        }
        self._calibrate_common(targets)

    def _calibrate_common(self, targets):
        """Interne Hilfsfunktion für Kalibrierung"""
        if self.dummy_mode: return
        
        # Filter zurücksetzen, damit der Sprung zur neuen Pose nicht blockiert wird
        for name, target_val in targets.items():
            self.last_valid_data[name] = target_val

        for name, sensor in self.sensors.items():
            got_value = False
            attempts = 0
            target = targets.get(name, (0,0,0))

            while not got_value and attempts < 10:
                try:
                    euler = sensor.euler
                    if euler and len(euler) == 3 and euler[0] is not None:
                        # Offset Berechnung: Offset = Aktuell - Ziel
                        # Wir nutzen Modulo nicht hier, sondern bei der Ausgabe.
                        # Einfache Differenz reicht.
                        off_h = euler[0] - target[0]
                        off_r = euler[1] - target[1]
                        off_p = euler[2] - target[2]
                        
                        self.offsets[name] = (off_h, off_r, off_p)
                        print(f"[HAL] -> {name} kalibriert auf Ziel {target}")
                        got_value = True
                    else:
                        time.sleep(0.05)
                except OSError:
                    time.sleep(0.05)
                attempts += 1
            
            if not got_value:
                print(f"[HAL] WARNUNG: Konnte {name} nicht kalibrieren.")

    def _angle_diff(self, a, b):
        diff = abs(a - b)
        if diff > 180: diff = 360 - diff
        return diff

    def get_data(self):
        data = {}
        if self.dummy_mode: return {"base": (0,0,0), "arm": (0,0,0)}

        for name, sensor in self.sensors.items():
            last_vector = self.last_valid_data.get(name, (0,0,0))
            try:
                curr = sensor.euler
                if curr and curr[0] is not None:
                    off = self.offsets.get(name, (0,0,0))
                    
                    # (Aktuell - Offset) ergibt den Wert relativ zum Ziel
                    h = (curr[0] - off[0]) % 360
                    r = (curr[1] - off[1]) % 360
                    p = (curr[2] - off[2]) % 360
                    
                    if h > 180: h -= 360
                    if r > 180: r -= 360
                    if p > 180: p -= 360
                    
                    new_vector = (h, r, p)
                    
                    # Outlier Check
                    is_valid = True
                    for i in range(3):
                        if self._angle_diff(new_vector[i], last_vector[i]) > JUMP_LIMIT:
                            is_valid = False
                            break
                    
                    if is_valid:
                        self.last_valid_data[name] = new_vector
                        data[name] = new_vector
                    else:
                        data[name] = last_vector
                else:
                    data[name] = last_vector
            except OSError:
                data[name] = last_vector
        
        # Fill missing
        for name in SENSOR_MAPPING.keys():
            if name not in data: data[name] = (0,0,0)
                
        return data
