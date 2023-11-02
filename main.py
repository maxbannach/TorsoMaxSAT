import sys, argparse, time

from torsomaxsat import WCNF
from torsomaxsat import PrimalGraph
from torsomaxsat import GurobiSolver
from torsomaxsat import ScipSolver
from torsomaxsat import RC2Solver
from torsomaxsat import FMSolver
from torsomaxsat import ORSolver
from torsomaxsat import DPSolver

__version__ = "0.0.1"
__author__  = "Max Bannach and Markus Hecher"

if __name__ == "__main__":

    # Program info and argument parsing.
    parser = argparse.ArgumentParser(description='A MaxSAT solver based on Tree Decompositions of the Torso Graph.')
    parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))
    parser.add_argument("-s", "--solver", choices=["gurobi", "scip", "rc2", "fm", "ortools", "dp"], help="Base solvered used.", default="rc2")
    parser.add_argument("-f", "--file", type=argparse.FileType("r"), default=sys.stdin, help="Input formula (as DIMACS2022 wcnf). Default is stdin.")
    parser.add_argument('-p', '--primal',  action='store_true', help='Just output the primal graph of the instance.')
    parser.add_argument('-d', '--display', action='store_true', help='Just produces a visual display of the instance.')
    
    # Parse the arguments and map them to internal objects.
    args  = parser.parse_args()
    input = args.file
    
    # Print the header (very important).
    print(f"c\nc ------------ TorsoMaxSAT v{__version__} ------------")
    print(f"c\nc Authors: {__author__}\nc")    
    
    # Read the input formula (either from stdin or a file).
    tstart = time.time()
    print(f"c parsing input formula ...", end = "")
    phi = WCNF()
    for line in input:
        line = line.strip()
        if line and not line.startswith(('c', 'p')):
            w, c = line.split(" ")[0], [int(x) for x in line.split(" ")[1:-1]]
            if w == "h":
                phi.add_clause( c );
            else:
                phi.add_clause( c, weight = float(w) );
    print(f" {(time.time()-tstart):06.2f}s")
    print(f"c after translating to internal format:")
    print(f"c variables:    {phi.n}")
    print(f"c hard clauses: {len(phi.hard)}")
    print(f"c soft clauses: {len(phi.soft)}")
    print("c")

    # Auxillary modes.
    if args.primal:
        g = PrimalGraph(phi, external = True)
        print(g)
        sys.exit(0)

    # Auxillary modes.
    if args.display:
        g = PrimalGraph(phi, external = True)
        g.display()
        sys.exit(0)
        
    # Initialize the selected solver.
    if args.solver == "gurobi":
        solver = GurobiSolver(phi)
    elif args.solver == "scip":
        solver = ScipSolver(phi)
    elif args.solver == "rc2":
        solver = RC2Solver(phi)
    elif args.solver == "fm":
        solver = FMSolver(phi)
    elif args.solver == "ortools":
        solver = ORSolver(phi)
    elif args.solver == "dp":
        solver = DPSolver(phi)

    # Solve the instance.
    tstart = time.time()
    print(f"c running {args.solver}        ...", end = "")
    solver.solve()
    print(f" {(time.time()-tstart):06.2f}s")
    
    # Report the results.
    print(f"c Fitness:    {solver.get_fitness()}")
    print(f"c Cost:       {solver.get_cost()}")
    print("c")

    # MSE output.
    print("s OPTIMUM FOUND")
    print(f"o {solver.get_cost()}")
    for (i,l) in enumerate( phi._to_external_model(solver.assignment) ):
        if i % 25 == 0:
            if i > 0:
                print()
            print("v", end="")
        print(f" {l}", end="")
    print()
