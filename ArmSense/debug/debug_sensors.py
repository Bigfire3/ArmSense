import sys
import os
import time
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Pfad erweitern
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.sensor_manager import SensorManager
from utils import q_to_euler

# Configuration
HISTORY_LEN = 100  # How many data points to show on screen
INTERVAL = 100     # Update interval in milliseconds

def main():
    print("--- IMU Live Graph ---")
    print("Initializing SensorManager...")
    
    # Initialize your hardware
    try:
        sensors = SensorManager()
    except Exception as e:
        print(f"Error initializing hardware: {e}")
        return

    # --- Data Storage ---
    # We use deques (double-ended queues) with a fixed length 
    # to automatically discard old data.
    x_data = deque(maxlen=HISTORY_LEN)
    
    # Base Data Containers
    base_h = deque(maxlen=HISTORY_LEN)
    base_r = deque(maxlen=HISTORY_LEN)
    base_p = deque(maxlen=HISTORY_LEN)
    
    # Arm Data Containers
    arm_h = deque(maxlen=HISTORY_LEN)
    arm_r = deque(maxlen=HISTORY_LEN)
    arm_p = deque(maxlen=HISTORY_LEN)

    # Pre-fill x_data simply as a counter 0..N
    # (or you can use time.time() if you want absolute timestamps)
    for i in range(HISTORY_LEN):
        x_data.append(i)
        base_h.append(0); base_r.append(0); base_p.append(0)
        arm_h.append(0);  arm_r.append(0);  arm_p.append(0)

    # --- Plot Setup ---
    # Create a figure with 2 subplots vertically
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
    fig.suptitle('Real-Time IMU Data (Base vs. Arm)')

    # Setup Subplot 1: BASE
    ax1.set_title("BASE (Oberarm)")
    ax1.set_ylabel("Angle (Degrees)")
    line_bh, = ax1.plot(x_data, base_h, label='Heading', color='red')
    line_br, = ax1.plot(x_data, base_r, label='Roll',    color='green')
    line_bp, = ax1.plot(x_data, base_p, label='Pitch',   color='blue')
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # Setup Subplot 2: ARM
    ax2.set_title("ARM (Unterarm)")
    ax2.set_xlabel("Samples")
    ax2.set_ylabel("Angle (Degrees)")
    line_ah, = ax2.plot(x_data, arm_h, label='Heading', color='red')
    line_ar, = ax2.plot(x_data, arm_r, label='Roll',    color='green')
    line_ap, = ax2.plot(x_data, arm_p, label='Pitch',   color='blue')
    ax2.legend(loc='upper right')
    ax2.grid(True)

    # --- Update Function ---
    def update(frame):
        # 1. Fetch data from hardware
        data = sensors.get_data()
        
        # Extract Quaternions (Default to Identity)
        q_b = data.get("base", (1, 0, 0, 0))
        q_a = data.get("arm",  (1, 0, 0, 0))

        # Convert to Euler
        b_h_val, b_r_val, b_p_val = q_to_euler(q_b)
        a_h_val, a_r_val, a_p_val = q_to_euler(q_a)

        # 2. Update Data Containers
        # (x_data stays fixed as 0..100, we just shift y-values if using simple scrolling)
        # However, a cleaner way for 'rolling' graphs is just appending new data 
        # and matplotlib handles the plotting of the deque.
        
        base_h.append(b_h_val)
        base_r.append(b_r_val)
        base_p.append(b_p_val)
        
        arm_h.append(a_h_val)
        arm_r.append(a_r_val)
        arm_p.append(a_p_val)

        # 3. Update Lines on the Plot
        line_bh.set_ydata(base_h)
        line_br.set_ydata(base_r)
        line_bp.set_ydata(base_p)
        
        line_ah.set_ydata(arm_h)
        line_ar.set_ydata(arm_r)
        line_ap.set_ydata(arm_p)

        # 4. Rescale Y-Axis dynamically
        # This ensures if angles wrap or jump, the graph adapts
        ax1.relim()
        ax1.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()

        return line_bh, line_br, line_bp, line_ah, line_ar, line_ap

    # --- Start Animation ---
    print("Graph started. Close the window to stop.")
    ani = animation.FuncAnimation(fig, update, interval=INTERVAL, blit=False)
    
    plt.show()

if __name__ == "__main__":
    main()
