from datetime import datetime, timedelta

def generate_time_slots(days, start_time_str, end_time_str, lecture_duration, break_duration=0):
    """
    days: list of weekday names, e.g. ["Monday","Tuesday",...]
    start_time_str, end_time_str: "HH:MM AM/PM"
    lecture_duration, break_duration: in minutes
    Returns a list of strings like "Monday 08:00 AM-09:00 AM"
    """
    start_dt = datetime.strptime(start_time_str, "%I:%M %p")
    end_dt   = datetime.strptime(end_time_str,   "%I:%M %p")
    total_minutes = (end_dt.hour*60 + end_dt.minute) - (start_dt.hour*60 + start_dt.minute)
    slot_length = lecture_duration + break_duration
    slots_per_day = total_minutes // slot_length
    slots = []
    for day in days:
        current = start_dt
        for _ in range(slots_per_day):
            end_slot = current + timedelta(minutes=lecture_duration)
            slots.append(f"{day} {current.strftime('%I:%M %p')}-{end_slot.strftime('%I:%M %p')}")
            current = current + timedelta(minutes=slot_length)
    return slots
