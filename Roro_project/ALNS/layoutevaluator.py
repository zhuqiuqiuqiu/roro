class LayoutEvaluator:
    def __init__(self):
        self.cache = {}

    def encode_key(self, yard_id, type_dict):
        # 转成可hash key（排序很关键！）
        return (yard_id, tuple(sorted(type_dict.items())))

    def evaluate(self, yard_id, type_dict):
        key = self.encode_key(yard_id, type_dict)

        if key in self.cache:
            return self.cache[key]

        # 👉 这里调用你的“最低水平线法”
        cost, feasible = self.lowest_skyline_layout(yard_id, type_dict)

        self.cache[key] = (cost, feasible)
        return cost, feasible

    def lowest_skyline_layout(self, yard_id, type_dict):
        """
        这里你替换成自己的布局算法
        返回：
            cost: float
            feasible: bool
        """
        # 示例（你要换掉）
        total = sum(type_dict.values())
        cost = total * 10
        feasible = True if total < 100 else False

        return cost, feasible