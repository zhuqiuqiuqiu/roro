import math
from data import yard_sizes, vehicle_info
class SkylineLayout:
    '''
    堆场布局评估器，
    使用Skyline算法评估车辆布局的成本和可行性
    '''
    def __init__(self):
        self.cache = {}

    def encode_key(self, yard_id, vehicles):
        return (yard_id, tuple(sorted(vehicles.items())))

    def evaluate(self, yard_id, vehicles):
        key = self.encode_key(yard_id, vehicles)

        if key in self.cache:
            return self.cache[key]

        cost, feasible = self._layout(yard_sizes[yard_id], vehicles)

        self.cache[key] = (cost, feasible)
        return cost, feasible

    def _layout(self, yard_size, vehicles):
        W, H = yard_size

        rects = []
        for t, q in vehicles.items():
            w, h = vehicle_info[t]
            rects += [(w, h)] * q

        # 按高度排序（关键）
        rects.sort(key=lambda x: -x[1])

        skyline = [(0, 0, W)]  # (x, y, width)

        placements = []

        for rw, rh in rects:
            best_y = math.inf
            best_x = None
            best_idx = None

            for i in range(len(skyline)):
                x, y, avail_w = skyline[i]

                if avail_w >= rw:
                    max_y = y
                    width_left = rw
                    j = i

                    while width_left > 0 and j < len(skyline):
                        sx, sy, sw = skyline[j]
                        max_y = max(max_y, sy)
                        width_left -= sw
                        j += 1

                    if width_left <= 0 and max_y + rh <= H:
                        if max_y < best_y:
                            best_y = max_y
                            best_x = x
                            best_idx = i

            if best_x is None:
                return 1e6, False

            self._add_skyline(skyline, best_idx, best_x, best_y, rw, rh)
            placements.append((rw, rh))

        used_area = sum(w*h for (w, h) in placements)
        total_area = W * H

        return total_area - used_area, True

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