from datetime import datetime, timedelta

def generate_time_slots(days, start_time_str, end_time_str, lecture_duration, break_duration=0, breaks=None):
    """Generate time slots with consistent handling for all days, skipping user-defined breaks"""
    start_dt = datetime.strptime(start_time_str, "%I:%M %p")
    end_dt = datetime.strptime(end_time_str, "%I:%M %p")
    slots = []
    breaks = breaks or []

    # Preprocess breaks into a dict: {day: [(start, end), ...]}
    breaks_by_day = {}
    for br in breaks:
        day = br["day"]
        b_start = datetime.strptime(br["start"], "%I:%M %p")
        b_end = datetime.strptime(br["end"], "%I:%M %p")
        breaks_by_day.setdefault(day, []).append((b_start, b_end))

    for day in days:
        current = start_dt
        while current + timedelta(minutes=lecture_duration) <= end_dt:
            end_slot = current + timedelta(minutes=lecture_duration)
            # Check if this slot overlaps with any break for this day
            skip = False
            for b_start, b_end in breaks_by_day.get(day, []):
                # If slot overlaps with break
                if not (end_slot <= b_start or current >= b_end):
                    skip = True
                    break
            if not skip:
                slots.append(
                    f"{day} {current.strftime('%I:%M %p')}-{end_slot.strftime('%I:%M %p')}"
                )
            current = end_slot  # Remove break by directly using end time as next start

    return slots
