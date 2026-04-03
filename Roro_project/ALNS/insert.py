from evaluate_solution import compute_type_spread, WEIGHTS  # 4/3需求：导入集中化权重参数
from data import yard_sizes as _yard_sizes, vehicle_info as _vehicle_info  # 4/2新增代码
import copy
import random


# ─────────────────────────────────────────────────────────────────────────────
# 4/2新增代码: 均衡辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _compute_balance_delta(solution, target_yard, t, qty):  # 4/2新增代码
    """
    计算将 qty 辆 t 型车插入 target_yard 后，堆场负载均衡惩罚的变化量 (Δbalance)。
    4/3修改：只统计活跃堆场（与 compute_balance_penalty 保持一致）。
    """
    yard_ids = list(solution.yards.keys())

    old_utils = []
    active_mask = []
    for yid in yard_ids:
        is_active = bool(solution.yards[yid])
        active_mask.append(is_active)
        W, H = _yard_sizes[yid]
        used = sum(
            _vehicle_info[vt][0] * _vehicle_info[vt][1] * q
            for vt, q in solution.yards[yid].items()
            if vt in _vehicle_info
        )
        old_utils.append(used / (W * H))

    # 插入后的利用率
    new_utils = list(old_utils)
    idx = yard_ids.index(target_yard)
    W, H = _yard_sizes[target_yard]
    w, h = _vehicle_info[t]
    new_utils[idx] = min(1.0, old_utils[idx] + w * h * qty / (W * H))

    # 4/3需求：只在活跃堆场（或插入后变活跃的堆场）间计算方差
    new_active = [active_mask[i] or (yard_ids[i] == target_yard) for i in range(len(yard_ids))]

    def _var_active(utils, mask):
        active_utils = [u for u, m in zip(utils, mask) if m]
        if len(active_utils) < 2:
            return 0.0
        m = sum(active_utils) / len(active_utils)
        return sum((u - m) ** 2 for u in active_utils) / len(active_utils)

    return (_var_active(new_utils, new_active) - _var_active(old_utils, active_mask)) * WEIGHTS['balance']


# ─────────────────────────────────────────────────────────────────────────────
# 原有贪心修复算子（保留，alns.py 已改用 repair_regret）
# ─────────────────────────────────────────────────────────────────────────────

def repair(solution, removed, layout):
    """
    修复算子（原贪心版本）：已被 repair_regret 取代，此处保留以备对比。
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
# 4/3需求：车型集中与少堆场 — 增加亲和度机制
# ─────────────────────────────────────────────────────────────────────────────

def repair_regret(solution, removed, layout, batch_size=10):  # 4/2新增代码
    """
    Regret-2 + 分批插入 + 亲和度机制修复算子。

    Δcost 综合指标 = Δlayout + Δbalance + 亲和度调整
      - 同类已存在目标堆场：给予 WEIGHTS['affinity_bonus'] 折扣（鼓励集中）
      - 目标堆场为空：施加 WEIGHTS['empty_penalty'] 惩罚（排斥开新堆场）
      - 若所有非空堆场均不可行，才允许写入空堆场
    """
    new_sol = solution.deepcopy()

    # 4/2新增代码: 将 removed 按 batch_size 拆分为细粒度批次
    pending = []
    for _, t, qty in removed:
        while qty > 0:
            b = min(qty, batch_size)
            pending.append((t, b))
            qty -= b

    while pending:
        best_item_idx  = None
        best_regret    = -float('inf')
        best_target_yard = None

        for idx, (t, qty) in enumerate(pending):
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
                delta_bal    = _compute_balance_delta(new_sol, yard_id, t, qty)

                # 4/3需求：车型集中与少堆场 — 亲和度调整
                yard_is_empty     = not bool(old_types)
                already_has_type  = t in old_types
                affinity_adj = 0
                if already_has_type:
                    affinity_adj -= WEIGHTS['affinity_bonus']  # 4/3需求: 同类吸引，成本折扣
                elif yard_is_empty:
                    affinity_adj += WEIGHTS['empty_penalty']   # 4/3需求: 排斥空堆场

                delta = delta_layout + delta_bal + affinity_adj
                candidates.append((delta, yard_id))

            if not candidates:
                continue

            candidates.sort(key=lambda x: x[0])
            best_cost_val     = candidates[0][0]
            best_yard_for_item = candidates[0][1]
            second_cost_val   = candidates[1][0] if len(candidates) > 1 else best_cost_val + 1e5

            # 4/2新增代码: 后悔值 = 次优cost - 最优cost
            regret = second_cost_val - best_cost_val
            if regret > best_regret:
                best_regret      = regret
                best_item_idx    = idx
                best_target_yard = best_yard_for_item

        if best_item_idx is None:
            break

        # 4/2新增代码: 插入后悔值最大的批次
        t, qty = pending[best_item_idx]
        if best_target_yard is not None:
            new_sol.yards[best_target_yard][t] = \
                new_sol.yards[best_target_yard].get(t, 0) + qty
        pending.pop(best_item_idx)

    return new_sol
