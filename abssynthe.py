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

import argparse
from algos import (
    ABS_TECH,
    backward_upre_synth,
    extract_output_funs,
    forward_explicit_synth
)
import bdd
import aig
import aig2bdd
import bdd2aig
import log


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


def synth(argv):
    # Explicit approach
    if argv.use_symb:
        w = forward_explicit_synth()
        if w is None:
            return False
    # Symbolic approach with some optimizations
    elif not argv.no_decomp and aig.lit_is_negated(aig.error_fake_latch.next):
        log.DBG_MSG("Decomposition opt possible")
        (A, B) = aig.get_1l_land(aig.strip_lit(aig.error_fake_latch.next))
        s = bdd.true()
        for a in A:
            log.DBG_MSG("Solving sub-safety game for var " + str(a))
            latchset = set([x.lit for x in aig.iterate_latches()])
            log.DBG_MSG("Avoidable latch # = " +
                        str(len(latchset - aig.get_rec_latch_deps(a))))
            aig.push_error_function(aig.negate_lit(a))
            w = backward_upre_synth(
                restrict_like_crazy=argv.restrict_like_crazy,
                use_trans=argv.use_trans, abs_tech=argv.abs_tech,
                only_real=argv.out_file is None)
            if w is None:
                return False
            s &= aig2bdd.cpre_bdd(w, get_strat=True)
            aig.pop_error_function()
            if (s == bdd.false() or
                    aig2bdd.init_state_bdd() & s == bdd.false()):
                return False
        # we have to make sure the controller can stay in the win'n area
        if not aig2bdd.strat_is_inductive(s, use_trans=argv.use_trans):
            return False
    # Symbolic approach (allows for abstraction techniques)
    else:
        w = backward_upre_synth(
            restrict_like_crazy=argv.restrict_like_crazy,
            use_trans=argv.use_trans, abs_tech=argv.abs_tech,
            only_real=argv.out_file is None)
        # check if realizable and write output file
        if w is None:
            return False

    # synthesis from the realizability analysis
    if argv.out_file is not None:
        log.DBG_MSG("Win region bdd node count = " +
                    str(w.dag_size()))
        c_input_info = []
        n_strategy = aig2bdd.cpre_bdd(w, get_strat=True)
        func_per_output = extract_output_funs(n_strategy, care_set=w)
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

    return True


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
