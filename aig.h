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

#include "aiger.h"

class AIG {
    private:
    aiger* spec;
    std::vector<aiger_symbol*> latches;
    std::vector<aiger_symbol*> c_inputs;
    std::vector<aiger_symbol*> u_inputs;
    aiger_symbol* error_fake_latch;

    unsigned nextLit();
    void introduceErrorLatch();
        /*
    aiger_symbol* error_fake_latch;
    void introduceErrorLatch();
    void replaceErrorFunction();

    static:
    long negateLit(long lit) { return lit ^ 1; }
    bool litIsNegated(long lit) { return (lit & 1) == 1; }
    long stripLit(long lit) { return long & ~1; }
    long symbolLit(aiger_symbol* const symbol) { return symbol.lit; }*/

    public:
    AIG(const char*, bool intro_error_latch=false);
    /*long numLatches();
    long maxVar();
    long nextLit();*/
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

#endif
