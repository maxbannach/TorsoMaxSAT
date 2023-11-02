from torsomaxsat import Solver, State

import pyscipopt as sp

class ScipSolver(Solver):

    def solve(self):
        # build a SCIP model
        scip = sp.Model()

        # adding the variables
        ilp_vars = [0]
        for i in range(1,self.wcnf.n+1):
            ilp_vars.append( scip.addVar(format(f"x{i}"), vtype = "BINARY") )
            
        # adding the hard clauses
        for c in self.wcnf.hard:
            bound  = 1
            clause = []
            for l in c:        
                if l < 0:
                    clause.append( -1*ilp_vars[abs(l)] )
                    bound  -= 1
                else:
                    clause.append( ilp_vars[abs(l)] )
            scip.addCons( sp.quicksum(l for l in clause) >= bound )

        # adding the soft clauses
        obj = []
        for v in self.wcnf.soft:
            obj.append( (ilp_vars[abs(v)],  self.wcnf.soft[v]) )
        scip.setObjective(sp.quicksum( x*w for (x,w) in obj ), "maximize")
            
        # solving the model
        scip.hideOutput()
        scip.optimize()
        
        # store computed results
        if scip.getStatus() == sp.SCIP_STATUS.OPTIMAL:
            self.fitness    = scip.getObjVal()
            self.assignment = list(map(lambda v: int(scip.getVal(v)), ilp_vars[1:]))
            self.state      = State.OPTIMAL
        else:
            self.state = State.UNSAT
