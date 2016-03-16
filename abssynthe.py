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
import log
from bdd_aig import BDDAIG
from algos import (
    backward_safety_synth,
    forward_safety_synth,
    test_safety_synth
)
from bdd_games import (
    ConcGame,
    SymblicitGame,
)
from comp_algos import (
    decompose,
    comp_synth,
    comp_synth3,
    comp_synth4,
    subgame_mapper,
    subgame_reducer
)


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


def synth(argv):
    # parse the input spec
    aig = BDDAIG(aiger_file_name=argv.spec, intro_error_latch=True)
    return synth_from_spec(aig, argv)


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
            game = ConcGame(BDDAIG(aig).short_error(~strat),
                            use_trans=argv.use_trans)
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
        elif argv.comp_algo == 4:
            # solve games by up-down algo
            gen_game = ConcGame(aig, use_trans=argv.use_trans)
            w = comp_synth4(game_it, gen_game)
        else:
            raise NotImplementedError()
    # Symbolic approach (avoiding compositional opts)
    else:
        game = ConcGame(aig,
                        use_trans=argv.use_trans)
        if argv.use_beta:
            w = test_safety_synth(game)
        else:
            w = backward_safety_synth(game)
    # final check
    if w is None:
        return False
    log.DBG_MSG("Win region bdd node count = " +
                str(w.dag_size()))
    # synthesis from the realizability analysis
    if w is not None:
        if argv.out_file is not None:
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
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("spec", metavar="spec", type=str,
                        help="input specification in extended AIGER format")
    parser.add_argument("-t", "--use_trans", action="store_true",
                        dest="use_trans", default=False,
                        help="Compute a transition relation")
    parser.add_argument("-b", "--use_beta", action="store_true",
                        dest="use_beta", default=False,
                        help="Use algorithm which is being tested")
    parser.add_argument("-s", "--use_symb", action="store_true",
                        dest="use_symb", default=False,
                        help="Use the symblicit forward approach")
    parser.add_argument("-d", "--decomp", dest="decomp", default=None,
                        type=str, help="Decomposition type", choices="12")
    parser.add_argument("-ca", "--comp_algo", dest="comp_algo", type=str,
                        default="1", choices="1234",
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
    # realizability / synthesis
    is_realizable = synth(args)
    log.LOG_MSG("Realizable? " + str(bool(is_realizable)))
    exit([EXIT_STATUS_UNREALIZABLE, EXIT_STATUS_REALIZABLE][is_realizable])


if __name__ == "__main__":
    main()
