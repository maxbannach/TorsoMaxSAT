import itertools
import networkx          as nx
import matplotlib.pyplot as plt

def _separation(g):
    """
    Returns a separation (A,S,B) such that S is a separator
    between A and B. A soft constraint is that A and B have similar size while S is small.
    """    
    # First, compute a partition into two sets.
    part = nx.community.kernighan_lin_bisection(g, seed = 42)
    A, B = g.subgraph(part[0]), g.subgraph(part[1])

    # Then, compute the bipartite graph between these two sets.
    h = nx.Graph()
    h.add_nodes_from(A, bipartite = 0)
    h.add_nodes_from(B, bipartite = 1)

    # Add crossing edges to the bipartite graph.
    for (u,v) in g.edges:
        if (u in A and v in B) or (u in B and v in A):
            h.add_edge(u,v)

    # Compute a minimum vertex cover, which is the separator between A and B.
    matching     = nx.bipartite.maximum_matching(h,           top_nodes = A)
    vertex_cover = nx.bipartite.to_vertex_cover( h, matching, top_nodes = A)

    # Return the separation
    return (A.nodes - vertex_cover, vertex_cover, B.nodes - vertex_cover)

def _neighbors_of_set_in(g, c, s):
    """
    Computes the neighbors of c in set s in g.
    """
    neighbors = set()
    for v in c:
        neighbors = neighbors.union(g.neighbors(v))
    return neighbors.intersection(s)

class PrimalGraph:

    def __init__(self, wcnf, external = False):
        self.wcnf = wcnf
        self.n    = wcnf.n
        
        # build the graph
        self.g    = nx.Graph()

        # add a clique for every clause
        for c in self.wcnf.hard:
            if external:
                c = self.wcnf._to_external(c)
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

        # done
        return (width, td)

    def to_torso_decomposition(self, td, bound):
        print("computing a torso decomposition")
        colors = ['red' if len(x) <= bound else 'gray' for x in td.nodes]

        t = map(lambda x: x[1], filter(lambda v: colors[v[0]] == 'red', enumerate(td.nodes)))
        h = nx.Graph(td.subgraph(t))

        torso = set()
        for c in nx.connected_components(h):
            for v in c:
                torso = torso.union(v)


        h = self.g.subgraph(torso)
        print(len(h))
        (w,td) = nx.algorithms.approximation.treewidth_min_fill_in(h)
        print(f"tw = {w}")
        
        pos = nx.kamada_kawai_layout(td)
        nx.draw(td, pos, with_labels=False, node_size=25)
        plt.show()
    
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

    def display(self, separation = None):
        """
        Renders the graph with matplotlib (opens a window).
        """
        pos = nx.spring_layout(self.g, seed=42)
        if separation is not None:                
            colors = ['lightgray' if value < 0.5 else 'blue' if value < 1.5 else 'orange' for value in separation]
            nx.draw(self.g, pos, with_labels=False, node_size=25, node_color=colors)
        else:
            nx.draw(self.g, pos, with_labels=False, node_size=25, node_color='lightblue')
        plt.show()

