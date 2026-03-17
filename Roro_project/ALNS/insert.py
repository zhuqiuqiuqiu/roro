def insert_greedy(solution, removed, evaluator):
    new_sol = solution.deepcopy()
    for (veh_type, qty) in removed:
        best_yard = None
        best_delta = float("inf")
        for yard_id in new_sol.yards:
            old_types = new_sol.yards[yard_id]
            new_types = old_types.copy()
            new_types[veh_type] = new_types.get(veh_type, 0) + qty
            # Δcost
            old_cost, _ = evaluator.evaluate(yard_id, old_types)
            new_cost, feasible = evaluator.evaluate(yard_id, new_types)

            delta = new_cost - old_cost
            if not feasible:
                delta += 1e6
            if delta < best_delta:
                best_delta = delta
                best_yard = yard_id
        # 插入最优堆场
        if best_yard is not None:
            new_sol.yards[best_yard][veh_type] = \
                new_sol.yards[best_yard].get(veh_type, 0) + qty
    return new_sol