# hardware/sensor_manager.py
import time
import sys
import os
import board
import busio
import adafruit_bno055
import adafruit_tca9548a

# Pfad-Fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from utils import q_mult, q_conjugate

try: JUMP_LIMIT = MAX_ANGLE_JUMP
except NameError: JUMP_LIMIT = 25.0 

class SensorManager:
    def __init__(self):
        self.sensors = {}
        self.offsets = {}
        self.alignments = {} 
        self.dummy_mode = False
        
        # Zähler für das Durchschalten der Kalibrierung
        self.calib_cycle = 0 
        
        for name in SENSOR_MAPPING.keys():
            self.offsets[name] = (1, 0, 0, 0)
            self.alignments[name] = (1, 0, 0, 0)
        
        try:
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
        print("[HAL] Kalibriere Nullpunkt (Arm haengt)...")
        self.calib_cycle = 0 # Reset Cycle
        if self.dummy_mode: return

        for name, sensor in self.sensors.items():
            try:
                q = sensor.quaternion
                if q and q[0] is not None:
                    self.offsets[name] = q_conjugate(q)
                    self.alignments[name] = (1, 0, 0, 0) 
            except: pass
        print("[HAL] Nullpunkt gesetzt.")

    def calibrate_forward(self):
        """
        ZYKLISCH: Schaltet durch 4 mögliche Ausrichtungen durch.
        Jedes Drücken der Taste '1' dreht das Ziel-Koordinatensystem um 90 Grad.
        """
        if self.dummy_mode: return
        
        # Liste der 4 möglichen Ziele für "Vorne" (jeweils 90 Grad gerollt)
        # 1. Standard (Daumen oben)
        # 2. 90 Grad rechts (Daumen rechts)
        # 3. 180 Grad (Daumen unten)
        # 4. 270 Grad links (Daumen links)
        targets = [
            (0.7071, 0.0, 0.7071, 0.0),    # Modus 1
            (0.5, 0.5, 0.5, 0.5),          # Modus 2
            (0.0, 0.7071, 0.0, 0.7071),    # Modus 3
            (0.5, -0.5, 0.5, -0.5)         # Modus 4
        ]
        
        # Wähle aktuelles Ziel basierend auf Zähler
        q_target = targets[self.calib_cycle % 4]
        mode_num = (self.calib_cycle % 4) + 1
        
        print(f"[HAL] Kalibriere Ausrichtung -> MODUS {mode_num} / 4")
        print("      (Wenn Bewegung falsch ist: Arm wieder vor und nochmal '1')")

        for name_key in self.sensors.keys():
            # Daten holen (nur Nullpunkt-korrigiert)
            data = self.get_data(raw_align=True) 
            q_current_zeroed = data.get(name_key, (1,0,0,0))
            
            # Korrektur berechnen
            q_inv = q_conjugate(q_current_zeroed)
            self.alignments[name_key] = q_mult(q_target, q_inv)
            
        # Zähler erhöhen für nächstes Mal
        self.calib_cycle += 1

    def get_data(self, raw_align=False):
        data = {}
        if self.dummy_mode: return {"base": (1,0,0,0), "arm": (1,0,0,0)}
        
        for name, sensor in self.sensors.items():
            try:
                q_raw = sensor.quaternion
                if q_raw and q_raw[0] is not None:
                    offset = self.offsets.get(name, (1,0,0,0))
                    q_zeroed = q_mult(offset, q_raw)
                    
                    if raw_align:
                        data[name] = q_zeroed
                    else:
                        align = self.alignments.get(name, (1,0,0,0))
                        data[name] = q_mult(align, q_zeroed)
                else:
                    data[name] = (1,0,0,0)
            except: 
                data[name] = (1,0,0,0)
        
        for name in SENSOR_MAPPING.keys():
            if name not in data: data[name] = (1, 0, 0, 0)
                
        return data
