import sys, argparse, time
from pysat.formula import WCNF

from pysat.examples.rc2 import RC2
from pysat.examples.fm import FM

__version__ = "0.0.1"
__author__ = "Max Bannach and Markus Hecher"

if __name__ == "__main__":

    # program info and argument parsing
    parser = argparse.ArgumentParser(description='A MaxSAT solver based on Tree Decompositions of the Torso Graph.')
    parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))
   
    args = parser.parse_args()

    # header
    print(f"c\nc ------ TorsoMaxSAT v{__version__} ------")
    print(f"c\nc Authors: {__author__}\nc")

    print(f"c parsing formula ...", end="")
    tstart = time.time()
    # parse a wcnf in dimacs2022 format
    hard = []
    soft = []
    nv   = 0
    for line in sys.stdin:
        line = line.strip() 
        if line and not line.startswith(('c', 'p')):
            ll = line.split(" ")[:-1]
            c  = [int(x) for x in ll[1:]]
            if max(map(abs, c)) > nv:
                nv += 1
            if ll[0] == "h":
                hard.append(c)
            else:
                w = float(ll[0])
                if w.is_integer():
                    w = int(w)
                soft.append( (c,w) )
                
    # generate a wcnf with positive unit soft clauses
    phi    = WCNF()
    offset = 0
    for c in hard:
        phi.append(c)
    for (c,w) in soft:
        sign = 1
        if w < 0:
            offset +=  w
            w       = -w
            sign     = -1
        if len(c) >= 2:
            nv += 1
            c.append(nv)
            phi.append(c)
            phi.append([-nv*sign], weight = w)
        else:
            phi.append([c[0]*sign], weight = w)
    print(f" {(time.time()-tstart):06.2f}s\nc")

    #
    # Run RC2
    #
    tstart = time.time()
    print(f"c running RC2     ...", end = "")
    rc2 = RC2(phi)
    model = rc2.compute()
    print(f" {(time.time()-tstart):06.2f}s")
    print(f"c Optimal Solution: {sum(phi.wght) - rc2.cost + offset}\nc")

    #
    # Run FM
    #
    tstart = time.time()
    print(f"c running FM      ...", end = "")
    fm = FM(phi, verbose=0)
    fm.compute()
    print(f" {(time.time()-tstart):06.2f}s")
    print(f"c Optimal Solution: {sum(phi.wght) - fm.cost + offset}\nc")
