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
#include <string.h>
#include <string>
#include <vector>
#include <set>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <iterator>
#include <iostream>

#include "cudd.h"
#include "cuddObj.hh"

#include "aiger.h"
#include "aig.h"
#include "logging.h"

// A <= B iff A - B = empty
static bool setInclusion(std::set<unsigned>* A, std::set<unsigned>* B) {
    std::set<unsigned> diff;
    std::set_difference(A->begin(), A->end(), B->begin(), B->end(),
                        std::inserter(diff, diff.begin()));
    return diff.size() == 0;
}

unsigned AIG::maxVar() {
    return this->spec->maxvar;
}

void AIG::writeToFile(const char* aiger_file_name) {
    aiger_open_and_write_to_file(this->spec, aiger_file_name);
}

void AIG::addGate(unsigned res, unsigned rh0, unsigned rh1) {
    aiger_add_and(this->spec, res, rh0, rh1);
}

void AIG::input2gate(unsigned input, unsigned rh0) {
    aiger_redefine_input_as_and(this->spec, input, rh0, rh0);
    dbgMsg("Gated input " + std::to_string(input));
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
    this->must_clean = true;
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
    for (unsigned i = 0; i < spec->num_latches; i++)
        this->latches.push_back(spec->latches + i);
    // we now introduce a fake latch for the error function
    if (intro_error_latch) {
        this->introduceErrorLatch();
        this->latches.push_back(this->error_fake_latch);
    }
    for (unsigned i = 0; i < spec->num_inputs; i++) {
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
    dbgMsg(std::to_string(this->latches.size()) + " Latches: " + litstring);
    litstring.clear();
    for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
         i != this->c_inputs.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::to_string(this->c_inputs.size()) + " C.Inputs: " + litstring);
    litstring.clear();
    for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
         i != this->u_inputs.end(); i++)
        litstring += std::to_string((*i)->lit) + ", ";
    dbgMsg(std::to_string(this->u_inputs.size()) + " U.Inputs: " + litstring);
#endif
}

AIG::AIG(const AIG &other) {
    this->must_clean = false;
    this->spec = other.spec;
    this->latches = other.latches;
    this->c_inputs = other.c_inputs;
    this->u_inputs = other.u_inputs;
    this->error_fake_latch = other.error_fake_latch;
    this->lit2deps_map = other.lit2deps_map;
    this->lit2ninputand_map = other.lit2ninputand_map;
}

AIG::~AIG() {
    if (this->must_clean) {
        dbgMsg("Cleaning!");
        this->cleanCaches();
    }
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
    
    if (stripped_lit != 0) {
        aiger_and* and_gate = aiger_is_and(this->spec, stripped_lit);
        // is it a gate? then recurse
        if (and_gate) {
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
                    //dbgMsg("Recursing on latch " + std::to_string(symbol->lit));
                    this->getLitDepsRecur(symbol->next, result, visited);
                }
            }
            result.insert(stripped_lit);
        }
    }
}

std::set<unsigned> AIG::getLitDeps(unsigned lit) {
    std::set<unsigned> deps;

    // check cache
    std::unordered_map<unsigned, std::set<unsigned>>::iterator cache_hit =
        this->lit2deps_map->find(lit);
    if (cache_hit != this->lit2deps_map->end()) {
        deps.insert(cache_hit->second.begin(), cache_hit->second.end());
        return deps;
    }

    std::unordered_set<unsigned> visited;
    this->getLitDepsRecur(lit, deps, &visited);
    
    // cache the result
    (*this->lit2deps_map)[lit] = deps;

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

BDD BDDAIG::safeRestrict(BDD original, BDD rest_region) {
    BDD approx = original.Restrict(rest_region);
    assert((approx & rest_region) == (original & rest_region));
    if (approx.nodeCount() < original.nodeCount())
        return approx;
    else
        return original;
}

unsigned AIG::numLatches(){
	return latches.size();
}

BDDAIG::BDDAIG(const AIG &base, Cudd* local_mgr) : AIG(base) {
    this->mgr = local_mgr;
    this->primed_latch_cube = NULL;
    this->cinput_cube = NULL;
    this->uinput_cube = NULL;
    this->next_fun_compose_vec = NULL;
    this->trans_rel = NULL;
    this->short_error = NULL;
}

BDDAIG::BDDAIG(const BDDAIG &base, BDD error) : AIG(base) {
    this->mgr = base.mgr;
    this->primed_latch_cube = NULL;
    this->cinput_cube = NULL;
    this->uinput_cube = NULL;
    this->next_fun_compose_vec = NULL;
    this->trans_rel = NULL;
    this->short_error = new BDD(error);
    // we are now going to reduce the size of the latches and inputs based on
    // error
    dbgMsg("Creating new game with less variables");
    std::set<unsigned> deps = this->getBddDeps(error);
    std::vector<aiger_symbol*> new_vector;
    unsigned c = 0;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
        i != this->latches.end(); i++) {
        
        if ((*i)->lit != this->error_fake_latch->lit &&
            deps.find((*i)->lit) == deps.end()) {
            c++;
            continue; // skip latches not in the cone of error
        }
        new_vector.push_back(*i);
    }
    dbgMsg("Removed " + std::to_string(c) + " latches");
    this->latches = new_vector;
    // controllable inputs now
    new_vector.clear();
    c = 0;
    for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
         i != this->c_inputs.end(); i++) {
        if (deps.find((*i)->lit) == deps.end()) {
            c++;
            continue; // skip cinputs not in the cone of error
        }
        new_vector.push_back(*i);
    }
    dbgMsg("Removed " + std::to_string(c) + " controllable inputs");
    this->c_inputs = new_vector;
    // uncontrollable inputs to finish
    new_vector.clear();
    c = 0;
    for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
         i != this->u_inputs.end(); i++) {
        if (deps.find((*i)->lit) == deps.end()) {
            c++;
            continue; // skip uinputs not in the cone of error
        }
        new_vector.push_back(*i);
    }
    dbgMsg("Removed " + std::to_string(c) + " uncontrollable inputs");
    this->u_inputs = new_vector;
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
    if (this->short_error != NULL)
        delete this->short_error;
}

BDD BDDAIG::initState() {
    BDD result = this->mgr->bddOne();
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++)
        result &= ~this->mgr->bddVar((*i)->lit);
#ifndef NDEBUG
    this->dump2dot(result, "init_state.dot");
#endif
    assert(this->isValidLatchBdd(result));
    return result;
}

BDD BDDAIG::errorStates() {
    BDD result = this->mgr->bddVar(this->error_fake_latch->lit);
#ifndef NDEBUG
    this->dump2dot(result, "error_states.dot");
#endif
    assert(this->isValidLatchBdd(result));
    return result;
}

BDD BDDAIG::primeLatchesInBdd(BDD original) {
    std::vector<BDD> latch_bdds, primed_latch_bdds;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++) {
        latch_bdds.push_back(this->mgr->bddVar((*i)->lit));
        primed_latch_bdds.push_back(this->mgr->bddVar(AIG::primeVar((*i)->lit)));
    }
    BDD result = original.SwapVariables(latch_bdds, primed_latch_bdds);
    return result;
}

BDD BDDAIG::primedLatchCube() {
    if (this->primed_latch_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++)
            result &= this->mgr->bddVar(AIG::primeVar((*i)->lit));
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

std::vector<unsigned> AIG::getCInputLits(){
  std::vector<unsigned> v;
  std::vector<aiger_symbol*>::iterator it = this->c_inputs.begin();
  for(; it != this->c_inputs.end(); it++){
		v.push_back((*it)->lit);
  }
  return v;
}
std::vector<unsigned> AIG::getUInputLits(){
  std::vector<unsigned> v;
  std::vector<aiger_symbol*>::iterator it = this->u_inputs.begin();
  for(; it != this->u_inputs.end(); it++){
		v.push_back((*it)->lit);
  }
  return v;
}
std::vector<BDD> BDDAIG::nextFunComposeVec() {
    if (this->next_fun_compose_vec == NULL) {
        dbgMsg("building and caching next_fun_compose_vec");
        this->next_fun_compose_vec = new std::vector<BDD>();
        // get the right bdd for the next fun of every latch
        std::unordered_map<unsigned, BDD> lit2bdd_map;
        if (this->short_error){
          lit2bdd_map[this->error_fake_latch->next] =  *this->short_error;
        }
        BDD next_fun_bdd;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++) {
            next_fun_bdd = this->lit2bdd((*i)->next, &lit2bdd_map);
        }
        // fill the vector with singleton bdds except for the latches
        std::vector<aiger_symbol*>::iterator latch_it = this->latches.begin();
        for (unsigned i = 0; ((int) i) < this->mgr->ReadSize(); i++) {
            if (latch_it != this->latches.end() && i == (*latch_it)->lit) {
                // since we allow for short_error to override the next fun...
                BDD next_fun;
                if (i == this->error_fake_latch->lit &&
                    this->short_error != NULL) {
                    next_fun = *this->short_error; // lit2bdd_map[(*i)->next] | *this->short_error;
                    //dbgMsg("Latch " + std::to_string(i) + " is the error latch");
                } else if (this->short_error != NULL) { // simplify functions
                    next_fun = BDDAIG::safeRestrict(lit2bdd_map[(*latch_it)->next],
                                                    ~(*this->short_error));
                    //dbgMsg("Restricting next function of latch " + std::to_string(i));
                } else {
                    next_fun = lit2bdd_map[(*latch_it)->next];
                    //dbgMsg("Taking the next function of latch " + std::to_string(i));
                }
                this->next_fun_compose_vec->push_back(next_fun);
                latch_it++;
            } else {
                this->next_fun_compose_vec->push_back(this->mgr->bddVar(i));
            }
        }
        dbgMsg("done with the next_fun_compose_vec");
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
            // since we allow for short_error to override the next fun...
            if ((*i)->lit == this->error_fake_latch->lit &&
                this->short_error != NULL) {
                BDD error_next_fun = *this->short_error; // lit2bdd_map[(*i)->next] | *this->short_error;
                result &= (~this->mgr->bddVar(AIG::primeVar((*i)->lit)) |
                           error_next_fun) &
                          (this->mgr->bddVar(AIG::primeVar((*i)->lit)) |
                           ~error_next_fun);
            } else if (this->short_error != NULL) { // simplify functions
                BDD fun = BDDAIG::safeRestrict(lit2bdd_map[(*i)->next],
                                               ~(*this->short_error));
                result &= (~this->mgr->bddVar(AIG::primeVar((*i)->lit)) |
                           fun) &
                          (this->mgr->bddVar(AIG::primeVar((*i)->lit)) |
                           ~fun);
            } else {
                result &= (~this->mgr->bddVar(AIG::primeVar((*i)->lit)) |
                           lit2bdd_map[(*i)->next]) &
                          (this->mgr->bddVar(AIG::primeVar((*i)->lit)) |
                           ~lit2bdd_map[(*i)->next]);
            }
        }
        this->trans_rel = new BDD(result);
    }
#ifndef NDEBUG
    this->dump2dot(*this->trans_rel, "trans_rel.dot");
#endif
    return *this->trans_rel;
}

std::set<unsigned> BDDAIG::getBddDeps(BDD b) {
    dbgMsg("Computing dependencies of BDD");
		std::cout << &b << std::endl;
		if (cache_bdd_deps.find(b.getNode()) != cache_bdd_deps.end()){
			std::cout << "Cache hit\n";
			return cache_bdd_deps[b.getNode()];
		}
			std::cout << "Cache miss\n";
		// std::cout << &b << std::endl;
    std::set<unsigned> one_step_deps = this->semanticDeps(b);
    dbgMsg("Which deps are actually latches?");
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
    dbgMsg("Recursing on latches found in dependencies");
    std::set<unsigned> result = one_step_deps;
    for (std::vector<unsigned>::iterator i = latch_next_to_explore.begin();
         i != latch_next_to_explore.end(); i++) {
        std::set<unsigned> lit_deps = this->getLitDeps(*i);
        result.insert(lit_deps.begin(), lit_deps.end());
    }
		cache_bdd_deps[b.getNode()] = result;
    return result;
}
std::string stringOfUnsignedSet(std::set<unsigned> s){
  // print some debug information
  std::string litstring;
  for (std::set<unsigned>::iterator i = s.begin(); i != s.end(); i++)
    litstring += std::to_string(*i) + ", ";
  return(std::string("the cube deps: ") + litstring);
}

template<class T>
bool set_inclusion(std::set<T> a, std::set<T> b){
  std::set<T> diff;
  std::set_difference(a.begin(), a.end(), b.begin(), b.end(), inserter(diff, diff.end()));
  return (diff.size() == 0);
}

std::vector<BDD> BDDAIG::mergeSomeSignals(BDD cube, std::vector<unsigned>* original) {
		
    logMsg(std::to_string(original->size()) + " sub-games originally");
    const std::set<unsigned> cube_deps = this->getBddDeps(cube);
#ifndef NDEBUG
        // print some debug information
        std::string litstring;
        for (std::set<unsigned>::iterator i = cube_deps.begin(); i != cube_deps.end(); i++)
            litstring += std::to_string(*i) + ", ";
        dbgMsg("the cube deps: " + litstring);
#endif
    std::vector<std::set<unsigned>> dep_vector;
    std::vector<BDD> bdd_vector;
    std::unordered_map<unsigned, BDD> lit2bdd_map;

    for (std::vector<unsigned>::iterator i = original->begin();
         i != original->end(); i++) {
        dbgMsg("Processing subgame...");
        std::set<unsigned> lit_deps = this->getLitDeps(*i);
        std::set<unsigned> deps;
        deps.insert(cube_deps.begin(), cube_deps.end());
        deps.insert(lit_deps.begin(), lit_deps.end());
#if true
        // print some debug information
        std::string litstring;
        for (std::set<unsigned>::iterator j = deps.begin(); j != deps.end(); j++)
            litstring += std::to_string(*j) + ", ";
        dbgMsg("the current subgame has in its cone... " + litstring);
#endif
        dbgMsg("We will compare with " + std::to_string(dep_vector.size()) + " previous subgames");
        std::vector<std::set<unsigned>>::iterator dep_it = dep_vector.begin();
        std::vector<BDD>::iterator bdd_it = bdd_vector.begin();
        bool found = false;
        for (; dep_it != dep_vector.end();) {
            if (setInclusion(&deps, &(*dep_it))) {
                //dbgMsg("this subgame is subsumed by some previous subgame");
								clock_t atime = clock();
                (*bdd_it) &= this->lit2bdd(*i, &lit2bdd_map);
								clock_t btime = clock();
								std::cout << "----------------------------------- took " 
									<< (btime-atime)/ (double)CLOCKS_PER_SEC << " time\n";
                found = true;
                break;
            } else if (setInclusion(&(*dep_it), &deps)) {
                //dbgMsg("this new subgame subsumes some previous subgame");
								clock_t atime = clock();
                (*bdd_it) &= this->lit2bdd(*i, &lit2bdd_map);
                assert((*bdd_it) == ((*bdd_it) & this->lit2bdd(*i, &lit2bdd_map)));
                // we also update the deps because the new one is bigger
                (*dep_it) = deps;
								clock_t btime = clock();
								std::cout << "----------------------------------- took " 
									<< (btime-atime)/ (double)CLOCKS_PER_SEC << " time\n";
            }
            dep_it++;
            bdd_it++;
        }
        if (!found) {
            dbgMsg("Adding new");
            dep_vector.push_back(deps);
            bdd_vector.push_back(this->lit2bdd(*i, &lit2bdd_map));
        }

    }

    logMsg(std::to_string(dep_vector.size()) + " sub-games after incl. red.");
    
    // as a last step, we should take NOT x AND cube, for each bdd
    std::vector<BDD> bdd_vector_with_cube;
    for (std::vector<BDD>::iterator i = bdd_vector.begin();
         i != bdd_vector.end(); i++) {
        bdd_vector_with_cube.push_back(~(*i) & cube);
    }
    return bdd_vector_with_cube;
}

std::set<unsigned> BDDAIG::semanticDeps(BDD b) {
    std::set<unsigned> result;
    for (unsigned i = 0; ((int) i) < this->mgr->ReadSize(); i++) {
        BDD simpler_b = b.ExistAbstract(this->mgr->bddVar(i));
        if (b != simpler_b) {
            result.insert(i);
            //dbgMsg("Depends on var " + std::to_string(i));
        }
    }
#if false // previous code which fails for huge bdds
    std::vector<DdNode*> waiting;
    unsigned bdd_size = b.nodeCount();
    dbgMsg("semanticDeps of BDD with node count: " + std::to_string(bdd_size));
    waiting.push_back(b.getRegularNode());
    while (waiting.size() > 0) {
        DdNode* node = waiting.back();
        waiting.pop_back();
        if (!Cudd_IsConstant(node)) {
            result.insert((unsigned) node->index);
            DdNode* child = Cudd_Regular(Cudd_T(node));
            if (!Cudd_IsConstant(child))
                waiting.push_back(child);
            child = Cudd_Regular(Cudd_E(node));
            if (!Cudd_IsConstant(child))
                waiting.push_back(child);
        }
        assert(result.size() <= bdd_size);
    }
#endif
    return result;
}

std::vector<BDDAIG*> BDDAIG::decompose() {
    std::vector<BDDAIG*> result;
    if (AIG::litIsNegated(this->error_fake_latch->next)) {
        logMsg("Decomposition possible (BIG OR case)");
        std::vector<unsigned> A, B;
        this->getNInputAnd(AIG::stripLit(this->error_fake_latch->next), &A, &B);
        std::vector<BDD> clean_signals = this->mergeSomeSignals(this->mgr->bddOne(),
                                                                &A);
        for (std::vector<BDD>::iterator i = clean_signals.begin();
             i != clean_signals.end(); i++) {
            result.push_back(new BDDAIG(*this, *i));
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
                result.push_back(new BDDAIG(*this, *i));
            }
        }
    }
    return result;
}

bool BDDAIG::isValidLatchBdd(BDD b) {
#ifndef NDEBUG
    std::set<unsigned> vars_in_cone = this->semanticDeps(b);
    int hits = 0;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++) {
        if (vars_in_cone.find((*i)->lit) != vars_in_cone.end())
            hits++;
    }
    if (hits != vars_in_cone.size()) {
        std::string litstring;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++)
            litstring += std::to_string((*i)->lit) + ", ";
        dbgMsg(std::to_string(this->latches.size()) + " Latches: " + litstring);
        litstring.clear();
        for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
             i != this->c_inputs.end(); i++)
            litstring += std::to_string((*i)->lit) + ", ";
        dbgMsg(std::to_string(this->c_inputs.size()) + " C.Inputs: " + litstring);
        litstring.clear();
        for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
             i != this->u_inputs.end(); i++)
            litstring += std::to_string((*i)->lit) + ", ";
        dbgMsg(std::to_string(this->u_inputs.size()) + " U.Inputs: " + litstring);
        litstring.clear();
        for (std::set<unsigned>::iterator i = vars_in_cone.begin();
             i != vars_in_cone.end(); i++)
            litstring += std::to_string(*i) + ", ";
        dbgMsg(std::to_string(vars_in_cone.size()) + " Vars in cone: " + litstring);
        return false;
    } else {
        return true;
    }
#else
    return true;
#endif
}

bool BDDAIG::isValidBdd(BDD b) {
#ifndef NDEBUG
    std::set<unsigned> vars_in_cone = this->semanticDeps(b);
    int hits = 0;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++) {
        if (vars_in_cone.find((*i)->lit) != vars_in_cone.end())
            hits++;
    }
    for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
         i != this->c_inputs.end(); i++) {
        if (vars_in_cone.find((*i)->lit) != vars_in_cone.end())
            hits++;
    }
    for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
         i != this->u_inputs.end(); i++) {
        if (vars_in_cone.find((*i)->lit) != vars_in_cone.end())
            hits++;
    }
    if (hits != vars_in_cone.size()) {
        std::string litstring;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++)
            litstring += std::to_string((*i)->lit) + ", ";
        dbgMsg(std::to_string(this->latches.size()) + " Latches: " + litstring);
        litstring.clear();
        for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
             i != this->c_inputs.end(); i++)
            litstring += std::to_string((*i)->lit) + ", ";
        dbgMsg(std::to_string(this->c_inputs.size()) + " C.Inputs: " + litstring);
        litstring.clear();
        for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
             i != this->u_inputs.end(); i++)
            litstring += std::to_string((*i)->lit) + ", ";
        dbgMsg(std::to_string(this->u_inputs.size()) + " U.Inputs: " + litstring);
        litstring.clear();
        for (std::set<unsigned>::iterator i = vars_in_cone.begin();
             i != vars_in_cone.end(); i++)
            litstring += std::to_string(*i) + ", ";
        dbgMsg(std::to_string(vars_in_cone.size()) + " Vars in bdd: " + litstring);
        litstring.clear();
        std::set<unsigned> all_deps = this->getBddDeps(*this->short_error);
        for (std::set<unsigned>::iterator i = all_deps.begin();
             i != all_deps.end(); i++)
            litstring += std::to_string(*i) + ", ";
        dbgMsg(std::to_string(vars_in_cone.size()) + " Vars in cone: " + litstring);
        litstring.clear();
        return false;
    } else {
        return true;
    }
#else
    return true;
#endif
}
