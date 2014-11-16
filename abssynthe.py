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
import argparse

import log
from cudd_bdd import BDD
from aig import (
    symbol_lit,
    strip_lit,
)
from bdd_aig import BDDAIG
from utils import funcomp
from algos import (
    BackwardGame,
    ForwardGame,
    backward_safety_synth,
    forward_safety_synth,
    comp_safety_synth,
)


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


class ABS_TECH:
    LOC_RED = 1,
    PRED_ABS = 2,
    NONE = 3


class ConcGame(BackwardGame):
    def __init__(self, aig, restrict_like_crazy=False,
                 use_trans=False):
        self.restrict_like_crazy = restrict_like_crazy
        self.use_trans = use_trans
        self.aig = aig

    def init(self):
        return self.aig.init_state_bdd()

    def error(self):
        return self.aig.get_bdd_for_lit(self.aig.error_fake_latch.lit)

    def upre(self, dst):
        return self.aig.upre_bdd(
            dst, restrict_like_crazy=self.restrict_like_crazy,
            use_trans=self.use_trans)

    def cpre(self, dst, get_strat=False):
        return self.aig.cpre_bdd(
            dst, restrict_like_crazy=self.restrict_like_crazy,
            use_trans=self.use_trans, get_strat=get_strat)


class SymblicitGame(ForwardGame):
    def __init__(self, aig):
        self.aig = aig
        self.uinputs = [x.lit for x in
                        self.aig.iterate_uncontrollable_inputs()]
        self.latches = [x.lit for x in self.aig.iterate_latches()]
        self.latch_cube = BDD.make_cube(imap(funcomp(BDD,
                                                     symbol_lit),
                                             self.ig.iterate_latches()))
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
        self.init_state_bdd = self.init_state_bdd()
        self.error_bdd = self.get_bdd_for_lit(self.aig.error_fake_latch.lit)
        self.Venv = dict()
        self.Venv[self.init_state_bdd] = True
        self.succ_cache = dict()

    def init(self):
        return self.init_state_bdd

    def error(self):
        return self.error_bdd

    def upost(self, q):
        if q in self.succ_cache:
            return self.succ_cache[q]
        A = BDD.true()
        M = set()
        while A != BDD.false():
            a = A.get_one_minterm(self.uinputs)
            trans = BDD.make_cube(
                imap(lambda x: BDD.make_eq(BDD(self.aig.get_primed_var(x.lit)),
                                           self.aig.get_bdd_for_lit(x.next)
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
                if not BDD.make_impl(m, simd):
                    Mp.add(m)
            M = Mp
            M.add(a)
        log.DBG_MSG("|M| = " + str(len(M)))
        self.succ_cache[q] = M
        return imap(lambda x: (q, x), M)

    def cpost(self, s):
        q = s[0]
        au = s[1]
        if s in self.succ_cache:
            L = self.succ_cache[s]
        else:
            L = BDD.make_cube(
                imap(lambda x: BDD.make_eq(BDD(x.lit),
                                           self.aig.get_bdd_for_lit(x.next)
                                           .and_abstract(q & au,
                                                         self.latch_cube &
                                                         self.uinputs_cube)),
                     self.aig.iterate_latches()))\
                .exist_abstract(self.cinputs_cube)
            self.succ_cache[s] = L
        while L != BDD.false():
            l = L.get_one_minterm(self.latches)
            L &= ~l
            self.Venv[l] = True
            yield l

    def is_env_state(self, s):
        return s in self.Venv


def synth(argv):
    # parse the input spec
    aig = BDDAIG(argv.spec, intro_error_latch=True)
    # Explicit approach
    if argv.use_symb:
        assert argv.out_file is None
        symgame = SymblicitGame()
        w = forward_safety_synth(symgame)
    # Symbolic approach with compositional opts
    elif not argv.no_decomp and aig.lit_is_negated(aig.error_fake_latch.next):
        log.DBG_MSG("Decomposition opt possible (BIG OR case)")
        (A, B) = aig.get_1l_land(strip_lit(aig.error_fake_latch.next))
        s = comp_safety_synth(imap(lambda a: BDDAIG(aig).set_lit2bdd(
            aig.error_fake_latch.next, ~(aig.lit2bdd(a))), A))
        # we have to make sure the controller can stay in the win'n area
        if s is None or\
                not aig.strat_is_inductive(s, use_trans=argv.use_trans):
            return False
    # Symbolic approach with compositional opts geared towards GR(1) specs
    # the idea is that if the error signal is of the form
    # A ^ (C v D) then we can distribute the disjunction to get
    # (A ^ C) v (A ^ D)
    elif not argv.no_decomp:
        (A, B) = aig.get_1l_land(aig.error_fake_latch.next)
        if not B:
            log.DBG_MSG("No decomposition opt possible")
            argv.no_decomp = True
            return synth(argv)
        else:
            log.DBG_MSG("Decomposition opt possible (A ^ [C v D] case)")
        b = B.pop()
        cube = BDD.make_cube(filter(lambda x: x != strip_lit(b), A))
        (C, D) = aig.get_1l_land(b)
        s = comp_safety_synth(imap(lambda a: BDDAIG(aig).set_lit2bdd(
            aig.error_fake_latch.lit, ~(aig.lit2bdd(a)) & cube), C))
        # we have to make sure the controller can stay in the win'n area
        if s is None or\
                not aig.strat_is_inductive(s, use_trans=argv.use_trans):
            return False
    # Symbolic approach (avoiding compositional opts)
    else:
        game = ConcGame(restrict_like_crazy=argv.restrict_like_crazy,
                        use_trans=argv.use_trans)
        w = backward_safety_synth(game)

    # synthesis from the realizability analysis
    if w is not None and argv.out_file is not None:
        log.DBG_MSG("Win region bdd node count = " +
                    str(w.dag_size()))
        c_input_info = []
        n_strategy = aig.cpre_bdd(w, get_strat=True)
        func_per_output = aig.extract_output_funs(n_strategy, care_set=w)
        if argv.only_transducer:
            for c in aig.iterate_controllable_inputs():
                c_input_info.append((c.lit, c.name))
        for (c, func_bdd) in func_per_output.items():
            aig.input2and(c, aig.bdd2aig(func_bdd))
        if argv.only_transducer:
            aig.remove_outputs()
            for (l, n) in c_input_info:
                aig.add_output(l, n)
        aig.write_spec(argv.out_file)
    elif w is not None:
        return True
    else:
        return False


def parse_abs_tech(abs_arg):
    if "D" == abs_arg:
        return ABS_TECH.LOC_RED
    elif "L" == abs_arg:
        return ABS_TECH.PRED_ABS
    elif "" == abs_arg:
        return ABS_TECH.NONE
    else:
        log.WRN_MSG("Abs. tech '" + abs_arg + "' not valid. Ignored it.")
        return None


def main():
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("spec", metavar="spec", type=str,
                        help="input specification in extended AIGER format")
    parser.add_argument("-a", "--abs_tech", dest="abs_tech",
                        default="", required=False,
                        help=("Use abstraction techniques = (L)ocalization " +
                              "reduction or (P)redicate abstraction"))
    parser.add_argument("-t", "--use_trans", action="store_true",
                        dest="use_trans", default=False,
                        help="Compute a transition relation")
    parser.add_argument("-s", "--use_symb", action="store_true",
                        dest="use_symb", default=False,
                        help="Use the symblicit forward approach")
    parser.add_argument("-nd", "--no_decomp", action="store_true",
                        dest="no_decomp", default=False,
                        help="Inhibits the decomposition optimization")
    parser.add_argument("-rc", "--restrict_like_crazy", action="store_true",
                        dest="restrict_like_crazy", default=False,
                        help=("Use restrict to minimize BDDs " +
                              "everywhere possible"))
    parser.add_argument("-v", "--verbose_level", dest="verbose_level",
                        default="", required=False,
                        help="Verbose level = (D)ebug, (W)arnings, " +
                             "(L)og messages, (B)DD dot dumps")
    parser.add_argument("-o", "--out_file", dest="out_file", type=str,
                        required=False, default=None,
                        help=("Output file path. If file extension = .aig, " +
                              "binary output format will be used, if " +
                              "file extension = .aag, ASCII output will be " +
                              "used. The argument is ignored if the spec is " +
                              "not realizable."))
    parser.add_argument("-ot", "--only_transducer", action="store_true",
                        dest="only_transducer", default=False,
                        help=("Output only the synth'd transducer (i.e. " +
                              "remove the error monitor logic)."))
    args = parser.parse_args()
    # initialize the log verbose level
    log.parse_verbose_level(args.verbose_level)
    # parse the abstraction tech
    args.abs_tech = parse_abs_tech(args.abs_tech)
    # realizability / synthesis
    is_realizable = synth(args)
    log.LOG_MSG("Realizable? " + str(bool(is_realizable)))
    exit([EXIT_STATUS_UNREALIZABLE, EXIT_STATUS_REALIZABLE][is_realizable])


if __name__ == "__main__":
    main()
