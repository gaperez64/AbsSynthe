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

#include <assert.h>
#include <string>
#include <algorithm>
#include <iostream>
#include "cuddObj.hh"

#include "abssynthe.h"
#include "logging.h"
#include "aig.h"

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

static bool internalSolve(Cudd* mgr, BDDAIG* spec) {
    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    unsigned cnt = 0;
    BDD bad_transitions;
    BDD init_state = spec->initState();
    BDD error_states = spec->errorStates();
    BDD prev_error = ~mgr->bddOne();
    includes_init = ((init_state & error_states) != ~mgr->bddOne());
    while (!includes_init && error_states != prev_error) {
        prev_error = error_states;
        error_states = prev_error | upre(spec, prev_error, bad_transitions);
        includes_init = ((init_state & error_states) != ~mgr->bddOne());
        cnt++;
    }
    
    dbgMsg("Early exit? " + std::to_string(includes_init) + 
           ", after " + std::to_string(cnt) + " iterations.");

#ifndef NDEBUG
    spec->dump2dot(error_states & init_state, "uprestar_and_init.dot");
#endif

    // if !includes_init == true, then ~bad_transitions is the set of all
    // good transitions for controller (Eve)
    return !includes_init;
}

bool solve(AIG* spec_base) {
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    return internalSolve(&mgr, &spec);
}

bool compSolve1(AIG* spec_base) {
		bool latchless = false;
    bool cinput_independent = true;
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    std::vector<BDDAIG*> subgames = spec.decompose();
    if (subgames.size() == 0) return internalSolve(&mgr, &spec);

    if(std::all_of(subgames.begin(),subgames.end(),[](BDDAIG*sg){return (sg->numLatches() == 1);})){
			latchless = true;
			dbgMsg("We are going latchless\n");
		}
    // Check if subgames are cinput-independent
    std::set<unsigned> total_cinputs;
    for (std::vector<BDDAIG*>::iterator i = subgames.begin();
         i != subgames.end(); i++) {
      std::vector<unsigned> ic = (*i)->getCInputLits();
      std::set<unsigned> intersection;
      set_intersection(ic.begin(), ic.end(), total_cinputs.begin(), 
            total_cinputs.end(), std::inserter(intersection,intersection.begin()));
      if (intersection.size() > 0 ){
        cinput_independent = false;
        break;
      } else {
        total_cinputs.insert(ic.begin(), ic.end());
      }
    }   
    if (cinput_independent){
      dbgMsg("We are cinput-independent!");
    }
    // Let us aggregate the losing region
    BDD losing_states = spec.errorStates();
    BDD losing_transitions = ~mgr.bddOne();
    int gamecount = 0;
    std::vector<std::pair<BDD,BDD> > subgame_results;
    for (std::vector<BDDAIG*>::iterator i = subgames.begin();
         i != subgames.end(); i++) {
        gamecount++;
        dbgMsg("Solving a subgame");
        bool includes_init = false;
        unsigned cnt = 0;
        BDD bad_transitions;
        BDD init_state = (*i)->initState();
        BDD error_states = (*i)->errorStates();
        BDD prev_error = ~mgr.bddOne();
        includes_init = ((init_state & error_states) != ~mgr.bddOne());
        while (!includes_init && error_states != prev_error) {
            prev_error = error_states;
            error_states = prev_error | upre(*i, prev_error, bad_transitions);
            includes_init = ((init_state & error_states) != ~mgr.bddOne());
            cnt++;
        }
        
        dbgMsg("Early exit? " + std::to_string(includes_init) + 
               ", after " + std::to_string(cnt) + " iterations.");
        if (includes_init) {
#ifndef NDEBUG
            (*i)->dump2dot(init_state, "local_init.dot");
            (*i)->dump2dot(error_states & init_state, "uprestar_and_init.dot");
#endif
            return false;
        }
        else {
            // we aggregate the losing states and transitions
            // losing_states |= error_states;
            // losing_transitions |= bad_transitions;
						subgame_results.push_back(std::pair<BDD,BDD>(error_states, bad_transitions));
        }
        // we have to release the memory used for the caches and stuff
        delete (*i);
    }
    if (cinput_independent){
      return true;
    } else {
      std::vector<std::pair<BDD,BDD> >::iterator sg = subgame_results.begin();
      for (; sg != subgame_results.end(); sg++){
        losing_states |= sg->first;
        losing_transitions |= sg->second;
      }
    }
    // we now solve the aggregated game
    dbgMsg("");
    dbgMsg("Solving the aggregated game");
    BDDAIG aggregated_game(spec, losing_transitions);
    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    unsigned cnt = 0;
    BDD bad_transitions;
    BDD init_state = aggregated_game.initState();
    BDD error_states = aggregated_game.errorStates();
    BDD prev_error = ~mgr.bddOne();
    includes_init = ((init_state & error_states) != ~mgr.bddOne());
    while (!includes_init && error_states != prev_error) {
        prev_error = error_states;
        error_states = prev_error | upre(&aggregated_game, prev_error,
                                         bad_transitions);
        includes_init = ((init_state & error_states) != ~mgr.bddOne());
        cnt++;
    }
    
    dbgMsg("Early exit? " + std::to_string(includes_init) + 
           ", after " + std::to_string(cnt) + " iterations.");

    // if !includes_init == true, then ~bad_transitions is the set of all
    // good transitions for controller (Eve)
    return !includes_init;
}
