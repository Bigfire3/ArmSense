# visualization/arm_renderer.py
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from config import *
from .body import Body

class ArmVisualizer:
    def __init__(self):
        pygame.init()
        self.display = (WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("ArmSense V1.3 - Calibration Added")
        
        self.clock = pygame.time.Clock()
        self._init_gl()
        
        self.body = Body()
        
        self.cam_rot_x = 20
        self.cam_rot_y = -30
        self.mouse_down = False
        self.last_mouse = (0,0)

    def _init_gl(self):
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_input(self, sensor_manager=None):
        """
        Verarbeitet Maus und Tastatur.
        NEU: sensor_manager Argument für Kalibrierungs-Trigger
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                return False
            
            # --- TASTENDRUCK ---
            if event.type == pygame.KEYDOWN:
                # Taste '1' für Referenz-Kalibrierung
                if event.key == pygame.K_1:
                    if sensor_manager:
                        sensor_manager.calibrate_reference_pose()
                
                # Optional: Taste '0' für Reset auf Null (Arm hängt)
                if event.key == pygame.K_0:
                    if sensor_manager:
                        sensor_manager.calibrate_zero()

            # --- MAUS STEUERUNG ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_down = True
                    self.last_mouse = event.pos
            if event.type == pygame.MOUSEBUTTONUP: 
                self.mouse_down = False
            if event.type == pygame.MOUSEMOTION and self.mouse_down:
                dx, dy = event.pos[0] - self.last_mouse[0], event.pos[1] - self.last_mouse[1]
                self.cam_rot_x += dy * 0.5
                self.cam_rot_y += dx * 0.5
                self.last_mouse = event.pos
                
        return True

    def _draw_grid(self):
        grid_size = 20
        y_floor = -8
        step = 5
        
        glLineWidth(1)
        glBegin(GL_LINES)
        glColor3fv((0.3, 0.3, 0.3))
        for i in range(-grid_size, grid_size + 1, step):
            glVertex3f(i, y_floor, -grid_size); glVertex3f(i, y_floor, grid_size)
            glVertex3f(-grid_size, y_floor, i); glVertex3f(grid_size, y_floor, i)
        glEnd()
        
    def _draw_axes_hud(self):
        size = 1.5 
        glDisable(GL_DEPTH_TEST)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(-6.5, -4.5, -15.0)
        glRotatef(self.cam_rot_x, 1, 0, 0)
        glRotatef(self.cam_rot_y, 0, 1, 0)
        
        glLineWidth(3)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(size, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, size, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, size)
        glEnd()
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
        
        glPushMatrix()
        glTranslatef(0, 0, -40)
        glRotatef(self.cam_rot_x, 1, 0, 0)
        glRotatef(self.cam_rot_y, 0, 1, 0)

        self._draw_grid()
        self.body.draw()

        glPushMatrix()
        glRotatef(-90, 0, 0, 1)
        
        # Oberarm
        glPushMatrix()
        glRotatef(h1, 0, 1, 0)
        glRotatef(p1, 0, 0, -1)
        glRotatef(r1, 1, 0, 0)
        self._draw_segment(ARM_LENGTH_1, (1, 0.2, 0.2))
        
        # Unterarm
        glTranslatef(ARM_LENGTH_1, 0, 0)
        glRotatef(-r1, 1, 0, 0); glRotatef(-p1, 0, 0, 1); glRotatef(-h1, 0, 1, 0)
        glRotatef(h2, 0, 1, 0); glRotatef(p2, 0, 0, 1); glRotatef(r2, 1, 0, 0)
        self._draw_segment(ARM_LENGTH_2, (0.2, 1, 0.2))
        
        glPopMatrix()
        glPopMatrix()
        glPopMatrix()

        self._draw_axes_hud()
        
        pygame.display.flip()
        self.clock.tick(FPS)
