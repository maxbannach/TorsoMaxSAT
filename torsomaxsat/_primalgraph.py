import itertools
import networkx as nx

class PrimalGraph:

    def __init__(self, wcnf):
        self.wcnf = wcnf
        self.n    = wcnf.n

        # build the graph
        self.g    = nx.Graph()
        for v in range(1,self.n+1):
            self.g.add_node(v)

        # add a clique for every clause
        for c in self.wcnf.hard:
            for (l1,l2) in itertools.combinations(c, 2):
                self.g.add_edge(abs(l1), abs(l2))
                
    def compute_tree_decomposition(self, heuristic = "deg"):
        # compute a tree decomposition with a networkx heuristic
        if heuristic == "fillin":
            (width, td) = nx.algorithms.approximation.treewidth_min_fill_in(self.g)
        else:
            (width, td) = nx.algorithms.approximation.treewidth_min_degree(self.g)

        # find a suitable root
        td = self._root_td(td)            

                
        return (width, td)

    def _root_td(self, td):
        """
        Heuristically root the given tree decomposition (and returns a new directed decomposition).
        """
        # find a root and generate a directed graph
        root    = next(iter(td.nodes))
        digraph = nx.DiGraph()

        # perform a bfs to point edges towards the root
        queue   = [root]
        visited = set()
        visited.add(root)
        while queue:            
            v = queue.pop()
            for w in td.neighbors(v):
                if w in visited:
                    continue
                digraph.add_edge(w, v)
                queue.append(w)
                visited.add(w)

        # mark the root and the leaves
        digraph.nodes[root]['root'] = True
        for v in digraph.nodes:
            if digraph.in_degree(v) == 0:
                digraph.nodes[v]['leaf'] = True
        
        return digraph
                
    def __str__(self):
        """
        Prints the graph in the format of PACE (which is similar to the DIMACS format).
        Comments will be used to indicate the labels.
        """
        buffer = []
        buffer.append(format(f"p tw {self.n} {len(self.g.edges)}"))
        for (u,v) in self.g.edges:
            buffer.append(format(f"{u} {v}"))
        return "\n".join(buffer)
