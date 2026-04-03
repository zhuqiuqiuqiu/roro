from data import yard_sizes as _yard_sizes, vehicle_info as _vehicle_info  # 4/2新增代码: 导入数据用于均衡惩罚计算


def evaluate_solution(solution, evaluator):
    """
    evaluate是最终评分，调用layout布局评估 + 堆场负载均衡惩罚
    """
    total_cost = 0
    for yard_id, type_dict in solution.yards.items():
        cost, feasible, placements = evaluator.evaluate(yard_id, type_dict)
        if not feasible:
            cost += 1e6
        total_cost += cost

    # 4/2新增代码: 用堆场均衡惩罚替换原有spread惩罚
    # 原compute_spread统计车型分布堆场数并惩罚分散，方向与业务相反，导致集中
    balance_penalty = compute_balance_penalty(solution)
    total_cost += balance_penalty
    return total_cost


def compute_balance_penalty(solution):  # 4/2新增代码
    """
    堆场负载均衡惩罚：计算各堆场利用率的方差，方差越大（分布越不均匀）惩罚越高。
    促使车辆在各堆场间均匀分布，消除单堆场极度拥挤现象。
    """
    utils = []
    for yard_id, types in solution.yards.items():
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
    variance = sum((u - mean_util) ** 2 for u in utils) / len(utils)
    # 4/2新增代码: 系数10000使均衡惩罚与layout cost处于同一量级
    return variance * 10000


def compute_spread(solution):
    """
    保留原函数，不再在主目标函数中使用（逻辑鼓励集中，已被compute_balance_penalty替代）
    """
    type_yard_count = {}
    for yard_id, types in solution.yards.items():
        for t in types:
            type_yard_count.setdefault(t, set()).add(yard_id)
    spread = sum(len(v) for v in type_yard_count.values())
    return spread * 5


def compute_type_spread(solution, t):
    """
    单独计算有多少个堆场存放了类型为t的车辆
    """
    count = 0
    for yard_id, types in solution.yards.items():
        if t in types:
            count += 1
    return count
