# hardware/sensor_manager.py
import time
import sys
import os
import board
import busio
import adafruit_bno055
import adafruit_tca9548a
import math  # Neu für die Berechnung des Differenzwinkels

# Pfad-Fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from utils import q_mult, q_conjugate

try: JUMP_LIMIT = MAX_ANGLE_JUMP
except NameError: JUMP_LIMIT = 20.0 

class SensorManager:
    def __init__(self):
        self.sensors = {}
        self.offsets = {}
        self.alignments = {} 
        self.dummy_mode = False
        
        # --- Speicher für Filterung ---
        self.last_valid_data = {}
        self.outlier_count = {}
        
        self.calib_cycle = 0 
        
        for name in SENSOR_MAPPING.keys():
            self.offsets[name] = (1, 0, 0, 0)
            self.alignments[name] = (1, 0, 0, 0)
            self.last_valid_data[name] = (1, 0, 0, 0)
            self.outlier_count[name] = 0
        
        try:
            # I2C Initialisierung (10kHz für Stabilität)
            self.i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
            self.tca = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDRESS)
            self._init_sensors()
        except Exception as e:
            print(f"[HAL] Hardware Fehler: {e}")
            self.dummy_mode = True

        if not self.dummy_mode:
            print("[HAL] Warte auf Sensoren...")
            time.sleep(1.0)
            self.calibrate_zero()

    def _init_sensors(self):
        for name, channel in SENSOR_MAPPING.items():
            try:
                bno = adafruit_bno055.BNO055_I2C(self.tca[channel], address=BNO_ADDRESS)
                self.sensors[name] = bno
            except: pass

    def calibrate_zero(self):
        """Schritt 1: Arm hängt entspannt (Gravitations-Referenz)"""
        print("[HAL] Kalibriere Nullpunkt (Arm haengt)...")
        if self.dummy_mode: return

        for name, sensor in self.sensors.items():
            try:
                q = sensor.quaternion
                if q and q[0] is not None:
                    # Speichert die Inverse als Nullpunkt-Offset
                    self.offsets[name] = q_conjugate(q)
                    self.alignments[name] = (1, 0, 0, 0) 
            except: pass
        print("[HAL] Nullpunkt gesetzt.")

    def calibrate_forward(self):
        """Schritt 2: Arm zeigt 90° nach vorne (Kompensiert schräge Montage)"""
        if self.dummy_mode: return
        print("[HAL] Kalibriere Vorwärts-Ausrichtung...")
        
        # Aktuelle Daten ohne Alignment holen
        current_data = self.get_data(raw_align=True)
        # Ziel: Arm zeigt waagerecht nach vorne (90° um Y-Achse)
        q_target = (0.7071, 0.0, 0.7071, 0.0) 
        
        for name_key in self.sensors.keys():
            q_measured = current_data.get(name_key, (1,0,0,0))
            # Alignment berechnen: q_align = q_target * inv(q_measured)
            q_inv = q_conjugate(q_measured)
            self.alignments[name_key] = q_mult(q_target, q_inv)

        print("[HAL] Ausrichtung für ungenaue Montage kompensiert.")

    def get_data(self, raw_align=False):
        data = {}
        if self.dummy_mode: 
            return {"base": (1,0,0,0), "arm": (1,0,0,0)}
        
        for name, sensor in self.sensors.items():
            try:
                q_raw = sensor.quaternion
                if q_raw and q_raw[0] is not None:
                    # 1. Nullpunkt anwenden
                    offset = self.offsets.get(name, (1,0,0,0))
                    q_zeroed = q_mult(offset, q_raw)
                    
                    # 2. Montage-Korrektur anwenden
                    if raw_align:
                        q_final = q_zeroed
                    else:
                        align = self.alignments.get(name, (1,0,0,0))
                        q_final = q_mult(align, q_zeroed)
                    
                    # --- JUMP-FILTER (GLITCH PROTECTION) ---
                    q_last = self.last_valid_data.get(name, q_final)
                    
                    # Berechne den Winkel-Unterschied zum letzten Frame
                    # q_rel = q_final * inv(q_last)
                    q_rel = q_mult(q_final, q_conjugate(q_last))
                    # Clamp für mathematische Stabilität
                    w = max(-1.0, min(1.0, q_rel[0]))
                    diff_angle = 2.0 * math.degrees(math.acos(abs(w)))
                    
                    if diff_angle > JUMP_LIMIT and self.outlier_count[name] < MAX_OUTLIERS:
                        # Sprung ist zu groß -> Behalte den alten Wert bei
                        data[name] = q_last
                        self.outlier_count[name] += 1
                    else:
                        # Normaler Wert oder Limit für Ausreißer erreicht -> Akzeptieren
                        data[name] = q_final
                        self.last_valid_data[name] = q_final
                        self.outlier_count[name] = 0
                else:
                    # Falls Sensor keine Daten liefert -> Letzten gültigen Wert nehmen
                    data[name] = self.last_valid_data.get(name, (1,0,0,0))
            except: 
                data[name] = self.last_valid_data.get(name, (1,0,0,0))
        
        # Sicherstellen, dass alle Mapping-Keys (base, arm) im Output sind
        for name in SENSOR_MAPPING.keys():
            if name not in data: 
                data[name] = self.last_valid_data.get(name, (1, 0, 0, 0))
                
        return data