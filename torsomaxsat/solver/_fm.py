from torsomaxsat import Solver, State

from pysat.formula import WCNF
from pysat.examples.fm import FM

class FMSolver(Solver):

    def solve(self):

        # Translate the torsomaxsat formula to a PySAT formula.
        phi = WCNF()
        for c in self.wcnf.hard:
            phi.append(c)
        for v in self.wcnf.soft:
            phi.append([v], weight = self.wcnf.soft[v])

        # Setup the FM solver and compute a model.
        fm    = FM(phi, verbose=0)
        state = fm.compute()

        # Store the result in the internal format.
        if state:
            model           = fm.model
            self.fitness    = self.wcnf._max_fitness() - fm.cost
            self.assignment = list(map(lambda l: 1 if l >= 0 else 0, model))
            self.state      = State.OPTIMAL
        else:
            self.state = State.UNSAT
