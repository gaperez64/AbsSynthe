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


from utils import fixpoint
import log
import aig
import bdd


# Our standard solver: compute the fixpoint MX.X U Upre(X) starting from the
# error states (the transitionless version is a.k.a. Romain's algo).
# Returns None if Eve loses the game and a bdd with the winning states
# otherwise.
def backward_upre_synth(restrict_like_crazy=False, use_trans=False):
    init_state_bdd = aig.init_state_bdd()
    error_bdd = bdd.BDD(aig.error_fake_latch.lit)

    log.DBG_MSG("Computing fixpoint of UPRE.")
    win_region = ~fixpoint(
        error_bdd,
        fun=lambda x: x | aig.upre_bdd(
            x, restrict_like_crazy=restrict_like_crazy,
            use_trans=use_trans),
        early_exit=lambda x: x & init_state_bdd != bdd.false()
    )

    if win_region & init_state_bdd == bdd.false():
        log.LOG_MSG("The spec is unrealizable.")
        log.LOG_ACCUM()
        return None
    else:
        log.LOG_MSG("The spec is realizable.")
        log.LOG_ACCUM()
        return win_region


# Given a bdd representing the set of safe states-action paris for the
# controller (Eve) we compute a winning strategy for her (trying to get a
# minimal one via a greedy algo on the way).
def extract_output_funs(strategy, care_set=None):
    """
    Calculate BDDs for output functions given non-deterministic winning
    strategy.
    """
    if care_set is None:
        care_set = bdd.true()

    output_models = dict()
    all_outputs = [bdd.BDD(x.lit) for x in aig.iterate_controllable_inputs()]
    for c_symb in aig.iterate_controllable_inputs():
        c = bdd.BDD(c_symb.lit)
        others = set(set(all_outputs) - set([c]))
        if others:
            others_cube = bdd.get_cube(others)
            c_arena = strategy.exist_abstract(others_cube)
        else:
            c_arena = strategy
        # pairs (x,u) in which c can be true
        can_be_true = c_arena.cofactor(c)
        # pairs (x,u) in which c can be false
        can_be_false = c_arena.cofactor(~c)
        must_be_true = (~can_be_false) & can_be_true
        must_be_false = (~can_be_true) & can_be_false
        local_care_set = care_set & (must_be_true | must_be_false)
        # Restrict operation:
        #   on care_set: must_be_true.restrict(care_set) <-> must_be_true
        c_model = min([must_be_true.safe_restrict(local_care_set),
                      (~must_be_false).safe_restrict(local_care_set)],
                      key=bdd.dag_size)
        output_models[c_symb.lit] = c_model
        log.DBG_MSG("Size of function for " + str(c.get_index()) + " = " +
                    str(c_model.dag_size()))
        strategy &= bdd.make_eq(c, c_model)
    return output_models
