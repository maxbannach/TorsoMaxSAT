import heapq

def solver_from_string(cmd, wcnf, preprocessor = None, twsolver = None, subsolver = None):
    if cmd is None or cmd == "rc2":
        solver = RC2Solver(wcnf,    preprocessor = preprocessor)        
    elif cmd == "gurobi":
        solver = GurobiSolver(wcnf, preprocessor = preprocessor)
    elif cmd == "scip":
        solver = ScipSolver(wcnf,   preprocessor = preprocessor)
    elif cmd == "hs":
        solver = HSSolver(wcnf,     preprocessor = preprocessor)
    elif cmd == "fm":
        solver = FMSolver(wcnf,     preprocessor = preprocessor)
    elif cmd == "ortools":
        solver = ORSolver(wcnf,     preprocessor = preprocessor)
    elif cmd == "dp":
        solver = VBSolver(wcnf,     preprocessor = preprocessor, subsolver = subsolver)
        solver.twsolver = twsolver
    elif cmd == "dpp":
        solver = DPSolver(wcnf,     preprocessor = preprocessor, subsolver = subsolver)
        solver.twsolver = twsolver
    else:
        solver = ExternalSolver(wcnf, cmd, preprocessor = preprocessor)
    return solver

def _neighbors_of_set_in(g, c, s):
    """
    Computes the neighbors of c in set s in g.
    """
    neighbors = set()
    for v in s:
        for w in g.neighbors(v):
            if w in c:
                neighbors.add(v)
    return neighbors

class PriorityQueue:
    """
    Max Priortiy Queue.
    """
    def __init__(self):
        self._queue = []
        self._index = 0 

    def push(self, item, priority):
        heapq.heappush(self._queue, (-priority, self._index, item))
        self._index += 1

    def pop(self):
        if not self.is_empty():
            priority, _, item = heapq.heappop(self._queue)
            return item, -priority 
        else:
            raise IndexError("pop from an empty priority queue")
        
    def is_empty(self):
        return not bool(self._queue)

    def __len__(self):
        return len(self._queue)
    
from ._utils           import BiMap
from ._wcnf            import WCNF
from ._torso           import Torso
from ._primalgraph     import PrimalGraph
from .solver           import Solver, State
from .solver._gurobi   import GurobiSolver
from .solver._scip     import ScipSolver
from .solver._rc2      import RC2Solver
from .solver._hs       import HSSolver
from .solver._fm       import FMSolver
from .solver._ortools  import ORSolver
from .solver._dp       import DPSolver
from .solver._vb       import VBSolver
from .solver._external import ExternalSolver
