import sys, argparse, time


import pyscipopt as scip

# from pysat.formula import WCNF
# from pysat.examples.rc2 import RC2
# from pysat.examples.fm import FM

#import torsomaxsat
from torsomaxsat import WCNF
from torsomaxsat import GurobiSolver as Solver

__version__ = "0.0.1"
__author__ = "Max Bannach and Markus Hecher"

if __name__ == "__main__":

    # program info and argument parsing
    parser = argparse.ArgumentParser(description='A MaxSAT solver based on Tree Decompositions of the Torso Graph.')
    parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))
    parser.add_argument("-f", "--file", type=argparse.FileType("r"), default=sys.stdin, help="Input formula (as DIMACS2022 wcnf). Default is stdin.")

    # parse the arguments and map them to internal objects
    args  = parser.parse_args()
    input = args.file
    
    # print the header (very important)
    print(f"c\nc ------ TorsoMaxSAT v{__version__} ------")
    print(f"c\nc Authors: {__author__}\nc")

    # read the input formula (either from stdin or a file)
    phi = WCNF()
    for line in input:
        line = line.strip()
        if line and not line.startswith(('c', 'p')):
            w, c = line.split(" ")[0], [int(x) for x in line.split(" ")[1:-1]]
            if w == "h":
                phi.add_clause( c );
            else:
                phi.add_clause( c, weight = float(w) );


    print(repr(phi))
    print("--------")
                
    print(f"{phi}")

    solver = Solver(phi)
    solver.solve()
    print(f"Solver Fitness:    {solver.get_fitness()}")
    print(f"Solver Cost:       {solver.get_cost()}")
    print(f"Solver Assignment: {solver.assignment}")
    print( phi._to_external_model(solver.assignment) )
        
    # print(f"c parsing formula ...", end="")
    # tstart = time.time()
    # # parse a wcnf in dimacs2022 format
    # hard = []
    # soft = []
    # nv   = 0
    # for line in sys.stdin:
    #     line = line.strip() 
    #     if line and not line.startswith(('c', 'p')):
    #         ll = line.split(" ")[:-1]
    #         c  = [int(x) for x in ll[1:]]
    #         if max(map(abs, c)) > nv:
    #             nv += 1
    #         if ll[0] == "h":
    #             hard.append(c)
    #         else:
    #             w = float(ll[0])
    #             if w.is_integer():
    #                 w = int(w)
    #             soft.append( (c,w) )
                
    # # generate a wcnf with positive unit soft clauses
    # phi    = WCNF()
    # offset = 0
    # for c in hard:
    #     phi.append(c)
    # for (c,w) in soft:
    #     sign = 1
    #     if w < 0:
    #         offset +=  w
    #         w       = -w
    #         sign    = -1
    #     if len(c) >= 2:
    #         nv += 1
    #         c.append(nv)
    #         phi.append(c)
    #         phi.append([-nv*sign], weight = w)
    #     else:
    #         phi.append([c[0]*sign], weight = w)
    # print(f" {(time.time()-tstart):06.2f}s\nc")

    #
    # Run Gurobi
    #
    # tstart = time.time()
    # print(f"c running Gurobi  ...", end = "")
    # env = gp.Env(empty=True)
    # env.setParam("OutputFlag",0)
    # env.start()
    # gurobi = gp.Model(env=env)
    # ilp_vars = [0]
    # for i in range(1,phi.nv+1):
    #     ilp_vars.append( gurobi.addVar(vtype = GRB.BINARY, name = format(f"x{i}")) )
    # for c in phi.hard:
    #     bound  = 1
    #     clause = gp.LinExpr()
    #     for v in c:        
    #         if v < 0:
    #             clause += -1*ilp_vars[abs(v)]
    #             bound  -= 1
    #         else:
    #             clause += ilp_vars[abs(v)]
    #     gurobi.addConstr( clause >= bound )

    # gurobi_offset = 0
    # obj = gp.LinExpr()
    # for (i,v) in enumerate(phi.soft):
    #     v = v[0] # we have only unit soft clauses
    #     w = phi.wght[i]        
    #     if v < 0:
    #         obj += ilp_vars[abs(v)] * -w
    #         gurobi_offset += w
    #     else:
    #         obj += ilp_vars[abs(v)] * w

            
    # gurobi.setObjective(obj, GRB.MAXIMIZE)
    # gurobi.optimize()           
    # print(f" {(time.time()-tstart):06.2f}s")
    # print(f"c Optimal Solution: { gurobi.objVal + gurobi_offset + offset }\nc")

    # #
    # # Run Scip
    # #
    # tstart = time.time()
    # print(f"c running SCIP    ...", end = "")
    # scip_offset = 0
    # model       = scip.Model()
    # ilp_vars    = [0]
    # for i in range(1,phi.nv+1):
    #     ilp_vars.append( model.addVar(format(f"x{i}"), vtype = "BINARY") )
    # for c in phi.hard:
    #     bound  = 1
    #     clause = []
    #     for v in c:        
    #         if v < 0:
    #             clause.append( -1*ilp_vars[abs(v)] )
    #             bound  -= 1
    #         else:
    #             clause.append( ilp_vars[abs(v)] )
    #     model.addCons( scip.quicksum(l for l in clause) >= bound )
                
    # obj = []
    # for (i,v) in enumerate(phi.soft):
    #     v = v[0] # we have only unit soft clauses
    #     w = phi.wght[i]        
    #     if v < 0:
    #         obj.append( (ilp_vars[abs(v)], -w) )
    #         scip_offset += w
    #     else:
    #         obj.append( (ilp_vars[abs(v)],  w) )
    # model.setObjective(scip.quicksum( x*w for (x,w) in obj ), "maximize")    
    # model.hideOutput()
    # model.optimize()
    # print(f" {(time.time()-tstart):06.2f}s")
    # print(f"c Optimal Solution: { model.getObjVal() + scip_offset + offset }\nc")        
    
    # #
    # # Run RC2
    # #
    # tstart = time.time()
    # print(f"c running RC2     ...", end = "")
    # rc2 = RC2(phi)
    # model = rc2.compute()
    # print(f" {(time.time()-tstart):06.2f}s")
    # print(f"c Optimal Solution: {sum(phi.wght) - rc2.cost + offset}\nc")

    # #
    # # Run FM
    # #
    # tstart = time.time()
    # print(f"c running FM      ...", end = "")
    # fm = FM(phi, verbose=0)
    # fm.compute()
    # print(f" {(time.time()-tstart):06.2f}s")
    # print(f"c Optimal Solution: {sum(phi.wght) - fm.cost + offset}\nc")
