import argparse
import sys
import os

# Das Hauptverzeichnis zum Pfad hinzufügen, damit 'ArmSense' importiert werden kann
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def assert_test(module_name, func_name, hardcoded_data, expected_value, actual_value):
    """
    Hilfsfunktion, um die Testergebnisse im gewünschten Format auszugeben.
    Gibt True zurück, wenn der Test bestanden wurde, sonst False.
    """
    passed = actual_value == expected_value
    # Konsolen-Farben konfigurieren (Grün: Bestanden, Rot: Fehlgeschlagen)
    color_green = '\033[92m'
    color_red = '\033[91m'
    color_reset = '\033[0m'
    
    if passed:
        result_str = f"{color_green}Bestanden{color_reset}"
    else:
        result_str = f"{color_red}Fehlgeschlagen (Ist: {actual_value}){color_reset}"
        
    print(f"[{module_name}] {func_name} | Hardcoded Daten: {hardcoded_data} | Erwartungswert: {expected_value} | Resultat: {result_str}")
    return passed

def main():
    parser = argparse.ArgumentParser(description="ArmSense Eigener Test-Runner")
    parser.add_argument('test_module', nargs='?', default='all', choices=['all', 'pose', 'sensor'], 
                        help="Gibt an, welche Tests ausgeführt werden sollen: 'all', 'pose', oder 'sensor'")
    
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print(f" Starte ArmSense Test-Runner (Modus: {args.test_module})")
    print("="*50)
    
    all_tests_passed = True

    # 1. Pose Detector Tests ausführen
    if args.test_module in ['all', 'pose']:
        print("\n--- Posenerkennung Tests ---")
        try:
            from test_pose_detector import run_all_tests as run_pose_tests
            success = run_pose_tests(assert_test)
            if not success:
                all_tests_passed = False
        except ImportError:
            print("[\u26A0] test_pose_detector.py wurde noch nicht implementiert.")

    # 2. Sensor Manager Tests ausführen
    if args.test_module in ['all', 'sensor']:
        print("\n--- Sensor Manager & Filter Tests ---")
        try:
            from test_sensor_manager import run_all_tests as run_sensor_tests
            success = run_sensor_tests(assert_test)
            if not success:
                all_tests_passed = False
        except ImportError as e:
            print(f"[\u26A0] test_sensor_manager.py konnte nicht importiert werden: {e}")

    print("\n" + "="*50)
    if all_tests_passed:
        print("\033[92mGESAMT-RESULTAT: Alle ausgeführten Tests erfolgreich!\033[0m")
    else:
        print("\033[91mGESAMT-RESULTAT: Einige Tests sind fehlgeschlagen.\033[0m")
        sys.exit(1)

if __name__ == '__main__':
    main()
