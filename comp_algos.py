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

from algos import (
    BackwardGame,
    backward_safety_synth
)
from cudd_bdd import BDD
from bdd_aig import BDDAIG
from bdd_games import ConcGame
import log


# Compositional approach, receives an iterable of BackwardGames
def comp_synth(games):
    s = None
    cum_w = None
    cnt = 0
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit after sub-game #" + str(cnt))
            return (None, None)
        if s is None:
            s = game.cpre(w, get_strat=True)
            cum_w = w
        else:
            s &= game.cpre(w, get_strat=True)
            cum_w &= w
        # sanity check before moving forward
        if (not s or not game.init() & s):
            return (None, None)
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    return (cum_w, s)


def comp_synth3(games, gen_game):
    s = None
    cum_s = None
    cum_w = None
    cnt = 0
    triple_list = []
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit 1 after sub-game #" + str(cnt))
            return None
        s = game.cpre(w, get_strat=True)
        if cum_s is None:
            cum_s = s
            cum_w = w
        else:
            cum_s &= s
            cum_w &= w
        # another short-circuit exit
        if (not cum_s or not game.init() & cum_s):
            log.DBG_MSG("Short-circuit exit 2 after sub-game #" + str(cnt))
            return None
        triple_list.append((game, s, w))
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    # lets simplify transition functions
    #aig.restrict_latch_next_funs(cum_s)
    # what comes next is a fixpoint computation using a UPRE
    # step at a time in the global game and using it to get more
    # information from the local sub-games
    lose = BDD.true()
    lose_next = ~cum_w | gen_game.error()
    while lose_next != lose:
        lose = lose_next
        lose_next = lose | gen_game.upre(lose)
        #for i in range(len(triple_list)):
        #    wt = triple_list[i][2]
        #    gamet = triple_list[i][0]
        #    local_deps = set([x.lit for x in gamet.aig.iterate_latches()])
        #    rem_lats = aig.get_bdd_latch_deps(lose_next) - local_deps
        #    pt = lose_next
        #    if rem_lats:
        #        pt = lose_next.univ_abstract(
        #            BDD.make_cube(map(BDD, rem_lats)))
        #    #log.BDD_DMP(lose_next, "global losing area iterate")
        #    #log.BDD_DMP(pt, "new losing area")
        #    assert BDD.make_impl(~wt, pt) == BDD.true()
        #    if BDD.make_impl(pt, ~wt) != BDD.true():
        #        gamet.short_error = pt
        #        wt = backward_safety_synth(gamet)
        #        if (wt is None or not gamet.init() & wt):
        #            log.DBG_MSG("Short-circuit exit 3")
        #            return None
        #        st = gamet.cpre(wt, get_strat=True)
        #        #aig.restrict_latch_next_funs(st)
        #        triple_list[i] = (gamet, st, wt)
        #for t in triple_list:
        #    lose_next |= ~t[2]
    # after the fixpoint has been reached we can compute the error
    log.BDD_DMP(lose, "lose region")
    win = ~lose
    if (not win or not gen_game.init() & win):
        return None
    else:
        return win


def subgame_mapper(games, aig):
    s = None
    cum_s = None
    cnt = 0
    pair_list = []
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit 1 after sub-game #" + str(cnt))
            return None
        s = game.cpre(w, get_strat=True)
        if cum_s is None:
            cum_s = s
        else:
            cum_s &= s
        # another short-circuit exit
        if (not cum_s or not game.init() & cum_s):
            log.DBG_MSG("Short-circuit exit 2 after sub-game #" + str(cnt))
            return None
        pair_list.append((game, s))
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    # lets simplify transition functions
    aig.restrict_latch_next_funs(cum_s)
    return pair_list


def subgame_reducer(games, aig, argv, a=None, b=None, c=None):
    assert games
    if a is None:
        a = 2
    if b is None:
        b = -1
    if c is None:
        c = -1
    while len(games) >= 2:
        triple_list = []
        # we first compute an fij function for all pairs
        for i in range(0, len(games) - 1):
            for j in range(i + 1, len(games)):
                li = set(aig.get_bdd_latch_deps(games[i][1]))
                lj = set(aig.get_bdd_latch_deps(games[j][1]))
                cij = len(li & lj)
                nij = len(li | lj)
                sij = (games[i][1] & games[j][1]).dag_size()
                triple_list.append((i, j, a * cij + b * nij + c * sij))
        # now we get the best pair according to the fij function
        (i, j, val) = max(triple_list, key=lambda x: x[2])
        log.DBG_MSG("We must reduce games " + str(i) + " and " + str(j))
        # we must reduce games i and j now
        game = ConcGame(BDDAIG(aig).short_error(~(games[i][1] & games[j][1])),
                        use_trans=argv.use_trans)
        w = backward_safety_synth(game)
        if w is None:
            return None
        else:
            s = game.cpre(w, get_strat=True)
        games[i] = (game, s)
        games.pop(j)
        # lets simplify the transition relations
        aig.restrict_latch_next_funs(s)
    return games[0][1]
