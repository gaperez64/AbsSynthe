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

from functools import reduce
import log


def never(x):
    return False


def fixpoint(s, fun, early_exit=never):
    """ fixpoint of monotone function starting from s """
    prev = None
    cur = s
    cnt = 0
    while prev is None or prev != cur:
        prev = cur
        cur = fun(prev)
        cnt += 1
        if early_exit(cur):
            log.DBG_MSG("Early exit after " + str(cnt) + " steps.")
            return cur
    log.DBG_MSG("Fixpoint reached after " + str(cnt) + " steps.")
    return cur


def funcomp(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)
