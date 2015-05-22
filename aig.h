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

#ifndef ABSSYNTHE_AIG_H
#define ABSSYNTHE_AIG_H

#include <string>
#include <vector>
#include <set>
#include <unordered_set>
#include <unordered_map>
#include <cassert>

#include "cuddObj.hh"

#include "aiger.h"

class AIG {
    private:
        bool must_clean;
    protected:
        aiger* spec;
        std::vector<aiger_symbol*> latches;
        std::vector<aiger_symbol*> c_inputs;
        std::vector<aiger_symbol*> u_inputs;
        aiger_symbol* error_fake_latch;
        void introduceErrorLatch();
        std::unordered_map<unsigned, std::set<unsigned>>* lit2deps_map;
        std::unordered_map<unsigned,
                           std::pair<std::vector<unsigned>,
                                     std::vector<unsigned>>>* lit2ninputand_map;
        void getNInputAnd(unsigned, std::vector<unsigned>*,
                          std::vector<unsigned>*);
        void getLitDepsRecur(unsigned, std::set<unsigned>&,
                             std::unordered_set<unsigned>*);
        std::set<unsigned> getLitDeps(unsigned);
        static unsigned primeVar(unsigned lit) { return AIG::stripLit(lit) + 1; }
    public:
        static unsigned negateLit(unsigned lit) { return lit ^ 1; }
        static bool litIsNegated(unsigned lit) { return (lit & 1) == 1; }
        static unsigned stripLit(unsigned lit) { return lit & ~1; }

        AIG(const char*, bool intro_error_latch=true);
        AIG(const AIG&);
        ~AIG();
        void cleanCaches();
        unsigned maxVar();
        void addGate(unsigned, unsigned, unsigned);
        void input2gate(unsigned, unsigned);
        void writeToFile(const char*);
        std::vector<aiger_symbol*> getLatches() { return this->latches; }
        std::vector<aiger_symbol*> getCInputs() { return this->c_inputs; }
	    unsigned numLatches();
        void check(){
#ifndef NDEBUG
          if (this->c_inputs.size() != 1 ){
            std::cout << "c_inputs size: " << this->c_inputs.size() << std::endl;
            std::cout << "u_inputs size: " << this->u_inputs.size() << std::endl;
          }
          assert(this->c_inputs.size() == 1);
#endif
        }
        std::vector<unsigned> getCInputLits();
        std::vector<unsigned> getUInputLits();
};

class BDDAIG : public AIG {
    private:
        bool must_clean;
    protected:
        BDD* primed_latch_cube;
        BDD* cinput_cube;
        BDD* uinput_cube;
        BDD* trans_rel;
        BDD* short_error;
        std::unordered_map<unsigned, BDD>* lit2bdd_map;
        std::unordered_map<unsigned long, std::set<unsigned>>* bdd2deps_map;
        std::vector<BDD>* next_fun_compose_vec;
        BDD lit2bdd(unsigned);
        std::vector<BDD> mergeSomeSignals(BDD, std::vector<unsigned>*);
        bool isValidLatchBdd(BDD);
        bool isValidBdd(BDD);
    public:
        static BDD safeRestrict(BDD, BDD);
        std::set<unsigned> semanticDeps(BDD);
        
        Cudd* mgr;
        static unsigned primeVar(unsigned lit) { return AIG::stripLit(lit) + 1; }
        BDDAIG(const AIG&, Cudd*);
        BDDAIG(const BDDAIG&, BDD);
        ~BDDAIG();
        void dump2dot(BDD, const char*);
        BDD initState();
        BDD errorStates();
        BDD primeLatchesInBdd(BDD);
        BDD primedLatchCube();
        BDD cinputCube();
        BDD uinputCube();
        BDD transRelBdd();
        std::set<unsigned> getBddDeps(BDD);
        std::vector<BDD> nextFunComposeVec(BDD*);
        std::vector<BDDAIG*> decompose();
};

#endif
