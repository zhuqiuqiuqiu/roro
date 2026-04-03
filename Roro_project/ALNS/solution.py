import copy

class Solution:
    def __init__(self, yards):
        self.yards = yards  # dict
        self.cost = None

    def deepcopy(self):
        new_sol = Solution(copy.deepcopy(self.yards))
        new_sol.cost = self.cost  #
        return new_sol