# hardware/sensor_manager.py
import board
import busio
import adafruit_bno055
import adafruit_tca9548a
from config import *

class SensorManager:
    def __init__(self):
        self.sensors = {}
        self.offsets = {}  # HIER: Speicher für die Null-Werte
        self.dummy_mode = False
        
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA, frequency=I2C_FREQ)
            self.tca = adafruit_tca9548a.TCA9548A(self.i2c, address=MUX_ADDRESS)
            self._init_sensors()
        except Exception as e:
            print(f"[HAL] Hardware Fehler: {e}")
            print("[HAL] Starte im Simulations-Modus (Dummy Data)")
            self.dummy_mode = True

        # Automatisch kalibrieren beim Start
        self.calibrate_zero()

    def _init_sensors(self):
        for name, channel in SENSOR_MAPPING.items():
            try:
                print(f"[HAL] Init Sensor '{name}' auf Kanal {channel}...")
                # Modus NDOF ist Standard, aber explizit gut
                bno = adafruit_bno055.BNO055_I2C(self.tca[channel], address=BNO_ADDRESS)
                self.sensors[name] = bno
            except Exception as e:
                print(f"[HAL] Fehler bei Sensor '{name}': {e}")

    def calibrate_zero(self):
        """Liest aktuelle Werte und setzt sie als neuen Nullpunkt."""
        print("[HAL] Kalibriere Nullposition (Arm haengt gerade runter)...")
        if self.dummy_mode:
            return

        for name, sensor in self.sensors.items():
            try:
                euler = sensor.euler
                if euler and euler[0] is not None:
                    self.offsets[name] = euler
                else:
                    self.offsets[name] = (0, 0, 0)
            except:
                self.offsets[name] = (0, 0, 0)

    def get_data(self):
        data = {}
        
        if self.dummy_mode:
            return {"base": (0,0,0), "arm": (0,0,0)}

        for name, sensor in self.sensors.items():
            try:
                curr = sensor.euler
                if curr and curr[0] is not None:
                    # Offset abziehen
                    off = self.offsets.get(name, (0,0,0))
                    
                    # Euler-Mathematik: (Aktuell - Offset)
                    # Wir nutzen Modulo 360, um Sprünge bei 0/360 zu glätten
                    h = (curr[0] - off[0]) % 360
                    r = (curr[1] - off[1]) % 360
                    p = (curr[2] - off[2]) % 360
                    
                    # Optional: In +/- 180 Grad Format wandeln für OpenGL
                    if h > 180: h -= 360
                    if r > 180: r -= 360
                    if p > 180: p -= 360
                    
                    data[name] = (h, r, p)
                else:
                    data[name] = (0, 0, 0)
            except OSError:
                data[name] = (0, 0, 0)
        
        # Fehlende Sensoren auffüllen
        for name in SENSOR_MAPPING.keys():
            if name not in data:
                data[name] = (0, 0, 0)
                
        return data
