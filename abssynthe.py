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
    lit_is_negated
)
from bdd_aig import BDDAIG
from algos import (
    backward_safety_synth,
    forward_safety_synth,
)
from bdd_games import (
    ConcGame,
    SymblicitGame,
)
from comp_algos import (
    comp_synth,
    comp_synth3,
    subgame_mapper,
    subgame_reducer
)


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


class ABS_TECH:
    LOC_RED = 1,
    PRED_ABS = 2,
    NONE = 3


def merge_some_signals(cube, C, aig, argv):
    # TODO: there must be a more pythonic way of doing all of this
    log.LOG_MSG(str(len(C)) + " sub-games originally")
    cube_latch_deps = set(cube.occ_sem(imap(symbol_lit,
                                            aig.iterate_latches())))
    latch_deps = reduce(set.union,
                        map(aig.get_lit_latch_deps,
                            cube_latch_deps),
                        set())
    dep_map = dict()
    for c in C:
        deps = frozenset(latch_deps | aig.get_lit_latch_deps(c))
        found = False
        for key in dep_map:
            if key >= deps:
                dep_map[key] &= aig.lit2bdd(c)
                found = True
                break
            elif key <= deps:
                dep_map[deps] = dep_map[key] & aig.lit2bdd(c)
                del dep_map[key]
                found = True
                break
        if not found:
            dep_map[deps] = aig.lit2bdd(c)
    log.LOG_MSG(str(len(dep_map.keys())) + " sub-games after incl. red.")
    for key in dep_map:
        yield ~dep_map[key] & cube


def synth(argv):
    # parse the input spec
    aig = BDDAIG(aiger_file_name=argv.spec, intro_error_latch=True)
    return synth_from_spec(aig, argv)


def decompose(aig, argv):
    if argv.decomp == 1:
        if lit_is_negated(aig.error_fake_latch.next):
            log.DBG_MSG("Decomposition opt possible (BIG OR case)")
            (A, B) = aig.get_1l_land(strip_lit(aig.error_fake_latch.next))
            return imap(lambda a: ConcGame(
                BDDAIG(aig).short_error(a),
                use_trans=argv.use_trans),
                merge_some_signals(BDD.true(), A, aig, argv))
        else:
            (A, B) = aig.get_1l_land(aig.error_fake_latch.next)
            if not B:
                log.DBG_MSG("No decomposition opt possible")
                return None
            else:
                log.DBG_MSG("Decomposition opt possible (A ^ [C v D] case)")
                log.DBG_MSG(str(len(A)) + " AND leaves: " + str(A))
            # critical heuristic: which OR leaf do we distribute?
            # here I propose to choose the one with the most children
            b = B.pop()
            (C, D) = aig.get_1l_land(b)
            for bp in B:
                (Cp, Dp) = aig.get_1l_land(bp)
                if len(Cp) > len(C):
                    b = bp
                    C = Cp
            rem_AND_leaves = filter(lambda x: strip_lit(x) != b, A)
            rdeps = set()
            for r in rem_AND_leaves:
                rdeps |= aig.get_lit_latch_deps(strip_lit(r))
            log.DBG_MSG("Rem. AND leaves' deps: " + str(rdeps))
            cube = BDD.make_cube(map(aig.lit2bdd, rem_AND_leaves))
            log.DBG_MSG(str(len(C)) + " OR leaves: " + str(C))
            return imap(lambda a: ConcGame(
                BDDAIG(aig).short_error(a),
                use_trans=argv.use_trans), merge_some_signals(cube, C, aig,
                                                              argv))
    elif argv.decomp == 2:
        raise NotImplementedError


def synth_from_spec(aig, argv):
    # Explicit approach
    if argv.use_symb:
        assert argv.out_file is None
        symgame = SymblicitGame(aig)
        w = forward_safety_synth(symgame)
    # Symbolic approach with compositional opts
    elif argv.decomp is not None:
        game_it = decompose(aig, argv)
        # if there was no decomposition possible then call simple
        # solver
        if game_it is None:
            argv.decomp = None
            return synth_from_spec(aig, argv)
        if argv.comp_algo == 1:
            # solve and aggregate sub-games
            (w, strat) = comp_synth(game_it)
            # back to the general game
            if w is None:
                return False
            log.DBG_MSG("Interm. win region bdd node count = " +
                        str(w.dag_size()))
            game = ConcGame(aig,
                            use_trans=argv.use_trans)
            game.short_error = ~w
            w = backward_safety_synth(game)
        elif argv.comp_algo == 2:
            games_mapped = subgame_mapper(game_it, aig)
            # local aggregation yields None if short-circ'd
            if games_mapped is None:
                return False
            w = subgame_reducer(games_mapped, aig, argv)
        elif argv.comp_algo == 3:
            # solve games by up-down algo
            gen_game = ConcGame(aig, use_trans=argv.use_trans)
            w = comp_synth3(game_it, gen_game)
    # Symbolic approach (avoiding compositional opts)
    else:
        game = ConcGame(aig,
                        use_trans=argv.use_trans)
        w = backward_safety_synth(game)
    # final check
    if w is None:
        return False
    log.DBG_MSG("Win region bdd node count = " +
                str(w.dag_size()))
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
    parser.add_argument("-d", "--decomp", dest="decomp", default=None,
                        type=str, help="Decomposition type", choices="12")
    parser.add_argument("-ca", "--comp_algo", dest="comp_algo", type=str,
                        default="1", choices="123",
                        help="Choice of compositional algorithm")
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
    args.decomp = int(args.decomp) if args.decomp is not None else None
    args.comp_algo = int(args.comp_algo)
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
