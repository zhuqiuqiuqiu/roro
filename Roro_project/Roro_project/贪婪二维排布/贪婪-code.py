"""
最低水平线法（Skyline）多车型 - 多矩形堆场二维排布示例

说明：
- vehicle_types: 每项为 dict {'name','w','h','count'}
- containers: 每项为 dict {'name','W','H'}
- 算法：先按车型 count 降序；按容器面积降序依次填充。
- 放置策略：对于给定容器，从所有 skyline 起点扫描，寻找能放下且 resulting y 最低的位置，若并列取最左。
- skyline 用分段表示：一系列 (x, width, height) 隐式；查询区间 max height 时对分段遍历。
"""

import math
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple, defaultdict

Placement = namedtuple("Placement", ["container","name","x","y","w","h","instance_id"])

class SkylineContainer:
    def __init__(self, name, W, H):
        self.name = name
        self.W = W
        self.H = H
        # skyline 存为链表式分段：每一段 (x, width, height)
        # 初始为一段从 0 到 W，高度 0
        self.segs = [(0.0, W, 0.0)]

    def _segments_covering(self, x0, x1):
        """返回覆盖 [x0,x1) 的分段列表的索引与片段信息（部分重叠也作为片段）。
        假定 0<=x0<x1<=W"""
        res = []
        cur = 0.0
        for i, (sx, sw, sh) in enumerate(self.segs):
            sx_e = sx + sw
            if sx_e <= x0:
                continue
            if sx >= x1:
                break
            # 有交集
            res.append((i, (sx, sw, sh)))
        return res

    def _max_height_over(self, x0, x1):
        """返回区间 [x0,x1) 上 skyline 的最大高度"""
        maxh = 0.0
        for _, (sx, sw, sh) in self._segments_covering(x0, x1):
            maxh = max(maxh, sh)
        return maxh

    def _insert_skyline_segment(self, x0, x1, new_h):
        """在 [x0,x1) 区间上把 skyline 高度设置为 new_h（实际上为 max(existing, new_h)），并合并相邻同高段"""
        # 建立新的分段数组
        new_segs = []
        i = 0
        W = self.W
        while i < len(self.segs):
            sx, sw, sh = self.segs[i]
            sx_e = sx + sw
            if sx_e <= x0 or sx >= x1:
                # 完全在目标区间左边或右边，保留
                new_segs.append((sx, sw, sh))
                i += 1
                continue
            # 部分或全部重叠
            # 可能产生左边不重叠段
            if sx < x0:
                left_w = x0 - sx
                new_segs.append((sx, left_w, sh))
                sx = x0
                sw = sx_e - x0
            # 重叠部分
            overlap_w = min(x1, sx + sw) - sx
            # new height = max(sh, new_h)
            new_segs.append((sx, overlap_w, max(sh, new_h)))
            # 如果有右边不重叠，保留为后续处理（将修改当前 seg 的起点）
            right_start = sx + overlap_w
            right_end = sx + sw
            if right_start < right_end:
                # replace current seg with its right remainder by adjusting iteration:
                # we'll process the remainder by inserting a synthetic seg and continue
                # set up to continue from the remainder
                self.segs[i] = (right_start, right_end - right_start, sh)
                # do NOT increment i; next loop will handle this remainder
            else:
                i += 1
        # 合并相邻同高段，确保段连贯且覆盖 [0,W)
        merged = []
        for sx, sw, sh in new_segs:
            if not merged:
                merged.append([sx, sw, sh])
            else:
                px, pw, ph = merged[-1]
                if math.isclose(ph, sh, rel_tol=1e-9) and math.isclose(px + pw, sx, rel_tol=1e-9):
                    # 合并
                    merged[-1][1] += sw
                else:
                    merged.append([sx, sw, sh])
        # 有时候合并后第一段起点可能不是 0（数值误差或逻辑），修正并确保覆盖到 W
        # 如果第段起点 > 0，插入空白段高度为0
        if merged and merged[0][0] > 0:
            merged.insert(0, [0.0, merged[0][0], 0.0])
        # 最后确保覆盖到 W
        if merged:
            last_x_end = merged[-1][0] + merged[-1][1]
            if last_x_end < W - 1e-9:
                merged.append([last_x_end, W - last_x_end, 0.0])
        else:
            merged = [[0.0, W, 0.0]]
        # write back
        self.segs = [(float(x), float(w), float(h)) for x,w,h in merged]

    def try_place(self, w, h):
        """尝试在容器中放置一个尺寸为 w x h 的矩形。
        返回 (x,y) 放置坐标（左下角），或者 None 如果放不下。"""
        if w > self.W + 1e-9 or h > self.H + 1e-9:
            return None
        best = None  # (resulting_y, x)
        # 我们从每个 segment 的起点尝试（常见策略）
        for sx, sw, sh in self.segs:
            x_try = sx
            if x_try + w > self.W + 1e-9:
                continue
            # 计算区间 [x_try, x_try+w) 的最大高度
            maxh = self._max_height_over(x_try, x_try + w)
            if maxh + h <= self.H + 1e-9:
                # 可放，记录
                if best is None or (maxh < best[0] - 1e-9) or (abs(maxh - best[0]) < 1e-9 and x_try < best[1] - 1e-9):
                    best = (maxh, x_try)
        if best is None:
            return None
        y_place, x_place = best
        # 更新 skyline：在 [x_place, x_place+w) 上设置新高度为 y_place + h
        self._insert_skyline_segment(x_place, x_place + w, y_place + h)
        return (float(x_place), float(y_place))

def pack_vehicles_into_containers(vehicle_types, containers):
    """
    vehicle_types: list of dict {'name','w','h','count'}
    containers: list of dict {'name','W','H'}
    返回：placements 列表（Placement），以及未放下的实例数统计
    """
    # 排序：车型按数量降序
    vehicle_types_sorted = sorted(vehicle_types, key=lambda v: v['count'], reverse=True)
    # 容器按面积降序
    containers_sorted = sorted(containers, key=lambda c: c['W'] * c['H'], reverse=True)
    # 初始化 SkylineContainer
    skyline_containers = [SkylineContainer(c['name'], c['W'], c['H']) for c in containers_sorted]

    placements = []
    leftover = defaultdict(int)

    # 对每个车型，按照数量逐辆放入（也可一次性放置所有实例）
    for vt in vehicle_types_sorted:
        name = vt['name']
        w = float(vt['w'])
        h = float(vt['h'])
        cnt = int(vt['count'])
        placed = 0
        inst_id = 0
        for k in range(cnt):
            placed_flag = False
            # 对容器顺序尝试放入（最大面积优先）
            for sc in skyline_containers:
                pos = sc.try_place(w, h)
                if pos is not None:
                    x, y = pos
                    placements.append(Placement(container=sc.name, name=name, x=x, y=y, w=w, h=h, instance_id=inst_id))
                    placed = placed + 1
                    inst_id += 1
                    placed_flag = True
                    break
            if not placed_flag:
                leftover[name] += 1
                inst_id += 1
        # 下一车型
    return placements, leftover, skyline_containers

# --- 示例数据 ---
if __name__ == "__main__":
    # 定义若干车型（单位：米，示例）
    vehicle_types = [
        {'name': 'Sedan', 'w': 1.8, 'h': 4.6, 'count': 12},
        {'name': 'SUV',   'w': 2.2, 'h': 4.9, 'count': 9},
        {'name': 'Truck', 'w': 2.5, 'h': 10.0, 'count': 4},
        {'name': 'Van',   'w': 2.1, 'h': 5.2, 'count': 6},
        {'name': 'Mini',  'w': 1.6, 'h': 3.6, 'count': 15},
    ]

    # 定义堆场矩形（W 宽度为 x 方向，H 为 y 方向）
    containers = [
        {'name': 'Yard_A', 'W': 30.0, 'H': 12.0},   # largest area
        {'name': 'Yard_B', 'W': 20.0, 'H': 10.0},
        {'name': 'Yard_C', 'W': 10.0, 'H': 8.0},
    ]

    placements, leftover, scs = pack_vehicles_into_containers(vehicle_types, containers)
    # ---- 新增统计指标 ----
    yard_stats = {}

    for sc in scs:  # sc = SkylineContainer
        yard_name = sc.name
        W, H = sc.W, sc.H
        total_area = W * H

        # 找该堆场的所有放置记录
        plist = [p for p in placements if p.container == yard_name]

        # 不重复的车型数量
        unique_vehicle_types = set(p.name for p in plist)

        # 使用面积（车辆面积相加）
        used_area = sum(p.w * p.h for p in plist)

        yard_stats[yard_name] = {
            "unique_vehicle_types": len(unique_vehicle_types),
            "used_area_ratio": used_area / total_area if total_area > 0 else 0,
            "vehicle_count": len(plist),
            "used_area": used_area,
            "total_area": total_area,
        }

    # 打印结果
    print("\n------ 堆场统计结果 ------")
    for y, stat in yard_stats.items():
        print(f"堆场：{y}")
        print(f"  不重复车型数量：{stat['unique_vehicle_types']}")
        print(f"  车辆数量：{stat['vehicle_count']}")
        print(f"  使用面积：{stat['used_area']:.2f} / {stat['total_area']:.2f}")
        print(f"  面积利用率：{stat['used_area_ratio'] * 100:.2f}%")
        print()

    # 输出结果摘要
    print(f"总放置数: {len(placements)}")
    placed_by_type = defaultdict(int)
    for p in placements:
        placed_by_type[p.name] += 1
    print("按车型放置数量：")
    for t in vehicle_types:
        print(f"  {t['name']}: 放置 {placed_by_type[t['name']]} / {t['count']}")

    if leftover:
        print("未放下（剩余）：")
        for k,v in leftover.items():
            if v>0:
                print(f"  {k}: {v}")

    # 可视化：按容器分别绘图
    # 为清晰起见，把每个容器画在不同 subplot
    n = len(scs)
    fig_h = max(4, 3*n)
    fig, axes = plt.subplots(n, 1, figsize=(12, fig_h))
    if n == 1:
        axes = [axes]
    color_map = {}
    cmap = plt.get_cmap("tab20")
    # 给车型上色
    unique_names = list({p.name for p in placements})
    for i, nm in enumerate(unique_names):
        color_map[nm] = cmap(i % 20)

    for ax, sc in zip(axes, scs):
        ax.set_title(f"{sc.name} (W={sc.W}, H={sc.H})")
        ax.set_xlim(0, sc.W)
        ax.set_ylim(0, sc.H)
        ax.set_aspect('equal', adjustable='box')
        # 画出边框
        ax.plot([0, sc.W, sc.W, 0, 0], [0, 0, sc.H, sc.H, 0], '-k')
        # 画放置的矩形
        for p in placements:
            if p.container != sc.name:
                continue
            rect = plt.Rectangle((p.x, p.y), p.w, p.h, fill=True, edgecolor='k', alpha=0.8, facecolor=color_map.get(p.name, 'gray'))
            ax.add_patch(rect)
            ax.text(p.x + 0.02, p.y + 0.02, f"{p.name[:3]}#{p.instance_id}", fontsize=6, va='bottom', ha='left')
        # 画 skyline 线以辅助理解
        xs = []
        ys = []
        for sx, sw, sh in sc.segs:
            xs.append(sx)
            ys.append(sh)
            xs.append(sx + sw)
            ys.append(sh)
        if xs:
            ax.step(xs, ys, where='post', linestyle='--', color='gray')
    plt.tight_layout()
    plt.show()
