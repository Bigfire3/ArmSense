class PoseDetector:
    def __init__(self):
        self.current_pose = "Unbekannt"
        # Toleranz in Grad +/-
        self.TOL = 25.0

    def detect(self, sensor_data):
        """
        Analysiert die Sensor-Daten und gibt den Namen der Pose zurück.
        Erwartet sensor_data = {"base": (h,r,p), "arm": (h,r,p)}
        """
        # Pitch ist Index 2 (Y-Achse im Code, 'Vorne/Hinten')
        b_p = sensor_data["base"][2] 
        a_p = sensor_data["arm"][2]
        
        # 1. Arm gerade runter (Hanging)
        # Beide Sensoren nahe 0 Grad
        if abs(b_p) < self.TOL and abs(a_p) < self.TOL:
            return "Arm haengt"

        # 2. L-Form (Unterarm oben)
        # Base nahe 0, Arm nahe 90
        if abs(b_p) < self.TOL and abs(a_p - 90) < self.TOL:
            return "L-Form (90 Grad)"

        # 3. Arm gerade nach vorne gestreckt (Zombie)
        # Base nahe 90, Arm nahe 90 (da absolute Sensoren)
        if abs(b_p - 90) < self.TOL and abs(a_p - 90) < self.TOL:
            return "Arm gestreckt (Vorne)"
            
        return "..."
