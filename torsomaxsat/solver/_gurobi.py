from torsomaxsat import Solver, State

import gurobipy as gp
from gurobipy import GRB

class GurobiSolver(Solver):

    def solve(self):
   
        # hide Gurobi messages
        env = gp.Env(empty=True)
        env.setParam("OutputFlag",0)
        env.start()

        # build a Gurobi model
        gurobi = gp.Model(env=env)

        # improve integer variables
        gurobi.Params.IntFeasTol       = 1e-09
        gurobi.Params.IntegralityFocus = 1
        
        # adding the variables
        ilp_vars = [0]
        for i in range(1,self.wcnf.n+1):
            ilp_vars.append( gurobi.addVar(vtype = GRB.BINARY, name = format(f"x{i}")) )
        
        # adding the hard clauses
        for c in self.wcnf.hard:
            bound  = 1
            clause = []
            for l in c:
                if l < 0:
                    clause.append( -1*ilp_vars[abs(l)] )
                    bound -= 1
                else:
                    clause.append( ilp_vars[abs(l)] )
            gurobi.addConstr(gp.quicksum(clause) >= bound)

        # adding the soft clauses
        obj = []
        for v in self.wcnf.soft:
            obj.append( (ilp_vars[abs(v)], self.wcnf.soft[v]) )
        gurobi.setObjective(gp.quicksum( x*w for (x, w) in obj ), GRB.MAXIMIZE)
        
        # solving the model
        gurobi.optimize()

        # store computed results
        if gurobi.status == gp.GRB.OPTIMAL:
            self.fitness    = gurobi.objVal
            self.assignment = list(map(lambda v: int(v.X), ilp_vars[1:]))
            self.state      = State.OPTIMAL
        else:
            self.state = State.UNSAT
    
