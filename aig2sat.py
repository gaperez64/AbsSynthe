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

from aig import (
    lit_is_negated,
    get_lit_type,
    strip_lit,
    introduce_error_latch,
    iterate_latches,
    get_primed_var,
    max_var,
    iterate_controllable_inputs,
    iterate_uncontrollable_inputs,
    get_1l_land
)
import sat


###################### CNF stuff ################
def get_mand(lit):
    (A, B) = get_1l_land(lit)
    A2 = set(map(A, lambda x: strip_lit(x) * -1
                 if lit_is_negated(x)
                 else x))
    return (A2, B)


cached_tr_cnf = None


def trans_rel_CNF():
    global cached_tr_cnf
    # we create a fake latch for the error
    introduce_error_latch()

    if cached_tr_cnf is not None:
        return cached_tr_cnf

    # per latch, handle the next function
    T = sat.CNF()
    for l in iterate_latches():
        # easy case, the latch just directly maps input or terminal
        (ii, ll, a) = get_lit_type(l.next)
        if not a:
            if l.next == 0 or l.next == 1:  # is it a terminal?
                T.add_mand(get_primed_var(l.lit), [l.next])
            else:  # otherwise
                x = strip_lit(l.next) * -1 if lit_is_negated(l.next)\
                    else strip_lit(l.next)
                T.add_mand(get_primed_var(l.lit), [x])
        else:  # complicated case, l.next is an AND
            if lit_is_negated(l.next):
                A = set([strip_lit(l.next) * -1])
                B = set([strip_lit(l.next)])
            else:
                (A, B) = get_mand(l.next)
            T.add_mand(get_primed_var(l.lit), A)
            pending = B
            # handle CNF for each pending gate
            while pending:
                cur = pending.pop()
                (A, B) = get_mand(cur)
                pending |= B
                T.add_mand(cur, A)
    # handle caching
    cached_tr_cnf = T
    return T


cached_unrolled = {}


def unroll_CNF(n):
    assert n >= 1

    # we need the transition relation CNF and we will copy it n times
    # and make latch variables match, we will also return a map of the
    # variables to the renamed version

    mv = max_var() + 4  # space for negation of last var & fake error latch
    T = trans_rel_CNF()
    trash_vars = T.literals() - set([x.lit for x in iterate_latches()] +
                                    [get_primed_var(x.lit) for x in
                                        iterate_controllable_inputs()] +
                                    [x.lit for x in
                                        iterate_controllable_inputs()] +
                                    [x.lit for x in
                                        iterate_uncontrollable_inputs()])

    # recursive handling
    def _rec_unroll(n):
        global cached_unrolled
        if n in cached_unrolled:
            return cached_unrolled[n]

        if n == 0:
            var_map = dict([(x.lit, x.lit)
                            for x in iterate_latches()] +
                           [(get_primed_var(x.lit), get_primed_var(x.lit))
                            for x in iterate_latches()] +
                           [(x.lit, x.lit)
                            for x in iterate_controllable_inputs()] +
                           [(x.lit, x.lit)
                            for x in iterate_uncontrollable_inputs()] +
                           [(x, x) for x in trash_vars])
            form = sat.CNF().append_cnf(T)
        else:
            (form, var_map) = _rec_unroll(n - 1)
            var_map = dict([(x.lit, var_map[x.lit])
                            for x in iterate_latches()] +
                           [(get_primed_var(x.lit),
                             var_map[get_primed_var(x.lit)] + mv)
                            for x in iterate_latches()] +
                           [(x.lit, var_map[x.lit] + mv)
                            for x in iterate_controllable_inputs()] +
                           [(x.lit, var_map[x.lit] + mv)
                            for x in iterate_uncontrollable_inputs()] +
                           [(x, var_map[x] + mv) for x in trash_vars])
            form.append_cnf(T.rename_vars(var_map))
            cached_unrolled[n] = (form, var_map)
        return (form, var_map)

    (form, var_map) = _rec_unroll(n)
    return (form, [cached_unrolled[i][1] for i in cached_unrolled])
