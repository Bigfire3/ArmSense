# config.py

# --- HARDWARE ---
I2C_FREQ = 10000
MUX_ADDRESS = 0x70
BNO_ADDRESS = 0x28

# Mapping der Sensoren am Multiplexer
SENSOR_MAPPING = {
    "base": 2,  # Sensor am Oberarm
    "arm": 7    # Sensor am Unterarm
}

# --- KINEMATIK (Menschliche Proportionen) ---
# Wir gehen von abstrakten Einheiten aus (z.B. 1 Einheit = 1 dm)
# Oberarm und Unterarm sind beim Menschen etwa gleich lang.
ARM_LENGTH_1 = 3.0  # Länge Oberarm
ARM_LENGTH_2 = 3.0  # Länge Unterarm (bis Handwurzel)

# --- KÖRPER (BODY) ---
# Der Körper wird links vom Ursprung (0,0,0) platziert.
# (0,0,0) ist das Schultergelenk des rechten Arms.

BODY_WIDTH = 4.0   # Breite des Torsos
BODY_HEIGHT = 7.0  # Höhe des Torsos (Rumpf)
BODY_DEPTH = 2.0   # Tiefe des Torsos (Brustkorb)

# Position der linken unteren hinteren Ecke des Körpers relative zur Schulter (0,0,0).
# X = -4.5 (Körperbreite 4.0 + 0.5 Abstand zur Schulter)
# Y = -6.0 (Damit die Schulter bei Y=0 im oberen Bereich des Torsos sitzt; Top wäre Y=1.0)
# Z = -1.0 (Zentriert in der Tiefe: -Tiefe/2)
BODY_POS = (-BODY_WIDTH - 0.5, -6.0, -BODY_DEPTH/2)

# --- GRAFIK ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 30
# --- SIGNAL FILTERING ---
# Maximal erlaubter Sprung pro Frame in Grad.
# Alles darüber wird als Glitch ignoriert.
MAX_ANGLE_JUMP = 20.0
MAX_OUTLIERS = 5  # Anzahl Frames, die ein Wert abweichen darf, bevor er akzeptiert wird