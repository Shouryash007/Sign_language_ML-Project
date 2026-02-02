# glove_reciever.py

import serial
import threading
import queue
import time
import pandas as pd
import joblib
from collections import Counter

# CONFIGURATION
PORT          = 'COM3'
BAUD_RATE     = 115200
PIPELINE_PATH = 'models/gesture_pipeline.pkl'

FEATURE_NAMES = [
    "flex1","flex2","flex3","flex4","flex5",
    "accelX","accelY","accelZ",
    "gyroX","gyroY","gyroZ"
]

VOTE_WINDOW = 3       # reduce flicker by voting over last N
COOLDOWN    = 0.5     # min seconds between spoken gestures

#  LOAD THE TRAINED PIPELINE 
pipeline = joblib.load(PIPELINE_PATH)
print(f" Loaded pipeline from {PIPELINE_PATH}")

# SPEECH WORKING
speech_q = queue.Queue()

def speech_worker():
    while True:
        text = speech_q.get()
        if text is None:
            break
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            print("🔈 SpeechError:", e)
        finally:
            speech_q.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

# SERIAL SETUP
ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
time.sleep(2)
ser.reset_input_buffer()
print(f"🧤 Connected to {PORT} @ {BAUD_RATE}bps\n")

last_time    = 0
last_spoken  = None
vote_buffer  = []

print(" Gesture interpreter running. Ctrl+C to stop.\n")
try:
    while True:
        raw = ser.readline().decode('ascii', errors='ignore').strip()
        if not raw:
            continue

        parts = [p.strip() for p in raw.split(',')]
        if len(parts) != len(FEATURE_NAMES):
            continue

        try:
            vals = list(map(float, parts))
        except ValueError:
            continue

        # predict
        df = pd.DataFrame([vals], columns=FEATURE_NAMES)
        pred = pipeline.predict(df)[0]

        # rolling vote
        vote_buffer.append(pred)
        if len(vote_buffer) > VOTE_WINDOW:
            vote_buffer.pop(0)
        if VOTE_WINDOW > 1:
            pred = Counter(vote_buffer).most_common(1)[0][0]

        now = time.time()
        if pred != last_spoken and (now - last_time) >= COOLDOWN:
            print(f" Detected gesture → {pred}")
            speech_q.put(pred)
            last_spoken = pred
            last_time   = now

except KeyboardInterrupt:
    pass

# teardown
speech_q.put(None)
ser.close()
print("\n Interpreter stopped.")