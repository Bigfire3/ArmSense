import math

def q_mult(q1, q2):
    """
    Multipliziert zwei Quaternionen (w, x, y, z).
    Rückgabe: Neues Quaternion (w, x, y, z).
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    
    return (w, x, y, z)

def q_conjugate(q):
    """
    Gibt das konjugierte (getauschte) Quaternion zurück.
    Für Einheitsquaternionen entspricht dies der Inversen.
    """
    w, x, y, z = q
    return (w, -x, -y, -z)

def q_normalize(q):
    """
    Normalisiert das Quaternion (Länge = 1).
    Wichtig gegen Drift.
    """
    w, x, y, z = q
    norm_sq = w*w + x*x + y*y + z*z
    if norm_sq == 0:
        return (1.0, 0.0, 0.0, 0.0)
    norm = math.sqrt(norm_sq)
    return (w/norm, x/norm, y/norm, z/norm)

def q_rotate_vec(q, v):
    """
    Rotiert Vektor v(x,y,z) mit Quaternion q(w,x,y,z).
    Formel: v' = v + 2 * cross(q_xyz, cross(q_xyz, v) + q_w * v)
    """
    w, x, y, z = q
    vx, vy, vz = v
    
    # q_xyz
    qx, qy, qz = x, y, z
    
    # t = 2 * cross(q_xyz, v)
    tx = 2 * (qy * vz - qz * vy)
    ty = 2 * (qz * vx - qx * vz)
    tz = 2 * (qx * vy - qy * vx)
    
    # v' = v + w * t + cross(q_xyz, t)
    rx = vx + w * tx + (qy * tz - qz * ty)
    ry = vy + w * ty + (qz * tx - qx * tz)
    rz = vz + w * tz + (qx * ty - qy * tx)
    
    return (rx, ry, rz)

def q_to_euler(q):
    """
    Konvertiert Quaternion (w, x, y, z) zu Euler-Winkeln (Heading, Roll, Pitch) in Grad.
    Nuetzlich fuer Debugging-Ausgaben.
    """
    w, x, y, z = q
    
    # Heading (z-axis rotation)
    t0 = +2.0 * (w * z + x * y)
    t1 = +1.0 - 2.0 * (y * y + z * z)
    heading = math.degrees(math.atan2(t0, t1))
    
    # Pitch (y-axis rotation)
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.degrees(math.asin(t2))
    
    # Roll (x-axis rotation)
    t3 = +2.0 * (w * x + y * z)
    t4 = +1.0 - 2.0 * (x * x + y * y)
    roll = math.degrees(math.atan2(t3, t4))
    
    return heading, roll, pitch  

def q_to_matrix(q):
    """
    Konvertiert Quaternion (w,x,y,z) in eine 4x4 OpenGL Matrix (flat list, column-major).
    """
    w, x, y, z = q
    
    xx = x * x
    xy = x * y
    xz = x * z
    xw = x * w
    
    yy = y * y
    yz = y * z
    yw = y * w
    
    zz = z * z
    zw = z * w
    
    # Column-Major Order (OpenGL erwartet dies)
    # Spalte 1
    m00 = 1 - 2 * (yy + zz)
    m01 = 2 * (xy + zw)
    m02 = 2 * (xz - yw)
    m03 = 0
    
    # Spalte 2
    m10 = 2 * (xy - zw)
    m11 = 1 - 2 * (xx + zz)
    m12 = 2 * (yz + xw)
    m13 = 0
    
    # Spalte 3
    m20 = 2 * (xz + yw)
    m21 = 2 * (yz - xw)
    m22 = 1 - 2 * (xx + yy)
    m23 = 0
    
    # Spalte 4
    m30 = 0
    m31 = 0
    m32 = 0
    m33 = 1
    
    return [m00, m01, m02, m03,
            m10, m11, m12, m13,
            m20, m21, m22, m23,
            m30, m31, m32, m33]
