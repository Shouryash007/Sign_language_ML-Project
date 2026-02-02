# collect_data.py

import serial
import csv
import time

# configuration
PORT        = 'COM3'              #  ESP32 port name
BAUD_RATE   = 115200              
CSV_PATH    = 'data/gesture_data.csv'

FEATURES = [
    'flex1','flex2','flex3','flex4','flex5',
    'accelX','accelY','accelZ',
    'gyroX','gyroY','gyroZ'
]

BURST_SIZE    = 50    # number of samples per gesture
BURST_DELAY   = 0.05  # 50 ms between samples
PREPARE_DELAY = 1.0   # time to get into gesture

# CSV file opening
with open(CSV_PATH, 'w', newline='') as f:
    csv.writer(f).writerow(FEATURES + ['label'])

# Opening the serials
ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
time.sleep(2)               # wait for ESP32 reset
ser.reset_input_buffer()    # clear any junk
print(f"Connected to {ser.port}\n")

print("Gesture Burst Collector")
print("Type gesture label and press ENTER to record.")
print("Just ENTER to quit.\n")

try:
    while True:
        label = input("Label: ").strip()
        if not label:
            break

        print(f"Get ready to hold '{label}' gesture…")
        time.sleep(PREPARE_DELAY)

        # flush any leftover to start fresh
        ser.reset_input_buffer()
        print(f"Recording {BURST_SIZE} samples for '{label}'…")

        # collection of samples
        rows = []
        for i in range(BURST_SIZE):
            raw = ser.readline().decode('ascii', errors='ignore').strip()
            parts = [p.strip() for p in raw.split(',')]
            if len(parts) != len(FEATURES):
                print(f"Frame {i}: malformed ({parts})")
                continue

            try:
                vals = [float(p) for p in parts]
            except:
                print(f"Frame {i}: non-numeric ({parts})")
                continue

            rows.append(vals)
            # live-printing the flex sensors
            flexs = vals[:5]
            print(f"   {i+1:02d}: flex = {flexs}")
            time.sleep(BURST_DELAY)

        # write the frames to CSV
        with open(CSV_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            for vals in rows:
                writer.writerow(vals + [label])

        print(f"Saved {len(rows)} frames for '{label}'\n")

except KeyboardInterrupt:
    pass

print("\nDone collecting.")
print(f"Data → {CSV_PATH}")
ser.close()