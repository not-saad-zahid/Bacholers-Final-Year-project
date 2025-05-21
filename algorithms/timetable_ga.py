"""
Genetic algorithm for generating class timetables with improved distribution of lectures.
"""
import random
from datetime import datetime, timedelta
from tkinter import messagebox

class TimetableGeneticAlgorithm:
    def __init__(self,
                 *,
                 entries,                # List of dictionaries with course details
                 time_slots_input,       # List of pre-generated time slot strings from UI
                 lectures_per_course,
                 course_exceptions=None, # Dictionary for exceptions in required lectures per course
                 population_size=100,
                 max_generations=100,
                 mutation_rate=0.15):

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

        # Convert room names to string
        for entry in self.entries:
            entry['room'] = str(entry['room'])

        # Extract unique sets
        self.unique_rooms = list(set(e['room'] for e in self.entries))
        self.unique_teachers = list(set(e['teacher'] for e in self.entries))
        self.unique_sections = list(set(e['class_section'] for e in self.entries))

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

        # Store required lectures for each course
        self.required_lectures = {}
        for entry in self.entries:
            code = entry['course_code']
            self.required_lectures[code] = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
        
        # Debug available vs required lectures
        self.debug_timetable_requirements()

    def debug_timetable_requirements(self):
        """Debug function to check lecture requirements vs available slots"""
        total_lectures = 0
        lectures_by_section = {}
        lectures_by_section_course = {}
        
        # Count required lectures by section and section-course
        for entry in self.entries:
            section = entry['class_section']
            code = entry['course_code']
            course = entry['course_name']
            required = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
            
            if section not in lectures_by_section:
                lectures_by_section[section] = 0
                lectures_by_section_course[section] = {}
            
            key = (course, code)
            if key not in lectures_by_section_course[section]:
                lectures_by_section[section] += required
                total_lectures += required
                lectures_by_section_course[section][key] = required
        
        # Count available slots
        total_slots = len(self.unique_time_slots)
        
        print(f"Total required lectures across all sections: {total_lectures}")
        print(f"Available unique time slots: {total_slots}")
        print("Lectures required by section:")
        for section, count in lectures_by_section.items():
            print(f"  Section {section}: {count} lectures")
            if count > total_slots:
                print(f"  WARNING: Section {section} requires {count} lectures but only {total_slots} slots available")
        
        # Check individual course requirements
        print("Detailed course requirements by section:")
        for section, courses in lectures_by_section_course.items():
            print(f"  Section {section}:")
            for (course, code), required in courses.items():
                print(f"    {course} ({code}): {required} lectures")

    def _create_random_timetable(self):
        """Create a random timetable with section-specific time slot assignments"""
        timetable = {}
        section_time_slot_usage = {section: set() for section in self.unique_sections}
        course_assignments = {}

        # Group entries by section for separate processing
        entries_by_section = {}
        for entry in self.entries:
            section = entry['class_section']
            if section not in entries_by_section:
                entries_by_section[section] = []
            entries_by_section[section].append(entry)

        # For each section, do course assignment separately
        for section, section_entries in entries_by_section.items():
            # Prepare a list of (course, section, code, required_lectures) and sort descending by required lectures
            course_info = []
            for entry in section_entries:
                course = entry['course_name']
                code = entry['course_code']
                required_lectures = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
                course_info.append((course, section, code, required_lectures, entry))
            
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
            for course, section, code, required_lectures, entry in course_info:
                assigned_slots = []
                key_prefix = (course, section, code)
                
                # First attempt: try to use consecutive days at the same time if possible
                if required_lectures <= len(self.ordered_days):  # Only try this for courses that could fit consecutive days
                    for time in all_times:
                        # Find consecutive days with available slots
                        consecutive_days = []
                        for day in self.ordered_days:
                            slot_key = f"{day} {time}"
                            if slot_key in self.unique_time_slots and slot_key not in section_time_slot_usage[section]:
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
                                section_time_slot_usage[section].add(slot_key)
                            break  # We've assigned all needed slots for this course
                
                # Second attempt: try to find the same time slot on any days
                if len(assigned_slots) < required_lectures:
                    for time in all_times:
                        available_days = []
                        for day in self.ordered_days:
                            slot_key = f"{day} {time}"
                            if slot_key in self.unique_time_slots and slot_key not in section_time_slot_usage[section]:
                                available_days.append(day)
                        
                        if len(available_days) >= required_lectures - len(assigned_slots):
                            needed = required_lectures - len(assigned_slots)
                            for i in range(needed):
                                day = available_days[i]
                                slot_key = f"{day} {time}"
                                assigned_slots.append((day, time))
                                section_time_slot_usage[section].add(slot_key)
                            break  # We've assigned all needed slots for this course
                
                # Final attempt: use any available slots (fallback method)
                if len(assigned_slots) < required_lectures:
                    for day, time in all_slots_shuffled:
                        slot_key = f"{day} {time}"
                        if slot_key not in section_time_slot_usage[section]:
                            assigned_slots.append((day, time))
                            section_time_slot_usage[section].add(slot_key)
                            if len(assigned_slots) == required_lectures:
                                break
                
                # Create timetable entries for this course
                for idx, (day, time) in enumerate(assigned_slots):
                    key = (course, section, idx, code)
                    timetable[key] = {
                        'course_name': course,
                        'course_code': code,
                        'course_indicators': entry.get('course_indicators', ''),
                        'time_slot': f"{day} {time}",
                        'room': entry['room'],
                        'teacher': entry['teacher'],
                        'semester': entry['semester'],
                        'class_section': section
                    }

        # Final check: verify we haven't assigned conflicting slots
        self._verify_timetable_slots(timetable)
        return timetable

    def _verify_timetable_slots(self, timetable):
        """Verify that the timetable doesn't have conflicting slot assignments"""
        section_timeslots = {}
        teacher_timeslots = {}
        
        for key, details in timetable.items():
            section = details['class_section']
            time_slot = details['time_slot']
            teacher = details['teacher']
            
            # Check section-timeslot conflicts
            if section not in section_timeslots:
                section_timeslots[section] = set()
            if time_slot in section_timeslots[section]:
                print(f"WARNING: Conflicting timeslot {time_slot} for section {section}")
            section_timeslots[section].add(time_slot)
            
            # Check teacher-timeslot conflicts
            if teacher not in teacher_timeslots:
                teacher_timeslots[teacher] = set()
            if time_slot in teacher_timeslots[teacher]:
                print(f"WARNING: Conflicting timeslot {time_slot} for teacher {teacher}")
            teacher_timeslots[teacher].add(time_slot)

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

        for key, details in timetable.items():
            course = details['course_name']
            code = details['course_code']
            section = details['class_section']
            time_slot = details['time_slot']
            room = details['room']
            teacher = details['teacher']
            
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

            # Teacher conflicts
            teacher_key = f"{time_slot}_{teacher}"
            if teacher_key in teacher_usage:
                score += 5000
            teacher_usage[teacher_key] = course_key

            # Class conflicts
            class_key = f"{time_slot}_{section}"
            if class_key in class_usage:
                score += 5000
            class_usage[class_key] = course_key

            # Daily load tracking
            teacher_day_key = f"{teacher}_{day}"
            teacher_daily_load[teacher_day_key] = teacher_daily_load.get(teacher_day_key, 0) + 1
            if teacher_daily_load[teacher_day_key] > 4:
                score += 50 * (teacher_daily_load[teacher_day_key] - 4)

            section_day_key = f"{section}_{day}"
            section_daily_load[section_day_key] = section_daily_load.get(section_day_key, 0) + 1
            if section_daily_load[section_day_key] > 5:
                score += 50 * (section_daily_load[section_day_key] - 5)

        # Create a mapping of required lectures that accounts for section-specific courses
        required_lectures = {}
        for entry in self.entries:
            course_key = (entry['course_name'], entry['class_section'], entry['course_code'])
            required = self.course_exceptions.get(entry['course_code'], self.LECTURES_PER_COURSE)
            required_lectures[course_key] = required

        # Check lecture count requirements
        for course_key, required in required_lectures.items():
            actual = course_lecture_counts.get(course_key, 0)
            
            if actual != required:
                # Heavy penalty for wrong lecture count - but make it proportional to the difference
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
                               if (details['course_name'], details['class_section'], details['course_code']) == course_key]
                
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
        """Perform crossover between two parent timetables"""
        if not p1 or not p2:  # Safety check
            return self._create_random_timetable()
            
        child = {}
        
        # Group courses by section for each parent
        p1_by_section = {}
        p2_by_section = {}
        
        for key, details in p1.items():
            section = details['class_section']
            if section not in p1_by_section:
                p1_by_section[section] = {}
            p1_by_section[section][key] = details
            
        for key, details in p2.items():
            section = details['class_section']
            if section not in p2_by_section:
                p2_by_section[section] = {}
            p2_by_section[section][key] = details
        
        # For each section, perform crossover between parent sections
        for section in set(list(p1_by_section.keys()) + list(p2_by_section.keys())):
            # If section exists in only one parent, just copy it
            if section not in p1_by_section:
                child.update(p2_by_section[section])
                continue
            if section not in p2_by_section:
                child.update(p1_by_section[section])
                continue
                
            # Group by course within section
            p1_courses = {}
            p2_courses = {}
            
            for key, details in p1_by_section[section].items():
                course = (details['course_name'], details['course_code'])
                if course not in p1_courses:
                    p1_courses[course] = []
                p1_courses[course].append((key, details))
                
            for key, details in p2_by_section[section].items():
                course = (details['course_name'], details['course_code'])
                if course not in p2_courses:
                    p2_courses[course] = []
                p2_courses[course].append((key, details))
            
            # Choose randomly between parent schedules for each course
            for course in set(list(p1_courses.keys()) + list(p2_courses.keys())):
                if random.random() < 0.5 and course in p1_courses:
                    for key, details in p1_courses[course]:
                        # Create a new key with the same structure
                        new_key = key
                        child[new_key] = dict(details)  # Copy to avoid reference issues
                else:
                    if course in p2_courses:
                        for key, details in p2_courses[course]:
                            new_key = key
                            child[new_key] = dict(details)  # Copy to avoid reference issues
        
        return child

    def mutate(self, timetable):
        if not isinstance(timetable, dict):
            print("Warning: Mutation received invalid timetable.")
            return {}
        # Group by course-section
        blocks = {}
        for key in timetable:
            # key can be (course, section, idx, code)
            course, section, idx = key[0], key[1], key[2]
            code = key[3] if len(key) > 3 else None
            blocks.setdefault((course, section, code), []).append(key)
        
        # mutate whole blocks
        for cs, keys in blocks.items():
            course, section, code = cs
            required = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
            
            if len(keys) != required:
                continue
                
            if random.random() < self.MUTATION_RATE:
                # Determine mutation type
                mutation_type = random.choice(['time_slot', 'move_block', 'shuffle'])
                
                if mutation_type == 'time_slot':
                    # Change time slot but keep same days
                    current_time_slots = [timetable[key]['time_slot'] for key in keys]
                    current_days = [ts.split(' ', 1)[0] for ts in current_time_slots]
                    
                    # Get all available time parts
                    all_times = sorted({ts.split(' ', 1)[1] for ts in self.unique_time_slots})
                    
                    # Try to find a new time that works for all days
                    for new_time in random.sample(all_times, len(all_times)):
                        valid = True
                        for day in current_days:
                            new_slot = f"{day} {new_time}"
                            if new_slot not in self.unique_time_slots:
                                valid = False
                                break
                        
                        if valid:
                            # Apply new time slot
                            for i, key in enumerate(sorted(keys, key=lambda x: x[2])):
                                timetable[key]['time_slot'] = f"{current_days[i]} {new_time}"
                            break
                
                elif mutation_type == 'move_block':
                    # Try to find a new block of consecutive days
                    num_days = required
                    if num_days > len(self.ordered_days):
                        continue
                        
                    # Get common time slots across all days
                    all_times = sorted({ts.split(' ', 1)[1] for ts in self.unique_time_slots})
                    
                    # Try finding consecutive days with the same time slot
                    attempts = 10  # Limit attempts to avoid infinite loops
                    for _ in range(attempts):
                        # Pick a random starting day and time
                        if len(self.ordered_days) <= num_days:
                            # Not enough days for a random start
                            start_idx = 0
                        else:
                            start_idx = random.randint(0, len(self.ordered_days) - num_days)
                            
                        candidate_days = self.ordered_days[start_idx:start_idx+num_days]
                        
                        # Pick a random time slot
                        for new_time in random.sample(all_times, len(all_times)):
                            valid = True
                            for day in candidate_days:
                                new_slot = f"{day} {new_time}"
                                if new_slot not in self.unique_time_slots:
                                    valid = False
                                    break
                            
                            if valid:
                                # Apply new time slots
                                for i, key in enumerate(sorted(keys, key=lambda x: x[2])):
                                    timetable[key]['time_slot'] = f"{candidate_days[i]} {new_time}"
                                break
                        
                        if valid:  # If we found a valid assignment
                            break
                
                elif mutation_type == 'shuffle':
                    # Shuffle the days while keeping the same time
                    current_time_slots = [timetable[key]['time_slot'] for key in keys]
                    current_time = current_time_slots[0].split(' ', 1)[1]  # Assume all have same time
                    
                    # Get all days where this time slot is available
                    valid_days = []
                    for day in self.ordered_days:
                        slot = f"{day} {current_time}"
                        if slot in self.unique_time_slots:
                            valid_days.append(day)
                    
                    if len(valid_days) >= required:
                        # Pick a random subset of days
                        selected_days = random.sample(valid_days, required)
                        
                        # Apply new days
                        for i, key in enumerate(sorted(keys, key=lambda x: x[2])):
                            if i < len(selected_days):  # Safety check
                                timetable[key]['time_slot'] = f"{selected_days[i]} {current_time}"
        
        return timetable

    def generate_optimized_timetable(self):
        if not self.entries or not self.unique_time_slots:
            messagebox.showerror("GA Error", "Cannot generate timetable without entries or time slots.")
            return None

        try:
            population = self.generate_initial_population()
        except ValueError as e:
            messagebox.showerror("GA Initialization Error", str(e))
            return None
            
        if not population: # Double check if generate_initial_population returned empty
             messagebox.showerror("GA Error", "Initial population is empty. Cannot proceed.")
             return None

        best_fitness_overall = float('inf')
        best_solution_overall = None
        no_improvement_streak = 0
        CONVERGENCE_STREAK = 25 # Generations with no improvement to consider convergence

        for generation in range(self.MAX_GENERATIONS):
            scored_population = []
            for timetable_individual in population:
                if timetable_individual is None or not isinstance(timetable_individual, dict): # Paranoia
                    # This individual is invalid, assign worst fitness or skip
                    # print(f"Warning: Invalid individual found in population generation {generation}")
                    scored_population.append((timetable_individual, float('inf')))
                    continue
                scored_population.append((timetable_individual, self.calculate_fitness(timetable_individual)))
            
            scored_population.sort(key=lambda x: x[1]) # Sort by fitness (lower is better)
            
            current_generation_best_timetable, current_generation_best_fitness = scored_population[0]
            self.best_fitness_history.append(current_generation_best_fitness) # Track fitness history

            if current_generation_best_fitness < best_fitness_overall:
                best_fitness_overall = current_generation_best_fitness
                best_solution_overall = current_generation_best_timetable
                no_improvement_streak = 0
                print(f"Generation {generation+1}: New best fitness = {best_fitness_overall}")
            else:
                no_improvement_streak += 1
                # print(f"Generation {generation+1}: Fitness = {current_generation_best_fitness} (No improvement streak: {no_improvement_streak})")

            if best_fitness_overall == 0:
                print(f"Perfect solution found at generation {generation+1}!")
                return best_solution_overall # Ideal solution found
            
            if no_improvement_streak >= CONVERGENCE_STREAK:
                print(f"Converged after {CONVERGENCE_STREAK} generations with no improvement. Best fitness: {best_fitness_overall}")
                return best_solution_overall # Early stopping due to convergence

            # Elitism: Carry over the top N individuals to the next generation
            elite_count = max(1, self.POPULATION_SIZE // 10) # At least 1, e.g., top 10%
            elites = [timetable for timetable, fitness in scored_population[:elite_count]]

            # Selection, Crossover, Mutation to create the new population
            new_population = elites[:] # Start new population with elites

            # Fill the rest of the population
            num_to_generate = self.POPULATION_SIZE - elite_count
            
            # Tournament selection for parents
            tournament_size = 3 # Typical value for tournament selection
            
            children_generated = 0
            while children_generated < num_to_generate:
                # Select parents using tournament selection
                tournament1 = random.sample(scored_population, tournament_size)
                tournament2 = random.sample(scored_population, tournament_size)
                
                # Select best from each tournament
                parent1 = min(tournament1, key=lambda x: x[1])[0]
                parent2 = min(tournament2, key=lambda x: x[1])[0]
                
                # Crossover
                child = self.crossover(parent1, parent2)
                
                # Mutation
                if random.random() < self.MUTATION_RATE:
                    child = self.mutate(child)
                
                # Add child to new population
                new_population.append(child)
                children_generated += 1
            
            # Replace old population
            population = new_population
        
        print(f"Completed {self.MAX_GENERATIONS} generations. Best fitness: {best_fitness_overall}")
        return best_solution_overall
    
    def get_formatted_timetable(self, timetable):
        """
        Return the timetable as a structured format for display
        """
        if not timetable:
            return []
            
        formatted_entries = []
        for key, details in timetable.items():
            formatted_entries.append({
                'course_name': details['course_name'],
                'course_code': details['course_code'],
                'course_indicators': details.get('course_indicators', ''),
                'time_slot': details['time_slot'],
                'room': details['room'],
                'teacher': details['teacher'],
                'semester': details['semester'],
                'class_section': details['class_section']
            })
            
        return formatted_entries
    
    def get_fitness_history(self):
        """
        Return the history of best fitness values for plotting
        """
        return self.best_fitness_history