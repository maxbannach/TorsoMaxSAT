from torsomaxsat import Solver, State
import tempfile, os, subprocess, sys

class ExternalSolver(Solver):
    
    def solve(self):

        # Write the formula to a temporary file.
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(repr(self.wcnf))
            temp_file.flush()
            
        # Try to solve it with the sub solver.
        try:
            result = subprocess.run(self.solver_cmd + " " + temp_file.name, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout           
            if result.returncode == 0:
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

                    # Parse the assignment.
                    if line.startswith("v"):
                        self.assignment = list(map(lambda x: int(x), line.split(" ")[1]))                
            else:
                print("c Sub solver failed with an error.")
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            print("c Error executing the sub solver:", e)
            sys.exit(1)
        finally:
            temp_file.close()
            os.remove(temp_file.name)
