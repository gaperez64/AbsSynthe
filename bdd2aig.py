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

import aig
import bdd


def get_optimized_and_lit(a_lit, b_lit):
    if a_lit == 0 or b_lit == 0:
        return 0
    if a_lit == 1 and b_lit == 1:
        return 1
    if a_lit == 1:
        return b_lit
    if b_lit == 1:
        return a_lit
    if a_lit > 1 and b_lit > 1:
        a_b_lit = aig.next_lit()
        aig.add_gate(a_b_lit, a_lit, b_lit)
        return a_b_lit
    assert 0, 'impossible'


bdd_gate_cache = dict()


def bdd2aig(a_bdd):
    global bdd_gate_cache
    """
    Walk given BDD node (recursively).  If given input BDD requires
    intermediate AND gates for its representation, the function adds them.
    Literal representing given input BDD is `not` added to the spec.
    """
    if a_bdd in bdd_gate_cache:
        return bdd_gate_cache[a_bdd]

    if a_bdd.is_constant():
        res = int(a_bdd == bdd.true())   # in aiger 0/1 = False/True
        return res
    # get an index of variable,
    # all variables used in bdds also introduced in aiger,
    # except fake error latch literal,
    # but fake error latch will not be used in output functions (at least we
    # don't need this..)
    a_lit = a_bdd.get_index()
    assert (a_lit != aig.error_fake_latch.lit), ("using error latch in the " +
                                                 "definition of output " +
                                                 "function is not allowed")
    t_bdd = a_bdd.then_child()
    e_bdd = a_bdd.else_child()
    t_lit = bdd2aig(t_bdd)
    e_lit = bdd2aig(e_bdd)
    # ite(a_bdd, then_bdd, else_bdd)
    # = a*then + !a*else
    # = !(!(a*then) * !(!a*else))
    # -> in general case we need 3 more ANDs
    a_t_lit = get_optimized_and_lit(a_lit, t_lit)
    na_e_lit = get_optimized_and_lit(aig.negate_lit(a_lit), e_lit)
    n_a_t_lit = aig.negate_lit(a_t_lit)
    n_na_e_lit = aig.negate_lit(na_e_lit)
    ite_lit = get_optimized_and_lit(n_a_t_lit, n_na_e_lit)
    res = aig.negate_lit(ite_lit)
    if a_bdd.is_complement():
        res = aig.negate_lit(res)
    # cache result
    bdd_gate_cache[a_bdd] = res
    return res
