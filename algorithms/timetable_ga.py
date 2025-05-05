"""
Genetic algorithm for generating class timetables with improved distribution of lectures.
"""
import random
from datetime import datetime, timedelta
from db.timetable_db import load_timetable

"""
Genetic algorithm for generating class timetables with improved distribution of lectures.
"""
import random
from datetime import datetime, timedelta
from db.timetable_db import load_timetable

class TimetableGeneticAlgorithm:
    def __init__(self, semester, shift, lectures_per_course, max_lectures_per_day, lecture_duration, start_time, end_time, population_size=100, max_generations=100, mutation_rate=0.15):
        """
        semester: Semester for which the timetable is being generated
        shift: Shift (e.g., Morning or Evening) for which the timetable is being generated
        lectures_per_course: Number of lectures per course per week
        max_lectures_per_day: Maximum lectures of the same course per day
        lecture_duration: Duration of each lecture in minutes
        start_time: Daily start time for lectures
        end_time: Daily end time for lectures
        population_size: Number of candidate timetables per generation
        max_generations: Number of generations to evolve
        mutation_rate: Probability of mutation per assignment
        """
        self.entries = load_timetable(semester, shift)
        if not self.entries:
            raise ValueError("No timetable entries found for the specified semester and shift.")
        
        self.POPULATION_SIZE = population_size
        self.MAX_GENERATIONS = max_generations
        self.MUTATION_RATE = mutation_rate
        self.LECTURES_PER_COURSE = lectures_per_course
        self.MAX_LECTURES_PER_DAY = max_lectures_per_day
        self.LECTURE_DURATION = lecture_duration
        self.START_TIME = start_time
        self.END_TIME = end_time
        
        # Extract unique values from entries
        self.unique_time_slots = self._generate_time_slots()
        self.unique_rooms = list({e['room'] for e in self.entries})
        self.unique_teachers = list({e['teacher'] for e in self.entries})
        
        # Group time slots by day for distribution checks
        self.time_slots_by_day = {}
        for ts in self.unique_time_slots:
            day = ts.split()[0]
            if day not in self.time_slots_by_day:
                self.time_slots_by_day[day] = []
            self.time_slots_by_day[day].append(ts)
        
        # Extract unique courses and sections
        self.unique_courses = list({e['course'] for e in self.entries})
        self.unique_sections = list({e['class_section'] for e in self.entries})
        
        # Add tracking for best fitness
        self.best_fitness_history = []

    def _generate_time_slots(self):
        """Generate time slots based on the provided start and end times."""
        start_dt = datetime.strptime(self.START_TIME, "%I:%M %p")
        end_dt = datetime.strptime(self.END_TIME, "%I:%M %p")
        break_duration = 10  # Break duration in minutes
        
        time_slots = []
        total_minutes = ((end_dt.hour * 60 + end_dt.minute) - 
                         (start_dt.hour * 60 + start_dt.minute))
        slot_duration = self.LECTURE_DURATION + break_duration
        slots_per_day = total_minutes // slot_duration
        
        if slots_per_day <= 0:
            return []
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            current_time = start_dt
            for _ in range(slots_per_day):
                end_time = (datetime(1, 1, 1, current_time.hour, current_time.minute) + 
                            timedelta(minutes=self.LECTURE_DURATION))
                slot_start = current_time.strftime("%I:%M %p")
                slot_end = end_time.strftime("%I:%M %p")
                time_slot = f"{day} {slot_start}-{slot_end}"
                time_slots.append(time_slot)
                current_time = (datetime(1, 1, 1, current_time.hour, current_time.minute) + 
                                timedelta(minutes=slot_duration))
        return time_slots

    def generate_initial_population(self):
        """Generate initial population of random timetables."""
        population = []
        for _ in range(self.POPULATION_SIZE):
            population.append(self._create_random_timetable())
        return population

    def _create_random_timetable(self):
        """Create a single random timetable assignment with better distribution."""
        timetable = {}
        courses_by_section = {}
            
        # First pass: group courses by section
        for entry in self.entries:
            key = (entry['course'], entry['class_section'])
            if entry['class_section'] not in courses_by_section:
                courses_by_section[entry['class_section']] = []
            courses_by_section[entry['class_section']].append(entry['course'])
        
        # Second pass: create multiple entries per course (lectures_per_course times)
        for entry in self.entries:
            course = entry['course']
            section = entry['class_section']
            key = (course, section)
            
            # Create multiple lecture instances for each course
            for i in range(self.LECTURES_PER_COURSE):
                lecture_key = (course, section, i)
                
                # Try to distribute across different days
                available_slots = self._get_distributed_time_slot(timetable, course, section)
                chosen_slot = random.choice(available_slots) if available_slots else random.choice(self.unique_time_slots)
                
                timetable[lecture_key] = {
                    'time_slot': chosen_slot,
                    'room': entry['room'],
                    'teacher': entry['teacher']
                }
                
        return timetable

    def _get_distributed_time_slot(self, timetable, course, section):
        """Get time slots that help distribute this course across different days."""
        # Count how many lectures for this course are on each day
        days_used = {}
        for key, details in timetable.items():
            # Ensure the key has the expected structure
            if len(key) >= 2 and key[0] == course and key[1] == section:
                day = details['time_slot'].split()[0]
                if day not in days_used:
                    days_used[day] = 0
                days_used[day] += 1

        # Prioritize days with fewer lectures of this course
        preferred_days = []
        for day in self.time_slots_by_day:
            count = days_used.get(day, 0)
            if count < self.MAX_LECTURES_PER_DAY:
                preferred_days.append((day, count))

        # Sort by usage (least used first)
        preferred_days.sort(key=lambda x: x[1])

        # If we have preferred days, return slots from those days
        if preferred_days:
            chosen_day = preferred_days[0][0]
            return self.time_slots_by_day[chosen_day]

        # Otherwise return all slots
        return self.unique_time_slots


    def calculate_fitness(self, timetable):
        """Calculate fitness score: lower is better (fewer conflicts)."""
        score = 0
        room_usage = {}
        teacher_usage = {}
        class_usage = {}
        
        # Track distribution metrics
        course_day_counts = {}  # (course, section) -> {day: count}
        day_conflicts = {}
        
        for (course, class_sec, instance), details in timetable.items():
            ts = details['time_slot']
            rm = details['room']
            tch = details['teacher']
            
            # Extract day from time slot (format: "Day HH:MM AM-HH:MM PM")
            day = ts.split()[0] if ' ' in ts else 'Unknown'

            # Room conflict - same room, same time
            room_key = f"{ts}_{rm}"
            if room_key in room_usage:
                score += 20  # Major penalty for room double-booking
            room_usage[room_key] = (course, class_sec)

            # Teacher conflict - same teacher, same time
            teacher_key = f"{tch}_{ts}"
            if teacher_key in teacher_usage:
                score += 15  # Penalty for teacher double-booking
            teacher_usage[teacher_key] = (course, class_sec)

            # Class conflict - same class, same time
            class_key = f"{class_sec}_{ts}"
            if class_key in class_usage:
                score += 25  # Severe penalty for class double-booking
            class_usage[class_key] = (course, class_sec)
            
            # Track course distribution across days
            course_key = (course, class_sec)
            if course_key not in course_day_counts:
                course_day_counts[course_key] = {}
            if day not in course_day_counts[course_key]:
                course_day_counts[course_key][day] = 0
            course_day_counts[course_key][day] += 1
            
            # Penalize multiple classes of same course on same day
            if course_day_counts[course_key][day] > self.MAX_LECTURES_PER_DAY:
                score += 15  # Strong penalty for clustering too many lectures on same day
            
            # Track day distribution penalties - try to spread classes across days
            if day not in day_conflicts:
                day_conflicts[day] = {}
            
            # Track class occurrences per day
            if class_sec not in day_conflicts[day]:
                day_conflicts[day][class_sec] = 0
            day_conflicts[day][class_sec] += 1
            
            # Penalize multiple classes for same section on same day
            if day_conflicts[day][class_sec] > 3:
                score += 10  # Penalty for 4+ classes same day for same section
            
            # Track teacher load per day
            teacher_day_key = f"{tch}_{day}"
            if teacher_day_key not in day_conflicts:
                day_conflicts[teacher_day_key] = 0
            day_conflicts[teacher_day_key] += 1
            
            # Penalize teachers with more than 3 classes per day
            if day_conflicts[teacher_day_key] > 3:
                score += 5  # Penalty for excessive teacher workload per day

        # Add penalties for courses not spread across enough days
        for course_key, day_data in course_day_counts.items():
            # Penalize if a course isn't spread across enough different days
            if len(day_data) < min(3, len(self.time_slots_by_day)):
                score += 20 * (min(3, len(self.time_slots_by_day)) - len(day_data))
            
            # Penalize if course doesn't have exactly the required number of lectures
            total_lectures = sum(day_data.values())
            if total_lectures != self.LECTURES_PER_COURSE:
                score += 30 * abs(total_lectures - self.LECTURES_PER_COURSE)

        return score

    def crossover(self, parent1, parent2):
        """Combine two parent timetables into one child via uniform crossover."""
        child = {}
        keys = list(parent1.keys())
        
        for k in keys:
            # 50% chance of inheriting from each parent
            if random.random() < 0.5:
                child[k] = parent1[k].copy()  # Use .copy() to avoid reference issues
            else:
                child[k] = parent2[k].copy() 
                
        return child

    def mutate(self, timetable):
        """Randomly mutate some assignments in the timetable."""
        for key in list(timetable.keys()):
            if random.random() < self.MUTATION_RATE:
                # Only mutate time slots, keep room and teacher assignments
                timetable[key]['time_slot'] = random.choice(self.unique_time_slots)
        return timetable

    def generate_optimized_timetable(self):
        """Run the genetic algorithm and return the best timetable found."""
        if not self.entries:
            return None

        population = self.generate_initial_population()
        best_fitness = float('inf')
        best_solution = None
        no_improvement_count = 0

        for generation in range(self.MAX_GENERATIONS):
            # Evaluate all solutions
            scored = [(tt, self.calculate_fitness(tt)) for tt in population]
            # Sort ascending by score (lower is better)
            scored.sort(key=lambda x: x[1])
            
            current_best = scored[0]
            self.best_fitness_history.append(current_best[1])
            
            # Check if we found a better solution
            if current_best[1] < best_fitness:
                best_fitness = current_best[1]
                best_solution = current_best[0]
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # If perfect (0 conflicts) or no improvement for many generations, return early
            if current_best[1] == 0 or no_improvement_count > 20:
                return best_solution
                
            # Select top performers (elitism)
            elite_count = self.POPULATION_SIZE // 10  # Top 10%
            elites = [tt for tt, _ in scored[:elite_count]]
            
            # Selection pool - use tournament selection
            tournament_size = 3
            
            # Create new generation
            new_pop = elites.copy()  # Keep elites
            
            # Fill the rest with crossover and mutation
            while len(new_pop) < self.POPULATION_SIZE:
                # Tournament selection for parents
                parent1 = min(random.sample(population, tournament_size), 
                            key=self.calculate_fitness)
                parent2 = min(random.sample(population, tournament_size), 
                            key=self.calculate_fitness)
                
                # Create child via crossover
                child = self.crossover(parent1, parent2)
                
                # Mutate
                child = self.mutate(child)
                
                # Add to new population
                new_pop.append(child)
                
            population = new_pop

        # Return best after final generation
        return best_solution