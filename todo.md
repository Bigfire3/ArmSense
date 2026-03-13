# ArmSense - Gimbal Lock Probleme & Lösungen

## Was ist Gimbal Lock?

**Gimbal Lock** ist ein Zustand bei Euler-Winkeln, bei dem zwei Rotationsachsen parallel werden (typischerweise bei ±90° Pitch). Dadurch geht ein Freiheitsgrad verloren und die Orientierung wird mehrdeutig oder "springt" unkontrolliert.

---

## ❌ Identifizierte Probleme im Code

### 1. `utils.py` - `q_to_euler()` Funktion (Zeile 61-81)

**Problem:** Die Konvertierung von Quaternion zu Euler-Winkeln ist anfällig für Gimbal Lock.

```python
# Pitch (y-axis rotation)
t2 = +2.0 * (w * y - z * x)
t2 = +1.0 if t2 > +1.0 else t2
t2 = -1.0 if t2 < -1.0 else t2
pitch = math.degrees(math.asin(t2))  # <-- Problem: asin wird instabil bei ±90°
```

**Warum Gimbal Lock?** Bei `pitch = ±90°` (t2 ≈ ±1.0) wird `asin()` numerisch instabil und `heading`/`roll` werden ununterscheidbar.

**Lösung:** Euler-Winkel nur für Debug-Ausgaben verwenden. Für alle Berechnungen direkt Quaternionen nutzen (wie bereits größtenteils implementiert).

---

### 2. `arm_renderer.py` - `glRotatef()` mit festen Winkeln (Zeile 233)

**Problem:** Feste Euler-Rotation zur Achsenkorrektur.

```python
glRotatef(-90, 0, 0, 1)  # X zeigt jetzt nach unten (Y)
```

**Warum Gimbal Lock?** Diese einzelne Rotation ist zwar unproblematisch, aber wenn mehrere `glRotatef()` Aufrufe kombiniert werden, kann Gimbal Lock bei bestimmten Armstellungen auftreten.

**Lösung:** Statt `glRotatef()` sollte eine kombinierte Quaternion-Matrix berechnet und mit `glMultMatrixf()` angewendet werden.

---

### 3. `pose_detector.py` - Winkelberechnung aus Quaternion (Zeile 43-48)

**Problem:** Die Funktion berechnet nur den **Gesamtwinkel** relativ zur Identity, nicht die einzelnen Achsen.

```python
def _get_angle_from_identity(self, q):
    w = q[0]
    w = max(-1.0, min(1.0, w))
    angle_rad = 2 * math.acos(abs(w))  # Nur Gesamtrotation
    return math.degrees(angle_rad)
```

**Warum problematisch?** Diese Methode erkennt nicht die Rotationsrichtung. Ein Arm bei 90° nach vorne und 90° zur Seite geben den gleichen Wert!

**Lösung:** Für Pose-Erkennung die Quaternion-Komponenten direkt analysieren oder spezifische Achsen-Projektionen nutzen (z.B. `q_rotate_vec()` auf eine Referenzachse anwenden).

---

### 4. `sensor_manager.py` - `calibrate_forward()` Hardcoded Quaternion (Zeile 79)

**Problem:** Fest kodiertes Ziel-Quaternion für 90° Rotation.

```python
q_target = (0.7071, 0.0, 0.7071, 0.0)  # Hardcoded 90° um Y-Achse
```

**Warum problematisch?** Diese Annahme gilt nur, wenn der Arm exakt horizontal und in der Sagittalebene ist. Abweichungen führen zu Fehlern.

**Lösung:** Dynamische Berechnung des Ziel-Quaternions basierend auf der gewünschten Ausrichtung relativ zur Schwerkraft.

---

### 5. `arm_renderer.py` - Kamera-Steuerung mit Euler-Winkeln (Zeile 76-78, 218-219)

**Problem:** Kamerarotation basiert auf akkumulierten Euler-Winkeln.

```python
self.cam_rot_x += dy * 0.5
self.cam_rot_y += dx * 0.5
```

Und später:

```python
glRotatef(self.cam_rot_x, 1, 0, 0)
glRotatef(self.cam_rot_y, 0, 1, 0)
```

**Warum Gimbal Lock?** Bei extremen Kamerawinkeln (cam_rot_x ≈ ±90°) kann die Steuerung "einfrieren" oder springen.

**Lösung:** Kamerarotation durch eine Quaternion oder eine Arcball-Rotation ersetzen.

---

## ✅ Bereits korrekt umgesetzt (Quaternion-basiert)

| Datei | Funktion | Status |
|-------|----------|--------|
| `utils.py` | `q_mult()`, `q_conjugate()`, `q_normalize()` | ✅ Gimbal Lock frei |
| `utils.py` | `q_rotate_vec()` | ✅ Gimbal Lock frei |
| `utils.py` | `q_to_matrix()` | ✅ Gimbal Lock frei |
| `sensor_manager.py` | Quaternion-basierte Kalibrierung | ✅ Gimbal Lock frei |
| `arm_renderer.py` | Arm-Rotation via `glMultMatrixf(q_to_matrix())` | ✅ Gimbal Lock frei |

---

## 📋 Zusammenfassung der Lösungsansätze

| Problem | Lösung |
|---------|--------|
| `q_to_euler()` Gimbal Lock | Nur für Debug nutzen, nie für Berechnungen |
| `glRotatef()` Kombinationen | Durch Quaternion-Matrix ersetzen |
| Pose-Erkennung ungenau | Achsen-Projektion statt Gesamtwinkel |
| Hardcoded Quaternions | Dynamisch berechnen |
| Euler-Kamera | Arcball oder Quaternion-Kamera |

---

## 🎯 Priorität der Fixes

1. **Hoch:** Pose-Erkennung verbessern (falsche Erkennung bei seitlicher Armbewegung)
2. **Mittel:** Kamera-Steuerung bei extremen Winkeln
3. **Niedrig:** `q_to_euler()` (wird nur für Debug genutzt)
