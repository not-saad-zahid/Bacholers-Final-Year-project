from datetime import datetime, timedelta

def generate_time_slots(days, start_time_str, end_time_str, lecture_duration, break_duration=0):
    """Generate time slots with consistent handling for all days"""
    start_dt = datetime.strptime(start_time_str, "%I:%M %p")
    end_dt = datetime.strptime(end_time_str, "%I:%M %p")
    slots = []
    
    for day in days:
        # Generate slots for each day uniformly
        current = start_dt
        while current + timedelta(minutes=lecture_duration) <= end_dt:
            end_slot = current + timedelta(minutes=lecture_duration)
            slots.append(
                f"{day} {current.strftime('%I:%M %p')}-{end_slot.strftime('%I:%M %p')}"
            )
            current = end_slot  # Remove break by directly using end time as next start
    
    return slots
