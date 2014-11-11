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

from abc import ABCMeta, abstractmethod
from itertools import imap
from utils import fixpoint
import log


# safety game template for the algorithms implemented here, they all
# use only the functions provided here
class Game:
    __metaclass__ = ABCMeta

    def upre(self, dst):
        raise NotImplementedError()

    def upost(self, src):
        raise NotImplementedError()

    def cpre(self, dst):
        raise NotImplementedError()

    def cpost(self, src):
        raise NotImplementedError()

    @abstractmethod
    def error(self):
        pass

    @abstractmethod
    def init(self):
        pass

    def is_env_state(self, state):
        raise NotImplementedError()


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
            local_lose = any(imap(is_loser, game.upost(s)))\
                if game.is_env_state(s)\
                else all(imap(is_loser, game.cpost(s)))
            if local_lose:
                losing[s] = True
                waiting.extend(depend[s])
            if sp not in losing or not losing[sp]:
                depend[sp] = depend[sp] | set([(s, sp)])
    log.DBG_MSG("OTFUR, losing[init_state] = " +
                str(losing[init_state]))
    return None if losing[init_state] else True


# Classical backward fixpoint algo
def backward_safety_synth(game):
    init_state = game.init()
    error_states = game.error()
    log.DBG_MSG("Computing fixpoint of UPRE.")
    win_region = ~fixpoint(
        error_states,
        fun=lambda x: x | game.upre(x),
        early_exit=lambda x: x & init_state
    )

    if not (win_region & init_state):
        return None
    else:
        return win_region
