import sys, argparse, time

from torsomaxsat import WCNF
from torsomaxsat import PrimalGraph
from torsomaxsat import State
from torsomaxsat import GurobiSolver
from torsomaxsat import ScipSolver
from torsomaxsat import RC2Solver
from torsomaxsat import FMSolver
from torsomaxsat import ORSolver
from torsomaxsat import DPSolver
from torsomaxsat import ExternalSolver

__version__ = "0.0.1"
__author__  = "Max Bannach and Markus Hecher"

if __name__ == "__main__":

    # Program info and argument parsing.
    parser = argparse.ArgumentParser(description='A MaxSAT solver based on Tree Decompositions of the Torso Graph.')
    parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))
    parser.add_argument("-s", "--solver", choices=["gurobi", "scip", "rc2", "fm", "ortools", "dp", "external"], help="Base solvere used.", default="rc2")
    parser.add_argument("--externalsolver", help="Command to execute an external solver.")
    parser.add_argument("-t", "--twsolver", help="Command to execute an external treewidth solver (PACE compatible).")
    parser.add_argument("-f", "--file", type=argparse.FileType("r"), default=sys.stdin, help="Input formula (as DIMACS2022 wcnf). Default is stdin.")
    parser.add_argument('-p', '--primal',  action='store_true', help='Just output the primal graph of the instance.')
    parser.add_argument('-d', '--display', action='store_true', help='Just produces a visual display of the instance.')    
    parser.add_argument('-tw', action='store_true', help='Estimate the treewidth of the formula and quit.')
    parser.add_argument('-to', action='store_true', help='Computes and visualizes information about the torso of the formula and quit.')
    parser.add_argument("--maxpre", help="Path to the maxpre2 preprocessor.")
    
    # Parse the arguments and map them to internal objects.
    args  = parser.parse_args()
    input = args.file
    
    # Print the header (very important).
    print(f"c\nc ------------ TorsoMaxSAT v{__version__} ------------")
    print(f"c\nc Authors: {__author__}\nc")    
    
    # Read the input formula (either from stdin or a file).
    tstart = time.time()
    print(f"c Parsing the input formula ...", end = "", flush=True)    
    phi = WCNF()
    for line in input:
        line = line.strip()
        if line and not line.startswith(('c', 'p')):
            w, c = line.split(" ")[0], [int(x) for x in line.split(" ")[1:-1]]
            if w == "h":
                phi.add_clause( c );
            else:
                phi.add_clause( c, weight = float(w) );
    print(f" {(time.time()-tstart):06.2f}s.\nc")

    # Print some stats.
    print(f"c After translating to internal format:")
    print(f"c Variables:    {phi.n}")
    print(f"c Hard Clauses: {len(phi.hard)}")
    print(f"c Soft Clauses: {len(phi.soft)}")
    print("c")

    # Auxillary modes.
    if args.primal:
        g = PrimalGraph(phi, external = True, twsolver = args.twsolver)
        print(g)
        sys.exit(0)
    if args.display:
        g = PrimalGraph(phi, external = True, twsolver = args.twsolver)
        g.display()
        sys.exit(0)
    if args.tw:
        g = PrimalGraph(phi, external = True, twsolver = args.twsolver)
        (tw,_) = g.compute_tree_decomposition()
        print(tw)
        sys.exit(0)
    if args.to:        
        g = PrimalGraph(phi, external = True, twsolver = args.twsolver)
        g.compute_torso_decomposition()
        sys.exit(0)

    # Initialize the selected solver.
    if args.solver == "gurobi":
        solver = GurobiSolver(phi, preprocessor = args.maxpre)
    elif args.solver == "scip":
        solver = ScipSolver(phi,   preprocessor = args.maxpre)
    elif args.solver == "rc2":
        solver = RC2Solver(phi,    preprocessor = args.maxpre)
    elif args.solver == "fm":
        solver = FMSolver(phi,     preprocessor = args.maxpre)
    elif args.solver == "ortools":
        solver = ORSolver(phi,     preprocessor = args.maxpre)
    elif args.solver == "dp":
        solver = DPSolver(phi,     preprocessor = args.maxpre)
        solver.twsolver = args.twsolver
    elif args.solver == "external":
        if not args.externalsolver:
            print("c\nc Error: Solver <external> is used but no external solver was specified.\nc")
            sys.exit(1)
        solver = ExternalSolver(phi, preprocessor = args.maxpre)
        solver.solver_cmd = args.externalsolver

    # Solve the instance.
    tstart = time.time()
    solver.preprocess_and_solve()
    print(f"c Solved with {args.solver} in {(time.time()-tstart):06.2f}s")
    
    # Report the results.
    if solver.state == State.UNSAT:
        print("s UNSATISFIABLE")
        sys.exit(0)

    # Comment on the results.
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
