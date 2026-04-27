from datetime import datetime
from config import TEST_MODE, TEST_TIME

def get_now():
    if TEST_MODE:
        today = datetime.now().strftime("%Y-%m-%d")
        return datetime.strptime(f"{today} {TEST_TIME}", "%Y-%m-%d %H:%M")
    return datetime.now()

def get_slot_key(slot):
    return f"{slot['start']}-{slot['end']}" if slot else None

def get_current_slot(timetable):
    now = get_now().time()
    day = get_now().strftime("%A")

    for slot in timetable.get(day, []):
        start = datetime.strptime(slot["start"], "%H:%M").time()
        end = datetime.strptime(slot["end"], "%H:%M").time()

        if start <= now <= end:
            return slot

    return None