# visualization/body.py
from OpenGL.GL import *
import pygame
from config import *

class Body:
    def __init__(self):
        # Wir berechnen die Geometrie EINMAL beim Start, nicht jeden Frame
        self._init_geometry()
        self._init_labels()

    def _init_labels(self):
        self.font = pygame.font.SysFont('Arial', 12, bold=True)
        self.tex_front = self._create_text_texture("Brust", (255, 255, 255), (100, 100, 100))
        self.tex_back = self._create_text_texture("Ruecken", (255, 255, 255), (100, 100, 100))
    
    def _create_text_texture(self, text, color, bg_color):
        surface = self.font.render(text, True, color, bg_color)
        w, h = surface.get_width(), surface.get_height()
        data = pygame.image.tostring(surface, "RGBA", 1)
        
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return tex


    def _init_geometry(self):
        x, y, z = BODY_POS
        w, h, d = BODY_WIDTH, BODY_HEIGHT, BODY_DEPTH
        
        # Die 8 Eckpunkte (Vertices)
        self.vertices = [
            (x, y, z),       (x+w, y, z),       (x+w, y+h, z),       (x, y+h, z),       # Hinten
            (x, y, z+d),     (x+w, y, z+d),     (x+w, y+h, z+d),     (x, y+h, z+d)      # Vorne
        ]
        
        # Flächen (Quads)
        self.faces = [
            (0,1,2,3), (4,5,6,7), # Hinten, Vorne
            (0,4,7,3), (1,5,6,2), # Links, Rechts
            (3,2,6,7), (0,1,5,4)  # Oben, Unten
        ]
        
        # Kanten (Lines)
        self.edges = [
            (0,1),(1,2),(2,3),(3,0), 
            (4,5),(5,6),(6,7),(7,4), 
            (0,4),(1,5),(2,6),(3,7)
        ]

    def draw(self):
        """Zeichnet den Körper"""
        # 1. Flächen (Grau)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Zeichne Labels
        # Front (Vertices 4,5,6,7)
        self._draw_label_face(self.tex_front, self.vertices[4], self.vertices[5], self.vertices[6], self.vertices[7])
        
        # Back (Vertices 0,1,2,3) - Reversed for correct view from back
        self._draw_label_face(self.tex_back, self.vertices[1], self.vertices[0], self.vertices[3], self.vertices[2])

        # Rest grau
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glColor3f(0.5, 0.5, 0.5)
        # Nur Seiten, Oben, Unten zeichnen (Front/Back sind Labels)
        other_faces = self.faces[2:]
        for face in other_faces:
            for i in face:
                glVertex3fv(self.vertices[i])
        glEnd()
        
        # 2. Wireframe (Schwarz)
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(0.1, 0.1, 0.1)
        for edge in self.edges:
            for i in edge:
                glVertex3fv(self.vertices[i])
        glEnd()

    def _draw_label_face(self, tex, p1, p2, p3, p4):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex)
        glColor3f(1,1,1)
        glBegin(GL_QUADS)
        # Texture coordinates: (0,0) -> (1,0) -> (1,1) -> (0,1)
        glTexCoord2f(0, 0); glVertex3fv(p1)
        glTexCoord2f(1, 0); glVertex3fv(p2)
        glTexCoord2f(1, 1); glVertex3fv(p3)
        glTexCoord2f(0, 1); glVertex3fv(p4)
        glEnd()
