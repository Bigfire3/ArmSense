# visualization/body.py
from OpenGL.GL import *
from config import *

class Body:
    def __init__(self):
        # Wir berechnen die Geometrie EINMAL beim Start, nicht jeden Frame
        self._init_geometry()

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
        glBegin(GL_QUADS)
        glColor3f(0.5, 0.5, 0.5)
        for face in self.faces:
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