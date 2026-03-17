import random

def remove_by_type(solution, remove_ratio=0.3):
    new_sol = solution.deepcopy()
    removed = []
    for yard_id, types in new_sol.yards.items():
        for t in list(types.keys()):
            if random.random() < remove_ratio:
                removed.append((t, types[t]))
                del types[t]

    return new_sol, removed