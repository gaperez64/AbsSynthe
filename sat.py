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

import math
import pycosat
#import log
import aig


class CNF:
    """ A CNF object: set of frozensets """
    clauses = set()

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
        result = pycosat.itersolve(self.clauses)
        return False if result == "UNSAT" else result

    def add_clause(self, lits, avoid_checks=False):
        lits = frozenset(lits)
        if not avoid_checks:
            if next((c for c in self.clauses if c <= lits), None):
                return
            self.clauses = set(filter(lambda x: not lits <= x, self.clauses))
        self.clauses.add(lits)
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
    def add_land(self, o, lits):
        for l in lits:
            self.add_clause([l, o * -1], True)
        self.add_clause([o] + map(lambda x: x * -1, lits))
        return self

    def rename_vars(self, name_map):
        self.clauses = set(
            frozenset([int(math.copysign(name_map[abs(y)], y))
                       for y in x if abs(y) in name_map])
            for x in self.clauses)
        return self


cached_unrolled = {}


def unroll_CNF(n):
    assert n >= 1

    # we need the transition relation CNF and we will copy it n times
    # and make latch variables match, we will also return a map of the
    # variables to the renamed version

    mv = aig.max_var()
    T = trans_rel_CNF()
    trash_vars = T.literals() - set([x.lit for x in aig.iterate_latches()] +
                                    [x.next for x in
                                        aig.iterate_controllable_inputs()] +
                                    [x.lit for x in
                                        aig.iterate_controllable_inputs()] +
                                    [x.lit for x in
                                        aig.iterate_uncontrollable_inputs()])

    # recursive handling
    def _rec_unroll(n):
        global cached_unrolled
        if n in cached_unrolled:
            return cached_unrolled[n]

        if n == 0:
            var_map = dict([(x.lit, x.lit)
                            for x in aig.iterate_latches()] +
                           [(x.next, x.next)
                            for x in aig.iterate_latches()] +
                           [(x.lit, x.lit)
                            for x in aig.iterate_controllable_inputs()] +
                           [(x.lit, x.lit)
                            for x in aig.iterate_uncontrollable_inputs()] +
                           [(x, x) for x in trash_vars])
            form = CNF().append_cnf(T)
        else:
            (form, var_map) = _rec_unroll(n - 1)
            var_map = dict([(x.lit, var_map[x.next])
                            for x in aig.iterate_latches()] +
                           [(x.next, var_map[x.next] + mv)
                            for x in aig.iterate_latches()] +
                           [(x.lit, var_map[x.lit] + mv)
                            for x in aig.iterate_controllable_inputs()] +
                           [(x.lit, var_map[x.lit] + mv)
                            for x in aig.iterate_uncontrollable_inputs()] +
                           [(x, var_map[x] + mv) for x in trash_vars])
            form.append_cnf(
                CNF().append_cnf(T).rename_vars(var_map))
            cached_unrolled[n] = (form, var_map)
        return (form, var_map)

    (form, var_map) = _rec_unroll(n)
    return (form, [cached_unrolled[i][1] for i in cached_unrolled])


cached_tr_cnf = None


def trans_rel_CNF():
    global cached_tr_cnf

    if cached_tr_cnf is not None:
        return cached_tr_cnf

    # We need to do a first pass to determine which variables are to be
    # created because a negation took place, we will also create the first
    # part of the formula on the way.
    cache = {}

    # returns the lits for the conjunction and a set of variables that have to
    # be further explored as a sub tree
    def _rec_dfs(lit):
        if lit in cache:
            return cache[lit]
        (i, l, a) = aig.get_lit_type(lit)
        # base cases: inputs or latches
        if l or i:
            result = (set([lit]), set())
        # ands require we recurse if the sibling is not negated
        elif a:
            if aig.lit_is_negated(a.rhs0) and aig.lit_is_and(a.rhs0):
                x = aig.strip_lit(a.rhs0)
                result0 = (set([x * -1]), set([x]))
            else:
                result0 = _rec_dfs(a.rhs0)
            if aig.lit_is_negated(a.rhs1) and aig.lit_is_and(a.rhs1):
                x = aig.strip_lit(a.rhs1)
                result1 = (set([x * -1]), set([x]))
            else:
                result1 = _rec_dfs(a.rhs1)

            result = tuple(map(set.union, result0, result1))
        # terminals
        else:
            assert aig.lit_is_negated(lit)
            result = (set(), set())
        cache[lit] = result
        return result

    # initialize sub tree list with latches
    sub_trees = set([x.next * -1 if aig.lit_is_negated(x.next) and x.next > 1
                     else x.next for x in aig.iterate_latches()])
    # call _rec_dfs for each sub tree
    T = CNF()
    while sub_trees:
        x = sub_trees.pop()
        (v, t) = _rec_dfs(abs(x))
        T.add_land(x, v)
        sub_trees |= t

    cached_tr_cnf = T
    return T
