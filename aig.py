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
    aiger_add_output,
    aiger_symbol,
    aiger_open_and_write_to_file,
    aiger_redefine_input_as_and,
    aiger_remove_outputs,
)
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
    return (int(spec.maxvar) + 2) * 2


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


def introduce_error_latch():
    global error_fake_latch

    if error_fake_latch is not None:
        return
    error_fake_latch = new_aiger_symbol()
    error_symbol = get_err_symbol()
    error_fake_latch.lit = next_lit()
    error_fake_latch.name = "fake_error_latch"
    error_fake_latch.next = error_symbol.lit


def parse_into_spec(aiger_file_name, intro_error_latch=False):
    global spec

    spec = aiger_init()
    err = aiger_open_and_read_from_file(spec, aiger_file_name)
    assert not err, err
    # if required, introduce a fake latch for the error and call the given hook
    if intro_error_latch:
        introduce_error_latch()
    # dump some info about the spec
    log.DBG_MSG("AIG spec file parsed")
    log.DBG_MSG("Latches: " + str([x.lit for x in
                                   iterate_latches()]))
    log.DBG_MSG("U. Inputs: " + str([x.lit for x in
                                     iterate_uncontrollable_inputs()]))
    log.DBG_MSG("C. Inputs: " + str([x.lit for x in
                                     iterate_controllable_inputs()]))


def input2and(c_lit, func_as_aiger_lit):
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


def add_output(lit, name):
    return aiger_add_output(spec, lit, name)


def remove_outputs():
    return aiger_remove_outputs(spec)


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


def symbol_lit(x):
    return x.lit


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
