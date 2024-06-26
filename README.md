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

## Using Subsolvers

If TorsoMaxSAT is used with option `-s dp` the instance is solved with a dynamic program on the formulas torso, whereby subinstances are solved with another solver (called subsolver). This subsolver can be specifed via `--subsolver <solver>` with the same options as for `-s`. For instance:

```
xz -dc examples/<file>  | python main.py -s dp --subsolver rc2 
```

## Use an External Treewidth Solver
TorsoMaxSAT computes tree decompositions by default with [NetworkX](https://networkx.org).
However, it supports external treewidth solvers that are compatible with the PACE format:

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

# Reference

If you use TorsoMaxSAT in your research, please cite the corresponding
paper:

```
@inproceedings{BannachH24,
  author       = {Max Bannach and
                  Markus Hecher},
  title        = {Structure-Guided Cube-and-Conquer for MaxSAT},
  booktitle    = {{NASA} Formal Methods - 16th International Symposium, {NFM} 2024,
                  Moffett Field, CA, USA, June 4-6, 2024, Proceedings},
  pages        = {3--20},
  year         = {2024},
  doi          = {10.1007/978-3-031-60698-4\_1},
}
```

