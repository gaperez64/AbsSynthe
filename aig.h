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

#include "cuddObj.hh"

#include "aiger.h"

/* The AIG class has no explicit destructor because it only keeps a collection
 * of pointers to elements in the original aiger structure. Also, since we
 * manipulate copies of AIGs, it would be bad to delete stuff while another,
 * previous created, copy is still being used... However, if we want to clean
 * up caches or other stuff used by AIG, one may use cleanCaches.
 */
class AIG {
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

    public:
        static unsigned negateLit(unsigned lit) { return lit ^ 1; }
        static bool litIsNegated(unsigned lit) { return (lit & 1) == 1; }
        static unsigned stripLit(unsigned lit) { return lit & ~1; }

        AIG(const char*, bool intro_error_latch=true);
        AIG(const AIG&);
        void cleanCaches();
        unsigned maxVar();
    /*
    void input2and(aiger_symbol*, aiger_symbol*);
    void writeSpec();
    void getLitType(long lit);
    void getLitName(long lit);
    bool litIsAnd(long lit);
    aiger_symbol* const getErrSymbol();
    aiger_symbol* const addGate(long, aiger_symbol*, aiger_symbol*);
    aiger_symbol* const addOutput(long, char*);
    void removeOutputs();*/
    /*
    void aigSearchUntilNegs(aiger_symbol*, std::vector<long>, std::vector<long>);
    std::vector<long>* getMultLitDeps(std::vector<long>*);
    std::vector<long>* getLitDeps(long);
    std::vector<long>* getLitLatchDeps(long);
    std::vector<long>* getLitCInputDeps(long);
    std::vector<long>* getLitUInputDeps(long);
    long** latchDepMap(long* const, int);
    aiger_symbol* newSymbol();
*/
};

class BDDAIG : public AIG {
    protected:
        Cudd* mgr;
        BDD* primed_latch_cube;
        BDD* cinput_cube;
        BDD* uinput_cube;
        BDD* trans_rel;
        std::vector<BDD>* next_fun_compose_vec;
        BDD lit2bdd(unsigned, std::unordered_map<unsigned, BDD>*);
        std::vector<BDD> mergeSomeSignals(BDD, std::vector<unsigned>*);
        std::set<unsigned> semanticDeps(BDD);

    public:
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
        std::vector<BDD> nextFunComposeVec();
        std::vector<BDDAIG> decompose();
};

#endif
