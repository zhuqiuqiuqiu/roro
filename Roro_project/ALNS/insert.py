from evaluate_solution import compute_spread
def repair(solution, removed, layout):
    new_sol = solution.deepcopy()

    for t, qty in removed:

        best_yard = None
        best_delta = float("inf")

        for yard_id in new_sol.yards:

            old_types = new_sol.yards[yard_id]
            new_types = old_types.copy()
            new_types[t] = new_types.get(t, 0) + qty

            # --- layout cost ---
            old_cost, _ = layout.evaluate(yard_id, old_types)
            new_cost, feasible = layout.evaluate(yard_id, new_types)

            delta_layout = new_cost - old_cost

            # --- spread cost ---
            old_spread = compute_spread(new_sol)

            # 临时加进去算
            new_sol.yards[yard_id] = new_types
            new_spread = compute_spread(new_sol)
            new_sol.yards[yard_id] = old_types  # 还原

            delta_spread = new_spread - old_spread

            # --- 总 delta ---
            delta = delta_layout + delta_spread

            if not feasible:
                delta += 1e6

            if delta < best_delta:
                best_delta = delta
                best_yard = yard_id

        if best_yard is not None:
            new_sol.yards[best_yard][t] = \
                new_sol.yards[best_yard].get(t, 0) + qty

    return new_sol