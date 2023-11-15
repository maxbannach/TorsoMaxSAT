import itertools
import networkx          as nx
import matplotlib.pyplot as plt
import tempfile, subprocess, os

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

    def __init__(self, wcnf, external = False, twsolver = None):
        self.wcnf     = wcnf
        self.n        = wcnf.n
        self.twsolver = twsolver
        
        # build the graph
        self.g    = nx.Graph()

        # add a clique for every clause
        for c in self.wcnf.hard:
            if external:
                c = self.wcnf._to_external(c)
            for (l1,l2) in itertools.combinations(c, 2):
                self.g.add_edge(abs(l1), abs(l2))
                
    def compute_tree_decomposition(self, heuristic = "deg"):
        """
        Computes a tree decomposition of this graph.
        If `self.twsolver` is set, the decomposition is computed with the external solver.
        Otherwise it is computed with the networkx heuristic (min_degree or min_fill_in).

        If the external solver fails for whatever reason, this functions falls back to networkx as well.
        """
        # If an external solver is defined, try to use it.
        if self.twsolver is not None:
            wtd = self._compute_tree_decomposition_external()
            if wtd is not None: # If it worked, we return the result, otherwise we fallback to networkx.
                (width, td) = wtd
                td, root = self._root_td(td) 
                return (width, td, root)
            
        # Compute a tree decomposition with a networkx heuristic.
        if heuristic == "fillin":
            (width, td) = nx.algorithms.approximation.treewidth_min_fill_in(self.g)
        else:
            (width, td) = nx.algorithms.approximation.treewidth_min_degree(self.g)

        # find a suitable root
        td, root = self._root_td(td)            

        # done
        return (width, td, root)

    def _compute_tree_decomposition_external(self):
        """
        Compute a tree decomposition with an external solver.
        This returns None if the subprocess fails.
        This method is used by @see compute_tree_decomposition and should not be called directly.
        """
        # Generate a temporary file to store the graph.
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:                
            temp_file.write(str(self))
            temp_file.flush()
        try:
            # Call the external treewidth solver.
            result      = subprocess.run(self.twsolver + " < " + temp_file.name, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output      = result.stdout
            (width, td) = (0,nx.Graph())
            bags        = {}
            # Parse the results and read the decomposition.
            if result.returncode == 0:
                for line in output.splitlines():
                    if line.startswith("s") or line.startswith("c"):
                        continue
                    elif line.startswith("b"):
                        ll  = line.split(" ")
                        b   = int(ll[1])
                        bag = frozenset(map(int,ll[2:]))
                        bags[b] = bag
                        if len(bag) > width:
                            width = len(bag)
                            td.add_node(bag)
                    else:
                        e = list(map(int, line.split(" ")))
                        td.add_edge(bags[e[0]], bags[e[1]])
            else:
                print("c Treewidth solver failed with an error.")
                return None # If we fail, we return None.
        except subprocess.CalledProcessError as e:
            print("c Error executing the treewidth solver:", e)
            return None # If we fail, we return None.
        finally:
            # Clean up -> close and remove temporary files.
            temp_file.close()
            os.remove(temp_file.name)
        return (width,td)

    
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
                # edges to child nodes
                digraph.add_edge(v, w)  #works with nx.dfs_postorder_nodes
                queue.append(w)
                visited.add(w)

        # add empty artificial root
        aroot = frozenset()
        digraph.add_edge(aroot, root)
        root = aroot
        # mark the root and the leaves
        digraph.nodes[root]['root'] = True
        for v in digraph.nodes:
            if digraph.out_degree(v) == 0: #works with nx.dfs_postorder_nodes
                digraph.nodes[v]['leaf'] = True
        
        return digraph, root
                
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

