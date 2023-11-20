# TorsoMaxSAT
A MaxSAT solver based on Tree Decompositions of the Torso Graph.

# Run Examples

You can run the solver (with some of the provided examples) as follows:
```
xz -cd examples/<file> | python main.py
```
In TorsoMaxSAT you have the option to chose one of multiple predefined
solvers via:
```
xz -cd examples/<file> | python main.py -s <solver>
```

Where `<solver>` is one of `gurobi`, `scip`, `rc2`, `hs`, `fm`, `ortools`,
or `dp`. Alternatively, `<solver>` can also be a command used to
execute an external solver.


## Use an External Treewidth Solver
TorsoMaxSAT computes tree decompositions by default with [NetworkX](https://networkx.org).
However, it supports external treewidth solvers that are that are compatible with the PACE format:

```
xz -cd examples/<file> | python main.py -s db --twsolver <cmd>
```
Here, `<cmd>` is the command that should be executed to run the external treewidth solver.

## Preprocessing
TorsoMaxSAT supports the MaxSAT preprocessor
[maxpre2](https://bitbucket.org/coreo-group/maxpre2). By providing a
path to the executable, all implemented solvers will operate on a
preprocessed formula:
```
xz -cd examples/<file> | python main.py --maxpre <path to maxpre executable>
```
Currently, we do not support configurations of maxpre but use a
carefully chosen setting tailored toward a decomposition-guided
approach. In particular, `<path to maxpre executable>` should indeed
map to the executable and should not contain any flags or options. 

# Install the Conda Environment
After having downloaded the repository and moved to its root, you can
install your conda environment as follows: 

```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda env create -f environment.yml
```

# Additional Packages

The following packages need to be installed addionaly via `pip`:

```
pip install gurobipy
pip install 'python-sat[aiger,approxmc,pblib]'
pip install ortools
```

# Updating the Conda Environment
```
conda env update --file environment.yml --prune
```

# Testing the Solver
Run the following command to see if the installation works as intended:
```
python -m unittest -v
```

