from torsomaxsat import Solver, State
import tempfile, os, subprocess, sys
from subprocess import TimeoutExpired

class ExternalSolver(Solver):

    def __init__(self, wcnf, solver_cmd, preprocessor = None, timeout = None):
        """
        An external solver may be given an additional timeout, which limits the time the sub process is run.
        This option is intended for the use of anytime solvers.
        """
        super().__init__(wcnf, preprocessor)
        self.solver_cmd = solver_cmd
        self.timeout    = timeout
    
    def solve(self):

        # Write the formula to a temporary file.
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(repr(self.wcnf))
            temp_file.flush()
            
        # Try to solve it with the sub solver.
        try:
            if self.timeout is None:
                result = subprocess.run(self.solver_cmd + " " + temp_file.name,
                                          shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                result = subprocess.run("timeout --preserve-status " + str(self.timeout) + " "
                                        + self.solver_cmd + " " + temp_file.name,
                                          shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout           
            self.state = State.ERROR
            if result.returncode == 0 or result.returncode == 10 or result.returncode == 40:
                for line in output.splitlines():
                    # Parse the statae of the sub solver.
                    if line.startswith("s"):
                        if line == "s OPTIMUM FOUND":
                            self.state = State.OPTIMAL
                        elif line == "s UNSATISFIABLE":
                            self.state = State.UNSAT
                            return

                    # Parse the optimum value.
                    if line.startswith("o"):
                        self.fitness = self.wcnf._max_fitness() - float(line.split(" ")[1])
                        if self.state != State.OPTIMAL:
                            self.state = State.UNKNOWN

                    # Parse the assignment.
                    if line.startswith("v"):
                        self.assignment = list(map(lambda x: int(x), line.split(" ")[1]))                
        except subprocess.CalledProcessError as e:
            print("c Error executing the sub solver:", e)
            sys.exit(1)
        finally:
            temp_file.close()
            os.remove(temp_file.name)
