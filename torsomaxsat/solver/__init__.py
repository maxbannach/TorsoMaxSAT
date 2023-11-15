from torsomaxsat import WCNF
from enum import Enum
import tempfile, subprocess, os

class Solver():

    def __init__(self, wcnf, preprocessor = None):
        self.wcnf         = wcnf  # The input formula (a torsomaxsat WCNF).
        self.fitness      = 0     # The value of the best model (after run solve).
        self.assignment   = []    # An assignment (of the internal representation of) the wcnf after solver.
        self.preprocessor = preprocessor
        self.state        = State.UNKNOWN

    def preprocess_and_solve(self):
         # If there is no preprocessor, we just solve the problem.
        if self.preprocessor is None:           
            self.solve()
            return        
        # Otherwise we preprocess, solve, and reconstruct.
        self._maxpre_preprocess()
        print(f"c After preprocessing:")
        print(f"c Variables:    {self.wcnf.n}")
        print(f"c Hard Clauses: {len(self.wcnf.hard)}")
        print(f"c Soft Clauses: {len(self.wcnf.soft)}")
        print("c")
        self.solve()
        if self.state == State.OPTIMAL:
            self._maxpre_reconstruct()

    def _maxpre_preprocess(self):
        # Generate a temporary file to store the formula.
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as wcnf_file, \
             tempfile.NamedTemporaryFile(delete=True, mode='r', encoding='utf-8') as map_file:

            # Write the formula to the first temporary file.
            wcnf_file.write(repr(self.wcnf))
            wcnf_file.flush()
            try:
                # Run maxpre and store the map file to the second temporary file.
                result = subprocess.run(self.preprocessor + " " + wcnf_file.name + " preprocess -techniques=[bu]#[buvsrg] -mapfile="+map_file.name,
                                        shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Obtain the preprocessed wcnf.
                output    = result.stdout
                self.old  = self.wcnf
                self.wcnf = WCNF()
                for line in output.splitlines():
                    line = line.strip().replace("  ", " ")
                    if line and not line.startswith(('c', 'p')):                        
                        w, c = line.split(" ")[0], [int(x) for x in line.split(" ")[1:-1]]
                        if w == "h":
                            self.wcnf.add_clause( c );
                        else:
                            self.wcnf.add_clause( c, weight = float(w) );

                # Obtain the map file.
                map_file.seek(0)
                self.map = map_file.read()
            except subprocess.CalledProcessError as e:
                print("c Error executing maxpre2 preprocess:", e)
            finally:
                # Clean up.
                wcnf_file.close()
                map_file.close()

    def _maxpre_reconstruct(self):
        with tempfile.NamedTemporaryFile(delete=True, mode='w', encoding='utf-8') as sol_file, \
             tempfile.NamedTemporaryFile(delete=True, mode='w', encoding='utf-8') as map_file:
            # Write the mapfile.
            map_file.write(self.map)
            map_file.flush()
            
            # Write the solution to the temporary file.
            sol_file.write("s OPTIMUM FOUND\n")
            sol_file.write(f"o {self.get_cost()}\n")
            for (i,l) in enumerate( self.assignment ):
                if i % 25 == 0:
                    if i > 0:
                        sol_file.write("\n")
                    sol_file.write("v")
                sol_file.write(f" {l}")
            sol_file.write("\n")
            sol_file.flush()
                
            try:
                 # Run maxpre to reconstruct a full solution.
                result = subprocess.run(self.preprocessor + " " + sol_file.name + " reconstruct -mapfile="+map_file.name,
                                        shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Reconstruct a full assignment.
                self.assignment = []
                output    = result.stdout
                cost      = 0
                for line in output.splitlines():
                    if line.startswith("o"):
                        cost = int(line.strip().split(" ")[1])
                    elif line.startswith("v"):
                        for (v,sign) in enumerate(line):
                            self.assignment.append(v if sign == "1" else -v)
                self.wcnf = self.old
                self.fitness = self.wcnf._max_fitness() - cost
            except subprocess.CalledProcessError as e:
                print("c Error executing maxpre2 reconstruct:", e)
            finally:
                # Clean up.
                sol_file.close()
                map_file.close()
            
    def solve(self):
        pass

    def get_fitness(self):
        return self.fitness + self.wcnf.offset

    def get_cost(self):
        return self.wcnf._max_fitness() - self.fitness + self.wcnf.offset

class State(Enum):
    UNKNOWN = "UNKNOWN"
    UNSAT   = "UNSAT"
    OPTIMAL = "OPTIMAL"
    ERROR   = "ERROR"
