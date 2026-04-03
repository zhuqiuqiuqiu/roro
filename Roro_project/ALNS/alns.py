from insert import repair, repair_regret  # 4/2新增代码: 导入新Regret修复算子
from delete import destroy, destroy_size, destroy_spread
from evaluate_solution import evaluate_solution
from layoutevaluator import SkylineLayout
import random
import math  # 4/2新增代码: 显式导入math


# ─────────────────────────────────────────────────────────────────────────────
# 4/2新增代码: 轮盘赌选择函数
# ─────────────────────────────────────────────────────────────────────────────

def _roulette_wheel(weights):  # 4/2新增代码
    """
    轮盘赌选择：根据权重概率返回算子索引。
    权重越高的算子被选中概率越大。
    """
    total = sum(weights)
    r = random.random() * total
    cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if r <= cumulative:
            return i
    return len(weights) - 1


# ─────────────────────────────────────────────────────────────────────────────
# ALNS 主函数（含自适应权重 + Regret-2）
# ─────────────────────────────────────────────────────────────────────────────

def alns(initial_solution, layout, max_iter=300,
         snapshot_callback=None, save_interval=50):  # 4/2新增：可视化触发接口
    current = initial_solution
    current.cost = evaluate_solution(current, layout)

    best = current.deepcopy()
    best.cost = current.cost
    history = []
    T = 500.0

    # ── 破坏算子列表 ──────────────────────────────────────────────────────────
    destroy_ops = [
        lambda sol: destroy(sol, layout),
        lambda sol: destroy_size(sol, layout),
        lambda sol: destroy_spread(sol, layout)
    ]
    n_ops = len(destroy_ops)

    # 4/2新增代码: 自适应权重初始化（各算子初始权重相等）
    weights = [1.0] * n_ops
    scores  = [0.0] * n_ops   # 4/2新增代码: 当前周期内的累计得分
    uses    = [0]   * n_ops   # 4/2新增代码: 当前周期内的使用次数

    # 4/2新增代码: 评分参数（参考 Ropke & Pisinger 2006 ALNS框架）
    SIGMA1 = 10   # 发现全局最优解
    SIGMA2 = 5    # 产生可接受的改进解
    SIGMA3 = 1    # 被模拟退火接受但未改善best

    # 4/2新增代码: 权重更新参数
    DECAY       = 0.8   # 旧权重保留比例（指数平滑）
    UPDATE_FREQ = 20    # 每20次迭代更新一次权重

    for it in range(max_iter):

        # 4/2新增代码: 用轮盘赌替换原先的 random.choice，概率与权重成正比
        op_idx = _roulette_wheel(weights)
        uses[op_idx] += 1

        op = destroy_ops[op_idx]
        destroyed, removed = op(current)
        print(f'移除的大小{len(removed)}')

        # 4/2新增代码: 使用 Regret-2 + 分批插入修复算子
        candidate = repair_regret(destroyed, removed, layout)
        candidate.cost = evaluate_solution(candidate, layout)

        delta = candidate.cost - current.cost

        # 4/2新增代码: 根据接受结果更新算子得分
        if candidate.cost < best.cost:
            # 情形1：发现全局最优
            scores[op_idx] += SIGMA1           # 4/2新增代码
            current = candidate
            best = current.deepcopy()
            best.cost = current.cost
        elif delta < 0:
            # 情形2：产生改进解（局部更优）
            scores[op_idx] += SIGMA2           # 4/2新增代码
            current = candidate
        elif random.random() < math.exp(-delta / T):
            # 情形3：模拟退火接受劣解
            scores[op_idx] += SIGMA3           # 4/2新增代码
            current = candidate

        T *= 0.995

        # 4/2新增代码: 每 UPDATE_FREQ 次迭代用指数平滑更新算子权重
        if (it + 1) % UPDATE_FREQ == 0:
            for i in range(n_ops):
                if uses[i] > 0:
                    avg_score = scores[i] / uses[i]
                    # 指数平滑：保留DECAY比例旧权重，引入新得分
                    weights[i] = max(0.1, (1 - DECAY) * weights[i] + DECAY * avg_score)
                scores[i] = 0.0                # 4/2新增代码: 重置周期得分
                uses[i]   = 0                  # 4/2新增代码: 重置周期使用次数
            print(f"Iter {it+1}: 算子权重 = {[f'{w:.3f}' for w in weights]}")  # 4/2新增代码

        if it % 50 == 0:
            history.append(current.deepcopy())

        # 4/2新增：可视化触发 —— 每隔 save_interval 次迭代保存一张布局图
        if snapshot_callback and (it + 1) % save_interval == 0:
            snapshot_callback(current, it + 1, current.cost)

        if it % 20 == 0:
            print(f"Iter {it}, Best Cost: {best.cost:.2f}")
        print(current.cost, candidate.cost)

    return best, history
