import os
import csv
import time
from config import LOG_DIR, COOLDOWN, PRESENCE_THRESHOLD
from utils import get_now

present_students = set()
presence_counter = {}
last_seen = {}
attendance_finalized = False

def save_attendance(name, subject, status):
    from utils import get_now
    import os, csv

    date = get_now().strftime("%Y-%m-%d")
    time_str = get_now().strftime("%H:%M:%S")

    os.makedirs("logs", exist_ok=True)
    file = f"logs/attendance_{date}.csv"

    write_header = not os.path.exists(file)

    with open(file, "a", newline="") as f:
        writer = csv.writer(f)

        if write_header:
            writer.writerow(["Name", "Date", "Time", "Subject", "Status"])

        # THIS IS WHERE YOUR LINE GOES
        writer.writerow([name, date, time_str, subject, status])

def mark_present(name, subject):
    if name not in presence_counter:
        presence_counter[name] = 0

    presence_counter[name] += 1

    if presence_counter[name] < PRESENCE_THRESHOLD:
        return

    now = time.time()

    if name in last_seen and now - last_seen[name] < COOLDOWN:
        return

    last_seen[name] = now

    if name not in present_students:
        present_students.add(name)
        save_attendance(name, subject, "Present")
        print(f"{name} PRESENT in {subject}")

def finalize(students, slot_mapping, slot_key):
    global attendance_finalized

    if attendance_finalized:
        return

    print("Finalizing attendance...")

    day = get_now().strftime("%A")

    for s in students:
        subject = slot_mapping.get(day, {}).get(slot_key, {}).get(s)
        if subject and s not in present_students:
            save_attendance(s, subject, "Absent")
            print(f"{s} ABSENT in {subject}")

    attendance_finalized = True

def reset_state():
    global attendance_finalized
    present_students.clear()
    presence_counter.clear()
    last_seen.clear()
    attendance_finalized = False