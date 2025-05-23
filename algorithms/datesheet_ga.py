"""
Genetic algorithm for generating examination datesheets.
"""
import random
import datetime

class DatesheetGeneticAlgorithm:
    def __init__(
        self,
        entries,
        max_generations=100,
        population_size=50,
        start_date=None,
        exam_start_time="09:00",
        exam_end_time="13:00",
        exam_days=None,
        excluded_dates=None,
    ):
        """
        entries: list of dicts with keys 'subject', 'room', 'shift', 'semester', 'teacher', 'course_code', 'class_section'
        start_date: string YYYY-MM-DD
        exam_start_time, exam_end_time: string HH:MM
        exam_days: list of weekdays, e.g. ["Monday", ...]
        excluded_dates: list of YYYY-MM-DD strings
        """
        self.entries = entries
        self.max_generations = max_generations
        self.population_size = population_size
        self.start_date = start_date
        self.exam_start_time = exam_start_time
        self.exam_end_time = exam_end_time
        self.exam_days = exam_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.excluded_dates = set(excluded_dates or [])

        # Prepare exam slots (dates) based on parameters
        self.exam_slots = self._generate_exam_slots()

    def _generate_exam_slots(self):
        # Generate a list of valid exam dates (YYYY-MM-DD) based on start_date, days, and excluded_dates
        if not self.start_date:
            return []
        slots = []
        dt = datetime.datetime.strptime(self.start_date, "%Y-%m-%d")
        needed = self._needed_exam_days()
        while len(slots) < needed:
            day_name = dt.strftime("%A")
            date_str = dt.strftime("%Y-%m-%d")
            if (
                day_name in self.exam_days
                and date_str not in self.excluded_dates
            ):
                slots.append(date_str)
            dt += datetime.timedelta(days=1)
        return slots

    def _needed_exam_days(self):
        # One exam per day per semester/section
        # So, for each unique (semester, class_section), count number of exams
        sem_sec = {}
        for e in self.entries:
            key = (e["semester"], e["class_section"])
            sem_sec.setdefault(key, 0)
            sem_sec[key] += 1
        # The max number of exams for any (semester, section)
        return max(sem_sec.values()) if sem_sec else 0

    def calculate_fitness(self, schedule):
        """
        Fitness is higher if:
        - No two exams for the same semester/section are on the same day
        - No room conflicts (all exams run at the same time, so each room can only have one exam per day)
        - Each course's teacher is the invigilator (enforced by construction)
        - All exams are assigned
        """
        conflicts = 0
        # 1. No two exams for the same semester/section on the same day
        sem_sec_day = {}
        room_day = {}
        for exam in schedule:
            key = (exam["semester"], exam["class_section"], exam["date"])
            if key in sem_sec_day:
                conflicts += 1
            sem_sec_day[key] = True

            # 2. No room conflicts (all exams at same time)
            room_key = (exam["room"], exam["date"])
            if room_key in room_day:
                conflicts += 1
            room_day[room_key] = True

        # 3. All exams assigned
        missing = 0
        if len(schedule) < len(self.entries):
            missing = len(self.entries) - len(schedule)
            conflicts += missing * 10

        # 4. Spread bonus: more unique dates used (encourage spreading)
        unique_dates = len(set(exam["date"] for exam in schedule))
        spread_bonus = unique_dates / (len(schedule) or 1)

        return (1 / (1 + conflicts)) * spread_bonus

    def crossover(self, parent1, parent2):
        point = random.randint(0, len(parent1) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2

    def mutate(self, schedule):
        mutated = [exam.copy() for exam in schedule]
        for exam in mutated:
            if random.random() < 0.1:
                # Only mutate date (room is fixed per exam)
                exam["date"] = random.choice(self.exam_slots)
        return mutated

    def generate_initial_population(self):
        """
        Each schedule is a list of exams, each assigned to a date (from allowed slots).
        All exams for a given day are at the same time (enforced by output).
        Each course's teacher is the invigilator (enforced by construction).
        """
        population = []
        for _ in range(self.population_size):
            # For each (semester, class_section), assign exams to unique days (one per day)
            # Shuffle exams per group, assign to random available days
            exams_by_group = {}
            for e in self.entries:
                key = (e["semester"], e["class_section"])
                exams_by_group.setdefault(key, []).append(e)
            schedule = []
            for group, exams in exams_by_group.items():
                days = random.sample(self.exam_slots, len(exams))
                for exam, date in zip(exams, days):
                    sched_exam = exam.copy()
                    sched_exam["date"] = date
                    sched_exam["time"] = self.exam_start_time  # All exams at same time
                    # Teacher is invigilator (enforced by construction)
                    schedule.append(sched_exam)
            population.append(schedule)
        return population

    def run(self):
        if not self.exam_slots or not self.entries:
            return []

        population = self.generate_initial_population()
        for _ in range(self.max_generations):
            scored = [(sched, self.calculate_fitness(sched)) for sched in population]
            scored.sort(key=lambda x: x[1], reverse=True)
            top = [sched for sched, fit in scored[:self.population_size // 2]]
            new_pop = top.copy()
            while len(new_pop) < self.population_size:
                p1, p2 = random.sample(top, 2)
                c1, c2 = self.crossover(p1, p2)
                new_pop.append(self.mutate(c1))
                if len(new_pop) < self.population_size:
                    new_pop.append(self.mutate(c2))
            population = new_pop

        best = max(population, key=self.calculate_fitness)
        # Output: add 'teacher' as invigilator, all exams at same time
        for exam in best:
            exam["invigilator"] = exam["teacher"]
            exam["time"] = self.exam_start_time
        # Sort by date, semester, section
        best.sort(key=lambda e: (e["date"], e["semester"], e["class_section"]))
        return best
