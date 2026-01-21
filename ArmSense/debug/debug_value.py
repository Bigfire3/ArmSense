# debug_sensors.py
import time
import sys
import os

# Pfad erweitern, damit wir Module vom Parent importieren koennen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.sensor_manager import SensorManager
from utils import q_to_euler

def main():
    print("--- IMU Debug Monitor (Quaternion Mode) ---")
    print("Initialisiere SensorManager...")
    
    # Nutzt deine existierende Logik (inkl. Multiplexer & Config)
    sensors = SensorManager()
    
    print("\nMessung läuft. Drücke STRG+C zum Beenden.\n")
    print(f"{'BASE (Heading, Roll, Pitch)':^35} | {'ARM (Heading, Roll, Pitch)':^35}")
    print("-" * 75)

    try:
        while True:
            # 1. Daten holen (Quaternions)
            data = sensors.get_data()
            
            # Quaternion extrahieren
            q_base = data.get("base", (1,0,0,0))
            q_arm = data.get("arm",  (1,0,0,0))
            
            # Convert to Euler for display
            b_h, b_r, b_p = q_to_euler(q_base)
            a_h, a_r, a_p = q_to_euler(q_arm)
            
            # 2. Formatieren
            line = (
                f"H:{b_h:6.1f} R:{b_r:6.1f} P:{b_p:6.1f}   |   "
                f"H:{a_h:6.1f} R:{a_r:6.1f} P:{a_p:6.1f}"
            )
            
            # Ausgabe mit Carriage Return (\r) am Ende statt Newline
            sys.stdout.write("\r" + line)
            sys.stdout.flush()
            
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nBeendet.")

if __name__ == "__main__":
    main()