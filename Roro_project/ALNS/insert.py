from evaluate_solution import compute_type_spread
from data import yard_sizes as _yard_sizes, vehicle_info as _vehicle_info  # 4/2新增代码
import copy
import random


# ─────────────────────────────────────────────────────────────────────────────
# 4/2新增代码: 均衡辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _compute_balance_delta(solution, target_yard, t, qty):  # 4/2新增代码
    """
    计算将 qty 辆 t 型车插入 target_yard 后，堆场负载均衡惩罚的变化量 (Δbalance)。
    与 evaluate_solution.compute_balance_penalty 系数保持一致（×10000）。
    """
    yard_ids = list(solution.yards.keys())

    old_utils = []
    for yid in yard_ids:
        W, H = _yard_sizes[yid]
        used = sum(
            _vehicle_info[vt][0] * _vehicle_info[vt][1] * q
            for vt, q in solution.yards[yid].items()
            if vt in _vehicle_info
        )
        old_utils.append(used / (W * H))

    new_utils = list(old_utils)
    idx = yard_ids.index(target_yard)
    W, H = _yard_sizes[target_yard]
    w, h = _vehicle_info[t]
    # 4/2新增代码: 限制在1.0以内防止浮点越界
    new_utils[idx] = min(1.0, old_utils[idx] + w * h * qty / (W * H))

    def _var(utils):
        if len(utils) < 2:
            return 0.0
        m = sum(utils) / len(utils)
        return sum((u - m) ** 2 for u in utils) / len(utils)

    return (_var(new_utils) - _var(old_utils)) * 10000  # 4/2新增代码: 与evaluate_solution系数一致


# ─────────────────────────────────────────────────────────────────────────────
# 原有贪心修复算子（保留，alns.py 已改用 repair_regret）
# ─────────────────────────────────────────────────────────────────────────────

def repair(solution, removed, layout):
    """
    修复算子（原贪心版本）：将 removed 中的车辆重新分配到最优堆场。
    已被 repair_regret 取代，此处保留以备对比。
    """
    new_sol = solution.deepcopy()
    for yard_id_old, t, qty in removed:
        best_yard = None
        best_delta = float("inf")
        for yard_id in new_sol.yards:
            old_types = new_sol.yards[yard_id]
            new_types = copy.deepcopy(old_types)
            new_types[t] = new_types.get(t, 0) + qty
            old_cost, _, _ = layout.evaluate(yard_id, old_types)
            new_cost, feasible, _ = layout.evaluate(yard_id, new_types)
            delta_layout = new_cost - old_cost

            old_spread = compute_type_spread(new_sol, t)
            if t not in old_types:
                new_spread = old_spread + 1
            else:
                new_spread = old_spread
            delta_spread = (new_spread - old_spread) * 5

            delta = delta_layout + delta_spread
            if not feasible:
                continue
            if delta < best_delta:
                best_delta = delta
                best_yard = yard_id
        if best_yard is not None:
            new_sol.yards[best_yard][t] = \
                new_sol.yards[best_yard].get(t, 0) + qty
    return new_sol


# ─────────────────────────────────────────────────────────────────────────────
# 4/2新增代码: Regret-2 + 分批插入修复算子
# ─────────────────────────────────────────────────────────────────────────────

def repair_regret(solution, removed, layout, batch_size=10):  # 4/2新增代码
    """
    Regret-2 + 分批插入修复算子（替代原贪心 repair）。

    核心思路：
    1. 分批插入 —— 将每批次车辆数限制为 batch_size，避免一次性贪心陷入极端局部最优。
    2. Regret-2  —— 对每个待插入批次，计算所有堆场的 Δcost；
                   "后悔值" = 次优cost - 最优cost，后悔值最大的批次优先插入，
                   防止忽略"错过最佳位置代价极高"的车辆。
    3. Δcost 综合指标 = Δlayout + Δbalance（均衡惩罚变化量）。
    """
    new_sol = solution.deepcopy()

    # 4/2新增代码: 将 removed 按 batch_size 拆分为细粒度批次
    pending = []  # list of (t, qty)
    for _, t, qty in removed:
        while qty > 0:
            b = min(qty, batch_size)
            pending.append((t, b))
            qty -= b

    while pending:
        best_item_idx = None
        best_regret = -float('inf')
        best_target_yard = None

        for idx, (t, qty) in enumerate(pending):
            # 4/2新增代码: 对每个候选堆场计算综合 Δcost = Δlayout + Δbalance
            candidates = []
            for yard_id in new_sol.yards:
                old_types = new_sol.yards[yard_id]
                new_types = copy.deepcopy(old_types)
                new_types[t] = new_types.get(t, 0) + qty

                old_cost, _, _ = layout.evaluate(yard_id, old_types)
                new_cost, feasible, _ = layout.evaluate(yard_id, new_types)
                if not feasible:
                    continue

                delta_layout = new_cost - old_cost
                # 4/2新增代码: Δbalance 促进均衡分布
                delta_bal = _compute_balance_delta(new_sol, yard_id, t, qty)
                delta = delta_layout + delta_bal
                candidates.append((delta, yard_id))

            if not candidates:
                continue

            candidates.sort(key=lambda x: x[0])
            best_cost_val = candidates[0][0]
            best_yard_for_item = candidates[0][1]
            # 4/2新增代码: Regret-2 后悔值 = 次优 - 最优
            second_cost_val = candidates[1][0] if len(candidates) > 1 else best_cost_val + 1e5
            regret = second_cost_val - best_cost_val

            if regret > best_regret:
                best_regret = regret
                best_item_idx = idx
                best_target_yard = best_yard_for_item

        if best_item_idx is None:
            break

        # 4/2新增代码: 将后悔值最大的批次插入最优堆场
        t, qty = pending[best_item_idx]
        if best_target_yard is not None:
            new_sol.yards[best_target_yard][t] = \
                new_sol.yards[best_target_yard].get(t, 0) + qty
        pending.pop(best_item_idx)

    return new_sol
