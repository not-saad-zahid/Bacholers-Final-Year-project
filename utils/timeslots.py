from datetime import datetime, timedelta

def generate_time_slots(days, start_time_str, end_time_str, lecture_duration, break_duration=0):
    """Generate time slots with special handling for Friday prayer break"""
    start_dt = datetime.strptime(start_time_str, "%I:%M %p")
    end_dt = datetime.strptime(end_time_str, "%I:%M %p")
    slots = []
    
    for day in days:
        # Friday special handling
        if day == "Friday":
            # First session: start_time to 12:15 PM
            friday_morning_end = datetime.strptime("12:15 PM", "%I:%M %p")
            morning_slots = generate_day_slots(
                start_dt, 
                friday_morning_end, 
                lecture_duration, 
                break_duration, 
                day
            )
            
            # Prayer break: 12:15 PM - 1:30 PM
            # Then session: 1:30 PM to end_time
            friday_afternoon_start = datetime.strptime("1:30 PM", "%I:%M %p")
            afternoon_slots = generate_day_slots(
                friday_afternoon_start,
                end_dt,
                lecture_duration,
                break_duration,
                day
            )
            
            slots.extend(morning_slots + afternoon_slots)
        else:
            # Regular day handling
            day_slots = generate_day_slots(
                start_dt,
                end_dt,
                lecture_duration,
                break_duration,
                day
            )
            slots.extend(day_slots)
    
    return slots

def generate_day_slots(start, end, lecture_duration, break_duration, day):
    """Helper function to generate slots for a single day"""
    slots = []
    current = start
    while current + timedelta(minutes=lecture_duration) <= end:
        end_slot = current + timedelta(minutes=lecture_duration)
        slots.append(
            f"{day} {current.strftime('%I:%M %p')}-{end_slot.strftime('%I:%M %p')}"
        )
        current = end_slot + timedelta(minutes=break_duration)
    return slots
