import math
from insert import *
from delete import *
from evaluate_solution import *
from layoutevaluator import *
from solution import Solution
def alns(initial_solution, max_iter=300):

    layout = SkylineLayout()

    current = initial_solution
    current.cost = evaluate_solution(current, layout)

    best = current.deepcopy()
    best.cost = current.cost

    T = 500

    for it in range(max_iter):

        destroyed, removed = destroy(current)

        candidate = repair(destroyed, removed, layout)
        candidate.cost = evaluate_solution(candidate, layout)

        delta = candidate.cost - current.cost

        if delta < 0 or random.random() < math.exp(-delta / T):
            current = candidate

        if current.cost < best.cost:
            best = current.deepcopy()
            best.cost = current.cost

        T *= 0.98

        if it % 50 == 0:
            print(f"Iter {it}, Best Cost: {best.cost}")

    return best