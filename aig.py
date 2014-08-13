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


def introduce_error_latch(after_intro=None):
    global error_fake_latch

    if error_fake_latch is not None:
        return
    error_fake_latch = new_aiger_symbol()
    error_symbol = get_err_symbol()
    error_fake_latch.lit = next_lit()
    error_fake_latch.name = "fake_error_latch"
    error_fake_latch.next = error_symbol.lit
    # if after_intro was provided we shall call it
    if after_intro is not None:
        after_intro(error_fake_latch)


def parse_into_spec(aiger_file_name, intro_error_latch=False,
                    after_intro=None):
    global spec

    spec = aiger_init()
    err = aiger_open_and_read_from_file(spec, aiger_file_name)
    assert not err, err
    # if required, introduce a fake latch for the error and call the given hook
    introduce_error_latch(after_intro)


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
            result = rec_dependencies(a.rhs0) | rec_dependencies(a.rhs1)
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
