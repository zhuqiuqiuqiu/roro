"""
visualizer.py — ALNS 二维布局可视化模块
=========================================
提供两个公开函数：
  - plot_solution(solution, evaluator, iteration, cost, output_dir)
      静默保存当前解的二维布局到 output_dir/iter_XXX.png，绝不调用 plt.show()。
  - make_gif(output_dir, gif_path, duration)
      将所有 iter_*.png 串联成 GIF 动图。
"""

import os
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle


# ── 颜色配置 ─────────────────────────────────────────────────────────────────
VEHICLE_COLORS = {
    'SEAL U': '#4C72B0',
    'G13': '#55A868',
    'EV3': '#C44E52',
    'EV ': '#C44E52',
    'NIRO': '#4C72B0',
    'PICANTO': '#55A868',
    'SELTOS': '#4C72B0',
    'STONIC': '#4C72B0',
}
_EXTRA_COLORS = ["#64B5CD", "#E07B54", "#A2B9BC", "#B0C4DE", "#F0C27F"]


def _get_color(vtype, dynamic_colors):
    """返回车型对应颜色，未预定义车型自动分配备用颜色。"""
    if vtype in VEHICLE_COLORS:
        return VEHICLE_COLORS[vtype]
    if vtype not in dynamic_colors:
        idx = len(dynamic_colors) % len(_EXTRA_COLORS)
        dynamic_colors[vtype] = _EXTRA_COLORS[idx]
    return dynamic_colors[vtype]


# ── 核心绘图函数 ──────────────────────────────────────────────────────────────

def plot_solution(solution, evaluator, iteration, cost, output_dir="output_images"):
    """
    将当前 ALNS 解的二维布局静默保存为 PNG。

    参数：
        solution    : Solution 对象（含 yards 字典）
        evaluator   : SkylineLayout 对象（含 yard_sizes / vehicle_info）
        iteration   : 当前迭代编号（用于文件名与标题）
        cost        : 当前 total cost
        output_dir  : 图片输出目录（自动创建）
    """
    os.makedirs(output_dir, exist_ok=True)

    # 只展示分配了车辆的堆场
    active_yards = [
        (yid, types)
        for yid, types in sorted(solution.yards.items())
        if types
    ]
    if not active_yards:
        return

    n = len(active_yards)
    yard_widths  = [evaluator.yard_sizes[yid][0] for yid, _ in active_yards]
    yard_heights = [evaluator.yard_sizes[yid][1] for yid, _ in active_yards]

    # 图宽按各堆场实际宽度比例分配（每米 ≈ 0.07 英寸）
    SCALE = 0.07
    fig_width  = max(10, sum(w * SCALE for w in yard_widths) + 2 * n)
    fig_height = max(4,  max(yard_heights) * SCALE * 6 + 2.5)

    fig, axes = plt.subplots(
        1, n,
        figsize=(fig_width, fig_height),
        gridspec_kw={"width_ratios": yard_widths}
    )
    if n == 1:
        axes = [axes]

    dynamic_colors = {}   # 动态颜色映射（应对未预定义车型）

    for ax, (yard_id, types) in zip(axes, active_yards):
        W, H = evaluator.yard_sizes[yard_id]
        _, feasible, placements = evaluator.evaluate(yard_id, types)

        ax.set_xlim(0, W)
        ax.set_ylim(0, H)
        ax.invert_yaxis()   # y=0 对应顶部（与 Skyline 放置方向一致）

        # ── 堆场底色与边框 ───────────────────────────────────────────────────
        ax.add_patch(Rectangle((0, 0), W, H, linewidth=0, facecolor="#F8F8F0"))
        ax.add_patch(Rectangle((0, 0), W, H, linewidth=2,
                               edgecolor="#222222", facecolor="none"))

        # ── 绘制车辆矩形 ──────────────────────────────────────────────────────
        used_area = 0
        legend_handles = {}

        for (x, y, w, h, t) in placements:
            color = _get_color(t, dynamic_colors)
            ax.add_patch(Rectangle(
                (x, y), w, h,
                linewidth=0.4,
                edgecolor="black",
                facecolor=color,
                alpha=0.85
            ))
            used_area += w * h
            if t not in legend_handles:
                legend_handles[t] = mpatches.Patch(
                    facecolor=color, edgecolor="black",
                    linewidth=0.6, label=t
                )

        # ── 子图标题：堆场ID + 利用率 ─────────────────────────────────────────
        util_pct   = used_area / (W * H) * 100
        warn_str   = "  ⚠ INFEASIBLE" if not feasible else ""
        ax.set_title(
            f"Yard {yard_id}  —  Utilization: {util_pct:.1f}%{warn_str}",
            fontsize=9, pad=5
        )
        ax.set_xlabel("Width (m)", fontsize=7)
        ax.set_ylabel("Depth (m)", fontsize=7)
        ax.tick_params(labelsize=6)

        # ── 图例（每个子图独立） ──────────────────────────────────────────────
        if legend_handles:
            ax.legend(
                handles=list(legend_handles.values()),
                loc="lower right", fontsize=6.5,
                framealpha=0.75, borderpad=0.4, handlelength=1.0
            )

    # ── 总标题 ───────────────────────────────────────────────────────────────
    fig.suptitle(
        f"Iteration: {iteration}   |   Total Cost: {cost:.2f}",
        fontsize=11, fontweight="bold", y=1.02
    )
    plt.tight_layout()

    filename = os.path.join(output_dir, f"iter_{iteration:03d}.png")
    plt.savefig(filename, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visualizer] Saved → {filename}")


# ── GIF 生成 ──────────────────────────────────────────────────────────────────

def make_gif(output_dir="output_images",
             gif_path="optimization_process.gif",
             duration=0.5):
    """
    将 output_dir 下所有 iter_*.png 文件按迭代顺序串联为 GIF。

    优先使用 imageio；若未安装则自动回退到 Pillow。
    安装命令：pip install imageio   或   pip install Pillow
    """
    png_files = sorted(
        glob.glob(os.path.join(output_dir, "iter_*.png")),
        key=lambda p: int(os.path.splitext(os.path.basename(p))[0].split("_")[1])
    )
    if not png_files:
        print("[Visualizer] 未找到 iter_*.png 文件，跳过 GIF 生成")
        return

    # ── 方案 A：imageio ───────────────────────────────────────────────────────
    # try:
    #     import imageio
    #     images = [imageio.imread(f) for f in png_files]
    #     imageio.mimsave(gif_path, images, duration=duration)
    #     print(f"[Visualizer] GIF saved → {gif_path}  ({len(images)} frames, {duration}s/frame)")
    #     return
    # except ImportError:
    #     pass

    # ── 方案 B：Pillow ────────────────────────────────────────────────────────
    try:
        from PIL import Image
        frames = [Image.open(f).copy() for f in png_files]
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=int(duration * 1000),
            loop=0
        )
        print(f"[Visualizer] GIF saved → {gif_path}  ({len(frames)} frames, {duration}s/frame)")
        return
    except ImportError:
        pass

    print("[Visualizer] ⚠ 无法生成 GIF：请安装 imageio 或 Pillow")
    print("             pip install imageio    或    pip install Pillow")
