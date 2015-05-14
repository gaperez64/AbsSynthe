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

static BDD safeRestrict(BDD original, BDD rest_region) {
    BDD approx = original.Restrict(rest_region);
    if (approx.nodeCount() < original.nodeCount())
        return approx;
    else
        return original;
}

static BDD substituteLatchesNext(BDDAIG* spec, BDD dst) {
    BDD result;
    if (settings.use_trans) {
        BDD trans_rel_bdd = spec->transRelBdd();
        BDD primed_dst = spec->primeLatchesInBdd(dst);
        BDD primed_latch_cube = spec->primedLatchCube();
        result = trans_rel_bdd.AndAbstract(primed_dst,
                                           primed_latch_cube);
    } else {
        std::vector<BDD> next_funs = spec->nextFunComposeVec();
        result = dst.VectorCompose(next_funs);
#if false       
        BDD trans_rel_bdd = spec->transRelBdd();
        BDD primed_dst = spec->primeLatchesInBdd(dst);
        BDD primed_latch_cube = spec->primedLatchCube();
        BDD result2 = trans_rel_bdd.AndAbstract(primed_dst,
                                                primed_latch_cube);
        if (result != result2) {
            errMsg("Vector compose resulted in the wrong BDD");
        }
#endif
    }
    return result;
}

// NOTE: trans_bdd contains the set of all transitions going into bad
// states after the upre step (the complement of all good transitions)
static BDD upre(BDDAIG* spec, BDD dst, BDD &trans_bdd) {
    trans_bdd = substituteLatchesNext(spec, dst);
    BDD cinput_cube = spec->cinputCube();
    BDD uinput_cube = spec->uinputCube();
    BDD temp_bdd = trans_bdd.UnivAbstract(cinput_cube);
    return temp_bdd.ExistAbstract(uinput_cube);
}

bool solve(AIG* spec_base) {
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);

    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    unsigned cnt = 0;
    BDD bad_transitions;
    BDD init_state = spec.initState();
    BDD error_states = spec.errorStates();
    BDD prev_error = ~mgr.bddOne();
        includes_init = ((init_state & error_states) != ~mgr.bddOne());
    while (!includes_init && error_states != prev_error) {
        prev_error = error_states;
        error_states = prev_error | upre(&spec, prev_error, bad_transitions);
        includes_init = ((init_state & error_states) != ~mgr.bddOne());
        cnt++;
    }
    
    dbgMsg("Early exit? " + std::to_string(includes_init) + 
           ", after " + std::to_string(cnt) + " iterations.");

#ifndef NDEBUG
    spec.dump2dot(error_states & init_state, "uprestar_and_init.dot");
#endif

    // if !includes_init == true, then ~bad_transitions is the set of all
    // good transitions for controller (Eve)
    return !includes_init;
}
