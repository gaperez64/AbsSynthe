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

static unsigned optimizedGate(AIG* spec, unsigned a_lit, unsigned b_lit) {
    if (a_lit == 0 || b_lit == 0)
        return 0;
    if (a_lit == 1 && b_lit == 1)
        return 1;
    if (a_lit == 1)
        return b_lit;
    if (b_lit == 1)
        return a_lit;
    assert(a_lit > 1 && b_lit > 1);
    unsigned a_and_b_lit = (spec->maxVar() + 1) * 2;
    spec->addGate(a_and_b_lit, a_lit, b_lit);
    return a_and_b_lit;
}

/* I'm going to play a dangerous game here...
 * Since Cudd keeps a unique table with DdNodes that are currently referrenced
 * and the BDD class is in fact a wrapper for a pointer to such a node, I will
 * cache the actual address of the Nodes with their corresponding aig
 */
static unsigned bdd2aig(Cudd* mgr, BDDAIG* spec, BDD a_bdd, 
                        std::unordered_map<unsigned long, unsigned>* cache) {
    std::unordered_map<unsigned long, unsigned>::iterator cache_hit =
        cache->find((unsigned long) a_bdd.getRegularNode());
    if (cache_hit != cache->end()) {
        unsigned res = (*cache_hit).second;
        if (Cudd_IsComplement(a_bdd.getNode()))
            res = AIG::negateLit(res);
        return res;
    }

    if (Cudd_IsConstant(a_bdd.getNode()))
        return (a_bdd == mgr->bddOne()) ? 1 : 0;

    unsigned a_lit = a_bdd.NodeReadIndex();

    BDD then_bdd(*mgr, Cudd_T(a_bdd.getNode()));
    BDD else_bdd(*mgr, Cudd_E(a_bdd.getNode()));
    /* We are performing the following operation
     *
     * ite(a_bdd, then_bdd, else_bdd)
     * = a^then v ~a^else
     * = ~(~(a^then) ^ ~(~a^else))
     *
     * so we need 3 more ANDs
     */
    unsigned then_lit = bdd2aig(mgr, spec, then_bdd, cache);
    unsigned else_lit = bdd2aig(mgr, spec, else_bdd, cache);
    unsigned a_then_lit = optimizedGate(spec, a_lit, then_lit);
    unsigned na_else_lit = optimizedGate(spec, AIG::negateLit(a_lit), else_lit);
    unsigned n_a_then_lit = AIG::negateLit(a_then_lit);
    unsigned n_na_else_lit = AIG::negateLit(na_else_lit);
    unsigned ite_lit = optimizedGate(spec, n_a_then_lit, n_na_else_lit);
    unsigned res = AIG::negateLit(ite_lit);

    (*cache)[(unsigned long) a_bdd.getRegularNode()] = res;

    if (Cudd_IsComplement(a_bdd.getNode()))
        res = AIG::negateLit(res);

    return res;
}

static void synthAlgo(Cudd* mgr, BDDAIG* spec, BDD non_det_strategy,
                      BDD* ext_care_set=NULL) {
    BDD care_set;
    if (ext_care_set == NULL)
        care_set = mgr->bddOne();
    else
        care_set = *ext_care_set;

    BDD strategy = non_det_strategy;
    std::vector<aiger_symbol*> c_inputs = spec->getCInputs();
    std::vector<unsigned> c_input_lits;
    std::vector<BDD> c_input_funs;

    // as a first step, we compute a single bdd per controllable input
    for (std::vector<aiger_symbol*>::iterator i = c_inputs.begin();
         i != c_inputs.end(); i++) {
        BDD c = mgr->bddVar((*i)->lit);
        BDD others_cube = mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator j = c_inputs.begin();
             j != c_inputs.end(); j++) {
            if ((*i)->lit == (*j)->lit)
                continue;
            others_cube &= mgr->bddVar((*j)->lit);
        }
        BDD c_arena = strategy.ExistAbstract(others_cube);
        // pairs (x,u) in which c can be true
        BDD can_be_true = c_arena.Cofactor(c);
        // pairs (x,u) in which c can be false
        BDD can_be_false = c_arena.Cofactor(~c);
        BDD must_be_true = (~can_be_false) & can_be_true;
        BDD must_be_false = (~can_be_true) & can_be_false;
        BDD local_care_set = care_set & (must_be_true | must_be_false);
        // on care set: must_be_true.restrict(care_set) <-> must_be_true
        // or         ~(must_be_false).restrict(care_set) <-> ~must_be_false
        BDD opt1 = BDDAIG::safeRestrict(must_be_true, local_care_set);
        BDD opt2 = BDDAIG::safeRestrict(~must_be_false, local_care_set);
        BDD res;
        if (opt1.nodeCount() < opt2.nodeCount())
            res = opt1;
        else
            res = opt2;
        dbgMsg("Size of function for " + std::to_string(c.NodeReadIndex()) + " = " +
               std::to_string(res.nodeCount()));
        strategy &= (~c | res) & (~res | c);
        c_input_funs.push_back(res);
        c_input_lits.push_back((*i)->lit);
    }
    
    // we now get rid of all controllable inputs in the aig spec by replacing
    // each one with an and computed using bdd2aig...
    // NOTE: because of the way bdd2aig is implemented, we must ensure that BDDs are
    // no longer operated on after this point!
    std::unordered_map<unsigned long, unsigned> cache;
    std::vector<unsigned>::iterator i = c_input_lits.begin();
    std::vector<BDD>::iterator j = c_input_funs.begin();
    for (; i != c_input_lits.end();) {
        spec->input2gate(*i, bdd2aig(mgr, spec, *j, &cache));
        i++;
        j++;
    }
    // Finally, we write the modified spec to file
    spec->writeToFile(settings.out_file);
}

static BDD substituteLatchesNext(BDDAIG* spec, BDD dst, BDD* care_region=NULL) {
    BDD result;
    if (settings.use_trans) {
        BDD trans_rel_bdd = spec->transRelBdd();
        if (care_region != NULL)
            trans_rel_bdd = BDDAIG::safeRestrict(trans_rel_bdd, *care_region);
        BDD primed_dst = spec->primeLatchesInBdd(dst);
        BDD primed_latch_cube = spec->primedLatchCube();
        result = trans_rel_bdd.AndAbstract(primed_dst,
                                           primed_latch_cube);
    } else {
        std::vector<BDD> next_funs = spec->nextFunComposeVec(care_region);
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
    BDD not_dst = ~dst;
    trans_bdd = substituteLatchesNext(spec, dst, &not_dst);
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
    if (!includes_init && settings.out_file != NULL)
        synthAlgo(mgr, spec, ~bad_transitions);
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
#ifndef NDEBUG
    if(std::all_of(subgames.begin(), subgames.end(), 
                   [](BDDAIG*sg){ return (sg->numLatches() == 1); })) {
        latchless = true;
        errMsg("We are going latchless");
    }
#endif
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
    dbgMsg("Are we cinput-independent? " + std::to_string(cinput_independent));
    // Let us aggregate the losing region
    BDD losing_states = spec.errorStates();
    BDD losing_transitions = ~mgr.bddOne();
    int gamecount = 0;
    std::vector<std::pair<BDD,BDD> > subgame_results;
    for (std::vector<BDDAIG*>::iterator i = subgames.begin();
         i != subgames.end(); i++) {
        gamecount++;
        dbgMsg("");
        dbgMsg("Solving a subgame (" + std::to_string((*i)->numLatches()) +
               " latches)");
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
            subgame_results.push_back(std::pair<BDD,BDD>(error_states,
                                                         bad_transitions));
        }
        // we have to release the memory used for the caches and stuff
        delete (*i);
    }

    BDD bad_transitions;
    bool includes_init = false;
    if (!cinput_independent){ // we still have one game to solve
        std::vector<std::pair<BDD,BDD> >::iterator sg = subgame_results.begin();
        for (sg = subgame_results.begin(); sg != subgame_results.end(); sg++){
            losing_states |= sg->first;
            losing_transitions |= sg->second;
        }
        // we now solve the aggregated game
        dbgMsg("Solving the aggregated game");
        BDDAIG aggregated_game(spec, losing_transitions);
        dbgMsg("Computing fixpoint of UPRE.");
        unsigned cnt = 0;
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
    } else if (settings.out_file != NULL) {
        // we have to output a strategy so we should aggregate the good
        // transitions
        bad_transitions = ~mgr.bddOne();
        std::vector<std::pair<BDD,BDD> >::iterator sg = subgame_results.begin();
        for (sg = subgame_results.begin(); sg != subgame_results.end(); sg++)
            bad_transitions |= sg->second;
    }

    // if !includes_init == true, then ~bad_transitions is the set of all
    // good transitions for controller (Eve)
    if (!includes_init && settings.out_file != NULL)
        synthAlgo(&mgr, &spec, ~bad_transitions);
    return !includes_init;
}
