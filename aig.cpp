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

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <string>
#include <vector>
#include <set>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <iterator>

#include "cudd.h"
#include "cuddObj.hh"

#include "aiger.h"
#include "aig.h"
#include "logging.h"

unsigned AIG::maxVar() {
    return this->spec->maxvar;
}

void AIG::introduceErrorLatch() {
    if (this->error_fake_latch != NULL)
        return;
    this->error_fake_latch = (aiger_symbol*) malloc(sizeof(aiger_symbol));
    this->error_fake_latch->name = new char[6];
    strncpy(this->error_fake_latch->name, "error", 6);
    this->error_fake_latch->lit = (this->maxVar() + 1) * 2;
    this->error_fake_latch->next = this->spec->outputs[0].lit;
    dbgMsg(std::string("Error fake latch = ") + 
           std::to_string(this->error_fake_latch->lit));
}

AIG::AIG(const char* aiger_file_name, bool intro_error_latch) {
    // default values for some local (for this instance) variables
    this->error_fake_latch = NULL;
    this->spec = NULL;
    this->lit2deps_map = new std::unordered_map<unsigned, std::set<unsigned>>();
    this->lit2ninputand_map =
        new std::unordered_map<unsigned,
                               std::pair<std::vector<unsigned>,
                                         std::vector<unsigned>>>();
    // start lodaing
    this->spec = aiger_init();
    const char* err = aiger_open_and_read_from_file (spec, aiger_file_name);
    if (err) {
        errMsg(std::string("Error ") + err +
               " encountered while reading AIGER file " +
               aiger_file_name);
        exit(1);
    }
    if (spec->num_outputs != 1) {
        errMsg(std::string() +
               std::to_string(spec->num_outputs) + " > 1 number of outputs in " +
               "AIGER file " +
               aiger_file_name);
        exit(1);
    }
    // let us now build the vector of latches, c_inputs, and u_inputs
    for (int i = 0; i < spec->num_latches; i++)
        this->latches.push_back(spec->latches + i);
    // we now introduce a fake latch for the error function
    if (intro_error_latch) {
        this->introduceErrorLatch();
        this->latches.push_back(this->error_fake_latch);
    }
    for (int i = 0; i < spec->num_inputs; i++) {
        aiger_symbol* symbol = spec->inputs + i;
        std::string name(symbol->name);
        if (name.find("controllable") == 0) // starts with "controllable"
            this->c_inputs.push_back(symbol);
        else
            this->u_inputs.push_back(symbol);
    }

#ifndef NDEBUG
    // print some debug information
    std::string litstring;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::string() + std::to_string(this->latches.size()) + " Latches: " +
           litstring);
    litstring.clear();
    for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
         i != this->c_inputs.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::string() + std::to_string(this->c_inputs.size()) + " C.Inputs: " +
           litstring);
    litstring.clear();
    for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
         i != this->u_inputs.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::string() + std::to_string(this->u_inputs.size()) + " U.Inputs: " +
           litstring);
#endif
}

AIG::AIG(const AIG &other) {
    this->spec = other.spec;
    this->latches = other.latches;
    this->c_inputs = other.c_inputs;
    this->u_inputs = other.u_inputs;
    this->error_fake_latch = other.error_fake_latch;
    this->lit2deps_map = other.lit2deps_map;
    this->lit2ninputand_map = other.lit2ninputand_map;
}

void AIG::cleanCaches() {
    if (this->lit2deps_map != NULL)
        delete this->lit2deps_map;
    if (this->lit2ninputand_map != NULL)
        delete this->lit2ninputand_map;
}

void AIG::getLitDepsRecur(unsigned lit, std::set<unsigned> &result,
                          std::unordered_set<unsigned>* visited) {
    unsigned stripped_lit = AIG::stripLit(lit);

    // visit the lit and its complement
    visited->insert(lit);
    visited->insert(AIG::negateLit(lit));
    
    // check cache
    std::unordered_map<unsigned, std::set<unsigned>>::iterator cache_hit =
        this->lit2deps_map->find(stripped_lit);
    if (cache_hit != this->lit2deps_map->end()) {
        result.insert(cache_hit->second.begin(), cache_hit->second.end());
        return;
    }

    if (stripped_lit != 0) {
        aiger_and* and_gate = aiger_is_and(this->spec, stripped_lit);
        // is it a gate? then recurse
        if (and_gate) {
            std::set<unsigned> temp;
            if (visited->find(and_gate->rhs0) == visited->end()) {
                this->getLitDepsRecur(and_gate->rhs0, result, visited);
            }
            if (visited->find(and_gate->rhs1) == visited->end()) {
                this->getLitDepsRecur(and_gate->rhs1, result, visited);
            }
        } else if (stripped_lit == this->error_fake_latch->lit) {
            result.insert(stripped_lit);
        } else {
            aiger_symbol* symbol = aiger_is_input(this->spec, stripped_lit);
            if (!symbol) {
                symbol = aiger_is_latch(this->spec, stripped_lit);
                assert(symbol);
                // we are sure that we have a latch here, we have to recurse
                // on latch.next
                if (visited->find(symbol->next) == visited->end()) {
                    std::set<unsigned> temp;
                    this->getLitDepsRecur(symbol->next, result, visited);
                }
            }
            result.insert(stripped_lit);
        }
    }
    
    // cache the result
    (*this->lit2deps_map)[stripped_lit] = result;
}

std::set<unsigned> AIG::getLitDeps(unsigned lit) {
    dbgMsg("Getting dependencies for literal " + std::to_string(lit));
    std::unordered_set<unsigned> visited;
    std::set<unsigned> deps;
    this->getLitDepsRecur(lit, deps, &visited);
    return deps;
}

void AIG::getNInputAnd(unsigned lit, std::vector<unsigned>* A,
                       std::vector<unsigned>* B) {
    assert(!AIG::litIsNegated(lit));
    aiger_and* symbol = aiger_is_and(this->spec, lit);
    assert(symbol);

    // is the result in cache?
    std::unordered_map<unsigned,
                       std::pair<std::vector<unsigned>,
                                 std::vector<unsigned>>>::iterator cache_hit =
        this->lit2ninputand_map->find(lit);
    if (cache_hit != this->lit2ninputand_map->end()) {
        A->insert(A->end(), cache_hit->second.first.begin(),
                  cache_hit->second.first.end());
        B->insert(B->end(), cache_hit->second.second.begin(),
                  cache_hit->second.second.end());
        return;
    }

    std::vector<unsigned> waiting;
    waiting.push_back(lit);
    while (waiting.size() > 0) {
        unsigned cur_lit = waiting.back();
        waiting.pop_back();
        symbol = aiger_is_and(this->spec, cur_lit);
        // we now deal with the left side of the and
        unsigned stripped_left = AIG::stripLit(symbol->rhs0);
        aiger_and* left_sym = aiger_is_and(this->spec, stripped_left);
        if (!left_sym) { // not an AND gate
            A->push_back(symbol->rhs0);
        } else if (AIG::litIsNegated(symbol->rhs0)) { // negated AND gate
            A->push_back(symbol->rhs0);
            B->push_back(stripped_left);
        } else { // non-negated AND gate, this is a recursive step
            waiting.push_back(symbol->rhs0);
        }
        // we now deal with the right side symmetrically
        unsigned stripped_right = AIG::stripLit(symbol->rhs1);
        aiger_and* right_sym = aiger_is_and(this->spec, stripped_right);
        if (!right_sym) { // not an AND gate
            A->push_back(symbol->rhs1);
        } else if (AIG::litIsNegated(symbol->rhs1)) { // negated AND gate
            A->push_back(symbol->rhs1);
            B->push_back(stripped_right);
        } else { // non-negated AND gate, this is a recursive step
            waiting.push_back(symbol->rhs1);
        }

    }

    // cache the result
    (*this->lit2ninputand_map)[lit] = std::make_pair(*A, *B);
}

BDDAIG::BDDAIG(const AIG &base, Cudd* local_mgr) : AIG(base) {
    this->mgr = local_mgr;
    this->primed_latch_cube = NULL;
    this->cinput_cube = NULL;
    this->uinput_cube = NULL;
    this->next_fun_compose_vec = NULL;
    this->trans_rel = NULL;
}

BDDAIG::BDDAIG(const BDDAIG &base, BDD error) : AIG(base) {
    this->mgr = base.mgr;
    this->primed_latch_cube = NULL;
    this->cinput_cube = NULL;
    this->uinput_cube = NULL;
    this->next_fun_compose_vec = NULL;
    this->trans_rel = NULL;
}

void BDDAIG::dump2dot(BDD b, const char* file_name) {
    std::vector<BDD> v;
    v.push_back(b);
    FILE* file = fopen(file_name, "w");
    this->mgr->DumpDot(v, 0, 0, file);
    fclose(file);
}

BDDAIG::~BDDAIG() {
    if (this->primed_latch_cube != NULL)
        delete this->primed_latch_cube;
    if (this->cinput_cube != NULL)
        delete this->cinput_cube;
    if (this->uinput_cube != NULL)
        delete this->uinput_cube;
    if (this->next_fun_compose_vec != NULL)
        delete this->next_fun_compose_vec;
    if (this->trans_rel != NULL)
        delete this->trans_rel;
}

BDD BDDAIG::initState() {
    BDD result = this->mgr->bddOne();
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++)
        result &= ~this->mgr->bddVar((*i)->lit);
#ifndef NDEBUG
    this->dump2dot(result, "init_state.dot");
#endif
    return result;
}

BDD BDDAIG::errorStates() {
    BDD result = this->mgr->bddVar(this->error_fake_latch->lit);
#ifndef NDEBUG
    this->dump2dot(result, "error_states.dot");
#endif
    return result;
}

BDD BDDAIG::primeLatchesInBdd(BDD original) {
    std::vector<BDD> latch_bdds, primed_latch_bdds;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++) {
        latch_bdds.push_back(this->mgr->bddVar((*i)->lit));
        primed_latch_bdds.push_back(this->mgr->bddVar(BDDAIG::primeVar((*i)->lit)));
    }
    BDD result = original.SwapVariables(latch_bdds, primed_latch_bdds);
    return result;
}

BDD BDDAIG::primedLatchCube() {
    if (this->primed_latch_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++)
            result &= this->mgr->bddVar(BDDAIG::primeVar((*i)->lit));
        this->primed_latch_cube = new BDD(result);
    }
    return BDD(*this->primed_latch_cube);
}

BDD BDDAIG::cinputCube() {
    if (this->cinput_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
             i != this->c_inputs.end(); i++)
            result &= this->mgr->bddVar((*i)->lit);
        this->cinput_cube = new BDD(result);
    }
    return BDD(*this->cinput_cube);
}

BDD BDDAIG::uinputCube() {
    if (this->uinput_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
             i != this->u_inputs.end(); i++)
            result &= this->mgr->bddVar((*i)->lit);
        this->uinput_cube = new BDD(result);
    }
    return BDD(*this->uinput_cube);
}

BDD BDDAIG::lit2bdd(unsigned lit, std::unordered_map<unsigned, BDD>* cache=NULL) {
    BDD result;
    // we first check the cache
    if (cache != NULL && (cache->find(lit) != cache->end()))
        return (*cache)[lit];
    unsigned stripped_lit = AIG::stripLit(lit);
    if (stripped_lit == 0) { // return the true/false BDD
        result = ~this->mgr->bddOne();
    } else {
        aiger_and* and_gate = aiger_is_and(this->spec, stripped_lit);
        // is it a gate? then recurse
        if (and_gate) {
            result = (this->lit2bdd(and_gate->rhs0, cache) &
                      this->lit2bdd(and_gate->rhs1, cache));
        } else if (stripped_lit == this->error_fake_latch->lit) {
            result = this->mgr->bddVar(stripped_lit);
        } else {
            // is it an input or latch? these are base cases
            aiger_symbol* symbol = aiger_is_input(this->spec, stripped_lit);
            if (!symbol)
                symbol = aiger_is_latch(this->spec, stripped_lit);
            assert(symbol);
            result = this->mgr->bddVar(stripped_lit);
        }
    }
    // let us deal with the negation now
    if (AIG::litIsNegated(lit))
        result = ~result;
    // cache result if possible
    if (cache != NULL) {
        (*cache)[lit] = result;
        (*cache)[AIG::negateLit(lit)] = ~result;
    }
    return result;
}

std::vector<BDD> BDDAIG::nextFunComposeVec() {
    if (this->next_fun_compose_vec == NULL) {
        this->next_fun_compose_vec = new std::vector<BDD>();
        // get the right bdd for the next fun of every latch
        std::unordered_map<unsigned, BDD> lit2bdd_map;
        BDD next_fun_bdd;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++)
            next_fun_bdd = this->lit2bdd((*i)->next, &lit2bdd_map);

        // fill the vector with singleton bdds except for the latches
        std::vector<aiger_symbol*>::iterator latch_it = this->latches.begin();
        for (unsigned i = 0; i < this->mgr->ReadSize(); i++) {
            if (latch_it != this->latches.end() && i == (*latch_it)->lit) {
                this->next_fun_compose_vec->push_back(lit2bdd_map[(*latch_it)->next]);
                latch_it++;
            } else {
                this->next_fun_compose_vec->push_back(this->mgr->bddVar(i));
            }
        }
    }
    return *this->next_fun_compose_vec;
}

BDD BDDAIG::transRelBdd() {
    if (this->trans_rel == NULL) {
        // get the right bdd for the next fun of every latch
        std::unordered_map<unsigned, BDD> lit2bdd_map;
        BDD next_fun_bdd;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++) {
            next_fun_bdd = this->lit2bdd((*i)->next, &lit2bdd_map);
        }

        // take the conjunction of each primed var and its next fun
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++) {
            result &= (~this->mgr->bddVar(BDDAIG::primeVar((*i)->lit)) |
                       lit2bdd_map[(*i)->next]) &
                      (this->mgr->bddVar(BDDAIG::primeVar((*i)->lit)) |
                       ~lit2bdd_map[(*i)->next]);
        }
        this->trans_rel = new BDD(result);
    }
#ifndef NDEBUG
    this->dump2dot(*this->trans_rel, "trans_rel.dot");
#endif
    return *this->trans_rel;
}

std::set<unsigned> BDDAIG::getBddDeps(BDD b) {
    std::set<unsigned> one_step_deps = this->semanticDeps(b);
    std::vector<unsigned> latch_next_to_explore;
    for (std::set<unsigned>::iterator i = one_step_deps.begin();
         i != one_step_deps.end(); i++) {
        aiger_symbol* symbol = aiger_is_latch(this->spec, *i);
        if (symbol) {
            latch_next_to_explore.push_back(symbol->next);
        }
    }

    // once we have all latch deps in one step, we can call getLitDeps (which
    // is completely recursive) and get the full set
    std::set<unsigned> result = one_step_deps;
    for (std::vector<unsigned>::iterator i = latch_next_to_explore.begin();
         i != latch_next_to_explore.end(); i++) {
        std::set<unsigned> lit_deps = this->getLitDeps(*i);
        result.insert(lit_deps.begin(), lit_deps.end());
    }
    return result;
}

std::vector<BDD> BDDAIG::mergeSomeSignals(BDD cube, std::vector<unsigned>* original) {
    logMsg(std::to_string(original->size()) + " sub-games originally");
    std::set<unsigned> cube_deps = this->getBddDeps(cube);
    dbgMsg("Got the bdddeps");
    std::vector<std::set<unsigned>> dep_vector;
    std::vector<BDD> bdd_vector;
    std::unordered_map<unsigned, BDD> lit2bdd_map;

    for (std::vector<unsigned>::iterator i = original->begin();
         i != original->end(); i++) {
        std::set<unsigned> lit_deps = this->getLitDeps(*i);
        std::set<unsigned> deps;
        deps.insert(cube_deps.begin(), cube_deps.end());
        deps.insert(lit_deps.begin(), lit_deps.end());
        std::vector<std::set<unsigned>>::iterator dep_it = dep_vector.begin();
        std::vector<BDD>::iterator bdd_it = bdd_vector.begin();
        bool found = false;
        for (; dep_it != dep_vector.end();) {
            if ((*dep_it) >= deps) {
                dbgMsg("Some key subsumes current deps");
                (*bdd_it) &= this->lit2bdd(*i, &lit2bdd_map);
                found = true;
                break;
            } else if ((*dep_it) <= deps) {
                dbgMsg("New deps subsumes some key");
                (*bdd_it) &= this->lit2bdd(*i, &lit2bdd_map);
                // we also update the deps because the new one is bigger
                (*dep_it) = deps;
            }
            dep_it++;
            bdd_it++;
        }
        if (!found) {
            dbgMsg("Adding a new subgame");
            dep_vector.push_back(deps);
            bdd_vector.push_back(this->lit2bdd(*i, &lit2bdd_map));
        }

    }

    logMsg(std::to_string(dep_vector.size()) + " sub-games after incl. red.");
    
    // as a last step, we should take NOT x AND cube, for each bdd
    for (std::vector<BDD>::iterator i = bdd_vector.begin();
         i != bdd_vector.end(); i++)
        (*i) = ~(*i) & cube;

    return bdd_vector;
}

std::set<unsigned> BDDAIG::semanticDeps(BDD b) {
    std::set<unsigned> result;
    std::vector<DdNode*> waiting;
    waiting.push_back(b.getNode());
    while (waiting.size() > 0) {
        DdNode* node = waiting.back();
        waiting.pop_back();
        if (!Cudd_IsConstant(node)) {
            result.insert((unsigned) node->index);
            waiting.push_back(Cudd_T(node));
            waiting.push_back(Cudd_E(node));
        }
    }
    return result;
}

std::vector<BDDAIG> BDDAIG::decompose() {
    std::vector<BDDAIG> result;
    if (AIG::litIsNegated(this->error_fake_latch->next)) {
        logMsg("Decomposition possible (BIG OR case)");
        std::vector<unsigned> A, B;
        this->getNInputAnd(AIG::stripLit(this->error_fake_latch->next), &A, &B);
        std::vector<BDD> clean_signals = this->mergeSomeSignals(this->mgr->bddOne(),
                                                                &A);
        for (std::vector<BDD>::iterator i = clean_signals.begin();
             i != clean_signals.end(); i++) {
            BDDAIG subgame(*this, *i);
            result.push_back(subgame);
        }
    } else {
        std::vector<unsigned> A, B;
        this->getNInputAnd(AIG::stripLit(this->error_fake_latch->next), &A, &B);
        if (B.size() == 0) {
            logMsg("No decomposition possible");
        } else {
            logMsg("Decomposition possible (A and [C or D] case)");
            dbgMsg(std::to_string(A.size()) + " AND leaves");
            // how do we choose an OR leaf to distribute?
            // the current heuristic is to choose the one with the most children
            unsigned b = B.back();
            B.pop_back();
            std::vector<unsigned> C, D;
            // getNInputAnd guarantees all of B is stripped
            // so we don't have to strip b
            this->getNInputAnd(b, &C, &D); 
            for (std::vector<unsigned>::iterator i = B.begin(); i != B.end(); i++) {
                std::vector<unsigned> C2, D2;
                this->getNInputAnd(*i, &C2, &D2);
                if (C2.size() > C.size()) {
                    b = (*i);
                    C = C2;
                }
            }
            logMsg("Chosen OR leaf: " + std::to_string(b));
            std::unordered_map<unsigned, BDD> lit2bdd_map; // local cache
            BDD and_leaves_cube = this->mgr->bddOne();
            for (std::vector<unsigned>::iterator i = A.begin(); i != A.end(); i++) {
                if (AIG::stripLit(*i) != b)
                    and_leaves_cube &= this->lit2bdd(*i, &lit2bdd_map);
            }
            std::vector<BDD> clean_signals = this->mergeSomeSignals(and_leaves_cube,
                                                                    &C);
            for (std::vector<BDD>::iterator i = clean_signals.begin();
                 i != clean_signals.end(); i++) {
                BDDAIG subgame(*this, *i);
                result.push_back(subgame);
            }
        }
    }
    return result;
}
