from torsomaxsat import Solver
from torsomaxsat import State
from torsomaxsat import PrimalGraph
from torsomaxsat import _utils
import networkx as nx
import functools

class DPSolver(Solver):

    def __init__(self, wcnf):
        super().__init__(wcnf)
        #self.nogoods = []
        #self.softngs = []
        #self.costmap = {}

        self.varmap  = {}
        #self.varmap_rev  = {}
        self.poses = 0
        print(wcnf.hard)
        print(wcnf.soft)
        # make bitmaps
        #for c in self.wcnf.hard:
        #    print("hard ", c)
        #    self.nogoods.append(self.convert2nogood(c))

        #for (c,w) in self.wcnf.soft.items():
        #    print("soft ", (c,w))
            # tuples of soft nogood + variable bitmask
        #    n,m = self.convert2nogood([-c])
        #    self.softngs.append((n,m,))
        #    self.costmap[n] = w

        #print("poses ", self.poses)
        #print("nogoods ", self.nogoods)
        #print("softngs ", self.softngs)
        #print("costmap ", self.costmap)
        #print("varmap ", self.varmap)

    def conv2nogood(self,clause):
        return self.makeMask([-l for l in clause]), self.makeMask(clause, zero_as_false=False)

    def solve(self):
        # compute a tree decomposition
        g = PrimalGraph(self.wcnf)
        width, self.td, self.root = g.compute_tree_decomposition(heuristic="fillin")

        # execute the dp
        t=self.dp()
        # only at most 1 row at the root
        assert(len(t) <= 1)
        if len(t) > 0:
            it = tuple(t.items())[0]
            #self.fitness = functools.reduce(lambda a,w: a+w, self.costmap.values()) -it[1]
            self.fitness = it[1] #sum(self.wcnf.soft.values()) -it[1]
            #self.fitness = -it[1]
            #self.assignment = self.ass2lits(it[0])
            #print(self.assignment)
            self.state = State.OPTIMAL
            #print("c OPTIMUM FOUND ", self.fitness)
        else:
            #print("UNSAT")
            self.state = State.UNSAT
            # Store the result in the internal format.
            #self.fitness    = None 
            #self.assignment = []

    def inscope(self, clause, bag, par=None):
        #print("SCOPE ", clause, bag)
        for l in clause:
            if abs(l) not in bag: #self.varmap:
                return False

        if par is not None:
            for l in clause:
                if abs(l) not in par:
                    return True
            return False
            #else:
            #    pos = self.varmap[abs(l)]
            #    if pos not in self.varmap_rev or self.varmap_rev[pos] != abs(l):
            #        return False
        return True

    def first(self, v, mask, start=0):
        p = start
        while (p < self.poses):
            if mask & 1 == v:
                #print("FIRST ", p, self.poses)
                return p
            p = p + 1
            mask = mask >> 1
        #print(" NO FIRST ", p, self.poses)
        return self.poses

    def maxpos(self, bag):
        self.poses = 0
        for i in bag:
            self.poses = max(self.poses, self.varmap[i]+1)
        #print("SET POS ", bag, self.pos)

    def makeMask(self, nogood, update=None, zero_as_false=True):
        m = 0
        free = 0
        firstfree = 0
        if update is not None:
            free = update[0]
            self.maxpos(update[1])
            #print("FREE ", free, self.poses)
            #for pos in self.varmap_rev: # positions in-use
            #    free = free | (1 << pos)
        for b in nogood:
            pos = None 
            try:
                pos = self.varmap[abs(b)]   # already assigned?
                #print(abs(b), pos, self.varmap)
                if firstfree == pos:
                    firstfree = firstfree + 1
            except KeyError:
                assert(update is not None)
                pos = self.first(0,free,firstfree)
                firstfree = pos + 1
            if update is not None:
                free = free | (1 << pos)
                self.varmap[abs(b)] = pos
                #self.varmap_rev[pos] = abs(b)
                self.poses = max(pos + 1, self.poses)
            if b > 0 or not zero_as_false:
                m = m | (1 << pos) #_utils._shift(pos)
        return m

    def mask2pos(self, mask):
        pos = []
        for i in range(0, self.poses):
            if mask & 1:
                pos.append(i)
            mask = mask >> 1
        return pos

    #def ass2lits(self, ass):
    #    lits = []
    #    for i in range(0, self.poses):
    #        lits.append(self.varmap_rev[i] * (1 if ass & 1 else -1))
    #        ass = ass >> 1
    #    return lits

    def inv_nogood(self, nogood, k, mask):
        n,m = nogood
        # note that nogood needs to be visible (mind negative assignments)
        # nogood visible and nogood invalidated
        #return m & mask == m and k & m == n&m
        return k & m == n

    #clausel x v -y v z
    #check whether 010 matches, i.e., whether we have nogood -x,y,-z
    def good(self, ngs, k, mask):
        for ng in ngs:                
            if self.inv_nogood(ng, k, mask):  #nogood invalidated
                print("INV nogood ", ng, " for ", k)
                return False
        return True

    def softgood(self, ngs, k, chmask, mask):
        costs = 0
        for (n,m,w,cl) in ngs:
            #print("CHECKING SOFT ", n, k, chmask, mask)
            if self.inv_nogood((n,m), k, chmask): #if we have clause -> expensive
                print("INV soft nogood ", (n,w), " for ", k)
        # m & chmask == m and m & mask != m and k & n & m == n & m: 
        # nogood visible in child, not anymore and unmatched --> cost + 1
                costs = costs + w  
        return costs

    def dp(self):
        tables = {}
       
        # precompute non-interfering masks first
        for n in nx.dfs_preorder_nodes(self.td, self.root):
            u = 0
            p = frozenset()
            if n != self.root:
                p = list(self.td.predecessors(n))[0]
                u = tables[p][1]
            
            mask = self.makeMask(n, update=(u,p)) #bring parent mask 
            #print("DP TRAV NODE ", n, " MASK ", mask, " poses ", self.poses, " varmap ", self.varmap, " parent ", p, " parmap ", u)
            tables[n] = (None, mask)


        for n in nx.dfs_postorder_nodes(self.td, self.root):
            chmasks = 0
            #cs = []
            for c in self.td.successors(n):   #child nodes
                #cs.append(c)
                chmasks = chmasks | tables[c][1]

            print("chmasks ", chmasks)
            
            mask = tables[n][1] #self.makeMask(n, update=0)   #update max poses
            self.maxpos(n)
            print("NODE ", n, " MASK ", mask, " poses ", self.poses, " varmap ", self.varmap)
            m = None
            if 'leaf' in self.td.nodes[n]: #n.isLeaf():
                m = {0:0}   #empty assignment 0 : costs 0
                print('leaf')
            else:
                prevch = 0
                #for c in self.td.predecessors(n):   #child nodes
                for c in self.td.successors(n):   #child nodes
                    print("previous: ", c, tables[c][0])
                    chmask = tables[c][1] #self.td.bag(c))
                    
                    # grab table
                    mn = tables[c][0]
                    # project
                    #mn = self.forget(list(self.td.predecessors(n))[0], mn, mask, chmask)
                    mn = self.forget(c, n, mn, mask, chmask)
                    print("project ", mn, " mask ", mask, " chmask ", chmask)
                    # join
                    if m is None:
                        m = mn
                        prevch = chmask
                    else:
                        print("joining ", mn, " with ", m)
                        m = self.join(mask, mn, chmask, m, prevch)
                        print("join ", m)
                        prevch = (chmask & mask) | (prevch & mask)    # could be union over both

                    # free table
                    del tables[c]
                    # free allocated, removed mask elements
                    #print(self.mask2pos(chmask & ~mask))
                    #for i in self.mask2pos(chmask & ~mask):
                        #assert(i in self.varmap_rev)
                    #    del self.varmap_rev[i]
           
            # intr
            print("intro ", mask, " chmasks ", chmasks)
            m = self.intro(n, m, mask, chmasks)
            tables[n] = (m,mask)
            print("SETTING ", m, " for ", n)
        return tables[self.root][0]   #root table


    #equijoin of two dicts (only works if scheme is identical)
    def join(self, mask, m1, m1mask, m2, m2mask):
        m1mask = mask & m1mask
        m2mask = mask & m2mask

#        b = None
#        if len(self.mask2pos(m1mask & ~m2mask)) < len(self.mask2pos(m2mask & ~m1mask)): #swap
#            m = m1
#            mm = m1mask
#            
#            m1 = m2
#            m1 = m2mask
#            
#            m2 = m
#            m2mask = mm
#
#        if ~m1mask & m2mask > 0:    #sth missing?
#            b = self.mask2pos(m1mask | (~m1mask & m2mask))
#            m1 = self.intro(b, m1, m1mask | (~m1mask & m2mask), m1mask)

        m = {}

        if False: #True: #m1mask == m2mask:    #equijoin
            for (k,o) in m1.items():
                try:
                    m[k] = o + m2[k]
                except KeyError:
                    pass
        else:           # FIXME, only quadratic join ;/
            for (k,o) in m1.items():
                k = k & mask  #1,2   1,6   
                for (k2,o2) in m2.items():
                    k2 = k2 & mask
                    if k & m2mask == k2 & m1mask:
                        sofar = 0
                        try:
                            sofar = m[k|k2] #take sum of costs
                        except KeyError:
                            pass
                        m[k|k2] = max(sofar, o + o2)
        return m


    #fresh items at poses
    def intro(self, bag, m1, mask, chmasks):
        #pos = set(bag).difference(ch_bag)
        #print(pos)
        pos = self.mask2pos(mask & ~chmasks)    #intro poses
        if len(pos) == 0:
            return m1

        print("INTR POS ", pos)

        ngs = []
        for clause in self.wcnf.hard:
            if self.inscope(clause, bag):
                ng = self.conv2nogood(clause)
                #if n & mask == n:
                ngs.append(ng)

        m = m1
        if len(pos) > 0:
            m = {}
            for (k,o) in m1.items():
                for ps in _utils.powerset(pos):
                    kk = k 
                    for p in ps:
                        kk = kk | (1 << p)
                    #print(kk)
                    if self.good(ngs, kk, mask):   #no nogood invalidated
                        m[kk] = o
        return m

    #project according to bitmask
    def forget(self, bag, par_bag, m1, mask, chmask):
        keep = mask & chmask

        ngs = []
        for (clause,w) in self.wcnf.soft.items():
            #print("candidate soft nogood ", clause)
            clause = [-clause]  #clause means we should have -clause
            if self.inscope(clause, bag, par=par_bag):
                (n,m) = self.conv2nogood(clause)
                #if n & mask != n: # and m & mask != m:
                ngs.append((n,m,w,clause))
                #else:
                #    print(clause, bag, n, chmask, m, mask)
                #    assert(False)
       
        print("soft nogoods ", mask, chmask, ngs)
        m = {}

        for (k,o) in m1.items():
            #print(k,o)
            o = o + self.softgood(ngs, k, chmask, mask)
            k = k & keep
            try:
                m[k] = max(m[k], o) #take smallest costs
            except KeyError:
                m[k] = o
        return m
