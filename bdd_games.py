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

from itertools import imap

import log
from cudd_bdd import BDD
from bdd_aig import BDDAIG
from aig import (
    symbol_lit,
)
from utils import (
    funcomp,
    fixpoint
)
from algos import (
    BackwardGame,
    ForwardGame,
)


class ConcGame(BackwardGame):
    def __init__(self, aig, use_trans=False):
        self.use_trans = use_trans
        self.aig = aig
        self.short_error = None

    def init(self):
        return self.aig.init_state_bdd()

    def error(self):
        if self.short_error is not None:
            return self.short_error
        else:
            return self.aig.lit2bdd(self.aig.error_fake_latch.lit)

    def short_aig_error(self, error):
        self.aig = self.aig.short_error(error)

    def upre(self, dst):
        return self.aig.upre_bdd(
            dst,
            use_trans=self.use_trans)

    def pre(self, dst, no_projection=False):
        return self.aig.pre_bdd(
            dst,
            no_projection,
            use_trans=self.use_trans)

    def cpre(self, dst, get_strat=False):
        return self.aig.cpre_bdd(
            dst,
            use_trans=self.use_trans, get_strat=get_strat)


class SymblicitGame(ForwardGame):
    def __init__(self, aig):
        self.aig = aig
        self.uinputs = [x.lit for x in
                        self.aig.iterate_uncontrollable_inputs()]
        self.latches = [x.lit for x in self.aig.iterate_latches()]
        self.latch_cube = BDD.make_cube(imap(funcomp(BDD,
                                                     symbol_lit),
                                             self.aig.iterate_latches()))
        self.platch_cube = BDD.make_cube(imap(funcomp(BDD,
                                                      self.aig.get_primed_var,
                                                      symbol_lit),
                                              self.aig.iterate_latches()))
        self.cinputs_cube = BDD.make_cube(
            imap(funcomp(BDD, symbol_lit),
                 self.aig.iterate_controllable_inputs()))
        self.pcinputs_cube = self.aig.prime_all_inputs_in_bdd(
            self.cinputs_cube)
        self.uinputs_cube = BDD.make_cube(
            imap(funcomp(BDD, symbol_lit),
                 self.aig.iterate_uncontrollable_inputs()))
        self.init_state_bdd = self.aig.init_state_bdd()
        self.error_bdd = self.aig.lit2bdd(self.aig.error_fake_latch.lit)
        self.Venv = dict()
        self.Venv[self.init_state_bdd] = True
        self.succ_cache = dict()

    def init(self):
        return self.init_state_bdd

    def error(self):
        return self.error_bdd

    def upost(self, q):
        assert isinstance(q, BDD)
        if q in self.succ_cache:
            return iter(self.succ_cache[q])
        A = BDD.true()
        M = set()
        while A != BDD.false():
            a = A.get_one_minterm(self.uinputs)
            trans = BDD.make_cube(
                imap(lambda x: BDD.make_eq(BDD(self.aig.get_primed_var(x.lit)),
                                           self.aig.lit2bdd(x.next)
                                           .and_abstract(q, self.latch_cube)),
                     self.aig.iterate_latches()))
            lhs = trans & a
            rhs = self.aig.prime_all_inputs_in_bdd(trans)
            simd = BDD.make_impl(lhs, rhs).univ_abstract(self.platch_cube)\
                .exist_abstract(self.pcinputs_cube)\
                .univ_abstract(self.cinputs_cube)
            simd = self.aig.unprime_all_inputs_in_bdd(simd)

            A &= ~simd
            Mp = set()
            for m in M:
                if not (BDD.make_impl(m, simd) == BDD.true()):
                    Mp.add(m)
            M = Mp
            M.add(a)
        log.DBG_MSG("Upost |M| = " + str(len(M)))
        self.succ_cache[q] = map(lambda x: (q, x), M)
        return iter(self.succ_cache[q])

    def cpost(self, s):
        assert isinstance(s, tuple)
        q = s[0]
        au = s[1]
        if s in self.succ_cache:
            L = self.succ_cache[s]
        else:
            L = BDD.make_cube(
                imap(lambda x: BDD.make_eq(BDD(x.lit),
                                           self.aig.lit2bdd(x.next)
                                           .and_abstract(q & au,
                                                         self.latch_cube &
                                                         self.uinputs_cube)),
                     self.aig.iterate_latches()))\
                .exist_abstract(self.cinputs_cube)
            self.succ_cache[s] = L
        M = set()
        while L != BDD.false():
            l = L.get_one_minterm(self.latches)
            L &= ~l
            self.Venv[l] = True
            M.add(l)
        log.DBG_MSG("Cpost |M| = " + str(len(M)))
        return iter(M)

    def is_env_state(self, s):
        return s in self.Venv


# Test your algo here
def test_safety_synth(game):
    assert isinstance(game, BackwardGame)

    init_state = game.init()
    error_states = game.error()

    while True:
        while True:
            nu_error_states = error_states
            temp_error = game.pre(nu_error_states)
            deps = game.aig.get_bdd_deps(temp_error)
            log.DBG_MSG("Deps of pre: " + str(deps))
            proj_cube = BDD.make_cube(imap(funcomp(BDD, symbol_lit),
                                      game.aig.iterate_controllable_inputs()))
            deps = game.aig.get_bdd_deps(proj_cube)
            log.DBG_MSG("Deps of proj_cube: " + str(deps))
            pre_error = temp_error.exist_abstract(proj_cube)
            assert temp_error != pre_error
            # Error above! no controllable deps should come here
            deps = game.aig.get_bdd_deps(pre_error)
            log.DBG_MSG("Deps of pre: " + str(deps))
            unc_lits = [x.lit for x in game.aig.iterate_uncontrollable_inputs()]
            unc_funs = BDD.extract_funs(pre_error, unc_lits)
            unc_eqs = [BDD.make_eq(BDD(v), unc_funs[v]) for v in unc_lits]
            uncfun_cube = BDD.make_cube(unc_eqs)
            unc_cube = BDD.make_cube([BDD(v) for v in unc_lits])
            nu_aig = BDDAIG(game.aig)
            nu_aig.assume_funs_latch_next_funs(uncfun_cube, unc_cube)
            nu_game = ConcGame(nu_aig)
            log.DBG_MSG("Computing the fixpoint with fixed strategy")
            nu_error_states = fixpoint(
                nu_error_states,
                fun=lambda x: x | nu_game.upre(x),
                early_exit=lambda x: x & init_state
            )
            if not (~nu_error_states & init_state):
                return None
            if error_states != nu_error_states:
                break
        log.DBG_MSG("Testing with a full UPRE")
        error_states = game.upre(nu_error_states) | nu_error_states
        if error_states != nu_error_states:
            break

    if not (~error_states & init_state):
        return None
    else:
        return ~error_states
