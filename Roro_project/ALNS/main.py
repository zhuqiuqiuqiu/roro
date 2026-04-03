import matplotlib
matplotlib.use('Agg')   # 4/2新增：可视化触发 —— 使用非交互后端，plot_solution 静默保存不弹窗

from solution import Solution
from layoutevaluator import SkylineLayout
from alns import alns
from visualizer import plot_solution, make_gif  # 4/2新增：可视化触发
from data import yard_sizes, vehicle_info


# ─────────────────────────────────────────────────────────────────────────────
# 初始解生成
# ─────────────────────────────────────────────────────────────────────────────

def init_solution():
    # 4/2新增代码: 修改初始解为物理可行的分布
    # 原始解严重超容（Yard0需2059m²但只有800m²，总需求4116m²远超总容量2080m²）
    # 新初始解各堆场利用率约65-70%，为ALNS优化留出空间
    # 各堆场容量：Yard0=800m², Yard1=1200m², Yard2=80m²
    sol = {
        0: {"SUV": 30, "Sedan": 15, "Truck": 15},   # 约547m² / 800m²  ≈ 68%
        1: {"Sedan": 40, "Truck": 20, "SUV": 20},    # 约800m² / 1200m² ≈ 67%
        2: {"Truck": 6},                              # 约54m²  / 80m²   ≈ 67%
    }
    return Solution(sol)


# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    MAX_ITER    = 500
    SAVE_INTERVAL = 100                          # 4/2新增：可视化触发 —— 每50次迭代保存一张图
    OUTPUT_DIR  = "output_images"               # 4/2新增：可视化触发 —— 图片输出目录

    layout = SkylineLayout(yard_sizes, vehicle_info)
    sol    = init_solution()
    sol.cost = sum(
        layout.evaluate(yid, types)[0]
        for yid, types in sol.yards.items()
    )

    # 4/2新增：可视化触发 —— 保存初始解（Iteration 0）
    plot_solution(sol, layout, iteration=0, cost=sol.cost, output_dir=OUTPUT_DIR)

    # 4/2新增：可视化触发 —— 定义回调，每隔 SAVE_INTERVAL 次迭代由 alns() 调用
    def _snapshot(solution, iteration, cost):
        plot_solution(solution, layout, iteration=iteration,
                      cost=cost, output_dir=OUTPUT_DIR)

    best, history = alns(
        sol, layout,
        max_iter=MAX_ITER,
        snapshot_callback=_snapshot,        # 4/2新增：可视化触发
        save_interval=SAVE_INTERVAL         # 4/2新增：可视化触发
    )

    # 4/2新增：可视化触发 —— 保存最终最优解
    plot_solution(best, layout, iteration=MAX_ITER,
                  cost=best.cost, output_dir=OUTPUT_DIR)

    # 4/2新增：可视化触发 —— 生成 GIF 动图
    make_gif(
        output_dir=OUTPUT_DIR,
        gif_path="optimization_process.gif",
        duration=0.5
    )

    # ── 控制台输出最优解 ──────────────────────────────────────────────────────
    print("\n最优解：")
    for yard, types in best.yards.items():
        W, H = yard_sizes[yard]
        used = sum(
            vehicle_info[t][0] * vehicle_info[t][1] * q
            for t, q in types.items() if t in vehicle_info
        )
        util = used / (W * H) * 100
        print(f"  堆场 {yard} ({W}×{H}m²): {types}  利用率={util:.1f}%")
    print(f"最优 cost: {best.cost:.2f}")
