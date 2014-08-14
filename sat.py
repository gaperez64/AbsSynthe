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

#import pycosat
import log
import aig


class CNF:
    """ A CNF object """
    clauses = []

    def add_clause(lits):
        clauses.append(lits)

    def add_land(o, lits):




cached_tr_cnf = None


def trans_rel_CNF():
    global cached_tr_cnf

    if cached_tr_cnf is not None:
        return cached_tr_cnf

    next_v = aig.max_var() + 2
    cache = {}

    def _rec_lit_cnf(lit):
        if lit in cache:
            return cache[lit]

        (i, l, a) = get_lit_type(lit)
        # base cases: inputs or latches
        if l or i:
            result = (l.lit, [[l.lit]])
        # ands require union of siblings
        elif a:
            result = rec_dependencies(a.rhs0) | rec_dependencies(a.rhs1)
        # inputs or terminals
        else:
            result = set([])
        cache[lit] = result
        return result

    cached_tr_cnf = c
    return c
