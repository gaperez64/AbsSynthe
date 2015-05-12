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

#include "cuddObj.hh"

#include "abssynthe.h"
#include "logging.h"
#include "aig.h"

static void substituteLatchesNext(BDDAIG* spec, BDD* dst, BDD &result) {
    if (settings.use_trans) {
        BDD* trans_rel_bdd = spec->transRelBdd();
        BDD primed_dst;
        spec->primeLatchesInBdd(dst, primed_dst);
        result = trans_rel_bdd->AndAbstract(primed_dst,
                                            *spec->primedLatchCube());
    } else {
        result = dst->VectorCompose(*spec->nextFunComposeVec());
    }
}

// NOTE: trans_bdd contains the set of all transitions going into bad
// states after the upre step (the complement of all good transitions)
static void upre(BDDAIG* spec, BDD* dst, BDD &result, BDD &trans_bdd) {
    substituteLatchesNext(spec, dst, trans_bdd);
    BDD temp_bdd = trans_bdd.UnivAbstract(*spec->cinputCube());
    result = temp_bdd.ExistAbstract(*spec->uinputCube());
}

bool solve(AIG* spec_base) {
    Cudd mgr(0, 0);
    BDD init_state, error_states, prev_error;
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);

    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    BDD bad_transitions;
    spec.initState(init_state);
    spec.errorStates(error_states);
    prev_error = mgr.bddZero();
    while (!includes_init && error_states != prev_error) {
        prev_error = error_states;
        upre(&spec, &prev_error, error_states, bad_transitions);
        error_states = prev_error | error_states;
        includes_init = ((error_states & init_state) != mgr.bddZero());
    }
    // if !includes_init == true, then ~bad_transitions is the set of all
    // good transitions for controller (Eve)
    
    return !includes_init;
}

