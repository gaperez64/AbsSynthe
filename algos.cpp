/**************************************************************************
 * Copyright (c) 2015, Guillermo A. Perez, Universite Libre de Bruxelles
 * 
 * This file is part of the (Swiss) AbsSynthe tool.
 * 
 * AbsSynthe is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * AbsSynthe is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with AbsSynthe.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * 
 * Guillermo A. Perez
 * Universite Libre de Bruxelles
 * gperezme@ulb.ac.be
 *************************************************************************/

#include <string>

#include "abssynthe.h"
#include "logging.h"
#include "aig.h"

bool solve(AIG* spec) {
    
    init_state = game.init()
    error_states = game.error()
    dbgMsg("Computing fixpoint of UPRE.")
    win_region = ~fixpoint(
        error_states,
        fun=lambda x: x | game.upre(x),
        early_exit=lambda x: x & init_state
    )

    if not (win_region & init_state):
        return None
    else:
        return win_region
}
