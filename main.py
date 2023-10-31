import sys, argparse, time

# from pysat.formula import WCNF
# from pysat.examples.rc2 import RC2
# from pysat.examples.fm import FM

#import torsomaxsat
from torsomaxsat import WCNF
#from torsomaxsat import GurobiSolver as Solver
#from torsomaxsat import ScipSolver as Solver
#from torsomaxsat import RC2Solver as Solver
from torsomaxsat import FMSolver as Solver

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
    #print( phi._to_external_model(solver.assignment) )

    # #
    # # Run FM
    # #
    # tstart = time.time()
    # print(f"c running FM      ...", end = "")
    # fm = FM(phi, verbose=0)
    # fm.compute()
    # print(f" {(time.time()-tstart):06.2f}s")
    # print(f"c Optimal Solution: {sum(phi.wght) - fm.cost + offset}\nc")
