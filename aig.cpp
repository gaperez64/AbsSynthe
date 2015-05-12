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
#include <string>
#include <vector>
#include <unordered_map>

#include "cuddObj.hh"

#include "aiger.h"
#include "aig.h"
#include "logging.h"

unsigned AIG::maxVar() {
    return this->spec->maxvar;
}

unsigned AIG::nextLit() {
    return (this->maxVar() + 1) * 2;
}

void AIG::introduceErrorLatch() {
    if (this->error_fake_latch != NULL)
        return;
    this->error_fake_latch = (aiger_symbol*) malloc(sizeof(aiger_symbol));
    this->error_fake_latch->name = new char[6];
    strncpy(this->error_fake_latch->name, "error", 6);
    this->error_fake_latch->lit = this->nextLit();
    this->error_fake_latch->next = this->spec->outputs[0].lit;
    dbgMsg(std::string("Error fake latch = ") + 
           std::to_string(this->error_fake_latch->lit));
}

AIG::AIG(const char* aiger_file_name, bool intro_error_latch) {
    // default values for some local (for this instance) variables
    this->error_fake_latch = NULL;
    this->spec = NULL;
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
    for (int i = 0; i <= spec->num_latches; i++)
        this->latches.push_back(spec->latches + i);
    // we now introduce a fake latch for the error function
    if (intro_error_latch) {
        this->introduceErrorLatch();
        this->latches.push_back(this->error_fake_latch);
    }
    for (int i = 0; i <= spec->num_inputs; i++) {
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
}

BDDAIG::BDDAIG(const AIG &base, Cudd* local_mgr) : AIG(base) {
    this->mgr = local_mgr;
    this->primed_latch_cube = NULL;
    this->cinput_cube = NULL;
    this->uinput_cube = NULL;
    this->next_fun_compose_vec = NULL;
    this->trans_rel = NULL;
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

void BDDAIG::initState(BDD &result) {
    result = this->mgr->bddOne();
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++)
        result &= this->mgr->bddVar((*i)->lit);
}

void BDDAIG::errorStates(BDD &result) {
    result = this->mgr->bddVar(this->error_fake_latch->lit);
}

void BDDAIG::primeLatchesInBdd(BDD* original, BDD &primed) {
    std::vector<BDD> latch_bdds, primed_latch_bdds;
    for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
         i != this->latches.end(); i++) {
        latch_bdds.push_back(this->mgr->bddVar((*i)->lit));
        primed_latch_bdds.push_back(this->mgr->bddVar(BDDAIG::primeVar((*i)->lit)));
    }
    primed = original->SwapVariables(latch_bdds, primed_latch_bdds);
}

BDD* BDDAIG::primedLatchCube() {
    if (this->primed_latch_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++)
            result &= this->mgr->bddVar(BDDAIG::primeVar((*i)->lit));
        this->primed_latch_cube = new BDD(result);
    }
    return this->primed_latch_cube;
}

BDD* BDDAIG::cinputCube() {
    if (this->cinput_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->c_inputs.begin();
             i != this->c_inputs.end(); i++)
            result &= this->mgr->bddVar(BDDAIG::primeVar((*i)->lit));
        this->cinput_cube = new BDD(result);
    }
    return this->cinput_cube;
}

BDD* BDDAIG::uinputCube() {
    if (this->uinput_cube == NULL) {
        BDD result = this->mgr->bddOne();
        for (std::vector<aiger_symbol*>::iterator i = this->u_inputs.begin();
             i != this->u_inputs.end(); i++)
            result &= this->mgr->bddVar(BDDAIG::primeVar((*i)->lit));
        this->uinput_cube = new BDD(result);
    }
    return this->uinput_cube;
}

void BDDAIG::lit2bdd(unsigned lit, BDD &result,
                     std::unordered_map<unsigned, BDD>* cache=NULL) {
    // we first check the cache
    if (cache != NULL && cache->find(lit) != cache->end())
        return;
    unsigned stripped_lit = AIG::stripLit(lit);
    aiger_and* and_gate = aiger_is_and(this->spec, stripped_lit);
    // is it a gate? then recurse
    if (and_gate) {
        BDD left, right;
        this->lit2bdd(and_gate->rhs0, left, cache);
        this->lit2bdd(and_gate->rhs1, right, cache);
        result = left & right;
    } else if (stripped_lit == 1) { // then return the true/false BDD
        result = ~this->mgr->bddOne();
    } else if (stripped_lit == this->error_fake_latch->lit) {
        result = this->mgr->bddVar(stripped_lit);
    } else {
        aiger_symbol* symbol = aiger_is_input(this->spec, stripped_lit);
        if (!symbol)
            symbol = aiger_is_latch(this->spec, stripped_lit);
        // is it an input or latch? these are base cases
        if (!symbol)
            result = this->mgr->bddVar(stripped_lit);
    }
    // let us deal with the negation now
    if (AIG::litIsNegated(lit))
        result = ~result;
    // cache result if possible
    if (cache != NULL)
        (*cache)[lit] = result;
}

std::vector<BDD>* BDDAIG::nextFunComposeVec() {
    if (this->next_fun_compose_vec == NULL) {
        this->next_fun_compose_vec = new std::vector<BDD>();
        // get the right bdd for the next fun of every latch
        std::unordered_map<unsigned, BDD> lit2bdd_map;
        unsigned latch_lits[this->latches.size()];
        int j = 0;
        BDD next_fun_bdd;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++) {
            latch_lits[j++] = (*i)->lit;
            this->lit2bdd((*i)->next, next_fun_bdd, &lit2bdd_map);
        }

        // fill the vector with singleton bdds except for the latches
        for (unsigned i = 0; i < this->maxVar() * 2; i++) {
            if (std::find(latch_lits, latch_lits + this->latches.size(), i)) {
                this->next_fun_compose_vec->push_back(lit2bdd_map[i]);
            } else {
                this->next_fun_compose_vec->push_back(this->mgr->bddVar(i));
            }
        }
    }
    return this->next_fun_compose_vec;
}

BDD* BDDAIG::transRelBdd() {
    if (this->trans_rel == NULL) {
        // get the right bdd for the next fun of every latch
        std::unordered_map<unsigned, BDD> lit2bdd_map;
        BDD next_fun_bdd;
        for (std::vector<aiger_symbol*>::iterator i = this->latches.begin();
             i != this->latches.end(); i++) {
            this->lit2bdd((*i)->next, next_fun_bdd, &lit2bdd_map);
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
    return this->trans_rel;
}
