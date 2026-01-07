import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import board
import busio
import adafruit_bno055
import adafruit_tca9548a
import sys
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

# --- KONFIGURATION ---
ARM_LENGTH_1 = 6.0
ARM_LENGTH_2 = 5.0

# --- HARDWARE SETUP ---
sensor1 = None
sensor2 = None

print("Initialisiere Hardware...")

try:
    # Frequenz runter auf 10kHz für maximale Stabilität beim Debuggen
    i2c = busio.I2C(board.SCL, board.SDA, frequency=10000)
    tca = adafruit_tca9548a.TCA9548A(i2c, address=0x70)

    try:
        sensor1 = adafruit_bno055.BNO055_I2C(tca[2], address=0x28)
        print("Sensor 1 (Kanal 2) OK")
    except: print("Sensor 1 fehlt")

    try:
        sensor2 = adafruit_bno055.BNO055_I2C(tca[7], address=0x28)
        print("Sensor 2 (Kanal 7) OK")
    except: print("Sensor 2 fehlt")

except Exception as e:
    print(f"I2C Fehler: {e}")

# --- HELPER ---
def get_euler(sensor):
    if sensor:
        try:
            e = sensor.euler
            if e and e[0] is not None: return e
        except: pass
    return (0, 0, 0)

def draw_segment(length, color):
    glLineWidth(4)
    glBegin(GL_LINES)
    glColor3fv(color)
    glVertex3f(0, 0, 0); glVertex3f(length, 0, 0)
    glEnd()
    glPointSize(8)
    glBegin(GL_POINTS)
    glColor3f(1, 1, 1)
    glVertex3f(length, 0, 0)
    glEnd()

def draw_grid():
    glLineWidth(1)
    glBegin(GL_LINES)
    glColor3fv((0.3, 0.3, 0.3))
    y = -5
    for i in range(-15, 16, 5):
        glVertex3f(i, y, -15); glVertex3f(i, y, 15)
        glVertex3f(-15, y, i); glVertex3f(15, y, i)
    glEnd()
    # Achsenkreuz
    glLineWidth(3)
    glBegin(GL_LINES)
    glColor3f(1,0,0); glVertex3f(0,0,0); glVertex3f(2,0,0)
    glColor3f(0,1,0); glVertex3f(0,0,0); glVertex3f(0,2,0)
    glColor3f(0,0,1); glVertex3f(0,0,0); glVertex3f(0,0,2)
    glEnd()

# --- WICHTIGE NEUE FUNKTION ---
def init_gl(width, height):
    # 1. Hintergrund auf GRAU setzen (damit wir sehen, ob es rendert)
    glClearColor(0.2, 0.2, 0.2, 1.0) 
    
    # 2. Tiefentest aktivieren
    glEnable(GL_DEPTH_TEST)
    
    # 3. Beleuchtung AUSschalten (sonst ist alles schwarz ohne Lichtquellen)
    glDisable(GL_LIGHTING)
    
    # 4. Projektions-Matrix (Linse) einstellen
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (width / height), 0.1, 100.0)
    
    # 5. Zurück in den Zeichen-Modus (Modelview) wechseln
    glMatrixMode(GL_MODELVIEW)

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Roboterarm")
    
    # OpenGL sauber initialisieren
    init_gl(display[0], display[1])
    
    cam_rot_x, cam_rot_y = 20, 0 # Start-Winkel
    mouse_down = False
    last_mouse = (0,0)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: mouse_down = True; last_mouse = event.pos
            if event.type == pygame.MOUSEBUTTONUP: mouse_down = False
            if event.type == pygame.MOUSEMOTION and mouse_down:
                dx, dy = event.pos[0] - last_mouse[0], event.pos[1] - last_mouse[1]
                cam_rot_x += dy * 0.5
                cam_rot_y += dx * 0.5
                last_mouse = event.pos

        h1, r1, p1 = get_euler(sensor1)
        h2, r2, p2 = get_euler(sensor2)

        # --- RENDERING ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity() # Reset NUR die Welt-Matrix, nicht die Kamera!
        
        # Kamera positionieren
        glTranslatef(0, 0, -30)
        glRotatef(cam_rot_x, 1, 0, 0)
        glRotatef(cam_rot_y, 0, 1, 0)
        
        draw_grid()

        # Arm zeichnen
        glTranslatef(-3, 0, 0) # Startpunkt
        
        # Segment 1
        glPushMatrix()
        glRotatef(h1, 0, 1, 0); glRotatef(p1, 0, 0, 1); glRotatef(r1, 1, 0, 0)
        draw_segment(ARM_LENGTH_1, (1, 0.2, 0.2)) # Rot
        glTranslatef(ARM_LENGTH_1, 0, 0)
        
        # Segment 2
        glRotatef(-r1, 1, 0, 0); glRotatef(-p1, 0, 0, 1); glRotatef(-h1, 0, 1, 0) # Reset 1
        glRotatef(h2, 0, 1, 0); glRotatef(p2, 0, 0, 1); glRotatef(r2, 1, 0, 0) # Apply 2
        draw_segment(ARM_LENGTH_2, (0.2, 1, 0.2)) # Grün
        
        glPopMatrix()

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
