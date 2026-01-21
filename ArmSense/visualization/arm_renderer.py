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
        
        # Calibration State
        self.calib_step = 0 # 0=Idle, 1=Wait Hang, 2=Wait Fwd
        self.font = pygame.font.SysFont('Arial', 24)
        
        # Pose Detection State
        self.pose_detection_active = False

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
                key_name = pygame.key.name(event.key)

                # 2-Punkt Kalibrierung State Machine
                if key_name == '2' or event.key == pygame.K_2 or event.unicode == '2':
                    print("[UI] Starting 2-Point Calibration (Step 1)")
                    self.calib_step = 1 # Start Sequence
                
                if event.key == pygame.K_SPACE:
                    if self.calib_step == 1 and sensor_manager:
                        sensor_manager.calibrate_two_point_step1()
                        self.calib_step = 2
                    elif self.calib_step == 2 and sensor_manager:
                        sensor_manager.calibrate_two_point_step2()
                        self.calib_step = 0
                
                # Taste '1' für Referenz-Kalibrierung (Legacy)
                # Check KeyCode AND Unicode (Robuster)
                if key_name == '1' or event.key == pygame.K_1 or event.unicode == '1':
                    print("[UI] Action: '1' pressed -> Reference Pose")
                    if sensor_manager:
                        sensor_manager.calibrate_reference_pose()
                    self.calib_step = 0 
                
                # Optional: Taste '0', 'z' oder '*' für Reset auf Null (Arm hängt)
                is_zero_key = (key_name == '0' or event.key == pygame.K_0 or event.unicode == '0' or
                               key_name == 'z' or event.key == pygame.K_z or
                               event.unicode == '*' or key_name == '*')
                               
                if is_zero_key:
                    print("[UI] Action: Zero Calibration triggered")
                    if sensor_manager:
                        sensor_manager.calibrate_zero()
                    self.calib_step = 0 # Force reset of UI state

                # Taste '9' für Pose Detection an/aus
                if key_name == '9' or event.key == pygame.K_9 or event.unicode == '9':
                    self.pose_detection_active = not self.pose_detection_active
                    status = "AN" if self.pose_detection_active else "AUS"
                    print(f"[UI] Pose Detection: {status}")
                    self.calib_step = 0 # Ensure overlay shows pose
                    print(f"[UI] Pose Detection: {status}")
                    self.calib_step = 0 # Ensure overlay shows pose

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

    def _draw_text_overlay(self, pose_text=""):
        """Zeichnet 2D Text fuer Kalibrierungs-Anweisungen und Active Pose"""
        
        text = ""
        color = (255, 255, 0) # Gelb fuer Instructions
        
        # Priority 1: Calibration Steps
        if self.calib_step == 1:
            text = "STEP 1: Arm haengen lassen (Relaxed) -> [SPACE]"
        elif self.calib_step == 2:
            text = "STEP 2: Arm 90 Grad nach vorne (Forward) -> [SPACE]"
        # Priority 2: Pose Detection Result
        elif self.pose_detection_active:
            display_pose = pose_text if pose_text else "Scanning..."
            text = f"Pose Detection: {display_pose}"
            color = (0, 255, 0) # Green
        # Priority 3: Default Instruction
        else:
            text = "'0': Hang | '1': Fwd 90 | '9': Detection | '2': Man. Calib"
            color = (180, 180, 180) # Grey
            
        if not text: return
            
        text_surface = self.font.render(text, True, color)
        # Check if text surface is valid
        if text_surface.get_width() == 0: return

        w, h = text_surface.get_width(), text_surface.get_height()
        # Use simple string data, ensure flipped=0 for 2D UI (Top-Left origin)
        text_data = pygame.image.tostring(text_surface, "RGBA", 0)
        
        # --- FIXED: GL State ---
        # Ensure we are drawing in clean 2D state
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], self.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glColor3f(1,1,1)
        glEnable(GL_TEXTURE_2D)
        
        x_pos, y_pos = 20, 20
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
        glTexCoord2f(1, 0); glVertex2f(x_pos+w, y_pos)
        glTexCoord2f(1, 1); glVertex2f(x_pos+w, y_pos+h)
        glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos+h)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([tex_id])
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        # GL_DEPTH_TEST was disabled, re-enable if it was enabled
        glPopAttrib()
        # glEnable(GL_DEPTH_TEST) # Not needed with PopAttrib

    def render(self, sensor_data, pose_text=""):
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
        glRotatef(h1, 1, 0, 0)
        glRotatef(r1, 0, 0, 1) # Roll -> Z (Sideways)
        # Changed: Removed minus sign to fix direction (Positive Pitch = Forward)
        glRotatef(p1, 0, 1, 0) # Pitch -> Y (Forward)
        self._draw_segment(ARM_LENGTH_1, (1, 0.2, 0.2))
        
        # Unterarm
        glTranslatef(ARM_LENGTH_1, 0, 0)
        # Undo Transformations (Inverse Order of Upper Arm)
        glRotatef(-p1, 0, 1, 0) # Undo Pitch (Inverse of p1)
        glRotatef(-r1, 0, 0, 1) # Undo Roll
        glRotatef(-h1, 1, 0, 0) # Undo Heading
        
        # Apply Forearm Transformations
        glRotatef(h2, 1, 0, 0)
        glRotatef(r2, 0, 0, 1)
        glRotatef(p2, 0, 1, 0) # Pitch (Positive = Forward)
        self._draw_segment(ARM_LENGTH_2, (0.2, 1, 0.2))
        
        glPopMatrix()
        glPopMatrix()
        glPopMatrix()

        self._draw_axes_hud()
        self._draw_text_overlay(pose_text)
        
        pygame.display.flip()
        self.clock.tick(FPS)
