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
from utils import fixpoint
import aig
import log
import bdd


EXIT_STATUS_REALIZABLE = 10
EXIT_STATUS_UNREALIZABLE = 20


def synth(argv):
    init_state_bdd = aig.trans_rel_bdd_bdd()
    error_bdd = bdd.BDD(aig.error_fake_latch.lit)

    log.DBG_MSG("Computing fixpoint of UPRE")
    win_region = ~fixpoint(
        error_bdd,
        fun=lambda x: aig.upre_bdd(
            x, restrict_like_crazy=argv.restrict_like_crazy,
            use_trans=argv.use_trans),
        early_exit=lambda x: x & init_state_bdd != bdd.false()
    )

    if win_region & init_state_bdd == bdd.false():
        log.LOG_MSG("The spec is unrealizable.")
        log.LOG_ACCUM()
        return False
    else:
        log.LOG_MSG("The spec is realizable.")
        log.LOG_ACCUM()
        return True


def main():
    parser = argparse.ArgumentParser(description="AIG Format Based Synth")
    parser.add_argument("spec", metavar="spec", type=str,
                        help="input specification in extended AIGER format")
    parser.add_argument("-t", "--use_trans", action="store_true",
                        dest="use_trans", default=False,
                        help="Compute a transition relation")
    parser.add_argument("-rc", "--restrict_like_crazy", action="store_true",
                        dest="restrict_like_crazy", default=False,
                        help=("Use restrict to minimize BDDs" +
                              "everywhere possible"))
    parser.add_argument("-v", "--verbose", dest="verbose_level",
                        default="", required=False,
                        help="Verbose level = (D)ebug, (W)arnings, " +
                             "(L)og messages, (B)DD dot dumps")
    parser.add_argument("--out", "-o", dest="out_file", type=str,
                        required=False, default=None,
                        help=("output file (only used if "
                              "spec is realizable)"))
    args = parser.parse_args()
    # initialize the log verbose level
    log.parse_verbose_level(args.verbose_level)
    is_realizable = synth(args)
    exit([EXIT_STATUS_UNREALIZABLE, EXIT_STATUS_REALIZABLE][is_realizable])


if __name__ == "__main__":
    main()
