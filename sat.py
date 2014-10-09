"""
Copyright (c) 2014, Guillermo A. Perez, Universite Libre de Bruxelles

This file is part of the AbsSynthe tool.

AbsSynthe is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

AbsSynthe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with AbsSynthe.  If not, see <http://www.gnu.org/licenses/>.


Guillermo A. Perez
Universite Libre de Bruxelles
gperezme@ulb.ac.be
"""

from math import copysign
import pycosat
import bdd
import log


class CNF:
    """ A CNF object: set of frozensets """
    clauses = set()

    def __init__(self):
        self.clauses = set()

    def literals(self):
        return set([x * -1 if x < 0 else x
                    for x in frozenset.union(*self.clauses)])

    def to_string(self):
        return " ".join(["(" + " ".join(map(str, x)) + ")"
                         for x in self.clauses])

    def sat_solve(self):
        result = pycosat.solve([[y for y in x] for x in self.clauses])
        return False if result == "UNSAT" else result

    def iter_solve(self):
        result = pycosat.itersolve([[y for y in x] for x in self.clauses])
        return False if result == "UNSAT" else result

    def add_clause(self, lits, avoid_checks=False):
        # just a simple check to get rid of False in clauses and clauses that
        # are trivially true
        if 1 in lits:
            log.DBG_MSG("The clause includes lit 1. It is trivially true.")
            return self
        if 0 in lits:
            log.DBG_MSG("The clause includes lit 0. I removed it.")
            lits = [l for l in lits if l != 0]
#        if not avoid_checks:
#            if next((c for c in self.clauses if c <= lits), None):
#                log.DBG_MSG("The clause is subsumed by an existing one.")
#                return
#            self.clauses = set(filter(lambda x: not lits <= x, self.clauses))
        self.clauses.add(frozenset(lits))
        return self

    def add_cube(self, lits):
        for l in lits:
            self.add_clause([l])
        return self

    def append_clauses(self, clauses):
        for c in clauses:
            self.add_clause(c)
        return self

    def append_cnf(self, cnf):
        self.append_clauses(cnf.clauses)
        return self

    def remove_clauses(self, clauses):
        self.clauses = set(filter(lambda x: x not in clauses, self.clauses))
        return self

    def remove_cnf(self, cnf):
        self.remove_clauses(cnf.clauses)
        return self

    # add clauses for a boolean formula of the form l <=> AND(x0,x1,..,xn)
    # where xi could be a negated literal
    def add_mand(self, o, lits):
        assert 0 not in lits
        clean_lits = frozenset(set(lits) - set([1]))
        for l in clean_lits:
            self.add_clause([l, o * -1], True)
        self.add_clause([o] + map(lambda x: x * -1, clean_lits))
        return self

    def rename_vars(self, name_map):
        self.clauses = set(
            frozenset([int(copysign(name_map[abs(y)], y))
                       for y in x if abs(y) in name_map])
            for x in self.clauses)
        return self

    def to_bdd(self):
        b = bdd.true()
        for c in self.clauses:
            nu_clause = bdd.false()
            for l in c:
                nu_var = bdd.BDD(abs(l))
                if l < 0:
                    nu_var = ~nu_var
                nu_clause |= nu_var
            b &= nu_clause
        return b
