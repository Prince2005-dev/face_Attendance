import cv2
import json
import time
from datetime import datetime
from collections import deque

from utils import get_now, get_slot_key
from facerecognition import recognize_face
from attendance import mark_present, finalize, reset_state, present_students
from config import RECOGNITION_COOLDOWN

# ===== LOAD DATA =====
with open("data/students.json") as f:
    data = json.load(f)

students = data["students"]
slots = data["slots"]
working_days = data["working_days"]
slot_mapping = data["slot_mapping"]

# ===== CAMERA =====
cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

last_recognition_time = 0
last_name = "Unknown"
last_distance = None
current_slot_key = None

#  STABILITY
name_buffer = deque(maxlen=5)

#  LOCK
locked_name = None
lock_time = 0
LOCK_DURATION = 10

print("System started...")

# ===== SLOT FUNCTION =====
def get_current_slot(slots):
    now = get_now().time()

    for slot in slots:
        start = datetime.strptime(slot["start"], "%H:%M").time()
        end = datetime.strptime(slot["end"], "%H:%M").time()

        if start <= now <= end:
            return slot
    return None


while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = get_now()
    day = now.strftime("%A")

    #  Skip non-working days
    if day not in working_days:
        cv2.putText(frame, "Holiday", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        cv2.imshow("Attendance System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # ===== SLOT =====
    slot = get_current_slot(slots)
    slot_key = get_slot_key(slot)

    display_name = "Unknown"
    display_subject = ""

    # ===== FACE DETECTION =====
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # ===== TIME WINDOW LOGIC =====
    minutes_passed = None
    if slot:
        slot_start = datetime.strptime(slot["start"], "%H:%M")
        slot_start_dt = now.replace(
            hour=slot_start.hour,
            minute=slot_start.minute,
            second=0
        )
        minutes_passed = (now - slot_start_dt).seconds / 60

    for (x, y, w, h) in faces:
        face_img = frame[y:y+h, x:x+w]

        # ===== RECOGNITION =====
        if time.time() - last_recognition_time > RECOGNITION_COOLDOWN:
            name, distance = recognize_face(face_img)
            last_recognition_time = time.time()
            last_name = name
            last_distance = distance
        else:
            name = last_name
            distance = last_distance

        name_buffer.append(name)

        current_time = time.time()

        #  LOCK LOGIC
        if locked_name and (current_time - lock_time < LOCK_DURATION):
            stable_name = locked_name
        else:
            if (
                name_buffer.count(name) >= 3
                and distance is not None
                and distance < 0.25
            ):
                stable_name = name
                locked_name = name
                lock_time = current_time
            else:
                stable_name = "Unknown"

        subject = slot_mapping.get(day, {}).get(slot_key, {}).get(stable_name)

        display_name = stable_name
        display_subject = subject if subject else ""

        # ===== ATTENDANCE RULE =====
        if stable_name != "Unknown" and subject:
            if minutes_passed is not None and minutes_passed <= 20:
                mark_present(stable_name, subject)
            else:
                cv2.putText(frame, "Late → Absent", (400, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        color = (0,255,0) if stable_name != "Unknown" else (0,0,255)
        cv2.rectangle(frame, (x,y), (x+w,y+h), color, 2)

        cv2.putText(frame, stable_name, (x,y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    # ===== SLOT CHANGE =====
    if slot_key != current_slot_key:
        if current_slot_key is not None:
            finalize(students, slot_mapping, current_slot_key)

        current_slot_key = slot_key
        reset_state()
        name_buffer.clear()
        locked_name = None

    # ===== UI =====
    cv2.putText(frame, f"Time: {now.strftime('%H:%M:%S')}", (20,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Slot: {slot_key}", (20,60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    cv2.putText(frame, f"Name: {display_name}", (20,90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.putText(frame, f"Subject: {display_subject}", (20,120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

    cv2.putText(frame, f"Present: {len(present_students)}", (20,150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    if last_distance is not None:
        cv2.putText(frame, f"Conf: {last_distance:.2f}", (20,180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.imshow("Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()