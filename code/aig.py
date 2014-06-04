"""
Copyright (c) 2014, Guillermo A. Perez, Universite Libre de Bruxelles

This file is part of a the AbsSynthe tool.

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

spec = None


def new_aiger_symbol():
    return aiger_symbol()


def num_latches():
    return spec.num_latches


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


def parse_into_spec(aiger_file_name):
    global spec

    spec = aiger_init()
    err = aiger_open_and_read_from_file(spec, aiger_file_name)
    assert not err, err


def change_input_to_and(c_lit, func_as_aiger_lit):
    aiger_redefine_input_as_and(spec, c_lit,
                                func_as_aiger_lit, func_as_aiger_lit)


def write_spec(out_file):
    aiger_open_and_write_to_file(spec, out_file)


def get_lit_type(stripped_lit):
    input_ = aiger_is_input(spec, stripped_lit)
    latch_ = aiger_is_latch(spec, stripped_lit)
    and_ = aiger_is_and(spec, strip_lit(stripped_lit))

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
