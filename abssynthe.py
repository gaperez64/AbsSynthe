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
from utils import funcomp
from algos import (
    Game,
    backward_safety_synth,
    forward_safety_synth
)
from cudd_bdd import BDD
import aig
import aig2bdd
import bdd2aig
import log


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


class ABS_TECH:
    LOC_RED = 1,
    PRED_ABS = 2,
    NONE = 3


class ConcGame(Game):
    def __init__(self, restrict_like_crazy=False,
                 use_trans=False):
        self.restrict_like_crazy = restrict_like_crazy
        self.use_trans = use_trans

    def init(self):
        return aig2bdd.init_state_bdd()

    def error(self):
        return aig2bdd.get_bdd_for_lit(aig.error_fake_latch.lit)

    def upre(self, dst):
        return aig2bdd.upre_bdd(
            dst, restrict_like_crazy=self.restrict_like_crazy,
            use_trans=self.use_trans)


class SymblicitGame(Game):
    def __init__(self):
        self.uinputs = [x.lit for x in aig.iterate_uncontrollable_inputs()]
        self.latches = [x.lit for x in aig.iterate_latches()]
        self.trans = aig2bdd.trans_rel_bdd()
        self.latch_cube = BDD.get_cube(imap(funcomp(BDD,
                                                    aig.symbol_lit),
                                            aig.iterate_latches()))
        self.platch_cube = BDD.get_cube(imap(funcomp(BDD,
                                                     aig.get_primed_var,
                                                     aig.symbol_lit),
                                             aig.iterate_latches()))
        self.cinputs_cube = BDD.get_cube(
            imap(funcomp(BDD, aig.symbol_lit),
                 aig.iterate_controllable_inputs()))
        self.uinputs_cube = BDD.get_cube(
            imap(funcomp(BDD, aig.symbol_lit),
                 aig.iterate_uncontrollable_inputs()))
        self.init_state_bdd = aig2bdd.init_state_bdd()
        self.error_bdd = aig2bdd.get_bdd_for_lit(aig.error_fake_latch.lit)
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
            lhs = self.trans.and_abstract(a & q, self.latch_cube)
            rhs = aig2bdd.prime_all_inputs_in_bdd(self.trans & q)\
                .exist_abstract(self.latch_cube)
            simd = BDD.make_impl(lhs, rhs).univ_abstract(self.platch_cube)\
                .exist_abstract(self.cinputs_cube)\
                .univ_abstract(self.uinputs_cube)
            simd = aig2bdd.unprime_all_inputs_in_bdd(simd)

            A &= ~simd
            for m in M:
                if BDD.make_impl(m, simd) == BDD.true():
                    M.remove(m)
            M.add(a)
        log.DBG_MSG("|M| = " + str(len(M)))
        self.succ_cache[q] = M
        return set([(q, m) for m in M])

    def cpost(self, s):
        q = s[0]
        au = s[1]
        if s in self.succ_cache:
            return self.succ_cache[s]
        L = aig2bdd.unprime_latches_in_bdd(
            self.trans.and_abstract(q & au, self.latch_cube &
                                    self.uinputs_cube & self.cinputs_cube))
        R = set()
        while L != BDD.false():
            l = L.get_one_minterm(self.latches)
            R.add(l)
            L &= ~l
            self.Venv[l] = True
        log.DBG_MSG("|R| = " + str(len(R)))
        self.succ_cache[s] = R
        return R

    def is_env_state(self, s):
        return s in self.Venv


def synth(argv):
    # Explicit approach
    if argv.use_symb:
        assert argv.out_file is None
        symgame = SymblicitGame()
        w = forward_safety_synth(symgame)
    # Symbolic approach with compositional opts
    elif not argv.no_decomp and aig.lit_is_negated(aig.error_fake_latch.next):
        log.DBG_MSG("Decomposition opt possible")
        (A, B) = aig.get_1l_land(aig.strip_lit(aig.error_fake_latch.next))
        s = BDD.true()
        for a in A:
            log.DBG_MSG("Solving sub-safety game for var " + str(a))
            latchset = set([x.lit for x in aig.iterate_latches()])
            log.DBG_MSG("Avoidable latch # = " +
                        str(len(latchset - aig.get_rec_latch_deps(a))))
            aig.push_error_function(aig.negate_lit(a))
            game = ConcGame(restrict_like_crazy=argv.restrict_like_crazy,
                            use_trans=argv.use_trans)
            w = backward_safety_synth(game)
            # short-circuit a negative response
            if w is None:
                return False
            s &= aig2bdd.cpre_bdd(w, get_strat=True)
            aig.pop_error_function()
            # sanity check before moving forward
            if (s == BDD.false() or
                    aig2bdd.init_state_bdd() & s == BDD.false()):
                return False
        # we have to make sure the controller can stay in the win'n area
        if not aig2bdd.strat_is_inductive(s, use_trans=argv.use_trans):
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
        n_strategy = aig2bdd.cpre_bdd(w, get_strat=True)
        func_per_output = bdd2aig.extract_output_funs(n_strategy, care_set=w)
        if argv.only_transducer:
            for c in aig.iterate_controllable_inputs():
                c_input_info.append((c.lit, c.name))
        for (c, func_bdd) in func_per_output.items():
            aig.input2and(c, bdd2aig.bdd2aig(func_bdd))
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
    # parse the input spec
    aig.parse_into_spec(args.spec, intro_error_latch=True)
    # realizability / synthesis
    is_realizable = synth(args)
    log.LOG_MSG("Realizable? " + str(bool(is_realizable)))
    exit([EXIT_STATUS_UNREALIZABLE, EXIT_STATUS_REALIZABLE][is_realizable])


if __name__ == "__main__":
    main()
