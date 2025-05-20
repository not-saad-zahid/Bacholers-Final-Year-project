"""
Genetic algorithm for generating class timetables with improved distribution of lectures.
"""
import random
from datetime import datetime, timedelta
from tkinter import messagebox
# from db.timetable_db import load_timetable # Not directly used by GA class itself after entries are passed
from utils.timeslots import generate_time_slots # May not be needed if UI provides slots

class TimetableGeneticAlgorithm:
    def __init__(self,
                 *, # Make all subsequent arguments keyword-only
                 entries,                # List of dictionaries with course details
                 time_slots_input,       # List of pre-generated time slot strings from UI
                 lectures_per_course,
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

        # Room capacities (example, can be made dynamic if needed)
        # This is not used in the current fitness function but kept for potential future use.
        self.room_capacities = {
            "71": 40, "72": 35, "73": 30,
            "74": 45, "77": 50, "80": 40,
            # Add other rooms as string keys if they are numbers
            # Or ensure room names in entries match these keys.
        }
        # Convert room names from entries to string if they are numbers, to match capacities dict
        for entry in self.entries:
            entry['room'] = str(entry['room'])

        # Extract unique values from entries (can be useful for some constraints or logging)
        self.unique_rooms = list(set(str(e['room']) for e in self.entries)) # Ensure rooms are strings
        self.unique_teachers = list(set(e['teacher'] for e in self.entries))
        self.unique_courses_full_info = list(set((e['course_name'], e['course_code']) for e in self.entries))
        self.unique_sections = list(set(e['class_section'] for e in self.entries))
        
        # Group time slots by day for distribution checks
        self.time_slots_by_day = {}
        for ts in self.unique_time_slots:
            try:
                day = ts.split()[0] # Assumes format "Day HH:MM PM-HH:MM PM"
                if day not in self.time_slots_by_day:
                    self.time_slots_by_day[day] = []
                self.time_slots_by_day[day].append(ts)
            except IndexError:
                print(f"Warning: Could not parse day from time slot: {ts}")
        
        self.best_fitness_history = []
        print(f"GA initialized with {len(self.entries)} entry types, {len(self.unique_time_slots)} unique time slots.")
        print(f"Lectures per course: {self.LECTURES_PER_COURSE}")


    # _generate_time_slots is no longer needed as time_slots_input is provided by UI
    # def _generate_time_slots(self): ...

    def generate_initial_population(self):
        population = []
        for i in range(self.POPULATION_SIZE):
            timetable = self._create_random_timetable()
            if timetable is None: # Could happen if constraints are too tight from start
                print(f"Warning: Failed to create a valid random timetable for individual {i+1}. Retrying or check constraints.")
                # Potentially return fewer than POPULATION_SIZE or handle error
                continue
            population.append(timetable)
        if not population:
            raise ValueError("Failed to generate any initial population. Check data and constraints (especially LECTURES_PER_COURSE vs available slots).")
        return population

    def _create_random_timetable(self):
        timetable = {}
        
        # Track used (day, course_name, class_section) to enforce 1 lecture per day
        lectures_on_day_for_course_section = {}

        for entry in self.entries:
            course_n = entry['course_name']
            class_sec = entry['class_section']
            
            # Create LECTURES_PER_COURSE instances for this specific course offering
            for i in range(self.LECTURES_PER_COURSE):
                lecture_key = (course_n, class_sec, i)
                
                assigned_slot = False
                attempts = 0
                max_attempts = len(self.unique_time_slots) * 2

                while not assigned_slot and attempts < max_attempts:
                    attempts += 1
                    chosen_slot = random.choice(self.unique_time_slots)
                    day_of_chosen_slot = chosen_slot.split()[0]

                    day_course_key = (day_of_chosen_slot, course_n, class_sec)
                    current_lectures_on_day = lectures_on_day_for_course_section.get(day_course_key, 0)

                    if current_lectures_on_day == 0:  # Changed condition to strictly enforce 1 lecture per day
                        timetable[lecture_key] = {
                            'course_name': course_n,
                            'course_code': entry['course_code'],
                            'course_indicators': entry.get('course_indicators', ''),
                            'time_slot': chosen_slot,
                            'room': str(entry['room']),
                            'teacher': entry['teacher'],
                            'semester': entry['semester'],
                            'class_section': class_sec
                        }
                        lectures_on_day_for_course_section[day_course_key] = 1  # Set to 1 (not incrementing)
                        assigned_slot = True
                
                if not assigned_slot:
                    print(f"Warning: Could not assign lecture {lecture_key} with 1-per-day constraint. May need more available days.")
                    # Fallback: assign to a random slot if we must
                    chosen_slot = random.choice(self.unique_time_slots)
                    timetable[lecture_key] = {
                        'course_name': course_n,
                        'course_code': entry['course_code'],
                        'course_indicators': entry.get('course_indicators', ''),
                        'time_slot': chosen_slot,
                        'room': str(entry['room']),
                        'teacher': entry['teacher'],
                        'semester': entry['semester'],
                        'class_section': class_sec
                    }
                    day_of_chosen_slot = chosen_slot.split()[0]
                    day_course_key = (day_of_chosen_slot, course_n, class_sec)
                    lectures_on_day_for_course_section[day_course_key] = 1
        
        return timetable

    def calculate_fitness(self, timetable):
        score = 0
        room_usage = {}
        teacher_usage = {}
        class_usage = {}

        course_lectures_count = {}
        course_on_day_count = {}
        teacher_daily_load = {}
        section_daily_load = {}

        if timetable is None:
            return float('inf')

        for lecture_key, details in timetable.items():
            course_n = details['course_name']
            class_sec = details['class_section']
            ts = details['time_slot']
            rm = str(details['room'])
            tch = details['teacher']
            
            try:
                day = ts.split()[0]
            except IndexError:
                score += 1000
                continue

            # Room conflict check
            room_key = f"{ts}_{rm}"
            if room_key in room_usage:
                score += 100
            room_usage[room_key] = (course_n, class_sec)

            # Teacher conflict check
            teacher_key = f"{tch}_{ts}"
            if teacher_key in teacher_usage:
                score += 100
            teacher_usage[teacher_key] = (course_n, class_sec)

            # Class/Section conflict check
            class_key = f"{class_sec}_{ts}"
            if class_key in class_usage:
                score += 150
            class_usage[class_key] = (course_n, class_sec)

            # Track lectures per course offering
            course_offering_key = (course_n, class_sec)
            course_lectures_count[course_offering_key] = course_lectures_count.get(course_offering_key, 0) + 1
            
            # Strictly enforce 1 lecture per day per course-section
            day_course_section_key = (day, course_n, class_sec)
            course_on_day_count[day_course_section_key] = course_on_day_count.get(day_course_section_key, 0) + 1
            if course_on_day_count[day_course_section_key] > 1:
                score += 200  # Heavy penalty for multiple lectures of same course in a day

            # Teacher daily load check
            teacher_day_key = (tch, day)
            teacher_daily_load[teacher_day_key] = teacher_daily_load.get(teacher_day_key, 0) + 1
            if teacher_daily_load[teacher_day_key] > 4:
                score += 15 * (teacher_daily_load[teacher_day_key] - 4)

            # Section daily load check
            section_day_key = (class_sec, day)
            section_daily_load[section_day_key] = section_daily_load.get(section_day_key, 0) + 1
            if section_daily_load[section_day_key] > 5:
                score += 10 * (section_daily_load[section_day_key] - 5)
        
        # Check for required number of lectures
        for entry in self.entries:
            course_offering_key_check = (entry['course_name'], entry['class_section'])
            actual_lectures = course_lectures_count.get(course_offering_key_check, 0)
            if actual_lectures != self.LECTURES_PER_COURSE:
                score += 50 * abs(actual_lectures - self.LECTURES_PER_COURSE)

        return score

    def crossover(self, parent1, parent2):
        child = {}
        # Ensure both parents are valid timetables (dicts)
        if not isinstance(parent1, dict) or not isinstance(parent2, dict):
            # This can happen if initial population had issues.
            # Return one of the parents or an empty dict, and fitness will be high.
            print("Warning: Crossover received invalid parent(s).")
            return parent1 if isinstance(parent1, dict) else (parent2 if isinstance(parent2, dict) else {})


        # Keys are (course_name, class_section, instance_num)
        # It's important that both parents have the same set of keys,
        # which should be true if they are generated from the same self.entries and LECTURES_PER_COURSE.
        
        # Check if keys match, if not, this is a problem with population generation or consistency.
        if set(parent1.keys()) != set(parent2.keys()):
            # This is a significant issue. For robustness, try to proceed or return a copy of a parent.
            # print(f"Warning: Parents in crossover have different key sets. Parent1: {len(parent1.keys())}, Parent2: {len(parent2.keys())}")
            # Fallback: choose one parent or try to merge. Simplest is to return parent1.
            # A better approach might be to ensure population consistency.
            # However, if _create_random_timetable can fail to schedule all lectures, keys *might* differ.
            # Let's assume for now that keys *should* be the same.
             # A safer merge:
            all_keys = list(set(parent1.keys()) | set(parent2.keys())) # Union of keys
            for k in all_keys:
                if random.random() < 0.5:
                    if k in parent1:
                        child[k] = parent1[k].copy()
                    elif k in parent2: # If p1 doesn't have it, take from p2
                        child[k] = parent2[k].copy()
                else:
                    if k in parent2:
                        child[k] = parent2[k].copy()
                    elif k in parent1: # If p2 doesn't have it, take from p1
                        child[k] = parent1[k].copy()
            # This child might still be problematic if it doesn't have all required lectures.
            return child


        keys = list(parent1.keys()) # Assuming keys are consistent
        for k in keys:
            if random.random() < 0.5:
                child[k] = parent1[k].copy() 
            else:
                child[k] = parent2[k].copy()
        return child

    def mutate(self, timetable):
        if not isinstance(timetable, dict): # Safety check
            print("Warning: Mutation received invalid timetable.")
            return {}

        for lecture_key_to_mutate in list(timetable.keys()): # (course_name, class_section, instance_num)
            if random.random() < self.MUTATION_RATE:
                original_details = timetable[lecture_key_to_mutate]
                original_slot = original_details['time_slot']

                # Try to find a new slot
                assigned_new_slot = False
                attempts = 0
                max_attempts = len(self.unique_time_slots) # Try each slot once on average

                while not assigned_new_slot and attempts < max_attempts:
                    attempts += 1
                    new_random_slot = random.choice(self.unique_time_slots)
                    if new_random_slot == original_slot: # Avoid mutating to the same slot if possible
                        if len(self.unique_time_slots) > 1: # Only if other slots exist
                            continue 
                    
                    timetable[lecture_key_to_mutate]['time_slot'] = new_random_slot
                    assigned_new_slot = True
                    break # Exit attempt loop
                
                # If still not assigned a new slot (e.g. all other slots violate constraints)
                # the original slot remains, or you could force a random change if strict mutation is desired
                # Current logic: if no better slot found, it stays as is.
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
                parent1 = min(tournament1, key=lambda x: x[1])[0] # Get timetable (index 0)
                
                tournament2 = random.sample(scored_population, tournament_size)
                parent2 = min(tournament2, key=lambda x: x[1])[0]

                if parent1 is None or parent2 is None: # Skip if parents are somehow invalid
                    # print("Warning: Skipping crossover/mutation due to invalid parent(s).")
                    continue 

                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)
                children_generated +=1
            
            population = new_population

        print(f"Max generations reached. Best fitness found: {best_fitness_overall}")
        return best_solution_overall