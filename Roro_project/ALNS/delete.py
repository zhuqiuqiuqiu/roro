import random
from data import yard_sizes
def destroy(solution, layout, ratio=0.4):
    new_sol = solution.deepcopy()
    removed = []
    all_items = []
    for yard_id, types in new_sol.yards.items():
        for t in types:
            all_items.append((yard_id, t))
    num_remove = max(1, int(len(all_items) * ratio))
    selected = random.sample(all_items, num_remove)
    for yard_id, t in selected:
        removed.append((yard_id, t, new_sol.yards[yard_id][t]))
        del new_sol.yards[yard_id][t]
    return new_sol, removed

def destroy_size(solution, layout, ratio=0.4):
    """
    移除占用率低的堆场上面的车辆，删除比例由remove_ratio控制
    """
    new_sol = solution.deepcopy()
    removed = []
    yard_util = {}
    for yard_id, types in new_sol.yards.items():
        W, H = layout.yard_sizes[yard_id]
        total_area = W * H
        used_area = 0
        for t, q in types.items():
            if t not in layout.vehicle_info:
                continue
            w, h = layout.vehicle_info[t]
            used_area += w * h * q
        util = used_area / total_area if total_area > 0 else 0
        yard_util[yard_id] = util
    #根据利用率排序
    sorted_yards = sorted(yard_util.items(), key=lambda x: x[1])
    num_remove = max(1, int(len(sorted_yards) * ratio))
    selected_yards = [y for y, _ in sorted_yards[:num_remove]]
    for yard_id in selected_yards:
        types = new_sol.yards[yard_id]
        for t in list(types.keys()):
            removed.append((yard_id, t, types[t]))
            del types[t]
    return new_sol, removed

def destroy_spread(solution, layout, ratio=0.4):
    """
    破坏被分散的车型
    """
    new_sol = solution.deepcopy()
    removed = []
    # 车型分散程度
    type_yards = {}
    for yard_id, types in new_sol.yards.items():
        for t in types:
            type_yards.setdefault(t, set()).add(yard_id)
    # 计算分散程度
    type_spread = [ ]
    for t , yards in type_yards.items():
        spread = len(yards)
        type_spread.append((t, spread))
    # 根据分散程度排序
    type_spread.sort(key=lambda x: -x[1])
    # 移除车型的筛选
    num_remove = max(1, int(len(type_spread) * ratio))
    selected_types = [t for t, _ in type_spread[:num_remove]]
    # 从所有堆场中移除这些车型
    for yard_id, types in new_sol.yards.items():
        for t in list(types.keys()):
            if t in selected_types and random.random() < 0.7:
                removed.append((yard_id, t, types[t]))
                del types[t]
    return new_sol, removed


def destroy_fragmented_types(solution, layout, ratio=0.4):   # 4/3需求：车型集中与少堆场
    """
    针对性破坏算子：找出"打散最严重"的车型（分布堆场数最多），
    将其所有车辆从全部堆场中移出，交由 repair_regret 重新集中插入。

    若当前解中所有车型都只在一个堆场，则退化为普通随机破坏。
    """
    new_sol = solution.deepcopy()
    removed = []

    # 统计每种车型分布的堆场集合
    type_yards = {}
    for yard_id, types in new_sol.yards.items():
        for t in types:
            type_yards.setdefault(t, set()).add(yard_id)

    if not type_yards:
        return new_sol, removed

    # 按打散度（堆场数）降序排列
    type_spread = sorted(type_yards.items(), key=lambda x: -len(x[1]))

    # 选取打散度 > 1 的车型（真正跨堆场）
    fragmented = [(t, yards) for t, yards in type_spread if len(yards) > 1]

    if not fragmented:
        # 退化：无打散车型时随机破坏
        return destroy(solution, layout, ratio=ratio)

    # 选取打散最严重的 max(1, int(len * ratio)) 个车型
    num_select   = max(1, int(len(fragmented) * ratio))
    selected_types = {t for t, _ in fragmented[:num_select]}

    # 将所选车型的全部实例从所有堆场移出
    for yard_id, types in new_sol.yards.items():
        for t in list(types.keys()):
            if t in selected_types:
                removed.append((yard_id, t, types[t]))
                del types[t]

    return new_sol, removed