from solution import Solution
from evaluate_solution import evaluate_solution
from delete import *
from insert import *
from layoutevaluator import *
import random
from alns import alns
#数据结构  堆场 {"车型": 数量}
def init_solution():
    sol = {
        0: {"SUV": 10, "Truck": 5},
        1: {"Sedan": 10, "Truck": 3, "SUV": 2},
        2: {"Truck": 5}
    }
    return Solution(sol)
# =============================
# 主程序
# =============================
if __name__ == "__main__":
    sol = init_solution()
    best = alns(sol, max_iter=300)
    print("\n最优解：")
    for yard, types in best.yards.items():
        print(f"堆场 {yard}: {types}")
    print("最优 cost:", best.cost)