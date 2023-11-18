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

from ._utils           import BiMap
from ._wcnf            import WCNF
from ._torso           import Torso
from ._primalgraph     import PrimalGraph
from .solver           import Solver, State
from .solver._gurobi   import GurobiSolver
from .solver._scip     import ScipSolver
from .solver._rc2      import RC2Solver
from .solver._fm       import FMSolver
from .solver._ortools  import ORSolver
from .solver._dp       import DPSolver
from .solver._external import ExternalSolver
