from torsomaxsat import Solver
from torsomaxsat import PrimalGraph

class DPSolver(Solver):

	def __init__(self, wcnf):
        super().__init__()
        self.nogoods = []
        self.softngs = []
        self.costmap = {}

        self.varmap  = {}
        self.varmap_rev  = {}
        self.poses = 0

        # make bitmaps
        for c in self.wcnf.hard:
            self.nogoods = self.makeMask([-l for l in c])

        for (c,w) in self.wcnf.soft.items():
            # tuples of soft nogood + variable bitmask
            n,m = self.makeMask([-l for l in c]), self.makeMask(c, zero_as_false=False)
            self.softngs.append(tuple(n,m))
            self.costmap[n] = w

    def solve(self):
        # compute a tree decomposition
        g = PrimalGraph(self.wcnf)
        width, self.td, self.root = g.compute_tree_decomposition(heuristic="fillin")

        # execute the dp
        t=self.dp()
        # ...
        assert(len(t) < 1)
        if len(t) > 0:
            it = t.items()[0]
            self.fitness = it[1]
            self.assignment = self.ass2lits(it[0])
        else:
            # Store the result in the internal format.
            self.fitness    =  0
            self.assignment = [0]*self.wcnf.n

    def makeMask(self, clause, zero_as_false=True):
        m = 0
        for b in bag:
            pos = self.poses
            try:
                pos = self.varmap[abs(b)]
                self.varmap_rev[pos] = abs(b)
            except KeyError:
                self.varmap[abs(b)] = self.poses
                self.varmap_rev[self.poses] = abs(b)
                self.poses = self.poses + 1
            if b > 0 or not zero_as_false:
                m = m | self._shift(1, pos)
        return m

    def mask2pos(self, mask):
        pos = []
        for i in range(0, self.poses):
            if mask & 1:
                pos.append(i)
            mask = mask >> 1
        return pos

    def ass2lits(self, ass):
        lits = []
        for i in range(0, self.poses):
            lits.append(self.varmap_rev[i] * (1 if mask & 1 else -1))
            mask = mask >> 1
        return lits

    #shift v by p positions to left
    def _shift(v, p):
        while p > 0:
            v = v << p
            p = p-1
        return v

    #clausel x v -y v z
    #check whether 010 matches, i.e., whether we have nogood -x,y,-z
    def good(self, k):
        for (n,m) in self.nogoods:
            if k & n & m == n & m:  #nogood invalidated
                return False
        return True

    def softgood(self, k, chmask, mask):
        costs = 0
        for (n,m) in self.softngs:    #nogood + mask
            if m & chmask == m and m & mask != m and k & n & m == n & m: # nogood visible in child, not anymore and unmatched --> cost + 1
                costs = costs + self.costmap[n]
        return costs

    def dp(self):
        tables = {}
        
        m = None
        for n in nx.dfs_postorder_nodes(self.td, self.root):
            bag = n #self.td.bag(n)
            mask = self.makeMask(bag)

            if self.td.nodes(n)['leaf']: #n.isLeaf():
                m = {}
            else:
                chmasks = 0
                for c in self.td.predecessors(n):   #child nodes
                    chmask = self.makeMask(c) #self.td.bag(c))
                    chmasks = chmasks | chmask
                    
                    # grab table
                    mn = tables[c]
                    # free table
                    del tables[c]

                    # project
                    mn = self.forget(mn, mask, chmask)
                    # join
                    if m is None:
                        m = mn
                    else:
                        m = self.join(mn, m)
           
            # intr
            m = self.intro(m, mask, chmasks)
            tables[n] = m
        return m    #root table


    #equijoin of two dicts
    def join(self, m1, m2):
        m = {}
        for (k,o) in m1.items():
            try:
                m[k] = o + m2[k] #take sum of costs
            except KeyError:
                pass


    #fresh items at poses
    def intro(self, m1, mask, chmasks):
        pos = self.mask2pos(mask & ~chmasks)    #intro poses

        for (k,o) in m1.items():
            for p in pos:
                for v in (0,1):
                    kk = k | self._shift(v,p)
                    if self.good(kk):   #no nogood invalidated
                        m[kk] = o


    #project according to bitmask
    def forget(self, m1, mask, chmask):
        m = {}
        keep = mask & chmask

        for (k,o) in m1.items():
            k = k & keep
            try:
                m[k] = min(m[k], o + self.softgood(k, chmask, mask)) #take smallest costs
            except KeyError:
                m[k] = o
