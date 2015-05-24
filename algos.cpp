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
#include <ctime>
#include <list>
#include <set>
#include <tuple>
#include <cfloat>
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

static bool internalSolve(Cudd* mgr, BDDAIG* spec, const BDD * upre_init, 
			BDD * losing_region, BDD * losing_transitions) {
    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    unsigned cnt = 0;
    BDD bad_transitions;
    BDD init_state = spec->initState();
		BDD error_states;
		if (upre_init){
			error_states = *upre_init;
		} else {
    	error_states = spec->errorStates();
		}
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
		if (losing_region){
			*losing_region = error_states;
		}
		if (losing_transitions){
			*losing_transitions = bad_transitions;
		}
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
    return internalSolve(&mgr, &spec, NULL, NULL, NULL);
}

struct bdd_pair_compare{
  bool operator()(std::pair<BDD,BDD> & u, std::pair<BDD,BDD> &v){
    int u_ = u.second.nodeCount();
    int v_ = v.second.nodeCount();
    return u_ < v_;
  }
}bdd_pair_cmp;

bool compSolve1(AIG* spec_base) {
		// whether we use the locally winning max. strategies to define the
		// aggregate game
		// bool use_strat = false;
    bool latchless = false;
    bool cinput_independent = true;
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    std::vector<BDDAIG*> subgames = spec.decompose();
    if (subgames.size() == 0) return internalSolve(&mgr, &spec, NULL, NULL, NULL);
    if(std::all_of(subgames.begin(), subgames.end(), 
                   [](BDDAIG*sg){ return (sg->numLatches() == 1); })) {
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
                         total_cinputs.end(), 
                         std::inserter(intersection,intersection.begin()));
        if (intersection.size() > 0 ) {
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
        dbgMsg("Solving subgame " + std::to_string(gamecount) + " (" +
               std::to_string((*i)->numLatches()) + " latches)");
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
        
        dbgMsg("Early exit at game " + std::to_string(gamecount) + "? " + std::to_string(includes_init) + 
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
    if (latchless && cinput_independent){
			// TODO Implement a synthesis procedure in this case
      return true;
    } else {
			// TODO In the Python version not intersecting losing_transitions
			// but rather defining the aggregate game with the error function 
			// ferror | losing_states was more efficient. Do this here.
      std::vector<std::pair<BDD,BDD> >::iterator sg = subgame_results.begin();
      std::sort(subgame_results.begin(), subgame_results.end(), bdd_pair_cmp);
      for (sg = subgame_results.begin(); sg != subgame_results.end(); sg++){
        losing_states |= sg->first;
        // losing_transitions |= sg->second;
      }
    }
    // we now solve the aggregated game
    dbgMsg("Solving the aggregated game");
    // BDDAIG aggregated_game(spec, losing_transitions);
    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    BDD bad_transitions;
    if (!cinput_independent){ // we still have one game to solve
        // we now solve the aggregated game
        dbgMsg("Computing *global* fixpoint of UPRE.");
        unsigned cnt = 0;
        BDD init_state = spec.initState();
        BDD error_states = losing_states;
        BDD prev_error = ~mgr.bddOne();
        includes_init = ((init_state & error_states) != ~mgr.bddOne());
        while (!includes_init && error_states != prev_error) {
            prev_error = error_states;
            //error_states = prev_error | upre(&aggregated_game, prev_error,
            //                                 bad_transitions);
            error_states = prev_error | upre(&spec, prev_error, bad_transitions);
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

using namespace std;
bool compSolve2(AIG* spec_base) {
    typedef pair<BDD, set<unsigned> > subgame_info;
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    std::vector<BDDAIG*> subgames = spec.decompose();
    if (subgames.size() == 0) return internalSolve(&mgr, &spec, NULL, NULL, NULL);

		// Solving now the subgames
		BDD losing_transitions;
    int gamecount = 0;
		list<subgame_info> subgame_results;
		int total_bdd_size = 0;
		int total_cinp_size = 0;
    for (std::vector<BDDAIG*>::iterator i = subgames.begin();
         i != subgames.end(); i++) {
        gamecount++;
        dbgMsg("Solving subgame " + std::to_string(gamecount) + " (" +
               std::to_string((*i)->numLatches()) + " latches)");
				if (!internalSolve(&mgr, *i, NULL, NULL, &losing_transitions)){
            return false;
        }
				vector<unsigned> cinput_vect = (*i)->getCInputLits();
				set<unsigned> cinput_set(cinput_vect.begin(), cinput_vect.end());
				subgame_results.push_back(subgame_info(losing_transitions, cinput_set));
				total_bdd_size += losing_transitions.nodeCount();
				total_cinp_size += cinput_set.size();
        // we have to release the memory used for the caches and stuff
        delete (*i);
    }
		double mean_bdd_size = total_bdd_size / subgame_results.size();
		double mean_cinp_size = total_cinp_size / subgame_results.size();
		double cinp_factor = 0.5 * mean_bdd_size / mean_cinp_size;
		// TODO We should now check for cinput-independence and latchless
		while (subgame_results.size() >= 2){
			// final_iteration = (subgame_results.size() == 2);
			// Get the pair min_i,min_j that minimizes the score
			// The score is defined as 
			// 					b.countNode() + cinp_factor * cinp_union.size()
			// where b is the disjunction of the error functions, and cinp_union
			// is the union of the cinputs of the subgames.
			int min_i, min_j;														 // the indices of the selected games
			list<subgame_info>::iterator min_it, min_jt; // iterators to selected games
			double best_score = DBL_MAX; 								 // the score of the selected pair
			BDD joint_err; 															 // the disjunction of the error function of the pair
			set<unsigned> joint_cinp;										 // union of the cinp dependencies

			list<subgame_info>::iterator it, jt;
			int i,j;
			for (i=0, it = subgame_results.begin(); 
						it != subgame_results.end(); i++, it++){
				jt = it; jt++;
				j = i + 1;
				for (; jt != subgame_results.end(); j++, jt++){
					BDD b = it->first | jt->first;
					set<unsigned> cinp_union;
					set_union(it->second.begin(), it->second.end(), 
								jt->second.begin(), jt->second.end(), inserter(cinp_union,cinp_union.begin()));
					double score = b.nodeCount() + cinp_factor * cinp_union.size();
					if (score < best_score){
						min_i = i;
						min_j = j;
						min_it = it;
						min_jt = jt;
						joint_err = b;
						joint_cinp = cinp_union;
						best_score = score;
					}
				}
			}
		  dbgMsg("Selected subgames " + to_string(min_i) + " and " + to_string(min_j));
			BDDAIG subgame(spec, joint_err);
			BDD losing_transitions;
      set<unsigned> intersection;
      set_intersection(min_it->second.begin(), min_it->second.end(),
                 min_jt->second.begin(), min_jt->second.end(), 
                 inserter(intersection, intersection.begin()));
      bool sub_realizable;
      if (intersection.size() == 0){
           // TODO Is it correct if we don't compute upre here?
           // Check with Guillermo
      }
      sub_realizable = internalSolve(&mgr, &subgame, NULL, NULL, &losing_transitions);
			if (!sub_realizable) return false;
			subgame_results.erase(min_it);
			subgame_results.erase(min_jt);
			subgame_results.push_back(subgame_info(losing_transitions, joint_cinp));
		}
		return true;
}

bool compSolve3(AIG* spec_base) {
    typedef pair<BDD, BDD> subgame_info;
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    resetTimer("decompose");
    std::vector<BDDAIG*> subgames = spec.decompose();
    cout << "Decomposition ended with " << subgames.size() << " subgames\n";
    if (subgames.size() == 0) return internalSolve(&mgr, &spec, NULL, NULL, NULL);
		// Solving now the subgames
		BDD losing_transitions;
    BDD losing_region;
    BDD global_lose = mgr.bddZero();
		vector<subgame_info> subgame_results;
    for (int i = 0; i < subgames.size(); i++) {
        dbgMsg("Solving subgame " + std::to_string(i) + " (" +
               std::to_string(subgames[i]->numLatches()) + " latches)");
				if (!internalSolve(&mgr, subgames[i], NULL, &losing_region, &losing_transitions)){
            return false;
        }
				subgame_results.push_back(subgame_info(~losing_region, ~losing_transitions));
        global_lose |= losing_region;
        BDDAIG * old_sg = subgames[i];
        subgames[i] = new BDDAIG(*subgames[i], losing_transitions);
        delete(old_sg);
    }
    addTime("decompose");
    dbgMsg("");
    dbgMsg("Now refining the aggregate game");
    BDD prev_lose = mgr.bddOne();
    BDD tmp_lose;
    BDD tmp_losing_trans;
    int count = 1;
    while(prev_lose != global_lose){
      dbgMsg("Refinement iterate: " + to_string(count++));
      resetTimer("localstep");
      prev_lose = global_lose;
      for (int i = 0; i < subgames.size(); i++){
          BDDAIG * subgame = subgames[i];
          subgame_info & sg_info = subgame_results[i];
          vector<unsigned> latches_u = spec.getLatchLits();
          set<unsigned> latches_sg = spec.getBddLatchDeps(sg_info.second);
          set<unsigned> rem_latches;
          set_difference(latches_u.begin(), latches_u.end(), 
              latches_sg.begin(), latches_sg.end(), 
              inserter(rem_latches, rem_latches.begin()));
          BDD local_lose = global_lose.UnivAbstract(spec.toCube(rem_latches));
          BDD & local_win_over = sg_info.first;
          // if local_lose intersects local_win_over
          if ( ~(local_lose & local_win_over) != mgr.bddOne() ){
            if (!internalSolve(&mgr, subgame, &local_lose, 
                &tmp_lose, &tmp_losing_trans)){
                  return false;
            }
            // subgames[i] = new BDDAIG(*subgame, tmp_losing_trans);
            // delete(subgame);
            sg_info.first = ~tmp_lose;
            sg_info.second = ~tmp_losing_trans;
            global_lose |= tmp_lose;
          }
      }
      addTime("localstep");
      if (global_lose == prev_lose){
        dbgMsg("Global Upre");
        BDD dummy;
        resetTimer("globalstep");
        global_lose = global_lose | upre(&spec, global_lose, dummy);
        addTime("globalstep");
      } else {
        dbgMsg("Local Upre");
      }
    }
    return true;
}
