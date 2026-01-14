# debug_sensors.py
import time
import sys
from hardware.sensor_manager import SensorManager

def main():
    print("--- IMU Debug Monitor ---")
    print("Initialisiere SensorManager...")
    
    # Nutzt deine existierende Logik (inkl. Multiplexer & Config)
    sensors = SensorManager()
    
    print("\nMessung läuft. Drücke STRG+C zum Beenden.\n")
    print(f"{'BASE (Oberarm)':^30} | {'ARM (Unterarm)':^30}")
    print("-" * 63)

    try:
        while True:
            # 1. Daten holen
            data = sensors.get_data()
            
            # Werte extrahieren (H=Heading, R=Roll, P=Pitch)
            b_h, b_r, b_p = data.get("base", (0,0,0))
            a_h, a_r, a_p = data.get("arm",  (0,0,0))
            
            # 2. Formatieren
            # \r sorgt dafür, dass die Zeile überschrieben wird (kein Scrollen)
            # {:6.1f} bedeutet: Zahl mit min. 6 Zeichen Platz und 1 Nachkommastelle
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