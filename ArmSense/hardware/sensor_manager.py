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

try:
    OUTLIER_LIMIT = MAX_OUTLIERS
except NameError:
    OUTLIER_LIMIT = 5

class SensorManager:
    def __init__(self):
        self.sensors = {}
        self.offsets = {}
        self.dummy_mode = False
        self.is_calibrated = False # Flag für abgeschlossene 2-Punkt-Kalibrierung
        self.calib_stage = 0 # 0=Uncalibrated (Static), 1=Hanging Calibrated (Live), 2=Fully Calibrated

        # Speicher für Glitch-Filter
        self.last_valid_data = {}
        self.outlier_counts = {}
        for name in SENSOR_MAPPING.keys():
            self.last_valid_data[name] = (0, 0, 0)
            self.outlier_counts[name] = 0
        
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
            self.tca = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDRESS)
            self._init_sensors()
        except Exception as e:
            print(f"[HAL] Hardware Fehler: {e}")
            print("[HAL] Starte im Simulations-Modus")
            self.dummy_mode = True

        # Beim Start automatisch auf haengende Position kalibrieren
        self.calibrate_zero()
        self.calib_stage = 1 

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

            while not got_value and attempts < 60:
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

    def calibrate_two_point_step1(self):
        """
        Schritt 1: Arm haengt (0,0,0).
        Wir speichern die Offsets, wenden sie aber noch nicht final an,
        oder wir speichern sie als 'Basis-Offsets'.
        Fuer Roll/Pitch (Neigung) nehmen wir DIESE Werte.
        """
        print("[HAL] 2-Punkt Step 1: Hanging (Gravity Reference)...")
        # Wir nutzen die bestehen Funktion, speichern aber das Ergebnis temporaer
        # Da _calibrate_common direkt offsets schreibt, nutzen wir das.
        # Wir merken uns diese Offsets als 'hanging'
        self.calibrate_zero()
        self.temp_hanging_offsets = self.offsets.copy()
        self.calib_stage = 1 # Ab jetzt Live-Werte anzeigen
        print("[HAL] Step 1 gespeichert. Weiter zu Step 2...")

    def calibrate_two_point_step2(self):
        """
        Schritt 2: Arm 90 Grad nach vorne (90,0,0).
        Wir nutzen die Heading-Korrektur von HIER.
        """
        print("[HAL] 2-Punkt Step 2: Forward 90 deg (Heading Reference)...")
        self.calibrate_reference_pose()
        forward_offsets = self.offsets.copy()
        
        # MERGE:
        # Heading (Index 0) -> Von Step 2 (Forward)
        # Roll (Index 1)    -> Von Step 1 (Hanging)
        # Pitch (Index 2)   -> Von Step 1 (Hanging)
        
        final_offsets = {}
        for name in SENSOR_MAPPING.keys():
            # Falls ein Sensor ausgefallen ist, Default (0,0,0)
            off_hang = self.temp_hanging_offsets.get(name, (0,0,0))
            off_fwd  = forward_offsets.get(name, (0,0,0))
            
            # (Heading_Fwd, Roll_Hang, Pitch_Hang)
            merged = (off_fwd[0], off_hang[1], off_hang[2])
            final_offsets[name] = merged
            
        self.offsets = final_offsets
        self.is_calibrated = True
        self.calib_stage = 2
        print(f"[HAL] 2-Punkt Kalibrierung abgeschlossen: {self.offsets}")

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
                    
                    # Outlier Check / Glitch Filter
                    is_valid = True
                    max_diff = 0
                    for i in range(3):
                        d = self._angle_diff(new_vector[i], last_vector[i])
                        if d > max_diff: max_diff = d
                    
                    if max_diff > JUMP_LIMIT:
                        current_count = self.outlier_counts.get(name, 0) + 1
                        self.outlier_counts[name] = current_count
                        
                        if current_count > OUTLIER_LIMIT:
                            # Wenn der Wert laenger abweicht, ist es wohl eine echte Bewegung
                            is_valid = True
                            self.outlier_counts[name] = 0
                        else:
                            # Spikes ignorieren
                            is_valid = False
                    else:
                        # Alles okay, Zaehler reset
                        self.outlier_counts[name] = 0
                        is_valid = True
                    
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
