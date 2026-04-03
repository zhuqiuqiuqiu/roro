from data import yard_sizes as _yard_sizes, vehicle_info as _vehicle_info  # 4/2新增代码: 导入数据用于均衡惩罚计算

# ─────────────────────────────────────────────────────────────────────────────
# 4/3需求：车型集中与少堆场 — 全局权重参数（集中前置，便于手动调参）
# ─────────────────────────────────────────────────────────────────────────────
WEIGHTS = {
    # ── 原有权重 ──────────────────────────────────────────────────────────────
    'layout':         1.0,    # layout cost（空余面积 + 高利用率惩罚）乘数
    'balance':        10000,  # 已启用堆场间利用率方差惩罚系数（只计算活跃堆场）

    # ── 4/3新增权重 ───────────────────────────────────────────────────────────
    'activation':     10000,  # 每启用一个堆场的固定惩罚（逼迫少开堆场）
    'fragmentation':  5000,   # 同车型每多跨一个堆场的打散惩罚（(N-1) × weight）

    # ── insert.py 使用的亲和度参数（集中在此便于联合调参）────────────────────
    'affinity_bonus': 3000,   # 车型已存在目标堆场时给予的成本折扣（越大越倾向集中）
    'empty_penalty':  8000,   # 向空堆场插入车辆时施加的惩罚（越大越排斥开新堆场）
}


# ─────────────────────────────────────────────────────────────────────────────
# 目标函数
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_solution(solution, evaluator):
    """
    综合目标函数：
      layout cost × layout权重
      + 已启用堆场利用率均衡惩罚（仅活跃堆场）
      + 堆场启用固定成本
      + 车型打散惩罚
    """
    total_cost = 0
    for yard_id, type_dict in solution.yards.items():
        cost, feasible, placements = evaluator.evaluate(yard_id, type_dict)
        if not feasible:
            cost += 1e6
        total_cost += cost * WEIGHTS['layout']

    total_cost += compute_balance_penalty(solution)
    total_cost += compute_activation_cost(solution)        # 4/3需求：车型集中与少堆场
    total_cost += compute_fragmentation_penalty(solution)  # 4/3需求：车型集中与少堆场
    return total_cost


# ─────────────────────────────────────────────────────────────────────────────
# 各惩罚项计算
# ─────────────────────────────────────────────────────────────────────────────

def compute_balance_penalty(solution):
    """
    已启用堆场间负载均衡惩罚：各活跃堆场利用率方差 × WEIGHTS['balance']。
    4/3修改：只在已启用（有车辆）的堆场间评估，绝不为了均衡而激活空堆场。
    """
    utils = []
    for yard_id, types in solution.yards.items():
        if not types:          # 4/3需求：跳过空堆场，只计算活跃堆场
            continue
        W, H = _yard_sizes[yard_id]
        total_area = W * H
        used_area = sum(
            _vehicle_info[t][0] * _vehicle_info[t][1] * q
            for t, q in types.items()
            if t in _vehicle_info
        )
        utils.append(used_area / total_area if total_area > 0 else 0.0)

    if len(utils) < 2:
        return 0.0

    mean_util = sum(utils) / len(utils)
    variance  = sum((u - mean_util) ** 2 for u in utils) / len(utils)
    return variance * WEIGHTS['balance']


def compute_activation_cost(solution):   # 4/3需求：车型集中与少堆场
    """
    堆场启用固定成本：每启用一个有车辆的堆场，施加固定惩罚。
    逼迫算法优先塞满已启用堆场，而不是开辟新堆场。
    """
    active_count = sum(1 for types in solution.yards.values() if types)
    return active_count * WEIGHTS['activation']


def compute_fragmentation_penalty(solution):   # 4/3需求：车型集中与少堆场
    """
    车型打散惩罚：某车型分布在 N 个堆场 → penalty = (N-1) × WEIGHTS['fragmentation']。
    鼓励同类车型高度集中在一个堆场。
    """
    type_yards = {}
    for yard_id, types in solution.yards.items():
        for t in types:
            type_yards.setdefault(t, set()).add(yard_id)

    penalty = 0
    for t, yards in type_yards.items():
        n = len(yards)
        if n > 1:
            penalty += (n - 1) * WEIGHTS['fragmentation']
    return penalty


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数（供其他模块调用）
# ─────────────────────────────────────────────────────────────────────────────

def compute_spread(solution):
    """保留原函数签名（已被 compute_fragmentation_penalty 替代，不再参与主目标）"""
    type_yard_count = {}
    for yard_id, types in solution.yards.items():
        for t in types:
            type_yard_count.setdefault(t, set()).add(yard_id)
    spread = sum(len(v) for v in type_yard_count.values())
    return spread * 5


def compute_type_spread(solution, t):
    """单独计算车型 t 分布在几个堆场（insert.py 使用）"""
    count = 0
    for yard_id, types in solution.yards.items():
        if t in types:
            count += 1
    return count
