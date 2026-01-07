import board
import busio
import adafruit_tca9548a
import time

# --- I2C INITIALISIERUNG ---
# Wir nutzen die Standard SCL/SDA Pins des Raspberry Pi
try:
    i2c = busio.I2C(board.SCL, board.SDA)
except Exception as e:
    print(f"KRITISCHER FEHLER: Konnte I2C Bus nicht öffnen.")
    print(f"Details: {e}")
    exit(1)

# --- MULTIPLEXER SETUP ---
try:
    # Adresse 0x70 ist Standard für PCA9548A und TCA9548A
    tca = adafruit_tca9548a.TCA9548A(i2c, address=0x70)
    print("\n------------------------------------------------")
    print("ERFOLG: Multiplexer (0x70) auf dem Haupt-Bus gefunden!")
    print("------------------------------------------------\n")
except Exception as e:
    print("\n------------------------------------------------")
    print("FEHLER: Kein Multiplexer bei Adresse 0x70 gefunden!")
    print("Bitte Verkabelung (SDA, SCL, VIN, GND) prüfen.")
    print("------------------------------------------------\n")
    exit(1)

# --- SCAN SCHLEIFE ---
print("Starte Scan aller 8 Kanäle...\n")

found_sensors = []

for channel in range(8):
    print(f"[Kanal {channel}]: ", end="")
    
    # Versuch, den Kanal zu sperren (Lock), um exklusiven Zugriff zu haben
    if tca[channel].try_lock():
        try:
            # Scan durchführen
            addresses = tca[channel].scan()
            
            # Ergebnisse filtern und anzeigen
            devices = []
            for addr in addresses:
                # 0x70 ist der Mux selbst (er taucht immer auf), den ignorieren wir in der Ausgabe
                if addr != 0x70:
                    devices.append(hex(addr))
            
            if devices:
                print(f"GERÄTE GEFUNDEN -> {', '.join(devices)}")
                # Spezieller Check für BNO055 (Standard ist 0x28 oder 0x29)
                if '0x28' in devices or '0x29' in devices:
                    found_sensors.append(channel)
            else:
                print("--- (Leer)")
                
        except Exception as e:
            print(f"Fehler beim Scannen: {e}")
        finally:
            # WICHTIG: Kanal wieder freigeben!
            tca[channel].unlock()
    else:
        print("Konnte Kanal nicht sperren.")
    
    # Kurze Pause für Stabilität
    time.sleep(0.1)

print("\n------------------------------------------------")
if len(found_sensors) > 0:
    print(f"BNO055 Sensoren (0x28/0x29) gefunden auf Kanal: {found_sensors}")
    if 2 in found_sensors and 7 in found_sensors:
        print(">> PERFEKT! Sensoren auf Kanal 2 und 7 sind bereit.")
    else:
        print(f">> ACHTUNG: Du erwartest Sensoren auf 2 und 7.")
        print(f"   Gefunden wurden sie aber nur auf: {found_sensors if found_sensors else 'NIRGENDWO'}")
else:
    print("KEINE SENSOREN (0x28) GEFUNDEN.")
    print("Tipp: Prüfe VIN und GND direkt an den Sensoren!")
print("------------------------------------------------")
