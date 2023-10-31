from torsomaxsat import Solver

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
        fm.compute()
        model = fm.model

        # Store the result in the internal format.
        self.fitness    = self.wcnf._max_fitness() - fm.cost
        self.assignment = list(map(lambda l: 1 if l >= 0 else 0, model))            
