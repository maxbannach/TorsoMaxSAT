from torsomaxsat import Solver, solver_from_string
from torsomaxsat import State
from torsomaxsat import PrimalGraph
from torsomaxsat import _utils
from torsomaxsat import _wcnf

import networkx as nx
import functools
import copy

class DPSolver(Solver):

    def __init__(self, wcnf, preprocessor, subsolver = "rc2"):
        super().__init__(wcnf, preprocessor)
        #self.nogoods = []
        #self.softngs = []
        #self.costmap = {}

        self.subsolver = subsolver
        self.nodes = None
        self.varmap  = {}
        #self.varmap_rev  = {}
        self.poses = 0
        #print(wcnf.hard)
        #print(wcnf.soft)
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
        g = PrimalGraph(self.wcnf, twsolver = self.twsolver)
        #width, self.td, self.root = g.compute_tree_decomposition(heuristic="fillin")
        torso = g.compute_torso_decomposition()
        if torso is not None:
            width, self.td, self.root, self.nodes  = torso
        else:
            # We did not find a good torso, fall back to subsolver.
            print("c Unable to find a good torso.")
            sub = solver_from_string(self.subsolver, self.wcnf, preprocessor = self.preprocessor, twsolver = self.twsolver, subsolver = self.subsolver)
            sub.solve()
            self.fitness    = sub.get_fitness()
            self.assignment = sub.assignment
            self.state      = sub.state
            return

        # execute the dp
        t=self.dp(self.prepare_dp())
        # only at most 1 row at the root
        assert(len(t) <= 1)
        if len(t) > 0:
            it = tuple(t.items())[0]
            #self.fitness = functools.reduce(lambda a,w: a+w, self.costmap.values()) -it[1]
            self.fitness = float(it[1]) #sum(self.wcnf.soft.values()) -it[1]
            #self.fitness = -it[1]

            #FIXME: enable tracking of assignment parts and output assignment
            self.assignment = [0] * max(self.wcnf.varmap.value_to_key)
            #self.assignment = [i for i in self.wcnf.varmap.value_to_key] #self.ass2lits(it[0])
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
        while start > 0:
            mask = mask >> 1
            start = start - 1
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
        alloc = 0
        firstfree = 0
        if update is not None:
            alloc = update[0]
            self.maxpos(update[1])
            #print("FREE ", alloc, self.poses)
            #for pos in self.varmap_rev: # positions in-use
            #    free = free | (1 << pos)
        for b in nogood:
            pos = None 
            try:
                pos = self.varmap[abs(b)]   # already assigned?
                #print(abs(b), pos, self.varmap)
                #print("ASS ", abs(b), pos)
                if firstfree == pos:
                    firstfree = firstfree + 1
            except KeyError:
                assert(update is not None)
                pos = self.first(0,alloc,firstfree)
                firstfree = pos + 1
                assert(alloc & (1 << pos) == 0)
            if update is not None:
                alloc = alloc | (1 << pos)
                self.varmap[abs(b)] = pos
                #self.varmap_rev[pos] = abs(b)
                self.poses = max(pos + 1, self.poses)
            if b > 0 or not zero_as_false:
                m = m | (1 << pos) #_utils._shift(pos)
        return m

    def mask2pos(self, mask):
        pos = []
        for i in range(0, self.poses):
            if mask & 1 > 0:
                pos.append(i)
            mask = mask >> 1
        return pos

    def ass2lits(self, bag, ass):
        #pos = self.mask2pos(ass)    #get positive list
        lits = [] #pos and neg

        for i in bag:
            if ass & (1 << self.varmap[i]) > 0: # true / pos
                lits.append(i)
            else:   # false / neg
                lits.append(-i)
        return lits

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
                #print("INV nogood ", ng, " for ", k)
                return False
        return True

    def softgood(self, ngs, k, chmask, mask):
        fitness = 0
        for (n,m,w) in ngs:
            #print("CHECKING SOFT ", n, m, k, chmask, mask)
            if self.inv_nogood((n,m), k, chmask): #if we have clause -> expensive
                #print("INV soft nogood ", (n,w), " for ", k)
        # m & chmask == m and m & mask != m and k & n & m == n & m: 
        # nogood visible in child, not anymore and unmatched --> cost + 1
                fitness = fitness + w  
        return fitness

    def prepare_dp(self):
        tables = {}
      
        softs = copy.copy(self.wcnf.soft)
       
        #ngs = []
        #for (clause,w) in self.wcnf.soft.items():
        #    clause = [-clause]  #clause means we should have -clause
        #    if self.inscope(clause, bag, par=par_bag):
        #        (n,m) = self.conv2nogood(clause)
        #        ngs.append((n,m,w,clause))
       
        # precompute non-interfering masks first
        # assign bag formulas and subformulas
        for n in nx.dfs_preorder_nodes(self.td, self.root):
            # skip subproblem nodes
            if self.nodes is not None and n not in self.nodes:
                continue
            print("c PREPARE ", n, self.nodes, self.root)
            p = frozenset()
            u = 0
            if n != self.root:
                p = list(self.td.predecessors(n))[0]
                u = tables[p][1]
            
            mask = self.makeMask(n, update=(u,p)) #bring parent mask 
            

            # soft constraints
            soft = []
            delc = []
            for k in n:
                if k not in p:
                    try:
                        w = softs[k]
                        nn,m = self.conv2nogood([-k])
                        soft.append((nn,m,w,))
                        delc.append(k)
                    except KeyError:
                        pass

            for d in delc:  # never, ever do this soft constraint again! (in particular: not for any subinstance!)
                #print(" DEL ", d)
                del softs[d]

            hard = []
            
            delc = []
            pos = 0
            sub = {}
            
            #FIXME: make faster somehow? --> better data structure like SDD?
            for clause in self.wcnf.hard:
                if self.inscope(clause, n):
                    ng = self.conv2nogood(clause)
                    #if n & mask == n:
                    hard.append(ng) 
                elif self.nodes is not None:
                    for nn in self.td.successors(n):   #child nodes
                        if nn not in self.nodes:    # only take the subproblem nodes
                            if self.inscope(clause, nn):
                                s = None
                                try:
                                    s = sub[nn]
                                except KeyError:
                                    s = _wcnf.WCNF()
                                    sub[nn] = s

                                s.add_clause(clause)
                                for k in nn:
                                    if k not in n:
                                        w = None
                                        try:
                                            w=softs[k]
                                        except KeyError:
                                            pass
                                        if w is not None:
                                            s.add_clause([k], weight=float(w))
                                            del softs[k]   # never do soft constraints twice!
                                #print(" DEL ", pos)
                                delc.append(pos)
                                break   # a clause is only once in-scope!
                pos = pos + 1
          
            #print(delhard, len(self.wcnf.hard))
            pos = 0
            for d in delc:
                #print(d,pos,d-pos,len(self.wcnf.hard))
                del self.wcnf.hard[d-pos]
                pos = pos + 1

            assert(n not in tables)
            tables[n] = (None, mask, hard, soft, sub)
            #print(tables)
        #assert(False)
        return tables


    def dp(self, tables):
        # dp
        for n in nx.dfs_postorder_nodes(self.td, self.root):
            if self.nodes is not None and n not in self.nodes:
                #print("skip ", n)
                continue
            chmasks = 0
            #cs = []
            for c in self.td.successors(n):   #child nodes
                #cs.append(c)
                try:
                    chmasks = chmasks | tables[c][1]
                except KeyError:
                    continue        # found subproblems

            #print("chmasks ", chmasks)
            
            _,mask,hard,nsoft,sub = tables[n] #self.makeMask(n, update=0)   #update max poses
            self.maxpos(n)
            print("c NODE ", n, " MASK ", mask, " poses ", self.poses, " varmap ", self.varmap, hard, nsoft, "# sub maxsats: ", len(sub)) #, " sub ", sub)
            m = None
            if 'leaf' in self.td.nodes[n]: #n.isLeaf():
                m = {0:0}   #empty assignment 0 : costs 0
                #print('leaf')
            else:
                prevch = 0
                mn,chmask,_,soft = (None, None, None, None)
                #subbags = []
                #for c in self.td.predecessors(n):   #child nodes
                for c in self.td.successors(n):   #child nodes
                    try:
                        mn,chmask,_,soft,_ = tables[c]
                    except KeyError:
                        #subbags.append(c)
                        continue
                    #print("previous: ", c, tables[c][0])
                    #chmask = tables[c][1] #self.td.bag(c))
                    
                    # grab table and soft (soft is 1 level behind)
                    #soft = tables[c][3]
                    # project
                    #mn = self.forget(list(self.td.predecessors(n))[0], mn, mask, chmask)
                    #mn = self.forget(c,n,soft, mn, mask, chmask)
                    mn = self.forget(soft, mn, mask, chmask)
                    #print("project ", mn, " mask ", mask, " chmask ", chmask)
                    # join
                    if m is None:
                        m = mn
                        prevch = chmask
                    else:
                        #print("joining ", mn, " with ", m)
                        m = self.join(mask, mn, chmask, m, prevch)
                        #print("join ", m)
                        prevch = (chmask & mask) | (prevch & mask)    # could be union over both

                    # free table
                    del tables[c]
                    # free allocated, removed mask elements
                    #print(self.mask2pos(chmask & ~mask))
                    #for i in self.mask2pos(chmask & ~mask):
                        #assert(i in self.varmap_rev)
                    #    del self.varmap_rev[i]
           
            # intr
            print("c INTRO+SUB ", mask, " chmasks ", chmasks)
            m = self.intro(n, hard, m, mask, chmasks, sub)
            tables[n] = (m,mask,hard,nsoft,sub)
            print("c SETTING ", m, " for ", n)
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
    def intro(self, bag, hard, m1, mask, chmasks, sub):
        #pos = set(bag).difference(ch_bag)
        #print(pos)
        pos = self.mask2pos(mask & ~chmasks)    #intro poses
        #if len(pos) == 0:
        #    return m1

        #print("INTR POS ", pos)

        # find sub bag-vars after projection
        sub_vars = {}
        for (ns,s) in sub.items():
            submask = 0
            for b in bag:
                if b in s.varmap.key_to_value: #value_to_key:
                    submask = submask | (1 << self.varmap[b])
            sub_vars[ns] = submask

        sub_cache = {}

        #FIXME: avoid copying in some cases?
        m = m1
        if len(pos) > 0 or len(hard) > 0 or len(sub) > 0:
            m = {}
            for (k,o) in m1.items():
                for ps in _utils.powerset(pos):
                    kk = k 
                    for p in ps:
                        kk = kk | (1 << p)  #new candidate

                    #print(kk)
                    if self.good(hard, kk, mask):   #no nogood invalidated
                        ow = 0
                        for (ns,s) in sub.items():
                            cache = None
                            try:
                                cache = sub_cache[ns]
                            except KeyError:
                                cache = {}
                                sub_cache[ns] = cache

                            submask = sub_vars[ns]
                            wcnf = s
                            kk_sub = kk & submask
                            ass = self.ass2lits(bag, kk_sub)
                            sub_res = None
                            try:
                                sub_res = cache[kk_sub]
                                #print("CACHE HIT ", kk_sub, kk)
                                if sub_res is None:
                                    ow = None # no need to further call sth -> UNSAT
                                    break
                            except KeyError:
                                pass
                            if sub_res is not None: #cache hit
                                ow = ow + sub_res
                            else:  # not computed so far
                                if len(ass) > 0: # something to assign?
                                    wcnf = copy.deepcopy(s)
                                    for l in ass:
                                        if abs(l) in wcnf.varmap.key_to_value:  # only assign req. elements
                                            wcnf.add_clause([l])
                                #print("SOLVING SUBINSTANCE ", wcnf.varmap, wcnf.hard, " SOFT PART ", wcnf.soft, " FOR ", ns, " ON ", ass, kk_sub)
                                subs = solver_from_string(self.subsolver, wcnf, preprocessor = self.preprocessor, twsolver = self.twsolver, subsolver = self.subsolver)
                                subs.preprocess_and_solve()
                                wcnf = None
                                if subs.state != State.OPTIMAL:
                                    #print("UNSAT")
                                    subs.fitness = None
                                    ow = None
                                    break
                                else:
                                    #print("SOLVED SUBINSTANCE ", subs.fitness, " FOR ", ns, " ON ", ass, kk_sub)
                                    #print("SOLVED SUBINSTANCE ", subs.fitness)
                                    ow = ow + subs.fitness
                                cache[kk_sub] = subs.fitness
                        if ow is not None:
                            #if ow > 0:
                                #print("SUBINSTANCES ", ow, " to be added to ", o, " FOR ", kk, kk_sub)
                            m[kk] = o + ow
        return m

    #project according to bitmask
    #def forget(self, bag, par_bag, soft, m1, mask, chmask):
    def forget(self, soft, m1, mask, chmask):
        keep = mask & chmask

        #ngs = []
        #for (clause,w) in self.wcnf.soft.items():
        #    #print("candidate soft nogood ", clause)
        #    clause = [-clause]  #clause means we should have -clause
        #    if self.inscope(clause, bag, par=par_bag):
        #        (n,m) = self.conv2nogood(clause)
        #        #if n & mask != n: # and m & mask != m:
        #        ngs.append((n,m,w))
        #        #else:
        #        #    print(clause, bag, n, chmask, m, mask)
        #        #    assert(False)
        #print(" SOFT vs ", soft, ngs)

#        soft = ngs
        #print("soft nogoods ", mask, chmask, soft)
        m = {}
        #print(m1)
        for (k,o) in m1.items():
            #print(k,o)
            o = o + self.softgood(soft, k, chmask, mask)
            k = k & keep
            try:
                m[k] = max(m[k], o) #take max fitness 
            except KeyError:
                m[k] = o
        return m
