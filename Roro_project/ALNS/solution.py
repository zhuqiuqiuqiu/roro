import copy

class Solution:
    def __init__(self, yards):
        self.yards = yards  # dict
        self.cost = None

    def deepcopy(self):
        return Solution(copy.deepcopy(self.yards))