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

static std::vector<std::pair<unsigned, BDD>> synthAlgo(Cudd* mgr,
                                                       BDDAIG* spec,
                                                       BDD non_det_strategy,
                                                       BDD care_set) {
    BDD strategy = non_det_strategy;
#ifndef NDEBUG
    spec->dump2dot(strategy, "strategy.dot");
    std::set<unsigned> deps = spec->semanticDeps(strategy);
    std::string litstring;
    for (std::set<unsigned>::iterator i = deps.begin();
         i != deps.end(); i++)
        litstring += std::to_string(*i) + ", ";
    dbgMsg(litstring);
#endif
    std::vector<aiger_symbol*> c_inputs = spec->getCInputs();
    std::vector<unsigned> c_input_lits;
    std::vector<BDD> c_input_funs;

    dbgMsg("non-det strategy BDD size: " +
           std::to_string(non_det_strategy.nodeCount()));

    // as a first step, we compute a single bdd per controllable input
    for (std::vector<aiger_symbol*>::iterator i = c_inputs.begin();
         i != c_inputs.end(); i++) {
        BDD c = mgr->bddVar((*i)->lit);
        BDD others_cube = mgr->bddOne();
        unsigned others_count = 0;
        for (std::vector<aiger_symbol*>::iterator j = c_inputs.begin();
             j != c_inputs.end(); j++) {
            dbgMsg("CInput " + std::to_string((*j)->lit));
            if ((*i)->lit == (*j)->lit)
                continue;
            others_cube &= mgr->bddVar((*j)->lit);
            dbgMsg("Other cube has lit " + std::to_string((*j)->lit));
            others_count++;
        }
        BDD c_arena;
        if (others_count > 0)
            c_arena = strategy.ExistAbstract(others_cube);
        else {
            dbgMsg("No need to abstract other cinputs");
            c_arena = strategy;
        }
#ifndef NDEBUG
        spec->dump2dot(c_arena, "c_arena.dot");
        spec->dump2dot(c_arena.Cofactor(c), "c_arena_true.dot");
#endif
        // pairs (x,u) in which c can be true
        BDD can_be_true = c_arena.Cofactor(c);
        dbgMsg("Can be true BDD size: " + std::to_string(can_be_true.nodeCount()));
        // pairs (x,u) in which c can be false
        BDD can_be_false = c_arena.Cofactor(~c);
        dbgMsg("Can be false BDD size: " + std::to_string(can_be_false.nodeCount()));
        BDD must_be_true = (~can_be_false) & can_be_true;
        dbgMsg("Must be true BDD size: " + std::to_string(must_be_true.nodeCount()));
        BDD must_be_false = (~can_be_true) & can_be_false;
        dbgMsg("Must be false BDD size: " + std::to_string(must_be_false.nodeCount()));
        BDD local_care_set = care_set & (must_be_true | must_be_false);
        // on care set: must_be_true.restrict(care_set) <-> must_be_true
        // or         ~(must_be_false).restrict(care_set) <-> ~must_be_false
        BDD opt1 = BDDAIG::safeRestrict(must_be_true, local_care_set);
        dbgMsg("opt1 BDD size: " + std::to_string(opt1.nodeCount()));
        BDD opt2 = BDDAIG::safeRestrict(~must_be_false, local_care_set);
        dbgMsg("opt2 BDD size: " + std::to_string(opt2.nodeCount()));
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

    std::vector<std::pair<unsigned, BDD>> result;
    std::vector<unsigned>::iterator i = c_input_lits.begin();
    std::vector<BDD>::iterator j = c_input_funs.begin();
    for (; i != c_input_lits.end();) {
        result.push_back(std::make_pair(*i, *j));
        i++;
        j++;
    }

    return result;
}

void finalizeSynth(Cudd* mgr, BDDAIG* spec, 
                   std::vector<std::pair<unsigned, BDD>> result) {
    // we now get rid of all controllable inputs in the aig spec by replacing
    // each one with an and computed using bdd2aig...
    // NOTE: because of the way bdd2aig is implemented, we must ensure that BDDs are
    // no longer operated on after this point!
    std::unordered_map<unsigned long, unsigned> cache;
    for (std::vector<std::pair<unsigned, BDD>>::iterator i = result.begin();
         i != result.end(); i++)
        spec->input2gate(i->first, bdd2aig(mgr, spec, i->second, &cache));
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

static bool internalSolve(Cudd* mgr, BDDAIG* spec, const BDD* upre_init, 
                          BDD* losing_region, BDD* losing_transitions,
                          bool do_synth=true) {
    dbgMsg("Computing fixpoint of UPRE.");
    bool includes_init = false;
    unsigned cnt = 0;
    BDD bad_transitions;
    BDD init_state = spec->initState();
    BDD error_states;
    if (upre_init != NULL) {
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
    if (losing_region != NULL) {
        *losing_region = error_states;
    }
    if (losing_transitions != NULL){
        *losing_transitions = bad_transitions;
    }
    // if !includes_init == true, then ~bad_transitions is the set of all
    // good transitions for controller (Eve)
    if (!includes_init && do_synth)
        finalizeSynth(mgr, spec, 
                      synthAlgo(mgr, spec, ~bad_transitions, ~error_states));
    return !includes_init;
}

bool solve(AIG* spec_base) {
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    return internalSolve(&mgr, &spec, NULL, NULL, NULL);
}

struct {
    bool operator()(std::pair<BDD, BDD> &u, std::pair<BDD, BDD> &v){
        int u_ = u.second.nodeCount();
        int v_ = v.second.nodeCount();
        return u_ < v_;
    }
} bddPairCompare;

bool compSolve1(AIG* spec_base) {
    Cudd mgr(0, 0);
    mgr.AutodynEnable(CUDD_REORDER_SIFT);
    BDDAIG spec(*spec_base, &mgr);
    std::vector<BDDAIG*> subgames = spec.decompose();
    unsigned gamecount = 0;
    if (subgames.size() == 0) return internalSolve(&mgr, &spec, NULL, NULL, NULL);
    std::vector<std::pair<BDD,BDD> > subgame_results;
    for (std::vector<BDDAIG*>::iterator i = subgames.begin();
         i != subgames.end(); i++) {
        gamecount++;
        BDD error_states;
        BDD bad_transitions;
        dbgMsg("Solving subgame " + std::to_string(gamecount) + " (" +
               std::to_string((*i)->numLatches()) + " latches)");
        if (!internalSolve(&mgr, *i, NULL, &error_states, &bad_transitions, false)) {
            return false;
        } else {
            subgame_results.push_back(std::pair<BDD,BDD>(error_states,
                                                         bad_transitions));
        }
    }

    bool includes_init = false;
    BDD bad_transitions;

    // Check if subgames are cinput-independent
    bool cinput_independent = true;
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

    if (!cinput_independent) { // we still have one game to solve
        BDD losing_states = spec.errorStates();
        BDD losing_transitions = ~mgr.bddOne();
        std::vector<std::pair<BDD, BDD> >::iterator sg = subgame_results.begin();
        std::sort(subgame_results.begin(), subgame_results.end(), bddPairCompare);
        for (sg = subgame_results.begin(); sg != subgame_results.end(); sg++){
            losing_states |= sg->first;
            losing_transitions |= sg->second;
        }
        dbgMsg("Solving the aggregated game");
        // TODO: try out using losing_states instead of losing_transition here
        BDDAIG aggregated_game(spec, losing_transitions);
        BDD error_states;
        includes_init = !internalSolve(&mgr, &aggregated_game, &losing_states,
                                       &error_states, &bad_transitions, false);

        // if !includes_init == true, then ~bad_transitions is the set of all
        // good transitions for controller (Eve)
        if (!includes_init && settings.out_file != NULL)
        finalizeSynth(&mgr, &spec, 
                      synthAlgo(&mgr, &spec, ~bad_transitions, ~error_states));

    } else if (settings.out_file != NULL) {
        // we have to output a strategy from the local non-deterministic
        // strategies...
#if true
        std::vector<std::pair<unsigned, BDD>> all_cinput_strats;
        std::vector<std::pair<BDD, BDD> >::iterator sg = subgame_results.begin();
        for (std::vector<BDDAIG*>::iterator i = subgames.begin();
             i != subgames.end(); i++) {
            std::vector<std::pair<unsigned, BDD>> temp;
            temp = synthAlgo(&mgr, *i, ~sg->second, ~sg->first);
            all_cinput_strats.insert(all_cinput_strats.end(), 
                                     temp.begin(), temp.end());
            sg++;
        }
        finalizeSynth(&mgr, &spec, all_cinput_strats);
#endif
#if false
        BDD losing_states = spec.errorStates();
        BDD losing_transitions = ~mgr.bddOne();
        std::vector<std::pair<BDD, BDD> >::iterator sg = subgame_results.begin();
        std::sort(subgame_results.begin(), subgame_results.end(), bddPairCompare);
        for (sg = subgame_results.begin(); sg != subgame_results.end(); sg++){
            losing_states |= sg->first;
            losing_transitions |= sg->second;
        }
        finalizeSynth(&mgr, &spec, 
                      synthAlgo(&mgr, &spec, ~losing_transitions, ~losing_states));
#endif
    }

    // release cache memory and other stuff used in BDDAIG instances
    for (std::vector<BDDAIG*>::iterator i = subgames.begin();
         i != subgames.end(); i++)
        delete *i;

    return !includes_init;
}

using namespace std;
// subgame, error bdd size, and cinputs
// typedef std::tuple<BDD, unsigned, set<unsigned> > subgame_info;
typedef pair<BDD, set<unsigned>> subgame_info;
bool compSolve2(AIG* spec_base) {
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
        bool final_iteration = false;
        while (subgame_results.size() >= 2){
            final_iteration = (subgame_results.size() == 2);
            // Get the pair min_i,min_j that minimizes the score
            // The score is defined as 
            //                  b.countNode() + cinp_factor * cinp_union.size()
            // where b is the disjunction of the error functions, and cinp_union
            // is the union of the cinputs of the subgames.
            int min_i, min_j;                                                        // the indices of the selected games
            list<subgame_info>::iterator min_it, min_jt; // iterators to selected games
            double best_score = DBL_MAX;                                 // the score of the selected pair
            BDD joint_err;                                                           // the disjunction of the error function of the pair
            set<unsigned> joint_cinp;                                        // union of the cinp dependencies

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
            bool sub_realizable = internalSolve(&mgr, &subgame, NULL, NULL, &losing_transitions);
            if (!sub_realizable) return false;
            subgame_results.erase(min_it);
            subgame_results.erase(min_jt);
            subgame_results.push_back(subgame_info(losing_transitions, joint_cinp));
        }
        return true;
}
