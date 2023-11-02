from torsomaxsat import Solver, State

from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

class RC2Solver(Solver):

    def solve(self):

        # Translate the torsomaxsat formula to a PySAT formula.
        phi = WCNF()
        for c in self.wcnf.hard:
            phi.append(c)
        for v in self.wcnf.soft:
            phi.append([v], weight = self.wcnf.soft[v])

        # Setup the RC2 solver and compute a model.
        rc2   = RC2(phi)
        model = rc2.compute()
        
        # Store the result in the internal format.
        if model:
            self.fitness    = self.wcnf._max_fitness() - rc2.cost
            self.assignment = list(map(lambda l: 1 if l >= 0 else 0, model))
            self.state      = State.OPTIMAL
        else:
            self.state = State.UNSAT
