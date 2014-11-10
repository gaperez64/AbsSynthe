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
from utils import fixpoint
import log
import bdd
import aig


# safety game template for the algorithms implemented here, they all
# use only the functions provided here
class Game:
    def upre(self, dst):
        pass

    def upost(self, src):
        pass

    def cpre(self, dst):
        pass

    def cpost(self, src):
        pass

    def error(self):
        pass

    def init(self):
        pass

    def is_env_state(self, state):
        pass


# Explicit OTFUR based on the transition relation and using smart simulation
# relation abstraction
def forward_safety_synth(game):
    init_state = game.init()
    error_states = game.error()
    passed = set([init_state])
    depend = dict()
    depend[init_state] = set()
    losing = dict()
    losing[init_state] = False
    waiting = [(init_state, x) for x in game.upost(init_state)]
    while waiting and not losing[init_state]:
        (s, sp) = waiting.pop()
        if sp not in passed:
            passed.add(sp)
            losing[sp] = game.is_env_state(sp) and (sp & error_states)
            if sp in depend:
                depend[sp].add((s, sp))
            else:
                depend[sp] = set([(s, sp)])
            if losing[sp]:
                waiting.append((s, sp))
            else:
                if game.is_env_state(sp):
                    waiting.extend([(sp, x) for x in game.upost(sp)])
                else:
                    waiting.extend([(sp, x) for x in game.cpost(sp)])
        else:
            is_loser = lambda x: x in losing and losing[x]
            local_lose = (game.is_env_state(s) and
                          any(imap(is_loser, game.upost(s))) or
                          all(imap(is_loser, game.cpost(s))))
            if local_lose:
                losing[s] = True
                waiting.extend(depend[s])
            if sp not in losing or not losing[sp]:
                depend[sp] = depend[sp] | set([(s, sp)])
    log.DBG_MSG("OTFUR, losing[init_state] = " +
                str(losing[init_state]))
    return None if losing[init_state] else True


# Classical backward fixpoint algo
def backward_safety_synth(game, only_real=False):
    init_state = game.init()
    error_states = game.error()
    log.DBG_MSG("Computing fixpoint of UPRE.")
    win_region = ~fixpoint(
        error_states,
        fun=lambda x: x | game.upre(x),
        early_exit=lambda x: x & init_state
    )

    if not win_region & init_state:
        return None
    else:
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
