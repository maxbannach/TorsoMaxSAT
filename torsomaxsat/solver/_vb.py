from torsomaxsat import Solver, solver_from_string
import multiprocessing
import copy
import time

def solve_sub(cmd, wcnf, subsolver, twsolver, preprocessor, result_queue):    
    solver = solver_from_string(cmd, wcnf, preprocessor = preprocessor, twsolver = twsolver, subsolver = subsolver)
    solver.solve()
    result_queue.put( (solver.assignment, solver.fitness, solver.state) )
                
def solve_vb(wcnf, subsolver, twsolver, preprocessor):
    # Run the solver and the solver in dp mode in parallel.
    result_queue = multiprocessing.Queue()
    process_a    = multiprocessing.Process(target=solve_sub, args=("dpp", wcnf, subsolver, twsolver, preprocessor, result_queue))
    process_b    = multiprocessing.Process(target=solve_sub, args=(subsolver, wcnf, subsolver, twsolver, preprocessor, result_queue))
    
    # Start the solvers.
    process_a.start()
    process_b.start()

    # Wait until one of the solvers is done.
    while True:
        if not process_a.is_alive() or not process_b.is_alive():
            process_a.terminate()
            process_b.terminate()            
            return result_queue.get()
        time.sleep(0.1)
    
class VBSolver(Solver):

    def __init__(self, wcnf, preprocessor, subsolver = "rc2"):
        super().__init__(wcnf, preprocessor)
        self.subsolver = subsolver

    def solve(self):
        result = solve_vb(self.wcnf, self.subsolver, self.twsolver, self.preprocessor)
        self.assignment = result[0]
        self.fitness    = result[1]
        self.state      = result[2]
