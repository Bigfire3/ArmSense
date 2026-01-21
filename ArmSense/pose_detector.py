# pose_detector.py
import math

class PoseDetector:
    def __init__(self):
        self.current_pose = "Unbekannt"
        # Toleranz in Grad (+/-)
        self.TOL = 25.0

    def detect(self, sensor_data):
        """
        Analysiert die Quaternion-Daten und erkennt die Pose.
        """
        q_base = sensor_data.get("base", (1,0,0,0))
        q_arm = sensor_data.get("arm", (1,0,0,0))
        
        # Berechne Winkelabweichung vom Nullpunkt (Hängen = 0 Grad)
        deg_base = self._get_angle_from_identity(q_base)
        deg_arm = self._get_angle_from_identity(q_arm)
        
        # Debugging: Zeigt die Winkel live im Terminal (falls nötig einkommentieren)
        # print(f"DEBUG: Base={int(deg_base)}° Arm={int(deg_arm)}°")

        # 1. Arm haengt (Beide nahe 0°)
        if deg_base < self.TOL and deg_arm < self.TOL:
            return "Arm haengt"

        # 2. L-Form (Oberarm hängt, Unterarm ~90°)
        if deg_base < self.TOL and abs(deg_arm - 90) < self.TOL:
            return "L-Form"

        # 3. Vorne Gestreckt (Beide ~90°)
        # Da wir 'Vorne' als 90° Abweichung vom Hängen definiert haben
        if abs(deg_base - 90) < self.TOL and abs(deg_arm - 90) < self.TOL:
            return "Vorne Gestreckt"
            
        # Keine Pose erkannt -> Zeige aktuelle Winkel an
        return f"Winkel: B{int(deg_base)} A{int(deg_arm)}"

    def _get_angle_from_identity(self, q):
        """Berechnet Rotationswinkel eines Quaternions relativ zu (1,0,0,0) in Grad"""
        w = q[0]
        # Sicherstellen, dass w im gültigen Bereich für acos liegt
        w = max(-1.0, min(1.0, w))
        # Formel: Winkel = 2 * acos(w)
        angle_rad = 2 * math.acos(abs(w))
        return math.degrees(angle_rad)
