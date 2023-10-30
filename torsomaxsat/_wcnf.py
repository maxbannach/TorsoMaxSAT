from torsomaxsat import BiMap

class WCNF:
    __slots__ = 'n', 'hard', 'soft', 'varmap'
    """
    A *weighted* formula in conjunctive normal form with support for
    floating point weights (including negative weights).

    Slots:
      n:       Number of variables in the formula (internally, the variables are 1...n).
      hard:    An array of hard clauses (every model needs to satisfy them).
      soft:    A map from (some) variables to weights. Variables occurring in the map are soft auxiliary literals introduced by this class.
      offset:  An value added to the value of the optimal model.
      varmap:  A BiMap from added variables to internal variables (needed, as auxiliary variables will be added on-the-fly).
    """

    def __init__(self):
        self.n       = 0
        self.hard    = []
        self.soft    = {}
        self.varmap  = BiMap()

    def _sign(self, l):
        """
        Returns the sign of a literal as 1 or -1.
        """
        return 1 if l >= 0 else -1 
        
    def _ensure_vars(self, clause):
        """
        Ensures that the variables of the given clause appear in the internal representation of the formula.
        """
        for l in filter(lambda l: not self.varmap.get_value(abs(l)), clause):
            self.n += 1
            self.varmap.insert( abs(l), self.n )                    
        
    def _to_internal(self, clause):
        """
        Returns the given clause in internal representation (which eventually renames the variables).
        """
        return list(map(lambda l: self._sign(l) * self.varmap.get_value(abs(l)), clause))

    def _to_external(self, clause):
        """
        Returns the given clause in the original representation (that is, with the original variable names).
        This function will also remove auxiliary variables from the clause.
        """
        return list(map(
            lambda l: self._sign(l) * self.varmap.get_key(abs(l)),
            filter(lambda l: self.varmap.get_key(abs(l)), clause)
        ))

    def _get_weight(self, clause):
        """
        Returns the weight of a clause in internal representation.
        If the clause has no weight (i.e., if it is hard), this will return float("inf").
        """
        try:
            soft_literal = next(filter(lambda l: self.soft.get(abs(l)), clause))
            return self.soft[abs(soft_literal)]        
        except StopIteration:
            return float("inf")
    
    def add_clause( self, clause, weight = None ):
        """
        Add a clause to the formula. If no weight is given, the clause
        is added as *hard* clause. If a weight is specified, the clause is *soft*.

        Example:
        ```
        phi = WCNF()
        phi.add_clause( [1,-2,3] ) # add a hard clause
        phi.add_clause( [1,-2,3], weight = -0.3 ) # add a soft clause
        ```

        If a non-unit soft clause is added, it will be added as hard clause with a fresh variable, whose
        negation is then added as unit soft clause.        
        """        
        self._ensure_vars( clause )
        clause = self._to_internal(clause)
        if weight:
            self.n += 1
            clause.append(-self.n)
            self.soft[self.n] = weight
            
        self.hard.append(clause)

    def __str__(self):
        """
        Prints the clause in the new DIMACS format (used since 2022).
        """
        buffer = []
        for c in self.hard:
            w = self._get_weight(c)
            if w == float("inf"):
                w = "h"
            c = self._to_external(c)
            buffer.append(f"{w} {' '.join(map(str,c))} 0")            
        return "\n".join(buffer)
