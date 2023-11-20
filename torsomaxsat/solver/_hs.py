from torsomaxsat import Solver, State

from pysat.formula         import WCNF
from pysat.examples.hitman import Hitman
from pysat.solvers         import Solver as SatSolver

class HSSolver(Solver):

    def solve(self):

        # Translate the torsomaxsat formula to a PySAT formula.
        phi = WCNF()
        for c in self.wcnf.hard:
            phi.append(c)
        for v in self.wcnf.soft:
            phi.append([v], weight = self.wcnf.soft[v])

        # Setup a hitting set solver and a sat solver.
        hitman = Hitman(htype="maxsat")
        solver = SatSolver(name='g3', bootstrap_with = phi.hard )

        # Perform the MaxHS like algorithm.
        hitting_set = None 
        while True:
            hitting_set = set( hitman.get() )
            not_blocked = set(self.wcnf.soft.keys()).difference(hitting_set)

            if solver.solve( assumptions = list(not_blocked) ):
                break
            else:
                core = solver.get_core()
                if core is None:
                    break
                hitman.hit(core, self.wcnf.soft)
            
        # Store the result in the internal format.
        model = solver.get_model()
        if model:
            self.state      = State.OPTIMAL
            self.assignment = list(map(lambda l: 1 if l >= 0 else 0, model))            
            self.fitness    = sum(
                map(
                    lambda v: self.wcnf.soft[v],
                    filter( lambda v: self.assignment[v-1] == 1, self.wcnf.soft.keys() )
                )
            )            
        else:
            self.state = State.UNSAT

