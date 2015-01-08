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

from itertools import ifilter
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
import log


class AIG:
    def num_latches(self):
        return self.spec.num_latches

    def max_var(self):
        return int(self.spec.maxvar)

    def next_lit(self):
        return (int(self.spec.maxvar) + 1) * 2

    def iterate_latches(self):
        for i in range(int(self.spec.num_latches)):
            yield get_aiger_symbol(self.spec.latches, i)
        if self.error_fake_latch is not None:
            yield self.error_fake_latch

    def introduce_error_latch(self):
        if self.error_fake_latch is not None:
            return
        self.error_fake_latch = new_aiger_symbol()
        error_symbol = self.get_err_symbol()
        self.error_fake_latch.lit = self.next_lit()
        self.error_fake_latch.name = "fake_error_latch"
        self.error_fake_latch.next = error_symbol.lit
        log.DBG_MSG("Error fake latch = " + str(self.error_fake_latch.lit))

    def replace_error_function(self, e):
        self.ntroduce_error_latch()
        self.error_fake_latch.next = e

    def __init__(self, aiger_file_name, intro_error_latch=False):
        self.spec = aiger_init()
        err = aiger_open_and_read_from_file(self.spec, aiger_file_name)
        assert not err, err
        # introduce a fake latch for the error and call the given hook
        self.error_fake_latch = None
        if intro_error_latch:
            self.introduce_error_latch()
        # initialize caches
        self._1l_land_cache = dict()
        self._deps_cache = dict()
        # dump some info about the spec
        if not log.debug:
            return
        latches = [x.lit for x in self.iterate_latches()]
        log.DBG_MSG(str(len(latches)) + " Latches: " + str(latches))
        uinputs = [x.lit for x in self.iterate_uncontrollable_inputs()]
        log.DBG_MSG(str(len(uinputs)) + " U. Inputs: " + str(uinputs))
        cinputs = [x.lit for x in self.iterate_controllable_inputs()]
        log.DBG_MSG(str(len(cinputs)) + " C. Inputs: " + str(cinputs))

    def input2and(self, c_lit, func_as_aiger_lit):
        aiger_redefine_input_as_and(self.spec, c_lit,
                                    func_as_aiger_lit, func_as_aiger_lit)

    def write_spec(self, out_file):
        aiger_open_and_write_to_file(self.spec, out_file)

    def get_lit_type(self, lit):
        stripped_lit = strip_lit(lit)
        if (self.error_fake_latch is not None and
                stripped_lit == self.error_fake_latch.lit):
            return None, self.error_fake_latch, None
        input_ = aiger_is_input(self.spec, stripped_lit)
        latch_ = aiger_is_latch(self.spec, stripped_lit)
        and_ = aiger_is_and(self.spec, stripped_lit)
        return input_, latch_, and_

    def get_lit_name(self, lit):
        (i, l, a) = self.get_lit_type(lit)
        if i:
            return i.name
        if l:
            return l.name
        if a:
            return str(lit)
        assert False

    def lit_is_and(self, lit):
        (i, l, a) = self.get_lit_type(lit)
        return a

    def get_err_symbol(self):
        assert self.spec.num_outputs == 1
        return self.spec.outputs

    def add_gate(self, fresh_var, conjunct1, conjunct2):
        return aiger_add_and(self.spec, fresh_var, conjunct1, conjunct2)

    def add_output(self, lit, name):
        return aiger_add_output(self.spec, lit, name)

    def remove_outputs(self):
        return aiger_remove_outputs(self.spec)

    def _iterate_inputs(self):
        for i in range(int(self.spec.num_inputs)):
            yield get_aiger_symbol(self.spec.inputs, i)

    def iterate_uncontrollable_inputs(self):
        return ifilter(lambda sym: not sym.name.startswith("controllable"),
                       self._iterate_inputs())

    def iterate_controllable_inputs(self):
        return ifilter(lambda sym: sym.name.startswith("controllable"),
                       self._iterate_inputs())

    # returns the set A = {a_0,a_1,...} from the expression AND(a_0,a_1,...)
    # and a subset B <= A of the latches that were not completely explored
    def get_1l_land(self, lit):
        assert not lit_is_negated(lit) and self.lit_is_and(lit)
        if lit in self._1l_land_cache:
            return self._1l_land_cache[lit]
        # init variables
        A = set()
        B = set()
        # put first lit in the wait queue
        waiting = [lit]
        while waiting:
            lit = waiting.pop()
            a = self.lit_is_and(lit)
            # base cases: children are leaves
            if not self.lit_is_and(a.rhs0):
                A.add(a.rhs0)
            elif lit_is_negated(a.rhs0):  # AND with negation
                A.add(a.rhs0)
                B.add(strip_lit(a.rhs0))
            else:  # recursive case: AND gate without negation
                waiting.append(a.rhs0)
            # symmetric handling for a.rhs1
            # base cases: children are leaves
            if not self.lit_is_and(a.rhs1):
                A.add(a.rhs1)
            elif lit_is_negated(a.rhs1):  # AND with negation
                A.add(a.rhs1)
                B.add(strip_lit(a.rhs1))
            else:  # recursive case: AND gate without negation
                waiting.append(a.rhs1)
        # cache handling
        self._1l_land_cache[lit] = (A, B)
        return (A, B)

    def get_mult_lit_deps(self, lits):
        visited = dict()
        waiting = set(lits)
        deps = set()
        while waiting:
            lit = waiting.pop()
            if lit in visited:
                continue
            visited[lit] = True
            (i, l, a) = self.get_lit_type(lit)
            # latches count towards one
            if l:
                deps.add(l.lit)
                waiting.add(l.next)
            # ands require union of siblings
            elif a:
                waiting |= set([a.rhs0, a.rhs1])
            # inputs
            elif i:
                deps.add(i.lit)
            # 0/1 constants
            else:
                pass
        return deps

    def get_lit_deps(self, lit):
        if lit not in self._deps_cache:
            self._deps_cache[lit] = self.get_mult_lit_deps([lit])
        return self._deps_cache[lit]

    def get_lit_latch_deps(self, lit):
        latchset = set([x.lit for x in self.iterate_latches()])
        return self.get_lit_deps(lit) & latchset

    def latch_dependency_map(self):
        m = dict()
        latchset = set([x.lit for x in self.iterate_latches()])
        # call the recursive worker for each gate with the next step
        # value of a latch and map the sets to each latch lit
        for l in self.iterate_latches():
            m[l.lit] = self.get_lit_deps(l.next) & latchset
        return m

    # very important for BDD and CNF translations, we need this to be uniform
    # and consistent
    def get_primed_var(self, lit):
        return strip_lit(lit) + 1


def new_aiger_symbol():
    return aiger_symbol()


def negate_lit(l):
    return l ^ 1


def lit_is_negated(l):
    return (l & 1) == 1


def strip_lit(l):
    return l & ~1


def symbol_lit(x):
    return x.lit
