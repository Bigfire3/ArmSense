# ArmSense

ArmSense ist ein Echtzeit-Visualisierungssystem für Armbewegungen. Es nutzt Bewegungssensoren (IMUs), um die Orientierung von Ober- und Unterarm zu erfassen und einen virtuellen 3D-Arm entsprechend zu animieren. Das System erkennt zudem definierte Posen (Gestenerkennung).

## Funktionsweise

Das System liest Quaternion-Daten von BNO055-Sensoren aus, verarbeitet diese kinematisch und stellt sie grafisch dar:

1.  **Hardware-Layer (`hardware/`)**:
    *   Kommuniziert mit einem I2C-Multiplexer (TCA9548A) und mehreren BNO055 Sensoren.
    *   Filtert Signale (Glitch-Rejection) und handhabt Sensor-Mapping.
    *   Stellt Rohdaten als Quaternionen zur Verfügung.

2.  **Visualisierung (`visualization/`)**:
    *   Nutzt **PyGame** und **OpenGL** für das Rendering.
    *   Zeichnet einen schematischen Körper und überträgt die Sensor-Rotationen auf 3D-Zylinder (Oberarm/Unterarm).
    *   Ermöglicht freie Kamerasteuerung.

3.  **Logik & Erkennung (`pose_detector.py`)**:
    *   Berechnet Winkelabweichungen relativ zu Referenzpostionen.
    *   Identifiziert Posen wie "Arm hängt", "L-Form" oder "Vorne gestreckt" basierend auf konfigurierten Winkeltoleranzen.

## Projektstruktur

*   **`main.py`**: Einstiegspunkt. Initialisiert Sensoren und Grafik, startet den Main-Loop.
*   **`config.py`**: Zentrale Konfiguration (Sensor-Adressen, Körpermaße, Filter-Parameter).
*   **`pose_detector.py`**: Algorithmen zur Erkennung statischer Armhaltungen.
*   **`hardware/sensor_manager.py`**: Abstraktionsschicht für Sensor-Zugriff und Kalibrierung.
*   **`visualization/arm_renderer.py`**: OpenGL-Rendering-Pipeline und Input-Handling.

## Hardware Setup

*   **Sensoren**: Bosch BNO055 (IMU).
*   **Multiplexer**: TCA9548A (für mehrere Sensoren am selben I2C-Bus).
*   **Mapping** (in `config.py`):
    *   Kanal 2: Oberarm (Base)
    *   Kanal 7: Unterarm (Arm)

## Bedienung

Starten des Programms:
```bash
python ArmSense/main.py
```

### Steuerung (Tastatur & Maus)

| Taste / Aktion | Funktion |
| :--- | :--- |
| **0 / Leertaste** | **Null-Kalibrierung**: Arm muss locker nach unten hängen. Setzt den Nullpunkt. |
| **1** | **Forward-Kalibrierung**: Arm muss waagerecht nach vorne zeigen. Korrigiert die Ausrichtung. |
| **9** | **Posen-Erkennung**: Schaltet die automatische Erkennung der aktuellen Haltung an/aus. |
| **Maus (Links)** | Gedrückt halten und ziehen, um die **Kamera** um das Modell zu drehen. |
