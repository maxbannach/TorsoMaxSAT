from torsomaxsat import Solver
from torsomaxsat import State

from ortools.sat.python import cp_model

from cylp.cy import CyClpSimplex

class CyLPSolver(Solver):

    def solve(self):

        # Build a ortools representation of the formula.
        phi  = cp_model.CpModel()
        vars = [0]
        for v in range(1,self.wcnf.n+1):
            vars.append( phi.NewBoolVar(format(f"x{v}")) )

        # Helper function to translate integers to variables.
        def int2var(x):
            return vars[x] if x > 0 else vars[abs(x)].Not()

        # Add the hard clauses.
        for c in self.wcnf.hard:
            phi.AddBoolOr(list(map(int2var, c)))

        # Add the soft clauses (as the objective function).
        soft = []
        for v in self.wcnf.soft:
            w = self.wcnf.soft[v]
            soft.append( (v,w) )
        phi.Maximize( sum(vars[abs(v)] * w for (v, w) in soft) )
        
        # Run the CP-Solver and obtain the status.
        solver = cp_model.CpSolver()
        status = solver.Solve(phi)                      

        # Store the result in the internal format.
        if status == cp_model.OPTIMAL:
            self.fitness    = solver.ObjectiveValue()
            self.assignment = [solver.Value(x) for x in vars[1:]]            
            self.state = State.OPTIMAL
        else:
            self.state = State.UNSAT
