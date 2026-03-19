def evaluate_solution(solution, evaluator):
    total_cost = 0
    for yard_id, type_dict in solution.yards.items():
        cost, feasible = evaluator.evaluate(yard_id, type_dict)   #调用layout
        if not feasible:
            cost += 1e6  # penalty
        total_cost += cost
    spread_penalty = compute_spread(solution)   #计算分散度
    total_cost += spread_penalty
    return total_cost

def compute_spread(solution):
    type_yard_count = {}
    for yard_id, types in solution.yards.items():
        for t in types:
            type_yard_count.setdefault(t, set()).add(yard_id)
    spread = sum(len(v) for v in type_yard_count.values())
    return spread * 100  # 权重自己调