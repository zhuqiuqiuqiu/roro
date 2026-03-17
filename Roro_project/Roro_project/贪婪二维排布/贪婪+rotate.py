
import math
import csv
from collections import namedtuple, defaultdict
import numpy as np
import matplotlib.pyplot as plt

Placement = namedtuple("Placement", ["container","name","x","y","w","h","instance_id","rotated"])

class SkylineContainer:
    def __init__(self, name, W, H):
        self.name = name
        self.W = float(W)
        self.H = float(H)
        # segments stored as list of (x, width, height), covering [0,W)
        self.segs = [(0.0, float(W), 0.0)]

    def _segments_covering(self, x0, x1):
        res = []
        for i, (sx, sw, sh) in enumerate(self.segs):
            sx_e = sx + sw
            if sx_e <= x0:
                continue
            if sx >= x1:
                break
            res.append((i, (sx, sw, sh)))
        return res

    def _max_height_over(self, x0, x1):
        maxh = 0.0
        for _, (sx, sw, sh) in self._segments_covering(x0, x1):
            if sh > maxh:
                maxh = sh
        return maxh

    def _insert_skyline_segment(self, x0, x1, new_h):
        """在 [x0,x1) 上把高度提升为 max(existing, new_h)，并合并相邻相同高度段。"""
        new_segs = []
        i = 0
        # iterate original segments and build new list
        while i < len(self.segs):
            sx, sw, sh = self.segs[i]
            sx_e = sx + sw
            if sx_e <= x0 or sx >= x1:
                # no overlap
                new_segs.append((sx, sw, sh))
                i += 1
                continue
            # overlapping
            if sx < x0:
                # left remainder
                left_w = x0 - sx
                new_segs.append((sx, left_w, sh))
                sx = x0
                sw = sx_e - x0
            # now sx >= x0
            overlap_w = min(x1, sx + sw) - sx
            new_segs.append((sx, overlap_w, max(sh, new_h)))
            right_start = sx + overlap_w
            right_end = sx + sw
            if right_start < right_end:
                # replace current segment with remainder and continue processing it
                self.segs[i] = (right_start, right_end - right_start, sh)
                # do not increment i
            else:
                i += 1

        # merge adjacent same-height segments and ensure coverage
        merged = []
        for sx, sw, sh in new_segs:
            if not merged:
                merged.append([sx, sw, sh])
            else:
                px, pw, ph = merged[-1]
                if math.isclose(ph, sh, rel_tol=1e-9) and math.isclose(px + pw, sx, rel_tol=1e-9):
                    merged[-1][1] += sw
                else:
                    merged.append([sx, sw, sh])

        if merged and merged[0][0] > 0:
            merged.insert(0, [0.0, merged[0][0], 0.0])
        if merged:
            last_x_end = merged[-1][0] + merged[-1][1]
            if last_x_end < self.W - 1e-9:
                merged.append([last_x_end, self.W - last_x_end, 0.0])
        else:
            merged = [[0.0, self.W, 0.0]]

        self.segs = [(float(x), float(w), float(h)) for x,w,h in merged]

    def _try_place_single_direction(self, w, h):
        """尝试某一方向 (w,h)，返回最佳 (x,y) 或 None"""
        best = None
        for sx, sw, sh in self.segs:
            x_try = sx
            if x_try + w > self.W + 1e-9:
                continue
            maxh = self._max_height_over(x_try, x_try + w)
            if maxh + h <= self.H + 1e-9:
                if best is None or (maxh < best[1] - 1e-9) or (abs(maxh - best[1]) < 1e-9 and x_try < best[0] - 1e-9):
                    best = (x_try, maxh)
        return best

    def try_place(self, w, h, allow_rotate=True):
        """
        尝试放置 (w,h)。如果 allow_rotate=True，会在不成功时尝试 (h,w)。
        返回 (x, y, used_w, used_h, rotated_flag) 或 None。
        """
        orientations = [(w, h)]
        if allow_rotate and not math.isclose(w, h, rel_tol=1e-9):
            orientations.append((h, w))

        best_result = None  # (x, y, used_w, used_h, rotated)
        for idx, (ow, oh) in enumerate(orientations):
            if ow > self.W + 1e-9 or oh > self.H + 1e-9:
                continue
            candidate = self._try_place_single_direction(ow, oh)
            if candidate is None:
                continue
            x_try, y_try = candidate
            rotated = (idx == 1)
            if best_result is None or (y_try < best_result[1] - 1e-9) or (abs(y_try - best_result[1]) < 1e-9 and x_try < best_result[0] - 1e-9):
                best_result = (x_try, y_try, ow, oh, rotated)

        if best_result is None:
            return None
        x, y, ow, oh, rotated = best_result
        # update skyline
        self._insert_skyline_segment(x, x + ow, y + oh)
        return (float(x), float(y), float(ow), float(oh), bool(rotated))

def pack_vehicles_into_containers(vehicle_types, containers, allow_rotate_global=True):
    """
    vehicle_types: list of dict {'name','w','h','count'}
    containers: list of dict {'name','W','H'}
    返回 placements 列表 和 leftover dict 及 containers skyline 对象
    """
    # 车型按数量降序
    vehicle_types_sorted = sorted(vehicle_types, key=lambda v: v['count'], reverse=True)
    # 容器按面积降序
    containers_sorted = sorted(containers, key=lambda c: c['W'] * c['H'], reverse=True)
    skyline_containers = [SkylineContainer(c['name'], c['W'], c['H']) for c in containers_sorted]

    placements = []
    leftover = defaultdict(int)

    for vt in vehicle_types_sorted:
        name = vt['name']
        w = float(vt['w'])
        h = float(vt['h'])
        cnt = int(vt['count'])
        inst_id = 0
        for k in range(cnt):
            placed_flag = False
            for sc in skyline_containers:
                pos = sc.try_place(w, h, allow_rotate=allow_rotate_global)
                if pos is not None:
                    x, y, used_w, used_h, rotated = pos
                    placements.append(Placement(container=sc.name, name=name, x=x, y=y, w=used_w, h=used_h, instance_id=inst_id, rotated=rotated))
                    placed_flag = True
                    inst_id += 1
                    break
            if not placed_flag:
                leftover[name] += 1
                inst_id += 1

    return placements, leftover, skyline_containers

def compute_yard_stats(placements, skyline_containers):
    yard_stats = {}
    for sc in skyline_containers:
        yard_name = sc.name
        W, H = sc.W, sc.H
        total_area = W * H
        plist = [p for p in placements if p.container == yard_name]
        unique_vehicle_types = set(p.name for p in plist)
        used_area = sum(p.w * p.h for p in plist)
        yard_stats[yard_name] = {
            "unique_vehicle_types": len(unique_vehicle_types),
            "used_area_ratio": (used_area / total_area) if total_area > 0 else 0.0,
            "vehicle_count": len(plist),
            "used_area": used_area,
            "total_area": total_area,
        }
    return yard_stats

def save_placements_to_csv(placements, filepath="placements.csv"):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["container","name","instance_id","x","y","w","h","rotated"])
        for p in placements:
            writer.writerow([p.container, p.name, p.instance_id, f"{p.x:.4f}", f"{p.y:.4f}", f"{p.w:.4f}", f"{p.h:.4f}", int(p.rotated)])
    print(f"[INFO] placements saved to {filepath}")

def visualize(placements, skyline_containers, figsize=(12, 3)):
    n = len(skyline_containers)
    fig_h = max(3, 3*n)
    fig, axes = plt.subplots(n, 1, figsize=(12, fig_h))
    if n == 1:
        axes = [axes]
    cmap = plt.get_cmap("tab20")
    unique_names = list({p.name for p in placements})
    color_map = {nm: cmap(i % 20) for i, nm in enumerate(unique_names)}

    for ax, sc in zip(axes, skyline_containers):
        ax.set_title(f"{sc.name} (W={sc.W}, H={sc.H})")
        ax.set_xlim(0, sc.W)
        ax.set_ylim(0, sc.H)
        ax.set_aspect('equal', adjustable='box')
        ax.plot([0, sc.W, sc.W, 0, 0], [0, 0, sc.H, sc.H, 0], '-k')
        # draw placements
        for p in placements:
            if p.container != sc.name:
                continue
            rect = plt.Rectangle((p.x, p.y), p.w, p.h, fill=True, edgecolor='k', alpha=0.85, facecolor=color_map.get(p.name, 'gray'))
            ax.add_patch(rect)
            label = f"{p.name[:6]}#{p.instance_id}"
            ax.text(p.x + 0.02, p.y + 0.02, label, fontsize=6, va='bottom', ha='left')
            # annotate size and rotated
            ax.text(p.x + p.w/2, p.y + p.h/2, f"{p.w:.1f}×{p.h:.1f}" + (" R" if p.rotated else ""), fontsize=6, va='center', ha='center')
        # draw skyline steps
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

# -------------------------
# 示例数据与运行
# -------------------------
if __name__ == "__main__":
    # 车辆类型示例（单位：米），name, width(x方向), height(y方向), count
    # vehicle_types = [
    #     {'name': 'Mini',  'w': 1.6, 'h': 3.6, 'count': 15},
    #     {'name': 'Sedan', 'w': 1.8, 'h': 4.6, 'count': 12},
    #     {'name': 'SUV',   'w': 2.0, 'h': 4.9, 'count': 9},
    #     {'name': 'Van',   'w': 2.1, 'h': 5.2, 'count': 6},
    #     {'name': 'Truck', 'w': 2.5, 'h': 10.0, 'count': 4},
    # ]
    # 堆场矩形（W为x方向，H为y方向）
    # containers = [
    #     {'name': 'Yard_A', 'W': 30.0, 'H': 12.0},
    #     {'name': 'Yard_B', 'W': 20.0, 'H': 10.0},
    #     {'name': 'Yard_C', 'W': 10.0, 'H': 8.0},
    # ]
    ####-----------------------------    测试gurobi的模型案例
    containers = [
        {'name': 'Yard_A', 'W': 20.0, 'H': 30.0},
        {'name': 'Yard_B', 'W': 16.0, 'H': 30.0},
        {'name': 'Yard_C', 'W': 22.0, 'H': 30.0},
    ]
    vehicle_types = [
        {'name': 'Mini',  'w': 2.2, 'h': 5, 'count': 19},
        {'name': 'Sedan', 'w': 2, 'h': 3, 'count': 20},
        {'name': 'SUV',   'w': 1.9, 'h': 4.5, 'count': 9},
        {'name': 'dazong', 'w': 2.1, 'h': 4, 'count': 42},
    ]
    allow_rotate_global = True  # 全局开关：是否允许旋转尝试

    placements, leftover, scs = pack_vehicles_into_containers(vehicle_types, containers, allow_rotate_global)

    # 输出 summary
    print(f"Total placed: {len(placements)}")
    placed_by_type = defaultdict(int)
    for p in placements:
        placed_by_type[p.name] += 1
    print("Placed by vehicle type:")
    for t in vehicle_types:
        print(f"  {t['name']}: placed {placed_by_type[t['name']]} / {t['count']}")
    if leftover:
        print("Leftover (not placed):")
        for k,v in leftover.items():
            if v>0:
                print(f"  {k}: {v}")

    # 统计每个堆场指标
    yard_stats = compute_yard_stats(placements, scs)
    print("\n------ Yard Stats ------")
    for y, stat in yard_stats.items():
        print(f"Yard: {y}")
        print(f"  Unique vehicle types: {stat['unique_vehicle_types']}")
        print(f"  Vehicle count: {stat['vehicle_count']}")
        print(f"  Used area: {stat['used_area']:.2f} / {stat['total_area']:.2f}")
        print(f"  Utilization: {stat['used_area_ratio']*100:.2f}%\n")

    # 保存放置结果到 CSV（可选）
    save_placements_to_csv(placements, filepath="Greedy_placements.csv")

    # 可视化
    visualize(placements, scs)
