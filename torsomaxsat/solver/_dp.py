from torsomaxsat import Solver
from torsomaxsat import PrimalGraph

class DPSolver(Solver):

    def solve(self):

        # compute a tree decomposition
        g = PrimalGraph(self.wcnf, twsolver = self.twsolver)
        width, td = g.compute_tree_decomposition(heuristic="fillin")

        # execute the dp

        # ...
        
        # Store the result in the internal format.
        self.fitness    = 0
        self.assignment = [0]*self.wcnf.n
