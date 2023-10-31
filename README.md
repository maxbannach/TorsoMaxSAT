# TorsoMaxSAT
A MaxSAT solver based on Tree Decompositions of the Torso Graph.

# Run Examples

You can run the solver (with some of the provided examples) as follows:
```
xz -cd examples/<file> | python main.py -s <solver>
```
Where `<solver>` is one of `gurobi`, `scip`, `sc2`, or `fm`. 


# Install the Conda Environment
After having downloaded the repository and moved to its root, you can install your conda environment as follows:

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
```

# Updating the Conda Environment
```
conda env update --file environment.yml --prune
```

