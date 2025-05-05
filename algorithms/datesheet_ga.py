"""
Genetic algorithm for generating examination datesheets.
"""
import random

class DatesheetGeneticAlgorithm:
    def __init__(self, entries, max_generations=100, population_size=50):
        """
        entries: list of dicts with keys 'date', 'subject', 'room', 'time'
        max_generations: number of generations to evolve
        population_size: number of candidate schedules per generation
        """
        self.entries = entries
        self.max_generations = max_generations
        self.population_size = population_size

    def calculate_fitness(self, schedule):
        """
        Calculate fitness based on:
        1. No subject conflicts on same date
        2. No room conflicts on same date
        3. Spread of exams across dates
        Higher fitness means fewer conflicts and better spread.
        """
        conflicts = 0
        room_usage = {}
        date_subjects = {}

        for exam in schedule:
            date = exam['date']
            room = exam['room']
            subject = exam['subject']

            # Subject conflict
            if date not in date_subjects:
                date_subjects[date] = set()
            if subject in date_subjects[date]:
                conflicts += 1
            date_subjects[date].add(subject)

            # Room conflict
            if room not in room_usage:
                room_usage[room] = set()
            if date in room_usage[room]:
                conflicts += 1
            room_usage[room].add(date)

        # Spread bonus
        unique_dates = len(set(exam['date'] for exam in schedule))
        spread_bonus = unique_dates / len(schedule)

        # Higher is better
        return (1 / (1 + conflicts)) * spread_bonus

    def crossover(self, parent1, parent2):
        """
        Single-point crossover between two schedules.
        """
        point = random.randint(0, len(parent1) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2

    def mutate(self, schedule):
        """
        Randomly change date or room in the schedule.
        """
        mutated = [exam.copy() for exam in schedule]
        for exam in mutated:
            if random.random() < 0.1:  # 10% chance
                if random.random() < 0.5:
                    exam['date'] = random.choice(
                        list({e['date'] for e in self.entries})
                    )
                else:
                    exam['room'] = random.choice(
                        list({e['room'] for e in self.entries})
                    )
        return mutated

    def generate_initial_population(self):
        """
        Create initial random population of schedules.
        """
        population = []
        dates = list({e['date'] for e in self.entries})
        rooms = list({e['room'] for e in self.entries})

        for _ in range(self.population_size):
            schedule = []
            for exam in self.entries:
                new_exam = exam.copy()
                new_exam['date'] = random.choice(dates)
                new_exam['room'] = random.choice(rooms)
                schedule.append(new_exam)
            population.append(schedule)
        return population

    def run(self):
        """
        Evolve the population and return the best schedule.
        """
        population = self.generate_initial_population()

        for _ in range(self.max_generations):
            # Score and sort
            scored = [(sched, self.calculate_fitness(sched)) for sched in population]
            scored.sort(key=lambda x: x[1], reverse=True)

            # Select top half
            top = [sched for sched, fit in scored[:self.population_size // 2]]

            # Reproduce
            new_pop = top.copy()
            while len(new_pop) < self.population_size:
                p1, p2 = random.sample(top, 2)
                c1, c2 = self.crossover(p1, p2)
                new_pop.append(self.mutate(c1))
                if len(new_pop) < self.population_size:
                    new_pop.append(self.mutate(c2))
            population = new_pop

        # Return best schedule
        best = max(population, key=self.calculate_fitness)
        return best
