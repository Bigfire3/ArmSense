# main.py
import sys
from hardware.sensor_manager import SensorManager
from visualization.arm_renderer import ArmVisualizer

def main():
    print("--- ArmSense Start ---")
    print("Steuerung: Maus=Kamera | '1'=Ref-Kalibrierung | '0'=Null-Kalibrierung")
    
    # 1. Module initialisieren
    sensors = SensorManager()
    vis = ArmVisualizer()
    
    running = True
    print("Main Loop gestartet.")
    
    while running:
        # A. Input verarbeiten (jetzt mit sensors Uebergabe)
        running = vis.handle_input(sensor_manager=sensors)
        
        # B. Daten holen (Model Update)
        data = sensors.get_data()
        
        # C. Grafik zeichnen (View Update)
        vis.render(data)

    print("Beendet.")
    sys.exit()

if __name__ == "__main__":
    main()
