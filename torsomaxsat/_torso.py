import clingo
from clingo import Control
import threading

clingo_program = """
% We can selected candidate vertices to the torso.
{ torso(X) : candidate(X) }.

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

def Torso(g, cost = 10, k = 50, timeout = 30):        
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

    # Add the the graph as relational structure, identify candidate vertices for the torso, and provide the logic program.
    control.add("base", [], _graph2structure(g))
    control.add("base", [], _candidates(g, k = k))
    control.add("base", [], clingo_program.replace("@cost", str(cost)))    

    # Ground the Program.
    control.ground([("base", [])])

    # Define hat to do with answer sets.
    torso = []
    def model_callback(model):            
        torso.clear()
        for a in [atom for atom in model.symbols(shown=True) if atom.name == "torso"]:
            torso.append(a.arguments[0].number)
        print(f"c Found a new torso of length {len(torso)}.")

    # Pack everything to a function ...
    def solver(control, model_callback):
        control.solve(on_model = model_callback)

    # .. and execute it in a thread with the given timeout.
    t = threading.Thread(target=solver, args=(control, model_callback))
    t.start()
    t.join(timeout)
    control.interrupt()
    t.join()          

    # done
    return torso

def _candidates(g, k = 50):
    candidates = []

    # The k nodes of minimum degree.
    degrees = dict(g.degree())
    for v in sorted(degrees, key=degrees.get)[:k]:
        candidates.append(f"candidate({v}).")
    
    return "\n".join(candidates)

def _graph2structure(graph):
    facts = []

    for node in graph.nodes:
        facts.append(f"node({node}).")

    for edge in graph.edges:
        facts.append(f"edge({edge[0]}, {edge[1]}).")

    return "\n".join(facts)
