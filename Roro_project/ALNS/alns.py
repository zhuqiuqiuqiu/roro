import math
from insert import *
from delete import *
from evaluate_solution import *

def alns(initial_solution, evaluator, max_iter=1000):
    current = initial_solution
    current.cost = evaluate_solution(current, evaluator)
    best = current.deepcopy()
    best.cost = current.cost
    T = 1000  # 初始温度
    for it in range(max_iter):
        # ---- 破坏 ----
        destroyed, removed = remove_by_type(current)
        # ---- 修复 ----
        candidate = insert_greedy(destroyed, removed, evaluator)
        candidate.cost = evaluate_solution(candidate, evaluator)
        # ---- 接受准则（模拟退火）----
        delta = candidate.cost - current.cost
        if delta < 0 or random.random() < math.exp(-delta / T):
            current = candidate
        # 更新最优
        if current.cost < best.cost:
            best = current.deepcopy()
            best.cost = current.cost
        # 降温
        T *= 0.995
        if it % 50 == 0:
            print(f"Iter {it}, Best Cost: {best.cost}")
    return best