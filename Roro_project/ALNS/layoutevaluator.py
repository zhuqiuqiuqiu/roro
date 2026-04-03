import math
from data import yard_sizes, vehicle_info


class SkylineLayout:
    '''
    堆场布局评估器，
    使用Skyline算法评估车辆布局的成本和可行性
    '''
    def __init__(self, yard_sizes, vehicle_info):
        self.cache = {}
        self.yard_sizes = yard_sizes
        self.vehicle_info = vehicle_info

    def encode_key(self, yard_id, vehicles):
        return (yard_id, tuple(sorted(vehicles.items())))

    def evaluate(self, yard_id, vehicles):
        key = self.encode_key(yard_id, vehicles)

        if key in self.cache:
            return self.cache[key]

        cost, feasible, placements = self._layout(
            self.yard_sizes[yard_id], vehicles
        )

        self.cache[key] = (cost, feasible, placements)
        return cost, feasible, placements

    def _layout(self, yard_size, vehicles):
        W, H = yard_size

        rects = []

        # 4/2新增代码: 按实际数量q生成矩形，修复原先忽略车辆数量只生成2个的严重bug
        for t, q in vehicles.items():
            w, h = self.vehicle_info[t]
            for _ in range(q):
                rects.append((w, h, t))

        #  按面积排序（更稳定）
        rects.sort(key=lambda x: (-x[0]*x[1], -max(x[0], x[1])))

        skyline = [(0, 0, W)]  # (x, y, width)
        placements = []

        for rw, rh, t in rects:

            best_y = math.inf
            best_x = None
            best_idx = None

            for i in range(len(skyline)):
                x, y, avail_w = skyline[i]

                if avail_w >= rw:
                    max_y = y
                    width_left = rw
                    j = i

                    prev_x = x

                    while width_left > 0 and j < len(skyline):
                        sx, sy, sw = skyline[j]
                        # 检查是否连续
                        if sx != prev_x:
                            break
                        max_y = max(max_y, sy)
                        width_left -= sw
                        prev_x = sx + sw
                        j += 1

                    # ✅ 高度限制（必须）
                    if width_left <= 0 and max_y + rh <= H:
                        if max_y < best_y:
                            best_y = max_y
                            best_x = x
                            best_idx = i

            # ❗ 放不下 → 不可行
            if best_x is None:
                return 1e6, False, []

            # 插入
            self._add_skyline(skyline, best_idx, best_x, best_y, rw, rh)

            placements.append((best_x, best_y, rw, rh, t))

        # ===== 计算 cost =====
        used_area = sum(w * h for (_, _, w, h, _) in placements)
        total_area = W * H

        utilization = used_area / total_area

        # ===== 基础cost（越小越好）=====
        empty_area = total_area - used_area

        penalty = 0

        # 硬约束：超过95%视为物理不可行
        if utilization > 0.95:
            return 1e6, False, []
        # 4/2新增代码: 降低软约束阈值从0.9→0.85，过高利用率施加惩罚防止极度拥挤
        elif utilization > 0.85:
            penalty += (utilization - 0.85) * 5000

        cost = empty_area * 0.5 + penalty

        return cost, True, placements

    def _add_skyline(self, skyline, idx, x, y, w, h):
        skyline.insert(idx, (x, y + h, w))

        i = idx + 1
        while i < len(skyline):
            sx, sy, sw = skyline[i]
            px, py, pw = skyline[i - 1]

            if sx < px + pw:
                overlap = px + pw - sx
                if sw <= overlap:
                    skyline.pop(i)
                else:
                    skyline[i] = (sx + overlap, sy, sw - overlap)
                    break
            else:
                break

        i = 0
        while i < len(skyline) - 1:
            if skyline[i][1] == skyline[i + 1][1]:
                x1, y1, w1 = skyline[i]
                x2, y2, w2 = skyline[i + 1]
                skyline[i] = (x1, y1, w1 + w2)
                skyline.pop(i + 1)
            else:
                i += 1