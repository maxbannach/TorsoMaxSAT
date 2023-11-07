from torsomaxsat import Solver
from torsomaxsat import State

from ortools.sat.python import cp_model


import cylp

class CyLPSolver(Solver):

    def solve(self):

        cylp = CyClpSimplex()

        # Addding the variables.
        ilp_vars = [0]
        for i in range(1,self.wcnf.n+1):
            ilp_vars.append( cylp.addVariable(format(f"x{i}"), isInt=True) )

        # Adding the hard clauses.
        for c in self.wcnf.hard:
            bound        = 1
            coefficients = []
            variables    = []
            for l in c:
                variables.append(ilp_vars[abs(l)])
                if l < 0:
                    coefficents.append(-1)
                    clause.append( -1* )
                    bound  -= 1
                else:
                    coefficents.append(1)
            constraint = coefficients @ CyLPArray(variables)
            cylp += constraint >= bound

        cylp.solver = CyClpSimplex()
        cylp.solver.logLevel = 0
        cylp.optimize()

        print("Optimal solution:")
        for variable in all_variables:
            print(f"{variable.name} = {model.primalVariableSolution[variable.name]:.2f}")
        print(f"Objective value = {model.objectiveValue:.2f}")
        print()
        print()
            
