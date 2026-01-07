# main.py
import sys
from hardware.sensor_manager import SensorManager
from visualization.arm_renderer import ArmVisualizer

def main():
    print("--- ArmSense Start ---")
    
    # 1. Module initialisieren
    sensors = SensorManager()
    vis = ArmVisualizer()
    
    running = True
    print("Main Loop gestartet.")
    
    while running:
        # A. Input verarbeiten
        running = vis.handle_input()
        
        # B. Daten holen (Model Update)
        data = sensors.get_data()
        
        # C. Grafik zeichnen (View Update)
        vis.render(data)

    print("Beendet.")
    sys.exit()

if __name__ == "__main__":
    main()