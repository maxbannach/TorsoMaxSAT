from enum import Enum

class Solver():

    def __init__(self, wcnf):
        self.wcnf       = wcnf  # The input formula (a torsomaxsat WCNF).
        self.fitness    = 0     # The value of the best model (after run solve).
        self.assignment = []    # An assignment (of the internal representation of) the wcnf after solver.
        self.state      = State.UNKNOWN
        
    def solve(self):
        pass

    def get_fitness(self):
        return self.fitness + self.wcnf.offset

    def get_cost(self):
        return self.wcnf._max_fitness() - self.fitness + self.wcnf.offset

class State(Enum):
    UNKNOWN = "UNKNOWN"
    UNSAT   = "UNSAT"
    OPTIMAL = "OPTIMAL"
    ERROR   = "ERROR"
