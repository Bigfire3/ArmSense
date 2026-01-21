import math

class PoseDetector:
    def __init__(self):
        self.current_pose = "Unbekannt"
        # Toleranz in Grad +/- (etwas groesser, da wir alle Achsen messen)
        self.TOL = 20.0

    def detect(self, sensor_data):
        """
        Analysiert die Quaternion-Daten.
        sensor_data = {"base": (w,x,y,z), "arm": (w,x,y,z)}
        """
        q_base = sensor_data.get("base", (1,0,0,0))
        q_arm = sensor_data.get("arm", (1,0,0,0))
        
        # Berechne Abweichung von Identity (Hanging = 0 deg)
        deg_base = self._get_angle_from_identity(q_base)
        deg_arm = self._get_angle_from_identity(q_arm)
        
        # 1. Arm haengt (Beide ~0)
        if deg_base < self.TOL and deg_arm < self.TOL:
            return "Arm haengt"

        # 2. L-Form (Base~0, Arm~90)
        if deg_base < self.TOL and abs(deg_arm - 90) < self.TOL:
            return "L-Form (90 Grad)"

        # 3. Arm gestreckt (Base~90, Arm~90)
        if abs(deg_base - 90) < self.TOL and abs(deg_arm - 90) < self.TOL:
            return "Arm gestreckt"
            
        return f"B:{int(deg_base)} A:{int(deg_arm)}"

    def _get_angle_from_identity(self, q):
        """Berechnet Rotationswinkel in Grad relativ zu Identity (0,0,0)"""
        w = q[0]
        # Clamp w fuer acos
        w = max(-1.0, min(1.0, w))
        # Winkel theta = 2 * acos(w)
        angle_rad = 2 * math.acos(abs(w))
        return math.degrees(angle_rad)
