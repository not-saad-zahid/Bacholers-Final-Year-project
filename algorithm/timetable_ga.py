"""
Genetic algorithm for generating class timetables with improved handling of teacher conflicts.
"""
import random
from datetime import datetime, timedelta
from tkinter import messagebox

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

class TimetableGeneticAlgorithm:
    def __init__(self,
                 *,
                 entries,
                 time_slots_input,
                 lectures_per_course,
                 course_exceptions=None,
                 population_size=100,
                 max_generations=150,
                 mutation_rate=0.20,
                 breaks=None):

        if not entries:
            raise ValueError("No timetable entries provided to GA.")
        self.entries = entries

        if not time_slots_input:
            raise ValueError("No time slots provided to GA.")
        self.unique_time_slots = list(set(time_slots_input))

        self.POPULATION_SIZE = population_size
        self.MAX_GENERATIONS = max_generations
        self.MUTATION_RATE = mutation_rate
        self.LECTURES_PER_COURSE = lectures_per_course
        self.course_exceptions = course_exceptions or {}
        self.breaks = breaks or []

        # Convert room names to string
        for entry in self.entries:
            entry['room'] = str(entry['room'])

        # Extract unique sets
        self.unique_rooms = list(set(e['room'] for e in self.entries))
        self.unique_teachers = list(set(e['teacher'] for e in self.entries))
        # Use (semester, class_section) as unique identifier
        self.unique_semester_sections = list(set((e['semester'], e['class_section']) for e in self.entries))

        # Group time slots by day
        self.time_slots_by_day = {}
        for ts in self.unique_time_slots:
            try:
                day = ts.split()[0]
                self.time_slots_by_day.setdefault(day, []).append(ts)
            except IndexError:
                print(f"Warning: Could not parse day from time slot: {ts}")

        # Define ordered weekdays and filter to available
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        self.ordered_days = [d for d in day_order if d in self.time_slots_by_day]

        self.best_fitness_history = []
        print(f"GA initialized with {len(self.entries)} entries, {len(self.unique_time_slots)} time slots.")
        print(f"Lectures per course: {self.LECTURES_PER_COURSE}")

        # Store required lectures for each course (now keyed by (semester, section, code))
        self.required_lectures = {}
        for entry in self.entries:
            code = entry['course_code']
            semester = entry['semester']
            section = entry['class_section']
            self.required_lectures[(semester, section, code)] = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
        
        # Create a mapping of teachers to courses they teach
        self.teacher_courses = {}
        for entry in self.entries:
            teacher = entry['teacher']
            if teacher not in self.teacher_courses:
                self.teacher_courses[teacher] = []
            course_key = (entry['course_name'], entry['course_code'], entry['class_section'])
            if course_key not in self.teacher_courses[teacher]:
                self.teacher_courses[teacher].append(course_key)
        
        # Debug available vs required lectures
        self.debug_timetable_requirements()

    def debug_timetable_requirements(self):
        """Debug function to check lecture requirements vs available slots"""
        total_lectures = 0
        lectures_by_section = {}
        lectures_by_semester_section = {}
        lectures_by_semester_section_course = {}
        
        # Count required lectures by section and section-course
        for entry in self.entries:
            semester = entry['semester']
            section = entry['class_section']
            code = entry['course_code']
            course = entry['course_name']
            required = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
            
            key = (semester, section)
            if key not in lectures_by_semester_section:
                lectures_by_semester_section[key] = 0
                lectures_by_semester_section_course[key] = {}
            
            course_key = (course, code)
            if course_key not in lectures_by_semester_section_course[key]:
                lectures_by_semester_section[key] += required
                total_lectures += required
                lectures_by_semester_section_course[key][course_key] = required
        
        # Count available slots
        total_slots = len(self.unique_time_slots)
        
        print(f"Total required lectures across all sections: {total_lectures}")
        print(f"Available unique time slots: {total_slots}")
        print("Lectures required by section:")
        overbooked_sections = []
        for (semester, section), count in lectures_by_semester_section.items():
            print(f"  Semester '{semester}' Section '{section}': {count} lectures")
            if count > total_slots:
                print(f"  WARNING: Semester '{semester}' Section '{section}' requires {count} lectures but only {total_slots} slots available")
                overbooked_sections.append(((semester, section), count))
        
        # Show message box and raise exception if any section is overbooked
        if overbooked_sections:
            msg = "Cannot generate timetable:\n"
            for (semester, section), count in overbooked_sections:
                msg += f"'{semester}' '{section}' requires {count} lectures but only {total_slots} time slots are available.\n"
            messagebox.showerror("Timetable Generation Error", msg)
            raise ValueError(msg)

        # Print teacher workload
        print("\nTeacher assignments:")
        for teacher, courses in self.teacher_courses.items():
            total_lectures = 0
            for course_name, course_code, section in courses:
                required = self.course_exceptions.get(course_code, self.LECTURES_PER_COURSE)
                total_lectures += required
            print(f"  {teacher}: {len(courses)} courses, approximately {total_lectures} lectures")

    def _create_random_timetable(self):
        """Create a random timetable with improved teacher conflict handling"""
        timetable = {}
        # Use (semester, section) as key
        section_time_slot_usage = {sem_sec: set() for sem_sec in self.unique_semester_sections}
        teacher_time_slot_usage = {teacher: set() for teacher in self.unique_teachers}
        course_assignments = {}

        # Group entries by (semester, section)
        entries_by_semester_section = {}
        for entry in self.entries:
            sem_sec = (entry['semester'], entry['class_section'])
            if sem_sec not in entries_by_semester_section:
                entries_by_semester_section[sem_sec] = []
            entries_by_semester_section[sem_sec].append(entry)

        # For each (semester, section), do course assignment separately
        for sem_sec, section_entries in entries_by_semester_section.items():
            semester, section = sem_sec
            # Prepare a list of (course, section, code, required_lectures) and sort descending by required lectures
            course_info = []
            for entry in section_entries:
                course = entry['course_name']
                code = entry['course_code']
                teacher = entry['teacher']
                required_lectures = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
                course_info.append((course, section, code, required_lectures, teacher, entry, semester))
            
            # Sort by required_lectures descending (prioritize courses with more lectures)
            course_info.sort(key=lambda x: -x[3])

            # Prepare ordered list of all (day, time) slots for this section
            all_times = sorted({ts.split(' ', 1)[1] for ts in self.unique_time_slots})
            all_slots = []
            for time in all_times:
                for day in self.ordered_days:
                    slot_key = f"{day} {time}"
                    if slot_key in self.unique_time_slots:
                        all_slots.append((day, time))

            # Randomly shuffle the time slots to avoid bias
            # We'll use this for fallback assignment
            all_slots_shuffled = all_slots.copy()
            random.shuffle(all_slots_shuffled)
            
            # Create a second copy of slots we'll use for initial preferred time assignment
            # We'll try to assign consecutive days first when possible
            preferred_slots = []
            for time in all_times:
                # For each time slot (e.g. 7:30-8:30), try to find consecutive days
                day_groups = []
                current_group = []
                
                for day in self.ordered_days:
                    slot_key = f"{day} {time}"
                    if slot_key in self.unique_time_slots:
                        current_group.append(day)
                    else:
                        if current_group:
                            day_groups.append(current_group)
                            current_group = []
                
                if current_group:  # Don't forget the last group
                    day_groups.append(current_group)
                
                # Add these grouped days to preferred slots
                for group in day_groups:
                    for day in group:
                        preferred_slots.append((day, time))

            # For each course in this section, assign time slots
            for course, section, code, required_lectures, teacher, entry, semester in course_info:
                assigned_slots = []
                key_prefix = (semester, course, section, code)
                
                # First attempt: try to use consecutive days at the same time if possible
                if required_lectures <= len(self.ordered_days):  # Only try this for courses that could fit consecutive days
                    for time in all_times:
                        # Find consecutive days with available slots that don't conflict with teacher's schedule
                        consecutive_days = []
                        for day in self.ordered_days:
                            slot_key = f"{day} {time}"
                            if (slot_key in self.unique_time_slots
                                and slot_key not in section_time_slot_usage[sem_sec]
                                and slot_key not in teacher_time_slot_usage[teacher]):  # Check teacher availability
                                consecutive_days.append(day)
                            else:
                                # Break in consecutive days, check if we have enough
                                if len(consecutive_days) >= required_lectures:
                                    break
                                consecutive_days = []  # Reset and continue looking
                        
                        # If we found enough consecutive days at this time slot
                        if len(consecutive_days) >= required_lectures:
                            for i in range(required_lectures):
                                day = consecutive_days[i]
                                slot_key = f"{day} {time}"
                                assigned_slots.append((day, time))
                                section_time_slot_usage[sem_sec].add(slot_key)
                                teacher_time_slot_usage[teacher].add(slot_key)  # Mark teacher as busy
                            break  # We've assigned all needed slots for this course
                
                # Second attempt: try to find the same time slot on any days
                if len(assigned_slots) < required_lectures:
                    for time in all_times:
                        available_days = []
                        for day in self.ordered_days:
                            slot_key = f"{day} {time}"
                            if (slot_key in self.unique_time_slots
                                and slot_key not in section_time_slot_usage[sem_sec]
                                and slot_key not in teacher_time_slot_usage[teacher]):  # Check teacher availability
                                available_days.append(day)
                        
                        if len(available_days) >= required_lectures - len(assigned_slots):
                            needed = required_lectures - len(assigned_slots)
                            for i in range(needed):
                                day = available_days[i]
                                slot_key = f"{day} {time}"
                                assigned_slots.append((day, time))
                                section_time_slot_usage[sem_sec].add(slot_key)
                                teacher_time_slot_usage[teacher].add(slot_key)  # Mark teacher as busy
                            break  # We've assigned all needed slots for this course
                
                # Final attempt: use any available slots (fallback method)
                if len(assigned_slots) < required_lectures:
                    for day, time in all_slots_shuffled:
                        slot_key = f"{day} {time}"
                        if (slot_key not in section_time_slot_usage[sem_sec]
                            and slot_key not in teacher_time_slot_usage[teacher]):  # Check teacher availability
                            assigned_slots.append((day, time))
                            section_time_slot_usage[sem_sec].add(slot_key)
                            teacher_time_slot_usage[teacher].add(slot_key)  # Mark teacher as busy
                            if len(assigned_slots) == required_lectures:
                                break
                    
                    # If we still don't have enough, allow teacher conflicts (but warn about it)
                    if len(assigned_slots) < required_lectures:
                        print(f"WARNING: Teacher conflict may be unavoidable for {teacher} - {course} ({code})")
                        for day, time in all_slots_shuffled:
                            slot_key = f"{day} {time}"
                            if slot_key not in section_time_slot_usage[sem_sec]:
                                assigned_slots.append((day, time))
                                section_time_slot_usage[sem_sec].add(slot_key)
                                # Make note of potential teacher conflict but still add it
                                if slot_key in teacher_time_slot_usage[teacher]:
                                    print(f"CONFLICT: Teacher {teacher} double-booked at {slot_key}")
                                teacher_time_slot_usage[teacher].add(slot_key)
                                if len(assigned_slots) == required_lectures:
                                    break
                
                # Create timetable entries for this course
                for idx, (day, time) in enumerate(assigned_slots):
                    key = (semester, course, section, idx, code)
                    timetable[key] = {
                        'course_name': course,
                        'course_code': code,
                        'course_indicators': entry.get('course_indicators', ''),
                        'time_slot': f"{day} {time}",
                        'room': entry['room'],
                        'teacher': teacher,
                        'semester': semester,
                        'class_section': section
                    }

        # Final check: verify we haven't assigned conflicting slots
        self._verify_timetable_slots(timetable)
        return timetable

    def _verify_timetable_slots(self, timetable):
        """Verify that the timetable doesn't have conflicting slot assignments"""
        section_timeslots = {}
        teacher_timeslots = {}
        room_timeslots = {}

        # Track all types of conflicts
        teacher_conflicts = 0
        section_conflicts = 0
        room_conflicts = 0
        teacher_conflict_details = []

        for key, details in timetable.items():
            semester = details['semester']
            section = details['class_section']
            time_slot = details['time_slot']
            teacher = details['teacher']
            room = details['room']
            sem_sec = (semester, section)

            # Section-timeslot conflicts
            if sem_sec not in section_timeslots:
                section_timeslots[sem_sec] = {}
            if time_slot in section_timeslots[sem_sec]:
                section_conflicts += 1
                print(f"WARNING: Conflicting timeslot {time_slot} for semester {semester} section {section}")
                print(f"  - {section_timeslots[sem_sec][time_slot]['course_name']} vs {details['course_name']}")
            section_timeslots[sem_sec][time_slot] = details

            # Check teacher-timeslot conflicts
            if teacher not in teacher_timeslots:
                teacher_timeslots[teacher] = {}
            if time_slot in teacher_timeslots[teacher]:
                teacher_conflicts += 1
                teacher_conflict_details.append(
                    (teacher, time_slot, teacher_timeslots[teacher][time_slot], details)
                )
                print(f"WARNING: Conflicting timeslot {time_slot} for teacher {teacher}")
                print(f"  - {teacher_timeslots[teacher][time_slot]['course_name']} ({teacher_timeslots[teacher][time_slot]['class_section']}) vs {details['course_name']} ({details['class_section']})")
            teacher_timeslots[teacher][time_slot] = details

            # Check room-timeslot conflicts
            room_key = f"{room}_{time_slot}"
            if room_key in room_timeslots:
                room_conflicts += 1
                print(f"WARNING: Room conflict at {time_slot} in room {room}")
            room_timeslots[room_key] = details

        # If any teacher is double-booked, show error and stop
        if teacher_conflicts > 0:
            msg = "Cannot generate timetable:\n"
            msg += "The following teacher(s) are assigned to more than one class at the same time:\n"
            for teacher, time_slot, d1, d2 in teacher_conflict_details:
                msg += (
                    f"\nTeacher '{teacher}' has a conflict at '{time_slot}':\n"
                    f"  - {d1['course_name']} (Section {d1['class_section']})\n"
                    f"  - {d2['course_name']} (Section {d2['class_section']})\n"
                )
            # Add teacher workload info
            msg += "\nTeacher workload summary:\n"
            for teacher, slots in teacher_timeslots.items():
                msg += f"  {teacher}: {len(slots)} lectures assigned\n"
            messagebox.showerror("Timetable Generation Error", msg)
            raise ValueError(msg)
        
        # Print teacher daily workload
        teacher_daily_load = {}
        for teacher, slots in teacher_timeslots.items():
            for time_slot in slots:
                day = time_slot.split()[0]
                key = f"{teacher}_{day}"
                teacher_daily_load[key] = teacher_daily_load.get(key, 0) + 1
        
        print("\nTeacher daily workload:")
        for key, count in teacher_daily_load.items():
            teacher, day = key.rsplit("_", 1)
            if count > 3:
                print(f"  {teacher} on {day}: {count} lectures")

    def calculate_fitness(self, timetable):
        if timetable is None:
            return float('inf')

        score = 0
        time_slot_usage = {}  # Track all courses in each time slot
        room_usage = {}
        teacher_usage = {}
        class_usage = {}
        course_lecture_counts = {}
        teacher_daily_load = {}
        section_daily_load = {}
        course_time_slots = {}
        teacher_conflicts = 0  # Track specific teacher conflicts

        for key, details in timetable.items():
            course = details['course_name']
            code = details['course_code']
            section = details['class_section']
            time_slot = details['time_slot']
            room = details['room']
            teacher = details['teacher']
            semester = details['semester']
            
            day, time = time_slot.split(' ', 1)
            course_key = (course, section, code)

            # Check for multiple courses in same time slot
            if time_slot not in time_slot_usage:
                time_slot_usage[time_slot] = []
            time_slot_usage[time_slot].append(course_key)
            if len(time_slot_usage[time_slot]) > 1:
                score += 10000  # Very heavy penalty for multiple courses in same time slot

            # Track unique time slots used per course
            if course_key not in course_time_slots:
                course_time_slots[course_key] = set()
            course_time_slots[course_key].add(time)

            # Count lectures per course
            if course_key not in course_lecture_counts:
                course_lecture_counts[course_key] = 0
            course_lecture_counts[course_key] += 1

            # Room conflicts
            room_key = f"{time_slot}_{room}"
            if room_key in room_usage:
                score += 5000
            room_usage[room_key] = course_key

            # Teacher conflicts - HIGHER PENALTY
            teacher_key = f"{time_slot}_{teacher}"
            if teacher_key in teacher_usage:
                score += 10000  # Increased penalty for teacher conflicts
                teacher_conflicts += 1
            teacher_usage[teacher_key] = course_key

            # Class conflicts
            class_key = f"{time_slot}_{semester}_{section}"
            if class_key in class_usage:
                score += 5000
            class_usage[class_key] = course_key

            # Daily load tracking - stricter limits
            teacher_day_key = f"{teacher}_{day}"
            teacher_daily_load[teacher_day_key] = teacher_daily_load.get(teacher_day_key, 0) + 1
            if teacher_daily_load[teacher_day_key] > 3:  # Reduced from 4 to 3
                score += 100 * (teacher_daily_load[teacher_day_key] - 3)  # Increased penalty

            section_day_key = f"{semester}_{section}_{day}"
            section_daily_load[section_day_key] = section_daily_load.get(section_day_key, 0) + 1
            if section_daily_load[section_day_key] > 5:
                score += 50 * (section_daily_load[section_day_key] - 5)

        # Create a mapping of required lectures that accounts for semester-section-specific courses
        required_lectures = {}
        for entry in self.entries:
            course_key = (entry['semester'], entry['course_name'], entry['class_section'], entry['course_code'])
            required = self.course_exceptions.get(entry['course_code'], self.LECTURES_PER_COURSE)
            required_lectures[course_key] = required

        # Check lecture count requirements
        for course_key, required in required_lectures.items():
            actual = course_lecture_counts.get((course_key[1], course_key[2], course_key[3]), 0)
            if actual != required:
                score += 5000 * abs(actual - required)

        # Check same time slot requirement
        for course_key, times in course_time_slots.items():
            if len(times) > 1:
                score += 1000  # Penalty for different time slots
                # Add a slightly smaller penalty for each additional time slot
                score += 500 * (len(times) - 1)

        # Reward for consecutive days at same time
        for course_key, required in required_lectures.items():
            # Only check if course has multiple lectures
            if required > 1:
                # Get all time slots for this course
                course_slots = [details['time_slot'] for key, details in timetable.items() 
                               if (details['semester'], details['course_name'], details['class_section'], details['course_code']) == course_key]
                
                if not course_slots:
                    continue
                    
                # Check if all times are the same
                times = [slot.split(' ', 1)[1] for slot in course_slots]
                if len(set(times)) == 1:
                    # All lectures are at the same time, check for consecutive days
                    days = [slot.split(' ', 1)[0] for slot in course_slots]
                    day_indices = [self.ordered_days.index(day) for day in days if day in self.ordered_days]
                    day_indices.sort()
                    
                    # Check for consecutive days
                    consecutive = True
                    for i in range(1, len(day_indices)):
                        if day_indices[i] != day_indices[i-1] + 1:
                            consecutive = False
                            break
                    
                    if consecutive:
                        # Reward for consecutive days at same time
                        score -= 500  # Negative score is good
        
        # Add extra penalty for teacher conflicts
        score += 5000 * teacher_conflicts
                
        return score

    def generate_initial_population(self):
        population = []
        for i in range(self.POPULATION_SIZE):
            timetable = self._create_random_timetable()
            if timetable is None:
                print(f"Warning: Failed to create valid timetable for individual {i+1}.")
                continue
            population.append(timetable)
        if not population:
            raise ValueError("Failed to generate any initial population. Check constraints.")
        return population

    def crossover(self, p1, p2):
        """Perform crossover between two parent timetables with improved teacher conflict awareness"""
        if not p1 or not p2:  # Safety check
            return self._create_random_timetable()
            
        child = {}
        teacher_time_slot_usage = {teacher: set() for teacher in self.unique_teachers}
        
        # Group courses by (semester, section) for each parent
        p1_by_semester_section = {}
        p2_by_semester_section = {}
        for key, details in p1.items():
            semester = details['semester']
            section = details['class_section']
            sem_sec = (semester, section)
            if sem_sec not in p1_by_semester_section:
                p1_by_semester_section[sem_sec] = {}
            p1_by_semester_section[sem_sec][key] = details
        for key, details in p2.items():
            semester = details['semester']
            section = details['class_section']
            sem_sec = (semester, section)
            if sem_sec not in p2_by_semester_section:
                p2_by_semester_section[sem_sec] = {}
            p2_by_semester_section[sem_sec][key] = details

        for sem_sec in set(list(p1_by_semester_section.keys()) + list(p2_by_semester_section.keys())):
            # If section exists in only one parent, just copy it
            if sem_sec not in p1_by_semester_section:
                child.update(p2_by_semester_section[sem_sec])
                # Update teacher usage
                for key, details in p2_by_semester_section[sem_sec].items():
                    teacher_time_slot_usage[details['teacher']].add(details['time_slot'])
                continue
            if sem_sec not in p2_by_semester_section:
                child.update(p1_by_semester_section[sem_sec])
                # Update teacher usage
                for key, details in p1_by_semester_section[sem_sec].items():
                    teacher_time_slot_usage[details['teacher']].add(details['time_slot'])
                continue
                
            # Group by course within section
            p1_courses = {}
            p2_courses = {}
            
            for key, details in p1_by_semester_section[sem_sec].items():
                course = (details['course_name'], details['course_code'])
                if course not in p1_courses:
                    p1_courses[course] = []
                p1_courses[course].append((key, details))
                
            for key, details in p2_by_semester_section[sem_sec].items():
                course = (details['course_name'], details['course_code'])
                if course not in p2_courses:
                    p2_courses[course] = []
                p2_courses[course].append((key, details))
            
            # Choose between parent schedules for each course, preferring the one with fewer teacher conflicts
            for course in set(list(p1_courses.keys()) + list(p2_courses.keys())):
                # Check if both parents have this course
                if course in p1_courses and course in p2_courses:
                    # Evaluate potential conflicts in each parent's schedule for this course
                    p1_conflicts = 0
                    p2_conflicts = 0
                    
                    # Count conflicts for parent 1
                    for _, details in p1_courses[course]:
                        teacher = details['teacher']
                        time_slot = details['time_slot']
                        if time_slot in teacher_time_slot_usage[teacher]:
                            p1_conflicts += 1
                    
                    # Count conflicts for parent 2
                    for _, details in p2_courses[course]:
                        teacher = details['teacher']
                        time_slot = details['time_slot']
                        if time_slot in teacher_time_slot_usage[teacher]:
                            p2_conflicts += 1
                    
                    # Choose parent with fewer conflicts (or randomly if equal)
                    if p1_conflicts < p2_conflicts:
                        chosen_parent = p1_courses[course]
                    elif p2_conflicts < p1_conflicts:
                        chosen_parent = p2_courses[course]
                    else:
                        # Equal conflicts, choose randomly
                        chosen_parent = p1_courses[course] if random.random() < 0.5 else p2_courses[course]
                
                elif course in p1_courses:
                    chosen_parent = p1_courses[course]
                else:
                    chosen_parent = p2_courses[course]
                
                # Add chosen course schedule to child
                for key, details in chosen_parent:
                    # Create a new key with the same structure
                    new_key = key
                    child[new_key] = dict(details)  # Copy to avoid reference issues
                    # Update teacher usage
                    teacher_time_slot_usage[details['teacher']].add(details['time_slot'])
        
        return child

    def mutate(self, timetable):
        if not isinstance(timetable, dict):
            print("Warning: Mutation received invalid timetable.")
            return {}
            
        # Create a copy of the timetable to avoid modifying the original
        mutated_timetable = {}
        for key, value in timetable.items():
            mutated_timetable[key] = value.copy()
        
        # Track teacher assignments and conflicts to prioritize mutation targets
        teacher_time_slots = {}
        teacher_conflicts = {}
        
        # Identify teacher assignments and conflicts
        for key, details in mutated_timetable.items():
            teacher = details['teacher']
            time_slot = details['time_slot']
            
            if teacher not in teacher_time_slots:
                teacher_time_slots[teacher] = {}
                teacher_conflicts[teacher] = []
            
            if time_slot in teacher_time_slots[teacher]:
                # This is a conflict - add both this and the other course to conflicts list
                conflict_key = teacher_time_slots[teacher][time_slot]
                teacher_conflicts[teacher].append((key, conflict_key))
            else:
                teacher_time_slots[teacher][time_slot] = key
        
        # If there are teacher conflicts, prioritize mutating those
        conflict_mutations = 0
        for teacher, conflicts in teacher_conflicts.items():
            if conflicts and random.random() < 0.8:  # High chance to fix conflicts
                # Pick a random conflict to fix
                course_key, conflict_key = random.choice(conflicts)
                
                # Decide which course to move (randomly)
                key_to_mutate = course_key if random.random() < 0.5 else conflict_key
                details = mutated_timetable[key_to_mutate]
                
                # Find alternative time slots where this teacher is not scheduled
                current_time_slot = details['time_slot']
                available_slots = []
                
                for time_slot in self.unique_time_slots:
                    if time_slot != current_time_slot and time_slot not in teacher_time_slots[teacher]:
                        available_slots.append(time_slot)
                
                if available_slots:
                    # Move this course to a new time slot
                    new_time_slot = random.choice(available_slots)
                    mutated_timetable[key_to_mutate]['time_slot'] = new_time_slot
                    conflict_mutations += 1
        
        # Group by (semester, course-section) for regular mutations
        blocks = {}
        for key in mutated_timetable:
            # key can be (semester, course, section, idx, code)
            if len(key) == 5:
                semester, course, section, idx, code = key
            else:
                # fallback for legacy keys
                semester, course, section, idx, code = None, key[0], key[1], key[2], key[3] if len(key) > 3 else None
            blocks.setdefault((semester, course, section, code), []).append(key)
        
        # Mutate whole blocks (courses) with standard probability
        for cs, keys in blocks.items():
            semester, course, section, code = cs
            required = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
            if random.random() < self.MUTATION_RATE:
                # For this course-section, we'll try new time slots
                # First, find all possible time slots
                possible_slots = list(self.unique_time_slots)
                random.shuffle(possible_slots)
                
                # Get current slots for comparison
                current_slots = [mutated_timetable[key]['time_slot'] for key in keys]
                
                # Try to find a better assignment - prioritize same time different days
                if len(set(slot.split(' ', 1)[1] for slot in current_slots)) == 1:
                    # Currently all using same time, try to preserve this good property
                    current_time = current_slots[0].split(' ', 1)[1]
                    # Find all slots at this time
                    same_time_slots = [s for s in possible_slots if s.split(' ', 1)[1] == current_time]
                    
                    if len(same_time_slots) >= required:
                        # Enough slots at same time, randomly assign
                        random.shuffle(same_time_slots)
                        for i, key in enumerate(keys):
                            if i < required:
                                mutated_timetable[key]['time_slot'] = same_time_slots[i]
                else:
                    # Try to get same time slots
                    for time in set(slot.split(' ', 1)[1] for slot in possible_slots):
                        same_time_slots = [s for s in possible_slots if s.split(' ', 1)[1] == time]
                        if len(same_time_slots) >= required:
                            random.shuffle(same_time_slots)
                            for i, key in enumerate(keys):
                                if i < required:
                                    mutated_timetable[key]['time_slot'] = same_time_slots[i]
                            break
        
        # Occasional room mutation
        for key, details in mutated_timetable.items():
            if random.random() < self.MUTATION_RATE * 0.2:  # Lower chance for room mutation
                details['room'] = random.choice(self.unique_rooms)
        
        return mutated_timetable

    def select_parents(self, population, fitness_scores):
        """Tournament selection with better fitness (lower score) prioritized"""
        tournament_size = max(3, self.POPULATION_SIZE // 10)
        
        # First tournament
        tournament_indices = random.sample(range(len(population)), tournament_size)
        parent1_idx = min(tournament_indices, key=lambda i: fitness_scores[i])
        
        # Second tournament
        tournament_indices = random.sample(range(len(population)), tournament_size)
        parent2_idx = min(tournament_indices, key=lambda i: fitness_scores[i])
        
        return population[parent1_idx], population[parent2_idx]

    def evolve(self):
        # Initialize population
        print("Generating initial population...")
        start_time = datetime.now()
        population = self.generate_initial_population()
        
        # Find the best initial timetable
        fitness_scores = [self.calculate_fitness(tt) for tt in population]
        best_idx = fitness_scores.index(min(fitness_scores))
        best_timetable = population[best_idx]
        best_fitness = fitness_scores[best_idx]
        
        print(f"Initial population generated in {datetime.now() - start_time}")
        print(f"Initial best fitness: {best_fitness}")
        self.best_fitness_history.append(best_fitness)
        
        no_improvement_count = 0
        generation = 0
        
        while generation < self.MAX_GENERATIONS and no_improvement_count < 30:
            generation += 1
            
            # Create new population
            new_population = []
            
            # Elitism: Keep the best individual
            new_population.append(best_timetable)
            
            while len(new_population) < self.POPULATION_SIZE:
                # Select parents
                parent1, parent2 = self.select_parents(population, fitness_scores)
                
                # Crossover
                child = self.crossover(parent1, parent2)
                
                # Mutation
                if random.random() < self.MUTATION_RATE:
                    child = self.mutate(child)
                
                new_population.append(child)
            
            # Update population
            population = new_population
            
            # Calculate fitness scores
            fitness_scores = [self.calculate_fitness(tt) for tt in population]
            current_best_idx = fitness_scores.index(min(fitness_scores))
            current_best_fitness = fitness_scores[current_best_idx]
            
            # Update best timetable if better
            if current_best_fitness < best_fitness:
                best_fitness = current_best_fitness
                best_timetable = population[current_best_idx]
                no_improvement_count = 0
                print(f"Generation {generation}: Improved fitness to {best_fitness}")
            else:
                no_improvement_count += 1
            
            self.best_fitness_history.append(best_fitness)
            
            # Print progress every 10 generations
            if generation % 10 == 0:
                print(f"Generation {generation}: Best fitness = {best_fitness}")
                
                # Debug stats: teacher conflicts
                self._check_teacher_conflicts(best_timetable)
        
        print(f"Evolution completed after {generation} generations")
        print(f"Final best fitness: {best_fitness}")
        
        # Final verification of the best timetable
        self._verify_timetable_slots(best_timetable)
        
        # Final check for teacher conflicts
        conflict_count = self._check_teacher_conflicts(best_timetable)
        if conflict_count > 0:
            print(f"WARNING: Best solution still has {conflict_count} teacher conflicts")
            
        return best_timetable, best_fitness

    def _check_teacher_conflicts(self, timetable):
        """Check and report teacher conflicts in the timetable"""
        teacher_timeslots = {}
        conflicts = 0
        
        for key, details in timetable.items():
            teacher = details['teacher']
            time_slot = details['time_slot']
            
            if teacher not in teacher_timeslots:
                teacher_timeslots[teacher] = {}
                
            if time_slot in teacher_timeslots[teacher]:
                conflicts += 1
                existing = teacher_timeslots[teacher][time_slot]
                print(f"Teacher conflict: {teacher} at {time_slot}")
                print(f"  - {existing['course_name']} ({existing['class_section']}) vs {details['course_name']} ({details['class_section']})")
            else:
                teacher_timeslots[teacher][time_slot] = details
        
        return conflicts

    def convert_to_schedule_format(self, timetable):
        """Convert the genetic algorithm timetable to a format suitable for the UI"""
        schedule = []
        
        # Sort keys to ensure consistent order
        sorted_keys = sorted(timetable.keys())
        
        for key in sorted_keys:
            details = timetable[key]
            
            # Create a schedule entry
            entry = {
                'course_name': details['course_name'],
                'course_code': details['course_code'],
                'course_indicators': details.get('course_indicators', ''),
                'time_slot': details['time_slot'],
                'room': details['room'],
                'teacher': details['teacher'],
                'semester': details['semester'],
                'class_section': details['class_section']
            }
            
            schedule.append(entry)
        
        return schedule

    def plot_fitness_history(self):
        """Plot the evolution of fitness over generations"""
        try:
            import matplotlib.pyplot as plt
            
            generations = list(range(len(self.best_fitness_history)))
            plt.figure(figsize=(10, 6))
            plt.plot(generations, self.best_fitness_history, 'b-')
            plt.title('Fitness Evolution')
            plt.xlabel('Generation')
            plt.ylabel('Best Fitness Score (lower is better)')
            plt.grid(True)
            
            # Save plot
            plt.savefig('fitness_evolution.png')
            plt.close()
            
            print("Fitness evolution plot saved as 'fitness_evolution.png'")
        except ImportError:
            print("Matplotlib not available - skipping fitness plot")

def run_genetic_algorithm(entries, time_slots, lectures_per_course, course_exceptions=None):
    """Run the genetic algorithm and return the best timetable"""
    try:
        # Initialize the genetic algorithm
        ga = TimetableGeneticAlgorithm(
            entries=entries,
            time_slots_input=time_slots,
            lectures_per_course=lectures_per_course,
            course_exceptions=course_exceptions,
            population_size=100,
            max_generations=150,
            mutation_rate=0.20
        )
        
        # Run the evolution process
        best_timetable, best_fitness = ga.evolve()
        
        # Generate fitness plot
        ga.plot_fitness_history()
        
        # Convert to schedule format
        schedule = ga.convert_to_schedule_format(best_timetable)
        
        return schedule, best_fitness
    except Exception as e:
        messagebox.showerror("Genetic Algorithm Error", f"An error occurred while generating the timetable: {str(e)}")
        print(f"Error in genetic algorithm: {str(e)}")
        return [], float('inf')