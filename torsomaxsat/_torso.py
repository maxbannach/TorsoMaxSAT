import torsomaxsat as tms
import networkx    as nx
import itertools

import clingo
from clingo import Control
import threading

clingo_program = """
% We can selected candidate vertices to the torso.
{ torso(X) : node(X) }.

% Select as many vertices as possible.
#maximize { @cost, X : torso(X) }.

% Each vertex in the torso is assigned to a component with its own id.
% The semantic of component(C,X) is that X is in the component with label C.
component(X,X) :- torso(X).

% We propagate components along elements outside of the torso.
component(X,Y) :- torso(X), not torso(Y), edge(X,Y).
component(X,Y) :- torso(X), not torso(Y), edge(Y,X).

% We also propagate the components after beyond the torso.
component(C,Y) :- component(C,X), not torso(X), edge(X,Y).
component(C,Y) :- component(C,X), not torso(X), edge(Y,X).

% Edges added to the torso.
:~ X < Y, torso(Y), component(X,Y), not edge(X,Y). [1,X,Y] % added via the cliques
:~ torso(X), torso(Y), edge(X,Y). [1,X,Y]                  % induced edges
"""

def Torso(g, cost = 8, k = 60, timeout = 60):        
    """
    Initializes a torso for the given graph *g*, which is computed on initialization with cling.
    
    args:
        cost:    Point given to nodes added to the torso in the optimization.
        k:       Number of candidates from which the torso is chosen.
        timeout: Maximum time in seconds used to find a torso.
    """
    # Setup Clingo.
    control = Control()             
    control.configuration.solver.opt_strategy   = "usc,pmres,disjoint,stratify"
    control.configuration.solver.opt_usc_shrink = "min"
    control.configuration.solve.opt_mode        = "opt"
    control.configuration.solve.solve_limit     = "umax,umax"
    
    # Add the the pre torso of the graph as relational structure and provide the logic program.
    control.add("base", [], _graph2structure(_pretorso(g,k)))
    control.add("base", [], clingo_program.replace("@cost", str(cost)))    
    
    # Ground the Program.
    print("c ├─ Grounding the logic program.")
    control.ground([("base", [])])

    # Define hat to do with answer sets.
    torso = []
    def model_callback(model):            
        torso.clear()
        for a in [atom for atom in model.symbols(shown=True) if atom.name == "torso"]:
            torso.append(a.arguments[0].number)
        print(f"c ├─── Found a new torso of size {len(torso)}.")

    # Pack everything to a function ...
    def solver(control, model_callback):
        control.solve(on_model = model_callback)

    # .. and execute it in a thread with the given timeout.
    print("c ├─ Computing the real torso with Clingo.")
    t = threading.Thread(target=solver, args=(control, model_callback))
    t.start()
    t.join(timeout)
    control.interrupt()
    t.join()          

    # done
    return torso

def _pretorso(g, k):
    """
    Computes a pre torso in which we search the real torso via ASP.
    The pre torso is a graph obtained by a subset of vertices of g selected by a heuristic.
    Components outside of this selection are made into cliques.
    """   
    # Select k vertices with small degree to the previously selected nodes and high degree to the others.
    print("c ├─ Computing nodes of the pre torso.")
    candidates = set()
    scores     = [0]
    queue      = tms.PriorityQueue()
    for v in g.nodes:
        while len(scores) < v+1:
            scores.append(0)
        scores[v] = g.degree(v)
        queue.push(v, scores[v])

    while len(candidates) < k:
        v = None        
        while not queue.is_empty():
            v, score = queue.pop()
            if score == scores[v]:
                break # otherwise the this is an outdated element
        if v is None:
            break # queue did not contain any remaining elements
        if v in candidates:
            continue
        candidates.add(v)
        for w in g.neighbors(v):
            scores[w] -= 2 # We reduce two, to punish edges within the candidates
            queue.push(w, scores[w])
        
    # Computing the torso graph of these vertices.
    pretorso = nx.Graph(g.subgraph(candidates))
    t = nx.Graph(g)
    t.remove_nodes_from(candidates)
    for c in nx.connected_components(t):
        for (u,v) in itertools.combinations(tms._neighbors_of_set_in(g, c, candidates), 2):
                pretorso.add_edge(u, v)            

    print(f"c ├─ Computed a pre torso with {len(pretorso.nodes)} vertices and {len(pretorso.edges)} edges.")
    return pretorso

def _graph2structure(graph):
    facts = []

    for node in graph.nodes:
        facts.append(f"node({node}).")

    for edge in graph.edges:
        facts.append(f"edge({edge[0]}, {edge[1]}).")

    return "\n".join(facts)
