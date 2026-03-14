import sys
import os

# Damit das Skript das 'ArmSense' Modul findet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ArmSense')))

from pose_detector import PoseDetector

def run_all_tests(assert_func):
    """
    Führt alle Tests für die Posenerkennung aus.
    Gibt True zurück, wenn alle Tests erfolgreich waren, sonst False.
    """
    detector = PoseDetector()
    all_passed = True

    # Quaternions für spezifische Winkel.
    # Wichtig: q = (cos(theta/2), sin(theta/2)*x, sin(theta/2)*y, sin(theta/2)*z)
    
    # 0° -> (cos(0), x, y, z) -> (1.0, 0.0, 0.0, 0.0)
    q_0_deg = (1.0, 0.0, 0.0, 0.0)
    
    # 90° -> (cos(45°), sin(45°), 0, 0) -> (0.7071, 0.7071, 0.0, 0.0)
    q_90_deg = (0.7071, 0.7071, 0.0, 0.0)
    
    # 45° (für den undefinierten Fall) -> (cos(22.5°), sin(22.5°), 0, 0) -> (0.92388, 0.38268, 0.0, 0.0)
    q_45_deg = (0.92388, 0.38268, 0.0, 0.0)


    # === TEST 1: Arm hängt (Beide nahe 0°) ===
    sensor_data_hang = {
        "base": q_0_deg,
        "arm": q_0_deg
    }
    result = detector.detect(sensor_data_hang)
    if not assert_func("pose_detector", "Arm hängt", "Base: 0°, Arm: 0°", "Arm haengt", result):
        all_passed = False


    # === TEST 2: L-Form (Base nahe 0°, Arm nahe 90°) ===
    sensor_data_l_form = {
        "base": q_0_deg,
        "arm": q_90_deg
    }
    result = detector.detect(sensor_data_l_form)
    if not assert_func("pose_detector", "L-Form", "Base: 0°, Arm: 90°", "L-Form", result):
        all_passed = False


    # === TEST 3: Vorne Gestreckt (Beide nahe 90°) ===
    sensor_data_gestreckt = {
        "base": q_90_deg,
        "arm": q_90_deg
    }
    result = detector.detect(sensor_data_gestreckt)
    if not assert_func("pose_detector", "Vorne Gestreckt", "Base: 90°, Arm: 90°", "Vorne Gestreckt", result):
        all_passed = False


    # === TEST 4: Undefiniert (Zeigt stattdessen die berechneten Winkel) ===
    # Wenn wir 45° reinschicken, sollte er beide Winkel printen, da keine der 3 Hauptposen greift (Toleranz ist +/- 25°)
    sensor_data_undefiniert = {
        "base": q_45_deg,
        "arm": q_45_deg
    }
    result = detector.detect(sensor_data_undefiniert)
    # Beachte: Auf Grund von acos Runden ergibt unser Quaternion für 45° im Code ~44.99° -> "B44 A44"
    if not assert_func("pose_detector", "Undefinierte Pose", "Base: 45°, Arm: 45°", "Winkel: B44 A44", result):
        all_passed = False


    return all_passed

if __name__ == '__main__':
    # Falls das Skript direkt aufgerufen wird, simuliere die assert Funktion
    def dummy_assert(mod, func, data, exp, act):
        passed = act == exp
        print(f"[{func}] {'BESTANDEN' if passed else 'FEHLGESCHLAGEN'} (Ist: {act}, Erwartet: {exp})")
        return passed
    run_all_tests(dummy_assert)
