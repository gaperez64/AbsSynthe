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

from aiger_swig.aiger_wrap import (
    get_aiger_symbol,
    aiger_init,
    aiger_open_and_read_from_file,
    aiger_is_input,
    aiger_is_latch,
    aiger_is_and,
    aiger_add_and,
    aiger_symbol,
    aiger_open_and_write_to_file,
    #aiger_write_to_string,
    aiger_redefine_input_as_and,
    #aiger_ascii_mode
)
import sat
import bdd
import log


# global variables to keep a spec and a fake latch for the error bit
spec = None
error_fake_latch = None


def new_aiger_symbol():
    return aiger_symbol()


def num_latches():
    return spec.num_latches


def max_var():
    return int(spec.maxvar) * 2


def next_lit():
    return (int(spec.maxvar) + 1) * 2


def negate_lit(l):
    return l ^ 1


def lit_is_negated(l):
    return (l & 1) == 1


def strip_lit(l):
    return l & ~1


def iterate_latches():
    for i in range(int(spec.num_latches)):
        yield get_aiger_symbol(spec.latches, i)
    if error_fake_latch is not None:
        yield error_fake_latch


def introduce_error_latch(using_bdds=False):
    global error_fake_latch

    if error_fake_latch is not None:
        return
    error_fake_latch = new_aiger_symbol()
    error_symbol = get_err_symbol()
    error_fake_latch.lit = next_lit()
    error_fake_latch.name = "fake_error_latch"
    error_fake_latch.next = error_symbol.lit
    # lets save two variables for error and primed version
    # this also saves all variables <= error_symbol.lit + 1
    # for CONCRETE variables
    bdd.BDD(error_fake_latch.lit)
    bdd.BDD(get_primed_var(error_fake_latch.lit))


def parse_into_spec(aiger_file_name, intro_error_latch=False,
                    after_intro=None):
    global spec

    spec = aiger_init()
    err = aiger_open_and_read_from_file(spec, aiger_file_name)
    assert not err, err
    # if required, introduce a fake latch for the error and call the given hook
    if intro_error_latch:
        introduce_error_latch(after_intro)
    # dump some info about the spec
    log.DBG_MSG("AIG spec file parsed")
    log.LOG_MSG("Nr. of latches: " + str(num_latches()))
    log.DBG_MSG("Latches: " + str([x.lit for x in
                                   iterate_latches()]))
    log.DBG_MSG("U. Inputs: " + str([x.lit for x in
                                     iterate_uncontrollable_inputs()]))
    log.DBG_MSG("C. Inputs: " + str([x.lit for x in
                                     iterate_controllable_inputs()]))


def change_input_to_and(c_lit, func_as_aiger_lit):
    aiger_redefine_input_as_and(spec, c_lit,
                                func_as_aiger_lit, func_as_aiger_lit)


def write_spec(out_file):
    aiger_open_and_write_to_file(spec, out_file)


def get_lit_type(lit):
    stripped_lit = strip_lit(lit)
    if error_fake_latch is not None and stripped_lit == error_fake_latch.lit:
        return None, error_fake_latch, None

    input_ = aiger_is_input(spec, stripped_lit)
    latch_ = aiger_is_latch(spec, stripped_lit)
    and_ = aiger_is_and(spec, stripped_lit)

    return input_, latch_, and_


def lit_is_and(lit):
    (i, l, a) = get_lit_type(lit)
    return a


def get_err_symbol():
    assert spec.num_outputs == 1
    return spec.outputs
    # swig return one element instead of array, to iterate over array use
    # iterate_symbols


def add_gate(fresh_var, conjunct1, conjunct2):
    return aiger_add_and(spec, fresh_var, conjunct1, conjunct2)


def _iterate_inputs(filter_func):
    for i in range(int(spec.num_inputs)):
        input_aiger_symbol = get_aiger_symbol(spec.inputs, i)
        if filter_func(input_aiger_symbol.name.strip()):
            yield input_aiger_symbol


def iterate_uncontrollable_inputs():
    for i in _iterate_inputs(lambda name: not name.startswith("controllable")):
        yield i


def iterate_controllable_inputs():
    for i in _iterate_inputs(lambda name: name.startswith("controllable")):
        yield i


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
        a_b_lit = next_lit()
        add_gate(a_b_lit, a_lit, b_lit)
        return a_b_lit
    assert 0, 'impossible'


def latch_dependency_map():
    m = {}
    cache = {}

    # recursive worker
    def _rec_dependencies(lit):
        if lit in cache:
            return cache[lit]
        (i, l, a) = get_lit_type(lit)
        # latches count towards one
        if l:
            result = set([l.lit])
        # ands require union of siblings
        elif a:
            result = _rec_dependencies(a.rhs0) | _rec_dependencies(a.rhs1)
        # inputs or terminals
        else:
            result = set([])

        cache[lit] = result
        return result

    # call the recursive worker for each gate with the next step
    # value of a latch and map the sets to each latch lit
    for l in iterate_latches():
        m[l.lit] = _rec_dependencies(l.next)
    return m


# very important for BDD and CNF translations, we need this to be uniform and
# consistent
# WARNING: I am not returning the literal with the same sign as the incoming
# literal
def get_primed_var(lit):
    return strip_lit(lit) + 1


###################### BDD stuff ################
lit_to_bdd = dict()
bdd_to_lit = dict()


def get_bdd_for_lit(lit):
    """ Convert AIGER lit into BDD """
    # query cache
    if lit in lit_to_bdd:
        return lit_to_bdd[lit]
    # get stripped lit
    stripped_lit = strip_lit(lit)
    (intput, latch, and_gate) = get_lit_type(stripped_lit)
    # is it an input, latch, gate or constant
    print lit
    if intput or latch:
        print "input or latch"
        result = bdd.BDD(stripped_lit)
    elif and_gate:
        print "gate"
        result = (get_bdd_for_lit(and_gate.rhs0) &
                  get_bdd_for_lit(and_gate.rhs1))
    else:  # 0 literal, 1 literal and errors
        print "terminal"
        result = bdd.false()
    # cache result
    lit_to_bdd[stripped_lit] = result
    bdd_to_lit[result] = stripped_lit
    # check for negation
    if lit_is_negated(lit):
        result = ~result
        lit_to_bdd[lit] = result
        bdd_to_lit[result] = lit
    return result


cached_transition = None


def trans_rel_BDD():
    global cached_transition

    # check cache
    if cached_transition:
        return cached_transition
    b = bdd.true()
    for x in iterate_latches():
        b &= bdd.make_eq(bdd.BDD(get_primed_var(x.lit)),
                         get_bdd_for_lit(x.next))
    cached_transition = b
    log.BDD_DMP(b, "Composed and cached the concrete transition relation")
    return b


###################### CNF stuff ################
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
        (i, l, a) = get_lit_type(lit)
        # base cases: inputs or latches
        if l or i:
            result = (set([lit]), set())
        # ands require we recurse if the sibling is not negated
        elif a:
            if lit_is_negated(a.rhs0) and lit_is_and(a.rhs0):
                x = strip_lit(a.rhs0)
                result0 = (set([x * -1]), set([x]))
            else:
                result0 = _rec_dfs(a.rhs0)
            if lit_is_negated(a.rhs1) and lit_is_and(a.rhs1):
                x = strip_lit(a.rhs1)
                result1 = (set([x * -1]), set([x]))
            else:
                result1 = _rec_dfs(a.rhs1)

            result = tuple(map(set.union, result0, result1))
        # terminals
        else:
            assert lit_is_negated(lit)
            result = (set(), set())
        cache[lit] = result
        return result

    # initialize sub tree list with latches
    # TODO: handle latches.next being other stuff than just and gates...
    sub_trees = set([(get_primed_var(x.lit) * -1, strip_lit(x.next))
                     if lit_is_negated(x.next) and x.next > 1
                     else (get_primed_var(x.lit), strip_lit(x.next))
                     for x in iterate_latches()])
    # call _rec_dfs for each sub tree
    T = sat.CNF()
    while sub_trees:
        (o, x) = sub_trees.pop()
        (v, t) = _rec_dfs(abs(x))
        T.add_land(o, v)
        sub_trees |= set([(y, y) for y in t])

    cached_tr_cnf = T
    return T


cached_unrolled = {}


def unroll_CNF(n):
    assert n >= 1

    # we need the transition relation CNF and we will copy it n times
    # and make latch variables match, we will also return a map of the
    # variables to the renamed version

    mv = max_var() + 2  # +2 to make space for the negation of the last var
    T = trans_rel_CNF()
    trash_vars = T.literals() - set([x.lit for x in iterate_latches()] +
                                    [x.next for x in
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
                           [(x.next, x.next)
                            for x in iterate_latches()] +
                           [(x.lit, x.lit)
                            for x in iterate_controllable_inputs()] +
                           [(x.lit, x.lit)
                            for x in iterate_uncontrollable_inputs()] +
                           [(x, x) for x in trash_vars])
            form = sat.CNF().append_cnf(T)
        else:
            (form, var_map) = _rec_unroll(n - 1)
            var_map = dict([(x.lit, var_map[x.next])
                            for x in iterate_latches()] +
                           [(x.next, var_map[x.next] + mv)
                            for x in iterate_latches()] +
                           [(x.lit, var_map[x.lit] + mv)
                            for x in iterate_controllable_inputs()] +
                           [(x.lit, var_map[x.lit] + mv)
                            for x in iterate_uncontrollable_inputs()] +
                           [(x, var_map[x] + mv) for x in trash_vars])
            form.append_cnf(
                sat.CNF().append_cnf(T).rename_vars(var_map))
            cached_unrolled[n] = (form, var_map)
        return (form, var_map)

    (form, var_map) = _rec_unroll(n)
    return (form, [cached_unrolled[i][1] for i in cached_unrolled])
