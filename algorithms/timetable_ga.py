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

        # Check lecture count requirements
        for entry in self.entries:
            course_key = (entry['course_name'], entry['class_section'], entry['course_code'])
            required = self.course_exceptions.get(entry['course_code'], self.LECTURES_PER_COURSE)
            actual = course_lecture_counts.get(course_key, 0)
            
            if actual != required:
                score += 5000  # Heavy penalty for wrong lecture count

        # Check same time slot requirement
        for course_key, times in course_time_slots.items():
            if len(times) > 1:
                score += 5000  # Heavy penalty for different time slots

        return score

    def _create_random_timetable(self):
        """Assign earliest time slots to courses with highest lectures-per-course."""
        timetable = {}
        time_slot_usage = set()  # Track used time slots (day + time)
        course_assignments = {}

        # Prepare a list of (course, section, code, required_lectures) and sort descending
        course_info = []
        for entry in self.entries:
            course = entry['course_name']
            section = entry['class_section']
            code = entry['course_code']
            required_lectures = self.course_exceptions.get(code, self.LECTURES_PER_COURSE)
            course_info.append((course, section, code, required_lectures, entry))
        # Sort by required_lectures descending
        course_info.sort(key=lambda x: -x[3])

        # Prepare ordered list of all (day, time) slots
        days = self.ordered_days
        # Get all unique times (sorted)
        all_times = sorted({ts.split(' ', 1)[1] for ts in self.unique_time_slots})
        all_slots = []
        for time in all_times:
            for day in days:
                if f"{day} {time}" in self.unique_time_slots:
                    all_slots.append((day, time))

        slot_index = 0  # Index in all_slots

        for course, section, code, required_lectures, entry in course_info:
            assigned_slots = []
            # Try to assign required_lectures slots, preferring earliest available
            for _ in range(required_lectures):
                while slot_index < len(all_slots):
                    day, time = all_slots[slot_index]
                    slot_key = f"{day} {time}"
                    slot_index += 1
                    if slot_key not in time_slot_usage:
                        assigned_slots.append((day, time))
                        time_slot_usage.add(slot_key)
                        break
            # If not enough slots found, fallback: assign any available slot
            if len(assigned_slots) < required_lectures:
                for day in days:
                    for time in all_times:
                        slot_key = f"{day} {time}"
                        if slot_key not in time_slot_usage:
                            assigned_slots.append((day, time))
                            time_slot_usage.add(slot_key)
                            if len(assigned_slots) == required_lectures:
                                break
                    if len(assigned_slots) == required_lectures:
                        break

            # Create timetable entries
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

        return timetable

    def crossover(self, p1, p2):
        # unchanged
        ...

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
            if len(keys) != self.LECTURES_PER_COURSE:
                continue
            if random.random() < self.MUTATION_RATE:
                # pick new block
                num_days = self.LECTURES_PER_COURSE
                if num_days > len(self.ordered_days):
                    continue
                attempts = len(self.ordered_days) * 2
                new_days = None
                new_tr = None
                for _ in range(attempts):
                    start = random.randint(0, len(self.ordered_days) - num_days)
                    cand = self.ordered_days[start:start+num_days]
                    common = set(ts.split(' ',1)[1] for ts in self.time_slots_by_day[cand[0]])
                    for d in cand[1:]:
                        common &= set(ts.split(' ',1)[1] for ts in self.time_slots_by_day[d])
                    if common:
                        new_days = cand
                        new_tr = random.choice(list(common))
                        break
                if not new_days:
                    continue
                # apply
                for i, key in enumerate(sorted(keys, key=lambda x: x[2])):
                    timetable[key]['time_slot'] = f"{new_days[i]} {new_tr}"
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