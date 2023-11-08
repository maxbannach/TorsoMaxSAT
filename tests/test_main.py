import unittest
import subprocess
from itertools import chain

simple = [
    ('examples/simple.wcnf.xz', -1.25),
    ('examples/simple2.wcnf.xz', -1),
    ('examples/unsat.wcnf.xz', float('inf')),
]

medium = [
    ('examples/spot5_wt-54.wcsp.log.wcnf.xz', 37),
    ('examples/warehouses_wt-warehouse0.wcsp.wcnf.xz', 328),
    ('examples/MaxSATQueriesinInterpretableClassifiers_wt-transfusion_test_7_DNF_3_5.wcnf.xz', 96),
]

hard = [        
    ('examples/auctions_wt-cat_paths_60_70_0003.txt.wcnf.xz', 44555),
    ('examples/staff-scheduling_wt-instance1.wcnf.xz', 607),
]

def run(file_path, solver_config=""):
        cost = float('inf')
        try:
            result = subprocess.run("xz -dc " + file_path + " | python main.py " + solver_config, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout
            if result.returncode == 0:
                for line in output.splitlines():
                    if line.startswith("o"):
                        cost = float(line.split(" ")[1])
        finally:
            return cost

class TestSolver(unittest.TestCase):
    
    def test_rc2(self):
        for (file, goal) in chain(simple, medium):
            self.assertEqual(run(file), goal)

    def test_fm(self):
        for (file, goal) in simple:
            self.assertEqual(run(file, "-s fm"), goal)

    def test_ortools(self):
        for (file, goal) in chain(simple, medium, hard):
            self.assertEqual(run(file, "-s ortools"), goal)

    def test_gurobi(self):
        for (file, goal) in chain(simple, medium, hard):
            self.assertEqual(run(file, "-s gurobi"), goal)

    def test_scip(self):
        for (file, goal) in chain(simple, medium):
            if goal != float('inf'):
                self.assertLessEqual(abs(run(file, "-s scip")-goal), 0.001)
            else:
                self.assertEqual(run(file, "-s scip"), goal)
    
if __name__ == '__main__':
    unittest.main()
