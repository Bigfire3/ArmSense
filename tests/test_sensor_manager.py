import sys
import os
import math
from unittest.mock import MagicMock

# --- MODULE MOCKING --- 
# Wir mocken die Raspberry Pi Hardware-Bibliotheken, da diese auf Windows 
# sofort beim Import crashen wuerden (No module named 'board')
sys.modules['board'] = MagicMock()
sys.modules['busio'] = MagicMock()
sys.modules['adafruit_bno055'] = MagicMock()
sys.modules['adafruit_tca9548a'] = MagicMock()

# Damit das Skript das 'ArmSense' Modul findet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ArmSense')))

from hardware.sensor_manager import SensorManager

def round_quaternion(q_dict, decimal_places=4):
    """Rundet die Werte in einem Quaternionen-Dict für verlässliche Vergleiche."""
    rounded = {}
    for key, q in q_dict.items():
        if isinstance(q, tuple) or isinstance(q, list):
            rounded[key] = tuple(round(val, decimal_places) for val in q)
        else:
            rounded[key] = q
    return rounded

def run_all_tests(assert_func):
    """
    Führt alle Tests für den SensorManager und dessen Filter aus.
    Gibt True zurück, wenn alle Tests erfolgreich waren, sonst False.
    """
    all_passed = True

    # Quaternions
    q_0_deg = (1.0, 0.0, 0.0, 0.0)
    q_10_deg = (0.99619, 0.08716, 0.0, 0.0) # Regulärer kleiner Sprung
    q_45_deg = (0.92388, 0.38268, 0.0, 0.0) # Großer Sprung (sollte gefiltert werden)

    # === TEST 1: Normale Datenverarbeitung (Kein Jump) ===
    sm_normal = SensorManager()
    
    # Warteschlange füllen: Frame 1=0°, Frame 2=10°
    test_queue = [
        {"base": q_0_deg, "arm": q_0_deg},
        {"base": q_10_deg, "arm": q_10_deg}
    ]
    sm_normal.inject_test_data(test_queue)
    
    # Frame 1 abholen
    res_1 = sm_normal.get_data()
    # Frame 2 abholen (10° liegt im Rahmen < JUMP_LIMIT)
    res_2 = sm_normal.get_data()
    
    # Runden um Fließkommafehler zu ignorieren
    res_2_rounded = round_quaternion(res_2)
    expected_2 = {"base": (0.9962, 0.0872, 0.0, 0.0), "arm": (0.9962, 0.0872, 0.0, 0.0)}
    
    if not assert_func("sensor_manager", "Normaler Datenfluss (10°)", "Letzter: 0°, Neu: 10°", expected_2, res_2_rounded):
        all_passed = False

    # === TEST 2: Jump Filter (Ausreißer ignorieren) ===
    sm_jump = SensorManager()
    
    # Frame 1=0°, Frame 2=45° (Sprung von 45° ist größer als 20° Limit) -> muss gefiltert werden!
    test_queue_jump = [
        {"base": q_0_deg, "arm": q_0_deg},
        {"base": q_45_deg, "arm": q_45_deg}
    ]
    sm_jump.inject_test_data(test_queue_jump)
    
    # Frame 1 speichern Initialwert
    sm_jump.get_data()
    
    # Frame 2 abholen: Der 45° Ausreißer sollte abgeblockt werden, es muss noch q_0_deg ausgegeben werden
    res_jump = sm_jump.get_data()
    res_jump_rounded = round_quaternion(res_jump)
    expected_jump = {"base": (1.0, 0.0, 0.0, 0.0), "arm": (1.0, 0.0, 0.0, 0.0)}
    
    if not assert_func("sensor_manager", "Glitch Protection (Jump Filter >20°)", "Letzter: 0°, Neu (Glitch): 45°", expected_jump, res_jump_rounded):
        all_passed = False

    return all_passed

if __name__ == '__main__':
    def dummy_assert(mod, func, data, exp, act):
        passed = act == exp
        print(f"[{func}] {'BESTANDEN' if passed else 'FEHLGESCHLAGEN'} (Ist: {act}, Erwartet: {exp})")
        return passed
    run_all_tests(dummy_assert)
