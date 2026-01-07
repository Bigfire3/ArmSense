import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from config import *
# NEU: Importiere die Body-Klasse
from .body import Body

class ArmVisualizer:
    def __init__(self):
        pygame.init()
        self.display = (WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("ArmSense V1.2 - OOP Structure")
        
        self.clock = pygame.time.Clock()
        self._init_gl()
        
        # NEU: Das Body-Objekt wird hier einmalig erstellt
        self.body = Body()
        
        self.cam_rot_x = 20
        self.cam_rot_y = -30
        self.mouse_down = False
        self.last_mouse = (0,0)

    def _init_gl(self):
        # ... (bleibt gleich wie vorher) ...
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_input(self):
        # ... (bleibt gleich wie vorher) ...
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_down = True
                    self.last_mouse = event.pos
            if event.type == pygame.MOUSEBUTTONUP: self.mouse_down = False
            if event.type == pygame.MOUSEMOTION and self.mouse_down:
                dx, dy = event.pos[0] - self.last_mouse[0], event.pos[1] - self.last_mouse[1]
                self.cam_rot_x += dy * 0.5
                self.cam_rot_y += dx * 0.5
                self.last_mouse = event.pos
        return True

    def _draw_grid(self):
        # 1. Gitter zeichnen (Achsen entfernt!)
        grid_size = 20
        y_floor = -8 # Boden etwas tiefer setzen wegen Körpergröße
        step = 5
        
        glLineWidth(1)
        glBegin(GL_LINES)
        glColor3fv((0.3, 0.3, 0.3))
        # Gitterlinien
        for i in range(-grid_size, grid_size + 1, step):
            glVertex3f(i, y_floor, -grid_size); glVertex3f(i, y_floor, grid_size)
            glVertex3f(-grid_size, y_floor, i); glVertex3f(grid_size, y_floor, i)
        glEnd()
        
    def _draw_axes_hud(self):
        """Zeichnet ein kleines Koordinatensystem unten links"""
        # Größe der HUD-Achsen
        size = 1.5 
        
        glDisable(GL_DEPTH_TEST) # HUD soll immer VOR allem anderen sein
        glPushMatrix()
        glLoadIdentity()
        
        # Positionierung:
        # Z = -15 (Abstand zur Kamera, damit es sichtbar ist)
        # X = -6.5 (Links am Rand, abhängig von Aspect Ratio)
        # Y = -4.5 (Unten am Rand)
        glTranslatef(-6.5, -4.5, -15.0)
        
        # Rotation der Kamera anwenden, damit Orientierung stimmt
        glRotatef(self.cam_rot_x, 1, 0, 0)
        glRotatef(self.cam_rot_y, 0, 1, 0)
        
        glLineWidth(3)
        glBegin(GL_LINES)
        # X-Achse (Rot)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(size, 0, 0)
        # Y-Achse (Grün)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, size, 0)
        # Z-Achse (Blau)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, size)
        glEnd()
        
        # Beschriftung ist in reinem OpenGL ohne Text-Lib schwer, 
        # aber die Farben (RGB = XYZ) sind Standard.
        
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)

    def _draw_segment(self, length, color):
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

    def render(self, sensor_data):
        h1, r1, p1 = sensor_data["base"]
        h2, r2, p2 = sensor_data["arm"]

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # --- 1. Hauptszene ---
        glPushMatrix()
        glTranslatef(0, 0, -40) # Zoom auf Szene
        glRotatef(self.cam_rot_x, 1, 0, 0)
        glRotatef(self.cam_rot_y, 0, 1, 0)

        self._draw_grid()
        self.body.draw()

        # Arm Visualisierung (mit Korrektur für hängenden Arm)
        glPushMatrix()
        glRotatef(-90, 0, 0, 1) # Basis-Rotation: X zeigt nach unten
        
        # Oberarm
        glPushMatrix()
        glRotatef(h1, 0, 1, 0)
        glRotatef(p1, 0, 0, 1)
        glRotatef(r1, 1, 0, 0)
        self._draw_segment(ARM_LENGTH_1, (1, 0.2, 0.2))
        
        # Unterarm
        glTranslatef(ARM_LENGTH_1, 0, 0)
        glRotatef(-r1, 1, 0, 0); glRotatef(-p1, 0, 0, 1); glRotatef(-h1, 0, 1, 0)
        glRotatef(h2, 0, 1, 0); glRotatef(p2, 0, 0, 1); glRotatef(r2, 1, 0, 0)
        self._draw_segment(ARM_LENGTH_2, (0.2, 1, 0.2))
        
        glPopMatrix() # Oberarm Pop
        glPopMatrix() # Arm-Basis Pop
        glPopMatrix() # Kamera Pop

        # --- 2. HUD Overlay (Nach der Szene zeichnen) ---
        self._draw_axes_hud()
        
        pygame.display.flip()
        self.clock.tick(FPS)
