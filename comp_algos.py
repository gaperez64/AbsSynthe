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


def subgame_mapper(games):
    s = None
    cnt = 0
    pair_list = []
    for game in games:
        assert isinstance(game, BackwardGame)
        w = backward_safety_synth(game)
        cnt += 1
        # short-circuit a negative response
        if w is None:
            log.DBG_MSG("Short-circuit exit after sub-game #" + str(cnt))
            return None
        if s is None:
            s = game.cpre(w, get_strat=True)
        else:
            s &= game.cpre(w, get_strat=True)
        # sanity check before moving forward
        if (not s or not game.init() & s):
            return None
        pair_list.append((game, s))
    log.DBG_MSG("Solved " + str(cnt) + " sub games.")
    return pair_list


def subgame_reducer(games, aig, argv, a=None, b=None):
    assert games
    if a is None:
        a = 2
    if b is None:
        b = -1
    while len(games) >= 2:
        triple_list = []
        # we first compute an fij function for all pairs
        for i in range(0, len(games) - 1):
            for j in range(i + 1, len(games)):
                li = set(aig.get_bdd_latch_deps(games[i][1]))
                lj = set(aig.get_bdd_latch_deps(games[j][1]))
                cij = len(li & lj)
                nij = len(li | lj)
                triple_list.append((i, j, a * cij + b * nij))
        # now we get the best pair according to the fij function
        (i, j, val) = max(triple_list, key=lambda x: x[2])
        log.DBG_MSG("We must reduce games " + str(i) + " and " + str(j))
        # we must reduce games i and j now
        game = ConcGame(BDDAIG(aig).short_error(~(games[i][1] & games[j][1])),
                        restrict_like_crazy=argv.restrict_like_crazy,
                        use_trans=argv.use_trans)
        w = backward_safety_synth(game)
        if w is None:
            return None
        else:
            s = game.cpre(w, get_strat=True)
        games[i] = (game, s)
        games.pop(j)
    return games[0][1]
