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

    def _create_random_timetable(self):
        # Block scheduling: each course's lectures occur on consecutive days at same time
        if self.LECTURES_PER_COURSE > len(self.ordered_days):
            print(f"Warning: Not enough days to schedule all {self.LECTURES_PER_COURSE} lectures consecutively.")
            return None

        timetable = {}
        for entry in self.entries:
            course = entry['course_name']
            section = entry['class_section']
            num_days = self.LECTURES_PER_COURSE
            max_attempts = len(self.ordered_days) * 2
            block_days = None
            time_range = None

            for _ in range(max_attempts):
                start_idx = random.randint(0, len(self.ordered_days) - num_days)
                candidate = self.ordered_days[start_idx:start_idx + num_days]
                # find common time slots across days
                common = set(ts.split(" ",1)[1] for ts in self.time_slots_by_day[candidate[0]])
                for d in candidate[1:]:
                    common &= set(ts.split(" ",1)[1] for ts in self.time_slots_by_day[d])
                if common:
                    block_days = candidate
                    time_range = random.choice(list(common))
                    break

            if not block_days:
                print(f"Warning: Could not assign block for {course} ({section}).")
                return None

            # assign lectures
            for idx, day in enumerate(block_days):
                lecture_key = (course, section, idx)
                slot = f"{day} {time_range}"
                timetable[lecture_key] = {
                    'course_name': course,
                    'course_code': entry['course_code'],
                    'course_indicators': entry.get('course_indicators',''),
                    'time_slot': slot,
                    'room': entry['room'],
                    'teacher': entry['teacher'],
                    'semester': entry['semester'],
                    'class_section': section
                }
        return timetable

    def calculate_fitness(self, timetable):
        score = 0
        room_usage = {}
        teacher_usage = {}
        class_usage = {}
        course_count = {}
        day_course = {}
        teacher_load = {}
        section_load = {}

        if timetable is None:
            return float('inf')

        # Basic conflict checks
        for key, det in timetable.items():
            course = det['course_name']
            section = det['class_section']
            ts = det['time_slot']
            room = det['room']
            teacher = det['teacher']
            parts = ts.split(' ',1)
            if len(parts) < 2:
                score += 1000
                continue
            day, tr = parts[0], parts[1]

            # room conflict
            ru = f"{ts}_{room}"
            if ru in room_usage:
                score += 100
            room_usage[ru] = (course, section)
            # teacher conflict
            tu = f"{teacher}_{ts}"
            if tu in teacher_usage:
                score += 100
            teacher_usage[tu] = (course, section)
            # class conflict
            cu = f"{section}_{ts}"
            if cu in class_usage:
                score += 150
            class_usage[cu] = (course, section)
            # count
            key_cs = (course, section)
            course_count[key_cs] = course_count.get(key_cs, 0) + 1
            # per-day course
            dc = (day, course, section)
            day_course[dc] = day_course.get(dc, 0) + 1
            if day_course[dc] > 1:
                score += 200
            # teacher load
            tl = (teacher, day)
            teacher_load[tl] = teacher_load.get(tl, 0) + 1
            if teacher_load[tl] > 4:
                score += 15 * (teacher_load[tl] - 4)
            # section load
            sl = (section, day)
            section_load[sl] = section_load.get(sl, 0) + 1
            if section_load[sl] > 5:
                score += 10 * (section_load[sl] - 5)

        # missing lectures penalty
        for e in self.entries:
            key_cs = (e['course_name'], e['class_section'])
            actual = course_count.get(key_cs, 0)
            if actual != self.LECTURES_PER_COURSE:
                score += 50 * abs(actual - self.LECTURES_PER_COURSE)

        # enforce block structure
        day_idx = {d:i for i,d in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])}
        course_days = {}
        course_times = {}
        for key, det in timetable.items():
            course, section, _ = key
            ts = det['time_slot']
            parts = ts.split(' ',1)
            if len(parts) < 2: continue
            d, tr = parts[0], parts[1]
            idx = day_idx.get(d)
            if idx is None: continue
            cs_key = (course, section)
            course_days.setdefault(cs_key, []).append(idx)
            course_times.setdefault(cs_key, set()).add(tr)

        for cs_key, days in course_days.items():
            days.sort()
            # non-consecutive
            for i in range(len(days)-1):
                if days[i+1] != days[i] + 1:
                    score += 100
                    break
            # multi-time
            if len(course_times.get(cs_key, [])) > 1:
                score += 100

        return score

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
            course, section, idx = key
            blocks.setdefault((course, section), []).append(key)
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